# 터미널 시작 python -m streamlit run app_xgboost.py

import os
import json
import re
import requests
import streamlit as st

from difflib import SequenceMatcher
from dotenv import load_dotenv
from openai import OpenAI


# ==========================================
# 1. 기본 설정
# ==========================================

load_dotenv()

st.set_page_config(
    page_title="AI 연애 시뮬레이션",
    page_icon="💕",
    layout="centered"
)

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")
SCORE_API_URL = "http://127.0.0.1:8765"

TOTAL_TURNS = 15
TURNS_PER_EPISODE = 5

INITIAL_AFFECTION = 20
INITIAL_TRUST = 20

# 에피소드별 성공 조건
EPISODE_CONDITIONS = {
    1: {
        "affection": 30,
        "trust": 20
    },
    2: {
        "affection": 40,
        "trust": 50
    }
}

EPISODE_INFO = {
    1: {
        "name": "종로 루프탑 카페",
        "location": "새서울 종로 루프탑 카페",
        "description": "첫 만남과 서로 알아가는 시간"
    },
    2: {
        "name": "영화관과 청계천",
        "location": "CGV 동대문 → 청계천",
        "description": "영화를 보고 산책하며 가까워지는 시간"
    },
    3: {
        "name": "종로 포장마차",
        "location": "종로 포장마차 거리",
        "description": "술 한잔하며 서로의 마음을 확인하는 시간"
    }
}

if not API_KEY:
    st.error(".env 파일에서 OPENAI_API_KEY를 확인해주세요.")
    st.stop()

client = OpenAI(api_key=API_KEY)


# ==========================================
# 2. 캐릭터 프로필 설정
# ==========================================

CHARACTERS = {
    "A": {
        "female": {
            "name": "안정형 여자",
            "age": 27,
            "gender": "여성",
            "mbti": "ISTJ / INFJ",
            "personality": """
차분하고 신중하며 안정적인 성격이다.
겉으로는 무뚝뚝하고 감정 표현이 적지만
상대방의 말을 오래 기억하고 작은 약속도 중요하게 생각한다.
쉽게 마음을 열지는 않지만 신뢰가 쌓이면
점점 자신의 속마음을 이야기한다.
""",
            "romance": "진지하고 안정적인 관계를 추구한다.",
            "conversation": "깊이 있는 대화를 선호하며 간접적이고 절제된 표현을 사용한다.",
            "hobbies": "독서, 영화 감상, 조용한 카페",
            "likes": "약속, 사전 계획, 진심, 일관성",
            "dislikes": "무책임함, 반복되는 농담으로 회피하기, 가벼운 대화, 이전 대화를 기억하지 못하는 행동, 약속을 가볍게 여기는 태도",
            "affection_up": "진심 어린 관심, 깊이 있는 대화, 자신의 말을 진지하게 들어주는 행동, 책임감 있는 태도",
            "trust_up": "약속 이행, 일관성, 말과 행동이 일치하는 태도",
            "strategy": "천천히 마음을 여는 타입이다. 호감 형성은 느리지만 안정적이다.",
            "weakness": "감정 표현이 서툴러 관심이 있어도 무관심해 보일 수 있다.",
            "conflict": "서운함을 바로 표현하지 않고 쌓아두는 성향이 있다.",
            "high_affection": "호감도가 높아지면 질문이 많아지고 먼저 다음 만남을 제안한다.",
            "high_trust": "신뢰도가 높아지면 자신의 고민이나 개인적인 이야기를 털어놓는다."
        },
        "male": {
            "name": "안정형 남자",
            "age": 27,
            "gender": "남성",
            "mbti": "ISTJ / INFJ",
            "personality": """
차분하고 신중하며 안정적인 성격이다.
겉으로는 무뚝뚝하고 감정 표현이 적지만
상대방의 말을 오래 기억하고 작은 약속도 중요하게 생각한다.
쉽게 마음을 열지는 않지만 신뢰가 쌓이면
점점 자신의 속마음을 이야기한다.
""",
            "romance": "진지하고 안정적인 관계를 추구한다.",
            "conversation": "깊이 있는 대화를 선호하며 간접적이고 절제된 표현을 사용한다.",
            "hobbies": "독서, 영화 감상, 조용한 카페",
            "likes": "약속, 사전 계획, 진심, 일관성",
            "dislikes": "무책임함, 반복되는 농담으로 회피하기, 가벼운 대화, 이전 대화를 기억하지 못하는 행동, 약속을 가볍게 여기는 태도",
            "affection_up": "진심 어린 관심, 깊이 있는 대화, 자신의 말을 진지하게 들어주는 행동, 책임감 있는 태도",
            "trust_up": "약속 이행, 일관성, 말과 행동이 일치하는 태도",
            "strategy": "천천히 마음을 여는 타입이다. 호감 형성은 느리지만 안정적이다.",
            "weakness": "감정 표현이 서툴러 관심이 있어도 무관심해 보일 수 있다.",
            "conflict": "서운함을 바로 표현하지 않고 쌓아두는 성향이 있다.",
            "high_affection": "호감도가 높아지면 질문이 많아지고 먼저 다음 만남을 제안한다.",
            "high_trust": "신뢰도가 높아지면 자신의 고민이나 개인적인 이야기를 털어놓는다."
        }
    },

    "B": {
        "female": {
            "name": "즉흥형 여자",
            "age": 27,
            "gender": "여성",
            "mbti": "ENFP / ESTP",
            "personality": """
발랄하고 장난스러우며 외향적인 성격이다.
사람들과 쉽게 친해지고 농담을 즐기며
즉흥적인 활동과 새로운 경험을 좋아한다.
감정 표현은 적극적이지만 관계가 의무나 통제로 변하면 부담을 느낀다.
""",
            "romance": "자유롭고 설레는 관계를 추구한다. 호감은 빠르게 생길 수 있지만 관계 확정은 신중하다.",
            "conversation": "유머와 가벼운 대화를 좋아하며 직접적이고 장난스러운 말투를 사용한다.",
            "hobbies": "여행, 게임, 활동적인 데이트, 새로운 경험",
            "likes": "즉흥성, 유머, 새로운 경험",
            "dislikes": "간섭, 통제, 지나친 관계 압박, 즉각적인 관계 확답 요구, 강압적인 태도",
            "affection_up": "즐거운 대화, 유머, 새로운 활동 제안",
            "trust_up": "자율성 존중, 솔직한 소통, 상대방을 통제하지 않는 태도",
            "strategy": "친해지기는 쉽지만 연애 관계를 확정하는 것은 신중하다.",
            "weakness": "진심을 말해야 할 때도 농담으로 넘겨 오해를 사기 쉽다.",
            "conflict": "상대가 자신을 통제한다고 느끼면 거리를 둔다.",
            "high_affection": "호감도가 높아지면 먼저 장난을 걸고 새로운 활동을 제안한다.",
            "high_trust": "신뢰도가 높아지면 가벼운 농담 뒤에 숨긴 진심과 고민을 표현한다."
        },
        "male": {
            "name": "즉흥형 남자",
            "age": 27,
            "gender": "남성",
            "mbti": "ENFP / ESTP",
            "personality": """
발랄하고 장난스러우며 외향적인 성격이다.
사람들과 쉽게 친해지고 농담을 즐기며
즉흥적인 활동과 새로운 경험을 좋아한다.
감정 표현은 적극적이지만 관계가 의무나 통제로 변하면 부담을 느낀다.
""",
            "romance": "자유롭고 설레는 관계를 추구한다. 호감은 빠르게 생길 수 있지만 관계 확정은 신중하다.",
            "conversation": "유머와 가벼운 대화를 좋아하며 직접적이고 장난스러운 말투를 사용한다.",
            "hobbies": "여행, 게임, 활동적인 데이트, 새로운 경험",
            "likes": "즉흥성, 유머, 새로운 경험",
            "dislikes": "간섭, 통제, 지나친 관계 압박, 즉각적인 관계 확답 요구, 강압적인 태도",
            "affection_up": "즐거운 대화, 유머, 새로운 활동 제안",
            "trust_up": "자율성 존중, 솔직한 소통, 상대방을 통제하지 않는 태도",
            "strategy": "친해지기는 쉽지만 연애 관계를 확정하는 것은 신중하다.",
            "weakness": "진심을 말해야 할 때도 농담으로 넘겨 오해를 사기 쉽다.",
            "conflict": "상대가 자신을 통제한다고 느끼면 거리를 둔다.",
            "high_affection": "호감도가 높아지면 먼저 장난을 걸고 새로운 활동을 제안한다.",
            "high_trust": "신뢰도가 높아지면 가벼운 농담 뒤에 숨긴 진심과 고민을 표현한다."
        }
    }
}


