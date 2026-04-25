<template>
  <view class="accordion-group">
    <view v-for="section in sections" :key="section.module" class="accordion" :class="{ open: openMap[section.module] }">
      <view class="accordion-header" @tap="$emit('toggle-open', section.module)">
        <view class="header-copy">
          <view class="title">{{ section.module }}</view>
          <view class="sub">{{ section.description }}</view>
        </view>
        <view class="arrow">{{ openMap[section.module] ? '⌃' : '⌄' }}</view>
      </view>

      <view v-if="openMap[section.module]" class="accordion-body">
        <view
          v-for="submodule in section.submodules"
          :key="submodule"
          class="check-row"
          @tap="$emit('toggle-tag', submodule)"
        >
          <view class="check-box" :class="{ checked: selectedTags.includes(submodule) }">
            <text v-if="selectedTags.includes(submodule)">✓</text>
          </view>
          <view class="check-copy">
            <view class="check-title">{{ submodule }}</view>
            <view class="check-sub">真题 {{ getCount(submodule) }} 道</view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
defineProps({
  sections: {
    type: Array,
    default: () => []
  },
  selectedTags: {
    type: Array,
    default: () => []
  },
  openMap: {
    type: Object,
    default: () => ({})
  },
  getCount: {
    type: Function,
    required: true
  }
})

defineEmits(['toggle-open', 'toggle-tag'])
</script>

<style scoped>
.accordion-group {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.accordion {
  overflow: hidden;
  border-radius: 30rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.04);
}

.accordion-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 28rpx;
}

.header-copy {
  flex: 1;
}

.title {
  font-size: 28rpx;
  font-weight: 800;
  color: #172033;
}

.sub {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.5;
}

.arrow {
  color: #98a2b3;
  font-size: 30rpx;
}

.accordion-body {
  padding: 0 28rpx 16rpx;
  border-top: 2rpx solid #edf1f7;
  background: #fcfdff;
}

.check-row {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding: 22rpx 0;
  border-bottom: 2rpx dashed #edf1f7;
}

.check-row:last-child {
  border-bottom: 0;
}

.check-box {
  width: 36rpx;
  height: 36rpx;
  border-radius: 12rpx;
  border: 2rpx solid #c7d2fe;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 20rpx;
  font-weight: 800;
  flex-shrink: 0;
}

.check-box.checked {
  border-color: #2563eb;
  background: #2563eb;
}

.check-copy {
  flex: 1;
}

.check-title {
  font-size: 26rpx;
  color: #172033;
  font-weight: 700;
}

.check-sub {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
}
</style>
