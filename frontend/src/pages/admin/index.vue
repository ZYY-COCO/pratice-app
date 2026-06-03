<template>
  <view class="admin-page" :class="{ 'question-mode': activeTab === 'questions' }" :style="themeInlineStyle">
    <view class="admin-hero">
      <button class="back-btn" @tap="goBack">‹</button>
      <view class="admin-heading">
        <view class="admin-title">{{ pageTitle }}</view>
        <view class="admin-subtitle">{{ pageSubtitle }}</view>
      </view>
      <button v-if="activeTab === 'questions'" class="hero-refresh-btn" @tap="refreshQuestionManager">↻</button>
    </view>

    <view v-if="loading" class="state-card">正在读取后台数据...</view>
    <view v-else-if="!allowed" class="state-card denied">
      <view class="state-title">无后台权限</view>
      <view class="state-copy">请使用管理员账号登录后再访问。</view>
    </view>

    <template v-else>
      <view v-if="activeTab !== 'questions'" class="stat-grid">
        <view v-for="item in primaryOverviewCards" :key="item.label" class="stat-card primary">
          <view class="stat-label">{{ item.label }}</view>
          <view class="stat-value">{{ item.value }}</view>
        </view>
      </view>
      <view v-if="activeTab !== 'questions'" class="metric-strip">
        <view v-for="item in secondaryOverviewCards" :key="item.label" class="metric-item">
          <text class="metric-label">{{ item.label }}</text>
          <text class="metric-value">{{ item.value }}</text>
        </view>
      </view>

      <view v-if="!questionEntryMode" class="tab-bar">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @tap="switchTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </view>

      <view v-if="activeTab === 'users'" class="panel-card">
        <view class="panel-head">
          <view>
            <view class="panel-title">用户数据</view>
            <view class="panel-subtitle">账号、刷题量与会员状态</view>
          </view>
          <button class="ghost-btn refresh-btn" @tap="loadUsers">刷新</button>
        </view>
        <view class="search-row">
          <input v-model="userSearch" class="search-input" placeholder="搜索邮箱" confirm-type="search" @confirm="loadUsers" />
          <button class="search-btn" @tap="loadUsers">搜索</button>
        </view>
        <view class="filter-row">
          <button
            v-for="item in userFilterOptions"
            :key="item.key"
            class="filter-chip"
            :class="{ active: userFilter === item.key }"
            @tap="userFilter = item.key"
          >
            {{ item.label }}
          </button>
        </view>
        <view v-if="usersLoading" class="inline-state">正在加载用户...</view>
        <view v-else-if="visibleUsers.length === 0" class="inline-state">暂无匹配用户</view>
        <view v-else class="record-list">
          <view v-for="user in visibleUsers" :key="user.id" class="record-card" @tap="openUser(user)">
            <view class="record-main">
              <view class="record-title">{{ user.email || user.phone || '未绑定账号' }}</view>
              <view class="record-subtitle">
                {{ user.nickname || '未设置昵称' }} · {{ user.exam_target || '未设置目标' }} · 刷题 {{ user.answer_count || 0 }} 道
              </view>
              <view class="badge-row">
                <text class="badge" :class="{ active: user.membership_status === 'active' }">
                  {{ user.membership_status === 'active' ? '会员' : '非会员' }}
                </text>
                <text v-if="user.role === 'admin'" class="badge admin">管理员</text>
                <text v-if="user.membership_expires_at" class="record-date">至 {{ formatDate(user.membership_expires_at) }}</text>
              </view>
            </view>
            <button class="small-btn" @tap.stop="openMembershipActions(user)">{{ membershipActionLabel(user) }}</button>
          </view>
        </view>
      </view>

      <view v-if="activeTab === 'feedback'" class="panel-card">
        <view class="panel-head">
          <view>
            <view class="panel-title">用户反馈</view>
            <view class="panel-subtitle">来自 App 内帮助与反馈</view>
          </view>
          <button class="ghost-btn refresh-btn" @tap="loadFeedback">刷新</button>
        </view>
        <view v-if="feedbackLoading" class="inline-state">正在加载反馈...</view>
        <view v-else-if="feedbackItems.length === 0" class="inline-state">暂无反馈</view>
        <view v-else class="record-list">
          <view v-for="item in feedbackItems" :key="item.id" class="record-card feedback-card" @tap="openFeedback(item)">
            <view class="record-title">{{ item.feedback_type || '反馈' }}</view>
            <view class="record-subtitle clamp">{{ item.content }}</view>
            <view class="badge-row">
              <text class="badge" :class="{ active: item.status === 'resolved' || item.status === 'reviewed' }">
                {{ feedbackStatusText(item.status) }}
              </text>
              <text class="record-date">{{ formatDate(item.created_at) }} · {{ item.source_page || '未知来源' }}</text>
            </view>
            <button class="small-btn inline-action" @tap.stop="openFeedbackStatusAction(item)">处理状态</button>
          </view>
        </view>
      </view>

      <view v-if="activeTab === 'questions'" class="question-manager">
        <view class="question-stats-grid">
          <view
            v-for="item in questionStatCards"
            :key="item.label"
            class="question-stat-card"
            :class="item.tone"
          >
            <view class="question-stat-head">
              <view class="question-stat-icon">{{ item.icon }}</view>
              <view class="question-stat-label">{{ item.label }}</view>
            </view>
            <view class="question-stat-value">{{ item.value }}</view>
          </view>
        </view>

        <view class="question-search-box">
          <text class="question-search-icon">⌕</text>
          <input
            v-model.trim="questionFilters.search"
            class="question-search-input"
            placeholder="搜索题干 / ID"
            confirm-type="search"
            @confirm="loadQuestions"
          />
        </view>

        <view class="question-filter-row">
          <picker :range="questionSubjectLabels" :value="selectedQuestionSubjectIndex" @change="handleQuestionSubjectChange">
            <view class="question-filter-pill">
              <text>{{ selectedQuestionSubjectLabel }}</text>
              <text class="question-filter-arrow">⌄</text>
            </view>
          </picker>
          <picker :range="questionModuleLabels" :value="selectedQuestionModuleIndex" @change="handleQuestionModuleChange">
            <view class="question-filter-pill">
              <text>{{ selectedQuestionModuleLabel }}</text>
              <text class="question-filter-arrow">⌄</text>
            </view>
          </picker>
          <picker :range="questionDifficultyLabels" :value="selectedQuestionDifficultyIndex" @change="handleQuestionDifficultyChange">
            <view class="question-filter-pill">
              <text>{{ selectedQuestionDifficultyLabel }}</text>
              <text class="question-filter-arrow">⌄</text>
            </view>
          </picker>
          <picker :range="questionStatusLabels" :value="selectedQuestionStatusIndex" @change="handleQuestionStatusChange">
            <view class="question-filter-pill">
              <text>{{ selectedQuestionStatusLabel }}</text>
              <text class="question-filter-arrow">⌄</text>
            </view>
          </picker>
        </view>

        <view class="question-action-row">
          <button class="question-action-btn outline" @tap="showComingSoon('新增题目')">
            <text class="question-action-icon">＋</text>
            <text>新增题目</text>
          </button>
          <button class="question-action-btn outline" @tap="showComingSoon('批量导入')">
            <text class="question-action-icon">⇧</text>
            <text>批量导入</text>
          </button>
          <button class="question-action-btn filled" @tap="showComingSoon('审核队列')">
            <text class="question-action-icon">☷</text>
            <text>进入审核队列</text>
          </button>
        </view>

        <view v-if="questionsLoading" class="inline-state">正在加载题库...</view>
        <view v-else-if="questions.length === 0" class="inline-state">暂无题目</view>
        <view v-else class="question-card-list">
          <view v-for="item in questions" :key="item.id" class="question-admin-card" @tap="openQuestion(item)">
            <button
              class="question-check"
              :class="{ checked: isQuestionSelected(item.id) }"
              @tap.stop="toggleQuestionSelection(item.id)"
            >
              {{ isQuestionSelected(item.id) ? '✓' : '' }}
            </button>
            <view class="question-card-main">
              <view class="question-chip-row">
                <text class="question-chip">{{ item.subject || item.exam_code || '未分类' }}</text>
                <text class="question-chip">{{ item.submodule || item.module || '未分模块' }}</text>
                <text class="question-chip">难度 {{ item.difficulty || '-' }}</text>
              </view>
              <view class="question-stem-preview">{{ previewQuestionStem(item.stem) }}</view>
              <view class="question-status-row">
                <text class="question-status-pill" :class="questionStatusTone(item.status)">
                  {{ questionStatusText(item.status) }}
                </text>
                <text v-if="item.answer" class="question-answer">答案 {{ item.answer }}</text>
              </view>
            </view>
            <button class="question-edit-btn" @tap.stop="openQuestion(item)">
              <text class="question-edit-icon">✎</text>
              <text>编辑</text>
            </button>
          </view>
        </view>

        <view class="question-bulk-bar">
          <view class="question-selected-label">
            已选 <text class="question-selected-count">{{ selectedQuestionIds.length }}</text> 题
          </view>
          <button class="question-bulk-btn" @tap="toggleSelectAllQuestions">
            <text class="question-bulk-icon">☑</text>
            <text>{{ allVisibleQuestionsSelected ? '取消' : '全选' }}</text>
          </button>
          <button class="question-bulk-btn archive" @tap="archiveSelectedQuestions">
            <text class="question-bulk-icon">▣</text>
            <text>归档</text>
          </button>
          <button class="question-bulk-btn publish" @tap="publishSelectedQuestions">
            <text class="question-bulk-icon">⇩</text>
            <text>发布</text>
          </button>
        </view>
      </view>

      <view v-if="activeTab === 'messages'" class="panel-card">
        <view class="panel-head">
          <view>
            <view class="panel-title">官方消息</view>
            <view class="panel-subtitle">发布首页铃铛公告，用户读后不再自动弹出</view>
          </view>
          <button class="ghost-btn" @tap="resetMessageForm">新建</button>
        </view>

        <view class="message-editor">
          <input v-model.trim="messageForm.title" class="search-input" placeholder="消息标题" />
          <textarea v-model.trim="messageForm.content" class="message-textarea" placeholder="消息内容，支持换行" />
          <view class="message-status-row">
            <button
              v-for="item in messageStatusOptions"
              :key="item.value"
              class="status-chip"
              :class="{ active: messageForm.status === item.value }"
              @tap="messageForm.status = item.value"
            >
              {{ item.label }}
            </button>
          </view>
          <button class="search-btn wide" @tap="saveOfficialMessage">
            {{ messageForm.id ? '保存消息' : '创建消息' }}
          </button>
        </view>

        <view class="panel-head compact">
          <view class="panel-title small">消息列表</view>
          <button class="ghost-btn refresh-btn" @tap="loadMessages">刷新</button>
        </view>
        <view v-if="messagesLoading" class="inline-state">正在加载消息...</view>
        <view v-else-if="officialMessageItems.length === 0" class="inline-state">暂无官方消息</view>
        <view v-else class="record-list">
          <view v-for="item in officialMessageItems" :key="item.id" class="record-card feedback-card" @tap="editOfficialMessage(item)">
            <view class="record-title">{{ item.title }}</view>
            <view class="record-subtitle clamp">{{ item.content }}</view>
            <view class="badge-row">
              <text class="badge" :class="{ active: item.status === 'published', archived: item.status === 'archived' }">
                {{ messageStatusText(item.status) }}
              </text>
              <text class="record-date">{{ formatDate(item.published_at || item.created_at) }}</text>
            </view>
            <button class="small-btn inline-action" @tap.stop="editOfficialMessage(item)">编辑</button>
          </view>
        </view>
      </view>
    </template>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import {
  cancelAdminMembership,
  createAdminMessage,
  fetchAdminFeedback,
  fetchAdminMe,
  fetchAdminMessages,
  fetchAdminOverview,
  fetchAdminQuestionDetail,
  fetchAdminQuestions,
  fetchAdminUserDetail,
  fetchAdminUsers,
  grantAdminMembership,
  updateAdminMessage,
  updateAdminFeedbackStatus,
  updateAdminQuestionStatus
} from '../../api/admin'
import { getAuthUser, isLoggedIn, updateAuthUser } from '../../utils/auth'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const ADMIN_EMAIL = '2221073755@qq.com'
const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const loading = ref(true)
const allowed = ref(false)
const overview = ref({})
const activeTab = ref('users')
const questionEntryMode = ref(false)
const users = ref([])
const usersLoading = ref(false)
const userSearch = ref('')
const userFilter = ref('all')
const feedbackItems = ref([])
const feedbackLoading = ref(false)
const questions = ref([])
const questionsLoading = ref(false)
const questionListCount = ref(0)
const selectedQuestionIds = ref([])
const questionStats = reactive({
  active: 0,
  archived: 0,
  pendingReview: 0
})
const officialMessageItems = ref([])
const messagesLoading = ref(false)
const authUser = ref(getAuthUser())

