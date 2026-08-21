<template>
  <view class="mentor-apply-page">
    <MentorPageHeader :title="pageTitle" @back="goBack" />

    <scroll-view :scroll-y="pageMode !== 'center'" class="mentor-apply-scroll">
      <view v-if="pageMode === 'apply'" class="mentor-apply-content">
        <view class="mentor-apply-card">
          <view class="mentor-apply-section-title">认证基本信息</view>
          <view class="mentor-apply-field">
            <view class="mentor-apply-label">真实姓名 <text>后台审核使用</text></view>
            <input v-model="form.realName" placeholder="请输入真实姓名" placeholder-class="mentor-apply-placeholder" />
            <view class="mentor-apply-tip">公开展示时系统会自动进行姓名脱敏。</view>
          </view>
          <view class="mentor-apply-field">
            <view class="mentor-apply-label">录取院校</view>
            <input v-model="schoolKeyword" placeholder="搜索或输入录取院校" placeholder-class="mentor-apply-placeholder" @input="handleSchoolInput" />
            <view v-if="schoolResults.length" class="mentor-apply-search-results">
              <button v-for="school in schoolResults" :key="school" @tap="selectSchool(school)">{{ school }}</button>
            </view>
          </view>
          <view class="mentor-apply-field">
            <view class="mentor-apply-label">录取专业</view>
            <input v-model="form.major" placeholder="支持搜索或直接输入专业" placeholder-class="mentor-apply-placeholder" />
          </view>
          <view class="mentor-apply-two-column">
            <view class="mentor-apply-field">
              <view class="mentor-apply-label">入学年份</view>
              <picker mode="selector" :range="yearOptions" :value="admissionYearIndex" @change="selectAdmissionYear">
                <view class="mentor-apply-picker">{{ form.admissionYear }} <text>⌄</text></view>
              </picker>
            </view>
            <view class="mentor-apply-field">
              <view class="mentor-apply-label">毕业年份</view>
              <picker mode="selector" :range="yearOptions" :value="graduationYearIndex" @change="selectGraduationYear">
                <view class="mentor-apply-picker">{{ form.graduationYear }} <text>⌄</text></view>
              </picker>
            </view>
          </view>
          <view class="mentor-apply-two-column">
            <view class="mentor-apply-field">
              <view class="mentor-apply-label">初试成绩</view>
              <input v-model="form.score" type="number" min="0" max="150" placeholder="例如 110" placeholder-class="mentor-apply-placeholder" @input="handleScoreInput" />
            </view>
            <view class="mentor-apply-field">
              <view class="mentor-apply-label">考试类别</view>
              <view class="mentor-apply-exam-row">
                <button v-for="item in examOptions" :key="item" :class="{ active: form.examType === item }" @tap="form.examType = item">{{ item }}</button>
              </view>
            </view>
          </view>
        </view>

        <view class="mentor-apply-card">
          <view class="mentor-apply-section-title">证明材料</view>
          <view class="mentor-apply-copy">上传录取通知书、学生证或其他录取证明；材料仅用于平台认证审核，不对其他用户公开。</view>
          <view class="mentor-proof-grid">
            <view v-for="(proof, index) in proofImages" :key="proof.id || proof.path" class="mentor-proof-image">
              <image :src="proof.path" mode="aspectFill" />
              <button @tap="removeProof(index)">×</button>
            </view>
            <button v-if="proofImages.length < 3" class="mentor-proof-upload" @tap="chooseProof">
              <text>＋</text><view>上传证明</view>
            </button>
          </view>
        </view>

        <view class="mentor-apply-card">
          <view class="mentor-apply-section-title">擅长咨询领域</view>
          <view class="mentor-apply-copy">最多选择 4 项，方便考生更精准地找到你。</view>
          <view class="mentor-skill-options">
            <button v-for="item in skillOptions" :key="item" :class="{ active: form.skills.includes(item) }" @tap="toggleSkill(item)">{{ item }}</button>
          </view>
        </view>

        <view class="mentor-apply-card">
          <view class="mentor-apply-label"><text>个人简介</text><text>{{ form.bio.length }} / 500</text></view>
          <textarea v-model="form.bio" maxlength="500" placeholder="介绍你的上岸经历、可提供的帮助和擅长方向。" placeholder-class="mentor-apply-placeholder" />
          <view class="mentor-apply-price-field">
            <view><strong>咨询价格</strong><text>单次咨询默认开启 60 分钟咨询窗口。</text></view>
            <view class="mentor-price-input"><text>¥</text><input v-model="form.price" type="number" /><text>/ 次</text></view>
          </view>
        </view>
        <view class="mentor-apply-bottom-space"></view>
      </view>

      <view v-else-if="pageMode === 'pending'" class="mentor-apply-status-content">
        <view class="mentor-apply-status-icon pending">⌛</view>
        <view class="mentor-apply-status-title">认证审核中</view>
        <view class="mentor-apply-status-copy">认证资料已提交，平台将在审核后通知结果。审核期间你可以继续使用考研圈的其他功能。</view>
        <view class="mentor-apply-status-card">
          <view><text>申请院校</text><strong>{{ form.school || '待审核院校' }}</strong></view>
          <view><text>申请专业</text><strong>{{ form.major || '待审核专业' }}</strong></view>
          <view><text>提交状态</text><strong class="green">资料已提交</strong></view>
        </view>
      </view>

      <view v-else class="mentor-apply-center-content">
        <template v-if="mentorProfile">
          <view
            class="mentor-center-hero mentor-center-hero-action"
            role="button"
            aria-label="查看我的信息"
            @tap="openMentorInfo"
          >
            <view class="mentor-center-avatar" :class="`tone-${mentorProfile.avatarTone || 'blue'}`">
              <image v-if="mentorCenterAvatarUrl" :src="mentorCenterAvatarUrl" mode="aspectFill" />
              <text v-else>{{ mentorProfile.avatar || '前' }}</text>
            </view>
            <view>
              <strong>{{ mentorProfile.maskedName }}</strong>
              <text>✓ 平台认证前辈</text>
              <view>{{ mentorProfile.school }} · {{ mentorProfile.major }}</view>
            </view>
            <text class="mentor-center-hero-arrow" aria-hidden="true">›</text>
          </view>

          <view class="mentor-center-status">
            <view>
              <strong>{{ mentorProfile.onlineStatus === 'online' ? '在线接单中' : '暂不接即时咨询' }}</strong>
              <text>{{ mentorProfile.onlineStatus === 'online' ? '考生可以向你发起即时咨询' : '仍可保留已完成支付的预约咨询' }}</text>
            </view>
            <view class="mentor-center-status-actions">
              <view
                v-if="mentorProfile.onlineStatus !== 'online'"
                class="mentor-center-schedule-button"
                role="button"
                aria-label="设置预约时段"
                @tap="openMentorSchedule"
              ><text class="mentor-center-schedule-button-label">设置预约时段</text></view>
              <switch
                :checked="mentorProfile.onlineStatus === 'online'"
                :disabled="onlineStatusUpdating"
                color="#3478f6"
                @change="handleOnlineStatusChange"
              />
            </view>
          </view>

          <view class="mentor-center-orders">
            <view class="mentor-center-orders-heading">
              <view><strong>咨询请求</strong><text>即时咨询需在 10 分钟内处理</text></view>
              <button :loading="mentorOrdersLoading" @tap="loadReceivedOrders">刷新</button>
            </view>

            <scroll-view scroll-y :show-scrollbar="false" class="mentor-center-orders-scroll">
              <view class="mentor-center-orders-list">
                <view v-if="mentorOrdersLoading && !mentorOrders.length" class="mentor-center-empty">正在加载咨询请求…</view>
                <view v-else-if="!mentorOrders.length" class="mentor-center-empty">暂时没有新的咨询请求</view>

                <view v-for="order in mentorOrders" :key="order.id" class="mentor-center-order-card">
                  <view class="mentor-center-order-head">
                    <view>
                      <strong>{{ getOrderTypeLabel(order) }}</strong>
                      <text>{{ formatOrderTime(order.createdAt) }}</text>
                    </view>
                    <view class="mentor-center-order-status" :class="order.orderStatus">{{ getOrderStatusLabel(order.orderStatus) }}</view>
                  </view>

                  <view class="mentor-center-order-student">
                    {{ order.questionnaire?.name || '匿名同学' }} · {{ order.questionnaire?.school || '未填写学校' }} · {{ order.questionnaire?.major || '未填写专业' }}
                  </view>
                  <view v-if="order.questionnaire?.question" class="mentor-center-order-question">“{{ order.questionnaire.question }}”</view>
                  <view class="mentor-center-order-meta">
                    <text>{{ order.consultationType === 'booking' ? '预约咨询' : '即时咨询' }}</text>
                    <strong>¥{{ order.price }}</strong>
                  </view>

                  <view v-if="order.orderStatus === 'pending_accept'" class="mentor-center-order-actions">
                    <button class="light" :loading="centerActionId === order.id" @tap="handleOrderDecision(order, 'reject')">暂不接受</button>
                    <button :loading="centerActionId === order.id" @tap="handleOrderDecision(order, 'accept')">接受咨询</button>
                  </view>
                  <view v-else-if="['accepted', 'in_progress'].includes(order.orderStatus)" class="mentor-center-order-actions">
                    <button :loading="centerActionId === order.id" @tap="openMentorOrderChat(order)">{{ order.orderStatus === 'accepted' ? '开始咨询' : '进入咨询' }}</button>
                  </view>
                </view>
              </view>
            </scroll-view>
          </view>
        </template>

        <view v-else-if="centerLoading" class="mentor-center-skeleton" aria-label="正在加载前辈主页">
          <view class="mentor-center-skeleton-hero">
            <view class="mentor-center-skeleton-avatar"></view>
            <view class="mentor-center-skeleton-copy"><view></view><view></view><view></view></view>
          </view>
          <view class="mentor-center-skeleton-status"><view></view><view></view></view>
          <view class="mentor-center-skeleton-orders"><view></view><view></view><view></view></view>
        </view>

        <view v-else class="mentor-center-loading">当前账号暂未绑定可用的前辈档案。</view>
      </view>
    </scroll-view>

    <view v-if="pageMode === 'apply'" class="mentor-apply-footer"><button :disabled="submitting" @tap="submitApplication">{{ submitting ? '提交中…' : '提交认证' }}</button></view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import {
  createMentorVerificationApplication,
  decideMentorConsultationOrder,
  fetchMyMentorProfile,
  fetchMyMentorVerificationApplication,
  fetchMyReceivedMentorOrders,
  startMentorConsultationOrder,
  updateMyMentorAvailability,
  uploadMentorVerificationDocument
} from '../../api/mentorConsultation'
import {
  MENTOR_SKILL_OPTIONS,
  getMentorApplication,
  getMentorVerificationStatus,
  maskMentorName,
  normalizeMentorConsultationOrder,
  normalizeMentorDetailResponse,
  saveMentorApplication,
  searchMentorSchools,
  setMentorVerificationStatus
} from '../../data/mentorConsultation'
import { getAuthUser, isLoggedIn } from '../../utils/auth'

