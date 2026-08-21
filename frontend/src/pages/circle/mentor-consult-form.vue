<template>
  <view class="mentor-form-page">
    <MentorPageHeader title="填写咨询信息" @back="goBack" />

    <scroll-view scroll-y class="mentor-form-scroll">
      <view v-if="mentor" class="mentor-form-content">
        <view class="mentor-form-intro">
          为了让前辈提前了解你的情况，请先填写以下信息。支付成功后，这些信息会发送给前辈。
        </view>

        <view class="mentor-form-card">
          <view class="mentor-form-section-title">你的基本情况</view>
          <view class="mentor-form-field">
            <view class="mentor-form-label"><text>姓名 / 称呼</text><strong>必填</strong></view>
            <input v-model="questionnaire.name" placeholder="请输入姓名或称呼" placeholder-class="mentor-form-placeholder" />
          </view>
          <view class="mentor-form-field">
            <view class="mentor-form-label"><text>当前学校</text><strong>必填</strong></view>
            <input v-model="questionnaire.school" placeholder="请输入目前就读学校" placeholder-class="mentor-form-placeholder" />
          </view>
          <view class="mentor-form-field">
            <view class="mentor-form-label"><text>当前专业</text><strong>必填</strong></view>
            <input v-model="questionnaire.major" placeholder="请输入当前专业" placeholder-class="mentor-form-placeholder" />
          </view>
          <view class="mentor-form-field mentor-form-half-row">
            <view>
              <view class="mentor-form-label"><text>当前年级</text></view>
              <picker mode="selector" :range="gradeOptions" :value="gradeIndex" @change="selectGrade">
                <view class="mentor-form-picker">{{ questionnaire.grade }} <text>⌄</text></view>
              </picker>
            </view>
            <view>
              <view class="mentor-form-label"><text>预计毕业年份</text></view>
              <picker mode="selector" :range="yearOptions" :value="yearIndex" @change="selectGraduationYear">
                <view class="mentor-form-picker">{{ questionnaire.graduationYear }} <text>⌄</text></view>
              </picker>
            </view>
          </view>
        </view>

        <view class="mentor-form-card mentor-question-card">
          <view class="mentor-form-label mentor-question-label"><text>本次想咨询的问题</text><strong>建议填写</strong></view>
          <textarea
            v-model="questionnaire.question"
            maxlength="500"
            auto-height
            placeholder="请尽量具体描述你的问题，例如目标院校、专业选择、复习规划或复试准备等。"
            placeholder-class="mentor-form-placeholder"
          />
          <view class="mentor-question-count">{{ questionnaire.question.length }} / 500</view>
        </view>

        <view class="mentor-form-card mentor-order-summary">
          <view class="mentor-form-section-title">订单摘要</view>
          <view class="mentor-order-mentor">
            <view class="mentor-order-avatar" :class="`tone-${mentor.avatarTone || 'blue'}`">{{ mentor.avatar }}</view>
            <view><strong>{{ mentor.maskedName }}</strong><text>{{ mentor.school }} · {{ mentor.major }}</text></view>
          </view>
          <view class="mentor-order-lines">
            <view v-if="isBooking"><text>预约时间</text><strong>{{ bookingSlotLabel }}</strong></view>
            <view><text>咨询方式</text><strong>文字 / 语音消息</strong></view>
            <view><text>服务形式</text><strong>{{ isBooking ? '预约咨询' : '单次即时咨询' }}</strong></view>
            <view><text>咨询窗口</text><strong>{{ mentor.consultationWindowMinutes || 60 }}分钟</strong></view>
            <view class="mentor-order-price"><text>价格</text><strong>¥{{ orderPrice }}</strong></view>
          </view>
        </view>
      </view>
      <view v-else class="mentor-form-missing">前辈信息已失效，请返回重新选择。</view>
      <view class="mentor-form-bottom-space"></view>
    </scroll-view>

    <view v-if="mentor" class="mentor-form-footer">
      <view><text>{{ isBooking ? '确认预约' : '即时咨询' }}</text><strong>¥{{ orderPrice }}</strong></view>
      <button :loading="isPaying" @tap="submitOrder">{{ isPaying ? '支付处理中' : `确认并支付 ¥${orderPrice}` }}</button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import {
  createMentorConsultationOrder,
  mockPayMentorConsultationOrder
} from '../../api/mentorConsultation'
import {
  MENTOR_GRADE_OPTIONS,
  createDefaultConsultationQuestionnaire,
  getConsultationDraft,
  getMentorById,
  saveConsultationOrder,
  saveConsultationQuestionnaire,
  startConsultationDraft
} from '../../data/mentorConsultation'
import { isLoggedIn } from '../../utils/auth'

