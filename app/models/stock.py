# app/models/stock.py
from __future__ import annotations
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Integer, ForeignKey
from app.db.base import Base

# 타입체커 전용 임포트
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .category import Category

# 재고 엔티티 정의함
class Stock(Base):
    __tablename__ = "Stocks"    # RDS 실제 테이블명과 일치시킴

    # 기본키
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 물품명
    # - 필수 값
    # - 검색 성능 위해 인덱스 부여
    # - 이름 중복 허용(이전에 단일 조회를 위해 findByName 사용했더라도, 실무상 동명이 가능하므로 unique 지정하지 않음)
    name: Mapped[str] = mapped_column(String(200), index=True, nullable=False)

    # 수량
    # - 0 이상 정수
    inventory: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # 카테고리 외래키
    # - 삭제 시 자식 행 처리: 상위에서 cascade 설정됨
    category_id: Mapped[int] = mapped_column(
        ForeignKey("Category.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # 연관 관계: 재고 → 카테고리(다대일의 다 측)
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="stocks",
        lazy="joined",
    )

    # 표현용
    def __repr__(self) -> str:
        return f"Stock(id={self.id!r}, name={self.name!r}, inventory={self.inventory!r}, category_id={self.category_id!r})"
