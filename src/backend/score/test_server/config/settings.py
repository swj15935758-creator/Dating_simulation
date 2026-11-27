
import os
from pathlib import Path
from dotenv import load_dotenv

# 테스트 서버 루트 경로
BASE_DIR = Path(__file__).resolve().parents[1]

# 테스트 서버 내부 .env 불러오기
load_dotenv(BASE_DIR / ".env")

# API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

SCORE_API_URL = os.getenv(
    "SCORE_API_URL",
    "http://127.0.0.1:8765"
)

# 게임 기본 설정
INITIAL_AFFECTION = 20
INITIAL_TRUST = 20

MAX_SCORE = 100
MIN_SCORE = 0

TOTAL_EPISODES = 3
TURNS_PER_EPISODE = 5
TOTAL_TURNS = TOTAL_EPISODES * TURNS_PER_EPISODE

# 턴당 점수 변화 제한
MIN_SCORE_CHANGE = -10
MAX_SCORE_CHANGE = 10

# 최종 엔딩 기준
ENDING_THRESHOLDS = {
    "연인 엔딩": 90,
    "썸 엔딩": 80,
    "친구 엔딩": 70,
    "남남 엔딩": 0
}
