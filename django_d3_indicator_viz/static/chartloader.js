import LineChart from "./linechart.js";
import ColumnChart from "./columnchart.js";
import DonutChart from "./donutchart.js";
import MinMedMaxChart from "./minmedmaxchart.js";
import Ban from "./ban.js";
import DataTable from "./datatable.js";
import { getVisualContainer, getTableContainer } from "./utils.js";

// Cache reference data (loaded once from script tag)
let cachedReferenceData = null;

/**
 * Gets cached reference data from the script tag.
 * Loads once on first call and caches for subsequent calls.
 */
function getReferenceData() {
    if (!cachedReferenceData) {
        const scriptTag = document.getElementById('reference-data');
        if (!scriptTag) {
            console.error('Reference data script tag not found');
            return {
                filterOptions: [],
                colorScales: [],
                locationTypes: [],
                locations: [],
                primaryLocId: null,
                parentLocIds: '',
                siblingLocIds: ''
            };
        }
        cachedReferenceData = JSON.parse(scriptTag.textContent);
    }
    return cachedReferenceData;
}

/**
 * Loads and renders a chart by fetching data from the API.
 *
 * @param {HTMLElement} container - The chart container element with data attributes
 */
export async function loadChart(container) {
    // Prevent duplicate loads
    if (container.dataset.loaded) return;
    container.dataset.loaded = "true";

    // Parse metadata from data attributes
    const indicator = JSON.parse(container.dataset.indicator);
    const visual = JSON.parse(container.dataset.visual);

    // Get cached reference data
    const { filterOptions, colorScales, locationTypes, locations, primaryLocId, parentLocIds, siblingLocIds } = getReferenceData();

    // Build API query parameters
    const baseParams = {
        indicator_id: container.dataset.indicatorId,
        source_id: visual.source_id,
    };

    // For line charts, fetch all dates; for others, filter by specific dates
    if (visual.data_visual_type !== 'line') {
        baseParams.start_date = visual.start_date;
        baseParams.end_date = visual.end_date;
    }

    const primaryParams = new URLSearchParams({
        ...baseParams,
        location_id: primaryLocId,
    });

    // Fetch primary location data
    const promises = [
        fetch(`/api/values/?${primaryParams}`)
            .then(r => r.json())
            .then(data => data.results || data)
    ];

    // Fetch comparison data if needed based on location_comparison_type
    let comparisonLocIds = null;
    if (visual.location_comparison_type === 'parents') {
        comparisonLocIds = parentLocIds;
    } else if (visual.location_comparison_type === 'siblings') {
        comparisonLocIds = siblingLocIds;
    }

    if (comparisonLocIds) {
        const compParams = new URLSearchParams({
            ...baseParams,
            location_id__in: comparisonLocIds,
        });
        promises.push(
            fetch(`/api/values/?${compParams}`)
                .then(r => r.json())
                .then(data => data.results || data)
        );
    }

    try {
        const [primaryData, comparisonData] = await Promise.all(promises);

        if (!primaryData || primaryData.length === 0) {
            container.innerHTML = 'No data available';
            return;
        }

        // Look up location from cached data
        const location = locations.find(l => l.id === primaryLocId);
        if (!location) {
            console.error('Location not found:', primaryLocId);
            container.innerHTML = 'Location not found';
            return;
        }

        // Transform indicator data to match expected format
        const indicatorData = transformIndicatorData(primaryData);

        // Look up comparison locations from cached data
        let compareLocations = [];
        let compareData = [];

        if (comparisonData && comparisonData.length > 0) {
            // Get unique location IDs from comparison data
            const comparisonLocationIds = [...new Set(comparisonData.map(item => item.location))];
            // Look them up from cached locations
            compareLocations = locations.filter(l => comparisonLocationIds.includes(l.id));
            compareData = transformIndicatorData(comparisonData);
        }

        // Chart options
        const chartOptions = {
            animation: false,
            textStyle: {
                fontFamily: 'inherit',
                fontSize: 16,
                color: '#000'
            }
        };

        // Get table container if it exists
        const tableContainer = getTableContainer(indicator.id);

        // Render the appropriate chart type
        switch (visual.data_visual_type) {
            case 'ban':
                new Ban(
                    visual,
                    container,
                    indicator,
                    location,
                    indicatorData[0],
                    compareLocations,
                    compareData,
                    filterOptions,
                    chartOptions
                );
                break;

            case 'column':
                new ColumnChart(
                    visual,
                    container,
                    indicator,
                    location,
                    indicatorData,
                    compareLocations,
                    compareData,
                    filterOptions,
                    colorScales,
                    visual.location_comparison_type,
                    chartOptions
                );
                if (tableContainer) {
                    new DataTable(
                        visual,
                        tableContainer,
                        indicator,
                        location,
                        indicatorData,
                        compareLocations,
                        compareData,
                        filterOptions,
                        chartOptions
                    );
                }
                break;

            case 'line':
                new LineChart(
                    visual,
                    container,
                    indicator,
                    location,
                    indicatorData,
                    compareLocations,
                    compareData,
                    filterOptions,
                    locationTypes,
                    colorScales,
                    chartOptions
                );
                if (tableContainer) {
                    new DataTable(
                        visual,
                        tableContainer,
                        indicator,
                        location,
                        indicatorData,
                        compareLocations,
                        compareData,
                        filterOptions,
                        chartOptions
                    );
                }
                break;

            case 'min_med_max':
                new MinMedMaxChart(
                    visual,
                    container,
                    indicator,
                    location,
                    indicatorData[0],
                    compareLocations,
                    compareData,
                    filterOptions,
                    locationTypes,
                    chartOptions
                );
                break;

            case 'donut':
                new DonutChart(
                    visual,
                    container,
                    indicator,
                    location,
                    indicatorData,
                    compareLocations,
                    compareData,
                    filterOptions,
                    locationTypes,
                    colorScales,
                    chartOptions
                );
                if (tableContainer) {
                    new DataTable(
                        visual,
                        tableContainer,
                        indicator,
                        location,
                        indicatorData,
                        compareLocations,
                        compareData,
                        filterOptions,
                        chartOptions
                    );
                }
                break;

            default:
                console.error("Unknown data visual type:", visual.data_visual_type);
                container.innerHTML = 'Unsupported chart type';
        }

    } catch (error) {
        console.error("Error loading chart:", error);
        container.innerHTML = 'Error loading chart';
    }
}

/**
 * Transforms API response data to match the format expected by chart classes.
 *
 * @param {Array} apiData - Array of IndicatorValue objects from API
 * @returns {Array} Transformed data array
 */
function transformIndicatorData(apiData) {
    return apiData.map(item => ({
        location_id: typeof item.location === 'object' ? item.location.id : item.location,
        indicator_id: typeof item.indicator === 'object' ? item.indicator.id : item.indicator,
        source_id: typeof item.source === 'object' ? item.source.id : item.source,
        filter_option_id: item.filter_option ?
            (typeof item.filter_option === 'object' ? item.filter_option.id : item.filter_option)
            : null,
        start_date: item.start_date,
        end_date: item.end_date,
        value: item.value,
        value_moe: item.value_moe,
        count: item.count,
        count_moe: item.count_moe,
        universe: item.universe,
        universe_moe: item.universe_moe,
    }));
}

/**
 * Loads all charts on the page.
 */
export function loadAllCharts() {
    document.querySelectorAll('.chart-container').forEach(loadChart);
}
