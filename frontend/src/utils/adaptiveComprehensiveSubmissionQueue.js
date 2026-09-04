const STORAGE_VERSION = 1
const STORAGE_KEY_PREFIX = 'adaptiveComprehensivePendingSubmissionsV1'
const VALID_ANSWERS = new Set(['A', 'B', 'C', 'D'])
const TERMINAL_ERROR_CODES = new Set([
  'ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT',
  'ADAPTIVE_PRACTICE_MODE_MISMATCH',
  'ADAPTIVE_COMPREHENSIVE_ROUND_INCOMPLETE',
  'ADAPTIVE_COMPREHENSIVE_ANSWERS_INCOMPLETE',
  'ADAPTIVE_COMPREHENSIVE_SNAPSHOT_SCOPE_MISMATCH'
])

function requiredText(value, label) {
  const normalized = String(value || '').trim()
  if (!normalized) throw queueError(`${label}缺失`, 'ADAPTIVE_COMPREHENSIVE_LOCAL_TASK_INVALID', false)
  return normalized
}

function queueError(message, code, retryable) {
  const error = new Error(message)
  error.code = code
  error.retryable = retryable
  return error
}

function persistenceError(error) {
  const wrapped = queueError(
    '交卷数据暂未保存到本机，请重试',
    'ADAPTIVE_COMPREHENSIVE_LOCAL_PERSISTENCE_FAILED',
    true
  )
  wrapped.cause = error
  return wrapped
}

function ownerChangedError() {
  return queueError(
    '登录账号已变更，已保留原账号的待续交整卷',
    'ADAPTIVE_COMPREHENSIVE_OWNER_CHANGED',
    true
  )
}

function normalizePayload(payload) {
  const clientSubmissionId = requiredText(payload?.client_submission_id, '整卷提交标识')
  if (!Array.isArray(payload?.answers) || !payload.answers.length) {
    throw queueError(
      '整卷作答清单为空',
      'ADAPTIVE_COMPREHENSIVE_LOCAL_TASK_INVALID',
      false
    )
  }

  const itemIds = new Set()
  const answerSubmissionIds = new Set()
  const answers = payload.answers.map((answer, index) => {
    const itemId = requiredText(answer?.practice_session_item_id, `第 ${index + 1} 个题位标识`)
    const answerSubmissionId = requiredText(answer?.client_submission_id, `第 ${index + 1} 道题提交标识`)
    const selectedAnswer = answer?.selected_answer ?? null
    const usedTime = Number(answer?.used_time)
    if (itemIds.has(itemId) || answerSubmissionIds.has(answerSubmissionId)) {
      throw queueError(
        '整卷作答清单包含重复标识',
        'ADAPTIVE_COMPREHENSIVE_LOCAL_TASK_INVALID',
        false
      )
    }
    if (selectedAnswer !== null && !VALID_ANSWERS.has(selectedAnswer)) {
      throw queueError(
        `第 ${index + 1} 道题答案格式异常`,
        'ADAPTIVE_COMPREHENSIVE_LOCAL_TASK_INVALID',
        false
      )
    }
    if (!Number.isFinite(usedTime)) {
      throw queueError(
        `第 ${index + 1} 道题用时异常`,
        'ADAPTIVE_COMPREHENSIVE_LOCAL_TASK_INVALID',
        false
      )
    }
    itemIds.add(itemId)
    answerSubmissionIds.add(answerSubmissionId)
    return Object.freeze({
      practice_session_item_id: itemId,
      selected_answer: selectedAnswer,
      used_time: Math.min(86400, Math.max(0, Math.round(usedTime))),
      client_submission_id: answerSubmissionId
    })
  })

  return Object.freeze({
    client_submission_id: clientSubmissionId,
    answers: Object.freeze(answers)
  })
}

function normalizeTask(task, expectedOwnerId = '') {
  const ownerUserId = requiredText(task?.ownerUserId, '交卷账号')
  if (expectedOwnerId && ownerUserId !== expectedOwnerId) return null
  const sessionId = requiredText(task?.sessionId, '综合刷题会话标识')
  const payload = normalizePayload(task?.payload)
  return Object.freeze({
    version: STORAGE_VERSION,
    ownerUserId,
    sessionId,
    payload,
    createdAt: Math.max(0, Number(task?.createdAt || Date.now())),
    updatedAt: Math.max(0, Number(task?.updatedAt || task?.createdAt || Date.now()))
  })
}

