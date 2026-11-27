
# ==========================================
# XGBoost 점수 예측 서버
# ==========================================
# 주요 기능
# 1. A/B 유형별 XGBoost 모델 로딩
# 2. 호감도 및 신뢰도 변화량 예측
# 3. 예측 결과를 FastAPI로 반환
# ==========================================

from pathlib import Path
from typing import Literal

import joblib
import pandas as pd

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


# ==========================================
# 1. 경로 및 기본 설정
# ==========================================

# 현재 파일 위치
BASE_DIR = Path(__file__).resolve().parent

# 기존 프로젝트의 모델 저장 경로
MODEL_DIR = BASE_DIR.parent / "model" / "saved_models"

# 점수 변화량 제한
MIN_SCORE_CHANGE = -10
MAX_SCORE_CHANGE = 10


# ==========================================
# 2. XGBoost 입력 특성
# ==========================================

FEATURE_COLUMNS = [
    "preference_match",
    "dislike_match",
    "empathy",
    "interest",
    "sincerity",
    "context_match",
    "repetition_count",
    "previous_affection",
    "previous_trust"
]


# ==========================================
# 3. FastAPI 생성
# ==========================================

app = FastAPI(
    title="HEARTLINE Score Server",
    description="XGBoost 호감도 및 신뢰도 예측 서버",
    version="1.0.0"
)


# ==========================================
# 4. 모델 파일 경로
# ==========================================

MODEL_PATHS = {
    "A": {
        "affection": MODEL_DIR / "type_a_affection_model.pkl",
        "trust": MODEL_DIR / "type_a_trust_model.pkl"
    },
    "B": {
        "affection": MODEL_DIR / "type_b_affection_model.pkl",
        "trust": MODEL_DIR / "type_b_trust_model.pkl"
    }
}


# ==========================================
# 5. XGBoost 모델 로딩
# ==========================================

MODELS = {}


def load_models():
    """
    A/B 유형별 호감도 및 신뢰도 모델을 로딩한다.
    """

    for personality_type, model_paths in MODEL_PATHS.items():

        MODELS[personality_type] = {}

        for score_type, model_path in model_paths.items():

            if not model_path.exists():
                raise FileNotFoundError(
                    f"모델 파일을 찾을 수 없습니다: {model_path}"
                )

            MODELS[personality_type][score_type] = joblib.load(
                model_path
            )

            print(
                f"[모델 로딩 완료] {personality_type} 유형 / {score_type}"
            )


# 서버 시작 시 모델 로딩
@app.on_event("startup")
def startup_event():
    load_models()


# ==========================================
# 6. 요청 데이터 검증
# ==========================================

class ScoreRequest(BaseModel):

    personality_type: Literal["A", "B"]

    features: dict[str, float]


# ==========================================
# 7. 입력 특성 검증 및 정리
# ==========================================

def validate_features(features: dict) -> pd.DataFrame:
    """
    입력 특성 9개의 존재 여부와 범위를 검사한다.
    """

    # 필수 특성 누락 확인
    missing_features = [
        feature
        for feature in FEATURE_COLUMNS
        if feature not in features
    ]

    if missing_features:
        raise ValueError(
            f"필수 특성이 누락되었습니다: {missing_features}"
        )

    # 특성 순서에 맞춰 데이터 구성
    feature_data = {}

    for feature in FEATURE_COLUMNS:

        value = features[feature]

        # 숫자형 확인
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f"{feature}는 숫자형이어야 합니다."
            )

        # GPT 분석 특성 범위 확인
        if feature in [
            "preference_match",
            "dislike_match",
            "empathy",
            "interest",
            "sincerity",
            "context_match"
        ]:
            if not 0 <= value <= 1:
                raise ValueError(
                    f"{feature} 값은 0~1 범위여야 합니다."
                )

        # 반복 횟수 범위 확인
        elif feature == "repetition_count":
            if not 0 <= value <= 3:
                raise ValueError(
                    "repetition_count는 0~3 범위여야 합니다."
                )

        # 이전 점수 범위 확인
        elif feature in [
            "previous_affection",
            "previous_trust"
        ]:
            if not 0 <= value <= 100:
                raise ValueError(
                    f"{feature} 값은 0~100 범위여야 합니다."
                )

        feature_data[feature] = float(value)

    return pd.DataFrame(
        [feature_data],
        columns=FEATURE_COLUMNS
    )


# ==========================================
# 8. 점수 예측
# ==========================================

def predict_score(
    personality_type: str,
    features: dict
) -> dict:
    """
    캐릭터 유형에 맞는 XGBoost 모델로
    호감도와 신뢰도 변화량을 각각 예측한다.
    """

    if personality_type not in MODELS:
        raise ValueError(
            f"지원하지 않는 캐릭터 유형입니다: {personality_type}"
        )

    # 입력 데이터 검증
    input_data = validate_features(features)

    # 유형별 모델 가져오기
    affection_model = MODELS[personality_type]["affection"]
    trust_model = MODELS[personality_type]["trust"]

    # 호감도 변화량 예측
    affection_change = float(
        affection_model.predict(input_data)[0]
    )

    # 신뢰도 변화량 예측
    trust_change = float(
        trust_model.predict(input_data)[0]
    )

    # 변화량 제한
    affection_change = max(
        MIN_SCORE_CHANGE,
        min(MAX_SCORE_CHANGE, affection_change)
    )

    trust_change = max(
        MIN_SCORE_CHANGE,
        min(MAX_SCORE_CHANGE, trust_change)
    )

    return {
        "personality_type": personality_type,
        "affection_change": round(affection_change, 2),
        "trust_change": round(trust_change, 2)
    }


# ==========================================
# 9. 서버 상태 확인
# ==========================================

@app.get("/health")
def health_check():
    """
    점수 서버와 모델 로딩 상태를 확인한다.
    """

    return {
        "status": "ok",
        "models_loaded": len(MODELS) == 2
    }


# ==========================================
# 10. 점수 예측 API
# ==========================================

@app.post("/score")
def score_endpoint(request: ScoreRequest):
    """
    프론트엔드 또는 대화 관리자로부터
    입력 특성을 받아 점수 변화량을 반환한다.
    """

    try:
        result = predict_score(
            request.personality_type,
            request.features
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"점수 예측 실패: {e}"
        )

