from django.core.serializers import serialize
from django.db.models import Q, OuterRef, Subquery, Prefetch
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.template import loader
from django_filters import rest_framework as filters
from rest_framework import routers, serializers, viewsets

from .models import (
    Section,
    Category,
    ColorScale,
    IndicatorDataVisual,
    IndicatorDataVisualSource,
    Indicator,
    IndicatorValue,
    Location,
    CustomLocation,
    IndicatorFilterOption,
    LocationType,
    CopyDataEvent,
    assemble_header_data,
    assemble_custom_header_data,
)
from .serializers import (
    CategorySerializer,
    CustomLocationSerializer,
    DataVisualSerializer,
    IndicatorValueSerializer,
    IndicatorFilterOptionSerializer,
    LocationSerializer,
    LocationTypeSerializer,
    ColorScaleSerializer,
)
from django_d3_indicator_viz.indicator_value_aggregator import (
    aggregation_result,
    IndicatorValueAggregator,
)
from django_d3_indicator_viz.aggregation import (
    build_indicator_values_dict_list,
    aggregate_indicator_values,
    aggregate_indicator_value_set,
)

import json


def build_profile_context(request, location_slug, indicator_value_aggregator):
    """
    Build the context for the profile page. Mostly 
    """

    is_custom_location = False
    try:
        geoid, *slug = location_slug.split("-")

        location = Location.objects.get(id=geoid)

        (
            location_type,
            locations,
            parent_locations,
            location_geojson,
            sibling_locations_geojson,
            indicator_values_dict_list,
            header_data,
        ) = __build_standard_profile_context(location)

    except Location.DoesNotExist:
        try:
            location = CustomLocation.objects.get(slug__iexact=location_slug)
            is_custom_location = True

            (
                location_type,
                locations,
                parent_locations,
                location_geojson,
                sibling_locations_geojson,
                indicator_values_dict_list,
                header_data,
            ) = __build_custom_profile_context(location, indicator_value_aggregator)

        except CustomLocation.DoesNotExist:
            return None

    (
        sections,
        categories,
        indicators,
        location_types,
        color_scales,
        data_visuals,
        filter_options,
    ) = __build_common_profile_context(location_type, parent_locations, location.id)

    return {
        "sections": sections,
        "categories": categories,
        "indicators": indicators,
        "data_visuals": data_visuals,
        "header_data": header_data,
        "location": location,
        "location_type": location_type,
        "parent_locations": parent_locations,
        "indicators_json": json.dumps(list(indicators), default=str),
        "locations_json": json.dumps(list(locations), default=str),
        "location_geojson": location_geojson,
        "sibling_locations_geojson": sibling_locations_geojson,
        "parent_locations_json": json.dumps(list(parent_locations), default=str),
        "location_types_json": json.dumps(list(location_types), default=str),
        "color_scales_json": json.dumps(list(color_scales), default=str),
        "data_visuals_json": json.dumps(list(data_visuals), default=str),
        "indicator_values_json": json.dumps(indicator_values_dict_list, default=str),
        "filter_options_json": json.dumps(list(filter_options), default=str),
        "is_custom_location": is_custom_location,
    }


def __build_common_profile_context(location_type, parent_locations, location_id=None):
    sections = Section.objects.all().order_by("sort_order").values()
    categories = Category.objects.all().order_by("sort_order").values()
    indicators = Indicator.objects.all().order_by("sort_order").values()

    location_types = LocationType.objects.all().values()

    color_scales = ColorScale.objects.all().order_by("name").values()

    # Get data visuals with resolved sources based on data availability
    data_visuals = [
        dv.to_dict_with_resolved_source(location_id)
        for dv in IndicatorDataVisual.objects.filter(indicator__category_id__isnull=False)
            .prefetch_related('indicatordatavisualsource_set__source')
            .order_by("indicator__sort_order")
    ]
    # Filter out any that returned None (no sources configured)
    data_visuals = [dv for dv in data_visuals if dv is not None]

    filter_options = (
        IndicatorFilterOption.objects.all().order_by("sort_order").values()
    )

    return (
        sections,
        categories,
        indicators,
        location_types,
        color_scales,
        data_visuals,
        filter_options,
    )


