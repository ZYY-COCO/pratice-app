<template>
  <view class="mentor-chat-page">
    <MentorPageHeader
      :title="chatTitle"
      :subtitle="mentor ? `✓ 已认证 · ${mentor.school} · ${mentor.major}` : ''"
      @back="goBack"
    >
      <template #right><button class="mentor-chat-more" @tap="showMore">•••</button></template>
    </MentorPageHeader>

    <view v-if="mentor" class="mentor-chat-service-tip" :class="{ ended: consultationEnded }">
      <text>{{ consultationEnded ? '历史聊天记录' : `本次咨询窗口剩余 ${serviceCountdownText}` }}</text>
      <view>{{ consultationEnded ? '本次咨询已结束 · 仅供查阅' : `服务时间：${consultationWindowMinutes}分钟` }}</view>
    </view>

    <scroll-view scroll-y class="mentor-chat-scroll" :scroll-into-view="scrollTarget" scroll-with-animation>
      <view v-if="mentor" class="mentor-chat-content">
        <view class="mentor-chat-context-card">
          <view class="mentor-chat-context-title">{{ isMentorViewer ? '考生咨询信息' : '我的情况' }}</view>
          <view class="mentor-chat-context-line"><text>当前学校</text><strong>{{ questionnaire.school || '天津科技大学' }}</strong></view>
          <view class="mentor-chat-context-line"><text>当前专业</text><strong>{{ questionnaire.major || '金融学' }}</strong></view>
          <view class="mentor-chat-context-line"><text>当前年级</text><strong>{{ questionnaire.grade || '大三' }}</strong></view>
          <view class="mentor-chat-context-line"><text>预计毕业</text><strong>{{ questionnaire.graduationYear || '2027' }}年</strong></view>
          <view class="mentor-chat-context-question"><text>咨询问题</text><view>{{ questionnaire.question || defaultQuestion }}</view></view>
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
              <view class="mentor-chat-bubble" :class="message.type">
                <template v-if="message.type === 'voice'">▶ <text>{{ message.duration || '00:12' }} 语音消息</text></template>
                <template v-else-if="message.type === 'image'"><view class="mentor-chat-image-placeholder">咨询图片（示意）</view></template>
                <template v-else>{{ message.content }}</template>
              </view>
              <view class="mentor-chat-time">{{ formatTime(message.createdAt) }}</view>
            </view>
          </view>
        </template>
        <view id="mentor-chat-bottom" class="mentor-chat-bottom-anchor"></view>
      </view>
    </scroll-view>

    <view v-if="mentor && consultationEnded" class="mentor-chat-completed-bar" :class="{ mentor: isMentorViewer }">
      <view><strong>本次咨询已结束</strong><text>感谢你的信任，聊天记录已保留。</text></view>
      <template v-if="isMentorViewer">
        <button @tap="goBack">返回咨询主页</button>
      </template>
      <template v-else>
        <button :disabled="reviewSubmitted" @tap="openReview">{{ reviewSubmitted ? '已评价' : '评价本次咨询' }}</button>
        <button class="light" @tap="consultAgain">再次咨询</button>
      </template>
    </view>

    <view v-else-if="mentor" class="mentor-chat-input-bar" :class="{ voice: voiceInputMode }">
      <button
        class="mentor-chat-tool mentor-chat-mode-toggle"
        :aria-label="voiceInputMode ? '切换键盘输入' : '切换语音输入'"
        @tap="toggleInputMode"
      >
        <image :src="voiceInputMode ? '/static/ui-icons/mentor-chat-keyboard.svg' : '/static/ui-icons/mentor-chat-voice.svg'" mode="aspectFit" />
      </button>
      <button
        v-if="voiceInputMode"
        class="mentor-chat-voice-hold"
        :class="{ recording: voiceRecording }"
        @touchstart.stop="startVoiceRecording"
        @touchend.stop="finishVoiceRecording"
        @touchcancel.stop="cancelVoiceRecording"
      >{{ voiceRecording ? '松开发送' : '按住说话' }}</button>
      <input
        v-else
        v-model="messageInput"
        :placeholder="isMentorViewer ? '输入回复内容' : '输入想继续咨询的问题'"
        placeholder-class="mentor-chat-placeholder"
        confirm-type="send"
        @confirm="sendText"
      />
      <button class="mentor-chat-tool" aria-label="发送图片" @tap="sendImage">
        <image src="/static/ui-icons/mentor-chat-add.svg" mode="aspectFit" />
      </button>
      <button v-if="!voiceInputMode" class="mentor-chat-send" :disabled="!messageInput.trim()" @tap="sendText">发送</button>
    </view>

    <view
      v-if="voiceWaveVisible"
      class="mentor-chat-recording-overlay"
      :class="{ ending: !voiceRecording }"
      aria-live="polite"
    >
      <view class="mentor-chat-recording-bubble">
        <view class="mentor-chat-waveform" aria-hidden="true">
          <view
            v-for="(height, index) in voiceWaveHeights"
            :key="index"
            class="mentor-chat-wave-bar"
            :style="{ transform: 'scaleY(' + height + ')' }"
          ></view>
        </view>
      </view>
    </view>

    <view v-if="!isMentorViewer && reviewVisible" class="mentor-review-mask" @tap="closeReview">
      <view class="mentor-review-sheet" @tap.stop>
        <view class="mentor-review-handle"></view>
        <view class="mentor-review-title">评价本次咨询</view>
        <view class="mentor-review-subtitle">你的反馈会帮助更多同学找到合适的前辈。</view>
        <view class="mentor-review-stars">
          <button v-for="star in 5" :key="star" :class="{ active: reviewRating >= star }" @tap="reviewRating = star">★</button>
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
import { onLoad, onShow } from '@dcloudio/uni-app'
import MentorPageHeader from '../../components/MentorPageHeader.vue'
import {
  completeMentorConsultationOrder,
  createMentorConsultationMessage,
  createMentorConsultationReview,
  fetchMentorProfile,
  fetchMentorConsultationMessages,
  fetchMentorConsultationOrder
} from '../../api/mentorConsultation'
import {
  cacheMentors,
  getConsultationDraft,
  getMentorById,
  normalizeMentorDetailResponse,
  saveConsultationOrder
} from '../../data/mentorConsultation'

