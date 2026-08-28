<template>
  <view
    class="page major-catalog-page"
    :class="{
      'is-glass-theme': isGlassTheme,
      'is-results-expanded': isResultsExpanded
    }"
    :style="pageInlineStyle"
  >
    <view class="catalog-shell">
      <view class="catalog-topbar">
        <button class="catalog-back-button" hover-class="none" aria-label="返回" @tap="goBack">
          <image class="catalog-back-icon" src="/static/ui-icons/png/original/back.png" mode="aspectFit" />
        </button>
        <text class="catalog-topbar-title">专业目录</text>
        <view class="catalog-topbar-placeholder"></view>
      </view>

      <view class="catalog-filter-panel">
        <view class="catalog-filter-grid">
          <picker
            class="catalog-select"
            mode="selector"
            :range="examOptions"
            range-key="label"
            :value="examPickerIndex"
            @change="onExamPickerChange"
          >
            <view class="catalog-select-control">
              <text class="catalog-select-name">统考科目</text>
              <text class="catalog-select-value">{{ selectedExamCompactLabel }}</text>
              <image class="catalog-select-arrow-icon" :src="catalogSelectArrowIconSrc" mode="aspectFit" aria-hidden="true" />
            </view>
          </picker>

          <picker
            class="catalog-select"
            mode="selector"
            :range="catalogYearOptions"
            range-key="label"
            :value="catalogYearPickerIndex"
            @change="onCatalogYearPickerChange"
          >
            <view class="catalog-select-control">
              <text class="catalog-select-name">目录年份</text>
              <text class="catalog-select-value">{{ selectedCatalogYearCompactLabel }}</text>
              <image class="catalog-select-arrow-icon" :src="catalogSelectArrowIconSrc" mode="aspectFit" aria-hidden="true" />
            </view>
          </picker>

          <picker
            class="catalog-select"
            mode="selector"
            :range="regionPickerOptions"
            range-key="label"
            :value="regionPickerIndex"
            @change="onRegionPickerChange"
          >
            <view class="catalog-select-control">
              <text class="catalog-select-name">地域查找</text>
              <text class="catalog-select-value" :class="{ muted: !selectedRegion }">{{ selectedRegionCompactLabel }}</text>
              <image class="catalog-select-arrow-icon" :src="catalogSelectArrowIconSrc" mode="aspectFit" aria-hidden="true" />
            </view>
          </picker>

          <picker
            class="catalog-select"
            :class="{ disabled: !selectedRegion }"
            mode="selector"
            :range="schoolPickerOptions"
            range-key="label"
            :value="schoolPickerIndex"
            :disabled="!selectedRegion"
            @change="onSchoolPickerChange"
          >
            <view class="catalog-select-control">
              <text class="catalog-select-name">招生院校</text>
              <text class="catalog-select-value" :class="{ muted: !selectedSchool }">{{ selectedSchoolCompactLabel }}</text>
              <image class="catalog-select-arrow-icon" :src="catalogSelectArrowIconSrc" mode="aspectFit" aria-hidden="true" />
            </view>
          </picker>
        </view>

        <view class="catalog-keyword-row">
          <view class="catalog-keyword-field">
            <AppSearchIcon />
            <input
              v-model="keyword"
              class="catalog-keyword-input"
              placeholder="搜索院校、专业、代码或研究方向"
              placeholder-class="catalog-keyword-placeholder"
              confirm-type="search"
              @input="markFiltersPending"
              @confirm="runSearch"
            />
            <button
              v-if="keyword"
              class="catalog-keyword-clear"
              hover-class="none"
              aria-label="清除关键词"
              @tap="clearKeyword"
            >
              ×
            </button>
          </view>
          <button class="catalog-search-button" hover-class="none" :loading="loading" @tap="runSearch">查找</button>
        </view>

      </view>

      <view class="catalog-results-frame">
        <view class="catalog-results-heading">
          <view class="catalog-results-heading-copy">
            <text class="catalog-results-title">{{ resultTitle }}</text>
            <text v-if="resultCountText" class="catalog-results-count">{{ resultCountText }}</text>
          </view>
          <view class="catalog-results-actions">
            <button v-if="hasActiveFilters" class="catalog-results-reset" hover-class="none" @tap="resetFilters">重置</button>
            <button
              class="catalog-expand-button"
              :class="{ active: isResultsExpanded }"
              hover-class="none"
              :aria-label="isResultsExpanded ? '退出全屏浏览' : '全屏浏览'"
              @tap="toggleResultsExpanded"
            >
              <image
                class="catalog-expand-icon"
                :class="{ 'is-shrink': isResultsExpanded }"
                :src="catalogExpandIconSrc"
                mode="aspectFit"
                aria-hidden="true"
              />
            </button>
          </view>
        </view>

        <scroll-view
          class="catalog-results-scroll"
          scroll-y
          show-scrollbar="false"
          :scroll-top="resultScrollTop"
        >
          <view class="catalog-results-content">
            <view v-if="!hasActiveCatalogYearData" class="catalog-inline-state">
              <text class="catalog-state-title">{{ activeCatalogYear }} 年专业目录暂未收录</text>
              <text class="catalog-state-desc">请选择“全部目录”、2026 或 2025 年已核验官方目录。</text>
            </view>

            <view v-else-if="error" class="catalog-inline-state is-error">
              <text class="catalog-state-title">目录暂时加载失败</text>
              <text class="catalog-state-desc">{{ error }}</text>
              <button class="catalog-retry-button" hover-class="none" @tap="runSearch">重新加载</button>
            </view>

            <AppPageLoadingState v-else-if="loading" compact message="正在整理招生专业目录..." />

            <view v-else-if="hasPendingFilters" class="catalog-inline-state">
              已更新筛选条件，点击“查找”查看结果。
            </view>

            <template v-else-if="currentView === 'regions'">
              <AppEmptyState
                v-if="regions.length === 0"
                compact
                label="暂无地区数据"
                title="当前筛选条件下暂无可展示的地区"
              />
              <view v-else class="catalog-region-grid">
                <button
                  v-for="region in regions"
                  :key="region.name"
                  class="catalog-region-card"
                  hover-class="none"
                  @tap="selectRegionFromResult(region)"
                >
                  <text class="catalog-region-name">{{ region.name }}</text>
                  <text class="catalog-region-meta">{{ region.school_count }} 所院校</text>
                  <text class="catalog-region-programs">{{ region.program_count }} 个专业</text>
                </button>
              </view>
            </template>

            <template v-else-if="currentView === 'schools'">
              <AppEmptyState
                v-if="schoolItems.length === 0"
                compact
                label="暂未找到院校"
                title="该筛选条件下暂未找到院校"
              />
              <view v-else class="catalog-school-list">
                <button
                  v-for="school in schoolItems"
                  :key="school.id"
                  class="catalog-school-card"
                  hover-class="none"
                  @tap="openSchoolCatalog(school)"
                >
                  <view class="catalog-school-main">
                    <text class="catalog-school-name">{{ school.name }}</text>
                    <text class="catalog-school-meta">{{ school.department_count }} 个院系 · {{ school.program_count }} 个专业</text>
                    <view class="catalog-exam-tag-row">
                      <text v-for="code in school.exam_codes" :key="code" class="catalog-code-tag">{{ code }}</text>
                    </view>
                  </view>
                  <text class="catalog-card-action">查看专业</text>
                </button>
              </view>
            </template>

            <template v-else-if="currentView === 'search'">
              <AppEmptyState
                v-if="searchResults.total_count === 0"
                compact
                label="没有找到相关院校或专业"
                title="没有找到相关院校或专业"
                description="请换一个关键词。"
              />
              <template v-else>
                <view v-if="searchResults.schools.length" class="catalog-search-section">
                  <view class="catalog-subsection-heading">
                    <text>匹配院校</text>
                    <text>{{ searchResults.school_count }} 所</text>
                  </view>
                  <view class="catalog-school-list">
                    <button
                      v-for="school in searchResults.schools"
                      :key="school.id"
                      class="catalog-school-card"
                      hover-class="none"
                      @tap="openSchoolCatalog(school)"
                    >
                      <view class="catalog-school-main">
                        <text class="catalog-school-region">{{ school.region }}</text>
                        <text class="catalog-school-name">{{ school.name }}</text>
                        <text class="catalog-school-meta">{{ school.department_count }} 个院系 · {{ school.program_count }} 个专业</text>
                      </view>
                      <text class="catalog-card-action">查看目录</text>
                    </button>
                  </view>
                </view>

                <view v-if="searchResults.programs.length" class="catalog-search-section">
                  <view class="catalog-subsection-heading">
                    <text>匹配专业</text>
                    <text>{{ searchResults.program_count }} 个</text>
                  </view>
                  <view class="catalog-search-program-list">
                    <button
                      v-for="item in searchResults.programs"
                      :key="`${item.school_id}-${item.program_id}`"
                      class="catalog-search-program-card"
                      hover-class="none"
                      @tap="openProgramResult(item)"
                    >
                      <view class="catalog-search-program-head">
                        <view class="catalog-search-program-copy">
                          <text class="catalog-search-program-name">{{ item.program_name }}</text>
                          <text v-if="item.program_code" class="catalog-search-program-code">{{ item.program_code }}</text>
                        </view>
                        <text class="catalog-card-action">查看</text>
                      </view>
                      <text class="catalog-search-program-school">{{ item.school_name }} · {{ item.department_name }}</text>
                      <view class="catalog-search-match-row">
                        <text v-for="scope in item.match_scopes" :key="scope" class="catalog-match-tag">匹配{{ scope }}</text>
                        <text v-for="code in item.exam_codes" :key="code" class="catalog-code-tag">{{ code }}</text>
                      </view>
                      <text v-if="item.matched_directions.length" class="catalog-search-direction">{{ item.matched_directions.join('、') }}</text>
                    </button>
                  </view>
                </view>

                <text v-if="searchResults.truncated" class="catalog-truncated-note">匹配结果较多，当前仅展示前 80 项。</text>
              </template>
            </template>

            <template v-else-if="currentView === 'programs'">
              <view class="catalog-school-summary">
                <view>
                  <text class="catalog-school-summary-eyebrow">{{ selectedSchool?.region }} · 招生单位</text>
                  <text class="catalog-school-summary-name">{{ selectedSchool?.name }}</text>
                  <text class="catalog-school-summary-meta">{{ selectedSchool?.department_count || 0 }} 个院系 · {{ selectedSchool?.program_count || 0 }} 个专业</text>
                </view>
                <view class="catalog-exam-tag-row is-summary">
                  <text v-for="code in selectedSchool?.exam_codes || []" :key="code" class="catalog-code-tag">{{ code }}</text>
                </view>
              </view>

              <AppEmptyState
                v-if="departments.length === 0"
                compact
                label="没有找到匹配的专业"
                title="没有找到匹配的专业"
                description="请调整关键词或统考科目。"
              />
              <view v-else class="catalog-department-list">
                <view v-for="department in departments" :key="department.name" class="catalog-department-block">
                  <view class="catalog-department-heading">
                    <text class="catalog-department-name">{{ department.name }}</text>
                    <text class="catalog-department-count">{{ department.program_count }} 个专业</text>
                  </view>

                  <view class="catalog-program-list">
                    <button
                      v-for="program in department.programs"
                      :key="program.id"
                      class="catalog-program-card"
                      :class="{ expanded: expandedProgramId === program.id }"
                      hover-class="none"
                      @tap="toggleProgram(program.id)"
                    >
                      <view class="catalog-program-head">
                        <view class="catalog-program-copy">
                          <text class="catalog-program-name">{{ program.name }}</text>
                          <text v-if="program.code" class="catalog-program-code">{{ program.code }}</text>
                          <text class="catalog-program-meta">{{ program.direction_count }} 个研究方向</text>
                        </view>
                        <view class="catalog-program-right">
                          <view class="catalog-exam-tag-row is-program">
                            <text v-for="code in program.exam_codes" :key="code" class="catalog-code-tag">{{ code }}</text>
                          </view>
                          <text class="catalog-expand-mark">{{ expandedProgramId === program.id ? '收起' : '展开' }}</text>
                        </view>
                      </view>

                      <view v-if="expandedProgramId === program.id" class="catalog-program-detail" @tap.stop>
                        <view v-for="(direction, index) in program.directions" :key="`${program.id}-${index}`" class="catalog-direction-row">
                          <view class="catalog-direction-head">
                            <text class="catalog-direction-index">{{ index + 1 }}</text>
                            <text class="catalog-direction-name">{{ direction.name }}</text>
                          </view>
                          <view class="catalog-direction-meta">
                            <text v-if="direction.tutor">导师：{{ direction.tutor }}</text>
                            <text v-if="direction.degree">学位：{{ direction.degree }}</text>
                            <text v-if="direction.study_mode">学习方式：{{ direction.study_mode }}</text>
                            <text v-if="direction.exam_code" class="catalog-direction-exam">{{ getExamLabel(direction.exam_code) }}</text>
                          </view>
                        </view>
                      </view>
                    </button>
                  </view>
                </view>
              </view>
            </template>

            <!-- #ifdef H5 -->
            <IcpFooter inline :glass="isGlassTheme" />
            <!-- #endif -->
          </view>
        </scroll-view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onBackPress, onShow } from '@dcloudio/uni-app'
