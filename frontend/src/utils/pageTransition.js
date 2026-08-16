const ROUTE_DURATION = 380
const FORWARD_ANIMATION = 'slide-in-right'
const BACK_ANIMATION = 'slide-out-right'
const WRAPPED_FLAG = '__gytPageTransitionWrapped__'
const H5_ROUTE_CLASSES = ['gyt-route-enter-forward', 'gyt-route-leave-back']
const H5_EDGE_SWIPE_EXCLUDED_ROUTES = new Set([
  'pages/home/index',
  'pages/circle/publish'
])

let h5BackTransitionPending = false
let h5EnterRequestId = 0

export function installPageTransitions() {
  if (typeof uni === 'undefined') return

  wrapForwardNavigation('navigateTo')
  wrapForwardNavigation('redirectTo')
  wrapForwardNavigation('reLaunch')
  wrapBackNavigation()
  installH5EdgeSwipeBack()
}

function wrapForwardNavigation(methodName) {
  const nativeMethod = uni[methodName]
  if (typeof nativeMethod !== 'function' || nativeMethod[WRAPPED_FLAG]) return

  const wrappedMethod = (options = {}) => {
    const normalizedOptions = normalizeNavigationOptions(options)
    const sourcePage = getH5ActivePage()
    const sourceRoute = getH5PageRoute(sourcePage)
    const result = nativeMethod.call(uni, {
      animationType: FORWARD_ANIMATION,
      animationDuration: ROUTE_DURATION,
      ...normalizedOptions
    })

    if (!hasExplicitAnimation(normalizedOptions)) {
      scheduleH5PageEnter(sourcePage, sourceRoute)
    }
    return result
  }

  wrappedMethod[WRAPPED_FLAG] = true
  try {
    uni[methodName] = wrappedMethod
  } catch (error) {
    // Some runtimes expose read-only navigation methods. Their native animation remains unchanged.
  }
}

function wrapBackNavigation() {
  const nativeMethod = uni.navigateBack
  if (typeof nativeMethod !== 'function' || nativeMethod[WRAPPED_FLAG]) return

  const wrappedMethod = (options = {}) => {
    const normalizedOptions = normalizeBackOptions(options)
    const navigate = () => nativeMethod.call(uni, {
      animationType: BACK_ANIMATION,
      animationDuration: ROUTE_DURATION,
      ...normalizedOptions
    })

    if (hasExplicitAnimation(normalizedOptions)) {
      return navigate()
    }
    return runH5PageExit(navigate)
  }

  wrappedMethod[WRAPPED_FLAG] = true
  try {
    uni.navigateBack = wrappedMethod
  } catch (error) {
    // Some runtimes expose read-only navigation methods. Their native animation remains unchanged.
  }
}

function normalizeNavigationOptions(options) {
  return options && typeof options === 'object' ? options : {}
}

function normalizeBackOptions(options) {
  if (typeof options === 'number') return { delta: options }
  return normalizeNavigationOptions(options)
}

function hasExplicitAnimation(options) {
  return Object.prototype.hasOwnProperty.call(options, 'animationType')
}

function getH5ActivePage() {
  // #ifdef H5
  if (typeof document === 'undefined') return null
  const pages = Array.from(document.querySelectorAll('uni-page'))
  return pages[pages.length - 1] || document.querySelector('uni-page-body')
  // #endif
  return null
}

function getH5PageRoute(page) {
  if (!page) return ''
  return page.getAttribute?.('data-page') || page.dataset?.page || ''
}

function scheduleH5PageEnter(sourcePage, sourceRoute) {
  // #ifdef H5
  if (prefersReducedMotion()) return
  const requestId = ++h5EnterRequestId
  let attempts = 0

  const applyWhenMounted = () => {
    if (requestId !== h5EnterRequestId) return
    const targetPage = getH5ActivePage()
    const changed = targetPage && (targetPage !== sourcePage || getH5PageRoute(targetPage) !== sourceRoute)
    if (changed) {
      applyH5RouteMotion(targetPage, 'gyt-route-enter-forward')
      return
    }
    attempts += 1
    if (attempts < 12) {
      nextH5Frame(applyWhenMounted)
    }
  }

  nextH5Frame(applyWhenMounted)
  // #endif
}

function runH5PageExit(navigate) {
  // #ifdef H5
  if (prefersReducedMotion()) return navigate()
  if (h5BackTransitionPending) return undefined

  const currentPage = getH5ActivePage()
  if (!currentPage) return navigate()

  h5BackTransitionPending = true
  const sourceRoute = getH5PageRoute(currentPage)
  const exitOverlay = createH5ExitOverlay(currentPage)
  if (!exitOverlay) {
    h5BackTransitionPending = false
    return navigate()
  }

  try {
    navigate()
  } catch (error) {
    removeH5ExitOverlay(exitOverlay)
    h5BackTransitionPending = false
    throw error
  }

  scheduleH5ExitOverlay(exitOverlay, currentPage, sourceRoute)
  return undefined
  // #endif
  return navigate()
}

