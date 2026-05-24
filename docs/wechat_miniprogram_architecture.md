# 港研通微信小程序架构预检说明

## 目标

先建立微信小程序技术预检版，验证核心刷题闭环能在微信开发者工具中运行。当前阶段不接入微信支付、不提交审核、不改动 H5 网页端现有部署逻辑。

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

## manifest 配置

`frontend/src/manifest.json` 已新增 `mp-weixin` 配置。正式预览前需要把：

```json
"appid": ""
```

替换为微信公众平台中的小程序 AppID。

## 第一轮预检清单

- 首页是否正常显示。
- 邮箱登录是否能请求后端。
- 专项刷题是否能加载题目。
- 提交答案是否能写入记录。
- 解析是否能正常展示。
- 数学公式是否可读。
- AI 助教浮窗是否能打开、提问、返回内容。
- 错题本、收藏、复习入口是否不崩溃。
- 后台管理页是否只对管理员可见。

## 已知注意事项

- 小程序正式环境必须使用 HTTPS 合法域名，不能使用 `http://159.75.155.82`。
- 当前阶段保留邮箱、手机号登录。后续可单独增加 `wx.login` 绑定微信身份。
- 支付功能需要后续单独设计，建议等小程序主体和微信支付商户号确定后再做。
- 如果页面使用 H5 特有能力，需要使用 `#ifdef H5` / `#ifdef MP-WEIXIN` 做平台隔离。
