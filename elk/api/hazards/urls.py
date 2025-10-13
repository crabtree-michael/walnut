from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HazardViewSet, LocationSearchViewSet

router = DefaultRouter()
router.register(r"hazards", HazardViewSet, basename="hazard")
router.register(r"locations", LocationSearchViewSet, basename="location")

urlpatterns = [
    path("", include(router.urls)),
]
