import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const storage = new Map()
const responsiveCalls = []
const durableCalls = []
const committed = new Map()
const scheduledTimers = []
let joinedSubmissionResolve = null
let joinedSubmissionReject = null
let fakeNow = 1_800_000_000_000

Date.now = () => fakeNow

globalThis.setTimeout = (callback, delay) => {
  const timer = { callback, delay: Number(delay || 0), cancelled: false }
  scheduledTimers.push(timer)
  return timer
}
globalThis.clearTimeout = (timer) => {
  if (timer) timer.cancelled = true
}

globalThis.uni = {
  getStorageSync(key) {
    return storage.get(key)
  },
  setStorageSync(key, value) {
    storage.set(key, structuredClone(value))
  },
  removeStorageSync(key) {
    storage.delete(key)
  }
}

globalThis.__answerSubmissionTestMocks = {
  getAuthUser() {
    return { id: 'payload-lock-user' }
  },
  async submitAnswerResponsive(payload, onGraded) {
    const snapshot = structuredClone(payload)
    responsiveCalls.push(snapshot)
    if (snapshot.question_id === 'question-joined') {
      return await new Promise((resolve) => {
        joinedSubmissionResolve = () => resolve({
          persisted: true,
          correct_answer: 'A',
          is_correct: true,
          adaptive: { adaptive_updated: true }
        })
      })
    }
    if (snapshot.question_id === 'question-joined-failure') {
      return await new Promise((resolve, reject) => {
        joinedSubmissionReject = () => reject({ code: 'NETWORK_TIMEOUT', retryable: true })
      })
    }
    if (snapshot.question_id === 'question-joined-pending') {
      return {
        persisted: false,
        persistence_retryable: true,
        adaptive: { adaptive_updated: false, retryable: true }
      }
    }
    if (snapshot.question_id === 'question-update-terminal') {
      return {
        persisted: true,
        adaptive: { adaptive_updated: false, retryable: false }
      }
    }
    if (snapshot.question_id === 'question-persistence-pending') {
      return {
        persisted: false,
        persistence_retryable: true,
        adaptive: { adaptive_updated: false, retryable: true }
      }
    }
    if (snapshot.question_id === 'question-migration-not-persisted') {
      return {
        persisted: false,
        persistence_retryable: true,
        adaptive: { migration_pending: true }
      }
    }
    if (snapshot.question_id === 'question-auth') {
      throw { statusCode: 401, retryable: false, detail: 'login required' }
    }
    if (snapshot.question_id === 'question-invalid') {
      throw { statusCode: 422, retryable: false, detail: 'invalid payload' }
    }
    if (snapshot.question_id === 'question-update-pending') {
      throw {
        statusCode: 409,
        retryable: false,
        detail: { code: 'ADAPTIVE_UPDATE_PENDING' }
      }
    }
    if (snapshot.question_id === 'question-terminal-409') {
      throw {
        statusCode: 409,
        retryable: false,
        detail: '作答与当前个性化练习作用域不一致'
      }
    }
    const submissionId = snapshot.client_submission_id
    const existing = committed.get(submissionId)
    if (!existing) {
      committed.set(submissionId, snapshot)
      throw { code: 'NETWORK_TIMEOUT', retryable: true }
    }
    assert.deepEqual(snapshot, existing, 'manual retry must reuse the first committed payload')
    onGraded?.({
      questionId: snapshot.question_id,
      correctAnswer: 'A',
      isCorrect: snapshot.selected_answer === 'A',
      addedToWrongQuestions: snapshot.selected_answer !== 'A'
    })
    return {
      question_id: snapshot.question_id,
      selected_answer: snapshot.selected_answer,
      correct_answer: 'A',
      is_correct: snapshot.selected_answer === 'A',
      persisted: true,
      adaptive: { adaptive_updated: true }
    }
  },
  async submitAnswerDurably(payload) {
    const snapshot = structuredClone(payload)
    durableCalls.push(snapshot)
    const existing = committed.get(snapshot.client_submission_id)
    assert.deepEqual(snapshot, existing, 'automatic retry must reuse the first committed payload')
    return {
      persisted: true,
      selected_answer: snapshot.selected_answer,
      adaptive: { adaptive_updated: true }
    }
  }
}

