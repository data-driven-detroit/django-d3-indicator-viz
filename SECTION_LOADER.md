# SectionLoader.js Documentation

## Overview

`SectionLoader` is a JavaScript class that loads and renders all charts 
for a section using pre-fetched data. It makes ONE API call to fetch all 
section data, then filters data client-side with indexed lookups for 
performance.

## Class Structure

### Constructor

```javascript
constructor(sectionData, options = {})
```

**Purpose:** Initialize the section loader with all data needed to render charts.

**Parameters:**
- `sectionData` - Object containing all data for this section:
  - `sectionData.section` - Section metadata `{id, name, sort_order}`
  - `sectionData.categories` - Array of categories with nested indicators
  - `sectionData.dataVisuals` - Array of data visual configurations
  - `sectionData.indicatorValues` - Array of all indicator values for this section
  - `sectionData.filterOptions` - Array of filter options (age groups, etc)
  - `sectionData.colorScales` - Array of color scale definitions
  - `sectionData.locations` - Object with `{primary, parents, siblings}`
  - `sectionData.locationTypes` - Array of location type definitions
- `options` - Object with chart options for echarts (animation settings, text styles, etc.)

**What it does:**
1. Stores all the data as instance properties
2. Calls `_buildIndexes()` to create fast lookup structures

---

## Methods

### `_buildIndexes()`

**Purpose:** Builds indexed data structures for fast O(1) lookups instead of O(n) array filtering.

**Creates three indexes:**

#### 1. `this.valueIndex` - Nested map for indicator values

Structure: `[indicator_id][location_id][source_id] -> array of values`

```javascript
{
  42: {                    // indicator_id
    "loc123": {            // location_id
      "src1": [            // source_id
        {id: 1, value: 100, start_date: "2023-01-01", ...},
        {id: 2, value: 105, start_date: "2022-01-01", ...}
      ]
    }
  }
}
```

**How it's built:**
- Loops through all `indicatorValues`
- Extracts `indicator_id`, `location_id`, `source_id` (handles both object and primitive values)
- Creates nested objects on demand
- Pushes each value into the appropriate array

**Why:** Allows O(1) lookup instead of filtering the entire indicatorValues array each time.

#### 2. `this.indicatorIndex` - Map of indicators by ID

Structure: `[indicator_id] -> indicator object`

```javascript
{
  42: {id: 42, name: "Median Income", formatter: "${value}", ...},
  43: {id: 43, name: "Population", formatter: "{value}", ...}
}
```

**How it's built:**
- Loops through all categories
- Loops through indicators in each category
- Stores each indicator by its ID

**Why:** Quick lookup of indicator metadata when rendering charts.

#### 3. `this.visualIndex` - Map of data visuals by indicator ID

Structure: `[indicator_id] -> visual object`

```javascript
{
  42: {
    id: 10,
    indicator_id: 42,
    data_visual_type: "column",
    source_id: 5,
    start_date: "2023-01-01",
    end_date: "2023-12-31",
    location_comparison_type: "parents",
    ...
  }
}
```

**How it's built:**
- Loops through all `dataVisuals`
- Stores each by its `indicator_id`

**Why:** Quick lookup of visual configuration for each indicator.

---

### `drawAll()`

**Purpose:** Main entry point to draw all charts in the section.

**What it does:**
- Loops through all `dataVisuals`
- Calls `_drawChart(visual)` for each one

**Usage:**
```javascript
const loader = new SectionLoader(sectionData);
loader.drawAll();
```

---

### `_drawChart(visual)`

**Purpose:** Draws a single chart for a given visual configuration.

**Parameters:**
- `visual` - A data visual object (from `dataVisuals` array)

**Steps:**

#### 1. Get the DOM containers
```javascript
const container = getVisualContainer(visual.indicator_id, visual.data_visual_type);
const tableContainer = getTableContainer(visual.indicator_id);
```
- `container` - Required. The div where the chart will render.
- `tableContainer` - Optional. The div where the data table will render (for some chart types).
- If container not found, logs error and returns early.

#### 2. Get the indicator
```javascript
const indicator = this.indicatorIndex[visual.indicator_id];
```
- Uses the indicator index for O(1) lookup
- If not found, logs error and returns early

#### 3. Get the primary location
```javascript
const location = this.locations.primary;
```
- Gets the primary location from the locations object
- If not found, logs error and returns early