import IcpFooter from '../../components/IcpFooter.vue'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import {
  fetchMajorCatalogRegions,
  fetchMajorCatalogSchoolPrograms,
  fetchMajorCatalogSchools,
  searchMajorCatalog
} from '../../api/majorCatalog'
import AppSearchIcon from '../../components/ui/AppSearchIcon.vue'
import { getThemeIconSrc, getToneIconSrc } from '../../utils/iconAssets'
import { buildMpPageSafeStyle } from '../../utils/mpSafeLayout'
import { buildThemeStyle, getStoredThemeKey, getThemePreset } from '../../utils/theme'

const examOptions = [
  { value: '', label: '全部统考科目' },
  { value: 'Z001', label: 'Z001 · 综合能力（一）' },
  { value: 'Z002', label: 'Z002 · 综合能力（二）' }
]

const catalogYearOptions = [
  { value: '', label: '全部目录' },
  { value: '2026', label: '2026 年' },
  { value: '2025', label: '2025 年' },
  { value: '2024', label: '2024 年' }
]

const availableCatalogYears = new Set(['2026', '2025'])

const examLabelMap = {
  Z001: 'Z001 · 综合能力（一）',
  Z002: 'Z002 · 综合能力（二）'
}

const themeKey = ref(getStoredThemeKey())
const mpLayoutStyle = ref(buildMpPageSafeStyle())
const activeExamCode = ref('')
const activeCatalogYear = ref('')
const selectedRegion = ref(null)
const selectedSchool = ref(null)
const keyword = ref('')
const regions = ref([])
const availableSchoolOptions = ref([])
const schoolItems = ref([])
const departments = ref([])
const searchResults = ref(createEmptySearchResults())
const searchReturnState = ref(null)
const currentView = ref('regions')
const hasPendingFilters = ref(false)
const loading = ref(false)
const error = ref('')
const expandedProgramId = ref('')
const resultScrollTop = ref(0)
const isResultsExpanded = ref(false)
let requestSequence = 0
let schoolOptionsSequence = 0