const mentor = ref(null)
const mode = ref('instant')
const questionnaire = ref(createDefaultConsultationQuestionnaire())
const bookingSlot = ref(null)
const isPaying = ref(false)
const gradeOptions = MENTOR_GRADE_OPTIONS
const yearOptions = ['2031', '2030', '2029', '2028', '2027', '2026', '2025', '2024']

const isBooking = computed(() => mode.value === 'booking')
const gradeIndex = computed(() => Math.max(0, gradeOptions.indexOf(questionnaire.value.grade)))
const yearIndex = computed(() => Math.max(0, yearOptions.indexOf(String(questionnaire.value.graduationYear))))
const orderPrice = computed(() => bookingSlot.value?.price ?? mentor.value?.price ?? 0)
const bookingSlotLabel = computed(() => bookingSlot.value ? `${bookingSlot.value.date} ${bookingSlot.value.time}` : '待选择')

onLoad((options) => {
  mode.value = options?.mode === 'booking' ? 'booking' : 'instant'
  mentor.value = getMentorById(options?.mentorId)
  if (!mentor.value) return

  const existingDraft = getConsultationDraft()
  const matchingDraft = existingDraft
    && existingDraft.mentorId === mentor.value.id
    && existingDraft.consultationType === mode.value
    && ['draft', 'pending_payment'].includes(existingDraft.orderStatus)

  if (matchingDraft) {
    questionnaire.value = { ...createDefaultConsultationQuestionnaire(), ...existingDraft.questionnaire }
    bookingSlot.value = existingDraft.bookingSlot || null
  } else {
    const nextDraft = startConsultationDraft({ mentorId: mentor.value.id, consultationType: mode.value })
    questionnaire.value = { ...createDefaultConsultationQuestionnaire(), ...(nextDraft?.questionnaire || {}) }
    bookingSlot.value = nextDraft?.bookingSlot || null
  }
})

function selectGrade(event) {
  questionnaire.value.grade = gradeOptions[Number(event?.detail?.value)] || gradeOptions[0]
}

function selectGraduationYear(event) {
  questionnaire.value.graduationYear = yearOptions[Number(event?.detail?.value)] || yearOptions[0]
}

