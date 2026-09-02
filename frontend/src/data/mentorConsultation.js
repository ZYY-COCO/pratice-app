import { getAuthUser } from '../utils/auth'

export const MENTOR_SORT_OPTIONS = [
  { value: 'recommended', label: '综合推荐' },
  { value: 'consult_count', label: '咨询最多' },
  { value: 'rating', label: '评分最高' },
  { value: 'price', label: '价格最低' }
]

export const MENTOR_SCHOOL_OPTIONS = ['暨南大学', '中山大学', '华南理工大学', '厦门大学', '浙江大学', '北京师范大学', '复旦大学', '武汉大学']
export const MENTOR_MAJOR_OPTIONS = ['应用经济学', '金融学', '国际商务', '工商管理', '计算机科学与技术', '教育学', '中国语言文学', '法学']
export const MENTOR_EXAM_TYPE_OPTIONS = ['不限', 'Z001', 'Z002']
export const MENTOR_ADMISSION_YEAR_OPTIONS = ['不限', '2026', '2025', '2024', '更早']
export const MENTOR_PRICE_OPTIONS = ['不限', '≤30元', '30–50元', '50–100元', '100元以上']
export const MENTOR_AVAILABILITY_OPTIONS = ['不限', '在线', '可预约']
export const MENTOR_GRADE_OPTIONS = ['大一', '大二', '大三', '大四', '大五', '研究生', '已毕业', '其他']
export const MENTOR_SKILL_OPTIONS = ['院校选择', '专业选择', 'Z001备考', 'Z002备考', '英语备考', '复试经验', '学习规划', '其他']

export const CONSULT_ORDER_STATUSES = ['draft', 'pending_payment', 'pending_accept', 'accepted', 'in_progress', 'completed', 'rejected', 'timeout', 'refunded', 'cancelled', 'booked']
export const MENTOR_VERIFICATION_STATUSES = ['unverified', 'pending', 'verified', 'rejected']

const FAVORITE_STORAGE_KEY = 'circle-mentor-favorite-ids-v1'
const CONSULT_DRAFT_STORAGE_KEY = 'circle-mentor-consult-draft-v1'
const VERIFICATION_STORAGE_KEY = 'circle-mentor-verification-v1'
const APPLICATION_STORAGE_KEY = 'circle-mentor-application-v1'
const MENTOR_CACHE_STORAGE_KEY = 'circle-mentor-directory-v2'

let mentorCache = []

export function createDefaultMentorFilters() {
  return {
    examType: '不限',
    admissionYear: '不限',
    price: '不限',
    availability: '不限'
  }
}

export function maskMentorName(name = '') {
  const normalized = String(name).trim()
  if (normalized.length <= 1) return normalized
  if (normalized.length === 2) return `${normalized.slice(0, 1)}*`
  return `${normalized.slice(0, 1)}*${normalized.slice(-1)}`
}

export function normalizeMentorListResponse(payload = {}) {
  const items = Array.isArray(payload) ? payload : payload?.items
  return (Array.isArray(items) ? items : []).map((item) => normalizeMentorRecord(item))
}

export function normalizeMentorDetailResponse(payload = {}) {
  const rawMentor = payload?.mentor || payload
  if (!rawMentor?.id) return null
  return normalizeMentorRecord(rawMentor, {
    reviews: payload?.reviews,
    availableSlots: payload?.available_slots ?? payload?.availableSlots
  })
}

export function cacheMentors(mentors = [], { replace = false } = {}) {
  const normalizedMentors = (Array.isArray(mentors) ? mentors : [])
    .map((mentor) => normalizeMentorRecord(mentor))
    .filter((mentor) => mentor.id)

  if (replace) {
    mentorCache = normalizedMentors
  } else {
    const merged = new Map(getCachedMentors().map((mentor) => [mentor.id, mentor]))
    normalizedMentors.forEach((mentor) => {
      merged.set(mentor.id, { ...(merged.get(mentor.id) || {}), ...mentor })
    })
    mentorCache = [...merged.values()]
  }
  writeStorage(MENTOR_CACHE_STORAGE_KEY, mentorCache)
  return clone(mentorCache)
}

// 目录缓存用于先回填上一次成功获取的公开前辈资料，再在后台刷新真实数据。
export function getCachedMentorDirectory() {
  return clone(getCachedMentors())
}

export function getMentorById(id) {
  const mentorId = String(id || '')
  if (!mentorId) return null
  const cachedMentor = getCachedMentors().find((item) => item.id === mentorId)
  return cachedMentor ? withMentorDisplayFields(clone(cachedMentor)) : null
}

