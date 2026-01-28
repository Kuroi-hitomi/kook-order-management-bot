"""orders: add kook ids & names; drop old user_id cols

Revision ID: 1246c2126c2b
Revises: 17fd6480a497
Create Date: 2025-11-02 07:44:40.488847

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1246c2126c2b'
down_revision: Union[str, Sequence[str], None] = '17fd6480a497'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1) 新增 4 列（先允许为空，避免老代码写不进去）
    op.add_column("orders", sa.Column("boss_kook_id",   sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("boss_kook_name", sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("player_kook_id",   sa.Text(), nullable=True))
    op.add_column("orders", sa.Column("player_kook_name", sa.Text(), nullable=True))

    # 2) 可选：给 id 列建索引，便于查询/导出（不影响功能）
    op.create_index("ix_orders_boss_kook_id", "orders", ["boss_kook_id"], unique=False)
    op.create_index("ix_orders_player_kook_id", "orders", ["player_kook_id"], unique=False)

    # 3) 删除旧列（如有外键，需先 drop constraint）
    # op.drop_constraint("orders_boss_user_id_fkey", "orders", type_="foreignkey")
    # op.drop_constraint("orders_player_user_id_fkey", "orders", type_="foreignkey")
    with op.batch_alter_table("orders") as b:
        b.drop_column("boss_user_id")
        b.drop_column("player_user_id")



def downgrade() -> None:
    """Downgrade schema."""
# 回滚：加回旧列（类型按你之前的定义；一般是 BigInteger）
    with op.batch_alter_table("orders") as b:
        b.add_column(sa.Column("player_user_id", sa.BigInteger(), nullable=True))
        b.add_column(sa.Column("boss_user_id",   sa.BigInteger(), nullable=False))

    # 恢复索引
    op.drop_index("ix_orders_player_kook_id", table_name="orders")
    op.drop_index("ix_orders_boss_kook_id",   table_name="orders")

    # 删除新列
    with op.batch_alter_table("orders") as b:
        b.drop_column("player_kook_name")
        b.drop_column("player_kook_id")
        b.drop_column("boss_kook_name")
        b.drop_column("boss_kook_id")