<template>
  <view class="mentor-page-header">
    <button class="mentor-page-back" aria-label="返回" @tap="emit('back')">
      <image src="/static/ui-icons/back.svg" mode="aspectFit" />
    </button>
    <view class="mentor-page-heading">
      <view class="mentor-page-title">{{ title }}</view>
      <view v-if="subtitle" class="mentor-page-subtitle">{{ subtitle }}</view>
    </view>
    <view class="mentor-page-header-side">
      <slot name="right">
        <view class="mentor-page-header-placeholder"></view>
      </slot>
    </view>
  </view>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['back'])
</script>

<style scoped>
.mentor-page-header {
  position: relative;
  z-index: 2;
  min-height: calc(env(safe-area-inset-top) + 108rpx);
  padding: env(safe-area-inset-top) 28rpx 0;
  box-sizing: border-box;
  border-bottom: 2rpx solid rgba(215, 229, 255, 0.82);
  background: rgba(250, 252, 255, 0.94);
  display: grid;
  grid-template-columns: 66rpx minmax(0, 1fr) 66rpx;
  align-items: center;
  gap: 14rpx;
  -webkit-backdrop-filter: blur(18px) saturate(118%);
  backdrop-filter: blur(18px) saturate(118%);
}

.mentor-page-back {
  width: 66rpx;
  height: 66rpx;
  min-width: 66rpx;
  min-height: 66rpx;
  margin: 0;
  padding: 16rpx;
  border: 0;
  border-radius: 50%;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 18rpx rgba(30, 55, 100, 0.08);
}

.mentor-page-back::after {
  border: 0;
}

.mentor-page-back:active {
  transform: scale(0.96);
}

.mentor-page-back image {
  width: 100%;
  height: 100%;
}

.mentor-page-heading {
  min-width: 0;
  text-align: center;
}

.mentor-page-title {
  color: #172033;
  overflow: hidden;
  font-size: 30rpx;
  line-height: 1.25;
  font-weight: 900;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mentor-page-subtitle {
  margin-top: 4rpx;
  color: #728198;
  overflow: hidden;
  font-size: 18rpx;
  line-height: 1.2;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mentor-page-header-side,
.mentor-page-header-placeholder {
  width: 66rpx;
  min-width: 66rpx;
  min-height: 66rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
