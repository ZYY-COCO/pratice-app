<template>
  <view class="wallet-detail-page" :style="themeInlineStyle">
    <MentorPageHeader title="账单详情" @back="goBack" />

    <scroll-view scroll-y class="wallet-detail-scroll">
      <view v-if="transaction" class="wallet-detail-content">
        <view class="wallet-detail-hero">
          <view class="wallet-detail-icon" :class="`tone-${transaction.iconTone || 'blue'}`">{{ transaction.iconLabel || '账' }}</view>
          <view class="wallet-detail-type">{{ transactionTypeLabel }}</view>
          <view class="wallet-detail-amount" :class="amountTone">{{ detailAmount }}</view>
          <view class="wallet-detail-status" :class="`status-${transaction.status}`">{{ statusLabel }}</view>
          <view class="wallet-detail-description">{{ transaction.description }}</view>
        </view>

        <view v-if="showExpectedWithdrawal" class="wallet-expected-card">
          <view class="wallet-expected-icon">i</view>
          <view>
            <strong>预计可提现时间</strong>
            <text>{{ transaction.availableAt }}</text>
          </view>
        </view>

        <view class="wallet-detail-card">
          <view class="wallet-detail-card-title">交易信息</view>
          <view v-for="item in detailFields" :key="item.label" class="wallet-detail-field">
            <text>{{ item.label }}</text>
            <strong>{{ item.value }}</strong>
          </view>
        </view>

        <view v-if="transaction.note" class="wallet-detail-card wallet-detail-note-card">
          <view class="wallet-detail-card-title">备注</view>
          <view class="wallet-detail-note">{{ transaction.note }}</view>
        </view>

        <view class="wallet-detail-footnote">当前交易为本地 Mock 演示记录。</view>
      </view>

      <view v-else class="wallet-detail-missing">
        <view class="wallet-detail-missing-icon">账</view>
        <strong>未找到这笔账单</strong>
        <text>该演示记录可能已失效，请返回钱包重新查看。</text>
        <button @tap="goBack">返回钱包</button>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'
import {
  getWalletTransactionById,
  walletStatusLabels,
  walletTypeLabels
} from '../../data/walletMock'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const transaction = ref(null)
const role = ref('user')

const transactionTypeLabel = computed(() => walletTypeLabels[transaction.value?.type] || '钱包账单')
const statusLabel = computed(() => walletStatusLabels[transaction.value?.status] || '待处理')
const amountTone = computed(() => Number(transaction.value?.amount || 0) >= 0 ? 'positive' : 'negative')
const detailAmount = computed(() => {
  const amount = Number(transaction.value?.amount || 0)
  const formatted = Math.abs(amount).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
  return `${amount >= 0 ? '+' : '-'}¥${formatted}`
})
const showExpectedWithdrawal = computed(() => (
  role.value === 'mentor' && transaction.value?.status === 'settling' && transaction.value?.availableAt
))
const detailFields = computed(() => {
  if (!transaction.value) return []
  const item = transaction.value
  if (role.value === 'mentor') {
    return compactFields([
      { label: '交易类型', value: transactionTypeLabel.value },
      { label: '交易状态', value: statusLabel.value },
      { label: '关联咨询订单', value: item.orderId },
      { label: '来源用户', value: item.sourceUser },
      { label: '结算状态', value: item.settlementStatus },
      { label: '到账方式', value: item.withdrawalMethod },
      { label: '交易编号', value: item.transactionId },
      { label: '创建时间', value: item.createdAt },
      { label: '完成时间', value: item.completedAt }
    ])
  }
  return compactFields([
    { label: '交易类型', value: transactionTypeLabel.value },
    { label: '交易状态', value: statusLabel.value },
    { label: '支付方式', value: item.paymentMethod },
    { label: '交易对象', value: item.counterparty },
    { label: '咨询前辈', value: item.mentor },
    { label: '订单编号', value: item.orderId },
    { label: '交易编号', value: item.transactionId },
    { label: '创建时间', value: item.createdAt },
    { label: '完成时间', value: item.completedAt }
  ])
})

onLoad((options) => {
  role.value = options?.role === 'mentor' ? 'mentor' : 'user'
  transaction.value = getWalletTransactionById(options?.id, role.value)
})

function compactFields(fields) {
  return fields.filter((item) => item.value !== undefined && item.value !== null && String(item.value).trim())
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: `/pages/wallet/index?role=${role.value}` })
    }
  })
}
</script>

