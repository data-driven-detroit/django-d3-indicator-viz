import { getVisualContainer, getTableContainer, DataVisualLocationComparisonType } from "./utils.js";
import Ban from "./ban.js";
import ColumnChart from "./columnchart.js";
import LineChart from "./linechart.js";
import MinMedMaxChart from "./minmedmaxchart.js";
import DonutChart from "./donutchart.js";
import DataTable from "./datatable.js";

/**
 * Loads and renders all charts for a section using pre-fetched data.
 *
 * This is a hybrid approach between chartloader.js and visuals.js:
 * - Makes ONE API call to fetch all section data (not per-chart like chartloader.js)
 * - Filters data client-side with indexed lookups (faster than visuals.js linear search)
 * - Section-scoped instead of page-scoped
 */
export default class SectionLoader {

    /**
     * Creates a section loader with all data needed to render charts.
     *
     * @param {Object} sectionData - All data for this section
     * @param {Object} sectionData.section - Section metadata {id, name, sort_order}
     * @param {Array} sectionData.categories - Categories with nested indicators
     * @param {Array} sectionData.dataVisuals - Data visual configurations
     * @param {Array} sectionData.indicatorValues - All indicator values for this section
     * @param {Array} sectionData.filterOptions - Filter options (age groups, etc)
     * @param {Array} sectionData.colorScales - Color scale definitions
     * @param {Object} sectionData.locations - {primary, parents, siblings}
     * @param {Array} sectionData.locationTypes - Location type definitions
     * @param {Object} options - Chart options for echarts
     */
    constructor(sectionData, options = {}) {
        this.section = sectionData.section;
        this.categories = sectionData.categories;
        this.dataVisuals = sectionData.dataVisuals;
        this.indicatorValues = sectionData.indicatorValues;
        this.filterOptions = sectionData.filterOptions;
        this.colorScales = sectionData.colorScales;
        this.locations = sectionData.locations;
        this.locationTypes = sectionData.locationTypes;
        this.options = options;

        // Build indexes for O(1) lookups
        this._buildIndexes();
    }

    /**
     * Builds indexed data structures for fast lookups.
     *
     * Instead of filtering arrays with O(n) complexity, we create nested maps
     * for O(1) lookups: indicator_id -> location_id -> source_id -> values[]
     */
    _buildIndexes() {
        // Index indicator values by [indicator_id][location_id][source_id]
        this.valueIndex = {};

        this.indicatorValues.forEach(val => {
            const indicatorId = typeof val.indicator === 'object' ? val.indicator.id : val.indicator;
            const locationId = typeof val.location === 'object' ? val.location.id : val.location;
            const sourceId = typeof val.source === 'object' ? val.source.id : val.source;

            if (!this.valueIndex[indicatorId]) {
                this.valueIndex[indicatorId] = {};
            }
            if (!this.valueIndex[indicatorId][locationId]) {
                this.valueIndex[indicatorId][locationId] = {};
            }
            if (!this.valueIndex[indicatorId][locationId][sourceId]) {
                this.valueIndex[indicatorId][locationId][sourceId] = [];
            }

            this.valueIndex[indicatorId][locationId][sourceId].push(val);
        });

        // Index indicators by id for quick lookup
        this.indicatorIndex = {};
        this.categories.forEach(category => {
            if (category.indicators) {
                category.indicators.forEach(indicator => {
                    this.indicatorIndex[indicator.id] = indicator;
                });
            }
        });

        // Index data visuals by indicator_id for quick lookup
        this.visualIndex = {};
        this.dataVisuals.forEach(visual => {
            this.visualIndex[visual.indicator_id] = visual;
        });
    }

    /**
     * Draws all charts in this section.
     */
    drawAll() {
        this.dataVisuals.forEach(visual => {
            this._drawChart(visual);
        });
    }

