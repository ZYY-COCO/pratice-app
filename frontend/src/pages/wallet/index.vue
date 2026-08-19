<template>
  <view class="wallet-page" :style="themeInlineStyle">
    <MentorPageHeader title="我的钱包" @back="goBack" />

    <scroll-view scroll-y class="wallet-scroll">
      <view class="wallet-content">
        <view class="wallet-overview-card" :class="`role-${walletRole}`">
          <view class="wallet-overview-glow"></view>
          <view class="wallet-overview-head">
            <view>
              <view class="wallet-overview-label">{{ balanceLabel }}</view>
              <view class="wallet-overview-amount">{{ mainBalance }}</view>
            </view>
            <view class="wallet-overview-actions">
              <button class="wallet-secondary-action" @tap="handleRecharge">充值</button>
              <button class="wallet-primary-action" @tap="openWithdraw">提现</button>
            </view>
          </view>
          <view class="wallet-overview-divider"></view>
          <view class="wallet-overview-stats">
            <view v-for="item in overviewStats" :key="item.label" class="wallet-overview-stat">
              <text>{{ item.label }}</text>
              <strong>{{ item.value }}</strong>
            </view>
          </view>
        </view>

        <view v-if="isMentor" class="wallet-settlement-tip" @tap="openSettlementRules">
          <view class="wallet-tip-icon">i</view>
          <view class="wallet-tip-copy">
            <strong>结算说明</strong>
            <text>咨询完成后进入待结算，满 3 天自动转入可提现余额。</text>
          </view>
          <view class="wallet-tip-arrow">›</view>
        </view>

        <view class="wallet-bill-card">
          <view class="wallet-section-heading">
            <view>
              <view class="wallet-section-title">账单</view>
              <view class="wallet-section-subtitle">资金变化清晰可追溯</view>
            </view>
            <button class="wallet-bill-all" @tap="activeFilter = 'all'">查看全部</button>
          </view>

          <scroll-view scroll-x class="wallet-filter-scroll" :show-scrollbar="false">
            <view class="wallet-filter-list">
              <button
                v-for="item in filterOptions"
                :key="item.value"
                class="wallet-filter"
                :class="{ active: activeFilter === item.value }"
                @tap="activeFilter = item.value"
              >
                {{ item.label }}
              </button>
            </view>
          </scroll-view>

          <view v-if="transactionGroups.length" class="wallet-month-list">
            <view v-for="group in transactionGroups" :key="group.monthKey" class="wallet-month-group">
              <view class="wallet-month-heading">
                <text>{{ group.label }}</text>
                <view>{{ group.summary }}</view>
              </view>
              <WalletTransactionRow
                v-for="transaction in group.transactions"
                :key="transaction.id"
                :transaction="transaction"
                @select="openTransactionDetail"
              />
            </view>
          </view>

          <view v-else class="wallet-empty-state">
            <view class="wallet-empty-icon">账</view>
            <strong>{{ emptyTitle }}</strong>
            <text>{{ emptyCopy }}</text>
          </view>
        </view>

        <view class="wallet-bottom-note">当前为本地 Mock 演示，未接入真实充值、支付或打款。</view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import WalletTransactionRow from '../../components/WalletTransactionRow.vue'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'
import {
  formatWalletAmount,
  getStoredWalletRole,
  getWalletMockByRole,
  matchesWalletFilter,
  setStoredWalletRole,
  walletFilterOptions
} from '../../data/walletMock'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const walletRole = ref(getStoredWalletRole())
const activeFilter = ref('all')