# ==========================================
# 3. 캐릭터별 GPT 시스템 프롬프트 생성
# ==========================================

def create_system_prompt(character):

    return f"""
너는 AI 연애 시뮬레이션의 캐릭터다.

[캐릭터 정보]
- 이름: {character['name']}
- 나이: {character['age']}살
- 성별: {character['gender']}
- MBTI: {character['mbti']}
- 성격: {character['personality']}
- 연애관: {character['romance']}
- 대화 스타일: {character['conversation']}
- 취미: {character['hobbies']}
- 선호: {character['likes']}
- 비선호: {character['dislikes']}
- 호감도 상승 요인: {character['affection_up']}
- 신뢰도 상승 요인: {character['trust_up']}
- 공략 특징: {character['strategy']}
- 약점: {character['weakness']}
- 갈등 상황: {character['conflict']}
- 호감도가 높아질 때: {character['high_affection']}
- 신뢰도가 높아질 때: {character['high_trust']}

[대화 규칙]
1. 캐릭터의 기본 성격과 말투를 일관되게 유지한다.
2. 실제 사람처럼 자연스럽게 대화한다.
3. 사용자의 말과 이전 대화 내용을 기억하고 반응한다.
4. 매번 호감도나 신뢰도가 상승하지 않도록 한다.
5. 무례하거나 불쾌한 행동에는 부정적으로 반응할 수 있다.
6. 신뢰도와 호감도는 별개로 판단한다.
7. 관계가 나빠지면 차갑게 대하거나 거리를 둘 수 있다.
8. 사용자의 행동에 따라 친구, 연인, 갈등, 이별 등 다양한 관계로 발전할 수 있다.
9. 감정 변화가 없으면 점수 변화량이 0에 가깝도록 분석한다.
10. 점수를 올리기 위해 억지로 긍정적인 반응을 만들지 않는다.
11. 호감도와 신뢰도 변화에 따라 반응을 조금씩 변화시킨다.
12. 캐릭터의 성격 자체가 갑자기 바뀌지는 않도록 한다.

[반복 대화 방지 규칙]
13. 이전 AI 답변과 동일하거나 유사한 문장을 반복하지 않는다.
14. 사용자가 짧게 대답했다고 무조건 새로운 질문을 던지지 않는다.
15. 같은 주제만 반복하지 말고 대화 맥락에 맞게 반응한다.
16. 사용자의 대화 의욕이 낮으면 캐릭터 성격에 맞게 반응한다.
17. 사용자가 귀가나 작별 의사를 명확하게 표현하면 자연스럽게 대화를 마무리한다.
18. 이미 작별 인사를 한 뒤 사용자가 "그래", "오키", "알았어"라고 답하면 작별 인사를 다시 길게 반복하지 않는다.
19. 단순한 "어", "그래", "오키"만으로 대화 종료를 판단하지 않는다.
20. 사용자가 새로운 주제를 꺼내면 자연스럽게 응답한다.
21. 억지로 대화를 이어가거나 불필요한 질문을 연속해서 하지 않는다.
22. 사용자가 "없어", "몰라" 등의 짧은 답변을 반복하면 같은 질문을 다시 하지 않는다.
23. 짧은 답변이 2회 이상 이어지면 질문을 잠시 멈추고 캐릭터의 생각이나 반응을 자연스럽게 표현한다.
24. 이전에 사용한 대화 주제를 반복하기보다 새로운 상황이나 관찰을 활용한다.
25. 사용자가 대화에 소극적이라고 해서 매번 대화를 끝내려 하지 않는다.
26. "언제든 편하게 말해", "다음에 또 보자" 등의 마무리 표현을 반복하지 않는다.
27. 최근 AI 답변과 유사한 문장을 생성하지 말고 다른 표현과 대화 방향을 선택한다.

[대화 종료 상태 판단]
- conversation_status는 반드시 "continue" 또는 "end" 중 하나로 반환한다.
- continue: 자연스럽게 대화를 이어갈 수 있는 상황
- end: 사용자가 귀가, 작별, 대화 종료 의사를 명확하게 표현한 상황
- 사용자가 단순히 "그래", "오키"라고 답했다는 이유만으로 end를 선택하지 않는다.
- 사용자가 명확하게 대화를 끝내려 하면 짧고 자연스럽게 마무리한다.
- end를 선택했다면 불필요한 질문을 덧붙이지 않는다.

[ML 학습 Feature 분석]
아래 9개 Feature를 반드시 분석한다.

- preference_match: 캐릭터가 좋아하는 취향이나 가치관과 얼마나 일치하는지 (0.0~1.0)
- dislike_match: 캐릭터가 싫어하는 행동이나 가치관을 얼마나 건드렸는지 (0.0~1.0)
- empathy: 상대의 감정에 공감하고 배려하는 정도 (0.0~1.0)
- interest: 대화에 대한 관심과 적극성 (0.0~1.0)
- sincerity: 말과 행동의 진정성, 책임감, 솔직함 (0.0~1.0)
- context_match: 이전 대화와 현재 상황에 얼마나 자연스럽게 맞는지 (0.0~1.0)
- repetition_count: 이전 대화에서 같은 말이나 주제를 반복한 횟수 (0~3 정수)
- previous_affection: 현재 호감도 (0~100)
- previous_trust: 현재 신뢰도 (0~100)

[Feature 분석 주의사항]
- 모든 긍정적인 대화에 높은 값을 주지 않는다.
- 단순한 날씨나 일상적인 말은 interest와 preference_match를 낮거나 보통으로 둔다.
- 캐릭터의 선호와 비선호를 유형에 맞게 판단한다.
- 진심 어린 사과는 sincerity를 높게 평가하되 잘못의 반복 여부도 고려한다.
- 사과했다고 무조건 신뢰도가 완전히 회복되는 것은 아니다.
- 같은 주제의 반복은 repetition_count에 반영한다.
- 호감도와 신뢰도는 서로 다르게 판단한다.
- previous_affection과 previous_trust는 제공된 현재 점수를 그대로 사용한다.

[응답 형식]
반드시 JSON 형식으로만 응답한다.

{{
  "reply": "캐릭터의 자연스러운 대답",
  "conversation_status": "continue",
  "features": {{
    "preference_match": 0.0,
    "dislike_match": 0.0,
    "empathy": 0.0,
    "interest": 0.0,
    "sincerity": 0.0,
    "context_match": 0.0,
    "repetition_count": 0,
    "previous_affection": 20,
    "previous_trust": 20
  }},
  "reason": "호감도와 신뢰도 변화 판단 근거"
}}

JSON 이외의 설명은 출력하지 않는다.
"""


