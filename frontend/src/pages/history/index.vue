<template>
  <view class="page history-page">
    <view class="history-topbar">
      <view class="back-btn" @tap="goBack">‹</view>
      <view class="top-title">练习历史</view>
      <view class="top-actions">
        <view class="top-action-btn" :class="{ active: searchVisible || searchKeyword }" @tap="toggleSearch">
          <view class="search-glyph"></view>
        </view>
        <view class="top-action-btn filter-icon-wrap" :class="{ active: activeFilterCount > 0 }" @tap="openFilterPanel">
          <view class="filter-glyph"></view>
          <text v-if="activeFilterCount > 0" class="filter-badge">{{ activeFilterCount }}</text>
        </view>
      </view>
    </view>

    <view v-if="searchVisible" class="search-card">
      <text class="search-symbol">⌕</text>
      <input
        v-model="searchKeyword"
        class="search-input"
        placeholder="搜索题干、科目、模块"
        confirm-type="search"
      />
      <text v-if="searchKeyword" class="search-clear" @tap="clearSearch">×</text>
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

    <view v-if="filterSummaryText" class="filter-summary">
      <text>{{ filterSummaryText }}</text>
      <text class="summary-clear" @tap="resetAllFilters">清除筛选</text>
    </view>

    <view v-if="loading" class="state-card">正在读取你的真实练习记录...</view>
    <view v-else-if="error" class="state-card warning">{{ error }}</view>
    <view v-else-if="items.length === 0" class="state-card">
      暂无练习历史。完成一组刷题后，这里会自动记录你的答题情况。
    </view>
    <view v-else-if="filteredItems.length === 0" class="state-card">
      没有找到符合条件的练习记录。可以换个关键词，或清除筛选后再试。
    </view>

    <view v-else class="history-list">
      <view v-for="item in filteredItems" :key="item.id" class="history-card" @tap="openDetail(item)">
        <view class="card-head">
          <view class="card-title">{{ getTitle(item) }}</view>
          <view class="result-pill" :class="{ wrong: !item.is_correct }">
            {{ item.is_correct ? '✓ 答对' : '× 答错' }}
          </view>
        </view>
        <MathText class="stem" :value="item.question?.stem || '题目内容暂不可用'" />
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

    <view v-if="filterPanelVisible" class="filter-mask" @tap="closeFilterPanel">
      <view class="filter-panel" @tap.stop>
        <view class="sheet-handle"></view>
        <view class="sheet-head">
          <view>
            <view class="sheet-title">筛选练习记录</view>
            <view class="sheet-sub">按结果、科目、模块和时间快速定位题目</view>
          </view>
          <view class="sheet-close" @tap="closeFilterPanel">×</view>
        </view>

        <view class="filter-section">
          <view class="filter-label">答题结果</view>
          <view class="chip-grid three">
            <button
              v-for="item in filters"
              :key="`status-${item.key}`"
              class="filter-chip"
              :class="{ active: activeFilter === item.key }"
              @tap="changeFilter(item.key)"
            >
              {{ item.label }}
            </button>
          </view>
        </view>

        <view class="filter-section">
          <view class="filter-label">科目</view>
          <view class="chip-grid">
            <button
              v-for="subject in subjectOptions"
              :key="`subject-${subject.value}`"
              class="filter-chip"
              :class="{ active: advancedFilters.subject === subject.value }"
              @tap="setSubjectFilter(subject.value)"
            >
              {{ subject.label }}
            </button>
          </view>
        </view>

        <view class="filter-section">
          <view class="filter-label">模块</view>
          <view class="chip-grid">
            <button
              v-for="module in moduleOptions"
              :key="`module-${module.value}`"
              class="filter-chip"
              :class="{ active: advancedFilters.module === module.value }"
              @tap="advancedFilters.module = module.value"
            >
              {{ module.label }}
            </button>
          </view>
        </view>

        <view class="filter-section">
          <view class="filter-label">时间范围</view>
          <view class="chip-grid">
            <button
              v-for="time in timeOptions"
              :key="`time-${time.value}`"
              class="filter-chip"
              :class="{ active: advancedFilters.timeRange === time.value }"
              @tap="advancedFilters.timeRange = time.value"
            >
              {{ time.label }}
            </button>
          </view>
        </view>

        <view class="sheet-actions">
          <button class="ghost-action" @tap="resetAllFilters">重置</button>
          <button class="primary-action" @tap="closeFilterPanel">完成</button>
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
        <MathText class="detail-stem" :value="selectedItem.question?.stem" />
        <view class="option-list">
          <view
            v-for="option in selectedOptions"
            :key="option.key"
            class="option-row"
            :class="getOptionClass(option.key)"
          >
            <text class="option-key">{{ option.key }}</text>
            <MathText class="option-text" :value="option.text" />
          </view>
        </view>
        <view class="explanation">
          <view class="explain-title">解析</view>
          <MathText class="explain-text" :value="selectedItem.question?.explanation || '暂无解析'" />
        </view>
      </view>
    </view>

    <!-- #ifdef H5 -->
    <IcpFooter />
    <!-- #endif -->
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { fetchAnswerHistory } from '../../api/answers'
import IcpFooter from '../../components/IcpFooter.vue'
import MathText from '../../components/MathText.vue'

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
const searchVisible = ref(false)
const searchKeyword = ref('')
const filterPanelVisible = ref(false)
const advancedFilters = ref({
  subject: 'all',
  module: 'all',
  timeRange: 'all'
})

