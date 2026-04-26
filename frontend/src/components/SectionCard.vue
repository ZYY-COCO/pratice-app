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
  padding: 30rpx;
  border-radius: 36rpx;
  background: #ffffff;
  border: 2rpx solid rgba(230, 235, 245, 0.96);
  box-shadow: 0 18rpx 42rpx rgba(20, 31, 66, 0.06);
}

.head {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 18rpx;
}

.title {
  font-size: 30rpx;
  font-weight: 900;
  color: #172033;
}

.subtitle {
  margin-top: 10rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.55;
}

.right {
  color: #667085;
  font-size: 22rpx;
}
</style>
