<template>
  <view class="page stats-page" :class="{ 'is-modal-open': goalModalOpen }" :style="themeInlineStyle">
    <view class="stats-shell">
      <view class="stats-header">
        <button class="stats-back-button" hover-class="none" aria-label="返回" @tap="goBack">
          <image class="stats-back-icon" src="/static/ui-icons/png/original/back.png" mode="aspectFit" />
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
          <view class="refresh-icon-wrap" aria-hidden="true"><AppRefreshIcon /></view>
        </button>
      </view>

      <view v-if="error" class="sync-notice" role="status">
        <text>{{ error }}</text>
        <button class="sync-retry" :disabled="loading" @tap="loadStats">重试</button>
      </view>

      <view class="study-goal-card-wrap">
        <view class="study-goal-card-depth" aria-hidden="true"></view>
        <view
          class="score-card"
          :class="{ 'is-pressed': goalCardPressed }"
          role="button"
          aria-label="双击设置学习任务"
          @tap="handleGoalCardTap"
          @touchstart="handleGoalCardTouchStart"
          @touchmove="handleGoalCardTouchMove"
          @touchend="handleGoalCardTouchEnd"
          @touchcancel="handleGoalCardTouchEnd"
        >
          <view class="score-illustration" aria-hidden="true">
            <view class="score-mascot-stage">
              <image class="score-mascot-image" src="/static/brand/study-stat-mascot.png" mode="aspectFit" />
              <!-- #ifndef APP-PLUS -->
              <svg class="score-mascot-blink-eye score-mascot-blink-eye--left" viewBox="0 0 32 22" xmlns="http://www.w3.org/2000/svg">
                <ellipse cx="16" cy="11" rx="16" ry="11" fill="#b4d9f8" />
                <path d="M6 12c4-6 16-6 20 0" fill="none" stroke="#111820" stroke-width="3.2" stroke-linecap="round" />
              </svg>
              <svg class="score-mascot-blink-eye score-mascot-blink-eye--right" viewBox="0 0 32 22" xmlns="http://www.w3.org/2000/svg">
                <ellipse cx="16" cy="11" rx="16" ry="11" fill="#afd5f6" />
                <path d="M6 12c4-6 16-6 20 0" fill="none" stroke="#111820" stroke-width="3.2" stroke-linecap="round" />
              </svg>
              <!-- #endif -->
            </view>
          </view>
          <view class="score-copy">
            <view
              class="score-toggle-area"
              role="button"
              :aria-label="goalMetricAriaLabel"
              @tap.stop="handleGoalMetricTap"
            >
              <view :key="goalMetricMode" class="score-toggle-content">
                <view
                  class="score-main"
                  :class="{
                    'is-empty': !studyGoal.configured,
                    'is-duration': studyGoal.configured && isDailyGoalMode
                  }"
                >
                  {{ goalMetricValue }}
                </view>
                <view class="score-label">{{ goalMetricLabel }}</view>
              </view>
            </view>
            <view class="score-meta">{{ goalMetricMeta }}</view>
          </view>
          <view class="score-action-hint">双击设置</view>
        </view>
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
              <image class="metric-icon-image" :src="item.iconSrc" mode="aspectFit" />
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
          <!-- #ifdef APP-PLUS -->
          <CanvasLineChart
            class="trend-chart"
            canvas-id="stats-trend-canvas"
            :view-width="320"
            :view-height="166"
            :points="chartPoints"
            :grid-y="chartGridY"
            line-color="#75b6b8"
            point-stroke="#75b6b8"
            fill-color="rgba(169, 214, 215, 0.3)"
            :area-baseline="128"
            :line-width="4"
            :point-radius="5"
            grid-color="#eeeeed"
            :grid-line-width="1.5"
          />
          <!-- #endif -->
          <!-- #ifndef APP-PLUS -->
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
          <!-- #endif -->
          <view class="trend-axis-labels">
            <text v-for="point in chartPoints" :key="`${point.key}-label`">{{ point.label }}</text>
          </view>
        </view>
        <AppEmptyState
          v-else
          compact
          label="暂无学习曲线"
          title="暂无学习曲线"
          description="完成至少两天练习后，这里会生成你的学习曲线。"
        />

        <button class="practice-button" @tap="goPractice">
          <text>开始今日训练</text>
          <text class="practice-button-arrow">→</text>
        </button>
      </view>

      <!-- #ifdef H5 -->
      <IcpFooter />
      <!-- #endif -->
    </view>

    <view v-if="goalModalOpen" class="study-goal-modal" @tap="closeStudyGoalModal">
      <view class="study-goal-panel-wrap" @tap.stop>
        <view class="study-goal-panel-depth" aria-hidden="true"></view>
        <view class="study-goal-panel" role="dialog" aria-label="设置学习任务">
          <view class="study-goal-panel-header">
            <view>
              <text class="study-goal-panel-eyebrow">学习任务</text>
              <text class="study-goal-panel-title">安排你的学习节奏</text>
            </view>
            <button class="study-goal-close" hover-class="none" aria-label="关闭" @tap="closeStudyGoalModal">×</button>
          </view>

          <view class="study-goal-setting">
            <view class="study-goal-setting-heading">
              <view>
                <text class="study-goal-setting-title">每日学习时长</text>
                <text class="study-goal-setting-note">每天留出一段稳定的专注时间</text>
              </view>
              <text class="study-goal-setting-value">{{ formatStudyDuration(goalDraft.dailyMinutes) }}</text>
            </view>
            <slider
              class="study-goal-slider"
              :value="goalDraft.dailyMinutes"
              :min="20"
              :max="180"
              :step="10"
              activeColor="#75b6b8"
              backgroundColor="#e7e5e3"
              block-color="#171817"
              :block-size="22"
              @changing="handleDailyMinutesChange"
              @change="handleDailyMinutesChange"
            />
            <view class="study-goal-range"><text>20min</text><text>3h</text></view>
          </view>

          <view class="study-goal-setting">
            <view class="study-goal-setting-heading">
              <view>
                <text class="study-goal-setting-title">每周刷题目标</text>
                <text class="study-goal-setting-note">以周为周期，进度更容易坚持</text>
              </view>
              <text class="study-goal-setting-value">{{ goalDraft.weeklyQuestionTarget }} 题</text>
            </view>
            <slider
              class="study-goal-slider"
              :value="goalDraft.weeklyQuestionTarget"
              :min="50"
              :max="2000"
              :step="50"
              activeColor="#75b6b8"
              backgroundColor="#e7e5e3"
              block-color="#171817"
              :block-size="22"
              @changing="handleWeeklyQuestionTargetChange"
              @change="handleWeeklyQuestionTargetChange"
            />
            <view class="study-goal-range"><text>50题</text><text>2000题</text></view>
          </view>

          <view class="study-goal-actions">
            <button
              class="study-goal-action study-goal-action-confirm"
              :disabled="goalSaving"
              hover-class="none"
              @tap="confirmStudyGoal"
            >
              {{ goalSaving ? '正在保存...' : '确定' }}
            </button>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow, onUnload } from '@dcloudio/uni-app'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppRefreshIcon from '../../components/ui/AppRefreshIcon.vue'
