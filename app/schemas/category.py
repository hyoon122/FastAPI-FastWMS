# app/schemas/category.py
from pydantic import BaseModel, Field, ConfigDict

# 공통 속성 정의용 베이스 스키마
class CategoryBase(BaseModel):
    # 카테고리 이름. 공백 제거 및 길이 제약 검증함
    name: str = Field(..., min_length=1, max_length=50)

# 생성 요청 바디용 스키마
class CategoryCreate(CategoryBase):
    pass  # 추가 필드 없음

# 부분 수정 요청 바디용 스키마
class CategoryUpdate(BaseModel):
    # 부분 업데이트 허용함
    name: str | None = Field(None, min_length=1, max_length=50)

# 응답용 스키마 (ORM 객체 직렬화 허용)
class CategoryOut(CategoryBase):
    id: int = Field(..., ge=1) # PK 양수 제한함
    # SQLAlchemy 모델 -> 스키마 변환 허용함
    model_config = ConfigDict(from_attributes=True)
