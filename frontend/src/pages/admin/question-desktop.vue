<template>
  <view class="portal-shell">
    <aside class="portal-sidebar">
      <view class="sidebar-brand">
        <view class="brand-mark">港</view>
        <view class="brand-copy">
          <view class="brand-name">港研通</view>
          <view class="brand-caption">题库中台</view>
        </view>
      </view>

      <view class="sidebar-section-label">工作台</view>
      <view class="sidebar-nav">
        <button
          v-for="item in navItems"
          :key="item.key"
          class="nav-item"
          :class="{ active: activeSection === item.key }"
          @tap="switchSection(item.key)"
        >
          <text class="nav-glyph">{{ item.icon }}</text>
          <text class="nav-label">{{ item.label }}</text>
          <text v-if="item.key === 'review' && questionStats.pendingReview" class="nav-count">
            {{ compactCount(questionStats.pendingReview) }}
          </text>
        </button>
      </view>

      <view class="sidebar-spacer"></view>
      <view class="sidebar-security">
        <view class="security-icon">✓</view>
        <view class="security-copy">
          <view class="security-title">内部安全访问</view>
          <view class="security-text">权限由数据库白名单控制</view>
        </view>
      </view>
      <button class="logout-button" @tap="logout">
        <text class="nav-glyph">↗</text>
        <text class="nav-label">退出登录</text>
      </button>
    </aside>

    <main class="portal-main">
      <header class="portal-header">
        <view>
          <view class="header-breadcrumb">港研通 / {{ currentNavLabel }}</view>
          <view class="header-title">{{ pageTitle }}</view>
        </view>
        <view class="header-actions">
          <button class="header-refresh" :disabled="refreshing" @tap="refreshCurrentSection">
            <text class="refresh-symbol" :class="{ spinning: refreshing }">↻</text>
            <text>{{ refreshing ? '刷新中' : '刷新数据' }}</text>
          </button>
          <view class="profile-chip">
            <view class="profile-avatar">{{ profileInitial }}</view>
            <view class="profile-copy">
              <view class="profile-name">{{ profileName }}</view>
              <view class="profile-role">题库运营</view>
            </view>
          </view>
        </view>
      </header>

      <view v-if="portalLoading" class="page-state">
        <view class="state-spinner"></view>
        <view class="state-title">正在验证内部权限</view>
        <view class="state-copy">请稍候，系统正在建立安全会话。</view>
      </view>

      <template v-else>
        <section v-if="activeSection === 'dashboard'" class="content-section dashboard-section">
          <view class="welcome-row">
            <view>
              <view class="welcome-kicker">{{ todayLabel }}</view>
              <view class="welcome-title">{{ greeting }}，{{ profileName }}</view>
              <view class="welcome-copy">这里汇总今天的刷题活跃、会员在线情况与高频错题。</view>
            </view>
            <view class="welcome-badge">
              <text class="badge-dot"></text>
              数据口径已校准
            </view>
          </view>

          <view class="dashboard-metrics">
            <view class="metric-card">
              <view class="metric-icon mint">今</view>
              <view class="metric-content">
                <view class="metric-label">今日访问</view>
                <view class="metric-value">{{ formatCount(dashboard.today_practicing_users) }}</view>
                <view class="metric-note">今日成功登录的去重用户</view>
              </view>
              <view class="metric-chip">北京时间</view>
            </view>

            <view class="metric-card">
              <view class="metric-icon blue">会</view>
              <view class="metric-content">
                <view class="metric-label">在线会员</view>
                <view class="metric-value">{{ formatCount(dashboard.online_members) }}</view>
                <view class="metric-note">近 {{ dashboard.online_window_minutes || 15 }} 分钟有刷题行为的有效会员</view>
              </view>
              <view class="live-indicator"><text></text>LIVE</view>
            </view>

            <view class="metric-card">
              <view class="metric-icon slate">题</view>
              <view class="metric-content">
                <view class="metric-label">正式题库</view>
                <view class="metric-value">{{ formatCount(totalQuestionCount) }}</view>
                <view class="metric-note">其中 {{ formatCount(questionStats.pendingReview) }} 道等待审核</view>
              </view>
              <button class="metric-link" @tap="switchSection('questions')">查看题库 →</button>
            </view>
          </view>

          <view class="dashboard-panel">
            <view class="panel-heading">
              <view>
                <view class="panel-title">刷题数据 · 高频错题</view>
                <view class="panel-subtitle">按累计答错次数排序，用于优先发现题目质量或知识盲区问题。</view>
              </view>
              <view class="panel-legend">
                <text class="legend-dot"></text>
                正确率越低越需要关注
              </view>
            </view>

            <view v-if="dashboardLoading" class="inline-loading">正在汇总刷题数据…</view>
            <view v-else-if="dashboard.difficult_questions.length === 0" class="empty-panel">
              <view class="empty-icon">∿</view>
              <view class="empty-title">暂无可汇总的刷题记录</view>
              <view class="empty-copy">产生用户答题记录后，这里会自动显示高频错题。</view>
            </view>
            <view v-else class="data-table difficult-table">
              <view class="table-row table-head">
                <view class="rank-cell">排名</view>
                <view class="stem-cell">题目</view>
                <view class="category-cell">分类</view>
                <view class="number-cell">答错次数</view>
                <view class="number-cell">作答次数</view>
                <view class="accuracy-cell">正确率</view>
              </view>
              <button
                v-for="(item, index) in dashboard.difficult_questions"
                :key="item.question_id"
                class="table-row difficult-row"
                @tap="openQuestionById(item.question_id)"
              >
                <view class="rank-cell">
                  <text class="rank-badge" :class="{ top: index < 3 }">{{ index + 1 }}</text>
                </view>
                <view class="stem-cell">
                  <view class="stem-primary">{{ item.stem }}</view>
                  <view class="stem-id">ID {{ shortId(item.question_id) }}</view>
                </view>
                <view class="category-cell">
                  <text class="category-primary">{{ item.subject || '未分类' }}</text>
                  <text class="category-secondary">{{ item.module || '未分模块' }}</text>
                </view>
                <view class="number-cell wrong-number">{{ item.wrong_count }}</view>
                <view class="number-cell">{{ item.attempt_count }}</view>
                <view class="accuracy-cell">
                  <view class="accuracy-copy">
                    <text>{{ formatAccuracy(item.accuracy) }}</text>
                    <text class="accuracy-tone" :class="accuracyTone(item.accuracy)">
                      {{ accuracyHint(item.accuracy) }}
                    </text>
                  </view>
                  <view class="accuracy-track">
                    <view
                      class="accuracy-fill"
                      :class="accuracyTone(item.accuracy)"
                      :style="{ width: `${clampAccuracy(item.accuracy)}%` }"
                    ></view>
                  </view>
                </view>
              </button>
            </view>
          </view>
        </section>

        <section
          v-if="activeSection === 'questions' || activeSection === 'review'"
          class="content-section question-section"
        >
          <view class="question-summary">
            <button
              v-for="item in summaryCards"
              :key="item.key"
              class="summary-card"
              :class="{ active: summaryCardActive(item.key) }"
              @tap="applySummaryFilter(item.key)"
            >
              <view class="summary-top">
                <view class="summary-icon" :class="item.tone">{{ item.icon }}</view>
                <view class="summary-label">{{ item.label }}</view>
              </view>
              <view class="summary-value">{{ formatCount(item.value) }}</view>
            </button>
          </view>

          <view class="question-workspace">
            <view class="workspace-heading">
              <view>
                <view class="panel-title">{{ activeSection === 'review' ? '审核队列' : '题目列表' }}</view>
                <view class="panel-subtitle">
                  {{ activeSection === 'review'
                    ? '逐题检查内容，确认后发布或退回修改。'
                    : '搜索、筛选、编辑并维护正式题库。' }}
                </view>
              </view>
              <view class="workspace-actions">
                <button class="secondary-button" @tap="openImportWorkspace">批量导入</button>
                <button class="primary-button" @tap="openCreateDrawer">＋ 新增题目</button>
              </view>
            </view>

            <view class="filter-toolbar">
              <view class="search-shell">
                <text class="search-icon">⌕</text>
                <input
                  v-model.trim="filters.search"
                  class="search-input"
                  placeholder="搜索题干或题目 ID"
                  confirm-type="search"
                  @input="handleSearchInput"
                  @confirm="applyFilters"
                />
                <button v-if="filters.search" class="search-clear" @tap="clearSearch">×</button>
              </view>

              <picker :range="subjectLabels" :value="selectedSubjectIndex" @change="handleSubjectChange">
                <view class="filter-select">
                  <text>{{ selectedSubjectLabel }}</text><text class="select-arrow">⌄</text>
                </view>
              </picker>
              <picker :range="moduleLabels" :value="selectedModuleIndex" @change="handleModuleChange">
                <view class="filter-select">
                  <text>{{ selectedModuleLabel }}</text><text class="select-arrow">⌄</text>
                </view>
              </picker>
              <picker :range="difficultyLabels" :value="selectedDifficultyIndex" @change="handleDifficultyChange">
                <view class="filter-select narrow">
                  <text>{{ selectedDifficultyLabel }}</text><text class="select-arrow">⌄</text>
                </view>
              </picker>
              <picker
                v-if="activeSection !== 'review'"
                :range="statusLabels"
                :value="selectedStatusIndex"
                @change="handleStatusChange"
              >
                <view class="filter-select narrow">
                  <text>{{ selectedStatusLabel }}</text><text class="select-arrow">⌄</text>
                </view>
              </picker>
              <button v-if="hasFilters" class="clear-filter-button" @tap="clearFilters">清空</button>
            </view>

            <view v-if="selectedIds.length" class="bulk-toolbar">
              <view class="bulk-copy">已选择 <text>{{ selectedIds.length }}</text> 道题</view>
              <button class="bulk-button" @tap="bulkChangeStatus('active')">批量发布</button>
              <button class="bulk-button danger" @tap="bulkChangeStatus('archived')">批量下架</button>
              <button class="bulk-cancel" @tap="selectedIds = []">取消选择</button>
            </view>

            <view class="question-table-wrap">
              <view class="question-table">
                <view class="question-grid table-head">
                  <view class="check-cell">
                    <button class="check-box" :class="{ checked: allPageSelected }" @tap="toggleSelectPage">
                      {{ allPageSelected ? '✓' : '' }}
                    </button>
                  </view>
                  <view class="id-cell">题目 ID</view>
                  <view class="question-stem-cell">题干</view>
                  <view class="question-category-cell">科目 / 模块</view>
                  <view class="difficulty-cell">难度</view>
                  <view class="status-cell">状态</view>
                  <view class="date-cell">创建时间</view>
                  <view class="action-cell">操作</view>
                </view>

                <view v-if="questionsLoading" class="table-state">正在加载题库…</view>
                <view v-else-if="questionLoadError" class="table-state error">
                  <view>题库加载失败，请检查网络或权限状态。</view>
                  <button @tap="loadQuestions">重新加载</button>
                </view>
                <view v-else-if="questions.length === 0" class="table-state">
                  <view class="empty-icon small">□</view>
                  <view>当前条件下没有题目</view>
                  <button v-if="hasFilters" @tap="clearFilters">清空筛选</button>
                </view>
                <button
                  v-for="item in questions"
                  v-else
                  :key="item.id"
                  class="question-grid question-row"
                  @tap="openEditDrawer(item, activeSection === 'review')"
                >
                  <view class="check-cell">
                    <button
                      class="check-box"
                      :class="{ checked: isSelected(item.id) }"
                      @tap.stop="toggleSelection(item.id)"
                    >
                      {{ isSelected(item.id) ? '✓' : '' }}
                    </button>
                  </view>
                  <view class="id-cell mono">{{ shortId(item.id) }}</view>
                  <view class="question-stem-cell">
                    <view class="table-stem">{{ item.stem || '未填写题干' }}</view>
                    <view class="table-answer">答案 {{ item.answer || '-' }} · {{ item.submodule || '未设置考点' }}</view>
                  </view>
                  <view class="question-category-cell">
                    <text class="table-subject">{{ item.subject || item.exam_code || '未分类' }}</text>
                    <text class="table-module">{{ item.module || '未分模块' }}</text>
                  </view>
                  <view class="difficulty-cell">
                    <view class="difficulty-dots">
                      <text
                        v-for="level in 5"
                        :key="level"
                        :class="{ active: level <= Number(item.difficulty || 0) }"
                      ></text>
                    </view>
                    <text class="difficulty-copy">{{ item.difficulty || '-' }}</text>
                  </view>
                  <view class="status-cell">
                    <text class="status-pill" :class="questionStatusTone(questionDisplayStatus(item))">
                      {{ questionStatusText(questionDisplayStatus(item)) }}
                    </text>
                  </view>
                  <view class="date-cell">{{ formatDate(item.created_at) }}</view>
                  <view class="action-cell">
                    <button class="row-action" @tap.stop="openEditDrawer(item, activeSection === 'review')">
                      {{ activeSection === 'review' ? '审核' : '编辑' }}
                    </button>
                  </view>
                </button>
              </view>
            </view>

            <view class="pagination-row">
              <view class="pagination-info">
                共 {{ formatCount(questionCount) }} 道，每页 {{ pageSize }} 道
              </view>
              <view class="pagination-actions">
                <button :disabled="currentPage <= 1" @tap="changePage(currentPage - 1)">‹</button>
                <view class="page-current">{{ currentPage }}</view>
                <view class="page-total">/ {{ totalPages }}</view>
                <button :disabled="currentPage >= totalPages" @tap="changePage(currentPage + 1)">›</button>
              </view>
            </view>
          </view>
        </section>

        <section v-if="activeSection === 'import'" class="content-section import-section">
          <view class="import-hero-card">
            <view class="import-hero-copy">
              <view class="import-eyebrow">BATCH IMPORT</view>
              <view class="import-title">批量导入工作区</view>
              <view class="import-copy">
                上传图片、JSON、CSV、TXT、XLSX、DOCX 或 PDF，完成识别、预览与 dry-run 后再写入待审核队列。
              </view>
              <button class="primary-button large" @tap="openImportWorkspace">打开批量导入工作区 →</button>
            </view>
            <view class="import-visual">
              <view class="import-file file-one">PDF</view>
              <view class="import-file file-two">XLSX</view>
              <view class="import-file file-three">JSON</view>
              <view class="import-orbit"></view>
              <view class="import-center">⇧</view>
            </view>
          </view>

          <view class="import-flow">
            <view v-for="(item, index) in importSteps" :key="item.title" class="flow-card">
              <view class="flow-index">0{{ index + 1 }}</view>
              <view class="flow-title">{{ item.title }}</view>
              <view class="flow-copy">{{ item.copy }}</view>
            </view>
          </view>

          <view class="import-safety">
            <view class="safety-icon">✓</view>
            <view>
              <view class="safety-title">安全导入规则</view>
              <view class="safety-copy">
                导入内容不会直接发布。只有 dry-run 中无效题为 0、重复题为 0 时才允许写入，写入后仍保持待审核状态。
              </view>
            </view>
          </view>
        </section>
      </template>
    </main>

    <view v-if="drawerVisible" class="drawer-backdrop" @tap="requestCloseDrawer">
      <view class="question-drawer" @tap.stop>
        <view class="drawer-header">
          <view>
            <view class="drawer-kicker">{{ drawerKicker }}</view>
            <view class="drawer-title">{{ drawerTitle }}</view>
          </view>
          <button class="drawer-close" @tap="requestCloseDrawer">×</button>
        </view>

        <view v-if="drawerLoading" class="drawer-state">正在读取题目详情…</view>
        <scroll-view v-else scroll-y class="drawer-scroll">
          <view class="drawer-content">
            <view class="drawer-meta-grid">
              <view class="form-field">
                <view class="form-label">科目</view>
                <picker :range="editorSubjectLabels" :value="editorSubjectIndex" @change="handleEditorSubjectChange">
                  <view class="form-picker">{{ form.subject }}<text>⌄</text></view>
                </picker>
              </view>
              <view class="form-field">
                <view class="form-label">模块</view>
                <picker :range="editorModuleLabels" :value="editorModuleIndex" @change="handleEditorModuleChange">
                  <view class="form-picker">{{ form.module }}<text>⌄</text></view>
                </picker>
              </view>
            </view>

            <view class="drawer-meta-grid">
              <view class="form-field">
                <view class="form-label">考点</view>
                <picker :range="editorSubmoduleLabels" :value="editorSubmoduleIndex" @change="handleEditorSubmoduleChange">
                  <view class="form-picker">{{ form.submodule }}<text>⌄</text></view>
                </picker>
              </view>
              <view class="form-field">
                <view class="form-label">难度</view>
                <view class="difficulty-picker">
                  <button
                    v-for="level in 5"
                    :key="level"
                    :class="{ active: Number(form.difficulty) === level }"
                    @tap="form.difficulty = level"
                  >{{ level }}</button>
                </view>
              </view>
            </view>

            <view class="form-field full">
              <view class="form-heading">
                <view class="form-label">题干</view>
                <text class="required-tag">必填</text>
              </view>
              <textarea v-model.trim="form.stem" class="form-textarea stem" placeholder="请输入完整题干" />
            </view>

            <view class="form-field full">
              <view class="form-heading">
                <view class="form-label">选项与答案</view>
                <text class="form-hint">点击字母设置正确答案</text>
              </view>
              <view class="option-editor">
                <view
                  v-for="option in answerOptions"
                  :key="option"
                  class="option-row"
                  :class="{ correct: form.answer === option }"
                >
                  <button class="answer-selector" @tap="form.answer = option">{{ option }}</button>
                  <input
                    v-model.trim="form[`option_${option.toLowerCase()}`]"
                    class="option-input"
                    :placeholder="`${option} 选项`"
                  />
                </view>
              </view>
            </view>

            <view class="form-field full">
              <view class="form-heading">
                <view class="form-label">解析</view>
                <text class="form-hint">建议包含答案理由与易错点</text>
              </view>
              <textarea v-model.trim="form.explanation" class="form-textarea explanation" placeholder="请输入题目解析" />
            </view>

            <view v-if="drawerMode === 'review'" class="form-field full review-note-field">
              <view class="form-label">审核备注</view>
              <textarea v-model.trim="form.review_note" class="form-textarea note" placeholder="退回修改时请写明问题" />
            </view>

            <view v-if="form.id" class="question-meta-note">
              <text>ID {{ form.id }}</text>
              <text>当前状态：{{ questionStatusText(questionDisplayStatus(form)) }}</text>
            </view>
          </view>
        </scroll-view>

        <view class="drawer-footer">
          <button v-if="drawerMode === 'review'" class="footer-button warning" :disabled="saving" @tap="markNeedsChanges">
            需要修改
          </button>
          <button v-if="drawerMode !== 'create'" class="footer-button secondary" :disabled="saving" @tap="saveQuestionEdits">
            保存修改
          </button>
          <button v-if="drawerMode === 'create'" class="footer-button secondary" :disabled="saving" @tap="createQuestion('pending')">
            存入待审核
          </button>
          <button v-if="drawerMode === 'review'" class="footer-button primary" :disabled="saving" @tap="approveAndPublish">
            通过并发布
          </button>
          <button v-else-if="drawerMode === 'create'" class="footer-button primary" :disabled="saving" @tap="createQuestion('publish')">
            直接发布
          </button>
          <button
            v-else
            class="footer-button"
            :class="questionDisplayStatus(form) === 'active' ? 'danger' : 'primary'"
            :disabled="saving"
            @tap="toggleCurrentQuestionStatus"
          >
            {{ questionDisplayStatus(form) === 'active' ? '下架题目' : '发布题目' }}
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import {
  bulkUpdateAdminQuestionStatus,
  createAdminQuestion,
  fetchAdminQuestionDetail,
  fetchAdminQuestions,
  fetchQuestionAdminDashboard,
  fetchQuestionAdminPortalMe,
  updateAdminQuestion,
  updateAdminQuestionReview,
  updateAdminQuestionStatus
} from '../../api/admin'
import { clearAuthSession, getAuthUser, isLoggedIn, updateAuthUser } from '../../utils/auth'
import { isAiGeneratedQuestion } from '../../utils/questionSource'
import {
  QUESTION_CATALOG,
  QUESTION_MODULES,
  QUESTION_STATUS,
  QUESTION_SUBJECTS
} from './question-admin-catalog'

