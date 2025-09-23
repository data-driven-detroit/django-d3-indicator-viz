from django.core.serializers import serialize
from django.db.models import Q
from django.http import HttpResponse
from django.template import loader

from .models import Section, Category, ColorScale, IndicatorDataVisual, Indicator, IndicatorValue, Location, CustomLocation, IndicatorFilterOption, LocationType
from django_d3_indicator_viz.indicator_value_aggregator import * 

import json

def build_profile_context(request, location_slug=None):
    """
    Build the context for the profile page.
    """

    is_custom_location = False
    try: 
        location = Location.objects.get(id__iexact=location_slug.split('-')[0])
        location_type, locations, parent_locations, location_geojson, sibling_locations_geojson, indicator_values_dict_list, header_data = __build_standard_profile_context(location)
    except (Location.DoesNotExist):
        try:
            location = CustomLocation.objects.get(slug__iexact=location_slug)
            is_custom_location = True
            location_type, locations, parent_locations, location_geojson, sibling_locations_geojson, indicator_values_dict_list, header_data = __build_custom_profile_context(location)
        except (CustomLocation.DoesNotExist):
            return None
        
    sections, categories, indicators, location_types, color_scales, data_visuals, filter_options = __build_common_profile_context(location_type, parent_locations)

    return {
        'sections': sections,
        'categories': categories,
        'indicators': indicators,
        'data_visuals': data_visuals,
        'header_data': header_data,
        'location': location,
        'location_type': location_type,
        'parent_locations': parent_locations,
        'indicators_json': json.dumps(list(indicators), default=str),
        'locations_json': json.dumps(list(locations), default=str),
        'location_geojson': location_geojson,
        'sibling_locations_geojson': sibling_locations_geojson,
        'parent_locations_json': json.dumps(list(parent_locations), default=str),
        'location_types_json': json.dumps(list(location_types), default=str),
        'color_scales_json': json.dumps(list(color_scales), default=str),
        'data_visuals_json': json.dumps(list(data_visuals), default=str),
        'indicator_values_json': json.dumps(indicator_values_dict_list, default=str),
        'filter_options_json': json.dumps(list(filter_options), default=str),
        'is_custom_location': is_custom_location
    }

def __build_common_profile_context(location_type, parent_locations):
    sections = Section.objects.all().order_by('sort_order').values()
    categories = Category.objects.all().order_by('sort_order').values()
    indicators = Indicator.objects.all().order_by('sort_order').values()
    
    location_types = LocationType.objects.all().values()
    
    color_scales = ColorScale.objects.all().order_by('name').values()
    data_visuals = IndicatorDataVisual.objects.filter(indicator__category_id__isnull=False).order_by('indicator__sort_order').values()
    filter_options = IndicatorFilterOption.objects.all().order_by('sort_order').values()

    return sections, categories, indicators, location_types, color_scales, data_visuals, filter_options

def __build_standard_profile_context(location):
    location_type = location.location_type
    parent_location_types = location.location_type.parent_location_types.all()
    # parent locations are of a different type than the profile location, set up as a parent type of the profile location's type, have a larger area, and contain the profile location's center point
    # limit to the two closest parent locations
    parent_locations = Location.objects.extra(
        select={ 'area': 'st_area(geometry)' },
        where=[
            'location_type_id <> %s',
            'location_type_id = any(%s)',
            'st_area(geometry) > (select st_area(geometry) from location where id = %s)',
            'st_contains(geometry, (select st_pointonsurface(geometry) from location where id = %s))'
        ],
        params=[location_type.id, list(parent_location_types.values_list('id', flat=True)), location.id, location.id],
        order_by=['area']
    )[:2].values()
    locations = Location.objects.filter(Q(location_type_id=location_type.id) | Q(id__in=[loc['id'] for loc in parent_locations])).order_by('location_type__name', 'name').values('id', 'location_type_id', 'name')
    location_geojson = serialize("geojson", [location], geometry_field='geometry', fields=('id', 'name'))
    sibling_locations_geojson = serialize("geojson", Location.objects.filter(Q(location_type_id=location_type.id) & ~Q(id=location.id)), geometry_field='geometry', fields=('id', 'name', 'location_type'))

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
        (location.id, location_type.id, [loc['id'] for loc in parent_locations])
    )
    indicator_values_dict_list = __build_indicator_values_dict_list(indicator_values)

    # indicators with no category will be shown in the header area
    header_data_visuals = IndicatorDataVisual.objects.filter(indicator__category_id__isnull=True).order_by('indicator__sort_order')
    header_data = [{
        'indicator_name': hdv.indicator.name,
        'source_name': hdv.source.name,
        'year': str(hdv.end_date.year) if hdv.end_date else None,
        'value': IndicatorValue.objects.filter(
            indicator_id=hdv.indicator_id, location_id=location.id, source_id=hdv.source_id, start_date=hdv.start_date, end_date=hdv.end_date
        ).first().value if IndicatorValue.objects.filter(
            indicator_id=hdv.indicator_id, location_id=location.id, source_id=hdv.source_id, start_date=hdv.start_date, end_date=hdv.end_date
        ).exists() else None,
    } for hdv in header_data_visuals]

    return location_type, locations, parent_locations, location_geojson, sibling_locations_geojson, indicator_values_dict_list, header_data

