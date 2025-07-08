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
        let valueEl = document.createElement('div');
        valueEl.className = 'ban-value';
        valueEl.style.fontSize = (this.chartOptions.textStyle?.fontSize || 16) * 3 + 'px';
        valueEl.textContent = formatData(this.indicatorData, this.visual.value_field);
        let indicatorEl = document.createElement('div');
        indicatorEl.className = 'ban-indicator';
        indicatorEl.textContent = this.indicator.name;
        this.container.appendChild(indicatorEl);
        this.container.appendChild(valueEl);
        if (this.visual.location_comparison_type) {
            this.compareLocations.forEach((loc, index) => {
                let compareEl = document.createElement('div');
                compareEl.className = 'ban-compare';
                compareEl.style.fontSize = (this.chartOptions.textStyle?.fontSize || 16)  * 0.75 + 'px';
                compareEl.textContent = loc.name + ": " + formatData(this.compareData.find(d => d.location_id === loc.id), this.visual.value_field);
                this.container.appendChild(compareEl);
            });
        }
    }
}