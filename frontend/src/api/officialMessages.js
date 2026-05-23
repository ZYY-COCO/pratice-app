import { request } from './http'

export function fetchOfficialMessages() {
  return request({
    url: '/official-messages',
    method: 'GET'
  })
}

export function markOfficialMessageRead(messageId) {
  return request({
    url: `/official-messages/${messageId}/read`,
    method: 'POST'
  })
}
