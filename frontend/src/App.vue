<script>
import { enforceAuthOnCurrentPage } from './utils/routeGuard'
import { applyThemeByKey, getStoredThemeKey } from './utils/theme'

export default {
  onLaunch() {
    applyThemeByKey(getStoredThemeKey())
    const examCode = uni.getStorageSync('examCode')
    if (!examCode) {
      uni.setStorageSync('examCode', 'Z001')
    }
    enforceAuthOnCurrentPage()
  },
  onShow() {
    enforceAuthOnCurrentPage()
  }
}
</script>

<style>
:root {
  --gyt-primary: #3478f6;
  --gyt-primary-soft: #edf4ff;
  --gyt-primary-tint: #f4f8ff;
  --gyt-primary-border: #d7e5ff;
  --gyt-primary-gradient: linear-gradient(135deg, #3478f6, #68a0ff);
  --gyt-primary-shadow: rgba(52, 120, 246, 0.2);
  --gyt-page-bg: radial-gradient(circle at top right, rgba(52, 120, 246, 0.1), transparent 25%), linear-gradient(180deg, #fbfcff 0%, #f4f7fb 100%);
  --gyt-panel-bg: radial-gradient(circle at 86% 10%, rgba(52, 120, 246, 0.14), transparent 30%), linear-gradient(135deg, #ffffff 0%, #eef6ff 100%);
}

page {
  width: 100%;
  min-height: 100%;
  min-height: 100vh;
  min-height: 100dvh;
  overflow-x: hidden;
  background: var(--gyt-page-bg);
  color: #172033;
  font-family: "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
}

.page {
  width: 100%;
  max-width: 100vw;
  min-height: 100vh;
  min-height: 100dvh;
  box-sizing: border-box;
  overflow-x: hidden;
  padding: 28rpx 24rpx calc(env(safe-area-inset-bottom) + 36rpx);
}

.app-card {
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  border-radius: 32rpx;
  box-shadow: 0 18rpx 44rpx rgba(20, 31, 66, 0.06);
}

.muted {
  color: #667085;
  font-size: 24rpx;
  line-height: 1.6;
}

.section-title {
  margin: 34rpx 0 20rpx;
  font-size: 36rpx;
  font-weight: 900;
  color: #172033;
}

.primary-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 102rpx;
  border-radius: 28rpx;
  background: var(--gyt-primary, #1677ff);
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 900;
  box-shadow: 0 14rpx 28rpx var(--gyt-primary-shadow, rgba(37, 99, 235, 0.18));
}

.ghost-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  min-height: 100rpx;
  border-radius: 28rpx;
  border: 2rpx solid #e6ebf5;
  background: #ffffff;
  color: var(--gyt-primary, #1677ff);
  font-size: 30rpx;
  font-weight: 800;
}
</style>
