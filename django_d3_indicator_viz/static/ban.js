import { formatData } from "./utils.js";

export default class Ban {
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
        
        window.addEventListener('resize', () => {
            this.draw();
        });
    }

    /**
     * Draws a BAN visual.
     * 
     * @param {Object} visual - The data visual.
     * @param {Element} container - The data visual container element.
     * @param {Object} location - The location.
     * @param {Array} indicatorData - The indicator data.
     * @param {Array} compareLocations - The comparison locations.
     * @param {Array} compareData - The comparison data.
     * @param {Array} filterOptions - The filter options.
     */
    draw() {
        this.container.innerHTML = '';
        this.container.classList.add('ban-container');
        this.container.style.fontFamily = this.chartOptions.textStyle?.fontFamily;
        let valueContainerEl = document.createElement('div');
        valueContainerEl.className = 'ban-value-container';
        let valueEl = document.createElement('span');
        valueEl.className = 'ban-value';
        valueEl.style.fontSize = (this.chartOptions.textStyle?.fontSize || 16) * 3 + 'px';
        valueEl.textContent = formatData(this.indicatorData, this.visual.value_field);
        valueContainerEl.appendChild(valueEl);
        if (this.indicatorData[this.visual.value_field + '_moe']) {
            let moePlusMinusEl = document.createElement('span');
            moePlusMinusEl.className = 'ban-moe';
            moePlusMinusEl.innerHTML = '&plusmn;';
            valueContainerEl.appendChild(moePlusMinusEl);
            let moeEl = document.createElement('span');
            moeEl.className = 'ban-moe';
            moeEl.textContent = formatData(this.indicatorData, this.visual.value_field + '_moe');
            valueContainerEl.appendChild(moeEl);
        }
        this.container.appendChild(valueContainerEl);
        if (this.visual.location_comparison_type) {
            this.compareLocations.forEach((loc, index) => {
                let compareEl = document.createElement('div');
                compareEl.className = 'ban-compare';
                compareEl.style.fontSize = (this.chartOptions.textStyle?.fontSize || 16)  * 0.75 + 'px';
                let compareLocEl = document.createElement('strong');
                compareLocEl.className = 'ban-compare-location';
                compareLocEl.textContent = loc.name + ': ';
                compareEl.appendChild(compareLocEl);
                let compareValEl = document.createElement('span');
                compareValEl.className = 'ban-compare-value';
                let locCompareData = this.compareData.find(d => d.location_id === loc.id)
                compareValEl.textContent = formatData(locCompareData, this.visual.value_field);
                compareEl.appendChild(compareValEl);
                if (locCompareData[this.visual.value_field + '_moe']) {
                    let compareMoePlusMinusEl = document.createElement('span');
                    compareMoePlusMinusEl.className = 'ban-compare-moe';
                    compareMoePlusMinusEl.innerHTML = '&plusmn;';
                    compareEl.appendChild(compareMoePlusMinusEl);
                    let compareMoeEl = document.createElement('span');
                    compareMoeEl.className = 'ban-compare-moe';
                    compareMoeEl.textContent = formatData(locCompareData, this.visual.value_field + '_moe');
                    compareEl.appendChild(compareMoeEl);
                }
                this.container.appendChild(compareEl);
            });
        }
    }
}