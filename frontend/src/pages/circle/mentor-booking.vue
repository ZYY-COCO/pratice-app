<template>
  <view class="mentor-booking-page">
    <MentorPageHeader title="预约咨询" @back="goBack" />

    <scroll-view scroll-y class="mentor-booking-scroll">
      <view v-if="mentor" class="mentor-booking-content">
        <view class="mentor-booking-hero">
          <view class="mentor-booking-avatar" :class="`tone-${mentor.avatarTone || 'blue'}`">{{ mentor.avatar }}</view>
          <view class="mentor-booking-hero-copy">
            <view class="mentor-booking-name-row">
              <text>{{ mentor.maskedName }}</text>
              <text>✓ 已认证</text>
            </view>
            <view>{{ mentor.school }} · {{ mentor.major }}</view>
            <view class="mentor-booking-rating">★ {{ Number(mentor.rating).toFixed(1) }} <text>· {{ mentor.priceLabel }} / 次</text></view>
          </view>
        </view>

        <view class="mentor-booking-heading">
          <view>
            <view class="mentor-booking-title">选择预约时间</view>
            <view class="mentor-booking-copy">以下时间由前辈主动开放，支付后即为你保留。</view>
          </view>
          <view class="mentor-booking-window">60分钟</view>
        </view>

        <view v-for="group in slotGroups" :key="group.date" class="mentor-booking-date-card">
          <view class="mentor-booking-date">{{ group.date }}</view>
          <view class="mentor-booking-slots">
            <button
              v-for="slot in group.slots"
              :key="slot.id"
              class="mentor-booking-slot"
              :class="{ selected: selectedSlotId === slot.id, unavailable: slot.status !== 'available' }"
              :disabled="slot.status !== 'available'"
              @tap="selectSlot(slot)"
            >
              <text>{{ slot.time }}</text>
              <view>{{ slot.status === 'available' ? `¥${slot.price}` : '已约满' }}</view>
            </button>
          </view>
        </view>

        <view class="mentor-booking-notice">
          <text>预约说明</text>
          <view>付款后不需要再次等待接单；在预约时间到达后即可开始本次 60 分钟文字与语音消息咨询。</view>
        </view>
      </view>
      <view v-else class="mentor-booking-missing">未找到该前辈可预约的时间</view>
      <view class="mentor-booking-bottom-space"></view>
    </scroll-view>

    <view v-if="mentor" class="mentor-booking-footer">
      <view class="mentor-booking-selection">
        <text>{{ selectedSlot ? `${selectedSlot.date} ${selectedSlot.time}` : '请选择一个可预约时间' }}</text>
        <view v-if="selectedSlot">¥{{ selectedSlot.price }} / 次</view>
      </view>
      <button :disabled="!selectedSlot" @tap="nextStep">下一步</button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import { getMentorById, startConsultationDraft } from '../../data/mentorConsultation'

const mentor = ref(null)
const selectedSlotId = ref('')

const slotGroups = computed(() => {
  const groups = []
  const groupMap = new Map()
  for (const slot of mentor.value?.availableSlots || []) {
    if (!groupMap.has(slot.date)) {
      const group = { date: slot.date, slots: [] }
      groupMap.set(slot.date, group)
      groups.push(group)
    }
    groupMap.get(slot.date).slots.push(slot)
  }
  return groups
})

const selectedSlot = computed(() => (
  (mentor.value?.availableSlots || []).find((slot) => slot.id === selectedSlotId.value) || null
))

onLoad((options) => {
  mentor.value = getMentorById(options?.mentorId)
})

function selectSlot(slot) {
  if (slot?.status === 'available') selectedSlotId.value = slot.id
}

function nextStep() {
  if (!mentor.value || !selectedSlot.value) return
  startConsultationDraft({
    mentorId: mentor.value.id,
    consultationType: 'booking',
    bookingSlot: selectedSlot.value
  })
  uni.navigateTo({
    url: `/pages/circle/mentor-consult-form?mentorId=${encodeURIComponent(mentor.value.id)}&mode=booking`
  })
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/home/index?tab=circle&section=community&communityTab=mentor' })
    }
  })
}
</script>

