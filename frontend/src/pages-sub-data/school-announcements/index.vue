<template>
  <view
    class="page school-announcement-page"
    :class="{
      'is-glass-theme': isGlassTheme,
      'is-results-expanded': isResultsExpanded
    }"
    :style="pageInlineStyle"
  >
    <view class="announcement-shell">
      <view class="announcement-topbar">
        <button class="announcement-back-button" hover-class="none" aria-label="返回" @tap="goBack">
          <image class="announcement-back-icon" src="/static/ui-icons/png/original/back.png" mode="aspectFit" />
        </button>
        <text class="announcement-topbar-title">院校公告</text>
        <view class="announcement-topbar-placeholder"></view>
      </view>

      <view class="announcement-filter-panel">
        <view class="announcement-filter-grid">
          <picker
            class="announcement-select"
            mode="selector"
            :range="noticeTypeOptions"
            range-key="label"
            :value="noticeTypePickerIndex"
            @change="onNoticeTypePickerChange"
          >
            <view class="announcement-select-control">
              <text class="announcement-select-name">公告类型</text>
              <text class="announcement-select-value">{{ selectedNoticeTypeCompactLabel }}</text>
              <image class="announcement-select-arrow-icon" :src="announcementSelectArrowIconSrc" mode="aspectFit" aria-hidden="true" />
            </view>
          </picker>

          <picker
            class="announcement-select"
            mode="selector"
            :range="yearOptions"
            range-key="label"
            :value="yearPickerIndex"
            @change="onYearPickerChange"
          >
            <view class="announcement-select-control">
              <text class="announcement-select-name">公告年份</text>
              <text class="announcement-select-value">{{ selectedYearCompactLabel }}</text>
              <image class="announcement-select-arrow-icon" :src="announcementSelectArrowIconSrc" mode="aspectFit" aria-hidden="true" />
            </view>
          </picker>

          <picker
            class="announcement-select"
            mode="selector"
            :range="regionPickerOptions"
            range-key="label"
            :value="regionPickerIndex"
            @change="onRegionPickerChange"
          >
            <view class="announcement-select-control">
              <text class="announcement-select-name">地域查找</text>
              <text class="announcement-select-value" :class="{ muted: !selectedRegion }">
                {{ selectedRegionCompactLabel }}
              </text>
              <image class="announcement-select-arrow-icon" :src="announcementSelectArrowIconSrc" mode="aspectFit" aria-hidden="true" />
            </view>
          </picker>

          <picker
            class="announcement-select"
            :class="{ disabled: !selectedRegion }"
            mode="selector"
            :range="schoolPickerOptions"
            range-key="label"
            :value="schoolPickerIndex"
            :disabled="!selectedRegion"
            @change="onSchoolPickerChange"
          >
            <view class="announcement-select-control">
              <text class="announcement-select-name">招生院校</text>
              <text class="announcement-select-value" :class="{ muted: !selectedSchool }">
                {{ selectedSchoolCompactLabel }}
              </text>
              <image class="announcement-select-arrow-icon" :src="announcementSelectArrowIconSrc" mode="aspectFit" aria-hidden="true" />
            </view>
          </picker>
        </view>

        <view class="announcement-keyword-row">
          <view class="announcement-keyword-field">
            <view class="announcement-search-mark" aria-hidden="true"></view>
            <input
              v-model="keyword"
              class="announcement-keyword-input"
              placeholder="搜索院校、学院、公告标题或正文"
              placeholder-class="announcement-keyword-placeholder"
              confirm-type="search"
              @input="markKeywordPending"
              @confirm="runSearch"
            />
            <button
              v-if="keyword"
              class="announcement-keyword-clear"
              hover-class="none"
              aria-label="清除关键词"
              @tap="clearKeyword"
            >
              ×
            </button>
          </view>
          <button class="announcement-search-button" hover-class="none" :loading="loading" @tap="runSearch">
            查找
          </button>
        </view>
      </view>

      <view class="announcement-results-frame">
        <view class="announcement-results-heading">
          <view class="announcement-results-heading-copy">
            <text class="announcement-results-title">{{ resultTitle }}</text>
            <text v-if="resultCountText" class="announcement-results-count">{{ resultCountText }}</text>
          </view>
          <view class="announcement-results-actions">
            <button v-if="hasActiveFilters" class="announcement-results-reset" hover-class="none" @tap="resetFilters">
              重置
            </button>
            <button
              class="announcement-expand-button"
              :class="{ active: isResultsExpanded }"
              hover-class="none"
              :aria-label="isResultsExpanded ? '退出全屏浏览' : '全屏浏览'"
              @tap="toggleResultsExpanded"
            >
              <image
                class="announcement-expand-icon"
                :class="{ 'is-shrink': isResultsExpanded }"
                :src="announcementExpandIconSrc"
                mode="aspectFit"
                aria-hidden="true"
              />
            </button>
          </view>
        </view>

        <scroll-view
          class="announcement-results-scroll"
          scroll-y
          show-scrollbar="false"
          :scroll-top="resultScrollTop"
        >
          <view class="announcement-results-content">
            <view v-if="error" class="announcement-inline-state is-error">
              <text class="announcement-state-title">公告暂时加载失败</text>
              <text class="announcement-state-desc">{{ error }}</text>
              <button class="announcement-retry-button" hover-class="none" @tap="runSearch">重新加载</button>
            </view>

            <AppPageLoadingState v-else-if="loading" compact message="正在整理院校公告..." />

            <view v-else-if="hasPendingKeyword" class="announcement-inline-state">
              已保留当前筛选条件，点击“查找”检索关键词。
            </view>

            <template v-else-if="currentView === 'regions'">
              <AppEmptyState v-if="regions.length === 0" compact label="暂无地区数据" title="当前条件下暂无地区数据" />
              <view v-else class="announcement-region-grid">
                <button
                  v-for="region in regions"
                  :key="region.name"
                  class="announcement-region-card"
                  hover-class="none"
                  @tap="selectRegionFromResult(region)"
                >
                  <text class="announcement-region-name">{{ region.name }}</text>
                  <text class="announcement-region-meta">{{ region.school_count }} 所院校</text>
                  <text class="announcement-region-count">{{ region.announcement_count }} 条公告</text>
                </button>
              </view>
            </template>

            <template v-else-if="currentView === 'schools'">
              <AppEmptyState
                v-if="schoolItems.length === 0"
                compact
                label="暂无院校公告"
                title="当前地区暂无符合条件的院校公告"
              />
              <view v-else class="announcement-school-list">
                <button
                  v-for="school in schoolItems"
                  :key="school.id"
                  class="announcement-school-card"
                  hover-class="none"
                  @tap="openSchoolAnnouncements(school)"
                >
                  <view class="announcement-school-main">
                    <text class="announcement-school-name">{{ school.name }}</text>
                    <text class="announcement-school-meta">{{ formatSchoolCounts(school) }}</text>
                    <view v-if="school.image_only_count" class="announcement-school-warning">
                      {{ school.image_only_count }} 份图片公告待OCR
                    </view>
                  </view>
                  <text class="announcement-card-action">查看公告</text>
                </button>
              </view>
            </template>

            <template v-else-if="currentView === 'announcements' || currentView === 'search'">
              <AppEmptyState
                v-if="visibleAnnouncementItems.length === 0"
                compact
                label="没有匹配的公告"
                title="当前条件下没有匹配的公告"
              />
              <view v-else class="announcement-notice-list">
                <button
                  v-for="item in visibleAnnouncementItems"
                  :key="item.id"
                  class="announcement-notice-card"
                  hover-class="none"
                  @tap="openAnnouncement(item)"
                >
                  <view class="announcement-notice-head">
                    <view class="announcement-notice-tags">
                      <text class="announcement-type-tag" :class="`is-${item.notice_type}`">
                        {{ getNoticeTypeLabel(item.notice_type) }}
                      </text>
                      <text v-if="item.notice_level !== 'school'" class="announcement-level-tag">
                        {{ getNoticeLevelLabel(item.notice_level) }}
                      </text>
                      <text v-if="item.content_mode === 'image_only'" class="announcement-ocr-tag">待OCR</text>
                    </view>
                    <text class="announcement-card-action">查看</text>
                  </view>
                  <text class="announcement-notice-title">{{ item.title }}</text>
                  <text v-if="currentView === 'search'" class="announcement-notice-school">
                    {{ formatAnnouncementOwner(item) }}
                  </text>
                  <text v-else-if="item.unit_name" class="announcement-notice-school">{{ item.unit_name }}</text>
                  <text v-if="item.summary" class="announcement-notice-summary">{{ item.summary }}</text>
                  <text v-if="item.published_at" class="announcement-notice-date">{{ item.published_at }}</text>
                </button>
              </view>
              <text v-if="searchTruncated" class="announcement-truncated-note">结果较多，已优先展示前 200 条。</text>
            </template>

            <template v-else-if="currentView === 'detail'">
              <view v-if="announcementDetail" class="announcement-detail">
                <view class="announcement-detail-tags">
                  <text class="announcement-type-tag" :class="`is-${announcementDetail.notice_type}`">
                    {{ getNoticeTypeLabel(announcementDetail.notice_type) }}
                  </text>
                  <text class="announcement-level-tag">{{ getNoticeLevelLabel(announcementDetail.notice_level) }}</text>
                  <text v-if="announcementDetail.content_mode === 'image_only'" class="announcement-ocr-tag">待OCR</text>
                </view>
                <text class="announcement-detail-title">{{ announcementDetail.title }}</text>
                <text class="announcement-detail-school">
                  {{ formatAnnouncementOwner(announcementDetail) }}
                </text>
                <text v-if="announcementDetail.published_at" class="announcement-detail-date">
                  {{ announcementDetail.published_at }}
                </text>

                <view v-if="announcementDetail.content_mode === 'image_only'" class="announcement-ocr-state">
                  <text class="announcement-state-title">图片公告正在整理</text>
                  <text class="announcement-state-desc">
                    原始文件已收录 {{ announcementDetail.media_count || 0 }} 张图片，完成OCR核验后将开放全文检索。
                  </text>
                </view>
                <text v-else class="announcement-detail-content" selectable>{{ announcementDetail.content_text }}</text>

                <view v-if="announcementDetail.source_note" class="announcement-source-warning">
                  来源备注：{{ announcementDetail.source_note }}
                </view>
                <button
                  v-if="announcementDetail.source_url"
                  class="announcement-source-button"
                  hover-class="none"
                  @tap="openExternalLink(announcementDetail.source_url)"
                >
                  查看原始公告
                </button>
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
  fetchSchoolAnnouncementDetail,
  fetchSchoolAnnouncementRegions,
  fetchSchoolAnnouncements,
  fetchSchoolAnnouncementSchools,
  searchSchoolAnnouncements
} from '../../api/schoolAnnouncements'
import { getThemeIconSrc, getToneIconSrc } from '../../utils/iconAssets'
import { buildMpPageSafeStyle } from '../../utils/mpSafeLayout'
import { buildThemeStyle, getStoredThemeKey, getThemePreset } from '../../utils/theme'

