<template>
  <view class="mentor-form-page" :style="themeInlineStyle">
    <MentorPageHeader title="填写咨询信息" @back="goBack" />

    <scroll-view scroll-y class="mentor-form-scroll">
      <view v-if="accessChecking" class="mentor-form-missing">正在验证登录状态…</view>
      <view v-else-if="mentor" class="mentor-form-content">
        <view class="mentor-form-intro">
          为了让前辈提前了解你的情况，请先填写以下信息。确认咨询后，这些信息会发送给前辈。
        </view>
        <view
          class="mentor-local-rehearsal-note"
          :class="{ disabled: !paymentCapability.order_creation_enabled }"
        >
          {{ paymentCapability.message }}
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
            <view><text>咨询方式</text><strong>站内文字咨询</strong></view>
            <view><text>服务形式</text><strong>{{ isBooking ? '预约咨询' : '单次即时咨询' }}</strong></view>
            <view><text>咨询窗口</text><strong>{{ mentor.consultationWindowMinutes || 60 }}分钟</strong></view>
            <view class="mentor-order-price"><text>价格</text><strong>¥{{ orderPrice }}</strong></view>
          </view>
        </view>

        <view class="mentor-form-card mentor-rules-card">
          <view class="mentor-form-section-title">咨询服务与争议处理</view>
          <view class="mentor-rules-copy">请全程使用站内沟通；平台会保留订单、消息、双方凭证及处理记录。遇到履约、隐私或评价争议，可提交平台介入并申请复核。</view>
          <view class="mentor-rules-link" @tap="showServiceRules">查看完整规则 ›</view>
          <view class="mentor-rules-agreement" :class="{ accepted: serviceRulesAccepted }" @tap="serviceRulesAccepted = !serviceRulesAccepted">
            <text>{{ serviceRulesAccepted ? '✓' : '' }}</text>
            <view>我已阅读并同意《咨询服务与纠纷处理规则》</view>
          </view>
        </view>
      </view>
      <view v-else class="mentor-form-missing">
        <view>{{ mentorLoadError || '前辈信息已失效，请返回重新选择。' }}</view>
        <button v-if="mentorId" @tap="loadMentorForForm">重新加载</button>
      </view>
      <view class="mentor-form-bottom-space"></view>
    </scroll-view>

    <view v-if="mentor && !accessChecking" class="mentor-form-footer">
      <view><text>{{ isBooking ? '确认预约' : '即时咨询' }}</text><strong>¥{{ orderPrice }}</strong></view>
      <button :loading="isPaying" :disabled="!canSubmitOrder || isPaying" @tap="submitOrder">{{ submitButtonText }}</button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import {
  createMentorConsultationOrder,
  createMentorConsultationPaymentIntent,
  fetchMentorConsultationPaymentCapability,
  fetchMentorProfile
} from '../../api/mentorConsultation'
import {
  MENTOR_GRADE_OPTIONS,
  cacheMentors,
  createDefaultConsultationQuestionnaire,
  getConsultationDraft,
  getMentorById,
  normalizeMentorDetailResponse,
  saveConsultationOrder,
  saveConsultationQuestionnaire,
  startConsultationDraft
} from '../../data/mentorConsultation'
import { isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const mentor = ref(null)
const mentorId = ref('')
const mentorLoadError = ref('')
const mode = ref('instant')
const questionnaire = ref(createDefaultConsultationQuestionnaire())
const bookingSlot = ref(null)
const isPaying = ref(false)
const accessChecking = ref(true)
const serviceRulesAccepted = ref(false)
const paymentCapability = ref({
  order_creation_enabled: false,
  payment_mode: 'disabled',
  message: '正在检查咨询支付开放状态…'
})
const gradeOptions = MENTOR_GRADE_OPTIONS
const yearOptions = ['2031', '2030', '2029', '2028', '2027', '2026', '2025', '2024']
const themeKey = ref(getStoredThemeKey())

const isBooking = computed(() => mode.value === 'booking')
const gradeIndex = computed(() => Math.max(0, gradeOptions.indexOf(questionnaire.value.grade)))
const yearIndex = computed(() => Math.max(0, yearOptions.indexOf(String(questionnaire.value.graduationYear))))
const orderPrice = computed(() => bookingSlot.value?.price ?? mentor.value?.price ?? 0)
const bookingSlotLabel = computed(() => bookingSlot.value ? `${bookingSlot.value.date} ${bookingSlot.value.time}` : '待选择')
const themeInlineStyle = computed(() => buildThemeStyle(themeKey.value))
const submitButtonText = computed(() => {
  if (isPaying.value) return paymentCapability.value.payment_mode === 'demo' ? '提交咨询请求中' : '创建订单中'
  if (!paymentCapability.value.order_creation_enabled) return '支付资质审核中'
  return paymentCapability.value.payment_mode === 'demo'
    ? '确认并提交咨询请求'
    : `确认并创建支付订单 ¥${orderPrice.value}`
})
const canSubmitOrder = computed(() => Boolean(
  mentor.value
  && questionnaire.value.name.trim()
  && questionnaire.value.school.trim()
  && questionnaire.value.major.trim()
  && (!isBooking.value || bookingSlot.value)
  && serviceRulesAccepted.value
  && paymentCapability.value.order_creation_enabled
))

onLoad((options) => {
  mode.value = options?.mode === 'booking' ? 'booking' : 'instant'
  mentorId.value = String(options?.mentorId || '').trim()
  if (!isLoggedIn()) {
    goLogin(mentorId.value)
    return
  }
  void loadMentorForForm()
  void loadPaymentCapability()
})

async function loadPaymentCapability() {
  try {
    paymentCapability.value = await fetchMentorConsultationPaymentCapability()
  } catch (error) {
    paymentCapability.value = {
      order_creation_enabled: false,
      payment_mode: 'disabled',
      message: error?.detail || '支付开放状态暂时不可用，请稍后重试。'
    }
  }
}

async function loadMentorForForm() {
  const id = mentorId.value
  accessChecking.value = true
  mentorLoadError.value = ''
  mentor.value = getMentorById(id)
  if (!id) {
    mentorLoadError.value = '未找到前辈信息，请返回重新选择。'
    accessChecking.value = false
    return
  }

  try {
    const profile = normalizeMentorDetailResponse(await fetchMentorProfile(id))
    if (!profile) throw new Error('前辈详情数据不完整')
    mentor.value = profile
    cacheMentors([profile])
  } catch (error) {
    if (Number(error?.statusCode) === 404) {
      mentor.value = null
      mentorLoadError.value = '该前辈已下架或暂不可咨询，请返回重新选择。'
    } else if (!mentor.value) {
      mentorLoadError.value = error?.detail || '前辈资料暂时不可用，请检查网络后重试。'
    }
  }

  if (!mentor.value) {
    accessChecking.value = false
    return
  }

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
  accessChecking.value = false
}

onShow(() => {
  themeKey.value = getStoredThemeKey()
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
  if (!serviceRulesAccepted.value) {
    uni.showToast({ title: '请先阅读并同意咨询服务与纠纷处理规则', icon: 'none' })
    return
  }
  if (!paymentCapability.value.order_creation_enabled) {
    uni.showToast({ title: paymentCapability.value.message || '收费咨询暂未开放', icon: 'none' })
    return
  }

  isPaying.value = true
  try {
    const orderDraft = saveConsultationQuestionnaire(questionnaire.value)
    const createdOrder = await createMentorConsultationOrder({
      mentor_id: mentor.value.id,
      client_order_id: orderDraft?.clientOrderId,
      consultation_type: mode.value,
      ...(isBooking.value ? { slot_id: bookingSlot.value.id } : {}),
      service_rules_version: paymentCapability.value.service_rules_version || '2026-08-23',
      service_rules_accepted: true,
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
    let paymentInfo = null
    if (paymentCapability.value.payment_mode === 'real') {
      try {
        paymentInfo = await createMentorConsultationPaymentIntent(createdOrder.id)
      } catch (paymentIntentError) {
        paymentInfo = {
          message: paymentIntentError?.detail || '支付订单暂未生成完成。订单仍保持待支付，可在订单状态页取消或稍后重试。'
        }
      }
    }
    const draft = saveConsultationOrder({
      ...createdOrder,
      payment_reference: paymentInfo?.provider_order_id || createdOrder.payment_reference || '',
      payment_provider: paymentInfo?.provider || '',
      payment_checkout_url: paymentInfo?.checkout_url || '',
      payment_message: paymentInfo?.message || ''
    })
    uni.navigateTo({
      url: `/pages-sub-consultation/consultation/mentor-waiting?mentorId=${encodeURIComponent(mentor.value.id)}&mode=${mode.value}&orderId=${encodeURIComponent(draft.orderId)}`
    })
  } catch (error) {
    uni.showToast({
      title: error?.detail || '创建咨询订单失败，请稍后重试',
      icon: 'none'
    })
  } finally {
    isPaying.value = false
  }
}

function showServiceRules() {
  uni.showModal({
    title: '咨询服务与纠纷处理规则',
    content: '1. 订单和沟通应在站内完成；请勿私下交易或索取无关隐私。\n2. 前辈须按约定时段履约，用户须如实说明需求并文明沟通。\n3. 双方可提交说明和凭证；平台将结合订单、聊天记录与材料处理。\n4. 对处理结果有异议时，双方均可申请一次复核。\n5. 平台会持续展示相关处理状态。',
    showCancel: false,
    confirmText: '我知道了'
  })
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/home/index?tab=circle&section=community&communityTab=mentor' })
    }
  })
}

function goLogin(mentorId = '') {
  const target = `/pages-sub-consultation/consultation/mentor-consult-form?mentorId=${encodeURIComponent(mentorId)}&mode=${mode.value}`
  uni.redirectTo({
    url: `/pages/login/index?redirect=${encodeURIComponent(target)}`
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
.mentor-form-missing button { box-sizing: border-box; min-height: 60rpx; margin: 24rpx auto 0; padding: 0 24rpx; border: 0; border-radius: 18rpx; background: var(--gyt-primary-gradient, #3478f6); color: #fff; display: flex; align-items: center; justify-content: center; text-align: center; font-size: 21rpx; line-height: 1; font-weight: 850; }
.mentor-form-missing button::after { border: 0; }
.mentor-form-footer { padding: 16rpx 24rpx calc(24rpx + env(safe-area-inset-bottom)); border-top: 2rpx solid #dbe7f8; background: rgba(255,255,255,.97); display: flex; align-items: center; gap: 18rpx; }
.mentor-form-footer > view { min-width: 0; flex: 1; }
.mentor-form-footer text, .mentor-form-footer strong { display: block; }
.mentor-form-footer text { color: #8290a5; font-size: 19rpx; font-weight: 650; }
.mentor-form-footer strong { margin-top: 4rpx; color: #203048; font-size: 28rpx; line-height: 1.2; font-weight: 900; }
.mentor-form-footer button { position: relative; box-sizing: border-box; flex: 0 1 360rpx; min-width: 250rpx; height: 74rpx; min-height: 74rpx; margin: 0; border: 0; border-radius: 20rpx; background: #3478f6; color: #fff; display: flex; align-items: center; justify-content: center; padding: 0 16rpx; text-align: center; font-size: 23rpx; line-height: 1.2; font-weight: 900; white-space: normal; box-shadow: 0 10rpx 22rpx rgba(52,120,246,.2); }
.mentor-form-footer button::after { border: 0; }
.mentor-form-footer button[loading]::before { position: absolute; top: 0; bottom: 0; left: 14rpx; width: 24rpx; height: 24rpx; margin: auto 0; }
.mentor-local-rehearsal-note{margin-top:14rpx;padding:14rpx 16rpx;border-radius:16rpx;color:#2e806d;background:#edf9f5;font-size:19rpx;line-height:1.55;font-weight:750}
.mentor-local-rehearsal-note.disabled{color:#9a7445;background:#fff7e9}
.mentor-rules-card{padding-bottom:24rpx}.mentor-rules-copy{color:#70829a;font-size:20rpx;line-height:1.65}.mentor-rules-link{margin-top:14rpx;color:var(--gyt-primary,#3478f6);font-size:20rpx;font-weight:800}.mentor-rules-agreement{display:flex;align-items:center;gap:12rpx;margin-top:20rpx;color:#718299;font-size:20rpx;line-height:1.4}.mentor-rules-agreement>text{width:30rpx;height:30rpx;box-sizing:border-box;border:2rpx solid #a8b9cf;border-radius:8rpx;display:flex;align-items:center;justify-content:center;color:#fff;font-size:20rpx;font-weight:900}.mentor-rules-agreement.accepted{color:#326cae}.mentor-rules-agreement.accepted>text{border-color:var(--gyt-primary,#3478f6);background:var(--gyt-primary,#3478f6)}.mentor-form-footer button[disabled]{height:74rpx;min-height:74rpx;padding-top:0;padding-bottom:0;opacity:.46;box-shadow:none}
@media (max-width:350px){.mentor-form-footer{gap:12rpx;padding-right:18rpx;padding-left:18rpx}.mentor-form-footer button{flex-basis:310rpx;min-width:220rpx;font-size:21rpx}.mentor-form-card{padding:24rpx}}

/* Keep this payment form in step with the global appearance themes. */
.mentor-form-page { background: var(--gyt-page-bg); }
.mentor-form-intro { border-color: var(--gyt-primary-border, #d6e6ff); background: var(--gyt-primary-soft, #edf4ff); }
.mentor-form-card { border-color: var(--gyt-primary-border, #d9e7fc); background: var(--gyt-panel-bg, #ffffff); box-shadow: 0 14rpx 34rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.06)); }
.mentor-form-field input,.mentor-form-picker,.mentor-question-card textarea { border-color: var(--gyt-primary-border, #e0eafa); background: var(--gyt-primary-tint, #fbfdff); }
.mentor-order-avatar.tone-blue { background: var(--gyt-primary-soft, #e6efff); color: var(--gyt-primary, #3478f6); }
.mentor-order-mentor { border-color: var(--gyt-primary-border, #edf1f8); }
.mentor-form-footer { border-color: var(--gyt-primary-border, #dbe7f8); background: var(--gyt-primary-tint, #ffffff); }
.mentor-form-footer button { background: var(--gyt-primary-gradient, #3478f6); box-shadow: 0 10rpx 22rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.2)); }
</style>
