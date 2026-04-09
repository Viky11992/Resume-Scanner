# PostgreSQL Setup Guide

This guide will help you set up PostgreSQL for the AI Resume Screener application.

## Prerequisites

- Python 3.10+
- PostgreSQL 14+ installed and running
- pip for package management

---

## Step 1: Install PostgreSQL

### Windows
1. Download PostgreSQL from: https://www.postgresql.org/download/windows/
2. Run the installer (use default settings)
3. During installation, remember the password you set for the `postgres` user
4. Ensure PostgreSQL service is running (check in Services app)

### Verify Installation
```bash
psql --version
```

---

## Step 2: Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `sqlalchemy` - ORM for database operations
- `psycopg2-binary` - PostgreSQL adapter for Python
- `alembic` - Database migration tool

---

## Step 3: Create Database

### Option A: Using pgAdmin (GUI)
1. Open pgAdmin (installed with PostgreSQL)
2. Connect to your PostgreSQL server
3. Right-click "Databases" → "Create" → "Database"
4. Name: `resume_screener`
5. Owner: `postgres`
6. Click "Save"

### Option B: Using psql (Command Line)
```bash
psql -U postgres
```

Then run:
```sql
CREATE DATABASE resume_screener;
```

---

## Step 4: Configure Environment Variables

1. Copy `.env.example` to `.env`:
```bash
copy .env.example .env
```

2. Edit `.env` file and update the `DATABASE_URL`:
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/resume_screener
```

Replace `YOUR_PASSWORD` with the password you set during PostgreSQL installation.

### Optional: Connection Pool Settings
```env
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=1800
```

---

## Step 5: Initialize Database Tables

The application will automatically create tables on first run. However, you can manually initialize them:

```python
from database_postgres import init_db
init_db()
```

Or simply run the application - tables are created automatically.

---

## Step 6: Migrate Data from MongoDB (Optional)

If you have existing data in MongoDB:

```bash
python migrate_data.py
```

This script will:
- Connect to both MongoDB and PostgreSQL
- Migrate all users, jobs, candidates, and rankings
- Skip duplicate records
- Provide detailed migration statistics

---

## Step 7: Run the Application

```bash
streamlit run app.py
```

The application will:
1. Initialize database tables (if not exists)
2. Create default admin and recruiter accounts
3. Start the web interface

### Default Credentials
- **Admin**: `admin` / `admin123`
- **Recruiter**: `recruiter` / `recruiter123`

**⚠️ Change these passwords immediately after first login!**

---

## Verification

### Check Database Connection
```python
from database_postgres import check_connection, get_database_status

print(check_connection())  # Should print True
print(get_database_status())  # Shows database info and record counts
```

### Check Tables Created
Using psql:
```bash
psql -U postgres -d resume_screener
\dt
```

You should see:
- `users`
- `jobs`
- `candidates`
- `rankings`
- `alembic_version` (if using Alembic)

---

## Troubleshooting

### Issue: "could not connect to server"
**Solution**: Ensure PostgreSQL service is running
- Windows: Open Services app → Start "postgresql-x64-XX" service
- Check: `pg_lsclusters` (Linux/Mac) or Services app (Windows)

### Issue: "password authentication failed"
**Solution**: Update password in `.env` file to match your PostgreSQL password

### Issue: "database does not exist"
**Solution**: Create the database using Step 3 above

### Issue: "relation does not exist"
**Solution**: Run `init_db()` or restart the application to create tables

---

## Database Schema

### Tables Created

#### `users`
- User authentication and profile data
- Unique constraints on `username` and `email`
- Indexes for fast lookups

#### `jobs`
- Job descriptions and parsed data
- Required skills stored as JSON
- One-to-many relationship with rankings

#### `candidates`
- Resume parsing results
- Skills, education, experience stored as JSON
- One-to-many relationship with rankings

#### `rankings`
- Screening results linking jobs and candidates
- Match scores (0-1 range enforced by CHECK constraint)
- Skills matched/missing stored as JSON
- Foreign keys with CASCADE delete

---

## Backup & Restore

### Backup Database
```bash
pg_dump -U postgres resume_screener > backup.sql
```

### Restore Database
```bash
psql -U postgres resume_screener < backup.sql
```

---

## Performance Optimization

### Indexes
All frequently queried columns are indexed:
- `users.username`, `users.email`
- `jobs.job_id`, `jobs.created_at`
- `candidates.candidate_id`, `candidates.email`, `candidates.name`
- `rankings.job_id`, `rankings.candidate_id`, `rankings.score`
- Composite index: `rankings(job_id, score)`

### Connection Pooling
Default settings handle 10 concurrent connections with overflow up to 30.
Adjust in `.env` based on your server capacity.

---

## Next Steps

1. **Secure Your Database**: Change default PostgreSQL password
2. **Update JWT_SECRET**: Generate a secure random key
3. **Add SSL**: Configure PostgreSQL SSL for production
4. **Setup Backups**: Schedule regular pg_dump backups
5. **Monitor Performance**: Use pg_stat_statements extension

---

## Support

For issues or questions:
1. Check PostgreSQL logs
2. Review error messages in application
3. Verify connection string in `.env`
4. Test connection: `psql -U postgres -d resume_screener`