const noticeTypeOptions = [
  { value: '', label: '全部公告' },
  { value: 'brochure', label: '招生简章' },
  { value: 'scoreline_retest', label: '分数线与复试' }
]

const yearOptions = [
  { value: '', label: '全部年份' },
  { value: '2026', label: '2026 年' }
]

const themeKey = ref(getStoredThemeKey())
const mpLayoutStyle = ref(buildMpPageSafeStyle())
const activeNoticeType = ref('')
const activeYear = ref('')
const selectedRegion = ref(null)
const selectedSchool = ref(null)
const keyword = ref('')
const regions = ref([])
const availableSchoolOptions = ref([])
const schoolItems = ref([])
const announcementItems = ref([])
const searchItems = ref([])
const announcementDetail = ref(null)
const currentView = ref('regions')
const hasPendingKeyword = ref(false)
const loading = ref(false)
const error = ref('')
const searchTruncated = ref(false)
const resultScrollTop = ref(0)
const isResultsExpanded = ref(false)
const searchReturnState = ref(null)
const detailReturnState = ref(null)
let requestSequence = 0
let schoolOptionsSequence = 0

const pageInlineStyle = computed(() => [
  buildThemeStyle(themeKey.value),
  mpLayoutStyle.value
].filter(Boolean).join(';'))
const announcementSelectArrowIconSrc = computed(() => (
  getThemeIconSrc('/static/ui-icons/png/original/major-catalog-dropdown.png', themeKey.value)
))
const announcementExpandIconSrc = computed(() => (
  isResultsExpanded.value
    ? getToneIconSrc('/static/ui-icons/png/original/major-catalog-shrink.png', 'white')
    : getThemeIconSrc('/static/ui-icons/png/original/major-catalog-fullscreen.png', themeKey.value)
))

