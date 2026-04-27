<template>
  <view class="page home-page">
    <template v-if="activeTab === 'home'">
      <view class="home-dashboard">
        <view class="home-header">
          <view class="brand-line">
            <text class="brand-title">港澳台考研刷题</text>
            <text class="brand-badge">{{ examCode }}</text>
          </view>
          <view class="profile-entry" @tap="activeTab = 'profile'">
            <text>{{ avatarText }}</text>
          </view>
        </view>

        <view class="welcome-card">
          <view class="welcome-main">
            <view class="wave-icon">👋</view>
            <view class="welcome-copy">
              <text class="welcome-title">{{ dashboard.userName }}，今天刷一组题吧</text>
              <text class="welcome-subtitle">登录后可直接刷真题并同步错题本</text>
            </view>
            <view class="hero-illustration">📋</view>
          </view>

          <view class="stats-card">
            <view class="stat-item">
              <text class="stat-value">{{ homeStats.weeklyAnswers }}</text>
              <text class="stat-label">本周刷题</text>
            </view>
            <view class="stat-divider"></view>
            <view class="stat-item">
              <text class="stat-value">{{ homeStats.accuracy }}</text>
              <text class="stat-label">总正确率</text>
            </view>
            <view class="stat-divider"></view>
            <view class="stat-item">
              <text class="stat-value">{{ homeStats.wrongCount }}</text>
              <text class="stat-label">错题数</text>
            </view>
          </view>
        </view>

        <view class="module-grid">
          <ModuleCard
            v-for="(item, index) in moduleCards"
            :key="item.key"
            :item="item"
            :index="index + 1"
            @select="goModule"
          />
        </view>

      </view>
    </template>

    <template v-else-if="activeTab === 'mistakes'">
      <PageHeader
        eyebrow="错题本"
        title="自动归档的高频错题"
        :subtitle="mistakeSubtitle"
      />
      <SectionCard title="最近需要重刷" subtitle="按薄弱标签自动聚合">
        <view v-if="!isAuthed" class="state-box warning">登录后才能查看你的真实错题本。</view>
        <view v-else class="filter-card">
          <scroll-view scroll-x class="filter-scroll">
            <button
              v-for="item in subjectFilters"
              :key="item"
              class="filter-chip"
              :class="{ active: wrongFilters.subject === item }"
              @tap="setWrongFilter('subject', item)"
            >
              {{ item || '全部科目' }}
            </button>
          </scroll-view>
          <scroll-view scroll-x class="filter-scroll">
            <button
              v-for="item in moduleFilters"
              :key="item"
              class="filter-chip"
              :class="{ active: wrongFilters.module === item }"
              @tap="setWrongFilter('module', item)"
            >
              {{ item || '全部模块' }}
            </button>
          </scroll-view>
          <scroll-view scroll-x class="filter-scroll">
            <button
              v-for="item in submoduleFilters"
              :key="item"
              class="filter-chip"
              :class="{ active: wrongFilters.submodule === item }"
              @tap="setWrongFilter('submodule', item)"
            >
              {{ item || '全部子模块' }}
            </button>
          </scroll-view>
        </view>
        <view v-if="wrongLoading" class="state-box">正在读取真实错题记录...</view>
        <view v-else-if="wrongError" class="state-box warning">{{ wrongError }}</view>
        <view v-else-if="isAuthed && filteredMistakes.length === 0" class="state-box">当前筛选条件下还没有错题。</view>
        <MistakeList :items="fullMistakes" @select="openWrongDetail" />
      </SectionCard>

      <SectionCard v-if="selectedWrongDetail" title="错题详情" subtitle="查看完整题目、最近选择、正确答案与解析。">
        <view class="wrong-detail">
          <view class="wrong-stem">{{ selectedWrongDetail.question.stem }}</view>
          <view class="wrong-meta">
            {{ selectedWrongDetail.question.subject }} / {{ selectedWrongDetail.question.module }} / {{ selectedWrongDetail.question.submodule }}
          </view>
          <view class="wrong-options">
            <button
              v-for="option in wrongDetailOptions"
              :key="option.key"
              class="wrong-option"
              :class="getWrongOptionClass(option.key)"
              @tap="selectReviewAnswer(option.key)"
            >
              <text class="option-key">{{ option.key }}</text>
              <text>{{ option.text }}</text>
            </button>
          </view>
          <view class="answer-line">最近一次选择：{{ selectedWrongDetail.latest_selected_answer || '暂无记录' }}</view>
          <view class="answer-line">正确答案：{{ selectedWrongDetail.question.answer }}</view>
          <view class="explain-text">{{ selectedWrongDetail.question.explanation }}</view>
          <view v-if="reviewResultText" class="state-box" :class="{ mastered: reviewMastered }">{{ reviewResultText }}</view>
          <view class="detail-actions">
            <button class="task-btn" :disabled="!reviewAnswer || reviewingWrong" @tap="submitWrongReview">
              {{ reviewingWrong ? '提交中...' : '重做错题' }}
            </button>
            <button class="task-btn ghost" @tap="closeWrongDetail">收起详情</button>
          </view>
        </view>
      </SectionCard>
    </template>

    <template v-else-if="activeTab === 'report'">
      <PageHeader
        eyebrow="AI 诊断"
        title="提分路径已生成"
        :subtitle="reportSubtitle"
      />

      <view v-if="reportLoading" class="state-box">正在生成真实能力报告...</view>
      <view v-else-if="reportError" class="state-box warning">{{ reportError }}</view>
      <ReportRadarMock :metrics="report.metrics" />

      <SectionCard title="真实统计概览" subtitle="按正确率分级：稳定 / 一般 / 薄弱 / 重点补强">
        <view v-if="!isAuthed" class="state-box warning">登录并完成几道题后，这里会显示你的真实能力统计。</view>
        <view v-else-if="report.items.length === 0" class="state-box">暂无能力统计。先完成一轮专项或综合刷题吧。</view>
        <view v-else class="ability-list">
          <view v-for="item in report.items" :key="item.id" class="ability-row">
            <view>
              <view class="ability-title">{{ item.subject }} · {{ item.module }}</view>
              <view class="ability-sub">{{ item.submodule }} · 已做 {{ item.total_count }} 题</view>
            </view>
            <view class="ability-pill" :class="levelClass(item.level)">
              {{ Math.round(item.accuracy) }}% · {{ item.level }}
            </view>
          </view>
        </view>
      </SectionCard>

      <SectionCard title="每日训练计划" subtitle="根据当前最低正确率的知识点自动生成，暂不接 AI。">
        <view v-if="dailyPlan.length === 0" class="state-box">暂无真实薄弱项，先完成一轮练习后会自动生成训练计划。</view>
        <view v-else class="daily-list">
          <view v-for="item in dailyPlan" :key="item.title" class="daily-card">
            <view>
              <view class="daily-title">{{ item.title }}</view>
              <view class="daily-desc">{{ item.desc }}</view>
            </view>
            <button class="task-btn" @tap="goTaskPractice(item)">开始</button>
          </view>
        </view>
      </SectionCard>

      <view class="diagnosis-card">
        <view class="diagnosis-title">AI 诊断结论</view>
        <view class="diagnosis-text">{{ report.diagnosis }}</view>
      </view>

      <SectionCard title="Pro 预览：深度 AI 诊断即将开放" subtitle="免费用户当前可查看基础统计；Pro 将提供更细的提分路径。">
        <view class="pro-preview">
          <view v-for="item in proPreviewItems" :key="item" class="pro-preview-item">{{ item }}</view>
        </view>
        <button class="primary-button pro-btn" @tap="goPro">查看会员中心 / Pro 功能</button>
      </SectionCard>

      <SectionCard title="行动建议" subtitle="根据当前短板推荐优先训练方向">
        <view class="task-list">
          <view v-for="task in report.tasks" :key="task.title" class="task-item">
            <view class="task-copy">
              <view class="task-title">{{ task.title }}</view>
              <view class="task-desc">{{ task.desc }}</view>
            </view>
            <button class="task-btn" @tap="goTaskPractice(task)">{{ task.action }}</button>
          </view>
        </view>
      </SectionCard>

      <button class="unlock-btn" @tap="showMockToast">解锁完整 AI 诊断与专属提分计划</button>
    </template>

    <template v-else>
      <view class="profile-dashboard">
        <view class="profile-top-title">港澳台考研刷题</view>

        <view class="account-card" @tap="isAuthed ? null : goLogin()">
          <view class="account-avatar">{{ profileAvatarText }}</view>
          <view class="account-main">
            <view class="account-name-row">
              <text class="account-name">{{ profile.userName }}</text>
              <text class="account-badge">{{ profile.badge }}</text>
            </view>
            <view class="account-desc">{{ isAuthed ? profile.subtitle : '登录后同步学习进度与数据' }}</view>
            <view class="exam-switch">
              <button
                v-for="option in examOptions"
                :key="option.code"
                class="exam-pill"
                :class="{ active: option.code === examCode }"
                @tap.stop="changeExam(option.code)"
              >
                {{ option.code }}
              </button>
            </view>
          </view>
          <view class="account-arrow">›</view>
        </view>

        <view class="member-card">
          <view class="member-copy">
            <view class="member-title">{{ isAuthed ? '学习数据已云端同步' : '登录享受完整功能' }}</view>
            <view class="member-subtitle">{{ isAuthed ? '错题本、能力报告和练习记录会持续更新' : '高效刷题，科学备考上岸' }}</view>
            <button class="member-login-btn" @tap="isAuthed ? openReport() : goLogin()">
              {{ isAuthed ? '查看报告' : '登录 / 注册' }}
            </button>
          </view>
          <view class="shield-art">✓</view>
          <view class="benefit-row">
            <view v-for="item in profileBenefits" :key="item.label" class="benefit-item" @tap="handleBenefit(item)">
              <view class="benefit-icon">{{ item.icon }}</view>
              <view class="benefit-label">{{ item.label }}</view>
            </view>
          </view>
        </view>

        <view class="profile-section-card">
          <view class="profile-section-title">练习工具</view>
          <view class="menu-list">
            <view v-for="item in practiceTools" :key="item.label" class="menu-row" @tap="handleMenu(item)">
              <view class="menu-icon" :class="item.tone">{{ item.icon }}</view>
              <view class="menu-copy">
                <view class="menu-title">{{ item.label }}</view>
                <view class="menu-subtitle">{{ item.desc }}</view>
              </view>
              <view class="menu-arrow">›</view>
            </view>
          </view>
        </view>

        <view class="profile-section-card">
          <view class="profile-section-title">其他服务</view>
          <view class="menu-list">
            <view v-for="item in serviceTools" :key="item.label" class="menu-row" @tap="handleMenu(item)">
              <view class="menu-icon" :class="item.tone">{{ item.icon }}</view>
              <view class="menu-copy">
                <view class="menu-title">{{ item.label }}</view>
                <view class="menu-subtitle">{{ item.desc }}</view>
              </view>
              <view class="menu-arrow">›</view>
            </view>
          </view>
        </view>

        <view v-if="isAuthed" class="logout-card" @tap="logout">退出登录</view>
      </view>
    </template>

    <BottomTabBar v-model="activeTab" :items="tabs" />
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import BottomTabBar from '../../components/BottomTabBar.vue'
import MistakeList from '../../components/MistakeList.vue'
import ModuleCard from '../../components/ModuleCard.vue'
import PageHeader from '../../components/PageHeader.vue'
import ReportRadarMock from '../../components/ReportRadarMock.vue'
import SectionCard from '../../components/SectionCard.vue'
import { updateProfile } from '../../api/auth'
import { fetchAbilityReport, fetchLearningSummary } from '../../api/reports'
import { fetchWrongQuestionDetail, fetchWrongQuestions, reviewWrongQuestion } from '../../api/wrongQuestions'
import {
  getFullMistakes,
  getHomeDashboard,
  getHomeModules,
  getProfileMock,
  getReportMock
} from '../../mock/appMock'
import { clearAuthSession, getAuthUser, isLoggedIn, updateAuthUser } from '../../utils/auth'
import { EXAM_OPTIONS } from '../../utils/exam'

