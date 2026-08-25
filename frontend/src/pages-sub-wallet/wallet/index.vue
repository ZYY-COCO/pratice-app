<template>
  <view class="wallet-page" :style="themeInlineStyle">
    <AppPageHeader title="我的钱包" @back="goBack" />

    <scroll-view scroll-y class="wallet-scroll">
      <view class="wallet-content">
        <view class="wallet-balance-card">
          <view class="wallet-card-orbit wallet-card-orbit-large"></view>
          <view class="wallet-card-orbit wallet-card-orbit-small"></view>

          <view class="wallet-currency-mark">
            <view class="wallet-currency-core">¥</view>
          </view>

          <view class="wallet-balance-copy">
            <view class="wallet-balance-label">可用余额 · 人民币</view>
            <view class="wallet-balance-amount">{{ mainBalance }}</view>
          </view>
        </view>

        <view class="wallet-action-row">
          <button class="wallet-action wallet-action-recharge" @tap="handleRecharge">
            <view class="wallet-action-icon wallet-recharge-icon" aria-hidden="true">
              <view class="wallet-recharge-card"></view>
              <view class="wallet-recharge-plus">+</view>
            </view>
            <text>充值</text>
          </button>
          <button class="wallet-action wallet-action-withdraw" @tap="openWithdraw">
            <view class="wallet-action-icon wallet-withdraw-icon" aria-hidden="true">
              <view class="wallet-withdraw-box"></view>
              <view class="wallet-withdraw-arrow">
                <view class="wallet-withdraw-arrow-head"></view>
              </view>
            </view>
            <text>提现</text>
          </button>
        </view>

        <view v-if="isMentor" class="wallet-settlement-tip" @tap="openSettlementRules">
          <view class="wallet-tip-icon">i</view>
          <view class="wallet-tip-copy">
            <strong>结算说明</strong>
            <text>咨询完成后进入待结算，满 3 天自动转入可用余额。</text>
          </view>
          <view class="wallet-tip-arrow">›</view>
        </view>

        <view class="wallet-record-section">
          <view class="wallet-section-heading">
            <view class="wallet-section-title">交易记录</view>
            <button v-if="activeFilter !== 'all'" class="wallet-reset-filter" @tap="activeFilter = 'all'">
              查看全部
            </button>
            <text v-else class="wallet-record-count">{{ filteredTransactions.length }} 笔</text>
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

          <view v-if="walletLoading" class="wallet-loading-state">
            <view v-for="index in 3" :key="index" class="wallet-loading-row">
              <view class="wallet-loading-icon"></view>
              <view class="wallet-loading-copy">
                <view></view>
                <view></view>
              </view>
              <view class="wallet-loading-amount"></view>
            </view>
          </view>

          <view v-else-if="transactionGroups.length" class="wallet-month-list">
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
            <view class="wallet-empty-coin">
              <view>¥</view>
            </view>
            <strong>{{ emptyTitle }}</strong>
            <text>{{ emptyCopy }}</text>
          </view>
        </view>

        <view v-if="walletStatusMessage" class="wallet-bottom-note">{{ walletStatusMessage }}</view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import WalletTransactionRow from '../../components/WalletTransactionRow.vue'
import { fetchWalletSummary } from '../../api/wallet'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'
import {
  formatWalletAmount,
  getStoredWalletRole,
  matchesWalletFilter,
  setStoredWalletRole,
  walletFilterOptions
} from '../../data/walletPresentation'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const walletRole = ref(getStoredWalletRole())
const activeFilter = ref('all')
const walletLoadError = ref('')
const walletLoading = ref(true)

