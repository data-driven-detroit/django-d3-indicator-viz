# django-d3-indicator-viz
Django package for D3 indicators and data visuals

## Setup

### Installation
In addition to adding ```django-d3-indicator-viz``` to the ```INSTALLED_APPS``` in ```settings.py```, be sure to include the following apps:
- ```import_export```
- ```adminsortable2```
- ```django.contrib.gis```

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

        return super(NewGeographyDetailView, self).dispatch(*args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        return d3_views.build_profile_context(self.request, self.location_slug)
```

### Urls
Add the profile view in ```urls.py```
> [!IMPORTANT]
> The ```location_slug``` must start with a location id from the ```Location``` model, optionally followed by a hyphen and any additional text, such as the location name.

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
To build the view template, simply loop through the sections, categories, and indicators. Create elements as needed, such as headings with the section/category/indicator names. For the data visuals, the package depends on a naming convention for the ID attribuate on all data visual DOM elements:

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
To populate the data visual containers, simply create a new ```visuals``` instance, passing in the context variables from the view.
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
    {{ color_scales_json|safe }}
    {} // additional echarts options as needed
);
```

