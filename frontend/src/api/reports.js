import { request } from './http'

export function fetchAbilityReport(params = {}) {
  const query = Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')

  return request({
    url: query ? `/report/ability?${query}` : '/report/ability'
  })
}

export function fetchLearningSummary(params = {}) {
  const query = Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')

  return request({
    url: query ? `/report/summary?${query}` : '/report/summary'
  })
}
