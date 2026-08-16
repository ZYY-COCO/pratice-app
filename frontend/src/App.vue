<script>
import { enforceAuthOnCurrentPage } from './utils/routeGuard'
import { installPageTransitions } from './utils/pageTransition'
import { applyThemeByKey, getStoredThemeKey } from './utils/theme'
import { closeNativeSplashscreen } from './platform/runtime'

export default {
  onLaunch() {
    installPageTransitions()
    applyThemeByKey(getStoredThemeKey())
    const examCode = uni.getStorageSync('examCode')
    if (!examCode) {
      uni.setStorageSync('examCode', 'Z001')
    }
    enforceAuthOnCurrentPage()
    closeNativeSplashscreen()
  },
  onShow() {
    enforceAuthOnCurrentPage()
    closeNativeSplashscreen()
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
  --gyt-content-surface-shadow: none;
  --gyt-page-bg: radial-gradient(circle at top right, rgba(52, 120, 246, 0.1), transparent 25%), linear-gradient(180deg, #fbfcff 0%, #f4f7fb 100%);
  --gyt-panel-bg: radial-gradient(circle at 86% 10%, rgba(52, 120, 246, 0.14), transparent 30%), linear-gradient(135deg, #ffffff 0%, #eef6ff 100%);
  --gyt-route-duration: 380ms;
  --gyt-route-ease: cubic-bezier(0.25, 0.8, 0.25, 1);
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
  box-shadow: var(--gyt-content-surface-shadow);
}

:root.gyt-circle-glass-theme page {
  color: #1c2423;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
}

:root.gyt-circle-glass-theme .app-card,
:root.gyt-circle-glass-theme .ghost-button {
  border-color: rgba(255, 255, 255, 0.66);
  background: rgba(250, 253, 252, 0.62);
  -webkit-backdrop-filter: blur(18px) saturate(118%);
  backdrop-filter: blur(18px) saturate(118%);
}

/* Keep rounded content surfaces clean across every theme. Sheets and tab bars
   deliberately retain their own elevation because they sit above page content. */
.card,
.hero-card,
.module-card,
.section-card,
.profile-card,
.option-card,
.option,
.panel,
.accordion,
.landing-focus-swiper,
.landing-focus-art,
.landing-news-card,
.landing-news-document,
.landing-service-card,
.circle-trend-card,
.circle-entry,
.circle-score-card,
.experience-search,
.experience-card,
.circle-community-tabs,
.circle-community-tab.active,
.community-post-card,
.community-reader-media-swiper,
.material-card,
.circle-empty-card,
.welcome-card,
.stats-card,
.mock-exam-card,
.filter-card,
.learning-advice-card,
.overview-art,
.overview-metrics,
.logout-card,
.catalog-results-frame,
.catalog-inline-state,
.catalog-program-card,
.setup-hero,
.comprehensive-card,
.culture-progress-card,
.sticky-bar,
.quiz-shell,
.summary-card,
.mock-section-card,
.ai-diagnosis-card,
.subject-card,
.rank-hero,
.state-card,
.leaderboard-row,
.search-card,
.filter-tabs,
.history-card,
.favorite-card,
.empty-card,
.access-hero,
.version-card,
.agreement-card,
.publish-card,
.login-card,
.status-card {
  box-shadow: var(--gyt-content-surface-shadow) !important;
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

uni-page.gyt-route-enter-forward,
uni-page-body.gyt-route-enter-forward,
uni-page.gyt-route-leave-back,
uni-page-body.gyt-route-leave-back,
.gyt-route-exit-overlay.gyt-route-leave-back {
  contain: paint;
  will-change: transform;
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
  transform-style: preserve-3d;
}

.gyt-route-exit-overlay {
  position: fixed;
  inset: 0;
  z-index: 2147483000;
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  pointer-events: none;
  isolation: isolate;
}

.gyt-route-exit-snapshot {
  position: absolute;
  box-sizing: border-box;
}

uni-page.gyt-route-enter-forward,
uni-page-body.gyt-route-enter-forward {
  animation: gyt-route-enter-forward var(--gyt-route-duration) var(--gyt-route-ease) both;
}

uni-page.gyt-route-leave-back,
uni-page-body.gyt-route-leave-back,
.gyt-route-exit-overlay.gyt-route-leave-back {
  pointer-events: none;
  animation: gyt-route-leave-back var(--gyt-route-duration) var(--gyt-route-ease) both;
}

@keyframes gyt-route-enter-forward {
  from {
    transform: translate3d(100%, 0, 0);
  }

  to {
    transform: translate3d(0, 0, 0);
  }
}

@keyframes gyt-route-leave-back {
  from {
    transform: translate3d(0, 0, 0);
  }

  to {
    transform: translate3d(100%, 0, 0);
  }
}

@media (prefers-reduced-motion: reduce) {
  uni-page.gyt-route-enter-forward,
  uni-page-body.gyt-route-enter-forward,
  uni-page.gyt-route-leave-back,
  uni-page-body.gyt-route-leave-back,
  .gyt-route-exit-overlay.gyt-route-leave-back {
    animation: none;
  }
}
</style>
