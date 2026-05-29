from __future__ import annotations

import datetime
import json
import logging
import time
from dataclasses import dataclass

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.models import (
    Base,
    GameInteraction,
    GameSession,
    PersistentGameSession,
    User,
    UserGameDifficulty,
)

logger = logging.getLogger(__name__)


@dataclass
class UserCounters:
    total_attempted: int
    skill_opportunities: int


class DBStore:
    def __init__(self, database_url: str = "") -> None:
        url = database_url or settings.database_url
        is_sqlite = "sqlite" in url

        connect_args: dict = {}
        if is_sqlite:
            connect_args["check_same_thread"] = False

        self._engine = create_engine(url, connect_args=connect_args, echo=False)
        self._SessionLocal = sessionmaker(bind=self._engine, autoflush=False)
        self._is_sqlite = is_sqlite
        self._init_db()

    def _init_db(self) -> None:
        Base.metadata.create_all(self._engine)
        logger.info("Database tables ensured (dialect: %s)", "sqlite" if self._is_sqlite else "postgresql")

    def _session(self) -> Session:
        return self._SessionLocal()

    # ── users ──────────────────────────────────────────────

    def create_user(self, user_id: str, password_hash: str, birthday: str, role: str) -> None:
        now = time.time()
        with self._session() as s:
            s.add(User(user_id=user_id, password_hash=password_hash, birthday=birthday,
                        role=role, created_at=now, updated_at=now))
            s.commit()

    def get_user(self, user_id: str) -> dict[str, object] | None:
        with self._session() as s:
            row = s.get(User, user_id)
        if row is None:
            return None
        return {
            "user_id": row.user_id,
            "password_hash": row.password_hash,
            "birthday": row.birthday,
            "role": row.role,
            "first_test_completed": bool(row.first_test_completed),
            "n_back_level": row.n_back_level,
            "created_at": row.created_at,
            "updated_at": row.updated_at,
        }

    def update_user_first_test_completed(self, user_id: str, completed: bool) -> None:
        with self._session() as s:
            u = s.get(User, user_id)
            if u:
                u.first_test_completed = 1 if completed else 0
                u.updated_at = time.time()
                s.commit()

    def get_user_n_back_level(self, user_id: str) -> int:
        with self._session() as s:
            u = s.get(User, user_id)
        return u.n_back_level if u else 2

    def update_user_n_back_level(self, user_id: str, n_back_level: int) -> None:
        with self._session() as s:
            u = s.get(User, user_id)
            if u:
                u.n_back_level = n_back_level
                u.updated_at = time.time()
                s.commit()

    # ── sessions ───────────────────────────────────────────

    def create_session(self, session_id: str, user_id: str, game_type: str,
                       difficulty_level: float, duration_seconds: int,
                       started_at: float) -> None:
        now = time.time()
        with self._session() as s:
            s.add(GameSession(
                session_id=session_id, user_id=user_id, game_type=game_type,
                difficulty_level=difficulty_level, duration_seconds=duration_seconds,
                started_at=started_at, updated_at=now,
            ))
            s.commit()

    def update_session(self, session_id: str, score: int, difficulty_level: float,
                       consecutive_errors: int, last_attempt_index: int, status: str,
                       accuracy: float | None = None, game_duration: int | None = None) -> None:
        with self._session() as s:
            gs = s.get(GameSession, session_id)
            if gs:
                gs.score = score
                gs.difficulty_level = difficulty_level
                gs.consecutive_errors = consecutive_errors
                gs.last_attempt_index = last_attempt_index
                gs.status = status
                gs.accuracy = accuracy
                gs.game_duration = game_duration
                gs.updated_at = time.time()
                s.commit()

    # ── interactions ───────────────────────────────────────

    def get_user_counters(self, user_id: str, game_type: str) -> UserCounters:
        with self._session() as s:
            total = s.query(GameInteraction).filter(
                GameInteraction.user_id == user_id,
            ).count()
            skill = s.query(GameInteraction).filter(
                GameInteraction.user_id == user_id,
                GameInteraction.game_type == game_type,
            ).count()
        return UserCounters(total_attempted=total, skill_opportunities=skill)

    def get_time_since_last_same_game(self, user_id: str, game_type: str,
                                       now_ts: float) -> float | None:
        with self._session() as s:
            row = s.query(GameSession.started_at).filter(
                GameSession.user_id == user_id,
                GameSession.game_type == game_type,
            ).order_by(GameSession.started_at.desc()).first()
        if row is None:
            return None
        return max(0.0, now_ts - row[0])

    def get_today_play_time(self, user_id: str, game_type: str) -> int:
        now = datetime.datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        with self._session() as s:
            result = s.query(GameSession.duration_seconds).filter(
                GameSession.user_id == user_id,
                GameSession.game_type == game_type,
                GameSession.started_at >= start_of_day,
            ).all()
        return int(sum(r[0] for r in result))

    def get_today_session_count(self, user_id: str, game_type: str) -> int:
        now = datetime.datetime.now()
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0).timestamp()
        with self._session() as s:
            return s.query(GameSession).filter(
                GameSession.user_id == user_id,
                GameSession.game_type == game_type,
                GameSession.started_at >= start_of_day,
            ).count()

    # ── difficulties ───────────────────────────────────────

    def get_user_game_difficulty(self, user_id: str, game_type: str) -> float | None:
        with self._session() as s:
            row = s.get(UserGameDifficulty, (user_id, game_type))
        return float(row.current_difficulty) if row else None

    def upsert_user_game_difficulty(self, user_id: str, game_type: str,
                                     current_difficulty: float,
                                     last_predicted_p: float | None,
                                     last_confidence: float | None,
                                     last_action: str | None) -> None:
        now = time.time()
        with self._session() as s:
            d = s.get(UserGameDifficulty, (user_id, game_type))
            if d:
                d.current_difficulty = current_difficulty
                d.last_predicted_p = last_predicted_p
                d.last_confidence = last_confidence
                d.last_action = last_action
                d.updated_at = now
            else:
                s.add(UserGameDifficulty(
                    user_id=user_id, game_type=game_type,
                    current_difficulty=current_difficulty,
                    last_predicted_p=last_predicted_p,
                    last_confidence=last_confidence,
                    last_action=last_action,
                    updated_at=now,
                ))
            s.commit()

    def list_recent_interactions(self, user_id: str, game_type: str,
                                  limit: int = 20) -> list[dict[str, object]]:
        with self._session() as s:
            rows = s.query(GameInteraction).filter(
                GameInteraction.user_id == user_id,
                GameInteraction.game_type == game_type,
            ).order_by(GameInteraction.created_at.desc()).limit(limit).all()

        return [_interaction_to_dict(r) for r in rows]

    def insert_interaction(self, session_id: str, user_id: str, game_type: str,
                           difficulty_level: float, attempt_index: int, correct: bool,
                           response_time: float, consecutive_errors: int,
                           total_attempted: int, skill_opportunities: int,
                           time_since_last_same_game: float | None,
                           gesture: str) -> None:
        with self._session() as s:
            s.add(GameInteraction(
                session_id=session_id, user_id=user_id, game_type=game_type,
                difficulty_level=difficulty_level, attempt_index=attempt_index,
                correct=1 if correct else 0, response_time=response_time,
                consecutive_errors=consecutive_errors,
                total_attempted=total_attempted,
                skill_opportunities=skill_opportunities,
                time_since_last_same_game=time_since_last_same_game,
                help_used=0, skip_used=0, gesture=gesture,
                created_at=time.time(),
            ))
            s.commit()

    def list_interactions(self, session_id: str, game_type: str | None = None,
                          user_id: str | None = None,
                          limit: int = 200) -> list[dict[str, object]]:
        with self._session() as s:
            q = s.query(GameInteraction).filter(GameInteraction.session_id == session_id)
            if game_type:
                q = q.filter(GameInteraction.game_type == game_type)
            if user_id:
                q = q.filter(GameInteraction.user_id == user_id)
            rows = q.order_by(GameInteraction.attempt_index.asc()).limit(limit).all()
        return [_interaction_to_dict(r) for r in rows]

    # ── summaries ──────────────────────────────────────────

    @staticmethod
    def _day_bounds(date_str: str | None = None) -> tuple[float, float, str]:
        if date_str:
            day = datetime.date.fromisoformat(date_str)
        else:
            day = datetime.datetime.now().date()
        start = datetime.datetime.combine(day, datetime.time.min).timestamp()
        end = start + 86400
        return start, end, day.isoformat()

    @staticmethod
    def _period_bounds(period: str, anchor_date: str | None = None) -> tuple[float, float, str, str, str]:
        if anchor_date:
            day = datetime.date.fromisoformat(anchor_date)
        else:
            day = datetime.datetime.now().date()
        if period == "daily":
            start_day = day
            end_day = day + datetime.timedelta(days=1)
        elif period == "monthly":
            start_day = day.replace(day=1)
            if start_day.month == 12:
                end_day = start_day.replace(year=start_day.year + 1, month=1, day=1)
            else:
                end_day = start_day.replace(month=start_day.month + 1, day=1)
        elif period == "quarterly":
            qm = ((day.month - 1) // 3) * 3 + 1
            start_day = day.replace(month=qm, day=1)
            if qm == 10:
                end_day = start_day.replace(year=start_day.year + 1, month=1, day=1)
            else:
                end_day = start_day.replace(month=qm + 3, day=1)
        else:
            raise ValueError("period must be daily, monthly, or quarterly")
        start_ts = datetime.datetime.combine(start_day, datetime.time.min).timestamp()
        end_ts = datetime.datetime.combine(end_day, datetime.time.min).timestamp()
        return start_ts, end_ts, day.isoformat(), start_day.isoformat(), (end_day - datetime.timedelta(days=1)).isoformat()

    def get_daily_summary(self, user_id: str, date_str: str | None = None) -> dict[str, object]:
        start_ts, end_ts, normalized_date = self._day_bounds(date_str)
        result = self._build_summary(user_id, start_ts, end_ts, normalized_date, normalized_date)
        result["date"] = normalized_date
        result["shu_xiang_remaining_rounds"] = max(0, 5 - self.get_today_session_count(user_id, "shu-xiang"))
        return result

    def get_period_summary(self, user_id: str, period: str,
                            anchor_date: str | None = None) -> dict[str, object]:
        start_ts, end_ts, normalized_anchor, period_start, period_end = self._period_bounds(period, anchor_date)
        result = self._build_summary(user_id, start_ts, end_ts, normalized_anchor, period_start, period_end)
        result["period"] = period
        return result

    def _build_summary(self, user_id: str, start_ts: float, end_ts: float,
                        anchor_date: str, period_start: str, period_end: str = "") -> dict[str, object]:
        period_name = period_end or period_start
        with self._session() as s:
            rows = s.query(GameSession).filter(
                GameSession.user_id == user_id,
                GameSession.started_at >= start_ts,
                GameSession.started_at < end_ts,
            ).order_by(GameSession.started_at.asc()).all()

        sessions: list[dict[str, object]] = []
        total_duration = 0
        shu = suanshi = rps = 0
        accuracies: list[float] = []

        for row in rows:
            dur = int(row.game_duration) if row.game_duration is not None else int(row.duration_seconds)
            total_duration += max(0, dur)
            gt = row.game_type
            if gt == "shu-xiang":
                shu += 1
            elif gt == "suan-shi":
                suanshi += 1
            elif gt == "rps":
                rps += 1
            if row.accuracy is not None:
                accuracies.append(float(row.accuracy))
            sessions.append({
                "session_id": row.session_id,
                "game_type": gt,
                "started_at": float(row.started_at),
                "duration_seconds": max(0, dur),
                "score": int(row.score),
                "accuracy": float(row.accuracy) if row.accuracy is not None else None,
                "status": row.status,
            })

        avg_acc = (sum(accuracies) / len(accuracies)) if accuracies else None
        result: dict[str, object] = {
            "user_id": user_id,
            "period": "custom",
            "anchor_date": anchor_date,
            "period_start": period_start,
            "period_end": period_name,
            "total_duration_seconds": total_duration,
            "total_sessions": len(sessions),
            "shu_xiang_sessions": shu,
            "suan_shi_sessions": suanshi,
            "rps_sessions": rps,
            "average_accuracy": avg_acc,
            "sessions": sessions,
        }
        return result

    # ── persistent game sessions ───────────────────────────

    SESSION_FIELDS = [
        "session_id", "user_id", "game", "started_at", "duration_seconds",
        "difficulty_level", "score", "attempt_index", "consecutive_errors",
        "last_action_at", "time_since_last_same_game", "box_count",
        "current_question", "current_answer", "n_back_level",
        "suanshi_total_questions", "suanshi_presented_questions",
        "suanshi_answered_questions", "suanshi_target_answer",
        "suanshi_can_answer", "suanshi_recent_answers",
        "rps_instruction", "rps_cpu_action", "correct_count",
        "judged_attempts", "answer_time_limit_ms", "answer_deadline_at",
    ]

    def save_game_state(self, state: dict[str, object]) -> None:
        with self._session() as s:
            existing = s.get(PersistentGameSession, state["session_id"])
            if existing:
                for k, v in state.items():
                    if k == "suanshi_recent_answers" and isinstance(v, list):
                        v = json.dumps(v)
                    if hasattr(existing, k):
                        setattr(existing, k, v)
            else:
                kwargs = dict(state)
                if "suanshi_recent_answers" in kwargs and isinstance(kwargs["suanshi_recent_answers"], list):
                    kwargs["suanshi_recent_answers"] = json.dumps(kwargs["suanshi_recent_answers"])
                s.add(PersistentGameSession(**{k: kwargs[k] for k in self.SESSION_FIELDS if k in kwargs}))
            s.commit()

    def load_game_state(self, session_id: str) -> dict[str, object] | None:
        with self._session() as s:
            row = s.get(PersistentGameSession, session_id)
        if row is None:
            return None
        d = {c.name: getattr(row, c.name) for c in PersistentGameSession.__table__.columns}
        if d.get("suanshi_recent_answers") and isinstance(d["suanshi_recent_answers"], str):
            d["suanshi_recent_answers"] = json.loads(d["suanshi_recent_answers"])
        return d

    def delete_game_state(self, session_id: str) -> None:
        with self._session() as s:
            row = s.get(PersistentGameSession, session_id)
            if row:
                s.delete(row)
                s.commit()

    def list_active_sessions(self, user_id: str) -> list[dict[str, object]]:
        with self._session() as s:
            rows = s.query(PersistentGameSession).filter(
                PersistentGameSession.user_id == user_id,
            ).all()
        result: list[dict[str, object]] = []
        for row in rows:
            d = {c.name: getattr(row, c.name) for c in PersistentGameSession.__table__.columns}
            if d.get("suanshi_recent_answers") and isinstance(d["suanshi_recent_answers"], str):
                d["suanshi_recent_answers"] = json.loads(d["suanshi_recent_answers"])
            result.append(d)
        return result


def _interaction_to_dict(row: GameInteraction) -> dict[str, object]:
    return {
        "id": row.id,
        "session_id": row.session_id,
        "user_id": row.user_id,
        "game_type": row.game_type,
        "difficulty_level": float(row.difficulty_level),
        "attempt_index": row.attempt_index,
        "correct": bool(row.correct),
        "response_time": float(row.response_time),
        "consecutive_errors": row.consecutive_errors,
        "total_attempted": row.total_attempted,
        "skill_opportunities": row.skill_opportunities,
        "time_since_last_same_game": row.time_since_last_same_game,
        "help_used": bool(row.help_used) if row.help_used is not None else None,
        "skip_used": bool(row.skip_used) if row.skip_used is not None else None,
        "gesture": row.gesture,
        "created_at": float(row.created_at),
    }


# Global instance - replaces sqlite_store
db_store = DBStore()
