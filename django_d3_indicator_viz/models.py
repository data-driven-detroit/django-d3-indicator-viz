from django.contrib.gis.db import models
from django.db.models import Window, Prefetch, F, Q
from django.db.models.functions import RowNumber
from django.core.validators import MinValueValidator, MaxValueValidator
from django.forms import ValidationError


class Section(models.Model):
    """
    Represents a section for categories, such as "Youth & Family Demographics".
    Sections group related categories together and are the top level of the data hierarchy.
    """

    # The name of the section
    name = models.TextField()

    # The sort order for the section
    sort_order = models.PositiveIntegerField(
        default=0, null=False, blank=False, db_index=True
    )

    # The color associated with the section
    color = models.TextField(null=True, blank=True)

    # An image URL or path associated with the section
    image = models.TextField(null=True, blank=True)

    # An anchor for linking to this category in a web page
    anchor = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "section"
        ordering = ["sort_order"]

    def __str__(self):
        return self.name

    def __get_indicators(self, location_id, partition_by):
        priority_subquery = IndicatorDataVisualSource.objects.filter(
            data_visual=OuterRef('indicator__indicatordatavisual'),
            source=OuterRef('source')
        ).values('priority')[:1]

        return IndicatorValue.objects.filter(
            location_id=location_id,
            indicator__category__section_id=self.id
        ).annotate(
            source_priority=priority_subquery,
            rn=Window(
                expression=RowNumber(),
                partition_by=partition_by,
                order_by=[F('source_priority').asc(nulls_last=True), F('start_date').desc()]
            ),
            data_visual_type=F('indicator__indicatordatavisual__data_visual_type')
        ).filter(
            Q(rn=1) | Q(data_visual_type='line')
        ).select_related('filter_option', 'location', 'source')

    def get_annotated_indicators(self, location_id):
        # NO filter_option_id
        return self.__get_indicators(location_id, [F('indicator_id')])

    def get_filtered_values(self, location_id):
        """
        This queries from the point of view of the IndicatorValue, but 
        filters to the values that fall in this section.
        """

        return self.__get_indicators(location_id, [F('indicator_id'), F('filter_option_id')])

    def get_hydrated_categories(self, location_id):
        annotated_indicators = self.get_annotated_indicators(location_id)
        filtered_values = self.get_filtered_values(location_id)

        categories = Category.objects.filter(
          section_id=self.id
        ).prefetch_related(
          Prefetch(
              'indicator_set__indicatorvalue_set',
              queryset=annotated_indicators,
              to_attr='annotated_indicators'
          ),
          Prefetch(
              'indicator_set__indicatorvalue_set',
              queryset=filtered_values,
              to_attr='filtered_values'
          ),
          'indicator_set__indicatordatavisual_set'
        ).select_related('section')

        return categories


class Category(models.Model):
    """
    Represents a category for indicators, such as "Youth population, sex & age".
    Categories group related indicators together and are the second level of the data hierarchy.
    """

    # The name of the category
    name = models.TextField()

    # A description or additional information about the category
    about = models.TextField()

    # The sort order for the category
    sort_order = models.PositiveIntegerField(
        default=0, null=False, blank=False, db_index=True
    )

    # The color associated with the category (USED IN NVI, not in SDC / HIP)
    color = models.TextField(null=True, blank=True)

    # An image URL or path associated with the category
    image = models.TextField(null=True, blank=True)

    # The section this category belongs to
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, null=True, blank=True
    )
    
    # If the axes are shared among all the column charts in the visual
    share_axes = models.BooleanField(
        default=False,
        help_text="When enabled, all line and column charts in this category will share the same Y-axis scale for easier comparison."
    )

    # An anchor for linking to this category in a web page
    anchor = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "category"
        verbose_name_plural = "categories"
        ordering = ["sort_order"]

    def __str__(self):
        return self.name
        

