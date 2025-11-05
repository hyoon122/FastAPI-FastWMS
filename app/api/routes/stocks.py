# app/api/routes/stocks.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.stock import Stocks  # ORM 가정: Stocks 모델 (id, name, inventory, category_id)
from app.models.category import Category  # ORM 가정: Category 모델 (id, name)
from app.schemas.stock import StockCreate, StockUpdate, StockRead

router = APIRouter(prefix="/api/stocks", tags=["stocks"])

# 생성
@router.post("", response_model=StockRead, status_code=status.HTTP_201_CREATED)
def create_stock(payload: StockCreate, db: Session = Depends(get_db)):
    # 카테고리 존재 확인
    cat = db.query(Category).get(payload.category_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="카테고리를 찾을 수 없음")

    obj = Stocks(name=payload.name, inventory=payload.inventory, category_id=payload.category_id)
    db.add(obj)
    db.commit()
    db.refresh(obj)

    # 응답용에 category_name 포함
    return {
        "id": obj.id,
        "name": obj.name,
        "inventory": obj.inventory,
        "category_id": obj.category_id,
        "category_name": cat.name,
    }

# 목록 조회 (간단 페이징 + 옵션: category_id, query)
@router.get("", response_model=list[StockRead])
def list_stocks(
    category_id: Optional[int] = Query(None, ge=1),
    query: Optional[str] = Query(None, min_length=1),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    q = db.query(Stocks)

    if category_id is not None:
        q = q.filter(Stocks.category_id == category_id)

    if query:
        like = f"%{query}%"
        q = q.filter(Stocks.name.ilike(like))

    q = q.order_by(Stocks.id.desc())

    offset = (page - 1) * size
    rows = q.offset(offset).limit(size).all()

    # category_name 채우기 (관계 미정이라 안전하게 별도 조회)
    result = []
    for r in rows:
        cat = db.query(Category).get(r.category_id)
        result.append(
            {
                "id": r.id,
                "name": r.name,
                "inventory": r.inventory,
                "category_id": r.category_id,
                "category_name": cat.name if cat else None,
            }
        )
    return result

# 단건 조회
@router.get("/{stock_id}", response_model=StockRead)
def get_stock(stock_id: int, db: Session = Depends(get_db)):
    obj = db.query(Stocks).get(stock_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="대상을 찾을 수 없음")
    cat = db.query(Category).get(obj.category_id)
    return {
        "id": obj.id,
        "name": obj.name,
        "inventory": obj.inventory,
        "category_id": obj.category_id,
        "category_name": cat.name if cat else None,
    }

# 부분 수정
@router.patch("/{stock_id}", response_model=StockRead)
def update_stock(stock_id: int, payload: StockUpdate, db: Session = Depends(get_db)):
    obj = db.query(Stocks).get(stock_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="대상을 찾을 수 없음")

    if payload.name is not None:
        obj.name = payload.name
    if payload.inventory is not None:
        obj.inventory = payload.inventory
    if payload.category_id is not None:
        # 지정된 카테고리 존재 확인
        cat = db.query(Category).get(payload.category_id)
        if not cat:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="지정한 카테고리를 찾을 수 없음")
        obj.category_id = payload.category_id

    db.add(obj)
    db.commit()
    db.refresh(obj)

    cat = db.query(Category).get(obj.category_id)
    return {
        "id": obj.id,
        "name": obj.name,
        "inventory": obj.inventory,
        "category_id": obj.category_id,
        "category_name": cat.name if cat else None,
    }

# 삭제
@router.delete("/{stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock(stock_id: int, db: Session = Depends(get_db)):
    obj = db.query(Stocks).get(stock_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="대상을 찾을 수 없음")
    db.delete(obj)
    db.commit()
    return None
