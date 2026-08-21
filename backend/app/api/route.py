from typing import Any

from pathlib import Path

from fastapi import APIRouter, HTTPException

from app.schemas.route_schema import (
    RouteByPlaceRequest,
    RouteCandidateRequest,
)

from app.services.geocode_service import (
    GeocodeService,
)

from app.services.kakao_service import (
    get_transit_routes,
    simplify_routes,
)

from app.services.movement_extraction_service import (
    attach_station_movements,
    LINE_STATION_ORDERS,
)

from app.services.recommendation_service import (
    select_best_candidate,
)

from app.services.station_path_service import (
    analyze_station_movement,
    resolve_movement_nodes,
    find_shortest_internal_path,
    extract_required_facilities,
    find_realtime_safe_internal_path,
)

from app.services.facility_status_service import (
    attach_realtime_status_to_facilities,
    summarize_route_facility_status,
)

from app.services.bus_matching_service import (
    match_bus_step_identifiers,
)

from app.services.bus_arrival_service import (
    get_low_floor_bus_status,
)
from app.services.walking_route_service import (
    get_walking_route,
)
from app.services.walking_integration_service import (
    attach_walking_access_to_routes,
)
from app.station_routing_v2.graph_merge import (
    build_station_graph_from_directory,
)

from app.station_routing_v2.graph_loader import (
    load_station_graph,
)

from app.station_routing_v2.path_finder import (
    find_internal_route,
)

from app.station_routing_v2.realtime_route_service import (
    find_realtime_internal_route,
)

router = APIRouter(
    prefix="/routes",
    tags=["Routes"],
)
# ==============================================================================
# 신형 역사 그래프 V2 설정
# ==============================================================================

STATION_GRAPHS_V2_DIR = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "station_graphs_v2"
)


TRANSFER_STATION_CONFIG = {
    "이매": {
        "folder": "imae",
        "parent_station_code": "IMA",
    },
    "정자": {
        "folder": "jeongja",
        "parent_station_code": "JJA",
    },
    "미금": {
        "folder": "migeum",
        "parent_station_code": "MIG",
    },
    "모란": {
        "folder": "moran",
        "parent_station_code": "MOR",
    },
    "판교": {
        "folder": "pangyo",
        "parent_station_code": "PYO",
    },
}


STATION_FILE_CONFIG = {
    "태평": "taepyeong",
    "가천대": "gachon_univ",
    "수진": "sujin",
    "야탑": "yatap",
    "서현": "seohyeon",
    "수내": "sunae",
    "오리": "ori",
    "산성": "sanseong",
    "남한산성입구": "namhansanseong",
    "단대오거리": "dandaeogeori",
    "신흥": "sinheung",
    "남위례": "namwirye",
    "성남": "seongnam",
}


def _normalize_station_text(
    value: Any,
) -> str:
    """
    역명/방향역 비교를 위한 간단한 정규화.
    """

    return (
        str(value or "")
        .replace("역", "")
        .replace(" ", "")
        .strip()
    )


def _find_v2_platform_node_by_target(
    graph: Any,
    target: str,
    line_name: str | None = None,
) -> str | None:
    """
    이미 정규화된 target 문자열 하나로 V2 PLATFORM node를 찾는다.

    복수 노선 역에서 같은 방향명이 여러 PLATFORM에
    존재할 수 있으므로 line_name을 함께 사용한다.
    """

    if not target:
        return None

    # --------------------------------------------------------------------------
    # 노선명 -> 그래프 파일명 식별 키워드
    # --------------------------------------------------------------------------

    line_file_keywords = {
        "신분당선": "sinbundang",
        "수인분당선": "suinbundang",
        "경강선": "gyeonggang",
        "8호선": "line8",
    }

    candidates: list[
        tuple[str, dict[str, Any]]
    ] = []

    # --------------------------------------------------------------------------
    # 1. 우선 방향명이 맞는 PLATFORM을 모두 찾는다.
    # --------------------------------------------------------------------------

    for node_id, node_data in graph.nodes(
        data=True
    ):
        node_type = str(
            node_data.get(
                "type",
                "",
            )
        ).upper()

        is_platform = (
            node_type == "PLATFORM"
            or "PLATFORM" in str(
                node_id
            ).upper()
        )

        if not is_platform:
            continue

        node_name = (
            _normalize_station_text(
                node_data.get(
                    "name",
                    "",
                )
            )
        )

        if target not in node_name:
            continue

        candidates.append(
            (
                str(node_id),
                node_data,
            )
        )

    # 후보 자체가 없으면 실패
    if not candidates:
        return None

    # 방향만으로 정확히 하나면 바로 사용
    if len(candidates) == 1:
        return candidates[0][0]

    # --------------------------------------------------------------------------
    # 2. 같은 방향 PLATFORM이 여러 개라면 노선으로 구분
    # --------------------------------------------------------------------------

    normalized_line_name = str(
        line_name or ""
    ).strip()

    line_keyword = (
        line_file_keywords.get(
            normalized_line_name
        )
    )

    if line_keyword:

        line_matching_candidates: list[
            str
        ] = []

        for node_id, node_data in candidates:

            source_files = (
                node_data.get(
                    "source_files",
                    [],
                )
            )

            if not isinstance(
                source_files,
                list,
            ):
                source_files = []

            source_text = " ".join(
                str(source_file).lower()
                for source_file in source_files
            )

            if (
                line_keyword.lower()
                in source_text
            ):
                line_matching_candidates.append(
                    node_id
                )

        if len(
            line_matching_candidates
        ) == 1:
            return (
                line_matching_candidates[0]
            )

    # --------------------------------------------------------------------------
    # 애매한 경우 임의 선택하지 않는다.
    # --------------------------------------------------------------------------

    return None