class LocationType(models.Model):
    """
    Represents a type of location, such as "City", "County", "State", etc.
    """

    # The name of the location type
    name = models.TextField()

    # The parent location types
    parent_location_types = models.ManyToManyField("LocationType", related_name="child_location_types", blank=True)

    # The sort order for the location type
    sort_order = models.PositiveIntegerField(
        default=0, null=False, blank=False, db_index=True
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "location_type"


class Location(models.Model):
    """
    Represents a geographical location, such as a Detroit, Wayne County, or Michigan.
    """

    # The unique identifier for the location (e.g., FIPS code)
    id = models.CharField(max_length=50, primary_key=True)

    # The name of the location
    name = models.TextField()

    # The type of the location
    location_type = models.ForeignKey(LocationType, on_delete=models.CASCADE)

    # The location geometry
    geometry = models.MultiPolygonField(null=True, blank=True)

    # The color associated with the location
    color = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "location"


class CustomLocation(models.Model):
    """
    Represents a custom geographical location, such as a collection of specific tracts or zip codes.
    """

    # The name of the custom location
    name = models.TextField(blank=False, null=False, unique=True)

    # The type of the locations that make up this custom location
    location_type = models.ForeignKey(LocationType, on_delete=models.CASCADE)

    # The geometry of the custom location (union of the geometries of the locations that make up this custom location)
    geometry = models.MultiPolygonField(null=True, blank=True)

    # The color associated with the custom location
    color = models.TextField(null=True, blank=True)

    # A unique slug for the custom location
    slug = models.CharField(max_length=1000, blank=False, null=False, unique=True)

    # The organization that created the custom location
    organization = models.TextField(blank=True, null=True)

    # The locations that make up this custom location
    locations = models.ManyToManyField(Location, related_name="custom_locations", blank=False)

    # The date and time when the custom location was created
    created_at = models.DateTimeField(auto_now_add=True)

    # The date and time when the custom location was last updated
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        # raise a validation error if the first part of the slug before a hyphen matches an existing location id
        if Location.objects.filter(id__iexact=self.slug.split('-')[0]).exists():
            raise ValidationError({'slug': 'Slug must be unique and cannot match any existing location id.'})

    def __str__(self):
        return self.name
    
    class Meta:
        db_table = "custom_location"


class IndicatorSource(models.Model):
    """
    Represents a source of data for indicators, such as "ACS 5-year estimates Table B01001", "MDE", etc.
    """

    # The name of the indicator source
    name = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = "indicator_source"


class IndicatorType(models.TextChoices):
    """
    Represents the type of indicator, such as "percentage", "average", "count", etc.
    Necessary for custom location aggregation logic.
    """

    PERCENTAGE = "percentage",
    AVERAGE = "average",
    MEDIAN = "median",
    COUNT = "count",
    RATE = "rate",
    INDEX = "index"

    def __str__(self):
        return self.name


class Indicator(models.Model):
    """
    Represents an indicator, which is a measurable value that provides information about a specific aspect of a location.
    Indicators are the third level of the data hierarchy.
    """

    # The name of the indicator
    name = models.TextField()

    # A qualifier, such as "All children under 18 years old" (universe) or " D3 Open Data Portal, State of Michigan, Department of Heath and Human Services data" (source)
    qualifier = models.TextField(null=True, blank=True)

    # The sort order for the indicator
    sort_order = models.PositiveIntegerField(
        default=0, null=False, blank=False, db_index=True
    )

    # The category this indicator belongs to
    category = models.ForeignKey(
        Category, on_delete=models.CASCADE, null=True, blank=True
    )

    # The type of the indicator, such as "percentage", "average", "count", etc.
    indicator_type = models.TextField(choices=IndicatorType.choices, null=True, blank=True)

    # The rate per which the indicator is calculated, if applicable (e.g., per 1,000 or per 100,000)
    rate_per = models.IntegerField(null=True, blank=True)

    # A formatter string for displaying the indicator value, such as ${value} for dollars or {value}% for percentage
    formatter = models.TextField(null=True, blank=True)

    def to_json(self):
        """Returns JSON representation of this indicator for use in templates."""
        from django_d3_indicator_viz.views import IndicatorSerializer
        import json
        return json.dumps(IndicatorSerializer(self).data)

    def __str__(self):
        return self.name

    class Meta:
        db_table = "indicator"
        ordering = ["sort_order"]


class IndicatorFilterType(models.Model):
    """
    Represents a type of filter that can be applied to indicators, such as Age.
    """

    # The name of the filter type
    name = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = "indicator_filter_type"
        verbose_name_plural = "indicator filters"


class IndicatorFilterOption(models.Model):
    """
    Represents an option for a specific indicator filter type, such as Under 18 or 65 and Older.
    """

    # The name of the filter option
    name = models.TextField()

    # The indicator filter type this option belongs to
    indicator_filter_type = models.ForeignKey(IndicatorFilterType, on_delete=models.CASCADE)

    # The sort order for the filter option
    sort_order = models.PositiveIntegerField(
        default=0, null=False, blank=False, db_index=True
    )

    def __str__(self):
        return self.indicator_filter_type.name + ' - ' + self.name

    class Meta:
        db_table = "indicator_filter_option"
        unique_together = ("name", "indicator_filter_type")
        ordering = ["sort_order"]


class IndicatorValue(models.Model):
    """
    Represents a value for an indicator at a specific location, time, and filter.
    """

    # The source of the indicator value
    source = models.ForeignKey(
        IndicatorSource, on_delete=models.CASCADE, null=True, blank=True
    )

    # The start date for the indicator value
    start_date = models.DateField()

    # The end date for the indicator value
    end_date = models.DateField()

    # The indicator this value belongs to
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE)

    # The filter option applied to this indicator value, if any
    filter_option = models.ForeignKey(
        IndicatorFilterOption, on_delete=models.CASCADE, null=True, blank=True
    )

    # The location that this indicator value represents
    location = models.ForeignKey(Location, on_delete=models.CASCADE)

    # The actual value for this indicator value
    value = models.FloatField(null=True, blank=True)

    # The margin of error for the value
    value_moe = models.FloatField(null=True, blank=True)

    # The count (numerator) for this indicator value
    count = models.FloatField(null=True, blank=True)

    # The margin of error for the count
    count_moe = models.FloatField(null=True, blank=True)

    # The universe (denominator) for this indicator value
    universe = models.FloatField(null=True, blank=True)

    # The margin of error for the universe
    universe_moe = models.FloatField(null=True, blank=True)
    
    active_data = models.BooleanField(default=False)


    def __str__(self):
        return (
            ("" if not self.source else self.source.name)
            + " - "
            + self.indicator.name
            + " - "
            + ("" if not self.filter_option else self.filter_option.name)
            + " - "
            + self.location.name
            + " - "
            + str(self.end_date)
        )

    class Meta:
        db_table = "indicator_value"
        unique_together = (
            "source",
            "start_date",
            "end_date",
            "indicator",
            "filter_option",
            "location",
        )


