/**
 * Chart Connector
 *
 * Simple connector between template data and chart drawing code.
 * Finds chart containers, filters data, and calls the appropriate chart class.
 */
import Ban from './ban.js';
import ColumnChart from './columnchart.js';
import LineChart from './linechart.js';
import MultiLineChart from './multilinechart.js';
import TimeLineChart from './timelinechart.js';
import MinMedMaxChart from './minmedmaxchart.js';
import DonutChart from './donutchart.js';
import DataTable from './datatable.js';


/**
 * Compute shared y-axis scales for percentage indicators grouped by category.
 *
 * Returns a Map of categoryId -> { min: 0, max: roundedMax }
 */
function computeCategoryScales(section, allValues) {
    const scales = new Map();
    const categories = section.querySelectorAll('.section-container[data-category-id]');

    categories.forEach(category => {
        const categoryId = category.dataset.categoryId;
        const pctContainers = category.querySelectorAll('.chart-container[data-indicator-type="percentage"]');

        if (pctContainers.length === 0) return;

        // Collect all indicator/source pairs for percentage charts in this category
        const keys = new Set();
        pctContainers.forEach(c => {
            keys.add(`${c.dataset.indicatorId}:${c.dataset.sourceId}`);
        });

        // Find global max across all matching values
        let globalMax = 0;
        allValues.forEach(v => {
            if (keys.has(`${v.indicator_id}:${v.source_id}`) && v.value != null) {
                globalMax = Math.max(globalMax, v.value);
            }
        });

        // Round up to nearest 5 for clean tick marks
        const roundedMax = Math.ceil(globalMax / 5) * 5;

        scales.set(categoryId, { min: 0, max: roundedMax });
    });

    return scales;
}

/**
 * Draw all charts in a container.
 */

function drawCharts(container = document) {
    // Find all sections with indicator values
    let sections = Array.from(container.querySelectorAll('article[data-indicator-values]'));

    // If the container itself is an article with indicator values, include it
    if (container.matches && container.matches('article[data-indicator-values]')) {
        sections.push(container);
    }

    sections.forEach(section => {
        // Skip if already drawn
        if (section.dataset.chartsDrawn === 'true') return;

        // Parse indicator values
        const allValues = JSON.parse(section.dataset.indicatorValues);

        // Compute shared y-axis scales for percentage indicators per category
        const categoryScales = computeCategoryScales(section, allValues);

        // Find all chart containers in this section
        const chartContainers = section.querySelectorAll('.chart-container[data-indicator-id]');

        chartContainers.forEach(chartContainer => {
            drawChart(chartContainer, allValues, categoryScales);
        });

        // Mark as drawn
        section.dataset.chartsDrawn = 'true';
    });
}

/**
 * Draw a single chart.
 */
