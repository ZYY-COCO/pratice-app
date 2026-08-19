<template>
  <view class="wallet-withdraw-page" :style="themeInlineStyle">
    <MentorPageHeader title="提现" @back="goBack" />

    <scroll-view scroll-y class="wallet-withdraw-scroll">
      <view v-if="!withdrawSubmitted" class="wallet-withdraw-content">
        <view class="wallet-balance-card">
          <text>可提现余额</text>
          <strong>{{ availableBalance }}</strong>
          <view>{{ balanceHint }}</view>
        </view>

        <view class="wallet-withdraw-card">
          <view class="wallet-withdraw-card-title">到账方式</view>
          <button
            v-for="item in channels"
            :key="item.value"
            class="wallet-channel-row"
            :class="{ active: selectedChannel === item.value }"
            @tap="selectedChannel = item.value"
          >
            <view class="wallet-channel-icon" :class="`tone-${item.tone}`">{{ item.icon }}</view>
            <view class="wallet-channel-copy">
              <strong>{{ item.label }}<text v-if="item.recommended">推荐</text></strong>
              <view>未绑定 · 第一版仅展示到账方式</view>
            </view>
            <view class="wallet-channel-check">{{ selectedChannel === item.value ? '✓' : '' }}</view>
          </button>
        </view>

        <view class="wallet-withdraw-card">
          <view class="wallet-withdraw-card-title">提现金额</view>
          <view class="wallet-amount-input-wrap">
            <text>¥</text>
            <input v-model="amountInput" type="digit" maxlength="10" placeholder="请输入提现金额" placeholder-class="wallet-input-placeholder" />
          </view>
          <view class="wallet-amount-actions">
            <text>可提现 {{ availableBalance }}</text>
            <button @tap="withdrawAll">全部提现</button>
          </view>
        </view>

        <view class="wallet-withdraw-rules">
          <view class="wallet-withdraw-rules-title">提现说明</view>
          <view v-for="item in withdrawalRules" :key="item" class="wallet-rule-row"><text>•</text><view>{{ item }}</view></view>
        </view>

        <button class="wallet-confirm-button" :disabled="!canSubmit" @tap="confirmWithdraw">确认提现</button>
      </view>

      <view v-else class="wallet-withdraw-success">
        <view class="wallet-success-icon">✓</view>
        <view class="wallet-success-title">提现申请已提交</view>
        <view class="wallet-success-amount">{{ submittedAmount }}</view>
        <view class="wallet-success-copy">到账审核通过后，将发起至你的{{ submittedRecord?.withdrawalMethod || '微信' }}账户。</view>
        <view class="wallet-success-note">当前为本地 Mock 演示，不会发起真实打款。</view>
        <button class="wallet-success-primary" @tap="goWallet">返回钱包</button>
        <button class="wallet-success-secondary" @tap="openRecords">查看提现记录</button>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'
import { formatWalletAmount, getWalletMockByRole, submitMockWithdrawal } from '../../data/walletMock'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const amountInput = ref('')
const selectedChannel = ref('wechat')
const withdrawSubmitted = ref(false)
const submittedRecord = ref(null)
const walletRole = ref('user')
const wallet = ref(getWalletMockByRole('user'))

const channels = [
  { value: 'wechat', label: '微信', icon: '微', tone: 'wechat', recommended: true },
  { value: 'alipay', label: '支付宝', icon: '支', tone: 'alipay', recommended: false }
]
const isMentor = computed(() => walletRole.value === 'mentor')
const balanceHint = computed(() => (
  isMentor.value
    ? '待结算资金将在结算完成后自动转入可提现余额'
    : '钱包余额可用于咨询支付，也可以申请提现'
))
const withdrawalRules = computed(() => [
  isMentor.value ? '仅可提现可提现余额，待结算金额暂不可提现。' : '钱包余额可用于咨询支付或申请提现。',
  '提现申请提交后，后续将支持 1–3 个工作日到账。',
  '第一版仅为页面演示，不发起真实提现和真实打款。'
])
const numericAmount = computed(() => Number(amountInput.value || 0))
const availableNumber = computed(() => Number(isMentor.value ? wallet.value.withdrawableBalance : wallet.value.balance) || 0)
const availableBalance = computed(() => formatWalletAmount(availableNumber.value))
const canSubmit = computed(() => (
  numericAmount.value > 0 && numericAmount.value <= availableNumber.value
))
const submittedAmount = computed(() => formatWalletAmount(Math.abs(Number(submittedRecord.value?.amount || 0))))

