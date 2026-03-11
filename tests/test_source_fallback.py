"""
Tests for source priority fallback in custom profile aggregation.

Ensures that get_indicator_values and get_visual_metadata agree on source_id
when the primary source has no data but a fallback source does.
"""
import pytest
from datetime import date
from tests.factories import (
    SectionFactory,
    CategoryFactory,
    CustomLocationFactory,
    IndicatorFactory,
    IndicatorDataVisualFactory,
    IndicatorDataVisualSourceFactory,
    IndicatorSourceFactory,
    IndicatorValueFactory,
    LocationFactory,
    LocationTypeFactory,
)
from django_d3_indicator_viz.indicator_value_aggregator import (
    IndicatorValueAggregator,
)


@pytest.fixture
def section_with_two_sources():
    """
    Create a section with one indicator that has two sources configured
    (priority 0 and priority 1), plus a custom location with two
    constituent locations.

    Locations are created without geometry to avoid SpatiaLite HEX parsing
    issues in the test environment.
    """
    loc_type = LocationTypeFactory(name="Tract")
    loc_a = LocationFactory(id="tract-001", location_type=loc_type, geometry=None)
    loc_b = LocationFactory(id="tract-002", location_type=loc_type, geometry=None)
    custom_loc = CustomLocationFactory(
        slug="test-area",
        location_type=loc_type,
        locations=[loc_a, loc_b],
        geometry=None,
    )

    section = SectionFactory()
    category = CategoryFactory(section=section)
    indicator = IndicatorFactory(
        category=category,
        indicator_type="count",
    )

    source_primary = IndicatorSourceFactory(name="Primary Source")
    source_fallback = IndicatorSourceFactory(name="Fallback Source")

    dv = IndicatorDataVisualFactory(
        indicator=indicator,
        data_visual_type="ban",
        start_date=date(2020, 1, 1),
        end_date=date(2020, 12, 31),
    )
    IndicatorDataVisualSourceFactory(
        data_visual=dv, source=source_primary, priority=0
    )
    IndicatorDataVisualSourceFactory(
        data_visual=dv, source=source_fallback, priority=1
    )

    return {
        "section": section,
        "indicator": indicator,
        "source_primary": source_primary,
        "source_fallback": source_fallback,
        "data_visual": dv,
        "custom_location": custom_loc,
        "loc_a": loc_a,
        "loc_b": loc_b,
    }