const messageStatusOptions = [
  { value: 'draft', label: '草稿' },
  { value: 'published', label: '发布' },
  { value: 'archived', label: '归档' }
]

const messageForm = reactive({
  id: '',
  title: '',
  content: '',
  status: 'draft',
  expires_at: ''
})

const questionFilters = reactive({
  exam_code: '',
  subject: '',
  module: '',
  difficulty: '',
  status: '',
  search: ''
})

const questionSubjectOptions = [
  { label: '科目', value: '' },
  { label: '中华文化', value: '中华文化' },
  { label: '英语运用', value: '英语运用' },
  { label: '数学基础', value: '数学基础' },
  { label: '逻辑推理', value: '逻辑推理' }
]

const questionModuleMap = {
  中华文化: ['中国哲学常识', '文学常识', '历史文化', '艺术民俗', '宗教思想'],
  英语运用: ['语言知识', '词汇', '语法', '语用'],
  数学基础: ['一元函数微分学', '一元函数积分学', '多元函数微分学'],
  逻辑推理: ['论证', '概念判断', '削弱加强', '推理规则']
}

const fallbackQuestionModules = ['中国哲学常识', '词汇', '论证', '一元函数微分学']

const questionDifficultyOptions = [
  { label: '难度', value: '' },
  { label: '难度 1', value: '1' },
  { label: '难度 2', value: '2' },
  { label: '难度 3', value: '3' },
  { label: '难度 4', value: '4' },
  { label: '难度 5', value: '5' }
]

