<template>
  <view class="ai-assistant">
    <view
      class="assistant-trigger-hitbox"
      :class="{ dragging: triggerDragging }"
      :style="assistantTriggerStyle"
      @tap="handleTriggerTap"
      @click="handleTriggerTap"
      @longpress="openPanel"
      @touchstart.stop="startTriggerDrag"
      @touchmove.stop.prevent="moveTriggerDrag"
      @touchend.stop="endTriggerDrag"
      @touchcancel.stop="endTriggerDrag"
    >
      <view class="assistant-trigger">
        <text>AI</text>
      </view>
    </view>

    <view v-if="visible" class="assistant-mask" @tap="closePanel">
      <view class="assistant-panel" @tap.stop>
        <view class="panel-handle"></view>

        <view class="panel-head">
          <view class="panel-title-block">
            <view class="panel-title">AI 助教</view>
            <view class="panel-subtitle">基于当前题目为你解答</view>
          </view>
          <button class="close-btn" hover-class="close-btn-active" @tap.stop="closePanel">
            <text class="close-icon">×</text>
          </button>
        </view>

        <scroll-view
          class="panel-body"
          scroll-y
          scroll-with-animation
          :scroll-into-view="assistantScrollTarget"
        >
          <view class="question-summary">
            <view class="summary-title">当前题目</view>
            <view class="summary-grid">
              <view class="summary-item">
                <text class="summary-label">科目</text>
                <text class="summary-value">{{ subject || '未识别' }}</text>
              </view>
              <view class="summary-item">
                <text class="summary-label">模块</text>
                <text class="summary-value">{{ moduleDisplay }}</text>
              </view>
              <view class="summary-item">
                <text class="summary-label">状态</text>
                <text class="summary-value">{{ submitted ? '已提交' : '未提交' }}</text>
              </view>
            </view>

            <view v-if="submitted" class="answer-row">
              <text>你的选择：{{ selectedAnswer || '-' }}</text>
              <text>正确答案：{{ correctAnswer || '-' }}</text>
            </view>
          </view>

          <view v-if="!messages.length" class="prompt-section">
            <view class="section-title">推荐提问</view>
            <button
              v-for="item in promptOptions"
              :key="item"
              class="prompt-chip"
              :class="{ disabled: sending }"
              :disabled="sending"
              @tap="sendPrompt(item)"
            >
              {{ item }}
            </button>
          </view>

          <view class="chat-section">
            <view v-if="!messages.length" class="empty-message">
              可以先问一个方向性问题，第一版会返回测试回复。
            </view>
            <view
              v-for="(message, index) in messages"
              :key="`${message.role}-${index}`"
              class="message-row"
              :class="message.role"
            >
              <view class="message-bubble">
                <template v-if="message.role === 'assistant'">
                  <MathText
                    v-for="(paragraph, paragraphIndex) in visibleAssistantParagraphs(message)"
                    :key="paragraphIndex"
                    class="assistant-message-text"
                    :class="{ 'paragraph-gap': paragraphIndex > 0 }"
                    :value="paragraph"
                  />
                  <button
                    v-if="shouldCollapseAssistantMessage(message)"
                    class="message-toggle"
                    @tap.stop="toggleAssistantMessage(index)"
                  >
                    {{ message.expanded ? '收起' : '展开完整解析' }}
                  </button>
                </template>
                <text v-else>{{ message.content }}</text>
              </view>
            </view>
            <view v-if="sending" class="message-row assistant">
              <view class="message-bubble thinking">AI 正在思考...</view>
            </view>
          </view>
          <view v-if="messages.length" class="prompt-section compact">
            <view class="section-title compact-title">继续追问</view>
            <view class="compact-prompt-list">
              <button
                v-for="item in promptOptions"
                :key="item"
                class="prompt-chip compact-chip"
                :class="{ disabled: sending }"
                :disabled="sending"
                @tap="sendPrompt(item)"
              >
                {{ item }}
              </button>
            </view>
          </view>
          <view id="ai-chat-bottom" class="chat-bottom-anchor"></view>
        </scroll-view>

        <view class="input-bar">
          <input
            v-model="draft"
            class="assistant-input"
            type="text"
            confirm-type="send"
            placeholder="向 AI 助教提问"
            @confirm="sendDraft"
          />
          <button class="send-btn" :class="{ ready: canSend, disabled: !canSend }" :disabled="!canSend" @tap="sendDraft">
            {{ sending ? '发送中' : '发送' }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { aiQuestionChat } from '../api/ai'
import MathText from './MathText.vue'

const props = defineProps({
  questionId: {
    type: String,
    default: ''
  },
  subject: {
    type: String,
    default: ''
  },
  moduleName: {
    type: String,
    default: ''
  },
  submodule: {
    type: String,
    default: ''
  },
  submitted: {
    type: Boolean,
    default: false
  },
  selectedAnswer: {
    type: String,
    default: ''
  },
  correctAnswer: {
    type: String,
    default: ''
  }
})

const visible = ref(false)
const draft = ref('')
const messages = ref([])
const sending = ref(false)
const assistantScrollTarget = ref('')
const triggerPosition = ref({ x: 0, y: 0 })
const triggerReady = ref(false)
const triggerDragging = ref(false)
const suppressNextTriggerTap = ref(false)
let triggerDragContext = null

const TRIGGER_STORAGE_KEY = 'aiAssistantTriggerPosition'
const COLLAPSED_PARAGRAPH_LIMIT = 4
const COLLAPSED_CHAR_LIMIT = 360

const moduleDisplay = computed(() => {
  const parts = [props.moduleName, props.submodule].filter(Boolean)
  return parts.length ? parts.join(' / ') : '未识别'
})

const promptOptions = computed(() =>
  props.submitted
    ? ['为什么正确答案是这个', '每个选项分别是什么意思', '这类题以后怎么判断']
    : ['给我一点解题思路', '这题考什么知识点', '可以用排除法分析吗']
)

const canSend = computed(() => Boolean(draft.value.trim()) && !sending.value)

const assistantTriggerStyle = computed(() =>
  triggerReady.value
    ? {
        left: `${triggerPosition.value.x}px`,
        top: `${triggerPosition.value.y}px`,
        right: 'auto',
        bottom: 'auto'
      }
    : {}
)

function getTriggerViewport() {
  const info = uni.getSystemInfoSync()
  return {
    width: Number(info.windowWidth) || 375,
    height: Number(info.windowHeight) || 667,
    size: uni.upx2px(116),
    margin: uni.upx2px(24),
    defaultBottom: uni.upx2px(250)
  }
}

function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max)
}

