import { API_BASE_URL } from './config'
import { clearAuthSession } from '../utils/auth'

export function request(options) {
  const token = uni.getStorageSync('accessToken')

  return new Promise((resolve, reject) => {
    uni.request({
      url: `${API_BASE_URL}${options.url}`,
      method: options.method || 'GET',
      timeout: options.timeout || 12000,
      data: options.data || {},
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

function getCurrentPagePath() {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  if (!current?.route) {
    return '/pages/home/index'
  }
  return `/${current.route}`
}