const questionStatusOptions = [
  { label: '状态', value: '' },
  { label: '已发布', value: 'active' },
  { label: '已归档', value: 'archived' }
]

const tabs = [
  { key: 'users', label: '用户' },
  { key: 'feedback', label: '反馈' },
  { key: 'messages', label: '消息' }
]

const pageTitle = computed(() => (activeTab.value === 'questions' ? '题库管理' : '后台管理'))
const pageSubtitle = computed(() => (
  activeTab.value === 'questions'
    ? '编辑、审核与题库质量运营'
    : '用户、反馈与消息运营面板'
))

const userFilterOptions = [
  { key: 'all', label: '全部' },
  { key: 'member', label: '会员' },
  { key: 'non_member', label: '非会员' },
  { key: 'active', label: '有刷题' }
]

const primaryOverviewCards = computed(() => [
  { label: '总用户', value: overview.value.total_users || 0 },
  { label: '今日活跃', value: overview.value.active_today || 0 },
  { label: '会员数', value: overview.value.active_members || 0 },
  { label: '待处理', value: overview.value.pending_feedback || 0 }
])

const secondaryOverviewCards = computed(() => [
  { label: '本周活跃', value: overview.value.active_week || 0 },
  { label: '本月活跃', value: overview.value.active_month || 0 },
  { label: '题库量', value: overview.value.total_questions || 0 },
  { label: '反馈数', value: overview.value.total_feedback || 0 }
])

const questionStatCards = computed(() => [
  {
    label: '总题量',
    value: overview.value.total_questions || questionListCount.value || 0,
    icon: '▤',
    tone: 'blue'
  },
  {
    label: '待审核',
    value: questionStats.pendingReview,
    icon: '◷',
    tone: 'orange'
  },
  {
    label: '已归档',
    value: questionStats.archived,
    icon: '▣',
    tone: 'green'
  },
  {
    label: '已发布',
    value: questionStats.active,
    icon: '✓',
    tone: 'blue'
  }
])

const questionModuleOptions = computed(() => {
  const modules = questionModuleMap[questionFilters.subject] || fallbackQuestionModules
  const uniqueModules = new Set(modules)
  if (questionFilters.module) {
    uniqueModules.add(questionFilters.module)
  }
  return [
    { label: '模块', value: '' },
    ...Array.from(uniqueModules).map((item) => ({ label: item, value: item }))
  ]
})

const questionSubjectLabels = computed(() => questionSubjectOptions.map((item) => item.label))
const questionModuleLabels = computed(() => questionModuleOptions.value.map((item) => item.label))
const questionDifficultyLabels = computed(() => questionDifficultyOptions.map((item) => item.label))
const questionStatusLabels = computed(() => questionStatusOptions.map((item) => item.label))

const selectedQuestionSubjectIndex = computed(() => getOptionIndex(questionSubjectOptions, questionFilters.subject))
const selectedQuestionModuleIndex = computed(() => getOptionIndex(questionModuleOptions.value, questionFilters.module))
const selectedQuestionDifficultyIndex = computed(() => getOptionIndex(questionDifficultyOptions, questionFilters.difficulty))
const selectedQuestionStatusIndex = computed(() => getOptionIndex(questionStatusOptions, questionFilters.status))

const selectedQuestionSubjectLabel = computed(() => questionSubjectOptions[selectedQuestionSubjectIndex.value]?.label || '科目')
const selectedQuestionModuleLabel = computed(() => questionModuleOptions.value[selectedQuestionModuleIndex.value]?.label || '模块')
const selectedQuestionDifficultyLabel = computed(() => questionDifficultyOptions[selectedQuestionDifficultyIndex.value]?.label || '难度')
const selectedQuestionStatusLabel = computed(() => questionStatusOptions[selectedQuestionStatusIndex.value]?.label || '状态')

const selectedQuestionIdSet = computed(() => new Set(selectedQuestionIds.value))
const allVisibleQuestionsSelected = computed(() => (
  questions.value.length > 0 && questions.value.every((item) => selectedQuestionIdSet.value.has(item.id))
))

const visibleUsers = computed(() => {
  if (userFilter.value === 'member') {
    return users.value.filter((user) => user.membership_status === 'active')
  }
  if (userFilter.value === 'non_member') {
    return users.value.filter((user) => user.membership_status !== 'active')
  }
  if (userFilter.value === 'active') {
    return users.value.filter((user) => Number(user.answer_count || 0) > 0)
  }
  return users.value
})

