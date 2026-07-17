let runtimePlatform = 'unknown'

// #ifdef H5
runtimePlatform = 'h5'
// #endif

// #ifdef MP-WEIXIN
runtimePlatform = 'mp-weixin'
// #endif

// #ifdef APP-PLUS
runtimePlatform = 'app-plus'
// #endif

export const RUNTIME_PLATFORM = runtimePlatform
export const IS_H5 = runtimePlatform === 'h5'
export const IS_MP_WEIXIN = runtimePlatform === 'mp-weixin'
export const IS_APP_PLUS = runtimePlatform === 'app-plus'

export function openExternalUrl(url, options = {}) {
  if (!url) return false

  // #ifdef APP-PLUS
  if (typeof plus !== 'undefined' && plus?.runtime?.openURL) {
    plus.runtime.openURL(url)
    return true
  }
  // #endif

  // #ifdef H5
  if (typeof window !== 'undefined') {
    window.location.href = url
    return true
  }
  // #endif

  uni.setClipboardData({
    data: url,
    success() {
      uni.showToast({ title: options.copyMessage || '链接已复制', icon: 'none' })
    }
  })
  return false
}

export function redirectH5(url) {
  let redirected = false

  // #ifdef H5
  if (url && typeof window !== 'undefined') {
    window.location.href = url
    redirected = true
  }
  // #endif

  return redirected
}

export function getCurrentH5Url() {
  let url = ''

  // #ifdef H5
  if (typeof window !== 'undefined') {
    url = window.location.href || ''
  }
  // #endif

  return url
}

export function replaceCurrentH5Url(url) {
  let replaced = false

  // #ifdef H5
  if (url && typeof window !== 'undefined' && window.history?.replaceState) {
    const title = typeof document === 'undefined' ? '' : document.title
    window.history.replaceState({}, title, url)
    replaced = true
  }
  // #endif

  return replaced
}

export function readLegacyH5Storage(keys = []) {
  let value = ''

  // #ifdef H5
  if (typeof window !== 'undefined' && window.localStorage) {
    for (const key of keys) {
      value = window.localStorage.getItem(key) || ''
      if (value) break
    }
  }
  // #endif

  return value
}

export function applyRootCssVariables(variables = {}) {
  let applied = false

  // #ifdef H5 || APP-PLUS
  if (typeof document !== 'undefined') {
    const root = document.documentElement
    Object.entries(variables).forEach(([name, value]) => {
      root.style.setProperty(name, value)
    })
    applied = true
  }
  // #endif

  return applied
}

export function closeNativeSplashscreen() {
  // #ifdef APP-PLUS
  const close = () => {
    try {
      const runtime = typeof plus === 'undefined' ? null : plus
      if (runtime?.navigator?.closeSplashscreen) {
        runtime.navigator.closeSplashscreen()
      }
    } catch (error) {
      // Keep launch resilient if the native runtime is not ready yet.
    }
  }

  setTimeout(close, 300)
  setTimeout(close, 1200)
  // #endif
}