export function searchMentorSchools(keyword = '') {
  const normalized = normalize(keyword)
  if (!normalized) return []
  return MENTOR_SCHOOL_OPTIONS.filter((item) => normalize(item).includes(normalized)).slice(0, 6)
}

export function searchMentorMajors(keyword = '') {
  const normalized = normalize(keyword)
  if (!normalized) return []
  return MENTOR_MAJOR_OPTIONS.filter((item) => normalize(item).includes(normalized)).slice(0, 6)
}

export function filterMentors({ mentors, keyword = '', filters = createDefaultMentorFilters(), sort = 'recommended' } = {}) {
  const sourceMentors = Array.isArray(mentors) ? mentors : []
  const activeFilters = { ...createDefaultMentorFilters(), ...(filters || {}) }
  const keywordTokens = splitMentorSearchTokens(keyword)
  const searchedMentors = sourceMentors
    .map((mentor) => withMentorDisplayFields(mentor))
    .filter((mentor) => matchesMentorKeyword(mentor, keywordTokens))
  const filteredMentors = searchedMentors.filter((mentor) => {
    if (activeFilters.examType !== '不限' && mentor.examType !== activeFilters.examType) return false
    if (activeFilters.admissionYear === '更早' && Number(mentor.admissionYear) > 2023) return false
    if (activeFilters.admissionYear !== '不限' && activeFilters.admissionYear !== '更早' && mentor.admissionYear !== activeFilters.admissionYear) return false
    if (!matchesMentorPrice(mentor.price, activeFilters.price)) return false
    if (activeFilters.availability === '在线' && getMentorStatus(mentor) !== 'online') return false
    if (activeFilters.availability === '可预约' && !isMentorBookable(mentor)) return false
    return true
  })

  return [...filteredMentors].sort((left, right) => {
    if (sort === 'consult_count') return right.consultCount - left.consultCount || right.rating - left.rating
    if (sort === 'rating') return right.rating - left.rating || right.consultCount - left.consultCount
    if (sort === 'price') return left.price - right.price || right.rating - left.rating
    return right.recommendScore - left.recommendScore
      || Number(right.featured) - Number(left.featured)
      || right.rating - left.rating
      || right.consultCount - left.consultCount
  })
}

export function getMentorAvailabilityLabel(mentor = {}) {
  if (getMentorStatus(mentor) === 'online') return '在线'
  return mentor.acceptsBooking === false ? '暂不可预约' : '可预约'
}

export function getMentorActionLabel(mentor = {}) {
  if (getMentorStatus(mentor) === 'online') return '立即咨询'
  return mentor.acceptsBooking === false ? '查看详情' : '预约咨询'
}

export function formatMentorPrice(price) {
  const value = Number(price || 0)
  return `¥${Number.isInteger(value) ? value : value.toFixed(2)}`
}

export function getMentorFavoriteIds() {
  const stored = readUserStorage(FAVORITE_STORAGE_KEY, [])
  return Array.isArray(stored) ? stored.map(String) : []
}

export function setMentorFavoriteIds(ids = []) {
  const next = [...new Set((Array.isArray(ids) ? ids : []).map((id) => String(id || '')).filter(Boolean))]
  writeUserStorage(FAVORITE_STORAGE_KEY, next)
  return next
}

export function toggleMentorFavorite(mentorId) {
  const id = String(mentorId || '')
  if (!id) return getMentorFavoriteIds()
  const favoriteIds = getMentorFavoriteIds()
  const next = favoriteIds.includes(id)
    ? favoriteIds.filter((item) => item !== id)
    : [...favoriteIds, id]
  return setMentorFavoriteIds(next)
}

export function startConsultationDraft({ mentorId, consultationType = 'instant', bookingSlot = null } = {}) {
  const mentor = getMentorById(mentorId)
  if (!mentor) return null
  const draft = {
    mentorId: mentor.id,
    clientOrderId: createClientOrderId(),
    consultationType: consultationType === 'booking' ? 'booking' : 'instant',
    bookingSlot: bookingSlot ? clone(bookingSlot) : null,
    questionnaire: createDefaultConsultationQuestionnaire(),
    orderId: '',
    orderNo: '',
    orderStatus: 'draft',
    paymentStatus: 'unpaid',
    paymentProvider: '',
    paymentCheckoutUrl: '',
    paymentMessage: '',
    price: bookingSlot?.price || mentor.price || 0,
    consultationWindowMinutes: mentor.consultationWindowMinutes || 60,
    expiresAt: '',
    acceptedAt: '',
    startedAt: '',
    endedAt: '',
    messages: [],
    createdAt: Date.now()
  }
  writeUserStorage(CONSULT_DRAFT_STORAGE_KEY, draft)
  return clone(draft)
}

