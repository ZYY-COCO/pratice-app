<template>
  <view class="page practice-page">
    <view class="top-nav">
      <button class="back-btn" @tap="goBack">‹</button>
      <view class="top-copy">
        <view class="top-title">{{ pageTitle }}</view>
        <view class="top-sub">{{ examCode }} / {{ subject }}</view>
      </view>
    </view>

    <template v-if="mode === 'tags'">
      <view class="setup-hero">
        <view class="setup-eyebrow">刷题模式</view>
        <view class="setup-title">选择本轮练习方式</view>
        <view class="setup-sub">专项刷题按知识点训练；综合刷题会从当前科目全部知识点随机组卷。</view>
      </view>

      <view class="mode-card">
        <view
          v-for="item in practiceModeOptions"
          :key="item.value"
          class="mode-option"
          :class="{ active: practiceMode === item.value }"
          @tap="switchPracticeMode(item.value)"
        >
          <view class="mode-title">{{ item.label }}</view>
          <view class="mode-sub">{{ item.description }}</view>
        </view>
      </view>

      <view class="count-card">
        <view class="count-title">本轮题量</view>
        <view class="count-sub">
          {{ practiceMode === 'comprehensive' ? '综合刷题会从全部知识点随机抽题。' : '进入刷题前先选择数量，当前会按你选择的题量整组加载。' }}
        </view>
        <view class="count-options">
          <view
            v-for="count in questionCountOptions"
            :key="count"
            class="count-option"
            :class="{ active: selectedQuestionSize === count }"
            @tap="selectedQuestionSize = count"
          >
            {{ count }}题
          </view>
        </view>
      </view>

      <view v-if="practiceMode === 'comprehensive'" class="comprehensive-card">
        <view class="comprehensive-title">综合刷题规则</view>
        <view class="comprehensive-line">随机覆盖当前科目的全部知识点。</view>
        <view class="comprehensive-line">答题过程中不展示所属模块。</view>
        <view class="comprehensive-line">完成本轮并统一提交后，才公布答案和解析。</view>
      </view>

      <view v-if="loadError" class="state-box warning">{{ loadError }}</view>
      <view v-if="shortageTip" class="state-box">{{ shortageTip }}</view>

      <TagAccordion
        v-if="practiceMode === 'special'"
        :sections="subjectTree"
        :selected-tags="selectedTags"
        :open-map="openMap"
        :get-count="getCount"
        @toggle-open="toggleOpen"
        @toggle-tag="toggleTag"
      />

      <view class="sticky-bar">
        <view class="sticky-copy">
          <view class="sticky-title">{{ stickyTitle }}</view>
          <view class="sticky-sub">{{ stickySub }}</view>
          <view class="sticky-tip">本轮将加载 {{ plannedQuestionLimit }} 道题</view>
        </view>
        <button class="sticky-btn" :disabled="loading" @tap="startQuiz">
          {{ loading ? '加载中...' : startButtonText }}
        </button>
      </view>
    </template>

    <template v-else>
      <template v-if="summaryMode">
        <view class="summary-card">
          <view class="summary-kicker">综合刷题结果</view>
          <view class="summary-score">{{ correctCount }} / {{ reviewResults.length }}</view>
          <view class="summary-sub">绿色代表答对，红色代表答错。点击题号可直接查看对应解析。</view>
        </view>

        <view class="summary-grid">
          <button
            v-for="(item, index) in reviewResults"
            :key="item.question.questionId || item.question.id"
            class="summary-dot"
            :class="{ correct: item.isCorrect, wrong: !item.isCorrect }"
            @tap="openReviewQuestion(index)"
          >
            {{ index + 1 }}
          </button>
        </view>

        <view class="summary-actions">
          <button class="next-btn" @tap="openReviewQuestion(0)">从第 1 题开始看解析</button>
          <button class="ghost-button back-tags" @tap="resetToTags">返回刷题范围</button>
        </view>
      </template>

      <template v-else>
      <view class="quiz-shell">
        <view class="quiz-top">
          <view class="badge">{{ quizProgressText }}</view>
          <view class="timer">⏱ {{ formattedTimer }}</view>
        </view>

        <view class="question-card">
          <view class="question-head">
            <view class="badge plain">{{ questionBadgeText }}</view>
            <button
              class="favorite-btn"
              :class="{ active: currentFavorited }"
              :disabled="favoriteLoading || !canFavoriteCurrent"
              @tap.stop="toggleCurrentFavorite"
            >
              {{ currentFavorited ? '★' : '☆' }}
            </button>
          </view>
          <view class="question-title">{{ currentQuestion.stem }}</view>
          <view class="helper-box">{{ questionHelperText }}</view>
        </view>
      </view>

      <view class="options">
        <QuestionOption
          v-for="option in currentQuestion.options"
          :key="option.key"
          :option="option"
          :selected-key="selectedOption"
          :submitted="optionSubmitted"
          :correct-key="correctAnswer"
          @select="selectOption"
        />
      </view>

      <button
        v-if="!reviewMode"
        class="submit-btn"
        :disabled="!selectedOption || submitted || submitting"
        @tap="handlePrimaryAction"
      >
        {{ primaryButtonText }}
      </button>

      <view id="result-anchor">
        <ExplanationPanel
          :visible="submitting || submitted"
          :pending="submitting && !submitted"
          :correct-answer="correctAnswer"
          :explanation="answerExplanation"
          :auto-tag="resultTag"
        />
      </view>

      <view v-if="submitted && abilityAccuracy !== null && !reviewMode" class="result-note">
        当前知识点正确率：{{ abilityAccuracy }}%
      </view>

      <view v-if="submitted || reviewMode" class="action-row">
        <template v-if="reviewMode">
          <view class="review-nav-row">
            <button class="next-btn secondary" :disabled="!hasPrevQuestion" @tap="goPrevQuestion">上一题</button>
            <button class="next-btn" :disabled="!hasNextQuestion" @tap="goNextQuestion">下一题</button>
          </view>
          <button class="next-btn outline" @tap="showSummary">查看结果总览</button>
        </template>

        <template v-else>
          <button v-if="hasNextQuestion" class="next-btn" @tap="goNextQuestion">下一题</button>
          <button v-else class="next-btn done" @tap="finishQuiz">完成本轮</button>
        </template>
      </view>

      <button class="ghost-button back-tags" @tap="resetToTags">返回刷题范围</button>
      </template>
    </template>
  </view>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { onBackPress, onLoad, onShow, onUnload } from '@dcloudio/uni-app'
