<template>
  <view class="mock-admin-shell">
    <template v-if="!editor">
      <view class="mock-admin-toolbar">
        <view class="mock-status-tabs">
          <button
            v-for="item in paperStatusOptions"
            :key="item.value"
            :class="{ active: paperStatus === item.value }"
            @tap="changePaperStatus(item.value)"
          >{{ item.label }}</button>
        </view>
        <button class="mock-primary-button" :disabled="creating" @tap="createPaper">
          {{ creating ? '创建中…' : '＋ 新建模拟卷' }}
        </button>
      </view>

      <view v-if="listLoading" class="mock-admin-state">正在加载模拟卷…</view>
      <view v-else-if="listError" class="mock-admin-state error">
        <text>{{ listError }}</text>
        <button @tap="loadPapers">重新加载</button>
      </view>
      <view v-else-if="!papers.length" class="mock-admin-state">
        当前状态下还没有模拟卷
      </view>
      <view v-else class="mock-paper-admin-grid">
        <button
          v-for="paper in papers"
          :key="paper.id"
          class="mock-paper-admin-card"
          @tap="openPaper(paper.id)"
        >
          <view class="mock-paper-admin-head">
            <view class="mock-paper-admin-icon">卷</view>
            <text class="mock-paper-status" :class="paper.status">{{ paperStatusText(paper.status) }}</text>
          </view>
          <view class="mock-paper-admin-name">{{ paper.title }}</view>
          <view class="mock-paper-admin-meta">{{ paper.exam_code }} · {{ paper.question_count }}/55 题 · {{ paper.total_score }}/105 分</view>
          <view class="mock-paper-admin-footer">
            <text>V{{ paper.version || 1 }} · {{ formatDateTime(paper.updated_at) }}</text>
            <text class="mock-paper-enter">进入组卷 →</text>
          </view>
        </button>
      </view>
    </template>

    <template v-else>
      <view class="mock-editor-toolbar">
        <view class="mock-validation-strip" :class="{ ready: localPublishReady }">
          <view class="mock-validation-heading">
            <strong>{{ localPublishReady ? '卷面规格已满足，可发布' : '卷面规格校验中' }}</strong>
            <text>发布前后端还会再次强校验</text>
          </view>
          <view class="mock-validation-metrics">
            <view v-for="item in sectionProgress" :key="item.key" :class="{ complete: item.selected === item.required }">
              <text>{{ item.label }}</text>
              <strong>{{ item.selected }}/{{ item.required }}</strong>
            </view>
            <view v-for="item in difficultyProgress" :key="item.key" :class="{ complete: item.selected === item.required }">
              <text>{{ item.label }}</text>
              <strong>{{ item.selected }}/{{ item.required }}</strong>
            </view>
          </view>
        </view>
        <view class="mock-editor-actions">
          <button class="mock-secondary-button" :disabled="busy" @tap="saveDraft">{{ saving ? '保存中…' : '保存草稿' }}</button>
          <button
            v-if="editor.paper.status === 'published'"
            class="mock-archive-button"
            :disabled="busy"
            @tap="archivePaper"
          >{{ archiving ? '下架中…' : '下架' }}</button>
          <button class="mock-primary-button" :disabled="busy" @tap="publishPaper">{{ publishing ? '发布中…' : editor.paper.status === 'published' ? '重新发布' : '发布试卷' }}</button>
        </view>
      </view>

      <view class="mock-paper-settings">
        <view class="mock-setting-field">
          <text>考试类型</text>
          <view class="mock-exam-code-tabs">
            <button
              v-for="code in ['Z001', 'Z002']"
              :key="code"
              :class="{ active: editor.paper.exam_code === code }"
              :disabled="busy"
              @tap="changeExamCode(code)"
            >{{ code }}</button>
          </view>
        </view>
        <view class="mock-setting-field mock-title-field">
          <text>试卷名称</text>
          <input v-model.trim="editor.paper.title" class="mock-title-input" maxlength="80" placeholder="请输入模拟卷名称" />
        </view>
        <view class="mock-setting-field mock-duration-field">
          <text>建议时长</text>
          <input v-model.number="editor.paper.duration_minutes" type="number" min="30" max="360" />
          <small>分钟</small>
        </view>
      </view>

      <view class="mock-builder-grid">
        <aside class="mock-section-panel">
          <view class="mock-panel-heading">卷面分区</view>
          <button
            v-for="section in sectionProgress"
            :key="section.key"
            class="mock-section-button"
            :class="{ active: activeSection === section.key, complete: section.selected === section.required }"
            @tap="selectSection(section.key)"
          >
            <view><strong>{{ section.label }}</strong><text>{{ section.pointValue }} 分/题</text></view>
            <text class="mock-section-count">{{ section.selected }}/{{ section.required }}</text>
            <view class="mock-section-progress">
              <view class="mock-section-progress-value" :style="{ width: `${Math.min(100, section.selected / section.required * 100)}%` }"></view>
            </view>
          </button>
          <view class="mock-spec-note">
            <strong>固定规格</strong>
            <text>总计 55 题、105 分</text>
            <text>公共科目排除阅读理解</text>
            <text>题目可来自已发布或未发布题库</text>
          </view>
        </aside>

        <section class="mock-question-picker">
          <view class="mock-panel-heading-row">
            <view>
              <view class="mock-panel-heading">选择{{ activeSectionRule.label }}题目</view>
              <view class="mock-panel-subtitle">当前分区还可加入 {{ activeSectionRemaining }} 题</view>
            </view>
            <button class="mock-refresh-options" :disabled="optionsLoading" @tap="loadQuestionOptions">刷新</button>
          </view>

          <view class="mock-question-filters">
            <view class="mock-question-search">
              <text>⌕</text>
              <input v-model.trim="optionFilters.search" placeholder="搜索题干" @input="scheduleQuestionSearch" @confirm="applyQuestionFilters" />
              <button v-if="optionFilters.search" @tap="clearQuestionSearch">×</button>
            </view>
            <view class="mock-filter-row">
              <view class="mock-filter-pill-groups">
                <view class="mock-filter-pills">
                  <button
                    v-for="item in publicationOptions"
                    :key="item.value"
                    :class="{ active: optionFilters.publication === item.value }"
                    @tap="setPublicationFilter(item.value)"
                  >{{ item.label }}</button>
                </view>
                <view class="mock-filter-pills difficulty">
                  <button :class="{ active: !optionFilters.difficulty }" @tap="setDifficultyFilter('')">全部难度</button>
                  <button v-for="level in 5" :key="level" :class="{ active: Number(optionFilters.difficulty) === level }" @tap="setDifficultyFilter(level)">{{ level }}</button>
                </view>
              </view>
              <view class="mock-classification-filters">
                <AdminSelect
                  class="mock-classification-select"
                  :options="moduleFilterOptions"
                  :value-index="selectedModuleFilterIndex"
                  prefix="分类："
                  aria-label="题目一级分类筛选"
                  @change="setModuleFilter"
                />
                <AdminSelect
                  class="mock-classification-select"
                  :options="submoduleFilterOptions"
                  :value-index="selectedSubmoduleFilterIndex"
                  :disabled="submoduleFilterDisabled"
                  prefix="考点："
                  aria-label="题目二级考点筛选"
                  @change="setSubmoduleFilter"
                />
              </view>
            </view>
          </view>

          <view v-if="optionsLoading" class="mock-picker-state">正在筛选题目…</view>
          <view v-else-if="optionsError" class="mock-picker-state error">{{ optionsError }}</view>
          <view v-else-if="!questionOptions.length" class="mock-picker-state">当前筛选条件下没有可用题目</view>
          <view v-else class="mock-question-option-list">
            <view v-for="question in questionOptions" :key="question.id" class="mock-question-option-row">
              <view class="mock-question-option-main">
                <view class="mock-question-option-tags">
                  <text>{{ question.subject }}</text>
                  <text>{{ question.module }}</text>
                  <text v-if="question.submodule">{{ question.submodule }}</text>
                  <text>难度 {{ question.difficulty }}</text>
                  <text :class="question.status === 'active' ? 'published' : 'unpublished'">{{ questionStatusText(question) }}</text>
                </view>
                <MathText class="mock-question-stem" :value="question.stem" />
              </view>
              <button
                :class="{ selected: isQuestionSelected(question.id) }"
                :disabled="isQuestionSelected(question.id) || activeSectionRemaining <= 0"
                @tap="addQuestion(question)"
              >{{ isQuestionSelected(question.id) ? '已加入' : '加入' }}</button>
            </view>
          </view>

          <view class="mock-option-pagination">
            <text>共 {{ optionCount }} 道</text>
            <view>
              <button :disabled="optionPage <= 1 || optionsLoading" @tap="changeOptionPage(optionPage - 1)">上一页</button>
              <text>{{ optionPage }} / {{ optionTotalPages }}</text>
              <button :disabled="optionPage >= optionTotalPages || optionsLoading" @tap="changeOptionPage(optionPage + 1)">下一页</button>
            </view>
          </view>
        </section>

        <aside class="mock-selected-panel">
          <view class="mock-panel-heading-row">
            <view>
              <view class="mock-panel-heading">当前题序</view>
              <view class="mock-panel-subtitle">{{ selectedSectionItems.length }}/{{ activeSectionRule.count }} 题</view>
            </view>
          </view>
          <scroll-view scroll-y class="mock-selected-scroll">
            <view v-if="!selectedSectionItems.length" class="mock-selected-empty">从左侧题库加入题目</view>
            <view v-for="(item, index) in selectedSectionItems" :key="item.question_id" class="mock-selected-row">
              <view class="mock-selected-number">{{ index + 1 }}</view>
              <view class="mock-selected-copy">
                <MathText :value="item.stem" />
                <small>难度 {{ item.difficulty }} · {{ questionStatusText(item) }}</small>
              </view>
              <view class="mock-selected-actions">
                <button :disabled="index === 0" @tap="moveQuestion(item, -1)">↑</button>
                <button :disabled="index === selectedSectionItems.length - 1" @tap="moveQuestion(item, 1)">↓</button>
                <button class="remove" @tap="removeQuestion(item)">×</button>
              </view>
            </view>
          </scroll-view>
        </aside>
      </view>
    </template>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import {
  archiveAdminMockExamPaper,
  createAdminMockExamPaper,
  fetchAdminMockExamPaperDetail,
  fetchAdminMockExamPapers,
  fetchAdminMockExamQuestionOptions,
  publishAdminMockExamPaper,
  updateAdminMockExamPaper
} from '../api/admin'
import { QUESTION_CATALOG } from '../pages-sub-admin/admin/question-admin-catalog'
import AdminSelect from './AdminSelect.vue'
import MathText from './MathText.vue'

