from __future__ import annotations

from typing import Any


REALTIME_FACILITY_MAPPING: dict[str, dict[str, Any]] = {

    # ==========================================================================
    # 정자역 - 수인분당선 ELEVATOR
    # ==========================================================================

    # 2번 출구
    "JGJ_01_EV_001": {
        "station_name": "정자역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2056151",
        "mapping_status": "CONFIRMED",
    },

    # 4번 출구
    "JGJ_01_EV_002": {
        "station_name": "정자역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2056152",
        "mapping_status": "CONFIRMED",
    },

    # 미금 방향(하행) B2 ↔ B1
    "JGJ_01_EV_003": {
        "station_name": "정자역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2050987",
        "mapping_status": "CONFIRMED",
    },

    # 수내 방향(상행) B2 ↔ B1
    "JGJ_01_EV_004": {
        "station_name": "정자역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2050986",
        "mapping_status": "CONFIRMED",
    },



    # ==========================================================================
    # 정자역 - 신분당선 ELEVATOR
    # ==========================================================================

    # 6번 출구
    "JGJ_02_EV_001": {
        "station_name": "정자역",
        "line_name": "신분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2051672",
        "mapping_status": "CONFIRMED",
    },

    # 미금 방향 환승 연결
    "JGJ_02_EV_002": {
        "station_name": "정자역",
        "line_name": "신분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2051675",
        "mapping_status": "CONFIRMED",
    },

    # 수내 방향 환승 연결
    "JGJ_02_EV_003": {
        "station_name": "정자역",
        "line_name": "신분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2051676",
        "mapping_status": "CONFIRMED",
    },

    # 판교 방향 B3 ↔ B2
    "JGJ_02_EV_004": {
        "station_name": "정자역",
        "line_name": "신분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2051674",
        "mapping_status": "CONFIRMED",
    },

    # 미금 방향 B3 ↔ B2
    "JGJ_02_EV_005": {
        "station_name": "정자역",
        "line_name": "신분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2051673",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 야탑역 - 수인분당선 ELEVATOR
    #
    # 출처: 역사별_승강기_통합(번호).json (KR/K1/K226) — V2 그래프(yatap.json)의
    # facility_id와 elevatorNo가 그대로 일치함을 직접 확인함.
    # ==========================================================================

    # 1·2번 출입구 (지상 ↔ B1)
    "YTP_EV_001": {
        "station_name": "야탑역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2050607",
        "mapping_status": "CONFIRMED",
    },

    # 3·4번 출입구 (지상 ↔ B1)
    "YTP_EV_002": {
        "station_name": "야탑역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2050608",
        "mapping_status": "CONFIRMED",
    },

    # 이매 방면 승강장 (B1 ↔ B2)
    "YTP_EV_003": {
        "station_name": "야탑역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2050605",
        "mapping_status": "CONFIRMED",
    },

    # 모란 방면 승강장 (B1 ↔ B2)
    "YTP_EV_004": {
        "station_name": "야탑역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2050606",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 서현역 - 수인분당선 ELEVATOR
    #
    # 출처: 역사별_승강기_통합(번호).json (KR/K1/K228) — V2 그래프(seohyeon.json)와
    # facility_id 일치 확인.
    # ==========================================================================

    # 1번 출입구 (지상 ↔ B1)
    "SHN_EV_001": {
        "station_name": "서현역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2115488",
        "mapping_status": "CONFIRMED",
    },

    # 이매 방면 승강장 (B1 ↔ B2)
    "SHN_EV_002": {
        "station_name": "서현역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2050935",
        "mapping_status": "CONFIRMED",
    },

    # 수내 방면 승강장 (B1 ↔ B2)
    "SHN_EV_003": {
        "station_name": "서현역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2050936",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 수내역 - 수인분당선 ELEVATOR
    #
    # 출처: 역사별_승강기_통합(번호).json (KR/K1/K229) — V2 그래프(sunae.json)와
    # facility_id 일치 확인.
    # ==========================================================================

    # 1번 출입구 (지상 ↔ B1)
    "SNA_EV_001": {
        "station_name": "수내역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2126115",
        "mapping_status": "CONFIRMED",
    },

    # 정자 방면 승강장 (B1 ↔ B2)
    "SNA_EV_002": {
        "station_name": "수내역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2050938",
        "mapping_status": "CONFIRMED",
    },

    # 서현 방면 승강장 (B1 ↔ B2)
    "SNA_EV_003": {
        "station_name": "수내역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2050937",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 판교역 - 신분당선 ELEVATOR
    #
    # 출처: 역사별_승강기_통합(번호).json (DX/D1/4311) — V2 그래프
    # (pangyo/pangyo_sinbundang_graph.json)와 facility_id 일치 확인.
    # ==========================================================================

    # 1번 출입구 (지상 ↔ B1 ↔ B2)
    "PYO_SD_EV_001": {
        "station_name": "판교역",
        "line_name": "신분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2051683",
        "mapping_status": "CONFIRMED",
    },

    # 3번 출입구 (지상 ↔ B1 ↔ B2)
    "PYO_SD_EV_002": {
        "station_name": "판교역",
        "line_name": "신분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2051684",
        "mapping_status": "CONFIRMED",
    },

    # 정자 방면 승강장 (B2 ↔ B3)
    "PYO_SD_EV_003": {
        "station_name": "판교역",
        "line_name": "신분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2051685",
        "mapping_status": "CONFIRMED",
    },

    # 청계산입구 방면 승강장 (B2 ↔ B3)
    "PYO_SD_EV_004": {
        "station_name": "판교역",
        "line_name": "신분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2051686",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 판교역 - 경강선 ELEVATOR
    #
    # 출처: 역사별_승강기_통합(번호).json (KR/K5/K409) — V2 그래프
    # (pangyo/pangyo_gyeonggang_graph.json)와 facility_id 일치 확인.
    # ==========================================================================

    # 이매역 방면 승강장 (B3 ↔ B4)
    "PYO_GG_EV_001": {
        "station_name": "판교역",
        "line_name": "경강선",
        "facility_type": "ELEVATOR",
        "device_no": "2168132",
        "mapping_status": "CONFIRMED",
    },

    # 당역종착(판교 착발) 승강장 (B3 ↔ B4)
    "PYO_GG_EV_002": {
        "station_name": "판교역",
        "line_name": "경강선",
        "facility_type": "ELEVATOR",
        "device_no": "2168131",
        "mapping_status": "CONFIRMED",
    },

    # 이매역 방면 승강장, 별도 출입문 (B3 ↔ B4)
    "PYO_GG_EV_003": {
        "station_name": "판교역",
        "line_name": "경강선",
        "facility_type": "ELEVATOR",
        "device_no": "2168133",
        "mapping_status": "CONFIRMED",
    },

    # 당역종착(판교 착발) 승강장, 별도 출입문 (B3 ↔ B4)
    "PYO_GG_EV_004": {
        "station_name": "판교역",
        "line_name": "경강선",
        "facility_type": "ELEVATOR",
        "device_no": "2168134",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 이매역 - 수인분당선 ELEVATOR
    #
    # 출처: 역사별_승강기_통합(번호).json (KR/K1/K227) — V2 그래프
    # (imae/imae_suinbundang_graph.json)와 facility_id 일치 확인.
    #
    # 참고: 원본 데이터에는 "야탑역 방면 승강장" 장비번호가 2150934로
    # 적혀 있었으나, 실제로는 V2 그래프(imae_suinbundang_graph.json)의
    # facility_id인 2050934가 맞는 값으로 확인됨(2026-08-21).
    # ==========================================================================

    # 3번 출구 / 서현방향 대합실 (지상 ↔ B1)
    "IMA_SB_EV_001": {
        "station_name": "이매역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2141631",
        "mapping_status": "CONFIRMED",
    },

    # 9번 출입구 / 야탑방향 연결통로 (지상 ↔ B1)
    "IMA_SB_EV_002": {
        "station_name": "이매역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2141639",
        "mapping_status": "CONFIRMED",
    },

    # 서현역 방면 승강장 (B1 ↔ B2)
    "IMA_SB_EV_003": {
        "station_name": "이매역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2141638",
        "mapping_status": "CONFIRMED",
    },

    # 야탑역 방면 승강장 (B1 ↔ B2)
    "IMA_SB_EV_004": {
        "station_name": "이매역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2050934",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 이매역 - 경강선 ELEVATOR
    #
    # 출처: 역사별_승강기_통합(번호).json (KR/K5/K411) — V2 그래프
    # (imae/imae_gyeonggang_graph.json)와 facility_id 일치 확인.
    # ==========================================================================

    # 6번 출입구 (지상 ↔ B2)
    "IMA_GG_EV_001": {
        "station_name": "이매역",
        "line_name": "경강선",
        "facility_type": "ELEVATOR",
        "device_no": "2155248",
        "mapping_status": "CONFIRMED",
    },

    # 5번 출입구 (지상 ↔ B2)
    "IMA_GG_EV_002": {
        "station_name": "이매역",
        "line_name": "경강선",
        "facility_type": "ELEVATOR",
        "device_no": "2155256",
        "mapping_status": "CONFIRMED",
    },

    # 판교행 승강장 (B2 ↔ B3)
    "IMA_GG_EV_003": {
        "station_name": "이매역",
        "line_name": "경강선",
        "facility_type": "ELEVATOR",
        "device_no": "2155255",
        "mapping_status": "CONFIRMED",
    },

    # 삼동행 승강장 (B2 ↔ B3)
    "IMA_GG_EV_004": {
        "station_name": "이매역",
        "line_name": "경강선",
        "facility_type": "ELEVATOR",
        "device_no": "2155249",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 이매역 - 환승간선 (수인분당선 ↔ 경강선) ELEVATOR
    #
    # 출처: 역사별_승강기_통합(번호).json (KR/K5/K411) — V2 그래프
    # (imae/imae_transfer_trunk_graph.json)와 facility_id 일치 확인.
    # ==========================================================================

    # 대합실 중앙계단 (B1 ↔ B2)
    "IMA_TRANSFER_EV_001": {
        "station_name": "이매역",
        "line_name": "환승통로(수인분당선 ↔ 경강선)",
        "facility_type": "ELEVATOR",
        "device_no": "2155252",
        "mapping_status": "CONFIRMED",
    },

    # 수원인천행 환승구간 ↔ 삼동행 승강장 (B2 ↔ B3)
    "IMA_TRANSFER_EV_002": {
        "station_name": "이매역",
        "line_name": "환승통로(수인분당선 ↔ 경강선)",
        "facility_type": "ELEVATOR",
        "device_no": "2155251",
        "mapping_status": "CONFIRMED",
    },

    # 왕십리행 환승구간 ↔ 삼동행 승강장 (B2 ↔ B3)
    "IMA_TRANSFER_EV_003": {
        "station_name": "이매역",
        "line_name": "환승통로(수인분당선 ↔ 경강선)",
        "facility_type": "ELEVATOR",
        "device_no": "2155250",
        "mapping_status": "CONFIRMED",
    },

    # 수원인천행 환승구간 ↔ 판교행 승강장 (B2 ↔ B3)
    "IMA_TRANSFER_EV_004": {
        "station_name": "이매역",
        "line_name": "환승통로(수인분당선 ↔ 경강선)",
        "facility_type": "ELEVATOR",
        "device_no": "2155253",
        "mapping_status": "CONFIRMED",
    },

    # 왕십리행 환승구간 ↔ 판교행 승강장 (B2 ↔ B3)
    "IMA_TRANSFER_EV_005": {
        "station_name": "이매역",
        "line_name": "환승통로(수인분당선 ↔ 경강선)",
        "facility_type": "ELEVATOR",
        "device_no": "2155254",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 단대오거리역 - 8호선 ELEVATOR
    #
    # 출처: V2 그래프(dandaeogeori.json)의 facility_id.
    # 표본(2116586) 라이브 조회로 buldNm="서울교통공사 단대오거리역" 확인.
    # ==========================================================================

    # 4번 출입구 (지상 ↔ B1)
    "DDG_EV_001": {
        "station_name": "단대오거리역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2116588",
        "mapping_status": "CONFIRMED",
    },

    # 남한산성입구 방면 승강장 (B1 ↔ B3)
    "DDG_EV_002": {
        "station_name": "단대오거리역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2116586",
        "mapping_status": "CONFIRMED",
    },

    # 신흥 방면 승강장 (B1 ↔ B3)
    "DDG_EV_003": {
        "station_name": "단대오거리역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2116587",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 가천대역 - 수인분당선 ELEVATOR
    #
    # 출처: V2 그래프(gachon_univ.json)의 facility_id.
    # 표본(2051156) 라이브 조회로 buldNm="한국철도공사 분당선 가천대역" 확인.
    # ==========================================================================

    # 2번 출입구 (지상 ↔ B1)
    "GCU_EV_001": {
        "station_name": "가천대역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2146048",
        "mapping_status": "CONFIRMED",
    },

    # 4/5번 출입구 (지상 ↔ B1)
    "GCU_EV_002": {
        "station_name": "가천대역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2146049",
        "mapping_status": "CONFIRMED",
    },

    # 태평 방면 승강장 (B1 ↔ B2)
    "GCU_EV_003": {
        "station_name": "가천대역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2051156",
        "mapping_status": "CONFIRMED",
    },

    # 복정 방면 승강장 (B1 ↔ B2)
    "GCU_EV_004": {
        "station_name": "가천대역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2051157",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 남한산성입구역 - 8호선 ELEVATOR
    #
    # 출처: V2 그래프(namhansanseong.json)의 facility_id.
    # 표본(2022967) 라이브 조회로 buldNm="서울교통공사8호선남한산성입구역" 확인
    # (해당 장비는 조회 시점 기준 실제 운행중지/불합격 상태였음).
    # ==========================================================================

    # 3번 출입구 (지상 ↔ B2)
    "NHS_EV_001": {
        "station_name": "남한산성입구역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2231773",
        "mapping_status": "CONFIRMED",
    },

    # 산성 방면 승강장 (B2 ↔ B3)
    "NHS_EV_002": {
        "station_name": "남한산성입구역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2022967",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 남위례역 - 8호선 ELEVATOR
    #
    # 출처: V2 그래프(namwirye.json)의 facility_id.
    # 표본(2249471) 라이브 조회로 buldNm="서울교통공사8호선 남위례역" 확인.
    # ==========================================================================

    # 5번 출입구 (지상 ↔ 2F)
    "NWR_EV_001": {
        "station_name": "남위례역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2249471",
        "mapping_status": "CONFIRMED",
    },

    # 모란 방면 승강장 (지상 ↔ 2F)
    "NWR_EV_002": {
        "station_name": "남위례역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2249472",
        "mapping_status": "CONFIRMED",
    },

    # 육교 엘리베이터 1-1 (지상 ↔ 2F 육교)
    "NWR_EV_003": {
        "station_name": "남위례역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2253164",
        "mapping_status": "CONFIRMED",
    },

    # 육교 엘리베이터 1-2 (지상 ↔ 2F 육교)
    "NWR_EV_004": {
        "station_name": "남위례역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2253165",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 오리역 - 수인분당선 ELEVATOR
    #
    # 출처: V2 그래프(ori.json)의 facility_id.
    # 표본(2056548) 라이브 조회로 buldNm="한국철도공사 분당선 오리역" 확인.
    # ==========================================================================

    # 6번 출입구 (지상 ↔ B1)
    "ORI_EV_001": {
        "station_name": "오리역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2056548",
        "mapping_status": "CONFIRMED",
    },

    # 죽전 방면 승강장 (B1 ↔ B2)
    "ORI_EV_002": {
        "station_name": "오리역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2056549",
        "mapping_status": "CONFIRMED",
    },

    # 미금 방면 승강장 (B1 ↔ B2)
    "ORI_EV_003": {
        "station_name": "오리역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2056550",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 산성역 - 8호선 ELEVATOR
    #
    # 출처: V2 그래프(sanseong.json)의 facility_id.
    # 표본(2024722) 라이브 조회로 buldNm="서울교통공사8호선산성역" 확인.
    # ==========================================================================

    # 3번 출입구 (지상 ↔ B1)
    "SNS_EV_001": {
        "station_name": "산성역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2075288",
        "mapping_status": "CONFIRMED",
    },

    # 경사 엘리베이터 (B1 ↔ B2 대합실)
    "SNS_EV_002": {
        "station_name": "산성역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2276758",
        "mapping_status": "CONFIRMED",
    },

    # 남위례 방면 경사 엘리베이터 (B2 ↔ B3 승강장)
    "SNS_EV_003": {
        "station_name": "산성역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2024722",
        "mapping_status": "CONFIRMED",
    },

    # 남한산성입구 방면 경사 엘리베이터 (B2 ↔ B3 승강장)
    "SNS_EV_004": {
        "station_name": "산성역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2024723",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 성남역 - 경강선 ELEVATOR
    #
    # 출처: V2 그래프(seongnam.json)의 facility_id.
    # 표본(2268765) 라이브 조회로 buldNm="성남역 경강선" 확인.
    # ==========================================================================

    # 3번 출입구 (지상 ↔ B2 대합실)
    "SNG_EV_001": {
        "station_name": "성남역",
        "line_name": "경강선",
        "facility_type": "ELEVATOR",
        "device_no": "2268789",
        "mapping_status": "CONFIRMED",
    },

    # 5번 출입구 (지상 ↔ B2 대합실)
    "SNG_EV_002": {
        "station_name": "성남역",
        "line_name": "경강선",
        "facility_type": "ELEVATOR",
        "device_no": "2268769",
        "mapping_status": "CONFIRMED",
    },

    # 판교 방면 승강장 (B2 ↔ B3)
    "SNG_EV_003": {
        "station_name": "성남역",
        "line_name": "경강선",
        "facility_type": "ELEVATOR",
        "device_no": "2268772",
        "mapping_status": "CONFIRMED",
    },

    # 이매 방면 승강장 (B2 ↔ B3)
    "SNG_EV_004": {
        "station_name": "성남역",
        "line_name": "경강선",
        "facility_type": "ELEVATOR",
        "device_no": "2268765",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 신흥역 - 8호선 ELEVATOR
    #
    # 출처: V2 그래프(sinheung.json)의 facility_id.
    # 표본(2022969) 라이브 조회로 buldNm="서울교통공사 8호선 신흥역" 확인.
    #
    # 참고: V2 그래프의 ELEVATOR edge 3개 중 1개는 facility_id가 None으로
    # 비어 있어 매핑할 수 없습니다.
    # ==========================================================================

    # 단대오거리 방면 승강장 (지상 ↔ B2)
    "SHH_EV_001": {
        "station_name": "신흥역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2022969",
        "mapping_status": "CONFIRMED",
    },

    # 수진 방면 승강장 (지상 ↔ B2)
    "SHH_EV_002": {
        "station_name": "신흥역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2022970",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 수진역 - 8호선 ELEVATOR
    #
    # 출처: V2 그래프(sujin.json)의 facility_id.
    # 표본(2116589) 라이브 조회로 buldNm="서울교통공사 8호선 수진역" 확인.
    # ==========================================================================

    # 3번 출입구 (지상 ↔ B1 대합실)
    "SUJ_EV_001": {
        "station_name": "수진역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2212625",
        "mapping_status": "CONFIRMED",
    },

    # 신흥 방면 승강장 (B1 ↔ B2)
    "SUJ_EV_002": {
        "station_name": "수진역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2116589",
        "mapping_status": "CONFIRMED",
    },

    # 모란 방면 승강장 (B1 ↔ B2)
    "SUJ_EV_003": {
        "station_name": "수진역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2116590",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 태평역 - 수인분당선 ELEVATOR
    #
    # 출처: V2 그래프(taepyeong.json)의 facility_id.
    # 표본(2054926) 라이브 조회로 buldNm="한국철도공사 수인분당선 태평역" 확인.
    # ==========================================================================

    # 5번 출입구 (지상 ↔ B1)
    "TPY_EV_001": {
        "station_name": "태평역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2054928",
        "mapping_status": "CONFIRMED",
    },

    # 가천대 방면 승강장 (B1 ↔ B2)
    "TPY_EV_002": {
        "station_name": "태평역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2054926",
        "mapping_status": "CONFIRMED",
    },

    # 모란 방면 승강장 (B1 ↔ B2)
    "TPY_EV_003": {
        "station_name": "태평역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2054927",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 미금역 - 신분당선 · 수인분당선 (공용 포함) ELEVATOR
    #
    # 출처: V2 그래프(migeum/migeum_sinbundang_graph.json,
    # migeum/migeum_suinbundang_graph.json)의 facility_id — 두 파일에 겹치는
    # 장비는 두 노선이 공용으로 쓰는 환승 엘리베이터입니다.
    # 표본(2056582) 라이브 조회로 buldNm="한국철도공사 수인분당선 미금역" 확인.
    # ==========================================================================

    # 대합실 공용 (B1) — 신분당선/수인분당선 공용
    "MIG_EV_001": {
        "station_name": "미금역",
        "line_name": "신분당선 · 수인분당선 공용",
        "facility_type": "ELEVATOR",
        "device_no": "2056582",
        "mapping_status": "CONFIRMED",
    },

    # 대합실 공용 (B1) — 신분당선/수인분당선 공용
    "MIG_EV_002": {
        "station_name": "미금역",
        "line_name": "신분당선 · 수인분당선 공용",
        "facility_type": "ELEVATOR",
        "device_no": "2195144",
        "mapping_status": "CONFIRMED",
    },

    # B2 승강장 접근 — 신분당선/수인분당선 공용
    "MIG_EV_003": {
        "station_name": "미금역",
        "line_name": "신분당선 · 수인분당선 공용",
        "facility_type": "ELEVATOR",
        "device_no": "2195141",
        "mapping_status": "CONFIRMED",
    },

    # B2 승강장 접근 — 신분당선/수인분당선 공용
    "MIG_EV_004": {
        "station_name": "미금역",
        "line_name": "신분당선 · 수인분당선 공용",
        "facility_type": "ELEVATOR",
        "device_no": "2195140",
        "mapping_status": "CONFIRMED",
    },

    # 수인분당선 측 B2 승강장 접근
    "MIG_EV_005": {
        "station_name": "미금역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2056584",
        "mapping_status": "CONFIRMED",
    },

    # 수인분당선 측 B2 승강장 접근
    "MIG_EV_006": {
        "station_name": "미금역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2056583",
        "mapping_status": "CONFIRMED",
    },

    # 신분당선 측 B5 승강장 접근
    "MIG_EV_007": {
        "station_name": "미금역",
        "line_name": "신분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2195143",
        "mapping_status": "CONFIRMED",
    },

    # 신분당선 측 B5 승강장 접근
    "MIG_EV_008": {
        "station_name": "미금역",
        "line_name": "신분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2195142",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 모란역 - 8호선 ELEVATOR
    #
    # 출처: V2 그래프(moran/moran_line8_graph.json)의 facility_id.
    # 표본(2116583) 라이브 조회로 buldNm="서울교통공사8호선모란역" 확인.
    # ==========================================================================

    # 지상 ↔ B1
    "MOR_L8_EV_001": {
        "station_name": "모란역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2116585",
        "mapping_status": "CONFIRMED",
    },

    # B1 ↔ B2
    "MOR_L8_EV_002": {
        "station_name": "모란역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2116583",
        "mapping_status": "CONFIRMED",
    },

    # B2 ↔ B3
    "MOR_L8_EV_003": {
        "station_name": "모란역",
        "line_name": "8호선",
        "facility_type": "ELEVATOR",
        "device_no": "2116584",
        "mapping_status": "CONFIRMED",
    },


    # ==========================================================================
    # 모란역 - 수인분당선 ELEVATOR
    #
    # 출처: V2 그래프(moran/moran_suinbundang_graph.json)의 facility_id.
    # 표본(2050878) 라이브 조회로 buldNm="한국철도공사 분당선 모란역" 확인.
    # ==========================================================================

    # 승강장 접근 (B2)
    "MOR_SB_EV_001": {
        "station_name": "모란역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2050879",
        "mapping_status": "CONFIRMED",
    },

    # 승강장 접근 (B2)
    "MOR_SB_EV_002": {
        "station_name": "모란역",
        "line_name": "수인분당선",
        "facility_type": "ELEVATOR",
        "device_no": "2050878",
        "mapping_status": "CONFIRMED",
    },
}


def get_realtime_facility_mapping(
    edge_id: str,
) -> dict[str, Any] | None:
    """
    내부 그래프 edge_id에 대응하는
    실시간 장비 매핑 정보를 반환합니다.
    """

    return REALTIME_FACILITY_MAPPING.get(
        edge_id
    )


def get_realtime_device_no(
    edge_id: str,
) -> str | None:
    """
    edge_id에 대응하는 실시간 API 장비번호를 반환합니다.
    """

    mapping = (
        get_realtime_facility_mapping(
            edge_id
        )
    )

    if not mapping:
        return None

    device_no = mapping.get(
        "device_no"
    )

    if not device_no:
        return None

    return str(
        device_no
    )