const wallet = computed(() => getWalletMockByRole(walletRole.value))
const isMentor = computed(() => walletRole.value === 'mentor')
const filterOptions = computed(() => walletFilterOptions[walletRole.value] || walletFilterOptions.user)
const balanceLabel = computed(() => isMentor.value ? '可提现余额' : '钱包余额')
const mainBalance = computed(() => formatWalletAmount(isMentor.value ? wallet.value.withdrawableBalance : wallet.value.balance))
const overviewStats = computed(() => {
  if (isMentor.value) {
    return [
      { label: '待结算', value: formatWalletAmount(wallet.value.pendingSettlement) },
      { label: '本月收入', value: formatWalletAmount(wallet.value.monthlyIncome) },
      { label: '累计收入', value: formatWalletAmount(wallet.value.totalIncome) }
    ]
  }
  return [
    { label: '本月支出', value: formatWalletAmount(wallet.value.monthlyExpense) },
    { label: '本月退款', value: formatWalletAmount(wallet.value.monthlyRefund) },
    { label: '累计支付', value: formatWalletAmount(wallet.value.totalPaid) }
  ]
})
const filteredTransactions = computed(() => wallet.value.transactions.filter((item) => (
  matchesWalletFilter(item, activeFilter.value, walletRole.value)
)))
const transactionGroups = computed(() => {
  const groups = new Map()
  filteredTransactions.value.forEach((transaction) => {
    const monthKey = transaction.monthKey || 'unknown'
    if (!groups.has(monthKey)) groups.set(monthKey, [])
    groups.get(monthKey).push(transaction)
  })
  return [...groups.entries()]
    .sort(([left], [right]) => right.localeCompare(left))
    .map(([monthKey, transactions]) => ({
      monthKey,
      label: formatMonthLabel(monthKey),
      summary: getMonthSummary(transactions, walletRole.value),
      transactions
    }))
})
const emptyTitle = computed(() => {
  if (activeFilter.value !== 'all') return '暂无匹配账单'
  return isMentor.value ? '暂无钱包收入' : '暂无账单记录'
})
const emptyCopy = computed(() => (
  isMentor.value
    ? '完成咨询后，收入会先进入待结算，再转入可提现余额。'
    : '完成咨询支付或收到退款后，账单会显示在这里。'
))

onLoad((options) => {
  if (options?.role === 'mentor' || options?.role === 'user') {
    walletRole.value = setStoredWalletRole(options.role)
  }
})

onShow(() => {
  walletRole.value = getStoredWalletRole()
})

function handleRecharge() {
  uni.showToast({ title: '钱包充值功能即将开放', icon: 'none' })
}

function openWithdraw() {
  uni.navigateTo({ url: `/pages/wallet/withdraw?role=${walletRole.value}` })
}

function openSettlementRules() {
  uni.showModal({
    title: '结算规则说明',
    content: '咨询完成后，收入先进入待结算；待结算期为 3 天；结算完成后自动转入可提现余额。提现申请提交后，后续将支持微信 / 支付宝到账。',
    showCancel: false,
    confirmText: '我知道了'
  })
}

function openTransactionDetail(transaction) {
  if (!transaction?.id) return
  uni.navigateTo({
    url: `/pages/wallet/transaction-detail?id=${encodeURIComponent(transaction.id)}&role=${walletRole.value}`
  })
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/home/index?tab=profile' })
    }
  })
}

function formatMonthLabel(monthKey) {
  const match = String(monthKey || '').match(/^(\d{4})-(\d{2})$/)
  return match ? `${match[1]}年${Number(match[2])}月` : '最近账单'
}

function getMonthSummary(transactions, role) {
  if (role === 'mentor') {
    const income = transactions
      .filter((item) => item.type === 'consult_income')
      .reduce((sum, item) => sum + Math.max(0, Number(item.amount || 0)), 0)
    const withdrawn = transactions
      .filter((item) => item.type === 'withdraw' && item.status !== 'failed')
      .reduce((sum, item) => sum + Math.abs(Number(item.amount || 0)), 0)
    return `收入 ${formatWalletAmount(income)}　提现 ${formatWalletAmount(withdrawn)}`
  }
  const expense = transactions
    .filter((item) => Number(item.amount || 0) < 0)
    .reduce((sum, item) => sum + Math.abs(Number(item.amount || 0)), 0)
  const refund = transactions
    .filter((item) => item.type === 'refund')
    .reduce((sum, item) => sum + Math.max(0, Number(item.amount || 0)), 0)
  return `支出 ${formatWalletAmount(expense)}　退款 ${formatWalletAmount(refund)}`
}
</script>

