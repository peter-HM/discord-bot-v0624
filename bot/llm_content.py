"""
Gemini API를 이용한 콘텐츠 자동 생성.

content.py의 정적 풀 조회 함수와 동일한 반환 타입(딕셔너리)을 맞춰서,
호출하는 쪽(scheduler, cogs)이 정적 풀이든 LLM 생성이든 신경 쓸 필요 없게 한다.

실패(API 에러, 타임아웃, 키 누락 등) 시에는 예외를 던지고,
호출부에서 정적 풀로 폴백하도록 설계한다.
"""

import os
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


ENGLISH_PROMPT = """\
외국계 기업/글로벌 기업에서 일하는 직장인들이 실제로 나눌 법한 영어 대화를 만들어줘.

조건:
- 업무 상황(회의, 협업, 마감, 잡담 등) 중 하나를 배경으로 설정
- 화자는 2~3명(A, B, C), 대화는 4~6턴 정도의 자연스러운 구어체
- 교과서적인 표현이 아니라, 실제 동료들이 캐주얼하게 쓰는 숙어/구동사/업무 은어를
  최소 3개 이상 자연스럽게 포함시켜줘
- 사용된 구어체 표현은 따로 정리해서 한국어 뜻을 붙여줘
- 너무 어렵거나 전문적인 용어는 피하고, 실무에서 자주 들을 수 있는 수준으로
"""


async def generate_english_situation() -> EnglishSituationLLM:
    """Gemini로 영어 섀도잉 시나리오를 새로 생성한다. 실패 시 예외 발생."""
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=ENGLISH_PROMPT,
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


JAPANESE_PROMPT = """\
일본어를 완전 초급 수준으로 배우는 학습자를 위한 일상 회화 문장을 1개 만들어줘.

조건:
- JLPT N5 수준의 쉬운 일상 회화 문장 (인사, 날씨, 쇼핑, 간단한 업무 표현 등)
- 너무 길지 않게, 한 문장으로
- 후리가나(전체 히라가나 표기), 로마자, 한국어 번역을 모두 포함
"""


async def generate_japanese_sentence() -> JapaneseSentenceLLM:
    """Gemini로 일본어 초급 문장을 새로 생성한다. 실패 시 예외 발생."""
    client = _get_client()
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=JAPANESE_PROMPT,
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
