import { formatData, hasHighMoe, addHighMoeNotice, sortByFilterOption, renderNoData, redrawOnResize } from "./utils.js";

/**
 * The Quartile Line chart visualization.
 *
 * Renders pre-stored quartile values (Q1, Median, Q3) on a horizontal scale
 * with a shaded IQR band and labeled tick marks.  Data is stored as separate
 * filter_option rows; sort_order determines the quartile ordering (lowest =
 * Q1, middle = Median, highest = Q3).
 */
export default class QuartileLineChart {

    /**
     * @param {Object}  visual           the visual object
     * @param {Element} container        the container element
     * @param {Object}  indicator        the indicator object
     * @param {Object}  location         the location object
     * @param {Array}   indicatorData    array of indicator values (one per quartile)
     * @param {Array}   compareLocations (unused, kept for interface consistency)
     * @param {Array}   compareData      (unused)
     * @param {Array}   filterOptions    global filter options list
     * @param {Array}   locationTypes    (unused)
     * @param {Array}   colorScales      color scale definitions
     * @param {Object}  chartOptions     echarts base options
     */
    constructor(visual, container, indicator, location, indicatorData,
        compareLocations, compareData, filterOptions, locationTypes,
        colorScales, chartOptions = {}) {

        this.visual = visual;
        this.container = container;
        this.indicator = indicator;
        this.location = location;
        this.indicatorData = indicatorData;
        this.filterOptions = filterOptions;
        this.colorScales = colorScales;
        this.chartOptions = chartOptions;
        this.chart = null;

        this.draw();

        // redraw the visualization on window resize
        redrawOnResize(this);
    }

    /**
     * Draws the quartile line chart.
     */
    draw() {
        if (!this.indicatorData || !this.indicatorData.length) {
            renderNoData(this.container);
            return;
        }

        // Sort by filter option sort_order so quartiles are in order
        let sorted = sortByFilterOption(this.indicatorData, this.filterOptions);

        // We expect 3 items (Q1, Median, Q3) or 5 (Min, Q1, Median, Q3, Max)
        let quartileValues = sorted.map(d => d.value);
        let quartileNames = sorted.map(d => {
            let fo = this.filterOptions.find(f => f.id === d.filter_option_id);
            return fo ? fo.name : 'Unknown';
        });

        // Filter out null values
        let validIndices = quartileValues.reduce((acc, v, i) => {
            if (v !== null && v !== undefined) acc.push(i);
            return acc;
        }, []);

        if (validIndices.length < 2) {
            renderNoData(this.container, 'Insufficient data available');
            return;
        }

        let validValues = validIndices.map(i => quartileValues[i]);
        let minVal = Math.min(...validValues);
        let maxVal = Math.max(...validValues);

        // Identify Q1 (first), Median (middle), Q3 (last) from sorted valid items
        let q1Idx = validIndices[0];
        let medIdx = validIndices.length >= 3 ? validIndices[Math.floor(validIndices.length / 2)] : validIndices[0];
        let q3Idx = validIndices[validIndices.length - 1];

        let q1 = quartileValues[q1Idx];
        let median = quartileValues[medIdx];
        let q3 = quartileValues[q3Idx];

        // Resolve colors
        let colors = this.colorScales.find(scale => scale.id === this.visual.color_scale_id)?.colors
            || ['#5470c6'];
        let bandColor = colors[0];

        // Check for high MOE on any quartile value
        sorted.forEach(d => {
            if (hasHighMoe(d)) addHighMoeNotice(this.container);
        });

        // Set up the container
        this.container.classList.add('quartile-line-container');
        this.container.style.height = '48px';

        // Dispose the old chart (if redrawing)
        if (this.chart) {
            this.chart.dispose();
        }

        this.chart = echarts.init(this.container, null, { renderer: 'svg' });

        // Build tick values and labels for each quartile point
        let tickValues = validIndices.map(i => quartileValues[i]);

        let fontSize = (this.chartOptions.textStyle?.fontSize || 16) * 0.75;

        let option = {
            ...this.chartOptions,
            grid: {
                left: 8,
                right: 8,
                top: '10'
            },
            tooltip: {
                show: true,
                trigger: 'item',
                triggerOn: 'mousemove',
                formatter: params => {
                    let content = '';
                    sorted.forEach(d => {
                        let name = this.filterOptions.find(f => f.id === d.filter_option_id)?.name || '';
                        content += `<div><strong>${name}:</strong> ${formatData(d.value, this.indicator.formatter, true)}</div>`;
                    });
                    return content;
                }
            },
            xAxis: {
                type: 'value',
                boundaryGap: ['0%', '0%'],
                min: minVal,
                max: maxVal,
                axisLabel: {
                    margin: 12,
                    interval: 0,
                    width: 100,
                    overflow: 'break',
                    showMinLabel: true,
                    showMaxLabel: true,
                    alignMinLabel: 'left',
                    alignMaxLabel: 'right',
                    formatter: (value) => {
                        // Find which quartile this tick corresponds to
                        let idx = validIndices.find(i => quartileValues[i] === value);
                        let name = idx !== undefined ? quartileNames[idx] : '';
                        let dataItem = idx !== undefined ? sorted[idx] : null;
                        let highMoe = dataItem && hasHighMoe(dataItem);
                        let isActive = dataItem ? dataItem.active_data !== false : true;
                        return '{bold|' + name + ': }'
                            + '{normal|' + formatData(value, this.indicator.formatter, true, isActive) + '}'
                            + (highMoe ? '\u2020' : '');
                    },
                    rich: {
                        normal: { fontSize: fontSize },
                        bold: { fontWeight: 'bold', fontSize: fontSize }
                    },
                    customValues: tickValues
                },
                axisTick: {
                    show: true,
                    customValues: tickValues,
                    length: 8,
                    lineStyle: { width: 2 }
                },
                axisLine: { show: true },
                splitLine: { show: false }
            },
            yAxis: {
                type: 'value',
                min: 0,
                max: 0,
                show: false
            },
            series: [{
                type: 'scatter',
                // Invisible scatter point to anchor the markArea and markLine
                data: [{ value: [median, 0] }],
                symbolSize: 0,
                emphasis: { disabled: true },
                cursor: 'default',
                // Shaded IQR band between Q1 and Q3
                markArea: {
                    silent: true,
                    itemStyle: {
                        color: bandColor,
                        opacity: 0.2
                    },
                    data: [[{ xAxis: q1 }, { xAxis: q3 }]]
                },
                // Bold vertical line at the Median
                markLine: {
                    silent: true,
                    symbol: 'none',
                    lineStyle: {
                        color: bandColor,
                        width: 3,
                        type: 'solid'
                    },
                    label: { show: false },
                    data: [{ xAxis: median }]
                }
            }]
        };

        this.chart.setOption(option);
    }
}
