"""Initial database schema with users, projects, and usage_logs tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2024-08-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_schema'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types (only if they don't exist)
    op.execute("CREATE TYPE IF NOT EXISTS subscriptiontier AS ENUM ('free', 'pro', 'enterprise')")
    op.execute("CREATE TYPE IF NOT EXISTS projectstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled')")
    op.execute("CREATE TYPE IF NOT EXISTS actiontype AS ENUM ('upload', 'processing', 'download', 'api_call', 'export')")

    # Create users table (check if exists first)
    op.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(100),
            last_name VARCHAR(100),
            company VARCHAR(200),
            subscription_tier subscriptiontier NOT NULL DEFAULT 'free',
            api_key VARCHAR(255),
            is_active BOOLEAN NOT NULL DEFAULT true,
            is_verified BOOLEAN NOT NULL DEFAULT false,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            last_login TIMESTAMP
        )
    """)
    
    # Create indexes for users table
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_email ON users (email)")
    op.execute("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_api_key ON users (api_key)")

    # Create projects table (using raw SQL for better control)
    op.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255) NOT NULL,
            input_file_path VARCHAR(500) NOT NULL,
            file_size_mb FLOAT NOT NULL,
            file_format VARCHAR(10) NOT NULL,
            status projectstatus NOT NULL DEFAULT 'pending',
            current_step VARCHAR(100),
            progress_percent INTEGER NOT NULL DEFAULT 0,
            output_files JSON,
            processing_metadata JSON,
            error_message TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMP
        )
    """)
    
    # Create indexes for projects table
    op.execute("CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_projects_status ON projects (status)")

    # Create usage_logs table
    op.execute("""
        CREATE TABLE IF NOT EXISTS usage_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            project_id INTEGER REFERENCES projects(id),
            action_type actiontype NOT NULL,
            api_endpoint VARCHAR(200) NOT NULL,
            file_size_mb FLOAT,
            processing_time_seconds FLOAT,
            request_metadata JSON,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    
    # Create indexes for usage_logs table
    op.execute("CREATE INDEX IF NOT EXISTS ix_usage_logs_user_id ON usage_logs (user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_usage_logs_created_at ON usage_logs (created_at)")

    # Insert default admin user (only if not exists)
    op.execute("""
        INSERT INTO users (email, password_hash, first_name, last_name, company, subscription_tier, is_active, is_verified, created_at, updated_at)
        SELECT 'admin@plancast.com', '$2b$12$dummy.hash.for.admin', 'Admin', 'User', 'PlanCast', 'enterprise', true, true, NOW(), NOW()
        WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@plancast.com')
    """)


def downgrade() -> None:
    # Drop tables
    op.execute("DROP TABLE IF EXISTS usage_logs CASCADE")
    op.execute("DROP TABLE IF EXISTS projects CASCADE")
    op.execute("DROP TABLE IF EXISTS users CASCADE")
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS actiontype")
    op.execute("DROP TYPE IF EXISTS projectstatus") 
    op.execute("DROP TYPE IF EXISTS subscriptiontier")