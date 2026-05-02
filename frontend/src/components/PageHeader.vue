<template>
  <view class="header">
    <view v-if="eyebrow" class="eyebrow">{{ eyebrow }}</view>
    <view class="title">{{ title }}</view>
    <view v-if="subtitle" class="subtitle">{{ subtitle }}</view>
  </view>
</template>

<script setup>
defineProps({
  eyebrow: {
    type: String,
    default: '港研通'
  },
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.header {
  padding: 12rpx 0 20rpx;
}

.eyebrow {
  color: var(--gyt-primary);
  font-size: 22rpx;
  font-weight: 800;
  letter-spacing: 1rpx;
}

.title {
  margin-top: 12rpx;
  color: #172033;
  font-size: 46rpx;
  font-weight: 900;
  line-height: 1.2;
}

.subtitle {
  margin-top: 14rpx;
  color: #667085;
  font-size: 25rpx;
  line-height: 1.6;
}
</style>
