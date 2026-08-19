import { formatData, showAggregateNotice, hasHighMoe, addHighMoeNotice, sortByFilterOption, renderNoData, DEFAULT_COLORS, redrawOnResize } from "./utils.js";

// Space between adjacent groups, as a share of the category band ECharts gives
// each group. ECharts centres a group inside its band, so half of this also
// lands before the first group and after the last one -- outerInsetPercent()
// below cancels those two outer halves so the gap only reads between groups.
const GROUP_GAP = 0.18;

// Space between the bars inside a single group, as a share of the bar width.
const BAR_GAP = '10%';

/**
 * How far to pull each end of the category axis outwards, as a percentage of
 * the visible span, so the bars sit flush to the edges.
 *
 * For a plot span P over n groups each band is P/n wide, and ECharts leaves
 * (GROUP_GAP / 2) * P/n empty at either end. Growing the span by d on both
 * sides makes P = V + 2d for a visible span V, and solving
 * d = GROUP_GAP * (V + 2d) / 2n gives d / V = GROUP_GAP / (2 * (n - GROUP_GAP)).
 *
 * @param {number} groupCount - number of category groups being drawn
 */
function outerInsetPercent(groupCount) {
    if (!groupCount) return 0;
    return 100 * GROUP_GAP / (2 * (groupCount - GROUP_GAP));
}

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
 * The Grouped Column chart visualization.
 *
 * Uses filter_option_id for x-axis categories and filter_option_2_id for the
 * bars within each category, drawn side-by-side rather than stacked. Same data
 * shape as the stacked column chart — only the layout differs.
 */
export default class GroupedColumnChart {

