# 라우터: 상품 목록 화면 렌더링
# DB 연결 시 실제 목록 조회
# DB 미연결 시에도 템플릿 최소 렌더 보장
from typing import Optional, List, Dict

from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

# DB 세션 유틸의 실제 경로로 변경
#   화면 캡처 기준: app/db/session.py 존재
from app.db.session import get_session

# 모델 파일 구조에 맞춰 import
#   화면 캡처 기준: app/models/stock.py, app/models/category.py 존재
from app.models.stock import Stock
from app.models.category import Category

templates = Jinja2Templates(directory="app/templates")
router = APIRouter(prefix="/stocks", tags=["stocks"])


@router.get("", response_class=HTMLResponse)
async def list_stocks(
    request: Request,
    page: int = Query(1, ge=1, description="현재 페이지(1부터 시작)"),
    categoryId: Optional[int] = Query(None, description="카테고리 필터"),
    keyword: Optional[str] = Query(None, description="상품명 검색어"),
    db: AsyncSession = Depends(get_session),   # 조건식 제거: 정식 의존성 주입
):
    # 페이지 크기 고정
    page_size = 20

    # 기본 컨텍스트
    context: Dict = {
        "request": request,
        "stocks": [],
        "categories": [],
        "categoryId": categoryId,
        "keyword": keyword or "",
        "pageInfo": None,
    }

    # 1) 카테고리 조회
    categories = (await db.execute(select(Category).order_by(Category.id.desc()))).scalars().all()
    context["categories"] = [{"id": c.id, "name": getattr(c, "name", "-")} for c in categories]

    # 2) where 절 구성
    filters = []
    if categoryId:
        # 모델 필드명이 category_id 라고 가정
        filters.append(Stock.category_id == categoryId)
    if keyword:
        filters.append(Stock.name.ilike(f"%{keyword}%"))

    # 3) 총 개수
    total = (await db.execute(select(func.count(Stock.id)).where(*filters))).scalar_one() if filters \
        else (await db.execute(select(func.count(Stock.id)))).scalar_one()

    # 4) 페이지 계산
    total_pages = max((total + page_size - 1) // page_size, 1)
    page = min(max(page, 1), total_pages)
    offset = (page - 1) * page_size

    # 5) 데이터 조회
    stmt = select(Stock).order_by(Stock.id.desc())
    if filters:
        stmt = stmt.where(*filters)
    rows: List[Stock] = (await db.execute(stmt.offset(offset).limit(page_size))).scalars().all()

    # 6) 템플릿용 정규화
    normalized = []
    for s in rows:
        category_name = None
        if hasattr(s, "category") and getattr(s, "category") is not None:
            category_name = getattr(s.category, "name", None)
        normalized.append({
            "id": getattr(s, "id", None),
            "name": getattr(s, "name", None),
            "inventory": getattr(s, "inventory", None),
            "categoryName": category_name,
        })
    context["stocks"] = normalized

    # 7) 페이지 정보
    context["pageInfo"] = {
        "page": page,
        "totalPages": total_pages,
        "hasPrev": page > 1,
        "hasNext": page < total_pages,
    }

    return templates.TemplateResponse("stocks_list.html", context)
