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
  gap: 22rpx;
}

.accordion {
  overflow: hidden;
  border-radius: 36rpx;
  background: #ffffff;
  border: 2rpx solid rgba(230, 235, 245, 0.96);
  box-shadow: 0 16rpx 36rpx rgba(20, 31, 66, 0.06);
}

.accordion-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  min-height: 118rpx;
  padding: 30rpx;
}

.header-copy {
  flex: 1;
}

.title {
  font-size: 31rpx;
  font-weight: 900;
  color: #172033;
}

.sub {
  margin-top: 10rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.5;
}

.arrow {
  color: #98a2b3;
  font-size: 34rpx;
}

.accordion-body {
  padding: 10rpx 24rpx 22rpx;
  border-top: 2rpx solid #edf1f7;
  background: linear-gradient(180deg, #fcfdff 0%, #f8fbff 100%);
}

.check-row {
  display: flex;
  align-items: center;
  gap: 20rpx;
  min-height: 92rpx;
  margin-top: 12rpx;
  padding: 20rpx;
  border: 2rpx solid #edf1f7;
  border-radius: 26rpx;
  background: #ffffff;
}

.check-row:last-child {
  border-bottom: 2rpx solid #edf1f7;
}

.check-box {
  width: 48rpx;
  height: 48rpx;
  border-radius: 16rpx;
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
  box-shadow: 0 8rpx 16rpx rgba(37, 99, 235, 0.18);
}

.check-copy {
  flex: 1;
}

.check-title {
  font-size: 28rpx;
  color: #172033;
  font-weight: 800;
}

</style>
