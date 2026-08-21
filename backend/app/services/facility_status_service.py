from __future__ import annotations

import re
from collections import defaultdict
from typing import Any

from app.data.realtime_facility_mapping import (
    get_realtime_facility_mapping,
)


CLASSIFY_FIELDS = [
    "elvtrDivNm",
    "elvtrKindNm",
    "elvtrForm",
    "elvtrSeNm",
]


# ==============================================================================
# 2. 문자열 정규화
# ==============================================================================

def normalize_device_no(
    value: Any,
) -> str:
    """
    elevatorNo를 숫자 7자리 문자열로 통일합니다.
    """

    if value is None:
        return ""

    digits = re.sub(
        r"\D",
        "",
        str(value),
    )

    if not digits:
        return ""

    return digits.zfill(7)


def normalize_floor(
    value: Any,
) -> str:

    if value is None:
        return ""

    text = (
        str(value)
        .strip()
        .upper()
        .replace(" ", "")
    )

    if text.endswith("F"):
        text = text[:-1]

    return text


def normalize_line_name(
    value: Any,
) -> str:
    """
    노선명 표현 차이를 조금 보정합니다.
    """

    text = (
        str(value or "")
        .strip()
        .replace(" ", "")
    )

    replacements = {
        "수인분당선": "분당선",
        "경의·중앙선": "경의중앙선",
    }

    for before, after in replacements.items():
        text = text.replace(
            before,
            after,
        )

    return text


def normalize_location(
    value: Any,
) -> str:
    """
    상세 위치 문자열 비교용 정규화.

    예:

    (B2) 삼동행 표 내는 곳 내 계단 옆
    (B3) 삼동행 승강장 3-4 출입문 앞

    과

    (B2)삼동행표내는곳내계단옆
    (B3)삼동행승강장3-4출입문앞

    을 동일하게 비교할 수 있도록 합니다.
    """

    if value is None:
        return ""

    text = str(
        value
    ).strip()

    if not text:
        return ""

    text = text.lower()

    # 공백 제거
    text = re.sub(
        r"\s+",
        "",
        text,
    )

    # 쉼표 / > / ↔ 등 표현 차이 제거
    text = re.sub(
        r"[,>↔→←]",
        "",
        text,
    )

    # 일부 흔한 구두점 제거
    text = re.sub(
        r"[._]",
        "",
        text,
    )

    return text


# ==============================================================================
# 3. 시설 종류 판별
# ==============================================================================

def classify_facility(
    item: dict[str, Any],
) -> str:

    text = " ".join(
        str(
            item.get(
                field,
                "",
            )
        )
        for field
        in CLASSIFY_FIELDS
    ).strip()

    if not text:
        text = " ".join(
            str(value)
            for value
            in item.values()
        )

    if (
        "에스컬레이터" in text
        or
        "무빙워크" in text
    ):
        return "ESCALATOR"

    if (
        "휠체어리프트" in text
        or
        "리프트" in text
    ):
        return "WHEELCHAIR_LIFT"

    if (
        "엘리베이터" in text
        or
        "승강기" in text
    ):
        return "ELEVATOR"

    return "OTHER"


# ==============================================================================
# 4. 운행 상태 정규화
# ==============================================================================

def normalize_operation_status(
    raw_status: Any,
) -> str:

    if raw_status is None:
        return "UNKNOWN"

    status = (
        str(raw_status)
        .strip()
        .replace(" ", "")
        .upper()
    )

    if not status:
        return "UNKNOWN"

    # 주의: unavailable_keywords를 먼저 검사해야 한다.
    # "운행중지"에는 "운행중"이 부분 문자열로 포함되어 있어서,
    # AVAILABLE 키워드를 먼저 검사하면 실제로는 고장/운행중지인
    # 장비가 "운행중"으로 잘못 매칭되어 AVAILABLE로 판정된다.
    unavailable_keywords = [
        "운행정지",
        "운행중지",
        "정지",
        "고장",
        "점검",
        "휴지",
        "폐지",
        "사용중지",
        "사용불가",
    ]

    for keyword in unavailable_keywords:

        if keyword in status:
            return "UNAVAILABLE"

    available_keywords = [
        "운행중",
        "정상",
        "정상운행",
        "가동중",
    ]

    for keyword in available_keywords:

        if keyword in status:
            return "AVAILABLE"

    return "UNKNOWN"


