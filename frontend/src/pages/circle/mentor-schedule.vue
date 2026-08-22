<template>
  <view class="mentor-schedule-page">
    <MentorPageHeader title="预约时段" @back="goBack" />

    <scroll-view scroll-y class="mentor-schedule-scroll">
      <view class="mentor-schedule-content">
        <view class="mentor-schedule-card mentor-schedule-create-card">
          <view class="mentor-schedule-field">
            <text>日期</text>
            <view class="mentor-schedule-date-options" role="radiogroup" aria-label="选择预约日期">
              <button
                v-for="option in selectableDates"
                :key="option.value"
                class="mentor-schedule-date-option"
                :class="{ selected: selectedDate === option.value }"
                :aria-pressed="selectedDate === option.value"
                @tap="selectDate(option.value)"
              >
                <text>{{ option.relativeLabel }}</text>
                <view>{{ option.label }}</view>
              </button>
            </view>
          </view>

          <view class="mentor-schedule-field mentor-schedule-time-field">
            <view class="mentor-schedule-time-heading">
              <text>选择放号时段</text>
              <text>09:00–23:00</text>
            </view>
            <view class="mentor-schedule-time-grid" role="group" aria-label="可多选放号时段" aria-multiselectable="true">
              <button
                v-for="timeSlot in timeSlotOptions"
                :key="timeSlot.id"
                class="mentor-schedule-time-slot"
                :class="{
                  selected: selectedTimeSlotIds.includes(timeSlot.id),
                  unavailable: isTimeSlotUnavailable(timeSlot)
                }"
                :disabled="isTimeSlotUnavailable(timeSlot)"
                :aria-pressed="selectedTimeSlotIds.includes(timeSlot.id)"
                @tap="selectTimeSlot(timeSlot)"
              >
                <text>{{ timeSlot.label }}</text>
                <view v-if="getTimeSlotHint(timeSlot)">{{ getTimeSlotHint(timeSlot) }}</view>
              </button>
            </view>
          </view>

          <view class="mentor-schedule-field">
            <text>价格</text>
            <view class="mentor-schedule-fixed-price">
              <text>¥ {{ fixedSlotPriceLabel }}</text>
              <text>/ 次</text>
            </view>
            <view class="mentor-schedule-price-tip">价格调整需重新提交审核</view>
          </view>

          <button class="mentor-schedule-add-button" :disabled="!mentorProfile || !selectedTimeSlots.length || slotSaving" :loading="slotSaving" @tap="addAvailabilitySlot">
            {{ slotSaving ? '正在添加…' : '添加预约时段' }}
          </button>
        </view>

        <view class="mentor-schedule-card mentor-schedule-list-card">
          <view class="mentor-schedule-card-heading">
            <view>
              <strong>已设置时段</strong>
              <text>仅显示已开放或已预约的时段。</text>
            </view>
            <button class="mentor-schedule-refresh" :loading="scheduleLoading" @tap="loadSchedule">刷新</button>
          </view>

          <view v-if="scheduleLoading && !displayedAvailabilitySlots.length" class="mentor-schedule-empty">正在加载预约时段…</view>
          <view v-else-if="!displayedAvailabilitySlots.length" class="mentor-schedule-empty">
            还没有开放预约时间。添加一个时段后，考生即可在你的详情页预约。
          </view>
          <view v-else class="mentor-schedule-slot-list">
            <view v-for="slot in displayedAvailabilitySlots" :key="slot.id" class="mentor-schedule-slot-item">
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
import { computed, ref, watch } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import {
  createMyMentorAvailabilitySlot,
  fetchMyMentorAvailabilitySlots,
  fetchMyMentorProfile,
  updateMyMentorAvailabilitySlot
} from '../../api/mentorConsultation'
import { normalizeMentorDetailResponse } from '../../data/mentorConsultation'

