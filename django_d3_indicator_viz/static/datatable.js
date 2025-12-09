import { formatData, showAggregateNotice, buildAggregateNotice } from "./utils.js";

/**
 * The DataTable visualization.
 */
export default class DataTable {

    /**
     * Creates a DataTable visualization.
     * 
     * @param {Object} visual the visual object
     * @param {Element} container the container element
     * @param {Object} indicator the indicator object
     * @param {Object} location the location object
     * @param {Array} indicatorData the indicator data object
     * @param {Array} compareLocations the comparison locations
     * @param {Array} compareData the comparison data
     * @param {Array} filterOptions the filter options
     * @param {Object} chartOptions the chart options for echarts
     */
    constructor(visual, container, indicator, location, indicatorData, compareLocations, compareData, filterOptions, 
        chartOptions = {}) {
        
        this.visual = visual;
        this.container = container;
        this.indicator = indicator;
        this.location = location;
        this.indicatorData = indicatorData;
        this.compareLocations = compareLocations;
        this.compareData = compareData;
        this.filterOptions = filterOptions;
        this.chartOptions = chartOptions;

        this.draw();
    }

    /**
     * Draws a DataTable visual.
     */
    draw() {
        if (!this.indicatorData || !this.indicatorData.length) {
            this.container.innerHTML = 'No data';
            return;
        }

        // set up the table and header
        let table = this.container.querySelector('table');
        let thead = document.createElement('thead');
        let headerRow = document.createElement('tr');
        let headers = ['Column', this.location.name, ...this.compareLocations.map(loc => loc.name)];
        headers.forEach((header, index) => {
            let th = document.createElement('th');
            if (index > 0) {
                th.colSpan = 4;
            }
            th.textContent = header;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);
        table.appendChild(thead);

        // set up the table body
        let tbody = document.createElement('tbody');

        // Add source row
        let sourceRow = document.createElement('tr');
        sourceRow.innerHTML = `<td class="name">Source</td><td colspan="${(headers.length * 4) - (headers.length - 1) - 1}">${this.visual.source_name || 'N/A'}</td>`;
        tbody.appendChild(sourceRow);

        // Add universe row
        if (this.indicatorData[0] && this.indicatorData[0].universe) {
            let universeRow = document.createElement('tr');
            universeRow.innerHTML = `<td class="name">Universe</td><td colspan="${(headers.length * 4) - (headers.length - 1) - 1}">${formatData(this.indicatorData[0].universe, null)}</td>`;
            tbody.appendChild(universeRow);
        }

        let filterOptions = this.indicatorData.map(item => {
            let option = this.filterOptions.find(o => o.id === item.filter_option_id)?.name;
            if (!option) {
                option = item.end_date.substring(0, 4);
            }
            return option;
        });
        let aggregateNoticePresent = false;
        filterOptions.forEach((option, index) => {
            let row = document.createElement('tr');
            let cell = document.createElement('td');
            cell.className = 'name';
            cell.textContent = option;
            row.appendChild(cell);
            
            let valueCell = document.createElement('td');
            valueCell.className = 'value';
            valueCell.textContent = formatData(this.indicatorData[index].value, this.indicator.formatter);
            if (showAggregateNotice(this.indicatorData[index])) {
                valueCell.innerHTML += '*';
                aggregateNoticePresent = true;
            }
            row.appendChild(valueCell);
            let valueMoeCell = document.createElement('td');
            valueMoeCell.className = 'context';
            let valueMoePlusMinus = document.createElement('span');
            valueMoePlusMinus.innerHTML = '&plusmn;';
            valueMoeCell.appendChild(valueMoePlusMinus);
            let valueMoe = document.createElement('span');
            valueMoe.textContent = formatData(this.indicatorData[index].value_moe, this.indicator.formatter);
            valueMoeCell.appendChild(valueMoe);
            row.appendChild(valueMoeCell);

            let countCell = document.createElement('td');
            countCell.textContent = formatData(this.indicatorData[index].count, null);
            row.appendChild(countCell);
            let countMoeCell = document.createElement('td');
            countMoeCell.className = 'context';
            let countMoePlusMinus = document.createElement('span');
            countMoePlusMinus.innerHTML = '&plusmn;';
            countMoeCell.appendChild(countMoePlusMinus);
            let countMoe = document.createElement('span');
            countMoe.textContent = formatData(this.indicatorData[index].count_moe, null);
            countMoeCell.appendChild(countMoe);
            row.appendChild(countMoeCell);

            this.compareLocations.forEach((loc, locIndex) => {
                let valueCell = document.createElement('td');
                valueCell.className = 'value';
                let compareDataItem = this.compareData.find(d => d.location_id === loc.id 
                    && ((!d.filter_option_id  || d.filter_option_id === this.indicatorData[index].filter_option_id)
                    && d.end_date === this.indicatorData[index].end_date)
                );
                valueCell.textContent = formatData(compareDataItem.value, this.indicator.formatter);
                row.appendChild(valueCell);
                let valueMoeCell = document.createElement('td');
                valueMoeCell.className = 'context';
                let valueMoePlusMinus = document.createElement('span');
                valueMoePlusMinus.innerHTML = '&plusmn;';
                valueMoeCell.appendChild(valueMoePlusMinus);
                let valueMoe = document.createElement('span');
                valueMoe.textContent = formatData(compareDataItem.value_moe, this.indicator.formatter);
                valueMoeCell.appendChild(valueMoe);
                row.appendChild(valueMoeCell);
                let countCell = document.createElement('td');
                countCell.textContent = formatData(compareDataItem.count, null);
                row.appendChild(countCell);
                let countMoeCell = document.createElement('td');
                countMoeCell.className = 'context';
                let countMoePlusMinus = document.createElement('span');
                countMoePlusMinus.innerHTML = '&plusmn;';
                countMoeCell.appendChild(countMoePlusMinus);
                let countMoe = document.createElement('span');
                countMoe.textContent = formatData(compareDataItem.count_moe, null);
                countMoeCell.appendChild(countMoe);
                row.appendChild(countMoeCell);
            });
            
            tbody.appendChild(row);
        });
        table.appendChild(tbody);

        if (aggregateNoticePresent) {
            let footer = document.createElement('tfoot');
            let footerRow = document.createElement('tr');
            let footerCell = document.createElement('td');
            footerCell.colSpan = headers.length * 4 - (headers.length - 1);
            footerCell.appendChild(buildAggregateNotice());
            footerRow.appendChild(footerCell);
            footer.appendChild(footerRow);
            table.appendChild(footer);
        }
    }
}