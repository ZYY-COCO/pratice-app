import { request } from './http'

export function fetchCircleResources(resourceType) {
  return request({
    url: '/circle/resources',
    method: 'GET',
    data: { resource_type: resourceType },
    authRedirect: false
  })
}

export function fetchQuestionAdminResources(params = {}) {
  return request({
    url: '/admin/question-portal/resources',
    method: 'GET',
    data: params
  })
}

export function createQuestionAdminResource(payload) {
  return request({
    url: '/admin/question-portal/resources',
    method: 'POST',
    data: payload
  })
}

export function updateQuestionAdminResource(resourceId, payload) {
  return request({
    url: `/admin/question-portal/resources/${encodeURIComponent(resourceId)}`,
    method: 'PATCH',
    data: payload
  })
}

export function deleteQuestionAdminResource(resourceId) {
  return request({
    url: `/admin/question-portal/resources/${encodeURIComponent(resourceId)}`,
    method: 'DELETE'
  })
}
