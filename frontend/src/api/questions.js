import { request } from './http'

export function fetchQuestionsByModule(params) {
  const query = Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')

  return request({
    url: `/questions/by-module?${query}`
  })
}

export function fetchQuestionProgress(params) {
  const query = Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')

  return request({
    url: `/questions/progress?${query}`
  })
}

export function fetchReviewDueQuestions(params) {
  const query = Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')

  return request({
    url: `/questions/review-due?${query}`
  })
}
