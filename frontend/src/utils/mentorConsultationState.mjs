const TERMINAL_STATUS_LABELS = {
  completed: '已完成',
  rejected: '已拒绝',
  timeout: '已超时',
  refunded: '已退款',
  cancelled: '已取消'
}

const BASE_STATUS_LABELS = {
  draft: '草稿',
  pending_payment: '待支付',
  pending_accept: '待接单',
  accepted: '已接受',
  booked: '已预约',
  in_progress: '咨询中',
  ...TERMINAL_STATUS_LABELS
}

const TERMINAL_ORDER_STATUSES = new Set(Object.keys(TERMINAL_STATUS_LABELS))

function parseTimestamp(value) {
  const timestamp = Date.parse(String(value || ''))
  return Number.isFinite(timestamp) ? timestamp : Number.NaN
}

function normalizeViewerRole(value) {
  return value === 'mentor' ? 'mentor' : 'applicant'
}

function normalizeLocalNow(value) {
  const timestamp = Number(value)
  return Number.isFinite(timestamp) ? timestamp : Date.now()
}

export function resolveMentorConsultationServiceEndTimestamp(order = {}) {
  const explicitServiceEnd = parseTimestamp(order.serviceEndsAt || order.service_ends_at)
  if (Number.isFinite(explicitServiceEnd)) return explicitServiceEnd

  const status = String(order.orderStatus || order.order_status || '')
  const startedAt = parseTimestamp(order.startedAt || order.started_at)
  const legacyStartedAt = status === 'in_progress'
    ? parseTimestamp(order.acceptedAt || order.accepted_at || order.createdAt || order.created_at)
    : Number.NaN
  const serviceStart = Number.isFinite(startedAt) ? startedAt : legacyStartedAt
  if (!Number.isFinite(serviceStart)) return Number.NaN

  const rawMinutes = Number(order.consultationWindowMinutes ?? order.consultation_window_minutes ?? 60)
  const windowMinutes = Math.max(15, Math.min(180, Number.isFinite(rawMinutes) ? rawMinutes : 60))
  return serviceStart + windowMinutes * 60 * 1000
}

export function resolveMentorConsultationReferenceNow(order = {}, localNow = Date.now()) {
  const now = normalizeLocalNow(localNow)
  const offset = Number(order.serverClockOffsetMs ?? order.server_clock_offset_ms)
  return now + (Number.isFinite(offset) ? offset : 0)
}

export function isMentorConsultationServiceExpired(order = {}, localNow = Date.now()) {
  if (String(order.orderStatus || order.order_status || '') !== 'in_progress') return false
  const serviceEnd = resolveMentorConsultationServiceEndTimestamp(order)
  return Number.isFinite(serviceEnd)
    && serviceEnd <= resolveMentorConsultationReferenceNow(order, localNow)
}

export function mergeMentorConsultationStopState(baseOrder = {}, stopEvidenceOrder = {}) {
  if (!baseOrder || typeof baseOrder !== 'object') return stopEvidenceOrder
  if (!stopEvidenceOrder || typeof stopEvidenceOrder !== 'object') return baseOrder

  const baseOrderId = String(baseOrder.id || baseOrder.orderId || baseOrder.order_id || '')
  const evidenceOrderId = String(stopEvidenceOrder.id || stopEvidenceOrder.orderId || stopEvidenceOrder.order_id || '')
  if (baseOrderId && evidenceOrderId && baseOrderId !== evidenceOrderId) return baseOrder

  const baseStatus = String(baseOrder.orderStatus || baseOrder.order_status || '')
  const evidenceStatus = String(stopEvidenceOrder.orderStatus || stopEvidenceOrder.order_status || '')
  let nextOrder = baseOrder

  const assignIfChanged = (field, value) => {
    if (value === undefined || value === null || value === '' || nextOrder[field] === value) return
    if (nextOrder === baseOrder) nextOrder = { ...baseOrder }
    nextOrder[field] = value
  }
  const assignIfMissing = (field, value) => {
    if (nextOrder[field] !== undefined && nextOrder[field] !== null && nextOrder[field] !== '') return
    assignIfChanged(field, value)
  }

  if (TERMINAL_ORDER_STATUSES.has(evidenceStatus) && !TERMINAL_ORDER_STATUSES.has(baseStatus)) {
    assignIfChanged('orderStatus', evidenceStatus)
  }

  assignIfMissing(
    'applicantCompletionConfirmedAt',
    stopEvidenceOrder.applicantCompletionConfirmedAt || stopEvidenceOrder.applicant_completion_confirmed_at
  )
  assignIfMissing(
    'mentorCompletionConfirmedAt',
    stopEvidenceOrder.mentorCompletionConfirmedAt || stopEvidenceOrder.mentor_completion_confirmed_at
  )
  assignIfMissing('endedAt', stopEvidenceOrder.endedAt || stopEvidenceOrder.ended_at)
  assignIfMissing('startedAt', stopEvidenceOrder.startedAt || stopEvidenceOrder.started_at)
  assignIfMissing('serviceEndsAt', stopEvidenceOrder.serviceEndsAt || stopEvidenceOrder.service_ends_at)

  return nextOrder
}

