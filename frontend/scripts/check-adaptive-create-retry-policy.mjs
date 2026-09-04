import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const practicePageUrl = new URL('../src/pages/practice/index.vue', import.meta.url)
const source = await readFile(practicePageUrl, 'utf8')
const policyStart = source.indexOf('function isAdaptiveCreateFallbackError')
const policyEnd = source.indexOf('function captureAdaptiveQuestionContext')

assert.ok(policyStart >= 0 && policyEnd > policyStart, 'adaptive retry policy helpers must remain discoverable')

const policySource = source.slice(policyStart, policyEnd)
const loadPolicy = new Function(`
  ${policySource}
  return {
    isAdaptiveCreateFallbackError,
    isAdaptiveCreateImmediateFallbackError,
    isAdaptiveCreateRetryableError,
    isAdaptiveNextFallbackError
  }
`)
const policy = loadPolicy()

const immediateFallbackErrors = [
  { statusCode: 404, detail: 'route missing', retryable: false },
  { statusCode: 503, detail: '个性化出题正在灰度开放', retryable: true },
  { statusCode: 503, detail: '个性化出题数据迁移尚未启用', retryable: true },
  { statusCode: 503, detail: { code: 'ADAPTIVE_MIGRATION_PENDING' }, retryable: true },
  { statusCode: 503, detail: { code: 'ADAPTIVE_DIAGNOSTIC_POOL_UNAVAILABLE' }, retryable: true },
  { statusCode: 503, detail: { code: 'ADAPTIVE_COMPREHENSIVE_POOL_UNAVAILABLE' }, retryable: true }
]

for (const error of immediateFallbackErrors) {
  assert.equal(policy.isAdaptiveCreateImmediateFallbackError(error), true)
  assert.equal(policy.isAdaptiveCreateRetryableError(error), false)
  assert.equal(policy.isAdaptiveCreateFallbackError(error), true)
}

const transientServiceError = {
  statusCode: 503,
  detail: '个性化练习会话创建失败',
  retryable: true
}
assert.equal(policy.isAdaptiveCreateImmediateFallbackError(transientServiceError), false)
assert.equal(policy.isAdaptiveCreateRetryableError(transientServiceError), true)
assert.equal(policy.isAdaptiveCreateFallbackError(transientServiceError), true)

const incompleteComprehensiveRound = {
  statusCode: 503,
  detail: { code: 'ADAPTIVE_COMPREHENSIVE_ROUND_INCOMPLETE' },
  retryable: true
}
assert.equal(policy.isAdaptiveCreateImmediateFallbackError(incompleteComprehensiveRound), false)
assert.equal(policy.isAdaptiveCreateRetryableError(incompleteComprehensiveRound), true)

const safePoolError = {
  statusCode: 503,
  detail: { code: 'ADAPTIVE_SAFE_POOL_UNAVAILABLE' },
  retryable: true
}
assert.equal(
  policy.isAdaptiveNextFallbackError(safePoolError),
  false,
  'safe-pool exhaustion must not fall back to an unconstrained legacy question'
)

const startQuizStart = source.indexOf('async function startQuiz()')
const startQuizEnd = source.indexOf('function selectOption', startQuizStart)
assert.ok(startQuizStart >= 0 && startQuizEnd > startQuizStart)
const startQuizSource = source.slice(startQuizStart, startQuizEnd)
assert.match(
  startQuizSource,
  /resetQuizState\(\)[\s\S]*mode\.value = 'tags'[\s\S]*uni\.showLoading/,
  'a backgrounded retry must not expose the previous round as an interactive quiz'
)
assert.match(
  startQuizSource,
  /const legacyPoolRequest = loadLegacyQuestionPool\(moduleInfos, \{[\s\S]*updateShortageTip: false[\s\S]*Promise\.race\(\[[\s\S]*ADAPTIVE_FOREGROUND_PREFETCH_WAIT_MS/,
  'legacy fallback at quiz start must share one request and use the 1.2s foreground budget'
)
assert.equal(
  (startQuizSource.match(/loadLegacyQuestionPool\(moduleInfos/g) || []).length,
  1,
  'a backgrounded start must reuse the original legacy-pool promise instead of loading twice'
)
assert.doesNotMatch(
  startQuizSource,
  /await loadLegacyQuestionPool\(moduleInfos/,
  'quiz start must not wait for the full legacy request timeout'
)

const createStart = source.indexOf('async function createAdaptivePractice(')
const createEnd = source.indexOf('async function startQuiz()', createStart)
assert.ok(createStart >= 0 && createEnd > createStart)
const createSource = source.slice(createStart, createEnd)
assert.equal(
  (createSource.match(/createAdaptivePracticeSession\(/g) || []).length,
  2,
  'adaptive create may issue at most one explicit recovery request'
)
assert.match(
  createSource,
  /createAdaptivePracticeSession\(payload\)[\s\S]*createAdaptivePracticeSession\(\{[\s\S]*\.\.\.payload,[\s\S]*resume_existing_session: true/,
  'only the second create attempt must be marked as an existing-session recovery'
)
assert.match(
  startQuizSource,
  /legacyPoolOutcome === ADAPTIVE_LEGACY_START_STILL_RUNNING[\s\S]*quizStartBackgrounded\.value = true[\s\S]*loading\.value = false[\s\S]*uni\.hideLoading\(\)[\s\S]*legacyPoolRequest[\s\S]*\.then\(\(nextPool\)/,
  'the full-screen loader must clear at the patience boundary while the same request continues'
)
assert.match(
  startQuizSource,
  /activeQuizStartRequestToken === startRequestToken &&[\s\S]*!startContinuesInBackground/,
  'foreground cleanup must not unlock a still-running background start for duplicate taps'
)
assert.match(
  startQuizSource,
  /activeQuizStartRequestToken !== startRequestToken \|\|[\s\S]*flowGeneration !== adaptiveFlowGeneration \|\|[\s\S]*!isPracticeStartContextCurrent\(startContext\)/,
  'a late legacy-pool result must not enter an obsolete run'
)

console.log('adaptive create retry policy: ok')
