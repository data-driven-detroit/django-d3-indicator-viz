from unittest import TestCase
import unittest

from django_d3_indicator_viz.indicator_value_aggregator import * 

class SampleIndicatorValueAggregator(IndicatorValueAggregator):
    def aggregate_index_values(self, index_values):
        raise NotImplementedError

    def aggregate_index_moe_values(self, index_values, index_moe_values):
        raise NotImplementedError

class IndicatorValueAggregatorTests(TestCase):

    # create instance of the aggregator before running tests
    def setUp(self):
        self.aggregator = SampleIndicatorValueAggregator()

    def test_aggregate_count_values(self):
        count_values = [1157, 1739, 2924, 1620]
        result = self.aggregator.aggregate_count_values(count_values)
        self.assertEqual(result.value, 7440)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 4)

    def test_aggregate_count_values_with_none(self):
        count_values = [1157, None, 2924, 1620]
        result = self.aggregator.aggregate_count_values(count_values)
        result_without_nones = self.aggregator.aggregate_count_values([1157, 2924, 1620])
        self.assertEqual(result.value, result_without_nones.value)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 3)

    def test_aggregate_count_moe_values(self):
        moe_values = [193, 342, 516, 441]
        result = self.aggregator.aggregate_count_moe_values(moe_values)
        self.assertEqual(result.value, 784.19)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 4)

    def test_aggregate_count_moe_values_with_none(self):
        moe_values = [193, None, 516, 441]
        result = self.aggregator.aggregate_count_moe_values(moe_values)
        result_without_nones = self.aggregator.aggregate_count_moe_values([193, 516, 441])
        self.assertEqual(result.value, result_without_nones.value)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 3)

    def test_aggregate_percentage_values(self):
        count_values = [11, 69, 14, 0]
        universe_values = [236, 303, 784, 402]
        result = self.aggregator.aggregate_percentage_values(count_values, universe_values)
        self.assertEqual(result.value, 5.45)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 4)

    def test_aggregate_percentage_values_with_none(self):
        count_values = [11, None, 14, 0]
        universe_values = [236, 303, None, 402]
        result = self.aggregator.aggregate_percentage_values(count_values, universe_values)
        result_without_nones = self.aggregator.aggregate_percentage_values(
            [11, 0],
            [236, 402]
        )
        self.assertEqual(result.value, result_without_nones.value)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 2)

    def test_aggregate_percentage_moe_values(self):
        count_values = [11, 69, 14, 0]
        universe_values = [236, 303, 784, 402]
        count_moe_values = [17, 64, 23, 11]
        universe_moe_values = [88, 116, 186, 187]
        result = self.aggregator.aggregate_percentage_moe_values(count_values, universe_values, count_moe_values, universe_moe_values)
        self.assertEqual(result.value, 4.0)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 4)

    def test_aggregate_percentage_moe_values_with_none(self):
        count_values = [11, None, 14, 0]
        universe_values = [236, 303, None, 402]
        count_moe_values = [17, None, 23, 11]
        universe_moe_values = [88, 116, None, 187]
        result = self.aggregator.aggregate_percentage_moe_values(count_values, universe_values, count_moe_values, universe_moe_values)
        result_without_nones = self.aggregator.aggregate_percentage_moe_values(
            [11, 0],
            [236, 402],
            [17, 11],
            [88, 187]
        )
        self.assertEqual(result.value, result_without_nones.value)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 2)

    def test_aggregate_median_values(self):
        median_values = [30216, 18342, 60239, 22963]
        universe_values = [553, 1049, 1289, 792]
        result = self.aggregator.aggregate_median_values(median_values, universe_values)
        self.assertEqual(result.value, 35781.96)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 4)

    def test_aggregate_median_values_with_none(self):
        median_values = [30216, None, 60239, 22963]
        universe_values = [553, 1049, 1289, 792]
        result = self.aggregator.aggregate_median_values(median_values, universe_values)
        result_without_nones = self.aggregator.aggregate_median_values([30216, 60239, 22963], [553, 1289, 792])
        self.assertEqual(result.value, result_without_nones.value)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 3)

    def test_aggregate_median_moe_values(self):
        median_values = [30216, 18342, 60239, 22963]
        universe_values = [553, 1049, 1289, 792]
        median_moe_values = [10610, 5167, 23060, 8839]
        universe_moe_values = [91, 216, 162, 180]
        result = self.aggregator.aggregate_median_moe_values(median_values, universe_values, median_moe_values, universe_moe_values)
        self.assertEqual(result.value, 9704.03)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 4)

    def test_aggregate_median_moe_values_with_none(self):
        median_values = [30216, None, 60239, 22963]
        universe_values = [553, 1049, 1289, 792]
        median_moe_values = [10610, None, 23060, 8839]
        universe_moe_values = [91, 216, 162, 180]
        result = self.aggregator.aggregate_median_moe_values(median_values, universe_values, median_moe_values, universe_moe_values)
        result_without_nones = self.aggregator.aggregate_median_moe_values(
            [30216, 60239, 22963],
            [553, 1289, 792],
            [10610, 23060, 8839],
            [91, 162, 180]
        )
        self.assertEqual(result.value, result_without_nones.value)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 3)

    def test_aggregate_average_values(self):
        average_values = [30216, 18342, 60239, 22963]
        universe_values = [553, 1049, 1289, 792]
        result = self.aggregator.aggregate_average_values(average_values, universe_values)
        self.assertEqual(result.value, 35781.96)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 4)

    def test_aggregate_average_values_with_none(self):
        average_values = [30216, None, 60239, 22963]
        universe_values = [553, 1049, 1289, None]
        result = self.aggregator.aggregate_average_values(average_values, universe_values)
        result_without_nones = self.aggregator.aggregate_average_values([30216, 60239], [553, 1289])
        self.assertEqual(result.value, result_without_nones.value)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 2)

    def test_aggregate_average_moe_values(self):
        average_values = [30216, 18342, 60239, 22963]
        universe_values = [553, 1049, 1289, 792]
        average_moe_values = [10610, 5167, 23060, 8839]
        universe_moe_values = [91, 216, 162, 180]
        self.assertEqual(self.aggregator.aggregate_average_moe_values(average_values, universe_values, average_moe_values, universe_moe_values).value, 9704.03)

    def test_aggregate_average_moe_values_with_none(self):
        average_values = [30216, None, 60239, 22963]
        universe_values = [553, 1049, 1289, None]
        average_moe_values = [10610, None, 23060, 8839]
        universe_moe_values = [91, 216, 162, None]
        result = self.aggregator.aggregate_average_moe_values(average_values, universe_values, average_moe_values, universe_moe_values)
        result_without_nones = self.aggregator.aggregate_average_moe_values(
            [30216, 60239],
            [553, 1289],
            [10610, 23060],
            [91, 162]
        )
        self.assertEqual(result.value, result_without_nones.value)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 2)

    def test_aggregate_rate_values(self):
        count_values = [1157, 1739, 2924, 1620]
        universe_values = [7440, 10320, 17400, 9660]
        rate_per = 1000
        result = self.aggregator.aggregate_rate_values(count_values, universe_values, rate_per)
        self.assertEqual(result.value, 166.00)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 4)

    def test_aggregate_rate_values_with_none(self):
        count_values = [1157, None, 2924, 1620]
        universe_values = [7440, None, 17400, 9660]
        rate_per = 1000
        result = self.aggregator.aggregate_rate_values(count_values, universe_values, rate_per)
        result_without_nones = self.aggregator.aggregate_rate_values([1157, 2924, 1620], [7440, 17400, 9660], rate_per)
        self.assertEqual(result.value, result_without_nones.value)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 3)

    def test_aggregate_rate_moe_values(self):
        count_values = [1157, 1739, 2924, 1620]
        universe_values = [7440, 10320, 17400, 9660]
        count_moe_values = [193, 342, 516, 441]
        universe_moe_values = [784, 1020, 1740, 966]
        rate_per = 1000
        result = self.aggregator.aggregate_rate_moe_values(count_values, universe_values, count_moe_values, universe_moe_values, rate_per)
        self.assertEqual(result.value, 8.78)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 4)

    def test_aggregate_rate_moe_values_with_none(self):
        count_values = [1157, None, 2924, 1620]
        universe_values = [7440, 10320, 17400, 9660]
        count_moe_values = [193, None, 516, 441]
        universe_moe_values = [784, 1020, 1740, 966]
        rate_per = 1000
        result = self.aggregator.aggregate_rate_moe_values(count_values, universe_values, count_moe_values, universe_moe_values, rate_per)
        result_without_nones = self.aggregator.aggregate_rate_moe_values(
            [1157, 2924, 1620],
            [7440, 17400, 9660],
            [193, 516, 441],
            [784, 1740, 966],
            rate_per
        )
        self.assertEqual(result.value, result_without_nones.value)
        self.assertEqual(result.values_considered, 4)
        self.assertEqual(result.values_aggregated, 3)

    if __name__ == '__main__':
        unittest.main()