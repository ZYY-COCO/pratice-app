import { API_BASE_URL } from './config'
import {
  clearAuthSession,
  getAccessToken,
  getAuthUser,
  getRefreshToken,
  isAccessTokenExpiring,
  saveAuthSession
} from '../utils/auth'

let refreshPromise = null
let authRedirectPending = false

export async function request(options) {
  const token = await getRequestAccessToken(options)
  try {
    return await dispatchRequest(options, token, false)
  } catch (error) {
    if (!shouldRetryTransientReadRequest(options, error)) {
      throw error
    }

    await wait(350)
    const retryToken = await getRequestAccessToken(options)
    return dispatchRequest(options, retryToken, false)
  }
}

function dispatchRequest(options, token, retried) {
  const data = cleanRequestData(options.data)

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}${options.url}`,
      method: options.method || 'GET',
      timeout: options.timeout || 12000,
      data,
      header: buildRequestHeaders(options, token, 'application/json'),
      async success(response) {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(response.data)
          return
        }

        if (response.statusCode === 401 && token && !retried) {
          try {
            await refreshAuthSession()
            resolve(dispatchRequest(options, getAccessToken(), true))
            return
          } catch (error) {
            if (options.authRedirect !== false && shouldClearAuthSession(error)) {
              handleAuthFailure()
            }
            reject(error)
            return
          }
        } else if (response.statusCode === 401 && token && options.authRedirect !== false) {
          handleAuthFailure()
        }

        reject(createHttpError(response.data, response.statusCode))
      },
      fail(error) {
        const message = error?.errMsg || ''
        const normalizedMessage = message.toLowerCase()

        if (
          normalizedMessage.includes('timeout') ||
          normalizedMessage.includes('timed out') ||
          normalizedMessage.includes('-1001')
        ) {
          reject({
            detail: '请求超时，请检查网络连接后重试',
            code: 'NETWORK_TIMEOUT',
            retryable: true
          })
          return
        }

        reject({
          detail: message || '网络请求失败，请稍后重试',
          code: 'NETWORK_ERROR',
          retryable: true
        })
      }
    })
  })
}

export async function getRequestAccessToken(options = {}) {
  const token = getAccessToken()
  if (!shouldRefreshBeforeRequest(options, token)) {
    return token
  }

  try {
    await refreshAuthSession()
    return getAccessToken()
  } catch (error) {
    // A short network failure must not be converted into a forced logout. The
    // existing access token can still be accepted until it actually expires.
    if (options.authRedirect !== false && shouldClearAuthSession(error)) {
      handleAuthFailure()
      throw error
    }
    return token
  }
}

function shouldRefreshBeforeRequest(options, token) {
  if (!token) return false
  if (options.header?.Authorization === '') return false
  return Boolean(getRefreshToken() && isAccessTokenExpiring(token))
}

function createHttpError(data, statusCode) {
  const retryable = [408, 429, 502, 503, 504].includes(statusCode)
  if (data && typeof data === 'object' && !Array.isArray(data)) {
    return { ...data, statusCode, retryable: data.retryable ?? retryable }
  }
  return {
    detail: typeof data === 'string' && data ? data : '请求失败',
    statusCode,
    retryable
  }
}

function shouldRetryTransientReadRequest(options, error) {
  return String(options.method || 'GET').toUpperCase() === 'GET' && error?.retryable === true
}

function wait(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds))
}

function shouldClearAuthSession(error) {
  return error?.code === 'AUTH_REFRESH_REJECTED' || error?.code === 'AUTH_REFRESH_UNAVAILABLE'
}

function refreshAuthSession() {
  if (refreshPromise) return refreshPromise

  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    return Promise.reject({ detail: '登录已过期，请重新登录', code: 'AUTH_REFRESH_UNAVAILABLE' })
  }

  refreshPromise = refreshAuthSessionOnce(refreshToken)
    .catch(async (error) => {
      if (!error?.retryable) throw error
      await wait(500)
      return refreshAuthSessionOnce(refreshToken)
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

function refreshAuthSessionOnce(refreshToken) {
  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}/auth/refresh`,
      method: 'POST',
      timeout: 20000,
      data: { refresh_token: refreshToken },
      header: { 'Content-Type': 'application/json' },
      success(response) {
        if (response.statusCode >= 200 && response.statusCode < 300 && response.data?.access_token) {
          saveAuthSession({
            accessToken: response.data.access_token,
            refreshToken: response.data.refresh_token || refreshToken,
            user: response.data.user || getAuthUser()
          })
          resolve(response.data)
          return
        }
        const rejectedByAuthServer = response.statusCode === 401 || response.statusCode === 403
        const retryable = [408, 429, 502, 503, 504].includes(response.statusCode)
        reject({
          ...(response.data || {}),
          detail: response.data?.detail || (
            response.statusCode === 429
              ? '登录状态刷新请求过于频繁，请稍后重试'
              : '登录状态刷新失败，请稍后重试'
          ),
          statusCode: response.statusCode,
          code: rejectedByAuthServer ? 'AUTH_REFRESH_REJECTED' : 'AUTH_REFRESH_FAILED',
          retryable: !rejectedByAuthServer && retryable
        })
      },
      fail(error) {
        const message = error?.errMsg || ''
        const timedOut = message.toLowerCase().includes('timeout') || message.includes('-1001')
        reject({
          detail: message || '登录状态刷新失败，请检查网络后重试',
          code: timedOut ? 'NETWORK_TIMEOUT' : 'NETWORK_ERROR',
          retryable: true
        })
      }
    })
  })
}

