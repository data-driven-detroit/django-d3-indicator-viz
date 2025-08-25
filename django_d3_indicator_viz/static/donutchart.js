import { formatData, buildTooltipContent } from "./utils.js";

export default class DonutChart {
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
        this.lastSelectedIndex = null; // keep track of the last selected index for hover events
        this.option = null; // store the chart option for events

        this.draw();

        window.addEventListener('resize', () => {
            this.draw();
        });
    }

    /**
     * Update the title, legend opacity and chart opacity on series select.
     * 
     * @param {Object} params - The event parameters.
     */
    _seriesSelectHandler(params) {
        // do not allow items to be unselected
        if (params.fromAction === 'unselect') {
            this.chart.dispatchAction({
                type: 'select',
                seriesIndex: 0,
                dataIndex: params.fromActionPayload.dataIndexInside
            });
        }
        
        // update the title and legend opacity with the selected item
        if (params.fromAction === 'select') {
            // update the last selected index
            this.lastSelectedIndex = params.selected[0].dataIndex[0];
            
            this.chart.setOption({
                title: {
                    text: [
                        '{normal|' + this.option.series[0].data[params.selected[0].dataIndex[0]].name + '}',
                        '{bold|' + formatData(this.option.series[0].data[params.selected[0].dataIndex[0]], this.visual.value_field, true) + '}'
                    ].join(' '),
                },
                legend: {
                    data: this.option.series[0].data.map((item, index) => {
                        return {
                            ...item,
                            itemStyle: {
                                opacity: index === params.selected[0].dataIndex[0] ? 1 : 0.5
                            }
                        }
                    }),
                }
            })
        }
    }

    /**
     * Update the title, legend opacity and chart opacity on legend select.
     * 
     * @param {Object} params - The event parameters.
     */
    _legendSelectHandler(params) {
        // do not allow items to be unselected
        for (let key in params.selected) {
            params.selected[key] = true;
        }
        this.chart.setOption({
            legend: {
                selected: params.selected
            }
        });

        // select the corresponding item in the chart
        this.chart.dispatchAction({
            type: 'select',
            seriesIndex: 0,
            name: params.name
        });
    }

    /**
     * Update the title, legend opacity and chart opacity on hover.
     * 
     * @param {Object} params - The event parameters.
     */
    _hoverHandler(params) {
        // the data item to be styled (the item being hovered or the previously selected item)
        let dataItem;
        let dataItemIndex;
        if (params.type === 'mouseover' || params.type === 'highlight') {
            dataItem = this.chart.getOption().series[0].data.find(d => d.name === params.name);
            dataItemIndex = this.chart.getOption().series[0].data.findIndex(d => d.name === params.name);
        } else if (params.type === 'mouseout' || params.type === 'downplay') {
            dataItem = this.chart.getOption().series[0].data[this.lastSelectedIndex];
            dataItemIndex = this.lastSelectedIndex;
        }
        
        this.chart.setOption({
            // set the title to the hovered item or the previously selected item
            title: {
                text: [
                    '{normal|' + dataItem.name + '}',
                    '{bold|' + formatData(dataItem, this.visual.value_field, true) + '}'
                ].join(' '),
            },
            legend: {
                // set the legend opacity to 1 for the hovered item or the previously selected item
                data: this.chart.getOption().series[0].data.map((item, index) => {
                    return {
                        ...item,
                        itemStyle: {
                            opacity: index === dataItemIndex ? 1 : 0.5
                        }
                    }
                }),
            },
            series: [{
                // set the chart opacity to 1 for the hovered item or the previously selected item
                data: this.chart.getOption().series[0].data.map((item, index) => {
                    return {
                        ...item,
                        itemStyle: {
                            opacity: index === dataItemIndex ? 1 : 0.5
                        }
                    }
                }),
                // set the chart 'selected' opacity to 0.5 when hovering over a different item
                select: {
                    itemStyle: {
                        opacity: params.type === 'mouseover' || params.type === 'highlight' ? 0.5 : 1
                    }
                }
            }]
        });
    }

    /**
     * Draws a donut chart visual.
     */
    draw() {
        this.container.classList.add('donut-chart-container');
        this.container.style.height = null;
        let computedStyleHeight = window.getComputedStyle(this.container).height;
        computedStyleHeight = Number(computedStyleHeight.substring(0, computedStyleHeight.length - 2));
        if (window.innerWidth < 1200) {
            this.container.style.height = computedStyleHeight + (30 * this.indicatorData.length) + 30 + 'px';
        }

        // transform the data for the chart
        let data = this.indicatorData.map(item => {
            return {
                ...item,
                value: item[this.visual.value_field],
                name: this.filterOptions.find(o => o.id === item.filter_option_id).name
            }
        });
        
        // configure the chart
        if (this.chart) {
            this.chart.dispose();
        }
        this.chart = echarts.init(this.container, null, { renderer: 'svg' });
        this.option = {
            ...this.chartOptions,
            color: this.colorScales.find(scale => scale.id === this.visual.color_scale_id).colors,
            grid: {
                left: 0,
                right: '80px',
                top: 0,
                bottom: 0,
                containLabel: true
            },
            // the title will update when an item is hovered selected (both from the legend or the chart)
            title: {
                text: null, // will be set on hover/select
                textStyle: {
                    rich: {
                        normal: {
                            fontWeight: 'normal',
                            fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 1.25
                        },
                        bold: {
                            fontWeight: 'bold',
                            fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 1.25
                        }
                    }
                },
                top: window.innerWidth >= 1200 ? '20px' : computedStyleHeight + 'px',
                left: window.innerWidth >= 1200  ? computedStyleHeight + 'px' : 0
            },
            // the legend will update when an item is hovered selected (both from the legend or the chart)
            legend: {
                orient: 'vertical',
                top: window.innerWidth >= 1200  ? '60px' : computedStyleHeight + 30 + 'px',
                left: window.innerWidth >= 1200  ? computedStyleHeight + 'px' : 0,
                icon: 'rect',
                selectedMode: 'series',
                data: data.map(item => {
                    return {
                        ...item,
                        itemStyle: {
                            opacity: 0.5
                        }
                    }
                }),
                tooltip: {
                    show: 'true',
                    formatter: params => {
                        let data = this.chart.getOption().series[0].data.find(d => d.name === params.name);
                        return buildTooltipContent(params.name, data, this.visual.value_field, this.compareLocations, this.compareData);
                    }
                }
            },
            tooltip: {
                show: 'true',
                trigger: 'item',
                triggerOn: 'mousemove',
                formatter: params => {
                    return buildTooltipContent(params.name, params.data, this.visual.value_field, this.compareLocations, this.compareData);
                }
            },
            yAxis: {
                type: 'value',
                position: 'right',
                show: false
            },
            series: [
                {
                    type: 'pie',
                    width: computedStyleHeight + 'px',
                    height: computedStyleHeight + 'px',
                    radius: ['60%', '80%'],
                    center: [computedStyleHeight / 2 + 'px', '50%'],
                    label: {
                        show: false
                    },
                    labelLine: {
                        show: false
                    },
                    itemStyle: {
                        opacity: 0.5
                    },
                    blur: {
                        itemStyle: {
                            opacity: 0.5
                        }
                    },
                    selectedMode: 'single',
                    selectedOffset: 0,
                    select: {
                        itemStyle: {
                            opacity: 1
                        }
                    },
                    emphasis: {
                        scale: false,
                        itemStyle: {
                            color: 'inherit',
                            opacity: 1
                        },
                        focus: 'series'
                    },
                    data: data
                }
            ]
        };
        this.chart.setOption(this.option);

        this.chart.on('selectchanged', this._seriesSelectHandler, this);

        this.chart.on('legendselectchanged', this._legendSelectHandler, this);

        // update the title, legend opacity and chart opacity on all hover events
        this.chart.on('highlight', this._hoverHandler, this);
        this.chart.on('downplay', this._hoverHandler, this);
        this.chart.on('mouseover', this._hoverHandler, this);
        this.chart.on('mouseout', this._hoverHandler, this);

        // select the highest value by default
        this.chart.dispatchAction({
            type: 'select',
            seriesIndex: 0,
            dataIndex: this.option.series[0].data.findIndex(item => item.value === Math.max(...data.map(item => item.value)))
        });
    }
}