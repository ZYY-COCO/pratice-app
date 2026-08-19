<template>
  <view class="mentor-waiting-page">
    <MentorPageHeader :title="isBooking ? '预约成功' : '等待前辈接单'" @back="goBack" />

    <scroll-view scroll-y class="mentor-waiting-scroll">
      <view v-if="mentor" class="mentor-waiting-content">
        <view v-if="isBooking" class="mentor-waiting-main mentor-booked-main">
          <view class="mentor-waiting-icon booked">✓</view>
          <view class="mentor-waiting-title">预约成功</view>
          <view class="mentor-waiting-copy">已为你保留本次咨询时间，到预约时间即可进入咨询。</view>
          <view class="mentor-booked-slot">{{ bookingSlotLabel }}</view>
        </view>

        <view v-else-if="isFailed" class="mentor-waiting-main mentor-failed-main">
          <view class="mentor-waiting-icon failed">!</view>
          <view class="mentor-waiting-title">本次咨询未能成功接单</view>
          <view class="mentor-waiting-copy">{{ status === 'rejected' ? '前辈暂时未能接受本次咨询。' : '前辈在 10 分钟内未确认本次咨询。' }}费用将原路退回。</view>
        </view>

        <view v-else class="mentor-waiting-main">
          <view class="mentor-waiting-icon waiting">⌛</view>
          <view class="mentor-waiting-title">{{ status === 'accepted' ? '前辈已接单' : '已向前辈发送咨询请求' }}</view>
          <view class="mentor-waiting-copy">{{ status === 'accepted' ? '正在为你打开咨询窗口。' : '前辈将在 10 分钟内确认是否接受本次咨询。' }}</view>
          <view v-if="status !== 'accepted'" class="mentor-countdown">{{ countdownText }}</view>
        </view>

        <view class="mentor-waiting-person-card">
          <view class="mentor-waiting-avatar" :class="`tone-${mentor.avatarTone || 'blue'}`">{{ mentor.avatar }}</view>
          <view>
            <view class="mentor-waiting-name">{{ mentor.maskedName }} <text>✓ 已认证</text></view>
            <view>{{ mentor.school }} · {{ mentor.major }}</view>
            <view v-if="isBooking" class="mentor-waiting-booked-note">本次服务：{{ bookingSlotLabel }} · 60分钟</view>
          </view>
        </view>

        <view v-if="!isBooking && !isFailed" class="mentor-waiting-flow-card">
          <view class="mentor-waiting-flow-title">本次咨询流程</view>
          <view class="mentor-waiting-flow">
            <view><text class="done">1</text><text class="mentor-waiting-flow-copy">已支付咨询费用</text></view>
            <view><text class="active">2</text><text class="mentor-waiting-flow-copy">前辈确认接单</text></view>
            <view><text>3</text><text class="mentor-waiting-flow-copy">进入 60 分钟咨询</text></view>
          </view>
        </view>

        <view v-if="isBooking" class="mentor-waiting-notice">
          <text>预约说明</text>
          <view>这是前辈主动开放的可预约时间，因此不需要再次等待接单。这里提供“进入咨询（演示）”用于本地体验聊天页面。</view>
        </view>

        <view v-if="!isBooking && !isFailed" class="mentor-demo-card">
          <view>本地演示控制</view>
          <text>用于体验接单成功和超时退款两种前端状态，不会发起真实请求。</text>
          <view class="mentor-demo-actions">
            <button @tap="acceptConsultation">模拟接单</button>
            <button class="light" @tap="timeoutConsultation">模拟超时</button>
            <button class="light" @tap="rejectConsultation">模拟拒绝</button>
          </view>
        </view>
      </view>
      <view class="mentor-waiting-bottom-space"></view>
    </scroll-view>

    <view v-if="mentor" class="mentor-waiting-footer">
      <button v-if="isFailed" @tap="chooseAgain">重新选择前辈</button>
      <button v-else-if="isBooking" @tap="openChat">进入咨询（演示）</button>
      <button v-else-if="status === 'accepted'" @tap="openChat">进入聊天</button>
      <button v-else class="secondary" @tap="goBack">返回填写信息</button>
    </view>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import {
  getConsultationDraft,
  getMentorById,
  setConsultationOrderStatus
} from '../../data/mentorConsultation'