class DataVisualType(models.TextChoices):
    """
    Represents the type of data visualizations that can be created for indicators.
    """
    
    BAN = "ban",
    COLUMN = "column",
    DONUT = "donut",
    MIN_MED_MAX = "min_med_max",
    LINE = "line",

    def __str__(self):
        return self.name


class DataVisualLocationComparisonType(models.TextChoices):
    """
    Represents the type of location comparison for data visualizations.
    """
    
    PARENTS = "parents",
    SIBLINGS = "siblings"

    def __str__(self):
        return self.name


class ColorScale(models.Model):
    """
    Represents a color scale for data visualizations.
    """

    # The name of the color scale
    name = models.CharField(max_length=100)

    # The colors in the color scale as a JSON array of hex color codes
    colors = models.JSONField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = "color_scale"


class IndicatorDataVisualSource(models.Model):
    """
    Intermediate model to maintain priority order for data visual sources.
    Allows multiple sources per data visual with fallback priority.
    """

    # The data visual this source belongs to
    data_visual = models.ForeignKey('IndicatorDataVisual', on_delete=models.CASCADE)

    # The source of the indicator data
    source = models.ForeignKey(IndicatorSource, on_delete=models.CASCADE)

    # Priority/order of this source (lower number = higher priority, 0 = primary)
    priority = models.PositiveIntegerField(
        default=0,
        help_text="Source priority: 0 = primary source, 1+ = fallback sources in order"
    )

    class Meta:
        db_table = "indicator_data_visual_source"
        ordering = ['priority']
        unique_together = ('data_visual', 'source')

    def __str__(self):
        return f"{self.data_visual.indicator.name} - {self.source.name} (priority {self.priority})"


