<template>
  <view class="option" :class="optionClass" @tap="$emit('select', option.key)">
    <view class="letter">{{ option.key }}</view>
    <view class="text">{{ option.text }}</view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  option: {
    type: Object,
    required: true
  },
  selectedKey: {
    type: String,
    default: ''
  },
  submitted: {
    type: Boolean,
    default: false
  },
  correctKey: {
    type: String,
    default: ''
  }
})

defineEmits(['select'])

const optionClass = computed(() => {
  if (!props.submitted) {
    return props.selectedKey === props.option.key ? 'selected' : ''
  }

  if (props.option.key === props.correctKey) {
    return 'correct'
  }

  if (props.option.key === props.selectedKey && props.selectedKey !== props.correctKey) {
    return 'wrong'
  }

  return ''
})
</script>

<style scoped>
.option {
  display: flex;
  gap: 20rpx;
  align-items: flex-start;
  min-height: 102rpx;
  padding: 28rpx 26rpx;
  border-radius: 30rpx;
  border: 2rpx solid #e6ebf5;
  background: #ffffff;
  box-shadow: 0 10rpx 24rpx rgba(20, 31, 66, 0.04);
}

.option.selected {
  border-color: #2563eb;
  background: #f4f8ff;
}

.option.correct {
  border-color: rgba(22, 163, 74, 0.4);
  background: rgba(22, 163, 74, 0.08);
}

.option.wrong {
  border-color: rgba(239, 68, 68, 0.4);
  background: rgba(239, 68, 68, 0.08);
}

.letter {
  width: 58rpx;
  height: 58rpx;
  border-radius: 20rpx;
  background: #eef3ff;
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 900;
  flex-shrink: 0;
  margin-top: 2rpx;
}

.text {
  flex: 1;
  color: #172033;
  font-size: 30rpx;
  line-height: 1.6;
  font-weight: 700;
}
</style>