def __build_standard_profile_context(location):
    location_type = location.location_type
    parent_location_types = location.location_type.parent_location_types.all()

    # Parent locations are of a different type than the profile location, 
    # set up as a parent type of the profile location's type, have a larger 
    # area, and contain the profile location's center point


    # limit to the two closest parent locations
    parent_locations = Location.objects.extra(
        select={"area": "st_area(geometry)"},
        where=[
            "location_type_id <> %s",
            "location_type_id = any(%s)",
            "st_area(geometry) > (select st_area(geometry) from location where id = %s)",
            "st_contains(geometry, (select st_pointonsurface(geometry) from location where id = %s))",
        ],
        params=[
            location_type.id,
            list(parent_location_types.values_list("id", flat=True)),
            location.id,
            location.id,
        ],
        order_by=["area"],
    )[:2].values()

    locations = (
        Location.objects.filter(
            Q(location_type_id=location_type.id)
            | Q(id__in=[loc["id"] for loc in parent_locations])
        )
        .order_by("location_type__name", "name")
        .values("id", "location_type_id", "name")
    )
    location_geojson = serialize(
        "geojson", [location], geometry_field="geometry", fields=("id", "name")
    )

    sibling_locations_geojson = serialize(
        "geojson",
        (
            Location.objects
            .filter(location_type_id=location_type.id)
            .exclude(id=location.id)
            .extra(
                where=["ST_DWithin(geometry, (SELECT geometry FROM location WHERE id = %s), %s)"],
                params=[location.id, 0.01]
            )
        ),
        geometry_field="geometry",
        fields=("id", "name", "location_type"),
    )

    # indicator values are all values for the profile location
    # additional values for the profile location's parents or siblings are included if the data visual's location comparison type is set
    # values are filtered by the corresponding data visual's source and start date (start date is ignored if the data visual type is 'line')
    indicator_values = IndicatorValue.objects.raw(
        """
        select iv.*, l.name, idv.*, i.*, ifo.*
        from indicator_value iv
            join location l on iv.location_id = l.id
            join indicator i on iv.indicator_id = i.id
            join indicator_data_visual idv on iv.indicator_id = idv.indicator_id
            join indicator_data_visual_source idvs on idvs.data_visual_id = idv.id and idvs.source_id = iv.source_id
            left join indicator_filter_option ifo on iv.filter_option_id = ifo.id
        where (iv.location_id = %s
            or (idv.location_comparison_type = 'siblings' and l.location_type_id = %s)
            or (idv.location_comparison_type = 'parents' and l.id = any(%s)))
            and (idv.start_date IS NULL or iv.start_date = idv.start_date or idv.data_visual_type = 'line')
            and (idv.start_date IS NOT NULL
                 or idv.data_visual_type = 'line'
                 or iv.end_date = (SELECT MAX(iv2.end_date)
                                  FROM indicator_value iv2
                                  WHERE iv2.indicator_id = iv.indicator_id
                                    AND iv2.source_id = iv.source_id))
        order by i.sort_order, l.name, iv.start_date, ifo.sort_order
        """,
        (
            location.id,
            location_type.id,
            [loc["id"] for loc in parent_locations],
        ),
    )
    indicator_values_dict_list = __build_indicator_values_dict_list(
        indicator_values
    )

    # indicators with no category will be shown in the header area
    from django.db.models import Exists, OuterRef, Subquery, Q
    from django.db.models.expressions import RawSQL

    header_data_visuals = list(
        IndicatorDataVisual.objects.filter(indicator__category_id__isnull=True)
        .select_related("indicator")
        .prefetch_related('indicatordatavisualsource_set__source')
        .extra(
            select={
                'header_value': '''
                    SELECT iv.value
                    FROM indicator_value iv
                    JOIN indicator_data_visual_source idvs ON iv.source_id = idvs.source_id
                    WHERE iv.indicator_id = indicator_data_visual.indicator_id
                      AND EXTRACT(YEAR FROM iv.end_date) = EXTRACT(YEAR FROM indicator_data_visual.end_date)
                      AND iv.location_id = %s
                      AND idvs.data_visual_id = indicator_data_visual.id
                    ORDER BY idvs.priority, iv.end_date DESC
                    LIMIT 1
                '''
            },
            select_params=(location.id,)
        )
        .order_by("indicator__sort_order")
    )

    header_data = [
        {
            "indicator_name": hdv.indicator.name,
            "source_name": hdv.indicatordatavisualsource_set.first().source.name if hdv.indicatordatavisualsource_set.first() else None,
            "year": str(hdv.end_date.year) if hdv.end_date else None,
            "value": hdv.header_value if hdv.header_value else None,
        }
        for hdv in header_data_visuals
    ]

    return (
        location_type,
        locations,
        parent_locations,
        location_geojson,
        sibling_locations_geojson,
        indicator_values_dict_list,
        header_data,
    )