const portalLoading = ref(true)
const refreshing = ref(false)
const dashboardLoading = ref(false)
const questionsLoading = ref(false)
const questionLoadError = ref(false)
const activeSection = ref('dashboard')
const authUser = ref(getAuthUser() || {})
const dashboard = reactive({
  today_practicing_users: 0,
  online_members: 0,
  online_window_minutes: 15,
  difficult_questions: []
})
const questionStats = reactive({
  active: 0,
  archived: 0,
  pendingReview: 0
})
const questions = ref([])
const questionCount = ref(0)
const currentPage = ref(1)
const pageSize = 20
const selectedIds = ref([])
const drawerVisible = ref(false)
const drawerLoading = ref(false)
const drawerMode = ref('edit')
const saving = ref(false)
const lastSectionBeforeImport = ref('')
const devPreviewMode = ref(false)
let searchTimer = null

const filters = reactive({
  subject: '',
  module: '',
  difficulty: '',
  status: '',
  search: ''
})

const form = reactive({
  id: '',
  exam_code: 'COMMON',
  subject: '英语运用',
  module: '语言知识',
  submodule: '语法',
  stem: '',
  option_a: '',
  option_b: '',
  option_c: '',
  option_d: '',
  answer: 'A',
  explanation: '',
  difficulty: 2,
  status: 'archived',
  review_status: 'pending',
  review_note: ''
})

