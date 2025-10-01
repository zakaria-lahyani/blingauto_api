"""Add resource allocation to bookings (wash_bay_id, mobile_team_id)

Revision ID: 003
Revises: 002
Create Date: 2025-10-01 16:00:00.000000

Implements:
- Wash bay capacity management
- Resource allocation for stationary bookings
- Mobile team allocation for mobile bookings
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add wash_bay_id and mobile_team_id columns to bookings table."""

    # Add wash_bay_id column
    op.add_column(
        'bookings',
        sa.Column('wash_bay_id', sa.String(), nullable=True)
    )

    # Add mobile_team_id column
    op.add_column(
        'bookings',
        sa.Column('mobile_team_id', sa.String(), nullable=True)
    )

    # Add foreign key constraints
    op.create_foreign_key(
        'fk_bookings_wash_bay_id',
        'bookings',
        'wash_bays',
        ['wash_bay_id'],
        ['id'],
        ondelete='SET NULL'
    )

    op.create_foreign_key(
        'fk_bookings_mobile_team_id',
        'bookings',
        'mobile_teams',
        ['mobile_team_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Create index for faster bay availability queries
    op.create_index(
        'ix_bookings_wash_bay_scheduled',
        'bookings',
        ['wash_bay_id', 'scheduled_at', 'status']
    )

    # Create index for mobile team booking queries
    op.create_index(
        'ix_bookings_mobile_team_scheduled',
        'bookings',
        ['mobile_team_id', 'scheduled_at', 'status']
    )


def downgrade() -> None:
    """Remove wash_bay_id and mobile_team_id columns from bookings table."""

    # Drop indexes
    op.drop_index('ix_bookings_mobile_team_scheduled', table_name='bookings')
    op.drop_index('ix_bookings_wash_bay_scheduled', table_name='bookings')

    # Drop foreign key constraints
    op.drop_constraint('fk_bookings_mobile_team_id', 'bookings', type_='foreignkey')
    op.drop_constraint('fk_bookings_wash_bay_id', 'bookings', type_='foreignkey')

    # Drop columns
    op.drop_column('bookings', 'mobile_team_id')
    op.drop_column('bookings', 'wash_bay_id')
