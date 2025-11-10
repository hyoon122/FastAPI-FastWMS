# app/db/session.py
# 목적: 동기 SQLAlchemy 세션 + FastAPI 의존성 제공 (단일 진실 원천)

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv  # ← 추가: .env 로드용

# .env 파일 로드
load_dotenv()

# .env에 정의된 연결 문자열 우선 사용
DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URL")

# 백업: 환경변수에 없다면 SQLite로 폴백
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///./app.db"

# 엔진 생성
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    pool_pre_ping=True,    # MariaDB 등 연결 유효성 체크용
)

# 세션팩토리
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

# FastAPI 의존성 주입용 세션 생성기
def get_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
