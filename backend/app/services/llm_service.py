from __future__ import annotations

import json
import logging
from typing import Any

from openai import OpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """你是一位专业的认知训练分析专家，负责分析用户的脑力锻炼数据并给出个性化建议。

你的分析应该包括以下方面：
1. **总体评估**：对用户在该周期内的训练表现进行总体评价
2. **趋势分析**：识别正确率、反应速度、训练时长的变化趋势
3. **游戏分析**：对算式回溯（n-back记忆）、数箱子（空间记忆）、指令石头剪刀布（执行功能）分别分析
4. **难度适配**：评估当前难度是否合适，是否处于最优学习区间（65%-75%正确率）
5. **个性化建议**：给出2-3条具体的、可操作的改进建议
6. **鼓励结语**：用温暖鼓励的语气结束分析

请用中文输出，使用markdown格式，保持专业但友好的语调。不要超过500字。"""


class LLMService:
    def __init__(self) -> None:
        api_key = settings.deepseek_api_key
        base_url = settings.deepseek_base_url
        self._available = bool(api_key)
        if self._available:
            self._client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self._client = None
            logger.warning("DEEPSEEK_API_KEY not set, LLM service disabled")

    @property
    def available(self) -> bool:
        return self._available

    def _build_report_context(self, user_data: dict[str, Any]) -> str:
        sessions = user_data.get("sessions", [])
        total = user_data.get("total_sessions", 0)
        avg_acc = user_data.get("average_accuracy")
        total_dur = user_data.get("total_duration_seconds", 0)
        period = user_data.get("period", "daily")
        period_start = user_data.get("period_start", "")
        period_end = user_data.get("period_end", "")

        ctx = f"报告周期：{period}（{period_start} 至 {period_end}）\n"
        ctx += f"总训练局数：{total}\n"
        ctx += f"总训练时长：{total_dur // 60}分{total_dur % 60}秒\n"
        if avg_acc is not None:
            ctx += f"平均正确率：{avg_acc * 100:.1f}%\n"

        ctx += f"算式回溯局数：{user_data.get('suan_shi_sessions', 0)}\n"
        ctx += f"数箱子局数：{user_data.get('shu_xiang_sessions', 0)}\n"
        ctx += f"指令石头剪刀布局数：{user_data.get('rps_sessions', 0)}\n"

        if sessions:
            ctx += "\n各局详情：\n"
            for i, s in enumerate(sessions[-10:], 1):
                game = s.get("game_type", "unknown")
                score = s.get("score", 0)
                acc = s.get("accuracy")
                dur = s.get("duration_seconds", 0)
                acc_str = f"{acc * 100:.0f}%" if acc is not None else "-"
                ctx += f"  {i}. {game} | 得分:{score} | 正确率:{acc_str} | 时长:{dur}s\n"

        return ctx

    def analyze_report(self, user_data: dict[str, Any]) -> tuple[str, str]:
        if not self._available:
            return "LLM 服务未配置（缺少 DEEPSEEK_API_KEY 环境变量）。", "disabled"

        context = self._build_report_context(user_data)

        try:
            response = self._client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"请分析以下用户的训练数据：\n\n{context}"},
                ],
                temperature=0.7,
                max_tokens=1024,
            )
            text = response.choices[0].message.content or ""
            return text.strip(), "deepseek-chat"
        except Exception:
            logger.exception("DeepSeek API call failed")
            return "AI 分析暂时不可用，请稍后再试。", "error"

    def chat(self, user_message: str, context: str = "") -> tuple[str, str]:
        if not self._available:
            return "LLM 服务未配置。", "disabled"

        messages: list[dict[str, str]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        if context:
            messages.append({"role": "system", "content": f"用户背景信息：\n{context}"})
        messages.append({"role": "user", "content": user_message})

        try:
            response = self._client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=1024,
            )
            text = response.choices[0].message.content or ""
            return text.strip(), "deepseek-chat"
        except Exception:
            logger.exception("DeepSeek chat failed")
            return "AI 暂时不可用，请稍后再试。", "error"


llm_service = LLMService()
