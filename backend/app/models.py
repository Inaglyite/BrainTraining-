from __future__ import annotations

from sqlalchemy import (
    Boolean,
    Column,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    user_id = Column(String, primary_key=True)
    password_hash = Column(String, nullable=False)
    birthday = Column(String, nullable=False)
    role = Column(String, nullable=False)
    first_test_completed = Column(Integer, nullable=False, default=0)
    n_back_level = Column(Integer, nullable=False, default=2)
    created_at = Column(Float, nullable=False)
    updated_at = Column(Float, nullable=False)


class GameSession(Base):
    __tablename__ = "game_sessions"

    session_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    game_type = Column(String, nullable=False)
    difficulty_level = Column(Float, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    started_at = Column(Float, nullable=False)
    status = Column(String, nullable=False, default="active")
    score = Column(Integer, nullable=False, default=0)
    consecutive_errors = Column(Integer, nullable=False, default=0)
    last_attempt_index = Column(Integer, nullable=False, default=-1)
    accuracy = Column(Float, nullable=True)
    game_duration = Column(Integer, nullable=True)
    updated_at = Column(Float, nullable=False)

    __table_args__ = (
        Index("idx_sessions_user", "user_id"),
        Index("idx_sessions_user_game", "user_id", "game_type"),
    )


class GameInteraction(Base):
    __tablename__ = "game_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String, ForeignKey("game_sessions.session_id"), nullable=False, index=True)
    user_id = Column(String, nullable=False)
    game_type = Column(String, nullable=False)
    difficulty_level = Column(Float, nullable=False)
    attempt_index = Column(Integer, nullable=False)
    correct = Column(Integer, nullable=False)
    response_time = Column(Float, nullable=False)
    consecutive_errors = Column(Integer, nullable=False)
    total_attempted = Column(Integer, nullable=False)
    skill_opportunities = Column(Integer, nullable=False)
    time_since_last_same_game = Column(Float, nullable=True)
    help_used = Column(Integer, nullable=True)
    skip_used = Column(Integer, nullable=True)
    gesture = Column(String, nullable=True)
    created_at = Column(Float, nullable=False)

    __table_args__ = (
        Index("idx_interactions_user", "user_id"),
        Index("idx_interactions_game", "game_type"),
        Index("idx_interactions_user_attempt", "user_id", "attempt_index"),
        Index("idx_interactions_user_game", "user_id", "game_type"),
        Index("idx_interactions_game_difficulty", "game_type", "difficulty_level"),
    )


class UserGameDifficulty(Base):
    __tablename__ = "user_game_difficulties"

    user_id = Column(String, ForeignKey("users.user_id"), primary_key=True)
    game_type = Column(String, primary_key=True)
    current_difficulty = Column(Float, nullable=False)
    last_predicted_p = Column(Float, nullable=True)
    last_confidence = Column(Float, nullable=True)
    last_action = Column(String, nullable=True)
    updated_at = Column(Float, nullable=False)

    __table_args__ = (
        Index("idx_user_game_difficulties_user", "user_id"),
    )


class PersistentGameSession(Base):
    """Stores in-progress game session state so it survives server restarts."""
    __tablename__ = "persistent_game_sessions"

    session_id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False, index=True)
    game = Column(String, nullable=False)
    started_at = Column(Float, nullable=False)
    duration_seconds = Column(Integer, nullable=False)
    difficulty_level = Column(Float, nullable=False)
    score = Column(Integer, nullable=False, default=0)
    attempt_index = Column(Integer, nullable=False, default=0)
    consecutive_errors = Column(Integer, nullable=False, default=0)
    last_action_at = Column(Float, nullable=False, default=0)
    time_since_last_same_game = Column(Float, nullable=True)
    box_count = Column(Integer, nullable=True)
    current_question = Column(String, nullable=True)
    current_answer = Column(Integer, nullable=True)
    n_back_level = Column(Integer, nullable=True)
    suanshi_total_questions = Column(Integer, nullable=True)
    suanshi_presented_questions = Column(Integer, nullable=False, default=0)
    suanshi_answered_questions = Column(Integer, nullable=False, default=0)
    suanshi_target_answer = Column(Integer, nullable=True)
    suanshi_can_answer = Column(Boolean, nullable=False, default=False)
    suanshi_recent_answers = Column(Text, nullable=True)
    rps_instruction = Column(String, nullable=True)
    rps_cpu_action = Column(String, nullable=True)
    correct_count = Column(Integer, nullable=False, default=0)
    judged_attempts = Column(Integer, nullable=False, default=0)
    answer_time_limit_ms = Column(Integer, nullable=False, default=3000)
    answer_deadline_at = Column(Float, nullable=False, default=0)
