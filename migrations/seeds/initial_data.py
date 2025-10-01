"""
Initial seed data for the car wash application.
Creates default categories, services, facilities, and admin user.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import text
from app.core.db.session import get_db


def seed_initial_data():
    """Seed the database with initial data."""
    
    db = next(get_db())
    
    try:
        print("🌱 Starting database seeding...")
        
        # Create admin user
        admin_user_id = str(uuid.uuid4())
        admin_sql = text("""
            INSERT INTO users (id, email, password_hash, first_name, last_name, role, is_active, is_email_verified, email_verified_at, created_at, updated_at)
            VALUES (:id, :email, :password_hash, :first_name, :last_name, :role, :is_active, :is_email_verified, :email_verified_at, :created_at, :updated_at)
            ON CONFLICT (email) DO NOTHING
        """)
        
        db.execute(admin_sql, {
            'id': admin_user_id,
            'email': 'admin@blingauto.com',
            'password_hash': '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LdMpNrLLIz8/Jz8qG',  # 'admin123'
            'first_name': 'Admin',
            'last_name': 'User',
            'role': 'admin',
            'is_active': True,
            'is_email_verified': True,
            'email_verified_at': datetime.utcnow(),
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        print("✓ Admin user created")
        
        # Create service categories
        categories_data = [
            {
                'id': str(uuid.uuid4()),
                'name': 'Exterior Wash',
                'description': 'Complete exterior cleaning services',
                'icon': 'car-wash',
                'display_order': 1
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Interior Cleaning',
                'description': 'Thorough interior cleaning and detailing',
                'icon': 'vacuum',
                'display_order': 2
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Premium Detailing',
                'description': 'Professional detailing services',
                'icon': 'sparkles',
                'display_order': 3
            },
            {
                'id': str(uuid.uuid4()),
                'name': 'Protection Services',
                'description': 'Paint and interior protection',
                'icon': 'shield',
                'display_order': 4
            }
        ]
        
        category_sql = text("""
            INSERT INTO categories (id, name, description, icon, display_order, is_active, created_at, updated_at)
            VALUES (:id, :name, :description, :icon, :display_order, :is_active, :created_at, :updated_at)
            ON CONFLICT (name) DO NOTHING
        """)
        
        for category in categories_data:
            db.execute(category_sql, {
                **category,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
        
        print("✓ Service categories created")
        
        # Get category IDs for services
        exterior_cat = db.execute(text("SELECT id FROM categories WHERE name = 'Exterior Wash'")).first()
        interior_cat = db.execute(text("SELECT id FROM categories WHERE name = 'Interior Cleaning'")).first()
        premium_cat = db.execute(text("SELECT id FROM categories WHERE name = 'Premium Detailing'")).first()
        protection_cat = db.execute(text("SELECT id FROM categories WHERE name = 'Protection Services'")).first()
        
        # Create services
        services_data = [
            # Exterior Wash services
            {
                'id': str(uuid.uuid4()),
                'category_id': exterior_cat[0],
                'name': 'Basic Wash',
                'description': 'Exterior wash with soap and rinse',
                'price': Decimal('15.00'),
                'duration_minutes': 30,
                'is_popular': True,
                'display_order': 1
            },
            {
                'id': str(uuid.uuid4()),
                'category_id': exterior_cat[0],
                'name': 'Premium Wash',
                'description': 'Wash, wax, and tire shine',
                'price': Decimal('25.00'),
                'duration_minutes': 45,
                'is_popular': True,
                'display_order': 2
            },
            {
                'id': str(uuid.uuid4()),
                'category_id': exterior_cat[0],
                'name': 'Deluxe Wash',
                'description': 'Premium wash with undercarriage cleaning',
                'price': Decimal('35.00'),
                'duration_minutes': 60,
                'is_popular': False,
                'display_order': 3
            },
            
            # Interior Cleaning services
            {
                'id': str(uuid.uuid4()),
                'category_id': interior_cat[0],
                'name': 'Interior Vacuum',
                'description': 'Complete interior vacuuming',
                'price': Decimal('20.00'),
                'duration_minutes': 30,
                'is_popular': True,
                'display_order': 1
            },
            {
                'id': str(uuid.uuid4()),
                'category_id': interior_cat[0],
                'name': 'Interior Detail',
                'description': 'Deep cleaning and conditioning',
                'price': Decimal('40.00'),
                'duration_minutes': 90,
                'is_popular': False,
                'display_order': 2
            },
            
            # Premium Detailing services
            {
                'id': str(uuid.uuid4()),
                'category_id': premium_cat[0],
                'name': 'Full Detail',
                'description': 'Complete interior and exterior detailing',
                'price': Decimal('80.00'),
                'duration_minutes': 180,
                'is_popular': True,
                'display_order': 1
            },
            {
                'id': str(uuid.uuid4()),
                'category_id': premium_cat[0],
                'name': 'Paint Correction',
                'description': 'Professional paint correction and polishing',
                'price': Decimal('150.00'),
                'duration_minutes': 240,
                'is_popular': False,
                'display_order': 2
            },
            
            # Protection Services
            {
                'id': str(uuid.uuid4()),
                'category_id': protection_cat[0],
                'name': 'Ceramic Coating',
                'description': 'Long-lasting ceramic paint protection',
                'price': Decimal('300.00'),
                'duration_minutes': 360,
                'is_popular': False,
                'display_order': 1
            },
            {
                'id': str(uuid.uuid4()),
                'category_id': protection_cat[0],
                'name': 'Paint Protection Film',
                'description': 'Clear protective film application',
                'price': Decimal('500.00'),
                'duration_minutes': 480,
                'is_popular': False,
                'display_order': 2
            }
        ]
        
        service_sql = text("""
            INSERT INTO services (id, category_id, name, description, price, duration_minutes, is_popular, display_order, is_active, created_at, updated_at)
            VALUES (:id, :category_id, :name, :description, :price, :duration_minutes, :is_popular, :display_order, :is_active, :created_at, :updated_at)
            ON CONFLICT DO NOTHING
        """)
        
        for service in services_data:
            db.execute(service_sql, {
                **service,
                'is_active': True,
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
        
        print("✓ Services created")
        
        # Create wash bays
        wash_bays_data = [
            {
                'id': str(uuid.uuid4()),
                'bay_number': 'Bay 1',
                'max_vehicle_size': 'large',
                'equipment_types': ['pressure_washer', 'foam_cannon', 'dryer'],
                'status': 'active'
            },
            {
                'id': str(uuid.uuid4()),
                'bay_number': 'Bay 2',
                'max_vehicle_size': 'oversized',
                'equipment_types': ['pressure_washer', 'foam_cannon', 'dryer', 'wax_applicator'],
                'status': 'active'
            },
            {
                'id': str(uuid.uuid4()),
                'bay_number': 'Bay 3',
                'max_vehicle_size': 'standard',
                'equipment_types': ['pressure_washer', 'foam_cannon'],
                'status': 'active'
            }
        ]
        
        bay_sql = text("""
            INSERT INTO wash_bays (id, bay_number, max_vehicle_size, equipment_types, status, created_at, updated_at)
            VALUES (:id, :bay_number, :max_vehicle_size, :equipment_types, :status, :created_at, :updated_at)
            ON CONFLICT (bay_number) DO NOTHING
        """)
        
        for bay in wash_bays_data:
            db.execute(bay_sql, {
                **bay,
                'equipment_types': str(bay['equipment_types']),  # Convert to JSON string
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
        
        print("✓ Wash bays created")
        
        # Create mobile teams
        mobile_teams_data = [
            {
                'id': str(uuid.uuid4()),
                'team_name': 'Mobile Team Alpha',
                'base_location_latitude': 40.7128,
                'base_location_longitude': -74.0060,
                'service_radius_km': 50,
                'daily_capacity': 8,
                'equipment_types': ['portable_washer', 'vacuum', 'detailing_kit'],
                'status': 'active'
            },
            {
                'id': str(uuid.uuid4()),
                'team_name': 'Mobile Team Beta',
                'base_location_latitude': 34.0522,
                'base_location_longitude': -118.2437,
                'service_radius_km': 40,
                'daily_capacity': 6,
                'equipment_types': ['portable_washer', 'vacuum'],
                'status': 'active'
            }
        ]
        
        team_sql = text("""
            INSERT INTO mobile_teams (id, team_name, base_location_latitude, base_location_longitude, service_radius_km, daily_capacity, equipment_types, status, created_at, updated_at)
            VALUES (:id, :team_name, :base_location_latitude, :base_location_longitude, :service_radius_km, :daily_capacity, :equipment_types, :status, :created_at, :updated_at)
            ON CONFLICT DO NOTHING
        """)
        
        for team in mobile_teams_data:
            db.execute(team_sql, {
                **team,
                'equipment_types': str(team['equipment_types']),  # Convert to JSON string
                'created_at': datetime.utcnow(),
                'updated_at': datetime.utcnow()
            })
        
        print("✓ Mobile teams created")
        
        # Create default scheduling constraints
        constraints_sql = text("""
            INSERT INTO scheduling_constraints (id, is_active, min_advance_hours, max_advance_days, slot_duration_minutes, buffer_minutes, created_at, updated_at)
            VALUES (:id, :is_active, :min_advance_hours, :max_advance_days, :slot_duration_minutes, :buffer_minutes, :created_at, :updated_at)
            ON CONFLICT DO NOTHING
        """)
        
        db.execute(constraints_sql, {
            'id': str(uuid.uuid4()),
            'is_active': True,
            'min_advance_hours': 2,
            'max_advance_days': 90,
            'slot_duration_minutes': 30,
            'buffer_minutes': 15,
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow()
        })
        
        print("✓ Scheduling constraints created")
        
        # Create business hours for Monday-Saturday
        days = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday']
        
        hours_sql = text("""
            INSERT INTO business_hours (id, day_of_week, open_time, close_time, is_closed)
            VALUES (:id, :day_of_week, :open_time, :close_time, :is_closed)
            ON CONFLICT DO NOTHING
        """)
        
        for day in days:
            db.execute(hours_sql, {
                'id': str(uuid.uuid4()),
                'day_of_week': day,
                'open_time': '08:00:00',
                'close_time': '18:00:00',
                'is_closed': False
            })
        
        # Sunday closed
        db.execute(hours_sql, {
            'id': str(uuid.uuid4()),
            'day_of_week': 'sunday',
            'open_time': None,
            'close_time': None,
            'is_closed': True
        })
        
        print("✓ Business hours created")
        
        db.commit()
        print("🎉 Database seeding completed successfully!")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_initial_data()