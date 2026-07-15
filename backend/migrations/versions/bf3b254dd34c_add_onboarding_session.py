"""add_onboarding_session

Revision ID: bf3b254dd34c
Revises: f1a2b3c4d5e6
Create Date: 2026-07-10 05:16:02.611560

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "bf3b254dd34c"
down_revision: str | Sequence[str] | None = "f1a2b3c4d5e6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("onboardingsession", schema=None) as batch_op:
        pass  # table may not exist yet — create below

    op.create_table(
        "onboardingsession",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("company_id", sa.String(), nullable=False),
        sa.Column("phase", sa.String(), nullable=False),
        sa.Column("search_context", sa.Text(), nullable=True),
        sa.Column("messages_json", sa.Text(), nullable=True),
        sa.Column("structure_json", sa.Text(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["company.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("onboardingsession", schema=None) as batch_op:
        batch_op.create_index(
            "ix_onboardingsession_company_id", ["company_id"], unique=True
        )


def downgrade() -> None:
    with op.batch_alter_table("onboardingsession", schema=None) as batch_op:
        batch_op.drop_index("ix_onboardingsession_company_id")
    op.drop_table("onboardingsession")