const papers = ref([])
const paperStatus = ref('all')
const listLoading = ref(false)
const listError = ref('')
const creating = ref(false)
const editor = ref(null)
const saving = ref(false)
const publishing = ref(false)
const archiving = ref(false)
const activeSection = ref('culture')
const questionOptions = ref([])
const optionCount = ref(0)
const optionPage = ref(1)
const optionPageSize = 30
const optionsLoading = ref(false)
const optionsError = ref('')
const optionFilters = reactive({
  search: '',
  publication: 'all',
  difficulty: '',
  module: '',
  submodule: ''
})
let searchTimer = null

const paperStatusOptions = [
  { label: '全部', value: 'all' },
  { label: '草稿', value: 'draft' },
  { label: '已发布', value: 'published' },
  { label: '已下架', value: 'archived' }
]
const publicationOptions = [
  { label: '全部题目', value: 'all' },
  { label: '已发布', value: 'published' },
  { label: '未发布', value: 'unpublished' }
]
const difficultyTargets = [
  { key: 'basic', label: '基础', required: 19 },
  { key: 'medium', label: '中等', required: 28 },
  { key: 'hard', label: '较难', required: 8 }
]

const busy = computed(() => saving.value || publishing.value || archiving.value)
const sectionRules = computed(() => ({
  culture: { key: 'culture', label: '中华文化常识', subject: '中华文化', count: 20, pointValue: 2 },
  english: { key: 'english', label: '英语语言知识', subject: '英语运用', count: 20, pointValue: 1 },
  third: {
    key: 'third',
    label: editor.value?.paper?.exam_code === 'Z002' ? '数学基础' : '逻辑推理',
    subject: editor.value?.paper?.exam_code === 'Z002' ? '数学基础' : '逻辑推理',
    count: 15,
    pointValue: 3
  }
}))
const activeSectionRule = computed(() => sectionRules.value[activeSection.value])
const activeSubjectCatalog = computed(() => QUESTION_CATALOG[activeSectionRule.value?.subject] || { modules: {} })
const activeModuleNames = computed(() => Object.keys(activeSubjectCatalog.value.modules || {}))
const moduleFilterOptions = computed(() => [
  { label: '全部分类', value: '' },
  ...activeModuleNames.value.map((value) => ({ label: value, value }))
])
const selectedModuleFilterIndex = computed(() => Math.max(
  0,
  moduleFilterOptions.value.findIndex((item) => item.value === optionFilters.module)
))
const submoduleSourceModule = computed(() => (
  optionFilters.module || (activeModuleNames.value.length === 1 ? activeModuleNames.value[0] : '')
))
const submoduleFilterOptions = computed(() => [
  { label: '全部考点', value: '' },
  ...((activeSubjectCatalog.value.modules || {})[submoduleSourceModule.value] || [])
    .map((value) => ({ label: value, value }))
])
const selectedSubmoduleFilterIndex = computed(() => Math.max(
  0,
  submoduleFilterOptions.value.findIndex((item) => item.value === optionFilters.submodule)
))
const submoduleFilterDisabled = computed(() => !submoduleSourceModule.value)
const selectedSectionItems = computed(() => (
  editor.value?.items?.filter((item) => item.section_key === activeSection.value) || []
))
const selectedQuestionIdSet = computed(() => new Set((editor.value?.items || []).map((item) => item.question_id)))
const activeSectionRemaining = computed(() => Math.max(0, activeSectionRule.value.count - selectedSectionItems.value.length))
const currentTotalScore = computed(() => (editor.value?.items || []).reduce((total, item) => (
  total + (sectionRules.value[item.section_key]?.pointValue || 0)
), 0))
const sectionProgress = computed(() => Object.values(sectionRules.value).map((rule) => ({
  ...rule,
  selected: (editor.value?.items || []).filter((item) => item.section_key === rule.key).length,
  required: rule.count
})))
const difficultyProgress = computed(() => difficultyTargets.map((target) => ({
  ...target,
  selected: (editor.value?.items || []).filter((item) => difficultyBand(item) === target.key).length
})))
const localPublishReady = computed(() => (
  (editor.value?.items?.length || 0) === 55 &&
  currentTotalScore.value === 105 &&
  sectionProgress.value.every((item) => item.selected === item.required) &&
  difficultyProgress.value.every((item) => item.selected === item.required)
))
const optionTotalPages = computed(() => Math.max(1, Math.ceil(Number(optionCount.value || 0) / optionPageSize)))