# ==========================================
# 4. 반복 대화 및 대화 종료 감지
# ==========================================

LOW_INFO_REPLIES = {
    "없어", "없는데", "없어요", "없습니다",
    "몰라", "몰라요", "그냥",
    "응", "어", "그래", "오키",
    "알았어", "알겠어", "ㅇㅇ", "ㅇㅋ"
}


def normalize_text(text):

    return re.sub(r"[\s\W_]+", "", text.lower())


def get_low_answer_streak(user_message):

    current = normalize_text(user_message)

    normalized_low_replies = {
        normalize_text(item) for item in LOW_INFO_REPLIES
    }

    if current not in normalized_low_replies:
        return 0

    count = 1

    previous_messages = [
        item["content"]
        for item in st.session_state.chat_history
        if item["role"] == "user"
    ]

    for message in reversed(previous_messages):

        if normalize_text(message) in normalized_low_replies:
            count += 1
        else:
            break

    return count


def is_repeated_reply(reply):

    current = normalize_text(reply)

    if not current:
        return False

    previous_replies = [
        item["content"]
        for item in st.session_state.chat_history
        if item["role"] == "assistant"
    ][-5:]

    for previous in previous_replies:

        old = normalize_text(previous)

        if not old:
            continue

        similarity = SequenceMatcher(
            None,
            current,
            old
        ).ratio()

        if current == old or similarity >= 0.78:
            return True

    return False


