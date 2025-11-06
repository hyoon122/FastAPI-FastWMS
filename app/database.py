# app/database.py
# 목적: 동기 SQLAlchemy 세션 팩토리 + FastAPI 의존성 제공

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Alembic/alembic.ini 의 sqlalchemy.url 과 맞추는 게 중요함
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./fastwms.db")

# SQLite일 때만 check_same_thread 옵션 필요
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
