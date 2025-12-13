/**
 * Example data structure for SectionLoader
 *
 * This shows the expected format of data that should be returned
 * from the Django API endpoint for a section.
 */


export const profileData = {
    // These items are going to be used across all sections

    // Location type definitions
    locationTypes: [
        {
            id: 1,
            name: "State",
            sort_order: 0
        },
        {
            id: 2,
            name: "County",
            sort_order: 1
        },
        {
            id: 3,
            name: "City",
            sort_order: 2
        }
    ]

    // Filter options (age groups, race/ethnicity categories, etc.)
    filterOptions: [
        {
            id: 1,
            name: "Under 18",
            sort_order: 0
        },
        {
            id: 2,
            name: "18-64",
            sort_order: 1
        },
        {
            id: 3,
            name: "65+",
            sort_order: 2
        }
    ],

    // Color scales for visualizations
    colorScales: [
        {
            id: 1,
            name: "Blue Scale",
            colors: ["#08519c", "#3182bd", "#6baed6", "#9ecae1", "#c6dbef"]
        },
        {
            id: 2,
            name: "Sequential Green",
            colors: ["#00441b", "#006d2c", "#238b45", "#41ab5d", "#74c476", "#a1d99b"]
        }
    ],

    // Location data
    locations: {
        // Primary location being viewed
        primary: {
            id: "26163",
            name: "Detroit",
            location_type_id: 3,
            color: "#1f77b4"
        },
        // Parent locations (county, state, etc.)
        parents: [
            {
                id: "26",
                name: "Wayne County",
                location_type_id: 2,
                color: "#ff7f0e"
            },
            {
                id: "MI",
                name: "Michigan",
                location_type_id: 1,
                color: "#2ca02c"
            }
        ],
        // Sibling locations (same type, nearby)
        siblings: [
            {
                id: "2634000",
                name: "Grand Rapids",
                location_type_id: 3,
                color: "#d62728"
            },
            {
                id: "2622000",
                name: "Dearborn",
                location_type_id: 3,
                color: "#9467bd"
            }
        ]
    },

}


