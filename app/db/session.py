# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings

# 설정 로드
settings = get_settings()

# 엔진 생성
# - pool_pre_ping: 유휴 커넥션 죽었을 때 자동 재연결
# - pool_recycle: MySQL의 wait_timeout 대비(초 단위)
# - future=True: SQLAlchemy 2.x 스타일
engine = create_engine(
    settings.sqlalchemy_database_uri,
    echo=settings.db_echo,
    pool_size=settings.db_pool_size,
    pool_recycle=settings.db_pool_recycle,
    pool_pre_ping=True,
    future=True,
)

# 세션 팩토리
# - autocommit False: 트랜잭션 명시적 제어
# - autoflush False: flush 시점 제어
# - expire_on_commit False: 커밋 후 객체 속성 유지
SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    future=True,
)

# FastAPI에서 의존성 주입으로 사용할 세션 제공자
# - 사용 예: def endpoint(db: Session = Depends(get_db))
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