onLoad(async (options = {}) => {
  if (options.tab === 'questions') {
    activeTab.value = 'questions'
    questionEntryMode.value = true
  }
  await bootstrap()
})

async function bootstrap() {
  if (!isLoggedIn()) {
    uni.redirectTo({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/admin/index')}` })
    return
  }

  loading.value = true
  try {
    const me = await fetchAdminMe()
    allowed.value = Boolean(me?.is_admin)
    if (me?.profile) {
      const nextUser = updateAuthUser(me.profile)
      authUser.value = nextUser || me.profile
    }
    if (allowed.value) {
      const initialLoads = [loadOverview()]
      if (activeTab.value === 'questions') {
        initialLoads.push(loadQuestionStats(), loadQuestions())
      } else {
        initialLoads.push(loadUsers())
      }
      await Promise.all(initialLoads)
    }
  } catch (error) {
    const email = String(authUser.value?.email || '').toLowerCase()
    allowed.value = email === ADMIN_EMAIL
    if (!allowed.value) {
      uni.showToast({ title: '无后台权限', icon: 'none' })
    }
  } finally {
    loading.value = false
  }
}

async function loadOverview() {
  overview.value = await fetchAdminOverview()
}

async function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'users' && users.value.length === 0) await loadUsers()
  if (tab === 'feedback' && feedbackItems.value.length === 0) await loadFeedback()
  if (tab === 'questions' && questions.value.length === 0) await refreshQuestionManager()
  if (tab === 'messages' && officialMessageItems.value.length === 0) await loadMessages()
}

async function refreshQuestionManager() {
  await Promise.all([loadOverview(), loadQuestionStats(), loadQuestions()])
}

async function loadUsers() {
  usersLoading.value = true
  try {
    const keyword = String(userSearch.value || '').trim()
    const params = {
      limit: 30,
      offset: 0
    }
    if (keyword) {
      params.search = keyword
    }
    const response = await fetchAdminUsers(params)
    users.value = normalizeListResponse(response)
  } catch (error) {
    uni.showToast({ title: '用户数据加载失败', icon: 'none' })
  } finally {
    usersLoading.value = false
  }
}

function normalizeListResponse(response) {
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.items)) return response.items
  if (Array.isArray(response?.users)) return response.users
  if (Array.isArray(response?.data)) return response.data
  return []
}

async function loadFeedback() {
  feedbackLoading.value = true
  try {
    const response = await fetchAdminFeedback({ limit: 50, offset: 0 })
    feedbackItems.value = response.items || []
  } catch (error) {
    uni.showToast({ title: '反馈加载失败', icon: 'none' })
  } finally {
    feedbackLoading.value = false
  }
}

async function loadQuestions() {
  questionsLoading.value = true
  try {
    const response = await fetchAdminQuestions({
      exam_code: questionFilters.exam_code || undefined,
      subject: questionFilters.subject || undefined,
      module: questionFilters.module || undefined,
      status: questionFilters.status || undefined,
      search: questionFilters.search || undefined,
      limit: 50,
      offset: 0
    })
    const rawItems = response.items || []
    const filteredItems = questionFilters.difficulty
      ? rawItems.filter((item) => String(item.difficulty || '') === String(questionFilters.difficulty))
      : rawItems
    questions.value = filteredItems
    questionListCount.value = Number(response.count || rawItems.length || 0)
    const visibleIds = new Set(filteredItems.map((item) => item.id))
    selectedQuestionIds.value = selectedQuestionIds.value.filter((id) => visibleIds.has(id))
  } catch (error) {
    uni.showToast({ title: '题库加载失败', icon: 'none' })
  } finally {
    questionsLoading.value = false
  }
}

async function loadQuestionStats() {
  try {
    const [activeResponse, archivedResponse] = await Promise.all([
      fetchAdminQuestions({ status: 'active', limit: 1, offset: 0 }),
      fetchAdminQuestions({ status: 'archived', limit: 1, offset: 0 })
    ])
    questionStats.active = Number(activeResponse?.count || 0)
    questionStats.archived = Number(archivedResponse?.count || 0)
    questionStats.pendingReview = 0
  } catch (error) {
    questionStats.active = 0
    questionStats.archived = 0
    questionStats.pendingReview = 0
  }
}

function getOptionIndex(options, value) {
  const index = options.findIndex((item) => item.value === value)
  return index >= 0 ? index : 0
}

function handleQuestionSubjectChange(event) {
  const index = Number(event?.detail?.value || 0)
  questionFilters.subject = questionSubjectOptions[index]?.value || ''
  questionFilters.module = ''
  loadQuestions()
}

function handleQuestionModuleChange(event) {
  const index = Number(event?.detail?.value || 0)
  questionFilters.module = questionModuleOptions.value[index]?.value || ''
  loadQuestions()
}

function handleQuestionDifficultyChange(event) {
  const index = Number(event?.detail?.value || 0)
  questionFilters.difficulty = questionDifficultyOptions[index]?.value || ''
  loadQuestions()
}

function handleQuestionStatusChange(event) {
  const index = Number(event?.detail?.value || 0)
  questionFilters.status = questionStatusOptions[index]?.value || ''
  loadQuestions()
}

function showComingSoon(label) {
  uni.showToast({ title: `${label}后续接入`, icon: 'none' })
}

function previewQuestionStem(stem) {
  const text = String(stem || '未填写题干').replace(/\s+/g, ' ').trim()
  if (text.length <= 58) return text
  return `${text.slice(0, 58)}...`
}

function questionStatusTone(status) {
  if (status === 'archived') return 'archived'
  if (status === 'pending' || status === 'pending_review') return 'pending'
  if (status === 'needs_review' || status === 'rejected') return 'warning'
  return 'published'
}

function isQuestionSelected(id) {
  return selectedQuestionIdSet.value.has(id)
}

function toggleQuestionSelection(id) {
  if (!id) return
  if (selectedQuestionIdSet.value.has(id)) {
    selectedQuestionIds.value = selectedQuestionIds.value.filter((item) => item !== id)
    return
  }
  selectedQuestionIds.value = [...selectedQuestionIds.value, id]
}

