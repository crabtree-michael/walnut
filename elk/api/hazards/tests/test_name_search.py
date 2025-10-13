from __future__ import annotations

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from hazards.models import Hazard, HazardSeverity, HazardType, Location


class LocationNameSearchAPITests(APITestCase):
    def setUp(self):
        self.location = Location.objects.create(
            name="Rocky Mountain National Park",
            type="National Park",
            latitude=40.3428,
            longitude=-105.6836,
            description="Trails and wildlife encounters.",
            image="https://example.com/rocky.jpg",
            boundary=[{"latitude": 40.34, "longitude": -105.68}],
        )
        Location.objects.create(
            name="Yosemite National Park",
            type="National Park",
            latitude=37.8651,
            longitude=-119.5383,
            boundary=[{"latitude": 37.86, "longitude": -119.53}],
        )

    def test_requires_query_parameter(self):
        url = reverse("location-list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("q", response.json())

    def test_returns_fuzzy_matches(self):
        url = reverse("location-list")
        response = self.client.get(url, {"q": "rokky"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertGreaterEqual(len(payload), 1)
        self.assertEqual(payload[0]["id"], str(self.location.id))
        self.assertIn("boundary", payload[0])


class HazardNameSearchAPITests(APITestCase):
    def setUp(self):
        self.hazard = Hazard.objects.create(
            name="Bear Activity",
            severity=HazardSeverity.HIGH,
            type=HazardType.ANIMAL,
            description="Bears observed near campsites.",
        )
        Hazard.objects.create(
            name="Avalanche Risk",
            severity=HazardSeverity.MEDIUM,
            type=HazardType.WEATHER,
        )

    def test_requires_query_parameter(self):
        url = reverse("hazard-search")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("q", response.json())

    def test_returns_fuzzy_matches(self):
        url = reverse("hazard-search")
        response = self.client.get(url, {"q": "berr"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        payload = response.json()
        self.assertTrue(any(item["id"] == str(self.hazard.id) for item in payload))

    def test_limit_parameter(self):
        Hazard.objects.create(
            name="Bear Advisory",
            severity=HazardSeverity.LOW,
            type=HazardType.ANIMAL,
        )
        url = reverse("hazard-search")
        response = self.client.get(url, {"q": "bear", "limit": 1})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.json()), 1)
