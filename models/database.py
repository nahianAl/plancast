"""
Database models for PlanCast application.

This module defines the SQLAlchemy models for the PostgreSQL database,
including users, projects, usage tracking, and team collaboration.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float, 
    ForeignKey, JSON, Enum, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, Mapped
from sqlalchemy.sql import func
import enum

# Create base class for all models
Base = declarative_base()

# Enums
class UserRole(str, enum.Enum):
    """User roles in the system."""
    USER = "user"
    ADMIN = "admin"
    MODERATOR = "moderator"

class SubscriptionTier(str, enum.Enum):
    """Subscription tiers for billing (uppercase to match DB enum)."""
    FREE = "FREE"
    PROFESSIONAL = "PROFESSIONAL"
    ENTERPRISE = "ENTERPRISE"

class ProjectStatus(str, enum.Enum):
    """Project processing status (lowercase to match DB enum)."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TeamRole(str, enum.Enum):
    """Team member roles."""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"

class ActionType(str, enum.Enum):
    """Types of actions for usage tracking."""
    UPLOAD = "upload"
    CONVERT = "convert"
    EXPORT = "export"
    PREVIEW = "preview"
    DOWNLOAD = "download"

# User Management
class User(Base):
    """User account information."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    company = Column(String(255))
    subscription_tier = Column(
        Enum(SubscriptionTier, values_callable=lambda x: [e.value for e in x], name="subscriptiontier"),
        default=SubscriptionTier.FREE.value
    )
    api_key = Column(String(255), unique=True, index=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # Relationships
    projects: Mapped[List["Project"]] = relationship("Project", back_populates="user")
    usage_logs: Mapped[List["UsageLog"]] = relationship("UsageLog", back_populates="user")
    team_memberships: Mapped[List["TeamMember"]] = relationship("TeamMember", back_populates="user")
    owned_teams: Mapped[List["Team"]] = relationship("Team", back_populates="owner")
    
    # Indexes
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_subscription', 'subscription_tier'),
        Index('idx_users_created', 'created_at'),
    )

# Project Management
class Project(Base):
    """Project/Job tracking for floor plan conversions."""
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    status = Column(
        Enum(ProjectStatus, values_callable=lambda x: [e.value for e in x], name="projectstatus"),
        default=ProjectStatus.PENDING.value
    )
    
    # File information
    input_file_path = Column(String(500), nullable=False)
    file_size_mb = Column(Float, nullable=False)
    file_format = Column(String(10), nullable=False)  # jpg, png, pdf

    # Processing information
    current_step = Column(String(100))
    progress_percent = Column(Integer, default=0)
    processing_metadata = Column(JSON)  # AI processing results or misc

    # Output information
    output_files = Column(JSON)  # {format: file_path}

    # Error handling
    error_message = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="projects")
    usage_logs: Mapped[List["UsageLog"]] = relationship("UsageLog", back_populates="project")
    
    # Indexes
    __table_args__ = (
        Index('idx_projects_user', 'user_id'),
        Index('idx_projects_status', 'status'),
        Index('idx_projects_created', 'created_at'),
        Index('idx_projects_filename', 'filename'),
    )

# Usage Tracking
class UsageLog(Base):
    """Usage tracking for billing and analytics."""
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    action_type = Column(
        Enum(ActionType, values_callable=lambda x: [e.value for e in x], name="actiontype"),
        nullable=False
    )
    api_endpoint = Column(String(255), nullable=False)
    
    # Processing metrics
    processing_time_seconds = Column("processing_time_seconds", Float)
    file_size_mb = Column(Float)
    request_metadata = Column(JSON)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="usage_logs")
    project: Mapped[Optional["Project"]] = relationship("Project", back_populates="usage_logs")
    
    # Indexes
    __table_args__ = (
        Index('idx_usage_user', 'user_id'),
        Index('idx_usage_project', 'project_id'),
        Index('idx_usage_action', 'action_type'),
        Index('idx_usage_created', 'created_at'),
        Index('idx_usage_endpoint', 'api_endpoint'),
    )

# Team Collaboration
class Team(Base):
    """Team workspace for collaboration."""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subscription_tier = Column(Enum(SubscriptionTier), default=SubscriptionTier.PROFESSIONAL)
    max_members = Column(Integer, default=10)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="owned_teams")
    members: Mapped[List["TeamMember"]] = relationship("TeamMember", back_populates="team")
    
    # Indexes
    __table_args__ = (
        Index('idx_teams_owner', 'owner_id'),
        Index('idx_teams_subscription', 'subscription_tier'),
        Index('idx_teams_created', 'created_at'),
    )

class TeamMember(Base):
    """Team membership and permissions."""
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(Enum(TeamRole), default=TeamRole.MEMBER)
    permissions = Column(JSON)  # Specific permissions
    joined_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)
    
    # Relationships
    team: Mapped["Team"] = relationship("Team", back_populates="members")
    user: Mapped["User"] = relationship("User", back_populates="team_memberships")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('team_id', 'user_id', name='uq_team_member'),
        Index('idx_team_members_team', 'team_id'),
        Index('idx_team_members_user', 'user_id'),
        Index('idx_team_members_role', 'role'),
    )

# API Key Management
class APIKey(Base):
    """API key management for enterprise users."""
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    key_name = Column(String(255), nullable=False)
    key_hash = Column(String(255), nullable=False, unique=True)
    permissions = Column(JSON)  # API permissions
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True))
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_api_keys_user', 'user_id'),
        Index('idx_api_keys_hash', 'key_hash'),
        Index('idx_api_keys_active', 'is_active'),
        Index('idx_api_keys_expires', 'expires_at'),
    )

# Subscription and Billing
class Subscription(Base):
    """User subscription information."""
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tier = Column(Enum(SubscriptionTier), nullable=False)
    status = Column(String(50), default="active")  # active, cancelled, expired
    current_period_start = Column(DateTime(timezone=True), nullable=False)
    current_period_end = Column(DateTime(timezone=True), nullable=False)
    cancel_at_period_end = Column(Boolean, default=False)
    
    # Billing information
    stripe_subscription_id = Column(String(255))
    stripe_customer_id = Column(String(255))
    amount_cents = Column(Integer)
    currency = Column(String(3), default="USD")
    
    # Usage limits
    monthly_uploads = Column(Integer)
    monthly_conversions = Column(Integer)
    storage_gb = Column(Float)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user: Mapped["User"] = relationship("User")
    
    # Indexes
    __table_args__ = (
        Index('idx_subscriptions_user', 'user_id'),
        Index('idx_subscriptions_tier', 'tier'),
        Index('idx_subscriptions_status', 'status'),
        Index('idx_subscriptions_period', 'current_period_end'),
    )