def __build_custom_profile_context(location, indicator_value_aggregator):

    # Only one we need the geography on
    location_type = location.locations.first().location_type
    
    # This table says which 

    parent_location_types = location_type.parent_location_types.all()
    # parent locations are of a different type than the profile location, 
    # set up as a parent type of the profile location's type, have a larger area, 
    # and contain the profile location's center point limit to the two closest 
    # parent locations

    parent_locations = Location.objects.extra(
        select={"area": "st_area(geometry)"},
        where=[
            "location_type_id <> %s",
            "location_type_id = any(%s)",

            # This handles the 'custom' stuff basically unioning the 
            "st_area(geometry) > (select st_area(st_union(geometry)) from location where id = any(%s))",
            "st_contains(geometry, (select st_pointonsurface(st_union(geometry)) from location where id = any(%s)))",
        ],
        params=[
            location_type.id,
            list(parent_location_types.values_list("id", flat=True)),
            list(location.locations.values_list("id", flat=True)),
            list(location.locations.values_list("id", flat=True)),
        ],
        order_by=["area"],
    )[:2].values()
    locations = (
        Location.objects.filter(
            Q(location_type_id=location_type.id)
            | Q(id__in=[loc["id"] for loc in parent_locations])
        )
        .order_by("location_type__name", "name")
        .values("id", "location_type_id", "name")
    )
    locations = list(locations)
    # include the custom location in the locations list
    locations.append(
        {
            "id": str(location.id),
            "location_type_id": location.location_type_id,
            "name": location.name,
        }
    )
    location_geojson = serialize(
        "geojson",
        Location.objects.filter(
            Q(id__in=location.locations.values_list("id", flat=True))
        ),
        geometry_field="geometry",
        fields=("id", "name"),
    )
    # include all sibling locations of the same type as the profile location, including those that make up the custom location
    sibling_locations_geojson = serialize(
        "geojson",
        Location.objects.filter(Q(location_type_id=location_type.id)),
        geometry_field="geometry",
        fields=("id", "name", "location_type"),
    )

    # indicator values are all values for the profile location
    # additional values for the profile location's parents or siblings are included if the data visual's location comparison type is set
    # values are filtered by the corresponding data visual's source and start date (start date is ignored if the data visual type is 'line')
    custom_indicator_values = IndicatorValue.objects.raw(
        """
        select *
        from indicator_value iv
            join location l on iv.location_id = l.id
            join indicator i on iv.indicator_id = i.id
            join indicator_data_visual idv on iv.indicator_id = idv.indicator_id
            join indicator_data_visual_source idvs on idvs.data_visual_id = idv.id and idvs.source_id = iv.source_id
            left join indicator_filter_option ifo on iv.filter_option_id = ifo.id
        where iv.location_id = any(%s)
            and (idv.start_date IS NULL or iv.start_date = idv.start_date or idv.data_visual_type = 'line')
            and (idv.start_date IS NOT NULL
                 or idv.data_visual_type = 'line'
                 or iv.end_date = (SELECT MAX(iv2.end_date)
                                  FROM indicator_value iv2
                                  WHERE iv2.indicator_id = iv.indicator_id
                                    AND iv2.source_id = iv.source_id))
        order by i.sort_order, l.name, iv.start_date, ifo.sort_order
        """,
        ([id for id in location.locations.values_list("id", flat=True)],),
    )
    parent_sibling_indicator_values = IndicatorValue.objects.raw(
        """
        select *
        from indicator_value iv
            join location l on iv.location_id = l.id
            join indicator i on iv.indicator_id = i.id
            join indicator_data_visual idv on iv.indicator_id = idv.indicator_id
            join indicator_data_visual_source idvs on idvs.data_visual_id = idv.id and idvs.source_id = iv.source_id
            left join indicator_filter_option ifo on iv.filter_option_id = ifo.id
        where ((idv.location_comparison_type = 'siblings' and l.location_type_id = %s)
            or (idv.location_comparison_type = 'parents' and l.id = any(%s)))
            and (idv.start_date IS NULL or iv.start_date = idv.start_date or idv.data_visual_type = 'line')
            and (idv.start_date IS NOT NULL
                 or idv.data_visual_type = 'line'
                 or iv.end_date = (SELECT MAX(iv2.end_date)
                                  FROM indicator_value iv2
                                  WHERE iv2.indicator_id = iv.indicator_id
                                    AND iv2.source_id = iv.source_id))
        order by i.sort_order, l.name, iv.start_date, ifo.sort_order
        """,
        (location_type.id, [loc["id"] for loc in parent_locations]),
    )
    data_visuals = IndicatorDataVisual.objects.filter(
        indicator__category_id__isnull=False
    )
    indicator_values_dict_list = []
    for dv in data_visuals:
        indicator_values_dict_list.extend(
            __aggregate_indicator_values(
                location,
                dv,
                custom_indicator_values,
                indicator_value_aggregator,
            )
            or []
        )
    indicator_values_dict_list.extend(
        __build_indicator_values_dict_list(parent_sibling_indicator_values)
    )
    # indicators with no category will be shown in the header area
    header_data_visuals = IndicatorDataVisual.objects.filter(
        indicator__category_id__isnull=True
    ).prefetch_related('indicatordatavisualsource_set__source').order_by("indicator__sort_order")
    header_data = []
    for hdv in header_data_visuals:
        indicators = Indicator.objects.filter(id=hdv.indicator_id)
        indicator_values = IndicatorValue.objects.filter(
            indicator_id=hdv.indicator_id,
            location_id__in=location.locations.values_list("id", flat=True),
            source_id=hdv.get_primary_source().id if hdv.get_primary_source() else None,
            start_date=hdv.start_date,
            end_date=hdv.end_date,
        )
        aggregated_value = (
            __aggregate_indicator_values(
                location, hdv, indicator_values, indicator_value_aggregator
            )[0]
            if indicator_values.exists()
            else None
        )
        header_data.append(
            {
                "indicator_name": hdv.indicator.name,
                "source_name": hdv.get_primary_source().name if hdv.get_primary_source() else None,
                "year": str(hdv.end_date.year) if hdv.end_date else None,
                "value": aggregated_value.value if aggregated_value else None,
            }
        )

    return (
        location_type,
        locations,
        parent_locations,
        location_geojson,
        sibling_locations_geojson,
        indicator_values_dict_list,
        header_data,
    )


