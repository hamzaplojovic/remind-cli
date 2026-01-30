"""Database operations for Remind."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from remind.config import get_db_path
from remind.models import PriorityLevel, Reminder

Base = declarative_base()


class ReminderModel(Base):
    """SQLAlchemy ORM model for reminders."""

    __tablename__ = "reminders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    text = Column(String(1000), nullable=False)
    due_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    done_at = Column(DateTime, nullable=True)
    priority = Column(String(20), nullable=False, default="medium")
    project_context = Column(String(500), nullable=True)
    ai_suggested_text = Column(Text, nullable=True)

    def to_pydantic(self) -> Reminder:
        """Convert ORM model to Pydantic model."""
        return Reminder(
            id=self.id,
            text=self.text,
            due_at=self.due_at,
            created_at=self.created_at,
            done_at=self.done_at,
            priority=PriorityLevel(self.priority),
            project_context=self.project_context,
            ai_suggested_text=self.ai_suggested_text,
        )


class Database:
    """Database manager for Remind."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection."""
        if db_path is None:
            db_path = get_db_path()

        self.db_path = db_path
        connection_string = f"sqlite:///{db_path}"

        # For testing, use in-memory DB
        if str(db_path) == ":memory:":
            self.engine = create_engine(
                "sqlite:///:memory:",
                connect_args={"check_same_thread": False},
                poolclass=StaticPool,
            )
        else:
            self.engine = create_engine(connection_string)

        Base.metadata.create_all(self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)
        self._init_schema_version()

    def _init_schema_version(self) -> None:
        """Initialize schema version tracking."""
        # Simple version 1 schema - no migrations needed yet
        pass

    def add_reminder(
        self,
        text: str,
        due_at: datetime,
        priority: PriorityLevel = PriorityLevel.MEDIUM,
        project_context: Optional[str] = None,
        ai_suggested_text: Optional[str] = None,
    ) -> Reminder:
        """Add a new reminder to the database."""
        session = self.SessionLocal()
        try:
            reminder = ReminderModel(
                text=text,
                due_at=due_at,
                priority=priority.value,
                project_context=project_context,
                ai_suggested_text=ai_suggested_text,
            )
            session.add(reminder)
            session.commit()
            session.refresh(reminder)
            return reminder.to_pydantic()
        finally:
            session.close()

    def get_reminder(self, reminder_id: int) -> Optional[Reminder]:
        """Get a single reminder by ID."""
        session = self.SessionLocal()
        try:
            reminder = session.query(ReminderModel).filter_by(id=reminder_id).first()
            return reminder.to_pydantic() if reminder else None
        finally:
            session.close()

    def list_active_reminders(self) -> list[Reminder]:
        """List all active (not done) reminders, sorted by due date."""
        session = self.SessionLocal()
        try:
            reminders = (
                session.query(ReminderModel)
                .filter(ReminderModel.done_at.is_(None))
                .order_by(ReminderModel.due_at)
                .all()
            )
            return [r.to_pydantic() for r in reminders]
        finally:
            session.close()

    def list_all_reminders(self) -> list[Reminder]:
        """List all reminders, including done ones."""
        session = self.SessionLocal()
        try:
            reminders = (
                session.query(ReminderModel).order_by(ReminderModel.due_at).all()
            )
            return [r.to_pydantic() for r in reminders]
        finally:
            session.close()

    def mark_done(self, reminder_id: int) -> Optional[Reminder]:
        """Mark a reminder as done (soft delete)."""
        session = self.SessionLocal()
        try:
            reminder = session.query(ReminderModel).filter_by(id=reminder_id).first()
            if reminder:
                reminder.done_at = datetime.now(timezone.utc)
                session.commit()
                session.refresh(reminder)
                return reminder.to_pydantic()
            return None
        finally:
            session.close()

    def delete_reminder(self, reminder_id: int) -> bool:
        """Delete a reminder permanently."""
        session = self.SessionLocal()
        try:
            reminder = session.query(ReminderModel).filter_by(id=reminder_id).first()
            if reminder:
                session.delete(reminder)
                session.commit()
                return True
            return False
        finally:
            session.close()

    def search_reminders(self, query: str) -> list[Reminder]:
        """Search reminders by text content."""
        session = self.SessionLocal()
        try:
            search_pattern = f"%{query}%"
            reminders = (
                session.query(ReminderModel)
                .filter(ReminderModel.text.ilike(search_pattern))
                .order_by(ReminderModel.due_at)
                .all()
            )
            return [r.to_pydantic() for r in reminders]
        finally:
            session.close()

    def get_due_reminders(self, now: datetime) -> list[Reminder]:
        """Get all reminders that are due (and not done)."""
        session = self.SessionLocal()
        try:
            reminders = (
                session.query(ReminderModel)
                .filter(ReminderModel.done_at.is_(None))
                .filter(ReminderModel.due_at <= now)
                .order_by(ReminderModel.due_at)
                .all()
            )
            return [r.to_pydantic() for r in reminders]
        finally:
            session.close()

    def close(self) -> None:
        """Close database connection."""
        self.engine.dispose()
