import { request } from './http'

export function fetchUserNotifications(params = {}) {
  return request({
    url: '/notifications',
    method: 'GET',
    data: params
  })
}

export function fetchUserNotificationUnreadSummary() {
  return request({
    url: '/notifications/unread-summary',
    method: 'GET'
  })
}

export function markUserNotificationRead(notificationId) {
  return request({
    url: `/notifications/${encodeURIComponent(notificationId)}/read`,
    method: 'POST',
    data: {}
  })
}

export function markUserNotificationReadScope(scope) {
  return request({
    url: '/notifications/read-scope',
    method: 'POST',
    data: { scope }
  })
}

export function markUserNotificationReadTarget(targetType, targetId) {
  return request({
    url: '/notifications/read-target',
    method: 'POST',
    data: {
      target_type: targetType,
      target_id: targetId
    }
  })
}
