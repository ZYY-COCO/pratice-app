# 港研通微信小程序架构预检说明

## 目标

建立可预览、可真机测试、可进入提审准备的小程序版本，验证微信登录和核心刷题闭环。当前阶段不接入微信支付，不改动 H5 网页端现有部署逻辑。

## 构建命令

H5 网页端：

```bash
cd frontend
npm run build:h5
```

微信小程序端：

```bash
cd frontend
npm run build:mp-weixin
```

构建完成后，用微信开发者工具导入：

```text
frontend/dist/build/mp-weixin
```

## 平台差异

### 前端共享与隔离边界

H5、微信小程序和 uni-app App 共用 `frontend/src` 中的业务页面、组件、API 请求和登录会话；三端构建产物分别输出到各自的 `dist` 子目录，构建产物不是源码，不直接编辑。

平台能力统一从 `frontend/src/platform/runtime.js` 调用。浏览器 `window` / `document` / `localStorage`、App `plus` 运行时和微信小程序不支持的外链行为不得直接散落在业务页面中。新增平台专属能力时优先扩展该适配层；仅涉及少量模板或样式差异时，使用 `#ifdef H5`、`#ifdef MP-WEIXIN` 或 `#ifdef APP-PLUS` 条件编译。

以下内容继续三端共用：

- FastAPI 接口与 Supabase 数据。
- 题库、答题、错题、收藏和学习报告业务逻辑。
- 邮箱账号、Token 会话刷新和用户资料。
- 通用组件、主题和页面主体结构。

以下内容必须按平台隔离：

- 微信登录、微信支付和小程序授权。
- 浏览器地址栏、网页 OAuth 回调和 DOM 操作。
- App 原生运行时、启动页和系统外链。
- 平台特有的文件选择、上传和权限处理。

### H5

H5 默认使用相对 API 地址：

```text
/api
```

这会继续走腾讯云 Nginx 反向代理，不改变现有网页端行为。

### 微信小程序

微信小程序默认使用完整 HTTPS API 地址：

```text
https://www.gangyantong.com/api
```

微信公众平台需要在小程序后台配置 request 合法域名：

```text
https://www.gangyantong.com
```

头像上传和后台题库文件上传还需要把同一域名加入 uploadFile 合法域名。

### 微信小程序登录

小程序端调用 `uni.login` 获取一次性 code，后端使用小程序 AppID/AppSecret 请求微信 `jscode2session`，取得 openid 后复用现有 Supabase 用户、Token、题库和学习数据体系。

微信用户在个人资料页绑定 QQ 邮箱时，后端按邮箱状态处理：

- 邮箱未注册：验证邮箱验证码后直接绑定当前微信账号。
- 邮箱已注册但未绑定微信：先返回合并预览，用户确认合并并选择保留微信或邮箱侧的昵称、头像、性别和考试目标；作答、错题、收藏、学习统计和会员数据始终合并。
- 邮箱已绑定其他微信：拒绝重复绑定，要求先在原账号解除微信绑定。

账号合并依赖数据库函数 `database/wechat_email_account_merge.sql`。必须先在 Supabase SQL Editor 执行该文件，再部署包含 `/auth/bind-wechat-email` 的后端版本。合并时保留邮箱账号作为主账号，因此不会覆盖原邮箱账号密码。

后端正式环境必须配置：

```env
WECHAT_MINIPROGRAM_APP_ID=
WECHAT_MINIPROGRAM_APP_SECRET=
WECHAT_AUTH_PASSWORD_SECRET=
```

AppSecret 和 `WECHAT_AUTH_PASSWORD_SECRET` 只允许保存在后端环境变量中，不得进入 `frontend/`、Git 或微信小程序包。

## manifest 配置

`frontend/src/manifest.json` 已配置小程序 AppID，并启用微信隐私检查。构建后的 `app.json` 由后处理脚本再次确认 `__usePrivacyCheck__` 为 `true`。

## 第一轮预检清单

- 首页是否正常显示。
- 微信快捷登录是否能自动创建或登录用户。
- 邮箱备用登录是否仍能请求后端。
- 专项刷题是否能加载题目。
- 提交答案是否能写入记录。
- 解析是否能正常展示。
- 数学公式是否可读。
- AI 助教浮窗是否能打开、提问、返回内容。
- 错题本、收藏、复习入口是否不崩溃。
- 后台管理页是否只对管理员可见。

## 已知注意事项

- 小程序正式环境必须使用 HTTPS 合法域名，不能使用 `http://159.75.155.82`。
- 小程序默认使用微信快捷登录，邮箱登录作为备用入口；手机号入口仍未开放。
- 微信登录只返回 openid，不自动获得昵称和头像；用户可在个人资料页自行设置。
- 现有邮箱账号不会在首次微信登录时自动合并；用户需要在个人资料页验证目标 QQ 邮箱并主动确认合并。
- 支付功能需要后续单独设计，建议等小程序主体和微信支付商户号确定后再做。
- 如果页面使用 H5 特有能力，需要使用 `#ifdef H5` / `#ifdef MP-WEIXIN` 做平台隔离。
