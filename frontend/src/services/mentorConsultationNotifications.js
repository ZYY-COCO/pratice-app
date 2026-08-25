import {
  fetchMyMentorProfile
} from '../api/mentorConsultation'
import { fetchUserNotifications, markUserNotificationRead } from '../api/notifications'
import { getAuthUser, isLoggedIn } from '../utils/auth'

const POLL_INTERVAL_MS = 10 * 1000
const ROLE_RECHECK_INTERVAL_MS = 5 * 60 * 1000
const NOTICE_VISIBLE_MS = 7 * 1000
const NOTICE_LEAVE_MS = 240
const NOTICE_EVENT_MAX_AGE_MS = 24 * 60 * 60 * 1000
const NOTICE_SEEN_TTL_MS = 30 * 24 * 60 * 60 * 1000
const NOTICE_SEEN_MAX_ENTRIES = 100
const NOTICE_SEEN_STORAGE_PREFIX = 'mentor-consultation-notice-seen-v2'
const NOTICE_HOST_ID = 'gyt-mentor-consultation-notice-host'
const NOTICE_STYLE_ID = 'gyt-mentor-consultation-notice-style'
const MENTOR_ORDER_NOTIFICATION_TYPE = 'mentor_order_created'

let pollTimer = null
let polling = false
let activeUserId = ''
let verifiedMentorId = ''
let lastRoleCheckAt = 0
let mentorRoleResolved = false
let activeNotice = null
let noticeLeaving = false
let noticeTimer = null
let noticeLeaveTimer = null
let noticeHost = null
let noticeQueue = []
const queuedNoticeKeys = new Set()

export function startMentorConsultationNotifications() {
  if (pollTimer !== null) {
    void refreshMentorConsultationNotifications()
    return
  }

  void refreshMentorConsultationNotifications()
  pollTimer = setInterval(() => {
    void refreshMentorConsultationNotifications()
  }, POLL_INTERVAL_MS)
}

