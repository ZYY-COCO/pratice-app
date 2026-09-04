const VALID_ANSWERS = new Set(['A', 'B', 'C', 'D'])
const WARMUP_PHASES = new Set(['NEW', 'PROBING', 'VERIFYING'])

function contractError(message) {
  const error = new Error(message)
  error.code = 'ADAPTIVE_COMPREHENSIVE_CONTRACT_INVALID'
  error.statusCode = 503
  error.retryable = false
  return error
}

function requiredText(value, label) {
  const normalized = String(value || '').trim()
  if (!normalized) {
    throw contractError(`${label}缺失`)
  }
  return normalized
}

export function summarizeAdaptiveReviewResults(results) {
  const scored = Array.isArray(results)
    ? results.filter((item) => item?.skipped !== true)
    : []
  const correctCount = scored.filter((item) => item?.isCorrect === true).length
  const answeredCount = scored.length
  return {
    answeredCount,
    correctCount,
    accuracy: answeredCount ? Math.round((correctCount / answeredCount) * 100) : 0
  }
}

export function isAdaptiveWarmupSession({
  active,
  questionCount,
  diagnosticStatus,
  reliableFirstAttemptCount
}) {
  if (!active || Number(questionCount || 0) !== 8) return false
  const phase = String(diagnosticStatus || '').trim().toUpperCase()
  const hasReliableCount = reliableFirstAttemptCount !== null
    && reliableFirstAttemptCount !== undefined
    && Number.isFinite(Number(reliableFirstAttemptCount))
  return WARMUP_PHASES.has(phase) || (
    hasReliableCount && Number(reliableFirstAttemptCount) < 8
  )
}

export function normalizeAdaptiveComprehensiveItems(
  items,
  { sessionId = '', expectedCount = 0 } = {}
) {
  if (!Array.isArray(items) || !items.length) {
    throw contractError('综合刷题固定题单为空')
  }

  const normalizedSessionId = requiredText(sessionId, '综合刷题会话标识')
  const normalizedExpectedCount = Math.max(0, Number(expectedCount || 0))
  const sorted = [...items].sort((left, right) => Number(left?.position || 0) - Number(right?.position || 0))

  if (normalizedExpectedCount && sorted.length !== normalizedExpectedCount) {
    throw contractError(`综合刷题固定题单数量异常：${sorted.length}/${normalizedExpectedCount}`)
  }

  const itemIds = new Set()
  const questionIds = new Set()
  sorted.forEach((item, index) => {
    const itemId = requiredText(item?.id, `第 ${index + 1} 个题位标识`)
    const itemSessionId = requiredText(item?.session_id, `第 ${index + 1} 个题位会话标识`)
    const questionId = requiredText(item?.question?.id, `第 ${index + 1} 道题标识`)
    const position = Number(item?.position || 0)

    if (itemSessionId !== normalizedSessionId) {
      throw contractError('综合刷题题位与当前会话不一致')
    }
    if (position !== index + 1) {
      throw contractError('综合刷题题位顺序不连续')
    }
    if (itemIds.has(itemId)) {
      throw contractError('综合刷题题位重复')
    }
    if (questionIds.has(questionId)) {
      throw contractError('综合刷题中出现重复题目')
    }
    itemIds.add(itemId)
    questionIds.add(questionId)
  })

  return sorted
}

export function buildAdaptiveComprehensiveSubmissionPayload({
  sessionId,
  clientSubmissionId,
  questions,
  answersByQuestion,
  getQuestionSubmissionId,
  getUsedTime
}) {
  const normalizedSessionId = requiredText(sessionId, '综合刷题会话标识')
  const normalizedSubmissionId = requiredText(clientSubmissionId, '整卷提交标识')
  if (!Array.isArray(questions) || !questions.length) {
    throw contractError('综合刷题题单为空')
  }

  return {
    client_submission_id: normalizedSubmissionId,
    answers: questions.map((question, index) => {
      const questionKey = requiredText(question?.questionId || question?.id, `第 ${index + 1} 道题标识`)
      const itemId = requiredText(question?.adaptiveSessionItemId, `第 ${index + 1} 个题位标识`)
      const itemSessionId = requiredText(question?.adaptiveSessionId, `第 ${index + 1} 个题位会话标识`)
      const selectedAnswer = answersByQuestion?.[questionKey] ?? null

      if (itemSessionId !== normalizedSessionId) {
        throw contractError('综合刷题作答与当前会话不一致')
      }
      if (selectedAnswer !== null && !VALID_ANSWERS.has(selectedAnswer)) {
        throw contractError(`第 ${index + 1} 道题答案格式异常`)
      }

      return {
        practice_session_item_id: itemId,
        selected_answer: selectedAnswer,
        used_time: Math.min(86400, Math.max(0, Math.round(Number(getUsedTime(questionKey) || 0)))),
        client_submission_id: requiredText(
          getQuestionSubmissionId(questionKey),
          `第 ${index + 1} 道题提交标识`
        )
      }
    })
  }
}

export function mapAdaptiveComprehensiveResults(entries, results) {
  if (!Array.isArray(entries) || !entries.length || !Array.isArray(results)) {
    throw contractError('综合刷题批改结果格式异常')
  }

  const resultMap = new Map()
  results.forEach((result) => {
    const itemId = requiredText(result?.practice_session_item_id, '批改结果题位标识')
    if (resultMap.has(itemId)) {
      throw contractError('综合刷题批改结果重复')
    }
    resultMap.set(itemId, result)
  })

  if (resultMap.size !== entries.length) {
    throw contractError(`综合刷题批改结果数量异常：${resultMap.size}/${entries.length}`)
  }

  return entries.map(({ question, selected }, index) => {
    const itemId = requiredText(question?.adaptiveSessionItemId, `第 ${index + 1} 个题位标识`)
    const questionId = requiredText(question?.questionId || question?.id, `第 ${index + 1} 道题标识`)
    const result = resultMap.get(itemId)
    if (!result) {
      throw contractError(`第 ${index + 1} 道题缺少批改结果`)
    }
    if (String(result.question_id || '') !== questionId || Number(result.position || 0) !== index + 1) {
      throw contractError(`第 ${index + 1} 道题批改结果与固定题单不一致`)
    }

    const selectedAnswer = result.selected_answer ?? selected ?? ''
    return {
      question,
      selectedAnswer,
      correctAnswer: result.correct_answer || '',
      explanation: result.explanation || '',
      isCorrect: result.is_correct,
      skipped: selectedAnswer === '',
      syncFailed: false
    }
  })
}
