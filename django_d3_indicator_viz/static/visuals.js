import { getVisualContainer, getTableContainer, DataVisualLocationComparisonType } from "./utils.js";
import Ban from "./ban.js";
import ColumnChart from "./columnchart.js";
import LineChart from "./linechart.js";
import MinMedMaxChart from "./minmedmaxchart.js";
import DonutChart from "./donutchart.js";
import DataTable from "./datatable.js";

/**
 * The main visualization class that handles the rendering of different data visualizations.
 */
export default class Visuals {

    /**
     * Constructor for the Visuals class.
     * 
     * @param {Array} dataVisuals the data visuals to be rendered
     * @param {String} locationId the ID of the location
     * @param {Array} indicators the indicators
     * @param {Array} locations the locations
     * @param {Array} parentLocations the parent locations
     * @param {Array} locationTypes the location types
     * @param {Array} filterOptions the filter options
     * @param {Array} data the indicator data
     * @param {Array} colorScales the color scales
     * @param {Object} options additional options for echarts
     */
    constructor(dataVisuals, locationId, indicators, locations, parentLocations, locationTypes, filterOptions, data, colorScales, options = {}) {
        this.dataVisuals = dataVisuals;
        this.locationId = locationId;
        this.indicators = indicators;
        this.locations = locations;
        this.parentLocations = parentLocations;
        this.colorScales = colorScales;
        this.locationTypes = locationTypes;
        this.filterOptions = filterOptions;
        this.data = data;
        this.options = options;

        // draw the visualizations
        dataVisuals.forEach(visual => {
            this._draw(visual);
        });
    }

    /**
     * Draw the visualization for a specific visual object.
     * 
     * @param {Object} visual the data visual object
     */
    _draw(visual) {
        // get the visual container (required)
        let container = getVisualContainer(visual.indicator_id, visual.data_visual_type);
        if (!container) {
            console.error("Container not found for indicatorId:", visual.indicator_id);
            return;
        }
        // get the table container (not required for all data visual types)
        let tableContainer = getTableContainer(visual.indicator_id);
        // get the indicator (required)
        let indicator = this.indicators.find(ind => ind.id === visual.indicator_id);
        if (!indicator) {
            console.error("Indicator not found for indicatorId:", visual.indicator_id);
            return;
        }
        // get the location (required)
        let location = this.locations.find(loc => loc.id === this.locationId);
        if (!location) {
            console.error("Location not found for locationId:", this.locationId);
            return;
        }
        // get the visual data (required)
        let indicatorData = this._filterData(this.locationId, visual);
        if (!indicatorData) {
            console.error("Data not found for visual:", visual);
            return;
        }
        // get the locations and data for comparison
        let compareLocations = [];
        let compareData = [];
        if (visual.location_comparison_type) {
            if (visual.location_comparison_type === DataVisualLocationComparisonType.PARENTS) {
                compareLocations = this.parentLocations;
            } else if (visual.location_comparison_type === DataVisualLocationComparisonType.SIBLINGS) {
                compareLocations = this.locations.filter(loc => loc.location_type_id === location.location_type_id
                    && loc.id !== this.locationId);
            }
            if (visual.location_comparison_type && compareLocations.length === 0) {
                console.warn("No comparison locations found for visual:", visual);
            }
            compareLocations.forEach((location, index) => {
                compareData = compareData.concat(this._filterData(location.id, visual));
            });
            if (visual.location_comparison_type && compareData.length === 0) {
                console.warn("No comparison data found for visual:", visual);
            }
        }

        // create the visual
        switch (visual.data_visual_type) {
            case 'ban':
                new Ban(visual, container, indicator, location, indicatorData[0], compareLocations, compareData, this.filterOptions, this.options);
                break;
            case 'column':
                new ColumnChart(visual, container, indicator, location, indicatorData, compareLocations, compareData, this.filterOptions, this.colorScales, this.options);
                if (tableContainer) {
                    new DataTable(visual, tableContainer, indicator, location, indicatorData, compareLocations, compareData, this.filterOptions, this.options);
                }
                break;
            case 'line':
                new LineChart(visual, container, indicator, location, indicatorData, compareLocations, compareData, this.filterOptions, this.locationTypes, this.colorScales, this.options);
                if (tableContainer) {
                    new DataTable(visual, tableContainer, indicator, location, indicatorData, compareLocations, compareData, this.filterOptions, this.options);
                }
                break;
            case 'min_med_max':
                new MinMedMaxChart(visual, container, indicator, location, indicatorData[0], compareLocations, compareData, this.filterOptions, this.locationTypes, this.options);
                break;
            case 'donut':
                new DonutChart(visual, container, indicator, location, indicatorData, compareLocations, compareData, this.filterOptions, this.locationTypes, this.colorScales, this.options);
                if (tableContainer) {
                    new DataTable(visual, tableContainer, indicator, location, indicatorData, compareLocations, compareData, this.filterOptions, this.options);
                }
                break;
            default:
                console.error("Unknown data visual type:", visual.data_visual_type);
        }
    }

    /**
     * Filter data for a specific location ID and data visual.
     * 
     * @param {String} locationId - The ID of the location to filter data for.
     * @param {Object} visual - The data visual object.
     * @returns {Array} - The filtered data for the specified location ID.
     */
    _filterData(locationId, visual) {
        // filter for the data with a matching start/end date, unless it's a line chart
        return this.data.filter(d => d.location_id === locationId
            && (visual.data_visual_type === 'line' || d.start_date === visual.start_date)
            && (visual.data_visual_type === 'line' || d.end_date === visual.end_date)
            && d.source_id === visual.source_id
            && d.indicator_id === visual.indicator_id
        );
    }
}