def _resolve_direction_station_chain(
    line_name: str | None,
    from_station_name: str | None,
    direction_station: str | None,
) -> list[str]:
    """
    direction_station이 V2 그래프의 승강장 라벨과 직접 매칭되지 않을 때를
    위한 보완책이다.

    카카오가 주는 direction_station은 보통 "바로 다음 정차역"인데,
    V2 그래프의 방향 라벨은 그보다 더 먼 대표 지명을 쓰는 경우가 있다
    (예: 판교역 경강선의 "이매 방면" 승강장 — 실제 바로 다음 역은 성남역).

    LINE_STATION_ORDERS(movement_extraction_service.py에 정의된,
    방향 판별용으로 축소된 노선 순서)를 이용해 from_station_name에서
    direction_station 쪽으로 이어지는 역 이름을 전부(그 노선 순서 목록의
    끝까지) 순서대로 반환한다. 노선/역이 이 목록에 없으면 빈 리스트를
    반환한다.
    """

    order = LINE_STATION_ORDERS.get(
        str(line_name or "").strip()
    )

    if not order:
        return []

    from_norm = _normalize_station_text(
        from_station_name
    )

    direction_norm = _normalize_station_text(
        direction_station
    )

    order_norm = [
        _normalize_station_text(station)
        for station in order
    ]

    if (
        not from_norm
        or not direction_norm
        or from_norm not in order_norm
        or direction_norm not in order_norm
    ):
        return []

    from_index = order_norm.index(
        from_norm
    )

    direction_index = order_norm.index(
        direction_norm
    )

    if from_index == direction_index:
        return []

    sign = (
        1
        if direction_index > from_index
        else -1
    )

    chain: list[str] = []
    index = direction_index

    while 0 <= index < len(order):
        chain.append(order[index])
        index += sign

    return chain


TERMINUS_PLATFORM_KEYWORDS = [
    "종점",
    "종착",
]


def _is_line_terminus(
    line_name: str | None,
    station_name: str | None,
) -> bool:
    """
    station_name이 LINE_STATION_ORDERS 상에서 해당 노선의
    양쪽 끝(첫 역 또는 마지막 역)인지 확인한다.

    종착역에서는 "도착 후 계속 갈 다음 역"이 애초에 존재하지 않으므로
    direction_station이 항상 계산되지 않는다.
    """

    order = LINE_STATION_ORDERS.get(
        str(line_name or "").strip()
    )

    if not order:
        return False

    normalized_station = _normalize_station_text(
        station_name
    )

    order_norm = [
        _normalize_station_text(station)
        for station in order
    ]

    if normalized_station not in order_norm:
        return False

    index = order_norm.index(
        normalized_station
    )

    return (
        index == 0
        or index == len(order_norm) - 1
    )


def _find_v2_terminus_platform_node(
    graph: Any,
    line_name: str | None = None,
) -> str | None:
    """
    이름에 "종점"/"종착"이 들어간 PLATFORM node를 찾는다.

    예: 판교역(경강선) "종점 방면 승강장",
        모란역(8호선) "모란(종착역) 승강장"
    """

    target_keywords = TERMINUS_PLATFORM_KEYWORDS

    candidates: list[str] = []

    for node_id, node_data in graph.nodes(
        data=True
    ):
        node_type = str(
            node_data.get(
                "type",
                "",
            )
        ).upper()

        is_platform = (
            node_type == "PLATFORM"
            or "PLATFORM" in str(
                node_id
            ).upper()
        )

        if not is_platform:
            continue

        node_name = str(
            node_data.get(
                "name",
                "",
            )
        )

        if any(
            keyword in node_name
            for keyword in target_keywords
        ):
            candidates.append(
                str(node_id)
            )

    if len(candidates) == 1:
        return candidates[0]

    # 여러 개거나 없으면 임의로 고르지 않는다.
    return None


def _find_v2_platform_node(
    graph: Any,
    direction_station: str | None,
    line_name: str | None = None,
    from_station_name: str | None = None,
    previous_station: str | None = None,
) -> str | None:
    """
    진행 방향 + 노선 정보를 이용해
    V2 그래프의 PLATFORM node를 찾는다.

    1순위: direction_station 그대로 매칭한다.
    2순위: 그래도 못 찾으면, 같은 노선에서 그 방향으로 이어지는 역
           이름들을 순서대로 시도한다(LINE_STATION_ORDERS 기반) — V2
           그래프 라벨이 "바로 다음 역"이 아니라 더 먼 대표 지명을 쓰는
           역(예: 판교역 경강선)을 위한 보완책이다.
    3순위: direction_station을 아예 계산하지 못했고(target 없음),
           from_station_name이 해당 노선의 종착역이면 "종점"/"종착"
           라벨의 승강장을 찾는다 — 종착역은 "계속 갈 다음 역"이 없어서
           direction_station이 원천적으로 안 나오는 역이다(예: 판교역
           경강선, 모란역 8호선). previous_station보다 먼저 시도해야
           한다 — previous_station이 우연히 "OO 방면"(출발용) 승강장과
           문자열이 겹쳐서 틀린 승강장으로 매칭될 수 있기 때문이다.
    4순위: 그래도 못 찾으면 previous_station(카카오가 이미 정확히 주는,
           이 역 바로 이전 정차역)을 시도한다. LINE_STATION_ORDERS에
           노선 자체가 없거나 목록이 짧아서 direction_station을 전혀
           계산하지 못한 하차/환승 도착 방향을 보완하기 위한 것이다.
    """

    target = _normalize_station_text(
        direction_station
    )

    if target:

        result = _find_v2_platform_node_by_target(
            graph,
            target,
            line_name,
        )

        if result is not None:
            return result

    fallback_chain = _resolve_direction_station_chain(
        line_name=line_name,
        from_station_name=from_station_name,
        direction_station=direction_station,
    )

    # chain[0]은 direction_station 자신이므로 이미 위에서 시도했다.
    for candidate_name in fallback_chain[1:]:

        candidate_target = _normalize_station_text(
            candidate_name
        )

        if not candidate_target:
            continue

        result = _find_v2_platform_node_by_target(
            graph,
            candidate_target,
            line_name,
        )

        if result is not None:
            return result

    if (
        not target
        and _is_line_terminus(
            line_name,
            from_station_name,
        )
    ):

        result = _find_v2_terminus_platform_node(
            graph,
            line_name,
        )

        if result is not None:
            return result

    previous_target = _normalize_station_text(
        previous_station
    )

    if previous_target:

        result = _find_v2_platform_node_by_target(
            graph,
            previous_target,
            line_name,
        )

        if result is not None:
            return result

    return None


