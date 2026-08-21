<template>
  <view class="mentor-schedule-page">
    <MentorPageHeader title="预约时段" @back="goBack" />

    <scroll-view scroll-y class="mentor-schedule-scroll">
      <view class="mentor-schedule-content">
        <view class="mentor-schedule-intro">
          <view class="mentor-schedule-intro-icon">时</view>
          <view>
            <strong>设置可预约时间</strong>
            <text>暂不接即时咨询时，考生可预约你在此处开放的 60 分钟咨询时段。</text>
          </view>
        </view>

        <view class="mentor-schedule-card mentor-schedule-create-card">
          <view class="mentor-schedule-card-heading">
            <view>
              <strong>新增预约时段</strong>
              <text>每个时段固定为 60 分钟</text>
            </view>
            <view class="mentor-schedule-window">60分钟</view>
          </view>

          <view class="mentor-schedule-field">
            <text>日期</text>
            <picker mode="date" :start="minimumDate" :value="selectedDate" @change="selectDate">
              <view class="mentor-schedule-picker">
                <text>{{ formattedSelectedDate }}</text>
                <text>⌄</text>
              </view>
            </picker>
          </view>

          <view class="mentor-schedule-field">
            <text>开始时间</text>
            <picker mode="selector" :range="startTimeOptions" :value="selectedStartTimeIndex" @change="selectStartTime">
              <view class="mentor-schedule-picker">
                <text>{{ selectedStartTime }}</text>
                <text>⌄</text>
              </view>
            </picker>
            <view class="mentor-schedule-end-time">咨询将于 {{ selectedEndTime }} 结束</view>
          </view>

          <view class="mentor-schedule-field">
            <text>本时段价格</text>
            <view class="mentor-schedule-price-input">
              <text>¥</text>
              <input v-model="slotPrice" type="number" maxlength="5" />
              <text>/ 次</text>
            </view>
          </view>

          <button class="mentor-schedule-add-button" :loading="slotSaving" @tap="addAvailabilitySlot">
            {{ slotSaving ? '正在添加…' : '添加预约时段' }}
          </button>
        </view>

        <view class="mentor-schedule-card mentor-schedule-list-card">
          <view class="mentor-schedule-card-heading">
            <view>
              <strong>已设置时段</strong>
              <text>关闭后不会再展示给考生，已预约时段会继续保留。</text>
            </view>
            <button class="mentor-schedule-refresh" :loading="scheduleLoading" @tap="loadSchedule">刷新</button>
          </view>

          <view v-if="scheduleLoading && !availabilitySlots.length" class="mentor-schedule-empty">正在加载预约时段…</view>
          <view v-else-if="!availabilitySlots.length" class="mentor-schedule-empty">
            还没有开放预约时间。添加一个时段后，考生即可在你的详情页预约。
          </view>
          <view v-else class="mentor-schedule-slot-list">
            <view v-for="slot in availabilitySlots" :key="slot.id" class="mentor-schedule-slot-item">
              <view class="mentor-schedule-slot-main">
                <view class="mentor-schedule-slot-date">{{ formatSlotDate(slot.startsAt) }}</view>
                <view class="mentor-schedule-slot-time">{{ formatSlotTime(slot.startsAt, slot.endsAt) }}</view>
                <view class="mentor-schedule-slot-price">¥{{ formatPrice(slot.price) }} / 次</view>
              </view>
              <view class="mentor-schedule-slot-side">
                <view class="mentor-schedule-slot-status" :class="slot.status">{{ getSlotStatusLabel(slot.status) }}</view>
                <button
                  v-if="slot.status === 'available'"
                  :loading="slotUpdatingId === slot.id"
                  @tap="updateSlotStatus(slot, 'closed')"
                >关闭</button>
                <button
                  v-else-if="slot.status === 'closed' && isFutureSlot(slot)"
                  class="reopen"
                  :loading="slotUpdatingId === slot.id"
                  @tap="updateSlotStatus(slot, 'available')"
                >重新开放</button>
              </view>
            </view>
          </view>
        </view>

        <view class="mentor-schedule-bottom-space"></view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import {
  createMyMentorAvailabilitySlot,
  fetchMyMentorAvailabilitySlots,
  fetchMyMentorProfile,
  updateMyMentorAvailabilitySlot
} from '../../api/mentorConsultation'
import { normalizeMentorDetailResponse } from '../../data/mentorConsultation'

