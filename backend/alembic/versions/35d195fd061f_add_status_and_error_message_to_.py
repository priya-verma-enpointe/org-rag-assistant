"""add_status_and_error_message_to_documents

Revision ID: 35d195fd061f
Revises: f39303ccb112
Create Date: 2026-08-19 19:00:42.099674

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '35d195fd061f'
down_revision: Union[str, Sequence[str], None] = 'f39303ccb112'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Ensure columns exist safely
    op.add_column('documents', sa.Column('status', sa.String(length=50), nullable=False, server_default='COMPLETED'))
    op.add_column('documents', sa.Column('error_message', sa.Text(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('documents', 'error_message')
    op.drop_column('documents', 'status')