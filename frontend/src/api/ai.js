import { request } from './http'

export function generateAiTraining(data) {
  return request({
    url: '/ai/training/generate',
    method: 'POST',
    timeout: 90000,
    data
  })
}

export function fetchAiTrainingRecommendation(examCode) {
  const query = examCode ? `?exam_code=${encodeURIComponent(examCode)}` : ''
  return request({
    url: `/ai/training/recommendation${query}`,
    timeout: 30000
  })
}

export function fetchAiTrainingSession(sessionId) {
  return request({
    url: `/ai/training/sessions/${encodeURIComponent(sessionId)}`,
    timeout: 30000
  })
}

export function fetchAiTrainingSummary(sessionId) {
  return request({
    url: `/ai/training/sessions/${encodeURIComponent(sessionId)}/summary`,
    timeout: 30000
  })
}
