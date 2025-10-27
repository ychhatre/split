"""Initial migration

Revision ID: 34af9e3f9315
Revises: 
Create Date: 2025-10-26 19:46:04.965629

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision: str = '34af9e3f9315'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables for the initial schema."""
    # Create sessions table
    op.create_table(
        'sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('host_name', sa.String(), nullable=True),
        sa.Column('host_payment_handle', sa.String(), nullable=True),
        sa.Column('receipt_image_url', sa.String(), nullable=True),
        sa.Column('receipt_items', sa.JSON(), nullable=True),
        sa.Column('tax_amount', sa.Float(), nullable=True),
        sa.Column('tip_amount', sa.Float(), nullable=True),
        sa.Column('subtotal', sa.Float(), nullable=True),
        sa.Column('total', sa.Float(), nullable=True),
        sa.Column('qr_code_url', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_id'), 'sessions', ['id'], unique=False)

    # Create session_users table
    op.create_table(
        'session_users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('selected_items', sa.JSON(), nullable=True),
        sa.Column('subtotal', sa.Float(), nullable=True),
        sa.Column('tax', sa.Float(), nullable=True),
        sa.Column('tip', sa.Float(), nullable=True),
        sa.Column('total', sa.Float(), nullable=True),
        sa.Column('paid', sa.Boolean(), nullable=True),
        sa.Column('payment_method', sa.String(), nullable=True),
        sa.Column('payment_handle', sa.String(), nullable=True),
        sa.Column('host_payment_handle', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['session_id'], ['sessions.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_session_users_id'), 'session_users', ['id'], unique=False)
    op.create_index(op.f('ix_session_users_session_id'), 'session_users', ['session_id'], unique=False)


def downgrade() -> None:
    """Drop all tables."""
    op.drop_index(op.f('ix_session_users_session_id'), table_name='session_users')
    op.drop_index(op.f('ix_session_users_id'), table_name='session_users')
    op.drop_table('session_users')
    op.drop_index(op.f('ix_sessions_id'), table_name='sessions')
    op.drop_table('sessions')
