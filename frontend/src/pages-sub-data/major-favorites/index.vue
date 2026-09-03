<template>
  <view class="page major-favorites-page" :style="pageInlineStyle">
    <AppPageHeader title="院校专业收藏" fixed @back="goBack" />

    <view class="favorite-tabs" role="tablist" aria-label="选择收藏类型">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        class="favorite-tab"
        :class="{ active: activeTab === tab.key }"
        role="tab"
        :aria-selected="activeTab === tab.key"
        hover-class="none"
        @tap="selectTab(tab.key)"
      >
        {{ tab.label }}
      </button>
    </view>

    <AppPageLoadingState
      v-if="currentState.loading && currentState.items.length === 0"
      message="正在整理收藏内容..."
    />

    <view v-else-if="currentState.error && currentState.items.length === 0" class="state-card warning">
      <text>{{ currentState.error }}</text>
      <button hover-class="none" @tap="reloadCurrent">重新加载</button>
    </view>

    <AppEmptyState
      v-else-if="currentState.items.length === 0"
      :label="activeTab === 'school' ? '还没有收藏院校' : '还没有收藏专业'"
      :title="activeTab === 'school' ? '还没有收藏院校' : '还没有收藏专业'"
      description="在专业目录点击收藏图标后，会同步保存在这里。"
    >
      <button hover-class="none" @tap="openMajorCatalog">去专业目录看看</button>
    </AppEmptyState>

    <scroll-view
      v-else
      scroll-y
      enhanced
      class="favorites-scroll"
      :scroll-top="currentState.scrollTop"
      :refresher-enabled="true"
      :refresher-triggered="currentState.refreshing"
      :show-scrollbar="false"
      @scroll="handleScroll"
      @scrolltolower="loadMore"
      @refresherrefresh="refreshCurrent"
    >
      <view class="list-heading">
        <text>{{ activeTab === 'school' ? '收藏的院校' : '收藏的专业' }}</text>
        <text class="list-heading-note">按收藏时间排列</text>
      </view>

      <view class="favorite-list">
        <view
          v-for="item in currentState.items"
          :key="item.key"
          class="favorite-card"
          :class="{ unavailable: !item.available }"
          @tap="openFavorite(item)"
        >
          <view class="favorite-card-main">
            <view class="favorite-card-kicker">
              <text>{{ item.catalogYear }} 年目录</text>
              <text v-if="!item.available" class="history-tag">历史目录</text>
            </view>

            <template v-if="item.targetType === 'school'">
              <view class="favorite-card-title">{{ item.schoolName }}</view>
              <view v-if="item.regionName" class="favorite-card-context">{{ item.regionName }}</view>
              <view v-if="item.departmentCount || item.programCount" class="favorite-card-meta">
                <text v-if="item.departmentCount">{{ item.departmentCount }} 个院系</text>
                <text v-if="item.departmentCount && item.programCount">·</text>
                <text v-if="item.programCount">{{ item.programCount }} 个专业</text>
              </view>
            </template>

            <template v-else>
              <view class="favorite-card-title-row">
                <view class="favorite-card-title">{{ item.programName }}</view>
                <view v-if="item.examCodes.length" class="exam-code-row">
                  <text v-for="code in item.examCodes" :key="code" class="exam-code">{{ code }}</text>
                </view>
              </view>
              <view class="favorite-card-code">{{ item.programCode || '专业代码待补充' }}</view>
              <view class="favorite-card-context">
                {{ [item.schoolName, item.departmentName].filter(Boolean).join(' · ') }}
              </view>
              <view v-if="item.directionCount" class="favorite-card-meta">{{ item.directionCount }} 个研究方向</view>
            </template>
          </view>

          <view class="favorite-card-actions">
            <button
              class="favorite-remove"
              :disabled="isPending(item)"
              :aria-label="`取消收藏${item.targetType === 'school' ? '院校' : '专业'}`"
              hover-class="none"
              @tap.stop="removeFavorite(item)"
            >
              <image src="/static/ui-icons/png/gold/favorite.png" mode="aspectFit" />
            </button>
            <text class="favorite-open">{{ item.available ? '查看' : '已失效' }} ›</text>
          </view>
        </view>
      </view>

      <view class="load-state" @tap="loadMore">
        {{ currentState.loadingMore ? '正在加载更多…' : currentState.hasMore ? '继续下滑加载更多' : '已加载全部收藏' }}
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { deleteMajorCatalogFavorite, listMajorCatalogFavorites } from '../../api/majorCatalogFavorites'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import { isLoggedIn } from '../../utils/auth'
import { buildMpPageSafeStyle } from '../../utils/mpSafeLayout'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const PAGE_PATH = '/pages-sub-data/major-favorites/index'
const ACTIVE_TAB_STORAGE_KEY = 'major-catalog-favorites-active-tab-v1'
const PAGE_SIZE = 40

