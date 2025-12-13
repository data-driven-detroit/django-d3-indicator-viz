from django.test import TestCase
from django_d3_indicator_viz.models import (
    Category,
    Indicator,
    IndicatorDataVisual,
    IndicatorValue,
    Location,
    LocationType,
    IndicatorSource,
)


class CategoryAxisScaleTests(TestCase):
    """Tests for Category.get_axis_scale() method - shared axis functionality"""

    def test_returns_none_when_sharing_disabled(self):
        """Test that get_axis_scale returns None when share_axes=False"""
        # Setup
        loc_type = LocationType.objects.create(name='City')
        location = Location.objects.create(id='1', name='Test City', location_type=loc_type)

        category = Category.objects.create(name='Test Category', share_axes=False)
        indicator = Indicator.objects.create(name='Population', category=category, indicator_type='count')
        IndicatorDataVisual.objects.create(
            indicator=indicator,
            data_visual_type='column',
            start_date='2023-01-01',
            end_date='2023-12-31',
            columns=1
        )
        source = IndicatorSource.objects.create(name='Test Source')
        IndicatorValue.objects.create(
            indicator=indicator,
            location=location,
            source=source,
            value=100,
            start_date='2023-01-01',
            end_date='2023-12-31'
        )

        # Test
        scale = category.get_axis_scale(location.id)

        # Assert
        self.assertIsNone(scale, "Scale should be None when share_axes=False")

    def test_returns_none_when_all_values_are_null(self):
        """Test that get_axis_scale returns None when all indicator values are NULL"""
        # Setup
        loc_type = LocationType.objects.create(name='City')
        location = Location.objects.create(id='1', name='Test City', location_type=loc_type)

        category = Category.objects.create(name='Test Category', share_axes=True)
        indicator = Indicator.objects.create(name='Population', category=category, indicator_type='count')
        IndicatorDataVisual.objects.create(
            indicator=indicator,
            data_visual_type='column',
            start_date='2023-01-01',
            end_date='2023-12-31',
            columns=1
        )
        source = IndicatorSource.objects.create(name='Test Source')
        IndicatorValue.objects.create(
            indicator=indicator,
            location=location,
            source=source,
            value=None,  # NULL value
            start_date='2023-01-01',
            end_date='2023-12-31'
        )

        # Test
        scale = category.get_axis_scale(location.id)

        # Assert
        self.assertIsNone(scale, "Scale should be None when all values are NULL")

    def test_calculates_scale_for_multiple_indicators(self):
        """Test that scale encompasses all indicators' data ranges"""
        # Setup
        loc_type = LocationType.objects.create(name='City')
        location = Location.objects.create(id='1', name='Test City', location_type=loc_type)

        category = Category.objects.create(name='Test Category', share_axes=True)
        source = IndicatorSource.objects.create(name='Test Source')

        # Indicator 1: values 10-20
        indicator1 = Indicator.objects.create(name='Pop A', category=category, indicator_type='count')
        visual1 = IndicatorDataVisual.objects.create(
            indicator=indicator1,
            data_visual_type='column',
            start_date='2023-01-01',
            end_date='2023-12-31',
            columns=1
        )
        IndicatorValue.objects.create(
            indicator=indicator1, location=location, source=source,
            value=10, start_date='2023-01-01', end_date='2023-12-31'
        )
        IndicatorValue.objects.create(
            indicator=indicator1, location=location, source=source,
            value=20, start_date='2023-01-01', end_date='2023-12-31'
        )

        # Indicator 2: values 50-60
        indicator2 = Indicator.objects.create(name='Pop B', category=category, indicator_type='count')
        visual2 = IndicatorDataVisual.objects.create(
            indicator=indicator2,
            data_visual_type='line',
            start_date='2023-01-01',
            end_date='2023-12-31',
            columns=1
        )
        IndicatorValue.objects.create(
            indicator=indicator2, location=location, source=source,
            value=50, start_date='2023-01-01', end_date='2023-12-31'
        )
        IndicatorValue.objects.create(
            indicator=indicator2, location=location, source=source,
            value=60, start_date='2023-01-01', end_date='2023-12-31'
        )

        # Test
        scale = category.get_axis_scale(location.id)

        # Assert - scale should span 10-60 with 10% padding
        # Range = 60 - 10 = 50
        # Padding = 50 * 0.1 = 5
        # Expected: min = 10 - 5 = 5, max = 60 + 5 = 65
        self.assertIsNotNone(scale)
        self.assertAlmostEqual(scale['min'], 5, places=1)
        self.assertAlmostEqual(scale['max'], 65, places=1)

    def test_applies_10_percent_padding(self):
        """Test that exactly 10% padding is applied to min and max"""
        # Setup
        loc_type = LocationType.objects.create(name='City')
        location = Location.objects.create(id='1', name='Test City', location_type=loc_type)

        category = Category.objects.create(name='Test Category', share_axes=True)
        indicator = Indicator.objects.create(name='Population', category=category, indicator_type='count')
        IndicatorDataVisual.objects.create(
            indicator=indicator,
            data_visual_type='column',
            start_date='2023-01-01',
            end_date='2023-12-31',
            columns=1
        )
        source = IndicatorSource.objects.create(name='Test Source')
        # Values: 10 and 20
        IndicatorValue.objects.create(
            indicator=indicator, location=location, source=source,
            value=10, start_date='2023-01-01', end_date='2023-12-31'
        )
        IndicatorValue.objects.create(
            indicator=indicator, location=location, source=source,
            value=20, start_date='2023-01-01', end_date='2023-12-31'
        )

        # Test
        scale = category.get_axis_scale(location.id)

        # Assert
        # Range = 20 - 10 = 10
        # Padding = 10 * 0.1 = 1
        # Expected: min = 10 - 1 = 9, max = 20 + 1 = 21
        self.assertIsNotNone(scale)
        self.assertEqual(scale['min'], 9)
        self.assertEqual(scale['max'], 21)

    def test_handles_single_value_zero(self):
        """Test special case: all values = 0 should return {min: -1, max: 1}"""
        # Setup
        loc_type = LocationType.objects.create(name='City')
        location = Location.objects.create(id='1', name='Test City', location_type=loc_type)

        category = Category.objects.create(name='Test Category', share_axes=True)
        indicator = Indicator.objects.create(name='Population', category=category, indicator_type='count')
        IndicatorDataVisual.objects.create(
            indicator=indicator,
            data_visual_type='column',
            start_date='2023-01-01',
            end_date='2023-12-31',
            columns=1
        )
        source = IndicatorSource.objects.create(name='Test Source')
        # All values are zero
        IndicatorValue.objects.create(
            indicator=indicator, location=location, source=source,
            value=0, start_date='2023-01-01', end_date='2023-12-31'
        )

        # Test
        scale = category.get_axis_scale(location.id)

        # Assert - special case for zero
        self.assertIsNotNone(scale)
        self.assertEqual(scale['min'], -1)
        self.assertEqual(scale['max'], 1)

    def test_handles_single_value_non_zero(self):
        """Test single value case: value = 5 should return {min: 4.5, max: 5.5}"""
        # Setup
        loc_type = LocationType.objects.create(name='City')
        location = Location.objects.create(id='1', name='Test City', location_type=loc_type)

        category = Category.objects.create(name='Test Category', share_axes=True)
        indicator = Indicator.objects.create(name='Population', category=category, indicator_type='count')
        IndicatorDataVisual.objects.create(
            indicator=indicator,
            data_visual_type='column',
            start_date='2023-01-01',
            end_date='2023-12-31',
            columns=1
        )
        source = IndicatorSource.objects.create(name='Test Source')
        # Single value = 5
        IndicatorValue.objects.create(
            indicator=indicator, location=location, source=source,
            value=5, start_date='2023-01-01', end_date='2023-12-31'
        )

        # Test
        scale = category.get_axis_scale(location.id)

        # Assert - asymmetric padding: 5 * 0.9 = 4.5, 5 * 1.1 = 5.5
        self.assertIsNotNone(scale)
        self.assertAlmostEqual(scale['min'], 4.5, places=2)
        self.assertAlmostEqual(scale['max'], 5.5, places=2)

    def test_handles_negative_values(self):
        """Test that negative values are handled correctly in scale"""
        # Setup
        loc_type = LocationType.objects.create(name='City')
        location = Location.objects.create(id='1', name='Test City', location_type=loc_type)

        category = Category.objects.create(name='Test Category', share_axes=True)
        indicator = Indicator.objects.create(name='Temperature', category=category, indicator_type='count')
        IndicatorDataVisual.objects.create(
            indicator=indicator,
            data_visual_type='line',
            start_date='2023-01-01',
            end_date='2023-12-31',
            columns=1
        )
        source = IndicatorSource.objects.create(name='Test Source')
        # Values: -10 and 5
        IndicatorValue.objects.create(
            indicator=indicator, location=location, source=source,
            value=-10, start_date='2023-01-01', end_date='2023-12-31'
        )
        IndicatorValue.objects.create(
            indicator=indicator, location=location, source=source,
            value=5, start_date='2023-01-01', end_date='2023-12-31'
        )

        # Test
        scale = category.get_axis_scale(location.id)

        # Assert
        # Range = 5 - (-10) = 15
        # Padding = 15 * 0.1 = 1.5
        # Expected: min = -10 - 1.5 = -11.5, max = 5 + 1.5 = 6.5
        self.assertIsNotNone(scale)
        self.assertAlmostEqual(scale['min'], -11.5, places=1)
        self.assertAlmostEqual(scale['max'], 6.5, places=1)

    def test_filters_none_values(self):
        """Test that None values are filtered out and don't affect scale"""
        # Setup
        loc_type = LocationType.objects.create(name='City')
        location = Location.objects.create(id='1', name='Test City', location_type=loc_type)

        category = Category.objects.create(name='Test Category', share_axes=True)
        indicator = Indicator.objects.create(name='Population', category=category, indicator_type='count')
        IndicatorDataVisual.objects.create(
            indicator=indicator,
            data_visual_type='column',
            start_date='2023-01-01',
            end_date='2023-12-31',
            columns=1
        )
        source = IndicatorSource.objects.create(name='Test Source')
        # Mix of None and numeric values
        IndicatorValue.objects.create(
            indicator=indicator, location=location, source=source,
            value=10, start_date='2023-01-01', end_date='2023-12-31'
        )
        IndicatorValue.objects.create(
            indicator=indicator, location=location, source=source,
            value=None, start_date='2023-01-01', end_date='2023-12-31'
        )
        IndicatorValue.objects.create(
            indicator=indicator, location=location, source=source,
            value=20, start_date='2023-01-01', end_date='2023-12-31'
        )

        # Test
        scale = category.get_axis_scale(location.id)

        # Assert - should calculate based on 10 and 20 only
        # Range = 20 - 10 = 10
        # Padding = 10 * 0.1 = 1
        # Expected: min = 9, max = 21
        self.assertIsNotNone(scale)
        self.assertEqual(scale['min'], 9)
        self.assertEqual(scale['max'], 21)

    def test_includes_parent_location_values(self):
        """Test that parent location values are included when location_comparison_type='parents'"""
        # Setup
        loc_type = LocationType.objects.create(name='City')
        parent_type = LocationType.objects.create(name='County')

        location = Location.objects.create(id='1', name='Test City', location_type=loc_type)
        parent = Location.objects.create(id='2', name='Test County', location_type=parent_type)

        category = Category.objects.create(name='Test Category', share_axes=True)
        indicator = Indicator.objects.create(name='Population', category=category, indicator_type='count')
        visual = IndicatorDataVisual.objects.create(
            indicator=indicator,
            data_visual_type='column',
            location_comparison_type='parents',  # Enable parent comparison
            start_date='2023-01-01',
            end_date='2023-12-31',
            columns=1
        )
        source = IndicatorSource.objects.create(name='Test Source')

        # Primary location value: 10
        IndicatorValue.objects.create(
            indicator=indicator, location=location, source=source,
            value=10, start_date='2023-01-01', end_date='2023-12-31'
        )
        # Parent location value: 100
        IndicatorValue.objects.create(
            indicator=indicator, location=parent, source=source,
            value=100, start_date='2023-01-01', end_date='2023-12-31'
        )

        # Test
        scale = category.get_axis_scale(location.id, parent_location_ids=['2'])

        # Assert - scale should include both 10 and 100
        # Range = 100 - 10 = 90
        # Padding = 90 * 0.1 = 9
        # Expected: min = 10 - 9 = 1, max = 100 + 9 = 109
        self.assertIsNotNone(scale)
        self.assertAlmostEqual(scale['min'], 1, places=0)
        self.assertAlmostEqual(scale['max'], 109, places=0)

    def test_handles_missing_comparison_parameters(self):
        """Test that missing parent_location_ids parameter doesn't cause error"""
        # Setup
        loc_type = LocationType.objects.create(name='City')
        location = Location.objects.create(id='1', name='Test City', location_type=loc_type)

        category = Category.objects.create(name='Test Category', share_axes=True)
        indicator = Indicator.objects.create(name='Population', category=category, indicator_type='count')
        visual = IndicatorDataVisual.objects.create(
            indicator=indicator,
            data_visual_type='column',
            location_comparison_type='parents',  # Expects parents
            start_date='2023-01-01',
            end_date='2023-12-31',
            columns=1
        )
        source = IndicatorSource.objects.create(name='Test Source')
        IndicatorValue.objects.create(
            indicator=indicator, location=location, source=source,
            value=50, start_date='2023-01-01', end_date='2023-12-31'
        )

        # Test - call without parent_location_ids parameter
        scale = category.get_axis_scale(location.id, parent_location_ids=None)

        # Assert - should not error, should calculate based on primary location only
        self.assertIsNotNone(scale)
        # Single value 50: 50 * 0.9 = 45, 50 * 1.1 = 55
        self.assertAlmostEqual(scale['min'], 45, places=0)
        self.assertAlmostEqual(scale['max'], 55, places=0)
