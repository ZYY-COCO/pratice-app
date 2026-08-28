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

export function fetchStudyGoal(params = {}) {
  const query = Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')

  return request({
    url: query ? `/report/study-goal?${query}` : '/report/study-goal'
  })
}

export function saveStudyGoal(data) {
  return request({
    url: '/report/study-goal',
    method: 'PUT',
    data
  })
}

export function fetchPlatformPracticeTrend() {
  return request({
    url: '/report/platform-practice-trend',
    method: 'GET',
    authRedirect: false
  })
}

export function fetchStudyAdvice(params = {}) {
  const query = Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')

  return request({
    url: query ? `/report/study-advice?${query}` : '/report/study-advice',
    timeout: 45000
  })
}

export function fetchLeaderboard(params = {}) {
  const query = Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')

  return request({
    url: query ? `/report/leaderboard?${query}` : '/report/leaderboard'
  })
}

export function fetchDailyStudyLeaderboard(params = {}) {
  const query = Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')

  return request({
    url: query ? `/report/daily-study-leaderboard?${query}` : '/report/daily-study-leaderboard'
  })
}
