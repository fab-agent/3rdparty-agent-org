"""add company ai_onboarded

Revision ID: f1a2b3c4d5e6
Revises: e5f2a8c3b917
Create Date: 2026-07-09
"""

import sqlalchemy as sa
from alembic import op

revision = "f1a2b3c4d5e6"
down_revision = "e5f2a8c3b917"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("company") as batch_op:
        batch_op.add_column(
            sa.Column("ai_onboarded", sa.Boolean(), nullable=False, server_default="0")
        )


def downgrade():
    with op.batch_alter_table("company") as batch_op:
        batch_op.drop_column("ai_onboarded")
