<template>
  <view class="segment">
    <button
      v-for="item in options"
      :key="item.code"
      class="segment-btn"
      :class="{ active: modelValue === item.code }"
      @tap="emit('update:modelValue', item.code)"
    >
      {{ item.shortLabel }}
    </button>
  </view>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: 'Z001'
  },
  options: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue'])
</script>

<style scoped>
.segment {
  display: flex;
  padding: 8rpx;
  gap: 8rpx;
  border-radius: 28rpx;
  background: var(--gyt-primary-soft);
}

.segment-btn {
  flex: 1;
  min-height: 74rpx;
  border: 0;
  border-radius: 22rpx;
  background: transparent;
  color: #667085;
  font-size: 26rpx;
  font-weight: 700;
}

.segment-btn.active {
  background: #ffffff;
  color: var(--gyt-primary);
  box-shadow: 0 6rpx 16rpx var(--gyt-primary-shadow);
}
</style>
