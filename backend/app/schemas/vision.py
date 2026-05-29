from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

GestureName = str
GameName = Literal["shu-xiang", "suan-shi", "rps"]
GestureSet = Literal["digits", "rps"]


class GestureDetectRequest(BaseModel):
    image_base64: str = Field(..., description="Base64 image string, supports optional data URL prefix")
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    gesture_set: GestureSet = Field(default="digits")


class GestureDetectResponse(BaseModel):
    gesture: GestureName
    raw_label: str | None = None
    confidence: float | None = None
    hand_detected: bool
    threshold: float


class SessionCreateRequest(BaseModel):
    duration_seconds: int = Field(default=60, ge=10, le=600)
    user_id: str = Field(default="anonymous")
    difficulty_level: float = Field(default=1.0, ge=0.1, le=10.0)


class DifficultyRecommendation(BaseModel):
    user_id: str
    game_type: Literal["算式回溯", "数箱子", "指令石头剪刀布"]
    current_difficulty: float
    recommended_difficulty: float
    action: Literal["increase", "decrease", "keep"]
    target_band: tuple[float, float]
    predicted_p_correct: float
    confidence: float
    reason_codes: list[Literal["theta_low", "theta_high", "in_band", "consecutive_errors", "slow_response"]]
    explanation_cn: str


class SessionState(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: str
    game: GameName
    score: int
    remaining_seconds: int
    elapsed_seconds: int
    status: Literal["active", "completed"]
    user_id: str
    difficulty_level: float
    attempt_index: int
    consecutive_errors: int
    current_question: str | None = None
    n_back_level: int | None = None
    suanshi_total_questions: int | None = None
    suanshi_answered_questions: int | None = None
    suanshi_target_answer: int | None = None
    suanshi_can_answer: bool | None = None
    suanshi_recent_answers: list[int] | None = None
    box_count: int | None = None
    rps_instruction: Literal["win", "lose", "draw"] | None = None
    rps_cpu_action: Literal["rock", "paper", "scissors"] | None = None
    answer_time_limit_ms: int | None = None
    answer_remaining_ms: int | None = None
    difficulty_recommendation: DifficultyRecommendation | None = None


class LandmarkClassifyRequest(BaseModel):
    landmarks: list[float] = Field(..., min_length=63, max_length=63)
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    gesture_set: GestureSet = Field(default="digits")


class SessionActionRequest(BaseModel):
    gesture: GestureName | None = None
    image_base64: str | None = None
    min_confidence: float | None = Field(default=None, ge=0.0, le=1.0)


class SessionActionResponse(BaseModel):
    state: SessionState
    used_gesture: GestureName | None = None
    correct: bool | None = None
    response_time: float | None = None
    inference: GestureDetectResponse | None = None


class InteractionRecord(BaseModel):
    id: int
    session_id: str
    user_id: str
    game_type: str
    difficulty_level: float
    attempt_index: int
    correct: bool
    response_time: float
    consecutive_errors: int
    total_attempted: int
    skill_opportunities: int
    time_since_last_same_game: float | None = None
    help_used: bool | None = None
    skip_used: bool | None = None
    gesture: str | None = None
    created_at: float


class DailySessionItem(BaseModel):
    session_id: str
    game_type: GameName
    started_at: float
    duration_seconds: int
    score: int
    accuracy: float | None = None
    status: str


class DailySummaryResponse(BaseModel):
    user_id: str
    date: str
    total_duration_seconds: int
    total_sessions: int
    shu_xiang_sessions: int
    suan_shi_sessions: int
    rps_sessions: int
    shu_xiang_remaining_rounds: int
    sessions: list[DailySessionItem]


class PeriodSummaryResponse(BaseModel):
    user_id: str
    period: Literal["daily", "monthly", "quarterly"]
    anchor_date: str
    period_start: str
    period_end: str
    total_duration_seconds: int
    total_sessions: int
    shu_xiang_sessions: int
    suan_shi_sessions: int
    rps_sessions: int
    average_accuracy: float | None = None
    sessions: list[DailySessionItem]
    report_text: str

