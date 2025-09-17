"""initial

Revision ID: 20250907_0001
Revises: 
Create Date: 2025-09-07 00:00:00

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250907_0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'schools',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=120), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id')),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'questions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=True),
        sa.Column('action', sa.String(length=120), nullable=False),
        sa.Column('target_type', sa.String(length=120), nullable=True),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('ip', sa.String(length=64), nullable=True),
    )
    op.create_index('ix_audit_timestamp', 'audit_logs', ['timestamp'])

def downgrade():
    op.drop_index('ix_audit_timestamp', table_name='audit_logs')
    op.drop_table('audit_logs')
    op.drop_table('questions')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    op.drop_table('schools')
