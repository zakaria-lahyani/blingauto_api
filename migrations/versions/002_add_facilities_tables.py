"""Add facilities tables (wash_bays, mobile_teams)

Revision ID: 002
Revises: 001
Create Date: 2025-10-01 14:00:00.000000

Implements:
- RG-FAC-001: Wash bay configuration tables
- RG-FAC-003: Mobile team configuration tables
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create wash_bays and mobile_teams tables."""

    # Create wash_bays table
    op.create_table(
        'wash_bays',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('bay_number', sa.String(length=50), nullable=False),
        sa.Column('max_vehicle_size', sa.String(length=20), nullable=False),
        sa.Column('equipment_types', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('location_latitude', sa.Numeric(precision=10, scale=8), nullable=True),
        sa.Column('location_longitude', sa.Numeric(precision=11, scale=8), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bay_number')
    )

    # Create indexes for wash_bays
    op.create_index('ix_wash_bays_bay_number', 'wash_bays', ['bay_number'])
    op.create_index('ix_wash_bays_status', 'wash_bays', ['status'])
    op.create_index('ix_wash_bays_status_deleted', 'wash_bays', ['status', 'deleted_at'])
    op.create_index('ix_wash_bays_bay_number_deleted', 'wash_bays', ['bay_number', 'deleted_at'])

    # Create mobile_teams table
    op.create_table(
        'mobile_teams',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('team_name', sa.String(length=100), nullable=False),
        sa.Column('base_latitude', sa.Numeric(precision=10, scale=8), nullable=False),
        sa.Column('base_longitude', sa.Numeric(precision=11, scale=8), nullable=False),
        sa.Column('service_radius_km', sa.Numeric(precision=6, scale=2), nullable=False, server_default='50.0'),
        sa.Column('daily_capacity', sa.Integer(), nullable=False, server_default='8'),
        sa.Column('equipment_types', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='active'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('team_name')
    )

    # Create indexes for mobile_teams
    op.create_index('ix_mobile_teams_team_name', 'mobile_teams', ['team_name'])
    op.create_index('ix_mobile_teams_status', 'mobile_teams', ['status'])
    op.create_index('ix_mobile_teams_status_deleted', 'mobile_teams', ['status', 'deleted_at'])
    op.create_index('ix_mobile_teams_team_name_deleted', 'mobile_teams', ['team_name', 'deleted_at'])
    op.create_index('ix_mobile_teams_location', 'mobile_teams', ['base_latitude', 'base_longitude'])


def downgrade() -> None:
    """Drop wash_bays and mobile_teams tables."""

    # Drop mobile_teams table and indexes
    op.drop_index('ix_mobile_teams_location', table_name='mobile_teams')
    op.drop_index('ix_mobile_teams_team_name_deleted', table_name='mobile_teams')
    op.drop_index('ix_mobile_teams_status_deleted', table_name='mobile_teams')
    op.drop_index('ix_mobile_teams_status', table_name='mobile_teams')
    op.drop_index('ix_mobile_teams_team_name', table_name='mobile_teams')
    op.drop_table('mobile_teams')

    # Drop wash_bays table and indexes
    op.drop_index('ix_wash_bays_bay_number_deleted', table_name='wash_bays')
    op.drop_index('ix_wash_bays_status_deleted', table_name='wash_bays')
    op.drop_index('ix_wash_bays_status', table_name='wash_bays')
    op.drop_index('ix_wash_bays_bay_number', table_name='wash_bays')
    op.drop_table('wash_bays')
