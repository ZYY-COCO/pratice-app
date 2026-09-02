import { submitAnswerDurably, submitAnswerResponsive } from '../api/answers'
import { getAuthUser } from './auth'

const STORAGE_KEY = 'pendingAnswerSubmissionsV1'
const MAX_PENDING_SUBMISSIONS = 200
const activeSubmissionIds = new Set()
let flushPromise = null
let scheduledFlushTimer = null

function readQueue() {
  const stored = uni.getStorageSync(STORAGE_KEY)
  if (!Array.isArray(stored)) return []
  return stored.filter((item) => item?.payload?.client_submission_id)
}

function writeQueue(items) {
  if (items.length) {
    uni.setStorageSync(STORAGE_KEY, items.slice(-MAX_PENDING_SUBMISSIONS))
  } else {
    uni.removeStorageSync(STORAGE_KEY)
  }
}

function currentOwnerId() {
  return String(getAuthUser()?.id || '')
}

function queueSubmission(payload) {
  const submissionId = String(payload?.client_submission_id || '')
  if (!submissionId) return

  const queue = readQueue()
  const existingIndex = queue.findIndex((item) => item.payload.client_submission_id === submissionId)
  const entry = {
    ownerId: currentOwnerId(),
    payload: { ...payload },
    queuedAt: Date.now()
  }
  if (existingIndex >= 0) {
    queue.splice(existingIndex, 1, entry)
  } else {
    queue.push(entry)
  }
  writeQueue(queue)
}

function removeSubmission(submissionId) {
  const normalizedId = String(submissionId || '')
  if (!normalizedId) return
  writeQueue(readQueue().filter((item) => item.payload.client_submission_id !== normalizedId))
}

export async function submitAnswerWithReliableSync(payload, { onGraded } = {}) {
  const submissionId = String(payload?.client_submission_id || '')
  queueSubmission(payload)
  if (submissionId) activeSubmissionIds.add(submissionId)

  try {
    const result = await submitAnswerResponsive(payload, onGraded)
    if (result?.persisted === true) {
      removeSubmission(submissionId)
    } else if (result?.persistence_retryable === false) {
      removeSubmission(submissionId)
    }
    return result
  } finally {
    activeSubmissionIds.delete(submissionId)
  }
}

export function flushPendingAnswerSubmissions() {
  if (flushPromise) return flushPromise

  flushPromise = flushPendingAnswerSubmissionsOnce().finally(() => {
    flushPromise = null
  })
  return flushPromise
}

async function flushPendingAnswerSubmissionsOnce() {
  const ownerId = currentOwnerId()
  if (!ownerId) return { synced: 0, pending: readQueue().length }

  let synced = 0
  for (const entry of readQueue()) {
    const submissionId = String(entry.payload.client_submission_id || '')
    if (entry.ownerId !== ownerId || activeSubmissionIds.has(submissionId)) continue

    activeSubmissionIds.add(submissionId)
    try {
      const result = await submitAnswerDurably(entry.payload)
      if (result?.persisted !== false) {
        removeSubmission(submissionId)
        synced += 1
      }
    } catch (error) {
      if (error?.retryable === false && [400, 404, 409, 422].includes(Number(error?.statusCode))) {
        removeSubmission(submissionId)
      }
      break
    } finally {
      activeSubmissionIds.delete(submissionId)
    }
  }

  return { synced, pending: readQueue().length }
}

export function schedulePendingAnswerFlush(delayMs = 1500) {
  if (scheduledFlushTimer) clearTimeout(scheduledFlushTimer)
  scheduledFlushTimer = setTimeout(() => {
    scheduledFlushTimer = null
    void flushPendingAnswerSubmissions()
  }, Math.max(0, Number(delayMs || 0)))
}
