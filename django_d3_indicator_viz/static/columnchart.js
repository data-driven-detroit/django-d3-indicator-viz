import { formatData, buildTooltipContent } from "./utils.js";

export default class ColumnChart {
    constructor(visual, container, indicator, location, indicatorData, compareLocations, compareData, filterOptions, colorScales, chartOptions = {}) {
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
        this.compareData.forEach(item => {
            if (!seriesData[item.location_id]) {
                seriesData[item.location_id] = []
                seriesNames.push(this.compareLocations.find(loc => loc.id === item.location_id).name);
            }
            seriesData[item.location_id].push(item);
        });
        seriesData = Object.values(seriesData);

        // set up the container
        this.container.classList.add('column-chart-container');
        if (window.innerWidth < 768) {
            this.container.style.height = (seriesData.length * seriesData[0].length * 60) + (seriesData.length * 30) + 'px';
        } else if (window.innerWidth < 1200) { 
            this.container.style.height = (seriesData.length * seriesData[0].length * 30) + (seriesData.length * 30) + 'px';
        }
        if (window.innerWidth < 1200) {
            seriesData = seriesData.map(series => series.reverse());
        }

        // configure the chart
        if (this.chart) {
            this.chart.dispose();
        }
        this.chart = echarts.init(this.container, null, { renderer: 'svg' });
        let categoryAxis = {
            type: 'category',
            data: seriesData[0].map(item => this.filterOptions.find(f => f.id === item.filter_option_id).name),
            show: window.innerWidth >= 768 ? true : false,
            boundaryGap: true,
            axisLabel: {
                fontWeight: 'bold',
                fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 0.75 + 'px',
                interval: 0,
                width: window.innerWidth >= 768 ? 110 : 0,
                overflow: 'break',
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
                    return buildTooltipContent(params.name, params.data, this.visual.value_field);
                }
            },
            xAxis: window.innerWidth < 1200 ? valueAxis : categoryAxis,
            yAxis: window.innerWidth < 1200 ? categoryAxis : valueAxis,
            series: seriesData.map((data, index) => {
                return {
                    name: seriesNames[index],
                    type: 'bar',
                    colorBy: 'data',
                    data: data.map(item => { return { ...item, value: item[this.visual.value_field] } }),
                    label: {
                        show: true,
                        position: window.innerWidth >= 1200 ? 'top' : 'right',
                        formatter: (params) =>{
                            return formatData(params.data, this.visual.value_field);
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
                data: seriesData[0].map(item => { return { value: 0, label: this.filterOptions.find(f => f.id === item.filter_option_id) } }),
                label: {
                    show: true,
                    position: 'right',
                    distance: 0,
                    fontWeight: 'bold',
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
            option.color = ['transparent'].concat(option.color);
        }
        this.chart.setOption(option);
    }
}