import { fetchFavoriteStatus, toggleFavorite } from '../../api/favorites'
import { request } from '../../api/http'
import ExplanationPanel from '../../components/ExplanationPanel.vue'
import QuestionOption from '../../components/QuestionOption.vue'
import TagAccordion from '../../components/TagAccordion.vue'
import { getPracticeQuestion, getTagCount } from '../../mock/appMock'
import { getSubjectTree } from '../../utils/knowledgeTree'

const practiceModeOptions = [
  {
    value: 'special',
    label: '专项刷题',
    description: '选择一个或多个知识点，提交后立即看解析。'
  },
  {
    value: 'comprehensive',
    label: '综合刷题',
    description: '全部知识点随机混合，整轮完成后统一公布答案。'
  }
]

const examCode = ref(uni.getStorageSync('examCode') || 'Z001')
const subject = ref(uni.getStorageSync('subject') || '中华文化')
const mode = ref('tags')
const practiceMode = ref('special')
const selectedTags = ref([])
const questionCountOptions = [10, 20]
const selectedQuestionSize = ref(10)
const selectedOption = ref('')
const submitted = ref(false)
const submitting = ref(false)
const loading = ref(false)
const loadError = ref('')
const shortageTip = ref('')
const timerSeconds = ref(0)
const accessToken = ref(readAccessToken())
const questionPool = ref([buildMockQuestion(subject.value, examCode.value)])
const currentQuestionIndex = ref(0)
const correctAnswer = ref('')
const answerExplanation = ref('')
const resultTag = ref('')
const abilityAccuracy = ref(null)
const currentFavorited = ref(false)
const favoriteLoading = ref(false)
const favoriteQuestionId = ref('')
const questionMeta = ref({
  questionId: '',
  module: '',
  submodule: ''
})
const comprehensiveAnswers = ref({})
const reviewMode = ref(false)
const reviewResults = ref([])
const summaryMode = ref(false)

const questionCache = new Map()
let timerId = null

