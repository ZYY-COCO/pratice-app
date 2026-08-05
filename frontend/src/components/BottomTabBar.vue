<template>
  <view class="tabbar" :class="{ glass, collapsed }">
    <view v-if="collapsed && activeItem" class="tab-compact" role="button" :aria-label="`展开${activeItem.label}导航`" @tap="emit('expand')">
      <!-- #ifdef MP-WEIXIN -->
      <image
        v-if="activeItem.mpIconSrc"
        class="tab-icon-image tab-icon-png"
        :src="activeItem.mpIconSrc"
        mode="aspectFit"
      />
      <text v-else class="tab-icon">{{ activeItem.icon }}</text>
      <!-- #endif -->
      <!-- #ifndef MP-WEIXIN -->
      <view
        v-if="activeItem.iconSrc"
        class="tab-icon-image tab-icon-mask"
        :style="getIconMaskStyle(activeItem.iconSrc)"
      />
      <text v-else class="tab-icon">{{ activeItem.icon }}</text>
      <!-- #endif -->
      <text class="tab-label">{{ activeItem.label }}</text>
    </view>

    <template v-else>
      <view
        v-for="item in items"
        :key="item.key"
        class="tab-item"
        :class="{ active: modelValue === item.key }"
        @tap="emit('update:modelValue', item.key)"
      >
        <!-- #ifdef MP-WEIXIN -->
        <image
          v-if="item.mpIconSrc"
          class="tab-icon-image tab-icon-png"
          :src="item.mpIconSrc"
          mode="aspectFit"
        />
        <text v-else class="tab-icon">{{ item.icon }}</text>
        <!-- #endif -->
        <!-- #ifndef MP-WEIXIN -->
        <view
          v-if="item.iconSrc"
          class="tab-icon-image tab-icon-mask"
          :style="getIconMaskStyle(item.iconSrc)"
        />
        <text v-else class="tab-icon">{{ item.icon }}</text>
        <!-- #endif -->
        <text class="tab-label">{{ item.label }}</text>
      </view>
    </template>
  </view>
</template>

<script setup>
import { computed } from 'vue'

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
  }
})

const emit = defineEmits(['update:modelValue', 'expand'])

const activeItem = computed(() =>
  props.items.find((item) => item.key === props.modelValue) || props.items[0]
)

const getIconMaskStyle = (iconSrc) => ({
  WebkitMaskImage: `url("${iconSrc}")`,
  maskImage: `url("${iconSrc}")`
})
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

.tabbar.glass {
  right: auto;
  bottom: calc(env(safe-area-inset-bottom) + 12px);
  left: 50%;
  box-sizing: border-box;
  width: calc(100% - var(--circle-screen-gutter, 16px) - var(--circle-screen-gutter, 16px));
  height: 68px;
  gap: 4px;
  padding: 5px;
  border-color: rgba(255, 255, 255, 0.78);
  border-radius: 28px;
  background: var(--circle-tab-bg, rgba(247, 250, 249, 0.58));
  box-shadow: var(--circle-tab-shadow, 0 14px 34px rgba(30, 55, 56, 0.16));
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
  background: rgba(247, 250, 249, 0.66);
  box-shadow: 0 12px 28px rgba(30, 55, 56, 0.15);
}

.tab-item {
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
  background: var(--gyt-primary-soft, #edf4ff);
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
  background: rgba(255, 255, 255, 0.52);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.66), 0 3px 10px rgba(37, 71, 69, 0.08);
}

.tabbar.glass .tab-item:active {
  transform: scale(0.98);
}

.tab-compact {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  padding: 4px 14px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.56);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.66), 0 3px 10px rgba(37, 71, 69, 0.08);
  animation: tab-compact-in 180ms ease both;
}

.tabbar.glass .tab-compact .tab-icon,
.tabbar.glass .tab-compact .tab-label {
  color: var(--circle-brand, #5b8fdf);
}

.tabbar.glass .tab-compact .tab-icon-image {
  width: 20px;
  height: 20px;
  background-color: var(--circle-brand, #5b8fdf);
}

.tabbar.glass .tab-compact .tab-label {
  font-size: 14px;
  font-weight: 650;
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
}

.tab-icon-image {
  width: 36rpx;
  height: 36rpx;
  background-color: #98a2b3;
}

.tab-icon-mask {
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-size: contain;
  mask-size: contain;
}

.tab-icon-png {
  background-color: transparent;
  opacity: 0.46;
}

.tab-label {
  color: #8a94a6;
  font-size: 25rpx;
  line-height: 1.2;
  font-weight: 800;
}

.tabbar.glass .tab-icon,
.tabbar.glass .tab-label {
  color: var(--circle-muted, #718096);
}

.tabbar.glass .tab-icon-image {
  width: 20px;
  height: 20px;
  background-color: var(--circle-muted, #718096);
}

.tabbar.glass .tab-label {
  font-size: 12px;
  font-weight: 600;
}

.tab-item.active .tab-icon {
  color: var(--gyt-primary, #1677ff);
}

.tab-item.active .tab-icon-image {
  background-color: var(--gyt-primary, #1677ff);
}

.tab-item.active .tab-icon-png {
  background-color: transparent;
  opacity: 1;
}

.tab-item.active .tab-label {
  color: var(--gyt-primary, #1677ff);
}

.tabbar.glass .tab-item.active .tab-icon,
.tabbar.glass .tab-item.active .tab-label {
  color: var(--circle-brand, #5b8fdf);
}

.tabbar.glass .tab-item.active .tab-icon-image {
  background-color: var(--circle-brand, #5b8fdf);
}

@supports not (backdrop-filter: blur(1px)) {
  .tabbar.glass {
    background: rgba(255, 255, 255, 0.96);
  }
}

@media (prefers-reduced-motion: reduce) {
  .tabbar.glass,
  .tabbar.glass .tab-item {
    transition: none;
  }

  .tab-compact {
    animation: none;
  }
}
</style>
