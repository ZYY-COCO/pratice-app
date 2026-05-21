<template>
  <view class="ai-assistant">
    <button class="assistant-trigger" @tap="openPanel">
      <text class="trigger-dot"></text>
      <text>AI 助教</text>
    </button>

    <view v-if="visible" class="assistant-mask" @tap="closePanel">
      <view class="assistant-panel" @tap.stop>
        <view class="panel-handle"></view>

        <view class="panel-head">
          <view>
            <view class="panel-title">AI 助教</view>
            <view class="panel-subtitle">基于当前题目为你解答</view>
          </view>
          <button class="close-btn" @tap="closePanel">×</button>
        </view>

        <scroll-view class="panel-body" scroll-y>
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

          <view class="prompt-section">
            <view class="section-title">推荐提问</view>
            <button
              v-for="item in promptOptions"
              :key="item"
              class="prompt-chip"
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
              <view class="message-bubble">{{ message.content }}</view>
            </view>
          </view>
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
          <button class="send-btn" :disabled="!draft.trim() || sending" @tap="sendDraft">
            {{ sending ? '发送中' : '发送' }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { sendQuestionChat } from '../api/ai'

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

const moduleDisplay = computed(() => {
  const parts = [props.moduleName, props.submodule].filter(Boolean)
  return parts.length ? parts.join(' / ') : '未识别'
})

const promptOptions = computed(() =>
  props.submitted
    ? ['为什么正确答案是这个', '每个选项分别是什么意思', '这类题以后怎么判断']
    : ['给我一点解题思路', '这题考什么知识点', '可以用排除法分析吗']
)

function openPanel() {
  visible.value = true
}

function closePanel() {
  visible.value = false
}

function buildFallbackReply() {
  return '这是 AI 助教的测试回复，后续将接入真实接口。'
}

function pushAssistantReply(content) {
  messages.value.push({
    role: 'assistant',
    content: content || buildFallbackReply()
  })
}

async function requestAssistantReply(text) {
  if (!props.questionId || String(props.questionId).startsWith('mock-')) {
    pushAssistantReply(buildFallbackReply())
    return
  }

  sending.value = true
  try {
    const data = await sendQuestionChat({
      question_id: props.questionId,
      user_message: text,
      submitted: props.submitted,
      user_answer: props.selectedAnswer || null
    })
    pushAssistantReply(data?.reply || buildFallbackReply())
  } catch (error) {
    pushAssistantReply(error?.detail || 'AI 助教暂时无法连接，请稍后再试。')
  } finally {
    sending.value = false
  }
}

async function sendPrompt(text) {
  if (!text || sending.value) return
  messages.value.push({ role: 'user', content: text })
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
  }
)
</script>

<style scoped>
.ai-assistant {
  position: relative;
  z-index: 80;
}

.assistant-trigger {
  position: fixed;
  right: 24rpx;
  bottom: calc(250rpx + env(safe-area-inset-bottom));
  z-index: 80;
  display: inline-flex;
  align-items: center;
  gap: 10rpx;
  height: 76rpx;
  padding: 0 24rpx;
  border: 0;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #3478f6, #7c5cff);
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 800;
  box-shadow: 0 18rpx 34rpx rgba(52, 120, 246, 0.28);
}

.assistant-trigger::after {
  border: 0;
}

.trigger-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 999rpx;
  background: #dff7ff;
  box-shadow: 0 0 0 8rpx rgba(255, 255, 255, 0.16);
}

.assistant-mask {
  position: fixed;
  inset: 0;
  z-index: 100;
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
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18rpx 30rpx 22rpx;
  border-bottom: 2rpx solid #eef2f8;
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
  width: 64rpx;
  height: 64rpx;
  padding: 0;
  border: 0;
  border-radius: 999rpx;
  background: #f4f7fb;
  color: #667085;
  font-size: 40rpx;
  line-height: 64rpx;
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

.prompt-chip::after {
  border: 0;
}

.prompt-chip[disabled] {
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
  background: #3478f6;
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 72rpx;
}

.send-btn::after {
  border: 0;
}

.send-btn[disabled] {
  background: #c9d5ea;
  color: #ffffff;
}
</style>
