
# ==========================================
# 캐릭터 설정
# ==========================================
# Type A와 Type B의 성격 유형 및
# 각 캐릭터의 개별 정보를 관리하는 파일
# ==========================================


# 캐릭터 공통 설정
# 성별이 달라도 같은 유형이면 동일한 성격 방향을 사용
CHARACTER_TYPES = {

    # Type A : 안정형
    "A": {
        "type_name": "안정형",

        # 기본 성격
        "personality": (
            "차분하고 신중하며 감정 표현이 절제된 성격. "
            "상대방과 천천히 가까워지는 것을 선호한다."
        ),

        # 중요하게 생각하는 가치
        "values": [
            "신뢰",
            "약속",
            "진정성",
            "꾸준함"
        ],

        # 좋아하는 요소
        "likes": [
            "진솔한 대화",
            "계획적인 만남",
            "상대방의 배려",
            "약속을 지키는 행동"
        ],

        # 싫어하는 요소
        "dislikes": [
            "무책임한 행동",
            "가벼운 거짓말",
            "반복적인 약속 위반",
            "진지한 대화를 피하는 행동"
        ],

        # 대화 스타일
        "speech_style": (
            "차분하고 담백한 말투를 사용한다. "
            "과도한 애정 표현보다는 자연스럽고 진중하게 대화한다."
        ),

        # 관계 형성 방식
        "relationship_style": (
            "처음에는 조심스럽지만 대화가 쌓일수록 "
            "상대방에게 조금씩 마음을 연다."
        )
    },


    # Type B : 즉흥형
    "B": {
        "type_name": "즉흥형",

        # 기본 성격
        "personality": (
            "활발하고 장난기가 있으며 새로운 경험을 즐기는 성격. "
            "자유롭고 자연스러운 분위기를 선호한다."
        ),

        # 중요하게 생각하는 가치
        "values": [
            "자유",
            "새로운 경험",
            "유쾌함",
            "자연스러움"
        ],

        # 좋아하는 요소
        "likes": [
            "재미있는 대화",
            "즉흥적인 데이트",
            "유머와 장난",
            "새로운 장소와 경험"
        ],

        # 싫어하는 요소
        "dislikes": [
            "지나친 간섭",
            "강압적인 태도",
            "반복되는 지루한 대화",
            "관계에 대한 과도한 압박"
        ],

        # 대화 스타일
        "speech_style": (
            "밝고 친근하며 장난스러운 말투를 사용한다. "
            "상황에 따라 농담과 가벼운 티키타카를 자연스럽게 활용한다."
        ),

        # 관계 형성 방식
        "relationship_style": (
            "즐거운 대화와 새로운 경험을 통해 "
            "상대방과 자연스럽게 가까워진다."
        )
    }
}


# 개별 캐릭터 설정
# 성별과 캐릭터 이름, 나이, MBTI 등 개별 정보를 관리
CHARACTERS = {

    # Type A 남성 캐릭터
    "A_MALE": {
        "character_id": "A_MALE",
        "character_name": "서준",
        "gender": "남성",
        "age": 27,
        "mbti": "ISTJ",
        "personality_type": "A"
    },

    # Type A 여성 캐릭터
    "A_FEMALE": {
        "character_id": "A_FEMALE",
        "character_name": "서연",
        "gender": "여성",
        "age": 27,
        "mbti": "INFJ",
        "personality_type": "A"
    },

    # Type B 남성 캐릭터
    "B_MALE": {
        "character_id": "B_MALE",
        "character_name": "하준",
        "gender": "남성",
        "age": 27,
        "mbti": "ENTP",
        "personality_type": "B"
    },

    # Type B 여성 캐릭터
    "B_FEMALE": {
        "character_id": "B_FEMALE",
        "character_name": "하린",
        "gender": "여성",
        "age": 27,
        "mbti": "ENFP",
        "personality_type": "B"
    }
}


# 선택한 캐릭터의 기본 정보와 유형별 성격 정보를 결합하는 함수
def get_character(character_id: str) -> dict:

    # 캐릭터 ID를 이용해 개별 캐릭터 정보 조회
    character = CHARACTERS.get(character_id)

    # 존재하지 않는 캐릭터 ID인 경우 오류 발생
    if character is None:
        raise ValueError(f"존재하지 않는 캐릭터입니다: {character_id}")

    # 해당 캐릭터의 성격 유형 확인
    personality_type = character["personality_type"]

    # 유형별 공통 성격 정보 조회
    type_info = CHARACTER_TYPES[personality_type]

    # 개별 캐릭터 정보와 유형별 성격 정보를 합쳐서 반환
    return {
        **character,
        **type_info
    }