<style scoped>
.wallet-page { height: 100vh; height: 100dvh; overflow: hidden; background: var(--gyt-page-bg); display: flex; flex-direction: column; }
.wallet-scroll { min-height: 0; flex: 1; }
.wallet-content { width: 100%; max-width: 760rpx; margin: 0 auto; padding: 24rpx 24rpx calc(46rpx + env(safe-area-inset-bottom)); box-sizing: border-box; }
.wallet-overview-card { position: relative; overflow: hidden; padding: 32rpx 30rpx 26rpx; border: 2rpx solid rgba(201,219,253,.9); border-radius: 34rpx; background: linear-gradient(135deg,#fafdff 0%,#e8f1ff 58%,#dceafe 100%); box-shadow: 0 18rpx 42rpx rgba(52,120,246,.14); }.wallet-overview-card.role-mentor { border-color: #c8e6e1; background: linear-gradient(135deg,#fcfffe 0%,#ebf9f7 57%,#def3ee 100%); box-shadow: 0 18rpx 42rpx rgba(34,138,118,.12); }.wallet-overview-glow { position: absolute; right: -60rpx; top: -80rpx; width: 260rpx; height: 260rpx; border-radius: 50%; background: rgba(255,255,255,.58); }.wallet-overview-head { position: relative; display: flex; align-items: flex-start; justify-content: space-between; gap: 16rpx; }.wallet-overview-label { color: #60769a; font-size: 22rpx; line-height: 1.35; font-weight: 750; }.wallet-overview-amount { margin-top: 12rpx; color: #18365f; font-size: 55rpx; line-height: 1.05; font-weight: 950; letter-spacing: -.8rpx; }.role-mentor .wallet-overview-label { color: #54847c; }.role-mentor .wallet-overview-amount { color: #285d55; }.wallet-overview-actions { flex-shrink: 0; display: flex; gap: 10rpx; margin-top: 8rpx; }.wallet-primary-action,.wallet-secondary-action { min-width: 90rpx; min-height: 62rpx; margin: 0; padding: 0 16rpx; border: 0; border-radius: 19rpx; font-size: 22rpx; line-height: 62rpx; font-weight: 900; }.wallet-primary-action { background: var(--gyt-primary,#3478f6); color: #fff; box-shadow: 0 10rpx 22rpx var(--gyt-primary-shadow,rgba(52,120,246,.2)); }.wallet-secondary-action { border: 2rpx solid var(--gyt-primary-border,#d7e5ff); background: rgba(255,255,255,.78); color: var(--gyt-primary,#3478f6); box-sizing: border-box; }.wallet-primary-action::after,.wallet-secondary-action::after,.wallet-bill-all::after,.wallet-filter::after { border: 0; }.role-mentor .wallet-primary-action { background: #278a78; box-shadow: 0 10rpx 22rpx rgba(39,138,120,.18); }.role-mentor .wallet-secondary-action { border-color: #c7e5df; color: #278a78; }.wallet-overview-divider { position: relative; height: 2rpx; margin-top: 28rpx; background: rgba(106,143,200,.18); }.role-mentor .wallet-overview-divider { background: rgba(75,142,130,.18); }.wallet-overview-stats { position: relative; display: grid; grid-template-columns: repeat(3,minmax(0,1fr)); gap: 12rpx; margin-top: 24rpx; }.wallet-overview-stat { min-width: 0; }.wallet-overview-stat text,.wallet-overview-stat strong { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.wallet-overview-stat text { color: #788da9; font-size: 18rpx; font-weight: 650; }.wallet-overview-stat strong { margin-top: 9rpx; color: #314e75; font-size: 24rpx; line-height: 1.25; font-weight: 900; }.role-mentor .wallet-overview-stat text { color: #71948e; }.role-mentor .wallet-overview-stat strong { color: #377166; }
.wallet-settlement-tip { margin-top: 18rpx; padding: 18rpx 20rpx; border: 2rpx solid #d5ebe7; border-radius: 22rpx; background: rgba(246,253,251,.9); display: flex; align-items: center; gap: 14rpx; }.wallet-tip-icon { width: 34rpx; height: 34rpx; flex: 0 0 34rpx; border-radius: 50%; background: #dff4ef; color: #26836f; display: flex; align-items: center; justify-content: center; font-size: 21rpx; font-weight: 950; }.wallet-tip-copy { min-width: 0; flex: 1; }.wallet-tip-copy strong,.wallet-tip-copy text { display: block; }.wallet-tip-copy strong { color: #40685f; font-size: 21rpx; font-weight: 900; }.wallet-tip-copy text { margin-top: 5rpx; color: #75918d; font-size: 18rpx; line-height: 1.45; font-weight: 650; }.wallet-tip-arrow { color: #7eaaa1; font-size: 36rpx; font-weight: 700; }
.wallet-bill-card { margin-top: 22rpx; padding: 28rpx 24rpx 10rpx; border: 2rpx solid #e5ecf8; border-radius: 32rpx; background: rgba(255,255,255,.96); box-shadow: 0 16rpx 38rpx rgba(25,48,89,.07); }.wallet-section-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 16rpx; }.wallet-section-title { color: #1b2a41; font-size: 30rpx; line-height: 1.25; font-weight: 950; }.wallet-section-subtitle { margin-top: 7rpx; color: #8b99ab; font-size: 19rpx; line-height: 1.4; font-weight: 650; }.wallet-bill-all { min-height: 48rpx; margin: 0; padding: 0; border: 0; background: transparent; color: var(--gyt-primary,#3478f6); font-size: 19rpx; line-height: 48rpx; font-weight: 850; }.wallet-filter-scroll { margin: 22rpx -4rpx 0; width: calc(100% + 8rpx); white-space: nowrap; }.wallet-filter-list { display: inline-flex; gap: 10rpx; padding: 0 4rpx; }.wallet-filter { min-width: 78rpx; min-height: 50rpx; margin: 0; padding: 0 17rpx; border: 2rpx solid #e2eaf7; border-radius: 16rpx; background: #fbfdff; color: #7b8ca2; font-size: 19rpx; line-height: 46rpx; font-weight: 750; }.wallet-filter.active { border-color: var(--gyt-primary,#3478f6); background: var(--gyt-primary-soft,#edf4ff); color: var(--gyt-primary,#3478f6); }
.wallet-month-list { margin-top: 10rpx; }.wallet-month-group + .wallet-month-group { margin-top: 16rpx; padding-top: 18rpx; border-top: 2rpx solid #edf2fb; }.wallet-month-heading { padding: 14rpx 0 3rpx; display: flex; align-items: center; justify-content: space-between; gap: 12rpx; }.wallet-month-heading text { color: #384d6a; font-size: 23rpx; line-height: 1.35; font-weight: 900; }.wallet-month-heading view { color: #90a0b4; font-size: 17rpx; line-height: 1.35; font-weight: 650; text-align: right; white-space: nowrap; }.wallet-empty-state { padding: 78rpx 24rpx 68rpx; text-align: center; }.wallet-empty-icon { width: 80rpx; height: 80rpx; margin: 0 auto; border-radius: 28rpx; background: #f0f5fc; color: #8da2bf; display: flex; align-items: center; justify-content: center; font-size: 29rpx; font-weight: 900; }.wallet-empty-state strong,.wallet-empty-state text { display: block; }.wallet-empty-state strong { margin-top: 22rpx; color: #50647f; font-size: 25rpx; font-weight: 900; }.wallet-empty-state text { max-width: 460rpx; margin: 10rpx auto 0; color: #91a0b3; font-size: 19rpx; line-height: 1.6; font-weight: 650; }.wallet-bottom-note { margin: 20rpx 12rpx 0; color: #9aa7b8; text-align: center; font-size: 18rpx; line-height: 1.45; font-weight: 650; }
@media (max-width:350px){.wallet-content{padding-right:18rpx;padding-left:18rpx}.wallet-overview-card{padding:28rpx 24rpx 22rpx}.wallet-overview-amount{font-size:48rpx}.wallet-overview-actions{gap:7rpx}.wallet-primary-action,.wallet-secondary-action{min-width:76rpx;padding:0 12rpx;font-size:20rpx}.wallet-month-heading view{font-size:16rpx}.wallet-bill-card{padding-right:20rpx;padding-left:20rpx}}
</style>
