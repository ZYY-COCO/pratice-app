import { request } from './http'

export function fetchMembershipStatus() {
  return request({
    url: '/membership/status',
    method: 'GET'
  })
}

export function fetchMembershipPlans() {
  return request({
    url: '/membership/plans',
    method: 'GET',
    authRedirect: false
  })
}

export function createMembershipOrder(payload) {
  return request({
    url: '/membership/orders',
    method: 'POST',
    data: payload
  })
}
