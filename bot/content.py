"""
콘텐츠 서비스: 영어/일본어 콘텐츠를 가져오는 단일 진입점.

전략: Gemini API로 즉시 생성을 먼저 시도하고, 실패(키 누락, API 에러,
타임아웃 등)하면 DB에 미리 넣어둔(seed) 정적 풀로 자동 폴백한다.
이렇게 하면 LLM이 잠깐 죽어도 발송 자체가 끊기지 않는다.

호출하는 쪽(scheduler, cogs)은 get_next_english_situation /
get_next_japanese_sentence 두 함수만 쓰면 되고, 내부적으로
LLM이냐 정적 풀이냐는 신경 쓸 필요가 없다.
"""

import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from db.models import EnglishSituation, JapaneseSentence
from bot import llm_content

logger = logging.getLogger("content")


async def get_next_english_situation(db: Session) -> EnglishSituation | None:
    """영어 시나리오를 가져온다. LLM 생성을 먼저 시도하고, 실패하면 정적 풀로 폴백."""
    try:
        generated = await llm_content.generate_english_situation()
        situation = EnglishSituation(
            title=generated.title,
            dialogue=[turn.model_dump() for turn in generated.dialogue],
            expressions=[exp.model_dump() for exp in generated.expressions],
            difficulty="llm-generated",
            sent_at=datetime.now(timezone.utc),
        )
        db.add(situation)
        db.commit()
        db.refresh(situation)
        return situation
    except Exception as e:
        logger.warning(f"LLM 생성 실패, 정적 풀로 폴백합니다: {e}")
        return _get_next_english_situation_static(db)


async def get_next_japanese_sentence(db: Session) -> JapaneseSentence | None:
    """일본어 문장을 가져온다. LLM 생성을 먼저 시도하고, 실패하면 정적 풀로 폴백."""
    try:
        generated = await llm_content.generate_japanese_sentence()
        sentence = JapaneseSentence(
            sentence=generated.sentence,
            furigana=generated.furigana,
            romaji=generated.romaji,
            translation=generated.translation,
            sent_at=datetime.now(timezone.utc),
        )
        db.add(sentence)
        db.commit()
        db.refresh(sentence)
        return sentence
    except Exception as e:
        logger.warning(f"LLM 생성 실패, 정적 풀로 폴백합니다: {e}")
        return _get_next_japanese_sentence_static(db)


# ---------------------------------------------------------------------------
# 정적 풀 폴백 (기존 MVP 로직, 그대로 유지)
# ---------------------------------------------------------------------------

def _get_next_english_situation_static(db: Session) -> EnglishSituation | None:
    """아직 발송하지 않은 시드 영어 시나리오 중 하나를 가져온다.

    전부 소진되면 가장 오래전에 보낸 것부터 재사용(순환)한다.
    LLM이 생성한 항목(difficulty='llm-generated')은 폴백 풀에서 제외한다.
    """
    situation = (
        db.query(EnglishSituation)
        .filter(EnglishSituation.sent_at.is_(None))
        .filter(EnglishSituation.difficulty != "llm-generated")
        .order_by(EnglishSituation.id)
        .first()
    )

    if situation is None:
        situation = (
            db.query(EnglishSituation)
            .filter(EnglishSituation.difficulty != "llm-generated")
            .order_by(EnglishSituation.sent_at.asc())
            .first()
        )

    if situation is not None:
        situation.sent_at = datetime.now(timezone.utc)
        db.commit()

    return situation


def _get_next_japanese_sentence_static(db: Session) -> JapaneseSentence | None:
    """아직 발송하지 않은 시드 일본어 문장 중 하나를 가져온다. 로직은 영어와 동일."""
    sentence = (
        db.query(JapaneseSentence)
        .filter(JapaneseSentence.sent_at.is_(None))
        .order_by(JapaneseSentence.id)
        .first()
    )

    if sentence is None:
        sentence = (
            db.query(JapaneseSentence)
            .order_by(JapaneseSentence.sent_at.asc())
            .first()
        )

    if sentence is not None:
        sentence.sent_at = datetime.now(timezone.utc)
        db.commit()

    return sentence

