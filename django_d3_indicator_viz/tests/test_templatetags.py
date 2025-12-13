from django.test import TestCase
from django_d3_indicator_viz.templatetags.madlibs import tojson, dict_get
import json


class TemplateTagTests(TestCase):
    """Tests for custom template tags/filters"""

    def test_tojson_converts_dict_to_json(self):
        """Test that tojson filter converts Python dict to JSON string"""
        # Setup
        test_dict = {'min': 0, 'max': 100}

        # Test
        result = tojson(test_dict)

        # Assert
        # Result should be JSON string
        self.assertIsInstance(result, str)

        # Should be valid JSON
        parsed = json.loads(result)
        self.assertEqual(parsed['min'], 0)
        self.assertEqual(parsed['max'], 100)

        # Should match expected format
        self.assertIn('"min":', result)
        self.assertIn('"max":', result)

    def test_dict_get_retrieves_value(self):
        """Test that dict_get filter retrieves values from dict with variable key"""
        # Setup
        test_dict = {1: 'value_a', 2: 'value_b', 3: 'value_c'}

        # Test
        result1 = dict_get(test_dict, 1)
        result2 = dict_get(test_dict, 2)
        result_missing = dict_get(test_dict, 999)

        # Assert
        self.assertEqual(result1, 'value_a')
        self.assertEqual(result2, 'value_b')
        self.assertIsNone(result_missing, "Should return None for missing key")

    def test_dict_get_handles_none_dict(self):
        """Test that dict_get handles None dict gracefully"""
        # Test
        result = dict_get(None, 1)

        # Assert
        self.assertIsNone(result, "Should return None when dict is None")

    def test_tojson_handles_nested_structures(self):
        """Test that tojson handles nested dicts/lists correctly"""
        # Setup
        test_data = {
            'min': -10,
            'max': 100,
            'metadata': {
                'unit': 'count',
                'precision': 2
            },
            'values': [1, 2, 3]
        }

        # Test
        result = tojson(test_data)

        # Assert
        parsed = json.loads(result)
        self.assertEqual(parsed['min'], -10)
        self.assertEqual(parsed['max'], 100)
        self.assertEqual(parsed['metadata']['unit'], 'count')
        self.assertListEqual(parsed['values'], [1, 2, 3])
