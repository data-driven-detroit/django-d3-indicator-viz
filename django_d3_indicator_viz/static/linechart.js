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
    constructor(visual, container, indicator, location, indicatorData, 
        compareLocations, compareData, filterOptions, locationTypes, 
        colorScales, chartOptions = {}) {

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
        // If there isn't any indicator data for the indicator, just write it
        if (!this.indicatorData || !this.indicatorData.length) {
            this.container.innerHTML = 'No data';
            return;
        }
        
        // This may not be necessary -- we're mostly concerned about passing 
        // the location metadata to the series in the correct order
        const compareLookup = Object.fromEntries(
            this.compareLocations.map(l => [l.id, l])
        );

        // Need a list of lists from the compare data
        let compareGroups = Object.groupBy(this.compareData, item => item.location_id);
        let compareSeriesMeta = Object.keys(compareGroups).map(k => compareLookup[k]);

        // Parse date string as local time (not UTC) to avoid timezone issues
        const parseLocalDate = (dateStr) => {
            const [year, month, day] = dateStr.split('-').map(Number);
            return new Date(year, month - 1, day);
        };

        // Awkward, but idk better than dealing with missing dates by hand
        // and in theory we could have logic to allow for different resolutions.
        // which is a TODO
        let compareSeriesData = Object.values(compareGroups).map(
            j => j.map(i => [parseLocalDate(i.start_date), i])
        )
        
        // Reverse these so the right items show up on the line charts.
        compareSeriesMeta.reverse();
        compareSeriesData.reverse();

        // TODO: Need to deal with having comparisons NOT enabled
        let allLocationMeta = [
            this.location,
            ...compareSeriesMeta
        ];

        // Use start_date for axis positioning
        let seriesData = [
            this.indicatorData.map(i => [parseLocalDate(i.start_date), i]),
            ...compareSeriesData,
        ]

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

        // Keeps the grid sensible -- it was getting squashed
        if (window.innerWidth >= 1200) {
            grid.top = '10px';
            grid.left = '5px';
            grid.right = '5px';
            grid.bottom = hasLegend ? '35px' : '10px';
        } else {
            grid.top = '20px';
            grid.left = '5px';
            grid.right = '5px';
            grid.bottom = hasLegend ? '40px' : '20px';
        }
        
        let option = {
            ...this.chartOptions,
            color: this.colorScales.find(scale => scale.id === this.visual.color_scale_id).colors,
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
                trigger: 'axis',
                triggerOn: 'mousemove',
                formatter: params => {
                    const year = new Date(params[0].value[0]).getFullYear();
                    return buildTooltipContent(
                        String(year),
                        params[0].data.item,
                        this.indicator,
                        this.compareLocations,
                        this.compareData
                    );
                }
            },
            xAxis: {
                type: 'time',
                boundaryGap: false,
                minInterval: 365 * 24 * 60 * 60 * 1000,  // 1 year in milliseconds
                axisLabel: {
                    width: 100,
                    overflow: 'break',
                    showMinLabel: true,
                    showMaxLabel: true,
                    alignMinLabel: 'left',
                    alignMaxLabel: 'right',
                    formatter: value => String(new Date(value).getFullYear()),
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
                show: true,
                axisLabel: {
                    formatter: (value) => formatData(value, this.indicator.formatter, this.indicator.indicator_type !== 'rate')
                },
                ...(this.indicator.indicator_type === 'percentage' && {
                    min: 0,
                    max: 100
                })
            },
            series: seriesData
                .map(data => {
                    let leadingRow = data[0][1];

                    // data is an array of [timestamp, data]
                    return {
                        // consolidate to two series names - the name of the location being viewed and the name of the 
                        // other locations
                        // if there are only two series, use the location name for the second series name
                        name: leadingRow.location_id === this.location.id
                            ? this.location.name 
                            : this.visual.location_comparison_type === 'parents'
                                ? this.compareLocations.find(l => l.id === leadingRow.location_id).name
                                : 'Other ' 
                                    + this.locationTypes.find(lt => lt.id === this.location.location_type_id).name 
                                    + 's',
                        type: 'line',
                        data: data.map(([timestamp, item]) => ({ value: [timestamp, item.value], item: item })),
                        // make sure the location being viewed sits above the other locations
                        z: leadingRow.location_id === this.location.id ? 3 : 2,
                        // show symbols at all data points to make gaps visible
                        symbol: 'circle',
                        showSymbol: true,
                        symbolSize: leadingRow.location_id === this.location.id ? 8 : 6,
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
