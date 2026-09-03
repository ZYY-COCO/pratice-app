<template>
  <view class="mentor-info-page" :style="themeInlineStyle">
    <MentorPageHeader title="我的信息" @back="goBack" />

    <scroll-view scroll-y class="mentor-info-scroll">
      <view v-if="mentor" class="mentor-info-content">
        <view class="mentor-info-hero">
          <view class="mentor-info-person-row">
            <view class="mentor-info-avatar" :class="`tone-${mentor.avatarTone || 'blue'}`">
              <image v-if="mentorAvatarUrl" :src="mentorAvatarUrl" mode="aspectFill" />
              <text v-else>{{ mentor.avatar || '前' }}</text>
            </view>
            <view class="mentor-info-person-copy">
              <view class="mentor-info-name-row">
                <text>{{ mentor.maskedName }}</text>
                <text v-if="mentor.verified" class="mentor-info-verified">✓ 平台认证</text>
              </view>
              <view class="mentor-info-school">{{ mentor.school || '未填写院校' }}</view>
              <view class="mentor-info-major">{{ mentor.major || '未填写专业' }}<text v-if="mentor.admissionYear"> · {{ mentor.admissionYear }}级</text></view>
            </view>
          </view>
          <view class="mentor-info-status" :class="{ online: mentor.onlineStatus === 'online' }">
            <view></view>
            <text>{{ mentor.onlineStatus === 'online' ? '在线接单中' : '暂不接即时咨询' }}</text>
          </view>
        </view>

        <view v-if="isProfileEditing" class="mentor-info-edit-mode-notice">
          <view>
            <strong>资料修改模式</strong>
            <text>浅红边框内的信息可修改，提交后会重新进入审核。</text>
          </view>
          <button @tap="cancelProfileEdit">退出</button>
        </view>
        <view v-else-if="profileEditPending" class="mentor-info-edit-pending">
          <view>
            <strong>资料修改审核中</strong>
            <text>审核完成前，仍会按照当前已认证资料继续接单。</text>
          </view>
        </view>

        <view class="mentor-info-section" :class="{ 'is-editing': isProfileEditing }">
          <view class="mentor-info-section-heading">
            <view>
              <strong>我的资料</strong>
              <text>{{ isProfileEditing ? '浅红边框内的信息支持修改并重新提交审核' : '已通过平台认证的信息' }}</text>
            </view>
          </view>
          <view class="mentor-info-facts">
            <view :class="{ 'is-editable': isProfileEditing }">
              <text>考试类型</text>
              <picker v-if="isProfileEditing" mode="selector" :range="profileEditExamLabels" :value="profileEditExamIndex" @change="selectProfileEditExamType">
                <view class="mentor-info-edit-picker">{{ profileEditExamLabel }}<text>⌄</text></view>
              </picker>
              <strong v-else>{{ examTypeLabel }}</strong>
            </view>
            <view :class="{ 'is-editable': isProfileEditing }">
              <text>初试成绩</text>
              <strong v-if="isProfileEditing && isProfileEditApplication">无需填写</strong>
              <input v-else-if="isProfileEditing" v-model="profileEditDraft.score" class="mentor-info-edit-input" type="number" maxlength="3" @input="handleProfileEditScore" />
              <strong v-else>{{ scoreLabel }}</strong>
            </view>
            <view :class="{ 'is-editable': isProfileEditing }">
              <text>录取院校</text>
              <input v-if="isProfileEditing" v-model="profileEditDraft.school" class="mentor-info-edit-input" maxlength="120" placeholder="请输入录取院校" placeholder-class="mentor-info-edit-placeholder" />
              <strong v-else>{{ mentor.school || '未填写' }}</strong>
            </view>
            <view :class="{ 'is-editable': isProfileEditing }">
              <text>录取专业</text>
              <input v-if="isProfileEditing" v-model="profileEditDraft.major" class="mentor-info-edit-input" maxlength="120" placeholder="请输入录取专业" placeholder-class="mentor-info-edit-placeholder" />
              <strong v-else>{{ mentor.major || '未填写' }}</strong>
            </view>
          </view>
        </view>

        <view v-if="isProfileEditing || mentor.skills?.length || mentor.bio" class="mentor-info-section" :class="{ 'is-editing': isProfileEditing }">
          <view v-if="isProfileEditing || mentor.skills?.length" class="mentor-info-detail-block" :class="{ 'is-editable': isProfileEditing }">
            <view class="mentor-info-detail-title">擅长咨询</view>
            <view v-if="isProfileEditing" class="mentor-info-skill-options">
              <button v-for="skill in profileEditSkillOptions" :key="skill" :class="{ active: profileEditDraft.skills.includes(skill) }" @tap="toggleProfileEditSkill(skill)">{{ formatSkillLabel(skill) }}</button>
            </view>
            <view v-else class="mentor-info-skills">
              <text v-for="skill in mentor.skills" :key="skill">{{ formatSkillLabel(skill) }}</text>
            </view>
          </view>
          <view v-if="isProfileEditing || mentor.bio" class="mentor-info-detail-block" :class="{ 'has-divider': !isProfileEditing && mentor.skills?.length, 'is-editable': isProfileEditing }">
            <view class="mentor-info-detail-title">个人简介<text v-if="isProfileEditing">{{ profileEditDraft.bio.length }} / 500</text></view>
            <view v-if="isProfileEditing" class="mentor-info-bio-editor">
              <textarea v-model="profileEditDraft.bio" maxlength="500" placeholder="介绍你的上岸经历、可提供的帮助和擅长方向。" placeholder-class="mentor-info-edit-placeholder" />
            </view>
            <view v-else class="mentor-info-bio">{{ mentor.bio }}</view>
          </view>
        </view>

        <view class="mentor-info-section mentor-info-stats-section">
          <view class="mentor-info-section-heading">
            <view>
              <strong>咨询数据</strong>
              <text>实时同步你的咨询情况</text>
            </view>
          </view>
          <view class="mentor-info-stats-grid">
            <view :class="{ 'is-editable': isProfileEditing }">
              <text>咨询价格</text>
              <view v-if="isProfileEditing" class="mentor-info-price-editor"><text>¥</text><input v-model="profileEditDraft.price" type="number" maxlength="5" @input="handleProfileEditPrice" /><text>/ 次</text></view>
              <strong v-else>{{ mentor.priceLabel }} / 次</strong>
            </view>
            <view><text>待处理请求</text><strong>{{ pendingOrderCount }} 单</strong></view>
            <view><text>进行中咨询</text><strong>{{ activeOrderCount }} 单</strong></view>
            <view><text>已完成咨询</text><strong>{{ mentor.consultCount || 0 }} 单</strong></view>
          </view>
          <view class="mentor-info-profile-edit-action" :class="{ 'is-editing': isProfileEditing }">
            <button v-if="isProfileEditing" class="mentor-info-profile-edit-button submit" :loading="profileEditSubmitting" @tap="submitProfileEdit">提交修改并重新审核</button>
            <button v-else class="mentor-info-profile-edit-button" @tap="openProfileEditNotice">{{ profileEditPending ? '资料审核中' : '修改个人信息' }}</button>
          </view>
        </view>

        <view class="mentor-info-bottom-space"></view>
      </view>

      <AppPageLoadingState v-else-if="infoLoading" message="正在整理我的信息..." />
      <view v-else class="mentor-info-state mentor-info-state-empty">
        <view>前辈资料暂时不可用</view>
        <button @tap="goBack">返回咨询主页</button>
      </view>
    </scroll-view>

    <transition name="mentor-info-modal">
      <view v-if="showProfileEditNotice" class="mentor-info-modal-mask" @tap="closeProfileEditNotice">
        <view class="mentor-info-modal-card" @tap.stop>
          <view class="mentor-info-modal-title">修改个人信息提醒</view>
          <view class="mentor-info-modal-copy">
            <text>提交修改后，个人资料需要重新经过平台审核，预计 1–3 个工作日完成。</text>
            <text>审核期间，你仍可按照当前已认证的旧信息继续接单，不影响已有咨询和预约。</text>
          </view>
          <view class="mentor-info-modal-actions">
            <button class="mentor-info-modal-button secondary" @tap="dismissProfileEditNoticeForever">不再提示</button>
            <button class="mentor-info-modal-button primary" @tap="acknowledgeProfileEditNotice">知道了</button>
          </view>
        </view>
      </view>
    </transition>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from 'vue'
