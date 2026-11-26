# XGBoost: 여러 의사결정나무가 이전 예측의 오차를 보완하며 학습하는 트리 기반 회귀 알고리즘

from pathlib import Path
from datetime import datetime

import joblib
import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error
from xgboost import XGBRegressor


# ==========================================
# 1. 기본 설정
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATA_FILE = BASE_DIR / "llm_generated_data.csv"
MODEL_DIR = BASE_DIR / "saved_models"
RESULT_FILE = BASE_DIR / "training_results.csv"

MODEL_DIR.mkdir(exist_ok=True)

PERSONALITY_TYPES = ["A", "B"]

FEATURES = [
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

TARGETS = {
    "affection": "llm_suggested_affection_change",
    "trust": "llm_suggested_trust_change"
}


# ==========================================
# 2. 데이터 불러오기 및 검증
# ==========================================

def load_data():

    if not DATA_FILE.exists():
        raise FileNotFoundError(
            f"학습 데이터 파일이 없습니다: {DATA_FILE}"
        )

    df = pd.read_csv(
        DATA_FILE,
        encoding="utf-8-sig"
    )

    required_columns = [
        "sample_id",
        "personality_type"
    ] + FEATURES + list(TARGETS.values())

    missing_columns = [
        col for col in required_columns
        if col not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"CSV에 필요한 컬럼이 없습니다: {missing_columns}"
        )

    df = df[required_columns].copy()

    # 성격 유형 정리
    df["personality_type"] = (
        df["personality_type"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    if not df["personality_type"].isin(PERSONALITY_TYPES).all():
        raise ValueError(
            "personality_type은 A 또는 B만 사용할 수 있습니다."
        )

    # 숫자형 데이터 변환
    numeric_columns = FEATURES + list(TARGETS.values())

    for col in numeric_columns:
        df[col] = pd.to_numeric(
            df[col],
            errors="coerce"
        )

    if df[numeric_columns].isnull().any().any():
        raise ValueError(
            "숫자형 컬럼에 비어 있거나 잘못된 값이 있습니다."
        )

    # 입력 변수 범위 검증
    for col in FEATURES[:6]:
        if not df[col].between(0, 1).all():
            raise ValueError(f"{col} 값은 0~1이어야 합니다.")

    if (df["repetition_count"] < 0).any():
        raise ValueError("repetition_count는 0 이상이어야 합니다.")

    for col in ["previous_affection", "previous_trust"]:
        if not df[col].between(0, 100).all():
            raise ValueError(f"{col} 값은 0~100이어야 합니다.")

    # 정답 점수 범위 검증
    for col in TARGETS.values():
        if not df[col].between(-10, 10).all():
            raise ValueError(f"{col} 값은 -10~+10이어야 합니다.")

    # 성격별 데이터 개수 확인
    print("\n========== 데이터 확인 ==========")

    for personality in PERSONALITY_TYPES:
        count = len(
            df[df["personality_type"] == personality]
        )

        print(f"Type {personality}: {count}개")

        if count < 10:
            raise ValueError(
                f"Type {personality} 데이터가 부족합니다. "
                "최소 10개 이상 필요합니다."
            )

    print(f"\n전체 데이터: {len(df)}개")

    return df


# ==========================================
# 3. XGBoost 모델 생성
# ==========================================

def create_model():

    return XGBRegressor(
        n_estimators=100,
        max_depth=2,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1,
        random_state=42,
        objective="reg:squarederror",
        n_jobs=1
    )


# ==========================================
# 4. 모델 학습 및 평가
# ==========================================

def train_model(
    df,
    personality_type,
    target_name,
    target_column
):

    print("\n========================================")
    print(f"Type {personality_type} - {target_name} 모델")
    print("========================================")

    # 성격 유형별 데이터 분리
    personality_df = df[
        df["personality_type"] == personality_type
    ].copy()

    X = personality_df[FEATURES]
    y = personality_df[target_column]

    # 학습 데이터와 테스트 데이터 분리
    X_train, X_test, y_train, y_test, id_train, id_test = (
        train_test_split(
            X,
            y,
            personality_df["sample_id"],
            test_size=0.2,
            random_state=42
        )
    )

    # 평가용 모델 학습
    eval_model = create_model()

    eval_model.fit(
        X_train,
        y_train
    )

    # 테스트 데이터 예측
    predictions = eval_model.predict(X_test)

    # 성능 평가
    mae = mean_absolute_error(
        y_test,
        predictions
    )

    rmse = np.sqrt(
        mean_squared_error(
            y_test,
            predictions
        )
    )

    print(f"전체 데이터: {len(personality_df)}개")
    print(f"학습 데이터: {len(X_train)}개")
    print(f"테스트 데이터: {len(X_test)}개")

    print(f"\nMAE: {mae:.3f}")
    print(f"RMSE: {rmse:.3f}")

    print("\n[실제값 / 예측값]")

    for actual, predicted in zip(y_test, predictions):
        print(
            f"실제: {actual:+.2f} / "
            f"예측: {predicted:+.2f}"
        )

    # 평가 결과 CSV용 데이터 생성
    results = []

    for sample_id, actual, predicted in zip(
        id_test,
        y_test,
        predictions
    ):

        results.append({
            "model_name": target_name,
            "personality_type": personality_type,
            "sample_id": sample_id,
            "actual_value": float(actual),
            "predicted_value": float(predicted),
            "absolute_error": abs(
                float(actual) - float(predicted)
            ),
            "MAE": float(mae),
            "RMSE": float(rmse),
            "train_count": len(X_train),
            "test_count": len(X_test),
            "trained_at": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )
        })

    # 최종 모델은 해당 성격의 전체 데이터로 다시 학습
    final_model = create_model()

    final_model.fit(
        X,
        y
    )

    # 모델 저장
    model_name = (
        f"type_{personality_type.lower()}_"
        f"{target_name}_model.pkl"
    )

    model_path = MODEL_DIR / model_name

    joblib.dump(
        final_model,
        model_path
    )

    print(f"\n모델 저장 완료: {model_path}")

    return results


# ==========================================
# 5. 메인 실행
# ==========================================

def main():

    print("AI 연애 시뮬레이션 ML 학습 시작")

    df = load_data()

    all_results = []

    # Type A / Type B 각각 학습
    for personality in PERSONALITY_TYPES:

        for target_name, target_column in TARGETS.items():

            results = train_model(
                df,
                personality,
                target_name,
                target_column
            )

            all_results.extend(results)

    # 학습 결과 CSV 저장
    result_df = pd.DataFrame(all_results)

    result_df.to_csv(
        RESULT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    print("\n========================================")
    print("모든 모델 학습 및 저장 완료!")
    print("========================================")

    print("\n[저장된 모델]")

    for personality in PERSONALITY_TYPES:
        print(
            f"- type_{personality.lower()}_"
            "affection_model.pkl"
        )
        print(
            f"- type_{personality.lower()}_"
            "trust_model.pkl"
        )

    print(f"\n학습 결과 CSV: {RESULT_FILE}")


if __name__ == "__main__":
    main()
