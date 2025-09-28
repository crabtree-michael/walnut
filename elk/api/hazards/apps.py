from __future__ import annotations

from django.apps import AppConfig


class HazardsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hazards"
    verbose_name = "Hazard Management"
