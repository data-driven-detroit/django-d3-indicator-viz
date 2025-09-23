from unittest import TestCase
import unittest

from django_d3_indicator_viz.indicator_value_aggregator import * 

class IndicatorValueAggregatorTests(TestCase):
    def test_aggregate_count_values(self):
        count_values = [1157, 1739, 2924, 1620]
        self.assertEqual(aggregate_count_values(count_values), 7440)

    def test_aggregate_count_moe_values(self):
        moe_values = [193, 342, 516, 441]
        self.assertEqual(aggregate_count_moe_values(moe_values), 784.19)

    def test_aggregate_percentage_values(self):
        count_values = [11, 69, 14, 0]
        universe_values = [236, 303, 784, 402]
        self.assertEqual(aggregate_percentage_values(count_values, universe_values), 5.45)

    def test_aggregate_percentage_moe_values(self):
        count_values = [11, 69, 14, 0]
        universe_values = [236, 303, 784, 402]
        count_moe_values = [17, 64, 23, 11]
        universe_moe_values = [88, 116, 186, 187]
        self.assertEqual(aggregate_percentage_moe_values(count_values, universe_values, count_moe_values, universe_moe_values), 4.0)

    def test_aggregate_median_values(self):
        median_values = [30216, 18342, 60239, 22963]
        universe_values = [553, 1049, 1289, 792]
        self.assertEqual(aggregate_median_values(median_values, universe_values), 35781.96)

    def test_aggregate_median_moe_values(self):
        median_values = [30216, 18342, 60239, 22963]
        universe_values = [553, 1049, 1289, 792]
        median_moe_values = [10610, 5167, 23060, 8839]
        universe_moe_values = [91, 216, 162, 180]
        self.assertEqual(aggregate_median_moe_values(median_values, universe_values, median_moe_values, universe_moe_values), 9704.03)

    def test_aggregate_average_values(self):
        #TODO: should be tested with real data once available, currently using same as median
        average_values = [30216, 18342, 60239, 22963]
        universe_values = [553, 1049, 1289, 792]
        self.assertEqual(aggregate_average_values(average_values, universe_values), 35781.96)

    def test_aggregate_average_moe_values(self):
        #TODO: should be tested with real data once available, currently using same as median
        average_values = [30216, 18342, 60239, 22963]
        universe_values = [553, 1049, 1289, 792]
        average_moe_values = [10610, 5167, 23060, 8839]
        universe_moe_values = [91, 216, 162, 180]
        self.assertEqual(aggregate_average_moe_values(average_values, universe_values, average_moe_values, universe_moe_values), 9704.03)

    def test_aggregate_rate_values(self):
        count_values = [1157, 1739, 2924, 1620]
        universe_values = [7440, 10320, 17400, 9660]
        rate_per = 1000
        self.assertEqual(aggregate_rate_values(count_values, universe_values, rate_per), 166.00)

    def test_aggregate_rate_moe_values(self):
        count_values = [1157, 1739, 2924, 1620]
        universe_values = [7440, 10320, 17400, 9660]
        count_moe_values = [193, 342, 516, 441]
        universe_moe_values = [784, 1020, 1740, 966]
        rate_per = 1000
        self.assertEqual(aggregate_rate_moe_values(count_values, universe_values, count_moe_values, universe_moe_values, rate_per), 8.78)

    if __name__ == '__main__':
        unittest.main()