const pageInlineStyle = computed(() => [
  buildThemeStyle(themeKey.value),
  mpLayoutStyle.value
].filter(Boolean).join(';'))
const catalogSelectArrowIconSrc = computed(() => (
  getThemeIconSrc('/static/ui-icons/png/original/major-catalog-dropdown.png', themeKey.value)
))
const catalogExpandIconSrc = computed(() => (
  isResultsExpanded.value
    ? getToneIconSrc('/static/ui-icons/png/original/major-catalog-shrink.png', 'white')
    : getThemeIconSrc('/static/ui-icons/png/original/major-catalog-fullscreen.png', themeKey.value)
))

const isGlassTheme = computed(() => getThemePreset(themeKey.value).circleGlass === true)

const hasActiveCatalogYearData = computed(() => {
  return !activeCatalogYear.value || availableCatalogYears.has(activeCatalogYear.value)
})

const examPickerIndex = computed(() => Math.max(0, examOptions.findIndex((item) => item.value === activeExamCode.value)))
const catalogYearPickerIndex = computed(() => Math.max(0, catalogYearOptions.findIndex((item) => item.value === activeCatalogYear.value)))

const regionPickerOptions = computed(() => [
  { name: '', label: '全部地域' },
  ...regions.value.map((region) => ({
    ...region,
    label: region.name
  }))
])

const schoolPickerOptions = computed(() => {
  if (!selectedRegion.value) {
    return [{ id: '', name: '', label: '请先选择地域' }]
  }
  const options = [
    { id: '', name: '', label: '全部院校' },
    ...availableSchoolOptions.value.map((school) => ({ ...school, label: school.name }))
  ]
  if (selectedSchool.value && !options.some((item) => item.id === selectedSchool.value.id)) {
    options.push({ ...selectedSchool.value, label: selectedSchool.value.name })
  }
  return options
})

const regionPickerIndex = computed(() => Math.max(0, regionPickerOptions.value.findIndex(
  (item) => item.name === (selectedRegion.value?.name || '')
)))

const schoolPickerIndex = computed(() => Math.max(0, schoolPickerOptions.value.findIndex(
  (item) => item.id === (selectedSchool.value?.id || '')
)))

const selectedExamCompactLabel = computed(() => activeExamCode.value || '全部')
const selectedCatalogYearCompactLabel = computed(() => activeCatalogYear.value || '全部')
const selectedRegionCompactLabel = computed(() => selectedRegion.value?.name || '全部')
const selectedSchoolCompactLabel = computed(() => selectedSchool.value?.name || (selectedRegion.value ? '全部' : '请选择'))
const hasActiveFilters = computed(() => Boolean(
  activeExamCode.value
  || activeCatalogYear.value
  || selectedRegion.value?.name
  || selectedSchool.value?.id
  || keyword.value.trim()
))

const resultTitle = computed(() => {
  if (!hasActiveCatalogYearData.value) return '目录数据'
  if (currentView.value === 'schools') return `${selectedRegion.value?.name || ''}招生院校`
  if (currentView.value === 'programs') return selectedSchool.value?.name || '院校专业目录'
  if (currentView.value === 'search') return '检索结果'
  return '按地域浏览'
})

const resultCountText = computed(() => {
  if (loading.value || hasPendingFilters.value || !hasActiveCatalogYearData.value) return ''
  if (currentView.value === 'schools') return `${schoolItems.value.length} 所`
  if (currentView.value === 'programs') return `${departments.value.length} 个院系`
  if (currentView.value === 'search') return `${searchResults.value.total_count} 项`
  return `${regions.value.length} 个地区`
})

onShow(() => {
  themeKey.value = getStoredThemeKey()
  mpLayoutStyle.value = buildMpPageSafeStyle()
  if (!regions.value.length && !loading.value) {
    loadRegions()
  }
})

onBackPress(() => {
  if (!isResultsExpanded.value) return false
  isResultsExpanded.value = false
  return true
})

function toggleResultsExpanded() {
  isResultsExpanded.value = !isResultsExpanded.value
}

function createEmptySearchResults() {
  return {
    school_count: 0,
    program_count: 0,
    total_count: 0,
    truncated: false,
    schools: [],
    programs: []
  }
}

function createSearchReturnState() {
  return {
    activeExamCode: activeExamCode.value,
    activeCatalogYear: activeCatalogYear.value,
    selectedRegion: selectedRegion.value ? { ...selectedRegion.value } : null,
    selectedSchool: selectedSchool.value ? { ...selectedSchool.value } : null,
    keyword: keyword.value,
    availableSchoolOptions: availableSchoolOptions.value.map((school) => ({ ...school })),
    searchResults: {
      ...searchResults.value,
      schools: [...searchResults.value.schools],
      programs: [...searchResults.value.programs]
    },
    isResultsExpanded: isResultsExpanded.value
  }
}

function restoreSearchReturnState() {
  const state = searchReturnState.value
  if (!state) return false

  requestSequence += 1
  schoolOptionsSequence += 1
  activeExamCode.value = state.activeExamCode
  activeCatalogYear.value = state.activeCatalogYear
  selectedRegion.value = state.selectedRegion
  selectedSchool.value = state.selectedSchool
  keyword.value = state.keyword
  availableSchoolOptions.value = state.availableSchoolOptions
  schoolItems.value = []
  departments.value = []
  searchResults.value = state.searchResults
  currentView.value = 'search'
  hasPendingFilters.value = false
  loading.value = false
  error.value = ''
  expandedProgramId.value = ''
  isResultsExpanded.value = state.isResultsExpanded
  scrollResultsToTop()
  searchReturnState.value = null
  return true
}

function beginRequest() {
  const sequence = ++requestSequence
  loading.value = true
  error.value = ''
  return sequence
}

function isCurrentRequest(sequence) {
  return sequence === requestSequence
}

function finishRequest(sequence) {
  if (isCurrentRequest(sequence)) loading.value = false
}

function setRequestError(sequence, requestError) {
  if (!isCurrentRequest(sequence)) return
  error.value = requestError?.detail || requestError?.message || '请检查网络后重试'
}

function scrollResultsToTop() {
  resultScrollTop.value = 0
}

function clearResultData({ keepRegions = true } = {}) {
  if (!keepRegions) regions.value = []
  schoolItems.value = []
  departments.value = []
  searchResults.value = createEmptySearchResults()
  expandedProgramId.value = ''
}

