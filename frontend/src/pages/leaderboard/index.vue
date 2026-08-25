<template>
  <view class="page stats-page" :style="themeInlineStyle">
    <view class="stats-shell">
      <view class="stats-header">
        <button class="stats-back-button" hover-class="none" aria-label="返回" @tap="goBack">
          <image class="stats-back-icon" src="/static/ui-icons/back.svg" mode="aspectFit" />
        </button>
        <view class="stats-header-copy">
          <text class="stats-title">学习统计</text>
        </view>
        <button
          class="header-refresh"
          :class="{ spinning: loading }"
          :disabled="loading"
          aria-label="刷新学习统计"
          @tap="loadStats"
        >
          <text class="refresh-glyph" aria-hidden="true">↻</text>
        </button>
      </view>

      <view v-if="error" class="sync-notice" role="status">
        <text>{{ error }}</text>
        <button class="sync-retry" :disabled="loading" @tap="loadStats">重试</button>
      </view>

      <view class="score-card" @tap="goPractice">
        <view class="score-illustration" aria-hidden="true">
          <view class="score-mascot-stage">
            <image class="score-mascot-image" src="/static/brand/study-stat-mascot.png" mode="aspectFit" />
            <svg class="score-mascot-blink-eye score-mascot-blink-eye--left" viewBox="0 0 32 22" xmlns="http://www.w3.org/2000/svg">
              <ellipse cx="16" cy="11" rx="16" ry="11" fill="#b4d9f8" />
              <path d="M6 12c4-6 16-6 20 0" fill="none" stroke="#111820" stroke-width="3.2" stroke-linecap="round" />
            </svg>
            <svg class="score-mascot-blink-eye score-mascot-blink-eye--right" viewBox="0 0 32 22" xmlns="http://www.w3.org/2000/svg">
              <ellipse cx="16" cy="11" rx="16" ry="11" fill="#afd5f6" />
              <path d="M6 12c4-6 16-6 20 0" fill="none" stroke="#111820" stroke-width="3.2" stroke-linecap="round" />
            </svg>
          </view>
        </view>
        <view class="score-copy">
          <view class="score-main">{{ scoreFraction }}</view>
          <view class="score-label">学习总览 <text class="score-date">（{{ scoreDateLabel }}）</text></view>
          <view class="score-meta">正确率 {{ accuracyLabel }} · {{ examOption.title }}</view>
        </view>
        <text class="score-arrow" aria-hidden="true">›</text>
      </view>

      <view class="streak-card">
          <view class="streak-heading">
            <view class="flame-wrap" :class="{ 'is-idle': studyStreak === 0 }" aria-label="连续学习火焰">
              <image
                class="flame-mascot-image is-animating"
                src="/static/brand/study-streak-flame.png"
                mode="aspectFit"
              />
            <text class="flame-count">{{ studyStreak }}</text>
          </view>
          <view class="streak-copy">
            <text class="streak-title">连续学习</text>
            <text class="streak-subtitle">{{ streakSubtitle }}</text>
          </view>
        </view>

        <view class="streak-days" aria-label="近七天学习情况">
          <view v-for="day in streakDays" :key="day.key" class="streak-day">
            <text class="streak-day-label" :class="{ muted: !day.active }">{{ day.label }}</text>
            <view class="streak-day-dot" :class="{ active: day.active, today: day.isToday }">
              <text v-if="day.active" class="streak-check">✓</text>
            </view>
          </view>
        </view>
      </view>

      <view class="metric-grid">
        <view v-for="item in metricCards" :key="item.key" class="metric-card" @tap="handleMetric(item.key)">
          <view class="metric-topline">
            <text class="metric-value">{{ item.value }}</text>
            <view class="metric-icon" :class="`metric-icon-${item.key}`" aria-hidden="true">
              <svg v-if="item.key === 'total'" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <rect x="10" y="7" width="28" height="34" rx="4" fill="#a9d6d7" stroke="#1d2929" stroke-width="2" />
                <path d="M16 16h16M16 23h16M16 30h10" stroke="#1d2929" stroke-width="2" stroke-linecap="round" />
              </svg>
              <svg v-else-if="item.key === 'favorite'" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <path d="M24 39S8 29 8 18c0-6 4-10 10-10 3 0 5 1 6 4 1-3 4-4 6-4 6 0 10 4 10 10 0 11-16 21-16 21Z" fill="#a9d6d7" stroke="#1d2929" stroke-width="2" stroke-linejoin="round" />
              </svg>
              <svg v-else-if="item.key === 'wrong'" viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <path d="M13 7h22a4 4 0 0 1 4 4v30l-15-7-15 7V11a4 4 0 0 1 4-4Z" fill="#a9d6d7" stroke="#1d2929" stroke-width="2" stroke-linejoin="round" />
                <path d="M19 17h10M19 24h10" stroke="#1d2929" stroke-width="2" stroke-linecap="round" />
              </svg>
              <svg v-else viewBox="0 0 48 48" xmlns="http://www.w3.org/2000/svg">
                <path d="M6 22 24 10l18 12-18 12Z" fill="#a9d6d7" stroke="#1d2929" stroke-width="2" stroke-linejoin="round" />
                <path d="M14 28v8c0 4 5 7 10 7s10-3 10-7v-8" fill="#d4e9e9" stroke="#1d2929" stroke-width="2" />
              </svg>
            </view>
          </view>
          <text class="metric-label">{{ item.label }}</text>
          <text class="metric-note">{{ item.note }}</text>
        </view>
      </view>

      <view class="trend-card">
        <view class="trend-heading">
          <view>
            <text class="trend-title">近 7 天正确率趋势</text>
            <text class="trend-subtitle">{{ trendSubtitle }}</text>
          </view>
          <text class="trend-change" :class="trendChangeTone">{{ trendChangeLabel }}</text>
        </view>

        <view v-if="trendReady" class="trend-chart-wrap">
          <svg class="trend-chart" viewBox="0 0 320 166" preserveAspectRatio="none" aria-label="近七天正确率曲线">
            <defs>
              <linearGradient id="stats-area-gradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#a9d6d7" stop-opacity="0.62" />
                <stop offset="100%" stop-color="#a9d6d7" stop-opacity="0.04" />
              </linearGradient>
            </defs>
            <line x1="12" x2="308" y1="28" y2="28" class="chart-grid-line" />
            <line x1="12" x2="308" y1="78" y2="78" class="chart-grid-line" />
            <line x1="12" x2="308" y1="128" y2="128" class="chart-axis-line" />
            <path :d="trendAreaPath" class="chart-area" />
            <path :d="trendPath" class="chart-line" />
            <circle
              v-for="point in chartPoints"
              :key="point.key"
              :cx="point.x"
              :cy="point.y"
              r="5"
              class="chart-point"
            />
          </svg>
          <view class="trend-axis-labels">
            <text v-for="point in chartPoints" :key="`${point.key}-label`">{{ point.label }}</text>
          </view>
        </view>
        <view v-else class="trend-empty">
          <view class="trend-empty-line"></view>
          <text>完成至少两天练习后，这里会生成你的学习曲线</text>
        </view>

        <button class="practice-button" @tap="goPractice">
          <text>开始今日训练</text>
          <text class="practice-button-arrow">→</text>
        </button>
      </view>

      <!-- #ifdef H5 -->
      <IcpFooter />
      <!-- #endif -->
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import IcpFooter from '../../components/IcpFooter.vue'
import { fetchFavorites } from '../../api/favorites'
import { fetchLearningSummary } from '../../api/reports'
import { getAuthUser, isLoggedIn } from '../../utils/auth'
import { getExamOption } from '../../utils/exam'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const authUser = ref(getAuthUser())
const examCode = ref(uni.getStorageSync('examCode') || authUser.value?.exam_target || 'Z001')
const loading = ref(false)
const error = ref('')
const favoriteCount = ref(0)
const favoriteLoaded = ref(false)
const summary = ref(createEmptySummary())

