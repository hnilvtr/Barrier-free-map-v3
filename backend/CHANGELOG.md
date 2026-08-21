# 변경 로그 — 승강기 실시간 상태 반영 (2026-08-21)

역사 내부 승강기 실시간 운행 상태를 정부 API 폴링 기반으로 전환하고, V1(레거시)·V2 경로 시스템 양쪽에 반영한 작업 기록.

## 1. `app/services/elevator_status_poller.py` — 신규 생성

**목적**: 역별 승강기 실시간 운행 상태를 사전에 저장해둔 JSON 스냅샷 대신, 정부 API(일련번호 단건 조회)를 백그라운드에서 직접 폴링해 항상 최신 상태를 유지하기 위함.

**내용**:
- `REALTIME_FACILITY_MAPPING`에 등록된 모든 장비의 일련번호를 대상으로 `poll_once()`가 정부 API(`getElevatorViewM`)를 직접 호출
- 동시 3개 / 0.3초 간격으로 페이싱(실측한 초당 요청 제한 대응)
- 장비 하나 실패가 전체 폴링을 죽이지 않도록 예외를 넓게 흡수(`except Exception`)
- 결과를 `station_name -> [장비 목록]` 형태의 인메모리 캐시로 저장, `get_station_devices()`로 조회
- 이벤트 로깅(diff 추적) 없이 순수 폴링만 수행 — 최신성은 폴링 주기로만 보장

## 2. `app/services/facility_status_service.py` — 수정

**목적**: 실시간 상태 조회를 JSON 스냅샷/구 라이브 API 방식에서 폴링 캐시 기반으로 전환, 더 이상 안 쓰는 코드 제거, 실제 버그 수정.

**내용**:
- `get_station_facility_data()`를 폴링 캐시(`elevator_status_poller.get_station_devices()`)를 읽도록 재작성
- 더 이상 안 쓰는 `load_station_facilities_from_json()`, `fetch_station_facilities()`, `get_station_json_path()`, `normalize_station_name()`과 관련 import(`json`, `os`, `Path`, `requests`, `dotenv`, `unquote`) 삭제
- **버그 수정**: `normalize_operation_status()`가 AVAILABLE 키워드를 먼저 검사해서, `"운행중지"`가 `"운행중"`을 부분 포함한다는 이유로 실제 고장 장비를 AVAILABLE로 오판정하던 문제 — UNAVAILABLE 키워드를 먼저 검사하도록 순서 변경 (실측으로 발견: 남한산성입구역 2022967)

## 3. `app/main.py` — 수정

**목적**: 폴러를 FastAPI 앱 생명주기에 연결.

**내용**: `lifespan`에서 서버가 트래픽을 받기 전 `poll_once()` 1회 실행(콜드스타트 방지) 후 `run_forever()` 백그라운드 태스크 시작, 종료 시 태스크 취소.

## 4. `app/data/realtime_facility_mapping.py` — 대폭 확장

**목적**: 실시간 매핑 데이터 정비 및 커버리지 확장.

**내용**:
- 출처 불명이던 에스컬레이터 4개 삭제
- `역사별_승강기_통합(번호).json`(9개 역 코드) + V2 그래프 `facility_id`(=실제 일련번호) 대조로 **정자·야탑·서현·수내·판교·이매 6개 역, 40개 장비** 매핑
- 나머지 12개 역은 라이브 API 표본 검증(`buldNm` 필드로 역명 실제 일치 확인) 후 **총 18개 역, 85개 장비**로 확장(단대오거리·가천대·남한산성입구·남위례·오리·산성·성남·신흥·수진·태평·미금·모란)
- 이매역 "야탑역 방면" 장비번호 오타(2150934→2050934, 사용자 확인) 수정

## 5. `app/station_routing_v2/realtime_route_service.py` — 재작성

**목적**: V2 실시간 경로 계산이 "역 전체 엘리베이터"를 검사해서, 경로와 무관한 고장 시설이 상태/차단 정보를 오염시키던 문제 해결.

