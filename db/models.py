from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, BigInteger
from sqlalchemy.sql import func

from db.database import Base


class GuildSettings(Base):
    """서버(길드)별 토글 설정. 혼자 쓰는 서버 하나만 있어도 구조는 다중 서버 대응."""

    __tablename__ = "guild_settings"

    id = Column(Integer, primary_key=True)
    guild_id = Column(BigInteger, unique=True, nullable=False, index=True)
    channel_id = Column(BigInteger, nullable=True)  # 발송할 채널, 미설정 시 첫 채널
    english_enabled = Column(Boolean, default=False, nullable=False)
    japanese_enabled = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class EnglishSituation(Base):
    """영어 섀도잉용 대화 시나리오. dialogue/expressions는 JSON으로 저장."""

    __tablename__ = "english_situations"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    # dialogue 예: [{"speaker": "A", "line": "Hey, you good?"}, ...]
    dialogue = Column(JSON, nullable=False)
    # expressions 예: [{"phrase": "swamped", "meaning": "일이 너무 많아 바쁜"}, ...]
    expressions = Column(JSON, nullable=True)
    difficulty = Column(String(20), default="intermediate")  # 추후 난이도별 필터링 대비
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class JapaneseSentence(Base):
    """일본어 초급 회화 문장. 후리가나/로마자/번역 포함."""

    __tablename__ = "japanese_sentences"

    id = Column(Integer, primary_key=True)
    sentence = Column(String(300), nullable=False)  # 한자+히라가나 원문
    furigana = Column(String(300), nullable=True)
    romaji = Column(String(300), nullable=True)
    translation = Column(String(300), nullable=False)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
