# PlanCast PostgreSQL Database Setup

This document explains how to set up and configure the PostgreSQL database for PlanCast, including local development and production deployment.

## 🗄️ Database Overview

PlanCast uses PostgreSQL for:
- **User Management**: Authentication, profiles, subscriptions
- **Project Tracking**: Floor plan conversions, processing status, file management
- **Usage Analytics**: API usage, billing metrics, performance tracking
- **Team Collaboration**: Workspaces, member management, permissions
- **Billing Integration**: Subscription management, payment tracking

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install PostgreSQL dependencies
pip install -r requirements.txt

# Or install just the database packages
pip install sqlalchemy psycopg2-binary alembic asyncpg
```

### 2. Set Up Environment Variables

Copy the environment template and configure your database:

```bash
cp env.example .env
```

Edit `.env` with your database settings:

```bash
# Local Development
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=plancast
POSTGRES_USER=plancast_user
POSTGRES_PASSWORD=plancast_password

# PostgreSQL superuser password (for setup script)
POSTGRES_SUPERUSER_PASSWORD=your_superuser_password
```

### 3. Run Database Setup

```bash
# Automatic setup (creates database, user, and tables)
python scripts/setup_database.py

# Or manual setup (see Manual Setup section below)
```

### 4. Test Database Connection

```bash
# Run comprehensive database tests
python test_database_setup.py
```

## 💻 Local Development Setup

### Prerequisites

- **PostgreSQL 12+** installed and running
- **Python 3.8+** with pip
- **psycopg2** or **psycopg2-binary** for PostgreSQL connectivity

### Step-by-Step Setup

#### 1. Install PostgreSQL

**macOS (using Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**Windows:**
Download and install from [PostgreSQL official website](https://www.postgresql.org/download/windows/)

#### 2. Create Database and User

**Option A: Using the setup script (recommended)**
```bash
python scripts/setup_database.py
```

**Option B: Manual creation**
```bash
# Connect as postgres superuser
sudo -u postgres psql

# Create user and database
CREATE USER plancast_user WITH PASSWORD 'plancast_password';
CREATE DATABASE plancast;
GRANT ALL PRIVILEGES ON DATABASE plancast TO plancast_user;
GRANT ALL ON SCHEMA public TO plancast_user;
\q
```

#### 3. Run Database Migrations

```bash
# Initialize Alembic (first time only)
alembic init migrations

# Create initial migration
alembic revision --autogenerate -m "Initial database schema"

# Apply migrations
alembic upgrade head
```

#### 4. Verify Setup

```bash
# Test database connection
python test_database_setup.py
```

## 🌐 Production Deployment (Railway)

### Automatic Setup

Railway automatically provides a `DATABASE_URL` environment variable when you add a PostgreSQL service.

### Manual Configuration

1. **Add PostgreSQL Service** in Railway dashboard
2. **Set Environment Variables**:
   ```bash
   DATABASE_URL=postgresql://username:password@host:port/database
   ENVIRONMENT=production
   ```
3. **Deploy** - migrations run automatically

### Railway Configuration

The `railway.json` file is already configured for PostgreSQL:

```json
{
  "services": [
    {
      "name": "plancast-database",
      "type": "postgresql"
    }
  ]
}
```

## 🗂️ Database Schema

### Core Tables

#### Users
```sql
users (
  id, email, password_hash, first_name, last_name, company,
  subscription_tier, api_key, is_active, is_verified,
  created_at, updated_at, last_login
)
```

#### Projects
```sql
projects (
  id, user_id, filename, original_filename, status,
  input_file_path, file_size_mb, file_format,
  scale_reference, processing_metadata, current_step,
  progress_percent, output_files_json, building_dimensions,
  processing_time_seconds, error_message, warnings,
  created_at, started_at, completed_at
)
```

#### Usage Logs
```sql
usage_logs (
  id, user_id, project_id, action_type, api_endpoint,
  processing_time, file_size_mb, credits_used,
  ip_address, user_agent, request_metadata, created_at
)
```

#### Teams
```sql
teams (
  id, name, description, owner_id, subscription_tier,
  max_members, is_active, created_at, updated_at
)
```

### Relationships

- **User** → **Projects** (one-to-many)
- **User** → **UsageLogs** (one-to-many)
- **User** → **Teams** (many-to-many via TeamMember)
- **Project** → **UsageLogs** (one-to-many)

## 🔧 Database Operations

### Using the Repository Layer

```python
from models.repository import UserRepository, ProjectRepository
from models.database_connection import get_db_session

# Create a user
with get_db_session() as session:
    user = UserRepository.create_user(
        session=session,
        email="user@example.com",
        password_hash="hashed_password",
        first_name="John",
        last_name="Doe"
    )

# Create a project
project = ProjectRepository.create_project(
    session=session,
    user_id=user.id,
    filename="floorplan.jpg",
    original_filename="floorplan.jpg",
    input_file_path="/uploads/floorplan.jpg",
    file_size_mb=2.5,
    file_format="jpg"
)
```

### Direct SQLAlchemy Usage

```python
from models.database import User, Project
from models.database_connection import get_db_session

