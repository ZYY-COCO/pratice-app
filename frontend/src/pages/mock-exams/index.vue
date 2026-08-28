<template>
  <view class="page mock-exam-page" :style="pageInlineStyle">
    <AppPageHeader title="模拟卷" fixed @back="goBack">
      <template #right>
        <button class="random-paper-button" hover-class="none" @tap.stop="startRandomPaper">
          随机组卷
        </button>
      </template>
    </AppPageHeader>

    <view class="paper-section-heading">
      <text class="paper-section-title">已发布试卷</text>
      <text class="paper-section-count">{{ papers.length }} 套</text>
    </view>

    <AppPageLoadingState v-if="loading" message="正在整理模拟卷..." />

    <view v-else-if="error" class="paper-state-card paper-state-error">
      <text>{{ error }}</text>
      <button @tap="loadPapers">重新加载</button>
    </view>

    <view v-else-if="papers.length === 0" class="paper-empty-wrap">
      <AppEmptyState label="暂无已发布模拟卷" />
    </view>

    <view v-else class="paper-list">
      <button
        v-for="(paper, index) in papers"
        :key="paper.id"
        class="paper-card"
        hover-class="paper-card-pressed"
        @tap="startFixedPaper(paper)"
      >
        <view class="paper-index">{{ String(index + 1).padStart(2, '0') }}</view>
        <view class="paper-card-main">
          <view class="paper-title-row">
            <text class="paper-title">{{ paper.title }}</text>
            <text class="paper-version">V{{ paper.version || 1 }}</text>
          </view>
          <text v-if="paper.description" class="paper-description">{{ paper.description }}</text>
          <view class="paper-meta-row">
            <text>{{ paper.question_count || 55 }} 题</text>
            <text>{{ paper.total_score || 105 }} 分</text>
            <text>{{ paper.duration_minutes || 120 }} 分钟</text>
          </view>
        </view>
        <text class="paper-arrow">›</text>
      </button>
    </view>

    <!-- #ifdef H5 -->
    <IcpFooter />
    <!-- #endif -->
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { fetchMockExamPapers } from '../../api/mockExams'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import IcpFooter from '../../components/IcpFooter.vue'
import { buildMpPageSafeStyle } from '../../utils/mpSafeLayout'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const examCode = ref(uni.getStorageSync('examCode') || 'Z001')
const papers = ref([])
const loading = ref(true)
const error = ref('')
const mpLayoutStyle = ref(buildMpPageSafeStyle())
const pageInlineStyle = computed(() => [
  buildThemeStyle(getStoredThemeKey()),
  mpLayoutStyle.value
].filter(Boolean).join(';'))
const thirdSubject = computed(() => (examCode.value === 'Z002' ? '数学基础' : '逻辑推理'))

onLoad((options) => {
  const routeExamCode = String(options?.exam_code || '')
  if (routeExamCode === 'Z001' || routeExamCode === 'Z002') {
    examCode.value = routeExamCode
    uni.setStorageSync('examCode', routeExamCode)
  }
})

onShow(() => {
  mpLayoutStyle.value = buildMpPageSafeStyle()
  loadPapers()
})

