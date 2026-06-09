#!/usr/bin/env bash
set -euo pipefail

APP_NAME="gangyantong"
APP_ROOT="/opt/${APP_NAME}"
APP_DIR="${APP_ROOT}/app"
WEB_DIR="/var/www/${APP_NAME}"
BRANCH="${BRANCH:-main}"
VITE_API_BASE_URL="${VITE_API_BASE_URL:-/api}"

cd "${APP_DIR}"

echo "==> Updating source"
git fetch origin "${BRANCH}"
git sparse-checkout disable || true
git config core.sparseCheckout false
git ls-files -v | awk '$1 ~ /^[a-zS]/ {print substr($0, 3)}' | while IFS= read -r tracked_file; do
  git update-index --no-assume-unchanged --no-skip-worktree -- "${tracked_file}"
done
git reset --hard "origin/${BRANCH}"

echo "==> Installing backend dependencies"
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install --upgrade pip
backend/.venv/bin/pip install -r backend/requirements.txt

echo "==> Building frontend"
cd frontend
npm ci
rm -rf dist/build/h5 dist/cache unpackage/dist/build/h5 node_modules/.vite
VITE_API_BASE_URL="${VITE_API_BASE_URL}" npm run build:h5
test -f dist/build/h5/index.html
cd "${APP_DIR}"

echo "==> Publishing frontend"
sudo mkdir -p "${WEB_DIR}"
sudo rsync -a --delete frontend/dist/build/h5/ "${WEB_DIR}/"

echo "==> Updating Nginx site"
sudo cp deploy/tencent-cloud/nginx.conf /etc/nginx/sites-available/gangyantong
sudo ln -sfn /etc/nginx/sites-available/gangyantong /etc/nginx/sites-enabled/gangyantong
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

echo "==> Restarting services"
sudo systemctl restart gangyantong-backend
sudo systemctl reload nginx

echo "==> Health check"
for attempt in {1..20}; do
  if curl -fsS http://127.0.0.1:8000/health; then
    echo
    echo "Deployment finished."
    exit 0
  fi
  echo "Backend is not ready yet, retrying (${attempt}/20)..."
  sleep 2
done

echo
echo "Backend health check failed after waiting."
sudo systemctl status gangyantong-backend --no-pager || true
exit 1
