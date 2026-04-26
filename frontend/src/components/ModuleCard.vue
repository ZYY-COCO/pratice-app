<template>
  <view class="module-card" @tap="$emit('select', item.key)">
    <view class="module-head">
      <view class="icon">{{ item.icon }}</view>
      <view class="number">{{ paddedIndex }}</view>
    </view>
    <view class="content">
      <view class="title">{{ item.title }}</view>
      <view class="desc">{{ item.desc }}</view>
      <view class="entry-text">进入练习</view>
    </view>
    <view class="arrow">›</view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

defineEmits(['select'])

const props = defineProps({
  item: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    default: 1
  }
})

const paddedIndex = computed(() => String(props.index).padStart(2, '0'))
</script>

<style scoped>
.module-card {
  display: flex;
  align-items: stretch;
  gap: 26rpx;
  min-height: 214rpx;
  padding: 34rpx 30rpx;
  border-radius: 34rpx;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(252, 248, 239, 0.96)),
    #ffffff;
  border: 2rpx solid rgba(203, 172, 111, 0.42);
  box-shadow: 0 18rpx 42rpx rgba(92, 64, 29, 0.08);
}

.module-head {
  width: 112rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  flex-shrink: 0;
}

.icon {
  width: 76rpx;
  height: 76rpx;
  border-radius: 22rpx;
  background: #eef4ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42rpx;
}

.number {
  color: #1f73a8;
  font-size: 34rpx;
  line-height: 1;
  font-weight: 900;
}

.content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.title {
  font-size: 42rpx;
  line-height: 1.2;
  font-weight: 900;
  color: #242424;
}

.desc {
  margin-top: 16rpx;
  color: #625b50;
  font-size: 27rpx;
  line-height: 1.55;
}

.entry-text {
  margin-top: 22rpx;
  color: #4f4a43;
  font-size: 30rpx;
  line-height: 1;
  font-weight: 700;
}

.arrow {
  align-self: center;
  color: #b99b62;
  font-size: 48rpx;
  font-weight: 700;
}
</style>
