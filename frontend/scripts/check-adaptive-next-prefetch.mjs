import assert from 'node:assert/strict'
import fs from 'node:fs'

const brokerPath = new URL('../src/utils/adaptiveNextRequestBroker.js', import.meta.url)
const brokerSource = fs.readFileSync(brokerPath, 'utf8')
const brokerModule = await import(`data:text/javascript;base64,${Buffer.from(brokerSource).toString('base64')}`)

function deferred() {
  let resolve
  let reject
  const promise = new Promise((nextResolve, nextReject) => {
    resolve = nextResolve
    reject = nextReject
  })
  return { promise, resolve, reject }
}

const broker = brokerModule.createAdaptiveNextRequestBroker()
const firstGate = deferred()
let claimCalls = 0
const first = broker.run('session-1:item-1', async ({ isCurrent }) => {
  claimCalls += 1
  assert.equal(isCurrent(), true)
  await firstGate.promise
  return 'prefetched'
})
const joined = broker.run('session-1:item-1', async () => {
  claimCalls += 1
  return 'duplicate'
})

assert.strictEqual(joined, first, 'tap must join the in-flight prefetch promise')
await Promise.resolve()
assert.equal(claimCalls, 1, 'prefetch and tap must issue only one claim')
await assert.rejects(
  broker.run('session-1:item-other', async () => 'wrong-item'),
  (error) => error?.code === 'ADAPTIVE_NEXT_REQUEST_IN_FLIGHT',
  'a tap for another item must not join or replace the active claim'
)
assert.equal(claimCalls, 1, 'an overlapping item must not start another claim')
firstGate.resolve()
assert.equal(await joined, 'prefetched')
assert.equal(broker.hasInFlight(), false)

const staleGate = deferred()
let staleGuard
const staleRequest = broker.run('session-1:item-2', async ({ isCurrent }) => {
  staleGuard = isCurrent
  await staleGate.promise
  return 'stale'
})
await Promise.resolve()
assert.equal(staleGuard(), true)
broker.invalidate()
assert.equal(staleGuard(), false, 'reset must invalidate an old-session response')

const currentGate = deferred()
const currentRequest = broker.run('session-2:item-1', async ({ isCurrent }) => {
  assert.equal(isCurrent(), true)
  await currentGate.promise
  return 'current'
})
staleGate.resolve()
assert.equal(await staleRequest, 'stale')
assert.equal(
  broker.hasInFlight('session-2:item-1'),
  true,
  'an old request settling must not clear the new session request'
)
currentGate.resolve()
assert.equal(await currentRequest, 'current')

await assert.rejects(
  broker.run('session-2:item-2', async () => {
    throw Object.assign(new Error('temporary failure'), { statusCode: 503 })
  }),
  /temporary failure/
)
assert.equal(
  await broker.run('session-2:item-2', async () => 'retry-success'),
  'retry-success',
  'a failed speculative request must not block the foreground retry'
)

const pagePath = new URL('../src/pages/practice/index.vue', import.meta.url)
const pageSource = fs.readFileSync(pagePath, 'utf8')
const submitStart = pageSource.indexOf('async function submitAnswer()')
const submitEnd = pageSource.indexOf('function applyReviewAt', submitStart)
const submitSource = pageSource.slice(submitStart, submitEnd)
assert.match(
  submitSource,
  /adaptiveSubmissionBarrierSatisfied\(result\)[\s\S]*void prefetchNextAdaptiveQuestion\(submittedQuestion, adaptiveContext\)/,
  'successful durable adaptive answers must start background prefetch'
)
assert.match(
  submitSource,
  /!adaptivePendingSubmissionPayloads\.has\(adaptiveItemId\)/,
  'answers with pending adaptive updates must not prefetch'
)
assert.match(
  submitSource,
  /adaptiveAnswerSyncing\.value = false[\s\S]*drainAdaptiveNavigationIntent\(adaptiveContext\)/,
  'a queued tap may advance only after durable adaptive submission settles'
)
assert.match(
  submitSource,
  /const initialSubmissionPromise = submitAnswerWithReliableSync[\s\S]*rememberAdaptiveAnswerSubmission[\s\S]*adaptiveSubmissionTask\.initialPromise = initialSubmissionPromise/,
  'the first submit promise, immutable payload, and item context must stay attached'
)
assert.match(
  submitSource,
  /if \(earlyGradeReceived\)[\s\S]*adaptivePendingSubmissionPayloads\.set[\s\S]*adaptiveSubmissionTask\?\.markInitialFlowDone\(\)[\s\S]*!adaptivePendingSubmissionPayloads\.has\(adaptiveItemId\)[\s\S]*clearAdaptiveNavigationIntent/,
  'a transient first failure must retain the queued intent until settlement'
)

const barrierStart = pageSource.indexOf('function adaptiveSubmissionBarrierSatisfied')
const barrierEnd = pageSource.indexOf('function isAdaptiveSubmissionRetryableError', barrierStart)
const barrierSource = pageSource.slice(barrierStart, barrierEnd)
const barrierSatisfied = new Function(
  'getAdaptiveSubmissionOutcome',
  `${barrierSource}\nreturn adaptiveSubmissionBarrierSatisfied`
)((result) => result?.adaptive || result?.adaptive_state || null)
assert.equal(barrierSatisfied({ persisted: false, adaptive: { adaptive_updated: true } }), false)
assert.equal(barrierSatisfied({ persisted: true, adaptive: { adaptive_updated: false } }), false)
assert.equal(barrierSatisfied({ persisted: true }), false)
assert.equal(barrierSatisfied({ persisted: true, adaptive: { adaptive_updated: true } }), true)