def _load_v2_station_graph(
    station_name: str,
) -> Any | None:
    """
    V2 역사 그래프를 로드한다.

    - 환승역/분절형 그래프: 폴더 내부 JSON을 병합
    - 일반역: 단일 JSON 로드
    """

    normalized_station_name = (
        _normalize_station_text(
            station_name
        )
    )

    transfer_config = (
        TRANSFER_STATION_CONFIG.get(
            normalized_station_name
        )
    )

    if transfer_config:
        station_directory = (
            STATION_GRAPHS_V2_DIR
            / transfer_config["folder"]
        )

        return (
            build_station_graph_from_directory(
                station_directory,
                transfer_config[
                    "parent_station_code"
                ],
            )
        )

    file_name = (
        STATION_FILE_CONFIG.get(
            normalized_station_name
        )
    )

    if not file_name:
        return None

    try:
        return load_station_graph(
            file_name
        )

    except FileNotFoundError:
        return None


def _find_v2_exit_nodes(
    graph: Any,
) -> list[str]:
    """
    그래프의 EXIT / ENTRANCE 노드를 모두 찾는다.
    """

    exit_nodes: list[str] = []

    for node_id, node_data in graph.nodes(
        data=True
    ):
        node_type = str(
            node_data.get(
                "type",
                "",
            )
        ).upper()

        if node_type in {
            "EXIT",
            "ENTRANCE",
        }:
            exit_nodes.append(
                str(node_id)
            )

    return exit_nodes


def _rank_v2_internal_routes(
    graph: Any,
    start_nodes: list[str],
    end_nodes: list[str],
) -> list[dict[str, Any]]:
    """
    가능한 start/end 조합을 전부 구조적으로(실시간 미반영) 탐색해서
    edge 수가 적은 순으로 정렬한다.
    """

    candidates: list[
        dict[str, Any]
    ] = []

    for start_node in start_nodes:
        for end_node in end_nodes:
            if start_node == end_node:
                continue

            try:
                result = (
                    find_internal_route(
                        graph,
                        start_node,
                        end_node,
                    )
                )

            except ValueError:
                continue

            if (
                result.get("status")
                != "SUCCESS"
            ):
                continue

            candidates.append(
                result
            )

    candidates.sort(
        key=lambda item: len(
            item.get(
                "edge_path",
                [],
            )
        ),
    )

    return candidates


def _find_best_v2_realtime_route(
    graph: Any,
    station_name: str,
    start_nodes: list[str],
    end_nodes: list[str],
    movement: dict[str, Any],
) -> dict[str, Any] | None:
    """
    구조적으로 가장 짧은 start/end 조합부터 순서대로 실시간 상태를
    반영해 재탐색한다.

    가장 짧은 조합(예: 가장 가까운 출구)의 승강기가 고장이고 그 조합
    안에서 우회로도 없으면, 다음으로 짧은 조합(다른 출구 등)으로 넘어간다.
    모든 조합이 실패하면 구조적으로 가장 짧았던 조합의 실패 결과를
    반환한다(완전히 실패했을 때도 어떤 시도를 했는지 알 수 있도록).
    """

    ranked_candidates = (
        _rank_v2_internal_routes(
            graph=graph,
            start_nodes=start_nodes,
            end_nodes=end_nodes,
        )
    )

    if not ranked_candidates:
        return None

    first_failure: dict[str, Any] | None = None

    for candidate in ranked_candidates:

        realtime_result = (
            _attach_v2_realtime_path(
                graph=graph,
                station_name=station_name,
                start_node=candidate[
                    "start_node"
                ],
                end_node=candidate[
                    "end_node"
                ],
                movement=movement,
            )
        )

        if (
            realtime_result.get(
                "status"
            )
            == "SUCCESS"
        ):
            return realtime_result

        if first_failure is None:
            first_failure = realtime_result

    return first_failure


def _attach_v2_realtime_path(
    graph: Any,
    station_name: str,
    start_node: str,
    end_node: str,
    movement: dict[str, Any],
) -> dict[str, Any]:
    """
    확정된 start/end node 쌍에 대해 실시간 승강기 상태를 반영하여
    다시 경로를 계산한다.

    find_realtime_internal_route()가 내부적으로:
    1. 그래프의 ELEVATOR facility_id를 수집하고
    2. elevator_status_poller 캐시 기반 실시간 상태를 조회해
    3. 고장난 시설은 차단하고 경로를 다시 탐색한다.

    매핑 테이블(REALTIME_FACILITY_MAPPING)에 등록되지 않은 역/시설은
    안전하게 UNKNOWN으로 처리되고 차단되지 않는다(기존 동작과 동일).
    """

    result = find_realtime_internal_route(
        graph=graph,
        station_name=station_name,
        start_node=start_node,
        end_node=end_node,
    )

    result = dict(result)
    result["movement"] = movement

    required_facilities: list[
        dict[str, Any]
    ] = []

    for facility_status in result.get(
        "facility_statuses",
        [],
    ):
        if not isinstance(
            facility_status,
            dict,
        ):
            continue

        required_facilities.append(
            {
                "facility_id": facility_status.get(
                    "facility_id"
                ),
                "facility_type": "ELEVATOR",
                "realtime": {
                    "realtime_status": (
                        facility_status.get(
                            "realtime_status",
                            "UNKNOWN",
                        )
                    ),
                },
            }
        )

    result[
        "required_facilities"
    ] = required_facilities

    return result


