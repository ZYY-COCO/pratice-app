import { submitAnswerDurably, submitAnswerResponsive } from '../api/answers'
import { getAuthUser } from './auth'

const STORAGE_KEY = 'pendingAnswerSubmissionsV1'
const MAX_PENDING_SUBMISSIONS = 200
const MAX_RETRY_BACKOFF_STEP = 8
const MAX_RETRY_DELAY_MS = 5 * 60 * 1000
const activeSubmissionIds = new Set()
const activeSubmissionPromises = new Map()
const lockedSubmissionPayloads = new Map()
const submissionSettlementRecords = new Map()
let flushPromise = null
let flushRequestedAfterCurrent = false
const scopedFlushPromises = new Map()
const scopedFlushRequestedAfterCurrent = new Set()
let scheduledFlushTimer = null
let scheduledFlushDueAt = 0
const scheduledScopedFlushes = new Map()

function readQueue() {
  const stored = uni.getStorageSync(STORAGE_KEY)
  if (!Array.isArray(stored)) return []
  return stored.filter((item) => item?.payload?.client_submission_id)
}

function writeQueue(items) {
  const retainedItems = items.slice(-MAX_PENDING_SUBMISSIONS)
  if (items.length > retainedItems.length) {
    const retainedIds = new Set(
      retainedItems.map((item) => String(item?.payload?.client_submission_id || ''))
    )
    for (const item of items.slice(0, items.length - retainedItems.length)) {
      const submissionId = String(item?.payload?.client_submission_id || '')
      if (!submissionId || retainedIds.has(submissionId)) continue
      lockedSubmissionPayloads.delete(submissionId)
      publishSubmissionSettlement(submissionId, {
        status: 'terminal',
        error: Object.assign(new Error('answer submission queue capacity exceeded'), {
          code: 'ANSWER_SUBMISSION_QUEUE_CAPACITY_EXCEEDED'
        })
      })
    }
  }

  if (retainedItems.length) {
    uni.setStorageSync(STORAGE_KEY, retainedItems)
  } else {
    uni.removeStorageSync(STORAGE_KEY)
  }
}

function currentOwnerId() {
  return String(getAuthUser()?.id || '')
}

function adaptiveScopeKey(payload) {
  if (!payload?.practice_session_item_id) return ''
  const clientId = String(payload?.client_submission_id || '')
  const practiceRunId = clientId.split(':')[0] || String(payload.practice_session_item_id)
  return `adaptive:${String(payload?.exam_code || '')}:${practiceRunId}`
}

function retryDelayMs(retryCount) {
  const exponent = Math.max(0, Math.min(Number(retryCount || 1) - 1, 8))
  return Math.min(MAX_RETRY_DELAY_MS, 1500 * (2 ** exponent))
}

function lockSubmissionPayload(submissionId, payload) {
  const existing = lockedSubmissionPayloads.get(submissionId)
  if (existing) return { ...existing }

  const locked = { ...payload }
  lockedSubmissionPayloads.set(submissionId, locked)
  if (lockedSubmissionPayloads.size > MAX_PENDING_SUBMISSIONS) {
    const oldestId = lockedSubmissionPayloads.keys().next().value
    if (oldestId) lockedSubmissionPayloads.delete(oldestId)
  }
  return { ...locked }
}

function getSubmissionSettlementRecord(submissionId) {
  const normalizedId = String(submissionId || '')
  if (!normalizedId) return null
  const existing = submissionSettlementRecords.get(normalizedId)
  if (existing) return existing

  let resolve
  const promise = new Promise((nextResolve) => {
    resolve = nextResolve
  })
  const record = { promise, resolve, settled: false }
  submissionSettlementRecords.set(normalizedId, record)
  if (submissionSettlementRecords.size > MAX_PENDING_SUBMISSIONS) {
    const removableId = [...submissionSettlementRecords.entries()]
      .find(([id, item]) => id !== normalizedId && item.settled)?.[0]
    if (removableId) submissionSettlementRecords.delete(removableId)
  }
  return record
}

