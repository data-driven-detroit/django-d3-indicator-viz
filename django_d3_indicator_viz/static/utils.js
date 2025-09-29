/**
 * Get the visual container element.
 * 
 * @param {number} indicatorId - The indicator ID
 * @param {String} dataVisual - The data visual type
 */
function getVisualContainer(indicatorId, dataVisualType) {
    return document.getElementById('indicator-' + indicatorId + '-' + dataVisualType + '-container');
}

/**
 * Get the table container element for a specific indicator.
 * 
 * @param {number} indicatorId - The indicator ID
 * @return {Element} The table container element
 */
function getTableContainer(indicatorId) {
    return document.getElementById('indicator-' + indicatorId + '-datatable-container');
}

/**
 * Format a number.
 * 
 * @param {number} number - The number to be formatted.
 * @param {string} formatter - The formatter string.
 * @param {boolean} [round=false] - Whether to round the value.
 * @returns {string} The formatted value.
 */
function formatData(number, formatter, round = false) {
    if (number === null) {
        return 'No data';
    }
    let valueToFormat = round ? Math.round(number) : number;
    if (formatter) {
        return formatter.replace('{value}', valueToFormat.toLocaleString());
    } else {
        return valueToFormat.toLocaleString();
    }
}

/**
 * Build the content for a tooltip.
 * 
 * @param {string} name - The name to be displayed in the tooltip.
 * @param {Object} data - The data to be displayed in the tooltip.
 * @param {Object} indicator - The indicator object.
 * @param {Array} compareLocations - An array of locations to compare against.
 * @param {Array} compareData - The data for the locations to compare against.
 */
function buildTooltipContent(name, data, indicator, compareLocations, compareData) {
    let showAggregateNotice = data.values_considered 
            && data.values_aggregated 
            && data.values_considered > data.values_aggregated;
    let tooltipContent = `<div class='tooltip-value'>
        <strong>${name}</strong>: 
        ${formatData(data.value, indicator.formatter, true)}${showAggregateNotice ? '*' : ''}
    </div>`;
    if (compareLocations) {
        compareLocations.forEach((location, index) => {
            let locationData = compareData.find(d => d.location_id === location.id 
                && data.filter_option_id === d.filter_option_id
                && data.end_date === d.end_date);
            if (locationData) {
                let comparisonPhrases = getComparisonPhrases(data.value, locationData.value, indicator.indicator_type);
                tooltipContent += `<div class='tooltip-comparison'>
                    <strong>${comparisonPhrases[0]}</strong> 
                    ${comparisonPhrases[1]} ${comparisonPhrases[2]} ${location.name}: 
                    ${formatData(locationData.value, indicator.formatter, true)}
                </div>`;
            } else {
                tooltipContent += `<div class='tooltip-comparison'>
                    <strong>No comparison available</strong> for ${location.name}
                </div>`;
            }
        });
    }
    if (indicator.indicator_type === 'percentage' 
        && data.count_moe 
        && data.count 
        && data.count_moe > (data.count / 10)) {
        
            tooltipContent += '<div class="tooltip-moe-note">†Margin of error at least 10% of total value</div>';
    }
    if (showAggregateNotice) {
        tooltipContent += buildAggregateNotice(data.values_considered, data.values_aggregated).outerHTML;
    }

    return tooltipContent;
}

/**
 * Get comparison phrases based on the base and comparison values.
 *
 * @param {Number} baseValue the base value
 * @param {Number} comparisonValue the comparison value
 * @param {String} indicatorType the type of indicator being compared (e.g., 'percentage', 'rate', etc.)
 * @returns {Array} An array containing the comparison phrases.
 */
