import json
import math
import os
from typing import Any
from urllib.parse import quote

import httpx
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

TMAP_APP_KEY = os.getenv("TMAP_APP_KEY", "").strip()

TMAP_WALKING_URL = (
    "https://apis.openapi.sk.com/tmap/routes/pedestrian"
)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
GEOJSON_PATH = os.path.join(DATA_DIR, "성남시_보행망.geojson")


_seongnam_walking_network_cache: dict[str, Any] | None = None
_seongnam_walking_network_load_attempted = False


def load_seongnam_walking_network():
    """
    성남시 보행망 GeoJSON 데이터를 로드한다.

    51MB/58,364개 feature짜리 정적 파일이라 매 호출마다 다시 읽고
    파싱하면 호출당 약 700ms가 낭비된다(실측). 실시간으로 바뀌는
    데이터가 아니므로 프로세스 생애주기 동안 한 번만 읽어 캐싱한다.
    """

    global _seongnam_walking_network_cache
    global _seongnam_walking_network_load_attempted

    if _seongnam_walking_network_load_attempted:
        return _seongnam_walking_network_cache

    _seongnam_walking_network_load_attempted = True

    if os.path.exists(GEOJSON_PATH):
        try:
            with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
                content = f.read()
                _seongnam_walking_network_cache = json.loads(content, strict=False)
        except Exception as e:
            print(f"[경고] GeoJSON 로드 중 오류 발생: {e}")
            _seongnam_walking_network_cache = None
    else:
        _seongnam_walking_network_cache = None

    return _seongnam_walking_network_cache


def calculate_distance_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """두 위도/경도 좌표 사이의 실제 직선 거리(m) 계산 (Haversine)"""
    R = 6371000
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


async def get_walking_route(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
    start_name: str = "출발지",
    end_name: str = "도착지",
    avoid_stairs: bool = False,
) -> dict[str, Any]:

    if not TMAP_APP_KEY:
        raise RuntimeError("TMAP_APP_KEY가 없습니다. .env 파일을 확인하세요.")

    search_option = "30" if avoid_stairs else "0"

    headers = {
        "appKey": TMAP_APP_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "startX": str(start_x),
        "startY": str(start_y),
        "endX": str(end_x),
        "endY": str(end_y),
        "startName": quote(start_name),
        "endName": quote(end_name),
        "reqCoordType": "WGS84GEO",
        "resCoordType": "WGS84GEO",
        "searchOption": search_option,
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                TMAP_WALKING_URL,
                params={"version": "1"},
                headers=headers,
                json=payload,
            )

        response.raise_for_status()
        raw_data = json.loads(response.text, strict=False)
        return simplify_walking_route(raw_data)

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail={
                "message": "TMAP 보행 경로 API 호출 실패",
                "tmap_response": exc.response.text,
            },
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail=f"TMAP API 서버 연결 실패: {exc}",
        ) from exc


def simplify_walking_route(data: dict[str, Any]) -> dict[str, Any]:
    features = data.get("features", [])

    if not features:
        raise HTTPException(
            status_code=502,
            detail="TMAP 보행 경로 결과가 없습니다.",
        )

    path_coordinates = []
    instructions = []
    segments = []

    first_properties = features[0].get("properties", {})
    total_distance = first_properties.get("totalDistance", 0)
    total_time = first_properties.get("totalTime", 0)

    for feature in features:
        geometry = feature.get("geometry", {})
        properties = feature.get("properties", {})
        geometry_type = geometry.get("type")

        if geometry_type == "LineString":
            coordinates = geometry.get("coordinates", [])
            path_coordinates.extend(coordinates)

            segments.append(
                {
                    "distance_meters": properties.get("distance", 0),
                    "duration_seconds": properties.get("time", 0),
                    "road_name": properties.get("name", ""),
                    "description": properties.get("description", ""),
                    "road_type": properties.get("roadType"),
                    "facility_type": properties.get("facilityType"),
                    "coordinates": coordinates,
                }
            )

        elif geometry_type == "Point":
            description = properties.get("description", "")
            if description:
                instructions.append(
                    {
                        "description": description,
                        "turn_type": properties.get("turnType"),
                        "point_type": properties.get("pointType"),
                        "intersection_name": properties.get("intersectionName", ""),
                        "coordinate": geometry.get("coordinates", []),
                    }
                )

    # 💡 [핵심] 경사도 8.0% 이상인 급경사 구간만 선별 감지
    detected_slopes = detect_slopes_on_path(path_coordinates, slope_threshold=8.0)

    # 💡 급경사 여부 플래그 (경로 추천 알고리즘에서 우회할 때 활용)
    has_steep_slope = len(detected_slopes) > 0

    return {
        "type": "WALK",
        "total_distance_meters": total_distance,
        "total_duration_seconds": total_time,
        "total_duration_minutes": round(total_time / 60, 1),
        "path": path_coordinates,
        "instructions": instructions,
        "segments": segments,
        "detected_slopes": detected_slopes,
        "has_steep_slope": has_steep_slope,  # 8% 이상 급경사 포함 여부 (True/False)
    }


SEARCH_RADIUS_METERS = 80.0  # 경로 주변 이내 보행망 체크 반경

