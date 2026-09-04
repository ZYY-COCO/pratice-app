import assert from 'node:assert/strict'
import fs from 'node:fs'

const utilityPath = new URL('../src/utils/adaptiveComprehensivePractice.js', import.meta.url)
const submissionQueuePath = new URL('../src/utils/adaptiveComprehensiveSubmissionQueue.js', import.meta.url)
const practicePath = new URL('../src/pages/practice/index.vue', import.meta.url)
const apiPath = new URL('../src/api/adaptivePractice.js', import.meta.url)

const utilitySource = fs.readFileSync(utilityPath, 'utf8')
const utility = await import(
  `data:text/javascript;base64,${Buffer.from(utilitySource).toString('base64')}`
)
const submissionQueueSource = fs.readFileSync(submissionQueuePath, 'utf8')
const submissionQueueUtility = await import(
  `data:text/javascript;base64,${Buffer.from(submissionQueueSource).toString('base64')}`
)

function extractNamedFunction(source, name) {
  const regularStart = source.indexOf(`function ${name}`)
  const asyncStart = source.indexOf(`async function ${name}`)
  const starts = [regularStart, asyncStart].filter((value) => value >= 0)
  assert.ok(starts.length, `missing function: ${name}`)
  const start = Math.min(...starts)
  const bodyStart = source.indexOf('{', start)
  let depth = 0
  for (let index = bodyStart; index < source.length; index += 1) {
    if (source[index] === '{') depth += 1
    if (source[index] === '}') depth -= 1
    if (depth === 0) return source.slice(start, index + 1)
  }
  assert.fail(`unterminated function: ${name}`)
}

function item(position, overrides = {}) {
  return {
    id: `item-${position}`,
    session_id: 'session-fixed',
    position,
    question: {
      id: `question-${position}`,
      stem: `Question ${position}`,
      option_a: 'A',
      option_b: 'B',
      option_c: 'C',
      option_d: 'D'
    },
    ...overrides
  }
}

const normalized = utility.normalizeAdaptiveComprehensiveItems(
  [item(2), item(1)],
  { sessionId: 'session-fixed', expectedCount: 2 }
)
assert.deepEqual(normalized.map((value) => value.position), [1, 2])

assert.throws(
  () => utility.normalizeAdaptiveComprehensiveItems(
    [item(1), item(2, { session_id: 'other-session' })],
    { sessionId: 'session-fixed', expectedCount: 2 }
  ),
  /current session|\u5f53\u524d\u4f1a\u8bdd|\u4f1a\u8bdd不一致/i
)
assert.throws(
  () => utility.normalizeAdaptiveComprehensiveItems(
    [item(1), item(2, { question: { ...item(1).question } })],
    { sessionId: 'session-fixed', expectedCount: 2 }
  ),
  /重复题目/
)
assert.throws(
  () => utility.normalizeAdaptiveComprehensiveItems(
    [item(1)],
    { sessionId: 'session-fixed', expectedCount: 2 }
  ),
  /数量异常/
)

const questions = normalized.map((value) => ({
  questionId: value.question.id,
  adaptiveSessionId: value.session_id,
  adaptiveSessionItemId: value.id
}))
const payload = utility.buildAdaptiveComprehensiveSubmissionPayload({
  sessionId: 'session-fixed',
  clientSubmissionId: 'batch-fixed',
  questions,
  answersByQuestion: {
    'question-1': 'A'
  },
  getQuestionSubmissionId: (questionId) => `submission-${questionId}`,
  getUsedTime: (questionId) => questionId === 'question-1' ? 12 : 7
})
assert.deepEqual(payload, {
  client_submission_id: 'batch-fixed',
  answers: [
    {
      practice_session_item_id: 'item-1',
      selected_answer: 'A',
      used_time: 12,
      client_submission_id: 'submission-question-1'
    },
    {
      practice_session_item_id: 'item-2',
      selected_answer: null,
      used_time: 7,
      client_submission_id: 'submission-question-2'
    }
  ]
})
const boundedUsedTimePayload = utility.buildAdaptiveComprehensiveSubmissionPayload({
  sessionId: 'session-fixed',
  clientSubmissionId: 'batch-bounded-time',
  questions,
  answersByQuestion: {},
  getQuestionSubmissionId: (questionId) => `bounded-${questionId}`,
  getUsedTime: (questionId) => questionId === 'question-1' ? 90000.7 : -3.2
})
assert.deepEqual(
  boundedUsedTimePayload.answers.map((answer) => answer.used_time),
  [86400, 0],
  'used_time 必须取整并限制在 0..86400'
)

