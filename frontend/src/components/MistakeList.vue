<template>
  <view class="mistake-list">
    <view v-for="item in items" :key="item.id || item.title" class="mistake-item" @tap="$emit('select', item)">
      <view class="title">{{ item.title }}</view>
      <view v-if="item.meta" class="meta">{{ item.meta }}</view>
      <view class="tags">
        <text v-for="tag in item.tags" :key="tag" class="tag">{{ tag }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
defineProps({
  items: {
    type: Array,
    default: () => []
  }
})

defineEmits(['select'])
</script>

<style scoped>
.mistake-item {
  padding: 18rpx 0;
  border-bottom: 2rpx dashed #edf1f7;
}

.mistake-item:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.title {
  font-size: 26rpx;
  line-height: 1.6;
  font-weight: 700;
  color: #172033;
}

.meta {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.5;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 14rpx;
}

.tag {
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: #eef4ff;
  color: #4c5f85;
  font-size: 20rpx;
}
</style>
