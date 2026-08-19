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

export const CONSULT_ORDER_STATUSES = ['draft', 'pending_payment', 'pending_accept', 'accepted', 'in_progress', 'completed', 'rejected', 'timeout', 'refunded', 'booked']
export const MENTOR_VERIFICATION_STATUSES = ['unverified', 'pending', 'verified', 'rejected']

const FAVORITE_STORAGE_KEY = 'circle-mentor-favorite-ids-v1'
const CONSULT_DRAFT_STORAGE_KEY = 'circle-mentor-consult-draft-v1'
const VERIFICATION_STORAGE_KEY = 'circle-mentor-verification-v1'
const APPLICATION_STORAGE_KEY = 'circle-mentor-application-v1'

const mentorSeeds = [
  {
    id: 'mentor-zhong-yuanhong',
    name: '钟源宏',
    avatar: '钟',
    avatarTone: 'blue',
    verified: true,
    school: '暨南大学',
    major: '应用经济学',
    admissionYear: '2025',
    graduationYear: '2027',
    examType: 'Z001',
    score: 382,
    rating: 4.9,
    consultCount: 28,
    price: 39,
    onlineStatus: 'online',
    available: true,
    featured: true,
    recommendScore: 98,
    bio: '2025 年港澳台研究生考试上岸，熟悉院校选择、Z001 备考以及复试准备，可以帮助分析备考规划和目标院校情况。',
    skills: ['院校选择', '初试备考', '复试经验'],
    story: '2025 年通过港澳台研究生招生考试录取至暨南大学应用经济学专业，初试 382 分，复试综合排名靠前。',
    reviews: [
      { id: 'z1', author: '匿名用户', rating: 5, date: '2026-08-12', content: '前辈讲得比较具体，帮我分析了学校和专业选择。' },
      { id: 'z2', author: '匿名用户', rating: 5, date: '2026-08-05', content: '问了复习节奏的问题，建议很实际，信息也很新。' },
      { id: 'z3', author: '匿名用户', rating: 4, date: '2026-07-28', content: '对 Z001 的阶段安排讲得很清楚。' }
    ],
    availableSlots: [
      { id: 'zhong-0822-0900', date: '8月22日 周六', time: '09:00–10:00', price: 39, status: 'booked' },
      { id: 'zhong-0822-1030', date: '8月22日 周六', time: '10:30–11:30', price: 39, status: 'available' },
      { id: 'zhong-0822-1400', date: '8月22日 周六', time: '14:00–15:00', price: 39, status: 'available' },
      { id: 'zhong-0822-1930', date: '8月22日 周六', time: '19:30–20:30', price: 49, status: 'available' },
      { id: 'zhong-0823-1000', date: '8月23日 周日', time: '10:00–11:00', price: 39, status: 'available' },
      { id: 'zhong-0823-1500', date: '8月23日 周日', time: '15:00–16:00', price: 39, status: 'available' }
    ]
  },
  {
    id: 'mentor-wang-ruoxi',
    name: '王若曦',
    avatar: '王',
    avatarTone: 'violet',
    verified: true,
    school: '中山大学',
    major: '金融学',
    admissionYear: '2024',
    graduationYear: '2026',
    examType: 'Z001',
    score: 391,
    rating: 4.9,
    consultCount: 46,
    price: 49,
    onlineStatus: 'offline',
    available: true,
    featured: true,
    recommendScore: 96,
    bio: '金融学在读，熟悉经管类院校定位、初试科目搭配和复试专业课准备，偏向提供可执行的阶段规划。',
    skills: ['院校选择', '专业选择', '学习规划'],
    story: '2024 年录取至中山大学金融学专业，曾从跨专业备考视角重新梳理过院校梯度和复试表达。',
    reviews: [
      { id: 'w1', author: '匿名用户', rating: 5, date: '2026-08-10', content: '把保底、稳妥、冲刺的学校划分得很清楚。' },
      { id: 'w2', author: '匿名用户', rating: 5, date: '2026-07-22', content: '回答很耐心，复试准备建议很有针对性。' }
    ],
    availableSlots: [
      { id: 'wang-0822-1100', date: '8月22日 周六', time: '11:00–12:00', price: 49, status: 'available' },
      { id: 'wang-0823-1500', date: '8月23日 周日', time: '15:00–16:00', price: 49, status: 'available' }
    ]
  },
  {
    id: 'mentor-lin-yan',
    name: '林妍',
    avatar: '林',
    avatarTone: 'mint',
    verified: true,
    school: '厦门大学',
    major: '国际商务',
    admissionYear: '2025',
    graduationYear: '2027',
    examType: 'Z002',
    score: 366,
    rating: 4.8,
    consultCount: 21,
    price: 35,
    onlineStatus: 'online',
    available: true,
    featured: false,
    recommendScore: 89,
    bio: '专注 Z002 综合能力复习节奏和国际商务专业方向，适合需要从基础阶段重新搭建计划的同学。',
    skills: ['Z002备考', '学习规划', '复试经验'],
    story: '2025 年录取至厦门大学国际商务专业，备考期间将数学与逻辑拆成了可复盘的周计划。',
    reviews: [
      { id: 'l1', author: '匿名用户', rating: 5, date: '2026-08-08', content: 'Z002 每周怎么分配时间讲得特别明白。' },
      { id: 'l2', author: '匿名用户', rating: 4, date: '2026-07-18', content: '很适合刚开始准备的同学。' }
    ],
    availableSlots: [
      { id: 'lin-0822-1430', date: '8月22日 周六', time: '14:30–15:30', price: 35, status: 'available' },
      { id: 'lin-0823-1000', date: '8月23日 周日', time: '10:00–11:00', price: 35, status: 'available' }
    ]
  },
  {
    id: 'mentor-chen-yucheng',
    name: '陈宇程',
    avatar: '陈',
    avatarTone: 'warm',
    verified: true,
    school: '华南理工大学',
    major: '工商管理',
    admissionYear: '2025',
    graduationYear: '2027',
    examType: 'Z001',
    score: 376,
    rating: 4.7,
    consultCount: 18,
    price: 45,
    onlineStatus: 'busy',
    available: true,
    featured: false,
    recommendScore: 84,
    bio: '了解管理类专业选择、跨专业准备和复试案例表达，咨询时偏重梳理目标与行动优先级。',
    skills: ['院校选择', '复试经验', '学习规划'],
    story: '2025 年录取至华南理工大学工商管理专业，曾结合工作经历完成跨专业申请与复试准备。',
    reviews: [
      { id: 'c1', author: '匿名用户', rating: 5, date: '2026-08-02', content: '跨专业背景怎么准备，讲得很落地。' },
      { id: 'c2', author: '匿名用户', rating: 4, date: '2026-07-15', content: '问题拆得很细，后续行动很明确。' }
    ],
    availableSlots: [
      { id: 'chen-0822-1930', date: '8月22日 周六', time: '19:30–20:30', price: 45, status: 'available' },
      { id: 'chen-0823-1400', date: '8月23日 周日', time: '14:00–15:00', price: 45, status: 'available' }
    ]
  },
  {
    id: 'mentor-li-junhao',
    name: '李俊豪',
    avatar: '李',
    avatarTone: 'blue',
    verified: true,
    school: '浙江大学',
    major: '计算机科学与技术',
    admissionYear: '2024',
    graduationYear: '2026',
    examType: 'Z002',
    score: 375,
    rating: 4.9,
    consultCount: 35,
    price: 59,
    onlineStatus: 'offline',
    available: true,
    featured: true,
    recommendScore: 93,
    bio: '可协助计算机相关专业的院校定位、Z002 复习安排与复试项目表达，适合有技术背景的考生。',
    skills: ['Z002备考', '院校选择', '复试经验'],
    story: '2024 年录取至浙江大学计算机科学与技术专业，复试阶段重点准备项目复盘与技术表达。',
    reviews: [
      { id: 'li1', author: '匿名用户', rating: 5, date: '2026-08-09', content: '讲清了技术项目如何转换成复试表达。' },
      { id: 'li2', author: '匿名用户', rating: 5, date: '2026-07-30', content: '目标院校的准备节奏很有参考价值。' }
    ],
    availableSlots: [
      { id: 'li-0822-1000', date: '8月22日 周六', time: '10:00–11:00', price: 59, status: 'available' },
      { id: 'li-0823-1930', date: '8月23日 周日', time: '19:30–20:30', price: 59, status: 'available' }
    ]
  },
  {
    id: 'mentor-zhao-yuxin',
    name: '赵雨欣',
    avatar: '赵',
    avatarTone: 'mint',
    verified: true,
    school: '北京师范大学',
    major: '教育学',
    admissionYear: '2025',
    graduationYear: '2027',
    examType: 'Z001',
    score: 388,
    rating: 4.8,
    consultCount: 24,
    price: 39,
    onlineStatus: 'online',
    available: true,
    featured: false,
    recommendScore: 88,
    bio: '熟悉教育学专业方向、文献阅读与复试试讲准备，也可以一起梳理长期学习计划。',
    skills: ['专业选择', '初试备考', '复试经验'],
    story: '2025 年录取至北京师范大学教育学专业，复试阶段以研究计划和试讲结构作为重点。',
    reviews: [
      { id: 'zhao1', author: '匿名用户', rating: 5, date: '2026-08-01', content: '建议具体，尤其是复试试讲部分。' },
      { id: 'zhao2', author: '匿名用户', rating: 4, date: '2026-07-20', content: '对专业方向的讲解很清晰。' }
    ],
    availableSlots: [
      { id: 'zhao-0822-1530', date: '8月22日 周六', time: '15:30–16:30', price: 39, status: 'available' },
      { id: 'zhao-0823-1100', date: '8月23日 周日', time: '11:00–12:00', price: 39, status: 'available' }
    ]
  },
  {
    id: 'mentor-zhou-ziming',
    name: '周子明',
    avatar: '周',
    avatarTone: 'violet',
    verified: true,
    school: '复旦大学',
    major: '中国语言文学',
    admissionYear: '2024',
    graduationYear: '2026',
    examType: 'Z001',
    score: 386,
    rating: 4.7,
    consultCount: 16,
    price: 32,
    onlineStatus: 'busy',
    available: true,
    featured: false,
    recommendScore: 80,
    bio: '擅长中文、文化类专业的专业方向比较、阅读材料积累和复试问答准备。',
    skills: ['专业选择', '初试备考', '学习规划'],
    story: '2024 年录取至复旦大学中国语言文学专业，备考时坚持将阅读积累转为可复用的答题框架。',
    reviews: [
      { id: 'zhou1', author: '匿名用户', rating: 5, date: '2026-07-31', content: '材料怎么整理的建议非常实用。' },
      { id: 'zhou2', author: '匿名用户', rating: 4, date: '2026-07-12', content: '对中文专业方向很熟悉。' }
    ],
    availableSlots: [
      { id: 'zhou-0822-0900', date: '8月22日 周六', time: '09:00–10:00', price: 32, status: 'available' },
      { id: 'zhou-0823-1430', date: '8月23日 周日', time: '14:30–15:30', price: 32, status: 'available' }
    ]
  },
  {
    id: 'mentor-he-yuting',
    name: '何雨婷',
    avatar: '何',
    avatarTone: 'warm',
    verified: true,
    school: '武汉大学',
    major: '法学',
    admissionYear: '2026',
    graduationYear: '2028',
    examType: 'Z002',
    score: 371,
    rating: 4.8,
    consultCount: 12,
    price: 29,
    onlineStatus: 'online',
    available: true,
    featured: false,
    recommendScore: 83,
    bio: '刚完成上岸流程，熟悉法学专业定位、备考节奏调整和从初试到复试的信息衔接。',
    skills: ['Z002备考', '院校选择', '学习规划'],
    story: '2026 年录取至武汉大学法学专业，备考中通过阶段测评逐步调整逻辑与数学的投入比例。',
    reviews: [
      { id: 'he1', author: '匿名用户', rating: 5, date: '2026-08-14', content: '刚上岸的信息很新，回答也很真诚。' },
      { id: 'he2', author: '匿名用户', rating: 4, date: '2026-08-03', content: '价格友好，建议很有帮助。' }
    ],
    availableSlots: [
      { id: 'he-0822-1100', date: '8月22日 周六', time: '11:00–12:00', price: 29, status: 'available' },
      { id: 'he-0823-1600', date: '8月23日 周日', time: '16:00–17:00', price: 29, status: 'available' }
    ]
  }
]

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

