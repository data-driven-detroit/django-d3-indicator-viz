from django.core.serializers import serialize
from django.db.models import Q
from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse

from .indicator_value_aggregator import IndicatorValueAggregator

from .models import (
    Section,
    ColorScale,
    Indicator,
    Location,
    CustomLocation,
    IndicatorFilterOption,
    LocationType,
    CopyDataEvent,
    assemble_header_data,
    assemble_custom_header_data,
)
from .serializers import (
    CustomLocationSerializer,
    IndicatorFilterOptionSerializer,
    LocationSerializer,
    LocationTypeSerializer,
    ColorScaleSerializer,
)
import json


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
            template_path="django_d3_indicators_viz/profile.html",
            extra_context=None):
    indicator_value_aggregator = indicator_value_aggregator or IndicatorValueAggregator()
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

    context = {
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
    if extra_context:
        context.update(extra_context)

    return render(
        request, template_path,
        context
    )


def custom_profile(request, location_slug, indicator_value_aggregator=None,
                   template_path="django_d3_indicators_viz/profile.html"):
    indicator_value_aggregator = indicator_value_aggregator or IndicatorValueAggregator()
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
    indicator_value_aggregator = indicator_value_aggregator or IndicatorValueAggregator()
    after = request.GET.get("after")
    fetch_all = request.GET.get("all") == "true"

    remaining = Section.objects.filter(sort_order__gt=after).order_by("sort_order")
    if not fetch_all:
        remaining = remaining[:1]
    sections_list = list(remaining)

    if not sections_list:
        return HttpResponse("")

    primary_loc_id = request.GET.get('primary_loc_id')
    parent_loc_ids = request.GET.get('parent_loc_ids', '')
    sibling_loc_ids = request.GET.get('sibling_loc_ids', '')
    is_custom = request.GET.get('is_custom', 'false') == 'true'

    # If you hit '', you'll get a list with [''] on split, so handle that case
    lst_parent_loc_ids = parent_loc_ids.split(",") if parent_loc_ids else []

    is_custom_location = False
    custom_location = None
    try:
        location = Location.objects.get(id=primary_loc_id)
    except Location.DoesNotExist:
        location = CustomLocation.objects.get(slug__iexact=primary_loc_id)
        is_custom_location = True
        custom_location = location

    parent_locations = Location.objects.filter(id__in=lst_parent_loc_ids)

    if not fetch_all:
        # Single section (normal chain behavior)
        return render(
            request, "django_d3_indicator_viz/section.html",
            {
                "section": roll_section(
                    sections_list[0], location, parent_locations,
                    custom_location=custom_location,
                    aggregator=indicator_value_aggregator,
                ),
                "primary_loc_id": primary_loc_id,
                "parent_loc_ids": parent_loc_ids,
                "sibling_loc_ids": "",
                "is_custom_location": is_custom,
                "chain_next": True,
            }
        )

    # Batch: render all remaining sections, only last gets chain_next
    html_parts = []
    for i, section in enumerate(sections_list):
        is_last = (i == len(sections_list) - 1)
        html_parts.append(render_to_string(
            "django_d3_indicator_viz/section.html",
            {
                "section": roll_section(
                    section, location, parent_locations,
                    custom_location=custom_location,
                    aggregator=indicator_value_aggregator,
                ),
                "primary_loc_id": primary_loc_id,
                "parent_loc_ids": parent_loc_ids,
                "sibling_loc_ids": "",
                "is_custom_location": is_custom,
                "chain_next": is_last,
            },
            request=request,
        ))
    return HttpResponse("".join(html_parts))


def get_custom_section(request, indicator_value_aggregator=None):
    indicator_value_aggregator = indicator_value_aggregator or IndicatorValueAggregator()
    after = request.GET.get("after")
    fetch_all = request.GET.get("all") == "true"

    remaining = Section.objects.filter(sort_order__gt=after).order_by("sort_order")
    if not fetch_all:
        remaining = remaining[:1]
    sections_list = list(remaining)

    if not sections_list:
        return HttpResponse("")

    primary_loc_id = request.GET.get('primary_loc_id')
    parent_loc_ids = request.GET.get('parent_loc_ids', '')
    lst_parent_loc_ids = parent_loc_ids.split(",") if parent_loc_ids else []

    location = CustomLocation.objects.get(slug__iexact=primary_loc_id)
    parent_locations = Location.objects.filter(id__in=lst_parent_loc_ids)

    if not fetch_all:
        # Single section (normal chain behavior)
        return render(
            request, "django_d3_indicator_viz/section.html",
            {
                "section": roll_section(
                    sections_list[0], location, parent_locations,
                    custom_location=location,
                    aggregator=indicator_value_aggregator,
                ),
                "primary_loc_id": primary_loc_id,
                "parent_loc_ids": parent_loc_ids,
                "sibling_loc_ids": "",
                "is_custom_location": True,
                "chain_next": True,
            }
        )

    # Batch: render all remaining sections, only last gets chain_next
    html_parts = []
    for i, section in enumerate(sections_list):
        is_last = (i == len(sections_list) - 1)
        html_parts.append(render_to_string(
            "django_d3_indicator_viz/section.html",
            {
                "section": roll_section(
                    section, location, parent_locations,
                    custom_location=location,
                    aggregator=indicator_value_aggregator,
                ),
                "primary_loc_id": primary_loc_id,
                "parent_loc_ids": parent_loc_ids,
                "sibling_loc_ids": "",
                "is_custom_location": True,
                "chain_next": is_last,
            },
            request=request,
        ))
    return HttpResponse("".join(html_parts))


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