const examOptions = EXAM_OPTIONS
const initialAuthUser = getAuthUser()
const examCode = ref(uni.getStorageSync('examCode') || initialAuthUser?.exam_target || 'Z001')
const activeTab = ref('home')
const authUser = ref(initialAuthUser)
const authed = ref(isLoggedIn())
const wrongItems = ref([])
const wrongLoading = ref(false)
const wrongError = ref('')
const abilityReport = ref(null)
const learningSummary = ref(null)
const reportLoading = ref(false)
const reportError = ref('')
const wrongFilters = ref({
  subject: '',
  module: '',
  submodule: ''
})
const selectedWrongDetail = ref(null)
const reviewAnswer = ref('')
const reviewingWrong = ref(false)
const reviewResultText = ref('')
const reviewMastered = ref(false)
const tabs = [
  { key: 'home', label: '首页', icon: '⌂' },
  { key: 'profile', label: '我的', icon: '☺' }
]
const proPreviewItems = [
  'AI 薄弱诊断：把低正确率知识点转成更清晰的错因总结',
  '错题同类加练：围绕错题自动推荐同 submodule 题目',
  '每日训练计划：每天 10-20 题，优先补最低正确率模块',
  '每周提分报告：总结正确率变化、刷题量和下周重点'
]
const profileBenefits = [
  { label: '云端同步', icon: '☁', action: 'sync' },
  { label: '收藏夹', icon: '☆', action: 'favorites' },
  { label: '学习报告', icon: '▥', action: 'report' },
  { label: 'AI 解析', icon: '⌘', action: 'soon' },
  { label: '专属推荐', icon: '👍', action: 'soon' }
]

