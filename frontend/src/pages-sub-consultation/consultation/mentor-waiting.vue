<template>
  <view class="mentor-waiting-page" :style="themeInlineStyle">
    <MentorPageHeader :title="pageTitle" @back="goBack" />

    <scroll-view scroll-y class="mentor-waiting-scroll">
      <view v-if="mentor" class="mentor-waiting-content">
        <view v-if="isPaymentPending" class="mentor-waiting-main">
          <view class="mentor-waiting-icon waiting">⌛</view>
          <view class="mentor-waiting-title">{{ isDemoOrder ? '确认咨询' : (paymentStatus === 'failed' ? '本次支付未完成' : '等待支付确认') }}</view>
          <view class="mentor-waiting-copy">{{ isDemoOrder ? '点击下方“跳过支付并继续”，即可把咨询请求发送给前辈。' : (paymentStatus === 'failed' ? '支付渠道未确认本次付款。你可以重新进入支付页面，或取消本次订单。' : (paymentMessage || '支付完成后，系统会自动确认并把咨询请求发送给前辈。')) }}</view>
          <view v-if="showCountdown" class="mentor-countdown"><text>{{ countdownLabel }}</text>{{ countdownText }}</view>
        </view>

        <view v-else-if="isRefunding" class="mentor-waiting-main mentor-failed-main">
          <view class="mentor-waiting-icon waiting">⌛</view>
          <view class="mentor-waiting-title">退款处理中</view>
          <view class="mentor-waiting-copy">平台已提交 ¥{{ refundAmount || 0 }} 的退款申请；支付渠道确认完成后，这里会自动更新。</view>
        </view>

        <view v-else-if="isRefundFailed" class="mentor-waiting-main mentor-failed-main">
          <view class="mentor-waiting-icon failed">!</view>
          <view class="mentor-waiting-title">退款需要平台继续跟进</view>
          <view class="mentor-waiting-copy">退款渠道返回异常，平台已保留订单与处理记录。请进入平台处理进度查看后续结果。</view>
        </view>

        <view v-else-if="isCancelled" class="mentor-waiting-main mentor-failed-main">
          <view class="mentor-waiting-icon failed">—</view>
          <view class="mentor-waiting-title">本次咨询已取消</view>
          <view class="mentor-waiting-copy">{{ paymentStatus === 'refunded' ? '订单已取消，退款已完成并将原路退回。' : '订单已取消；如已支付，退款记录可在平台处理进度中查看。' }}</view>
        </view>

        <view v-else-if="isFailed" class="mentor-waiting-main mentor-failed-main">
          <view class="mentor-waiting-icon failed">!</view>
          <view class="mentor-waiting-title">{{ isBooking ? '本次预约未开始服务' : (acceptedStartTimedOut ? '本次咨询未能按时开始' : '本次咨询未能成功接单') }}</view>
          <view class="mentor-waiting-copy">{{ failureCopy }}</view>
        </view>

        <view v-else-if="isBooking && status === 'booked'" class="mentor-waiting-main mentor-booked-main">
          <view class="mentor-waiting-icon booked">✓</view>
          <view class="mentor-waiting-title">预约成功</view>
          <view class="mentor-waiting-copy">已为你保留本次咨询时间；到预约时段后，请等待认证前辈开始服务。</view>
          <view class="mentor-booked-slot">{{ bookingSlotLabel }}</view>
        </view>

        <view v-else class="mentor-waiting-main">
          <view class="mentor-waiting-icon waiting">⌛</view>
          <view class="mentor-waiting-title">{{ waitingTitle }}</view>
          <view class="mentor-waiting-copy">{{ waitingCopy }}</view>
          <view v-if="showCountdown" class="mentor-countdown"><text>{{ countdownLabel }}</text>{{ countdownText }}</view>
        </view>

        <view class="mentor-waiting-person-card">
          <view class="mentor-waiting-avatar" :class="`tone-${mentor.avatarTone || 'blue'}`">{{ mentor.avatar }}</view>
          <view>
            <view class="mentor-waiting-name">{{ mentor.maskedName }} <text>✓ 已认证</text></view>
            <view>{{ mentor.school }} · {{ mentor.major }}</view>
            <view v-if="isBooking" class="mentor-waiting-booked-note">本次服务：{{ bookingSlotLabel }} · {{ consultationWindowMinutes }}分钟</view>
          </view>
        </view>

        <view v-if="!isBooking && !isFailed && !isPaymentPending && !isRefunding && !isRefundFailed" class="mentor-waiting-flow-card">
          <view class="mentor-waiting-flow-title">本次咨询流程</view>
          <view class="mentor-waiting-flow">
            <view><text class="done">1</text><text class="mentor-waiting-flow-copy">{{ isNoPaymentOrder ? '已确认咨询' : '已支付咨询费用' }}</text></view>
            <view><text class="active">2</text><text class="mentor-waiting-flow-copy">前辈确认接单</text></view>
            <view><text>3</text><text class="mentor-waiting-flow-copy">进入 {{ consultationWindowMinutes }} 分钟咨询</text></view>
          </view>
        </view>

        <view v-if="isBooking" class="mentor-waiting-notice">
          <text>预约说明</text>
          <view>这是前辈主动开放的可预约时间，因此不需要再次等待接单。到预约时段后可进入等待室，文字聊天会在前辈开始服务后开放。</view>
        </view>
      </view>
      <view class="mentor-waiting-bottom-space"></view>
    </scroll-view>

    <view v-if="mentor" class="mentor-waiting-footer">
      <view v-if="isPaymentPending" class="mentor-waiting-footer-actions">
        <button class="secondary" :loading="cancelling" @tap="confirmCancel">取消订单</button>
        <button v-if="isDemoOrder" :loading="skippingPayment" @tap="skipPaymentForLocalRehearsal">{{ skippingPayment ? '正在继续' : '跳过支付并继续' }}</button>
        <button v-else :loading="preparingPayment" @tap="openPaymentCheckout">{{ preparingPayment ? '准备支付中' : (hasPaymentCheckout ? '前往支付' : '获取支付说明') }}</button>
      </view>
      <view v-else-if="isRefunding || isRefundFailed" class="mentor-waiting-footer-actions">
        <button class="secondary" @tap="requestPlatformIntervention">申请平台介入</button>
        <button @tap="openSupport">查看处理进度</button>
      </view>
      <view v-else-if="isFailed" class="mentor-waiting-footer-actions">
        <button class="secondary" @tap="requestPlatformIntervention">申请平台介入</button>
        <button @tap="chooseAgain">重新选择前辈</button>
      </view>
      <view v-else-if="isCancelled" class="mentor-waiting-footer-actions">
        <button class="secondary" @tap="requestPlatformIntervention">申请平台介入</button>
        <button @tap="openSupport">查看退款进度</button>
      </view>
      <view v-else class="mentor-waiting-footer-actions">
        <button v-if="canCancel" class="secondary" :loading="cancelling" @tap="confirmCancel">取消订单</button>
        <button v-if="isBooking || status === 'in_progress'" :loading="openingChat" @tap="openChat">{{ isBooking && status === 'booked' ? '进入等待室' : '进入咨询' }}</button>
        <button v-else class="secondary" @tap="goBack">返回前辈详情</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import {
  fetchMentorProfile,
  fetchMentorConsultationOrder,
  cancelMentorConsultationOrder,
  confirmMentorConsultationLocalRehearsal,
  createMentorConsultationPaymentIntent
} from '../../api/mentorConsultation'
import {
  cacheMentors,
  getConsultationDraft,
  getMentorById,
  normalizeMentorDetailResponse,
  saveConsultationOrder
} from '../../data/mentorConsultation'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const mentor = ref(null)
const mode = ref('instant')
const status = ref('pending_accept')
const bookingSlot = ref(null)
const orderId = ref('')
const expiresAt = ref('')
const paymentExpiresAt = ref('')
const acceptedAt = ref('')
const paymentStatus = ref('unpaid')
const paymentReference = ref('')
const paymentMode = ref('real')
const refundReference = ref('')
const refundAmount = ref(0)
const rejectionReason = ref('')
const paymentCheckoutUrl = ref('')
const paymentMessage = ref('')
const remainingSeconds = ref(0)
const consultationWindowMinutes = ref(60)
const openingChat = ref(false)
const cancelling = ref(false)
const skippingPayment = ref(false)
const preparingPayment = ref(false)
const themeKey = ref(getStoredThemeKey())
let countdownTimer = null
let orderPollTimer = null

