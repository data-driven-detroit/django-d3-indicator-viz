import { getVisualContainer, DataVisualLocationComparisonType } from "./utils.js";
import Ban from "./ban.js";
import ColumnChart from "./columnchart.js";
import LineChart from "./linechart.js";
import MinMedMaxChart from "./minmedmaxchart.js";
import DonutChart from "./donutchart.js";

export default class Visuals {
    constructor(dataVisuals, locationId, indicators, locations, parentLocations, locationTypes, filterOptions, data, options = {}) {
        this.dataVisuals = dataVisuals;
        this.locationId = locationId;
        this.indicators = indicators;
        this.locations = locations;
        this.parentLocations = parentLocations;
        this.locationTypes = locationTypes;
        this.filterOptions = filterOptions;
        this.data = data;
        this.options = options;

        dataVisuals.forEach(visual => {
            this._draw(visual);
        });
    }

    _draw(visual) {
        let container = getVisualContainer(visual.indicator_id, visual.data_visual_type);
        if (!container) {
            console.error("Container not found for indicatorId:", visual.indicator_id);
            return;
        }
        let indicator = this.indicators.find(ind => ind.id === visual.indicator_id);
        if (!indicator) {
            console.error("Indicator not found for indicatorId:", visual.indicator_id);
            return;
        }
        let location = this.locations.find(loc => loc.id === this.locationId);
        if (!location) {
            console.error("Location not found for locationId:", this.locationId);
            return;
        }
        let indicatorData = this._filterData(this.locationId, visual);
        if (!indicatorData) {
            console.error("Data not found for visual:", visual);
            return;
        }
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
                return;
            }
            compareLocations.forEach((location, index) => {
                compareData = compareData.concat(this._filterData(location.id, visual));
            });
            if (visual.location_comparison_type && compareData.length === 0) {
                console.warn("No comparison data found for visual:", visual);
                return;
            }
        }

        switch (visual.data_visual_type) {
            case 'ban':
                new Ban(visual, container, indicator, location, indicatorData[0], compareLocations, compareData, this.filterOptions, this.options);
                break;
            case 'column':
                new ColumnChart(visual, container, indicator, location, indicatorData, compareLocations, compareData, this.filterOptions, this.options);
                break;
            case 'line':
                new LineChart(visual, container, indicator, location, indicatorData, compareLocations, compareData, this.filterOptions, this.locationTypes, this.options);
                break;
            case 'min_med_max':
                new MinMedMaxChart(visual, container, indicator, location, indicatorData[0], compareLocations, compareData, this.filterOptions, this.locationTypes, this.options);
                break;
            case 'donut':
                new DonutChart(visual, container, indicator, location, indicatorData, compareLocations, compareData, this.filterOptions, this.locationTypes, this.options);
                break;
            default:
                console.error("Unknown data visual type:", visual.data_visual_type);
        }
    }

    /**
     * Filter data for a specific location ID.
     * @param {number} locationId - The ID of the location to filter data for.
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