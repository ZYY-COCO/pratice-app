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
  gap: 22rpx;
  min-height: 128rpx;
  padding: 30rpx 28rpx;
  border-radius: 32rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 14rpx 32rpx rgba(20, 31, 66, 0.06);
}

.icon {
  width: 98rpx;
  height: 98rpx;
  border-radius: 30rpx;
  background: #eef4ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 46rpx;
  flex-shrink: 0;
}

.content {
  flex: 1;
}

.title {
  font-size: 32rpx;
  font-weight: 800;
  color: #172033;
}

.desc {
  margin-top: 10rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.5;
}

.arrow {
  color: #b2bccd;
  font-size: 46rpx;
  font-weight: 700;
}
</style>