with get_db_session() as session:
    # Query users
    users = session.query(User).filter(User.is_active == True).all()
    
    # Query projects with user info
    projects = session.query(Project).join(User).filter(
        Project.status == "completed"
    ).all()
```

## 📊 Database Health Monitoring

### Health Check Endpoint

The database health is automatically checked at `/health`:

```python
from models.database_connection import check_database_health

health_status = check_database_health()
# Returns: {'status': 'healthy', 'connection': 'ok', 'query': 'ok'}
```

### Connection Pooling

Database connections are automatically managed with connection pooling:

```python
# Configuration in config/settings.py
POSTGRES_POOL_SIZE = 10
POSTGRES_MAX_OVERFLOW = 20
POSTGRES_POOL_TIMEOUT = 30
POSTGRES_POOL_RECYCLE = 3600
```

## 🔄 Database Migrations

### Creating Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Description of changes"

# Manual migration
alembic revision -m "Description of changes"
```

### Applying Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply specific migration
alembic upgrade <revision_id>

# Rollback migration
alembic downgrade <revision_id>
```

### Migration Status

```bash
# Check current migration
alembic current

# Check migration history
alembic history

# Check pending migrations
alembic show <revision_id>
```

## 🧪 Testing

### Run Database Tests

```bash
# Comprehensive database testing
python test_database_setup.py

# Test specific components
python -c "
from models.database_connection import test_connection
print('Connection:', test_connection())
"
```

### Test Data

The test script creates and cleans up test data automatically:

- Test users with sample profiles
- Test projects with various statuses
- Usage logs for analytics testing
- Automatic cleanup after tests

## 🚨 Troubleshooting

### Common Issues

#### 1. Connection Refused
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql  # macOS
sudo systemctl status postgresql      # Linux
```

#### 2. Authentication Failed
```bash
# Check pg_hba.conf configuration
# Ensure password authentication is enabled for local connections
```

#### 3. Permission Denied
```bash
# Ensure user has proper privileges
GRANT ALL PRIVILEGES ON DATABASE plancast TO plancast_user;
GRANT ALL ON SCHEMA public TO plancast_user;
```

#### 4. Migration Errors
```bash
# Reset migrations (DANGEROUS - destroys data)
alembic downgrade base
alembic upgrade head

# Check migration files for syntax errors
alembic check
```

### Debug Mode

Enable SQL query logging:

```bash
# Set in .env
SQL_ECHO=true

# Or set environment variable
export SQL_ECHO=true
```

## 📚 API Integration

### Database in FastAPI Endpoints

```python
from fastapi import Depends
from models.database_connection import get_db_session
from models.repository import ProjectRepository

@app.get("/projects/{project_id}")
async def get_project(
    project_id: int,
    session: Session = Depends(get_db_session)
):
    project = ProjectRepository.get_project_by_id(session, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project
```

### Async Database Support

```python
from models.database_connection import get_async_db_session

@app.get("/projects")
async def list_projects(
    session: AsyncSession = Depends(get_async_db_session)
):
    # Async database operations
    pass
```

## 🔐 Security Considerations

### Password Hashing
- Passwords are hashed using SHA-256 (consider upgrading to bcrypt/Argon2)
- API keys are securely generated using `secrets.token_urlsafe()`

### SQL Injection Protection
- All queries use SQLAlchemy ORM (parameterized queries)
- No raw SQL strings in user input

### Connection Security
- SSL mode enabled for production connections
- Connection pooling with automatic cleanup
- Prepared statements for repeated queries

## 📈 Performance Optimization

### Indexes
- Primary keys automatically indexed
- Foreign keys indexed for join performance
- Custom indexes on frequently queried fields

### Query Optimization
- Lazy loading with `joinedload()` for relationships
- Pagination support for large result sets
- Efficient aggregation queries for analytics

### Connection Management
- Connection pooling reduces connection overhead
- Automatic connection recycling prevents stale connections
- Connection health checks with `pool_pre_ping`

## 🔮 Future Enhancements

### Planned Features
- **Read Replicas**: Separate read/write databases for scaling
- **Sharding**: Horizontal partitioning for large datasets
- **Caching**: Redis integration for frequently accessed data
- **Backup**: Automated database backups and point-in-time recovery
- **Monitoring**: Advanced metrics and alerting

### Migration Path
- Database schema versioning
- Backward compatibility maintenance
- Zero-downtime migration strategies

## 📞 Support

### Getting Help
1. Check this README for common solutions
2. Review the test scripts for working examples
3. Check database logs for detailed error messages
4. Verify environment variables and configuration

### Useful Commands
```bash
# Database connection test
python -c "from models.database_connection import test_connection; print(test_connection())"

# Migration status
alembic current

# Database health
python -c "from models.database_connection import check_database_health; print(check_database_health())"

# Create fresh database
python scripts/setup_database.py
```

---

**🎉 Congratulations!** Your PlanCast PostgreSQL database is now set up and ready to use. The database will automatically handle user management, project tracking, and usage analytics for your floor plan conversion service.