# 공간 인덱스 격자 한 칸 크기(도 단위, 위도 기준 약 111m).
# SEARCH_RADIUS_METERS보다 크게 잡아야 3x3 이웃 칸 조회만으로
# 반경 안의 모든 지점을 놓치지 않고 찾을 수 있다.
_SLOPE_INDEX_CELL_SIZE_DEG = 0.001

_slope_spatial_index_cache: (
    dict[tuple[int, int], list[tuple[float, float, float, str, int]]] | None
) = None


def _extract_slope_geometry_coords(
    geom: dict[str, Any],
) -> list[tuple[float, float]]:
    """feature의 geometry에서 (lat, lng) 좌표 목록을 뽑는다."""

    geom_type = geom.get("type")
    coords: list[tuple[float, float]] = []

    if geom_type == "MultiLineString":
        for line_coords in geom.get("coordinates", []):
            for coord in line_coords:
                if len(coord) >= 2:
                    coords.append((float(coord[1]), float(coord[0])))
    elif geom_type == "LineString":
        for coord in geom.get("coordinates", []):
            if len(coord) >= 2:
                coords.append((float(coord[1]), float(coord[0])))
    elif geom_type == "Point":
        pt_coords = geom.get("coordinates", [])
        if len(pt_coords) >= 2:
            coords.append((float(pt_coords[1]), float(pt_coords[0])))

    return coords


def _build_slope_spatial_index(
    network: dict[str, Any],
) -> dict[tuple[int, int], list[tuple[float, float, float, str, int]]]:
    """
    보행망 GeoJSON의 경사도 있는 지점들을 위경도 격자로 미리 묶어둔다.

    detect_slopes_on_path()가 경로 좌표 하나당 58,364개 feature 전체를
    순회하던 것을(실측 O(경로좌표 수 × feature 수)) 경로 좌표 주변
    격자 몇 칸만 조회하도록 바꾸기 위한 사전 준비 단계다. 프로세스
    생애주기 동안 한 번만 만들면 된다.
    """

    index: dict[
        tuple[int, int],
        list[tuple[float, float, float, str, int]],
    ] = {}

    features = network.get("features", [])

    for feature_id, feature in enumerate(features):

        props = feature.get("properties", {})
        geom = feature.get("geometry", {})

        raw_grade = (
            props.get("grade_100m")
            or props.get("grade_local")
            or props.get("slope_deg")
            or props.get("slope")
        )

        if raw_grade is None:
            continue

        try:
            raw_val = abs(float(raw_grade))
            slope_val = raw_val * 100.0 if raw_val < 1.0 else raw_val
        except (ValueError, TypeError):
            continue

        road_name = str(
            props.get("walk_class") or props.get("명칭") or "급경사 구간"
        )

        for lat, lng in _extract_slope_geometry_coords(geom):
            cell = (
                int(lat // _SLOPE_INDEX_CELL_SIZE_DEG),
                int(lng // _SLOPE_INDEX_CELL_SIZE_DEG),
            )
            index.setdefault(cell, []).append(
                (lat, lng, slope_val, road_name, feature_id)
            )

    return index


def _get_slope_spatial_index() -> (
    dict[tuple[int, int], list[tuple[float, float, float, str, int]]]
):
    global _slope_spatial_index_cache

    if _slope_spatial_index_cache is not None:
        return _slope_spatial_index_cache

    network = load_seongnam_walking_network()

    _slope_spatial_index_cache = (
        _build_slope_spatial_index(network) if network else {}
    )

    return _slope_spatial_index_cache


def detect_slopes_on_path(
    path_coordinates: list[list[float]], slope_threshold: float = 8.0
) -> list[dict[str, Any]]:
    """
    경사도 8.0% 이상의 급경사 구간만 정확히 감지한다(공간 인덱스 기반).

    경로 좌표마다 자신이 속한 격자 칸 + 주변 8칸만 조회하므로,
    전체 feature 수(58,364개)와 무관하게 경로 길이에 비례하는
    비용만 든다. feature 하나당 결과는 하나만 남긴다(기존 동작과 동일).
    """

    spatial_index = _get_slope_spatial_index()

    if not spatial_index:
        return []

    detected_slopes: list[dict[str, Any]] = []
    matched_feature_ids: set[int] = set()

    for p_lng, p_lat in path_coordinates:

        p_lat = float(p_lat)
        p_lng = float(p_lng)

        cell_x = int(p_lat // _SLOPE_INDEX_CELL_SIZE_DEG)
        cell_y = int(p_lng // _SLOPE_INDEX_CELL_SIZE_DEG)

        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):

                bucket = spatial_index.get(
                    (cell_x + dx, cell_y + dy)
                )

                if not bucket:
                    continue

                for s_lat, s_lng, slope_val, road_name, feature_id in bucket:

                    if (
                        slope_val < slope_threshold
                        or feature_id in matched_feature_ids
                    ):
                        continue

                    dist = calculate_distance_meters(
                        s_lat, s_lng, p_lat, p_lng
                    )

                    if dist <= SEARCH_RADIUS_METERS:
                        matched_feature_ids.add(feature_id)
                        detected_slopes.append(
                            {
                                "name": road_name,
                                "latitude": round(s_lat, 6),
                                "longitude": round(s_lng, 6),
                                "slope_degree": round(slope_val, 1),
                            }
                        )

    print(f"🔍 [백엔드 로그] 감지된 8% 이상 급경사로 개수: {len(detected_slopes)}개")
    return detected_slopes