const examOption = computed(() => getExamOption(examCode.value))
const totalAnswers = computed(() => Number(summary.value.total_answers || 0))
const correctAnswers = computed(() => Number(summary.value.correct_answers || 0))
const accuracy = computed(() => Number(summary.value.accuracy || 0))
const accuracyLabel = computed(() => `${Math.round(accuracy.value)}%`)
const studyStreak = computed(() => Number(summary.value.study_streak || 0))
const scoreFraction = computed(() => `${correctAnswers.value}/${totalAnswers.value}`)
const scoreDateLabel = computed(() => {
  const latest = streakDays.value.slice().reverse().find((item) => item.active)
  return latest?.dateLabel || '开始练习后同步'
})
const streakSubtitle = computed(() => {
  if (studyStreak.value > 0) return `已坚持 ${studyStreak.value} 天，保持这个节奏`
  return '完成今天第一组题，点亮连续学习'
})
const weeklyAnswers = computed(() => Number(summary.value.weekly_answers || 0))
const wrongCount = computed(() => Number(summary.value.wrong_question_count || 0))
const favoriteValue = computed(() => (favoriteLoaded.value ? favoriteCount.value : '--'))

const metricCards = computed(() => [
  {
    key: 'total',
    value: totalAnswers.value,
    label: '累计作答',
    note: totalAnswers.value ? `正确 ${correctAnswers.value} 题` : '完成练习后自动累计'
  },
  {
    key: 'favorite',
    value: favoriteValue.value,
    label: '收藏题目',
    note: favoriteLoaded.value ? '随时回看重点题' : '正在同步收藏'
  },
  {
    key: 'wrong',
    value: wrongCount.value,
    label: '错题待复盘',
    note: wrongCount.value ? '建议优先处理' : '暂无待复盘错题'
  },
  {
    key: 'practice',
    value: weeklyAnswers.value,
    label: '本周刷题',
    note: summary.value.weekly_accuracy ? `本周正确率 ${Math.round(summary.value.weekly_accuracy)}%` : '本周还未开始'
  }
])