def __build_custom_profile_context(location):
    location_type = location.locations.first().location_type
    parent_location_types = location_type.parent_location_types.all()
    # parent locations are of a different type than the profile location, set up as a parent type of the profile location's type, have a larger area, and contain the profile location's center point
    # limit to the two closest parent locations
    parent_locations = Location.objects.extra(
        select={ 'area': 'st_area(geometry)' },
        where=[
            'location_type_id <> %s',
            'location_type_id = any(%s)',
            'st_area(geometry) > (select st_area(st_union(geometry)) from location where id = any(%s))',
            'st_contains(geometry, (select st_pointonsurface(st_union(geometry)) from location where id = any(%s)))'
        ],
        params=[location_type.id, list(parent_location_types.values_list('id', flat=True)), list(location.locations.values_list('id', flat=True)), list(location.locations.values_list('id', flat=True))],
        order_by=['area']
    )[:2].values()
    locations = Location.objects.filter(Q(location_type_id=location_type.id) | Q(id__in=[loc['id'] for loc in parent_locations])).order_by('location_type__name', 'name').values('id', 'location_type_id', 'name')
    locations = list(locations)
    # include the custom location in the locations list
    locations.append({'id': str(location.id), 'location_type_id': location.location_type_id, 'name': location.name})
    location_geojson = serialize("geojson", Location.objects.filter(Q(id__in=location.locations.values_list('id', flat=True))), geometry_field='geometry', fields=('id', 'name'))
    # include all sibling locations of the same type as the profile location, including those that make up the custom location
    sibling_locations_geojson = serialize("geojson", Location.objects.filter(Q(location_type_id=location_type.id)), geometry_field='geometry', fields=('id', 'name', 'location_type'))

    # indicator values are all values for the profile location
    # additional values for the profile location's parents or siblings are included if the data visual's location comparison type is set
    # values are filtered by the corresponding data visual's source and start date (start date is ignored if the data visual type is 'line')
    custom_indicator_values = IndicatorValue.objects.raw(
        """
        select *
        from indicator_value iv
            join location l on iv.location_id = l.id
            join indicator_data_visual idv on iv.indicator_id = idv.indicator_id and iv.source_id = idv.source_id
            join indicator i on iv.indicator_id = i.id
            left join indicator_filter_option ifo on iv.filter_option_id = ifo.id
        where iv.location_id = any(%s)
            and (iv.start_date = idv.start_date or idv.data_visual_type = 'line')
        order by i.sort_order, l.name, iv.start_date, ifo.sort_order
        """,
        ([id for id in location.locations.values_list('id', flat=True)],)
    )
    parent_sibling_indicator_values = IndicatorValue.objects.raw(
        """
        select *
        from indicator_value iv
            join location l on iv.location_id = l.id
            join indicator_data_visual idv on iv.indicator_id = idv.indicator_id and iv.source_id = idv.source_id
            join indicator i on iv.indicator_id = i.id
            left join indicator_filter_option ifo on iv.filter_option_id = ifo.id
        where ((idv.location_comparison_type = 'siblings' and l.location_type_id = %s)
            or (idv.location_comparison_type = 'parents' and l.id = any(%s)))
            and (iv.start_date = idv.start_date or idv.data_visual_type = 'line')
        order by i.sort_order, l.name, iv.start_date, ifo.sort_order
        """,
        (location_type.id, [loc['id'] for loc in parent_locations])
    )
    data_visuals = IndicatorDataVisual.objects.filter(indicator__category_id__isnull=False)
    indicator_values_dict_list = []
    for dv in data_visuals:
        indicator_values_dict_list.extend(__aggregate_indicator_values(location, dv, custom_indicator_values) or [])
    indicator_values_dict_list.extend(__build_indicator_values_dict_list(parent_sibling_indicator_values))
    # indicators with no category will be shown in the header area
    header_data_visuals = IndicatorDataVisual.objects.filter(indicator__category_id__isnull=True).order_by('indicator__sort_order')
    header_data = []
    for hdv in header_data_visuals:
        indicators = Indicator.objects.filter(id=hdv.indicator_id)
        indicator_values = IndicatorValue.objects.filter(
            indicator_id=hdv.indicator_id, location_id__in=location.locations.values_list('id', flat=True), source_id=hdv.source_id, start_date=hdv.start_date, end_date=hdv.end_date
        )
        aggregated_value = __aggregate_indicator_values(location, hdv, indicator_values)[0] if indicator_values.exists() else None
        header_data.append({
            'indicator_name': hdv.indicator.name,
            'source_name': hdv.source.name,
            'year': str(hdv.end_date.year) if hdv.end_date else None,
            'value': aggregated_value.value if aggregated_value else None,
        })

    return location_type, locations, parent_locations, location_geojson, sibling_locations_geojson, indicator_values_dict_list, header_data


