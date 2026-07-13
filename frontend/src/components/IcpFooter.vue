<template>
  <!-- #ifdef H5 -->
  <view class="icp-footer" :class="{ compact }">
    <view class="icp-footer-inner">
      <a
        class="icp-link"
        href="https://beian.miit.gov.cn/"
        target="_blank"
        rel="noopener noreferrer"
      >
        粤ICP备2026058975号
      </a>
      <a
        class="icp-link police-link"
        href="https://beian.mps.gov.cn/#/query/webSearch?code=44011402001320"
        target="_blank"
        rel="noreferrer"
      >
        <image class="police-icon" src="/static/beian-gongan.png" mode="aspectFit" />
        <text>粤公网安备44011402001320号</text>
      </a>
      <a class="icp-link" href="/privacy">
        隐私政策
      </a>
    </view>
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
  position: relative;
  z-index: 0;
  isolation: isolate;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28rpx 24rpx calc(env(safe-area-inset-bottom) + 28rpx);
  color: #8a94a6;
  font-size: 22rpx;
  line-height: 1.4;
  text-align: center;
}

.icp-footer-inner {
  position: relative;
  z-index: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-wrap: wrap;
  gap: 12rpx 20rpx;
}

.icp-footer.compact {
  padding-bottom: calc(env(safe-area-inset-bottom) + 142rpx);
}

.icp-link {
  color: #8a94a6;
  text-decoration: none;
}

.police-link {
  position: relative;
  z-index: 0;
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
}

.police-icon {
  width: 24rpx;
  height: 24rpx;
  flex: 0 0 24rpx;
}

.icp-link:active,
.icp-link:hover {
  color: var(--gyt-primary, #1677ff);
}
</style>