const entries = [
  { question: questions[0], selected: 'A' },
  { question: questions[1], selected: undefined }
]
const results = utility.mapAdaptiveComprehensiveResults(entries, [
  {
    practice_session_item_id: 'item-2',
    question_id: 'question-2',
    position: 2,
    selected_answer: null,
    correct_answer: 'C',
    is_correct: null,
    explanation: 'Skipped explanation'
  },
  {
    practice_session_item_id: 'item-1',
    question_id: 'question-1',
    position: 1,
    selected_answer: 'A',
    correct_answer: 'A',
    is_correct: true,
    explanation: 'Correct explanation'
  }
])
assert.deepEqual(results.map((value) => value.question.questionId), ['question-1', 'question-2'])
assert.equal(results[0].isCorrect, true)
assert.equal(results[1].skipped, true)

assert.deepEqual(
  utility.summarizeAdaptiveReviewResults([
    { isCorrect: true, skipped: false },
    { isCorrect: false, skipped: false },
    { isCorrect: null, skipped: true }
  ]),
  { answeredCount: 2, correctCount: 1, accuracy: 50 },
  '异常题跳过结果不得进入成绩或正确率分母'
)
assert.equal(
  utility.isAdaptiveWarmupSession({
    active: true,
    questionCount: 8,
    diagnosticStatus: 'CALIBRATING',
    reliableFirstAttemptCount: 4
  }),
  true,
  '已有 4–7 条证据但仍由服务端强制为 8 题时必须继续显示智能热身'
)
assert.equal(
  utility.isAdaptiveWarmupSession({
    active: true,
    questionCount: 8,
    diagnosticStatus: 'STABLE',
    reliableFirstAttemptCount: 20
  }),
  false
)

function cloneStored(value) {
  if (value === undefined) return undefined
  return JSON.parse(JSON.stringify(value))
}

function createMemoryStorage() {
  const values = new Map()
  return {
    failSet: false,
    getStorageSync(key) {
      return cloneStored(values.get(key))
    },
    setStorageSync(key, value) {
      if (this.failSet) throw new Error('quota exceeded')
      values.set(key, cloneStored(value))
    },
    removeStorageSync(key) {
      values.delete(key)
    },
    raw(key) {
      return cloneStored(values.get(key))
    }
  }
}

function storedPayload(sessionId, suffix = 'fixed') {
  return {
    client_submission_id: `batch-${suffix}`,
    answers: [
      {
        practice_session_item_id: `item-${sessionId}`,
        selected_answer: 'A',
        used_time: 12,
        client_submission_id: `answer-${suffix}`
      }
    ]
  }
}

function completedResponse(sessionId, payload) {
  const results = payload.answers.map((answer, index) => ({
    practice_session_item_id: answer.practice_session_item_id,
    question_id: `question-${index + 1}`,
    position: index + 1,
    selected_answer: answer.selected_answer,
    correct_answer: 'A',
    is_correct: answer.selected_answer === null ? null : answer.selected_answer === 'A',
    explanation: `explanation-${index + 1}`
  }))
  const answeredCount = results.filter((result) => result.selected_answer !== null).length
  const correctCount = results.filter((result) => result.is_correct === true).length
  return {
    session_id: sessionId,
    status: 'completed',
    reason: 'completed',
    idempotent: false,
    adaptive_settled: true,
    results,
    summary: {
      total_count: results.length,
      answered_count: answeredCount,
      correct_count: correctCount,
      wrong_count: answeredCount - correctCount,
      skipped_count: results.length - answeredCount,
      accuracy: answeredCount ? Math.round((correctCount / answeredCount) * 10000) / 100 : 0,
      used_time: payload.answers.reduce((total, answer) => total + answer.used_time, 0)
    },
    state: {
      theta: 0.2,
      uncertainty: 0.8,
      effective_evidence: 8,
      reliable_first_attempt_count: 8,
      diagnostic_status: 'STABLE',
      pending_conflicts: 0,
      confidence_label: '中等',
      initial_level_range: 'D2–D3'
    }
  }
}

