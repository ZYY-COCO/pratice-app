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
  let token = getAccessToken()

  if (shouldRefreshBeforeRequest(options, token)) {
    try {
      await refreshAuthSession()
      token = getAccessToken()
    } catch (error) {
      handleAuthFailure()
      return Promise.reject(error)
    }
  }

  return dispatchRequest(options, token, false)
}

function dispatchRequest(options, token, retried) {
  const data = cleanRequestData(options.data)

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}${options.url}`,
      method: options.method || 'GET',
      timeout: options.timeout || 12000,
      data,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.header || {})
      },
      async success(response) {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(response.data)
          return
        }

        if (response.statusCode === 401 && token && options.authRedirect !== false && !retried) {
          try {
            await refreshAuthSession()
            resolve(dispatchRequest(options, getAccessToken(), true))
            return
          } catch (error) {
            handleAuthFailure()
          }
        } else if (response.statusCode === 401 && token && options.authRedirect !== false) {
          handleAuthFailure()
        }

        reject(response.data || { detail: '请求失败' })
      },
      fail(error) {
        const message = error?.errMsg || ''

        if (message.includes('timeout')) {
          reject({ detail: '请求超时，请检查后端服务或网络连接' })
          return
        }

        reject({ detail: message || '网络请求失败，请稍后重试' })
      }
    })
  })
}

function shouldRefreshBeforeRequest(options, token) {
  if (!token || options.authRedirect === false) return false
  if (options.header?.Authorization === '') return false
  return Boolean(getRefreshToken() && isAccessTokenExpiring(token))
}

function refreshAuthSession() {
  if (refreshPromise) return refreshPromise

  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    return Promise.reject({ detail: '登录已过期，请重新登录' })
  }

  refreshPromise = new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}/auth/refresh`,
      method: 'POST',
      timeout: 12000,
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
        reject(response.data || { detail: '登录已过期，请重新登录' })
      },
      fail(error) {
        reject({ detail: error?.errMsg || '登录状态刷新失败' })
      }
    })
  }).finally(() => {
    refreshPromise = null
  })

  return refreshPromise
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
  const token = getAccessToken()
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
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.header || {})
      },
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
      header: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(options.header || {})
      },
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
