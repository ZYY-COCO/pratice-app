export function buildMpPageSafeStyle() {
  let style = ''

  // #ifdef MP-WEIXIN
  let systemInfo = {}
  let menuRect = null

  try {
    systemInfo = uni.getSystemInfoSync() || {}
  } catch (error) {
    systemInfo = {}
  }

  try {
    if (typeof uni.getMenuButtonBoundingClientRect === 'function') {
      menuRect = uni.getMenuButtonBoundingClientRect()
    } else if (typeof wx !== 'undefined' && typeof wx.getMenuButtonBoundingClientRect === 'function') {
      menuRect = wx.getMenuButtonBoundingClientRect()
    }
  } catch (error) {
    menuRect = null
  }

  const statusBarHeight = Number(systemInfo.statusBarHeight || systemInfo.safeArea?.top || 20)
  const capsuleHeight = Number(menuRect?.height || 32)
  const capsuleBottom = Number(menuRect?.bottom || statusBarHeight + capsuleHeight + 8)
  const contentTop = Math.ceil(Math.max(capsuleBottom + 8, statusBarHeight + 48))
  const headerHeight = Math.ceil(Math.max(capsuleHeight, 40))

  style = `--mp-page-content-top:${contentTop}px;--mp-page-header-height:${headerHeight}px`
  // #endif

  return style
}