const failedStorage = createMemoryStorage()
let failedStorageSubmitCalls = 0
const failedStorageQueue = submissionQueueUtility.createAdaptiveComprehensiveSubmissionQueue({
  storage: failedStorage,
  getOwnerId: () => 'user-a',
  submit: async (sessionId, payload) => {
    failedStorageSubmitCalls += 1
    return completedResponse(sessionId, payload)
  }
})
failedStorage.failSet = true
assert.throws(
  () => failedStorageQueue.persist({ sessionId: 'session-a', payload: storedPayload('a') }),
  (error) => error?.code === 'ADAPTIVE_COMPREHENSIVE_LOCAL_PERSISTENCE_FAILED' && error?.retryable === true,
  '本地持久化失败必须在服务端锁定 manifest 前中止'
)
assert.equal(failedStorageSubmitCalls, 0)

const crossUserStorage = createMemoryStorage()
let activeOwnerId = 'user-a'
let crossUserSubmitCalls = 0
const crossUserQueue = submissionQueueUtility.createAdaptiveComprehensiveSubmissionQueue({
  storage: crossUserStorage,
  getOwnerId: () => activeOwnerId,
  submit: async (sessionId, payload) => {
    crossUserSubmitCalls += 1
    return completedResponse(sessionId, payload)
  }
})
const userATask = crossUserQueue.persist({
  sessionId: 'session-a',
  payload: storedPayload('a')
})
const userAStorageKey = submissionQueueUtility.getAdaptiveComprehensiveSubmissionStorageKey('user-a')
assert.equal(crossUserStorage.raw(userAStorageKey)?.tasks?.length, 1)
activeOwnerId = 'user-b'
assert.deepEqual(crossUserQueue.list(), [])
assert.equal(crossUserQueue.remove(userATask), false)
await crossUserQueue.resumeAll()
assert.equal(crossUserSubmitCalls, 0, '新账号不得续交旧账号整卷')
assert.equal(
  crossUserStorage.raw(userAStorageKey)?.tasks?.length,
  1,
  '新账号不得清除原 owner 的待续交任务'
)
activeOwnerId = 'user-a'
await crossUserQueue.resumeAll()
assert.equal(crossUserSubmitCalls, 1)
assert.equal(crossUserStorage.raw(userAStorageKey), undefined)

const accountSwitchStorage = createMemoryStorage()
let requestOwnerId = 'user-a'
let finishAccountSwitchRequest
const accountSwitchQueue = submissionQueueUtility.createAdaptiveComprehensiveSubmissionQueue({
  storage: accountSwitchStorage,
  getOwnerId: () => requestOwnerId,
  submit: (sessionId, payload) => new Promise((resolve) => {
    finishAccountSwitchRequest = () => resolve(completedResponse(sessionId, payload))
  })
})
accountSwitchQueue.persist({ sessionId: 'session-switch', payload: storedPayload('switch') })
const switchingResume = accountSwitchQueue.resumeAll()
await Promise.resolve()
await Promise.resolve()
requestOwnerId = 'user-b'
finishAccountSwitchRequest()
await switchingResume
assert.equal(
  accountSwitchStorage.raw(
    submissionQueueUtility.getAdaptiveComprehensiveSubmissionStorageKey('user-a')
  )?.tasks?.length,
  1,
  '请求期间切换账号时必须保留原 owner 任务'
)

