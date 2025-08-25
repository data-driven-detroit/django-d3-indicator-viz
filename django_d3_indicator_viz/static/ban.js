import { formatData, getComparisonPhrases } from "./utils.js";

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
        let moeContainers = [];
        if (this.indicatorData[this.visual.value_field + '_moe']) {
            let moeContainerEl = document.createElement('span');
            moeContainerEl.className = 'ban-moe';
            let moePlusMinusEl = document.createElement('span');
            moePlusMinusEl.innerHTML = '&plusmn;';
            let moeEl = document.createElement('span');
            moeEl.textContent = formatData(this.indicatorData, this.visual.value_field + '_moe');
            moeContainerEl.appendChild(moePlusMinusEl);
            moeContainerEl.appendChild(moeEl);
            valueContainerEl.appendChild(moeContainerEl);
            if (this.visual.value_field === 'percentage') {
                let countContainerEl = document.createElement('span');
                let countEl = document.createElement('span');
                countEl.className = 'ban-moe';
                countEl.textContent = '(' + formatData(this.indicatorData, 'count');
                countContainerEl.appendChild(countEl);
                let countMoeEl = document.createElement('span');
                countMoeEl.className = 'ban-compare-moe';
                countMoeEl.textContent = ' ± ' + formatData(this.indicatorData, 'count_moe') + ')';
                countContainerEl.appendChild(countMoeEl);
                moeContainerEl.appendChild(countContainerEl);
            }
            moeContainers.push(moeContainerEl);
        }
        this.container.appendChild(valueContainerEl);
        
        if (this.visual.location_comparison_type) {
            this.compareLocations.forEach((loc, index) => {
                let locCompareData = this.compareData.find(d => d.location_id === loc.id)
                let compareEl = document.createElement('div');
                compareEl.className = 'ban-compare';
                compareEl.style.fontSize = (this.chartOptions.textStyle?.fontSize || 16)  * 0.75 + 'px';
                if (this.visual.value_field === 'percentage') {
                    let phrases = getComparisonPhrases(this.indicatorData[this.visual.value_field], locCompareData[this.visual.value_field]);
                    let comparePhraseEl = document.createElement('strong');
                    comparePhraseEl.className = 'ban-compare-phrase';
                    comparePhraseEl.textContent = phrases[0];
                    compareEl.appendChild(comparePhraseEl);
                    if (phrases[1]) {
                        let comparePhraseEl2 = document.createElement('span');
                        comparePhraseEl2.className = 'ban-compare-phrase';
                        comparePhraseEl2.textContent = phrases[1];
                        comparePhraseEl.appendChild(comparePhraseEl2);
                        compareEl.appendChild(comparePhraseEl2);
                    }
                    let comparePhraseEl3 = document.createElement('span');
                    comparePhraseEl3.className = 'ban-compare-phrase';
                    comparePhraseEl3.textContent = ' the rate in ';
                    compareEl.appendChild(comparePhraseEl3);
                }
                let compareLocEl;
                if (this.visual.value_field === 'percentage') {
                    compareLocEl = document.createElement('span');
                } else {
                    compareLocEl = document.createElement('strong');
                }
                compareLocEl.className = 'ban-compare-location';
                compareLocEl.textContent = loc.name + ': ';
                compareEl.appendChild(compareLocEl);
                let compareValEl = document.createElement('span');
                compareValEl.className = 'ban-compare-value';
                compareValEl.textContent = formatData(locCompareData, this.visual.value_field);
                compareEl.appendChild(compareValEl);
                if (locCompareData[this.visual.value_field + '_moe']) {
                    let compareMoeContainer = document.createElement('span');
                    compareMoeContainer.className = 'ban-compare-moe';
                    let compareMoePlusMinusEl = document.createElement('span');
                    compareMoePlusMinusEl.innerHTML = '&plusmn;';
                    compareMoeContainer.appendChild(compareMoePlusMinusEl);
                    let compareMoeEl = document.createElement('span');
                    compareMoeEl.textContent = formatData(locCompareData, this.visual.value_field + '_moe');
                    compareMoeContainer.appendChild(compareMoeEl);
                    compareEl.appendChild(compareMoeContainer);
                    if (this.visual.value_field === 'percentage') {
                        let countContainerEl = document.createElement('span');
                        let countEl = document.createElement('span');
                        countEl.className = 'ban-moe';
                        countEl.textContent = '(' + formatData(locCompareData, 'count');
                        countContainerEl.appendChild(countEl);
                        let countMoeEl = document.createElement('span');
                        countMoeEl.className = 'ban-compare-moe';
                        countMoeEl.textContent = ' ± ' + formatData(locCompareData, 'count_moe') + ')';
                        countContainerEl.appendChild(countMoeEl);
                        compareMoeContainer.appendChild(countContainerEl);
                    }
                    moeContainers.push(compareMoeContainer);
                }
                this.container.appendChild(compareEl);
            });
        }
        if (moeContainers.length > 0) {
            moeContainers.forEach(moeContainerEl => {
                moeContainerEl.style.display = 'none';
            });
            this.container.addEventListener('touchstart', () => {
                moeContainers.forEach(moeContainerEl => {
                    moeContainerEl.style.display = 'inline';
                });
            });
            this.container.addEventListener('touchend', () => {
                moeContainers.forEach(moeContainerEl => {
                    moeContainerEl.style.display = 'none';
                });
            });
            this.container.addEventListener('mouseenter', () => {
                moeContainers.forEach(moeContainerEl => {
                    moeContainerEl.style.display = 'inline';
                });
            });
            this.container.addEventListener('mouseleave', () => {
                moeContainers.forEach(moeContainerEl => {
                    moeContainerEl.style.display = 'none';
                });
            });
        }
    }
}