
import os
import json
import uuid
import re
from difflib import SequenceMatcher
from pathlib import Path
from datetime import datetime

import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI


# ==========================================
# 1. 기본 설정
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

ENV_FILE = BASE_DIR / ".env"
OUTPUT_FILE = BASE_DIR / "llm_generated_data.csv"
TEMP_FILE = BASE_DIR / "llm_generated_data.tmp"

# 성격별 추가 생성 목표
GENERATE_COUNT = 20

# 중복 데이터가 발생했을 때 재생성 시도 횟수
MAX_RETRIES = 4

# 유사 발언 중복 판단 기준
SIMILARITY_THRESHOLD = 0.82

MODEL_NAME = "gpt-4.1-mini"

COLUMNS = [
    "sample_id",
    "created_at",
    "personality_type",
    "scenario_type",
    "user_utterance",
    "context_summary",
    "emotion",
    "behavior",
    "preference_match",
    "dislike_match",
    "empathy",
    "interest",
    "sincerity",
    "context_match",
    "repetition_count",
    "previous_affection",
    "previous_trust",
    "llm_suggested_affection_change",
    "llm_suggested_trust_change"
]


# ==========================================
# 2. 캐릭터 성격 설정
# ==========================================

PERSONALITIES = {
    "A": """
[Type A - 안정형]

성격:
- 차분하고 신중하며 안정적인 성격
- 겉으로는 무뚝뚝하고 감정 표현이 적음
- 상대방의 말을 오래 기억하고 작은 약속도 중요하게 생각함
- 쉽게 마음을 열지 않지만 신뢰가 쌓이면 속마음을 이야기함

연애관:
- 진지하고 안정적인 관계를 선호함
- 신중하고 점진적으로 관계를 발전시킴

선호:
- 약속을 잘 지키는 행동
- 사전 계획과 책임감
- 진심 어린 대화
- 일관성 있는 태도
- 깊이 있는 대화

비선호:
- 무책임한 행동
- 반복되는 농담으로 진지한 대화를 회피하는 태도
- 가벼운 대화만 지속하는 행동
- 이전 대화를 기억하지 못하는 행동
- 약속을 가볍게 여기는 태도

호감도 판단:
- 진심 어린 관심과 깊은 대화에 호감도가 상승함
- 자신의 말을 진지하게 들어주면 긍정적으로 반응함
- 쉽게 호감이 올라가지 않으며 점진적으로 상승함

신뢰도 판단:
- 약속을 지키고 일관성 있는 행동을 하면 상승함
- 말과 행동이 다르면 하락할 수 있음

갈등 상황:
- 서운함을 쌓아두는 경향이 있음
- 상대방이 무책임하거나 약속을 어기면 부정적으로 판단함
""",

    "B": """
[Type B - 즉흥형]

성격:
- 발랄하고 장난스러우며 외향적인 성격
- 사람들과 쉽게 친해지고 농담을 즐김
- 즉흥적인 활동과 새로운 경험을 좋아함
- 감정 표현이 적극적임
- 관계가 의무나 통제로 변하면 부담을 느낌

연애관:
- 자유롭고 설레는 관계를 선호함
- 호감은 빠르게 형성될 수 있지만 관계 확정은 신중함

선호:
- 유머와 즐거운 대화
- 즉흥적인 데이트 제안
- 새로운 경험
- 자유로운 분위기
- 솔직한 소통

비선호:
- 지나친 간섭과 통제
- 관계에 대한 지나친 압박
- 즉각적인 관계 확답 요구
- 강압적인 태도

호감도 판단:
- 즐거운 대화와 유머에 호감도가 상승함
- 새로운 활동이나 데이트 제안에 긍정적으로 반응함
- 호감도가 빠르게 상승할 수 있지만 상황에 따라 변동이 큼

신뢰도 판단:
- 자신의 자율성을 존중하면 상승함
- 솔직하고 편안한 소통을 중요하게 생각함
- 통제하거나 압박하면 신뢰도가 하락할 수 있음

갈등 상황:
- 상대방이 자신을 통제한다고 느끼면 거리를 둠
- 진지한 상황에서도 농담으로 넘기는 경향이 있음
"""
}


# ==========================================
# 3. 공통 상황 유형
# ==========================================

