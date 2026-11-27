
# ==========================================
# LLM 서비스
# ==========================================
# OpenAI GPT API를 호출하는 파일
#
# 주요 기능
# 1. 에피소드 시작 시 캐릭터 첫 대사 생성
# 2. 사용자 메시지에 대한 캐릭터 답변 생성
# 3. 사용자와 캐릭터의 대화 분석
# ==========================================

import json

from openai import OpenAI

from config.settings import OPENAI_API_KEY, OPENAI_MODEL

from prompts.prompt_builder import (
    build_opening_messages,
    build_response_messages,
    build_analysis_messages
)


# ==========================================
# OpenAI 클라이언트 생성
# ==========================================

# .env에 API 키가 설정되어 있는지 확인
if not OPENAI_API_KEY:
    raise ValueError(
        ".env에 OPENAI_API_KEY 또는 AI_API_KEY를 설정해 주세요."
    )

# OpenAI API 연결 객체 생성
client = OpenAI(
    api_key=OPENAI_API_KEY
)


# ==========================================
# 공통 기능: GPT JSON 응답 처리
# ==========================================

def call_gpt_json(messages: list) -> dict:
    """
    GPT에 메시지를 전달하고 JSON 응답을 반환한다.
    """

    try:
        # GPT API 호출
        response = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            response_format={
                "type": "json_object"
            },
            temperature=0.7
        )

        # GPT 응답 내용 가져오기
        content = response.choices[0].message.content

        if not content:
            raise ValueError("GPT 응답 내용이 비어 있습니다.")

        # JSON 문자열을 Python 딕셔너리로 변환
        result = json.loads(content)

        # 응답이 JSON 객체인지 확인
        if not isinstance(result, dict):
            raise ValueError(
                "GPT 응답이 JSON 객체가 아닙니다."
            )

        return result

    except json.JSONDecodeError as e:
        raise ValueError(
            f"GPT JSON 파싱 실패: {e}"
        ) from e

    except Exception as e:
        raise RuntimeError(
            f"GPT API 호출 실패: {e}"
        ) from e


# ==========================================
# 공통 기능: 캐릭터 대사 검증
# ==========================================

def validate_reply(result: dict) -> str:
    """
    GPT 응답에서 reply 항목을 확인하고
    정상적인 문자열 대사를 반환한다.
    """

    if not isinstance(result, dict):
        raise ValueError("GPT 응답이 딕셔너리가 아닙니다.")

    # reply 항목 존재 여부 확인
    if "reply" not in result:
        raise ValueError(
            "GPT 응답에 reply 항목이 없습니다."
        )

    reply = result["reply"]

    # 문자열인지 확인
    if not isinstance(reply, str):
        raise ValueError(
            "캐릭터 대사는 문자열이어야 합니다."
        )

    # 빈 대사인지 확인
    if not reply.strip():
        raise ValueError(
            "GPT가 빈 대사를 반환했습니다."
        )

    return reply.strip()


# ==========================================
# 1. 에피소드 시작 첫 대사 생성
# ==========================================

def generate_opening_dialogue(
    persona: dict,
    context: dict,
    episode: dict
) -> str:
    """
    에피소드 시작 시 캐릭터가 먼저 건네는 대사를 생성한다.

    주의:
    - 실제 대화 5턴에 포함하지 않는다.
    - 호감도와 신뢰도 분석을 하지 않는다.
    - XGBoost 점수 예측을 호출하지 않는다.
    """

    # 첫 대사 생성을 위한 프롬프트 구성
    messages = build_opening_messages(
        persona=persona,
        context=context,
        episode=episode
    )

    # GPT API 호출
    result = call_gpt_json(messages)

    # 생성된 첫 대사 반환
    return validate_reply(result)


# ==========================================
# 2. 사용자 메시지에 대한 캐릭터 답변 생성
# ==========================================

def generate_character_response(
    persona: dict,
    context: dict,
    episode: dict,
    user_message: str
) -> str:
    """
    사용자의 메시지를 바탕으로 캐릭터 답변을 생성한다.
    """

    # 빈 사용자 메시지 방지
    if not isinstance(user_message, str) or not user_message.strip():
        raise ValueError(
            "사용자 메시지가 비어 있습니다."
        )

    # 답변 생성을 위한 프롬프트 구성
    messages = build_response_messages(
        persona=persona,
        context=context,
        episode=episode,
        user_message=user_message
    )

    # GPT API 호출
    result = call_gpt_json(messages)

    # 캐릭터 대사 반환
    return validate_reply(result)


# ==========================================
# 3. 사용자와 캐릭터의 대화 분석
# ==========================================

def analyze_conversation(
    persona: dict,
    context: dict,
    user_message: str,
    character_message: str
) -> dict:
    """
    사용자와 캐릭터가 주고받은 대화를 분석한다.

    GPT는 6개 분석 특성만 추출한다.
    실제 점수 변화량은 XGBoost가 예측한다.
    """

    # 사용자와 캐릭터의 대화가 모두 존재하는지 확인
    if not isinstance(user_message, str) or not user_message.strip():
        raise ValueError(
            "분석할 사용자 메시지가 없습니다."
        )

    if not isinstance(character_message, str) or not character_message.strip():
        raise ValueError(
            "분석할 캐릭터 메시지가 없습니다."
        )

    # 대화 분석용 프롬프트 구성
    messages = build_analysis_messages(
        persona=persona,
        context=context,
        user_message=user_message,
        character_message=character_message
    )

    # GPT API 호출
    result = call_gpt_json(messages)

    # features 항목 확인
    if "features" not in result:
        raise ValueError(
            "GPT 분석 결과에 features 항목이 없습니다."
        )

    features = result["features"]

    # features가 딕셔너리인지 확인
    if not isinstance(features, dict):
        raise ValueError(
            "GPT 분석 결과의 features는 딕셔너리여야 합니다."
        )

    # GPT가 반환해야 하는 분석 특성 6개
    required_features = [
        "preference_match",
        "dislike_match",
        "empathy",
        "interest",
        "sincerity",
        "context_match"
    ]

    # 필수 특성 검증
    for feature in required_features:

        if feature not in features:
            raise ValueError(
                f"분석 특성이 누락되었습니다: {feature}"
            )

        value = features[feature]

        # 숫자형인지 확인
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(
                f"{feature}는 숫자형이어야 합니다."
            )

        # 0.0~1.0 범위인지 확인
        if not 0.0 <= value <= 1.0:
            raise ValueError(
                f"{feature} 값이 허용 범위를 벗어났습니다."
            )

        # 모든 값을 실수형으로 통일
        features[feature] = float(value)

    # 분석 근거가 없으면 빈 문자열로 처리
    result["reason"] = str(
        result.get("reason", "")
    )

    return result
