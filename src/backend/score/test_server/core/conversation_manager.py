
from services.llm_service import (
    generate_character_response,
    analyze_conversation
)

from services.score_service import predict_score

from core.game_manager import (
    complete_turn,
    get_current_episode,
    get_previous_conversation
)


# ==========================================
# 1. 대화에 필요한 Context 구성
# ==========================================

def build_conversation_context(state: dict) -> dict:
    """
    현재 게임 상태를 GPT에 전달할 Context로 구성한다.
    """

    return {
        "conversation_history": state["conversation_history"],
        "current_episode": state["current_episode"],
        "conversation_count": state["total_turn"],
        "affection": state["affection"],
        "trust": state["trust"],
        "previous_behavior": state.get("previous_behavior", ""),
        "relationship_state": state.get("relationship_state", ""),
        "memory": state.get("memory", [])
    }


# ==========================================
# 2. 반복 대화 횟수 계산
# ==========================================

def calculate_repetition_count(
    state: dict,
    user_message: str
) -> int:
    """
    최근 사용자 메시지와 동일한 문장이 반복된 횟수를 계산한다.
    점수 서버의 입력 범위에 맞춰 0~3으로 제한한다.
    """

    # 공백을 정리하고 소문자로 변환
    current_message = " ".join(user_message.strip().lower().split())

    # 최근 사용자 대화 3개 확인
    recent_messages = [
        record["user_message"]
        for record in state["conversation_history"][-3:]
    ]

    repetition_count = 0

    for previous_message in recent_messages:
        normalized_message = " ".join(
            previous_message.strip().lower().split()
        )

        if current_message == normalized_message:
            repetition_count += 1

    return min(3, repetition_count)


# ==========================================
# 3. GPT 분석 특성에 Python 특성 추가
# ==========================================

def build_score_features(
    analysis: dict,
    state: dict,
    user_message: str
) -> dict:
    """
    GPT 분석 결과 6개와 Python 관리 특성 3개를 합친다.

    GPT 분석:
    preference_match
    dislike_match
    empathy
    interest
    sincerity
    context_match

    Python 관리:
    repetition_count
    previous_affection
    previous_trust
    """

    # GPT가 분석한 6개 특성
    features = analysis["features"].copy()

    # Python에서 계산하는 3개 특성
    features["repetition_count"] = calculate_repetition_count(
        state,
        user_message
    )

    features["previous_affection"] = state["affection"]
    features["previous_trust"] = state["trust"]

    return features


# ==========================================
# 4. 사용자 대화 처리
# ==========================================

def process_user_turn(
    state: dict,
    user_message: str
) -> dict:
    """
    사용자 메시지 한 건을 처리한다.

    GPT 답변 생성
    → GPT 대화 분석
    → XGBoost 점수 예측
    → 게임 상태 업데이트

    이 함수 한 번이 실제 게임의 한 턴이다.
    """

    # 빈 메시지 확인
    if not isinstance(user_message, str) or not user_message.strip():
        raise ValueError("대화 내용을 입력해 주세요.")

    # 게임 종료 여부 확인
    if state["is_finished"]:
        raise ValueError("이미 종료된 게임입니다.")

    # 다음 에피소드로 이동해야 하는지 확인
    if state["can_transition"]:
        raise ValueError(
            "다음 에피소드로 이동한 후 대화할 수 있습니다."
        )

    # 캐릭터 정보
    persona = state["persona"]

    # 현재 에피소드 정보
    episode = get_current_episode(state)

    # GPT에 전달할 Context
    context = build_conversation_context(state)

    # ======================================
    # 1단계: GPT 캐릭터 답변 생성
    # ======================================

    character_result = generate_character_response(
        persona,
        context,
        episode,
        user_message
    )

    # GPT 응답은 문자열로 반환된다.
    character_message = character_result

    # 캐릭터 응답 유효성 검사
    if not isinstance(character_message, str):
        raise ValueError(
            f"캐릭터 응답이 문자열이 아닙니다: {character_result}"
        )

    if not character_message.strip():
        raise ValueError("캐릭터 응답이 비어 있습니다.")

    # ======================================
    # 2단계: 완료된 대화 분석
    # ======================================

    analysis = analyze_conversation(
        persona,
        context,
        user_message,
        character_message
    )

    print("\n===== GPT 분석 결과 =====")
    print(analysis)

    # ======================================
    # 3단계: XGBoost 입력 특성 구성
    # ======================================

    features = build_score_features(
        analysis,
        state,
        user_message
    )

    print("\n===== XGBoost 입력 특성 =====")
    print(features)

    # ======================================
    # 4단계: XGBoost 점수 예측
    # ======================================

    personality_type = persona["personality_type"]

    score_prediction = predict_score(
        personality_type,
        features
    )

    print("\n===== XGBoost 예측 결과 =====")
    print(score_prediction)

    # ======================================
    # 5단계: 게임 상태 업데이트
    # ======================================

    # 점수 반영 전 상태
    previous_affection = state["affection"]
    previous_trust = state["trust"]

    turn_result = complete_turn(
        state=state,
        user_message=user_message,
        character_message=character_message,
        affection_change=score_prediction["affection_change"],
        trust_change=score_prediction["trust_change"],
        analysis=analysis
    )

    # 점수 반영 후 상태
    print("\n===== 점수 반영 결과 =====")
    print(
        f"호감도: {previous_affection} → {state['affection']}"
    )
    print(
        f"신뢰도: {previous_trust} → {state['trust']}"
    )

    print("\n===== 게임 진행 상태 =====")
    print(f"현재 에피소드: {state['current_episode']}")
    print(f"현재 턴: {state['current_turn']}")
    print(f"전체 턴: {state['total_turn']}")

    # ======================================
    # 6단계: 사용자에게 보여줄 결과
    # ======================================

    return {
        "reply": character_message,
        "progress": turn_result["progress"]
    }