export function getConsultationDraft() {
  const draft = readUserStorage(CONSULT_DRAFT_STORAGE_KEY, null)
  if (!draft || typeof draft !== 'object') return null
  const normalized = {
        ...draft,
        clientOrderId: String(draft.clientOrderId || createClientOrderId()),
        orderId: String(draft.orderId || ''),
        orderNo: String(draft.orderNo || ''),
        orderStatus: String(draft.orderStatus || 'draft'),
        paymentStatus: String(draft.paymentStatus || 'unpaid'),
        paymentProvider: String(draft.paymentProvider || ''),
        paymentCheckoutUrl: String(draft.paymentCheckoutUrl || ''),
        paymentMessage: String(draft.paymentMessage || ''),
        questionnaire: { ...createDefaultConsultationQuestionnaire(), ...(draft.questionnaire || {}) }
      }
  if (!draft.clientOrderId) writeUserStorage(CONSULT_DRAFT_STORAGE_KEY, normalized)
  return normalized
}

export function saveConsultationQuestionnaire(questionnaire = {}) {
  const draft = getConsultationDraft()
  if (!draft) return null
  const next = {
    ...draft,
    questionnaire: { ...createDefaultConsultationQuestionnaire(), ...questionnaire },
    orderStatus: 'pending_payment'
  }
  writeUserStorage(CONSULT_DRAFT_STORAGE_KEY, next)
  return clone(next)
}

export function normalizeMentorConsultationOrder(rawOrder = {}) {
  const questionnaire = rawOrder.questionnaire && typeof rawOrder.questionnaire === 'object'
    ? rawOrder.questionnaire
    : {}
  return {
    id: String(rawOrder.id || ''),
    orderNo: String(rawOrder.orderNo || rawOrder.order_no || ''),
    clientOrderId: String(rawOrder.clientOrderId || rawOrder.client_order_id || ''),
    mentorId: String(rawOrder.mentorId || rawOrder.mentor_id || ''),
    slotId: rawOrder.slotId || rawOrder.slot_id ? String(rawOrder.slotId || rawOrder.slot_id) : '',
    consultationType: String(rawOrder.consultationType || rawOrder.consultation_type || 'instant'),
    orderStatus: String(rawOrder.orderStatus || rawOrder.order_status || 'draft'),
    paymentStatus: String(rawOrder.paymentStatus || rawOrder.payment_status || 'unpaid'),
    paymentProvider: String(rawOrder.paymentProvider || rawOrder.payment_provider || ''),
    paymentCheckoutUrl: String(rawOrder.paymentCheckoutUrl || rawOrder.payment_checkout_url || rawOrder.checkout_url || ''),
    paymentMessage: String(rawOrder.paymentMessage || rawOrder.payment_message || rawOrder.message || ''),
    price: toNumber(rawOrder.price ?? (rawOrder.price_cents == null ? 0 : rawOrder.price_cents / 100)),
    consultationWindowMinutes: toNumber(rawOrder.consultationWindowMinutes ?? rawOrder.consultation_window_minutes, 60),
    paymentReference: String(rawOrder.paymentReference || rawOrder.payment_reference || ''),
    paymentExpiresAt: String(rawOrder.paymentExpiresAt || rawOrder.payment_expires_at || ''),
    paymentMode: String(rawOrder.paymentMode || rawOrder.payment_mode || 'real'),
    acceptedAt: String(rawOrder.acceptedAt || rawOrder.accepted_at || ''),
    expiresAt: String(rawOrder.expiresAt || rawOrder.expires_at || ''),
    startedAt: String(rawOrder.startedAt || rawOrder.started_at || ''),
    endedAt: String(rawOrder.endedAt || rawOrder.ended_at || ''),
    applicantCompletionConfirmedAt: String(rawOrder.applicantCompletionConfirmedAt || rawOrder.applicant_completion_confirmed_at || ''),
    mentorCompletionConfirmedAt: String(rawOrder.mentorCompletionConfirmedAt || rawOrder.mentor_completion_confirmed_at || ''),
    refundAmount: toNumber(rawOrder.refundAmount ?? rawOrder.refund_amount ?? (rawOrder.refund_amount_cents == null ? 0 : rawOrder.refund_amount_cents / 100)),
    refundReference: String(rawOrder.refundReference || rawOrder.refund_reference || ''),
    rejectionReason: String(rawOrder.rejectionReason || rawOrder.rejection_reason || ''),
    createdAt: String(rawOrder.createdAt || rawOrder.created_at || ''),
    updatedAt: String(rawOrder.updatedAt || rawOrder.updated_at || ''),
    questionnaire: {
      ...createDefaultConsultationQuestionnaire(),
      name: String(questionnaire.name || ''),
      school: String(questionnaire.school || ''),
      major: String(questionnaire.major || ''),
      grade: String(questionnaire.grade || '其他'),
      graduationYear: questionnaire.graduationYear ?? questionnaire.graduation_year ?? '',
      question: String(questionnaire.question || '')
    }
  }
}

