# app/core/db.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 로컬 개발용 SQLite 파일 경로 지정
DATABASE_URL = "sqlite:///./app.db"

# SQLite 동시성 제약 해제용 옵션 포함
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# 세션 팩토리 구성
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# FastAPI 의존성 주입용 제너레이터
# 요청마다 세션 열고 응답 후 닫음
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
