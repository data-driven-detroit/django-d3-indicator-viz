/**
 * Chart Connector
 *
 * Simple connector between template data and chart drawing code.
 * Finds chart containers, filters data, and calls the appropriate chart class.
 */

import Ban from './ban.js';
import ColumnChart from './columnchart.js';
import LineChart from './linechart.js';
import MinMedMaxChart from './minmedmaxchart.js';
import DonutChart from './donutchart.js';
import DataTable from './datatable.js';


/**
 * Draw all charts in a container.
 */

function drawCharts(container = document) {
    // Find all sections with indicator values
    const sections = container.querySelectorAll('article[data-indicator-values]');

    sections.forEach(section => {
        // Skip if already drawn
        if (section.dataset.chartsDrawn === 'true') return;

        // Parse indicator values
        const allValues = JSON.parse(section.dataset.indicatorValues);

        // Find all chart containers in this section
        const chartContainers = section.querySelectorAll('.chart-container[data-indicator-id]');

        chartContainers.forEach(chartContainer => {
            drawChart(chartContainer, allValues);
        });

        // Mark as drawn
        section.dataset.chartsDrawn = 'true';
    });
}

/**
 * Draw a single chart.
 */
function drawChart(container, allValues) {
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

    // Filter values for this indicator and source
    const indicatorValues = allValues.filter(v =>
        v.indicator === indicatorId && v.source === sourceId
    );

    if (!indicatorValues.length) {
        container.innerHTML = '<p>No data available</p>';
        return;
    }

    // Get primary location
    const primaryLocation = window.profileData.locations.primary;

    // Filter for primary location
    const primaryValues = indicatorValues.filter(v => v.location === primaryLocation.id);

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
        const compareLocationIds = compareLocations.map(loc => loc.id);
        compareValues = indicatorValues.filter(v => compareLocationIds.includes(v.location));
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
                null  // axisScale - could read from category container if needed
            );
            break;

        case 'line':
            new LineChart(
                visual,
                container,
                indicator,
                primaryLocation,
                primaryValues,  // Time series
                compareLocations,
                compareValues,
                window.profileData.filterOptions,
                window.profileData.locationTypes,
                window.profileData.colorScales,
                chartOptions,
                null  // axisScale
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
}

// Listen for HTMX events
document.body.addEventListener('htmx:afterSettle', function(evt) {
    drawCharts(evt.detail.target);
});

// Draw on page load
document.addEventListener('DOMContentLoaded', function() {
    drawCharts();
});

// Export for manual usage
export default { drawAll: drawCharts };