async function loadPapers() {
  loading.value = true
  error.value = ''
  try {
    const response = await fetchMockExamPapers({ exam_code: examCode.value })
    papers.value = Array.isArray(response?.items) ? response.items : []
  } catch (err) {
    papers.value = []
    error.value = err?.detail || '模拟卷读取失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

function startRandomPaper() {
  uni.setStorageSync('subject', thirdSubject.value)
  uni.navigateTo({
    url: `/pages/practice/index?mock_exam=1&exam_code=${encodeURIComponent(examCode.value)}`
  })
}

function startFixedPaper(paper) {
  if (!paper?.id) return
  uni.setStorageSync('subject', thirdSubject.value)
  uni.navigateTo({
    url: `/pages/practice/index?mock_paper_id=${encodeURIComponent(paper.id)}&exam_code=${encodeURIComponent(paper.exam_code || examCode.value)}`
  })
}

function returnToPracticeHome() {
  uni.reLaunch({
    url: '/pages/home/index?tab=home',
    fail() {
      uni.redirectTo({ url: '/pages/home/index?tab=home' })
    }
  })
}

function goBack() {
  returnToPracticeHome()
}
</script>

<style scoped>
.mock-exam-page {
  box-sizing: border-box;
  min-height: 100vh;
  padding: 0 28rpx calc(env(safe-area-inset-bottom) + 64rpx);
  background: var(--gyt-page-bg, #f7f8fc);
  color: #172238;
}

.mock-exam-page :deep(.app-page-header) {
  grid-template-columns: 164rpx minmax(0, 1fr) 164rpx;
}

.mock-exam-page :deep(.app-page-header-side) {
  width: 164rpx;
  min-width: 164rpx;
}

.random-paper-button {
  position: relative;
  box-sizing: border-box;
  width: 164rpx;
  min-width: 164rpx;
  height: 64rpx;
  min-height: 64rpx;
  margin: 0;
  padding: 0 24rpx;
  border: 0;
  border-radius: 22rpx;
  background: var(--gyt-primary-soft, #eaf2ff);
  color: var(--gyt-primary, #3478f6);
  font-size: 23rpx;
  line-height: 1.2;
  font-weight: 700;
  transform: none;
  flex: 0 0 164rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  align-self: center;
  white-space: nowrap;
}

.random-paper-button::after {
  display: none;
}

.paper-card::after,
.paper-state-card button::after {
  border: 0;
}

.paper-card-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.paper-section-heading {
  margin: 38rpx 4rpx 18rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.paper-section-title {
  font-size: 29rpx;
  line-height: 1.3;
  font-weight: 800;
}

.paper-section-count {
  color: #8994a7;
  font-size: 22rpx;
}

.paper-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.paper-card {
  box-sizing: border-box;
  width: 100%;
  min-height: 154rpx;
  margin: 0;
  padding: 26rpx 24rpx;
  border: 1rpx solid #e5eaf3;
  border-radius: 34rpx;
  background: #ffffff;
  color: inherit;
  display: flex;
  align-items: center;
  gap: 22rpx;
  text-align: left;
  box-shadow: 0 12rpx 28rpx rgba(28, 42, 78, 0.04);
}

.paper-card-pressed {
  background: var(--gyt-primary-tint, #f4f8ff);
}

.paper-index {
  width: 74rpx;
  height: 74rpx;
  flex: 0 0 74rpx;
  border-radius: 25rpx;
  background: var(--gyt-primary-soft, #eaf2ff);
  color: var(--gyt-primary, #3478f6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 25rpx;
  font-weight: 800;
}

.paper-card-main {
  flex: 1 1 auto;
}

.paper-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.paper-title {
  min-width: 0;
  overflow: hidden;
  color: #172238;
  font-size: 29rpx;
  line-height: 1.35;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.paper-version {
  padding: 4rpx 10rpx;
  border-radius: 999rpx;
  background: #f1f4f8;
  color: #7d899d;
  font-size: 17rpx;
  line-height: 1.2;
}

.paper-description {
  margin-top: 7rpx;
  overflow: hidden;
  color: #7b879b;
  font-size: 21rpx;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.paper-meta-row {
  margin-top: 13rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
  color: #6d7a91;
  font-size: 20rpx;
}

.paper-meta-row text:not(:last-child)::after {
  content: '·';
  margin-left: 10rpx;
  color: #c5ccd7;
}

.paper-arrow {
  flex: 0 0 auto;
  color: #bcc5d1;
  font-size: 46rpx;
  line-height: 1;
  font-weight: 300;
}

.paper-state-card {
  margin-top: 28rpx;
  padding: 28rpx;
  border: 1rpx solid #e6ebf4;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.88);
}

.paper-state-card,
.paper-empty-wrap {
  color: #76839a;
  font-size: 24rpx;
  text-align: center;
}

.paper-state-card button {
  width: auto;
  margin: 22rpx auto 0;
  padding: 0 28rpx;
  border: 0;
  border-radius: 24rpx;
  background: var(--gyt-primary-soft, #eaf2ff);
  color: var(--gyt-primary, #3478f6);
  font-size: 22rpx;
  line-height: 66rpx;
  font-weight: 700;
}
</style>
