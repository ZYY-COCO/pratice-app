<template>
  <view class="page history-page">
    <view class="history-topbar">
      <view class="back-btn" @tap="goBack">‹</view>
      <view class="top-title">练习历史</view>
      <view class="top-actions">
        <text class="top-icon">⌕</text>
        <text class="top-icon">⛃</text>
      </view>
    </view>

    <view class="filter-tabs">
      <button
        v-for="item in filters"
        :key="item.key"
        class="filter-tab"
        :class="{ active: activeFilter === item.key }"
        @tap="changeFilter(item.key)"
      >
        {{ item.label }}
      </button>
    </view>

    <view v-if="loading" class="state-card">正在读取你的真实练习记录...</view>
    <view v-else-if="error" class="state-card warning">{{ error }}</view>
    <view v-else-if="items.length === 0" class="state-card">
      暂无练习历史。完成一组刷题后，这里会自动记录你的答题情况。
    </view>

    <view v-else class="history-list">
      <view v-for="item in items" :key="item.id" class="history-card" @tap="openDetail(item)">
        <view class="card-head">
          <view class="card-title">{{ getTitle(item) }}</view>
          <view class="result-pill" :class="{ wrong: !item.is_correct }">
            {{ item.is_correct ? '✓ 答对' : '× 答错' }}
          </view>
        </view>
        <view class="stem">{{ item.question?.stem || '题目内容暂不可用' }}</view>
        <view class="answer-row">
          <text>{{ formatTime(item.created_at) }}</text>
          <text>我的答案：{{ item.selected_answer || '--' }}</text>
        </view>
        <view v-if="!item.is_correct" class="correct-row">
          <text>正确答案：{{ item.question?.answer || '--' }}</text>
          <text class="detail-link">查看解析 ›</text>
        </view>
      </view>
    </view>

    <view v-if="selectedItem" class="detail-mask" @tap="closeDetail">
      <view class="detail-panel" @tap.stop>
        <view class="detail-head">
          <view>
            <view class="detail-title">答题详情</view>
            <view class="detail-sub">{{ getTitle(selectedItem) }}</view>
          </view>
          <view class="close-btn" @tap="closeDetail">×</view>
        </view>
        <view class="detail-stem">{{ selectedItem.question?.stem }}</view>
        <view class="option-list">
          <view
            v-for="option in selectedOptions"
            :key="option.key"
            class="option-row"
            :class="getOptionClass(option.key)"
          >
            <text class="option-key">{{ option.key }}</text>
            <text class="option-text">{{ option.text }}</text>
          </view>
        </view>
        <view class="explanation">
          <view class="explain-title">解析</view>
          <view class="explain-text">{{ selectedItem.question?.explanation || '暂无解析' }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { fetchAnswerHistory } from '../../api/answers'

const filters = [
  { key: 'all', label: '全部' },
  { key: 'correct', label: '答对' },
  { key: 'wrong', label: '答错' }
]

const activeFilter = ref('all')
const loading = ref(false)
const error = ref('')
const items = ref([])
const selectedItem = ref(null)

const selectedOptions = computed(() => buildOptions(selectedItem.value?.question))

onShow(() => {
  loadHistory()
})

function changeFilter(key) {
  if (activeFilter.value === key) return
  activeFilter.value = key
  loadHistory()
}

async function loadHistory() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetchAnswerHistory({
      status: activeFilter.value,
      limit: 50
    })
    items.value = response.items || []
  } catch (err) {
    error.value = err?.detail || '练习历史读取失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function getTitle(item) {
  const question = item?.question || {}
  return [question.subject, question.module].filter(Boolean).join(' · ') || '练习记录'
}