function payloadFingerprint(payload) {
  return JSON.stringify(payload)
}

function taskKey(task) {
  return [
    task.ownerUserId,
    task.sessionId,
    task.payload.client_submission_id
  ].join(':')
}

function errorCode(error) {
  return String(error?.detail?.code || error?.code || '').trim().toUpperCase()
}

function errorText(error) {
  if (typeof error === 'string') return error
  try {
    return JSON.stringify(error || '')
  } catch (serializationError) {
    return String(error?.detail || error?.message || error?.code || '')
  }
}

export function getAdaptiveComprehensiveSubmissionStorageKey(ownerUserId) {
  return `${STORAGE_KEY_PREFIX}:${encodeURIComponent(requiredText(ownerUserId, '交卷账号'))}`
}

export function isAdaptiveComprehensiveTerminalSubmissionError(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  const code = errorCode(error)
  if (TERMINAL_ERROR_CODES.has(code)) return true
  return statusCode === 404 && /ADAPTIVE_.+SESSION.+NOT_FOUND|个性化练习会话不存在/i.test(errorText(error))
}

export function isAdaptiveComprehensiveCompletedResponse(task, response) {
  let normalizedTask
  try {
    normalizedTask = normalizeTask(task)
  } catch (error) {
    return false
  }
  if (
    String(response?.session_id || '') !== normalizedTask.sessionId ||
    String(response?.status || '').trim().toLowerCase() !== 'completed' ||
    String(response?.reason || '').trim().toLowerCase() !== 'completed' ||
    response?.adaptive_settled !== true ||
    typeof response?.idempotent !== 'boolean'
  ) {
    return false
  }

  const results = response?.results
  const expectedAnswers = normalizedTask.payload.answers
  if (!Array.isArray(results) || results.length !== expectedAnswers.length) return false
  const expectedByItemId = new Map(
    expectedAnswers.map((answer, index) => [answer.practice_session_item_id, { answer, position: index + 1 }])
  )
  const seenItemIds = new Set()
  const seenPositions = new Set()
  for (const result of results) {
    const itemId = String(result?.practice_session_item_id || '').trim()
    const expected = expectedByItemId.get(itemId)
    const position = Number(result?.position)
    const selectedAnswer = result?.selected_answer ?? null
    const correctAnswer = String(result?.correct_answer || '').trim().toUpperCase()
    if (
      !expected ||
      seenItemIds.has(itemId) ||
      !Number.isInteger(position) ||
      position !== expected.position ||
      seenPositions.has(position) ||
      String(result?.question_id || '').trim() === '' ||
      selectedAnswer !== expected.answer.selected_answer ||
      !VALID_ANSWERS.has(correctAnswer) ||
      typeof result?.explanation !== 'string' ||
      (selectedAnswer === null ? result?.is_correct !== null : typeof result?.is_correct !== 'boolean')
    ) {
      return false
    }
    seenItemIds.add(itemId)
    seenPositions.add(position)
  }
  if (seenItemIds.size !== expectedByItemId.size) return false

  const answeredCount = expectedAnswers.filter((answer) => answer.selected_answer !== null).length
  const correctCount = results.filter((result) => result?.is_correct === true).length
  const summary = response?.summary
  if (
    !summary ||
    Number(summary.total_count) !== expectedAnswers.length ||
    Number(summary.answered_count) !== answeredCount ||
    Number(summary.correct_count) !== correctCount ||
    Number(summary.wrong_count) !== answeredCount - correctCount ||
    Number(summary.skipped_count) !== expectedAnswers.length - answeredCount ||
    Number(summary.used_time) !== expectedAnswers.reduce((total, answer) => total + answer.used_time, 0) ||
    !Number.isFinite(Number(summary.accuracy)) ||
    Number(summary.accuracy) < 0 ||
    Number(summary.accuracy) > 100
  ) {
    return false
  }

  const state = response?.state
  return Boolean(
    state &&
    Number.isFinite(Number(state.theta)) &&
    Number.isFinite(Number(state.uncertainty)) &&
    Number.isFinite(Number(state.effective_evidence)) &&
    Number.isInteger(Number(state.reliable_first_attempt_count)) &&
    Number(state.reliable_first_attempt_count) >= 0 &&
    String(state.diagnostic_status || '').trim() &&
    Number.isInteger(Number(state.pending_conflicts)) &&
    Number(state.pending_conflicts) >= 0 &&
    String(state.confidence_label || '').trim() &&
    String(state.initial_level_range || '').trim()
  )
}

