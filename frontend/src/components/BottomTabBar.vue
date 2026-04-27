<template>
  <view class="tabbar">
    <view
      v-for="item in items"
      :key="item.key"
      class="tab-item"
      :class="{ active: modelValue === item.key }"
      @tap="$emit('update:modelValue', item.key)"
    >
      <text class="tab-icon">{{ item.icon }}</text>
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
  left: 26rpx;
  right: 26rpx;
  bottom: calc(env(safe-area-inset-bottom) + 28rpx);
  display: flex;
  gap: 14rpx;
  padding: 12rpx 16rpx;
  border-radius: 34rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid #edf2fb;
  box-shadow: 0 20rpx 52rpx rgba(25, 48, 89, 0.12);
  z-index: 20;
  backdrop-filter: blur(16rpx);
}

.tab-item {
  flex: 1;
  min-height: 82rpx;
  padding: 12rpx 8rpx;
  border-radius: 26rpx;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
}

.tab-item.active {
  background: #edf4ff;
}

.tab-icon {
  color: #98a2b3;
  font-size: 34rpx;
  line-height: 1;
  font-weight: 900;
}

.tab-label {
  color: #8a94a6;
  font-size: 25rpx;
  line-height: 1.2;
  font-weight: 800;
}

.tab-item.active .tab-icon {
  color: #1677ff;
}

.tab-item.active .tab-label {
  color: #1677ff;
}
</style>