import CanvasLineChart from '../../components/CanvasLineChart.vue'
import IcpFooter from '../../components/IcpFooter.vue'
import { fetchFavorites } from '../../api/favorites'
import { fetchLearningSummary, fetchStudyGoal, saveStudyGoal } from '../../api/reports'
import { getAuthUser, isLoggedIn } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const authUser = ref(getAuthUser())
const examCode = ref(uni.getStorageSync('examCode') || authUser.value?.exam_target || 'Z001')
const loading = ref(false)
const error = ref('')
const favoriteCount = ref(0)
const favoriteLoaded = ref(false)
const summary = ref(createEmptySummary())
const studyGoal = ref(createDefaultStudyGoal())
const goalDraft = ref(createGoalDraft(studyGoal.value))
const goalModalOpen = ref(false)
const goalCardPressed = ref(false)
const goalMetricMode = ref('weekly')
const goalSaving = ref(false)

const GOAL_DOUBLE_TAP_WINDOW = 280
let lastGoalCardTapAt = 0
let lastGoalMetricTapAt = 0
let goalMetricTapTimer = null
let goalCardTouchStart = null
let goalCardPointerMoved = false

const totalAnswers = computed(() => Number(summary.value.total_answers || 0))
const correctAnswers = computed(() => Number(summary.value.correct_answers || 0))
const accuracy = computed(() => Number(summary.value.accuracy || 0))
const studyStreak = computed(() => Number(summary.value.study_streak || 0))
const streakSubtitle = computed(() => {
  if (studyStreak.value > 0) return `已坚持 ${studyStreak.value} 天，保持这个节奏`
  return '完成今天第一组题，点亮连续学习'
})
const weeklyAnswers = computed(() => Number(summary.value.weekly_answers || 0))
const wrongCount = computed(() => Number(summary.value.wrong_question_count || 0))
const favoriteValue = computed(() => (favoriteLoaded.value ? favoriteCount.value : '--'))
const studyDurationLabel = computed(() => formatStudyDuration(studyGoal.value.daily_minutes))
const todayStudySeconds = computed(() => Math.max(0, Number(summary.value.today_study_seconds || 0)))
const isDailyGoalMode = computed(() => goalMetricMode.value === 'daily')
const goalMetricValue = computed(() => {
  if (!studyGoal.value.configured) return '尚未设定'
  if (isDailyGoalMode.value) {
    return `${formatElapsedStudyDuration(todayStudySeconds.value)}/${formatCompactStudyMinutes(studyGoal.value.daily_minutes)}`
  }
  return `${weeklyAnswers.value}/${studyGoal.value.weekly_question_target}`
})
const goalMetricLabel = computed(() => {
  if (!studyGoal.value.configured) return '学习任务'
  return isDailyGoalMode.value ? '本日学习时长' : '本周学习任务'
})
const goalMetricMeta = computed(() => {
  if (!studyGoal.value.configured) return '双击设置每日时长与每周题量'
  return isDailyGoalMode.value
    ? `目标每日 ${studyDurationLabel.value} · 单击查看周任务`
    : `每日 ${studyDurationLabel.value} · 单击查看本日时长`
})
const goalMetricAriaLabel = computed(() => {
  if (!studyGoal.value.configured) return '学习任务尚未设定，双击打开设置'
  const nextLabel = isDailyGoalMode.value ? '本周学习任务' : '本日学习时长'
  return `当前${goalMetricLabel.value}${goalMetricValue.value}，单击切换为${nextLabel}，双击打开设置`
})

