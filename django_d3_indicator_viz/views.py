from django.http import HttpResponse
from django.template import loader

from .models import Section, Category, IndicatorDataVisual, Indicator, IndicatorValue, Location, IndicatorFilterOption, LocationType

import json

def build_profile_context(request, location_slug=None):
    print("Building profile context for location:", location_slug)
    sections = Section.objects.all().order_by('sort_order').values()
    categories = Category.objects.all().order_by('sort_order').values()
    indicators = Indicator.objects.all().order_by('name').values()
    locations = Location.objects.all().order_by('location_type__name', 'name').values()
    location = Location.objects.get(name__iexact=location_slug.replace("-", " "))
    # parent locations are of a different type than the profile location, have a larger area, and contain the profile location's center point
    parent_locations = Location.objects.extra(
        select={ 'area': 'st_area(geometry)' },
        where=[
            'location_type_id <> %s',
            'st_area(geometry) > (select st_area(geometry) from location where id = %s)',
            'st_contains(geometry, (select st_pointonsurface(geometry) from location where id = %s))'
        ],
        params=[location.location_type.id, location.id, location.id],
        order_by=['area'],
    ).values()
    print("Parent locations found:", parent_locations)
    location_types = LocationType.objects.all().values()
    data_visuals = IndicatorDataVisual.objects.all().order_by('indicator__sort_order').values()
    # indicator values are all values for the profile location
    # additional values for the profile location's parents or siblings are included if the data visual's location comparison type is set
    # values are filtered by the corresponding data visual's source and start date (start date is ignored if the data visual type is 'line')
    indicator_values = IndicatorValue.objects.extra(
            tables=['location', 'indicator_data_visual', 'indicator_filter_option', 'indicator'],
            where=[
                'indicator_value.location_id = location.id',
                'indicator_value.filter_option_id = indicator_filter_option.id',
                'indicator_value.indicator_id = indicator.id',
                'indicator_value.source_id = indicator_data_visual.source_id',
                'indicator_value.indicator_id = indicator_data_visual.indicator_id',
                'indicator_value.start_date = indicator_data_visual.start_date OR indicator_data_visual.data_visual_type = \'line\'',
                """indicator_value.location_id = %s
                    OR (indicator_data_visual.location_comparison_type = \'siblings\' AND location.location_type_id = %s)
                    OR (indicator_data_visual.location_comparison_type = \'parents\' AND location.id = any(%s))"""
            ],
            params=[
                location.id,
                location.location_type.id,
                [loc.id for loc in parent_locations]
            ],
            order_by=['indicator.sort_order', 'location.name', 'indicator_value.start_date', 'indicator_filter_option.sort_order']
        ).values()
    filter_options = IndicatorFilterOption.objects.all().order_by('sort_order').values()

    return {
        'sections': sections,
        'categories': categories,
        'indicators': indicators,
        'data_visuals': data_visuals,
        'location_id': location.id,
        'indicators_json': json.dumps(list(indicators), default=str),
        'locations_json': json.dumps(list(locations), default=str),
        'parent_locations_json': json.dumps(list(parent_locations), default=str),
        'location_types_json': json.dumps(list(location_types), default=str),
        'data_visuals_json': json.dumps(list(data_visuals), default=str),
        'indicator_values_json': json.dumps(list(indicator_values), default=str),
        'filter_options_json': json.dumps(list(filter_options), default=str),
    }

# Create your views here.
def demo(request, location_slug=None):
    """
    Render the demo page.
    """
    template = loader.get_template('demo.html')
    context = build_profile_context(request, location_slug)
    return HttpResponse(template.render(context, request))