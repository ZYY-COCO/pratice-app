import { request, uploadFileRequest } from './http'

export function fetchMentorProfiles(params = {}) {
  return request({
    url: '/mentor-consultation/mentors',
    method: 'GET',
    data: params,
    header: { Authorization: '' },
    authRedirect: false
  })
}

export function fetchMentorProfile(mentorId) {
  return request({
    url: `/mentor-consultation/mentors/${encodeURIComponent(mentorId)}`,
    method: 'GET',
    header: { Authorization: '' },
    authRedirect: false
  })
}

export function fetchMyMentorVerificationApplication() {
  return request({
    url: '/mentor-consultation/me/verification-application',
    method: 'GET'
  })
}

export function fetchMyMentorProfile() {
  return request({
    url: '/mentor-consultation/me/mentor-profile',
    method: 'GET'
  })
}

export function fetchMyMentorProfileChangeRequest() {
  return request({
    url: '/mentor-consultation/me/mentor-profile/change-request',
    method: 'GET'
  })
}

export function createMyMentorProfileChangeRequest(payload) {
  return request({
    url: '/mentor-consultation/me/mentor-profile/change-request',
    method: 'POST',
    data: payload
  })
}

export function updateMyMentorAvailability(onlineStatus) {
  return request({
    url: '/mentor-consultation/me/mentor-profile/availability',
    method: 'PATCH',
    data: { online_status: onlineStatus }
  })
}

export function fetchMyMentorAvailabilitySlots(params = {}) {
  return request({
    url: '/mentor-consultation/me/mentor-slots',
    method: 'GET',
    data: params
  })
}

export function createMyMentorAvailabilitySlot(payload) {
  return request({
    url: '/mentor-consultation/me/mentor-slots',
    method: 'POST',
    data: payload
  })
}

export function updateMyMentorAvailabilitySlot(slotId, payload) {
  return request({
    url: `/mentor-consultation/me/mentor-slots/${encodeURIComponent(slotId)}`,
    method: 'PATCH',
    data: payload
  })
}

export function fetchMyReceivedMentorOrders(params = {}) {
  return request({
    url: '/mentor-consultation/me/mentor-orders',
    method: 'GET',
    data: params
  })
}

export function createMentorVerificationApplication(payload) {
  return request({
    url: '/mentor-consultation/verification-applications',
    method: 'POST',
    data: payload
  })
}

export function uploadMentorVerificationDocument(applicationId, { path, filePath, file, fileName } = {}) {
  return uploadFileRequest({
    url: `/mentor-consultation/verification-applications/${encodeURIComponent(applicationId)}/documents`,
    filePath: filePath || path,
    file,
    fileName,
    name: 'file',
    timeout: 120000
  })
}

export function fetchMyMentorFavorites() {
  return request({
    url: '/mentor-consultation/me/favorites',
    method: 'GET'
  })
}

export function toggleMentorFavoriteRequest(mentorId) {
  return request({
    url: `/mentor-consultation/mentors/${encodeURIComponent(mentorId)}/favorite`,
    method: 'POST',
    data: {}
  })
}

export function createMentorConsultationOrder(payload) {
  return request({
    url: '/mentor-consultation/orders',
    method: 'POST',
    data: payload
  })
}

export function fetchMentorConsultationPaymentCapability() {
  return request({
    url: '/mentor-consultation/payment-capability',
    method: 'GET',
    header: { Authorization: '' },
    authRedirect: false
  })
}

// 仅由本地开发态的免支付确认调用；服务端仍要求显式开启本地开关。
export function confirmMentorConsultationLocalRehearsal(orderId) {
  return request({
    url: `/mentor-consultation/orders/${encodeURIComponent(orderId)}/mock-pay`,
    method: 'POST',
    data: {}
  })
}

export function createMentorConsultationPaymentIntent(orderId) {
  return request({
    url: `/mentor-consultation/orders/${encodeURIComponent(orderId)}/payment-intent`,
    method: 'POST',
    data: {}
  })
}

