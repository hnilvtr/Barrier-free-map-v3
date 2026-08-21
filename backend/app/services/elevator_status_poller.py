from __future__ import annotations

import asyncio
import os
import time
from collections import defaultdict
from typing import Any
from urllib.parse import unquote

import httpx
from dotenv import load_dotenv

from app.data.realtime_facility_mapping import (
    REALTIME_FACILITY_MAPPING,
)


load_dotenv()


# ==============================================================================
# 1. 기본 설정
#
# 승강기 일련번호(elevator_no) 단건 조회 오퍼레이션. 엔드포인트/파라미터명은
# 실제 호출로 확인 완료.
# ==============================================================================

ELEVATOR_DEVICE_STATUS_URL = (
    "http://apis.data.go.kr/B553664/ElevatorInformationService/getElevatorViewM"
)

ELEVATOR_DEVICE_NO_PARAM_NAME = "elevator_no"

SERVICE_KEY = os.getenv("ELEVATOR_SERVICE_KEY", "")

POLL_INTERVAL_SECONDS = int(
    os.getenv("ELEVATOR_POLL_INTERVAL_SECONDS", "7200")
)

# 동시 호출 제한 (API 서버 부담 및 순간 폭주 방지)
#
# 실측(2026-08-21): 14개를 동시에 쏘자 게이트웨이가 즉시
# returnReasonCode=23(LIMITED_NUMBER_OF_SERVICE_REQUESTS_PER_SECOND_EXCEEDS_ERROR)로
# 거절함. 정확한 승인 TPS를 모르므로 보수적으로 시작하고, 필요하면 올린다.
MAX_CONCURRENT_REQUESTS = 3

# 세마포어로 동시 실행 개수만 제한하면 그 개수만큼은 여전히 같은 순간에
# 몰릴 수 있으므로, 요청 하나를 실제로 보내기 전에 약간의 간격을 둔다.
REQUEST_STAGGER_SECONDS = 0.3

# 폴링 대상 일련번호 -> 매핑 정보 (station_name 등)를 미리 뽑아둠
_DEVICE_ENTRIES: list[dict[str, Any]] = [
    {"edge_id": edge_id, **mapping}
    for edge_id, mapping in REALTIME_FACILITY_MAPPING.items()
    if mapping.get("device_no")
]


# ==============================================================================
# 2. 캐시 상태
# ==============================================================================
#
# get_station_facility_data()가 기대하는 기존 반환 형태(station_name -> 장비 리스트)를
# 그대로 유지해서, facility_status_service.py의 매칭 로직(find_device_by_no 등)을
# 하나도 건드리지 않아도 되게 한다.
# ==============================================================================

_cache_by_station: dict[str, list[dict[str, Any]]] = {}
_cache_updated_at: float | None = None
_poll_lock = asyncio.Lock()


# ==============================================================================
# 3. 장비 1대 상태 조회
# ==============================================================================

async def _fetch_device_status(
    client: httpx.AsyncClient,
    device_no: str,
) -> dict[str, Any] | None:
    """
    일련번호 하나에 대한 실시간 상태를 조회합니다.

    실패해도 전체 폴링을 중단하지 않도록 예외를 삼키고 None을 반환합니다.
    """

    params = {
        "serviceKey": unquote(SERVICE_KEY),
        "_type": "json",
        ELEVATOR_DEVICE_NO_PARAM_NAME: device_no,
    }

    try:
        response = await client.get(
            ELEVATOR_DEVICE_STATUS_URL,
            params=params,
        )
        response.raise_for_status()
        data = response.json()

        body = data.get("response", {}).get("body", {})
        item = body.get("item") if isinstance(body, dict) else None

        if isinstance(item, list):
            item = item[0] if item else None

        if not isinstance(item, dict):
            return None

        return item

    except Exception as error:
        # 네트워크 오류, 429, 응답 형식이 예상과 다른 경우 등
        # 장비 하나의 실패가 poll_once() 전체(asyncio.gather)를
        # 죽이지 않도록 여기서 전부 흡수한다.
        print(f"[승강기 폴링 실패] device_no={device_no}: {error}")
        return None


# ==============================================================================
# 4. 매핑된 장비 전체를 한 번에 폴링
# ==============================================================================

async def poll_once() -> None:
    """
    REALTIME_FACILITY_MAPPING에 등록된 모든 승강기의 실시간 상태를
    동시에(동시 호출 수 제한 하에) 조회해 캐시를 통째로 교체합니다.

    이벤트(변경 diff) 로깅은 하지 않습니다 — 캐시는 항상 최신 폴링 결과로
    덮어써지며, 최신성은 POLL_INTERVAL_SECONDS 주기로만 보장됩니다.
    """

    global _cache_by_station, _cache_updated_at

    if not SERVICE_KEY:
        print("[승강기 폴링] ELEVATOR_SERVICE_KEY가 없어 폴링을 건너뜁니다.")
        return

    if not _DEVICE_ENTRIES:
        print("[승강기 폴링] REALTIME_FACILITY_MAPPING에 등록된 장비가 없습니다.")
        return

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def bound_fetch(
        client: httpx.AsyncClient,
        entry: dict[str, Any],
        launch_delay: float,
    ) -> tuple[dict[str, Any], dict[str, Any] | None]:
        # 세마포어는 "동시 실행 개수"만 제한하므로, 그 개수만큼은
        # 여전히 같은 순간에 몰려 나갈 수 있다. 장비 순서대로 약간씩
        # 늦게 출발시켜서 초당 요청 수 자체를 눌러준다.
        await asyncio.sleep(launch_delay)

        async with semaphore:
            device = await _fetch_device_status(
                client,
                str(entry["device_no"]),
            )
            return entry, device

    async with httpx.AsyncClient(timeout=15.0) as client:
        results = await asyncio.gather(
            *[
                bound_fetch(client, entry, index * REQUEST_STAGGER_SECONDS)
                for index, entry in enumerate(_DEVICE_ENTRIES)
            ]
        )

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for entry, device in results:
        if device is None:
            continue

        station_name = str(entry.get("station_name", "")).strip()
        if not station_name:
            continue

        grouped[station_name].append(device)

    async with _poll_lock:
        _cache_by_station = dict(grouped)
        _cache_updated_at = time.time()


# ==============================================================================
# 5. 백그라운드 무한 루프
# ==============================================================================

async def run_forever() -> None:
    while True:
        try:
            await poll_once()
        except Exception as error:
            print(f"[승강기 폴링 루프 오류] {error}")

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


# ==============================================================================
# 6. facility_status_service.py에서 읽어가는 조회 함수
# ==============================================================================

def get_station_devices(
    station_name: str,
) -> list[dict[str, Any]] | None:
    """
    캐시가 아직 한 번도 채워지지 않았으면 None을 반환합니다.
    (해당 역이 매핑 테이블에 없어서 빈 리스트인 것과 구분하기 위함)
    """

    if _cache_updated_at is None:
        return None

    return _cache_by_station.get(station_name, [])


def get_cache_age_seconds() -> float | None:
    if _cache_updated_at is None:
        return None
    return time.time() - _cache_updated_at
