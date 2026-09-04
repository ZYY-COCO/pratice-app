import { request } from './http'

function encodePathSegment(value) {
  return encodeURIComponent(String(value || ''))
}

export function createAdaptivePracticeSession(payload) {
  return request({
    url: '/adaptive-practice/sessions',
    method: 'POST',
    timeout: 20000,
    data: payload
  })
}

export function fetchNextAdaptivePracticeItem(sessionId) {
  return request({
    url: `/adaptive-practice/sessions/${encodePathSegment(sessionId)}/next`,
    timeout: 8000,
    retryTransientRead: false
  })
}

export function submitAdaptiveComprehensivePracticeSession(sessionId, payload) {
  return request({
    url: `/adaptive-practice/sessions/${encodePathSegment(sessionId)}/submit`,
    method: 'POST',
    timeout: 30000,
    data: payload
  })
}

export function recordAdaptivePracticeItemEvent(sessionId, itemId, eventType) {
  return request({
    url: `/adaptive-practice/sessions/${encodePathSegment(sessionId)}/items/${encodePathSegment(itemId)}/events`,
    method: 'POST',
    timeout: 12000,
    authRedirect: false,
    data: {
      event_type: eventType
    }
  })
}

export function completeAdaptivePracticeSession(sessionId, reason = 'completed') {
  return request({
    url: `/adaptive-practice/sessions/${encodePathSegment(sessionId)}/complete`,
    method: 'POST',
    timeout: 15000,
    authRedirect: false,
    data: {
      reason
    }
  })
}