const tabs = [
  { key: 'school', label: '院校' },
  { key: 'program', label: '专业' }
]

function createCollectionState() {
  return {
    items: [],
    cursor: '',
    hasMore: false,
    loading: false,
    loadingMore: false,
    refreshing: false,
    loaded: false,
    error: '',
    scrollTop: 0
  }
}

const activeTab = ref('school')
const themeKey = ref(getStoredThemeKey())
const mpLayoutStyle = ref(buildMpPageSafeStyle())
const pendingKeys = ref([])
const collectionStates = reactive({
  school: createCollectionState(),
  program: createCollectionState()
})

const currentState = computed(() => collectionStates[activeTab.value])
const pageInlineStyle = computed(() => [buildThemeStyle(themeKey.value), mpLayoutStyle.value].filter(Boolean).join(';'))

onLoad((options = {}) => {
  const requestedTab = String(options.tab || uni.getStorageSync(ACTIVE_TAB_STORAGE_KEY) || '')
  if (tabs.some((tab) => tab.key === requestedTab)) {
    activeTab.value = requestedTab
    uni.setStorageSync(ACTIVE_TAB_STORAGE_KEY, requestedTab)
  }
})

onShow(() => {
  themeKey.value = getStoredThemeKey()
  mpLayoutStyle.value = buildMpPageSafeStyle()
  if (!isLoggedIn()) {
    const returnUrl = `${PAGE_PATH}?tab=${encodeURIComponent(activeTab.value)}`
    uni.reLaunch({ url: `/pages/login/index?redirect=${encodeURIComponent(returnUrl)}` })
    return
  }
  void loadFavorites(activeTab.value, { reset: true, silent: currentState.value.loaded })
})

function selectTab(tab) {
  if (!collectionStates[tab] || activeTab.value === tab) return
  activeTab.value = tab
  uni.setStorageSync(ACTIVE_TAB_STORAGE_KEY, tab)
  if (!collectionStates[tab].loaded) void loadFavorites(tab, { reset: true })
}

async function loadFavorites(tab, { reset = false, silent = false } = {}) {
  const state = collectionStates[tab]
  if (!state || state.loading || state.loadingMore || state.refreshing) return

  if (reset) {
    if (silent) state.refreshing = true
    else state.loading = true
  } else {
    if (!state.hasMore) return
    state.loadingMore = true
  }
  state.error = ''

  try {
    const response = await listMajorCatalogFavorites({
      targetType: tab,
      limit: PAGE_SIZE,
      cursor: reset ? '' : state.cursor
    })
    const items = normalizeFavoriteItems(response?.items || [])
    state.items = reset ? items : mergeUniqueFavorites(state.items, items)
    state.cursor = String(response?.next_cursor || response?.nextCursor || response?.pagination?.next_cursor || '')
    state.hasMore = response?.has_more ?? response?.hasMore ?? Boolean(state.cursor)
    state.loaded = true
  } catch (error) {
    state.error = error?.detail || '收藏内容读取失败，请稍后重试'
    if ((!reset || silent) && state.items.length) {
      uni.showToast({ title: state.error, icon: 'none' })
    }
  } finally {
    state.loading = false
    state.loadingMore = false
    state.refreshing = false
  }
}

function normalizeFavoriteItems(rows) {
  return rows.map(normalizeFavoriteItem).filter((item) => item.targetId)
}

function normalizeFavoriteItem(row = {}) {
  const snapshot = parseSnapshot(row.snapshot)
  const current = row.target || row.current || row.resource || {}
  const data = { ...snapshot, ...current }
  const targetType = String(row.target_type || data.target_type || '').toLowerCase() === 'program' ? 'program' : 'school'
  const targetId = String(row.target_id || data.target_id || (targetType === 'program' ? data.program_id : data.school_id) || '')
  const schoolId = String(row.school_id || data.school_id || (targetType === 'school' ? targetId : ''))
  const catalogYear = String(row.catalog_year || data.catalog_year || '')
  const examCodes = normalizeExamCodes(data.exam_codes || data.examCodes || data.exam_code)

  return {
    key: `${catalogYear}:${targetType}:${targetId}`,
    favoriteId: row.id || row.favorite_id || '',
    catalogYear,
    targetType,
    targetId,
    schoolId,
    schoolName: String(data.school_name || (targetType === 'school' ? data.name : '') || '院校信息待补充'),
    regionName: String(data.region_name || data.region || ''),
    departmentName: String(data.department_name || data.department || ''),
    programName: String(data.program_name || (targetType === 'program' ? data.name : '') || '专业信息待补充'),
    programCode: String(data.program_code || data.code || ''),
    departmentCount: Math.max(0, Number(data.department_count || 0) || 0),
    programCount: Math.max(0, Number(data.program_count || 0) || 0),
    directionCount: Math.max(0, Number(data.direction_count || data.research_direction_count || 0) || 0),
    examCodes,
    available: row.available !== false,
    createdAt: row.created_at || ''
  }
}

