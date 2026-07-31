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

export function markQuestionUnfamiliar(payload) {
  return request({
    url: '/answers/mark-unfamiliar',
    method: 'POST',
    data: payload
  })
}
