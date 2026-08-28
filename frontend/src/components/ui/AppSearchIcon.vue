<template>
  <view class="app-search-icon" aria-hidden="true"></view>
</template>

<style scoped>
.app-search-icon {
  position: relative;
  width: 22rpx;
  height: 22rpx;
  flex: 0 0 22rpx;
  box-sizing: border-box;
  border: 4rpx solid currentColor;
  border-radius: 50%;
  color: var(--gyt-primary, #3478f6);
  opacity: 0.88;
}

.app-search-icon::after {
  position: absolute;
  right: -9rpx;
  bottom: -7rpx;
  width: 11rpx;
  height: 4rpx;
  border-radius: 999rpx;
  background: currentColor;
  content: '';
  transform: rotate(45deg);
}
</style>