export function saveConsultationOrder(order = {}) {
  const normalizedOrder = normalizeMentorConsultationOrder(order)
  const current = getConsultationDraft()
  const next = {
    ...(current || {}),
    mentorId: normalizedOrder.mentorId || current?.mentorId || '',
    consultationType: normalizedOrder.consultationType || current?.consultationType || 'instant',
    orderId: normalizedOrder.id,
    orderNo: normalizedOrder.orderNo,
    clientOrderId: normalizedOrder.clientOrderId || current?.clientOrderId || createClientOrderId(),
    orderStatus: normalizedOrder.orderStatus,
    paymentStatus: normalizedOrder.paymentStatus,
    paymentReference: normalizedOrder.paymentReference || current?.paymentReference || '',
    paymentExpiresAt: normalizedOrder.paymentExpiresAt,
    paymentMode: normalizedOrder.paymentMode,
    paymentProvider: normalizedOrder.paymentProvider || current?.paymentProvider || '',
    paymentCheckoutUrl: normalizedOrder.paymentCheckoutUrl || current?.paymentCheckoutUrl || '',
    paymentMessage: normalizedOrder.paymentMessage || current?.paymentMessage || '',
    price: normalizedOrder.price,
    consultationWindowMinutes: normalizedOrder.consultationWindowMinutes,
    expiresAt: normalizedOrder.expiresAt,
    acceptedAt: normalizedOrder.acceptedAt,
    startedAt: normalizedOrder.startedAt,
    endedAt: normalizedOrder.endedAt,
    applicantCompletionConfirmedAt: normalizedOrder.applicantCompletionConfirmedAt,
    mentorCompletionConfirmedAt: normalizedOrder.mentorCompletionConfirmedAt,
    refundAmount: normalizedOrder.refundAmount,
    refundReference: normalizedOrder.refundReference,
    rejectionReason: normalizedOrder.rejectionReason,
    questionnaire: normalizedOrder.questionnaire,
    updatedAt: Date.now()
  }
  writeUserStorage(CONSULT_DRAFT_STORAGE_KEY, next)
  return clone(next)
}

export function setConsultationOrderStatus(status) {
  const draft = getConsultationDraft()
  const nextStatus = CONSULT_ORDER_STATUSES.includes(status) ? status : 'draft'
  if (!draft) return null
  const next = { ...draft, orderStatus: nextStatus, updatedAt: Date.now() }
  writeUserStorage(CONSULT_DRAFT_STORAGE_KEY, next)
  return clone(next)
}

function createClientOrderId() {
  try {
    if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
      return `mco_${crypto.randomUUID()}`
    }
  } catch (error) {
    // 小程序或旧 WebView 不支持 randomUUID 时使用时间戳与随机片段。
  }
  return `mco_${Date.now()}_${Math.random().toString(36).slice(2, 12)}`
}

export function appendConsultationMessage(message) {
  const draft = getConsultationDraft()
  if (!draft) return null
  const messages = Array.isArray(draft.messages) ? draft.messages : []
  const next = {
    ...draft,
    messages: [...messages, { id: `message-${Date.now()}-${messages.length}`, createdAt: Date.now(), ...message }]
  }
  writeUserStorage(CONSULT_DRAFT_STORAGE_KEY, next)
  return clone(next)
}

export function resetConsultationDraft() {
  removeUserStorage(CONSULT_DRAFT_STORAGE_KEY)
}

export function createDefaultConsultationQuestionnaire() {
  return {
    name: '',
    school: '',
    major: '',
    grade: '大三',
    graduationYear: '2027',
    question: ''
  }
}