const retainedStorage = createMemoryStorage()
let retainedMode = 'pending'
let retainedCalls = 0
const retainedQueue = submissionQueueUtility.createAdaptiveComprehensiveSubmissionQueue({
  storage: retainedStorage,
  getOwnerId: () => 'user-a',
  submit: async (sessionId) => {
    retainedCalls += 1
    if (retainedMode === 'pending') {
      throw {
        statusCode: 409,
        detail: { code: 'ADAPTIVE_COMPREHENSIVE_SUBMISSION_PENDING' }
      }
    }
    if (retainedMode === 'network') {
      throw { code: 'NETWORK_TIMEOUT', retryable: true }
    }
    if (retainedMode === 'terminal') {
      throw {
        statusCode: 409,
        detail: { code: 'ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT' }
      }
    }
    return completedResponse(sessionId, storedPayload('pending'))
  }
})
retainedQueue.persist({ sessionId: 'session-pending', payload: storedPayload('pending') })
let resumeOutcome = await retainedQueue.resumeAll()
assert.equal(resumeOutcome[0]?.status, 'retained')
assert.equal(retainedQueue.list().length, 1, '409 pending 必须保留原任务')
retainedMode = 'network'
resumeOutcome = await retainedQueue.resumeAll()
assert.equal(resumeOutcome[0]?.status, 'retained')
assert.equal(retainedQueue.list().length, 1, '网络错误必须保留原任务')
retainedMode = 'terminal'
resumeOutcome = await retainedQueue.resumeAll()
assert.equal(resumeOutcome[0]?.status, 'terminal')
assert.equal(retainedQueue.list().length, 0, '明确终态冲突应只清除对应任务')
assert.equal(retainedCalls, 3)

const malformedCompletedStorage = createMemoryStorage()
const malformedCompletedQueue = submissionQueueUtility.createAdaptiveComprehensiveSubmissionQueue({
  storage: malformedCompletedStorage,
  getOwnerId: () => 'user-a',
  submit: async (sessionId, payload) => ({
    ...completedResponse(sessionId, payload),
    results: []
  })
})
malformedCompletedQueue.persist({
  sessionId: 'session-malformed-completed',
  payload: storedPayload('malformed-completed')
})
resumeOutcome = await malformedCompletedQueue.resumeAll()
assert.equal(resumeOutcome[0]?.status, 'retained')
assert.equal(
  malformedCompletedQueue.list().length,
  1,
  'completed 响应的 results 不全时必须保留续交任务'
)

const missingStateStorage = createMemoryStorage()
const missingStateQueue = submissionQueueUtility.createAdaptiveComprehensiveSubmissionQueue({
  storage: missingStateStorage,
  getOwnerId: () => 'user-a',
  submit: async (sessionId, payload) => ({
    ...completedResponse(sessionId, payload),
    state: null
  })
})
missingStateQueue.persist({
  sessionId: 'session-missing-state',
  payload: storedPayload('missing-state')
})
resumeOutcome = await missingStateQueue.resumeAll()
assert.equal(resumeOutcome[0]?.status, 'retained')
assert.equal(missingStateQueue.list().length, 1, 'completed 响应缺少 state 时必须保留任务')

const concurrentStorage = createMemoryStorage()
let completeConcurrentRequest
let concurrentSubmitCalls = 0
const concurrentQueue = submissionQueueUtility.createAdaptiveComprehensiveSubmissionQueue({
  storage: concurrentStorage,
  getOwnerId: () => 'user-a',
  submit: (sessionId, payload) => {
    concurrentSubmitCalls += 1
    return new Promise((resolve) => {
      completeConcurrentRequest = () => resolve(completedResponse(sessionId, payload))
    })
  }
})
const concurrentTask = concurrentQueue.persist({
  sessionId: 'session-concurrent',
  payload: storedPayload('concurrent')
})
const firstResume = concurrentQueue.resumeAll()
const secondResume = concurrentQueue.resumeAll()
assert.strictEqual(firstResume, secondResume, 'onLoad/onShow 并发恢复必须合并')
await Promise.resolve()
await Promise.resolve()
assert.equal(concurrentSubmitCalls, 1)
const joinedForegroundSubmit = concurrentQueue.submit(concurrentTask)
assert.equal(concurrentSubmitCalls, 1, '前台交卷必须复用正在恢复的同一请求')
completeConcurrentRequest()
await Promise.all([firstResume, secondResume, joinedForegroundSubmit])
assert.equal(concurrentQueue.list().length, 0, '确认 completed 后应清除精确任务')

