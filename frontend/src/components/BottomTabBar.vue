<template>
  <view class="tabbar" :class="{ glass, collapsed }">
    <view v-if="collapsed && activeItem" class="tab-compact" role="button" :aria-label="`展开${activeItem.label}导航`" @tap="emit('expand')">
      <image
        v-if="activeItem.iconSrc"
        :class="['tab-icon-image', 'tab-icon-raster', activeItem.iconClass]"
        :src="resolveTabIcon(activeItem, true)"
        mode="aspectFit"
      />
      <text v-else class="tab-icon">{{ activeItem.icon }}</text>
      <text class="tab-label">{{ activeItem.label }}</text>
      <view v-if="activeItem.unread" class="tab-unread-dot tab-unread-dot--compact" aria-label="有新消息"></view>
    </view>

    <view v-else class="tabbar-items">
      <view class="tab-active-indicator" :style="activeIndicatorStyle" aria-hidden="true">
        <view class="tab-active-indicator-surface"></view>
      </view>
      <view
        v-for="item in items"
        :key="item.key"
        class="tab-item"
        :class="{ active: modelValue === item.key }"
        @tap="emit('update:modelValue', item.key)"
      >
        <image
          v-if="item.iconSrc"
          :class="['tab-icon-image', 'tab-icon-raster', item.iconClass]"
          :src="resolveTabIcon(item, modelValue === item.key)"
          mode="aspectFit"
        />
        <text v-else class="tab-icon">{{ item.icon }}</text>
        <text class="tab-label">{{ item.label }}</text>
        <view v-if="item.unread" class="tab-unread-dot" aria-label="有新消息"></view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { getThemeIconSrc, getToneIconSrc } from '../utils/iconAssets'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'home'
  },
  items: {
    type: Array,
    default: () => []
  },
  glass: {
    type: Boolean,
    default: false
  },
  collapsed: {
    type: Boolean,
    default: false
  },
  themeKey: {
    type: String,
    default: 'blue'
  }
})

const emit = defineEmits(['update:modelValue', 'expand'])

const activeItem = computed(() =>
  props.items.find((item) => item.key === props.modelValue) || props.items[0]
)

const activeIndex = computed(() => {
  const index = props.items.findIndex((item) => item.key === props.modelValue)
  return index < 0 ? 0 : index
})

const activeIndicatorStyle = computed(() => {
  const itemCount = Math.max(props.items.length, 1)
  return {
    width: `${100 / itemCount}%`,
    transform: `translate3d(${activeIndex.value * 100}%, 0, 0)`
  }
})

const resolveTabIcon = (item, active) => {
  if (active) return getThemeIconSrc(item.iconSrc, props.themeKey)
  return getToneIconSrc(item.iconSrc, 'neutral')
}
</script>

<style scoped>
.tabbar {
  position: fixed;
  left: 26rpx;
  right: 26rpx;
  bottom: calc(env(safe-area-inset-bottom) + 28rpx);
  display: flex;
  gap: 14rpx;
  padding: 12rpx 16rpx;
  border-radius: 34rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid #edf2fb;
  box-shadow: 0 20rpx 52rpx rgba(25, 48, 89, 0.12);
  z-index: 20;
  backdrop-filter: blur(16rpx);
}

.tabbar-items {
  position: relative;
  min-width: 0;
  flex: 1;
  display: flex;
  align-items: stretch;
}

.tab-active-indicator {
  position: absolute;
  z-index: 0;
  top: 0;
  bottom: 0;
  left: 0;
  box-sizing: border-box;
  padding: 0 7rpx;
  pointer-events: none;
  will-change: transform;
  transition: transform 320ms cubic-bezier(0.22, 1, 0.36, 1);
}

.tab-active-indicator-surface {
  width: 100%;
  height: 100%;
  border-radius: 26rpx;
  background: var(--gyt-primary-soft, #edf4ff);
}

.tabbar.glass {
  right: auto;
  bottom: calc(env(safe-area-inset-bottom) + 12px);
  left: 50%;
  box-sizing: border-box;
  width: calc(100% - var(--circle-screen-gutter, 16px) - var(--circle-screen-gutter, 16px));
  height: 68px;
  gap: 4px;
  padding: 5px;
  border-color: rgba(255, 255, 255, 0.72);
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.64);
  box-shadow: 0 14px 34px var(--gyt-primary-shadow, rgba(52, 120, 246, 0.16));
  transform: translateX(-50%);
  -webkit-backdrop-filter: blur(26px) saturate(125%);
  backdrop-filter: blur(26px) saturate(125%);
  transition: width 260ms ease, height 260ms ease, border-radius 260ms ease, background-color 180ms ease, box-shadow 180ms ease;
}

.tabbar.glass.collapsed {
  width: 152px;
  height: 56px;
  gap: 0;
  padding: 4px;
  border-radius: 28px;
  background: rgba(255, 255, 255, 0.58);
  box-shadow: 0 12px 28px var(--gyt-primary-shadow, rgba(52, 120, 246, 0.15));
}

