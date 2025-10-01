# Database Migrations

## Overview

This directory contains database migration scripts for the BlingAuto API.

## Structure

```
migrations/
├── versions/           # Migration files (auto-generated)
├── seeds/             # Data seeding scripts
├── alembic.ini        # Alembic configuration
├── env.py            # Migration environment setup
└── README.md         # This file
```

## Migration Commands

```bash
# Generate a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply all pending migrations
alembic upgrade head

# Downgrade one migration
alembic downgrade -1

# Show current revision
alembic current

# Show migration history
alembic history

# Upgrade to specific revision
alembic upgrade <revision>

# Downgrade to specific revision  
alembic downgrade <revision>
```

## Seeding Data

```bash
# Run all seed scripts
python -m migrations.seeds.run_all

# Run specific seed script
python -m migrations.seeds.initial_categories
python -m migrations.seeds.initial_services
```

## Migration Guidelines

1. **Always review** auto-generated migrations before applying
2. **Test migrations** on a copy of production data
3. **Backup database** before running migrations in production
4. **Use descriptive names** for migration messages
5. **Keep migrations focused** - one logical change per migration
6. **Add data migrations** when needed for schema changes

## File Naming

- Migration files: `<revision>_<description>.py`
- Seed files: `<order>_<description>.py`

Example:
- `001_initial_schema.py`
- `002_add_user_roles.py`
- `003_booking_status_enum.py`

## Production Deployment

1. Create migration: `alembic revision --autogenerate -m "Description"`
2. Review generated migration file
3. Test on staging environment
4. Deploy to production: `alembic upgrade head`
5. Verify schema changes
6. Run seed scripts if needed