@pytest.mark.django_db
class TestSourceFallbackInGetIndicatorValues:
    """Tests that get_indicator_values picks the correct source by priority."""

    def test_uses_primary_source_when_data_exists(self, section_with_two_sources):
        """When the primary source has data, use it."""
        s = section_with_two_sources
        # Create data for the PRIMARY source
        IndicatorValueFactory(
            indicator=s["indicator"], location=s["loc_a"],
            source=s["source_primary"],
            count=100, count_moe=10, universe=1000, universe_moe=100,
            start_date=date(2020, 1, 1), end_date=date(2020, 12, 31),
        )
        IndicatorValueFactory(
            indicator=s["indicator"], location=s["loc_b"],
            source=s["source_primary"],
            count=200, count_moe=20, universe=2000, universe_moe=200,
            start_date=date(2020, 1, 1), end_date=date(2020, 12, 31),
        )

        values = s["section"].get_indicator_values(
            locations=[],
            custom_location=s["custom_location"],
            aggregator=IndicatorValueAggregator(),
        )

        assert len(values) == 1
        assert values[0]["source_id"] == s["source_primary"].id
        assert values[0]["value"] == 300  # count aggregation: 100 + 200

    def test_falls_back_when_primary_has_no_data(self, section_with_two_sources):
        """When primary source has no data, fall back to the next priority source."""
        s = section_with_two_sources
        # Create data ONLY for the FALLBACK source (not primary)
        IndicatorValueFactory(
            indicator=s["indicator"], location=s["loc_a"],
            source=s["source_fallback"],
            count=50, count_moe=5, universe=500, universe_moe=50,
            start_date=date(2020, 1, 1), end_date=date(2020, 12, 31),
        )
        IndicatorValueFactory(
            indicator=s["indicator"], location=s["loc_b"],
            source=s["source_fallback"],
            count=60, count_moe=6, universe=600, universe_moe=60,
            start_date=date(2020, 1, 1), end_date=date(2020, 12, 31),
        )

        values = s["section"].get_indicator_values(
            locations=[],
            custom_location=s["custom_location"],
            aggregator=IndicatorValueAggregator(),
        )

        assert len(values) == 1
        assert values[0]["source_id"] == s["source_fallback"].id
        assert values[0]["value"] == 110  # 50 + 60

    def test_skips_when_no_source_has_data(self, section_with_two_sources):
        """When no source has data for the constituent locations, skip entirely."""
        s = section_with_two_sources
        # Don't create any IndicatorValue data at all

        values = s["section"].get_indicator_values(
            locations=[],
            custom_location=s["custom_location"],
            aggregator=IndicatorValueAggregator(),
        )

        assert values == []

    def test_skips_data_visual_with_no_sources_configured(self):
        """When a data visual has no IndicatorDataVisualSource entries, skip it."""
        loc_type = LocationTypeFactory(name="Tract-NoSrc")
        loc = LocationFactory(location_type=loc_type, geometry=None)
        custom_loc = CustomLocationFactory(
            slug="no-source-area",
            location_type=loc_type,
            locations=[loc],
            geometry=None,
        )

        section = SectionFactory()
        category = CategoryFactory(section=section)
        indicator = IndicatorFactory(category=category, indicator_type="count")

        # Create data visual WITHOUT any source configuration
        IndicatorDataVisualFactory(
            indicator=indicator,
            data_visual_type="ban",
            start_date=date(2020, 1, 1),
            end_date=date(2020, 12, 31),
        )

        # Create data that would match if sources were configured
        source = IndicatorSourceFactory(name="Orphan Source")
        IndicatorValueFactory(
            indicator=indicator, location=loc, source=source,
            count=100, count_moe=10, universe=1000, universe_moe=100,
            start_date=date(2020, 1, 1), end_date=date(2020, 12, 31),
        )

        values = section.get_indicator_values(
            locations=[],
            custom_location=custom_loc,
            aggregator=IndicatorValueAggregator(),
        )

        assert values == []


@pytest.mark.django_db
class TestSourceAgreement:
    """
    Tests that get_visual_metadata and get_indicator_values produce the same
    source_id, which is required for charts to render.
    """

    def test_source_ids_match_with_primary_data(self, section_with_two_sources):
        """Both methods agree on source_id when primary has data."""
        s = section_with_two_sources
        IndicatorValueFactory(
            indicator=s["indicator"], location=s["loc_a"],
            source=s["source_primary"],
            count=100, count_moe=10, universe=1000, universe_moe=100,
            start_date=date(2020, 1, 1), end_date=date(2020, 12, 31),
        )

        # (A) get_visual_metadata
        meta = s["indicator"].get_visual_metadata(s["custom_location"])
        assert meta is not None
        template_source_id = meta.source_id

        # (B) get_indicator_values
        values = s["section"].get_indicator_values(
            locations=[],
            custom_location=s["custom_location"],
            aggregator=IndicatorValueAggregator(),
        )
        assert len(values) >= 1
        json_source_id = values[0]["source_id"]

        assert template_source_id == json_source_id

    def test_source_ids_match_with_fallback_data(self, section_with_two_sources):
        """
        Both methods agree on source_id when primary has NO data
        and the fallback source does.
        """
        s = section_with_two_sources
        # Only create data for FALLBACK source
        IndicatorValueFactory(
            indicator=s["indicator"], location=s["loc_a"],
            source=s["source_fallback"],
            count=50, count_moe=5, universe=500, universe_moe=50,
            start_date=date(2020, 1, 1), end_date=date(2020, 12, 31),
        )

        # (A) get_visual_metadata
        meta = s["indicator"].get_visual_metadata(s["custom_location"])
        assert meta is not None
        template_source_id = meta.source_id

        # (B) get_indicator_values
        values = s["section"].get_indicator_values(
            locations=[],
            custom_location=s["custom_location"],
            aggregator=IndicatorValueAggregator(),
        )
        assert len(values) >= 1
        json_source_id = values[0]["source_id"]

        assert template_source_id == json_source_id
        assert template_source_id == s["source_fallback"].id