# ==============================================================================
# 5. 역 데이터 가져오기 — elevator_status_poller의 폴링 캐시에서 읽음
# ==============================================================================

def get_station_facility_data(
    station_name: str,
) -> dict[str, Any]:
    """
    실시간 승강기 상태를 elevator_status_poller의 인메모리 캐시에서 읽어옵니다.

    JSON 스냅샷 파일(load_station_facilities_from_json)과 요청 시점
    라이브 API 호출(fetch_station_facilities)은 더 이상 요청 경로에서
    사용하지 않습니다 — 백그라운드 폴러가 미리 채워둔 캐시만 읽습니다.
    """

    from app.services.elevator_status_poller import (
        get_cache_age_seconds,
        get_station_devices,
    )

    devices = get_station_devices(station_name)

    if devices is None:
        return {
            "status": "DATA_NOT_AVAILABLE",
            "station_name": station_name,
            "items": [],
            "source": "POLL_CACHE",
            "updated_at": None,
            "message": (
                "아직 승강기 상태 폴링 캐시가 준비되지 않았습니다."
            ),
        }

    return {
        "status": "SUCCESS",
        "station_name": station_name,
        "items": devices,
        "total_count": len(devices),
        "updated_at": get_cache_age_seconds(),
        "source": "POLL_CACHE",
    }


# ==============================================================================
# 9. elevatorNo 정확 매칭
# ==============================================================================

def find_device_by_no(
    devices: list[dict[str, Any]],
    device_no: str,
) -> dict[str, Any] | None:

    target = (
        normalize_device_no(
            device_no
        )
    )

    if not target:
        return None

    for device in devices:

        current = (
            normalize_device_no(
                device.get(
                    "elevatorNo"
                )
            )
        )

        if current == target:
            return device

    return None


# ==============================================================================
# 10. 노선 비교
# ==============================================================================

def device_matches_line(
    device: dict[str, Any],
    line_name: str,
) -> bool:

    expected = (
        normalize_line_name(
            line_name
        )
    )

    if not expected:
        return True

    building_name = (
        normalize_line_name(
            device.get(
                "buldNm",
                "",
            )
        )
    )

    if not building_name:
        return True

    return (
        expected
        in building_name
    )


# ==============================================================================
# 11. ★ 상세 위치 기준 1:1 매칭
# ==============================================================================

