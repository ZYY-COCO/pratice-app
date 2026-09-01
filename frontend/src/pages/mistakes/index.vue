<template>
  <view class="page mistakes-page" :style="pageInlineStyle">
    <AppPageHeader
      :title="retestMode ? '错题重测' : '错题本'"
      :subtitle="retestMode ? retestScopeText : ''"
      fixed
      @back="goBack"
    >
      <template #right>
        <button
          v-if="!retestMode"
          class="retest-entry-btn"
          :disabled="!isAuthed || retestCandidateMistakes.length === 0"
          @tap="startWrongRetest"
        >
          {{ retestButtonText }}
        </button>
      </template>
    </AppPageHeader>

    <template v-if="retestMode">
      <SectionCard v-if="retestCompleted" title="重测完成" subtitle="本轮错题复盘结果">
        <view class="retest-summary-card">
          <view class="summary-score">{{ retestCorrectCount }} / {{ retestTotal }}</view>
          <view class="summary-copy">
            本轮共重测 {{ retestTotal }} 道错题，答对 {{ retestCorrectCount }} 道。
            建议优先回看红色题目，再进行一次短组复盘。
          </view>
          <view class="answer-map">
            <button
              v-for="(item, index) in retestResults"
              :key="item.question_id || index"
              class="answer-dot"
              :class="{ correct: item.is_correct, wrong: !item.is_correct }"
              @tap="jumpRetestReview(index)"
            >
              {{ index + 1 }}
            </button>
          </view>
          <view class="detail-actions">
            <button class="task-btn" @tap="restartWrongRetest">再测一遍</button>
            <button class="task-btn ghost" @tap="exitWrongRetest">返回错题本</button>
          </view>
        </view>
      </SectionCard>

      <view v-else-if="retestLoading" class="state-box">正在整理本题...</view>

      <SectionCard v-else-if="retestDetail" :title="`重测进度 ${retestProgressLabel}`">
        <view class="wrong-detail retest-detail">
          <MathText class="wrong-stem" :value="retestDetail.question.stem" />
          <view class="wrong-options">
            <button
              v-for="option in retestOptions"
              :key="option.key"
              class="wrong-option"
              :class="getRetestOptionClass(option.key)"
              @tap="selectRetestAnswer(option.key)"
            >
              <text class="option-key">{{ option.key }}</text>
              <MathText class="option-text" :value="option.text" />
            </button>
          </view>
          <view v-if="retestResultText" class="answer-line">正确答案：{{ retestDetail.question.answer }}</view>
          <MathText v-if="retestResultText" class="explain-text" :value="retestDetail.question.explanation" />
          <view class="detail-actions">
            <button
              v-if="!retestResultText"
              class="modal-submit-btn"
              :disabled="!retestAnswer || retestSubmitting"
              @tap="submitRetestAnswer"
            >
              {{ retestSubmitting ? '提交中...' : retestAnswer ? '提交答案' : '请选择一个答案' }}
            </button>
            <button v-else class="modal-submit-btn done" @tap="nextRetestQuestion">
              {{ retestIndex + 1 >= retestItems.length ? '查看重测结果' : '下一题' }}
            </button>
          </view>
        </view>
      </SectionCard>
    </template>

    <template v-else>
      <AppPageLoadingState v-if="wrongLoading" message="正在整理错题本..." />
      <SectionCard v-else>
        <view v-if="!isAuthed" class="state-box warning">登录后才能查看你的真实错题本。</view>
        <view v-else class="wrong-filter-card">
          <view class="wrong-filter-grid">
            <picker
              class="wrong-filter-select"
              mode="selector"
              :range="wrongSubjectPickerOptions"
              range-key="label"
              :value="wrongSubjectPickerIndex"
              @change="onWrongSubjectPickerChange"
            >
              <view class="wrong-filter-select-control">
                <text class="wrong-filter-select-name">科目</text>
                <text class="wrong-filter-select-value">{{ selectedWrongSubjectLabel }}</text>
                <view class="wrong-filter-select-arrow-icon" aria-hidden="true"></view>
              </view>
            </picker>

            <picker
              class="wrong-filter-select"
              :class="{ disabled: !wrongFilters.subject }"
              mode="selector"
              :range="wrongModulePickerOptions"
              range-key="label"
              :value="wrongModulePickerIndex"
              :disabled="!wrongFilters.subject"
              @change="onWrongModulePickerChange"
            >
              <view class="wrong-filter-select-control">
                <text class="wrong-filter-select-name">模块</text>
                <text class="wrong-filter-select-value" :class="{ muted: !wrongFilters.subject }">{{ selectedWrongModuleLabel }}</text>
                <view class="wrong-filter-select-arrow-icon" aria-hidden="true"></view>
              </view>
            </picker>

            <picker
              class="wrong-filter-select is-submodule"
              :class="{ disabled: !wrongFilters.module }"
              mode="selector"
              :range="wrongSubmodulePickerOptions"
              range-key="label"
              :value="wrongSubmodulePickerIndex"
              :disabled="!wrongFilters.module"
              @change="onWrongSubmodulePickerChange"
            >
              <view class="wrong-filter-select-control">
                <text class="wrong-filter-select-name">子模块</text>
                <text class="wrong-filter-select-value" :class="{ muted: !wrongFilters.module }">{{ selectedWrongSubmoduleLabel }}</text>
                <view class="wrong-filter-select-arrow-icon" aria-hidden="true"></view>
              </view>
            </picker>
          </view>
        </view>
        <view v-if="wrongError" class="state-box warning">{{ wrongError }}</view>
        <AppEmptyState
          v-else-if="isAuthed && filteredMistakes.length === 0"
          label="暂无错题"
          title="当前筛选条件下还没有错题"
          description="继续练习后，答错的题目会自动收录在这里。"
        />
        <MistakeList v-else :items="visibleMistakes" @select="openWrongDetail" />
        <view v-if="isAuthed && (fullMistakes.length || wrongHasMore)" class="list-load-state" @tap="loadMoreMistakes">
          {{ wrongLoadingMore ? '正在加载更多错题…' : hasMoreMistakes ? '继续下滑加载更多错题' : '已加载全部错题' }}
        </view>
      </SectionCard>
    </template>

    <view v-if="selectedWrongDetail" class="wrong-modal-mask" @tap="closeWrongDetail">
      <view class="wrong-modal-panel" @tap.stop>
        <view class="wrong-modal-grabber"></view>
        <view class="wrong-modal-head">
          <view class="wrong-modal-heading">
            <view class="wrong-modal-title">错题重练</view>
            <view class="wrong-modal-sub">
              {{ selectedWrongDetail.question.subject }} / {{ selectedWrongDetail.question.module }}
            </view>
          </view>
          <button class="wrong-modal-close" aria-label="关闭" @tap="closeWrongDetail"><CloseIcon /></button>
        </view>
        <scroll-view scroll-y class="wrong-modal-scroll">
          <view class="wrong-detail">
            <view class="wrong-section-label">题目</view>
            <MathText class="wrong-stem" :value="selectedWrongDetail.question.stem" />
            <view class="wrong-section-label">选项</view>
            <view class="wrong-options">
              <button
                v-for="option in wrongDetailOptions"
                :key="option.key"
                class="wrong-option"
                :class="getWrongOptionClass(option.key)"
                @tap="selectReviewAnswer(option.key)"
              >
                <text class="option-key">{{ option.key }}</text>
                <MathText class="option-text" :value="option.text" />
              </button>
            </view>
            <view v-if="!reviewResultText" class="review-hint">
              <text class="review-hint-main">上次选择：{{ selectedWrongDetail.latest_selected_answer || '暂无记录' }}</text>
              <text class="review-hint-sub">提交后查看正确答案与解析</text>
            </view>
            <view v-if="reviewResultText" class="state-box" :class="{ mastered: reviewMastered }">{{ reviewResultText }}</view>
            <view v-if="reviewResultText" class="answer-line">正确答案：{{ selectedWrongDetail.question.answer }}</view>
            <MathText v-if="reviewResultText" class="explain-text" :value="selectedWrongDetail.question.explanation" />
            <view class="detail-actions">
              <button
                v-if="!reviewResultText"
                class="modal-submit-btn"
                :disabled="!reviewAnswer || reviewingWrong"
                @tap="submitWrongReview"
              >
                {{ reviewingWrong ? '提交中...' : reviewAnswer ? '提交答案' : '请选择一个答案' }}
              </button>
              <button v-else class="modal-submit-btn done" @tap="closeWrongDetail">我知道了</button>
            </view>
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { onBackPress, onShow } from '@dcloudio/uni-app'
import { fetchLearningSummary } from '../../api/reports'
import { fetchWrongQuestionDetail, fetchWrongQuestions, reviewWrongQuestion } from '../../api/wrongQuestions'
import CloseIcon from '../../components/CloseIcon.vue'
import MathText from '../../components/MathText.vue'
import MistakeList from '../../components/MistakeList.vue'
import SectionCard from '../../components/SectionCard.vue'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import { getFullMistakes } from '../../mock/appMock'
import { isLoggedIn } from '../../utils/auth'
import { EXAM_OPTIONS } from '../../utils/exam'
import { buildMpPageSafeStyle } from '../../utils/mpSafeLayout'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const examCode = ref(uni.getStorageSync('examCode') || 'Z001')
const authed = ref(isLoggedIn())
const wrongItems = ref([])
const wrongLoading = ref(false)
const wrongNextCursor = ref('')
const wrongHasMore = ref(false)
const wrongLoadingMore = ref(false)
const wrongError = ref('')
const visibleMistakeCount = ref(15)
const wrongFilters = ref({
  subject: '',
  module: '',
  submodule: ''
})
const selectedWrongDetail = ref(null)
const reviewAnswer = ref('')
const reviewingWrong = ref(false)
const reviewResultText = ref('')
const reviewMastered = ref(false)
const reviewSubmissionId = ref('')
const retestMode = ref(false)
const retestItems = ref([])
const retestIndex = ref(0)
const retestDetail = ref(null)
const retestAnswer = ref('')
const retestSubmitting = ref(false)
const retestResultText = ref('')
const retestResults = ref([])
const retestLoading = ref(false)
const retestCompleted = ref(false)
const retestSubmissionIds = ref({})
const learningSummary = ref(null)
const themeInlineStyle = ref(buildThemeStyle(getStoredThemeKey()))
const mpLayoutStyle = ref(buildMpPageSafeStyle())
const pageInlineStyle = computed(() => [themeInlineStyle.value, mpLayoutStyle.value].filter(Boolean).join(';'))