export const exampleSectionData = {
    // Section metadata
    section: {
        id: 1,
        name: "Demographics",
        sort_order: 0
    },

    // Categories with nested indicators
    categories: [
        {
            id: 1,
            name: "Population",
            sort_order: 0,
            section_id: 1,
            indicators: [
                {
                    id: 101,
                    name: "Total Population",
                    qualifier: null,
                    indicator_type: "count",
                    formatter: "number",
                    category_id: 1,
                    sort_order: 0
                },
                {
                    id: 102,
                    name: "Population by Age",
                    qualifier: "5-year estimates",
                    indicator_type: "count",
                    formatter: "number",
                    category_id: 1,
                    sort_order: 1
                }
            ]
        },
        {
            id: 2,
            name: "Housing",
            sort_order: 1,
            section_id: 1,
            indicators: [
                {
                    id: 201,
                    name: "Median Home Value",
                    qualifier: null,
                    indicator_type: "currency",
                    formatter: "currency",
                    category_id: 2,
                    sort_order: 0
                }
            ]
        }
    ],

    // Data visual configurations
    dataVisuals: [
        {
            id: 1,
            indicator_id: 101,
            data_visual_type: "ban",
            source_id: 1,
            start_date: "2018-01-01",
            end_date: "2022-12-31",
            location_comparison_type: null,
            color_scale_id: 1
        },
        {
            id: 2,
            indicator_id: 102,
            data_visual_type: "column",
            source_id: 1,
            start_date: "2018-01-01",
            end_date: "2022-12-31",
            location_comparison_type: "parents",
            color_scale_id: 2
        },
        {
            id: 3,
            indicator_id: 201,
            data_visual_type: "line",
            source_id: 2,
            start_date: null,
            end_date: null,
            location_comparison_type: "siblings",
            color_scale_id: 1
        }
    ],

    // All indicator values for this section
    // Includes data for primary location + comparison locations (parents/siblings)
    indicatorValues: [
        // Total Population - Primary Location
        {
            id: 1,
            indicator: 101,  // Can be ID or object with {id, name, ...}
            location: "26163",  // Can be ID or object
            source: 1,  // Can be ID or object
            filter_option: null,  // Can be null, ID, or object
            start_date: "2018-01-01",
            end_date: "2022-12-31",
            value: 670031,
            value_moe: 0,
            count: null,
            count_moe: null,
            universe: null,
            universe_moe: null
        },

        // Population by Age - Primary Location (multiple filter options)
        {
            id: 2,
            indicator: 102,
            location: "26163",
            source: 1,
            filter_option: 1,  // "Under 18"
            start_date: "2018-01-01",
            end_date: "2022-12-31",
            value: 145234,
            value_moe: 156,
            count: 145234,
            count_moe: 156,
            universe: 670031,
            universe_moe: 234
        },
        {
            id: 3,
            indicator: 102,
            location: "26163",
            source: 1,
            filter_option: 2,  // "18-64"
            start_date: "2018-01-01",
            end_date: "2022-12-31",
            value: 420156,
            value_moe: 298,
            count: 420156,
            count_moe: 298,
            universe: 670031,
            universe_moe: 234
        },
        {
            id: 4,
            indicator: 102,
            location: "26163",
            source: 1,
            filter_option: 3,  // "65+"
            start_date: "2018-01-01",
            end_date: "2022-12-31",
            value: 104641,
            value_moe: 187,
            count: 104641,
            count_moe: 187,
            universe: 670031,
            universe_moe: 234
        },

        // Population by Age - Parent Location (Wayne County)
        {
            id: 5,
            indicator: 102,
            location: "26",  // Wayne County
            source: 1,
            filter_option: 1,
            start_date: "2018-01-01",
            end_date: "2022-12-31",
            value: 421567,
            value_moe: 423,
            count: 421567,
            count_moe: 423,
            universe: 1749343,
            universe_moe: 567
        },
        {
            id: 6,
            indicator: 102,
            location: "26",
            source: 1,
            filter_option: 2,
            start_date: "2018-01-01",
            end_date: "2022-12-31",
            value: 1089234,
            value_moe: 678,
            count: 1089234,
            count_moe: 678,
            universe: 1749343,
            universe_moe: 567
        },
        {
            id: 7,
            indicator: 102,
            location: "26",
            source: 1,
            filter_option: 3,
            start_date: "2018-01-01",
            end_date: "2022-12-31",
            value: 238542,
            value_moe: 345,
            count: 238542,
            count_moe: 345,
            universe: 1749343,
            universe_moe: 567
        },

        // Median Home Value - Line chart with multiple years
        // Primary Location
        {
            id: 8,
            indicator: 201,
            location: "26163",
            source: 2,
            filter_option: null,
            start_date: "2010-01-01",
            end_date: "2014-12-31",
            value: 89000,
            value_moe: 1234,
            count: null,
            count_moe: null,
            universe: null,
            universe_moe: null
        },
        {
            id: 9,
            indicator: 201,
            location: "26163",
            source: 2,
            filter_option: null,
            start_date: "2015-01-01",
            end_date: "2019-12-31",
            value: 145000,
            value_moe: 1567,
            count: null,
            count_moe: null,
            universe: null,
            universe_moe: null
        },
        {
            id: 10,
            indicator: 201,
            location: "26163",
            source: 2,
            filter_option: null,
            start_date: "2018-01-01",
            end_date: "2022-12-31",
            value: 187000,
            value_moe: 1890,
            count: null,
            count_moe: null,
            universe: null,
            universe_moe: null
        },

        // Median Home Value - Sibling Location (Grand Rapids)
        {
            id: 11,
            indicator: 201,
            location: "2634000",  // Grand Rapids
            source: 2,
            filter_option: null,
            start_date: "2010-01-01",
            end_date: "2014-12-31",
            value: 125000,
            value_moe: 2345,
            count: null,
            count_moe: null,
            universe: null,
            universe_moe: null
        },
        {
            id: 12,
            indicator: 201,
            location: "2634000",
            source: 2,
            filter_option: null,
            start_date: "2015-01-01",
            end_date: "2019-12-31",
            value: 198000,
            value_moe: 2678,
            count: null,
            count_moe: null,
            universe: null,
            universe_moe: null
        },
        {
            id: 13,
            indicator: 201,
            location: "2634000",
            source: 2,
            filter_option: null,
            start_date: "2018-01-01",
            end_date: "2022-12-31",
            value: 245000,
            value_moe: 2987,
            count: null,
            count_moe: null,
            universe: null,
            universe_moe: null
        }
    ],
};

/**
 * Example usage:
 *
 * import SectionLoader from './sectionloader.js';
 * import { exampleSectionData } from './example_data.js';
 *
 * const loader = new SectionLoader(exampleSectionData);
 * loader.drawAll();
 */

/**
 * Notes on the data structure:
 *
 * 1. IDs vs Objects:
 *    - indicator, location, source, filter_option can be either:
 *      a) Simple IDs (101, "26163", etc.) - more compact
 *      b) Full objects ({id: 101, name: "Total Population", ...}) - self-contained
 *    - SectionLoader handles both formats
 *
 * 2. Dates:
 *    - Use ISO format strings: "2018-01-01"
 *    - Can be null for line charts that show all available dates
 *
 * 3. Comparison locations:
 *    - Always include data for primary location
 *    - Include parent data if any visual has location_comparison_type: "parents"
 *    - Include sibling data if any visual has location_comparison_type: "siblings"
 *
 * 4. Filter options:
 *    - Some indicators have no filter_option (null)
 *    - Others break down by age, race, etc. (multiple rows with different filter_option values)
 *
 * 5. MOE (Margin of Error):
 *    - ACS data includes margins of error for statistical validity
 *    - value_moe, count_moe, universe_moe correspond to their base fields
 *    - Can be 0 or null if not applicable
 *
 * 6. Performance:
 *    - This structure is optimized for a single API call per section
 *    - Client-side indexed filtering is very fast even with 1000+ indicator values
 *    - Better than making 10-20 API calls (one per chart)
 */