export function getMentorAvailabilityLabel(mentor = {}) {
  return getMentorStatus(mentor) === 'online' ? '在线' : '可预约'
}

export function getMentorActionLabel(mentor = {}) {
  return getMentorStatus(mentor) === 'online' ? '立即咨询' : '预约咨询'
}

export function formatMentorPrice(price) {
  return `¥${Number(price || 0)}`
}

export function getMockMentors() {
  return clone(mentorSeeds).map(withMentorDisplayFields)
}

export function getMentorById(id) {
  const mentor = mentorSeeds.find((item) => item.id === String(id || ''))
  return mentor ? withMentorDisplayFields(clone(mentor)) : null
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

export function filterMentors({ keyword = '', filters = createDefaultMentorFilters(), sort = 'recommended' } = {}) {
  const activeFilters = { ...createDefaultMentorFilters(), ...(filters || {}) }
  const keywordTokens = splitMentorSearchTokens(keyword)
  const searchedMentors = getMockMentors().filter((mentor) => matchesMentorKeyword(mentor, keywordTokens))
  const filteredMentors = searchedMentors.filter((mentor) => {
    if (activeFilters.examType !== '不限' && mentor.examType !== activeFilters.examType) return false
    if (activeFilters.admissionYear === '更早' && Number(mentor.admissionYear) > 2023) return false
    if (activeFilters.admissionYear !== '不限' && activeFilters.admissionYear !== '更早' && mentor.admissionYear !== activeFilters.admissionYear) return false
    if (!matchesMentorPrice(mentor.price, activeFilters.price)) return false
    if (activeFilters.availability === '在线' && getMentorStatus(mentor) !== 'online') return false
    if (activeFilters.availability === '可预约' && !isMentorBookable(mentor)) return false
    return true
  })

  if (sort === 'recommended') return filteredMentors
  return [...filteredMentors].sort((left, right) => {
    if (sort === 'consult_count') return right.consultCount - left.consultCount || right.rating - left.rating
    if (sort === 'rating') return right.rating - left.rating || right.consultCount - left.consultCount
    if (sort === 'price') return left.price - right.price || right.rating - left.rating
    return 0
  })
}

export function getMentorFavoriteIds() {
  const stored = readStorage(FAVORITE_STORAGE_KEY, [])
  return Array.isArray(stored) ? stored.map(String) : []
}

export function toggleMentorFavorite(mentorId) {
  const id = String(mentorId || '')
  if (!id) return getMentorFavoriteIds()
  const favoriteIds = getMentorFavoriteIds()
  const next = favoriteIds.includes(id)
    ? favoriteIds.filter((item) => item !== id)
    : [...favoriteIds, id]
  writeStorage(FAVORITE_STORAGE_KEY, next)
  return next
}

export function startConsultationDraft({ mentorId, consultationType = 'instant', bookingSlot = null } = {}) {
  const mentor = getMentorById(mentorId)
  if (!mentor) return null
  const draft = {
    mentorId: mentor.id,
    consultationType: consultationType === 'booking' ? 'booking' : 'instant',
    bookingSlot: bookingSlot ? clone(bookingSlot) : null,
    questionnaire: createDefaultConsultationQuestionnaire(),
    orderStatus: 'draft',
    messages: [],
    createdAt: Date.now()
  }
  writeStorage(CONSULT_DRAFT_STORAGE_KEY, draft)
  return clone(draft)
}

export function getConsultationDraft() {
  const draft = readStorage(CONSULT_DRAFT_STORAGE_KEY, null)
  return draft && typeof draft === 'object' ? { ...draft, questionnaire: { ...createDefaultConsultationQuestionnaire(), ...(draft.questionnaire || {}) } } : null
}

export function saveConsultationQuestionnaire(questionnaire = {}) {
  const draft = getConsultationDraft()
  if (!draft) return null
  const next = {
    ...draft,
    questionnaire: { ...createDefaultConsultationQuestionnaire(), ...questionnaire },
    orderStatus: 'pending_payment'
  }
  writeStorage(CONSULT_DRAFT_STORAGE_KEY, next)
  return clone(next)
}

export function setConsultationOrderStatus(status) {
  const draft = getConsultationDraft()
  const nextStatus = CONSULT_ORDER_STATUSES.includes(status) ? status : 'draft'
  if (!draft) return null
  const next = { ...draft, orderStatus: nextStatus, updatedAt: Date.now() }
  writeStorage(CONSULT_DRAFT_STORAGE_KEY, next)
  return clone(next)
}

export function appendConsultationMessage(message) {
  const draft = getConsultationDraft()
  if (!draft) return null
  const messages = Array.isArray(draft.messages) ? draft.messages : []
  const next = {
    ...draft,
    messages: [...messages, { id: `message-${Date.now()}-${messages.length}`, createdAt: Date.now(), ...message }]
  }
  writeStorage(CONSULT_DRAFT_STORAGE_KEY, next)
  return clone(next)
}

export function resetConsultationDraft() {
  removeStorage(CONSULT_DRAFT_STORAGE_KEY)
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
  const status = String(readStorage(VERIFICATION_STORAGE_KEY, 'unverified') || 'unverified')
  return MENTOR_VERIFICATION_STATUSES.includes(status) ? status : 'unverified'
}

export function setMentorVerificationStatus(status) {
  const next = MENTOR_VERIFICATION_STATUSES.includes(status) ? status : 'unverified'
  writeStorage(VERIFICATION_STORAGE_KEY, next)
  return next
}

export function saveMentorApplication(application = {}) {
  const next = { ...application, submittedAt: Date.now() }
  writeStorage(APPLICATION_STORAGE_KEY, next)
  return clone(next)
}

export function getMentorApplication() {
  const application = readStorage(APPLICATION_STORAGE_KEY, null)
  return application && typeof application === 'object' ? clone(application) : null
}

function withMentorDisplayFields(mentor) {
  const mentorStatus = getMentorStatus(mentor)
  return {
    ...mentor,
    mentorStatus,
    maskedName: maskMentorName(mentor.name),
    availabilityLabel: getMentorAvailabilityLabel(mentor),
    actionLabel: getMentorActionLabel(mentor),
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
  return normalize(keyword)
    .split(/[\s,，、/]+/)
    .filter(Boolean)
}

function matchesMentorKeyword(mentor, keywordTokens) {
  if (!keywordTokens.length) return true
  const searchable = normalize([
    mentor.school,
    mentor.major,
    mentor.name,
    mentor.maskedName
  ].join(' '))
  const compactSearchable = searchable.replace(/\s/g, '')
  return keywordTokens.every((token) => (
    searchable.includes(token) || compactSearchable.includes(token.replace(/\s/g, ''))
  ))
}

function getMentorStatus(mentor = {}) {
  return mentor.mentorStatus || mentor.onlineStatus || 'offline'
}

function isMentorBookable(mentor = {}) {
  return getMentorStatus(mentor) !== 'online'
    && Array.isArray(mentor.availableSlots)
    && mentor.availableSlots.some((slot) => slot?.status === 'available')
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

function writeStorage(key, value) {
  try {
    if (typeof uni !== 'undefined' && typeof uni.setStorageSync === 'function') {
      uni.setStorageSync(key, value)
    }
  } catch (error) {
    // 本地缓存不可用时，页面仍可作为单次 Mock 演示继续使用。
  }
}

function removeStorage(key) {
  try {
    if (typeof uni !== 'undefined' && typeof uni.removeStorageSync === 'function') {
      uni.removeStorageSync(key)
    }
  } catch (error) {
    // 忽略本地缓存清理失败，不影响本次演示。
  }
}