def _build_v2_transfer_internal_path(
    movement: dict[str, Any],
) -> dict[str, Any] | None:
    """
    TRANSFER movement 하나를 신형 역사 그래프로 계산한다.

    실시간 승강기 운행 상태를 반영한다(고장 시 우회 재탐색).
    """

    raw_station_name = str(
        movement.get(
            "station_name"
        )
        or ""
    ).strip()

    station_name = (
        _normalize_station_text(
            movement.get(
                "station_name"
            )
        )
    )

    config = TRANSFER_STATION_CONFIG.get(
        station_name
    )

    # 아직 V2 그래프가 없는 환승역
    if not config:
        return None

    station_directory = (
        STATION_GRAPHS_V2_DIR
        / config["folder"]
    )

    graph = (
        build_station_graph_from_directory(
            station_directory,
            config[
                "parent_station_code"
            ],
        )
    )

    # 환승 전 열차가 들어온 방향
    # -> 현재 승강장 판별
    start_node = (
        _find_v2_platform_node(
            graph,
            movement.get(
                "arrival_direction_station"
            ),
            movement.get(
                "from_line"
            ),
            from_station_name=raw_station_name,
            previous_station=movement.get(
                "previous_station"
            ),
        )
    )

    # 환승 후 열차가 출발하는 방향
    # -> 환승할 승강장 판별
    end_node = (
        _find_v2_platform_node(
            graph,
            movement.get(
                "departure_direction_station"
            ),
            movement.get(
                "to_line"
            ),
            from_station_name=raw_station_name,
        )
    )

    if (
        not start_node
        or not end_node
    ):
        return {
            "status": "NODE_NOT_FOUND",
            "movement": movement,
            "start_node": start_node,
            "end_node": end_node,
            "node_path": [],
            "edge_path": [],
            "steps": [],
            "required_facilities": [],
        }

    return (
        _attach_v2_realtime_path(
            graph=graph,
            station_name=raw_station_name,
            start_node=start_node,
            end_node=end_node,
            movement=movement,
        )
    )


def _build_v2_boarding_internal_path(
    movement: dict[str, Any],
) -> dict[str, Any] | None:
    """
    BOARDING movement를 V2 그래프로 계산한다.

    EXIT -> 역사 내부 이동 -> 탑승 방향 PLATFORM
    """

    raw_station_name = str(
        movement.get(
            "station_name"
        )
        or ""
    ).strip()

    station_name = (
        _normalize_station_text(
            movement.get(
                "station_name"
            )
        )
    )

    graph = _load_v2_station_graph(
        station_name
    )

    if graph is None:
        return None

    platform_node = (
        _find_v2_platform_node(
            graph,
            movement.get(
                "departure_direction_station"
            ),
            movement.get(
                "line_name"
            ),
            from_station_name=raw_station_name,
        )
    )

    exit_nodes = (
        _find_v2_exit_nodes(
            graph
        )
    )

    if (
        not platform_node
        or not exit_nodes
    ):
        return {
            "status": "NODE_NOT_FOUND",
            "movement": movement,
            "start_node": None,
            "end_node": platform_node,
            "node_path": [],
            "edge_path": [],
            "steps": [],
            "required_facilities": [],
        }

    result = (
        _find_best_v2_realtime_route(
            graph=graph,
            station_name=raw_station_name,
            start_nodes=exit_nodes,
            end_nodes=[
                platform_node
            ],
            movement=movement,
        )
    )

    if result is None:
        return {
            "status": "PATH_NOT_FOUND",
            "movement": movement,
            "start_node": None,
            "end_node": platform_node,
            "node_path": [],
            "edge_path": [],
            "steps": [],
            "required_facilities": [],
        }

    return result


def _build_v2_alighting_internal_path(
    movement: dict[str, Any],
) -> dict[str, Any] | None:
    """
    ALIGHTING movement를 V2 그래프로 계산한다.

    하차 PLATFORM -> 역사 내부 이동 -> EXIT
    """

    raw_station_name = str(
        movement.get(
            "station_name"
        )
        or ""
    ).strip()

    station_name = (
        _normalize_station_text(
            movement.get(
                "station_name"
            )
        )
    )

    graph = _load_v2_station_graph(
        station_name
    )

    if graph is None:
        return None

    platform_node = (
        _find_v2_platform_node(
            graph,
            movement.get(
                "arrival_direction_station"
            ),
            movement.get(
                "line_name"
            ),
            from_station_name=raw_station_name,
            previous_station=movement.get(
                "previous_station"
            ),
        )
    )

    exit_nodes = (
        _find_v2_exit_nodes(
            graph
        )
    )

    if (
        not platform_node
        or not exit_nodes
    ):
        return {
            "status": "NODE_NOT_FOUND",
            "movement": movement,
            "start_node": platform_node,
            "end_node": None,
            "node_path": [],
            "edge_path": [],
            "steps": [],
            "required_facilities": [],
        }

    result = (
        _find_best_v2_realtime_route(
            graph=graph,
            station_name=raw_station_name,
            start_nodes=[
                platform_node
            ],
            end_nodes=exit_nodes,
            movement=movement,
        )
    )

    if result is None:
        return {
            "status": "PATH_NOT_FOUND",
            "movement": movement,
            "start_node": platform_node,
            "end_node": None,
            "node_path": [],
            "edge_path": [],
            "steps": [],
            "required_facilities": [],
        }

    return result


