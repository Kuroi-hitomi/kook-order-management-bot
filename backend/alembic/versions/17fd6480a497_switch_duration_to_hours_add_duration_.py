"""switch duration to hours (add duration_hours, migrate, drop duration_min)

Revision ID: 17fd6480a497
Revises: d32453d37bd6
Create Date: 2025-11-01 20:32:12.693864

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '17fd6480a497'
down_revision: Union[str, Sequence[str], None] = 'd32453d37bd6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("orders", sa.Column("duration_hours", sa.Numeric(6,2), nullable=True))
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE orders SET duration_hours = ROUND(duration_min / 60.0, 2)"))
    op.alter_column("orders", "duration_hours", nullable=False)
    op.drop_column("orders", "duration_min")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column("orders", sa.Column("duration_min", sa.Integer(), nullable=True))
    conn = op.get_bind()
    conn.execute(sa.text("UPDATE orders SET duration_min = ROUND(duration_hours * 60)"))
    op.alter_column("orders", "duration_min", nullable=False)
    op.drop_column("orders", "duration_hours")