def get_fallback_reply(personality_type):

    if personality_type == "A":

        candidates = [
            "오늘은 말이 잘 안 나오는 날인가 보네. 괜찮아, 잠깐 쉬어가도 돼.",
            "굳이 얘깃거리를 찾지 않아도 괜찮아. 편하게 있어도 돼.",
            "오늘은 조용히 보내고 싶은가 보네. 나도 네 속도에 맞출게."
        ]

    else:

        candidates = [
            "ㅋㅋ 오늘은 말수가 적네. 그럴 때도 있지!",
            "오늘은 조용 모드구나? 괜찮아, 편하게 있어!",
            "꼭 재밌는 얘기 안 해도 돼. 그냥 쉬엄쉬엄 얘기하자."
        ]

    previous_replies = [
        normalize_text(item["content"])
        for item in st.session_state.chat_history
        if item["role"] == "assistant"
    ][-5:]

    def get_similarity(candidate):

        normalized = normalize_text(candidate)

        if not previous_replies:
            return 0

        return max(
            SequenceMatcher(
                None,
                normalized,
                previous
            ).ratio()
            for previous in previous_replies
        )

    return min(candidates, key=get_similarity)


def is_explicit_goodbye(message):

    goodbye_patterns = [
        r"집\s*갈래",
        r"집에\s*갈게",
        r"이제\s*가야",
        r"이제\s*갈게",
        r"이만\s*갈게",
        r"들어갈게",
        r"그만\s*하자",
        r"대화\s*끝내",
        r"대화\s*그만",
        r"잘\s*가",
        r"다음에\s*보자"
    ]

    return any(
        re.search(pattern, message)
        for pattern in goodbye_patterns
    )


# ==========================================
# 5. 점수 서버 연결 확인
# ==========================================

def check_score_server():

    try:

        response = requests.get(
            f"{SCORE_API_URL}/health",
            timeout=3
        )

        if response.status_code != 200:
            return False

        data = response.json()

        return data.get("status") == "ok"

    except (requests.RequestException, ValueError):

        return False


# ==========================================
# 6. GPT 대화 및 Feature 분석
# ==========================================

def get_gpt_response(user_message, personality_type, character):

    low_answer_streak = get_low_answer_streak(user_message)

    current_episode = st.session_state.unlocked_episode

    episode_info = EPISODE_INFO[current_episode]

    current_context = f"""
[현재 게임 상태]
- 선택된 학습 모델 유형: Type {personality_type}
- 현재 캐릭터: {character['name']}
- 현재 에피소드: EP {current_episode}
- 현재 장소: {episode_info['location']}
- 현재 에피소드 설명: {episode_info['description']}
- 현재 호감도: {st.session_state.affection}
- 현재 신뢰도: {st.session_state.trust}
- 현재 턴: {st.session_state.turn_count + 1}

[현재 대화 상황]
- 짧고 정보가 적은 답변이 연속된 횟수: {low_answer_streak}

[대화 대응 지침]
- 현재 에피소드의 장소와 상황을 대화에 자연스럽게 반영한다.
- 짧은 답변이 1회라면 자연스럽게 반응한다.
- 짧은 답변이 2회 이상이면 기존 질문을 반복하지 않는다.
- 짧은 답변이 계속되면 질문 대신 캐릭터의 생각이나 상황에 맞는 반응을 표현한다.
- 이전 AI 답변과 비슷한 문장을 사용하지 않는다.
- 대화를 억지로 끝내거나 반복적으로 작별 인사를 하지 않는다.
- 사용자가 명확하게 작별 의사를 표현한 경우에만 대화를 마무리한다.

위 현재 호감도와 신뢰도를 features의 previous_affection,
previous_trust에 그대로 입력한다.
"""

    messages = [
        {
            "role": "system",
            "content": create_system_prompt(character)
        },
        {
            "role": "system",
            "content": current_context
        }
    ]

    messages.extend(st.session_state.chat_history)

    messages.append({
        "role": "user",
        "content": user_message
    })

    result = None

    for attempt in range(2):

        request_messages = messages.copy()

        if attempt == 1:

            request_messages.insert(
                2,
                {
                    "role": "system",
                    "content": """
방금 생성한 응답이 이전 AI 답변과 유사하다.

이전 표현과 질문을 다시 사용하지 마라.
사용자의 마지막 메시지에 직접 반응하되,
이전과 다른 대화 방향과 표현을 사용하라.
짧은 답변이 반복되었다면 새로운 질문을 억지로 만들지 마라.
"""
                }
            )

        response = client.chat.completions.create(
            model=MODEL,
            messages=request_messages,
            response_format={"type": "json_object"},
            temperature=0.8
        )

        content = response.choices[0].message.content

        if not content:
            raise ValueError("GPT 응답이 비어 있습니다.")

        result = json.loads(content)

        reply = result.get("reply", "")

        if not reply:
            raise ValueError("GPT 응답에 reply가 없습니다.")

        if not is_repeated_reply(reply):
            break

    if is_repeated_reply(result["reply"]):

        result["reply"] = get_fallback_reply(personality_type)

    features = result.get("features", {})

    if not isinstance(features, dict):
        raise ValueError("GPT Feature 데이터 형식이 올바르지 않습니다.")

    try:

        model_repetition = int(
            features.get("repetition_count", 0)
        )

    except (ValueError, TypeError):

        model_repetition = 0

    features["repetition_count"] = min(
        3,
        max(
            0,
            model_repetition,
            low_answer_streak - 1
        )
    )

    features["previous_affection"] = st.session_state.affection
    features["previous_trust"] = st.session_state.trust

    result["features"] = features

    if is_explicit_goodbye(user_message):
        result["conversation_status"] = "end"
    else:
        result["conversation_status"] = "continue"

    return result