async function loadRegions() {
  if (!hasActiveCatalogYearData.value) return
  const sequence = beginRequest()
  try {
    const response = await fetchMajorCatalogRegions({
      exam_code: activeExamCode.value,
      catalog_year: activeCatalogYear.value
    })
    if (!isCurrentRequest(sequence)) return
    regions.value = response?.items || []
  } catch (requestError) {
    setRequestError(sequence, requestError)
  } finally {
    finishRequest(sequence)
  }
}

async function loadSchoolOptions() {
  const regionName = selectedRegion.value?.name || ''
  const sequence = ++schoolOptionsSequence
  if (!regionName || !hasActiveCatalogYearData.value) {
    availableSchoolOptions.value = []
    return
  }
  try {
    const response = await fetchMajorCatalogSchools({
      region: regionName,
      exam_code: activeExamCode.value,
      catalog_year: activeCatalogYear.value
    })
    if (sequence !== schoolOptionsSequence || selectedRegion.value?.name !== regionName) return
    availableSchoolOptions.value = response?.items || []
  } catch (requestError) {
    if (sequence === schoolOptionsSequence) availableSchoolOptions.value = []
  }
}

async function loadSchools() {
  if (!hasActiveCatalogYearData.value || !selectedRegion.value?.name) return
  const sequence = beginRequest()
  try {
    const response = await fetchMajorCatalogSchools({
      region: selectedRegion.value.name,
      exam_code: activeExamCode.value,
      catalog_year: activeCatalogYear.value
    })
    if (!isCurrentRequest(sequence)) return
    schoolItems.value = response?.items || []
  } catch (requestError) {
    setRequestError(sequence, requestError)
  } finally {
    finishRequest(sequence)
  }
}

async function loadPrograms() {
  if (!hasActiveCatalogYearData.value || !selectedSchool.value?.id) return
  const sequence = beginRequest()
  try {
    const response = await fetchMajorCatalogSchoolPrograms(selectedSchool.value.id, {
      keyword: keyword.value.trim(),
      exam_code: activeExamCode.value,
      catalog_year: activeCatalogYear.value
    })
    if (!isCurrentRequest(sequence)) return
    selectedSchool.value = response?.school || selectedSchool.value
    departments.value = response?.departments || []
  } catch (requestError) {
    setRequestError(sequence, requestError)
  } finally {
    finishRequest(sequence)
  }
}

async function loadSearchResults() {
  const sequence = beginRequest()
  try {
    const response = await searchMajorCatalog({
      keyword: keyword.value.trim(),
      region: selectedRegion.value?.name || '',
      exam_code: activeExamCode.value,
      catalog_year: activeCatalogYear.value
    })
    if (!isCurrentRequest(sequence)) return
    searchResults.value = {
      ...createEmptySearchResults(),
      ...(response || {})
    }
  } catch (requestError) {
    setRequestError(sequence, requestError)
  } finally {
    finishRequest(sequence)
  }
}

async function runSearch() {
  searchReturnState.value = null
  expandedProgramId.value = ''
  hasPendingFilters.value = false
  error.value = ''
  scrollResultsToTop()

  if (!hasActiveCatalogYearData.value) {
    requestSequence += 1
    loading.value = false
    currentView.value = 'regions'
    clearResultData()
    return
  }

  if (selectedSchool.value?.id) {
    currentView.value = 'programs'
    schoolItems.value = []
    searchResults.value = createEmptySearchResults()
    await loadPrograms()
    return
  }

  if (keyword.value.trim()) {
    currentView.value = 'search'
    schoolItems.value = []
    departments.value = []
    await loadSearchResults()
    return
  }

  if (selectedRegion.value?.name) {
    currentView.value = 'schools'
    departments.value = []
    searchResults.value = createEmptySearchResults()
    await loadSchools()
    return
  }

  currentView.value = 'regions'
  clearResultData({ keepRegions: false })
  await loadRegions()
}

async function resetFilterContext() {
  searchReturnState.value = null
  requestSequence += 1
  schoolOptionsSequence += 1
  selectedRegion.value = null
  selectedSchool.value = null
  availableSchoolOptions.value = []
  currentView.value = 'regions'
  clearResultData({ keepRegions: false })
  scrollResultsToTop()

  if (!hasActiveCatalogYearData.value) {
    loading.value = false
    error.value = ''
    hasPendingFilters.value = false
    return
  }

  hasPendingFilters.value = false
  await runSearch()
}

async function onExamPickerChange(event) {
  const option = examOptions[Number(event.detail.value)] || examOptions[0]
  if (option.value === activeExamCode.value) return
  activeExamCode.value = option.value
  await resetFilterContext()
}

async function onCatalogYearPickerChange(event) {
  const option = catalogYearOptions[Number(event.detail.value)] || catalogYearOptions[0]
  if (option.value === activeCatalogYear.value) return
  activeCatalogYear.value = option.value
  await resetFilterContext()
}

async function onRegionPickerChange(event) {
  const option = regionPickerOptions.value[Number(event.detail.value)] || regionPickerOptions.value[0]
  const nextRegionName = option?.name || ''
  if (nextRegionName === (selectedRegion.value?.name || '')) return
  searchReturnState.value = null
  selectedRegion.value = nextRegionName ? { ...option, name: nextRegionName } : null
  selectedSchool.value = null
  availableSchoolOptions.value = []
  currentView.value = 'regions'
  clearResultData()
  hasPendingFilters.value = false
  scrollResultsToTop()
  void loadSchoolOptions()
  await runSearch()
}

async function onSchoolPickerChange(event) {
  const option = schoolPickerOptions.value[Number(event.detail.value)] || schoolPickerOptions.value[0]
  const nextSchoolId = option?.id || ''
  if (nextSchoolId === (selectedSchool.value?.id || '')) return
  searchReturnState.value = null
  selectedSchool.value = nextSchoolId ? { ...option, id: nextSchoolId } : null
  currentView.value = 'regions'
  clearResultData()
  hasPendingFilters.value = false
  scrollResultsToTop()
  await runSearch()
}

function markFiltersPending() {
  searchReturnState.value = null
  if (!hasActiveCatalogYearData.value) return
  hasPendingFilters.value = true
  expandedProgramId.value = ''
}

function clearKeyword() {
  keyword.value = ''
  markFiltersPending()
}

async function resetFilters() {
  searchReturnState.value = null
  activeExamCode.value = ''
  activeCatalogYear.value = ''
  requestSequence += 1
  schoolOptionsSequence += 1
  selectedRegion.value = null
  selectedSchool.value = null
  keyword.value = ''
  availableSchoolOptions.value = []
  currentView.value = 'regions'
  hasPendingFilters.value = false
  error.value = ''
  clearResultData({ keepRegions: false })
  scrollResultsToTop()
  await loadRegions()
}

async function selectRegionFromResult(region) {
  searchReturnState.value = null
  selectedRegion.value = { ...region, name: region.name }
  selectedSchool.value = null
  keyword.value = ''
  availableSchoolOptions.value = []
  currentView.value = 'schools'
  hasPendingFilters.value = false
  clearResultData()
  scrollResultsToTop()
  void loadSchoolOptions()
  await loadSchools()
}