const mentor = ref(null)
const mode = ref('instant')
const status = ref('pending_accept')
const bookingSlot = ref(null)
const remainingSeconds = ref(598)
let countdownTimer = null

const isBooking = computed(() => mode.value === 'booking')
const isFailed = computed(() => ['timeout', 'rejected', 'refunded'].includes(status.value))
const bookingSlotLabel = computed(() => bookingSlot.value ? `${bookingSlot.value.date} ${bookingSlot.value.time}` : '已预约时间')
const countdownText = computed(() => {
  const minutes = String(Math.floor(Math.max(0, remainingSeconds.value) / 60)).padStart(2, '0')
  const seconds = String(Math.max(0, remainingSeconds.value) % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
})

onLoad((options) => {
  mode.value = options?.mode === 'booking' ? 'booking' : 'instant'
  mentor.value = getMentorById(options?.mentorId)
  const draft = getConsultationDraft()
  if (draft?.mentorId === mentor.value?.id) {
    status.value = draft.orderStatus || (mode.value === 'booking' ? 'booked' : 'pending_accept')
    bookingSlot.value = draft.bookingSlot || null
  }
  if (mode.value === 'booking') status.value = 'booked'
  if (!isBooking.value && !isFailed.value && status.value !== 'accepted') startCountdown()
})

onBeforeUnmount(stopCountdown)

function startCountdown() {
  stopCountdown()
  countdownTimer = setInterval(() => {
    if (remainingSeconds.value <= 1) {
      timeoutConsultation()
      return
    }
    remainingSeconds.value -= 1
  }, 1000)
}

function stopCountdown() {
  if (countdownTimer) clearInterval(countdownTimer)
  countdownTimer = null
}

function acceptConsultation() {
  if (isBooking.value || isFailed.value) return
  stopCountdown()
  status.value = 'accepted'
  setConsultationOrderStatus('accepted')
}

function timeoutConsultation() {
  if (isBooking.value || isFailed.value) return
  stopCountdown()
  remainingSeconds.value = 0
  status.value = 'timeout'
  setConsultationOrderStatus('timeout')
}

function rejectConsultation() {
  if (isBooking.value || isFailed.value) return
  stopCountdown()
  status.value = 'rejected'
  setConsultationOrderStatus('rejected')
}

function openChat() {
  if (!mentor.value) return
  stopCountdown()
  setConsultationOrderStatus('in_progress')
  uni.navigateTo({ url: `/pages/circle/mentor-chat?mentorId=${encodeURIComponent(mentor.value.id)}&mode=${mode.value}` })
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
.mentor-waiting-page { height: 100vh; overflow: hidden; background:#f4f8ff; display:flex; flex-direction:column; }
.mentor-waiting-scroll { min-height:0; flex:1; }.mentor-waiting-content { padding:32rpx 24rpx 0; }
.mentor-waiting-main { padding:38rpx 28rpx 32rpx; border:2rpx solid #d6e6ff; border-radius:30rpx; background:rgba(255,255,255,.94); text-align:center; box-shadow:0 16rpx 38rpx rgba(52,120,246,.08); }
.mentor-waiting-icon { width:92rpx; height:92rpx; margin:0 auto; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:45rpx; line-height:1; font-weight:900; }.mentor-waiting-icon.waiting{background:#edf4ff;color:#3478f6}.mentor-waiting-icon.booked{background:#e6f6ec;color:#26955a}.mentor-waiting-icon.failed{background:#fff0ee;color:#e46a5f}
.mentor-waiting-title { margin-top:20rpx; color:#243550; font-size:31rpx; line-height:1.25; font-weight:900; }.mentor-waiting-copy{margin-top:12rpx;color:#73839a;font-size:22rpx;line-height:1.55;font-weight:650}.mentor-countdown{margin:25rpx auto 0;padding:15rpx 28rpx;border-radius:18rpx;background:#f4f8ff;color:#3478f6;font-size:42rpx;line-height:1;font-weight:900;letter-spacing:2rpx;width:max-content}.mentor-booked-slot{margin-top:20rpx;color:#277b54;font-size:24rpx;font-weight:850}
.mentor-waiting-person-card,.mentor-waiting-flow-card,.mentor-waiting-notice,.mentor-demo-card { margin-top:18rpx; border:2rpx solid #dce8fa; border-radius:26rpx; background:rgba(255,255,255,.91); box-shadow:0 12rpx 30rpx rgba(52,120,246,.055); }
.mentor-waiting-person-card { padding:24rpx; display:flex; align-items:center; gap:15rpx; color:#7c8ca1;font-size:21rpx;line-height:1.4;font-weight:650; }.mentor-waiting-avatar{width:68rpx;height:68rpx;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:26rpx;font-weight:900;flex-shrink:0}.mentor-waiting-avatar.tone-blue{background:#e6efff;color:#3478f6}.mentor-waiting-avatar.tone-mint{background:#e2f4ef;color:#198777}.mentor-waiting-avatar.tone-violet{background:#eeeafe;color:#7162bd}.mentor-waiting-avatar.tone-warm{background:#f9eee1;color:#b66c32}.mentor-waiting-name{color:#354863;font-size:25rpx;font-weight:900}.mentor-waiting-name text{margin-left:8rpx;padding:5rpx 9rpx;border-radius:999rpx;background:#edf4ff;color:#3478f6;font-size:17rpx;font-weight:800}.mentor-waiting-booked-note{margin-top:5rpx;color:#3d9161;font-size:19rpx;font-weight:750}
.mentor-waiting-flow-card{padding:26rpx}.mentor-waiting-flow-title{color:#3e5472;font-size:24rpx;font-weight:900}.mentor-waiting-flow{margin-top:18rpx}.mentor-waiting-flow>view{position:relative;display:flex;align-items:center;gap:12rpx;color:#8391a4;font-size:21rpx;line-height:1.3;font-weight:700}.mentor-waiting-flow>view+view{margin-top:15rpx}.mentor-waiting-flow text{width:30rpx;height:30rpx;border-radius:50%;background:#e9eef6;color:#8290a4;display:inline-flex;align-items:center;justify-content:center;font-size:18rpx;font-weight:900;flex-shrink:0}.mentor-waiting-flow text.done{background:#e7f5ec;color:#249458}.mentor-waiting-flow text.active{background:#edf4ff;color:#3478f6}.mentor-waiting-flow text.mentor-waiting-flow-copy{width:auto;height:auto;border-radius:0;background:transparent;color:inherit;display:block;font-size:21rpx;font-weight:700}
.mentor-waiting-notice{padding:25rpx;color:#728399;font-size:21rpx;line-height:1.6;font-weight:650}.mentor-waiting-notice text{display:block;margin-bottom:8rpx;color:#42608c;font-size:24rpx;font-weight:900}
.mentor-demo-card{padding:24rpx;color:#7b8ca3;font-size:20rpx;line-height:1.55;font-weight:650}.mentor-demo-card>view:first-child{color:#48648e;font-size:24rpx;font-weight:900}.mentor-demo-card>text{display:block;margin-top:7rpx}.mentor-demo-actions{display:flex;flex-wrap:wrap;gap:10rpx;margin-top:18rpx}.mentor-demo-actions button{min-height:52rpx;margin:0;padding:0 16rpx;border:0;border-radius:15rpx;background:#3478f6;color:#fff;font-size:20rpx;font-weight:850}.mentor-demo-actions button::after,.mentor-waiting-footer button::after{border:0}.mentor-demo-actions button.light{background:#edf4ff;color:#4d72ab}
.mentor-waiting-bottom-space{height:calc(150rpx + env(safe-area-inset-bottom))}.mentor-waiting-footer{padding:16rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));border-top:2rpx solid #dbe7f8;background:rgba(255,255,255,.97)}.mentor-waiting-footer button{width:100%;min-height:76rpx;margin:0;border:0;border-radius:20rpx;background:#3478f6;color:#fff;font-size:24rpx;font-weight:900;box-shadow:0 10rpx 22rpx rgba(52,120,246,.2)}.mentor-waiting-footer button.secondary{background:#edf4ff;color:#4f71a8;box-shadow:none}
</style>