const timeOptions = [
  { value: 'all', label: '全部时间' },
  { value: 'today', label: '今天' },
  { value: '7d', label: '近 7 天' },
  { value: '30d', label: '近 30 天' }
]

const selectedOptions = computed(() => buildOptions(selectedItem.value?.question))
const normalizedKeyword = computed(() => searchKeyword.value.trim().toLowerCase())
const subjectOptions = computed(() => {
  const subjects = uniqueQuestionValues('subject')
  return [{ value: 'all', label: '全部科目' }, ...subjects.map((item) => ({ value: item, label: item }))]
})
const moduleOptions = computed(() => {
  const source = advancedFilters.value.subject === 'all'
    ? items.value
    : items.value.filter((item) => item.question?.subject === advancedFilters.value.subject)
  const modules = Array.from(new Set(source.map((item) => item.question?.module).filter(Boolean)))
  return [{ value: 'all', label: '全部模块' }, ...modules.map((item) => ({ value: item, label: item }))]
})
const activeFilterCount = computed(() => {
  let count = activeFilter.value === 'all' ? 0 : 1
  if (advancedFilters.value.subject !== 'all') count += 1
  if (advancedFilters.value.module !== 'all') count += 1
  if (advancedFilters.value.timeRange !== 'all') count += 1
  if (normalizedKeyword.value) count += 1
  return count
})
const filterSummaryText = computed(() => {
  const parts = []
  const statusLabel = filters.find((item) => item.key === activeFilter.value)?.label
  const timeLabel = timeOptions.find((item) => item.value === advancedFilters.value.timeRange)?.label
  if (activeFilter.value !== 'all') parts.push(statusLabel)
  if (advancedFilters.value.subject !== 'all') parts.push(advancedFilters.value.subject)
  if (advancedFilters.value.module !== 'all') parts.push(advancedFilters.value.module)
  if (advancedFilters.value.timeRange !== 'all') parts.push(timeLabel)
  if (normalizedKeyword.value) parts.push(`搜索：${searchKeyword.value.trim()}`)
  return parts.length ? `当前筛选：${parts.join(' / ')}` : ''
})
const filteredItems = computed(() => {
  return items.value.filter((item) => {
    const question = item.question || {}
    if (advancedFilters.value.subject !== 'all' && question.subject !== advancedFilters.value.subject) {
      return false
    }
    if (advancedFilters.value.module !== 'all' && question.module !== advancedFilters.value.module) {
      return false
    }
    if (!matchesTimeRange(item.created_at, advancedFilters.value.timeRange)) {
      return false
    }
    if (!matchesKeyword(item)) {
      return false
    }
    return true
  })
})

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
      limit: 100
    })
    items.value = response.items || []
  } catch (err) {
    error.value = getHistoryErrorMessage(err)
  } finally {
    loading.value = false
  }
}

