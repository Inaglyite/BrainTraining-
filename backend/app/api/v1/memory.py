from __future__ import annotations

from fastapi import APIRouter, Query

from app.services.memory_service import memory_service

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("/search")
def search_memories(
    user_id: str = Query(...),
    q: str = Query(default="", alias="q"),
    k: int = Query(default=5, ge=1, le=20),
) -> dict[str, object]:
    if not q.strip():
        memories = memory_service.get_recent_memories(user_id, limit=k)
    else:
        memories = memory_service.search_memories(user_id, q, k=k)
    return {"user_id": user_id, "query": q, "memories": memories}


@router.get("/recent")
def get_recent_memories(
    user_id: str = Query(...),
    limit: int = Query(default=20, ge=1, le=50),
) -> dict[str, object]:
    memories = memory_service.get_recent_memories(user_id, limit=limit)
    return {"user_id": user_id, "memories": memories}
