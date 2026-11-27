
import requests

from config.settings import SCORE_API_URL


# ==========================================
# 1. 점수 서버 기본 설정
# ==========================================

# XGBoost 점수 서버 주소
SCORE_API_TIMEOUT = 10

# 점수 예측 API 주소
SCORE_API_ENDPOINT = f"{SCORE_API_URL}/score"

# 서버 상태 확인 API 주소
SCORE_HEALTH_ENDPOINT = f"{SCORE_API_URL}/health"


# ==========================================
# 2. XGBoost 점수 예측 요청
# ==========================================

def predict_score(personality_type: str, features: dict) -> dict:
    """
    XGBoost 서버에 분석 특성을 전달하고
    호감도와 신뢰도 변화량을 받아온다.

    personality_type: 캐릭터 성격 유형 A 또는 B
    features: 총 9개의 분석 특성
    """

    # 성격 유형 확인
    if personality_type not in ["A", "B"]:
        raise ValueError("성격 유형은 A 또는 B여야 합니다.")

    # 서버에 전달할 데이터 구성
    request_data = {
        "personality_type": personality_type,
        "features": features
    }

    try:
        # XGBoost 서버에 점수 예측 요청
        response = requests.post(
            SCORE_API_ENDPOINT,
            json=request_data,
            timeout=SCORE_API_TIMEOUT
        )

        # HTTP 오류 확인
        response.raise_for_status()

        # 서버 응답 JSON 변환
        result = response.json()

        # 예측 결과 확인
        if "affection_change" not in result:
            raise ValueError("호감도 변화량이 응답에 없습니다.")

        if "trust_change" not in result:
            raise ValueError("신뢰도 변화량이 응답에 없습니다.")

        # 점수 변화량을 정수로 변환하고 -10~+10 제한
        affection_change = max(
            -10,
            min(10, int(result["affection_change"]))
        )

        trust_change = max(
            -10,
            min(10, int(result["trust_change"]))
        )

        return {
            "personality_type": personality_type,
            "affection_change": affection_change,
            "trust_change": trust_change
        }

    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            "XGBoost 점수 서버에 연결할 수 없습니다. "
            "score_server_xgboost.py가 실행 중인지 확인하세요."
        )

    except requests.exceptions.Timeout:
        raise RuntimeError("XGBoost 점수 서버 응답 시간이 초과되었습니다.")

    except requests.exceptions.HTTPError as e:
        raise RuntimeError(
            f"XGBoost 점수 서버 요청 오류: {e}"
        )

    except (KeyError, TypeError, ValueError) as e:
        raise RuntimeError(
            f"점수 예측 결과를 처리할 수 없습니다: {e}"
        )


# ==========================================
# 3. 점수 서버 상태 확인
# ==========================================

def check_score_server() -> bool:
    """
    XGBoost 서버가 정상적으로 실행 중인지 확인한다.
    """

    try:
        response = requests.get(
            SCORE_HEALTH_ENDPOINT,
            timeout=SCORE_API_TIMEOUT
        )

        response.raise_for_status()

        result = response.json()

        return result.get("status") == "ok"

    except requests.exceptions.RequestException:
        return False
