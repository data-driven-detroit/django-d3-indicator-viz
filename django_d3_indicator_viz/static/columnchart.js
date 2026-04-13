import { formatData, buildTooltipContent, showAggregateNotice, hasHighMoe, addHighMoeNotice, DataVisualComparisonMode } from "./utils.js";

/**
 * Returns the ECharts label position for a bar given its value sign and orientation.
 * @param {number}  value     - the data point value
 * @param {boolean} isDesktop - true when width >= 1200 (vertical bars)
 */
function getLabelPosition(value, isDesktop) {
    if (isDesktop) return value < 0 ? 'bottom' : 'top';
    return value < 0 ? 'left' : 'right';
}

/**
 * Enriches each data item with a per-item label.position override so ECharts
 * positions the label correctly for both positive and negative bars.
 * ECharts ignores a function at series.label.position; per-item config works.
 */
function withLabelPositions(data, isDesktop, distance = 6) {
    return data.map(item => ({
        ...item,
        label: { position: getLabelPosition(item.value, isDesktop), distance }
    }));
}

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
        colorScales, dataVisualComparisonMode, chartOptions = {}, axisScale = null) {

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
        this.axisScale = axisScale;
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

        const isDesktop = window.innerWidth >= 1200;

        // create a series for each location
        let seriesNames = [this.location.name];
        let seriesData = {};
        seriesData[this.location.id] = [].concat(this.indicatorData);
        if (this.dataVisualComparisonMode === DataVisualComparisonMode.DATA_VISUAL) {
            this.compareData.forEach(item => {
                // Skip items with null values
                if (item.value === null || item.value === undefined) {
                    return;
                }
                if (!seriesData[item.location_id]) {
                    seriesData[item.location_id] = [];
                    let location = this.compareLocations.find(loc => loc.id === item.location_id);
                    seriesNames.push(location ? location.name : 'Unknown');
                }
                seriesData[item.location_id].push(item);
            });
        }
        seriesData = Object.values(seriesData);

        // Check if all data is inactive
        let allDataInactive = this.indicatorData.every(item => item.active_data === false);
        if (this.dataVisualComparisonMode === DataVisualComparisonMode.DATA_VISUAL) {
            allDataInactive = allDataInactive && this.compareData.every(item => item.active_data === false);
        }

        // set up the container
        this.container.classList.add('column-chart-container');
        if (window.innerWidth < 768) {
            this.container.style.height = (seriesData.length * seriesData[0].length * 60)
                + (seriesData.length * 30)
                + 'px';
        } else if (!isDesktop) {
            this.container.style.height = (seriesData.length * seriesData[0].length * 30)
                + (seriesData.length * 30)
                + 'px';
        } else {
            // Desktop screens >= 1200px
            this.container.style.height = '200px';
        }
        if (!isDesktop) {
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
            show: window.innerWidth >= 768,
            boundaryGap: true,
            axisLabel: {
                fontSize: (this.chartOptions.textStyle?.fontSize || 12) * 0.75 + 'px',
                interval: 0,
                width: 80, // window.innerWidth >= 768 ? 120 : 65,
                overflow: 'break', // break, breakAll, ... with another 
                // rotate the axis label 45% if the screen width is less than 1720px
                rotate: isDesktop && window.innerWidth < 1720 && seriesData[0].length > 12 ? 45 : 0
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

        if (this.axisScale) {
            valueAxis.min = this.axisScale.min;
            valueAxis.max = this.axisScale.max;
        }
        let grid = { containLabel: true };
        if (isDesktop) {
            grid.left = '0px';
            grid.right = '0px';
            grid.top = '10px';
            grid.bottom = '10px';
        } else if (window.innerWidth >= 768) {
            grid.top = '20px';
            grid.bottom = '20px';
        } else {
            grid.top = '20px';
            grid.bottom = (30 * seriesData.length) + 'px';
            grid.left = '0px';
        }
        let option = {
            ...this.chartOptions, // This upacks the options set in the chartloader.js file
            color: allDataInactive
                ? ['#CCCCCC', '#999999', '#777777', '#555555']
                : this.colorScales.find(scale => scale.id === this.visual.color_scale_id).colors,
            grid: grid,
            legend: {
                show: seriesData.length > 1,
                bottom: '0',
                left: '0',
                icon: 'rect',
                selectedMode: false,
                itemGap: isDesktop ? 40 : 10,
                textStyle: {
                    fontWeight: 'bold',
                },
                orient: isDesktop ? 'horizontal' : 'vertical'
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
            xAxis: isDesktop ? categoryAxis : valueAxis,
            yAxis: isDesktop ? valueAxis : categoryAxis,
            series: seriesData.map((data, index) => {
                return {
                    name: seriesNames[index],
                    type: 'bar',
                    colorBy: 'data',
                    // withLabelPositions sets per-item label.position for correct
                    // placement above/below (desktop) or right/left (mobile) based
                    // on value sign. Series-level label.position is intentionally
                    // omitted — ECharts ignores a function there; per-item wins.
                    data: withLabelPositions(data, isDesktop),
                    // NOTE (Mike): Sean, this is where you can adjust the width of bars
                    barWidth: '85%',
                    label: {
                        show: true,
                        fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 0.75 + 'px',
                        formatter: (params) =>{
                            let isActive = params.data.active_data !== false;
                            let highMoe = hasHighMoe(params.data);
                            if (highMoe) addHighMoeNotice(this.container);
                            return formatData(params.data.value, this.indicator.formatter, true, isActive)
                                + (highMoe ? '\u2020' : '')
                                + (showAggregateNotice(params.data) ? '*' : '');
                        }
                    },
                    emphasis: {
                        disabled: true
                    },
                    cursor: 'default',
                    // Zero baseline — only attach to first series to avoid duplicating the line
                    ...(index === 0 ? {
                        markLine: {
                            silent: true,
                            symbol: 'none',
                            lineStyle: {
                                color: '#cccccc',
                                width: 1,
                                type: 'solid',
                            },
                            label: { show: false },
                            data: [isDesktop ? { yAxis: 0 } : { xAxis: 0 }]
                        }
                    } : {}),
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