#### 4. Get data for primary location
```javascript
const indicatorData = this._filterData(location.id, visual);
```
- Calls `_filterData()` to get values for this indicator/location/source
- If no data found, shows "No data available" and returns

#### 5. Get comparison locations and their data
```javascript
let compareLocations = [];
let compareData = [];

if (visual.location_comparison_type) {
  if (visual.location_comparison_type === "parents") {
    compareLocations = this.locations.parents || [];
  } else if (visual.location_comparison_type === "siblings") {
    compareLocations = this.locations.siblings || [];
  }

  compareLocations.forEach(loc => {
    const locData = this._filterData(loc.id, visual);
    if (locData && locData.length > 0) {
      compareData = compareData.concat(locData);
    }
  });
}
```
- Checks if this visual needs comparison data
- Gets parent or sibling locations based on `location_comparison_type`
- Fetches data for each comparison location
- Concatenates into `compareData` array

#### 6. Get shared axis scale (optional)
```javascript
let axisScale = null;
const categoryContainer = container.closest('[data-category-id]');
if (categoryContainer && categoryContainer.dataset.axisScale) {
  const categoryScale = JSON.parse(categoryContainer.dataset.axisScale);
  if (['line', 'column'].includes(visual.data_visual_type)) {
    axisScale = categoryScale;
  }
}
```
- Looks for a shared axis scale on the category container
- Only applies to line and column charts
- Allows multiple charts in a category to share the same Y-axis scale

#### 7. Render the chart
```javascript
this._renderChart(visual, container, tableContainer, indicator, location,
    indicatorData, compareLocations, compareData, axisScale);
```
- Calls `_renderChart()` with all the data collected

---

### `_filterData(locationId, visual)`

**Purpose:** Filters indicator values for a specific location and visual using indexed lookup.

**Parameters:**
- `locationId` - The location ID to filter for
- `visual` - The visual configuration object

**How it works:**

#### 1. Use indexed lookup (O(1))
```javascript
const byIndicator = this.valueIndex[visual.indicator_id];
if (!byIndicator) return [];

const byLocation = byIndicator[locationId];
if (!byLocation) return [];

const bySource = byLocation[visual.source_id];
if (!bySource) return [];
```
- Navigates through the nested index: indicator -> location -> source
- Returns empty array if any level doesn't exist
- Much faster than filtering the entire `indicatorValues` array

#### 2. Handle line charts vs. other charts
```javascript
if (visual.data_visual_type === 'line') {
  return bySource;  // Return ALL dates
}
```
- Line charts need all time points for the time series
- Returns the entire array of values for this indicator/location/source

#### 3. Filter by date for non-line charts
```javascript
return bySource.filter(d => {
  const startDateMatch = !visual.start_date || d.start_date === visual.start_date;
  const endDateMatch = !visual.end_date || d.end_date === visual.end_date;
  return startDateMatch && endDateMatch;
});
```
- Other chart types only show specific dates
- Filters to values matching the visual's start_date and end_date
- If visual doesn't specify dates, all dates match

**Returns:** Array of indicator value objects

---

### `_renderChart(visual, container, tableContainer, indicator, location, indicatorData, compareLocations, compareData, axisScale)`

**Purpose:** Renders a chart of the appropriate type using echarts.

**Parameters:**
- `visual` - Visual configuration
- `container` - DOM element for the chart
- `tableContainer` - DOM element for data table (optional)
- `indicator` - Indicator metadata
- `location` - Primary location object
- `indicatorData` - Array of values for primary location
- `compareLocations` - Array of comparison location objects
- `compareData` - Array of values for comparison locations
- `axisScale` - Optional shared axis scale `{min, max}`

**Steps:**

#### 1. Build chart options
```javascript
const chartOptions = {
  animation: false,
  textStyle: {
    fontFamily: 'inherit',
    fontSize: 16,
    color: '#000'
  },
  ...this.options
};
```
- Merges default options with any options passed to the constructor
- These are echarts configuration options

