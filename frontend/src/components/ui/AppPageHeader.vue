<template>
  <view class="app-page-header-layout" :class="{ 'is-fixed': fixed, 'with-subtitle': subtitle }">
    <view class="app-page-header" :class="[`variant-${variant}`, { 'with-subtitle': subtitle }]">
      <view class="app-page-header-side is-left">
        <slot name="left">
          <button v-if="showBack" class="app-page-header-back" aria-label="返回" @tap="emit('back')">
            <image src="/static/ui-icons/png/original/back.png" mode="aspectFit" />
          </button>
          <view v-else class="app-page-header-placeholder"></view>
        </slot>
      </view>

      <view class="app-page-header-heading">
        <view class="app-page-header-title">{{ title }}</view>
        <view v-if="subtitle" class="app-page-header-subtitle">{{ subtitle }}</view>
      </view>

      <view class="app-page-header-side is-right">
        <slot name="right">
          <view class="app-page-header-placeholder"></view>
        </slot>
      </view>
    </view>
  </view>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    required: true
  },
  subtitle: {
    type: String,
    default: ''
  },
  showBack: {
    type: Boolean,
    default: true
  },
  variant: {
    type: String,
    default: 'standard'
  },
  fixed: {
    type: Boolean,
    default: true
  }
})

const emit = defineEmits(['back'])
</script>

<style scoped>
.app-page-header-layout {
  width: 100%;
  flex: 0 0 auto;
}

.app-page-header {
  position: relative;
  z-index: 24;
  width: 100%;
  max-width: 760rpx;
  min-height: calc(var(--status-bar-height, env(safe-area-inset-top)) + 116rpx);
  margin: 0 auto;
  box-sizing: border-box;
  padding: calc(var(--status-bar-height, env(safe-area-inset-top)) + 14rpx) 28rpx 10rpx;
  border-bottom: 0;
  background: transparent;
  display: grid;
  grid-template-columns: 82rpx minmax(0, 1fr) 82rpx;
  align-items: center;
  gap: 0;
}

.app-page-header-layout.is-fixed {
  min-height: calc(var(--status-bar-height, env(safe-area-inset-top)) + 116rpx);
}

.app-page-header-layout.is-fixed .app-page-header {
  position: fixed;
  top: 0;
  right: 0;
  left: 0;
  z-index: 80;
  width: 100vw;
  background: var(--gyt-page-bg, #fbfcff);
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.app-page-header.variant-transparent { border-bottom-color: transparent; background: transparent; }
.app-page-header.variant-glass {
  border-bottom-color: rgba(255, 255, 255, .62);
  background: rgba(248, 252, 255, .64);
  -webkit-backdrop-filter: blur(18px) saturate(118%);
  backdrop-filter: blur(18px) saturate(118%);
}

.app-page-header-side,
.app-page-header-placeholder {
  width: 82rpx;
  min-width: 82rpx;
  min-height: 82rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.app-page-header-side.is-left { justify-content: flex-start; }
.app-page-header-side.is-right { justify-content: flex-end; }

.app-page-header-back {
  box-sizing: border-box;
  width: 82rpx;
  height: 82rpx;
  min-width: 82rpx;
  min-height: 82rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 12rpx 30rpx rgba(29, 45, 86, 0.08);
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.app-page-header-back::after { border: 0; }
.app-page-header-back:active { background: var(--gyt-primary-soft, #edf4ff); transform: scale(.97); }
.app-page-header-back image { display: block; width: 44rpx; height: 44rpx; }

.app-page-header-heading {
  position: relative;
  min-width: 0;
  height: 82rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}
.app-page-header-title {
  overflow: hidden;
  color: #0d1020;
  font-size: var(--gyt-font-size-page-title, 34rpx);
  line-height: 1.2;
  font-weight: var(--gyt-font-weight-bold, 700);
  text-overflow: ellipsis;
  white-space: nowrap;
}
.app-page-header-subtitle {
  position: absolute;
  top: calc(50% + 22rpx);
  right: 0;
  left: 0;
  margin-top: 0;
  overflow: hidden;
  color: #728198;
  font-size: 17rpx;
  line-height: 1.15;
  font-weight: var(--gyt-font-weight-semibold, 600);
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* #ifdef MP-WEIXIN */
.app-page-header {
  min-height: calc(var(--mp-page-content-top, 96px) + var(--mp-page-header-height, 40px) + 20rpx);
  padding-top: var(--mp-page-content-top, 96px);
}

.app-page-header-layout.is-fixed {
  min-height: calc(var(--mp-page-content-top, 96px) + var(--mp-page-header-height, 40px) + 20rpx);
}

/* #endif */

</style>
