"""Transformer component: consolidates parser output, hydrates locations, and emits API-ready JSON."""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence

from difflib import SequenceMatcher

import requests

try:  # pragma: no cover - optional dependency is validated in runtime environments
    import googlemaps
except ImportError:  # pragma: no cover
    googlemaps = None  # type: ignore

LOGGER = logging.getLogger(__name__)

DEFAULT_INPUT_DIR = Path(__file__).resolve().parent / "output" / "json"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parent / "output" / "transformed"
HAZARD_SEVERITIES = {"low", "medium", "high"}
HAZARD_TYPES = {"animal", "event", "weather", "disease"}
LOCATION_TYPES = {"national park": "National Park", "region": "Region"}
FUZZY_MATCH_THRESHOLD = 0.6


def normalize_name(value: str) -> str:
    return value.strip().lower()


def to_float(value) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_boundary(raw_boundary) -> List[Dict[str, float]]:
    if not raw_boundary:
        return []

    def normalize_point(point) -> Optional[Dict[str, float]]:
        if isinstance(point, dict):
            lat = to_float(point.get("latitude") or point.get("lat"))
            lng = to_float(point.get("longitude") or point.get("lng") or point.get("lon"))
        elif isinstance(point, Sequence) and len(point) >= 2:
            lat = to_float(point[0])
            lng = to_float(point[1])
        else:
            lat = lng = None
        if lat is None or lng is None:
            return None
        return {"latitude": lat, "longitude": lng}

    points: List[Dict[str, float]] = []
    if isinstance(raw_boundary, list):
        for element in raw_boundary:
            if isinstance(element, list):
                for inner in element:
                    point = normalize_point(inner)
                    if point:
                        points.append(point)
            else:
                point = normalize_point(element)
                if point:
                    points.append(point)
    elif isinstance(raw_boundary, dict):
        coordinates = raw_boundary.get("coordinates")
        if isinstance(coordinates, list) and coordinates:
            if raw_boundary.get("type") == "Polygon":
                return normalize_boundary(coordinates[0])
            if raw_boundary.get("type") == "MultiPolygon":
                return normalize_boundary(coordinates[0][0])
    if len(points) < 3:
        return []
    if points[0] != points[-1]:  # Ensure closed polygon by repeating the first point at the end
        points.append(points[0])
    return points