const immutableStorage = createMemoryStorage()
const immutableQueue = submissionQueueUtility.createAdaptiveComprehensiveSubmissionQueue({
  storage: immutableStorage,
  getOwnerId: () => 'user-a',
  submit: async () => ({ status: 'completed' })
})
const originalTask = immutableQueue.persist({
  sessionId: 'session-fixed',
  payload: storedPayload('fixed')
})
const attemptedReplacement = immutableQueue.persist({
  sessionId: 'session-fixed',
  payload: storedPayload('replacement')
})
assert.deepEqual(
  attemptedReplacement.payload,
  originalTask.payload,
  '同一会话只能复用首份持久化交卷清单'
)
assert.equal(
  submissionQueueUtility.isAdaptiveComprehensiveTerminalSubmissionError({
    statusCode: 409,
    detail: { code: 'ADAPTIVE_COMPREHENSIVE_SUBMISSION_PENDING' }
  }),
  false
)
assert.equal(
  submissionQueueUtility.isAdaptiveComprehensiveTerminalSubmissionError({
    statusCode: 409,
    detail: { code: 'ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT' }
  }),
  true
)
for (const statusCode of [400, 410, 422]) {
  assert.equal(
    submissionQueueUtility.isAdaptiveComprehensiveTerminalSubmissionError({
      statusCode,
      detail: 'generic client response'
    }),
    false,
    `普通 ${statusCode} 不得被当作明确终态`
  )
}
assert.equal(
  submissionQueueUtility.isAdaptiveComprehensiveTerminalSubmissionError({
    statusCode: 404,
    detail: 'Not Found'
  }),
  false,
  '普通路由 404 可能来自滚动部署，不得误删续交任务'
)
assert.equal(
  submissionQueueUtility.isAdaptiveComprehensiveTerminalSubmissionError({
    statusCode: 404,
    detail: '个性化练习会话不存在'
  }),
  true
)