async function openSchoolCatalog(school, { preserveKeyword, focusProgramId = '' } = {}) {
  const openedFromSearch = currentView.value === 'search'
  const shouldPreserveKeyword = preserveKeyword ?? openedFromSearch
  searchReturnState.value = openedFromSearch ? createSearchReturnState() : null
  selectedRegion.value = { name: school.region }
  selectedSchool.value = { ...school }
  availableSchoolOptions.value = [{ ...school }]
  if (!shouldPreserveKeyword) keyword.value = ''
  currentView.value = 'programs'
  hasPendingFilters.value = false
  schoolItems.value = []
  searchResults.value = createEmptySearchResults()
  departments.value = []
  expandedProgramId.value = ''
  scrollResultsToTop()
  void loadSchoolOptions()
  await loadPrograms()
  if (!error.value && focusProgramId) expandedProgramId.value = focusProgramId
}

async function openProgramResult(item) {
  await openSchoolCatalog(
    {
      id: item.school_id,
      name: item.school_name,
      region: item.region,
      exam_codes: item.exam_codes || []
    },
    {
      preserveKeyword: true,
      focusProgramId: item.program_id
    }
  )
}

function toggleProgram(programId) {
  expandedProgramId.value = expandedProgramId.value === programId ? '' : programId
}

function exitCatalogToHome() {
  const homeUrl = '/pages/home/index?tab=landing'
  uni.redirectTo({
    url: homeUrl,
    fail() {
      uni.reLaunch({ url: homeUrl })
    }
  })
}

function canNavigateBackFromCatalog() {
  if (typeof getCurrentPages !== 'function') return false
  return getCurrentPages().length > 1
}

async function goBack() {
  if (currentView.value === 'programs') {
    if (restoreSearchReturnState()) return
    selectedSchool.value = null
    keyword.value = ''
    expandedProgramId.value = ''
    hasPendingFilters.value = false
    if (selectedRegion.value?.name) {
      currentView.value = 'schools'
      departments.value = []
      scrollResultsToTop()
      await loadSchools()
      return
    }
  }

  if (currentView.value === 'schools' || currentView.value === 'search') {
    selectedRegion.value = null
    selectedSchool.value = null
    keyword.value = ''
    availableSchoolOptions.value = []
    currentView.value = 'regions'
    hasPendingFilters.value = false
    clearResultData({ keepRegions: false })
    scrollResultsToTop()
    await loadRegions()
    return
  }

  if (!canNavigateBackFromCatalog()) {
    exitCatalogToHome()
    return
  }

  uni.navigateBack({
    delta: 1,
    fail: exitCatalogToHome
  })
}

function getExamLabel(code) {
  return examLabelMap[code] || code
}
</script>

<style scoped>
.major-catalog-page {
  --catalog-horizontal-gutter: 32rpx;
  height: 100vh;
  min-height: 100vh;
  width: 100%;
  max-width: none;
  box-sizing: border-box;
  overflow: hidden;
  /*
   * This page owns the full App canvas.  The fallback preserves the
   * mini-program capsule offset while App uses the native status-bar height.
   */
  padding: calc(var(--mp-page-content-top, var(--status-bar-height, 0px)) + 12rpx) 0 0;
  background: var(--gyt-page-bg);
  color: #172033;
}

@supports (height: 100dvh) {
  .major-catalog-page {
    height: 100dvh;
    min-height: 100dvh;
  }
}

.catalog-shell {
  display: flex;
  height: 100%;
  min-height: 0;
  box-sizing: border-box;
  flex-direction: column;
  padding: 0;
}

.catalog-topbar {
  display: grid;
  grid-template-columns: 72rpx minmax(0, 1fr) 72rpx;
  flex: 0 0 auto;
  align-items: center;
  min-height: 76rpx;
  margin: 0 var(--catalog-horizontal-gutter);
  padding: 0 0 14rpx;
}

.catalog-back-button,
.catalog-topbar-placeholder {
  width: 58rpx;
  height: 58rpx;
}

.catalog-back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0;
  border: 1rpx solid var(--gyt-primary-border);
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 8rpx 20rpx rgba(21, 37, 68, 0.06);
}

.catalog-back-button::after,
.catalog-keyword-clear::after,
.catalog-search-button::after,
.catalog-results-reset::after,
.catalog-region-card::after,
.catalog-school-card::after,
.catalog-search-program-card::after,
.catalog-program-card::after,
.catalog-retry-button::after {
  border: 0;
}

.catalog-back-icon {
  width: 28rpx;
  height: 28rpx;
}

.catalog-topbar-title {
  color: #172033;
  font-size: 34rpx;
  line-height: 1.3;
  font-weight: 900;
  text-align: center;
}

.catalog-filter-panel {
  flex: 0 0 auto;
  box-sizing: border-box;
  margin: 0 var(--catalog-horizontal-gutter);
  padding: 0;
  border: 0;
  background: transparent;
  box-shadow: none;
}

.catalog-results-title,
.catalog-results-count,
.catalog-region-name,
.catalog-region-meta,
.catalog-region-programs,
.catalog-school-region,
.catalog-school-name,
.catalog-school-meta,
.catalog-card-action,
.catalog-subsection-heading,
.catalog-search-program-name,
.catalog-search-program-code,
.catalog-search-program-school,
.catalog-search-direction,
.catalog-school-summary-eyebrow,
.catalog-school-summary-name,
.catalog-school-summary-meta,
.catalog-department-name,
.catalog-department-count,
.catalog-program-name,
.catalog-program-code,
.catalog-program-meta,
.catalog-expand-mark,
.catalog-state-title,
.catalog-state-desc,
.catalog-truncated-note {
  display: block;
}

.catalog-filter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.catalog-select {
  display: block;
  width: 100%;
  min-width: 0;
}

.catalog-select-control {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8rpx;
  min-height: 62rpx;
  box-sizing: border-box;
  padding: 0 14rpx;
  overflow: hidden;
  border: 1rpx solid #dfe7f1;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.94);
}

.catalog-select.disabled .catalog-select-control {
  border-color: #e5eaf3;
  background: rgba(245, 247, 251, 0.88);
}

.catalog-select-value {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  color: #253047;
  font-size: 21rpx;
  line-height: 1.3;
  font-weight: 780;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.catalog-select-name {
  flex: 0 0 auto;
  color: #69778c;
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 780;
}

.catalog-select-value.muted {
  color: #9aa5b6;
}

.catalog-select-arrow-icon {
  flex: 0 0 auto;
  width: 18rpx;
  height: 11rpx;
  display: block;
}

.catalog-select.disabled .catalog-select-arrow-icon {
  opacity: 0.42;
}

.catalog-keyword-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin-top: 12rpx;
}

.catalog-keyword-field {
  display: flex;
  min-width: 0;
  min-height: 64rpx;
  flex: 1;
  align-items: center;
  gap: 13rpx;
  box-sizing: border-box;
  padding: 0 15rpx;
  border: 1rpx solid #dfe7f1;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.94);
}

.catalog-keyword-input {
  min-width: 0;
  flex: 1;
  color: #172033;
  font-size: 22rpx;
  line-height: 1.35;
  font-weight: 700;
}

.catalog-keyword-placeholder {
  color: #a1acbd;
  font-weight: 600;
}

.catalog-keyword-clear {
  width: 34rpx;
  height: 34rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #e8edf5;
  color: #758196;
  font-size: 28rpx;
  line-height: 31rpx;
  font-weight: 500;
}

