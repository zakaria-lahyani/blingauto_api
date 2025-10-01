"""Initial schema for all features

Revision ID: 001_initial_schema
Revises: 
Create Date: 2025-01-10 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all initial tables for the complete application."""
    
    # AUTH FEATURE TABLES
    
    # Users table
    op.create_table('users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=False),
        sa.Column('last_name', sa.String(100), nullable=False),
        sa.Column('phone_number', sa.String(20), nullable=True),
        sa.Column('role', sa.String(50), nullable=False, default='customer'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_email_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('email_verified_at', sa.DateTime(), nullable=True),
        sa.Column('failed_login_attempts', sa.Integer(), nullable=False, default=0),
        sa.Column('locked_until', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_role'), 'users', ['role'], unique=False)
    
    # Sessions table
    op.create_table('sessions',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('access_token', sa.String(500), nullable=False),
        sa.Column('refresh_token', sa.String(500), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sessions_user_id'), 'sessions', ['user_id'], unique=False)
    op.create_index(op.f('ix_sessions_access_token'), 'sessions', ['access_token'], unique=True)
    
    # Email verification table
    op.create_table('email_verifications',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('token', sa.String(500), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, default=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_verifications_token'), 'email_verifications', ['token'], unique=True)
    
    # Password reset table
    op.create_table('password_resets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('token', sa.String(500), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('is_used', sa.Boolean(), nullable=False, default=False),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_resets_token'), 'password_resets', ['token'], unique=True)
    
    # Login attempts table
    op.create_table('login_attempts',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('ip_address', sa.String(45), nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False),
        sa.Column('failure_reason', sa.String(200), nullable=True),
        sa.Column('attempted_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_login_attempts_email'), 'login_attempts', ['email'], unique=False)
    op.create_index(op.f('ix_login_attempts_ip_address'), 'login_attempts', ['ip_address'], unique=False)
    
    # SERVICES FEATURE TABLES
    
    # Categories table
    op.create_table('categories',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('display_order', sa.Integer(), nullable=False, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_categories_display_order'), 'categories', ['display_order'], unique=False)
    
    # Services table
    op.create_table('services',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('category_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_popular', sa.Boolean(), nullable=False, default=False),
        sa.Column('display_order', sa.Integer(), nullable=False, default=0),
        sa.Column('image_url', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_services_category_id'), 'services', ['category_id'], unique=False)
    op.create_index(op.f('ix_services_is_popular'), 'services', ['is_popular'], unique=False)
    
    # VEHICLES FEATURE TABLES
    
    # Vehicles table
    op.create_table('vehicles',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('make', sa.String(50), nullable=False),
        sa.Column('model', sa.String(50), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('color', sa.String(30), nullable=False),
        sa.Column('license_plate', sa.String(20), nullable=False),
        sa.Column('vin', sa.String(17), nullable=True),
        sa.Column('vehicle_type', sa.String(20), nullable=False, default='car'),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vehicles_customer_id'), 'vehicles', ['customer_id'], unique=False)
    op.create_index(op.f('ix_vehicles_license_plate'), 'vehicles', ['license_plate'], unique=False)
    
    # BOOKINGS FEATURE TABLES
    
    # Bookings table
    op.create_table('bookings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('customer_id', sa.String(), nullable=False),
        sa.Column('vehicle_id', sa.String(), nullable=False),
        sa.Column('scheduled_at', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, default='pending'),
        sa.Column('booking_type', sa.String(20), nullable=False),
        sa.Column('total_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True, default=''),
        sa.Column('phone_number', sa.String(20), nullable=True, default=''),
        sa.Column('customer_location', sa.JSON(), nullable=True),
        sa.Column('cancellation_fee', sa.Numeric(10, 2), nullable=False, default=0.00),
        sa.Column('quality_rating', sa.Integer(), nullable=True),
        sa.Column('quality_feedback', sa.Text(), nullable=True),
        sa.Column('actual_start_time', sa.DateTime(), nullable=True),
        sa.Column('actual_end_time', sa.DateTime(), nullable=True),
        sa.Column('overtime_charges', sa.Numeric(10, 2), nullable=False, default=0.00),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancelled_by', sa.String(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('payment_intent_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['customer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vehicle_id'], ['vehicles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_bookings_customer_id'), 'bookings', ['customer_id'], unique=False)
    op.create_index(op.f('ix_bookings_scheduled_at'), 'bookings', ['scheduled_at'], unique=False)
    op.create_index(op.f('ix_bookings_status'), 'bookings', ['status'], unique=False)
    
    # Booking services table (junction table with additional data)
    op.create_table('booking_services',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('booking_id', sa.String(), nullable=False),
        sa.Column('service_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('price', sa.Numeric(10, 2), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['service_id'], ['services.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_booking_services_booking_id'), 'booking_services', ['booking_id'], unique=False)
    
    # SCHEDULING FEATURE TABLES
    
    # Wash bays table
    op.create_table('wash_bays',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('bay_number', sa.String(50), nullable=False),
        sa.Column('max_vehicle_size', sa.String(20), nullable=False, default='standard'),
        sa.Column('equipment_types', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('location_latitude', sa.Numeric(10, 8), nullable=True),
        sa.Column('location_longitude', sa.Numeric(11, 8), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bay_number')
    )
    
    # Mobile teams table
    op.create_table('mobile_teams',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('team_name', sa.String(100), nullable=False),
        sa.Column('base_location_latitude', sa.Numeric(10, 8), nullable=False),
        sa.Column('base_location_longitude', sa.Numeric(11, 8), nullable=False),
        sa.Column('service_radius_km', sa.Numeric(8, 2), nullable=False, default=50.0),
        sa.Column('daily_capacity', sa.Integer(), nullable=False, default=8),
        sa.Column('equipment_types', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, default='active'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Time slots table
    op.create_table('time_slots',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('resource_id', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(20), nullable=False),
        sa.Column('is_available', sa.Boolean(), nullable=False, default=True),
        sa.Column('booking_id', sa.String(), nullable=True),
        sa.Column('buffer_minutes', sa.Integer(), nullable=False, default=15),
        sa.Column('wash_bay_id', sa.String(), nullable=True),
        sa.Column('mobile_team_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['wash_bay_id'], ['wash_bays.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['mobile_team_id'], ['mobile_teams.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_time_slots_start_time'), 'time_slots', ['start_time'], unique=False)
    op.create_index(op.f('ix_time_slots_resource_id'), 'time_slots', ['resource_id'], unique=False)
    
    # Scheduling constraints table
    op.create_table('scheduling_constraints',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('min_advance_hours', sa.Integer(), nullable=False, default=2),
        sa.Column('max_advance_days', sa.Integer(), nullable=False, default=90),
        sa.Column('slot_duration_minutes', sa.Integer(), nullable=False, default=30),
        sa.Column('buffer_minutes', sa.Integer(), nullable=False, default=15),
        sa.Column('business_hours', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Business hours table
    op.create_table('business_hours',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('day_of_week', sa.String(10), nullable=False),
        sa.Column('open_time', sa.String(8), nullable=True),
        sa.Column('close_time', sa.String(8), nullable=True),
        sa.Column('is_closed', sa.Boolean(), nullable=False, default=False),
        sa.Column('break_periods', sa.JSON(), nullable=True),
        sa.Column('facility_id', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Drop all tables."""
    # Drop in reverse order due to foreign key constraints
    op.drop_table('business_hours')
    op.drop_table('scheduling_constraints')
    op.drop_table('time_slots')
    op.drop_table('mobile_teams')
    op.drop_table('wash_bays')
    op.drop_table('booking_services')
    op.drop_table('bookings')
    op.drop_table('vehicles')
    op.drop_table('services')
    op.drop_table('categories')
    op.drop_table('login_attempts')
    op.drop_table('password_resets')
    op.drop_table('email_verifications')
    op.drop_table('sessions')
    op.drop_table('users')