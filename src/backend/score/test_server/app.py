
import streamlit as st

from config.characters import get_character
from core.game_manager import (
    create_game_state,
    transition_episode,
    get_ending
)
from core.episode_manager import start_episode
from core.conversation_manager import process_user_turn


# ==========================================
# 1. 페이지 설정
# ==========================================

st.set_page_config(
    page_title="HEARTLINE",
    page_icon="💗",
    layout="centered"
)


# ==========================================
# 2. 캐릭터 선택 정보
# ==========================================

CHARACTER_OPTIONS = {
    "A_MALE": "서준 · 안정형 남성",
    "A_FEMALE": "서연 · 안정형 여성",
    "B_MALE": "하준 · 즉흥형 남성",
    "B_FEMALE": "하린 · 즉흥형 여성"
}


# ==========================================
# 3. 세션 상태 초기화
# ==========================================

def initialize_session():

    default_values = {
        "game_state": None,
        "episode_data": None,
        "movie_info": {
            "title": "",
            "genre": "",
            "summary": ""
        },
        "error_message": ""
    }

    for key, value in default_values.items():

        if key not in st.session_state:
            st.session_state[key] = value


def reset_game():

    keys_to_reset = [
        "game_state",
        "episode_data",
        "movie_info",
        "error_message"
    ]

    for key in keys_to_reset:

        if key in st.session_state:
            del st.session_state[key]

    initialize_session()


initialize_session()


# ==========================================
# 4. 화면 제목
# ==========================================

st.title("💗 HEARTLINE")
st.caption("AI 음성 대화형 연애 시뮬레이션")

st.divider()


# ==========================================
# 5. 게임 시작 화면
# ==========================================

if st.session_state.game_state is None:

    st.subheader("캐릭터 선택")

    with st.form("character_select_form"):

        character_id = st.selectbox(
            "만나고 싶은 캐릭터를 선택하세요.",
            options=list(CHARACTER_OPTIONS.keys()),
            format_func=lambda value: CHARACTER_OPTIONS[value]
        )

        st.divider()

        st.subheader("EP2 영화 정보")

        st.caption(
            "두 번째 에피소드에서 함께 관람할 영화 정보를 입력해 주세요."
        )

        movie_title = st.text_input(
            "영화 제목",
            placeholder="예: 인터스텔라"
        )

        movie_genre = st.text_input(
            "영화 장르",
            placeholder="예: SF, 드라마"
        )

        movie_summary = st.text_area(
            "영화 줄거리",
            placeholder="영화의 간단한 줄거리를 입력해 주세요."
        )

        start_button = st.form_submit_button(
            "게임 시작",
            use_container_width=True
        )

    if start_button:

        try:

            # 캐릭터 정보 가져오기
            persona = get_character(character_id)

            # 게임 상태 생성
            game_state = create_game_state(persona)

            # 영화 정보 저장
            movie_info = {
                "title": movie_title.strip(),
                "genre": movie_genre.strip(),
                "summary": movie_summary.strip()
            }

            # EP1 시작
            episode_data = start_episode(game_state)

            # 세션에 저장
            st.session_state.game_state = game_state
            st.session_state.episode_data = episode_data
            st.session_state.movie_info = movie_info
            st.session_state.error_message = ""

            st.rerun()

        except Exception as error:

            st.error(
                f"게임 시작 중 오류가 발생했습니다: {error}"
            )


# ==========================================
# 6. 게임 진행 화면
# ==========================================

