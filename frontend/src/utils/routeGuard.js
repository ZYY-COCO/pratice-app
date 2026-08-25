import { isLoggedIn } from './auth'

const LOGIN_PAGE = '/pages/login/index'
const HOME_PAGE = '/pages/home/index'
const PUBLIC_PAGE_PATHS = new Set([
  HOME_PAGE,
  LOGIN_PAGE,
  '/pages-sub-data/major-catalog/index',
  '/pages-sub-data/school-announcements/index',
  '/pages-sub-consultation/consultation/mentor-detail',
  '/pages/version/index',
  '/pages/subjects/index',
  '/pages/pro/index',
  '/pages/about/index',
  '/pages/legal/user-agreement',
  '/pages-sub-admin/admin/question-login'
])

export function enforceAuthOnCurrentPage() {
  setTimeout(() => {
    const currentUrl = getCurrentPageUrl()
    const currentPath = stripQuery(currentUrl)

    if (!currentPath || isPublicRoute(currentPath) || isLoggedIn()) {
      return
    }

    uni.reLaunch({
      url: `${LOGIN_PAGE}?redirect=${encodeURIComponent(currentUrl)}`
    })
  }, 0)
}

export function isPublicRoute(url = '') {
  return PUBLIC_PAGE_PATHS.has(stripQuery(url))
}

export function redirectIfAlreadyAuthed(targetUrl = HOME_PAGE) {
  if (!isLoggedIn()) return false

  const safeTarget = stripQuery(targetUrl) === LOGIN_PAGE ? HOME_PAGE : targetUrl
  setTimeout(() => {
    uni.reLaunch({ url: safeTarget || HOME_PAGE })
  }, 80)
  return true
}

export function getCurrentPageUrl() {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  if (!current?.route) return ''

  const path = `/${current.route}`
  const query = serializeOptions(current.options || {})
  return query ? `${path}?${query}` : path
}

function stripQuery(url = '') {
  return String(url).split('?')[0]
}

function serializeOptions(options) {
  return Object.keys(options)
    .filter((key) => options[key] !== undefined && options[key] !== null && options[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(options[key])}`)
    .join('&')
}
