import { formatData, buildTooltipContent, showAggregateNotice } from "./utils.js";

/**
 * The Multi-Line chart visualization (supports multiple filter options as separate lines).
 */
export default class MultiLineChart {

    /**
     * Creates a Multi-Line chart visualization.
     *
     * @param {Object} visual the visual object
     * @param {Element} container the container element
     * @param {Object} indicator the indicator object
     * @param {Object} location the location object
     * @param {Array} indicatorData the indicator data object
     * @param {Array} compareLocations the comparison locations
     * @param {Array} compareData the comparison data
     * @param {Array} filterOptions the filter options
     * @param {Array} locationTypes the location types
     * @param {Array} colorScales the color scales
     * @param {Object} chartOptions the chart options for echarts
     */
    constructor(visual, container, indicator, location, indicatorData, compareLocations, compareData, filterOptions,
        locationTypes, colorScales, chartOptions = {}) {

        this.visual = visual;
        this.container = container;
        this.indicator = indicator;
        this.location = location;
        this.indicatorData = indicatorData;
        this.compareLocations = compareLocations;
        this.compareData = compareData;
        this.filterOptions = filterOptions;
        this.locationTypes = locationTypes;
        this.colorScales = colorScales;
        this.chartOptions = chartOptions;
        this.chart = null;

        this.draw();

        // redraw the visualization on window resize
        window.addEventListener('resize', () => {
            this.draw();
        });
    }

    /**
     * Draws a multi-line chart visual.
     */
    draw() {
        if (!this.indicatorData || !this.indicatorData.length) {
            this.container.innerHTML = 'No data';
            return;
        }

        // Group data by filter option (for multiple lines) or use single series
        let seriesData = {};
        let seriesNames = [];

        // Check if we have multiple filter options
        let uniqueFilterOptions = [...new Set(this.indicatorData.map(d => d.filter_option_id))];

        if (uniqueFilterOptions.length > 1 && uniqueFilterOptions.some(id => id !== null)) {
            // Multiple filter options - create a series for each
            uniqueFilterOptions.forEach(filterOptionId => {
                let filterOption = this.filterOptions.find(o => o.id === filterOptionId);
                let filterName = filterOption ? filterOption.name : 'No filter';
                let key = `${this.location.id}-${filterOptionId}`;
                // Sort data chronologically (oldest to newest)
                let filteredData = this.indicatorData.filter(d => d.filter_option_id === filterOptionId);
                seriesData[key] = filteredData.sort((a, b) => new Date(a.end_date) - new Date(b.end_date));
                seriesNames.push(filterName);
            });
        } else {
            // Single series for the location
            // Sort data chronologically (oldest to newest)
            let sortedData = [].concat(this.indicatorData).sort((a, b) =>
                new Date(a.end_date) - new Date(b.end_date)
            );
            seriesData[this.location.id] = sortedData;
            seriesNames = [this.location.name];
        }

        seriesData = Object.values(seriesData);

        // set up the container
        this.container.classList.add('line-chart-container');
        this.container.style.height = '200px';

        // dispose the old chart (if redrawing)
        if (this.chart) {
            this.chart.dispose();
        }

        // configure the chart
        this.chart = echarts.init(this.container, null, { renderer: 'svg' });
        let grid = { containLabel: true };
        if (window.innerWidth >= 1200) {
            grid.left = '5px';
            grid.right = '5px';
            grid.top = '10px';
            grid.bottom = '10px';
        } else if (window.innerWidth < 1200 && window.innerWidth >= 768) {
            grid.left = '5px';
            grid.right = '5px';
            grid.top = '20px';
            grid.bottom = '20px';
        } else {
            grid.top = '20px';
            grid.bottom = '20px';
            grid.left = '5px';
            grid.right = '5px';
        }
        let option = {
            ...this.chartOptions,
            color: this.colorScales.find(scale => scale.id === this.visual.color_scale_id).colors,
            grid: grid,
            legend: {
                show: seriesData.length > 1,
                bottom: '0',
                left: '0',
                icon: 'rect',
                selectedMode: false,
                textStyle: {
                    fontWeight: 'bold',
                }
            },
            tooltip: {
                show: 'true',
                trigger: 'axis',
                triggerOn: 'mousemove',
                axisPointer: {
                    type: 'none'
                },
                formatter: params => {
                    return buildTooltipContent(
                        params[0].name.substring(0, 4),
                        params[0].data,
                        this.indicator,
                        this.compareLocations,
                        this.compareData
                    );
                }
            },
            xAxis: {
                type: 'category',
                data: seriesData[0].map(item => item.end_date),
                boundaryGap: false,
                axisLabel: {
                    width: 100,
                    overflow: 'break',
                    showMinLabel: true,
                    showMaxLabel: true,
                    alignMinLabel: 'left',
                    alignMaxLabel: 'right',
                    formatter: (value) => {
                        let data = seriesData[0].find(item => item.end_date === value);
                        return '{bold|' + value.substring(0, 4) + ': ' + '}'
                            + '{normal|' + formatData(data.value, this.indicator.formatter, true) + '}'
                            + (showAggregateNotice(data) ? '*' : '');
                    },
                    rich: {
                        normal: {
                            fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 0.75,
                        },
                        bold: {
                            fontWeight: 'bold',
                            fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 0.75
                        }
                    }
                },
                axisTick: {
                    show: false
                },
                axisLine: {
                    show: false
                },
                splitLine: {
                    show: false
                }
            },
            yAxis: {
                type: 'value',
                position: 'right',
                show: false,
                axisLabel: {
                    formatter: (value) => formatData(value, this.indicator.formatter, true)
                }
            },
            series: seriesData
                .map((data, index) => {
                    return {
                        // Use filter option name if we have multiple series by filter, otherwise location name
                        name: seriesNames[index],
                        type: 'line',
                        data: data,
                        z: 3,
                        symbol: 'circle',
                        showSymbol: true,
                        symbolSize: 8,
                        connectNulls: false,
                        clip: false,
                        lineStyle: {
                            width: 4
                        },
                        emphasis: {
                            disabled: true
                        },
                        cursor: 'default'
                    }
                })
        }
        this.chart.setOption(option);
    }
}
