import { request } from './http'

export function generateAiTraining(data) {
  return request({
    url: '/ai/training/generate',
    method: 'POST',
    timeout: 90000,
    data
  })
}

export function fetchAiTrainingSession(sessionId) {
  return request({
    url: `/ai/training/sessions/${encodeURIComponent(sessionId)}`,
    timeout: 30000
  })
}
