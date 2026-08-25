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

export function fetchSubscriptionPageConfig() {
  return request({
    url: '/membership/subscription-page-config',
    method: 'GET',
    authRedirect: false,
    header: { Authorization: '' }
  })
}

export function fetchAdminSubscriptionPageConfig() {
  return request({
    url: '/membership/admin/subscription-page-config',
    method: 'GET'
  })
}

export function updateAdminSubscriptionPageConfig(payload) {
  return request({
    url: '/membership/admin/subscription-page-config',
    method: 'PUT',
    data: payload
  })
}

export function createMembershipOrder(payload) {
  return request({
    url: '/membership/orders',
    method: 'POST',
    data: payload
  })
}