function toggleSelectAllQuestions() {
  if (questions.value.length === 0) {
    uni.showToast({ title: '当前没有可选题目', icon: 'none' })
    return
  }
  if (allVisibleQuestionsSelected.value) {
    const visibleIds = new Set(questions.value.map((item) => item.id))
    selectedQuestionIds.value = selectedQuestionIds.value.filter((id) => !visibleIds.has(id))
    return
  }
  const mergedIds = new Set(selectedQuestionIds.value)
  questions.value.forEach((item) => mergedIds.add(item.id))
  selectedQuestionIds.value = Array.from(mergedIds)
}

function archiveSelectedQuestions() {
  updateSelectedQuestionStatus('archived')
}

function publishSelectedQuestions() {
  updateSelectedQuestionStatus('active')
}

function updateSelectedQuestionStatus(nextStatus) {
  const ids = [...selectedQuestionIds.value]
  if (ids.length === 0) {
    uni.showToast({ title: '请先选择题目', icon: 'none' })
    return
  }
  const isArchive = nextStatus === 'archived'
  uni.showModal({
    title: isArchive ? '确认归档所选题目？' : '确认发布所选题目？',
    content: isArchive
      ? `将归档 ${ids.length} 道题，归档后不会进入普通刷题抽题。`
      : `将发布 ${ids.length} 道题，发布后会进入可刷题范围。`,
    confirmText: isArchive ? '归档' : '发布',
    confirmColor: isArchive ? '#16a34a' : '#2563eb',
    success: async (result) => {
      if (!result.confirm) return
      try {
        await Promise.all(ids.map((id) => updateAdminQuestionStatus(id, { status: nextStatus })))
        selectedQuestionIds.value = []
        uni.showToast({ title: isArchive ? '已归档' : '已发布', icon: 'success' })
        await refreshQuestionManager()
      } catch (error) {
        uni.showToast({ title: '批量状态更新失败', icon: 'none' })
      }
    }
  })
}

async function loadMessages() {
  messagesLoading.value = true
  try {
    const response = await fetchAdminMessages({ limit: 50, offset: 0 })
    officialMessageItems.value = response.items || []
  } catch (error) {
    uni.showToast({ title: '消息加载失败', icon: 'none' })
  } finally {
    messagesLoading.value = false
  }
}

function resetMessageForm() {
  messageForm.id = ''
  messageForm.title = ''
  messageForm.content = ''
  messageForm.status = 'draft'
  messageForm.expires_at = ''
}

function editOfficialMessage(item) {
  messageForm.id = item.id || ''
  messageForm.title = item.title || ''
  messageForm.content = item.content || ''
  messageForm.status = item.status || 'draft'
  messageForm.expires_at = item.expires_at || ''
}

function messageStatusText(status) {
  const map = {
    draft: '草稿',
    published: '已发布',
    archived: '已归档'
  }
  return map[status] || '草稿'
}

async function saveOfficialMessage() {
  if (!messageForm.title || !messageForm.content) {
    uni.showToast({ title: '请填写标题和内容', icon: 'none' })
    return
  }
  const payload = {
    title: messageForm.title,
    content: messageForm.content,
    status: messageForm.status,
    expires_at: messageForm.expires_at || null
  }
  try {
    if (messageForm.id) {
      await updateAdminMessage(messageForm.id, payload)
      uni.showToast({ title: '消息已保存', icon: 'success' })
    } else {
      await createAdminMessage(payload)
      uni.showToast({ title: payload.status === 'published' ? '消息已发布' : '消息已创建', icon: 'success' })
    }
    resetMessageForm()
    await loadMessages()
  } catch (error) {
    uni.showToast({ title: '消息保存失败', icon: 'none' })
  }
}

function openMembershipActions(user) {
  const isActiveMember = user.membership_status === 'active'
  const itemList = isActiveMember
    ? ['续期 1 个月', '续期 3 个月', '续期 6 个月', '续期 12 个月', '取消会员']
    : ['开通 1 个月', '开通 3 个月', '开通 6 个月', '开通 12 个月']

  uni.showActionSheet({
    itemList,
    success: async ({ tapIndex }) => {
      if (isActiveMember && tapIndex === 4) {
        await confirmCancelMembership(user)
        return
      }
      const months = [1, 3, 6, 12][tapIndex] || 1
      await grantMembership(user, months, isActiveMember)
    }
  })
}

function membershipActionLabel(user) {
  return user.membership_status === 'active' ? '管理会员' : '开通会员'
}

async function grantMembership(user, months, isRenewal = false) {
  try {
    await grantAdminMembership(user.id, { months, plan: `admin_${months}_month` })
    uni.showToast({ title: isRenewal ? '会员已续期' : '会员已授权', icon: 'success' })
    await Promise.all([loadUsers(), loadOverview()])
  } catch (error) {
    uni.showToast({ title: isRenewal ? '续期失败' : '授权失败', icon: 'none' })
  }
}

function confirmCancelMembership(user) {
  return new Promise((resolve) => {
    uni.showModal({
      title: '确认取消会员？',
      content: `将取消 ${user.email || user.phone || '该用户'} 的会员权益。取消后不会删除用户账号和刷题记录。`,
      confirmText: '取消会员',
      confirmColor: '#ef4444',
      success: async (result) => {
        if (!result.confirm) {
          resolve(false)
          return
        }
        try {
          await cancelAdminMembership(user.id)
          uni.showToast({ title: '会员已取消', icon: 'success' })
          await Promise.all([loadUsers(), loadOverview()])
          resolve(true)
        } catch (error) {
          uni.showToast({ title: '取消失败', icon: 'none' })
          resolve(false)
        }
      },
      fail: () => resolve(false)
    })
  })
}

async function openUser(user) {
  try {
    const detail = await fetchAdminUserDetail(user.id)
    const profile = detail.profile || user
    const summary = detail.answer_summary || {}
    const latestOrder = (detail.membership_orders || [])[0]
    const latestMembershipAction = (detail.admin_actions || []).find((action) => (
      action.action === 'grant_membership' || action.action === 'cancel_membership'
    ))
    const content = [
      `账号：${profile.email || profile.phone || '未绑定'}`,
      `昵称：${profile.nickname || '未设置'}`,
      `目标：${profile.exam_target || '未设置'}`,
      `角色：${profile.role || 'user'}`,
      `会员：${profile.membership_status || 'inactive'}`,
      profile.membership_expires_at ? `到期：${formatDate(profile.membership_expires_at)}` : '',
      `累计作答：${summary.total || 0} 题，正确 ${summary.correct || 0} 题，正确率 ${summary.accuracy || 0}%`,
      latestOrder ? `最近订单：${latestOrder.plan_code || '-'} / ${latestOrder.status || '-'}` : '暂无会员订单记录',
      latestMembershipAction ? `最近后台操作：${membershipActionText(latestMembershipAction)} / ${formatDate(latestMembershipAction.created_at)}` : '暂无后台会员操作记录'
    ].filter(Boolean).join('\n')
    uni.showModal({ title: '用户详情', content, showCancel: false, confirmText: '关闭' })
  } catch (error) {
    uni.showToast({ title: '用户详情加载失败', icon: 'none' })
  }
}