const isAuthed = computed(() => authed.value)
const realMistakes = computed(() => wrongItems.value.map(formatWrongQuestion))
const activeExamSubjects = computed(() => {
  const option = EXAM_OPTIONS.find((item) => item.code === examCode.value) || EXAM_OPTIONS[0]
  return option?.subjects || []
})
const examMistakes = computed(() => (
  realMistakes.value.filter((item) => activeExamSubjects.value.includes(item.subject))
))
const filteredMistakes = computed(() => (
  examMistakes.value.filter((item) => {
    if (wrongFilters.value.subject && item.subject !== wrongFilters.value.subject) return false
    if (wrongFilters.value.module && item.module !== wrongFilters.value.module) return false
    if (wrongFilters.value.submodule && item.submodule !== wrongFilters.value.submodule) return false
    return true
  })
))
const fullMistakes = computed(() => (isAuthed.value ? filteredMistakes.value : getFullMistakes()))
const visibleMistakes = computed(() => fullMistakes.value.slice(0, visibleMistakeCount.value))
const hasMoreMistakes = computed(() => (
  visibleMistakeCount.value < fullMistakes.value.length || wrongHasMore.value
))
const retestCandidateMistakes = computed(() => (isAuthed.value ? filteredMistakes.value : []))
const retestTotal = computed(() => retestItems.value.length)
const retestCorrectCount = computed(() => retestResults.value.filter((item) => item.is_correct).length)
const retestProgressLabel = computed(() => {
  if (!retestTotal.value) return '0 / 0'
  return `${Math.min(retestIndex.value + 1, retestTotal.value)} / ${retestTotal.value}`
})
const retestOptions = computed(() => buildQuestionOptions(retestDetail.value?.question))
const subjectFilters = computed(() => [
  '',
  ...activeExamSubjects.value.filter((subject) => examMistakes.value.some((item) => item.subject === subject))
])
const moduleFilters = computed(() => buildFilterOptions(examMistakes.value, 'module', { subject: wrongFilters.value.subject }))
const submoduleFilters = computed(() => (
  buildFilterOptions(examMistakes.value, 'submodule', {
    subject: wrongFilters.value.subject,
    module: wrongFilters.value.module
  })
))
const wrongSubjectPickerOptions = computed(() => toWrongFilterPickerOptions(subjectFilters.value, '全部科目'))
const wrongModulePickerOptions = computed(() => (
  wrongFilters.value.subject
    ? toWrongFilterPickerOptions(moduleFilters.value, '全部模块')
    : [{ value: '', label: '请先选科目' }]
))
const wrongSubmodulePickerOptions = computed(() => (
  wrongFilters.value.module
    ? toWrongFilterPickerOptions(submoduleFilters.value, '全部子模块')
    : [{ value: '', label: '请先选模块' }]
))
const wrongSubjectPickerIndex = computed(() => getWrongFilterPickerIndex(
  wrongSubjectPickerOptions.value,
  wrongFilters.value.subject
))
const wrongModulePickerIndex = computed(() => getWrongFilterPickerIndex(
  wrongModulePickerOptions.value,
  wrongFilters.value.module
))
const wrongSubmodulePickerIndex = computed(() => getWrongFilterPickerIndex(
  wrongSubmodulePickerOptions.value,
  wrongFilters.value.submodule
))
const selectedWrongSubjectLabel = computed(() => wrongSubjectPickerOptions.value[wrongSubjectPickerIndex.value]?.label || '全部科目')
const selectedWrongModuleLabel = computed(() => wrongModulePickerOptions.value[wrongModulePickerIndex.value]?.label || '请先选科目')
const selectedWrongSubmoduleLabel = computed(() => wrongSubmodulePickerOptions.value[wrongSubmodulePickerIndex.value]?.label || '请先选模块')
const wrongFilterScopeParts = computed(() => (
  [wrongFilters.value.subject, wrongFilters.value.module, wrongFilters.value.submodule].filter(Boolean)
))
const retestScopeText = computed(() => {
  const scope = wrongFilterScopeParts.value.length ? wrongFilterScopeParts.value.join(' / ') : '全部错题'
  return `正在重测：${scope}，可随时退出。`
})
const retestButtonText = computed(() => {
  if (!isAuthed.value || !wrongFilterScopeParts.value.length) return '重测错题'
  return `重测${wrongFilters.value.subject ? '本科目' : '当前范围'}`
})
const wrongDetailOptions = computed(() => buildQuestionOptions(selectedWrongDetail.value?.question))

