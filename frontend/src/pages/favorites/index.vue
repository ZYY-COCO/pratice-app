<template>
  <view class="page favorites-page" :style="pageInlineStyle">
    <view class="topbar">
      <view class="back-btn" @tap="goBack">
        <image class="back-icon" src="/static/ui-icons/back.svg" mode="aspectFit" />
      </view>
      <view>
        <view class="app-name">港研通</view>
        <view class="page-title">收藏夹</view>
      </view>
      <view class="top-placeholder"></view>
    </view>

    <view class="search-card">
      <text class="search-icon">⌕</text>
      <input
        v-model="keyword"
        class="search-input"
        confirm-type="search"
        placeholder="搜索收藏题目"
        placeholder-class="placeholder"
      />
    </view>

    <scroll-view scroll-x class="subject-scroll" show-scrollbar="false">
      <view class="subject-row">
        <button
          v-for="item in subjects"
          :key="item"
          class="subject-chip"
          :class="{ active: activeSubject === item }"
          @tap="activeSubject = item"
        >
          {{ item }}
        </button>
      </view>
    </scroll-view>

    <view class="summary-card">
      <view class="summary-icon"><FavoriteIcon /></view>
      <view>
        <view class="summary-number">{{ favoriteCards.length }}</view>
        <view class="summary-label">总收藏</view>
      </view>
    </view>

    <view class="list-head">
      <text class="list-title">我的收藏题目</text>
      <text class="list-note">按收藏时间展示</text>
    </view>

    <view v-if="loading" class="empty-card">正在同步你的收藏题目...</view>
    <view v-else-if="error" class="empty-card warning">{{ error }}</view>
    <view v-else-if="filteredItems.length === 0" class="empty-card">
      当前没有匹配的收藏题目。刷题时点亮五角星，这里会自动归档。
    </view>

    <view v-else class="favorite-list">
      <view v-for="item in filteredItems" :key="item.favorite_id" class="favorite-card" @tap="openDetail(item)">
        <view class="tag-row">
          <text class="subject-tag">{{ item.subject }}</text>
          <text class="module-tag">{{ item.module }}</text>
          <text v-if="item.sourceLabel" class="source-origin-tag">{{ item.sourceLabel }}</text>
        </view>
        <MathText class="stem" :value="item.stem" />
        <view class="card-footer">
          <text class="saved-time">收藏于 {{ formatTime(item.saved_at) }}</text>
          <text class="view-link">查看 ›</text>
        </view>
      </view>
    </view>

    <view v-if="selectedItem" class="detail-mask" @tap="closeDetail">
      <view class="detail-panel" @tap.stop>
        <view class="detail-head">
          <view class="detail-copy">
            <view class="detail-title">收藏题目</view>
            <view class="detail-sub">{{ selectedItem.subject }} / {{ selectedItem.module }}</view>
            <view v-if="selectedItem.sourceLabel" class="detail-source-tag">{{ selectedItem.sourceLabel }}</view>
          </view>
          <view class="detail-actions">
            <button
              class="star-btn active"
              :disabled="toggling"
              aria-label="取消收藏"
              @tap="toggleSelectedFavorite"
            >
              <FavoriteIcon />
            </button>
            <button class="close-btn" aria-label="关闭" @tap="closeDetail"><CloseIcon /></button>
          </view>
        </view>

        <MathText class="detail-stem" :value="selectedItem.stem" />
        <view class="option-list">
          <view
            v-for="option in selectedOptions"
            :key="option.key"
            class="option-row"
            :class="{ correct: option.key === selectedItem.answer }"
          >
            <text class="option-key">{{ option.key }}</text>
            <MathText class="option-text" :value="option.text" />
          </view>
        </view>
        <view class="answer-box">
          <view class="answer-title">正确答案：{{ selectedItem.answer }}</view>
          <MathText class="answer-text" :value="selectedItem.explanation || '暂无解析'" />
        </view>
      </view>
    </view>

    <!-- #ifdef H5 -->
    <IcpFooter />
    <!-- #endif -->
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { fetchFavorites, toggleFavorite } from '../../api/favorites'
import CloseIcon from '../../components/CloseIcon.vue'
import FavoriteIcon from '../../components/FavoriteIcon.vue'
import IcpFooter from '../../components/IcpFooter.vue'
import MathText from '../../components/MathText.vue'
import { confirmFavoriteRemoval } from '../../utils/favorites'
import { buildMpPageSafeStyle } from '../../utils/mpSafeLayout'
import { getQuestionSourceLabel } from '../../utils/questionSource'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const mpLayoutStyle = ref(buildMpPageSafeStyle())
const pageInlineStyle = computed(() => [themeInlineStyle, mpLayoutStyle.value].filter(Boolean).join(';'))
const keyword = ref('')
const activeSubject = ref('全部')
const selectedItem = ref(null)
const favoriteRows = ref([])
const loading = ref(false)
const error = ref('')
const toggling = ref(false)

