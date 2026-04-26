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
  flex: 1;
  min-width: 0;
  min-height: 330rpx;
  padding: 28rpx 24rpx 24rpx;
  border-radius: 32rpx;
  background: #ffffff;
  border: 2rpx solid #e8effc;
  box-shadow: 0 18rpx 42rpx rgba(25, 48, 89, 0.08);
  display: flex;
  flex-direction: column;
}

.icon {
  width: 82rpx;
  height: 82rpx;
  border-radius: 22rpx;
  background: #f1f6ff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 46rpx;
}

.content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.title {
  margin-top: 28rpx;
  color: #101828;
  font-size: 30rpx;
  line-height: 1.25;
  font-weight: 900;
}

.desc {
  margin-top: 22rpx;
  min-height: 74rpx;
  color: #8a95a8;
  font-size: 23rpx;
  line-height: 1.55;
  font-weight: 600;
}

.divider {
  margin-top: auto;
  height: 2rpx;
  background: #edf2fb;
}

.entry-row {
  margin-top: 22rpx;
  color: #1677ff;
  font-size: 27rpx;
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
