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
 * Format data based on the value field.
 * 
 * @param {Object} data - The data to be formatted.
 * @param {string} value_field - The field in the data to be used as the value.
 * @returns {string} The formatted value.
 */
function formatData(data, value_field) {
    if (!data || !data[value_field]) {
        return 'No data';
    }
    switch (value_field) {
        case 'percentage':
        case 'percentage_moe':
            return data[value_field] + '%';
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

const DataVisualLocationComparisonType = {
    PARENTS: 'parents',
    SIBLINGS: 'siblings'
}

export { getVisualContainer, formatData, DataVisualLocationComparisonType };