watch(wrongFilters, () => {
  resetMistakeVisibleCount()
  if (isAuthed.value) void loadWrongQuestions({ reset: true })
}, { deep: true })

watch(wrongItems, resetMistakeVisibleCount)

onShow(() => {
  authed.value = isLoggedIn()
  examCode.value = uni.getStorageSync('examCode') || 'Z001'
  themeInlineStyle.value = buildThemeStyle(getStoredThemeKey())
  mpLayoutStyle.value = buildMpPageSafeStyle()
  if (isAuthed.value) {
    void loadWrongQuestions({ reset: true })
    void loadLearningSummary()
  } else {
    wrongItems.value = []
    wrongNextCursor.value = ''
    wrongHasMore.value = false
    wrongError.value = ''
  }
})

onBackPress(() => {
  if (selectedWrongDetail.value) {
    closeWrongDetail()
    return true
  }
  if (retestMode.value) {
    confirmExitRetest()
    return true
  }
  return false
})

async function loadWrongQuestions({ reset = true } = {}) {
  if (!isAuthed.value || wrongLoading.value || wrongLoadingMore.value) return
  if (reset) {
    wrongItems.value = []
    wrongNextCursor.value = ''
    wrongHasMore.value = false
    wrongLoading.value = true
  } else {
    wrongLoadingMore.value = true
  }
  wrongError.value = ''
  try {
    const response = await fetchWrongQuestions({
      limit: 30,
      subject: wrongFilters.value.subject || undefined,
      module: wrongFilters.value.module || undefined,
      submodule: wrongFilters.value.submodule || undefined,
      cursor: reset ? undefined : (wrongNextCursor.value || undefined)
    })
    const nextItems = Array.isArray(response?.items) ? response.items : []
    wrongItems.value = reset
      ? nextItems
      : [...wrongItems.value, ...nextItems.filter((item) => !wrongItems.value.some((existing) => existing.id === item.id))]
    wrongNextCursor.value = String(response?.next_cursor || '')
    wrongHasMore.value = response?.has_more === true
  } catch (error) {
    wrongError.value = getSafeError(error, '错题本同步失败，请稍后重试')
  } finally {
    if (reset) wrongLoading.value = false
    else wrongLoadingMore.value = false
  }
}