const answerTaskStart = pageSource.indexOf('function rememberAdaptiveAnswerSubmission')
const answerTaskEnd = pageSource.indexOf('function queueAdaptiveNavigationIntent', answerTaskStart)
const answerTaskSource = pageSource.slice(answerTaskStart, answerTaskEnd)
assert.match(answerTaskSource, /Promise\.all\(\[[\s\S]*task\.settlementPromise[\s\S]*task\.initialFlowDonePromise/)
assert.match(
  answerTaskSource,
  /outcome\?\.status === 'terminal'[\s\S]*outcome\?\.result\?\.persisted === true[\s\S]*switchAdaptiveSessionToLegacy[\s\S]*drainAdaptiveNavigationIntent/,
  'a permanently failed adaptive update may advance only after safe legacy fallback'
)
assert.match(
  answerTaskSource,
  /outcome\?\.status === 'migration'[\s\S]*await switchAdaptiveSessionToLegacy\('cancelled', task\.context\)/,
  'migration settlement must join the session-scoped fallback task before releasing navigation'
)
assert.match(
  answerTaskSource,
  /!isAdaptiveSessionContextCurrent\(task\.context\)[\s\S]*adaptiveAnswerSubmissionTasks\.delete\(key\)[\s\S]*releaseAnswerSubmissionSettlement/,
  'only a stale run may discard a completed settlement before processing it'
)
assert.doesNotMatch(
  answerTaskSource.slice(0, answerTaskSource.indexOf("if (outcome?.status === 'terminal')")),
  /!isAdaptiveQuestionContextCurrent\(task\.context\)/,
  'viewing the previous question must not invalidate the answered frontier settlement'
)
assert.match(
  answerTaskSource,
  /adaptivePendingSubmissionPayloads\.delete\(task\.context\.itemId\)[\s\S]*if \(isAdaptiveQuestionContextCurrent\(task\.context\)\)[\s\S]*prefetchNextAdaptiveQuestion/,
  'a settled off-screen answer must clear its barrier while visible navigation stays item-scoped'
)
assert.match(answerTaskSource, /releaseAnswerSubmissionSettlement\(task\.submissionId\)/)

const settleStart = pageSource.indexOf('async function settleAdaptiveSubmission')
const settleEnd = pageSource.indexOf('function continueAdaptiveProgressInBackground', settleStart)
const settleSource = pageSource.slice(settleStart, settleEnd)
const migrationPendingPayloads = new Map([
  ['migration-item', { client_submission_id: 'migration-submission' }]
])
let migrationFallbackStarts = 0
let migrationRetryCalls = 0
const settleHarness = new Function(
  'isAdaptiveSessionContextCurrent',
  'adaptiveMigrationPending',
  'startAdaptiveLegacyFallbackTask',
  'adaptivePendingSubmissionPayloads',
  'adaptiveSubmissionNeedsRetry',
  'submitAnswerWithReliableSync',
  'adaptiveSession',
  'uni',
  `${settleSource}\nreturn settleAdaptiveSubmission`
)(
  () => true,
  (result) => result?.persisted === true && result?.adaptive?.migration_pending === true,
  () => {
    migrationFallbackStarts += 1
    return { promise: new Promise(() => {}) }
  },
  migrationPendingPayloads,
  () => false,
  async () => {
    migrationRetryCalls += 1
    return null
  },
  { value: { id: 'migration-session' } },
  { showToast() {} }
)
const migrationResult = {
  persisted: true,
  adaptive: { adaptive_updated: false, migration_pending: true }
}
assert.strictEqual(
  await settleHarness(
    migrationResult,
    { client_submission_id: 'migration-submission' },
    'migration-item',
    { context: { flowGeneration: 1, sessionId: 'migration-session' } }
  ),
  migrationResult,
  'a persisted migration result must return without waiting for the legacy pool'
)
assert.equal(migrationFallbackStarts, 1, 'migration must start legacy loading immediately')
assert.equal(migrationRetryCalls, 0, 'migration must not enter the adaptive-update retry loop')
assert.equal(
  migrationPendingPayloads.has('migration-item'),
  false,
  'a persisted migration result must release the obsolete adaptive retry payload'
)
assert.match(
  settleSource,
  /adaptiveMigrationPending\(finalResult\)[\s\S]*startAdaptiveLegacyFallbackTask\('cancelled', context\)[\s\S]*return finalResult/,
  'the immediate migration branch must launch fallback without awaiting it'
)

const progressStart = pageSource.indexOf('function continueAdaptiveProgressInBackground')
const progressEnd = pageSource.indexOf('async function recordAdaptiveEvent', progressStart)
const progressSource = pageSource.slice(progressStart, progressEnd)
const progressGate = deferred()
const progressLoading = { value: false }
const pendingProgress = new Map([['progress-item', { client_submission_id: 'progress-submission' }]])
const progressContext = {
  flowGeneration: 12,
  sessionId: 'progress-session',
  itemId: 'progress-item',
  questionKey: 'progress-question'
}
let progressPatienceMs = null
let progressIntent = null
let progressDrainCalls = 0
let progressClearCalls = 0
let progressFallbackTask = null
const progressHarness = new Function(
  'adaptivePendingSubmissionPayloads',
  'captureAdaptiveQuestionContext',
  'rememberAdaptiveAnswerSubmission',
  'getAdaptiveLegacyFallbackTask',
  'schedulePendingAnswerFlush',
  'isAdaptiveQuestionContextCurrent',
  'adaptiveNextLoading',
  'ADAPTIVE_PREFETCH_STILL_RUNNING',
  'ADAPTIVE_FOREGROUND_PREFETCH_WAIT_MS',
  'setTimeout',
  'setAdaptiveNavigationIntent',
  'drainAdaptiveNavigationIntent',
  'clearAdaptiveNavigationIntent',
  'uni',
  `let adaptiveNextLoadingSequence = 0
   let activeAdaptiveNextLoadingToken = 0
   ${progressSource}
   return ensureAdaptiveProgressBeforeNext`
)(
  pendingProgress,
  () => ({ ...progressContext }),
  () => ({ readyPromise: progressGate.promise }),
  () => progressFallbackTask,
  () => {},
  () => true,
  progressLoading,
  'STILL_RUNNING',
  1200,
  (callback, delayMs) => {
    progressPatienceMs = delayMs
    queueMicrotask(callback)
    return 1
  },
  (action, context, options) => {
    progressIntent = { action, context, options }
  },
  () => { progressDrainCalls += 1 },
  () => { progressClearCalls += 1 },
  { showToast() {} }
)

assert.equal(
  await progressHarness({ adaptiveSessionItemId: 'progress-item' }),
  false,
  'a pending adaptive update must release foreground navigation at the patience boundary'
)
assert.equal(progressPatienceMs, 1200)
assert.equal(progressLoading.value, false)
assert.equal(progressIntent?.action, 'next')
assert.equal(progressIntent?.options?.ready, false)
assert.equal(progressDrainCalls, 0)
progressGate.resolve(true)
await progressGate.promise
await Promise.resolve()
await Promise.resolve()
assert.equal(progressDrainCalls, 1, 'a completed background progress update must resume navigation once')
assert.equal(progressClearCalls, 0)

const fallbackProgressGate = deferred()
pendingProgress.delete('progress-item')
progressFallbackTask = {
  settled: false,
  promise: fallbackProgressGate.promise
}
progressIntent = null
progressDrainCalls = 0
progressClearCalls = 0
assert.equal(
  await progressHarness({ adaptiveSessionItemId: 'progress-item' }),
  false,
  'a pending legacy fallback must share the same foreground patience budget'
)
assert.equal(progressPatienceMs, 1200)
assert.equal(progressLoading.value, false)
assert.equal(progressIntent?.action, 'next')
assert.equal(progressIntent?.options?.ready, false)
assert.equal(progressDrainCalls, 0)
progressFallbackTask.settled = true
fallbackProgressGate.resolve({ ready: true, stale: false, extended: true })
await fallbackProgressGate.promise
await Promise.resolve()
await Promise.resolve()
await Promise.resolve()
assert.equal(
  progressDrainCalls,
  1,
  'a legacy pool completing in the background must consume the saved tap exactly once'
)
assert.equal(progressClearCalls, 0)
progressFallbackTask = null

const queueStart = pageSource.indexOf('function queueAdaptiveNavigationIntent')
const queueEnd = pageSource.indexOf('function resetAdaptivePracticeState', queueStart)
const queueSource = pageSource.slice(queueStart, queueEnd)
assert.match(queueSource, /captureAdaptiveQuestionContext\(\)/)
assert.match(queueSource, /adaptiveContextsMatch\(queued\.context, context\)/)
assert.match(queueSource, /questionNavigationLocked\.value/)

const intentFunctionsStart = pageSource.indexOf('function adaptiveContextsMatch')
const intentFunctionsSource = pageSource.slice(intentFunctionsStart, queueEnd)
const queuedNavigation = { value: null }
const navigationLocked = { value: false }
const canAdvance = { value: true }
const hasNext = { value: false }
const nextExhausted = { value: false }
const nextFinishAvailable = { value: false }
const queueable = { value: true }
const practiceMode = { value: 'special' }
const mockExamMode = { value: false }
const reviewMode = { value: false }
let currentContext = {
  flowGeneration: 1,
  sessionId: 'session-queued',
  itemId: 'item-queued',
  questionKey: 'question-queued'
}
let nextCalls = 0
let finishCalls = 0
let comprehensiveSubmitCalls = 0
let intentFallbackTask = null
const intentHarness = new Function(
  'adaptiveForwardNavigationQueueable',
  'adaptiveQueuedNavigation',
  'captureAdaptiveQuestionContext',
  'isAdaptiveQuestionContextCurrent',
  'getAdaptiveLegacyFallbackTask',
  'questionNavigationLocked',
  'canAdvanceQuestion',
  'hasNextQuestion',
  'adaptiveNextExhausted',
  'adaptiveNextFinishAvailable',
  'practiceMode',
  'mockExamMode',
  'reviewMode',
  'goNextQuestion',
  'finishQuiz',
  'submitComprehensiveAnswers',
  `${intentFunctionsSource}\nreturn { queueAdaptiveNavigationIntent, drainAdaptiveNavigationIntent }`
)(
  queueable,
  queuedNavigation,
  () => ({ ...currentContext }),
  (context) => (
    context.flowGeneration === currentContext.flowGeneration &&
    context.sessionId === currentContext.sessionId &&
    context.itemId === currentContext.itemId &&
    context.questionKey === currentContext.questionKey
  ),
  () => intentFallbackTask,
  navigationLocked,
  canAdvance,
  hasNext,
  nextExhausted,
  nextFinishAvailable,
  practiceMode,
  mockExamMode,
  reviewMode,
  () => { nextCalls += 1 },
  () => { finishCalls += 1 },
  () => { comprehensiveSubmitCalls += 1 }
)

assert.equal(intentHarness.queueAdaptiveNavigationIntent('next'), true)
const firstQueuedIntent = queuedNavigation.value
assert.equal(intentHarness.queueAdaptiveNavigationIntent('next'), true)
assert.strictEqual(
  queuedNavigation.value,
  firstQueuedIntent,
  'rapid repeated taps must retain one navigation intent object'
)
const firstQueuedContext = { ...queuedNavigation.value.context }
assert.equal(
  intentHarness.drainAdaptiveNavigationIntent({ ...firstQueuedContext, itemId: 'another-item' }),
  false,
  'another item must not consume the queued tap'
)
assert.equal(intentHarness.drainAdaptiveNavigationIntent(firstQueuedContext), true)
await Promise.resolve()
assert.equal(nextCalls, 1, 'a queued tap must auto-advance exactly once after the barrier')
assert.equal(intentHarness.drainAdaptiveNavigationIntent(firstQueuedContext), false)
assert.equal(nextCalls, 1, 'settling the same submission twice must not advance twice')

assert.equal(intentHarness.queueAdaptiveNavigationIntent('finish'), true)
navigationLocked.value = true
assert.equal(intentHarness.drainAdaptiveNavigationIntent(currentContext), false)
assert.equal(finishCalls, 0, 'a stale locked drain must never bypass navigation guards')
assert.equal(queuedNavigation.value?.ready, true, 'a result racing navigation cleanup must preserve a ready intent')
navigationLocked.value = false
assert.equal(intentHarness.drainAdaptiveNavigationIntent(currentContext), true)
assert.equal(finishCalls, 1, 'the preserved intent must drain once after navigation unlocks')
assert.equal(intentHarness.drainAdaptiveNavigationIntent(currentContext), false)
assert.equal(finishCalls, 1, 'a ready intent must not drain twice')

assert.equal(intentHarness.queueAdaptiveNavigationIntent('next'), true)
nextExhausted.value = true
assert.equal(intentHarness.drainAdaptiveNavigationIntent(currentContext), true)
await Promise.resolve()
assert.equal(nextCalls, 1, 'a terminal background result must not start another next request')
assert.equal(
  finishCalls,
  2,
  'a terminal background result must consume the queued next tap by finishing the run once'
)
nextExhausted.value = false

practiceMode.value = 'comprehensive'
assert.equal(intentHarness.queueAdaptiveNavigationIntent('finish'), true)
assert.equal(intentHarness.drainAdaptiveNavigationIntent(currentContext), true)
assert.equal(comprehensiveSubmitCalls, 1, 'comprehensive finish intent must submit the fixed round')
assert.equal(finishCalls, 2, 'comprehensive finish intent must not use the special-practice finish path')
practiceMode.value = 'special'

const nextCallsBeforeFallback = nextCalls
assert.equal(intentHarness.queueAdaptiveNavigationIntent('next'), true)
intentFallbackTask = { settled: false }
assert.equal(intentHarness.drainAdaptiveNavigationIntent(currentContext), false)
assert.equal(
  queuedNavigation.value?.ready,
  false,
  'navigation must remain queued while the shared legacy pool is still loading'
)
assert.equal(nextCalls, nextCallsBeforeFallback)
intentFallbackTask.settled = true
assert.equal(intentHarness.drainAdaptiveNavigationIntent(currentContext), true)
assert.equal(
  nextCalls,
  nextCallsBeforeFallback + 1,
  'the saved tap may advance once after the shared fallback task settles'
)
assert.equal(intentHarness.drainAdaptiveNavigationIntent(currentContext), false)
assert.equal(nextCalls, nextCallsBeforeFallback + 1)
intentFallbackTask = null

const navigationStart = pageSource.indexOf('async function goNextQuestion()')
const navigationEnd = pageSource.indexOf('function showSummary', navigationStart)
const navigationSource = pageSource.slice(navigationStart, navigationEnd)
assert.match(
  navigationSource,
  /adaptiveForwardNavigationQueueable\.value[\s\S]*queueAdaptiveNavigationIntent\('next'\)[\s\S]*practiceMutationLocked\.value/,
  'an early tap must be queued instead of bypassing the answer/update barrier'
)

const finishStart = pageSource.indexOf('async function finishQuiz()')
const finishEnd = pageSource.indexOf('function buildSpecialPracticeReviewResults', finishStart)
const finishSource = pageSource.slice(finishStart, finishEnd)
assert.match(finishSource, /navigationAction: 'finish'/)
assert.match(
  finishSource,
  /const completionPromise = endAdaptiveSession\('completed'\)\.catch[\s\S]*showSummary\(\)[\s\S]*void completionPromise/,
  'the result page must render without waiting for the session-complete request'
)
assert.doesNotMatch(
  finishSource,
  /await endAdaptiveSession\('completed'\)/,
  'the 15-second session close timeout must never block the visible summary'
)
assert.match(
  finishSource,
  /questionNavigationPending\.value = false[\s\S]*adaptiveQueuedNavigation\.value\?\.ready === true[\s\S]*drainAdaptiveNavigationIntent\(context\)/,
  'finish cleanup must consume a progress result that became ready while navigation was locked'
)

const startQuizStart = pageSource.indexOf('async function startQuiz()')
const startQuizEnd = pageSource.indexOf('function selectOption', startQuizStart)
const startQuizSource = pageSource.slice(startQuizStart, startQuizEnd)
assert.doesNotMatch(
  startQuizSource,
  /await endAdaptiveSession\('abandoned'\)/,
  'starting or cleaning up a run must not wait for the old 12s + 15s close path'
)
assert.match(startQuizSource, /const previousSessionClose = endAdaptiveSession\('abandoned'\)\.catch/)
assert.match(startQuizSource, /const failedSessionClose = endAdaptiveSession\('abandoned'\)\.catch/)

const invalidSkipStart = pageSource.indexOf('async function handleInvalidQuestionNext()')
const invalidSkipEnd = pageSource.indexOf('function toggleExplanation', invalidSkipStart)
const invalidSkipSource = pageSource.slice(invalidSkipStart, invalidSkipEnd)
assert.match(invalidSkipSource, /const recorded = await recordAdaptiveEvent\(question, 'skipped'\)/)
assert.match(invalidSkipSource, /Promise\.race\([\s\S]*ADAPTIVE_FOREGROUND_PREFETCH_WAIT_MS/)
assert.match(
  invalidSkipSource,
  /setAdaptiveNavigationIntent\(navigationAction, context, \{ ready: false \}\)[\s\S]*continueAdaptiveProgressInBackground\(skipRequest, context\)/,
  'a slow skip must keep one navigation intent and resume only after its server event succeeds'
)
assert.match(
  invalidSkipSource,
  /activeAdaptiveEventRequestToken !== eventRequestToken[\s\S]*!isAdaptiveQuestionContextCurrent\(context\)/,
  'a late skip result must stay isolated to its original generation and item'
)

const unfamiliarStart = pageSource.indexOf('async function markCurrentUnfamiliarAndNext()')
const unfamiliarEnd = pageSource.indexOf('async function handleComprehensiveAction', unfamiliarStart)
const unfamiliarSource = pageSource.slice(unfamiliarStart, unfamiliarEnd)
assert.match(unfamiliarSource, /const unfamiliarRequest = \(async \(\) =>/)
assert.match(unfamiliarSource, /Promise\.race\([\s\S]*ADAPTIVE_FOREGROUND_PREFETCH_WAIT_MS/)
assert.match(
  unfamiliarSource,
  /setAdaptiveNavigationIntent\(navigationAction, context, \{ ready: false \}\)[\s\S]*continueAdaptiveProgressInBackground\(unfamiliarRequest, context\)/,
  'a slow unfamiliar submission must resume through the same single-use intent barrier'
)
assert.match(
  unfamiliarSource,
  /activeUnfamiliarRequestToken !== unfamiliarRequestToken[\s\S]*!isAdaptiveQuestionContextCurrent\(context\)/,
  'a late unfamiliar response must not mutate a newer question or run'
)
assert.match(
  unfamiliarSource,
  /result = await settleAdaptiveSubmission\([\s\S]*return true/,
  'an adaptive unfamiliar action may become ready only after its update settlement runs'
)
assert.match(
  pageSource,
  /currentQuestionHasBlockingIssue[\s\S]*:disabled="practiceMutationLocked"[\s\S]*@tap="handleInvalidQuestionNext"/,
  'a queued slow skip must not be submitted twice'
)
assert.match(
  pageSource,
  /const practiceMutationLocked = computed\(\(\) => \([\s\S]*questionNavigationLocked\.value \|\| adaptiveNavigationQueued\.value/,
  'a background navigation intent must become an explicit mutation barrier'
)

const selectOptionStart = pageSource.indexOf('function selectOption')
const selectOptionEnd = pageSource.indexOf('function isQuestionAnswered', selectOptionStart)
assert.match(
  pageSource.slice(selectOptionStart, selectOptionEnd),
  /practiceMutationLocked\.value/,
  'a slow unfamiliar action must not allow the answer to change underneath it'
)
const submitAnswerStart = pageSource.indexOf('async function submitAnswer()')
const submitAnswerEnd = pageSource.indexOf('function applyReviewAt', submitAnswerStart)
assert.match(pageSource.slice(submitAnswerStart, submitAnswerEnd), /practiceMutationLocked\.value/)
const previousStart = pageSource.indexOf('function goPrevQuestion()')
const previousEnd = pageSource.indexOf('async function goNextQuestion()', previousStart)
assert.match(
  pageSource.slice(previousStart, previousEnd),
  /practiceMutationLocked\.value/,
  'a queued barrier must prevent switching to the previous item'
)
const applyQuestionStart = pageSource.indexOf('function applyQuestionAt')
const applyQuestionEnd = pageSource.indexOf('async function loadAiTrainingSession', applyQuestionStart)
assert.match(
  pageSource.slice(applyQuestionStart, applyQuestionEnd),
  /savedInstantResult && nextQuestion\.adaptiveSessionItemId[\s\S]*prefetchNextAdaptiveQuestion/,
  'returning to a settled answered frontier must restart one-item look-ahead'
)
const resetStart = pageSource.indexOf('function resetToTags()')
const resetEnd = pageSource.indexOf('function createClientNonce', resetStart)
assert.match(
  pageSource.slice(resetStart, resetEnd),
  /adaptiveAnswerSyncing\.value \|\| adaptiveNavigationQueued\.value/,
  'a queued background barrier must not be discarded by resetting the run'
)

const requestStart = pageSource.indexOf('function requestAdaptiveNextQuestion')
const requestEnd = pageSource.indexOf('function goPrevQuestion', requestStart)
const requestSource = pageSource.slice(requestStart, requestEnd)
assert.match(requestSource, /adaptiveNextRequestBroker\.run\(/)
assert.match(requestSource, /if \(prefetchOnly\) \{[\s\S]*return true[\s\S]*applyQuestionAt\(nextIndex\)/)
assert.match(requestSource, /if \(prefetchOnly\) \{[\s\S]*return false/)
assert.match(requestSource, /Promise\.race\([\s\S]*ADAPTIVE_FOREGROUND_PREFETCH_WAIT_MS/)
assert.match(
  requestSource,
  /const outcome = !prefetchOnly\s*\? await Promise\.race/,
  'every foreground next request must use the short patience budget'
)
assert.doesNotMatch(
  requestSource,
  /const outcome = !prefetchOnly && joinsInFlightPrefetch/,
  'a fresh foreground request must not fall back to the full network timeout'
)

const loadStart = pageSource.indexOf('async function loadNextAdaptiveQuestion')
const loadEnd = pageSource.indexOf('function prefetchNextAdaptiveQuestion', loadStart)
const loadSource = pageSource.slice(loadStart, loadEnd)
const freshRequest = deferred()
const freshContext = {
  flowGeneration: 9,
  sessionId: 'fresh-session',
  itemId: 'fresh-item',
  questionKey: 'fresh-question'
}
const freshLoading = { value: false }
let observedPatienceMs = null
let savedFreshIntent = null
let backgroundContinuation = null
const loadHarness = new Function(
  'captureAdaptiveQuestionContext',
  'adaptiveSession',
  'adaptiveNextRequestBroker',
  'adaptiveNextRequestKey',
  'isAdaptiveSessionContextCurrent',
  'adaptiveMayHaveNext',
  'adaptiveNextLoading',
  'adaptiveNextPrefetching',
  'requestAdaptiveNextQuestion',
  'ADAPTIVE_PREFETCH_STILL_RUNNING',
  'ADAPTIVE_FOREGROUND_PREFETCH_WAIT_MS',
  'setTimeout',
  'setAdaptiveNavigationIntent',
  'continueAdaptiveNextRequestInBackground',
  'uni',
  `let adaptiveNextLoadingSequence = 0
   let activeAdaptiveNextLoadingToken = 0
   let adaptiveNextPrefetchSequence = 0
   let activeAdaptiveNextPrefetchToken = 0
   ${loadSource}
   return loadNextAdaptiveQuestion`
)(
  () => ({ ...freshContext }),
  { value: { id: freshContext.sessionId } },
  { hasInFlight: () => false },
  () => 'fresh-key',
  () => true,
  { value: true },
  freshLoading,
  { value: false },
  () => freshRequest.promise,
  'STILL_RUNNING',
  1200,
  (callback, delayMs) => {
    observedPatienceMs = delayMs
    queueMicrotask(callback)
    return 1
  },
  (action, context, options) => {
    savedFreshIntent = { action, context, options }
  },
  (request, context) => {
    backgroundContinuation = { request, context }
  },
  { showToast() {} }
)

assert.equal(
  await loadHarness({ context: freshContext }),
  false,
  'a fresh foreground request must release control when its patience budget expires'
)
assert.equal(observedPatienceMs, 1200)
assert.equal(freshLoading.value, false, 'foreground loading must unlock at the patience boundary')
assert.equal(savedFreshIntent?.action, 'next')
assert.equal(savedFreshIntent?.options?.ready, false)
assert.strictEqual(backgroundContinuation?.request, freshRequest.promise)
assert.deepEqual(backgroundContinuation?.context, freshContext)
assert.match(
  requestSource,
  /outcome === ADAPTIVE_PREFETCH_STILL_RUNNING[\s\S]*setAdaptiveNavigationIntent\('next', requestContext, \{ ready: false \}\)/,
  'a foreground patience timeout must preserve the learner navigation intent'
)
assert.match(
  requestSource,
  /!joinsInFlightPrefetch[\s\S]*continueAdaptiveNextRequestInBackground\(nextRequest, requestContext\)/,
  'a fresh timed-out request must continue under a background completion observer'
)
assert.match(
  requestSource,
  /if \(prefetchOnly\) \{[\s\S]*drainAdaptiveNavigationIntent\(requestContext\)[\s\S]*return true/,
  'a late background prefetch must consume the saved intent and auto-advance'
)
assert.match(pageSource, /!adaptiveNextFinishAvailable\.value[\s\S]*adaptiveMayHaveNext\.value \|\| adaptiveNextPrefetching\.value/)
assert.match(pageSource, /adaptiveMayHaveNext\.value \|\| adaptiveNextPrefetching\.value/)
assert.ok(
  (pageSource.match(/adaptiveNextRequestBroker\.invalidate\(\)/g) || []).length >= 2,
  'page reset and unload must invalidate any speculative response'
)

const fallbackStart = pageSource.indexOf('function isAdaptiveNextFallbackError')
const fallbackEnd = pageSource.indexOf('function isAdaptiveSafePoolError', fallbackStart)
const fallbackPolicy = pageSource.slice(fallbackStart, fallbackEnd)
assert.doesNotMatch(
  fallbackPolicy,
  /SAFE_POOL/,
  'safe-pool exhaustion must stay in adaptive mode instead of legacy fallback'
)
assert.match(
  fallbackPolicy,
  /ADAPTIVE_\(\?:MIGRATION_PENDING\|DIAGNOSTIC_POOL_UNAVAILABLE\)/,
  'a thrown migration-pending next response must enter the same legacy fallback path'
)
assert.match(
  requestSource,
  /isAdaptiveNextFallbackError\(error\)[\s\S]*await switchAdaptiveSessionToLegacy\('abandoned', context\)/,
  'a thrown migration-pending next response must start fallback inside the existing request'
)

const switchStart = pageSource.indexOf('function adaptiveLegacyFallbackTaskKey')
const switchEnd = pageSource.indexOf('function adaptiveNextRequestKey', switchStart)
const switchSource = pageSource.slice(switchStart, switchEnd)
assert.match(switchSource, /const closePromise = endAdaptiveSession\(reason\)\.catch/)
assert.match(switchSource, /status: reason === 'completed' \? 'completed' : 'abandoned'/)
assert.match(switchSource, /adaptiveFallbackMode\.value = true/)
assert.match(switchSource, /settled: false/)
assert.match(switchSource, /task\.settled = true/)
assert.match(
  switchSource,
  /loadLegacyQuestionPool\(moduleInfos, \{[\s\S]*updateShortageTip: false/,
  'fallback loading must keep all reactive writes behind the task identity guard'
)
assert.doesNotMatch(
  switchSource,
  /adaptiveLegacyFallbackTasks\.delete\(key\)/,
  'a settled fallback record must remain reusable for the rest of the session'
)
assert.doesNotMatch(
  switchSource,
  /await endAdaptiveSession\(reason\)/,
  'legacy fallback must not wait on or remain blocked by the old close request'
)

let activeFallbackFlow = 41
const fallbackTasks = new Map()
const fallbackSession = {
  value: { id: 'fallback-session', status: 'active', question_count: 2 }
}
const fallbackMode = { value: false }
const fallbackLoading = { value: false }
const fallbackExhausted = { value: false }
const fallbackFinishAvailable = { value: true }
const fallbackPool = { value: [{ id: 'question-1' }] }
const fallbackTip = { value: '' }
let fallbackLoaderCalls = 0
let fallbackCloseCalls = 0
let fallbackLoaderOptions = []
let fallbackLoadImplementation
const fallbackHarness = new Function(
  'adaptiveLegacyFallbackTasks',
  'captureAdaptiveQuestionContext',
  'isAdaptiveSessionContextCurrent',
  'getTargetModuleInfos',
  'plannedQuestionLimit',
  'endAdaptiveSession',
  'adaptiveSession',
  'adaptiveFallbackMode',
  'adaptiveLegacyFallbackLoading',
  'adaptiveNextExhausted',
  'adaptiveNextFinishAvailable',
  'loadLegacyQuestionPool',
  'questionPool',
  'getQuestionIdentityKey',
  'shortageTip',
  `${switchSource}\nreturn {
    getAdaptiveLegacyFallbackTask,
    startAdaptiveLegacyFallbackTask,
    switchAdaptiveSessionToLegacy
  }`
)(
  fallbackTasks,
  () => ({
    flowGeneration: activeFallbackFlow,
    sessionId: String(fallbackSession.value?.id || ''),
    itemId: 'fallback-item',
    questionKey: 'question-1'
  }),
  (context) => (
    context?.flowGeneration === activeFallbackFlow &&
    (!context?.sessionId || context.sessionId === String(fallbackSession.value?.id || ''))
  ),
  () => [{ module: 'module', submodule: 'submodule' }],
  { value: 3 },
  async () => {
    fallbackCloseCalls += 1
    return null
  },
  fallbackSession,
  fallbackMode,
  fallbackLoading,
  fallbackExhausted,
  fallbackFinishAvailable,
  (moduleInfos, options) => {
    fallbackLoaderCalls += 1
    fallbackLoaderOptions.push(options)
    return fallbackLoadImplementation(moduleInfos, options)
  },
  fallbackPool,
  (question) => String(question?.id || ''),
  fallbackTip
)

const fallbackContext = {
  flowGeneration: activeFallbackFlow,
  sessionId: 'fallback-session',
  itemId: 'fallback-item',
  questionKey: 'question-1'
}
const fallbackGate = deferred()
fallbackLoadImplementation = () => fallbackGate.promise
const firstFallbackTask = fallbackHarness.startAdaptiveLegacyFallbackTask(
  'cancelled',
  fallbackContext
)
const joinedFallbackTask = fallbackHarness.startAdaptiveLegacyFallbackTask(
  'cancelled',
  fallbackContext
)
assert.strictEqual(
  joinedFallbackTask,
  firstFallbackTask,
  'the same generation and session must share one legacy-pool task'
)
assert.equal(fallbackLoaderCalls, 1)
assert.equal(fallbackCloseCalls, 1)
assert.equal(fallbackMode.value, true)
assert.equal(fallbackLoading.value, true)
assert.equal(fallbackExhausted.value, true)
assert.equal(fallbackFinishAvailable.value, false)
fallbackGate.resolve([
  { id: 'question-1' },
  { id: 'question-2' },
  { id: 'question-3' }
])
const firstFallbackOutcome = await firstFallbackTask.promise
assert.equal(firstFallbackOutcome.ready, true)
assert.equal(firstFallbackOutcome.extended, true)
assert.equal(firstFallbackTask.settled, true)
assert.equal(fallbackLoading.value, false)
assert.deepEqual(fallbackPool.value.map((question) => question.id), ['question-1', 'question-2'])
assert.equal(
  fallbackPool.value.length,
  fallbackSession.value.question_count,
  'fallback must preserve the server-forced warm-up length'
)
assert.equal(fallbackLoaderOptions[0]?.updateShortageTip, false)
assert.strictEqual(
  fallbackHarness.startAdaptiveLegacyFallbackTask('cancelled', fallbackContext),
  firstFallbackTask,
  'a fast completed fallback must not be loaded a second time by settlement callbacks'
)
assert.equal(
  await fallbackHarness.switchAdaptiveSessionToLegacy('cancelled', fallbackContext),
  true
)
assert.equal(fallbackLoaderCalls, 1)
assert.equal(fallbackCloseCalls, 1)

fallbackSession.value = { id: 'fallback-empty', status: 'active' }
fallbackPool.value = [{ id: 'question-current' }]
const emptyFallbackContext = {
  ...fallbackContext,
  sessionId: 'fallback-empty',
  questionKey: 'question-current'
}
fallbackLoadImplementation = async () => [{ id: 'question-current' }]
const emptyFallbackTask = fallbackHarness.startAdaptiveLegacyFallbackTask(
  'cancelled',
  emptyFallbackContext
)
const emptyFallbackOutcome = await emptyFallbackTask.promise
assert.equal(emptyFallbackOutcome.ready, true)
assert.equal(emptyFallbackOutcome.extended, false)
assert.equal(emptyFallbackTask.settled, true)
assert.equal(fallbackLoading.value, false)
assert.strictEqual(
  fallbackHarness.startAdaptiveLegacyFallbackTask('cancelled', emptyFallbackContext),
  emptyFallbackTask,
  'an empty fallback result is final for that session and must not refetch in a loop'
)

fallbackSession.value = { id: 'fallback-failed', status: 'active' }
fallbackTip.value = ''
const failedFallbackContext = {
  ...fallbackContext,
  sessionId: 'fallback-failed'
}
fallbackLoadImplementation = async () => {
  throw new Error('legacy pool unavailable')
}
const failedFallbackTask = fallbackHarness.startAdaptiveLegacyFallbackTask(
  'cancelled',
  failedFallbackContext
)
const failedFallbackOutcome = await failedFallbackTask.promise
assert.equal(failedFallbackOutcome.ready, true)
assert.equal(failedFallbackOutcome.extended, false)
assert.equal(failedFallbackTask.settled, true)
assert.equal(fallbackLoading.value, false)
assert.match(fallbackTip.value, /后续题目暂时加载失败/)
const callsAfterFailure = fallbackLoaderCalls
assert.strictEqual(
  fallbackHarness.startAdaptiveLegacyFallbackTask('cancelled', failedFallbackContext),
  failedFallbackTask
)
assert.equal(fallbackLoaderCalls, callsAfterFailure, 'a failed fallback must not spin duplicate loads')

fallbackSession.value = { id: 'fallback-stale', status: 'active' }
fallbackPool.value = [{ id: 'stale-current' }]
fallbackTip.value = 'stale-before-reset'
const staleFallbackContext = {
  ...fallbackContext,
  sessionId: 'fallback-stale',
  questionKey: 'stale-current'
}
const staleFallbackGate = deferred()
fallbackLoadImplementation = () => staleFallbackGate.promise
const staleFallbackTask = fallbackHarness.startAdaptiveLegacyFallbackTask(
  'cancelled',
  staleFallbackContext
)
assert.equal(fallbackLoading.value, true)
activeFallbackFlow += 1
fallbackSession.value = { id: 'new-session', status: 'active' }
fallbackTasks.clear()
fallbackLoading.value = false
fallbackPool.value = [{ id: 'new-question' }]
fallbackTip.value = 'new-session-tip'
staleFallbackGate.resolve([{ id: 'stale-added' }])
const staleFallbackOutcome = await staleFallbackTask.promise
assert.equal(staleFallbackOutcome.ready, false)
assert.equal(staleFallbackOutcome.stale, true)
assert.deepEqual(fallbackPool.value, [{ id: 'new-question' }])
assert.equal(fallbackTip.value, 'new-session-tip')
assert.equal(fallbackLoading.value, false)

assert.ok(
  (pageSource.match(/adaptiveLegacyFallbackTasks\.clear\(\)/g) || []).length >= 2,
  'reset and unload must both detach old fallback tasks'
)
assert.ok(
  (pageSource.match(/adaptiveLegacyFallbackLoading\.value = false/g) || []).length >= 3,
  'reset, unload, and the current task settlement must all release fallback loading'
)

const legacyPoolStart = pageSource.indexOf('async function loadLegacyQuestionPool')
const legacyPoolEnd = pageSource.indexOf('async function fetchMockExamSectionPool', legacyPoolStart)
const legacyPoolSource = pageSource.slice(legacyPoolStart, legacyPoolEnd)
assert.match(legacyPoolSource, /\{ updateShortageTip = true \} = \{\}/)
assert.match(
  legacyPoolSource,
  /if \(updateShortageTip\) \{[\s\S]*shortageTip\.value/,
  'a stale fallback loader must not write a newer run\'s shortage message'
)

const safeCompletionStart = pageSource.indexOf('function exposeAdaptiveSafePoolCompletion')
const safeCompletionEnd = pageSource.indexOf('function continueAdaptiveNextRequestInBackground', safeCompletionStart)
const safeCompletionSource = pageSource.slice(safeCompletionStart, safeCompletionEnd)
assert.match(safeCompletionSource, /adaptiveNextExhausted\.value = true/)
assert.match(safeCompletionSource, /adaptiveNextFinishAvailable\.value = true/)
assert.match(
  requestSource,
  /if \(prefetchOnly\) \{[\s\S]*isAdaptiveSafePoolError\(error\)[\s\S]*drainAdaptiveNavigationIntent\(requestContext\)/,
  'a safe-pool result from background prefetch must settle an already queued tap'
)
assert.match(
  navigationSource,
  /questionNavigationPending\.value = false[\s\S]*adaptiveQueuedNavigation\.value\?\.ready === true[\s\S]*drainAdaptiveNavigationIntent\(context\)/,
  'navigation cleanup must drain a result that became ready during its narrow locked window'
)
assert.match(
  navigationSource,
  /adaptiveNextExhausted\.value[\s\S]*!adaptiveNextFinishAvailable\.value[\s\S]*finishAfterNavigation = true/,
  'safe-pool exhaustion must leave completion to the visible finish action'
)

console.log('adaptive next prefetch: ok')
