from __future__ import annotations

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from hazards import geometry
from hazards.models import Hazard, HazardPresentation, HazardSeverity, HazardType, Location, Tip


def circle_boundary(lat: float, lng: float, radius_meters: float):
    center = geometry.Point(lat, lng)
    return [
        {"latitude": point.latitude, "longitude": point.longitude}
        for point in geometry.circle_boundary(center, radius_meters)
    ]


def create_presentation(*, hazard, location=None, lat, lng, radius):
    return HazardPresentation.objects.create(
        hazard=hazard,
        location=location,
        center_latitude=lat,
        center_longitude=lng,
        radius_meters=radius,
        boundary=circle_boundary(lat, lng, radius),
    )


class HazardSearchTests(APITestCase):
    def setUp(self):
        self.hazard = Hazard.objects.create(
            name="Bear",
            severity=HazardSeverity.HIGH,
            type=HazardType.ANIMAL,
            description="Black bears active in the area.",
        )
        tip = Tip.objects.create(name="Bear Spray", description="Carry bear spray at all times.")
        tip.hazards.add(self.hazard)
        self.location = Location.objects.create(
            name="Rocky Mountain National Park",
            type="National Park",
            latitude=40.3428,
            longitude=-105.6836,
        )
        create_presentation(
            hazard=self.hazard,
            location=self.location,
            lat=40.34,
            lng=-105.68,
            radius=5_000,
        )

        self.non_matching_hazard = Hazard.objects.create(
            name="Avalanche",
            severity=HazardSeverity.MEDIUM,
            type=HazardType.WEATHER,
        )
        create_presentation(
            hazard=self.non_matching_hazard,
            lat=38.5,
            lng=-106.0,
            radius=1_000,
        )

    def test_requires_latitude_and_longitude(self):
        url = reverse("hazard-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_hazards_containing_point(self):
        url = reverse("hazard-list")
        response = self.client.get(url, {"latitude": 40.34, "longitude": -105.68})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
        hazard_payload = response.json()[0]
        self.assertEqual(hazard_payload["id"], self.hazard.id)
        self.assertEqual(len(hazard_payload["tips"]), 1)
        self.assertEqual(len(hazard_payload["presentations"]), 1)
        presentation = hazard_payload["presentations"][0]
        self.assertEqual(presentation["location"]["id"], self.location.id)

    def test_admin_can_create_hazard_and_presentation(self):
        url = reverse("hazard-list")
        payload = {
            "name": "Flood",
            "severity": HazardSeverity.MEDIUM,
            "type": HazardType.WEATHER,
            "description": "Seasonal flooding expected.",
        }
        create_response = self.client.post(url, payload, format="json")
        self.assertEqual(create_response.status_code, status.HTTP_403_FORBIDDEN)

        user_model = get_user_model()
        admin_user = user_model.objects.create_user(
            username="admin",
            email="admin@example.com",
            password="password",
            is_staff=True,
        )
        self.client.force_authenticate(user=admin_user)
        create_response = self.client.post(url, payload, format="json")
        self.assertEqual(create_response.status_code, status.HTTP_201_CREATED)
        hazard_id = create_response.json()["id"]

        presentation_url = reverse("hazard-add-presentation", args=[hazard_id])
        presentation_payload = {
            "latitude": 39.74,
            "longitude": -104.99,
            "radius_meters": 2_000,
            "notes": "Downtown area.",
        }
        presentation_response = self.client.post(presentation_url, presentation_payload, format="json")
        self.assertEqual(presentation_response.status_code, status.HTTP_201_CREATED)
        payload = presentation_response.json()
        self.assertIn("radius_meters", payload)
        self.assertEqual(payload["radius_meters"], 2000)
