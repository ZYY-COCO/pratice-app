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

Every push to `main` will run `deploy/tencent-cloud/deploy.sh` on the server.

## Useful server commands

```bash
sudo systemctl status gangyantong-backend
sudo journalctl -u gangyantong-backend -n 100 --no-pager
sudo nginx -t
sudo systemctl reload nginx
curl http://127.0.0.1:8000/health
```