const isBooking = computed(() => mode.value === 'booking')
const isFailed = computed(() => ['timeout', 'rejected', 'refunded'].includes(status.value))
const isCancelled = computed(() => status.value === 'cancelled')
const isPaymentPending = computed(() => status.value === 'pending_payment')
const isRefunding = computed(() => paymentStatus.value === 'refunding')
const isRefundFailed = computed(() => paymentStatus.value === 'failed' && Boolean(refundReference.value))
const isDemoOrder = computed(() => paymentMode.value === 'demo')
const isNoPaymentOrder = computed(() => isDemoOrder.value && paymentReference.value.toUpperCase().startsWith('DEMO-'))
const hasPaymentCheckout = computed(() => Boolean(paymentCheckoutUrl.value))
const acceptedStartTimedOut = computed(() => status.value === 'timeout' && Boolean(acceptedAt.value))
const canCancel = computed(() => ['pending_payment', 'pending_accept', 'accepted', 'booked'].includes(status.value))
const pageTitle = computed(() => {
  if (isPaymentPending.value) return isDemoOrder.value ? '确认咨询' : '支付确认'
  if (isRefunding.value || isRefundFailed.value) return '退款进度'
  if (isFailed.value || isCancelled.value) return isBooking.value ? '预约服务状态' : '咨询状态'
  if (status.value === 'accepted') return '等待服务开始'
  return isBooking.value ? '预约成功' : '等待前辈接单'
})
const bookingSlotLabel = computed(() => bookingSlot.value ? `${bookingSlot.value.date} ${bookingSlot.value.time}` : '已预约时间')
const countdownText = computed(() => {
  const minutes = String(Math.floor(Math.max(0, remainingSeconds.value) / 60)).padStart(2, '0')
  const seconds = String(Math.max(0, remainingSeconds.value) % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
})
const showCountdown = computed(() => Boolean(
  isPaymentPending.value ? paymentExpiresAt.value : (['pending_accept', 'accepted'].includes(status.value) && expiresAt.value)
))
const countdownLabel = computed(() => {
  if (isPaymentPending.value) return isBooking.value ? '预约预占倒计时' : '订单支付倒计时'
  return status.value === 'accepted' ? '开始服务倒计时' : '接单倒计时'
})
const waitingTitle = computed(() => {
  if (status.value === 'in_progress') return '咨询服务已开始'
  if (status.value === 'accepted') return '前辈已接单，等待开始服务'
  return '等待前辈确认接单'
})
const waitingCopy = computed(() => {
  if (status.value === 'in_progress') return '咨询窗口已打开，你可以进入站内聊天继续沟通。'
  if (status.value === 'accepted') return '服务开始后会自动开放文字聊天；若前辈未在保护时间内开始，本次咨询将自动取消并进入退款处理。'
  return '你的咨询资料和问题已发送给前辈，前辈将在 10 分钟内确认是否接单。'
})
const failureCopy = computed(() => {
  const outcome = isBooking.value
    ? '预约时段内未开始服务，本次咨询已自动取消。'
    : (acceptedStartTimedOut.value
        ? '前辈已接单但未在保护时间内开始服务，本次咨询已自动取消。'
        : (status.value === 'rejected'
            ? `前辈暂时未能接受本次咨询。${rejectionReason.value ? ` 前辈说明：${rejectionReason.value}` : ''}`
            : '前辈在 10 分钟内未确认本次咨询。'))
  if (paymentStatus.value === 'refunded') return `${outcome} 退款已完成并将原路退回。`
  if (isRefunding.value) return `${outcome} 平台已提交退款处理，完成后会自动同步。`
  if (isRefundFailed.value) return `${outcome} 退款处理需要平台继续跟进，请查看平台处理进度。`
  return outcome
})
const themeInlineStyle = computed(() => buildThemeStyle(themeKey.value))

onLoad((options) => {
  const draft = getConsultationDraft()
  orderId.value = String(options?.orderId || draft?.orderId || '')
  const mentorId = options?.mentorId || draft?.mentorId
  mentor.value = getMentorById(mentorId)
  bookingSlot.value = draft?.bookingSlot || null
  paymentCheckoutUrl.value = draft?.paymentCheckoutUrl || ''
  paymentMessage.value = draft?.paymentMessage || ''
  mode.value = options?.mode === 'booking' || draft?.consultationType === 'booking' ? 'booking' : 'instant'
  if (!orderId.value) {
    uni.showToast({ title: '未找到咨询订单，请重新发起咨询', icon: 'none' })
    return
  }
  void loadMentor(mentorId)
  void loadOrder()
})

onShow(() => {
  themeKey.value = getStoredThemeKey()
  if (orderId.value) void loadOrder({ silent: true })
})

onBeforeUnmount(stopOrderTimers)

async function loadOrder({ silent = false } = {}) {
  if (!orderId.value) return
  try {
    const order = await fetchMentorConsultationOrder(orderId.value)
    applyOrder(order)
  } catch (error) {
    if (!silent) uni.showToast({ title: error?.detail || '咨询订单加载失败', icon: 'none' })
  }
}

async function loadMentor(mentorId) {
  const id = String(mentorId || '')
  if (!id) return
  try {
    const profile = normalizeMentorDetailResponse(await fetchMentorProfile(id))
    if (!profile) return
    mentor.value = profile
    cacheMentors([profile])
  } catch (error) {
    // 已有缓存或当前订单仍可继续使用时，不用网络短暂失败打断等待页。
  }
}

function applyOrder(order) {
  const draft = saveConsultationOrder(order)
  status.value = draft.orderStatus || 'pending_accept'
  mode.value = draft.consultationType === 'booking' ? 'booking' : 'instant'
  paymentStatus.value = draft.paymentStatus || 'unpaid'
  paymentReference.value = draft.paymentReference || ''
  paymentMode.value = draft.paymentMode || 'real'
  refundReference.value = draft.refundReference || ''
  refundAmount.value = Number(draft.refundAmount) || 0
  rejectionReason.value = draft.rejectionReason || ''
  paymentCheckoutUrl.value = draft.paymentCheckoutUrl || paymentCheckoutUrl.value
  paymentMessage.value = draft.paymentMessage || paymentMessage.value
  expiresAt.value = draft.expiresAt || ''
  paymentExpiresAt.value = draft.paymentExpiresAt || ''
  acceptedAt.value = draft.acceptedAt || ''
  consultationWindowMinutes.value = Number(draft.consultationWindowMinutes) || 60
  if (['pending_payment', 'pending_accept', 'accepted'].includes(status.value)) {
    syncRemainingSeconds()
    startCountdown()
  } else if (countdownTimer) {
    clearInterval(countdownTimer)
    countdownTimer = null
  }
  if (['pending_payment', 'pending_accept', 'accepted', 'booked'].includes(status.value) || isRefunding.value) {
    startOrderPolling()
  } else {
    stopOrderTimers()
  }
}

function syncRemainingSeconds() {
  const deadline = Date.parse((isPaymentPending.value ? paymentExpiresAt.value : expiresAt.value) || '')
  remainingSeconds.value = Number.isFinite(deadline)
    ? Math.max(0, Math.ceil((deadline - Date.now()) / 1000))
    : 0
}

function startCountdown() {
  if (countdownTimer) return
  countdownTimer = setInterval(() => {
    syncRemainingSeconds()
    if (remainingSeconds.value <= 0) {
      void loadOrder({ silent: true })
    }
  }, 1000)
}

function startOrderPolling() {
  if (orderPollTimer) return
  orderPollTimer = setInterval(() => {
    void loadOrder({ silent: true })
  }, status.value === 'booked' ? 30000 : 5000)
}

function stopOrderTimers() {
  if (countdownTimer) clearInterval(countdownTimer)
  if (orderPollTimer) clearInterval(orderPollTimer)
  countdownTimer = null
  orderPollTimer = null
}

async function openChat() {
  if (!mentor.value || !orderId.value || openingChat.value) return
  if (status.value !== 'in_progress' && !(isBooking.value && status.value === 'booked')) {
    uni.showToast({ title: '请等待前辈确认接单后进入咨询', icon: 'none' })
    return
  }
  openingChat.value = true
  try {
    uni.navigateTo({
      url: `/pages-sub-consultation/consultation/mentor-chat?mentorId=${encodeURIComponent(mentor.value.id)}&mode=${mode.value}&orderId=${encodeURIComponent(orderId.value)}`
    })
  } catch (error) {
    uni.showToast({ title: error?.detail || '暂时无法进入咨询', icon: 'none' })
  } finally {
    openingChat.value = false
  }
}

function confirmCancel() {
  if (!canCancel.value || cancelling.value || !orderId.value) return
  uni.showModal({
    title: '取消本次咨询？',
    content: paymentStatus.value === 'paid' ? '取消后会释放预约时段；已支付的订单将进入退款处理。' : '取消后会释放预约时段，未支付订单不会产生退款。',
    confirmText: '确认取消',
    confirmColor: '#d66b61',
    success(result) {
      if (result.confirm) void cancelOrder()
    }
  })
}

async function skipPaymentForLocalRehearsal() {
  if (!isDemoOrder.value || skippingPayment.value || !orderId.value) return
  skippingPayment.value = true
  try {
    const order = await confirmMentorConsultationLocalRehearsal(orderId.value)
    applyOrder(order)
    uni.showToast({ title: '咨询请求已发送，请等待前辈确认', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '咨询服务未启用，请刷新本地服务后重试', icon: 'none' })
  } finally {
    skippingPayment.value = false
  }
}

async function openPaymentCheckout() {
  if (!paymentCheckoutUrl.value && !preparingPayment.value && orderId.value) {
    preparingPayment.value = true
    try {
      const intent = await createMentorConsultationPaymentIntent(orderId.value)
      const order = await fetchMentorConsultationOrder(orderId.value)
      const draft = saveConsultationOrder({
        ...order,
        payment_provider: intent?.provider || '',
        payment_checkout_url: intent?.checkout_url || '',
        payment_message: intent?.message || ''
      })
      paymentCheckoutUrl.value = draft.paymentCheckoutUrl || ''
      paymentMessage.value = draft.paymentMessage || ''
      paymentStatus.value = draft.paymentStatus || paymentStatus.value
    } catch (error) {
      uni.showToast({ title: error?.detail || '支付订单暂时无法刷新，请稍后重试', icon: 'none' })
      return
    } finally {
      preparingPayment.value = false
    }
  }
  const checkoutUrl = String(paymentCheckoutUrl.value || '').trim()
  if (!checkoutUrl) {
    uni.showModal({
      title: '支付订单已创建',
      content: paymentMessage.value || '当前支付渠道尚未配置。订单会保持待支付状态，系统不会提前标记为已支付。',
      showCancel: false,
      confirmText: '知道了'
    })
    return
  }
  if (typeof window !== 'undefined' && window.location) {
    window.location.assign(checkoutUrl)
    return
  }
  uni.setClipboardData({
    data: checkoutUrl,
    success: () => uni.showToast({ title: '支付链接已复制，请在浏览器打开', icon: 'none' })
  })
}

async function cancelOrder() {
  if (cancelling.value || !orderId.value) return
  cancelling.value = true
  try {
    const order = await cancelMentorConsultationOrder(orderId.value)
    applyOrder(order)
    uni.showToast({ title: '订单已取消', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '取消订单失败，请稍后重试', icon: 'none' })
  } finally {
    cancelling.value = false
  }
}

function requestPlatformIntervention() {
  if (!orderId.value) return
  uni.navigateTo({
    url: `/pages-sub-consultation/consultation/mentor-report?orderId=${encodeURIComponent(orderId.value)}&mentorId=${encodeURIComponent(mentor.value?.id || '')}&targetRole=mentor`
  })
}

function openSupport() {
  uni.navigateTo({ url: '/pages-sub-consultation/consultation/mentor-support' })
}

function chooseAgain() {
  uni.reLaunch({ url: '/pages/home/index?tab=circle&section=community&communityTab=mentor' })
}

function goBack() {
  uni.navigateBack({
    fail: chooseAgain
  })
}
</script>

<style scoped>
.mentor-waiting-page { height: 100vh; height: 100dvh; overflow: hidden; background:#f4f8ff; display:flex; flex-direction:column; }
.mentor-waiting-scroll { min-height:0; flex:1; }.mentor-waiting-content { padding:32rpx 24rpx 0; }
.mentor-waiting-main { padding:38rpx 28rpx 32rpx; border:2rpx solid #d6e6ff; border-radius:30rpx; background:rgba(255,255,255,.94); text-align:center; box-shadow:0 16rpx 38rpx rgba(52,120,246,.08); }
.mentor-waiting-icon { width:92rpx; height:92rpx; margin:0 auto; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:45rpx; line-height:1; font-weight:900; }.mentor-waiting-icon.waiting{background:#edf4ff;color:#3478f6}.mentor-waiting-icon.booked{background:#e6f6ec;color:#26955a}.mentor-waiting-icon.failed{background:#fff0ee;color:#e46a5f}
.mentor-waiting-title { margin-top:20rpx; color:#243550; font-size:31rpx; line-height:1.25; font-weight:900; }.mentor-waiting-copy{margin-top:12rpx;color:#73839a;font-size:22rpx;line-height:1.55;font-weight:650}.mentor-countdown{margin:25rpx auto 0;padding:15rpx 28rpx;border-radius:18rpx;background:#f4f8ff;color:#3478f6;font-size:42rpx;line-height:1;font-weight:900;letter-spacing:2rpx;width:max-content}.mentor-booked-slot{margin-top:20rpx;color:#277b54;font-size:24rpx;font-weight:850}
.mentor-waiting-person-card,.mentor-waiting-flow-card,.mentor-waiting-notice,.mentor-demo-card { margin-top:18rpx; border:2rpx solid #dce8fa; border-radius:26rpx; background:rgba(255,255,255,.91); box-shadow:0 12rpx 30rpx rgba(52,120,246,.055); }
.mentor-waiting-person-card { padding:24rpx; display:flex; align-items:center; gap:15rpx; color:#7c8ca1;font-size:21rpx;line-height:1.4;font-weight:650; }.mentor-waiting-avatar{width:68rpx;height:68rpx;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26rpx;font-weight:900;flex-shrink:0}.mentor-waiting-avatar.tone-blue{background:#e6efff;color:#3478f6}.mentor-waiting-avatar.tone-mint{background:#e2f4ef;color:#198777}.mentor-waiting-avatar.tone-violet{background:#eeeafe;color:#7162bd}.mentor-waiting-avatar.tone-warm{background:#f9eee1;color:#b66c32}.mentor-waiting-name{color:#354863;font-size:25rpx;font-weight:900}.mentor-waiting-name text{margin-left:8rpx;padding:5rpx 9rpx;border-radius:999rpx;background:#edf4ff;color:#3478f6;font-size:17rpx;font-weight:800}.mentor-waiting-booked-note{margin-top:5rpx;color:#3d9161;font-size:19rpx;font-weight:750}
.mentor-waiting-flow-card{padding:26rpx}.mentor-waiting-flow-title{color:#3e5472;font-size:24rpx;font-weight:900}.mentor-waiting-flow{margin-top:18rpx}.mentor-waiting-flow>view{position:relative;display:flex;align-items:center;gap:12rpx;color:#8391a4;font-size:21rpx;line-height:1.3;font-weight:700}.mentor-waiting-flow>view+view{margin-top:15rpx}.mentor-waiting-flow text{width:30rpx;height:30rpx;border-radius:50%;background:#e9eef6;color:#8290a4;display:inline-flex;align-items:center;justify-content:center;font-size:18rpx;font-weight:900;flex-shrink:0}.mentor-waiting-flow text.done{background:#e7f5ec;color:#249458}.mentor-waiting-flow text.active{background:#edf4ff;color:#3478f6}.mentor-waiting-flow text.mentor-waiting-flow-copy{width:auto;height:auto;border-radius:0;background:transparent;color:inherit;display:block;font-size:21rpx;font-weight:700}
.mentor-waiting-notice{padding:25rpx;color:#728399;font-size:21rpx;line-height:1.6;font-weight:650}.mentor-waiting-notice text{display:block;margin-bottom:8rpx;color:#42608c;font-size:24rpx;font-weight:900}
.mentor-demo-card{padding:24rpx;color:#7b8ca3;font-size:20rpx;line-height:1.55;font-weight:650}.mentor-demo-card>view:first-child{color:#48648e;font-size:24rpx;font-weight:900}.mentor-demo-card>text{display:block;margin-top:7rpx}.mentor-demo-actions{display:flex;flex-wrap:wrap;gap:10rpx;margin-top:18rpx}.mentor-demo-actions button{min-height:52rpx;margin:0;padding:0 16rpx;border:0;border-radius:15rpx;background:#3478f6;color:#fff;font-size:20rpx;font-weight:850}.mentor-demo-actions button::after,.mentor-waiting-footer button::after{border:0}.mentor-demo-actions button.light{background:#edf4ff;color:#4d72ab}
.mentor-waiting-bottom-space{height:calc(150rpx + env(safe-area-inset-bottom))}.mentor-waiting-footer{padding:16rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));border-top:2rpx solid #dbe7f8;background:rgba(255,255,255,.97)}.mentor-waiting-footer-actions{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14rpx}.mentor-waiting-footer-actions>button:only-child{grid-column:1/-1}.mentor-waiting-footer button{width:100%;min-height:76rpx;margin:0;border:0;border-radius:20rpx;background:#3478f6;color:#fff;font-size:24rpx;font-weight:900;box-shadow:0 10rpx 22rpx rgba(52,120,246,.2)}.mentor-waiting-footer button.secondary{background:#edf4ff;color:#4f71a8;box-shadow:none}

.mentor-countdown text{display:block;margin-bottom:8rpx;color:#7590bc;font-size:18rpx;letter-spacing:0;font-weight:750}
.mentor-waiting-page { background: var(--gyt-page-bg); }
.mentor-waiting-main,.mentor-waiting-person-card,.mentor-waiting-flow-card,.mentor-waiting-notice,.mentor-demo-card { border-color: var(--gyt-primary-border, #d6e6ff); background: var(--gyt-panel-bg, #ffffff); box-shadow: 0 14rpx 34rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.07)); }
.mentor-waiting-icon.waiting,.mentor-countdown,.mentor-waiting-avatar.tone-blue,.mentor-waiting-name text,.mentor-waiting-flow text.active,.mentor-demo-actions button.light,.mentor-waiting-footer button.secondary { background: var(--gyt-primary-soft, #edf4ff); color: var(--gyt-primary, #3478f6); }
.mentor-demo-actions button,.mentor-waiting-footer button { background: var(--gyt-primary-gradient, #3478f6); box-shadow: 0 10rpx 22rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.2)); }
</style>