else:

    state = st.session_state.game_state
    episode = st.session_state.episode_data
    persona = state["persona"]

    # --------------------------------------
    # 6-1. 사이드바
    # --------------------------------------

    with st.sidebar:

        st.subheader("개발자 테스트 정보")

        st.metric(
            "현재 호감도",
            int(round(state["affection"]))
        )

        st.metric(
            "현재 신뢰도",
            int(round(state["trust"]))
        )

        st.divider()

        st.write(
            f"현재 에피소드: {state['current_episode']}"
        )

        st.write(
            f"현재 턴: {state['current_turn']} / 5"
        )

        st.write(
            f"전체 턴: {state['total_turn']} / 15"
        )

        st.divider()

        # 대화 초기화 버튼
        if st.button(
            "🔄 대화 초기화",
            use_container_width=True
        ):

            reset_game()
            st.rerun()

    # --------------------------------------
    # 6-2. 캐릭터 정보
    # --------------------------------------

    character_name = persona.get(
        "character_name",
        "캐릭터"
    )

    mbti = persona.get(
        "mbti",
        persona.get("MBTI", "")
    )

    st.subheader(f"💗 {character_name}")

    if mbti:
        st.caption(f"MBTI · {mbti}")

    st.divider()

    # --------------------------------------
    # 6-3. 에피소드 정보
    # --------------------------------------

    st.subheader(
        f"EP{episode['episode_number']} · {episode['episode_name']}"
    )

    st.write(f"📍 장소: {episode['location']}")
    st.write(f"🕒 시간: {episode['time']}")

    # --------------------------------------
    # 6-4. 장면 이미지 영역
    # --------------------------------------

    st.markdown("### 🎬 현재 장면")

    st.info(
        episode.get("scene_image_prompt", "장면 이미지 준비 영역")
    )

    # --------------------------------------
    # 6-5. 장면 설명
    # --------------------------------------

    st.markdown("### 📖 장면 설명")

    st.write(
        episode["scene_description"]
    )

    st.divider()

    # --------------------------------------
    # 6-6. 캐릭터 첫 대사
    # --------------------------------------

    st.markdown("### 💬 캐릭터")

    st.chat_message(
        "assistant",
        avatar="💗"
    ).write(
        episode["opening_dialogue"]
    )

    st.divider()

    # --------------------------------------
    # 6-7. 이전 대화 기록
    # --------------------------------------

    st.markdown("### 🗨️ 대화 기록")

    for record in state["conversation_history"]:

        with st.chat_message("user"):

            st.write(
                record["user_message"]
            )

        with st.chat_message(
            "assistant",
            avatar="💗"
        ):

            st.write(
                record["character_message"]
            )

    # --------------------------------------
    # 6-8. 진행 상황
    # --------------------------------------

    current_turn = state["current_turn"]

    st.progress(
        current_turn / 5,
        text=f"EP{state['current_episode']} 진행도 · {current_turn}/5"
    )

    st.caption(
        f"전체 진행 · {state['total_turn']}/15"
    )

    # --------------------------------------
    # 6-9. 오류 메시지
    # --------------------------------------

    if st.session_state.error_message:

        st.error(
            st.session_state.error_message
        )

    # --------------------------------------
    # 6-10. 게임 종료
    # --------------------------------------

    if state["is_finished"]:

        st.divider()

        st.title("💗 데이트 종료")

        ending = get_ending(state)

        st.success(
            f"최종 엔딩: {ending}"
        )

        st.write(
            "HEARTLINE과 함께한 3개의 에피소드가 모두 끝났습니다."
        )

        if st.button(
            "새로운 데이트 시작",
            use_container_width=True
        ):

            reset_game()
            st.rerun()

    # --------------------------------------
    # 6-11. 다음 에피소드 이동
    # --------------------------------------

    elif state["can_transition"]:

        st.divider()

        st.success(
            f"EP{state['current_episode']} 대화가 완료되었습니다."
        )

        if st.button(
            "다음 에피소드로 이동",
            use_container_width=True
        ):

            try:

                # 다음 에피소드로 상태 변경
                transition_episode(state)

                # 다음 에피소드 오프닝 생성
                next_episode = start_episode(
                    state,
                    movie_info=st.session_state.movie_info
                )

                st.session_state.episode_data = next_episode
                st.session_state.error_message = ""

                st.rerun()

            except Exception as error:

                st.session_state.error_message = (
                    f"다음 에피소드 이동 중 오류: {error}"
                )

                st.rerun()

    # --------------------------------------
    # 6-12. 사용자 대화 입력
    # --------------------------------------

    else:

        user_message = st.chat_input(
            "캐릭터에게 메시지를 입력하세요."
        )

        if user_message:

            try:

                with st.spinner(
                    "캐릭터가 답변을 생각하고 있습니다..."
                ):

                    result = process_user_turn(
                        state,
                        user_message
                    )

                st.session_state.error_message = ""

                st.rerun()

            except Exception as error:

                st.session_state.error_message = (
                    f"대화 처리 중 오류가 발생했습니다: {error}"
                )

                st.rerun()