function publishSubmissionSettlement(submissionId, outcome) {
  const record = getSubmissionSettlementRecord(submissionId)
  if (!record || record.settled) return
  record.settled = true
  record.resolve(outcome)
}

export function waitForAnswerSubmissionSettlement(clientSubmissionId) {
  const record = getSubmissionSettlementRecord(clientSubmissionId)
  return record
    ? record.promise
    : Promise.resolve({ status: 'terminal', error: new Error('missing client submission id') })
}

export function releaseAnswerSubmissionSettlement(clientSubmissionId) {
  const normalizedId = String(clientSubmissionId || '')
  if (normalizedId) submissionSettlementRecords.delete(normalizedId)
}

function submissionResultStatus(payload, result) {
  if (result?.persisted !== true) {
    return result?.persistence_retryable === false ? 'terminal' : 'pending'
  }
  if (hasPendingAdaptiveMigration(result)) return 'migration'
  if (!payload?.practice_session_item_id) return 'settled'
  const adaptive = result?.adaptive || result?.adaptive_state
  if (adaptive?.adaptive_updated === true) return 'settled'
  if (hasRetryableAdaptiveUpdate(result)) return 'pending'
  return 'terminal'
}

function trackSubmissionResult(submissionId, payload, result) {
  const status = submissionResultStatus(payload, result)
  if (status !== 'pending') {
    publishSubmissionSettlement(submissionId, { status, result })
  }
  return status
}

function runActiveSubmission(submissionId, requestFactory) {
  const normalizedId = String(submissionId || '')
  const existing = activeSubmissionPromises.get(normalizedId)
  if (existing) return { promise: existing, owner: false }

  activeSubmissionIds.add(normalizedId)
  const promise = (async () => {
    try {
      return await requestFactory()
    } finally {
      if (activeSubmissionPromises.get(normalizedId) === promise) {
        activeSubmissionPromises.delete(normalizedId)
      }
      activeSubmissionIds.delete(normalizedId)
    }
  })()
  activeSubmissionPromises.set(normalizedId, promise)
  return { promise, owner: true }
}

function queueSubmission(payload, queueScopeKey = '') {
  const submissionId = String(payload?.client_submission_id || '')
  if (!submissionId) return { ...payload }

  const queue = readQueue()
  const existingIndex = queue.findIndex((item) => item.payload.client_submission_id === submissionId)
  const existing = existingIndex >= 0 ? queue[existingIndex] : null
  const explicitScopeKey = String(queueScopeKey || '').trim()
  // The first payload attached to a client submission id is immutable. A
  // response can be lost after the server has already committed the answer;
  // replacing the queued option on a later tap would turn the idempotency key
  // into a conflicting request and make the UI disagree with durable history.
  const lockedPayload = lockSubmissionPayload(
    submissionId,
    existing?.payload || payload
  )
  const entry = {
    ownerId: existing?.ownerId || currentOwnerId(),
    payload: lockedPayload,
    queuedAt: existing?.queuedAt || Date.now(),
    scopeKey: existing?.scopeKey || (
      explicitScopeKey
        ? `adaptive-session:${explicitScopeKey}`
        : (adaptiveScopeKey(lockedPayload) || `submission:${submissionId}`)
    ),
    retryCount: Number(existing?.retryCount || 0),
    nextRetryAt: Number(existing?.nextRetryAt || 0),
    autoPaused: false
  }
  if (existingIndex >= 0) {
    queue.splice(existingIndex, 1, entry)
  } else {
    queue.push(entry)
  }
  writeQueue(queue)
  return { ...lockedPayload }
}

function markSubmissionForRetry(submissionId) {
  const normalizedId = String(submissionId || '')
  if (!normalizedId) return { paused: true, delayMs: MAX_RETRY_DELAY_MS }

  const queue = readQueue()
  const index = queue.findIndex((item) => item.payload.client_submission_id === normalizedId)
  if (index < 0) return { paused: true, delayMs: MAX_RETRY_DELAY_MS }

  const retryCount = Math.min(
    Number(queue[index].retryCount || 0) + 1,
    MAX_RETRY_BACKOFF_STEP
  )
  const paused = false
  const delayMs = retryDelayMs(retryCount)
  queue.splice(index, 1, {
    ...queue[index],
    retryCount,
    nextRetryAt: Date.now() + delayMs,
    autoPaused: false
  })
  writeQueue(queue)
  return { paused, delayMs }
}