SCENARIO_TYPES = """
다음 상황들을 골고루 활용하라.

1. 처음 만나는 상황
2. 일상적인 안부와 관심 표현
3. 진심 어린 칭찬
4. 상대방의 취미에 관심 보이기
5. 갑작스러운 데이트 제안
6. 계획적인 데이트 제안
7. 약속을 지키는 상황
8. 약속을 잊어버리는 상황
9. 사과와 화해
10. 질투하는 상황
11. 서운함을 표현하는 상황
12. 상대방을 위로하는 상황
13. 상대방의 고민을 들어주는 상황
14. 거짓말을 하거나 진실을 밝히는 상황
15. 지나친 간섭과 통제
16. 자유와 개인 시간을 존중하는 상황
17. 반복적인 농담과 장난
18. 진지한 대화를 회피하는 상황
19. 이전 대화를 기억하는 상황
20. 이전 대화를 기억하지 못하는 상황
21. 무관심하거나 대화를 회피하는 상황
22. 예상하지 못한 배려를 하는 상황
23. 갈등이 발생하는 상황
24. 관계에 대한 부담을 표현하는 상황
25. 호감은 높지만 신뢰가 낮은 상황
26. 신뢰는 높지만 호감이 낮은 상황
27. 상대방의 실수를 이해하는 상황
28. 상대방에게 솔직하게 감정을 표현하는 상황
"""


# ==========================================
# 4. 환경변수 및 OpenAI 연결
# ==========================================

def create_client():

    if not ENV_FILE.exists():
        raise FileNotFoundError(
            f".env 파일을 찾을 수 없습니다: {ENV_FILE}"
        )

    load_dotenv(ENV_FILE)

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError(
            ".env 파일에 OPENAI_API_KEY가 설정되어 있는지 확인하세요."
        )

    model_name = os.getenv("OPENAI_MODEL", MODEL_NAME)

    client = OpenAI(
        api_key=api_key,
        timeout=60,
        max_retries=2
    )

    return client, model_name


# ==========================================
# 5. 기존 데이터 참고용 목록 생성
# ==========================================

def get_existing_examples(existing_df, personality_type):

    if existing_df.empty:
        return []

    filtered_df = existing_df[
        existing_df["personality_type"].astype(str)
        == personality_type
    ]

    examples = []

    for _, row in filtered_df.iterrows():

        examples.append({
            "scenario_type": str(row["scenario_type"]),
            "user_utterance": str(row["user_utterance"])
        })

    return examples


# ==========================================
# 6. LLM 데이터 생성 프롬프트
# ==========================================