def _compute_v2_internal_paths_for_route(
    route: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    경로 하나(route)의 station_movements에 대해
    신형 V2 역사 내부 경로를 계산해 리스트로 반환한다.
    """

    station_movements = (
        route.get(
            "station_movements",
            [],
        )
    )

    if not isinstance(
        station_movements,
        list,
    ):
        return []

    internal_paths_v2: list[
        dict[str, Any]
    ] = []

    for movement in station_movements:

        if not isinstance(
            movement,
            dict,
        ):
            continue

        movement_type = str(
            movement.get(
                "movement_type",
                "",
            )
        ).upper()

        try:
            internal_path = None

            if movement_type == "BOARDING":
                internal_path = (
                    _build_v2_boarding_internal_path(
                        movement
                    )
                )

            elif movement_type == "TRANSFER":
                internal_path = (
                    _build_v2_transfer_internal_path(
                        movement
                    )
                )

            elif movement_type == "ALIGHTING":
                internal_path = (
                    _build_v2_alighting_internal_path(
                        movement
                    )
                )

            else:
                continue

            if internal_path is not None:
                internal_paths_v2.append(
                    internal_path
                )

        except Exception as error:
            # V2 경로 계산 실패 때문에
            # 기존 추천 API 전체가 실패하면 안 된다.
            internal_paths_v2.append(
                {
                    "status": "ERROR",
                    "movement": movement,
                    "message": str(error),
                    "node_path": [],
                    "edge_path": [],
                    "steps": [],
                    "required_facilities": [],
                }
            )

    return internal_paths_v2


def _has_v2_confirmed_block(
    internal_paths_v2: list[dict[str, Any]],
) -> list[str]:
    """
    V2 내부 경로 결과 중 "확정된 고장 시설 때문에 대체 경로가 없다"고
    판단된 movement의 역명을 반환한다.

    status가 SUCCESS가 아니면서 blocked_facility_ids가 채워져 있는
    경우만 확정된 차단으로 본다 — 단순히 V2 그래프에서 승강장 노드를
    못 찾은 경우(NODE_NOT_FOUND)나 V2 커버리지가 아예 없는 역은
    "확인 불가"일 뿐 "확정된 고장"이 아니므로 제외 사유로 삼지 않는다.
    """

    blocked_stations: list[str] = []

    for path in internal_paths_v2:

        if not isinstance(path, dict):
            continue

        if path.get("status") == "SUCCESS":
            continue

        blocked_facility_ids = path.get(
            "blocked_facility_ids"
        )

        if not blocked_facility_ids:
            continue

        movement = path.get("movement")

        station_name = (
            str(
                movement.get(
                    "station_name",
                    "",
                )
            )
            if isinstance(movement, dict)
            else ""
        )

        if station_name:
            blocked_stations.append(
                station_name
            )

    return list(
        dict.fromkeys(blocked_stations)
    )


def _apply_v2_confirmed_block_veto(
    recommendation_result: dict[str, Any],
) -> None:
    """
    select_best_candidate()가 고른 추천 경로에 V2 실시간 검증을 적용한다.

    V1(레거시) 그래프에 승강장 정보가 없는 역(예: 8호선 일부 역)은
    "확인 불가"로 처리되어 V1 단계에서는 걸러지지 않는다. V2가 그
    역의 실제 승강기 상태를 확정적으로(blocked_facility_ids 존재)
    "대체 경로 없음"으로 판단하면, 이 후보를 제외하고 다음 대안으로
    넘어간다. 대안도 실패하면 그다음으로, 전부 실패하면 추천 없음으로
    처리한다.

    각 후보에는 internal_paths_v2를 그대로 붙여서 화면 표시에도
    계속 쓸 수 있게 한다.
    """

    recommended_route = (
        recommendation_result.get(
            "recommended_route"
        )
    )

    alternative_routes = (
        recommendation_result.get(
            "alternative_routes",
            [],
        )
    )

    if not isinstance(
        alternative_routes,
        list,
    ):
        alternative_routes = []

    excluded_routes = (
        recommendation_result.get(
            "excluded_routes",
            [],
        )
    )

    if not isinstance(
        excluded_routes,
        list,
    ):
        excluded_routes = []

    while isinstance(
        recommended_route,
        dict,
    ):

        internal_paths_v2 = (
            _compute_v2_internal_paths_for_route(
                recommended_route
            )
        )

        recommended_route[
            "internal_paths_v2"
        ] = internal_paths_v2

        blocked_stations = (
            _has_v2_confirmed_block(
                internal_paths_v2
            )
        )

        if not blocked_stations:
            # 통과 — 이 후보를 그대로 추천한다.
            break

        # V2가 확정적으로 차단을 발견함 -> 이 후보를 제외하고
        # 다음 대안으로 넘어간다.
        station_text = ", ".join(
            blocked_stations
        )

        evaluation = recommended_route.get(
            "evaluation"
        )

        if isinstance(evaluation, dict):

            evaluation["is_available"] = False
            evaluation["is_recommended"] = False

            reasons = list(
                evaluation.get(
                    "exclusion_reasons",
                    [],
                )
            )

            reasons.append(
                "역사 내부 그래프(V1)에서는 확인되지 않았지만, "
                "실시간 승강설비 상태 확인 결과 승강설비 고장으로 "
                f"대체 내부 경로를 확보하지 못했습니다: {station_text}"
            )

            evaluation["exclusion_reasons"] = (
                list(
                    dict.fromkeys(reasons)
                )
            )

        excluded_routes.append(
            recommended_route
        )

        if not alternative_routes:
            recommended_route = None
            break

        recommended_route = (
            alternative_routes.pop(0)
        )

        next_evaluation = recommended_route.get(
            "evaluation"
        )

        if isinstance(next_evaluation, dict):
            next_evaluation["is_recommended"] = True

    recommendation_result[
        "recommended_route"
    ] = recommended_route

    recommendation_result[
        "alternative_routes"
    ] = alternative_routes

    recommendation_result[
        "excluded_routes"
    ] = excluded_routes

    if recommended_route is None:
        recommendation_result["message"] = (
            "선택한 이동 조건으로 이용 가능한 경로를 찾지 못했습니다."
        )

    summary = recommendation_result.get(
        "summary"
    )

    if isinstance(summary, dict):

        available_count = len(
            alternative_routes
        ) + (
            1
            if recommended_route is not None
            else 0
        )

        summary["available_route_count"] = (
            available_count
        )

        summary["excluded_route_count"] = len(
            excluded_routes
        )

# ==============================================================================
# 1. 좌표 기반 후보 경로 조회
# ==============================================================================

@router.post("/candidates")
async def get_route_candidates(
    request: RouteCandidateRequest,
) -> dict[str, Any]:
    """
    출발지와 목적지 좌표를 직접 입력받아
    카카오 후보 경로 전체를 반환합니다.
    """

    try:
        kakao_data = (
            await get_transit_routes(
                origin_x=request.origin_x,
                origin_y=request.origin_y,
                destination_x=request.destination_x,
                destination_y=request.destination_y,
            )
        )

        return simplify_routes(
            kakao_data
        )

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "카카오 후보 경로 조회 중 "
                f"오류가 발생했습니다: {error}"
            ),
        ) from error


# ==============================================================================
# 2. 장소명 기반 후보 경로 조회
# ==============================================================================

@router.post("/by-places")
async def get_routes_by_places(
    request: RouteByPlaceRequest,
) -> dict[str, Any]:
    """
    출발지·목적지 장소명을 좌표로 변환한 뒤
    카카오 후보 경로 전체를 반환합니다.

    각 후보에는 station_movements도 추가합니다.
    """

    geocode_service = (
        GeocodeService()
    )

    # --------------------------------------------------------------------------
    # 1. 출발지 검색
    # --------------------------------------------------------------------------

    _, origin_results = (
        await geocode_service.search_auto(
            request.origin_name
        )
    )

    if not origin_results:
        raise HTTPException(
            status_code=404,
            detail=(
                "출발지를 찾을 수 없습니다: "
                f"{request.origin_name}"
            ),
        )

    # --------------------------------------------------------------------------
    # 2. 목적지 검색
    # --------------------------------------------------------------------------

    _, destination_results = (
        await geocode_service.search_auto(
            request.destination_name
        )
    )

    if not destination_results:
        raise HTTPException(
            status_code=404,
            detail=(
                "목적지를 찾을 수 없습니다: "
                f"{request.destination_name}"
            ),
        )

    origin = (
        origin_results[0]
    )

    destination = (
        destination_results[0]
    )

    # --------------------------------------------------------------------------
    # 3. 카카오 후보 경로 조회
    # --------------------------------------------------------------------------

    try:
        kakao_data = (
            await get_transit_routes(
                origin_x=origin.longitude,
                origin_y=origin.latitude,
                destination_x=destination.longitude,
                destination_y=destination.latitude,
            )
        )

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "카카오 후보 경로 조회 중 "
                f"오류가 발생했습니다: {error}"
            ),
        ) from error

    # --------------------------------------------------------------------------
    # 4. 응답 단순화
    # --------------------------------------------------------------------------

    simplified_data = simplify_routes(
        kakao_data
    )

    routes = simplified_data["routes"]

    routes = await attach_walking_access_to_routes(
        routes=routes,

        origin_x=origin.longitude,
        origin_y=origin.latitude,

        destination_x=destination.longitude,
        destination_y=destination.latitude,

        origin_name=request.origin_name,
        destination_name=request.destination_name,

        avoid_stairs=(
            request.mobility_constraints.avoid_stairs
        ),
    )

    result = await select_best_candidate(
        routes=routes,
        mobility_constraints=(
            request.mobility_constraints.model_dump()
        ),
        route_preference=(
            request.route_preference
        ),
    )

    # --------------------------------------------------------------------------
    # 5. 승차 / 환승 / 하차 movement 추출
    # --------------------------------------------------------------------------

    routes = (
        attach_station_movements(
            routes
        )
    )

    # --------------------------------------------------------------------------
    # 6. 반환
    # --------------------------------------------------------------------------

    return {
        "origin": (
            origin.model_dump()
        ),

        "destination": (
            destination.model_dump()
        ),

        "mobility_constraints": (
            request.mobility_constraints.model_dump()
        ),

        "route_preference": (
            request.route_preference
        ),

        **simplified_data,

        "routes": (
            routes
        ),
    }


# ==============================================================================
# 3. 최종 사용자 맞춤 경로 추천
# ==============================================================================

@router.post("/recommend")
async def get_recommended_route(
    request: RouteByPlaceRequest,
) -> dict[str, Any]:
    """
    최종 사용자 맞춤 경로 추천 API.

    처리 과정:

    1. 장소명 → 좌표 변환
    2. 카카오 대중교통 후보 경로 조회
    3. 후보 경로 단순화
    4. station_movements 추출
    5. 역 내부 이동 그래프 탐색
    6. 이동 조건 제약 적용
    7. 실제 EV / ES 실시간 상태 조회
    8. 고장 시설 발견 시 해당 edge 차단
    9. 역 내부 우회 경로 재탐색
    10. Hard Barrier 검사
    11. 경로 선호도 기반 점수 계산
    12. 가장 적합한 경로 추천
    """

    geocode_service = (
        GeocodeService()
    )

    # ==========================================================================
    # 1. 출발지 검색
    # ==========================================================================

    _, origin_results = (
        await geocode_service.search_auto(
            request.origin_name
        )
    )

    if not origin_results:
        raise HTTPException(
            status_code=404,
            detail=(
                "출발지를 찾을 수 없습니다: "
                f"{request.origin_name}"
            ),
        )

    # ==========================================================================
    # 2. 목적지 검색
    # ==========================================================================

    _, destination_results = (
        await geocode_service.search_auto(
            request.destination_name
        )
    )

    if not destination_results:
        raise HTTPException(
            status_code=404,
            detail=(
                "목적지를 찾을 수 없습니다: "
                f"{request.destination_name}"
            ),
        )

    origin = (
        origin_results[0]
    )

    destination = (
        destination_results[0]
    )

    # ==========================================================================
    # 3. 카카오 후보 경로 조회
    # ==========================================================================

    try:
        kakao_data = (
            await get_transit_routes(
                origin_x=origin.longitude,
                origin_y=origin.latitude,
                destination_x=destination.longitude,
                destination_y=destination.latitude,
            )
        )

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "카카오 후보 경로 조회 중 "
                f"오류가 발생했습니다: {error}"
            ),
        ) from error

    # ==========================================================================
    # 4. 카카오 응답 단순화
    # ==========================================================================

    simplified_data = (
        simplify_routes(
            kakao_data
        )
    )

    routes = (
        simplified_data.get(
            "routes",
            [],
        )
    )

    if not routes:
        raise HTTPException(
            status_code=404,
            detail=(
                "조회된 후보 경로가 없습니다."
            ),
        )
    # ==========================================================================
    # 5. 출발지/목적지 보행 경로 연결
    # ==========================================================================

    try:
        routes = await attach_walking_access_to_routes(
            routes=routes,

            origin_x=origin.longitude,
            origin_y=origin.latitude,

            destination_x=destination.longitude,
            destination_y=destination.latitude,

            origin_name=request.origin_name,
            destination_name=request.destination_name,

            avoid_stairs=(
                request.mobility_constraints.avoid_stairs
            ),

            # TMAP 호출 전 후보 3개를
            # 사용자의 경로 선호도에 따라 선별
            route_preference=request.route_preference,
        )

    except Exception as error:
        raise HTTPException(
            status_code=502,
            detail=(
                "보행 경로 연결 중 "
                f"오류가 발생했습니다: {error}"
            ),
        ) from error

    # ==========================================================================
    # 5. station_movements 추출
    # ==========================================================================

    routes = (
        attach_station_movements(
            routes
        )
    )

    # ==========================================================================
    # 6. 최종 추천
    #
    # recommendation_service 내부에서:
    #
    # station_movements
    # → 역 내부 그래프
    # → 이동 조건 제약
    # → 실시간 EV / ES
    # → 고장 시설 우회
    # → Hard Barrier
    # → 경로 선호도 점수
    # → 최종 추천
    #
    # 순으로 처리됩니다.
    # ==========================================================================

    try:
        recommendation_result = (
            await select_best_candidate(
                routes=routes,
                mobility_constraints=(
                    request.mobility_constraints.model_dump()
                ),
                route_preference=(
                    request.route_preference
                ),
            )
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "경로 추천에 필요한 데이터 파일을 "
                f"찾을 수 없습니다: {error}"
            ),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "추천 경로 계산 중 "
                f"오류가 발생했습니다: {error}"
            ),
        ) from error

    # ==========================================================================
    # 7. 신형 역사 그래프 V2 내부 경로 추가 + 확정 차단 검증
    #
    # internal_paths_v2를 화면 표시용으로 붙이는 동시에, V1(레거시)
    # 그래프에 승강장 정보가 없어 걸러지지 않은 역(예: 8호선 일부)의
    # 확정된 승강설비 고장을 V2로 다시 검증한다. V2가 확정적으로
    # "대체 경로 없음"을 발견하면 이 후보를 제외하고 다음 대안으로
    # 넘어간다.
    # ==========================================================================

    _apply_v2_confirmed_block_veto(
        recommendation_result
    )

    # ==========================================================================
    # 8. 최종 반환
    # ==========================================================================

    return {
        "origin": (
            origin.model_dump()
        ),

        "destination": (
            destination.model_dump()
        ),

        **recommendation_result,
    }

    # ==========================================================================
    # 7. 최종 반환
    # ==========================================================================

    return {
        "origin": (
            origin.model_dump()
        ),

        "destination": (
            destination.model_dump()
        ),

        **recommendation_result,
    }


# ==============================================================================
# 4. 기본 역 내부 경로 디버그
# ==============================================================================

@router.post("/debug/path")
async def debug_station_path(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    station_movement 하나의 기본 역 내부 경로를 테스트합니다.

    payload 예시:
    {
        "movement": {...},
        "mobility_constraints": {
            "avoid_stairs": true,
            "require_elevator": true,
            "avoid_escalator": false,
            "avoid_steep_slope": false
        }
    }

    실시간 상태는 반영하지 않습니다.
    """

    movement = payload.get(
        "movement"
    )

    mobility_constraints = payload.get(
        "mobility_constraints",
        {},
    )

    if not isinstance(
        movement,
        dict,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "movement는 객체(dict) 형태여야 합니다."
            ),
        )

    if not isinstance(
        mobility_constraints,
        dict,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "mobility_constraints는 "
                "객체(dict) 형태여야 합니다."
            ),
        )

    return (
        analyze_station_movement(
            movement=movement,
            mobility_constraints=(
                mobility_constraints
            ),
        )
    )