import { onHide, onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import {
  createMyMentorProfileChangeRequest,
  fetchMyMentorProfile,
  fetchMyMentorProfileChangeRequest,
  fetchMyReceivedMentorOrders
} from '../../api/mentorConsultation'
import { MENTOR_SKILL_OPTIONS, normalizeMentorConsultationOrder, normalizeMentorDetailResponse } from '../../data/mentorConsultation'
import { getAuthUser } from '../../utils/auth'
import {
  getMentorConsultationOrderUiState,
  mergeMentorConsultationStopState
} from '../../utils/mentorConsultationState.mjs'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const mentor = ref(null)
const mentorOrders = ref([])
const infoLoading = ref(false)
const ownerUser = ref(getAuthUser() || {})
const themeKey = ref(getStoredThemeKey())
const showProfileEditNotice = ref(false)
const isProfileEditing = ref(false)
const profileEditPending = ref(false)
const profileEditSubmitting = ref(false)
const profileEditDraft = ref(createProfileEditDraft())
const PROFILE_EDIT_NOTICE_STORAGE_KEY = 'mentor_profile_edit_notice_dismissed'
const profileEditExamOptions = [
  { value: 'Z001', label: 'Z001' },
  { value: 'Z002', label: 'Z002' },
  { value: 'application', label: '申请制' }
]
const profileEditExamLabels = profileEditExamOptions.map((item) => item.label)
const profileEditSkillOptions = MENTOR_SKILL_OPTIONS
const MENTOR_ORDER_COUNT_SYNC_INTERVAL_MS = 15000
const MENTOR_ORDER_COUNT_SYNC_STATUSES = new Set(['pending_accept', 'accepted', 'booked', 'in_progress'])
const mentorOrderClock = ref(Date.now())
let mentorOrderCountSyncTimer = null
let mentorOrderCountSyncing = false
let mentorInfoPageActive = false
let mentorInfoPageDestroyed = false
let mentorInfoVisibilityRevision = 0
let mentorInfoRefreshQueued = false
let mentorInfoLoadVisibilityRevision = -1

const mentorAvatarUrl = computed(() => getUserAvatarUrl(ownerUser.value) || mentor.value?.avatarUrl || '')
const themeInlineStyle = computed(() => buildThemeStyle(themeKey.value))
const pendingOrderCount = computed(() => mentorOrders.value.filter((order) => order.orderStatus === 'pending_accept').length)
const activeOrderCount = computed(() => mentorOrders.value.filter((order) => (
  order.orderStatus === 'accepted'
  || getMentorConsultationOrderUiState(order, {
    viewerRole: 'mentor',
    now: mentorOrderClock.value
  }).isLiveChat
)).length)
const examTypeLabel = computed(() => mentor.value?.examType === 'application' ? '申请制' : (mentor.value?.examType || '未填写'))
const scoreLabel = computed(() => {
  if (mentor.value?.examType === 'application') return '无需填写'
  const score = mentor.value?.score
  return score !== null && score !== undefined && score !== '' && Number.isFinite(Number(score))
    ? `${score} 分`
    : '未填写'
})
const profileEditExamIndex = computed(() => Math.max(0, profileEditExamOptions.findIndex((item) => item.value === profileEditDraft.value.examType)))
const profileEditExamLabel = computed(() => profileEditExamOptions[profileEditExamIndex.value]?.label || 'Z001')
const isProfileEditApplication = computed(() => profileEditDraft.value.examType === 'application')

onLoad(() => {
  void loadMentorInfo()
})

onShow(() => {
  mentorInfoPageActive = true
  mentorOrderClock.value = Date.now()
  themeKey.value = getStoredThemeKey()
  ownerUser.value = getAuthUser() || {}
  void loadMentorInfo({ silent: true })
})

onHide(() => {
  mentorInfoVisibilityRevision += 1
  mentorInfoPageActive = false
  mentorInfoRefreshQueued = false
  stopMentorOrderCountSync()
})

onBeforeUnmount(() => {
  mentorInfoVisibilityRevision += 1
  mentorInfoPageDestroyed = true
  mentorInfoPageActive = false
  mentorInfoRefreshQueued = false
  stopMentorOrderCountSync()
})

async function loadMentorInfo({ silent = false } = {}) {
  if (infoLoading.value) {
    if (
      mentorInfoPageActive
      && mentorInfoLoadVisibilityRevision !== mentorInfoVisibilityRevision
    ) mentorInfoRefreshQueued = true
    return
  }
  const requestVisibilityRevision = mentorInfoVisibilityRevision
  mentorInfoLoadVisibilityRevision = requestVisibilityRevision
  infoLoading.value = true

  try {
    const [profileResult, ordersResult, profileChangeRequestResult] = await Promise.allSettled([
      fetchMyMentorProfile(),
      fetchMyReceivedMentorOrders({ limit: 50 }),
      fetchMyMentorProfileChangeRequest()
    ])
    if (!isCurrentMentorInfoRead(requestVisibilityRevision)) return

    if (profileResult.status === 'fulfilled') {
      const profile = normalizeMentorDetailResponse(profileResult.value)
      if (profile) {
        mentor.value = profile
        if (!isProfileEditing.value && !profileEditPending.value) profileEditDraft.value = createProfileEditDraft(profile)
      }
    } else if (!mentor.value && !silent) {
      uni.showToast({ title: profileResult.reason?.detail || '我的信息加载失败', icon: 'none' })
    }

    if (ordersResult.status === 'fulfilled') {
      const existingById = new Map(mentorOrders.value.map((order) => [order.id, order]))
      mentorOrders.value = (Array.isArray(ordersResult.value?.items) ? ordersResult.value.items : [])
        .map((order) => normalizeMentorConsultationOrder(order))
        .map((order) => mergeMentorConsultationStopState(order, existingById.get(order.id)))
    } else if (!silent && mentor.value) {
      uni.showToast({ title: ordersResult.reason?.detail || '咨询数据加载失败', icon: 'none' })
    }

    if (profileChangeRequestResult.status === 'fulfilled') {
      const request = profileChangeRequestResult.value?.request || null
      profileEditPending.value = request?.request_status === 'pending'
      if (request?.request_status === 'pending' && !isProfileEditing.value) {
        profileEditDraft.value = normalizeProfileEditDraft({
          ...request,
          price: request.price
        })
      } else if (!isProfileEditing.value && mentor.value) {
        profileEditDraft.value = createProfileEditDraft(mentor.value)
      }
    } else if (!silent && mentor.value) {
      uni.showToast({ title: profileChangeRequestResult.reason?.detail || '资料修改审核状态加载失败', icon: 'none' })
    }

    mentorOrderClock.value = Date.now()
  } finally {
    infoLoading.value = false
    mentorInfoLoadVisibilityRevision = -1
    if (mentorInfoRefreshQueued && mentorInfoPageActive && !mentorInfoPageDestroyed) {
      mentorInfoRefreshQueued = false
      void loadMentorInfo({ silent: true })
    } else {
      if (!mentorInfoPageActive) mentorInfoRefreshQueued = false
      scheduleMentorOrderCountSync()
    }
  }
}

function isCurrentMentorInfoRead(visibilityRevision) {
  return (
    !mentorInfoPageDestroyed
    && mentorInfoPageActive
    && visibilityRevision === mentorInfoVisibilityRevision
  )
}

function hasMentorOrdersNeedingCountSync() {
  return mentorOrders.value.some((order) => (
    order?.id && MENTOR_ORDER_COUNT_SYNC_STATUSES.has(String(order.orderStatus || ''))
  ))
}

async function syncMentorOrderCounts() {
  if (
    mentorInfoPageDestroyed
    || !mentorInfoPageActive
    || infoLoading.value
    || mentorOrderCountSyncing
  ) {
    scheduleMentorOrderCountSync()
    return
  }
  const requestVisibilityRevision = mentorInfoVisibilityRevision
  mentorOrderCountSyncing = true
  try {
    const payload = await fetchMyReceivedMentorOrders({ limit: 50 })
    if (isCurrentMentorInfoRead(requestVisibilityRevision)) {
      const existingById = new Map(mentorOrders.value.map((order) => [order.id, order]))
      mentorOrders.value = (Array.isArray(payload?.items) ? payload.items : [])
        .map((order) => normalizeMentorConsultationOrder(order))
        .map((order) => mergeMentorConsultationStopState(order, existingById.get(order.id)))
      mentorOrderClock.value = Date.now()
    }
  } catch (error) {
    // 计数后台同步失败时保留上次成功数据，下一轮继续重试。
  } finally {
    mentorOrderCountSyncing = false
    mentorOrderClock.value = Date.now()
    scheduleMentorOrderCountSync()
  }
}

function scheduleMentorOrderCountSync() {
  stopMentorOrderCountSync()
  if (
    mentorInfoPageDestroyed
    || !mentorInfoPageActive
    || infoLoading.value
    || mentorOrderCountSyncing
    || !hasMentorOrdersNeedingCountSync()
  ) return
  mentorOrderCountSyncTimer = setTimeout(() => {
    mentorOrderCountSyncTimer = null
    void syncMentorOrderCounts()
  }, MENTOR_ORDER_COUNT_SYNC_INTERVAL_MS)
}

function stopMentorOrderCountSync() {
  if (mentorOrderCountSyncTimer) clearTimeout(mentorOrderCountSyncTimer)
  mentorOrderCountSyncTimer = null
}

function formatSkillLabel(skill) {
  return skill === '初试备考' ? '初试规划' : skill
}

function getUserAvatarUrl(user = {}) {
  const value = String(user?.avatar_url || user?.avatarUrl || '').trim()
  return /^(https?:\/\/|data:image\/)/i.test(value) ? value : ''
}

function normalizeProfileEditExamType(value) {
  return value === 'application' || value === '申请制' ? 'application' : value === 'Z002' ? 'Z002' : 'Z001'
}

function createProfileEditDraft(profile = {}) {
  const examType = normalizeProfileEditExamType(profile.examType)
  const score = profile.score
  return {
    examType,
    score: examType === 'application' || score === null || score === undefined || score === ''
      ? ''
      : (Number.isFinite(Number(score)) ? String(score) : ''),
    school: String(profile.school || ''),
    major: String(profile.major || ''),
    skills: Array.isArray(profile.skills) ? profile.skills.map(String).filter(Boolean).slice(0, 4) : [],
    bio: String(profile.bio || ''),
    price: Number.isFinite(Number(profile.price)) ? String(profile.price) : ''
  }
}

function normalizeProfileEditDraft(draft = {}, profile = mentor.value || {}) {
  const fallback = createProfileEditDraft(profile)
  const examType = normalizeProfileEditExamType(draft.examType || fallback.examType)
  return {
    ...fallback,
    examType,
    score: examType === 'application' ? '' : String(draft.score ?? fallback.score),
    school: String(draft.school ?? fallback.school),
    major: String(draft.major ?? fallback.major),
    skills: Array.isArray(draft.skills) ? draft.skills.map(String).filter(Boolean).slice(0, 4) : fallback.skills,
    bio: String(draft.bio ?? fallback.bio).slice(0, 500),
    price: String(draft.price ?? fallback.price)
  }
}

function enterProfileEditMode() {
  if (!mentor.value || profileEditPending.value) return
  profileEditDraft.value = createProfileEditDraft(mentor.value)
  isProfileEditing.value = true
}

function cancelProfileEdit() {
  isProfileEditing.value = false
  profileEditDraft.value = createProfileEditDraft(mentor.value)
}

function selectProfileEditExamType(event) {
  const index = Number(event?.detail?.value)
  profileEditDraft.value.examType = profileEditExamOptions[index]?.value || profileEditExamOptions[0].value
  if (profileEditDraft.value.examType === 'application') profileEditDraft.value.score = ''
}

function handleProfileEditScore(event) {
  const rawValue = String(event?.detail?.value ?? '')
  if (!rawValue) {
    profileEditDraft.value.score = ''
    return
  }
  const score = Number(rawValue)
  profileEditDraft.value.score = Number.isFinite(score) ? String(Math.min(150, Math.max(0, Math.trunc(score)))) : ''
}

function handleProfileEditPrice(event) {
  profileEditDraft.value.price = String(event?.detail?.value ?? '')
}

function toggleProfileEditSkill(skill) {
  if (profileEditDraft.value.skills.includes(skill)) {
    profileEditDraft.value.skills = profileEditDraft.value.skills.filter((item) => item !== skill)
    return
  }
  if (profileEditDraft.value.skills.length >= 4) {
    uni.showToast({ title: '最多选择 4 个擅长领域', icon: 'none' })
    return
  }
  profileEditDraft.value.skills = [...profileEditDraft.value.skills, skill]
}

async function submitProfileEdit() {
  if (profileEditSubmitting.value || !mentor.value) return
  const draft = normalizeProfileEditDraft(profileEditDraft.value)
  if (!draft.school.trim() || !draft.major.trim()) {
    uni.showToast({ title: '请补充录取院校和专业', icon: 'none' })
    return
  }
  const applicationExam = draft.examType === 'application'
  if (!applicationExam && !draft.score.trim()) {
    uni.showToast({ title: '请填写初试成绩', icon: 'none' })
    return
  }
  const score = applicationExam ? null : Number(draft.score)
  if (!applicationExam && (!Number.isInteger(score) || score < 0 || score > 150)) {
    uni.showToast({ title: '初试成绩请填写 0–150 分', icon: 'none' })
    return
  }
  const price = Number(draft.price)
  if (!Number.isFinite(price) || price < 0 || price > 1000) {
    uni.showToast({ title: '请输入正确的咨询价格', icon: 'none' })
    return
  }

  profileEditSubmitting.value = true
  try {
    profileEditDraft.value = { ...draft, score: applicationExam ? '' : String(score), price: String(price) }
    const request = await createMyMentorProfileChangeRequest({
      school: profileEditDraft.value.school.trim(),
      major: profileEditDraft.value.major.trim(),
      exam_type: profileEditDraft.value.examType,
      score,
      skills: [...profileEditDraft.value.skills],
      bio: profileEditDraft.value.bio.trim(),
      price_cents: Math.round(price * 100)
    })
    isProfileEditing.value = false
    profileEditPending.value = true
    uni.showToast({ title: '资料修改已提交，等待审核', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '资料修改申请提交失败，请稍后重试', icon: 'none' })
  } finally {
    profileEditSubmitting.value = false
  }
}

function openProfileEditNotice() {
  if (profileEditPending.value) {
    uni.showToast({ title: '资料修改正在审核中', icon: 'none' })
    return
  }
  try {
    if (uni.getStorageSync(PROFILE_EDIT_NOTICE_STORAGE_KEY) === '1') {
      enterProfileEditMode()
      return
    }
  } catch (error) {
    // Storage reads are best effort; the reminder can still be shown.
  }
  showProfileEditNotice.value = true
}

function closeProfileEditNotice() {
  showProfileEditNotice.value = false
}

function dismissProfileEditNoticeForever() {
  uni.setStorageSync(PROFILE_EDIT_NOTICE_STORAGE_KEY, '1')
  acknowledgeProfileEditNotice()
}

function acknowledgeProfileEditNotice() {
  closeProfileEditNotice()
  enterProfileEditMode()
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages-sub-consultation/consultation/mentor-apply' })
    }
  })
}
</script>

