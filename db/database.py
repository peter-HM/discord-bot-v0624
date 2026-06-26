import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://bot_user:bot_password@db:5432/discord_bot_db",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI 스타일 의존성 주입 패턴. 봇 코드에서도 동일하게 사용."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """테이블이 없으면 생성. 컨테이너 최초 기동 시 호출."""
    from db import models  # noqa: F401  (모델 등록을 위해 import)

    Base.metadata.create_all(bind=engine)