const MENTOR_SLOT_FIRST_HOUR = 9
const MENTOR_SLOT_LAST_HOUR = 23
const timeSlotOptions = Array.from({ length: MENTOR_SLOT_LAST_HOUR - MENTOR_SLOT_FIRST_HOUR }, (_, index) => {
  const startHour = MENTOR_SLOT_FIRST_HOUR + index
  const endHour = startHour + 1
  const startTime = `${String(startHour).padStart(2, '0')}:00`
  const endTime = `${String(endHour).padStart(2, '0')}:00`
  return { id: `${startTime}-${endTime}`, startTime, endTime, label: `${startTime}–${endTime}` }
})
const selectedDate = ref(formatDateInput(addDays(new Date(), 1)))
const selectedTimeSlotIds = ref([])
const mentorProfile = ref(null)
const availabilitySlots = ref([])
const scheduleLoading = ref(false)
const slotSaving = ref(false)
const slotUpdatingId = ref('')

const minimumDate = computed(() => formatDateInput(new Date()))
const selectableDates = computed(() => ['今天', '明天', '后天'].map((relativeLabel, offset) => {
  const value = formatDateInput(addDays(new Date(`${minimumDate.value}T12:00:00`), offset))
  return { value, relativeLabel, label: formatDateLabel(value) }
}))
const selectedTimeSlots = computed(() => timeSlotOptions.filter((item) => selectedTimeSlotIds.value.includes(item.id)))
const fixedSlotPriceLabel = computed(() => mentorProfile.value ? formatPrice(mentorProfile.value.price) : '—')
const displayedAvailabilitySlots = computed(() => availabilitySlots.value.filter((slot) => slot.status !== 'closed'))

watch([selectedDate, availabilitySlots], () => {
  ensureSelectedTimeSlots()
})

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
    }
    availabilitySlots.value = normalizeAvailabilitySlots(slotsPayload?.items)
  } catch (error) {
    uni.showToast({ title: error?.detail || '预约时段加载失败，请稍后重试', icon: 'none' })
  } finally {
    scheduleLoading.value = false
  }
}

function selectDate(value) {
  const nextDate = String(value || '')
  if (selectableDates.value.some((option) => option.value === nextDate)) {
    selectedDate.value = nextDate
  }
}

function selectTimeSlot(timeSlot) {
  if (!timeSlot || isTimeSlotUnavailable(timeSlot)) return
  selectedTimeSlotIds.value = selectedTimeSlotIds.value.includes(timeSlot.id)
    ? selectedTimeSlotIds.value.filter((id) => id !== timeSlot.id)
    : [...selectedTimeSlotIds.value, timeSlot.id]
}

async function addAvailabilitySlot() {
  if (slotSaving.value) return
  if (!mentorProfile.value?.id) {
    uni.showToast({ title: '正在同步审核通过的价格，请稍后重试', icon: 'none' })
    return
  }

  const slotsToCreate = selectedTimeSlots.value.filter((timeSlot) => !isTimeSlotUnavailable(timeSlot))
  if (!slotsToCreate.length) {
    uni.showToast({ title: '请选择一个可放号的整点时段', icon: 'none' })
    return
  }

  const slotPayloads = slotsToCreate.map((timeSlot) => ({
    starts_at: buildLocalIso(selectedDate.value, timeSlot.startTime),
    ends_at: buildLocalIso(selectedDate.value, timeSlot.endTime)
  }))
  if (slotPayloads.some((payload) => !payload.starts_at || !payload.ends_at)) {
    uni.showToast({ title: '请选择正确的日期和时间', icon: 'none' })
    return
  }

  slotSaving.value = true
  try {
    const results = await Promise.allSettled(slotPayloads.map((payload) => createMyMentorAvailabilitySlot(payload)))
    const createdSlots = results
      .filter((result) => result.status === 'fulfilled')
      .map((result) => normalizeAvailabilitySlot(result.value))
      .filter((slot) => slot.id)

    if (createdSlots.length) {
      availabilitySlots.value = sortAvailabilitySlots([...availabilitySlots.value, ...createdSlots])
    }

    const failedResults = results.filter((result) => result.status === 'rejected')
    if (failedResults.length) {
      const firstError = failedResults[0]?.reason
      uni.showToast({
        title: createdSlots.length
          ? `已开放 ${createdSlots.length} 个时段，${failedResults.length} 个未成功`
          : firstError?.detail || '预约时段添加失败，请稍后重试',
        icon: 'none'
      })
      return
    }

    uni.showToast({
      title: createdSlots.length > 1 ? `已开放 ${createdSlots.length} 个预约时段` : '预约时段已开放',
      icon: 'success'
    })
  } catch (error) {
    uni.showToast({ title: error?.detail || '预约时段添加失败，请稍后重试', icon: 'none' })
  } finally {
    slotSaving.value = false
  }
}

