import { formatData } from "./utils.js";

export default class MinMedMaxChart {
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

        window.addEventListener('resize', () => {
            this.draw();
        });
    }

    /**
     * Draws a min med max chart visual.
     */
    draw() {
        this.container.classList.add('min-med-max-container');
        this.container.style.height = '48px';

        // get the min, median, and max values
        let values = [this.indicatorData[this.visual.value_field]].concat(this.compareData.map(d => d[this.visual.value_field]));
        let minMedMax = [Math.min(...values)];
        let mid = Math.floor(values.length / 2);
        let sortedValues = this.compareData.map(d => d[this.visual.value_field]).sort((a, b) => a - b);
        if (sortedValues.length % 2 === 0) {
            minMedMax.push((sortedValues[mid - 1] + sortedValues[mid]) / 2);
        } else {
            minMedMax.push(sortedValues[mid]);
        }
        minMedMax.push(Math.max(...values));
        
        // configure the chart
        if (this.chart) {
            this.chart.dispose();
        }
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
                        let data = {};
                        data[this.visual.value_field] = value;
                        return label + '{normal|' + formatData(data, this.visual.value_field) + '}';
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
                data: [[this.indicatorData[this.visual.value_field], 0]],
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