const pageMode = ref('apply')
const schoolKeyword = ref('')
const proofImages = ref([])
const submitting = ref(false)
const skillOptions = MENTOR_SKILL_OPTIONS
const examOptions = ['Z001', 'Z002', '申请制']
const yearOptions = ['2028', '2027', '2026', '2025', '2024', '2023', '2022']
const form = ref(createDefaultApplication())
const mentorProfile = ref(null)
const mentorOrders = ref([])
const centerLoading = ref(false)
const mentorOrdersLoading = ref(false)
const onlineStatusUpdating = ref(false)
const centerActionId = ref('')
const ownerUser = ref(getAuthUser() || {})

const MENTOR_CENTER_PROFILE_CACHE_PREFIX = 'circle-mentor-center-profile-v1'
const MENTOR_CENTER_PROFILE_CACHE_MAX_AGE = 7 * 24 * 60 * 60 * 1000

const pageTitle = computed(() => pageMode.value === 'pending' ? '认证审核中' : pageMode.value === 'center' ? '我的咨询主页' : '申请成为前辈')
const schoolResults = computed(() => searchMentorSchools(schoolKeyword.value))
const admissionYearIndex = computed(() => Math.max(0, yearOptions.indexOf(String(form.value.admissionYear))))
const graduationYearIndex = computed(() => Math.max(0, yearOptions.indexOf(String(form.value.graduationYear))))
const maskedApplicationName = computed(() => maskMentorName(form.value.realName || '前辈'))
const mentorCenterAvatarUrl = computed(() => getUserAvatarUrl(ownerUser.value) || mentorProfile.value?.avatarUrl || '')