const streakDays = computed(() => {
  const raw = Array.isArray(summary.value.trend) ? summary.value.trend : []
  const normalized = raw.slice(-7)
  const padCount = Math.max(0, 7 - normalized.length)
  const padded = [
    ...Array.from({ length: padCount }, () => null),
    ...normalized
  ]
  const fallbackLabels = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']
  return padded.map((item, index) => {
    const total = Number(item?.total_answers || 0)
    return {
      key: item?.date || `empty-${index}`,
      label: item?.label || fallbackLabels[index],
      dateLabel: formatShortDate(item?.date),
      date: item?.date || '',
      active: total > 0,
      total,
      accuracy: item?.accuracy == null ? null : Number(item.accuracy),
      isToday: index === 6
    }
  })
})

const trendReady = computed(() => streakDays.value.filter((item) => item.accuracy !== null && item.total > 0).length >= 2)
const chartPoints = computed(() => {
  if (!trendReady.value) return []
  const known = streakDays.value.filter((item) => item.accuracy !== null && item.total > 0)
  const fallback = known[known.length - 1]?.accuracy || accuracy.value || 0
  const values = streakDays.value.map((item) => clamp(Number(item.accuracy == null ? fallback : item.accuracy), 0, 100))
  const step = 296 / Math.max(values.length - 1, 1)
  return values.map((value, index) => ({
    key: streakDays.value[index].key,
    label: streakDays.value[index].label,
    value,
    x: 12 + step * index,
    y: 128 - (value / 100) * 100
  }))
})
const trendPath = computed(() => {
  const points = chartPoints.value
  if (!points.length) return ''
  return points.reduce((path, point, index) => {
    if (index === 0) return `M ${point.x.toFixed(2)} ${point.y.toFixed(2)}`
    const previous = points[index - 1]
    const controlX = (previous.x + point.x) / 2
    return `${path} C ${controlX.toFixed(2)} ${previous.y.toFixed(2)}, ${controlX.toFixed(2)} ${point.y.toFixed(2)}, ${point.x.toFixed(2)} ${point.y.toFixed(2)}`
  }, '')
})
const trendAreaPath = computed(() => {
  const points = chartPoints.value
  if (!points.length) return ''
  const first = points[0]
  const last = points[points.length - 1]
  return `${trendPath.value} L ${last.x.toFixed(2)} 128 L ${first.x.toFixed(2)} 128 Z`
})
const trendChangeValue = computed(() => summary.value.weekly_accuracy_change)
const trendChangeTone = computed(() => {
  if (trendChangeValue.value == null) return 'muted'
  return Number(trendChangeValue.value) >= 0 ? 'up' : 'down'
})
const trendChangeLabel = computed(() => {
  if (trendChangeValue.value == null) return '待积累'
  const value = Number(trendChangeValue.value)
  return `${value >= 0 ? '+' : ''}${Math.round(value)}%`
})
const trendSubtitle = computed(() => {
  if (!trendReady.value) return '完成两天练习后查看变化'
  return `本周平均正确率 ${Math.round(Number(summary.value.weekly_accuracy || 0))}%`
})

