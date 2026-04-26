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
    radial-gradient(circle at top left, rgba(203, 172, 111, 0.14), transparent 24%),
    radial-gradient(circle at bottom right, rgba(37, 99, 235, 0.07), transparent 26%),
    #f7f3ea;
  color: #172033;
  font-family: "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
}

.page {
  min-height: 100vh;
  box-sizing: border-box;
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
  background: #2563eb;
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 900;
  box-shadow: 0 14rpx 28rpx rgba(37, 99, 235, 0.18);
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
  color: #2563eb;
  font-size: 30rpx;
  font-weight: 800;
}
</style>
