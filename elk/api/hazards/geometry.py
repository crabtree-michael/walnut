from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence
import math


@dataclass(frozen=True)
class Point:
    latitude: float
    longitude: float


def _looks_like_point(raw: object) -> bool:
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        return True
    if isinstance(raw, dict) and {"latitude", "longitude"}.issubset(raw.keys()):
        return True
    return False


def _coerce_point(raw: object) -> Point:
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        lat, lng = raw
        return Point(float(lat), float(lng))
    if isinstance(raw, dict):
        try:
            return Point(float(raw["latitude"]), float(raw["longitude"]))
        except KeyError as exc:  # pragma: no cover - defensive
            raise ValueError("Boundary points must include latitude and longitude keys") from exc
    raise ValueError("Unsupported boundary coordinate format")



EARTH_RADIUS_METERS = 6_371_000


def circle_boundary(center: Point, radius_meters: float, segments: int = 32) -> List[Point]:
    if radius_meters <= 0:
        raise ValueError("Radius must be greater than zero")
    if segments < 3:
        raise ValueError("Circle boundary requires at least three segments")

    angular_distance = radius_meters / EARTH_RADIUS_METERS
    center_lat = math.radians(center.latitude)
    center_lng = math.radians(center.longitude)

    polygon: List[Point] = []
    for step in range(segments):
        bearing = 2 * math.pi * step / segments
        lat = math.asin(
            math.sin(center_lat) * math.cos(angular_distance)
            + math.cos(center_lat) * math.sin(angular_distance) * math.cos(bearing)
        )
        lng = center_lng + math.atan2(
            math.sin(bearing) * math.sin(angular_distance) * math.cos(center_lat),
            math.cos(angular_distance) - math.sin(center_lat) * math.sin(lat)
        )
        polygon.append(Point(math.degrees(lat), math.degrees(lng)))

    return polygon


def point_within_circle(point: Point, center: Point, radius_meters: float) -> bool:
    if radius_meters <= 0:
        return False

    lat1, lon1 = math.radians(point.latitude), math.radians(point.longitude)
    lat2, lon2 = math.radians(center.latitude), math.radians(center.longitude)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(delta_lon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance = EARTH_RADIUS_METERS * c
    return distance <= radius_meters

def normalize_boundary(raw_boundary: object) -> List[List[Point]]:
    """Normalize JSON boundary structures to a list of polygons of Points."""
    if raw_boundary is None:
        return []
    boundary: List[List[Point]] = []

    def add_polygon(raw_polygon: Iterable[object]) -> None:
        polygon: List[Point] = [_coerce_point(p) for p in raw_polygon]
        if len(polygon) < 3:
            raise ValueError("Boundary polygons require at least three points")
        boundary.append(polygon)

    if isinstance(raw_boundary, dict):
        coordinates = raw_boundary.get("coordinates")
        boundary_type = raw_boundary.get("type")
        if not coordinates:
            raise ValueError("Boundary coordinate list is empty")
        if boundary_type == "Polygon":
            add_polygon(coordinates[0] if coordinates and not _looks_like_point(coordinates[0]) else coordinates)
        elif boundary_type == "MultiPolygon":
            for polygon in coordinates:
                add_polygon(polygon[0] if polygon and not _looks_like_point(polygon[0]) else polygon)
        else:
            raise ValueError("Unrecognised boundary dict structure")
    elif isinstance(raw_boundary, (list, tuple)):
        if not raw_boundary:
            return []
        if all(_looks_like_point(item) for item in raw_boundary):
            add_polygon(raw_boundary)
        else:
            for polygon in raw_boundary:
                if not isinstance(polygon, (list, tuple)):
                    raise ValueError("Unsupported boundary polygon format")
                add_polygon(polygon)
    else:  # pragma: no cover - defensive
        raise ValueError("Unsupported boundary type")

    return boundary


def point_within_boundary(polygons: Sequence[Sequence[Point]], point: Point) -> bool:
    for polygon in polygons:
        if _point_in_polygon(polygon, point):
            return True
    return False


def _point_in_polygon(polygon: Sequence[Point], point: Point) -> bool:
    """Ray casting algorithm for point-in-polygon."""
    inside = False
    if not polygon:
        return False
    x = point.longitude
    y = point.latitude
    num_vertices = len(polygon)
    for i in range(num_vertices):
        j = (i - 1) % num_vertices
        xi, yi = polygon[i].longitude, polygon[i].latitude
        xj, yj = polygon[j].longitude, polygon[j].latitude
        if (yi > y) != (yj > y):
            slope = (xj - xi) / (yj - yi + 1e-12)
            intersect_x = slope * (y - yi) + xi
            if intersect_x > x:
                inside = not inside
    return inside