const isAuthed = computed(() => authed.value)
const avatarText = computed(() => (dashboard.value.userName || '游').slice(0, 1))
const profileAvatarText = computed(() => (profile.value.userName || examCode.value || '游').slice(0, 1))

const dashboard = computed(() => {
  const base = getHomeDashboard(examCode.value)
  if (!isAuthed.value) {
    return {
      ...base,
      userName: '游客',
      statusText: '登录后可直接刷真实题目并同步错题本',
      heroTitle: '登录后开启本周刷题统计',
      heroSubtitle: '当前可以先浏览界面与 mock 内容；登录后即可直接使用真实题库、提交答案和能力统计。'
    }
  }

  const weeklyAnswers = Number(learningSummary.value?.weekly_answers || 0)
  const totalAnswers = Number(learningSummary.value?.total_answers || 0)
  const accuracy = Number(learningSummary.value?.accuracy || 0)

  return {
    ...base,
    userName: authUser.value?.nickname || authUser.value?.email || base.userName,
    statusText: '今日学习状态：已登录，可直连真实题库',
    heroTitle: `本周已刷真题：${weeklyAnswers} 道`,
    heroSubtitle: totalAnswers
      ? `累计已完成 ${totalAnswers} 道，当前总正确率 ${Math.round(accuracy)}%。继续刷题后，错题本和能力报告会自动同步。`
      : '你已经登录成功。本周刷题数暂为 0，完成第一轮练习后这里会自动更新真实数据。'
  }
})

const homeStats = computed(() => {
  if (!isAuthed.value) {
    return {
      weeklyAnswers: '0',
      accuracy: '--',
      wrongCount: '--'
    }
  }

  const weeklyAnswers = Number(learningSummary.value?.weekly_answers || 0)
  const totalAnswers = Number(learningSummary.value?.total_answers || 0)
  const accuracy = Number(learningSummary.value?.accuracy || 0)
  const wrongCount = Number(learningSummary.value?.wrong_question_count || wrongItems.value.length || 0)

  return {
    weeklyAnswers: String(weeklyAnswers),
    accuracy: totalAnswers ? `${Math.round(accuracy)}%` : '--',
    wrongCount: String(wrongCount)
  }
})