const startTimeOptions = ['09:00', '10:30', '13:00', '14:30', '16:00', '19:30', '21:00']
const selectedDate = ref(formatDateInput(addDays(new Date(), 1)))
const selectedStartTimeIndex = ref(0)
const slotPrice = ref('39')
const mentorProfile = ref(null)
const availabilitySlots = ref([])
const scheduleLoading = ref(false)
const slotSaving = ref(false)
const slotUpdatingId = ref('')

const minimumDate = computed(() => formatDateInput(new Date()))
const selectedStartTime = computed(() => startTimeOptions[selectedStartTimeIndex.value] || startTimeOptions[0])
const selectedEndTime = computed(() => addMinutesToTime(selectedStartTime.value, 60))
const formattedSelectedDate = computed(() => formatDateLabel(selectedDate.value))

onLoad(() => {
  void loadSchedule()
})

async function loadSchedule() {
  if (scheduleLoading.value) return
  scheduleLoading.value = true
  try {
    const [profilePayload, slotsPayload] = await Promise.all([
      fetchMyMentorProfile(),
      fetchMyMentorAvailabilitySlots({ limit: 100 })
    ])
    const profile = normalizeMentorDetailResponse(profilePayload)
    if (profile) {
      mentorProfile.value = profile
      if (!String(slotPrice.value || '').trim() || slotPrice.value === '39') {
        slotPrice.value = String(profile.price ?? 39)
      }
    }
    availabilitySlots.value = normalizeAvailabilitySlots(slotsPayload?.items)
  } catch (error) {
    uni.showToast({ title: error?.detail || '预约时段加载失败，请稍后重试', icon: 'none' })
  } finally {
    scheduleLoading.value = false
  }
}

function selectDate(event) {
  const value = String(event?.detail?.value || '')
  if (value) selectedDate.value = value
}

function selectStartTime(event) {
  const nextIndex = Number(event?.detail?.value)
  if (Number.isInteger(nextIndex) && startTimeOptions[nextIndex]) {
    selectedStartTimeIndex.value = nextIndex
  }
}

async function addAvailabilitySlot() {
  if (slotSaving.value) return
  const price = Number(slotPrice.value)
  if (!Number.isFinite(price) || price < 0 || price > 1000) {
    uni.showToast({ title: '请输入 0–1000 元之间的预约价格', icon: 'none' })
    return
  }

  const startsAt = buildLocalIso(selectedDate.value, selectedStartTime.value)
  const endsAt = buildLocalIso(selectedDate.value, selectedEndTime.value)
  if (!startsAt || !endsAt) {
    uni.showToast({ title: '请选择正确的日期和时间', icon: 'none' })
    return
  }

  slotSaving.value = true
  try {
    const created = await createMyMentorAvailabilitySlot({
      starts_at: startsAt,
      ends_at: endsAt,
      price_cents: Math.round(price * 100)
    })
    availabilitySlots.value = sortAvailabilitySlots([
      ...availabilitySlots.value,
      normalizeAvailabilitySlot(created)
    ])
    uni.showToast({ title: '预约时段已开放', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '预约时段添加失败，请稍后重试', icon: 'none' })
  } finally {
    slotSaving.value = false
  }
}

async function updateSlotStatus(slot, status) {
  if (!slot?.id || slotUpdatingId.value) return
  slotUpdatingId.value = slot.id
  try {
    const updated = normalizeAvailabilitySlot(await updateMyMentorAvailabilitySlot(slot.id, { status }))
    availabilitySlots.value = availabilitySlots.value.map((item) => item.id === updated.id ? updated : item)
    uni.showToast({ title: status === 'closed' ? '该预约时段已关闭' : '该预约时段已重新开放', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '预约时段更新失败，请稍后重试', icon: 'none' })
  } finally {
    slotUpdatingId.value = ''
  }
}

function normalizeAvailabilitySlots(value) {
  return sortAvailabilitySlots((Array.isArray(value) ? value : []).map(normalizeAvailabilitySlot).filter((item) => item.id))
}

function normalizeAvailabilitySlot(raw = {}) {
  return {
    id: String(raw.id || ''),
    startsAt: String(raw.startsAt || raw.starts_at || ''),
    endsAt: String(raw.endsAt || raw.ends_at || ''),
    price: Number(raw.price ?? (raw.price_cents == null ? 0 : Number(raw.price_cents) / 100)) || 0,
    status: String(raw.status || 'available')
  }
}

function sortAvailabilitySlots(slots) {
  return [...slots].sort((left, right) => Date.parse(left.startsAt || '') - Date.parse(right.startsAt || ''))
}

function formatDateInput(date) {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}

function addDays(date, days) {
  const next = new Date(date)
  next.setDate(next.getDate() + days)
  return next
}

