import { formatData, buildTooltipContent, showAggregateNotice } from "./utils.js";

/**
 * The Line chart visualization.
 */
export default class LineChart {

    /**
     * Creates a Line chart visualization.
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
     * Draws a column chart visual.
     */
    draw() {
        if (!this.indicatorData || !this.indicatorData.length) {
            this.container.innerHTML = 'No data';
            return;
        }

        // generate a date range for the x axis, filling in any missing years
        let xAxisData = [];
        let currentDate = new Date(this.indicatorData[0].end_date);
        let endDate = new Date(this.indicatorData[this.indicatorData.length - 1].end_date);
        while (currentDate <= endDate) {
            xAxisData.push(currentDate.toISOString().substring(0, 10));
            currentDate.setFullYear(currentDate.getFullYear() + 1);
        }

        // create a series for each location, ensuring each series has a data point for each x axis date
        let seriesData = {};
        seriesData[this.location.id] = [];
        xAxisData.forEach(end_date => {
            seriesData[this.location.id].push(
                this.indicatorData.find(d => d.end_date === end_date && d.location_id === this.location.id) 
                    || { end_date: end_date, value: null }
            );
        });
        this.compareLocations.forEach(location => {
            seriesData[location.id] = [];
            xAxisData.forEach(end_date => {
                seriesData[location.id].push(
                    this.compareData.find(d => d.end_date === end_date && d.location_id === location.id) || null
                );
            });
        });
        seriesData = Object.values(seriesData);

        // set up the container
        this.container.classList.add('line-chart-container');

        // dispose the old chart (if redrawing)
        if (this.chart) {
            this.chart.dispose();
        }

        // configure the chart
        this.chart = echarts.init(this.container, null, { renderer: 'svg' });
        let option = {
            ...this.chartOptions,
            color: this.colorScales.find(scale => scale.id === this.visual.color_scale_id).colors,
            grid: {
                left: 0,
                right: 0,
                containLabel: true
            },
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
                data: xAxisData,
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
                            + '{normal|' + formatData(data?.value, this.indicator.formatter, true) + '}'
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
                show: false
            },
            series: seriesData
                .map(data => {
                    return {
                        // consolidate to two series names - the name of the location being viewed and the name of the 
                        // other locations
                        // if there are only two series, use the location name for the second series name
                        name: data[0].location_id === this.location.id
                            ? this.location.name 
                            : this.visual.location_comparison_type === 'parents'
                                ? this.compareLocations.find(l => l.id === data[0].location_id).name
                                : 'Other ' 
                                    + this.locationTypes.find(lt => lt.id === this.location.location_type_id).name 
                                    + 's',
                        type: 'line',
                        data: data,
                        // make sure the location being viewed sits above the other locations
                        z: data[0].location_id === this.location.id ? 3 : 2,
                        // only show a symbol for the location being viewed on the last data point
                        showSymbol: false,
                        markPoint: {
                            symbol: 'circle',
                            symbolSize: data[0].location_id === this.location.id  ? 10 : 0,
                            data: [{
                                type: 'coordinate',
                                coord: [data[data.length-1].end_date, data[data.length-1].value]
                            }]
                        },
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