function ensureSelectedTimeSlots() {
  const selectableIds = selectedTimeSlotIds.value.filter((id) => {
    const timeSlot = timeSlotOptions.find((item) => item.id === id)
    return Boolean(timeSlot && !isTimeSlotUnavailable(timeSlot))
  })
  if (selectableIds.length !== selectedTimeSlotIds.value.length) {
    selectedTimeSlotIds.value = selectableIds
  }
}

function isTimeSlotUnavailable(timeSlot) {
  return isPastTimeSlot(timeSlot) || Boolean(getManagedTimeSlot(timeSlot))
}

function isPastTimeSlot(timeSlot) {
  const startsAt = Date.parse(buildLocalIso(selectedDate.value, timeSlot?.startTime))
  return Number.isFinite(startsAt) && startsAt <= Date.now() + 5 * 60 * 1000
}

function getManagedTimeSlot(timeSlot) {
  const startsAt = Date.parse(buildLocalIso(selectedDate.value, timeSlot?.startTime))
  const endsAt = Date.parse(buildLocalIso(selectedDate.value, timeSlot?.endTime))
  if (!Number.isFinite(startsAt) || !Number.isFinite(endsAt)) return null
  return availabilitySlots.value.find((slot) => {
    const slotStart = Date.parse(slot.startsAt || '')
    const slotEnd = Date.parse(slot.endsAt || '')
    return slot.status !== 'expired' && slotStart === startsAt && slotEnd === endsAt
  }) || null
}

