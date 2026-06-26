"""
콘텐츠 서비스: 영어/일본어 콘텐츠를 가져오는 단일 진입점.

MVP에서는 DB에 미리 넣어둔(seed) 정적 풀에서 '아직 안 보낸' 항목을 골라온다.
추후 LLM API 자동 생성으로 전환할 때는 이 두 함수의 내부 구현만 바꾸면 되고,
호출하는 쪽(scheduler, cogs)은 변경할 필요가 없도록 인터페이스를 고정해둔다.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from db.models import EnglishSituation, JapaneseSentence


def get_next_english_situation(db: Session) -> EnglishSituation | None:
    """아직 발송하지 않은 영어 시나리오 중 하나를 가져온다.

    전부 소진되면 가장 오래전에 보낸 것부터 재사용(순환)한다.
    """
    situation = (
        db.query(EnglishSituation)
        .filter(EnglishSituation.sent_at.is_(None))
        .order_by(EnglishSituation.id)
        .first()
    )

    if situation is None:
        # 풀 소진 -> 가장 오래된 sent_at부터 재사용
        situation = (
            db.query(EnglishSituation)
            .order_by(EnglishSituation.sent_at.asc())
            .first()
        )

    if situation is not None:
        situation.sent_at = datetime.now(timezone.utc)
        db.commit()

    return situation


def get_next_japanese_sentence(db: Session) -> JapaneseSentence | None:
    """아직 발송하지 않은 일본어 문장 중 하나를 가져온다. 로직은 영어와 동일."""
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


# ---------------------------------------------------------------------------
# Phase 2 확장 지점:
#
# async def get_next_english_situation_llm(db: Session) -> dict:
#     """무료 LLM API(예: Gemini free tier)로 매주 시나리오를 자동 생성.
#     반환 형식은 dialogue/expressions 동일한 JSON 구조로 맞춰서
#     호출부(scheduler)는 그대로 두고 이 함수 내부만 교체한다."""
#     ...
# ---------------------------------------------------------------------------
