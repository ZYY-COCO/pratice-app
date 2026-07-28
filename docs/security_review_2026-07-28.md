# 2026-07-28 安全审查与登录稳定性报告

## 范围与边界

本次审查覆盖前端 H5 / uni-app 源码、FastAPI 路由与依赖、Supabase SQL、Nginx 与部署脚本、已锁定的前端依赖。未读取任何 `.env` 内容，未连接生产数据库、Supabase 控制台或云服务器，因此线上环境变量、已执行的 SQL 迁移、Nginx 实际生效配置仍需在部署时复核。

## 已修复

### 登录会话被误判失效（高优先级，可用性）

刷题页曾把进入页面时读取的 access token 手动写入请求头。共享请求层刷新令牌后，旧请求头会覆盖新 token；重试仍使用旧 token，导致用户正在刷题时被带回登录页。

修复措施：

- 刷题相关请求不再自行传递 `Authorization`，统一由 `frontend/src/api/http.js` 注入最新 token。
- 共享请求层忽略非空的调用方 `Authorization` 覆盖，避免未来出现相同的旧 token 覆盖问题；保留空值作为匿名接口的显式标记。
- token 刷新失败时，只有服务端明确以 `401/403` 拒绝 refresh token 才清空会话并跳转登录。网络超时、网关暂时故障等可恢复错误会保留会话并允许后续请求重试。
- AI 训练这一可取消的长请求也会在真正发出前检查、刷新接近到期的 token。

### 跨域与认证接口防护（高优先级）

- 后端和首次部署模板不再默认 `API_CORS_ORIGINS=*`，改为仅允许 `https://www.gangyantong.com` 与 `https://gangyantong.com`。
- Nginx 对 `/api/auth/` 增加每 IP 20 次/分钟、突发 12 次的限流，覆盖密码登录、验证码和 refresh 请求，不影响高频刷题/交卷接口。
- HTTPS 站点增加 HSTS、`X-Content-Type-Options`、禁止嵌入和 Referrer Policy，并隐藏 Nginx 版本。
- 认证、资料与头像接口不再把 SMTP、Supabase 等内部异常文本回传给客户端；详细错误仅写入服务端日志。

## 审查结论

### 已确认的正向控制

- 前端没有直接使用 Supabase 浏览器 SDK；service-role key 仅应存在于后端环境变量。
- 受保护 API 普遍通过 `get_current_user_id` 校验 Supabase access token；管理与题库中台接口有额外管理员/白名单依赖。
- SQL 源码对用户数据、验证码、题库中台等表启用了 RLS；`security definer` 函数指定了 `search_path` 并限制到 `service_role`。
- 头像上传检查文件大小和 PNG/JPEG/WebP 文件头；公式 SVG 与 KaTeX 渲染分别使用 HTML 转义和 `trust: false`。
- 代码仓库忽略 `.env` 与 `.env.*`，本次路径扫描未发现已提交的密钥值。

### 待处理风险

| 优先级 | 风险 | 建议 |
| --- | --- | --- |
| P1 | 前端依赖审计报告 9 个 high、17 个 moderate、3 个 low；重点包括 Vite 5.2.8、esbuild、`@intlify/core-base`、PostCSS、`adm-zip` 与 `ws` 的传递依赖。 | 以可兼容的新版 uni-app alpha 为单位升级，而非单独强升 Vite；升级后同时构建 H5、微信小程序和 App。 |
| P1 | 邮箱/手机 6 位验证码只有发送冷却，没有“错误次数上限/锁定”机制。反向代理限流只能降低速率，不能绑定单个验证码的猜测次数。 | 为验证码表增加失败计数、最大 5 次尝试和锁定时间；服务端以原子更新执行校验。 |
| P1 | 线上现有 `backend.env` 可能仍配置 `API_CORS_ORIGINS=*`；代码默认值不会覆盖已有环境变量。 | 部署前手动改为两个正式域名，并用 `nginx -t` 验证后重启后端/重载 Nginx。 |
| P2 | H5 会把 access / refresh token 持久化在浏览器存储中。若发生同源 XSS，令牌可能被窃取。 | 中长期改为 HttpOnly + Secure + SameSite cookie 的 BFF 会话；短期新增严格 CSP 前先在预发布环境验证。 |
| P2 | 注册/找回密码接口会通过不同的状态码和文案暴露邮箱是否已注册。 | 对外统一返回成功提示和通用错误文案。 |
| P2 | `SMS_MOCK_RETURN_CODE=true` 会将短信验证码返回给调用方，仅适合本地测试。 | 生产环境保持为 `false`，并在发布前做环境变量检查。 |
| P2 | 后端允许用户资料写入任意 `avatar_url`；虽然服务端不会抓取该 URL，但其他用户加载排行榜头像时会向第三方发起图片请求。 | 只允许预置头像或本项目 Supabase Storage 域名；必要时通过自有图片代理。 |

## 验证记录

- `node --check frontend/src/api/http.js`、`node --check frontend/src/api/ai.js` 通过。
- `python -m compileall -q backend/app` 通过。
- `frontend/node_modules/.bin/uni.cmd build -p h5` 于 2026-07-28 通过。构建保留了两条既有的静态 SVG 运行时解析提示，不影响构建完成。
- `pnpm audit --prod --json` 已执行；结果见上方依赖风险，未自动升级依赖，避免破坏当前 uni-app alpha 组合。
- 本机未安装 Nginx，无法执行 `nginx -t`；部署服务器必须在 reload 前执行该命令。
- bundled Python 未包含 `pip-audit`，后端第三方依赖仍需在隔离环境或 CI 中补跑 CVE 审计。

## 发布后回归

1. 用即将过期的 access token 打开刷题页，确认首个拉题、提交答案都成功，且 local storage 中的 token 已更新。
2. 模拟 refresh 请求超时，确认页面保留登录态并显示可重试错误；网络恢复后下一次请求可正常续期。
3. 让 refresh token 返回 401，确认只出现一次“登录已过期”提示并只跳转一次登录页。
4. 在服务器确认 `API_CORS_ORIGINS` 是两个正式域名，执行 `sudo nginx -t` 后再 `sudo systemctl reload nginx`。
5. 在浏览器检查首页响应中的 HSTS、`X-Content-Type-Options`、`X-Frame-Options` 与 `Referrer-Policy`；连续调用认证接口超过限额时应返回 429。