.catalog-search-button {
  width: 92rpx;
  min-height: 64rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 16rpx;
  background: var(--gyt-primary);
  color: #ffffff;
  font-size: 21rpx;
  line-height: 64rpx;
  font-weight: 900;
  box-shadow: 0 7rpx 16rpx var(--gyt-primary-shadow);
}

.catalog-results-frame {
  display: flex;
  min-height: 0;
  margin: 18rpx var(--catalog-horizontal-gutter) calc(env(safe-area-inset-bottom, 0px) + 18rpx);
  flex: 1;
  flex-direction: column;
  overflow: hidden;
  border: 1rpx solid #e2e8f0;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 8rpx 20rpx rgba(25, 41, 76, 0.035);
}

.catalog-results-heading {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  min-height: 70rpx;
  box-sizing: border-box;
  padding: 18rpx 16rpx 14rpx;
  border-bottom: 1rpx solid #e8edf3;
  background: transparent;
}

.catalog-results-heading-copy {
  min-width: 0;
}

.catalog-results-title {
  overflow: hidden;
  color: #172033;
  font-size: 27rpx;
  line-height: 1.25;
  font-weight: 930;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.catalog-results-count {
  display: block;
  margin-top: 5rpx;
  color: var(--gyt-primary);
  font-size: 18rpx;
  line-height: 1.3;
  font-weight: 800;
}

.catalog-results-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 12rpx;
}

.catalog-expand-button {
  display: flex;
  width: 52rpx;
  height: 52rpx;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0;
  border: 1rpx solid var(--gyt-primary-border);
  border-radius: 15rpx;
  background: var(--gyt-primary-soft);
}

.catalog-expand-button::after {
  border: 0;
}

.catalog-expand-button.active {
  background: var(--gyt-primary);
}

.catalog-expand-icon {
  width: 25rpx;
  height: 25rpx;
  display: block;
}

.catalog-expand-button.active .catalog-expand-icon {
  opacity: 1;
}

.catalog-results-reset {
  min-height: 36rpx;
  margin: 0;
  padding: 0 4rpx;
  border: 0;
  background: transparent;
  color: #7e8b9e;
  font-size: 18rpx;
  line-height: 36rpx;
  font-weight: 750;
}

.catalog-results-scroll {
  height: 0;
  min-height: 0;
  flex: 1;
}

.catalog-results-scroll::-webkit-scrollbar,
.catalog-results-scroll ::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.catalog-results-content {
  min-height: 100%;
  box-sizing: border-box;
  padding: 16rpx 16rpx calc(env(safe-area-inset-bottom, 0px) + 30rpx);
}

.major-catalog-page.is-results-expanded .catalog-topbar,
.major-catalog-page.is-results-expanded .catalog-filter-panel {
  display: none;
}

.major-catalog-page.is-results-expanded .catalog-results-frame {
  margin: 0 0 calc(env(safe-area-inset-bottom, 0px) + 18rpx);
  border: 0;
  border-radius: 0;
}

.major-catalog-page.is-results-expanded .catalog-results-heading {
  min-height: 82rpx;
  padding-right: var(--catalog-horizontal-gutter);
  padding-left: var(--catalog-horizontal-gutter);
}

.major-catalog-page.is-results-expanded .catalog-results-content {
  padding-right: var(--catalog-horizontal-gutter);
  padding-left: var(--catalog-horizontal-gutter);
}

.catalog-region-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
  overflow: visible;
  border: 0;
  border-radius: 0;
  background: transparent;
}

.catalog-region-card,
.catalog-school-card,
.catalog-search-program-card,
.catalog-program-card {
  margin: 0;
  border: 0;
  background: #ffffff;
  color: #172033;
  text-align: left;
  transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
}

.catalog-region-card:active,
.catalog-school-card:active,
.catalog-search-program-card:active,
.catalog-program-card:active {
  transform: scale(0.988);
}

.catalog-region-card {
  min-width: 0;
  min-height: 106rpx;
  padding: 16rpx 18rpx;
  overflow: hidden;
  border: 1rpx solid #dfe7f1;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.94);
}

.catalog-region-name {
  color: #172033;
  font-size: 27rpx;
  line-height: 1.3;
  font-weight: 920;
}

.catalog-region-meta {
  margin-top: 11rpx;
  color: #68758a;
  font-size: 20rpx;
  line-height: 1.3;
  font-weight: 700;
}

.catalog-region-programs {
  margin-top: 5rpx;
  color: var(--gyt-primary);
  font-size: 19rpx;
  line-height: 1.3;
  font-weight: 850;
}

.catalog-school-list,
.catalog-search-program-list,
.catalog-program-list {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1rpx solid #e3e9f1;
  border-radius: 16rpx;
  background: #ffffff;
}

.catalog-school-card {
  display: flex;
  width: 100%;
  min-height: 104rpx;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  box-sizing: border-box;
  padding: 17rpx;
  border-bottom: 1rpx solid #e8edf3;
  border-radius: 0;
}

.catalog-school-card:last-child,
.catalog-search-program-card:last-child,
.catalog-program-card:last-child {
  border-bottom: 0;
}

.catalog-school-main,
.catalog-search-program-copy,
.catalog-program-copy {
  min-width: 0;
  flex: 1;
}

.catalog-school-region,
.catalog-school-summary-eyebrow {
  color: var(--gyt-primary);
  font-size: 19rpx;
  line-height: 1.3;
  font-weight: 900;
}

.catalog-school-name,
.catalog-school-summary-name {
  color: #172033;
  font-size: 25rpx;
  line-height: 1.35;
  font-weight: 920;
}

.catalog-school-region + .catalog-school-name {
  margin-top: 5rpx;
}

.catalog-school-meta,
.catalog-school-summary-meta {
  margin-top: 7rpx;
  color: #7e8a9c;
  font-size: 19rpx;
  line-height: 1.35;
  font-weight: 650;
}

.catalog-exam-tag-row,
.catalog-search-match-row {
  display: flex;
  flex-wrap: wrap;
  gap: 7rpx;
}

.catalog-exam-tag-row {
  margin-top: 10rpx;
}

.catalog-code-tag,
.catalog-match-tag {
  display: inline-flex;
  align-items: center;
  min-height: 27rpx;
  padding: 0 9rpx;
  border-radius: 999rpx;
  font-size: 17rpx;
  line-height: 1.2;
  font-weight: 900;
}

.catalog-code-tag {
  border: 1rpx solid var(--gyt-primary-border);
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
}

.catalog-match-tag {
  background: #f2f5fa;
  color: #6e7b91;
}

.catalog-card-action {
  flex: 0 0 auto;
  color: var(--gyt-primary);
  font-size: 19rpx;
  line-height: 1.3;
  font-weight: 880;
}

.catalog-search-section + .catalog-search-section {
  margin-top: 18rpx;
}

.catalog-subsection-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 0 2rpx 12rpx;
  color: #263149;
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 900;
}

.catalog-subsection-heading text:last-child {
  color: var(--gyt-primary);
  font-size: 19rpx;
}

.catalog-search-program-card {
  width: 100%;
  padding: 17rpx;
  border-bottom: 1rpx solid #e8edf3;
  border-radius: 0;
}

