<template>
  <view class="section-card">
    <view v-if="title || rightText" class="head">
      <view>
        <view v-if="title" class="title">{{ title }}</view>
        <view v-if="subtitle" class="subtitle">{{ subtitle }}</view>
      </view>
      <view v-if="rightText" class="right">{{ rightText }}</view>
    </view>
    <slot />
  </view>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  },
  rightText: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.section-card {
  padding: 28rpx;
  border-radius: 30rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.05);
}

.head {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 18rpx;
}

.title {
  font-size: 28rpx;
  font-weight: 800;
  color: #172033;
}

.subtitle {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
}

.right {
  color: #667085;
  font-size: 22rpx;
}
</style>
