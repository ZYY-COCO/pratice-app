# Tencent Cloud Deployment

This setup deploys the H5 frontend and FastAPI backend on one Ubuntu server.

- Frontend: `/var/www/gangyantong`
- Backend app: `/opt/gangyantong/app/backend`
- Backend env file: `/opt/gangyantong/backend.env`
- Backend service: `gangyantong-backend`
- API path: `/api/*` proxied by Nginx to `127.0.0.1:8000`

## First-time server setup

SSH into the server and run:

```bash
REPO_URL="https://github.com/ZYY-COCO/pratice-app.git" BRANCH="main" bash <(curl -fsSL https://raw.githubusercontent.com/ZYY-COCO/pratice-app/main/deploy/tencent-cloud/setup_ubuntu.sh)
```

If the env file is empty, edit it:

```bash
nano /opt/gangyantong/backend.env
```

For WeChat Mini Program login, the existing server env must include:

```env
WECHAT_MINIPROGRAM_APP_ID=
WECHAT_MINIPROGRAM_APP_SECRET=
WECHAT_AUTH_PASSWORD_SECRET=
```

Keep these values only in `/opt/gangyantong/backend.env`; never put the AppSecret in frontend code or Git.

Then deploy:

```bash
cd /opt/gangyantong/app
bash deploy/tencent-cloud/deploy.sh
```

## GitHub Actions secrets

Add these repository secrets:

- `TENCENT_HOST`: server public IP, for example `159.75.155.82`
- `TENCENT_USER`: `ubuntu`
- `TENCENT_SSH_KEY`: private SSH key that can log into the server
- `TENCENT_PORT`: optional, defaults to `22`

Every push to `main` runs `.github/workflows/tencent-cloud-deploy.yml`. The
workflow builds H5 in GitHub Actions, uploads verified frontend/backend archives,
syncs them into the two production directories, installs backend dependencies,
restarts `gangyantong-backend`, and checks both the static support page and API
health endpoint. It does not call the server-side `deploy.sh` and it does not run
database migrations.

Before replacing production files, the workflow also verifies that the server
Python is 3.10 or newer, compiles the candidate backend, and checks the effective
adaptive-practice configuration is closed (`ADAPTIVE_PRACTICE_ENABLED=false`
and `ADAPTIVE_PRACTICE_ROLLOUT_PERCENT=0`; missing values use the same fail-closed
application defaults). Keep those values closed for the first deployment and
ordinary-practice regression.

## Useful server commands

```bash
sudo systemctl status gangyantong-backend
sudo journalctl -u gangyantong-backend -n 100 --no-pager
sudo nginx -t
sudo systemctl reload nginx
curl http://127.0.0.1:8000/health
```
