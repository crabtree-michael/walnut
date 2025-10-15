from __future__ import annotations

from typing import Iterable

from django.http import HttpRequest, JsonResponse
from django.views import View

from .models import Expert, Speciality


def _parse_specialities(raw_values: Iterable[str]) -> tuple[list[str], list[str]]:
    """Normalize specialities into canonical enum values."""
    allowed = {choice.value for choice in Speciality}
    selected: list[str] = []
    invalid: list[str] = []

    for value in raw_values:
        if not value:
            continue
        # Allow comma-separated values in addition to repeated query params
        parts = [part.strip() for part in value.split(",") if part.strip()]
        for part in parts:
            if part in allowed:
                if part not in selected:
                    selected.append(part)
            else:
                invalid.append(part)

    return selected, invalid


class ExpertSearchView(View):
    """Provide read-only access to experts, filtered by specialities."""

    def get(self, request: HttpRequest) -> JsonResponse:
        requested_values = request.GET.getlist("speciality")
        requested_values.extend(request.GET.getlist("specialities"))
        selected, invalid = _parse_specialities(requested_values)

        if invalid:
            return JsonResponse(
                {
                    "error": "invalid_specialities",
                    "invalid": invalid,
                },
                status=400,
            )

        experts = Expert.objects.all()
        if selected:
            experts = experts.filter(specialities__contains=selected)

        payload = {
            "experts": [
                {
                    "id": str(expert.id),
                    "name": expert.name,
                    "photo": expert.photo,
                    "expertise": expert.expertise,
                    "specialities": expert.specialities,
                    "availability": {
                        "days": expert.availability_days,
                        "hours": expert.availability_hours,
                    },
                }
                for expert in experts
            ]
        }
        return JsonResponse(payload)
