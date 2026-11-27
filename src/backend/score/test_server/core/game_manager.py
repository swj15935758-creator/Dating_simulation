
from config.settings import (
    INITIAL_AFFECTION,
    INITIAL_TRUST,
    MIN_SCORE,
    MAX_SCORE,
    TOTAL_EPISODES,
    TURNS_PER_EPISODE,
    TOTAL_TURNS
)

from config.episodes import get_episode


# ==========================================
# 1. 새로운 게임 상태 생성
# ==========================================

def create_game_state(persona: dict) -> dict:
    """
    새로운 게임을 시작할 때 기본 상태를 생성한다.

    persona: 선택한 캐릭터 정보
    """

    return {
        # 선택한 캐릭터 정보
        "persona": persona,

        # 현재 진행 상태
        "current_episode": 1,
        "current_turn": 0,
        "total_turn": 0,

        # 현재 관계 점수
        "affection": INITIAL_AFFECTION,
        "trust": INITIAL_TRUST,

        # 대화 기록
        "conversation_history": [],

        # 에피소드별 대화 기록
        "episode_history": {
            1: [],
            2: [],
            3: []
        },

        # 이전 대화에서 추출한 주요 정보
        "memory": [],

        # 게임 종료 여부
        "is_finished": False,

        # 다음 에피소드로 이동할 수 있는지
        "can_transition": False
    }


# ==========================================
# 2. 현재 에피소드 정보 가져오기
# ==========================================

def get_current_episode(state: dict) -> dict:
    """
    현재 진행 중인 에피소드 정보를 가져온다.
    """

    episode_number = state["current_episode"]

    return get_episode(episode_number)


# ==========================================
# 3. 현재 게임 진행 정보 확인
# ==========================================

def get_game_progress(state: dict) -> dict:
    """
    현재 에피소드와 전체 턴 진행 상황을 반환한다.
    """

    return {
        "current_episode": state["current_episode"],
        "current_turn": state["current_turn"],
        "turns_per_episode": TURNS_PER_EPISODE,
        "total_turn": state["total_turn"],
        "total_turns": TOTAL_TURNS,
        "is_episode_finished": state["can_transition"],
        "is_game_finished": state["is_finished"]
    }


# ==========================================
# 4. 점수 업데이트
# ==========================================

def update_scores(
    state: dict,
    affection_change: int,
    trust_change: int
) -> dict:
    """
    XGBoost에서 예측한 점수 변화량을 적용한다.

    한 턴 변화량은 각각 -10~+10으로 제한한다.
    최종 점수는 0~100 범위로 제한한다.
    """

    # 한 턴의 점수 변화량 제한
    affection_change = max(
        -10,
        min(10, int(affection_change))
    )

    trust_change = max(
        -10,
        min(10, int(trust_change))
    )

    # 기존 점수에 변화량 적용
    new_affection = state["affection"] + affection_change
    new_trust = state["trust"] + trust_change

    # 최종 점수 범위 제한
    state["affection"] = max(
        MIN_SCORE,
        min(MAX_SCORE, new_affection)
    )

    state["trust"] = max(
        MIN_SCORE,
        min(MAX_SCORE, new_trust)
    )

    return {
        "affection_change": affection_change,
        "trust_change": trust_change,
        "affection": state["affection"],
        "trust": state["trust"]
    }


# ==========================================
# 5. 대화 한 턴 완료 처리
# ==========================================

def complete_turn(
    state: dict,
    user_message: str,
    character_message: str,
    affection_change: int,
    trust_change: int,
    analysis: dict = None
) -> dict:
    """
    사용자 메시지와 캐릭터 답변이 완료된 후
    대화 기록, 점수, 턴을 업데이트한다.

    한 턴 = 사용자 메시지 1개 + 캐릭터 답변 1개

    오프닝 대화는 이 함수에 전달하지 않는다.
    """

    # 이미 게임이 끝났는지 확인
    if state["is_finished"]:
        raise ValueError("이미 종료된 게임입니다.")

    # 현재 에피소드의 5턴이 완료되었는지 확인
    if state["can_transition"]:
        raise ValueError(
            "현재 에피소드가 종료되었습니다. "
            "다음 에피소드로 먼저 이동하세요."
        )

    # 현재 에피소드 번호
    episode_number = state["current_episode"]

    # 이번 턴의 대화 기록
    turn_record = {
        "episode": episode_number,
        "turn": state["current_turn"] + 1,
        "user_message": user_message,
        "character_message": character_message,
        "analysis": analysis or {}
    }

    # 전체 대화 기록에 저장
    state["conversation_history"].append(turn_record)

    # 현재 에피소드 대화 기록에 저장
    state["episode_history"][episode_number].append(
        turn_record
    )

    # 점수 업데이트
    score_result = update_scores(
        state,
        affection_change,
        trust_change
    )

    # 턴 수 증가
    state["current_turn"] += 1
    state["total_turn"] += 1

    # 에피소드 5턴 완료 여부 확인
    if state["current_turn"] >= TURNS_PER_EPISODE:
        state["can_transition"] = True

    # 전체 15턴 완료 여부 확인
    if state["total_turn"] >= TOTAL_TURNS:
        state["is_finished"] = True
        state["can_transition"] = False

    return {
        "turn_record": turn_record,
        "score_result": score_result,
        "progress": get_game_progress(state)
    }


# ==========================================
# 6. 다음 에피소드로 이동
# ==========================================

def transition_episode(state: dict) -> dict:
    """
    현재 에피소드의 5턴이 완료되었을 때
    다음 에피소드로 이동한다.

    마지막 에피소드에서는 이동할 수 없다.
    """

    if state["is_finished"]:
        raise ValueError("게임이 이미 종료되었습니다.")

    if not state["can_transition"]:
        raise ValueError(
            "현재 에피소드의 5턴을 모두 완료해야 합니다."
        )

    if state["current_episode"] >= TOTAL_EPISODES:
        raise ValueError("마지막 에피소드입니다.")

    # 다음 에피소드로 이동
    state["current_episode"] += 1

    # 새 에피소드의 턴 초기화
    state["current_turn"] = 0

    # 전환 상태 초기화
    state["can_transition"] = False

    return get_current_episode(state)


# ==========================================
# 7. 에피소드별 대화 기억 가져오기
# ==========================================

def get_previous_conversation(state: dict) -> list:
    """
    이전 에피소드에서 나눈 대화를 가져온다.

    현재 에피소드의 이전 에피소드 기록만 반환한다.
    """

    current_episode = state["current_episode"]

    previous_conversations = []

    for episode_number in range(1, current_episode):
        previous_conversations.extend(
            state["episode_history"][episode_number]
        )

    return previous_conversations


# ==========================================
# 8. 최종 엔딩 판정
# ==========================================

def get_ending(state):

    affection = state["affection"]
    trust = state["trust"]

    # 호감도와 신뢰도의 평균 계산
    average_score = (affection + trust) / 2

    # 엔딩 판정
    if average_score >= 90:
        return "연인 엔딩"

    elif average_score >= 80:
        return "썸 엔딩"

    elif average_score >= 70:
        return "친구 엔딩"

    else:
        return "남남 엔딩"