const navItems = [
  { key: 'dashboard', label: '仪表盘', icon: '⌂' },
  { key: 'questions', label: '题目管理', icon: '≡' },
  { key: 'review', label: '审核队列', icon: '✓' },
  { key: 'import', label: '批量导入', icon: '⇧' }
]

const importSteps = [
  { title: '选择文件', copy: '支持图片与常用结构化、Office、PDF 文件。' },
  { title: '识别解析', copy: '提取题干、选项、答案、解析及分类信息。' },
  { title: '预览修正', copy: '逐题检查识别内容并补全缺失字段。' },
  { title: '校验入库', copy: '通过 dry-run 后写入待审核队列。' }
]

const difficultyOptions = [
  { label: '全部难度', value: '' },
  ...[1, 2, 3, 4, 5].map((value) => ({ label: `难度 ${value}`, value: String(value) }))
]
const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '待审核', value: QUESTION_STATUS.PENDING_REVIEW },
  { label: '已发布', value: QUESTION_STATUS.ACTIVE },
  { label: '已下架', value: QUESTION_STATUS.ARCHIVED }
]
const answerOptions = ['A', 'B', 'C', 'D']
const previewQuestions = [
  {
    id: '6d7b1b2a-8f21-4cf1-91c2-a10294db8301',
    exam_code: 'COMMON',
    subject: '中华文化',
    module: '中国文学常识',
    submodule: '代表作家及作品',
    stem: '下列作品与作者对应正确的是哪一项？',
    option_a: '《文心雕龙》—刘勰',
    option_b: '《世说新语》—司马迁',
    option_c: '《资治通鉴》—班固',
    option_d: '《梦溪笔谈》—郦道元',
    answer: 'A',
    explanation: '《文心雕龙》是南朝文学理论家刘勰创作的文学理论专著。',
    difficulty: 2,
    status: 'active',
    review_status: 'approved',
    created_at: '2026-07-22T08:20:00Z'
  },
  {
    id: '274f0ca7-145b-4ffd-bf04-51458d8ac802',
    exam_code: 'COMMON',
    subject: '英语运用',
    module: '语言知识',
    submodule: '语法',
    stem: 'Had the weather been better, we ____ the outdoor ceremony as planned.',
    option_a: 'would hold',
    option_b: 'would have held',
    option_c: 'held',
    option_d: 'had held',
    answer: 'B',
    explanation: '题干使用省略 if 的虚拟条件句，表示与过去事实相反。',
    difficulty: 3,
    status: 'archived',
    review_status: 'pending',
    created_at: '2026-07-22T07:15:00Z'
  },
  {
    id: '0327ad6f-b5c5-46f7-a297-ce378e199203',
    exam_code: 'Z002',
    subject: '数学基础',
    module: '一元函数微分学',
    submodule: '极值与最值',
    stem: '函数 \\(f(x)=x^3-3x\\) 在区间 \\([-2,2]\\) 上的最大值为（ ）。',
    option_a: '2',
    option_b: '3',
    option_c: '4',
    option_d: '6',
    answer: 'A',
    explanation: '比较驻点与区间端点处的函数值可得最大值。',
    difficulty: 3,
    status: 'active',
    review_status: 'approved',
    created_at: '2026-07-21T11:40:00Z'
  },
  {
    id: '887c5694-74e1-4e92-b1ae-fae9b5023604',
    exam_code: 'Z001',
    subject: '逻辑推理',
    module: '论证',
    submodule: '削弱',
    stem: '某校认为延长图书馆开放时间能显著提高学生平均成绩。下列哪项最能削弱该结论？',
    option_a: '延长开放后，到馆人数明显增加',
    option_b: '多数到馆学生主要使用自习座位',
    option_c: '同期学校调整了课程考核方式',
    option_d: '学生普遍支持延长开放时间',
    answer: 'C',
    explanation: '同期考核方式变化为成绩提高提供了另一种解释。',
    difficulty: 4,
    status: 'archived',
    review_status: 'needs_changes',
    created_at: '2026-07-20T05:18:00Z'
  }
]

const currentNavLabel = computed(() => navItems.find((item) => item.key === activeSection.value)?.label || '题库中台')
const pageTitle = computed(() => {
  const titles = {
    dashboard: '题库仪表盘',
    questions: '题目管理',
    review: '审核队列',
    import: '批量导入'
  }
  return titles[activeSection.value] || '题库中台'
})
const profileName = computed(() => authUser.value?.nickname || authUser.value?.email?.split('@')[0] || '运营同事')
const profileInitial = computed(() => String(profileName.value || '港').slice(0, 1).toUpperCase())
const todayLabel = computed(() => new Intl.DateTimeFormat('zh-CN', {
  month: 'long',
  day: 'numeric',
  weekday: 'long'
}).format(new Date()))
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
})
const totalQuestionCount = computed(() => (
  Number(questionStats.active || 0) +
  Number(questionStats.archived || 0) +
  Number(questionStats.pendingReview || 0)
))
const summaryCards = computed(() => [
  { key: '', label: '全部题目', value: totalQuestionCount.value, icon: '题', tone: 'blue' },
  { key: QUESTION_STATUS.PENDING_REVIEW, label: '待审核', value: questionStats.pendingReview, icon: '审', tone: 'orange' },
  { key: QUESTION_STATUS.ACTIVE, label: '已发布', value: questionStats.active, icon: '发', tone: 'mint' },
  { key: QUESTION_STATUS.ARCHIVED, label: '已下架', value: questionStats.archived, icon: '架', tone: 'slate' }
])
const moduleOptions = computed(() => [
  { label: '全部模块', value: '' },
  ...(QUESTION_MODULES[filters.subject] || []).map((item) => ({ label: item, value: item }))
])
const subjectLabels = computed(() => QUESTION_SUBJECTS.map((item) => item.label))
const moduleLabels = computed(() => moduleOptions.value.map((item) => item.label))
const difficultyLabels = computed(() => difficultyOptions.map((item) => item.label))
const statusLabels = computed(() => statusOptions.map((item) => item.label))
const selectedSubjectIndex = computed(() => optionIndex(QUESTION_SUBJECTS, filters.subject))
const selectedModuleIndex = computed(() => optionIndex(moduleOptions.value, filters.module))
const selectedDifficultyIndex = computed(() => optionIndex(difficultyOptions, filters.difficulty))
const selectedStatusIndex = computed(() => optionIndex(statusOptions, filters.status))
const selectedSubjectLabel = computed(() => QUESTION_SUBJECTS[selectedSubjectIndex.value]?.label || '全部科目')
const selectedModuleLabel = computed(() => moduleOptions.value[selectedModuleIndex.value]?.label || '全部模块')
const selectedDifficultyLabel = computed(() => difficultyOptions[selectedDifficultyIndex.value]?.label || '全部难度')
const selectedStatusLabel = computed(() => statusOptions[selectedStatusIndex.value]?.label || '全部状态')
const hasFilters = computed(() => Boolean(
  filters.subject || filters.module || filters.difficulty || filters.status || filters.search
))
const totalPages = computed(() => Math.max(1, Math.ceil(Number(questionCount.value || 0) / pageSize)))
const selectedSet = computed(() => new Set(selectedIds.value))
const allPageSelected = computed(() => (
  questions.value.length > 0 && questions.value.every((item) => selectedSet.value.has(item.id))
))

const editorSubjects = computed(() => Object.keys(QUESTION_CATALOG))
const editorModules = computed(() => Object.keys(QUESTION_CATALOG[form.subject]?.modules || {}))
const editorSubmodules = computed(() => QUESTION_CATALOG[form.subject]?.modules?.[form.module] || [])
const editorSubjectLabels = computed(() => editorSubjects.value)
const editorModuleLabels = computed(() => editorModules.value)
const editorSubmoduleLabels = computed(() => editorSubmodules.value)
const editorSubjectIndex = computed(() => Math.max(0, editorSubjects.value.indexOf(form.subject)))
const editorModuleIndex = computed(() => Math.max(0, editorModules.value.indexOf(form.module)))
const editorSubmoduleIndex = computed(() => Math.max(0, editorSubmodules.value.indexOf(form.submodule)))
const drawerKicker = computed(() => (
  drawerMode.value === 'create' ? 'NEW QUESTION' : drawerMode.value === 'review' ? 'REVIEW QUEUE' : 'QUESTION DETAIL'
))
const drawerTitle = computed(() => (
  drawerMode.value === 'create' ? '新增题目' : drawerMode.value === 'review' ? '审核题目' : '编辑题目'
))

