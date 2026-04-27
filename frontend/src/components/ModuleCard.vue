<template>
  <view class="module-card" @tap="$emit('select', item.key)">
    <view class="icon">{{ item.icon }}</view>
    <view class="content">
      <view class="title">{{ item.title }}</view>
      <view class="desc">{{ item.desc }}</view>
      <view class="divider"></view>
      <view class="entry-row">
        <text>进入练习</text>
        <text class="arrow">›</text>
      </view>
    </view>
  </view>
</template>

<script setup>
defineEmits(['select'])

defineProps({
  item: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    default: 1
  }
})
</script>

<style scoped>
.module-card {
  width: 100%;
  max-width: 100%;
  min-width: 0;
  min-height: 216rpx;
  padding: 28rpx 28rpx;
  border-radius: 36rpx;
  background: #ffffff;
  border: 2rpx solid #e8effc;
  box-shadow: 0 18rpx 42rpx rgba(25, 48, 89, 0.08);
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 26rpx;
}

.icon {
  width: 98rpx;
  height: 98rpx;
  border-radius: 30rpx;
  background: #f1f6ff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 52rpx;
}

.content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.title {
  color: #101828;
  font-size: 34rpx;
  line-height: 1.25;
  font-weight: 900;
}

.desc {
  margin-top: 12rpx;
  min-height: 0;
  color: #8a95a8;
  font-size: 26rpx;
  line-height: 1.55;
  font-weight: 600;
}

.divider {
  margin-top: 20rpx;
  height: 2rpx;
  background: #edf2fb;
}

.entry-row {
  margin-top: 16rpx;
  color: #1677ff;
  font-size: 29rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.arrow {
  font-size: 36rpx;
  line-height: 1;
}
</style>
