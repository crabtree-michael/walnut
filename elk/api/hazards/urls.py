from __future__ import annotations

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import HazardViewSet

router = DefaultRouter()
router.register(r"hazards", HazardViewSet, basename="hazard")

urlpatterns = [
    path("", include(router.urls)),
]
