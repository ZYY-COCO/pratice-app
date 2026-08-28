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
API_CORS_ORIGINS=https://www.gangyantong.com,https://gangyantong.com
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
PHONE_AUTH_PASSWORD_SECRET=
SMS_PROVIDER=tencent
SMS_MOCK_RETURN_CODE=false
TENCENT_SMS_SECRET_ID=
TENCENT_SMS_SECRET_KEY=
TENCENT_SMS_SDK_APP_ID=
TENCENT_SMS_SIGN_NAME=
TENCENT_SMS_TEMPLATE_ID=
TENCENT_SMS_TEMPLATE_PARAMS=code
TENCENT_SMS_REGION=ap-guangzhou
TENCENT_OCR_SECRET_ID=
TENCENT_OCR_SECRET_KEY=
TENCENT_OCR_REGION=ap-guangzhou
TENCENT_OCR_ENDPOINT=ocr.tencentcloudapi.com
TENCENT_OCR_TIMEOUT_SECONDS=30
WECHAT_OAUTH_APP_ID=
WECHAT_OAUTH_APP_SECRET=
WECHAT_OAUTH_SCOPE=snsapi_userinfo
WECHAT_MINIPROGRAM_APP_ID=
WECHAT_MINIPROGRAM_APP_SECRET=
WECHAT_AUTH_PASSWORD_SECRET=
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
- `GET /auth/wechat-auth-url`：生成微信网页授权地址。
- `POST /auth/wechat-login`：微信登录；`platform=h5` 走网页授权，`platform=miniprogram` 走小程序 `code2Session`，按 openid 创建或登录用户。
- `GET /report/study-goal`：读取当前账号、当前考试版本的学习任务。
- `PUT /report/study-goal`：保存每日学习时长与每周刷题目标；启用前需执行 `database/user_study_goals.sql`。
- `POST /auth/refresh`：使用 refresh token 续期 access token。
- `GET /questions/by-module`：按 `exam_code + subject + module + submodule` 获取专项题目。
- `POST /answers/submit`：提交答案，同步写入作答记录、错题本和能力统计。
- `GET /report/ability`：读取能力统计并返回薄弱项建议。
- `GET /membership/plans`：读取 Pro 套餐配置。
- `POST /membership/orders`：创建会员订单，当前先返回待支付订单。
- `POST /membership/webhooks/manual`：支付回调骨架，校验 `PAYMENT_WEBHOOK_SECRET` 后更新订单和会员状态。
- `GET /admin/me`：检查当前账号是否有后台权限。
- `GET /admin/question-portal/me`：检查当前账号是否有题库中台权限。
- `GET /admin/question-portal/dashboard`：读取今日刷题用户、近 15 分钟活跃会员和高频错题。
- `GET /admin/questions`：后台题库列表，支持科目、模块、状态、审核状态、难度和关键词筛选。
- `POST /admin/questions`：后台新增题目。
- `PATCH /admin/questions/{question_id}`：后台编辑题目。
- `PATCH /admin/questions/{question_id}/status`：发布或下架单题。
- `PATCH /admin/questions/{question_id}/review`：更新审核状态，可将审核通过题目发布。
- `PATCH /admin/questions/bulk-status`：批量发布或下架筛选 / 勾选题目。
- `POST /admin/questions/image-import/recognize`：识别上传的题库文件，支持图片、JSON、CSV、TXT、XLSX、DOCX、PDF。
- `POST /admin/questions/image-import/dry-run`：批量导入前校验草稿题。
- `POST /admin/questions/image-import/commit`：把校验通过的草稿题写入待审核状态。

## 题库中台权限

先在 Supabase SQL Editor 执行：

```text
database/question_admin_portal.sql
```

新增内部访问账号只能通过数据库白名单，不提供前端授权入口：

```sql
insert into public.question_admin_access (user_id, display_name, note)
select id, coalesce(nickname, email), '题库后台'
from public.users
where lower(email) = lower('editor@example.com')
on conflict (user_id) do update
set is_active = true,
    display_name = excluded.display_name,
    note = excluded.note,
    updated_at = now();
```

撤销权限时把对应记录的 `is_active` 更新为 `false`。原有 `role = 'admin'` 的管理员仍保留题库能力，避免影响手机端后台。