const subjects = ['全部', '中华文化', '英语运用', '逻辑推理', '数学基础']

const favoriteCards = computed(() =>
  favoriteRows.value
    .map((row) => {
      const question = row.question || {}
      return {
        favorite_id: row.id,
        question_id: row.question_id,
        saved_at: row.created_at,
        subject: question.subject || '',
        module: question.module || '',
        submodule: question.submodule || '',
        stem: question.stem || '题目内容暂不可用',
        option_a: question.option_a,
        option_b: question.option_b,
        option_c: question.option_c,
        option_d: question.option_d,
        answer: question.answer || '',
        explanation: question.explanation || '',
        source_type: question.source_type || '',
        sourceLabel: getQuestionSourceLabel(question)
      }
    })
    .filter((item) => item.question_id)
)

const filteredItems = computed(() => {
  const word = keyword.value.trim().toLowerCase()
  return favoriteCards.value.filter((item) => {
    const subjectMatched = activeSubject.value === '全部' || item.subject === activeSubject.value
    const keywordMatched =
      !word ||
      item.stem.toLowerCase().includes(word) ||
      item.subject.toLowerCase().includes(word) ||
      item.module.toLowerCase().includes(word) ||
      item.submodule.toLowerCase().includes(word)
    return subjectMatched && keywordMatched
  })
})

const selectedOptions = computed(() => {
  const item = selectedItem.value
  if (!item) return []
  return [
    { key: 'A', text: item.option_a },
    { key: 'B', text: item.option_b },
    { key: 'C', text: item.option_c },
    { key: 'D', text: item.option_d }
  ].filter((option) => option.text)
})

onShow(() => {
  mpLayoutStyle.value = buildMpPageSafeStyle()
  loadFavorites()
})

async function loadFavorites() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetchFavorites({ limit: 200 })
    favoriteRows.value = response.items || []
  } catch (err) {
    error.value = err?.detail || '收藏夹读取失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function openDetail(item) {
  selectedItem.value = item
}

function closeDetail() {
  selectedItem.value = null
}

async function toggleSelectedFavorite() {
  if (!selectedItem.value?.question_id || toggling.value) return
  const questionId = selectedItem.value.question_id
  toggling.value = true
  try {
    const confirmed = await confirmFavoriteRemoval()
    if (!confirmed) return

    const result = await toggleFavorite(questionId)
    if (!result.is_favorited) {
      favoriteRows.value = favoriteRows.value.filter((row) => row.question_id !== questionId)
      selectedItem.value = null
      uni.showToast({ title: '已取消收藏', icon: 'none' })
    }
  } catch (err) {
    uni.showToast({ title: err?.detail || '收藏状态更新失败', icon: 'none' })
  } finally {
    toggling.value = false
  }
}

function formatTime(value) {
  if (!value) return '暂无时间'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 16)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function goBack() {
  uni.navigateBack({
    fail() {
      uni.redirectTo({ url: '/pages/home/index' })
    }
  })
}
</script>