.catalog-search-program-head,
.catalog-program-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.catalog-search-program-name,
.catalog-program-name {
  color: #202b42;
  font-size: 23rpx;
  line-height: 1.36;
  font-weight: 900;
}

.catalog-search-program-code,
.catalog-program-code {
  margin-top: 5rpx;
  color: var(--gyt-primary);
  font-size: 18rpx;
  line-height: 1.25;
  font-weight: 850;
}

.catalog-search-program-school {
  margin-top: 9rpx;
  overflow: hidden;
  color: #66758a;
  font-size: 19rpx;
  line-height: 1.35;
  font-weight: 750;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.catalog-search-match-row {
  margin-top: 10rpx;
}

.catalog-search-direction {
  margin-top: 9rpx;
  overflow: hidden;
  color: #7d899b;
  font-size: 18rpx;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.catalog-truncated-note {
  margin-top: 16rpx;
  color: #8792a3;
  font-size: 18rpx;
  line-height: 1.4;
  text-align: center;
}

.catalog-school-summary {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
  margin-bottom: 18rpx;
  padding: 17rpx;
  border: 1rpx solid #e3e9f1;
  border-radius: 16rpx;
  background: #f8fafc;
}

.catalog-school-summary .catalog-exam-tag-row {
  justify-content: flex-end;
  margin-top: 0;
}

.catalog-department-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.catalog-department-heading {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 14rpx;
  margin-bottom: 11rpx;
  padding: 0 3rpx;
}

.catalog-department-name {
  min-width: 0;
  color: #263149;
  font-size: 24rpx;
  line-height: 1.35;
  font-weight: 900;
}

.catalog-department-count {
  flex: 0 0 auto;
  color: #8b96a7;
  font-size: 18rpx;
  line-height: 1.3;
  font-weight: 700;
}

.catalog-program-card {
  width: 100%;
  padding: 17rpx;
  border-bottom: 1rpx solid #e8edf3;
  border-radius: 0;
}

.catalog-program-card.expanded {
  background: var(--gyt-primary-tint);
  box-shadow: none;
}

.catalog-program-meta {
  margin-top: 8rpx;
  color: #8994a6;
  font-size: 18rpx;
  line-height: 1.3;
  font-weight: 650;
}

.catalog-program-right {
  display: flex;
  flex: 0 0 auto;
  flex-direction: column;
  align-items: flex-end;
  gap: 8rpx;
}

.catalog-exam-tag-row.is-program {
  justify-content: flex-end;
  margin-top: 0;
}

.catalog-expand-mark {
  color: var(--gyt-primary);
  font-size: 18rpx;
  line-height: 1.25;
  font-weight: 850;
}

.catalog-program-detail {
  margin-top: 15rpx;
  padding-top: 14rpx;
  border-top: 2rpx solid var(--gyt-primary-border);
}

.catalog-direction-row {
  padding: 13rpx 0;
  border-bottom: 2rpx solid rgba(222, 230, 241, 0.78);
}

.catalog-direction-row:last-child {
  padding-bottom: 2rpx;
  border-bottom: 0;
}

.catalog-direction-head {
  display: flex;
  align-items: flex-start;
  gap: 9rpx;
}

.catalog-direction-index {
  display: inline-flex;
  width: 26rpx;
  height: 26rpx;
  flex: 0 0 26rpx;
  align-items: center;
  justify-content: center;
  margin-top: 2rpx;
  border-radius: 50%;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 16rpx;
  line-height: 1;
  font-weight: 900;
}

.catalog-direction-name {
  color: #34405a;
  font-size: 21rpx;
  line-height: 1.45;
  font-weight: 800;
}

.catalog-direction-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6rpx 12rpx;
  margin: 7rpx 0 0 35rpx;
  color: #7e8a9d;
  font-size: 18rpx;
  line-height: 1.45;
  font-weight: 650;
}

.catalog-direction-exam {
  color: var(--gyt-primary);
  font-weight: 850;
}

.catalog-inline-state {
  padding: 28rpx 22rpx;
  border: 1rpx dashed #d8e1ec;
  border-radius: 16rpx;
  background: #fafbfd;
  color: #718096;
  font-size: 22rpx;
  line-height: 1.55;
  font-weight: 650;
  text-align: center;
}

.catalog-inline-state.is-error {
  text-align: left;
}

.catalog-state-title {
  color: #263149;
  font-size: 25rpx;
  line-height: 1.35;
  font-weight: 900;
}

.catalog-state-desc {
  margin-top: 9rpx;
}

.catalog-retry-button {
  display: inline-flex;
  min-height: 54rpx;
  align-items: center;
  justify-content: center;
  margin: 18rpx 0 0;
  padding: 0 22rpx;
  border: 0;
  border-radius: 999rpx;
  background: var(--gyt-primary);
  color: #ffffff;
  font-size: 20rpx;
  line-height: 1;
  font-weight: 850;
}

.major-catalog-page.is-glass-theme .catalog-topbar,
.major-catalog-page.is-glass-theme .catalog-results-frame,
.major-catalog-page.is-glass-theme .catalog-back-button,
.major-catalog-page.is-glass-theme .catalog-select-control,
.major-catalog-page.is-glass-theme .catalog-keyword-field,
.major-catalog-page.is-glass-theme .catalog-region-card,
.major-catalog-page.is-glass-theme .catalog-school-card,
.major-catalog-page.is-glass-theme .catalog-search-program-card,
.major-catalog-page.is-glass-theme .catalog-school-summary,
.major-catalog-page.is-glass-theme .catalog-program-card,
.major-catalog-page.is-glass-theme .catalog-inline-state {
  border-color: rgba(255, 255, 255, 0.7);
  background: rgba(249, 253, 252, 0.62);
  box-shadow: 0 14rpx 32rpx rgba(30, 55, 56, 0.12);
  -webkit-backdrop-filter: blur(18px) saturate(118%);
  backdrop-filter: blur(18px) saturate(118%);
}

.major-catalog-page.is-glass-theme .catalog-filter-panel {
  border: 0;
  background: transparent;
  box-shadow: none;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.major-catalog-page.is-glass-theme .catalog-region-grid,
.major-catalog-page.is-glass-theme .catalog-school-list,
.major-catalog-page.is-glass-theme .catalog-search-program-list,
.major-catalog-page.is-glass-theme .catalog-program-list {
  border-color: rgba(255, 255, 255, 0.62);
  background: rgba(248, 253, 251, 0.4);
}

.major-catalog-page.is-glass-theme .catalog-region-card,
.major-catalog-page.is-glass-theme .catalog-school-card,
.major-catalog-page.is-glass-theme .catalog-search-program-card,
.major-catalog-page.is-glass-theme .catalog-program-card {
  border-right-color: rgba(255, 255, 255, 0.5);
  border-bottom-color: rgba(255, 255, 255, 0.5);
  border-radius: 0;
  background: rgba(249, 253, 252, 0.42);
  box-shadow: none;
}

.major-catalog-page.is-glass-theme .catalog-results-heading {
  border-bottom-color: rgba(255, 255, 255, 0.56);
  background: rgba(234, 246, 242, 0.3);
}

.major-catalog-page.is-glass-theme .catalog-topbar-title,
.major-catalog-page.is-glass-theme .catalog-filter-title,
.major-catalog-page.is-glass-theme .catalog-results-title,
.major-catalog-page.is-glass-theme .catalog-region-name,
.major-catalog-page.is-glass-theme .catalog-school-name,
.major-catalog-page.is-glass-theme .catalog-search-program-name,
.major-catalog-page.is-glass-theme .catalog-school-summary-name,
.major-catalog-page.is-glass-theme .catalog-department-name,
.major-catalog-page.is-glass-theme .catalog-program-name {
  color: #1d2d2b;
}

.major-catalog-page.is-glass-theme .catalog-filter-desc,
.major-catalog-page.is-glass-theme .catalog-filter-label,
.major-catalog-page.is-glass-theme .catalog-school-meta,
.major-catalog-page.is-glass-theme .catalog-school-summary-meta,
.major-catalog-page.is-glass-theme .catalog-direction-meta {
  color: #6b7b78;
}

/* 方案一：筛选工作台 + 结果工作台，保留研圈背景并提升目录信息的阅读层级。 */
.major-catalog-page.is-glass-theme::before {
  position: fixed;
  z-index: 0;
  inset: 0;
  content: '';
  pointer-events: none;
  background: linear-gradient(180deg, rgba(7, 43, 41, 0.4) 0%, rgba(15, 55, 52, 0.24) 46%, rgba(10, 38, 37, 0.34) 100%);
}

.major-catalog-page.is-glass-theme .catalog-shell {
  position: relative;
  z-index: 1;
}

.major-catalog-page.is-glass-theme .catalog-topbar {
  min-height: 72rpx;
  margin-top: 8rpx;
  padding: 0 12rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.5);
  border-radius: 24rpx;
  background: rgba(14, 57, 54, 0.28);
  box-shadow: none;
  -webkit-backdrop-filter: blur(16px) saturate(116%);
  backdrop-filter: blur(16px) saturate(116%);
}

.major-catalog-page.is-glass-theme .catalog-topbar-title {
  color: #f7fffd;
  text-shadow: 0 2rpx 10rpx rgba(2, 31, 29, 0.24);
}

.major-catalog-page.is-glass-theme .catalog-back-button {
  border-color: rgba(255, 255, 255, 0.68);
  background: rgba(255, 255, 255, 0.72);
  box-shadow: none;
}

.major-catalog-page.is-glass-theme .catalog-filter-panel {
  margin-top: 14rpx;
  padding: 16rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.62);
  border-radius: 28rpx;
  background: rgba(231, 246, 241, 0.34);
  box-shadow: 0 14rpx 32rpx rgba(7, 42, 39, 0.15);
  -webkit-backdrop-filter: blur(20px) saturate(118%);
  backdrop-filter: blur(20px) saturate(118%);
}

