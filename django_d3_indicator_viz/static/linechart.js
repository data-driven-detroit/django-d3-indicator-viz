import { formatData, buildTooltipContent } from "./utils.js";

export default class LineChart {
    constructor(visual, container, indicator, location, indicatorData, compareLocations, compareData, filterOptions, locationTypes, colorScales, chartOptions = {}) {
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

        window.addEventListener('resize', () => {
            this.draw();
        });
    }

    /**
     * Draws a column chart visual.
     */
    draw() {
        // create a series for each location
        let seriesNames = [this.location.name];
        let seriesData = {};
        seriesData[this.location.id] = [].concat(this.indicatorData);
        seriesData = Object.values(seriesData);

        // set up the container
        this.container.classList.add('line-chart-container');

        // configure the chart
        if (this.chart) {
            this.chart.dispose();
            //this.container.innerHTML = '';
        }
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
                    return buildTooltipContent(params[0].name.substring(0, 4), params[0].data, this.visual.value_field, this.compareLocations, this.compareData);
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
                        let label = '{bold|' + value.substring(0, 4) + ': ' + '}';
                        return label + '{normal|' + formatData(seriesData[0].find(item => item.end_date === value), this.visual.value_field) + '}';
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
                        // consolidate to two series names - the name of the location being viewed and the name of the other locations
                        // if there are only two series, use the location name for the second series name
                        name: data[0].location_id === this.location.id
                            ? this.location.name 
                            : this.visual.location_comparison_type === 'parents'
                                ? this.compareLocations.find(l => l.id === data[0].location_id).name
                                : 'Other ' + this.locationTypes.find(lt => lt.id === this.location.location_type_id).name + 's',
                        type: 'line',
                        data: data.map(item => { return { ...item, value: item[this.visual.value_field] } }),
                        // make sure the location being viewed sits above the other locations
                        z: data[0].location_id === this.location.id ? 3 : 2,
                        // only show a symbol for the location being viewed on the last data point
                        showSymbol: false,
                        markPoint: {
                            symbol: 'circle',
                            symbolSize: data[0].location_id === this.location.id  ? 10 : 0,
                            data: [{
                                type: 'coordinate',
                                coord: [data[data.length-1].end_date, data[data.length-1][this.visual.value_field]]
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