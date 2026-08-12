"""add_fts_gin_index

Revision ID: f39303ccb112
Revises: 0535c4545545
Create Date: 2026-08-12 18:19:12.792550

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f39303ccb112'
down_revision: Union[str, Sequence[str], None] = '0535c4545545'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "CREATE INDEX IF NOT EXISTS document_chunks_fts_idx ON document_chunks USING gin (to_tsvector('english', chunk_content))"
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("DROP INDEX IF EXISTS document_chunks_fts_idx")
