<template>
  <view class="admin-page">
    <view class="admin-hero">
      <button class="back-btn" @tap="goBack">‹</button>
      <view>
        <view class="admin-title">后台管理</view>
        <view class="admin-subtitle">用户、反馈与题库运营面板</view>
      </view>
    </view>

    <view v-if="loading" class="state-card">正在读取后台数据...</view>
    <view v-else-if="!allowed" class="state-card denied">
      <view class="state-title">无后台权限</view>
      <view class="state-copy">请使用管理员账号登录后再访问。</view>
    </view>

    <template v-else>
      <view class="stat-grid">
        <view v-for="item in overviewCards" :key="item.label" class="stat-card">
          <view class="stat-label">{{ item.label }}</view>
          <view class="stat-value">{{ item.value }}</view>
        </view>
      </view>

      <view class="tab-bar">
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
          <button class="ghost-btn" @tap="loadUsers">刷新</button>
        </view>
        <view class="search-row">
          <input v-model="userSearch" class="search-input" placeholder="搜索邮箱" confirm-type="search" @confirm="loadUsers" />
          <button class="search-btn" @tap="loadUsers">搜索</button>
        </view>
        <view v-if="usersLoading" class="inline-state">正在加载用户...</view>
        <view v-else-if="users.length === 0" class="inline-state">暂无用户数据</view>
        <view v-else class="record-list">
          <view v-for="user in users" :key="user.id" class="record-card" @tap="openUser(user)">
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
            <button class="small-btn" @tap.stop="openMembershipActions(user)">会员操作</button>
          </view>
        </view>
      </view>

      <view v-if="activeTab === 'feedback'" class="panel-card">
        <view class="panel-head">
          <view>
            <view class="panel-title">用户反馈</view>
            <view class="panel-subtitle">来自 App 内帮助与反馈</view>
          </view>
          <button class="ghost-btn" @tap="loadFeedback">刷新</button>
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

      <view v-if="activeTab === 'questions'" class="panel-card">
        <view class="panel-head">
          <view>
            <view class="panel-title">题库查看</view>
            <view class="panel-subtitle">按考试、科目、模块和题干检索</view>
          </view>
          <button class="ghost-btn" @tap="loadQuestions">刷新</button>
        </view>
        <view class="filter-grid">
          <input v-model="questionFilters.exam_code" class="search-input" placeholder="考试代码，如 Z001" />
          <input v-model="questionFilters.subject" class="search-input" placeholder="科目，如 中华文化" />
          <input v-model="questionFilters.module" class="search-input" placeholder="模块" />
          <input v-model="questionFilters.status" class="search-input" placeholder="状态 active/archived" />
          <input v-model="questionFilters.search" class="search-input" placeholder="题干关键词" />
        </view>
        <button class="search-btn wide" @tap="loadQuestions">筛选题目</button>
        <view v-if="questionsLoading" class="inline-state">正在加载题库...</view>
        <view v-else-if="questions.length === 0" class="inline-state">暂无题目</view>
        <view v-else class="record-list">
          <view v-for="item in questions" :key="item.id" class="record-card" @tap="openQuestion(item)">
            <view class="record-title">{{ item.stem }}</view>
            <view class="record-subtitle">
              {{ item.exam_code }} / {{ item.subject }} / {{ item.module }} / {{ item.submodule }}
            </view>
            <view class="badge-row">
              <text class="badge">难度 {{ item.difficulty }}</text>
              <text class="badge" :class="{ archived: item.status === 'archived' }">{{ questionStatusText(item.status) }}</text>
              <text class="record-date">答案 {{ item.answer }}</text>
            </view>
            <button class="small-btn inline-action" @tap.stop="toggleQuestionStatus(item)">
              {{ item.status === 'archived' ? '恢复' : '下架' }}
            </button>
          </view>
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
          <button class="ghost-btn" @tap="loadMessages">刷新</button>
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

const ADMIN_EMAIL = '2221073755@qq.com'
const loading = ref(true)
const allowed = ref(false)
const overview = ref({})
const activeTab = ref('users')
const users = ref([])
const usersLoading = ref(false)
const userSearch = ref('')
const feedbackItems = ref([])
const feedbackLoading = ref(false)
const questions = ref([])
const questionsLoading = ref(false)
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
  status: '',
  search: ''
})

