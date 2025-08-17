"""
Repository layer for PlanCast database operations.

This module provides clean data access methods for all database models,
abstracting away the SQLAlchemy session management details.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, desc, func

from models.database import (
    User, Project, UsageLog, Team, TeamMember, APIKey, Subscription,
    UserRole, SubscriptionTier, ProjectStatus, TeamRole, ActionType
)

class UserRepository:
    """Repository for user-related database operations."""
    
    @staticmethod
    def create_user(
        session: Session,
        email: str,
        password_hash: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        company: Optional[str] = None,
        subscription_tier: SubscriptionTier = SubscriptionTier.FREE
    ) -> User:
        """Create a new user."""
        user = User(
            email=email,
            password_hash=password_hash,
            first_name=first_name,
            last_name=last_name,
            company=company,
            subscription_tier=subscription_tier
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    
    @staticmethod
    def get_user_by_id(session: Session, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return session.query(User).filter(User.id == user_id).first()
    
    @staticmethod
    def get_user_by_email(session: Session, email: str) -> Optional[User]:
        """Get user by email."""
        return session.query(User).filter(User.email == email).first()
    
    @staticmethod
    def get_user_by_api_key(session: Session, api_key: str) -> Optional[User]:
        """Get user by API key."""
        return session.query(User).filter(User.api_key == api_key).first()
    
    @staticmethod
    def update_user(
        session: Session,
        user_id: int,
        **kwargs
    ) -> Optional[User]:
        """Update user information."""
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            user.updated_at = datetime.now()
            session.commit()
            session.refresh(user)
        return user
    
    @staticmethod
    def delete_user(session: Session, user_id: int) -> bool:
        """Delete a user."""
        user = session.query(User).filter(User.id == user_id).first()
        if user:
            session.delete(user)
            session.commit()
            return True
        return False
    
    @staticmethod
    def list_users(
        session: Session,
        skip: int = 0,
        limit: int = 100,
        active_only: bool = True
    ) -> List[User]:
        """List users with pagination."""
        query = session.query(User)
        if active_only:
            query = query.filter(User.is_active == True)
        return query.offset(skip).limit(limit).all()

class ProjectRepository:
    """Repository for project-related database operations."""
    
    @staticmethod
    def create_project(
        session: Session,
        user_id: int,
        filename: str,
        original_filename: str,
        input_file_path: str,
        file_size_mb: float,
        file_format: str,
        scale_reference: Optional[Dict] = None
    ) -> Project:
        """Create a new project."""
        project = Project(
            user_id=user_id,
            filename=filename,
            original_filename=original_filename,
            input_file_path=input_file_path,
            file_size_mb=file_size_mb,
            file_format=file_format,
        )
        session.add(project)
        session.commit()
        session.refresh(project)
        return project
    
    @staticmethod
    def get_project_by_id(session: Session, project_id: int) -> Optional[Project]:
        """Get project by ID with user information."""
        return session.query(Project).options(
            joinedload(Project.user)
        ).filter(Project.id == project_id).first()
    
    @staticmethod
    def get_projects_by_user(
        session: Session,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[ProjectStatus] = None
    ) -> List[Project]:
        """Get projects for a specific user."""
        query = session.query(Project).filter(Project.user_id == user_id)
        if status:
            query = query.filter(Project.status == status)
        return query.order_by(desc(Project.created_at)).offset(skip).limit(limit).all()
    
    @staticmethod
    def update_project_status(
        session: Session,
        project_id: int,
        status: ProjectStatus,
        current_step: Optional[str] = None,
        progress_percent: Optional[int] = None,
        **kwargs
    ) -> Optional[Project]:
        """Update project status and progress."""
        project = session.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = status
            if current_step:
                project.current_step = current_step
            if progress_percent is not None:
                project.progress_percent = progress_percent
            
            # Update timestamps
            if status == ProjectStatus.PROCESSING and not project.started_at:
                project.started_at = datetime.now()
            elif status in [ProjectStatus.COMPLETED, ProjectStatus.FAILED] and not project.completed_at:
                project.completed_at = datetime.now()
            
            # Update other fields
            for key, value in kwargs.items():
                if hasattr(project, key):
                    setattr(project, key, value)
            
            session.commit()
            session.refresh(project)
        return project
    
    @staticmethod
    def get_project_stats(session: Session, user_id: int) -> Dict[str, Any]:
        """Get project statistics for a user."""
        stats = session.query(
            func.count(Project.id).label('total_projects'),
            func.count(Project.id).filter(Project.status == ProjectStatus.COMPLETED).label('completed_projects'),
            func.count(Project.id).filter(Project.status == ProjectStatus.FAILED).label('failed_projects'),
            func.avg(Project.processing_time_seconds).label('avg_processing_time')
        ).filter(Project.user_id == user_id).first()
        
        return {
            'total_projects': stats.total_projects or 0,
            'completed_projects': stats.completed_projects or 0,
            'failed_projects': stats.failed_projects or 0,
            'avg_processing_time': stats.avg_processing_time or 0
        }

class UsageRepository:
    """Repository for usage tracking operations."""
    
    @staticmethod
    def log_usage(
        session: Session,
        user_id: int,
        action_type: ActionType,
        api_endpoint: str,
        project_id: Optional[int] = None,
        processing_time: Optional[float] = None,
        file_size_mb: Optional[float] = None,
        credits_used: int = 1,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        request_metadata: Optional[Dict] = None
    ) -> UsageLog:
        """Log a usage event."""
        usage_log = UsageLog(
            user_id=user_id,
            project_id=project_id,
            action_type=action_type,
            api_endpoint=api_endpoint,
            processing_time=processing_time,
            file_size_mb=file_size_mb,
            credits_used=credits_used,
            ip_address=ip_address,
            user_agent=user_agent,
            request_metadata=request_metadata
        )
        session.add(usage_log)
        session.commit()
        session.refresh(usage_log)
        return usage_log
    
    @staticmethod
    def get_user_usage(
        session: Session,
        user_id: int,
        days: int = 30
    ) -> List[UsageLog]:
        """Get usage logs for a user within a time period."""
        cutoff_date = datetime.now() - timedelta(days=days)
        return session.query(UsageLog).filter(
            and_(
                UsageLog.user_id == user_id,
                UsageLog.created_at >= cutoff_date
            )
        ).order_by(desc(UsageLog.created_at)).all()
    
    @staticmethod
    def get_usage_summary(
        session: Session,
        user_id: int,
        days: int = 30
    ) -> Dict[str, Any]:
        """Get usage summary for a user."""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Get total usage
        total_usage = session.query(
            func.count(UsageLog.id).label('total_actions'),
            func.sum(UsageLog.credits_used).label('total_credits'),
            func.sum(UsageLog.processing_time).label('total_processing_time')
        ).filter(
            and_(
                UsageLog.user_id == user_id,
                UsageLog.created_at >= cutoff_date
            )
        ).first()
        
        # Get usage by action type
        usage_by_type = session.query(
            UsageLog.action_type,
            func.count(UsageLog.id).label('count')
        ).filter(
            and_(
                UsageLog.user_id == user_id,
                UsageLog.created_at >= cutoff_date
            )
        ).group_by(UsageLog.action_type).all()
        
        return {
            'total_actions': total_usage.total_actions or 0,
            'total_credits': total_usage.total_credits or 0,
            'total_processing_time': total_usage.total_processing_time or 0,
            'usage_by_type': {item.action_type.value: item.count for item in usage_by_type}
        }

class TeamRepository:
    """Repository for team-related operations."""
    
    @staticmethod
    def create_team(
        session: Session,
        name: str,
        owner_id: int,
        description: Optional[str] = None,
        subscription_tier: SubscriptionTier = SubscriptionTier.PROFESSIONAL,
        max_members: int = 10
    ) -> Team:
        """Create a new team."""
        team = Team(
            name=name,
            owner_id=owner_id,
            description=description,
            subscription_tier=subscription_tier,
            max_members=max_members
        )
        session.add(team)
        session.commit()
        session.refresh(team)
        
        # Add owner as team member
        member = TeamMember(
            team_id=team.id,
            user_id=owner_id,
            role=TeamRole.OWNER
        )
        session.add(member)
        session.commit()
        
        return team
    
    @staticmethod
    def get_team_by_id(session: Session, team_id: int) -> Optional[Team]:
        """Get team by ID with members."""
        return session.query(Team).options(
            joinedload(Team.members).joinedload(TeamMember.user)
        ).filter(Team.id == team_id).first()
    
    @staticmethod
    def get_user_teams(session: Session, user_id: int) -> List[Team]:
        """Get all teams a user is a member of."""
        return session.query(Team).join(TeamMember).filter(
            and_(
                TeamMember.user_id == user_id,
                TeamMember.is_active == True
            )
        ).all()
    
    @staticmethod
    def add_team_member(
        session: Session,
        team_id: int,
        user_id: int,
        role: TeamRole = TeamRole.MEMBER,
        permissions: Optional[Dict] = None
    ) -> TeamMember:
        """Add a user to a team."""
        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role,
            permissions=permissions
        )
        session.add(member)
        session.commit()
        session.refresh(member)
        return member

class SubscriptionRepository:
    """Repository for subscription operations."""
    
    @staticmethod
    def create_subscription(
        session: Session,
        user_id: int,
        tier: SubscriptionTier,
        current_period_start: datetime,
        current_period_end: datetime,
        stripe_subscription_id: Optional[str] = None,
        stripe_customer_id: Optional[str] = None,
        amount_cents: Optional[int] = None,
        monthly_uploads: Optional[int] = None,
        monthly_conversions: Optional[int] = None,
        storage_gb: Optional[float] = None
    ) -> Subscription:
        """Create a new subscription."""
        subscription = Subscription(
            user_id=user_id,
            tier=tier,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            stripe_subscription_id=stripe_subscription_id,
            stripe_customer_id=stripe_customer_id,
            amount_cents=amount_cents,
            monthly_uploads=monthly_uploads,
            monthly_conversions=monthly_conversions,
            storage_gb=storage_gb
        )
        session.add(subscription)
        session.commit()
        session.refresh(subscription)
        return subscription
    
    @staticmethod
    def get_active_subscription(session: Session, user_id: int) -> Optional[Subscription]:
        """Get the active subscription for a user."""
        return session.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == "active",
                Subscription.current_period_end > datetime.now()
            )
        ).first()
    
    @staticmethod
    def update_subscription_status(
        session: Session,
        subscription_id: int,
        status: str,
        **kwargs
    ) -> Optional[Subscription]:
        """Update subscription status."""
        subscription = session.query(Subscription).filter(Subscription.id == subscription_id).first()
        if subscription:
            subscription.status = status
            for key, value in kwargs.items():
                if hasattr(subscription, key):
                    setattr(subscription, key, value)
            subscription.updated_at = datetime.now()
            session.commit()
            session.refresh(subscription)
        return subscription
