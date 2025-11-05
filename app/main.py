# app/main.py

from fastapi import FastAPI, Request                      # 요청 객체 사용함
from fastapi.responses import HTMLResponse                # HTML 응답 사용함
from fastapi.staticfiles import StaticFiles               # 정적 파일 서빙용
from fastapi.templating import Jinja2Templates            # Jinja2 템플릿 엔진
import pathlib                                            # 경로 계산용

# 앱 생성
app = FastAPI()

# --- ADD: 경로 기준 설정 (app 디렉터리 기준으로 고정) ---
BASE_DIR = pathlib.Path(__file__).resolve().parent

# --- ADD: 정적 리소스 마운트 (/static/...) ---
# 예: /static/css/app.css, /static/js/app.js, /static/img/logo.png
app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

# --- ADD: 템플릿 엔진 등록 (app/templates) ---
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# --- ADD: 동작 확인용 라우트 ---
# 추후 실제 라우터로 대체 가능함. 템플릿 파일 존재 시 렌더됨.
@app.get("/", response_class=HTMLResponse)
def root(request: Request):
    # 템플릿에서 request 필요함 (Jinja2Templates 규칙)
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "FastWMS 홈"}      # 템플릿 변수 예시
    )