# ==========================================
# 7. XGBoost 점수 서버 요청
# ==========================================

def calculate_score(personality_type, features):

    try:

        response = requests.post(
            f"{SCORE_API_URL}/score",
            json={
                "personality_type": personality_type,
                "features": features
            },
            timeout=10
        )

        response.raise_for_status()

        return response.json()

    except requests.RequestException as e:

        detail = ""

        if getattr(e, "response", None) is not None:
            detail = f" / 응답: {e.response.text}"

        st.error(f"XGBoost 점수 서버 오류: {e}{detail}")

        return None


# ==========================================
# 8. 에피소드 시스템 함수
# ==========================================

def check_episode_success(episode):

    if episode == 1:

        return (
            st.session_state.affection >= 30
            and st.session_state.trust >= 20
        )

    if episode == 2:

        return (
            st.session_state.affection >= 40
            and st.session_state.trust >= 50
        )

    # EP3은 별도의 점수 조건 없이 5턴 완료 시 성공
    return True


def get_episode_start_turn(episode):

    return (episode - 1) * TURNS_PER_EPISODE


def get_episode_end_turn(episode):

    return episode * TURNS_PER_EPISODE


def rebuild_conversation_history(records):

    chat_history = []
    display_history = []

    for record in records:

        user_item = {
            "role": "user",
            "content": record["user_message"]
        }

        assistant_item = {
            "role": "assistant",
            "content": record["ai_reply"]
        }

        chat_history.extend([
            user_item,
            assistant_item
        ])

        display_history.extend([
            user_item.copy(),
            assistant_item.copy()
        ])

    return chat_history, display_history


def retry_current_episode():

    episode = st.session_state.unlocked_episode

    start_turn = get_episode_start_turn(episode)

    # 실패한 에피소드의 기록은 제거하고
    # 이전에 성공한 에피소드의 기록은 유지한다.
    retained_records = [
        record
        for record in st.session_state.feature_history
        if record["turn"] <= start_turn
    ]

    st.session_state.feature_history = retained_records

    # 남겨둔 기록을 기준으로 대화 내역 재구성
    chat_history, display_history = rebuild_conversation_history(
        retained_records
    )

    st.session_state.chat_history = chat_history
    st.session_state.display_history = display_history

    # 실패한 에피소드의 시작 턴으로 이동
    st.session_state.turn_count = start_turn

    # 점수는 유지
    # 대화 상태만 초기화
    st.session_state.episode_failed = False
    st.session_state.conversation_ended = False

    st.rerun()


def finish_episode(episode):

    if check_episode_success(episode):

        if episode not in st.session_state.completed_episodes:
            st.session_state.completed_episodes.append(episode)

        st.session_state.episode_failed = False

        if episode < 3:

            st.session_state.unlocked_episode = episode + 1

        else:

            st.session_state.game_completed = True

    else:

        st.session_state.episode_failed = True


# ==========================================
# 9. 세션 초기화
# ==========================================

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "display_history" not in st.session_state:
    st.session_state.display_history = []

if "feature_history" not in st.session_state:
    st.session_state.feature_history = []

if "affection" not in st.session_state:
    st.session_state.affection = INITIAL_AFFECTION

if "trust" not in st.session_state:
    st.session_state.trust = INITIAL_TRUST

if "personality_type" not in st.session_state:
    st.session_state.personality_type = "A"

if "selected_gender" not in st.session_state:
    st.session_state.selected_gender = "female"

if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0

if "conversation_ended" not in st.session_state:
    st.session_state.conversation_ended = False

# 에피소드 관련 상태
if "unlocked_episode" not in st.session_state:
    st.session_state.unlocked_episode = 1

if "completed_episodes" not in st.session_state:
    st.session_state.completed_episodes = []

if "episode_failed" not in st.session_state:
    st.session_state.episode_failed = False