async function submitOrder() {
  if (!mentor.value || isPaying.value) return
  if (!isLoggedIn()) {
    uni.showToast({ title: '请先登录后再发起咨询', icon: 'none' })
    return
  }
  if (!questionnaire.value.name.trim() || !questionnaire.value.school.trim() || !questionnaire.value.major.trim()) {
    uni.showToast({ title: '请先填写姓名、当前学校和当前专业', icon: 'none' })
    return
  }
  if (isBooking.value && !bookingSlot.value) {
    uni.showToast({ title: '请先选择预约时间', icon: 'none' })
    return
  }

  isPaying.value = true
  try {
    saveConsultationQuestionnaire(questionnaire.value)
    const createdOrder = await createMentorConsultationOrder({
      mentor_id: mentor.value.id,
      consultation_type: mode.value,
      ...(isBooking.value ? { slot_id: bookingSlot.value.id } : {}),
      questionnaire: {
        name: questionnaire.value.name.trim(),
        school: questionnaire.value.school.trim(),
        major: questionnaire.value.major.trim(),
        grade: questionnaire.value.grade,
        graduation_year: Number(questionnaire.value.graduationYear) || undefined,
        question: questionnaire.value.question.trim()
      }
    })
    saveConsultationOrder(createdOrder)
    const paidOrder = await mockPayMentorConsultationOrder(createdOrder.id)
    const draft = saveConsultationOrder(paidOrder)
    uni.navigateTo({
      url: `/pages/circle/mentor-waiting?mentorId=${encodeURIComponent(mentor.value.id)}&mode=${mode.value}&orderId=${encodeURIComponent(draft.orderId)}`
    })
  } catch (error) {
    uni.showToast({ title: error?.detail || '创建咨询订单失败，请稍后重试', icon: 'none' })
  } finally {
    isPaying.value = false
  }
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
.mentor-form-page { height: 100vh; height: 100dvh; overflow: hidden; background: #f4f8ff; display: flex; flex-direction: column; }
.mentor-form-scroll { min-height: 0; flex: 1; }
.mentor-form-content { padding: 24rpx 24rpx 0; }
.mentor-form-intro { padding: 20rpx 22rpx; border: 2rpx solid #d6e6ff; border-radius: 20rpx; background: #edf4ff; color: #5c7398; font-size: 21rpx; line-height: 1.6; font-weight: 650; }
.mentor-form-card { margin-top: 18rpx; padding: 28rpx; border: 2rpx solid #d9e7fc; border-radius: 28rpx; background: rgba(255,255,255,.93); box-shadow: 0 14rpx 34rpx rgba(52,120,246,.06); }
.mentor-form-section-title { color: #273953; font-size: 28rpx; line-height: 1.25; font-weight: 900; }
.mentor-form-field { margin-top: 24rpx; }
.mentor-form-label { display: flex; align-items: center; justify-content: space-between; gap: 14rpx; margin-bottom: 12rpx; color: #40546e; font-size: 23rpx; line-height: 1.25; font-weight: 850; }
.mentor-form-label strong { color: #9aabc1; font-size: 18rpx; font-weight: 700; }
.mentor-form-field input, .mentor-form-picker { box-sizing: border-box; width: 100%; height: 72rpx; padding: 0 18rpx; border: 2rpx solid #e0eafa; border-radius: 18rpx; background: #fbfdff; color: #2d405d; font-size: 23rpx; line-height: 68rpx; font-weight: 650; }
.mentor-form-placeholder { color: #a7b3c4; font-weight: 500; }
.mentor-form-half-row { display: grid; grid-template-columns: repeat(2,minmax(0,1fr)); gap: 16rpx; }
.mentor-form-half-row > view { min-width: 0; }
.mentor-form-picker { overflow: hidden; display: flex; align-items: center; justify-content: space-between; line-height: 1.2; }
.mentor-form-picker text { color: #8192aa; font-size: 24rpx; }
.mentor-question-card { padding-bottom: 20rpx; }
.mentor-question-label { margin-bottom: 14rpx; }
.mentor-question-card textarea { box-sizing: border-box; width: 100%; min-height: 220rpx; padding: 18rpx; border: 2rpx solid #e0eafa; border-radius: 18rpx; background: #fbfdff; color: #2d405d; font-size: 23rpx; line-height: 1.55; font-weight: 600; }
.mentor-question-count { margin-top: 10rpx; color: #9aa9bb; text-align: right; font-size: 19rpx; font-weight: 650; }
.mentor-order-mentor { display: flex; align-items: center; gap: 14rpx; margin-top: 22rpx; padding-bottom: 20rpx; border-bottom: 2rpx solid #edf1f8; }
.mentor-order-avatar { width: 62rpx; height: 62rpx; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 24rpx; font-weight: 900; flex-shrink: 0; }
.mentor-order-avatar.tone-blue { background:#e6efff; color:#3478f6; }.mentor-order-avatar.tone-mint{background:#e2f4ef;color:#198777}.mentor-order-avatar.tone-violet{background:#eeeafe;color:#7162bd}.mentor-order-avatar.tone-warm{background:#f9eee1;color:#b66c32}
.mentor-order-mentor strong, .mentor-order-mentor text { display: block; }
.mentor-order-mentor strong { color: #2b3b55; font-size: 24rpx; line-height: 1.2; font-weight: 900; }
.mentor-order-mentor text { margin-top: 6rpx; color: #8291a7; font-size: 20rpx; line-height: 1.2; font-weight: 650; }
.mentor-order-lines { margin-top: 12rpx; }
.mentor-order-lines > view { display: flex; align-items: center; justify-content: space-between; gap: 20rpx; padding-top: 15rpx; color: #8391a5; font-size: 21rpx; line-height: 1.3; font-weight: 650; }
.mentor-order-lines strong { color: #41556f; text-align: right; font-weight: 800; }
.mentor-order-lines .mentor-order-price strong { color: #1f2e44; font-size: 28rpx; font-weight: 900; }
.mentor-form-bottom-space { height: calc(154rpx + env(safe-area-inset-bottom)); }
.mentor-form-missing { padding: 150rpx 40rpx; color: #75869d; text-align: center; font-size: 25rpx; font-weight: 700; }
.mentor-form-footer { padding: 16rpx 24rpx calc(24rpx + env(safe-area-inset-bottom)); border-top: 2rpx solid #dbe7f8; background: rgba(255,255,255,.97); display: flex; align-items: center; gap: 18rpx; }
.mentor-form-footer > view { min-width: 0; flex: 1; }
.mentor-form-footer text, .mentor-form-footer strong { display: block; }
.mentor-form-footer text { color: #8290a5; font-size: 19rpx; font-weight: 650; }
.mentor-form-footer strong { margin-top: 4rpx; color: #203048; font-size: 28rpx; line-height: 1.2; font-weight: 900; }
.mentor-form-footer button { box-sizing: border-box; min-width: 250rpx; height: 74rpx; min-height: 74rpx; margin: 0; border: 0; border-radius: 20rpx; background: #3478f6; color: #fff; display: flex; align-items: center; justify-content: center; padding: 0 16rpx; text-align: center; font-size: 23rpx; line-height: 1; font-weight: 900; white-space: nowrap; box-shadow: 0 10rpx 22rpx rgba(52,120,246,.2); }
.mentor-form-footer button::after { border: 0; }
@media (max-width:350px){.mentor-form-footer{gap:12rpx;padding-right:18rpx;padding-left:18rpx}.mentor-form-footer button{min-width:220rpx;font-size:21rpx}.mentor-form-card{padding:24rpx}}
</style>
