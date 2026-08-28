import { request } from './http'

export function fetchMockExamPapers(params = {}) {
  return request({
    url: '/mock-exams',
    method: 'GET',
    data: params
  })
}

export function fetchMockExamPaperDetail(paperId) {
  return request({
    url: `/mock-exams/${encodeURIComponent(paperId)}`,
    method: 'GET',
    timeout: 25000
  })
}