onLoad(async (options = {}) => {
  if (['dashboard', 'questions', 'review', 'import'].includes(options.section)) {
    activeSection.value = options.section
  }
  if (import.meta.env.DEV && options.preview === '1') {
    devPreviewMode.value = true
    loadDevPreview()
    return
  }
  await bootstrap()
})

onShow(() => {
  if (!portalLoading.value && lastSectionBeforeImport.value) {
    activeSection.value = lastSectionBeforeImport.value
    lastSectionBeforeImport.value = ''
    refreshQuestionData()
  }
})

async function bootstrap() {
  if (!isLoggedIn()) {
    goToPortalLogin()
    return
  }
  portalLoading.value = true
  try {
    const me = await fetchQuestionAdminPortalMe()
    if (me?.profile) {
      authUser.value = updateAuthUser(me.profile) || me.profile
    }
    await Promise.all([loadDashboard(), loadQuestionStats()])
    if (activeSection.value === 'questions' || activeSection.value === 'review') {
      await loadQuestions()
    }
  } catch (error) {
    goToPortalLogin()
  } finally {
    portalLoading.value = false
  }
}

async function loadDashboard() {
  if (devPreviewMode.value) {
    loadDevPreviewDashboard()
    return
  }
  dashboardLoading.value = true
  try {
    const response = await fetchQuestionAdminDashboard()
    dashboard.today_practicing_users = Number(response?.today_practicing_users || 0)
    dashboard.online_members = Number(response?.online_members || 0)
    dashboard.online_window_minutes = Number(response?.online_window_minutes || 15)
    dashboard.difficult_questions = Array.isArray(response?.difficult_questions) ? response.difficult_questions : []
  } catch (error) {
    dashboard.difficult_questions = []
    uni.showToast({ title: '仪表盘数据加载失败', icon: 'none' })
  } finally {
    dashboardLoading.value = false
  }
}

async function loadQuestionStats() {
  if (devPreviewMode.value) {
    questionStats.active = 2846
    questionStats.archived = 126
    questionStats.pendingReview = 38
    return
  }
  const [activeResult, archivedResult, pendingResult] = await Promise.allSettled([
    fetchAdminQuestions({ status: QUESTION_STATUS.ACTIVE, limit: 1, offset: 0 }),
    fetchAdminQuestions({
      status: QUESTION_STATUS.ARCHIVED,
      exclude_review_status: 'pending',
      limit: 1,
      offset: 0
    }),
    fetchAdminQuestions({
      status: QUESTION_STATUS.ARCHIVED,
      review_status: 'pending',
      limit: 1,
      offset: 0
    })
  ])
  questionStats.active = settledCount(activeResult)
  questionStats.archived = settledCount(archivedResult)
  questionStats.pendingReview = settledCount(pendingResult)
}

async function loadQuestions() {
  if (devPreviewMode.value) {
    const status = activeSection.value === 'review' ? QUESTION_STATUS.PENDING_REVIEW : filters.status
    const filtered = previewQuestions.filter((item) => {
      if (filters.subject && item.subject !== filters.subject) return false
      if (filters.module && item.module !== filters.module) return false
      if (filters.difficulty && String(item.difficulty) !== String(filters.difficulty)) return false
      if (filters.search && !`${item.id} ${item.stem}`.toLowerCase().includes(filters.search.toLowerCase())) return false
      if (status && questionDisplayStatus(item) !== status) return false
      return true
    })
    questions.value = filtered
    questionCount.value = status ? filtered.length : 3010
    questionsLoading.value = false
    questionLoadError.value = false
    selectedIds.value = []
    return
  }
  questionsLoading.value = true
  questionLoadError.value = false
  try {
    const response = await fetchAdminQuestions({
      ...buildQuestionParams(),
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize
    })
    questions.value = (response?.items || []).filter((item) => !isAiGeneratedQuestion(item))
    questionCount.value = Number(response?.count || 0)
    selectedIds.value = []
  } catch (error) {
    questions.value = []
    questionCount.value = 0
    questionLoadError.value = true
  } finally {
    questionsLoading.value = false
  }
}

async function switchSection(section) {
  if (activeSection.value === section) return
  activeSection.value = section
  currentPage.value = 1
  selectedIds.value = []
  if (section === 'review') {
    filters.status = QUESTION_STATUS.PENDING_REVIEW
    await loadQuestions()
  } else if (section === 'questions') {
    if (filters.status === QUESTION_STATUS.PENDING_REVIEW) filters.status = ''
    await loadQuestions()
  } else if (section === 'dashboard') {
    await Promise.all([loadDashboard(), loadQuestionStats()])
  }
}

async function refreshCurrentSection() {
  if (refreshing.value) return
  refreshing.value = true
  try {
    if (activeSection.value === 'dashboard') {
      await Promise.all([loadDashboard(), loadQuestionStats()])
    } else if (activeSection.value === 'questions' || activeSection.value === 'review') {
      await refreshQuestionData()
    } else {
      await loadQuestionStats()
    }
  } finally {
    refreshing.value = false
  }
}

async function refreshQuestionData() {
  await Promise.all([loadQuestionStats(), loadQuestions()])
}

function buildQuestionParams() {
  const params = {}
  if (filters.subject) params.subject = filters.subject
  if (filters.module) params.module = filters.module
  if (filters.difficulty) params.difficulty = filters.difficulty
  if (filters.search) params.search = filters.search
  const status = activeSection.value === 'review' ? QUESTION_STATUS.PENDING_REVIEW : filters.status
  if (status === QUESTION_STATUS.PENDING_REVIEW) {
    params.status = QUESTION_STATUS.ARCHIVED
    params.review_status = 'pending'
  } else if (status === QUESTION_STATUS.ARCHIVED) {
    params.status = QUESTION_STATUS.ARCHIVED
    params.exclude_review_status = 'pending'
  } else if (status === QUESTION_STATUS.ACTIVE) {
    params.status = QUESTION_STATUS.ACTIVE
  }
  return params
}

function applyFilters() {
  currentPage.value = 1
  loadQuestions()
}

function clearFilters() {
  filters.subject = ''
  filters.module = ''
  filters.difficulty = ''
  filters.search = ''
  filters.status = activeSection.value === 'review' ? QUESTION_STATUS.PENDING_REVIEW : ''
  applyFilters()
}

function clearSearch() {
  filters.search = ''
  applyFilters()
}

function handleSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(applyFilters, 420)
}

function handleSubjectChange(event) {
  filters.subject = QUESTION_SUBJECTS[Number(event?.detail?.value || 0)]?.value || ''
  filters.module = ''
  applyFilters()
}

function handleModuleChange(event) {
  filters.module = moduleOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  applyFilters()
}

function handleDifficultyChange(event) {
  filters.difficulty = difficultyOptions[Number(event?.detail?.value || 0)]?.value || ''
  applyFilters()
}

function handleStatusChange(event) {
  filters.status = statusOptions[Number(event?.detail?.value || 0)]?.value || ''
  applyFilters()
}

function applySummaryFilter(status) {
  if (status === QUESTION_STATUS.PENDING_REVIEW) {
    activeSection.value = 'review'
    filters.status = status
  } else {
    activeSection.value = 'questions'
    filters.status = status
  }
  currentPage.value = 1
  loadQuestions()
}

function summaryCardActive(status) {
  if (activeSection.value === 'review') return status === QUESTION_STATUS.PENDING_REVIEW
  return activeSection.value === 'questions' && filters.status === status
}

function changePage(page) {
  const next = Math.max(1, Math.min(totalPages.value, Number(page || 1)))
  if (next === currentPage.value) return
  currentPage.value = next
  loadQuestions()
}

function isSelected(id) {
  return selectedSet.value.has(id)
}

function toggleSelection(id) {
  selectedIds.value = isSelected(id)
    ? selectedIds.value.filter((item) => item !== id)
    : [...selectedIds.value, id]
}

function toggleSelectPage() {
  if (allPageSelected.value) {
    const visibleIds = new Set(questions.value.map((item) => item.id))
    selectedIds.value = selectedIds.value.filter((id) => !visibleIds.has(id))
    return
  }
  selectedIds.value = Array.from(new Set([
    ...selectedIds.value,
    ...questions.value.map((item) => item.id)
  ]))
}

async function bulkChangeStatus(status) {
  if (!selectedIds.value.length) return
  const actionText = status === QUESTION_STATUS.ACTIVE ? '发布' : '下架'
  const confirmed = await confirmAction(
    `确认批量${actionText}？`,
    `将对已选择的 ${selectedIds.value.length} 道题执行${actionText}。`,
    actionText
  )
  if (!confirmed) return
  try {
    const response = await bulkUpdateAdminQuestionStatus({
      status,
      ids: selectedIds.value
    })
    uni.showToast({ title: `已${actionText} ${response?.updated_count || 0} 道`, icon: 'success' })
    await refreshQuestionData()
  } catch (error) {
    uni.showToast({ title: `批量${actionText}失败`, icon: 'none' })
  }
}

function openCreateDrawer() {
  resetForm({
    subject: filters.subject || '英语运用',
    module: filters.module || '',
    difficulty: filters.difficulty || 2
  })
  drawerMode.value = 'create'
  drawerVisible.value = true
}

async function openEditDrawer(item, review = false) {
  drawerVisible.value = true
  drawerLoading.value = true
  drawerMode.value = review ? 'review' : 'edit'
  if (devPreviewMode.value) {
    fillForm(previewQuestions.find((question) => question.id === item.id) || item)
    drawerLoading.value = false
    return
  }
  try {
    const response = await fetchAdminQuestionDetail(item.id)
    fillForm(response?.question || item)
  } catch (error) {
    drawerVisible.value = false
    uni.showToast({ title: '题目详情加载失败', icon: 'none' })
  } finally {
    drawerLoading.value = false
  }
}