function membershipActionText(action) {
  if (action.action === 'cancel_membership') return '取消会员'
  return `授权 ${action.details?.months || '-'} 个月`
}

function feedbackStatusText(status) {
  const map = {
    open: '待处理',
    reviewed: '已查看',
    resolved: '已解决',
    ignored: '忽略'
  }
  return map[status] || '待处理'
}

function questionStatusText(status) {
  const map = {
    active: '已发布',
    archived: '已归档',
    pending: '待审核',
    pending_review: '待审核',
    needs_review: '需修改',
    rejected: '需修改'
  }
  return map[status] || '待审核'
}

async function openFeedback(item) {
  let latest = item
  try {
    // The list already contains full rows; keep this lightweight for now.
    latest = item
  } catch (error) {
    latest = item
  }
  uni.showModal({
    title: latest.feedback_type || '用户反馈',
    content: `${latest.content || ''}\n\n状态：${feedbackStatusText(latest.status)}\n联系方式：${latest.contact || '未填写'}\n备注：${latest.admin_note || '无'}`,
    showCancel: false,
    confirmText: '知道了'
  })
}

function openFeedbackStatusAction(item) {
  uni.showActionSheet({
    itemList: ['标记已查看', '标记已解决', '标记忽略', '重新打开'],
    success: async ({ tapIndex }) => {
      const statuses = ['reviewed', 'resolved', 'ignored', 'open']
      const nextStatus = statuses[tapIndex] || 'reviewed'
      try {
        await updateAdminFeedbackStatus(item.id, { status: nextStatus })
        uni.showToast({ title: '反馈状态已更新', icon: 'success' })
        await Promise.all([loadFeedback(), loadOverview()])
      } catch (error) {
        uni.showToast({ title: '状态更新失败', icon: 'none' })
      }
    }
  })
}

async function openQuestion(item) {
  let question = item
  try {
    const response = await fetchAdminQuestionDetail(item.id)
    question = response.question || item
  } catch (error) {
    question = item
  }
  const content = [
    question.stem,
    `A. ${question.option_a}`,
    `B. ${question.option_b}`,
    `C. ${question.option_c}`,
    `D. ${question.option_d}`,
    `答案：${question.answer}`,
    `状态：${questionStatusText(question.status)}`,
    question.explanation ? `解析：${question.explanation}` : ''
  ].filter(Boolean).join('\n')
  uni.showModal({
    title: `${question.subject || '题目'}详情`,
    content,
    showCancel: false,
    confirmText: '关闭'
  })
}

function toggleQuestionStatus(item) {
  const nextStatus = item.status === 'archived' ? 'active' : 'archived'
  uni.showModal({
    title: nextStatus === 'archived' ? '确认下架题目？' : '确认恢复题目？',
    content: nextStatus === 'archived'
      ? '下架后，该题不会再进入普通刷题抽题，但历史记录仍保留。'
      : '恢复后，该题会重新进入普通刷题抽题范围。',
    confirmText: nextStatus === 'archived' ? '下架' : '恢复',
    confirmColor: nextStatus === 'archived' ? '#ef4444' : '#16a34a',
    success: async (result) => {
      if (!result.confirm) return
      try {
        await updateAdminQuestionStatus(item.id, { status: nextStatus })
        uni.showToast({ title: nextStatus === 'archived' ? '题目已归档' : '题目已发布', icon: 'success' })
        await refreshQuestionManager()
      } catch (error) {
        uni.showToast({ title: '题目状态更新失败', icon: 'none' })
      }
    }
  })
}

function formatDate(value) {
  if (!value) return '无日期'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 10)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.redirectTo({ url: '/pages/home/index?tab=profile' })
    }
  })
}
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  padding: 24rpx 24rpx 170rpx;
  background: linear-gradient(180deg, #eef5ff 0%, #f6f8fb 28%, #f6f8fb 100%);
  box-sizing: border-box;
}

.admin-page.question-mode {
  padding-bottom: calc(env(safe-area-inset-bottom) + 270rpx);
  background:
    radial-gradient(circle at 12% 0%, rgba(186, 226, 255, 0.72) 0, rgba(186, 226, 255, 0) 300rpx),
    radial-gradient(circle at 92% 2%, rgba(205, 249, 216, 0.78) 0, rgba(205, 249, 216, 0) 320rpx),
    linear-gradient(180deg, #f7fbff 0%, #ffffff 48%, #f7fbff 100%);
}

.admin-hero {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100rpx;
  padding: 2rpx 96rpx 12rpx;
  margin-bottom: 12rpx;
  box-sizing: border-box;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 70rpx;
  height: 70rpx;
  transform: translateY(-50%);
  border-radius: 22rpx;
  border: 0;
  background: #ffffff;
  color: #101828;
  font-size: 42rpx;
  line-height: 1;
  box-shadow: 0 14rpx 34rpx rgba(15, 23, 42, 0.08);
}

.back-btn::after,
.hero-refresh-btn::after,
.tab-btn::after,
.ghost-btn::after,
.search-btn::after,
.small-btn::after,
.status-chip::after,
.question-action-btn::after,
.question-check::after,
.question-edit-btn::after,
.question-bulk-btn::after {
  border: 0;
}

.hero-refresh-btn {
  position: absolute;
  right: 0;
  top: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 70rpx;
  height: 70rpx;
  margin: 0;
  transform: translateY(-50%);
  border: 0;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.68);
  color: #101828;
  font-size: 44rpx;
  line-height: 1;
  box-shadow: none;
}

.admin-heading {
  min-width: 0;
  text-align: center;
}

.admin-title {
  color: #101828;
  font-size: 38rpx;
  font-weight: 900;
  line-height: 1.2;
}

.admin-subtitle {
  margin-top: 8rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.35;
}

