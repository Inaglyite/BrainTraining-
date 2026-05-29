#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR"
VENV_DIR="$BACKEND_DIR/.venv"
PID_DIR="$ROOT_DIR/.run"
DATA_DIR="$BACKEND_DIR/data"
CERT_DIR="$ROOT_DIR/.cert"
CERT_FILE="$CERT_DIR/lan-cert.pem"
KEY_FILE="$CERT_DIR/lan-key.pem"
ENV_FILE="$BACKEND_DIR/.env"
ENV_EXAMPLE="$BACKEND_DIR/.env.example"

mkdir -p "$PID_DIR" "$DATA_DIR" "$CERT_DIR"

# ---- auto-detect environment ----
BIND_HOST="${HOST:-}"
if [ -z "$BIND_HOST" ]; then
  if [ -n "${SSH_CONNECTION:-}" ] || [ -n "${SSH_TTY:-}" ] || hostname | grep -qiE 'vm|cloud|ec2|vps'; then
    BIND_HOST="0.0.0.0"
  else
    BIND_HOST="127.0.0.1"
  fi
fi

# ---- .env setup ----
if [ ! -f "$ENV_FILE" ]; then
  if [ -f "$ENV_EXAMPLE" ]; then
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    echo ">>> Created backend/.env from .env.example"
    echo ">>> REMEMBER to set DEEPSEEK_API_KEY in backend/.env or AI features won't work!"
  else
    cat > "$ENV_FILE" << 'EOF'
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
EOF
    echo ">>> Created backend/.env — fill in DEEPSEEK_API_KEY"
  fi
fi

# Clean up any hardcoded local paths leaked into .env
sed -i '/^SQLITE_DB_PATH=/d' "$ENV_FILE" 2>/dev/null || true
sed -i '/^GESTURE_MODEL_PATH=/d' "$ENV_FILE" 2>/dev/null || true
sed -i '/^MEDIAPIPE_TASK_MODEL_PATH=/d' "$ENV_FILE" 2>/dev/null || true
sed -i '/^IRT_MODEL_PATH=/d' "$ENV_FILE" 2>/dev/null || true
sed -i '/^XGB_MODEL_PATH=/d' "$ENV_FILE" 2>/dev/null || true

echo "[1/6] Stop previous services"
if [ -f "$PID_DIR/backend.pid" ]; then
  old="$(cat "$PID_DIR/backend.pid" 2>/dev/null || true)"
  [ -n "${old:-}" ] && kill "$old" 2>/dev/null || true
fi
pkill -f "uvicorn app.main:app.*8443" 2>/dev/null || true
sleep 1

echo "[2/6] Install frontend dependencies"
cd "$FRONTEND_DIR"
npm install

echo "[3/6] Install backend dependencies"
cd "$BACKEND_DIR"
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel -q
pip install -r requirements.txt -q

echo "[4/6] Build frontend"
mkdir -p "$FRONTEND_DIR/public/wasm" "$FRONTEND_DIR/public/models"
cp "$FRONTEND_DIR/node_modules/@mediapipe/tasks-vision/wasm/"* "$FRONTEND_DIR/public/wasm/" 2>/dev/null || true
if [ ! -f "$FRONTEND_DIR/public/models/hand_landmarker.task" ]; then
  curl -fsSL "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task" \
    -o "$FRONTEND_DIR/public/models/hand_landmarker.task" || echo "WARNING: failed to download hand_landmarker.task"
fi

cd "$FRONTEND_DIR"
export VITE_API_BASE="/api/v1"
npm run build

echo "[5/6] Prepare HTTPS certificate"
if [ ! -f "$CERT_FILE" ] || [ ! -f "$KEY_FILE" ]; then
  openssl req -x509 -nodes -newkey rsa:2048 \
    -keyout "$KEY_FILE" \
    -out "$CERT_FILE" \
    -days 365 \
    -subj "/CN=lan-local" 2>/dev/null
fi

echo "[6/6] Start backend ($BIND_HOST:8443)"
cd "$BACKEND_DIR"
source "$VENV_DIR/bin/activate"
nohup uvicorn app.main:app --host "$BIND_HOST" --port 8443 \
  --ssl-keyfile "$KEY_FILE" \
  --ssl-certfile "$CERT_FILE" > "$PID_DIR/backend.log" 2>&1 &
echo $! > "$PID_DIR/backend.pid"

sleep 2
if kill -0 "$(cat "$PID_DIR/backend.pid")" 2>/dev/null; then
  echo ""
  echo "============================================"
  echo "  Deploy OK — https://localhost:8443"
  echo "  API docs — https://localhost:8443/docs"
  echo "============================================"
else
  echo "FAILED to start! Check .run/backend.log:"
  tail -20 "$PID_DIR/backend.log"
  exit 1
fi