const queueSourceUrl = new URL('../src/utils/answerSubmissionQueue.js', import.meta.url)
let queueSource = await readFile(queueSourceUrl, 'utf8')
queueSource = queueSource
  .replace(
    "import { submitAnswerDurably, submitAnswerResponsive } from '../api/answers'",
    'const { submitAnswerDurably, submitAnswerResponsive } = globalThis.__answerSubmissionTestMocks'
  )
  .replace(
    "import { getAuthUser } from './auth'",
    'const { getAuthUser } = globalThis.__answerSubmissionTestMocks'
  )

const queueModule = await import(
  `data:text/javascript;base64,${Buffer.from(queueSource).toString('base64')}`
)

const firstPayload = {
  question_id: 'question-manual',
  selected_answer: 'A',
  client_submission_id: 'run-1:answer:question-manual',
  used_time: 12,
  exam_code: 'Z001',
  practice_session_item_id: 'item-manual'
}

await assert.rejects(
  queueModule.submitAnswerWithReliableSync(firstPayload, { queueScopeKey: 'session-1' }),
  (error) => error?.code === 'NETWORK_TIMEOUT'
)
assert.equal(scheduledTimers.length, 1, 'a thrown retryable error must schedule a queue flush')
assert.equal(scheduledTimers[0].delay, 1500)

let lockedPayload = null
const changedPayload = {
  ...firstPayload,
  selected_answer: 'B',
  used_time: 30
}
const manualRetryResult = await queueModule.submitAnswerWithReliableSync(changedPayload, {
  queueScopeKey: 'session-1',
  onPayloadLocked(payload) {
    lockedPayload = payload
  }
})

assert.deepEqual(lockedPayload, firstPayload)
assert.deepEqual(responsiveCalls, [firstPayload, firstPayload])
assert.equal(manualRetryResult.selected_answer, 'A')

const automaticPayload = {
  question_id: 'question-auto',
  selected_answer: 'C',
  client_submission_id: 'run-2:answer:question-auto',
  used_time: 7,
  exam_code: 'Z002',
  practice_session_item_id: 'item-auto'
}

const automaticSettlement = queueModule.waitForAnswerSubmissionSettlement(
  automaticPayload.client_submission_id
)
await assert.rejects(
  queueModule.submitAnswerWithReliableSync(automaticPayload, { queueScopeKey: 'session-2' }),
  (error) => error?.code === 'NETWORK_TIMEOUT'
)
fakeNow += 2000
await queueModule.flushPendingAnswerSubmissions()
const automaticSettlementOutcome = await automaticSettlement

assert.deepEqual(durableCalls, [automaticPayload])
assert.equal(automaticSettlementOutcome.status, 'settled')
assert.equal(automaticSettlementOutcome.result.persisted, true)
assert.equal(automaticSettlementOutcome.result.adaptive.adaptive_updated, true)
assert.equal(storage.has('pendingAnswerSubmissionsV1'), false)

const changedAfterAutomaticSync = {
  ...automaticPayload,
  selected_answer: 'D',
  used_time: 45
}
let lockedAfterAutomaticSync = null
await queueModule.submitAnswerWithReliableSync(changedAfterAutomaticSync, {
  queueScopeKey: 'session-2',
  onPayloadLocked(payload) {
    lockedAfterAutomaticSync = payload
  }
})

assert.deepEqual(lockedAfterAutomaticSync, automaticPayload)
assert.deepEqual(responsiveCalls.at(-1), automaticPayload)

const scopedPayloadA = {
  ...automaticPayload,
  question_id: 'question-scope-a',
  client_submission_id: 'run-scope-a:answer:question-scope-a',
  practice_session_item_id: 'item-scope-a'
}
const scopedPayloadB = {
  ...automaticPayload,
  question_id: 'question-scope-b',
  client_submission_id: 'run-scope-b:answer:question-scope-b',
  practice_session_item_id: 'item-scope-b'
}
await assert.rejects(
  queueModule.submitAnswerWithReliableSync(scopedPayloadA, { queueScopeKey: 'session-scope-a' }),
  (error) => error?.code === 'NETWORK_TIMEOUT'
)
await assert.rejects(
  queueModule.submitAnswerWithReliableSync(scopedPayloadB, { queueScopeKey: 'session-scope-b' }),
  (error) => error?.code === 'NETWORK_TIMEOUT'
)
fakeNow += 2000
const durableCountBeforeScopedFlush = durableCalls.length
const scopedFlushResult = await queueModule.flushPendingAnswerSubmissions({
  queueScopeKey: 'session-scope-a'
})
assert.deepEqual(
  durableCalls.slice(durableCountBeforeScopedFlush),
  [scopedPayloadA],
  'a session-scoped flush must not wait for or submit another session'
)
assert.deepEqual(scopedFlushResult, { synced: 1, pending: 0 })
const queueAfterScopedFlush = storage.get('pendingAnswerSubmissionsV1') || []
assert.equal(
  queueAfterScopedFlush.some((entry) => entry.payload.client_submission_id === scopedPayloadA.client_submission_id),
  false
)
assert.equal(
  queueAfterScopedFlush.some((entry) => entry.payload.client_submission_id === scopedPayloadB.client_submission_id),
  true,
  'the unrelated session must remain queued for its own flush'
)
await queueModule.flushPendingAnswerSubmissions({ queueScopeKey: 'session-scope-b' })

