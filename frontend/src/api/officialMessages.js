import { request } from './http'
import {
  readAfterNotificationMutations,
  trackNotificationRead
} from '../utils/notificationReadCoordinator'

export function fetchOfficialMessages() {
  return readAfterNotificationMutations(() => request({
    url: '/official-messages',
    method: 'GET',
    data: { _read_ts: Date.now() }
  }))
}

export function markOfficialMessageRead(messageId) {
  const normalizedId = String(messageId || '').trim()
  if (!normalizedId) return Promise.resolve({ ok: true })
  return trackNotificationRead(`official:${normalizedId}`, () => request({
    url: `/official-messages/${encodeURIComponent(normalizedId)}/read`,
    method: 'POST'
  }))
}
