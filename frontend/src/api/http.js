import { API_BASE_URL } from './config'
import { clearAuthSession, getAccessToken } from '../utils/auth'

export function request(options) {
  const token = getAccessToken()
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
      success(response) {
        if (response.statusCode >= 200 && response.statusCode < 300) {
          resolve(response.data)
          return
        }

        if (response.statusCode === 401 && token && options.authRedirect !== false) {
          clearAuthSession()
          uni.showToast({ title: '登录已过期，请重新登录', icon: 'none' })
          setTimeout(() => {
            uni.navigateTo({
              url: `/pages/login/index?redirect=${encodeURIComponent(getCurrentPagePath())}`
            })
          }, 300)
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