onShow(() => {
  authUser.value = getAuthUser()
  examCode.value = uni.getStorageSync('examCode') || authUser.value?.exam_target || 'Z001'
  if (!isLoggedIn()) {
    uni.navigateTo({
      url: `/pages/login/index?redirect=${encodeURIComponent('/pages/leaderboard/index')}`
    })
    return
  }
  loadStats()
})

async function loadStats() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  const [summaryResult, favoriteResult] = await Promise.allSettled([
    fetchLearningSummary({ exam_code: examCode.value }),
    fetchFavorites({ limit: 200 })
  ])

  if (summaryResult.status === 'fulfilled') {
    summary.value = { ...createEmptySummary(), ...(summaryResult.value || {}) }
  } else {
    error.value = getStatsErrorMessage(summaryResult.reason)
  }

  if (favoriteResult.status === 'fulfilled') {
    const response = favoriteResult.value || {}
    favoriteCount.value = Number(response.count ?? response.items?.length ?? 0)
    favoriteLoaded.value = true
  } else if (!error.value) {
    error.value = '收藏数据暂时未同步，学习统计仍可正常查看'
  }
  loading.value = false
}

function getStatsErrorMessage(err) {
  if (Array.isArray(err?.detail)) return '登录状态已失效，请重新登录'
  if (typeof err?.detail === 'string' && err.detail.trim()) return err.detail
  return '学习数据暂时未同步，请点击重试'
}

function goBack() {
  const pages = getCurrentPages()
  if (pages.length > 1) {
    uni.navigateBack({
      fail() {
        uni.reLaunch({ url: '/pages/home/index' })
      }
    })
    return
  }
  uni.reLaunch({ url: '/pages/home/index' })
}

function goPractice() {
  uni.setStorageSync('examCode', examCode.value)
  uni.navigateTo({
    url: `/pages/practice/index?exam_code=${encodeURIComponent(examCode.value)}`
  })
}

function handleMetric(key) {
  if (key === 'favorite') {
    uni.navigateTo({ url: '/pages/favorites/index' })
    return
  }
  if (key === 'total' || key === 'practice') {
    goPractice()
    return
  }
  if (key === 'wrong') {
    uni.reLaunch({ url: '/pages/home/index?tab=mistakes' })
    return
  }
  goPractice()
}

function formatShortDate(value) {
  if (!value) return ''
  const match = String(value).match(/^(\d{4})-(\d{1,2})-(\d{1,2})/)
  return match ? `${Number(match[2])}/${Number(match[3])}` : String(value).slice(5, 10)
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, Number.isFinite(value) ? value : min))
}

function createEmptySummary() {
  return {
    exam_code: examCode.value,
    total_answers: 0,
    correct_answers: 0,
    accuracy: 0,
    wrong_question_count: 0,
    weekly_answers: 0,
    weekly_correct_answers: 0,
    weekly_accuracy: 0,
    weekly_accuracy_change: null,
    study_streak: 0,
    trend: []
  }
}
</script>

<style scoped>
.stats-page {
  --stats-bg: #f3ebe2;
  --stats-card: #ffffff;
  --stats-ink: #171817;
  --stats-muted: #858181;
  --stats-line: #4b4b49;
  --stats-mint: #a9d6d7;
  --stats-mint-deep: #75b6b8;
  min-height: 100vh;
  min-height: 100dvh;
  box-sizing: border-box;
  padding: calc(env(safe-area-inset-top) + 18rpx) 28rpx calc(env(safe-area-inset-bottom) + 54rpx);
  overflow-x: hidden;
  background: var(--stats-bg);
  color: var(--stats-ink);
  font-family: var(--gyt-app-font);
}

.stats-shell {
  width: 100%;
  max-width: 720rpx;
  margin: 0 auto;
}

.stats-header {
  display: grid;
  grid-template-columns: 88rpx minmax(0, 1fr) 88rpx;
  align-items: center;
  gap: 12rpx;
  min-height: 88rpx;
  margin-bottom: 18rpx;
}

.stats-back-button {
  width: 76rpx;
  height: 76rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 26rpx;
  background: #ffffff;
  color: #172033;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.08);
}

