import { formatData, buildTooltipContent, showAggregateNotice, DataVisualComparisonMode } from "./utils.js";

/**
 * The Column chart visualization.
 */
export default class ColumnChart {

    /**
     * Creates a Column chart visualization.
     * 
     * @param {Object} visual the visual object
     * @param {Element} container the container element
     * @param {Object} indicator the indicator object
     * @param {Object} location the location object
     * @param {Array} indicatorData the indicator data object
     * @param {Array} compareLocations the comparison locations
     * @param {Array} compareData the comparison data
     * @param {Array} filterOptions the filter options
     * @param {Array} colorScales the color scales
     * @param {String} dataVisualComparisonMode the mode for displaying data visual comparisons
     * @param {Object} chartOptions the chart options for echarts
     */
    constructor(visual, container, indicator, location, indicatorData, compareLocations, compareData, filterOptions, 
        colorScales, dataVisualComparisonMode, chartOptions = {}) {
        
        this.visual = visual;
        this.container = container;
        this.indicator = indicator;
        this.location = location;
        this.indicatorData = indicatorData;
        this.compareLocations = compareLocations;
        this.compareData = compareData;
        this.filterOptions = filterOptions;
        this.colorScales = colorScales;
        this.chartOptions = chartOptions;
        this.dataVisualComparisonMode = dataVisualComparisonMode;
        this.chart = null;

        this.draw();

        // redraw the visualization on window resize
        window.addEventListener('resize', () => {
            this.draw();
        });
    }

    /**
     * Draws a column chart visual.
     */
    draw() {
        if (!this.indicatorData || !this.indicatorData.length) {
            this.container.innerHTML = 'No data';
            return;
        }

        // create a series for each location
        let seriesNames = [this.location.name];
        let seriesData = {};
        seriesData[this.location.id] = [].concat(this.indicatorData);
        if (this.dataVisualComparisonMode === DataVisualComparisonMode.DATA_VISUAL) {
            this.compareData.forEach(item => {
                if (!seriesData[item.location_id]) {
                    seriesData[item.location_id] = []
                    seriesNames.push(this.compareLocations.find(loc => loc.id === item.location_id).name);
                }
                seriesData[item.location_id].push(item);
            });
        }
        seriesData = Object.values(seriesData);

        // set up the container
        this.container.classList.add('column-chart-container');
        if (window.innerWidth < 768) {
            this.container.style.height = (seriesData.length * seriesData[0].length * 60) 
                + (seriesData.length * 30) 
                + 'px';
        } else if (window.innerWidth < 1200) { 
            this.container.style.height = (seriesData.length * seriesData[0].length * 30) 
                + (seriesData.length * 30) 
                + 'px';
        }
        if (window.innerWidth < 1200) {
            seriesData = seriesData.map(series => series.reverse());
        }

        // dispose the old chart (if redrawing)
        if (this.chart) {
            this.chart.dispose();
        }

        // configure the chart
        this.chart = echarts.init(this.container, null, { renderer: 'svg' });
        let categoryAxis = {
            type: 'category',
            data: seriesData[0].map(
                item => this.filterOptions.find(f => f.id === item.filter_option_id).name
            ),
            show: window.innerWidth >= 768 ? true : false,
            boundaryGap: true,
            axisLabel: {
                fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 0.75 + 'px',
                interval: 0,
                width: window.innerWidth >= 768 ? 80 : 0,
                overflow: 'wrap',
                // rotate the axis label 45% if the screen width is less than 1720px
                rotate: window.innerWidth >= 1200 && window.innerWidth < 1720 && seriesData[0].length > 12 ? 45 : 0
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
        };
        let valueAxis = {
            type: 'value',
            position: 'right',
            show: false
        };
        let grid = { containLabel: true};
        if (window.innerWidth >= 1200) {
            grid.left = '0px';
            grid.right = '0px';
        } else if (window.innerWidth < 1200 && window.innerWidth >= 768) {
            grid.top = '20px';
            grid.bottom = '20px';
        } else {
            grid.top = '20px';
            grid.bottom = (30 * seriesData.length) + 'px';
            grid.left = '0px';
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
                itemGap: window.innerWidth >= 768 ? 40 : 10,
                textStyle: {
                    fontWeight: 'bold',
                },
                orient: window.innerWidth >= 768 ? 'horizontal' : 'vertical'
            },
            tooltip: {
                show: 'true',
                trigger: 'item',
                triggerOn: 'mousemove',
                formatter: params => {
                    if (this.dataVisualComparisonMode === DataVisualComparisonMode.DATA_VISUAL) {
                        return buildTooltipContent(params.name, params.data, this.indicator);
                    } else {
                        return buildTooltipContent(params.seriesName, params.data, this.indicator, 
                            this.compareLocations, this.compareData);
                    }
                }
            },
            xAxis: window.innerWidth < 1200 ? valueAxis : categoryAxis,
            yAxis: window.innerWidth < 1200 ? categoryAxis : valueAxis,
            series: seriesData.map((data, index) => {
                return {
                    name: seriesNames[index],
                    type: 'bar',
                    colorBy: 'data',
                    data: data,
                    label: {
                        show: true,
                        position: window.innerWidth >= 1200 ? 'top' : 'right',
                        fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 0.75 + 'px',
                        formatter: (params) =>{
                            return formatData(params.data.value, this.indicator.formatter, true) 
                                + (showAggregateNotice(params.data) ? '*' : '');
                        }
                    },
                    emphasis: {
                        disabled: true
                    },
                    cursor: 'default',
                    
                }
            })
        }
        if (window.innerWidth < 768) {
            let labelSeries = {
                name: '',
                type: 'bar',
                data: seriesData[0].map(item => { 
                    return {
                        value: 0,
                        label: this.filterOptions.find(f => f.id === item.filter_option_id)
                    } 
                }),
                label: {
                    show: true,
                    position: 'right',
                    distance: 0,
                    fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 0.75 + 'px',
                    formatter: function(params) {
                        return params.name;
                    },
                },
                emphasis: {
                    disabled: true
                },
                cursor: 'default'
            };
            option.series = [labelSeries].concat(option.series);
        }
        this.chart.setOption(option);
    }
}