export function stopMentorConsultationNotifications() {
  if (pollTimer !== null) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

// WebSocket / App 原生推送到达后也会转换为同一份通知载荷，再复用这一展示入口。
export function presentMentorConsultationNotification(notice) {
  const normalized = normalizeNotice(notice)
  if (!normalized || queuedNoticeKeys.has(normalized.key)) return
  queuedNoticeKeys.add(normalized.key)
  noticeQueue.push(normalized)
  showNextNotice()
}

export async function refreshMentorConsultationNotifications() {
  if (polling) return
  const userId = getCurrentUserId()
  if (!userId || !isLoggedIn()) {
    resetMentorNotificationSession()
    return
  }

  if (activeUserId && activeUserId !== userId) resetMentorNotificationSession()
  activeUserId = userId
  polling = true

  try {
    const mentorId = await getVerifiedMentorId(userId)
    if (!mentorId) return

    const response = await fetchUserNotifications({ category: 'consultation', limit: 50 })
    const notifications = Array.isArray(response?.items) ? response.items : []
    notifications.forEach((notification) => {
      const notice = createOrderNotice(notification)
      if (!notice || notification.read || !isFreshNotice(notification) || hasSeenNotice(notice.key, userId)) return
      rememberNotice(notice.key, userId)
      presentMentorConsultationNotification(notice)
    })
  } catch (error) {
    // 网络短暂波动时保留当前已确认的前辈身份，下次轮询自动重试。
  } finally {
    polling = false
  }
}

async function getVerifiedMentorId(userId) {
  const now = Date.now()
  if (mentorRoleResolved && now - lastRoleCheckAt < ROLE_RECHECK_INTERVAL_MS) return verifiedMentorId

  lastRoleCheckAt = now
  try {
    const payload = await fetchMyMentorProfile()
    const mentor = payload?.mentor || null
    const mentorId = String(mentor?.id || '').trim()
    if (!mentorId || mentor?.verified !== true) {
      verifiedMentorId = ''
      mentorRoleResolved = true
      return ''
    }
    verifiedMentorId = mentorId
    mentorRoleResolved = true
    return mentorId
  } catch (error) {
    if (Number(error?.statusCode) === 404) {
      verifiedMentorId = ''
      mentorRoleResolved = true
    }
    return verifiedMentorId
  }
}

function createOrderNotice(notification = {}) {
  const notificationId = String(notification?.id || '').trim()
  const notificationType = String(notification?.notification_type || notification?.notificationType || '').trim()
  if (!notificationId || notificationType !== MENTOR_ORDER_NOTIFICATION_TYPE) return null

  const payload = notification?.delivery_payload && typeof notification.delivery_payload === 'object'
    ? notification.delivery_payload
    : (notification?.deliveryPayload && typeof notification.deliveryPayload === 'object' ? notification.deliveryPayload : {})
  const orderId = String(payload.order_id || notification?.related_id || notification?.relatedId || '').trim()
  const consultationType = String(payload.consultation_type || 'instant').trim()
  const expiresAt = String(payload.expires_at || '').trim()
  const expiresTimestamp = Date.parse(expiresAt)
  if (!orderId || (consultationType === 'instant' && Number.isFinite(expiresTimestamp) && expiresTimestamp <= Date.now())) return null

  const nativePush = payload.native_push && typeof payload.native_push === 'object' ? payload.native_push : {}
  return {
    key: `notification:${notificationId}`,
    notificationId,
    orderId,
    routePath: String(notification?.route_path || notification?.routePath || nativePush.route_path || '').trim(),
    title: String(nativePush.title || notification?.title || '新的咨询通知').trim(),
    content: String(nativePush.body || notification?.content || notification?.summary || '你有一条新的咨询请求，请点击查看。').trim()
  }
}

function normalizeNotice(notice = {}) {
  const key = String(notice?.key || '').trim()
  const orderId = String(notice?.orderId || '').trim()
  if (!key || !orderId) return null
  return {
    key,
    orderId,
    notificationId: String(notice?.notificationId || '').trim(),
    routePath: String(notice?.routePath || '').trim(),
    title: String(notice?.title || '新的咨询通知').trim() || '新的咨询通知',
    content: String(notice?.content || '你有一条新的咨询请求，请点击查看。').trim()
  }
}

function isFreshNotice(notification = {}) {
  const timeValue = notification?.created_at || notification?.createdAt || ''
  const timestamp = Date.parse(String(timeValue || ''))
  return !Number.isFinite(timestamp) || (Date.now() >= timestamp && Date.now() - timestamp <= NOTICE_EVENT_MAX_AGE_MS)
}

function getCurrentUserId() {
  const user = getAuthUser() || {}
  return String(user.id || user.user_id || user.userId || '').trim()
}

function getSeenStorageKey(userId) {
  return userId ? `${NOTICE_SEEN_STORAGE_PREFIX}:${userId}` : ''
}

function readSeenNotices(userId) {
  const storageKey = getSeenStorageKey(userId)
  if (!storageKey) return {}
  try {
    const stored = uni.getStorageSync(storageKey)
    const now = Date.now()
    const entries = Object.entries(stored && typeof stored === 'object' ? stored : {})
      .filter(([key, timestamp]) => key && Number(timestamp) > now - NOTICE_SEEN_TTL_MS)
      .slice(-NOTICE_SEEN_MAX_ENTRIES)
    return Object.fromEntries(entries)
  } catch (error) {
    return {}
  }
}

function hasSeenNotice(key, userId) {
  return Boolean(readSeenNotices(userId)[key])
}

function rememberNotice(key, userId) {
  const storageKey = getSeenStorageKey(userId)
  if (!storageKey || !key) return
  try {
    const next = {
      ...readSeenNotices(userId),
      [key]: Date.now()
    }
    const compact = Object.fromEntries(
      Object.entries(next)
        .sort((left, right) => Number(left[1]) - Number(right[1]))
        .slice(-NOTICE_SEEN_MAX_ENTRIES)
    )
    uni.setStorageSync(storageKey, compact)
  } catch (error) {
    // 本地去重缓存失败不影响订单本身，下一次轮询仍会继续检查。
  }
}

function showNextNotice() {
  if (activeNotice || noticeLeaving) return
  const nextNotice = noticeQueue.shift()
  if (!nextNotice) return

  activeNotice = nextNotice
  const host = ensureNoticeHost()
  if (!host) {
    showFallbackNotice(nextNotice)
    finishActiveNotice()
    return
  }

  updateNoticeHost(host, nextNotice)
  host.classList.remove('is-leaving')
  requestFrame(() => host.classList.add('is-visible'))
  clearNoticeTimers()
  noticeTimer = setTimeout(() => dismissActiveNotice(), NOTICE_VISIBLE_MS)
}

function dismissActiveNotice({ openOrder = false } = {}) {
  if (!activeNotice || noticeLeaving) return
  const notice = activeNotice
  if (openOrder) {
    void markNoticeAsRead(notice)
    openMentorOrder(notice)
  }

  clearNoticeTimers()
  noticeLeaving = true
  if (!noticeHost) {
    finishActiveNotice()
    return
  }

  noticeHost.classList.remove('is-visible')
  noticeHost.classList.add('is-leaving')
  noticeLeaveTimer = setTimeout(() => {
    if (activeNotice !== notice) return
    finishActiveNotice()
  }, NOTICE_LEAVE_MS)
}

function finishActiveNotice() {
  clearNoticeTimers()
  if (activeNotice?.key) queuedNoticeKeys.delete(activeNotice.key)
  activeNotice = null
  noticeLeaving = false
  if (noticeHost) noticeHost.classList.remove('is-visible', 'is-leaving')
  showNextNotice()
}

function clearNoticeTimers() {
  if (noticeTimer !== null) {
    clearTimeout(noticeTimer)
    noticeTimer = null
  }
  if (noticeLeaveTimer !== null) {
    clearTimeout(noticeLeaveTimer)
    noticeLeaveTimer = null
  }
}

function resetMentorNotificationSession() {
  activeUserId = ''
  verifiedMentorId = ''
  lastRoleCheckAt = 0
  mentorRoleResolved = false
  noticeQueue = []
  queuedNoticeKeys.clear()
  clearNoticeTimers()
  activeNotice = null
  noticeLeaving = false
  if (noticeHost) noticeHost.classList.remove('is-visible', 'is-leaving')
}

function ensureNoticeHost() {
  if (typeof document === 'undefined' || !document.body) return null
  if (noticeHost?.isConnected) return noticeHost

  injectNoticeStyles()
  const existing = document.getElementById(NOTICE_HOST_ID)
  if (existing) {
    noticeHost = existing
    return noticeHost
  }

  const host = document.createElement('div')
  host.id = NOTICE_HOST_ID
  host.className = 'gyt-mentor-notice-host'
  host.setAttribute('aria-live', 'polite')

  const card = document.createElement('button')
  card.type = 'button'
  card.className = 'gyt-mentor-notice-card'
  card.setAttribute('aria-label', '查看新的咨询通知')
  card.addEventListener('click', () => dismissActiveNotice({ openOrder: true }))

  const icon = document.createElement('span')
  icon.className = 'gyt-mentor-notice-icon'
  icon.textContent = '咨'

  const content = document.createElement('span')
  content.className = 'gyt-mentor-notice-content'
  const eyebrow = document.createElement('span')
  eyebrow.className = 'gyt-mentor-notice-eyebrow'
  eyebrow.textContent = '港研通 · 前辈咨询'
  const title = document.createElement('strong')
  title.className = 'gyt-mentor-notice-title'
  const copy = document.createElement('span')
  copy.className = 'gyt-mentor-notice-copy'
  content.append(eyebrow, title, copy)

  const arrow = document.createElement('span')
  arrow.className = 'gyt-mentor-notice-arrow'
  arrow.textContent = '›'
  card.append(icon, content, arrow)
  host.appendChild(card)
  document.body.appendChild(host)
  noticeHost = host
  return host
}

function updateNoticeHost(host, notice) {
  const title = host.querySelector('.gyt-mentor-notice-title')
  const copy = host.querySelector('.gyt-mentor-notice-copy')
  if (title) title.textContent = notice.title
  if (copy) copy.textContent = notice.content
}

function injectNoticeStyles() {
  if (typeof document === 'undefined' || document.getElementById(NOTICE_STYLE_ID)) return
  const style = document.createElement('style')
  style.id = NOTICE_STYLE_ID
  style.textContent = `
    .gyt-mentor-notice-host { position: fixed; z-index: 2147483600; top: calc(env(safe-area-inset-top) + 12px); right: 12px; left: 12px; pointer-events: none; }
    .gyt-mentor-notice-card { box-sizing: border-box; width: 100%; min-height: 76px; margin: 0; padding: 11px 13px; border: 1px solid rgba(215, 229, 255, .92); border-radius: 20px; background: rgba(255, 255, 255, .96); color: #263650; display: flex; align-items: center; gap: 11px; overflow: hidden; text-align: left; opacity: 0; pointer-events: auto; transform: translate3d(0, -128%, 0); box-shadow: 0 14px 32px rgba(52, 120, 246, .16); -webkit-backdrop-filter: blur(18px) saturate(116%); backdrop-filter: blur(18px) saturate(116%); -webkit-tap-highlight-color: transparent; }
    .gyt-mentor-notice-host.is-visible .gyt-mentor-notice-card { animation: gyt-mentor-notice-enter 280ms cubic-bezier(.22,.9,.32,1) both; }
    .gyt-mentor-notice-host.is-leaving .gyt-mentor-notice-card { animation: gyt-mentor-notice-leave 240ms cubic-bezier(.4,0,1,1) both; }
    .gyt-mentor-notice-icon { width: 42px; height: 42px; border-radius: 14px; background: #eaf2ff; color: #3478f6; display: flex; align-items: center; justify-content: center; font-size: 18px; line-height: 1; font-weight: 800; flex: 0 0 42px; }
    .gyt-mentor-notice-content { min-width: 0; flex: 1; display: block; }
    .gyt-mentor-notice-eyebrow, .gyt-mentor-notice-copy { display: block; overflow: hidden; color: #7f90a8; font-size: 12px; line-height: 1.35; font-weight: 500; text-overflow: ellipsis; white-space: nowrap; }
    .gyt-mentor-notice-title { display: block; margin-top: 2px; color: #24344f; font-size: 16px; line-height: 1.3; font-weight: 800; }
    .gyt-mentor-notice-copy { margin-top: 2px; }
    .gyt-mentor-notice-arrow { color: #7090bf; font-size: 29px; line-height: 1; font-weight: 400; }
    @keyframes gyt-mentor-notice-enter { from { opacity: 0; transform: translate3d(0, -128%, 0); } to { opacity: 1; transform: translate3d(0, 0, 0); } }
    @keyframes gyt-mentor-notice-leave { from { opacity: 1; transform: translate3d(0, 0, 0); } to { opacity: 0; transform: translate3d(0, -128%, 0); } }
    @media (prefers-reduced-motion: reduce) { .gyt-mentor-notice-host.is-visible .gyt-mentor-notice-card, .gyt-mentor-notice-host.is-leaving .gyt-mentor-notice-card { animation-duration: 1ms; } }
  `
  document.head?.appendChild(style)
}

function requestFrame(callback) {
  if (typeof requestAnimationFrame === 'function') {
    requestAnimationFrame(callback)
    return
  }
  setTimeout(callback, 0)
}

function showFallbackNotice(notice) {
  if (typeof uni === 'undefined' || typeof uni.showToast !== 'function') return
  uni.showToast({ title: notice.title, icon: 'none', duration: NOTICE_VISIBLE_MS })
}

async function markNoticeAsRead(notice = {}) {
  const notificationId = String(notice.notificationId || '').trim()
  if (!notificationId) return
  try {
    await markUserNotificationRead(notificationId)
  } catch (error) {
    // 跳转不应被已读状态的短暂网络失败阻塞；消息中心下次同步后会恢复真实状态。
  }
}

function openMentorOrder(notice = {}) {
  const orderId = String(notice.orderId || '').trim()
  if (!orderId || typeof uni === 'undefined') return
  const preferredRoute = String(notice.routePath || '').trim()
  const url = preferredRoute.startsWith('/pages/')
    ? preferredRoute
    : `/pages-sub-consultation/consultation/mentor-apply?mode=center&orderId=${encodeURIComponent(orderId)}`
  uni.navigateTo({
    url,
    fail() {
      uni.redirectTo({
        url,
        fail() {
          uni.reLaunch({ url })
        }
      })
    }
  })
}
