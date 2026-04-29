#!/usr/bin/env bash
set -euo pipefail

APP_NAME="gangyantong"
APP_USER="${APP_USER:-ubuntu}"
APP_ROOT="/opt/${APP_NAME}"
APP_DIR="${APP_ROOT}/app"
WEB_DIR="/var/www/${APP_NAME}"
BACKEND_ENV="${APP_ROOT}/backend.env"
REPO_URL="${REPO_URL:-https://github.com/ZYY-COCO/pratice-app.git}"
BRANCH="${BRANCH:-main}"
NODE_MAJOR="${NODE_MAJOR:-20}"

echo "==> Installing system packages"
sudo apt-get update
sudo apt-get install -y ca-certificates curl git nginx python3 python3-pip python3-venv rsync

if ! command -v node >/dev/null 2>&1 || ! node -v | grep -q "^v${NODE_MAJOR}\\."; then
  echo "==> Installing Node.js ${NODE_MAJOR}"
  curl -fsSL "https://deb.nodesource.com/setup_${NODE_MAJOR}.x" | sudo -E bash -
  sudo apt-get install -y nodejs
fi

echo "==> Preparing directories"
sudo mkdir -p "${APP_ROOT}" "${WEB_DIR}"
sudo chown -R "${APP_USER}:${APP_USER}" "${APP_ROOT}"
sudo chown -R "${APP_USER}:${APP_USER}" "${WEB_DIR}"

if [ ! -d "${APP_DIR}/.git" ]; then
  echo "==> Cloning repository"
  git clone --branch "${BRANCH}" "${REPO_URL}" "${APP_DIR}"
else
  echo "==> Repository already exists, updating"
  git -C "${APP_DIR}" fetch origin "${BRANCH}"
  git -C "${APP_DIR}" reset --hard "origin/${BRANCH}"
fi

if [ ! -f "${BACKEND_ENV}" ]; then
  echo "==> Creating backend env placeholder at ${BACKEND_ENV}"
  sudo tee "${BACKEND_ENV}" >/dev/null <<'ENVEOF'
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
API_CORS_ORIGINS=*
SMTP_HOST=
SMTP_PORT=465
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=Gangyantong
SMTP_USE_TLS=false
PAYMENT_WEBHOOK_SECRET=
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_TIMEOUT_SECONDS=60
ENVEOF
  sudo chown "${APP_USER}:${APP_USER}" "${BACKEND_ENV}"
  sudo chmod 600 "${BACKEND_ENV}"
fi

echo "==> Installing systemd service"
sudo cp "${APP_DIR}/deploy/tencent-cloud/gangyantong-backend.service" /etc/systemd/system/gangyantong-backend.service
sudo systemctl daemon-reload
sudo systemctl enable gangyantong-backend

echo "==> Installing Nginx site"
sudo cp "${APP_DIR}/deploy/tencent-cloud/nginx.conf" /etc/nginx/sites-available/gangyantong
sudo ln -sfn /etc/nginx/sites-available/gangyantong /etc/nginx/sites-enabled/gangyantong
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl reload nginx

if grep -Eq '^(SUPABASE_URL|SUPABASE_ANON_KEY|SUPABASE_SERVICE_ROLE_KEY)=$' "${BACKEND_ENV}"; then
  echo
  echo "Setup finished, but backend env is not filled yet."
  echo "Run this on the server, fill real values, then deploy:"
  echo "  nano ${BACKEND_ENV}"
  echo "  cd ${APP_DIR} && bash deploy/tencent-cloud/deploy.sh"
  exit 0
fi

echo "==> Running first deployment"
cd "${APP_DIR}"
bash deploy/tencent-cloud/deploy.sh
