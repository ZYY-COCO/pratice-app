<template>
  <view class="mentor-chat-page" :style="themeInlineStyle">
    <MentorPageHeader
      :title="chatTitle"
      :subtitle="mentor ? `✓ 已认证 · ${mentor.school} · ${mentor.major}` : ''"
      @back="goBack"
    >
      <template #right><button class="mentor-chat-more" @tap="showMore">•••</button></template>
    </MentorPageHeader>

    <view v-if="mentor" class="mentor-chat-service-tip" :class="{ ended: consultationEnded }">
      <view class="mentor-chat-service-main">
        <view class="mentor-chat-service-dot"></view>
        <text>{{ serviceTipText }}</text>
      </view>
      <text class="mentor-chat-service-detail">{{ serviceTipDetail }}</text>
    </view>

    <scroll-view scroll-y class="mentor-chat-scroll" :scroll-into-view="scrollTarget" scroll-with-animation>
      <view v-if="mentor" class="mentor-chat-content">
        <view class="mentor-chat-context-card" :class="{ expanded: contextExpanded }">
          <view
            class="mentor-chat-context-toggle"
            role="button"
            :aria-expanded="contextExpanded"
            aria-label="展开或收起本次咨询资料"
            @tap="contextExpanded = !contextExpanded"
          >
            <view class="mentor-chat-context-heading">
              <view class="mentor-chat-context-title">{{ isMentorViewer ? '考生咨询资料' : '本次咨询资料' }}</view>
              <view class="mentor-chat-context-summary">{{ contextSummary }}</view>
            </view>
            <view class="mentor-chat-context-arrow" :class="{ expanded: contextExpanded }"></view>
          </view>
          <view v-if="contextExpanded" class="mentor-chat-context-details">
            <view class="mentor-chat-context-line"><text>当前学校</text><strong>{{ questionnaire.school || '未填写' }}</strong></view>
            <view class="mentor-chat-context-line"><text>当前专业</text><strong>{{ questionnaire.major || '未填写' }}</strong></view>
            <view class="mentor-chat-context-line"><text>当前年级</text><strong>{{ questionnaire.grade || '未填写' }}</strong></view>
            <view class="mentor-chat-context-line"><text>预计毕业</text><strong>{{ questionnaire.graduationYear ? `${questionnaire.graduationYear}年` : '未填写' }}</strong></view>
            <view class="mentor-chat-context-question"><text>咨询问题</text><view>{{ questionnaire.question || '未填写咨询问题' }}</view></view>
          </view>
        </view>

        <view v-if="hasMoreHistoryMessages" class="mentor-chat-history-load">
          <button :loading="loadingEarlierMessages" @tap="loadEarlierMessages">{{ loadingEarlierMessages ? '正在加载更早记录' : '加载更早聊天记录' }}</button>
        </view>

        <view v-if="!consultationEnded && !shouldShowCompletionBar" class="mentor-chat-text-hint">
          {{ consultationActive ? '当前咨询仅支持文字沟通；如需提交图片凭证，可从右上角“…”进入举报页上传。' : waitingChatHint }}
        </view>

        <template v-for="message in messages" :key="message.id">
          <view
            v-if="message.sender === 'system'"
            :id="`mentor-message-${message.id}`"
            class="mentor-chat-system-message"
          >{{ message.content }}</view>
          <view
            v-else
            :id="`mentor-message-${message.id}`"
            class="mentor-chat-message-row"
            :class="isOwnMessage(message) ? 'user' : 'mentor'"
          >
            <view
              v-if="!isOwnMessage(message)"
              class="mentor-chat-avatar"
              :class="message.sender === 'mentor' ? `tone-${mentor.avatarTone || 'blue'}` : 'tone-mint'"
            >{{ message.sender === 'mentor' ? mentor.avatar : '同' }}</view>
            <view class="mentor-chat-message-stack">
              <view v-if="!isOwnMessage(message)" class="mentor-chat-sender">{{ message.sender === 'mentor' ? mentor.maskedName : '咨询同学' }}</view>
              <view class="mentor-chat-bubble">{{ message.content }}</view>
              <view class="mentor-chat-time">
                <text>{{ formatTime(message.createdAt) }}</text>
                <text v-if="message.deliveryState === 'sending'" class="mentor-chat-delivery sending">发送中</text>
                <text v-else-if="message.deliveryState === 'failed'" class="mentor-chat-delivery failed" @tap.stop="retryMessage(message)">发送失败，点击重试</text>
              </view>
            </view>
          </view>
        </template>
        <view id="mentor-chat-bottom" class="mentor-chat-bottom-anchor"></view>
      </view>
    </scroll-view>

    <view v-if="mentor && consultationEnded" class="mentor-chat-completed-bar" :class="{ mentor: isMentorViewer }">
      <view><strong>{{ endedTitle }}</strong><text>{{ endedCopy }}</text></view>
      <template v-if="isMentorViewer">
        <button @tap="goBack">返回咨询主页</button>
      </template>
      <template v-else-if="canReview">
        <button :disabled="reviewSubmitted" @tap="openReview">{{ reviewSubmitted ? '已评价' : '评价本次咨询' }}</button>
        <button class="light" @tap="consultAgain">再次咨询</button>
      </template>
      <template v-else>
        <button @tap="openSupport">查看处理进度</button>
        <button class="light" @tap="consultAgain">再次咨询</button>
      </template>
    </view>

    <view v-else-if="mentor && shouldShowCompletionBar" class="mentor-chat-completion-bar" :class="{ confirmed: currentViewerCompletionConfirmed }">
      <view>
        <strong>{{ completionTitle }}</strong>
        <text>{{ completionCopy }}</text>
      </view>
      <button v-if="!currentViewerCompletionConfirmed" :loading="finishing" @tap="requestFinishConsultation">确认结束</button>
      <button v-else class="light" @tap="openSupport">查看处理进度</button>
    </view>

    <view v-else-if="mentor" class="mentor-chat-input-bar">
      <input
        v-model="messageInput"
        :disabled="!consultationActive"
        :placeholder="chatInputPlaceholder"
        placeholder-class="mentor-chat-placeholder"
        confirm-type="send"
        maxlength="2000"
        cursor-spacing="16"
        @focus="scrollToBottom"
        @confirm="sendText"
      />
      <button class="mentor-chat-send" :disabled="!canSendText" @tap="sendText">发送</button>
    </view>

    <view v-if="!isMentorViewer && reviewVisible" class="mentor-review-mask" @tap="closeReview">
      <view class="mentor-review-sheet" @tap.stop>
        <view class="mentor-review-handle"></view>
        <view class="mentor-review-title">评价本次咨询</view>
        <view class="mentor-review-subtitle">你的反馈会帮助更多同学找到合适的前辈。</view>
        <view class="mentor-review-stars">
          <button v-for="star in 5" :key="star" :class="{ active: reviewRating >= star }" @tap="reviewRating = star">
            <image
              :src="reviewRating >= star
                ? '/static/ui-icons/png/gold/star.png'
                : '/static/ui-icons/png/neutral/star.png'"
              mode="aspectFit"
              aria-hidden="true"
            />
          </button>
        </view>
        <view class="mentor-review-tags">
          <button v-for="tag in reviewTags" :key="tag" :class="{ active: selectedReviewTags.includes(tag) }" @tap="toggleReviewTag(tag)">{{ tag }}</button>
        </view>
        <textarea v-model="reviewText" maxlength="300" placeholder="写下你的咨询体验（选填）" placeholder-class="mentor-chat-placeholder" />
        <view class="mentor-review-count">{{ reviewText.length }} / 300</view>
        <button class="mentor-review-submit" :loading="submittingReview" @tap="submitReview">提交评价</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import { onHide, onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import {
  completeMentorConsultationLocalRehearsal,
  completeMentorConsultationOrder,
  createMentorConsultationMessage,
  createMentorConsultationReview,
  fetchMentorProfile,
  fetchMentorConsultationMessages,
  fetchMentorConsultationOrder
} from '../../api/mentorConsultation'
import { markUserNotificationReadTarget } from '../../api/notifications'
import {
  cacheMentors,
  getConsultationDraft,
  getMentorById,
  normalizeMentorDetailResponse,
  saveConsultationOrder
} from '../../data/mentorConsultation'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const CHAT_MESSAGE_POLL_INTERVAL = 1500
const CHAT_POLL_RETRY_INTERVAL = 3200
const CHAT_ORDER_POLL_INTERVAL = 12000
const CHAT_RECONCILIATION_WINDOW_MS = 2 * 60 * 1000
const CHAT_CURSOR_OVERLAP_MS = 2000
const CHAT_HISTORY_PAGE_SIZE = 100

const mentor = ref(null)
const themeKey = ref(getStoredThemeKey())
const themeInlineStyle = computed(() => buildThemeStyle(themeKey.value))
const viewerRole = ref('applicant')
const questionnaire = ref({})
const contextExpanded = ref(false)
const messages = ref([])
const messageInput = ref('')
const orderId = ref('')
const orderStatus = ref('in_progress')
const acceptedAt = ref('')
const startedAt = ref('')
const paymentStatus = ref('unpaid')
const paymentReference = ref('')
const refundReference = ref('')
const rejectionReason = ref('')
const consultationWindowMinutes = ref(60)
const consultationEnded = ref(false)
const applicantCompletionConfirmedAt = ref('')
const mentorCompletionConfirmedAt = ref('')
const remainingServiceSeconds = ref(0)
const scrollTarget = ref('mentor-chat-bottom')
const reviewVisible = ref(false)
const reviewRating = ref(5)
const selectedReviewTags = ref([])
const reviewText = ref('')
const reviewSubmitted = ref(false)
const submittingReview = ref(false)
const finishing = ref(false)
const hasMoreHistoryMessages = ref(false)
const loadingEarlierMessages = ref(false)
const isLocalRehearsalMode = Boolean(import.meta.env.DEV)
let serviceTimer = null
let messagePollTimer = null
let orderPollTimer = null
let messagePollInFlight = false
let orderPollInFlight = false
let messageCursor = ''
let chatLoadPromise = null
let pageVisible = true
let returnSource = ''
let historyStartReached = false

const reviewTags = ['解答清晰', '回复及时', '很有帮助', '经验丰富', '建议具体']
const isMentorViewer = computed(() => viewerRole.value === 'mentor')
const contextSummary = computed(() => {
  const school = String(questionnaire.value.school || '').trim()
  const major = String(questionnaire.value.major || '').trim()
  return [school, major].filter(Boolean).join(' · ') || '点击查看本次咨询资料'
})
const currentViewerCompletionConfirmed = computed(() => Boolean(
  isMentorViewer.value ? mentorCompletionConfirmedAt.value : applicantCompletionConfirmedAt.value
))
const otherPartyCompletionConfirmed = computed(() => Boolean(
  isMentorViewer.value ? applicantCompletionConfirmedAt.value : mentorCompletionConfirmedAt.value
))
const consultationActive = computed(() => orderStatus.value === 'in_progress')
const isLocalRehearsalOrder = computed(() => isLocalRehearsalMode && paymentReference.value.toUpperCase().startsWith('DEMO-'))
const canReview = computed(() => !isMentorViewer.value && orderStatus.value === 'completed')
const autoRefundedOrder = computed(() => ['timeout', 'refunded'].includes(orderStatus.value))
const acceptedStartTimedOut = computed(() => orderStatus.value === 'timeout' && Boolean(acceptedAt.value) && !startedAt.value)
const serviceWindowExpired = computed(() => (
  consultationActive.value && remainingServiceSeconds.value <= 0
))
const shouldShowCompletionBar = computed(() => (
  !consultationEnded.value
  && orderStatus.value === 'in_progress'
  && (serviceWindowExpired.value || currentViewerCompletionConfirmed.value || otherPartyCompletionConfirmed.value)
))
const completionTitle = computed(() => {
  if (currentViewerCompletionConfirmed.value) return '已提交结束确认'
  return otherPartyCompletionConfirmed.value ? '对方已确认结束本次咨询' : '服务时间已结束'
})
const completionCopy = computed(() => {
  if (currentViewerCompletionConfirmed.value) return '等待对方确认后，本次咨询才会正式结束。'
  if (otherPartyCompletionConfirmed.value) return '请核对本次沟通内容后确认结束；如有问题可先从右上角举报。'
  return '双方确认后才会正式结束，本次聊天记录会继续保留。'
})
const chatTitle = computed(() => {
  if (!mentor.value) return '咨询聊天'
  if (shouldShowCompletionBar.value) return `${mentor.value.maskedName} · 待确认`
  if (!consultationActive.value && !consultationEnded.value) return `${mentor.value.maskedName} · 等待开始`
  return consultationEnded.value ? `${mentor.value.maskedName} · 聊天记录` : `${mentor.value.maskedName} · 咨询中`
})
const serviceTipText = computed(() => {
  if (consultationEnded.value) return '历史聊天记录'
  if (shouldShowCompletionBar.value) return currentViewerCompletionConfirmed.value ? '已提交结束确认' : '等待双方确认结束'
  if (!consultationActive.value) return isMentorViewer.value ? '请从咨询主页开始本次服务' : '等待认证前辈开始咨询'
  return `本次咨询窗口剩余 ${serviceCountdownText.value}`
})
const serviceTipDetail = computed(() => {
  if (consultationEnded.value) return '本次咨询已结束 · 仅供查阅'
  if (shouldShowCompletionBar.value) return currentViewerCompletionConfirmed.value ? '对方确认后即可完成订单' : '确认前可通过右上角发起平台介入'
  if (!consultationActive.value) return '服务开始后会开放文字聊天'
  return `服务时间：${consultationWindowMinutes.value}分钟`
})
const endedTitle = computed(() => {
  if (autoRefundedOrder.value) return '本次咨询已自动取消'
  if (orderStatus.value === 'cancelled') return '本次咨询已取消'
  if (orderStatus.value === 'rejected') return '本次咨询未获接单'
  return '本次咨询已结束'
})
const refundProgressCopy = computed(() => {
  if (paymentStatus.value === 'refunded') return '退款已完成并将原路退回。'
  if (paymentStatus.value === 'refunding') return '平台已提交退款处理，完成后会自动同步到平台处理进度。'
  if (paymentStatus.value === 'failed' && refundReference.value) return '退款处理出现异常，平台正在继续跟进，请查看平台处理进度。'
  return '如已支付，退款结果会同步到平台处理进度。'
})
const endedCopy = computed(() => {
  if (acceptedStartTimedOut.value) return `前辈已接单但未在保护时间内开始服务，${refundProgressCopy.value}`
  if (autoRefundedOrder.value) return `预约时段内未开始服务，${refundProgressCopy.value}`
  if (orderStatus.value === 'cancelled') return `订单已取消；${refundProgressCopy.value}`
  if (orderStatus.value === 'rejected') return `${rejectionReason.value ? `前辈说明：${rejectionReason.value}。` : '本次订单未进入服务阶段；'}${refundProgressCopy.value}`
  return '感谢你的信任，聊天记录已保留。'
})
const waitingChatHint = computed(() => (
  isMentorViewer.value
    ? '请返回咨询主页，在可服务时间内开始本次咨询；开始后文字聊天会自动开放。'
    : '认证前辈开始服务后会自动开放文字聊天；你可返回订单页取消订单或查看平台处理进度。'
))
const chatInputPlaceholder = computed(() => {
  if (!consultationActive.value) return isMentorViewer.value ? '请先从咨询主页开始服务' : '等待认证前辈开始咨询'
  return isMentorViewer.value ? '输入文字回复' : '输入想继续咨询的问题'
})
const canSendText = computed(() => (
  consultationActive.value
  && !consultationEnded.value
  && !shouldShowCompletionBar.value
  && Boolean(messageInput.value.trim())
))
const serviceCountdownText = computed(() => {
  const minutes = String(Math.floor(Math.max(0, remainingServiceSeconds.value) / 60)).padStart(2, '0')
  const seconds = String(Math.max(0, remainingServiceSeconds.value) % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
})

onLoad((options) => {
  const draft = getConsultationDraft()
  returnSource = String(options?.from || '')
  viewerRole.value = options?.role === 'mentor' ? 'mentor' : 'applicant'
  orderId.value = String(options?.orderId || draft?.orderId || '')
  const mentorId = options?.mentorId || draft?.mentorId
  mentor.value = getMentorById(mentorId)
  historyStartReached = false
  hasMoreHistoryMessages.value = false
  if (!orderId.value) {
    uni.showToast({ title: '未找到咨询订单，请返回重新进入', icon: 'none' })
    return
  }
  void markCurrentOrderNotificationsRead()
  void loadMentor(mentorId)
  void loadChatData()
})

onShow(() => {
  pageVisible = true
  themeKey.value = getStoredThemeKey()
  if (orderId.value) {
    void markCurrentOrderNotificationsRead()
    void loadChatData({ silent: true })
  }
})

onHide(() => {
  pageVisible = false
  stopChatTimers()
})

onBeforeUnmount(() => {
  pageVisible = false
  stopChatTimers()
})

async function loadChatData({ silent = false } = {}) {
  if (!orderId.value) return
  if (chatLoadPromise) return chatLoadPromise

  chatLoadPromise = Promise.all([
    fetchMentorConsultationOrder(orderId.value),
    fetchMentorConsultationMessages(orderId.value, { limit: 100 })
  ])
    .then(([order, messagePayload]) => {
      applyOrder(order)
      const incoming = Array.isArray(messagePayload?.items) ? messagePayload.items : []
      if (!historyStartReached) hasMoreHistoryMessages.value = incoming.length >= CHAT_HISTORY_PAGE_SIZE
      if (mergeRemoteMessages(incoming)) scrollToBottom()
      startMessagePolling()
      startOrderPolling()
    })
    .catch((error) => {
      if (!silent) uni.showToast({ title: error?.detail || '咨询聊天加载失败', icon: 'none' })
    })
    .finally(() => {
      chatLoadPromise = null
    })

  return chatLoadPromise
}

async function markCurrentOrderNotificationsRead() {
  if (!orderId.value) return
  try {
    await markUserNotificationReadTarget('consultation_order', orderId.value)
  } catch (error) {
    // 已读状态的短暂同步失败不应影响咨询聊天。
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
    // 目录缓存可保证订单页在短暂网络波动时仍能展示前辈信息。
  }
}

function applyOrder(order) {
  const draft = saveConsultationOrder(order)
  questionnaire.value = draft.questionnaire || {}
  orderStatus.value = draft.orderStatus || 'in_progress'
  paymentStatus.value = draft.paymentStatus || 'unpaid'
  paymentReference.value = draft.paymentReference || ''
  refundReference.value = draft.refundReference || ''
  rejectionReason.value = draft.rejectionReason || ''
  acceptedAt.value = draft.acceptedAt || ''
  startedAt.value = draft.startedAt || ''
  consultationWindowMinutes.value = Number(draft.consultationWindowMinutes) || 60
  applicantCompletionConfirmedAt.value = draft.applicantCompletionConfirmedAt || ''
  mentorCompletionConfirmedAt.value = draft.mentorCompletionConfirmedAt || ''
  consultationEnded.value = ['completed', 'refunded', 'cancelled', 'rejected', 'timeout'].includes(orderStatus.value)
  if (consultationEnded.value) {
    remainingServiceSeconds.value = 0
    stopChatTimers()
    return
  }
  if (!consultationActive.value) {
    remainingServiceSeconds.value = 0
    stopServiceTimer()
    return
  }
  syncServiceRemainingSeconds()
  startServiceTimer()
}

function normalizeMessage(message = {}) {
  const senderRole = String(message.sender || message.sender_role || 'system')
  return {
    id: String(message.id || `local-${Date.now()}`),
    sender: senderRole === 'applicant' ? 'user' : senderRole,
    type: String(message.type || message.message_type || 'text'),
    content: String(message.content || ''),
    createdAt: message.createdAt || message.created_at || Date.now(),
    clientMessageId: String(message.clientMessageId || message.client_message_id || ''),
    deliveryState: message.deliveryState || 'sent'
  }
}

function mergeRemoteMessages(incoming = []) {
  const remoteMessages = incoming.map(normalizeMessage)
  if (!remoteMessages.length) return false

  const next = [...messages.value]
  let changed = false
  for (const remoteMessage of remoteMessages) {
    const existingIndex = next.findIndex((item) => item.id === remoteMessage.id)
    if (existingIndex >= 0) {
      if (next[existingIndex].deliveryState !== 'sent') {
        next[existingIndex] = remoteMessage
        changed = true
      }
      continue
    }

    const optimisticIndex = next.findIndex((item) => isMatchingOptimisticMessage(item, remoteMessage))
    if (optimisticIndex >= 0) {
      next[optimisticIndex] = remoteMessage
    } else {
      next.push(remoteMessage)
    }
    changed = true
  }

  updateMessageCursor(remoteMessages)
  if (changed) {
    next.sort((left, right) => (
      toTimestamp(left.createdAt) - toTimestamp(right.createdAt)
      || String(left.id).localeCompare(String(right.id))
    ))
    messages.value = next
  }
  return changed
}

function isMatchingOptimisticMessage(localMessage, remoteMessage) {
  if (!localMessage || localMessage.deliveryState === 'sent') return false
  if (localMessage.clientMessageId && localMessage.clientMessageId === remoteMessage.clientMessageId) return true
  if (localMessage.sender !== remoteMessage.sender || localMessage.type !== remoteMessage.type) return false
  if (localMessage.content !== remoteMessage.content) return false
  return Math.abs(toTimestamp(localMessage.createdAt) - toTimestamp(remoteMessage.createdAt)) <= CHAT_RECONCILIATION_WINDOW_MS
}

function updateMessageCursor(remoteMessages = []) {
  for (const message of remoteMessages) {
    if (!message.createdAt) continue
    if (!messageCursor || toTimestamp(message.createdAt) > toTimestamp(messageCursor)) {
      messageCursor = String(message.createdAt)
    }
  }
}

function toTimestamp(value) {
  const timestamp = value instanceof Date ? value.getTime() : Date.parse(String(value || ''))
  return Number.isFinite(timestamp) ? timestamp : 0
}

function getIncrementalMessageCursor() {
  const timestamp = toTimestamp(messageCursor)
  return timestamp ? new Date(Math.max(0, timestamp - CHAT_CURSOR_OVERLAP_MS)).toISOString() : ''
}

function isOwnMessage(message = {}) {
  return isMentorViewer.value
    ? message.sender === 'mentor'
    : message.sender === 'user'
}

function syncServiceRemainingSeconds() {
  const startedTimestamp = Date.parse(startedAt.value || '')
  const windowSeconds = consultationWindowMinutes.value * 60
  remainingServiceSeconds.value = Number.isFinite(startedTimestamp)
    ? Math.max(0, Math.ceil((startedTimestamp + windowSeconds * 1000 - Date.now()) / 1000))
    : windowSeconds
}

function startServiceTimer() {
  if (serviceTimer || consultationEnded.value || !consultationActive.value) return
  serviceTimer = setInterval(() => {
    syncServiceRemainingSeconds()
    if (remainingServiceSeconds.value <= 0 && serviceTimer) {
      clearInterval(serviceTimer)
      serviceTimer = null
    }
  }, 1000)
}

function stopServiceTimer() {
  if (serviceTimer) clearInterval(serviceTimer)
  serviceTimer = null
}

function startMessagePolling() {
  if (messagePollTimer || consultationEnded.value || !orderId.value || !pageVisible) return
  scheduleNextMessagePoll(CHAT_MESSAGE_POLL_INTERVAL)
}

function scheduleNextMessagePoll(delay) {
  if (consultationEnded.value || !orderId.value || !pageVisible) return
  if (messagePollTimer) clearTimeout(messagePollTimer)
  messagePollTimer = setTimeout(async () => {
    messagePollTimer = null
    const synced = await syncLatestMessages()
    scheduleNextMessagePoll(synced ? CHAT_MESSAGE_POLL_INTERVAL : CHAT_POLL_RETRY_INTERVAL)
  }, delay)
}

async function syncLatestMessages({ full = false } = {}) {
  if (!pageVisible || !orderId.value || messagePollInFlight) return true
  messagePollInFlight = true
  try {
    const after = full ? '' : getIncrementalMessageCursor()
    const payload = await fetchMentorConsultationMessages(orderId.value, {
      limit: 100,
      ...(after ? { after } : {})
    })
    const incoming = Array.isArray(payload?.items) ? payload.items : []
    if (mergeRemoteMessages(incoming)) scrollToBottom()
    return true
  } catch (error) {
    return false
  } finally {
    messagePollInFlight = false
  }
}

async function loadEarlierMessages() {
  if (loadingEarlierMessages.value || !hasMoreHistoryMessages.value || !orderId.value) return
  const earliestMessage = messages.value.reduce((earliest, message) => {
    if (!earliest || toTimestamp(message.createdAt) < toTimestamp(earliest.createdAt)) return message
    return earliest
  }, null)
  const before = String(earliestMessage?.createdAt || '')
  if (!before) {
    hasMoreHistoryMessages.value = false
    return
  }

  loadingEarlierMessages.value = true
  try {
    const payload = await fetchMentorConsultationMessages(orderId.value, {
      before,
      limit: CHAT_HISTORY_PAGE_SIZE
    })
    const incoming = Array.isArray(payload?.items) ? payload.items : []
    mergeRemoteMessages(incoming)
    hasMoreHistoryMessages.value = incoming.length >= CHAT_HISTORY_PAGE_SIZE
    if (!hasMoreHistoryMessages.value) historyStartReached = true
  } catch (error) {
    uni.showToast({ title: error?.detail || '更早聊天记录加载失败', icon: 'none' })
  } finally {
    loadingEarlierMessages.value = false
  }
}

function startOrderPolling() {
  if (orderPollTimer || consultationEnded.value || !orderId.value || !pageVisible) return
  scheduleNextOrderPoll(CHAT_ORDER_POLL_INTERVAL)
}

function scheduleNextOrderPoll(delay) {
  if (consultationEnded.value || !orderId.value || !pageVisible) return
  if (orderPollTimer) clearTimeout(orderPollTimer)
  orderPollTimer = setTimeout(async () => {
    orderPollTimer = null
    const synced = await syncCurrentOrder()
    scheduleNextOrderPoll(synced ? CHAT_ORDER_POLL_INTERVAL : CHAT_POLL_RETRY_INTERVAL)
  }, delay)
}

async function syncCurrentOrder() {
  if (!pageVisible || !orderId.value || orderPollInFlight) return true
  orderPollInFlight = true
  try {
    applyOrder(await fetchMentorConsultationOrder(orderId.value))
    return true
  } catch (error) {
    return false
  } finally {
    orderPollInFlight = false
  }
}

function stopChatTimers() {
  if (serviceTimer) clearInterval(serviceTimer)
  if (messagePollTimer) clearTimeout(messagePollTimer)
  if (orderPollTimer) clearTimeout(orderPollTimer)
  serviceTimer = null
  messagePollTimer = null
  orderPollTimer = null
}

function sendText() {
  if (!consultationActive.value) {
    uni.showToast({ title: '请等待认证前辈开始咨询', icon: 'none' })
    return
  }
  const content = messageInput.value.trim()
  if (!content || consultationEnded.value || shouldShowCompletionBar.value || !orderId.value) return

  const clientMessageId = createClientMessageId()
  const localMessageId = `local-${clientMessageId}`
  messages.value = [...messages.value, {
    id: localMessageId,
    sender: isMentorViewer.value ? 'mentor' : 'user',
    type: 'text',
    content,
    createdAt: new Date().toISOString(),
    clientMessageId,
    deliveryState: 'sending'
  }]
  messageInput.value = ''
  scrollToBottom()
  void sendPendingMessage(localMessageId)
}

async function sendPendingMessage(localMessageId) {
  const pendingMessage = messages.value.find((item) => item.id === localMessageId)
  if (!pendingMessage || pendingMessage.deliveryState !== 'sending') return
  try {
    const message = await createMentorConsultationMessage(orderId.value, {
      message_type: 'text',
      content: pendingMessage.content,
      client_message_id: pendingMessage.clientMessageId
    })
    const confirmedMessage = normalizeMessage(message)
    messages.value = messages.value.map((item) => item.id === localMessageId ? confirmedMessage : item)
    updateMessageCursor([confirmedMessage])
    scrollToBottom()
    scheduleNextMessagePoll(0)
  } catch (error) {
    messages.value = messages.value.map((item) => item.id === localMessageId
      ? { ...item, deliveryState: 'failed' }
      : item)
  }
}

function createClientMessageId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') return crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(36).slice(2, 14)}`
}

async function retryMessage(message) {
  if (!message || message.deliveryState !== 'failed') return
  if (!consultationActive.value) {
    uni.showToast({ title: '本次咨询暂未开始或已结束', icon: 'none' })
    return
  }
  messages.value = messages.value.map((item) => item.id === message.id
    ? { ...item, deliveryState: 'sending' }
    : item)
  const synced = await syncLatestMessages({ full: true })
  const pendingMessage = messages.value.find((item) => item.id === message.id)
  if (synced && pendingMessage?.deliveryState === 'sending') {
    void sendPendingMessage(message.id)
  }
}

function requestFinishConsultation() {
  if (consultationEnded.value || currentViewerCompletionConfirmed.value || finishing.value || !orderId.value) return
  const canCompleteLocalRehearsal = isLocalRehearsalOrder.value && !isMentorViewer.value
  uni.showModal({
    title: '确认结束本次咨询？',
    content: canCompleteLocalRehearsal
      ? '结束后会进入评价阶段；聊天、举报和后台处理记录会继续保留。'
      : '提交后需要等待对方确认；双方确认后订单才会正式结束。',
    confirmText: canCompleteLocalRehearsal ? '结束并评价' : '确认结束',
    success(result) {
      if (result.confirm) void finishConsultation()
    }
  })
}

async function finishConsultation() {
  if (consultationEnded.value || currentViewerCompletionConfirmed.value || finishing.value || !orderId.value) return
  finishing.value = true
  try {
    const canCompleteLocalRehearsal = isLocalRehearsalOrder.value && !isMentorViewer.value
    const order = canCompleteLocalRehearsal
      ? await completeMentorConsultationLocalRehearsal(orderId.value)
      : await completeMentorConsultationOrder(orderId.value)
    applyOrder(order)
    await loadChatData({ silent: true })
    scrollToBottom()
    const completed = String(order?.order_status || order?.orderStatus || '') === 'completed'
    uni.showToast({ title: completed ? (canCompleteLocalRehearsal ? '咨询已结束，可以评价' : '双方已确认，咨询已结束') : '已确认结束，等待对方确认', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '结束咨询确认失败', icon: 'none' })
  } finally {
    finishing.value = false
  }
}

function scrollToBottom() {
  nextTick(() => {
    scrollTarget.value = ''
    nextTick(() => { scrollTarget.value = 'mentor-chat-bottom' })
  })
}

function formatTime(timestamp) {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  if (Number.isNaN(date.getTime())) return ''
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function showMore() {
  const actions = [
    { label: '查看咨询规则', key: 'rules' },
    { label: '举报此咨询', key: 'report' }
  ]
  if (orderStatus.value === 'in_progress' && !currentViewerCompletionConfirmed.value) {
    actions.push({ label: isLocalRehearsalOrder.value && !isMentorViewer.value ? '结束并评价' : '确认结束本次咨询', key: 'complete' })
  }
  uni.showActionSheet({
    itemList: actions.map((item) => item.label),
    success: ({ tapIndex }) => {
      const action = actions[tapIndex]?.key
      if (action === 'report') openReport()
      if (action === 'complete') requestFinishConsultation()
      if (action === 'rules') showConsultationRules()
    }
  })
}

function showConsultationRules() {
  uni.showModal({
    title: '咨询规则',
    content: '请在站内完成沟通，不要泄露隐私或进行私下交易；服务结束后需双方确认，如有争议可提交平台介入。',
    showCancel: false,
    confirmText: '我知道了'
  })
}

function openReport() {
  if (!orderId.value) return
  const targetRole = isMentorViewer.value ? 'applicant' : 'mentor'
  uni.navigateTo({
    url: `/pages-sub-consultation/consultation/mentor-report?orderId=${encodeURIComponent(orderId.value)}&mentorId=${encodeURIComponent(mentor.value?.id || '')}&reporterRole=${isMentorViewer.value ? 'mentor' : 'applicant'}&targetRole=${targetRole}`
  })
}

function openSupport() {
  uni.navigateTo({ url: '/pages-sub-consultation/consultation/mentor-support' })
}

function openReview() {
  if (canReview.value && !reviewSubmitted.value) reviewVisible.value = true
}
function closeReview() {
  if (!submittingReview.value) reviewVisible.value = false
}
function toggleReviewTag(tag) {
  selectedReviewTags.value = selectedReviewTags.value.includes(tag)
    ? selectedReviewTags.value.filter((item) => item !== tag)
    : [...selectedReviewTags.value, tag]
}
async function submitReview() {
  if (!canReview.value || submittingReview.value || !orderId.value) return
  submittingReview.value = true
  try {
    await createMentorConsultationReview(orderId.value, {
      rating: reviewRating.value,
      tags: selectedReviewTags.value,
      content: reviewText.value.trim()
    })
    reviewSubmitted.value = true
    reviewVisible.value = false
    uni.showToast({ title: '评价已提交，感谢你的反馈', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '评价提交失败', icon: 'none' })
  } finally {
    submittingReview.value = false
  }
}
function consultAgain() {
  if (!mentor.value) return
  uni.navigateTo({ url: `/pages-sub-consultation/consultation/mentor-consult-form?mentorId=${encodeURIComponent(mentor.value.id)}&mode=instant` })
}
function goBack() {
  const fallbackUrl = returnSource === 'my-consultations'
    ? '/pages-sub-consultation/consultation/my-consultations'
    : returnSource === 'mentor-center' || isMentorViewer.value
      ? '/pages-sub-consultation/consultation/mentor-apply?mode=center'
      : '/pages/home/index?tab=circle&section=community&communityTab=mentor'
  uni.navigateBack({ fail() { uni.reLaunch({ url: fallbackUrl }) } })
}
</script>

<style scoped>
.mentor-chat-page{height:100vh;height:100dvh;overflow:hidden;background:#f4f8ff;display:flex;flex-direction:column}.mentor-chat-service-tip{margin:16rpx 24rpx 0;padding:14rpx 18rpx;border:2rpx solid #d7e7ff;border-radius:17rpx;background:#edf4ff;color:#3478f6;display:flex;align-items:center;justify-content:space-between;gap:14rpx;font-size:20rpx;line-height:1.3;font-weight:850}.mentor-chat-service-tip view{color:#7690ba;font-size:18rpx;font-weight:650;white-space:nowrap}.mentor-chat-service-tip.ended{border-color:#dce8f6;background:#f5f8fc;color:#6b7d95}.mentor-chat-scroll{min-height:0;flex:1}.mentor-chat-content{padding:22rpx 24rpx 36rpx}.mentor-chat-system-message{margin:0 auto 22rpx;padding:10rpx 16rpx;border-radius:999rpx;background:#e7eef9;color:#7b8da5;text-align:center;font-size:18rpx;line-height:1.35;font-weight:650;width:max-content;max-width:88%}
.mentor-chat-context-card{padding:24rpx;border:2rpx solid #d9e7fc;border-radius:25rpx;background:rgba(255,255,255,.92);box-shadow:0 12rpx 28rpx rgba(52,120,246,.06)}.mentor-chat-context-title{color:#314764;font-size:25rpx;font-weight:900}.mentor-chat-context-line{display:flex;align-items:center;justify-content:space-between;gap:18rpx;margin-top:15rpx;color:#8896a9;font-size:20rpx;font-weight:650}.mentor-chat-context-line strong{color:#465a74;text-align:right;font-size:21rpx;font-weight:800}.mentor-chat-context-question{margin-top:18rpx;padding-top:16rpx;border-top:2rpx solid #eef2f8}.mentor-chat-context-question text{display:block;color:#8090a6;font-size:20rpx;font-weight:750}.mentor-chat-context-question view{margin-top:8rpx;color:#51647e;font-size:21rpx;line-height:1.55;font-weight:650}
.mentor-chat-message-row{display:flex;align-items:flex-start;gap:12rpx;margin-top:26rpx}.mentor-chat-message-row.user{justify-content:flex-end}.mentor-chat-avatar{width:56rpx;height:56rpx;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:22rpx;font-weight:900;flex-shrink:0}.mentor-chat-avatar.tone-blue{background:#e6efff;color:#3478f6}.mentor-chat-avatar.tone-mint{background:#e2f4ef;color:#198777}.mentor-chat-avatar.tone-violet{background:#eeeafe;color:#7162bd}.mentor-chat-avatar.tone-warm{background:#f9eee1;color:#b66c32}.mentor-chat-message-stack{max-width:78%}.mentor-chat-message-row.user .mentor-chat-message-stack{display:flex;flex-direction:column;align-items:flex-end}.mentor-chat-sender{margin:0 0 6rpx 3rpx;color:#8090a6;font-size:18rpx;font-weight:700}.mentor-chat-bubble{padding:16rpx 18rpx;border-radius:8rpx 20rpx 20rpx 20rpx;background:#fff;color:#465a74;font-size:22rpx;line-height:1.55;font-weight:600;box-shadow:0 7rpx 16rpx rgba(49,83,132,.06)}.mentor-chat-message-row.user .mentor-chat-bubble{border-radius:20rpx 8rpx 20rpx 20rpx;background:#3478f6;color:#fff}.mentor-chat-bubble.voice{min-width:162rpx;color:#4d6ea0;font-weight:800}.mentor-chat-message-row.user .mentor-chat-bubble.voice{color:#fff}.mentor-chat-bubble.image{padding:8rpx}.mentor-chat-image-placeholder{width:190rpx;height:128rpx;border-radius:14rpx;background:linear-gradient(135deg,#dceaff,#bcd5ff);color:#5b7cae;display:flex;align-items:center;justify-content:center;font-size:19rpx;font-weight:800}.mentor-chat-message-row.user .mentor-chat-image-placeholder{background:rgba(255,255,255,.28);color:#fff}.mentor-chat-time{margin-top:6rpx;color:#a1adbd;font-size:16rpx;font-weight:650}.mentor-chat-bottom-anchor{height:2rpx}
.mentor-chat-input-bar{padding:14rpx 18rpx calc(30rpx + env(safe-area-inset-bottom));border-top:2rpx solid #dbe7f8;background:rgba(255,255,255,.97);display:flex;align-items:center;gap:10rpx}.mentor-chat-input-bar input{min-width:0;flex:1;height:72rpx;padding:0 18rpx;border:2rpx solid #e0eafa;border-radius:18rpx;background:#f9fbff;color:#3b4f6b;font-size:21rpx;font-weight:600}.mentor-chat-placeholder{color:#a3b1c2;font-weight:500}.mentor-chat-tool,.mentor-chat-send,.mentor-chat-more,.mentor-chat-voice-hold{margin:0;border:0}.mentor-chat-tool{box-sizing:border-box;width:60rpx;height:60rpx;min-width:60rpx;min-height:60rpx;padding:9rpx;border-radius:50%;background:#edf4ff;color:#5d80ba;display:flex;align-items:center;justify-content:center;font-size:26rpx;line-height:1}.mentor-chat-tool image{width:100%;height:100%}.mentor-chat-mode-toggle image{transform:scale(1.18)}.mentor-chat-voice-hold{min-width:0;flex:1;height:72rpx;padding:0 18rpx;border:2rpx solid #d9e7fa;border-radius:18rpx;background:#f9fbff;color:#526e98;display:flex;align-items:center;justify-content:center;text-align:center;font-size:22rpx;line-height:1;font-weight:800}.mentor-chat-voice-hold.recording{border-color:#a8c7fa;background:#e8f1ff;color:#3478f6}.mentor-chat-send{box-sizing:border-box;min-width:116rpx;height:72rpx;padding:0 16rpx;border-radius:19rpx;background:#3478f6;color:#fff;display:flex;align-items:center;justify-content:center;text-align:center;font-size:23rpx;line-height:1;font-weight:900;white-space:nowrap;box-shadow:0 8rpx 18rpx rgba(52,120,246,.18)}.mentor-chat-send[disabled]{background:#bfccdd;box-shadow:none}.mentor-chat-tool::after,.mentor-chat-send::after,.mentor-chat-more::after,.mentor-chat-voice-hold::after{border:0}.mentor-chat-more{box-sizing:border-box;width:54rpx;height:54rpx;min-width:54rpx;min-height:54rpx;padding:0;border-radius:50%;background:#edf4ff;color:#6681ad;display:flex;align-items:center;justify-content:center;text-align:center;font-size:21rpx;line-height:1;font-weight:900;white-space:nowrap}
.mentor-chat-completed-bar{padding:14rpx 20rpx calc(16rpx + env(safe-area-inset-bottom));border-top:2rpx solid #dbe7f8;background:rgba(255,255,255,.98);display:grid;grid-template-columns:minmax(0,1fr) 166rpx 118rpx;align-items:center;gap:10rpx}.mentor-chat-completed-bar>view{min-width:0}.mentor-chat-completed-bar strong,.mentor-chat-completed-bar text{display:block}.mentor-chat-completed-bar strong{color:#31445f;font-size:22rpx;font-weight:900}.mentor-chat-completed-bar text{margin-top:5rpx;color:#8998aa;font-size:17rpx;line-height:1.3;font-weight:650}.mentor-chat-completed-bar button{box-sizing:border-box;height:64rpx;min-height:64rpx;margin:0;padding:0 10rpx;border:0;border-radius:17rpx;background:#3478f6;color:#fff;display:flex;align-items:center;justify-content:center;text-align:center;font-size:19rpx;line-height:1;font-weight:850;white-space:nowrap}.mentor-chat-completed-bar button::after{border:0}.mentor-chat-completed-bar button.light{background:#edf4ff;color:#5274aa}
.mentor-chat-completed-bar.mentor{grid-template-columns:minmax(0,1fr) 180rpx}
.mentor-chat-recording-overlay{position:fixed;z-index:30;top:50%;left:50%;box-sizing:border-box;width:100%;padding:0 36rpx;transform:translate(-50%,-50%);pointer-events:none;display:flex;justify-content:center;opacity:1;transition:opacity 160ms ease}.mentor-chat-recording-overlay.ending{opacity:0}.mentor-chat-recording-bubble{box-sizing:border-box;min-width:284rpx;height:178rpx;padding:32rpx 30rpx;border:2rpx solid rgba(255,255,255,.34);border-radius:34rpx;background:var(--gyt-primary-gradient,linear-gradient(135deg,#3478f6,#68a0ff));box-shadow:0 22rpx 54rpx var(--gyt-primary-shadow,rgba(52,120,246,.2));display:flex;align-items:center;justify-content:center}.mentor-chat-waveform{height:94rpx;display:flex;align-items:center;justify-content:center;gap:7rpx}.mentor-chat-wave-bar{display:block;width:7rpx;min-width:7rpx;height:82rpx;min-height:82rpx;border-radius:999rpx;background:rgba(255,255,255,.96);transform-origin:center;transition:transform 72ms cubic-bezier(.2,.8,.2,1);will-change:transform}
.mentor-review-mask{position:fixed;z-index:10;inset:0;padding:32rpx 20rpx calc(20rpx + env(safe-area-inset-bottom));background:rgba(19,37,66,.35);display:flex;align-items:flex-end}.mentor-review-sheet{width:100%;padding:20rpx 28rpx 28rpx;border-radius:30rpx;background:#fff;box-shadow:0 -16rpx 46rpx rgba(28,62,117,.16)}.mentor-review-handle{width:64rpx;height:7rpx;margin:0 auto 22rpx;border-radius:999rpx;background:#dce6f4}.mentor-review-title{color:#273a55;font-size:29rpx;font-weight:900}.mentor-review-subtitle{margin-top:7rpx;color:#8796aa;font-size:20rpx;line-height:1.45;font-weight:650}.mentor-review-stars{display:flex;gap:12rpx;margin-top:22rpx}.mentor-review-stars button{width:54rpx;height:54rpx;margin:0;padding:0;border:0;background:transparent;display:flex;align-items:center;justify-content:center}.mentor-review-stars button image{display:block;width:42rpx;height:42rpx}.mentor-review-stars button::after,.mentor-review-tags button::after,.mentor-review-submit::after{border:0}.mentor-review-tags{display:flex;flex-wrap:wrap;gap:10rpx;margin-top:18rpx}.mentor-review-tags button{min-height:48rpx;margin:0;padding:0 15rpx;border:2rpx solid #dce7f8;border-radius:14rpx;background:#fbfdff;color:#71839d;font-size:20rpx;font-weight:750}.mentor-review-tags button.active{border-color:#b9d2ff;background:#edf4ff;color:#3478f6}.mentor-review-sheet textarea{box-sizing:border-box;width:100%;min-height:144rpx;margin-top:20rpx;padding:16rpx;border:2rpx solid #e0eafa;border-radius:18rpx;background:#fbfdff;color:#3a4f6e;font-size:21rpx;line-height:1.5}.mentor-review-count{margin-top:7rpx;color:#9aa9ba;text-align:right;font-size:18rpx}.mentor-review-submit{width:100%;min-height:72rpx;margin-top:16rpx;border:0;border-radius:20rpx;background:#3478f6;color:#fff;font-size:24rpx;font-weight:900;box-shadow:0 10rpx 22rpx rgba(52,120,246,.2)}
@media(max-width:350px){.mentor-chat-completed-bar{grid-template-columns:minmax(0,1fr) 142rpx 98rpx}.mentor-chat-completed-bar button{font-size:17rpx}.mentor-chat-input-bar{gap:7rpx;padding-right:12rpx;padding-left:12rpx}.mentor-chat-tool{width:54rpx;min-width:54rpx;height:54rpx;min-height:54rpx;padding:8rpx}.mentor-chat-send{min-width:100rpx;font-size:21rpx}}
.mentor-chat-page { background: var(--gyt-page-bg); }
.mentor-chat-text-hint{margin:15rpx 4rpx 0;color:#8192a8;font-size:18rpx;line-height:1.5;font-weight:650}
.mentor-chat-completion-bar{padding:16rpx 20rpx calc(18rpx + env(safe-area-inset-bottom));border-top:2rpx solid var(--gyt-primary-border,#dbe7f8);background:var(--gyt-primary-tint,rgba(255,255,255,.98));display:grid;grid-template-columns:minmax(0,1fr) 156rpx;align-items:center;gap:14rpx}.mentor-chat-completion-bar.confirmed{background:#f7fbff}.mentor-chat-completion-bar>view{min-width:0}.mentor-chat-completion-bar strong,.mentor-chat-completion-bar text{display:block}.mentor-chat-completion-bar strong{color:#31445f;font-size:22rpx;font-weight:900}.mentor-chat-completion-bar text{margin-top:5rpx;color:#8191a7;font-size:17rpx;line-height:1.4;font-weight:650}.mentor-chat-completion-bar button{box-sizing:border-box;height:66rpx;min-height:66rpx;margin:0;padding:0 10rpx;border:0;border-radius:17rpx;background:var(--gyt-primary-gradient,#3478f6);color:#fff;display:flex;align-items:center;justify-content:center;text-align:center;font-size:19rpx;line-height:1;font-weight:850;white-space:nowrap;box-shadow:0 8rpx 18rpx var(--gyt-primary-shadow,rgba(52,120,246,.18))}.mentor-chat-completion-bar button::after{border:0}.mentor-chat-completion-bar button.light{background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);box-shadow:none}
.mentor-chat-service-tip { border-color: rgba(229, 226, 224, .94); background: rgba(255, 255, 255, .94); color: var(--gyt-primary, #3478f6); box-shadow: 0 8rpx 20rpx rgba(48, 42, 38, .035); }
.mentor-chat-service-tip.ended { border-color: rgba(229, 226, 224, .94); background: rgba(255, 255, 255, .94); }
.mentor-chat-context-card { border-color: rgba(229, 226, 224, .94); background: rgba(255, 255, 255, .94); box-shadow: 0 10rpx 24rpx rgba(48, 42, 38, .045); }
.mentor-chat-avatar.tone-blue,.mentor-chat-tool,.mentor-chat-more,.mentor-chat-completed-bar button.light,.mentor-review-tags button.active { background: var(--gyt-primary-soft, #edf4ff); color: var(--gyt-primary, #3478f6); }
.mentor-chat-message-row.user .mentor-chat-bubble,.mentor-chat-send,.mentor-chat-completed-bar button:not(.light),.mentor-review-submit { background: var(--gyt-primary-gradient, #3478f6); box-shadow: 0 8rpx 18rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.18)); }
.mentor-chat-input-bar,.mentor-chat-completed-bar { border-color: var(--gyt-primary-border, #dbe7f8); background: var(--gyt-primary-tint, #ffffff); }
.mentor-chat-input-bar input,.mentor-chat-voice-hold,.mentor-review-sheet textarea { border-color: var(--gyt-primary-border, #e0eafa); background: var(--gyt-primary-tint, #fbfdff); }
.mentor-chat-input-bar input:disabled { border-color: #e7edf6; background: #f4f7fb; color: #9aa9bd; }
.mentor-chat-voice-hold.recording,.mentor-review-tags button.active { border-color: var(--gyt-primary-border, #b9d2ff); }
.mentor-chat-time { min-height: 22rpx; display: flex; align-items: center; gap: 10rpx; }
.mentor-chat-message-row.user .mentor-chat-time { justify-content: flex-end; }
.mentor-chat-delivery { white-space: nowrap; }
.mentor-chat-delivery.sending { color: #8291a5; }
.mentor-chat-delivery.failed { color: #cf5b63; font-weight: 800; }
.mentor-chat-history-load{margin:16rpx auto 2rpx;text-align:center}.mentor-chat-history-load button{min-height:54rpx;margin:0;padding:0 22rpx;border:0;border-radius:999rpx;background:var(--gyt-primary-soft,#edf4ff);color:var(--gyt-primary,#3478f6);font-size:19rpx;line-height:54rpx;font-weight:800}.mentor-chat-history-load button::after{border:0}

/* 移动端聊天优先保留对话空间，咨询资料按需展开。 */
.mentor-chat-service-tip {
  box-sizing: border-box;
  min-height: 66rpx;
  margin: 12rpx 18rpx 0;
  padding: 11rpx 15rpx;
  border-radius: 20rpx;
}

.mentor-chat-service-tip .mentor-chat-service-main {
  min-width: 0;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10rpx;
  color: inherit;
  font-size: 20rpx;
  line-height: 1.3;
  font-weight: 850;
  white-space: normal;
}

.mentor-chat-service-main text {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mentor-chat-service-tip .mentor-chat-service-dot {
  width: 12rpx;
  height: 12rpx;
  flex: 0 0 12rpx;
  border-radius: 50%;
  background: var(--gyt-primary, #3478f6);
  box-shadow: 0 0 0 6rpx var(--gyt-primary-soft, #dce9ff);
}

.mentor-chat-service-tip.ended .mentor-chat-service-dot {
  background: #93a2b5;
  box-shadow: 0 0 0 6rpx #e8edf4;
}

.mentor-chat-service-detail {
  max-width: 42%;
  overflow: hidden;
  color: #7690ba;
  font-size: 17rpx;
  line-height: 1.3;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mentor-chat-content {
  padding: 18rpx 18rpx 30rpx;
}

.mentor-chat-context-card {
  padding: 0;
  overflow: hidden;
}

.mentor-chat-context-toggle {
  min-height: 92rpx;
  padding: 18rpx 20rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.mentor-chat-context-heading {
  min-width: 0;
  flex: 1;
}

.mentor-chat-context-title {
  font-size: 23rpx;
}

.mentor-chat-context-summary {
  margin-top: 6rpx;
  overflow: hidden;
  color: #8b99ac;
  font-size: 18rpx;
  line-height: 1.3;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mentor-chat-context-arrow {
  width: 15rpx;
  height: 15rpx;
  flex: 0 0 15rpx;
  margin-right: 5rpx;
  border-right: 3rpx solid #91a1b5;
  border-bottom: 3rpx solid #91a1b5;
  transform: rotate(45deg) translateY(-3rpx);
  transition: transform 180ms ease;
}

.mentor-chat-context-arrow.expanded {
  transform: rotate(225deg) translate(-2rpx, -2rpx);
}

.mentor-chat-context-details {
  padding: 2rpx 20rpx 22rpx;
  border-top: 2rpx solid rgba(78, 113, 151, 0.08);
}

.mentor-chat-context-details .mentor-chat-context-line:first-child {
  margin-top: 18rpx;
}

.mentor-chat-context-line strong {
  max-width: 68%;
  overflow-wrap: anywhere;
}

.mentor-chat-input-bar {
  position: relative;
  padding: 12rpx 16rpx calc(14rpx + env(safe-area-inset-bottom));
  border-top-color: rgba(97, 126, 166, 0.12);
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 -10rpx 28rpx rgba(44, 75, 119, 0.07);
  -webkit-backdrop-filter: blur(18rpx);
  backdrop-filter: blur(18rpx);
}

.mentor-chat-input-bar input {
  height: 76rpx;
  padding: 0 22rpx;
  border-color: transparent;
  border-radius: 24rpx;
  background: #f1f5fa;
  font-size: 22rpx;
}

.mentor-chat-input-bar:focus-within input {
  border-color: var(--gyt-primary-border, #c8daf8);
  background: #ffffff;
}

.mentor-chat-send {
  min-width: 108rpx;
  height: 68rpx;
  border-radius: 22rpx;
  font-size: 22rpx;
}

@media (max-width: 350px) {
  .mentor-chat-service-tip {
    margin-right: 14rpx;
    margin-left: 14rpx;
  }

  .mentor-chat-service-detail {
    max-width: 36%;
  }

  .mentor-chat-content {
    padding-right: 14rpx;
    padding-left: 14rpx;
  }

  .mentor-chat-input-bar {
    padding-right: 12rpx;
    padding-left: 12rpx;
  }

  .mentor-chat-send {
    min-width: 96rpx;
  }
}
</style>
