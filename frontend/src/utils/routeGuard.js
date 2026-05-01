import { isLoggedIn } from './auth'

const LOGIN_PAGE = '/pages/login/index'
const HOME_PAGE = '/pages/home/index'

export function enforceAuthOnCurrentPage() {
  setTimeout(() => {
    const currentUrl = getCurrentPageUrl()
    const currentPath = stripQuery(currentUrl)

    if (!currentPath || currentPath === LOGIN_PAGE || isLoggedIn()) {
      return
    }

    uni.reLaunch({
      url: `${LOGIN_PAGE}?redirect=${encodeURIComponent(currentUrl)}`
    })
  }, 0)
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