def generate_prompt(personality_type, count, existing_examples):

    personality = PERSONALITIES[personality_type]

    existing_text = json.dumps(
        existing_examples,
        ensure_ascii=False,
        indent=2
    )

    return f"""
너는 AI 연애 시뮬레이션 게임의 감정 분석 학습 데이터를 생성하는 전문가다.

다음 캐릭터의 성격을 기준으로 사용자의 발언을 분석해야 한다.

{personality}

[데이터 생성 목표]

이번에는 기존 학습 데이터에 없는 새로운 데이터를 생성해야 한다.

정확히 {count}개의 데이터를 생성한다.

기존 데이터의 상황과 발언을 반드시 참고하라.

[기존 데이터 목록]

아래는 이미 CSV에 저장되어 있는 데이터다.

{existing_text}

[중요한 생성 규칙]

1. 기존 데이터와 동일한 사용자 발언을 만들지 마라.
2. 단어 몇 개만 바꾼 비슷한 문장도 만들지 마라.
3. 기존 데이터와 의미가 유사한 상황도 최대한 피하라.
4. 새로운 대화 소재와 새로운 갈등 원인을 활용하라.
5. 동일한 상황이라도 기존과 다른 관계 맥락과 감정 흐름을 만들어라.
6. 모든 데이터가 긍정적이거나 부정적인 상황에 치우치지 않도록 하라.
7. 단순히 문장만 바꾸지 말고 실제 상황 자체를 다양하게 구성하라.

[상황 유형]

다음 상황들을 골고루 활용하라.

{SCENARIO_TYPES}

[Type A / Type B 비교 조건]

두 성격 유형 모두 비슷한 상황 유형을 경험할 수 있도록 구성하라.

단, 동일한 상황이라도 캐릭터 성격에 따라
감정, 행동, 분석 변수, 호감도 및 신뢰도 변화량이 달라져야 한다.

예를 들어 약속을 갑자기 변경하는 상황에서
Type A는 계획과 약속의 중요성을 중심으로 판단하고,
Type B는 변경 이유와 상황의 자유로움을 중심으로 판단할 수 있다.

다른 성격 유형의 판단 기준을 섞지 마라.

[분석 변수]

다음 변수는 모두 0.0부터 1.0 사이의 숫자로 작성한다.

- preference_match: 캐릭터 선호와 일치하는 정도
- dislike_match: 캐릭터 비선호 행동과 일치하는 정도
- empathy: 사용자의 감정에 공감하는 정도
- interest: 사용자 발언에 느끼는 관심 정도
- sincerity: 사용자의 말이 진정성 있게 느껴지는 정도
- context_match: 이전 대화 및 현재 상황과 잘 맞는 정도

[기타 변수]

- scenario_type: 상황 유형
- user_utterance: 실제 사용자가 말한 자연스러운 한국어 문장
- context_summary: 이전 대화 및 현재 상황 요약
- emotion: 캐릭터가 느끼는 감정
- behavior: 캐릭터가 보일 행동
- repetition_count: 같은 행동이나 표현의 반복 횟수, 0 이상의 정수
- previous_affection: 이전 호감도, 0~100
- previous_trust: 이전 신뢰도, 0~100

[점수 생성 규칙]

- llm_suggested_affection_change: 호감도 변화량, -10~+10
- llm_suggested_trust_change: 신뢰도 변화량, -10~+10

호감도와 신뢰도는 반드시 독립적으로 판단한다.

호감도가 높다고 신뢰도도 반드시 높아지는 것은 아니다.
신뢰도가 높다고 호감도도 반드시 높아지는 것은 아니다.

긍정적인 상황이라고 무조건 +10점을 주지 않는다.
부정적인 상황이라고 무조건 -10점을 주지 않는다.

캐릭터의 성격과 실제 대화 내용을 종합하여 현실적으로 점수를 부여한다.

이전 호감도와 신뢰도도 다양하게 설정한다.
특히 낮은 점수, 중간 점수, 높은 점수를 골고루 포함한다.

repetition_count도 0만 사용하지 말고 다양한 값을 활용한다.

[출력 형식]

반드시 아래 JSON 구조로만 출력한다.

{{
    "samples": [
        {{
            "scenario_type": "긍정적인 대화",
            "user_utterance": "오늘 네가 추천해준 영화를 봤는데 정말 좋았어.",
            "context_summary": "이전에 캐릭터가 영화를 추천해준 상황",
            "emotion": "기쁨",
            "behavior": "관심을 보이며 대화를 이어감",
            "preference_match": 0.9,
            "dislike_match": 0.0,
            "empathy": 0.8,
            "interest": 0.9,
            "sincerity": 0.9,
            "context_match": 0.9,
            "repetition_count": 0,
            "previous_affection": 40,
            "previous_trust": 35,
            "llm_suggested_affection_change": 5,
            "llm_suggested_trust_change": 4
        }}
    ]
}}

위 예시는 출력 형식을 설명하기 위한 예시다.
실제 데이터는 서로 다른 상황과 발언으로 생성해야 한다.

정확히 {count}개의 데이터를 생성하라.
JSON 이외의 설명은 출력하지 마라.
"""


# ==========================================
# 7. LLM 데이터 생성
# ==========================================