onMounted(loadPapers)
onBeforeUnmount(() => {
  if (searchTimer) clearTimeout(searchTimer)
})

defineExpose({
  isBusy: () => busy.value,
  closeEditor,
  refresh: async () => {
    if (editor.value?.paper?.id) {
      await openPaper(editor.value.paper.id)
    } else {
      await loadPapers()
    }
  }
})

async function loadPapers() {
  listLoading.value = true
  listError.value = ''
  try {
    const response = await fetchAdminMockExamPapers({ status: paperStatus.value })
    papers.value = Array.isArray(response?.items) ? response.items : []
  } catch (error) {
    papers.value = []
    listError.value = errorText(error, '模拟卷加载失败，请检查数据库迁移或网络状态')
  } finally {
    listLoading.value = false
  }
}

async function changePaperStatus(value) {
  if (paperStatus.value === value) return
  paperStatus.value = value
  await loadPapers()
}

async function createPaper() {
  if (creating.value) return
  creating.value = true
  try {
    const response = await createAdminMockExamPaper({
      title: `模拟卷${chineseNumber(papers.value.length + 1)}`,
      exam_code: uni.getStorageSync('examCode') === 'Z002' ? 'Z002' : 'Z001',
      duration_minutes: 120,
      description: '',
      sort_order: papers.value.length
    })
    assignEditor(response)
    await loadQuestionOptions()
  } catch (error) {
    uni.showToast({ title: errorText(error, '模拟卷创建失败'), icon: 'none' })
  } finally {
    creating.value = false
  }
}

