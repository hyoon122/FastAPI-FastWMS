from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url
from alembic import context

# 앱의 메타데이터 로드용 (여기서 엔진/세션 생성 같은 실행 로직은 없음)
from app.db.base import Base  # ← 네 프로젝트 구조에 맞춰 유지

# Alembic 설정 객체
config = context.config

# 로깅 설정
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 자동 생성 시 사용할 메타데이터
target_metadata = Base.metadata  # 기존에 있던 값 유지

def _sync_url_from_any(url_str: str) -> str:
    """
    Alembic은 동기 엔진으로만 실행.
    async URL을 sync URL로 자동 변환해서 사용함.
    """
    if not url_str:
        return url_str
    url = make_url(url_str)
    # sqlite+aiosqlite -> sqlite
    if url.get_backend_name() == "sqlite" and url.get_dialect().driver == "aiosqlite":
        url = url.set(drivername="sqlite")
    # mysql+asyncmy -> mysql+pymysql
    if url.get_backend_name() == "mysql" and url.get_dialect().driver == "asyncmy":
        url = url.set(drivername="mysql+pymysql")
    return str(url)

def run_migrations_offline() -> None:
    """오프라인 모드: 데이터베이스 연결 없이 스크립트만 생성"""
    url = _sync_url_from_any(config.get_main_option("sqlalchemy.url"))
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        render_as_batch=True if url.startswith("sqlite") else False,  # SQLite ALTER 대응
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """온라인 모드: 실제 연결 후 마이그레이션 실행"""
    url = _sync_url_from_any(config.get_main_option("sqlalchemy.url"))

    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
        future=True,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            render_as_batch=True if url.startswith("sqlite") else False,
        )
        with context.begin_transaction():
            context.run_migrations()

# Alembic 엔트리포인트
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