const subjectTree = computed(() => getSubjectTree(subject.value))
const openMap = ref(buildOpenMap(subjectTree.value))
const hasAccessToken = computed(() => Boolean(accessToken.value))
const plannedQuestionLimit = computed(() => selectedQuestionSize.value)
const currentQuestion = computed(() => questionPool.value[currentQuestionIndex.value] || buildMockQuestion(subject.value, examCode.value))
const currentQuestionKey = computed(() => currentQuestion.value.questionId || currentQuestion.value.id)
const hasPrevQuestion = computed(() => currentQuestionIndex.value > 0)
const hasNextQuestion = computed(() => currentQuestionIndex.value < questionPool.value.length - 1)
const correctCount = computed(() => reviewResults.value.filter((item) => item.isCorrect).length)
const canFavoriteCurrent = computed(() => {
  const questionId = questionMeta.value.questionId
  return Boolean(questionId) && !String(questionId).startsWith('mock-')
})
const optionSubmitted = computed(() => reviewMode.value || submitted.value || (submitting.value && practiceMode.value === 'special'))
const pageTitle = computed(() => {
  if (mode.value === 'tags') {
    return '选择刷题范围'
  }
  return practiceMode.value === 'comprehensive' ? '综合刷题' : '专项刷题'
})
const dataModeLabel = computed(() => (hasAccessToken.value ? '将使用真实题库' : '当前使用 mock 题目'))
const selectedQuestionCount = computed(() => selectedTags.value.reduce((sum, tag) => sum + getCount(tag), 0))
const stickyTitle = computed(() => {
  if (practiceMode.value === 'comprehensive') {
    return `综合刷题：全部知识点`
  }
  return `已选：${selectedTags.value.length} 个考点`
})
const stickySub = computed(() => {
  if (practiceMode.value === 'comprehensive') {
    return `${dataModeLabel.value} · 覆盖 ${getAllModuleInfos().length} 个考点`
  }
  return `预计 ${selectedQuestionCount.value} 道题 · ${dataModeLabel.value}`
})
const startButtonText = computed(() => (practiceMode.value === 'comprehensive' ? '开始综合刷题' : '开始刷题'))
const quizProgressText = computed(() => {
  const prefix = reviewMode.value ? '查看解析' : '当前进度'
  return `${prefix} ${currentQuestionIndex.value + 1} / ${questionPool.value.length}`
})
const questionBadgeText = computed(() => {
  if (practiceMode.value === 'comprehensive') {
    return reviewMode.value ? '综合刷题 · 解析回顾' : '综合刷题 · 隐藏知识点'
  }
  return `${currentQuestion.value.year} · ${currentQuestion.value.badge}`
})
const questionHelperText = computed(() => {
  if (practiceMode.value === 'comprehensive') {
    return reviewMode.value ? '答案和解析已公布，可逐题回看。' : '本题知识点已隐藏，完成本轮后统一公布答案。'
  }
  return currentQuestion.value.helper
})
const primaryButtonText = computed(() => {
  if (practiceMode.value === 'comprehensive') {
    if (submitting.value) {
      return '正在提交整卷...'
    }
    return hasNextQuestion.value ? '下一题' : '提交整卷并查看答案'
  }
  return submitted.value ? '解析已展开' : submitting.value ? '正在判题...' : '提交并查看解析'
})

const formattedTimer = computed(() => {
  const min = String(Math.floor(timerSeconds.value / 60)).padStart(2, '0')
  const sec = String(timerSeconds.value % 60).padStart(2, '0')
  return `${min}:${sec}`
})

watch(subject, () => {
  openMap.value = buildOpenMap(getSubjectTree(subject.value))
  questionPool.value = [buildMockQuestion(subject.value, examCode.value)]
  currentQuestionIndex.value = 0
  resetQuizState()
})

onLoad((options) => {
  syncAccessToken()
  if (options?.subject) {
    subject.value = decodeURIComponent(options.subject)
    uni.setStorageSync('subject', subject.value)
  }
  openMap.value = buildOpenMap(getSubjectTree(subject.value))
  if (options?.module && options?.submodule) {
    const module = decodeURIComponent(options.module)
    const submodule = decodeURIComponent(options.submodule)
    openMap.value = {
      ...openMap.value,
      [module]: true
    }
    selectedTags.value = [submodule]
  }
})

onShow(() => {
  syncAccessToken()
})

onUnload(() => {
  clearTimer()
})

onBackPress(() => {
  if (summaryMode.value || reviewMode.value || mode.value === 'quiz') {
    confirmExitPractice()
    return true
  }
  return false
})

function buildOpenMap(sections) {
  return sections.reduce((result, item, index) => {
    result[item.module] = index === 0
    return result
  }, {})
}

function readAccessToken() {
  let token = ''

  try {
    token = uni.getStorageSync('accessToken') || ''
  } catch (error) {
    token = ''
  }

  if (!token && typeof window !== 'undefined' && window.localStorage) {
    token = window.localStorage.getItem('uni-storage-accessToken') || window.localStorage.getItem('accessToken') || ''
  }

  return typeof token === 'string' ? token.trim() : ''
}

function syncAccessToken() {
  const token = readAccessToken()
  accessToken.value = token
  if (token) {
    uni.setStorageSync('accessToken', token)
  }
}

function buildMockQuestion(nextSubject, nextExamCode, index = 0) {
  const mock = getPracticeQuestion(nextSubject, nextExamCode)
  return {
    ...mock,
    id: `${mock.id}-${index}`,
    year: mock.year || '题库练习',
    badge: mock.badge || '专项练习',
    helper: `${mock.helper}（mock 模式）`
  }
}

function buildApiQuestion(apiQuestion, meta) {
  const options = [
    { key: 'A', text: apiQuestion.option_a },
    { key: 'B', text: apiQuestion.option_b },
    { key: 'C', text: apiQuestion.option_c },
    { key: 'D', text: apiQuestion.option_d }
  ]
  if (apiQuestion.option_e) {
    options.push({ key: 'E', text: apiQuestion.option_e })
  }

  return {
    id: apiQuestion.id,
    year: apiQuestion.source_year ? `${apiQuestion.source_year} 年题目` : '题库练习',
    badge: meta.submodule || apiQuestion.submodule || meta.module || apiQuestion.module,
    stem: apiQuestion.stem,
    helper: `当前来自真实题库：${apiQuestion.subject} / ${apiQuestion.module} / ${apiQuestion.submodule}`,
    options,
    answer: '',
    explanation: '',
    autoTag: '',
    questionId: apiQuestion.id,
    module: apiQuestion.module,
    submodule: apiQuestion.submodule
  }
}

