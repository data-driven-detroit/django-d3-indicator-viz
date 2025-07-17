from django.forms.models import model_to_dict
from django.http import HttpResponse
from django.template import loader

from .models import Section, Category, IndicatorDataVisual, Indicator, IndicatorValue, Location, IndicatorFilterOption, LocationType

import json

def build_profile_context(request, location_slug=None):
    print("Building profile context for location:", location_slug)
    sections = Section.objects.all().order_by('sort_order').values()
    categories = Category.objects.all().order_by('sort_order').values()
    indicators = Indicator.objects.all().order_by('sort_order').values()
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
    indicator_values = IndicatorValue.objects.raw(
        """
        select *
        from indicator_value iv
            join location l on iv.location_id = l.id
            join indicator_data_visual idv on iv.indicator_id = idv.indicator_id and iv.source_id = idv.source_id
            join indicator i on iv.indicator_id = i.id
            left join indicator_filter_option ifo on iv.filter_option_id = ifo.id
        where (iv.location_id = %s
            or (idv.location_comparison_type = 'siblings' and l.location_type_id = %s)
            or (idv.location_comparison_type = 'parents' and l.id = any(%s)))
            and (iv.start_date = idv.start_date or idv.data_visual_type = 'line')
        order by i.sort_order, l.name, iv.start_date, ifo.sort_order
        """,
        (location.id, location.location_type.id, [loc['id'] for loc in parent_locations])
    )
    indicator_values_dict_list = [{
        'id': iv.id,
        'location_id': iv.location_id,
        'indicator_id': iv.indicator_id,
        'source_id': iv.source_id,
        'filter_option_id': iv.filter_option_id,
        'start_date': iv.start_date,
        'end_date': iv.end_date,
        'count': iv.count,
        'count_moe': iv.count_moe,
        'universe': iv.universe,
        'universe_moe': iv.universe_moe,
        'percentage': iv.percentage,
        'percentage_moe': iv.percentage_moe,
        'rate': iv.rate,
        'rate_moe': iv.rate_moe,
        'rate_per': iv.rate_per,
        'dollars': iv.dollars,
        'dollars_moe': iv.dollars_moe,
        'index': iv.index,
        'index_moe': iv.index_moe
    } for iv in indicator_values]
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
        'indicator_values_json': json.dumps(indicator_values_dict_list, default=str),
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