    /**
     * Draws a single chart for a given visual configuration.
     *
     * @param {Object} visual - The data visual configuration
     */
    _drawChart(visual) {
        // Get the visual container (required)
        const container = getVisualContainer(visual.indicator_id, visual.data_visual_type);
        if (!container) {
            console.error("Container not found for indicatorId:", visual.indicator_id);
            return;
        }

        // Get the table container (optional, for some chart types)
        const tableContainer = getTableContainer(visual.indicator_id);

        // Get the indicator (required)
        const indicator = this.indicatorIndex[visual.indicator_id];
        if (!indicator) {
            console.error("Indicator not found for indicatorId:", visual.indicator_id);
            return;
        }

        // Get the primary location (required)
        const location = this.locations.primary;
        if (!location) {
            console.error("Primary location not found");
            return;
        }

        // Get indicator data for primary location
        const indicatorData = this._filterData(location.id, visual);
        if (!indicatorData || indicatorData.length === 0) {
            console.warn("No data found for visual:", visual);
            container.innerHTML = 'No data available';
            return;
        }

        // Get comparison locations and data
        let compareLocations = [];
        let compareData = [];

        if (visual.location_comparison_type) {
            if (visual.location_comparison_type === DataVisualLocationComparisonType.PARENTS) {
                compareLocations = this.locations.parents || [];
            } else if (visual.location_comparison_type === DataVisualLocationComparisonType.SIBLINGS) {
                compareLocations = this.locations.siblings || [];
            }

            if (compareLocations.length === 0) {
                console.warn("No comparison locations found for visual:", visual);
            }

            // Fetch data for each comparison location
            compareLocations.forEach(loc => {
                const locData = this._filterData(loc.id, visual);
                if (locData && locData.length > 0) {
                    compareData = compareData.concat(locData);
                }
            });

            if (visual.location_comparison_type && compareData.length === 0) {
                console.warn("No comparison data found for visual:", visual);
            }
        }

        // Check if this chart's category has a shared axis scale
        let axisScale = null;
        const categoryContainer = container.closest('[data-category-id]');
        if (categoryContainer && categoryContainer.dataset.axisScale) {
            try {
                const categoryScale = JSON.parse(categoryContainer.dataset.axisScale);
                // Only apply to line and column charts
                if (['line', 'column'].includes(visual.data_visual_type)) {
                    axisScale = categoryScale;
                }
            } catch (e) {
                console.error('Error parsing axis scale:', e);
            }
        }

        // Render the appropriate chart type
        this._renderChart(visual, container, tableContainer, indicator, location,
            indicatorData, compareLocations, compareData, axisScale);
    }

    /**
     * Filters indicator values using indexed lookup.
     *
     * Much faster than linear search through all values.
     *
     * @param {String} locationId - The location ID to filter for
     * @param {Object} visual - The data visual configuration
     * @returns {Array} Filtered indicator values
     */
    _filterData(locationId, visual) {
        // Use indexed lookup: O(1) instead of O(n)
        const byIndicator = this.valueIndex[visual.indicator_id];
        if (!byIndicator) return [];

        const byLocation = byIndicator[locationId];
        if (!byLocation) return [];

        const bySource = byLocation[visual.source_id];
        if (!bySource) return [];

        // For line charts, return all dates
        if (visual.data_visual_type === 'line') {
            return bySource;
        }

        // For other chart types, filter by date
        return bySource.filter(d => {
            // Match start_date if visual has one
            const startDateMatch = !visual.start_date || d.start_date === visual.start_date;
            // Match end_date if visual has one
            const endDateMatch = !visual.end_date || d.end_date === visual.end_date;
            return startDateMatch && endDateMatch;
        });
    }

    /**
     * Renders a chart of the appropriate type.
     *
     * @param {Object} visual - The data visual configuration
     * @param {Element} container - The chart container element
     * @param {Element} tableContainer - The data table container element (optional)
     * @param {Object} indicator - The indicator object
     * @param {Object} location - The primary location object
     * @param {Array} indicatorData - The indicator data for primary location
     * @param {Array} compareLocations - The comparison locations
     * @param {Array} compareData - The comparison data
     * @param {Object} axisScale - Optional shared axis scale {min, max}
     */
    _renderChart(visual, container, tableContainer, indicator, location, indicatorData,
        compareLocations, compareData, axisScale) {

        // Chart options
        const chartOptions = {
            animation: false,
            textStyle: {
                fontFamily: 'inherit',
                fontSize: 16,
                color: '#000'
            },
            ...this.options
        };

        // Render based on visual type
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
                    this.filterOptions,
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
                    this.filterOptions,
                    this.colorScales,
                    visual.location_comparison_type,
                    chartOptions,
                    axisScale
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
                        this.filterOptions,
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
                    this.filterOptions,
                    this.locationTypes,
                    this.colorScales,
                    chartOptions,
                    axisScale
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
                        this.filterOptions,
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
                    this.filterOptions,
                    this.locationTypes,
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
                    this.filterOptions,
                    this.locationTypes,
                    this.colorScales,
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
                        this.filterOptions,
                        chartOptions
                    );
                }
                break;

            default:
                console.error("Unknown data visual type:", visual.data_visual_type);
                container.innerHTML = 'Unsupported chart type';
        }
    }
}