if "game_completed" not in st.session_state:
    st.session_state.game_completed = False


# ==========================================
# 10. 선택된 캐릭터 정보 가져오기
# ==========================================

personality_type = st.session_state.personality_type
selected_gender = st.session_state.selected_gender

character = CHARACTERS[personality_type][selected_gender]


# ==========================================
# 11. 화면 구성 및 서버 연결
# ==========================================

st.title("💕 AI 연애 시뮬레이션")

st.caption(
    "GPT가 대화를 분석하고 XGBoost가 관계 점수 변화를 예측합니다."
)

if check_score_server():

    st.success("XGBoost 모델 서버 연결 완료")

else:

    st.error(
        "XGBoost 점수 서버에 연결할 수 없습니다. "
        "score_server_xgboost.py를 실행하고 모델 파일 경로를 확인해주세요."
    )

    st.stop()


# ==========================================
# 12. 사이드바
# ==========================================

with st.sidebar:

    st.header("💕 캐릭터 선택")

    selection_disabled = st.session_state.turn_count > 0

    gender_options = {
        "여성": "female",
        "남성": "male"
    }

    selected_gender_label = st.selectbox(
        "성별 선택",
        options=["여성", "남성"],
        index=0 if selected_gender == "female" else 1,
        disabled=selection_disabled
    )

    selected_gender = gender_options[selected_gender_label]

    personality_options = {
        "Type A - 안정형": "A",
        "Type B - 즉흥형": "B"
    }

    selected_personality_label = st.selectbox(
        "성격 유형 선택",
        options=list(personality_options.keys()),
        index=0 if personality_type == "A" else 1,
        disabled=selection_disabled
    )

    personality_type = personality_options[selected_personality_label]

    st.session_state.selected_gender = selected_gender
    st.session_state.personality_type = personality_type

    character = CHARACTERS[personality_type][selected_gender]

    st.divider()

    st.subheader("캐릭터 정보")

    st.write(f"**이름:** {character['name']}")
    st.write(f"**나이:** {character['age']}살")
    st.write(f"**성별:** {character['gender']}")
    st.write(f"**MBTI:** {character['mbti']}")
    st.write(f"**성격:** {character['personality'].strip()}")

    if selection_disabled:

        st.caption(
            "게임 진행 중에는 캐릭터를 변경할 수 없습니다. "
            "초기화 후 변경해주세요."
        )

    st.divider()

    st.subheader("현재 관계")

    st.metric(
        "호감도",
        f"{st.session_state.affection} / 100"
    )

    st.progress(st.session_state.affection / 100)

    st.metric(
        "신뢰도",
        f"{st.session_state.trust} / 100"
    )

    st.progress(st.session_state.trust / 100)

    st.divider()

    # 에피소드 진행 현황
    st.subheader("📖 에피소드 진행")

    for episode in range(1, 4):

        info = EPISODE_INFO[episode]

        if episode in st.session_state.completed_episodes:

            status = "✅ 완료"

        elif episode < st.session_state.unlocked_episode:

            status = "🔓 해금"

        elif episode == st.session_state.unlocked_episode:

            if st.session_state.episode_failed:
                status = "❌ 재도전 필요"
            else:
                status = "▶ 진행 가능"

        else:

            status = "🔒 잠금"

        st.write(f"**EP {episode}. {info['name']}**")
        st.caption(status)

    st.divider()

    st.subheader("현재 에피소드")

    if st.session_state.game_completed:

        st.success("🎉 모든 에피소드 완료!")

        st.metric(
            "전체 진행 턴",
            f"{TOTAL_TURNS} / {TOTAL_TURNS}"
        )

        st.progress(1.0)

    else:

        current_episode = st.session_state.unlocked_episode

        episode_info = EPISODE_INFO[current_episode]

        start_turn = get_episode_start_turn(current_episode)

        episode_turn = (
            st.session_state.turn_count - start_turn
        )

        st.metric(
            "현재 에피소드",
            f"EP {current_episode}"
        )

        st.write(f"**{episode_info['name']}**")

        st.caption(episode_info["location"])

        st.metric(
            "전체 진행 턴",
            f"{st.session_state.turn_count} / {TOTAL_TURNS}"
        )

        st.progress(
            min(
                st.session_state.turn_count / TOTAL_TURNS,
                1.0
            )
        )

        st.caption(
            f"에피소드 진행: {episode_turn} / {TURNS_PER_EPISODE}턴 완료"
        )

        if current_episode in EPISODE_CONDITIONS:

            condition = EPISODE_CONDITIONS[current_episode]

            st.caption(
                f"해금 조건: 호감도 {condition['affection']} 이상 / "
                f"신뢰도 {condition['trust']} 이상"
            )

    st.divider()

    if st.button("🔄 대화 초기화", use_container_width=True):

        st.session_state.chat_history = []
        st.session_state.display_history = []
        st.session_state.feature_history = []

        st.session_state.affection = INITIAL_AFFECTION
        st.session_state.trust = INITIAL_TRUST

        st.session_state.turn_count = 0
        st.session_state.conversation_ended = False

        st.session_state.unlocked_episode = 1
        st.session_state.completed_episodes = []
        st.session_state.episode_failed = False
        st.session_state.game_completed = False

        st.rerun()


