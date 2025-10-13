from __future__ import annotations

from collections import defaultdict
from difflib import SequenceMatcher
from typing import Dict, Iterable, List

from django.db.models import Prefetch
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from .models import Hazard, HazardPresentation, Location, Tip
from .serializers import (
    HazardCreateSerializer,
    HazardPresentationCreateSerializer,
    HazardPresentationReadSerializer,
    HazardSerializer,
    HazardSearchSerializer,
    LocationSerializer,
    TipSerializer,
)

FUZZY_MIN_SCORE = 0.35
DEFAULT_SEARCH_LIMIT = 10
MAX_SEARCH_LIMIT = 50


def _extract_query_param(request) -> str:
    raw_query = request.query_params.get("q")
    if raw_query is None or not raw_query.strip():
        raise ValidationError({"q": "Query parameter 'q' is required."})
    return raw_query.strip()


def _extract_limit_param(request) -> int:
    raw_limit = request.query_params.get("limit")
    if raw_limit is None:
        return DEFAULT_SEARCH_LIMIT
    try:
        limit_value = int(raw_limit)
    except (TypeError, ValueError) as exc:
        raise ValidationError({"limit": "Limit must be an integer value."}) from exc
    if limit_value <= 0:
        raise ValidationError({"limit": "Limit must be greater than zero."})
    return min(limit_value, MAX_SEARCH_LIMIT)


def _score_name(candidate: str, query: str) -> float:
    candidate_lower = candidate.lower()
    query_lower = query.lower()
    if not candidate_lower:
        return 0.0
    ratio = SequenceMatcher(None, candidate_lower, query_lower).ratio()
    if candidate_lower.startswith(query_lower):
        ratio = max(ratio, 0.95)
    elif query_lower in candidate_lower:
        ratio = max(ratio, 0.85)
    return ratio


def _fuzzy_rank(queryset: Iterable, query: str, *, limit: int) -> List:
    candidates = list(queryset)
    if not candidates:
        return []

    scored = [(_score_name(getattr(candidate, "name", ""), query), candidate) for candidate in candidates]
    significant = [entry for entry in scored if entry[0] >= FUZZY_MIN_SCORE]
    pool = significant or scored
    sorted_pool = sorted(pool, key=lambda item: (-item[0], getattr(item[1], "name", "")))
    return [candidate for _score, candidate in sorted_pool[:limit]]


class LocationSearchViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly]
    serializer_class = LocationSerializer

    def get_queryset(self):
        return (
            Location.objects.all()
            .only(
                "id",
                "name",
                "type",
                "latitude",
                "longitude",
                "description",
                "image",
                "google_maps_id",
                "boundary",
            )
            .order_by("name")
        )

    def list(self, request, *args, **kwargs):
        query = _extract_query_param(request)
        limit = _extract_limit_param(request)
        results = _fuzzy_rank(self.get_queryset(), query, limit=limit)
        serializer = self.get_serializer(results, many=True)
        return Response(serializer.data)


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
        if self.action == "search":
            return HazardSearchSerializer
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

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request, *args, **kwargs):
        query = _extract_query_param(request)
        limit = _extract_limit_param(request)
        queryset = (
            Hazard.objects.all()
            .only("id", "name", "severity", "type", "description")
            .order_by("name")
        )
        results = _fuzzy_rank(queryset, query, limit=limit)
        serializer = HazardSearchSerializer(results, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
