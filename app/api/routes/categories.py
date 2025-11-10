# app/api/routes/categories.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.orm import Session
from sqlalchemy import func

# 동기 세션 주입 (단일 진실 원천)
from app.db.session import get_session

from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryOut
from app.models.category import Category

router = APIRouter(prefix="/api/categories", tags=["categories"])


# 생성
@router.post("", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(payload: CategoryCreate, db: Session = Depends(get_session)):
    # 입력 정규화
    name = (payload.name or "").strip()
    if not name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="이름이 비어 있음")

    # 중복 체크 (대소문자 구분 유지)
    exists = db.query(Category).filter(Category.name == name).first()
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 존재하는 카테고리 이름임")

    try:
        obj = Category(name=name)
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


# 목록 (페이지네이션)
@router.get("", response_model=list[CategoryOut])
def list_categories(
    response: Response,
    page: int = Query(0, ge=0, description="0부터 시작"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기(1~100)"),
    db: Session = Depends(get_session),
):
    total = db.query(func.count(Category.id)).scalar() or 0
    items = (
        db.query(Category)
        .order_by(Category.id.desc())
        .offset(page * size)
        .limit(size)
        .all()
    )
    # 총건수 전달
    response.headers["X-Total-Count"] = str(total)
    return items


# 단건 조회
@router.get("/{category_id}", response_model=CategoryOut)
def get_category(category_id: int, db: Session = Depends(get_session)):
    obj = db.get(Category, category_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="대상을 찾을 수 없음")
    return obj


# 부분 수정
@router.patch("/{category_id}", response_model=CategoryOut)
def update_category(category_id: int, payload: CategoryUpdate, db: Session = Depends(get_session)):
    obj = db.get(Category, category_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="대상을 찾을 수 없음")

    try:
        if payload.name is not None:
            new_name = payload.name.strip()
            if not new_name:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="이름이 비어 있음")

            dup = (
                db.query(Category)
                .filter(Category.name == new_name, Category.id != category_id)
                .first()
            )
            if dup:
                raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="이미 존재하는 카테고리 이름임")

            obj.name = new_name

        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj
    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise


# 삭제
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_session)):
    obj = db.get(Category, category_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="대상을 찾을 수 없음")
    try:
        db.delete(obj)
        db.commit()
        return None
    except Exception:
        db.rollback()
        raise
