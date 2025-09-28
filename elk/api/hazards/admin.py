from __future__ import annotations

from django.contrib import admin

from . import geometry
from .models import Hazard, HazardPresentation, Location, Tip


@admin.register(Hazard)
class HazardAdmin(admin.ModelAdmin):
    list_display = ("name", "severity", "type", "updated_at")
    search_fields = ("name",)
    list_filter = ("severity", "type")
    filter_horizontal = ("tips",)


@admin.register(HazardPresentation)
class HazardPresentationAdmin(admin.ModelAdmin):
    list_display = ("hazard", "location", "radius_meters", "updated_at")
    search_fields = ("hazard__name", "location__name")

    def save_model(self, request, obj, form, change):
        if obj.center_latitude is not None and obj.center_longitude is not None and obj.radius_meters and not obj.boundary:
            center = geometry.Point(float(obj.center_latitude), float(obj.center_longitude))
            obj.boundary = [
                {"latitude": point.latitude, "longitude": point.longitude}
                for point in geometry.circle_boundary(center, obj.radius_meters)
            ]
        super().save_model(request, obj, form, change)
@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ("name", "type", "latitude", "longitude")
    search_fields = ("name",)
    list_filter = ("type",)


@admin.register(Tip)
class TipAdmin(admin.ModelAdmin):
    list_display = ("name", "updated_at")
    search_fields = ("name",)