function getComparisonPhrases(baseValue, comparisonValue, indicatorType) {
    let valueFieldPhrase = ' the value in ';
    switch (indicatorType) {
        case 'percentage':
            valueFieldPhrase = ' the rate in ';
            break;
        case 'rate':
        case 'index':
            valueFieldPhrase = ' the figure in ';
            break;
        case 'median':
        case 'average':
            valueFieldPhrase = ' the amount in ';
            break;
    }
    let phrases = {
        206: ['more than double', '', valueFieldPhrase],
        195: ['about double', '', valueFieldPhrase],
        180: ['nearly double', '', valueFieldPhrase],
        161: ['more than 1.5 times', '', valueFieldPhrase],
        145: ['about 1.5 times', '', valueFieldPhrase],
        135: ['about 1.4 times', '', valueFieldPhrase],
        128: ['about 1.3 times', '', valueFieldPhrase],
        122: ['about 25 percent higher', 'than', valueFieldPhrase],
        115: ['about 20 percent higher', 'than', valueFieldPhrase],
        107: ['about 10 percent higher', 'than', valueFieldPhrase],
        103: ['a little higher', 'than', valueFieldPhrase],
        98: ['about the same as', '', valueFieldPhrase],
        94: ['a little less', 'than', valueFieldPhrase],
        86: ['about 90 percent', 'of', valueFieldPhrase],
        78: ['about 80 percent', 'of', valueFieldPhrase],
        72: ['about three-quarters', 'of', valueFieldPhrase],
        64: ['about two-thirds', 'of', valueFieldPhrase],
        56: ['about three-fifths', 'of', valueFieldPhrase],
        45: ['about half', '', valueFieldPhrase],
        37: ['about two-fifths', 'of', valueFieldPhrase],
        30: ['about one-third', 'of', valueFieldPhrase],
        23: ['about one-quarter', 'of', valueFieldPhrase],
        17: ['about one-fifth', 'of', valueFieldPhrase],
        13: ['less than a fifth', 'of', valueFieldPhrase],
        8: ['about 10 percent', 'of', valueFieldPhrase],
        0: ['less than 10 percent', 'of', valueFieldPhrase],
    };

    let index = baseValue / comparisonValue * 100;
    
    return phrases[Object.keys(phrases).findLast(key => index >= key)]
}

/**
 * Determine if an aggregate notice should be shown.
 * 
 * @param {Object} data - The data object containing values_considered and values_aggregated.
 * @returns {boolean} True if the aggregate notice should be shown, false otherwise.
 */
function showAggregateNotice(data) {
    return data.values_considered 
            && data.values_aggregated 
            && data.values_considered > data.values_aggregated;
}

/**
 * Build an aggregate notice element.
 * 
 * @param {Number} valuesConsidered - The number of values considered.
 * @param {Number} valuesAggregated - The number of values aggregated.
 * @returns {Element} The aggregate notice element.
 */
function buildAggregateNotice(valuesConsidered, valuesAggregated) {
    let aggregateNoticeEl = document.createElement('div');
    aggregateNoticeEl.className = 'aggregate-notice';
    if (valuesConsidered && valuesAggregated) {
    aggregateNoticeEl.textContent = `*Based on ${valuesAggregated} out of ${valuesConsidered} 
        locations with data available.`;
    } else {
        aggregateNoticeEl.textContent = '*Based on a subset of locations with data available.';
    }
    return aggregateNoticeEl;
}

/**
 * Represents the types of location comparisons that can be made in the data visualization.
 * 
 * PARENTS: compare to larger locations containing the current location (e.g., county to state)
 * SIBLINGS: compare to similar locations at the same level (e.g., county to county)
 */
const DataVisualLocationComparisonType = {
    PARENTS: 'parents',
    SIBLINGS: 'siblings'
}

/**
 * Represents the modes for displaying data visual comparisons.
 * 
 * DATA_VISUAL: comparisons are shown directly in the data visual (e.g., bars within a chart).
 * TOOLTIP: comparisons are shown in the tooltip when hovering over data points.
 */
const DataVisualComparisonMode = {
    DATA_VISUAL: 'data_visual',
    TOOLTIP: 'tooltip'
}

/**
 * Exports utility functions for data visualization.
 */
export {
    getVisualContainer,
    getTableContainer,
    formatData,
    buildTooltipContent,
    getComparisonPhrases,
    showAggregateNotice,
    buildAggregateNotice,
    DataVisualLocationComparisonType,
    DataVisualComparisonMode
};