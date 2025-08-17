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
    # Create enum types
    op.execute("CREATE TYPE subscriptiontier AS ENUM ('free', 'pro', 'enterprise')")
    op.execute("CREATE TYPE projectstatus AS ENUM ('pending', 'processing', 'completed', 'failed', 'cancelled')")
    op.execute("CREATE TYPE actiontype AS ENUM ('upload', 'processing', 'download', 'api_call', 'export')")

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('company', sa.String(length=200), nullable=True),
        sa.Column('subscription_tier', postgresql.ENUM('free', 'pro', 'enterprise', name='subscriptiontier'), nullable=False),
        sa.Column('api_key', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_api_key'), 'users', ['api_key'], unique=True)

    # Create projects table
    op.create_table('projects',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('input_file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size_mb', sa.Float(), nullable=False),
        sa.Column('file_format', sa.String(length=10), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'processing', 'completed', 'failed', 'cancelled', name='projectstatus'), nullable=False),
        sa.Column('current_step', sa.String(length=100), nullable=True),
        sa.Column('progress_percent', sa.Integer(), nullable=False),
        sa.Column('output_files', sa.JSON(), nullable=True),
        sa.Column('processing_metadata', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_projects_user_id'), 'projects', ['user_id'])
    op.create_index(op.f('ix_projects_status'), 'projects', ['status'])

    # Create usage_logs table
    op.create_table('usage_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('action_type', postgresql.ENUM('upload', 'processing', 'download', 'api_call', 'export', name='actiontype'), nullable=False),
        sa.Column('api_endpoint', sa.String(length=200), nullable=False),
        sa.Column('file_size_mb', sa.Float(), nullable=True),
        sa.Column('processing_time_seconds', sa.Float(), nullable=True),
        sa.Column('request_metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usage_logs_user_id'), 'usage_logs', ['user_id'])
    op.create_index(op.f('ix_usage_logs_created_at'), 'usage_logs', ['created_at'])

    # Insert default admin user
    op.execute("""
        INSERT INTO users (email, password_hash, first_name, last_name, company, subscription_tier, is_active, is_verified, created_at, updated_at)
        VALUES ('admin@plancast.com', '$2b$12$dummy.hash.for.admin', 'Admin', 'User', 'PlanCast', 'enterprise', true, true, NOW(), NOW())
    """)


def downgrade() -> None:
    # Drop tables
    op.drop_table('usage_logs')
    op.drop_table('projects')
    op.drop_table('users')
    
    # Drop enum types
    op.execute("DROP TYPE IF EXISTS actiontype")
    op.execute("DROP TYPE IF EXISTS projectstatus") 
    op.execute("DROP TYPE IF EXISTS subscriptiontier")