    /**
     * Creates a Grouped Column chart visualization.
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
     * @param {Object} axisScale the shared axis scale
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
        redrawOnResize(this);
    }

    /**
     * Draws a grouped column chart visual.
     */
    draw() {
        if (!this.indicatorData || !this.indicatorData.length) {
            renderNoData(this.container);
            return;
        }

        const isDesktop = window.innerWidth >= 1200;

        // Sort data by filter option order for consistent category ordering
        let sortedData = sortByFilterOption(this.indicatorData, this.filterOptions);

        // Build x-axis categories from filter_option_id (primary filter)
        let seenCategoryIds = [];
        sortedData.forEach(d => {
            if (!seenCategoryIds.includes(d.filter_option_id)) {
                seenCategoryIds.push(d.filter_option_id);
            }
        });
        let categories = seenCategoryIds.map(
            id => this.filterOptions.find(f => f.id === id)?.name ?? 'Unknown'
        );

        // Build the bars within each group from filter_option_2_id (secondary filter)
        // Sort by filter option sort_order for consistent legend/bar ordering
        let seenSegmentIds = [];
        sortedData.forEach(d => {
            if (d.filter_option_2_id != null && !seenSegmentIds.includes(d.filter_option_2_id)) {
                seenSegmentIds.push(d.filter_option_2_id);
            }
        });
        // Sort segment IDs by their filter option sort_order
        seenSegmentIds.sort((a, b) => {
            let aOrder = this.filterOptions.find(f => f.id === a)?.sort_order ?? 9999;
            let bOrder = this.filterOptions.find(f => f.id === b)?.sort_order ?? 9999;
            return aOrder - bOrder;
        });

        // Check if all data is inactive
        let allDataInactive = this.indicatorData.every(item => item.active_data === false);

        let colors = allDataInactive
            ? ['#CCCCCC', '#999999', '#777777', '#555555']
            : this.colorScales.find(scale => scale.id === this.visual.color_scale_id)?.colors
                || DEFAULT_COLORS;

        let hasLegend = seenSegmentIds.length > 1;

        // Build series - one per bar within the group (filter_option_2)
        let series = seenSegmentIds.map((segmentId, segmentIndex) => {
            let segmentName = this.filterOptions.find(f => f.id === segmentId)?.name ?? 'Unknown';

            // For each category, find the matching data point
            let seriesData = seenCategoryIds.map(categoryId => {
                let item = sortedData.find(
                    d => d.filter_option_id === categoryId && d.filter_option_2_id === segmentId
                );
                if (item) {
                    let highMoe = hasHighMoe(item);
                    if (highMoe) addHighMoeNotice(this.container);
                    // Labels sit outside the bar, so position depends on the value sign.
                    // ECharts ignores a function at series.label.position; per-item wins.
                    return { ...item, label: { position: getLabelPosition(item.value, isDesktop), distance: 6 } };
                }
                return { value: null };
            });

            return {
                name: segmentName,
                type: 'bar',
                data: seriesData,
                // Bar widths are left to ECharts so any number of segments fits the
                // band; the gaps control how tight each group reads. ECharts resolves
                // these per axis rather than per series, so every series repeats the
                // same values to keep the result independent of series order.
                barCategoryGap: (GROUP_GAP * 100) + '%',
                barGap: BAR_GAP,
                label: {
                    show: true,
                    fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 0.75 + 'px',
                    formatter: (params) => {
                        if (params.data.value === null || params.data.value === undefined) return '';
                        let isActive = params.data.active_data !== false;
                        let highMoe = hasHighMoe(params.data);
                        if (highMoe) addHighMoeNotice(this.container);
                        return formatData(params.data.value, this.indicator.formatter, true, isActive)
                            + (highMoe ? '†' : '')
                            + (showAggregateNotice(params.data) ? '*' : '');
                    }
                },
                emphasis: {
                    disabled: true
                },
                cursor: 'default',
                // Zero baseline — only attach to first series to avoid duplicating the line
                ...(segmentIndex === 0 ? {
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
            };
        });

        // set up the container - height grows with the total number of bars when
        // they are drawn horizontally
        let barCount = seenCategoryIds.length * Math.max(seenSegmentIds.length, 1);
        this.container.classList.add('column-chart-container');
        if (window.innerWidth < 768) {
            this.container.style.height = (barCount * 40) + (hasLegend ? 60 : 30) + 'px';
        } else if (!isDesktop) {
            this.container.style.height = (barCount * 24) + (hasLegend ? 60 : 30) + 'px';
        } else {
            this.container.style.height = hasLegend ? '240px' : '200px';
        }

        if (!isDesktop) {
            // Reverse categories for horizontal bars so they read top-to-bottom
            categories.reverse();
            series.forEach(s => { s.data = [...s.data].reverse(); });
        }

        // dispose the old chart (if redrawing)
        if (this.chart) {
            this.chart.dispose();
        }

        // configure the chart
        this.chart = echarts.init(this.container, null, { renderer: 'svg' });
        let categoryAxis = {
            type: 'category',
            data: categories,
            show: window.innerWidth >= 768,
            boundaryGap: true,
            axisLabel: {
                fontSize: (this.chartOptions.textStyle?.fontSize || 12) * 0.75 + 'px',
                interval: 0,
                width: 80,
                overflow: 'break',
                rotate: isDesktop && window.innerWidth < 1720 && categories.length > 12 ? 45 : 0
            },
            axisTick: { show: false },
            axisLine: { show: false },
            splitLine: { show: false }
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

        // Pull the ends of the category axis outwards by the half-gap ECharts
        // leaves outside the first and last group, so the bars run edge to edge.
        let outerInset = outerInsetPercent(seenCategoryIds.length);

        let grid = { containLabel: true };
        if (isDesktop) {
            // Vertical bars: the category axis runs left to right, so the
            // correction comes off the left and right edges.
            grid.left = -outerInset + '%';
            grid.right = -outerInset + '%';
            grid.top = '10px';
            grid.bottom = hasLegend ? '35px' : '10px';
        } else {
            // Horizontal bars: the category axis runs top to bottom, so the
            // same correction applies to the top and bottom instead. Those are
            // in px because the legend and axis labels claim a fixed amount,
            // and they are clamped at 0 so the bars can never ride over the
            // legend -- a very short chart keeps a sliver of end gap.
            let topPx = 20;
            let bottomPx = window.innerWidth >= 768
                ? (hasLegend ? 40 : 20)
                : (hasLegend ? 60 : 30);
            let containerHeight = parseInt(this.container.style.height, 10)
                || this.container.clientHeight;
            let plotHeight = containerHeight - topPx - bottomPx;
            let insetPx = (outerInset / 100) * plotHeight;

            grid.top = Math.max(0, topPx - insetPx) + 'px';
            grid.bottom = Math.max(0, bottomPx - insetPx) + 'px';
            if (window.innerWidth < 768) {
                grid.left = '0px';
            }
        }

        let option = {
            ...this.chartOptions,
            color: colors,
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
                axisPointer: { type: 'shadow' },
                formatter: params => {
                    let content = `<strong>${params[0].name}</strong>`;
                    params.forEach(p => {
                        if (p.data && p.data.value !== null && p.data.value !== undefined) {
                            let isActive = p.data.active_data !== false;
                            content += `<br/>${p.marker} ${p.seriesName}: ${formatData(p.data.value, this.indicator.formatter, true, isActive)}`;
                            if (showAggregateNotice(p.data)) {
                                content += '*';
                            }
                        }
                    });
                    return content;
                }
            },
            xAxis: isDesktop ? categoryAxis : valueAxis,
            yAxis: isDesktop ? valueAxis : categoryAxis,
            series: series
        };

        // Mobile: add label series for category names (same pattern as columnchart.js).
        // Pinned to 1px so it claims almost none of the group's band width.
        if (window.innerWidth < 768) {
            let labelSeries = {
                name: '',
                type: 'bar',
                barWidth: 1,
                data: categories.map(name => ({ value: 0, label: { name } })),
                label: {
                    show: true,
                    position: 'right',
                    distance: 0,
                    fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 0.75 + 'px',
                    formatter: function(params) {
                        return params.name;
                    },
                },
                emphasis: { disabled: true },
                cursor: 'default'
            };
            option.series = [labelSeries].concat(option.series);
        }

        this.chart.setOption(option);
    }
}