function clampTriggerPosition(position) {
  const viewport = getTriggerViewport()
  return {
    x: clamp(position.x, viewport.margin, viewport.width - viewport.size - viewport.margin),
    y: clamp(position.y, viewport.margin, viewport.height - viewport.size - viewport.margin)
  }
}

function getTouchPoint(event) {
  const touch = event?.touches?.[0] || event?.changedTouches?.[0]
  if (!touch) return null
  return {
    x: Number(touch.clientX),
    y: Number(touch.clientY)
  }
}

function snapTriggerToSide(position) {
  const viewport = getTriggerViewport()
  const leftX = viewport.margin
  const rightX = viewport.width - viewport.size - viewport.margin
  const centerX = position.x + viewport.size / 2
  return {
    x: centerX < viewport.width / 2 ? leftX : rightX,
    y: clamp(position.y, viewport.margin, viewport.height - viewport.size - viewport.margin)
  }
}

function saveTriggerPosition(position) {
  const viewport = getTriggerViewport()
  const side = position.x + viewport.size / 2 < viewport.width / 2 ? 'left' : 'right'
  uni.setStorageSync(TRIGGER_STORAGE_KEY, {
    side,
    y: position.y
  })
}

function initializeTriggerPosition() {
  const viewport = getTriggerViewport()
  let saved = null
  try {
    saved = uni.getStorageSync(TRIGGER_STORAGE_KEY)
  } catch (error) {
    saved = null
  }

  const defaultPosition = {
    x: viewport.width - viewport.size - viewport.margin,
    y: viewport.height - viewport.size - viewport.defaultBottom
  }
  const side = saved?.side === 'left' ? 'left' : 'right'
  const restoredPosition = saved && typeof saved.y === 'number'
    ? {
        x: side === 'left' ? viewport.margin : viewport.width - viewport.size - viewport.margin,
        y: saved.y
      }
    : defaultPosition

  triggerPosition.value = clampTriggerPosition(restoredPosition)
  triggerReady.value = true
}