function getHistoryErrorMessage(err) {
  const detail = err?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return '练习历史读取失败，请稍后重试'
  return err?.message || '练习历史读取失败，请稍后重试'
}

function uniqueQuestionValues(field) {
  return Array.from(new Set(items.value.map((item) => item.question?.[field]).filter(Boolean)))
}

function toggleSearch() {
  searchVisible.value = !searchVisible.value
  if (!searchVisible.value) searchKeyword.value = ''
}

function clearSearch() {
  searchKeyword.value = ''
}

function openFilterPanel() {
  filterPanelVisible.value = true
}

function closeFilterPanel() {
  filterPanelVisible.value = false
}

function setSubjectFilter(value) {
  advancedFilters.value.subject = value
  advancedFilters.value.module = 'all'
}

function resetAdvancedFilters() {
  advancedFilters.value = {
    subject: 'all',
    module: 'all',
    timeRange: 'all'
  }
  searchKeyword.value = ''
  searchVisible.value = false
}

function resetAllFilters() {
  activeFilter.value = 'all'
  resetAdvancedFilters()
  loadHistory()
}

function matchesKeyword(item) {
  if (!normalizedKeyword.value) return true
  const question = item.question || {}
  const text = [
    question.subject,
    question.module,
    question.submodule,
    question.stem,
    question.option_a,
    question.option_b,
    question.option_c,
    question.option_d,
    item.selected_answer
  ]
    .filter(Boolean)
    .join(' ')
    .toLowerCase()
  return text.includes(normalizedKeyword.value)
}