onLoad((options) => {
  walletRole.value = options?.role === 'mentor' ? 'mentor' : 'user'
  wallet.value = getWalletMockByRole(walletRole.value)
})

function withdrawAll() {
  amountInput.value = availableNumber.value.toFixed(2)
}

function confirmWithdraw() {
  if (!numericAmount.value || numericAmount.value <= 0) {
    uni.showToast({ title: '请输入正确的提现金额', icon: 'none' })
    return
  }
  if (numericAmount.value > availableNumber.value) {
    uni.showToast({ title: '提现金额不能超过可提现余额', icon: 'none' })
    return
  }
  const channel = channels.find((item) => item.value === selectedChannel.value)
  uni.showModal({
    title: '确认提交提现？',
    content: `将申请提现 ${formatWalletAmount(numericAmount.value)} 至${channel?.label || '微信'}。第一版仅保存本地演示状态。`,
    confirmText: '确认提交',
    cancelText: '再想想',
    success(result) {
      if (!result.confirm) return
      submittedRecord.value = submitMockWithdrawal({
        amount: numericAmount.value,
        channel: selectedChannel.value,
        role: walletRole.value
      })
      wallet.value = getWalletMockByRole(walletRole.value)
      withdrawSubmitted.value = true
    }
  })
}

function goWallet() {
  uni.redirectTo({ url: `/pages/wallet/index?role=${walletRole.value}` })
}

function openRecords() {
  uni.redirectTo({ url: `/pages/wallet/withdrawal-records?role=${walletRole.value}` })
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: `/pages/wallet/index?role=${walletRole.value}` })
    }
  })
}
</script>

