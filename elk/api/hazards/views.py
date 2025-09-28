from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

from django.db.models import Prefetch
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Hazard, HazardPresentation, Tip
from .serializers import (
    HazardCreateSerializer,
    HazardPresentationCreateSerializer,
    HazardPresentationReadSerializer,
    HazardSerializer,
    TipSerializer,
)


class HazardViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    queryset = (
        Hazard.objects.all()
        .prefetch_related(
            "tips",
            Prefetch("presentations", queryset=HazardPresentation.objects.select_related("location")),
        )
        .order_by("name")
    )
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.action == "create":
            return HazardCreateSerializer
        if self.action == "add_presentation":
            return HazardPresentationCreateSerializer
        return HazardSerializer

    def list(self, request, *args, **kwargs):
        latitude = request.query_params.get("latitude")
        longitude = request.query_params.get("longitude")
        if latitude is None or longitude is None:
            raise ValidationError("Both latitude and longitude query parameters are required.")
        try:
            latitude_value = float(latitude)
            longitude_value = float(longitude)
        except ValueError as exc:
            raise ValidationError("Latitude and longitude must be numeric.") from exc

        matched_presentations: Dict[int, List[HazardPresentation]] = defaultdict(list)
        for presentation in HazardPresentation.objects.select_related("hazard", "location").all():
            try:
                if presentation.contains(latitude_value, longitude_value):
                    matched_presentations[presentation.hazard_id].append(presentation)
            except ValueError as exc:
                # Invalid boundary data should not block the entire query
                continue

        hazards = (
            Hazard.objects.filter(id__in=matched_presentations.keys())
            .prefetch_related("tips")
        )

        response_payload = []
        for hazard in hazards:
            presentations = matched_presentations.get(hazard.id, [])
            payload = {
                "id": hazard.id,
                "name": hazard.name,
                "severity": hazard.severity,
                "type": hazard.type,
                "description": hazard.description,
                "tips": TipSerializer(hazard.tips.all(), many=True).data,
                "presentations": HazardPresentationReadSerializer(presentations, many=True).data,
            }
            response_payload.append(payload)

        return Response(response_payload)

    def create(self, request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            raise PermissionDenied("Only admin users may add hazards.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        hazard = serializer.save()
        read_serializer = HazardSerializer(hazard, context=self.get_serializer_context())
        headers = self.get_success_headers(read_serializer.data)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=["post"], url_path="presentations")
    def add_presentation(self, request, pk=None):
        if not request.user.is_authenticated or not request.user.is_staff:
            raise PermissionDenied("Only admin users may add hazard presentations.")
        hazard = self.get_object()
        serializer = HazardPresentationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        presentation = serializer.save(hazard=hazard)
        output = HazardPresentationReadSerializer(presentation)
        return Response(output.data, status=status.HTTP_201_CREATED)
