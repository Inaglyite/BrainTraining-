from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.report import AIAnalysisRequest, AIAnalysisResponse, ExperimentResultRequest, ModelConclusionResponse
from app.services.report_generation_service import generate_model_conclusion
from app.services.llm_service import llm_service
from app.services.sqlite_store import sqlite_store

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("/model-conclusion", response_model=ModelConclusionResponse)
def generate_model_conclusion_section(payload: ExperimentResultRequest) -> ModelConclusionResponse:
    content = generate_model_conclusion(payload)
    return ModelConclusionResponse(section_title="第6节 模型性能与结论", content=content)


@router.post("/ai-analysis", response_model=AIAnalysisResponse)
def get_ai_analysis(payload: AIAnalysisRequest) -> AIAnalysisResponse:
    summary = sqlite_store.get_period_summary(
        user_id=payload.user_id,
        period=payload.period,
        anchor_date=payload.anchor_date,
    )

    analysis_text, model_used = llm_service.analyze_report(summary)

    return AIAnalysisResponse(
        user_id=payload.user_id,
        period=payload.period,
        analysis_text=analysis_text,
        model_used=model_used,
    )