#### 2. Switch on visual type and instantiate appropriate chart class
```javascript
switch (visual.data_visual_type) {
  case 'ban':
    new Ban(visual, container, indicator, location, indicatorData[0],
            compareLocations, compareData, this.filterOptions, chartOptions);
    break;

  case 'column':
    new ColumnChart(visual, container, indicator, location, indicatorData,
                    compareLocations, compareData, this.filterOptions,
                    this.colorScales, visual.location_comparison_type,
                    chartOptions, axisScale);
    // Also render data table if container exists
    if (tableContainer) {
      new DataTable(...);
    }
    break;

  // ... similar for 'line', 'min_med_max', 'donut'
}
```

**Chart types and their data:**
- **ban** (Big Ass Number): Single value - uses `indicatorData[0]`
- **column**: Array of values (one per filter option) - uses full `indicatorData`
- **line**: Time series - uses full `indicatorData` with all dates
- **min_med_max**: Single value with min/med/max - uses `indicatorData[0]`
- **donut**: Array of values (segments) - uses full `indicatorData`

**Data tables:**
- Only rendered for `column`, `line`, and `donut` charts
- Requires `tableContainer` to exist
- Uses same data as the chart

---

## Data Flow Summary

```
1. Constructor receives sectionData
   ↓
2. _buildIndexes() creates fast lookup structures
   ↓
3. drawAll() loops through dataVisuals
   ↓
4. _drawChart(visual) for each visual
   ↓
5. _filterData() gets data using indexes (O(1) lookup)
   ↓
6. _renderChart() instantiates appropriate chart class
   ↓
7. Chart class (Ban, ColumnChart, etc.) renders using echarts
```

---

## Expected Data Structures

### sectionData object
```javascript
{
  section: {
    id: 1,
    name: "Demographics",
    sort_order: 1
  },

  categories: [
    {
      id: 10,
      name: "Population",
      indicators: [
        {
          id: 42,
          name: "Total Population",
          formatter: "{value}",
          indicator_type: "count",
          rate_per: null
        }
      ]
    }
  ],

  dataVisuals: [
    {
      id: 100,
      indicator_id: 42,
      data_visual_type: "column",
      source_id: 5,
      start_date: "2023-01-01",
      end_date: "2023-12-31",
      location_comparison_type: "parents",
      columns: 6,
      color_scale_id: 3
    }
  ],

  indicatorValues: [
    {
      id: 1000,
      indicator: 42,  // Can be ID or {id: 42, ...}
      location: "loc123",  // Can be ID or {id: "loc123", ...}
      source: 5,  // Can be ID or {id: 5, ...}
      filter_option: 10,
      start_date: "2023-01-01",
      end_date: "2023-12-31",
      value: 1500000,
      value_moe: 1000,
      count: 1500000,
      count_moe: 1000,
      universe: 1500000,
      universe_moe: 1000
    }
  ],

  filterOptions: [
    {id: 10, name: "All ages", sort_order: 0},
    {id: 11, name: "Under 18", sort_order: 1}
  ],

  colorScales: [
    {id: 3, name: "Blues", colors: ["#f0f0f0", "#2171b5"]}
  ],

  locations: {
    primary: {id: "loc123", name: "Detroit", location_type_id: 1},
    parents: [
      {id: "loc456", name: "Wayne County", location_type_id: 2}
    ],
    siblings: [
      {id: "loc789", name: "Ann Arbor", location_type_id: 1}
    ]
  },

  locationTypes: [
    {id: 1, name: "City", sort_order: 1},
    {id: 2, name: "County", sort_order: 2}
  ]
}
```

---

## Key Performance Features

1. **Single data fetch** - All data loaded in one API call, not per-chart
2. **Indexed lookups** - O(1) instead of O(n) for finding data
3. **Client-side filtering** - Fast filtering with pre-built indexes
4. **Section-scoped** - Only loads data needed for this section, not whole page

---

## Dependencies

- **Utility functions** (from `utils.js`):
  - `getVisualContainer(indicatorId, visualType)` - Finds chart container DOM element
  - `getTableContainer(indicatorId)` - Finds table container DOM element
  - `DataVisualLocationComparisonType` - Constants for comparison types

- **Chart classes** (echarts-based):
  - `Ban` - Big number displays
  - `ColumnChart` - Column/bar charts
  - `LineChart` - Time series line charts
  - `MinMedMaxChart` - Min/median/max displays
  - `DonutChart` - Donut/pie charts
  - `DataTable` - Data tables

All chart classes are instantiated with the constructor pattern - they render themselves upon instantiation.