function drawChart(container, allValues, categoryScales) {
    // Get chart config from data attributes
    const indicatorId = parseInt(container.dataset.indicatorId);
    const visualType = container.dataset.visualType;
    const sourceId = parseInt(container.dataset.sourceId);
    const comparisonType = container.dataset.comparisonType || null;
    const colorScaleId = container.dataset.colorScaleId ? parseInt(container.dataset.colorScaleId) : null;

    // Get indicator metadata from data attributes
    const indicator = {
        id: indicatorId,
        formatter: container.dataset.formatter || '{value}',
        indicator_type: container.dataset.indicatorType,
        rate_per: container.dataset.ratePer ? parseInt(container.dataset.ratePer) : null,
    };

    // Filter values for this indicator and source (coerce types — JSON values
    // may be strings while dataset attributes are parsed as numbers, or vice-versa)
    const indicatorValues = allValues.filter(v =>
        Number(v.indicator_id) === indicatorId && Number(v.source_id) === sourceId
    );

    if (!indicatorValues.length) {
        container.innerHTML = '<p>No data available</p>';
        return;
    }

    // Get primary location
    const primaryLocation = window.profileData.locations.primary;

    // Filter for primary location (coerce to string for safe comparison)
    const primaryValues = indicatorValues.filter(v => String(v.location_id) === String(primaryLocation.id));

    // Get comparison locations if needed
    let compareLocations = [];
    let compareValues = [];

    if (comparisonType === 'parents') {
        compareLocations = window.profileData.locations.parents || [];
    } else if (comparisonType === 'siblings') {
        compareLocations = window.profileData.locations.siblings || [];
    }

    // Filter for comparison locations
    if (compareLocations.length > 0) {
        const compareLocationIds = compareLocations.map(loc => String(loc.id));
        compareValues = indicatorValues.filter(v => compareLocationIds.includes(String(v.location_id)));
    }

    // Get color scale if specified
    let colorScale = null;
    if (colorScaleId) {
        colorScale = window.profileData.colorScales.find(cs => cs.id === colorScaleId);
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

    // Visual config object
    const visual = {
        id: 0,
        indicator_id: indicatorId,
        data_visual_type: visualType,
        source_id: sourceId,
        location_comparison_type: comparisonType,
        color_scale_id: colorScaleId,
    };

    // Look up shared axis scale for percentage indicators in this category
    let axisScale = null;
    if (indicator.indicator_type === 'percentage') {
        const categoryEl = container.closest('[data-category-id]');
        if (categoryEl && categoryScales) {
            axisScale = categoryScales.get(categoryEl.dataset.categoryId) || null;
        }
    }

    // Draw the appropriate chart type
    switch (visualType) {
        case 'ban':
            new Ban(
                visual,
                container,
                indicator,
                primaryLocation,
                primaryValues[0],  // Single value
                compareLocations,
                compareValues,
                window.profileData.filterOptions,
                chartOptions
            );
            break;

        case 'column':
            new ColumnChart(
                visual,
                container,
                indicator,
                primaryLocation,
                primaryValues,  // Array of values
                compareLocations,
                compareValues,
                window.profileData.filterOptions,
                window.profileData.colorScales,
                comparisonType,
                chartOptions,
                axisScale
            );
            break;

        case 'line':
        case 'multiline':
            new TimeLineChart(
                visual,
                container,
                indicator,
                primaryLocation,
                primaryValues,
                compareLocations,
                compareValues,
                window.profileData.filterOptions,
                window.profileData.locationTypes,
                window.profileData.colorScales,
                chartOptions,
                axisScale
            );
            break;

        case 'min_med_max':
            new MinMedMaxChart(
                visual,
                container,
                indicator,
                primaryLocation,
                primaryValues[0],  // Single value
                compareLocations,
                compareValues,
                window.profileData.filterOptions,
                window.profileData.locationTypes,
                chartOptions
            );
            break;

        case 'donut':
            new DonutChart(
                visual,
                container,
                indicator,
                primaryLocation,
                primaryValues,  // Array of segments
                compareLocations,
                compareValues,
                window.profileData.filterOptions,
                window.profileData.locationTypes,
                window.profileData.colorScales,
                chartOptions
            );
            break;

        default:
            container.innerHTML = `<p>Unknown chart type: ${visualType}</p>`;
    }

    // Create data table for chart types that support it (not ban or min_med_max)
    if (['column', 'line', 'multiline', 'donut'].includes(visualType)) {
        const tableContainer = document.getElementById(`indicator-${indicatorId}-datatable-container`);
        if (tableContainer) {
            new DataTable(
                visual,
                tableContainer,
                indicator,
                primaryLocation,
                primaryValues,
                compareLocations,
                compareValues,
                window.profileData.filterOptions,
                chartOptions
            );
        }
    }
}

// Listen for HTMX events - htmx:load fires on the newly loaded content
document.body.addEventListener('htmx:load', function(evt) {
    drawCharts(evt.detail.elt);
});

// Draw on page load
document.addEventListener('DOMContentLoaded', function() {
    drawCharts();
});

// Export for manual usage
export default { drawAll: drawCharts };