<style scoped>
.favorites-page {
  min-height: 100vh;
  min-height: 100dvh;
  padding: calc(env(safe-area-inset-top) + 18rpx) 24rpx calc(env(safe-area-inset-bottom) + 44rpx);
  background: var(--gyt-page-bg);
  box-sizing: border-box;
  overflow-x: hidden;
}

.topbar {
  display: grid;
  grid-template-columns: 64rpx 1fr 64rpx;
  align-items: center;
  gap: 12rpx;
  margin-bottom: 24rpx;
}

.back-btn,
.top-placeholder,
.close-btn,
.star-btn {
  width: 60rpx;
  height: 60rpx;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-btn {
  background: #ffffff;
  box-shadow: 0 10rpx 26rpx rgba(25, 48, 89, 0.06);
}

/* #ifdef MP-WEIXIN */
.favorites-page {
  padding-top: var(--mp-page-content-top, 96px);
}

.topbar {
  min-height: var(--mp-page-header-height, 40px);
}
/* #endif */

.back-icon {
  width: 28rpx;
  height: 28rpx;
  display: block;
}

.app-name {
  text-align: center;
  color: #667085;
  font-size: 22rpx;
  font-weight: 700;
}

.page-title {
  margin-top: 4rpx;
  text-align: center;
  color: #101828;
  font-size: 44rpx;
  line-height: 1.15;
  font-weight: 900;
}

.search-card {
  height: 76rpx;
  padding: 0 24rpx;
  border-radius: 28rpx;
  background: #ffffff;
  border: 2rpx solid #edf2fb;
  box-shadow: 0 14rpx 34rpx rgba(25, 48, 89, 0.06);
  display: flex;
  align-items: center;
  gap: 14rpx;
  margin-bottom: 20rpx;
}

.search-icon {
  color: #98a2b3;
  font-size: 30rpx;
}

.search-input {
  flex: 1;
  height: 72rpx;
  color: #101828;
  font-size: 26rpx;
}

.placeholder {
  color: #a7b0c0;
}

.subject-scroll {
  width: 100%;
  white-space: nowrap;
  margin-bottom: 20rpx;
}

.subject-row {
  display: inline-flex;
  gap: 12rpx;
  padding-right: 8rpx;
}

.subject-chip {
  min-width: 112rpx;
  height: 60rpx;
  margin: 0;
  padding: 0 24rpx;
  border: 0;
  border-radius: 22rpx;
  background: #eef3fb;
  color: #667085;
  font-size: 24rpx;
  font-weight: 800;
  line-height: 60rpx;
}

.subject-chip.active {
  background: var(--gyt-primary);
  color: #ffffff;
}

.summary-card {
  padding: 26rpx 30rpx;
  border-radius: 30rpx;
  background: #ffffff;
  border: 2rpx solid #edf2fb;
  box-shadow: 0 16rpx 38rpx rgba(25, 48, 89, 0.07);
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-bottom: 28rpx;
}

.summary-icon {
  width: 68rpx;
  height: 68rpx;
  border-radius: 22rpx;
  background: #fff8d9;
  color: #f5b700;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  font-weight: 900;
}

.summary-number {
  color: var(--gyt-primary);
  font-size: 44rpx;
  line-height: 1;
  font-weight: 900;
}

.summary-label {
  margin-top: 8rpx;
  color: #8a95a8;
  font-size: 24rpx;
  font-weight: 700;
}

.list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.list-title {
  color: #101828;
  font-size: 30rpx;
  font-weight: 900;
}

.list-note {
  color: #98a2b3;
  font-size: 24rpx;
  font-weight: 700;
}

.favorite-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.favorite-card,
.empty-card {
  padding: 26rpx 26rpx;
  border-radius: 30rpx;
  background: #ffffff;
  border: 2rpx solid #edf2fb;
  box-shadow: 0 14rpx 34rpx rgba(25, 48, 89, 0.06);
}

.empty-card {
  color: #667085;
  font-size: 26rpx;
  line-height: 1.7;
}

.empty-card.warning {
  color: #9a6510;
  background: #fff8eb;
  border-color: #fde7b0;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-bottom: 14rpx;
}

.subject-tag,
.module-tag,
.source-origin-tag,
.detail-source-tag {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  font-size: 21rpx;
  font-weight: 800;
}

.subject-tag {
  color: var(--gyt-primary);
  background: var(--gyt-primary-soft);
}

.module-tag {
  color: #667085;
  background: #f3f6fb;
}

.source-origin-tag,
.detail-source-tag {
  color: #0f766e;
  background: #e6fffb;
  border: 1rpx solid rgba(20, 184, 166, 0.18);
}

.stem {
  color: #1d2939;
  font-size: 28rpx;
  line-height: 1.55;
  font-weight: 800;
}

.card-footer {
  margin-top: 18rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.saved-time {
  color: #98a2b3;
  font-size: 22rpx;
  font-weight: 700;
}

.view-link {
  color: var(--gyt-primary);
  font-size: 24rpx;
  font-weight: 900;
  white-space: nowrap;
}

.detail-mask {
  position: fixed;
  inset: 0;
  z-index: 20;
  padding: 80rpx 24rpx 32rpx;
  background: rgba(15, 23, 42, 0.35);
  display: flex;
  align-items: flex-end;
  box-sizing: border-box;
}

.detail-panel {
  width: 100%;
  max-height: 82vh;
  padding: 30rpx;
  border-radius: 34rpx;
  background: #ffffff;
  box-shadow: 0 -12rpx 50rpx rgba(15, 23, 42, 0.16);
  overflow-y: auto;
}

.detail-head {
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.detail-copy {
  flex: 1;
  min-width: 0;
}

.detail-actions {
  display: flex;
  gap: 10rpx;
  flex-shrink: 0;
}

.detail-title {
  color: #101828;
  font-size: 32rpx;
  font-weight: 900;
}

.detail-sub {
  margin-top: 8rpx;
  color: #667085;
  font-size: 24rpx;
  font-weight: 700;
}

.detail-source-tag {
  display: inline-flex;
  margin-top: 12rpx;
}

.close-btn,
.star-btn {
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  color: #667085;
  font-size: 34rpx;
  font-weight: 900;
  line-height: 60rpx;
}

.star-btn.active {
  background: transparent;
  color: #f5b700;
}

.close-btn::after,
.star-btn::after {
  border: 0;
}

.star-btn[disabled] {
  opacity: 0.55;
}

.detail-stem {
  color: #101828;
  font-size: 31rpx;
  line-height: 1.65;
  font-weight: 900;
  margin-bottom: 20rpx;
}

.option-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.option-row {
  padding: 20rpx;
  border-radius: 22rpx;
  background: var(--gyt-primary-tint);
  border: 2rpx solid #edf2fb;
  display: flex;
  gap: 16rpx;
}

.option-row.correct {
  border-color: rgba(22, 163, 74, 0.42);
  background: rgba(22, 163, 74, 0.1);
}

.option-key {
  width: 44rpx;
  height: 44rpx;
  border-radius: 16rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 900;
  flex-shrink: 0;
}

.option-row.correct .option-key {
  background: #dcfce7;
  color: #16a34a;
}

.option-text {
  flex: 1;
  color: #344054;
  font-size: 26rpx;
  line-height: 1.55;
  font-weight: 700;
}

.answer-box {
  margin-top: 20rpx;
  padding: 22rpx;
  border-radius: 24rpx;
  background: var(--gyt-primary-tint);
  border: 2rpx dashed var(--gyt-primary-border);
}

.answer-title {
  color: #101828;
  font-size: 26rpx;
  font-weight: 900;
}

.answer-text {
  margin-top: 10rpx;
  color: #4b5f80;
  font-size: 25rpx;
  line-height: 1.7;
}
</style>
