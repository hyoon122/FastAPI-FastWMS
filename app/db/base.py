# app/db/base.py
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# 제약조건/인덱스 명명 규칙 고정함 (Alembic 마이그레이션 안정성 확보 목적)
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

metadata = MetaData(naming_convention=naming_convention)

class Base(DeclarativeBase):
    # 모든 모델이 공유할 메타데이터 지정함
    metadata = metadata


# ⚠️ 주의: 아래 임포트는 나중에 모델 파일 생성 후 활성화할 것
# Alembic autogenerate가 테이블을 감지하려면 Base를 참조하는 모델들이 임포트되어 있어야 함
from app.models import category, stock # Alembic 인식용