**내용**: `find_realtime_internal_route()`를 레거시(`station_path_service`)와 같은 "차단 없이 탐색 → 실제 경로가 쓰는 시설만 검사 → 고장이면 그것만 차단 후 재탐색(최대 10회)" 방식으로 재작성. 역 전체를 스캔하던 `collect_elevator_facility_ids()` 삭제.

## 6. `app/api/route.py` — 다수 수정

**목적**: V2(boarding/alighting/transfer) 경로에 실시간 반영 연결 + 방향 판별 관련 버그 3종 수정.

**내용**:
- `_attach_v2_realtime_path()` 신설로 V1/V2 실시간 로직 연결(하드코딩된 `"UNKNOWN"` 제거)
- `_find_best_v2_realtime_route()`: 구조적으로 가장 짧은 출구부터 시도하다 고장이면 다음 후보 출구로 자동 전환
- **판교역 BOARDING 버그**: 카카오의 "바로 다음 역"과 V2 그래프 라벨(더 먼 대표 지명)이 안 맞던 문제 → `LINE_STATION_ORDERS` 기반 체인 폴백 추가
- **8호선 등 ALIGHTING 버그**: `previous_station`(카카오가 정확히 주는 값) 폴백 추가
- **종착역 오매칭 버그**(모란역이 실제로는 "수진 방면"이라는 틀린 승강장에 조용히 매칭되던 것) → `_is_line_terminus()` + `_find_v2_terminus_platform_node()`로 "종점/종착" 라벨을 previous_station보다 먼저 시도하도록 우선순위 조정

## 7. `app/services/movement_extraction_service.py` — 수정

**목적**: 8호선 방향 판별 지원 추가(6번 항목의 체인 폴백이 동작하려면 필요).

**내용**: `LINE_STATION_ORDERS`에 `"8호선": ["남위례역","산성역","남한산성입구역","단대오거리역","신흥역","수진역","모란역"]` 추가.

## 8. `app/api/route.py` — 추가 수정 (V1이 놓친 확정 고장을 V2로 보완)

**목적**: V1(레거시) 그래프에 승강장 정보 자체가 없는 역(예: 산성역·남한산성입구역 — PLATFORM 노드 0개)은 "확인 불가"로 처리되어 실제 추천 필터링(`select_best_candidate`)에서 그냥 통과되고 있었음. 화면 표시용으로만 쓰이던 V2의 정확한 실시간 판단을 실제 추천 결정에도 반영.

**내용**:
- `_attach_v2_internal_paths()`를 `_compute_v2_internal_paths_for_route()`(경로 하나 계산, 재사용용)로 분리
- `_has_v2_confirmed_block()`: V2 결과 중 `status != SUCCESS`이면서 `blocked_facility_ids`가 채워진(=확정된 실시간 고장) 경우만 걸러냄 — 단순 `NODE_NOT_FOUND`(V2 그래프 매칭 실패)나 V2 커버리지 자체가 없는 경우는 "확인 불가"로 보고 제외 사유로 삼지 않음(V1과 동일한 "모르면 차단 안 함" 원칙 유지)
- `_apply_v2_confirmed_block_veto()`: 추천된 경로에서 확정 차단이 발견되면 그 후보를 제외 처리하고 다음 대안으로 교체, 통과할 때까지(또는 대안 소진 시까지) 반복. 기존 `_attach_v2_internal_paths()` 호출부를 이걸로 교체
- 실측 확인: 남한산성입구역 방향 승강기(2022967)가 실제로 고장인 요청에서 해당 후보만 정확히 제외되고, 다른 대안이 있으면 그걸로 정상 추천됨

## 검증 방식

- 매 단계마다 실제 정부 API를 라이브로 호출해 검증(오프라인 매칭이 아니라 `buldNm`·`elvtrStts` 실측값으로 확인)
- 전체 파이프라인(`/routes/recommend`)을 카카오·TMAP·Gemini까지 포함해 다양한 이동조건·경로선호도·역 조합으로 반복 실행, 크래시 여부 확인
- 회귀 확인: 새 수정이 기존에 정상 동작하던 케이스를 깨뜨리지 않는지 매번 재확인
