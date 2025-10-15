from django.contrib import admin
from .models import *
from import_export.admin import ImportExportMixin
from adminsortable2.admin import SortableAdminBase
from adminsortable2.admin import SortableAdminMixin
from adminsortable2.admin import SortableTabularInline


class IndicatorInline(SortableTabularInline):
    model = Indicator
    ordering = ["sort_order"]
    max_num = 1
    extra = 0


class CategoryInline(SortableTabularInline):
    model = Category
    ordering = ["sort_order"]
    extra = 0


class SectionAdmin(ImportExportMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = ["id", "name", "sort_order"]
    readonly_fields = ("id",)
    inlines = [CategoryInline]
    ordering = ["sort_order"]


admin.site.register(Section, SectionAdmin)


class CategoryAdmin(ImportExportMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = ["id", "section", "name", "sort_order"]
    readonly_fields = ("id",)
    inlines = [IndicatorInline]
    ordering = ["sort_order"]


admin.site.register(Category, CategoryAdmin)


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


admin.site.register(Location, LocationAdmin)


class CustomLocationAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["id", "name"]
    readonly_fields = ("id",)
    ordering = ["created_at"]


admin.site.register(CustomLocation, CustomLocationAdmin)


class IndicatorSourceAdmin(ImportExportMixin, admin.ModelAdmin):
    list_display = ["id", "name"]
    readonly_fields = ("id",)
    ordering = ["name"]


admin.site.register(IndicatorSource, IndicatorSourceAdmin)


class VisualInline(admin.TabularInline):
    model = IndicatorDataVisual
    can_delete = False


class IndicatorAdmin(ImportExportMixin, SortableAdminMixin, admin.ModelAdmin):
    list_display = ["id", "category", "name", "sort_order"]
    readonly_fields = ("id",)
    ordering = ["sort_order"]
    inlines = [VisualInline]


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


admin.site.register(IndicatorValue, IndicatorValueAdmin)


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


admin.site.register(IndicatorDataVisual, IndicatorDataVisualAdmin)
