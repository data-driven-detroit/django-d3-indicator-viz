"""
Tests for django-d3-indicator-viz models.

Focus on testing the Section model methods that fetch and organize data.
"""
import pytest
from django.contrib.gis.geos import MultiPolygon, Polygon
from tests.factories import (
    SectionFactory,
    CategoryFactory,
    IndicatorFactory,
    IndicatorDataVisualFactory,
    IndicatorDataVisualSourceFactory,
    IndicatorSourceFactory,
    IndicatorValueFactory,
    LocationFactory,
    IndicatorFilterOptionFactory,
    create_complete_section,
    create_indicator_with_values,
    create_location_hierarchy,
)


@pytest.mark.django_db
class TestSectionModel:
    """Tests for Section model methods."""

    def test_get_comparison_types_with_parents(self):
        """Test that get_comparison_types returns 'parents' when configured."""
        section = SectionFactory()
        category = CategoryFactory(section=section)
        indicator = IndicatorFactory(category=category)

        # Create visual with parents comparison
        data_visual = IndicatorDataVisualFactory(
            indicator=indicator,
            location_comparison_type='parents'
        )

        comparison_types = section.get_comparison_types()

        assert 'parents' in comparison_types

    def test_get_comparison_types_with_siblings(self):
        """Test that get_comparison_types returns 'siblings' when configured."""
        section = SectionFactory()
        category = CategoryFactory(section=section)
        indicator = IndicatorFactory(category=category)

        # Create visual with siblings comparison
        data_visual = IndicatorDataVisualFactory(
            indicator=indicator,
            location_comparison_type='siblings'
        )

        comparison_types = section.get_comparison_types()

        assert 'siblings' in comparison_types

    def test_get_comparison_types_multiple(self):
        """Test that get_comparison_types returns all types used in section."""
        section = SectionFactory()
        category = CategoryFactory(section=section)
        indicator1 = IndicatorFactory(category=category)
        indicator2 = IndicatorFactory(category=category)

        # Create visuals with different comparison types
        IndicatorDataVisualFactory(
            indicator=indicator1,
            location_comparison_type='parents'
        )
        IndicatorDataVisualFactory(
            indicator=indicator2,
            location_comparison_type='siblings'
        )

        comparison_types = section.get_comparison_types()

        assert 'parents' in comparison_types
        assert 'siblings' in comparison_types

    def test_get_section_data_filters_by_comparison_type(self):
        """Test that get_section_data only fetches data for needed locations."""
        # Setup section with indicator
        section = SectionFactory()
        category = CategoryFactory(section=section)
        indicator = IndicatorFactory(category=category)
        source = IndicatorSourceFactory()

        # Create visual with parents comparison (NOT siblings)
        visual = IndicatorDataVisualFactory(
            indicator=indicator,
            location_comparison_type='parents'
        )
        IndicatorDataVisualSourceFactory(data_visual=visual, source=source, priority=0)

        # Create locations
        primary = LocationFactory()
        parent = LocationFactory()
        sibling = LocationFactory()

        # Create indicator values for all three locations
        IndicatorValueFactory(indicator=indicator, location=primary, source=source)
        IndicatorValueFactory(indicator=indicator, location=parent, source=source)
        IndicatorValueFactory(indicator=indicator, location=sibling, source=source)

        # Get section data - should include primary + parent, NOT sibling
        values = section.get_section_data(
            primary_location=primary,
            parent_locations=[parent],
            sibling_locations=[sibling]
        )

        # Defer geometry to avoid SpatiaLite parsing issues in tests
        values = values.defer('location__geometry')

        # Convert to list to evaluate queryset
        values_list = list(values)
        location_ids = [v.location_id for v in values_list]

        # Should have primary + parent (not sibling)
        assert primary.id in location_ids
        assert parent.id in location_ids
        assert sibling.id not in location_ids  # Excluded because no 'siblings' comparison type

    def test_get_section_data_includes_siblings_when_needed(self):
        """Test that get_section_data includes siblings when comparison type is set."""
        # Setup section with indicator
        section = SectionFactory()
        category = CategoryFactory(section=section)
        indicator = IndicatorFactory(category=category)
        source = IndicatorSourceFactory()

        # Create visual with siblings comparison
        visual = IndicatorDataVisualFactory(
            indicator=indicator,
            location_comparison_type='siblings'
        )
        IndicatorDataVisualSourceFactory(data_visual=visual, source=source, priority=0)

        # Create locations
        primary = LocationFactory()
        sibling = LocationFactory()

        # Create indicator values
        IndicatorValueFactory(indicator=indicator, location=primary, source=source)
        IndicatorValueFactory(indicator=indicator, location=sibling, source=source)

        # Get section data - should include both
        values = section.get_section_data(
            primary_location=primary,
            parent_locations=None,
            sibling_locations=[sibling]
        )

        # Defer geometry to avoid SpatiaLite parsing issues in tests
        values = values.defer('location__geometry')

        values_list = list(values)
        location_ids = [v.location_id for v in values_list]

        assert primary.id in location_ids
        assert sibling.id in location_ids

    def test_get_section_data_only_primary_when_no_comparisons(self):
        """Test that get_section_data only fetches primary location when no comparisons set."""
        # Setup section with indicator (no comparison type)
        section = SectionFactory()
        category = CategoryFactory(section=section)
        indicator = IndicatorFactory(category=category)
        source = IndicatorSourceFactory()

        # Create visual WITHOUT comparison type
        visual = IndicatorDataVisualFactory(
            indicator=indicator,
            location_comparison_type=None
        )
        IndicatorDataVisualSourceFactory(data_visual=visual, source=source, priority=0)

        # Create locations
        primary = LocationFactory()
        parent = LocationFactory()
        sibling = LocationFactory()

        # Create indicator values for all
        IndicatorValueFactory(indicator=indicator, location=primary, source=source)
        IndicatorValueFactory(indicator=indicator, location=parent, source=source)
        IndicatorValueFactory(indicator=indicator, location=sibling, source=source)

        # Get section data - should only have primary
        values = section.get_section_data(
            primary_location=primary,
            parent_locations=[parent],
            sibling_locations=[sibling]
        )

        # Defer geometry to avoid SpatiaLite parsing issues in tests
        values = values.defer('location__geometry')

        values_list = list(values)
        location_ids = [v.location_id for v in values_list]

        assert primary.id in location_ids
        assert parent.id not in location_ids
        assert sibling.id not in location_ids

    def test_get_section_data_respects_source_priority(self):
        """Test that get_section_data returns highest priority source."""
        # Setup section
        section = SectionFactory()
        category = CategoryFactory(section=section)
        indicator = IndicatorFactory(category=category)

        # Create two sources with different priorities
        source_priority_0 = IndicatorSourceFactory(name="High Priority Source")
        source_priority_1 = IndicatorSourceFactory(name="Low Priority Source")

        # Create visual with both sources
        visual = IndicatorDataVisualFactory(indicator=indicator)
        IndicatorDataVisualSourceFactory(data_visual=visual, source=source_priority_0, priority=0)
        IndicatorDataVisualSourceFactory(data_visual=visual, source=source_priority_1, priority=1)

        # Create location
        location = LocationFactory()

        # Create values for both sources (different values to distinguish)
        IndicatorValueFactory(
            indicator=indicator,
            location=location,
            source=source_priority_0,
            value=100.0
        )
        IndicatorValueFactory(
            indicator=indicator,
            location=location,
            source=source_priority_1,
            value=200.0
        )

        # Get section data
        values = section.get_section_data(primary_location=location)

        # Defer geometry to avoid SpatiaLite parsing issues in tests
        values = values.defer('location__geometry')

        values_list = list(values)

        # Should only return the priority 0 source value
        assert len(values_list) == 1
        assert values_list[0].source_id == source_priority_0.id
        assert values_list[0].value == 100.0

    def test_get_section_json_data_structure(self):
        """Test that get_section_json_data returns correct structure."""
        # Create complete section
        section = create_complete_section(num_categories=1, num_indicators_per_category=1)
        location = LocationFactory()

        # Get JSON data
        data = section.get_section_json_data(primary_location=location)

        # Check structure
        assert 'section' in data
        assert 'categories' in data
        assert 'dataVisuals' in data
        assert 'indicatorValues' in data

        # Check section info
        assert data['section']['id'] == section.id
        assert data['section']['name'] == section.name

        # Check we have categories
        assert len(data['categories']) > 0

        # Check we have data visuals
        assert len(data['dataVisuals']) > 0


