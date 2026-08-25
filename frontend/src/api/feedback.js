import { request } from './http'

export function submitBetaFeedback(payload) {
  return request({
    url: '/feedback/beta',
    method: 'POST',
    data: payload
  })
}

export function fetchMyFeedback(params = {}) {
  return request({
    url: '/feedback/me',
    method: 'GET',
    data: params
  })
}
