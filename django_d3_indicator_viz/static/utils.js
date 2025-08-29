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
 * Format data based on the value field.
 * 
 * @param {Object} data - The data to be formatted.
 * @param {string} value_field - The field in the data to be used as the value.
 * @returns {string} The formatted value.
 * @param {boolean} [round=false] - Whether to round the value.
 */
function formatData(data, value_field, round = false) {
    if (!data || !data[value_field]) {
        return 'No data';
    }
    switch (value_field) {
        case 'percentage':
        case 'percentage_moe':
            let formattedValue = (round ? Math.round(data[value_field]) : data[value_field]) + '%';
            if (value_field === 'percentage' && data.count_moe && data.count && data.count_moe > (data.count / 10)) {
                formattedValue += '†';
            }
            return formattedValue;
        case 'dollars':
        case 'dollars_moe':
            return '$' + Number(data[value_field]).toLocaleString();
        case 'count':
        case 'count_moe':
        case 'universe':
        case 'universe_moe':
        case 'rate':
        case 'rate_moe':
        case 'index':
        case 'index_moe':
            return Number(data[value_field]).toLocaleString();
        default:
            return data[value_field];
    }
}

/**
 * Build the content for a tooltip.
 * 
 * @param {string} name - The name to be displayed in the tooltip.
 * @param {Object} data - The data to be displayed in the tooltip.
 * @param {string} value_field - The field in the data to be shown as the value.
 * @param {Array} compareLocations - An array of locations to compare against.
 * @param {Array} compareData - The data for the locations to compare against.
 */
function buildTooltipContent(name, data, value_field, compareLocations, compareData) {
    let tooltipContent = `<div class='tooltip-value'><strong>${name}</strong>: ${formatData(data, value_field)}</div>`;
    if (compareLocations) {
        compareLocations.forEach((location, index) => {
            let locationData = compareData.find(d => d.location_id === location.id 
                && data.filter_option_id === d.filter_option_id
                && data.end_date === d.end_date);
            if (locationData) {
                let comparisonPhrases = getComparisonPhrases(data[value_field], locationData[value_field]);
                tooltipContent += `<div class='tooltip-comparison'><strong>${comparisonPhrases[0]}</strong> ${comparisonPhrases[1]} the rate in ${location.name}: ${formatData(locationData, value_field)}</div>`;
            } else {
                tooltipContent += `<div class='tooltip-comparison'><strong>No comparison available</strong> for ${location.name}</div>`;
            }
        });
    }
    if (value_field === 'percentage' && data.count_moe && data.count && data.count_moe > (data.count / 10)) {
        tooltipContent += '<div class="tooltip-moe-note">†Margin of error at least 10% of total value</div>';
    }

    return tooltipContent;
}

/**
 * Get comparison phrases based on the base and comparison values.
 *
 * @param {Number} baseValue the base value
 * @param {Number} comparisonValue the comparison value
 * @returns {Array} An array containing the comparison phrases.
 */
function getComparisonPhrases(baseValue, comparisonValue) {
    let phrases = {
        206: ["more than double", ""],
        195: ["about double", ""],
        180: ["nearly double", ""],
        161: ["more than 1.5 times", ""],
        145: ["about 1.5 times", ""],
        135: ["about 1.4 times", ""],
        128: ["about 1.3 times", ""],
        122: ["about 25 percent higher", "than"],
        115: ["about 20 percent higher", "than"],
        107: ["about 10 percent higher", "than"],
        103: ["a little higher", "than"],
        98: ["about the same as", ""],
        94: ["a little less", "than"],
        86: ["about 90 percent", "of"],
        78: ["about 80 percent", "of"],
        72: ["about three-quarters", "of"],
        64: ["about two-thirds", "of"],
        56: ["about three-fifths", "of"],
        45: ["about half", ""],
        37: ["about two-fifths", "of"],
        30: ["about one-third", "of"],
        23: ["about one-quarter", "of"],
        17: ["about one-fifth", "of"],
        13: ["less than a fifth", "of"],
        8: ["about 10 percent", "of"],
        0: ["less than 10 percent", "of"],
    };

    let index = baseValue / comparisonValue * 100;
    
    return phrases[Object.keys(phrases).findLast(key => index >= key)]
}

/**
 * Represents the types of location comparisons that can be made in the data visualization.
 */
const DataVisualLocationComparisonType = {
    PARENTS: 'parents',
    SIBLINGS: 'siblings'
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
    DataVisualLocationComparisonType 
};