import { formatData } from "./utils.js";

export default class DataTable {
    constructor(visual, container, indicator, location, indicatorData, compareLocations, compareData, filterOptions, chartOptions = {}) {
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
     *
     * @param {Object} visual - The data visual this data table is based on.
     * @param {Element} container - The data table container element.
     * @param {Object} location - The location.
     * @param {Array} indicatorData - The indicator data.
     * @param {Array} compareLocations - The comparison locations.
     * @param {Array} compareData - The comparison data.
     * @param {Array} filterOptions - The filter options.
     */
    draw() {
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
        
        let tbody = document.createElement('tbody');
        let filterOptions = this.indicatorData.map(item => {
            let option = this.filterOptions.find(o => o.id === item.filter_option_id)?.name;
            if (!option) {
                option = item.end_date.substring(0, 4);
            }
            return option;
        });
        filterOptions.forEach((option, index) => {
            let row = document.createElement('tr');
            let cell = document.createElement('td');
            cell.className = 'name';
            cell.textContent = option;
            row.appendChild(cell);
            
            let valueCell = document.createElement('td');
            valueCell.className = 'value';
            valueCell.textContent = formatData(this.indicatorData[index], this.visual.value_field);
            row.appendChild(valueCell);
            let valueMoeCell = document.createElement('td');
            valueMoeCell.className = 'context';
            let valueMoePlusMinus = document.createElement('span');
            valueMoePlusMinus.innerHTML = '&plusmn;';
            valueMoeCell.appendChild(valueMoePlusMinus);
            let valueMoe = document.createElement('span');
            valueMoe.textContent = formatData(this.indicatorData[index], this.visual.value_field + '_moe');
            valueMoeCell.appendChild(valueMoe);
            row.appendChild(valueMoeCell);

            let countCell = document.createElement('td');
            countCell.textContent = formatData(this.indicatorData[index], 'count');
            row.appendChild(countCell);
            let countMoeCell = document.createElement('td');
            countMoeCell.className = 'context';
            let countMoePlusMinus = document.createElement('span');
            countMoePlusMinus.innerHTML = '&plusmn;';
            countMoeCell.appendChild(countMoePlusMinus);
            let countMoe = document.createElement('span');
            countMoe.textContent = formatData(this.indicatorData[index], 'count_moe');
            countMoeCell.appendChild(countMoe);
            row.appendChild(countMoeCell);

            this.compareLocations.forEach((loc, locIndex) => {
                let valueCell = document.createElement('td');
                valueCell.className = 'value';
                let compareDataItem = this.compareData.find(d => d.location_id === loc.id 
                    && ((!d.filter_option_id  || d.filter_option_id === this.indicatorData[index].filter_option_id)
                    && d.end_date === this.indicatorData[index].end_date)
                );
                valueCell.textContent = formatData(compareDataItem, this.visual.value_field);
                row.appendChild(valueCell);
                let valueMoeCell = document.createElement('td');
                valueMoeCell.className = 'context';
                let valueMoePlusMinus = document.createElement('span');
                valueMoePlusMinus.innerHTML = '&plusmn;';
                valueMoeCell.appendChild(valueMoePlusMinus);
                let valueMoe = document.createElement('span');
                valueMoe.textContent = formatData(compareDataItem, this.visual.value_field + '_moe');
                valueMoeCell.appendChild(valueMoe);
                row.appendChild(valueMoeCell);
                let countCell = document.createElement('td');
                countCell.textContent = formatData(compareDataItem, 'count');
                row.appendChild(countCell);
                let countMoeCell = document.createElement('td');
                countMoeCell.className = 'context';
                let countMoePlusMinus = document.createElement('span');
                countMoePlusMinus.innerHTML = '&plusmn;';
                countMoeCell.appendChild(countMoePlusMinus);
                let countMoe = document.createElement('span');
                countMoe.textContent = formatData(compareDataItem, 'count_moe');
                countMoeCell.appendChild(countMoe);
                row.appendChild(countMoeCell);
            });
            
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
    }
}