const ACCESS_TOKEN_KEY = 'accessToken'
const REFRESH_TOKEN_KEY = 'refreshToken'
const AUTH_USER_KEY = 'authUser'
const AUTH_EXPIRES_AT_KEY = 'authExpiresAt'
const SESSION_TTL_DAYS = 30

export function saveAuthSession(session) {
  const accessToken = session?.accessToken || ''
  const refreshToken = session?.refreshToken || ''
  const user = session?.user || null
  const expiresAt = Date.now() + SESSION_TTL_DAYS * 24 * 60 * 60 * 1000

  uni.setStorageSync(ACCESS_TOKEN_KEY, accessToken)
  uni.setStorageSync(REFRESH_TOKEN_KEY, refreshToken)
  uni.setStorageSync(AUTH_USER_KEY, user)
  uni.setStorageSync(AUTH_EXPIRES_AT_KEY, expiresAt)
}

export function getAccessToken() {
  if (!isAuthSessionValid()) {
    clearAuthSession()
    return ''
  }
  return uni.getStorageSync(ACCESS_TOKEN_KEY) || ''
}

export function getAuthUser() {
  return uni.getStorageSync(AUTH_USER_KEY) || null
}

export function updateAuthUser(patch) {
  const currentUser = getAuthUser()
  if (!currentUser) return null

  const nextUser = {
    ...currentUser,
    ...patch
  }
  uni.setStorageSync(AUTH_USER_KEY, nextUser)
  return nextUser
}

export function isLoggedIn() {
  const hasToken = Boolean(uni.getStorageSync(ACCESS_TOKEN_KEY))
  if (!hasToken) return false
  if (isAuthSessionValid()) return true
  clearAuthSession()
  return false
}

export function clearAuthSession() {
  uni.removeStorageSync(ACCESS_TOKEN_KEY)
  uni.removeStorageSync(REFRESH_TOKEN_KEY)
  uni.removeStorageSync(AUTH_USER_KEY)
  uni.removeStorageSync(AUTH_EXPIRES_AT_KEY)
}

function isAuthSessionValid() {
  const expiresAt = Number(uni.getStorageSync(AUTH_EXPIRES_AT_KEY) || 0)
  if (!expiresAt) return true
  return expiresAt > Date.now()
}