async function loadLearningSummary() {
  try {
    learningSummary.value = await fetchLearningSummary({ exam_code: examCode.value })
  } catch (error) {
    learningSummary.value = null
  }
}

function formatWrongQuestion(item) {
  const question = item?.question || {}
  const title = question.stem || `错题 ${item?.question_id || ''}`
  const tags = [
    question.subject,
    question.module,
    question.submodule,
    item?.wrong_count ? `错 ${item.wrong_count} 次` : ''
  ].filter(Boolean)

  return {
    id: item?.question_id || item?.id,
    title,
    subject: question.subject || '',
    module: question.module || '',
    submodule: question.submodule || '',
    wrongCount: item?.wrong_count || 0,
    lastWrongAt: item?.last_wrong_at || '',
    meta: `错 ${item?.wrong_count || 0} 次 · 最近：${formatDateTime(item?.last_wrong_at)}`,
    tags: tags.length ? tags : ['真实错题', '待补充标签']
  }
}

function buildFilterOptions(items, field, constraints = {}) {
  const values = items
    .filter((item) => {
      if (constraints.subject && item.subject !== constraints.subject) return false
      if (constraints.module && item.module !== constraints.module) return false
      return true
    })
    .map((item) => item[field])
    .filter(Boolean)
  return ['', ...Array.from(new Set(values))]
}

function toWrongFilterPickerOptions(values, allLabel) {
  return values.map((value) => ({ value, label: value || allLabel }))
}

function getWrongFilterPickerIndex(options, value) {
  return Math.max(0, options.findIndex((item) => item.value === value))
}

function getWrongFilterPickerValue(event, options) {
  const option = options[Number(event?.detail?.value)] || options[0]
  return option?.value || ''
}