function handleAuthFailure() {
  clearAuthSession()
  if (authRedirectPending) return

  authRedirectPending = true
  const redirect = encodeURIComponent(getCurrentPagePath())
  uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
  setTimeout(() => {
    uni.reLaunch({
      url: `/pages/login/index?redirect=${redirect}`,
      complete() {
        setTimeout(() => {
          authRedirectPending = false
        }, 1000)
      }
    })
  }, 300)
}

export function uploadFileRequest(options) {
  return getRequestAccessToken(options).then((token) => uploadFileWithToken(options, token))
}

function uploadFileWithToken(options, token) {
  const url = `${API_BASE_URL}${options.url}`

  if (options.file && typeof FormData !== 'undefined' && typeof fetch !== 'undefined') {
    const formData = new FormData()
    formData.append(options.name || 'file', options.file, options.fileName || options.file.name || 'upload')
    Object.entries(options.formData || {}).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        formData.append(key, value)
      }
    })

    return fetch(url, {
      method: 'POST',
      headers: buildRequestHeaders(options, token),
      body: formData
    }).then(async (response) => {
      const data = await response.json().catch(() => ({}))
      if (response.ok) {
        return data
      }
      return Promise.reject(data || { detail: '上传失败' })
    })
  }

  return new Promise((resolve, reject) => {
    uni.uploadFile({
      url,
      filePath: options.filePath,
      name: options.name || 'file',
      formData: options.formData || {},
      timeout: options.timeout || 60000,
      header: buildRequestHeaders(options, token),
      success(response) {
        let data = response.data
        try {
          data = typeof response.data === 'string' ? JSON.parse(response.data) : response.data
        } catch (error) {
          data = { detail: response.data || '上传失败' }
        }
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(data)
          return
        }
        reject(data || { detail: '上传失败' })
      },
      fail(error) {
        reject({ detail: error?.errMsg || '上传失败' })
      }
    })
  })
}

function buildRequestHeaders(options, token, contentType = '') {
  const { Authorization: requestedAuthorization, ...customHeaders } = options.header || {}
  const isAnonymousRequest = requestedAuthorization === ''

  return {
    ...(contentType ? { 'Content-Type': contentType } : {}),
    ...customHeaders,
    ...(!isAnonymousRequest && token ? { Authorization: `Bearer ${token}` } : {})
  }
}

function cleanRequestData(data) {
  if (!data || typeof data !== 'object' || Array.isArray(data)) {
    return data || {}
  }

  return Object.keys(data).reduce((result, key) => {
    if (data[key] !== undefined) {
      result[key] = data[key]
    }
    return result
  }, {})
}

function getCurrentPagePath() {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  if (!current?.route) {
    return '/pages/home/index'
  }
  return `/${current.route}`
}
