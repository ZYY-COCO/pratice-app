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
        <view v-if="item.label === '目标版本'" class="target-options">
          <button
            v-for="option in examOptions"
            :key="option.code"
            class="target-option"
            :class="{ active: option.code === targetValue }"
            @tap="handleTargetChange(option.code)"
          >
            {{ option.shortLabel || option.code }}
          </button>
        </view>
        <text v-else class="value">{{ item.value }}</text>
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
  },
  examOptions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['changeExam'])

const avatarText = computed(() => props.profile.userName.slice(0, 1))
const targetValue = computed(() => props.profile.stats?.find((item) => item.label === '目标版本')?.value || 'Z001')

function handleTargetChange(code) {
  if (code && code !== targetValue.value) {
    emit('changeExam', code)
  }
}
</script>

<style scoped>
.profile-card {
  padding: 34rpx 30rpx;
  border-radius: 40rpx;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(244, 248, 255, 0.98)),
    radial-gradient(circle at top right, rgba(37, 99, 235, 0.12), transparent 44%);
  border: 2rpx solid rgba(230, 235, 245, 0.96);
  box-shadow: 0 20rpx 48rpx rgba(20, 31, 66, 0.07);
}

.header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
}

.user-wrap {
  display: flex;
  align-items: center;
  gap: 20rpx;
  min-width: 0;
}

.avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #2563eb, #7aa2ff);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
  font-weight: 800;
  box-shadow: 0 14rpx 26rpx rgba(37, 99, 235, 0.24);
}

.name {
  color: #101828;
  font-size: 34rpx;
  font-weight: 900;
  line-height: 1.2;
}

.subtitle {
  margin-top: 10rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.45;
}

.badge {
  padding: 14rpx 18rpx;
  border-radius: 22rpx;
  background: #edf3ff;
  color: #2563eb;
  font-size: 23rpx;
  font-weight: 900;
  white-space: nowrap;
}

.rows {
  margin-top: 28rpx;
  padding: 4rpx 0;
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.72);
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  padding: 22rpx 4rpx;
  border-bottom: 2rpx solid rgba(237, 241, 247, 0.86);
}

.row:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.label {
  color: #475467;
  font-size: 25rpx;
  font-weight: 700;
}

.value {
  color: #101828;
  font-size: 28rpx;
  font-weight: 900;
}

.target-options {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10rpx;
  margin-left: auto;
}

.target-option {
  min-width: 116rpx;
  min-height: 62rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 2rpx solid #d7e3fb;
  border-radius: 22rpx;
  background: #ffffff;
  color: #2563eb;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 62rpx;
}

.target-option.active {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
  box-shadow: 0 8rpx 18rpx rgba(37, 99, 235, 0.2);
}
</style>
