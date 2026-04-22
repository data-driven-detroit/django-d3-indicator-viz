# django-d3-indicator-viz
Django package for D3 indicators and data visuals

## Setup

### Installation
In addition to adding ```django-d3-indicator-viz``` to the ```INSTALLED_APPS``` in ```settings.py```, be sure to 
include the following apps:
- ```import_export```
- ```adminsortable2```
- ```django.contrib.gis```

### IndicatorValueAggregator
The package includes aggregation logic for custom aggregated locations. Logic for aggregating count, percentage, rate,
mean, and median values is provided. Index value aggregation returns empty results by default; override
`aggregate_index_values` and `aggregate_index_moe_values` if your project needs custom index aggregation.

```python
from django_d3_indicator_viz.indicator_value_aggregator import IndicatorValueAggregator

aggregator = IndicatorValueAggregator()
```

### Views
Wire up the profile views in ```urls.py``` using the function-based views provided by the package:

```python
from django_d3_indicator_viz import views as d3_views
from django_d3_indicator_viz.indicator_value_aggregator import IndicatorValueAggregator

# Standard location profile
path("profiles/<str:location_id>/", lambda r, location_id: d3_views.profile(
    r, location_id,
    indicator_value_aggregator=IndicatorValueAggregator(),
    template_path="my_app/profile.html",
), name="profile")

# Custom (aggregated) location profile
path("profiles/custom/<slug:location_slug>/", lambda r, location_slug: d3_views.custom_profile(
    r, location_slug,
    indicator_value_aggregator=IndicatorValueAggregator(),
    template_path="my_app/profile.html",
), name="custom_profile")
```

### Location Search Widget
The package includes a self-contained location search autocomplete widget. To add it to any page in your project, include the template:

```html
{% include "django_d3_indicator_viz/location_search.html" %}
```

This renders a text input with typeahead search. As the user types (minimum 2 characters), matching locations are shown in a dropdown with their location type. Selecting a result navigates to its profile page.

The widget requires that your project's URL configuration includes the library's URLs and that a URL named `profile` exists with a `location_id` parameter (see Urls section below).

Features:
- 250ms debounced search against the `api/location-search/` endpoint
- Keyboard navigation (arrow keys, Enter, Escape)
- Click-outside to dismiss
- CSS scoped with `.ddiv-search-*` prefix to avoid style collisions

### Urls
Add the profile view in ```urls.py```
> [!IMPORTANT]
> The ```location_slug``` must start with a location id from the ```Location``` model, optionally followed by a hyphen and any additional text, such as the location name for all standard locations. Custom locations allow for more flexibility, but cannot begin with a standard location id.

```python
from .views import (
    ProfileView
)
path(
    route="profiles/<slug:location_slug>/",
    view=ProfileView.as_view(),
    kwargs={},
    name="profile",
)
```

### Templates

#### HTML
To build the view template, simply loop through the sections, categories, and indicators. Create elements as needed, such as headings with the section/category/indicator names. For the data visuals, the package depends on a naming convention for the ID attribute on all data visual DOM elements:

```indicator-{indicatorId}-{dataVisualType}-container```

Where ```{dataVisualType}``` may be one of the following:
- ban
- column
- donut
- line
- multiline
- min_med_max
- datatable

For example,

```<div id="indicator-17-column-container"></div>```

#### JavaScript
Chart rendering is handled by `chart-connector.js`, which reads configuration from DOM data attributes on each `*-container` element. Import it once from your template (see `chart_roll.html` for the canonical pattern); it hooks into `htmx:load` so HTMX-swapped sections render automatically on arrival.

#### CSS
The following CSS classes are automatically added to data visual containers. These CSS classes may be used to apply styles to the containers, such as the container height.

|Data Visual Type|CSS Class|
|-|-|
|ban|```ban-container```|
|column|```column-chart-container```|
|donut|```donut-chart-container```|
|line|```line-chart-container```|
|min_med_max|```min-med-max-container```|

Additionally, the following CSS classes are applied to elements within HTML-rendered data visuals:

|Data Visual Type|CSS Class|Notes|
|-|-|-|
|ban|```ban-value-container```|Contains the BAN value and MOE|
|ban|```ban-value```|The BAN value|
|ban|```ban-moe```|The BAN MOE|
|ban|```ban-compare```|Contains the location comparison name, value, and MOE|
|ban|```ban-compare-moe```|The location comparison MOE|
|ban|```ban-compare-phrase```|The comparison phrase (e.g., 'about half of ')|
|ban|```ban-compare-location```|The compared location|
|ban|```ban-compare-value```|The compared location's value|
|datatable|```name```|The first cell in each row containing the name (e.g., 'Female')|
|datatable|```value```|The second cell in each row containing the value.|
|datatable|```context```|The third cell in each row containing the MOE|
|all types|```aggregate-notice```|The aggregate notice text (e.g., 'Based on 3 out of 4 locations with data available.')|

