# app/api/routes/stocks.py
# 라우터: 상품 목록 화면 + 목록 API
# - 검색(keyword), 카테고리 필터(categoryId)
# - 페이지네이션(page, size) + id desc 정렬
# - API는 X-Total-Count 헤더로 총건수 제공
# - 템플릿은 구(old) 변수(stocks, pageInfo)와 신(new) 변수(pageData) 둘 다 지원
# - base.html의 {{ now().year }} 지원
# - DB 미연결 시에도 템플릿 폴백 렌더 보장


from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Request, Depends, Query, Response
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi.templating import Jinja2Templates
from datetime import datetime

from app.db.session import get_session
from app.models.stock import Stock
from app.models.category import Category
from app.schemas.stock import StockCreate, StockUpdate  # JSON 스키마

from math import ceil

router = APIRouter(tags=["stocks"])
templates = Jinja2Templates(directory="app/templates")

# ----------------------------------------------------------
# 내부 유틸: 필터 쿼리 구성
# ----------------------------------------------------------
def _build_stock_query(
    db: Session,
    category_id: Optional[int],
    keyword: Optional[str],
):
    q = db.query(Stock).outerjoin(Category, Stock.category_id == Category.id)

    if category_id is not None:
        q = q.filter(Stock.category_id == category_id)

    if keyword:
        kw = keyword.strip()
        if kw:
            q = q.filter(Stock.name.ilike(f"%{kw}%"))

    return q


# ----------------------------------------------------------
# 1) 목록 화면 렌더 (/stocks)
# ----------------------------------------------------------
@router.get("/stocks", response_class=HTMLResponse)
def render_stocks_page(
    request: Request,
    categoryId: Optional[int] = Query(None, description="카테고리 ID 필터"),
    keyword: Optional[str] = Query(None, description="이름 검색 키워드"),
    page: int = Query(0, ge=0, description="0부터 시작하는 페이지"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기(1~100)"),
    db: Session = Depends(get_session),
):
    try:
        # 기본 쿼리
        base_q = _build_stock_query(db, categoryId, keyword)
        total: int = base_q.with_entities(func.count(Stock.id)).scalar() or 0

        # 페이지 데이터
        result_items: List[Stock] = (
            base_q.order_by(Stock.id.desc())
            .offset(page * size)
            .limit(size)
            .all()
        )

        # 카테고리 목록 (검색폼용)
        cats = db.query(Category).order_by(Category.name.asc()).all()

        # 신규 포맷(pageData)
        page_data: Dict[str, Any] = {
            "items": result_items,
            "total": total,
            "page": page,
            "size": size,
            "categoryId": categoryId,
            "keyword": (keyword or "").strip(),
        }

        # 구 포맷(pageInfo)
        total_pages = (total + size - 1) // size if size else 1
        page_info = {
            "page": page,
            "size": size,
            "total": total,
            "totalPages": total_pages,
            "hasPrev": page > 0,
            "hasNext": (page + 1) < total_pages,
        }

        # 템플릿 렌더
        return templates.TemplateResponse(
            "stocks/index.html",
            {
                "request": request,
                "now": datetime.now,          # ← base.html에서 사용
                "pageData": page_data,
                "stocks": result_items,
                "pageInfo": page_info,
                "items": result_items,        # ← 템플릿 호환
                "categories": cats,
                "categoryId": categoryId,
                "keyword": (keyword or "").strip(),
            },
        )

    except Exception:
        # 폴백: DB 문제 시에도 렌더 보장
        empty_items: List[Stock] = []
        empty_page_data: Dict[str, Any] = {
            "items": empty_items,
            "total": 0,
            "page": page,
            "size": size,
            "categoryId": categoryId,
            "keyword": (keyword or "").strip(),
            "error": "DB 연결 불가 또는 조회 오류 발생",
        }
        empty_page_info = {
            "page": page,
            "size": size,
            "total": 0,
            "totalPages": 1,
            "hasPrev": False,
            "hasNext": False,
        }
        return templates.TemplateResponse(
            "stocks/index.html",
            {
                "request": request,
                "now": datetime.now,         # ← 여기도 추가
                "pageData": empty_page_data,
                "stocks": empty_items,
                "pageInfo": empty_page_info,
                "items": empty_items,
                "categories": [],
                "categoryId": categoryId,
                "keyword": (keyword or "").strip(),
            },
        )


# ----------------------------------------------------------
# 2) 목록 API (/api/stocks)
#  - 프런트(JS)와 포맷 통일: { items, page, total_pages }
#  - 페이지는 1부터 시작 (JS와 동일)
# ----------------------------------------------------------
@router.get("/api/stocks")
def list_stocks_api(
    response: Response,
    categoryId: Optional[int] = Query(None),
    keyword: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_session),
):
    base_q = _build_stock_query(db, categoryId, keyword)
    total: int = base_q.with_entities(func.count(Stock.id)).scalar() or 0

    from math import ceil
    total_pages = ceil(total / size) if total > 0 else 1
    offset = (page - 1) * size

    rows: List[Stock] = (
        base_q.order_by(Stock.id.desc())
        .offset(offset)
        .limit(size)
        .all()
    )

    items = [
        {
            "id": r.id,
            "name": r.name,
            "inventory": getattr(r, "inventory", None),
            "category_id": getattr(r, "category_id", None),
            "category_name": getattr(r.category, "name", None) if hasattr(r, "category") else None,
        }
        for r in rows
    ]

    # 헤더는 유지 (총건수)
    response.headers["X-Total-Count"] = str(total)
    return {
        "page": page,
        "total_pages": total_pages,
        "items": items
    }