const authPayload = {
  ...automaticPayload,
  question_id: 'question-auth',
  client_submission_id: 'run-3:answer:question-auth',
  practice_session_item_id: 'item-auth'
}
await assert.rejects(
  queueModule.submitAnswerWithReliableSync(authPayload, { queueScopeKey: 'session-3' }),
  (error) => error?.statusCode === 401
)

const invalidPayload = {
  ...automaticPayload,
  question_id: 'question-invalid',
  client_submission_id: 'run-4:answer:question-invalid',
  practice_session_item_id: 'item-invalid'
}
const invalidSettlement = queueModule.waitForAnswerSubmissionSettlement(
  invalidPayload.client_submission_id
)
await assert.rejects(
  queueModule.submitAnswerWithReliableSync(invalidPayload, { queueScopeKey: 'session-4' }),
  (error) => error?.statusCode === 422
)
assert.equal((await invalidSettlement).status, 'terminal')

const updatePendingPayload = {
  ...automaticPayload,
  question_id: 'question-update-pending',
  client_submission_id: 'run-5:answer:question-update-pending',
  practice_session_item_id: 'item-update-pending'
}
await assert.rejects(
  queueModule.submitAnswerWithReliableSync(updatePendingPayload, { queueScopeKey: 'session-5' }),
  (error) => error?.detail?.code === 'ADAPTIVE_UPDATE_PENDING'
)

const remainingQueue = storage.get('pendingAnswerSubmissionsV1') || []
assert.equal(
  remainingQueue.some((entry) => entry.payload.client_submission_id === authPayload.client_submission_id),
  true,
  '401 must preserve the owner-scoped payload for a later same-user login'
)
assert.equal(
  remainingQueue.some((entry) => entry.payload.client_submission_id === invalidPayload.client_submission_id),
  false,
  'a non-retryable validation error must be removed from the queue'
)
const pendingUpdateEntry = remainingQueue.find(
  (entry) => entry.payload.client_submission_id === updatePendingPayload.client_submission_id
)
assert.equal(pendingUpdateEntry?.retryCount, 1, 'ADAPTIVE_UPDATE_PENDING must remain retryable')

const terminal409Payload = {
  ...automaticPayload,
  question_id: 'question-terminal-409',
  client_submission_id: 'run-5b:answer:question-terminal-409',
  practice_session_item_id: 'item-terminal-409'
}
const terminal409Settlement = queueModule.waitForAnswerSubmissionSettlement(
  terminal409Payload.client_submission_id
)
await assert.rejects(
  queueModule.submitAnswerWithReliableSync(terminal409Payload, {
    queueScopeKey: 'session-5b'
  }),
  (error) => error?.statusCode === 409
)
assert.equal(
  (await terminal409Settlement).status,
  'terminal',
  'a non-retryable adaptive 409 must settle instead of hanging forever'
)
assert.equal(
  (storage.get('pendingAnswerSubmissionsV1') || []).some(
    (entry) => entry.payload.client_submission_id === terminal409Payload.client_submission_id
  ),
  false,
  'a terminal adaptive 409 must be removed from the durable retry queue'
)

const joinedPayload = {
  ...automaticPayload,
  question_id: 'question-joined',
  client_submission_id: 'run-6:answer:question-joined',
  practice_session_item_id: 'item-joined'
}
const responsiveCountBeforeJoin = responsiveCalls.length
const joinedFirst = queueModule.submitAnswerWithReliableSync(joinedPayload, {
  queueScopeKey: 'session-6'
})
const joinedSecond = queueModule.submitAnswerWithReliableSync(
  { ...joinedPayload, selected_answer: 'D' },
  { queueScopeKey: 'session-6' }
)
await Promise.resolve()
assert.equal(
  responsiveCalls.length - responsiveCountBeforeJoin,
  1,
  'concurrent retries for one client id must share the first active request'
)
joinedSubmissionResolve()
await Promise.all([joinedFirst, joinedSecond])