export function getMentorVerificationStatus() {
  const status = String(readUserStorage(VERIFICATION_STORAGE_KEY, 'unverified') || 'unverified')
  return MENTOR_VERIFICATION_STATUSES.includes(status) ? status : 'unverified'
}

export function setMentorVerificationStatus(status) {
  const next = MENTOR_VERIFICATION_STATUSES.includes(status) ? status : 'unverified'
  writeUserStorage(VERIFICATION_STORAGE_KEY, next)
  return next
}

export function saveMentorApplication(application = {}) {
  const next = { ...application, submittedAt: Date.now() }
  writeUserStorage(APPLICATION_STORAGE_KEY, next)
  return clone(next)
}

export function getMentorApplication() {
  const application = readUserStorage(APPLICATION_STORAGE_KEY, null)
  return application && typeof application === 'object' ? clone(application) : null
}

function normalizeMentorRecord(rawMentor = {}, related = {}) {
  const rawPrice = rawMentor.price ?? (rawMentor.price_cents == null ? 0 : rawMentor.price_cents / 100)
  const name = String(rawMentor.name || rawMentor.displayName || rawMentor.display_name || '').trim()
  const maskedName = String(rawMentor.maskedName || rawMentor.displayName || rawMentor.display_name || maskMentorName(name)).trim()
  const reviews = related.reviews ?? rawMentor.reviews ?? []
  const availableSlots = related.availableSlots ?? rawMentor.availableSlots ?? rawMentor.available_slots ?? []
  return withMentorDisplayFields({
    id: String(rawMentor.id || ''),
    name: name || maskedName,
    maskedName: maskedName || '前辈',
    avatar: String(rawMentor.avatar || rawMentor.avatarLabel || rawMentor.avatar_label || maskedName.slice(0, 1) || '研'),
    avatarUrl: String(rawMentor.avatarUrl || rawMentor.avatar_url || ''),
    avatarTone: String(rawMentor.avatarTone || rawMentor.avatar_tone || 'blue'),
    verified: Boolean(rawMentor.verified ?? rawMentor.verification_status === 'verified'),
    school: String(rawMentor.school || ''),
    major: String(rawMentor.major || ''),
    admissionYear: String(rawMentor.admissionYear ?? rawMentor.admission_year ?? ''),
    graduationYear: rawMentor.graduationYear ?? rawMentor.graduation_year ?? null,
    examType: String(rawMentor.examType || rawMentor.exam_type || 'Z001'),
    score: toNumber(rawMentor.score),
    rating: toNumber(rawMentor.rating),
    ratingCount: toNumber(rawMentor.ratingCount ?? rawMentor.rating_count),
    consultCount: toNumber(rawMentor.consultCount ?? rawMentor.consult_count),
    price: toNumber(rawPrice),
    consultationWindowMinutes: toNumber(rawMentor.consultationWindowMinutes ?? rawMentor.consultation_window_minutes, 60),
    consultationEnabled: Boolean(rawMentor.consultationEnabled ?? rawMentor.consultation_enabled ?? true),
    onlineStatus: String(rawMentor.onlineStatus || rawMentor.online_status || 'offline'),
    acceptsBooking: Boolean(rawMentor.acceptsBooking ?? rawMentor.accepts_booking ?? true),
    featured: Boolean(rawMentor.featured ?? rawMentor.is_featured),
    recommendScore: toNumber(rawMentor.recommendScore ?? rawMentor.recommend_score),
    bio: String(rawMentor.bio || ''),
    story: String(rawMentor.story || ''),
    skills: Array.isArray(rawMentor.skills) ? rawMentor.skills.map(String).filter(Boolean) : [],
    reviews: (Array.isArray(reviews) ? reviews : []).map(normalizeMentorReview),
    availableSlots: (Array.isArray(availableSlots) ? availableSlots : []).map((slot) => normalizeMentorSlot(slot, rawPrice))
  })
}

function normalizeMentorReview(review = {}) {
  return {
    id: String(review.id || ''),
    author: String(review.author || review.reviewer_display_name || '匿名用户'),
    rating: toNumber(review.rating),
    date: String(review.date || review.created_at || '').slice(0, 10),
    content: String(review.content || '')
  }
}

function normalizeMentorSlot(slot = {}, defaultPrice = 0) {
  const startsAt = slot.startsAt || slot.starts_at || ''
  const endsAt = slot.endsAt || slot.ends_at || ''
  return {
    id: String(slot.id || ''),
    date: String(slot.date || formatMentorSlotDate(startsAt)),
    time: String(slot.time || formatMentorSlotTime(startsAt, endsAt)),
    startsAt,
    endsAt,
    price: toNumber(slot.price ?? (slot.price_cents == null ? defaultPrice : slot.price_cents / 100)),
    status: String(slot.status || 'available')
  }
}

