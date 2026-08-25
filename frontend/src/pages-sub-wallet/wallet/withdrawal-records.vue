<template>
  <view class="wallet-records-page" :style="themeInlineStyle">
    <MentorPageHeader title="提现记录" @back="goBack" />

    <scroll-view scroll-y class="wallet-records-scroll">
      <view class="wallet-records-content">
        <view class="wallet-records-intro">
          <view class="wallet-records-intro-icon">提</view>
          <view>
            <strong>我的提现记录</strong>
            <text>申请状态会在到账处理完成后更新</text>
          </view>
        </view>

        <view class="wallet-records-filter-list">
          <button
            v-for="item in filters"
            :key="item.value"
            :class="{ active: activeFilter === item.value }"
            @tap="activeFilter = item.value"
          >
            {{ item.label }}
          </button>
        </view>

        <view v-if="records.length" class="wallet-records-card">
          <WalletTransactionRow
            v-for="transaction in records"
            :key="transaction.id"
            :transaction="transaction"
            @select="openTransactionDetail"
          />
        </view>

        <view v-else class="wallet-records-empty">
          <view>提</view>
          <strong>暂无提现记录</strong>
          <text>{{ withdrawalEnabled ? '发起提现申请后，记录会显示在这里。' : '微信支付商户资质与打款能力接通后才会开放提现。' }}</text>
          <button v-if="withdrawalEnabled" @tap="openWithdraw">去提现</button>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import WalletTransactionRow from '../../components/WalletTransactionRow.vue'
import { fetchWalletSummary } from '../../api/wallet'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const activeFilter = ref('all')
const allRecords = ref([])
const walletRole = ref('user')
const withdrawalEnabled = ref(false)
const filters = [
  { value: 'all', label: '全部' },
  { value: 'processing', label: '处理中' },
  { value: 'success', label: '提现成功' },
  { value: 'failed', label: '提现失败' }
]
const records = computed(() => {
  if (activeFilter.value === 'all') return allRecords.value
  if (activeFilter.value === 'success') return allRecords.value.filter((item) => item.status === 'success')
  return allRecords.value.filter((item) => item.status === activeFilter.value)
})

onLoad((options) => {
  walletRole.value = options?.role === 'mentor' ? 'mentor' : 'user'
})

onShow(() => {
  void loadWithdrawalRecords()
})

async function loadWithdrawalRecords() {
  try {
    const wallet = await fetchWalletSummary({
      role: walletRole.value,
      ...(import.meta.env.DEV ? { mode: 'demo' } : {})
    })
    withdrawalEnabled.value = Boolean(wallet.withdrawalEnabled)
    allRecords.value = wallet.transactions.filter((item) => ['withdraw', 'withdraw_fail'].includes(item.type))
  } catch (error) {
    allRecords.value = []
    withdrawalEnabled.value = false
  }
}

function openTransactionDetail(transaction) {
  uni.navigateTo({
    url: `/pages-sub-wallet/wallet/transaction-detail?id=${encodeURIComponent(transaction.id)}&role=${walletRole.value}`
  })
}

function openWithdraw() {
  uni.redirectTo({ url: `/pages-sub-wallet/wallet/withdraw?role=${walletRole.value}` })
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: `/pages-sub-wallet/wallet/index?role=${walletRole.value}` })
    }
  })
}
</script>

<style scoped>
.wallet-records-page { height: 100vh; height: 100dvh; overflow: hidden; background: var(--gyt-page-bg); display: flex; flex-direction: column; }.wallet-records-scroll { min-height: 0; flex: 1; }.wallet-records-content { width: 100%; max-width: 760rpx; margin: 0 auto; padding: 28rpx 24rpx calc(46rpx + env(safe-area-inset-bottom)); box-sizing: border-box; }
.wallet-records-intro { padding: 24rpx; border: 2rpx solid rgba(229,226,224,.94); border-radius: 30rpx; background: rgba(255,255,255,.94); display: flex; align-items: center; gap: 16rpx; box-shadow: 0 15rpx 34rpx rgba(48,42,38,.055); }.wallet-records-intro-icon { width: 64rpx; height: 64rpx; flex: 0 0 64rpx; border-radius: 22rpx; background: #dff4ef; color: #278a78; display: flex; align-items: center; justify-content: center; font-size: 25rpx; font-weight: 900; }.wallet-records-intro strong,.wallet-records-intro text { display: block; }.wallet-records-intro strong { color: #39685f; font-size: 26rpx; font-weight: 950; }.wallet-records-intro text { margin-top: 7rpx; color: #78928e; font-size: 19rpx; line-height: 1.4; font-weight: 650; }
.wallet-records-filter-list { display: flex; gap: 10rpx; margin-top: 20rpx; overflow-x: auto; white-space: nowrap; }.wallet-records-filter-list button { min-width: 94rpx; min-height: 50rpx; margin: 0; padding: 0 15rpx; border: 2rpx solid #e0e9f5; border-radius: 16rpx; background: rgba(255,255,255,.84); color: #7b8da3; font-size: 19rpx; line-height: 46rpx; font-weight: 750; }.wallet-records-filter-list button::after { border: 0; }.wallet-records-filter-list button.active { border-color: #278a78; background: #edf8f5; color: #278a78; }
.wallet-records-card { margin-top: 18rpx; padding: 10rpx 24rpx; border: 2rpx solid #e4ebf7; border-radius: 30rpx; background: rgba(255,255,255,.96); box-shadow: 0 14rpx 32rpx rgba(34,65,112,.06); }.wallet-records-empty { padding: 126rpx 26rpx; text-align: center; }.wallet-records-empty>view { width: 86rpx; height: 86rpx; margin: 0 auto; border-radius: 29rpx; background: #edf5f3; color: #8fb2aa; display: flex; align-items: center; justify-content: center; font-size: 30rpx; font-weight: 900; }.wallet-records-empty strong,.wallet-records-empty text { display: block; }.wallet-records-empty strong { margin-top: 22rpx; color: #50647f; font-size: 26rpx; font-weight: 900; }.wallet-records-empty text { margin-top: 10rpx; color: #92a0b2; font-size: 19rpx; line-height: 1.6; font-weight: 650; }.wallet-records-empty button { min-width: 180rpx; min-height: 70rpx; margin-top: 24rpx; border: 0; border-radius: 20rpx; background: #278a78; color: #fff; font-size: 22rpx; font-weight: 900; }.wallet-records-empty button::after { border: 0; }
@media(max-width:350px){.wallet-records-content{padding-right:18rpx;padding-left:18rpx}.wallet-records-card{padding-right:20rpx;padding-left:20rpx}.wallet-records-filter-list button{min-width:86rpx;padding:0 12rpx}}
</style>
