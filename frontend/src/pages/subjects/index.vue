<template>
  <view class="page subjects-page">
    <PageHeader eyebrow="科目入口" title="选择学习模块" :subtitle="`${exam.title}：请选择今天要练习的科目。`" />

    <view class="subject-list">
      <view v-for="subject in exam.subjects" :key="subject" class="subject-card" @tap="goPractice(subject)">
        <view class="subject-main">
          <view class="subject-icon">{{ getSubjectIcon(subject) }}</view>
          <view class="subject-copy">
            <view class="subject-title">{{ subject }}</view>
            <view class="subject-desc">{{ getSubjectMeta(subject) }}</view>
          </view>
        </view>
        <view class="subject-arrow">›</view>
      </view>
    </view>

    <button class="ghost-button" @tap="changeVersion">切换考试版本</button>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import PageHeader from '../../components/PageHeader.vue'
import { getExamOption } from '../../utils/exam'

const examCode = uni.getStorageSync('examCode') || 'Z001'
const exam = computed(() => getExamOption(examCode))

function getSubjectIcon(subject) {
  const iconMap = {
    中华文化: '📚',
    英语运用: '📝',
    逻辑推理: '🧠',
    数学基础: '📐'
  }
  return iconMap[subject] || '📘'
}

function getSubjectMeta(subject) {
  const scoreMap = {
    中华文化: '55 分，公共模块',
    英语运用: '50 分，公共模块',
    逻辑推理: '45 分，Z001 差异模块',
    数学基础: '45 分，Z002 差异模块'
  }
  return scoreMap[subject]
}

function goPractice(subject) {
  uni.setStorageSync('subject', subject)
  uni.navigateTo({ url: `/pages/practice/index?subject=${encodeURIComponent(subject)}` })
}

function changeVersion() {
  uni.navigateTo({ url: '/pages/version/index' })
}
</script>

<style scoped>
.subject-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin: 20rpx 0 28rpx;
}

.subject-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 28rpx;
  border-radius: 32rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.05);
}

.subject-main {
  display: flex;
  align-items: center;
  gap: 18rpx;
  flex: 1;
}

.subject-icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: 24rpx;
  background: var(--gyt-primary-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
}

.subject-copy {
  flex: 1;
}

.subject-title {
  color: #172033;
  font-size: 30rpx;
  font-weight: 800;
}

.subject-desc {
  margin-top: 10rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.5;
}

.subject-arrow {
  color: #98a2b3;
  font-size: 40rpx;
  font-weight: 700;
}
</style>