# ==============================================================================
# 5. 실시간 시설 상태 디버그
# ==============================================================================

@router.post(
    "/debug/facility-status"
)
async def debug_facility_status(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    required_facilities에
    실제 EV / ES 실시간 운행 상태를 붙입니다.
    """

    required_facilities = (
        payload.get(
            "required_facilities",
            [],
        )
    )

    if not isinstance(
        required_facilities,
        list,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "required_facilities는 "
                "list 형태여야 합니다."
            ),
        )

    facilities_with_status = (
        attach_realtime_status_to_facilities(
            required_facilities
        )
    )

    summary = (
        summarize_route_facility_status(
            facilities_with_status
        )
    )

    return {
        "required_facilities": (
            facilities_with_status
        ),

        "facility_status_summary": (
            summary
        ),
    }


# ==============================================================================
# 6. 특정 시설 강제 차단 디버그
# ==============================================================================

@router.post(
    "/debug/path-with-blocked-facilities"
)
async def debug_path_with_blocked_facilities(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    특정 EV / ES를 강제로 차단하고
    이동 조건을 반영해 BFS를 수행합니다.
    """

    movement = payload.get(
        "movement"
    )

    blocked_edge_ids = payload.get(
        "blocked_edge_ids",
        [],
    )

    mobility_constraints = payload.get(
        "mobility_constraints",
        {},
    )

    if not isinstance(
        movement,
        dict,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "movement는 객체(dict) 형태여야 합니다."
            ),
        )

    if not isinstance(
        blocked_edge_ids,
        list,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "blocked_edge_ids는 list 형태여야 합니다."
            ),
        )

    if not isinstance(
        mobility_constraints,
        dict,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "mobility_constraints는 "
                "객체(dict) 형태여야 합니다."
            ),
        )

    blocked_set = {
        str(
            edge_id
        ).strip()
        for edge_id
        in blocked_edge_ids
        if str(
            edge_id
        ).strip()
    }

    resolved = (
        resolve_movement_nodes(
            movement
        )
    )

    if (
        resolved.get(
            "status"
        )
        != "SUCCESS"
    ):
        return {
            "status": (
                resolved.get(
                    "status",
                    "ERROR",
                )
            ),
            "mobility_constraints": (
                mobility_constraints
            ),
            "movement": (
                movement
            ),
            "blocked_edge_ids": (
                sorted(
                    blocked_set
                )
            ),
            "node_resolution": (
                resolved
            ),
        }

    station_name = str(
        resolved[
            "station_name"
        ]
    )

    start_node = (
        resolved[
            "start_node"
        ]
    )

    end_node = (
        resolved[
            "end_node"
        ]
    )

    internal_path = (
        find_shortest_internal_path(
            station_name=station_name,
            start_node_id=str(
                start_node[
                    "id"
                ]
            ),
            end_node_id=str(
                end_node[
                    "id"
                ]
            ),
            blocked_edge_ids=(
                blocked_set
            ),
            mobility_constraints=(
                mobility_constraints
            ),
        )
    )

    required_facilities = (
        extract_required_facilities(
            internal_path
        )
    )

    return {
        "status": (
            internal_path.get(
                "status"
            )
        ),
        "mobility_constraints": (
            mobility_constraints
        ),
        "movement": (
            movement
        ),
        "blocked_edge_ids": (
            sorted(
                blocked_set
            )
        ),
        "node_resolution": (
            resolved
        ),
        "start_node": (
            start_node
        ),
        "end_node": (
            end_node
        ),
        "node_path": (
            internal_path.get(
                "node_path",
                [],
            )
        ),
        "edge_count": (
            internal_path.get(
                "edge_count",
                0,
            )
        ),
        "required_facility_count": (
            len(
                required_facilities
            )
        ),
        "required_facilities": (
            required_facilities
        ),
    }