const VOICE_WAVE_MIN_SCALE = 0.11
const VOICE_WAVE_PROFILE = [0.18, 0.26, 0.37, 0.51, 0.68, 0.84, 0.96, 1, 0.96, 0.84, 0.68, 0.51, 0.37, 0.26, 0.18]

const mentor = ref(null)
const viewerRole = ref('applicant')
const questionnaire = ref({})
const messages = ref([])
const messageInput = ref('')
const orderId = ref('')
const orderStatus = ref('in_progress')
const startedAt = ref('')
const consultationWindowMinutes = ref(60)
const consultationEnded = ref(false)
const remainingServiceSeconds = ref(0)
const scrollTarget = ref('mentor-chat-bottom')
const reviewVisible = ref(false)
const reviewRating = ref(5)
const selectedReviewTags = ref([])
const reviewText = ref('')
const reviewSubmitted = ref(false)
const submittingReview = ref(false)
const finishing = ref(false)
const voiceInputMode = ref(false)
const voiceRecording = ref(false)
const voiceRecordingStartedAt = ref(0)
const voiceWaveVisible = ref(false)
const voiceWaveHeights = ref(createVoiceWaveHeights())
let serviceTimer = null
let messagePollTimer = null
let voiceAudioStream = null
let voiceAudioContext = null
let voiceAudioSource = null
let voiceAudioAnalyser = null
let voiceAudioSamples = null
let voiceWaveFrame = null
let voiceWaveCollapseFrame = null
let voiceLastMeterFrameAt = 0
let voiceSmoothedLevel = 0
let voiceRecordingSession = 0

const reviewTags = ['解答清晰', '回复及时', '很有帮助', '经验丰富', '建议具体']
const defaultQuestion = '我准备报考暨南大学应用经济学，目前比较纠结 Z001 的复习安排，希望了解前辈当时的复习节奏。'
const isMentorViewer = computed(() => viewerRole.value === 'mentor')
const chatTitle = computed(() => {
  if (!mentor.value) return '咨询聊天'
  return consultationEnded.value ? `${mentor.value.maskedName} · 聊天记录` : `${mentor.value.maskedName} · 咨询中`
})
const serviceCountdownText = computed(() => {
  const minutes = String(Math.floor(Math.max(0, remainingServiceSeconds.value) / 60)).padStart(2, '0')
  const seconds = String(Math.max(0, remainingServiceSeconds.value) % 60).padStart(2, '0')
  return `${minutes}:${seconds}`
})

