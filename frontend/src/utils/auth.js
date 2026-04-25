const ACCESS_TOKEN_KEY = 'accessToken'
const REFRESH_TOKEN_KEY = 'refreshToken'
const AUTH_USER_KEY = 'authUser'

export function saveAuthSession(session) {
  const accessToken = session?.accessToken || ''
  const refreshToken = session?.refreshToken || ''
  const user = session?.user || null

  uni.setStorageSync(ACCESS_TOKEN_KEY, accessToken)
  uni.setStorageSync(REFRESH_TOKEN_KEY, refreshToken)
  uni.setStorageSync(AUTH_USER_KEY, user)
}

export function getAccessToken() {
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
  return Boolean(getAccessToken())
}

export function clearAuthSession() {
  uni.removeStorageSync(ACCESS_TOKEN_KEY)
  uni.removeStorageSync(REFRESH_TOKEN_KEY)
  uni.removeStorageSync(AUTH_USER_KEY)
}