function onWrongSubjectPickerChange(event) {
  setWrongFilter('subject', getWrongFilterPickerValue(event, wrongSubjectPickerOptions.value))
}

function onWrongModulePickerChange(event) {
  setWrongFilter('module', getWrongFilterPickerValue(event, wrongModulePickerOptions.value))
}

function onWrongSubmodulePickerChange(event) {
  setWrongFilter('submodule', getWrongFilterPickerValue(event, wrongSubmodulePickerOptions.value))
}

function setWrongFilter(field, value) {
  if (wrongFilters.value[field] === value) return
  wrongFilters.value = { ...wrongFilters.value, [field]: value }
  if (field === 'subject') {
    wrongFilters.value.module = ''
    wrongFilters.value.submodule = ''
  }
  if (field === 'module') wrongFilters.value.submodule = ''
}

function resetMistakeVisibleCount() {
  visibleMistakeCount.value = 15
}

function loadMoreMistakes() {
  if (visibleMistakeCount.value < fullMistakes.value.length) {
    visibleMistakeCount.value += 15
    return
  }
  if (wrongHasMore.value) void loadWrongQuestions({ reset: false })
}

function goBack() {
  if (retestMode.value) {
    confirmExitRetest()
    return
  }
  uni.navigateBack({
    delta: 1,
    fail() {
      uni.reLaunch({ url: '/pages/home/index?tab=profile' })
    }
  })
}

async function openWrongDetail(item) {
  if (!isAuthed.value || !item?.id) return

  selectedWrongDetail.value = null
  reviewAnswer.value = ''
  reviewResultText.value = ''
  reviewMastered.value = false
  reviewSubmissionId.value = ''
  try {
    selectedWrongDetail.value = await fetchWrongQuestionDetail(item.id)
    reviewSubmissionId.value = createAnswerSubmissionId(getDetailQuestionId(selectedWrongDetail.value), 'review')
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '错题详情读取失败'), icon: 'none' })
  }
}

function closeWrongDetail() {
  selectedWrongDetail.value = null
  reviewAnswer.value = ''
  reviewResultText.value = ''
  reviewMastered.value = false
  reviewSubmissionId.value = ''
}

function buildQuestionOptions(question) {
  if (!question) return []
  return ['A', 'B', 'C', 'D']
    .map((key) => ({ key, text: question[`option_${key.toLowerCase()}`] || '' }))
    .filter((option) => option.text)
}

function selectReviewAnswer(key) {
  if (reviewingWrong.value || reviewResultText.value) return
  reviewAnswer.value = key
}

function getWrongOptionClass(key) {
  const correct = selectedWrongDetail.value?.question?.answer
  return {
    selected: reviewAnswer.value === key,
    correct: reviewResultText.value && correct === key,
    wrong: reviewResultText.value && reviewAnswer.value === key && correct !== key
  }
}

function getDetailQuestionId(detail) {
  return detail?.question_id || detail?.question?.id || ''
}