# ==============================================================================
# 7. 이동 조건 + 실시간 EV/ES 기반 내부 경로 디버그
# ==============================================================================

@router.post(
    "/debug/realtime-safe-path"
)
async def debug_realtime_safe_path(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    이동 조건과 실제 EV / ES 운행 상태를 반영하여
    역 내부 안전 경로를 계산합니다.

    운행 불가 시설이 발견되면 해당 edge를 차단하고
    자동으로 BFS를 다시 수행합니다.
    """

    movement = payload.get(
        "movement"
    )

    mobility_constraints = payload.get(
        "mobility_constraints",
        {},
    )

    if not isinstance(
        movement,
        dict,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "movement는 객체(dict) 형태여야 합니다."
            ),
        )

    if not isinstance(
        mobility_constraints,
        dict,
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "mobility_constraints는 "
                "객체(dict) 형태여야 합니다."
            ),
        )

    try:
        result = (
            find_realtime_safe_internal_path(
                movement=movement,
                mobility_constraints=(
                    mobility_constraints
                ),
            )
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "역 내부 그래프 파일을 "
                f"찾을 수 없습니다: {error}"
            ),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(
                error
            ),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "실시간 역 내부 경로 계산 중 "
                f"오류가 발생했습니다: {error}"
            ),
        ) from error

    return result

# ==============================================================================
# 버스 GBIS 식별자 매칭 디버그
# ==============================================================================

@router.post(
    "/debug/bus-identifiers"
)
async def debug_bus_identifiers(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """
    카카오 BUS step을 이용하여

    - 버스번호 -> GBIS routeId
    - 승차 정류장 -> GBIS stationId

    매칭 결과를 확인합니다.
    """

    step = payload.get("step")

    if not isinstance(step, dict):
        raise HTTPException(
            status_code=400,
            detail="step은 객체(dict) 형태여야 합니다.",
        )

    step_type = str(
        step.get("step_type", "")
    ).upper()

    if step_type != "BUS":
        raise HTTPException(
            status_code=400,
            detail="BUS step만 테스트할 수 있습니다.",
        )

    try:
        result = match_bus_step_identifiers(
            step
        )

    except FileNotFoundError as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        ) from error

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        ) from error

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=(
                "버스 식별자 매칭 중 "
                f"오류가 발생했습니다: {error}"
            ),
        ) from error

    return result

# ==============================================================================
# 실시간 저상버스 도착정보 디버그
# ==============================================================================

@router.get(
    "/debug/bus-arrival"
)
async def debug_bus_arrival(
    station_id: str,
    route_id: str,
    bus_number: str | None = None,
):
    """
    GBIS stationId와 routeId를 이용해
    해당 노선의 실시간 저상버스 도착정보를 확인합니다.
    """

    result = await get_low_floor_bus_status(
        station_id=station_id,
        route_id=route_id,
        bus_number=bus_number,
    )

    return result
@router.get("/debug/walking-route")
async def debug_walking_route(
    start_x: float,
    start_y: float,
    end_x: float,
    end_y: float,
):
    return await get_walking_route(
        start_x=start_x,
        start_y=start_y,
        end_x=end_x,
        end_y=end_y,
    )