function parseSnapshot(value) {
  if (value && typeof value === 'object' && !Array.isArray(value)) return value
  if (typeof value !== 'string' || !value.trim()) return {}
  try {
    const parsed = JSON.parse(value)
    return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : {}
  } catch (error) {
    return {}
  }
}

function normalizeExamCodes(value) {
  const values = Array.isArray(value) ? value : String(value || '').split(/[、,，/\s]+/)
  return [...new Set(values.map((item) => String(item || '').trim().toUpperCase()).filter(Boolean))]
}

function mergeUniqueFavorites(current, incoming) {
  const merged = new Map(current.map((item) => [item.key, item]))
  incoming.forEach((item) => merged.set(item.key, item))
  return sortFavoriteItems([...merged.values()])
}

function sortFavoriteItems(items) {
  return [...items].sort((left, right) => {
    const timeOrder = String(right.createdAt || '').localeCompare(String(left.createdAt || ''))
    return timeOrder || right.key.localeCompare(left.key)
  })
}

function isPending(item) {
  return pendingKeys.value.includes(item.key)
}

async function removeFavorite(item) {
  if (!item?.targetId || isPending(item)) return
  const state = collectionStates[item.targetType]
  const index = state.items.findIndex((candidate) => candidate.key === item.key)
  if (index < 0) return

  pendingKeys.value = [...pendingKeys.value, item.key]
  state.items.splice(index, 1)
  try {
    await deleteMajorCatalogFavorite({
      catalogYear: item.catalogYear,
      targetType: item.targetType,
      targetId: item.targetId
    })
    uni.showToast({ title: '已取消收藏', icon: 'none' })
    if (state.items.length === 0 && state.hasMore) {
      void loadFavorites(item.targetType)
    }
  } catch (error) {
    if (!state.items.some((candidate) => candidate.key === item.key)) {
      state.items = sortFavoriteItems([...state.items, item])
    }
    uni.showToast({ title: error?.detail || '取消收藏失败，请稍后重试', icon: 'none' })
  } finally {
    pendingKeys.value = pendingKeys.value.filter((key) => key !== item.key)
  }
}

function openFavorite(item) {
  if (!item.available) {
    uni.showToast({ title: '该条目属于历史目录，当前暂无可定位内容', icon: 'none' })
    return
  }

  const query = [
    ['catalogYear', item.catalogYear],
    ['schoolId', item.schoolId || (item.targetType === 'school' ? item.targetId : '')],
    ['programId', item.targetType === 'program' ? item.targetId : ''],
    ['source', 'favorites']
  ]
    .filter(([, value]) => value)
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&')

  uni.navigateTo({ url: `/pages-sub-data/major-catalog/index?${query}` })
}

function openMajorCatalog() {
  uni.navigateTo({ url: '/pages-sub-data/major-catalog/index?source=favorites' })
}

function handleScroll(event) {
  currentState.value.scrollTop = Math.max(0, Number(event?.detail?.scrollTop || 0))
}

function loadMore() {
  void loadFavorites(activeTab.value)
}

function refreshCurrent() {
  void loadFavorites(activeTab.value, { reset: true, silent: true })
}

function reloadCurrent() {
  void loadFavorites(activeTab.value, { reset: true })
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.reLaunch({ url: '/pages/home/index?tab=profile' })
    }
  })
}
</script>

<style scoped>
.major-favorites-page {
  width: 100%;
  height: 100vh;
  height: 100dvh;
  min-height: 0;
  overflow: hidden;
  box-sizing: border-box;
  background: var(--gyt-page-bg, #f5f3f7);
  display: flex;
  flex-direction: column;
}

.favorite-tabs {
  flex: 0 0 auto;
  margin: 14rpx 24rpx 20rpx;
  padding: 8rpx;
  border: 2rpx solid rgba(214, 222, 235, 0.72);
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.78);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8rpx;
}

.favorite-tab {
  height: 68rpx;
  min-height: 68rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  color: #7e899d;
  font-size: 25rpx;
  line-height: 68rpx;
  font-weight: 700;
}

.favorite-tab::after,
.favorite-remove::after,
.state-card button::after {
  border: 0;
}

