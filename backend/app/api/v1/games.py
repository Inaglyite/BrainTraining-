from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.report import AIAnalysisRequest, AIAnalysisResponse, KnowledgeStateResponse, UserAbilityResponse, GameAbility
from app.schemas.vision import (
    DailySummaryResponse,
    GameName,
    InteractionRecord,
    PeriodSummaryResponse,
    SessionActionRequest,
    SessionActionResponse,
    SessionCreateRequest,
    SessionState,
)
from app.services.game_engine import game_engine
from app.services.gesture_model_service import gesture_model_service
from app.services.sqlite_store import sqlite_store

router = APIRouter(prefix="/games", tags=["games"])


@router.post("/{game}/sessions", response_model=SessionState, status_code=201)
def create_game_session(game: GameName, payload: SessionCreateRequest) -> SessionState:
    try:
        return game_engine.create_session(game, payload.duration_seconds, payload.user_id, payload.difficulty_level)
    except ValueError as exc:
        if str(exc) == "shu_xiang_daily_round_limit_exceeded":
            raise HTTPException(status_code=403, detail="数箱子今日已达 5 局上限，请明天再来。") from exc
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{game}/sessions/{session_id}", response_model=SessionState)
def get_game_session(game: GameName, session_id: str) -> SessionState:
    try:
        return game_engine.get_session(game, session_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc


@router.post("/{game}/sessions/{session_id}/actions", response_model=SessionActionResponse)
def submit_game_action(game: GameName, session_id: str, payload: SessionActionRequest) -> SessionActionResponse:
    gesture = payload.gesture
    inference = None

    if gesture is None and payload.image_base64:
        gesture_set = "rps" if game == "rps" else "digits"
        inference = gesture_model_service.predict_from_base64(
            payload.image_base64,
            payload.min_confidence,
            gesture_set,
        )
        gesture = inference.gesture

    if gesture is None:
        raise HTTPException(status_code=400, detail="Either gesture or image_base64 is required")

    try:
        state, correct, response_time = game_engine.apply_action(game, session_id, gesture)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Session not found") from exc

    return SessionActionResponse(
        state=state,
        used_gesture=gesture,
        correct=correct,
        response_time=response_time,
        inference=inference,
    )


@router.get("/{game}/sessions/{session_id}/interactions", response_model=list[InteractionRecord])
def get_session_interactions(game: GameName, session_id: str, limit: int = 200) -> list[InteractionRecord]:
    if limit < 1 or limit > 2000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 2000")

    records = sqlite_store.list_interactions(session_id=session_id, game_type=game, limit=limit)
    return [InteractionRecord(**row) for row in records]


@router.get("/users/{user_id}/daily-summary", response_model=DailySummaryResponse)
def get_daily_summary(user_id: str, date: str | None = None) -> DailySummaryResponse:
    try:
        summary = sqlite_store.get_daily_summary(user_id=user_id, date_str=date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD") from exc
    return DailySummaryResponse(**summary)


def _build_period_report_text(summary: dict[str, object]) -> str:
    period = str(summary["period"])
    period_name = {"daily": "日报", "monthly": "月报", "quarterly": "季报"}.get(period, "周期报告")
    total_sessions = int(summary["total_sessions"])
    total_duration_seconds = int(summary["total_duration_seconds"])
    avg_accuracy = summary.get("average_accuracy")
    suan_shi_sessions = int(summary["suan_shi_sessions"])
    shu_xiang_sessions = int(summary["shu_xiang_sessions"])
    rps_sessions = int(summary["rps_sessions"])

    minutes = total_duration_seconds // 60
    seconds = total_duration_seconds % 60
    duration_text = f"{minutes}分{seconds:02d}秒"
    avg_text = f"{float(avg_accuracy) * 100:.1f}%" if isinstance(avg_accuracy, float) else "无可用正确率"

    if total_sessions == 0:
        return (
            f"{period_name}（{summary['period_start']} 至 {summary['period_end']}）暂无有效训练记录。"
            "建议先完成至少1局游戏，以便生成可分析的训练趋势。"
        )

    return (
        f"{period_name}（{summary['period_start']} 至 {summary['period_end']}）共完成 {total_sessions} 局训练，"
        f"总时长 {duration_text}，平均正确率 {avg_text}。"
        f"其中算式回溯 {suan_shi_sessions} 局、数箱子 {shu_xiang_sessions} 局、指令石头剪刀布 {rps_sessions} 局。"
        "建议优先保持稳定训练频率，并关注正确率偏低的游戏类型进行针对性练习。"
    )


@router.get("/users/{user_id}/period-summary", response_model=PeriodSummaryResponse)
def get_period_summary(user_id: str, period: str = "daily", anchor_date: str | None = None) -> PeriodSummaryResponse:
    try:
        summary = sqlite_store.get_period_summary(user_id=user_id, period=period, anchor_date=anchor_date)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    summary["report_text"] = _build_period_report_text(summary)
    return PeriodSummaryResponse(**summary)


@router.get("/users/{user_id}/ability", response_model=UserAbilityResponse)
def get_user_ability(user_id: str) -> UserAbilityResponse:
    from app.services.adaptive_service import adaptive_model_service

    games = ["suan-shi", "shu-xiang", "rps"]
    interactions_by_game: dict[str, list[dict[str, object]]] = {}
    for g in games:
        interactions_by_game[g] = sqlite_store.list_recent_interactions(user_id, g, limit=30)

    abilities = adaptive_model_service.get_user_ability_summary(user_id, interactions_by_game)

    ability_models: dict[str, GameAbility] = {}
    for g in games:
        entry = abilities.get(g, {})
        ability_models[g] = GameAbility(
            xgb_p_correct=entry.get("xgb_p_correct"),
            xgb_confidence=entry.get("xgb_confidence"),
            irt_theta=entry.get("irt_theta"),
        )

    return UserAbilityResponse(
        user_id=user_id,
        abilities=ability_models,
        model_status={
            "xgb_available": adaptive_model_service.xgb_available,
            "irt_available": adaptive_model_service.irt_available,
        },
    )


@router.get("/users/{user_id}/knowledge-state", response_model=list[KnowledgeStateResponse])
def get_knowledge_state(user_id: str) -> list[KnowledgeStateResponse]:
    from app.services.adaptive_service import adaptive_model_service

    games = ["suan-shi", "shu-xiang", "rps"]
    results: list[KnowledgeStateResponse] = []
    for g in games:
        interactions = sqlite_store.list_recent_interactions(user_id, g, limit=30)
        if adaptive_model_service.xgb_available and interactions:
            p, conf = adaptive_model_service.predict_p_correct(user_id, g, interactions)
        else:
            p, conf = 0.5, 0.3
        if p < 0.6:
            rec = "建议降低难度或增加练习频率"
        elif p > 0.85:
            rec = "表现优异，可尝试提高难度"
        else:
            rec = "当前难度适中，保持稳定训练"
        results.append(KnowledgeStateResponse(
            user_id=user_id,
            game=g,
            predicted_p_correct=round(p, 4),
            confidence=round(conf, 4),
            recommendation=rec,
        ))
    return results

