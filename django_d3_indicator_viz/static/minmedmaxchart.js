import { formatData } from "./utils.js";

/**
 * The Min/Median/Max chart visualization.
 */
export default class MinMedMaxChart {

    /**
     * Creates a Min/Median/Max chart visualization.
     * 
     * @param {Object} visual the visual object
     * @param {Element} container the container element
     * @param {Object} indicator the indicator object
     * @param {Object} location the location object
     * @param {Object} indicatorData the indicator data object
     * @param {Array} compareLocations the comparison locations
     * @param {Array} compareData the comparison data
     * @param {Array} filterOptions the filter options
     * @param {Array} locationTypes the location types
     * @param {Object} chartOptions the chart options for echarts
     */
    constructor(visual, container, indicator, location, indicatorData, compareLocations, compareData, filterOptions, locationTypes, chartOptions = {}) {
        this.visual = visual;
        this.container = container;
        this.indicator = indicator;
        this.location = location;
        this.indicatorData = indicatorData;
        this.compareLocations = compareLocations;
        this.compareData = compareData;
        this.filterOptions = filterOptions;
        this.locationTypes = locationTypes;
        this.chartOptions = chartOptions;
        this.chart = null;
        
        this.draw();

        // redraw the visualization on window resize
        window.addEventListener('resize', () => {
            this.draw();
        });
    }

    /**
     * Draws a min med max chart visual.
     */
    draw() {
        if (!this.indicatorData) {
            this.container.innerHTML = 'No data';
            return;
        }
        
        // set up the container
        this.container.classList.add('min-med-max-container');
        this.container.style.height = '48px';

        // get the min, median, and max values
        let values = [this.indicatorData.value].concat(this.compareData.map(d => d.value));
        let minMedMax = [Math.min(...values)];
        let mid = Math.floor(values.length / 2);
        let sortedValues = this.compareData.map(d => d.value).sort((a, b) => a - b);
        if (sortedValues.length % 2 === 0) {
            minMedMax.push((sortedValues[mid - 1] + sortedValues[mid]) / 2);
        } else {
            minMedMax.push(sortedValues[mid]);
        }
        minMedMax.push(Math.max(...values));

        // dispose the old chart (if redrawing)
        if (this.chart) {
            this.chart.dispose();
        }

        // configure the chart
        this.chart = echarts.init(this.container, null, { renderer: 'svg' });
        let option = {
            ...this.chartOptions,
            grid: {
                left: 8,
                right: 8,
                top: '10'
            },
            xAxis: {
                type: 'value',
                boundaryGap: ['0%', '0%'],
                startValue: minMedMax[0],
                min: minMedMax[0],
                max: minMedMax[2],
                axisLabel: {
                    margin: 12,
                    interval: 0,
                    width: 100,
                    overflow: 'break',
                    showMinLabel: true,
                    showMaxLabel: true,
                    alignMinLabel: 'left',
                    alignMaxLabel: 'right',
                    formatter: (value) => {
                        let label = '{bold|' + (value === minMedMax[0] ? 'Min: ' : value === minMedMax[1] ? 'Median: ' : 'Max: ') + '}';
                        return label + '{normal|' + formatData(value, this.indicator.formatter, true) + '}';
                    },
                    rich: {
                        normal: {
                            fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 0.75
                        },
                        bold: {
                            fontWeight: 'bold',
                            fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 0.75
                        }
                    },
                    customValues: minMedMax
                },
                axisTick: {
                    show: true,
                    customValues: minMedMax,
                    length: 8,
                    lineStyle: {
                        width: 2
                    }
                },
                axisLine: {
                    show: true
                },
                splitLine: {
                    show: false
                }
            },
            yAxis: {
                type: 'value',
                position: 'right',
                startValue: 0,
                min: 0,
                max: 0,
                show: false
            },
            series: [{
                data: [[this.indicatorData.value, 0]],
                type: 'scatter',
                symbolSize: 15,
                itemStyle: {
                    opacity: 1
                },
                emphasis: {
                    disabled: true
                },
                cursor: 'default'
            }]
        }
        this.chart.setOption(option);
    }
}