from app.db import get_session
from sqlalchemy import text
try:
    with get_session() as s:
        v = s.execute(text("select 1")).scalar_one()
        assert v == 1
    print("DB OK")
except Exception as e:
    print("DB FAIL:", e)
    raise SystemExit(1)