const moduleCards = computed(() => getHomeModules(examCode.value))
const realMistakes = computed(() => wrongItems.value.map(formatWrongQuestion))
const wrongSummaryCount = computed(() => {
  if (!isAuthed.value) return '0'
  return String(Number(learningSummary.value?.wrong_question_count || wrongItems.value.length || 0))
})
const reportStatus = computed(() => (isAuthed.value && abilityReport.value?.items?.length ? '已生成' : '未生成'))
const practiceTools = computed(() => [
  { label: '错题本', desc: `查看与重刷 ${wrongSummaryCount.value} 道错题`, icon: '▣', tone: 'blue', action: 'mistakes' },
  { label: '收藏夹', desc: '查看我收藏的重点题目', icon: '☆', tone: 'blue', action: 'favorites' },
  { label: '练习历史', desc: '回顾我的练习记录', icon: '◷', tone: 'green', action: 'history' },
  { label: '能力报告', desc: reportStatus.value === '已生成' ? '查看能力分析与提升建议' : '完成练习后生成报告', icon: '▧', tone: 'purple', action: 'report' }
])
const serviceTools = computed(() => [
  { label: '会员中心 / Pro 预览', desc: '查看 AI 诊断、同类加练与训练计划', icon: '◇', tone: 'dark', action: 'pro' },
  { label: '帮助与反馈', desc: '常见问题与意见反馈', icon: '?', tone: 'orange', action: 'feedback' },
  { label: '关于我们', desc: '了解项目定位与内测说明', icon: 'i', tone: 'blue', action: 'about' }
])
const filteredMistakes = computed(() =>
  realMistakes.value.filter((item) => {
    if (wrongFilters.value.subject && item.subject !== wrongFilters.value.subject) return false
    if (wrongFilters.value.module && item.module !== wrongFilters.value.module) return false
    if (wrongFilters.value.submodule && item.submodule !== wrongFilters.value.submodule) return false
    return true
  })
)
const fullMistakes = computed(() => (isAuthed.value ? filteredMistakes.value : getFullMistakes()))
const subjectFilters = computed(() => ['', '中华文化', '英语运用', '逻辑推理', '数学基础'])
const moduleFilters = computed(() => buildFilterOptions(realMistakes.value, 'module', { subject: wrongFilters.value.subject }))
const submoduleFilters = computed(() =>
  buildFilterOptions(realMistakes.value, 'submodule', {
    subject: wrongFilters.value.subject,
    module: wrongFilters.value.module
  })
)
const mistakeSubtitle = computed(() => {
  if (!isAuthed.value) {
    return '登录后会读取你的真实错题记录；当前展示示例内容。'
  }
  if (realMistakes.value.length) {
    return `已同步 ${realMistakes.value.length} 道真实错题，按最近错误时间排序。`
  }
  return '已连接真实错题接口，做错题后会自动归档到这里。'
})
const report = computed(() => buildReportView())
const dailyPlan = computed(() => report.value.tasks.slice(0, 3).map((item, index) => ({
  ...item,
  title: `今日任务 ${index + 1}：${item.subject} - ${item.submodule || item.module}`,
  desc: `建议先做 10 题。${item.desc}`
})))
const reportSubtitle = computed(() => {
  if (!isAuthed.value) {
    return '登录后会基于真实作答统计生成报告；当前展示示例诊断。'
  }
  if (abilityReport.value?.items?.length) {
    return '已根据真实作答记录生成能力报告，先用规则诊断，后续可升级 AI 总结。'
  }
  return '已连接真实能力统计接口，完成几道题后这里会出现你的准确率与薄弱项。'
})
const profile = computed(() => {
  const base = getProfileMock()
  if (!isAuthed.value) {
    return {
      ...base,
      userName: examCode.value,
      subtitle: '登录后同步学习进度与数据',
      badge: '游客',
      stats: [
        { label: '目标版本', value: examCode.value },
        { label: '累计刷题', value: '0 题' },
        { label: '总正确率', value: '--' },
        { label: '错题数', value: '0 题' }
      ]
    }
  }

  const totalAnswers = Number(learningSummary.value?.total_answers || 0)
  const accuracy = Number(learningSummary.value?.accuracy || 0)
  const wrongCount = Number(learningSummary.value?.wrong_question_count || wrongItems.value.length || 0)

  return {
    ...base,
    userName: authUser.value?.nickname || authUser.value?.email || base.userName,
    subtitle: authUser.value?.email || base.subtitle,
    badge: '已登录',
    stats: [
      { label: '目标版本', value: examCode.value },
      { label: '累计刷题', value: `${totalAnswers} 题` },
      { label: '总正确率', value: totalAnswers ? `${Math.round(accuracy)}%` : '暂无数据' },
      { label: '错题数', value: `${wrongCount} 题` }
    ]
  }
})

watch(examCode, (value) => {
  uni.setStorageSync('examCode', value)
  if (isAuthed.value) {
    loadAbilityReport()
    loadLearningSummary()
  }
})

onShow(() => {
  authUser.value = getAuthUser()
  authed.value = isLoggedIn()
  refreshLearningData()
})

async function changeExam(code) {
  if (!EXAM_OPTIONS.some((item) => item.code === code)) return
  const previousCode = examCode.value
  examCode.value = code
  const nextUser = updateAuthUser({ exam_target: code })
  if (nextUser) {
    authUser.value = nextUser
  }

  try {
    const remoteUser = await updateProfile({ exam_target: code })
    const syncedUser = updateAuthUser(remoteUser)
    if (syncedUser) {
      authUser.value = syncedUser
    }
    uni.showToast({ title: `目标版本已切换为 ${code}`, icon: 'none' })
  } catch (error) {
    examCode.value = previousCode
    const revertedUser = updateAuthUser({ exam_target: previousCode })
    if (revertedUser) {
      authUser.value = revertedUser
    }
    uni.showToast({ title: '目标版本同步失败，请稍后重试', icon: 'none' })
  }
}

function goModule(subject) {
  uni.setStorageSync('subject', subject)
  uni.navigateTo({ url: `/pages/practice/index?subject=${encodeURIComponent(subject)}` })
}

function goPractice() {
  uni.navigateTo({ url: '/pages/practice/index' })
}

function goTaskPractice(task) {
  if (task?.subject) {
    uni.setStorageSync('subject', task.subject)
    const query = [
      ['subject', task.subject],
      ['module', task.module || ''],
      ['submodule', task.submodule || '']
    ]
      .filter(([, value]) => value)
      .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
      .join('&')
    uni.navigateTo({ url: `/pages/practice/index?${query}` })
    return
  }
  goPractice()
}