.state-card,
.panel-card {
  border-radius: 28rpx;
  background: #ffffff;
  border: 1rpx solid #e6edf6;
  box-shadow: 0 20rpx 50rpx rgba(15, 23, 42, 0.06);
}

.state-card {
  padding: 48rpx 34rpx;
  color: #667085;
  font-size: 28rpx;
}

.state-card.denied {
  color: #b42318;
  background: #fff7f5;
}

.state-title {
  color: #101828;
  font-size: 32rpx;
  font-weight: 900;
}

.state-copy {
  margin-top: 12rpx;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
  margin-bottom: 12rpx;
}

.stat-card {
  min-height: 118rpx;
  padding: 20rpx 22rpx;
  border-radius: 22rpx;
  background: #ffffff;
  border: 1rpx solid #e6edf6;
  box-sizing: border-box;
}

.stat-card.primary:first-child {
  background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
  border-color: #d7e6ff;
}

.stat-label {
  color: #667085;
  font-size: 24rpx;
  line-height: 1.25;
}

.stat-value {
  margin-top: 8rpx;
  color: #101828;
  font-size: 38rpx;
  font-weight: 900;
  line-height: 1.1;
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8rpx;
  margin-bottom: 18rpx;
  padding: 10rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.74);
  border: 1rpx solid #e6edf6;
}

.metric-item {
  min-width: 0;
  text-align: center;
}

.metric-label {
  display: block;
  color: #667085;
  font-size: 19rpx;
  line-height: 1.2;
}

.metric-value {
  display: block;
  margin-top: 4rpx;
  color: #101828;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1.15;
}

.tab-bar {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  margin-bottom: 20rpx;
  padding: 8rpx;
  border-radius: 24rpx;
  background: #ffffff;
  border: 1rpx solid #e6edf6;
  box-shadow: 0 12rpx 28rpx rgba(15, 23, 42, 0.05);
}

.tab-btn,
.ghost-btn,
.search-btn,
.small-btn {
  border: 0;
  border-radius: 20rpx;
  font-weight: 800;
}

.tab-btn {
  height: 60rpx;
  border-radius: 18rpx;
  color: #475467;
  background: transparent;
  font-size: 25rpx;
  box-shadow: none;
}

.tab-btn.active {
  color: #ffffff;
  background: #3b82f6;
  box-shadow: 0 10rpx 22rpx rgba(59, 130, 246, 0.24);
}

.panel-card {
  padding: 26rpx;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 22rpx;
}

.panel-head > view {
  min-width: 0;
  flex: 1;
}

.panel-head.compact {
  margin-top: 26rpx;
  margin-bottom: 14rpx;
}

.panel-title {
  color: #101828;
  font-size: 30rpx;
  font-weight: 900;
}

.panel-title.small {
  font-size: 26rpx;
}

.panel-subtitle {
  margin-top: 6rpx;
  color: #667085;
  font-size: 22rpx;
}

.ghost-btn {
  height: 56rpx;
  min-width: 96rpx;
  padding: 0 20rpx;
  color: #2563eb;
  background: #eff6ff;
  font-size: 24rpx;
  box-shadow: 0 8rpx 20rpx rgba(37, 99, 235, 0.08);
}

.refresh-btn {
  flex: 0 0 auto;
  height: 58rpx;
  min-width: 100rpx;
  margin-top: 2rpx;
  border-radius: 18rpx;
}

.search-row {
  display: flex;
  gap: 14rpx;
  align-items: center;
  margin-bottom: 14rpx;
}

.filter-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10rpx;
  margin-bottom: 22rpx;
}

.filter-chip {
  height: 52rpx;
  border: 0;
  border-radius: 16rpx;
  color: #475467;
  background: #f3f6fb;
  font-size: 22rpx;
  font-weight: 800;
}

.filter-chip::after {
  border: 0;
}

.filter-chip.active {
  color: #2563eb;
  background: #eff6ff;
}

.search-input {
  min-width: 0;
  height: 68rpx;
  padding: 0 22rpx;
  border-radius: 18rpx;
  background: #f3f6fb;
  border: 1rpx solid #dbe6f5;
  color: #101828;
  font-size: 26rpx;
  box-sizing: border-box;
}

.search-row .search-input {
  flex: 1;
}

.search-btn {
  width: 128rpx;
  height: 68rpx;
  color: #ffffff;
  background: #3b82f6;
  font-size: 26rpx;
}

.search-btn.wide {
  width: 100%;
  margin: 16rpx 0 22rpx;
}

.inline-state {
  padding: 36rpx 0;
  color: #667085;
  text-align: center;
  font-size: 26rpx;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.record-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f8fbff;
  border: 1rpx solid #e3ebf7;
}

.feedback-card {
  display: block;
}

.record-main {
  min-width: 0;
  flex: 1;
}

.record-title {
  color: #101828;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 1.45;
  word-break: break-all;
}

.record-subtitle {
  margin-top: 6rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.5;
}

.clamp {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.badge-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 12rpx;
}

.badge {
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  color: #475467;
  background: #eef2f7;
  font-size: 21rpx;
  font-weight: 800;
}

.badge.active {
  color: #15803d;
  background: #dcfce7;
}

.badge.admin {
  color: #5b21b6;
  background: #ede9fe;
}

.badge.archived {
  color: #b42318;
  background: #fee4e2;
}

.record-date {
  color: #98a2b3;
  font-size: 21rpx;
}

.small-btn {
  flex: 0 0 auto;
  width: 164rpx;
  height: 58rpx;
  color: #ffffff;
  background: #0f172a;
  font-size: 23rpx;
}

.inline-action {
  margin-top: 16rpx;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.question-manager {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.question-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12rpx;
}

.question-stat-card {
  min-height: 150rpx;
  padding: 22rpx 18rpx 20rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1rpx solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 18rpx 44rpx rgba(15, 23, 42, 0.08);
  box-sizing: border-box;
}

.question-stat-head {
  display: flex;
  align-items: center;
  gap: 10rpx;
  min-width: 0;
}

.question-stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34rpx;
  height: 34rpx;
  color: #2563eb;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 1;
}

.question-stat-card.orange .question-stat-icon,
.question-stat-card.orange .question-stat-value {
  color: #f97316;
}

.question-stat-card.green .question-stat-icon,
.question-stat-card.green .question-stat-value {
  color: #16a34a;
}