function handleTriggerTap() {
  if (suppressNextTriggerTap.value) {
    suppressNextTriggerTap.value = false
    return
  }
  openPanel()
}

function startTriggerDrag(event) {
  const point = getTouchPoint(event)
  if (!point) return
  if (!triggerReady.value) initializeTriggerPosition()

  triggerDragging.value = true
  triggerDragContext = {
    startX: point.x,
    startY: point.y,
    offsetX: point.x - triggerPosition.value.x,
    offsetY: point.y - triggerPosition.value.y,
    moved: false
  }
}

function moveTriggerDrag(event) {
  const point = getTouchPoint(event)
  if (!point || !triggerDragContext) return

  const deltaX = Math.abs(point.x - triggerDragContext.startX)
  const deltaY = Math.abs(point.y - triggerDragContext.startY)
  if (deltaX > 12 || deltaY > 12) {
    triggerDragContext.moved = true
  }

  triggerPosition.value = clampTriggerPosition({
    x: point.x - triggerDragContext.offsetX,
    y: point.y - triggerDragContext.offsetY
  })
}

function endTriggerDrag() {
  if (!triggerDragContext) return

  const moved = triggerDragContext.moved
  triggerDragging.value = false
  triggerDragContext = null

  if (!moved) {
    openPanel()
  } else {
    const snappedPosition = snapTriggerToSide(triggerPosition.value)
    triggerPosition.value = snappedPosition
    saveTriggerPosition(snappedPosition)
  }

  suppressNextTriggerTap.value = true
  setTimeout(() => {
    suppressNextTriggerTap.value = false
  }, 250)
}

function openPanel() {
  visible.value = true
  scrollChatToBottom()
}

function closePanel() {
  visible.value = false
}

function buildFallbackReply() {
  return '这是 AI 助教的测试回复，后续将接入真实接口。'
}