function createH5ExitOverlay(page) {
  // #ifdef H5
  if (typeof document === 'undefined' || typeof window === 'undefined') return null

  const rect = page.getBoundingClientRect()
  if (!rect.width || !rect.height) return null

  const overlay = document.createElement('div')
  const snapshot = document.createElement('div')
  const pageStyle = window.getComputedStyle(page)

  overlay.className = 'gyt-route-exit-overlay'
  overlay.setAttribute('aria-hidden', 'true')
  overlay.style.background = pageStyle.background
  overlay.style.backgroundColor = pageStyle.backgroundColor

  snapshot.className = 'gyt-route-exit-snapshot'
  snapshot.style.left = `${Math.round(rect.left)}px`
  snapshot.style.top = `${Math.round(rect.top)}px`
  snapshot.style.width = `${Math.ceil(rect.width)}px`
  snapshot.style.minHeight = `${Math.ceil(rect.height)}px`
  snapshot.innerHTML = page.innerHTML

  overlay.appendChild(snapshot)
  document.body.appendChild(overlay)
  return overlay
  // #endif
  return null
}

function scheduleH5ExitOverlay(overlay, sourcePage, sourceRoute) {
  // #ifdef H5
  let attempts = 0

  const revealPreviousPage = () => {
    if (!overlay.isConnected) {
      h5BackTransitionPending = false
      return
    }

    const targetPage = getH5ActivePage()
    const pageChanged = targetPage
      && (targetPage !== sourcePage || getH5PageRoute(targetPage) !== sourceRoute)

    // Give the restored page a couple of frames to paint underneath the snapshot.
    if (!pageChanged && attempts < 2) {
      attempts += 1
      nextH5Frame(revealPreviousPage)
      return
    }

    nextH5Frame(() => {
      if (!overlay.isConnected) {
        h5BackTransitionPending = false
        return
      }
      applyH5RouteMotion(overlay, 'gyt-route-leave-back', () => {
        removeH5ExitOverlay(overlay)
        h5BackTransitionPending = false
      })
    })
  }

  nextH5Frame(revealPreviousPage)
  // #endif
}

function removeH5ExitOverlay(overlay) {
  // #ifdef H5
  if (overlay?.isConnected) overlay.remove()
  // #endif
}

function applyH5RouteMotion(page, className, onComplete) {
  // #ifdef H5
  if (!page?.classList) return
  page.classList.remove(...H5_ROUTE_CLASSES)
  void page.offsetWidth
  page.classList.add(className)

  let completed = false
  const clearMotion = () => {
    if (completed) return
    completed = true
    page.classList.remove(className)
    onComplete?.()
  }
  page.addEventListener('animationend', clearMotion, { once: true })
  window.setTimeout(clearMotion, ROUTE_DURATION + 80)
  // #endif
}

function nextH5Frame(callback) {
  // #ifdef H5
  if (typeof window === 'undefined') return
  if (typeof window.requestAnimationFrame === 'function') {
    window.requestAnimationFrame(callback)
    return
  }
  window.setTimeout(callback, 16)
  // #endif
}

function prefersReducedMotion() {
  // #ifdef H5
  return typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  // #endif
  return false
}

function installH5EdgeSwipeBack() {
  // #ifdef H5
  if (typeof window === 'undefined' || typeof document === 'undefined') return
  if (window.__gytPageEdgeSwipeInstalled) return
  window.__gytPageEdgeSwipeInstalled = true

  let gestureStart = null
  document.addEventListener('touchstart', (event) => {
    const touch = event.touches?.[0]
    if (!touch || !canUseH5EdgeSwipeBack() || isEdgeGestureBlocked(event.target)) {
      gestureStart = null
      return
    }
    gestureStart = { x: touch.clientX, y: touch.clientY }
  }, { passive: true })

  document.addEventListener('touchend', (event) => {
    const touch = event.changedTouches?.[0]
    const start = gestureStart
    gestureStart = null
    if (!touch || !start || start.x > 28) return

    const deltaX = touch.clientX - start.x
    const deltaY = touch.clientY - start.y
    if (deltaX >= 72 && Math.abs(deltaX) > Math.abs(deltaY) * 1.35) {
      uni.navigateBack({ delta: 1 })
    }
  }, { passive: true })
  // #endif
}

function canUseH5EdgeSwipeBack() {
  // #ifdef H5
  const pages = typeof getCurrentPages === 'function' ? getCurrentPages() : []
  const currentRoute = String(pages[pages.length - 1]?.route || '')
  return pages.length > 1 && !H5_EDGE_SWIPE_EXCLUDED_ROUTES.has(currentRoute)
  // #endif
  return false
}

function isEdgeGestureBlocked(target) {
  // #ifdef H5
  return Boolean(target?.closest?.('input, textarea, button, a, [data-gyt-no-edge-back]'))
  // #endif
  return false
}
