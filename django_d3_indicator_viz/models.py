from django.contrib.gis.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class Section(models.Model):
    """
    Represents a section for categories.
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

    def __str__(self):
        return self.name

    class Meta:
        db_table = "section"
        ordering = ["sort_order"]


class Category(models.Model):
    """
    Represents a category for indicators, such as "Health", "Education", etc.
    """

    # The name of the category
    name = models.TextField()

    # A description or additional information about the category
    about = models.TextField()

    # The sort order for the category
    sort_order = models.PositiveIntegerField(
        default=0, null=False, blank=False, db_index=True
    )

    # The color associated with the category
    color = models.TextField(null=True, blank=True)

    # An image URL or path associated with the category
    image = models.TextField(null=True, blank=True)

    # The section this category belongs to
    section = models.ForeignKey(
        Section, on_delete=models.CASCADE, null=True, blank=True
    )

    def __str__(self):
        return self.name

    class Meta:
        db_table = "category"
        verbose_name_plural = "categories"
        ordering = ["sort_order"]


class LocationType(models.Model):
    """
    Represents a type of location, such as "City", "County", "State", etc.
    """

    # The name of the location type
    name = models.TextField()

    def __str__(self):
        return self.name

    class Meta:
        db_table = "location_type"


class Location(models.Model):
    """
    Represents a geographical location, such as a city, county, or state.
    """

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


class Indicator(models.Model):
    """
    Represents an indicator, which is a measurable value that provides information about a specific aspect of a location.
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

    def __str__(self):
        return self.name

    class Meta:
        db_table = "indicator"
        ordering = ["sort_order"]


class IndicatorFilterType(models.Model):
    """
    Represents a type of filter that can be applied to indicators.
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
    Represents an option for a specific indicator filter type.
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

    # The count (numerator) for this indicator value
    count = models.FloatField(null=True, blank=True)

    # The margin of error for the count
    count_moe = models.FloatField(null=True, blank=True)

    # The universe (denominator) for this indicator value
    universe = models.FloatField(null=True, blank=True)

    # The margin of error for the universe
    universe_moe = models.FloatField(null=True, blank=True)

    # The percentage value for this indicator value
    percentage = models.FloatField(null=True, blank=True)

    # The margin of error for the percentage
    percentage_moe = models.FloatField(null=True, blank=True)

    # The rate for this indicator value, such as a ratio or rate per 1,000 or 100,000
    rate = models.FloatField(null=True, blank=True)

    # The margin of error for the rate
    rate_moe = models.FloatField(null=True, blank=True)

    # The rate per unit for this indicator value, such as 1,000 or 100,000
    rate_per = models.FloatField(null=True, blank=True)

    # The dollar amount for this indicator value
    dollars = models.FloatField(null=True, blank=True)

    # The margin of error for the dollar amount
    dollars_moe = models.FloatField(null=True, blank=True)

    # The index value for this indicator value
    index = models.FloatField(null=True, blank=True)

    # The margin of error for the index value
    index_moe = models.FloatField(null=True, blank=True)

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

    class Meta:
        db_table = "data_visual"

class DataVisualLocationComparisonType(models.TextChoices):
    """
    Represents the type of location comparison for data visualizations.
    """
    PARENTS = "parents",
    SIBLINGS = "siblings"

    def __str__(self):
        return self.name

    class Meta:
        db_table = "data_visual_location_comparison_type"


class ValueField(models.TextChoices):
    """
    Represents the type of value field to display in data visuals.
    """

    COUNT = "count",
    UNIVERSE = "universe",
    PERCENTAGE = "percentage",
    RATE = "rate",
    RATE_PER = "rate_per",
    DOLLARS = "dollars",
    INDEX = "index"

    def __str__(self):
        return self.name

    class Meta:
        db_table = "value_field"

class IndicatorDataVisual(models.Model):
    """
    Represents a data visual for an indicator, including its type, source, date range, and other attributes.
    """

    # The source of the indicator data visual, such as "Census", "CDC", etc.
    source = models.ForeignKey(
        IndicatorSource, on_delete=models.CASCADE, null=True, blank=True
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

    # The value field to display in the data visual, such as "count", "universe", "percentage", etc.
    value_field = models.TextField(choices=ValueField.choices)

    # The number of columns the data visual will span in a grid layout
    columns = models.IntegerField(
        default=12, null=False, blank=False, db_index=True, validators=[MinValueValidator(1), MaxValueValidator(12)]
    )

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
