"""
Django REST Framework serializers for django-d3-indicator-viz models.
"""
from rest_framework import serializers
from .models import (
    Section,
    Category,
    Indicator,
    IndicatorDataVisual,
    IndicatorValue,
    IndicatorFilterOption,
    Location,
    LocationType,
    ColorScale,
    IndicatorSource,
)


class SectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Section
        fields = ['id', 'name', 'sort_order', 'color', 'image', 'anchor']


class IndicatorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Indicator
        fields = ['id', 'name', 'qualifier', 'sort_order', 'category', 'indicator_type', 'rate_per', 'formatter']


class CategorySerializer(serializers.ModelSerializer):
    indicators = IndicatorSerializer(many=True, read_only=True, source='indicator_set')

    class Meta:
        model = Category
        fields = ['id', 'name', 'about', 'sort_order', 'color', 'image', 'section', 'anchor', 'indicators']


class IndicatorSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicatorSource
        fields = ['id', 'name']


class DataVisualSerializer(serializers.ModelSerializer):
    source_id = serializers.SerializerMethodField()

    class Meta:
        model = IndicatorDataVisual
        fields = ['id', 'indicator_id', 'data_visual_type', 'start_date', 'end_date',
                  'location_comparison_type', 'color_scale_id', 'columns', 'source_id']

    def get_source_id(self, obj):
        """Returns the primary source ID (priority 0)."""
        first_source = obj.indicatordatavisualsource_set.first()
        return first_source.source.id if first_source else None


class IndicatorValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicatorValue
        fields = ['id', 'indicator', 'location', 'source', 'filter_option',
                  'start_date', 'end_date', 'value', 'value_moe', 'count',
                  'count_moe', 'universe', 'universe_moe']


class IndicatorFilterOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = IndicatorFilterOption
        fields = ['id', 'name', 'sort_order']


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ['id', 'name', 'location_type_id', 'color']


class LocationTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationType
        fields = ['id', 'name', 'sort_order']


class ColorScaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorScale
        fields = ['id', 'name', 'colors']
