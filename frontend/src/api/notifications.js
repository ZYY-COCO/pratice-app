import { request } from './http'
import {
  readAfterNotificationMutations,
  trackNotificationRead
} from '../utils/notificationReadCoordinator'

function freshReadParams(params = {}) {
  return {
    ...params,
    // 未读状态是强实时数据，避免 H5/WebView 复用同一个 GET 缓存响应。
    _read_ts: Date.now()
  }
}

export function fetchUserNotifications(params = {}) {
  return readAfterNotificationMutations(() => request({
    url: '/notifications',
    method: 'GET',
    data: freshReadParams(params)
  }))
}

export function fetchUserNotificationUnreadSummary() {
  return readAfterNotificationMutations(() => request({
    url: '/notifications/unread-summary',
    method: 'GET',
    data: freshReadParams()
  }))
}

export function markUserNotificationRead(notificationId) {
  const normalizedId = String(notificationId || '').trim()
  if (!normalizedId) return Promise.resolve({ ok: true, updated_count: 0 })
  return trackNotificationRead(`notification:${normalizedId}`, () => request({
    url: `/notifications/${encodeURIComponent(normalizedId)}/read`,
    method: 'POST',
    data: {}
  }))
}

export function markUserNotificationReadScope(scope) {
  const normalizedScope = String(scope || '').trim()
  return trackNotificationRead(`scope:${normalizedScope}`, () => request({
    url: '/notifications/read-scope',
    method: 'POST',
    data: { scope: normalizedScope }
  }))
}

export function markUserNotificationReadTarget(targetType, targetId) {
  const normalizedType = String(targetType || '').trim()
  const normalizedId = String(targetId || '').trim()
  if (!normalizedId) return Promise.resolve({ ok: true, updated_count: 0 })
  return trackNotificationRead(`target:${normalizedType}:${normalizedId}`, () => request({
    url: '/notifications/read-target',
    method: 'POST',
    data: {
      target_type: normalizedType,
      target_id: normalizedId
    }
  }))
}

export function markAllUserNotificationsRead() {
  return trackNotificationRead('all', () => request({
    url: '/notifications/read-all',
    method: 'POST',
    data: {}
  }))
}
