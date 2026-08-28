<template>
  <view class="app-page-loading-state" :class="{ compact }" role="status" aria-live="polite">
    <text class="app-page-loading-state-copy">{{ message }}</text>
  </view>
</template>

<script setup>
defineProps({
  message: {
    type: String,
    required: true
  },
  compact: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.app-page-loading-state {
  box-sizing: border-box;
  width: 100%;
  min-height: 580rpx;
  padding: 220rpx 30rpx 72rpx;
  display: flex;
  align-items: flex-start;
  justify-content: center;
  text-align: center;
}

.app-page-loading-state-copy {
  color: #718198;
  font-size: 30rpx;
  line-height: 1.5;
  font-weight: 400;
  letter-spacing: 0;
}

.app-page-loading-state.compact {
  min-height: 250rpx;
  padding: 86rpx 24rpx 48rpx;
}

.app-page-loading-state.compact .app-page-loading-state-copy {
  font-size: 24rpx;
}
</style>