function buildMockPool() {
  return Array.from({ length: selectedQuestionSize.value }, (_, index) => buildMockQuestion(subject.value, examCode.value, index))
}

function shuffleArray(items) {
  const result = [...items]
  for (let index = result.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1))
    ;[result[index], result[swapIndex]] = [result[swapIndex], result[index]]
  }
  return result
}

function buildRandomQuestionPool(candidateGroups) {
  const groups = candidateGroups.map((group) => shuffleArray(group)).filter((group) => group.length)
  const selected = []
  const usedIds = new Set()

  while (selected.length < plannedQuestionLimit.value && groups.some((group) => group.length)) {
    for (const group of groups) {
      const item = group.shift()
      const key = item?.questionId || item?.id
      if (!item || usedIds.has(key)) {
        continue
      }
      selected.push(item)
      usedIds.add(key)
      if (selected.length >= plannedQuestionLimit.value) {
        break
      }
    }
  }

  return shuffleArray(selected)
}

function getSelectedModuleInfos() {
  return selectedTags.value
    .map((tag) => {
      const found = subjectTree.value.find((section) => section.submodules.includes(tag))
      if (!found) {
        return null
      }
      return {
        module: found.module,
        submodule: tag
      }
    })
    .filter(Boolean)
}

function getAllModuleInfos() {
  return subjectTree.value.flatMap((section) =>
    section.submodules.map((submodule) => ({
      module: section.module,
      submodule
    }))
  )
}

function getTargetModuleInfos() {
  return practiceMode.value === 'comprehensive' ? getAllModuleInfos() : getSelectedModuleInfos()
}

function getCacheKey(moduleInfos) {
  return JSON.stringify({
    mode: practiceMode.value,
    examCode: examCode.value,
    subject: subject.value,
    tags: moduleInfos.map((item) => `${item.module}:${item.submodule}`).sort(),
    seed: practiceMode.value === 'comprehensive' ? Date.now() : ''
  })
}

function goBack() {
  if (summaryMode.value || reviewMode.value || mode.value === 'quiz') {
    confirmExitPractice()
    return
  }

  uni.navigateBack({
    delta: 1,
    fail() {
      uni.redirectTo({ url: '/pages/subjects/index' })
    }
  })
}

function confirmExitPractice() {
  uni.showModal({
    title: '退出本次练习？',
    content: '退出后本轮未完成的题目不会继续保留，已提交的答案仍会保存。',
    confirmText: '退出',
    cancelText: '继续做题',
    success(result) {
      if (result.confirm) {
        resetToTags()
      }
    }
  })
}

function switchPracticeMode(value) {
  practiceMode.value = value
  selectedTags.value = []
  resetQuizState()
}

function toggleOpen(module) {
  openMap.value = {
    ...openMap.value,
    [module]: !openMap.value[module]
  }
}

function toggleTag(tag) {
  if (selectedTags.value.includes(tag)) {
    selectedTags.value = selectedTags.value.filter((item) => item !== tag)
    return
  }
  selectedTags.value = [...selectedTags.value, tag]
}

function getCount(tag) {
  return getTagCount(subject.value, tag)
}

async function fetchRealQuestionCandidates(moduleInfos) {
  if (practiceMode.value === 'comprehensive') {
    const query = new URLSearchParams({
      exam_code: examCode.value,
      subject: subject.value,
      limit: String(plannedQuestionLimit.value),
      randomize: 'true'
    }).toString()

    const data = await request({
      url: `/questions?${query}`,
      header: {
        Authorization: `Bearer ${accessToken.value}`
      }
    })

    const items = (data.items || []).map((item) =>
      buildApiQuestion(item, {
        module: item.module,
        submodule: item.submodule
      })
    )

    return items.length ? [items] : []
  }

  const perTagLimit =
    Math.min(50, Math.max(20, plannedQuestionLimit.value, Math.ceil(plannedQuestionLimit.value / moduleInfos.length) * 4))

  const responses = await Promise.allSettled(
    moduleInfos.map((meta) => {
      const query = new URLSearchParams({
        exam_code: examCode.value,
        subject: subject.value,
        module: meta.module,
        submodule: meta.submodule,
        limit: String(perTagLimit)
      }).toString()

      return request({
        url: `/questions/by-module?${query}`,
        header: {
          Authorization: `Bearer ${accessToken.value}`
        }
      }).then((data) => ({
        meta,
        items: data.items || []
      }))
    })
  )

  return responses
    .filter((response) => response.status === 'fulfilled')
    .map((response) => response.value.items.map((item) => buildApiQuestion(item, response.value.meta)))
    .filter((items) => items.length)
}

async function fetchSubjectSupplement(existingIds) {
  const query = new URLSearchParams({
    exam_code: examCode.value,
    subject: subject.value,
    limit: String(Math.min(50, plannedQuestionLimit.value * 3)),
    randomize: 'true'
  }).toString()

  const data = await request({
    url: `/questions?${query}`,
    header: {
      Authorization: `Bearer ${accessToken.value}`
    }
  })

  return (data.items || [])
    .filter((item) => !existingIds.has(item.id))
    .map((item) =>
      buildApiQuestion(item, {
        module: item.module,
        submodule: item.submodule
      })
    )
}

