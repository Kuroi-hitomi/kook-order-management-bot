"""order_audits add payload json

Revision ID: ea4045f06a00
Revises: 1246c2126c2b
Create Date: 2025-11-02 08:57:30.018990

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea4045f06a00'
down_revision: Union[str, Sequence[str], None] = '1246c2126c2b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("order_audits", sa.Column("payload", sa.JSON(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("order_audits", "payload")
