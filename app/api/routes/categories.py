# app/api/routes/categories.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from app.models.category import Category  # Category ORM 가정: id(int), name(str) 필드 존재

router = APIRouter(prefix="/api/categories", tags=["categories"])

# 생성
@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_db)):
    # 중복 이름 체크(대소문자 구분 일단 유지)
    exists = db.query(Category).filter(Category.name == payload.name).first()
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 존재하는 카테고리 이름임",
        )
    obj = Category(name=payload.name)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

# 전체 목록
@router.get("", response_model=list[CategoryOut])
def list_categories(db: Session = Depends(get_db)):
    items = db.query(Category).order_by(Category.id.desc()).all()
    return items

# 단건 조회
@router.get("/{category_id}", response_model=CategoryOut)
def get_category(category_id: int, db: Session = Depends(get_db)):
    obj = db.query(Category).get(category_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="대상을 찾을 수 없음")
    return obj

# 부분 수정
@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_db)):
    obj = db.query(Category).get(category_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="대상을 찾을 수 없음")

    if payload.name is not None:
        # 이름 변경 시 중복 검증
        dup = (
            db.query(Category)
            .filter(Category.name == payload.name, Category.id != category_id)
            .first()
        )
        if dup:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 존재하는 카테고리 이름임",
            )
        obj.name = payload.name

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

# 삭제
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    obj = db.query(Category).get(category_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="대상을 찾을 수 없음")
    db.delete(obj)
    db.commit()
    return None
