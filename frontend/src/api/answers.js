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
  const fallbackTimer = typeof onGraded === 'function'
    ? setTimeout(() => {
        if (gradeDelivered) return
        void request({
          url: '/answers/grade',
          method: 'POST',
          timeout: 6000,
          authRedirect: false,
          data: payload
        }).then((result) => {
          deliverGrade(parseResponsiveGradeResult(result))
        }).catch(() => {})
      }, 80)
    : null

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
    deliverGrade(parseResponsiveGradeResult(result))
    return result
  }).finally(() => {
    if (fallbackTimer) clearTimeout(fallbackTimer)
  })
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