def generate_data(
    client,
    model_name,
    personality_type,
    count,
    existing_examples
):

    print(
        f"\n========== Type {personality_type} "
        f"데이터 {count}개 생성 =========="
    )

    prompt = generate_prompt(
        personality_type,
        count,
        existing_examples
    )

    response = client.chat.completions.create(
        model=model_name,
        messages=[
            {
                "role": "system",
                "content": (
                    "너는 연애 시뮬레이션 감정 분석 "
                    "학습 데이터를 생성하는 전문가다."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={"type": "json_object"},
        temperature=0.8
    )

    result = json.loads(
        response.choices[0].message.content
    )

    samples = result.get("samples", [])

    if not isinstance(samples, list):
        raise ValueError(
            "생성된 samples가 리스트 형식이 아닙니다."
        )

    # 초과 생성된 데이터는 필요한 개수만 사용
    if len(samples) > count:

        print(
            f"초과 생성: {len(samples)}개 → "
            f"{count}개만 사용"
        )

        samples = samples[:count]

    # 요청한 개수보다 적으면 오류 처리
    if len(samples) < count:

        raise ValueError(
            f"요청한 데이터는 {count}개지만 "
            f"{len(samples)}개만 생성되었습니다."
        )

    print(f"생성 완료: {len(samples)}개")

    return samples


# ==========================================
# 8. 데이터 검증 및 행 생성
# ==========================================

NUMERIC_FEATURES = [
    "preference_match",
    "dislike_match",
    "empathy",
    "interest",
    "sincerity",
    "context_match"
]


def make_row(sample, personality_type):

    required_fields = [
        "scenario_type",
        "user_utterance",
        "context_summary",
        "emotion",
        "behavior",
        "preference_match",
        "dislike_match",
        "empathy",
        "interest",
        "sincerity",
        "context_match",
        "repetition_count",
        "previous_affection",
        "previous_trust",
        "llm_suggested_affection_change",
        "llm_suggested_trust_change"
    ]

    if not isinstance(sample, dict):
        raise ValueError(
            f"Type {personality_type}: 데이터 형식이 올바르지 않습니다."
        )

    for field in required_fields:

        if field not in sample:
            raise ValueError(
                f"Type {personality_type}: 필수 필드 누락 - {field}"
            )

    row = {
        "sample_id": str(uuid.uuid4()),
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "personality_type": personality_type
    }

    for field in required_fields:
        row[field] = sample[field]

    # 분석 변수 검증
    for field in NUMERIC_FEATURES:

        value = float(row[field])

        if not 0 <= value <= 1:
            raise ValueError(
                f"{field} 값은 0~1 사이여야 합니다: {value}"
            )

        row[field] = value

    # 반복 횟수 검증
    repetition = int(row["repetition_count"])

    if repetition < 0 or float(row["repetition_count"]) != repetition:
        raise ValueError(
            "repetition_count는 0 이상의 정수여야 합니다."
        )

    row["repetition_count"] = repetition

    # 이전 점수 검증
    for field in [
        "previous_affection",
        "previous_trust"
    ]:

        value = float(row[field])

        if not 0 <= value <= 100:
            raise ValueError(
                f"{field} 값은 0~100 사이여야 합니다."
            )

        row[field] = value

    # 변화량 검증
    for field in [
        "llm_suggested_affection_change",
        "llm_suggested_trust_change"
    ]:

        value = float(row[field])

        if not -10 <= value <= 10:
            raise ValueError(
                f"{field} 값은 -10~+10 사이여야 합니다."
            )

        row[field] = value

    # 문자열 검증
    text_fields = [
        "scenario_type",
        "user_utterance",
        "context_summary",
        "emotion",
        "behavior"
    ]

    for field in text_fields:

        row[field] = str(row[field]).strip()

        if not row[field]:
            raise ValueError(
                f"{field} 값이 비어 있습니다."
            )

    return row


# ==========================================
# 9. 기존 CSV 불러오기
# ==========================================

def load_existing_data():

    if not OUTPUT_FILE.exists():
        return pd.DataFrame(columns=COLUMNS)

    df = pd.read_csv(
        OUTPUT_FILE,
        encoding="utf-8-sig"
    )

    if list(df.columns) != COLUMNS:
        raise ValueError(
            "기존 CSV의 컬럼 구조가 현재 코드와 다릅니다. "
            "기존 파일을 확인하세요."
        )

    print(f"\n기존 데이터: {len(df)}개")

    return df


# ==========================================
# 10. 발언 유사도 검사
# ==========================================

def normalize_text(text):

    text = str(text).strip().lower()

    # 공백 및 문장부호 제거
    text = re.sub(r"[\s\W_]+", "", text)

    return text


def is_similar_utterance(new_text, existing_texts):

    new_text = normalize_text(new_text)

    if not new_text:
        return True

    for old_text in existing_texts:

        old_text = normalize_text(old_text)

        if not old_text:
            continue

        similarity = SequenceMatcher(
            None,
            new_text,
            old_text
        ).ratio()

        if similarity >= SIMILARITY_THRESHOLD:
            return True

    return False


# ==========================================
# 11. 새로운 데이터 확보
# ==========================================

def generate_unique_data(
    client,
    model_name,
    personality_type,
    existing_df
):

    existing_examples = get_existing_examples(
        existing_df,
        personality_type
    )

    existing_utterances = [
        item["user_utterance"]
        for item in existing_examples
    ]

    accepted_rows = []

    print(
        f"\nType {personality_type} 기존 데이터: "
        f"{len(existing_utterances)}개"
    )

    for attempt in range(1, MAX_RETRIES + 1):

        remaining = GENERATE_COUNT - len(accepted_rows)

        if remaining <= 0:
            break


        # 기존 데이터 + 이번에 통과한 데이터
        reference_utterances = (
            existing_utterances
            + [
                row["user_utterance"]
                for row in accepted_rows
            ]
        )

        reference_examples = (
            existing_examples
            + [
                {
                    "scenario_type": row["scenario_type"],
                    "user_utterance": row["user_utterance"]
                }
                for row in accepted_rows
            ]
        )

        samples = generate_data(
            client,
            model_name,
            personality_type,
            remaining,
            reference_examples
        )

        added_count = 0
        duplicate_count = 0

        for sample in samples:

            row = make_row(
                sample,
                personality_type
            )

            if is_similar_utterance(
                row["user_utterance"],
                reference_utterances
            ):

                duplicate_count += 1
                continue

            accepted_rows.append(row)

            reference_utterances.append(
                row["user_utterance"]
            )

            added_count += 1

        print(f"새 데이터 통과: {added_count}개")
        print(f"중복 제외: {duplicate_count}개")
        print(f"현재 확보: {len(accepted_rows)}개")

    if len(accepted_rows) != GENERATE_COUNT:

        raise ValueError(
            f"Type {personality_type}: "
            f"새 데이터 {GENERATE_COUNT}개 확보 실패. "
            f"현재 {len(accepted_rows)}개 확보했습니다. "
            "CSV는 저장하지 않았습니다. 다시 실행해 주세요."
        )

    return accepted_rows


# ==========================================
# 12. CSV 저장
# ==========================================

def save_data(new_rows, existing_df):

    new_df = pd.DataFrame(
        new_rows,
        columns=COLUMNS
    )

    # 기존 데이터와 새 데이터 합치기
    final_df = pd.concat(
        [existing_df, new_df],
        ignore_index=True
    )

    # 동일 성격 유형 + 동일 발언 중복 최종 검사
    final_df = final_df.drop_duplicates(
        subset=[
            "personality_type",
            "user_utterance"
        ],
        keep="first"
    )

    try:

        final_df.to_csv(
            TEMP_FILE,
            index=False,
            encoding="utf-8-sig"
        )

        TEMP_FILE.replace(OUTPUT_FILE)

    finally:

        if TEMP_FILE.exists():
            TEMP_FILE.unlink()

    print("\n========== CSV 저장 완료 ==========")
    print(f"새로 생성한 데이터: {len(new_df)}개")
    print(f"전체 데이터: {len(final_df)}개")
    print(f"저장 위치: {OUTPUT_FILE}")

    print("\n[성격별 데이터 개수]")

    print(
        final_df["personality_type"]
        .value_counts()
        .sort_index()
    )


# ==========================================
# 13. 메인 실행
# ==========================================

def main():

    print("AI 연애 시뮬레이션 학습 데이터 생성 시작")

    try:

        client, model_name = create_client()

        print(f"사용 모델: {model_name}")

        # 기존 데이터 먼저 불러오기
        existing_df = load_existing_data()

        all_rows = []

        # Type A 신규 데이터 20개
        type_a_rows = generate_unique_data(
            client,
            model_name,
            "A",
            existing_df
        )

        all_rows.extend(type_a_rows)

        # Type B 신규 데이터 20개
        type_b_rows = generate_unique_data(
            client,
            model_name,
            "B",
            existing_df
        )

        all_rows.extend(type_b_rows)

        # 모든 데이터 생성 성공 후 한 번에 저장
        save_data(
            all_rows,
            existing_df
        )

        print("\n================================")
        print("Type A / Type B 데이터 생성 완료!")
        print("================================")

    except Exception as e:

        print("\n데이터 생성 중 오류가 발생했습니다.")
        print(f"오류 내용: {e}")

        if TEMP_FILE.exists():
            TEMP_FILE.unlink()


if __name__ == "__main__":
    main()
