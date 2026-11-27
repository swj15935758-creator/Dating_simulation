
# ==========================================
# 프롬프트 조립 파일
# ==========================================
# GPT에게 전달할 메시지를 구성하는 파일
#
# 주요 기능
# 1. 에피소드 시작 시 캐릭터 첫 대사 생성
# 2. 사용자 메시지에 대한 캐릭터 답변 생성
# 3. 사용자와 캐릭터의 대화 분석
# ==========================================

import json

from prompts.system_prompt import get_system_prompt
from prompts.analysis_prompt import get_analysis_prompt
from prompts.response_prompt import get_response_prompt


# ==========================================
# 공통 기능: Python 데이터를 JSON으로 변환
# ==========================================

def convert_to_json(data: dict) -> str:

    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )


# ==========================================
# 1. 에피소드 시작용 첫 대사 생성
# ==========================================

def build_opening_messages(
    persona: dict,
    context: dict,
    episode: dict
) -> list:

    # 첫 대사 생성에 필요한 정보 구성
    opening_input = {
        "persona": persona,
        "context": context,
        "episode": episode,
        "opening_dialogue_prompt": episode.get(
            "opening_dialogue_prompt",
            ""
        )
    }

    # 캐릭터 성격 유형 확인
    personality_type = persona["personality_type"]

    # 공통 규칙과 캐릭터별 말투 규칙 결합
    system_content = (
        get_system_prompt()
        + "\n\n"
        + get_response_prompt(personality_type)
        + "\n\n"
        + """
        [에피소드 시작 첫 대사 생성 규칙]

        1. 현재 에피소드의 상황에 맞춰 캐릭터가 먼저 말을 건다.
        2. 캐릭터의 성격과 말투를 반드시 반영한다.
        3. 사용자가 대화를 이어갈 수 있는 자연스러운 말을 한다.
        4. 지나치게 긴 독백은 피한다.
        5. 첫 대사는 실제 대화 5턴에 포함하지 않는다.
        6. 호감도와 신뢰도 분석이나 점수 계산을 하지 않는다.
        7. 캐릭터의 대사만 생성한다.

        반드시 다음 JSON 형식으로 반환한다.

        {
            "reply": "캐릭터의 첫 대사"
        }
        """
    )

    return [
        {
            "role": "system",
            "content": system_content
        },
        {
            "role": "user",
            "content": (
                "다음 에피소드 정보를 참고하여 "
                "캐릭터의 첫 대사를 생성해.\n\n"
                + convert_to_json(opening_input)
            )
        }
    ]


# ==========================================
# 2. 사용자 메시지에 대한 캐릭터 답변 생성
# ==========================================

def build_response_messages(
    persona: dict,
    context: dict,
    episode: dict,
    user_message: str
) -> list:

    # 현재 대화에 필요한 정보 구성
    response_input = {
        "persona": persona,
        "context": context,
        "episode": episode,
        "user_message": user_message
    }

    # 캐릭터 성격 유형 확인
    personality_type = persona["personality_type"]

    # 공통 규칙과 캐릭터별 말투 규칙 결합
    system_content = (
        get_system_prompt()
        + "\n\n"
        + get_response_prompt(personality_type)
    )

    return [
        {
            "role": "system",
            "content": system_content
        },
        {
            "role": "user",
            "content": (
                "다음 JSON 데이터를 참고하여 "
                "캐릭터의 자연스러운 답변을 생성해.\n\n"
                + convert_to_json(response_input)
            )
        }
    ]


# ==========================================
# 3. 사용자와 캐릭터의 대화 분석
# ==========================================

def build_analysis_messages(
    persona: dict,
    context: dict,
    user_message: str,
    character_message: str
) -> list:

    # 실제로 주고받은 대화 내용 구성
    analysis_input = {
        "persona": persona,
        "context": context,
        "conversation": {
            "user_message": user_message,
            "character_message": character_message
        }
    }

    # 공통 규칙과 대화 분석 규칙 결합
    system_content = (
        get_system_prompt()
        + "\n\n"
        + get_analysis_prompt()
    )

    return [
        {
            "role": "system",
            "content": system_content
        },
        {
            "role": "user",
            "content": (
                "다음 JSON 데이터를 분석하고 "
                "지정된 분석 JSON 형식으로 반환해.\n\n"
                + convert_to_json(analysis_input)
            )
        }
    ]
