from __future__ import annotations

import sys
import types
import unittest
from dataclasses import dataclass
from typing import Dict, Optional

# Provide lightweight stubs so the transformer module does not require third-party
# dependencies to be installed in the unit-test environment.
requests_stub = types.ModuleType("requests")


class _StubSession:
    def __init__(self, *args, **kwargs):  # pragma: no cover - trivial
        pass


requests_stub.Session = _StubSession  # type: ignore[attr-defined]
sys.modules.setdefault("requests", requests_stub)

googlemaps_stub = types.ModuleType("googlemaps")


class _StubGoogleClient:
    def __init__(self, *args, **kwargs):  # pragma: no cover - trivial
        raise RuntimeError("Google Maps client should not be instantiated in unit tests")


googlemaps_stub.Client = _StubGoogleClient  # type: ignore[attr-defined]
sys.modules.setdefault("googlemaps", googlemaps_stub)

from scraper.transformer import Transformer, normalize_name


@dataclass
class StubApiClient:
    locations: Dict[str, dict]
    hazards: Dict[str, dict]

    def find_location(self, name: str) -> Optional[dict]:
        return self.locations.get(normalize_name(name))

    def find_hazard(self, name: str) -> Optional[dict]:
        return self.hazards.get(normalize_name(name))


class StubHydrator:
    def __init__(self) -> None:
        self.calls = []

    def hydrate(self, location) -> None:  # pragma: no cover - invoked via transformer
        self.calls.append(location.name)
        if not location.boundary:
            location.boundary = [
                {"latitude": 40.0, "longitude": -105.7},
                {"latitude": 40.0, "longitude": -105.6},
                {"latitude": 39.9, "longitude": -105.6},
                {"latitude": 39.9, "longitude": -105.7},
                {"latitude": 40.0, "longitude": -105.7},
            ]
        if not location.image:
            location.image = "https://example.com/placeholder.jpg"


class TransformerTests(unittest.TestCase):
    def test_transformer_consolidates_and_hydrates(self) -> None:
        api_client = StubApiClient(
            locations={
                normalize_name("Rocky Park"): {
                    "id": 42,
                    "name": "Rocky Park",
                    "latitude": 40.123,
                    "longitude": -105.654,
                }
            },
            hazards={
                normalize_name("Bear Activity"): {
                    "id": 7,
                    "name": "Bear Activity",
                    "description": "Existing description",
                    "severity": "high",
                    "type": "animal",
                }
            },
        )
        hydrator = StubHydrator()
        documents = [
            {
                "locations": [
                    {
                        "name": "Rocky Park",
                        "type": "National Park",
                    }
                ],
                "hazards": [
                    {
                        "name": "Bear Activity",
                        "severity": "high",
                        "type": "animal",
                        "presentations": [
                            {"location": "Rocky Park", "notes": "Stay alert."},
                        ],
                    }
                ],
            },
            {
                "hazards": [
                    {
                        "name": "Bear Activity",
                        "presentations": [
                            {"location": "Rocky Park", "notes": "Hike in groups."},
                        ],
                    }
                ],
            },
        ]

        transformer = Transformer(api_client=api_client, hydrator=hydrator)
        payload = transformer.transform_documents(documents)

        hazard_payload = payload["hazards"][0]
        self.assertEqual(hazard_payload["id"], "7")
        self.assertEqual(hazard_payload["description"], "Existing description")

        location_payload = payload["locations"][0]
        self.assertEqual(location_payload["id"], "42")
        self.assertAlmostEqual(location_payload["latitude"], 40.123)
        self.assertIn("presentations", location_payload)
        presentation = location_payload["presentations"][0]
        self.assertEqual(presentation["hazard_id"], "7")
        self.assertEqual(presentation["notes"], ["Hike in groups.", "Stay alert."])
        self.assertEqual(hydrator.calls, ["Rocky Park"])

    def test_assigns_new_ids_when_api_not_available(self) -> None:
        hydrator = StubHydrator()
        documents = [
            {
                "locations": [
                    {
                        "name": "Sunset Region",
                        "type": "Region",
                    }
                ],
                "hazards": [
                    {
                        "name": "Flooding",
                        "severity": "medium",
                        "type": "weather",
                        "presentations": [
                            {"location": "Sunset Region", "notes": "Avoid low areas."},
                        ],
                    }
                ],
            }
        ]

        transformer = Transformer(api_client=None, hydrator=hydrator)
        payload = transformer.transform_documents(documents)

        hazard_payload = payload["hazards"][0]
        self.assertTrue(hazard_payload["id"].startswith("new-hazard-"))
        location_payload = payload["locations"][0]
        self.assertTrue(location_payload["id"].startswith("new-location-"))
        self.assertEqual(
            location_payload["presentations"][0]["hazard_id"],
            hazard_payload["id"],
        )


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
