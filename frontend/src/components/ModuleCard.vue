<template>
  <view class="module-card" @tap="$emit('select', item.key)">
    <view class="icon">{{ item.icon }}</view>
    <view class="content">
      <view class="title">{{ item.title }}</view>
      <view class="desc">{{ item.desc }}</view>
    </view>
    <view class="arrow">›</view>
  </view>
</template>

<script setup>
defineEmits(['select'])

defineProps({
  item: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.module-card {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 28rpx;
  border-radius: 30rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.05);
}

.icon {
  width: 92rpx;
  height: 92rpx;
  border-radius: 26rpx;
  background: #eef4ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42rpx;
  flex-shrink: 0;
}

.content {
  flex: 1;
}

.title {
  font-size: 30rpx;
  font-weight: 800;
  color: #172033;
}

.desc {
  margin-top: 10rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.5;
}

.arrow {
  color: #98a2b3;
  font-size: 40rpx;
  font-weight: 700;
}
</style>
