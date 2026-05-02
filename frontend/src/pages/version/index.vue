<template>
  <view class="page version-page">
    <PageHeader eyebrow="版本选择" title="选择考试版本" subtitle="切换后，首页看板、科目入口和专项练习第三模块会同步变化。" />

    <view class="segment-wrap">
      <ExamSegment v-model="selectedCode" :options="examOptions" />
    </view>

    <view class="version-list">
      <view
        v-for="item in examOptions"
        :key="item.code"
        class="version-card"
        :class="{ active: selectedCode === item.code }"
        @tap="selectedCode = item.code"
      >
        <view class="card-code">{{ item.code }}</view>
        <view class="card-title">{{ item.title }}</view>
        <view class="card-subtitle">{{ item.subtitle }}</view>
        <view class="card-hero">{{ item.heroSubtitle }}</view>
      </view>
    </view>

    <button class="primary-button" @tap="confirm">进入科目选择</button>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import ExamSegment from '../../components/ExamSegment.vue'
import PageHeader from '../../components/PageHeader.vue'
import { EXAM_OPTIONS } from '../../utils/exam'

const examOptions = EXAM_OPTIONS
const selectedCode = ref(uni.getStorageSync('examCode') || 'Z001')

function confirm() {
  uni.setStorageSync('examCode', selectedCode.value)
  uni.navigateTo({ url: '/pages/subjects/index' })
}
</script>

<style scoped>
.segment-wrap {
  margin-top: 18rpx;
}

.version-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin: 22rpx 0 30rpx;
}

.version-card {
  padding: 30rpx;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.9);
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.05);
}

.version-card.active {
  border-color: var(--gyt-primary-shadow);
  background: #f7faff;
}

.card-code {
  color: var(--gyt-primary);
  font-size: 24rpx;
  font-weight: 900;
}

.card-title {
  margin-top: 12rpx;
  color: #172033;
  font-size: 34rpx;
  font-weight: 900;
}

.card-subtitle {
  margin-top: 12rpx;
  color: #475467;
  font-size: 24rpx;
  line-height: 1.6;
}

.card-hero {
  margin-top: 14rpx;
  padding: 16rpx 18rpx;
  border-radius: 22rpx;
  background: var(--gyt-primary-soft);
  color: #29417a;
  font-size: 22rpx;
  line-height: 1.6;
}
</style>