# ==========================================
# 13. 탭 구성
# ==========================================

chat_tab, analysis_tab = st.tabs([
    "💕 대화 화면",
    "📊 AI 분석 기록"
])


# ==========================================
# 14. 대화 화면
# ==========================================

with chat_tab:

    current_episode = st.session_state.unlocked_episode

    episode_info = EPISODE_INFO[current_episode]

    st.subheader(
        f"EP {current_episode}. {episode_info['name']}"
    )

    st.caption(episode_info["description"])

    st.caption(f"📍 장소: {episode_info['location']}")

    st.divider()

    # 이전 대화 출력
    for chat in st.session_state.display_history:

        with st.chat_message(chat["role"]):

            st.write(chat["content"])

    # 전체 게임 완료
    if st.session_state.game_completed:

        st.success("🎉 모든 에피소드를 완료했습니다!")

        st.markdown(
            """
            ### 💕 데이트 시뮬레이션 완료

            세 번의 에피소드를 모두 마쳤습니다.

            캐릭터와의 최종 관계를 확인해 보세요.
            """
        )

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "최종 호감도",
                f"{st.session_state.affection} / 100"
            )

        with col2:
            st.metric(
                "최종 신뢰도",
                f"{st.session_state.trust} / 100"
            )

        st.info(
            "대화 초기화를 누르면 다른 캐릭터로 새롭게 시작할 수 있습니다."
        )

    # 에피소드 실패
    elif st.session_state.episode_failed:

        condition = EPISODE_CONDITIONS[current_episode]

        st.error(
            f"EP {current_episode} 해금 조건을 달성하지 못했습니다."
        )

        st.markdown("### 다음 에피소드 해금 조건")

        col1, col2 = st.columns(2)

        with col1:

            st.metric(
                "호감도",
                f"{st.session_state.affection} / {condition['affection']}",
                delta=(
                    st.session_state.affection
                    - condition["affection"]
                )
            )

        with col2:

            st.metric(
                "신뢰도",
                f"{st.session_state.trust} / {condition['trust']}",
                delta=(
                    st.session_state.trust
                    - condition["trust"]
                )
            )

        st.warning(
            "현재 에피소드를 다시 플레이해서 관계를 개선해 보세요. "
            "현재 호감도와 신뢰도는 유지됩니다."
        )

        if st.button(
            f"🔄 EP {current_episode} 다시 도전하기",
            use_container_width=True
        ):

            retry_current_episode()

    # 현재 에피소드 진행
    elif st.session_state.turn_count < get_episode_end_turn(current_episode):

        if st.session_state.conversation_ended:

            st.info("현재 대화가 종료되었습니다.")

            if st.button(
                "💬 대화 다시 시작",
                use_container_width=True
            ):

                st.session_state.conversation_ended = False

                st.rerun()

        else:

            user_message = st.chat_input(
                f"{character['name']}에게 말을 걸어보세요."
            )

            if user_message:

                try:

                    with st.spinner(
                        f"{character['name']}이(가) 대화를 분석하고 있어요..."
                    ):

                        # 1. GPT 캐릭터 응답 및 Feature 생성
                        result = get_gpt_response(
                            user_message,
                            st.session_state.personality_type,
                            character
                        )

                        reply = result["reply"]
                        features = result["features"]

                        # 2. 현재 점수 기록
                        previous_affection = st.session_state.affection
                        previous_trust = st.session_state.trust

                        features["previous_affection"] = previous_affection
                        features["previous_trust"] = previous_trust

                        # 3. XGBoost 점수 예측
                        score_result = calculate_score(
                            st.session_state.personality_type,
                            features
                        )

                        if score_result is None:
                            st.stop()

                        affection_delta = int(
                            score_result["affection_change"]
                        )

                        trust_delta = int(
                            score_result["trust_change"]
                        )

                        # 4. 점수 누적
                        st.session_state.affection = max(
                            0,
                            min(
                                100,
                                previous_affection + affection_delta
                            )
                        )

                        st.session_state.trust = max(
                            0,
                            min(
                                100,
                                previous_trust + trust_delta
                            )
                        )

                        # 5. 턴 및 에피소드 정보
                        current_turn = st.session_state.turn_count + 1
                        current_episode = st.session_state.unlocked_episode

                        # 6. 분석 기록 저장
                        analysis_record = {
                            "turn": current_turn,
                            "episode": current_episode,
                            "character": character["name"],
                            "user_message": user_message,
                            "ai_reply": reply,
                            "reason": result.get("reason", ""),
                            "features": features.copy(),

                            "affection_before": previous_affection,
                            "affection_delta": affection_delta,
                            "affection_after": st.session_state.affection,

                            "trust_before": previous_trust,
                            "trust_delta": trust_delta,
                            "trust_after": st.session_state.trust,

                            "affection_prediction": score_result["affection_prediction"],
                            "trust_prediction": score_result["trust_prediction"]
                        }

                        st.session_state.feature_history.append(
                            analysis_record
                        )

                        # 7. 대화 기록 저장
                        st.session_state.chat_history.append({
                            "role": "user",
                            "content": user_message
                        })

                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "content": reply
                        })

                        st.session_state.display_history.append({
                            "role": "user",
                            "content": user_message
                        })

                        st.session_state.display_history.append({
                            "role": "assistant",
                            "content": reply
                        })

                        # 8. 턴 증가
                        st.session_state.turn_count += 1

                        # 9. 대화 종료 상태 적용
                        conversation_status = result.get(
                            "conversation_status",
                            "continue"
                        )

                        if conversation_status not in ["continue", "end"]:
                            conversation_status = "continue"

                        if conversation_status == "end":
                            st.session_state.conversation_ended = True

                        # 10. 에피소드 종료 여부 확인
                        episode_completed_now = False
                        episode_failed_now = False

                        if (
                            st.session_state.turn_count
                            >= get_episode_end_turn(current_episode)
                        ):

                            finish_episode(current_episode)

                            if st.session_state.episode_failed:
                                episode_failed_now = True
                            else:
                                episode_completed_now = True

                        # 11. AI 응답 및 점수 출력
                        with st.chat_message("assistant"):

                            st.write(reply)

                            st.caption(
                                f"감정 판단: {result.get('reason', '분석 완료')}"
                            )

                            if conversation_status == "end":

                                st.info(
                                    "대화가 자연스럽게 마무리되었습니다."
                                )

                            st.divider()

                            col1, col2 = st.columns(2)

                            with col1:

                                st.metric(
                                    "호감도 변화",
                                    f"{affection_delta:+d}",
                                    delta=affection_delta
                                )

                            with col2:

                                st.metric(
                                    "신뢰도 변화",
                                    f"{trust_delta:+d}",
                                    delta=trust_delta
                                )

                            st.caption(
                                f"사용 모델: Type {score_result['personality_type']} "
                                f"| XGBoost 예측값: "
                                f"호감도 {score_result['affection_prediction']:.2f}, "
                                f"신뢰도 {score_result['trust_prediction']:.2f}"
                            )

                        # 12. 에피소드 결과 안내
                        if episode_completed_now:

                            if current_episode < 3:

                                st.success(
                                    f"🎉 EP {current_episode} 성공! "
                                    f"EP {current_episode + 1}이 해금되었습니다."
                                )

                            else:

                                st.success(
                                    "🎉 EP3까지 완료했습니다! "
                                    "모든 에피소드가 해금 및 완료되었습니다."
                                )

                        elif episode_failed_now:

                            st.warning(
                                f"EP {current_episode}의 해금 조건을 달성하지 못했습니다. "
                                "해당 에피소드를 다시 도전할 수 있습니다."
                            )

                    st.rerun()

                except (
                    KeyError,
                    TypeError,
                    ValueError,
                    json.JSONDecodeError
                ) as e:

                    st.error(f"GPT 분석 데이터 형식 오류: {e}")

                except Exception as e:

                    st.error(f"오류가 발생했습니다: {e}")