onLoad((options) => {
  const draft = getConsultationDraft()
  viewerRole.value = options?.role === 'mentor' ? 'mentor' : 'applicant'
  orderId.value = String(options?.orderId || draft?.orderId || '')
  const mentorId = options?.mentorId || draft?.mentorId
  mentor.value = getMentorById(mentorId)
  if (!orderId.value) {
    uni.showToast({ title: '未找到咨询订单，请返回重新进入', icon: 'none' })
    return
  }
  void loadMentor(mentorId)
  void loadChatData()
})

onShow(() => {
  if (orderId.value) void loadChatData({ silent: true })
})

onBeforeUnmount(() => {
  stopChatTimers()
  stopVoiceRecordingResources({ hideImmediately: true })
})

async function loadChatData({ silent = false } = {}) {
  if (!orderId.value) return
  try {
    const [order, messagePayload] = await Promise.all([
      fetchMentorConsultationOrder(orderId.value),
      fetchMentorConsultationMessages(orderId.value)
    ])
    applyOrder(order)
    const incoming = Array.isArray(messagePayload?.items) ? messagePayload.items : []
    messages.value = incoming.map(normalizeMessage)
    scrollToBottom()
  } catch (error) {
    if (!silent) uni.showToast({ title: error?.detail || '咨询聊天加载失败', icon: 'none' })
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
  startedAt.value = draft.startedAt || ''
  consultationWindowMinutes.value = Number(draft.consultationWindowMinutes) || 60
  consultationEnded.value = orderStatus.value === 'completed'
  if (consultationEnded.value) {
    remainingServiceSeconds.value = 0
    stopChatTimers()
    stopVoiceRecordingResources({ hideImmediately: true })
    return
  }
  syncServiceRemainingSeconds()
  startServiceTimer()
  startMessagePolling()
}

function normalizeMessage(message = {}) {
  const senderRole = String(message.sender || message.sender_role || 'system')
  return {
    id: String(message.id || `local-${Date.now()}`),
    sender: senderRole === 'applicant' ? 'user' : senderRole,
    type: String(message.type || message.message_type || 'text'),
    content: String(message.content || ''),
    duration: message.duration || (message.duration_seconds ? formatDuration(message.duration_seconds) : ''),
    createdAt: message.createdAt || message.created_at || Date.now()
  }
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
  if (serviceTimer || consultationEnded.value) return
  serviceTimer = setInterval(() => {
    syncServiceRemainingSeconds()
    if (remainingServiceSeconds.value <= 0) void finishConsultation({ silent: true })
  }, 1000)
}

function startMessagePolling() {
  if (messagePollTimer || consultationEnded.value) return
  messagePollTimer = setInterval(() => {
    void loadChatData({ silent: true })
  }, 5000)
}

function stopChatTimers() {
  if (serviceTimer) clearInterval(serviceTimer)
  if (messagePollTimer) clearInterval(messagePollTimer)
  serviceTimer = null
  messagePollTimer = null
}

async function sendText() {
  const content = messageInput.value.trim()
  if (!content || consultationEnded.value || !orderId.value) return
  try {
    const message = await createMentorConsultationMessage(orderId.value, { message_type: 'text', content })
    messages.value = [...messages.value, normalizeMessage(message)]
    messageInput.value = ''
    scrollToBottom()
  } catch (error) {
    uni.showToast({ title: error?.detail || '消息发送失败', icon: 'none' })
  }
}

function toggleInputMode() {
  if (consultationEnded.value) return
  stopVoiceRecordingResources({ hideImmediately: true })
  voiceInputMode.value = !voiceInputMode.value
  if (voiceInputMode.value) messageInput.value = ''
}

async function startVoiceRecording() {
  if (!voiceInputMode.value || consultationEnded.value || voiceRecording.value) return
  cancelVoiceWaveCollapse()
  const session = ++voiceRecordingSession
  voiceRecordingStartedAt.value = Date.now()
  voiceRecording.value = true
  voiceWaveVisible.value = true
  voiceWaveHeights.value = createVoiceWaveHeights()
  voiceSmoothedLevel = 0

  const meterStarted = await startLiveVoiceMeter(session)
  if (!meterStarted && session === voiceRecordingSession && voiceRecording.value) {
    stopVoiceRecordingResources()
    uni.showToast({ title: '请允许麦克风权限后再录音', icon: 'none' })
  }
}

function finishVoiceRecording() {
  if (!voiceRecording.value) return
  const durationSeconds = Math.max(1, Math.round((Date.now() - voiceRecordingStartedAt.value) / 1000))
  stopVoiceRecordingResources()
  appendLocalDemoMessage({ type: 'voice', duration: formatDuration(durationSeconds) })
  uni.showToast({ title: '语音消息已发送（本地演示）', icon: 'none' })
}

function cancelVoiceRecording() {
  if (!voiceRecording.value && !voiceWaveVisible.value) return
  const wasRecording = voiceRecording.value
  stopVoiceRecordingResources()
  if (wasRecording) uni.showToast({ title: '已取消语音录制', icon: 'none' })
}

function createVoiceWaveHeights(scale = VOICE_WAVE_MIN_SCALE) {
  return VOICE_WAVE_PROFILE.map(() => scale)
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value))
}

