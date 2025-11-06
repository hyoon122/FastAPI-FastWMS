# app/api/routes/stocks.py
# 라우터: 상품 목록 화면 렌더링
# DB 연결 시 실제 목록 조회
# DB 미연결 시에도 템플릿 최소 렌더 보장
from datetime import datetime
from typing import Optional, List, Dict
from fastapi import APIRouter, Request, Query, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy import select, func
from sqlalchemy.orm import Session                 # ← (변경) 동기 세션 사용
from app.db.session import get_session             # ← 단일 진실 원천으로 고정
from app.models.stock import Stock
from app.models.category import Category
from pathlib import Path
from fastapi.templating import Jinja2Templates

# app/templates 를 안전하게 가리키도록 절대경로 계산
TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
templates.env.globals["now"] = datetime.utcnow   # 호출 가능한 함수로 등록

router = APIRouter(tags=["Stocks"])                # ← (변경) 내부 prefix 제거

@router.get("", response_class=HTMLResponse)
def list_stocks(                                   # ← (변경) async → def
    request: Request,
    page: int = Query(1, ge=1, description="현재 페이지(1부터 시작)"),
    categoryId: Optional[int] = Query(None, description="카테고리 필터"),
    keyword: Optional[str] = Query(None, description="상품명 검색어"),
    db: Session = Depends(get_session),            # ← (변경) AsyncSession → Session
):
    page_size = 20

    context: Dict = {
        "request": request,
        "stocks": [],
        "categories": [],
        "categoryId": categoryId,
        "keyword": keyword or "",
        "pageInfo": None,
    }

    # 1) 카테고리 조회
    categories = db.execute(                       # ← (변경) await 제거
        select(Category).order_by(Category.id.desc())
    ).scalars().all()
    context["categories"] = [{"id": c.id, "name": getattr(c, "name", "-")} for c in categories]

    # 2) where 절 구성
    filters = []
    if categoryId:
        filters.append(Stock.category_id == categoryId)
    if keyword:
        filters.append(Stock.name.ilike(f"%{keyword}%"))

    # 3) 총 개수
    if filters:
        total = db.execute(                        # ← (변경) await 제거
            select(func.count(Stock.id)).where(*filters)
        ).scalar_one()
    else:
        total = db.execute(select(func.count(Stock.id))).scalar_one()

    # 4) 페이지 계산
    total_pages = max((total + page_size - 1) // page_size, 1)
    page = min(max(page, 1), total_pages)
    offset = (page - 1) * page_size

    # 5) 데이터 조회
    stmt = select(Stock).order_by(Stock.id.desc())
    if filters:
        stmt = stmt.where(*filters)
    rows: List[Stock] = db.execute(                # ← (변경) await 제거
        stmt.offset(offset).limit(page_size)
    ).scalars().all()

    # 6) 템플릿용 정규화
    normalized = []
    for s in rows:
        category_name = getattr(getattr(s, "category", None), "name", None)
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

    # ← (변경) 실제 있는 템플릿 경로로 맞출 것
    return templates.TemplateResponse("stocks/index.html", context)
