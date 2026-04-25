<template>
  <view class="topbar">
    <view class="user-wrap">
      <view class="avatar">{{ avatarText }}</view>
      <view class="user-copy">
        <text class="name">{{ userName }}</text>
        <text class="status">{{ statusText }}</text>
      </view>
    </view>

    <picker class="picker" :range="examRange" :value="pickerIndex" @change="handleChange">
      <view class="picker-box">{{ currentLabel }}</view>
    </picker>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { EXAM_OPTIONS } from '../utils/exam'

const props = defineProps({
  examCode: {
    type: String,
    default: 'Z001'
  },
  userName: {
    type: String,
    default: '小钟'
  },
  statusText: {
    type: String,
    default: '今日学习状态：稳定推进'
  }
})

const emit = defineEmits(['changeExam'])

const examRange = EXAM_OPTIONS.map((item) => item.title)
const pickerIndex = computed(() => Math.max(0, EXAM_OPTIONS.findIndex((item) => item.code === props.examCode)))
const currentLabel = computed(() => EXAM_OPTIONS[pickerIndex.value]?.shortLabel || 'Z001')
const avatarText = computed(() => props.userName.slice(0, 1))

function handleChange(event) {
  const nextIndex = Number(event.detail.value)
  const nextExam = EXAM_OPTIONS[nextIndex]
  emit('changeExam', nextExam.code)
}
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.user-wrap {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #2563eb, #7aa2ff);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 800;
  box-shadow: 0 12rpx 24rpx rgba(37, 99, 235, 0.2);
}

.user-copy {
  display: flex;
  flex-direction: column;
}

.name {
  font-size: 28rpx;
  font-weight: 800;
  color: #172033;
}

.status {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
}

.picker-box {
  min-width: 152rpx;
  padding: 18rpx 20rpx;
  border-radius: 24rpx;
  border: 2rpx solid #e6ebf5;
  background: #ffffff;
  color: #2563eb;
  text-align: center;
  font-size: 24rpx;
  font-weight: 800;
}
</style>