const wallet = ref(createEmptyWallet())
const isMentor = computed(() => walletRole.value === 'mentor')
const filterOptions = computed(() => walletFilterOptions[walletRole.value] || walletFilterOptions.user)
const mainBalance = computed(() => formatWalletAmount(isMentor.value ? wallet.value.withdrawableBalance : wallet.value.balance))
const walletStatusMessage = computed(() => walletLoadError.value || wallet.value.message || '')
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
  if (activeFilter.value !== 'all') return '暂无匹配记录'
  return isMentor.value ? '暂无钱包收入' : '暂无交易记录'
})
const emptyCopy = computed(() => (
  isMentor.value
    ? '完成咨询后，收入会先进入待结算，再转入可用余额。'
    : '充值、支付或退款完成后，交易记录会显示在这里。'
))

onLoad((options) => {
  if (options?.role === 'mentor' || options?.role === 'user') {
    walletRole.value = setStoredWalletRole(options.role)
  }
})

onShow(() => {
  walletRole.value = getStoredWalletRole()
  void loadWallet()
})

async function loadWallet() {
  walletLoadError.value = ''
  walletLoading.value = true
  try {
    wallet.value = await fetchWalletSummary({
      role: walletRole.value,
      ...(import.meta.env.DEV ? { mode: 'demo' } : {})
    })
  } catch (error) {
    wallet.value = createEmptyWallet()
    walletLoadError.value = getWalletLoadError(error)
  } finally {
    walletLoading.value = false
  }
}

function handleRecharge() {
  uni.showToast({ title: '微信支付商户资质审核中，充值暂未开放', icon: 'none' })
}

function openWithdraw() {
  if (!wallet.value.withdrawalEnabled) {
    uni.showModal({
      title: '提现暂未开放',
      content: '微信支付商户资质与打款能力接通后才会开放真实提现；当前不会创建本地假提现记录。',
      showCancel: false,
      confirmText: '我知道了'
    })
    return
  }
  uni.navigateTo({ url: `/pages-sub-wallet/wallet/withdraw?role=${walletRole.value}` })
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
    url: `/pages-sub-wallet/wallet/transaction-detail?id=${encodeURIComponent(transaction.id)}&role=${walletRole.value}`
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
  return match ? `${match[1]}年${Number(match[2])}月` : '最近交易'
}

function getWalletLoadError(error) {
  const detail = String(error?.detail || '').trim()
  return /[\u3400-\u9fff]/.test(detail)
    ? detail
    : '钱包账本暂时不可用，请稍后重试。'
}

function getMonthSummary(transactions, role) {
  if (role === 'mentor') {
    const income = transactions
      .filter((item) => ['consult_income', 'settlement_transfer', 'consultation_income_pending', 'consultation_income_settled'].includes(item.type))
      .reduce((sum, item) => sum + Math.max(0, Number(item.amount || 0)), 0)
    const withdrawn = transactions
      .filter((item) => ['withdraw', 'withdraw_fail'].includes(item.type) && item.status !== 'failed')
      .reduce((sum, item) => sum + Math.abs(Number(item.amount || 0)), 0)
    return `收入 ${formatWalletAmount(income)}　提现 ${formatWalletAmount(withdrawn)}`
  }
  const expense = transactions
    .filter((item) => Number(item.amount || 0) < 0)
    .reduce((sum, item) => sum + Math.abs(Number(item.amount || 0)), 0)
  const refund = transactions
    .filter((item) => ['refund', 'consultation_refund', 'consultation_income_reversed'].includes(item.type))
    .reduce((sum, item) => sum + Math.max(0, Number(item.amount || 0)), 0)
  return `支出 ${formatWalletAmount(expense)}　退款 ${formatWalletAmount(refund)}`
}

function createEmptyWallet() {
  return {
    balance: 0,
    withdrawableBalance: 0,
    pendingSettlement: 0,
    monthlyExpense: 0,
    monthlyRefund: 0,
    monthlyIncome: 0,
    totalIncome: 0,
    totalPaid: 0,
    withdrawalEnabled: false,
    paymentEnabled: false,
    message: '',
    transactions: []
  }
}
</script>

