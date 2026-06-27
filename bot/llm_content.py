"""
Gemini API를 이용한 콘텐츠 자동 생성.

content.py의 정적 풀 조회 함수와 동일한 반환 타입(딕셔너리)을 맞춰서,
호출하는 쪽(scheduler, cogs)이 정적 풀이든 LLM 생성이든 신경 쓸 필요 없게 한다.

실패(API 에러, 타임아웃, 키 누락 등) 시에는 예외를 던지고,
호출부에서 정적 풀로 폴백하도록 설계한다.
"""

import os
import random
import logging
from pydantic import BaseModel, Field

from google import genai

logger = logging.getLogger("llm_content")

MODEL_NAME = "gemini-2.5-flash"  # 무료 tier 한도가 넉넉한 경량 모델


def _get_client() -> genai.Client:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    return genai.Client(api_key=api_key)


# ---------------------------------------------------------------------------
# 영어 섀도잉 시나리오 생성
# ---------------------------------------------------------------------------

# 매 생성마다 이 중 하나를 강제로 골라서 프롬프트에 박아넣는다.
# 모델이 스스로 "다양하게" 고르라고 하면 결국 비슷한 상황(마감/보고서)으로 수렴하기 때문에,
# 우리가 직접 무작위로 골라서 강제하는 방식으로 다양성을 확보한다.
ENGLISH_SCENARIOS = [
    "동료가 갑자기 아파서 결근했을 때 업무를 나눠 맡는 상황",
    "회의 시간을 깜빡 잊고 늦게 들어온 동료와의 대화",
    "새로 산 사무용품/장비가 고장 나서 불평하는 잡담",
    "점심 메뉴를 고민하며 나누는 가벼운 수다",
    "상사가 갑자기 추가 업무를 던져줬을 때의 반응",
    "퇴근 직전에 갑자기 잡힌 화상회의에 대한 불만",
    "팀 회식/모임 일정을 잡으려는 대화",
    "출근길 지하철/교통 상황에 대한 잡담",
    "새 동료를 처음 소개받는 상황",
    "주말 계획을 묻고 답하는 가벼운 대화",
    "프로젝트가 생각보다 일찍 끝나서 여유로운 분위기의 대화",
    "사내 시스템/장비 오류로 답답해하는 상황",
    "휴가 신청을 어떻게 할지 의논하는 대화",
    "재택근무 중 화상회의에서 생긴 사소한 해프닝",
    "동료의 승진/좋은 소식을 축하하는 대화",
]

# 모델이 디폴트로 자주 꺼내는 "교재형 비즈니스 표현"은 명시적으로 금지한다.
# 이미 충분히 격식 있고 흔해서, 우리가 원하는 진짜 캐주얼한 톤과는 거리가 있다.
BANNED_EXPRESSIONS = [
    "touch base", "circle back", "keep in the loop", "on my plate",
    "loop someone in", "get the ball rolling",
]

# 원하는 톤을 구체적으로 보여주기 위한 예시 표현 풀. 모델에게 "이런 느낌"을 직접 보여준다.
EXAMPLE_CASUAL_EXPRESSIONS = [
    "yikes", "I'm beat", "wing it", "pull an all-nighter", "let's table this",
    "I'm swamped", "that's a bummer", "no biggie", "my bad", "I'll bounce",
    "let's call it a day", "I'm dead (피곤하다는 뜻)", "ngl (not gonna lie)",
    "low-key", "I'm down (좋다는 뜻)", "that tracks", "I'm not gonna lie",
    "that's rough", "I got you", "hang tight",
]


class DialogueTurn(BaseModel):
    speaker: str = Field(description="화자 라벨, 예: A, B, C")
    line: str = Field(description="해당 화자의 대화 한 줄 (영어)")


class Expression(BaseModel):
    phrase: str = Field(description="구어체 표현/숙어/은어 (영어)")
    meaning: str = Field(description="한국어로 된 뜻 설명")


class EnglishSituationLLM(BaseModel):
    title: str = Field(description="상황을 설명하는 한국어 제목")
    dialogue: list[DialogueTurn] = Field(description="2~3인 대화, 4~6턴 정도")
    expressions: list[Expression] = Field(description="대화에 쓰인 구어체 표현 3~5개")


