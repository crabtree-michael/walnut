from __future__ import annotations

from typing import Any, Dict

from rest_framework import serializers

from . import geometry
from .models import Hazard, HazardPresentation, Location, Tip


class TipSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tip
        fields = ["id", "name", "description"]


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = ["id", "name", "type", "latitude", "longitude", "description", "image"]


class HazardPresentationReadSerializer(serializers.ModelSerializer):
    location = LocationSerializer(read_only=True)
    center_latitude = serializers.FloatField(read_only=True)
    center_longitude = serializers.FloatField(read_only=True)

    class Meta:
        model = HazardPresentation
        fields = [
            "id",
            "boundary",
            "notes",
            "location",
            "center_latitude",
            "center_longitude",
            "radius_meters",
        ]


class HazardSerializer(serializers.ModelSerializer):
    tips = TipSerializer(many=True, read_only=True)
    presentations = HazardPresentationReadSerializer(many=True, read_only=True)

    class Meta:
        model = Hazard
        fields = [
            "id",
            "name",
            "severity",
            "type",
            "description",
            "tips",
            "presentations",
        ]


class HazardCreateSerializer(serializers.ModelSerializer):
    tip_ids = serializers.PrimaryKeyRelatedField(
        queryset=Tip.objects.all(), many=True, required=False, write_only=True
    )

    class Meta:
        model = Hazard
        fields = ["name", "severity", "type", "description", "tip_ids"]

    def create(self, validated_data: Dict[str, Any]) -> Hazard:
        tips = validated_data.pop("tip_ids", [])
        hazard = super().create(validated_data)
        hazard.tips.set(tips)
        return hazard


class HazardPresentationCreateSerializer(serializers.ModelSerializer):
    latitude = serializers.FloatField(write_only=True)
    longitude = serializers.FloatField(write_only=True)
    radius_meters = serializers.IntegerField(write_only=True, min_value=1)
    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(), source="location", allow_null=True, required=False
    )

    class Meta:
        model = HazardPresentation
        fields = ["latitude", "longitude", "radius_meters", "notes", "location_id"]

    def validate(self, attrs: Dict[str, Any]) -> Dict[str, Any]:
        radius = attrs.get("radius_meters", 0)
        if radius <= 0:
            raise serializers.ValidationError({"radius_meters": "Radius must be greater than zero."})
        return attrs

    def create(self, validated_data: Dict[str, Any]) -> HazardPresentation:
        latitude = validated_data.pop("latitude")
        longitude = validated_data.pop("longitude")
        radius_meters = validated_data.pop("radius_meters")
        center = geometry.Point(latitude, longitude)
        boundary = [
            {"latitude": point.latitude, "longitude": point.longitude}
            for point in geometry.circle_boundary(center, radius_meters)
        ]
        return HazardPresentation.objects.create(
            center_latitude=latitude,
            center_longitude=longitude,
            radius_meters=radius_meters,
            boundary=boundary,
            **validated_data,
        )