function applyQuestionAt(index) {
  currentQuestionIndex.value = index
  const nextQuestion = questionPool.value[index]
  questionMeta.value = {
    questionId: nextQuestion.questionId || nextQuestion.id,
    module: nextQuestion.module || '',
    submodule: nextQuestion.submodule || ''
  }
  correctAnswer.value = ''
  answerExplanation.value = ''
  resultTag.value = ''
  selectedOption.value = practiceMode.value === 'comprehensive' ? comprehensiveAnswers.value[nextQuestion.questionId || nextQuestion.id] || '' : ''
  submitted.value = false
  submitting.value = false
  abilityAccuracy.value = null
  timerSeconds.value = 0
  loadCurrentFavoriteStatus()
  startTimer()
  scrollToQuestionTop()
}

async function startQuiz() {
  syncAccessToken()
  loadError.value = ''
  shortageTip.value = ''

  if (!hasAccessToken.value) {
    uni.showModal({
      title: '请先登录',
      content: '登录后才能使用真实题库、保存作答记录、同步错题本和能力报告。',
      confirmText: '去登录',
      cancelText: '先不登录',
      success(result) {
        if (result.confirm) {
          uni.navigateTo({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/practice/index')}` })
        }
      }
    })
    return
  }

  if (practiceMode.value === 'special' && !selectedTags.value.length) {
    uni.showToast({ title: '请先选择至少一个考点', icon: 'none' })
    return
  }

  loading.value = true
  resetQuizState()
  reviewMode.value = false
  reviewResults.value = []
  summaryMode.value = false
  comprehensiveAnswers.value = {}
  uni.showLoading({ title: '正在加载题目...' })

  try {
    const moduleInfos = getTargetModuleInfos()
    const cacheKey = getCacheKey(moduleInfos)
    let candidateGroups = questionCache.get(cacheKey)
    let nextPool = []

    if (!candidateGroups) {
      if (hasAccessToken.value && moduleInfos.length) {
        candidateGroups = await fetchRealQuestionCandidates(moduleInfos)
      }

      if (candidateGroups?.length) {
        questionCache.set(cacheKey, candidateGroups)
      }
    }

    if (candidateGroups?.length) {
      nextPool = buildRandomQuestionPool(candidateGroups)
    }

    if (nextPool.length < plannedQuestionLimit.value) {
      const existingIds = new Set(nextPool.map((item) => item.questionId || item.id))
      const supplement = await fetchSubjectSupplement(existingIds)
      if (supplement.length) {
        nextPool = shuffleArray([...nextPool, ...supplement]).slice(0, plannedQuestionLimit.value)
        shortageTip.value = '当前题库较少，已为你随机补充同科目题目。'
      }
    }

    if (!nextPool.length) {
      throw new Error('当前题库暂无可用题目，请换一个科目或稍后再试')
    }

    questionPool.value = nextPool
    mode.value = 'quiz'
    applyQuestionAt(0)

    if (shortageTip.value) {
      uni.showToast({ title: shortageTip.value, icon: 'none' })
    } else if (questionPool.value.length < plannedQuestionLimit.value) {
      shortageTip.value = '当前题库较少，本轮先按可用题目练习。'
      uni.showToast({ title: shortageTip.value, icon: 'none' })
    }
  } catch (error) {
    const detail = error?.detail || error?.message || '加载题目失败'
    loadError.value = detail
    uni.showToast({ title: detail, icon: 'none' })
  } finally {
    loading.value = false
    uni.hideLoading()
  }
}

function selectOption(key) {
  if (submitted.value || submitting.value || reviewMode.value) {
    return
  }
  selectedOption.value = key
  if (practiceMode.value === 'comprehensive') {
    comprehensiveAnswers.value = {
      ...comprehensiveAnswers.value,
      [currentQuestionKey.value]: key
    }
  }
}

async function handlePrimaryAction() {
  if (practiceMode.value === 'comprehensive') {
    await handleComprehensiveAction()
    return
  }
  await submitAnswer()
}

async function handleComprehensiveAction() {
  if (!selectedOption.value) {
    return
  }

  comprehensiveAnswers.value = {
    ...comprehensiveAnswers.value,
    [currentQuestionKey.value]: selectedOption.value
  }

  if (hasNextQuestion.value) {
    applyQuestionAt(currentQuestionIndex.value + 1)
    return
  }

  await submitComprehensiveAnswers()
}

async function submitComprehensiveAnswers() {
  syncAccessToken()
  submitting.value = true
  await nextTick()
  scrollToResultSection()

  try {
    const results = await Promise.all(
      questionPool.value.map(async (question) => {
        const key = question.questionId || question.id
        const selected = comprehensiveAnswers.value[key]

        if (hasAccessToken.value && question.questionId && !String(question.questionId).startsWith('mock-')) {
          const result = await request({
            url: '/answers/submit',
            method: 'POST',
            header: {
              Authorization: `Bearer ${accessToken.value}`
            },
            data: {
              question_id: question.questionId,
              selected_answer: selected,
              used_time: timerSeconds.value,
              exam_code: examCode.value
            }
          })

          return {
            question,
            selectedAnswer: selected,
            correctAnswer: result.correct_answer,
            explanation: result.explanation,
            isCorrect: result.is_correct
          }
        }

        return {
          question,
          selectedAnswer: selected,
          correctAnswer: question.answer,
          explanation: question.explanation,
          isCorrect: selected === question.answer
        }
      })
    )

    reviewResults.value = results
    summaryMode.value = true
    reviewMode.value = false
    submitted.value = false
    submitting.value = false
    clearTimer()
    await nextTick()
    scrollToQuestionTop()
  } catch (error) {
    uni.showToast({ title: error?.detail || '提交整卷失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

async function submitAnswer() {
  syncAccessToken()
  if (!selectedOption.value) {
    return
  }

  submitting.value = true
  await nextTick()
  scrollToResultSection()
  try {
    if (hasAccessToken.value && isRealQuestion()) {
      const result = await request({
        url: '/answers/submit',
        method: 'POST',
        header: {
          Authorization: `Bearer ${accessToken.value}`
        },
        data: {
          question_id: questionMeta.value.questionId,
          selected_answer: selectedOption.value,
          used_time: timerSeconds.value,
          exam_code: examCode.value
        }
      })

      correctAnswer.value = result.correct_answer
      answerExplanation.value = result.explanation
      resultTag.value = result.added_to_wrong_questions
        ? `已写入错题本：${subject.value} / ${questionMeta.value.module} / ${questionMeta.value.submodule}`
        : '本题答对，当前知识点继续保持。'
      abilityAccuracy.value = result.ability_accuracy
    } else {
      correctAnswer.value = currentQuestion.value.answer
      answerExplanation.value = currentQuestion.value.explanation
      resultTag.value = currentQuestion.value.autoTag
      abilityAccuracy.value = null
    }

    submitted.value = true
    clearTimer()
    await nextTick()
    scrollToResultSection()
  } catch (error) {
    uni.showToast({ title: error?.detail || '提交失败', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

function applyReviewAt(index) {
  currentQuestionIndex.value = index
  const result = reviewResults.value[index]
  const question = result.question
  questionMeta.value = {
    questionId: question.questionId || question.id,
    module: question.module || '',
    submodule: question.submodule || ''
  }
  selectedOption.value = result.selectedAnswer
  correctAnswer.value = result.correctAnswer
  answerExplanation.value = result.explanation
  resultTag.value = result.isCorrect ? '本题答对。' : '本题答错，已纳入错题统计。'
  submitted.value = true
  abilityAccuracy.value = null
  loadCurrentFavoriteStatus()
}

function openReviewQuestion(index) {
  summaryMode.value = false
  reviewMode.value = true
  applyReviewAt(index)
  nextTick(() => {
    scrollToQuestionTop()
  })
}

function isRealQuestion() {
  return canFavoriteCurrent.value
}

async function loadCurrentFavoriteStatus() {
  syncAccessToken()
  const questionId = questionMeta.value.questionId
  favoriteQuestionId.value = questionId
  currentFavorited.value = false

  if (!hasAccessToken.value || !isRealQuestion()) {
    return
  }

  favoriteLoading.value = true
  try {
    const result = await fetchFavoriteStatus(questionId)
    if (favoriteQuestionId.value === questionId) {
      currentFavorited.value = Boolean(result.is_favorited)
    }
  } catch (error) {
    if (favoriteQuestionId.value === questionId) {
      currentFavorited.value = false
    }
  } finally {
    if (favoriteQuestionId.value === questionId) {
      favoriteLoading.value = false
    }
  }
}

async function toggleCurrentFavorite() {
  syncAccessToken()

  if (!hasAccessToken.value) {
    uni.showToast({ title: '登录后才能收藏题目', icon: 'none' })
    return
  }

  if (!isRealQuestion() || favoriteLoading.value) {
    return
  }

  const questionId = questionMeta.value.questionId
  favoriteLoading.value = true
  try {
    const result = await toggleFavorite(questionId)
    currentFavorited.value = Boolean(result.is_favorited)
    uni.showToast({ title: result.is_favorited ? '已收藏' : '已取消收藏', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '收藏状态更新失败', icon: 'none' })
  } finally {
    favoriteLoading.value = false
  }
}

function goPrevQuestion() {
  if (!reviewMode.value || !hasPrevQuestion.value) {
    return
  }
  applyReviewAt(currentQuestionIndex.value - 1)
  scrollToQuestionTop()
}

function goNextQuestion() {
  if (!hasNextQuestion.value) {
    return
  }

  if (reviewMode.value) {
    applyReviewAt(currentQuestionIndex.value + 1)
    scrollToQuestionTop()
    return
  }

  applyQuestionAt(currentQuestionIndex.value + 1)
}

function showSummary() {
  summaryMode.value = true
  reviewMode.value = false
  submitted.value = false
  nextTick(() => {
    scrollToQuestionTop()
  })
}

function finishQuiz() {
  uni.showToast({ title: '本轮完成，已返回刷题范围', icon: 'none' })
  resetToTags()
}

function resetQuizState() {
  selectedOption.value = ''
  submitted.value = false
  submitting.value = false
  timerSeconds.value = 0
  abilityAccuracy.value = null
  correctAnswer.value = ''
  answerExplanation.value = ''
  resultTag.value = ''
  clearTimer()
}

function resetToTags() {
  mode.value = 'tags'
  questionPool.value = buildMockPool()
  currentQuestionIndex.value = 0
  questionMeta.value = {
    questionId: '',
    module: '',
    submodule: ''
  }
  comprehensiveAnswers.value = {}
  reviewMode.value = false
  reviewResults.value = []
  summaryMode.value = false
  resetQuizState()
}

function startTimer() {
  clearTimer()
  timerId = setInterval(() => {
    timerSeconds.value += 1
  }, 1000)
}

function clearTimer() {
  if (timerId) {
    clearInterval(timerId)
    timerId = null
  }
}

function scrollToQuestionTop() {
  setTimeout(() => {
    uni.pageScrollTo({
      scrollTop: 0,
      duration: 220
    })
  }, 30)
}

function scrollToResultSection() {
  setTimeout(() => {
    uni.pageScrollTo({
      selector: '#result-anchor',
      duration: 260
    })
  }, 30)
}
</script>

<style scoped>
.practice-page {
  min-height: 100vh;
  min-height: 100dvh;
  padding: calc(var(--status-bar-height) + 16rpx) 28rpx calc(env(safe-area-inset-bottom) + 188rpx);
  background:
    radial-gradient(circle at top right, rgba(22, 119, 255, 0.08), transparent 28%),
    linear-gradient(180deg, #f8fbff 0%, #f2f6fc 100%);
}

.top-nav {
  display: flex;
  align-items: center;
  gap: 18rpx;
  margin-bottom: 22rpx;
}

.back-btn {
  width: 76rpx;
  height: 76rpx;
  padding: 0;
  border: 0;
  border-radius: 26rpx;
  background: #ffffff;
  color: #172033;
  font-size: 42rpx;
  font-weight: 700;
  line-height: 76rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.08);
}

.top-copy {
  flex: 1;
}

.top-title {
  color: #172033;
  font-size: 38rpx;
  font-weight: 900;
}

.top-sub {
  margin-top: 6rpx;
  color: #667085;
  font-size: 24rpx;
}

.setup-hero {
  margin-bottom: 22rpx;
  padding: 34rpx 30rpx;
  border-radius: 36rpx;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(238, 244, 255, 0.96)),
    radial-gradient(circle at 0 0, rgba(37, 99, 235, 0.14), transparent 46%);
  border: 2rpx solid rgba(219, 228, 245, 0.92);
  box-shadow: 0 20rpx 46rpx rgba(20, 31, 66, 0.08);
}

.setup-eyebrow {
  color: #2563eb;
  font-size: 23rpx;
  font-weight: 900;
}

.setup-title {
  margin-top: 8rpx;
  color: #101828;
  font-size: 44rpx;
  line-height: 1.22;
  font-weight: 900;
}

.setup-sub {
  margin-top: 14rpx;
  color: #667085;
  font-size: 25rpx;
  line-height: 1.65;
}

.mode-card,
.count-card,
.comprehensive-card {
  margin-bottom: 24rpx;
  padding: 26rpx;
  border-radius: 34rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 16rpx 36rpx rgba(20, 31, 66, 0.06);
}

.mode-card {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.mode-option {
  min-height: 138rpx;
  padding: 26rpx 22rpx;
  border-radius: 28rpx;
  border: 2rpx solid #dbe4f5;
  background: #f8fbff;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.mode-option.active {
  border-color: #2563eb;
  background: linear-gradient(180deg, #f4f8ff 0%, #edf3ff 100%);
  box-shadow: 0 10rpx 22rpx rgba(37, 99, 235, 0.12);
}

.mode-title,
.count-title,
.comprehensive-title {
  color: #172033;
  font-size: 30rpx;
  font-weight: 900;
}

.mode-sub,
.count-sub,
.comprehensive-line {
  margin-top: 8rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.6;
}

.state-box {
  margin-bottom: 20rpx;
  padding: 20rpx 22rpx;
  border-radius: 22rpx;
  background: #f4f8ff;
  border: 2rpx dashed #c8d8ff;
  color: #36527f;
  font-size: 24rpx;
  line-height: 1.6;
}

.state-box.warning {
  background: #fff8eb;
  border-color: #fde7b0;
  color: #9a6510;
}

.count-options {
  display: flex;
  gap: 16rpx;
  margin-top: 24rpx;
}

.count-option {
  flex: 1;
  min-height: 100rpx;
  border-radius: 28rpx;
  border: 2rpx solid #dbe4f5;
  background: #f8fbff;
  color: #476089;
  font-size: 30rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}

.count-option.active {
  border-color: #2563eb;
  background: #edf3ff;
  color: #2563eb;
  box-shadow: 0 8rpx 18rpx rgba(37, 99, 235, 0.12);
}

.sticky-bar {
  position: fixed;
  left: 28rpx;
  right: 28rpx;
  bottom: calc(env(safe-area-inset-bottom) + 22rpx);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 22rpx 24rpx;
  border-radius: 36rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 18rpx 44rpx rgba(20, 31, 66, 0.12);
  backdrop-filter: blur(16rpx);
}

.sticky-copy {
  min-width: 0;
  flex: 1;
}

.sticky-title {
  font-size: 28rpx;
  font-weight: 900;
  color: #172033;
}

.sticky-sub,
.sticky-tip {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.35;
}

.sticky-tip {
  color: #2563eb;
}

.sticky-btn {
  min-width: 196rpx;
  min-height: 92rpx;
  padding: 0 24rpx;
  border: 0;
  border-radius: 28rpx;
  background: #2563eb;
  color: #ffffff;
  font-size: 26rpx;
  font-weight: 900;
  box-shadow: 0 14rpx 28rpx rgba(37, 99, 235, 0.2);
}

.sticky-btn[disabled] {
  background: #c6d3f2;
}

.quiz-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.quiz-shell {
  padding: 24rpx 22rpx 22rpx;
  border-radius: 36rpx;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.86), rgba(245, 248, 255, 0.94)),
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.08), transparent 42%);
  border: 2rpx solid rgba(230, 235, 245, 0.9);
  box-shadow: 0 16rpx 36rpx rgba(20, 31, 66, 0.06);
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  background: #edf3ff;
  color: #2563eb;
  font-size: 23rpx;
  font-weight: 900;
}

.badge.plain {
  margin-bottom: 0;
}

.question-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 18rpx;
}

.favorite-btn {
  width: 64rpx;
  height: 64rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 22rpx;
  background: #f3f6fb;
  color: #98a2b3;
  font-size: 34rpx;
  font-weight: 900;
  line-height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.favorite-btn.active {
  background: #fff7e8;
  color: #f59e0b;
}

.favorite-btn[disabled] {
  opacity: 0.55;
}

.timer {
  padding: 14rpx 18rpx;
  border-radius: 20rpx;
  background: #fff8eb;
  color: #b7791f;
  border: 2rpx solid #fde7b0;
  font-size: 23rpx;
  font-weight: 900;
}

.question-card {
  padding: 30rpx 8rpx 6rpx;
  border-radius: 0;
  background: #ffffff;
  border: 0;
  box-shadow: none;
  background: transparent;
}

.question-title {
  color: #172033;
  font-size: 38rpx;
  line-height: 1.55;
  font-weight: 900;
}

.helper-box {
  margin-top: 22rpx;
  padding: 22rpx;
  border-radius: 24rpx;
  border: 2rpx dashed #c8d3ea;
  background: #f8fbff;
  color: #476089;
  font-size: 24rpx;
  line-height: 1.6;
  text-align: center;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  margin: 24rpx 0;
}

.submit-btn {
  width: 100%;
  min-height: 104rpx;
  border: 0;
  border-radius: 28rpx;
  background: #2563eb;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 900;
  box-shadow: 0 14rpx 28rpx rgba(37, 99, 235, 0.2);
}

.submit-btn[disabled] {
  background: #c6d3f2;
  box-shadow: none;
}

.summary-card {
  padding: 36rpx 32rpx;
  border-radius: 36rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.05);
}

.summary-kicker {
  color: #2563eb;
  font-size: 24rpx;
  font-weight: 800;
}

.summary-score {
  margin-top: 12rpx;
  color: #172033;
  font-size: 64rpx;
  font-weight: 900;
}

.summary-sub {
  margin-top: 10rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.6;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 22rpx;
  padding: 24rpx;
  border-radius: 32rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
}

.summary-dot {
  min-height: 78rpx;
  border: 0;
  border-radius: 22rpx;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-dot.correct {
  background: #16a34a;
}

.summary-dot.wrong {
  background: #ef4444;
}

.summary-actions {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 20rpx;
}

.result-note {
  margin-top: 18rpx;
  color: #2563eb;
  font-size: 24rpx;
  font-weight: 700;
  text-align: center;
}

.action-row {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 18rpx;
}

.review-nav-row {
  display: flex;
  gap: 16rpx;
}

.next-btn {
  flex: 1;
  width: 100%;
  min-height: 102rpx;
  border: 0;
  border-radius: 28rpx;
  background: #172033;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
}

.next-btn.done {
  background: #0f8b5f;
}

.next-btn.secondary {
  background: #475569;
}

.next-btn.outline {
  background: #ffffff;
  color: #2563eb;
  border: 2rpx solid #bfd0f7;
  box-shadow: none;
}

.next-btn[disabled] {
  background: #c6d3f2;
  color: #ffffff;
  box-shadow: none;
}

.back-tags {
  margin-top: 20rpx;
}
</style>