async function startLiveVoiceMeter(session) {
  const canReadMicrophone = typeof window !== 'undefined'
    && typeof navigator !== 'undefined'
    && navigator.mediaDevices
    && typeof navigator.mediaDevices.getUserMedia === 'function'
  if (!canReadMicrophone) return false

  let stream = null
  let audioContext = null
  try {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true
      }
    })
    if (session !== voiceRecordingSession || !voiceRecording.value) {
      stream.getTracks().forEach((track) => track.stop())
      return false
    }

    const AudioContextConstructor = window.AudioContext || window.webkitAudioContext
    if (!AudioContextConstructor) {
      stream.getTracks().forEach((track) => track.stop())
      return false
    }

    audioContext = new AudioContextConstructor()
    if (audioContext.state === 'suspended') await audioContext.resume()
    if (session !== voiceRecordingSession || !voiceRecording.value) {
      stream.getTracks().forEach((track) => track.stop())
      if (audioContext.state !== 'closed') void audioContext.close()
      return false
    }

    const analyser = audioContext.createAnalyser()
    analyser.fftSize = 512
    analyser.smoothingTimeConstant = 0.78
    const source = audioContext.createMediaStreamSource(stream)
    source.connect(analyser)

    voiceAudioStream = stream
    voiceAudioContext = audioContext
    voiceAudioSource = source
    voiceAudioAnalyser = analyser
    voiceAudioSamples = new Uint8Array(analyser.fftSize)
    voiceLastMeterFrameAt = 0
    startVoiceWaveLoop(session)
    return true
  } catch (error) {
    if (stream) stream.getTracks().forEach((track) => track.stop())
    if (audioContext && audioContext.state !== 'closed') void audioContext.close()
    return false
  }
}

function startVoiceWaveLoop(session) {
  if (typeof window === 'undefined' || typeof window.requestAnimationFrame !== 'function') return
  const render = (timestamp) => {
    if (session !== voiceRecordingSession || !voiceRecording.value || !voiceAudioAnalyser || !voiceAudioSamples) return
    if (!voiceLastMeterFrameAt || timestamp - voiceLastMeterFrameAt >= 33) {
      voiceLastMeterFrameAt = timestamp
      voiceAudioAnalyser.getByteTimeDomainData(voiceAudioSamples)
      let sum = 0
      for (let index = 0; index < voiceAudioSamples.length; index += 1) {
        const sample = (voiceAudioSamples[index] - 128) / 128
        sum += sample * sample
      }
      const rms = Math.sqrt(sum / voiceAudioSamples.length)
      const rawLevel = clamp((rms - 0.008) * 10, 0, 1)
      const targetLevel = Math.pow(rawLevel, 0.62)
      const levelSmoothing = targetLevel > voiceSmoothedLevel ? 0.32 : 0.22
      voiceSmoothedLevel += (targetLevel - voiceSmoothedLevel) * levelSmoothing
      updateVoiceWaveHeights(timestamp)
    }
    voiceWaveFrame = window.requestAnimationFrame(render)
  }
  voiceWaveFrame = window.requestAnimationFrame(render)
}