def __aggregate_indicator_values(
    custom_location, data_visual, indicator_values, indicator_value_aggregator
):
    return aggregate_indicator_values(
        custom_location, data_visual, indicator_values, indicator_value_aggregator
    )


def __aggregate_indicator_value_set(
    custom_location, data_visual, indicator_values, indicator_value_aggregator
):
    return aggregate_indicator_value_set(
        custom_location, data_visual, indicator_values, indicator_value_aggregator
    )


def __build_indicator_values_dict_list(indicator_values):
    return build_indicator_values_dict_list(indicator_values)


def roll_indicators(category, location):
    """
    Annoying that this is necessary, but we're handling the case where 
    there isn't a data visual associated with an indicator.
    """
    result = []
    for indicator in category.indicator_set.all():
        meta = indicator.get_visual_metadata(location)
        if not meta: continue
        result.append(
            {
                "id": indicator.id,
                "name": indicator.name,
                "rate_per": indicator.rate_per,
                "visual_metadata": meta,
                "formatter": indicator.formatter,
                "type": indicator.indicator_type,
                "qualifier": indicator.qualifier
            }
        )
    return result


def roll_section(section, primary_location, comparison_locations, custom_location=None, aggregator=None):
    """
    Pre computing some things.
    """
    return {
        "name": section.name,
        "anchor": section.anchor,
        "sort_order": section.sort_order,
        "categories": [
            {
                "id": category.id,
                "name": category.name,
                "about": category.about,
                "anchor": category.anchor,
                "indicators": roll_indicators(category, primary_location)
            } for category in section.category_set.all()
        ],
        "indicator_values": json.dumps(
            section.get_indicator_values(
                [primary_location, *comparison_locations],
                custom_location=custom_location,
                aggregator=aggregator,
            )
        ),
    }


