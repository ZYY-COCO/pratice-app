<template>
  <view class="profile-card">
    <view class="header">
      <view class="user-wrap">
        <view class="avatar">{{ avatarText }}</view>
        <view>
          <view class="name">{{ profile.userName }}</view>
          <view class="subtitle">{{ profile.subtitle }}</view>
        </view>
      </view>
      <view class="badge">{{ profile.badge }}</view>
    </view>

    <view class="rows">
      <view v-for="item in profile.stats" :key="item.label" class="row">
        <text class="label">{{ item.label }}</text>
        <text class="value">{{ item.value }}</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  profile: {
    type: Object,
    required: true
  }
})

const avatarText = computed(() => props.profile.userName.slice(0, 1))
</script>

<style scoped>
.profile-card {
  padding: 28rpx;
  border-radius: 30rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.05);
}

.header {
  display: flex;
  justify-content: space-between;
  gap: 12rpx;
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
  background: linear-gradient(135deg, #2563eb, #7aa2ff);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 800;
}

.name {
  font-size: 28rpx;
  font-weight: 800;
}

.subtitle {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
}

.badge {
  padding: 12rpx 18rpx;
  border-radius: 18rpx;
  background: #edf3ff;
  color: #2563eb;
  font-size: 22rpx;
  font-weight: 800;
}

.rows {
  margin-top: 18rpx;
}

.row {
  display: flex;
  justify-content: space-between;
  gap: 16rpx;
  padding: 18rpx 0;
  border-bottom: 2rpx dashed #edf1f7;
}

.row:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.label {
  color: #475467;
  font-size: 25rpx;
}

.value {
  color: #172033;
  font-size: 25rpx;
  font-weight: 800;
}
</style>