function formatTime(value) {
  if (!value) return '暂无时间'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 16)
  const now = new Date()
  const sameDay = date.toDateString() === now.toDateString()
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  const prefix = sameDay ? '今天' : date.toDateString() === yesterday.toDateString() ? '昨天' : `${date.getMonth() + 1}-${date.getDate()}`
  return `${prefix} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function buildOptions(question = {}) {
  return [
    { key: 'A', text: question.option_a },
    { key: 'B', text: question.option_b },
    { key: 'C', text: question.option_c },
    { key: 'D', text: question.option_d },
    { key: 'E', text: question.option_e }
  ].filter((item) => item.text)
}

function openDetail(item) {
  selectedItem.value = item
}

function closeDetail() {
  selectedItem.value = null
}

function getOptionClass(key) {
  const item = selectedItem.value
  if (!item?.question) return ''
  if (key === item.question.answer) return 'correct'
  if (key === item.selected_answer && key !== item.question.answer) return 'wrong'
  return ''
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.redirectTo({ url: '/pages/home/index' })
    }
  })
}
</script>

<style scoped>
.history-page {
  min-height: 100vh;
  min-height: 100dvh;
  padding: calc(env(safe-area-inset-top) + 20rpx) 22rpx calc(env(safe-area-inset-bottom) + 40rpx);
  background: linear-gradient(180deg, #fbfcff 0%, #f4f7fb 100%);
  overflow-x: hidden;
}

.history-topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 72rpx;
  margin-bottom: 22rpx;
}

.back-btn,
.top-icon,
.close-btn {
  width: 58rpx;
  height: 58rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #101828;
  font-size: 40rpx;
  font-weight: 800;
}

.top-title {
  color: #101828;
  font-size: 32rpx;
  font-weight: 900;
}

.top-actions {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.top-icon {
  font-size: 30rpx;
}

.filter-tabs {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10rpx;
  padding: 8rpx;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 12rpx 34rpx rgba(25, 48, 89, 0.06);
  margin-bottom: 22rpx;
}

.filter-tab {
  min-height: 64rpx;
  margin: 0;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  color: #667085;
  font-size: 25rpx;
  font-weight: 800;
  line-height: 64rpx;
}

.filter-tab.active {
  background: #1677ff;
  color: #ffffff;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.history-card,
.state-card {
  padding: 26rpx 24rpx;
  border-radius: 28rpx;
  background: #ffffff;
  border: 2rpx solid #edf2fb;
  box-shadow: 0 14rpx 38rpx rgba(25, 48, 89, 0.07);
}

.state-card {
  color: #667085;
  font-size: 26rpx;
  line-height: 1.7;
}

.state-card.warning {
  color: #9a6510;
  background: #fff8eb;
  border-color: #fde7b0;
}

.card-head,
.answer-row,
.correct-row,
.detail-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.card-title {
  flex: 1;
  min-width: 0;
  color: #101828;
  font-size: 28rpx;
  line-height: 1.35;
  font-weight: 900;
}

.result-pill {
  flex-shrink: 0;
  color: #16a34a;
  font-size: 24rpx;
  font-weight: 900;
}

.result-pill.wrong {
  color: #ef4444;
}

.stem {
  margin-top: 16rpx;
  color: #475467;
  font-size: 25rpx;
  line-height: 1.55;
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.answer-row,
.correct-row {
  margin-top: 18rpx;
  color: #8a95a8;
  font-size: 22rpx;
  line-height: 1.4;
}

.detail-link {
  color: #1677ff;
  font-weight: 900;
}

.detail-mask {
  position: fixed;
  inset: 0;
  z-index: 50;
  padding: 120rpx 22rpx 40rpx;
  background: rgba(15, 23, 42, 0.34);
  display: flex;
  align-items: flex-end;
}

.detail-panel {
  width: 100%;
  max-height: 78vh;
  overflow-y: auto;
  padding: 28rpx 24rpx;
  border-radius: 34rpx;
  background: #ffffff;
}

.detail-title {
  color: #101828;
  font-size: 31rpx;
  font-weight: 900;
}

.detail-sub {
  margin-top: 8rpx;
  color: #8a95a8;
  font-size: 22rpx;
}

.detail-stem {
  margin-top: 24rpx;
  color: #101828;
  font-size: 29rpx;
  line-height: 1.65;
  font-weight: 800;
}

.option-list {
  margin-top: 20rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.option-row {
  display: flex;
  gap: 14rpx;
  padding: 18rpx;
  border-radius: 22rpx;
  background: #f8fbff;
  border: 2rpx solid #edf2fb;
}

.option-row.correct {
  border-color: rgba(22, 163, 74, 0.4);
  background: rgba(22, 163, 74, 0.08);
}

.option-row.wrong {
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.08);
}

.option-key {
  width: 44rpx;
  height: 44rpx;
  border-radius: 14rpx;
  background: #edf4ff;
  color: #1677ff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 23rpx;
  font-weight: 900;
}

.option-text {
  flex: 1;
  color: #344054;
  font-size: 25rpx;
  line-height: 1.55;
}

.explanation {
  margin-top: 22rpx;
  padding: 20rpx;
  border-radius: 24rpx;
  background: #f8fbff;
}

.explain-title {
  color: #101828;
  font-size: 26rpx;
  font-weight: 900;
}

.explain-text {
  margin-top: 10rpx;
  color: #475467;
  font-size: 24rpx;
  line-height: 1.7;
}
</style>