function formatMentorSlotDate(value) {
  const date = parseDate(value)
  if (!date) return '待确认日期'
  const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
  return `${date.getMonth() + 1}月${date.getDate()}日 ${weekdays[date.getDay()]}`
}

function formatMentorSlotTime(startValue, endValue) {
  const start = parseDate(startValue)
  const end = parseDate(endValue)
  if (!start || !end) return '待确认时间'
  return `${formatClock(start)}–${formatClock(end)}`
}

function formatClock(date) {
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function parseDate(value) {
  if (!value) return null
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? null : date
}

function getCachedMentors() {
  if (mentorCache.length) return mentorCache
  const stored = readStorage(MENTOR_CACHE_STORAGE_KEY, [])
  if (!Array.isArray(stored)) return []
  mentorCache = stored.map((mentor) => normalizeMentorRecord(mentor)).filter((mentor) => mentor.id)
  return mentorCache
}

function withMentorDisplayFields(mentor = {}) {
  const mentorStatus = getMentorStatus(mentor)
  const maskedName = mentor.maskedName || maskMentorName(mentor.name)
  return {
    ...mentor,
    mentorStatus,
    maskedName,
    availabilityLabel: getMentorAvailabilityLabel({ ...mentor, mentorStatus }),
    actionLabel: getMentorActionLabel({ ...mentor, mentorStatus }),
    priceLabel: formatMentorPrice(mentor.price)
  }
}

function matchesMentorPrice(price, filter) {
  const value = Number(price || 0)
  if (!filter || filter === '不限') return true
  if (filter === '≤30元') return value <= 30
  if (filter === '30–50元') return value > 30 && value <= 50
  if (filter === '50–100元') return value > 50 && value <= 100
  if (filter === '100元以上') return value > 100
  return true
}

function splitMentorSearchTokens(keyword) {
  return normalize(keyword).split(/[\s,，、/]+/).filter(Boolean)
}

function matchesMentorKeyword(mentor, keywordTokens) {
  if (!keywordTokens.length) return true
  const searchable = normalize([mentor.school, mentor.major, mentor.name, mentor.maskedName].join(' '))
  const compactSearchable = searchable.replace(/\s/g, '')
  return keywordTokens.every((token) => (
    searchable.includes(token) || compactSearchable.includes(token.replace(/\s/g, ''))
  ))
}

function getMentorStatus(mentor = {}) {
  return mentor.mentorStatus || mentor.onlineStatus || 'offline'
}

function isMentorBookable(mentor = {}) {
  return getMentorStatus(mentor) !== 'online' && mentor.acceptsBooking !== false
}

function toNumber(value, fallback = 0) {
  const number = Number(value)
  return Number.isFinite(number) ? number : fallback
}

function normalize(value) {
  return String(value || '').trim().toLowerCase()
}

function clone(value) {
  return JSON.parse(JSON.stringify(value))
}

function readStorage(key, fallback) {
  try {
    if (typeof uni === 'undefined' || typeof uni.getStorageSync !== 'function') return fallback
    const value = uni.getStorageSync(key)
    return value === undefined || value === '' || value === null ? fallback : value
  } catch (error) {
    return fallback
  }
}

function getUserScopedStorageKey(key) {
  const user = getAuthUser() || {}
  const userId = String(user.id || user.user_id || user.userId || '').trim()
  return `${key}:${userId || 'guest'}`
}

function readUserStorage(key, fallback) {
  return readStorage(getUserScopedStorageKey(key), fallback)
}

function writeUserStorage(key, value) {
  writeStorage(getUserScopedStorageKey(key), value)
}

function removeUserStorage(key) {
  removeStorage(getUserScopedStorageKey(key))
}

function writeStorage(key, value) {
  try {
    if (typeof uni !== 'undefined' && typeof uni.setStorageSync === 'function') {
      uni.setStorageSync(key, value)
    }
  } catch (error) {
    // 缓存失败只影响跨页面兜底，不影响本次接口数据展示。
  }
}

function removeStorage(key) {
  try {
    if (typeof uni !== 'undefined' && typeof uni.removeStorageSync === 'function') {
      uni.removeStorageSync(key)
    }
  } catch (error) {
    // 忽略本地演示状态清理失败。
  }
}
