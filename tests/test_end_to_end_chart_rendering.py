"""
End-to-end tests that call roll_section (which drives both get_visual_metadata
and get_indicator_values) and then simulate the JS filter logic in Python.

If any test here fails, the browser will show "No data available" for that chart.
"""
import pytest
import json
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
from django_d3_indicator_viz.views import roll_section
from django_d3_indicator_viz.indicator_value_aggregator import IndicatorValueAggregator


def simulate_js_filter(section_data):
    """
    Simulate chart-connector.js filter logic against roll_section output.

    For each indicator that has visual_metadata, check whether the source_id
    embedded in the HTML (from get_visual_metadata) matches any values in the
    JSON blob (from get_indicator_values).

    Returns list of dicts with keys:
        name, matched (bool), html_source_id, json_source_ids (set)
    """
    all_values = json.loads(section_data["indicator_values"])
    results = []
    for category in section_data["categories"]:
        for indicator in category["indicators"]:
            meta = indicator["visual_metadata"]
            ind_id = indicator["id"]
            src_id = meta.source_id
            matched = [
                v for v in all_values
                if v["indicator_id"] == ind_id and v["source_id"] == src_id
            ]
            json_src_ids = set(
                v["source_id"] for v in all_values
                if v["indicator_id"] == ind_id
            )
            results.append({
                "name": indicator["name"],
                "matched": len(matched) > 0,
                "html_source_id": src_id,
                "json_source_ids": json_src_ids,
            })
    return results


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_setup():
    """Common setup: loc_type, two constituent locations, custom location, section."""
    loc_type = LocationTypeFactory(name="Tract-e2e")
    loc_a = LocationFactory(id="e2e-001", location_type=loc_type, geometry=None)
    loc_b = LocationFactory(id="e2e-002", location_type=loc_type, geometry=None)
    custom_loc = CustomLocationFactory(
        slug="e2e-area",
        location_type=loc_type,
        locations=[loc_a, loc_b],
        geometry=None,
    )
    section = SectionFactory()
    category = CategoryFactory(section=section)
    return {
        "loc_type": loc_type,
        "loc_a": loc_a,
        "loc_b": loc_b,
        "custom_location": custom_loc,
        "section": section,
        "category": category,
    }