def normalize_location_type(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    canonical = LOCATION_TYPES.get(value.strip().lower())
    return canonical or value


def normalize_hazard_choice(value: Optional[str], *, allowed: set[str]) -> Optional[str]:
    if not value:
        return None
    candidate = value.strip().lower()
    return candidate if candidate in allowed else None


def score_name(candidate: str, query: str) -> float:
    candidate_lower = candidate.lower()
    query_lower = query.lower()
    ratio = SequenceMatcher(None, candidate_lower, query_lower).ratio()
    if candidate_lower.startswith(query_lower):
        ratio = max(ratio, 0.95)
    elif query_lower in candidate_lower:
        ratio = max(ratio, 0.85)
    return ratio


@dataclass
class LocationPresentationAggregate:
    hazard_key: str
    boundary: List[Dict[str, float]] = field(default_factory=list)
    notes: set[str] = field(default_factory=set)

    def merge(self, payload: dict) -> None:
        boundary = normalize_boundary(payload.get("boundary"))
        if boundary and not self.boundary:
            self.boundary = boundary
        note = payload.get("notes") or payload.get("description")
        if isinstance(note, str) and note.strip():
            self.notes.add(note.strip())

    def to_dict(self, hazard: "AggregatedHazard") -> dict:
        data: Dict[str, object] = {
            "hazard_id": hazard.id,
            "hazard_name": hazard.name,
        }
        if self.boundary:
            data["boundary"] = self.boundary
        if self.notes:
            notes = sorted(self.notes)
            data["notes"] = notes if len(notes) > 1 else notes[0]
        if hazard.severity:
            data["hazard_severity"] = hazard.severity
        if hazard.type:
            data["hazard_type"] = hazard.type
        return data


@dataclass
class AggregatedLocation:
    name: str
    type: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    description: Optional[str] = None
    image: Optional[str] = None
    google_maps_id: Optional[str] = None
    boundary: List[Dict[str, float]] = field(default_factory=list)
    id: Optional[str] = None
    presentations: Dict[str, LocationPresentationAggregate] = field(default_factory=dict)

    def merge(self, payload: dict) -> None:
        self.type = self.type or normalize_location_type(payload.get("type"))
        self.latitude = self.latitude if self.latitude is not None else to_float(payload.get("latitude"))
        self.longitude = self.longitude if self.longitude is not None else to_float(payload.get("longitude"))
        description = payload.get("description")
        if isinstance(description, str) and description.strip() and not self.description:
            self.description = description.strip()
        image = payload.get("image")
        if isinstance(image, str) and image.strip() and not self.image:
            self.image = image.strip()
        google_maps_id = payload.get("google_maps_id")
        if not google_maps_id:
            google_maps_id = payload.get("googleMapsId")
        if isinstance(google_maps_id, str) and google_maps_id.strip() and not self.google_maps_id:
            self.google_maps_id = google_maps_id.strip()
        boundary = normalize_boundary(payload.get("boundary"))
        if boundary and not self.boundary:
            self.boundary = boundary

    def merge_presentation(self, hazard_key: str, payload: dict) -> None:
        presentation = self.presentations.setdefault(hazard_key, LocationPresentationAggregate(hazard_key=hazard_key))
        presentation.merge(payload)

    def merge_api_payload(self, payload: dict) -> None:
        self.merge(payload)
        if payload.get("id") is not None:
            self.id = str(payload["id"])

    def to_dict(self, hazards: Dict[str, "AggregatedHazard"]) -> dict:
        data: Dict[str, object] = {
            "id": self.id,
            "name": self.name,
        }
        if self.type:
            data["type"] = self.type
        if self.latitude is not None:
            data["latitude"] = self.latitude
        if self.longitude is not None:
            data["longitude"] = self.longitude
        if self.description:
            data["description"] = self.description
        if self.image:
            data["image"] = self.image
        if self.google_maps_id:
            data["google_maps_id"] = self.google_maps_id
        if self.boundary:
            data["boundary"] = self.boundary

        presentations = []
        for hazard_key, presentation in self.presentations.items():
            hazard = hazards.get(hazard_key)
            if not hazard or hazard.id is None:
                continue
            presentations.append(presentation.to_dict(hazard))
        data["presentations"] = sorted(presentations, key=lambda item: item["hazard_name"])
        return data


@dataclass
class AggregatedHazard:
    name: str
    severity: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    id: Optional[str] = None

    def merge(self, payload: dict) -> None:
        severity = normalize_hazard_choice(payload.get("severity"), allowed=HAZARD_SEVERITIES)
        hazard_type = normalize_hazard_choice(payload.get("type"), allowed=HAZARD_TYPES)
        self.severity = self.severity or severity
        self.type = self.type or hazard_type
        description = payload.get("description")
        if isinstance(description, str) and description.strip() and not self.description:
            self.description = description.strip()

    def merge_api_payload(self, payload: dict) -> None:
        self.merge(payload)
        if payload.get("id") is not None:
            self.id = str(payload["id"])

    def to_dict(self) -> dict:
        data: Dict[str, object] = {
            "id": self.id,
            "name": self.name,
        }
        if self.severity:
            data["severity"] = self.severity
        if self.type:
            data["type"] = self.type
        if self.description:
            data["description"] = self.description
        return data


class ElkApiClient:
    def __init__(self, base_url: str, timeout: float = 5.0, session: Optional[requests.Session] = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or requests.Session()
        self._location_cache: Dict[str, Optional[dict]] = {}
        self._hazard_cache: Dict[str, Optional[dict]] = {}

    def _choose_best_match(self, name: str, candidates: Sequence[dict]) -> Optional[dict]:
        best: Optional[dict] = None
        best_score = 0.0
        for candidate in candidates:
            candidate_name = candidate.get("name")
            if not isinstance(candidate_name, str):
                continue
            score = score_name(candidate_name, name)
            if score > best_score:
                best_score = score
                best = candidate
        if best_score >= FUZZY_MATCH_THRESHOLD:
            return best
        return None

    def find_location(self, name: str) -> Optional[dict]:
        key = normalize_name(name)
        if key in self._location_cache:
            return self._location_cache[key]
        url = f"{self.base_url}/locations/"
        try:
            response = self.session.get(url, params={"q": name, "limit": 5}, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:  # pragma: no cover - network/runtime failures
            LOGGER.warning("Location search failed for '%s': %s", name, exc)
            self._location_cache[key] = None
            return None
        match = self._choose_best_match(name, data if isinstance(data, list) else [])
        self._location_cache[key] = match
        return match

    def find_hazard(self, name: str) -> Optional[dict]:
        key = normalize_name(name)
        if key in self._hazard_cache:
            return self._hazard_cache[key]
        url = f"{self.base_url}/hazards/search/"
        try:
            response = self.session.get(url, params={"q": name, "limit": 5}, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:  # pragma: no cover - network/runtime failures
            LOGGER.warning("Hazard search failed for '%s': %s", name, exc)
            self._hazard_cache[key] = None
            return None
        match = self._choose_best_match(name, data if isinstance(data, list) else [])
        self._hazard_cache[key] = match
        return match


class GoogleMapsHydrator:
    def __init__(self, api_key: Optional[str]) -> None:
        self.api_key = api_key.strip() if isinstance(api_key, str) and api_key.strip() else None
        self.client = None
        if self.api_key and googlemaps is not None:
            try:
                self.client = googlemaps.Client(key=self.api_key)
            except Exception as exc:  # pragma: no cover - depends on environment
                LOGGER.warning("Unable to initialise Google Maps client: %s", exc)
                self.client = None

    def hydrate(self, location: AggregatedLocation) -> None:
        if not self.client:
            return
        needs_geometry = location.latitude is None or location.longitude is None or not location.boundary
        needs_details = not location.image or not location.google_maps_id or needs_geometry
        if not needs_details:
            return

        try:
            result = self.client.places(query=location.name, language="en")
        except Exception as exc:  # pragma: no cover - network/runtime failures
            LOGGER.warning("Places search failed for '%s': %s", location.name, exc)
            return

        candidates = (result or {}).get("results", []) if isinstance(result, dict) else []
        if not candidates:
            return
        best = max(
            candidates,
            key=lambda item: score_name(str(item.get("name", "")), location.name),
        )

        geometry = best.get("geometry", {}) if isinstance(best, dict) else {}
        location_data = geometry.get("location", {})
        if isinstance(location_data, dict):
            lat = to_float(location_data.get("lat"))
            lng = to_float(location_data.get("lng"))
            if location.latitude is None and lat is not None:
                location.latitude = lat
            if location.longitude is None and lng is not None:
                location.longitude = lng
        place_id = best.get("place_id") if isinstance(best, dict) else None
        if isinstance(place_id, str) and place_id and not location.google_maps_id:
            location.google_maps_id = place_id
        photos = best.get("photos") if isinstance(best, dict) else None
        if isinstance(photos, list) and photos and not location.image:
            reference = photos[0].get("photo_reference") if isinstance(photos[0], dict) else None
            if isinstance(reference, str) and reference:
                location.image = (
                    "https://maps.googleapis.com/maps/api/place/photo"
                    f"?maxwidth=1600&photo_reference={reference}&key={self.api_key}"
                )

        if place_id and not location.boundary:
            self._hydrate_boundary(place_id, location)

    def _hydrate_boundary(self, place_id: str, location: AggregatedLocation) -> None:
        if not self.client:
            return
        try:
            results = self.client.geocode(place_id=place_id)
        except Exception as exc:  # pragma: no cover - network/runtime failures
            LOGGER.warning("Geocode lookup failed for '%s': %s", location.name, exc)
            return
        for entry in results or []:
            geometry = entry.get("geometry", {}) if isinstance(entry, dict) else {}
            bounds = geometry.get("bounds") if isinstance(geometry, dict) else None
            viewport = geometry.get("viewport") if isinstance(geometry, dict) else None
            polygon = self._rectangle_from_bounds(bounds) or self._rectangle_from_bounds(viewport)
            if polygon:
                location.boundary = polygon
                break

    def _rectangle_from_bounds(self, bounds: Optional[dict]) -> List[Dict[str, float]]:
        if not isinstance(bounds, dict):
            return []
        northeast = bounds.get("northeast")
        southwest = bounds.get("southwest")
        if not (isinstance(northeast, dict) and isinstance(southwest, dict)):
            return []
        ne_lat = to_float(northeast.get("lat"))
        ne_lng = to_float(northeast.get("lng"))
        sw_lat = to_float(southwest.get("lat"))
        sw_lng = to_float(southwest.get("lng"))
        if None in (ne_lat, ne_lng, sw_lat, sw_lng):
            return []
        northwest = {"latitude": ne_lat, "longitude": sw_lng}
        southeast = {"latitude": sw_lat, "longitude": ne_lng}
        polygon = [
            {"latitude": ne_lat, "longitude": ne_lng},
            northwest,
            {"latitude": sw_lat, "longitude": sw_lng},
            southeast,
        ]
        polygon.append(polygon[0])
        return polygon


class Transformer:
    def __init__(self, *, api_client: Optional[ElkApiClient], hydrator: GoogleMapsHydrator) -> None:
        self.api_client = api_client
        self.hydrator = hydrator
        self.locations: Dict[str, AggregatedLocation] = {}
        self.hazards: Dict[str, AggregatedHazard] = {}

    def transform_documents(self, documents: Iterable[dict]) -> dict:
        for document in documents:
            if isinstance(document, dict):
                self._ingest_document(document)

        self._attach_existing_ids()
        self._hydrate_locations()
        self._assign_new_ids()
        return self._build_output()

    def _ingest_document(self, document: dict) -> None:
        for location_payload in document.get("locations", []) or []:
            if not isinstance(location_payload, dict):
                continue
            key = normalize_name(location_payload.get("name", ""))
            if not key:
                continue
            location = self.locations.setdefault(key, AggregatedLocation(name=location_payload["name"].strip()))
            location.merge(location_payload)

        for hazard_payload in document.get("hazards", []) or []:
            if not isinstance(hazard_payload, dict):
                continue
            name = hazard_payload.get("name")
            if not isinstance(name, str) or not name.strip():
                continue
            hazard_key = normalize_name(name)
            hazard = self.hazards.setdefault(hazard_key, AggregatedHazard(name=name.strip()))
            hazard.merge(hazard_payload)

            presentations = hazard_payload.get("presentations") or []
            for presentation_payload in presentations:
                if not isinstance(presentation_payload, dict):
                    continue
                location_name = presentation_payload.get("location")
                if not isinstance(location_name, str) or not location_name.strip():
                    continue
                location_key = normalize_name(location_name)
                location = self.locations.setdefault(
                    location_key,
                    AggregatedLocation(name=location_name.strip()),
                )
                location.merge_presentation(hazard_key, presentation_payload)

    def _attach_existing_ids(self) -> None:
        if not self.api_client:
            return
        for location in self.locations.values():
            match = self.api_client.find_location(location.name)
            if match:
                location.merge_api_payload(match)
        for hazard in self.hazards.values():
            match = self.api_client.find_hazard(hazard.name)
            if match:
                hazard.merge_api_payload(match)

    def _hydrate_locations(self) -> None:
        for location in self.locations.values():
            self.hydrator.hydrate(location)

    def _assign_new_ids(self) -> None:
        next_location_id = 1
        for key in sorted(self.locations.keys()):
            location = self.locations[key]
            if location.id is None:
                location.id = f"new-location-{next_location_id}"
                next_location_id += 1
        next_hazard_id = 1
        for key in sorted(self.hazards.keys()):
            hazard = self.hazards[key]
            if hazard.id is None:
                hazard.id = f"new-hazard-{next_hazard_id}"
                next_hazard_id += 1

    def _build_output(self) -> dict:
        locations_payload = [
            location.to_dict(self.hazards)
            for key, location in sorted(self.locations.items(), key=lambda item: item[1].name.lower())
        ]
        hazards_payload = [
            hazard.to_dict()
            for key, hazard in sorted(self.hazards.items(), key=lambda item: item[1].name.lower())
        ]
        return {
            "locations": locations_payload,
            "hazards": hazards_payload,
        }


def load_documents(input_dir: Path) -> List[dict]:
    documents: List[dict] = []
    if not input_dir.exists():
        LOGGER.warning("Input directory %s does not exist", input_dir)
        return documents
    for path in sorted(input_dir.glob("*.json")):
        try:
            content = path.read_text(encoding="utf-8")
            document = json.loads(content)
            if isinstance(document, dict):
                documents.append(document)
            else:
                LOGGER.warning("Ignoring non-object JSON in %s", path)
        except json.JSONDecodeError as exc:
            LOGGER.error("Failed to decode JSON from %s: %s", path, exc)
        except OSError as exc:
            LOGGER.error("Failed to read %s: %s", path, exc)
    return documents


def write_output(output_dir: Path, payload: dict) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_path = output_dir / f"{timestamp}.json"
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return output_path


def parse_args(argv: Optional[Sequence[str]]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Transform parser output into consolidated Elk data.")
    parser.add_argument("--input-dir", type=Path, default=DEFAULT_INPUT_DIR, help="Directory containing parser JSON output.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where the consolidated JSON should be written.",
    )
    parser.add_argument(
        "--api-base-url",
        default=os.getenv("ELK_API_BASE_URL"),
        help="Base URL for the Elk API. When omitted, API lookups are skipped.",
    )
    parser.add_argument(
        "--api-timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds for Elk API requests.",
    )
    parser.add_argument(
        "--google-maps-key",
        default=os.getenv("GOOGLE_MAPS_API_KEY"),
        help="Google Maps API key. When omitted, hydration is skipped.",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging output.")
    return parser.parse_args(argv)


def configure_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(levelname)s %(message)s")


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    configure_logging(args.verbose)

    documents = load_documents(Path(args.input_dir))
    LOGGER.info("Loaded %d document(s) for transformation", len(documents))

    api_client = ElkApiClient(args.api_base_url, timeout=args.api_timeout) if args.api_base_url else None
    hydrator = GoogleMapsHydrator(args.google_maps_key)
    transformer = Transformer(api_client=api_client, hydrator=hydrator)
    payload = transformer.transform_documents(documents)
    output_path = write_output(Path(args.output_dir), payload)
    LOGGER.info("Wrote transformed data to %s", output_path)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