const metricCards = computed(() => [
  {
    key: 'total',
    value: totalAnswers.value,
    label: '累计作答',
    note: totalAnswers.value ? `正确 ${correctAnswers.value} 题` : '完成练习后自动累计',
    iconSrc: '/static/ui-icons/png/circle-materials/report.png'
  },
  {
    key: 'favorite',
    value: favoriteValue.value,
    label: '收藏题目',
    note: favoriteLoaded.value ? '随时回看重点题' : '正在同步收藏',
    iconSrc: '/static/ui-icons/png/circle-materials/favorite.png'
  },
  {
    key: 'wrong',
    value: wrongCount.value,
    label: '错题待复盘',
    note: wrongCount.value ? '建议优先处理' : '暂无待复盘错题',
    iconSrc: '/static/ui-icons/png/circle-materials/wrong-book.png'
  },
  {
    key: 'practice',
    value: weeklyAnswers.value,
    label: '本周刷题',
    note: summary.value.weekly_accuracy ? `本周正确率 ${Math.round(summary.value.weekly_accuracy)}%` : '本周还未开始',
    iconSrc: '/static/ui-icons/png/circle-materials/tab-practice.png'
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
      date: item?.date || '',
      active: total > 0,
      total,
      accuracy: item?.accuracy == null ? null : Number(item.accuracy),
      isToday: index === 6
    }
  })
})

const trendReady = computed(() => streakDays.value.filter((item) => item.accuracy !== null && item.total > 0).length >= 2)
const chartGridY = [28, 78, 128]
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
  const nextExamCode = uni.getStorageSync('examCode') || authUser.value?.exam_target || 'Z001'
  if (examCode.value !== nextExamCode) {
    goalMetricMode.value = 'weekly'
  }
  examCode.value = nextExamCode
  if (!isLoggedIn()) {
    uni.navigateTo({
      url: `/pages/login/index?redirect=${encodeURIComponent('/pages/leaderboard/index')}`
    })
    return
  }
  loadCachedStudyGoal()
  loadStats()
})