function addMinutesToTime(value, minutes) {
  const [hours, mins] = String(value || '00:00').split(':').map(Number)
  const total = (Number(hours) || 0) * 60 + (Number(mins) || 0) + minutes
  return `${String(Math.floor(total / 60) % 24).padStart(2, '0')}:${String(total % 60).padStart(2, '0')}`
}

function buildLocalIso(dateText, timeText) {
  const value = new Date(`${dateText}T${timeText}:00`)
  if (Number.isNaN(value.getTime())) return ''
  const offsetMinutes = -value.getTimezoneOffset()
  const sign = offsetMinutes >= 0 ? '+' : '-'
  const absoluteOffset = Math.abs(offsetMinutes)
  const offsetHours = String(Math.floor(absoluteOffset / 60)).padStart(2, '0')
  const offsetMins = String(absoluteOffset % 60).padStart(2, '0')
  return `${formatDateInput(value)}T${String(value.getHours()).padStart(2, '0')}:${String(value.getMinutes()).padStart(2, '0')}:00${sign}${offsetHours}:${offsetMins}`
}

function formatDateLabel(value) {
  const date = new Date(`${String(value || '')}T12:00:00`)
  if (Number.isNaN(date.getTime())) return '请选择日期'
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${date.getMonth() + 1}月${date.getDate()}日 ${weekdays[date.getDay()]}`
}

function formatSlotDate(value) {
  const date = new Date(value || '')
  if (Number.isNaN(date.getTime())) return '待确认日期'
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${date.getMonth() + 1}月${date.getDate()}日 ${weekdays[date.getDay()]}`
}

