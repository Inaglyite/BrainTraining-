from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator


MODEL_NAMES = ["IRT(1PL)", "DKT-Light", "LSTM-DKT", "RF-Seq", "XGBoost-Seq"]


class ModelMetric(BaseModel):
    accuracy: float | None = None
    auc: float | None = None
    brier: float | None = None


class UserRiskSegments(BaseModel):
    high_risk_ratio: float | None = None
    medium_risk_ratio: float | None = None
    low_risk_ratio: float | None = None


class XGBoostAux(BaseModel):
    user_risk_segments: UserRiskSegments | None = None
    top_feature_importance: list[tuple[str, float]] | None = None


class ExperimentResultRequest(BaseModel):
    dataset_name: str
    train_size: int = Field(ge=0)
    test_size: int = Field(ge=0)
    metrics: dict[str, ModelMetric]
    xgboost_aux: XGBoostAux | None = None
    target_flow_band: tuple[float, float] = (0.65, 0.75)

    @model_validator(mode="after")
    def validate_models(self) -> "ExperimentResultRequest":
        for model_name in MODEL_NAMES:
            if model_name not in self.metrics:
                self.metrics[model_name] = ModelMetric()
        return self


class ModelConclusionResponse(BaseModel):
    section_title: Literal["第6节 模型性能与结论"]
    content: str


class AIAnalysisRequest(BaseModel):
    user_id: str
    period: Literal["daily", "monthly", "quarterly"] = "daily"
    anchor_date: str | None = None


class AIAnalysisResponse(BaseModel):
    user_id: str
    period: str
    analysis_text: str
    model_used: str


class GameAbility(BaseModel):
    xgb_p_correct: float | None = None
    xgb_confidence: float | None = None
    irt_theta: float | None = None


class UserAbilityResponse(BaseModel):
    user_id: str
    abilities: dict[str, GameAbility]
    model_status: dict[str, bool]


class KnowledgeStateResponse(BaseModel):
    user_id: str
    game: str
    predicted_p_correct: float
    confidence: float
    recommendation: str
