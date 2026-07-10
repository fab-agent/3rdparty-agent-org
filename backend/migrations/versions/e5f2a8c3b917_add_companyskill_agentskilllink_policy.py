"""add CompanySkill, AgentSkillLink, Policy

Revision ID: e5f2a8c3b917
Revises: a3f9c12e8b45
Create Date: 2026-07-09
"""
import sqlmodel
from alembic import op
import sqlalchemy as sa

revision = 'e5f2a8c3b917'
down_revision = 'a3f9c12e8b45'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'companyskill',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('company_id', sa.String(), sa.ForeignKey('company.id'), nullable=False, index=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('skill_type', sa.String(), nullable=False, server_default='builtin'),
        sa.Column('config_json', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )

    op.create_table(
        'agentskilllink',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('agent_config_id', sa.String(), sa.ForeignKey('agentconfig.id'), nullable=False, index=True),
        sa.Column('company_skill_id', sa.String(), sa.ForeignKey('companyskill.id'), nullable=False, index=True),
    )

    op.create_table(
        'policy',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('company_id', sa.String(), sa.ForeignKey('company.id'), nullable=False, index=True),
        sa.Column('department_id', sa.String(), sa.ForeignKey('department.id'), nullable=True),
        sa.Column('agent_config_id', sa.String(), sa.ForeignKey('agentconfig.id'), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('slug', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False, server_default=''),
        sa.Column('scope', sa.String(), nullable=False, server_default='company'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )


def downgrade():
    op.drop_table('policy')
    op.drop_table('agentskilllink')
    op.drop_table('companyskill')
