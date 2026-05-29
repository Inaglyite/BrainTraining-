"""Lightweight JSON-file memory store. No vector DB, no embeddings — just keyword search.
Keeps per-user `.json` files under backend/data/memory_store/. Suitable for 2GB-RAM servers."""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Resolve relative to this file — avoids hardcoded paths from .env
MEMORY_DIR = Path(__file__).resolve().parents[2] / "data" / "memory_store"


class MemoryService:
    def __init__(self) -> None:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Memory service (JSON) initialized at %s", MEMORY_DIR)

    def _file_path(self, user_id: str) -> Path:
        return MEMORY_DIR / f"{user_id}.json"

    def _load(self, user_id: str) -> list[dict[str, Any]]:
        fp = self._file_path(user_id)
        if not fp.exists():
            return []
        try:
            return json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            return []

    def _save(self, user_id: str, memories: list[dict[str, Any]]) -> None:
        # Keep at most 500 entries per user
        memories = memories[-500:]
        self._file_path(user_id).write_text(
            json.dumps(memories, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def add_memory(
        self,
        user_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
        memory_id: str | None = None,
    ) -> str:
        mid = memory_id or f"{user_id}_{int(time.time() * 1000)}"
        memories = self._load(user_id)
        memories.append({
            "id": mid,
            "content": content,
            "metadata": {**(metadata or {}), "user_id": user_id, "timestamp": time.time()},
        })
        self._save(user_id, memories)
        return mid

    def search_memories(self, user_id: str, query: str, k: int = 5) -> list[dict[str, Any]]:
        memories = self._load(user_id)
        if not query.strip():
            return list(reversed(memories[-k:]))

        keywords = query.lower().split()
        scored: list[tuple[int, dict[str, Any]]] = []
        for m in memories:
            text = (m.get("content", "") + " " + str(m.get("metadata", {}))).lower()
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                scored.append((score, m))

        scored.sort(key=lambda x: (-x[0], -float(x[1].get("metadata", {}).get("timestamp", 0))))
        return [m for _, m in scored[:k]]

    def get_recent_memories(self, user_id: str, limit: int = 20) -> list[dict[str, Any]]:
        memories = self._load(user_id)
        memories.sort(key=lambda m: float(m.get("metadata", {}).get("timestamp", 0)), reverse=True)
        return memories[:limit]

    def add_session_memory(
        self,
        user_id: str,
        game_type: str,
        score: int,
        accuracy: float | None,
        difficulty: float,
        duration: int,
        session_id: str,
    ) -> str:
        acc_str = f"{accuracy * 100:.0f}%" if accuracy is not None else "-"
        content = (
            f"用户完成了{game_type}游戏。"
            f"得分：{score}，正确率：{acc_str}，难度：{difficulty:.1f}，时长：{duration}秒。"
        )
        return self.add_memory(
            user_id=user_id,
            content=content,
            metadata={
                "game_type": game_type,
                "score": score,
                "accuracy": accuracy,
                "difficulty": difficulty,
                "duration": duration,
                "session_id": session_id,
            },
        )

    def format_memories_for_context(self, user_id: str, query: str | None = None, limit: int = 10) -> str:
        if query:
            memories = self.search_memories(user_id, query, k=limit)
        else:
            memories = self.get_recent_memories(user_id, limit=limit)

        if not memories:
            return "暂无记忆记录。"

        lines = ["最近的训练记忆："]
        for i, m in enumerate(memories, 1):
            ts = m.get("metadata", {}).get("timestamp", 0)
            when = time.strftime("%m-%d %H:%M", time.localtime(float(ts))) if ts else "未知"
            lines.append(f"{i}. [{when}] {m['content']}")
        return "\n".join(lines)


memory_service = MemoryService()
