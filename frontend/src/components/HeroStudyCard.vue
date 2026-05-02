<template>
  <view class="hero-card">
    <view class="tag">{{ tag }}</view>
    <view class="title">{{ title }}</view>
    <view class="subtitle">{{ subtitle }}</view>
    <button class="cta" @tap="$emit('action')">{{ actionText }}</button>
  </view>
</template>

<script setup>
defineEmits(['action'])

defineProps({
  tag: {
    type: String,
    default: '学习看板'
  },
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  },
  actionText: {
    type: String,
    default: '生成最新诊断报告'
  }
})
</script>

<style scoped>
.hero-card {
  padding: 34rpx;
  border-radius: 34rpx;
  background: var(--gyt-primary-gradient);
  color: #ffffff;
  box-shadow: 0 20rpx 40rpx var(--gyt-primary-shadow);
}

.tag {
  display: inline-flex;
  align-items: center;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.18);
  border: 2rpx solid rgba(255, 255, 255, 0.2);
  font-size: 22rpx;
  margin-bottom: 22rpx;
}

.title {
  font-size: 42rpx;
  line-height: 1.24;
  font-weight: 900;
}

.subtitle {
  margin-top: 16rpx;
  color: rgba(255, 255, 255, 0.92);
  font-size: 25rpx;
  line-height: 1.7;
}

.cta {
  margin-top: 24rpx;
  width: 100%;
  min-height: 86rpx;
  border: 0;
  border-radius: 24rpx;
  background: #ffffff;
  color: var(--gyt-primary);
  font-size: 28rpx;
  font-weight: 800;
}
</style>
