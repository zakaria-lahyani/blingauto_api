"""add staff management tables

Revision ID: 004
Revises: 003
Create Date: 2025-10-02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create staff management tables."""

    # Create staff_members table
    op.create_table(
        'staff_members',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('employee_code', sa.String(20), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hire_date', sa.Date(), nullable=False),
        sa.Column('employment_type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='active'),
        sa.Column('hourly_rate', sa.Numeric(10, 2), nullable=False),
        sa.Column('assigned_bay_id', sa.String(), nullable=True),
        sa.Column('assigned_team_id', sa.String(), nullable=True),
        sa.Column('skills', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('total_services_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_revenue_generated', sa.Numeric(12, 2), nullable=False, server_default='0'),
        sa.Column('average_rating', sa.Numeric(3, 2), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['assigned_bay_id'], ['wash_bays.id'], ),
        sa.ForeignKeyConstraint(['assigned_team_id'], ['mobile_teams.id'], ),
    )

    # Create indexes for staff_members
    op.create_index('ix_staff_user_id', 'staff_members', ['user_id'], unique=True)
    op.create_index('ix_staff_employee_code', 'staff_members', ['employee_code'], unique=True)
    op.create_index('ix_staff_status', 'staff_members', ['status'])
    op.create_index('ix_staff_employment_type', 'staff_members', ['employment_type'])
    op.create_index('ix_staff_status_deleted', 'staff_members', ['status', 'deleted_at'])
    op.create_index('ix_staff_employee_code_deleted', 'staff_members', ['employee_code', 'deleted_at'])

    # Create staff_documents table
    op.create_table(
        'staff_documents',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('staff_id', sa.String(), nullable=False),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('document_name', sa.String(255), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verified_by_user_id', sa.String(), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['staff_id'], ['staff_members.id'], ),
        sa.ForeignKeyConstraint(['verified_by_user_id'], ['users.id'], ),
    )

    # Create indexes for staff_documents
    op.create_index('ix_documents_staff_id', 'staff_documents', ['staff_id'])
    op.create_index('ix_documents_document_type', 'staff_documents', ['document_type'])
    op.create_index('ix_documents_expires_at', 'staff_documents', ['expires_at'])
    op.create_index('ix_documents_expires_verified', 'staff_documents', ['expires_at', 'verified'])

    # Create attendance_records table
    op.create_table(
        'attendance_records',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('staff_id', sa.String(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('check_in', sa.DateTime(timezone=True), nullable=True),
        sa.Column('check_out', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('hours_worked', sa.Numeric(5, 2), nullable=False, server_default='0'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['staff_id'], ['staff_members.id'], ),
    )

    # Create indexes for attendance_records
    op.create_index('ix_attendance_staff_id', 'attendance_records', ['staff_id'])
    op.create_index('ix_attendance_date', 'attendance_records', ['date'])
    op.create_index('ix_attendance_status', 'attendance_records', ['status'])
    op.create_index('ix_attendance_staff_date', 'attendance_records', ['staff_id', 'date'], unique=True)
    op.create_index('ix_attendance_date_status', 'attendance_records', ['date', 'status'])

    # Create work_schedules table
    op.create_table(
        'work_schedules',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('staff_id', sa.String(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('shift_start', sa.Time(), nullable=False),
        sa.Column('shift_end', sa.Time(), nullable=False),
        sa.Column('break_duration_minutes', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('effective_from', sa.Date(), nullable=False),
        sa.Column('effective_until', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['staff_id'], ['staff_members.id'], ),
    )

    # Create indexes for work_schedules
    op.create_index('ix_schedule_staff_id', 'work_schedules', ['staff_id'])
    op.create_index('ix_schedule_day_of_week', 'work_schedules', ['day_of_week'])
    op.create_index('ix_schedule_is_active', 'work_schedules', ['is_active'])
    op.create_index('ix_schedule_effective_from', 'work_schedules', ['effective_from'])
    op.create_index('ix_schedule_effective_until', 'work_schedules', ['effective_until'])
    op.create_index('ix_schedule_staff_day_active', 'work_schedules', ['staff_id', 'day_of_week', 'is_active'])
    op.create_index('ix_schedule_day_active_dates', 'work_schedules', ['day_of_week', 'is_active', 'effective_from', 'effective_until'])


def downgrade() -> None:
    """Drop staff management tables."""

    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table('work_schedules')
    op.drop_table('attendance_records')
    op.drop_table('staff_documents')
    op.drop_table('staff_members')