<style scoped>
.mentor-info-page{height:100vh;overflow:hidden;background:#f4f8ff;display:flex;flex-direction:column}.mentor-info-scroll{min-height:0;flex:1}.mentor-info-content{padding:24rpx 24rpx 0}.mentor-info-hero,.mentor-info-section{border:2rpx solid #d9e7fc;border-radius:30rpx;background:rgba(255,255,255,.94);box-shadow:0 14rpx 34rpx rgba(52,120,246,.06)}.mentor-info-hero{padding:30rpx}.mentor-info-person-row{display:flex;align-items:center;gap:18rpx}.mentor-info-avatar{width:94rpx;height:94rpx;overflow:hidden;border:3rpx solid #fff;border-radius:50%;background:#e6efff;color:#3478f6;display:flex;align-items:center;justify-content:center;font-size:34rpx;font-weight:900;flex-shrink:0}.mentor-info-avatar image{width:100%;height:100%}.mentor-info-avatar.tone-mint{background:#e2f4ef;color:#198777}.mentor-info-avatar.tone-violet{background:#eeeafe;color:#7162bd}.mentor-info-avatar.tone-warm{background:#f9eee1;color:#b66c32}.mentor-info-person-copy{min-width:0;flex:1}.mentor-info-name-row{display:flex;align-items:center;gap:10rpx;min-width:0}.mentor-info-name-row>text:first-child{min-width:0;overflow:hidden;color:#263a57;font-size:30rpx;line-height:1.2;font-weight:900;text-overflow:ellipsis;white-space:nowrap}.mentor-info-verified{padding:6rpx 10rpx;border-radius:999rpx;background:#edf4ff;color:#3478f6;font-size:18rpx;line-height:1.2;font-weight:800;white-space:nowrap}.mentor-info-school{margin-top:12rpx;color:#506580;font-size:23rpx;line-height:1.3;font-weight:800}.mentor-info-major{margin-top:7rpx;color:#8292a8;font-size:20rpx;line-height:1.35;font-weight:650}.mentor-info-major text{color:inherit;font:inherit}.mentor-info-status{display:inline-flex;align-items:center;gap:8rpx;margin-top:22rpx;padding:9rpx 13rpx;border-radius:999rpx;background:#eef3fb;color:#7f8ea2;font-size:19rpx;line-height:1.2;font-weight:800}.mentor-info-status>view{width:12rpx;height:12rpx;border-radius:50%;background:#aeb9c8}.mentor-info-status.online{background:#e7f7ed;color:#258656}.mentor-info-status.online>view{background:#25b970;box-shadow:0 0 0 5rpx rgba(37,185,112,.12)}.mentor-info-section{margin-top:18rpx;padding:26rpx}.mentor-info-section-heading strong,.mentor-info-section-heading text{display:block}.mentor-info-section-heading strong{color:#40546e;font-size:25rpx;line-height:1.25;font-weight:900}.mentor-info-section-heading text{margin-top:6rpx;color:#8796a9;font-size:19rpx;line-height:1.4;font-weight:650}.mentor-info-facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2rpx;margin:22rpx -26rpx -26rpx;overflow:hidden;border-top:2rpx solid #edf2f8}.mentor-info-facts>view{min-width:0;padding:22rpx 26rpx;border-top:1rpx solid #edf2f8}.mentor-info-facts>view:nth-child(-n+2){border-top:0}.mentor-info-facts>view:nth-child(odd){border-right:1rpx solid #edf2f8}.mentor-info-facts text,.mentor-info-facts strong{display:block}.mentor-info-facts text{color:#8a98ab;font-size:19rpx;font-weight:650}.mentor-info-facts strong{margin-top:9rpx;overflow:hidden;color:#41546e;font-size:22rpx;line-height:1.35;font-weight:900;text-overflow:ellipsis;white-space:nowrap}.mentor-info-detail-block+.mentor-info-detail-block{margin-top:22rpx}.mentor-info-detail-block.has-divider{padding-top:22rpx;border-top:2rpx solid #edf2f8}.mentor-info-detail-title{color:#40546e;font-size:23rpx;font-weight:900}.mentor-info-skills{display:flex;flex-wrap:wrap;gap:10rpx;margin-top:16rpx}.mentor-info-skills text{padding:9rpx 13rpx;border-radius:999rpx;background:#edf4ff;color:#4f76ad;font-size:19rpx;line-height:1.2;font-weight:750}.mentor-info-bio{margin-top:12rpx;color:#6d7f97;font-size:21rpx;line-height:1.65;font-weight:600}.mentor-info-stats-section{padding-bottom:0;overflow:hidden}.mentor-info-stats-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2rpx;margin:22rpx -26rpx 0;overflow:hidden;border-top:2rpx solid #edf2f8}.mentor-info-stats-grid>view{padding:26rpx;border-top:1rpx solid #edf2f8}.mentor-info-stats-grid>view:nth-child(-n+2){border-top:0}.mentor-info-stats-grid>view:nth-child(odd){border-right:1rpx solid #edf2f8}.mentor-info-stats-grid text,.mentor-info-stats-grid strong{display:block}.mentor-info-stats-grid text{color:#8a98ab;font-size:19rpx;font-weight:650}.mentor-info-stats-grid strong{margin-top:9rpx;color:#41546e;font-size:23rpx;line-height:1.35;font-weight:900}.mentor-info-bottom-space{height:calc(44rpx + env(safe-area-inset-bottom))}.mentor-info-state{padding:110rpx 38rpx;color:#7d8ea6;text-align:center;font-size:23rpx;font-weight:700}.mentor-info-state-empty button{box-sizing:border-box;height:60rpx;min-height:60rpx;margin:28rpx auto 0;padding:0 24rpx;border:0;border-radius:18rpx;background:#3478f6;color:#fff;display:flex;align-items:center;justify-content:center;text-align:center;font-size:21rpx;line-height:1;font-weight:850}.mentor-info-state-empty button::after{border:0}@media(max-width:350px){.mentor-info-content{padding-right:18rpx;padding-left:18rpx}.mentor-info-hero,.mentor-info-section{padding-right:22rpx;padding-left:22rpx}.mentor-info-facts,.mentor-info-stats-grid{margin-right:-22rpx;margin-left:-22rpx}.mentor-info-facts>view,.mentor-info-stats-grid>view{padding-right:22rpx;padding-left:22rpx}.mentor-info-name-row{gap:7rpx}.mentor-info-verified{padding-right:8rpx;padding-left:8rpx;font-size:17rpx}}

.mentor-info-profile-edit-action{padding:22rpx 26rpx 26rpx;border-top:2rpx solid #edf2f8}
.mentor-info-profile-edit-button{position:relative;display:flex;align-items:center;justify-content:center;width:100%;height:72rpx;min-height:72rpx;margin:0;padding:0 20rpx;border:2rpx solid #bcd4fb;border-radius:18rpx;background:#f7faff;color:#3977df;text-align:center;font-size:22rpx;line-height:1.25;font-weight:850;box-sizing:border-box}
.mentor-info-profile-edit-button::after,.mentor-info-modal-button::after{border:0}
.mentor-info-profile-edit-button[loading]::before{position:absolute;top:0;bottom:0;left:18rpx;width:24rpx;height:24rpx;margin:auto 0}
.mentor-info-profile-edit-button[disabled]{height:72rpx;min-height:72rpx;padding-top:0;padding-bottom:0}
.mentor-info-modal-mask{position:fixed;z-index:1000;top:0;right:0;bottom:0;left:0;display:flex;align-items:center;justify-content:center;padding:32rpx;background:rgba(37,58,91,.28);box-sizing:border-box}
.mentor-info-modal-card{width:100%;max-width:620rpx;padding:34rpx 30rpx 30rpx;border:2rpx solid #d9e7fc;border-radius:30rpx;background:#fff;box-shadow:0 22rpx 56rpx rgba(39,70,119,.18);box-sizing:border-box}
.mentor-info-modal-title{color:#344a68;font-size:28rpx;line-height:1.35;font-weight:900;text-align:center}
.mentor-info-modal-copy{margin-top:22rpx;padding:20rpx;border-radius:18rpx;background:#f5f9ff}
.mentor-info-modal-copy text{display:block;color:#667b98;font-size:21rpx;line-height:1.65;font-weight:650}
.mentor-info-modal-copy text+text{margin-top:12rpx}
.mentor-info-modal-actions{display:flex;gap:16rpx;margin-top:28rpx}
.mentor-info-modal-button{display:flex;flex:1;align-items:center;justify-content:center;min-height:72rpx;margin:0;padding:0;border:0;border-radius:18rpx;font-size:22rpx;line-height:1.25;font-weight:850;box-sizing:border-box}
.mentor-info-modal-button.secondary{background:#edf3fb;color:#6b7e97}
.mentor-info-modal-button.primary{background:#3478f6;color:#fff;box-shadow:0 10rpx 20rpx rgba(52,120,246,.18)}
.mentor-info-modal-enter-active,.mentor-info-modal-leave-active{transition:opacity .2s ease}
.mentor-info-modal-enter-active .mentor-info-modal-card,.mentor-info-modal-leave-active .mentor-info-modal-card{transition:transform .2s ease,opacity .2s ease}
.mentor-info-modal-enter-from,.mentor-info-modal-leave-to{opacity:0}
.mentor-info-modal-enter-from .mentor-info-modal-card,.mentor-info-modal-leave-to .mentor-info-modal-card{opacity:0;transform:translateY(20rpx) scale(.98)}
@media(max-width:350px){.mentor-info-profile-edit-action{padding-right:22rpx;padding-left:22rpx}}

.mentor-info-edit-mode-notice,.mentor-info-edit-pending{display:flex;align-items:center;justify-content:space-between;gap:18rpx;margin-top:18rpx;padding:19rpx 22rpx;border:2rpx solid #f2c7ca;border-radius:22rpx;background:#fff9f9;box-shadow:0 10rpx 24rpx rgba(218,114,122,.05)}
.mentor-info-edit-mode-notice strong,.mentor-info-edit-mode-notice text,.mentor-info-edit-pending strong,.mentor-info-edit-pending text{display:block}
.mentor-info-edit-mode-notice strong,.mentor-info-edit-pending strong{color:#9b5963;font-size:23rpx;line-height:1.25;font-weight:900}
.mentor-info-edit-mode-notice text,.mentor-info-edit-pending text{margin-top:6rpx;color:#9b727a;font-size:18rpx;line-height:1.45;font-weight:650}
.mentor-info-edit-mode-notice button{box-sizing:border-box;min-width:78rpx;height:50rpx;min-height:50rpx;margin:0;padding:0 14rpx;border:0;border-radius:15rpx;background:#fff;color:#b26a73;display:flex;align-items:center;justify-content:center;text-align:center;font-size:19rpx;line-height:1;font-weight:850;white-space:nowrap;box-shadow:0 5rpx 14rpx rgba(180,106,115,.09);flex-shrink:0}
.mentor-info-edit-mode-notice button::after{border:0}
.mentor-info-facts>view.is-editable,.mentor-info-stats-grid>view.is-editable{position:relative;background:#fffafa;box-shadow:inset 0 0 0 2rpx #f2bfc3}
.mentor-info-edit-input,.mentor-info-edit-picker{box-sizing:border-box;width:100%;min-height:38rpx;margin-top:8rpx;padding:0;border:0;background:transparent;color:#435671;font-size:22rpx;line-height:1.35;font-weight:900}
.mentor-info-edit-picker{display:flex;align-items:center;justify-content:space-between}
.mentor-info-edit-picker text{margin:0;color:#bd7b82;font-size:23rpx;line-height:1}
.mentor-info-edit-placeholder{color:#b9a2a5;font-weight:600}
.mentor-info-detail-block.is-editable{padding:18rpx;border:2rpx solid #f2bfc3;border-radius:19rpx;background:#fffafa}
.mentor-info-detail-block.is-editable+.mentor-info-detail-block.is-editable{margin-top:14rpx}
.mentor-info-detail-title{display:flex;align-items:center;justify-content:space-between;gap:12rpx}
.mentor-info-detail-title text{color:#b4777e;font-size:18rpx;font-weight:700}
.mentor-info-skill-options{display:flex;flex-wrap:wrap;gap:10rpx;margin-top:16rpx}
.mentor-info-skill-options button{box-sizing:border-box;min-height:48rpx;margin:0;padding:0 14rpx;border:2rpx solid #f0d3d5;border-radius:14rpx;background:#fff;color:#8b737a;display:flex;align-items:center;justify-content:center;text-align:center;font-size:19rpx;line-height:1;font-weight:750;white-space:nowrap}
.mentor-info-skill-options button::after{border:0}
.mentor-info-skill-options button.active{border-color:#eaaeb3;background:#fff0f1;color:#b65f69}
.mentor-info-bio-editor{margin-top:14rpx}
.mentor-info-bio-editor textarea{box-sizing:border-box;width:100%;min-height:166rpx;padding:14rpx;border:0;border-radius:14rpx;background:#fff;color:#53677f;font-size:21rpx;line-height:1.58;font-weight:600}
.mentor-info-price-editor{display:flex;align-items:center;gap:5rpx;margin-top:6rpx;color:#b45f69}
.mentor-info-price-editor text{margin:0;color:#b45f69;font-size:20rpx;font-weight:850}
.mentor-info-price-editor input{width:74rpx;min-height:38rpx;padding:0;border:0;background:transparent;color:#435671;font-size:23rpx;font-weight:900;text-align:center}
.mentor-info-profile-edit-action.is-editing{border-top-color:#f3d5d7}
.mentor-info-profile-edit-button.submit{border:0;background:#3478f6;color:#fff;box-shadow:0 10rpx 20rpx rgba(52,120,246,.18)}

.mentor-info-page { background: var(--gyt-page-bg); }
.mentor-info-hero,.mentor-info-section { border-color: var(--gyt-primary-border, #d9e7fc); background: var(--gyt-panel-bg, #ffffff); box-shadow: 0 14rpx 34rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.06)); }
.mentor-info-avatar:not(.tone-mint):not(.tone-violet):not(.tone-warm),.mentor-info-verified,.mentor-info-skills text { background: var(--gyt-primary-soft, #edf4ff); color: var(--gyt-primary, #3478f6); }
.mentor-info-facts,.mentor-info-stats-grid,.mentor-info-detail-block.has-divider { border-color: var(--gyt-primary-border, #edf2f8); }
.mentor-info-state-empty button,.mentor-info-modal-button.primary,.mentor-info-profile-edit-button.submit { background: var(--gyt-primary-gradient, #3478f6); box-shadow: 0 10rpx 20rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.18)); }
@media(max-width:350px){.mentor-info-edit-mode-notice,.mentor-info-edit-pending{padding-right:18rpx;padding-left:18rpx}.mentor-info-detail-block.is-editable{padding:15rpx}.mentor-info-skill-options button{padding-right:11rpx;padding-left:11rpx;font-size:18rpx}}
</style>
