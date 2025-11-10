# __db_drop_views__.py
# 목적: 임시 소문자 뷰(stocks, categories) 제거

from sqlalchemy import create_engine, text

URL = "mysql+pymysql://WASDHY:Toast%26love6974@wasd-webservice.c3mcam44i77o.ap-northeast-2.rds.amazonaws.com:3306/WASD?charset=utf8mb4"
engine = create_engine(URL, pool_pre_ping=True)

SQLS = [
    "DROP VIEW IF EXISTS stocks",
    "DROP VIEW IF EXISTS categories",
]

with engine.begin() as conn:
    for q in SQLS:
        conn.execute(text(q))
print("OK: dropped views [stocks, categories]")