<style scoped>
.wallet-withdraw-page { height: 100vh; height: 100dvh; overflow: hidden; background: var(--gyt-page-bg); display: flex; flex-direction: column; }.wallet-withdraw-scroll { min-height: 0; flex: 1; }.wallet-withdraw-content,.wallet-withdraw-success { width: 100%; max-width: 760rpx; margin: 0 auto; padding: 28rpx 24rpx calc(48rpx + env(safe-area-inset-bottom)); box-sizing: border-box; }
.wallet-balance-card { padding: 30rpx 28rpx; border: 2rpx solid #cde8e2; border-radius: 32rpx; background: linear-gradient(135deg,#fbfffe 0%,#eaf9f5 100%); box-shadow: 0 18rpx 42rpx rgba(35,130,111,.1); }.wallet-balance-card text,.wallet-balance-card strong,.wallet-balance-card view { display: block; }.wallet-balance-card text { color: #5e8b83; font-size: 21rpx; font-weight: 750; }.wallet-balance-card strong { margin-top: 11rpx; color: #2e675d; font-size: 50rpx; line-height: 1.1; font-weight: 950; }.wallet-balance-card view { margin-top: 16rpx; color: #78968f; font-size: 18rpx; line-height: 1.45; font-weight: 650; }
.wallet-withdraw-card { margin-top: 20rpx; padding: 28rpx 24rpx; border: 2rpx solid #e3ebf7; border-radius: 30rpx; background: rgba(255,255,255,.96); box-shadow: 0 14rpx 32rpx rgba(34,65,112,.06); }.wallet-withdraw-card-title { margin-bottom: 8rpx; color: #273a55; font-size: 26rpx; font-weight: 950; }.wallet-channel-row { width: 100%; min-height: 92rpx; margin: 0; padding: 15rpx 0; border: 0; border-bottom: 2rpx solid #eef2f8; border-radius: 0; background: transparent; display: flex; align-items: center; gap: 15rpx; text-align: left; }.wallet-channel-row:last-child { border-bottom: 0; }.wallet-channel-row::after { border: 0; }.wallet-channel-icon { width: 56rpx; height: 56rpx; flex: 0 0 56rpx; border-radius: 19rpx; background: #eaf8f3; color: #25846f; display: flex; align-items: center; justify-content: center; font-size: 21rpx; font-weight: 900; }.wallet-channel-icon.tone-alipay { background: #edf5ff; color: #397bce; }.wallet-channel-copy { min-width: 0; flex: 1; }.wallet-channel-copy strong,.wallet-channel-copy view { display: block; }.wallet-channel-copy strong { color: #435873; font-size: 22rpx; font-weight: 900; }.wallet-channel-copy strong text { display: inline-flex; margin-left: 8rpx; padding: 3rpx 7rpx; border-radius: 8rpx; background: #edf4ff; color: #4b7ecc; font-size: 15rpx; line-height: 1.2; font-weight: 800; vertical-align: 2rpx; }.wallet-channel-copy view { margin-top: 6rpx; color: #99a7b8; font-size: 18rpx; font-weight: 650; }.wallet-channel-check { width: 30rpx; height: 30rpx; flex: 0 0 30rpx; border: 2rpx solid #d5dfed; border-radius: 50%; color: #fff; display: flex; align-items: center; justify-content: center; box-sizing: border-box; font-size: 18rpx; font-weight: 900; }.wallet-channel-row.active .wallet-channel-check { border-color: #278a78; background: #278a78; }
.wallet-amount-input-wrap { height: 100rpx; padding: 0 4rpx; border-bottom: 2rpx solid #dfe8f5; display: flex; align-items: center; gap: 14rpx; }.wallet-amount-input-wrap text { color: #304866; font-size: 37rpx; font-weight: 900; }.wallet-amount-input-wrap input { min-width: 0; flex: 1; height: 100%; color: #2d425e; font-size: 34rpx; font-weight: 900; }.wallet-input-placeholder { color: #b1bdca; font-size: 23rpx; font-weight: 650; }.wallet-amount-actions { margin-top: 15rpx; display: flex; align-items: center; justify-content: space-between; }.wallet-amount-actions text { color: #90a0b4; font-size: 18rpx; font-weight: 650; }.wallet-amount-actions button { min-height: 42rpx; margin: 0; padding: 0; border: 0; background: transparent; color: #278a78; font-size: 19rpx; line-height: 42rpx; font-weight: 850; }.wallet-amount-actions button::after { border: 0; }
.wallet-withdraw-rules { margin: 22rpx 4rpx 0; }.wallet-withdraw-rules-title { color: #60718a; font-size: 21rpx; font-weight: 900; }.wallet-rule-row { margin-top: 10rpx; display: flex; align-items: flex-start; gap: 8rpx; color: #8c9aab; font-size: 18rpx; line-height: 1.55; font-weight: 650; }.wallet-rule-row text { color: #72a096; }.wallet-confirm-button { width: 100%; min-height: 86rpx; margin-top: 30rpx; border: 0; border-radius: 25rpx; background: #278a78; color: #fff; font-size: 25rpx; font-weight: 900; box-shadow: 0 12rpx 25rpx rgba(39,138,120,.2); }.wallet-confirm-button::after { border: 0; }.wallet-confirm-button[disabled] { background: #b9c9c5; box-shadow: none; }
.wallet-withdraw-success { padding-top: 122rpx; text-align: center; }.wallet-success-icon { width: 108rpx; height: 108rpx; margin: 0 auto; border-radius: 50%; background: #e6f7f1; color: #26856f; display: flex; align-items: center; justify-content: center; font-size: 52rpx; line-height: 1; font-weight: 900; box-shadow: 0 16rpx 32rpx rgba(38,133,111,.12); }.wallet-success-title { margin-top: 26rpx; color: #304961; font-size: 32rpx; font-weight: 950; }.wallet-success-amount { margin-top: 13rpx; color: #278a78; font-size: 43rpx; font-weight: 950; }.wallet-success-copy { max-width: 520rpx; margin: 18rpx auto 0; color: #74899a; font-size: 21rpx; line-height: 1.6; font-weight: 650; }.wallet-success-note { margin-top: 12rpx; color: #a0acba; font-size: 18rpx; line-height: 1.45; font-weight: 650; }.wallet-success-primary,.wallet-success-secondary { width: 100%; min-height: 82rpx; margin-top: 34rpx; border: 0; border-radius: 24rpx; background: #278a78; color: #fff; font-size: 24rpx; font-weight: 900; }.wallet-success-primary::after,.wallet-success-secondary::after { border: 0; }.wallet-success-secondary { margin-top: 14rpx; background: #edf8f5; color: #287e6d; box-shadow: none; }
@media(max-width:350px){.wallet-withdraw-content,.wallet-withdraw-success{padding-right:18rpx;padding-left:18rpx}.wallet-balance-card strong{font-size:45rpx}}
</style>
