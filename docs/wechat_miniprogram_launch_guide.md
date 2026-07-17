# 港研通微信小程序登录与上架操作指南

更新日期：2026-07-17。

## 当前代码状态

- 小程序登录页默认展示微信快捷登录，邮箱登录保留为老用户备用入口。
- 小程序使用 `uni.login` 获取 code，后端使用微信 `jscode2session` 换取 openid。
- 微信用户复用现有 Supabase 用户、Token、题库和学习数据体系。
- access token 到期前会通过 `/auth/refresh` 自动续期；多个并发请求只执行一次刷新。
- refresh token 失效时只清理一次会话并跳转一次登录页。
- 微信隐私检查已启用，头像和后台文件选择前会触发隐私授权。
- H5 和 App 不包含小程序专属登录布局、`uni.login` 分支或微信隐私 API。
- 2026-07-17 只读检查显示正式后端健康，但正式 OpenAPI 尚未包含 `/auth/refresh`，说明本轮后端代码仍需部署。

## 上线前必须人工完成

### 1. 微信公众平台取得小程序密钥

1. 登录微信公众平台，进入当前小程序。
2. 在开发设置中确认小程序 AppID 与 `frontend/src/manifest.json` 一致。
3. 生成或查看小程序 AppSecret。
4. AppSecret 只能填写到服务器环境变量，不得粘贴到聊天、Git、前端源码或微信开发者工具代码中。

### 2. 配置服务器合法域名

在微信公众平台的服务器域名配置中加入：

- request 合法域名：`https://www.gangyantong.com`
- uploadFile 合法域名：`https://www.gangyantong.com`

域名必须使用 HTTPS，不能填写 IP、路径或 `/api` 后缀。

### 3. 完成用户隐私保护指引

1. 在微信公众平台进入用户隐私保护指引设置。
2. 隐私政策页面填写：`https://www.gangyantong.com/privacy.html`。
3. 按实际功能声明处理的信息和用途，至少核对：
   - 微信用户标识：用于创建和保持登录账号。
   - 用户选择的照片：用于上传个人头像。
   - 用户选择的文件或照片：仅管理员题库导入功能使用。
4. 保存并提交平台要求的隐私指引审核或确认。

### 4. 配置腾讯云后端环境变量

SSH 登录服务器后先备份环境文件：

```bash
sudo cp /opt/gangyantong/backend.env "/opt/gangyantong/backend.env.$(date +%Y%m%d%H%M%S).bak"
sudo nano /opt/gangyantong/backend.env
```

加入或更新：

```env
WECHAT_MINIPROGRAM_APP_ID=填写小程序AppID
WECHAT_MINIPROGRAM_APP_SECRET=填写小程序AppSecret
WECHAT_AUTH_PASSWORD_SECRET=填写独立随机密钥
```

随机密钥可在服务器执行以下命令生成，然后复制结果到 `WECHAT_AUTH_PASSWORD_SECRET`：

```bash
python3 -c 'import secrets; print(secrets.token_urlsafe(48))'
```

保存后确认文件权限：

```bash
sudo chmod 600 /opt/gangyantong/backend.env
```

### 5. 部署本轮后端代码

部署脚本使用远端 `main` 分支，因此必须先确保本轮代码已提交并推送到 GitHub。不要只修改服务器目录，部署脚本会用远端分支覆盖服务器代码。

推荐方式：推送到 `main` 后，在 GitHub Actions 中确认 `Tencent Cloud Deploy` 成功。

需要手动触发服务器部署时：

```bash
cd /opt/gangyantong/app
BRANCH=main bash deploy/tencent-cloud/deploy.sh
```

部署后检查：

```bash
curl -fsS https://www.gangyantong.com/api/health
curl -fsS https://www.gangyantong.com/api/openapi.json | grep -q '"/auth/refresh"' && echo refresh-route-ok
sudo systemctl status gangyantong-backend --no-pager
```

期望看到 `{"status":"ok"}`、`refresh-route-ok` 和服务状态 `active (running)`。

### 6. 微信开发者工具真机验证

1. 执行 `cd frontend && npm run build:mp-weixin`。
2. 微信开发者工具导入 `frontend/dist/build/mp-weixin`。
3. 确认项目 AppID 正确，清除全部缓存后重新编译。
4. 点击“预览”，使用手机微信扫码。
5. 首次点击“使用微信登录”，应进入首页并显示微信用户。
6. 退出后再次微信登录，应回到同一账号，错题、收藏和学习记录保持不变。
7. 点击《用户隐私保护指引》，应打开微信平台配置的指引。
8. 在个人资料选择头像时，应先出现隐私授权，再能选择照片。
9. 使用老邮箱账号测试备用登录，确认 H5/App 原账号仍可使用。
10. 检查控制台，不应持续出现 401、重复登录跳转或 WXML 解析错误。

## 账号策略提醒

微信 `wx.login` 不会提供用户邮箱，因此无法安全地自动判断一个微信用户是否就是某个已有邮箱用户。当前策略是：

- 新用户优先使用微信快捷登录。
- 已有邮箱账号的老用户继续选择“已有邮箱账号？使用邮箱密码登录”。
- 不自动合并微信账号和邮箱账号，避免误合并他人数据。

如果后续需要“一人一个跨平台账号”，应单独开发经过邮箱验证码确认的账号绑定和数据迁移流程，不应仅按昵称或头像自动合并。

## 提审前最终检查

- 微信登录、邮箱备用登录、刷新登录态均通过真机测试。
- request / uploadFile 合法域名已生效。
- 用户隐私保护指引已配置并能从小程序打开。
- 普通用户看不到后台管理入口。
- 管理员文件导入、头像上传和核心刷题闭环可用。
- 小程序体验版没有持续红色错误。
- 服务类目、功能说明、隐私声明和实际功能一致。
- 上传版本后先设为体验版复测，再提交审核。