const practiceSource = fs.readFileSync(practicePath, 'utf8')
assert.match(practiceSource, /practice_mode:\s*startContext\.practiceMode/)
assert.match(practiceSource, /scopes:\s*isComprehensive\s*\?\s*\[\]/)
assert.match(practiceSource, /nextPool\s*=\s*buildAdaptiveComprehensiveQuestionPool\(response, startContext\)/)
assert.match(practiceSource, /questionPool\.value\s*=\s*nextPool/)
assert.match(
  practiceSource,
  /createAdaptiveComprehensiveSubmissionQueue\(\{[\s\S]*?submit:\s*submitAdaptiveComprehensivePracticeSession/,
  '待续交队列必须使用综合整卷提交接口'
)
assert.ok(
  (practiceSource.match(/resumePendingAdaptiveComprehensiveSubmissions\(\)/g) || []).length >= 3,
  'onLoad 和 onShow 都必须触发待续交恢复'
)
assert.match(practiceSource, /adaptiveComprehensiveSubmissionSnapshot\.payload/)
assert.match(practiceSource, /practiceMode\.value === 'comprehensive'[\s\S]*?submitComprehensiveAnswers\(\)/)
assert.match(
  practiceSource,
  /delete nextAnswers\[currentQuestionKey\.value\][\s\S]*?comprehensiveSkippedQuestions\.value\s*=\s*\{/
)
assert.match(
  practiceSource,
  /const gradableEntries = entries\.filter\(\(item\) => !item\.skipped && item\.selected\)/,
  '旧综合交卷链路不得提交已跳过的异常题'
)
assert.match(
  practiceSource,
  /summarizeAdaptiveReviewResults\(reviewResults\.value\)/,
  '异常题跳过结果不得进入成绩分母'
)
assert.match(
  practiceSource,
  /reliableFirstAttemptCount:\s*adaptiveInitialReliableCount\.value/,
  '八题热身标签必须读取创建会话时冻结的可靠证据量'
)

const pendingClassifierStart = practiceSource.indexOf(
  'function isAdaptiveComprehensiveSubmissionPendingError'
)
const pendingClassifierEnd = practiceSource.indexOf(
  'function isAdaptiveNextFallbackError',
  pendingClassifierStart
)
assert.ok(
  pendingClassifierStart >= 0 && pendingClassifierEnd > pendingClassifierStart,
  '综合交卷 pending 必须有独立错误分类器'
)
const pendingClassifierSource = practiceSource.slice(pendingClassifierStart, pendingClassifierEnd)
assert.match(
  pendingClassifierSource,
  /statusCode\s*===\s*409\s*&&\s*detailCode\s*===\s*['"]ADAPTIVE_COMPREHENSIVE_SUBMISSION_PENDING['"]/,
  'HTTP 409 detail.code=ADAPTIVE_COMPREHENSIVE_SUBMISSION_PENDING 必须判定为综合交卷 pending'
)

const retryableClassifierStart = practiceSource.indexOf('function isAdaptiveSubmissionRetryableError')
const retryableClassifierEnd = practiceSource.indexOf(
  'function rememberAdaptiveAnswerSubmission',
  retryableClassifierStart
)
const retryableClassifierSource = practiceSource.slice(
  retryableClassifierStart,
  retryableClassifierEnd
)
assert.match(
  retryableClassifierSource,
  /isAdaptiveComprehensiveSubmissionPendingError\(error\)/,
  '综合交卷 pending 必须进入可重试错误分支'
)

const retryableClassifier = new Function(`
  ${extractNamedFunction(practiceSource, 'adaptiveErrorText')}
  ${extractNamedFunction(practiceSource, 'isAdaptiveUpdatePendingError')}
  ${extractNamedFunction(practiceSource, 'isAdaptiveComprehensiveSubmissionPendingError')}
  ${extractNamedFunction(practiceSource, 'isAdaptiveSubmissionRetryableError')}
  return isAdaptiveSubmissionRetryableError
`)()
const comprehensivePendingError = {
  statusCode: 409,
  retryable: false,
  detail: {
    code: 'ADAPTIVE_COMPREHENSIVE_SUBMISSION_PENDING',
    message: '综合交卷仍在处理'
  }
}
assert.equal(
  retryableClassifier(comprehensivePendingError),
  true,
  'HTTP 409 综合交卷 pending 必须在运行时被识别为可重试'
)
assert.equal(
  retryableClassifier({
    statusCode: 409,
    retryable: false,
    detail: { code: 'ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT' }
  }),
  false,
  '其他 409 冲突不得被宽泛误判为可重试'
)

const comprehensiveSubmitStart = practiceSource.indexOf('async function submitAdaptiveComprehensiveAnswers')
const comprehensiveSubmitEnd = practiceSource.indexOf('async function submitComprehensiveAnswers', comprehensiveSubmitStart)
const comprehensiveSubmitSource = practiceSource.slice(comprehensiveSubmitStart, comprehensiveSubmitEnd)
assert.doesNotMatch(
  comprehensiveSubmitSource,
  /fetchNextAdaptivePracticeItem/,
  '综合刷题交卷链路不应请求逐题 next'
)
assert.match(
  comprehensiveSubmitSource,
  /const task\s*=\s*getAdaptiveComprehensiveSubmissionTask\(\)/,
  '综合交卷请求前必须先取得已持久化的任务'
)
assert.equal(
  comprehensiveSubmitSource.match(
    /adaptiveComprehensiveSubmissionQueue\.submit\(task\)/g
  )?.length,
  2,
  '首次综合交卷与即时重试必须使用同一持久化 task'
)
assert.match(
  comprehensiveSubmitSource,
  /if \(!isAdaptiveSubmissionRetryableError\(error\)\) \{\s*releaseTerminalAdaptiveComprehensiveSubmission\(error, task\)\s*throw error\s*\}/,
  '只有明确终态错误才可释放持久化任务'
)
const resultMappingIndex = comprehensiveSubmitSource.indexOf(
  'mapAdaptiveComprehensiveResults(entries, response?.results)'
)
const durableRemovalIndex = comprehensiveSubmitSource.indexOf(
  'removeAdaptiveComprehensiveSubmissionTask(task)'
)
assert.ok(
  resultMappingIndex >= 0 && durableRemovalIndex > resultMappingIndex,
  '必须在 completed 响应的完整结果映射成功后才清理续交凭据'
)

const comprehensiveOuterSubmitStart = comprehensiveSubmitEnd
const comprehensiveOuterSubmitEnd = practiceSource.indexOf(
  'function isRealSubmitQuestion',
  comprehensiveOuterSubmitStart
)
const comprehensiveOuterSubmitSource = practiceSource.slice(
  comprehensiveOuterSubmitStart,
  comprehensiveOuterSubmitEnd
)
assert.match(
  comprehensiveOuterSubmitSource,
  /isAdaptiveComprehensiveTerminalSubmissionError\(error\)[\s\S]*?adaptiveComprehensiveSubmissionSnapshot = null/,
  '外层交卷异常只能对明确终态错误解锁'
)

const selectOptionStart = practiceSource.indexOf('function selectOption')
const selectOptionEnd = practiceSource.indexOf('function isQuestionAnswered', selectOptionStart)
const selectOptionSource = practiceSource.slice(selectOptionStart, selectOptionEnd)
const snapshotGuardIndex = selectOptionSource.indexOf(
  'adaptiveComprehensiveSubmissionSnapshot?.sessionId'
)
const answerMutationIndex = selectOptionSource.indexOf('selectedOption.value = key')
assert.ok(
  snapshotGuardIndex >= 0 && answerMutationIndex > snapshotGuardIndex,
  '综合交卷 snapshot 存在时必须在修改答案前锁定 selectOption'
)

const resetToTagsSource = extractNamedFunction(practiceSource, 'resetToTags')
assert.match(
  resetToTagsSource,
  /const preserveDurableComprehensiveSubmission\s*=\s*hasDurableAdaptiveComprehensiveSubmissionTask\(\)/
)
assert.match(
  resetToTagsSource,
  /if \(preserveDurableComprehensiveSubmission\) \{\s*resumePendingAdaptiveComprehensiveSubmissions\(\)\s*\} else \{\s*void endAdaptiveSession\('abandoned'\)\s*\}/,
  '退出已持久化的综合整卷时不得将会话 abandoned'
)
assert.match(
  extractNamedFunction(practiceSource, 'hasDurableAdaptiveComprehensiveSubmissionTask'),
  /ownerUserId[\s\S]*?sessionId[\s\S]*?client_submission_id/,
  '退出保护只能由已持久化的 owner\/session\/submission task 触发'
)

const payloadSnapshotStart = practiceSource.indexOf('function getAdaptiveComprehensiveSubmissionTask')
const payloadSnapshotEnd = practiceSource.indexOf(
  'async function submitAdaptiveComprehensiveAnswers',
  payloadSnapshotStart
)
const payloadSnapshotSource = practiceSource.slice(payloadSnapshotStart, payloadSnapshotEnd)
assert.match(
  payloadSnapshotSource,
  /adaptiveComprehensiveSubmissionQueue\.persist\(\{[\s\S]*?sessionId,[\s\S]*?payload:\s*adaptiveComprehensiveSubmissionSnapshot\.payload[\s\S]*?\}\)/,
  '首个服务端请求前必须同步持久化内存快照'
)

const toastMessages = []
const selectionHarness = new Function(
  'uni',
  `
    let adaptiveComprehensiveSubmissionSnapshot = {
      sessionId: 'session-fixed',
      payload: { client_submission_id: 'batch-fixed' }
    }
    const submitted = { value: false }
    const practiceMutationLocked = { value: false }
    const reviewMode = { value: false }
    const currentQuestionHasBlockingIssue = { value: false }
    const adaptiveComprehensivePracticeActive = { value: true }
    const adaptiveSession = { value: { id: 'session-fixed' } }
    const selectedOption = { value: 'A' }
    const practiceMode = { value: 'comprehensive' }
    const comprehensiveAnswers = { value: { 'question-1': 'A' } }
    const currentQuestionKey = { value: 'question-1' }
    ${extractNamedFunction(practiceSource, 'selectOption')}
    return {
      selectOption,
      selectedOption,
      comprehensiveAnswers
    }
  `
)({ showToast: (options) => toastMessages.push(options?.title) })
selectionHarness.selectOption('B')
assert.equal(selectionHarness.selectedOption.value, 'A')
assert.deepEqual(selectionHarness.comprehensiveAnswers.value, { 'question-1': 'A' })
assert.deepEqual(toastMessages, ['整卷已进入提交流程，请重试交卷'])

const comprehensiveActionStart = practiceSource.indexOf('async function handleComprehensiveAction')
const comprehensiveActionEnd = practiceSource.indexOf('function getAdaptiveComprehensiveSubmissionPayload', comprehensiveActionStart)
const comprehensiveActionSource = practiceSource.slice(comprehensiveActionStart, comprehensiveActionEnd)
assert.match(comprehensiveActionSource, /applyQuestionAt\(currentQuestionIndex\.value \+ 1\)/)
assert.doesNotMatch(
  comprehensiveActionSource,
  /fetchNextAdaptivePracticeItem|loadNextAdaptiveQuestion|requestAdaptiveNextQuestion/,
  '综合刷题正常翻页必须完全使用本地固定题单'
)

const answerSheetJumpStart = practiceSource.indexOf('function jumpToQuestion')
const answerSheetJumpEnd = practiceSource.indexOf('async function handlePrimaryAction', answerSheetJumpStart)
assert.doesNotMatch(
  practiceSource.slice(answerSheetJumpStart, answerSheetJumpEnd),
  /fetchNextAdaptivePracticeItem|loadNextAdaptiveQuestion|requestAdaptiveNextQuestion/,
  '综合刷题答题卡跳题不得请求逐题 next'
)

const invalidSkipStart = practiceSource.indexOf('async function handleInvalidQuestionNext')
const invalidSkipEnd = practiceSource.indexOf('function toggleExplanation', invalidSkipStart)
const invalidSkipSource = practiceSource.slice(invalidSkipStart, invalidSkipEnd)
const comprehensiveInvalidSkipEnd = invalidSkipSource.indexOf(
  'const context = captureAdaptiveQuestionContext(question)'
)
const comprehensiveInvalidSkipSource = invalidSkipSource.slice(0, comprehensiveInvalidSkipEnd)
assert.match(
  invalidSkipSource,
  /if \(isComprehensive\) \{[\s\S]*?applyQuestionAt\(currentQuestionIndex\.value \+ 1\)[\s\S]*?await submitComprehensiveAnswers\(\)[\s\S]*?return/,
  '综合异常题必须只在本地跳到下一题或提交固定整卷'
)
assert.ok(
  comprehensiveInvalidSkipEnd > 0,
  '综合异常题分支必须在专项事件逻辑之前结束'
)
assert.doesNotMatch(
  comprehensiveInvalidSkipSource,
  /recordAdaptiveEvent|recordAdaptivePracticeItemEvent|fetchNextAdaptivePracticeItem|loadNextAdaptiveQuestion|requestAdaptiveNextQuestion/,
  '综合异常题本地跳过不得发送 item event 或逐题 next'
)
assert.doesNotMatch(
  invalidSkipSource,
  /fetchNextAdaptivePracticeItem|loadNextAdaptiveQuestion|requestAdaptiveNextQuestion/,
  '综合异常题跳过不得请求逐题 next'
)

const apiSource = fs.readFileSync(apiPath, 'utf8')
assert.match(apiSource, /\/adaptive-practice\/sessions\/\$\{encodePathSegment\(sessionId\)\}\/submit/)

console.log('adaptive comprehensive practice contract: ok')