.header-refresh {
  width: 88rpx;
  height: 88rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stats-back-button::after,
.header-refresh::after,
.sync-retry::after,
.practice-button::after {
  border: 0;
}

.stats-back-button:active,
.header-refresh:active,
.practice-button:active {
  transform: scale(0.96);
}

.stats-back-icon {
  display: block;
  width: 30rpx;
  height: 30rpx;
}

.header-refresh {
  background: transparent;
  box-shadow: none;
}

.refresh-glyph {
  color: #9b9795;
  font-size: 43rpx;
  line-height: 1;
  font-weight: 500;
}

.header-refresh.spinning .refresh-glyph {
  display: block;
  animation: stats-spin 900ms linear infinite;
}

.stats-header-copy {
  min-width: 0;
  text-align: center;
}

.stats-title {
  display: block;
  color: var(--stats-ink);
  font-size: 42rpx;
  line-height: 1.16;
  font-weight: 900;
  letter-spacing: -0.5rpx;
}

.sync-notice {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 18rpx;
  padding: 16rpx 20rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.72);
  color: #8a5d4f;
  font-size: 21rpx;
  line-height: 1.4;
}

.sync-notice > text {
  min-width: 0;
  flex: 1;
}

.sync-retry {
  flex: 0 0 auto;
  margin: 0;
  padding: 8rpx 16rpx;
  border-radius: 999rpx;
  background: var(--stats-mint);
  color: var(--stats-ink);
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 800;
}

.score-card,
.streak-card,
.trend-card {
  background: var(--stats-card);
}

.score-card {
  position: relative;
  display: flex;
  align-items: center;
  gap: 22rpx;
  min-height: 188rpx;
  margin-bottom: 36rpx;
  padding: 28rpx 26rpx;
  border: 3rpx solid var(--stats-ink);
  border-radius: 46rpx;
  box-shadow: 0 13rpx 0 var(--stats-ink);
  transition: transform 160ms ease, box-shadow 160ms ease;
}

.score-card:active {
  transform: translateY(5rpx);
  box-shadow: 0 8rpx 0 var(--stats-ink);
}

.score-illustration {
  position: relative;
  width: 128rpx;
  min-width: 128rpx;
  height: 112rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
}

.score-mascot-stage {
  position: relative;
  width: 150rpx;
  height: 150rpx;
  flex: 0 0 150rpx;
  transform: translateY(3rpx);
}

.score-mascot-image {
  display: block;
  width: 100%;
  height: 100%;
}

.score-mascot-blink-eye {
  position: absolute;
  z-index: 1;
  top: 53.333%;
  width: 18%;
  height: 12.667%;
  opacity: 0;
  transform: scaleY(0.24);
  transform-origin: center;
  animation: score-mascot-blink 5.8s ease-in-out infinite;
}

.score-mascot-blink-eye--left {
  left: 31.333%;
}

.score-mascot-blink-eye--right {
  left: 51.333%;
}

@keyframes score-mascot-blink {
  0%,
  83%,
  100% {
    opacity: 0;
    transform: scaleY(0.24);
  }

  84.5%,
  87% {
    opacity: 1;
    transform: scaleY(1);
  }

  88.5% {
    opacity: 0;
    transform: scaleY(0.24);
  }
}

@media (prefers-reduced-motion: reduce) {
  .score-mascot-blink-eye {
    animation: none;
    opacity: 0;
  }
}

.score-copy {
  min-width: 0;
  flex: 1;
}

.score-main {
  color: var(--stats-ink);
  font-size: 46rpx;
  line-height: 1.05;
  font-weight: 900;
  letter-spacing: -1rpx;
}

.score-label {
  margin-top: 9rpx;
  color: var(--stats-ink);
  font-size: 30rpx;
  line-height: 1.2;
  font-weight: 600;
}

.score-date {
  color: #aaa6a5;
  font-size: 24rpx;
  font-weight: 600;
}

