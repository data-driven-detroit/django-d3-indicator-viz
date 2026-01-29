import { formatData, buildTooltipContent, showAggregateNotice } from "./utils.js";

/**
 * The Multi-Line chart visualization.
 * Shows different filter options as separate lines over time.
 */
export default class MultiLineChart {

    /**
     * Creates a Multi-Line chart visualization.
     *
     * @param {Object} visual the visual object
     * @param {Element} container the container element
     * @param {Object} indicator the indicator object
     * @param {Object} location the location object
     * @param {Array} indicatorData the indicator data for the primary location
     * @param {Array} compareLocations the comparison locations (not used for multiline)
     * @param {Array} compareData the comparison data (not used for multiline)
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
     * Draws a multi-line chart visual with lines grouped by filter option.
     */
    draw() {
        if (!this.indicatorData || !this.indicatorData.length) {
            this.container.innerHTML = 'No data';
            return;
        }

        // Group data by filter_option_id
        let seriesData = [];
        let seriesNames = [];

        // Get unique filter option IDs from the data
        let uniqueFilterOptionIds = [...new Set(this.indicatorData.map(d => d.filter_option_id))];

        // Get unique years for the category axis (sorted chronologically)
        let uniqueYears = [...new Set(this.indicatorData.map(d => d.end_date.substring(0, 4)))]
            .sort((a, b) => a - b);

        // Create a series for each filter option
        uniqueFilterOptionIds.forEach(filterOptionId => {
            // Get data for this filter option, sorted chronologically
            let filteredData = this.indicatorData
                .filter(d => d.filter_option_id === filterOptionId)
                .sort((a, b) => new Date(a.end_date) - new Date(b.end_date));

            // Skip filter options that have no valid (non-null) values
            let hasValidData = filteredData.some(d => d.value !== null && d.value !== undefined);
            if (!hasValidData) {
                return;
            }

            // Get the filter option name
            let filterOption = this.filterOptions.find(fo => fo.id === filterOptionId);
            let seriesName = filterOption ? filterOption.name : 'Unknown';

            seriesData.push(filteredData);
            seriesNames.push(seriesName);
        });

        // If no valid series data, show no data message
        if (seriesData.length === 0) {
            this.container.innerHTML = 'No data';
            return;
        }

        // Check if all data is inactive
        let allDataInactive = this.indicatorData.every(item => item.active_data === false);

        // set up the container
        this.container.classList.add('line-chart-container');
        this.container.style.height = '240px';

        // dispose the old chart (if redrawing)
        if (this.chart) {
            this.chart.dispose();
        }

        // configure the chart
        this.chart = echarts.init(this.container, null, { renderer: 'svg' });
        let grid = { containLabel: true };

        // Add extra bottom padding if there will be a legend
        const hasLegend = seriesData.length > 1;
        if (window.innerWidth >= 1200) {
            grid.left = '5px';
            grid.right = '5px';
            grid.top = '10px';
            grid.bottom = hasLegend ? '35px' : '10px';
        } else if (window.innerWidth < 1200 && window.innerWidth >= 768) {
            grid.left = '5px';
            grid.right = '5px';
            grid.top = '20px';
            grid.bottom = hasLegend ? '40px' : '20px';
        } else {
            grid.top = '20px';
            grid.bottom = hasLegend ? '40px' : '20px';
            grid.left = '5px';
            grid.right = '5px';
        }

        let option = {
            ...this.chartOptions,
            color: allDataInactive
                ? ['#CCCCCC', '#999999', '#777777', '#555555']
                : this.colorScales.find(scale => scale.id === this.visual.color_scale_id).colors,
            grid: grid,
            legend: {
                show: hasLegend,
                bottom: '5px',
                left: '0',
                icon: 'rect',
                selectedMode: false,
                itemGap: 15,
                textStyle: {
                    fontSize: 12,
                    fontWeight: 'normal',
                }
            },
            tooltip: {
                show: true,
                trigger: 'item',
                triggerOn: 'mousemove',
                formatter: params => {
                    let item = params.data;
                    let year = new Date(item.end_date).getFullYear();
                    let isActive = item.active_data !== false;
                    return `<strong>${params.seriesName}</strong> (${year})<br/>` +
                           formatData(item.value, this.indicator.formatter, true, isActive);
                }
            },
            xAxis: {
                type: 'category',
                data: uniqueYears,
                boundaryGap: false,
                axisLabel: {
                    showMinLabel: true,
                    showMaxLabel: true,
                    alignMinLabel: 'left',
                    alignMaxLabel: 'right',
                    fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 0.75,
                    fontWeight: 'bold'
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
                show: true,
                axisLabel: {
                    formatter: (value) => formatData(value, this.indicator.formatter, true)
                },
                ...(this.indicator.indicator_type === 'percentage' && {
                    min: 0,
                    max: 100
                })
            },
            series: seriesData.map((data, index) => {
                return {
                    name: seriesNames[index],
                    type: 'line',
                    // Map data to category axis format
                    // Each item needs to align with the category (year)
                    data: data.map(item => {
                        return {
                            value: item.value,
                            // Store original item properties we need for tooltip
                            end_date: item.end_date,
                            active_data: item.active_data
                        };
                    }),
                    z: 3 - index,  // First series on top
                    symbol: 'circle',
                    showSymbol: true,
                    symbolSize: 8,
                    connectNulls: false,  // Don't connect across null values (creates gaps)
                    clip: false,
                    lineStyle: {
                        width: 4
                    },
                    emphasis: {
                        disabled: true
                    },
                    cursor: 'default'
                };
            })
        };

        this.chart.setOption(option);
    }
}