async function openQuestionById(questionId) {
  await openEditDrawer({ id: questionId }, false)
}

function resetForm(seed = {}) {
  form.id = ''
  form.subject = QUESTION_CATALOG[seed.subject] ? seed.subject : '英语运用'
  form.module = seed.module || ''
  form.submodule = ''
  form.stem = ''
  form.option_a = ''
  form.option_b = ''
  form.option_c = ''
  form.option_d = ''
  form.answer = 'A'
  form.explanation = ''
  form.difficulty = Number(seed.difficulty || 2)
  form.status = 'archived'
  form.review_status = 'pending'
  form.review_note = ''
  syncEditorClassification()
}

function fillForm(question) {
  form.id = String(question?.id || '')
  form.subject = QUESTION_CATALOG[question?.subject] ? question.subject : '英语运用'
  form.module = String(question?.module || '')
  form.submodule = String(question?.submodule || '')
  syncEditorClassification()
  form.stem = String(question?.stem || '')
  form.option_a = String(question?.option_a || '')
  form.option_b = String(question?.option_b || '')
  form.option_c = String(question?.option_c || '')
  form.option_d = String(question?.option_d || '')
  form.answer = answerOptions.includes(question?.answer) ? question.answer : 'A'
  form.explanation = String(question?.explanation || '')
  form.difficulty = Number(question?.difficulty || 2)
  form.status = String(question?.status || 'archived')
  form.review_status = String(question?.review_status || 'pending')
  form.review_note = String(question?.review_note || '')
}

function syncEditorClassification() {
  const catalog = QUESTION_CATALOG[form.subject] || QUESTION_CATALOG['英语运用']
  form.subject = QUESTION_CATALOG[form.subject] ? form.subject : '英语运用'
  form.exam_code = catalog.exam_code
  const modules = Object.keys(catalog.modules)
  if (!modules.includes(form.module)) form.module = modules[0] || ''
  const submodules = catalog.modules[form.module] || []
  if (!submodules.includes(form.submodule)) form.submodule = submodules[0] || ''
}

function handleEditorSubjectChange(event) {
  form.subject = editorSubjects.value[Number(event?.detail?.value || 0)] || '英语运用'
  form.module = ''
  form.submodule = ''
  syncEditorClassification()
}

function handleEditorModuleChange(event) {
  form.module = editorModules.value[Number(event?.detail?.value || 0)] || ''
  form.submodule = ''
  syncEditorClassification()
}

function handleEditorSubmoduleChange(event) {
  form.submodule = editorSubmodules.value[Number(event?.detail?.value || 0)] || ''
  syncEditorClassification()
}

function buildEditablePayload() {
  syncEditorClassification()
  const payload = {
    exam_code: form.exam_code,
    subject: String(form.subject || '').trim(),
    module: String(form.module || '').trim(),
    submodule: String(form.submodule || '').trim(),
    stem: String(form.stem || '').trim(),
    option_a: String(form.option_a || '').trim(),
    option_b: String(form.option_b || '').trim(),
    option_c: String(form.option_c || '').trim(),
    option_d: String(form.option_d || '').trim(),
    answer: form.answer,
    explanation: String(form.explanation || '').trim(),
    difficulty: Number(form.difficulty || 2)
  }
  const required = ['subject', 'module', 'submodule', 'stem', 'option_a', 'option_b', 'option_c', 'option_d', 'answer']
  if (required.some((field) => !String(payload[field] || '').trim())) {
    uni.showToast({ title: '请补全分类、题干、选项和答案', icon: 'none' })
    return null
  }
  return payload
}