<style scoped>
.mentor-booking-page { height: 100vh; overflow: hidden; background: #f4f8ff; display: flex; flex-direction: column; }
.mentor-booking-scroll { min-height: 0; flex: 1; }
.mentor-booking-content { padding: 26rpx 24rpx 0; }

.mentor-booking-hero,
.mentor-booking-date-card,
.mentor-booking-notice {
  border: 2rpx solid #d9e7fc;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.91);
  box-shadow: 0 14rpx 34rpx rgba(52, 120, 246, 0.07);
}

.mentor-booking-hero { padding: 26rpx; display: flex; align-items: center; gap: 16rpx; }
.mentor-booking-avatar { width: 78rpx; height: 78rpx; border: 3rpx solid #fff; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 29rpx; font-weight: 900; flex-shrink: 0; }
.mentor-booking-avatar.tone-blue { background: #e6efff; color: #3478f6; }
.mentor-booking-avatar.tone-mint { background: #e2f4ef; color: #198777; }
.mentor-booking-avatar.tone-violet { background: #eeeafe; color: #7162bd; }
.mentor-booking-avatar.tone-warm { background: #f9eee1; color: #b66c32; }
.mentor-booking-hero-copy { min-width: 0; flex: 1; color: #6f7f95; font-size: 21rpx; line-height: 1.4; font-weight: 700; }
.mentor-booking-name-row { display: flex; align-items: center; gap: 10rpx; margin-bottom: 6rpx; }
.mentor-booking-name-row > text:first-child { color: #1e2b40; font-size: 28rpx; font-weight: 900; }
.mentor-booking-name-row > text:last-child { padding: 5rpx 9rpx; border-radius: 999rpx; background: #edf4ff; color: #3478f6; font-size: 17rpx; font-weight: 800; }
.mentor-booking-rating { margin-top: 8rpx; color: #dc942d; font-weight: 900; }
.mentor-booking-rating text { color: #6f7f95; font-weight: 700; }

.mentor-booking-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 18rpx; margin: 30rpx 6rpx 18rpx; }
.mentor-booking-title { color: #243651; font-size: 30rpx; line-height: 1.25; font-weight: 900; }
.mentor-booking-copy { margin-top: 8rpx; color: #8290a3; font-size: 21rpx; line-height: 1.45; font-weight: 600; }
.mentor-booking-window { margin-top: 4rpx; padding: 8rpx 12rpx; border-radius: 12rpx; background: #edf4ff; color: #4d72ab; font-size: 19rpx; line-height: 1.2; font-weight: 800; white-space: nowrap; }

.mentor-booking-date-card { padding: 24rpx; }
.mentor-booking-date-card + .mentor-booking-date-card { margin-top: 16rpx; }
.mentor-booking-date { color: #354864; font-size: 25rpx; line-height: 1.25; font-weight: 900; }
.mentor-booking-slots { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12rpx; margin-top: 18rpx; }
.mentor-booking-slot { min-height: 106rpx; margin: 0; padding: 12rpx; border: 2rpx solid #cfe0fb; border-radius: 18rpx; background: #fbfdff; color: #3d5474; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 8rpx; font-size: 22rpx; line-height: 1.2; font-weight: 850; }
.mentor-booking-slot::after, .mentor-booking-footer button::after { border: 0; }
.mentor-booking-slot view { color: #3478f6; font-size: 20rpx; }
.mentor-booking-slot.selected { border-color: #3478f6; background: #edf4ff; color: #3478f6; box-shadow: 0 8rpx 18rpx rgba(52, 120, 246, 0.12); }
.mentor-booking-slot.unavailable { border-color: #edf0f5; background: #f4f6f8; color: #a5afbd; }
.mentor-booking-slot.unavailable view { color: #a5afbd; }

.mentor-booking-notice { margin-top: 18rpx; padding: 24rpx; color: #718198; font-size: 21rpx; line-height: 1.6; font-weight: 600; }
.mentor-booking-notice text { display: block; margin-bottom: 8rpx; color: #46608a; font-size: 23rpx; font-weight: 850; }
.mentor-booking-bottom-space { height: calc(150rpx + env(safe-area-inset-bottom)); }
.mentor-booking-missing { padding: 150rpx 36rpx; color: #7b8da6; text-align: center; font-size: 25rpx; font-weight: 700; }

.mentor-booking-footer { padding: 16rpx 24rpx calc(18rpx + env(safe-area-inset-bottom)); border-top: 2rpx solid #dbe7f8; background: rgba(255,255,255,0.97); display: flex; align-items: center; gap: 16rpx; }
.mentor-booking-selection { min-width: 0; flex: 1; }
.mentor-booking-selection text { display: block; overflow: hidden; color: #4e627e; font-size: 20rpx; line-height: 1.3; font-weight: 700; text-overflow: ellipsis; white-space: nowrap; }
.mentor-booking-selection view { margin-top: 5rpx; color: #1e2d42; font-size: 27rpx; line-height: 1.2; font-weight: 900; }
.mentor-booking-footer button { min-width: 178rpx; min-height: 74rpx; margin: 0; border: 0; border-radius: 20rpx; background: #3478f6; color: #fff; font-size: 24rpx; font-weight: 900; box-shadow: 0 10rpx 22rpx rgba(52,120,246,.2); }
.mentor-booking-footer button[disabled] { background: #bdcadc; box-shadow: none; }
</style>
