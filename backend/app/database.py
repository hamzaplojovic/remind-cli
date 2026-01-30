"""Database models and initialization."""

from datetime import datetime, timezone
from typing import Generator, TYPE_CHECKING

from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

if TYPE_CHECKING:
    from app.config import Settings

Base = declarative_base()


class UserModel(Base):
    """Represents a user with a license token."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    token = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, nullable=False)
    plan_tier = Column(String, nullable=False)  # free, indie, pro, team
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime, nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<UserModel token={self.token} plan={self.plan_tier}>"


class UsageLogModel(Base):
    """Tracks usage of features for billing."""

    __tablename__ = "usage_logs"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    feature = Column(String, nullable=False)  # "ai_suggestion", "nudge", etc.
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    cost_cents = Column(Integer, nullable=False)  # Store as cents (integer)
    metadata_json = Column(JSON, default=dict, nullable=False)

    def __repr__(self):
        return (
            f"<UsageLogModel user_id={self.user_id} feature={self.feature} cost={self.cost_cents}¢>"
        )


class RateLimitModel(Base):
    """Tracks request rate limiting per user."""

    __tablename__ = "rate_limits"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    request_count = Column(Integer, default=0, nullable=False)
    reset_at = Column(DateTime, nullable=False)

    def __repr__(self):
        return f"<RateLimitModel user_id={self.user_id} count={self.request_count}>"


# Database session management
def get_engine():
    """Create database engine."""
    from app.config import get_settings

    settings = get_settings()
    is_sqlite = "sqlite" in settings.database_url
    connect_args = {"check_same_thread": False} if is_sqlite else {}
    return create_engine(settings.database_url, connect_args=connect_args)


def get_session_local():
    """Create session factory."""
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def init_db():
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Get database session (for dependency injection)."""
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
