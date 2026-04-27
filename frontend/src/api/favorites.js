import { request } from './http'

function buildQuery(params = {}) {
  return Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')
}

export function fetchFavorites(params = {}) {
  const query = buildQuery(params)
  return request({
    url: query ? `/favorites?${query}` : '/favorites'
  })
}

export function fetchFavoriteStatus(questionId) {
  return request({
    url: `/favorites/status?question_id=${encodeURIComponent(questionId)}`
  })
}

export function toggleFavorite(questionId) {
  return request({
    url: '/favorites/toggle',
    method: 'POST',
    data: {
      question_id: questionId
    }
  })
}