function matchesTimeRange(value, range) {
  if (range === 'all') return true
  if (!value) return false
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return false
  const now = new Date()
  if (range === 'today') {
    return date.toDateString() === now.toDateString()
  }
  const days = range === '7d' ? 7 : 30
  const start = new Date(now)
  start.setDate(now.getDate() - days)
  return date >= start
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
    { key: 'D', text: question.option_d }
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

.history-page button::after {
  border: 0;
}

.history-topbar {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  min-height: 72rpx;
  margin-bottom: 22rpx;
}

.back-btn,
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

.back-btn {
  justify-self: start;
}

.top-title {
  justify-self: center;
  color: #101828;
  font-size: 32rpx;
  font-weight: 900;
}

.top-actions {
  justify-self: end;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.top-action-btn {
  position: relative;
  width: 58rpx;
  height: 58rpx;
  border-radius: 20rpx;
  border: 2rpx solid transparent;
  background: rgba(255, 255, 255, 0.74);
  color: #344054;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 20rpx rgba(25, 48, 89, 0.05);
}

.top-action-btn.active {
  color: var(--gyt-primary);
  background: var(--gyt-primary-soft);
  border-color: var(--gyt-primary-border);
}

.search-glyph {
  position: relative;
  width: 21rpx;
  height: 21rpx;
  border: 4rpx solid currentColor;
  border-radius: 50%;
  box-sizing: border-box;
}

.search-glyph::after {
  content: '';
  position: absolute;
  right: -9rpx;
  bottom: -6rpx;
  width: 11rpx;
  height: 4rpx;
  border-radius: 999rpx;
  background: currentColor;
  transform: rotate(45deg);
}

.filter-glyph {
  position: relative;
  width: 30rpx;
  height: 24rpx;
}

.filter-glyph::before {
  content: '';
  position: absolute;
  left: 1rpx;
  top: 2rpx;
  width: 28rpx;
  height: 4rpx;
  border-radius: 999rpx;
  background: currentColor;
  box-shadow: 0 9rpx 0 currentColor, 0 18rpx 0 currentColor;
}

.filter-glyph::after {
  content: '';
  position: absolute;
  left: 17rpx;
  top: 0;
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: currentColor;
  box-shadow: -12rpx 9rpx 0 currentColor, 6rpx 18rpx 0 currentColor;
}

.filter-icon-wrap {
  position: relative;
}

.filter-badge {
  position: absolute;
  top: 2rpx;
  right: 2rpx;
  min-width: 26rpx;
  height: 26rpx;
  padding: 0 7rpx;
  border-radius: 999rpx;
  background: #ef4444;
  color: #ffffff;
  font-size: 18rpx;
  font-weight: 900;
  line-height: 26rpx;
  text-align: center;
}

.search-card {
  min-height: 72rpx;
  margin-bottom: 18rpx;
  padding: 0 18rpx;
  border-radius: 24rpx;
  background: #ffffff;
  border: 2rpx solid #edf2fb;
  box-shadow: 0 12rpx 34rpx rgba(25, 48, 89, 0.06);
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.search-symbol {
  color: #98a2b3;
  font-size: 28rpx;
  font-weight: 900;
}

.search-input {
  flex: 1;
  min-width: 0;
  height: 70rpx;
  color: #101828;
  font-size: 25rpx;
}

.search-clear {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: #f2f4f7;
  color: #667085;
  text-align: center;
  line-height: 42rpx;
  font-size: 30rpx;
  font-weight: 900;
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
  background: var(--gyt-primary);
  color: #ffffff;
}

.filter-summary {
  margin: -6rpx 0 18rpx;
  padding: 16rpx 18rpx;
  border-radius: 20rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 22rpx;
  line-height: 1.45;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.summary-clear {
  flex-shrink: 0;
  color: var(--gyt-primary);
  font-weight: 900;
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
  color: var(--gyt-primary);
  font-weight: 900;
}

.filter-mask {
  position: fixed;
  inset: 0;
  z-index: 48;
  padding: 120rpx 22rpx calc(env(safe-area-inset-bottom) + 22rpx);
  background: rgba(15, 23, 42, 0.34);
  display: flex;
  align-items: flex-end;
}

.filter-panel {
  width: 100%;
  max-height: 82vh;
  overflow-y: auto;
  padding: 14rpx 22rpx 22rpx;
  border-radius: 34rpx;
  background: #ffffff;
  box-shadow: 0 -18rpx 60rpx rgba(15, 23, 42, 0.14);
}

.sheet-handle {
  width: 76rpx;
  height: 8rpx;
  margin: 0 auto 20rpx;
  border-radius: 999rpx;
  background: #e4eaf4;
}

.sheet-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 24rpx;
}

.sheet-title {
  color: #101828;
  font-size: 32rpx;
  font-weight: 900;
}

.sheet-sub {
  margin-top: 8rpx;
  color: #8a95a8;
  font-size: 22rpx;
  line-height: 1.45;
}

.sheet-close {
  width: 58rpx;
  height: 58rpx;
  border-radius: 20rpx;
  background: #f2f4f7;
  color: #667085;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 34rpx;
  font-weight: 900;
}

.filter-section {
  margin-top: 22rpx;
}

.filter-label {
  margin-bottom: 12rpx;
  color: #101828;
  font-size: 25rpx;
  font-weight: 900;
}

.chip-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.chip-grid.three {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
}

.filter-chip {
  min-height: 62rpx;
  margin: 0;
  padding: 0 22rpx;
  border-radius: 999rpx;
  border: 2rpx solid #e4eaf4;
  background: #ffffff;
  color: #475467;
  font-size: 23rpx;
  font-weight: 800;
  line-height: 62rpx;
}

.filter-chip.active {
  border-color: var(--gyt-primary);
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
}

.sheet-actions {
  position: sticky;
  bottom: -22rpx;
  margin: 28rpx -22rpx -22rpx;
  padding: 18rpx 22rpx calc(env(safe-area-inset-bottom) + 18rpx);
  background: rgba(255, 255, 255, 0.94);
  backdrop-filter: blur(14rpx);
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 14rpx;
}

.ghost-action,
.primary-action {
  height: 76rpx;
  margin: 0;
  border-radius: 22rpx;
  font-size: 26rpx;
  font-weight: 900;
  line-height: 76rpx;
}

.ghost-action {
  border: 2rpx solid #d8e2f2;
  background: #ffffff;
  color: #475467;
}

.primary-action {
  border: 0;
  background: var(--gyt-primary);
  color: #ffffff;
  box-shadow: 0 14rpx 28rpx var(--gyt-primary-shadow);
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
  background: var(--gyt-primary-tint);
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
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
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
  background: var(--gyt-primary-tint);
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