async function openPaper(paperId) {
  if (!paperId) return
  listLoading.value = true
  try {
    const response = await fetchAdminMockExamPaperDetail(paperId)
    assignEditor(response)
    await loadQuestionOptions()
  } catch (error) {
    uni.showToast({ title: errorText(error, '模拟卷详情加载失败'), icon: 'none' })
  } finally {
    listLoading.value = false
  }
}

function assignEditor(response, { preserveSection = false } = {}) {
  const previousSection = activeSection.value
  editor.value = {
    paper: { ...(response?.paper || {}) },
    items: (response?.items || []).map((item) => ({
      ...item,
      question_id: String(item.question_id || item.id || ''),
      section_key: String(item.section_key || 'culture')
    })),
    validation: response?.validation || null
  }
  activeSection.value = preserveSection && sectionRules.value[previousSection]
    ? previousSection
    : 'culture'
  if (!preserveSection) resetOptionClassificationFilters()
  optionPage.value = 1
}

async function closeEditor() {
  if (busy.value || !editor.value) return false
  editor.value = null
  questionOptions.value = []
  await loadPapers()
  return true
}

async function saveDraft(silent = false) {
  if (!editor.value?.paper?.id || saving.value) return false
  if (!String(editor.value.paper.title || '').trim()) {
    uni.showToast({ title: '请输入模拟卷名称', icon: 'none' })
    return false
  }
  saving.value = true
  try {
    const response = await updateAdminMockExamPaper(editor.value.paper.id, {
      title: editor.value.paper.title.trim(),
      exam_code: editor.value.paper.exam_code,
      description: String(editor.value.paper.description || '').trim(),
      duration_minutes: Math.min(360, Math.max(30, Number(editor.value.paper.duration_minutes || 120))),
      sort_order: Number(editor.value.paper.sort_order || 0),
      items: editor.value.items.map((item) => ({
        question_id: item.question_id,
        section_key: item.section_key
      }))
    })
    assignEditor(response, { preserveSection: true })
    if (!silent) uni.showToast({ title: '草稿已保存', icon: 'success' })
    return true
  } catch (error) {
    uni.showToast({ title: errorText(error, '草稿保存失败'), icon: 'none' })
    return false
  } finally {
    saving.value = false
  }
}

async function publishPaper() {
  if (!editor.value?.paper?.id || busy.value) return
  if (!localPublishReady.value) {
    uni.showModal({
      title: '卷面规格尚未满足',
      content: '请先补齐55题，并确认三科题量、105分总分与19/28/8难度比例全部达标。',
      showCancel: false,
      confirmText: '继续组卷'
    })
    return
  }
  const confirmed = await confirmAction(
    '确认发布模拟卷？',
    '系统将再次校验55题、105分、三科数量、题型和难度比例；发布后学生端立即可见。',
    '确认发布'
  )
  if (!confirmed) return
  const saved = await saveDraft(true)
  if (!saved) return
  publishing.value = true
  try {
    const response = await publishAdminMockExamPaper(editor.value.paper.id)
    assignEditor(response, { preserveSection: true })
    uni.showToast({ title: '模拟卷已发布', icon: 'success' })
  } catch (error) {
    uni.showModal({
      title: '发布校验未通过',
      content: errorText(error, '请核对题量、分值与难度比例'),
      showCancel: false,
      confirmText: '继续调整'
    })
  } finally {
    publishing.value = false
  }
}