function removeSubmission(submissionId) {
  const normalizedId = String(submissionId || '')
  if (!normalizedId) return
  writeQueue(readQueue().filter((item) => item.payload.client_submission_id !== normalizedId))
}

function hasRetryableAdaptiveUpdate(result) {
  const adaptive = result?.adaptive || result?.adaptive_state
  return (
    adaptive?.migration_pending !== true &&
    (
      (adaptive?.adaptive_updated === false && adaptive?.retryable === true) ||
      hasAdaptiveUpdatePendingMarker(adaptive)
    )
  )
}

function hasAdaptiveUpdatePendingMarker(value) {
  if (!value) return false
  try {
    return /ADAPTIVE_UPDATE_PENDING/i.test(
      typeof value === 'string' ? value : JSON.stringify(value)
    )
  } catch (error) {
    return /ADAPTIVE_UPDATE_PENDING/i.test(String(value?.code || value?.error || value?.detail || ''))
  }
}

function isAdaptiveUpdatePendingError(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  return statusCode === 409 && hasAdaptiveUpdatePendingMarker(error)
}

function isPermanentSubmissionConflict(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  if (statusCode !== 409) return false
  let errorText = ''
  try {
    errorText = typeof error === 'string' ? error : JSON.stringify(error)
  } catch (serializationError) {
    errorText = String(error?.code || error?.detail || error?.message || '')
  }
  return /ANSWER_SUBMISSION_CONFLICT|同一提交标识已用于不同答案/i.test(errorText)
}

function isPermanentSubmissionError(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  if (isAdaptiveUpdatePendingError(error) || isDeferredAuthError(error)) return false
  if (isPermanentSubmissionConflict(error)) return true
  return (
    error?.retryable !== true &&
    statusCode >= 400 &&
    statusCode < 500 &&
    ![408, 429].includes(statusCode)
  )
}

function isDeferredAuthError(error) {
  return Number(error?.statusCode || error?.status || 0) === 401
}

function isRetryableSubmissionError(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  return error?.retryable === true || [408, 429, 500, 502, 503, 504].includes(statusCode)
}

function hasPendingAdaptiveMigration(result) {
  const adaptive = result?.adaptive || result?.adaptive_state
  return adaptive?.migration_pending === true
}

export async function submitAnswerWithReliableSync(
  payload,
  { onGraded, onPayloadLocked, queueScopeKey } = {}
) {
  const lockedPayload = queueSubmission(payload, queueScopeKey)
  const submissionId = String(lockedPayload?.client_submission_id || '')
  if (typeof onPayloadLocked === 'function') {
    onPayloadLocked({ ...lockedPayload })
  }
  let activeSubmission = null
  try {
    activeSubmission = runActiveSubmission(
      submissionId,
      () => submitAnswerResponsive(lockedPayload, onGraded)
    )
    const result = await activeSubmission.promise
    if (!activeSubmission.owner) return result
    const settlementStatus = trackSubmissionResult(submissionId, lockedPayload, result)
    if (settlementStatus === 'pending') {
      // Keep the durable answer queued: replaying this exact client id retries
      // only the idempotent adaptive update without creating another answer.
      const retry = markSubmissionForRetry(submissionId)
      if (!retry.paused) schedulePendingAnswerFlush(retry.delayMs, { queueScopeKey })
    } else if (settlementStatus === 'settled' || settlementStatus === 'migration') {
      removeSubmission(submissionId)
    } else {
      removeSubmission(submissionId)
    }
    return result
  } catch (error) {
    // A joiner observes the owner's network failure, but only the owner may
    // mutate retry metadata or schedule the replay. Otherwise one failed HTTP
    // request is counted once per caller and exponential backoff is inflated.
    if (activeSubmission?.owner === false) throw error
    if (isPermanentSubmissionError(error)) {
      removeSubmission(submissionId)
      publishSubmissionSettlement(submissionId, { status: 'terminal', error })
    } else if (isAdaptiveUpdatePendingError(error) || isRetryableSubmissionError(error)) {
      const retry = markSubmissionForRetry(submissionId)
      if (!retry.paused) schedulePendingAnswerFlush(retry.delayMs, { queueScopeKey })
    }
    // A 401 intentionally leaves the original owner-scoped payload queued
    // without an automatic retry loop. onShow will replay it after that same
    // user signs in again.
    throw error
  }
}