.question-stat-label {
  min-width: 0;
  color: #344054;
  font-size: 23rpx;
  font-weight: 700;
  line-height: 1.2;
  white-space: nowrap;
}

.question-stat-value {
  margin-top: 28rpx;
  color: #1d4ed8;
  font-size: 46rpx;
  font-weight: 900;
  line-height: 1;
}

.question-search-box {
  display: flex;
  align-items: center;
  gap: 16rpx;
  height: 78rpx;
  padding: 0 24rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.9);
  border: 1rpx solid #d5deeb;
  box-shadow: inset 0 1rpx 0 rgba(255, 255, 255, 0.8);
  box-sizing: border-box;
}

.question-search-icon {
  flex: 0 0 auto;
  color: #98a2b3;
  font-size: 42rpx;
  line-height: 1;
}

.question-search-input {
  min-width: 0;
  flex: 1;
  height: 78rpx;
  color: #101828;
  font-size: 27rpx;
  line-height: 78rpx;
}

.question-filter-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12rpx;
}

.question-filter-row picker {
  min-width: 0;
}

.question-filter-pill {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  height: 68rpx;
  padding: 0 10rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.84);
  border: 1rpx solid #d5deeb;
  color: #344054;
  font-size: 25rpx;
  font-weight: 800;
  line-height: 1;
  box-sizing: border-box;
  white-space: nowrap;
}

.question-filter-arrow {
  color: #667085;
  font-size: 22rpx;
  transform: translateY(-2rpx);
}

.question-action-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1.35fr;
  gap: 14rpx;
}

.question-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  min-width: 0;
  height: 74rpx;
  margin: 0;
  padding: 0 10rpx;
  border-radius: 12rpx;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1;
  box-sizing: border-box;
}

.question-action-btn.outline {
  color: #1769ff;
  background: rgba(255, 255, 255, 0.92);
  border: 1rpx solid #1769ff;
}

.question-action-btn.filled {
  color: #ffffff;
  background: linear-gradient(135deg, #0ea5b7 0%, #0891b2 100%);
  border: 1rpx solid #0891b2;
  box-shadow: 0 16rpx 30rpx rgba(8, 145, 178, 0.2);
}

.question-action-icon {
  font-size: 32rpx;
  font-weight: 900;
  line-height: 1;
}

.question-card-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.question-admin-card {
  display: flex;
  align-items: center;
  gap: 18rpx;
  min-height: 152rpx;
  padding: 26rpx 22rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid #edf2f7;
  box-shadow: 0 14rpx 38rpx rgba(15, 23, 42, 0.07);
  box-sizing: border-box;
}

.question-check {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34rpx;
  height: 34rpx;
  margin: 0;
  padding: 0;
  border-radius: 8rpx;
  border: 1rpx solid #98a2b3;
  background: #ffffff;
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1;
}

.question-check.checked {
  border-color: #1769ff;
  background: #1769ff;
}

.question-card-main {
  min-width: 0;
  flex: 1;
}

.question-chip-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10rpx;
}

.question-chip {
  max-width: 210rpx;
  padding: 7rpx 14rpx;
  border-radius: 10rpx;
  color: #1769ff;
  background: #eff6ff;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.question-stem-preview {
  margin-top: 18rpx;
  color: #101828;
  font-size: 27rpx;
  font-weight: 800;
  line-height: 1.45;
  word-break: break-word;
}

.question-status-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 18rpx;
}

.question-status-pill {
  padding: 8rpx 14rpx;
  border-radius: 12rpx;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 1;
}

.question-status-pill.published {
  color: #16a34a;
  background: #dcfce7;
}

.question-status-pill.archived {
  color: #64748b;
  background: #f1f5f9;
}

.question-status-pill.pending {
  color: #f97316;
  background: #fff7ed;
}

.question-status-pill.warning {
  color: #ea580c;
  background: #ffedd5;
}

.question-answer {
  color: #98a2b3;
  font-size: 22rpx;
  font-weight: 700;
}

.question-edit-btn {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  width: 132rpx;
  height: 64rpx;
  margin: 0;
  padding: 0;
  border-radius: 12rpx;
  border: 1rpx solid #1769ff;
  color: #1769ff;
  background: #ffffff;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 1;
}

.question-edit-icon {
  font-size: 28rpx;
  line-height: 1;
}

.question-bulk-bar {
  position: fixed;
  left: 24rpx;
  right: 24rpx;
  bottom: calc(env(safe-area-inset-bottom) + 24rpx);
  z-index: 30;
  display: grid;
  grid-template-columns: 1.05fr 1fr 0.8fr 0.8fr;
  align-items: center;
  gap: 12rpx;
  min-height: 86rpx;
  padding: 14rpx 22rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid #edf2f7;
  box-shadow: 0 12rpx 44rpx rgba(15, 23, 42, 0.12);
  box-sizing: border-box;
}

.question-selected-label {
  min-width: 0;
  color: #475467;
  font-size: 23rpx;
  font-weight: 700;
  white-space: nowrap;
}

.question-selected-count {
  color: #1769ff;
  font-size: 34rpx;
  font-weight: 900;
}

.question-bulk-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  min-width: 0;
  height: 60rpx;
  margin: 0;
  padding: 0 12rpx;
  border-radius: 12rpx;
  border: 1rpx solid #1769ff;
  color: #1769ff;
  background: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1;
  box-sizing: border-box;
}

.question-bulk-btn.archive {
  color: #16a34a;
  border-color: #16a34a;
}

.question-bulk-btn.publish {
  color: #1769ff;
  border-color: #1769ff;
}

.question-bulk-icon {
  font-size: 28rpx;
  line-height: 1;
}

.message-editor {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  padding: 18rpx;
  border-radius: 22rpx;
  background: #f8fbff;
  border: 1rpx solid #e3ebf7;
}

.message-textarea {
  min-height: 180rpx;
  padding: 18rpx 22rpx;
  border-radius: 18rpx;
  background: #ffffff;
  border: 1rpx solid #dbe6f5;
  color: #101828;
  font-size: 25rpx;
  line-height: 1.6;
  box-sizing: border-box;
}

.message-status-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.status-chip {
  height: 58rpx;
  border: 0;
  border-radius: 18rpx;
  background: #eef2f7;
  color: #475467;
  font-size: 23rpx;
  font-weight: 800;
}

.status-chip.active {
  background: #3b82f6;
  color: #ffffff;
}
</style>