function createAnswerSubmissionId(questionId, kind = 'review') {
  const normalizedId = String(questionId || '').trim()
  if (!normalizedId) return null
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}:${kind}:${normalizedId}`.slice(0, 120)
}

function getRetestSubmissionId(questionId) {
  const normalizedId = String(questionId || '').trim()
  if (!normalizedId) return null
  if (retestSubmissionIds.value[normalizedId]) return retestSubmissionIds.value[normalizedId]
  const nextId = createAnswerSubmissionId(normalizedId, 'retest')
  retestSubmissionIds.value = { ...retestSubmissionIds.value, [normalizedId]: nextId }
  return nextId
}

async function submitWrongReview() {
  if (!selectedWrongDetail.value || !reviewAnswer.value) return

  reviewingWrong.value = true
  try {
    const result = await reviewWrongQuestion({
      question_id: getDetailQuestionId(selectedWrongDetail.value),
      client_submission_id: reviewSubmissionId.value,
      selected_answer: reviewAnswer.value,
      used_time: 0,
      exam_code: examCode.value
    })
    reviewMastered.value = Boolean(result.is_correct)
    reviewResultText.value = result.is_correct
      ? '本次重做答对，已掌握。'
      : `本次仍需复盘，正确答案是 ${result.correct_answer}。`
    await loadLearningSummary()
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '重做提交失败'), icon: 'none' })
  } finally {
    reviewingWrong.value = false
  }
}

function shuffleMistakes(items) {
  const result = items.slice()
  for (let index = result.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1))
    const current = result[index]
    result[index] = result[randomIndex]
    result[randomIndex] = current
  }
  return result
}

async function startWrongRetest() {
  if (!isAuthed.value) {
    uni.showToast({ title: '登录后才能重测错题', icon: 'none' })
    return
  }
  if (realMistakes.value.length === 0) {
    uni.showToast({ title: '当前还没有可重测的错题', icon: 'none' })
    return
  }
  if (retestCandidateMistakes.value.length === 0) {
    uni.showToast({ title: '当前筛选范围下没有可重测的错题', icon: 'none' })
    return
  }

  selectedWrongDetail.value = null
  retestItems.value = shuffleMistakes(retestCandidateMistakes.value)
  retestIndex.value = 0
  retestResults.value = []
  retestSubmissionIds.value = {}
  retestCompleted.value = false
  retestMode.value = true
  await loadRetestQuestion()
}

async function loadRetestQuestion() {
  const item = retestItems.value[retestIndex.value]
  if (!item?.id) {
    retestCompleted.value = true
    return
  }

  retestLoading.value = true
  retestDetail.value = null
  retestAnswer.value = ''
  retestResultText.value = ''
  try {
    retestDetail.value = await fetchWrongQuestionDetail(item.id)
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '重测题目读取失败'), icon: 'none' })
  } finally {
    retestLoading.value = false
  }
}

function selectRetestAnswer(key) {
  if (retestSubmitting.value || retestResultText.value) return
  retestAnswer.value = key
}

function getRetestOptionClass(key) {
  const correct = retestDetail.value?.question?.answer
  return {
    selected: retestAnswer.value === key,
    correct: retestResultText.value && correct === key,
    wrong: retestResultText.value && retestAnswer.value === key && correct !== key
  }
}

async function submitRetestAnswer() {
  if (!retestDetail.value || !retestAnswer.value || retestResultText.value) return

  retestSubmitting.value = true
  try {
    const result = await reviewWrongQuestion({
      question_id: getDetailQuestionId(retestDetail.value),
      client_submission_id: getRetestSubmissionId(getDetailQuestionId(retestDetail.value)),
      selected_answer: retestAnswer.value,
      used_time: 0,
      exam_code: examCode.value
    })
    const isCorrect = Boolean(result.is_correct)
    const correctAnswer = result.correct_answer || retestDetail.value?.question?.answer || ''
    retestResultText.value = isCorrect ? '本题答对，继续保持。' : `本题答错，正确答案是 ${correctAnswer}。`
    retestResults.value[retestIndex.value] = {
      question_id: getDetailQuestionId(retestDetail.value),
      selected_answer: retestAnswer.value,
      correct_answer: correctAnswer,
      is_correct: isCorrect
    }
    await loadLearningSummary()
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '重测提交失败'), icon: 'none' })
  } finally {
    retestSubmitting.value = false
  }
}

async function nextRetestQuestion() {
  if (retestIndex.value + 1 >= retestItems.value.length) {
    retestCompleted.value = true
    await loadWrongQuestions()
    await loadLearningSummary()
    return
  }
  retestIndex.value += 1
  await loadRetestQuestion()
}

function jumpRetestReview(index) {
  if (index < 0 || index >= retestItems.value.length) return
  retestCompleted.value = false
  retestIndex.value = index
  void loadRetestQuestion()
}

function restartWrongRetest() {
  void startWrongRetest()
}

function exitWrongRetest() {
  retestMode.value = false
  retestItems.value = []
  retestIndex.value = 0
  retestDetail.value = null
  retestAnswer.value = ''
  retestResultText.value = ''
  retestResults.value = []
  retestSubmissionIds.value = {}
  retestLoading.value = false
  retestCompleted.value = false
  void loadWrongQuestions()
  void loadLearningSummary()
}

function confirmExitRetest() {
  uni.showModal({
    title: '退出重测？',
    content: '本轮重测进度不会继续保存，但已经提交的题目会同步到错题统计。',
    confirmText: '退出',
    cancelText: '继续做题',
    success: (res) => {
      if (res.confirm) exitWrongRetest()
    }
  })
}

function getSafeError(error, fallback) {
  return error?.detail || error?.message || fallback
}

function formatDateTime(value) {
  if (!value) return '暂无'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 10)
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.mistakes-page {
  box-sizing: border-box;
  width: 100%;
  max-width: 100vw;
  min-height: 100vh;
  min-height: 100dvh;
  overflow-x: hidden;
  padding: 0 22rpx calc(env(safe-area-inset-bottom) + 36rpx);
  background: var(--gyt-page-bg, #fbfcff);
}

button::after {
  border: 0;
}

.state-box {
  margin-bottom: 18rpx;
  padding: 20rpx 22rpx;
  border: 2rpx dashed var(--gyt-primary-border);
  border-radius: 22rpx;
  background: var(--gyt-primary-tint);
  color: #36527f;
  font-size: 24rpx;
  line-height: 1.6;
}

.state-box.warning {
  border-color: #fde7b0;
  background: #fff8eb;
  color: #9a6510;
}

.state-box.mastered {
  border-color: #b7ebc6;
  background: #effcf4;
  color: #17663a;
}

.wrong-detail,
.wrong-options,
.detail-actions {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.wrong-filter-card {
  margin: -2rpx 0 18rpx;
  padding: 14rpx;
  border: 2rpx solid rgba(221, 230, 246, 0.92);
  border-radius: 24rpx;
  background: rgba(247, 250, 255, 0.96);
}

.wrong-filter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.wrong-filter-select {
  display: block;
  min-width: 0;
}

.wrong-filter-select.is-submodule {
  grid-column: 1 / -1;
}

.wrong-filter-select-control {
  display: flex;
  align-items: center;
  gap: 8rpx;
  min-height: 64rpx;
  padding: 0 16rpx;
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  border-radius: 16rpx;
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.96);
}

.wrong-filter-select-name {
  flex: 0 0 auto;
  color: #69778c;
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 780;
}

.wrong-filter-select-value {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  color: #253047;
  font-size: 21rpx;
  line-height: 1.3;
  font-weight: 760;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wrong-filter-select-value.muted {
  color: #9aa5b6;
}

.wrong-filter-select-arrow-icon {
  width: 13rpx;
  height: 13rpx;
  flex: 0 0 auto;
  border-right: 3rpx solid var(--gyt-primary, #2563eb);
  border-bottom: 3rpx solid var(--gyt-primary, #2563eb);
  transform: translateY(-3rpx) rotate(45deg);
  box-sizing: border-box;
}

.wrong-filter-select.disabled .wrong-filter-select-control {
  border-color: #e5eaf3;
  background: rgba(245, 247, 251, 0.92);
}

.wrong-filter-select.disabled .wrong-filter-select-arrow-icon {
  border-color: #b2bac7;
}

.list-load-state {
  margin-top: 22rpx;
  padding: 18rpx 20rpx;
  border-radius: 24rpx;
  background: var(--gyt-primary-tint);
  color: #667085;
  text-align: center;
  font-size: 23rpx;
  line-height: 1.5;
}

.retest-entry-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 150rpx;
  min-height: 64rpx;
  margin: 0;
  padding: 0 22rpx;
  border: 0;
  border-radius: 22rpx;
  background: var(--gyt-primary);
  box-shadow: 0 14rpx 28rpx var(--gyt-primary-shadow);
  color: #ffffff;
  font-size: 24rpx;
  line-height: 1.2;
  font-weight: 900;
}

.retest-entry-btn:disabled {
  background: var(--gyt-primary-soft);
  box-shadow: none;
  color: #7a8aa6;
}

.wrong-stem {
  color: #172033;
  font-size: 30rpx;
  line-height: 1.7;
  font-weight: 800;
}

.answer-line,
.explain-text {
  color: #475467;
  font-size: 24rpx;
  line-height: 1.7;
}

.wrong-option {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  min-height: 76rpx;
  padding: 18rpx;
  border: 2rpx solid #e6ebf5;
  border-radius: 22rpx;
  background: #ffffff;
  color: #172033;
  text-align: left;
  font-size: 24rpx;
}

.wrong-option.selected {
  border-color: var(--gyt-primary);
  background: var(--gyt-primary-soft);
}

.wrong-option.correct {
  border-color: rgba(22, 163, 74, 0.45);
  background: rgba(22, 163, 74, 0.1);
}

.wrong-option.wrong {
  border-color: rgba(239, 68, 68, 0.45);
  background: rgba(239, 68, 68, 0.1);
}

.option-key {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 42rpx;
  height: 42rpx;
  border-radius: 14rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-weight: 900;
}

.task-btn {
  padding: 18rpx 22rpx;
  border: 0;
  border-radius: 22rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 24rpx;
  font-weight: 800;
}

.task-btn.ghost {
  border: 0;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
}

.wrong-modal-mask {
  position: fixed;
  right: 0;
  bottom: 0;
  left: 0;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: flex-end;
  padding: 22rpx 24rpx calc(env(safe-area-inset-bottom) + 22rpx);
  background: rgba(15, 23, 42, 0.46);
}

.wrong-modal-panel {
  width: 100%;
  max-height: 82vh;
  overflow: hidden;
  border-radius: 34rpx;
  background: #ffffff;
  box-shadow: 0 -20rpx 54rpx rgba(15, 23, 42, 0.22);
}

.wrong-modal-grabber {
  width: 72rpx;
  height: 8rpx;
  margin: 18rpx auto 0;
  border-radius: 999rpx;
  background: #d8dee9;
}

.wrong-modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 20rpx 34rpx 22rpx;
  border-bottom: 2rpx solid #eef2f8;
}

.wrong-modal-heading {
  flex: 1;
  min-width: 0;
}

.wrong-modal-title {
  color: #101828;
  font-size: 32rpx;
  line-height: 1.3;
  font-weight: 950;
}

.wrong-modal-sub {
  display: inline-flex;
  margin-top: 10rpx;
  padding: 7rpx 14rpx;
  border-radius: 999rpx;
  background: #f4f7fb;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.35;
  font-weight: 800;
}

.wrong-modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 54rpx;
  height: 54rpx;
  margin: 0 0 0 auto;
  flex: 0 0 54rpx;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  color: #667085;
  font-size: 32rpx;
  line-height: 50rpx;
  font-weight: 900;
}

.wrong-modal-scroll {
  max-height: 66vh;
  padding: 24rpx 34rpx 26rpx;
  box-sizing: border-box;
}

.wrong-modal-panel .wrong-detail {
  gap: 18rpx;
}

.wrong-section-label {
  margin-bottom: -6rpx;
  color: #667085;
  font-size: 21rpx;
  line-height: 1.2;
  font-weight: 900;
}

.wrong-modal-panel .wrong-stem {
  padding: 22rpx 24rpx;
  border: 2rpx solid #edf1f7;
  border-radius: 24rpx;
  background: #f8fafd;
  box-shadow: inset 0 0 0 1rpx rgba(255, 255, 255, 0.65);
  font-size: 29rpx;
  line-height: 1.56;
  text-align: left;
}

.wrong-modal-panel .wrong-options {
  width: 100%;
  gap: 14rpx;
}

.wrong-modal-panel .wrong-option {
  align-items: center;
  box-sizing: border-box;
  width: 100%;
  min-height: 78rpx;
  margin: 0;
  padding: 16rpx 18rpx;
  border-radius: 20rpx;
  box-shadow: none;
}

.wrong-modal-panel .option-key {
  width: 42rpx;
  height: 42rpx;
  flex: 0 0 42rpx;
  border-radius: 14rpx;
  font-size: 23rpx;
}

.retest-detail {
  gap: 24rpx;
}

.retest-detail .wrong-stem {
  padding: 18rpx 2rpx 8rpx;
  font-size: 32rpx;
  line-height: 1.65;
}

.retest-detail .wrong-options {
  width: 100%;
  gap: 18rpx;
}

.retest-detail .wrong-option {
  box-sizing: border-box;
  width: 100%;
  min-height: 98rpx;
  margin: 0;
  padding: 22rpx 24rpx;
  border-radius: 28rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 24rpx rgba(20, 31, 66, 0.05);
}

.retest-detail .option-key {
  width: 52rpx;
  height: 52rpx;
  flex: 0 0 52rpx;
  border-radius: 18rpx;
  font-size: 26rpx;
}

.retest-detail .detail-actions {
  margin-top: 6rpx;
}

.option-text {
  min-width: 0;
  flex: 1;
  color: #263247;
  font-size: 28rpx;
  line-height: 1.55;
  font-weight: 700;
}

.wrong-modal-panel .option-text {
  font-size: 26rpx;
  line-height: 1.45;
}

.review-hint {
  padding: 14rpx 18rpx;
  border-radius: 20rpx;
  background: #f8fafc;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.6;
}

.wrong-modal-panel .review-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8rpx 16rpx;
}

.review-hint-main {
  color: #475467;
  font-weight: 800;
}

.review-hint-sub {
  color: #98a2b3;
  text-align: right;
  font-weight: 700;
}

.modal-submit-btn {
  width: 100%;
  min-height: 82rpx;
  margin: 0;
  border: 0;
  border-radius: 22rpx;
  background: var(--gyt-primary);
  box-shadow: 0 16rpx 30rpx var(--gyt-primary-shadow);
  color: #ffffff;
  font-size: 26rpx;
  line-height: 82rpx;
  font-weight: 900;
}

.modal-submit-btn:disabled,
.modal-submit-btn[disabled] {
  background: #e8edf7;
  box-shadow: none;
  color: #98a2b3;
  opacity: 1;
}

.modal-submit-btn.done {
  background: #111827;
  box-shadow: 0 16rpx 30rpx rgba(17, 24, 39, 0.18);
}

.retest-summary-card {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.summary-score {
  color: var(--gyt-primary);
  font-size: 58rpx;
  line-height: 1;
  font-weight: 950;
  text-align: center;
}

.summary-copy {
  color: #475467;
  font-size: 26rpx;
  line-height: 1.7;
  text-align: center;
}

.answer-map {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 14rpx;
}

.answer-dot {
  width: 58rpx;
  height: 58rpx;
  border: 0;
  border-radius: 18rpx;
  color: #ffffff;
  font-size: 22rpx;
  line-height: 58rpx;
  font-weight: 900;
}

.answer-dot.correct {
  background: #16a34a;
}

.answer-dot.wrong {
  background: #ef4444;
}
</style>