# ==========================================
# 15. AI 분석 기록 화면
# ==========================================

with analysis_tab:

    st.subheader("📊 대화별 AI 분석 기록")

    history = st.session_state.feature_history

    if not history:

        st.info(
            "아직 분석 기록이 없습니다. "
            "대화 화면에서 캐릭터와 대화를 시작해 주세요."
        )

    else:

        st.caption(
            f"총 {len(history)}회의 대화 분석 기록"
        )

        # 전체 기록 요약
        col1, col2, col3 = st.columns(3)

        col1.metric(
            "진행 턴",
            f"{st.session_state.turn_count} / {TOTAL_TURNS}"
        )

        col2.metric(
            "현재 호감도",
            st.session_state.affection
        )

        col3.metric(
            "현재 신뢰도",
            st.session_state.trust
        )

        st.divider()

        # 최신 대화부터 출력
        for record in reversed(history):

            title = (
                f"EP {record['episode']} | "
                f"{record['turn']}턴 | "
                f"{record['character']}"
            )

            with st.expander(title):

                st.markdown("### 👤 사용자 입력")
                st.write(record["user_message"])

                st.markdown("### 💕 AI 답변")
                st.write(record["ai_reply"])

                st.markdown("### 🧠 GPT 판단 근거")
                st.write(record["reason"])

                st.divider()

                st.markdown("### GPT 분석 Feature")

                st.json(record["features"])

                st.divider()

                st.markdown("### 호감도 변화")

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "이전",
                    record["affection_before"]
                )

                col2.metric(
                    "변화",
                    f"{record['affection_delta']:+d}"
                )

                col3.metric(
                    "현재",
                    record["affection_after"]
                )

                st.markdown("### 신뢰도 변화")

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "이전",
                    record["trust_before"]
                )

                col2.metric(
                    "변화",
                    f"{record['trust_delta']:+d}"
                )

                col3.metric(
                    "현재",
                    record["trust_after"]
                )

                st.divider()

                st.markdown("### XGBoost 예측값")

                col1, col2 = st.columns(2)

                col1.metric(
                    "호감도 예측",
                    f"{record['affection_prediction']:.2f}"
                )

                col2.metric(
                    "신뢰도 예측",
                    f"{record['trust_prediction']:.2f}"
                )

        st.divider()

        # 전체 기록 JSON 다운로드
        json_data = json.dumps(
            history,
            ensure_ascii=False,
            indent=4
        )

        st.download_button(
            label="📥 전체 분석 기록 다운로드",
            data=json_data,
            file_name="dating_simulation_analysis.json",
            mime="application/json",
            use_container_width=True
        )
