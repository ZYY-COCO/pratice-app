import { API_BASE_URL } from './config'
import { getRequestAccessToken, request } from './http'

function normalizeAiRequestError(error) {
  const message = error?.errMsg || ''

  if (message.includes('abort')) {
    return { detail: '已取消生成' }
  }

  if (message.includes('timeout')) {
    return { detail: 'AI 生成超时，请稍后重试' }
  }

  return { detail: message || '网络请求失败，请稍后重试' }
}

export function createAiTrainingRequestTask(data, handlers = {}) {
  let innerTask = null
  let aborted = false

  // Preserve the existing abortable API while refreshing a nearly expired
  // token before this long-running request is dispatched.
  getRequestAccessToken()
    .then((token) => {
      if (aborted) return

      innerTask = uni.request({
        url: `${API_BASE_URL}/ai/training/generate`,
        method: 'POST',
        timeout: 90000,
        data,
        header: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {})
        },
        success(response) {
          if (response.statusCode >= 200 && response.statusCode < 300) {
            handlers.success?.(response.data)
            return
          }
          handlers.fail?.(response.data || { detail: 'AI 训练生成失败' })
        },
        fail(error) {
          handlers.fail?.(normalizeAiRequestError(error))
        }
      })
    })
    .catch((error) => {
      if (!aborted) handlers.fail?.(error)
    })

  return {
    abort() {
      aborted = true
      innerTask?.abort?.()
    }
  }
}

export function generateAiTraining(data) {
  return new Promise((resolve, reject) => {
    createAiTrainingRequestTask(data, {
      success: resolve,
      fail: reject
    })
  })
}

export function fetchAiTrainingRecommendation(examCode, subject) {
  const params = [
    examCode ? `exam_code=${encodeURIComponent(examCode)}` : '',
    subject ? `subject=${encodeURIComponent(subject)}` : ''
  ].filter(Boolean)
  const query = params.length ? `?${params.join('&')}` : ''
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

export function aiQuestionChat(payload) {
  return request({
    url: '/ai/question-chat',
    method: 'POST',
    timeout: 30000,
    data: payload
  })
}
