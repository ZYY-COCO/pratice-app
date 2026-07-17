const ACCESS_TOKEN_KEY = 'accessToken'
const REFRESH_TOKEN_KEY = 'refreshToken'
const AUTH_USER_KEY = 'authUser'
const AUTH_EXPIRES_AT_KEY = 'authExpiresAt'
const SESSION_TTL_DAYS = 30
const ACCESS_TOKEN_REFRESH_MARGIN_MS = 60 * 1000

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

export function getRefreshToken() {
  if (!isAuthSessionValid()) {
    clearAuthSession()
    return ''
  }
  return uni.getStorageSync(REFRESH_TOKEN_KEY) || ''
}

export function isAccessTokenExpiring(token = '') {
  const expiresAt = getJwtExpiresAt(token || uni.getStorageSync(ACCESS_TOKEN_KEY) || '')
  if (!expiresAt) return false
  return expiresAt <= Date.now() + ACCESS_TOKEN_REFRESH_MARGIN_MS
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

function getJwtExpiresAt(token) {
  const payload = String(token || '').split('.')[1]
  if (!payload) return 0

  try {
    const decoded = decodeBase64Url(payload)
    const data = JSON.parse(decoded)
    return Number(data?.exp || 0) * 1000
  } catch (error) {
    return 0
  }
}

function decodeBase64Url(value) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'
  const source = String(value || '').replace(/-/g, '+').replace(/_/g, '/').replace(/=+$/g, '')
  const bytes = []
  let buffer = 0
  let bits = 0

  for (const character of source) {
    const index = alphabet.indexOf(character)
    if (index < 0) continue
    buffer = (buffer << 6) | index
    bits += 6
    if (bits >= 8) {
      bits -= 8
      bytes.push((buffer >> bits) & 0xff)
    }
  }

  const encoded = bytes.map((byte) => `%${byte.toString(16).padStart(2, '0')}`).join('')
  return decodeURIComponent(encoded)
}
