<template>
  <!-- #ifdef H5 -->
  <view class="icp-footer" :class="{ compact }">
    <a
      class="icp-link"
      href="https://beian.miit.gov.cn/"
      target="_blank"
      rel="noopener noreferrer"
    >
      粤ICP备2026058975号
    </a>
  </view>
  <!-- #endif -->
</template>

<script setup>
defineProps({
  compact: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.icp-footer {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28rpx 24rpx calc(env(safe-area-inset-bottom) + 28rpx);
  color: #8a94a6;
  font-size: 22rpx;
  line-height: 1.4;
  text-align: center;
}

.icp-footer.compact {
  padding-bottom: calc(env(safe-area-inset-bottom) + 142rpx);
}

.icp-link {
  color: #8a94a6;
  text-decoration: none;
}

.icp-link:active,
.icp-link:hover {
  color: var(--gyt-primary, #1677ff);
}
</style>
