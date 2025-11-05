# app/schemas/stock.py
from typing import Optional
from pydantic import BaseModel, Field


# 공통 속성
class StockBase(BaseModel):
    # 물품명은 필수, 길이 제한 둠
    name: str = Field(..., min_length=1, max_length=200, description="물품명")
    # 수량은 0 이상 정수
    inventory: int = Field(..., ge=0, description="수량")
    # 카테고리 ID는 필수
    category_id: int = Field(..., ge=1, description="카테고리 ID")


# 생성 요청용
class StockCreate(StockBase):
    # 추가 필드는 없음
    pass


# 수정 요청용(부분 수정 허용)
class StockUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="물품명")
    inventory: Optional[int] = Field(None, ge=0, description="수량")
    category_id: Optional[int] = Field(None, ge=1, description="카테고리 ID")


# 조회 응답용
class StockRead(BaseModel):
    id: int
    name: str
    inventory: int
    category_id: int
    # Spring의 StocksDTO(categoryName)와 유사하게 내려줄 필드
    category_name: Optional[str] = None

    # ORM 객체 직렬화 지원
    model_config = {
        "from_attributes": True  # Pydantic v2: orm_mode 대체
    }
