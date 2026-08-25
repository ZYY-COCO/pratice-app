# 导师咨询支付基础发布说明

更新时间：2026-08-24

## 本批范围

本批只建设渠道无关的可靠性基础，不接入微信真实扣款、退款打款或提现：

- 客户端订单幂等键与数据库唯一约束。
- 预约时段 `held` 原子预占、支付倒计时、过期释放。
- 支付确认与时段 `booked` 在同一数据库事务完成。
- 迟到支付自动关闭订单并进入全额原路退款队列。
- 聊天消息同键同内容返回原消息，同键不同内容返回 `409`，历史正文不再被覆盖。
- 用户通知 outbox、唯一事件键、后台领取与指数退避重试。
- `demo` / `real` 完全隔离的不可变双向账本与真实钱包只读 API。
- 真实提现关闭；前端不再生成本地假提现记录。

## 发布顺序

本批必须先迁移数据库，再部署后端和前端。应用代码会读取新增字段和 RPC，顺序反过来会让咨询订单接口暂时不可用。

1. 在 Supabase SQL Editor 执行：

   ```text
   database/mentor_consultation_payment_foundation.sql
   ```

2. 确认 SQL 整体执行成功后，再发布应用代码。
3. 保持生产环境真实资金开关关闭：

   ```text
   MENTOR_CONSULTATION_REAL_PAYMENT_ENABLED=false
   MENTOR_CONSULTATION_DEMO_PAYMENT_ENABLED=false
   WALLET_WITHDRAWAL_ENABLED=false
   ```

4. 本地联调 Demo 时，只在本地后端环境显式设置：

   ```text
   MENTOR_CONSULTATION_DEMO_PAYMENT_ENABLED=true
   MENTOR_CONSULTATION_REAL_PAYMENT_ENABLED=false
   WALLET_WITHDRAWAL_ENABLED=false
   ```

## 迁移影响

- 旧版 `pending_payment + unpaid/failed` 订单没有可信的时段预占信息，迁移会将其支付截止时间设为立即到期；后台生命周期会关闭这些未支付订单并释放时段。
- 已支付、服务中、已完成、退款中的订单不会因上述清理被取消。
- 历史 `DEMO-` / `MOCK-` 支付流水会回填为 `demo`，不会进入生产真实余额。

## 微信商户资质通过后的接入点

届时无需改造订单和账本状态机，只需完成：

1. 微信下单适配器，返回支付跳转参数。
2. 微信回调签名校验，并映射到现有支付回调请求。
3. 退款执行器领取 `mentor_payment_operation_outbox` 中的退款命令。
4. 配置支付 provider、支付跳转、回调密钥后完成沙箱回归。
5. 最后才打开 `MENTOR_CONSULTATION_REAL_PAYMENT_ENABLED`。
6. 提现打款能力单独验收完成后，最后打开 `WALLET_WITHDRAWAL_ENABLED`。

## 验收清单

- 同一 `client_order_id` 重试只返回一个订单。
- 同一预约时段并发下单，仅一个订单获得 `held`。
- 预占到期后订单自动关闭，时段恢复可用。
- 支付确认后预约时段从 `held` 原子变为 `booked`。
- 迟到支付进入 `refunding`，退款命令只入队一次。
- 同一 `client_message_id`、同正文重试返回原消息；不同正文返回 `409`。
- 通知投递失败后 outbox 增加重试次数，成功后只生成一条用户通知。
- 生产钱包只查询 `real`；本地 Demo 只查询 `demo`。
- 生产提现按钮保持禁用，且不写本地记录。
