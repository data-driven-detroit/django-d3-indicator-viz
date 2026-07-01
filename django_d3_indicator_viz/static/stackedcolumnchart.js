import { formatData, showAggregateNotice, hasHighMoe, addHighMoeNotice, sortByFilterOption } from "./utils.js";

/**
 * Returns black or white depending on which has better contrast against
 * the given background hex color, using perceived luminance.
 * @param {string} hex - A hex color string (e.g. '#3a7bd5' or '3a7bd5')
 * @returns {string} '#000' or '#fff'
 */
function contrastTextColor(hex) {
    hex = hex.replace('#', '');
    if (hex.length === 3) {
        hex = hex[0] + hex[0] + hex[1] + hex[1] + hex[2] + hex[2];
    }
    let r = parseInt(hex.substring(0, 2), 16);
    let g = parseInt(hex.substring(2, 4), 16);
    let b = parseInt(hex.substring(4, 6), 16);
    // Perceived luminance (ITU-R BT.601)
    let luminance = (0.299 * r + 0.587 * g + 0.114 * b);
    return luminance > 150 ? '#000' : '#fff';
}

/**
 * The Stacked Column chart visualization.
 *
 * Uses filter_option_id for x-axis categories and filter_option_2_id
 * for stack segments within each bar.
 */
export default class StackedColumnChart {

    /**
     * Creates a Stacked Column chart visualization.
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
        window.addEventListener('resize', () => {
            this.draw();
        });
    }

    /**
     * Draws a stacked column chart visual.
     */
    draw() {
        if (!this.indicatorData || !this.indicatorData.length) {
            this.container.innerHTML = 'No data';
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

        // Build stack segments from filter_option_2_id (secondary filter)
        // Sort by filter option sort_order for consistent legend/stack ordering
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

        // Resolve colors for contrast-aware labels
        let colors = allDataInactive
            ? ['#CCCCCC', '#999999', '#777777', '#555555']
            : this.colorScales.find(scale => scale.id === this.visual.color_scale_id).colors;

        // Build series - one per stack segment (filter_option_2)
        let series = seenSegmentIds.map((segmentId, segmentIndex) => {
            let segmentName = this.filterOptions.find(f => f.id === segmentId)?.name ?? 'Unknown';
            let seriesColor = colors[segmentIndex % colors.length];
            let labelColor = contrastTextColor(seriesColor);

            // For each category, find the matching data point
            let seriesData = seenCategoryIds.map(categoryId => {
                let item = sortedData.find(
                    d => d.filter_option_id === categoryId && d.filter_option_2_id === segmentId
                );
                if (item) {
                    let highMoe = hasHighMoe(item);
                    if (highMoe) addHighMoeNotice(this.container);
                    return item;
                }
                return { value: null };
            });

            return {
                name: segmentName,
                type: 'bar',
                stack: 'total',
                data: seriesData,
                barWidth: '85%',
                label: {
                    show: true,
                    position: 'inside',
                    color: labelColor,
                    fontSize: (this.chartOptions.textStyle?.fontSize || 16) * 0.75 + 'px',
                    formatter: (params) => {
                        if (params.data.value === null || params.data.value === undefined) return '';
                        if (params.data.value < 20) return '';
                        let isActive = params.data.active_data !== false;
                        return formatData(params.data.value, this.indicator.formatter, true, isActive);
                    }
                },
                emphasis: {
                    disabled: true
                },
                cursor: 'default',
            };
        });

        let hasLegend = seenSegmentIds.length > 1;

        // set up the container
        this.container.classList.add('column-chart-container');
        if (window.innerWidth < 768) {
            this.container.style.height = (seenCategoryIds.length * 60) + (hasLegend ? 60 : 30) + 'px';
        } else if (!isDesktop) {
            this.container.style.height = (seenCategoryIds.length * 30) + (hasLegend ? 60 : 30) + 'px';
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

        let grid = { containLabel: true };
        if (isDesktop) {
            grid.left = '0px';
            grid.right = '0px';
            grid.top = '10px';
            grid.bottom = hasLegend ? '35px' : '10px';
        } else if (window.innerWidth >= 768) {
            grid.top = '20px';
            grid.bottom = hasLegend ? '40px' : '20px';
        } else {
            grid.top = '20px';
            grid.bottom = hasLegend ? '60px' : '30px';
            grid.left = '0px';
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

        // Mobile: add label series for category names (same pattern as columnchart.js)
        if (window.innerWidth < 768) {
            let labelSeries = {
                name: '',
                type: 'bar',
                stack: 'total-label',
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
