from __future__ import annotations

import json
import random
import time
import uuid
from dataclasses import dataclass, field
import math

from app.schemas.vision import DifficultyRecommendation, GameName, SessionState
from app.services.difficulty_service import difficulty_service
from app.services.sqlite_store import sqlite_store


@dataclass
class GameSession:
    id: str
    user_id: str
    game: GameName
    started_at: float
    duration_seconds: int
    difficulty_level: float
    score: int = 0
    attempt_index: int = 0
    consecutive_errors: int = 0
    last_action_at: float = 0.0
    time_since_last_same_game: float | None = None
    box_count: int | None = None
    current_question: str | None = None
    current_answer: int | None = None
    n_back_level: int | None = None
    suanshi_total_questions: int | None = None
    suanshi_presented_questions: int = 0
    suanshi_answered_questions: int = 0
    suanshi_target_answer: int | None = None
    suanshi_can_answer: bool = False
    suanshi_recent_answers: list[int] = field(default_factory=list)
    rps_instruction: str | None = None
    rps_cpu_action: str | None = None
    correct_count: int = 0
    judged_attempts: int = 0
    answer_time_limit_ms: int = 3000
    answer_deadline_at: float = 0.0
    difficulty_recommendation: DifficultyRecommendation | None = None


class GameEngine:
    def __init__(self) -> None:
        self._sessions: dict[str, GameSession] = {}
        self._restore_sessions()

    def _session_to_dict(self, s: GameSession) -> dict[str, object]:
        return {
            "session_id": s.id,
            "user_id": s.user_id,
            "game": s.game,
            "started_at": s.started_at,
            "duration_seconds": s.duration_seconds,
            "difficulty_level": s.difficulty_level,
            "score": s.score,
            "attempt_index": s.attempt_index,
            "consecutive_errors": s.consecutive_errors,
            "last_action_at": s.last_action_at,
            "time_since_last_same_game": s.time_since_last_same_game,
            "box_count": s.box_count,
            "current_question": s.current_question,
            "current_answer": s.current_answer,
            "n_back_level": s.n_back_level,
            "suanshi_total_questions": s.suanshi_total_questions,
            "suanshi_presented_questions": s.suanshi_presented_questions,
            "suanshi_answered_questions": s.suanshi_answered_questions,
            "suanshi_target_answer": s.suanshi_target_answer,
            "suanshi_can_answer": s.suanshi_can_answer,
            "suanshi_recent_answers": s.suanshi_recent_answers,
            "rps_instruction": s.rps_instruction,
            "rps_cpu_action": s.rps_cpu_action,
            "correct_count": s.correct_count,
            "judged_attempts": s.judged_attempts,
            "answer_time_limit_ms": s.answer_time_limit_ms,
            "answer_deadline_at": s.answer_deadline_at,
        }

    @staticmethod
    def _dict_to_session(d: dict[str, object]) -> GameSession:
        recent = d.get("suanshi_recent_answers", [])
        if isinstance(recent, str):
            recent = json.loads(recent)
        return GameSession(
            id=str(d["session_id"]),
            user_id=str(d["user_id"]),
            game=str(d["game"]),
            started_at=float(d["started_at"]),
            duration_seconds=int(d["duration_seconds"]),
            difficulty_level=float(d["difficulty_level"]),
            score=int(d.get("score", 0)),
            attempt_index=int(d.get("attempt_index", 0)),
            consecutive_errors=int(d.get("consecutive_errors", 0)),
            last_action_at=float(d.get("last_action_at", 0)),
            time_since_last_same_game=float(d["time_since_last_same_game"]) if d.get("time_since_last_same_game") is not None else None,
            box_count=int(d["box_count"]) if d.get("box_count") is not None else None,
            current_question=str(d["current_question"]) if d.get("current_question") is not None else None,
            current_answer=int(d["current_answer"]) if d.get("current_answer") is not None else None,
            n_back_level=int(d["n_back_level"]) if d.get("n_back_level") is not None else None,
            suanshi_total_questions=int(d["suanshi_total_questions"]) if d.get("suanshi_total_questions") is not None else None,
            suanshi_presented_questions=int(d.get("suanshi_presented_questions", 0)),
            suanshi_answered_questions=int(d.get("suanshi_answered_questions", 0)),
            suanshi_target_answer=int(d["suanshi_target_answer"]) if d.get("suanshi_target_answer") is not None else None,
            suanshi_can_answer=bool(d.get("suanshi_can_answer", False)),
            suanshi_recent_answers=list(recent) if recent else [],
            rps_instruction=str(d["rps_instruction"]) if d.get("rps_instruction") is not None else None,
            rps_cpu_action=str(d["rps_cpu_action"]) if d.get("rps_cpu_action") is not None else None,
            correct_count=int(d.get("correct_count", 0)),
            judged_attempts=int(d.get("judged_attempts", 0)),
            answer_time_limit_ms=int(d.get("answer_time_limit_ms", 3000)),
            answer_deadline_at=float(d.get("answer_deadline_at", 0)),
        )

    def _restore_sessions(self) -> None:
        try:
            from app.services.db_store import db_store
            now = time.time()
            # Only restore sessions that haven't expired (add 30s grace)
            for row in db_store.list_active_sessions("*"):
                deadline = float(row.get("answer_deadline_at", 0))
                started = float(row.get("started_at", 0))
                duration = int(row.get("duration_seconds", 0))
                if started + duration + 30 > now:
                    session = self._dict_to_session(row)
                    self._sessions[session.id] = session
        except Exception:
            pass

    def _persist_session(self, session: GameSession) -> None:
        try:
            from app.services.db_store import db_store
            db_store.save_game_state(self._session_to_dict(session))
        except Exception:
            pass

    def _delete_persisted_session(self, session_id: str) -> None:
        try:
            from app.services.db_store import db_store
            db_store.delete_game_state(session_id)
        except Exception:
            pass

    @staticmethod
    def _new_question_with_answer() -> tuple[str, int]:
        # Keep both operands and answer strictly in 1-9.
        answer = random.randint(2, 9)
        left = random.randint(1, answer - 1)
        right = answer - left
        return f"{left} + {right} = ?", answer

    @staticmethod
    def _n_back_from_difficulty(difficulty_level: float) -> int:
        # n.0 / n.5 / n.7 中 n 对应回溯层级。
        return max(2, int(math.floor(difficulty_level)))

    @staticmethod
    def _suanshi_total_questions(n_back_level: int) -> int:
        if n_back_level == 2:
            return 20
        if n_back_level == 3:
            return 21
        return 24

    def _elapsed(self, session: GameSession) -> int:
        return max(0, int(time.time() - session.started_at))

    @staticmethod
    def _new_rps_state() -> tuple[str, str]:
        cpu_action = random.choice(["rock", "paper", "scissors"])
        instruction = random.choice(["win", "lose", "draw"])
        return instruction, cpu_action

    @staticmethod
    def _new_box_count(difficulty_level: float) -> int:
        return random.randint(1, 9)

    def _remaining(self, session: GameSession) -> int:
        elapsed = int(time.time() - session.started_at)
        return max(0, session.duration_seconds - elapsed)

    def _status(self, session: GameSession) -> str:
        if session.game == "suan-shi" and session.suanshi_total_questions is not None:
            if session.suanshi_answered_questions >= session.suanshi_total_questions:
                return "completed"
            return "active"
        return "completed" if self._remaining(session) == 0 else "active"

    def _to_state(self, session: GameSession) -> SessionState:
        answer_remaining_ms = max(0, int((session.answer_deadline_at - time.time()) * 1000))
        return SessionState(
            session_id=session.id,
            game=session.game,
            score=session.score,
            remaining_seconds=self._remaining(session),
            elapsed_seconds=self._elapsed(session),
            status=self._status(session),
            user_id=session.user_id,
            difficulty_level=round(session.difficulty_level, 2),
            attempt_index=session.attempt_index,
            consecutive_errors=session.consecutive_errors,
            current_question=session.current_question if session.game == "suan-shi" else None,
            n_back_level=session.n_back_level if session.game == "suan-shi" else None,
            suanshi_total_questions=session.suanshi_total_questions if session.game == "suan-shi" else None,
            suanshi_answered_questions=session.suanshi_answered_questions if session.game == "suan-shi" else None,
            suanshi_target_answer=session.suanshi_target_answer if session.game == "suan-shi" else None,
            suanshi_can_answer=session.suanshi_can_answer if session.game == "suan-shi" else None,
            suanshi_recent_answers=session.suanshi_recent_answers[-5:] if session.game == "suan-shi" else None,
            box_count=session.box_count if session.game == "shu-xiang" else None,
            rps_instruction=session.rps_instruction if session.game == "rps" else None, # type: ignore[arg-type]
            rps_cpu_action=session.rps_cpu_action if session.game == "rps" else None,   # type: ignore[arg-type]
            answer_time_limit_ms=session.answer_time_limit_ms,
            answer_remaining_ms=answer_remaining_ms,
            difficulty_recommendation=session.difficulty_recommendation,
        )

    @staticmethod
    def _refresh_suanshi_prompt(session: GameSession) -> None:
        total = session.suanshi_total_questions or 0
        n_val = session.n_back_level or 1
        if total <= 0:
            session.suanshi_target_answer = None
            session.suanshi_can_answer = False
            return

        if session.suanshi_presented_questions >= total and session.current_answer is None:
            available_answers = len(session.suanshi_recent_answers)
        else:
            available_answers = max(0, session.suanshi_presented_questions - n_val)

        next_answer_index = session.suanshi_answered_questions
        if next_answer_index < available_answers and next_answer_index < len(session.suanshi_recent_answers):
            session.suanshi_target_answer = session.suanshi_recent_answers[next_answer_index]
            session.suanshi_can_answer = True
        else:
            session.suanshi_target_answer = None
            session.suanshi_can_answer = False

    def create_session(self, game: GameName, duration_seconds: int, user_id: str, difficulty_level: float) -> SessionState:
        session_id = str(uuid.uuid4())
        started_at = time.time()
        difficulty_level = difficulty_service.normalize_for_game(game, difficulty_level)

        stored_difficulty = sqlite_store.get_user_game_difficulty(user_id, game)
        if stored_difficulty is not None:
            difficulty_level = difficulty_service.normalize_for_game(game, stored_difficulty)
        else:
            default_difficulty = difficulty_service.get_default_difficulty(game)
            if game == "suan-shi" and difficulty_level < default_difficulty:
                difficulty_level = default_difficulty

        answer_time_limit_ms = difficulty_service.get_answer_time_limit_ms(game, difficulty_level)
        answer_deadline_at = started_at + (answer_time_limit_ms / 1000.0)

        if game == "shu-xiang":
            today_rounds = sqlite_store.get_today_session_count(user_id, game)
            if today_rounds >= 5:
                raise ValueError("shu_xiang_daily_round_limit_exceeded")
            duration_seconds = 60

        time_since_last_same_game = sqlite_store.get_time_since_last_same_game(user_id, game, started_at)
        rps_inst, rps_cpu = self._new_rps_state() if game == "rps" else (None, None)
        n_back_level = self._n_back_from_difficulty(difficulty_level) if game == "suan-shi" else None
        first_question, first_answer = self._new_question_with_answer() if game == "suan-shi" else (None, None)
        session = GameSession(
            id=session_id,
            user_id=user_id,
            game=game,
            started_at=started_at,
            duration_seconds=duration_seconds,
            difficulty_level=difficulty_level,
            last_action_at=started_at,
            time_since_last_same_game=time_since_last_same_game,
            current_question=first_question,
            current_answer=first_answer,
            n_back_level=n_back_level,
            suanshi_total_questions=self._suanshi_total_questions(n_back_level) if n_back_level is not None else None,
            suanshi_presented_questions=1 if game == "suan-shi" else 0,
            suanshi_answered_questions=0,
            suanshi_target_answer=None,
            suanshi_can_answer=False,
            suanshi_recent_answers=[],
            box_count=self._new_box_count(difficulty_level) if game == "shu-xiang" else None,
            rps_instruction=rps_inst,
            rps_cpu_action=rps_cpu,
            correct_count=0,
            judged_attempts=0,
            answer_time_limit_ms=answer_time_limit_ms,
            answer_deadline_at=answer_deadline_at,
        )
        self._sessions[session_id] = session
        self._persist_session(session)
        sqlite_store.create_session(
            session_id=session_id,
            user_id=user_id,
            game_type=game,
            difficulty_level=difficulty_level,
            duration_seconds=duration_seconds,
            started_at=started_at,
        )
        sqlite_store.upsert_user_game_difficulty(
            user_id=user_id,
            game_type=game,
            current_difficulty=round(difficulty_level, 2),
            last_predicted_p=None,
            last_confidence=None,
            last_action="keep",
        )
        return self._to_state(session)

    def get_session(self, game: GameName, session_id: str) -> SessionState:
        session = self._sessions.get(session_id)
        if session is None:
            try:
                from app.services.db_store import db_store
                state = db_store.load_game_state(session_id)
                if state:
                    session = self._dict_to_session(state)
                    self._sessions[session_id] = session
            except Exception:
                pass
        if session is None or session.game != game:
            raise KeyError("session_not_found")
        return self._to_state(session)

    @staticmethod
    def _is_correct_gesture(game: str, gesture: str, session: GameSession) -> bool:
        if game == "shu-xiang":
            return str(gesture) == str(session.box_count)
        elif game == "rps":
            choices = ["rock", "paper", "scissors"]
            if gesture not in choices or session.rps_cpu_action not in choices:
                return False
            cpu = session.rps_cpu_action
            if session.rps_instruction == "win":
                return (gesture == "rock" and cpu == "scissors") or \
                       (gesture == "scissors" and cpu == "paper") or \
                       (gesture == "paper" and cpu == "rock")
            if session.rps_instruction == "draw":
                return gesture == cpu
            else: # lose
                return (gesture == "rock" and cpu == "paper") or \
                       (gesture == "scissors" and cpu == "rock") or \
                       (gesture == "paper" and cpu == "scissors")
        elif game == "suan-shi":
            if not session.suanshi_can_answer or session.suanshi_target_answer is None:
                return False
            return str(gesture) == str(session.suanshi_target_answer)
            
        return False

    def _advance_suanshi(self, session: GameSession) -> None:
        if session.current_answer is not None:
            session.suanshi_recent_answers.append(session.current_answer)

        total = session.suanshi_total_questions or 0
        if session.suanshi_presented_questions < total:
            next_question, next_answer = self._new_question_with_answer()
            session.current_question = next_question
            session.current_answer = next_answer
            session.suanshi_presented_questions += 1
        else:
            session.current_question = "请继续回答剩余题目"
            session.current_answer = None

        self._refresh_suanshi_prompt(session)

    def apply_action(self, game: GameName, session_id: str, gesture: str) -> tuple[SessionState, bool, float]:
        session = self._sessions.get(session_id)
        if session is None or session.game != game:
            raise KeyError("session_not_found")

        if self._status(session) == "completed":
            return self._to_state(session), False, 0.0

        now = time.time()
        response_time = max(0.0, now - session.last_action_at)
        timed_out = now > session.answer_deadline_at
        in_warmup = game == "suan-shi" and not session.suanshi_can_answer
        if game == "suan-shi" and session.suanshi_can_answer:
            session.suanshi_answered_questions += 1
        correct = False if timed_out else self._is_correct_gesture(game, gesture, session)
        if in_warmup:
            session.consecutive_errors = 0
        else:
            session.consecutive_errors = 0 if correct else session.consecutive_errors + 1
        session.attempt_index += 1
        session.last_action_at = now

        if in_warmup:
            # Warmup rounds establish memory queue without affecting score.
            pass
        elif correct:
            session.score += 10
            session.correct_count += 1
            session.judged_attempts += 1
        else:
            session.score = max(0, session.score - 5)
            session.judged_attempts += 1
            
        if game == "shu-xiang":
            session.box_count = self._new_box_count(session.difficulty_level)
        elif game == "rps":
            session.rps_instruction, session.rps_cpu_action = self._new_rps_state()

        if game == "suan-shi":
            total = session.suanshi_total_questions or 0
            if session.suanshi_answered_questions >= total and total > 0:
                session.current_question = None
                session.current_answer = None
                session.suanshi_can_answer = False
                session.suanshi_target_answer = None
            else:
                self._advance_suanshi(session)

        counters = sqlite_store.get_user_counters(session.user_id, game)
        sqlite_store.insert_interaction(
            session_id=session.id,
            user_id=session.user_id,
            game_type=game,
            difficulty_level=round(session.difficulty_level, 2),
            attempt_index=session.attempt_index,
            correct=correct,
            response_time=round(response_time, 4),
            consecutive_errors=session.consecutive_errors,
            total_attempted=counters.total_attempted + 1,
            skill_opportunities=counters.skill_opportunities + 1,
            time_since_last_same_game=session.time_since_last_same_game,
            gesture=gesture,
        )

        status = self._status(session)
        if game == "suan-shi" and status == "completed":
            sqlite_store.update_user_first_test_completed(session.user_id, True)

        if status == "active":
            session.answer_time_limit_ms = difficulty_service.get_answer_time_limit_ms(game, session.difficulty_level)
            session.answer_deadline_at = now + (session.answer_time_limit_ms / 1000.0)

        # 计算正确率和游戏时长
        accuracy = None
        game_duration = None
        if status == "completed":
            if session.judged_attempts > 0:
                accuracy = session.correct_count / session.judged_attempts
                accuracy = min(1.0, max(0.0, accuracy))
            
            # 计算游戏时长
            game_duration = int(time.time() - session.started_at)

            recent = sqlite_store.list_recent_interactions(session.user_id, game, limit=20)
            recommendation = difficulty_service.recommend_next_difficulty(
                user_id=session.user_id,
                game=game,
                current_difficulty=session.difficulty_level,
                current_correct=correct,
                current_response_time=response_time,
                consecutive_errors=session.consecutive_errors,
                recent_interactions=recent,
            )
            session.difficulty_recommendation = DifficultyRecommendation(
                user_id=recommendation.user_id,
                game_type=recommendation.game_type,  # type: ignore[arg-type]
                current_difficulty=recommendation.current_difficulty,
                recommended_difficulty=recommendation.recommended_difficulty,
                action=recommendation.action,  # type: ignore[arg-type]
                target_band=recommendation.target_band,
                predicted_p_correct=recommendation.predicted_p_correct,
                confidence=recommendation.confidence,
                reason_codes=recommendation.reason_codes,  # type: ignore[arg-type]
                explanation_cn=recommendation.explanation_cn,
            )
            sqlite_store.upsert_user_game_difficulty(
                user_id=session.user_id,
                game_type=game,
                current_difficulty=round(recommendation.recommended_difficulty, 2),
                last_predicted_p=round(recommendation.predicted_p_correct, 4),
                last_confidence=round(recommendation.confidence, 4),
                last_action=recommendation.action,
            )

            try:
                from app.services.memory_service import memory_service
                memory_service.add_session_memory(
                    user_id=session.user_id,
                    game_type=game,
                    score=session.score,
                    accuracy=accuracy,
                    difficulty=session.difficulty_level,
                    duration=game_duration or 0,
                    session_id=session.id,
                )
            except Exception:
                pass

        sqlite_store.update_session(
            session_id=session.id,
            score=session.score,
            difficulty_level=round(session.difficulty_level, 2),
            consecutive_errors=session.consecutive_errors,
            last_attempt_index=session.attempt_index,
            status=status,
            accuracy=accuracy,
            game_duration=game_duration,
        )

        if status == "completed":
            self._delete_persisted_session(session.id)
        else:
            self._persist_session(session)

        return self._to_state(session), correct, round(response_time, 4)


game_engine = GameEngine()
