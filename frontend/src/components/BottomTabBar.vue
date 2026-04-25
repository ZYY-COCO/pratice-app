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
  left: 20rpx;
  right: 20rpx;
  bottom: calc(env(safe-area-inset-bottom) + 16rpx);
  display: flex;
  padding: 14rpx 12rpx;
  border-radius: 34rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 18rpx 44rpx rgba(20, 31, 66, 0.12);
  z-index: 20;
  backdrop-filter: blur(16rpx);
}

.tab-item {
  flex: 1;
  min-height: 82rpx;
  padding: 10rpx 6rpx;
  border-radius: 24rpx;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
}

.tab-item.active {
  background: linear-gradient(180deg, #edf3ff, #e7efff);
}

.tab-icon {
  color: #98a2b3;
  font-size: 30rpx;
  line-height: 1;
  font-weight: 900;
}

.tab-label {
  color: #8a94a6;
  font-size: 24rpx;
  line-height: 1.2;
  font-weight: 800;
}

.tab-item.active .tab-icon {
  color: #2563eb;
}

.tab-item.active .tab-label {
  color: #2563eb;
}
</style>
