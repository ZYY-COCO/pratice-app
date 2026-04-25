import { request } from './http'

function buildQuery(params = {}) {
  return Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')
}

export function fetchWrongQuestions(params = {}) {
  const query = buildQuery(params)
  return request({
    url: query ? `/wrong-questions?${query}` : '/wrong-questions'
  })
}

export function fetchWrongQuestionDetail(questionId) {
  return request({
    url: `/wrong-questions/${encodeURIComponent(questionId)}`
  })
}

export function reviewWrongQuestion(payload) {
  return request({
    url: '/wrong-questions/review',
    method: 'POST',
    data: payload
  })
}
