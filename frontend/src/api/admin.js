import { request, uploadFileRequest } from './http'

export function fetchAdminMe() {
  return request({
    url: '/admin/me',
    method: 'GET',
    timeout: 20000
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

export function fetchQuestionAdminOperationsOverview() {
  return request({
    url: '/admin/question-portal/operations/overview',
    method: 'GET'
  })
}

export function fetchQuestionAdminPortalUsers(params = {}) {
  return request({
    url: '/admin/question-portal/users',
    method: 'GET',
    data: params
  })
}

export function fetchQuestionAdminPortalUserDetail(userId) {
  return request({
    url: `/admin/question-portal/users/${encodeURIComponent(userId)}`,
    method: 'GET'
  })
}

export function updateQuestionAdminPortalUserDisabled(userId, payload) {
  return request({
    url: `/admin/question-portal/users/${encodeURIComponent(userId)}/disabled`,
    method: 'PATCH',
    data: payload
  })
}

export function renewQuestionAdminPortalUserMembership(userId, payload) {
  return request({
    url: `/admin/question-portal/users/${encodeURIComponent(userId)}/membership`,
    method: 'PATCH',
    data: payload
  })
}

export function cancelQuestionAdminPortalUserMembership(userId) {
  return request({
    url: `/admin/question-portal/users/${encodeURIComponent(userId)}/membership`,
    method: 'DELETE'
  })
}

export function previewQuestionAdminAdmissionImport(dataset, payload) {
  return uploadFileRequest({
    url: `/admin/question-portal/admission/${encodeURIComponent(dataset)}/preview`,
    file: payload.file,
    filePath: payload.filePath,
    fileName: payload.fileName,
    name: 'file',
    timeout: 60000
  })
}

export function commitQuestionAdminAdmissionImport(dataset, payload) {
  return uploadFileRequest({
    url: `/admin/question-portal/admission/${encodeURIComponent(dataset)}/commit`,
    file: payload.file,
    filePath: payload.filePath,
    fileName: payload.fileName,
    name: 'file',
    timeout: 90000
  })
}

export function fetchQuestionAdminAdmissionRuns(dataset, params = {}) {
  return request({
    url: `/admin/question-portal/admission/${encodeURIComponent(dataset)}/runs`,
    method: 'GET',
    data: params
  })
}

export function publishQuestionAdminAdmissionRun(dataset, runId) {
  return request({
    url: `/admin/question-portal/admission/${encodeURIComponent(dataset)}/runs/${encodeURIComponent(runId)}/publish`,
    method: 'POST'
  })
}

export function bootstrapQuestionAdminScorelines(payload) {
  return request({
    url: '/admin/question-portal/admission/scorelines/bootstrap',
    method: 'POST',
    data: payload,
    timeout: 90000
  })
}

export function bootstrapQuestionAdminAdmissionSnapshot(dataset) {
  return request({
    url: `/admin/question-portal/admission/${encodeURIComponent(dataset)}/bootstrap`,
    method: 'POST',
    timeout: 180000
  })
}

export function fetchQuestionAdminScorelineRecords(params = {}) {
  return request({
    url: '/admin/question-portal/admission/scorelines/records',
    method: 'GET',
    data: params
  })
}

export function updateQuestionAdminScorelineRecord(recordId, payload) {
  return request({
    url: `/admin/question-portal/admission/scorelines/records/${encodeURIComponent(recordId)}`,
    method: 'PATCH',
    data: payload
  })
}

export function fetchQuestionAdminMajorCatalogRecords(params = {}) {
  return request({
    url: '/admin/question-portal/admission/major-catalog/records',
    method: 'GET',
    data: params
  })
}

export function updateQuestionAdminMajorCatalogRecord(recordId, payload) {
  return request({
    url: `/admin/question-portal/admission/major-catalog/records/${encodeURIComponent(recordId)}`,
    method: 'PATCH',
    data: payload,
    timeout: 90000
  })
}

export function fetchQuestionAdminAnnouncementRecords(params = {}) {
  return request({
    url: '/admin/question-portal/admission/announcements/records',
    method: 'GET',
    data: params
  })
}

export function updateQuestionAdminAnnouncementRecord(recordId, payload) {
  return request({
    url: `/admin/question-portal/admission/announcements/records/${encodeURIComponent(recordId)}`,
    method: 'PATCH',
    data: payload
  })
}

export function fetchQuestionAdminHomeContent(params = {}) {
  return request({
    url: '/admin/question-portal/home-content',
    method: 'GET',
    data: params
  })
}

export function createQuestionAdminHomeContent(payload) {
  return request({
    url: '/admin/question-portal/home-content',
    method: 'POST',
    data: payload
  })
}

export function updateQuestionAdminHomeContent(contentId, payload) {
  return request({
    url: `/admin/question-portal/home-content/${encodeURIComponent(contentId)}`,
    method: 'PATCH',
    data: payload
  })
}

export function fetchQuestionAdminCommunityOverview() {
  return request({
    url: '/admin/question-portal/community/overview',
    method: 'GET'
  })
}

export function fetchQuestionAdminCommunityPosts(params = {}) {
  return request({
    url: '/admin/question-portal/community/posts',
    method: 'GET',
    data: params
  })
}

export function fetchQuestionAdminCommunityPostDetail(postId) {
  return request({
    url: `/admin/question-portal/community/posts/${encodeURIComponent(postId)}`,
    method: 'GET'
  })
}

export function updateQuestionAdminCommunityPostVisibility(postId, payload) {
  return request({
    url: `/admin/question-portal/community/posts/${encodeURIComponent(postId)}/visibility`,
    method: 'PATCH',
    data: payload
  })
}

export function updateQuestionAdminCommunityCommentVisibility(postId, commentId, payload) {
  return request({
    url: `/admin/question-portal/community/posts/${encodeURIComponent(postId)}/comments/${encodeURIComponent(commentId)}/visibility`,
    method: 'PATCH',
    data: payload
  })
}

export function bulkUpdateQuestionAdminCommunityPostVisibility(payload) {
  return request({
    url: '/admin/question-portal/community/posts/bulk-visibility',
    method: 'PATCH',
    data: payload
  })
}

export function bulkUpdateQuestionAdminCommunityPostFeatured(payload) {
  return request({
    url: '/admin/question-portal/community/posts/bulk-featured',
    method: 'PATCH',
    data: payload
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

export function fetchAdminQuestionBankPendingPublishPreview(questionBankId) {
  return request({
    url: `/admin/question-banks/${questionBankId}/pending-publish-preview`,
    method: 'GET'
  })
}

export function publishAdminQuestionBankPendingQuestions(questionBankId, payload) {
  return request({
    url: `/admin/question-banks/${questionBankId}/publish-pending`,
    method: 'POST',
    data: payload
  })
}

export function fetchAdminMockExamPapers(params = {}) {
  return request({
    url: '/admin/mock-exams',
    method: 'GET',
    data: params
  })
}

export function fetchAdminMockExamPaperDetail(paperId) {
  return request({
    url: `/admin/mock-exams/${encodeURIComponent(paperId)}`,
    method: 'GET'
  })
}

export function createAdminMockExamPaper(payload) {
  return request({
    url: '/admin/mock-exams',
    method: 'POST',
    data: payload
  })
}

export function updateAdminMockExamPaper(paperId, payload) {
  return request({
    url: `/admin/mock-exams/${encodeURIComponent(paperId)}`,
    method: 'PATCH',
    data: payload,
    timeout: 30000
  })
}

export function publishAdminMockExamPaper(paperId) {
  return request({
    url: `/admin/mock-exams/${encodeURIComponent(paperId)}/publish`,
    method: 'POST',
    timeout: 30000
  })
}

export function archiveAdminMockExamPaper(paperId) {
  return request({
    url: `/admin/mock-exams/${encodeURIComponent(paperId)}/archive`,
    method: 'POST'
  })
}

export function fetchAdminMockExamQuestionOptions(params = {}) {
  return request({
    url: '/admin/mock-exams/question-options',
    method: 'GET',
    data: params,
    timeout: 30000
  })
}

export function fetchAdminOverview() {
  return request({
    url: '/admin/overview',
    method: 'GET',
    timeout: 20000
  })
}

export function fetchAdminUsers(params = {}) {
  return request({
    url: '/admin/users',
    method: 'GET',
    data: params,
    timeout: 20000
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

export function fetchAdminQuestionStats(params = {}) {
  return request({
    url: '/admin/question-stats',
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

export function deleteAdminQuestions(payload) {
  return request({
    url: '/admin/questions/bulk',
    method: 'DELETE',
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

export function fetchQuestionAdminCommunityReports(params = {}) {
  return request({
    url: '/admin/question-portal/community/reports',
    method: 'GET',
    data: params
  })
}

export function updateQuestionAdminCommunityReport(reportId, payload) {
  return request({
    url: `/admin/question-portal/community/reports/${encodeURIComponent(reportId)}`,
    method: 'PATCH',
    data: payload
  })
}

export function fetchQuestionAdminCommunityAppeals(params = {}) {
  return request({
    url: '/admin/question-portal/community/appeals',
    method: 'GET',
    data: params
  })
}

export function updateQuestionAdminCommunityAppeal(appealId, payload) {
  return request({
    url: `/admin/question-portal/community/appeals/${encodeURIComponent(appealId)}`,
    method: 'PATCH',
    data: payload
  })
}

export function fetchAdminMentorProfiles(params = {}) {
  return request({
    url: '/admin/mentor-consultation/mentors',
    method: 'GET',
    data: params
  })
}

export function fetchAdminMentorProfile(mentorId) {
  return request({
    url: `/admin/mentor-consultation/mentors/${encodeURIComponent(mentorId)}`,
    method: 'GET'
  })
}

export function createAdminMentorProfile(payload) {
  return request({
    url: '/admin/mentor-consultation/mentors',
    method: 'POST',
    data: payload
  })
}

export function updateAdminMentorProfile(mentorId, payload) {
  return request({
    url: `/admin/mentor-consultation/mentors/${encodeURIComponent(mentorId)}`,
    method: 'PATCH',
    data: payload
  })
}

export function fetchAdminMentorSlots(mentorId, params = {}) {
  return request({
    url: `/admin/mentor-consultation/mentors/${encodeURIComponent(mentorId)}/slots`,
    method: 'GET',
    data: params
  })
}

export function createAdminMentorSlot(mentorId, payload) {
  return request({
    url: `/admin/mentor-consultation/mentors/${encodeURIComponent(mentorId)}/slots`,
    method: 'POST',
    data: payload
  })
}

export function updateAdminMentorSlot(slotId, payload) {
  return request({
    url: `/admin/mentor-consultation/slots/${encodeURIComponent(slotId)}`,
    method: 'PATCH',
    data: payload
  })
}

export function fetchAdminMentorVerificationApplications(params = {}) {
  return request({
    url: '/admin/mentor-consultation/applications',
    method: 'GET',
    data: params
  })
}

export function fetchAdminMentorVerificationApplication(applicationId) {
  return request({
    url: `/admin/mentor-consultation/applications/${encodeURIComponent(applicationId)}`,
    method: 'GET'
  })
}

export function decideAdminMentorVerificationApplication(applicationId, payload) {
  return request({
    url: `/admin/mentor-consultation/applications/${encodeURIComponent(applicationId)}/decision`,
    method: 'POST',
    data: payload
  })
}

export function fetchAdminMentorConsultationReports(params = {}) {
  return request({
    url: '/admin/mentor-consultation/reports',
    method: 'GET',
    data: params
  })
}

export function fetchAdminMentorConsultationReport(reportId) {
  return request({
    url: `/admin/mentor-consultation/reports/${encodeURIComponent(reportId)}`,
    method: 'GET'
  })
}

export function updateAdminMentorConsultationReportStatus(reportId, payload) {
  return request({
    url: `/admin/mentor-consultation/reports/${encodeURIComponent(reportId)}/status`,
    method: 'PATCH',
    data: payload
  })
}

export function fetchAdminMentorConsultationReportAppeals(params = {}) {
  return request({
    url: '/admin/mentor-consultation/report-appeals',
    method: 'GET',
    data: params
  })
}

export function fetchAdminMentorConsultationReportAppeal(appealId) {
  return request({
    url: `/admin/mentor-consultation/report-appeals/${encodeURIComponent(appealId)}`,
    method: 'GET'
  })
}

export function updateAdminMentorConsultationReportAppealStatus(appealId, payload) {
  return request({
    url: `/admin/mentor-consultation/report-appeals/${encodeURIComponent(appealId)}/status`,
    method: 'PATCH',
    data: payload
  })
}

export function fetchAdminMentorConsultationOrders(params = {}) {
  return request({
    url: '/admin/mentor-consultation/orders',
    method: 'GET',
    data: params
  })
}

export function fetchAdminMentorConsultationOrder(orderId) {
  return request({
    url: `/admin/mentor-consultation/orders/${encodeURIComponent(orderId)}`,
    method: 'GET'
  })
}

export function interveneAdminMentorConsultationOrder(orderId, payload) {
  return request({
    url: `/admin/mentor-consultation/orders/${encodeURIComponent(orderId)}/intervention`,
    method: 'POST',
    data: payload
  })
}

export function fetchAdminMentorProfileChangeRequests(params = {}) {
  return request({
    url: '/admin/mentor-consultation/profile-change-requests',
    method: 'GET',
    data: params
  })
}

export function fetchAdminMentorProfileChangeRequest(requestId) {
  return request({
    url: `/admin/mentor-consultation/profile-change-requests/${encodeURIComponent(requestId)}`,
    method: 'GET'
  })
}

export function decideAdminMentorProfileChangeRequest(requestId, payload) {
  return request({
    url: `/admin/mentor-consultation/profile-change-requests/${encodeURIComponent(requestId)}/decision`,
    method: 'POST',
    data: payload
  })
}
