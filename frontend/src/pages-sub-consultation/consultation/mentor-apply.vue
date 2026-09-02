<template>
  <view class="mentor-apply-page" :style="themeInlineStyle">
    <MentorPageHeader :title="pageTitle" @back="goBack" />

    <scroll-view :scroll-y="pageMode !== 'center'" class="mentor-apply-scroll">
      <view v-if="pageMode === 'apply'" class="mentor-apply-content">
        <view v-if="lastRejectionNote" class="mentor-rejection-notice">
          <view class="mentor-rejection-notice-icon" aria-hidden="true">!</view>
          <view class="mentor-rejection-notice-copy">
            <strong>上次认证未通过</strong>
            <text>{{ lastRejectionNote }}</text>
            <small>请根据审核说明修改信息或补充材料后重新提交。</small>
          </view>
        </view>
        <view class="mentor-apply-card">
          <view class="mentor-apply-section-title">认证基本信息</view>
          <view class="mentor-apply-field">
            <view class="mentor-apply-label">真实姓名 <text>后台审核使用</text></view>
            <input v-model="form.realName" maxlength="40" placeholder="请输入真实姓名" placeholder-class="mentor-apply-placeholder" />
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
              <picker mode="selector" :range="admissionYearOptions" :value="admissionYearIndex" @change="selectAdmissionYear">
                <view class="mentor-apply-picker">{{ form.admissionYear }} <text>⌄</text></view>
              </picker>
            </view>
            <view class="mentor-apply-field">
              <view class="mentor-apply-label">毕业年份</view>
              <picker mode="selector" :range="graduationYearOptions" :value="graduationYearIndex" @change="selectGraduationYear">
                <view class="mentor-apply-picker">{{ form.graduationYear }} <text>⌄</text></view>
              </picker>
            </view>
          </view>
          <view class="mentor-apply-two-column">
            <view class="mentor-apply-field">
              <view class="mentor-apply-label">初试成绩</view>
              <view v-if="isApplicationExam" class="mentor-apply-score-na">申请制无需填写</view>
              <input v-else :value="form.score" type="number" min="0" :max="MENTOR_SCORE_MAX" maxlength="3" placeholder="例如 110" placeholder-class="mentor-apply-placeholder" @input="handleScoreInput" />
            </view>
            <view class="mentor-apply-field">
              <view class="mentor-apply-label">考试类别</view>
              <view class="mentor-apply-exam-row">
                <button v-for="item in examOptions" :key="item" :class="{ active: form.examType === item }" @tap="selectExamType(item)">{{ item }}</button>
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
              <button @tap="removeProof(index)"><CloseIcon /></button>
            </view>
            <button v-if="proofImages.length < 3" class="mentor-proof-upload" @tap="chooseProof">
              <text>＋</text><view>上传证明</view>
            </button>
          </view>
        </view>

        <button
          class="mentor-consultation-opt-in"
          :class="{ 'is-selected': form.consultationEnabled }"
          type="button"
          :aria-label="form.consultationEnabled ? '取消同步申请开通前辈咨询服务' : '同步申请开通前辈咨询服务'"
          :aria-pressed="form.consultationEnabled ? 'true' : 'false'"
          :aria-expanded="form.consultationEnabled ? 'true' : 'false'"
          @tap="toggleConsultationEnabled"
        >
          <view class="mentor-consultation-opt-in-copy">
            <strong>是否同步申请开通前辈咨询服务？</strong>
            <text>认证通过后，可在「前辈咨询」频道提供付费咨询服务。</text>
          </view>
          <view class="mentor-consultation-opt-in-check" aria-hidden="true">
            <text v-if="form.consultationEnabled">✓</text>
          </view>
        </button>

        <view
          class="mentor-consultation-fields"
          :class="{ 'is-expanded': form.consultationEnabled }"
          :aria-hidden="form.consultationEnabled ? 'false' : 'true'"
        >
          <view class="mentor-apply-card">
            <view class="mentor-apply-section-title">擅长咨询领域</view>
            <view class="mentor-apply-copy">最多选择 4 项，方便考生更精准地找到你。</view>
            <view class="mentor-skill-options">
              <button
                v-for="item in skillOptions"
                :key="item"
                :class="{ active: form.skills.includes(item) }"
                :disabled="!form.consultationEnabled"
                @tap="toggleSkill(item)"
              >{{ item }}</button>
            </view>
          </view>

          <view class="mentor-apply-card">
            <view class="mentor-apply-label"><text>个人简介</text><text>{{ form.bio.length }} / 500</text></view>
            <textarea
              v-model="form.bio"
              :disabled="!form.consultationEnabled"
              maxlength="500"
              placeholder="介绍你的上岸经历、可提供的帮助和擅长方向。"
              placeholder-class="mentor-apply-placeholder"
            />
            <view class="mentor-apply-price-field">
              <view><strong>咨询价格</strong><text>单次咨询默认开启 60 分钟咨询窗口。</text></view>
              <view class="mentor-price-input"><text>¥</text><input v-model="form.price" :disabled="!form.consultationEnabled" type="number" /><text>/ 次</text></view>
            </view>
          </view>
        </view>
        <view class="mentor-apply-bottom-space"></view>
      </view>

      <view v-else-if="pageMode === 'pending'" class="mentor-apply-status-content">
        <view class="mentor-apply-status-icon pending">
          <image src="/static/ui-icons/png/blue/hourglass.png" mode="aspectFit" aria-hidden="true" />
        </view>
        <view class="mentor-apply-status-title">认证审核中</view>
        <view class="mentor-apply-status-copy">认证资料已提交，平台将在审核后通知结果。审核期间你可以继续使用考研圈的其他功能。</view>
        <view class="mentor-apply-status-card">
          <view><text>申请人</text><strong>{{ maskedApplicationName }}</strong></view>
          <view><text>申请院校</text><strong>{{ form.school || '待审核院校' }}</strong></view>
          <view><text>申请专业</text><strong>{{ form.major || '待审核专业' }}</strong></view>
          <view><text>考试类别</text><strong>{{ form.examType || '待审核类别' }}</strong></view>
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

          <view v-if="mentorProfile.consultationEnabled !== false" class="mentor-center-status">
            <view>
              <strong>{{ mentorProfile.onlineStatus === 'online' ? '在线接单中' : '暂不接即时咨询' }}</strong>
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
                :color="themePrimary"
                @change="handleOnlineStatusChange"
              />
            </view>
          </view>
          <view v-else class="mentor-center-status mentor-center-status-disabled">
            <view>
              <strong>咨询服务暂未开通</strong>
              <text>当前仅展示前辈认证身份，可正常发布经验帖，不会收到新的咨询申请。</text>
            </view>
          </view>

          <view class="mentor-center-orders">
            <view class="mentor-center-orders-heading">
              <view><strong>我的咨询记录</strong></view>
              <button :disabled="mentorOrdersLoading" @tap="loadReceivedOrders">
                <view v-if="mentorOrdersLoading" class="mentor-center-button-spinner" aria-hidden="true"></view>
                <text class="mentor-center-action-label">刷新</text>
              </button>
            </view>

            <scroll-view scroll-y :show-scrollbar="false" class="mentor-center-orders-scroll" @scrolltolower="loadMoreReceivedOrders">
              <view class="mentor-center-orders-list">
                <AppPageLoadingState
                  v-if="mentorOrdersLoading && !mentorOrders.length"
                  compact
                  message="正在整理咨询请求..."
                />
                <AppEmptyState
                  v-else-if="!mentorOrders.length"
                  compact
                  label="暂时没有新的咨询请求"
                  title="暂时没有新的咨询请求"
                />

                <view
                  v-for="order in mentorOrders"
                  :key="order.id"
                  class="mentor-center-order-card"
                  :class="{ 'is-chat-record': canOpenOrderChat(order), 'is-decision-request': order.orderStatus === 'pending_accept', 'has-unread-update': isMentorOrderUnread(order) }"
                  @tap="openMentorOrderCard(order)"
                >
                  <view class="mentor-center-order-head">
                    <view>
                      <strong>{{ getOrderTypeLabel(order) }}</strong>
                      <text>{{ formatOrderTime(order.createdAt) }}</text>
                    </view>
                    <view class="mentor-center-order-badges">
                      <view v-if="isMentorOrderUnread(order)" class="mentor-center-order-unread">新动态</view>
                      <view class="mentor-center-order-status" :class="order.orderStatus">{{ getOrderStatusLabel(order.orderStatus) }}</view>
                    </view>
                  </view>

                  <view class="mentor-center-order-student">
                    {{ order.questionnaire?.name || '匿名同学' }} · {{ order.questionnaire?.school || '未填写学校' }} · {{ order.questionnaire?.major || '未填写专业' }}
                  </view>
                  <view v-if="order.orderStatus === 'pending_accept'" class="mentor-center-order-deadline">请在 {{ getDecisionCountdownText(order) }} 内确认接单或暂不接受</view>
                  <view v-if="order.questionnaire?.question" class="mentor-center-order-question">“{{ order.questionnaire.question }}”</view>
                  <view class="mentor-center-order-meta">
                    <text>{{ order.consultationType === 'booking' ? '预约咨询' : '即时咨询' }}</text>
                    <strong>¥{{ order.price }}</strong>
                  </view>

                  <view v-if="order.orderStatus === 'pending_accept'" class="mentor-center-order-actions">
                    <button :disabled="Boolean(centerActionId)" @tap.stop="openOrderDecision(order)"><text class="mentor-center-action-label">查看资料并处理</text></button>
                  </view>
                  <view v-else-if="['accepted', 'booked', 'in_progress'].includes(order.orderStatus)" class="mentor-center-order-actions">
                    <button
                      v-if="canCancelReceivedOrder(order)"
                      class="light"
                      :disabled="Boolean(centerActionId)"
                      @tap.stop="confirmMentorOrderCancellation(order)"
                    >
                      <view v-if="isCenterActionLoading(order, 'cancel')" class="mentor-center-button-spinner" aria-hidden="true"></view>
                      <text class="mentor-center-action-label">{{ isCenterActionLoading(order, 'cancel') ? '取消中' : '暂时无法服务' }}</text>
                    </button>
                    <button :disabled="Boolean(centerActionId)" @tap.stop="openMentorOrderChat(order)">
                      <view v-if="isCenterActionLoading(order, 'chat')" class="mentor-center-button-spinner" aria-hidden="true"></view>
                      <text class="mentor-center-action-label">{{ isCenterActionLoading(order, 'chat') ? '进入中' : order.orderStatus === 'in_progress' ? '进入咨询' : '开始咨询' }}</text>
                    </button>
                  </view>
                </view>
                <view v-if="mentorOrders.length" class="mentor-center-orders-load-state" @tap="loadMoreReceivedOrders">
                  {{ mentorOrdersLoadingMore ? '正在加载更多…' : mentorOrdersHasMore ? '继续下滑加载更多咨询' : '已加载全部咨询记录' }}
                </view>
              </view>
            </scroll-view>
          </view>
        </template>

        <AppPageLoadingState v-else-if="centerLoading" message="正在整理我的咨询..." />

        <view v-else class="mentor-center-loading">当前账号暂未绑定可用的前辈档案。</view>
      </view>
    </scroll-view>

    <view v-if="pageMode === 'apply'" class="mentor-apply-footer"><button :disabled="submitting" @tap="submitApplication">{{ submitting ? '提交中…' : '提交认证' }}</button></view>

    <view v-if="decisionOrder" class="mentor-order-decision-mask" @tap="closeOrderDecision">
      <view class="mentor-order-decision-sheet" @tap.stop>
        <view class="mentor-order-decision-handle"></view>
        <view class="mentor-order-decision-heading"><view><strong>新的即时咨询</strong><text>请在 {{ getDecisionCountdownText(decisionOrder) }} 内完成处理</text></view><button aria-label="关闭咨询请求" @tap="closeOrderDecision"><CloseIcon /></button></view>
        <view class="mentor-order-decision-section-title">考生填写的信息</view>
        <view class="mentor-order-decision-fields">
          <view><text>姓名 / 称呼</text><strong>{{ decisionOrder.questionnaire?.name || '未填写' }}</strong></view>
          <view><text>当前学校</text><strong>{{ decisionOrder.questionnaire?.school || '未填写' }}</strong></view>
          <view><text>当前专业</text><strong>{{ decisionOrder.questionnaire?.major || '未填写' }}</strong></view>
          <view><text>年级 / 毕业年份</text><strong>{{ decisionOrder.questionnaire?.grade || '未填写' }} · {{ decisionOrder.questionnaire?.graduationYear || '未填写' }}</strong></view>
        </view>
        <view class="mentor-order-decision-question"><text>本次想咨询的问题</text><strong>{{ decisionOrder.questionnaire?.question || '考生暂未填写额外问题。' }}</strong></view>
        <view class="mentor-order-decision-reason"><view><text>暂不接受说明</text><strong>选填，提交后会同步给考生</strong></view><textarea v-model="decisionReason" maxlength="500" placeholder="例如：当前无法在约定时间内提供服务" placeholder-class="mentor-apply-placeholder" /><text>{{ decisionReason.length }} / 500</text></view>
        <view class="mentor-order-decision-actions">
          <button class="light" :disabled="decisionSubmitting" @tap="closeOrderDecision"><text class="mentor-order-decision-label">返回</text></button>
          <button class="reject" :disabled="decisionSubmitting" @tap="submitOrderDecision('reject')">
            <view v-if="decisionSubmitting && decisionAction === 'reject'" class="mentor-order-decision-spinner" aria-hidden="true"></view>
            <text class="mentor-order-decision-label">暂不接受</text>
          </button>
          <button :disabled="decisionSubmitting" @tap="submitOrderDecision('accept')">
            <view v-if="decisionSubmitting && decisionAction === 'accept'" class="mentor-order-decision-spinner" aria-hidden="true"></view>
            <text class="mentor-order-decision-label">确认接单并开始咨询</text>
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import CloseIcon from '../../components/CloseIcon.vue'
import { computed, onBeforeUnmount, ref } from 'vue'
import { onHide, onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import {
  cancelMentorConsultationOrder,
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
  fetchUserNotificationUnreadSummary,
  markUserNotificationReadTarget
} from '../../api/notifications'
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
import { buildThemeStyle, getStoredThemeKey, getThemePreset } from '../../utils/theme'

const pageMode = ref('apply')
const schoolKeyword = ref('')
const proofImages = ref([])
const submitting = ref(false)
const lastRejectionNote = ref('')
const skillOptions = MENTOR_SKILL_OPTIONS
const examOptions = ['Z001', 'Z002', '申请制']
const MENTOR_YEAR_MIN = 2000
const MENTOR_ADMISSION_YEAR_MAX = 2026
const MENTOR_SCORE_MAX = 150
const MENTOR_LEGAL_NAME_MIN_LENGTH = 2
const MENTOR_LEGAL_NAME_MAX_LENGTH = 40
const yearOptionsReferenceDate = ref(new Date())
const admissionYearOptions = buildYearOptions(MENTOR_ADMISSION_YEAR_MAX)
const graduationYearOptions = computed(() => buildYearOptions(getGraduationYearMaximum(yearOptionsReferenceDate.value)))
const form = ref(createDefaultApplication())
const mentorProfile = ref(null)
const mentorOrders = ref([])
const centerLoading = ref(false)
const mentorOrdersLoading = ref(false)
const mentorOrdersLoadingMore = ref(false)
const mentorOrdersNextCursor = ref('')
const mentorOrdersHasMore = ref(false)
const onlineStatusUpdating = ref(false)
const centerActionId = ref('')
const centerActionType = ref('')
const decisionOrder = ref(null)
const decisionReason = ref('')
const decisionAction = ref('')
const notificationOrderId = ref('')
const notificationOrderHandled = ref(false)
const unreadMentorOrderTargets = ref({})
const decisionClock = ref(Date.now())
const entryFromProfile = ref(false)
const entryFromExperiencePublish = ref(false)
const ownerUser = ref(getAuthUser() || {})
const themeKey = ref(getStoredThemeKey())

const MENTOR_CENTER_PROFILE_CACHE_PREFIX = 'circle-mentor-center-profile-v1'
const MENTOR_CENTER_PROFILE_CACHE_MAX_AGE = 7 * 24 * 60 * 60 * 1000
let decisionCountdownTimer = null

const pageTitle = computed(() => pageMode.value === 'pending' ? '认证审核中' : pageMode.value === 'center' ? '我的咨询主页' : '申请成为前辈')
const schoolResults = computed(() => searchMentorSchools(schoolKeyword.value))
const admissionYearIndex = computed(() => getYearOptionIndex(admissionYearOptions, form.value.admissionYear))
const graduationYearIndex = computed(() => getYearOptionIndex(graduationYearOptions.value, form.value.graduationYear))
const isApplicationExam = computed(() => form.value.examType === '申请制')
const maskedApplicationName = computed(() => maskMentorName(form.value.realName || '前辈'))
const mentorCenterAvatarUrl = computed(() => getUserAvatarUrl(ownerUser.value) || mentorProfile.value?.avatarUrl || '')
const themeInlineStyle = computed(() => buildThemeStyle(themeKey.value))
const themePrimary = computed(() => getThemePreset(themeKey.value).primary)
const decisionSubmitting = computed(() => Boolean(decisionOrder.value?.id) && centerActionId.value === decisionOrder.value.id)
let latestUnreadLoadToken = 0

onLoad((options) => {
  entryFromProfile.value = options?.from === 'profile-consultations'
  entryFromExperiencePublish.value = options?.from === 'experience-publish'
  notificationOrderId.value = String(options?.orderId || '')
  void initializePage(options)
})

onShow(() => {
  refreshYearOptions()
  themeKey.value = getStoredThemeKey()
  ownerUser.value = getAuthUser() || {}
  startDecisionCountdown()
  if (pageMode.value === 'center' && mentorProfile.value) {
    void loadUnreadMentorOrderTargets()
    void loadReceivedOrders({ silent: true })
  }
})

async function loadUnreadMentorOrderTargets() {
  const loadToken = ++latestUnreadLoadToken
  try {
    const summary = await fetchUserNotificationUnreadSummary()
    if (loadToken !== latestUnreadLoadToken) return
    const targets = summary?.consultation_order_targets?.mentor
    unreadMentorOrderTargets.value = targets && typeof targets === 'object' && !Array.isArray(targets)
      ? Object.fromEntries(
          Object.entries(targets)
            .map(([id, count]) => [String(id || '').trim(), Math.max(0, Number(count) || 0)])
            .filter(([id, count]) => id && count > 0)
        )
      : {}
  } catch (error) {
    // 未读提示同步失败不应妨碍前辈处理咨询。
  }
}

function isMentorOrderUnread(order = {}) {
  return Number(unreadMentorOrderTargets.value[String(order.id || '')] || 0) > 0
}

function markMentorOrderNotificationsRead(order = {}) {
  const orderId = String(order.id || '').trim()
  if (!orderId) return
  // 已读写入开始后，忽略此前启动的旧摘要响应。
  latestUnreadLoadToken += 1
  const nextTargets = { ...unreadMentorOrderTargets.value }
  delete nextTargets[orderId]
  unreadMentorOrderTargets.value = nextTargets
  void markUserNotificationReadTarget('consultation_order', orderId)
    .then(() => loadUnreadMentorOrderTargets())
    .catch(() => loadUnreadMentorOrderTargets())
}

onHide(stopDecisionCountdown)
onBeforeUnmount(stopDecisionCountdown)

async function initializePage(options) {
  ownerUser.value = getAuthUser() || {}
  lastRejectionNote.value = ''
  const defaultApplication = createDefaultApplication({ consultationEnabled: !entryFromExperiencePublish.value })
  const saved = getMentorApplication()
  if (saved) {
    form.value = { ...defaultApplication, ...saved }
    normalizeApplicationYears()
    normalizeApplicationScore()
    proofImages.value = normalizeProofImages(saved.proofImages)
  } else {
    form.value = defaultApplication
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
  void loadUnreadMentorOrderTargets()
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

function createDefaultApplication({ consultationEnabled = true } = {}) {
  const graduationYear = getGraduationYearMaximum(new Date())
  const admissionYear = Math.min(2025, graduationYear)
  return {
    realName: '', school: '', major: '', admissionYear: String(admissionYear), graduationYear: String(graduationYear), score: '', examType: 'Z001', skills: [], bio: '', price: '39', consultationEnabled: Boolean(consultationEnabled)
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

function buildYearOptions(maxYear) {
  const upperBound = Math.max(MENTOR_YEAR_MIN, Math.trunc(Number(maxYear) || MENTOR_YEAR_MIN))
  return Array.from({ length: upperBound - MENTOR_YEAR_MIN + 1 }, (_, index) => String(upperBound - index))
}

function getGraduationYearMaximum(date = new Date()) {
  const currentDate = date instanceof Date ? date : new Date(date)
  return currentDate.getFullYear() - (currentDate.getMonth() >= 6 ? 0 : 1)
}

function getYearOptionIndex(options, value) {
  const index = options.indexOf(String(value))
  return index >= 0 ? index : 0
}

function getSelectedYear(options, event) {
  return options[Number(event?.detail?.value)] || options[0]
}

function normalizeYearValue(value, options, fallback) {
  const year = Math.trunc(Number(value))
  const latestYear = Number(options[0])
  const earliestYear = Number(options[options.length - 1])
  if (!Number.isFinite(year)) return fallback
  return String(Math.min(latestYear, Math.max(earliestYear, year)))
}

function normalizeApplicationYears() {
  const admissionYear = normalizeYearValue(form.value.admissionYear, admissionYearOptions, admissionYearOptions[0])
  const graduationYear = normalizeYearValue(form.value.graduationYear, graduationYearOptions.value, graduationYearOptions.value[0])
  form.value = { ...form.value, admissionYear, graduationYear }
}

function refreshYearOptions() {
  yearOptionsReferenceDate.value = new Date()
  normalizeApplicationYears()
}

function selectAdmissionYear(event) {
  form.value.admissionYear = getSelectedYear(admissionYearOptions, event)
}

function selectGraduationYear(event) {
  form.value.graduationYear = getSelectedYear(graduationYearOptions.value, event)
}

function normalizeScoreInput(value) {
  const rawValue = String(value ?? '').trim()
  if (!rawValue) return ''
  const score = Number(rawValue)
  return Number.isFinite(score) ? String(Math.min(MENTOR_SCORE_MAX, Math.max(0, Math.trunc(score)))) : ''
}

function handleScoreInput(event) {
  form.value.score = normalizeScoreInput(event?.detail?.value)
}

function normalizeApplicationScore() {
  if (form.value.examType === 'application') form.value.examType = '申请制'
  form.value.score = form.value.examType === '申请制' ? '' : normalizeScoreInput(form.value.score)
}

function selectExamType(examType) {
  form.value.examType = examType
  if (examType === '申请制') form.value.score = ''
}

function toggleSkill(skill) {
  if (!form.value.consultationEnabled) return
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

function toggleConsultationEnabled() {
  form.value.consultationEnabled = !form.value.consultationEnabled
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
    uni.navigateTo({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages-sub-consultation/consultation/mentor-apply')}` })
    return
  }
  const legalName = form.value.realName.trim()
  if (!legalName || !form.value.school.trim() || !form.value.major.trim()) {
    uni.showToast({ title: '请补充真实姓名、录取院校和专业', icon: 'none' })
    return
  }
  const legalNameLength = Array.from(legalName).length
  if (legalNameLength < MENTOR_LEGAL_NAME_MIN_LENGTH || legalNameLength > MENTOR_LEGAL_NAME_MAX_LENGTH) {
    uni.showToast({ title: '真实姓名请填写 2–40 个字', icon: 'none' })
    return
  }
  const applicationExam = isApplicationExam.value
  if (!applicationExam && !String(form.value.score).trim()) {
    uni.showToast({ title: '请填写初试成绩', icon: 'none' })
    return
  }
  const score = applicationExam ? null : Number(form.value.score)
  if (!applicationExam && (!Number.isInteger(score) || score < 0 || score > MENTOR_SCORE_MAX)) {
    uni.showToast({ title: '初试成绩请填写 0–150 分', icon: 'none' })
    return
  }
  if (Number(form.value.graduationYear) < Number(form.value.admissionYear)) {
    uni.showToast({ title: '毕业年份不能早于入学年份', icon: 'none' })
    return
  }
  const consultationEnabled = form.value.consultationEnabled === true
  const price = consultationEnabled ? Number(form.value.price) : 0
  if (consultationEnabled && (!Number.isFinite(price) || price < 0 || price > 1000)) {
    uni.showToast({ title: '请输入正确的咨询价格', icon: 'none' })
    return
  }
  submitting.value = true
  let application = null
  try {
    application = await createMentorVerificationApplication({
      legal_name: legalName,
      school: form.value.school.trim(),
      major: form.value.major.trim(),
      admission_year: Number(form.value.admissionYear),
      graduation_year: form.value.graduationYear ? Number(form.value.graduationYear) : null,
      exam_type: applicationExam ? 'application' : form.value.examType,
      score,
      skills: consultationEnabled ? form.value.skills : [],
      bio: consultationEnabled ? form.value.bio.trim() : '',
      price_cents: consultationEnabled ? Math.round(price * 100) : 0,
      consultation_enabled: consultationEnabled
    })
  } catch (error) {
    uni.showToast({ title: error?.detail || '申请创建失败，请稍后重试', icon: 'none' })
    submitting.value = false
    return
  }

  try {
    saveMentorApplication({ ...form.value, proofImages: proofImages.value.map((item) => item.path) })
    setMentorVerificationStatus('pending')
    lastRejectionNote.value = ''
    pageMode.value = 'pending'

    const uploadFailures = []
    for (const [index, proof] of proofImages.value.entries()) {
      try {
        await uploadMentorVerificationDocument(application.id, proof)
      } catch (error) {
        uploadFailures.push({ index, error })
      }
    }

    if (uploadFailures.length) {
      const uploadedCount = proofImages.value.length - uploadFailures.length
      const uploadSummary = uploadedCount > 0
        ? `已成功上传 ${uploadedCount} 份，另有 ${uploadFailures.length} 份上传失败。`
        : `${uploadFailures.length} 份证明材料均未上传成功。`
      uni.showModal({
        title: '申请已提交',
        content: `认证申请已进入审核，${uploadSummary}平台会在材料不足时通知你补充。`,
        showCancel: false,
        confirmText: '知道了'
      })
      return
    }

    uni.showToast({ title: '申请已提交，等待审核', icon: 'success' })
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
  const consultationEnabled = application.consultation_enabled ?? application.consultationEnabled
  const resolvedConsultationEnabled = consultationEnabled == null
    ? form.value.consultationEnabled
    : Boolean(consultationEnabled)
  form.value = {
    ...createDefaultApplication(),
    realName: application.legal_name || '',
    school: application.school || '',
    major: application.major || '',
    admissionYear: String(application.admission_year || ''),
    graduationYear: application.graduation_year ? String(application.graduation_year) : '',
    score: String(application.score ?? ''),
    examType: application.exam_type === 'application' ? '申请制' : application.exam_type || 'Z001',
    skills: resolvedConsultationEnabled && Array.isArray(application.skills) ? application.skills : form.value.skills,
    bio: resolvedConsultationEnabled ? (application.bio || '') : form.value.bio,
    price: resolvedConsultationEnabled ? String(application.price ?? 39) : form.value.price,
    consultationEnabled: resolvedConsultationEnabled
  }
  normalizeApplicationYears()
  normalizeApplicationScore()
  schoolKeyword.value = form.value.school
  const status = application.application_status === 'approved' ? 'verified' : application.application_status === 'pending' ? 'pending' : 'rejected'
  const adminNote = String(application.admin_note || '').trim()
  lastRejectionNote.value = status === 'rejected'
    ? (adminNote || '原审核记录未填写具体理由，请核对认证信息和证明材料后重新提交。')
    : ''
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
  normalizeApplicationYears()
  normalizeApplicationScore()
  schoolKeyword.value = form.value.school
}

async function loadReceivedOrders({ silent = false } = {}) {
  if (mentorOrdersLoading.value || mentorOrdersLoadingMore.value) return
  mentorOrdersLoading.value = true
  mentorOrdersNextCursor.value = ''
  mentorOrdersHasMore.value = false
  try {
    const payload = await fetchMyReceivedMentorOrders({ limit: 20 })
    mentorOrders.value = (Array.isArray(payload?.items) ? payload.items : [])
      .map((order) => normalizeMentorConsultationOrder(order))
    mentorOrdersNextCursor.value = String(payload?.next_cursor || '')
    mentorOrdersHasMore.value = payload?.has_more === true
    openNotificationOrderIfNeeded()
  } catch (error) {
    if (!silent) uni.showToast({ title: error?.detail || '咨询请求加载失败', icon: 'none' })
  } finally {
    mentorOrdersLoading.value = false
  }
}

async function loadMoreReceivedOrders() {
  if (mentorOrdersLoading.value || mentorOrdersLoadingMore.value || !mentorOrdersHasMore.value || !mentorOrdersNextCursor.value) return
  mentorOrdersLoadingMore.value = true
  try {
    const payload = await fetchMyReceivedMentorOrders({ limit: 20, cursor: mentorOrdersNextCursor.value })
    const nextOrders = (Array.isArray(payload?.items) ? payload.items : [])
      .map((order) => normalizeMentorConsultationOrder(order))
    mentorOrders.value = [
      ...mentorOrders.value,
      ...nextOrders.filter((item) => !mentorOrders.value.some((existing) => existing.id === item.id))
    ]
    mentorOrdersNextCursor.value = String(payload?.next_cursor || '')
    mentorOrdersHasMore.value = payload?.has_more === true
  } catch (error) {
    uni.showToast({ title: error?.detail || '更多咨询记录加载失败', icon: 'none' })
  } finally {
    mentorOrdersLoadingMore.value = false
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

async function handleOrderDecision(order, decision, reason = '') {
  if (!order?.id || centerActionId.value) return
  centerActionId.value = order.id
  centerActionType.value = 'decision'
  try {
    const updated = normalizeMentorConsultationOrder(await decideMentorConsultationOrder(order.id, decision, reason))
    mentorOrders.value = mentorOrders.value.map((item) => item.id === updated.id ? updated : item)
    uni.showToast({ title: decision === 'accept' ? '已确认接单，咨询已开始' : '已通知考生本次暂不接受', icon: 'none' })
    return updated
  } catch (error) {
    uni.showToast({ title: error?.detail || '处理咨询请求失败', icon: 'none' })
    return null
  } finally {
    centerActionId.value = ''
    centerActionType.value = ''
  }
}

function openNotificationOrderIfNeeded() {
  if (!notificationOrderId.value || notificationOrderHandled.value || decisionOrder.value) return
  const order = mentorOrders.value.find((item) => item.id === notificationOrderId.value)
  if (!order) return
  notificationOrderHandled.value = true
  if (order.orderStatus === 'pending_accept') openOrderDecision(order)
}

function openOrderDecision(order) {
  if (!order?.id || order.orderStatus !== 'pending_accept' || centerActionId.value) return
  markMentorOrderNotificationsRead(order)
  decisionOrder.value = order
  decisionReason.value = ''
  decisionAction.value = ''
}

function closeOrderDecision() {
  if (decisionSubmitting.value) return
  decisionOrder.value = null
  decisionReason.value = ''
  decisionAction.value = ''
}

async function submitOrderDecision(decision) {
  const order = decisionOrder.value
  if (!order?.id || decisionSubmitting.value) return
  decisionAction.value = decision
  try {
    const updated = await handleOrderDecision(order, decision, decision === 'reject' ? decisionReason.value : '')
    if (!updated) return
    closeOrderDecision()
    if (decision === 'accept' && updated.orderStatus === 'in_progress') {
      await openMentorOrderChat(updated)
    }
  } finally {
    decisionAction.value = ''
  }
}

function confirmMentorOrderCancellation(order) {
  if (!canCancelReceivedOrder(order) || centerActionId.value) return
  uni.showModal({
    title: '取消本次服务？',
    content: order.consultationType === 'booking'
      ? '取消后会释放该预约时段，平台会同步为考生处理退款，并保留本次订单记录。'
      : '取消后平台会同步为考生处理退款，并保留本次订单记录。',
    confirmText: '确认取消',
    confirmColor: '#d66b61',
    success(result) {
      if (result.confirm) void cancelReceivedMentorOrder(order)
    }
  })
}

async function cancelReceivedMentorOrder(order) {
  if (!canCancelReceivedOrder(order) || centerActionId.value) return
  centerActionId.value = order.id
  centerActionType.value = 'cancel'
  try {
    const updated = normalizeMentorConsultationOrder(await cancelMentorConsultationOrder(order.id))
    mentorOrders.value = mentorOrders.value.map((item) => item.id === updated.id ? updated : item)
    uni.showToast({ title: '已取消，平台将同步处理退款', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '取消服务失败，请稍后重试', icon: 'none' })
  } finally {
    centerActionId.value = ''
    centerActionType.value = ''
  }
}

async function openMentorOrderChat(order) {
  markMentorOrderNotificationsRead(order)
  if (!order?.id || !mentorProfile.value || centerActionId.value || !canEnterOrderService(order)) return
  centerActionId.value = order.id
  centerActionType.value = 'chat'
  try {
    let activeOrder = order
    if (['accepted', 'booked'].includes(order.orderStatus)) {
      activeOrder = normalizeMentorConsultationOrder(await startMentorConsultationOrder(order.id))
      mentorOrders.value = mentorOrders.value.map((item) => item.id === activeOrder.id ? activeOrder : item)
    }
    uni.navigateTo({
      url: `/pages-sub-consultation/consultation/mentor-chat?mentorId=${encodeURIComponent(mentorProfile.value.id)}&orderId=${encodeURIComponent(activeOrder.id)}&role=mentor&from=mentor-center`
    })
  } catch (error) {
    uni.showToast({ title: error?.detail || '暂时无法进入咨询', icon: 'none' })
  } finally {
    centerActionId.value = ''
    centerActionType.value = ''
  }
}

function isCenterActionLoading(order, actionType) {
  return centerActionId.value === order?.id && centerActionType.value === actionType
}

function openMentorSchedule() {
  uni.navigateTo({ url: '/pages-sub-consultation/consultation/mentor-schedule' })
}

function openMentorInfo() {
  uni.navigateTo({ url: '/pages-sub-consultation/consultation/mentor-info' })
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

function canOpenOrderChat(order = {}) {
  return ['in_progress', 'completed'].includes(order.orderStatus)
}

function canEnterOrderService(order = {}) {
  return ['accepted', 'booked', 'in_progress', 'completed'].includes(order.orderStatus)
}

function canCancelReceivedOrder(order = {}) {
  return ['accepted', 'booked'].includes(order.orderStatus)
}

function openMentorOrderCard(order) {
  markMentorOrderNotificationsRead(order)
  if (order?.orderStatus === 'pending_accept') {
    openOrderDecision(order)
    return
  }
  if (canOpenOrderChat(order)) void openMentorOrderChat(order)
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

function getDecisionCountdownText(order = {}) {
  const deadline = Date.parse(String(order?.expiresAt || ''))
  if (!Number.isFinite(deadline)) return '10 分钟'
  const seconds = Math.max(0, Math.ceil((deadline - decisionClock.value) / 1000))
  if (!seconds) return '即将超时'
  const minutes = String(Math.floor(seconds / 60)).padStart(2, '0')
  return `${minutes}:${String(seconds % 60).padStart(2, '0')}`
}

function startDecisionCountdown() {
  if (decisionCountdownTimer) return
  decisionClock.value = Date.now()
  decisionCountdownTimer = setInterval(() => {
    decisionClock.value = Date.now()
  }, 1000)
}

function stopDecisionCountdown() {
  if (decisionCountdownTimer) clearInterval(decisionCountdownTimer)
  decisionCountdownTimer = null
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
  const fallbackUrl = entryFromProfile.value
    ? '/pages/home/index?tab=profile'
    : '/pages/home/index?tab=circle&section=community&communityTab=mentor'
  uni.navigateBack({ fail() { uni.reLaunch({ url: fallbackUrl }) } })
}
</script>

<style scoped>
.mentor-apply-page{height:100vh;overflow:hidden;background:#f4f8ff;display:flex;flex-direction:column}.mentor-apply-scroll{min-height:0;flex:1}.mentor-apply-content{padding:24rpx 24rpx 0}
.mentor-apply-card{margin-top:18rpx;padding:28rpx;border:2rpx solid #d9e7fc;border-radius:28rpx;background:rgba(255,255,255,.93);box-shadow:0 14rpx 34rpx rgba(52,120,246,.06)}.mentor-apply-section-title{color:#273953;font-size:28rpx;font-weight:900}.mentor-apply-field{margin-top:23rpx}.mentor-apply-label{display:flex;align-items:center;justify-content:space-between;gap:10rpx;margin-bottom:12rpx;color:#40546e;font-size:23rpx;line-height:1.25;font-weight:850}.mentor-apply-label>text:last-child{color:#98a9c0;font-size:18rpx;font-weight:650}.mentor-apply-label>text:first-child{color:inherit;font-size:inherit;font-weight:inherit}.mentor-apply-label>text{color:inherit;display:inline;font-weight:inherit}.mentor-apply-label>text+text{color:#98a9c0;font-size:18rpx}.mentor-apply-label > text:last-child{font-weight:650}
.mentor-apply-field input,.mentor-apply-picker{box-sizing:border-box;width:100%;height:72rpx;padding:0 18rpx;border:2rpx solid #e0eafa;border-radius:18rpx;background:#fbfdff;color:#2d405d;font-size:23rpx;line-height:68rpx;font-weight:650}.mentor-apply-placeholder{color:#a7b3c4;font-weight:500}.mentor-apply-tip{margin-top:8rpx;color:#91a0b4;font-size:18rpx;line-height:1.4;font-weight:600}.mentor-apply-search-results{display:flex;flex-wrap:wrap;gap:9rpx;margin-top:11rpx}.mentor-apply-search-results button,.mentor-apply-exam-row button,.mentor-skill-options button{min-height:48rpx;margin:0;padding:0 14rpx;border:2rpx solid #dce7f8;border-radius:14rpx;background:#fbfdff;color:#708199;font-size:20rpx;font-weight:750}.mentor-apply-search-results button::after,.mentor-apply-exam-row button::after,.mentor-skill-options button::after,.mentor-proof-image button::after,.mentor-proof-upload::after,.mentor-apply-footer button::after,.mentor-apply-demo-card button::after{border:0}.mentor-apply-two-column{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:16rpx}.mentor-apply-picker{display:flex;align-items:center;justify-content:space-between;line-height:1.2}.mentor-apply-picker text{color:#8494a9;font-size:24rpx}.mentor-apply-exam-row{display:flex;flex-wrap:wrap;gap:8rpx}.mentor-apply-exam-row button{min-width:70rpx}.mentor-apply-exam-row button.active,.mentor-skill-options button.active{border-color:#b9d2ff;background:#edf4ff;color:#3478f6}.mentor-apply-copy{margin-top:10rpx;color:#7e8ea4;font-size:20rpx;line-height:1.55;font-weight:650}.mentor-proof-grid{display:flex;flex-wrap:wrap;gap:12rpx;margin-top:20rpx}.mentor-proof-image,.mentor-proof-upload{width:140rpx;height:140rpx;border-radius:18rpx;overflow:hidden;position:relative}.mentor-proof-image{border:2rpx solid #d8e6fa}.mentor-proof-image image{width:100%;height:100%}.mentor-proof-image button{position:absolute;top:6rpx;right:6rpx;width:34rpx;height:34rpx;min-height:34rpx;margin:0;padding:0;border:0;border-radius:50%;background:rgba(27,42,66,.62);color:#fff;font-size:26rpx;line-height:1}.mentor-proof-upload{margin:0;border:2rpx dashed #bed4f7;background:#f7faff;color:#6180b4;display:flex;flex-direction:column;align-items:center;justify-content:center;font-size:20rpx;font-weight:750}.mentor-proof-upload>text{font-size:42rpx;line-height:1}.mentor-proof-upload view{margin-top:7rpx;font-size:18rpx}.mentor-skill-options{display:flex;flex-wrap:wrap;gap:10rpx;margin-top:18rpx}.mentor-apply-card textarea{box-sizing:border-box;width:100%;min-height:178rpx;padding:16rpx;border:2rpx solid #e0eafa;border-radius:18rpx;background:#fbfdff;color:#3a4f6e;font-size:22rpx;line-height:1.5}.mentor-apply-price-field{margin-top:24rpx;padding-top:20rpx;border-top:2rpx solid #edf1f8;display:flex;align-items:center;justify-content:space-between;gap:18rpx}.mentor-apply-price-field strong,.mentor-apply-price-field text{display:block}.mentor-apply-price-field strong{color:#40546e;font-size:23rpx;font-weight:900}.mentor-apply-price-field text{margin-top:6rpx;color:#8d9bb0;font-size:18rpx;line-height:1.35;font-weight:650}.mentor-price-input{display:flex;align-items:center;gap:5rpx;border:2rpx solid #d9e7fa;border-radius:16rpx;background:#fbfdff;color:#3478f6;padding:0 12rpx;flex-shrink:0}.mentor-price-input input{width:58rpx;height:58rpx;padding:0;border:0;background:transparent;color:#2d405d;text-align:center;font-size:25rpx;font-weight:900}.mentor-price-input text{margin:0;color:#5e78a3;font-size:20rpx;font-weight:800}.mentor-apply-bottom-space{height:calc(136rpx + env(safe-area-inset-bottom))}.mentor-apply-footer{padding:16rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));border-top:2rpx solid #dbe7f8;background:rgba(255,255,255,.97)}.mentor-apply-footer button{width:100%;min-height:76rpx;margin:0;border:0;border-radius:20rpx;background:#3478f6;color:#fff;font-size:24rpx;font-weight:900;box-shadow:0 10rpx 22rpx rgba(52,120,246,.2)}
.mentor-apply-status-content,.mentor-apply-center-content{padding:84rpx 24rpx 50rpx;text-align:center}.mentor-apply-status-icon{width:100rpx;height:100rpx;margin:0 auto;border-radius:50%;background:#edf4ff;color:#3478f6;display:flex;align-items:center;justify-content:center;font-size:45rpx;font-weight:900}.mentor-apply-status-icon image{display:block;width:54rpx;height:54rpx}.mentor-apply-status-title{margin-top:22rpx;color:#283b56;font-size:32rpx;font-weight:900}.mentor-apply-status-copy{max-width:560rpx;margin:14rpx auto 0;color:#7d8ea6;font-size:22rpx;line-height:1.6;font-weight:650}.mentor-apply-status-card,.mentor-apply-demo-card{margin-top:32rpx;padding:26rpx;border:2rpx solid #d9e7fc;border-radius:26rpx;background:rgba(255,255,255,.93);text-align:left;box-shadow:0 14rpx 34rpx rgba(52,120,246,.06)}.mentor-apply-status-card>view{display:flex;align-items:center;justify-content:space-between;gap:20rpx;color:#8796a9;font-size:21rpx;font-weight:650}.mentor-apply-status-card>view+view{margin-top:18rpx}.mentor-apply-status-card strong{color:#40546d;font-weight:850}.mentor-apply-status-card strong.green{color:#278d58}.mentor-apply-demo-card strong,.mentor-apply-demo-card text{display:block}.mentor-apply-demo-card strong{color:#48648e;font-size:24rpx;font-weight:900}.mentor-apply-demo-card text{margin-top:8rpx;color:#8291a5;font-size:20rpx;line-height:1.5;font-weight:650}.mentor-apply-demo-card button{min-height:60rpx;margin:18rpx 0 0;padding:0 20rpx;border:0;border-radius:17rpx;background:#3478f6;color:#fff;font-size:21rpx;font-weight:850}
.mentor-center-hero,.mentor-center-status,.mentor-center-grid,.mentor-center-reserve{border:2rpx solid #d9e7fc;border-radius:28rpx;background:rgba(255,255,255,.93);box-shadow:0 14rpx 34rpx rgba(52,120,246,.06)}.mentor-center-hero{padding:28rpx;display:flex;align-items:center;gap:16rpx;text-align:left}.mentor-center-avatar{width:78rpx;height:78rpx;border-radius:50%;background:#e6efff;color:#3478f6;display:flex;align-items:center;justify-content:center;font-size:30rpx;font-weight:900;flex-shrink:0}.mentor-center-hero strong,.mentor-center-hero text,.mentor-center-hero view{display:block}.mentor-center-hero strong{color:#273a55;font-size:28rpx;font-weight:900}.mentor-center-hero text{margin-top:6rpx;color:#3478f6;font-size:19rpx;font-weight:800}.mentor-center-hero view{margin-top:6rpx;color:#7c8ca2;font-size:20rpx;font-weight:650}.mentor-center-status{margin-top:18rpx;padding:25rpx;display:flex;align-items:center;justify-content:space-between;gap:20rpx;text-align:left}.mentor-center-status strong,.mentor-center-status text{display:block}.mentor-center-status strong{color:#40546e;font-size:24rpx;font-weight:900}.mentor-center-status text{margin-top:6rpx;color:#8391a6;font-size:19rpx;line-height:1.4;font-weight:650}.mentor-center-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2rpx;margin-top:18rpx;overflow:hidden}.mentor-center-grid>view{padding:26rpx;border:1rpx solid #edf2f8;text-align:left}.mentor-center-grid text,.mentor-center-grid strong{display:block}.mentor-center-grid text{color:#8a98ab;font-size:19rpx;font-weight:650}.mentor-center-grid strong{margin-top:9rpx;color:#41546e;font-size:23rpx;font-weight:900}.mentor-center-reserve{margin-top:18rpx;padding:26rpx;text-align:left}.mentor-center-reserve strong,.mentor-center-reserve text{display:block}.mentor-center-reserve strong{color:#46618c;font-size:24rpx;font-weight:900}.mentor-center-reserve text{margin-top:9rpx;color:#8090a6;font-size:20rpx;line-height:1.55;font-weight:650}
.mentor-apply-exam-row{flex-wrap:nowrap}.mentor-apply-exam-row button{flex:1;min-width:0;min-height:72rpx;height:72rpx;padding:0;border-radius:18rpx;font-size:23rpx;line-height:68rpx;white-space:nowrap}
.mentor-center-avatar{overflow:hidden}.mentor-center-avatar image{width:100%;height:100%}.mentor-center-avatar.tone-mint{background:#e2f4ef;color:#198777}.mentor-center-avatar.tone-violet{background:#eeeafe;color:#7162bd}.mentor-center-avatar.tone-warm{background:#f9eee1;color:#b66c32}
.mentor-apply-center-content{padding:20rpx 24rpx 50rpx}.mentor-center-status-actions{display:flex;align-items:center;justify-content:flex-end;gap:14rpx;flex-shrink:0}.mentor-center-schedule-button{min-width:156rpx;min-height:54rpx;margin:0;padding:0 14rpx;border:2rpx solid #c9dcfb;border-radius:16rpx;background:#f7faff;color:#4d72a9;font-size:19rpx;line-height:1.2;font-weight:850;white-space:nowrap}.mentor-center-schedule-button::after{border:0}
.mentor-center-loading{padding:70rpx 30rpx;color:#7d8ea6;font-size:23rpx;font-weight:700}.mentor-center-skeleton{display:grid;gap:18rpx}.mentor-center-skeleton-hero,.mentor-center-skeleton-status,.mentor-center-skeleton-grid,.mentor-center-skeleton-orders{border:2rpx solid #d9e7fc;border-radius:28rpx;background:rgba(255,255,255,.93);box-shadow:0 14rpx 34rpx rgba(52,120,246,.04)}.mentor-center-skeleton-hero{display:flex;align-items:center;gap:16rpx;padding:28rpx}.mentor-center-skeleton-avatar,.mentor-center-skeleton-copy view,.mentor-center-skeleton-status view,.mentor-center-skeleton-grid view,.mentor-center-skeleton-orders>view{border-radius:999rpx;background:linear-gradient(90deg,#edf3fc 20%,#f8fbff 38%,#edf3fc 58%);background-size:220% 100%;animation:mentorCenterSkeletonShimmer 1.45s ease-in-out infinite}.mentor-center-skeleton-avatar{width:78rpx;height:78rpx;border-radius:50%;flex-shrink:0}.mentor-center-skeleton-copy{flex:1}.mentor-center-skeleton-copy view:nth-child(1){width:122rpx;height:25rpx}.mentor-center-skeleton-copy view:nth-child(2){width:160rpx;height:18rpx;margin-top:12rpx}.mentor-center-skeleton-copy view:nth-child(3){width:220rpx;max-width:100%;height:18rpx;margin-top:10rpx}.mentor-center-skeleton-status{min-height:112rpx;padding:25rpx;display:flex;align-items:center;justify-content:space-between;gap:20rpx}.mentor-center-skeleton-status view:first-child{width:210rpx;height:24rpx}.mentor-center-skeleton-status view:last-child{width:76rpx;height:44rpx}.mentor-center-skeleton-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:2rpx;overflow:hidden}.mentor-center-skeleton-grid view{height:112rpx;border-radius:0}.mentor-center-skeleton-orders{padding:24rpx}.mentor-center-skeleton-orders>view:nth-child(1){width:126rpx;height:24rpx}.mentor-center-skeleton-orders>view:nth-child(2){width:100%;height:18rpx;margin-top:34rpx}.mentor-center-skeleton-orders>view:nth-child(3){width:68%;height:18rpx;margin-top:14rpx}@keyframes mentorCenterSkeletonShimmer{0%{background-position:100% 0}100%{background-position:-100% 0}}.mentor-center-orders{margin-top:18rpx;padding:24rpx;border:2rpx solid #d9e7fc;border-radius:28rpx;background:rgba(255,255,255,.93);box-shadow:0 14rpx 34rpx rgba(52,120,246,.06);text-align:left}.mentor-center-orders-heading{display:flex;align-items:center;justify-content:space-between;gap:16rpx}.mentor-center-orders-heading strong,.mentor-center-orders-heading text{display:block}.mentor-center-orders-heading strong{color:#40546e;font-size:25rpx;font-weight:900}.mentor-center-orders-heading text{margin-top:6rpx;color:#8796a9;font-size:18rpx;font-weight:650}.mentor-center-orders-heading button{min-width:84rpx;min-height:52rpx;margin:0;padding:0 14rpx;border:0;border-radius:15rpx;background:#edf4ff;color:#4e72aa;font-size:20rpx;font-weight:850}.mentor-center-orders-heading button::after,.mentor-center-order-actions button::after{border:0}.mentor-center-empty{padding:42rpx 12rpx 20rpx;color:#9aa8b9;text-align:center;font-size:21rpx;font-weight:650}.mentor-center-order-card{margin-top:20rpx;padding-top:20rpx;border-top:2rpx solid #edf2f8}.mentor-center-order-head{display:flex;align-items:flex-start;justify-content:space-between;gap:12rpx}.mentor-center-order-head strong,.mentor-center-order-head text{display:block}.mentor-center-order-head strong{color:#3e526f;font-size:23rpx;font-weight:900}.mentor-center-order-head text{margin-top:5rpx;color:#91a0b2;font-size:18rpx;font-weight:650}.mentor-center-order-status{padding:7rpx 10rpx;border-radius:999rpx;background:#edf4ff;color:#4e73aa;font-size:18rpx;line-height:1.2;font-weight:850;white-space:nowrap}.mentor-center-order-status.pending_accept{background:#fff4df;color:#b7791f}.mentor-center-order-status.in_progress{background:#e5f6ec;color:#238a57}.mentor-center-order-status.rejected,.mentor-center-order-status.timeout,.mentor-center-order-status.refunded{background:#fff0ee;color:#cf675e}.mentor-center-order-student{margin-top:16rpx;color:#5d718d;font-size:21rpx;line-height:1.45;font-weight:750}.mentor-center-order-question{margin-top:10rpx;color:#6e7f95;font-size:20rpx;line-height:1.55;font-weight:600}.mentor-center-order-meta{display:flex;align-items:center;justify-content:space-between;gap:16rpx;margin-top:14rpx;color:#8a99ac;font-size:19rpx;font-weight:650}.mentor-center-order-meta strong{color:#31445f;font-size:24rpx;font-weight:900}.mentor-center-order-actions{display:flex;justify-content:flex-end;gap:10rpx;margin-top:18rpx}.mentor-center-order-actions button{min-width:136rpx;min-height:58rpx;margin:0;padding:0 16rpx;border:0;border-radius:16rpx;background:#3478f6;color:#fff;font-size:21rpx;font-weight:850}.mentor-center-order-actions button.light{background:#edf4ff;color:#4d72aa}
.mentor-center-hero-action{cursor:pointer;transition:transform 160ms ease,background 160ms ease}.mentor-center-hero-action:active{transform:scale(.992);background:#f7faff}.mentor-center-hero-arrow{margin:0 0 0 auto!important;color:#8ba6d2!important;display:inline-flex!important;align-items:center;justify-content:center;font-size:42rpx!important;line-height:1!important;font-weight:500}.mentor-center-schedule-button{box-sizing:border-box;position:relative;width:172rpx;height:54rpx;min-width:172rpx;min-height:54rpx;margin:0;padding:0;border:2rpx solid #c9dcfb;border-radius:16rpx;background:#f7faff;color:#4d72a9;display:block;font-size:0;line-height:1;overflow:hidden}.mentor-center-schedule-button:active{transform:scale(.98);background:#edf4ff}.mentor-center-schedule-button-label{position:absolute;inset:0;margin:0;display:flex!important;align-items:center;justify-content:center;color:inherit;font-size:19rpx;line-height:1;font-weight:850;text-align:center;white-space:nowrap;transform:translateY(-2rpx)}
.mentor-apply-center-content{box-sizing:border-box;height:100%;min-height:0;padding:20rpx 24rpx 24rpx;display:flex;flex-direction:column}.mentor-apply-center-content>.mentor-center-hero,.mentor-apply-center-content>.mentor-center-status{flex-shrink:0}.mentor-center-orders{min-height:0;flex:1 1 auto;display:flex;flex-direction:column;overflow:hidden}.mentor-center-orders-heading{flex-shrink:0}.mentor-center-orders-scroll{height:0;min-height:0;flex:1 1 auto;margin-top:18rpx}.mentor-center-orders-list{padding-bottom:4rpx}
.mentor-center-orders-load-state{padding:24rpx 0 8rpx;color:#8a9ab0;font-size:18rpx;line-height:1.4;font-weight:750;text-align:center}
@media(max-width:350px){.mentor-apply-content{padding-right:18rpx;padding-left:18rpx}.mentor-apply-card{padding:23rpx}.mentor-proof-image,.mentor-proof-upload{width:126rpx;height:126rpx}}
.mentor-center-order-card.is-chat-record{cursor:pointer;transition:transform 160ms ease,background 160ms ease}
.mentor-center-order-card.is-chat-record:active{transform:scale(.992);background:#f8fbff}
.mentor-center-status strong,.mentor-center-orders-heading strong{font-size:28rpx;line-height:1.25}

/* Apply the selected appearance to the verification flow and mentor workspace. */
.mentor-apply-page{background:var(--gyt-page-bg)}
.mentor-apply-card,.mentor-apply-status-card,.mentor-apply-demo-card,.mentor-center-hero,.mentor-center-status,.mentor-center-grid,.mentor-center-reserve,.mentor-center-skeleton-hero,.mentor-center-skeleton-status,.mentor-center-skeleton-grid,.mentor-center-skeleton-orders,.mentor-center-orders{border-color:var(--gyt-primary-border,#d9e7fc);background:var(--gyt-panel-bg,#ffffff);box-shadow:0 14rpx 34rpx var(--gyt-primary-shadow,rgba(52,120,246,.06))}
.mentor-apply-card input,.mentor-apply-card textarea,.mentor-apply-picker,.mentor-price-input{border-color:var(--gyt-primary-border,#d9e7fa);background:var(--gyt-primary-tint,#fbfdff)}
.mentor-apply-exam-row button.active,.mentor-skill-options button.active{border-color:var(--gyt-primary,#3478f6);background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6)}
.mentor-proof-upload{border-color:var(--gyt-primary-border,#d9e7fa);background:var(--gyt-primary-tint,#fbfdff);color:var(--gyt-primary,#3478f6)}
.mentor-price-input{color:var(--gyt-primary,#3478f6)}
.mentor-apply-footer{border-color:var(--gyt-primary-border,#dbe7f8);background:var(--gyt-primary-tint,#ffffff)}
.mentor-apply-footer button,.mentor-apply-demo-card button,.mentor-center-order-actions button{background:var(--gyt-primary-gradient,#3478f6);box-shadow:0 10rpx 22rpx var(--gyt-primary-shadow,rgba(52,120,246,.2))}
.mentor-apply-status-icon,.mentor-center-avatar.tone-blue{background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6)}
.mentor-center-hero text,.mentor-center-hero-arrow{color:var(--gyt-primary,#3478f6)!important}
.mentor-center-schedule-button{border-color:var(--gyt-primary-border,#c9dcfb);background:var(--gyt-primary-tint,#f7faff);color:var(--gyt-primary,#3478f6)}
.mentor-center-orders-heading button,.mentor-center-order-actions button.light{background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6)}
.mentor-center-order-status{background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6)}
.mentor-center-order-card.is-chat-record:active{background:var(--gyt-primary-tint,#f8fbff)}
.mentor-center-order-badges{flex:0 0 auto;display:flex;align-items:center;gap:8rpx}.mentor-center-order-unread{padding:7rpx 10rpx;border-radius:999rpx;background:rgba(242,85,85,.1);color:#d94b4b;font-size:17rpx;line-height:1;font-weight:900;white-space:nowrap}.mentor-center-order-card.has-unread-update:not(.is-decision-request){padding-right:12rpx;padding-left:12rpx;background:rgba(255,252,252,.72)}
.mentor-center-skeleton-avatar,.mentor-center-skeleton-copy view,.mentor-center-skeleton-status view,.mentor-center-skeleton-grid view,.mentor-center-skeleton-orders>view{background:linear-gradient(90deg,var(--gyt-primary-soft,#edf3fc) 20%,var(--gyt-primary-tint,#f8fbff) 38%,var(--gyt-primary-soft,#edf3fc) 58%)}
.mentor-center-order-card.is-decision-request{padding:20rpx;border:2rpx solid var(--gyt-primary-border,#d9e7fc);border-radius:22rpx;background:var(--gyt-primary-tint,#f8fbff)}
.mentor-center-order-card.is-decision-request+.mentor-center-order-card{margin-top:18rpx}
.mentor-center-order-deadline{margin-top:12rpx;color:#a9792e;font-size:19rpx;line-height:1.45;font-weight:800}
.mentor-order-decision-mask{position:fixed;z-index:1000;inset:0;padding:30rpx 20rpx calc(20rpx + env(safe-area-inset-bottom));display:flex;align-items:flex-end;background:rgba(21,38,68,.38);box-sizing:border-box}
.mentor-order-decision-sheet{width:100%;max-height:94%;overflow:auto;padding:22rpx 24rpx 26rpx;border-radius:32rpx;background:var(--gyt-panel-bg,#fff);box-shadow:0 -18rpx 50rpx rgba(24,48,88,.2);box-sizing:border-box}
.mentor-order-decision-handle{width:66rpx;height:7rpx;margin:0 auto 22rpx;border-radius:999rpx;background:#dce6f4}
.mentor-order-decision-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:20rpx}.mentor-order-decision-heading strong,.mentor-order-decision-heading text{display:block}.mentor-order-decision-heading strong{color:#2b3f5d;font-size:29rpx;line-height:1.3;font-weight:900}.mentor-order-decision-heading text{margin-top:7rpx;color:#a9792e;font-size:19rpx;line-height:1.45;font-weight:750}.mentor-order-decision-heading button{width:54rpx;height:54rpx;min-height:54rpx;margin:0;padding:0;border:0;border-radius:50%;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);font-size:34rpx;line-height:1;font-weight:500}.mentor-order-decision-heading button::after,.mentor-order-decision-actions button::after{border:0}
.mentor-order-decision-section-title{margin-top:28rpx;color:#425974;font-size:23rpx;font-weight:900}.mentor-order-decision-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));margin-top:15rpx;overflow:hidden;border:2rpx solid var(--gyt-primary-border,#dce8fa);border-radius:20rpx;background:var(--gyt-primary-tint,#fbfdff)}.mentor-order-decision-fields>view{min-width:0;padding:17rpx}.mentor-order-decision-fields>view:nth-child(even){border-left:2rpx solid var(--gyt-primary-border,#e7eef8)}.mentor-order-decision-fields>view:nth-child(n+3){border-top:2rpx solid var(--gyt-primary-border,#e7eef8)}.mentor-order-decision-fields text,.mentor-order-decision-fields strong{display:block}.mentor-order-decision-fields text{color:#8b9aad;font-size:18rpx;font-weight:700}.mentor-order-decision-fields strong{margin-top:6rpx;overflow:hidden;color:#4c627e;font-size:21rpx;line-height:1.4;font-weight:800;text-overflow:ellipsis;white-space:nowrap}
.mentor-order-decision-question,.mentor-order-decision-reason{margin-top:18rpx;padding:20rpx;border:2rpx solid var(--gyt-primary-border,#dce8fa);border-radius:21rpx;background:var(--gyt-primary-tint,#fbfdff)}.mentor-order-decision-question text,.mentor-order-decision-question strong{display:block}.mentor-order-decision-question text{color:#8091a7;font-size:19rpx;font-weight:800}.mentor-order-decision-question strong{margin-top:9rpx;color:#536a86;font-size:22rpx;line-height:1.6;font-weight:650;white-space:pre-wrap}.mentor-order-decision-reason>view{display:flex;align-items:baseline;justify-content:space-between;gap:16rpx}.mentor-order-decision-reason>view text{color:#4c627e;font-size:22rpx;font-weight:900}.mentor-order-decision-reason>view strong{color:#94a1b2;font-size:17rpx;font-weight:650}.mentor-order-decision-reason textarea{box-sizing:border-box;width:100%;min-height:128rpx;margin-top:14rpx;padding:15rpx;border:2rpx solid var(--gyt-primary-border,#d7e5fb);border-radius:16rpx;background:var(--gyt-panel-bg,#fff);color:#415873;font-size:21rpx;line-height:1.55;font-weight:650}.mentor-order-decision-reason>text{display:block;margin-top:8rpx;color:#9aa8b8;text-align:right;font-size:17rpx;font-weight:650}
.mentor-order-decision-actions{display:grid;grid-template-columns:.8fr 1fr 1.45fr;gap:10rpx;margin-top:22rpx}.mentor-order-decision-actions button{box-sizing:border-box;position:relative;display:flex;align-items:center;justify-content:center;min-width:0;width:100%;height:68rpx;min-height:68rpx;margin:0;padding:0 10rpx;border:0;border-radius:18rpx;background:var(--gyt-primary-gradient,#3478f6);color:#fff;font-size:19rpx;line-height:1;font-weight:850;text-align:center;overflow:hidden;-webkit-appearance:none;appearance:none}.mentor-order-decision-actions button.light{background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6)}.mentor-order-decision-actions button.reject{background:#f4a39b;color:#fff}.mentor-order-decision-actions button[disabled]{background:var(--gyt-primary-gradient,#3478f6);color:#fff;opacity:.58}.mentor-order-decision-actions button.light[disabled]{background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6)}.mentor-order-decision-actions button.reject[disabled]{background:#f4a39b;color:#fff}.mentor-order-decision-label{display:block;width:100%;color:inherit;font-size:inherit;line-height:1.2;font-weight:inherit;text-align:center;white-space:nowrap}.mentor-order-decision-spinner{box-sizing:border-box;position:absolute;top:0;bottom:0;left:12rpx;width:28rpx;height:28rpx;margin:auto 0;border:3rpx solid rgba(255,255,255,.45);border-top-color:currentColor;border-radius:50%;color:inherit;pointer-events:none;animation:mentorOrderDecisionSpin .8s linear infinite}@keyframes mentorOrderDecisionSpin{to{transform:rotate(360deg)}}
@media(max-width:360px){.mentor-order-decision-fields{grid-template-columns:1fr}.mentor-order-decision-fields>view:nth-child(even){border-left:0}.mentor-order-decision-fields>view+view{border-top:2rpx solid var(--gyt-primary-border,#e7eef8)}.mentor-order-decision-actions{grid-template-columns:1fr}.mentor-order-decision-actions button{height:60rpx;min-height:60rpx}.mentor-order-decision-spinner{left:18rpx}}

/* 认证申请页沿用“我的”页的分组卡语言：暖灰底、白卡和中性字段面。
   品牌色只用于选中态与主操作，避免大面积蓝色描边和渐变。 */
.mentor-apply-page {
  height: 100vh;
  height: 100dvh;
  background: #f5f3f7;
}

.mentor-apply-page :deep(.app-page-header) {
  border-bottom-color: transparent;
  background: #f5f3f7;
  box-shadow: none;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.mentor-apply-page :deep(.app-page-header-title) {
  color: #243343;
}

.mentor-apply-page :deep(.app-page-header-back:active) {
  background: #ebe8ed;
}

.mentor-apply-content {
  padding: 18rpx 34rpx 0;
}

.mentor-rejection-notice {
  box-sizing: border-box;
  width: 100%;
  margin-top: 18rpx;
  padding: 24rpx 26rpx;
  display: flex;
  align-items: flex-start;
  gap: 18rpx;
  border: 2rpx solid #efd4d0;
  border-radius: 30rpx;
  background: #fff9f8;
  box-shadow: 0 12rpx 30rpx rgba(128, 74, 69, .05);
}

.mentor-rejection-notice-icon {
  width: 42rpx;
  height: 42rpx;
  min-width: 42rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: #f4dfdc;
  color: #b55f57;
  font-size: 25rpx;
  line-height: 1;
  font-weight: 900;
}

.mentor-rejection-notice-copy {
  min-width: 0;
  flex: 1;
}

.mentor-rejection-notice-copy strong,
.mentor-rejection-notice-copy text,
.mentor-rejection-notice-copy small {
  display: block;
}

.mentor-rejection-notice-copy strong {
  color: #744b49;
  font-size: 24rpx;
  line-height: 1.4;
  font-weight: 900;
}

.mentor-rejection-notice-copy text {
  margin-top: 9rpx;
  color: #815e5b;
  font-size: 21rpx;
  line-height: 1.65;
  font-weight: 700;
  white-space: pre-wrap;
}

.mentor-rejection-notice-copy small {
  margin-top: 8rpx;
  color: #a18380;
  font-size: 18rpx;
  line-height: 1.5;
  font-weight: 600;
}

.mentor-apply-content .mentor-apply-card {
  border: 0;
  border-radius: 38rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 14rpx 36rpx rgba(56, 49, 64, 0.04);
}

.mentor-apply-content .mentor-apply-section-title {
  color: #243343;
}

.mentor-apply-content .mentor-apply-label,
.mentor-apply-content .mentor-apply-price-field strong {
  color: #343039;
}

.mentor-apply-content .mentor-apply-label > text:last-child,
.mentor-apply-content .mentor-apply-label > text + text,
.mentor-apply-content .mentor-apply-tip,
.mentor-apply-content .mentor-apply-copy,
.mentor-apply-content .mentor-apply-price-field text {
  color: #918c95;
}

.mentor-apply-content .mentor-apply-card input,
.mentor-apply-content .mentor-apply-card textarea,
.mentor-apply-content .mentor-apply-picker,
.mentor-apply-content .mentor-price-input {
  border-color: transparent;
  background: #f7f6f8;
  color: #343039;
  box-shadow: none;
}

.mentor-apply-content .mentor-apply-card input,
.mentor-apply-content .mentor-apply-picker {
  height: 76rpx;
  border-radius: 24rpx;
}

.mentor-apply-content .mentor-apply-picker {
  line-height: 1.2;
}

.mentor-apply-content .mentor-apply-picker text,
.mentor-apply-content .mentor-apply-placeholder {
  color: #aaa5ad;
}

.mentor-apply-content .mentor-apply-search-results button,
.mentor-apply-content .mentor-apply-exam-row button,
.mentor-apply-content .mentor-skill-options button {
  border-color: transparent;
  background: #f7f6f8;
  color: #68636c;
  box-shadow: inset 0 0 0 2rpx rgba(42, 38, 48, 0.055);
}

.mentor-apply-content .mentor-apply-exam-row button.active,
.mentor-apply-content .mentor-skill-options button.active {
  border-color: transparent;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  box-shadow: inset 0 0 0 2rpx var(--gyt-primary, #3478f6);
}

.mentor-apply-content .mentor-proof-image {
  border-color: rgba(42, 38, 48, 0.09);
}

.mentor-apply-content .mentor-proof-upload {
  border-color: #cbc7cf;
  background: #f7f6f8;
  color: #68636c;
}

.mentor-apply-content .mentor-proof-upload > text {
  color: var(--gyt-primary, #3478f6);
}

.mentor-apply-content .mentor-apply-card textarea {
  border-radius: 24rpx;
}

.mentor-apply-content .mentor-apply-price-field {
  border-top-color: rgba(42, 38, 48, 0.065);
}

.mentor-apply-content .mentor-price-input {
  color: var(--gyt-primary, #3478f6);
}

.mentor-apply-content .mentor-price-input input {
  height: 58rpx;
  border: 0;
  background: transparent;
  color: #343039;
}

.mentor-apply-content .mentor-price-input text {
  color: #68636c;
}

.mentor-apply-bottom-space {
  height: calc(148rpx + env(safe-area-inset-bottom));
}

.mentor-apply-footer {
  flex-shrink: 0;
  padding: 10rpx 34rpx calc(34rpx + env(safe-area-inset-bottom));
  border-top: 0;
  background: rgba(245, 243, 247, 0.96);
}

.mentor-apply-footer button {
  box-sizing: border-box;
  width: 100%;
  height: 80rpx;
  min-height: 80rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 24rpx;
  line-height: 1;
  font-weight: 900;
  text-align: center;
}

.mentor-apply-footer button::after {
  border: 0;
}

.mentor-consultation-opt-in {
  box-sizing: border-box;
  width: 100%;
  min-height: 126rpx;
  margin: 18rpx 0 0;
  padding: 24rpx 26rpx;
  border: 0;
  border-radius: 38rpx;
  background: rgba(255, 255, 255, 0.96);
  color: #343039;
  box-shadow: 0 14rpx 36rpx rgba(56, 49, 64, 0.04);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 22rpx;
  text-align: left;
  line-height: 1.2;
  -webkit-appearance: none;
  appearance: none;
  transition: transform 160ms ease, box-shadow 220ms ease, background-color 220ms ease;
}

.mentor-consultation-opt-in::after {
  border: 0;
}

.mentor-consultation-opt-in:active {
  transform: scale(.994);
}

.mentor-consultation-opt-in.is-selected {
  background: var(--gyt-panel-bg, rgba(255, 255, 255, 0.98));
  box-shadow: 0 14rpx 36rpx rgba(56, 49, 64, 0.04), inset 0 0 0 2rpx var(--gyt-primary-border, #d9e7fc);
}

.mentor-consultation-opt-in-copy {
  min-width: 0;
  flex: 1;
}

.mentor-consultation-opt-in-copy strong,
.mentor-consultation-opt-in-copy text {
  display: block;
}

.mentor-consultation-opt-in-copy strong {
  color: #343039;
  font-size: 25rpx;
  line-height: 1.35;
  font-weight: 900;
}

.mentor-consultation-opt-in-copy text {
  margin-top: 8rpx;
  color: #918c95;
  font-size: 19rpx;
  line-height: 1.5;
  font-weight: 650;
}

.mentor-consultation-opt-in-check {
  box-sizing: border-box;
  width: 44rpx;
  height: 44rpx;
  min-width: 44rpx;
  border: 3rpx solid #c8c4cc;
  border-radius: 50%;
  background: #ffffff;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: border-color 180ms ease, background-color 180ms ease, transform 220ms cubic-bezier(.22, 1, .36, 1);
}

.mentor-consultation-opt-in-check text {
  margin: 0;
  color: inherit;
  font-size: 27rpx;
  line-height: 1;
  font-weight: 900;
  animation: mentorConsultationCheckIn 180ms cubic-bezier(.22, 1, .36, 1) both;
}

@keyframes mentorConsultationCheckIn {
  from { opacity: 0; transform: scale(.62); }
  to { opacity: 1; transform: scale(1); }
}

.mentor-consultation-opt-in.is-selected .mentor-consultation-opt-in-check {
  border-color: var(--gyt-primary, #3478f6);
  background: var(--gyt-primary, #3478f6);
  transform: scale(1.04);
}

.mentor-consultation-fields {
  max-height: 0;
  overflow: hidden;
  opacity: 0;
  visibility: hidden;
  transform: translateY(-12rpx);
  transform-origin: top;
  pointer-events: none;
  transition:
    max-height 380ms cubic-bezier(.22, 1, .36, 1),
    opacity 170ms ease,
    transform 280ms cubic-bezier(.22, 1, .36, 1),
    visibility 0s linear 380ms;
}

.mentor-consultation-fields.is-expanded {
  max-height: 1600rpx;
  opacity: 1;
  visibility: visible;
  transform: translateY(0);
  pointer-events: auto;
  transition:
    max-height 380ms cubic-bezier(.22, 1, .36, 1),
    opacity 220ms ease 70ms,
    transform 320ms cubic-bezier(.22, 1, .36, 1),
    visibility 0s linear 0s;
}

/* Keep every action label centered by its visible box, including loading and disabled states. */
.mentor-apply-content .mentor-apply-search-results button,
.mentor-apply-content .mentor-apply-exam-row button,
.mentor-apply-content .mentor-skill-options button,
.mentor-proof-image button,
.mentor-proof-upload,
.mentor-apply-demo-card button,
.mentor-center-orders-heading button,
.mentor-center-order-actions button,
.mentor-order-decision-heading button {
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  line-height: 1.2;
  -webkit-appearance: none;
  appearance: none;
}

.mentor-apply-content .mentor-apply-exam-row button {
  line-height: 1.2;
}

.mentor-proof-image,
.mentor-proof-upload {
  box-sizing: border-box;
}

.mentor-center-schedule-button {
  display: flex;
  align-items: center;
  justify-content: center;
}

.mentor-center-schedule-button-label {
  position: static;
  width: 100%;
  height: 100%;
  display: flex !important;
  align-items: center;
  justify-content: center;
  transform: none;
}

.mentor-center-orders-heading button,
.mentor-center-order-actions button {
  position: relative;
  overflow: hidden;
}

.mentor-center-orders-heading button {
  width: 112rpx;
  min-width: 112rpx;
  height: 52rpx;
  min-height: 52rpx;
}

.mentor-center-order-actions button {
  width: 196rpx;
  min-width: 196rpx;
  height: 58rpx;
  min-height: 58rpx;
}

.mentor-center-orders-heading button[disabled],
.mentor-center-order-actions button[disabled] {
  padding-top: 0;
  padding-bottom: 0;
  opacity: .62;
}

.mentor-center-action-label {
  display: block;
  width: 100%;
  margin: 0 !important;
  color: inherit !important;
  font-size: inherit !important;
  line-height: 1.2 !important;
  font-weight: inherit !important;
  text-align: center;
}

.mentor-center-button-spinner {
  box-sizing: border-box;
  position: absolute;
  top: 0;
  bottom: 0;
  left: 8rpx;
  width: 24rpx;
  height: 24rpx;
  margin: auto 0;
  border: 3rpx solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  color: inherit;
  pointer-events: none;
  animation: mentorCenterButtonSpin .8s linear infinite;
}

@keyframes mentorCenterButtonSpin {
  to { transform: rotate(360deg); }
}

@media(max-width:350px) {
  .mentor-apply-content {
    padding-right: 26rpx;
    padding-left: 26rpx;
  }

  .mentor-apply-footer {
    padding-right: 26rpx;
    padding-left: 26rpx;
  }
}

.mentor-apply-score-na {
  box-sizing: border-box;
  width: 100%;
  height: 72rpx;
  padding: 0 18rpx;
  border: 2rpx solid var(--gyt-primary-border, #e0eafa);
  border-radius: 18rpx;
  background: var(--gyt-primary-tint, #fbfdff);
  color: #8b99ad;
  display: flex;
  align-items: center;
  font-size: 23rpx;
  line-height: 1.2;
  font-weight: 650;
}

@media (prefers-reduced-motion: reduce) {
  .mentor-consultation-opt-in,
  .mentor-consultation-opt-in-check,
  .mentor-consultation-fields,
  .mentor-consultation-fields.is-expanded {
    transition: none;
  }

  .mentor-consultation-opt-in-check text {
    animation: none;
  }

  .mentor-consultation-fields,
  .mentor-consultation-fields.is-expanded {
    transform: none;
  }
}
</style>