# -----------------------------------------------------------
# 검색 엔드포인트: /api/stocks/search
# 조건: categoryId(선택), keyword(선택), page(기본1), size(기본20)
# 반환: items(목록), page(현재페이지), total_pages(전체 페이지수)
# -----------------------------------------------------------

@router.get("/api/stocks/search")
def search_stocks(
    categoryId: int | None = Query(None),
    keyword: str | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1),
    db: Session = Depends(get_session)
):
    query = db.query(Stock)

    # 카테고리 필터
    if categoryId:
        query = query.filter(Stock.category_id == categoryId)

    # 이름 검색
    if keyword:
        keyword_like = f"%{keyword}%"
        query = query.filter(Stock.name.ilike(keyword_like))

    total = query.count()
    total_pages = ceil(total / size) if total > 0 else 1

    # 페이지네이션
    offset = (page - 1) * size
    results = (
        query.order_by(Stock.id.desc())
        .offset(offset)
        .limit(size)
        .all()
    )

    items = [
        {
            "id": s.id,
            "name": s.name,
            "inventory": s.inventory,
            "category_id": s.category_id,
            "category_name": getattr(s.category, "name", None) if hasattr(s, "category") else None
        }
        for s in results
    ]

    return {
        "page": page,
        "total_pages": total_pages,
        "items": items
    }

# ============================
# CRUD: 생성 / 단건조회 / 수정 / 삭제
# ============================
from fastapi import HTTPException, status
from app.schemas.stock import StockCreate, StockUpdate

@router.post("/api/stocks", status_code=status.HTTP_201_CREATED)
def create_stock(payload: StockCreate, db: Session = Depends(get_session)):
    # 카테고리 존재 검증
    cat = db.get(Category, payload.category_id)
    if not cat:
        raise HTTPException(status_code=400, detail="유효하지 않은 category_id")

    # JSON 바디: { "name": str, "inventory": int, "category_id": int }
    obj = Stock(name=payload.name, inventory=payload.inventory, category_id=payload.category_id)

    db.add(obj)
    db.commit()
    db.refresh(obj)
    return {"id": obj.id, "message": "등록 완료"}

@router.get("/api/stocks/{stock_id}")
def get_stock(
    stock_id: int,
    db: Session = Depends(get_session),
):
    obj = db.get(Stock, stock_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="대상이 존재하지 않음")
    return {
        "id": obj.id,
        "name": obj.name,
        "inventory": obj.inventory,
        "category_id": obj.category_id,
        "category_name": getattr(obj.category, "name", None) if hasattr(obj, "category") else None,
    }

@router.put("/api/stocks/{stock_id}")
def update_stock(stock_id: int, payload: StockUpdate, db: Session = Depends(get_session)):
    # JSON 바디 일부만 와도 됨: { "name"?, "inventory"?, "category_id"? }
    obj = db.get(Stock, stock_id)
    if not obj:
        raise HTTPException(status_code=404, detail="존재하지 않음")

    if payload.name is not None:
        obj.name = payload.name
    if payload.inventory is not None:
        obj.inventory = payload.inventory
    if payload.category_id is not None:
        obj.category_id = payload.category_id

    db.commit()
    db.refresh(obj)
    return {"id": obj.id, "message": "수정 완료"}

@router.delete("/api/stocks/{stock_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_stock(
    stock_id: int,
    db: Session = Depends(get_session),
):
    obj = db.get(Stock, stock_id)
    if not obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="대상이 존재하지 않음")
    db.delete(obj)
    db.commit()
    return