const isGlassTheme = computed(() => getThemePreset(themeKey.value).circleGlass === true)
const noticeTypePickerIndex = computed(() => Math.max(0, noticeTypeOptions.findIndex(
  (item) => item.value === activeNoticeType.value
)))
const yearPickerIndex = computed(() => Math.max(0, yearOptions.findIndex((item) => item.value === activeYear.value)))

const regionPickerOptions = computed(() => {
  const options = [{ name: '', label: '全部地域' }, ...regions.value.map((item) => ({ ...item, label: item.name }))]
  if (selectedRegion.value && !options.some((item) => item.name === selectedRegion.value.name)) {
    options.push({ ...selectedRegion.value, label: selectedRegion.value.name })
  }
  return options
})

const schoolPickerOptions = computed(() => {
  if (!selectedRegion.value) return [{ id: '', name: '', label: '请先选择地域' }]
  const options = [
    { id: '', name: '', label: '全部院校' },
    ...availableSchoolOptions.value.map((item) => ({ ...item, label: item.name }))
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

const selectedNoticeTypeCompactLabel = computed(() => {
  if (activeNoticeType.value === 'brochure') return '招生简章'
  if (activeNoticeType.value === 'scoreline_retest') return '分数线/复试'
  return '全部'
})
const selectedYearCompactLabel = computed(() => activeYear.value || '全部')
const selectedRegionCompactLabel = computed(() => selectedRegion.value?.name || '全部')
const selectedSchoolCompactLabel = computed(() => selectedSchool.value?.name || (selectedRegion.value ? '全部' : '请选择'))
const visibleAnnouncementItems = computed(() => currentView.value === 'search' ? searchItems.value : announcementItems.value)
const hasActiveFilters = computed(() => Boolean(
  activeNoticeType.value || activeYear.value || selectedRegion.value?.name || selectedSchool.value?.id || keyword.value.trim()
))

const resultTitle = computed(() => {
  if (currentView.value === 'schools') return `${selectedRegion.value?.name || ''}院校公告`
  if (currentView.value === 'announcements') return selectedSchool.value?.name || '院校公告'
  if (currentView.value === 'search') return '检索结果'
  if (currentView.value === 'detail') return '公告详情'
  return '按地域浏览'
})

const resultCountText = computed(() => {
  if (loading.value || hasPendingKeyword.value) return ''
  if (currentView.value === 'schools') return `${schoolItems.value.length} 所院校`
  if (currentView.value === 'announcements') return `${announcementItems.value.length} 条公告`
  if (currentView.value === 'search') return `${searchItems.value.length} 条结果`
  if (currentView.value === 'detail') return announcementDetail.value?.year ? `${announcementDetail.value.year} 年` : ''
  return `${regions.value.length} 个地区`
})

onShow(() => {
  themeKey.value = getStoredThemeKey()
  mpLayoutStyle.value = buildMpPageSafeStyle()
  if (!regions.value.length && !loading.value) void loadRegions()
})

onBackPress(() => {
  if (isResultsExpanded.value) {
    isResultsExpanded.value = false
    return true
  }
  if (currentView.value !== 'regions') {
    void goBack()
    return true
  }
  return false
})

function beginRequest() {
  const sequence = ++requestSequence
  loading.value = true
  error.value = ''
  return sequence
}

function finishRequest(sequence) {
  if (sequence === requestSequence) loading.value = false
}

function setRequestError(sequence, requestError) {
  if (sequence !== requestSequence) return
  error.value = requestError?.detail || requestError?.message || '请检查网络后重试'
}

function apiFilters() {
  return {
    year: activeYear.value,
    notice_type: activeNoticeType.value
  }
}

function scrollResultsToTop() {
  resultScrollTop.value = 0
}

function toggleResultsExpanded() {
  isResultsExpanded.value = !isResultsExpanded.value
}

function clearResultData({ keepRegions = true } = {}) {
  if (!keepRegions) regions.value = []
  schoolItems.value = []
  announcementItems.value = []
  searchItems.value = []
  announcementDetail.value = null
  searchTruncated.value = false
}

function createViewSnapshot() {
  return {
    currentView: currentView.value,
    selectedRegion: selectedRegion.value ? { ...selectedRegion.value } : null,
    selectedSchool: selectedSchool.value ? { ...selectedSchool.value } : null,
    availableSchoolOptions: availableSchoolOptions.value.map((item) => ({ ...item })),
    schoolItems: schoolItems.value.map((item) => ({ ...item })),
    announcementItems: announcementItems.value.map((item) => ({ ...item })),
    searchItems: searchItems.value.map((item) => ({ ...item })),
    searchTruncated: searchTruncated.value,
    keyword: keyword.value,
    isResultsExpanded: isResultsExpanded.value
  }
}

function restoreViewSnapshot(snapshot) {
  if (!snapshot) return false
  requestSequence += 1
  currentView.value = snapshot.currentView
  selectedRegion.value = snapshot.selectedRegion
  selectedSchool.value = snapshot.selectedSchool
  availableSchoolOptions.value = snapshot.availableSchoolOptions
  schoolItems.value = snapshot.schoolItems
  announcementItems.value = snapshot.announcementItems
  searchItems.value = snapshot.searchItems
  searchTruncated.value = snapshot.searchTruncated
  keyword.value = snapshot.keyword
  isResultsExpanded.value = snapshot.isResultsExpanded
  announcementDetail.value = null
  hasPendingKeyword.value = false
  loading.value = false
  error.value = ''
  scrollResultsToTop()
  return true
}

async function loadRegions() {
  const sequence = beginRequest()
  try {
    const response = await fetchSchoolAnnouncementRegions(apiFilters())
    if (sequence !== requestSequence) return
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
  if (!regionName) {
    availableSchoolOptions.value = []
    return
  }
  try {
    const response = await fetchSchoolAnnouncementSchools({
      ...apiFilters(),
      region: regionName
    })
    if (sequence !== schoolOptionsSequence || selectedRegion.value?.name !== regionName) return
    availableSchoolOptions.value = response?.items || []
  } catch (requestError) {
    if (sequence === schoolOptionsSequence) availableSchoolOptions.value = []
  }
}

async function loadSchools() {
  if (!selectedRegion.value?.name) return
  const sequence = beginRequest()
  try {
    const response = await fetchSchoolAnnouncementSchools({
      ...apiFilters(),
      region: selectedRegion.value.name
    })
    if (sequence !== requestSequence) return
    schoolItems.value = response?.items || []
  } catch (requestError) {
    setRequestError(sequence, requestError)
  } finally {
    finishRequest(sequence)
  }
}

async function loadSchoolNotices() {
  if (!selectedSchool.value?.id) return
  const sequence = beginRequest()
  try {
    const response = await fetchSchoolAnnouncements(selectedSchool.value.id, {
      ...apiFilters(),
      region: selectedRegion.value?.name || '',
      keyword: keyword.value.trim()
    })
    if (sequence !== requestSequence) return
    selectedSchool.value = response?.school || selectedSchool.value
    announcementItems.value = response?.items || []
  } catch (requestError) {
    setRequestError(sequence, requestError)
  } finally {
    finishRequest(sequence)
  }
}

async function loadSearchResults() {
  const sequence = beginRequest()
  try {
    const response = await searchSchoolAnnouncements({
      ...apiFilters(),
      keyword: keyword.value.trim(),
      region: selectedRegion.value?.name || '',
      school_id: selectedSchool.value?.id || ''
    })
    if (sequence !== requestSequence) return
    searchItems.value = response?.items || []
    searchTruncated.value = Boolean(response?.truncated)
  } catch (requestError) {
    setRequestError(sequence, requestError)
  } finally {
    finishRequest(sequence)
  }
}

async function runSearch() {
  detailReturnState.value = null
  hasPendingKeyword.value = false
  error.value = ''
  scrollResultsToTop()

  if (selectedSchool.value?.id) {
    currentView.value = 'announcements'
    schoolItems.value = []
    searchItems.value = []
    await loadSchoolNotices()
    return
  }
  if (keyword.value.trim()) {
    currentView.value = 'search'
    schoolItems.value = []
    announcementItems.value = []
    await loadSearchResults()
    return
  }
  if (selectedRegion.value?.name) {
    currentView.value = 'schools'
    announcementItems.value = []
    searchItems.value = []
    await loadSchools()
    return
  }
  currentView.value = 'regions'
  clearResultData({ keepRegions: false })
  await loadRegions()
}

async function refreshFilters({ resetRegion = false } = {}) {
  searchReturnState.value = null
  detailReturnState.value = null
  selectedSchool.value = null
  availableSchoolOptions.value = []
  if (resetRegion) selectedRegion.value = null
  clearResultData({ keepRegions: false })
  if (selectedRegion.value?.name) void loadSchoolOptions()
  await runSearch()
}

async function onNoticeTypePickerChange(event) {
  const option = noticeTypeOptions[Number(event.detail.value)] || noticeTypeOptions[0]
  if (option.value === activeNoticeType.value) return
  activeNoticeType.value = option.value
  await refreshFilters()
}

async function onYearPickerChange(event) {
  const option = yearOptions[Number(event.detail.value)] || yearOptions[0]
  if (option.value === activeYear.value) return
  activeYear.value = option.value
  await refreshFilters()
}

async function onRegionPickerChange(event) {
  const option = regionPickerOptions.value[Number(event.detail.value)] || regionPickerOptions.value[0]
  const name = option?.name || ''
  if (name === (selectedRegion.value?.name || '')) return
  searchReturnState.value = null
  detailReturnState.value = null
  selectedRegion.value = name ? { ...option, name } : null
  selectedSchool.value = null
  availableSchoolOptions.value = []
  clearResultData()
  hasPendingKeyword.value = false
  if (name) void loadSchoolOptions()
  await runSearch()
}

async function onSchoolPickerChange(event) {
  const option = schoolPickerOptions.value[Number(event.detail.value)] || schoolPickerOptions.value[0]
  const schoolId = option?.id || ''
  if (schoolId === (selectedSchool.value?.id || '')) return
  searchReturnState.value = null
  detailReturnState.value = null
  selectedSchool.value = schoolId ? { ...option, id: schoolId } : null
  clearResultData()
  hasPendingKeyword.value = false
  await runSearch()
}

function markKeywordPending() {
  detailReturnState.value = null
  hasPendingKeyword.value = true
}

async function clearKeyword() {
  keyword.value = ''
  hasPendingKeyword.value = false
  await runSearch()
}

async function resetFilters() {
  requestSequence += 1
  schoolOptionsSequence += 1
  activeNoticeType.value = ''
  activeYear.value = ''
  selectedRegion.value = null
  selectedSchool.value = null
  keyword.value = ''
  availableSchoolOptions.value = []
  currentView.value = 'regions'
  hasPendingKeyword.value = false
  error.value = ''
  searchReturnState.value = null
  detailReturnState.value = null
  clearResultData({ keepRegions: false })
  scrollResultsToTop()
  await loadRegions()
}

async function selectRegionFromResult(region) {
  selectedRegion.value = { ...region, name: region.name }
  selectedSchool.value = null
  currentView.value = 'schools'
  clearResultData()
  scrollResultsToTop()
  void loadSchoolOptions()
  await loadSchools()
}

async function openSchoolAnnouncements(school) {
  const openedFromSearch = currentView.value === 'search'
  searchReturnState.value = openedFromSearch ? createViewSnapshot() : null
  selectedRegion.value = { name: school.region }
  selectedSchool.value = { ...school }
  availableSchoolOptions.value = [{ ...school }]
  currentView.value = 'announcements'
  clearResultData()
  scrollResultsToTop()
  void loadSchoolOptions()
  await loadSchoolNotices()
}

async function openAnnouncement(item) {
  detailReturnState.value = createViewSnapshot()
  currentView.value = 'detail'
  announcementDetail.value = null
  scrollResultsToTop()
  const sequence = beginRequest()
  try {
    const response = await fetchSchoolAnnouncementDetail(item.id)
    if (sequence !== requestSequence) return
    announcementDetail.value = response || null
  } catch (requestError) {
    setRequestError(sequence, requestError)
  } finally {
    finishRequest(sequence)
  }
}

function exitToHome() {
  const homeUrl = '/pages/home/index?tab=landing'
  uni.redirectTo({
    url: homeUrl,
    fail() {
      uni.reLaunch({ url: homeUrl })
    }
  })
}

function canNavigateBack() {
  return typeof getCurrentPages === 'function' && getCurrentPages().length > 1
}

async function goBack() {
  if (isResultsExpanded.value) {
    isResultsExpanded.value = false
    return
  }
  if (currentView.value === 'detail' && restoreViewSnapshot(detailReturnState.value)) {
    detailReturnState.value = null
    return
  }
  if (currentView.value === 'announcements') {
    if (restoreViewSnapshot(searchReturnState.value)) {
      searchReturnState.value = null
      return
    }
    selectedSchool.value = null
    announcementItems.value = []
    if (selectedRegion.value?.name) {
      currentView.value = 'schools'
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
    clearResultData({ keepRegions: false })
    await loadRegions()
    return
  }
  if (!canNavigateBack()) {
    exitToHome()
    return
  }
  uni.navigateBack({ delta: 1, fail: exitToHome })
}

function getNoticeTypeLabel(value) {
  return value === 'scoreline_retest' ? '分数线与复试' : '招生简章'
}

function getNoticeLevelLabel(value) {
  if (value === 'department') return '院系公告'
  if (value === 'program') return '项目公告'
  return '校级公告'
}

function formatSchoolCounts(school) {
  const parts = []
  if (school.brochure_count) parts.push(`${school.brochure_count} 份招生简章`)
  if (school.scoreline_count) parts.push(`${school.scoreline_count} 份分数线/复试公告`)
  return parts.join(' · ') || `${school.announcement_count || 0} 条公告`
}

function formatAnnouncementOwner(item) {
  return [item?.region, item?.school_name, item?.unit_name].filter(Boolean).join(' · ')
}

function openExternalLink(url) {
  if (!url) return
  // #ifdef H5
  window.open(url, '_blank', 'noopener,noreferrer')
  // #endif
  // #ifdef APP-PLUS
  plus.runtime.openURL(url)
  // #endif
  // #ifdef MP-WEIXIN
  uni.setClipboardData({
    data: url,
    success: () => uni.showToast({ title: '官方链接已复制', icon: 'none' })
  })
  // #endif
}
</script>

<style scoped>
.school-announcement-page {
  --announcement-horizontal-gutter: 32rpx;
  width: 100%;
  height: 100vh;
  min-height: 100vh;
  max-width: none;
  box-sizing: border-box;
  overflow: hidden;
  padding: calc(var(--mp-page-content-top, var(--status-bar-height, 0px)) + 12rpx) 0 0;
  background: var(--gyt-page-bg);
  color: #172033;
}

@supports (height: 100dvh) {
  .school-announcement-page { height: 100dvh; min-height: 100dvh; }
}

.announcement-shell {
  display: flex;
  height: 100%;
  min-height: 0;
  flex-direction: column;
}

.announcement-topbar {
  display: grid;
  grid-template-columns: 72rpx minmax(0, 1fr) 72rpx;
  flex: 0 0 auto;
  align-items: center;
  min-height: 76rpx;
  margin: 0 var(--announcement-horizontal-gutter);
  padding-bottom: 14rpx;
}

.announcement-back-button,
.announcement-topbar-placeholder { width: 58rpx; height: 58rpx; }

.announcement-back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0;
  padding: 0;
  border: 1rpx solid var(--gyt-primary-border);
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.88);
  box-shadow: 0 8rpx 20rpx rgba(21, 37, 68, 0.06);
}

.announcement-back-icon { width: 28rpx; height: 28rpx; }
.announcement-topbar-title { color: #172033; font-size: 34rpx; line-height: 1.3; font-weight: 900; text-align: center; }

.announcement-filter-panel {
  flex: 0 0 auto;
  margin: 0 var(--announcement-horizontal-gutter);
}

.announcement-filter-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12rpx; }
.announcement-select { display: block; width: 100%; min-width: 0; }

.announcement-select-control {
  display: flex;
  min-height: 62rpx;
  align-items: center;
  justify-content: space-between;
  gap: 8rpx;
  box-sizing: border-box;
  padding: 0 14rpx;
  overflow: hidden;
  border: 1rpx solid #dfe7f1;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.94);
}

.announcement-select.disabled .announcement-select-control { border-color: #e5eaf3; background: rgba(245, 247, 251, 0.88); }
.announcement-select-name { flex: 0 0 auto; color: #69778c; font-size: 22rpx; line-height: 1.3; font-weight: 780; }
.announcement-select-value { min-width: 0; flex: 1; overflow: hidden; color: #253047; font-size: 21rpx; line-height: 1.3; font-weight: 780; text-align: right; text-overflow: ellipsis; white-space: nowrap; }
.announcement-select-value.muted { color: #9aa5b6; }
.announcement-select-arrow-icon { display: block; width: 18rpx; height: 11rpx; flex: 0 0 auto; }
.announcement-select.disabled .announcement-select-arrow-icon { opacity: .42; }

.announcement-keyword-row { display: flex; align-items: center; gap: 12rpx; margin-top: 12rpx; }
.announcement-keyword-field { display: flex; min-width: 0; min-height: 64rpx; flex: 1; align-items: center; gap: 13rpx; box-sizing: border-box; padding: 0 15rpx; border: 1rpx solid #dfe7f1; border-radius: 16rpx; background: rgba(255, 255, 255, 0.94); }
.announcement-search-mark { position: relative; width: 22rpx; height: 22rpx; flex: 0 0 22rpx; box-sizing: border-box; border: 4rpx solid var(--gyt-primary); border-radius: 50%; opacity: 0.88; }
.announcement-search-mark::after { position: absolute; right: -9rpx; bottom: -7rpx; width: 11rpx; height: 4rpx; border-radius: 999rpx; background: var(--gyt-primary); content: ''; transform: rotate(45deg); }
.announcement-keyword-input { min-width: 0; flex: 1; color: #172033; font-size: 22rpx; line-height: 1.35; font-weight: 700; }
.announcement-keyword-placeholder { color: #a1acbd; font-weight: 600; }
.announcement-keyword-clear { width: 34rpx; height: 34rpx; margin: 0; padding: 0; border: 0; border-radius: 50%; background: #e8edf5; color: #758196; font-size: 28rpx; line-height: 31rpx; }
.announcement-search-button { width: 92rpx; min-height: 64rpx; margin: 0; padding: 0; border: 0; border-radius: 16rpx; background: var(--gyt-primary); color: #fff; font-size: 21rpx; line-height: 64rpx; font-weight: 900; box-shadow: 0 7rpx 16rpx var(--gyt-primary-shadow); }

.announcement-results-frame { display: flex; min-height: 0; margin: 18rpx var(--announcement-horizontal-gutter) calc(env(safe-area-inset-bottom, 0px) + 18rpx); flex: 1; flex-direction: column; overflow: hidden; border: 1rpx solid #e2e8f0; border-radius: 28rpx; background: rgba(255, 255, 255, 0.92); box-shadow: 0 8rpx 20rpx rgba(25, 41, 76, 0.035); }
.announcement-results-heading { display: flex; min-height: 70rpx; flex: 0 0 auto; align-items: center; justify-content: space-between; gap: 18rpx; box-sizing: border-box; padding: 18rpx 16rpx 14rpx; border-bottom: 1rpx solid #e8edf3; }
.announcement-results-heading-copy { min-width: 0; }
.announcement-results-title { display: block; overflow: hidden; color: #172033; font-size: 27rpx; line-height: 1.25; font-weight: 930; text-overflow: ellipsis; white-space: nowrap; }
.announcement-results-count { display: block; margin-top: 5rpx; color: var(--gyt-primary); font-size: 18rpx; line-height: 1.3; font-weight: 800; }
.announcement-results-actions { display: flex; flex: 0 0 auto; align-items: center; gap: 12rpx; }
.announcement-results-reset { min-height: 36rpx; margin: 0; padding: 0 4rpx; border: 0; background: transparent; color: #7e8b9e; font-size: 18rpx; line-height: 36rpx; font-weight: 750; }
.announcement-expand-button { display: flex; width: 52rpx; height: 52rpx; align-items: center; justify-content: center; margin: 0; padding: 0; border: 1rpx solid var(--gyt-primary-border); border-radius: 15rpx; background: var(--gyt-primary-soft); }
.announcement-expand-button.active { background: var(--gyt-primary); }
.announcement-expand-icon { display: block; width: 25rpx; height: 25rpx; }
.announcement-expand-button.active .announcement-expand-icon { opacity: 1; }
.announcement-results-scroll { height: 0; min-height: 0; flex: 1; }
.announcement-results-scroll::-webkit-scrollbar, .announcement-results-scroll ::-webkit-scrollbar { display: none; width: 0; height: 0; }
.announcement-results-content { min-height: 100%; box-sizing: border-box; padding: 16rpx 16rpx calc(env(safe-area-inset-bottom, 0px) + 30rpx); }

.school-announcement-page.is-results-expanded .announcement-topbar,
.school-announcement-page.is-results-expanded .announcement-filter-panel { display: none; }
.school-announcement-page.is-results-expanded .announcement-results-frame { margin: 0 0 calc(env(safe-area-inset-bottom, 0px) + 18rpx); border: 0; border-radius: 0; }
.school-announcement-page.is-results-expanded .announcement-results-heading { min-height: 82rpx; padding-right: var(--announcement-horizontal-gutter); padding-left: var(--announcement-horizontal-gutter); }
.school-announcement-page.is-results-expanded .announcement-results-content { padding-right: var(--announcement-horizontal-gutter); padding-left: var(--announcement-horizontal-gutter); }

.announcement-region-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12rpx; }
.announcement-region-card { min-width: 0; min-height: 106rpx; margin: 0; padding: 16rpx 18rpx; overflow: hidden; border: 1rpx solid #dfe7f1; border-radius: 16rpx; background: rgba(255, 255, 255, 0.94); color: #172033; text-align: left; }
.announcement-region-name { display: block; color: #172033; font-size: 27rpx; line-height: 1.3; font-weight: 920; }
.announcement-region-meta { display: block; margin-top: 9rpx; color: #68758a; font-size: 19rpx; line-height: 1.3; font-weight: 700; }
.announcement-region-count { display: block; margin-top: 4rpx; color: var(--gyt-primary); font-size: 19rpx; line-height: 1.3; font-weight: 850; }

.announcement-school-list, .announcement-notice-list { display: flex; flex-direction: column; overflow: hidden; border: 1rpx solid #e3e9f1; border-radius: 16rpx; background: #fff; }
.announcement-school-card, .announcement-notice-card { width: 100%; margin: 0; box-sizing: border-box; padding: 17rpx; border: 0; border-bottom: 1rpx solid #e8edf3; border-radius: 0; background: #fff; color: #172033; text-align: left; }
.announcement-school-card { display: flex; min-height: 108rpx; align-items: center; justify-content: space-between; gap: 16rpx; }
.announcement-school-card:last-child, .announcement-notice-card:last-child { border-bottom: 0; }
.announcement-school-main { min-width: 0; flex: 1; }
.announcement-school-name { display: block; color: #172033; font-size: 25rpx; line-height: 1.35; font-weight: 920; }
.announcement-school-meta { display: block; margin-top: 7rpx; color: #7e8a9c; font-size: 18rpx; line-height: 1.45; font-weight: 650; }
.announcement-school-warning { display: inline-flex; margin-top: 8rpx; padding: 3rpx 9rpx; border-radius: 999rpx; background: #fff5e8; color: #ad6a13; font-size: 16rpx; line-height: 1.3; font-weight: 750; }
.announcement-card-action { flex: 0 0 auto; color: var(--gyt-primary); font-size: 19rpx; line-height: 1.3; font-weight: 880; }

.announcement-notice-head { display: flex; align-items: center; justify-content: space-between; gap: 12rpx; }
.announcement-notice-tags, .announcement-detail-tags { display: flex; flex-wrap: wrap; gap: 7rpx; }
.announcement-type-tag, .announcement-level-tag, .announcement-ocr-tag { display: inline-flex; min-height: 27rpx; align-items: center; padding: 0 9rpx; border-radius: 999rpx; font-size: 16rpx; line-height: 1.2; font-weight: 850; }
.announcement-type-tag { border: 1rpx solid var(--gyt-primary-border); background: var(--gyt-primary-soft); color: var(--gyt-primary); }
.announcement-type-tag.is-scoreline_retest { border-color: #f2d6ab; background: #fff5e5; color: #a9660c; }
.announcement-level-tag { background: #f1f4f8; color: #718096; }
.announcement-ocr-tag { background: #fff0f0; color: #c65353; }
.announcement-notice-title { display: block; margin-top: 11rpx; color: #202b42; font-size: 23rpx; line-height: 1.42; font-weight: 900; }
.announcement-notice-school { display: block; margin-top: 7rpx; color: var(--gyt-primary); font-size: 18rpx; line-height: 1.4; font-weight: 780; }
.announcement-notice-summary { display: -webkit-box; margin-top: 8rpx; overflow: hidden; color: #748196; font-size: 18rpx; line-height: 1.5; font-weight: 600; -webkit-box-orient: vertical; -webkit-line-clamp: 2; }
.announcement-notice-date { display: block; margin-top: 9rpx; color: #a0a9b8; font-size: 17rpx; line-height: 1.3; font-weight: 650; }
.announcement-truncated-note { display: block; margin-top: 15rpx; color: #8792a3; font-size: 18rpx; line-height: 1.4; text-align: center; }

.announcement-detail { padding: 4rpx 3rpx 10rpx; }
.announcement-detail-title { display: block; margin-top: 14rpx; color: #172033; font-size: 29rpx; line-height: 1.42; font-weight: 930; }
.announcement-detail-school { display: block; margin-top: 10rpx; color: var(--gyt-primary); font-size: 19rpx; line-height: 1.45; font-weight: 800; }
.announcement-detail-date { display: block; margin-top: 5rpx; color: #8e99aa; font-size: 17rpx; line-height: 1.4; }
.announcement-detail-content { display: block; margin-top: 20rpx; padding: 20rpx; border: 1rpx solid #e3e9f1; border-radius: 18rpx; background: rgba(250, 252, 255, 0.92); color: #34405a; font-size: 21rpx; line-height: 1.8; white-space: pre-wrap; word-break: break-word; }
.announcement-ocr-state { margin-top: 20rpx; padding: 28rpx 22rpx; border: 1rpx dashed #efc8c8; border-radius: 16rpx; background: #fff8f8; text-align: center; }
.announcement-source-warning { margin-top: 16rpx; padding: 14rpx 16rpx; border-radius: 14rpx; background: #fff7e9; color: #8b631d; font-size: 18rpx; line-height: 1.5; }
.announcement-source-button { width: 100%; min-height: 66rpx; margin: 18rpx 0 0; border: 0; border-radius: 16rpx; background: var(--gyt-primary); color: #fff; font-size: 21rpx; line-height: 66rpx; font-weight: 900; }

.announcement-inline-state { padding: 28rpx 22rpx; border: 1rpx dashed #d8e1ec; border-radius: 16rpx; background: #fafbfd; color: #718096; font-size: 21rpx; line-height: 1.55; font-weight: 650; text-align: center; }
.announcement-inline-state.is-error { text-align: left; }
.announcement-state-title { display: block; color: #263149; font-size: 25rpx; line-height: 1.35; font-weight: 900; }
.announcement-state-desc { display: block; margin-top: 9rpx; }
.announcement-retry-button { display: inline-flex; min-height: 54rpx; align-items: center; justify-content: center; margin: 18rpx 0 0; padding: 0 22rpx; border: 0; border-radius: 999rpx; background: var(--gyt-primary); color: #fff; font-size: 20rpx; line-height: 1; font-weight: 850; }
.announcement-back-button::after, .announcement-keyword-clear::after, .announcement-search-button::after,
.announcement-results-reset::after, .announcement-expand-button::after, .announcement-region-card::after,
.announcement-school-card::after, .announcement-notice-card::after, .announcement-retry-button::after,
.announcement-source-button::after { border: 0; }

.school-announcement-page.is-glass-theme::before { position: fixed; z-index: 0; inset: 0; content: ''; pointer-events: none; background: linear-gradient(180deg, rgba(7, 43, 41, 0.4) 0%, rgba(15, 55, 52, 0.24) 46%, rgba(10, 38, 37, 0.34) 100%); }
.school-announcement-page.is-glass-theme .announcement-shell { position: relative; z-index: 1; }
.school-announcement-page.is-glass-theme .announcement-topbar { min-height: 72rpx; margin-top: 8rpx; padding: 0 12rpx; border: 1rpx solid rgba(255,255,255,.5); border-radius: 24rpx; background: rgba(14,57,54,.28); -webkit-backdrop-filter: blur(16px) saturate(116%); backdrop-filter: blur(16px) saturate(116%); }
.school-announcement-page.is-glass-theme .announcement-topbar-title { color: #f7fffd; text-shadow: 0 2rpx 10rpx rgba(2,31,29,.24); }
.school-announcement-page.is-glass-theme .announcement-back-button { border-color: rgba(255,255,255,.68); background: rgba(255,255,255,.72); box-shadow: none; }
.school-announcement-page.is-glass-theme .announcement-filter-panel { margin-top: 14rpx; padding: 16rpx; border: 1rpx solid rgba(255,255,255,.62); border-radius: 28rpx; background: rgba(231,246,241,.34); box-shadow: 0 14rpx 32rpx rgba(7,42,39,.15); -webkit-backdrop-filter: blur(20px) saturate(118%); backdrop-filter: blur(20px) saturate(118%); }
.school-announcement-page.is-glass-theme .announcement-select-control, .school-announcement-page.is-glass-theme .announcement-keyword-field { border-color: rgba(255,255,255,.72); background: rgba(255,255,255,.62); box-shadow: none; }
.school-announcement-page.is-glass-theme .announcement-select-name { color: #37534e; }
.school-announcement-page.is-glass-theme .announcement-select-value { color: #126d65; }
.school-announcement-page.is-glass-theme .announcement-select-value.muted { color: #899b98; }
.school-announcement-page.is-glass-theme .announcement-keyword-row { margin-top: 14rpx; padding-top: 14rpx; border-top: 1rpx solid rgba(255,255,255,.52); }
.school-announcement-page.is-glass-theme .announcement-search-button { background: #16786f; box-shadow: 0 10rpx 20rpx rgba(8,77,70,.28); }
.school-announcement-page.is-glass-theme .announcement-results-frame { margin-top: 20rpx; border-color: rgba(255,255,255,.58); background: rgba(236,248,244,.54); box-shadow: 0 -2rpx 22rpx rgba(6,45,42,.12); -webkit-backdrop-filter: blur(20px) saturate(114%); backdrop-filter: blur(20px) saturate(114%); }
.school-announcement-page.is-glass-theme .announcement-results-heading { border-bottom-color: rgba(255,255,255,.56); background: rgba(236,248,244,.28); }
.school-announcement-page.is-glass-theme .announcement-region-card, .school-announcement-page.is-glass-theme .announcement-school-card, .school-announcement-page.is-glass-theme .announcement-notice-card, .school-announcement-page.is-glass-theme .announcement-detail-content, .school-announcement-page.is-glass-theme .announcement-inline-state { border-color: rgba(255,255,255,.72); background: rgba(249,253,252,.58); box-shadow: none; -webkit-backdrop-filter: blur(16px) saturate(112%); backdrop-filter: blur(16px) saturate(112%); }
.school-announcement-page.is-glass-theme .announcement-school-list, .school-announcement-page.is-glass-theme .announcement-notice-list { border-color: rgba(255,255,255,.62); background: rgba(248,253,251,.4); }
.school-announcement-page.is-glass-theme .announcement-region-name, .school-announcement-page.is-glass-theme .announcement-school-name, .school-announcement-page.is-glass-theme .announcement-notice-title, .school-announcement-page.is-glass-theme .announcement-detail-title, .school-announcement-page.is-glass-theme .announcement-results-title { color: #173a35; }
.school-announcement-page.is-glass-theme .announcement-region-count, .school-announcement-page.is-glass-theme .announcement-card-action, .school-announcement-page.is-glass-theme .announcement-detail-school { color: #16786f; }

@media (max-width: 360px) {
  .school-announcement-page { --announcement-horizontal-gutter: 22rpx; }
  .announcement-select-control { padding-right: 12rpx; padding-left: 12rpx; }
  .announcement-select-name, .announcement-select-value, .announcement-keyword-input { font-size: 20rpx; }
}
</style>