.major-catalog-page.is-glass-theme .catalog-filter-grid {
  gap: 12rpx;
}

.major-catalog-page.is-glass-theme .catalog-select-control {
  min-height: 64rpx;
  border-color: rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.54);
  box-shadow: none;
}

.major-catalog-page.is-glass-theme .catalog-select-name {
  color: #37534e;
}

.major-catalog-page.is-glass-theme .catalog-select-value {
  color: #126d65;
}

.major-catalog-page.is-glass-theme .catalog-select-value.muted,
.major-catalog-page.is-glass-theme .catalog-select.disabled .catalog-select-value {
  color: #899b98;
}

.major-catalog-page.is-glass-theme .catalog-select.disabled .catalog-select-control {
  border-color: rgba(255, 255, 255, 0.42);
  background: rgba(230, 238, 236, 0.36);
}

.major-catalog-page.is-glass-theme .catalog-keyword-row {
  margin-top: 14rpx;
  padding-top: 14rpx;
  border-top: 1rpx solid rgba(255, 255, 255, 0.52);
}

.major-catalog-page.is-glass-theme .catalog-keyword-field {
  border-color: rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.7);
  box-shadow: none;
}

.major-catalog-page.is-glass-theme .catalog-keyword-input {
  color: #1f3733;
}

.major-catalog-page.is-glass-theme .catalog-keyword-placeholder {
  color: #80918e;
}

.major-catalog-page.is-glass-theme .catalog-search-button {
  background: #16786f;
  box-shadow: 0 10rpx 20rpx rgba(8, 77, 70, 0.28);
}

.major-catalog-page.is-glass-theme .catalog-results-frame {
  margin-top: 20rpx;
  border-color: rgba(255, 255, 255, 0.58);
  border-radius: 30rpx;
  background: rgba(236, 248, 244, 0.54);
  box-shadow: 0 -2rpx 22rpx rgba(6, 45, 42, 0.12);
  -webkit-backdrop-filter: blur(20px) saturate(114%);
  backdrop-filter: blur(20px) saturate(114%);
}

.major-catalog-page.is-glass-theme .catalog-results-heading {
  min-height: 92rpx;
  padding: 16rpx;
  border-bottom-color: rgba(255, 255, 255, 0.56);
  background: rgba(236, 248, 244, 0.28);
}

.major-catalog-page.is-glass-theme .catalog-results-title {
  color: #173a35;
}

.major-catalog-page.is-glass-theme .catalog-results-count {
  display: inline-flex;
  margin-top: 4rpx;
  padding: 2rpx 12rpx;
  border: 1rpx solid rgba(22, 120, 111, 0.16);
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.4);
  color: #16786f;
  font-weight: 800;
}

.major-catalog-page.is-glass-theme .catalog-expand-button {
  border: 1rpx solid rgba(255, 255, 255, 0.68);
  background: rgba(255, 255, 255, 0.58);
  box-shadow: none;
}

.major-catalog-page.is-glass-theme .catalog-region-grid {
  border: 0;
  border-radius: 0;
  background: transparent;
}

.major-catalog-page.is-glass-theme .catalog-region-card {
  display: flex;
  min-height: 106rpx;
  padding: 16rpx 18rpx;
  flex-wrap: wrap;
  align-content: center;
  column-gap: 0;
  row-gap: 2rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.72);
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.54);
  box-shadow: none;
}

.major-catalog-page.is-glass-theme .catalog-region-name {
  flex: 0 0 100%;
  margin-bottom: 2rpx;
  color: #153a35;
  font-size: 26rpx;
}

.major-catalog-page.is-glass-theme .catalog-region-meta,
.major-catalog-page.is-glass-theme .catalog-region-programs {
  display: inline;
  margin: 0;
  font-size: 18rpx;
  line-height: 1.5;
}

.major-catalog-page.is-glass-theme .catalog-region-meta {
  color: #637a76;
}

.major-catalog-page.is-glass-theme .catalog-region-meta::after {
  content: ' · ';
  color: rgba(57, 100, 93, 0.62);
}

.major-catalog-page.is-glass-theme .catalog-region-programs {
  color: #16786f;
  font-weight: 820;
}

.major-catalog-page.is-glass-theme.is-results-expanded .catalog-results-frame {
  border-radius: 0;
}

@media (max-width: 360px) {
  .major-catalog-page {
    --catalog-horizontal-gutter: 22rpx;
  }

  .catalog-select-control {
    padding-right: 13rpx;
    padding-left: 13rpx;
  }

  .catalog-select-value,
  .catalog-keyword-input {
    font-size: 20rpx;
  }

  .catalog-search-button {
    width: 92rpx;
  }
}
</style>
