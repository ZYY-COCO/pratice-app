# 港澳台考研初试刷题 App 前端

## 页面范围

当前 MVP 前端已包含：

- 首页：`src/pages/home/index.vue`
- 版本选择页：`src/pages/version/index.vue`
- 科目页：`src/pages/subjects/index.vue`
- 专项刷题页：`src/pages/practice/index.vue`

## API 配置

后端地址由 Vite 环境变量控制：

```js
VITE_API_BASE_URL=http://127.0.0.1:8000
```

本地开发默认读取 `frontend/.env.development`，指向：

```text
http://127.0.0.1:8000
```

H5 内测部署时，在 Vercel / Netlify / Cloudflare Pages 等平台配置：

```text
VITE_API_BASE_URL=https://你的后端公网域名
```

不要在前端配置 Supabase `service_role` key。前端只通过 FastAPI 调接口，所有 Supabase 密钥都应留在后端环境变量中。

## H5 构建

```bash
npm run build:h5
```

构建产物目录：

```text
dist/build/h5
```

如果部署平台的项目根目录设置为 `frontend`，发布目录填写 `dist/build/h5`。
