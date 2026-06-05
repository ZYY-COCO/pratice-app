# 港研通 iOS App 打包清单

本清单用于把当前 uni-app 前端补成可提交比赛演示的 iOS App 包。当前仓库负责生成 App 端资源；最终 `.ipa` 需要通过 HBuilderX/DCloud 云打包，或在 macOS/Xcode 环境中完成签名。

## 当前配置

- 应用名称：`港研通`
- DCloud AppID：见 `src/manifest.json`
- 建议 Bundle ID：`com.gangyantong.practice`
- App API 地址：`https://www.gangyantong.com/api`
- 图标资源：`unpackage/res/icons/`

App 端已在 `src/api/config.js` 中强制使用公网 HTTPS API，避免原生包里 `/api` 代理失效。

## 打包前需要准备

1. Apple Developer 账号。
2. iOS 证书：
   - 真机自测：iOS Development 证书 + Development provisioning profile。
   - 比赛分发：Ad Hoc 证书/Profile，或 TestFlight。
3. Bundle ID：
   - 建议使用 `com.gangyantong.practice`。
   - Bundle ID 必须和 provisioning profile 完全一致。
4. iPhone 真机 UDID：
   - 如果使用 Ad Hoc 或 Development 包，需要把测试设备加入 Apple Developer 后台。

## 本地构建验证

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
8. Bundle ID 填写：`com.gangyantong.practice`。
9. 上传 iOS 证书和 provisioning profile。
10. 开始云打包，等待生成 `.ipa`。

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
