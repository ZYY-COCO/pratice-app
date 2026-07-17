export function requireWechatPrivacyAuthorization() {
  // #ifdef MP-WEIXIN
  if (typeof wx !== 'undefined' && typeof wx.requirePrivacyAuthorize === 'function') {
    return new Promise((resolve, reject) => {
      wx.requirePrivacyAuthorize({
        success() {
          resolve(true)
        },
        fail(error) {
          reject({ detail: error?.errMsg || '需要同意隐私保护指引后才能继续' })
        }
      })
    })
  }
  // #endif

  return Promise.resolve(true)
}