function normalizeAssistantReply(content) {
  return String(content || '')
    .replace(/```[\s\S]*?```/g, (match) => match.replace(/```/g, ''))
    .replace(/`([^`]+)`/g, '$1')
    .replace(/^#{1,6}\s*/gm, '')
    .replace(/\*\*/g, '')
    .replace(/^\s*[-*]\s+/gm, '• ')
    .replace(/[ \t]+\n/g, '\n')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}

function splitAssistantParagraphs(content) {
  const normalized = normalizeAssistantReply(content || buildFallbackReply())
  return normalized.split(/\n+/).map((item) => item.trim()).filter(Boolean)
}

function getAssistantParagraphs(message) {
  return splitAssistantParagraphs(message?.content || '')
}

function shouldCollapseAssistantMessage(message) {
  if (!message || message.role !== 'assistant') return false
  const paragraphs = getAssistantParagraphs(message)
  return paragraphs.length > COLLAPSED_PARAGRAPH_LIMIT || String(message.content || '').length > COLLAPSED_CHAR_LIMIT
}

function visibleAssistantParagraphs(message) {
  const paragraphs = getAssistantParagraphs(message)
  if (!shouldCollapseAssistantMessage(message) || message.expanded) {
    return paragraphs
  }
  return paragraphs.slice(0, COLLAPSED_PARAGRAPH_LIMIT)
}

function toggleAssistantMessage(index) {
  const message = messages.value[index]
  if (!message || message.role !== 'assistant') return
  message.expanded = !message.expanded
  if (message.expanded) {
    scrollChatToBottom()
  }
}

function scrollChatToBottom() {
  assistantScrollTarget.value = ''
  nextTick(() => {
    assistantScrollTarget.value = 'ai-chat-bottom'
  })
}

function pushAssistantReply(content) {
  messages.value.push({
    role: 'assistant',
    content: normalizeAssistantReply(content || buildFallbackReply()),
    expanded: false
  })
  scrollChatToBottom()
}

async function requestAssistantReply(text) {
  if (!props.questionId || String(props.questionId).startsWith('mock-')) {
    pushAssistantReply(buildFallbackReply())
    return
  }

  sending.value = true
  scrollChatToBottom()
  try {
    const data = await aiQuestionChat({
      question_id: props.questionId,
      user_message: text,
      submitted: props.submitted,
      user_answer: props.selectedAnswer || null
    })
    pushAssistantReply(data?.reply || buildFallbackReply())
  } catch (error) {
    const detail = error?.detail || error?.message || '暂时无法连接 AI，请稍后再试'
    pushAssistantReply(detail)
  } finally {
    sending.value = false
  }
}

async function sendPrompt(text) {
  if (!text || sending.value) return
  messages.value.push({ role: 'user', content: text })
  scrollChatToBottom()
  await requestAssistantReply(text)
}

async function sendDraft() {
  const text = draft.value.trim()
  if (!text || sending.value) return
  draft.value = ''
  await sendPrompt(text)
}

watch(
  () => [props.questionId, props.subject, props.moduleName, props.submodule, props.submitted, props.selectedAnswer, props.correctAnswer],
  () => {
    draft.value = ''
    messages.value = []
    sending.value = false
    assistantScrollTarget.value = ''
  }
)

onMounted(() => {
  initializeTriggerPosition()
})
</script>

<style scoped>
.ai-assistant {
  position: relative;
  z-index: 80;
}

.assistant-trigger-hitbox {
  position: fixed;
  right: 24rpx;
  bottom: calc(250rpx + env(safe-area-inset-bottom));
  z-index: 180;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 116rpx;
  height: 116rpx;
  min-width: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  transition: left 0.18s ease, top 0.18s ease, transform 0.18s ease;
  touch-action: none;
  user-select: none;
}

.assistant-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 88rpx;
  height: 88rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #3478f6, #7c5cff);
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
  letter-spacing: 0;
  line-height: 88rpx;
  box-shadow: 0 18rpx 34rpx rgba(52, 120, 246, 0.3);
}

.assistant-trigger-hitbox.dragging {
  transform: scale(1.04);
  transition: none;
}

.assistant-trigger::after {
  border: 0;
}

.assistant-mask {
  position: fixed;
  inset: 0;
  z-index: 260;
  display: flex;
  align-items: flex-end;
  background: rgba(15, 23, 42, 0.22);
}

.assistant-panel {
  width: 100%;
  height: 70vh;
  max-height: 75vh;
  min-height: 65vh;
  display: flex;
  flex-direction: column;
  border-radius: 34rpx 34rpx 0 0;
  background: #ffffff;
  box-shadow: 0 -18rpx 48rpx rgba(15, 23, 42, 0.16);
  overflow: hidden;
}

.panel-handle {
  width: 72rpx;
  height: 8rpx;
  margin: 18rpx auto 4rpx;
  border-radius: 999rpx;
  background: #d8e0ed;
}

.panel-head {
  position: relative;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  min-height: 96rpx;
  padding: 20rpx 104rpx 24rpx 30rpx;
  border-bottom: 2rpx solid #eef2f8;
  box-sizing: border-box;
}

.panel-title-block {
  min-width: 0;
}

.panel-title {
  color: #172033;
  font-size: 32rpx;
  font-weight: 900;
}

.panel-subtitle {
  margin-top: 6rpx;
  color: #667085;
  font-size: 23rpx;
}

.close-btn {
  position: absolute;
  top: 22rpx;
  right: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56rpx;
  height: 56rpx;
  min-width: 0;
  padding: 0;
  border: 2rpx solid #e7edf7;
  border-radius: 999rpx;
  background: #ffffff;
  color: #8b95a8;
  font-size: 0;
  line-height: 1;
  box-shadow: 0 8rpx 20rpx rgba(15, 23, 42, 0.06);
}

.close-icon {
  color: inherit;
  font-size: 34rpx;
  font-weight: 700;
  line-height: 1;
  transform: translateY(-1rpx);
}

.close-btn-active {
  background: #eef5ff;
  border-color: #d5e4ff;
  color: #2f6fed;
}

.close-btn::after {
  border: 0;
}

.panel-body {
  flex: 1;
  min-height: 0;
  padding: 24rpx 30rpx;
  box-sizing: border-box;
}

.question-summary {
  padding: 24rpx;
  border-radius: 26rpx;
  background: #f7f9fd;
  border: 2rpx solid #e7edf7;
}

.summary-title,
.section-title {
  color: #172033;
  font-size: 25rpx;
  font-weight: 900;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 14rpx;
  margin-top: 18rpx;
}

.summary-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.summary-label {
  flex: 0 0 auto;
  color: #8b95a8;
  font-size: 22rpx;
}

.summary-value {
  color: #223254;
  font-size: 23rpx;
  font-weight: 800;
  text-align: right;
  word-break: break-all;
}

.answer-row {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  margin-top: 20rpx;
  padding-top: 18rpx;
  border-top: 2rpx dashed #dbe4f1;
  color: #475467;
  font-size: 22rpx;
}

.prompt-section,
.chat-section {
  margin-top: 26rpx;
}

.prompt-section.compact {
  margin-top: 18rpx;
  padding-top: 18rpx;
  border-top: 2rpx dashed #e7edf7;
}

.compact-title {
  color: #667085;
  font-size: 22rpx;
}

.compact-prompt-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 12rpx;
}

.prompt-chip {
  display: block;
  width: 100%;
  margin-top: 14rpx;
  padding: 18rpx 22rpx;
  border: 0;
  border-radius: 20rpx;
  background: #eef5ff;
  color: #2f6fed;
  font-size: 24rpx;
  font-weight: 800;
  text-align: left;
}

.compact-chip {
  display: inline-flex;
  width: auto;
  max-width: 100%;
  min-height: 56rpx;
  margin-top: 0;
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  background: #f4f7fb;
  color: #47617f;
  font-size: 21rpx;
  font-weight: 800;
  line-height: 1.3;
}

.prompt-chip::after {
  border: 0;
}

.prompt-chip.disabled {
  opacity: 0.62;
}

.empty-message {
  padding: 24rpx;
  border-radius: 22rpx;
  background: #fbfcff;
  border: 2rpx dashed #d8e0ed;
  color: #8b95a8;
  font-size: 23rpx;
  line-height: 1.6;
}

.chat-bottom-anchor {
  height: 2rpx;
}

.message-row {
  display: flex;
  margin-top: 16rpx;
}

.message-row.user {
  justify-content: flex-end;
}

.message-row.assistant {
  justify-content: flex-start;
}

.message-bubble {
  max-width: 78%;
  padding: 18rpx 22rpx;
  border-radius: 22rpx;
  color: #223254;
  font-size: 24rpx;
  line-height: 1.6;
  background: #f3f6fb;
}

.message-row.user .message-bubble {
  color: #ffffff;
  background: #3478f6;
}

.message-bubble.thinking {
  color: #667085;
  background: #f7f9fd;
}

.assistant-message-text {
  display: block;
  color: inherit;
  font-size: inherit;
  font-weight: inherit;
  line-height: inherit;
}

.assistant-message-text.paragraph-gap {
  margin-top: 12rpx;
}

.message-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  height: 48rpx;
  margin-top: 16rpx;
  padding: 0 18rpx;
  border: 0;
  border-radius: 999rpx;
  background: #ffffff;
  color: #2f6fed;
  font-size: 21rpx;
  font-weight: 900;
  line-height: 48rpx;
  box-shadow: inset 0 0 0 2rpx #dbe8ff;
}

.message-toggle::after {
  border: 0;
}

.input-bar {
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: 18rpx 24rpx calc(18rpx + env(safe-area-inset-bottom));
  border-top: 2rpx solid #eef2f8;
  background: #ffffff;
}

.assistant-input {
  flex: 1;
  height: 72rpx;
  padding: 0 22rpx;
  border-radius: 20rpx;
  background: #f5f7fb;
  color: #172033;
  font-size: 24rpx;
}

.send-btn {
  width: 128rpx;
  height: 72rpx;
  padding: 0;
  border: 0;
  border-radius: 20rpx;
  background: #c9d5ea;
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 72rpx;
  box-shadow: none;
  transition: background 0.18s ease, box-shadow 0.18s ease;
}

.send-btn::after {
  border: 0;
}

.send-btn.ready {
  background: linear-gradient(135deg, #3478f6, #6c5cff);
  box-shadow: 0 12rpx 24rpx rgba(52, 120, 246, 0.22);
}

.send-btn.disabled {
  color: #ffffff;
}
</style>