function goLogin() {
  uni.navigateTo({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/home/index')}` })
}

function goPro() {
  uni.navigateTo({ url: '/pages/pro/index' })
}

function logout() {
  clearAuthSession()
  authUser.value = null
  authed.value = false
  uni.showToast({ title: '已退出登录', icon: 'none' })
}

function openMistakes() {
  activeTab.value = 'mistakes'
}

function openReport() {
  activeTab.value = 'report'
}

function handleBenefit(item) {
  if (!item) return
  if (item.action === 'mistakes') {
    openMistakes()
    return
  }
  if (item.action === 'report') {
    openReport()
    return
  }
  if (item.action === 'favorites') {
    uni.navigateTo({ url: '/pages/favorites/index' })
    return
  }
  if (item.action === 'sync') {
    uni.showToast({
      title: isAuthed.value ? '学习数据已自动同步' : '登录后开启云端同步',
      icon: 'none'
    })
    return
  }
  showMockToast()
}

function handleMenu(item) {
  if (!item) return
  if (item.action === 'mistakes') {
    openMistakes()
    return
  }
  if (item.action === 'report') {
    openReport()
    return
  }
  if (item.action === 'pro') {
    goPro()
    return
  }
  if (item.action === 'history') {
    uni.navigateTo({ url: '/pages/history/index' })
    return
  }
  if (item.action === 'favorites') {
    uni.navigateTo({ url: '/pages/favorites/index' })
    return
  }
  if (item.action === 'feedback') {
    copyFeedbackTemplate()
    return
  }
  if (item.action === 'about') {
    uni.showToast({ title: '当前版本：内测版，专注刷题闭环验证', icon: 'none' })
    return
  }
  showMockToast()
}

function showMockToast() {
  uni.showToast({ title: '完整 AI 诊断后续再接入', icon: 'none' })
}

function copyFeedbackTemplate() {
  const text = [
    '内测反馈：',
    '1. 我测试的是哪个功能？',
    '2. 遇到了什么问题或不顺手的地方？',
    '3. 题目质量是否满意？',
    '4. 我是否愿意为 AI诊断/同类加练/每日计划付费？'
  ].join('\n')
  uni.setClipboardData({
    data: text,
    success() {
      uni.showToast({ title: '反馈模板已复制', icon: 'none' })
    }
  })
}

async function refreshLearningData() {
  if (!isAuthed.value) {
    wrongItems.value = []
    abilityReport.value = null
    learningSummary.value = null
    wrongError.value = ''
    reportError.value = ''
    return
  }

  loadWrongQuestions()
  loadAbilityReport()
  loadLearningSummary()
}

async function loadWrongQuestions() {
  if (wrongLoading.value) return

  wrongLoading.value = true
  wrongError.value = ''
  try {
    const response = await fetchWrongQuestions({ limit: 100 })
    wrongItems.value = response?.items || []
  } catch (error) {
    wrongError.value = getSafeError(error, '错题本同步失败，请稍后重试')
  } finally {
    wrongLoading.value = false
  }
}

async function loadAbilityReport() {
  if (reportLoading.value) return

  reportLoading.value = true
  reportError.value = ''
  try {
    abilityReport.value = await fetchAbilityReport({ exam_code: examCode.value })
  } catch (error) {
    reportError.value = getSafeError(error, '能力报告同步失败，请稍后重试')
  } finally {
    reportLoading.value = false
  }
}

async function loadLearningSummary() {
  try {
    learningSummary.value = await fetchLearningSummary({ exam_code: examCode.value })
  } catch (error) {
    learningSummary.value = null
  }
}

function formatWrongQuestion(item) {
  const question = item?.question || {}
  const title = question.stem || `错题 ${item?.question_id || ''}`
  const tags = [
    question.subject,
    question.module,
    question.submodule,
    item?.wrong_count ? `错 ${item.wrong_count} 次` : ''
  ].filter(Boolean)

  return {
    id: item?.question_id || item?.id,
    title,
    subject: question.subject || '',
    module: question.module || '',
    submodule: question.submodule || '',
    wrongCount: item?.wrong_count || 0,
    lastWrongAt: item?.last_wrong_at || '',
    meta: `错 ${item?.wrong_count || 0} 次 · 最近：${formatDateTime(item?.last_wrong_at)}`,
    tags: tags.length ? tags : ['真实错题', '待补充标签']
  }
}

function buildReportView() {
  const items = abilityReport.value?.items || []
  if (!isAuthed.value || items.length === 0) {
    return {
      ...getReportMock(),
      items: []
    }
  }

  const sortedByWeakness = items.slice().sort((a, b) => Number(a.accuracy || 0) - Number(b.accuracy || 0))
  const weakItems = sortedByWeakness.filter((item) => Number(item.accuracy || 0) < 60).slice(0, 5)
  const metrics = items
    .slice()
    .sort((a, b) => b.total_count - a.total_count)
    .slice(0, 5)
    .map((item) => ({
      label: item.submodule || item.module,
      value: Math.round(Number(item.accuracy || 0))
    }))

  const weakNames = weakItems.map((item) => `${item.module}-${item.submodule}`).join('、')
  const diagnosis = weakItems.length
    ? `你在 ${weakNames} 的正确率较低，建议优先做同类题强化。先从 10 题小组练习开始，做完后回看错题解析。`
    : '目前没有明显低于 60% 的薄弱模块，整体状态不错。建议继续混合练习，保持题感并扩大覆盖面。'

  const tasks = (weakItems.length ? weakItems : sortedByWeakness).slice(0, 3).map((item) => ({
    title: `优先训练：${item.subject} - ${item.module}`,
    desc: `${item.submodule} 已做 ${item.total_count} 题，正确率 ${Math.round(Number(item.accuracy || 0))}%。${item.recommendation}`,
    action: '去练习',
    subject: item.subject,
    module: item.module,
    submodule: item.submodule
  }))

  return {
    metrics,
    diagnosis,
    tasks,
    items: sortedByWeakness
  }
}

function getSafeError(error, fallback) {
  return error?.detail || error?.message || fallback
}

function buildFilterOptions(items, field, constraints = {}) {
  const values = items
    .filter((item) => {
      if (constraints.subject && item.subject !== constraints.subject) return false
      if (constraints.module && item.module !== constraints.module) return false
      return true
    })
    .map((item) => item[field])
    .filter(Boolean)
  return ['', ...Array.from(new Set(values))]
}

function setWrongFilter(field, value) {
  wrongFilters.value = {
    ...wrongFilters.value,
    [field]: value
  }
  if (field === 'subject') {
    wrongFilters.value.module = ''
    wrongFilters.value.submodule = ''
  }
  if (field === 'module') {
    wrongFilters.value.submodule = ''
  }
}

async function openWrongDetail(item) {
  if (!isAuthed.value || !item?.id) {
    return
  }

  selectedWrongDetail.value = null
  reviewAnswer.value = ''
  reviewResultText.value = ''
  reviewMastered.value = false
  try {
    selectedWrongDetail.value = await fetchWrongQuestionDetail(item.id)
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '错题详情读取失败'), icon: 'none' })
  }
}

