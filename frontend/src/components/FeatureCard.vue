<template>
  <view class="card" @tap="$emit('select')">
    <view>
      <view class="title">{{ title }}</view>
      <view class="desc">{{ desc }}</view>
    </view>
    <view class="arrow">›</view>
  </view>
</template>

<script setup>
defineEmits(['select'])
defineProps({
  title: {
    type: String,
    required: true
  },
  desc: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 26rpx;
  border-radius: 28rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.05);
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
}
</style>
