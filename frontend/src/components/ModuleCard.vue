<template>
  <view class="module-card" @tap="$emit('select', item.key)">
    <view
      class="icon"
      :class="{
        'icon--culture': item.iconVariant === 'culture',
        'icon--math': item.key === '数学基础',
        'icon--emphasis': ['英语运用', '逻辑推理'].includes(item.key)
      }"
    >
      <image
        v-if="item.iconVariant === 'culture'"
        class="culture-icon-image"
        src="/static/ui-icons/subject-culture-scroll-shadowless.png"
        mode="aspectFit"
      />
      <view v-else-if="item.key === '数学基础'" class="math-icon" aria-hidden="true" />
      <text v-else>{{ item.icon }}</text>
    </view>
    <view class="content">
      <view class="title">{{ item.title }}</view>
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
  width: 100%;
  max-width: 100%;
  min-width: 0;
  min-height: 200rpx;
  padding: 24rpx 28rpx;
  border-radius: 36rpx;
  background: #ffffff;
  border: 2rpx solid #e8effc;
  box-shadow: 0 18rpx 42rpx rgba(25, 48, 89, 0.08);
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 26rpx;
}

.icon {
  width: 98rpx;
  height: 98rpx;
  border-radius: 30rpx;
  background: var(--gyt-primary-soft, #f1f6ff);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 52rpx;
}

.icon--culture {
  overflow: hidden;
  box-sizing: border-box;
  background: var(--gyt-primary-soft, #f1f6ff);
  border: none;
  border-radius: 30rpx;
  box-shadow: none;
}

.icon--emphasis {
  font-size: 58rpx;
}

.icon--math {
  box-shadow: none;
}

.math-icon {
  width: 68rpx;
  height: 68rpx;
  flex: 0 0 68rpx;
  background: var(--gyt-primary, #1677ff);
  -webkit-mask: url('/static/ui-icons/subject-math.svg') center / contain no-repeat;
  mask: url('/static/ui-icons/subject-math.svg') center / contain no-repeat;
}

.culture-icon-image {
  width: 110rpx;
  height: 110rpx;
  max-width: none;
  flex: 0 0 110rpx;
  transform: translate(3rpx, 1rpx);
  filter: none;
}

.content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.title {
  color: #101828;
  font-size: 34rpx;
  line-height: 1.25;
  font-weight: 900;
}

.divider {
  margin-top: 24rpx;
  height: 2rpx;
  background: #edf2fb;
}

.entry-row {
  margin-top: 16rpx;
  color: var(--gyt-primary, #1677ff);
  font-size: 29rpx;
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