async function createQuestion(target) {
  if (saving.value) return
  const editable = buildEditablePayload()
  if (!editable) return
  if (target === 'publish') {
    const confirmed = await confirmAction('确认直接发布？', '新题将跳过待审核队列并立即进入正式题库。', '发布')
    if (!confirmed) return
  }
  saving.value = true
  try {
    await createAdminQuestion({
      ...editable,
      question_type: 'single_choice',
      source_type: 'manual',
      source_year: null,
      status: target === 'publish' ? QUESTION_STATUS.ACTIVE : QUESTION_STATUS.ARCHIVED,
      review_status: target === 'publish' ? 'approved' : 'pending',
      review_note: null
    })
    uni.showToast({ title: target === 'publish' ? '题目已发布' : '已进入待审核', icon: 'success' })
    drawerVisible.value = false
    await refreshQuestionData()
  } catch (error) {
    uni.showToast({ title: '新增题目失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

async function saveQuestionEdits(showSuccess = true) {
  if (saving.value || !form.id) return false
  const payload = buildEditablePayload()
  if (!payload) return false
  saving.value = true
  try {
    const response = await updateAdminQuestion(form.id, payload)
    fillForm(response?.question || { ...form, ...payload })
    if (showSuccess) uni.showToast({ title: '修改已保存', icon: 'success' })
    await loadQuestions()
    return true
  } catch (error) {
    uni.showToast({ title: '保存失败', icon: 'none' })
    return false
  } finally {
    saving.value = false
  }
}

async function approveAndPublish() {
  if (!form.id || saving.value) return
  const saved = await saveQuestionEdits(false)
  if (!saved) return
  saving.value = true
  try {
    await updateAdminQuestionReview(form.id, {
      review_status: 'approved',
      review_note: form.review_note || null,
      publish: true
    })
    uni.showToast({ title: '审核通过并已发布', icon: 'success' })
    drawerVisible.value = false
    await refreshQuestionData()
  } catch (error) {
    uni.showToast({ title: '审核操作失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

async function markNeedsChanges() {
  if (!form.id || saving.value) return
  if (!String(form.review_note || '').trim()) {
    uni.showToast({ title: '请填写需要修改的原因', icon: 'none' })
    return
  }
  saving.value = true
  try {
    await updateAdminQuestionReview(form.id, {
      review_status: 'needs_changes',
      review_note: form.review_note,
      publish: false
    })
    uni.showToast({ title: '已标记为需要修改', icon: 'success' })
    drawerVisible.value = false
    await refreshQuestionData()
  } catch (error) {
    uni.showToast({ title: '审核操作失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

async function toggleCurrentQuestionStatus() {
  if (!form.id || saving.value) return
  const next = questionDisplayStatus(form) === QUESTION_STATUS.ACTIVE
    ? QUESTION_STATUS.ARCHIVED
    : QUESTION_STATUS.ACTIVE
  const label = next === QUESTION_STATUS.ACTIVE ? '发布' : '下架'
  const confirmed = await confirmAction(
    `确认${label}题目？`,
    next === QUESTION_STATUS.ACTIVE
      ? '发布后题目将进入普通刷题抽题范围。'
      : '下架后题目不会进入新练习，但历史记录仍保留。',
    label
  )
  if (!confirmed) return
  saving.value = true
  try {
    const response = await updateAdminQuestionStatus(form.id, { status: next })
    fillForm(response?.question || { ...form, status: next })
    uni.showToast({ title: `题目已${label}`, icon: 'success' })
    await refreshQuestionData()
  } catch (error) {
    uni.showToast({ title: `${label}失败`, icon: 'none' })
  } finally {
    saving.value = false
  }
}

function requestCloseDrawer() {
  if (saving.value) return
  drawerVisible.value = false
}

function openImportWorkspace() {
  lastSectionBeforeImport.value = activeSection.value
  uni.navigateTo({ url: '/pages/admin/question-image-import?portal=1' })
}

function logout() {
  if (devPreviewMode.value) {
    goToPortalLogin()
    return
  }
  uni.showModal({
    title: '退出题库中台？',
    content: '退出后需要重新输入内部账号和密码。',
    confirmText: '退出',
    confirmColor: '#d85a5a',
    success(result) {
      if (!result.confirm) return
      clearAuthSession()
      goToPortalLogin()
    }
  })
}

function goToPortalLogin() {
  uni.reLaunch({ url: '/pages/admin/question-login' })
}

function loadDevPreview() {
  authUser.value = {
    id: 'preview-user',
    email: 'editor@ganguantong.local',
    nickname: '题库老师'
  }
  portalLoading.value = false
  loadDevPreviewDashboard()
  loadQuestionStats()
  if (activeSection.value === 'questions' || activeSection.value === 'review') {
    loadQuestions()
  }
}

function loadDevPreviewDashboard() {
  dashboard.today_practicing_users = 186
  dashboard.online_members = 24
  dashboard.online_window_minutes = 15
  dashboard.difficult_questions = [
    {
      question_id: previewQuestions[3].id,
      stem: previewQuestions[3].stem,
      subject: previewQuestions[3].subject,
      module: previewQuestions[3].module,
      wrong_count: 89,
      attempt_count: 152,
      accuracy: 41.4
    },
    {
      question_id: previewQuestions[2].id,
      stem: previewQuestions[2].stem,
      subject: previewQuestions[2].subject,
      module: previewQuestions[2].module,
      wrong_count: 76,
      attempt_count: 113,
      accuracy: 32.7
    },
    {
      question_id: previewQuestions[1].id,
      stem: previewQuestions[1].stem,
      subject: previewQuestions[1].subject,
      module: previewQuestions[1].module,
      wrong_count: 64,
      attempt_count: 174,
      accuracy: 63.2
    },
    {
      question_id: previewQuestions[0].id,
      stem: previewQuestions[0].stem,
      subject: previewQuestions[0].subject,
      module: previewQuestions[0].module,
      wrong_count: 43,
      attempt_count: 201,
      accuracy: 78.6
    }
  ]
}

function optionIndex(options, value) {
  const index = options.findIndex((item) => item.value === value)
  return index >= 0 ? index : 0
}

function settledCount(result) {
  return result.status === 'fulfilled' ? Number(result.value?.count || 0) : 0
}

function questionDisplayStatus(question) {
  const status = String(question?.status || QUESTION_STATUS.ARCHIVED)
  const reviewStatus = String(question?.review_status || '')
  if (status === QUESTION_STATUS.ARCHIVED && reviewStatus === 'pending') {
    return QUESTION_STATUS.PENDING_REVIEW
  }
  return status
}

function questionStatusText(status) {
  return {
    [QUESTION_STATUS.ACTIVE]: '已发布',
    [QUESTION_STATUS.ARCHIVED]: '已下架',
    [QUESTION_STATUS.PENDING_REVIEW]: '待审核'
  }[status] || '待审核'
}

function questionStatusTone(status) {
  return {
    [QUESTION_STATUS.ACTIVE]: 'published',
    [QUESTION_STATUS.ARCHIVED]: 'archived',
    [QUESTION_STATUS.PENDING_REVIEW]: 'pending'
  }[status] || 'pending'
}

function confirmAction(title, content, confirmText) {
  return new Promise((resolve) => {
    uni.showModal({
      title,
      content,
      confirmText,
      cancelText: '取消',
      success: (result) => resolve(Boolean(result.confirm)),
      fail: () => resolve(false)
    })
  })
}

function formatCount(value) {
  return Number(value || 0).toLocaleString('zh-CN')
}

function compactCount(value) {
  const count = Number(value || 0)
  if (count > 999) return '999+'
  return String(count)
}

function shortId(value) {
  return String(value || '').replace(/-/g, '').slice(0, 8).toUpperCase() || '—'
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('zh-CN', {
    year: '2-digit',
    month: '2-digit',
    day: '2-digit'
  }).format(date)
}

function clampAccuracy(value) {
  return Math.max(0, Math.min(100, Number(value || 0)))
}

function formatAccuracy(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function accuracyTone(value) {
  const accuracy = Number(value || 0)
  if (accuracy < 40) return 'critical'
  if (accuracy < 65) return 'warning'
  return 'healthy'
}

function accuracyHint(value) {
  const tone = accuracyTone(value)
  return tone === 'critical' ? '高关注' : tone === 'warning' ? '需留意' : '正常'
}
</script>

<style scoped>
page {
  background: #eef3f7;
}

button::after {
  border: 0;
}

button {
  font-family: inherit;
}

.portal-shell {
  --sidebar: #21354b;
  --sidebar-deep: #1a2b3f;
  --ink: #182438;
  --muted: #748195;
  --line: #dde6eb;
  --soft-line: #eaf0f3;
  --panel: #ffffff;
  --page: #eef3f7;
  --mint: #50d0b4;
  --mint-dark: #22aa8f;
  min-height: 100vh;
  color: var(--ink);
  background: var(--page);
  font-family: Inter, "PingFang SC", "Microsoft YaHei", sans-serif;
}

.portal-sidebar {
  position: fixed;
  z-index: 20;
  left: 0;
  top: 0;
  bottom: 0;
  width: 238px;
  padding: 28px 18px 20px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  background:
    radial-gradient(circle at 10% 0%, rgba(89, 211, 184, 0.14), transparent 26%),
    linear-gradient(180deg, var(--sidebar), var(--sidebar-deep));
  color: #fff;
}

.sidebar-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 0 10px;
}

.brand-mark {
  width: 43px;
  height: 43px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 13px;
  color: #173a3c;
  background: linear-gradient(145deg, #7ce2cd, #48cdb0);
  box-shadow: 0 12px 24px rgba(44, 192, 160, 0.18);
  font-size: 20px;
  font-weight: 800;
}

.brand-name {
  font-size: 17px;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.brand-caption {
  margin-top: 4px;
  color: rgba(255, 255, 255, 0.48);
  font-size: 11px;
  letter-spacing: 0.13em;
}

.sidebar-section-label {
  margin: 42px 13px 12px;
  color: rgba(255, 255, 255, 0.35);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.18em;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.nav-item,
.logout-button {
  width: 100%;
  min-height: 46px;
  margin: 0;
  padding: 0 13px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.62);
  background: transparent;
  font-size: 13px;
  text-align: left;
  line-height: 1;
  transition: color 0.2s, background 0.2s;
}

.nav-item:hover,
.logout-button:hover {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.06);
}

.nav-item.active {
  color: #143d39;
  background: linear-gradient(135deg, #72dfc7, #4fceb2);
  box-shadow: 0 10px 20px rgba(46, 190, 158, 0.16);
  font-weight: 700;
}

.nav-glyph {
  width: 22px;
  flex: 0 0 auto;
  font-size: 17px;
  text-align: center;
}

.nav-label {
  flex: 1;
}

.nav-count {
  min-width: 19px;
  height: 19px;
  padding: 0 5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  color: #fff;
  background: #ee806c;
  box-sizing: border-box;
  font-size: 9px;
  font-weight: 700;
}

.nav-item.active .nav-count {
  color: #206857;
  background: rgba(255, 255, 255, 0.62);
}

.sidebar-spacer {
  flex: 1;
}

.sidebar-security {
  margin: 0 3px 13px;
  padding: 13px;
  display: flex;
  gap: 10px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 11px;
  background: rgba(255, 255, 255, 0.035);
}

.security-icon {
  width: 23px;
  height: 23px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  color: #74dfc8;
  background: rgba(87, 210, 183, 0.12);
  font-size: 11px;
  font-weight: 700;
}

.security-title {
  color: rgba(255, 255, 255, 0.72);
  font-size: 10px;
  font-weight: 700;
}

.security-text {
  margin-top: 4px;
  color: rgba(255, 255, 255, 0.32);
  font-size: 9px;
  line-height: 1.45;
}

.logout-button {
  color: rgba(255, 255, 255, 0.45);
}

.portal-main {
  min-height: 100vh;
  margin-left: 238px;
}

.portal-header {
  height: 86px;
  padding: 0 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e1e8ec;
  box-sizing: border-box;
  background: rgba(248, 251, 252, 0.92);
}

.header-breadcrumb {
  color: #8995a5;
  font-size: 10px;
}

.header-title {
  margin-top: 5px;
  color: #1d2b3f;
  font-size: 21px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 18px;
}

.header-refresh {
  width: auto;
  height: 36px;
  margin: 0;
  padding: 0 13px;
  display: flex;
  align-items: center;
  gap: 7px;
  border: 1px solid #dce5e9;
  border-radius: 9px;
  color: #607086;
  background: #fff;
  font-size: 11px;
  line-height: 1;
}

.refresh-symbol {
  font-size: 16px;
}

.refresh-symbol.spinning {
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.profile-chip {
  padding-left: 18px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-left: 1px solid #e0e8ec;
}

.profile-avatar {
  width: 35px;
  height: 35px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  color: #1a544b;
  background: #d9f4ed;
  font-size: 13px;
  font-weight: 800;
}

.profile-name {
  max-width: 130px;
  overflow: hidden;
  color: #304056;
  font-size: 11px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-role {
  margin-top: 3px;
  color: #97a1ae;
  font-size: 9px;
}

.content-section {
  padding: 30px 34px 44px;
  box-sizing: border-box;
}

.welcome-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
}

.welcome-kicker {
  color: #8491a1;
  font-size: 11px;
}

.welcome-title {
  margin-top: 7px;
  color: #17253a;
  font-size: 27px;
  line-height: 1.25;
  font-weight: 720;
  letter-spacing: -0.03em;
}

.welcome-copy {
  margin-top: 8px;
  color: #7d8999;
  font-size: 12px;
}

.welcome-badge {
  height: 30px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  gap: 7px;
  border: 1px solid #d9e8e3;
  border-radius: 15px;
  color: #5d786f;
  background: rgba(255, 255, 255, 0.55);
  font-size: 10px;
}

.badge-dot,
.live-indicator text,
.legend-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4ecdb0;
}

.dashboard-metrics {
  margin-top: 25px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
}

.metric-card {
  min-height: 142px;
  padding: 20px;
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 15px;
  border: 1px solid #e1e8ec;
  border-radius: 14px;
  box-sizing: border-box;
  background: #fff;
  box-shadow: 0 9px 26px rgba(31, 50, 71, 0.035);
}

.metric-icon,
.summary-icon {
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 800;
}

.metric-icon.mint,
.summary-icon.mint {
  color: #16836e;
  background: #dcf6ef;
}

.metric-icon.blue,
.summary-icon.blue {
  color: #416b98;
  background: #e5eef8;
}

.metric-icon.slate,
.summary-icon.slate {
  color: #65758b;
  background: #edf1f4;
}

.summary-icon.orange {
  color: #bd7544;
  background: #fff0e1;
}

.metric-content {
  min-width: 0;
  flex: 1;
}

.metric-label {
  color: #748195;
  font-size: 11px;
  font-weight: 600;
}

.metric-value {
  margin-top: 8px;
  color: #17263a;
  font-size: 31px;
  line-height: 1;
  font-weight: 700;
  letter-spacing: -0.035em;
}

.metric-note {
  margin-top: 12px;
  color: #98a2af;
  font-size: 9px;
  line-height: 1.5;
}

.metric-chip,
.live-indicator {
  position: absolute;
  top: 17px;
  right: 17px;
  color: #8190a1;
  font-size: 8px;
}

.metric-chip {
  padding: 5px 7px;
  border-radius: 6px;
  background: #f3f6f7;
}

.live-indicator {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #2aad91;
  font-weight: 800;
  letter-spacing: 0.08em;
}

.live-indicator text {
  animation: pulse 1.8s ease-in-out infinite;
}

@keyframes pulse {
  50% { opacity: 0.35; transform: scale(0.78); }
}

.metric-link {
  width: auto;
  margin: 0;
  padding: 5px;
  position: absolute;
  right: 14px;
  bottom: 13px;
  color: #2aad91;
  background: transparent;
  font-size: 9px;
  line-height: 1;
}

.dashboard-panel,
.question-workspace {
  margin-top: 19px;
  border: 1px solid #e0e8ec;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 9px 26px rgba(31, 50, 71, 0.03);
}

.panel-heading,
.workspace-heading {
  min-height: 78px;
  padding: 0 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e8eef1;
  box-sizing: border-box;
}

.panel-title {
  color: #26354a;
  font-size: 14px;
  font-weight: 750;
}

.panel-subtitle {
  margin-top: 5px;
  color: #8b96a5;
  font-size: 9px;
}

.panel-legend {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #8c97a5;
  font-size: 9px;
}

.legend-dot {
  background: #ea9c78;
}

.data-table {
  min-width: 760px;
}

.table-row {
  width: 100%;
  margin: 0;
  padding: 0 20px;
  display: grid;
  align-items: center;
  box-sizing: border-box;
  text-align: left;
}

.difficult-table .table-row {
  grid-template-columns: 60px minmax(260px, 2.2fr) minmax(140px, 1fr) 95px 95px minmax(150px, 1fr);
}

.table-head {
  min-height: 41px;
  color: #8a96a5;
  background: #f8fafb;
  font-size: 9px;
  font-weight: 700;
}

.difficult-row {
  min-height: 73px;
  border-top: 1px solid #edf1f3;
  border-radius: 0;
  color: #46556a;
  background: #fff;
  font-size: 10px;
  line-height: 1.3;
}

.difficult-row:hover,
.question-row:hover {
  background: #f7fbfa;
}

.rank-badge {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #7a8797;
  background: #f0f3f5;
  font-size: 9px;
  font-weight: 800;
}

.rank-badge.top {
  color: #16846f;
  background: #ddf5ef;
}

.stem-cell,
.category-cell,
.question-stem-cell,
.question-category-cell {
  min-width: 0;
}

.stem-primary,
.table-stem {
  overflow: hidden;
  color: #26364a;
  font-size: 10px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stem-id,
.table-answer {
  margin-top: 6px;
  color: #9aa4b0;
  font-size: 8px;
}

.category-cell,
.question-category-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-primary,
.table-subject {
  color: #4a596d;
  font-size: 9px;
  font-weight: 700;
}

.category-secondary,
.table-module {
  color: #939eab;
  font-size: 8px;
}

.number-cell {
  color: #536277;
  font-size: 11px;
  font-weight: 650;
}

.wrong-number {
  color: #d66f61;
}

.accuracy-copy {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #45546a;
  font-size: 10px;
  font-weight: 700;
}

.accuracy-tone {
  font-size: 8px;
  font-weight: 600;
}

.accuracy-tone.critical { color: #d45f57; }
.accuracy-tone.warning { color: #cf8c4a; }
.accuracy-tone.healthy { color: #2baa8d; }

.accuracy-track {
  height: 4px;
  margin-top: 7px;
  overflow: hidden;
  border-radius: 3px;
  background: #edf1f3;
}

.accuracy-fill {
  height: 100%;
  border-radius: 3px;
}

.accuracy-fill.critical { background: #e77f74; }
.accuracy-fill.warning { background: #e4ad68; }
.accuracy-fill.healthy { background: #50cdb1; }

.inline-loading,
.empty-panel,
.table-state,
.drawer-state {
  min-height: 230px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8a96a5;
  font-size: 11px;
}

.empty-icon {
  width: 46px;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 15px;
  color: #4ebda5;
  background: #e4f6f1;
  font-size: 22px;
  font-weight: 700;
}

.empty-icon.small {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  font-size: 15px;
}

.empty-title {
  margin-top: 14px;
  color: #4b5b70;
  font-size: 12px;
  font-weight: 700;
}

.empty-copy {
  margin-top: 6px;
  color: #9aa4b0;
  font-size: 9px;
}

.question-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 13px;
}

.summary-card {
  min-height: 100px;
  margin: 0;
  padding: 15px 17px;
  border: 1px solid #e0e8ec;
  border-radius: 13px;
  box-sizing: border-box;
  color: inherit;
  background: #fff;
  text-align: left;
  box-shadow: 0 7px 22px rgba(31, 50, 71, 0.025);
}

.summary-card.active {
  border-color: #72d7c0;
  box-shadow: 0 0 0 3px rgba(79, 205, 176, 0.08);
}

.summary-top {
  display: flex;
  align-items: center;
  gap: 10px;
}

.summary-icon {
  width: 31px;
  height: 31px;
  border-radius: 9px;
  font-size: 10px;
}

.summary-label {
  color: #738095;
  font-size: 10px;
  font-weight: 650;
}

.summary-value {
  margin: 10px 0 0 41px;
  color: #1d2b3f;
  font-size: 22px;
  line-height: 1;
  font-weight: 720;
}

.workspace-actions {
  display: flex;
  gap: 9px;
}

.primary-button,
.secondary-button {
  width: auto;
  height: 35px;
  margin: 0;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
}

.primary-button {
  color: #153f3a;
  background: linear-gradient(135deg, #69ddc4, #4ccaae);
}

.secondary-button {
  border: 1px solid #d9e3e8;
  color: #617086;
  background: #fff;
}

.primary-button.large {
  height: 43px;
  margin-top: 25px;
  padding: 0 19px;
  border-radius: 10px;
  font-size: 11px;
}

.filter-toolbar {
  min-height: 64px;
  padding: 11px 17px;
  display: flex;
  align-items: center;
  gap: 9px;
  border-bottom: 1px solid #e8eef1;
  box-sizing: border-box;
  background: #fbfcfd;
}

.search-shell {
  width: 270px;
  height: 37px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  border: 1px solid #dbe4e8;
  border-radius: 8px;
  box-sizing: border-box;
  background: #fff;
}

.search-shell:focus-within {
  border-color: #67cdb7;
  box-shadow: 0 0 0 3px rgba(79, 205, 176, 0.08);
}

.search-icon {
  width: 23px;
  color: #92a0ae;
  font-size: 16px;
}

.search-input {
  min-width: 0;
  height: 35px;
  flex: 1;
  color: #34445a;
  font-size: 10px;
}

.search-clear {
  width: 22px;
  height: 22px;
  margin: 0;
  padding: 0;
  border-radius: 7px;
  color: #8e99a7;
  background: #f1f4f5;
  font-size: 15px;
  line-height: 22px;
}

.filter-select {
  width: 132px;
  height: 37px;
  padding: 0 11px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #dbe4e8;
  border-radius: 8px;
  box-sizing: border-box;
  color: #657389;
  background: #fff;
  font-size: 9px;
}

.filter-select.narrow {
  width: 104px;
}

.select-arrow {
  color: #9aa5b1;
  font-size: 11px;
}

.clear-filter-button {
  width: auto;
  height: 32px;
  margin: 0;
  padding: 0 8px;
  color: #7a8797;
  background: transparent;
  font-size: 9px;
  line-height: 1;
}

.bulk-toolbar {
  min-height: 45px;
  padding: 7px 17px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #cdece4;
  box-sizing: border-box;
  background: #f0faf7;
}

.bulk-copy {
  margin-right: auto;
  color: #5d716c;
  font-size: 9px;
}

.bulk-copy text {
  color: #16846f;
  font-weight: 800;
}

.bulk-button,
.bulk-cancel {
  width: auto;
  height: 29px;
  margin: 0;
  padding: 0 10px;
  border-radius: 7px;
  color: #267b69;
  background: #d8f3ec;
  font-size: 9px;
  line-height: 1;
}

.bulk-button.danger {
  color: #ae5c56;
  background: #fae5e3;
}

.bulk-cancel {
  color: #7d8998;
  background: transparent;
}

.question-table-wrap {
  overflow-x: auto;
}

.question-table {
  min-width: 950px;
}

.question-grid {
  width: 100%;
  padding: 0 15px;
  display: grid;
  grid-template-columns: 42px 88px minmax(270px, 2.3fr) minmax(145px, 1fr) 78px 90px 82px 62px;
  align-items: center;
  box-sizing: border-box;
}

.question-row {
  min-height: 69px;
  margin: 0;
  border-top: 1px solid #edf1f3;
  border-radius: 0;
  color: #536176;
  background: #fff;
  text-align: left;
}

.check-box {
  width: 17px;
  height: 17px;
  margin: 0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #cbd6dc;
  border-radius: 5px;
  color: #fff;
  background: #fff;
  font-size: 9px;
  line-height: 1;
}

.check-box.checked {
  border-color: #45bea3;
  background: #4fcdb1;
}

.mono {
  color: #718094;
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 8px;
  letter-spacing: 0.03em;
}

.difficulty-cell {
  display: flex;
  align-items: center;
  gap: 7px;
}

.difficulty-dots {
  display: flex;
  gap: 2px;
}

.difficulty-dots text {
  width: 4px;
  height: 11px;
  border-radius: 2px;
  background: #e4e9ec;
}

.difficulty-dots text.active {
  background: #54cdb2;
}

.difficulty-copy {
  color: #7b8796;
  font-size: 8px;
}

.status-pill {
  padding: 5px 8px;
  display: inline-flex;
  border-radius: 10px;
  font-size: 8px;
  font-weight: 700;
}

.status-pill.published {
  color: #16816c;
  background: #dcf5ee;
}

.status-pill.pending {
  color: #b06e3f;
  background: #fff0e1;
}

.status-pill.archived {
  color: #69778a;
  background: #edf1f4;
}

.date-cell {
  color: #8793a2;
  font-size: 8px;
}

.row-action {
  width: auto;
  height: 27px;
  margin: 0;
  padding: 0 9px;
  border: 1px solid #d7e4e1;
  border-radius: 7px;
  color: #2a8a76;
  background: #f5fbf9;
  font-size: 8px;
  line-height: 1;
}

.table-state.error {
  color: #b2605b;
}

.table-state button {
  width: auto;
  height: 30px;
  margin: 12px 0 0;
  padding: 0 11px;
  border-radius: 7px;
  color: #267c6a;
  background: #dff5ef;
  font-size: 9px;
  line-height: 1;
}

.pagination-row {
  min-height: 58px;
  padding: 0 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid #e8eef1;
  box-sizing: border-box;
}

.pagination-info,
.page-total {
  color: #929daa;
  font-size: 9px;
}

.pagination-actions {
  display: flex;
  align-items: center;
  gap: 7px;
}

.pagination-actions button {
  width: 29px;
  height: 29px;
  margin: 0;
  padding: 0;
  border: 1px solid #dce5e9;
  border-radius: 7px;
  color: #536277;
  background: #fff;
  font-size: 16px;
  line-height: 27px;
}

.pagination-actions button[disabled] {
  color: #c1c8cf;
  background: #f5f7f8;
}

.page-current {
  width: 29px;
  height: 29px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  color: #185a50;
  background: #dff5ef;
  font-size: 9px;
  font-weight: 800;
}

.import-hero-card {
  min-height: 305px;
  padding: 47px 56px;
  position: relative;
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  align-items: center;
  overflow: hidden;
  border-radius: 18px;
  background:
    radial-gradient(circle at 85% 18%, rgba(100, 224, 198, 0.22), transparent 26%),
    linear-gradient(145deg, #21384f, #2e4a63);
  color: #fff;
  box-sizing: border-box;
}

.import-eyebrow {
  color: #6ddcc4;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.import-title {
  margin-top: 13px;
  font-size: 29px;
  font-weight: 700;
  letter-spacing: -0.03em;
}

.import-copy {
  max-width: 590px;
  margin-top: 13px;
  color: rgba(255, 255, 255, 0.58);
  font-size: 11px;
  line-height: 1.75;
}

.import-visual {
  width: 220px;
  height: 220px;
  margin-left: auto;
  position: relative;
}

.import-orbit {
  position: absolute;
  inset: 15px;
  border: 1px dashed rgba(105, 222, 197, 0.28);
  border-radius: 50%;
}

.import-center {
  width: 72px;
  height: 72px;
  position: absolute;
  left: 74px;
  top: 74px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 23px;
  color: #194a43;
  background: linear-gradient(145deg, #80e4cf, #4dcdb0);
  box-shadow: 0 18px 42px rgba(43, 196, 163, 0.24);
  font-size: 28px;
}

.import-file {
  position: absolute;
  padding: 8px 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.66);
  background: rgba(255, 255, 255, 0.07);
  font-size: 8px;
  font-weight: 700;
}

.file-one { left: 5px; top: 50px; transform: rotate(-9deg); }
.file-two { right: 0; top: 40px; transform: rotate(8deg); }
.file-three { right: 18px; bottom: 35px; transform: rotate(-5deg); }

.import-flow {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.flow-card {
  min-height: 132px;
  padding: 18px;
  border: 1px solid #e0e8ec;
  border-radius: 13px;
  box-sizing: border-box;
  background: #fff;
}

.flow-index {
  color: #49bfa5;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.flow-title {
  margin-top: 14px;
  color: #334359;
  font-size: 12px;
  font-weight: 750;
}

.flow-copy {
  margin-top: 8px;
  color: #8c97a5;
  font-size: 9px;
  line-height: 1.65;
}

.import-safety {
  margin-top: 15px;
  padding: 16px 18px;
  display: flex;
  gap: 12px;
  border: 1px solid #cfe8e1;
  border-radius: 12px;
  background: #f3faf8;
}

.safety-icon {
  width: 25px;
  height: 25px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #16816c;
  background: #d9f3ec;
  font-size: 11px;
  font-weight: 800;
}

.safety-title {
  color: #3b645b;
  font-size: 10px;
  font-weight: 750;
}

.safety-copy {
  margin-top: 5px;
  color: #759087;
  font-size: 9px;
  line-height: 1.55;
}

.drawer-backdrop {
  position: fixed;
  z-index: 100;
  inset: 0;
  display: flex;
  justify-content: flex-end;
  background: rgba(18, 31, 45, 0.42);
  backdrop-filter: blur(2px);
}

.question-drawer {
  width: min(630px, calc(100vw - 90px));
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8fafb;
  box-shadow: -20px 0 50px rgba(22, 37, 53, 0.15);
}

.drawer-header {
  height: 81px;
  padding: 0 25px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e0e8ec;
  box-sizing: border-box;
  background: #fff;
}

.drawer-kicker {
  color: #43b79e;
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.drawer-title {
  margin-top: 5px;
  color: #26364a;
  font-size: 18px;
  font-weight: 750;
}

.drawer-close {
  width: 32px;
  height: 32px;
  margin: 0;
  padding: 0;
  border-radius: 9px;
  color: #768397;
  background: #f0f3f5;
  font-size: 20px;
  line-height: 30px;
}

.drawer-scroll {
  min-height: 0;
  flex: 1;
}

.drawer-content {
  padding: 22px 25px 34px;
}

.drawer-meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 13px;
}

.drawer-meta-grid + .drawer-meta-grid,
.form-field.full {
  margin-top: 18px;
}

.form-label {
  color: #556479;
  font-size: 10px;
  font-weight: 700;
}

.form-picker {
  height: 38px;
  margin-top: 8px;
  padding: 0 11px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border: 1px solid #dbe4e8;
  border-radius: 8px;
  box-sizing: border-box;
  color: #536277;
  background: #fff;
  font-size: 10px;
}

.form-picker text {
  color: #9aa4b0;
}

.difficulty-picker {
  height: 38px;
  margin-top: 8px;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  overflow: hidden;
  border: 1px solid #dbe4e8;
  border-radius: 8px;
  background: #fff;
}

.difficulty-picker button {
  height: 36px;
  margin: 0;
  padding: 0;
  border-radius: 0;
  color: #7b8796;
  background: #fff;
  font-size: 9px;
  line-height: 36px;
}

.difficulty-picker button + button {
  border-left: 1px solid #e7ecef;
}

.difficulty-picker button.active {
  color: #176b5d;
  background: #dff5ef;
  font-weight: 800;
}

.form-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.required-tag,
.form-hint {
  color: #9aa4b0;
  font-size: 8px;
}

.required-tag {
  padding: 3px 6px;
  border-radius: 5px;
  color: #b26358;
  background: #fbe9e6;
}

.form-textarea {
  width: 100%;
  margin-top: 8px;
  padding: 12px;
  border: 1px solid #dbe4e8;
  border-radius: 9px;
  box-sizing: border-box;
  color: #334359;
  background: #fff;
  font-size: 10px;
  line-height: 1.65;
}

.form-textarea:focus {
  border-color: #62cbb4;
}

.form-textarea.stem { min-height: 105px; }
.form-textarea.explanation { min-height: 120px; }
.form-textarea.note { min-height: 76px; }

.option-editor {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-row {
  min-height: 43px;
  padding: 5px 9px 5px 5px;
  display: flex;
  align-items: center;
  gap: 9px;
  border: 1px solid #dfe6ea;
  border-radius: 9px;
  box-sizing: border-box;
  background: #fff;
}

.option-row.correct {
  border-color: #6dd3bd;
  background: #f2fbf8;
}

.answer-selector {
  width: 32px;
  height: 32px;
  margin: 0;
  padding: 0;
  border-radius: 7px;
  color: #69778a;
  background: #edf1f3;
  font-size: 10px;
  font-weight: 800;
  line-height: 32px;
}

.option-row.correct .answer-selector {
  color: #176b5d;
  background: #d6f2eb;
}

.option-input {
  min-width: 0;
  height: 32px;
  flex: 1;
  color: #3f4f64;
  font-size: 10px;
}

.review-note-field {
  padding: 15px;
  border: 1px solid #f0ddc8;
  border-radius: 10px;
  background: #fffaf4;
}

.question-meta-note {
  margin-top: 20px;
  padding: 12px 0;
  display: flex;
  justify-content: space-between;
  border-top: 1px dashed #dce4e8;
  color: #9aa4b0;
  font-family: Consolas, monospace;
  font-size: 8px;
}

.drawer-footer {
  min-height: 67px;
  padding: 11px 18px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 9px;
  border-top: 1px solid #dfe7eb;
  box-sizing: border-box;
  background: #fff;
}

.footer-button {
  width: auto;
  height: 37px;
  margin: 0;
  padding: 0 15px;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
}

.footer-button.primary {
  color: #17423c;
  background: #59d2b7;
}

.footer-button.secondary {
  border: 1px solid #d8e2e7;
  color: #617087;
  background: #fff;
}

.footer-button.warning {
  color: #a86639;
  background: #fff0df;
}

.footer-button.danger {
  color: #a95650;
  background: #fae4e2;
}

.page-state {
  min-height: calc(100vh - 86px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #7e8b9c;
}

.state-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #d8e4e5;
  border-top-color: #4fcbb0;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

.state-title {
  margin-top: 16px;
  color: #45566b;
  font-size: 13px;
  font-weight: 700;
}

.state-copy {
  margin-top: 6px;
  color: #929daa;
  font-size: 9px;
}

@media (max-width: 1180px) {
  .portal-sidebar {
    width: 82px;
    padding-left: 12px;
    padding-right: 12px;
  }

  .portal-main {
    margin-left: 82px;
  }

  .brand-copy,
  .sidebar-section-label,
  .nav-label,
  .sidebar-security,
  .profile-copy {
    display: none;
  }

  .sidebar-brand,
  .nav-item,
  .logout-button {
    justify-content: center;
  }

  .nav-item,
  .logout-button {
    padding: 0;
  }

  .nav-glyph {
    width: auto;
  }

  .nav-count {
    position: absolute;
    margin: -27px 0 0 26px;
  }

  .dashboard-metrics {
    grid-template-columns: 1fr 1fr;
  }

  .metric-card:last-child {
    grid-column: 1 / -1;
  }

  .filter-toolbar {
    flex-wrap: wrap;
  }
}

@media (max-width: 820px) {
  .portal-sidebar {
    display: none;
  }

  .portal-main {
    margin-left: 0;
  }

  .portal-header,
  .content-section {
    padding-left: 18px;
    padding-right: 18px;
  }

  .dashboard-metrics,
  .question-summary,
  .import-flow {
    grid-template-columns: 1fr 1fr;
  }

  .import-hero-card {
    grid-template-columns: 1fr;
  }

  .import-visual {
    display: none;
  }
}
</style>
