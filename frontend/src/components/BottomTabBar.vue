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
  left: 18rpx;
  right: 18rpx;
  bottom: calc(env(safe-area-inset-bottom) + 18rpx);
  display: flex;
  gap: 12rpx;
  padding: 16rpx;
  border-radius: 36rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 20rpx 46rpx rgba(20, 31, 66, 0.14);
  z-index: 20;
  backdrop-filter: blur(16rpx);
}

.tab-item {
  flex: 1;
  min-height: 106rpx;
  padding: 14rpx 8rpx;
  border-radius: 26rpx;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
}

.tab-item.active {
  background: linear-gradient(180deg, #2563eb, #4f82ff);
  box-shadow: 0 12rpx 26rpx rgba(37, 99, 235, 0.24);
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
  color: #ffffff;
}

.tab-item.active .tab-label {
  color: #ffffff;
}
</style>