def find_device_by_detail_location(
    facility: dict[str, Any],
    devices: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    내부 그래프의 detail_location과
    저장 JSON의 dtlLoc이 일치하는 실제 장비를 찾습니다.

    우선:
    시설 종류 + 노선 + 상세 위치

    가 모두 일치해야 합니다.
    """

    detail_location = (
        normalize_location(
            facility.get(
                "detail_location"
            )
        )
    )

    if not detail_location:
        return None

    expected_type = (
        str(
            facility.get(
                "facility_type",
                "",
            )
        )
        .strip()
        .upper()
    )

    line_name = str(
        facility.get(
            "line_name",
            "",
        )
    ).strip()

    matches: list[
        dict[str, Any]
    ] = []

    for device in devices:

        # ----------------------------------------------------------
        # 시설 종류
        # ----------------------------------------------------------

        actual_type = (
            classify_facility(
                device
            )
        )

        if (
            expected_type
            and
            actual_type
            != expected_type
        ):
            continue

        # ----------------------------------------------------------
        # 노선
        # ----------------------------------------------------------

        if (
            line_name
            and
            not device_matches_line(
                device,
                line_name,
            )
        ):
            continue

        # ----------------------------------------------------------
        # 상세위치
        # ----------------------------------------------------------

        device_location = (
            normalize_location(
                device.get(
                    "dtlLoc"
                )
            )
        )

        if not device_location:
            continue

        if (
            detail_location
            == device_location
        ):

            matches.append(
                device
            )

    # 상세위치가 같은 장비가 정확히 1대일 때만
    # 진짜 1:1 매칭으로 인정
    if len(matches) == 1:

        return matches[0]

    return None


# ==============================================================================
# 12. 층 구간 비교
# ==============================================================================

def normalize_section(
    value: Any,
) -> tuple[str, str] | None:

    if value is None:
        return None

    text = (
        str(value)
        .strip()
        .upper()
        .replace(" ", "")
    )

    parts = text.split(
        "-"
    )

    if len(parts) != 2:
        return None

    first = normalize_floor(
        parts[0]
    )

    second = normalize_floor(
        parts[1]
    )

    if not first or not second:
        return None

    return (
        first,
        second,
    )


def same_floor_section(
    from_floor: Any,
    to_floor: Any,
    section_value: Any,
) -> bool:

    section = (
        normalize_section(
            section_value
        )
    )

    if not section:
        return False

    expected_from = (
        normalize_floor(
            from_floor
        )
    )

    expected_to = (
        normalize_floor(
            to_floor
        )
    )

    if (
        not expected_from
        or
        not expected_to
    ):
        return False

    actual_from, actual_to = (
        section
    )

    return (
        (
            expected_from
            == actual_from
            and
            expected_to
            == actual_to
        )
        or
        (
            expected_from
            == actual_to
            and
            expected_to
            == actual_from
        )
    )


# ==============================================================================
# 13. 구간 fallback 장비 검색
# ==============================================================================

def find_segment_devices(
    facility: dict[str, Any],
    devices: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    expected_type = (
        str(
            facility.get(
                "facility_type",
                "",
            )
        )
        .upper()
    )

    line_name = str(
        facility.get(
            "line_name",
            "",
        )
    ).strip()

    from_floor = (
        facility.get(
            "actual_from_floor"
        )
        or
        facility.get(
            "edge_from_floor"
        )
    )

    to_floor = (
        facility.get(
            "actual_to_floor"
        )
        or
        facility.get(
            "edge_to_floor"
        )
    )

    candidates = []

    for device in devices:

        actual_type = (
            classify_facility(
                device
            )
        )

        if (
            expected_type
            and
            actual_type
            != expected_type
        ):
            continue

        if (
            line_name
            and
            not device_matches_line(
                device,
                line_name,
            )
        ):
            continue

        if not same_floor_section(
            from_floor,
            to_floor,
            device.get(
                "shuttleSection"
            ),
        ):
            continue

        candidates.append(
            device
        )

    return candidates


# ==============================================================================
# 14. 실제 장비 상태 결과 생성
# ==============================================================================

def build_device_status(
    device: dict[str, Any],
    facility: dict[str, Any],
    match_method: str,
    mapping_status: str,
    data_source: str,
    updated_at: Any,
) -> dict[str, Any]:

    raw_status = (
        device.get(
            "elvtrStts"
        )
    )

    realtime_status = (
        normalize_operation_status(
            raw_status
        )
    )

    expected_type = (
        str(
            facility.get(
                "facility_type",
                "",
            )
        )
        .upper()
    )

    actual_type = (
        classify_facility(
            device
        )
    )

    return {
        "realtime_status": (
            realtime_status
        ),

        "mapping_status": (
            mapping_status
        ),

        "match_method": (
            match_method
        ),

        "data_source": (
            data_source
        ),

        "updated_at": (
            updated_at
        ),

        "device_no": str(
            device.get(
                "elevatorNo",
                "",
            )
        ),

        "facility_type": (
            expected_type
        ),

        "api_facility_type": (
            actual_type
        ),

        "facility_type_matched": (
            (
                not expected_type
            )
            or
            (
                expected_type
                == actual_type
            )
        ),

        "raw_status": (
            raw_status
        ),

        "installation_place": (
            device.get(
                "dtlLoc"
            )
            or
            device.get(
                "installationPlace"
            )
        ),

        "shuttle_section": (
            device.get(
                "shuttleSection"
            )
        ),

        "exit_no": (
            device.get(
                "locationExitNo"
            )
        ),

        "pause_date": (
            device.get(
                "pauseAblDe"
            )
        ),

        "pause_reason": (
            device.get(
                "pauseAbleResn"
            )
        ),
    }


# ==============================================================================
# 15. 구간 fallback 상태
# ==============================================================================

def build_segment_fallback_status(
    facility: dict[str, Any],
    candidates: list[dict[str, Any]],
    data_source: str,
    updated_at: Any,
) -> dict[str, Any]:

    if not candidates:

        return {
            "realtime_status": (
                "UNKNOWN"
            ),

            "mapping_status": (
                "SEGMENT_NOT_FOUND"
            ),

            "match_method": (
                "STATION_LINE_FLOOR"
            ),

            "data_source": (
                data_source
            ),

            "updated_at": (
                updated_at
            ),

            "device_no": None,

            "raw_status": None,

            "message": (
                "동일 역·노선·시설종류·"
                "층 구간의 장비를 찾지 못했습니다."
            ),
        }

    available = []
    unavailable = []
    unknown = []

    for device in candidates:

        status = (
            normalize_operation_status(
                device.get(
                    "elvtrStts"
                )
            )
        )

        if status == "AVAILABLE":

            available.append(
                device
            )

        elif status == "UNAVAILABLE":

            unavailable.append(
                device
            )

        else:

            unknown.append(
                device
            )

    if available:

        representative = (
            available[0]
        )

        realtime_status = (
            "AVAILABLE"
        )

    elif (
        unavailable
        and
        not unknown
    ):

        representative = (
            unavailable[0]
        )

        realtime_status = (
            "UNAVAILABLE"
        )

    else:

        representative = (
            candidates[0]
        )

        realtime_status = (
            "UNKNOWN"
        )

    return {
        "realtime_status": (
            realtime_status
        ),

        "mapping_status": (
            "SEGMENT_FALLBACK"
        ),

        "match_method": (
            "STATION_LINE_FLOOR"
        ),

        "data_source": (
            data_source
        ),

        "updated_at": (
            updated_at
        ),

        "device_no": str(
            representative.get(
                "elevatorNo",
                "",
            )
        ),

        "facility_type": (
            facility.get(
                "facility_type"
            )
        ),

        "raw_status": (
            representative.get(
                "elvtrStts"
            )
        ),

        "matched_device_count": (
            len(candidates)
        ),

        "available_device_count": (
            len(available)
        ),

        "unavailable_device_count": (
            len(unavailable)
        ),

        "unknown_device_count": (
            len(unknown)
        ),

        "shuttle_section": (
            representative.get(
                "shuttleSection"
            )
        ),

        "message": (
            "정확한 장비 1:1 매칭 실패로 "
            "역·노선·시설종류·층 구간을 "
            "이용한 fallback 결과입니다."
        ),
    }


# ==============================================================================
# 16. 시설 하나의 실시간 상태
#
# 우선순위
#
# 1. edge_id → device_no 기존 확정 매핑
# 2. detail_location → dtlLoc 1:1 매핑
# 3. 역 + 노선 + 시설종류 + 층 구간 fallback
# ==============================================================================

def get_facility_realtime_status(
    facility: dict[str, Any],
    station_devices: list[dict[str, Any]],
    data_source: str = "UNKNOWN",
    updated_at: Any = None,
) -> dict[str, Any]:

    edge_id = str(
        facility.get(
            "edge_id",
            "",
        )
    ).strip()

    # --------------------------------------------------------------------------
    # 1순위
    # 기존 edge_id → device_no 확정 매핑
    # --------------------------------------------------------------------------

    mapping = None

    if edge_id:

        mapping = (
            get_realtime_facility_mapping(
                edge_id
            )
        )

    if mapping:

        device_no = (
            mapping.get(
                "device_no"
            )
        )

        if device_no:

            device = (
                find_device_by_no(
                    station_devices,
                    str(device_no),
                )
            )

            if device:

                return (
                    build_device_status(
                        device=device,

                        facility=facility,

                        match_method=(
                            "DEVICE_NO"
                        ),

                        mapping_status=(
                            "CONFIRMED"
                        ),

                        data_source=(
                            data_source
                        ),

                        updated_at=(
                            updated_at
                        ),
                    )
                )

    # --------------------------------------------------------------------------
    # 2순위
    # 상세 위치 기반 1:1 매칭
    # --------------------------------------------------------------------------

    location_device = (
        find_device_by_detail_location(
            facility,
            station_devices,
        )
    )

    if location_device:

        return (
            build_device_status(
                device=(
                    location_device
                ),

                facility=(
                    facility
                ),

                match_method=(
                    "DETAIL_LOCATION"
                ),

                mapping_status=(
                    "CONFIRMED"
                ),

                data_source=(
                    data_source
                ),

                updated_at=(
                    updated_at
                ),
            )
        )

    # --------------------------------------------------------------------------
    # 3순위
    # 기존 구간 fallback
    # --------------------------------------------------------------------------

    candidates = (
        find_segment_devices(
            facility,
            station_devices,
        )
    )

    return (
        build_segment_fallback_status(
            facility=facility,

            candidates=candidates,

            data_source=(
                data_source
            ),

            updated_at=(
                updated_at
            ),
        )
    )


# ==============================================================================
# 17. required_facilities 전체에 상태 추가
# ==============================================================================

def attach_realtime_status_to_facilities(
    required_facilities: list[
        dict[str, Any]
    ],
) -> list[dict[str, Any]]:

    if not required_facilities:
        return []

    facilities_by_station: dict[
        str,
        list[dict[str, Any]],
    ] = defaultdict(
        list
    )

    for facility in (
        required_facilities
    ):

        station_name = str(
            facility.get(
                "station_name",
                "",
            )
        ).strip()

        if not station_name:
            continue

        facilities_by_station[
            station_name
        ].append(
            facility
        )

    # --------------------------------------------------------------------------
    # 역별 JSON/API 결과 캐시
    # --------------------------------------------------------------------------

    station_cache: dict[
        str,
        dict[str, Any],
    ] = {}

    for station_name in (
        facilities_by_station
    ):

        station_cache[
            station_name
        ] = (
            get_station_facility_data(
                station_name
            )
        )

    result = []

    for facility in (
        required_facilities
    ):

        copied = dict(
            facility
        )

        edge_id = str(
            facility.get(
                "edge_id",
                "",
            )
        ).strip()

        station_name = str(
            facility.get(
                "station_name",
                "",
            )
        ).strip()

        if not edge_id:

            realtime_info = {
                "realtime_status": (
                    "UNKNOWN"
                ),

                "mapping_status": (
                    "INVALID_EDGE"
                ),

                "device_no": None,

                "raw_status": None,

                "message": (
                    "edge_id가 없습니다."
                ),
            }

        elif not station_name:

            realtime_info = {
                "realtime_status": (
                    "UNKNOWN"
                ),

                "mapping_status": (
                    "INVALID_STATION"
                ),

                "device_no": None,

                "raw_status": None,

                "message": (
                    "station_name이 없습니다."
                ),
            }

        else:

            station_result = (
                station_cache.get(
                    station_name,
                    {},
                )
            )

            station_status = (
                station_result.get(
                    "status"
                )
            )

            if (
                station_status
                != "SUCCESS"
            ):

                realtime_info = {
                    "realtime_status": (
                        "UNKNOWN"
                    ),

                    "mapping_status": (
                        "DATA_NOT_AVAILABLE"
                    ),

                    "device_no": None,

                    "raw_status": None,

                    "data_source": (
                        station_result.get(
                            "source"
                        )
                    ),

                    "updated_at": (
                        station_result.get(
                            "updated_at"
                        )
                    ),

                    "message": (
                        station_result.get(
                            "message",
                            (
                                "승강기 운행정보를 "
                                "불러오지 못했습니다."
                            ),
                        )
                    ),
                }

            else:

                realtime_info = (
                    get_facility_realtime_status(
                        facility=(
                            facility
                        ),

                        station_devices=(
                            station_result.get(
                                "items",
                                [],
                            )
                        ),

                        data_source=(
                            station_result.get(
                                "source",
                                "UNKNOWN",
                            )
                        ),

                        updated_at=(
                            station_result.get(
                                "updated_at"
                            )
                        ),
                    )
                )

        copied[
            "realtime"
        ] = (
            realtime_info
        )

        result.append(
            copied
        )

    return result


# ==============================================================================
# 18. 전체 경로 시설 상태 요약
# ==============================================================================

def summarize_route_facility_status(
    facilities: list[
        dict[str, Any]
    ],
) -> dict[str, Any]:

    if not facilities:

        return {
            "status": "AVAILABLE",
            "total_facility_count": 0,
            "available_count": 0,
            "unavailable_count": 0,
            "unknown_count": 0,
        }

    available_count = 0
    unavailable_count = 0
    unknown_count = 0

    for facility in facilities:

        realtime = (
            facility.get(
                "realtime",
                {},
            )
        )

        if not isinstance(
            realtime,
            dict,
        ):

            realtime = {}

        status = (
            realtime.get(
                "realtime_status",
                "UNKNOWN",
            )
        )

        if status == "AVAILABLE":

            available_count += 1

        elif status == "UNAVAILABLE":

            unavailable_count += 1

        else:

            unknown_count += 1

    if unavailable_count > 0:

        route_status = (
            "UNAVAILABLE"
        )

    elif unknown_count > 0:

        route_status = (
            "UNKNOWN"
        )

    else:

        route_status = (
            "AVAILABLE"
        )

    return {
        "status": (
            route_status
        ),

        "total_facility_count": (
            len(facilities)
        ),

        "available_count": (
            available_count
        ),

        "unavailable_count": (
            unavailable_count
        ),

        "unknown_count": (
            unknown_count
        ),
    }