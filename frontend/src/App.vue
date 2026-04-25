<script>
export default {
  onLaunch() {
    const examCode = uni.getStorageSync('examCode')
    if (!examCode) {
      uni.setStorageSync('examCode', 'Z001')
    }
  }
}
</script>

<style>
page {
  min-height: 100%;
  background:
    radial-gradient(circle at top left, rgba(37, 99, 235, 0.08), transparent 22%),
    radial-gradient(circle at bottom right, rgba(91, 140, 255, 0.08), transparent 24%),
    #f5f7fb;
  color: #172033;
  font-family: "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
}

.page {
  min-height: 100vh;
  box-sizing: border-box;
  padding: 28rpx 28rpx calc(env(safe-area-inset-bottom) + 36rpx);
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
  margin: 28rpx 0 18rpx;
  font-size: 32rpx;
  font-weight: 800;
  color: #172033;
}

.primary-button {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 88rpx;
  border-radius: 24rpx;
  background: #2563eb;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 800;
  box-shadow: 0 14rpx 28rpx rgba(37, 99, 235, 0.18);
}

.ghost-button {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 84rpx;
  border-radius: 24rpx;
  border: 2rpx solid #e6ebf5;
  background: #ffffff;
  color: #2563eb;
  font-size: 28rpx;
  font-weight: 700;
}
</style>