<style scoped>
.wallet-page {
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background:
    radial-gradient(circle at 88% 7%, rgba(114, 151, 255, 0.14), transparent 29%),
    linear-gradient(180deg, #fbfcff 0%, #f7f9fd 58%, #fbfcff 100%);
  display: flex;
  flex-direction: column;
  color: #101426;
}

.wallet-action::after,
.wallet-reset-filter::after,
.wallet-filter::after {
  border: 0;
}

.wallet-scroll {
  min-height: 0;
  flex: 1;
}

.wallet-content {
  width: 100%;
  max-width: 760rpx;
  margin: 0 auto;
  padding: 10rpx 28rpx calc(52rpx + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.wallet-balance-card {
  position: relative;
  min-height: 334rpx;
  overflow: hidden;
  padding: 32rpx 34rpx;
  box-sizing: border-box;
  border: 2rpx solid rgba(255, 255, 255, 0.34);
  border-radius: 34rpx;
  background:
    radial-gradient(circle at 16% 18%, rgba(239, 156, 255, 0.22), transparent 24%),
    linear-gradient(126deg, #8a36ed 0%, #6240ee 45%, #3a63f1 68%, #2f9af4 100%);
  box-shadow: 0 28rpx 58rpx rgba(67, 65, 199, 0.2);
}

.wallet-card-orbit {
  position: absolute;
  border: 2rpx solid rgba(255, 255, 255, 0.12);
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.05);
}

.wallet-card-orbit-large {
  right: -178rpx;
  top: 34rpx;
  width: 450rpx;
  height: 450rpx;
}

.wallet-card-orbit-small {
  right: -112rpx;
  top: 150rpx;
  width: 326rpx;
  height: 326rpx;
  background: rgba(255, 255, 255, 0.07);
}

.wallet-currency-mark {
  position: relative;
  width: 82rpx;
  height: 82rpx;
  border-radius: 50%;
  background: rgba(32, 8, 102, 0.68);
  box-shadow: 0 10rpx 26rpx rgba(41, 12, 123, 0.25);
  display: flex;
  align-items: center;
  justify-content: center;
}

.wallet-currency-core {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: #ffffff;
  color: #30107c;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  line-height: 1;
  font-weight: 900;
}

.wallet-balance-copy {
  position: absolute;
  left: 34rpx;
  right: 34rpx;
  bottom: 34rpx;
}

.wallet-balance-label {
  color: rgba(255, 255, 255, 0.9);
  font-size: 27rpx;
  line-height: 1.35;
  font-weight: 700;
}

.wallet-balance-amount {
  margin-top: 12rpx;
  color: #ffffff;
  font-size: 54rpx;
  line-height: 1.06;
  font-weight: 900;
  letter-spacing: -1rpx;
  text-shadow: 0 6rpx 18rpx rgba(31, 30, 119, 0.16);
}

.wallet-action-row {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20rpx;
  margin-top: 38rpx;
}

.wallet-action {
  min-width: 0;
  min-height: 88rpx;
  margin: 0;
  padding: 0 24rpx;
  border: 0;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 18rpx;
  color: #ffffff;
  font-size: 28rpx;
  line-height: 88rpx;
  font-weight: 900;
}

.wallet-action-recharge {
  background: linear-gradient(110deg, #5a23cb 0%, #4b22d4 56%, #4823c0 100%);
  box-shadow: 0 18rpx 34rpx rgba(75, 35, 199, 0.22);
}

.wallet-action-withdraw {
  background: linear-gradient(110deg, #347df3 0%, #2977f1 58%, #1685f5 100%);
  box-shadow: 0 18rpx 34rpx rgba(39, 119, 242, 0.22);
}

.wallet-action-icon {
  position: relative;
  width: 42rpx;
  height: 42rpx;
  flex: 0 0 42rpx;
}

.wallet-recharge-card {
  position: absolute;
  left: 1rpx;
  top: 5rpx;
  width: 28rpx;
  height: 26rpx;
  border: 4rpx solid #ffffff;
  border-radius: 6rpx;
  box-sizing: border-box;
}

.wallet-recharge-card::after {
  content: '';
  position: absolute;
  left: 4rpx;
  top: 5rpx;
  width: 17rpx;
  height: 4rpx;
  border-radius: 99rpx;
  background: #ffffff;
}

.wallet-recharge-plus {
  position: absolute;
  right: 0;
  bottom: 0;
  width: 22rpx;
  height: 22rpx;
  border: 3rpx solid #ffffff;
  border-radius: 50%;
  background: inherit;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  font-family: var(--gyt-app-font) !important;
  font-size: 18rpx;
  line-height: 17rpx;
  font-weight: 800;
}

.wallet-withdraw-box {
  position: absolute;
  left: 3rpx;
  bottom: 2rpx;
  width: 36rpx;
  height: 26rpx;
  border: 4rpx solid #ffffff;
  border-top: 0;
  border-radius: 0 0 7rpx 7rpx;
  box-sizing: border-box;
}

.wallet-withdraw-arrow {
  position: absolute;
  left: 19rpx;
  top: 2rpx;
  width: 4rpx;
  height: 27rpx;
  border-radius: 99rpx;
  background: #ffffff;
}

.wallet-withdraw-arrow-head {
  position: absolute;
  left: -7rpx;
  top: 0;
  width: 13rpx;
  height: 13rpx;
  border-top: 4rpx solid #ffffff;
  border-left: 4rpx solid #ffffff;
  transform: rotate(45deg);
}

.wallet-settlement-tip {
  margin-top: 24rpx;
  padding: 20rpx 22rpx;
  border: 2rpx solid rgba(98, 64, 238, 0.13);
  border-radius: 24rpx;
  background: rgba(244, 242, 255, 0.88);
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.wallet-tip-icon {
  width: 34rpx;
  height: 34rpx;
  flex: 0 0 34rpx;
  border-radius: 50%;
  background: #e5dfff;
  color: #5b43cf;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20rpx;
  font-weight: 900;
}

.wallet-tip-copy {
  min-width: 0;
  flex: 1;
}

.wallet-tip-copy strong,
.wallet-tip-copy text {
  display: block;
}

.wallet-tip-copy strong {
  color: #423a70;
  font-size: 21rpx;
  line-height: 1.35;
  font-weight: 900;
}

.wallet-tip-copy text {
  margin-top: 4rpx;
  color: #7b7697;
  font-size: 18rpx;
  line-height: 1.45;
  font-weight: 650;
}

.wallet-tip-arrow {
  color: #8d84bc;
  font-size: 34rpx;
  line-height: 1;
}

.wallet-record-section {
  margin-top: 48rpx;
}

.wallet-section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.wallet-section-title {
  color: #101426;
  font-size: 34rpx;
  line-height: 1.2;
  font-weight: 900;
}

.wallet-record-count,
.wallet-reset-filter {
  color: #8a90a3;
  font-size: 20rpx;
  line-height: 1.3;
  font-weight: 700;
}

.wallet-reset-filter {
  min-height: 48rpx;
  margin: 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--gyt-primary, #3478f6);
  line-height: 48rpx;
}

.wallet-filter-scroll {
  width: 100%;
  margin-top: 22rpx;
  white-space: nowrap;
}

.wallet-filter-list {
  display: inline-flex;
  gap: 12rpx;
  padding-right: 28rpx;
}

.wallet-filter {
  min-width: 82rpx;
  min-height: 48rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 2rpx solid #e7eaf2;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.76);
  color: #777e92;
  font-size: 20rpx;
  line-height: 44rpx;
  font-weight: 750;
}

.wallet-filter.active {
  border-color: rgba(52, 120, 246, 0.2);
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
}

.wallet-month-list {
  margin-top: 18rpx;
}

.wallet-month-group + .wallet-month-group {
  margin-top: 24rpx;
  padding-top: 18rpx;
  border-top: 2rpx solid #e9edf4;
}

.wallet-month-heading {
  padding: 8rpx 0 4rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14rpx;
}

.wallet-month-heading text {
  color: #34394a;
  font-size: 22rpx;
  line-height: 1.35;
  font-weight: 900;
}

.wallet-month-heading view {
  overflow: hidden;
  color: #969bad;
  font-size: 17rpx;
  line-height: 1.35;
  font-weight: 650;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wallet-loading-state {
  margin-top: 22rpx;
}

.wallet-loading-row {
  min-height: 126rpx;
  padding: 20rpx 0;
  border-bottom: 2rpx solid #e9edf4;
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.wallet-loading-icon,
.wallet-loading-copy view,
.wallet-loading-amount {
  background: linear-gradient(90deg, #edf0f6 25%, #f7f8fb 42%, #edf0f6 62%);
  background-size: 400% 100%;
  animation: wallet-loading 1.25s ease-in-out infinite;
}

.wallet-loading-icon {
  width: 76rpx;
  height: 76rpx;
  flex: 0 0 76rpx;
  border-radius: 50%;
}

.wallet-loading-copy {
  min-width: 0;
  flex: 1;
}

.wallet-loading-copy view:first-child {
  width: 72%;
  height: 22rpx;
  border-radius: 99rpx;
}

.wallet-loading-copy view:last-child {
  width: 52%;
  height: 16rpx;
  margin-top: 14rpx;
  border-radius: 99rpx;
}

.wallet-loading-amount {
  width: 92rpx;
  height: 22rpx;
  flex: 0 0 92rpx;
  border-radius: 99rpx;
}

.wallet-empty-state {
  padding: 92rpx 24rpx 78rpx;
  text-align: center;
}

.wallet-empty-coin {
  width: 88rpx;
  height: 88rpx;
  margin: 0 auto;
  border-radius: 50%;
  background: #e9e6fb;
  display: flex;
  align-items: center;
  justify-content: center;
}

.wallet-empty-coin view {
  width: 50rpx;
  height: 50rpx;
  border-radius: 50%;
  background: #ffffff;
  color: #7364b5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 27rpx;
  font-weight: 900;
}

.wallet-empty-state strong,
.wallet-empty-state text {
  display: block;
}

.wallet-empty-state strong {
  margin-top: 22rpx;
  color: #4b5163;
  font-size: 26rpx;
  line-height: 1.4;
  font-weight: 900;
}

.wallet-empty-state text {
  max-width: 480rpx;
  margin: 10rpx auto 0;
  color: #969bad;
  font-size: 19rpx;
  line-height: 1.6;
  font-weight: 650;
}

.wallet-bottom-note {
  margin: 28rpx 18rpx 0;
  color: #9ba0b0;
  text-align: center;
  font-size: 18rpx;
  line-height: 1.5;
  font-weight: 650;
}

@keyframes wallet-loading {
  0% { background-position: 100% 0; }
  100% { background-position: 0 0; }
}

@media (max-width: 350px) {
  .wallet-content {
    padding-right: 20rpx;
    padding-left: 20rpx;
  }

  .wallet-balance-card {
    min-height: 314rpx;
    padding-right: 28rpx;
    padding-left: 28rpx;
  }

  .wallet-balance-copy {
    left: 28rpx;
    right: 28rpx;
  }

  .wallet-balance-amount {
    font-size: 49rpx;
  }

  .wallet-action-row {
    gap: 14rpx;
  }

  .wallet-action {
    min-height: 82rpx;
    padding: 0 18rpx;
    gap: 12rpx;
    font-size: 26rpx;
    line-height: 82rpx;
  }

  .wallet-month-heading view {
    max-width: 330rpx;
    font-size: 16rpx;
  }
}

@media (prefers-reduced-motion: reduce) {
  .wallet-loading-icon,
  .wallet-loading-copy view,
  .wallet-loading-amount {
    animation: none;
  }
}
</style>
