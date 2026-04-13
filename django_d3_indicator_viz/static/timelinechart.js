import { formatData, buildTooltipContent, showAggregateNotice, parseLocalDate } from "./utils.js";

/**
 * Combined time-series line chart visualization.
 * Handles both 'line' (location comparisons) and 'multiline' (filter option groups) modes
 * based on visual.data_visual_type.
 */
export default class TimeLineChart {

    /**
     * Creates a time-series line chart visualization.
     *
     * @param {Object} visual the visual object
     * @param {Element} container the container element
     * @param {Object} indicator the indicator object
     * @param {Object} location the location object
     * @param {Array} indicatorData the indicator data for the primary location
     * @param {Array} compareLocations the comparison locations
     * @param {Array} compareData the comparison data
     * @param {Array} filterOptions the filter options
     * @param {Array} locationTypes the location types
     * @param {Array} colorScales the color scales
     * @param {Object} chartOptions the chart options for echarts
     */
    constructor(visual, container, indicator, location, indicatorData,
        compareLocations, compareData, filterOptions, locationTypes,
        colorScales, chartOptions = {}, axisScale = null) {

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
        this.axisScale = axisScale;
        this.chart = null;

        this.draw();

        // redraw the visualization on window resize
        window.addEventListener('resize', () => {
            this.draw();
        });
    }

    /**
     * Build series groups based on the visual type.
     *
     * Returns { groups, allDataInactive } where each group has:
     *   { name, data (array of items), z, symbolSize }
     */
    _buildSeriesGroups() {
        if (this.visual.data_visual_type === 'multiline') {
            return this._buildMultilineGroups();
        }
        return this._buildLineGroups();
    }

    /**
     * Build series groups for 'line' mode — grouped by location.
     */
    _buildLineGroups() {
        const compareLookup = Object.fromEntries(
            this.compareLocations.map(l => [l.id, l])
        );

        let compareGroups = Object.groupBy(this.compareData, item => item.location_id);
        let compareSeriesMeta = Object.keys(compareGroups).map(k => compareLookup[k]);
        let compareSeriesData = Object.values(compareGroups);

        // Reverse so the right items show up on the line charts
        compareSeriesMeta.reverse();
        compareSeriesData.reverse();

        // For 'line' mode, we need exactly one value per date per location.
        // Custom location aggregates often include multiple filter option breakdowns
        // (no null aggregate row), which causes zig-zag lines when plotted as one
        // series. Prefer null filter_option_id (aggregate); if none exist, fall back
        // to the first filter option so the chart still renders something.
        const pickOneFilterOption = (data) => {
            const hasNull = data.some(d => d.filter_option_id === null || d.filter_option_id === undefined);
            if (hasNull) {
                return data.filter(d => d.filter_option_id === null || d.filter_option_id === undefined);
            }
            const firstId = data.length > 0 ? data[0].filter_option_id : null;
            return data.filter(d => d.filter_option_id === firstId);
        };

        let allLocationMeta = [this.location, ...compareSeriesMeta];
        let allSeriesData = [
            pickOneFilterOption(this.indicatorData),
            ...compareSeriesData.map(pickOneFilterOption)
        ];

        let groups = allSeriesData.map((data, index) => {
            let loc = allLocationMeta[index];
            let isPrimary = loc.id === this.location.id;

            let name;
            if (isPrimary) {
                name = this.location.name;
            } else if (this.visual.location_comparison_type === 'parents') {
                name = this.compareLocations.find(l => l.id === loc.id).name;
            } else {
                name = 'Other '
                    + this.locationTypes.find(lt => lt.id === this.location.location_type_id).name
                    + 's';
            }

            return {
                name,
                data,
                z: isPrimary ? 3 : 2,
                symbolSize: isPrimary ? 8 : 6,
            };
        });

        return { groups, allDataInactive: false };
    }

    /**
     * Build series groups for 'multiline' mode — grouped by filter option.
     */
    _buildMultilineGroups() {
        let uniqueFilterOptionIds = [...new Set(this.indicatorData.map(d => d.filter_option_id))];
        let groups = [];

        uniqueFilterOptionIds.forEach((filterOptionId, index) => {
            let filteredData = this.indicatorData
                .filter(d => d.filter_option_id === filterOptionId)
                .sort((a, b) => new Date(a.start_date) - new Date(b.start_date));

            // Skip filter options that have no valid (non-null) values
            let hasValidData = filteredData.some(d => d.value !== null && d.value !== undefined);
            if (!hasValidData) return;

            let filterOption = this.filterOptions.find(fo => fo.id === filterOptionId);
            let seriesName = filterOption ? filterOption.name : 'Unknown';

            groups.push({
                name: seriesName,
                data: filteredData,
                z: 3 - index,
                symbolSize: 8,
            });
        });

        let allDataInactive = this.indicatorData.every(item => item.active_data === false);

        return { groups, allDataInactive };
    }

    /**
     * Build the tooltip formatter function based on the visual type.
     */
    _buildTooltipFormatter() {
        if (this.visual.data_visual_type === 'multiline') {
            return params => {
                const year = new Date(params[0].value[0]).getFullYear();
                let shouldRound = this.indicator.indicator_type !== 'rate';
                let content = `<strong>${year}</strong>`;
                params.forEach(p => {
                    let item = p.data.item;
                    let isActive = item.active_data !== false;
                    content += `<br/>${p.marker} ${p.seriesName}: ${formatData(item.value, this.indicator.formatter, shouldRound, isActive)}`;
                });
                return content;
            };
        }

        return params => {
            const year = new Date(params[0].value[0]).getFullYear();
            return buildTooltipContent(
                String(year),
                params[0].data.item,
                this.indicator,
                this.compareLocations,
                this.compareData
            );
        };
    }

    /**
     * Draws the time-series line chart.
     */
    draw() {
        if (!this.indicatorData || !this.indicatorData.length) {
            this.container.innerHTML = 'No data';
            return;
        }

        let { groups, allDataInactive } = this._buildSeriesGroups();

        // If no valid series data after filtering, show no data
        if (groups.length === 0) {
            this.container.innerHTML = 'No data';
            return;
        }

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

        const hasLegend = groups.length > 1;

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
                trigger: 'axis',
                triggerOn: 'mousemove',
                formatter: this._buildTooltipFormatter()
            },
            xAxis: {
                type: 'time',
                boundaryGap: false,
                minInterval: 365 * 24 * 60 * 60 * 1000,
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
                ...(this.axisScale && {
                    min: this.axisScale.min,
                    max: this.axisScale.max
                })
            },
            series: groups.map(group => ({
                name: group.name,
                type: 'line',
                data: group.data.map(item => ({
                    value: [parseLocalDate(item.start_date), item.value],
                    item: item
                })),
                z: group.z,
                symbol: 'circle',
                showSymbol: true,
                symbolSize: group.symbolSize,
                connectNulls: false,
                clip: false,
                lineStyle: {
                    width: 4
                },
                emphasis: {
                    disabled: true
                },
                cursor: 'default'
            }))
        };

        this.chart.setOption(option);
    }
}
