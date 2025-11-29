"""levels

Revision ID: 0ced7a44630f
Revises: 55bc71744354
Create Date: 2025-11-29 19:02:12.997802

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0ced7a44630f'
down_revision: Union[str, Sequence[str], None] = '55bc71744354'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "characters",
        sa.Column("level", sa.Integer(), server_default="1", nullable=False)
    )
    op.add_column(
        "characters",
        sa.Column("xp", sa.Integer(), server_default="0", nullable=False)
    )

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('characters', 'xp')
    op.drop_column('characters', 'level')