function getTimeSlotHint(timeSlot) {
  const managedSlot = getManagedTimeSlot(timeSlot)
  if (managedSlot) return getSlotStatusLabel(managedSlot.status)
  return isPastTimeSlot(timeSlot) ? '不可选' : ''
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
.mentor-schedule-card { border: 2rpx solid #d9e7fc; border-radius: 28rpx; background: rgba(255, 255, 255, .93); box-shadow: 0 14rpx 34rpx rgba(52, 120, 246, .06); }
.mentor-schedule-card { margin-top: 18rpx; padding: 26rpx; }
.mentor-schedule-create-card { margin-top: 0; }
.mentor-schedule-create-card > .mentor-schedule-field:first-child { margin-top: 0; }
.mentor-schedule-card-heading { display: flex; align-items: flex-start; justify-content: space-between; gap: 18rpx; }
.mentor-schedule-card-heading strong,
.mentor-schedule-card-heading text { display: block; }
.mentor-schedule-card-heading strong { color: #354966; font-size: 26rpx; line-height: 1.25; font-weight: 900; }
.mentor-schedule-card-heading text { margin-top: 7rpx; color: #8696aa; font-size: 18rpx; line-height: 1.45; font-weight: 650; }
.mentor-schedule-field { margin-top: 22rpx; }
.mentor-schedule-field > text { display: block; margin-bottom: 10rpx; color: #536881; font-size: 21rpx; line-height: 1.25; font-weight: 850; }
.mentor-schedule-date-options { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10rpx; }
.mentor-schedule-date-option { box-sizing: border-box; min-height: 84rpx; margin: 0; padding: 10rpx 4rpx; border: 2rpx solid #dce8fa; border-radius: 16rpx; background: #fbfdff; color: #4a6180; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 20rpx; line-height: 1.2; font-weight: 850; }.mentor-schedule-date-option::after { border: 0; }.mentor-schedule-date-option view { margin-top: 5rpx; color: #8495aa; font-size: 16rpx; line-height: 1.2; font-weight: 700; white-space: nowrap; }.mentor-schedule-date-option.selected { border-color: #3478f6; background: #edf4ff; color: #3478f6; box-shadow: 0 8rpx 18rpx rgba(52, 120, 246, .1); }.mentor-schedule-date-option.selected view { color: #5d85c7; }
.mentor-schedule-time-heading { display: flex; align-items: center; justify-content: space-between; gap: 16rpx; margin-bottom: 10rpx; color: #536881; font-size: 21rpx; line-height: 1.25; font-weight: 850; }.mentor-schedule-time-heading > text:last-child { color: #8495ab; font-size: 18rpx; font-weight: 700; }
.mentor-schedule-time-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10rpx; }.mentor-schedule-time-slot { box-sizing: border-box; min-height: 68rpx; margin: 0; padding: 8rpx 4rpx; border: 2rpx solid #dce8fa; border-radius: 16rpx; background: #fbfdff; color: #425a78; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 18rpx; line-height: 1.15; font-weight: 850; white-space: nowrap; }.mentor-schedule-time-slot::after { border: 0; }.mentor-schedule-time-slot view { margin-top: 4rpx; color: #8897aa; font-size: 15rpx; line-height: 1; font-weight: 700; }.mentor-schedule-time-slot.selected { border-color: #3478f6; background: #edf4ff; color: #3478f6; box-shadow: 0 8rpx 18rpx rgba(52, 120, 246, .1); }.mentor-schedule-time-slot.unavailable { border-color: #edf1f6; background: #f5f7fa; color: #a7b2c0; box-shadow: none; }.mentor-schedule-time-slot.unavailable view { color: #a7b2c0; }
.mentor-schedule-fixed-price { box-sizing: border-box; min-height: 72rpx; padding: 0 18rpx; border: 2rpx solid #dce8fa; border-radius: 18rpx; background: #f6f8fc; color: #4b6690; display: flex; align-items: center; justify-content: space-between; gap: 8rpx; }.mentor-schedule-fixed-price text:first-child { color: #314762; font-size: 24rpx; font-weight: 850; }.mentor-schedule-fixed-price text:last-child { color: #6380ab; font-size: 22rpx; font-weight: 850; }.mentor-schedule-price-tip { margin-top: 8rpx; color: #8c9bb0; font-size: 18rpx; line-height: 1.4; font-weight: 650; }
.mentor-schedule-add-button { box-sizing: border-box; width: 100%; height: 76rpx; min-height: 76rpx; margin: 26rpx 0 0; padding: 0 20rpx; border: 0; border-radius: 20rpx; background: #3478f6; color: #fff; display: flex; align-items: center; justify-content: center; text-align: center; font-size: 24rpx; line-height: 1; font-weight: 900; white-space: nowrap; box-shadow: 0 10rpx 22rpx rgba(52, 120, 246, .2); }.mentor-schedule-add-button[disabled] { background: #bdcadc; box-shadow: none; }
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
.mentor-schedule-slot-side { display: flex; align-items: center; justify-content: flex-end; gap: 10rpx; flex-shrink: 0; }
.mentor-schedule-slot-status { box-sizing: border-box; min-height: 48rpx; padding: 0 13rpx; border-radius: 999rpx; background: #edf4ff; color: #4d72aa; display: flex; align-items: center; justify-content: center; font-size: 18rpx; line-height: 1; font-weight: 850; white-space: nowrap; }
.mentor-schedule-slot-status.booked { background: #fff4df; color: #b7791f; }.mentor-schedule-slot-status.closed { background: #f2f4f7; color: #8391a4; }.mentor-schedule-slot-status.expired { background: #fff0ee; color: #c97168; }
.mentor-schedule-slot-side button { box-sizing: border-box; min-width: 92rpx; height: 48rpx; min-height: 48rpx; margin: 0; padding: 0 12rpx; border: 2rpx solid #d7e5f8; border-radius: 14rpx; background: #f7faff; color: #5f7faa; display: flex; align-items: center; justify-content: center; text-align: center; font-size: 19rpx; line-height: 1; font-weight: 850; white-space: nowrap; }
.mentor-schedule-slot-side button.reopen { border-color: #bfd7ff; background: #edf4ff; color: #3478f6; }
.mentor-schedule-bottom-space { height: calc(56rpx + env(safe-area-inset-bottom)); }
@media (max-width: 350px) { .mentor-schedule-content { padding-right: 18rpx; padding-left: 18rpx; }.mentor-schedule-card { padding: 22rpx; }.mentor-schedule-slot-side button { min-width: 82rpx; padding: 0 10rpx; } }
</style>
