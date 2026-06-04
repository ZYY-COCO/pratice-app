import { request } from './http'

export function fetchAdminMe() {
  return request({
    url: '/admin/me',
    method: 'GET'
  })
}

export function fetchAdminOverview() {
  return request({
    url: '/admin/overview',
    method: 'GET'
  })
}

export function fetchAdminUsers(params = {}) {
  return request({
    url: '/admin/users',
    method: 'GET',
    data: params
  })
}

export function grantAdminMembership(userId, payload) {
  return request({
    url: `/admin/users/${userId}/membership`,
    method: 'PATCH',
    data: payload
  })
}

export function cancelAdminMembership(userId) {
  return request({
    url: `/admin/users/${userId}/membership`,
    method: 'DELETE'
  })
}

export function fetchAdminUserDetail(userId) {
  return request({
    url: `/admin/users/${userId}`,
    method: 'GET'
  })
}

export function fetchAdminFeedback(params = {}) {
  return request({
    url: '/admin/feedback',
    method: 'GET',
    data: params
  })
}

export function updateAdminFeedbackStatus(feedbackId, payload) {
  return request({
    url: `/admin/feedback/${feedbackId}/status`,
    method: 'PATCH',
    data: payload
  })
}

export function fetchAdminQuestions(params = {}) {
  return request({
    url: '/admin/questions',
    method: 'GET',
    data: params
  })
}

export function fetchAdminQuestionDetail(questionId) {
  return request({
    url: `/admin/questions/${questionId}`,
    method: 'GET'
  })
}

export function updateAdminQuestionStatus(questionId, payload) {
  return request({
    url: `/admin/questions/${questionId}/status`,
    method: 'PATCH',
    data: payload
  })
}

export function updateAdminQuestion(questionId, payload) {
  return request({
    url: `/admin/questions/${questionId}`,
    method: 'PATCH',
    data: payload
  })
}

export function updateAdminQuestionReview(questionId, payload) {
  return request({
    url: `/admin/questions/${questionId}/review`,
    method: 'PATCH',
    data: payload
  })
}

export function bulkUpdateAdminQuestionStatus(payload) {
  return request({
    url: '/admin/questions/bulk-status',
    method: 'PATCH',
    data: payload
  })
}

export function fetchAdminMessages(params = {}) {
  return request({
    url: '/admin/messages',
    method: 'GET',
    data: params
  })
}

export function createAdminMessage(payload) {
  return request({
    url: '/admin/messages',
    method: 'POST',
    data: payload
  })
}

export function updateAdminMessage(messageId, payload) {
  return request({
    url: `/admin/messages/${messageId}`,
    method: 'PATCH',
    data: payload
  })
}
