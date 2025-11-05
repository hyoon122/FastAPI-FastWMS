# app/models/category.py
from typing import List, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String
from app.db.base import Base

# 카테고리 엔티티 정의함
class Category(Base):
    __tablename__ = "categories"

    # 기본키
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # 카테고리명
    # - 이름은 필수
    # - 중복 방지를 위해 unique 지정
    # - 검색 최적화를 위해 index 지정
    name: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)

    # 연관 관계: 카테고리 → 재고(다대일의 1 측)
    # - Stock 모델에서 back_populates="category"로 대응 예정
    stocks: Mapped[List["Stock"]] = relationship(
        back_populates="category",
        cascade="all, delete-orphan",
        passive_deletes=True,
        lazy="selectin",
    )

    # 표현용
    def __repr__(self) -> str:
        return f"Category(id={self.id!r}, name={self.name!r})"