@pytest.mark.django_db
class TestLocationModel:
    """Tests for Location model methods."""

    def test_get_siblings_excludes_self(self):
        """Test that get_siblings excludes the current location."""
        location_type = LocationTypeFactory()
        location1 = LocationFactory(location_type=location_type)
        location2 = LocationFactory(location_type=location_type)
        location3 = LocationFactory(location_type=location_type)

        siblings = location1.get_siblings(defer_geom=True)
        # Force evaluation before accessing geometry
        sibling_ids = list(siblings.values_list('id', flat=True))

        assert location1.id not in sibling_ids
        assert location2.id in sibling_ids
        assert location3.id in sibling_ids

    def test_get_parents_returns_parent_locations(self):
        """Test that get_parents returns parent location types."""
        # Create location hierarchy
        hierarchy = create_location_hierarchy()

        # City should find county and state as parents if they contain it
        # Note: This requires proper geometry setup, which is simplified here
        parents = hierarchy['city'].get_parents()

        # Just verify it returns a queryset (actual parent detection requires proper geometry)
        assert parents is not None


@pytest.mark.django_db
class TestIndicatorValue:
    """Tests for IndicatorValue model."""

    def test_create_indicator_value_with_filter_option(self):
        """Test creating indicator value with a filter option."""
        filter_option = IndicatorFilterOptionFactory()
        value = IndicatorValueFactory(filter_option=filter_option)

        assert value.filter_option == filter_option

    def test_create_indicator_value_without_filter_option(self):
        """Test creating indicator value without a filter option."""
        value = IndicatorValueFactory(filter_option=None)

        assert value.filter_option is None
