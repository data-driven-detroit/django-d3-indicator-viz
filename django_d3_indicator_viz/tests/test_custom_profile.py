from unittest import TestCase
from unittest.mock import MagicMock, patch
from types import SimpleNamespace

from django_d3_indicator_viz.aggregation import (
    build_indicator_values_dict_list,
    aggregate_indicator_values,
    aggregate_indicator_value_set,
)
from django_d3_indicator_viz.indicator_value_aggregator import (
    IndicatorValueAggregator,
)


class SampleAggregator(IndicatorValueAggregator):
    def aggregate_index_values(self, index_values):
        raise NotImplementedError

    def aggregate_index_moe_values(self, index_values, index_moe_values):
        raise NotImplementedError


def _make_iv(**kwargs):
    """Create a SimpleNamespace that looks like an IndicatorValue row."""
    defaults = {
        "location_id": "loc1",
        "indicator_id": 1,
        "source_id": 1,
        "filter_option_id": None,
        "start_date": "2020-01-01",
        "end_date": "2020-12-31",
        "value": 50.0,
        "value_moe": 5.0,
        "count": 100,
        "count_moe": 10,
        "universe": 200,
        "universe_moe": 20,
        "active_data": True,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def _make_data_visual(indicator_id=1, indicator_type="count", rate_per=None):
    """Create a mock data visual with the needed attributes."""
    dv = MagicMock()
    dv.indicator.id = indicator_id
    dv.indicator.indicator_type = indicator_type
    dv.indicator.rate_per = rate_per
    dv.rate_per = rate_per
    return dv


class TestBuildIndicatorValuesDictList(TestCase):

    def test_converts_objects_to_dicts(self):
        ivs = [_make_iv(location_id="A"), _make_iv(location_id="B")]
        result = build_indicator_values_dict_list(ivs)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["location_id"], "A")
        self.assertEqual(result[1]["location_id"], "B")
        expected_keys = {
            "location_id", "indicator_id", "source_id", "filter_option_id",
            "start_date", "end_date", "value", "value_moe", "count",
            "count_moe", "universe", "universe_moe", "active_data",
        }
        self.assertEqual(set(result[0].keys()), expected_keys)


class TestAggregateIndicatorValues(TestCase):

    def setUp(self):
        self.aggregator = SampleAggregator()

    def test_groups_by_filter_option_and_start_date(self):
        ivs = [
            _make_iv(filter_option_id=1, start_date="2020-01-01", count=10, universe=100),
            _make_iv(filter_option_id=1, start_date="2020-01-01", count=20, universe=200),
            _make_iv(filter_option_id=2, start_date="2020-01-01", count=30, universe=300),
        ]
        custom_loc = MagicMock()
        custom_loc.id = "custom-1"
        dv = _make_data_visual(indicator_id=1, indicator_type="count")

        result = aggregate_indicator_values(custom_loc, dv, ivs, self.aggregator)
        # Two groups: (1, 2020-01-01) and (2, 2020-01-01)
        self.assertEqual(len(result), 2)

    def test_filters_by_indicator_id(self):
        ivs = [
            _make_iv(indicator_id=1, count=10, universe=100),
            _make_iv(indicator_id=999, count=20, universe=200),
        ]
        custom_loc = MagicMock()
        custom_loc.id = "custom-1"
        dv = _make_data_visual(indicator_id=1, indicator_type="count")

        result = aggregate_indicator_values(custom_loc, dv, ivs, self.aggregator)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["value"], 10)

    def test_empty_input_returns_empty(self):
        custom_loc = MagicMock()
        custom_loc.id = "custom-1"
        dv = _make_data_visual(indicator_id=1, indicator_type="count")

        result = aggregate_indicator_values(custom_loc, dv, [], self.aggregator)
        self.assertEqual(result, [])


class TestAggregateIndicatorValueSetCount(TestCase):

    def setUp(self):
        self.aggregator = SampleAggregator()

    def test_count_aggregation(self):
        ivs = [
            {"location_id": "A", "indicator_id": 1, "source_id": 1,
             "filter_option_id": None, "start_date": "2020-01-01",
             "end_date": "2020-12-31", "value": 10, "value_moe": 1,
             "count": 10, "count_moe": 1, "universe": 100, "universe_moe": 10,
             "active_data": True},
            {"location_id": "B", "indicator_id": 1, "source_id": 1,
             "filter_option_id": None, "start_date": "2020-01-01",
             "end_date": "2020-12-31", "value": 20, "value_moe": 2,
             "count": 20, "count_moe": 2, "universe": 200, "universe_moe": 20,
             "active_data": True},
        ]
        custom_loc = MagicMock()
        custom_loc.id = "custom-1"
        dv = _make_data_visual(indicator_id=1, indicator_type="count")

        result = aggregate_indicator_value_set(custom_loc, dv, ivs, self.aggregator)
        self.assertEqual(result["value"], 30)
        self.assertEqual(result["location_id"], "custom-1")


class TestAggregateIndicatorValueSetPercentage(TestCase):

    def setUp(self):
        self.aggregator = SampleAggregator()

    def test_percentage_aggregation(self):
        # Use values from ACS handbook where MOE math works out
        ivs = [
            {"location_id": "A", "indicator_id": 1, "source_id": 1,
             "filter_option_id": None, "start_date": "2020-01-01",
             "end_date": "2020-12-31", "value": 4.66, "value_moe": 7.2,
             "count": 11, "count_moe": 17, "universe": 236, "universe_moe": 88,
             "active_data": True},
            {"location_id": "B", "indicator_id": 1, "source_id": 1,
             "filter_option_id": None, "start_date": "2020-01-01",
             "end_date": "2020-12-31", "value": 22.77, "value_moe": 16.88,
             "count": 69, "count_moe": 64, "universe": 303, "universe_moe": 116,
             "active_data": True},
        ]
        custom_loc = MagicMock()
        custom_loc.id = "custom-1"
        dv = _make_data_visual(indicator_id=1, indicator_type="percentage")

        result = aggregate_indicator_value_set(custom_loc, dv, ivs, self.aggregator)
        # (11+69) / (236+303) * 100 = 14.84
        self.assertAlmostEqual(result["value"], 14.84, places=2)


class TestAggregateIndicatorValueSetRate(TestCase):

    def setUp(self):
        self.aggregator = SampleAggregator()

    def test_rate_aggregation(self):
        ivs = [
            {"location_id": "A", "indicator_id": 1, "source_id": 1,
             "filter_option_id": None, "start_date": "2020-01-01",
             "end_date": "2020-12-31", "value": 100, "value_moe": 10,
             "count": 10, "count_moe": 1, "universe": 1000, "universe_moe": 100,
             "active_data": True},
            {"location_id": "B", "indicator_id": 1, "source_id": 1,
             "filter_option_id": None, "start_date": "2020-01-01",
             "end_date": "2020-12-31", "value": 200, "value_moe": 20,
             "count": 40, "count_moe": 4, "universe": 2000, "universe_moe": 200,
             "active_data": True},
        ]
        custom_loc = MagicMock()
        custom_loc.id = "custom-1"
        dv = _make_data_visual(indicator_id=1, indicator_type="rate", rate_per=1000)

        result = aggregate_indicator_value_set(custom_loc, dv, ivs, self.aggregator)
        # (10+40) / (1000+2000) * 1000 = 16.67
        self.assertAlmostEqual(result["value"], 16.67, places=2)
