# Alembic Migration Guide

## Why Use Alembic Instead of `create_all()`?

**`create_all()` (Current - Development Only):**
- ❌ No migration history
- ❌ Can't rollback changes
- ❌ Doesn't handle schema changes
- ❌ Not production-safe

**Alembic (Recommended - Production):**
- ✅ Version-controlled migrations
- ✅ Rollback capability
- ✅ Handles schema changes safely
- ✅ Production-ready

## Setup Alembic

### 1. Generate Initial Migration

```bash
# Create initial migration from current models
alembic revision --autogenerate -m "Initial migration with auth and RBAC models"
```

This will create a file in `alembic/versions/` with all your tables.

### 2. Review the Migration

```bash
# Check the generated migration file
ls -la alembic/versions/
cat alembic/versions/xxxx_initial_migration.py
```

**Important:** Always review auto-generated migrations! Alembic might miss:
- Custom indexes
- Constraints
- Data migrations

### 3. Apply Migration

```bash
# Apply to database
alembic upgrade head
```

### 4. Update Lifespan (Already Done)

The `app/core/lifespan.py` has been updated to NOT run `create_all()` automatically.

## Common Alembic Commands

```bash
# Create new migration after model changes
alembic revision --autogenerate -m "Add new field to User"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific version
alembic downgrade <revision_id>

# Show current version
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## Workflow for Schema Changes

1. **Modify your models** (e.g., `app/models/user.py`)
2. **Generate migration:**
   ```bash
   alembic revision --autogenerate -m "Describe your change"
   ```
3. **Review the migration file** in `alembic/versions/`
4. **Apply migration:**
   ```bash
   alembic upgrade head
   ```

## Production Deployment

```bash
# In your deployment script or CI/CD
alembic upgrade head
```

## Development vs Production

**Development:**
```python
# Option 1: Use Alembic (recommended)
alembic upgrade head

# Option 2: Quick dev setup (uncomment in lifespan.py)
# from app.core.database import init_db
# await init_db()
```

**Production:**
```bash
# ALWAYS use Alembic
alembic upgrade head
```

## Initial Setup (First Time)

Since you already have Alembic configured, just run:

```bash
# 1. Generate initial migration
alembic revision --autogenerate -m "Initial migration"

# 2. Apply it
alembic upgrade head

# 3. Seed data
python scripts/seed_data.py

# 4. (Optional) Add indexes
python scripts/add_indexes.py
```

## Troubleshooting

**"command not found: alembic"**
```bash
pip install alembic
```

**"Target database is not up to date"**
```bash
alembic upgrade head
```

**"Can't locate revision identified by 'xxxx'"**
```bash
# Reset alembic (DANGER: Only in development!)
# Drop alembic_version table and regenerate
```

## Benefits Summary

✅ **Version Control** - Track all schema changes  
✅ **Rollback** - Undo migrations if needed  
✅ **Team Collaboration** - Share migrations via git  
✅ **Production Safety** - Test migrations before deploying  
✅ **Data Migrations** - Handle data transformations  
✅ **Audit Trail** - Know who changed what and when