function updateVoiceWaveHeights(timestamp) {
  const level = voiceSmoothedLevel
  voiceWaveHeights.value = VOICE_WAVE_PROFILE.map((profile, index) => {
    const current = voiceWaveHeights.value[index] ?? VOICE_WAVE_MIN_SCALE
    const motion = (Math.sin(timestamp / 96 + index * 1.37) + Math.sin(timestamp / 151 + index * 0.73)) * 0.035 * level
    const target = clamp(VOICE_WAVE_MIN_SCALE + level * (0.12 + profile * 0.82) + motion, VOICE_WAVE_MIN_SCALE, 1)
    const barSmoothing = target > current ? 0.36 : 0.22
    return current + (target - current) * barSmoothing
  })
}

function stopVoiceRecordingResources({ hideImmediately = false } = {}) {
  voiceRecordingSession += 1
  voiceRecording.value = false
  disconnectLiveVoiceMeter()
  if (hideImmediately) {
    cancelVoiceWaveCollapse()
    voiceWaveVisible.value = false
    voiceWaveHeights.value = createVoiceWaveHeights()
    return
  }
  collapseVoiceWaveform()
}

function disconnectLiveVoiceMeter() {
  if (voiceWaveFrame !== null && typeof window !== 'undefined' && typeof window.cancelAnimationFrame === 'function') {
    window.cancelAnimationFrame(voiceWaveFrame)
  }
  voiceWaveFrame = null
  if (voiceAudioSource) voiceAudioSource.disconnect()
  if (voiceAudioStream) voiceAudioStream.getTracks().forEach((track) => track.stop())
  if (voiceAudioContext && voiceAudioContext.state !== 'closed') void voiceAudioContext.close()
  voiceAudioStream = null
  voiceAudioContext = null
  voiceAudioSource = null
  voiceAudioAnalyser = null
  voiceAudioSamples = null
  voiceLastMeterFrameAt = 0
  voiceSmoothedLevel = 0
}

function collapseVoiceWaveform() {
  if (!voiceWaveVisible.value) return
  cancelVoiceWaveCollapse()
  if (typeof window === 'undefined' || typeof window.requestAnimationFrame !== 'function') {
    voiceWaveHeights.value = createVoiceWaveHeights()
    voiceWaveVisible.value = false
    return
  }
  const startingHeights = [...voiceWaveHeights.value]
  const startedAt = performance.now()
  const duration = 160
  const render = (timestamp) => {
    const progress = Math.min(1, (timestamp - startedAt) / duration)
    const eased = 1 - Math.pow(1 - progress, 3)
    voiceWaveHeights.value = startingHeights.map((height) => height + (VOICE_WAVE_MIN_SCALE - height) * eased)
    if (progress < 1) {
      voiceWaveCollapseFrame = window.requestAnimationFrame(render)
      return
    }
    voiceWaveCollapseFrame = null
    voiceWaveHeights.value = createVoiceWaveHeights()
    voiceWaveVisible.value = false
  }
  voiceWaveCollapseFrame = window.requestAnimationFrame(render)
}

function cancelVoiceWaveCollapse() {
  if (voiceWaveCollapseFrame !== null && typeof window !== 'undefined' && typeof window.cancelAnimationFrame === 'function') {
    window.cancelAnimationFrame(voiceWaveCollapseFrame)
  }
  voiceWaveCollapseFrame = null
}

function sendImage() {
  if (consultationEnded.value) return
  appendLocalDemoMessage({ type: 'image' })
  uni.showToast({ title: '图片消息上传仍为本地演示', icon: 'none' })
}

function appendLocalDemoMessage(message = {}) {
  messages.value = [...messages.value, {
    id: `local-${Date.now()}-${messages.value.length}`,
    sender: isMentorViewer.value ? 'mentor' : 'user',
    createdAt: Date.now(),
    ...message
  }]
  scrollToBottom()
}