def profile(request, location_id, indicator_value_aggregator=None,
            template_path="django_d3_indicators_viz/profile.html"):
    is_custom_location = False
    custom_location = None

    try:
        location = Location.objects.get(id=location_id)
    except Location.DoesNotExist:
        from django.http import Http404
        raise Http404

    location_type = location.location_type

    # Serialize location geometry
    if is_custom_location:
        location_geojson = serialize(
            "geojson",
            Location.objects.filter(id__in=location.get_constituent_ids()),
            geometry_field="geometry",
            fields=("id", "name"),
        )
    else:
        location_geojson = serialize(
            "geojson", [location], geometry_field="geometry", fields=("id", "name")
        )

    # Both Location and CustomLocation have get_parents()
    parent_locations = location.get_parents()

    # The display siblings only focusing on the bounding box that roughly
    # covers the map, where all siblings skips the geometry for a speed-up
    display_siblings = location.get_siblings(nearby=True)

    display_siblings_geojson = serialize(
        "geojson",
        display_siblings,
        geometry_field="geometry",
        fields=("id", "name", "location_type"),
    )

    # TODO (Mike): We'll eventually have to put this back, but for now
    # we don't compare with siblings, and when we do we have to get to
    # all siblings within parents -- which is different than display.
    # all_siblings = location.get_siblings(defer_geom=True)

    # This is messy, but these are needed globally and can't be called from within
    # the tree. These are expected to be complete even down to the charts layer ...
    filter_options = IndicatorFilterOption.objects.all()
    color_scales = ColorScale.objects.all()
    location_types = LocationType.objects.all()

    if is_custom_location:
        header_data = assemble_custom_header_data(location, indicator_value_aggregator)
    else:
        header_data = assemble_header_data(location_id)

    # Get the first section, but as an iterator, not individually.
    section = Section.objects.all().order_by('sort_order').first()

    # FIXME (Mike): This creates a list with these unpacks, to then
    # create another list within 'roll_section.' try to avoid this many
    # list creations.
    sections = [roll_section(
        section, location, parent_locations,
        custom_location=custom_location,
        aggregator=indicator_value_aggregator,
    )]

    # Build profile data for JavaScript (locations, filter options, etc.)
    if is_custom_location:
        primary_data = CustomLocationSerializer(location).data
    else:
        primary_data = LocationSerializer(location).data

    profile_data = {
        "filterOptions": IndicatorFilterOptionSerializer(filter_options, many=True).data,
        "colorScales": ColorScaleSerializer(color_scales, many=True).data,
        "locationTypes": LocationTypeSerializer(location_types, many=True).data,
        "locations": {
            "primary": primary_data,
            "parents": LocationSerializer(parent_locations, many=True).data,
            "siblings": [] # LocationSerializer(all_siblings, many=True).data,
        },
    }

    primary_loc_id = location.slug if is_custom_location else location_id

    return render(
        request, template_path,
        {
            "sections": sections,
            "profile_data_json": json.dumps(profile_data),
            "primary_loc_id": primary_loc_id,
            "parent_loc_ids": ",".join(loc.id for loc in parent_locations),
            "sibling_loc_ids": "", # ",".join(loc.id for loc in all_siblings),
            "header_data": header_data,
            "location": location,
            "location_type": location_type,
            "parent_locations": parent_locations,
            "location_geojson": location_geojson,
            "sibling_locations_geojson": display_siblings_geojson,
            "is_custom_location": is_custom_location,
        }
    )