def _make_indicator(category, source_primary, source_fallback=None, visual_type="ban"):
    """Helper to create an indicator with data visual and source(s)."""
    indicator = IndicatorFactory(category=category, indicator_type="count")
    dv = IndicatorDataVisualFactory(
        indicator=indicator,
        data_visual_type=visual_type,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 12, 31),
    )
    IndicatorDataVisualSourceFactory(data_visual=dv, source=source_primary, priority=0)
    if source_fallback:
        IndicatorDataVisualSourceFactory(data_visual=dv, source=source_fallback, priority=1)
    return indicator, dv


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@pytest.mark.django_db
class TestEndToEndChartRendering:

    def test_single_source_all_constituents(self, base_setup):
        """Both constituents have data from the same source. Should always match."""
        s = base_setup
        source = IndicatorSourceFactory(name="Only Source")
        indicator, _ = _make_indicator(s["category"], source)

        for loc in [s["loc_a"], s["loc_b"]]:
            IndicatorValueFactory(
                indicator=indicator, location=loc, source=source,
                count=100, count_moe=10, universe=1000, universe_moe=100,
                start_date=date(2020, 1, 1), end_date=date(2020, 12, 31),
            )

        section_data = roll_section(
            s["section"], s["custom_location"], [],
            custom_location=s["custom_location"],
            aggregator=IndicatorValueAggregator(),
        )
        results = simulate_js_filter(section_data)

        assert len(results) == 1
        assert results[0]["matched"], (
            f"Source mismatch: html_source_id={results[0]['html_source_id']}, "
            f"json_source_ids={results[0]['json_source_ids']}"
        )

    def test_fallback_source_only(self, base_setup):
        """Primary source has no data, fallback does. Both functions should pick the fallback."""
        s = base_setup
        source_primary = IndicatorSourceFactory(name="Primary-e2e")
        source_fallback = IndicatorSourceFactory(name="Fallback-e2e")
        indicator, _ = _make_indicator(s["category"], source_primary, source_fallback)

        # Only create data for the FALLBACK source
        for loc in [s["loc_a"], s["loc_b"]]:
            IndicatorValueFactory(
                indicator=indicator, location=loc, source=source_fallback,
                count=50, count_moe=5, universe=500, universe_moe=50,
                start_date=date(2020, 1, 1), end_date=date(2020, 12, 31),
            )

        section_data = roll_section(
            s["section"], s["custom_location"], [],
            custom_location=s["custom_location"],
            aggregator=IndicatorValueAggregator(),
        )
        results = simulate_js_filter(section_data)

        assert len(results) == 1
        assert results[0]["matched"], (
            f"Source mismatch: html_source_id={results[0]['html_source_id']}, "
            f"json_source_ids={results[0]['json_source_ids']}"
        )
        assert results[0]["html_source_id"] == source_fallback.id

    def test_mixed_sources_across_constituents(self, base_setup):
        """
        Location A has data from source P (priority 0),
        Location B only has data from source F (priority 1).

        This is the likely failure case: get_visual_metadata might pick source F
        (from location B via .first()), while get_indicator_values picks source P.
        Both should agree on source P since it has data for at least one constituent.
        """
        s = base_setup
        source_p = IndicatorSourceFactory(name="SourceP-e2e")
        source_f = IndicatorSourceFactory(name="SourceF-e2e")
        indicator, _ = _make_indicator(s["category"], source_p, source_f)

        # Location A has data from PRIMARY source only
        IndicatorValueFactory(
            indicator=indicator, location=s["loc_a"], source=source_p,
            count=100, count_moe=10, universe=1000, universe_moe=100,
            start_date=date(2020, 1, 1), end_date=date(2020, 12, 31),
        )
        # Location B has data from FALLBACK source only
        IndicatorValueFactory(
            indicator=indicator, location=s["loc_b"], source=source_f,
            count=200, count_moe=20, universe=2000, universe_moe=200,
            start_date=date(2020, 1, 1), end_date=date(2020, 12, 31),
        )

        section_data = roll_section(
            s["section"], s["custom_location"], [],
            custom_location=s["custom_location"],
            aggregator=IndicatorValueAggregator(),
        )
        results = simulate_js_filter(section_data)

        assert len(results) == 1
        assert results[0]["matched"], (
            f"Source mismatch: html_source_id={results[0]['html_source_id']}, "
            f"json_source_ids={results[0]['json_source_ids']}"
        )

    def test_with_comparison_locations(self, base_setup):
        """Custom location + parent locations. Verify comparison values also match."""
        s = base_setup
        source = IndicatorSourceFactory(name="Comp-Source-e2e")
        indicator, _ = _make_indicator(s["category"], source)

        # Parent location type and location
        parent_type = LocationTypeFactory(name="County-e2e")
        parent_loc = LocationFactory(id="e2e-county", location_type=parent_type, geometry=None)

        # Data for constituents
        for loc in [s["loc_a"], s["loc_b"]]:
            IndicatorValueFactory(
                indicator=indicator, location=loc, source=source,
                count=100, count_moe=10, universe=1000, universe_moe=100,
                start_date=date(2020, 1, 1), end_date=date(2020, 12, 31),
            )
        # Data for parent
        IndicatorValueFactory(
            indicator=indicator, location=parent_loc, source=source,
            count=500, count_moe=50, universe=5000, universe_moe=500,
            start_date=date(2020, 1, 1), end_date=date(2020, 12, 31),
        )

        section_data = roll_section(
            s["section"], s["custom_location"], [parent_loc],
            custom_location=s["custom_location"],
            aggregator=IndicatorValueAggregator(),
        )
        results = simulate_js_filter(section_data)

        assert len(results) == 1
        assert results[0]["matched"], (
            f"Source mismatch: html_source_id={results[0]['html_source_id']}, "
            f"json_source_ids={results[0]['json_source_ids']}"
        )

        # Also verify that comparison location values are present in the JSON
        all_values = json.loads(section_data["indicator_values"])
        parent_values = [v for v in all_values if v["location_id"] == parent_loc.id]
        assert len(parent_values) >= 1, "Parent comparison location values missing from JSON"

    def test_mismatched_dv_and_iv_dates(self, base_setup):
        """
        DV has an old date range but actual data is newer.
        Should still aggregate the newer data (not return "No data").
        Regression test: a date range filter on DV dates would exclude this data.
        """
        s = base_setup
        source = IndicatorSourceFactory(name="Stale-DV-Source")
        indicator = IndicatorFactory(category=s["category"], indicator_type="count")
        # DV configured with old date range
        dv = IndicatorDataVisualFactory(
            indicator=indicator,
            data_visual_type="ban",
            start_date=date(2018, 1, 1),
            end_date=date(2020, 12, 31),
        )
        IndicatorDataVisualSourceFactory(data_visual=dv, source=source, priority=0)

        # Actual data is from 2022 — outside the DV's configured range
        for loc in [s["loc_a"], s["loc_b"]]:
            IndicatorValueFactory(
                indicator=indicator, location=loc, source=source,
                count=100, count_moe=10, universe=1000, universe_moe=100,
                start_date=date(2022, 1, 1), end_date=date(2022, 12, 31),
            )

        section_data = roll_section(
            s["section"], s["custom_location"], [],
            custom_location=s["custom_location"],
            aggregator=IndicatorValueAggregator(),
        )
        results = simulate_js_filter(section_data)

        assert len(results) == 1
        assert results[0]["matched"], (
            f"Source mismatch: html_source_id={results[0]['html_source_id']}, "
            f"json_source_ids={results[0]['json_source_ids']}"
        )

        # Verify aggregated value is not null (data was actually found)
        all_values = json.loads(section_data["indicator_values"])
        custom_values = [
            v for v in all_values
            if v["indicator_id"] == indicator.id and v["source_id"] == source.id
            and str(v["location_id"]) == str(s["custom_location"].id)
        ]
        assert len(custom_values) == 1
        assert custom_values[0]["value"] is not None, (
            "Aggregated value should not be null — data exists but dates are "
            "outside the DV's configured range"
        )
