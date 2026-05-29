from __future__ import annotations

import json
import logging
from typing import Any

from app.services.llm_service import llm_service
from app.services.memory_service import memory_service
from app.services.sqlite_store import sqlite_store

logger = logging.getLogger(__name__)

AGENT_SYSTEM_PROMPT = """你是一个脑力训练助手 Dr. Brain，专门帮助用户进行认知训练。

你的能力：
1. 查看用户的训练历史和统计数据
2. 分析用户的强项和弱项
3. 提供个性化的训练建议
4. 回答关于认知训练的问题

用户信息包括：
- 训练统计数据（正确率、时长、局数等）
- 最近的训练记忆
- 各游戏（算式回溯、数箱子、指令石头剪刀布）的表现

请用中文回答，保持专业且鼓励的语气。回答要简洁有针对性，不超过300字。"""


class AgentService:
    def _get_user_context(self, user_id: str, message: str) -> str:
        context_parts: list[str] = []

        summaries = []
        for period in ["daily", "monthly"]:
            try:
                s = sqlite_store.get_period_summary(user_id, period)
                summaries.append(s)
            except Exception:
                pass

        for s in summaries:
            total = s.get("total_sessions", 0)
            avg_acc = s.get("average_accuracy")
            dur = s.get("total_duration_seconds", 0)
            period = s.get("period", "")
            if total > 0:
                acc_str = f"{avg_acc * 100:.1f}%" if avg_acc is not None else "-"
                context_parts.append(
                    f"{period}报告：共{total}局，总时长{dur // 60}分{dur % 60}秒，平均正确率{acc_str}"
                )

        for game in ["suan-shi", "shu-xiang", "rps"]:
            interactions = sqlite_store.list_recent_interactions(user_id, game, limit=20)
            if interactions:
                acc = sum(1 for it in interactions if bool(it["correct"])) / len(interactions)
                context_parts.append(f"{game} 最近{len(interactions)}次正确率：{acc * 100:.0f}%")

        memories = memory_service.format_memories_for_context(user_id, limit=5)
        if memories and memories != "暂无记忆记录。":
            context_parts.append(memories)

        return "\n".join(context_parts) if context_parts else "暂无训练数据。"

    def chat(self, user_id: str, message: str) -> tuple[str, str]:
        context = self._get_user_context(user_id, message)

        full_message = f"用户问题：{message}\n\n用户训练背景：\n{context}"

        return llm_service.chat(full_message, context="")


agent_service = AgentService()