def custom_profile(request, location_slug, indicator_value_aggregator=None,
                   template_path="django_d3_indicators_viz/profile.html"):
    is_custom_location = True

    try:
        location = CustomLocation.objects.get(slug__iexact=location_slug)
    except CustomLocation.DoesNotExist:
        from django.http import Http404
        raise Http404

    custom_location = location
    location_type = location.location_type

    # Serialize location geometry
    location_geojson = serialize(
        "geojson",
        Location.objects.filter(id__in=location.get_constituent_ids()),
        geometry_field="geometry",
        fields=("id", "name"),
    )

    # Both Location and CustomLocation have get_parents()
    parent_locations = location.get_parents()

    # The display siblings only focusing on the bounding box that roughly
    # covers the map, where all siblings skips the geometry for a speed-up
    display_siblings = location.get_siblings(nearby=True)

    display_siblings_geojson = serialize(
        "geojson",
        display_siblings,
        geometry_field="geometry",
        fields=("id", "name", "location_type"),
    )

    # These are needed globally and can't be called from within the tree.
    filter_options = IndicatorFilterOption.objects.all()
    color_scales = ColorScale.objects.all()
    location_types = LocationType.objects.all()

    header_data = assemble_custom_header_data(location, indicator_value_aggregator)

    # Get the first section, but as an iterator, not individually.
    section = Section.objects.all().order_by('sort_order').first()

    sections = [roll_section(
        section, location, parent_locations,
        custom_location=custom_location,
        aggregator=indicator_value_aggregator,
    )]

    # Build profile data for JavaScript (locations, filter options, etc.)
    primary_data = CustomLocationSerializer(location).data

    profile_data = {
        "filterOptions": IndicatorFilterOptionSerializer(filter_options, many=True).data,
        "colorScales": ColorScaleSerializer(color_scales, many=True).data,
        "locationTypes": LocationTypeSerializer(location_types, many=True).data,
        "locations": {
            "primary": primary_data,
            "parents": LocationSerializer(parent_locations, many=True).data,
            "siblings": [],
        },
    }

    primary_loc_id = location.slug

    return render(
        request, template_path,
        {
            "sections": sections,
            "profile_data_json": json.dumps(profile_data),
            "primary_loc_id": primary_loc_id,
            "parent_loc_ids": ",".join(loc.id for loc in parent_locations),
            "sibling_loc_ids": "",
            "header_data": header_data,
            "location": location,
            "location_type": location_type,
            "parent_locations": parent_locations,
            "location_geojson": location_geojson,
            "sibling_locations_geojson": display_siblings_geojson,
            "is_custom_location": is_custom_location,
        }
    )


def get_section(request, indicator_value_aggregator=None):
    after = request.GET.get("after")
    next_section = Section.objects.filter(sort_order__gt=after).first()

    if not next_section:
        return HttpResponse("")

    primary_loc_id = request.GET.get('primary_loc_id')
    parent_loc_ids = request.GET.get('parent_loc_ids', '')
    sibling_loc_ids = request.GET.get('sibling_loc_ids', '')
    is_custom = request.GET.get('is_custom', 'false') == 'true'

    # If you hit '', you'll get a list with [''] on split, so handle that case
    lst_parent_loc_ids = parent_loc_ids.split(",") if parent_loc_ids else []
    lst_sibling_loc_ids = sibling_loc_ids.split(",") if sibling_loc_ids else []

    is_custom_location = False
    custom_location = None
    try:
        location = Location.objects.get(id=primary_loc_id)
    except Location.DoesNotExist:
        location = CustomLocation.objects.get(slug__iexact=primary_loc_id)
        is_custom_location = True
        custom_location = location

    parent_locations = Location.objects.filter(id__in=lst_parent_loc_ids)

    return render(
        request, "django_d3_indicator_viz/section.html",
        {
            "section": roll_section(
                next_section, location, parent_locations,
                custom_location=custom_location,
                aggregator=indicator_value_aggregator,
            ),
            "primary_loc_id": primary_loc_id,
            "parent_loc_ids": parent_loc_ids,
            "sibling_loc_ids": "",
            "is_custom_location": is_custom,
        }
    )


def location_search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    locations = (
        Location.objects
        .filter(name__icontains=q)
        .select_related('location_type')
        .order_by('location_type__sort_order', 'name')[:15]
    )
    results = [
        {'id': loc.id, 'name': loc.name, 'location_type': loc.location_type.name}
        for loc in locations
    ]
    return JsonResponse({'results': results})


def indicator_search(request):
    q = request.GET.get('q', '').strip()
    if len(q) < 2:
        return JsonResponse({'results': []})
    indicators = (
        Indicator.objects
        .filter(name__icontains=q, category__isnull=False)
        .select_related('category')
        .order_by('sort_order')[:15]
    )
    results = [
        {'id': ind.id, 'name': ind.name}
        for ind in indicators
    ]
    return JsonResponse({'results': results})


def track_copy(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    data = json.loads(request.body)
    CopyDataEvent.objects.create(
        indicator_id=data.get('indicator_id'),
        location_id=data.get('location_id'),
    )
    return JsonResponse({'status': 'ok'})


# Create your views here.
def demo(request, location_slug=None):
    """
    Render the demo page.
    """
    template = loader.get_template("demo.html")
    context = build_profile_context(
        request, location_slug, SampleIndicatorValueAggregator()
    )
    return HttpResponse(template.render(context, request))
