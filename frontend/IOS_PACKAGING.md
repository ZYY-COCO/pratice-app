# 港研通 iOS App 打包清单

本清单用于把当前 uni-app 前端补成可提交比赛演示的 iOS App 包。当前仓库负责生成 App 端资源；最终 `.ipa` 需要通过 HBuilderX/DCloud 云打包，或在 macOS/Xcode 环境中完成签名。

## 当前配置

- 应用名称：`港研通`
- DCloud AppID：见 `src/manifest.json`
- Bundle ID：`com.hmtc.app`
- App API 地址：`https://www.gangyantong.com/api`
- 图标资源：`unpackage/res/icons/`

App 端已在 `src/api/config.js` 中强制使用公网 HTTPS API，避免原生包里 `/api` 代理失效。

## 打包前需要准备

1. Apple Developer 账号。
2. iOS 证书：
   - 真机自测：iOS Development 证书 + Development provisioning profile。
   - 比赛分发：Ad Hoc 证书/Profile，或 TestFlight。
3. Bundle ID：
   - 固定使用 `com.hmtc.app`。
   - Bundle ID 必须和 provisioning profile 完全一致。
4. iPhone 真机 UDID：
   - 如果使用 Ad Hoc 或 Development 包，需要把测试设备加入 Apple Developer 后台。

## 源码与图标检查

首次准备环境：

```powershell
cd frontend
npm.cmd install
```

新增或修改 SVG 设计源后，先生成所有平台共用的透明 PNG：

```powershell
npm.cmd run icons:build
```

每次 HBuilderX 打包前都执行：

```powershell
npm.cmd run icons:check
npm.cmd run build:h5
npm.cmd run build:app
```

必须同时看到：

```text
Mobile icon audit passed: user-facing runtime uses generated PNG assets.
DONE  Build complete.
```

图标开发规则：

- 页面运行时只引用 `src/static/ui-icons/png/`。
- `src/static/ui-icons/*.svg` 只作为设计源文件；修改后运行 `npm.cmd run icons:build`。
- 不在用户端使用 CSS `mask`、CSS `filter` 给图标换色，也不使用 Emoji/Unicode 字符充当图标。
- 主题色图标统一通过 `src/utils/iconAssets.js` 选择预生成版本。
- `icons:check` 会根据生成清单拦截缺失、多余或已过期的 PNG；报错时重新运行 `npm.cmd run icons:build`。

## 本地 App 资源验证

在仓库根目录执行：

```powershell
cd frontend
npm.cmd run build:app
```

构建成功后，检查 App 构建产物目录：

```text
frontend/dist/build/app
```

这一步只验证 uni-app App 端资源能生成，不等于已经生成 `.ipa`。

## HBuilderX 云打包步骤

1. 打开 HBuilderX。
2. 导入 `frontend` 目录，不要导入仓库根目录。
3. 打开 `src/manifest.json`。
4. 确认应用名称为 `港研通`。
5. 确认 iOS 图标路径均存在，尤其是：
   - `unpackage/res/icons/1024x1024.png`
   - `unpackage/res/icons/120x120.png`
   - `unpackage/res/icons/180x180.png`
6. 菜单选择：发行 -> 原生 App - 云打包。
7. 平台选择：iOS。
8. Bundle ID 填写：`com.hmtc.app`。
9. 上传 iOS 证书和 provisioning profile。
10. Windows 上打 iOS 包时使用传统云打包；iOS 安心打包仅支持 macOS。
11. 开始云打包，等待生成 `.ipa`。

每次重新测试时建议同步增加 `versionCode`。如果只发现桌面 App 图标仍是旧图，那通常是 iOS 图标缓存；重启手机后再确认。页面内部图标应直接随新包更新。

## 比赛演示优先验证

真机安装后优先走完整学习闭环：

1. 首次打开、登录/注册、免登录保持。
2. 首页、刷题、我的、题库管理入口是否正常。
3. 专项刷题、提交答案、查看解析、收藏、错题本。
4. 学习报告和 AI 专项出题。
5. 后台题库管理、筛选、进入审核队列、编辑、发布/下架。
6. 弱网或接口失败时是否有清楚提示。
7. iPhone 安全区、底部栏、弹窗按钮文字是否不遮挡。

## 暂不急着做

- 不急着上架 App Store。
- 不急着接苹果内购。
- 不急着做正式推送证书。
- 不急着做 App Store Connect 物料，比赛阶段先保证可安装、可演示、流程稳定。
