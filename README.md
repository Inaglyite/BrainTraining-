# BrainTraining - Brain Training Prototype

This repo contains:

- Frontend: React + Vite (`/`)
- Backend: FastAPI + MediaPipe + joblib gesture model (`/backend`)

## RESTful API

Base URL: `https://localhost:8443/api/v1`

- `GET /health`
- `POST /vision/gestures`
- `POST /games/shu-xiang/sessions`
- `GET /games/shu-xiang/sessions/{session_id}`
- `POST /games/shu-xiang/sessions/{session_id}/actions`
- `GET /games/shu-xiang/sessions/{session_id}/interactions?limit=200`
- `POST /games/suan-shi/sessions`
- `GET /games/suan-shi/sessions/{session_id}`
- `POST /games/suan-shi/sessions/{session_id}/actions`
- `GET /games/suan-shi/sessions/{session_id}/interactions?limit=200`

## One-click deploy (LAN camera-ready)

```bash
cd /home/inaglyite/MyProjects/yuanxing/BrainTraining
bash deploy.sh
```

After deploy:

- App (frontend + backend): `https://localhost:8443`
- LAN app URL: `https://<your-lan-ip>:8443`
- API docs: `https://<your-lan-ip>:8443/docs`
- SQLite DB: `backend/data/game_data.db`

Notes:

- `deploy.sh` builds frontend with same-origin API (`/api/v1`) to avoid LAN `127.0.0.1` issues.
- The script creates a self-signed certificate in `.cert/` on first run.
- For camera permission via LAN IP, open HTTPS URL and trust the certificate once in browser.

Create session payload supports adaptive training fields:

```json
{
  "duration_seconds": 60,
  "user_id": "alice",
  "difficulty_level": 1.0
}
```

Backend dependency compatibility note:

- `mediapipe==0.10.21` needs `numpy<2`, so backend locks `numpy==1.26.4`.

## Local development

### Backend

```bash
cd /home/inaglyite/MyProjects/yuanxing/BrainTraining/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd /home/inaglyite/MyProjects/yuanxing/BrainTraining
npm install
npm run dev
```