def __aggregate_indicator_values(custom_location, data_visual, indicator_values):
    grouped_values = {}
    for iv in __build_indicator_values_dict_list(indicator_values):
        if iv['indicator_id'] != data_visual.indicator.id:
            continue
        key = (iv['filter_option_id'], iv['start_date'])
        if key not in grouped_values:
            grouped_values[key] = []
        grouped_values[key].append(iv)
    aggregated_values = []
    for (filter_option_id, start_date), ivs in grouped_values.items():
        aggregated_value = __aggregate_indicator_value_set(custom_location, data_visual, ivs)
        aggregated_values.append(aggregated_value)
    return aggregated_values

def __aggregate_indicator_value_set(custom_location, data_visual, indicator_values):
    aggregate_value = {
        'location_id': str(custom_location.id),
        'indicator_id': data_visual.indicator.id,
        'source_id': indicator_values[0]['source_id'] if indicator_values else None,
        'filter_option_id': indicator_values[0]['filter_option_id'] if indicator_values else None,
        'start_date': indicator_values[0]['start_date'] if indicator_values else None,
        'end_date': indicator_values[0]['end_date'] if indicator_values else None,
        'count': aggregate_count_values([iv['count'] for iv in indicator_values]),
        'count_moe': aggregate_count_moe_values([iv['count_moe'] for iv in indicator_values]),
        'universe': aggregate_count_values([iv['universe'] for iv in indicator_values]),
        'universe_moe': aggregate_count_moe_values([iv['universe_moe'] for iv in indicator_values]),
        'value': None,
        'value_moe': None,
        
    }

    if data_visual.indicator.indicator_type == 'percentage':
        aggregate_value['value'] = aggregate_percentage_values(
            [iv['count'] for iv in indicator_values],
            [iv['universe'] for iv in indicator_values]
        )
        aggregate_value['value_moe'] = aggregate_percentage_moe_values(
            [iv['count'] for iv in indicator_values],
            [iv['universe'] for iv in indicator_values],
            [iv['count_moe'] for iv in indicator_values],
            [iv['universe_moe'] for iv in indicator_values]
        )
    elif data_visual.indicator.indicator_type == 'median':
        aggregate_value['value'] = aggregate_median_values(
            [iv['value'] for iv in indicator_values],
            [iv['universe'] for iv in indicator_values]
        ) if aggregate_value['universe'] and aggregate_value['universe'] > 0 else None
        aggregate_value['value_moe'] = aggregate_median_moe_values(
            [iv['value'] for iv in indicator_values],
            [iv['universe'] for iv in indicator_values],
            [iv['value_moe'] for iv in indicator_values],
            [iv['universe_moe'] for iv in indicator_values]
        )
    elif data_visual.indicator.indicator_type == 'average':
        aggregate_value['value'] = aggregate_average_values(
            [iv['value'] for iv in indicator_values],
            [iv['universe'] for iv in indicator_values]
        ) if aggregate_value['universe'] and aggregate_value['universe'] > 0 else None
        aggregate_value['value_moe'] = aggregate_average_moe_values(
            [iv['value'] for iv in indicator_values],
            [iv['universe'] for iv in indicator_values],
            [iv['value_moe'] for iv in indicator_values],
            [iv['universe_moe'] for iv in indicator_values]
        )
    elif data_visual.indicator.indicator_type == 'rate':
        aggregate_value['value'] = aggregate_rate_values(
            [iv['count'] for iv in indicator_values],
            [iv['universe'] for iv in indicator_values],
            data_visual.rate_per
        ) if aggregate_value['universe'] and aggregate_value['universe'] > 0 else None
        aggregate_value['value_moe'] = aggregate_rate_moe_values(
            [iv['count'] for iv in indicator_values],
            [iv['universe'] for iv in indicator_values],
            [iv['count_moe'] for iv in indicator_values],
            [iv['universe_moe'] for iv in indicator_values],
            data_visual.rate_per
        )
    if data_visual.indicator.indicator_type == 'index':
        # TODO: implement index aggregation in indicator_value_aggregator.py. may need to be abstract since index is calculated differently depending on the indicator?
        pass

    return aggregate_value

def __build_indicator_values_dict_list(indicator_values):
    return [{
        'location_id': iv.location_id,
        'indicator_id': iv.indicator_id,
        'source_id': iv.source_id,
        'filter_option_id': iv.filter_option_id,
        'start_date': iv.start_date,
        'end_date': iv.end_date,
        'value': iv.value,
        'value_moe': iv.value_moe,
        'count': iv.count,
        'count_moe': iv.count_moe,
        'universe': iv.universe,
        'universe_moe': iv.universe_moe
    } for iv in indicator_values]

# Create your views here.
def demo(request, location_slug=None):
    """
    Render the demo page.
    """
    template = loader.get_template('demo.html')
    context = build_profile_context(request, location_slug)
    return HttpResponse(template.render(context, request))