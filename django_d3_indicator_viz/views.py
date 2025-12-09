from django.core.serializers import serialize
from django.db.models import Q, OuterRef, Subquery, Prefetch
from django.shortcuts import render
from django.http import HttpResponse
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
)
from django_d3_indicator_viz.indicator_value_aggregator import (
    aggregation_result,
    IndicatorValueAggregator,
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
            and (iv.start_date = idv.start_date or idv.data_visual_type = 'line')
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
    header_data_visuals = list(
        IndicatorDataVisual.objects.filter(indicator__category_id__isnull=True)
        .select_related("indicator")
        .prefetch_related('indicatordatavisualsource_set__source')
        .annotate(
            primary_source_id=Subquery(
                IndicatorDataVisualSource.objects.filter(
                    data_visual_id=OuterRef("id")
                ).order_by('priority').values('source_id')[:1]
            )
        )
        .annotate(
            header_value=Subquery(
                IndicatorValue.objects.filter(
                    indicator_id=OuterRef("indicator_id"),
                    source_id=OuterRef("primary_source_id"),
                    start_date=OuterRef("start_date"),
                    end_date=OuterRef("end_date"),
                    location_id=location.id,
                ).values("value")[:1]
            )
        )
        .order_by("indicator__sort_order")
    )

    header_data = [
        {
            "indicator_name": hdv.indicator.name,
            "source_name": hdv.get_primary_source().name if hdv.get_primary_source() else None,
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
            and (iv.start_date = idv.start_date or idv.data_visual_type = 'line')
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
            and (iv.start_date = idv.start_date or idv.data_visual_type = 'line')
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
    grouped_values = {}
    for iv in __build_indicator_values_dict_list(indicator_values):
        if iv["indicator_id"] != data_visual.indicator.id:
            continue
        key = (iv["filter_option_id"], iv["start_date"])
        if key not in grouped_values:
            grouped_values[key] = []
        grouped_values[key].append(iv)
    aggregated_values = []
    for (filter_option_id, start_date), ivs in grouped_values.items():
        aggregated_value = __aggregate_indicator_value_set(
            custom_location, data_visual, ivs, indicator_value_aggregator
        )
        aggregated_values.append(aggregated_value)
    return aggregated_values


def __aggregate_indicator_value_set(
    custom_location, data_visual, indicator_values, indicator_value_aggregator
):
    aggregate_value = {
        "location_id": str(custom_location.id),
        "indicator_id": data_visual.indicator.id,
        "source_id": (
            indicator_values[0]["source_id"] if indicator_values else None
        ),
        "filter_option_id": (
            indicator_values[0]["filter_option_id"]
            if indicator_values
            else None
        ),
        "start_date": (
            indicator_values[0]["start_date"] if indicator_values else None
        ),
        "end_date": (
            indicator_values[0]["end_date"] if indicator_values else None
        ),
        "count": indicator_value_aggregator.aggregate_count_values(
            [iv["count"] for iv in indicator_values]
        ).value,
        "count_moe": indicator_value_aggregator.aggregate_count_moe_values(
            [iv["count_moe"] for iv in indicator_values]
        ).value,
        "universe": indicator_value_aggregator.aggregate_count_values(
            [iv["universe"] for iv in indicator_values]
        ).value,
        "universe_moe": indicator_value_aggregator.aggregate_count_moe_values(
            [iv["universe_moe"] for iv in indicator_values]
        ).value,
        "value": None,
        "value_moe": None,
        "values_considered": None,
        "values_aggregated": None,
    }

    if data_visual.indicator.indicator_type == "count":
        aggregate_value_result = (
            indicator_value_aggregator.aggregate_count_values(
                [iv["count"] for iv in indicator_values]
            )
        )
        aggregate_moe_result = (
            indicator_value_aggregator.aggregate_count_moe_values(
                [iv["count_moe"] for iv in indicator_values]
            )
        )
        aggregate_value["value"] = aggregate_value_result.value
        aggregate_value["value_moe"] = aggregate_moe_result.value
        aggregate_value["values_considered"] = (
            aggregate_value_result.values_considered
        )
        aggregate_value["values_aggregated"] = (
            aggregate_value_result.values_aggregated
        )
    elif data_visual.indicator.indicator_type == "percentage":
        aggregate_value_result = (
            indicator_value_aggregator.aggregate_percentage_values(
                [iv["count"] for iv in indicator_values],
                [iv["universe"] for iv in indicator_values],
            )
        )
        aggregate_moe_result = (
            indicator_value_aggregator.aggregate_percentage_moe_values(
                [iv["count"] for iv in indicator_values],
                [iv["universe"] for iv in indicator_values],
                [iv["count_moe"] for iv in indicator_values],
                [iv["universe_moe"] for iv in indicator_values],
            )
        )
        aggregate_value["value"] = aggregate_value_result.value
        aggregate_value["value_moe"] = aggregate_moe_result.value
        aggregate_value["values_considered"] = (
            aggregate_value_result.values_considered
        )
        aggregate_value["values_aggregated"] = (
            aggregate_value_result.values_aggregated
        )
    elif data_visual.indicator.indicator_type == "median":
        aggregate_value_result = (
            indicator_value_aggregator.aggregate_median_values(
                [iv["value"] for iv in indicator_values],
                [iv["universe"] for iv in indicator_values],
            )
        )
        aggregate_moe_result = (
            indicator_value_aggregator.aggregate_median_moe_values(
                [iv["value"] for iv in indicator_values],
                [iv["universe"] for iv in indicator_values],
                [iv["value_moe"] for iv in indicator_values],
                [iv["universe_moe"] for iv in indicator_values],
            )
        )
        aggregate_value["value"] = aggregate_value_result.value
        aggregate_value["value_moe"] = aggregate_moe_result.value
        aggregate_value["values_considered"] = (
            aggregate_value_result.values_considered
        )
        aggregate_value["values_aggregated"] = (
            aggregate_value_result.values_aggregated
        )
    elif data_visual.indicator.indicator_type == "average":
        aggregate_result = indicator_value_aggregator.aggregate_average_values(
            [iv["value"] for iv in indicator_values],
            [iv["universe"] for iv in indicator_values],
        )
        aggregate_moe_result = (
            indicator_value_aggregator.aggregate_average_moe_values(
                [iv["value"] for iv in indicator_values],
                [iv["universe"] for iv in indicator_values],
                [iv["value_moe"] for iv in indicator_values],
                [iv["universe_moe"] for iv in indicator_values],
            )
        )
        aggregate_value["value"] = aggregate_result.value
        aggregate_value["value_moe"] = aggregate_moe_result.value
        aggregate_value["values_considered"] = (
            aggregate_result.values_considered
        )
        aggregate_value["values_aggregated"] = (
            aggregate_result.values_aggregated
        )
    elif data_visual.indicator.indicator_type == "rate":
        aggregate_result = indicator_value_aggregator.aggregate_rate_values(
            [iv["count"] for iv in indicator_values],
            [iv["universe"] for iv in indicator_values],
            data_visual.rate_per,
        )
        aggregate_moe_result = (
            indicator_value_aggregator.aggregate_rate_moe_values(
                [iv["count"] for iv in indicator_values],
                [iv["universe"] for iv in indicator_values],
                [iv["count_moe"] for iv in indicator_values],
                [iv["universe_moe"] for iv in indicator_values],
                data_visual.rate_per,
            )
        )
        aggregate_value["value"] = aggregate_result.value
        aggregate_value["value_moe"] = aggregate_moe_result.value
        aggregate_value["values_considered"] = (
            aggregate_result.values_considered
        )
        aggregate_value["values_aggregated"] = (
            aggregate_result.values_aggregated
        )
    elif data_visual.indicator.indicator_type == "index":
        # index aggregation not supported for custom locations in SDC
        pass

    return aggregate_value


def __build_indicator_values_dict_list(indicator_values):
    return [
        {
            "location_id": iv.location_id,
            "indicator_id": iv.indicator_id,
            "source_id": iv.source_id,
            "filter_option_id": iv.filter_option_id,
            "start_date": iv.start_date,
            "end_date": iv.end_date,
            "value": iv.value,
            "value_moe": iv.value_moe,
            "count": iv.count,
            "count_moe": iv.count_moe,
            "universe": iv.universe,
            "universe_moe": iv.universe_moe,
        }
        for iv in indicator_values
    ]


def profile(request, location_id, template_name="django_d3_indicator_viz/profile.html"):
    location = Location.objects.get(id=location_id)
    location_type = location.location_type
    parent_location_types = location.location_type.parent_location_types.all()

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
    )[:2]

    # Get sibling locations (same type, excluding current location)
    # This carries the geometry so can be a heavy pull
    sibling_locations = Location.objects.filter(
        location_type_id=location_type.id
    ).exclude(id=location_id)

    first_section = Section.objects.first()

    # Collect all locations for lookup (primary + parents + siblings)
    all_locations = [location] + list(parent_locations) + list(sibling_locations)

    # Serialize location geometry
    location_geojson = serialize(
        "geojson", [location], geometry_field="geometry", fields=("id", "name")
    )

    # This is messy, but these are needed globally and can't be called from within
    # the tree. These are expected to be complete even down to the charts layer ...
    filter_options = IndicatorFilterOption.objects.all()
    color_scales = ColorScale.objects.all()
    location_types = LocationType.objects.all()

    # Indicators with no category will be shown in the header area
    # They have no category and hence to section so they don't get pulled with
    # the first-section query.
    header_data_visuals = (
        IndicatorDataVisual.objects.filter(indicator__category_id__isnull=True)
        .select_related("indicator")
        .prefetch_related('indicatordatavisualsource_set__source')
        .annotate(
            primary_source_id=Subquery(
                IndicatorDataVisualSource.objects.filter(
                    data_visual_id=OuterRef("id")
                ).order_by('priority').values('source_id')[:1]
            )
        )
        .annotate(
            header_value=Subquery(
                IndicatorValue.objects.filter(
                    indicator_id=OuterRef("indicator_id"),
                    source_id=OuterRef("primary_source_id"),
                    start_date=OuterRef("start_date"),
                    end_date=OuterRef("end_date"),
                    location_id=location.id,
                ).values("value")[:1]
            )
        )
        .order_by("indicator__sort_order")
    )


    with open("header_data_query.sql", "w") as f:
        f.write(str(header_data_visuals.query))
    

    # NOTE (MIKE): Unsure why this renaming is needed, maybe refactor
    header_data = [
        {
            "indicator_name": hdv.indicator.name,
            "source_name": hdv.get_primary_source().name if hdv.get_primary_source() else None,
            "year": str(hdv.end_date.year) if hdv.end_date else None,
            "value": hdv.header_value if hdv.header_value else None,
        }
        for hdv in header_data_visuals
    ]

    return render(
        request, template_name,
        {
            "first_section": first_section,
            "primary_loc_id": location_id,
            "parent_loc_ids": ",".join(loc.id for loc in parent_locations),
            "sibling_loc_ids": ",".join(loc.id for loc in sibling_locations),
            "filter_options_json": json.dumps(IndicatorFilterOptionSerializer(filter_options, many=True).data),
            "color_scales_json": json.dumps(ColorScaleSerializer(color_scales, many=True).data),
            "location_types_json": json.dumps(LocationTypeSerializer(location_types, many=True).data),
            "locations_json": json.dumps(LocationSerializer(all_locations, many=True).data),
            "header_data": header_data,
            "location": location,
            "location_type": location_type,
            "parent_locations": parent_locations,
            "location_geojson": location_geojson,
            "sibling_locations_geojson": json.dumps({"type": "FeatureCollection", "features": []}),  # Empty initially, loaded later
            "is_custom_location": False,
        }
    )


def sibling_locations_geojson(request, location_id):
    """
    Returns the sibling locations geojson for a given location.
    This is a separate endpoint to avoid loading heavy geojson data on initial page load.
    """
    try:
        location = Location.objects.get(id=location_id)
        location_type = location.location_type

        # Get sibling locations (same type, excluding current location)
        sibling_locations = Location.objects.filter(
            location_type_id=location_type.id
        ).exclude(id=location_id)

        sibling_locations_geojson = serialize(
            "geojson",
            sibling_locations,
            geometry_field="geometry",
            fields=("id", "name", "location_type"),
        )

        return HttpResponse(sibling_locations_geojson, content_type="application/json")
    except Location.DoesNotExist:
        return HttpResponse(
            json.dumps({"type": "FeatureCollection", "features": []}),
            content_type="application/json",
            status=404
        )


def next_section(request):
    after = request.GET.get("after")
    next_section = Section.objects.filter(sort_order__gt=after).first()

    if not next_section:
        return HttpResponse("")

    # Get location context from query parameters
    primary_loc_id = request.GET.get('primary_loc_id')
    parent_loc_ids = request.GET.get('parent_loc_ids', '').split(',') if request.GET.get('parent_loc_ids') else []
    sibling_loc_ids = request.GET.get('sibling_loc_ids', '').split(',') if request.GET.get('sibling_loc_ids') else []

    # Filter out empty strings
    parent_loc_ids = [loc_id for loc_id in parent_loc_ids if loc_id]
    sibling_loc_ids = [loc_id for loc_id in sibling_loc_ids if loc_id]

    # Calculate axis scales for each category in this section
    category_scales = {}
    if primary_loc_id:
        for category in next_section.category_set.all():
            scale = category.get_axis_scale(
                primary_loc_id,
                parent_location_ids=parent_loc_ids,
                sibling_location_ids=sibling_loc_ids
            )
            if scale:
                category_scales[category.id] = scale

    return render(
        request, "django_d3_indicator_viz/section.html",
        {
            "section": next_section,
            "category_scales": category_scales
        }
    )


# A DRF Section to handle getting the data ready to be called by the chart code

class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicator
        fields = ['id', 'name', 'category_id', 'formatter', 'indicator_type', 'sort_order']


class IndicatorDataVisualSerializer(serializers.ModelSerializer):
    source_id = serializers.SerializerMethodField()
    source_name = serializers.SerializerMethodField()

    class Meta:
        model = IndicatorDataVisual
        fields = ['id', 'indicator_id', 'source_id', 'source_name', 'data_visual_type',
                  'location_comparison_type', 'start_date', 'end_date',
                  'color_scale_id', 'columns']

    def get_source_id(self, obj):
        """Returns the primary source ID (priority 0)."""
        primary_source = obj.get_primary_source()
        return primary_source.id if primary_source else None

    def get_source_name(self, obj):
        """Returns the primary source name."""
        primary_source = obj.get_primary_source()
        return primary_source.name if primary_source else None


class ColorScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorScale
        fields = ['id', 'name', 'colors']


class LocationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationType
        fields = ['id', 'name']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'location_type_id']


class IndicatorFilterOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicatorFilterOption
        fields = ['id', 'name', 'sort_order']


class ValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicatorValue
        fields = ["source", "start_date", "end_date", "indicator",
            "filter_option", "location", "value", "value_moe", "count",
            "count_moe", "universe", "universe_moe", "active_data"]


class ValueFilter(filters.FilterSet):
    class Meta:
        model = IndicatorValue
        fields = {
            'location_id': ['exact', 'in'],
            'indicator_id': ['exact', 'in'],
            'start_date': ['exact', 'gte', 'lte'],
            'end_date': ['exact', 'gte', 'lte'],
        }


class ValueViewSet(viewsets.ModelViewSet):
    queryset = IndicatorValue.objects.all().select_related("filter_option")
    serializer_class = ValueSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_fields = ("start_date", "end_date", "indicator_id", "location_id")
    filterset_class = ValueFilter

router = routers.DefaultRouter()
router.register("values", ValueViewSet)


class SampleIndicatorValueAggregator(IndicatorValueAggregator):
    def aggregate_index_values(self, index_values):
        raise NotImplementedError

    def aggregate_index_moe_values(self, index_values, index_moe_values):
        raise NotImplementedError


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