export function createAdaptiveComprehensiveSubmissionQueue({
  storage,
  getOwnerId,
  submit
}) {
  if (!storage || typeof storage.getStorageSync !== 'function' || typeof storage.setStorageSync !== 'function') {
    throw new Error('adaptive comprehensive submission storage is unavailable')
  }
  if (typeof getOwnerId !== 'function' || typeof submit !== 'function') {
    throw new Error('adaptive comprehensive submission queue dependencies are incomplete')
  }

  const activeSubmissions = new Map()
  const activeOwnerFlushes = new Map()

  function currentOwnerId() {
    return String(getOwnerId() || '').trim()
  }

  function readOwnerTasks(ownerUserId) {
    const normalizedOwnerId = requiredText(ownerUserId, '交卷账号')
    let stored
    try {
      stored = storage.getStorageSync(
        getAdaptiveComprehensiveSubmissionStorageKey(normalizedOwnerId)
      )
    } catch (error) {
      throw persistenceError(error)
    }
    if (!stored) return []
    if (
      Number(stored?.version || 0) !== STORAGE_VERSION ||
      String(stored?.ownerUserId || '') !== normalizedOwnerId ||
      !Array.isArray(stored?.tasks)
    ) {
      throw persistenceError(new Error('adaptive comprehensive submission bucket is invalid'))
    }

    const tasks = []
    for (const value of stored.tasks) {
      try {
        const task = normalizeTask(value, normalizedOwnerId)
        if (task) tasks.push(task)
      } catch (error) {
        // Keep malformed storage untouched. Valid tasks remain recoverable and a
        // later successful rewrite only happens after an explicit persist/remove.
      }
    }
    return tasks
  }

  function writeOwnerTasks(ownerUserId, tasks) {
    const normalizedOwnerId = requiredText(ownerUserId, '交卷账号')
    const storageKey = getAdaptiveComprehensiveSubmissionStorageKey(normalizedOwnerId)
    try {
      if (tasks.length) {
        storage.setStorageSync(storageKey, {
          version: STORAGE_VERSION,
          ownerUserId: normalizedOwnerId,
          tasks
        })
      } else if (typeof storage.removeStorageSync === 'function') {
        storage.removeStorageSync(storageKey)
      } else {
        storage.setStorageSync(storageKey, null)
      }
    } catch (error) {
      throw persistenceError(error)
    }
  }

  function list() {
    const ownerUserId = currentOwnerId()
    if (!ownerUserId) return []
    return readOwnerTasks(ownerUserId)
      .slice()
      .sort((left, right) => left.createdAt - right.createdAt)
  }

  function persist({ sessionId, payload }) {
    const ownerUserId = currentOwnerId()
    if (!ownerUserId) throw ownerChangedError()
    const now = Date.now()
    const candidate = normalizeTask({
      ownerUserId,
      sessionId,
      payload,
      createdAt: now,
      updatedAt: now
    }, ownerUserId)
    const tasks = readOwnerTasks(ownerUserId)
    const existing = tasks.find((task) => task.sessionId === candidate.sessionId)
    if (existing) {
      // The first durable manifest candidate is authoritative. It may already
      // be LOCKED server-side even if the corresponding response was lost.
      return existing
    }

    writeOwnerTasks(ownerUserId, [...tasks, candidate])
    const verified = readOwnerTasks(ownerUserId).find((task) => (
      task.sessionId === candidate.sessionId &&
      task.payload.client_submission_id === candidate.payload.client_submission_id &&
      payloadFingerprint(task.payload) === payloadFingerprint(candidate.payload)
    ))
    if (!verified) {
      throw persistenceError(new Error('adaptive comprehensive submission write verification failed'))
    }
    return verified
  }

  function remove(task) {
    const normalizedTask = normalizeTask(task)
    if (currentOwnerId() !== normalizedTask.ownerUserId) return false
    const tasks = readOwnerTasks(normalizedTask.ownerUserId)
    const retained = tasks.filter((candidate) => taskKey(candidate) !== taskKey(normalizedTask))
    if (retained.length === tasks.length) return true
    writeOwnerTasks(normalizedTask.ownerUserId, retained)
    return !readOwnerTasks(normalizedTask.ownerUserId)
      .some((candidate) => taskKey(candidate) === taskKey(normalizedTask))
  }

  function submitTask(task) {
    const normalizedTask = normalizeTask(task)
    if (currentOwnerId() !== normalizedTask.ownerUserId) {
      return Promise.reject(ownerChangedError())
    }
    const key = taskKey(normalizedTask)
    const existing = activeSubmissions.get(key)
    if (existing) return existing

    const promise = Promise.resolve()
      .then(() => {
        if (currentOwnerId() !== normalizedTask.ownerUserId) throw ownerChangedError()
        return submit(normalizedTask.sessionId, normalizedTask.payload)
      })
      .then((response) => {
        if (currentOwnerId() !== normalizedTask.ownerUserId) throw ownerChangedError()
        return response
      })
      .finally(() => {
        if (activeSubmissions.get(key) === promise) activeSubmissions.delete(key)
      })
    activeSubmissions.set(key, promise)
    return promise
  }

  async function resumeTask(task) {
    const normalizedTask = normalizeTask(task)
    if (currentOwnerId() !== normalizedTask.ownerUserId) {
      return { status: 'retained', reason: 'owner_changed', task: normalizedTask }
    }
    try {
      const response = await submitTask(normalizedTask)
      if (!isAdaptiveComprehensiveCompletedResponse(normalizedTask, response)) {
        return { status: 'retained', reason: 'not_completed', task: normalizedTask, response }
      }
      if (currentOwnerId() !== normalizedTask.ownerUserId) {
        return { status: 'retained', reason: 'owner_changed', task: normalizedTask, response }
      }
      try {
        const removed = remove(normalizedTask)
        return {
          status: removed ? 'completed' : 'retained',
          reason: removed ? 'confirmed_completed' : 'local_remove_failed',
          task: normalizedTask,
          response
        }
      } catch (error) {
        return { status: 'retained', reason: 'local_remove_failed', task: normalizedTask, response, error }
      }
    } catch (error) {
      if (
        currentOwnerId() === normalizedTask.ownerUserId &&
        isAdaptiveComprehensiveTerminalSubmissionError(error)
      ) {
        try {
          const removed = remove(normalizedTask)
          return {
            status: removed ? 'terminal' : 'retained',
            reason: removed ? 'terminal_error' : 'local_remove_failed',
            task: normalizedTask,
            error
          }
        } catch (removeError) {
          return {
            status: 'retained',
            reason: 'local_remove_failed',
            task: normalizedTask,
            error,
            removeError
          }
        }
      }
      return { status: 'retained', reason: 'retryable_or_unknown_error', task: normalizedTask, error }
    }
  }

  function resumeAll() {
    const ownerUserId = currentOwnerId()
    if (!ownerUserId) return Promise.resolve([])
    const existing = activeOwnerFlushes.get(ownerUserId)
    if (existing) return existing

    const promise = (async () => {
      const outcomes = []
      for (const task of list()) {
        if (currentOwnerId() !== ownerUserId) break
        outcomes.push(await resumeTask(task))
      }
      return outcomes
    })().finally(() => {
      if (activeOwnerFlushes.get(ownerUserId) === promise) {
        activeOwnerFlushes.delete(ownerUserId)
      }
    })
    activeOwnerFlushes.set(ownerUserId, promise)
    return promise
  }

  return Object.freeze({
    list,
    persist,
    remove,
    submit: submitTask,
    resumeAll
  })
}
