# 터미널 시작 python score_server_xgboost.py
from pathlib import Path
from typing import Dict, Literal

import joblib
import numpy as np
import pandas as pd
import uvicorn

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field


# ==========================================
# 1. FastAPI 서버 설정
# ==========================================

score_app = FastAPI(title="AI 연애 시뮬레이션 XGBoost 점수 서버")

score_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


# ==========================================
# 2. 모델 및 Feature 설정
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
MODEL_DIR = BASE_DIR.parent / "model" / "saved_models"

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

MODEL_FILES = {
    "A_affection": "type_a_affection_model.pkl",
    "A_trust": "type_a_trust_model.pkl",
    "B_affection": "type_b_affection_model.pkl",
    "B_trust": "type_b_trust_model.pkl"
}

MODELS = {}
MODEL_LOAD_ERROR = None


def load_models():
    """학습된 XGBoost 모델 4개를 불러온다."""
    global MODELS, MODEL_LOAD_ERROR

    try:
        loaded = {}

        for model_key, filename in MODEL_FILES.items():
            model_path = MODEL_DIR / filename

            if not model_path.exists():
                raise FileNotFoundError(
                    f"모델 파일을 찾을 수 없습니다: {model_path}"
                )

            loaded[model_key] = joblib.load(model_path)

        MODELS = loaded
        MODEL_LOAD_ERROR = None

    except Exception as e:
        MODELS = {}
        MODEL_LOAD_ERROR = str(e)


load_models()


# ==========================================
# 3. 요청 데이터 검증
# ==========================================

class ScoreRequest(BaseModel):
    personality_type: Literal["A", "B"]
    features: Dict[str, float]


# ==========================================
# 4. Feature 검증 및 정리
# ==========================================

def validate_features(features: Dict[str, float]):
    missing = [
        column for column in FEATURE_COLUMNS
        if column not in features
    ]

    if missing:
        raise ValueError(
            f"필수 Feature가 누락되었습니다: {', '.join(missing)}"
        )

    values = {}

    for column in FEATURE_COLUMNS:
        try:
            value = float(features[column])
        except (TypeError, ValueError):
            raise ValueError(f"{column} 값은 숫자여야 합니다.")

        if not np.isfinite(value):
            raise ValueError(f"{column} 값이 유효하지 않습니다.")

        values[column] = value

    # 학습 데이터 범위에 맞춰 입력값 검증
    ratio_features = [
        "preference_match",
        "dislike_match",
        "empathy",
        "interest",
        "sincerity",
        "context_match"
    ]

    for column in ratio_features:
        if not 0.0 <= values[column] <= 1.0:
            raise ValueError(
                f"{column}은 0.0~1.0 범위여야 합니다."
            )

    if not 0 <= values["repetition_count"] <= 3:
        raise ValueError("repetition_count는 0~3 범위여야 합니다.")

    if not 0 <= values["previous_affection"] <= 100:
        raise ValueError("previous_affection은 0~100 범위여야 합니다.")

    if not 0 <= values["previous_trust"] <= 100:
        raise ValueError("previous_trust는 0~100 범위여야 합니다.")

    # 학습 때 사용한 Feature 순서를 그대로 유지
    return [values[column] for column in FEATURE_COLUMNS]


# ==========================================
# 5. XGBoost 예측
# ==========================================

def predict_score(personality_type: str, features: Dict[str, float]):
    if MODEL_LOAD_ERROR or len(MODELS) != 4:
        raise RuntimeError(
            "XGBoost 모델을 불러오지 못했습니다. "
            f"모델 경로: {MODEL_DIR} / 원인: {MODEL_LOAD_ERROR}"
        )

    feature_values = validate_features(features)

    # DataFrame으로 전달해 학습 당시 Feature 이름과 순서를 유지
    input_df = pd.DataFrame(
        [feature_values],
        columns=FEATURE_COLUMNS
    )

    affection_model = MODELS[f"{personality_type}_affection"]
    trust_model = MODELS[f"{personality_type}_trust"]

    affection_prediction = float(
        affection_model.predict(input_df)[0]
    )
    trust_prediction = float(
        trust_model.predict(input_df)[0]
    )

    # 학습 타깃 점수 범위(-8~+8) 내로 제한하고 정수 점수로 변환
    affection_change = int(
        np.clip(np.rint(affection_prediction), -8, 8)
    )
    trust_change = int(
        np.clip(np.rint(trust_prediction), -8, 8)
    )

    return {
        "personality_type": personality_type,
        "affection_change": affection_change,
        "trust_change": trust_change,
        "affection_prediction": affection_prediction,
        "trust_prediction": trust_prediction
    }


# ==========================================
# 6. 서버 상태 확인
# ==========================================

@score_app.get("/health")
def health():
    if MODEL_LOAD_ERROR or len(MODELS) != 4:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "model_dir": str(MODEL_DIR),
                "error": MODEL_LOAD_ERROR
            }
        )

    return {
        "status": "ok",
        "loaded_models": list(MODELS.keys()),
        "model_dir": str(MODEL_DIR)
    }


# ==========================================
# 7. 점수 예측 API
# ==========================================

@score_app.post("/score")
def score_api(data: ScoreRequest):
    try:
        return predict_score(
            data.personality_type,
            data.features
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"점수 예측 중 오류가 발생했습니다: {e}"
        )


# ==========================================
# 8. 서버 실행
# ==========================================

if __name__ == "__main__":
    uvicorn.run(
        score_app,
        host="127.0.0.1",
        port=8765,
        log_level="info"
    )