onLoad((options) => {
  void initializePage(options)
})

onShow(() => {
  ownerUser.value = getAuthUser() || {}
  if (pageMode.value === 'center' && mentorProfile.value) {
    void loadReceivedOrders({ silent: true })
  }
})

async function initializePage(options) {
  ownerUser.value = getAuthUser() || {}
  const saved = getMentorApplication()
  if (saved) {
    form.value = { ...createDefaultApplication(), ...saved }
    proofImages.value = normalizeProofImages(saved.proofImages)
  }
  const verificationStatus = getMentorVerificationStatus()
  const fallbackPageMode = verificationStatus === 'verified' ? 'center' : verificationStatus === 'pending' ? 'pending' : (options?.mode === 'pending' ? 'pending' : 'apply')
  pageMode.value = fallbackPageMode
  if (!isLoggedIn()) {
    pageMode.value = 'apply'
    return
  }

  pageMode.value = 'center'
  const cachedProfile = getCachedMentorCenterProfile()
  if (cachedProfile) {
    applyMentorProfile(cachedProfile)
  }
  centerLoading.value = !mentorProfile.value

  // The profile and order list do not depend on each other.  Starting them
  // together prevents the homepage from waiting for two network round trips.
  void loadReceivedOrders({ silent: true })
  try {
    const profilePayload = await fetchMyMentorProfile()
    const profile = normalizeMentorDetailResponse(profilePayload)
    if (profile) {
      applyMentorProfile(profile, { persist: true })
      pageMode.value = 'center'
      return
    }
    clearCachedMentorCenterProfile()
    mentorProfile.value = null
  } catch (error) {
    // Keep the last successful screen visible when a background refresh is
    // temporarily affected by a weak network or a token refresh.
    if (error?.statusCode === 404) {
      clearCachedMentorCenterProfile()
      mentorProfile.value = null
    }
    if (mentorProfile.value) return
    if (error?.statusCode !== 404) {
      uni.showToast({ title: error?.detail || '前辈主页加载失败', icon: 'none' })
    }
  } finally {
    centerLoading.value = false
  }

  try {
    const response = await fetchMyMentorVerificationApplication()
    if (response?.application) {
      applyServerApplication(response.application)
      return
    }
  } catch (error) {
    // Preserve the local state when the verification service is temporarily unavailable.
  }
  pageMode.value = fallbackPageMode
}

function createDefaultApplication() {
  return {
    realName: '', school: '', major: '', admissionYear: '2025', graduationYear: '2027', score: '', examType: 'Z001', skills: [], bio: '', price: '39'
  }
}

function handleSchoolInput(event) {
  form.value.school = event?.detail?.value || schoolKeyword.value
  schoolKeyword.value = form.value.school
}

function selectSchool(school) {
  form.value.school = school
  schoolKeyword.value = school
}

function selectAdmissionYear(event) { form.value.admissionYear = yearOptions[Number(event?.detail?.value)] || yearOptions[0] }
function selectGraduationYear(event) { form.value.graduationYear = yearOptions[Number(event?.detail?.value)] || yearOptions[0] }

function handleScoreInput(event) {
  const rawValue = String(event?.detail?.value ?? '')
  if (!rawValue) {
    form.value.score = ''
    return
  }
  const score = Number(rawValue)
  form.value.score = Number.isFinite(score) ? String(Math.min(150, Math.max(0, Math.trunc(score)))) : ''
}

function toggleSkill(skill) {
  if (form.value.skills.includes(skill)) {
    form.value.skills = form.value.skills.filter((item) => item !== skill)
    return
  }
  if (form.value.skills.length >= 4) {
    uni.showToast({ title: '最多选择 4 个擅长领域', icon: 'none' })
    return
  }
  form.value.skills = [...form.value.skills, skill]
}

function chooseProof() {
  uni.chooseImage({
    count: Math.max(1, 3 - proofImages.value.length),
    sizeType: ['compressed'],
    success(result) {
      const tempFiles = Array.isArray(result.tempFiles) ? result.tempFiles : []
      const tempFilePaths = Array.isArray(result.tempFilePaths) ? result.tempFilePaths : []
      const files = tempFilePaths.map((path, index) => {
        const tempFile = tempFiles[index]
        const candidate = tempFile?.file || tempFile?.fileObject || tempFile
        const file = typeof Blob !== 'undefined' && candidate instanceof Blob ? candidate : null
        return {
          id: `mentor-proof-${Date.now()}-${index}-${Math.random().toString(36).slice(2, 8)}`,
          path: path || tempFile?.path || tempFile?.tempFilePath || '',
          file,
          fileName: tempFile?.name || file?.name || `mentor-proof-${index + 1}`
        }
      }).filter((item) => item.path)
      proofImages.value = [...proofImages.value, ...files].slice(0, 3)
    },
    fail() {
      uni.showToast({ title: '未选择证明材料', icon: 'none' })
    }
  })
}