export function getMentorConsultationOrderUiState(
  order = {},
  { viewerRole = 'applicant', now = Date.now() } = {}
) {
  const status = String(order.orderStatus || order.order_status || '')
  const normalizedViewerRole = normalizeViewerRole(viewerRole)
  const applicantConfirmed = Boolean(
    order.applicantCompletionConfirmedAt || order.applicant_completion_confirmed_at
  )
  const mentorConfirmed = Boolean(
    order.mentorCompletionConfirmedAt || order.mentor_completion_confirmed_at
  )
  const viewerConfirmed = normalizedViewerRole === 'mentor' ? mentorConfirmed : applicantConfirmed
  const otherPartyConfirmed = normalizedViewerRole === 'mentor' ? applicantConfirmed : mentorConfirmed
  const serviceExpired = isMentorConsultationServiceExpired(order, now)

  if (status === 'completed') {
    return createUiState('completed', '已完成', 'history', '查看聊天记录', { serviceExpired: true })
  }

  if (status === 'in_progress') {
    if (serviceExpired && Boolean(order.autoCompletionBlockedByDispute ?? order.auto_completion_blocked_by_dispute)) {
      return createUiState('platform_processing', '平台处理中', 'history', '查看聊天记录', {
        serviceExpired,
        viewerConfirmed,
        otherPartyConfirmed
      })
    }
    if (serviceExpired || (applicantConfirmed && mentorConfirmed)) {
      return createUiState('ending', '正在结束', 'history', '查看聊天记录', {
        serviceExpired,
        viewerConfirmed,
        otherPartyConfirmed
      })
    }
    if (otherPartyConfirmed && !viewerConfirmed) {
      return createUiState('awaiting_viewer_confirmation', '待你确认', 'history', '查看并处理', {
        viewerConfirmed,
        otherPartyConfirmed
      })
    }
    if (viewerConfirmed) {
      return createUiState('viewer_confirmed', '已确认结束', 'history', '查看结束状态', {
        viewerConfirmed,
        otherPartyConfirmed
      })
    }
    return createUiState('in_progress', '咨询中', 'enter', '进入咨询')
  }

  if (status === 'accepted' || status === 'booked') {
    return createUiState(status, BASE_STATUS_LABELS[status], 'start', '开始咨询')
  }

  const startedAt = parseTimestamp(order.startedAt || order.started_at)
  if (Number.isFinite(startedAt) && ['cancelled', 'refunded', 'timeout'].includes(status)) {
    return createUiState(status, TERMINAL_STATUS_LABELS[status], 'history', '查看聊天记录')
  }

  return createUiState(status || 'unknown', BASE_STATUS_LABELS[status] || '处理中', 'none', '')
}

function createUiState(phase, statusLabel, action, actionLabel, extra = {}) {
  return {
    phase,
    statusClass: phase,
    statusLabel,
    action,
    actionLabel,
    canOpenChat: action === 'enter' || action === 'history',
    canStartService: action === 'start',
    isLiveChat: action === 'enter',
    ...extra
  }
}