async function archivePaper() {
  if (!editor.value?.paper?.id || busy.value) return
  const confirmed = await confirmAction('确认下架模拟卷？', '下架后学生端不再展示，已有作答记录仍保留。', '确认下架')
  if (!confirmed) return
  archiving.value = true
  try {
    const response = await archiveAdminMockExamPaper(editor.value.paper.id)
    assignEditor(response, { preserveSection: true })
    uni.showToast({ title: '模拟卷已下架', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: errorText(error, '模拟卷下架失败'), icon: 'none' })
  } finally {
    archiving.value = false
  }
}

function changeExamCode(code) {
  if (!editor.value || editor.value.paper.exam_code === code || busy.value) return
  if (!editor.value.items.length) {
    applyExamCode(code)
    return
  }
  uni.showModal({
    title: '切换考试类型？',
    content: 'Z001 与 Z002 的第三科不同，切换后将清空当前已选题目。',
    confirmText: '切换并清空',
    cancelText: '取消',
    success(result) {
      if (result.confirm) applyExamCode(code)
    }
  })
}

function applyExamCode(code) {
  editor.value.paper.exam_code = code
  editor.value.items = []
  activeSection.value = 'culture'
  resetOptionClassificationFilters()
  optionPage.value = 1
  loadQuestionOptions()
}

async function selectSection(key) {
  if (activeSection.value === key) return
  activeSection.value = key
  resetOptionClassificationFilters()
  optionPage.value = 1
  await loadQuestionOptions()
}

async function loadQuestionOptions() {
  if (!editor.value?.paper?.exam_code || optionsLoading.value) return
  optionsLoading.value = true
  optionsError.value = ''
  try {
    const response = await fetchAdminMockExamQuestionOptions({
      exam_code: editor.value.paper.exam_code,
      section_key: activeSection.value,
      publication: optionFilters.publication,
      search: optionFilters.search || undefined,
      difficulty: optionFilters.difficulty || undefined,
      module: optionFilters.module || undefined,
      submodule: optionFilters.submodule || undefined,
      limit: optionPageSize,
      offset: (optionPage.value - 1) * optionPageSize
    })
    questionOptions.value = Array.isArray(response?.items) ? response.items : []
    optionCount.value = Number(response?.count || 0)
  } catch (error) {
    questionOptions.value = []
    optionCount.value = 0
    optionsError.value = errorText(error, '题目筛选失败')
  } finally {
    optionsLoading.value = false
  }
}

function scheduleQuestionSearch() {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(applyQuestionFilters, 380)
}

function applyQuestionFilters() {
  optionPage.value = 1
  loadQuestionOptions()
}

function clearQuestionSearch() {
  optionFilters.search = ''
  applyQuestionFilters()
}

function setPublicationFilter(value) {
  if (optionFilters.publication === value) return
  optionFilters.publication = value
  applyQuestionFilters()
}

function setDifficultyFilter(value) {
  if (String(optionFilters.difficulty) === String(value)) return
  optionFilters.difficulty = value
  applyQuestionFilters()
}

function setModuleFilter(event) {
  const value = moduleFilterOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  if (optionFilters.module === value) return
  optionFilters.module = value
  optionFilters.submodule = ''
  applyQuestionFilters()
}

function setSubmoduleFilter(event) {
  const value = submoduleFilterOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  if (optionFilters.submodule === value) return
  optionFilters.submodule = value
  applyQuestionFilters()
}

function resetOptionClassificationFilters() {
  optionFilters.module = ''
  optionFilters.submodule = ''
}

function changeOptionPage(page) {
  optionPage.value = Math.min(optionTotalPages.value, Math.max(1, Number(page || 1)))
  loadQuestionOptions()
}

function addQuestion(question) {
  if (!editor.value || !question?.id || isQuestionSelected(question.id) || activeSectionRemaining.value <= 0) return
  editor.value.items.push({
    ...question,
    question_id: String(question.id),
    section_key: activeSection.value
  })
}

function removeQuestion(item) {
  if (!editor.value) return
  editor.value.items = editor.value.items.filter((row) => row.question_id !== item.question_id)
}

function moveQuestion(item, offset) {
  if (!editor.value) return
  const sectionRows = selectedSectionItems.value
  const currentSectionIndex = sectionRows.findIndex((row) => row.question_id === item.question_id)
  const target = sectionRows[currentSectionIndex + offset]
  if (!target) return
  const currentGlobalIndex = editor.value.items.findIndex((row) => row.question_id === item.question_id)
  const targetGlobalIndex = editor.value.items.findIndex((row) => row.question_id === target.question_id)
  ;[editor.value.items[currentGlobalIndex], editor.value.items[targetGlobalIndex]] = [
    editor.value.items[targetGlobalIndex],
    editor.value.items[currentGlobalIndex]
  ]
}

