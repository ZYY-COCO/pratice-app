import { request, uploadFileRequest } from './http'

export function fetchAdminMe() {
  return request({
    url: '/admin/me',
    method: 'GET'
  })
}

export function fetchQuestionAdminPortalMe() {
  return request({
    url: '/admin/question-portal/me',
    method: 'GET',
    authRedirect: false
  })
}

export function fetchQuestionAdminDashboard(params = {}) {
  return request({
    url: '/admin/question-portal/dashboard',
    method: 'GET',
    data: params
  })
}

export function fetchAdminQuestionBanks() {
  return request({
    url: '/admin/question-banks',
    method: 'GET'
  })
}

export function createAdminQuestionBank(payload) {
  return request({
    url: '/admin/question-banks',
    method: 'POST',
    data: payload
  })
}

export function renameAdminQuestionBank(questionBankId, payload) {
  return request({
    url: `/admin/question-banks/${questionBankId}`,
    method: 'PATCH',
    data: payload
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

export function createAdminQuestion(payload) {
  return request({
    url: '/admin/questions',
    method: 'POST',
    data: payload
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

export function dryRunAdminQuestionImageImport(payload) {
  return request({
    url: '/admin/questions/image-import/dry-run',
    method: 'POST',
    data: payload,
    timeout: 30000
  })
}

export function commitAdminQuestionImageImport(payload) {
  return request({
    url: '/admin/questions/image-import/commit',
    method: 'POST',
    data: payload,
    timeout: 45000
  })
}

export function recognizeAdminQuestionImportFile(payload) {
  return uploadFileRequest({
    url: '/admin/questions/image-import/recognize',
    file: payload.file,
    filePath: payload.filePath,
    fileName: payload.fileName,
    name: 'file',
    timeout: 90000
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
