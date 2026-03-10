"""
Factory classes for generating test data for django-d3-indicator-viz models.

Uses factory_boy to create model instances with realistic fake data.
"""
import factory
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyChoice, FuzzyDecimal, FuzzyInteger
from django.contrib.gis.geos import MultiPolygon, Polygon
from datetime import date


class SectionFactory(DjangoModelFactory):
    """Factory for Section model."""

    class Meta:
        model = 'django_d3_indicator_viz.Section'
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f"Test Section {n}")
    sort_order = factory.Sequence(lambda n: n)
    color = factory.Faker('hex_color')
    anchor = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))


class CategoryFactory(DjangoModelFactory):
    """Factory for Category model."""

    class Meta:
        model = 'django_d3_indicator_viz.Category'
        django_get_or_create = ('name', 'section')

    name = factory.Sequence(lambda n: f"Test Category {n}")
    about = factory.Faker('paragraph')
    sort_order = factory.Sequence(lambda n: n)
    section = factory.SubFactory(SectionFactory)
    color = factory.Faker('hex_color')
    anchor = factory.LazyAttribute(lambda obj: obj.name.lower().replace(' ', '-'))


class LocationTypeFactory(DjangoModelFactory):
    """Factory for LocationType model."""

    class Meta:
        model = 'django_d3_indicator_viz.LocationType'
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f"Location Type {n}")
    sort_order = factory.Sequence(lambda n: n)


class LocationFactory(DjangoModelFactory):
    """Factory for Location model."""

    class Meta:
        model = 'django_d3_indicator_viz.Location'

    id = factory.Sequence(lambda n: f"LOC{n:05d}")
    name = factory.Faker('city')
    location_type = factory.SubFactory(LocationTypeFactory)
    color = factory.Faker('hex_color')

    @factory.lazy_attribute
    def geometry(self):
        """Create a simple test polygon geometry."""
        # Create a simple square polygon
        # Note: Coordinates must be in (longitude, latitude) format
        coords = (
            (-84.0, 42.0),
            (-84.0, 42.1),
            (-83.9, 42.1),
            (-83.9, 42.0),
            (-84.0, 42.0),  # Close the polygon
        )
        polygon = Polygon(coords, srid=4326)  # WGS84 coordinate system
        # MultiPolygon expects a list/tuple of polygons
        multi = MultiPolygon([polygon], srid=4326)
        return multi


class IndicatorSourceFactory(DjangoModelFactory):
    """Factory for IndicatorSource model."""

    class Meta:
        model = 'django_d3_indicator_viz.IndicatorSource'
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f"Test Source {n}")


class IndicatorFactory(DjangoModelFactory):
    """Factory for Indicator model."""

    class Meta:
        model = 'django_d3_indicator_viz.Indicator'

    name = factory.Sequence(lambda n: f"Test Indicator {n}")
    qualifier = factory.Faker('sentence')
    sort_order = factory.Sequence(lambda n: n)
    category = factory.SubFactory(CategoryFactory)
    indicator_type = FuzzyChoice(['percentage', 'average', 'median', 'count', 'rate', 'index'])
    formatter = 'number'


class IndicatorFilterTypeFactory(DjangoModelFactory):
    """Factory for IndicatorFilterType model."""

    class Meta:
        model = 'django_d3_indicator_viz.IndicatorFilterType'
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f"Filter Type {n}")


class IndicatorFilterOptionFactory(DjangoModelFactory):
    """Factory for IndicatorFilterOption model."""

    class Meta:
        model = 'django_d3_indicator_viz.IndicatorFilterOption'
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f"Filter Option {n}")
    sort_order = factory.Sequence(lambda n: n)
    indicator_filter_type = factory.SubFactory(IndicatorFilterTypeFactory)


class IndicatorValueFactory(DjangoModelFactory):
    """Factory for IndicatorValue model."""

    class Meta:
        model = 'django_d3_indicator_viz.IndicatorValue'

    indicator = factory.SubFactory(IndicatorFactory)
    location = factory.SubFactory(LocationFactory)
    source = factory.SubFactory(IndicatorSourceFactory)
    filter_option = None  # Optional, can be set explicitly
    start_date = date(2018, 1, 1)
    end_date = date(2022, 12, 31)
    value = FuzzyDecimal(0.0, 100000.0, precision=2)
    value_moe = FuzzyDecimal(0.0, 1000.0, precision=2)
    count = None
    count_moe = None
    universe = None
    universe_moe = None


