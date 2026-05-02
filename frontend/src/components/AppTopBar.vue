<template>
  <view class="topbar">
    <view class="user-wrap">
      <view class="avatar">{{ avatarText }}</view>
      <view class="user-copy">
        <text class="name">{{ userName }}</text>
        <text class="status">{{ statusText }}</text>
      </view>
    </view>

  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  userName: {
    type: String,
    default: '小钟'
  },
  statusText: {
    type: String,
    default: '今日学习状态：稳定推进'
  }
})

const avatarText = computed(() => props.userName.slice(0, 1))
</script>

<style scoped>
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.user-wrap {
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.avatar {
  width: 80rpx;
  height: 80rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-gradient);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 800;
  box-shadow: 0 12rpx 24rpx var(--gyt-primary-shadow);
}

.user-copy {
  display: flex;
  flex-direction: column;
}

.name {
  font-size: 28rpx;
  font-weight: 800;
  color: #172033;
}

.status {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
}

</style>
