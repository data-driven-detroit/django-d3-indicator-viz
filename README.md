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
mean, and median values is provided. However, implementation of aggregation logic for index values is abstract and must 
be provided by the project installing this package. If no index aggregation is needed, simply extend the base class
and raise an error in the unneeded abstract methods:

```python
from django_d3_indicator_viz import indicator_value_aggregator

class MyIndicatorValueAggregator(indicator_value_aggregator.IndicatorValueAggregator):
    def aggregate_index_values(self, index_values):
        raise NotImplementedError('This project does not support index aggregation.')

    def aggregate_index_moe_values(self, index_values, index_moe_values):
        raise NotImplementedError('This project does not support index MOE aggregation.')
```

### Views
Create the profile view in  ```views.py```

```python
from django_d3_indicator_viz import (
    views as d3_views,
)
class ProfileView(TemplateView):
    template_name = "profile.html"

    def dispatch(self, *args, **kwargs):
        self.location_slug = kwargs.get("location_slug")
        if not self.location_slug:
            raise Http404("No location_slug provided.")

        return super(ProfileView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        return d3_views.build_profile_context(self.request, self.location_slug, MyIndicatorValueAggregator)
```

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
- min_med_max
- datatable

For example,

```<div id="indicator-17-column-container"></div>```

#### JavaScript
To populate the data visual containers, simply create a new ```Visuals``` instance, passing in the context variables from the view.
```javascript
import Visuals from "../visuals.js";
const visuals = new Visuals(
    {{ data_visuals_json|safe }},
    '{{ location.id|safe }}',
    {{ indicators_json|safe }},
    {{ locations_json|safe }},
    {{ parent_locations_json|safe }},
    {{ location_types_json|safe }},
    {{ filter_options_json|safe }},
    {{ indicator_values_json|safe }},
    {{ color_scales_json|safe }},
    {{ utils.DataVisualComparisonMode.TOOLTIP }}
    {} // additional echarts options as needed
);
```

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

