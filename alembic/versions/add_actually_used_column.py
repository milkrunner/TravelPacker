"""Add actually_used column to packing_items

Revision ID: a1b2c3d4e5f6
Revises: 36a04cd7adbc
Create Date: 2026-03-10
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "36a04cd7adbc"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("packing_items", sa.Column("actually_used", sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column("packing_items", "actually_used")