def _build_english_prompt() -> str:
    scenario = random.choice(ENGLISH_SCENARIOS)
    example_picks = random.sample(EXAMPLE_CASUAL_EXPRESSIONS, 5)

    return f"""\
외국계 기업에서 일하는 20~30대 동료들이 사무실에서 나눌 법한, 진짜 캐주얼한 영어 대화를 만들어줘.

상황: {scenario}

조건:
- 화자는 2~3명(A, B, C), 대화는 4~6턴 정도
- 친한 동료끼리 편하게 말하는 톤. 격식 있는 비즈니스 영어가 아니라 진짜 일상 구어체로
- 이런 느낌의 캐주얼한 표현을 최소 3개 이상 자연스럽게 포함시켜줘 (참고 예시: {", ".join(example_picks)} 등.
  이 단어를 그대로 써도 되고, 비슷한 톤의 다른 표현을 써도 됨)
- 다음 표현들은 이미 너무 많이 나왔으니 절대 쓰지 말 것: {", ".join(BANNED_EXPRESSIONS)}
- 사용된 캐주얼 표현은 따로 정리해서 한국어 뜻을 붙여줘
- "보고서", "마감일 확인" 같은 전형적인 업무 체크인 대화는 피하고, 위에 정해준 상황에 맞게 만들어줘
"""


async def generate_english_situation() -> EnglishSituationLLM:
    """Gemini로 영어 섀도잉 시나리오를 새로 생성한다. 실패 시 예외 발생.

    매 호출마다 상황과 예시 표현을 랜덤으로 새로 골라 프롬프트에 박아넣어서,
    매번 비슷한 시나리오/표현으로 수렴하는 걸 방지한다.
    """
    client = _get_client()
    prompt = _build_english_prompt()
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": EnglishSituationLLM,
            },
        )
        result = EnglishSituationLLM.model_validate_json(response.text)
        logger.info(f"LLM generated English situation: {result.title}")
        return result
    except Exception as e:
        logger.error(f"Gemini English generation failed: {e}")
        raise


# ---------------------------------------------------------------------------
# 일본어 초급 문장 생성
# ---------------------------------------------------------------------------

class JapaneseSentenceLLM(BaseModel):
    sentence: str = Field(description="일본어 문장 (한자+히라가나 원문)")
    furigana: str = Field(description="문장 전체를 히라가나로 표기한 후리가나")
    romaji: str = Field(description="로마자 표기")
    translation: str = Field(description="한국어 번역")


JAPANESE_TOPICS = [
    "편의점에서 계산할 때", "카페에서 음료 주문하기", "길을 잃어서 누군가에게 묻기",
    "버스/지하철을 놓쳤을 때", "식당에서 메뉴 추천 받기", "옷가게에서 사이즈 묻기",
    "친구와 약속 시간 정하기", "비가 와서 우산을 빌리려 할 때", "택시를 부를 때",
    "물건을 잃어버려서 찾을 때", "사진을 찍어달라고 부탁하기", "맛집을 추천해달라고 하기",
    "화장실 위치를 물을 때", "와이파이 비밀번호를 물을 때", "계산을 나눠서 하자고 할 때",
]

# 모델이 "초급"이라는 말만 들으면 디폴트로 꺼내는 한 단어짜리 인사말. 이건 이제 너무 쉬워서 금지.
BANNED_JAPANESE_PHRASES = [
    "こんにちは", "お元気ですか", "ありがとう", "すみません(단독으로만 쓰는 경우)",
    "おはよう", "さようなら", "今日は天気がいいですね",
]


def _build_japanese_prompt() -> str:
    topic = random.choice(JAPANESE_TOPICS)
    return f"""\
일본어 초급(JLPT N5~N4 경계 수준) 학습자를 위한 실용적인 일상 회화 문장을 1개 만들어줘.

상황: {topic}

조건:
- 단순 인사말 한 마디가 아니라, 주어+동작이 있는 문장으로 만들어줘
  (예: "이 가방 좀 더 작은 사이즈 있어요?", "여기서 역까지 얼마나 걸려요?" 같은 구체적인 문장)
- 다음처럼 너무 쉬운 기본 인사말은 절대 쓰지 말 것: {", ".join(BANNED_JAPANESE_PHRASES)}
- 실제 그 상황에서 바로 써먹을 수 있는 실용적인 문장으로
- 너무 길지는 않게, 한 문장으로
- 후리가나(전체 히라가나 표기), 로마자, 한국어 번역을 모두 포함
"""


async def generate_japanese_sentence() -> JapaneseSentenceLLM:
    """Gemini로 일본어 초급 문장을 새로 생성한다. 실패 시 예외 발생.

    매 호출마다 주제를 랜덤으로 골라 다양성을 확보한다.
    """
    client = _get_client()
    prompt = _build_japanese_prompt()
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": JapaneseSentenceLLM,
            },
        )
        result = JapaneseSentenceLLM.model_validate_json(response.text)
        logger.info(f"LLM generated Japanese sentence: {result.sentence}")
        return result
    except Exception as e:
        logger.error(f"Gemini Japanese generation failed: {e}")
        raise  