export function cancelMentorConsultationOrder(orderId) {
  return request({
    url: `/mentor-consultation/orders/${encodeURIComponent(orderId)}/cancel`,
    method: 'POST',
    data: {}
  })
}

export function fetchMyMentorConsultationOrders(params = {}) {
  return request({
    url: '/mentor-consultation/me/orders',
    method: 'GET',
    data: params
  })
}

export function fetchMentorConsultationOrder(orderId) {
  return request({
    url: `/mentor-consultation/orders/${encodeURIComponent(orderId)}`,
    method: 'GET'
  })
}

export function decideMentorConsultationOrder(orderId, decision, reason = '') {
  return request({
    url: `/mentor-consultation/orders/${encodeURIComponent(orderId)}/decision`,
    method: 'POST',
    data: { decision, reason: String(reason || '').trim() }
  })
}

export function startMentorConsultationOrder(orderId) {
  return request({
    url: `/mentor-consultation/orders/${encodeURIComponent(orderId)}/start`,
    method: 'POST',
    data: {}
  })
}

export function completeMentorConsultationOrder(orderId) {
  return request({
    url: `/mentor-consultation/orders/${encodeURIComponent(orderId)}/complete`,
    method: 'POST',
    data: {}
  })
}

// 仅由本地开发态的免支付流程调用，自动完成双方结束确认。
export function completeMentorConsultationLocalRehearsal(orderId) {
  return request({
    url: `/mentor-consultation/orders/${encodeURIComponent(orderId)}/local-rehearsal-complete`,
    method: 'POST',
    data: {}
  })
}

export function fetchMentorConsultationMessages(orderId, params = {}) {
  return request({
    url: `/mentor-consultation/orders/${encodeURIComponent(orderId)}/messages`,
    method: 'GET',
    data: params,
    timeout: 6500
  })
}

export function createMentorConsultationMessage(orderId, payload) {
  return request({
    url: `/mentor-consultation/orders/${encodeURIComponent(orderId)}/messages`,
    method: 'POST',
    data: payload,
    timeout: 8000
  })
}

export function createMentorConsultationReview(orderId, payload) {
  return request({
    url: `/mentor-consultation/orders/${encodeURIComponent(orderId)}/review`,
    method: 'POST',
    data: payload
  })
}

export function createMentorConsultationReport(orderId, payload) {
  return request({
    url: `/mentor-consultation/orders/${encodeURIComponent(orderId)}/reports`,
    method: 'POST',
    data: payload,
    timeout: 20000
  })
}

export function fetchMyMentorConsultationReports(params = {}) {
  return request({
    url: '/mentor-consultation/me/reports',
    method: 'GET',
    data: params
  })
}

export function fetchMyMentorConsultationReportAppeals(params = {}) {
  return request({
    url: '/mentor-consultation/me/report-appeals',
    method: 'GET',
    data: params
  })
}

export function respondToMentorConsultationReport(reportId, payload) {
  return request({
    url: `/mentor-consultation/reports/${encodeURIComponent(reportId)}/response`,
    method: 'POST',
    data: payload,
    timeout: 20000
  })
}

export function uploadMentorConsultationReportEvidence(reportId, { filePath, file, fileName }) {
  return uploadFileRequest({
    url: `/mentor-consultation/reports/${encodeURIComponent(reportId)}/evidence`,
    filePath,
    file,
    fileName,
    name: 'file',
    timeout: 120000
  })
}

export function createMentorConsultationReportAppeal(reportId, payload) {
  return request({
    url: `/mentor-consultation/reports/${encodeURIComponent(reportId)}/appeals`,
    method: 'POST',
    data: payload,
    timeout: 20000
  })
}

export function uploadMentorConsultationReportAppealEvidence(appealId, { filePath, file, fileName }) {
  return uploadFileRequest({
    url: `/mentor-consultation/report-appeals/${encodeURIComponent(appealId)}/evidence`,
    filePath,
    file,
    fileName,
    name: 'file',
    timeout: 120000
  })
}