function normalizeRequestedScopeKey(queueScopeKey) {
  const normalized = String(queueScopeKey || '').trim()
  if (!normalized) return ''
  return normalized.startsWith('adaptive-session:')
    ? normalized
    : `adaptive-session:${normalized}`
}

export function flushPendingAnswerSubmissions({ queueScopeKey } = {}) {
  const targetScopeKey = normalizeRequestedScopeKey(queueScopeKey)
  if (targetScopeKey) {
    const existing = scopedFlushPromises.get(targetScopeKey)
    if (existing) {
      scopedFlushRequestedAfterCurrent.add(targetScopeKey)
      return existing
    }

    const scopedPromise = flushPendingAnswerSubmissionsUntilIdle(targetScopeKey).finally(() => {
      if (scopedFlushPromises.get(targetScopeKey) === scopedPromise) {
        scopedFlushPromises.delete(targetScopeKey)
      }
      scopedFlushRequestedAfterCurrent.delete(targetScopeKey)
    })
    scopedFlushPromises.set(targetScopeKey, scopedPromise)
    return scopedPromise
  }

  if (flushPromise) {
    flushRequestedAfterCurrent = true
    return flushPromise
  }

  flushPromise = flushPendingAnswerSubmissionsUntilIdle('').finally(() => {
    flushPromise = null
  })
  return flushPromise
}

async function flushPendingAnswerSubmissionsUntilIdle(targetScopeKey = '') {
  let result = { synced: 0, pending: countPendingSubmissions(targetScopeKey) }
  do {
    if (targetScopeKey) {
      scopedFlushRequestedAfterCurrent.delete(targetScopeKey)
    } else {
      flushRequestedAfterCurrent = false
    }
    const pass = await flushPendingAnswerSubmissionsOnce(targetScopeKey)
    result = {
      synced: result.synced + Number(pass?.synced || 0),
      pending: Number(pass?.pending || 0)
    }
  } while (
    targetScopeKey
      ? scopedFlushRequestedAfterCurrent.has(targetScopeKey)
      : flushRequestedAfterCurrent
  )
  return result
}

function countPendingSubmissions(targetScopeKey = '') {
  if (!targetScopeKey) return readQueue().length
  return readQueue().filter((entry) => (
    String(entry.scopeKey || adaptiveScopeKey(entry.payload) || '') === targetScopeKey
  )).length
}

