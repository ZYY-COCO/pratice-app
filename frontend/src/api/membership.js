import { request } from './http'

export function fetchMembershipStatus() {
  return request({
    url: '/membership/status',
    method: 'GET'
  })
}
