from __future__ import annotations

from dataclasses import dataclass

from app.schemas.report import ExperimentResultRequest, MODEL_NAMES, ModelMetric


@dataclass(frozen=True)
class _ModelLine:
    name: str
    metric: ModelMetric
    executed: bool
    reason: str | None = None


def _fmt_num(x: float | None) -> str:
    if x is None:
        return "-"
    return f"{x:.4f}"


def _model_executed(metric: ModelMetric) -> tuple[bool, str | None]:
    missing: list[str] = []
    if metric.accuracy is None:
        missing.append("Accuracy")
    if metric.auc is None:
        missing.append("AUC")
    if metric.brier is None:
        missing.append("Brier")

    if not missing:
        return True, None
    if len(missing) == 3:
        return False, "该模型指标未提供"
    return False, f"{', '.join(missing)} 指标缺失"


def _rank_models(lines: list[_ModelLine]) -> list[_ModelLine]:
    executed = [ln for ln in lines if ln.executed]
    return sorted(
        executed,
        key=lambda ln: (
            ln.metric.auc if ln.metric.auc is not None else -1.0,
            ln.metric.accuracy if ln.metric.accuracy is not None else -1.0,
            -(ln.metric.brier if ln.metric.brier is not None else 1.0),
        ),
        reverse=True,
    )


def generate_model_conclusion(payload: ExperimentResultRequest) -> str:
    lines: list[_ModelLine] = []
    for name in MODEL_NAMES:
        metric = payload.metrics.get(name, ModelMetric())
        executed, reason = _model_executed(metric)
        lines.append(_ModelLine(name=name, metric=metric, executed=executed, reason=reason))

    ranked = _rank_models(lines)
    best = ranked[0] if ranked else None

    conclusion_lines: list[str] = []
    conclusion_lines.append("1) 结论摘要（3-5行）")
    conclusion_lines.append(
        f"- 本次实验数据集为 {payload.dataset_name}，训练集 {payload.train_size}，测试集 {payload.test_size}。"
    )
    if best is not None:
        conclusion_lines.append(
            f"- 在已执行模型中，{best.name} 综合表现最佳（Accuracy={_fmt_num(best.metric.accuracy)}, AUC={_fmt_num(best.metric.auc)}, Brier={_fmt_num(best.metric.brier)}）。"
        )
    else:
        conclusion_lines.append("- 当前未提供可执行模型的完整 Accuracy/AUC/Brier 指标，无法得出性能优劣结论。")
    conclusion_lines.append(
        "- 模型比较统一基于 Accuracy / AUC / Brier 三项指标，且仅依据输入中的事实进行判断。"
    )
    conclusion_lines.append(
        f"- 难度目标流畅区间设为 {payload.target_flow_band[0]:.2f}~{payload.target_flow_band[1]:.2f}，后续应优先保障概率校准质量。"
    )

    model_lines: list[str] = []
    model_lines.append("2) 指标对比分析（按模型逐个）")
    for ln in lines:
        if ln.executed:
            model_lines.append(
                f"- {ln.name}: Accuracy={_fmt_num(ln.metric.accuracy)}, AUC={_fmt_num(ln.metric.auc)}, Brier={_fmt_num(ln.metric.brier)}。"
            )
        else:
            model_lines.append(f"- {ln.name}: 未执行（原因：{ln.reason}）。")

    xgb_lines: list[str] = []
    xgb_lines.append("3) XGBoost辅助洞察（分层+特征）")
    if payload.xgboost_aux is None:
        xgb_lines.append("- 未执行（原因：未提供 xgboost_aux 信息）。")
    else:
        seg = payload.xgboost_aux.user_risk_segments
        if seg is None:
            xgb_lines.append("- 用户风险分层：未执行（原因：未提供 user_risk_segments）。")
        else:
            xgb_lines.append(
                "- 用户风险分层："
                f"高风险={_fmt_num(seg.high_risk_ratio)}，"
                f"中风险={_fmt_num(seg.medium_risk_ratio)}，"
                f"低风险={_fmt_num(seg.low_risk_ratio)}。"
            )

        feats = payload.xgboost_aux.top_feature_importance
        if not feats:
            xgb_lines.append("- 关键特征：未执行（原因：未提供 top_feature_importance）。")
        else:
            feat_items = [f"{name}({weight:.4f})" for name, weight in feats]
            xgb_lines.append(f"- 关键特征：{', '.join(feat_items)}。")

    limit_lines: list[str] = []
    limit_lines.append("4) 局限性")
    missing_models = [ln.name for ln in lines if not ln.executed]
    if missing_models:
        limit_lines.append(
            f"- 以下模型未形成完整对比：{', '.join(missing_models)}；因此当前结论仅代表已执行模型。"
        )
    else:
        limit_lines.append("- 当前结论依赖单次输入结果，尚未包含跨时间窗口的稳定性检验。")
    limit_lines.append("- 若未提供风险分层或特征权重，则无法进行人群分层解释与特征归因验证。")

    improve_lines: list[str] = []
    improve_lines.append("5) 下一步优化（3条）")
    improve_lines.append("- 建立统一评测流水线：同一训练/测试划分下同时产出 IRT、DKT-Light、LSTM-DKT、RF-Seq、XGBoost-Seq 的 Accuracy/AUC/Brier。")
    improve_lines.append(
        f"- 以目标区间 {payload.target_flow_band[0]:.2f}~{payload.target_flow_band[1]:.2f} 为约束，增加概率校准（如温度缩放/等值回归）并优先优化 Brier。"
    )
    improve_lines.append("- 对 XGBoost-Seq 增加分层监控面板，持续跟踪高/中/低风险占比与 Top 特征漂移，指导规则与难度调整。")

    sections = [
        "\n".join(conclusion_lines),
        "\n".join(model_lines),
        "\n".join(xgb_lines),
        "\n".join(limit_lines),
        "\n".join(improve_lines),
    ]
    return "\n\n".join(sections)