function isQuestionSelected(questionId) {
  return selectedQuestionIdSet.value.has(String(questionId))
}

function difficultyBand(item) {
  const value = Number(item?.difficulty || 3)
  if (value <= 2) return 'basic'
  if (value === 3) return 'medium'
  return 'hard'
}

function questionStatusText(question) {
  if (question?.status === 'active') return '已发布'
  if (question?.review_status === 'pending') return '待审核'
  if (question?.review_status === 'needs_changes') return '需修改'
  return '未发布'
}

function paperStatusText(value) {
  return { draft: '草稿', published: '已发布', archived: '已下架' }[value] || '草稿'
}

function formatDateTime(value) {
  if (!value) return '暂无时间'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 16)
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit'
  }).format(date)
}

function chineseNumber(value) {
  const digits = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十']
  if (value <= 10) return digits[value]
  if (value < 20) return `十${digits[value - 10]}`
  return String(value)
}

function errorText(error, fallback) {
  const detail = error?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (detail && typeof detail === 'object') {
    if (typeof detail.message === 'string') return detail.message
    if (Array.isArray(detail.errors)) return detail.errors.slice(0, 4).join('；')
  }
  return error?.message || fallback
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
</script>

<style scoped>
.mock-admin-shell {
  min-width: 0;
  color: #26384f;
}

button::after { border: 0; }

.mock-admin-toolbar,
.mock-editor-toolbar,
.mock-paper-settings,
.mock-panel-heading-row,
.mock-paper-admin-head,
.mock-paper-admin-footer,
.mock-editor-actions,
.mock-validation-heading,
.mock-validation-metrics,
.mock-exam-code-tabs,
.mock-filter-pills,
.mock-option-pagination,
.mock-option-pagination > view,
.mock-question-option-tags,
.mock-selected-actions {
  display: flex;
  align-items: center;
}

.mock-admin-toolbar,
.mock-panel-heading-row,
.mock-paper-admin-head,
.mock-paper-admin-footer,
.mock-validation-heading,
.mock-option-pagination {
  justify-content: space-between;
}

.mock-panel-subtitle {
  margin-top: 5px;
  color: #8794a6;
  font-size: 12px;
}

.mock-primary-button,
.mock-secondary-button,
.mock-archive-button,
.mock-refresh-options {
  width: auto;
  min-height: 38px;
  margin: 0;
  padding: 0 16px;
  border: 0;
  border-radius: 9px;
  font-size: 12px;
  font-weight: 750;
  line-height: 38px;
}

.mock-primary-button { background: #2f9f8d; color: #fff; }
.mock-secondary-button { background: #edf8f5; color: #237c6e; }
.mock-archive-button { background: #fff0ef; color: #c95a55; }
.mock-refresh-options { background: #f1f5f7; color: #607187; }
button[disabled] { opacity: .48; }

.mock-admin-toolbar {
  gap: 16px;
  margin-bottom: 18px;
}

.mock-status-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.mock-status-tabs button,
.mock-filter-pills button,
.mock-exam-code-tabs button {
  width: auto;
  min-height: 32px;
  margin: 0;
  padding: 0 13px;
  border: 1px solid #dce6e8;
  border-radius: 8px;
  background: #fff;
  color: #68788c;
  font-size: 11px;
  line-height: 30px;
  font-weight: 650;
}

.mock-status-tabs button.active,
.mock-filter-pills button.active,
.mock-exam-code-tabs button.active {
  border-color: #79d2c0;
  background: #eaf8f5;
  color: #237d6d;
}

.mock-admin-state,
.mock-picker-state,
.mock-selected-empty {
  min-height: 180px;
  border: 1px dashed #d9e3e7;
  border-radius: 14px;
  background: rgba(255,255,255,.72);
  color: #8794a5;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14px;
  font-size: 13px;
}

.mock-admin-state button {
  width: auto;
  padding: 0 14px;
  border: 0;
  border-radius: 8px;
  background: #edf8f5;
  color: #237c6e;
  font-size: 11px;
  line-height: 34px;
}

.mock-paper-admin-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(250px, 1fr));
  gap: 18px;
}

.mock-paper-admin-card {
  box-sizing: border-box;
  width: 100%;
  min-height: 210px;
  margin: 0;
  padding: 22px;
  border: 1px solid #dce7e8;
  border-radius: 14px;
  background: #fff;
  color: inherit;
  text-align: left;
  box-shadow: 0 12px 30px rgba(39,58,76,.04);
}

.mock-paper-admin-card:hover { border-color: #8bd7c8; transform: translateY(-1px); }
.mock-paper-admin-icon {
  width: 50px;
  height: 50px;
  border-radius: 15px;
  background: #dff5ef;
  color: #25816f;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 900;
}

.mock-paper-status {
  padding: 4px 9px;
  border-radius: 999px;
  background: #eef2f6;
  color: #758397;
  font-size: 10px;
  font-weight: 750;
}
.mock-paper-status.published { background: #e6f7f1; color: #21806d; }
.mock-paper-status.archived { background: #fff0ef; color: #b75a56; }
.mock-paper-status.draft { background: #fff6df; color: #a77922; }
.mock-paper-admin-name { margin-top: 24px; font-size: 20px; font-weight: 850; }
.mock-paper-admin-meta { margin-top: 9px; color: #8490a1; font-size: 12px; }
.mock-paper-admin-footer { margin-top: 31px; color: #9aa5b3; font-size: 10px; }
.mock-paper-enter { color: #278775; font-weight: 750; }

.mock-editor-toolbar {
  justify-content: space-between;
  gap: 18px;
  padding-bottom: 18px;
  border-bottom: 1px solid #e5ebee;
}
.mock-editor-actions { flex: 0 0 auto; gap: 8px; }

.mock-paper-settings {
  gap: 18px;
  margin-top: 18px;
  padding: 16px 18px;
  border: 1px solid #e0e8eb;
  border-radius: 12px;
  background: #fff;
}
.mock-setting-field { position: relative; min-width: 160px; }
.mock-setting-field > text { display: block; margin-bottom: 7px; color: #7a889b; font-size: 10px; font-weight: 700; }
.mock-title-field { flex: 1 1 auto; }
.mock-setting-field input {
  box-sizing: border-box;
  width: 100%;
  height: 36px;
  padding: 0 10px;
  border: 1px solid #dce5e8;
  border-radius: 8px;
  background: #fbfdfd;
  color: #405168;
  font-size: 11px;
}
.mock-setting-field .mock-title-input {
  color: #26384f;
  font-size: 14px;
  font-weight: 800;
}
.mock-duration-field { width: 112px; min-width: 112px; }
.mock-duration-field input { padding-right: 42px; }
.mock-duration-field small { position: absolute; right: 10px; bottom: 10px; color: #929ead; font-size: 10px; }

.mock-validation-strip {
  min-width: 0;
  flex: 1 1 auto;
  padding: 16px 18px;
  border: 1px solid #f0dca5;
  border-radius: 12px;
  background: #fffaf0;
}
.mock-validation-strip.ready { border-color: #a9dfd3; background: #f0fbf8; }
.mock-validation-heading strong { color: #735d2d; font-size: 12px; }
.mock-validation-strip.ready .mock-validation-heading strong { color: #247564; }
.mock-validation-heading text { color: #9a8c6e; font-size: 10px; }
.mock-validation-metrics { flex-wrap: wrap; gap: 8px; margin-top: 12px; }
.mock-validation-metrics view {
  min-width: 104px;
  padding: 7px 9px;
  border-radius: 7px;
  background: rgba(255,255,255,.8);
  color: #8d7a51;
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 10px;
}
.mock-validation-metrics view.complete { color: #237966; }

.mock-builder-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: 210px minmax(420px, 1fr) 330px;
  gap: 16px;
  align-items: stretch;
}
.mock-section-panel,
.mock-question-picker,
.mock-selected-panel {
  min-width: 0;
  padding: 16px;
  border: 1px solid #dfe8eb;
  border-radius: 13px;
  background: #fff;
}
.mock-panel-heading { color: #2a3d55; font-size: 14px; font-weight: 850; }
.mock-section-button {
  box-sizing: border-box;
  width: 100%;
  min-height: 88px;
  margin: 12px 0 0;
  padding: 13px;
  border: 1px solid #e2e9ec;
  border-radius: 10px;
  background: #fbfcfd;
  color: #536478;
  text-align: left;
  position: relative;
}
.mock-section-button.active { border-color: #75cdbb; background: #edf9f6; color: #286f63; }
.mock-section-button > view:first-child { display: flex; flex-direction: column; }
.mock-section-button strong { font-size: 12px; }
.mock-section-button text { margin-top: 4px; color: #8c98a7; font-size: 9px; }
.mock-section-count { position: absolute; top: 15px; right: 12px; font-size: 11px; font-weight: 800; }
.mock-section-progress { height: 4px; margin-top: 13px; overflow: hidden; border-radius: 999px; background: #e8eef0; }
.mock-section-progress-value { display: block; height: 100%; border-radius: inherit; background: #4fbca6; }
.mock-spec-note { margin-top: 18px; padding: 13px; border-radius: 10px; background: #f5f8f9; display: flex; flex-direction: column; gap: 7px; }
.mock-spec-note strong { color: #56667a; font-size: 10px; }
.mock-spec-note text { color: #8a96a5; font-size: 9px; line-height: 1.4; }

.mock-question-filters { margin-top: 14px; display: flex; flex-direction: column; gap: 9px; }
.mock-question-search { height: 38px; padding: 0 10px; border: 1px solid #dce6e8; border-radius: 9px; display: flex; align-items: center; gap: 8px; }
.mock-question-search > text { color: #6f8093; font-size: 18px; }
.mock-question-search input { min-width: 0; flex: 1 1 auto; color: #43556b; font-size: 11px; }
.mock-question-search button { width: 24px; height: 24px; margin: 0; padding: 0; border: 0; border-radius: 50%; background: #eef3f5; color: #728194; font-size: 12px; line-height: 24px; }
.mock-filter-row { display: grid; grid-template-columns: max-content minmax(260px, 1fr); gap: 12px; align-items: start; }
.mock-filter-pill-groups { display: flex; flex-direction: column; gap: 9px; }
.mock-filter-pills { flex-wrap: wrap; gap: 6px; }
.mock-filter-pills button { min-height: 28px; padding: 0 10px; line-height: 26px; font-size: 9px; }
.mock-filter-pills.difficulty { padding-top: 1px; }
.mock-classification-filters { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 9px; }
.mock-classification-select { --admin-select-height: 32px; --admin-select-font-size: 10px; --admin-select-padding-x: 10px; }

.mock-picker-state { min-height: 330px; margin-top: 12px; }
.mock-question-option-list { height: 430px; margin-top: 12px; overflow-y: auto; padding-right: 4px; }
.mock-question-option-row { padding: 12px 2px; border-bottom: 1px solid #edf1f3; display: flex; align-items: center; gap: 12px; }
.mock-question-option-main { min-width: 0; flex: 1 1 auto; }
.mock-question-option-tags { flex-wrap: wrap; gap: 5px; }
.mock-question-option-tags text { padding: 3px 6px; border-radius: 5px; background: #f1f4f6; color: #778596; font-size: 8px; }
.mock-question-option-tags text.published { background: #e7f7f2; color: #277b6b; }
.mock-question-option-tags text.unpublished { background: #fff4df; color: #a27728; }
.mock-question-stem { display: -webkit-box; margin-top: 7px; overflow: hidden; color: #405168; font-size: 11px; line-height: 1.5; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.mock-question-option-row > button { width: 54px; min-width: 54px; height: 31px; margin: 0; padding: 0; border: 0; border-radius: 7px; background: #eaf8f5; color: #27816f; font-size: 10px; line-height: 31px; font-weight: 750; }
.mock-question-option-row > button.selected { background: #f0f2f4; color: #98a2af; }
.mock-option-pagination { margin-top: 12px; color: #8a96a5; font-size: 9px; }
.mock-option-pagination > view { gap: 8px; }
.mock-option-pagination button { width: auto; min-width: 56px; height: 29px; margin: 0; padding: 0 9px; border: 1px solid #dfe7ea; border-radius: 7px; background: #fff; color: #647589; font-size: 9px; line-height: 27px; }

.mock-selected-panel { padding-right: 10px; }
.mock-selected-scroll { height: 607px; margin-top: 13px; }
.mock-selected-empty { min-height: 180px; margin-right: 6px; }
.mock-selected-row { margin: 0 6px 8px 0; padding: 10px; border: 1px solid #e3eaed; border-radius: 9px; background: #fbfcfd; display: flex; align-items: center; gap: 9px; }
.mock-selected-number { width: 25px; height: 25px; flex: 0 0 25px; border-radius: 8px; background: #e8f6f2; color: #287b6c; display: flex; align-items: center; justify-content: center; font-size: 9px; font-weight: 800; }
.mock-selected-copy { min-width: 0; flex: 1 1 auto; display: flex; flex-direction: column; }
.mock-selected-copy text { overflow: hidden; color: #4b5d73; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.mock-selected-copy small { margin-top: 4px; color: #929dab; font-size: 8px; }
.mock-selected-actions { gap: 3px; }
.mock-selected-actions button { width: 23px; height: 23px; margin: 0; padding: 0; border: 0; border-radius: 6px; background: #edf2f4; color: #66778b; font-size: 9px; line-height: 23px; }
.mock-selected-actions button.remove { background: #fff0ef; color: #c05c57; }

@media (max-width: 1250px) {
  .mock-paper-admin-grid { grid-template-columns: repeat(2, minmax(240px, 1fr)); }
  .mock-builder-grid { grid-template-columns: 190px minmax(360px, 1fr); }
  .mock-selected-panel { grid-column: 1 / -1; }
  .mock-selected-scroll { height: 320px; }
}

@media (max-width: 820px) {
  .mock-admin-toolbar,
  .mock-editor-toolbar,
  .mock-paper-settings { align-items: stretch; flex-direction: column; }
  .mock-editor-actions { flex-wrap: wrap; justify-content: flex-end; }
  .mock-paper-admin-grid,
  .mock-builder-grid { grid-template-columns: 1fr; }
  .mock-filter-row,
  .mock-classification-filters { grid-template-columns: 1fr; }
  .mock-selected-panel { grid-column: auto; }
}
</style>