class ColorScaleFactory(DjangoModelFactory):
    """Factory for ColorScale model."""

    class Meta:
        model = 'django_d3_indicator_viz.ColorScale'
        django_get_or_create = ('name',)

    name = factory.Sequence(lambda n: f"Color Scale {n}")
    colors = factory.List([
        factory.Faker('hex_color') for _ in range(5)
    ])


class IndicatorDataVisualFactory(DjangoModelFactory):
    """Factory for IndicatorDataVisual model."""

    class Meta:
        model = 'django_d3_indicator_viz.IndicatorDataVisual'

    indicator = factory.SubFactory(IndicatorFactory)
    data_visual_type = FuzzyChoice(['ban', 'column', 'line', 'min_med_max', 'donut'])
    start_date = date(2018, 1, 1)
    end_date = date(2022, 12, 31)
    location_comparison_type = None  # Can be 'parents', 'siblings', or None
    color_scale = factory.SubFactory(ColorScaleFactory)
    columns = FuzzyInteger(1, 3)


class IndicatorDataVisualSourceFactory(DjangoModelFactory):
    """Factory for IndicatorDataVisualSource (through model)."""

    class Meta:
        model = 'django_d3_indicator_viz.IndicatorDataVisualSource'

    data_visual = factory.SubFactory(IndicatorDataVisualFactory)
    source = factory.SubFactory(IndicatorSourceFactory)
    priority = factory.Sequence(lambda n: n)


# Helper functions for creating complete data hierarchies

def create_complete_section(num_categories=2, num_indicators_per_category=3):
    """
    Create a complete section with categories, indicators, and data visuals.

    Args:
        num_categories: Number of categories to create
        num_indicators_per_category: Number of indicators per category

    Returns:
        Section instance with all related objects
    """
    section = SectionFactory()

    for _ in range(num_categories):
        category = CategoryFactory(section=section)

        for _ in range(num_indicators_per_category):
            indicator = IndicatorFactory(category=category)
            data_visual = IndicatorDataVisualFactory(indicator=indicator)
            # Create at least one source for the data visual
            IndicatorDataVisualSourceFactory(data_visual=data_visual, priority=0)

    return section


def create_indicator_with_values(location=None, num_values=5, with_filter_options=False):
    """
    Create an indicator with indicator values.

    Args:
        location: Location to use (creates new if None)
        num_values: Number of indicator values to create
        with_filter_options: Whether to create filter options

    Returns:
        Indicator instance with values
    """
    indicator = IndicatorFactory()
    location = location or LocationFactory()
    source = IndicatorSourceFactory()

    if with_filter_options:
        # Create values with different filter options
        for i in range(num_values):
            filter_option = IndicatorFilterOptionFactory()
            IndicatorValueFactory(
                indicator=indicator,
                location=location,
                source=source,
                filter_option=filter_option
            )
    else:
        # Create values without filter options
        for _ in range(num_values):
            IndicatorValueFactory(
                indicator=indicator,
                location=location,
                source=source
            )

    return indicator


def create_location_hierarchy():
    """
    Create a location hierarchy with state, county, and city.

    Returns:
        dict with 'state', 'county', 'city' Location instances
    """
    state_type = LocationTypeFactory(name="State", sort_order=0)
    county_type = LocationTypeFactory(name="County", sort_order=1)
    city_type = LocationTypeFactory(name="City", sort_order=2)

    # Set up parent relationships
    county_type.parent_location_types.add(state_type)
    city_type.parent_location_types.add(county_type, state_type)

    state = LocationFactory(location_type=state_type, name="Michigan")
    county = LocationFactory(location_type=county_type, name="Wayne County")
    city = LocationFactory(location_type=city_type, name="Detroit")

    return {
        'state': state,
        'county': county,
        'city': city
    }
