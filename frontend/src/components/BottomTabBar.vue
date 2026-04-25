<template>
  <view class="tabbar">
    <view
      v-for="item in items"
      :key="item.key"
      class="tab-item"
      :class="{ active: modelValue === item.key }"
      @tap="$emit('update:modelValue', item.key)"
    >
      <text class="tab-label">{{ item.label }}</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: 'home'
  },
  items: {
    type: Array,
    default: () => []
  }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.tabbar {
  position: fixed;
  left: 24rpx;
  right: 24rpx;
  bottom: calc(env(safe-area-inset-bottom) + 18rpx);
  display: flex;
  padding: 12rpx 10rpx;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 16rpx 36rpx rgba(20, 31, 66, 0.08);
  z-index: 20;
}

.tab-item {
  flex: 1;
  padding: 16rpx 8rpx;
  border-radius: 20rpx;
  text-align: center;
}

.tab-item.active {
  background: #edf3ff;
}

.tab-label {
  color: #8a94a6;
  font-size: 22rpx;
  font-weight: 700;
}

.tab-item.active .tab-label {
  color: #2563eb;
}
</style>
