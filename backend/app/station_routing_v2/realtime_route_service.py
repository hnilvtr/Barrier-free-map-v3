from __future__ import annotations

from typing import Any

import networkx as nx

from app.station_routing_v2.elevator_status_service import (
    get_facility_status_summary,
)
from app.station_routing_v2.path_finder import (
    find_internal_route,
)


def collect_route_elevator_facility_ids(
    route_result: dict[str, Any],
) -> list[str]:
    """
    이미 탐색된 경로 결과의 edge_path에서
    실제 사용되는 ELEVATOR facility_id만 수집한다.

    전체 역 그래프의 모든 엘리베이터를 검사할 필요가 없는 경우
    사용할 수 있는 보조 함수.
    """

    facility_ids: set[str] = set()

    edge_path = route_result.get(
        "edge_path",
        [],
    )

    if not isinstance(
        edge_path,
        list,
    ):
        return []

    for edge in edge_path:

        if not isinstance(
            edge,
            dict,
        ):
            continue

        mode = str(
            edge.get(
                "mode",
                "",
            )
        ).strip().upper()

        if mode != "ELEVATOR":
            continue

        facility_id = edge.get(
            "facility_id"
        )

        if facility_id is None:
            continue

        facility_id = str(
            facility_id
        ).strip()

        if facility_id:
            facility_ids.add(
                facility_id
            )

    return sorted(
        facility_ids
    )


def _attach_empty_realtime_metadata(
    result: dict[str, Any],
    blocked_facility_ids: set[str],
) -> dict[str, Any]:
    result["realtime_status"] = "UNKNOWN"
    result["checked_facility_ids"] = []
    result["available_facility_ids"] = []
    result["blocked_facility_ids"] = sorted(blocked_facility_ids)
    result["unknown_facility_ids"] = []
    result["facility_statuses"] = []
    result["realtime_data_source"] = None
    result["realtime_updated_at"] = None
    return result


def find_realtime_internal_route(
    graph: nx.DiGraph,
    station_name: str,
    start_node: str,
    end_node: str,
    max_retry: int = 10,
) -> dict[str, Any]:
    """
    실시간 승강기 운행 상태를 반영하여
    역사 내부 경로를 탐색한다.

    처리 과정 (station_path_service.find_realtime_safe_internal_path와
    동일한 전략을 신형 그래프에 적용한다):

    1. 차단 없이 최단 경로를 탐색한다.
    2. 그 경로가 실제로 사용하는 ELEVATOR facility_id만 실시간 상태를
       조회한다. 역 전체 엘리베이터가 아니라 "이 경로가 실제로 쓰는 것"만
       검사해서, 경로와 무관한 고장 시설 때문에 상태가 잘못 표시되거나
       불필요하게 차단되는 것을 막는다.
    3. 그중 UNAVAILABLE이 있으면 그 facility만 차단하고 다시 탐색한다.
    4. 새로 나온 경로도 같은 방식으로 검증하며, 더 이상 새로 차단할 게
       없거나 max_retry에 도달할 때까지 반복한다.

    정책:

    AVAILABLE
        경로 탐색에서 사용 가능

    UNAVAILABLE
        blocked_facility_ids에 포함하여 제외하고 재탐색

    UNKNOWN
        상태를 알 수 없는 시설
        경로에서는 차단하지 않음
    """

    blocked_facility_ids: set[str] = set()

    for _ in range(max_retry):

        result = find_internal_route(
            graph=graph,
            start_node=start_node,
            end_node=end_node,
            blocked_facility_ids=blocked_facility_ids,
        )

        if result.get("status") != "SUCCESS":
            return _attach_empty_realtime_metadata(
                result,
                blocked_facility_ids,
            )

        # 이 경로가 실제로 사용하는 엘리베이터만 검사한다.
        facility_ids = collect_route_elevator_facility_ids(
            result
        )

        status_summary = get_facility_status_summary(
            station_name=station_name,
            facility_ids=facility_ids,
        )

        summary_blocked_ids = {
            str(facility_id)
            for facility_id in status_summary.get(
                "blocked_facility_ids",
                [],
            )
        }

        newly_blocked = summary_blocked_ids - blocked_facility_ids

        if not newly_blocked:
            # 이 경로가 쓰는 시설 중 새로 고장난 게 없다 -> 확정.
            result["realtime_status"] = status_summary.get(
                "status", "UNKNOWN"
            )
            result["checked_facility_ids"] = status_summary.get(
                "checked_facility_ids", []
            )
            result["available_facility_ids"] = status_summary.get(
                "available_facility_ids", []
            )
            result["blocked_facility_ids"] = list(summary_blocked_ids)
            result["unknown_facility_ids"] = status_summary.get(
                "unknown_facility_ids", []
            )
            result["facility_statuses"] = status_summary.get(
                "facility_statuses", []
            )
            result["realtime_data_source"] = status_summary.get(
                "data_source"
            )
            result["realtime_updated_at"] = status_summary.get(
                "updated_at"
            )
            return result

        blocked_facility_ids |= newly_blocked
        # 다음 반복에서 이 facility들을 피해 재탐색한다.

    # max_retry를 넘도록 계속 새로운 고장 시설이 발견된 경우
    result = find_internal_route(
        graph=graph,
        start_node=start_node,
        end_node=end_node,
        blocked_facility_ids=blocked_facility_ids,
    )

    if result.get("status") == "SUCCESS":
        result["status"] = "MAX_RETRY_EXCEEDED"

    return _attach_empty_realtime_metadata(
        result,
        blocked_facility_ids,
    )