async function finishConsultation({ silent = false } = {}) {
  if (consultationEnded.value || finishing.value || !orderId.value) return
  finishing.value = true
  try {
    const order = await completeMentorConsultationOrder(orderId.value)
    applyOrder(order)
    await loadChatData({ silent: true })
    scrollToBottom()
  } catch (error) {
    if (!silent) uni.showToast({ title: error?.detail || '结束咨询失败', icon: 'none' })
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

function formatDuration(seconds) {
  const value = Math.max(0, Number(seconds) || 0)
  return `${String(Math.floor(value / 60)).padStart(2, '0')}:${String(value % 60).padStart(2, '0')}`
}

function showMore() {
  const itemList = ['查看咨询规则', '举报此咨询']
  uni.showActionSheet({
    itemList,
    success: ({ tapIndex }) => {
      if (tapIndex === 1) openReport()
    }
  })
}

function openReport() {
  if (!orderId.value) return
  const targetRole = isMentorViewer.value ? 'applicant' : 'mentor'
  uni.navigateTo({
    url: `/pages/circle/mentor-report?orderId=${encodeURIComponent(orderId.value)}&mentorId=${encodeURIComponent(mentor.value?.id || '')}&reporterRole=${isMentorViewer.value ? 'mentor' : 'applicant'}&targetRole=${targetRole}`
  })
}

function openReview() {
  if (!isMentorViewer.value && !reviewSubmitted.value) reviewVisible.value = true
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
  if (submittingReview.value || !orderId.value) return
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
  uni.navigateTo({ url: `/pages/circle/mentor-consult-form?mentorId=${encodeURIComponent(mentor.value.id)}&mode=instant` })
}
function goBack() {
  uni.navigateBack({ fail() { uni.reLaunch({ url: '/pages/home/index?tab=circle&section=community&communityTab=mentor' }) } })
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
.mentor-review-mask{position:fixed;z-index:10;inset:0;padding:32rpx 20rpx calc(20rpx + env(safe-area-inset-bottom));background:rgba(19,37,66,.35);display:flex;align-items:flex-end}.mentor-review-sheet{width:100%;padding:20rpx 28rpx 28rpx;border-radius:30rpx;background:#fff;box-shadow:0 -16rpx 46rpx rgba(28,62,117,.16)}.mentor-review-handle{width:64rpx;height:7rpx;margin:0 auto 22rpx;border-radius:999rpx;background:#dce6f4}.mentor-review-title{color:#273a55;font-size:29rpx;font-weight:900}.mentor-review-subtitle{margin-top:7rpx;color:#8796aa;font-size:20rpx;line-height:1.45;font-weight:650}.mentor-review-stars{display:flex;gap:12rpx;margin-top:22rpx}.mentor-review-stars button{width:54rpx;height:54rpx;margin:0;padding:0;border:0;background:transparent;color:#d3dce8;font-size:42rpx;line-height:1}.mentor-review-stars button::after,.mentor-review-tags button::after,.mentor-review-submit::after{border:0}.mentor-review-stars button.active{color:#f2a437}.mentor-review-tags{display:flex;flex-wrap:wrap;gap:10rpx;margin-top:18rpx}.mentor-review-tags button{min-height:48rpx;margin:0;padding:0 15rpx;border:2rpx solid #dce7f8;border-radius:14rpx;background:#fbfdff;color:#71839d;font-size:20rpx;font-weight:750}.mentor-review-tags button.active{border-color:#b9d2ff;background:#edf4ff;color:#3478f6}.mentor-review-sheet textarea{box-sizing:border-box;width:100%;min-height:144rpx;margin-top:20rpx;padding:16rpx;border:2rpx solid #e0eafa;border-radius:18rpx;background:#fbfdff;color:#3a4f6e;font-size:21rpx;line-height:1.5}.mentor-review-count{margin-top:7rpx;color:#9aa9ba;text-align:right;font-size:18rpx}.mentor-review-submit{width:100%;min-height:72rpx;margin-top:16rpx;border:0;border-radius:20rpx;background:#3478f6;color:#fff;font-size:24rpx;font-weight:900;box-shadow:0 10rpx 22rpx rgba(52,120,246,.2)}
@media(max-width:350px){.mentor-chat-completed-bar{grid-template-columns:minmax(0,1fr) 142rpx 98rpx}.mentor-chat-completed-bar button{font-size:17rpx}.mentor-chat-input-bar{gap:7rpx;padding-right:12rpx;padding-left:12rpx}.mentor-chat-tool{width:54rpx;min-width:54rpx;height:54rpx;min-height:54rpx;padding:8rpx}.mentor-chat-send{min-width:100rpx;font-size:21rpx}}
</style>
