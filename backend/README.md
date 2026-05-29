# FastAPI Backend

## Run locally

```bash
cd /home/inaglyite/MyProjects/yuanxing/BrainTraining/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Smoke test

```bash
cd /home/inaglyite/MyProjects/yuanxing/BrainTraining/backend
PYTHONPATH=. python3 tests/smoke_test.py
```

## Key endpoints (RESTful)

- `GET /api/v1/health`
- `POST /api/v1/vision/gestures`
- `POST /api/v1/games/shu-xiang/sessions`
- `GET /api/v1/games/shu-xiang/sessions/{session_id}`
- `POST /api/v1/games/shu-xiang/sessions/{session_id}/actions`
- `GET /api/v1/games/shu-xiang/sessions/{session_id}/interactions?limit=200`
- `POST /api/v1/games/suan-shi/sessions`
- `GET /api/v1/games/suan-shi/sessions/{session_id}`
- `POST /api/v1/games/suan-shi/sessions/{session_id}/actions`
- `GET /api/v1/games/suan-shi/sessions/{session_id}/interactions?limit=200`

## SQLite persistence

- DB path: `backend/data/game_data.db` (configurable via `SQLITE_DB_PATH`)
- Tables:
  - `game_sessions`
  - `game_interactions`
- `POST /api/v1/games/{game}/sessions` request body now supports:
  - `duration_seconds`
  - `user_id`
  - `difficulty_level`

## Dependency note

- To avoid `mediapipe` conflict, `numpy` is pinned to `1.26.4` (`mediapipe==0.10.21` requires `numpy<2`).