const joinedFailurePayload = {
  ...automaticPayload,
  question_id: 'question-joined-failure',
  client_submission_id: 'run-6a:answer:question-joined-failure',
  practice_session_item_id: 'item-joined-failure'
}
const responsiveCountBeforeJoinedFailure = responsiveCalls.length
const joinedFailureFirst = queueModule.submitAnswerWithReliableSync(joinedFailurePayload, {
  queueScopeKey: 'session-6a'
})
const joinedFailureSecond = queueModule.submitAnswerWithReliableSync(
  { ...joinedFailurePayload, selected_answer: 'D' },
  { queueScopeKey: 'session-6a' }
)
await Promise.resolve()
assert.equal(
  responsiveCalls.length - responsiveCountBeforeJoinedFailure,
  1,
  'concurrent failing callers must still share one active network request'
)
joinedSubmissionReject()
const joinedFailureResults = await Promise.allSettled([joinedFailureFirst, joinedFailureSecond])
assert.ok(joinedFailureResults.every((result) => result.status === 'rejected'))
const joinedFailureEntry = (storage.get('pendingAnswerSubmissionsV1') || []).find(
  (entry) => entry.payload.client_submission_id === joinedFailurePayload.client_submission_id
)
assert.equal(
  joinedFailureEntry?.retryCount,
  1,
  'one failed shared request must advance retry backoff exactly once'
)

const joinedPendingPayload = {
  ...automaticPayload,
  question_id: 'question-joined-pending',
  client_submission_id: 'run-6b:answer:question-joined-pending',
  practice_session_item_id: 'item-joined-pending'
}
await Promise.all([
  queueModule.submitAnswerWithReliableSync(joinedPendingPayload, {
    queueScopeKey: 'session-6b'
  }),
  queueModule.submitAnswerWithReliableSync(
    { ...joinedPendingPayload, selected_answer: 'D' },
    { queueScopeKey: 'session-6b' }
  )
])
const joinedPendingEntry = (storage.get('pendingAnswerSubmissionsV1') || []).find(
  (entry) => entry.payload.client_submission_id === joinedPendingPayload.client_submission_id
)
assert.equal(
  joinedPendingEntry?.retryCount,
  1,
  'joined callers must not increment retry backoff more than once'
)

const terminalPayload = {
  ...automaticPayload,
  question_id: 'question-update-terminal',
  client_submission_id: 'run-7:answer:question-update-terminal',
  practice_session_item_id: 'item-update-terminal'
}
const terminalSettlement = queueModule.waitForAnswerSubmissionSettlement(
  terminalPayload.client_submission_id
)
await queueModule.submitAnswerWithReliableSync(terminalPayload, { queueScopeKey: 'session-7' })
assert.equal(
  (await terminalSettlement).status,
  'terminal',
  'persisted without a successful adaptive update must never release the barrier'
)

const persistencePendingPayload = {
  ...automaticPayload,
  question_id: 'question-persistence-pending',
  client_submission_id: 'run-8:answer:question-persistence-pending',
  practice_session_item_id: 'item-persistence-pending'
}
const persistencePendingSettlement = queueModule.waitForAnswerSubmissionSettlement(
  persistencePendingPayload.client_submission_id
)
await queueModule.submitAnswerWithReliableSync(persistencePendingPayload, {
  queueScopeKey: 'session-8'
})
assert.equal(
  await Promise.race([
    persistencePendingSettlement.then(() => true),
    Promise.resolve(false)
  ]),
  false,
  'persisted:false must keep the settlement pending for reliable retry'
)

const migrationNotPersistedPayload = {
  ...automaticPayload,
  question_id: 'question-migration-not-persisted',
  client_submission_id: 'run-9:answer:question-migration-not-persisted',
  practice_session_item_id: 'item-migration-not-persisted'
}
const migrationNotPersistedSettlement = queueModule.waitForAnswerSubmissionSettlement(
  migrationNotPersistedPayload.client_submission_id
)
await queueModule.submitAnswerWithReliableSync(migrationNotPersistedPayload, {
  queueScopeKey: 'session-9'
})
assert.equal(
  await Promise.race([
    migrationNotPersistedSettlement.then(() => true),
    Promise.resolve(false)
  ]),
  false,
  'migration_pending cannot release navigation before the answer is persisted'
)

console.log('answer submission payload lock: ok')