.score-meta {
  margin-top: 10rpx;
  overflow: hidden;
  color: var(--stats-muted);
  font-size: 21rpx;
  line-height: 1.35;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.score-arrow {
  flex: 0 0 auto;
  color: #737272;
  font-size: 58rpx;
  line-height: 1;
  font-weight: 300;
}

.streak-card {
  margin-bottom: 34rpx;
  padding: 26rpx 25rpx 28rpx;
  border: 3rpx solid var(--stats-line);
  border-radius: 42rpx;
  box-shadow: 0 12rpx 0 var(--stats-line);
}

.streak-heading {
  display: grid;
  grid-template-columns: 118rpx minmax(0, 1fr);
  align-items: center;
  gap: 12rpx;
}

.flame-wrap {
  position: relative;
  width: 112rpx;
  height: 124rpx;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.flame-mascot-image {
  width: 136rpx;
  height: 136rpx;
  display: block;
  transform: translateY(16rpx);
  transform-origin: 50% 100%;
}

.flame-mascot-image.is-animating {
  animation: flame-mascot-float 2.2s ease-in-out infinite;
}

.flame-count {
  position: absolute;
  right: 7rpx;
  bottom: 7rpx;
  color: var(--stats-ink);
  font-size: 33rpx;
  line-height: 1;
  font-weight: 900;
}

.flame-wrap.is-idle .flame-mascot-image.is-animating {
  opacity: 0.62;
  animation-duration: 3.2s;
}

.streak-copy {
  min-width: 0;
}

.streak-title {
  display: block;
  color: var(--stats-ink);
  font-size: 35rpx;
  line-height: 1.2;
  font-weight: 900;
}

.streak-subtitle {
  display: block;
  margin-top: 8rpx;
  overflow: hidden;
  color: var(--stats-muted);
  font-size: 21rpx;
  line-height: 1.35;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.streak-days {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  gap: 4rpx;
  margin-top: 24rpx;
}

.streak-day {
  min-width: 0;
  text-align: center;
}

.streak-day-label {
  display: block;
  overflow: hidden;
  color: var(--stats-ink);
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.streak-day-label.muted {
  color: #d4d1d1;
}

.streak-day-dot {
  width: 48rpx;
  height: 48rpx;
  margin: 10rpx auto 0;
  border-radius: 50%;
  background: #eeecee;
  display: flex;
  align-items: center;
  justify-content: center;
}

.streak-day-dot.active {
  background: var(--stats-mint);
  border: 2rpx solid var(--stats-ink);
  box-sizing: border-box;
}

.streak-day-dot.today:not(.active) {
  background: #e5e2e2;
  box-shadow: inset 0 0 0 2rpx #c8c4c4;
}

.streak-check {
  color: var(--stats-ink);
  font-size: 28rpx;
  line-height: 1;
  font-weight: 900;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 22rpx;
  margin-bottom: 34rpx;
}

.metric-card {
  min-height: 170rpx;
  padding: 23rpx 24rpx 21rpx;
  box-sizing: border-box;
  border-radius: 38rpx;
  background: var(--stats-card);
  transition: transform 160ms ease;
}

.metric-card:active {
  transform: scale(0.98);
}

.metric-topline {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12rpx;
}

.metric-value {
  color: var(--stats-ink);
  font-size: 43rpx;
  line-height: 1;
  font-weight: 900;
  letter-spacing: -0.5rpx;
}

.metric-icon {
  width: 52rpx;
  height: 52rpx;
  flex: 0 0 52rpx;
}

.metric-icon svg {
  width: 100%;
  height: 100%;
  display: block;
}

.metric-label {
  display: block;
  margin-top: 22rpx;
  color: var(--stats-ink);
  font-size: 27rpx;
  line-height: 1.15;
  font-weight: 600;
}

.metric-note {
  display: block;
  margin-top: 9rpx;
  overflow: hidden;
  color: #a39f9f;
  font-size: 18rpx;
  line-height: 1.25;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.trend-card {
  margin-bottom: 28rpx;
  padding: 30rpx 27rpx 31rpx;
  border: 3rpx solid var(--stats-line);
  border-radius: 44rpx;
  box-shadow: 0 12rpx 0 var(--stats-line);
}

.trend-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
}

.trend-title {
  display: block;
  color: var(--stats-ink);
  font-size: 29rpx;
  line-height: 1.25;
  font-weight: 900;
}

.trend-subtitle {
  display: block;
  margin-top: 8rpx;
  color: var(--stats-muted);
  font-size: 21rpx;
  line-height: 1.35;
  font-weight: 600;
}

.trend-change {
  flex: 0 0 auto;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: #e9f5f5;
  color: #4b989a;
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 900;
}

.trend-change.down {
  background: #fff0ec;
  color: #c26e61;
}

.trend-change.muted {
  background: #f1efef;
  color: #aaa6a5;
}

.trend-chart-wrap {
  margin-top: 24rpx;
}

.trend-chart {
  width: 100%;
  height: 250rpx;
  display: block;
  overflow: visible;
}

.chart-grid-line {
  stroke: #eeeeed;
  stroke-width: 1.5;
  stroke-dasharray: 4 7;
}

.chart-axis-line {
  stroke: #c9c7c6;
  stroke-width: 2.5;
  stroke-linecap: round;
}

.chart-area {
  fill: url(#stats-area-gradient);
  opacity: 0.46;
}

.chart-line {
  fill: none;
  stroke: var(--stats-mint-deep);
  stroke-width: 4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.chart-point {
  fill: var(--stats-card);
  stroke: var(--stats-mint-deep);
  stroke-width: 3;
}

.trend-axis-labels {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  margin-top: -8rpx;
  color: #a4a1a0;
  font-size: 18rpx;
  line-height: 1.2;
  font-weight: 700;
  text-align: center;
}

.trend-empty {
  min-height: 250rpx;
  margin-top: 22rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 22rpx;
  color: #aaa6a5;
  font-size: 21rpx;
  line-height: 1.45;
  text-align: center;
}

.trend-empty-line {
  width: 82%;
  height: 100rpx;
  border-bottom: 5rpx solid #d7d4d3;
  border-radius: 50%;
  opacity: 0.7;
}

.practice-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
  min-width: 274rpx;
  height: 78rpx;
  margin: 25rpx auto 0;
  padding: 0 28rpx;
  border: 3rpx solid var(--stats-ink);
  border-radius: 44rpx;
  background: var(--stats-mint);
  color: var(--stats-ink);
  box-shadow: 0 8rpx 0 var(--stats-ink);
  font-size: 27rpx;
  line-height: 1;
  font-weight: 800;
  transition: transform 160ms ease, box-shadow 160ms ease;
}

.practice-button:active {
  box-shadow: 0 4rpx 0 var(--stats-ink);
}

.practice-button-arrow {
  font-size: 35rpx;
  line-height: 0.8;
  font-weight: 500;
}

@keyframes flame-mascot-float {
  0%,
  100% {
    filter: drop-shadow(0 3rpx 3rpx rgba(240, 139, 121, 0.06));
    transform: translateY(16rpx) rotate(-1deg) scale(1);
  }
  50% {
    filter: drop-shadow(0 5rpx 8rpx rgba(240, 139, 121, 0.25));
    transform: translateY(11rpx) rotate(2deg) scale(1.035, 0.98);
  }
}

@keyframes stats-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@media screen and (max-width: 360px) {
  .stats-page {
    padding-right: 22rpx;
    padding-left: 22rpx;
  }

  .stats-header {
    grid-template-columns: 76rpx minmax(0, 1fr) 76rpx;
  }

  .stats-back-button,
  .header-refresh {
    width: 76rpx;
    height: 76rpx;
  }

  .stats-title {
    font-size: 38rpx;
  }

  .score-card {
    gap: 12rpx;
    padding-right: 18rpx;
    padding-left: 18rpx;
  }

  .score-illustration {
    width: 110rpx;
    min-width: 110rpx;
  }

  .score-mascot-stage {
    width: 132rpx;
    height: 132rpx;
    flex-basis: 132rpx;
    transform: translateY(2rpx);
  }

  .score-main {
    font-size: 41rpx;
  }

  .score-label {
    font-size: 27rpx;
  }

  .score-meta {
    font-size: 19rpx;
  }

  .streak-heading {
    grid-template-columns: 104rpx minmax(0, 1fr);
  }

  .flame-wrap {
    width: 100rpx;
  }

  .streak-title {
    font-size: 31rpx;
  }

  .streak-subtitle {
    font-size: 19rpx;
  }

  .metric-card {
    min-height: 158rpx;
    padding-right: 19rpx;
    padding-left: 19rpx;
  }

  .metric-value {
    font-size: 38rpx;
  }

  .metric-label {
    font-size: 25rpx;
  }

  .metric-note {
    font-size: 17rpx;
  }
}

@media (prefers-reduced-motion: reduce) {
  .header-refresh.spinning .refresh-glyph,
  .flame-mascot-image.is-animating {
    animation: none;
  }

  .score-card,
  .metric-card,
  .practice-button {
    transition: none;
  }
}
</style>
