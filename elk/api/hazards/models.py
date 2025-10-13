from __future__ import annotations

import uuid

from typing import List

from django.core.validators import MinLengthValidator
from django.db import models
from django.utils import timezone

from . import geometry


class HazardSeverity(models.TextChoices):
    LOW = "low", "Low"
    MEDIUM = "medium", "Medium"
    HIGH = "high", "High"


class HazardType(models.TextChoices):
    ANIMAL = "animal", "Animal"
    EVENT = "event", "Event"
    WEATHER = "weather", "Weather"
    DISEASE = "disease", "Disease"


class LocationKind(models.TextChoices):
    NATIONAL_PARK = "National Park", "National Park"
    REGION = "Region", "Region"


class Location(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    type = models.CharField(max_length=32, choices=LocationKind.choices)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    description = models.TextField(blank=True)
    image = models.URLField(blank=True)
    google_maps_id = models.CharField(max_length=255, blank=True)
    boundary = models.JSONField(
        help_text="Collection of GPS coordinates describing the area.",
        default=list,
        blank=True,
    )
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - representation only
        return self.name


class Hazard(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, unique=True)
    severity = models.CharField(max_length=10, choices=HazardSeverity.choices)
    type = models.CharField(max_length=16, choices=HazardType.choices)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - representation only
        return f"{self.name} ({self.get_severity_display()})"


class Tip(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(validators=[MinLengthValidator(1)])
    hazards = models.ManyToManyField(Hazard, related_name="tips", blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("name",)
        ordering = ["name"]

    def __str__(self) -> str:  # pragma: no cover - representation only
        return self.name


class HazardPresentation(models.Model):
    hazard = models.ForeignKey(Hazard, on_delete=models.CASCADE, related_name="presentations")
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="presentations",
    )
    center_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    center_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius_meters = models.PositiveIntegerField()
    boundary = models.JSONField(help_text="Collection of GPS coordinates describing the area.", blank=True, default=list)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Hazard presentation"
        verbose_name_plural = "Hazard presentations"

    def __str__(self) -> str:  # pragma: no cover - representation only
        return f"Presentation of {self.hazard.name}"

    def normalized_boundary(self) -> List[List[geometry.Point]]:
        return geometry.normalize_boundary(self.boundary)

    def contains(self, latitude: float, longitude: float) -> bool:
        point = geometry.Point(latitude, longitude)
        if geometry.point_within_circle(point, geometry.Point(float(self.center_latitude), float(self.center_longitude)), self.radius_meters):
            return True
        polygons = self.normalized_boundary()
        if polygons:
            return geometry.point_within_boundary(polygons, point)
        return False