.favorite-tab.active {
  background: #ffffff;
  color: var(--gyt-primary, #3478f6);
  box-shadow: 0 5rpx 16rpx rgba(28, 50, 86, 0.07);
}

.favorites-scroll {
  height: 0;
  min-height: 0;
  flex: 1 1 0;
}

.list-heading {
  padding: 6rpx 30rpx 16rpx;
  color: #162033;
  font-size: 27rpx;
  line-height: 1.35;
  font-weight: 750;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.list-heading-note {
  color: #98a2b3;
  font-size: 20rpx;
  font-weight: 600;
}

.favorite-list {
  padding: 0 24rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.favorite-card {
  min-height: 170rpx;
  padding: 24rpx 18rpx 24rpx 26rpx;
  border: 2rpx solid #e8edf5;
  border-radius: 28rpx;
  background: #ffffff;
  box-sizing: border-box;
  display: flex;
  align-items: stretch;
  gap: 18rpx;
}

.favorite-card:active {
  background: var(--gyt-primary-tint, #f4f8ff);
}

.favorite-card.unavailable {
  background: rgba(255, 255, 255, 0.72);
}

.favorite-card-main {
  min-width: 0;
  flex: 1;
}

.favorite-card-kicker,
.favorite-card-title-row,
.exam-code-row,
.favorite-card-meta {
  display: flex;
  align-items: center;
}

.favorite-card-kicker {
  min-height: 30rpx;
  gap: 10rpx;
  color: var(--gyt-primary, #3478f6);
  font-size: 20rpx;
  line-height: 1.25;
  font-weight: 750;
}

.history-tag {
  padding: 4rpx 10rpx;
  border-radius: 999rpx;
  background: #f1f3f6;
  color: #7b8494;
  font-size: 17rpx;
}

.favorite-card-title-row {
  min-width: 0;
  margin-top: 8rpx;
  flex-wrap: wrap;
  gap: 8rpx 10rpx;
}

.favorite-card-title {
  margin-top: 8rpx;
  color: #162033;
  font-size: 29rpx;
  line-height: 1.35;
  font-weight: 800;
  word-break: break-word;
}

.favorite-card-title-row .favorite-card-title {
  min-width: 0;
  margin-top: 0;
}

.exam-code-row {
  flex-wrap: wrap;
  gap: 7rpx;
}

.exam-code {
  padding: 5rpx 11rpx;
  border: 1rpx solid var(--gyt-primary-border, #d7e5ff);
  border-radius: 999rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  font-size: 18rpx;
  line-height: 1.2;
  font-weight: 800;
}

.favorite-card-code {
  margin-top: 5rpx;
  color: var(--gyt-primary, #3478f6);
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 800;
}

.favorite-card-context {
  margin-top: 8rpx;
  overflow: hidden;
  color: #647189;
  font-size: 22rpx;
  line-height: 1.4;
  font-weight: 650;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.favorite-card-meta {
  margin-top: 8rpx;
  flex-wrap: wrap;
  gap: 8rpx;
  color: #8a95a8;
  font-size: 21rpx;
  line-height: 1.35;
  font-weight: 650;
}

.favorite-card-actions {
  width: 78rpx;
  flex: 0 0 78rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
}

.favorite-remove {
  width: 62rpx;
  height: 62rpx;
  min-width: 62rpx;
  min-height: 62rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: transparent;
  box-shadow: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.favorite-remove image {
  display: block;
  width: 34rpx;
  height: 34rpx;
}

.favorite-remove[disabled] {
  opacity: 0.5;
}

.favorite-open {
  color: var(--gyt-primary, #3478f6);
  font-size: 21rpx;
  line-height: 1.3;
  font-weight: 750;
  white-space: nowrap;
}

.favorite-card.unavailable .favorite-open {
  color: #98a2b3;
}

.load-state {
  padding: 24rpx 24rpx calc(32rpx + env(safe-area-inset-bottom));
  color: #929daf;
  font-size: 20rpx;
  line-height: 1.4;
  font-weight: 650;
  text-align: center;
}

.state-card {
  min-height: 250rpx;
  margin: 10rpx 24rpx;
  padding: 34rpx;
  border: 2rpx solid #fde7b0;
  border-radius: 28rpx;
  background: #fff8eb;
  color: #916317;
  font-size: 24rpx;
  line-height: 1.65;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.state-card button {
  min-height: 58rpx;
  margin: 20rpx 0 0;
  padding: 0 24rpx;
  border: 0;
  border-radius: 18rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  font-size: 21rpx;
  line-height: 58rpx;
  font-weight: 750;
}
</style>