function closeWrongDetail() {
  selectedWrongDetail.value = null
  reviewAnswer.value = ''
  reviewResultText.value = ''
  reviewMastered.value = false
}

const wrongDetailOptions = computed(() => {
  const question = selectedWrongDetail.value?.question
  if (!question) return []
  const options = [
    { key: 'A', text: question.option_a },
    { key: 'B', text: question.option_b },
    { key: 'C', text: question.option_c },
    { key: 'D', text: question.option_d }
  ]
  if (question.option_e) {
    options.push({ key: 'E', text: question.option_e })
  }
  return options
})

function selectReviewAnswer(key) {
  if (reviewingWrong.value) return
  reviewAnswer.value = key
  reviewResultText.value = ''
  reviewMastered.value = false
}

function getWrongOptionClass(key) {
  const correct = selectedWrongDetail.value?.question?.answer
  return {
    selected: reviewAnswer.value === key,
    correct: reviewResultText.value && correct === key,
    wrong: reviewResultText.value && reviewAnswer.value === key && correct !== key
  }
}

async function submitWrongReview() {
  if (!selectedWrongDetail.value || !reviewAnswer.value) {
    return
  }

  reviewingWrong.value = true
  try {
    const result = await reviewWrongQuestion({
      question_id: selectedWrongDetail.value.question_id,
      selected_answer: reviewAnswer.value,
      used_time: 0,
      exam_code: examCode.value
    })
    reviewMastered.value = Boolean(result.is_correct)
    reviewResultText.value = result.is_correct ? '本次重做答对，已掌握。' : `本次仍需复盘，正确答案是 ${result.correct_answer}。`
    await loadLearningSummary()
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '重做提交失败'), icon: 'none' })
  } finally {
    reviewingWrong.value = false
  }
}

function levelClass(level) {
  return {
    stable: level === '稳定',
    normal: level === '一般',
    weak: level === '薄弱',
    critical: level === '重点补强'
  }
}

function formatDateTime(value) {
  if (!value) {
    return '暂无'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value).slice(0, 10)
  }
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}
</script>

<style scoped>
.home-page {
  box-sizing: border-box;
  width: 100%;
  max-width: 100vw;
  min-height: 100vh;
  min-height: 100dvh;
  overflow-x: hidden;
  padding: calc(env(safe-area-inset-top) + 16rpx) 22rpx calc(env(safe-area-inset-bottom) + 152rpx);
}

.home-dashboard {
  box-sizing: border-box;
  width: 100%;
  max-width: 760rpx;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  overflow-x: hidden;
}

.home-dashboard view,
.home-dashboard text,
.home-dashboard button,
.home-dashboard scroll-view {
  box-sizing: border-box;
}

.home-header,
.brand-line,
.welcome-main {
  display: flex;
  align-items: center;
}

.home-header {
  justify-content: space-between;
  gap: 18rpx;
  padding: 0 2rpx;
}

.brand-line {
  min-width: 0;
  flex: 1;
  gap: 18rpx;
}

.brand-title {
  color: #101828;
  font-size: 42rpx;
  line-height: 1.15;
  font-weight: 900;
  letter-spacing: -1rpx;
  white-space: nowrap;
}

.brand-badge {
  padding: 10rpx 20rpx;
  border-radius: 18rpx;
  background: #edf4ff;
  color: #1677ff;
  font-size: 28rpx;
  line-height: 1.2;
  font-weight: 800;
}