onUnload(() => {
  cancelGoalMetricToggle()
})

async function loadStats() {
  if (loading.value) return
  loading.value = true
  error.value = ''
  const [summaryResult, favoriteResult, studyGoalResult] = await Promise.allSettled([
    fetchLearningSummary({ exam_code: examCode.value }),
    fetchFavorites({ limit: 200 }),
    fetchStudyGoal({ exam_code: examCode.value })
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

  if (studyGoalResult.status === 'fulfilled') {
    const remoteGoal = studyGoalResult.value || {}
    if (remoteGoal.sync_available === false) {
      studyGoal.value = {
        ...studyGoal.value,
        exam_code: examCode.value,
        sync_available: false
      }
    } else {
      applyStudyGoal(remoteGoal)
    }
  } else {
    studyGoal.value = { ...studyGoal.value, sync_available: false }
    if (!error.value) {
      error.value = '学习任务暂时使用本机记录，其余统计已同步'
    }
  }
  loading.value = false
}

function handleGoalCardTouchStart(event) {
  const touch = event?.touches?.[0]
  goalCardTouchStart = touch
    ? { x: Number(touch.clientX ?? touch.pageX ?? 0), y: Number(touch.clientY ?? touch.pageY ?? 0) }
    : null
  goalCardPointerMoved = false
  goalCardPressed.value = true
}

function handleGoalCardTouchMove(event) {
  if (!goalCardTouchStart) return
  const touch = event?.touches?.[0]
  if (!touch) return
  const x = Number(touch.clientX ?? touch.pageX ?? 0)
  const y = Number(touch.clientY ?? touch.pageY ?? 0)
  if (Math.abs(x - goalCardTouchStart.x) > 10 || Math.abs(y - goalCardTouchStart.y) > 10) {
    goalCardPointerMoved = true
    goalCardPressed.value = false
  }
}

function handleGoalCardTouchEnd() {
  goalCardPressed.value = false
  goalCardTouchStart = null
}

function handleGoalCardTap() {
  goalCardPressed.value = false
  if (goalCardPointerMoved) {
    goalCardPointerMoved = false
    lastGoalCardTapAt = 0
    return
  }

  const now = Date.now()
  if (lastGoalCardTapAt && now - lastGoalCardTapAt <= GOAL_DOUBLE_TAP_WINDOW) {
    lastGoalCardTapAt = 0
    openStudyGoalModal()
    return
  }
  lastGoalCardTapAt = now
}

function handleGoalMetricTap() {
  goalCardPressed.value = false
  if (goalCardPointerMoved) {
    goalCardPointerMoved = false
    cancelGoalMetricToggle()
    return
  }

  const now = Date.now()
  if (lastGoalMetricTapAt && now - lastGoalMetricTapAt <= GOAL_DOUBLE_TAP_WINDOW) {
    cancelGoalMetricToggle()
    openStudyGoalModal()
    return
  }

  lastGoalMetricTapAt = now
  if (goalMetricTapTimer) clearTimeout(goalMetricTapTimer)
  goalMetricTapTimer = setTimeout(() => {
    goalMetricTapTimer = null
    lastGoalMetricTapAt = 0
    if (!studyGoal.value.configured) return
    goalMetricMode.value = isDailyGoalMode.value ? 'weekly' : 'daily'
  }, GOAL_DOUBLE_TAP_WINDOW)
}

function cancelGoalMetricToggle() {
  if (goalMetricTapTimer) {
    clearTimeout(goalMetricTapTimer)
    goalMetricTapTimer = null
  }
  lastGoalMetricTapAt = 0
}

function openStudyGoalModal() {
  cancelGoalMetricToggle()
  lastGoalCardTapAt = 0
  goalDraft.value = createGoalDraft(studyGoal.value)
  goalModalOpen.value = true
}

function closeStudyGoalModal() {
  if (goalSaving.value) return
  goalModalOpen.value = false
}

function handleDailyMinutesChange(event) {
  goalDraft.value.dailyMinutes = normalizeStepValue(event?.detail?.value, 20, 180, 10)
}

function handleWeeklyQuestionTargetChange(event) {
  goalDraft.value.weeklyQuestionTarget = normalizeStepValue(event?.detail?.value, 50, 2000, 50)
}

async function confirmStudyGoal() {
  if (goalSaving.value) return
  const draft = goalDraft.value
  const payload = {
    exam_code: examCode.value,
    daily_minutes: normalizeStepValue(draft.dailyMinutes, 20, 180, 10),
    weekly_question_target: normalizeStepValue(draft.weeklyQuestionTarget, 50, 2000, 50)
  }

  goalSaving.value = true
  try {
    const saved = await saveStudyGoal(payload)
    applyStudyGoal(saved)
    goalModalOpen.value = false
    uni.showToast({ title: '学习任务已保存', icon: 'none' })
  } catch (err) {
    uni.showModal({
      title: '保存未完成',
      content: getStudyGoalErrorMessage(err, '学习任务保存失败，请检查网络后重试'),
      showCancel: false
    })
  } finally {
    goalSaving.value = false
  }
}

function loadCachedStudyGoal() {
  const cached = uni.getStorageSync(getStudyGoalCacheKey())
  if (cached && typeof cached === 'object') {
    applyStudyGoal({ ...cached, exam_code: examCode.value }, { cache: false })
    return
  }
  studyGoal.value = createDefaultStudyGoal()
}

function applyStudyGoal(value, options = {}) {
  const normalized = normalizeStudyGoal(value)
  studyGoal.value = normalized
  if (options.cache !== false) {
    uni.setStorageSync(getStudyGoalCacheKey(), normalized)
  }
}

function normalizeStudyGoal(value = {}) {
  return {
    exam_code: value.exam_code === 'Z002' ? 'Z002' : examCode.value,
    configured: Boolean(value.configured),
    sync_available: value.sync_available !== false,
    daily_minutes: normalizeStepValue(value.daily_minutes, 20, 180, 10, 60),
    weekly_question_target: normalizeStepValue(value.weekly_question_target, 50, 2000, 50, 300),
    updated_at: value.updated_at || null
  }
}

function createDefaultStudyGoal() {
  return {
    exam_code: examCode.value,
    configured: false,
    sync_available: true,
    daily_minutes: 60,
    weekly_question_target: 300,
    updated_at: null
  }
}

function createGoalDraft(value = {}) {
  return {
    dailyMinutes: normalizeStepValue(value.daily_minutes, 20, 180, 10, 60),
    weeklyQuestionTarget: normalizeStepValue(value.weekly_question_target, 50, 2000, 50, 300)
  }
}

function getStudyGoalCacheKey() {
  const userId = authUser.value?.id || authUser.value?.user_id || 'signed-in-user'
  return `studyGoal:${userId}:${examCode.value}`
}

function formatStudyDuration(value) {
  const minutes = normalizeStepValue(value, 20, 180, 10, 60)
  const hours = Math.floor(minutes / 60)
  const remaining = minutes % 60
  if (hours && remaining) return `${hours}h ${remaining}min`
  if (hours) return `${hours}h`
  return `${remaining}min`
}

function formatCompactStudyMinutes(value) {
  const minutes = Math.max(0, Math.floor(Number(value || 0)))
  const hours = Math.floor(minutes / 60)
  const remaining = minutes % 60
  if (hours && remaining) return `${hours}h${remaining}min`
  if (hours) return `${hours}h`
  return `${remaining}min`
}

function formatElapsedStudyDuration(value) {
  const seconds = Math.max(0, Math.floor(Number(value || 0)))
  if (seconds > 0 && seconds < 60) return '<1min'
  return formatCompactStudyMinutes(Math.floor(seconds / 60))
}

function normalizeStepValue(value, min, max, step, fallback = min) {
  const numeric = Number(value)
  const safeValue = Number.isFinite(numeric) ? numeric : fallback
  const stepped = Math.round(safeValue / step) * step
  return Math.min(max, Math.max(min, stepped))
}

function getStudyGoalErrorMessage(err, fallback) {
  if (typeof err?.detail === 'string' && err.detail.trim()) return err.detail
  if (Array.isArray(err?.detail)) return err.detail[0]?.msg || fallback
  return fallback
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
    today_study_seconds: 0,
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

.stats-page.is-modal-open {
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
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

.refresh-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
}

.header-refresh.spinning .refresh-icon-wrap {
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

.study-goal-card-wrap {
  position: relative;
  margin-bottom: 36rpx;
  padding-bottom: 13rpx;
  isolation: isolate;
}

.study-goal-card-depth {
  position: absolute;
  z-index: 0;
  top: 0;
  right: 0;
  bottom: 13rpx;
  left: 0;
  border-radius: 46rpx;
  background: var(--stats-ink);
  transform: translate3d(0, 13rpx, 0);
  pointer-events: none;
}

.score-card {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 22rpx;
  min-height: 188rpx;
  box-sizing: border-box;
  padding: 28rpx 26rpx;
  border: 3rpx solid var(--stats-ink);
  border-radius: 46rpx;
  background: var(--stats-card);
  transform: translate3d(0, 0, 0);
  transition: transform 110ms cubic-bezier(0.2, 0.8, 0.25, 1);
  -webkit-user-select: none;
  user-select: none;
  touch-action: manipulation;
  will-change: transform;
  backface-visibility: hidden;
}

.score-card.is-pressed {
  transform: translate3d(0, 7rpx, 0);
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

.score-toggle-area {
  min-width: 0;
  touch-action: manipulation;
}

.score-toggle-content {
  animation: score-toggle-in 150ms cubic-bezier(0.2, 0.8, 0.25, 1) both;
}

.score-main {
  color: var(--stats-ink);
  font-size: 46rpx;
  line-height: 1.05;
  font-weight: 900;
  letter-spacing: -1rpx;
}

.score-main.is-empty {
  font-size: 36rpx;
  letter-spacing: 0;
}

.score-main.is-duration {
  font-size: 40rpx;
  letter-spacing: -1.5rpx;
  white-space: nowrap;
}

.score-label {
  margin-top: 9rpx;
  color: var(--stats-ink);
  font-size: 30rpx;
  line-height: 1.2;
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

@keyframes score-toggle-in {
  from {
    opacity: 0.42;
    transform: translate3d(0, 5rpx, 0);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0);
  }
}

.score-action-hint {
  flex: 0 0 auto;
  padding: 9rpx 13rpx;
  border: 2rpx solid rgba(23, 24, 23, 0.16);
  border-radius: 999rpx;
  background: #f2f0ef;
  color: #777371;
  font-size: 18rpx;
  line-height: 1.1;
  font-weight: 600;
  white-space: nowrap;
}

.study-goal-modal {
  position: fixed;
  z-index: 1200;
  inset: 0;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: calc(env(safe-area-inset-top) + 32rpx) 28rpx calc(env(safe-area-inset-bottom) + 32rpx);
  background: rgba(19, 20, 19, 0.42);
  animation: study-goal-backdrop-in 160ms ease-out both;
}

.study-goal-panel-wrap {
  position: relative;
  width: 100%;
  max-width: 680rpx;
  max-height: calc(100vh - 96rpx);
  max-height: calc(100dvh - 96rpx);
  padding-bottom: 12rpx;
  isolation: isolate;
  animation: study-goal-panel-in 190ms cubic-bezier(0.2, 0.82, 0.3, 1) both;
}

.study-goal-panel-depth {
  position: absolute;
  z-index: 0;
  top: 0;
  right: 0;
  bottom: 12rpx;
  left: 0;
  border-radius: 44rpx;
  background: var(--stats-ink);
  transform: translate3d(0, 12rpx, 0);
}

.study-goal-panel {
  position: relative;
  z-index: 1;
  max-height: calc(100vh - 108rpx);
  max-height: calc(100dvh - 108rpx);
  box-sizing: border-box;
  padding: 32rpx 30rpx 28rpx;
  overflow-y: auto;
  border: 3rpx solid var(--stats-line);
  border-radius: 44rpx;
  background: #ffffff;
  -webkit-overflow-scrolling: touch;
}

.study-goal-panel-header,
.study-goal-setting-heading,
.study-goal-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.study-goal-panel-header {
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.study-goal-panel-eyebrow,
.study-goal-panel-title,
.study-goal-setting-title,
.study-goal-setting-note {
  display: block;
}

.study-goal-panel-eyebrow {
  color: var(--stats-mint-deep);
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 2rpx;
}

.study-goal-panel-title {
  margin-top: 5rpx;
  color: var(--stats-ink);
  font-size: 36rpx;
  line-height: 1.18;
  font-weight: 800;
}

.study-goal-close {
  flex: 0 0 auto;
  width: 62rpx;
  height: 62rpx;
  margin: 0;
  padding: 0 0 4rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2rpx solid #dedbd9;
  border-radius: 50%;
  background: #f5f3f2;
  color: #595654;
  font-size: 38rpx;
  line-height: 1;
  font-weight: 400;
}

.study-goal-close::after,
.study-goal-action::after {
  border: 0;
}

.study-goal-setting {
  box-sizing: border-box;
  border: 2rpx solid #e4e1df;
  border-radius: 30rpx;
  background: #faf9f8;
}

.study-goal-setting {
  margin-top: 18rpx;
  padding: 24rpx 22rpx 19rpx;
}

.study-goal-setting-heading {
  align-items: flex-start;
  gap: 18rpx;
}

.study-goal-setting-heading > view {
  min-width: 0;
  flex: 1;
}

.study-goal-setting-title {
  color: var(--stats-ink);
  font-size: 27rpx;
  line-height: 1.25;
  font-weight: 700;
}

.study-goal-setting-note {
  margin-top: 6rpx;
  color: var(--stats-muted);
  font-size: 19rpx;
  line-height: 1.35;
  font-weight: 400;
}

.study-goal-setting-value {
  flex: 0 0 auto;
  color: var(--stats-ink);
  font-size: 27rpx;
  line-height: 1.2;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.study-goal-slider {
  margin: 23rpx 0 0;
}

.study-goal-range {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: -2rpx;
  color: #9b9795;
  font-size: 18rpx;
  line-height: 1.2;
  font-weight: 500;
}

.study-goal-actions {
  margin-top: 26rpx;
}

.study-goal-action {
  min-width: 0;
  min-height: 82rpx;
  margin: 0;
  padding: 0 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3rpx solid var(--stats-ink);
  border-radius: 28rpx;
  font-size: 25rpx;
  line-height: 1.2;
  font-weight: 700;
  transition: transform 100ms ease, background-color 120ms ease;
}

.study-goal-action:active {
  transform: translate3d(0, 3rpx, 0);
}

.study-goal-action[disabled] {
  opacity: 0.58;
}

.study-goal-action-confirm {
  flex: 1;
  width: 100%;
  background: var(--stats-ink);
  color: #ffffff;
}

@keyframes study-goal-backdrop-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes study-goal-panel-in {
  from {
    opacity: 0;
    transform: translate3d(0, 22rpx, 0) scale(0.98);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0) scale(1);
  }
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

.metric-icon-image {
  display: block;
  width: 100%;
  height: 100%;
  opacity: 0.82;
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

  .score-main.is-empty {
    font-size: 32rpx;
  }

  .score-main.is-duration {
    font-size: 35rpx;
  }

  .score-label {
    font-size: 27rpx;
  }

  .score-meta {
    font-size: 19rpx;
  }

  .score-action-hint {
    padding-right: 10rpx;
    padding-left: 10rpx;
    font-size: 16rpx;
  }

  .study-goal-panel {
    padding-right: 24rpx;
    padding-left: 24rpx;
  }

  .study-goal-panel-title {
    font-size: 32rpx;
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
  .header-refresh.spinning .refresh-icon-wrap,
  .flame-mascot-image.is-animating {
    animation: none;
  }

  .score-card,
  .metric-card,
  .practice-button,
  .study-goal-action {
    transition: none;
  }

  .score-toggle-content {
    animation: none;
  }

  .study-goal-modal,
  .study-goal-panel-wrap {
    animation: none;
  }
}
</style>