function formatSlotTime(startsAt, endsAt) {
  const start = new Date(startsAt || '')
  const end = new Date(endsAt || '')
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime())) return '时间待确认'
  const formatTime = (date) => `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
  return `${formatTime(start)}–${formatTime(end)}`
}

function formatPrice(value) {
  const price = Number(value) || 0
  return Number.isInteger(price) ? String(price) : price.toFixed(2)
}

function getSlotStatusLabel(status) {
  return ({ available: '已开放', booked: '已预约', closed: '已关闭', expired: '已过期' })[status] || '处理中'
}

function isFutureSlot(slot) {
  const endsAt = new Date(slot?.endsAt || '')
  return !Number.isNaN(endsAt.getTime()) && endsAt.getTime() > Date.now()
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/circle/mentor-apply?mode=center' })
    }
  })
}
</script>

<style scoped>
.mentor-schedule-page { height: 100vh; overflow: hidden; background: #f4f8ff; display: flex; flex-direction: column; }
.mentor-schedule-scroll { min-height: 0; flex: 1; }
.mentor-schedule-content { padding: 22rpx 24rpx 0; }
.mentor-schedule-intro,
.mentor-schedule-card { border: 2rpx solid #d9e7fc; border-radius: 28rpx; background: rgba(255, 255, 255, .93); box-shadow: 0 14rpx 34rpx rgba(52, 120, 246, .06); }
.mentor-schedule-intro { padding: 24rpx; display: flex; align-items: center; gap: 16rpx; }
.mentor-schedule-intro-icon { width: 64rpx; height: 64rpx; border-radius: 20rpx; background: #e8f1ff; color: #3478f6; display: flex; align-items: center; justify-content: center; font-size: 26rpx; font-weight: 900; flex-shrink: 0; }
.mentor-schedule-intro strong,
.mentor-schedule-intro text { display: block; }
.mentor-schedule-intro strong { color: #314562; font-size: 25rpx; line-height: 1.25; font-weight: 900; }
.mentor-schedule-intro text { margin-top: 7rpx; color: #7f90a8; font-size: 19rpx; line-height: 1.48; font-weight: 650; }
.mentor-schedule-card { margin-top: 18rpx; padding: 26rpx; }
.mentor-schedule-card-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 18rpx; }
.mentor-schedule-card-heading strong,
.mentor-schedule-card-heading text { display: block; }
.mentor-schedule-card-heading strong { color: #354966; font-size: 26rpx; line-height: 1.25; font-weight: 900; }
.mentor-schedule-card-heading text { margin-top: 7rpx; color: #8696aa; font-size: 18rpx; line-height: 1.45; font-weight: 650; }
.mentor-schedule-window { margin-top: 2rpx; padding: 8rpx 12rpx; border-radius: 12rpx; background: #edf4ff; color: #4e73ac; font-size: 18rpx; line-height: 1.2; font-weight: 850; white-space: nowrap; }
.mentor-schedule-field { margin-top: 22rpx; }
.mentor-schedule-field > text { display: block; margin-bottom: 10rpx; color: #536881; font-size: 21rpx; line-height: 1.25; font-weight: 850; }
.mentor-schedule-picker { box-sizing: border-box; min-height: 72rpx; padding: 0 18rpx; border: 2rpx solid #dce8fa; border-radius: 18rpx; background: #fbfdff; color: #334962; display: flex; align-items: center; justify-content: space-between; font-size: 22rpx; line-height: 1.2; font-weight: 750; }
.mentor-schedule-picker text:last-child { color: #8293ab; font-size: 25rpx; }
.mentor-schedule-end-time { margin-top: 8rpx; color: #8c9bb0; font-size: 18rpx; line-height: 1.4; font-weight: 650; }
.mentor-schedule-price-input { box-sizing: border-box; height: 72rpx; padding: 0 18rpx; border: 2rpx solid #dce8fa; border-radius: 18rpx; background: #fbfdff; color: #4b6690; display: flex; align-items: center; gap: 8rpx; }
.mentor-schedule-price-input input { min-width: 0; height: 68rpx; flex: 1; padding: 0; border: 0; background: transparent; color: #314762; font-size: 24rpx; font-weight: 850; }
.mentor-schedule-price-input text { margin: 0; color: #6380ab; font-size: 22rpx; font-weight: 850; }
.mentor-schedule-add-button { width: 100%; min-height: 76rpx; margin: 26rpx 0 0; border: 0; border-radius: 20rpx; background: #3478f6; color: #fff; font-size: 24rpx; font-weight: 900; box-shadow: 0 10rpx 22rpx rgba(52, 120, 246, .2); }
.mentor-schedule-add-button::after,
.mentor-schedule-refresh::after,
.mentor-schedule-slot-side button::after { border: 0; }
.mentor-schedule-refresh { min-width: 84rpx; min-height: 52rpx; margin: 0; padding: 0 14rpx; border: 0; border-radius: 15rpx; background: #edf4ff; color: #4e73aa; font-size: 20rpx; font-weight: 850; }
.mentor-schedule-empty { padding: 42rpx 10rpx 18rpx; color: #90a0b5; text-align: center; font-size: 20rpx; line-height: 1.55; font-weight: 650; }
.mentor-schedule-slot-list { margin-top: 16rpx; border-top: 2rpx solid #edf2f8; }
.mentor-schedule-slot-item { padding: 20rpx 0; border-bottom: 2rpx solid #edf2f8; display: flex; align-items: center; justify-content: space-between; gap: 18rpx; }
.mentor-schedule-slot-main { min-width: 0; flex: 1; }
.mentor-schedule-slot-date { color: #40556f; font-size: 22rpx; line-height: 1.25; font-weight: 850; }
.mentor-schedule-slot-time { margin-top: 7rpx; color: #2f435e; font-size: 25rpx; line-height: 1.25; font-weight: 900; }
.mentor-schedule-slot-price { margin-top: 7rpx; color: #8292a7; font-size: 18rpx; line-height: 1.25; font-weight: 700; }
.mentor-schedule-slot-side { display: flex; flex-direction: column; align-items: flex-end; gap: 12rpx; flex-shrink: 0; }
.mentor-schedule-slot-status { padding: 7rpx 11rpx; border-radius: 999rpx; background: #edf4ff; color: #4d72aa; font-size: 18rpx; line-height: 1.2; font-weight: 850; white-space: nowrap; }
.mentor-schedule-slot-status.booked { background: #fff4df; color: #b7791f; }.mentor-schedule-slot-status.closed { background: #f2f4f7; color: #8391a4; }.mentor-schedule-slot-status.expired { background: #fff0ee; color: #c97168; }
.mentor-schedule-slot-side button { min-width: 92rpx; min-height: 48rpx; margin: 0; padding: 0 12rpx; border: 2rpx solid #d7e5f8; border-radius: 14rpx; background: #f7faff; color: #5f7faa; font-size: 19rpx; line-height: 1.2; font-weight: 850; }
.mentor-schedule-slot-side button.reopen { border-color: #bfd7ff; background: #edf4ff; color: #3478f6; }
.mentor-schedule-bottom-space { height: calc(56rpx + env(safe-area-inset-bottom)); }
@media (max-width: 350px) { .mentor-schedule-content { padding-right: 18rpx; padding-left: 18rpx; }.mentor-schedule-card { padding: 22rpx; }.mentor-schedule-slot-side button { min-width: 82rpx; padding: 0 10rpx; } }
</style>
