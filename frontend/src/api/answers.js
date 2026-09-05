import { request } from './http'

function buildQuery(params = {}) {
  return Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')
}

export function fetchAnswerHistory(params = {}) {
  const query = buildQuery(params)
  return request({
    url: query ? `/answers/history?${query}` : '/answers/history'
  })
}

export function fetchQuestionAbilityAccuracy(params = {}) {
  const query = buildQuery(params)
  return request({
    url: query ? `/answers/ability-accuracy?${query}` : '/answers/ability-accuracy'
  })
}

export function submitAnswerDurably(payload) {
  return request({
    url: '/answers/submit',
    method: 'POST',
    timeout: 25000,
    data: payload
  })
}

export function submitAnswerResponsive(payload, onGraded) {
  let gradeDelivered = false
  const deliverGrade = (grade) => {
    if (!grade || gradeDelivered || typeof onGraded !== 'function') return
    gradeDelivered = true
    onGraded(grade)
  }

  return request({
    url: '/answers/submit-responsive',
    method: 'POST',
    timeout: 25000,
    enableChunked: true,
    onHeadersReceived(response) {
      const grade = parseResponsiveGradeHeaders(response?.header || response?.headers || {})
      deliverGrade(grade)
    },
    data: payload
  }).then((result) => {
    assertResponsiveSubmissionPersisted(result)
    deliverGrade(parseResponsiveGradeResult(result))
    return result
  })
}

function assertResponsiveSubmissionPersisted(result) {
  if (result?.persisted === true) return

  throw Object.assign(
    new Error(result?.persistence_error || 'answer submission was not persisted'),
    {
      code: 'ANSWER_SUBMISSION_NOT_PERSISTED',
      statusCode: 503,
      retryable: result?.persistence_retryable !== false,
      result
    }
  )
}

function parseResponsiveGradeResult(result) {
  const correctAnswer = String(result?.correct_answer || '').trim().toUpperCase()
  if (!/^[ABCD]$/.test(correctAnswer)) return null
  return {
    questionId: String(result?.question_id || ''),
    correctAnswer,
    isCorrect: result?.is_correct === true,
    addedToWrongQuestions: result?.added_to_wrong_questions === true
  }
}

function parseResponsiveGradeHeaders(headers) {
  const normalized = Object.keys(headers || {}).reduce((result, key) => {
    result[String(key).toLowerCase()] = String(headers[key] ?? '')
    return result
  }, {})
  if (normalized['x-gyt-grading-ready'] !== '1') return null

  const correctAnswer = normalized['x-gyt-correct-answer']?.trim().toUpperCase()
  if (!/^[ABCD]$/.test(correctAnswer || '')) return null

  return {
    questionId: normalized['x-gyt-question-id'] || '',
    correctAnswer,
    isCorrect: normalized['x-gyt-is-correct'] === '1',
    addedToWrongQuestions: normalized['x-gyt-added-to-wrong-questions'] === '1'
  }
}

export function markQuestionUnfamiliar(payload) {
  return request({
    url: '/answers/mark-unfamiliar',
    method: 'POST',
    data: payload
  })
}
