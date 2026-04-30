# 港澳台考研初试刷题 App API

## 本地启动

1. 安装 Python 3.11+。
2. 复制 `.env.example` 为 `.env`，填入 Supabase 项目配置。
3. 安装依赖并启动服务：

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

启动目录建议为 `backend/`，接口文档地址为 `http://127.0.0.1:8000/docs`。

## H5 内测后端部署

Render / Railway / Zeabur 均可部署当前 FastAPI 后端。部署时建议：

- Root Directory：`backend`
- Install Command：`pip install -r requirements.txt`
- Start Command：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

云端不要使用 `--reload`，`--reload` 只适合本地开发。

需要在部署平台配置环境变量：

```env
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
API_CORS_ORIGINS=https://你的前端公网域名
SMTP_HOST=
SMTP_PORT=465
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_FROM_EMAIL=
SMTP_FROM_NAME=港澳台考研刷题
SMTP_USE_TLS=false
PAYMENT_WEBHOOK_SECRET=
DEEPSEEK_API_KEY=
DEEPSEEK_BASE_URL=https://api.deepseek.com
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_TIMEOUT_SECONDS=60
```

`SUPABASE_SERVICE_ROLE_KEY` 只能配置在后端部署平台，不能放到前端。

部署后先检查：

```text
https://你的后端公网域名/health
https://你的后端公网域名/docs
```

## 核心流程

- `POST /auth/register`：邮箱注册并写入 `public.users`。
- `POST /auth/login`：邮箱登录，返回 Supabase access token。
- `POST /auth/send-phone-code`：发送手机号验证码（需先执行 `database/phone_auth.sql` 并配置短信通道）。
- `POST /auth/phone-register`：手机号验证码注册，兼容 Supabase token。
- `POST /auth/phone-login`：手机号验证码登录，返回 Supabase access token。
- `POST /auth/wechat-login`：微信登录预留接口，需配置微信开放平台/公众号后启用。
- `GET /questions/by-module`：按 `exam_code + subject + module + submodule` 获取专项题目。
- `POST /answers/submit`：提交答案，同步写入作答记录、错题本和能力统计。
- `GET /report/ability`：读取能力统计并返回薄弱项建议。
- `GET /membership/plans`：读取 Pro 套餐配置。
- `POST /membership/orders`：创建会员订单，当前先返回待支付订单。
- `POST /membership/webhooks/manual`：支付回调骨架，校验 `PAYMENT_WEBHOOK_SECRET` 后更新订单和会员状态。