const tabs = [
  { key: 'users', label: '用户' },
  { key: 'feedback', label: '反馈' },
  { key: 'questions', label: '题库' },
  { key: 'messages', label: '消息' }
]

const overviewCards = computed(() => [
  { label: '总用户', value: overview.value.total_users || 0 },
  { label: '今日活跃', value: overview.value.active_today || 0 },
  { label: '本周活跃', value: overview.value.active_week || 0 },
  { label: '本月活跃', value: overview.value.active_month || 0 },
  { label: '会员数', value: overview.value.active_members || 0 },
  { label: '题库量', value: overview.value.total_questions || 0 },
  { label: '反馈数', value: overview.value.total_feedback || 0 },
  { label: '待处理', value: overview.value.pending_feedback || 0 }
])

onLoad(async () => {
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
      await Promise.all([loadOverview(), loadUsers()])
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
  if (tab === 'questions' && questions.value.length === 0) await loadQuestions()
  if (tab === 'messages' && officialMessageItems.value.length === 0) await loadMessages()
}

async function loadUsers() {
  usersLoading.value = true
  try {
    const response = await fetchAdminUsers({
      search: userSearch.value || undefined,
      limit: 30,
      offset: 0
    })
    users.value = response.items || []
  } catch (error) {
    uni.showToast({ title: '用户数据加载失败', icon: 'none' })
  } finally {
    usersLoading.value = false
  }
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
    questions.value = response.items || []
  } catch (error) {
    uni.showToast({ title: '题库加载失败', icon: 'none' })
  } finally {
    questionsLoading.value = false
  }
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
  return status === 'archived' ? '已下架' : '可刷题'
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
        uni.showToast({ title: nextStatus === 'archived' ? '题目已下架' : '题目已恢复', icon: 'success' })
        await Promise.all([loadQuestions(), loadOverview()])
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
  padding: 36rpx 24rpx 80rpx;
  background: linear-gradient(180deg, #eef5ff 0%, #f6f8fb 28%, #f6f8fb 100%);
  box-sizing: border-box;
}

.admin-hero {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-bottom: 20rpx;
}

.back-btn {
  width: 68rpx;
  height: 68rpx;
  border-radius: 22rpx;
  border: 0;
  background: #ffffff;
  color: #101828;
  font-size: 42rpx;
  box-shadow: 0 12rpx 32rpx rgba(15, 23, 42, 0.08);
}

.admin-title {
  color: #101828;
  font-size: 38rpx;
  font-weight: 900;
}

.admin-subtitle {
  margin-top: 4rpx;
  color: #667085;
  font-size: 23rpx;
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
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10rpx;
  margin-bottom: 18rpx;
}

.stat-card {
  min-height: 108rpx;
  padding: 16rpx 14rpx;
  border-radius: 18rpx;
  background: #ffffff;
  border: 1rpx solid #e6edf6;
  box-sizing: border-box;
}

.stat-label {
  color: #667085;
  font-size: 20rpx;
  line-height: 1.25;
}

.stat-value {
  margin-top: 6rpx;
  color: #101828;
  font-size: 32rpx;
  font-weight: 900;
  line-height: 1.1;
}

.tab-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10rpx;
  margin-bottom: 18rpx;
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
  height: 64rpx;
  color: #475467;
  background: #ffffff;
  font-size: 26rpx;
}

.tab-btn.active {
  color: #ffffff;
  background: #3b82f6;
}

.panel-card {
  padding: 24rpx;
}

.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 22rpx;
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
  padding: 0 22rpx;
  color: #2563eb;
  background: #eff6ff;
  font-size: 24rpx;
}

.search-row {
  display: flex;
  gap: 14rpx;
  margin-bottom: 22rpx;
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
  padding: 20rpx;
  border-radius: 20rpx;
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
  width: 136rpx;
  height: 58rpx;
  color: #ffffff;
  background: #0f172a;
  font-size: 22rpx;
}

.inline-action {
  margin-top: 16rpx;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
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