<style scoped>
.wallet-detail-page { height: 100vh; height: 100dvh; overflow: hidden; background: var(--gyt-page-bg); display: flex; flex-direction: column; }
.wallet-detail-scroll { min-height: 0; flex: 1; }.wallet-detail-content { width: 100%; max-width: 760rpx; margin: 0 auto; padding: 28rpx 24rpx calc(46rpx + env(safe-area-inset-bottom)); box-sizing: border-box; }
.wallet-detail-hero { padding: 34rpx 28rpx 30rpx; border: 2rpx solid #dce8fb; border-radius: 34rpx; background: linear-gradient(160deg,#fff 0%,#eff5ff 100%); text-align: center; box-shadow: 0 18rpx 42rpx rgba(40,79,139,.09); }.wallet-detail-icon { width: 78rpx; height: 78rpx; margin: 0 auto; border: 2rpx solid var(--gyt-primary-border,#d7e5ff); border-radius: 26rpx; background: var(--gyt-primary-soft,#edf4ff); color: var(--gyt-primary,#3478f6); display: flex; align-items: center; justify-content: center; box-sizing: border-box; font-size: 28rpx; font-weight: 900; }.wallet-detail-icon.tone-mint,.wallet-detail-icon.tone-cyan { border-color: #ccebe5; background: #effaf7; color: #258c78; }.wallet-detail-icon.tone-warm { border-color: #f0ddd0; background: #fff7f1; color: #b56d49; }.wallet-detail-type { margin-top: 15rpx; color: #536983; font-size: 22rpx; font-weight: 800; }.wallet-detail-amount { margin-top: 10rpx; color: #263a54; font-size: 48rpx; line-height: 1.12; font-weight: 950; }.wallet-detail-amount.positive { color: #238272; }.wallet-detail-amount.negative { color: #3d4b5d; }.wallet-detail-status { display: inline-flex; margin-top: 15rpx; padding: 7rpx 14rpx; border-radius: 999rpx; background: #edf4ff; color: #5c7fac; font-size: 18rpx; line-height: 1.25; font-weight: 850; }.wallet-detail-status.status-settling,.wallet-detail-status.status-processing { background: #fff5e9; color: #b87832; }.wallet-detail-status.status-failed { background: #fff0f0; color: #c36161; }.wallet-detail-description { margin-top: 14rpx; color: #8898ad; font-size: 19rpx; line-height: 1.55; font-weight: 650; }
.wallet-expected-card { margin-top: 18rpx; padding: 19rpx 20rpx; border: 2rpx solid #d5ebe7; border-radius: 22rpx; background: #f6fdfa; display: flex; align-items: center; gap: 14rpx; }.wallet-expected-icon { width: 36rpx; height: 36rpx; flex: 0 0 36rpx; border-radius: 50%; background: #dff4ef; color: #27826f; display: flex; align-items: center; justify-content: center; font-size: 21rpx; font-weight: 950; }.wallet-expected-card strong,.wallet-expected-card text { display: block; }.wallet-expected-card strong { color: #477169; font-size: 20rpx; font-weight: 900; }.wallet-expected-card text { margin-top: 5rpx; color: #27826f; font-size: 22rpx; font-weight: 850; }
.wallet-detail-card { margin-top: 18rpx; padding: 28rpx 24rpx; border: 2rpx solid #e4ebf7; border-radius: 30rpx; background: rgba(255,255,255,.96); box-shadow: 0 14rpx 32rpx rgba(34,65,112,.06); }.wallet-detail-card-title { margin-bottom: 8rpx; color: #273a55; font-size: 26rpx; font-weight: 950; }.wallet-detail-field { display: flex; align-items: flex-start; justify-content: space-between; gap: 26rpx; min-height: 58rpx; padding: 17rpx 0; border-bottom: 2rpx solid #eef2f8; }.wallet-detail-field:last-child { border-bottom: 0; padding-bottom: 0; }.wallet-detail-field text { flex-shrink: 0; color: #8696a9; font-size: 20rpx; line-height: 1.45; font-weight: 650; }.wallet-detail-field strong { min-width: 0; color: #475b77; font-size: 20rpx; line-height: 1.45; font-weight: 800; text-align: right; word-break: break-all; }.wallet-detail-note-card { padding-bottom: 26rpx; }.wallet-detail-note { color: #74869e; font-size: 21rpx; line-height: 1.65; font-weight: 650; }.wallet-detail-footnote { margin: 20rpx 12rpx 0; color: #9aa7b8; text-align: center; font-size: 18rpx; line-height: 1.45; font-weight: 650; }
.wallet-detail-missing { padding: 180rpx 38rpx; text-align: center; }.wallet-detail-missing-icon { width: 90rpx; height: 90rpx; margin: 0 auto; border-radius: 30rpx; background: #edf3fc; color: #89a0bd; display: flex; align-items: center; justify-content: center; font-size: 32rpx; font-weight: 900; }.wallet-detail-missing strong,.wallet-detail-missing text { display: block; }.wallet-detail-missing strong { margin-top: 25rpx; color: #435873; font-size: 28rpx; font-weight: 900; }.wallet-detail-missing text { margin-top: 12rpx; color: #90a0b5; font-size: 20rpx; line-height: 1.6; font-weight: 650; }.wallet-detail-missing button { min-width: 190rpx; min-height: 70rpx; margin-top: 24rpx; border: 0; border-radius: 20rpx; background: var(--gyt-primary,#3478f6); color: #fff; font-size: 22rpx; font-weight: 900; }.wallet-detail-missing button::after { border: 0; }
@media(max-width:350px){.wallet-detail-content{padding-right:18rpx;padding-left:18rpx}.wallet-detail-field{gap:18rpx}.wallet-detail-field strong{font-size:19rpx}.wallet-detail-amount{font-size:43rpx}}
</style>