function removeProof(index) { proofImages.value = proofImages.value.filter((_, itemIndex) => itemIndex !== index) }

async function submitApplication() {
  if (submitting.value) return
  if (!isLoggedIn()) {
    uni.navigateTo({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/circle/mentor-apply')}` })
    return
  }
  if (!form.value.realName.trim() || !form.value.school.trim() || !form.value.major.trim() || !String(form.value.score).trim()) {
    uni.showToast({ title: '请补充真实姓名、录取院校、专业和初试成绩', icon: 'none' })
    return
  }
  const score = Number(form.value.score)
  if (!Number.isInteger(score) || score < 0 || score > 150) {
    uni.showToast({ title: '初试成绩请填写 0–150 分', icon: 'none' })
    return
  }
  const price = Number(form.value.price)
  if (!Number.isFinite(price) || price < 0 || price > 1000) {
    uni.showToast({ title: '请输入正确的咨询价格', icon: 'none' })
    return
  }
  submitting.value = true
  try {
    const application = await createMentorVerificationApplication({
      legal_name: form.value.realName.trim(),
      school: form.value.school.trim(),
      major: form.value.major.trim(),
      admission_year: Number(form.value.admissionYear),
      graduation_year: form.value.graduationYear ? Number(form.value.graduationYear) : null,
      exam_type: form.value.examType === '申请制' ? 'application' : form.value.examType,
      score,
      skills: form.value.skills,
      bio: form.value.bio.trim(),
      price_cents: Math.round(price * 100)
    })
    for (const proof of proofImages.value) {
      await uploadMentorVerificationDocument(application.id, proof)
    }
    saveMentorApplication({ ...form.value, proofImages: proofImages.value.map((item) => item.path) })
    setMentorVerificationStatus('pending')
    pageMode.value = 'pending'
    uni.showToast({ title: '申请已提交，等待审核', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '申请提交失败，请稍后重试', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function normalizeProofImages(value) {
  return (Array.isArray(value) ? value : []).map((item, index) => {
    if (typeof item === 'string') return { id: `saved-proof-${index}`, path: item, file: null, fileName: `证明材料 ${index + 1}` }
    return { id: item?.id || `saved-proof-${index}`, path: item?.path || '', file: item?.file || null, fileName: item?.fileName || `证明材料 ${index + 1}` }
  }).filter((item) => item.path)
}

function applyServerApplication(application) {
  form.value = {
    ...createDefaultApplication(),
    realName: application.legal_name || '',
    school: application.school || '',
    major: application.major || '',
    admissionYear: String(application.admission_year || ''),
    graduationYear: application.graduation_year ? String(application.graduation_year) : '',
    score: String(application.score ?? ''),
    examType: application.exam_type === 'application' ? '申请制' : application.exam_type || 'Z001',
    skills: Array.isArray(application.skills) ? application.skills : [],
    bio: application.bio || '',
    price: String(application.price ?? 39)
  }
  schoolKeyword.value = form.value.school
  const status = application.application_status === 'approved' ? 'verified' : application.application_status === 'pending' ? 'pending' : 'rejected'
  setMentorVerificationStatus(status)
  pageMode.value = status === 'verified' ? 'center' : status === 'pending' ? 'pending' : 'apply'
}

function syncFormFromMentorProfile(profile) {
  form.value = {
    ...form.value,
    realName: profile.name || profile.maskedName || '',
    school: profile.school || '',
    major: profile.major || '',
    admissionYear: String(profile.admissionYear || form.value.admissionYear),
    graduationYear: String(profile.graduationYear || form.value.graduationYear),
    score: String(profile.score ?? form.value.score),
    examType: profile.examType === 'application' ? '申请制' : (profile.examType || form.value.examType),
    skills: Array.isArray(profile.skills) ? profile.skills.slice(0, 4) : form.value.skills,
    bio: profile.bio || form.value.bio,
    price: String(profile.price ?? form.value.price)
  }
  schoolKeyword.value = form.value.school
}

async function loadReceivedOrders({ silent = false } = {}) {
  if (mentorOrdersLoading.value) return
  mentorOrdersLoading.value = true
  try {
    const payload = await fetchMyReceivedMentorOrders({ limit: 50 })
    mentorOrders.value = (Array.isArray(payload?.items) ? payload.items : [])
      .map((order) => normalizeMentorConsultationOrder(order))
  } catch (error) {
    if (!silent) uni.showToast({ title: error?.detail || '咨询请求加载失败', icon: 'none' })
  } finally {
    mentorOrdersLoading.value = false
  }
}

async function handleOnlineStatusChange(event) {
  if (!mentorProfile.value || onlineStatusUpdating.value) return
  const online = Boolean(event?.detail?.value)
  onlineStatusUpdating.value = true
  try {
    const payload = await updateMyMentorAvailability(online ? 'online' : 'offline')
    const profile = normalizeMentorDetailResponse(payload)
    if (profile) {
      applyMentorProfile(profile, { persist: true })
    }
    uni.showToast({ title: online ? '已开启在线接单' : '已暂停即时咨询', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '在线状态更新失败', icon: 'none' })
  } finally {
    onlineStatusUpdating.value = false
  }
}

async function handleOrderDecision(order, decision) {
  if (!order?.id || centerActionId.value) return
  centerActionId.value = order.id
  try {
    const updated = normalizeMentorConsultationOrder(await decideMentorConsultationOrder(order.id, decision))
    mentorOrders.value = mentorOrders.value.map((item) => item.id === updated.id ? updated : item)
    uni.showToast({ title: decision === 'accept' ? '已接受本次咨询' : '已拒绝本次咨询', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '处理咨询请求失败', icon: 'none' })
  } finally {
    centerActionId.value = ''
  }
}

async function openMentorOrderChat(order) {
  if (!order?.id || !mentorProfile.value || centerActionId.value) return
  centerActionId.value = order.id
  try {
    let activeOrder = order
    if (order.orderStatus === 'accepted') {
      activeOrder = normalizeMentorConsultationOrder(await startMentorConsultationOrder(order.id))
      mentorOrders.value = mentorOrders.value.map((item) => item.id === activeOrder.id ? activeOrder : item)
    }
    uni.navigateTo({
      url: `/pages/circle/mentor-chat?mentorId=${encodeURIComponent(mentorProfile.value.id)}&orderId=${encodeURIComponent(activeOrder.id)}&role=mentor`
    })
  } catch (error) {
    uni.showToast({ title: error?.detail || '暂时无法进入咨询', icon: 'none' })
  } finally {
    centerActionId.value = ''
  }
}

function openMentorSchedule() {
  uni.navigateTo({ url: '/pages/circle/mentor-schedule' })
}

function openMentorInfo() {
  uni.navigateTo({ url: '/pages/circle/mentor-info' })
}

function applyMentorProfile(profile, { persist = false } = {}) {
  mentorProfile.value = profile
  syncFormFromMentorProfile(profile)
  if (persist) saveMentorCenterProfile(profile)
}

function getMentorCenterProfileCacheKey() {
  const user = ownerUser.value || {}
  const userId = String(user.id || user.user_id || user.userId || '').trim()
  return userId ? `${MENTOR_CENTER_PROFILE_CACHE_PREFIX}:${userId}` : ''
}

function getCachedMentorCenterProfile() {
  const cacheKey = getMentorCenterProfileCacheKey()
  if (!cacheKey) return null
  try {
    const cached = uni.getStorageSync(cacheKey)
    const updatedAt = Number(cached?.updatedAt || 0)
    if (!updatedAt || Date.now() - updatedAt > MENTOR_CENTER_PROFILE_CACHE_MAX_AGE) {
      if (cached) uni.removeStorageSync(cacheKey)
      return null
    }
    return normalizeMentorDetailResponse(cached?.profile)
  } catch (error) {
    return null
  }
}

function saveMentorCenterProfile(profile) {
  const cacheKey = getMentorCenterProfileCacheKey()
  if (!cacheKey || !profile?.id) return
  try {
    uni.setStorageSync(cacheKey, { updatedAt: Date.now(), profile })
  } catch (error) {
    // Cache failures should never block entering the mentor homepage.
  }
}

function clearCachedMentorCenterProfile() {
  const cacheKey = getMentorCenterProfileCacheKey()
  if (!cacheKey) return
  try {
    uni.removeStorageSync(cacheKey)
  } catch (error) {
    // Storage cleanup is best effort only.
  }
}

function getUserAvatarUrl(user = {}) {
  const value = String(user?.avatar_url || user?.avatarUrl || '').trim()
  return /^(https?:\/\/|data:image\/)/i.test(value) ? value : ''
}

function getOrderTypeLabel(order = {}) {
  return order.consultationType === 'booking' ? '预约咨询' : '即时咨询'
}

function getOrderStatusLabel(orderStatus) {
  return ({
    pending_accept: '待接单',
    accepted: '已接受',
    in_progress: '咨询中',
    completed: '已完成',
    rejected: '已拒绝',
    timeout: '已超时',
    refunded: '已退款',
    booked: '已预约'
  })[orderStatus] || '处理中'
}

function formatOrderTime(value) {
  const date = new Date(value || '')
  if (Number.isNaN(date.getTime())) return '刚刚'
  const now = new Date()
  const sameDate = now.toDateString() === date.toDateString()
  return sameDate
    ? `今天 ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
    : `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function goBack() {
  uni.navigateBack({ fail() { uni.reLaunch({ url: '/pages/home/index?tab=circle&section=community&communityTab=mentor' }) } })
}
</script>

<style scoped>
.mentor-apply-page{height:100vh;overflow:hidden;background:#f4f8ff;display:flex;flex-direction:column}.mentor-apply-scroll{min-height:0;flex:1}.mentor-apply-content{padding:24rpx 24rpx 0}
.mentor-apply-card{margin-top:18rpx;padding:28rpx;border:2rpx solid #d9e7fc;border-radius:28rpx;background:rgba(255,255,255,.93);box-shadow:0 14rpx 34rpx rgba(52,120,246,.06)}.mentor-apply-section-title{color:#273953;font-size:28rpx;font-weight:900}.mentor-apply-field{margin-top:23rpx}.mentor-apply-label{display:flex;align-items:center;justify-content:space-between;gap:10rpx;margin-bottom:12rpx;color:#40546e;font-size:23rpx;line-height:1.25;font-weight:850}.mentor-apply-label>text:last-child{color:#98a9c0;font-size:18rpx;font-weight:650}.mentor-apply-label>text:first-child{color:inherit;font-size:inherit;font-weight:inherit}.mentor-apply-label>text{color:inherit;display:inline;font-weight:inherit}.mentor-apply-label>text+text{color:#98a9c0;font-size:18rpx}.mentor-apply-label > text:last-child{font-weight:650}
.mentor-apply-field input,.mentor-apply-picker{box-sizing:border-box;width:100%;height:72rpx;padding:0 18rpx;border:2rpx solid #e0eafa;border-radius:18rpx;background:#fbfdff;color:#2d405d;font-size:23rpx;line-height:68rpx;font-weight:650}.mentor-apply-placeholder{color:#a7b3c4;font-weight:500}.mentor-apply-tip{margin-top:8rpx;color:#91a0b4;font-size:18rpx;line-height:1.4;font-weight:600}.mentor-apply-search-results{display:flex;flex-wrap:wrap;gap:9rpx;margin-top:11rpx}.mentor-apply-search-results button,.mentor-apply-exam-row button,.mentor-skill-options button{min-height:48rpx;margin:0;padding:0 14rpx;border:2rpx solid #dce7f8;border-radius:14rpx;background:#fbfdff;color:#708199;font-size:20rpx;font-weight:750}.mentor-apply-search-results button::after,.mentor-apply-exam-row button::after,.mentor-skill-options button::after,.mentor-proof-image button::after,.mentor-proof-upload::after,.mentor-apply-footer button::after,.mentor-apply-demo-card button::after{border:0}.mentor-apply-two-column{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16rpx}.mentor-apply-picker{display:flex;align-items:center;justify-content:space-between;line-height:1.2}.mentor-apply-picker text{color:#8494a9;font-size:24rpx}.mentor-apply-exam-row{display:flex;flex-wrap:wrap;gap:8rpx}.mentor-apply-exam-row button{min-width:70rpx}.mentor-apply-exam-row button.active,.mentor-skill-options button.active{border-color:#b9d2ff;background:#edf4ff;color:#3478f6}.mentor-apply-copy{margin-top:10rpx;color:#7e8ea4;font-size:20rpx;line-height:1.55;font-weight:650}.mentor-proof-grid{display:flex;flex-wrap:wrap;gap:12rpx;margin-top:20rpx}.mentor-proof-image,.mentor-proof-upload{width:140rpx;height:140rpx;border-radius:18rpx;overflow:hidden;position:relative}.mentor-proof-image{border:2rpx solid #d8e6fa}.mentor-proof-image image{width:100%;height:100%}.mentor-proof-image button{position:absolute;top:6rpx;right:6rpx;width:34rpx;height:34rpx;min-height:34rpx;margin:0;padding:0;border:0;border-radius:50%;background:rgba(27,42,66,.62);color:#fff;font-size:26rpx;line-height:1}.mentor-proof-upload{margin:0;border:2rpx dashed #bed4f7;background:#f7faff;color:#6180b4;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:20rpx;font-weight:750}.mentor-proof-upload>text{font-size:42rpx;line-height:1}.mentor-proof-upload view{margin-top:7rpx;font-size:18rpx}.mentor-skill-options{display:flex;flex-wrap:wrap;gap:10rpx;margin-top:18rpx}.mentor-apply-card textarea{box-sizing:border-box;width:100%;min-height:178rpx;padding:16rpx;border:2rpx solid #e0eafa;border-radius:18rpx;background:#fbfdff;color:#3a4f6e;font-size:22rpx;line-height:1.5}.mentor-apply-price-field{margin-top:24rpx;padding-top:20rpx;border-top:2rpx solid #edf1f8;display:flex;align-items:center;justify-content:space-between;gap:18rpx}.mentor-apply-price-field strong,.mentor-apply-price-field text{display:block}.mentor-apply-price-field strong{color:#40546e;font-size:23rpx;font-weight:900}.mentor-apply-price-field text{margin-top:6rpx;color:#8d9bb0;font-size:18rpx;line-height:1.35;font-weight:650}.mentor-price-input{display:flex;align-items:center;gap:5rpx;border:2rpx solid #d9e7fa;border-radius:16rpx;background:#fbfdff;color:#3478f6;padding:0 12rpx;flex-shrink:0}.mentor-price-input input{width:58rpx;height:58rpx;padding:0;border:0;background:transparent;color:#2d405d;text-align:center;font-size:25rpx;font-weight:900}.mentor-price-input text{margin:0;color:#5e78a3;font-size:20rpx;font-weight:800}.mentor-apply-bottom-space{height:calc(136rpx + env(safe-area-inset-bottom))}.mentor-apply-footer{padding:16rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));border-top:2rpx solid #dbe7f8;background:rgba(255,255,255,.97)}.mentor-apply-footer button{width:100%;min-height:76rpx;margin:0;border:0;border-radius:20rpx;background:#3478f6;color:#fff;font-size:24rpx;font-weight:900;box-shadow:0 10rpx 22rpx rgba(52,120,246,.2)}
.mentor-apply-status-content,.mentor-apply-center-content{padding:84rpx 24rpx 50rpx;text-align:center}.mentor-apply-status-icon{width:100rpx;height:100rpx;margin:0 auto;border-radius:50%;background:#edf4ff;color:#3478f6;display:flex;align-items:center;justify-content:center;font-size:45rpx;font-weight:900}.mentor-apply-status-title{margin-top:22rpx;color:#283b56;font-size:32rpx;font-weight:900}.mentor-apply-status-copy{max-width:560rpx;margin:14rpx auto 0;color:#7d8ea6;font-size:22rpx;line-height:1.6;font-weight:650}.mentor-apply-status-card,.mentor-apply-demo-card{margin-top:32rpx;padding:26rpx;border:2rpx solid #d9e7fc;border-radius:26rpx;background:rgba(255,255,255,.93);text-align:left;box-shadow:0 14rpx 34rpx rgba(52,120,246,.06)}.mentor-apply-status-card>view{display:flex;align-items:center;justify-content:space-between;gap:20rpx;color:#8796a9;font-size:21rpx;font-weight:650}.mentor-apply-status-card>view+view{margin-top:18rpx}.mentor-apply-status-card strong{color:#40546d;font-weight:850}.mentor-apply-status-card strong.green{color:#278d58}.mentor-apply-demo-card strong,.mentor-apply-demo-card text{display:block}.mentor-apply-demo-card strong{color:#48648e;font-size:24rpx;font-weight:900}.mentor-apply-demo-card text{margin-top:8rpx;color:#8291a5;font-size:20rpx;line-height:1.5;font-weight:650}.mentor-apply-demo-card button{min-height:60rpx;margin:18rpx 0 0;padding:0 20rpx;border:0;border-radius:17rpx;background:#3478f6;color:#fff;font-size:21rpx;font-weight:850}
.mentor-center-hero,.mentor-center-status,.mentor-center-grid,.mentor-center-reserve{border:2rpx solid #d9e7fc;border-radius:28rpx;background:rgba(255,255,255,.93);box-shadow:0 14rpx 34rpx rgba(52,120,246,.06)}.mentor-center-hero{padding:28rpx;display:flex;align-items:center;gap:16rpx;text-align:left}.mentor-center-avatar{width:78rpx;height:78rpx;border-radius:50%;background:#e6efff;color:#3478f6;display:flex;align-items:center;justify-content:center;font-size:30rpx;font-weight:900;flex-shrink:0}.mentor-center-hero strong,.mentor-center-hero text,.mentor-center-hero view{display:block}.mentor-center-hero strong{color:#273a55;font-size:28rpx;font-weight:900}.mentor-center-hero text{margin-top:6rpx;color:#3478f6;font-size:19rpx;font-weight:800}.mentor-center-hero view{margin-top:6rpx;color:#7c8ca2;font-size:20rpx;font-weight:650}.mentor-center-status{margin-top:18rpx;padding:25rpx;display:flex;align-items:center;justify-content:space-between;gap:20rpx;text-align:left}.mentor-center-status strong,.mentor-center-status text{display:block}.mentor-center-status strong{color:#40546e;font-size:24rpx;font-weight:900}.mentor-center-status text{margin-top:6rpx;color:#8391a6;font-size:19rpx;line-height:1.4;font-weight:650}.mentor-center-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2rpx;margin-top:18rpx;overflow:hidden}.mentor-center-grid>view{padding:26rpx;border:1rpx solid #edf2f8;text-align:left}.mentor-center-grid text,.mentor-center-grid strong{display:block}.mentor-center-grid text{color:#8a98ab;font-size:19rpx;font-weight:650}.mentor-center-grid strong{margin-top:9rpx;color:#41546e;font-size:23rpx;font-weight:900}.mentor-center-reserve{margin-top:18rpx;padding:26rpx;text-align:left}.mentor-center-reserve strong,.mentor-center-reserve text{display:block}.mentor-center-reserve strong{color:#46618c;font-size:24rpx;font-weight:900}.mentor-center-reserve text{margin-top:9rpx;color:#8090a6;font-size:20rpx;line-height:1.55;font-weight:650}
.mentor-apply-exam-row{flex-wrap:nowrap}.mentor-apply-exam-row button{flex:1;min-width:0;min-height:72rpx;height:72rpx;padding:0;border-radius:18rpx;font-size:23rpx;line-height:68rpx;white-space:nowrap}
.mentor-center-avatar{overflow:hidden}.mentor-center-avatar image{width:100%;height:100%}.mentor-center-avatar.tone-mint{background:#e2f4ef;color:#198777}.mentor-center-avatar.tone-violet{background:#eeeafe;color:#7162bd}.mentor-center-avatar.tone-warm{background:#f9eee1;color:#b66c32}
.mentor-apply-center-content{padding:20rpx 24rpx 50rpx}.mentor-center-status-actions{display:flex;align-items:center;justify-content:flex-end;gap:14rpx;flex-shrink:0}.mentor-center-schedule-button{min-width:156rpx;min-height:54rpx;margin:0;padding:0 14rpx;border:2rpx solid #c9dcfb;border-radius:16rpx;background:#f7faff;color:#4d72a9;font-size:19rpx;line-height:1.2;font-weight:850;white-space:nowrap}.mentor-center-schedule-button::after{border:0}
.mentor-center-loading{padding:70rpx 30rpx;color:#7d8ea6;font-size:23rpx;font-weight:700}.mentor-center-skeleton{display:grid;gap:18rpx}.mentor-center-skeleton-hero,.mentor-center-skeleton-status,.mentor-center-skeleton-grid,.mentor-center-skeleton-orders{border:2rpx solid #d9e7fc;border-radius:28rpx;background:rgba(255,255,255,.93);box-shadow:0 14rpx 34rpx rgba(52,120,246,.04)}.mentor-center-skeleton-hero{display:flex;align-items:center;gap:16rpx;padding:28rpx}.mentor-center-skeleton-avatar,.mentor-center-skeleton-copy view,.mentor-center-skeleton-status view,.mentor-center-skeleton-grid view,.mentor-center-skeleton-orders>view{border-radius:999rpx;background:linear-gradient(90deg,#edf3fc 20%,#f8fbff 38%,#edf3fc 58%);background-size:220% 100%;animation:mentorCenterSkeletonShimmer 1.45s ease-in-out infinite}.mentor-center-skeleton-avatar{width:78rpx;height:78rpx;border-radius:50%;flex-shrink:0}.mentor-center-skeleton-copy{flex:1}.mentor-center-skeleton-copy view:nth-child(1){width:122rpx;height:25rpx}.mentor-center-skeleton-copy view:nth-child(2){width:160rpx;height:18rpx;margin-top:12rpx}.mentor-center-skeleton-copy view:nth-child(3){width:220rpx;max-width:100%;height:18rpx;margin-top:10rpx}.mentor-center-skeleton-status{min-height:112rpx;padding:25rpx;display:flex;align-items:center;justify-content:space-between;gap:20rpx}.mentor-center-skeleton-status view:first-child{width:210rpx;height:24rpx}.mentor-center-skeleton-status view:last-child{width:76rpx;height:44rpx}.mentor-center-skeleton-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2rpx;overflow:hidden}.mentor-center-skeleton-grid view{height:112rpx;border-radius:0}.mentor-center-skeleton-orders{padding:24rpx}.mentor-center-skeleton-orders>view:nth-child(1){width:126rpx;height:24rpx}.mentor-center-skeleton-orders>view:nth-child(2){width:100%;height:18rpx;margin-top:34rpx}.mentor-center-skeleton-orders>view:nth-child(3){width:68%;height:18rpx;margin-top:14rpx}@keyframes mentorCenterSkeletonShimmer{0%{background-position:100% 0}100%{background-position:-100% 0}}.mentor-center-orders{margin-top:18rpx;padding:24rpx;border:2rpx solid #d9e7fc;border-radius:28rpx;background:rgba(255,255,255,.93);box-shadow:0 14rpx 34rpx rgba(52,120,246,.06);text-align:left}.mentor-center-orders-heading{display:flex;align-items:center;justify-content:space-between;gap:16rpx}.mentor-center-orders-heading strong,.mentor-center-orders-heading text{display:block}.mentor-center-orders-heading strong{color:#40546e;font-size:25rpx;font-weight:900}.mentor-center-orders-heading text{margin-top:6rpx;color:#8796a9;font-size:18rpx;font-weight:650}.mentor-center-orders-heading button{min-width:84rpx;min-height:52rpx;margin:0;padding:0 14rpx;border:0;border-radius:15rpx;background:#edf4ff;color:#4e72aa;font-size:20rpx;font-weight:850}.mentor-center-orders-heading button::after,.mentor-center-order-actions button::after{border:0}.mentor-center-empty{padding:42rpx 12rpx 20rpx;color:#9aa8b9;text-align:center;font-size:21rpx;font-weight:650}.mentor-center-order-card{margin-top:20rpx;padding-top:20rpx;border-top:2rpx solid #edf2f8}.mentor-center-order-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12rpx}.mentor-center-order-head strong,.mentor-center-order-head text{display:block}.mentor-center-order-head strong{color:#3e526f;font-size:23rpx;font-weight:900}.mentor-center-order-head text{margin-top:5rpx;color:#91a0b2;font-size:18rpx;font-weight:650}.mentor-center-order-status{padding:7rpx 10rpx;border-radius:999rpx;background:#edf4ff;color:#4e73aa;font-size:18rpx;line-height:1.2;font-weight:850;white-space:nowrap}.mentor-center-order-status.pending_accept{background:#fff4df;color:#b7791f}.mentor-center-order-status.in_progress{background:#e5f6ec;color:#238a57}.mentor-center-order-status.rejected,.mentor-center-order-status.timeout,.mentor-center-order-status.refunded{background:#fff0ee;color:#cf675e}.mentor-center-order-student{margin-top:16rpx;color:#5d718d;font-size:21rpx;line-height:1.45;font-weight:750}.mentor-center-order-question{margin-top:10rpx;color:#6e7f95;font-size:20rpx;line-height:1.55;font-weight:600}.mentor-center-order-meta{display:flex;align-items:center;justify-content:space-between;gap:16rpx;margin-top:14rpx;color:#8a99ac;font-size:19rpx;font-weight:650}.mentor-center-order-meta strong{color:#31445f;font-size:24rpx;font-weight:900}.mentor-center-order-actions{display:flex;justify-content:flex-end;gap:10rpx;margin-top:18rpx}.mentor-center-order-actions button{min-width:136rpx;min-height:58rpx;margin:0;padding:0 16rpx;border:0;border-radius:16rpx;background:#3478f6;color:#fff;font-size:21rpx;font-weight:850}.mentor-center-order-actions button.light{background:#edf4ff;color:#4d72aa}
.mentor-center-hero-action{cursor:pointer;transition:transform 160ms ease,background 160ms ease}.mentor-center-hero-action:active{transform:scale(.992);background:#f7faff}.mentor-center-hero-arrow{margin:0 0 0 auto!important;color:#8ba6d2!important;display:inline-flex!important;align-items:center;justify-content:center;font-size:42rpx!important;line-height:1!important;font-weight:500}.mentor-center-schedule-button{box-sizing:border-box;position:relative;width:172rpx;height:54rpx;min-width:172rpx;min-height:54rpx;margin:0;padding:0;border:2rpx solid #c9dcfb;border-radius:16rpx;background:#f7faff;color:#4d72a9;display:block;font-size:0;line-height:1;overflow:hidden}.mentor-center-schedule-button:active{transform:scale(.98);background:#edf4ff}.mentor-center-schedule-button-label{position:absolute;inset:0;margin:0;display:flex!important;align-items:center;justify-content:center;color:inherit;font-size:19rpx;line-height:1;font-weight:850;text-align:center;white-space:nowrap;transform:translateY(-2rpx)}
.mentor-apply-center-content{box-sizing:border-box;height:100%;min-height:0;padding:20rpx 24rpx 24rpx;display:flex;flex-direction:column}.mentor-apply-center-content>.mentor-center-hero,.mentor-apply-center-content>.mentor-center-status{flex-shrink:0}.mentor-center-orders{min-height:0;flex:1 1 auto;display:flex;flex-direction:column;overflow:hidden}.mentor-center-orders-heading{flex-shrink:0}.mentor-center-orders-scroll{height:0;min-height:0;flex:1 1 auto;margin-top:18rpx}.mentor-center-orders-list{padding-bottom:4rpx}
@media(max-width:350px){.mentor-apply-content{padding-right:18rpx;padding-left:18rpx}.mentor-apply-card{padding:23rpx}.mentor-proof-image,.mentor-proof-upload{width:126rpx;height:126rpx}}
</style>