async function flushPendingAnswerSubmissionsOnce(targetScopeKey = '') {
  const ownerId = currentOwnerId()
  if (!ownerId) return { synced: 0, pending: countPendingSubmissions(targetScopeKey) }

  let synced = 0
  let nextRetryDelay = null
  const blockedScopes = new Set()
  const queuedEntries = readQueue().sort((left, right) => (
    Number(left.queuedAt || 0) - Number(right.queuedAt || 0)
  ))
  for (const entry of queuedEntries) {
    const submissionId = String(entry.payload.client_submission_id || '')
    if (entry.ownerId !== ownerId) continue
    const scopeKey = String(entry.scopeKey || adaptiveScopeKey(entry.payload) || `submission:${submissionId}`)
    if (targetScopeKey && scopeKey !== targetScopeKey) continue
    if (blockedScopes.has(scopeKey)) continue
    if (activeSubmissionIds.has(submissionId)) {
      blockedScopes.add(scopeKey)
      continue
    }
    const waitMs = Number(entry.nextRetryAt || 0) - Date.now()
    if (waitMs > 0) {
      blockedScopes.add(scopeKey)
      nextRetryDelay = nextRetryDelay === null ? waitMs : Math.min(nextRetryDelay, waitMs)
      continue
    }

    let activeSubmission = null
    try {
      activeSubmission = runActiveSubmission(
        submissionId,
        () => submitAnswerDurably(entry.payload)
      )
      const result = await activeSubmission.promise
      if (!activeSubmission.owner) continue
      const settlementStatus = trackSubmissionResult(submissionId, entry.payload, result)
      if (settlementStatus === 'pending') {
        // Preserve ordering only inside this adaptive run. A failed update in
        // one subject/exam must not block unrelated practice submissions.
        blockedScopes.add(scopeKey)
        const retry = markSubmissionForRetry(submissionId)
        if (!retry.paused) {
          nextRetryDelay = nextRetryDelay === null
            ? retry.delayMs
            : Math.min(nextRetryDelay, retry.delayMs)
        }
        continue
      }
      if (settlementStatus === 'settled' || settlementStatus === 'migration') {
        removeSubmission(submissionId)
        synced += 1
      } else {
        removeSubmission(submissionId)
        continue
      }
    } catch (error) {
      // A scoped/global flush can join a foreground request for the same id.
      // The request owner alone advances backoff and publishes terminal state.
      if (activeSubmission?.owner === false) continue
      if (isAdaptiveUpdatePendingError(error)) {
        blockedScopes.add(scopeKey)
        const retry = markSubmissionForRetry(submissionId)
        if (!retry.paused) {
          nextRetryDelay = nextRetryDelay === null
            ? retry.delayMs
            : Math.min(nextRetryDelay, retry.delayMs)
        }
        continue
      }
      if (isPermanentSubmissionError(error)) {
        removeSubmission(submissionId)
        publishSubmissionSettlement(submissionId, { status: 'terminal', error })
        continue
      }
      blockedScopes.add(scopeKey)
      if (isDeferredAuthError(error) || !isRetryableSubmissionError(error)) {
        continue
      }
      const retry = markSubmissionForRetry(submissionId)
      if (!retry.paused) {
        nextRetryDelay = nextRetryDelay === null
          ? retry.delayMs
          : Math.min(nextRetryDelay, retry.delayMs)
      }
    }
  }

  if (nextRetryDelay !== null) {
    schedulePendingAnswerFlush(
      Math.max(100, nextRetryDelay),
      { queueScopeKey: targetScopeKey }
    )
  }

  return { synced, pending: countPendingSubmissions(targetScopeKey) }
}

export function schedulePendingAnswerFlush(delayMs = 1500, { queueScopeKey } = {}) {
  const normalizedDelay = Math.max(0, Number(delayMs || 0))
  const dueAt = Date.now() + normalizedDelay
  const targetScopeKey = normalizeRequestedScopeKey(queueScopeKey)
  if (targetScopeKey) {
    const existing = scheduledScopedFlushes.get(targetScopeKey)
    if (existing && existing.dueAt <= dueAt) return
    if (existing) clearTimeout(existing.timer)
    const timer = setTimeout(() => {
      if (scheduledScopedFlushes.get(targetScopeKey)?.timer === timer) {
        scheduledScopedFlushes.delete(targetScopeKey)
      }
      void flushPendingAnswerSubmissions({ queueScopeKey: targetScopeKey })
    }, normalizedDelay)
    scheduledScopedFlushes.set(targetScopeKey, { timer, dueAt })
    return
  }
  if (scheduledFlushTimer && scheduledFlushDueAt <= dueAt) {
    return
  }
  if (scheduledFlushTimer) clearTimeout(scheduledFlushTimer)
  scheduledFlushDueAt = dueAt
  scheduledFlushTimer = setTimeout(() => {
    scheduledFlushTimer = null
    scheduledFlushDueAt = 0
    void flushPendingAnswerSubmissions()
  }, normalizedDelay)
}