.profile-entry {
  width: 78rpx;
  height: 78rpx;
  border-radius: 39rpx;
  background: linear-gradient(180deg, #f2f5fb, #e3e9f4);
  color: #8b95a8;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 32rpx;
  font-weight: 900;
  box-shadow: inset 0 -4rpx 8rpx rgba(20, 31, 66, 0.04);
}

.welcome-card {
  border-radius: 34rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 2rpx solid #e8effc;
  box-shadow: 0 18rpx 48rpx rgba(25, 48, 89, 0.08);
}

.welcome-card {
  padding: 32rpx 26rpx 28rpx;
  overflow: hidden;
  position: relative;
}

.welcome-main {
  position: relative;
  z-index: 1;
  gap: 18rpx;
}

.wave-icon {
  width: 70rpx;
  height: 70rpx;
  border-radius: 22rpx;
  background: #edf4ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 44rpx;
  flex-shrink: 0;
}

.welcome-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.welcome-title {
  color: #101828;
  font-size: 32rpx;
  line-height: 1.28;
  font-weight: 900;
}

.welcome-subtitle {
  color: #8a95a8;
  font-size: 24rpx;
  line-height: 1.5;
  font-weight: 600;
}

.hero-illustration {
  position: absolute;
  right: -12rpx;
  top: -8rpx;
  color: rgba(22, 119, 255, 0.12);
  font-size: 118rpx;
  transform: rotate(-10deg);
  z-index: -1;
}

.stats-card {
  position: relative;
  z-index: 1;
  margin-top: 26rpx;
  padding: 24rpx 8rpx;
  border-radius: 28rpx;
  background: #ffffff;
  display: flex;
  align-items: center;
  box-shadow: 0 16rpx 38rpx rgba(25, 48, 89, 0.08);
}

.stat-item {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  color: #1677ff;
  font-size: 40rpx;
  line-height: 1;
  font-weight: 900;
}

.stat-label {
  margin-top: 12rpx;
  color: #8a95a8;
  font-size: 25rpx;
  font-weight: 600;
}

.stat-divider {
  width: 2rpx;
  height: 70rpx;
  background: #e6edf8;
}

.module-grid {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.state-box {
  margin-bottom: 18rpx;
  padding: 20rpx 22rpx;
  border-radius: 22rpx;
  background: #f4f8ff;
  border: 2rpx dashed #c8d8ff;
  color: #36527f;
  font-size: 24rpx;
  line-height: 1.6;
}

.state-box.warning {
  background: #fff8eb;
  border-color: #fde7b0;
  color: #9a6510;
}

.state-box.mastered {
  background: #effcf4;
  border-color: #b7ebc6;
  color: #17663a;
}

.beta-grid,
.ability-list,
.wrong-detail,
.wrong-options,
.detail-actions,
.daily-list,
.pro-preview {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.beta-item {
  padding: 18rpx 20rpx;
  border-radius: 24rpx;
  background: #f8fbff;
  color: #344054;
  font-size: 24rpx;
  line-height: 1.7;
}

.beta-item.muted {
  background: #f4f8ff;
  color: #667085;
}

.filter-card {
  margin-bottom: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.filter-scroll {
  white-space: nowrap;
}

.filter-chip {
  display: inline-flex;
  margin-right: 12rpx;
  padding: 14rpx 20rpx;
  border: 2rpx solid #dbe4f5;
  border-radius: 999rpx;
  background: #f8fbff;
  color: #476089;
  font-size: 22rpx;
  font-weight: 700;
}

.filter-chip.active {
  border-color: #2563eb;
  background: #edf3ff;
  color: #2563eb;
}

.wrong-stem {
  color: #172033;
  font-size: 30rpx;
  line-height: 1.7;
  font-weight: 800;
}

.wrong-meta,
.answer-line,
.explain-text {
  color: #475467;
  font-size: 24rpx;
  line-height: 1.7;
}

.wrong-option {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  min-height: 76rpx;
  padding: 18rpx;
  border: 2rpx solid #e6ebf5;
  border-radius: 22rpx;
  background: #ffffff;
  color: #172033;
  text-align: left;
  font-size: 24rpx;
}

.wrong-option.selected {
  border-color: #2563eb;
  background: #edf3ff;
}

.wrong-option.correct {
  border-color: rgba(22, 163, 74, 0.45);
  background: rgba(22, 163, 74, 0.1);
}

.wrong-option.wrong {
  border-color: rgba(239, 68, 68, 0.45);
  background: rgba(239, 68, 68, 0.1);
}

.option-key {
  width: 42rpx;
  height: 42rpx;
  border-radius: 14rpx;
  background: #eef3ff;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
}

.task-btn.ghost {
  background: #ffffff;
  color: #475467;
  border: 2rpx solid #dbe4f5;
}

.daily-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
  padding: 22rpx;
  border-radius: 26rpx;
  border: 2rpx solid #e6ebf5;
  background: #fbfcff;
}

.daily-title {
  color: #172033;
  font-size: 26rpx;
  font-weight: 900;
  line-height: 1.5;
}

.daily-desc {
  margin-top: 8rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.6;
}

.pro-preview-item {
  padding: 18rpx 20rpx;
  border-radius: 22rpx;
  background: #f4f8ff;
  color: #36527f;
  font-size: 24rpx;
  line-height: 1.6;
}

.pro-btn,
.feedback-btn {
  margin-top: 18rpx;
}

.pro-entry {
  background: linear-gradient(135deg, #111827, #334155);
}

.ability-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  padding: 18rpx 0;
  border-bottom: 2rpx dashed #edf1f7;
}

.ability-row:last-child {
  border-bottom: 0;
}

.ability-title {
  color: #172033;
  font-size: 25rpx;
  font-weight: 800;
}

.ability-sub {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
}

.ability-pill {
  padding: 12rpx 16rpx;
  border-radius: 999rpx;
  background: #edf3ff;
  color: #2563eb;
  font-size: 22rpx;
  font-weight: 800;
  white-space: nowrap;
}

.ability-pill.stable {
  background: #effcf4;
  color: #17663a;
}

.ability-pill.normal {
  background: #edf3ff;
  color: #2563eb;
}

.ability-pill.weak {
  background: #fff8eb;
  color: #9a6510;
}

.ability-pill.critical {
  background: #fff1f2;
  color: #b42318;
}

.diagnosis-card {
  margin-top: 20rpx;
  padding: 28rpx;
  border-radius: 34rpx;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.08), rgba(128, 90, 213, 0.08));
  border: 2rpx solid rgba(91, 140, 255, 0.28);
}

.diagnosis-title {
  font-size: 30rpx;
  font-weight: 800;
  color: #172033;
}

.diagnosis-text {
  margin-top: 14rpx;
  color: #384a6b;
  font-size: 25rpx;
  line-height: 1.8;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.task-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
  padding: 10rpx 0;
  border-bottom: 2rpx dashed #edf1f7;
}

.task-item:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.task-copy {
  flex: 1;
}

.task-title {
  font-size: 26rpx;
  line-height: 1.6;
  font-weight: 800;
  color: #172033;
}

.task-desc {
  margin-top: 10rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.6;
}

.task-btn {
  padding: 18rpx 22rpx;
  border: 0;
  border-radius: 22rpx;
  background: #edf3ff;
  color: #2563eb;
  font-size: 24rpx;
  font-weight: 800;
}

.unlock-btn {
  margin-top: 22rpx;
  width: 100%;
  min-height: 94rpx;
  border: 0;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #111827, #334155);
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 800;
  box-shadow: 0 16rpx 30rpx rgba(17, 24, 39, 0.22);
}

.profile-dashboard {
  width: 100%;
  max-width: 760rpx;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  overflow-x: hidden;
}

.profile-top-title {
  padding: 2rpx 0 4rpx;
  color: #101828;
  text-align: center;
  font-size: 30rpx;
  line-height: 1.3;
  font-weight: 900;
}

.account-card,
.member-card,
.profile-section-card,
.logout-card {
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid #e8effc;
  border-radius: 30rpx;
  box-shadow: 0 16rpx 42rpx rgba(25, 48, 89, 0.08);
}

.account-card {
  padding: 26rpx 24rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.account-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #4f7dff, #87aaff);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 36rpx;
  font-weight: 900;
  box-shadow: 0 14rpx 26rpx rgba(37, 99, 235, 0.22);
}

.account-main {
  flex: 1;
  min-width: 0;
}

.account-name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.account-name {
  color: #101828;
  font-size: 34rpx;
  line-height: 1.2;
  font-weight: 900;
}

.account-badge {
  padding: 6rpx 12rpx;
  border-radius: 14rpx;
  background: #edf4ff;
  color: #1677ff;
  font-size: 21rpx;
  font-weight: 900;
}

.account-desc {
  margin-top: 10rpx;
  color: #8a95a8;
  font-size: 23rpx;
  line-height: 1.4;
  font-weight: 600;
}

.exam-switch {
  margin-top: 16rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.exam-pill {
  min-width: 100rpx;
  min-height: 54rpx;
  margin: 0;
  padding: 0 18rpx;
  border: 2rpx solid #dbe7ff;
  border-radius: 18rpx;
  background: #ffffff;
  color: #1677ff;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 54rpx;
}

.exam-pill.active {
  color: #ffffff;
  border-color: #1677ff;
  background: #1677ff;
  box-shadow: 0 8rpx 18rpx rgba(22, 119, 255, 0.18);
}

.account-arrow,
.menu-arrow {
  color: #98a2b3;
  font-size: 42rpx;
  font-weight: 800;
}

.member-card {
  position: relative;
  overflow: hidden;
  padding: 30rpx 24rpx 24rpx;
  background:
    radial-gradient(circle at 82% 26%, rgba(22, 119, 255, 0.16), transparent 28%),
    linear-gradient(135deg, #ffffff 0%, #eef5ff 100%);
}

.member-copy {
  position: relative;
  z-index: 1;
  max-width: 430rpx;
}

.member-title {
  color: #101828;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 1.35;
}

.member-subtitle {
  margin-top: 10rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.5;
  font-weight: 600;
}

.member-login-btn {
  margin: 24rpx 0 0;
  width: 210rpx;
  min-height: 72rpx;
  border: 0;
  border-radius: 18rpx;
  background: #1677ff;
  color: #ffffff;
  font-size: 26rpx;
  font-weight: 900;
  line-height: 72rpx;
}

.shield-art {
  position: absolute;
  right: 40rpx;
  top: 28rpx;
  width: 150rpx;
  height: 150rpx;
  border-radius: 42rpx;
  background: linear-gradient(145deg, #72a5ff, #1677ff);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 82rpx;
  font-weight: 900;
  transform: rotate(-8deg);
  box-shadow: 0 18rpx 36rpx rgba(22, 119, 255, 0.28);
  opacity: 0.92;
}

.benefit-row {
  position: relative;
  z-index: 1;
  margin-top: 28rpx;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 10rpx;
}

.benefit-item {
  min-width: 0;
  text-align: center;
}

.benefit-icon {
  width: 54rpx;
  height: 54rpx;
  margin: 0 auto 10rpx;
  border-radius: 18rpx;
  background: #ffffff;
  color: #1677ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 900;
  box-shadow: 0 8rpx 20rpx rgba(25, 48, 89, 0.08);
}

.benefit-label {
  color: #344054;
  font-size: 21rpx;
  line-height: 1.25;
  font-weight: 700;
}

.profile-section-card {
  padding: 28rpx 24rpx 8rpx;
}

.profile-section-title {
  margin-bottom: 8rpx;
  color: #101828;
  font-size: 29rpx;
  font-weight: 900;
}

.menu-list {
  display: flex;
  flex-direction: column;
}

.menu-row {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 22rpx 0;
  border-bottom: 2rpx solid #edf2fb;
}

.menu-row:last-child {
  border-bottom: 0;
}

.menu-icon {
  width: 58rpx;
  height: 58rpx;
  border-radius: 18rpx;
  background: #edf4ff;
  color: #1677ff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 28rpx;
  font-weight: 900;
}

.menu-icon.green {
  background: #eafbf1;
  color: #16a34a;
}

.menu-icon.purple {
  background: #f0edff;
  color: #6d5dfc;
}

.menu-icon.orange {
  background: #fff3e8;
  color: #f97316;
}

.menu-icon.dark {
  background: #eef2f7;
  color: #344054;
}

.menu-copy {
  flex: 1;
  min-width: 0;
}

.menu-title {
  color: #101828;
  font-size: 27rpx;
  line-height: 1.3;
  font-weight: 900;
}

.menu-subtitle {
  margin-top: 8rpx;
  color: #8a95a8;
  font-size: 22rpx;
  line-height: 1.35;
  font-weight: 600;
}

.logout-card {
  min-height: 84rpx;
  color: #ef4444;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 27rpx;
  font-weight: 900;
}
</style>
