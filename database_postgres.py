"""
Database Models & Engine

SQLAlchemy ORM models and database engine setup.
Supports both SQLite (for development/testing) and PostgreSQL (for production).
Automatically handles Foreign Keys for SQLite and Connection Pooling for PostgreSQL.
"""

import os
from datetime import datetime
from contextlib import contextmanager

from sqlalchemy import (
    create_engine,
    Column,
    String,
    Float,
    Integer,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    CheckConstraint,
    UniqueConstraint,
    Index,
    event,
    engine,
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
    sessionmaker,
    scoped_session,
    Session,
)
from sqlalchemy.pool import QueuePool, StaticPool


# ─── Database Configuration ───────────────────────────────────────────────────
# Defaults to SQLite if DATABASE_URL is not set or starts with 'sqlite'
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///resume_screener.db"
)

# Determine if we are using SQLite or PostgreSQL
IS_SQLITE = DATABASE_URL.startswith("sqlite")

# Connection pool settings (Only applies to PostgreSQL)
POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "1800"))  # 30 minutes


# ─── Base Model ───────────────────────────────────────────────────────────────
Base = declarative_base()


# ─── ORM Models ───────────────────────────────────────────────────────────────

class User(Base):
    """User model for authentication and authorization."""
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
        CheckConstraint(
            "role IN ('admin', 'recruiter')",
            name="chk_users_role"
        ),
        Index("idx_users_username", "username"),
        Index("idx_users_email", "email"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="recruiter")
    name = Column(String(200), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    def to_dict(self, include_password=False):
        """Convert user to dictionary (excludes password by default)."""
        data = {
            "id": self.id,
            "user_id": self.user_id,
            "username": self.username,
            "role": self.role,
            "name": self.name,
            "email": self.email,
            "created_at": self.created_at,
            "last_login": self.last_login,
            "is_active": self.is_active,
        }
        if include_password:
            data["password_hash"] = self.password_hash
        return data


class Job(Base):
    """Job description model."""
    __tablename__ = "jobs"
    __table_args__ = (
        UniqueConstraint("job_id", name="uq_jobs_job_id"),
        Index("idx_jobs_job_id", "job_id"),
        Index("idx_jobs_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(36), unique=True, nullable=False, index=True)
    job_title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    required_skills = Column(Text, nullable=True)  # Stored as JSON string
    experience_required = Column(Integer, nullable=True, default=0)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rankings = relationship("Ranking", back_populates="job", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert job to dictionary."""
        import json
        return {
            "id": self.id,
            "job_id": self.job_id,
            "job_title": self.job_title,
            "description": self.description,
            "required_skills": json.loads(self.required_skills) if self.required_skills else [],
            "experience_required": self.experience_required,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class Candidate(Base):
    """Candidate resume data model."""
    __tablename__ = "candidates"
    __table_args__ = (
        UniqueConstraint("candidate_id", name="uq_candidates_candidate_id"),
        Index("idx_candidates_candidate_id", "candidate_id"),
        Index("idx_candidates_email", "email"),
        Index("idx_candidates_name", "name"),
        Index("idx_candidates_created_at", "created_at"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(String(36), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    skills = Column(Text, nullable=True)  # Stored as JSON string
    education = Column(Text, nullable=True)  # Stored as JSON string
    experience = Column(Text, nullable=True)  # Stored as JSON string
    years_of_experience = Column(Integer, nullable=True, default=0)
    resume_text = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    rankings = relationship("Ranking", back_populates="candidate", cascade="all, delete-orphan")

    def to_dict(self):
        """Convert candidate to dictionary."""
        import json
        return {
            "id": self.id,
            "candidate_id": self.candidate_id,
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "skills": json.loads(self.skills) if self.skills else [],
            "education": json.loads(self.education) if self.education else [],
            "experience": json.loads(self.experience) if self.experience else [],
            "years_of_experience": self.years_of_experience,
            "resume_text": self.resume_text,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class Ranking(Base):
    """Ranking/screener results model."""
    __tablename__ = "rankings"
    __table_args__ = (
        UniqueConstraint("ranking_id", name="uq_rankings_ranking_id"),
        CheckConstraint(
            "score >= 0 AND score <= 1",
            name="chk_rankings_score"
        ),
        Index("idx_rankings_ranking_id", "ranking_id"),
        Index("idx_rankings_job_id", "job_id"),
        Index("idx_rankings_candidate_id", "candidate_id"),
        Index("idx_rankings_score", "score"),
        Index("idx_rankings_job_score", "job_id", "score"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ranking_id = Column(String(36), unique=True, nullable=False, index=True)
    job_id = Column(String(36), ForeignKey("jobs.job_id", ondelete="CASCADE"), nullable=False)
    candidate_id = Column(String(36), ForeignKey("candidates.candidate_id", ondelete="CASCADE"), nullable=False)
    score = Column(Float, nullable=False)
    skills_matched = Column(Text, nullable=True)  # Stored as JSON string
    skills_missing = Column(Text, nullable=True)  # Stored as JSON string
    rank = Column(Integer, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    job = relationship("Job", back_populates="rankings")
    candidate = relationship("Candidate", back_populates="rankings")

    def to_dict(self):
        """Convert ranking to dictionary."""
        import json
        return {
            "id": self.id,
            "ranking_id": self.ranking_id,
            "job_id": self.job_id,
            "candidate_id": self.candidate_id,
            "score": self.score,
            "skills_matched": json.loads(self.skills_matched) if self.skills_matched else [],
            "skills_missing": json.loads(self.skills_missing) if self.skills_missing else [],
            "rank": self.rank,
            "created_at": self.created_at,
        }


# ─── Database Engine & Session Management ─────────────────────────────────────

# Global engine and session factory
_engine = None
_SessionFactory = None
ScopedSession = None


def get_engine():
    """
    Create and return SQLAlchemy engine.
    Automatically configures itself for SQLite or PostgreSQL.
    """
    global _engine
    if _engine is None:
        if IS_SQLITE:
            # SQLite Configuration
            _engine = create_engine(
                DATABASE_URL,
                poolclass=StaticPool,
                connect_args={"check_same_thread": False},
                echo=False,
            )
            
            # Enable Foreign Key support in SQLite (disabled by default)
            @event.listens_for(_engine, "connect")
            def set_sqlite_pragma(dbapi_connection, connection_record):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
                
        else:
            # PostgreSQL Configuration
            _engine = create_engine(
                DATABASE_URL,
                poolclass=QueuePool,
                pool_size=POOL_SIZE,
                max_overflow=MAX_OVERFLOW,
                pool_timeout=POOL_TIMEOUT,
                pool_recycle=POOL_RECYCLE,
                echo=False,
            )
    return _engine


def get_session_factory():
    """
    Create and return session factory.
    Creates factory once and reuses it.
    """
    global _SessionFactory
    if _SessionFactory is None:
        engine = get_engine()
        _SessionFactory = sessionmaker(bind=engine)
    return _SessionFactory


def get_scoped_session():
    """
    Get a thread-scoped session.
    Recommended for web applications (like Streamlit).
    """
    global ScopedSession
    if ScopedSession is None:
        factory = get_session_factory()
        ScopedSession = scoped_session(factory)
    return ScopedSession()


def get_session() -> Session:
    """
    Get a new database session.
    Returns a fresh session each time (caller must close it).
    """
    factory = get_session_factory()
    return factory()


@contextmanager
def session_scope():
    """
    Provide a transactional scope around a series of operations.
    This is the recommended way to handle database sessions.

    Usage:
        with session_scope() as session:
            session.add(user)
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db():
    """
    Initialize database: create all tables if they don't exist.
    Safe to call multiple times (won't drop existing data).
    """
    engine = get_engine()
    Base.metadata.create_all(engine)


def drop_db():
    """
    Drop all tables (DANGEROUS - use only for testing/migration).
    """
    engine = get_engine()
    Base.metadata.drop_all(engine)


def check_connection() -> bool:
    """
    Test database connectivity.
    Returns True if connection is successful, False otherwise.
    """
    try:
        from sqlalchemy import text
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
