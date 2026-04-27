<template>
  <view class="page favorites-page">
    <view class="topbar">
      <view class="back-btn" @tap="goBack">‹</view>
      <view>
        <view class="app-name">港澳台考研刷题</view>
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
      <view class="summary-icon">▣</view>
      <view>
        <view class="summary-number">{{ filteredItems.length }}</view>
        <view class="summary-label">总收藏</view>
      </view>
    </view>

    <view class="list-head">
      <text class="list-title">我的收藏题目</text>
      <text class="list-note">按收藏时间展示</text>
    </view>

    <view v-if="filteredItems.length === 0" class="empty-card">
      当前没有匹配的收藏题目。后续做题时点击收藏，这里会自动归档。
    </view>

    <view v-else class="favorite-list">
      <view v-for="item in filteredItems" :key="item.id" class="favorite-card" @tap="openDetail(item)">
        <view class="tag-row">
          <text class="subject-tag">{{ item.subject }}</text>
          <text class="module-tag">{{ item.module }}</text>
        </view>
        <view class="stem">{{ item.stem }}</view>
        <view class="card-footer">
          <text class="saved-time">收藏于 {{ item.saved_at }}</text>
          <text class="view-link">查看 ›</text>
        </view>
      </view>
    </view>

    <view v-if="selectedItem" class="detail-mask" @tap="closeDetail">
      <view class="detail-panel" @tap.stop>
        <view class="detail-head">
          <view>
            <view class="detail-title">收藏题目</view>
            <view class="detail-sub">{{ selectedItem.subject }} / {{ selectedItem.module }}</view>
          </view>
          <view class="close-btn" @tap="closeDetail">×</view>
        </view>
        <view class="detail-stem">{{ selectedItem.stem }}</view>
        <view class="option-list">
          <view v-for="option in selectedOptions" :key="option.key" class="option-row">
            <text class="option-key">{{ option.key }}</text>
            <text class="option-text">{{ option.text }}</text>
          </view>
        </view>
        <view class="answer-box">
          <view class="answer-title">正确答案：{{ selectedItem.answer }}</view>
          <view class="answer-text">{{ selectedItem.explanation }}</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'

const keyword = ref('')
const activeSubject = ref('全部')
const selectedItem = ref(null)

const subjects = ['全部', '中华文化', '英语运用', '逻辑推理', '数学基础']

const favoriteItems = [
  {
    id: 1,
    subject: '中华文化',
    module: '中国哲学常识',
    stem: '“天人合一”是中国古代哲学的重要思想之一，下列哪一观点最能体现这一思想？',
    option_a: '人与自然相互隔绝',
    option_b: '自然规律与人的活动可以相互协调',
    option_c: '人应完全征服自然',
    option_d: '自然变化不影响人事',
    answer: 'B',
    explanation: '“天人合一”强调人与自然、宇宙秩序之间的协调统一。',
    saved_at: '2026-04-27 21:10'
  },
  {
    id: 2,
    subject: '英语运用',
    module: '阅读理解',
    stem: 'The manager insisted that the report ______ before the meeting.',
    option_a: 'submitted',
    option_b: 'be submitted',
    option_c: 'was submitted',
    option_d: 'submitting',
    answer: 'B',
    explanation: 'insist 表示“坚持要求”时，宾语从句常用虚拟语气 should do，should 可省略。',
    saved_at: '2026-04-26 18:35'
  },
  {
    id: 3,
    subject: '逻辑推理',
    module: '演绎推理',
    stem: '所有金属都导电，铜是金属，所以铜导电。以下哪项最能说明上述推理形式？',
    option_a: '归纳推理',
    option_b: '演绎推理',
    option_c: '类比推理',
    option_d: '因果推断',
    answer: 'B',
    explanation: '从一般命题推出个别结论，是典型演绎推理。',
    saved_at: '2026-04-25 16:02'
  },
  {
    id: 4,
    subject: '中华文化',
    module: '中国历史学常识',
    stem: '明清时期，科举制度在发展过程中出现了新的特点，下列说法正确的是？',
    option_a: '废除了八股取士',
    option_b: '科举完全脱离儒家经典',
    option_c: '八股文成为重要考试文体',
    option_d: '考试不再分级',
    answer: 'C',
    explanation: '明清时期八股文成为科举考试的重要文体，对士人学习产生深远影响。',
    saved_at: '2026-04-24 20:45'
  }
]

const filteredItems = computed(() => {
  const word = keyword.value.trim().toLowerCase()
  return favoriteItems.filter((item) => {
    const subjectMatched = activeSubject.value === '全部' || item.subject === activeSubject.value
    const keywordMatched =
      !word ||
      item.stem.toLowerCase().includes(word) ||
      item.subject.toLowerCase().includes(word) ||
      item.module.toLowerCase().includes(word)
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
  ]
})

function openDetail(item) {
  selectedItem.value = item
}

function closeDetail() {
  selectedItem.value = null
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
  background: linear-gradient(180deg, #fbfcff 0%, #f3f7fc 100%);
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
.close-btn {
  width: 60rpx;
  height: 60rpx;
  border-radius: 22rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.back-btn {
  background: #ffffff;
  color: #101828;
  font-size: 44rpx;
  font-weight: 800;
  box-shadow: 0 10rpx 26rpx rgba(25, 48, 89, 0.06);
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
  background: #1677ff;
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
  background: #edf4ff;
  color: #1677ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
  font-weight: 900;
}

.summary-number {
  color: #1677ff;
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

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-bottom: 14rpx;
}

.subject-tag,
.module-tag {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  font-size: 21rpx;
  font-weight: 800;
}

.subject-tag {
  color: #1677ff;
  background: #edf4ff;
}

.module-tag {
  color: #667085;
  background: #f3f6fb;
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
  color: #1677ff;
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

.close-btn {
  background: #f3f6fb;
  color: #667085;
  font-size: 34rpx;
  font-weight: 900;
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
  background: #f8fbff;
  border: 2rpx solid #edf2fb;
  display: flex;
  gap: 16rpx;
}

.option-key {
  width: 44rpx;
  height: 44rpx;
  border-radius: 16rpx;
  background: #edf4ff;
  color: #1677ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  font-weight: 900;
  flex-shrink: 0;
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
  background: #f4f8ff;
  border: 2rpx dashed #c8d8ff;
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
