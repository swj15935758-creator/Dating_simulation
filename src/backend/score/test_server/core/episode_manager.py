
from services.llm_service import generate_opening_dialogue

from core.game_manager import (
    get_current_episode,
    get_previous_conversation
)


# ==========================================
# 1. GPT에 전달할 에피소드 시작 Context 구성
# ==========================================

def build_opening_context(state: dict) -> dict:
    """
    에피소드 시작 시 GPT에 전달할 대화 Context를 구성한다.
    이전 에피소드가 있다면 이전 대화 기록도 전달한다.
    """

    return {
        "conversation_history": state["conversation_history"],
        "previous_conversation": get_previous_conversation(state),
        "current_episode": state["current_episode"],
        "conversation_count": state["total_turn"],
        "affection": state["affection"],
        "trust": state["trust"],
        "memory": state.get("memory", [])
    }


# ==========================================
# 2. 에피소드 시작 정보 생성
# ==========================================

def start_episode(state: dict, movie_info: dict = None) -> dict:
    """
    현재 에피소드의 장면 정보와 오프닝 대사를 준비한다.

    장면 설명은 episodes.py의 고정 문구를 사용한다.
    오프닝 대사는 GPT가 캐릭터 성격과 대화 기록을 참고해 생성한다.

    오프닝 대사는 실제 턴 수와 점수 계산에 포함하지 않는다.
    """

    # 게임 종료 여부 확인
    if state["is_finished"]:
        raise ValueError("이미 종료된 게임입니다.")

    # 현재 에피소드 정보 가져오기
    episode = get_current_episode(state)

    # EP2 영화 정보 반영
    if state["current_episode"] == 2:
        if movie_info:
            episode["movie"] = {
                "title": movie_info.get("title", ""),
                "genre": movie_info.get("genre", ""),
                "summary": movie_info.get("summary", "")
            }

    # 오프닝 대사 중복 생성 방지용 저장 공간
    opening_cache = state.setdefault("episode_openings", {})

    episode_number = state["current_episode"]

    # 이미 생성한 오프닝 대사가 있으면 재사용
    if episode_number in opening_cache:
        opening_dialogue = opening_cache[episode_number]

    else:
        # GPT에 전달할 Context 구성
        context = build_opening_context(state)

        # GPT가 캐릭터의 첫 대사 생성
        result = generate_opening_dialogue(
            persona=state["persona"],
            context=context,
            episode=episode
        )

        # GPT 응답 확인
        print("\n===== GPT 오프닝 응답 확인 =====")
        print("응답 자료형:", type(result))
        print("응답 내용:", repr(result))
        print("================================\n")

        # GPT 응답은 문자열로 반환된다.
        opening_dialogue = result

        # 오프닝 대사 유효성 검사
        if not isinstance(opening_dialogue, str):
            raise ValueError(
                f"GPT 오프닝 응답이 문자열이 아닙니다: {result}"
            )

        if not opening_dialogue.strip():
            raise ValueError("GPT 오프닝 대사가 비어 있습니다.")

        # 생성한 오프닝 대사 저장
        opening_cache[episode_number] = opening_dialogue

    # UI에 전달할 에피소드 시작 정보
    return {
        "episode_number": episode["episode_id"],
        "episode_name": episode["episode_name"],
        "location": episode["location"],
        "time": episode["time"],
        "scene_image_prompt": episode["scene_image_prompt"],
        "scene_description": episode["scene_description"],
        "opening_dialogue": opening_dialogue,
        "movie": episode.get("movie")
    }


# ==========================================
# 3. 에피소드 시작 가능 여부 확인
# ==========================================

def can_start_episode(state: dict) -> bool:
    """
    현재 게임 상태에서 에피소드를 시작할 수 있는지 확인한다.
    """

    # 게임이 종료되었다면 시작 불가
    if state["is_finished"]:
        return False

    # 첫 에피소드 또는 다음 에피소드로 이동한 직후
    return state["current_turn"] == 0