class IndicatorDataVisual(models.Model):
    """
    Represents a data visual for an indicator, including its type, source, 
    date range, and other attributes.
    """

    # The sources for this data visual, ordered by priority (primary + fallbacks)
    sources = models.ManyToManyField(
        IndicatorSource,
        through='IndicatorDataVisualSource',
        related_name='data_visuals',
        help_text="Ordered list of data sources. First source is primary, rest are fallbacks."
    )

    # The start for the indicator data visual, representing the time period it covers
    start_date = models.DateField()

    # The end date for the indicator data visual, representing the time period it covers
    end_date = models.DateField()

    # The indicator this data visual represents
    indicator = models.ForeignKey(Indicator, on_delete=models.CASCADE)

    # The data visual type, such as "ban", "column", "donut", etc.
    data_visual_type = models.TextField(
        choices=DataVisualType.choices,
        null=True,
        blank=True
    )

    # The location comparison type, such as "parents" or "siblings"
    location_comparison_type = models.TextField(
        choices=DataVisualLocationComparisonType.choices,
        null=True,
        blank=True
    )

    # The number of columns the data visual will span in a grid layout
    columns = models.IntegerField(
        default=12, null=False, blank=False, db_index=True, validators=[
            MinValueValidator(1), MaxValueValidator(12)
        ]
    )

    # The color scale to use for the data visual
    color_scale = models.ForeignKey(ColorScale, on_delete=models.CASCADE, null=True, blank=True)

    def get_primary_source(self):
        """Returns the primary (priority 0) source, or None if no sources."""
        source_rel = self.indicatordatavisualsource_set.filter(priority=0).first()
        return source_rel.source if source_rel else None

    def get_ordered_sources(self):
        """Returns all sources ordered by priority."""
        return [rel.source for rel in self.indicatordatavisualsource_set.all().order_by('priority')]

    def resolve_source_for_location(self, location_id):
        """
        Returns the best available source for a specific location.
        Tries sources in priority order, returns first one with data.
        """
        for source in self.get_ordered_sources():
            has_data = IndicatorValue.objects.filter(
                indicator_id=self.indicator_id,
                source_id=source.id,
                start_date=self.start_date,
                end_date=self.end_date,
                location_id=location_id,
            ).exists()

            if has_data:
                return source

        # No data found for any source, return primary anyway
        return self.get_primary_source()

    def to_dict_with_resolved_source(self, location_id):
        """
        Returns a dictionary representation with resolved source for a location.
        Used by views to build data_visuals context.
        """
        resolved_source = self.resolve_source_for_location(location_id)

        if not resolved_source:
            return None

        return {
            "id": self.id,
            "source_id": resolved_source.id,
            "source__name": resolved_source.name,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "indicator_id": self.indicator_id,
            "data_visual_type": self.data_visual_type,
            "location_comparison_type": self.location_comparison_type,
            "columns": self.columns,
            "color_scale_id": self.color_scale_id,
        }

    def to_json(self):
        """Returns JSON representation of this data visual for use in templates."""
        from django_d3_indicator_viz.views import IndicatorDataVisualSerializer
        import json
        return json.dumps(IndicatorDataVisualSerializer(self).data)

    def __str__(self):
        return (
            self.indicator.name
            + " - "
            + self.data_visual_type
        )

    class Meta:
        db_table = "indicator_data_visual"
        unique_together = (
            "indicator",
            "start_date",
            "end_date",
            "data_visual_type",
        )
        ordering = ["indicator__category__section__sort_order", "indicator__category__sort_order", "indicator__sort_order"]
