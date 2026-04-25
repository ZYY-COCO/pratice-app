import { request } from './http'

export function submitBetaFeedback(payload) {
  return request({
    url: '/feedback/beta',
    method: 'POST',
    data: payload
  })
}