.tabbar.glass .tabbar-items {
  height: 100%;
}

.tabbar.glass .tab-active-indicator {
  padding: 0 2px;
}

.tabbar.glass .tab-active-indicator-surface {
  border-radius: var(--circle-radius-control, 18px);
  border: 1px solid var(--gyt-primary-border, #d7e5ff);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.82), var(--gyt-primary-soft, #edf4ff));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.78), 0 4px 12px var(--gyt-primary-shadow, rgba(52, 120, 246, 0.12));
}

.tab-item {
  position: relative;
  z-index: 1;
  flex: 1;
  min-height: 82rpx;
  padding: 12rpx 8rpx;
  border-radius: 26rpx;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
}

.tab-item.active {
  background: transparent;
}

.tab-unread-dot {
  position: absolute;
  z-index: 3;
  top: 10rpx;
  left: calc(50% + 14rpx);
  width: 16rpx;
  height: 16rpx;
  border: 3rpx solid #ffffff;
  border-radius: 50%;
  background: #f05d5d;
  box-shadow: 0 3rpx 8rpx rgba(240, 93, 93, 0.32);
  box-sizing: border-box;
  pointer-events: none;
}

.tab-unread-dot--compact {
  top: 8rpx;
  right: 18rpx;
  left: auto;
}

.tabbar.glass .tab-item {
  box-sizing: border-box;
  min-height: 0;
  height: 100%;
  padding: 4px 3px;
  border-radius: var(--circle-radius-control, 18px);
  gap: 1px;
  transition: transform 180ms ease, background-color 180ms ease;
}

.tabbar.glass .tab-item.active {
  background: transparent;
  box-shadow: none;
}

.tabbar.glass .tab-unread-dot {
  top: 6px;
  left: calc(50% + 8px);
  width: 9px;
  height: 9px;
  border-width: 1.5px;
}

.tabbar.glass .tab-unread-dot--compact {
  top: 6px;
  right: 13px;
  left: auto;
}

.tabbar.glass .tab-item:active {
  transform: scale(0.98);
}

.tab-compact {
  position: relative;
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  padding: 4px 14px;
  border-radius: 24px;
  border: 1px solid var(--gyt-primary-border, #d7e5ff);
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.8), var(--gyt-primary-soft, #edf4ff));
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.78), 0 4px 12px var(--gyt-primary-shadow, rgba(52, 120, 246, 0.12));
  animation: tab-compact-in 180ms ease both;
}

.tabbar.glass .tab-compact .tab-icon,
.tabbar.glass .tab-compact .tab-label {
  color: var(--gyt-primary, #3478f6);
}

.tabbar.glass .tab-compact .tab-icon-image {
  width: 20px;
  height: 20px;
  background-color: transparent;
}

.tabbar.glass .tab-compact .tab-label {
  font-size: 14px;
  font-weight: var(--gyt-font-weight-semibold, 600);
}

.tab-compact:active {
  transform: scale(0.98);
}

@keyframes tab-compact-in {
  from {
    opacity: 0;
    transform: scale(0.94);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.tab-icon {
  color: #98a2b3;
  font-size: 34rpx;
  line-height: 1;
  font-weight: 900;
  transition: color 160ms ease;
}

.tab-icon-image {
  width: 36rpx;
  height: 36rpx;
  background-color: transparent;
  transition: opacity 160ms ease;
}

.tab-icon-practice {
  transform: scale(0.9);
}

.tab-icon-raster {
  display: block;
  opacity: 0.9;
}

.tab-label {
  color: #8a94a6;
  font-size: 25rpx;
  line-height: 1.2;
  font-weight: var(--gyt-font-weight-semibold, 600);
  transition: color 160ms ease;
}

.tabbar.glass .tab-icon,
.tabbar.glass .tab-label {
  color: rgba(84, 98, 116, 0.72);
}

.tabbar.glass .tab-icon-image {
  width: 20px;
  height: 20px;
  background-color: transparent;
}

.tabbar.glass .tab-label {
  font-size: 12px;
  font-weight: var(--gyt-font-weight-semibold, 600);
}

.tab-item.active .tab-icon {
  color: var(--gyt-primary, #1677ff);
}

.tab-item.active .tab-icon-image {
  background-color: transparent;
  opacity: 1;
}

.tab-item.active .tab-label {
  color: var(--gyt-primary, #1677ff);
}

.tabbar.glass .tab-item.active .tab-icon,
.tabbar.glass .tab-item.active .tab-label {
  color: var(--gyt-primary, #3478f6);
}

.tabbar.glass .tab-item.active .tab-icon-image {
  background-color: transparent;
}

@supports not (backdrop-filter: blur(1px)) {
  .tabbar.glass {
    background: rgba(255, 255, 255, 0.96);
  }
}

@media (prefers-reduced-motion: reduce) {
  .tabbar.glass,
  .tabbar.glass .tab-item,
  .tab-active-indicator,
  .tab-icon,
  .tab-icon-image,
  .tab-label {
    transition: none;
  }

  .tab-compact {
    animation: none;
  }
}
</style>
