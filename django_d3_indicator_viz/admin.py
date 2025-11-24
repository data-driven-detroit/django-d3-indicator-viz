from django.contrib import admin
from django.db import models as django_models
from django.forms import TextInput
from django.urls import reverse
from django.utils.html import format_html

from import_export.admin import ImportExportMixin
from adminsortable2.admin import SortableAdminBase
from adminsortable2.admin import SortableAdminMixin
from adminsortable2.admin import SortableTabularInline


from .models import *


class IndicatorInline(SortableTabularInline):
    model = Indicator
    ordering = ["sort_order"]
    extra = 0
    fields = ["name"]
    readonly_fields = ["name"]
    show_change_link = True


class CategoryInline(SortableTabularInline):
    model = Category
    ordering = ["sort_order"]
    extra = 0
    fields = ["name"]
    readonly_fields = ["name"]
    show_change_link = True


class SectionAdmin(ImportExportMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = ["id", "name", "sort_order"]
    readonly_fields = ("id",)
    inlines = [CategoryInline]
    ordering = ["sort_order"]
    formfield_overrides = {
        models.TextField: {"widget": TextInput(attrs={"style": "width: 500px"})},
    }


admin.site.register(Section, SectionAdmin)


class CategoryAdmin(ImportExportMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = ["id", "section", "name", "sort_order"]
    readonly_fields = ("id","section_link")
    inlines = [IndicatorInline]
    ordering = ["sort_order"]
    formfield_overrides = {
        models.TextField: {"widget": TextInput(attrs={"style": "width: 500px"})},
    }

    def section_link(self, obj):
        meta = obj.section._meta
        url = reverse(f"admin:{meta.app_label}_{meta.model_name}_change", args=[obj.section_id])
        return format_html('<a href="{}">{}</a>', url, obj.section)

    section_link.short_description = "Section"


# admin.site.register(Category, CategoryAdmin)


class LocationTypeAdmin(
    ImportExportMixin, SortableAdminMixin, admin.ModelAdmin
):
    list_display = ["id", "name", "sort_order"]
    readonly_fields = ("id",)
    ordering = ["sort_order"]


admin.site.register(LocationType, LocationTypeAdmin)


class LocationAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["id", "location_type", "name"]
    readonly_fields = ("id",)
    ordering = ["location_type", "name"]


# admin.site.register(Location, LocationAdmin)


class CustomLocationAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["id", "name"]
    readonly_fields = ("id",)
    ordering = ["created_at"]


admin.site.register(CustomLocation, CustomLocationAdmin)


class IndicatorSourceAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["id", "name"]
    readonly_fields = ("id",)
    ordering = ["name"]


# admin.site.register(IndicatorSource, IndicatorSourceAdmin)


class VisualInline(admin.TabularInline):
    model = IndicatorDataVisual
    can_delete = False
    max_num = 1
    extra = 0


class IndicatorAdmin(ImportExportMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = ["id", "category", "name", "sort_order"]
    readonly_fields = ("id","category_link")
    ordering = ["sort_order"]
    inlines = [VisualInline]

    formfield_overrides = {
        models.TextField: {"widget": TextInput(attrs={"style": "width: 500px"})},
    }


    def category_link(self, obj):
        meta = obj.category._meta
        url = reverse(f"admin:{meta.app_label}_{meta.model_name}_change", args=[obj.category_id])
        return format_html('<a href="{}">{}</a>', url, obj.category)

    category_link.short_description = "Category"



admin.site.register(Indicator, IndicatorAdmin)


class IndicatorFilterOptionInline(SortableTabularInline):
    model = IndicatorFilterOption
    ordering = ["sort_order"]
    extra = 0


class IndicatorFilterTypeAdmin(
    ImportExportMixin, SortableAdminBase, admin.ModelAdmin
):
    list_display = ["id", "name"]
    readonly_fields = ("id",)
    ordering = ["name"]
    inlines = [IndicatorFilterOptionInline]


admin.site.register(IndicatorFilterType, IndicatorFilterTypeAdmin)


class IndicatorValueAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = [
        "id",
        "indicator",
        "location",
        "start_date",
        "end_date",
        "source",
    ]
    readonly_fields = ("id",)
    ordering = ["indicator", "location", "start_date", "end_date", "source"]


# admin.site.register(IndicatorValue, IndicatorValueAdmin)


class ColorScaleAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["id", "name", "colors"]
    readonly_fields = ("id",)
    ordering = ["name"]


admin.site.register(ColorScale, ColorScaleAdmin)


class IndicatorDataVisualAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = [
        "id",
        "indicator",
        "data_visual_type",
        "start_date",
        "end_date",
        "source",
    ]
    readonly_fields = ("id",)
    ordering = ["indicator", "start_date", "end_date", "source"]


# admin.site.register(IndicatorDataVisual, IndicatorDataVisualAdmin)
