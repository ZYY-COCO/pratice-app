# 港澳台考研初试刷题 App 前端

## 页面范围

当前 MVP 前端已包含：

- 首页：`src/pages/home/index.vue`
- 版本选择页：`src/pages/version/index.vue`
- 科目页：`src/pages/subjects/index.vue`
- 专项刷题页：`src/pages/practice/index.vue`
- 会员中心：`src/pages/pro/index.vue`
- 个人资料：`src/pages/profile/index.vue`
- 排行榜：`src/pages/leaderboard/index.vue`
- 练习历史：`src/pages/history/index.vue`
- 收藏夹：`src/pages/favorites/index.vue`
- 后台管理：`src/pages/admin/index.vue`
- 统一登录页：`src/pages/login/index.vue`（题库管理白名单用户会自动进入中台）
- 桌面题库中台：`src/pages/admin/question-desktop.vue`
- 题库批量导入：`src/pages/admin/question-image-import.vue`

后台管理仅管理员可见，包含用户、反馈、题库管理、题目编辑、审核队列、发布 / 下架和批量导入待审核流程。

桌面题库中台没有用户端菜单入口。请通过 H5 统一登录页登录：

```text
/#/pages/login/index
```

登录后由后端检查 `question_admin_access` 数据库白名单；白名单用户自动进入桌面题库中台，其他用户照常进入 App。旧的 `/#/pages/admin/question-login` 地址仅保留自动跳转兼容，不再显示独立登录页。该桌面页面独立于现有手机端后台，不替换 `src/pages/admin/index.vue`。

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

## App 打包

- Android 内测 APK：见 [APK_PACKAGING.md](APK_PACKAGING.md)
- iOS 比赛演示包：见 [IOS_PACKAGING.md](IOS_PACKAGING.md)
