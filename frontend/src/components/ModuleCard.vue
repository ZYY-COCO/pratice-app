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
        src="/static/ui-icons/subject-culture-scroll.webp"
        mode="aspectFit"
      />
      <view v-else-if="item.key === '数学基础'" class="math-icon" aria-hidden="true" />
      <text v-else>{{ item.icon }}</text>
    </view>
    <view class="content">
      <view class="title">{{ item.title }}</view>
    </view>
    <view class="arrow" aria-hidden="true">›</view>
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
  box-sizing: border-box;
  width: 100%;
  max-width: 100%;
  min-width: 0;
  min-height: 108rpx;
  height: 100%;
  margin: 0;
  padding: 18rpx 0;
  border: 0;
  border-bottom: 2rpx solid rgba(42, 55, 79, 0.065);
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 18rpx;
  overflow: hidden;
  text-align: left;
  transition: background-color 160ms ease, opacity 160ms ease;
}

.module-card:active {
  background: var(--gyt-primary-tint, #f4f8ff);
  opacity: 0.88;
}

.icon {
  width: 96rpx;
  height: 96rpx;
  flex: 0 0 96rpx;
  border-radius: 28rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 70rpx;
  box-shadow: none;
}

.icon--culture {
  overflow: hidden;
  box-sizing: border-box;
  background: var(--gyt-primary-soft, #edf4ff);
  border: none;
  border-radius: 28rpx;
}

.icon--emphasis {
  font-size: 74rpx;
}

.icon--math {
  box-shadow: none;
}

.math-icon {
  width: 78rpx;
  height: 78rpx;
  flex: 0 0 78rpx;
  background: var(--gyt-primary, #1677ff);
  -webkit-mask: url('/static/ui-icons/subject-math.svg') center / contain no-repeat;
  mask: url('/static/ui-icons/subject-math.svg') center / contain no-repeat;
}

.culture-icon-image {
  width: 108rpx;
  height: 108rpx;
  max-width: none;
  flex: 0 0 108rpx;
  transform: none;
  filter: none;
}

.content {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5rpx;
}

.title {
  color: #243343;
  font-size: 38rpx;
  line-height: 1.3;
  font-weight: var(--gyt-font-weight-bold, 700);
}

.arrow {
  width: 40rpx;
  height: 56rpx;
  flex: 0 0 40rpx;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: #c5cbd4;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  line-height: 1;
  font-weight: 650;
}

@media (max-height: 760px) {
  .module-card {
    min-height: 96rpx;
    padding: 14rpx 0;
    gap: 16rpx;
  }

  .icon {
    width: 84rpx;
    height: 84rpx;
    flex-basis: 84rpx;
    border-radius: 24rpx;
    font-size: 62rpx;
  }

  .culture-icon-image {
    width: 94rpx;
    height: 94rpx;
    flex-basis: 94rpx;
  }

  .math-icon {
    width: 68rpx;
    height: 68rpx;
    flex-basis: 68rpx;
  }

  .title {
    font-size: 36rpx;
  }

  .arrow {
    width: 36rpx;
    height: 52rpx;
    flex-basis: 36rpx;
    font-size: 36rpx;
  }
}

@media (max-width: 350px) {
  .module-card {
    gap: 14rpx;
  }
}
</style>
