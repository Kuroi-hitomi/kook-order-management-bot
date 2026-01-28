# backend/alembic/env.py
from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import urlparse

# ------- Alembic 基础配置 -------
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ------- 让 Alembic 能 import 到你的项目包 -------
# 这里将 backend 目录加到 sys.path，确保 "from app.models import Base" 可用
BASE_DIR = Path(__file__).resolve().parents[1]  # .../backend
if str(BASE_DIR) not in sys.path:
    sys.path.append(str(BASE_DIR))

load_dotenv(BASE_DIR / ".env")

# ------- 导入你的 ORM Base（务必确保 app/__init__.py 存在）-------
# 确保 app/models.py 中定义了： Base = declarative_base() 以及所有模型类
from app.models import Base  # ← 根据你的实际路径调整
target_metadata = Base.metadata

# ------- 数据库 URL 来源：优先 .env 的 DATABASE_URL -------
# 例如：postgresql+psycopg2://postgres:postgres@localhost:5432/payment_db
db_url = os.getenv("DATABASE_URL")
if db_url:
    # 覆盖 alembic.ini 里的 sqlalchemy.url
    config.set_main_option("sqlalchemy.url", db_url)

try:
    _url = config.get_main_option("sqlalchemy.url")
    if _url:
        p = urlparse(_url)
        host = p.hostname or ""
        if p.port:
            host += f":{p.port}"
        print(f"[Alembic] sqlalchemy.url = {p.scheme}://{p.username or ''}:***@{host}{p.path}")
    else:
        print("[Alembic] sqlalchemy.url is EMPTY")
except Exception as e:
    print(f"[Alembic] url log error: {e}")

# ------- 迁移运行逻辑 -------
def run_migrations_offline():
    """Offline 模式：不真正建立 DB 连接，直接生成 SQL / 迁移脚本"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        compare_type=True,              # 字段类型变化也能被检测
        compare_server_default=True,    # 默认值变化也能被检测
        literal_binds=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Online 模式：建立 DB 连接，真实读取数据库 schema"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
