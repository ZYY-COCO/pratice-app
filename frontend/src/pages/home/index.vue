<template>
  <view
    class="page home-page"
    :class="{
      'no-tab-page': !renderBottomTab,
      'circle-glass-page': activeTab === 'circle' || isCircleGlassTheme,
      'circle-themed-page': activeTab === 'circle' && !isCircleGlassTheme,
      'landing-glass-page': activeTab === 'landing' && isCircleGlassTheme,
      'landing-home-page': activeTab === 'landing',
      'practice-home-page': activeTab === 'home',
      'profile-reference-page': activeTab === 'profile',
      'profile-function-page': activeTab === 'mistakes' || activeTab === 'report',
      'scoreline-browser-page': isScoreLineBrowser,
      'circle-detail-active': isCircleDetail,
      'glass-theme-page': isCircleGlassTheme
    }"
    :style="pageInlineStyle"
    @mousemove="moveCircleEdgeSwipe"
    @mouseup="finishCircleEdgeSwipe"
    @mouseleave="cancelCircleEdgeSwipe"
  >
    <template v-if="activeTab === 'landing'">
        <view key="landing" class="landing-dashboard">
        <view class="home-header">
          <view class="brand-line">
            <view class="home-header-copy">
              <view class="home-header-brand">
                <image
                  class="home-header-logo"
                  src="/static/brand/hmtc-community-logo.png"
                  mode="aspectFit"
                  alt="HMTC 升学交流圈"
                />
                <text class="home-header-title">HMTC升学交流圈</text>
              </view>
            </view>
          </view>
          <view class="home-actions">
            <button class="message-bell" :class="{ unread: messageUnreadCount > 0 }" aria-label="打开消息中心" @tap="openMessageCenter">
              <image
                class="message-bell-icon-image"
                :src="getToneIconSrc('/static/ui-icons/png/original/notification-bell.png', messageUnreadCount > 0 ? 'gold' : 'dark')"
                mode="aspectFit"
                aria-hidden="true"
              />
              <view v-if="messageUnreadCount > 0" class="message-dot"></view>
            </button>
            <view class="profile-entry" aria-label="打开我的页面" @tap.stop="openProfileTab">
              <image
                v-if="avatarImageUrl"
                class="profile-entry-image"
                :src="avatarImageUrl"
                mode="aspectFill"
                alt="用户头像"
              />
              <text v-else>{{ avatarText }}</text>
            </view>
          </view>
        </view>

        <view v-if="homeFocusItems.length" class="landing-focus-block">
          <swiper
            class="landing-focus-swiper"
            :current="homeFocusIndex"
            :autoplay="true"
            :interval="4800"
            :duration="420"
            circular
            @change="handleHomeFocusChange"
          >
            <swiper-item v-for="(item, index) in homeFocusItems" :key="item.title">
              <view
                class="landing-focus-slide"
                :class="index === 0 ? 'is-blue' : index === 1 ? 'is-violet' : 'is-mint'"
                role="button"
                :aria-label="item.title"
                @tap="openHomeFocus(item)"
              >
                <view class="landing-focus-copy">
                  <text class="landing-focus-badge">{{ item.badge }}</text>
                  <view class="landing-focus-copy-main">
                    <text class="landing-focus-title">{{ item.title }}</text>
                    <text class="landing-focus-subtitle">{{ item.subtitle }}</text>
                  </view>
                </view>
                <view class="landing-focus-art" aria-hidden="true">
                  <view class="landing-focus-art-card">
                    <text class="landing-focus-art-year">2026</text>
                    <text class="landing-focus-art-label">{{ item.artLabel }}</text>
                    <view class="landing-focus-art-line"></view>
                    <view class="landing-focus-art-line short"></view>
                  </view>
                </view>
              </view>
            </swiper-item>
          </swiper>
          <view class="landing-focus-pagination" aria-label="首页资讯轮播">
            <button
              v-for="(item, index) in homeFocusItems"
              :key="item.title"
              class="landing-focus-dot"
              :class="{ active: homeFocusIndex === index }"
              :aria-label="'切换到：' + item.title"
              @tap="selectHomeFocus(index)"
            ></button>
          </view>
        </view>

        <view v-if="homeNewsItems.length" class="landing-section landing-news-section">
          <view class="landing-section-heading">
            <view>
              <text class="landing-section-title">港澳台考研资讯</text>
            </view>
            <button class="landing-more-button" @tap="openNewsArchive">更多 <text>›</text></button>
          </view>

          <view class="landing-news-list">
            <view
              v-for="(item, index) in homeNewsItems.slice(0, 3)"
              :key="item.title"
              class="landing-news-card"
              :class="index === 0 ? 'is-featured' : ''"
              role="button"
              :aria-label="item.title"
              @tap="openHomeNews(item)"
            >
              <view class="landing-news-copy">
                <text class="landing-news-source">{{ item.source }}</text>
                <text class="landing-news-title">{{ item.title }}</text>
                <text class="landing-news-date">{{ item.date }}</text>
              </view>
              <view class="landing-news-cover" :class="item.coverTone" aria-hidden="true">
                <view class="landing-news-document">
                  <view class="landing-news-document-top">
                    <text>研招</text>
                    <text>官方公告</text>
                  </view>
                  <text class="landing-news-document-title">{{ item.coverLabel }}</text>
                  <view class="landing-news-document-lines">
                    <view></view>
                    <view></view>
                    <view></view>
                  </view>
                </view>
              </view>
            </view>
          </view>
        </view>

        <view class="landing-section landing-services-section">
          <view class="landing-section-heading">
            <view>
              <text class="landing-section-title">报考服务</text>
            </view>
          </view>

          <view class="landing-service-grid">
            <button
              v-for="item in homeServiceItems"
              :key="item.key"
              class="landing-service-card"
              :class="item.tone"
              @tap="openHomeService(item)"
            >
              <view class="landing-service-icon">
                <image
                  class="landing-service-icon-image"
                  :src="getOriginalIconSrc(item.iconSrc)"
                  mode="aspectFit"
                  :alt="item.title"
                />
              </view>
              <view class="landing-service-row">
                <text class="landing-service-title">{{ item.title }}</text>
              </view>
            </button>
          </view>
        </view>

        <!-- #ifdef H5 -->
        <IcpFooter inline />
        <!-- #endif -->
      </view>
    </template>

    <template v-if="activeTab === 'home'">
      <view key="home" class="home-dashboard practice-dashboard">
        <view class="practice-overview-carousel">
          <swiper
            class="practice-overview-swiper"
            :current="practiceOverviewIndex"
            :autoplay="true"
            :interval="5000"
            :duration="420"
            circular
            @change="handlePracticeOverviewChange"
          >
            <swiper-item>
              <view
                class="welcome-card practice-data-card"
                role="button"
                aria-label="查看详细刷题数据"
                @tap="goLeaderboard"
              >
                <view class="practice-data-header">
                  <text class="practice-data-title">我的刷题数据</text>
                  <view class="practice-data-period" aria-hidden="true">
                    <text>本周数据</text>
                  </view>
                </view>

                <view class="practice-data-overview">
                  <view
                    class="practice-accuracy-ring"
                    :class="{ 'is-animating': practiceStatsAnimating }"
                    :style="{ '--practice-ring-progress': `${practiceStats.accuracyProgress}%` }"
                    aria-label="总正确率"
                  >
                    <!-- #ifdef H5 -->
                    <svg class="practice-accuracy-svg" viewBox="0 0 100 100" aria-hidden="true">
                      <circle class="practice-accuracy-track" cx="50" cy="50" r="43" pathLength="100" />
                      <circle
                        class="practice-accuracy-progress"
                        cx="50"
                        cy="50"
                        r="43"
                        pathLength="100"
                        stroke-dasharray="100"
                        :stroke-dashoffset="practiceStats.accuracyOffset"
                      />
                    </svg>
                    <!-- #endif -->
                    <!-- #ifndef H5 -->
                    <view class="practice-accuracy-app-ring" aria-hidden="true"></view>
                    <!-- #endif -->
                    <view class="practice-accuracy-copy">
                      <text class="practice-accuracy-value">{{ practiceStats.accuracy }}</text>
                      <text class="practice-accuracy-label">总正确率</text>
                    </view>
                  </view>

                  <view class="practice-key-metrics">
                    <view class="practice-key-metric">
                      <view class="practice-key-copy">
                        <text class="practice-key-value">{{ practiceStats.weeklyAnswers }}</text>
                        <text class="practice-key-label">本周刷题</text>
                      </view>
                    </view>
                    <view class="practice-key-metric">
                      <view class="practice-key-copy">
                        <text class="practice-key-value">{{ practiceStats.accuracy }}</text>
                        <text class="practice-key-label">总正确率</text>
                      </view>
                    </view>
                    <view class="practice-key-metric">
                      <view class="practice-key-copy">
                        <text class="practice-key-value">{{ practiceStats.wrongCount }}</text>
                        <text class="practice-key-label">错题数</text>
                      </view>
                    </view>
                  </view>
                </view>

                <view class="practice-data-link" aria-hidden="true">
                  <text>查看详细数据</text>
                  <text class="practice-data-link-arrow">›</text>
                </view>
              </view>
            </swiper-item>

            <swiper-item>
              <view
                class="welcome-card daily-rank-preview-card"
                role="button"
                aria-label="查看今日学习榜"
                @tap="goDailyLeaderboard"
              >
                <view class="daily-rank-preview-header">
                  <view>
                    <text class="practice-data-title">今日学习榜</text>
                    <text class="daily-rank-preview-subtitle">按有效刷题时长排名</text>
                  </view>
                  <view class="daily-rank-preview-live"><view></view><text>实时更新</text></view>
                </view>

                <view v-if="dailyLeaderboardLoading && !dailyLeaderboardLoaded" class="daily-rank-preview-state">
                  正在同步今日排名…
                </view>
                <view v-else-if="dailyLeaderboardError && !dailyLeaderboardLoaded" class="daily-rank-preview-state is-error">
                  {{ dailyLeaderboardError }}
                </view>
                <view v-else-if="!dailyLeaderboardItems.length" class="daily-rank-preview-state">
                  今天还没有学习记录，完成一道题即可上榜
                </view>
                <view v-else class="daily-rank-preview-list">
                  <view v-for="item in dailyLeaderboardItems" :key="item.userId" class="daily-rank-preview-row">
                    <view
                      class="daily-rank-preview-position"
                      :class="{ 'has-medal': item.rank >= 1 && item.rank <= 3 }"
                      aria-hidden="true"
                    >
                      <image
                        v-if="item.rank >= 1 && item.rank <= 3"
                        class="daily-rank-preview-medal"
                        :src="getDailyRankMedalIcon(item.rank)"
                        mode="aspectFit"
                      />
                      <text v-else>{{ item.rank }}</text>
                    </view>
                    <view class="daily-rank-preview-avatar" aria-hidden="true">
                      <image v-if="item.avatarUrl" :src="item.avatarUrl" mode="aspectFill" />
                      <text v-else>{{ getDailyRankAvatarText(item.nickname) }}</text>
                    </view>
                    <view class="daily-rank-preview-user">
                      <text>{{ item.nickname }}</text>
                      <text class="daily-rank-preview-answer-count">今日 {{ item.answerCount }} 题</text>
                    </view>
                    <text class="daily-rank-preview-duration">{{ formatDailyRankDuration(item.studySeconds) }}</text>
                  </view>
                </view>

                <view class="daily-rank-preview-footer">
                  <text>{{ dailyLeaderboardMyRankLabel }}</text>
                  <view><text>查看完整榜单</text><text class="practice-data-link-arrow">›</text></view>
                </view>
              </view>
            </swiper-item>
          </swiper>
          <view class="practice-overview-pagination" aria-label="刷题数据卡片轮播">
            <button
              v-for="index in 2"
              :key="index"
              class="practice-overview-dot"
              :class="{ active: practiceOverviewIndex === index - 1 }"
              :aria-label="`切换到第${index}张卡片`"
              hover-class="none"
              @tap="selectPracticeOverview(index - 1)"
            ></button>
          </view>
        </view>

        <view class="practice-entry-list">
          <ModuleCard
            v-for="(item, index) in moduleCards"
            :key="item.key"
            :item="item"
            :index="index + 1"
            :theme-key="selectedThemeKey"
            @select="goModule"
          />
          <view class="mock-exam-card" @tap="openMockExamIntro">
            <view class="mock-exam-main">
              <view class="mock-exam-icon" aria-hidden="true">
                <image
                  class="mock-exam-icon-image"
                  :src="getThemeIconSrc('/static/ui-icons/png/original/mock-paper-logo.png', selectedThemeKey)"
                  mode="aspectFit"
                />
              </view>
              <view class="mock-exam-copy">
                <view class="mock-exam-title">模拟卷</view>
                <view class="mock-exam-sub">55 题 · 105 分 · {{ examCode }} 轻量组卷</view>
              </view>
            </view>
            <view class="mock-exam-arrow" aria-hidden="true">›</view>
          </view>
        </view>

      </view>
    </template>

    <template v-if="activeTab === 'circle'">
      <view key="circle" class="circle-dashboard">
        <view class="circle-view-stage">
        <view
          v-if="circleOverviewVisible"
          key="circle-overview"
          class="circle-overview circle-view-panel"
          :class="{ 'is-app-route-underlay': circleAppRouteUnderlay }"
          :style="circleOverviewRouteStyle"
        >
          <swiper
            v-if="!circleAppRouteUnderlay"
            class="circle-insight-swiper"
            :current="circleInsightIndex"
            :autoplay="!isCircleScoreSwiperPaused"
            :interval="5000"
            :duration="420"
            circular
            @change="handleCircleInsightChange"
          >
            <swiper-item>
              <view class="circle-trend-card circle-glass-surface">
                <view class="circle-trend-heading">
                  <view class="circle-trend-title">刷题人数</view>
                  <view class="circle-trend-peak">
                    <text>峰值 </text>
                    <text class="circle-trend-peak-value">{{ circleTrendPeakLabel }}</text>
                    <text> 人</text>
                  </view>
                </view>
                <view v-if="circleTrendLoading && !circleTrendLoaded" class="circle-trend-state">
                  正在同步真实刷题人数…
                </view>
                <view v-else-if="circleTrendError && !circleTrendLoaded" class="circle-trend-state is-error">
                  <text>{{ circleTrendError }}</text>
                  <button hover-class="none" @tap="loadCirclePracticeTrend({ force: true })">重新加载</button>
                </view>
                <view v-else class="circle-trend-chart" aria-label="近 7 天刷题人数统计图">
                  <view class="circle-trend-grid" aria-hidden="true">
                    <view v-for="label in circleTrendAxis" :key="label" class="circle-trend-grid-line"></view>
                  </view>
                  <view class="circle-trend-axis" aria-hidden="true">
                    <text v-for="label in circleTrendAxis" :key="label">{{ label }}</text>
                  </view>
                  <view class="circle-trend-bars">
                    <view v-for="item in circlePracticeTrend" :key="item.day" class="circle-trend-column">
                      <view class="circle-trend-bar-space">
                        <view
                          class="circle-trend-bar"
                          :class="{ latest: item.latest, empty: item.count <= 0 }"
                          :style="{ height: getCircleTrendHeight(item.count) }"
                        >
                          <text class="circle-trend-value">{{ item.count }}</text>
                        </view>
                      </view>
                      <text class="circle-trend-day">{{ item.day }}</text>
                    </view>
                  </view>
                </view>
              </view>
            </swiper-item>

            <swiper-item>
              <view
                class="circle-score-card circle-glass-surface"
                role="button"
                :aria-label="`查看${getScoreLineRecordDisplayName(activeCircleScoreSchool)}历年分数线`"
                @tap="handleCircleScoreCardTap(activeCircleScoreSchool)"
              >
                <view class="circle-score-heading">
                  <view class="circle-score-copy">
                    <view class="circle-score-title">{{ getScoreLineSchoolName(activeCircleScoreSchool) }}</view>
                    <view v-if="activeCircleScoreSchool?.unitName" class="circle-score-subtitle">
                      {{ activeCircleScoreSchool.unitName }}
                    </view>
                  </view>
                  <view class="circle-score-total">总分 <text>150</text></view>
                </view>
                <view class="circle-score-chart" :aria-label="`${getScoreLineRecordDisplayName(activeCircleScoreSchool)}历年分数线`">
                  <view class="circle-score-axis" aria-hidden="true">
                    <text v-for="label in activeCircleScoreChart.axis" :key="label">{{ label }}</text>
                  </view>
                  <!-- #ifdef APP-PLUS -->
                  <CanvasLineChart
                    class="circle-score-canvas"
                    canvas-id="circle-score-overview-canvas"
                    :points="activeCircleScoreCanvasPoints"
                    :grid-y="activeCircleScoreChart.gridY"
                    :line-color="currentTheme.primary"
                    :point-stroke="currentTheme.primary"
                    :active-index="circleScoreOverviewActiveIndex"
                    interactive
                    @point-touch-start="startCircleScorePointHold('overview', $event)"
                    @point-touch-move="cancelCircleScorePointHold"
                    @point-touch-end="finishCircleScorePointHold"
                    @point-tap="showCircleScorePointTooltip('overview', $event)"
                  />
                  <!-- #endif -->
                  <!-- #ifndef APP-PLUS -->
                  <svg class="circle-score-svg" viewBox="0 0 300 112" preserveAspectRatio="none" aria-hidden="true">
                    <line v-for="y in activeCircleScoreChart.gridY" :key="y" x1="30" x2="292" :y1="y" :y2="y" class="circle-score-grid-line" />
                    <polyline :points="circleScoreLinePoints" class="circle-score-line" />
                    <g v-for="(score, index) in activeCircleScoreValues" :key="circleScoreYears[index]">
                      <g
                        class="circle-score-point-hit"
                        @touchstart.stop="startCircleScorePointHold('overview', index)"
                        @touchmove.stop="cancelCircleScorePointHold"
                        @touchend.stop="finishCircleScorePointHold"
                        @touchcancel.stop="finishCircleScorePointHold"
                        @mousedown.stop="startCircleScorePointHold('overview', index)"
                        @mouseup.stop="finishCircleScorePointHold"
                        @mouseleave.stop="finishCircleScorePointHold"
                        @tap.stop="showCircleScorePointTooltip('overview', index)"
                        @click.stop="showCircleScorePointTooltip('overview', index)"
                        @contextmenu.prevent.stop
                      >
                        <circle :cx="circleScoreX[index]" :cy="getCircleScoreY(score, activeCircleScoreChart)" r="13" class="circle-score-point-hit-area" />
                        <circle
                          :cx="circleScoreX[index]"
                          :cy="getCircleScoreY(score, activeCircleScoreChart)"
                          r="4.5"
                          class="circle-score-point"
                          :class="{ 'is-active': isCircleScorePointTooltipVisible('overview', index) }"
                        />
                      </g>
                    </g>
                  </svg>
                  <!-- #endif -->
                  <view class="circle-score-tooltip-layer" aria-hidden="true">
                    <template v-for="(score, index) in activeCircleScoreValues" :key="circleScoreYears[index]">
                      <view
                        v-if="isCircleScorePointTooltipVisible('overview', index)"
                        class="circle-score-tooltip"
                        :style="getCircleScoreTooltipStyle(circleScoreX[index], score, activeCircleScoreChart)"
                      >
                        {{ score }}分
                      </view>
                    </template>
                  </view>
                  <view class="circle-score-years" aria-hidden="true">
                    <text v-for="year in circleScoreYears" :key="year">{{ year }}</text>
                  </view>
                </view>
              </view>
            </swiper-item>
          </swiper>
          <view
            v-else
            class="circle-insight-swiper circle-insight-route-mirror"
            aria-hidden="true"
          >
            <view v-if="circleInsightIndex === 0" class="circle-trend-card circle-glass-surface">
              <view class="circle-trend-heading">
                <view class="circle-trend-title">刷题人数</view>
                <view class="circle-trend-peak">
                  <text>峰值 </text>
                  <text class="circle-trend-peak-value">{{ circleTrendPeakLabel }}</text>
                  <text> 人</text>
                </view>
              </view>
              <view class="circle-trend-chart" aria-hidden="true">
                <view class="circle-trend-grid">
                  <view v-for="label in circleTrendAxis" :key="label" class="circle-trend-grid-line"></view>
                </view>
                <view class="circle-trend-axis">
                  <text v-for="label in circleTrendAxis" :key="label">{{ label }}</text>
                </view>
                <view class="circle-trend-bars">
                  <view v-for="item in circlePracticeTrend" :key="item.day" class="circle-trend-column">
                    <view class="circle-trend-bar-space">
                      <view
                        class="circle-trend-bar"
                        :class="{ latest: item.latest, empty: item.count <= 0 }"
                        :style="{ height: getCircleTrendHeight(item.count) }"
                      >
                        <text class="circle-trend-value">{{ item.count }}</text>
                      </view>
                    </view>
                    <text class="circle-trend-day">{{ item.day }}</text>
                  </view>
                </view>
              </view>
            </view>

            <view v-else class="circle-score-card circle-glass-surface">
              <view class="circle-score-heading">
                <view class="circle-score-copy">
                  <view class="circle-score-title">{{ getScoreLineSchoolName(activeCircleScoreSchool) }}</view>
                  <view v-if="activeCircleScoreSchool?.unitName" class="circle-score-subtitle">
                    {{ activeCircleScoreSchool.unitName }}
                  </view>
                </view>
                <view class="circle-score-total">总分 <text>150</text></view>
              </view>
              <view class="circle-score-chart">
                <view class="circle-score-axis">
                  <text v-for="label in activeCircleScoreChart.axis" :key="label">{{ label }}</text>
                </view>
                <view class="circle-score-mirror-plot">
                  <view
                    v-for="(line, index) in circleScoreMirrorGridLines"
                    :key="`grid-${index}`"
                    class="circle-score-mirror-grid-line"
                    :style="line"
                  ></view>
                  <view
                    v-for="(segment, index) in circleScoreMirrorSegments"
                    :key="`segment-${index}`"
                    class="circle-score-mirror-segment"
                    :style="segment"
                  ></view>
                  <view
                    v-for="(point, index) in circleScoreMirrorPoints"
                    :key="`point-${index}`"
                    class="circle-score-mirror-point"
                    :style="point"
                  ></view>
                </view>
                <view class="circle-score-years">
                  <text v-for="year in circleScoreYears" :key="year">{{ year }}</text>
                </view>
              </view>
            </view>
          </view>
          <view class="circle-insight-pagination" aria-label="数据卡片轮播">
            <button
              v-for="index in 2"
              :key="index"
              class="circle-insight-dot"
              :class="{ active: circleInsightIndex === index - 1 }"
              :aria-label="`切换到第${index}张数据卡片`"
              @tap="selectCircleInsight(index - 1)"
            ></button>
          </view>

          <view class="circle-entry-list circle-glass-group">
            <button
              v-for="item in circleSections"
              :key="item.key"
              class="circle-entry"
              :aria-label="`进入${item.label}`"
              @tap="openCircleSection(item.key)"
            >
              <view class="circle-entry-icon">
                <image
                  class="circle-entry-icon-image"
                  :src="getThemeIconSrc(item.iconSrc, selectedThemeKey)"
                  mode="aspectFit"
                />
              </view>
              <text class="circle-entry-label">{{ item.label }}</text>
              <text v-if="getCircleSectionUnreadCount(item.key)" class="circle-entry-unread-count">
                {{ formatUnreadBadge(getCircleSectionUnreadCount(item.key)) }}
              </text>
              <view class="circle-entry-arrow" aria-hidden="true">›</view>
            </button>
          </view>
        </view>
        </view>

        <view
          v-if="circleDetailMounted"
          key="circle-detail"
          class="circle-detail-route-layer"
          :class="{
            'is-scoreline-browser': isScoreLineBrowser,
            'is-route-compositor-safe': selectedCircleSection !== 'scores',
            'is-community-reader-underlay': Boolean(selectedCommunityPost),
            'is-route-moving': circleDetailRouteMotion !== 'idle' && circleDetailRouteMotion !== 'dragging',
            'is-route-dragging': circleDetailRouteMotion === 'dragging',
            'is-route-settling': circleDetailRouteMotion === 'drag-cancelling' || circleDetailRouteMotion === 'drag-leaving',
            'is-route-offscreen': circleDetailRouteMotion === 'enter-from' || circleDetailRouteMotion === 'leaving'
          }"
          :style="circleDetailRouteStyle"
          @touchstart="beginCircleEdgeSwipe"
          @touchmove.stop="moveCircleEdgeSwipe"
          @touchend="finishCircleEdgeSwipe"
          @touchcancel="cancelCircleEdgeSwipe"
          @mousedown="beginCircleEdgeSwipe"
          @transitionend="handleCircleDetailRouteTransitionEnd"
        >
          <view class="circle-detail-header circle-detail-route-header" :style="circleCommunityHeaderStyle">
            <button
              class="circle-back-button"
              :aria-label="selectedScoreLineRecord ? (selectedScoreLineRecordEntry === 'overview' ? '返回研圈首页' : '返回分数线列表') : '返回研圈首页'"
              @tap="handleCircleDetailBack"
            >
              <image src="/static/ui-icons/png/original/back.png" mode="aspectFit" />
            </button>
            <view class="circle-detail-heading">{{ selectedCircleSectionLabel }}</view>
            <button
              v-if="selectedCircleSection === 'community'"
              class="circle-my-verification-entry"
              aria-label="查看我的前辈认证"
              @tap.stop="openMentorVerificationEntry()"
            >
              我的认证
            </button>
            <view v-else class="circle-detail-header-spacer"></view>
          </view>

          <scroll-view
            class="circle-detail-route-scroll"
            scroll-y
            :scroll-top="circleDetailScrollTop"
            :show-scrollbar="false"
            :lower-threshold="120"
            @scroll="handleCircleDetailScroll"
            @scrolltolower="handleCircleDetailReachBottom"
          >
          <view class="circle-detail-page circle-view-panel circle-detail-route-content">

          <view v-if="selectedCircleSection === 'community'" class="circle-section circle-community-section">
            <view class="circle-community-tabs circle-glass-group" role="tablist" aria-label="考研圈栏目">
              <button
                v-for="item in circleCommunityTabs"
                :key="item.key"
                class="circle-community-tab"
                :class="{ active: selectedCircleCommunityTab === item.key }"
                :aria-selected="selectedCircleCommunityTab === item.key"
                @tap="selectCircleCommunityTab(item.key)"
              >
                <text>{{ item.label }}</text>
                <text v-if="getCircleCommunityTabUnreadCount(item.key)" class="circle-community-tab-unread">
                  {{ formatUnreadBadge(getCircleCommunityTabUnreadCount(item.key)) }}
                </text>
              </button>
            </view>

            <template v-if="selectedCircleCommunityTab === 'mentor'">
              <view
                v-if="applicantConsultationUnreadCount || mentorConsultationUnreadCount"
                class="mentor-unread-entry-list"
                aria-label="前辈咨询新动态"
              >
                <button
                  v-if="applicantConsultationUnreadCount"
                  class="mentor-unread-entry"
                  @tap="openApplicantConsultationUpdates"
                >
                  <view class="mentor-unread-entry-dot"></view>
                  <view class="mentor-unread-entry-copy">
                    <strong>我的咨询</strong>
                    <text>{{ applicantConsultationUnreadCount }} 条新动态，查看具体咨询</text>
                  </view>
                  <view class="mentor-unread-entry-arrow">›</view>
                </button>
                <button
                  v-if="mentorConsultationUnreadCount"
                  class="mentor-unread-entry"
                  @tap="openMentorConsultationUpdates"
                >
                  <view class="mentor-unread-entry-dot"></view>
                  <view class="mentor-unread-entry-copy">
                    <strong>咨询主页</strong>
                    <text>{{ mentorConsultationUnreadCount }} 条待查看动态</text>
                  </view>
                  <view class="mentor-unread-entry-arrow">›</view>
                </button>
              </view>

              <view class="experience-search circle-glass-group mentor-search">
                <AppSearchIcon class="experience-search-icon" />
                <input
                  v-model="mentorSearchKeyword"
                  class="experience-search-input"
                  placeholder="搜索院校、专业或前辈"
                  placeholder-class="experience-search-placeholder"
                  confirm-type="search"
                />
                <button
                  v-if="mentorSearchKeyword"
                  class="experience-search-clear"
                  aria-label="清除前辈搜索"
                  @tap.stop="mentorSearchKeyword = ''"
                >
                  <CloseIcon />
                </button>
                <picker
                  class="community-post-sort-picker"
                  mode="selector"
                  :range="mentorSortOptions"
                  range-key="label"
                  :value="mentorSortIndex"
                  @change="selectMentorSort"
                >
                  <view class="community-post-sort-control mentor-sort-control" role="button" :aria-label="`前辈排序：${activeMentorSortLabel}`">
                    <text>{{ activeMentorSortLabel }}</text>
                    <view class="community-post-sort-arrow" aria-hidden="true"></view>
                  </view>
                </picker>
                <button
                  class="mentor-filter-trigger mentor-search-filter-trigger"
                  :class="{ 'has-filters': mentorActiveFilterCount > 0 }"
                  :aria-label="mentorActiveFilterCount ? `筛选前辈，已选 ${mentorActiveFilterCount} 项` : '筛选前辈'"
                  @tap="openMentorFilterSheet"
                >
                  <view class="mentor-filter-trigger-icon" aria-hidden="true"><view></view><view></view><view></view></view>
                  <text v-if="mentorActiveFilterCount" class="mentor-filter-trigger-count">{{ mentorActiveFilterCount }}</text>
                </button>
              </view>

              <view class="mentor-feed mentor-directory-grid">
                <MentorConsultCard
                  v-for="mentor in filteredMentors"
                  :key="mentor.id"
                  :mentor="mentor"
                  :favorite="mentorFavoriteIds.includes(mentor.id)"
                  :favorite-pending="mentorFavoritePendingIds.includes(mentor.id)"
                  :view-only="isCurrentMentorProfile(mentor)"
                  @open="openMentorDetail(mentor)"
                  @consult="beginMentorConsultation(mentor)"
                  @toggle-favorite="toggleMentorFavoriteState(mentor.id)"
                />
                <AppPageLoadingState
                  v-if="mentorProfilesLoading && mentorProfiles.length === 0"
                  class="mentor-directory-state"
                  message="正在整理前辈咨询..."
                />
                <view v-else-if="mentorProfilesError && mentorProfiles.length === 0" class="circle-empty-card mentor-empty-card">
                  <view class="circle-empty-title">前辈资料暂时不可用</view>
                  <view class="circle-empty-copy">平台不会展示未验证的示例前辈，请检查网络后重新加载。</view>
                  <button class="mentor-empty-reset" @tap="retryMentorProfiles">重新加载</button>
                </view>
                <AppEmptyState
                  v-else-if="filteredMentors.length === 0"
                  class="mentor-directory-state"
                  :label="mentorHasActiveSearch ? '暂时没有匹配的前辈' : '暂时没有可咨询的认证前辈'"
                  :title="mentorHasActiveSearch ? '暂时没有匹配的前辈' : '暂时没有可咨询的认证前辈'"
                  :description="mentorHasActiveSearch ? '可以尝试调整搜索关键词或筛选条件。' : '请稍后再来查看，或先申请成为认证前辈。'"
                >
                  <button v-if="mentorHasActiveSearch" class="mentor-empty-reset" @tap="resetMentorFilters">清除筛选</button>
                </AppEmptyState>
              </view>

            </template>

            <template v-else-if="selectedCircleCommunityTab">
              <button
                v-if="getCircleCommunityTabUnreadCount(selectedCircleCommunityTab)"
                class="community-unread-entry"
                @tap="openMyPostUpdates(selectedCircleCommunityTab)"
              >
                <view class="mentor-unread-entry-dot"></view>
                <text>{{ getCircleCommunityTabUnreadCount(selectedCircleCommunityTab) }} 条新互动来自你的帖子</text>
                <strong>查看 ›</strong>
              </button>

              <view class="experience-search circle-glass-group">
                <AppSearchIcon class="experience-search-icon" />
                <input
                  v-model="activeCommunitySearchKeyword"
                  class="experience-search-input"
                  :placeholder="selectedCircleCommunityTab === 'experience' ? '搜索经验贴' : '搜索研友聊'"
                  placeholder-class="experience-search-placeholder"
                  confirm-type="search"
                  @input="scheduleActiveCommunitySearch"
                  @confirm="submitActiveCommunitySearch"
                />
                <button
                  v-if="activeCommunitySearchKeyword"
                  class="experience-search-clear"
                  aria-label="清除搜索"
                  @tap.stop="clearActiveCommunitySearch"
                >
                  <CloseIcon />
                </button>
                <picker
                  class="community-post-sort-picker"
                  mode="selector"
                  :range="communityPostSortOptions"
                  range-key="label"
                  :value="communityPostSortIndex"
                  @change="selectCommunityPostSort"
                >
                  <view
                    class="community-post-sort-control"
                    role="button"
                    :aria-label="`帖子排序：${activeCommunityPostSortLabel}`"
                  >
                    <text>{{ activeCommunityPostSortLabel }}</text>
                    <view class="community-post-sort-arrow" aria-hidden="true"></view>
                  </view>
                </picker>
              </view>

              <scroll-view scroll-x class="community-filter-scroll">
                <view class="community-filter-row circle-glass-group">
                  <button
                    v-for="item in activeCommunityCategories"
                    :key="item"
                    class="community-filter-chip"
                    :class="{ active: activeCommunityCategory === item }"
                    @tap="selectActiveCommunityCategory(item)"
                  >
                    {{ item }}
                  </button>
                </view>
              </scroll-view>

              <view
                class="community-feed community-stream"
                :class="{
                  'is-empty': !activeCommunityLoadError
                    && filteredActiveCommunityPosts.length === 0
                }"
              >
                <view
                  v-for="post in filteredActiveCommunityPosts"
                  :key="post.id"
                  class="community-post-card community-stream-card"
                  :class="{ 'has-unread-interaction': isCommunityPostUnread(post) }"
                  @tap="openCommunityPost(post)"
                >
                  <view class="community-post-header">
                    <view class="community-avatar" :class="`tone-${post.tone}`">
                      <image v-if="post.avatarUrl" class="community-avatar-image" :src="post.avatarUrl" mode="aspectFill" />
                      <text v-else>{{ post.avatar }}</text>
                    </view>
                    <view class="community-author-main">
                      <view class="community-author-name">{{ post.author }}<text v-if="post.authorVerified" class="community-author-verified">已认证</text></view>
                      <view class="community-author-meta">{{ post.publishTime }}</view>
                    </view>
                    <view class="community-stream-header-actions">
                      <view v-if="isCommunityPostUnread(post)" class="community-post-unread-badge">新互动</view>
                      <view class="community-topic-list" :class="{ 'is-experience': post.postType === 'experience' }">
                        <view
                          v-for="tag in getCommunityPostTags(post)"
                          :key="`${post.id}-${tag}`"
                          class="community-topic"
                        >{{ tag }}</view>
                      </view>
                      <button class="community-post-more" aria-label="帖子更多操作" @tap.stop="openCommunityPostActions(post)">
                        <image src="/static/ui-icons/png/original/more.png" mode="aspectFit" />
                      </button>
                    </view>
                  </view>

                  <view class="community-post-title">{{ post.title }}</view>
                  <view class="community-post-copy">{{ post.summary }}</view>

                  <view v-if="post.media.length" class="community-media-grid" :class="`count-${Math.min(post.media.length, 2)}`">
                    <view
                      v-for="(media, mediaIndex) in post.media.slice(0, 2)"
                      :key="media.imageUrl || media.image_url || `${media.kicker}-${media.title}`"
                      class="community-media-tile"
                      :class="[`tone-${media.tone}`, { 'is-image': media.imageUrl || media.image_url }]"
                    >
                      <image
                        v-if="media.imageUrl || media.image_url"
                        class="community-media-image"
                        :src="media.thumbnailUrl || media.thumbnail_url || media.imageUrl || media.image_url"
                        mode="aspectFill"
                        lazy-load
                      />
                      <view v-else class="community-media-text">
                        <view class="community-media-kicker">{{ media.kicker }}</view>
                        <view class="community-media-title">{{ media.title }}</view>
                        <view class="community-media-copy">{{ media.copy }}</view>
                      </view>
                      <view v-if="post.mediaCount > 2 && mediaIndex === 1" class="community-media-more">+{{ post.mediaCount - 2 }}</view>
                    </view>
                  </view>

                  <view v-if="post.commentPreviews.length" class="community-comment-preview-list">
                    <view
                      v-for="comment in post.commentPreviews.slice(0, 1)"
                      :key="comment.id"
                      class="community-comment-preview"
                      @tap.stop="openCommunityPostComments(post)"
                    >
                      <text class="community-comment-name">{{ comment.author }}：</text>
                      <text class="community-comment-preview-copy">{{ comment.text }}</text>
                    </view>
                  </view>

                  <view class="community-post-footer">
                    <button
                      class="community-post-action"
                      :class="{ active: post.liked, pending: isCommunityPostLikePending(post.id) }"
                      :aria-label="post.liked ? '取消点赞' : '点赞'"
                      :aria-pressed="post.liked"
                      :aria-busy="isCommunityPostLikePending(post.id)"
                      @tap.stop="toggleCommunityLike(post)"
                    >
                      <image
                        class="community-action-icon"
                        :src="post.liked ? communityLikeFilledIconSrc : communityLikeIconSrc"
                        mode="aspectFit"
                      />
                      <text>{{ post.stats.likes }}</text>
                    </button>
                    <button
                      class="community-post-action"
                      aria-label="查看并评论"
                      @tap.stop="openCommunityPostComments(post)"
                    >
                      <image class="community-action-icon" src="/static/ui-icons/png/original/circle-comment.png" mode="aspectFit" />
                      <text>{{ post.stats.comments }}</text>
                    </button>
                  </view>
                </view>

                <AppPageLoadingState
                  v-if="activeCommunityLoading && filteredActiveCommunityPosts.length === 0"
                  class="community-feed-state"
                  :message="selectedCircleCommunityTab === 'experience' ? '正在整理经验贴...' : '正在整理研友聊...'"
                />
                <AppEmptyState
                  v-else-if="activeCommunityLoadError && filteredActiveCommunityPosts.length === 0"
                  class="community-feed-state"
                  label="帖子加载失败"
                  title="暂时没有加载出来"
                  :description="activeCommunityLoadError"
                >
                  <button @tap="retryActiveCommunityFeed">重新加载</button>
                </AppEmptyState>
                <AppEmptyState
                  v-else-if="filteredActiveCommunityPosts.length === 0"
                  class="community-feed-state"
                />
                <view
                  v-if="(activeCommunityLoading && filteredActiveCommunityPosts.length > 0) || activeCommunityLoadError || activeCommunityHasMore"
                  class="community-load-state"
                  @tap="activeCommunityLoadError ? retryActiveCommunityFeed() : loadMoreCircleCommunityPosts()"
                >
                  {{ activeCommunityLoading ? '正在加载更多帖子…' : (activeCommunityLoadError ? '加载失败，点击重试' : '继续下滑加载更多帖子') }}
                </view>
              </view>

            </template>

            <template v-else>
              <view class="experience-search circle-glass-group">
                <AppSearchIcon class="experience-search-icon" />
                <input
                  v-model="experienceSearchKeyword"
                  class="experience-search-input"
                  placeholder="搜索经验贴"
                  placeholder-class="experience-search-placeholder"
                  confirm-type="search"
                />
                <button
                  v-if="experienceSearchKeyword"
                  class="experience-search-clear"
                  aria-label="清除搜索"
                  @tap.stop="clearExperienceSearch"
                >
                  <CloseIcon />
                </button>
              </view>

              <scroll-view scroll-x class="experience-filter-scroll">
                <view class="experience-filter-row circle-glass-group">
                  <button
                    v-for="item in circleExperienceCategories"
                    :key="item"
                    class="experience-filter-chip"
                    :class="{ active: selectedExperienceCategory === item }"
                    @tap="selectExperienceCategory(item)"
                  >
                    {{ item }}
                  </button>
                </view>
              </scroll-view>

              <view
                v-for="post in filteredCircleExperiencePosts"
                :key="post.id"
                class="experience-card"
                @tap="openCirclePost(post)"
              >
                <view class="experience-author-row">
                  <view class="experience-avatar">
                    <image v-if="post.avatarUrl" class="experience-avatar-image" :src="post.avatarUrl" mode="aspectFill" />
                    <text v-else>{{ post.avatar }}</text>
                  </view>
                  <view class="experience-author-main">
                    <view class="experience-author-name">{{ post.author }}</view>
                    <view class="experience-author-role">{{ post.authorRole }} · {{ post.publishDate }}</view>
                  </view>
                  <view class="experience-exam">{{ post.subject }}</view>
                </view>
                <view class="experience-title">{{ post.title }}</view>
                <view class="experience-summary">{{ post.summary }}</view>
                <view class="experience-points">
                  <text v-for="point in post.points" :key="point">{{ point }}</text>
                </view>
                <view class="experience-footer">
                  <view class="experience-stats">
                    <text>{{ post.stats.likes }} 赞</text>
                    <text>{{ post.stats.saves }} 收藏</text>
                  </view>
                </view>
              </view>

              <AppEmptyState
                v-if="filteredCircleExperiencePosts.length === 0"
                label="暂无匹配的经验贴"
                title="暂无匹配的经验贴"
                description="换个关键词或分类试试。"
              />
            </template>
          </view>

          <view v-else-if="selectedCircleSection === 'scores'" class="circle-section circle-scoreline-section">
            <template v-if="selectedScoreLineRecord">
              <view class="scoreline-detail-toolbar">
                <text class="scoreline-detail-source">数据来源：2024-2026 年历年分数线</text>
              </view>

              <view class="scoreline-detail-card circle-glass-surface">
                <view class="scoreline-detail-school-row">
                  <view>
                    <view class="scoreline-detail-school">{{ getScoreLineSchoolName(selectedScoreLineRecord) }}</view>
                    <view class="scoreline-detail-meta">
                      {{ selectedScoreLineRecord.region }}地区
                      <text v-if="selectedScoreLineRecord.unitName"> · {{ selectedScoreLineRecord.unitName }}</text>
                    </view>
                  </view>
                  <view class="scoreline-detail-region">{{ selectedScoreLineRecord.region }}</view>
                </view>

                <view v-if="hasCompleteScoreLineTrend(selectedScoreLineRecord)" class="scoreline-detail-chart">
                  <view class="scoreline-detail-chart-title">三年总分趋势</view>
                  <view class="scoreline-detail-chart-plot">
                    <view class="circle-score-axis" aria-hidden="true">
                      <text v-for="label in selectedScoreLineChart.axis" :key="label">{{ label }}</text>
                    </view>
                    <!-- #ifdef APP-PLUS -->
                    <CanvasLineChart
                      class="circle-score-canvas"
                      canvas-id="circle-score-detail-canvas"
                      :points="selectedScoreLineCanvasPoints"
                      :grid-y="selectedScoreLineChart.gridY"
                      :line-color="currentTheme.primary"
                      :point-stroke="currentTheme.primary"
                      :active-index="circleScoreDetailActiveIndex"
                      interactive
                      @point-touch-start="startCircleScorePointHold('detail', $event)"
                      @point-touch-move="cancelCircleScorePointHold"
                      @point-touch-end="finishCircleScorePointHold"
                      @point-tap="showCircleScorePointTooltip('detail', $event)"
                    />
                    <!-- #endif -->
                    <!-- #ifndef APP-PLUS -->
                    <svg class="circle-score-svg" viewBox="0 0 300 112" preserveAspectRatio="none" aria-hidden="true">
                      <line v-for="y in selectedScoreLineChart.gridY" :key="y" x1="30" x2="292" :y1="y" :y2="y" class="circle-score-grid-line" />
                      <polyline :points="scoreLineDetailLinePoints" class="circle-score-line" />
                      <g v-for="(score, index) in selectedScoreLineValues" :key="circleScoreYears[index]">
                        <g
                          class="circle-score-point-hit"
                          @touchstart.stop="startCircleScorePointHold('detail', index)"
                          @touchmove.stop="cancelCircleScorePointHold"
                          @touchend.stop="finishCircleScorePointHold"
                          @touchcancel.stop="finishCircleScorePointHold"
                          @mousedown.stop="startCircleScorePointHold('detail', index)"
                          @mouseup.stop="finishCircleScorePointHold"
                          @mouseleave.stop="finishCircleScorePointHold"
                          @tap.stop="showCircleScorePointTooltip('detail', index)"
                          @click.stop="showCircleScorePointTooltip('detail', index)"
                          @contextmenu.prevent.stop
                        >
                          <circle :cx="circleScoreX[index]" :cy="getCircleScoreY(score, selectedScoreLineChart)" r="13" class="circle-score-point-hit-area" />
                          <circle
                            :cx="circleScoreX[index]"
                            :cy="getCircleScoreY(score, selectedScoreLineChart)"
                            r="4.5"
                            class="circle-score-point"
                            :class="{ 'is-active': isCircleScorePointTooltipVisible('detail', index) }"
                          />
                        </g>
                      </g>
                    </svg>
                    <!-- #endif -->
                    <view class="circle-score-tooltip-layer" aria-hidden="true">
                      <template v-for="(score, index) in selectedScoreLineValues" :key="circleScoreYears[index]">
                        <view
                          v-if="isCircleScorePointTooltipVisible('detail', index)"
                          class="circle-score-tooltip"
                          :style="getCircleScoreTooltipStyle(circleScoreX[index], score, selectedScoreLineChart)"
                        >
                          {{ score }}分
                        </view>
                      </template>
                    </view>
                    <view class="circle-score-years" aria-hidden="true">
                      <text v-for="year in circleScoreYears" :key="year">{{ year }}</text>
                    </view>
                  </view>
                </view>

                <view v-else class="scoreline-detail-note">
                  该校部分年份按专业、院系或学位类型公布，以下保留原始分数线说明。
                </view>

                <view class="scoreline-history-list">
                  <view v-for="year in historicalScoreLineDisplayYears" :key="year" class="scoreline-history-item">
                    <view class="scoreline-history-main">
                      <text class="scoreline-history-year">{{ year }}</text>
                      <text
                        class="scoreline-history-value"
                        :class="{ 'is-note': getScoreLineValue(selectedScoreLineRecord, year).kind !== 'score' }"
                      >
                        {{ getScoreLineDetailValue(selectedScoreLineRecord, year) }}
                      </text>
                    </view>
                    <text
                      v-if="getScoreLineValue(selectedScoreLineRecord, year).raw && getScoreLineValue(selectedScoreLineRecord, year).kind !== 'score'"
                      class="scoreline-history-copy"
                    >
                      {{ getScoreLineValue(selectedScoreLineRecord, year).raw }}
                    </text>
                  </view>
                </view>
              </view>
            </template>

            <view v-else class="scoreline-browser-layout">
              <view class="scoreline-filter-grid">
                <picker
                  class="scoreline-select"
                  mode="selector"
                  :range="scoreLineYearPickerOptions"
                  range-key="label"
                  :value="scoreLineYearPickerIndex"
                  @change="onScoreLineYearPickerChange"
                >
                  <view class="scoreline-select-control">
                    <text class="scoreline-select-name">年份</text>
                    <text class="scoreline-select-value">{{ selectedScoreLineYearCompactLabel }}</text>
                    <image
                      class="scoreline-select-arrow-icon"
                      :src="getThemeIconSrc('/static/ui-icons/png/original/major-catalog-dropdown.png', selectedThemeKey)"
                      mode="aspectFit"
                      aria-hidden="true"
                    />
                  </view>
                </picker>

                <picker
                  class="scoreline-select"
                  mode="selector"
                  :range="scoreLineRegionPickerOptions"
                  range-key="label"
                  :value="scoreLineRegionPickerIndex"
                  @change="onScoreLineRegionPickerChange"
                >
                  <view class="scoreline-select-control">
                    <text class="scoreline-select-name">地区</text>
                    <text class="scoreline-select-value">{{ selectedScoreLineRegionCompactLabel }}</text>
                    <image
                      class="scoreline-select-arrow-icon"
                      :src="getThemeIconSrc('/static/ui-icons/png/original/major-catalog-dropdown.png', selectedThemeKey)"
                      mode="aspectFit"
                      aria-hidden="true"
                    />
                  </view>
                </picker>
              </view>

              <view class="scoreline-search circle-glass-group">
                <AppSearchIcon class="scoreline-search-icon" />
                <input
                  v-model="scoreLineSearchKeyword"
                  class="scoreline-search-input"
                  placeholder="搜索高校或院系"
                  placeholder-class="scoreline-search-placeholder"
                  confirm-type="search"
                />
                <button
                  v-if="scoreLineSearchKeyword"
                  class="scoreline-search-clear"
                  hover-class="none"
                  aria-label="清除搜索"
                  @tap.stop="clearScoreLineSearch"
                >
                  <CloseIcon />
                </button>
              </view>

              <view class="scoreline-results-frame">
                <view class="scoreline-results-heading">
                  <view class="scoreline-results-heading-copy">
                    <text class="scoreline-results-title">院校 / 院系</text>
                    <text class="scoreline-results-count">{{ scoreLineResults.length }} 条结果</text>
                  </view>
                  <button
                    v-if="hasActiveScoreLineFilters"
                    class="scoreline-results-reset"
                    hover-class="none"
                    @tap="resetScoreLineFilters"
                  >
                    重置
                  </button>
                </view>

                <view class="scoreline-results-scroll">
                  <view class="scoreline-results-content">
                    <view v-if="visibleScoreLineRecords.length" class="scoreline-school-list">
                      <button
                        v-for="record in visibleScoreLineRecords"
                        :key="record.id"
                        class="scoreline-school-card"
                        hover-class="none"
                        @tap="openScoreLineRecord(record)"
                      >
                        <view class="scoreline-school-top">
                          <view class="scoreline-school-copy">
                            <text class="scoreline-school-name">{{ getScoreLineSchoolName(record) }}</text>
                            <text v-if="record.unitName" class="scoreline-school-unit">{{ record.unitName }}</text>
                            <text class="scoreline-school-meta">
                              {{ record.region }}地区 · {{ getScoreLineAvailableYearCount(record) }} 年有数据
                            </text>
                          </view>
                          <text class="scoreline-school-arrow" aria-hidden="true">›</text>
                        </view>
                        <view class="scoreline-year-grid">
                          <view v-for="year in historicalScoreLineDisplayYears" :key="year" class="scoreline-year-cell">
                            <text class="scoreline-year-label">{{ year }}</text>
                            <text
                              class="scoreline-year-value"
                              :class="{ 'is-note': getScoreLineValue(record, year).kind !== 'score' }"
                            >
                              {{ getScoreLineCardValue(record, year) }}
                            </text>
                          </view>
                        </view>
                      </button>
                    </view>

                    <AppEmptyState
                      v-else
                      class="scoreline-empty-card"
                      label="没有找到匹配的高校"
                      title="没有找到匹配的高校"
                      description="尝试更换关键词、地区或年份筛选。"
                    />

                    <button
                      v-if="visibleScoreLineRecords.length < scoreLineResults.length"
                      class="scoreline-load-more"
                      hover-class="none"
                      @tap="loadMoreScoreLineRecords"
                    >
                      加载更多（已显示 {{ visibleScoreLineRecords.length }} / {{ scoreLineResults.length }}）
                    </button>
                  </view>
                </view>
              </view>
            </view>
          </view>

          <view v-else-if="selectedCircleSection === 'materials'" class="circle-section circle-resource-empty-section">
            <CircleResourceSection resource-type="material" />
          </view>

          <view v-else-if="selectedCircleSection === 'courses'" class="circle-section circle-resource-empty-section">
            <CircleResourceSection resource-type="course" />
          </view>
          </view>
          </scroll-view>
        </view>
      </view>
    </template>

    <template v-if="activeTab === 'mistakes'">
      <view key="mistakes" class="home-detail-route-page mistakes-route-page">
      <AppPageHeader
        :title="retestMode ? '错题重测' : '错题本'"
        :subtitle="retestMode ? retestScopeText : ''"
        fixed
        @back="handleMistakeBack"
      >
        <template #right>
          <button
            v-if="!retestMode"
            class="retest-entry-btn"
            :disabled="!isAuthed || retestCandidateMistakes.length === 0"
            @tap="startWrongRetest"
          >
            {{ retestButtonText }}
          </button>
        </template>
      </AppPageHeader>

      <template v-if="retestMode">
        <SectionCard v-if="retestCompleted" title="重测完成" subtitle="本轮错题复盘结果">
          <view class="retest-summary-card">
            <view class="summary-score">{{ retestCorrectCount }} / {{ retestTotal }}</view>
            <view class="summary-copy">
              本轮共重测 {{ retestTotal }} 道错题，答对 {{ retestCorrectCount }} 道。
              建议优先回看红色题目，再进行一次短组复盘。
            </view>
            <view class="answer-map">
              <button
                v-for="(item, index) in retestResults"
                :key="item.question_id || index"
                class="answer-dot"
                :class="{ correct: item.is_correct, wrong: !item.is_correct }"
                @tap="jumpRetestReview(index)"
              >
                {{ index + 1 }}
              </button>
            </view>
            <view class="detail-actions">
              <button class="task-btn" @tap="restartWrongRetest">再测一遍</button>
              <button class="task-btn ghost" @tap="exitWrongRetest">返回错题本</button>
            </view>
          </view>
        </SectionCard>

        <view v-else-if="retestLoading" class="state-box">正在整理本题...</view>

        <SectionCard v-else-if="retestDetail" :title="`重测进度 ${retestProgressLabel}`">
          <view class="wrong-detail retest-detail">
            <MathText class="wrong-stem" :value="retestDetail.question.stem" />
            <view class="wrong-options">
              <button
                v-for="option in retestOptions"
                :key="option.key"
                class="wrong-option"
                :class="getRetestOptionClass(option.key)"
                @tap="selectRetestAnswer(option.key)"
              >
                <text class="option-key">{{ option.key }}</text>
                <MathText class="option-text" :value="option.text" />
              </button>
            </view>
            <view v-if="retestResultText" class="answer-line">正确答案：{{ retestDetail.question.answer }}</view>
            <MathText v-if="retestResultText" class="explain-text" :value="retestDetail.question.explanation" />
            <view class="detail-actions">
              <button
                v-if="!retestResultText"
                class="modal-submit-btn"
                :disabled="!retestAnswer || retestSubmitting"
                @tap="submitRetestAnswer"
              >
                {{ retestSubmitting ? '提交中...' : retestAnswer ? '提交答案' : '请选择一个答案' }}
              </button>
              <button v-else class="modal-submit-btn done" @tap="nextRetestQuestion">
                {{ retestIndex + 1 >= retestItems.length ? '查看重测结果' : '下一题' }}
              </button>
            </view>
          </view>
        </SectionCard>
      </template>

      <template v-else>
        <AppPageLoadingState v-if="wrongLoading" message="正在整理错题本..." />
        <SectionCard v-else>
          <view v-if="!isAuthed" class="state-box warning">登录后才能查看你的真实错题本。</view>
          <view v-else class="wrong-filter-card">
            <view class="wrong-filter-grid">
              <picker
                class="wrong-filter-select"
                mode="selector"
                :range="wrongSubjectPickerOptions"
                range-key="label"
                :value="wrongSubjectPickerIndex"
                @change="onWrongSubjectPickerChange"
              >
                <view class="wrong-filter-select-control">
                  <text class="wrong-filter-select-name">科目</text>
                  <text class="wrong-filter-select-value">{{ selectedWrongSubjectLabel }}</text>
                  <view class="wrong-filter-select-arrow-icon" aria-hidden="true"></view>
                </view>
              </picker>

              <picker
                class="wrong-filter-select"
                :class="{ disabled: !wrongFilters.subject }"
                mode="selector"
                :range="wrongModulePickerOptions"
                range-key="label"
                :value="wrongModulePickerIndex"
                :disabled="!wrongFilters.subject"
                @change="onWrongModulePickerChange"
              >
                <view class="wrong-filter-select-control">
                  <text class="wrong-filter-select-name">模块</text>
                  <text class="wrong-filter-select-value" :class="{ muted: !wrongFilters.subject }">{{ selectedWrongModuleLabel }}</text>
                  <view class="wrong-filter-select-arrow-icon" aria-hidden="true"></view>
                </view>
              </picker>

              <picker
                class="wrong-filter-select is-submodule"
                :class="{ disabled: !wrongFilters.module }"
                mode="selector"
                :range="wrongSubmodulePickerOptions"
                range-key="label"
                :value="wrongSubmodulePickerIndex"
                :disabled="!wrongFilters.module"
                @change="onWrongSubmodulePickerChange"
              >
                <view class="wrong-filter-select-control">
                  <text class="wrong-filter-select-name">子模块</text>
                  <text class="wrong-filter-select-value" :class="{ muted: !wrongFilters.module }">{{ selectedWrongSubmoduleLabel }}</text>
                  <view class="wrong-filter-select-arrow-icon" aria-hidden="true"></view>
                </view>
              </picker>
            </view>
          </view>
          <view v-if="wrongError" class="state-box warning">{{ wrongError }}</view>
          <AppEmptyState
            v-else-if="isAuthed && filteredMistakes.length === 0"
            label="暂无错题"
            title="当前筛选条件下还没有错题"
            description="继续练习后，答错的题目会自动收录在这里。"
          />
          <MistakeList v-else :items="visibleMistakes" @select="openWrongDetail" />
          <view v-if="isAuthed && (fullMistakes.length || wrongHasMore)" class="list-load-state" @tap="loadMoreMistakes">
            {{ wrongLoadingMore ? '正在加载更多错题…' : hasMoreMistakes ? '继续下滑加载更多错题' : '已加载全部错题' }}
          </view>
        </SectionCard>
      </template>

      <view v-if="selectedWrongDetail" class="wrong-modal-mask" @tap="closeWrongDetail">
        <view class="wrong-modal-panel" @tap.stop>
          <view class="wrong-modal-grabber"></view>
          <view class="wrong-modal-head">
            <view class="wrong-modal-heading">
              <view class="wrong-modal-title">错题重练</view>
              <view class="wrong-modal-sub">
                {{ selectedWrongDetail.question.subject }} / {{ selectedWrongDetail.question.module }}
              </view>
            </view>
            <button class="wrong-modal-close" aria-label="关闭" @tap="closeWrongDetail"><CloseIcon /></button>
          </view>
          <scroll-view scroll-y class="wrong-modal-scroll">
            <view class="wrong-detail">
              <view class="wrong-section-label">题目</view>
              <MathText class="wrong-stem" :value="selectedWrongDetail.question.stem" />
              <view class="wrong-section-label">选项</view>
              <view class="wrong-options">
                <button
                  v-for="option in wrongDetailOptions"
                  :key="option.key"
                  class="wrong-option"
                  :class="getWrongOptionClass(option.key)"
                  @tap="selectReviewAnswer(option.key)"
                >
                  <text class="option-key">{{ option.key }}</text>
                  <MathText class="option-text" :value="option.text" />
                </button>
              </view>
              <view v-if="!reviewResultText" class="review-hint">
                <text class="review-hint-main">上次选择：{{ selectedWrongDetail.latest_selected_answer || '暂无记录' }}</text>
                <text class="review-hint-sub">提交后查看正确答案与解析</text>
              </view>
              <view v-if="reviewResultText" class="state-box" :class="{ mastered: reviewMastered }">{{ reviewResultText }}</view>
              <view v-if="reviewResultText" class="answer-line">正确答案：{{ selectedWrongDetail.question.answer }}</view>
              <MathText v-if="reviewResultText" class="explain-text" :value="selectedWrongDetail.question.explanation" />
              <view class="detail-actions">
                <button
                  v-if="!reviewResultText"
                  class="modal-submit-btn"
                  :disabled="!reviewAnswer || reviewingWrong"
                  @tap="submitWrongReview"
                >
                  {{ reviewingWrong ? '提交中...' : reviewAnswer ? '提交答案' : '请选择一个答案' }}
                </button>
                <button v-else class="modal-submit-btn done" @tap="closeWrongDetail">我知道了</button>
              </view>
            </view>
          </scroll-view>
        </view>
      </view>
      </view>
    </template>
    <template v-if="activeTab === 'report'">
      <view key="report" class="report-dashboard">
        <AppPageHeader title="学习报告" fixed @back="activeTab = 'profile'" />

        <AppPageLoadingState v-if="reportLoading" message="正在整理学习报告..." />
        <view v-else-if="reportError" class="state-box warning">{{ reportError }}</view>

        <AppEmptyState
          v-if="!isAuthed"
          class="report-empty-card"
          label="尚未形成有效诊断"
          title="尚未形成有效诊断"
          description="登录并完成第一组练习后，我们会根据真实作答情况生成学习报告。"
        >
          <button class="report-empty-action" @tap="goLogin">登录后开始练习</button>
        </AppEmptyState>
        <AppEmptyState
          v-else-if="report.items.length === 0"
          class="report-empty-card"
          label="尚未形成有效诊断"
          title="尚未形成有效诊断"
          description="完成第一组练习后，我们会根据你的真实作答情况生成学习报告。"
        >
          <button class="report-empty-action" @tap="goPractice">开始第一次练习</button>
        </AppEmptyState>

        <template v-else>
          <view class="report-diagnosis-card">
            <view class="report-card-heading">
              <view>
                <view class="report-card-title">本周学习诊断</view>
                <view class="report-card-subtitle">根据你的真实练习数据生成</view>
              </view>
              <view class="report-diagnosis-icon"><image :src="getThemeIconSrc('/static/ui-icons/png/original/report.png', selectedThemeKey)" mode="aspectFit" aria-hidden="true" /></view>
            </view>
            <view class="diagnosis-copy">{{ report.diagnosis }}</view>
            <view class="diagnosis-metrics">
              <view v-for="metric in reportOverview.metrics" :key="metric.label" class="diagnosis-metric">
                <view class="diagnosis-metric-value" :class="metric.tone">{{ metric.value }}</view>
                <view class="diagnosis-metric-label">{{ metric.label }}</view>
              </view>
            </view>
            <view class="diagnosis-footnote">{{ reportOverview.note }}</view>
          </view>

          <view class="report-trend-card">
            <view class="report-card-heading">
              <view>
                <view class="report-card-title">学习趋势</view>
                <view class="report-card-subtitle">最近 7 天正确率</view>
              </view>
              <view class="trend-weekly-badge" :class="trendSummaryTone">{{ trendBadgeText }}</view>
            </view>
            <template v-if="trendUnlocked">
              <view class="trend-chart-wrap">
                <!-- #ifdef APP-PLUS -->
                <CanvasLineChart
                  class="trend-chart"
                  canvas-id="learning-report-trend-canvas"
                  :view-width="320"
                  :view-height="126"
                  :points="trendChartPoints"
                  :grid-y="trendCanvasGridY"
                  :line-color="currentTheme.primary"
                  :point-stroke="currentTheme.primary"
                  :fill-color="currentTheme.primarySoft"
                  :area-baseline="112"
                  :line-width="4"
                  :point-radius="4"
                  grid-color="#e9eef7"
                  :grid-line-width="1.5"
                />
                <!-- #endif -->
                <!-- #ifndef APP-PLUS -->
                <svg class="trend-chart" viewBox="0 0 320 126" preserveAspectRatio="none" aria-label="近七天正确率趋势">
                  <line x1="8" x2="312" y1="24" y2="24" class="trend-grid-line" />
                  <line x1="8" x2="312" y1="66" y2="66" class="trend-grid-line" />
                  <line x1="8" x2="312" y1="108" y2="108" class="trend-grid-line" />
                  <path :d="trendAreaPath" class="trend-area-path" />
                  <path :d="trendPath" class="trend-line-path" />
                  <circle
                    v-for="point in trendChartPoints"
                    :key="point.date"
                    :cx="point.x"
                    :cy="point.y"
                    r="4"
                    class="trend-point"
                  />
                </svg>
                <!-- #endif -->
              </view>
              <view class="trend-axis-labels">
                <text v-for="item in reportTrend" :key="item.date">{{ item.label }}</text>
              </view>
              <view class="trend-conclusion" :class="trendSummaryTone">{{ trendSummary }}</view>
            </template>
            <view v-else class="trend-unlock-state">
              <view class="trend-unlock-title">再完成 {{ trendUnlockRemaining }} 道题，即可解锁学习趋势分析</view>
              <view class="trend-unlock-meta">{{ trendAnsweredCount }} / 20 题</view>
              <view class="trend-unlock-track"><view :style="{ width: `${trendUnlockProgress}%` }"></view></view>
            </view>
          </view>

          <view class="report-section-heading">
            <view class="report-section-title">各模块掌握情况</view>
            <view class="report-section-subtitle">科目卡展示累计作答统计</view>
          </view>
          <view class="subject-report-list">
          <view
            v-for="item in subjectReportCards"
            :key="item.subject"
            class="subject-report-card"
            @tap="goTaskPractice(item)"
          >
            <view class="ring-wrap" :class="item.tone">
              <view class="ring-score">{{ item.accuracy }}%</view>
              <view class="ring-label">正确率</view>
            </view>
            <view class="subject-report-main">
              <view class="subject-head">
                <view class="subject-name">
                  <view class="subject-icon">
                    <image :src="item.iconSrc" mode="aspectFit" aria-hidden="true" />
                  </view>
                  <view class="subject-title">{{ item.subject }}</view>
                </view>
                <view class="subject-status" :class="item.tone">{{ item.status }}</view>
              </view>
              <view class="subject-count-label">做题数量</view>
              <view class="subject-count-row">
                <view class="subject-count">{{ item.total }}<text>题</text></view>
                <view class="subject-weekly-change" :class="item.weeklyChange.tone">{{ item.weeklyChange.text }}</view>
              </view>
              <view class="progress-track">
                <view class="progress-fill" :class="item.tone" :style="{ width: `${item.accuracy}%` }"></view>
              </view>
              <view class="subject-weakness">
                <text>薄弱知识点</text>
                <text>{{ item.weakestModule || '继续积累练习样本' }}</text>
              </view>
              <view class="subject-trend">{{ item.suggestion }}</view>
              <button class="subject-report-action" @tap.stop="goTaskPractice(item)">{{ item.action }} <text>›</text></button>
            </view>
          </view>
        </view>

        <view v-if="weeklyBreakthroughs.length" class="weekly-breakthrough-card">
          <view class="report-card-heading">
            <view>
              <view class="report-card-title">本周重点突破</view>
              <view class="report-card-subtitle">按正确率从低到高排序</view>
            </view>
          </view>
          <view class="breakthrough-list">
            <view v-for="(item, index) in weeklyBreakthroughs" :key="`${item.subject}-${item.topic}`" class="breakthrough-item">
              <view class="breakthrough-rank">{{ index + 1 }}</view>
              <view class="breakthrough-main">
                <view class="breakthrough-title">{{ item.subject }} · {{ item.topic }}</view>
                <view class="breakthrough-meta">{{ index === 0 ? '当前最薄弱知识点' : '建议本周安排专项巩固' }}</view>
              </view>
              <view class="breakthrough-score" :class="item.tone">{{ item.accuracy }}%</view>
            </view>
          </view>
        </view>

        <view class="learning-advice-card">
          <view class="advice-head">
            <view class="advice-title-wrap">
              <view class="advice-icon">
                <image :src="getToneIconSrc('/static/ui-icons/png/original/lightbulb.png', 'gold')" mode="aspectFit" aria-hidden="true" />
              </view>
              <view>
                <view class="advice-title">学习建议</view>
                <view class="advice-subtitle">{{ studyAdviceSubtitle }}</view>
              </view>
            </view>
          </view>
          <view class="advice-task-list">
            <view v-for="(item, index) in reportActionTasks" :key="item.id" class="advice-task-item">
              <view class="advice-task-index">任务 {{ index + 1 }}</view>
              <view class="advice-task-title">{{ item.title }}</view>
              <view class="advice-task-meta">{{ item.meta }}</view>
              <view class="advice-task-desc">{{ item.desc }}</view>
              <button class="advice-task-action" @tap.stop="goReportTask(item)">{{ item.actionLabel }} <text>›</text></button>
            </view>
          </view>
          <button v-if="isAuthed" class="advice-detail-btn" @tap="openStudyAdviceDetail">
            查看详细建议
          </button>
        </view>

        <view v-if="todayTraining.items.length" class="today-training-card">
          <view class="report-card-heading">
            <view>
              <view class="report-card-title">今日推荐训练</view>
              <view class="report-card-subtitle">{{ todayTraining.meta }}</view>
            </view>
            <view class="today-training-icon">
              <image :src="getThemeIconSrc('/static/ui-icons/png/original/play.png', selectedThemeKey)" mode="aspectFit" aria-hidden="true" />
            </view>
          </view>
          <view class="today-training-list">
            <text v-for="(item, index) in todayTraining.items" :key="item.subject">{{ index ? '＋' : '' }}{{ item.label }}</text>
          </view>
          <button class="report-action-btn" @tap="startTodayTraining">开始今日训练</button>
        </view>
        </template>
      </view>
    </template>

      <template v-if="activeTab === 'profile'">
        <view key="profile" class="profile-dashboard">
        <view class="profile-identity">
          <button class="profile-avatar-button" :aria-label="isAuthed ? '编辑头像和昵称' : '登录或注册'" @tap="openProfileEditModal">
            <image
              v-if="avatarImageUrl"
              class="profile-reference-avatar profile-reference-avatar-image"
              :src="avatarImageUrl"
              mode="aspectFill"
              alt="用户头像"
            />
            <view v-else class="profile-reference-avatar">{{ profileAvatarText }}</view>
            <view class="profile-avatar-edit" aria-hidden="true">编辑</view>
          </button>
          <view class="profile-reference-name" @tap="openProfileEditModal">{{ profile.userName }}</view>
          <button class="profile-exam-selector" aria-label="切换考试版本" @tap="openExamSwitchModal">
            <view class="profile-exam-mark">版本</view>
            <text class="profile-exam-code">{{ examCode }}</text>
            <text class="profile-exam-arrow">⌄</text>
          </button>
        </view>

        <view class="profile-reference-divider"></view>

        <view class="profile-group">
          <view class="profile-group-title">学习设置</view>
          <view class="profile-section-card profile-reference-card">
          <view class="menu-list">
            <view
              v-for="item in practiceTools"
              :key="item.label"
              class="menu-row"
              :class="{ locked: item.locked }"
              @tap="handleMenu(item)"
            >
              <view class="menu-icon" :class="[item.tone, item.iconClass]">
                <image
                  v-if="item.iconSrc"
                  class="menu-icon-img"
                  :src="getThemeIconSrc(item.iconSrc, selectedThemeKey)"
                  mode="aspectFit"
                />
                <text v-else-if="!item.iconClass">{{ item.icon }}</text>
              </view>
              <view class="menu-copy">
                <view class="menu-title-row">
                  <text class="menu-title">{{ item.label }}</text>
                  <text v-if="item.locked" class="pro-lock-badge">登录</text>
                </view>
              </view>
              <view v-if="item.value" class="menu-row-value">{{ item.value }}</view>
              <view class="menu-arrow">›</view>
            </view>
          </view>
        </view>
        </view>

        <view class="profile-group">
          <view class="profile-group-title">研圈互动</view>
          <view class="profile-section-card profile-reference-card">
          <view class="menu-list">
            <view
              v-for="item in communityTools"
              :key="item.label"
              class="menu-row"
              @tap="handleMenu(item)"
            >
              <view class="menu-icon" :class="[item.tone, item.iconClass]">
                <image
                  v-if="item.iconSrc"
                  class="menu-icon-img"
                  :src="getThemeIconSrc(item.iconSrc, selectedThemeKey)"
                  mode="aspectFit"
                />
                <text v-else-if="!item.iconClass">{{ item.icon }}</text>
                <view v-if="item.unread" class="menu-unread-dot" aria-label="有新消息"></view>
              </view>
              <view class="menu-copy">
                <view class="menu-title">{{ item.label }}</view>
              </view>
              <view v-if="item.value" class="menu-row-value">{{ item.value }}</view>
              <view class="menu-arrow">›</view>
            </view>
          </view>
        </view>
        </view>

        <view class="profile-group">
          <view class="profile-group-title">账户与服务</view>
          <view class="profile-section-card profile-reference-card">
          <view class="menu-list">
            <view v-for="item in serviceTools" :key="item.label" class="menu-row" @tap="handleMenu(item)">
              <view class="menu-icon" :class="[item.tone, item.iconClass]">
                <image
                  v-if="item.iconSrc"
                  class="menu-icon-img"
                  :src="getThemeIconSrc(item.iconSrc, selectedThemeKey)"
                  mode="aspectFit"
                />
                <text v-else-if="!item.iconClass">{{ item.icon }}</text>
                <view v-if="item.unread" class="menu-unread-dot" aria-label="有新消息"></view>
              </view>
              <view class="menu-copy">
                <view class="menu-title">{{ item.label }}</view>
              </view>
              <view v-if="item.value" class="menu-row-value">{{ item.value }}</view>
              <view class="menu-arrow">›</view>
            </view>
          </view>
        </view>
        </view>

        <view
          class="logout-card"
          hover-class="logout-card--pressed"
          :aria-label="isAuthed ? '退出登录' : '退出游客模式'"
          role="button"
          @tap="logout"
        >
          {{ isAuthed ? '退出登录' : '退出游客模式' }}
        </view>
      </view>
    </template>
    <view
      v-if="showSubscriptionSheet"
      class="subscription-sheet-mask"
      :class="{ 'is-visible': subscriptionSheetVisible }"
      :style="subscriptionSheetMaskStyle"
      role="presentation"
      @tap="closeSubscriptionSheet"
    >
      <view
        class="subscription-sheet"
        :class="{ 'is-dragging': subscriptionSheetDragging }"
        :style="subscriptionSheetDragStyle"
        role="dialog"
        aria-modal="true"
        aria-label="开通港研通 Plus"
        @tap.stop
        @click.stop
        @mousemove.stop="moveSubscriptionSheetDrag"
        @mouseup.stop="finishSubscriptionSheetDrag"
        @mouseleave="cancelSubscriptionSheetDrag"
      >
        <view
          class="subscription-sheet-drag-handle"
          role="button"
          aria-label="向下拖动关闭我的 PLUS"
          @touchstart.stop="beginSubscriptionSheetDrag"
          @touchmove.stop.prevent="moveSubscriptionSheetDrag"
          @touchend.stop="finishSubscriptionSheetDrag"
          @touchcancel.stop="cancelSubscriptionSheetDrag"
          @mousedown.stop="beginSubscriptionSheetDrag"
        >
          <view class="subscription-sheet-drag-bar"></view>
        </view>
        <MembershipSubscriptionPreview
          :config="subscriptionPageConfig"
          :membership="subscriptionMembership"
          @close="closeSubscriptionSheet"
          @subscribe="handleSubscriptionSubscribe"
          @restore="handleSubscriptionRestore"
        />
      </view>
    </view>

    <!-- #ifndef MP-WEIXIN -->
    <view v-if="showTrainingSheet" class="training-sheet-mask" @tap="closeRecommendedTrainingSheet">
      <view class="training-sheet" @tap.stop>
        <view class="sheet-handle"></view>
        <view class="sheet-head">
          <view class="sheet-title">推荐训练设置</view>
          <view class="sheet-subtitle">根据你的错题、正确率和薄弱模块生成专属训练</view>
        </view>

        <view class="sheet-section">
          <view class="subject-setting">
            <view class="manual-label">训练科目</view>
            <view class="subject-options">
              <button
                v-for="item in trainingSubjectOptions"
                :key="item.value"
                class="subject-chip"
                :class="{ active: trainingSubject === item.value }"
                @tap="selectTrainingSubject(item.value)"
              >
                {{ item.label }}
              </button>
            </view>
          </view>

          <view class="sheet-row">
            <view>
              <view class="sheet-section-title">智能推荐</view>
              <view class="sheet-section-sub">系统自动匹配当前最需要补强的范围</view>
            </view>
            <switch
              :checked="smartMode"
              :color="currentTheme.primary"
              @change="handleSmartModeChange"
            />
          </view>

          <view v-if="smartMode" class="smart-recommend-card">
            <view class="recommend-lines">
              <view class="recommend-line">
                <text>推荐模块：</text>
                <text class="recommend-value">{{ smartRecommendationSubjectLabel }}</text>
              </view>
              <view class="recommend-line">
                <text>推荐难度：</text>
                <text class="recommend-value">{{ smartRecommendation.difficulty }}</text>
              </view>
              <view class="recommend-line">
                <text>推荐题量：</text>
                <text class="recommend-value">{{ smartRecommendation.questionCount }}题</text>
              </view>
              <view class="recommend-line">
                <text>推荐依据：</text>
                <text class="recommend-text">{{ smartRecommendation.basis }}</text>
              </view>
            </view>
          </view>

          <view v-else class="manual-settings">
            <view class="manual-title">手动设置</view>
            <view class="manual-label">1. 选择难度</view>
            <view class="difficulty-options">
              <button
                v-for="item in difficultyOptions"
                :key="item"
                class="difficulty-chip"
                :class="{ active: manualDifficulty === item }"
                @tap="manualDifficulty = item"
              >
                {{ item }}
              </button>
            </view>

            <view class="manual-count-head">
              <view class="manual-label">2. 题目数量</view>
              <view class="manual-count-value">{{ manualQuestionCount }} 题</view>
            </view>
            <slider
              class="question-slider"
              :value="manualQuestionCount"
              :min="5"
              :max="30"
              :step="5"
              :activeColor="currentTheme.primary"
              backgroundColor="#e5ebf5"
              block-color="#ffffff"
              :block-size="22"
              @change="handleQuestionCountChange"
              @changing="handleQuestionCountChange"
            />
            <view class="slider-scale">
              <text>5</text>
              <text>10</text>
              <text>15</text>
              <text>20</text>
              <text>25</text>
              <text>30</text>
            </view>
          </view>
        </view>

        <view class="sheet-actions">
          <button class="sheet-cancel-btn" @tap="closeRecommendedTrainingSheet">取消</button>
          <button class="sheet-generate-btn" :disabled="generatingTraining" @tap="handleGenerateTraining">
            {{ generatingTraining ? '生成中...' : '生成训练' }}
          </button>
        </view>
      </view>
    </view>

    <view v-if="showGeneratingModal" class="generating-modal-mask">
      <view class="generating-modal-card">
        <view class="generating-orbit">
          <view class="generating-dot"></view>
        </view>
        <view class="generating-title">正在生成训练</view>
        <view class="generating-subtitle">
          DeepSeek 正在根据你的 {{ trainingSubjectLabel }} 记录生成专属题目，请稍等。
        </view>
        <view class="generating-countdown">预计还需 {{ generateCountdown }} 秒</view>
        <view class="generating-progress">
          <view class="generating-progress-bar" :style="{ width: generateProgressWidth }"></view>
        </view>
        <button class="generating-cancel-btn" @tap="cancelGenerateTraining">取消生成</button>
      </view>
    </view>
    <!-- #endif -->

    <view v-if="showStudyAdviceDetail" class="advice-detail-mask" @tap="closeStudyAdviceDetail">
      <view class="advice-detail-sheet" @tap.stop>
        <view class="advice-detail-handle"></view>
        <button class="advice-detail-close" aria-label="关闭" @tap="closeStudyAdviceDetail"><CloseIcon /></button>
        <view class="advice-detail-head">
          <view class="advice-detail-title">详细学习建议</view>
          <view class="advice-detail-subtitle">{{ studyAdviceSummary }}</view>
        </view>
        <scroll-view scroll-y class="advice-detail-scroll">
          <view
            v-for="item in studyAdviceDetails"
            :key="item.subject"
            class="advice-subject-card"
          >
            <view class="advice-subject-head">
              <view>
                <view class="advice-subject-title">{{ item.subject }}</view>
                <view class="advice-subject-meta">
                  {{ item.accuracyText }} · {{ item.status || '待分析' }}
                </view>
              </view>
              <view class="advice-subject-badge">{{ item.subject }}</view>
            </view>

            <view class="detail-block">
              <view class="detail-block-title">薄弱点</view>
              <view v-for="point in item.weak_points" :key="point" class="detail-line">{{ point }}</view>
            </view>

            <view class="detail-block">
              <view class="detail-block-title">容易害怕的地方</view>
              <view v-for="point in item.fear_points" :key="point" class="detail-line">{{ point }}</view>
            </view>

            <view class="detail-block">
              <view class="detail-block-title">提分建议</view>
              <view v-for="point in item.score_tips" :key="point" class="detail-line strong">{{ point }}</view>
            </view>

            <view class="detail-block">
              <view class="detail-block-title">下一步</view>
              <view v-for="point in item.next_actions" :key="point" class="detail-line">{{ point }}</view>
            </view>
          </view>
        </scroll-view>
        <!-- #ifndef MP-WEIXIN -->
        <button class="advice-detail-action" @tap="openRecommendedTrainingSheet">按建议生成训练</button>
        <!-- #endif -->
      </view>
    </view>

    <view v-if="showExamSwitchModal" class="profile-exam-modal-mask" @tap="closeExamSwitchModal">
      <view class="profile-exam-modal" role="dialog" aria-label="切换考试版本" @tap.stop>
        <view class="profile-exam-modal-title">切换考试版本</view>
        <view class="profile-exam-option-list">
          <button
            v-for="option in examOptions"
            :key="option.code"
            class="profile-exam-option"
            :class="{ active: option.code === examCode }"
            @tap="selectProfileExam(option.code)"
          >
            <view class="profile-exam-option-copy">
              <text class="profile-exam-option-code">{{ option.code }}</text>
            </view>
            <view class="profile-exam-option-check">{{ option.code === examCode ? '✓' : '' }}</view>
          </button>
        </view>
        <button class="profile-exam-modal-cancel" @tap="closeExamSwitchModal">取消</button>
      </view>
    </view>

    <view v-if="showProfileEditModal" class="profile-edit-modal-mask" @tap="closeProfileEditModal">
      <view class="profile-edit-modal" role="dialog" aria-label="编辑个人资料" @tap.stop>
        <view class="profile-edit-modal-head">
          <view class="profile-edit-modal-title">编辑个人资料</view>
          <button class="profile-edit-modal-cancel" @tap="closeProfileEditModal">取消</button>
        </view>
        <button
          class="profile-edit-avatar-trigger"
          :class="{ uploading: profileEditUploading }"
          :disabled="profileEditUploading"
          aria-label="更换头像"
          @tap="chooseProfileAvatar"
        >
          <image
            v-if="profileEditAvatarPreview"
            class="profile-edit-avatar-image"
            :src="profileEditAvatarPreview"
            mode="aspectFill"
            alt="待保存的用户头像"
          />
          <view v-else class="profile-edit-avatar-fallback">{{ profileAvatarText }}</view>
          <view class="profile-edit-avatar-badge">{{ profileEditUploading ? '上传中' : '更换' }}</view>
        </button>
        <view class="profile-edit-avatar-hint">点击头像选择照片</view>
        <view class="profile-edit-field-label">昵称</view>
        <input
          v-model.trim="profileEditNickname"
          class="profile-edit-input"
          type="text"
          maxlength="40"
          placeholder="请输入昵称"
        />
        <view class="profile-edit-copy">头像和昵称会同步到“我的”页面。</view>
        <button class="profile-edit-save" :disabled="profileEditSaving || profileEditUploading" @tap="saveProfileEdit">
          {{ profileEditSaving ? '保存中...' : '保存' }}
        </button>
      </view>
    </view>

    <view v-if="showEmailBindingModal" class="profile-email-modal-mask" @tap="closeEmailBindingModal">
      <view class="profile-email-modal" role="dialog" aria-label="绑定或更改邮箱" @tap.stop>
        <view class="profile-edit-modal-head">
          <view class="profile-edit-modal-title">绑定 / 更改邮箱</view>
          <button class="profile-edit-modal-cancel" @tap="closeEmailBindingModal">取消</button>
        </view>
        <view class="profile-email-current">当前邮箱：{{ currentProfileEmail }}</view>
        <view class="profile-edit-field-label">新 QQ 邮箱</view>
        <input
          v-model.trim="profileEmailForm.email"
          class="profile-edit-input"
          type="text"
          placeholder="例如：123456@qq.com"
        />
        <view class="profile-edit-field-label">验证码</view>
        <view class="profile-email-code-row">
          <input
            v-model.trim="profileEmailForm.code"
            class="profile-edit-input profile-email-code-input"
            type="text"
            maxlength="8"
            placeholder="请输入验证码"
          />
          <button class="profile-email-code-button" :disabled="profileEmailSending" @tap="sendProfileEmailCode">
            {{ profileEmailSending ? '发送中...' : '发送验证码' }}
          </button>
        </view>
        <button class="profile-edit-save" :disabled="profileEmailSaving" @tap="submitProfileEmailBinding">
          {{ profileEmailSaving ? '处理中...' : '确认绑定' }}
        </button>
      </view>
    </view>

    <view v-if="showPhoneBindingModal" class="profile-email-modal-mask" @tap="closePhoneBindingModal">
      <view class="profile-email-modal" role="dialog" aria-label="绑定或更改手机号码" @tap.stop>
        <view class="profile-edit-modal-head">
          <view class="profile-edit-modal-title">绑定手机号码</view>
          <button class="profile-edit-modal-cancel" @tap="closePhoneBindingModal">取消</button>
        </view>
        <view class="profile-email-current">当前手机号码：{{ currentProfilePhone }}</view>
        <view class="profile-edit-field-label">手机号码</view>
        <input
          v-model.trim="profilePhoneForm.phone"
          class="profile-edit-input"
          type="number"
          maxlength="15"
          placeholder="请输入手机号码"
        />
        <view class="profile-edit-field-label">验证码</view>
        <view class="profile-email-code-row">
          <input
            v-model.trim="profilePhoneForm.code"
            class="profile-edit-input profile-email-code-input"
            type="number"
            maxlength="8"
            placeholder="请输入验证码"
          />
          <button
            class="profile-email-code-button"
            :disabled="profilePhoneSending || profilePhoneCountdown > 0"
            @tap="sendProfilePhoneCode"
          >
            {{ profilePhoneCodeButtonText }}
          </button>
        </view>
        <view class="profile-phone-note">号码通过验证码核验后绑定，不会改变当前邮箱密码和登录方式。</view>
        <button class="profile-edit-save" :disabled="profilePhoneSaving" @tap="submitProfilePhoneBinding">
          {{ profilePhoneSaving ? '处理中...' : '确认绑定' }}
        </button>
      </view>
    </view>

    <view
      v-if="selectedCommunityPost"
      class="community-reader"
      :class="{
        'is-closing': communityReaderClosing,
        'is-owner-preview': communityReaderOwnerPreview,
        'is-route-moving': communityReaderRouteMotion === 'entering' || communityReaderRouteMotion === 'leaving',
        'is-route-offscreen': communityReaderRouteMotion === 'enter-from' || communityReaderRouteMotion === 'leaving'
      }"
      @tap.stop
      @touchstart="beginCommunityReaderEdgeSwipe"
      @touchend="finishCommunityReaderEdgeSwipe"
      @touchcancel="cancelCommunityReaderEdgeSwipe"
      @transitionend="handleCommunityReaderRouteTransitionEnd"
    >
      <view class="community-reader-surface">
        <view class="community-reader-topbar">
          <button
            class="community-reader-back"
            :aria-label="communityReaderReturnsToMyPosts ? '返回我的帖子' : '返回社区'"
            :disabled="communityReaderClosing"
            @tap.stop="closeCommunityPostWithTapGuard"
          >
            <image src="/static/ui-icons/png/original/back.png" mode="aspectFit" />
          </button>
          <view class="community-reader-author">
            <view class="community-reader-avatar" :class="`tone-${selectedCommunityPost.tone}`">
              <image v-if="selectedCommunityPost.avatarUrl" :src="selectedCommunityPost.avatarUrl" mode="aspectFill" />
              <text v-else>{{ selectedCommunityPost.avatar }}</text>
            </view>
            <view class="community-reader-author-copy">
              <view class="community-reader-author-name">{{ selectedCommunityPost.author }}<text v-if="selectedCommunityPost.authorVerified" class="community-author-verified">已认证</text></view>
              <view class="community-reader-author-meta">{{ communityReaderPostTypeLabel }} · {{ selectedCommunityPost.publishTime }}</view>
            </view>
            <view
              class="community-reader-top-hitbox"
              aria-label="双击回到文章顶部"
              @tap.stop="handleCommunityReaderTopZoneTap"
            ></view>
          </view>
          <view class="community-reader-tag-list">
            <view
              v-for="tag in getCommunityPostTags(selectedCommunityPost)"
              :key="`reader-${selectedCommunityPost.id}-${tag}`"
              class="community-reader-category"
            >{{ tag }}</view>
          </view>
          <button class="community-reader-share" aria-label="帖子更多操作" @tap="shareCommunityPost">•••</button>
        </view>

        <scroll-view
          scroll-y
          class="community-reader-scroll"
          :scroll-into-view="communityReaderScrollTarget"
          :scroll-with-animation="true"
          @scroll="handleCommunityReaderScroll"
          @touchmove="handleCommunityReaderScrollTouchMove"
        >
          <view id="community-reader-top" class="community-reader-body">
            <view
              v-if="communityReaderOwnerPreview && !communityReaderOwnerLoading"
              class="community-reader-owner-status"
              :class="`is-${communityReaderOwnerStatus.key}`"
            >{{ communityReaderOwnerStatus.label }}</view>
            <view
              v-if="selectedCommunityPost.media && selectedCommunityPost.media.length"
              class="community-reader-media"
            >
              <swiper
                class="community-reader-media-swiper"
                :current="communityReaderMediaIndex"
                :duration="260"
                @change="handleCommunityReaderMediaChange"
              >
                <swiper-item
                  v-for="media in selectedCommunityPost.media"
                  :key="media.imageUrl || media.image_url || `${media.kicker}-${media.title}`"
                >
                  <view class="community-reader-media-slide" :class="[`tone-${media.tone}`, { 'is-image': media.imageUrl || media.image_url }]">
                    <image
                      v-if="media.imageUrl || media.image_url"
                      :src="media.imageUrl || media.image_url"
                      mode="aspectFit"
                      @tap.stop="previewCommunityReaderImages(media)"
                    />
                    <view v-else class="community-reader-media-fallback">
                      <view>{{ media.kicker }}</view>
                      <view class="community-reader-media-fallback-title">{{ media.title }}</view>
                      <text>{{ media.copy }}</text>
                    </view>
                  </view>
                </swiper-item>
              </swiper>
              <view v-if="selectedCommunityPost.media.length > 1" class="community-reader-media-count">
                {{ communityReaderMediaIndex + 1 }}/{{ selectedCommunityPost.media.length }}
              </view>
            </view>

            <view class="community-reader-title">{{ selectedCommunityPost.title }}</view>
            <view class="community-reader-copy">{{ selectedCommunityPost.content || selectedCommunityPost.summary }}</view>

            <view v-if="communityReaderInteractionsEnabled" id="community-reader-comments" class="community-reader-comments-section">
              <view class="community-reader-comments-toolbar">
                <view class="community-reader-comments-tabs">
                  <button
                    class="community-reader-comments-tab"
                    :class="{ active: communityInteractionTab === 'comments' }"
                    @tap="selectCommunityInteractionTab('comments')"
                  >评论 {{ selectedCommunityPost.stats.comments }}</button>
                  <button
                    class="community-reader-comments-tab"
                    :class="{ active: communityInteractionTab === 'likes' }"
                    @tap="selectCommunityInteractionTab('likes')"
                  >点赞 {{ selectedCommunityPost.stats.likes }}</button>
                </view>
                <view v-if="communityInteractionTab === 'comments'" class="community-reader-sort" aria-label="评论排序">
                  <button
                    :class="{ active: communityCommentSort === 'default' }"
                    @tap="communityCommentSort = 'default'"
                  >默认</button>
                  <button
                    :class="{ active: communityCommentSort === 'latest' }"
                    @tap="communityCommentSort = 'latest'"
                  >最新</button>
                  <button
                    :class="{ active: communityCommentSort === 'earliest' }"
                    @tap="communityCommentSort = 'earliest'"
                  >最早</button>
                </view>
              </view>

              <template v-if="communityInteractionTab === 'comments'">
                <AppPageLoadingState v-if="communityCommentsLoading && sortedCommunityComments.length === 0" compact message="正在整理评论..." />
                <AppEmptyState
                  v-else-if="communityCommentsLoadError && sortedCommunityComments.length === 0"
                  compact
                  label="评论加载失败"
                  title="评论暂时没有加载出来"
                  :description="communityCommentsLoadError"
                >
                  <button @tap="retryCommunityComments">重新加载</button>
                </AppEmptyState>
                <AppEmptyState
                  v-else-if="sortedCommunityComments.length === 0"
                  compact
                  label="暂无评论"
                  title="暂无评论"
                  description="来留下第一条讨论吧。"
                />
                <view v-else class="community-reader-comment-list">
                  <button
                    v-if="communityCommentsHasMore || communityCommentsLoadingMore || communityCommentsLoadError"
                    class="community-comments-page-action"
                    :disabled="communityCommentsLoadingMore"
                    @tap.stop="communityCommentsHasMore ? loadMoreCommunityComments() : retryCommunityComments()"
                  >
                    {{ communityCommentsLoadingMore ? '正在加载更早评论…' : (communityCommentsLoadError ? '加载失败，点击重试' : '查看更早评论') }}
                  </button>
                  <view
                    v-for="comment in sortedCommunityComments"
                    :key="comment.id"
                    class="community-reader-comment-item"
                    :class="{ 'is-sending': comment.deliveryStatus === 'sending', 'is-failed': comment.deliveryStatus === 'failed' }"
                  >
                    <view class="community-reader-comment-avatar">
                      <image v-if="comment.avatarUrl" :src="comment.avatarUrl" mode="aspectFill" />
                      <text v-else>{{ comment.avatar }}</text>
                    </view>
                    <view class="community-reader-comment-main">
                      <view class="community-reader-comment-author">{{ comment.author }}</view>
                      <view class="community-reader-comment-copy">{{ comment.content }}</view>
                      <view class="community-reader-comment-time">
                        <text>{{ formatCommunityCommentTime(comment.createdAt) }}</text>
                        <text v-if="comment.deliveryStatus === 'sending'" class="community-comment-delivery-state"> · 发送中</text>
                        <button
                          v-else-if="comment.deliveryStatus === 'failed'"
                          class="community-comment-retry"
                          @tap.stop="retryCommunityComment(comment)"
                        >发送失败，点击重试</button>
                      </view>
                    </view>
                    <button
                      class="community-reader-comment-like"
                      :class="{ active: comment.liked, pending: isCommunityCommentLikePending(selectedCommunityCommentsPost.id, comment.id) }"
                      :aria-label="comment.liked ? '取消评论点赞' : '点赞评论'"
                      :aria-pressed="comment.liked"
                      :aria-busy="isCommunityCommentLikePending(selectedCommunityCommentsPost.id, comment.id)"
                      :disabled="Boolean(comment.deliveryStatus)"
                      @tap.stop="toggleCommunityCommentLike(comment)"
                    >
                      <image
                        class="community-reader-comment-like-icon-image"
                        :src="comment.liked ? communityLikeFilledIconSrc : communityLikeIconSrc"
                        mode="aspectFit"
                        aria-hidden="true"
                      />
                      <text>{{ comment.likeCount }}</text>
                    </button>
                    <button v-if="!comment.deliveryStatus" class="community-reader-comment-more" aria-label="评论更多操作" @tap.stop="openCommunityCommentActions(comment)">•••</button>
                  </view>
                </view>
              </template>

              <template v-else>
                <AppPageLoadingState v-if="communityLikesLoading" compact message="正在整理点赞用户..." />
                <AppEmptyState
                  v-else-if="communityLikes.length === 0"
                  compact
                  label="暂无点赞"
                  title="暂无点赞"
                  description="来成为第一位点赞的研友吧。"
                />
                <view v-else class="community-reader-like-list">
                  <view v-for="like in communityLikes" :key="like.id" class="community-reader-like-item">
                    <view class="community-reader-comment-avatar">
                      <image v-if="like.avatarUrl" :src="like.avatarUrl" mode="aspectFill" />
                      <text v-else>{{ like.avatar }}</text>
                    </view>
                    <view class="community-reader-comment-main">
                      <view class="community-reader-comment-author">{{ like.author }}</view>
                      <view class="community-reader-comment-time">{{ formatCommunityCommentTime(like.likedAt) }} 点赞</view>
                    </view>
                  </view>
                </view>
              </template>
            </view>
          </view>
        </scroll-view>

        <view
          v-if="communityReaderInteractionsEnabled"
          class="community-reader-actions"
          :class="{ 'keyboard-open': communityCommentKeyboardVisible }"
          :style="communityReaderActionsStyle"
        >
          <view class="community-reader-comment-entry" @tap.stop="handleCommunityCommentEntryTap">
            <image src="/static/ui-icons/png/original/circle-comment.png" mode="aspectFit" />
            <input
              v-if="communityCommentEntryReady"
              v-model="communityCommentDraft"
              maxlength="500"
              confirm-type="send"
              placeholder="说点什么..."
              placeholder-class="community-reader-comment-placeholder"
              :focus="communityCommentInputFocused"
              :adjust-position="false"
              cursor-spacing="0"
              :disabled="communityCommentSubmitting"
              @tap.stop
              @focus="handleCommunityCommentInputFocus"
              @blur="handleCommunityCommentInputBlur"
              @keyboardheightchange="handleCommunityCommentKeyboardHeightChange"
              @confirm="submitCommunityComment"
            />
            <view v-else class="community-reader-comment-prompt">说点什么...</view>
          </view>
            <button
              class="community-reader-action"
              :class="{
                active: selectedCommunityPost.liked,
                pending: isCommunityPostLikePending(selectedCommunityPost.id),
                'is-bursting': communityLikeBurstPostId === selectedCommunityPost.id
              }"
              :aria-label="selectedCommunityPost.liked ? '取消点赞' : '点赞'"
              :aria-pressed="selectedCommunityPost.liked"
              :aria-busy="isCommunityPostLikePending(selectedCommunityPost.id)"
              @tap="toggleCommunityLike(selectedCommunityPost)"
            >
              <view class="community-reader-like-icon-wrap">
                <image
                  class="community-reader-like-icon"
                  :src="selectedCommunityPost.liked ? communityLikeFilledIconSrc : communityLikeIconSrc"
                  mode="aspectFit"
                  aria-hidden="true"
                />
                <view
                  v-if="communityLikeBurstPostId === selectedCommunityPost.id"
                  class="community-like-burst"
                  aria-hidden="true"
                >
                  <image
                    v-for="bubble in communityLikeBurstBubbles"
                    :key="bubble"
                    class="community-like-bubble"
                    :src="communityLikeFilledIconSrc"
                    mode="aspectFit"
                  />
                </view>
              </view>
              <text>{{ selectedCommunityPost.stats.likes }}</text>
            </button>
          </view>
      </view>

      <view v-if="false" class="community-detail-sheet" @tap.stop>
        <view class="community-detail-handle"></view>
        <button class="community-detail-close" aria-label="关闭帖子详情" @tap="closeCommunityPost"><CloseIcon /></button>
        <view class="community-detail-heading">帖子详情</view>
        <scroll-view scroll-y class="community-detail-scroll">
          <view class="community-detail-author-row">
            <view class="community-avatar" :class="`tone-${selectedCommunityPost.tone}`">
              <image v-if="selectedCommunityPost.avatarUrl" class="community-avatar-image" :src="selectedCommunityPost.avatarUrl" mode="aspectFill" />
              <text v-else>{{ selectedCommunityPost.avatar }}</text>
            </view>
            <view class="community-author-main">
              <view class="community-author-name">{{ selectedCommunityPost.author }}</view>
              <view class="community-author-meta">{{ selectedCommunityPost.publishTime }}</view>
            </view>
            <view class="community-topic-list community-detail-topic-list">
              <view
                v-for="tag in getCommunityPostTags(selectedCommunityPost)"
                :key="`detail-${selectedCommunityPost.id}-${tag}`"
                class="community-topic"
              >{{ tag }}</view>
            </view>
          </view>

          <view class="community-detail-title">{{ selectedCommunityPost.title }}</view>
          <view class="community-detail-copy">{{ selectedCommunityPost.content || selectedCommunityPost.summary }}</view>

          <view
            v-if="selectedCommunityPost.media && selectedCommunityPost.media.length"
            class="community-media-grid community-detail-media"
            :class="`count-${selectedCommunityPost.media.length}`"
          >
            <view
              v-for="media in selectedCommunityPost.media"
              :key="media.imageUrl || media.image_url || `${media.kicker}-${media.title}`"
              class="community-media-tile"
              :class="[`tone-${media.tone}`, { 'is-image': media.imageUrl || media.image_url }]"
            >
              <image v-if="media.imageUrl || media.image_url" class="community-media-image" :src="media.imageUrl || media.image_url" mode="aspectFill" />
              <view v-else class="community-media-text">
                <view class="community-media-kicker">{{ media.kicker }}</view>
                <view class="community-media-title">{{ media.title }}</view>
                <view class="community-media-copy">{{ media.copy }}</view>
              </view>
            </view>
          </view>

          <view class="community-detail-stats">
            <button
              class="community-detail-like"
              :class="{ active: selectedCommunityPost.liked, pending: isCommunityPostLikePending(selectedCommunityPost.id) }"
              @tap="toggleCommunityLike(selectedCommunityPost)"
            >
              <image src="/static/ui-icons/png/original/circle-like.png" mode="aspectFit" />
              <text>{{ selectedCommunityPost.liked ? '已点赞' : '点赞' }} {{ selectedCommunityPost.stats.likes }}</text>
            </button>
            <text>{{ selectedCommunityPost.stats.views }} 浏览</text>
          </view>

          <button class="community-detail-comments-entry" @tap="openCommunityComments(selectedCommunityPost)">
            <view>
              <view class="community-detail-comments-count">评论 {{ selectedCommunityPost.stats.comments }}</view>
              <view class="community-detail-comments-copy">查看全部评论并参与讨论</view>
            </view>
            <text>查看评论</text>
          </button>
        </scroll-view>
      </view>
    </view>

      <view v-if="false && selectedCommunityCommentsPost" class="community-comments-mask" @tap="closeCommunityComments">
      <view class="community-comments-sheet" @tap.stop>
        <view class="community-detail-handle"></view>

        <view class="community-comments-toolbar">
          <view class="community-comments-counts">
            <button
              class="community-comments-count"
              :class="{ active: communityInteractionTab === 'comments' }"
              @tap="selectCommunityInteractionTab('comments')"
            >评论 {{ selectedCommunityCommentsPost.stats.comments }}</button>
            <button
              class="community-comments-count"
              :class="{ active: communityInteractionTab === 'likes' }"
              @tap="selectCommunityInteractionTab('likes')"
            >点赞 {{ selectedCommunityCommentsPost.stats.likes }}</button>
          </view>
          <view v-if="communityInteractionTab === 'comments'" class="community-comment-sort" aria-label="评论排序">
            <button
              class="community-comment-sort-button"
              :class="{ active: communityCommentSort === 'default' }"
              @tap="communityCommentSort = 'default'"
            >默认</button>
            <button
              class="community-comment-sort-button"
              :class="{ active: communityCommentSort === 'latest' }"
              @tap="communityCommentSort = 'latest'"
            >最新</button>
            <button
              class="community-comment-sort-button"
              :class="{ active: communityCommentSort === 'earliest' }"
              @tap="communityCommentSort = 'earliest'"
            >最早</button>
          </view>
          <button class="community-detail-close community-comments-close" aria-label="关闭评论" @tap="closeCommunityComments"><CloseIcon /></button>
        </view>

        <scroll-view scroll-y class="community-comments-scroll">
          <template v-if="communityInteractionTab === 'comments'">
            <AppPageLoadingState v-if="communityCommentsLoading" compact message="正在整理评论..." />
            <AppEmptyState
              v-else-if="sortedCommunityComments.length === 0"
              compact
              label="暂无评论"
              title="暂无评论"
              description="来留下第一条讨论吧。"
            />
            <view v-else class="community-comments-list">
              <view v-for="comment in sortedCommunityComments" :key="comment.id" class="community-comments-item">
                <view class="community-comments-avatar">
                  <image v-if="comment.avatarUrl" class="community-comments-avatar-image" :src="comment.avatarUrl" mode="aspectFill" />
                  <text v-else>{{ comment.avatar }}</text>
                </view>
                <view class="community-comments-main">
                  <view class="community-comments-author">{{ comment.author }}</view>
                  <view class="community-comments-copy">{{ comment.content }}</view>
                  <view class="community-comments-time">{{ formatCommunityCommentTime(comment.createdAt) }}</view>
                </view>
              </view>
            </view>
          </template>
          <template v-else>
            <AppPageLoadingState v-if="communityLikesLoading" compact message="正在整理点赞用户..." />
            <AppEmptyState
              v-else-if="communityLikes.length === 0"
              compact
              label="暂无点赞"
              title="暂无点赞"
              description="来成为第一位点赞的研友吧。"
            />
            <view v-else class="community-likes-list">
              <view v-for="like in communityLikes" :key="like.id" class="community-likes-item">
                <view class="community-likes-avatar">
                  <image v-if="like.avatarUrl" class="community-likes-avatar-image" :src="like.avatarUrl" mode="aspectFill" />
                  <text v-else>{{ like.avatar }}</text>
                </view>
                <view class="community-likes-main">
                  <view class="community-likes-author">{{ like.author }}</view>
                  <view class="community-likes-time">{{ formatCommunityCommentTime(like.likedAt) }} 点赞</view>
                </view>
              </view>
            </view>
          </template>
        </scroll-view>

        <view v-if="communityInteractionTab === 'comments'" class="community-comment-composer community-comments-composer">
          <input
            v-model="communityCommentDraft"
            class="community-comment-input"
            maxlength="500"
            confirm-type="send"
            placeholder="写下你的评论吧"
            placeholder-class="community-comment-placeholder"
            :disabled="communityCommentSubmitting"
            @confirm="submitCommunityComment"
          />
          <button
            class="community-comment-submit"
            :disabled="communityCommentSubmitting || !communityCommentDraft.trim()"
            @tap="submitCommunityComment"
          >
            {{ communityCommentSubmitting ? '发送中' : '发送' }}
          </button>
        </view>
      </view>
    </view>

    <view v-if="selectedCirclePost" class="circle-post-mask" @tap="closeCirclePost">
      <view class="circle-post-sheet" @tap.stop>
        <view class="circle-post-handle"></view>
        <button class="circle-post-close" aria-label="关闭" @tap="closeCirclePost"><CloseIcon /></button>
        <view class="circle-post-tag">{{ selectedCirclePost.tag }}</view>
        <view class="circle-post-title">{{ selectedCirclePost.title }}</view>
        <view class="circle-post-author-row">
          <view class="experience-avatar circle-post-avatar">
            <image v-if="selectedCirclePost.avatarUrl" class="experience-avatar-image" :src="selectedCirclePost.avatarUrl" mode="aspectFill" />
            <text v-else>{{ selectedCirclePost.avatar }}</text>
          </view>
          <view class="circle-post-author-main">
            <view class="circle-post-author-name">{{ selectedCirclePost.author }}</view>
            <view class="circle-post-meta">{{ selectedCirclePost.authorRole }} · {{ selectedCirclePost.examCode }} · {{ selectedCirclePost.readTime }}</view>
          </view>
        </view>
        <view class="circle-post-stat-row">
          <text>{{ selectedCirclePost.subject }}</text>
          <text>{{ selectedCirclePost.publishDate }} 发布</text>
          <text>{{ selectedCirclePost.stats.views }} 阅读</text>
        </view>
        <scroll-view scroll-y class="circle-post-scroll">
          <view
            v-for="section in selectedCirclePost.sections"
            :key="section.heading"
            class="circle-post-section"
          >
            <view class="circle-post-section-title">{{ section.heading }}</view>
            <view class="circle-post-paragraph">{{ section.body }}</view>
          </view>
          <view class="circle-post-checklist">
            <view v-for="point in selectedCirclePost.points" :key="point" class="circle-post-point">
              <text>✓</text>
              <text>{{ point }}</text>
            </view>
          </view>
          <view class="circle-post-action-row">
            <button @tap="handleCirclePostLocalAction('点赞')">点赞 {{ selectedCirclePost.stats.likes }}</button>
            <button @tap="handleCirclePostLocalAction('收藏')">收藏 {{ selectedCirclePost.stats.saves }}</button>
          </view>
        </scroll-view>
      </view>
    </view>

    <view
      v-if="mentorFilterMounted"
      class="mentor-filter-mask"
      :class="{ 'is-visible': mentorFilterVisible, 'is-leaving': mentorFilterClosing }"
      @tap="closeMentorFilterSheet"
    >
        <view class="mentor-filter-sheet" @tap.stop>
          <view class="mentor-filter-sheet-heading">
            <button class="mentor-filter-sheet-close" aria-label="关闭筛选" @tap="closeMentorFilterSheet">
              <text class="mentor-filter-sheet-close-icon" aria-hidden="true">×</text>
            </button>
          </view>

          <scroll-view class="mentor-filter-sheet-scroll" scroll-y>
            <view class="mentor-filter-sheet-body">
              <view class="mentor-filter-field">
                <view class="mentor-filter-field-label">考试类型</view>
                <view class="mentor-filter-option-row">
                  <button
                    v-for="item in mentorExamTypeOptions"
                    :key="item"
                    :class="{ active: mentorFilterDraft.examType === item }"
                    @tap="mentorFilterDraft.examType = item"
                  >{{ item }}</button>
                </view>
              </view>

              <view class="mentor-filter-field">
                <view class="mentor-filter-field-label">录取年份</view>
                <view class="mentor-filter-option-row">
                  <button
                    v-for="item in mentorAdmissionYearOptions"
                    :key="item"
                    :class="{ active: mentorFilterDraft.admissionYear === item }"
                    @tap="mentorFilterDraft.admissionYear = item"
                  >{{ item }}</button>
                </view>
              </view>

              <view class="mentor-filter-field">
                <view class="mentor-filter-field-label">咨询价格</view>
                <view class="mentor-filter-option-row">
                  <button
                    v-for="item in mentorPriceOptions"
                    :key="item"
                    :class="{ active: mentorFilterDraft.price === item }"
                    @tap="mentorFilterDraft.price = item"
                  >{{ item }}</button>
                </view>
              </view>

              <view class="mentor-filter-field">
                <view class="mentor-filter-field-label">当前状态</view>
                <view class="mentor-filter-option-row">
                  <button
                    v-for="item in mentorAvailabilityOptions"
                    :key="item"
                    :class="{ active: mentorFilterDraft.availability === item }"
                    @tap="mentorFilterDraft.availability = item"
                  >{{ item }}</button>
                </view>
              </view>
            </view>
          </scroll-view>

          <view class="mentor-filter-sheet-actions">
            <button class="mentor-filter-reset-button" @tap="resetMentorFilters">
              <text class="mentor-filter-action-label">重置</text>
            </button>
            <button class="mentor-filter-confirm-button" @tap="applyMentorFilters">
              <text class="mentor-filter-action-label">查看结果{{ mentorFilteredResultCount ? `（${mentorFilteredResultCount}）` : '' }}</text>
            </button>
          </view>
        </view>
    </view>

    <!-- #ifdef H5 -->
    <IcpFooter
      v-if="activeTab !== 'landing'"
      :class="{ 'is-route-obscured': isCircleDetail || isScoreLineBrowser || ['mistakes', 'report'].includes(activeTab) }"
      :compact="showBottomTab"
      :inline="showBottomTab"
      :lower="activeTab === 'home' || activeTab === 'profile'"
      :glass="true"
    />
    <!-- #endif -->
    <button
      v-if="showCommunityPublishButton && selectedCircleCommunityTab === 'mentor'"
      class="community-publish-button"
      :class="{
        'mentor-console-entry': mentorEntryStatus === 'verified',
        'mentor-pending-entry': mentorEntryStatus === 'pending'
      }"
      type="button"
      :aria-label="mentorEntryAriaLabel"
      @tap.stop="openMentorVerificationEntry"
    >
      <view v-if="mentorEntryLabel" class="mentor-entry-content">
        <view v-if="mentorEntryStatus === 'verified'" class="mentor-entry-grid-icon" aria-hidden="true">
          <view></view><view></view><view></view><view></view>
        </view>
        <view v-else class="mentor-entry-pending-dot" aria-hidden="true"></view>
        <text>{{ mentorEntryLabel }}</text>
      </view>
      <image v-else src="/static/ui-icons/png/original/circle-publish.png" mode="aspectFit" />
    </button>
    <button
      v-else-if="showCommunityPublishButton && selectedCircleCommunityTab === 'experience'"
      class="community-publish-button"
      type="button"
      aria-label="发布经验贴"
      @tap.stop="openExperiencePublishPage"
    >
      <image src="/static/ui-icons/png/original/circle-publish.png" mode="aspectFit" />
    </button>
    <button
      v-else-if="showCommunityPublishButton"
      class="community-publish-button"
      type="button"
      aria-label="发布话题"
      @tap.stop="openChatPublishPage"
    >
      <image src="/static/ui-icons/png/original/circle-publish.png" mode="aspectFit" />
    </button>
    <BottomTabBar
      v-if="renderBottomTab"
      :class="{ 'is-circle-route-underlay-tab': isCircleDetail }"
      v-model="activeTab"
      :items="tabs"
      :glass="true"
      :collapsed="isCircleDetail ? false : isCircleTabbarCollapsed"
      :theme-key="selectedThemeKey"
      @expand="expandCircleTabbar"
    />
  </view>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { onBackPress, onHide, onLoad, onPageScroll, onReachBottom, onShow } from '@dcloudio/uni-app'
import BottomTabBar from '../../components/BottomTabBar.vue'
import CanvasLineChart from '../../components/CanvasLineChart.vue'
import CloseIcon from '../../components/CloseIcon.vue'
import CircleResourceSection from '../../components/CircleResourceSection.vue'
import IcpFooter from '../../components/IcpFooter.vue'
import MembershipSubscriptionPreview from '../../components/MembershipSubscriptionPreview.vue'
import AppEmptyState from '../../components/ui/AppEmptyState.vue'
import AppPageHeader from '../../components/ui/AppPageHeader.vue'
import AppPageLoadingState from '../../components/ui/AppPageLoadingState.vue'
import AppSearchIcon from '../../components/ui/AppSearchIcon.vue'
import MistakeList from '../../components/MistakeList.vue'
import MentorConsultCard from '../../components/MentorConsultCard.vue'
import ModuleCard from '../../components/ModuleCard.vue'
import SectionCard from '../../components/SectionCard.vue'
import MathText from '../../components/MathText.vue'
import { createAiTrainingRequestTask, fetchAiTrainingRecommendation } from '../../api/ai'
import { fetchMembershipStatus, fetchSubscriptionPageConfig } from '../../api/membership'
import { createSubscriptionPageConfig } from '../../data/membershipSubscription'
import {
  bindPhone,
  bindWechatEmail,
  changeEmailWithCode,
  sendBindPhoneCode,
  sendBindEmailCode,
  sendChangeEmailCode,
  updateProfile,
  uploadAvatar
} from '../../api/auth'
import {
  createCommunityComment,
  deleteCommunityComment,
  deleteMyCommunityPosts,
  fetchCommunityComments,
  fetchMyCommunityPost,
  fetchCommunityPost,
  fetchCommunityPostLikes,
  fetchCommunityPosts,
  registerCommunityPostView,
  toggleCommunityCommentLike as toggleCommunityCommentLikeRequest,
  toggleCommunityPostLike
} from '../../api/community'
import { fetchOfficialMessages } from '../../api/officialMessages'
import {
  fetchUserNotificationUnreadSummary,
  fetchUserNotifications,
  markUserNotificationReadTarget
} from '../../api/notifications'
import { fetchHomeContent, fetchPublishedScorelines } from '../../api/homeContent'
import {
  fetchMentorProfiles,
  fetchMyMentorFavorites,
  fetchMyMentorProfile,
  fetchMyMentorVerificationApplication,
  toggleMentorFavoriteRequest
} from '../../api/mentorConsultation'
import {
  fetchAbilityReport,
  fetchDailyStudyLeaderboard,
  fetchLearningSummary,
  fetchPlatformPracticeTrend
} from '../../api/reports'
import { fetchWrongQuestionDetail, fetchWrongQuestions, reviewWrongQuestion } from '../../api/wrongQuestions'
import {
  historicalScoreLineRecords as fallbackHistoricalScoreLineRecords,
  historicalScoreLineRegions as fallbackHistoricalScoreLineRegions,
  historicalScoreLineStats as fallbackHistoricalScoreLineStats,
  historicalScoreLineYears as fallbackHistoricalScoreLineYears
} from '../../data/historicalScoreLines'
import {
  MENTOR_ADMISSION_YEAR_OPTIONS,
  MENTOR_AVAILABILITY_OPTIONS,
  MENTOR_EXAM_TYPE_OPTIONS,
  MENTOR_PRICE_OPTIONS,
  MENTOR_SORT_OPTIONS,
  cacheMentors,
  createDefaultMentorFilters,
  filterMentors,
  getCachedMentorDirectory,
  getMentorFavoriteIds,
  getMentorVerificationStatus,
  normalizeMentorListResponse,
  setMentorVerificationStatus,
  setMentorFavoriteIds
} from '../../data/mentorConsultation'
import {
  getFullMistakes,
  getHomeDashboard,
  getHomeModules,
  getProfileMock,
  getReportMock
} from '../../mock/appMock'
import { clearAuthSession, getAuthUser, isLoggedIn, saveAuthSession, updateAuthUser } from '../../utils/auth'
import { EXAM_OPTIONS } from '../../utils/exam'
import { getOriginalIconSrc, getSubjectIconSrc, getThemeIconSrc, getToneIconSrc } from '../../utils/iconAssets'
import { buildMpPageSafeStyle } from '../../utils/mpSafeLayout'
import { applyThemeByKey, buildThemeStyle, getStoredThemeKey, getThemePreset } from '../../utils/theme'
import { getPublicEmail, getUserContactLabel, getUserDisplayName } from '../../utils/userDisplay'

const examOptions = EXAM_OPTIONS
const ENABLE_CIRCLE = true
const CIRCLE_DETAIL_ROUTE_DURATION = 380
const MY_POSTS_REFRESH_REQUIRED_KEY = 'circle-my-posts-refresh-required'
const COMMUNITY_POST_EDIT_RESULT_KEY = 'circle-community-post-edit-result'
const CIRCLE_DETAIL_ROUTE_FRAME_DELAY = 32
const CIRCLE_DETAIL_ROUTE_FALLBACK_DELAY = 80
const CIRCLE_EDGE_SWIPE_START_WIDTH = 28
const CIRCLE_EDGE_SWIPE_LOCK_DISTANCE = 8
const CIRCLE_EDGE_SWIPE_FINISH_PROGRESS = 0.3
const CIRCLE_EDGE_SWIPE_FINISH_VELOCITY = 0.45
const CIRCLE_EDGE_SWIPE_MIN_FLING_DISTANCE = 42
const CIRCLE_SCORE_MIRROR_WIDTH = 300
const CIRCLE_SCORE_MIRROR_HEIGHT = 112
const COMMUNITY_READER_DOUBLE_TAP_WINDOW = 320
const historicalScoreLineYears = reactive([...fallbackHistoricalScoreLineYears])
const historicalScoreLineRecords = reactive(fallbackHistoricalScoreLineRecords.map((record) => ({
  ...record,
  scores: { ...record.scores }
})))
const historicalScoreLineRegions = reactive(fallbackHistoricalScoreLineRegions.map((region) => ({ ...region })))
const historicalScoreLineStats = reactive({
  ...fallbackHistoricalScoreLineStats,
  yearAvailability: { ...(fallbackHistoricalScoreLineStats.yearAvailability || {}) }
})
const historicalScoreLineDisplayYears = computed(() => [...historicalScoreLineYears].sort().reverse())
const historicalScoreLineTrendRecords = computed(() => historicalScoreLineRecords.filter((record) => (
  historicalScoreLineYears.length >= 2 && historicalScoreLineYears.every((year) => record.scores?.[year]?.kind === 'score')
)))
const initialAuthUser = getAuthUser()
const examCode = ref(uni.getStorageSync('examCode') || initialAuthUser?.exam_target || 'Z001')
const activeTab = ref('landing')
const authUser = ref(initialAuthUser)
const authed = ref(isLoggedIn())
const wrongItems = ref([])
const wrongLoading = ref(false)
const wrongNextCursor = ref('')
const wrongHasMore = ref(false)
const wrongLoadingMore = ref(false)
const wrongError = ref('')
const visibleMistakeCount = ref(15)
const abilityReport = ref(null)
const learningSummary = ref(null)
const practiceOverviewIndex = ref(0)
const dailyLeaderboardItems = ref([])
const dailyLeaderboardCurrentUser = ref(null)
const dailyLeaderboardLoading = ref(false)
const dailyLeaderboardLoaded = ref(false)
const dailyLeaderboardError = ref('')
const dailyLeaderboardUpdatedAt = ref(0)
const DAILY_LEADERBOARD_REFRESH_INTERVAL = 30000
let dailyLeaderboardRefreshTimer = null
const studyAdvice = ref(null)
const studyAdviceLoading = ref(false)
const studyAdviceError = ref('')
const studyAdviceExamCode = ref('')
const reportLoading = ref(false)
const reportError = ref('')
const wrongFilters = ref({
  subject: '',
  module: '',
  submodule: ''
})
const selectedWrongDetail = ref(null)
const reviewAnswer = ref('')
const reviewingWrong = ref(false)
const reviewResultText = ref('')
const reviewMastered = ref(false)
const retestMode = ref(false)
const retestItems = ref([])
const retestIndex = ref(0)
const retestDetail = ref(null)
const retestAnswer = ref('')
const retestSubmitting = ref(false)
const retestResultText = ref('')
const retestResults = ref([])
const retestLoading = ref(false)
const retestCompleted = ref(false)
const reviewSubmissionId = ref('')
const retestSubmissionIds = ref({})
const circleCommunityHeaderScrollTop = ref(0)
const showTrainingSheet = ref(false)
const showSubscriptionSheet = ref(false)
const subscriptionSheetVisible = ref(false)
const subscriptionSheetDragY = ref(0)
const subscriptionSheetDragging = ref(false)
const subscriptionPageConfig = ref(createSubscriptionPageConfig())
const subscriptionMembership = ref(createDefaultSubscriptionMembershipStatus())
let subscriptionSheetOpenTimer = null
let subscriptionSheetCloseTimer = null
let subscriptionMembershipRequest = null
let subscriptionSheetDragStartY = 0
let subscriptionSheetDragStartAt = 0
const showStudyAdviceDetail = ref(false)
const showExamSwitchModal = ref(false)
const showProfileEditModal = ref(false)
const showEmailBindingModal = ref(false)
const showPhoneBindingModal = ref(false)
const profileEditNickname = ref('')
const profileEditAvatarPreview = ref('')
const profileEditAvatarPath = ref('')
const profileEditAvatarFile = ref(null)
const profileEditAvatarName = ref('avatar.jpg')
const profileEditSaving = ref(false)
const profileEditUploading = ref(false)
const profileEmailForm = reactive({ email: '', code: '' })
const profileEmailSending = ref(false)
const profileEmailSaving = ref(false)
const profilePhoneForm = reactive({ phone: '', code: '' })
const profilePhoneSending = ref(false)
const profilePhoneSaving = ref(false)
const profilePhoneCountdown = ref(0)
let profilePhoneCountdownTimer = null
const officialUnreadCount = ref(0)
const notificationUnreadCount = ref(0)
const communityUnreadCount = ref(0)
const postInteractionUnreadCount = ref(0)
const communityReportUnreadCount = ref(0)
const consultationUnreadCount = ref(0)
const communityChatUnreadCount = ref(0)
const communityExperienceUnreadCount = ref(0)
const applicantConsultationUnreadCount = ref(0)
const mentorConsultationUnreadCount = ref(0)
const communityPostUnreadTargets = ref({ chat: {}, experience: {} })
const messageUnreadCount = computed(() => officialUnreadCount.value + notificationUnreadCount.value)
let latestUnreadRefreshToken = 0
const selectedThemeKey = ref(getStoredThemeKey())
const generatingTraining = ref(false)
const recommendationLoading = ref(false)
const selectedCircleSection = ref('overview')
const selectedCirclePost = ref(null)
const circleDetailVisible = ref(false)
const circleDetailMounted = ref(false)
const circleOverviewVisible = ref(true)
const circleAppRouteUnderlay = ref(false)
const circleDetailRouteMotion = ref('idle')
const circleDetailScrollTop = ref(0)
const circleOverviewScrollTop = ref(0)
let circleOverviewRestoreTimer = null
let circleDetailRouteFrameTimer = null
let circleDetailRouteFinishTimer = null
let circleDetailReturnScrollTop = 0
const circleEdgeSwipeStart = ref(null)
const circleEdgeSwipeOffset = ref(0)
const circleEdgeSwipeViewportWidth = ref(375)
const circleEdgeSwipeSettleDuration = ref(CIRCLE_DETAIL_ROUTE_DURATION)
const communityReaderEdgeSwipeStart = ref(null)
const circleInsightIndex = ref(0)
const circleScoreSchoolIndex = ref(
  historicalScoreLineTrendRecords.value.length > 1
    ? Math.floor(Math.random() * historicalScoreLineTrendRecords.value.length)
    : 0
)
const circleScoreTooltip = ref({ scope: '', index: -1 })
const isCircleScoreSwiperPaused = ref(false)
let circleScorePointHoldTimer = null
let circleScoreTooltipDismissTimer = null
const selectedScoreLineRecord = ref(null)
const selectedScoreLineRecordEntry = ref('list')
const scoreLineSearchKeyword = ref('')
const selectedScoreLineRegion = ref('全部')
const selectedScoreLineYear = ref('全部')
const visibleScoreLineRecordCount = ref(24)
const selectedExperienceCategory = ref('全部')
const experienceSearchKeyword = ref('')
const selectedCircleCommunityTab = ref('chat')
const selectedCommunityCategory = ref('全部')
const communitySearchKeyword = ref('')
const communityAppliedSearch = reactive({ chat: '', experience: '' })
const selectedCommunityPostSort = ref('latest')
const mentorSearchKeyword = ref('')
const selectedMentorSort = ref('recommended')
// 先回填上一次成功加载的公开目录，首屏不再因为等待网络而整块留白。
const mentorProfiles = ref(getCachedMentorDirectory())
const mentorProfilesLoading = ref(false)
const mentorProfilesLoaded = ref(false)
const mentorProfilesError = ref('')
const mentorEntryStatus = ref(isLoggedIn() ? getMentorVerificationStatus() : 'unverified')
const mentorEntryStatusLoaded = ref(false)
const openingMyConsultationEntry = ref(false)
const currentMentorProfileId = ref('')
let mentorEntryStatusRequest = null
let mentorEntryStatusLastConfirmedAt = 0
const MENTOR_ENTRY_STATUS_FRESH_MS = 60 * 1000
const mentorFilters = ref(createDefaultMentorFilters())
const mentorFilterDraft = ref(createDefaultMentorFilters())
const mentorFilterMounted = ref(false)
const mentorFilterVisible = ref(false)
const mentorFilterClosing = ref(false)
let mentorFilterCloseTimer = null
const mentorFavoriteIds = ref(getMentorFavoriteIds())
const mentorFavoritePendingIds = ref([])
const selectedCommunityPost = ref(null)
const communityReaderClosing = ref(false)
const communityReaderRouteMotion = ref('idle')
const communityReaderEntrySource = ref('')
const communityReaderOwnerPreview = ref(false)
const communityReaderOwnerLoading = ref(false)
const communityReaderInteractionsEnabled = ref(true)
let communityReaderRouteFrameTimer = null
let communityReaderRouteFinishTimer = null
const selectedCommunityCommentsPost = ref(null)
const communityReaderScrollTarget = ref('')
const communityReaderMediaIndex = ref(0)
const communityComments = ref([])
const communityCommentsLoading = ref(false)
const communityCommentsLoadingMore = ref(false)
const communityCommentsNextCursor = ref('')
const communityCommentsHasMore = ref(false)
const communityCommentsLoadError = ref('')
const communityInteractionTab = ref('comments')
const communityLikes = ref([])
const communityLikesLoading = ref(false)
const communityCommentSort = ref('default')
const communityPostsLoading = ref(false)
const communityFeedNextCursors = reactive({})
const communityFeedHasMore = reactive({})
const communityFeedPages = reactive({})
const communityFeedErrors = reactive({})
const communityFeedLoadingState = reactive({})
const communityLikeIconSrc = '/static/ui-icons/png/original/circle-like.png'
const communityLikeFilledIconSrc = '/static/ui-icons/png/original/circle-like-filled.png'
const communityLikeBurstPostId = ref('')
const communityLikeBurstBubbles = Object.freeze([1, 2, 3])
const communityCommentDraft = ref('')
const communityCommentSubmitting = ref(false)
const communityCommentEntryReady = ref(false)
const communityCommentInputFocused = ref(false)
const communityCommentKeyboardOffset = ref(0)
const communityCommentKeyboardVisible = ref(false)
const communityCommentKeyboardTransitionMs = ref(180)
const communityReaderActionsStyle = computed(() => ({
  transform: `translate3d(0, -${Math.max(0, Number(communityCommentKeyboardOffset.value) || 0)}px, 0)`,
  transitionDuration: `${Math.max(0, Number(communityCommentKeyboardTransitionMs.value) || 0)}ms`
}))
let communityReaderTopZoneLastTapAt = 0
let communityReaderLastScrollTop = 0
let communityCommentInputFocusStartedAt = 0
let communityCommentVisibilityTimer = null
let communityCommentKeyboardHeight = 0
let communityReaderViewportBaseHeight = 0
let communityCommentKeyboardSyncTimer = null
let communityCommentKeyboardResetTimer = null
let communityCommentVisualViewportBound = false
let communityCommentKeyboardSyncRevision = 0
let communitySearchDebounceTimer = null
const communityPostLikePendingIds = reactive({})
const communityCommentLikePendingIds = reactive({})
const communityPostLikeQueues = new Map()
const communityCommentLikeQueues = new Map()
const circleTabCollapsed = ref(false)
const circleLastScrollTop = ref(0)
const homeFocusIndex = ref(0)

const homeFocusItems = reactive([
  {
    badge: '考试提醒',
    title: '初试统考准考证打印提醒',
    subtitle: '广州报考点考生请及时核对考试信息',
    artLabel: '准考证',
    url: 'https://www.gatzs.com.cn/'
  },
  {
    badge: '官方公告',
    title: '广州报考点招生通告',
    subtitle: '报名、确认与考试方式一次看清',
    artLabel: '报考点',
    url: 'https://www.gatzs.com.cn/gatzsinfo/yzDetailInfo.action?categoryId=858151&infoId=3540991750&schId=858091'
  },
  {
    badge: '备考指南',
    title: 'Z001 / Z002 考试指南',
    subtitle: '了解考试模块、范围与备考方向',
    artLabel: '考试指南',
    url: 'https://yankao.neea.edu.cn/html1/report/2512/13-1.htm'
  }
])

const homeNewsItems = reactive([
  {
    source: '广东省教育考试院',
    title: '2026年面向港澳台地区研究生招生初试统考《准考证》打印提醒及广州报考点考生须知',
    date: '2026-04-01',
    coverLabel: '准考证打印',
    coverTone: 'is-blue',
    url: 'https://www.gatzs.com.cn/'
  },
  {
    source: '广东省教育考试院',
    title: '2026年港澳台研究生招生广州报考点通告',
    date: '2025-12-16',
    coverLabel: '广州报考点',
    coverTone: 'is-orange',
    url: 'https://eea.gd.gov.cn/yjsks/content/post_4830103.html'
  },
  {
    source: '教育部教育考试院',
    title: '2026年面向香港、澳门、台湾地区研究生招生考试指南正式公布',
    date: '2025-12-07',
    coverLabel: '考试指南',
    coverTone: 'is-mint',
    url: 'https://yankao.neea.edu.cn/html1/report/2512/13-1.htm'
  }
])

const homeServiceItems = [
  {
    key: 'school-notices',
    title: '院校公告',
    iconSrc: '/static/ui-icons/png/original/home-school-notices.png',
    tone: 'is-school'
  },
  {
    key: 'major-catalog',
    title: '专业目录',
    iconSrc: '/static/ui-icons/png/original/home-major-catalog.png',
    tone: 'is-major'
  },
  {
    key: 'application-guide',
    title: '报考指南',
    iconSrc: '/static/ui-icons/png/original/home-application-guide.png',
    tone: 'is-guide'
  }
]

applyThemeByKey(selectedThemeKey.value)
const smartMode = ref(true)
const manualDifficulty = ref('标准提升')
const manualQuestionCount = ref(10)
const trainingSubject = ref('')
const showGeneratingModal = ref(false)
const generateEstimate = ref(45)
const generateCountdown = ref(45)
const generationCancelled = ref(false)
let generateTimerId = null
let generateRequestTask = null
let communityViewTimerId = null
let communityLikeBurstTimerId = null
let communityFeedPersistTimerId = null
let lastCommunityPublishNavigationAt = 0
let openingExperiencePublishEntry = false
let openingMentorVerificationEntry = false
const communityPostsLoadingTypes = new Set()
const COMMUNITY_FEED_PAGE_SIZE = 12
const COMMUNITY_FEED_CACHE_TTL = 60 * 1000
const COMMUNITY_FEED_CACHE_PREFIX = 'circle-community-feed-v5'
const communityFeedCacheHydratedKeys = new Set()
const communityFeedCacheFreshness = new Map()
const communityFeedPageFreshness = new Map()
const pendingCommunityFeedPersistTypes = new Set()
let communityFeedPrefetchStarted = false
const tabs = computed(() => {
  const items = [
    {
      key: 'landing',
      label: '首页',
      icon: '',
      iconSrc: '/static/ui-icons/png/original/tab-home.png'
    },
    {
      key: 'home',
      label: '刷题',
      iconClass: 'tab-icon-practice',
      iconSrc: '/static/ui-icons/png/original/tab-practice.png'
    }
  ]

  if (ENABLE_CIRCLE) {
    items.push({
      key: 'circle',
      label: '研圈',
      iconSrc: '/static/ui-icons/png/original/tab-circle.png',
      unread: communityUnreadCount.value > 0
    })
  }

  items.push({
    key: 'profile',
    label: '我的',
    iconSrc: '/static/ui-icons/png/original/tab-profile.png'
  })

  return items
})
const isCircleDetail = computed(() => (
  activeTab.value === 'circle' && circleDetailVisible.value
))
const showBottomTab = computed(() =>
  !retestMode.value
  && !['mistakes', 'report'].includes(activeTab.value)
  && !isCircleDetail.value
)
const renderBottomTab = computed(() => (
  !retestMode.value && (showBottomTab.value || isCircleDetail.value)
))
const isScoreLineBrowser = computed(() => (
  isCircleDetail.value &&
  selectedCircleSection.value === 'scores' &&
  !selectedScoreLineRecord.value
))
const isCircleTabbarCollapsed = computed(() => isCircleDetail.value && circleTabCollapsed.value)
const circleEdgeSwipeProgress = computed(() => {
  const width = Math.max(1, Number(circleEdgeSwipeViewportWidth.value) || 1)
  return Math.min(1, Math.max(0, circleEdgeSwipeOffset.value / width))
})
const circleDetailRouteStyle = computed(() => {
  const motion = circleDetailRouteMotion.value
  if (!['dragging', 'drag-cancelling', 'drag-leaving'].includes(motion)) return {}

  const offset = Math.max(0, Number(circleEdgeSwipeOffset.value) || 0)
  const duration = Math.max(0, Number(circleEdgeSwipeSettleDuration.value) || 0)
  const settling = motion !== 'dragging'
  const style = {
    transition: settling
      ? `transform ${duration}ms cubic-bezier(0.22, 0.82, 0.24, 1)`
      : 'none',
    transform: `translate3d(${offset}px, 0, 0)`,
    willChange: 'transform'
  }

  // #ifdef APP-PLUS
  if (selectedCircleSection.value === 'scores') {
    style.right = 'auto'
    style.left = `${offset}px`
    style.transform = 'none'
    style.transition = settling
      ? `left ${duration}ms cubic-bezier(0.22, 0.82, 0.24, 1)`
      : 'none'
    style.willChange = 'left'
  }
  // #endif

  return style
})
const circleOverviewRouteStyle = computed(() => {
  const motion = circleDetailRouteMotion.value
  if (!['dragging', 'drag-cancelling', 'drag-leaving'].includes(motion)) return {}

  const progress = circleEdgeSwipeProgress.value
  const duration = Math.max(0, Number(circleEdgeSwipeSettleDuration.value) || 0)
  return {
    opacity: String(0.94 + progress * 0.06),
    transform: `translate3d(${-18 + progress * 18}px, 0, 0)`,
    transition: motion === 'dragging'
      ? 'none'
      : `transform ${duration}ms cubic-bezier(0.22, 0.82, 0.24, 1), opacity ${duration}ms ease`
  }
})
const difficultyOptions = ['基础巩固', '标准提升', '强化突破', '冲刺挑战']
const circleSections = [
  {
    key: 'community',
    label: '考研圈',
    iconSrc: '/static/ui-icons/png/original/circle-community.png'
  },
  {
    key: 'scores',
    label: '历年分数线',
    iconSrc: '/static/ui-icons/png/original/circle-scores.png'
  },
  {
    key: 'materials',
    label: '推荐资料',
    iconSrc: '/static/ui-icons/png/original/circle-materials.png'
  },
  {
    key: 'courses',
    label: '精选课程',
    iconSrc: '/static/ui-icons/png/original/circle-courses.png'
  }
]
const CIRCLE_PRACTICE_TREND_DAYS = 7
const CIRCLE_PRACTICE_TREND_REFRESH_MS = 60 * 1000
const circlePracticeTrend = ref(createCirclePracticeTrend())
const circleTrendLoading = ref(false)
const circleTrendLoaded = ref(false)
const circleTrendError = ref('')
const circleTrendLastLoadedAt = ref(0)
const circleScoreSchools = computed(() => historicalScoreLineTrendRecords.value)
const circleScoreYears = computed(() => historicalScoreLineYears.slice(-3))
const circleScoreX = [58, 160, 262]
const activeCircleScoreSchool = computed(() =>
  circleScoreSchools.value[circleScoreSchoolIndex.value] || circleScoreSchools.value[0]
)
const activeCircleScoreValues = computed(() => (
  circleScoreYears.value.map((year) => activeCircleScoreSchool.value?.scores?.[year]?.score || 0)
))
const activeCircleScoreChart = computed(() =>
  getCircleScoreChartConfig(activeCircleScoreValues.value)
)
const circleScoreLinePoints = computed(() =>
  activeCircleScoreValues.value
    .map((score, index) => `${circleScoreX[index]},${getCircleScoreY(score, activeCircleScoreChart.value)}`)
    .join(' ')
)
const activeCircleScoreCanvasPoints = computed(() => (
  activeCircleScoreValues.value.map((score, index) => ({
    x: circleScoreX[index],
    y: getCircleScoreY(score, activeCircleScoreChart.value)
  }))
))
const circleScoreMirrorGridLines = computed(() => (
  activeCircleScoreChart.value.gridY.map((y) => ({
    top: `${(Number(y) / CIRCLE_SCORE_MIRROR_HEIGHT) * 100}%`
  }))
))
const circleScoreMirrorSegments = computed(() => (
  activeCircleScoreCanvasPoints.value.slice(0, -1).map((point, index) => {
    const nextPoint = activeCircleScoreCanvasPoints.value[index + 1]
    const deltaX = Number(nextPoint.x) - Number(point.x)
    const deltaY = Number(nextPoint.y) - Number(point.y)
    return {
      left: `${(Number(point.x) / CIRCLE_SCORE_MIRROR_WIDTH) * 100}%`,
      top: `${(Number(point.y) / CIRCLE_SCORE_MIRROR_HEIGHT) * 100}%`,
      width: `${(Math.hypot(deltaX, deltaY) / CIRCLE_SCORE_MIRROR_WIDTH) * 100}%`,
      transform: `rotate(${Math.atan2(deltaY, deltaX) * 180 / Math.PI}deg)`
    }
  })
))
const circleScoreMirrorPoints = computed(() => (
  activeCircleScoreCanvasPoints.value.map((point) => ({
    left: `${(Number(point.x) / CIRCLE_SCORE_MIRROR_WIDTH) * 100}%`,
    top: `${(Number(point.y) / CIRCLE_SCORE_MIRROR_HEIGHT) * 100}%`
  }))
))
const scoreLineYearFilterOptions = computed(() => ['全部', ...historicalScoreLineDisplayYears.value])
const scoreLineRegionFilterOptions = computed(() => [
  { name: '全部', count: historicalScoreLineStats.recordCount },
  ...historicalScoreLineRegions
])
const scoreLineYearPickerOptions = computed(() => (
  scoreLineYearFilterOptions.value.map((year) => ({
    value: year,
    label: year === '全部' ? '全部年份' : `${year} 年`
  }))
))
const scoreLineRegionPickerOptions = computed(() => (
  scoreLineRegionFilterOptions.value.map((region) => ({
    ...region,
    value: region.name,
    label: region.name === '全部' ? '全部地区' : region.name
  }))
))
const scoreLineYearPickerIndex = computed(() => Math.max(
  0,
  scoreLineYearPickerOptions.value.findIndex((item) => item.value === selectedScoreLineYear.value)
))
const scoreLineRegionPickerIndex = computed(() => Math.max(
  0,
  scoreLineRegionPickerOptions.value.findIndex((item) => item.value === selectedScoreLineRegion.value)
))
const selectedScoreLineYearCompactLabel = computed(() => (
  selectedScoreLineYear.value === '全部' ? '全部' : selectedScoreLineYear.value
))
const selectedScoreLineRegionCompactLabel = computed(() => (
  selectedScoreLineRegion.value === '全部' ? '全部' : selectedScoreLineRegion.value
))
const hasActiveScoreLineFilters = computed(() => (
  Boolean(scoreLineSearchKeyword.value.trim()) ||
  selectedScoreLineRegion.value !== '全部' ||
  selectedScoreLineYear.value !== '全部'
))
const scoreLineResults = computed(() => {
  const keyword = normalizeScoreLineSearch(scoreLineSearchKeyword.value)

  return historicalScoreLineRecords.filter((record) => {
    if (selectedScoreLineRegion.value !== '全部' && record.region !== selectedScoreLineRegion.value) {
      return false
    }

    if (selectedScoreLineYear.value !== '全部' && !getScoreLineValue(record, selectedScoreLineYear.value).raw) {
      return false
    }

    if (!keyword) return true
    const searchable = [
      record.school,
      record.schoolName,
      record.unitName,
      record.region,
      ...historicalScoreLineYears.map((year) => getScoreLineValue(record, year).raw)
    ].join(' ')
    return normalizeScoreLineSearch(searchable).includes(keyword)
  })
})
const visibleScoreLineRecords = computed(() => (
  scoreLineResults.value.slice(0, visibleScoreLineRecordCount.value)
))
const selectedScoreLineValues = computed(() => (
  circleScoreYears.value.map((year) => getScoreLineValue(selectedScoreLineRecord.value, year).score || 0)
))
const selectedScoreLineChart = computed(() =>
  getCircleScoreChartConfig(selectedScoreLineValues.value)
)
const scoreLineDetailLinePoints = computed(() => (
  selectedScoreLineValues.value
    .map((score, index) => `${circleScoreX[index]},${getCircleScoreY(score, selectedScoreLineChart.value)}`)
    .join(' ')
))
const selectedScoreLineCanvasPoints = computed(() => (
  selectedScoreLineValues.value.map((score, index) => ({
    x: circleScoreX[index],
    y: getCircleScoreY(score, selectedScoreLineChart.value)
  }))
))
const circleScoreOverviewActiveIndex = computed(() => (
  circleScoreTooltip.value.scope === 'overview' ? circleScoreTooltip.value.index : -1
))
const circleScoreDetailActiveIndex = computed(() => (
  circleScoreTooltip.value.scope === 'detail' ? circleScoreTooltip.value.index : -1
))
watch(
  [scoreLineSearchKeyword, selectedScoreLineRegion, selectedScoreLineYear],
  () => {
    visibleScoreLineRecordCount.value = 24
  }
)
watch([activeCircleScoreSchool, selectedScoreLineRecord], () => {
  clearCircleScoreTooltip()
})
const circleCommunityTabs = [
  { key: 'chat', label: '研友聊' },
  { key: 'experience', label: '经验贴' },
  { key: 'mentor', label: '前辈咨询' }
]
const communityPostSortOptions = [
  { value: 'latest', label: '最新' },
  { value: 'hot', label: '热门' },
  { value: 'featured', label: '精选' }
]
const circleCommunityCategories = ['全部', '备考日常', '中华文化', '数学基础', '英语运用', '逻辑推理']
const circleCommunitySubjectCategories = circleCommunityCategories.slice(1)
const circleCommunityPosts = ref([])
const circleFeaturedCommunityPosts = ref([])
const circleHotCommunityPosts = ref([])
const circleExperienceExamCodes = ['Z001', 'Z002', '申请制']
const circleExperienceStages = ['初试', '复试']
const circleExperienceCategories = ['全部', ...circleExperienceExamCodes, ...circleExperienceStages]
const circleExperienceCommunityPosts = ref([])
const circleFeaturedExperiencePosts = ref([])
const circleHotExperienceCommunityPosts = ref([])
const filteredCircleCommunityPosts = computed(() => {
  const keyword = communityAppliedSearch.chat.trim().toLowerCase()
  const category = selectedCommunityCategory.value === '全部' ? '' : selectedCommunityCategory.value
  const sourcePosts = getCircleCommunityFeedPosts('chat', {
    featuredOnly: selectedCommunityPostSort.value === 'featured',
    sortBy: selectedCommunityPostSort.value,
    category,
    search: keyword
  })
  return sourcePosts.filter((item) => {
    const matchesCategory = selectedCommunityCategory.value === '全部' || item.category === selectedCommunityCategory.value
    if (!matchesCategory || !keyword) return matchesCategory
    return [
      item.author,
      item.category,
      item.title,
      item.summary,
      ...(item.commentPreviews || []).flatMap((comment) => [comment.author, comment.text]),
      ...item.media.map((media) => `${media.title} ${media.copy}`)
    ]
      .join(' ')
      .toLowerCase()
      .includes(keyword)
  })
})
const sortedCommunityComments = computed(() => {
  const comments = [...communityComments.value]
  if (communityCommentSort.value === 'default') return comments

  const direction = communityCommentSort.value === 'latest' ? -1 : 1
  return comments.sort((left, right) => {
    const leftTimestamp = Date.parse(left.createdAt) || 0
    const rightTimestamp = Date.parse(right.createdAt) || 0
    return (leftTimestamp - rightTimestamp) * direction
  })
})
const communityReaderPostTypeLabel = computed(() => (
  selectedCommunityPost.value?.postType === 'experience' ? '经验贴' : '研友聊'
))
const communityReaderReturnsToMyPosts = computed(() => communityReaderEntrySource.value === 'my-posts')
const communityReaderOwnerStatus = computed(() => {
  const post = selectedCommunityPost.value || {}
  if (post.reviewStatus === 'pending') return { key: 'pending', label: '待审核' }
  if (post.reviewStatus === 'rejected' || post.isPublished === false) return { key: 'archived', label: '已下架' }
  return { key: 'approved', label: '已通过' }
})
const filteredCircleExperiencePosts = computed(() => {
  const keyword = communityAppliedSearch.experience.trim().toLowerCase()
  const category = selectedExperienceCategory.value === '全部' ? '' : selectedExperienceCategory.value
  const sourcePosts = getCircleCommunityFeedPosts('experience', {
    featuredOnly: selectedCommunityPostSort.value === 'featured',
    sortBy: selectedCommunityPostSort.value,
    category,
    search: keyword
  })
  return sourcePosts.filter((item) => {
    // Also guard cached/legacy feed data on the client.  The API enforces the
    // same rule, while this keeps an old offline cache from impersonating an
    // authenticated predecessor after the policy is rolled out.
    if (
      !item.authorVerified
      || item.isPublished === false
      || item.reviewStatus !== 'approved'
      || !circleExperienceExamCodes.includes(String(item.examCode || '').trim())
    ) return false
    const matchesCategory = matchesExperienceFilter(item, selectedExperienceCategory.value)
    if (!matchesCategory || !keyword) return matchesCategory
    return [
      item.author,
      item.category,
      ...(item.experienceStages || []),
      item.title,
      item.summary,
      ...(item.commentPreviews || []).flatMap((comment) => [comment.author, comment.text]),
      ...(item.media || []).map((media) => `${media.title || ''} ${media.copy || ''}`)
    ]
      .join(' ')
      .toLowerCase()
      .includes(keyword)
  })
})
const activeCommunityPostSortOption = computed(() => (
  communityPostSortOptions.find((item) => item.value === selectedCommunityPostSort.value)
  || communityPostSortOptions[0]
))
const activeCommunityPostSortLabel = computed(() => activeCommunityPostSortOption.value.label)
const communityPostSortIndex = computed(() => Math.max(
  0,
  communityPostSortOptions.findIndex((item) => item.value === activeCommunityPostSortOption.value.value)
))
const mentorSortOptions = MENTOR_SORT_OPTIONS
const mentorExamTypeOptions = MENTOR_EXAM_TYPE_OPTIONS
const mentorAdmissionYearOptions = MENTOR_ADMISSION_YEAR_OPTIONS
const mentorPriceOptions = MENTOR_PRICE_OPTIONS
const mentorAvailabilityOptions = MENTOR_AVAILABILITY_OPTIONS
const activeMentorSortOption = computed(() => (
  mentorSortOptions.find((item) => item.value === selectedMentorSort.value) || mentorSortOptions[0]
))
const activeMentorSortLabel = computed(() => activeMentorSortOption.value.label)
const mentorSortIndex = computed(() => Math.max(
  0,
  mentorSortOptions.findIndex((item) => item.value === activeMentorSortOption.value.value)
))
const filteredMentors = computed(() => filterMentors({
  mentors: mentorProfiles.value,
  keyword: mentorSearchKeyword.value,
  filters: mentorFilters.value,
  sort: selectedMentorSort.value
}))
const mentorActiveFilterCount = computed(() => {
  const filters = mentorFilters.value
  return [
    filters.examType !== '不限' ? filters.examType : '',
    filters.admissionYear !== '不限' ? filters.admissionYear : '',
    filters.price !== '不限' ? filters.price : '',
    filters.availability !== '不限' ? filters.availability : ''
  ].filter(Boolean).length
})
const mentorFilteredResultCount = computed(() => filterMentors({
  mentors: mentorProfiles.value,
  keyword: mentorSearchKeyword.value,
  filters: mentorFilterDraft.value,
  sort: selectedMentorSort.value
}).length)
const activeCommunitySearchKeyword = computed({
  get: () => (
    selectedCircleCommunityTab.value === 'experience'
      ? experienceSearchKeyword.value
      : communitySearchKeyword.value
  ),
  set: (value) => {
    if (selectedCircleCommunityTab.value === 'experience') {
      experienceSearchKeyword.value = value
      return
    }
    communitySearchKeyword.value = value
  }
})
const activeCommunityCategories = computed(() => (
  selectedCircleCommunityTab.value === 'experience'
    ? circleExperienceCategories
    : circleCommunityCategories
))
const activeCommunityCategory = computed(() => (
  selectedCircleCommunityTab.value === 'experience'
    ? selectedExperienceCategory.value
    : selectedCommunityCategory.value
))
const filteredActiveCommunityPosts = computed(() => {
  const posts = selectedCircleCommunityTab.value === 'experience'
    ? filteredCircleExperiencePosts.value
    : filteredCircleCommunityPosts.value
  return sortCommunityPosts(posts, selectedCommunityPostSort.value)
})
const activeCommunityPageKey = computed(() => getCircleCommunityFeedPageKey(
  selectedCircleCommunityTab.value,
  {
    featuredOnly: selectedCommunityPostSort.value === 'featured',
    sortBy: selectedCommunityPostSort.value,
    category: activeCommunityCategory.value === '全部' ? '' : activeCommunityCategory.value,
    search: communityAppliedSearch[normalizeCircleCommunityPostType(selectedCircleCommunityTab.value)] || ''
  }
))
const activeCommunityHasMore = computed(() => communityFeedHasMore[activeCommunityPageKey.value] === true)
const activeCommunityLoading = computed(() => communityFeedLoadingState[activeCommunityPageKey.value] === true)
const activeCommunityLoadError = computed(() => String(communityFeedErrors[activeCommunityPageKey.value] || ''))
const mentorHasActiveSearch = computed(() => Boolean(
  mentorSearchKeyword.value.trim() || mentorActiveFilterCount.value
))
const mentorEntryLabel = computed(() => {
  if (mentorEntryStatus.value === 'verified') return '咨询主页'
  if (mentorEntryStatus.value === 'pending') return '审核中'
  return ''
})
const mentorEntryAriaLabel = computed(() => {
  if (mentorEntryStatus.value === 'verified') return '打开我的咨询主页'
  if (mentorEntryStatus.value === 'pending') return '查看认证审核状态'
  return '申请成为前辈'
})
const showCommunityPublishButton = computed(() => (
  activeTab.value === 'circle'
  && circleDetailVisible.value
  && circleDetailRouteMotion.value === 'idle'
  && selectedCircleSection.value === 'community'
  && Boolean(selectedCircleCommunityTab.value)
  && !selectedCommunityPost.value
  && !selectedCommunityCommentsPost.value
))
const circleTrendPeak = computed(() => Math.max(0, ...circlePracticeTrend.value.map((item) => item.count)))
const circleTrendPeakLabel = computed(() => (circleTrendLoaded.value ? circleTrendPeak.value : '—'))
const circleTrendScaleMax = computed(() => {
  const peak = circleTrendPeak.value
  if (peak <= 0) return 0
  if (peak < 10) return Math.max(2, peak)
  const step = peak < 100 ? 10 : 100
  return Math.ceil(peak / step) * step
})
const circleTrendAxis = computed(() => [circleTrendScaleMax.value, Math.round(circleTrendScaleMax.value / 2), 0])
const selectedCircleSectionLabel = computed(() =>
  circleSections.find((item) => item.key === selectedCircleSection.value)?.label || '研圈'
)
const circlePlannedSection = computed(() =>
  circleSections.find((item) => item.key === selectedCircleSection.value) || circleSections[0]
)
const fallbackSmartRecommendation = {
  subject: '逻辑推理',
  module: '判断',
  submodule: '判断关系',
  difficulty: '标准提升',
  questionCount: 10,
  basis: '当前正确率较低，优先巩固判断关系类题目'
}
const smartRecommendation = ref({ ...fallbackSmartRecommendation })
const subjectFallbackTargets = {
  中华文化: {
    subject: '中华文化',
    module: '中国文学常识',
    submodule: '文体流变',
    difficulty: '标准提升',
    questionCount: 10,
    basis: '优先巩固中华文化高频常识题。'
  },
  英语运用: {
    subject: '英语运用',
    module: '语言知识',
    submodule: '词汇',
    difficulty: '标准提升',
    questionCount: 10,
    basis: '优先巩固英语运用基础语言知识。'
  },
  逻辑推理: fallbackSmartRecommendation,
  数学基础: {
    subject: '数学基础',
    module: '一元函数微分学',
    submodule: '极限',
    difficulty: '标准提升',
    questionCount: 10,
    basis: '优先巩固数学基础题型。'
  }
}
const isAuthed = computed(() => authed.value)
const currentProfileEmail = computed(() => getPublicEmail(authUser.value) || '未绑定')
const currentProfilePhone = computed(() => maskProfilePhone(authUser.value?.phone) || '未绑定')
const profilePhoneCodeButtonText = computed(() => {
  if (profilePhoneSending.value) return '发送中...'
  if (profilePhoneCountdown.value > 0) return `${profilePhoneCountdown.value}s 后重发`
  return '发送验证码'
})
const subscriptionSheetDragStyle = computed(() => {
  if (!subscriptionSheetDragging.value || subscriptionSheetDragY.value <= 0) return {}
  return {
    transform: `translate3d(0, ${subscriptionSheetDragY.value}px, 0)`,
    transition: 'none'
  }
})
const subscriptionSheetMaskStyle = computed(() => {
  if (!subscriptionSheetDragging.value || subscriptionSheetDragY.value <= 0) return {}
  return {
    opacity: String(Math.max(0.18, 1 - subscriptionSheetDragY.value / 520))
  }
})
const profileUsesWechatBinding = computed(() => Boolean(authUser.value?.wechat_openid))
const avatarText = computed(() => (dashboard.value.userName || '游').slice(0, 1))
const avatarImageUrl = computed(() => {
  const avatar = authUser.value?.avatar_url || ''
  return isImageAvatar(avatar) ? avatar : ''
})
const profileAvatarText = computed(() => {
  if (!isAuthed.value) return '研'
  const avatar = authUser.value?.avatar_url || ''
  if (avatar && !isImageAvatar(avatar)) return avatar.slice(0, 2)
  return (getUserDisplayName(authUser.value, profile.value.userName || examCode.value || '游')).slice(0, 1)
})

function isImageAvatar(value) {
  const avatar = String(value || '')
  return avatar.startsWith('http://') || avatar.startsWith('https://') || avatar.startsWith('data:image')
}

const dashboard = computed(() => {
  const base = getHomeDashboard(examCode.value)
  if (!isAuthed.value) {
    return {
      ...base,
      userName: '游客',
      statusText: '登录后可直接刷真实题目并同步错题本',
      heroTitle: '登录后开启本周刷题统计',
      heroSubtitle: '当前可以先浏览界面与 mock 内容；登录后即可直接使用真实题库、提交答案和能力统计。'
    }
  }

  const weeklyAnswers = Number(learningSummary.value?.weekly_answers || 0)
  const totalAnswers = Number(learningSummary.value?.total_answers || 0)
  const accuracy = Number(learningSummary.value?.accuracy || 0)

  return {
    ...base,
    userName: getUserDisplayName(authUser.value, base.userName),
    statusText: '今日学习状态：已登录，可直连真实题库',
    heroTitle: `本周已刷真题：${weeklyAnswers} 道`,
    heroSubtitle: totalAnswers
      ? `累计已完成 ${totalAnswers} 道，当前总正确率 ${Math.round(accuracy)}%。继续刷题后，错题本和学习报告会自动同步。`
      : '你已经登录成功。本周刷题数暂为 0，完成第一轮练习后这里会自动更新真实数据。'
  }
})

const homeStats = computed(() => {
  if (!isAuthed.value) {
    return {
      weeklyAnswers: '0',
      accuracy: '--',
      accuracyOffset: 100,
      wrongCount: '--',
      totalAnswers: '0',
      correctAnswers: '0',
      studyStreak: '--'
    }
  }

  const weeklyAnswers = Number(learningSummary.value?.weekly_answers || 0)
  const totalAnswers = Number(learningSummary.value?.total_answers || 0)
  const correctAnswers = Number(learningSummary.value?.correct_answers || 0)
  const accuracy = Number(learningSummary.value?.accuracy || 0)
  const wrongCount = Number(learningSummary.value?.wrong_question_count || wrongItems.value.length || 0)
  const studyStreak = Number(learningSummary.value?.study_streak || 0)
  const accuracyValue = totalAnswers ? Math.min(100, Math.max(0, Math.round(accuracy))) : 0

  return {
    weeklyAnswers: String(weeklyAnswers),
    accuracy: totalAnswers ? `${accuracyValue}%` : '--',
    accuracyOffset: 100 - accuracyValue,
    wrongCount: String(wrongCount),
    totalAnswers: String(totalAnswers),
    correctAnswers: String(correctAnswers),
    studyStreak: `${studyStreak}天`
  }
})

// 进入“刷题”页时，圆环和右侧指标共用同一条动画时间线，目标值仍来自真实学习统计。
const practiceStatsAnimating = ref(false)
const practiceStatsAnimationPending = ref(false)
const animatedPracticeAccuracy = ref(0)
const animatedPracticeWeeklyAnswers = ref(0)
const animatedPracticeWrongCount = ref(0)
const PRACTICE_STATS_ANIMATION_DURATION = 900
let practiceStatsAnimationTimer = null
let practiceStatsAnimationToken = 0
let practiceStatsAnimationTarget = null

function parsePracticeStatsValue(value) {
  const normalized = String(value ?? '').replace(/[^\d.-]/g, '')
  if (!normalized) return null
  const parsed = Number(normalized)
  return Number.isFinite(parsed) ? Math.max(0, parsed) : null
}

const practiceStats = computed(() => {
  const base = homeStats.value
  const target = practiceStatsAnimationTarget
  const isAnimating = practiceStatsAnimating.value && target
  const baseAccuracy = parsePracticeStatsValue(base.accuracy)
  const accuracyProgress = isAnimating && target.accuracy !== null
    ? animatedPracticeAccuracy.value
    : baseAccuracy ?? 0
  const boundedAccuracyProgress = Math.min(100, Math.max(0, accuracyProgress))

  return {
    weeklyAnswers: isAnimating && target.weeklyAnswers !== null
      ? String(Math.round(animatedPracticeWeeklyAnswers.value))
      : base.weeklyAnswers,
    accuracy: isAnimating && target.accuracy !== null
      ? `${Math.round(boundedAccuracyProgress)}%`
      : base.accuracy,
    accuracyProgress: boundedAccuracyProgress,
    accuracyOffset: 100 - boundedAccuracyProgress,
    wrongCount: isAnimating && target.wrongCount !== null
      ? String(Math.round(animatedPracticeWrongCount.value))
      : base.wrongCount
  }
})

const dailyLeaderboardMyRankLabel = computed(() => {
  if (!isAuthed.value) return '登录后查看我的排名'
  if (dailyLeaderboardLoading.value && !dailyLeaderboardLoaded.value) return '正在同步我的排名'
  const item = dailyLeaderboardCurrentUser.value
  if (!item) return '我今天还未上榜'
  return `我的排名 ${item.rank} · ${formatDailyRankDuration(item.studySeconds)}`
})

function normalizeDailyLeaderboardItem(item = {}) {
  return {
    rank: Math.max(0, Number(item.rank || 0)),
    userId: String(item.user_id || item.userId || ''),
    nickname: String(item.nickname || '学习用户'),
    avatarUrl: String(item.avatar_url || item.avatarUrl || '').trim(),
    studySeconds: Math.max(0, Number(item.study_seconds ?? item.studySeconds ?? 0)),
    answerCount: Math.max(0, Number(item.answer_count ?? item.answerCount ?? 0)),
    isCurrentUser: item.is_current_user === true || item.isCurrentUser === true
  }
}

async function loadDailyLeaderboardPreview({ force = false } = {}) {
  if (!isAuthed.value) {
    dailyLeaderboardItems.value = []
    dailyLeaderboardCurrentUser.value = null
    dailyLeaderboardLoaded.value = false
    dailyLeaderboardError.value = ''
    return
  }
  if (dailyLeaderboardLoading.value) return
  if (!force && dailyLeaderboardLoaded.value && Date.now() - dailyLeaderboardUpdatedAt.value < 25000) return

  dailyLeaderboardLoading.value = true
  dailyLeaderboardError.value = ''
  try {
    const response = await fetchDailyStudyLeaderboard({ limit: 3, offset: 0 })
    dailyLeaderboardItems.value = Array.isArray(response?.items)
      ? response.items.map(normalizeDailyLeaderboardItem).filter((item) => item.userId)
      : []
    dailyLeaderboardCurrentUser.value = response?.current_user
      ? normalizeDailyLeaderboardItem(response.current_user)
      : null
    dailyLeaderboardLoaded.value = true
    dailyLeaderboardUpdatedAt.value = Date.now()
  } catch (error) {
    dailyLeaderboardError.value = getSafeError(error, '今日学习榜暂时不可用')
  } finally {
    dailyLeaderboardLoading.value = false
  }
}

function startDailyLeaderboardRefresh() {
  stopDailyLeaderboardRefresh()
  if (activeTab.value !== 'home' || !isAuthed.value) return
  dailyLeaderboardRefreshTimer = setInterval(() => {
    if (activeTab.value === 'home' && isAuthed.value) {
      void loadDailyLeaderboardPreview({ force: true })
    }
  }, DAILY_LEADERBOARD_REFRESH_INTERVAL)
}

function stopDailyLeaderboardRefresh() {
  if (!dailyLeaderboardRefreshTimer) return
  clearInterval(dailyLeaderboardRefreshTimer)
  dailyLeaderboardRefreshTimer = null
}

function handlePracticeOverviewChange(event) {
  const nextIndex = Number(event?.detail?.current)
  if (!Number.isInteger(nextIndex)) return
  practiceOverviewIndex.value = nextIndex
  if (nextIndex === 1) void loadDailyLeaderboardPreview()
}

function selectPracticeOverview(index) {
  if (index !== 0 && index !== 1) return
  practiceOverviewIndex.value = index
  if (index === 1) void loadDailyLeaderboardPreview()
}

function formatDailyRankDuration(value) {
  const seconds = Math.max(0, Math.floor(Number(value || 0)))
  if (seconds > 0 && seconds < 60) return '<1分钟'
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const remaining = minutes % 60
  if (hours && remaining) return `${hours}小时${remaining}分`
  if (hours) return `${hours}小时`
  return `${minutes}分钟`
}

function getDailyRankAvatarText(value) {
  return String(value || '学').trim().slice(0, 1) || '学'
}

function getDailyRankMedalIcon(rank) {
  const normalizedRank = Math.floor(Number(rank || 0))
  if (normalizedRank < 1 || normalizedRank > 3) return ''
  return `/static/ui-icons/png/original/rank-medal-${normalizedRank}.png`
}

function cancelPracticeStatsAnimation() {
  practiceStatsAnimationToken += 1
  if (practiceStatsAnimationTimer) {
    clearTimeout(practiceStatsAnimationTimer)
    practiceStatsAnimationTimer = null
  }
  practiceStatsAnimating.value = false
  practiceStatsAnimationPending.value = false
  practiceStatsAnimationTarget = null
}

function requestPracticeStatsAnimation() {
  cancelPracticeStatsAnimation()
  if (!isAuthed.value) return

  // onShow 会同时刷新学习统计；等真实响应落地后再开始，避免从临时 0 播放到真实值。
  if (!learningSummary.value) {
    practiceStatsAnimationPending.value = true
    return
  }

  const base = homeStats.value
  const target = {
    weeklyAnswers: parsePracticeStatsValue(base.weeklyAnswers),
    accuracy: parsePracticeStatsValue(base.accuracy),
    wrongCount: parsePracticeStatsValue(base.wrongCount)
  }
  if (![target.weeklyAnswers, target.accuracy, target.wrongCount].some((value) => value !== null)) return

  practiceStatsAnimationTarget = target
  animatedPracticeAccuracy.value = 0
  animatedPracticeWeeklyAnswers.value = 0
  animatedPracticeWrongCount.value = 0
  practiceStatsAnimationPending.value = false
  practiceStatsAnimating.value = true

  const token = ++practiceStatsAnimationToken
  const startedAt = Date.now()
  const tick = () => {
    if (token !== practiceStatsAnimationToken || !practiceStatsAnimating.value) return

    const elapsed = Date.now() - startedAt
    const linearProgress = Math.min(1, elapsed / PRACTICE_STATS_ANIMATION_DURATION)
    const easedProgress = 1 - Math.pow(1 - linearProgress, 3)
    if (target.accuracy !== null) animatedPracticeAccuracy.value = target.accuracy * easedProgress
    if (target.weeklyAnswers !== null) animatedPracticeWeeklyAnswers.value = target.weeklyAnswers * easedProgress
    if (target.wrongCount !== null) animatedPracticeWrongCount.value = target.wrongCount * easedProgress

    if (linearProgress >= 1) {
      if (target.accuracy !== null) animatedPracticeAccuracy.value = target.accuracy
      if (target.weeklyAnswers !== null) animatedPracticeWeeklyAnswers.value = target.weeklyAnswers
      if (target.wrongCount !== null) animatedPracticeWrongCount.value = target.wrongCount
      practiceStatsAnimating.value = false
      practiceStatsAnimationTimer = null
      return
    }

    practiceStatsAnimationTimer = setTimeout(tick, 16)
  }

  tick()
}

const moduleCards = computed(() => getHomeModules(examCode.value))
const trainingSubjectOptions = computed(() => {
  const option = EXAM_OPTIONS.find((item) => item.code === examCode.value) || EXAM_OPTIONS[0]
  return (option?.subjects || []).map((subject) => ({
    value: subject,
    label: getTrainingSubjectLabel(subject)
  }))
})
const trainingSubjectLabel = computed(() => getTrainingSubjectLabel(trainingSubject.value))
const smartRecommendationSubjectLabel = computed(() => getTrainingSubjectLabel(smartRecommendation.value.subject))
const generateProgressWidth = computed(() => {
  const total = Math.max(1, Number(generateEstimate.value || 1))
  const remaining = Math.max(0, Number(generateCountdown.value || 0))
  const progress = ((total - remaining) / total) * 100
  return `${Math.min(96, Math.max(8, progress))}%`
})
const realMistakes = computed(() => wrongItems.value.map(formatWrongQuestion))
const activeExamSubjects = computed(() => {
  const option = EXAM_OPTIONS.find((item) => item.code === examCode.value) || EXAM_OPTIONS[0]
  return option.subjects || []
})
const examMistakes = computed(() =>
  realMistakes.value.filter((item) => activeExamSubjects.value.includes(item.subject))
)
const wrongSummaryCount = computed(() => {
  if (!isAuthed.value) return '0'
  return String(examMistakes.value.length)
})
const reportStatus = computed(() => (isAuthed.value && abilityReport.value?.items?.length ? '已生成' : '未生成'))
const practiceTools = computed(() => {
  const proLocked = false
  const items = [
    { label: '收藏夹', desc: '查看我收藏的重点题目', icon: '', iconSrc: '/static/ui-icons/png/original/menu-favorite.png', tone: 'blue', action: 'favorites' },
    { label: '练习历史', desc: '回顾我的练习记录', icon: '', iconSrc: '/static/ui-icons/png/original/menu-history.png', tone: 'green', action: 'history' },
    {
      label: '错题本',
      desc: `查看与重刷 ${wrongSummaryCount.value} 道错题`,
      icon: '',
      iconSrc: '/static/ui-icons/png/original/menu-wrong-book.png',
      tone: proLocked ? 'locked' : 'blue',
      action: 'mistakes',
      locked: proLocked
    },
    {
      label: '院校专业收藏',
      desc: '查看收藏的院校与招生专业',
      icon: '',
      iconSrc: '/static/ui-icons/png/original/menu-major-favorite.png',
      tone: 'blue',
      action: 'major-favorites'
    },
  ]
  // #ifndef MP-WEIXIN
  items.push({
    label: '智能专项出题',
    desc: '按知识点生成专项练习',
    icon: '',
    iconSrc: '/static/ui-icons/png/original/question-admin.png',
    tone: proLocked ? 'locked' : 'green',
    action: 'ai-generator',
    locked: proLocked
  })
  // #endif
  items.push({
    label: '订阅',
    desc: '查看 PLUS 权益与套餐',
    icon: '',
    iconSrc: '/static/ui-icons/png/original/star.png',
    tone: 'dark',
    action: 'subscription',
    value: 'PLUS'
  })
  return items
})
const communityTools = computed(() => [
  {
    label: '我的咨询',
    desc: '找回咨询记录与聊天内容',
    icon: '',
    iconSrc: '/static/ui-icons/png/original/menu-consultation-outline.png',
    tone: 'blue',
    action: 'my-consultations',
    unread: consultationUnreadCount.value > 0
  },
  {
    label: '我的帖子',
    desc: '查看我在研圈发布的内容',
    icon: '',
    iconSrc: '/static/ui-icons/png/original/menu-my-posts.png',
    tone: 'blue',
    action: 'my-posts',
    unread: postInteractionUnreadCount.value > 0
  },
  {
    label: '我的收藏与点赞',
    desc: '查看点赞帖子与收藏前辈',
    icon: '',
    iconSrc: '/static/ui-icons/png/original/menu-favorite.png',
    tone: 'blue',
    action: 'liked-posts'
  }
])
const currentTheme = computed(() => getThemePreset(selectedThemeKey.value))
const isCircleGlassTheme = computed(() => currentTheme.value.circleGlass === true)
const themeInlineStyle = computed(() => buildThemeStyle(selectedThemeKey.value))
const mpLayoutStyle = ref('')
const pageInlineStyle = computed(() => [themeInlineStyle.value, mpLayoutStyle.value].filter(Boolean).join(';'))

const circleCommunityHeaderStyle = computed(() => {
  const progress = Math.min(1, Math.max(0, circleCommunityHeaderScrollTop.value / 220))

  return {
    '--circle-community-header-shadow-opacity': String(progress * 0.11)
  }
})

// #ifdef MP-WEIXIN
function syncMpSafeLayout() {
  mpLayoutStyle.value = buildMpPageSafeStyle()
}
// #endif

const isAdminUser = computed(() => {
  // #ifdef APP-PLUS
  return false
  // #endif
  const role = String(authUser.value?.role || '').toLowerCase()
  return role === 'admin'
})
const serviceTools = computed(() => {
  const items = [
    {
      label: '消息中心',
      desc: '处理进度、复核结果与平台公告',
      icon: '',
      iconSrc: '/static/ui-icons/png/original/notification-bell.png',
      tone: 'blue',
      action: 'messages',
      value: messageUnreadCount.value > 0 ? `${Math.min(messageUnreadCount.value, 99)} 条未读` : '',
      unread: messageUnreadCount.value > 0
    },
    {
      label: '绑定手机号码',
      desc: '绑定或更改手机号码',
      icon: '',
      iconSrc: '/static/ui-icons/png/original/menu-phone.png',
      tone: 'blue',
      action: 'bind-phone',
      value: currentProfilePhone.value
    },
    {
      label: '绑定邮箱',
      desc: '绑定或更改 QQ 邮箱',
      icon: '',
      iconSrc: '/static/ui-icons/png/original/email-login.png',
      tone: 'dark',
      action: 'bind-email',
      value: currentProfileEmail.value
    },
    {
      label: '我的钱包',
      desc: '余额、账单与咨询收入',
      icon: '',
      iconSrc: '/static/ui-icons/png/original/menu-wallet.png',
      tone: 'blue',
      action: 'wallet'
    },
    {
      label: '关于我们',
      desc: '帮助反馈、隐私政策与支持信息',
      icon: '',
      iconSrc: '/static/ui-icons/png/original/about.png',
      tone: 'blue',
      action: 'about'
    },
    {
      label: '我的举报',
      desc: '查看举报进度与处理结果',
      icon: '',
      iconSrc: '/static/ui-icons/png/original/menu-community-report.png',
      tone: 'orange',
      action: 'community-reports',
      unread: communityReportUnreadCount.value > 0
    }
  ]
  if (isAdminUser.value) {
    items.unshift(
      {
        label: '后台管理',
        desc: '管理用户、反馈和系统消息',
        icon: '',
        iconSrc: '/static/ui-icons/png/original/admin.png',
        tone: 'purple',
        action: 'admin'
      },
      {
        label: '题库管理',
        desc: '查看、筛选和上下架题目',
        icon: '',
        iconSrc: '/static/ui-icons/png/original/question-admin.png',
        tone: 'blue',
        action: 'question-admin'
      }
    )
  }
  return items
})
const filteredMistakes = computed(() =>
  examMistakes.value.filter((item) => {
    if (wrongFilters.value.subject && item.subject !== wrongFilters.value.subject) return false
    if (wrongFilters.value.module && item.module !== wrongFilters.value.module) return false
    if (wrongFilters.value.submodule && item.submodule !== wrongFilters.value.submodule) return false
    return true
  })
)
const fullMistakes = computed(() => (isAuthed.value ? filteredMistakes.value : getFullMistakes()))
const visibleMistakes = computed(() => fullMistakes.value.slice(0, visibleMistakeCount.value))
const hasMoreMistakes = computed(() => (
  visibleMistakeCount.value < fullMistakes.value.length || wrongHasMore.value
))
const retestCandidateMistakes = computed(() => (isAuthed.value ? filteredMistakes.value : []))
const retestTotal = computed(() => retestItems.value.length)
const retestCorrectCount = computed(() => retestResults.value.filter((item) => item.is_correct).length)
const retestProgressLabel = computed(() => {
  if (!retestTotal.value) return '0 / 0'
  return `${Math.min(retestIndex.value + 1, retestTotal.value)} / ${retestTotal.value}`
})
const retestOptions = computed(() => buildQuestionOptions(retestDetail.value?.question))
const subjectFilters = computed(() => [
  '',
  ...activeExamSubjects.value.filter((subject) => examMistakes.value.some((item) => item.subject === subject))
])
const moduleFilters = computed(() => buildFilterOptions(examMistakes.value, 'module', { subject: wrongFilters.value.subject }))
const submoduleFilters = computed(() =>
  buildFilterOptions(examMistakes.value, 'submodule', {
    subject: wrongFilters.value.subject,
    module: wrongFilters.value.module
  })
)
const wrongSubjectPickerOptions = computed(() => toWrongFilterPickerOptions(subjectFilters.value, '全部科目'))
const wrongModulePickerOptions = computed(() => (
  wrongFilters.value.subject
    ? toWrongFilterPickerOptions(moduleFilters.value, '全部模块')
    : [{ value: '', label: '请先选科目' }]
))
const wrongSubmodulePickerOptions = computed(() => (
  wrongFilters.value.module
    ? toWrongFilterPickerOptions(submoduleFilters.value, '全部子模块')
    : [{ value: '', label: '请先选模块' }]
))
const wrongSubjectPickerIndex = computed(() => getWrongFilterPickerIndex(
  wrongSubjectPickerOptions.value,
  wrongFilters.value.subject
))
const wrongModulePickerIndex = computed(() => getWrongFilterPickerIndex(
  wrongModulePickerOptions.value,
  wrongFilters.value.module
))
const wrongSubmodulePickerIndex = computed(() => getWrongFilterPickerIndex(
  wrongSubmodulePickerOptions.value,
  wrongFilters.value.submodule
))
const selectedWrongSubjectLabel = computed(() => wrongSubjectPickerOptions.value[wrongSubjectPickerIndex.value]?.label || '全部科目')
const selectedWrongModuleLabel = computed(() => wrongModulePickerOptions.value[wrongModulePickerIndex.value]?.label || '请先选科目')
const selectedWrongSubmoduleLabel = computed(() => wrongSubmodulePickerOptions.value[wrongSubmodulePickerIndex.value]?.label || '请先选模块')
const wrongFilterScopeParts = computed(() =>
  [wrongFilters.value.subject, wrongFilters.value.module, wrongFilters.value.submodule].filter(Boolean)
)
const retestScopeText = computed(() => {
  const scope = wrongFilterScopeParts.value.length ? wrongFilterScopeParts.value.join(' / ') : '全部错题'
  return `正在重测：${scope}，可随时退出。`
})
const retestButtonText = computed(() => {
  if (!isAuthed.value || !wrongFilterScopeParts.value.length) return '重测错题'
  return `重测${wrongFilters.value.subject ? '本科目' : '当前范围'}`
})
const report = computed(() => buildReportView())
const subjectReportCards = computed(() => {
  const groups = new Map()
  report.value.items.forEach((item) => {
    const subject = item.subject || '其他科目'
    const total = Number(item.total_count || 0)
    const accuracy = Number(item.accuracy || 0)
    const correct = Number(item.correct_count || Math.round((total * accuracy) / 100))
    const current = groups.get(subject) || {
      subject,
      total: 0,
      correct: 0,
      lowestAccuracy: 100,
      weakestModule: '',
      module: item.module || '',
      submodule: item.submodule || ''
    }
    current.total += total
    current.correct += correct
    if (accuracy < current.lowestAccuracy) {
      current.lowestAccuracy = accuracy
      current.weakestModule = item.submodule || item.module || ''
      current.module = item.module || ''
      current.submodule = item.submodule || ''
    }
    groups.set(subject, current)
  })

  const subjectOrder = ['中华文化', '英语运用', '逻辑推理', '数学基础']
  return Array.from(groups.values())
    .map((item) => {
      const accuracy = item.total ? Math.round((item.correct / item.total) * 100) : 0
      const mastery = getMasteryLevel(accuracy)
      return {
        ...item,
        accuracy,
        iconSrc: getSubjectIconSrc(item.subject, selectedThemeKey.value),
        status: mastery.label,
        tone: mastery.tone,
        weeklyChange: getSubjectWeeklyChange(item.subject),
        suggestion: getSubjectSuggestion(item.subject, item.weakestModule, accuracy),
        action: accuracy < 80 ? '去补强' : '开始训练',
        questionCount: 10
      }
    })
    .sort((a, b) => {
      const aIndex = subjectOrder.indexOf(a.subject)
      const bIndex = subjectOrder.indexOf(b.subject)
      return (aIndex === -1 ? 99 : aIndex) - (bIndex === -1 ? 99 : bIndex)
    })
})
const reportOverview = computed(() => {
  const total = subjectReportCards.value.reduce((sum, item) => sum + Number(item.total || 0), 0)
  const correct = subjectReportCards.value.reduce((sum, item) => sum + Number(item.correct || 0), 0)
  const accuracy = total ? Math.round((correct / total) * 100) : 0
  const weeklyAnswers = Number(learningSummary.value?.weekly_answers || 0)
  const weeklyChange = learningSummary.value?.weekly_accuracy_change
  const hasWeeklyChange = weeklyChange !== null && weeklyChange !== undefined
  const streak = Number(learningSummary.value?.study_streak || 0)
  const countLabel = weeklyAnswers ? '本周做题' : '累计做题'
  const changeValue = hasWeeklyChange
    ? formatAccuracyChange(weeklyChange)
    : '—'

  return {
    metrics: [
      { label: countLabel, value: `${weeklyAnswers || total}题`, tone: 'blue' },
      { label: '整体正确率', value: `${accuracy}%`, tone: getMasteryLevel(accuracy).tone },
      { label: hasWeeklyChange ? '较上周' : '对比积累中', value: changeValue, tone: getChangeTone(weeklyChange) },
      { label: '连续学习', value: streak ? `${streak}天` : '—', tone: streak ? 'green' : 'muted' }
    ],
    note: weeklyAnswers
      ? `本周完成 ${weeklyAnswers} 题；下方科目卡展示累计作答统计。`
      : '当前未取得本周答题记录，本页诊断与科目卡均按累计作答统计。'
  }
})
const reportTrend = computed(() => {
  const trend = learningSummary.value?.trend
  if (!Array.isArray(trend)) return []
  return trend.map((item, index) => ({
    date: item?.date || String(index),
    label: item?.label || `第${index + 1}天`,
    accuracy: Number.isFinite(Number(item?.accuracy)) ? Number(item.accuracy) : null,
    total: Number(item?.total_answers || 0)
  }))
})
const trendAnsweredCount = computed(() => reportTrend.value.reduce((sum, item) => sum + item.total, 0))
const trendUnlocked = computed(() => (
  trendAnsweredCount.value >= 20 && reportTrend.value.filter((item) => item.accuracy !== null).length >= 2
))
const trendUnlockRemaining = computed(() => Math.max(0, 20 - trendAnsweredCount.value))
const trendUnlockProgress = computed(() => Math.min(100, Math.round((trendAnsweredCount.value / 20) * 100)))
const trendCanvasGridY = [24, 66, 108]
const trendChartPoints = computed(() => {
  const points = reportTrend.value
    .map((item, index) => ({ ...item, index }))
    .filter((item) => item.accuracy !== null)
  if (!points.length) return []

  const values = points.map((item) => item.accuracy)
  const lower = Math.max(0, Math.min(...values) - 8)
  const upper = Math.min(100, Math.max(...values) + 8)
  const range = Math.max(12, upper - lower)
  return points.map((item) => ({
    ...item,
    x: 16 + (item.index / Math.max(1, reportTrend.value.length - 1)) * 288,
    y: 108 - ((item.accuracy - lower) / range) * 84
  }))
})
const trendPath = computed(() => trendChartPoints.value
  .map((item, index) => `${index ? 'L' : 'M'} ${item.x.toFixed(2)} ${item.y.toFixed(2)}`)
  .join(' '))
const trendAreaPath = computed(() => {
  const points = trendChartPoints.value
  if (!points.length) return ''
  const first = points[0]
  const last = points[points.length - 1]
  return `${trendPath.value} L ${last.x.toFixed(2)} 112 L ${first.x.toFixed(2)} 112 Z`
})
const trendSummaryTone = computed(() => getChangeTone(learningSummary.value?.weekly_accuracy_change))
const trendBadgeText = computed(() => {
  const change = learningSummary.value?.weekly_accuracy_change
  return change === null || change === undefined ? '趋势积累中' : formatAccuracyChange(change)
})
const trendSummary = computed(() => {
  const change = learningSummary.value?.weekly_accuracy_change
  if (change === null || change === undefined) {
    return '已形成近 7 天趋势，继续完成本周练习即可解锁周度对比。'
  }
  if (change > 0) return `本周正确率较上周提升 ${Math.abs(Math.round(change))}%`
  if (change < 0) return `本周正确率较上周下降 ${Math.abs(Math.round(change))}%，建议优先复盘近期错题。`
  return '本周正确率与上周持平，建议保持练习节奏。'
})
const weeklyBreakthroughs = computed(() => report.value.items
  .filter((item) => Number(item.total_count || 0) > 0 && (item.submodule || item.module))
  .slice()
  .sort((a, b) => Number(a.accuracy || 0) - Number(b.accuracy || 0))
  .slice(0, 3)
  .map((item) => {
    const accuracy = Math.round(Number(item.accuracy || 0))
    return {
      subject: item.subject,
      topic: item.submodule || item.module,
      accuracy,
      tone: getMasteryLevel(accuracy).tone,
      module: item.module,
      submodule: item.submodule
    }
  }))
const reportActionTasks = computed(() => {
  const ranked = subjectReportCards.value.slice().sort((a, b) => a.accuracy - b.accuracy)
  const first = ranked[0]
  const second = ranked[1]
  if (!first) return []

  const tasks = [
    {
      id: `train-${first.subject}`,
      title: `${first.subject} · ${first.weakestModule || '基础专项'}训练`,
      meta: '10题 · 约8分钟',
      desc: first.suggestion,
      actionLabel: '开始训练',
      type: 'practice',
      subject: first.subject,
      module: first.module,
      submodule: first.submodule,
      questionCount: 10
    },
    {
      id: `review-${first.subject}`,
      title: `复盘${first.subject}错题`,
      meta: `${examMistakes.value.filter((item) => item.subject === first.subject).length}题待复盘`,
      desc: `先查看 ${first.weakestModule || first.subject} 的错题解析，再完成同类练习。`,
      actionLabel: '查看错题',
      type: 'mistakes',
      subject: first.subject,
      module: first.module,
      submodule: first.submodule
    }
  ]
  if (second) {
    tasks.push({
      id: `train-${second.subject}`,
      title: `${second.subject} · ${second.weakestModule || '专项'}巩固`,
      meta: '10题 · 约8分钟',
      desc: second.suggestion,
      actionLabel: '开始训练',
      type: 'practice',
      subject: second.subject,
      module: second.module,
      submodule: second.submodule,
      questionCount: 10
    })
  }
  return tasks
})
const todayTraining = computed(() => {
  const trainingTasks = reportActionTasks.value.filter((item) => item.type === 'practice').slice(0, 2)
  const total = trainingTasks.reduce((sum, item) => sum + Number(item.questionCount || 10), 0)
  return {
    items: trainingTasks.map((item) => ({
      ...item,
      label: `${item.subject}${item.submodule ? ` · ${item.submodule}` : ''} ${item.questionCount || 10}题`
    })),
    primary: trainingTasks[0] || null,
    meta: `共${total}题 · 预计${Math.max(8, Math.round(total * 0.8))}分钟`
  }
})
const fallbackReportAdvice = computed(() => buildFallbackReportAdvice())
const reportAdvice = computed(() => {
  if (studyAdvice.value?.summary_items?.length) {
    return studyAdvice.value.summary_items.slice(0, 4)
  }
  return fallbackReportAdvice.value
})
const studyAdviceSubtitle = computed(() => {
  if (!isAuthed.value) return '登录后会根据真实作答记录生成建议。'
  if (studyAdviceLoading.value) return '正在结合正确率、错题和薄弱模块分析。'
  if (studyAdvice.value?.source === 'deepseek') return '已结合真实记录生成个性化提分建议。'
  return '已根据真实做题记录生成当前阶段建议。'
})
const studyAdviceSummary = computed(() => studyAdvice.value?.summary || fallbackReportAdvice.value[0] || '先完成一组练习，系统会继续更新建议。')
const studyAdviceDetails = computed(() => {
  const items = studyAdvice.value?.subject_advices || []
  if (!items.length) {
    return buildFallbackSubjectAdvice()
  }
  return items.map((item) => ({
    ...item,
    accuracyText: item.accuracy === null || item.accuracy === undefined ? '暂无正确率' : `正确率 ${Math.round(Number(item.accuracy || 0))}%`,
    weak_points: safeAdviceList(item.weak_points, ['先完成一组基础练习建立样本']),
    fear_points: safeAdviceList(item.fear_points, ['题干变长时容易紧张，先把关键词圈出来再判断。']),
    score_tips: safeAdviceList(item.score_tips, ['我建议先用 10 题小组练习，错题当天复盘。']),
    next_actions: safeAdviceList(item.next_actions, ['完成一组 10 题专项训练。'])
  }))
})

function buildFallbackReportAdvice() {
  if (!isAuthed.value) {
    return ['登录后会基于真实作答记录生成学习报告。', '完成一组专项或综合刷题后，可查看科目正确率和薄弱项。']
  }
  if (report.value.items.length === 0) {
    return ['当前还没有足够的作答数据，建议先完成 10 道专项练习。', '系统会在提交答案后自动更新正确率、错题和能力统计。']
  }

  const weakestSubjects = subjectReportCards.value.slice().sort((a, b) => a.accuracy - b.accuracy)
  const weakestStats = report.value.items.slice().sort((a, b) => Number(a.accuracy || 0) - Number(b.accuracy || 0)).slice(0, 2)
  const advice = []
  if (weakestSubjects[0]) {
    advice.push(`${weakestSubjects[0].subject} 当前正确率 ${weakestSubjects[0].accuracy}%，建议优先完成一组 10 题专项训练。`)
  }
  weakestStats.forEach((item) => {
    advice.push(`重点复盘 ${item.module}${item.submodule ? ` - ${item.submodule}` : ''}，先看错题解析，再做同类题。`)
  })
  return advice.slice(0, 4)
}

function buildFallbackSubjectAdvice() {
  return subjectReportCards.value.map((item) => ({
    subject: item.subject,
    status: item.status,
    accuracy: item.accuracy,
    accuracyText: `正确率 ${item.accuracy}%`,
    weak_points: [item.weakestModule || '当前薄弱点还在积累中'],
    fear_points: ['遇到不熟悉题型时容易急着选答案，建议先回到题干条件。'],
    score_tips: [`我建议先围绕 ${item.weakestModule || item.subject} 做一组 10 题短练。`],
    next_actions: ['先看错题解析，再做同类题确认是否掌握。']
  }))
}

function safeAdviceList(value, fallback) {
  return Array.isArray(value) && value.length ? value : fallback
}
const reportSubtitle = computed(() => {
  if (!isAuthed.value) {
    return '登录后会基于真实作答统计生成学习报告；当前展示示例诊断。'
  }
  if (abilityReport.value?.items?.length) {
    return '已根据真实作答记录生成学习报告。'
  }
  return '已连接真实能力统计接口，完成几道题后这里会出现你的准确率与薄弱项。'
})
const profile = computed(() => {
  const base = getProfileMock()
  if (!isAuthed.value) {
    return {
      ...base,
      userName: '欢迎来到港研通',
      subtitle: '登录后同步学习进度与数据',
      badge: '游客',
      stats: [
        { label: '目标版本', value: examCode.value },
        { label: '累计刷题', value: '0 题' },
        { label: '总正确率', value: '--' },
        { label: '错题数', value: '0 题' }
      ]
    }
  }

  const totalAnswers = Number(learningSummary.value?.total_answers || 0)
  const accuracy = Number(learningSummary.value?.accuracy || 0)
  const wrongCount = Number(learningSummary.value?.wrong_question_count || wrongItems.value.length || 0)

  return {
    ...base,
    userName: getUserDisplayName(authUser.value, base.userName),
    subtitle: getUserContactLabel(authUser.value, base.subtitle),
    badge: '已登录',
    stats: [
      { label: '目标版本', value: examCode.value },
      { label: '累计刷题', value: `${totalAnswers} 题` },
      { label: '总正确率', value: totalAnswers ? `${Math.round(accuracy)}%` : '暂无数据' },
      { label: '错题数', value: `${wrongCount} 题` }
    ]
  }
})

watch(examCode, (value) => {
  uni.setStorageSync('examCode', value)
  wrongFilters.value = {
    subject: '',
    module: '',
    submodule: ''
  }
  syncTrainingSubject()
  studyAdvice.value = null
  studyAdviceExamCode.value = ''
  if (isAuthed.value) {
    loadAbilityReport()
    loadLearningSummary()
  }
})

watch(activeTab, (value) => {
  resetCircleTabbar()
  if (value === 'home') {
    requestPracticeStatsAnimation()
    void loadDailyLeaderboardPreview({ force: true })
    startDailyLeaderboardRefresh()
  } else {
    cancelPracticeStatsAnimation()
    stopDailyLeaderboardRefresh()
  }
  if (value === 'landing') {
    resetLandingPageScroll()
  }
  if (value !== 'profile') {
    showExamSwitchModal.value = false
    showProfileEditModal.value = false
    showEmailBindingModal.value = false
    closePhoneBindingModal(true)
  }
  if (value === 'circle' && !ENABLE_CIRCLE) {
    activeTab.value = 'landing'
    return
  }
  if (value === 'circle') {
    clearCircleOverviewRestoreTimer()
    resetCircleDetailRouteState()
    selectedCircleSection.value = 'overview'
    circleDetailScrollTop.value = 0
    circleOverviewScrollTop.value = 0
    circleCommunityHeaderScrollTop.value = 0
    selectedCirclePost.value = null
    closeCommunityPost()
    // 在进入研圈时预取，用户切到“前辈咨询”时大多已准备就绪。
    void loadMentorProfiles()
    void loadMentorEntryStatus()
  }
  if (value !== 'mistakes') {
    selectedWrongDetail.value = null
    if (retestMode.value) {
      exitWrongRetest()
    }
  } else {
    resetMistakeVisibleCount()
  }
  if (value !== 'circle') {
    clearCircleOverviewRestoreTimer()
    resetCircleDetailRouteState()
    selectedCirclePost.value = null
    closeCommunityPost()
  }
})

watch([learningSummary, authed], () => {
  if (activeTab.value !== 'home' || !practiceStatsAnimationPending.value) return
  if (isAuthed.value && !learningSummary.value) return
  requestPracticeStatsAnimation()
})

watch(wrongFilters, () => {
  resetMistakeVisibleCount()
  if (isAuthed.value && activeTab.value === 'mistakes') void loadWrongQuestions({ reset: true })
}, { deep: true })

watch(wrongItems, () => {
  resetMistakeVisibleCount()
})

onLoad((options) => {
  const launchOptions = resolveHomeLaunchOptions(options)
  communityReaderEntrySource.value = String(launchOptions?.entry || '') === 'my-posts' ? 'my-posts' : ''
  // #ifdef MP-WEIXIN
  syncMpSafeLayout()
  // #endif
  if (launchOptions?.tab === 'circle' && ENABLE_CIRCLE) {
    activeTab.value = 'circle'
    if (launchOptions?.section === 'community') {
      const requestedCommunityTab = String(launchOptions?.communityTab || '')
      const requestedCommunityPostId = String(launchOptions?.postId || '').trim()
      const requestedOwnerPreview = communityReaderEntrySource.value === 'my-posts'
        && String(launchOptions?.ownerPreview || '') === '1'
      const restoreCommunityDeepLink = () => {
        selectedCircleSection.value = 'community'
        showCircleDetailImmediately()
        circleDetailScrollTop.value = 0
        if (circleCommunityTabs.some((item) => item.key === requestedCommunityTab)) {
          selectedCircleCommunityTab.value = requestedCommunityTab
        }
        if (requestedCommunityTab === 'mentor') {
          void loadMentorEntryStatus()
          void loadMentorProfiles()
        }
        resetCircleTabbar()
      }
      const openRequestedCommunityPost = () => {
        if (!requestedCommunityPostId || selectedCommunityPost.value?.id === requestedCommunityPostId) return
        if (requestedOwnerPreview) {
          void openOwnedCommunityPostFromRoute(requestedCommunityPostId, requestedCommunityTab)
          return
        }
        void openCommunityPost({
          id: requestedCommunityPostId,
          post_type: requestedCommunityTab === 'experience' ? 'experience' : 'chat',
          title: '正在整理帖子...'
        })
      }
      nextTick(() => {
        // activeTab 的既有监听会先复位到研圈首页；冷启动 H5 时该监听可能在挂载后补跑一次。
        restoreCommunityDeepLink()
        setTimeout(() => {
          restoreCommunityDeepLink()
          openRequestedCommunityPost()
        }, 0)
      })
    }
  } else if (launchOptions?.tab === 'landing') {
    activeTab.value = 'landing'
  } else if (launchOptions?.tab === 'home') {
    activeTab.value = 'home'
  } else if (launchOptions?.tab === 'profile') {
    activeTab.value = 'profile'
  }

  warmCircleCommunityFeeds()
  void loadCirclePracticeTrend()
  void loadSubscriptionPageConfig()
})

const HOME_CONTENT_SLOT_LIMITS = Object.freeze({ focus: 3, news: 3 })

async function loadPublishedOperationContent() {
  const [homeContentResult, scorelineResult] = await Promise.allSettled([
    fetchHomeContent(),
    fetchPublishedScorelines()
  ])

  if (homeContentResult.status === 'fulfilled') {
    const payload = homeContentResult.value || {}
    const focus = (payload.focus || []).filter((item) => item?.title).slice(0, HOME_CONTENT_SLOT_LIMITS.focus)
    const news = (payload.news || []).filter((item) => item?.title).slice(0, HOME_CONTENT_SLOT_LIMITS.news)
    const managedSlots = payload.managedSlots || {}
    if (managedSlots.focus === true || focus.length) {
      homeFocusItems.splice(0, homeFocusItems.length, ...focus.map((item) => ({
        badge: item.badge || '官方资讯',
        title: item.title,
        subtitle: item.subtitle || '',
        artLabel: item.artLabel || '资讯',
        url: item.url || '',
        routeKey: item.routeKey || ''
      })))
      homeFocusIndex.value = Math.min(homeFocusIndex.value, Math.max(0, homeFocusItems.length - 1))
    }
    if (managedSlots.news === true || news.length) {
      homeNewsItems.splice(0, homeNewsItems.length, ...news.map((item) => ({
        source: item.source || '港研通',
        title: item.title,
        date: item.date || '',
        coverLabel: item.coverLabel || '资讯',
        coverTone: item.coverTone || 'is-blue',
        url: item.url || '',
        routeKey: item.routeKey || ''
      })))
    }
  }

  if (scorelineResult.status === 'fulfilled') {
    const payload = scorelineResult.value || {}
    const records = Array.isArray(payload.records) ? payload.records : []
    const years = Array.isArray(payload.years) ? payload.years.filter((year) => /^20\d{2}$/.test(String(year))) : []
    if (payload.managed === true || (records.length && years.length)) {
      const orderedYears = [...years].sort()
      historicalScoreLineYears.splice(0, historicalScoreLineYears.length, ...orderedYears)
      historicalScoreLineRecords.splice(0, historicalScoreLineRecords.length, ...records.map((record) => ({
        ...record,
        scores: { ...(record.scores || {}) }
      })))
      historicalScoreLineRegions.splice(0, historicalScoreLineRegions.length, ...(payload.regions || []).map((region) => ({ ...region })))
      const yearAvailability = orderedYears.reduce((result, year) => {
        result[year] = records.filter((record) => Boolean(record?.scores?.[year]?.raw)).length
        return result
      }, {})
      Object.keys(historicalScoreLineStats).forEach((key) => {
        delete historicalScoreLineStats[key]
      })
      Object.assign(historicalScoreLineStats, {
        ...(payload.statistics || {}),
        recordCount: records.length,
        regionCount: historicalScoreLineRegions.length,
        yearAvailability,
        threeYearTrendCount: historicalScoreLineTrendRecords.value.length
      })
      if (selectedScoreLineYear.value !== '全部' && !orderedYears.includes(selectedScoreLineYear.value)) {
        selectedScoreLineYear.value = '全部'
      }
      if (selectedScoreLineRegion.value !== '全部' && !historicalScoreLineRegions.some((item) => item.name === selectedScoreLineRegion.value)) {
        selectedScoreLineRegion.value = '全部'
      }
      if (selectedScoreLineRecord.value && !historicalScoreLineRecords.some((item) => item.id === selectedScoreLineRecord.value.id)) {
        selectedScoreLineRecord.value = null
        selectedScoreLineRecordEntry.value = 'list'
      }
      circleScoreSchoolIndex.value = 0
    }
  }
}

function resolveHomeLaunchOptions(options = {}) {
  const resolved = { ...(options || {}) }
  if (typeof window === 'undefined') return resolved

  const hash = String(window.location?.hash || '')
  const query = hash.includes('?') ? hash.slice(hash.indexOf('?') + 1) : ''
  if (!query) return resolved

  query.split('&').forEach((pair) => {
    const separator = pair.indexOf('=')
    const rawKey = separator >= 0 ? pair.slice(0, separator) : pair
    const rawValue = separator >= 0 ? pair.slice(separator + 1) : ''
    if (!rawKey) return
    try {
      const key = decodeURIComponent(rawKey)
      if (resolved[key] !== undefined && resolved[key] !== '') return
      resolved[key] = decodeURIComponent(rawValue.replace(/\+/g, ' '))
    } catch (error) {
      // 路由参数异常时保留 uni-app 已提供的参数，不影响主页正常打开。
    }
  })

  return resolved
}

function createCirclePracticeTrend(now = new Date()) {
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  const lastIndex = CIRCLE_PRACTICE_TREND_DAYS - 1

  return Array.from({ length: CIRCLE_PRACTICE_TREND_DAYS }, (_, index) => {
    const date = new Date(today)
    date.setDate(today.getDate() - (lastIndex - index))
    return {
      date: `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`,
      day: `${date.getMonth() + 1}/${date.getDate()}`,
      count: 0,
      latest: index === lastIndex
    }
  })
}

function getCircleTrendDateText(value) {
  const matched = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})/)
  return matched ? matched[0] : ''
}

function getCircleTrendDayLabel(dateText) {
  const matched = String(dateText || '').match(/^\d{4}-(\d{2})-(\d{2})$/)
  if (!matched) return ''
  return `${Number(matched[1])}/${Number(matched[2])}`
}

function normalizeCirclePracticeTrend(payload = {}) {
  const rows = Array.isArray(payload?.items) ? payload.items : []
  const normalized = rows
    .map((row) => {
      const date = getCircleTrendDateText(row?.date)
      return {
        date,
        day: getCircleTrendDayLabel(date),
        count: Math.max(0, Math.round(Number(row?.practice_users ?? row?.user_count ?? 0) || 0))
      }
    })
    .filter((row) => row.date && row.day)
    .sort((left, right) => left.date.localeCompare(right.date))
    .slice(-CIRCLE_PRACTICE_TREND_DAYS)

  if (normalized.length !== CIRCLE_PRACTICE_TREND_DAYS) {
    throw new Error('近七天刷题人数数据不完整')
  }

  return normalized.map((row, index) => ({
    ...row,
    latest: index === normalized.length - 1
  }))
}

async function loadCirclePracticeTrend({ force = false } = {}) {
  const cacheIsFresh = circleTrendLoaded.value
    && Date.now() - circleTrendLastLoadedAt.value < CIRCLE_PRACTICE_TREND_REFRESH_MS
  if (circleTrendLoading.value || (!force && cacheIsFresh)) return

  circleTrendLoading.value = true
  circleTrendError.value = ''
  try {
    const response = await fetchPlatformPracticeTrend()
    circlePracticeTrend.value = normalizeCirclePracticeTrend(response)
    circleTrendLoaded.value = true
    circleTrendLastLoadedAt.value = Date.now()
  } catch (error) {
    circleTrendError.value = getSafeError(error, '刷题人数统计暂时不可用')
  } finally {
    circleTrendLoading.value = false
  }
}

onShow(() => {
  // #ifdef MP-WEIXIN
  syncMpSafeLayout()
  // #endif
  authUser.value = getAuthUser()
  authed.value = isLoggedIn()
  consumeCommunityPostEditResult()
  mentorFavoriteIds.value = getMentorFavoriteIds()
  if (authed.value) void loadMentorFavoriteIds({ silent: true })
  refreshLearningData()
  void refreshMessageUnreadCounts()
  void loadSubscriptionPageConfig()
  void loadSubscriptionMembershipStatus()
  loadPublishedOperationContent()
  void loadCirclePracticeTrend()
  if (activeTab.value === 'home') {
    void loadDailyLeaderboardPreview({ force: true })
    startDailyLeaderboardRefresh()
  }
  if (activeTab.value === 'landing') {
    resetLandingPageScroll()
  }
  if (activeTab.value === 'circle' && selectedCircleSection.value === 'community') {
    const postType = selectedCircleCommunityTab.value
    if (postType === 'mentor') {
      void loadMentorEntryStatus({ force: true })
      void loadMentorProfiles({ force: mentorProfilesLoaded.value })
    } else {
      if (postType === 'experience') {
        mentorEntryStatus.value = getMentorVerificationStatus()
        void loadMentorEntryStatus({ force: !isMentorEntryStatusFresh() })
      }
      const sortBy = selectedCommunityPostSort.value
      const featuredOnly = sortBy === 'featured'
      loadCircleCommunityPosts(postType, {
        force: consumeCircleCommunityFeedRefresh(postType),
        featuredOnly,
        sortBy,
        search: communityAppliedSearch[normalizeCircleCommunityPostType(postType)]
      })
    }
  }
})

onHide(() => {
  interruptCircleEdgeSwipe()
  cancelPracticeStatsAnimation()
  stopDailyLeaderboardRefresh()
  clearCommunityViewTimer()
  clearCommunityLikeBurst()
  clearCircleScoreTooltip()
  showExamSwitchModal.value = false
  showProfileEditModal.value = false
  showEmailBindingModal.value = false
  closePhoneBindingModal(true)
})

onBackPress(() => {
  if (activeTab.value !== 'circle') return false
  if (selectedCommunityPost.value) {
    if (communityReaderReturnsToMyPosts.value) return false
    closeCommunityPostWithTapGuard()
    return true
  }
  if (selectedCommunityCommentsPost.value) {
    closeCommunityComments()
    return true
  }
  if (selectedCirclePost.value) {
    closeCirclePost()
    return true
  }
  if (circleDetailVisible.value) {
    handleCircleDetailBack()
    return true
  }
  return false
})

onBeforeUnmount(() => {
  cancelPracticeStatsAnimation()
  stopDailyLeaderboardRefresh()
  clearCommunityLikeBurst()
  clearCircleScoreTooltip()
  clearCircleOverviewRestoreTimer()
  clearCircleDetailRouteTimers()
  resetCircleEdgeSwipeState()
  clearCommunityReaderRouteTimers()
  clearCommunityCommentVisibilityTimer()
  clearCommunityCommentKeyboardSyncTimer()
  clearCommunityCommentKeyboardResetTimer()
  unbindCommunityCommentVisualViewport()
  if (communitySearchDebounceTimer !== null) {
    clearTimeout(communitySearchDebounceTimer)
    communitySearchDebounceTimer = null
  }
  clearMentorFilterMotionTimers()
  flushScheduledCircleCommunityFeedPersist()
  if (subscriptionSheetOpenTimer) clearTimeout(subscriptionSheetOpenTimer)
  if (subscriptionSheetCloseTimer) clearTimeout(subscriptionSheetCloseTimer)
  clearProfilePhoneCountdown()
})

onPageScroll(({ scrollTop }) => {
  const nextScrollTop = Number(scrollTop) || 0
  if (activeTab.value === 'circle' && !circleDetailVisible.value) {
    circleOverviewScrollTop.value = nextScrollTop
  }
  circleCommunityHeaderScrollTop.value = nextScrollTop
  updateCircleTabbarOnScroll(nextScrollTop)
})

onReachBottom(() => {
  if (activeTab.value === 'mistakes' && !retestMode.value) {
    loadMoreMistakes()
  }
  if (activeTab.value === 'circle' && selectedCircleSection.value === 'community' && selectedCircleCommunityTab.value !== 'mentor') {
    void loadMoreCircleCommunityPosts()
  }
})

function openExamSwitchModal() {
  showExamSwitchModal.value = true
}

function closeExamSwitchModal() {
  showExamSwitchModal.value = false
}

async function selectProfileExam(code) {
  if (code === examCode.value) {
    closeExamSwitchModal()
    return
  }
  const switched = await changeExam(code)
  if (switched) closeExamSwitchModal()
}

async function changeExam(code) {
  if (!EXAM_OPTIONS.some((item) => item.code === code)) return false
  const previousCode = examCode.value
  examCode.value = code
  if (!isAuthed.value) {
    uni.setStorageSync('examCode', code)
    uni.showToast({ title: `目标版本已切换为 ${code}`, icon: 'none' })
    return true
  }
  const nextUser = updateAuthUser({ exam_target: code })
  if (nextUser) {
    authUser.value = nextUser
  }

  try {
    const remoteUser = await updateProfile({ exam_target: code })
    const syncedUser = updateAuthUser(remoteUser)
    if (syncedUser) {
      authUser.value = syncedUser
    }
    uni.showToast({ title: `目标版本已切换为 ${code}`, icon: 'none' })
    return true
  } catch (error) {
    examCode.value = previousCode
    const revertedUser = updateAuthUser({ exam_target: previousCode })
    if (revertedUser) {
      authUser.value = revertedUser
    }
    uni.showToast({ title: '目标版本同步失败，请稍后重试', icon: 'none' })
    return false
  }
}

function goModule(subject) {
  uni.setStorageSync('subject', subject)
  uni.navigateTo({ url: `/pages/practice/index?subject=${encodeURIComponent(subject)}` })
}

function handleHomeFocusChange(event) {
  const nextIndex = Number(event?.detail?.current)
  if (Number.isInteger(nextIndex) && nextIndex >= 0 && nextIndex < homeFocusItems.length) {
    homeFocusIndex.value = nextIndex
  }
}

function selectHomeFocus(index) {
  if (!Number.isInteger(index) || index < 0 || index >= homeFocusItems.length) return
  homeFocusIndex.value = index
}

function openHomeFocus(item) {
  openHomeContentTarget(item)
}

function openHomeNews(item) {
  openHomeContentTarget(item)
}

function openHomeContentTarget(item) {
  if (item?.routeKey === 'school-announcements') {
    uni.navigateTo({ url: '/pages-sub-data/school-announcements/index' })
    return
  }
  if (item?.routeKey === 'major-catalog') {
    uni.navigateTo({ url: '/pages-sub-data/major-catalog/index' })
    return
  }
  if (item?.routeKey === 'application-guide') {
    openNewsArchive()
    return
  }
  openHomeExternalLink(item?.url)
}

function openNewsArchive() {
  openHomeExternalLink('https://www.gatzs.com.cn/z/gatyz/')
}

function openHomeService(item) {
  if (item?.key === 'school-notices') {
    uni.navigateTo({ url: '/pages-sub-data/school-announcements/index' })
    return
  }
  if (item?.key === 'major-catalog') {
    uni.navigateTo({ url: '/pages-sub-data/major-catalog/index' })
    return
  }
  if (item?.key === 'application-guide') {
    openNewsArchive()
    return
  }
  uni.showToast({
    title: `${item?.title || '该'}查询功能即将开放`,
    icon: 'none'
  })
}

function openHomeExternalLink(url) {
  if (!url) return

  // #ifdef H5
  window.open(url, '_blank', 'noopener,noreferrer')
  // #endif

  // #ifdef APP-PLUS
  plus.runtime.openURL(url)
  // #endif

  // #ifdef MP-WEIXIN
  uni.setClipboardData({
    data: url,
    success: () => uni.showToast({ title: '官方链接已复制', icon: 'none' })
  })
  // #endif
}

function openMockExamIntro() {
  uni.navigateTo({
    url: `/pages/mock-exams/index?exam_code=${encodeURIComponent(examCode.value)}`
  })
}

function goPractice() {
  uni.navigateTo({ url: '/pages/practice/index' })
}

function goTaskPractice(task) {
  if (task?.subject) {
    uni.setStorageSync('subject', task.subject)
    const query = [
      ['subject', task.subject],
      ['module', task.module || ''],
      ['submodule', task.submodule || ''],
      ['count', task.questionCount || ''],
      ['difficulty', task.difficulty || ''],
      ['trainingMode', task.trainingMode || '']
    ]
      .filter(([, value]) => value)
      .map(([key, value]) => `${key}=${encodeURIComponent(value)}`)
      .join('&')
    uni.navigateTo({ url: `/pages/practice/index?${query}` })
    return
  }
  goPractice()
}

function goReportTask(task) {
  if (task?.type === 'mistakes') {
    wrongFilters.value = {
      subject: task.subject || '',
      module: task.module || '',
      submodule: task.submodule || ''
    }
    openMistakes()
    return
  }
  goTaskPractice(task)
}

function startTodayTraining() {
  if (!todayTraining.value.primary) {
    goPractice()
    return
  }
  goTaskPractice(todayTraining.value.primary)
}

function getTrainingSubjectLabel(subject) {
  return subject || '逻辑推理'
}

function getTrainingSubjectValues() {
  return trainingSubjectOptions.value.map((item) => item.value)
}

function getDefaultTrainingSubject() {
  const values = getTrainingSubjectValues()
  if (values.includes(trainingSubject.value)) {
    return trainingSubject.value
  }
  if (values.includes(smartRecommendation.value.subject)) {
    return smartRecommendation.value.subject
  }
  const preferred = examCode.value === 'Z002' ? '数学基础' : '逻辑推理'
  return values.includes(preferred) ? preferred : values[0] || fallbackSmartRecommendation.subject
}

function getSubjectFallbackTarget(subject) {
  return subjectFallbackTargets[subject] || fallbackSmartRecommendation
}

function syncTrainingSubject() {
  trainingSubject.value = getDefaultTrainingSubject()
  const fallback = getSubjectFallbackTarget(trainingSubject.value)
  if (!trainingSubject.value || smartRecommendation.value.subject !== trainingSubject.value) {
    smartRecommendation.value = { ...fallback }
  }
}

function selectTrainingSubject(subject) {
  if (trainingSubject.value === subject) return
  trainingSubject.value = subject
  const fallback = getSubjectFallbackTarget(subject)
  smartRecommendation.value = { ...fallback }
  if (smartMode.value) {
    refreshTrainingRecommendation()
  }
}

function openRecommendedTrainingSheet() {
  // #ifdef MP-WEIXIN
  uni.showToast({ title: '该功能暂未在小程序开放', icon: 'none' })
  return
  // #endif

  showStudyAdviceDetail.value = false
  smartMode.value = true
  manualDifficulty.value = '标准提升'
  manualQuestionCount.value = 10
  syncTrainingSubject()
  showTrainingSheet.value = true
  refreshTrainingRecommendation()
}

function closeRecommendedTrainingSheet() {
  if (generatingTraining.value) return
  showTrainingSheet.value = false
}

function openSubscriptionSheet() {
  void loadSubscriptionPageConfig()
  void loadSubscriptionMembershipStatus()
  resetSubscriptionSheetDrag()
  if (subscriptionSheetCloseTimer) {
    clearTimeout(subscriptionSheetCloseTimer)
    subscriptionSheetCloseTimer = null
  }
  if (subscriptionSheetOpenTimer) clearTimeout(subscriptionSheetOpenTimer)
  showSubscriptionSheet.value = true
  subscriptionSheetVisible.value = false
  nextTick(() => {
    subscriptionSheetOpenTimer = setTimeout(() => {
      if (showSubscriptionSheet.value) subscriptionSheetVisible.value = true
      subscriptionSheetOpenTimer = null
    }, 16)
  })
}

function closeSubscriptionSheet() {
  if (!showSubscriptionSheet.value) return
  resetSubscriptionSheetDrag()
  if (subscriptionSheetOpenTimer) {
    clearTimeout(subscriptionSheetOpenTimer)
    subscriptionSheetOpenTimer = null
  }
  subscriptionSheetVisible.value = false
  if (subscriptionSheetCloseTimer) clearTimeout(subscriptionSheetCloseTimer)
  subscriptionSheetCloseTimer = setTimeout(() => {
    showSubscriptionSheet.value = false
    subscriptionSheetCloseTimer = null
  }, 340)
}

function beginSubscriptionSheetDrag(event) {
  if (!subscriptionSheetVisible.value) return
  const touch = getSubscriptionSheetDragPoint(event)
  if (!touch) return
  subscriptionSheetDragStartY = Number(touch.clientY ?? touch.pageY ?? 0)
  subscriptionSheetDragStartAt = Date.now()
  subscriptionSheetDragY.value = 0
  subscriptionSheetDragging.value = true
}

function moveSubscriptionSheetDrag(event) {
  if (!subscriptionSheetDragging.value) return
  const touch = getSubscriptionSheetDragPoint(event)
  if (!touch) return
  const deltaY = Number(touch.clientY ?? touch.pageY ?? 0) - subscriptionSheetDragStartY
  if (deltaY <= 0) {
    subscriptionSheetDragY.value = 0
    return
  }
  event?.preventDefault?.()
  subscriptionSheetDragY.value = Math.round(deltaY <= 320 ? deltaY : 320 + (deltaY - 320) * 0.35)
}

function finishSubscriptionSheetDrag() {
  if (!subscriptionSheetDragging.value) return
  const elapsed = Math.max(1, Date.now() - subscriptionSheetDragStartAt)
  const velocity = subscriptionSheetDragY.value / elapsed
  const shouldClose = subscriptionSheetDragY.value >= 112
    || (subscriptionSheetDragY.value >= 48 && velocity >= 0.55)
  resetSubscriptionSheetDrag()
  if (shouldClose) closeSubscriptionSheet()
}

function cancelSubscriptionSheetDrag() {
  resetSubscriptionSheetDrag()
}

function resetSubscriptionSheetDrag() {
  subscriptionSheetDragging.value = false
  subscriptionSheetDragY.value = 0
  subscriptionSheetDragStartY = 0
  subscriptionSheetDragStartAt = 0
}

function getSubscriptionSheetDragPoint(event) {
  const touch = getCircleTouchPoint(event)
  if (touch) return touch
  const clientY = Number(event?.clientY ?? event?.pageY)
  return Number.isFinite(clientY) ? event : null
}

async function loadSubscriptionPageConfig() {
  try {
    const response = await fetchSubscriptionPageConfig()
    subscriptionPageConfig.value = createSubscriptionPageConfig(response)
  } catch (error) {
    // 配置接口在渐进部署期间不可用时保留内置默认值，避免阻塞“我的”页面。
  }
}

function createDefaultSubscriptionMembershipStatus() {
  return {
    membership_status: 'inactive',
    membership_plan: null,
    membership_started_at: null,
    membership_expires_at: null,
    membership_updated_at: null,
    membership_active: false
  }
}

function normalizeSubscriptionMembershipStatus(source = {}) {
  const rawStatus = String(source?.membership_status || 'inactive').toLowerCase()
  const membershipStatus = ['active', 'expired', 'inactive'].includes(rawStatus) ? rawStatus : 'inactive'
  return {
    membership_status: membershipStatus,
    membership_plan: source?.membership_plan || null,
    membership_started_at: source?.membership_started_at || null,
    membership_expires_at: source?.membership_expires_at || null,
    membership_updated_at: source?.membership_updated_at || null,
    membership_active: source?.membership_active === true || membershipStatus === 'active'
  }
}

function loadSubscriptionMembershipStatus() {
  if (!isLoggedIn()) {
    subscriptionMembership.value = createDefaultSubscriptionMembershipStatus()
    return Promise.resolve(subscriptionMembership.value)
  }
  if (subscriptionMembershipRequest) return subscriptionMembershipRequest

  subscriptionMembershipRequest = fetchMembershipStatus()
    .then((response) => {
      subscriptionMembership.value = normalizeSubscriptionMembershipStatus(response)
      return subscriptionMembership.value
    })
    .catch(() => subscriptionMembership.value)
    .finally(() => {
      subscriptionMembershipRequest = null
    })
  return subscriptionMembershipRequest
}

function handleSubscriptionSubscribe(plan) {
  const label = plan === 'quarterly' ? '季卡' : '月卡'
  uni.showToast({ title: `${label}订阅功能即将开放`, icon: 'none' })
}

function handleSubscriptionRestore() {
  uni.showToast({ title: '购买恢复功能即将开放', icon: 'none' })
}

function handleSmartModeChange(event) {
  smartMode.value = Boolean(event?.detail?.value)
  if (smartMode.value) {
    refreshTrainingRecommendation()
  }
}

function handleQuestionCountChange(event) {
  const nextValue = Number(event?.detail?.value || 10)
  manualQuestionCount.value = Math.min(30, Math.max(5, nextValue))
}

function normalizeTrainingRecommendation(response) {
  const target = response?.target || {}
  return {
    subject: target.subject || fallbackSmartRecommendation.subject,
    module: target.module || fallbackSmartRecommendation.module,
    submodule: target.submodule || fallbackSmartRecommendation.submodule,
    difficulty: target.difficulty || fallbackSmartRecommendation.difficulty,
    questionCount: Number(target.question_count || fallbackSmartRecommendation.questionCount),
    basis: target.basis || fallbackSmartRecommendation.basis
  }
}

async function refreshTrainingRecommendation() {
  if (!isAuthed.value || recommendationLoading.value) {
    return
  }

  recommendationLoading.value = true
  try {
    const response = await fetchAiTrainingRecommendation(examCode.value, trainingSubject.value)
    smartRecommendation.value = normalizeTrainingRecommendation(response)
  } catch (error) {
    smartRecommendation.value = { ...getSubjectFallbackTarget(trainingSubject.value) }
  } finally {
    recommendationLoading.value = false
  }
}

function buildAiTrainingPayload() {
  const recommendation = smartRecommendation.value
  const fallback = getSubjectFallbackTarget(trainingSubject.value)
  const subject = trainingSubject.value || recommendation.subject || fallback.subject
  const module = recommendation.subject === subject ? recommendation.module : fallback.module
  const submodule = recommendation.subject === subject ? recommendation.submodule : fallback.submodule
  if (smartMode.value) {
    return {
      smart_mode: true,
      exam_code: examCode.value,
      subject,
      question_count: recommendation.questionCount
    }
  }

  return {
    smart_mode: false,
    exam_code: examCode.value,
    subject,
    module,
    submodule,
    difficulty: manualDifficulty.value,
    question_count: manualQuestionCount.value
  }
}

function getGenerateEstimateSeconds(questionCount) {
  const count = Number(questionCount || 10)
  return Math.min(90, Math.max(25, count * 4 + 12))
}

function startGenerateCountdown(seconds) {
  stopGenerateCountdown()
  generateEstimate.value = seconds
  generateCountdown.value = seconds
  generateTimerId = setInterval(() => {
    generateCountdown.value = Math.max(1, generateCountdown.value - 1)
  }, 1000)
}

function stopGenerateCountdown() {
  if (generateTimerId) {
    clearInterval(generateTimerId)
    generateTimerId = null
  }
}

function openGeneratingModal(payload) {
  const estimate = getGenerateEstimateSeconds(payload.question_count)
  generationCancelled.value = false
  showGeneratingModal.value = true
  startGenerateCountdown(estimate)
}

function closeGeneratingModal() {
  showGeneratingModal.value = false
  stopGenerateCountdown()
}

function requestAiTrainingSession(payload) {
  return new Promise((resolve, reject) => {
    generateRequestTask = createAiTrainingRequestTask(payload, {
      success: resolve,
      fail: reject
    })
  })
}

function cancelGenerateTraining() {
  if (!generatingTraining.value) {
    closeGeneratingModal()
    return
  }

  generationCancelled.value = true
  if (generateRequestTask?.abort) {
    generateRequestTask.abort()
  }
  generateRequestTask = null
  generatingTraining.value = false
  closeGeneratingModal()
  uni.showToast({ title: '已取消生成', icon: 'none' })
}

async function handleGenerateTraining() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  if (generatingTraining.value) return

  const payload = buildAiTrainingPayload()
  generatingTraining.value = true
  showTrainingSheet.value = false
  openGeneratingModal(payload)

  try {
    const response = await requestAiTrainingSession(payload)
    if (generationCancelled.value) {
      return
    }
    closeGeneratingModal()
    uni.navigateTo({
      url: `/pages/practice/index?ai_session_id=${encodeURIComponent(response.session_id)}`
    })
  } catch (error) {
    if (generationCancelled.value) {
      return
    }
    closeGeneratingModal()
    const detail = error?.detail || 'AI 训练生成失败，请稍后重试'
    uni.showModal({
      title: '生成失败',
      content: detail,
      showCancel: false,
      confirmText: '知道了'
    })
  } finally {
    generateRequestTask = null
    generatingTraining.value = false
    if (!generationCancelled.value) {
      closeGeneratingModal()
    }
  }
}

function goLogin() {
  uni.navigateTo({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/home/index')}` })
}

function openProfileEditModal() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  profileEditNickname.value = String(authUser.value?.nickname || profile.value.userName || '').trim()
  profileEditAvatarPreview.value = avatarImageUrl.value || ''
  profileEditAvatarPath.value = ''
  profileEditAvatarFile.value = null
  profileEditAvatarName.value = 'avatar.jpg'
  showProfileEditModal.value = true
}

function closeProfileEditModal(force = false) {
  if (!force && (profileEditSaving.value || profileEditUploading.value)) return
  showProfileEditModal.value = false
  profileEditAvatarPreview.value = ''
  profileEditAvatarPath.value = ''
  profileEditAvatarFile.value = null
}

function chooseProfileAvatar() {
  if (profileEditUploading.value) return

  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
    success(result) {
      const tempFile = Array.isArray(result.tempFiles) ? result.tempFiles[0] : null
      const fileCandidate = tempFile?.file || tempFile?.fileObject || tempFile
      const file = typeof Blob !== 'undefined' && fileCandidate instanceof Blob ? fileCandidate : null
      const filePath = (
        (Array.isArray(result.tempFilePaths) ? result.tempFilePaths[0] : '') ||
        tempFile?.path ||
        tempFile?.tempFilePath ||
        ''
      )

      if (!filePath && !file) {
        uni.showToast({ title: '未读取到图片，请重新选择', icon: 'none' })
        return
      }

      profileEditAvatarPath.value = filePath
      profileEditAvatarFile.value = file
      profileEditAvatarName.value = tempFile?.name || file?.name || 'avatar.jpg'
      profileEditAvatarPreview.value = filePath || (file && typeof URL !== 'undefined' ? URL.createObjectURL(file) : '')
    },
    fail(error) {
      const message = String(error?.errMsg || '').toLowerCase()
      if (!message.includes('cancel')) {
        uni.showToast({ title: '图片选择失败，请重试', icon: 'none' })
      }
    }
  })
}

async function saveProfileEdit() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  const nickname = String(profileEditNickname.value || '').trim()
  if (!nickname) {
    uni.showToast({ title: '请填写昵称', icon: 'none' })
    return
  }
  if (profileEditSaving.value || profileEditUploading.value) return

  profileEditSaving.value = true
  let uploadedUser = null
  try {
    if (profileEditAvatarPath.value || profileEditAvatarFile.value) {
      profileEditUploading.value = true
      uploadedUser = await uploadAvatar({
        filePath: profileEditAvatarPath.value,
        file: profileEditAvatarFile.value,
        fileName: profileEditAvatarName.value
      })
      profileEditUploading.value = false
      if (!uploadedUser?.avatar_url) {
        throw { detail: '头像上传失败，请重试' }
      }
    }

    const payload = { nickname }
    if (uploadedUser?.avatar_url) payload.avatar_url = uploadedUser.avatar_url
    const nextUser = await updateProfile(payload)
    const savedUser = updateAuthUser(nextUser || uploadedUser || { nickname }) || nextUser || uploadedUser
    if (savedUser) authUser.value = savedUser
    closeProfileEditModal(true)
    uni.showToast({ title: '个人资料已保存', icon: 'success' })
  } catch (error) {
    profileEditUploading.value = false
    uni.showToast({ title: error?.detail || '保存失败，请稍后重试', icon: 'none' })
  } finally {
    profileEditSaving.value = false
    profileEditUploading.value = false
  }
}

function openEmailBindingModal() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  profileEmailForm.email = ''
  profileEmailForm.code = ''
  showEmailBindingModal.value = true
}

function closeEmailBindingModal(force = false) {
  if (!force && (profileEmailSending.value || profileEmailSaving.value)) return
  showEmailBindingModal.value = false
  profileEmailForm.email = ''
  profileEmailForm.code = ''
}

function isValidProfileEmail(value) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(String(value || ''))
}

async function sendProfileEmailCode() {
  const email = String(profileEmailForm.email || '').trim()
  if (!isValidProfileEmail(email)) {
    uni.showToast({ title: '请填写正确的新邮箱', icon: 'none' })
    return
  }
  if (email === getPublicEmail(authUser.value)) {
    uni.showToast({ title: '新邮箱不能与当前邮箱相同', icon: 'none' })
    return
  }

  profileEmailSending.value = true
  try {
    if (profileUsesWechatBinding.value) {
      await sendBindEmailCode({ email })
    } else {
      await sendChangeEmailCode({ email })
    }
    uni.showToast({ title: '验证码已发送', icon: 'none' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '验证码发送失败', icon: 'none' })
  } finally {
    profileEmailSending.value = false
  }
}

async function submitProfileEmailBinding() {
  const email = String(profileEmailForm.email || '').trim()
  const code = String(profileEmailForm.code || '').trim()
  if (!isValidProfileEmail(email) || !code) {
    uni.showToast({ title: '请填写邮箱和验证码', icon: 'none' })
    return
  }

  profileEmailSaving.value = true
  try {
    if (profileUsesWechatBinding.value) {
      let result = await bindWechatEmail({ email, verification_code: code })
      if (result?.status === 'merge_required') {
        const profileSource = await chooseProfileMergeSource(result)
        if (!profileSource) {
          uni.showToast({ title: '已取消账号合并', icon: 'none' })
          return
        }
        result = await bindWechatEmail({ email, verification_code: code, profile_source: profileSource })
      }
      applyProfileAuthResult(result?.auth)
      uni.showToast({ title: result?.detail || '邮箱绑定成功', icon: 'success' })
    } else {
      const nextUser = await changeEmailWithCode({ email, verification_code: code })
      const savedUser = updateAuthUser(nextUser) || nextUser
      if (savedUser) authUser.value = savedUser
      uni.showToast({ title: '绑定邮箱已更新', icon: 'success' })
    }
    closeEmailBindingModal(true)
  } catch (error) {
    uni.showToast({ title: error?.detail || '绑定失败，请检查验证码', icon: 'none' })
  } finally {
    profileEmailSaving.value = false
  }
}

function openPhoneBindingModal() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  profilePhoneForm.phone = ''
  profilePhoneForm.code = ''
  clearProfilePhoneCountdown()
  showPhoneBindingModal.value = true
}

function closePhoneBindingModal(force = false) {
  if (!force && (profilePhoneSending.value || profilePhoneSaving.value)) return
  showPhoneBindingModal.value = false
  profilePhoneForm.phone = ''
  profilePhoneForm.code = ''
  clearProfilePhoneCountdown()
}

function normalizeProfilePhoneInput(value) {
  return String(value || '').replace(/[\s\-()]/g, '')
}

function isValidProfilePhone(value) {
  return /^\+?\d{8,15}$/.test(normalizeProfilePhoneInput(value))
}

function maskProfilePhone(value) {
  const normalized = normalizeProfilePhoneInput(value)
  if (!normalized) return ''
  const sign = normalized.startsWith('+') ? '+' : ''
  const digits = normalized.replace(/\D/g, '')
  if (digits.length < 8) return normalized
  return `${sign}${digits.slice(0, 3)}****${digits.slice(-4)}`
}

function startProfilePhoneCountdown(seconds = 60) {
  clearProfilePhoneCountdown()
  profilePhoneCountdown.value = Math.max(0, Number(seconds) || 0)
  if (!profilePhoneCountdown.value) return
  profilePhoneCountdownTimer = setInterval(() => {
    profilePhoneCountdown.value = Math.max(0, profilePhoneCountdown.value - 1)
    if (profilePhoneCountdown.value <= 0) clearProfilePhoneCountdown()
  }, 1000)
}

function clearProfilePhoneCountdown() {
  if (profilePhoneCountdownTimer) {
    clearInterval(profilePhoneCountdownTimer)
    profilePhoneCountdownTimer = null
  }
  profilePhoneCountdown.value = 0
}

async function sendProfilePhoneCode() {
  const phone = normalizeProfilePhoneInput(profilePhoneForm.phone)
  if (!isValidProfilePhone(phone)) {
    uni.showToast({ title: '请填写正确的手机号码', icon: 'none' })
    return
  }
  if (normalizeProfilePhoneInput(authUser.value?.phone) === phone) {
    uni.showToast({ title: '该号码已绑定当前账号', icon: 'none' })
    return
  }

  profilePhoneSending.value = true
  try {
    const response = await sendBindPhoneCode({ phone })
    startProfilePhoneCountdown(60)
    if (response?.debug_code) {
      profilePhoneForm.code = String(response.debug_code)
      uni.showModal({
        title: '本地测试验证码',
        content: String(response.debug_code),
        showCancel: false
      })
    } else {
      uni.showToast({ title: '验证码已发送', icon: 'success' })
    }
  } catch (error) {
    uni.showToast({ title: error?.detail || '验证码发送失败', icon: 'none' })
  } finally {
    profilePhoneSending.value = false
  }
}

async function submitProfilePhoneBinding() {
  const phone = normalizeProfilePhoneInput(profilePhoneForm.phone)
  const code = String(profilePhoneForm.code || '').trim()
  if (!isValidProfilePhone(phone) || !code) {
    uni.showToast({ title: '请填写手机号码和验证码', icon: 'none' })
    return
  }

  profilePhoneSaving.value = true
  try {
    const nextUser = await bindPhone({ phone, verification_code: code })
    const savedUser = updateAuthUser(nextUser) || nextUser
    if (savedUser) authUser.value = savedUser
    closePhoneBindingModal(true)
    uni.showToast({ title: '手机号码绑定成功', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '绑定失败，请检查验证码', icon: 'none' })
  } finally {
    profilePhoneSaving.value = false
  }
}

function applyProfileAuthResult(auth) {
  if (!auth?.access_token || !auth?.user) {
    throw { detail: '账号会话更新失败，请重新登录' }
  }
  saveAuthSession({
    accessToken: auth.access_token,
    refreshToken: auth.refresh_token,
    user: auth.user
  })
  authUser.value = auth.user
  authed.value = true
}

function chooseProfileMergeSource(result) {
  const emailNickname = result?.email_account?.nickname || '邮箱账号'
  const wechatNickname = result?.wechat_account?.nickname || '微信账号'
  const maskedEmail = result?.email_account?.email_masked || profileEmailForm.email

  return new Promise((resolve) => {
    uni.showModal({
      title: '发现已注册邮箱账号',
      content: `${maskedEmail} 已注册。合并后两边的作答、错题、收藏和统计都会保留，是否继续？`,
      confirmText: '继续合并',
      cancelText: '暂不合并',
      success(modalResult) {
        if (!modalResult.confirm) {
          resolve(null)
          return
        }
        uni.showActionSheet({
          title: '选择合并后使用的账号资料',
          itemList: [`保留微信资料（${wechatNickname}）`, `保留邮箱资料（${emailNickname}）`],
          success(actionResult) {
            resolve(actionResult.tapIndex === 0 ? 'wechat' : 'email')
          },
          fail() {
            resolve(null)
          }
        })
      },
      fail() {
        resolve(null)
      }
    })
  })
}

function handleAccountEntry() {
  openProfileEditModal()
}

function goLeaderboard() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  uni.navigateTo({ url: '/pages/leaderboard/index' })
}

function goDailyLeaderboard() {
  if (!isAuthed.value) {
    uni.navigateTo({
      url: `/pages/login/index?redirect=${encodeURIComponent('/pages/daily-leaderboard/index')}`
    })
    return
  }
  uni.navigateTo({ url: '/pages/daily-leaderboard/index' })
}

function formatUnreadBadge(count) {
  const value = Math.max(0, Number(count) || 0)
  return value > 99 ? '99+' : String(value)
}

function normalizeUnreadTargetMap(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return {}
  return Object.fromEntries(
    Object.entries(value)
      .map(([key, count]) => [String(key || '').trim(), Math.max(0, Number(count) || 0)])
      .filter(([key, count]) => key && count > 0)
  )
}

function getCircleSectionUnreadCount(sectionKey) {
  return sectionKey === 'community' ? communityUnreadCount.value : 0
}

function getCircleCommunityTabUnreadCount(tab) {
  if (tab === 'chat') return communityChatUnreadCount.value
  if (tab === 'experience') return communityExperienceUnreadCount.value
  if (tab === 'mentor') return applicantConsultationUnreadCount.value + mentorConsultationUnreadCount.value
  return 0
}

function getCommunityPostUnreadCount(post = {}) {
  const tab = normalizeCircleCommunityPostType(post.postType || post.post_type)
  return Number(communityPostUnreadTargets.value?.[tab]?.[String(post.id || '')] || 0)
}

function isCommunityPostUnread(post) {
  return getCommunityPostUnreadCount(post) > 0
}

function applyCommunityPostReadLocally(post = {}) {
  const postId = String(post.id || '').trim()
  const tab = normalizeCircleCommunityPostType(post.postType || post.post_type)
  const unreadCount = Number(communityPostUnreadTargets.value?.[tab]?.[postId] || 0)
  if (!postId || unreadCount <= 0) return 0
  const nextTabTargets = { ...(communityPostUnreadTargets.value?.[tab] || {}) }
  delete nextTabTargets[postId]
  communityPostUnreadTargets.value = {
    ...communityPostUnreadTargets.value,
    [tab]: nextTabTargets
  }
  if (tab === 'experience') {
    communityExperienceUnreadCount.value = Math.max(0, communityExperienceUnreadCount.value - unreadCount)
  } else {
    communityChatUnreadCount.value = Math.max(0, communityChatUnreadCount.value - unreadCount)
  }
  postInteractionUnreadCount.value = Math.max(0, postInteractionUnreadCount.value - unreadCount)
  communityUnreadCount.value = Math.max(0, communityUnreadCount.value - unreadCount)
  notificationUnreadCount.value = Math.max(0, notificationUnreadCount.value - unreadCount)
  return unreadCount
}

function markCommunityPostNotificationsRead(post = {}) {
  const postId = String(post.id || '').trim()
  if (!postId || !isAuthed.value) return
  // 立即作废已发出的旧全局摘要，避免旧响应覆盖本地已清除的红点。
  latestUnreadRefreshToken += 1
  applyCommunityPostReadLocally(post)
  void markUserNotificationReadTarget('community_post', postId)
    .then(() => refreshMessageUnreadCounts())
    .catch(() => refreshMessageUnreadCounts())
}

async function refreshMessageUnreadCounts() {
  const refreshToken = ++latestUnreadRefreshToken
  if (!isAuthed.value) {
    if (refreshToken !== latestUnreadRefreshToken) return
    officialUnreadCount.value = 0
    notificationUnreadCount.value = 0
    communityUnreadCount.value = 0
    postInteractionUnreadCount.value = 0
    communityReportUnreadCount.value = 0
    consultationUnreadCount.value = 0
    communityChatUnreadCount.value = 0
    communityExperienceUnreadCount.value = 0
    applicantConsultationUnreadCount.value = 0
    mentorConsultationUnreadCount.value = 0
    communityPostUnreadTargets.value = { chat: {}, experience: {} }
    return
  }
  const [officialResult, summaryResult] = await Promise.allSettled([
    fetchOfficialMessages(),
    fetchUserNotificationUnreadSummary()
  ])
  if (refreshToken !== latestUnreadRefreshToken) return
  officialUnreadCount.value = officialResult.status === 'fulfilled'
    ? Number(officialResult.value?.unread_count || 0)
    : 0
  if (summaryResult.status === 'fulfilled') {
    const summary = summaryResult.value || {}
    notificationUnreadCount.value = Number(summary.total || 0)
    postInteractionUnreadCount.value = Number(summary.post_interactions || 0)
    communityReportUnreadCount.value = Number(summary.community_reports || 0)
    consultationUnreadCount.value = Number(summary.consultation_orders ?? summary.consultations ?? 0)
    communityChatUnreadCount.value = Number(summary.community_chat || 0)
    communityExperienceUnreadCount.value = Number(summary.community_experience || 0)
    applicantConsultationUnreadCount.value = Number(summary.applicant_consultations || 0)
    mentorConsultationUnreadCount.value = Number(summary.mentor_consultations || 0)
    const postTargets = summary.community_post_targets || {}
    communityPostUnreadTargets.value = {
      chat: normalizeUnreadTargetMap(postTargets.chat),
      experience: normalizeUnreadTargetMap(postTargets.experience)
    }
    const fallbackCircleUnread = postInteractionUnreadCount.value
      + applicantConsultationUnreadCount.value
      + mentorConsultationUnreadCount.value
    communityUnreadCount.value = Number(summary.circle ?? fallbackCircleUnread) || 0
    return
  }

  // 旧后端尚未重启到新接口时，仍让全局消息铃铛保持可用。
  try {
    const fallback = await fetchUserNotifications({ limit: 1 })
    if (refreshToken !== latestUnreadRefreshToken) return
    notificationUnreadCount.value = Number(fallback?.unread_count || 0)
  } catch (error) {
    if (refreshToken !== latestUnreadRefreshToken) return
    notificationUnreadCount.value = 0
  }
  if (refreshToken !== latestUnreadRefreshToken) return
  communityUnreadCount.value = 0
  postInteractionUnreadCount.value = 0
  communityReportUnreadCount.value = 0
  consultationUnreadCount.value = 0
  communityChatUnreadCount.value = 0
  communityExperienceUnreadCount.value = 0
  applicantConsultationUnreadCount.value = 0
  mentorConsultationUnreadCount.value = 0
  communityPostUnreadTargets.value = { chat: {}, experience: {} }
}

function openMessageCenter() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  uni.navigateTo({ url: '/pages/notifications/index' })
}

function openApplicantConsultationUpdates() {
  uni.navigateTo({ url: '/pages-sub-consultation/consultation/my-consultations' })
}

function openMentorConsultationUpdates() {
  uni.navigateTo({ url: '/pages-sub-consultation/consultation/mentor-apply?mode=center' })
}

function openMyPostUpdates(postType) {
  const normalizedType = normalizeCircleCommunityPostType(postType)
  uni.navigateTo({ url: `/pages/circle/my-posts?type=${normalizedType}` })
}

function clearCircleOverviewRestoreTimer() {
  if (!circleOverviewRestoreTimer) return
  clearTimeout(circleOverviewRestoreTimer)
  circleOverviewRestoreTimer = null
}

function prefersReducedCircleRouteMotion() {
  let reduced = false
  // #ifdef H5
  reduced = typeof window !== 'undefined'
    && typeof window.matchMedia === 'function'
    && window.matchMedia('(prefers-reduced-motion: reduce)').matches
  // #endif
  return reduced
}

function clearCircleDetailRouteTimers() {
  if (circleDetailRouteFrameTimer) {
    clearTimeout(circleDetailRouteFrameTimer)
    circleDetailRouteFrameTimer = null
  }
  if (circleDetailRouteFinishTimer) {
    clearTimeout(circleDetailRouteFinishTimer)
    circleDetailRouteFinishTimer = null
  }
}

function resetCircleEdgeSwipeState() {
  circleEdgeSwipeStart.value = null
  circleEdgeSwipeOffset.value = 0
  circleEdgeSwipeSettleDuration.value = CIRCLE_DETAIL_ROUTE_DURATION
}

function getCircleRouteViewportWidth() {
  let width = 0
  try {
    const systemInfo = uni.getSystemInfoSync?.() || {}
    width = Number(systemInfo.windowWidth || systemInfo.screenWidth || 0)
  } catch (error) {
    width = 0
  }
  // #ifdef H5
  if (!width && typeof window !== 'undefined') width = Number(window.innerWidth || 0)
  // #endif
  return Math.max(1, width || 375)
}

function prepareCircleRouteUnderlay() {
  circleOverviewVisible.value = true
  // 详情页下方始终使用真实数据静态镜像，避免返回首帧重新挂载 swiper/canvas。
  circleAppRouteUnderlay.value = true
}

function parkCircleRouteUnderlay() {
  if (!circleDetailVisible.value) return
  circleOverviewVisible.value = true
  circleAppRouteUnderlay.value = true
}

function resetCircleDetailRouteState() {
  clearCircleDetailRouteTimers()
  resetCircleEdgeSwipeState()
  circleDetailRouteMotion.value = 'idle'
  circleDetailMounted.value = false
  circleDetailVisible.value = false
  circleOverviewVisible.value = true
  circleAppRouteUnderlay.value = false
  circleDetailReturnScrollTop = 0
}

function showCircleDetailImmediately() {
  clearCircleDetailRouteTimers()
  resetCircleEdgeSwipeState()
  circleDetailRouteMotion.value = 'idle'
  circleOverviewVisible.value = true
  circleAppRouteUnderlay.value = true
  circleDetailVisible.value = true
  circleDetailMounted.value = true
}

function scheduleCircleDetailRouteFinish(expectedMotion, duration = CIRCLE_DETAIL_ROUTE_DURATION) {
  if (circleDetailRouteFinishTimer) clearTimeout(circleDetailRouteFinishTimer)
  const delay = prefersReducedCircleRouteMotion()
    ? 0
    : Math.max(0, Number(duration) || 0) + CIRCLE_DETAIL_ROUTE_FALLBACK_DELAY
  circleDetailRouteFinishTimer = setTimeout(() => {
    circleDetailRouteFinishTimer = null
    if (circleDetailRouteMotion.value !== expectedMotion) return
    if (expectedMotion === 'entering') {
      finishCircleDetailRouteEnter()
    } else if (expectedMotion === 'leaving' || expectedMotion === 'drag-leaving') {
      finishCircleDetailRouteLeave()
    } else if (expectedMotion === 'drag-cancelling') {
      finishCircleEdgeSwipeCancel()
    }
  }, delay)
}

function showCircleDetailWithTransition() {
  clearCircleDetailRouteTimers()
  resetCircleEdgeSwipeState()
  circleAppRouteUnderlay.value = false
  circleDetailVisible.value = true
  circleDetailMounted.value = true

  if (prefersReducedCircleRouteMotion()) {
    circleOverviewVisible.value = false
    circleDetailRouteMotion.value = 'idle'
    return
  }

  circleDetailRouteMotion.value = 'enter-from'
  circleOverviewVisible.value = false
  // H5 保留真实总览；App 使用不含原生 swiper/canvas 的静态底层，避免叠层和空白首帧。
  // #ifdef H5
  circleOverviewVisible.value = true
  // #endif

  // #ifdef APP-PLUS
  circleAppRouteUnderlay.value = true
  circleOverviewVisible.value = true
  // #endif

  nextTick(() => {
    circleDetailRouteFrameTimer = setTimeout(() => {
      circleDetailRouteFrameTimer = null
      if (!circleDetailMounted.value || circleDetailRouteMotion.value !== 'enter-from') return
      circleDetailRouteMotion.value = 'entering'
      scheduleCircleDetailRouteFinish('entering')
    }, CIRCLE_DETAIL_ROUTE_FRAME_DELAY)
  })
}

function finishCircleDetailRouteEnter() {
  if (circleDetailRouteMotion.value !== 'entering') return
  if (circleDetailRouteFinishTimer) {
    clearTimeout(circleDetailRouteFinishTimer)
    circleDetailRouteFinishTimer = null
  }
  resetCircleEdgeSwipeState()
  circleDetailRouteMotion.value = 'idle'
  circleOverviewVisible.value = true
  circleAppRouteUnderlay.value = true
}

function finishCircleDetailRouteLeave() {
  if (!['leaving', 'drag-leaving'].includes(circleDetailRouteMotion.value)) return
  const returnScrollTop = circleDetailReturnScrollTop
  clearCircleDetailRouteTimers()
  resetCircleEdgeSwipeState()
  circleDetailMounted.value = false
  circleDetailVisible.value = false
  circleOverviewVisible.value = true
  circleAppRouteUnderlay.value = true
  circleDetailRouteMotion.value = 'idle'
  selectedCircleSection.value = 'overview'
  selectedScoreLineRecord.value = null
  selectedScoreLineRecordEntry.value = 'list'
  selectedCirclePost.value = null
  closeCommunityPost()
  circleCommunityHeaderScrollTop.value = 0
  circleDetailReturnScrollTop = 0
  nextTick(() => {
    circleDetailRouteFrameTimer = setTimeout(() => {
      circleDetailRouteFrameTimer = null
      if (circleDetailVisible.value) return
      circleAppRouteUnderlay.value = false
      if (activeTab.value === 'circle') restoreCircleOverviewScrollPosition(returnScrollTop)
    }, CIRCLE_DETAIL_ROUTE_FRAME_DELAY)
  })
}

function handleCircleDetailRouteTransitionEnd(event) {
  if (event?.target && event?.currentTarget && event.target !== event.currentTarget) return
  const propertyName = event?.propertyName || event?.detail?.propertyName || ''
  if (propertyName && propertyName !== 'transform' && propertyName !== 'left') return
  if (circleDetailRouteMotion.value === 'entering') {
    finishCircleDetailRouteEnter()
  } else if (circleDetailRouteMotion.value === 'leaving' || circleDetailRouteMotion.value === 'drag-leaving') {
    finishCircleDetailRouteLeave()
  } else if (circleDetailRouteMotion.value === 'drag-cancelling') {
    finishCircleEdgeSwipeCancel()
  }
}

function restoreCircleOverviewScrollPosition(scrollTop) {
  const targetScrollTop = Math.max(0, Number(scrollTop) || 0)
  const restore = () => {
    uni.pageScrollTo({ scrollTop: targetScrollTop, duration: 0 })
  }
  clearCircleOverviewRestoreTimer()
  nextTick(() => {
    restore()
    circleOverviewRestoreTimer = setTimeout(() => {
      restore()
      circleOverviewRestoreTimer = null
    }, 48)
  })
}

function openCircleSection(key) {
  if (!circleSections.some((item) => item.key === key) || circleDetailVisible.value) return
  clearCircleOverviewRestoreTimer()
  resetCircleTabbar()
  clearCircleScoreTooltip()
  selectedCircleSection.value = key
  selectedScoreLineRecord.value = null
  selectedScoreLineRecordEntry.value = 'list'
  selectedCirclePost.value = null
  closeCommunityPost()
  circleDetailScrollTop.value = 0
  circleCommunityHeaderScrollTop.value = 0
  showCircleDetailWithTransition()
  if (key === 'community') {
    selectedCircleCommunityTab.value = 'chat'
    selectedCommunityCategory.value = '全部'
    communitySearchKeyword.value = ''
    selectedExperienceCategory.value = '全部'
    experienceSearchKeyword.value = ''
    // 先完成详情滑入，再回填社区内容，避免 iOS 首帧与缓存处理抢占同一帧。
    const communityLoadDelay = circleDetailRouteMotion.value === 'idle'
      ? 0
      : CIRCLE_DETAIL_ROUTE_DURATION + CIRCLE_DETAIL_ROUTE_FRAME_DELAY
    nextTick(() => {
      setTimeout(() => {
        if (!circleDetailVisible.value || selectedCircleSection.value !== 'community') return
        void loadMentorProfiles()
        const shouldRefreshChat = consumeCircleCommunityFeedRefresh('chat')
        const sortBy = selectedCommunityPostSort.value
        const featuredOnly = sortBy === 'featured'
        if (!featuredOnly && sortBy !== 'hot') hydrateCircleCommunityFeed('chat')
        void loadCircleCommunityPosts('chat', {
          force: shouldRefreshChat || featuredOnly || sortBy === 'hot',
          featuredOnly,
          sortBy
        })
      }, communityLoadDelay)
    })
  }
}

function prepareCircleDetailRouteLeave() {
  prepareCircleRouteUnderlay()
  circleDetailRouteMotion.value = 'leave-preparing'
  nextTick(() => {
    circleDetailRouteFrameTimer = setTimeout(() => {
      circleDetailRouteFrameTimer = null
      if (!circleDetailVisible.value || circleDetailRouteMotion.value !== 'leave-preparing') return
      circleDetailRouteMotion.value = 'leaving'
      scheduleCircleDetailRouteFinish('leaving')
    }, CIRCLE_DETAIL_ROUTE_FRAME_DELAY)
  })
}

function returnToCircleOverview() {
  if (circleDetailRouteMotion.value === 'dragging') {
    circleDetailReturnScrollTop = circleOverviewScrollTop.value
    resetCircleTabbar()
    clearCircleScoreTooltip()
    startCircleEdgeSwipeSettle('drag-leaving', circleEdgeSwipeViewportWidth.value)
    return
  }
  if (
    !circleDetailVisible.value
    || circleDetailRouteMotion.value === 'leave-preparing'
    || circleDetailRouteMotion.value === 'leaving'
    || circleDetailRouteMotion.value === 'drag-cancelling'
    || circleDetailRouteMotion.value === 'drag-leaving'
  ) return
  circleDetailReturnScrollTop = circleOverviewScrollTop.value
  resetCircleTabbar()
  clearCircleScoreTooltip()
  clearCircleDetailRouteTimers()

  if (prefersReducedCircleRouteMotion()) {
    circleDetailRouteMotion.value = 'leaving'
    finishCircleDetailRouteLeave()
    return
  }

  // 底层静态镜像已常驻；这里只启动详情离场，避免返回首帧重新挂载整页。
  // 镜像层不挂载原生 swiper/canvas，返回过程中不会被原生层覆盖。
  prepareCircleDetailRouteLeave()
  return
}

function handleCircleDetailBack() {
  if (selectedCircleSection.value === 'scores' && selectedScoreLineRecord.value) {
    closeScoreLineRecord()
    return
  }
  returnToCircleOverview()
}

function openCircleScoreLineRecord(record) {
  if (!record || circleDetailVisible.value) return
  clearCircleOverviewRestoreTimer()
  resetCircleTabbar()
  clearCircleScoreTooltip()
  selectedCircleSection.value = 'scores'
  selectedScoreLineRecord.value = record
  selectedScoreLineRecordEntry.value = 'overview'
  selectedCirclePost.value = null
  closeCommunityPost()
  circleDetailScrollTop.value = 0
  circleCommunityHeaderScrollTop.value = 0
  showCircleDetailWithTransition()
}

function openScoreLineRecord(record) {
  if (!record) return
  clearCircleScoreTooltip()
  selectedScoreLineRecord.value = record
  selectedScoreLineRecordEntry.value = 'list'
  scrollCircleContentToTop()
}

function closeScoreLineRecord() {
  if (!selectedScoreLineRecord.value) return
  if (selectedScoreLineRecordEntry.value === 'overview') {
    returnToCircleOverview()
    return
  }
  clearCircleScoreTooltip()
  selectedScoreLineRecord.value = null
  selectedScoreLineRecordEntry.value = 'list'
  scrollCircleContentToTop()
}

function selectScoreLineYear(year) {
  if (!scoreLineYearFilterOptions.value.includes(year)) return
  selectedScoreLineYear.value = year
}

function selectScoreLineRegion(region) {
  if (!scoreLineRegionFilterOptions.value.some((item) => item.name === region)) return
  selectedScoreLineRegion.value = region
}

function onScoreLineYearPickerChange(event) {
  const option = scoreLineYearPickerOptions.value[Number(event?.detail?.value)]
  if (option) selectScoreLineYear(option.value)
}

function onScoreLineRegionPickerChange(event) {
  const option = scoreLineRegionPickerOptions.value[Number(event?.detail?.value)]
  if (option) selectScoreLineRegion(option.value)
}

function clearScoreLineSearch() {
  scoreLineSearchKeyword.value = ''
}

function resetScoreLineFilters() {
  scoreLineSearchKeyword.value = ''
  selectedScoreLineRegion.value = '全部'
  selectedScoreLineYear.value = '全部'
}

function loadMoreScoreLineRecords() {
  visibleScoreLineRecordCount.value += 24
}

function handleCircleDetailScroll(event) {
  const nextScrollTop = Number(event?.detail?.scrollTop) || 0
  circleCommunityHeaderScrollTop.value = nextScrollTop
  updateCircleTabbarOnScroll(nextScrollTop)
}

function handleCircleDetailReachBottom() {
  if (
    selectedCircleSection.value === 'community'
    && selectedCircleCommunityTab.value !== 'mentor'
  ) {
    void loadMoreCircleCommunityPosts()
  }
}

function scrollCircleContentToTop() {
  circleCommunityHeaderScrollTop.value = 0
  if (circleDetailVisible.value || selectedCircleSection.value !== 'overview') {
    circleDetailScrollTop.value = circleDetailScrollTop.value === 0 ? 1 : 0
    nextTick(() => {
      circleDetailScrollTop.value = 0
    })
    return
  }
  uni.pageScrollTo({
    scrollTop: 0,
    duration: 0
  })
}

function getCircleTouchPoint(event) {
  return event?.touches?.[0]
    || event?.changedTouches?.[0]
    || (Number.isFinite(Number(event?.clientX)) ? event : null)
}

function canStartCircleEdgeSwipe() {
  if (!circleDetailVisible.value || circleDetailRouteMotion.value !== 'idle') return false
  if (selectedCommunityCommentsPost.value || selectedCommunityPost.value || selectedCirclePost.value) return false
  if (
    selectedCircleSection.value === 'scores'
    && selectedScoreLineRecord.value
    && selectedScoreLineRecordEntry.value === 'list'
  ) return false
  return true
}

function abandonCircleEdgeSwipeTracking() {
  const wasDragging = circleDetailRouteMotion.value === 'dragging'
  resetCircleEdgeSwipeState()
  if (wasDragging) circleDetailRouteMotion.value = 'idle'
  parkCircleRouteUnderlay()
}

function getCircleEdgeSwipeSettleDuration(targetOffset) {
  const width = Math.max(1, Number(circleEdgeSwipeViewportWidth.value) || 1)
  const distance = Math.abs(Number(targetOffset) - Number(circleEdgeSwipeOffset.value))
  return Math.round(Math.min(300, Math.max(140, 115 + (distance / width) * 185)))
}

function startCircleEdgeSwipeSettle(motion, targetOffset) {
  const width = Math.max(1, Number(circleEdgeSwipeViewportWidth.value) || 1)
  const normalizedTarget = Math.min(width, Math.max(0, Number(targetOffset) || 0))
  const duration = prefersReducedCircleRouteMotion()
    ? 0
    : getCircleEdgeSwipeSettleDuration(normalizedTarget)

  circleEdgeSwipeStart.value = null
  circleEdgeSwipeSettleDuration.value = duration
  circleDetailRouteMotion.value = motion

  nextTick(() => {
    if (circleDetailRouteMotion.value !== motion) return
    circleEdgeSwipeOffset.value = normalizedTarget
    if (duration <= 0) {
      if (motion === 'drag-leaving') finishCircleDetailRouteLeave()
      else finishCircleEdgeSwipeCancel()
      return
    }
    scheduleCircleDetailRouteFinish(motion, duration)
  })
}

function finishCircleEdgeSwipeCancel() {
  if (circleDetailRouteMotion.value !== 'drag-cancelling') return
  clearCircleDetailRouteTimers()
  resetCircleEdgeSwipeState()
  circleDetailRouteMotion.value = 'idle'
  parkCircleRouteUnderlay()
}

function beginCircleEdgeSwipe(event) {
  if (!canStartCircleEdgeSwipe()) return abandonCircleEdgeSwipeTracking()
  if (Number.isFinite(Number(event?.button)) && Number(event.button) !== 0) return

  const touch = getCircleTouchPoint(event)
  if (!touch) return
  const startX = Number(touch.clientX ?? touch.pageX ?? 0)
  const startY = Number(touch.clientY ?? touch.pageY ?? 0)
  if (startX > CIRCLE_EDGE_SWIPE_START_WIDTH) return

  clearCircleDetailRouteTimers()
  circleDetailReturnScrollTop = circleOverviewScrollTop.value
  circleEdgeSwipeViewportWidth.value = getCircleRouteViewportWidth()
  circleEdgeSwipeOffset.value = 0
  circleEdgeSwipeSettleDuration.value = 0
  circleEdgeSwipeStart.value = {
    x: startX,
    y: startY,
    lastX: startX,
    lastAt: Date.now(),
    velocityX: 0,
    axis: 'pending'
  }
  prepareCircleRouteUnderlay()
}

function moveCircleEdgeSwipe(event) {
  const start = circleEdgeSwipeStart.value
  if (!start || !circleDetailVisible.value) return
  if (!['idle', 'dragging'].includes(circleDetailRouteMotion.value)) return

  const touch = getCircleTouchPoint(event)
  if (!touch) return
  const currentX = Number(touch.clientX ?? touch.pageX ?? 0)
  const currentY = Number(touch.clientY ?? touch.pageY ?? 0)
  const deltaX = currentX - start.x
  const deltaY = currentY - start.y

  if (start.axis === 'pending') {
    if (Math.max(Math.abs(deltaX), Math.abs(deltaY)) < CIRCLE_EDGE_SWIPE_LOCK_DISTANCE) return
    if (deltaX <= 0 || Math.abs(deltaY) > Math.abs(deltaX)) {
      abandonCircleEdgeSwipeTracking()
      return
    }
    if (Math.abs(deltaX) < Math.abs(deltaY) * 1.15) return
    start.axis = 'horizontal'
    circleDetailRouteMotion.value = 'dragging'
  }

  if (start.axis !== 'horizontal') return
  event?.preventDefault?.()

  const width = Math.max(1, Number(circleEdgeSwipeViewportWidth.value) || 1)
  const nextOffset = Math.min(width, Math.max(0, deltaX))
  const now = Date.now()
  const elapsed = Math.max(1, now - Number(start.lastAt ?? now))
  const instantaneousVelocity = (currentX - Number(start.lastX ?? currentX)) / elapsed
  start.velocityX = Number.isFinite(instantaneousVelocity)
    ? start.velocityX * 0.45 + instantaneousVelocity * 0.55
    : start.velocityX
  start.lastX = currentX
  start.lastAt = now
  circleEdgeSwipeOffset.value = nextOffset
}

function finishCircleEdgeSwipe(event) {
  const start = circleEdgeSwipeStart.value
  if (!start || !circleDetailVisible.value) return

  if (start.axis !== 'horizontal' || circleDetailRouteMotion.value !== 'dragging') {
    abandonCircleEdgeSwipeTracking()
    return
  }

  const touch = getCircleTouchPoint(event)
  if (touch) moveCircleEdgeSwipe(event)

  const width = Math.max(1, Number(circleEdgeSwipeViewportWidth.value) || 1)
  const offset = Math.max(0, Number(circleEdgeSwipeOffset.value) || 0)
  const velocityX = Math.max(0, Number(start.velocityX) || 0)
  const shouldFinish = offset / width >= CIRCLE_EDGE_SWIPE_FINISH_PROGRESS
    || (offset >= CIRCLE_EDGE_SWIPE_MIN_FLING_DISTANCE && velocityX >= CIRCLE_EDGE_SWIPE_FINISH_VELOCITY)

  if (shouldFinish) {
    circleDetailReturnScrollTop = circleOverviewScrollTop.value
    resetCircleTabbar()
    clearCircleScoreTooltip()
    startCircleEdgeSwipeSettle('drag-leaving', width)
    return
  }
  startCircleEdgeSwipeSettle('drag-cancelling', 0)
}

function cancelCircleEdgeSwipe() {
  if (circleDetailRouteMotion.value === 'dragging') {
    startCircleEdgeSwipeSettle('drag-cancelling', 0)
    return
  }
  if (circleEdgeSwipeStart.value) abandonCircleEdgeSwipeTracking()
}

function interruptCircleEdgeSwipe() {
  if (circleDetailRouteMotion.value === 'drag-leaving') {
    finishCircleDetailRouteLeave()
    return
  }
  if (!['dragging', 'drag-cancelling'].includes(circleDetailRouteMotion.value)) return
  clearCircleDetailRouteTimers()
  resetCircleEdgeSwipeState()
  circleDetailRouteMotion.value = 'idle'
  parkCircleRouteUnderlay()
}

function resetCircleTabbar() {
  circleTabCollapsed.value = false
  circleLastScrollTop.value = 0
}

function expandCircleTabbar() {
  circleTabCollapsed.value = false
}

function updateCircleTabbarOnScroll(scrollTop) {
  const currentScrollTop = Math.max(0, Number(scrollTop) || 0)
  const shouldTrackCircleScroll = activeTab.value === 'circle'
    && selectedCircleSection.value !== 'overview'
    && !selectedCirclePost.value
    && !selectedCommunityPost.value

  if (!shouldTrackCircleScroll || currentScrollTop <= 32) {
    circleTabCollapsed.value = false
    circleLastScrollTop.value = currentScrollTop
    return
  }

  const scrollDelta = currentScrollTop - circleLastScrollTop.value
  circleLastScrollTop.value = currentScrollTop

  if (scrollDelta > 8) {
    circleTabCollapsed.value = true
  } else if (scrollDelta < -8) {
    circleTabCollapsed.value = false
  }
}

function getCircleTrendHeight(count) {
  if (Number(count) <= 0) return '0%'
  const scaleMax = Math.max(1, Number(circleTrendScaleMax.value) || 1)
  const ratio = (Number(count) || 0) / scaleMax
  return `${Math.max(7, Math.round(ratio * 100))}%`
}

function getCircleScoreChartConfig(values = []) {
  const scores = values
    .map((value) => Number(value))
    .filter((value) => Number.isFinite(value))
  const min = scores.some((score) => score < 50) ? 0 : 50
  const max = scores.some((score) => score > 120)
    ? 150
    : scores.some((score) => score > 100)
      ? 120
      : 100
  const axis = min === 50 && max === 100
    ? [100, 90, 80, 70, 60, 50]
    : min === 50 && max === 120
      ? [120, 100, 80, 60, 50]
      : min === 50
        ? [150, 125, 100, 75, 50]
        : max === 100
          ? [100, 75, 50, 25, 0]
          : max === 120
            ? [120, 90, 60, 30, 0]
            : [150, 100, 50, 0]
  const chart = { min, max }

  return {
    ...chart,
    axis,
    gridY: axis.map((score) => getCircleScoreY(score, chart))
  }
}

function getCircleScoreY(score, chart = {}) {
  const min = Number(chart.min)
  const max = Number(chart.max)
  const safeMin = Number.isFinite(min) ? min : 0
  const safeMax = Number.isFinite(max) && max > safeMin ? max : 150
  const safeScore = Math.min(safeMax, Math.max(safeMin, Number(score) || safeMin))
  const top = 18
  const bottom = 90
  return top + ((safeMax - safeScore) / (safeMax - safeMin)) * (bottom - top)
}

function handleCircleScoreCardTap(record) {
  openCircleScoreLineRecord(record)
}

function startCircleScorePointHold(scope, index) {
  cancelCircleScorePointHold()
  if (scope === 'overview') {
    isCircleScoreSwiperPaused.value = true
  }
  circleScorePointHoldTimer = setTimeout(() => {
    circleScorePointHoldTimer = null
    showCircleScorePointTooltip(scope, index)
  }, 360)
}

function cancelCircleScorePointHold() {
  if (circleScorePointHoldTimer === null) return
  clearTimeout(circleScorePointHoldTimer)
  circleScorePointHoldTimer = null
  if (circleScoreTooltip.value.scope !== 'overview') {
    isCircleScoreSwiperPaused.value = false
  }
}

function finishCircleScorePointHold() {
  cancelCircleScorePointHold()
}

function showCircleScorePointTooltip(scope, index) {
  cancelCircleScorePointHold()
  if (!['overview', 'detail'].includes(scope) || !Number.isInteger(index)) return
  if (scope === 'overview') {
    isCircleScoreSwiperPaused.value = true
  }
  clearCircleScoreTooltipDismissTimer()
  circleScoreTooltip.value = { scope, index }
  circleScoreTooltipDismissTimer = setTimeout(() => {
    circleScoreTooltip.value = { scope: '', index: -1 }
    isCircleScoreSwiperPaused.value = false
    circleScoreTooltipDismissTimer = null
  }, 2600)
}

function clearCircleScoreTooltip() {
  cancelCircleScorePointHold()
  clearCircleScoreTooltipDismissTimer()
  isCircleScoreSwiperPaused.value = false
  circleScoreTooltip.value = { scope: '', index: -1 }
}

function clearCircleScoreTooltipDismissTimer() {
  if (circleScoreTooltipDismissTimer === null) return
  clearTimeout(circleScoreTooltipDismissTimer)
  circleScoreTooltipDismissTimer = null
}

function isCircleScorePointTooltipVisible(scope, index) {
  return circleScoreTooltip.value.scope === scope && circleScoreTooltip.value.index === index
}

function getCircleScoreTooltipStyle(x, score, chart) {
  const pointY = getCircleScoreY(score, chart)
  const tooltipY = pointY <= 32 ? pointY + 18 : pointY - 18
  const left = Math.min(86, Math.max(14, (Number(x) || 150) / 3))
  const top = Math.min(94, Math.max(6, (tooltipY / 112) * 100))

  return {
    left: `${left}%`,
    top: `${top}%`
  }
}

function getScoreLineValue(record, year) {
  return record?.scores?.[year] || { raw: '', score: null, kind: 'missing' }
}

function getScoreLineSchoolName(record) {
  return String(record?.schoolName || record?.school || '').trim()
}

function getScoreLineRecordDisplayName(record) {
  const schoolName = getScoreLineSchoolName(record)
  const unitName = String(record?.unitName || '').trim()
  return unitName ? `${schoolName} ${unitName}` : schoolName
}

function normalizeScoreLineSearch(value) {
  return String(value || '').trim().toLocaleLowerCase()
}

function getScoreLineAvailableYearCount(record) {
  return historicalScoreLineYears.filter((year) => Boolean(getScoreLineValue(record, year).raw)).length
}

function hasCompleteScoreLineTrend(record) {
  return historicalScoreLineYears.every((year) => getScoreLineValue(record, year).kind === 'score')
}

function getScoreLineCardValue(record, year) {
  const value = getScoreLineValue(record, year)
  if (value.kind === 'score') return `${value.score} 分`
  if (value.kind === 'unavailable') return '无划线'
  if (value.kind === 'official') return '官网公布'
  if (value.kind === 'multiple') return '多专业'
  if (value.kind === 'note') return '详见'
  return '--'
}

function getScoreLineDetailValue(record, year) {
  const value = getScoreLineValue(record, year)
  if (value.kind === 'score') return `总分 ${value.score} 分`
  if (value.kind === 'unavailable') return '无统一分数线'
  if (value.kind === 'official') return '以官网名单为准'
  if (value.kind === 'multiple') return '按专业/学位区分'
  if (value.kind === 'note') return '原始说明'
  return '暂无数据'
}

function rotateCircleScoreSchool() {
  if (circleScoreSchools.value.length < 2) return
  let nextIndex = circleScoreSchoolIndex.value
  while (nextIndex === circleScoreSchoolIndex.value) {
    nextIndex = Math.floor(Math.random() * circleScoreSchools.value.length)
  }
  circleScoreSchoolIndex.value = nextIndex
}

function handleCircleInsightChange(event) {
  const nextIndex = Number(event?.detail?.current)
  if (!Number.isInteger(nextIndex) || nextIndex === circleInsightIndex.value) return
  clearCircleScoreTooltip()
  circleInsightIndex.value = nextIndex
  if (nextIndex === 1) {
    rotateCircleScoreSchool()
  }
}

function selectCircleInsight(index) {
  if (index !== 0 && index !== 1) return
  if (circleInsightIndex.value === index) return
  clearCircleScoreTooltip()
  circleInsightIndex.value = index
  if (index === 1) {
    rotateCircleScoreSchool()
  }
}

function openCirclePost(post) {
  selectedCirclePost.value = post
}

function closeCirclePost() {
  selectedCirclePost.value = null
}

function selectExperienceCategory(category) {
  if (!circleExperienceCategories.includes(category)) return
  if (selectedExperienceCategory.value === category) return
  selectedExperienceCategory.value = category
  selectedCirclePost.value = null
  const sortBy = selectedCommunityPostSort.value
  void loadCircleCommunityPosts('experience', {
    force: false,
    featuredOnly: sortBy === 'featured',
    sortBy,
    search: communityAppliedSearch.experience
  })
}

function clearExperienceSearch() {
  experienceSearchKeyword.value = ''
  applyCommunitySearch('experience', '', { force: true })
}

function clearCommunitySearch() {
  communitySearchKeyword.value = ''
  applyCommunitySearch('chat', '', { force: true })
}

function clearActiveCommunitySearch() {
  if (selectedCircleCommunityTab.value === 'experience') {
    clearExperienceSearch()
    return
  }
  clearCommunitySearch()
}

function applyCommunitySearch(postType, value, { force = false } = {}) {
  const normalizedPostType = normalizeCircleCommunityPostType(postType)
  const keyword = String(value || '').trim()
  if (!force && communityAppliedSearch[normalizedPostType] === keyword) return
  communityAppliedSearch[normalizedPostType] = keyword
  const sortBy = selectedCommunityPostSort.value
  void loadCircleCommunityPosts(normalizedPostType, {
    force: true,
    featuredOnly: sortBy === 'featured',
    sortBy,
    search: keyword
  })
}

function scheduleActiveCommunitySearch(event) {
  const postType = normalizeCircleCommunityPostType(selectedCircleCommunityTab.value)
  const fallbackValue = postType === 'experience'
    ? experienceSearchKeyword.value
    : communitySearchKeyword.value
  const keyword = String(event?.detail?.value ?? fallbackValue)
  if (communitySearchDebounceTimer !== null) clearTimeout(communitySearchDebounceTimer)
  communitySearchDebounceTimer = setTimeout(() => {
    communitySearchDebounceTimer = null
    applyCommunitySearch(postType, keyword)
  }, 360)
}

function submitActiveCommunitySearch(event) {
  if (communitySearchDebounceTimer !== null) {
    clearTimeout(communitySearchDebounceTimer)
    communitySearchDebounceTimer = null
  }
  const postType = normalizeCircleCommunityPostType(selectedCircleCommunityTab.value)
  const fallbackValue = postType === 'experience'
    ? experienceSearchKeyword.value
    : communitySearchKeyword.value
  applyCommunitySearch(postType, event?.detail?.value ?? fallbackValue, { force: true })
}

function retryActiveCommunityFeed() {
  const postType = normalizeCircleCommunityPostType(selectedCircleCommunityTab.value)
  const sortBy = selectedCommunityPostSort.value
  void loadCircleCommunityPosts(postType, {
    force: true,
    featuredOnly: sortBy === 'featured',
    sortBy,
    search: communityAppliedSearch[postType]
  })
}

function selectCommunityPostSort(event) {
  const selectedIndex = Number(event?.detail?.value)
  const nextSort = communityPostSortOptions[selectedIndex]?.value
  if (!nextSort) return
  selectedCommunityPostSort.value = nextSort
  if (selectedCircleCommunityTab.value !== 'mentor') {
    const postType = normalizeCircleCommunityPostType(selectedCircleCommunityTab.value)
    void loadCircleCommunityPosts(selectedCircleCommunityTab.value, {
      force: false,
      featuredOnly: nextSort === 'featured',
      sortBy: nextSort,
      search: communityAppliedSearch[postType]
    })
  }
}

async function loadMentorProfiles({ force = false } = {}) {
  if (mentorProfilesLoading.value || (mentorProfilesLoaded.value && !force)) return

  mentorProfilesLoading.value = true
  mentorProfilesError.value = ''
  try {
    const payload = await fetchMentorProfiles({ limit: 100 })
    const profiles = normalizeMentorListResponse(payload)
    mentorProfiles.value = profiles
    mentorProfilesLoaded.value = true
    cacheMentors(profiles, { replace: true })
  } catch (error) {
    mentorProfilesError.value = error?.detail || '前辈资料加载失败'
  } finally {
    mentorProfilesLoading.value = false
  }
}

function retryMentorProfiles() {
  void loadMentorProfiles({ force: true })
}

function setMentorEntryStatus(status) {
  mentorEntryStatusLastConfirmedAt = Date.now()
  mentorEntryStatus.value = setMentorVerificationStatus(status)
  return mentorEntryStatus.value
}

function isMentorEntryStatusFresh() {
  return mentorEntryStatusLastConfirmedAt > 0
    && Date.now() - mentorEntryStatusLastConfirmedAt <= MENTOR_ENTRY_STATUS_FRESH_MS
}

function isCurrentMentorProfile(mentor) {
  return mentorEntryStatus.value === 'verified'
    && Boolean(currentMentorProfileId.value)
    && String(mentor?.id || '') === currentMentorProfileId.value
}

function loadMentorEntryStatus({ force = false } = {}) {
  if (!isLoggedIn()) {
    mentorEntryStatus.value = 'unverified'
    mentorEntryStatusLoaded.value = false
    currentMentorProfileId.value = ''
    mentorEntryStatusLastConfirmedAt = 0
    return Promise.resolve(mentorEntryStatus.value)
  }
  if (mentorEntryStatusRequest) return mentorEntryStatusRequest
  if (mentorEntryStatusLoaded.value && !force) return Promise.resolve(mentorEntryStatus.value)

  const cachedStatus = getMentorVerificationStatus()
  mentorEntryStatus.value = cachedStatus
  currentMentorProfileId.value = ''
  mentorEntryStatusRequest = (async () => {
    try {
      try {
        const profilePayload = await fetchMyMentorProfile()
        const mentorId = String(profilePayload?.mentor?.id || '').trim()
        if (mentorId) {
          currentMentorProfileId.value = mentorId
          return setMentorEntryStatus('verified')
        }
      } catch (error) {
        // 未绑定档案时接口返回 404，继续读取当前账号的认证申请状态。
        if (error?.statusCode && Number(error.statusCode) !== 404) throw error
      }

      const applicationPayload = await fetchMyMentorVerificationApplication()
      const applicationStatus = String(applicationPayload?.application?.application_status || '').trim().toLowerCase()
      if (applicationStatus === 'pending') return setMentorEntryStatus('pending')
      if (applicationStatus === 'approved') return setMentorEntryStatus('verified')
      if (applicationStatus === 'rejected') return setMentorEntryStatus('rejected')
      if (applicationStatus === 'revoked') return setMentorEntryStatus('revoked')
      return setMentorEntryStatus('unverified')
    } catch (error) {
      // 接口暂时不可用时保留已知状态，避免入口在页面回显时反复跳变。
      mentorEntryStatusLastConfirmedAt = 0
      mentorEntryStatus.value = cachedStatus
      return mentorEntryStatus.value
    } finally {
      mentorEntryStatusLoaded.value = true
    }
  })()

  return mentorEntryStatusRequest.finally(() => {
    mentorEntryStatusRequest = null
  })
}

async function loadMentorFavoriteIds({ silent = false } = {}) {
  if (!isLoggedIn()) {
    mentorFavoriteIds.value = getMentorFavoriteIds()
    return
  }
  try {
    const payload = await fetchMyMentorFavorites()
    const favoriteIds = Array.isArray(payload?.items)
      ? payload.items.map((item) => item?.mentor_id || item?.mentorId).filter(Boolean)
      : []
    mentorFavoriteIds.value = setMentorFavoriteIds(favoriteIds)
  } catch (error) {
    mentorFavoriteIds.value = getMentorFavoriteIds()
    if (!silent) uni.showToast({ title: error?.detail || '收藏状态加载失败', icon: 'none' })
  }
}

function selectMentorSort(event) {
  const selectedIndex = Number(event?.detail?.value)
  const nextSort = mentorSortOptions[selectedIndex]?.value
  if (!nextSort) return
  selectedMentorSort.value = nextSort
}

function openMentorFilterSheet() {
  mentorFilterDraft.value = { ...mentorFilters.value }
  clearMentorFilterMotionTimers()
  mentorFilterMounted.value = true
  mentorFilterClosing.value = false
  mentorFilterVisible.value = true
}

function closeMentorFilterSheet() {
  if (!mentorFilterMounted.value || mentorFilterClosing.value) return
  clearMentorFilterMotionTimers()
  mentorFilterVisible.value = false
  mentorFilterClosing.value = true
  mentorFilterCloseTimer = setTimeout(() => {
    mentorFilterMounted.value = false
    mentorFilterClosing.value = false
    mentorFilterCloseTimer = null
  }, 260)
}

function clearMentorFilterMotionTimers() {
  if (mentorFilterCloseTimer !== null) {
    clearTimeout(mentorFilterCloseTimer)
    mentorFilterCloseTimer = null
  }
}

function resetMentorFilters() {
  const emptyFilters = createDefaultMentorFilters()
  mentorFilters.value = { ...emptyFilters }
  mentorFilterDraft.value = { ...emptyFilters }
}

function applyMentorFilters() {
  mentorFilters.value = { ...mentorFilterDraft.value }
  closeMentorFilterSheet()
}

async function toggleMentorFavoriteState(mentorId) {
  const normalizedMentorId = String(mentorId || '')
  if (!normalizedMentorId || mentorFavoritePendingIds.value.includes(normalizedMentorId)) return
  if (!isLoggedIn()) {
    uni.showToast({ title: '请先登录后再收藏前辈', icon: 'none' })
    return
  }

  const previousFavoriteIds = [...mentorFavoriteIds.value]
  const nextFavoriteIds = previousFavoriteIds.includes(normalizedMentorId)
    ? previousFavoriteIds.filter((id) => id !== normalizedMentorId)
    : [...previousFavoriteIds, normalizedMentorId]
  mentorFavoriteIds.value = nextFavoriteIds
  mentorFavoritePendingIds.value = [...mentorFavoritePendingIds.value, normalizedMentorId]
  setTimeout(() => setMentorFavoriteIds(nextFavoriteIds), 80)

  try {
    const result = await toggleMentorFavoriteRequest(normalizedMentorId)
    const confirmedFavorite = Boolean(result?.is_favorited ?? result?.isFavorited)
    const confirmedIds = confirmedFavorite
      ? [...new Set([...mentorFavoriteIds.value, normalizedMentorId])]
      : mentorFavoriteIds.value.filter((id) => id !== normalizedMentorId)
    mentorFavoriteIds.value = confirmedIds
    setTimeout(() => setMentorFavoriteIds(confirmedIds), 80)
  } catch (error) {
    mentorFavoriteIds.value = previousFavoriteIds
    setTimeout(() => setMentorFavoriteIds(previousFavoriteIds), 80)
    uni.showToast({ title: error?.detail || '收藏操作失败，请稍后重试', icon: 'none' })
  } finally {
    mentorFavoritePendingIds.value = mentorFavoritePendingIds.value.filter((id) => id !== normalizedMentorId)
  }
}

function openMentorDetail(mentor) {
  if (!mentor?.id) return
  const currentMentorId = String(currentMentorProfileId.value || '').trim()
  const viewerMentorQuery = currentMentorId
    ? `&viewerMentorId=${encodeURIComponent(currentMentorId)}`
    : ''
  uni.navigateTo({ url: `/pages-sub-consultation/consultation/mentor-detail?id=${encodeURIComponent(mentor.id)}${viewerMentorQuery}` })
}

function beginMentorConsultation(mentor) {
  if (!mentor?.id) return
  if (isCurrentMentorProfile(mentor)) {
    openMentorDetail(mentor)
    return
  }
  const page = mentor.onlineStatus === 'online' ? 'mentor-consult-form' : 'mentor-booking'
  const suffix = page === 'mentor-consult-form' ? '&mode=instant' : ''
  uni.navigateTo({ url: `/pages-sub-consultation/consultation/${page}?mentorId=${encodeURIComponent(mentor.id)}${suffix}` })
}

function resetLandingPageScroll() {
  nextTick(() => {
    uni.pageScrollTo({
      scrollTop: 0,
      duration: 0
    })
  })
}

async function openMentorVerificationEntry(options = {}) {
  if (openingMentorVerificationEntry) return
  openingMentorVerificationEntry = true

  try {
    await loadMentorEntryStatus({ force: !isMentorEntryStatusFresh() })
    const verificationStatus = mentorEntryStatus.value
    const mode = verificationStatus === 'verified' ? 'center' : verificationStatus === 'pending' ? 'pending' : 'apply'
    const from = options?.from === 'experience-publish' ? '&from=experience-publish' : ''
    await new Promise((resolve) => {
      uni.navigateTo({
        url: `/pages-sub-consultation/consultation/mentor-apply?mode=${mode}${from}`,
        complete() {
          openingMentorVerificationEntry = false
          resolve()
        }
      })
    })
  } catch (error) {
    openingMentorVerificationEntry = false
    uni.showToast({ title: '认证入口打开失败，请稍后重试', icon: 'none' })
  }
}

function getMyConsultationEntryUrl(status = mentorEntryStatus.value) {
  return status === 'verified'
    ? '/pages-sub-consultation/consultation/mentor-apply?mode=center&from=profile-consultations'
    : '/pages-sub-consultation/consultation/my-consultations'
}

function openMyConsultationEntry() {
  if (openingMyConsultationEntry.value) return
  openingMyConsultationEntry.value = true
  const url = getMyConsultationEntryUrl()
  uni.navigateTo({
    url,
    complete() {
      openingMyConsultationEntry.value = false
    }
  })
  void loadMentorEntryStatus({ force: true })
}

function getCommunityPostTimestamp(post = {}) {
  const value = post.createdAt || post.created_at || post.publishedAt || post.published_at || ''
  const timestamp = Date.parse(value)
  return Number.isFinite(timestamp) ? timestamp : 0
}

function getCommunityPostHotScore(post = {}) {
  const stats = post.stats || {}
  const likes = Math.max(0, Number(stats.likes) || 0)
  const comments = Math.max(0, Number(stats.comments) || 0)
  const views = Math.max(0, Number(stats.views) || 0)
  return likes * 6 + comments * 8 + Math.min(views, 1000) * 0.08
}

function isCommunityPostFeatured(post = {}) {
  return Boolean(post.isFeatured ?? post.is_featured ?? post.featured)
}

function shuffleCommunityPosts(posts) {
  const shuffled = [...posts]
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1))
    const current = shuffled[index]
    shuffled[index] = shuffled[swapIndex]
    shuffled[swapIndex] = current
  }
  return shuffled
}

function sortCommunityPosts(posts, sort) {
  if (sort === 'featured') {
    // 精选顺序由服务端稳定返回，互动状态更新时不再随机换位。
    return posts.filter(isCommunityPostFeatured)
  }
  // “热门”由服务端按完整公开内容池的互动数据排序，避免只在当前最新帖里重排。
  if (sort === 'hot') return [...posts]
  return posts
    .map((post, index) => ({
      post,
      index,
      timestamp: getCommunityPostTimestamp(post),
      hotScore: getCommunityPostHotScore(post)
    }))
    .sort((left, right) => {
      if (sort === 'hot') {
        return right.hotScore - left.hotScore || right.timestamp - left.timestamp || left.index - right.index
      }
      return right.timestamp - left.timestamp || left.index - right.index
    })
    .map((item) => item.post)
}

function getExperienceCategory(post = {}) {
  const category = String(post.category || '').trim()
  if (getRawExperienceStages(post).includes('申请制')) return '申请制'
  if (circleExperienceExamCodes.includes(category)) return category

  const explicitCode = String(post.examCode || post.exam_code || '').toUpperCase()
  if (circleExperienceExamCodes.includes(explicitCode)) return explicitCode

  const text = `${post.title || ''} ${post.summary || ''}`.toUpperCase()
  if (category === 'Z002' || category === '数学基础' || text.includes('Z002')) return 'Z002'
  return 'Z001'
}

function getRawExperienceStages(post = {}) {
  const rawStages = Array.isArray(post.experienceStages)
    ? post.experienceStages
    : Array.isArray(post.experience_stages)
      ? post.experience_stages
      : []
  return [...new Set(rawStages.map((stage) => String(stage || '').trim()).filter(Boolean))]
}

function getExperienceStages(post = {}) {
  const rawStages = getRawExperienceStages(post)
  const stages = [...new Set(
    rawStages
      .filter((stage) => circleExperienceStages.includes(stage))
  )]
  if (stages.length) return stages

  const legacyCategory = String(post.category || '').trim()
  if (legacyCategory === '专业课') return ['初试']
  if (legacyCategory === '复试') return ['复试']
  return []
}

function getCommunityPostTags(post = {}) {
  if ((post.postType || post.post_type) !== 'experience') {
    const category = String(post.category || '').trim()
    return category ? [category] : []
  }

  const selectedStages = new Set(getExperienceStages(post))
  return [
    getExperienceCategory(post),
    ...circleExperienceStages.filter((stage) => selectedStages.has(stage))
  ].filter(Boolean)
}

function matchesExperienceFilter(post, filter) {
  if (!filter || filter === '全部') return true
  if (circleExperienceExamCodes.includes(filter)) return post.examCode === filter
  if (circleExperienceStages.includes(filter)) return (post.experienceStages || []).includes(filter)
  return false
}

function getCommunityChatCategory(post = {}) {
  const category = String(post.category || '')
  if (circleCommunitySubjectCategories.includes(category)) return category

  const text = `${post.title || ''} ${post.summary || ''} ${post.content || ''}`.toUpperCase()
  if (category === 'Z002' || text.includes('Z002') || /数学|微积分|导数|积分/.test(text)) return '数学基础'
  if (/英语|词汇|语法|短语/.test(text)) return '英语运用'
  if (/逻辑|论点|论据|推理/.test(text)) return '逻辑推理'
  return '中华文化'
}

function normalizeCommunityPost(post = {}) {
  const ownershipKnown = Object.prototype.hasOwnProperty.call(post, 'ownershipKnown')
    ? Boolean(post.ownershipKnown)
    : Object.prototype.hasOwnProperty.call(post, 'isMine')
      || Object.prototype.hasOwnProperty.call(post, 'is_mine')
  const stats = post.stats || {}
  const rawCommentPreviews = Array.isArray(post.commentPreviews)
    ? post.commentPreviews
    : Array.isArray(post.comment_previews)
      ? post.comment_previews
      : [post.commentPreview || post.comment_preview].filter(Boolean)
  const commentPreviews = rawCommentPreviews
    .slice(0, 3)
    .map((comment, index) => ({
      id: String(comment.id || `${post.id || 'post'}-preview-${index}`),
      author: String(comment.author || '研友'),
      text: String(comment.text || comment.content || '')
    }))
    .filter((comment) => comment.text)

  const postType = post.postType || post.post_type || 'chat'
  const experienceCategory = getExperienceCategory(post)
  const experienceStages = postType === 'experience' ? getExperienceStages(post) : []
  const category = postType === 'experience'
    ? experienceCategory
    : getCommunityChatCategory(post)

  return {
    ...post,
    id: String(post.id || ''),
    postType,
    examCode: postType === 'experience' ? experienceCategory : '',
    experienceStages,
    category,
    author: post.author || '研友',
    avatar: post.avatar || '研',
    avatarUrl: post.avatarUrl || post.avatar_url || '',
    publishTime: post.publishTime || post.publish_time || '刚刚',
    tone: post.tone || 'blue',
    title: post.title || '',
    summary: String(post.summary || post.content || '').slice(0, 320),
    content: post.content || post.summary || '',
    media: Array.isArray(post.media) ? post.media.slice(0, 9) : [],
    mediaCount: Math.max(
      Array.isArray(post.media) ? post.media.length : 0,
      Number(post.mediaCount ?? post.media_count ?? 0)
    ),
    commentPreviews,
    commentPreview: commentPreviews[0] || null,
    isFeatured: isCommunityPostFeatured(post),
    liked: Boolean(post.liked || post.is_liked),
    isMine: Boolean(post.isMine || post.is_mine),
    ownershipKnown,
    authorVerified: Boolean(post.authorVerified || post.author_verified),
    isPublished: Boolean(post.isPublished ?? post.is_published ?? true),
    reviewStatus: String(post.reviewStatus || post.review_status || 'approved'),
    stats: {
      likes: Number(stats.likes ?? post.like_count ?? 0),
      comments: Number(stats.comments ?? post.comment_count ?? 0),
      views: Number(stats.views ?? post.view_count ?? 0)
    }
  }
}

function normalizeCommunityComment(comment = {}) {
  return {
    id: String(comment.id || `comment-${Date.now()}`),
    author: comment.author || '研友',
    avatar: comment.avatar || '研',
    avatarUrl: comment.avatarUrl || comment.avatar_url || '',
    content: comment.content || '',
    createdAt: comment.createdAt || comment.created_at || new Date().toISOString(),
    isMine: Boolean(comment.isMine || comment.is_mine),
    liked: Boolean(comment.liked || comment.is_liked),
    likeCount: Number(comment.likeCount ?? comment.like_count ?? 0),
    deliveryStatus: comment.deliveryStatus || '',
    clientRequestId: comment.clientRequestId || comment.client_request_id || '',
    optimisticCounted: Boolean(comment.optimisticCounted),
    errorMessage: comment.errorMessage || ''
  }
}

function patchCommunityPost(postId, patch, { persist = true } = {}) {
  if (!postId) return
  const applyPatch = (post) => ({
    ...post,
    ...patch,
    stats: {
      ...post.stats,
      ...(patch.stats || {})
    }
  })
  if (selectedCommunityPost.value?.id === postId) {
    selectedCommunityPost.value = applyPatch(selectedCommunityPost.value)
  }
  if (selectedCommunityCommentsPost.value?.id === postId) {
    selectedCommunityCommentsPost.value = applyPatch(selectedCommunityCommentsPost.value)
  }

  const patchList = (listRef) => {
    const index = listRef.value.findIndex((post) => post.id === postId)
    if (index < 0) return
    const nextList = [...listRef.value]
    nextList[index] = applyPatch(nextList[index])
    listRef.value = nextList
  }
  const communityPostLists = [
    circleCommunityPosts,
    circleFeaturedCommunityPosts,
    circleHotCommunityPosts,
    circleExperienceCommunityPosts,
    circleFeaturedExperiencePosts,
    circleHotExperienceCommunityPosts
  ]
  communityPostLists.forEach(patchList)
  Object.keys(communityFeedPages).forEach((pageKey) => {
    const posts = communityFeedPages[pageKey]
    if (!Array.isArray(posts)) return
    const index = posts.findIndex((post) => post.id === postId)
    if (index < 0) return
    const nextPosts = [...posts]
    nextPosts[index] = applyPatch(nextPosts[index])
    communityFeedPages[pageKey] = nextPosts
  })

  if (persist) {
    scheduleCircleCommunityFeedPersist('chat')
    scheduleCircleCommunityFeedPersist('experience')
  }
}

function toCommunityFeedCachePost(post = {}) {
  const normalized = normalizeCommunityPost(post)
  return {
    id: normalized.id,
    postType: normalized.postType,
    category: normalized.category,
    examCode: normalized.examCode,
    experienceStages: normalized.experienceStages,
    author: normalized.author,
    avatar: normalized.avatar,
    avatarUrl: normalized.avatarUrl,
    publishTime: normalized.publishTime,
    tone: normalized.tone,
    title: normalized.title,
    summary: normalized.summary,
    content: '',
    media: normalized.media.slice(0, 2).map((media = {}) => ({
      kicker: media.kicker || '',
      title: media.title || '',
      copy: media.copy || '',
      tone: media.tone || 'sky',
      imageUrl: media.imageUrl || media.image_url || '',
      thumbnailUrl: media.thumbnailUrl || media.thumbnail_url || ''
    })),
    mediaCount: normalized.mediaCount,
    commentPreviews: normalized.commentPreviews,
    isFeatured: normalized.isFeatured,
    liked: normalized.liked,
    isMine: normalized.isMine,
    ownershipKnown: normalized.ownershipKnown,
    authorVerified: normalized.authorVerified,
    stats: normalized.stats
  }
}

function patchCommunityCommentLike(commentId, patch) {
  if (!commentId) return
  communityComments.value = communityComments.value.map((comment) => (
    comment.id === commentId
      ? { ...comment, ...patch }
      : comment
  ))
}

function normalizeCircleCommunityPostType(postType) {
  return postType === 'experience' ? 'experience' : 'chat'
}

function getCircleCommunityFeedStorageKey(postType) {
  const viewerId = String(authUser.value?.id || 'guest').trim() || 'guest'
  return `${COMMUNITY_FEED_CACHE_PREFIX}:${viewerId}:${normalizeCircleCommunityPostType(postType)}`
}

function getCircleCommunityFeedPageKey(postType, { featuredOnly = false, sortBy = 'latest', category = '', search = '' } = {}) {
  const normalizedType = normalizeCircleCommunityPostType(postType)
  const normalizedCategory = String(category || '').trim()
  const normalizedSearch = String(search || '').trim().toLowerCase()
  return `${normalizedType}:${featuredOnly ? 'featured' : (sortBy === 'hot' ? 'hot' : 'latest')}:${normalizedCategory || 'all'}:${encodeURIComponent(normalizedSearch) || 'none'}`
}

function resetCircleCommunityFeedPagination(postType, { featuredOnly = false, sortBy = 'latest', category = '', search = '' } = {}) {
  const key = getCircleCommunityFeedPageKey(postType, { featuredOnly, sortBy, category, search })
  communityFeedNextCursors[key] = ''
  communityFeedHasMore[key] = true
  return key
}

function getCircleCommunityFeedRefreshKey(postType) {
  return `circle-community-feed-refresh-${normalizeCircleCommunityPostType(postType)}`
}

function consumeCircleCommunityFeedRefresh(postType) {
  const storageKey = getCircleCommunityFeedRefreshKey(postType)
  try {
    const refreshRequestedAt = Number(uni.getStorageSync(storageKey) || 0)
    if (!refreshRequestedAt) return false
    uni.removeStorageSync(storageKey)
    return true
  } catch (error) {
    return false
  }
}

function getCircleCommunityFeedPosts(postType, { featuredOnly = false, sortBy = 'latest', category = '', search = '' } = {}) {
  const pageKey = getCircleCommunityFeedPageKey(postType, { featuredOnly, sortBy, category, search })
  if (Array.isArray(communityFeedPages[pageKey])) return communityFeedPages[pageKey]
  if (normalizeCircleCommunityPostType(postType) === 'experience') {
    if (featuredOnly) return circleFeaturedExperiencePosts.value
    return sortBy === 'hot' ? circleHotExperienceCommunityPosts.value : circleExperienceCommunityPosts.value
  }
  if (featuredOnly) return circleFeaturedCommunityPosts.value
  return sortBy === 'hot' ? circleHotCommunityPosts.value : circleCommunityPosts.value
}

function setCircleCommunityFeedPosts(postType, posts, { persist = true, featuredOnly = false, sortBy = 'latest', category = '', search = '', append = false } = {}) {
  const normalizedPostType = normalizeCircleCommunityPostType(postType)
  const pageKey = getCircleCommunityFeedPageKey(normalizedPostType, { featuredOnly, sortBy, category, search })
  const incomingPosts = Array.isArray(posts) ? posts : []
  const currentPosts = getCircleCommunityFeedPosts(normalizedPostType, { featuredOnly, sortBy, category, search })
  const nextPosts = append
    ? [...currentPosts, ...incomingPosts.filter((item) => !currentPosts.some((existing) => existing.id === item.id))]
    : incomingPosts
  communityFeedPages[pageKey] = nextPosts
  if (!append && communityFeedNextCursors[pageKey] === undefined) {
    communityFeedNextCursors[pageKey] = ''
  }
  if (normalizedPostType === 'experience') {
    if (featuredOnly) {
      circleFeaturedExperiencePosts.value = nextPosts
    } else if (sortBy === 'hot') {
      circleHotExperienceCommunityPosts.value = nextPosts
    } else {
      circleExperienceCommunityPosts.value = nextPosts
    }
  } else if (featuredOnly) {
    circleFeaturedCommunityPosts.value = nextPosts
  } else if (sortBy === 'hot') {
    circleHotCommunityPosts.value = nextPosts
  } else {
    circleCommunityPosts.value = nextPosts
  }
  if (persist && !category && !search && !featuredOnly && sortBy === 'latest') {
    persistCircleCommunityFeed(normalizedPostType)
  }
}

function persistCircleCommunityFeed(postType) {
  const storageKey = getCircleCommunityFeedStorageKey(postType)
  try {
    uni.setStorageSync(storageKey, {
      cachedAt: Date.now(),
      posts: getCircleCommunityFeedPosts(postType).map((post) => toCommunityFeedCachePost(post)),
      nextCursor: communityFeedNextCursors[getCircleCommunityFeedPageKey(postType)] || '',
      hasMore: communityFeedHasMore[getCircleCommunityFeedPageKey(postType)] !== false
    })
    communityFeedCacheHydratedKeys.add(storageKey)
    communityFeedCacheFreshness.set(storageKey, Date.now())
  } catch (error) {
    // 缓存不可用时继续使用网络数据，不影响社区浏览。
  }
}

function consumeCommunityPostEditResult() {
  let storedResult = null
  try {
    storedResult = uni.getStorageSync(COMMUNITY_POST_EDIT_RESULT_KEY)
    if (storedResult) uni.removeStorageSync(COMMUNITY_POST_EDIT_RESULT_KEY)
  } catch (error) {
    return false
  }

  const editedPost = normalizeCommunityPost(storedResult?.post || {})
  if (!editedPost.id) return false

  const isSelectedPost = selectedCommunityPost.value?.id === editedPost.id
  const keepOwnerPreview = isSelectedPost && communityReaderOwnerPreview.value
  const editedContentPatch = { ...editedPost }
  delete editedContentPatch.liked
  delete editedContentPatch.stats
  delete editedContentPatch.commentPreviews
  delete editedContentPatch.commentPreview
  patchCommunityPost(editedPost.id, editedContentPatch)

  if (isSelectedPost) {
    const interactionsEnabled = editedPost.isPublished && editedPost.reviewStatus === 'approved'
    communityReaderOwnerPreview.value = keepOwnerPreview || !interactionsEnabled
    communityReaderOwnerLoading.value = false
    communityReaderInteractionsEnabled.value = interactionsEnabled
    if (!interactionsEnabled) {
      resetCommunityCommentEntry({ hideKeyboard: true })
      closeCommunityComments()
    }
  }
  if (editedPost.postType === 'experience' && (!editedPost.isPublished || editedPost.reviewStatus !== 'approved')) {
    removeCommunityPostFromFeeds(editedPost.id)
  }
  return true
}

function scheduleCircleCommunityFeedPersist(postType) {
  pendingCommunityFeedPersistTypes.add(normalizeCircleCommunityPostType(postType))
  if (communityFeedPersistTimerId !== null) return
  communityFeedPersistTimerId = setTimeout(() => {
    communityFeedPersistTimerId = null
    const postTypes = [...pendingCommunityFeedPersistTypes]
    pendingCommunityFeedPersistTypes.clear()
    postTypes.forEach((type) => persistCircleCommunityFeed(type))
  }, 160)
}

function flushScheduledCircleCommunityFeedPersist() {
  if (communityFeedPersistTimerId !== null) {
    clearTimeout(communityFeedPersistTimerId)
    communityFeedPersistTimerId = null
  }
  const postTypes = [...pendingCommunityFeedPersistTypes]
  pendingCommunityFeedPersistTypes.clear()
  postTypes.forEach((type) => persistCircleCommunityFeed(type))
}

function hydrateCircleCommunityFeed(postType) {
  const normalizedPostType = normalizeCircleCommunityPostType(postType)
  const storageKey = getCircleCommunityFeedStorageKey(normalizedPostType)
  if (communityFeedCacheHydratedKeys.has(storageKey)) {
    return Date.now() - Number(communityFeedCacheFreshness.get(storageKey) || 0) <= COMMUNITY_FEED_CACHE_TTL
  }
  communityFeedCacheHydratedKeys.add(storageKey)

  try {
    const cached = uni.getStorageSync(storageKey)
    if (!cached || !Array.isArray(cached.posts)) {
      communityFeedCacheFreshness.set(storageKey, 0)
      return false
    }
    const posts = cached.posts.map((post) => normalizeCommunityPost(post))
    setCircleCommunityFeedPosts(normalizedPostType, posts, { persist: false })
    const pageKey = getCircleCommunityFeedPageKey(normalizedPostType)
    communityFeedNextCursors[pageKey] = String(cached.nextCursor || '')
    communityFeedHasMore[pageKey] = cached.hasMore !== false
    const cachedAt = Number(cached.cachedAt || 0)
    communityFeedCacheFreshness.set(storageKey, cachedAt)
    communityFeedPageFreshness.set(pageKey, cachedAt)
    return Date.now() - cachedAt <= COMMUNITY_FEED_CACHE_TTL
  } catch (error) {
    communityFeedCacheFreshness.set(storageKey, 0)
    return false
  }
}

function warmCircleCommunityFeeds() {
  if (communityFeedPrefetchStarted) return
  communityFeedPrefetchStarted = true

  const chatCacheFresh = hydrateCircleCommunityFeed('chat')
  const experienceCacheFresh = hydrateCircleCommunityFeed('experience')

  if (!chatCacheFresh) {
    setTimeout(() => {
      void loadCircleCommunityPosts('chat')
    }, 0)
  }
  if (!experienceCacheFresh) {
    setTimeout(() => {
      void loadCircleCommunityPosts('experience')
    }, chatCacheFresh ? 80 : 220)
  }
}

async function loadCircleCommunityPosts(postType = 'chat', { force = false, featuredOnly = false, sortBy = 'latest', search } = {}) {
  const normalizedPostType = normalizeCircleCommunityPostType(postType)
  const normalizedSort = sortBy === 'hot' ? 'hot' : 'latest'
  const normalizedSearch = String(search ?? communityAppliedSearch[normalizedPostType] ?? '').trim()
  const selectedCategory = normalizedPostType === 'experience' ? selectedExperienceCategory.value : selectedCommunityCategory.value
  const normalizedExperienceStage = normalizedPostType === 'experience' && circleExperienceStages.includes(selectedCategory)
    ? selectedCategory
    : ''
  const normalizedCategory = selectedCategory && selectedCategory !== '全部' && !normalizedExperienceStage
    ? selectedCategory
    : ''
  const activeFilter = normalizedCategory || normalizedExperienceStage
  const pageKey = getCircleCommunityFeedPageKey(normalizedPostType, {
    featuredOnly,
    sortBy: normalizedSort,
    category: activeFilter,
    search: normalizedSearch
  })
  const cacheIsFresh = featuredOnly || normalizedSort !== 'latest' || activeFilter || normalizedSearch
    ? false
    : hydrateCircleCommunityFeed(normalizedPostType)
  const pageIsFresh = Array.isArray(communityFeedPages[pageKey])
    && Date.now() - Number(communityFeedPageFreshness.get(pageKey) || 0) <= COMMUNITY_FEED_CACHE_TTL
  if (!force && !communityFeedNextCursors[pageKey] && pageIsFresh) return
  if (!featuredOnly && normalizedSort === 'latest' && cacheIsFresh && !force) return
  if (force) resetCircleCommunityFeedPagination(normalizedPostType, {
    featuredOnly,
    sortBy: normalizedSort,
    category: activeFilter,
    search: normalizedSearch
  })
  const requestKey = pageKey
  if (communityPostsLoadingTypes.has(requestKey)) return
  communityPostsLoadingTypes.add(requestKey)
  communityPostsLoading.value = true
  communityFeedLoadingState[requestKey] = true
  communityFeedErrors[requestKey] = ''
  try {
    const response = await fetchCommunityPosts({
      limit: COMMUNITY_FEED_PAGE_SIZE,
      post_type: normalizedPostType,
      featured_only: featuredOnly,
      sort_by: normalizedSort,
      category: normalizedCategory || undefined,
      experience_stage: normalizedExperienceStage || undefined,
      search: normalizedSearch || undefined,
      cursor: communityFeedNextCursors[pageKey] || undefined
    })
    if (Array.isArray(response?.items)) {
      const posts = response.items.map((post) => normalizeCommunityPost(post))
      setCircleCommunityFeedPosts(normalizedPostType, posts, {
        persist: !activeFilter && !featuredOnly && normalizedSort === 'latest',
        featuredOnly,
        sortBy: normalizedSort,
        category: activeFilter,
        search: normalizedSearch,
        append: Boolean(communityFeedNextCursors[pageKey])
      })
      communityFeedNextCursors[pageKey] = String(response?.next_cursor || '')
      communityFeedHasMore[pageKey] = response?.has_more === true
      communityFeedPageFreshness.set(pageKey, Date.now())
      if (!activeFilter && !normalizedSearch && !featuredOnly && normalizedSort === 'latest') persistCircleCommunityFeed(normalizedPostType)
    }
  } catch (error) {
    communityFeedErrors[requestKey] = getSafeError(error, '帖子加载失败，请检查网络后重试')
  } finally {
    communityPostsLoadingTypes.delete(requestKey)
    communityFeedLoadingState[requestKey] = false
    communityPostsLoading.value = communityPostsLoadingTypes.size > 0
  }
}

async function openCommunityPost(post, options = {}) {
  const initialPost = normalizeCommunityPost(post)
  if (!initialPost.id) return
  clearCommunityReaderRouteTimers()
  markCommunityPostNotificationsRead(initialPost)
  clearCommunityViewTimer()
  clearCommunityLikeBurst()
  closeCommunityComments()
  communityReaderScrollTarget.value = ''
  communityReaderMediaIndex.value = 0
  communityCommentEntryReady.value = false
  communityCommentInputFocused.value = false
  communityReaderTopZoneLastTapAt = 0
  communityReaderLastScrollTop = 0
  communityReaderOwnerPreview.value = options.ownerPreview === true
  communityReaderInteractionsEnabled.value = options.interactionsEnabled !== false
  selectedCommunityPost.value = initialPost
  showCommunityReaderWithTransition()
  if (communityReaderInteractionsEnabled.value) {
    scheduleCommunityView(initialPost.id)
    void openCommunityComments(initialPost)
  }
  nextTick(() => {
    captureCommunityReaderViewportBaseHeight(true)
    bindCommunityCommentVisualViewport()
    scheduleCommunityCommentVisibilityCheck(80)
  })

  if (options.focusComments) {
    await nextTick()
    focusCommunityReaderComments()
  }
}

async function openOwnedCommunityPostFromRoute(postId, requestedCommunityTab = '') {
  const normalizedPostId = String(postId || '').trim()
  if (!normalizedPostId) return
  communityReaderOwnerLoading.value = true
  await openCommunityPost({
    id: normalizedPostId,
    post_type: requestedCommunityTab === 'experience' ? 'experience' : 'chat',
    author: '我',
    title: '正在加载帖子...',
    content: '',
    is_mine: true,
    is_published: false,
    ownershipKnown: true
  }, {
    ownerPreview: true,
    interactionsEnabled: false
  })

  try {
    const response = await fetchMyCommunityPost(normalizedPostId)
    if (selectedCommunityPost.value?.id !== normalizedPostId) return
    const ownedPost = normalizeCommunityPost(response?.post || {})
    if (!ownedPost.id) throw { detail: '帖子内容不存在' }
    selectedCommunityPost.value = ownedPost
    communityReaderOwnerLoading.value = false
    communityReaderInteractionsEnabled.value = ownedPost.isPublished && ownedPost.reviewStatus === 'approved'
    if (communityReaderInteractionsEnabled.value) {
      void openCommunityComments(ownedPost)
    }
  } catch (error) {
    if (selectedCommunityPost.value?.id !== normalizedPostId) return
    communityReaderOwnerLoading.value = false
    uni.showToast({ title: getSafeError(error, '帖子内容读取失败，请稍后重试'), icon: 'none' })
    returnToMyPostsFromCommunityReader()
  }
}

function openCommunityPostComments(post) {
  void openCommunityPost(post, { focusComments: true })
}

function scrollCommunityReaderTo(targetId) {
  const postId = selectedCommunityPost.value?.id
  if (!postId || !targetId) return

  communityReaderScrollTarget.value = ''
  nextTick(() => {
    if (selectedCommunityPost.value?.id === postId) {
      communityReaderScrollTarget.value = targetId
    }
  })
}

function focusCommunityReaderComments() {
  const post = selectedCommunityPost.value
  if (!post?.id) return

  if (selectedCommunityCommentsPost.value?.id !== post.id) {
    void openCommunityComments(post)
  }

  scrollCommunityReaderTo('community-reader-comments')
  scheduleCommunityCommentVisibilityCheck(360)
}

function getCommunityCommentViewportMetrics() {
  let layoutHeight = 0
  try {
    layoutHeight = Math.max(0, Number(uni.getWindowInfo?.()?.windowHeight || 0))
  } catch (error) {
    // 少数旧端不支持 getWindowInfo，继续使用浏览器视口或键盘高度兜底。
  }

  let visualBottom = layoutHeight
  if (typeof window !== 'undefined') {
    const browserHeight = Math.max(
      0,
      Number(window.innerHeight || window.document?.documentElement?.clientHeight || 0)
    )
    if (browserHeight > 0) layoutHeight = browserHeight

    const viewport = window.visualViewport
    const viewportHeight = Math.max(0, Number(viewport?.height || 0))
    if (viewport && viewportHeight > 0) {
      visualBottom = Math.max(0, Number(viewport.offsetTop || 0) + viewportHeight)
    } else {
      visualBottom = layoutHeight
    }
  }

  return {
    layoutHeight,
    visualBottom: visualBottom > 0 ? visualBottom : layoutHeight
  }
}

function captureCommunityReaderViewportBaseHeight(force = false) {
  const metrics = getCommunityCommentViewportMetrics()
  const candidate = Math.max(metrics.layoutHeight, metrics.visualBottom)
  if (candidate <= 0) return

  if (force || communityReaderViewportBaseHeight <= 0) {
    communityReaderViewportBaseHeight = candidate
    return
  }

  if (
    !communityCommentInputFocused.value
    && communityCommentKeyboardHeight <= 0
    && communityCommentKeyboardOffset.value <= 0
  ) {
    communityReaderViewportBaseHeight = candidate
    return
  }

  communityReaderViewportBaseHeight = Math.max(communityReaderViewportBaseHeight, candidate)
}

function normalizeCommunityCommentKeyboardDuration(duration) {
  const numericDuration = Number(duration)
  if (!Number.isFinite(numericDuration) || numericDuration <= 0) return 180
  const durationMs = numericDuration <= 10 ? numericDuration * 1000 : numericDuration
  return Math.min(600, Math.max(80, Math.round(durationMs)))
}

function clearCommunityCommentKeyboardSyncTimer() {
  if (communityCommentKeyboardSyncTimer === null) return
  clearTimeout(communityCommentKeyboardSyncTimer)
  communityCommentKeyboardSyncTimer = null
}

function clearCommunityCommentKeyboardResetTimer() {
  if (communityCommentKeyboardResetTimer === null) return
  clearTimeout(communityCommentKeyboardResetTimer)
  communityCommentKeyboardResetTimer = null
}

function syncCommunityCommentKeyboardOffset() {
  const syncRevision = ++communityCommentKeyboardSyncRevision
  const postId = selectedCommunityPost.value?.id
  if (!postId) {
    communityCommentKeyboardOffset.value = 0
    communityCommentKeyboardVisible.value = false
    return
  }

  const metrics = getCommunityCommentViewportMetrics()
  if (communityReaderViewportBaseHeight <= 0) {
    captureCommunityReaderViewportBaseHeight(true)
  }
  const baseHeight = Math.max(
    communityReaderViewportBaseHeight,
    metrics.layoutHeight,
    metrics.visualBottom
  )
  if (baseHeight <= 0) return

  let visibleBottom = communityCommentKeyboardHeight > 0
    ? Math.max(0, baseHeight - communityCommentKeyboardHeight)
    : baseHeight
  const visualViewportReduced = metrics.visualBottom > 0 && metrics.visualBottom < baseHeight - 1
  const layoutViewportReduced = metrics.layoutHeight > 0 && metrics.layoutHeight < baseHeight - 1
  if (visualViewportReduced) visibleBottom = Math.min(visibleBottom, metrics.visualBottom)
  if (layoutViewportReduced) visibleBottom = Math.min(visibleBottom, metrics.layoutHeight)

  const viewportCoveredHeight = Math.max(0, baseHeight - visibleBottom)
  communityCommentKeyboardVisible.value = communityCommentKeyboardHeight > 0 || viewportCoveredHeight > 80

  const currentOffset = Math.max(0, Number(communityCommentKeyboardOffset.value) || 0)
  const query = uni.createSelectorQuery()
  query.select('.community-reader-actions').boundingClientRect()
  query.exec((rects) => {
    if (
      selectedCommunityPost.value?.id !== postId
      || communityCommentKeyboardSyncRevision !== syncRevision
    ) return
    const actionsRect = rects?.[0]
    const unshiftedBottom = actionsRect
      ? Number(actionsRect.bottom || 0) + currentOffset
      : baseHeight
    const nextOffset = Math.min(
      baseHeight,
      Math.max(0, Math.round(unshiftedBottom - visibleBottom))
    )
    communityCommentKeyboardOffset.value = nextOffset > 1 ? nextOffset : 0
  })
}

function scheduleCommunityCommentKeyboardSync(delay = 0) {
  clearCommunityCommentKeyboardSyncTimer()
  communityCommentKeyboardSyncTimer = setTimeout(() => {
    communityCommentKeyboardSyncTimer = null
    syncCommunityCommentKeyboardOffset()
  }, Math.max(0, Number(delay) || 0))
}

function scheduleCommunityCommentKeyboardReset(delay = 360) {
  clearCommunityCommentKeyboardResetTimer()
  communityCommentKeyboardResetTimer = setTimeout(() => {
    communityCommentKeyboardResetTimer = null
    if (communityCommentInputFocused.value) return
    communityCommentKeyboardHeight = 0
    communityCommentKeyboardTransitionMs.value = 180
    syncCommunityCommentKeyboardOffset()
  }, Math.max(0, Number(delay) || 0))
}

function handleCommunityCommentVisualViewportChange() {
  if (!selectedCommunityPost.value?.id) return
  captureCommunityReaderViewportBaseHeight()
  scheduleCommunityCommentKeyboardSync(16)
}

function bindCommunityCommentVisualViewport() {
  const viewport = typeof window !== 'undefined' ? window.visualViewport : null
  if (
    communityCommentVisualViewportBound
    || !viewport
    || typeof viewport.addEventListener !== 'function'
  ) return

  viewport.addEventListener('resize', handleCommunityCommentVisualViewportChange)
  viewport.addEventListener('scroll', handleCommunityCommentVisualViewportChange)
  communityCommentVisualViewportBound = true
}

function unbindCommunityCommentVisualViewport() {
  const viewport = typeof window !== 'undefined' ? window.visualViewport : null
  if (!communityCommentVisualViewportBound) return

  if (viewport && typeof viewport.removeEventListener === 'function') {
    viewport.removeEventListener('resize', handleCommunityCommentVisualViewportChange)
    viewport.removeEventListener('scroll', handleCommunityCommentVisualViewportChange)
  }
  communityCommentVisualViewportBound = false
}

function resetCommunityCommentKeyboardState() {
  clearCommunityCommentKeyboardSyncTimer()
  clearCommunityCommentKeyboardResetTimer()
  communityCommentKeyboardSyncRevision += 1
  communityCommentKeyboardHeight = 0
  communityReaderViewportBaseHeight = 0
  communityCommentKeyboardOffset.value = 0
  communityCommentKeyboardVisible.value = false
  communityCommentKeyboardTransitionMs.value = 180
}

function handleCommunityCommentKeyboardHeightChange(event) {
  const keyboardHeight = Number(event?.detail?.height)
  if (!Number.isFinite(keyboardHeight)) return

  clearCommunityCommentKeyboardResetTimer()
  communityCommentKeyboardHeight = Math.max(0, keyboardHeight)
  communityCommentKeyboardTransitionMs.value = normalizeCommunityCommentKeyboardDuration(event?.detail?.duration)
  nextTick(syncCommunityCommentKeyboardOffset)
  scheduleCommunityCommentKeyboardSync(communityCommentKeyboardTransitionMs.value + 40)
}

function hideCommunityCommentKeyboard() {
  communityCommentInputFocused.value = false
  if (typeof uni.hideKeyboard === 'function') {
    uni.hideKeyboard()
  }
  if (communityCommentKeyboardVisible.value || communityCommentKeyboardHeight > 0) {
    scheduleCommunityCommentKeyboardReset()
  }
}

function clearCommunityCommentVisibilityTimer() {
  if (communityCommentVisibilityTimer === null) return
  clearTimeout(communityCommentVisibilityTimer)
  communityCommentVisibilityTimer = null
}

function resetCommunityCommentEntry(options = {}) {
  clearCommunityCommentVisibilityTimer()
  communityCommentEntryReady.value = false
  communityCommentInputFocused.value = false
  communityCommentInputFocusStartedAt = 0
  if (options.hideKeyboard === true) hideCommunityCommentKeyboard()
}

function isCommunityReaderCommentsInView() {
  return new Promise((resolve) => {
    const query = uni.createSelectorQuery()
    query.select('.community-reader-scroll').boundingClientRect()
    query.select('#community-reader-comments').boundingClientRect()
    query.exec((rects) => {
      const viewport = rects?.[0]
      const comments = rects?.[1]
      if (!viewport || !comments) {
        resolve(false)
        return
      }

      const viewportTop = Number(viewport.top || 0)
      const viewportHeight = Math.max(0, Number(viewport.height || 0))
      const activationLine = viewportTop + Math.min(96, Math.max(48, viewportHeight * 0.16))
      resolve(
        Number(comments.top || 0) <= activationLine
        && Number(comments.bottom || 0) > activationLine
      )
    })
  })
}

function scheduleCommunityCommentVisibilityCheck(delay = 120) {
  clearCommunityCommentVisibilityTimer()
  const postId = selectedCommunityPost.value?.id
  if (!postId) return

  communityCommentVisibilityTimer = setTimeout(async () => {
    communityCommentVisibilityTimer = null
    const commentsInView = await isCommunityReaderCommentsInView()
    if (
      selectedCommunityPost.value?.id === postId
      && !communityCommentInputFocused.value
    ) {
      communityCommentEntryReady.value = commentsInView
    }
  }, Math.max(0, Number(delay) || 0))
}

function handleCommunityCommentEntryTap() {
  if (!selectedCommunityPost.value?.id || communityCommentSubmitting.value) return

  if (communityCommentEntryReady.value) {
    communityCommentInputFocused.value = true
    return
  }

  hideCommunityCommentKeyboard()
  focusCommunityReaderComments()
}

function handleCommunityCommentInputFocus() {
  communityCommentInputFocused.value = true
  communityCommentInputFocusStartedAt = Date.now()
  clearCommunityCommentKeyboardResetTimer()
  bindCommunityCommentVisualViewport()
  captureCommunityReaderViewportBaseHeight()
  scheduleCommunityCommentKeyboardSync()
}

function handleCommunityCommentInputBlur() {
  communityCommentInputFocused.value = false
  communityCommentInputFocusStartedAt = 0
  communityCommentEntryReady.value = false
  scheduleCommunityCommentVisibilityCheck(80)
  scheduleCommunityCommentKeyboardReset()
}

function handleCommunityReaderScroll(event) {
  const nextScrollTop = Math.max(0, Number(event?.detail?.scrollTop || 0))
  const moved = Math.abs(nextScrollTop - communityReaderLastScrollTop) > 1
  communityReaderLastScrollTop = nextScrollTop
  if (!moved) return

  if (communityCommentInputFocused.value) {
    if (Date.now() - communityCommentInputFocusStartedAt > 220) {
      resetCommunityCommentEntry({ hideKeyboard: true })
    }
  } else {
    communityCommentEntryReady.value = false
  }
  scheduleCommunityCommentVisibilityCheck()
}

function handleCommunityReaderScrollTouchMove() {
  if (communityCommentInputFocused.value) {
    resetCommunityCommentEntry({ hideKeyboard: true })
  } else {
    communityCommentEntryReady.value = false
  }
}

function scrollCommunityReaderToTop() {
  resetCommunityCommentEntry({ hideKeyboard: true })
  communityReaderTopZoneLastTapAt = 0
  scrollCommunityReaderTo('community-reader-top')
}

function handleCommunityReaderTopZoneTap() {
  const now = Date.now()
  const elapsed = now - communityReaderTopZoneLastTapAt
  if (communityReaderTopZoneLastTapAt > 0 && elapsed <= COMMUNITY_READER_DOUBLE_TAP_WINDOW) {
    scrollCommunityReaderToTop()
    return
  }
  communityReaderTopZoneLastTapAt = now
}

function handleCommunityReaderMediaChange(event) {
  communityReaderMediaIndex.value = Number(event?.detail?.current ?? 0)
}

function getCommunityReaderImageUrl(media) {
  return String(media?.imageUrl || media?.image_url || '').trim()
}

function previewCommunityReaderImages(activeMedia) {
  const mediaItems = Array.isArray(selectedCommunityPost.value?.media)
    ? selectedCommunityPost.value.media
    : []
  const urls = mediaItems.map((media) => getCommunityReaderImageUrl(media)).filter(Boolean)
  if (!urls.length) return

  const activeUrl = getCommunityReaderImageUrl(activeMedia)
  const currentIndex = Math.max(0, urls.indexOf(activeUrl))
  uni.previewImage({
    urls,
    current: urls[currentIndex],
    indicator: 'number',
    loop: true
  })
}

function openCommunityPostActions(post) {
  if (!post?.title) return
  if (isAuthed.value && !post.ownershipKnown) {
    uni.showToast({ title: '正在确认帖子信息，请稍候', icon: 'none' })
    return
  }
  const isOwnPost = Boolean(post.isMine)
  const actions = isOwnPost
    ? ['分享帖子', '编辑', '删除帖子']
    : ['分享帖子', ...(isAuthed.value ? ['举报帖子', '我的举报'] : [])]
  uni.showActionSheet({
    itemList: actions,
    success(result) {
      const selected = actions[Number(result?.tapIndex || 0)]
      if (selected === '编辑') {
        openOwnCommunityPostEditor(post)
        return
      }
      if (selected === '删除帖子') {
        confirmDeleteOwnCommunityPost(post)
        return
      }
      if (selected === '举报帖子') {
        openCommunityReport(post)
        return
      }
      if (selected === '我的举报') {
        openCommunityReportCenter()
        return
      }
      copyCommunityPostShare(post)
    }
  })
}

function openOwnCommunityPostEditor(post) {
  if (!post?.id || !post.isMine) return
  const postType = normalizeCircleCommunityPostType(post.postType || post.post_type)
  const url = `/pages/circle/publish?type=${postType}&edit=${encodeURIComponent(post.id)}`
  uni.navigateTo({
    url,
    fail() {
      uni.showToast({ title: '编辑页打开失败，请重试', icon: 'none' })
    }
  })
}

function confirmDeleteOwnCommunityPost(post) {
  if (!post?.id || !post.isMine) return
  uni.showModal({
    title: '删除帖子',
    content: '删除后帖子、评论和点赞记录都会移除，请确认是否继续。',
    confirmText: '删除',
    confirmColor: '#d65f59',
    cancelText: '取消',
    success(result) {
      if (result.confirm) void deleteOwnCommunityPost(post)
    }
  })
}

function removeCommunityPostFromFeeds(postId) {
  if (!postId) return
  const feedRefs = [
    circleCommunityPosts,
    circleFeaturedCommunityPosts,
    circleHotCommunityPosts,
    circleExperienceCommunityPosts,
    circleFeaturedExperiencePosts,
    circleHotExperienceCommunityPosts
  ]
  feedRefs.forEach((listRef) => {
    listRef.value = listRef.value.filter((item) => item.id !== postId)
  })
  Object.keys(communityFeedPages).forEach((pageKey) => {
    if (!Array.isArray(communityFeedPages[pageKey])) return
    communityFeedPages[pageKey] = communityFeedPages[pageKey].filter((item) => item.id !== postId)
  })
  scheduleCircleCommunityFeedPersist('chat')
  scheduleCircleCommunityFeedPersist('experience')
}

async function deleteOwnCommunityPost(post) {
  const postId = String(post?.id || '')
  if (!postId || !post.isMine) return
  try {
    const response = await deleteMyCommunityPosts([postId])
    const deletedIds = Array.isArray(response?.deleted_post_ids) ? response.deleted_post_ids.map(String) : []
    if (!deletedIds.includes(postId)) throw { detail: '帖子状态已变化，请刷新后重试' }
    removeCommunityPostFromFeeds(postId)
    try {
      uni.setStorageSync(getCircleCommunityFeedRefreshKey(post.postType), Date.now())
      if (communityReaderReturnsToMyPosts.value) {
        uni.setStorageSync(MY_POSTS_REFRESH_REQUIRED_KEY, Date.now())
      }
    } catch (error) {
      // 本地刷新标记失败不影响已完成的删除。
    }
    if (selectedCommunityPost.value?.id === postId) {
      if (communityReaderReturnsToMyPosts.value) returnToMyPostsFromCommunityReader()
      else closeCommunityPost()
    }
    uni.showToast({ title: '帖子已删除', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '帖子删除失败，请稍后重试'), icon: 'none' })
  }
}

function shareCommunityPost() {
  openCommunityPostActions(selectedCommunityPost.value)
}

async function loadMoreCircleCommunityPosts() {
  const postType = normalizeCircleCommunityPostType(selectedCircleCommunityTab.value)
  const sortBy = selectedCommunityPostSort.value
  const featuredOnly = sortBy === 'featured'
  const category = activeCommunityCategory.value === '全部' ? '' : activeCommunityCategory.value
  const search = communityAppliedSearch[postType]
  const pageKey = getCircleCommunityFeedPageKey(postType, { featuredOnly, sortBy, category, search })
  if (communityPostsLoadingTypes.has(pageKey)) return
  if (communityFeedHasMore[pageKey] === false || !communityFeedNextCursors[pageKey]) return
  await loadCircleCommunityPosts(postType, { featuredOnly, sortBy, search })
}

function copyCommunityPostShare(post) {
  const url = typeof window !== 'undefined' ? window.location.href : ''
  if (typeof navigator !== 'undefined' && typeof navigator.share === 'function') {
    navigator.share({ title: post.title, text: post.title, url }).catch(() => {})
    return
  }

  uni.setClipboardData({
    data: url || post.title,
    success: () => uni.showToast({ title: '链接已复制', icon: 'none' })
  })
}

function openCommunityReport(post, comment = null) {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  if (!post?.id) return
  const targetTitle = comment?.content || post.title || '研圈内容'
  const query = [
    `postId=${encodeURIComponent(post.id)}`,
    comment?.id ? `commentId=${encodeURIComponent(comment.id)}` : '',
    `title=${encodeURIComponent(targetTitle)}`
  ].filter(Boolean).join('&')
  uni.navigateTo({ url: `/pages/circle/community-report?${query}` })
}

function openCommunityReportCenter() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  uni.navigateTo({ url: '/pages/circle/community-reports' })
}

function openCommunityCommentActions(comment) {
  const post = selectedCommunityCommentsPost.value
  if (!post?.id || !comment?.id) return
  if (!isAuthed.value) {
    goLogin()
    return
  }
  const actions = comment.isMine ? ['删除评论'] : ['举报评论']
  uni.showActionSheet({
    itemList: actions,
    itemColor: comment.isMine ? '#dc675d' : '#425d82',
    success(result) {
      if (actions[Number(result?.tapIndex || 0)] === '删除评论') {
        confirmDeleteCommunityComment(post, comment)
      } else {
        openCommunityReport(post, comment)
      }
    }
  })
}

function confirmDeleteCommunityComment(post, comment) {
  uni.showModal({
    title: '删除这条评论？',
    content: '删除后不可恢复；若评论已进入平台处理记录，将保留作为处理凭证。',
    confirmText: '删除',
    confirmColor: '#dc675d',
    success(result) {
      if (result.confirm) void deleteOwnCommunityComment(post, comment)
    }
  })
}

async function deleteOwnCommunityComment(post, comment) {
  try {
    const response = await deleteCommunityComment(post.id, comment.id)
    communityComments.value = communityComments.value.filter((item) => item.id !== comment.id)
    const commentPreviews = post.commentPreviews.filter((item) => item.id !== comment.id)
    patchCommunityPost(post.id, {
      commentPreviews,
      commentPreview: commentPreviews[0] || null,
      stats: { comments: Number(response?.comment_count || 0) }
    })
    uni.showToast({ title: '评论已删除', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '评论删除失败，请稍后重试'), icon: 'none' })
  }
}

function clearCommunityReaderRouteTimers() {
  if (communityReaderRouteFrameTimer) {
    clearTimeout(communityReaderRouteFrameTimer)
    communityReaderRouteFrameTimer = null
  }
  if (communityReaderRouteFinishTimer) {
    clearTimeout(communityReaderRouteFinishTimer)
    communityReaderRouteFinishTimer = null
  }
}

function scheduleCommunityReaderRouteFinish(expectedMotion) {
  if (communityReaderRouteFinishTimer) clearTimeout(communityReaderRouteFinishTimer)
  const delay = prefersReducedCircleRouteMotion()
    ? 0
    : CIRCLE_DETAIL_ROUTE_DURATION + CIRCLE_DETAIL_ROUTE_FALLBACK_DELAY
  communityReaderRouteFinishTimer = setTimeout(() => {
    communityReaderRouteFinishTimer = null
    if (communityReaderRouteMotion.value !== expectedMotion) return
    if (expectedMotion === 'entering') finishCommunityReaderRouteEnter()
    if (expectedMotion === 'leaving') finishCommunityPostClose()
  }, delay)
}

function showCommunityReaderWithTransition() {
  clearCommunityReaderRouteTimers()
  communityReaderClosing.value = false

  if (prefersReducedCircleRouteMotion()) {
    communityReaderRouteMotion.value = 'idle'
    return
  }

  communityReaderRouteMotion.value = 'enter-from'
  nextTick(() => {
    communityReaderRouteFrameTimer = setTimeout(() => {
      communityReaderRouteFrameTimer = null
      if (!selectedCommunityPost.value || communityReaderRouteMotion.value !== 'enter-from') return
      communityReaderRouteMotion.value = 'entering'
      scheduleCommunityReaderRouteFinish('entering')
    }, CIRCLE_DETAIL_ROUTE_FRAME_DELAY)
  })
}

function finishCommunityReaderRouteEnter() {
  if (communityReaderRouteMotion.value !== 'entering') return
  clearCommunityReaderRouteTimers()
  communityReaderRouteMotion.value = 'idle'
  communityReaderClosing.value = false
}

function finishCommunityPostClose() {
  clearCommunityReaderRouteTimers()
  clearCommunityViewTimer()
  clearCommunityLikeBurst()
  closeCommunityComments()
  communityReaderScrollTarget.value = ''
  communityReaderMediaIndex.value = 0
  communityReaderEdgeSwipeStart.value = null
  communityReaderClosing.value = false
  communityReaderRouteMotion.value = 'idle'
  selectedCommunityPost.value = null
  communityReaderOwnerPreview.value = false
  communityReaderOwnerLoading.value = false
  communityReaderInteractionsEnabled.value = true
}

function closeCommunityPost(options = {}) {
  const animated = options?.animated === true && Boolean(selectedCommunityPost.value)
  const currentMotion = communityReaderRouteMotion.value

  if (!animated) {
    finishCommunityPostClose()
    return
  }
  if (
    communityReaderClosing.value
    || communityReaderRouteMotion.value === 'leave-preparing'
    || communityReaderRouteMotion.value === 'leaving'
  ) return

  clearCommunityReaderRouteTimers()
  clearCommunityViewTimer()
  clearCommunityLikeBurst()
  resetCommunityCommentEntry({ hideKeyboard: true })
  communityReaderEdgeSwipeStart.value = null
  communityReaderClosing.value = true

  if (prefersReducedCircleRouteMotion()) {
    communityReaderRouteMotion.value = 'leaving'
    finishCommunityPostClose()
    return
  }

  if (currentMotion === 'enter-from') {
    finishCommunityPostClose()
    return
  }

  if (currentMotion === 'entering') {
    communityReaderRouteMotion.value = 'leaving'
    scheduleCommunityReaderRouteFinish('leaving')
    return
  }

  communityReaderRouteMotion.value = 'leave-preparing'
  nextTick(() => {
    communityReaderRouteFrameTimer = setTimeout(() => {
      communityReaderRouteFrameTimer = null
      if (!selectedCommunityPost.value || communityReaderRouteMotion.value !== 'leave-preparing') return
      communityReaderRouteMotion.value = 'leaving'
      scheduleCommunityReaderRouteFinish('leaving')
    }, CIRCLE_DETAIL_ROUTE_FRAME_DELAY)
  })
}

function closeCommunityPostWithTapGuard() {
  if (communityReaderReturnsToMyPosts.value) {
    returnToMyPostsFromCommunityReader()
    return
  }
  closeCommunityPost({ animated: true })
}

function returnToMyPostsFromCommunityReader() {
  if (communityReaderClosing.value) return
  clearCommunityReaderRouteTimers()
  clearCommunityViewTimer()
  clearCommunityLikeBurst()
  resetCommunityCommentEntry({ hideKeyboard: true })
  communityReaderEdgeSwipeStart.value = null
  communityReaderClosing.value = true
  uni.navigateBack({
    delta: 1,
    fail() {
      uni.redirectTo({
        url: '/pages/circle/my-posts',
        fail() {
          communityReaderClosing.value = false
        }
      })
    }
  })
}

function handleCommunityReaderRouteTransitionEnd(event) {
  if (event?.target && event?.currentTarget && event.target !== event.currentTarget) return
  const propertyName = event?.propertyName || event?.detail?.propertyName || ''
  if (propertyName && propertyName !== 'transform') return
  if (communityReaderRouteMotion.value === 'entering') {
    finishCommunityReaderRouteEnter()
  } else if (communityReaderRouteMotion.value === 'leaving') {
    finishCommunityPostClose()
  }
}

function beginCommunityReaderEdgeSwipe(event) {
  if (communityReaderClosing.value || communityReaderRouteMotion.value !== 'idle') return
  const touch = getCircleTouchPoint(event)
  if (!touch) return
  communityReaderEdgeSwipeStart.value = {
    x: Number(touch.clientX ?? touch.pageX ?? 0),
    y: Number(touch.clientY ?? touch.pageY ?? 0)
  }
}

function finishCommunityReaderEdgeSwipe(event) {
  const start = communityReaderEdgeSwipeStart.value
  communityReaderEdgeSwipeStart.value = null
  if (!start || !selectedCommunityPost.value || communityReaderRouteMotion.value !== 'idle') return

  const touch = getCircleTouchPoint(event)
  if (!touch) return
  const deltaX = Number(touch.clientX ?? touch.pageX ?? 0) - start.x
  const deltaY = Number(touch.clientY ?? touch.pageY ?? 0) - start.y
  if (start.x <= 28 && deltaX >= 72 && Math.abs(deltaX) > Math.abs(deltaY) * 1.35) {
    closeCommunityPostWithTapGuard()
  }
}

function cancelCommunityReaderEdgeSwipe() {
  communityReaderEdgeSwipeStart.value = null
}

async function openCommunityComments(post) {
  const initialPost = normalizeCommunityPost(post)
  if (!initialPost.id) return

  if (selectedCommunityCommentsPost.value?.id === initialPost.id) {
    communityInteractionTab.value = 'comments'
    return
  }

  selectedCommunityCommentsPost.value = initialPost
  communityInteractionTab.value = 'comments'
  communityCommentSort.value = 'default'
  communityCommentDraft.value = ''
  communityLikes.value = []
  communityLikesLoading.value = false
  communityCommentsNextCursor.value = ''
  communityCommentsHasMore.value = false
  communityCommentsLoadError.value = ''
  communityComments.value = initialPost.commentPreviews.map((comment) => normalizeCommunityComment({
    id: comment.id,
    author: comment.author,
    avatar: comment.author.slice(0, 1),
    content: comment.text,
    createdAt: ''
  }))
  communityCommentsLoading.value = true

  try {
    const response = await fetchCommunityPost(initialPost.id, { comments_limit: 20 })
    if (response?.post && selectedCommunityCommentsPost.value?.id === initialPost.id) {
      const remotePost = normalizeCommunityPost(response.post)
      selectedCommunityCommentsPost.value = remotePost
      patchCommunityPost(initialPost.id, remotePost)
      const remoteComments = Array.isArray(response.comments)
        ? response.comments.map((comment) => normalizeCommunityComment(comment))
        : []
      const remoteIds = new Set(remoteComments.map((comment) => comment.id))
      const recentLocalComments = communityComments.value.filter((comment) => {
        if (remoteIds.has(comment.id)) return false
        if (comment.deliveryStatus) return true
        const createdAt = Date.parse(comment.createdAt) || 0
        return comment.isMine && Date.now() - createdAt < 30000
      })
      communityComments.value = [...remoteComments, ...recentLocalComments]
      communityCommentsNextCursor.value = String(response.comments_next_cursor || '')
      communityCommentsHasMore.value = response.comments_has_more === true
    }
  } catch (error) {
    if (selectedCommunityCommentsPost.value?.id === initialPost.id) {
      communityCommentsLoadError.value = getSafeError(error, '评论加载失败，请检查网络后重试')
    }
  } finally {
    if (selectedCommunityCommentsPost.value?.id === initialPost.id) {
      communityCommentsLoading.value = false
    }
  }
}

async function loadMoreCommunityComments() {
  const postId = selectedCommunityCommentsPost.value?.id
  const cursor = communityCommentsNextCursor.value
  if (!postId || !cursor || !communityCommentsHasMore.value || communityCommentsLoadingMore.value) return

  communityCommentsLoadingMore.value = true
  communityCommentsLoadError.value = ''
  try {
    const response = await fetchCommunityComments(postId, { limit: 20, cursor })
    if (selectedCommunityCommentsPost.value?.id !== postId) return
    const incoming = Array.isArray(response?.items)
      ? response.items.map((comment) => normalizeCommunityComment(comment))
      : []
    const existingIds = new Set(communityComments.value.map((comment) => comment.id))
    communityComments.value = [
      ...incoming.filter((comment) => !existingIds.has(comment.id)),
      ...communityComments.value
    ]
    communityCommentsNextCursor.value = String(response?.next_cursor || '')
    communityCommentsHasMore.value = response?.has_more === true
  } catch (error) {
    if (selectedCommunityCommentsPost.value?.id === postId) {
      communityCommentsLoadError.value = getSafeError(error, '更早评论加载失败，请重试')
    }
  } finally {
    if (selectedCommunityCommentsPost.value?.id === postId) {
      communityCommentsLoadingMore.value = false
    }
  }
}

function retryCommunityComments() {
  const post = selectedCommunityCommentsPost.value
  if (!post?.id || communityCommentsLoading.value) return
  selectedCommunityCommentsPost.value = null
  void openCommunityComments(post)
}

async function selectCommunityInteractionTab(tab) {
  const post = selectedCommunityCommentsPost.value
  if (!post?.id) return

  communityInteractionTab.value = tab === 'likes' ? 'likes' : 'comments'
  if (communityInteractionTab.value === 'likes') {
    await loadCommunityPostLikes(post.id)
  }
}

async function loadCommunityPostLikes(postId) {
  if (!postId || communityLikesLoading.value) return

  communityLikesLoading.value = true
  try {
    const response = await fetchCommunityPostLikes(postId, { limit: 100 })
    if (selectedCommunityCommentsPost.value?.id === postId) {
      communityLikes.value = Array.isArray(response?.items)
        ? response.items.map((item) => ({
          id: String(item.id || `${postId}-${item.author || 'like'}`),
          author: item.author || '研友',
          avatar: item.avatar || String(item.author || '研友').slice(0, 1),
          avatarUrl: item.avatarUrl || item.avatar_url || '',
          likedAt: item.likedAt || item.liked_at || ''
        }))
        : []
    }
  } catch (error) {
    if (selectedCommunityCommentsPost.value?.id === postId) {
      communityLikes.value = []
      uni.showToast({ title: getSafeError(error, '点赞用户加载失败，请稍后重试'), icon: 'none' })
    }
  } finally {
    if (selectedCommunityCommentsPost.value?.id === postId) {
      communityLikesLoading.value = false
    }
  }
}

function closeCommunityComments() {
  resetCommunityCommentEntry({ hideKeyboard: true })
  resetCommunityCommentKeyboardState()
  communityReaderTopZoneLastTapAt = 0
  selectedCommunityCommentsPost.value = null
  communityComments.value = []
  communityCommentsLoading.value = false
  communityCommentsLoadingMore.value = false
  communityCommentsNextCursor.value = ''
  communityCommentsHasMore.value = false
  communityCommentsLoadError.value = ''
  communityInteractionTab.value = 'comments'
  communityLikes.value = []
  communityLikesLoading.value = false
  communityCommentSort.value = 'default'
  communityCommentDraft.value = ''
}

function clearCommunityViewTimer() {
  if (!communityViewTimerId) return
  clearTimeout(communityViewTimerId)
  communityViewTimerId = null
}

function clearCommunityLikeBurst() {
  if (communityLikeBurstTimerId !== null) {
    clearTimeout(communityLikeBurstTimerId)
    communityLikeBurstTimerId = null
  }
  communityLikeBurstPostId.value = ''
}

function triggerCommunityLikeBurst(postId) {
  const normalizedPostId = String(postId || '').trim()
  if (!normalizedPostId || selectedCommunityPost.value?.id !== normalizedPostId) return
  clearCommunityLikeBurst()
  communityLikeBurstPostId.value = normalizedPostId
  communityLikeBurstTimerId = setTimeout(() => {
    if (communityLikeBurstPostId.value === normalizedPostId) {
      communityLikeBurstPostId.value = ''
    }
    communityLikeBurstTimerId = null
  }, 520)
}

function scheduleCommunityView(postId) {
  clearCommunityViewTimer()
  communityViewTimerId = setTimeout(() => {
    communityViewTimerId = null
    if (selectedCommunityPost.value?.id !== postId) return
    if (typeof document !== 'undefined' && document.visibilityState === 'hidden') return
    registerEffectiveCommunityView(postId)
  }, 3000)
}

function getCommunityAnonymousId() {
  const storageKey = 'circle-community-anonymous-id'
  const stored = String(uni.getStorageSync(storageKey) || '')
  if (/^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(stored)) {
    return stored
  }

  const generated = typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`.replace(/[xy]/g, (marker) => {
      const random = Math.floor(Math.random() * 16)
      return (marker === 'x' ? random : ((random & 0x3) | 0x8)).toString(16)
    })
  uni.setStorageSync(storageKey, generated)
  return generated
}

async function registerEffectiveCommunityView(postId) {
  try {
    const response = await registerCommunityPostView(postId, {
      anonymous_id: getCommunityAnonymousId()
    })
    if (response?.post_id === postId) {
      patchCommunityPost(postId, {
        stats: { views: Number(response.view_count || 0) }
      })
    }
  } catch (error) {
    // 浏览统计在后台失败时不影响用户继续阅读，也不会在本地虚增数字。
  }
}

function normalizeCommunityLikeCount(value, fallback = 0) {
  const count = Number(value)
  if (!Number.isFinite(count)) return Math.max(0, Number(fallback) || 0)
  return Math.max(0, Math.round(count))
}

function isCommunityPostLikePending(postId) {
  const normalizedPostId = String(postId || '').trim()
  return Boolean(normalizedPostId && communityPostLikePendingIds[normalizedPostId])
}

function setCommunityPostLikePending(postId, pending) {
  const normalizedPostId = String(postId || '').trim()
  if (!normalizedPostId) return
  if (pending) {
    communityPostLikePendingIds[normalizedPostId] = true
  } else {
    delete communityPostLikePendingIds[normalizedPostId]
  }
}

function getCommunityCommentLikeQueueKey(postId, commentId) {
  const normalizedPostId = String(postId || '').trim()
  const normalizedCommentId = String(commentId || '').trim()
  return normalizedPostId && normalizedCommentId
    ? `${normalizedPostId}:${normalizedCommentId}`
    : ''
}

function isCommunityCommentLikePending(postId, commentId) {
  const key = getCommunityCommentLikeQueueKey(postId, commentId)
  return Boolean(key && communityCommentLikePendingIds[key])
}

function setCommunityCommentLikePending(postId, commentId, pending) {
  const key = getCommunityCommentLikeQueueKey(postId, commentId)
  if (!key) return
  if (pending) {
    communityCommentLikePendingIds[key] = true
  } else {
    delete communityCommentLikePendingIds[key]
  }
}

function getCommunityPostLikeQueue(post) {
  const postId = String(post?.id || '').trim()
  if (!postId) return null
  let queue = communityPostLikeQueues.get(postId)
  if (!queue) {
    const liked = Boolean(post.liked)
    const likeCount = normalizeCommunityLikeCount(post.stats?.likes)
    queue = {
      confirmedLiked: liked,
      confirmedCount: likeCount,
      desiredLiked: liked,
      optimisticCount: likeCount,
      running: false
    }
    communityPostLikeQueues.set(postId, queue)
  }
  return { postId, queue }
}

async function flushCommunityPostLikeQueue(postId, queue) {
  if (!postId || !queue || queue.running) return
  queue.running = true
  setCommunityPostLikePending(postId, true)

  try {
    let requestCount = 0
    while (queue.desiredLiked !== queue.confirmedLiked) {
      if (requestCount >= 4) {
        throw { detail: '点赞状态同步失败，请稍后重试' }
      }
      requestCount += 1

      const requestedLiked = queue.desiredLiked
      const response = await toggleCommunityPostLike(postId, requestedLiked)
      const confirmedLiked = Boolean(response?.is_liked)
      const confirmedCount = normalizeCommunityLikeCount(response?.like_count, queue.confirmedCount)
      queue.confirmedLiked = confirmedLiked
      queue.confirmedCount = confirmedCount

      // 连点时先保持用户最后一次点击的视觉状态，队列清空后再用服务端数量校正。
      if (queue.desiredLiked === confirmedLiked) {
        queue.optimisticCount = confirmedCount
        patchCommunityPost(postId, {
          liked: confirmedLiked,
          stats: { likes: confirmedCount }
        })
        if (!confirmedLiked && communityLikeBurstPostId.value === postId) {
          clearCommunityLikeBurst()
        }
        if (
          selectedCommunityCommentsPost.value?.id === postId
          && communityInteractionTab.value === 'likes'
        ) {
          void loadCommunityPostLikes(postId)
        }
      }
    }
  } catch (error) {
    queue.desiredLiked = queue.confirmedLiked
    queue.optimisticCount = queue.confirmedCount
    patchCommunityPost(postId, {
      liked: queue.confirmedLiked,
      stats: { likes: queue.confirmedCount }
    })
    if (!queue.confirmedLiked && communityLikeBurstPostId.value === postId) {
      clearCommunityLikeBurst()
    }
    uni.showToast({ title: getSafeError(error, '点赞失败，请稍后重试'), icon: 'none' })
  } finally {
    queue.running = false
    setCommunityPostLikePending(postId, false)
    if (communityPostLikeQueues.get(postId) === queue) {
      communityPostLikeQueues.delete(postId)
    }
  }
}

function toggleCommunityLike(post) {
  if (!post?.id) return
  if (!isAuthed.value) {
    goLogin()
    return
  }

  const entry = getCommunityPostLikeQueue(post)
  if (!entry) return
  const { postId, queue } = entry
  const nextLiked = !queue.desiredLiked
  queue.desiredLiked = nextLiked
  queue.optimisticCount = Math.max(0, queue.optimisticCount + (nextLiked ? 1 : -1))

  patchCommunityPost(postId, {
    liked: nextLiked,
    stats: { likes: queue.optimisticCount }
  }, { persist: false })
  if (nextLiked) {
    triggerCommunityLikeBurst(postId)
  } else if (communityLikeBurstPostId.value === postId) {
    clearCommunityLikeBurst()
  }

  void flushCommunityPostLikeQueue(postId, queue)
}

function getCommunityCommentLikeQueue(post, comment) {
  const postId = String(post?.id || '').trim()
  const commentId = String(comment?.id || '').trim()
  const key = getCommunityCommentLikeQueueKey(postId, commentId)
  if (!key) return null
  let queue = communityCommentLikeQueues.get(key)
  if (!queue) {
    const currentComment = communityComments.value.find((item) => item.id === commentId) || comment
    const liked = Boolean(currentComment.liked)
    const likeCount = normalizeCommunityLikeCount(currentComment.likeCount)
    queue = {
      confirmedLiked: liked,
      confirmedCount: likeCount,
      desiredLiked: liked,
      optimisticCount: likeCount,
      running: false
    }
    communityCommentLikeQueues.set(key, queue)
  }
  return { postId, commentId, key, queue }
}

async function flushCommunityCommentLikeQueue(postId, commentId, key, queue) {
  if (!postId || !commentId || !key || !queue || queue.running) return
  queue.running = true
  setCommunityCommentLikePending(postId, commentId, true)

  try {
    let requestCount = 0
    while (queue.desiredLiked !== queue.confirmedLiked) {
      if (requestCount >= 4) {
        throw { detail: '评论点赞状态同步失败，请稍后重试' }
      }
      requestCount += 1

      const requestedLiked = queue.desiredLiked
      const response = await toggleCommunityCommentLikeRequest(postId, commentId, requestedLiked)
      const confirmedLiked = Boolean(response?.is_liked)
      const confirmedCount = normalizeCommunityLikeCount(response?.like_count, queue.confirmedCount)
      queue.confirmedLiked = confirmedLiked
      queue.confirmedCount = confirmedCount

      if (queue.desiredLiked === confirmedLiked) {
        queue.optimisticCount = confirmedCount
        patchCommunityCommentLike(commentId, {
          liked: confirmedLiked,
          likeCount: confirmedCount
        })
      }
    }
  } catch (error) {
    queue.desiredLiked = queue.confirmedLiked
    queue.optimisticCount = queue.confirmedCount
    patchCommunityCommentLike(commentId, {
      liked: queue.confirmedLiked,
      likeCount: queue.confirmedCount
    })
    uni.showToast({ title: getSafeError(error, '评论点赞失败，请稍后重试'), icon: 'none' })
  } finally {
    queue.running = false
    setCommunityCommentLikePending(postId, commentId, false)
    if (communityCommentLikeQueues.get(key) === queue) {
      communityCommentLikeQueues.delete(key)
    }
  }
}

function toggleCommunityCommentLike(comment) {
  const post = selectedCommunityCommentsPost.value
  if (!post?.id || !comment?.id || comment.deliveryStatus) return
  if (!isAuthed.value) {
    goLogin()
    return
  }

  const entry = getCommunityCommentLikeQueue(post, comment)
  if (!entry) return
  const { postId, commentId, key, queue } = entry
  const nextLiked = !queue.desiredLiked
  queue.desiredLiked = nextLiked
  queue.optimisticCount = Math.max(0, queue.optimisticCount + (nextLiked ? 1 : -1))

  patchCommunityCommentLike(commentId, {
    liked: nextLiked,
    likeCount: queue.optimisticCount
  })

  void flushCommunityCommentLikeQueue(postId, commentId, key, queue)
}

function createCommunityInteractionRequestId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID()
  }
  return `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`.replace(/[xy]/g, (marker) => {
    const random = Math.floor(Math.random() * 16)
    return (marker === 'x' ? random : ((random & 0x3) | 0x8)).toString(16)
  })
}

function patchCommunityComment(commentId, patch) {
  communityComments.value = communityComments.value.map((comment) => (
    comment.id === commentId ? { ...comment, ...patch } : comment
  ))
}

function getOptimisticCommunityCommentAuthor() {
  const name = getUserDisplayName(authUser.value, profile.value.userName || '研友') || '研友'
  return {
    author: name,
    avatar: profileAvatarText.value || name.slice(0, 1) || '研',
    avatarUrl: avatarImageUrl.value || ''
  }
}

function updateCommunityCommentPreview(postId, comment, { remove = false } = {}) {
  const post = selectedCommunityCommentsPost.value?.id === postId
    ? selectedCommunityCommentsPost.value
    : selectedCommunityPost.value?.id === postId
      ? selectedCommunityPost.value
      : null
  if (!post) return
  const filtered = (post.commentPreviews || []).filter((item) => item.id !== comment.id)
  const commentPreviews = remove
    ? filtered
    : [{ id: comment.id, author: comment.author, text: comment.content }, ...filtered].slice(0, 3)
  patchCommunityPost(postId, {
    commentPreviews,
    commentPreview: commentPreviews[0] || null
  })
}

async function sendOptimisticCommunityComment(comment) {
  const postId = String(comment?.postId || selectedCommunityCommentsPost.value?.id || '')
  if (!postId || !comment?.content || communityCommentSubmitting.value) return

  const currentPost = selectedCommunityCommentsPost.value?.id === postId
    ? selectedCommunityCommentsPost.value
    : selectedCommunityPost.value
  const previousCommentCount = Math.max(0, Number(currentPost?.stats?.comments || 0))
  patchCommunityComment(comment.id, {
    deliveryStatus: 'sending',
    errorMessage: '',
    optimisticCounted: true,
    previousCommentCount
  })
  patchCommunityPost(postId, { stats: { comments: previousCommentCount + 1 } }, { persist: false })
  updateCommunityCommentPreview(postId, comment)
  communityCommentSubmitting.value = true

  try {
    const response = await createCommunityComment(postId, {
      content: comment.content,
      client_request_id: comment.clientRequestId
    })
    if (!response?.comment) throw { detail: '评论返回数据不完整，请重试' }

    const confirmedComment = normalizeCommunityComment(response.comment)
    if (selectedCommunityCommentsPost.value?.id === postId) {
      communityComments.value = communityComments.value.map((item) => (
        item.id === comment.id ? confirmedComment : item
      ))
    }
    const activePost = selectedCommunityCommentsPost.value?.id === postId
      ? selectedCommunityCommentsPost.value
      : selectedCommunityPost.value?.id === postId
        ? selectedCommunityPost.value
        : null
    const commentPreviews = [
      { id: confirmedComment.id, author: confirmedComment.author, text: confirmedComment.content },
      ...(activePost?.commentPreviews || []).filter((item) => ![comment.id, confirmedComment.id].includes(item.id))
    ].slice(0, 3)
    patchCommunityPost(postId, {
      commentPreviews,
      commentPreview: commentPreviews[0] || null,
      stats: { comments: Math.max(0, Number(response.comment_count || previousCommentCount + 1)) }
    })
  } catch (error) {
    const message = getSafeError(error, '评论发布失败，请点击重试')
    patchCommunityComment(comment.id, {
      deliveryStatus: 'failed',
      errorMessage: message,
      optimisticCounted: false,
      previousCommentCount
    })
    updateCommunityCommentPreview(postId, comment, { remove: true })
    patchCommunityPost(postId, { stats: { comments: previousCommentCount } }, { persist: false })
    uni.showToast({ title: message, icon: 'none' })
  } finally {
    communityCommentSubmitting.value = false
  }
}

function retryCommunityComment(comment) {
  if (!comment || comment.deliveryStatus !== 'failed') return
  void sendOptimisticCommunityComment(comment)
}

function submitCommunityComment() {
  const post = selectedCommunityCommentsPost.value
  const content = communityCommentDraft.value.trim()
  if (!post?.id || !content || communityCommentSubmitting.value) return
  if (!isAuthed.value) {
    goLogin()
    return
  }

  const clientRequestId = createCommunityInteractionRequestId()
  const author = getOptimisticCommunityCommentAuthor()
  const optimisticComment = normalizeCommunityComment({
    id: `pending-${clientRequestId}`,
    postId: post.id,
    ...author,
    content,
    createdAt: new Date().toISOString(),
    isMine: true,
    deliveryStatus: 'queued',
    clientRequestId
  })
  optimisticComment.postId = post.id
  communityComments.value.push(optimisticComment)
  communityCommentDraft.value = ''
  void sendOptimisticCommunityComment(optimisticComment)
}

function formatCommunityCommentTime(value) {
  if (!value) return '刚刚'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '刚刚'
  const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000))
  if (seconds < 60) return '刚刚'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分钟前`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} 小时前`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} 天前`
  return `${date.getMonth() + 1}/${date.getDate()}`
}

function showExperiencePublishVerificationModal() {
  let confirmationInProgress = false
  const qualificationRevoked = mentorEntryStatus.value === 'revoked'
  uni.showModal({
    title: qualificationRevoked ? '前辈资格已取消' : '发布经验帖需先完成前辈认证',
    content: qualificationRevoked
      ? '你可以核对资料后重新提交认证。再次审核通过后，原前辈档案和历史咨询记录会继续保留并恢复使用。'
      : '认证通过后，即可发布带有认证标识的经验帖。审核期间，平台将严格保护你填写的个人信息及证明材料；相关资料仅用于认证审核，不会向其他用户公开。',
    confirmText: qualificationRevoked ? '重新认证' : '去认证',
    success(result) {
      if (!result.confirm) return
      confirmationInProgress = true
      void openMentorVerificationEntry({ from: 'experience-publish' }).finally(() => {
        openingExperiencePublishEntry = false
      })
    },
    complete() {
      if (!confirmationInProgress) openingExperiencePublishEntry = false
    }
  })
}

async function openExperiencePublishPage() {
  if (openingExperiencePublishEntry) return
  openingExperiencePublishEntry = true

  if (!isAuthed.value) {
    goLogin()
    setTimeout(() => {
      openingExperiencePublishEntry = false
    }, 700)
    return
  }

  const knownStatus = getMentorVerificationStatus()
  mentorEntryStatus.value = knownStatus
  if (knownStatus !== 'verified') {
    // 未认证、审核中、被驳回或资格已取消都先给出明确认证入口；
    // 服务端状态在后台刷新，不再阻塞弹窗反馈。
    showExperiencePublishVerificationModal()
    void loadMentorEntryStatus({ force: true })
    return
  }

  try {
    // 已认证属于正向放行：命中一分钟内的预取结果时立即进入，
    // 状态过期时才等待服务端复核，网络失败不会凭陈旧缓存放行。
    if (!isMentorEntryStatusFresh()) await loadMentorEntryStatus({ force: true })
    if (mentorEntryStatus.value !== 'verified') {
      showExperiencePublishVerificationModal()
      return
    }
    if (!isMentorEntryStatusFresh()) throw new Error('mentor verification status unavailable')
    openCommunityPublishPage('experience')
    setTimeout(() => {
      openingExperiencePublishEntry = false
    }, 700)
  } catch (error) {
    openingExperiencePublishEntry = false
    uni.showToast({ title: '发布权限校验失败，请稍后重试', icon: 'none' })
  }
}

function openChatPublishPage() {
  openCommunityPublishPage('chat')
}

function openCommunityPublishPage(postType) {
  const now = Date.now()
  if (now - lastCommunityPublishNavigationAt < 700) return
  lastCommunityPublishNavigationAt = now

  const normalizedPostType = postType === 'experience' ? 'experience' : 'chat'
  const url = `/pages/circle/publish?type=${normalizedPostType}`
  uni.navigateTo({
    url,
    fail() {
      // Some H5 webviews can reject a deep navigation when their page stack is full.
      uni.redirectTo({
        url,
        fail() {
          uni.reLaunch({
            url,
            fail() {
              lastCommunityPublishNavigationAt = 0
              uni.showToast({ title: '发布页打开失败，请重试', icon: 'none' })
            }
          })
        }
      })
    }
  })
}

function selectCircleCommunityTab(tab) {
  if (!circleCommunityTabs.some((item) => item.key === tab)) return
  selectedCircleCommunityTab.value = tab
  selectedCirclePost.value = null
  closeCommunityPost()
  if (tab === 'mentor') {
    mentorFavoriteIds.value = getMentorFavoriteIds()
    void loadMentorEntryStatus()
    void loadMentorProfiles()
    void loadMentorFavoriteIds({ silent: true })
    resetCircleTabbar()
    return
  }
  if (tab === 'experience') void loadMentorEntryStatus({ force: !isMentorEntryStatusFresh() })
  const shouldRefreshTab = consumeCircleCommunityFeedRefresh(tab)
  const sortBy = selectedCommunityPostSort.value
  const featuredOnly = sortBy === 'featured'
  if (!featuredOnly && sortBy !== 'hot') hydrateCircleCommunityFeed(tab)
  loadCircleCommunityPosts(tab, {
    force: shouldRefreshTab,
    featuredOnly,
    sortBy,
    search: communityAppliedSearch[normalizeCircleCommunityPostType(tab)]
  })
  resetCircleTabbar()
}

function selectCircleCommunityCategory(category) {
  if (!circleCommunityCategories.includes(category)) return
  if (selectedCommunityCategory.value === category) return
  selectedCommunityCategory.value = category
  const sortBy = selectedCommunityPostSort.value
  void loadCircleCommunityPosts('chat', {
    force: false,
    featuredOnly: sortBy === 'featured',
    sortBy,
    search: communityAppliedSearch.chat
  })
}

function selectActiveCommunityCategory(category) {
  if (selectedCircleCommunityTab.value === 'experience') {
    selectExperienceCategory(category)
    return
  }
  selectCircleCommunityCategory(category)
}

function handleCirclePostLocalAction(action) {
  uni.showToast({ title: `${action}功能本地预览中`, icon: 'none' })
}

function logout() {
  if (!isAuthed.value) {
    clearAuthSession()
    authUser.value = null
    authed.value = false
    uni.reLaunch({ url: '/pages/login/index' })
    return
  }

  uni.showModal({
    title: '确认退出登录？',
    content: '退出后需要重新登录才能同步学习进度和查看个人数据。',
    confirmText: '退出登录',
    cancelText: '取消',
    confirmColor: '#ef4444',
    success(result) {
      if (!result.confirm) return
      clearAuthSession()
      authUser.value = null
      authed.value = false
      uni.reLaunch({ url: '/pages/login/index' })
    }
  })
}

function openProfileTab() {
  handleAccountEntry()
}

function openMistakes() {
  uni.navigateTo({ url: '/pages/mistakes/index' })
}

function openReport() {
  activeTab.value = 'report'
}

function handleMenu(item) {
  if (!item) return
  if (item.action === 'mistakes') {
    openMistakes()
    return
  }
  if (item.action === 'report') {
    openReport()
    return
  }
  if (item.action === 'history') {
    uni.navigateTo({ url: '/pages/history/index' })
    return
  }
  if (item.action === 'favorites') {
    uni.navigateTo({ url: '/pages/favorites/index' })
    return
  }
  if (item.action === 'major-favorites') {
    const destination = '/pages-sub-data/major-favorites/index'
    if (!isAuthed.value) {
      uni.navigateTo({ url: `/pages/login/index?redirect=${encodeURIComponent(destination)}` })
      return
    }
    uni.navigateTo({ url: destination })
    return
  }
  if (item.action === 'my-consultations') {
    if (!isAuthed.value) {
      goLogin()
      return
    }
    void openMyConsultationEntry()
    return
  }
  if (item.action === 'liked-posts') {
    if (!isAuthed.value) {
      goLogin()
      return
    }
    uni.navigateTo({ url: '/pages/circle/liked-posts' })
    return
  }
  if (item.action === 'my-posts') {
    if (!isAuthed.value) {
      goLogin()
      return
    }
    uni.navigateTo({ url: '/pages/circle/my-posts' })
    return
  }
  if (item.action === 'community-reports') {
    if (!isAuthed.value) {
      goLogin()
      return
    }
    uni.navigateTo({ url: '/pages/circle/community-reports' })
    return
  }
  if (item.action === 'ai-generator') {
    openRecommendedTrainingSheet()
    return
  }
  if (item.action === 'subscription') {
    openSubscriptionSheet()
    return
  }
  if (item.action === 'messages') {
    openMessageCenter()
    return
  }
  if (item.action === 'bind-phone') {
    openPhoneBindingModal()
    return
  }
  if (item.action === 'bind-email') {
    openEmailBindingModal()
    return
  }
  if (item.action === 'wallet') {
    const walletRole = mentorEntryStatus.value === 'verified' ? 'mentor' : 'user'
    uni.navigateTo({ url: `/pages-sub-wallet/wallet/index?role=${walletRole}` })
    return
  }
  if (item.action === 'admin') {
    uni.navigateTo({ url: '/pages-sub-admin/admin/index' })
    return
  }
  if (item.action === 'question-admin') {
    uni.navigateTo({ url: '/pages-sub-admin/admin/index?tab=questions' })
    return
  }
  if (item.action === 'about') {
    uni.navigateTo({ url: '/pages/about/index' })
    return
  }
  showMockToast()
}

function showMockToast() {
  uni.showToast({ title: '完整 AI 诊断后续再接入', icon: 'none' })
}

async function refreshLearningData() {
  if (!isAuthed.value) {
    wrongItems.value = []
    abilityReport.value = null
    learningSummary.value = null
    studyAdvice.value = null
    studyAdviceError.value = ''
    studyAdviceExamCode.value = ''
    wrongError.value = ''
    reportError.value = ''
    return
  }

  loadWrongQuestions()
  loadAbilityReport()
  loadLearningSummary()
}

async function loadWrongQuestions({ reset = true } = {}) {
  if (wrongLoading.value || wrongLoadingMore.value) return
  if (reset) {
    wrongItems.value = []
    wrongNextCursor.value = ''
    wrongHasMore.value = false
    wrongLoading.value = true
  } else {
    wrongLoadingMore.value = true
  }
  wrongError.value = ''
  try {
    const response = await fetchWrongQuestions({
      exam_code: examCode.value,
      limit: 30,
      subject: wrongFilters.value.subject || undefined,
      module: wrongFilters.value.module || undefined,
      submodule: wrongFilters.value.submodule || undefined,
      cursor: reset ? undefined : (wrongNextCursor.value || undefined)
    })
    const nextItems = Array.isArray(response?.items) ? response.items : []
    wrongItems.value = reset
      ? nextItems
      : [...wrongItems.value, ...nextItems.filter((item) => !wrongItems.value.some((existing) => existing.id === item.id))]
    wrongNextCursor.value = String(response?.next_cursor || '')
    wrongHasMore.value = response?.has_more === true
  } catch (error) {
    wrongError.value = getSafeError(error, '错题本同步失败，请稍后重试')
  } finally {
    if (reset) wrongLoading.value = false
    else wrongLoadingMore.value = false
  }
}

async function loadAbilityReport() {
  if (reportLoading.value) return

  reportLoading.value = true
  reportError.value = ''
  try {
    abilityReport.value = await fetchAbilityReport({ exam_code: examCode.value })
  } catch (error) {
    reportError.value = getSafeError(error, '学习报告同步失败，请稍后重试')
  } finally {
    reportLoading.value = false
  }
}

async function loadLearningSummary() {
  try {
    learningSummary.value = await fetchLearningSummary({ exam_code: examCode.value })
  } catch (error) {
    learningSummary.value = null
  }
}

function openStudyAdviceDetail() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  showStudyAdviceDetail.value = true
}

function closeStudyAdviceDetail() {
  showStudyAdviceDetail.value = false
}

function formatWrongQuestion(item) {
  const question = item?.question || {}
  const title = question.stem || `错题 ${item?.question_id || ''}`
  const tags = [
    question.subject,
    question.module,
    question.submodule,
    item?.wrong_count ? `错 ${item.wrong_count} 次` : ''
  ].filter(Boolean)

  return {
    id: item?.question_id || item?.id,
    title,
    subject: question.subject || '',
    module: question.module || '',
    submodule: question.submodule || '',
    wrongCount: item?.wrong_count || 0,
    lastWrongAt: item?.last_wrong_at || '',
    meta: `错 ${item?.wrong_count || 0} 次 · 最近：${formatDateTime(item?.last_wrong_at)}`,
    tags: tags.length ? tags : ['真实错题', '待补充标签']
  }
}

function buildReportView() {
  const items = abilityReport.value?.items || []
  if (!isAuthed.value || items.length === 0) {
    return {
      ...getReportMock(),
      items: []
    }
  }

  const sortedByWeakness = items.slice().sort((a, b) => Number(a.accuracy || 0) - Number(b.accuracy || 0))
  const weakItems = sortedByWeakness.filter((item) => Number(item.accuracy || 0) < 60).slice(0, 5)
  const metrics = items
    .slice()
    .sort((a, b) => b.total_count - a.total_count)
    .slice(0, 5)
    .map((item) => ({
      label: item.submodule || item.module,
      value: Math.round(Number(item.accuracy || 0))
    }))

  const weakNames = weakItems.map((item) => `${item.module}-${item.submodule}`).join('、')
  const diagnosis = weakItems.length
    ? `你在 ${weakNames} 的正确率较低，建议优先做同类题强化。先从 10 题小组练习开始，做完后回看错题解析。`
    : '目前没有明显低于 60% 的薄弱模块，整体状态不错。建议继续混合练习，保持题感并扩大覆盖面。'

  const tasks = (weakItems.length ? weakItems : sortedByWeakness).slice(0, 3).map((item) => ({
    title: `优先训练：${item.subject} - ${item.module}`,
    desc: `${item.submodule} 已做 ${item.total_count} 题，正确率 ${Math.round(Number(item.accuracy || 0))}%。${item.recommendation}`,
    action: '去练习',
    subject: item.subject,
    module: item.module,
    submodule: item.submodule
  }))

  return {
    metrics,
    diagnosis,
    tasks,
    items: sortedByWeakness
  }
}

function getMasteryLevel(accuracy) {
  const value = Number(accuracy || 0)
  if (value >= 80) return { key: 'good', label: '掌握良好', tone: 'green' }
  if (value >= 60) return { key: 'improving', label: '稳步提升', tone: 'blue' }
  if (value >= 40) return { key: 'weak', label: '待加强', tone: 'orange' }
  return { key: 'critical', label: '重点补强', tone: 'red' }
}

function getSubjectWeeklyChange(subject) {
  const items = Array.isArray(learningSummary.value?.subject_weekly_changes)
    ? learningSummary.value.subject_weekly_changes
    : []
  const item = items.find((entry) => entry?.subject === subject)
  const change = item?.accuracy_change
  if (change === null || change === undefined) {
    return { text: '本周对比积累中', tone: 'muted' }
  }
  if (change > 0) return { text: `↑ ${Math.abs(Math.round(change))}% 较上周`, tone: 'up' }
  if (change < 0) return { text: `↓ ${Math.abs(Math.round(change))}% 较上周`, tone: 'down' }
  return { text: '— 与上周持平', tone: 'muted' }
}

function getChangeTone(change) {
  if (change === null || change === undefined || Number(change) === 0) return 'muted'
  return Number(change) > 0 ? 'up' : 'down'
}

function formatAccuracyChange(change) {
  if (change === null || change === undefined || Number(change) === 0) return '—'
  return `${Number(change) > 0 ? '↑' : '↓'}${Math.abs(Math.round(Number(change)))}%`
}

function getSubjectSuggestion(subject, weakTopic, accuracy) {
  const focus = weakTopic || subject
  if (accuracy < 40) return `建议优先复盘 ${focus} 错题，再完成 10 题专项训练。`
  if (accuracy < 60) return `建议完成 20 题 ${focus} 专项巩固，及时复盘错题。`
  if (accuracy < 80) return `建议保持 ${focus} 的训练节奏，逐步提升稳定性。`
  return `当前掌握较好，建议穿插 ${focus} 练习保持题感。`
}

function getSafeError(error, fallback) {
  return error?.detail || error?.message || fallback
}

function buildFilterOptions(items, field, constraints = {}) {
  const values = items
    .filter((item) => {
      if (constraints.subject && item.subject !== constraints.subject) return false
      if (constraints.module && item.module !== constraints.module) return false
      return true
    })
    .map((item) => item[field])
    .filter(Boolean)
  return ['', ...Array.from(new Set(values))]
}

function toWrongFilterPickerOptions(values, allLabel) {
  return values.map((value) => ({
    value,
    label: value || allLabel
  }))
}

function getWrongFilterPickerIndex(options, value) {
  return Math.max(0, options.findIndex((item) => item.value === value))
}

function getWrongFilterPickerValue(event, options) {
  const option = options[Number(event?.detail?.value)] || options[0]
  return option?.value || ''
}

function onWrongSubjectPickerChange(event) {
  setWrongFilter('subject', getWrongFilterPickerValue(event, wrongSubjectPickerOptions.value))
}

function onWrongModulePickerChange(event) {
  setWrongFilter('module', getWrongFilterPickerValue(event, wrongModulePickerOptions.value))
}

function onWrongSubmodulePickerChange(event) {
  setWrongFilter('submodule', getWrongFilterPickerValue(event, wrongSubmodulePickerOptions.value))
}

function setWrongFilter(field, value) {
  if (wrongFilters.value[field] === value) return
  wrongFilters.value = {
    ...wrongFilters.value,
    [field]: value
  }
  if (field === 'subject') {
    wrongFilters.value.module = ''
    wrongFilters.value.submodule = ''
  }
  if (field === 'module') {
    wrongFilters.value.submodule = ''
  }
}

function resetMistakeVisibleCount() {
  visibleMistakeCount.value = 15
}

function loadMoreMistakes() {
  if (visibleMistakeCount.value < fullMistakes.value.length) {
    visibleMistakeCount.value += 15
    return
  }
  if (wrongHasMore.value) void loadWrongQuestions({ reset: false })
}

function handleMistakeBack() {
  if (retestMode.value) {
    confirmExitRetest()
    return
  }
  activeTab.value = 'profile'
}

async function openWrongDetail(item) {
  if (!isAuthed.value || !item?.id) {
    return
  }

  selectedWrongDetail.value = null
  reviewAnswer.value = ''
  reviewResultText.value = ''
  reviewMastered.value = false
  reviewSubmissionId.value = ''
  try {
    selectedWrongDetail.value = await fetchWrongQuestionDetail(item.id, { exam_code: examCode.value })
    reviewSubmissionId.value = createAnswerSubmissionId(getDetailQuestionId(selectedWrongDetail.value), 'review')
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '错题详情读取失败'), icon: 'none' })
  }
}

function closeWrongDetail() {
  selectedWrongDetail.value = null
  reviewAnswer.value = ''
  reviewResultText.value = ''
  reviewMastered.value = false
  reviewSubmissionId.value = ''
}

const wrongDetailOptions = computed(() => {
  return buildQuestionOptions(selectedWrongDetail.value?.question)
})

function buildQuestionOptions(question) {
  if (!question) return []
  return ['A', 'B', 'C', 'D']
    .map((key) => ({
      key,
      text: question[`option_${key.toLowerCase()}`] || ''
    }))
    .filter((option) => option.text)
}

function selectReviewAnswer(key) {
  if (reviewingWrong.value || reviewResultText.value) return
  reviewAnswer.value = key
}

function getWrongOptionClass(key) {
  const correct = selectedWrongDetail.value?.question?.answer
  return {
    selected: reviewAnswer.value === key,
    correct: reviewResultText.value && correct === key,
    wrong: reviewResultText.value && reviewAnswer.value === key && correct !== key
  }
}

function getDetailQuestionId(detail) {
  return detail?.question_id || detail?.question?.id || ''
}

function createAnswerSubmissionId(questionId, kind = 'review') {
  const normalizedId = String(questionId || '').trim()
  if (!normalizedId) return null
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}:${kind}:${normalizedId}`.slice(0, 120)
}

function getRetestSubmissionId(questionId) {
  const normalizedId = String(questionId || '').trim()
  if (!normalizedId) return null
  if (retestSubmissionIds.value[normalizedId]) {
    return retestSubmissionIds.value[normalizedId]
  }
  const nextId = createAnswerSubmissionId(normalizedId, 'retest')
  retestSubmissionIds.value = {
    ...retestSubmissionIds.value,
    [normalizedId]: nextId
  }
  return nextId
}

async function submitWrongReview() {
  if (!selectedWrongDetail.value || !reviewAnswer.value) {
    return
  }

  reviewingWrong.value = true
  try {
    const result = await reviewWrongQuestion({
      question_id: getDetailQuestionId(selectedWrongDetail.value),
      client_submission_id: reviewSubmissionId.value,
      selected_answer: reviewAnswer.value,
      used_time: 0,
      exam_code: examCode.value
    })
    reviewMastered.value = Boolean(result.is_correct)
    reviewResultText.value = result.is_correct ? '本次重做答对，已掌握。' : `本次仍需复盘，正确答案是 ${result.correct_answer}。`
    await loadLearningSummary()
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '重做提交失败'), icon: 'none' })
  } finally {
    reviewingWrong.value = false
  }
}

function shuffleMistakes(items) {
  const result = items.slice()
  for (let index = result.length - 1; index > 0; index -= 1) {
    const randomIndex = Math.floor(Math.random() * (index + 1))
    const current = result[index]
    result[index] = result[randomIndex]
    result[randomIndex] = current
  }
  return result
}

async function startWrongRetest() {
  if (!isAuthed.value) {
    uni.showToast({ title: '登录后才能重测错题', icon: 'none' })
    return
  }
  if (realMistakes.value.length === 0) {
    uni.showToast({ title: '当前还没有可重测的错题', icon: 'none' })
    return
  }
  if (retestCandidateMistakes.value.length === 0) {
    uni.showToast({ title: '当前筛选范围下没有可重测的错题', icon: 'none' })
    return
  }

  selectedWrongDetail.value = null
  retestItems.value = shuffleMistakes(retestCandidateMistakes.value)
  retestIndex.value = 0
  retestResults.value = []
  retestSubmissionIds.value = {}
  retestCompleted.value = false
  retestMode.value = true
  await loadRetestQuestion()
}

async function loadRetestQuestion() {
  const item = retestItems.value[retestIndex.value]
  if (!item?.id) {
    retestCompleted.value = true
    return
  }

  retestLoading.value = true
  retestDetail.value = null
  retestAnswer.value = ''
  retestResultText.value = ''
  try {
    retestDetail.value = await fetchWrongQuestionDetail(item.id, { exam_code: examCode.value })
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '重测题目读取失败'), icon: 'none' })
  } finally {
    retestLoading.value = false
  }
}

function selectRetestAnswer(key) {
  if (retestSubmitting.value || retestResultText.value) return
  retestAnswer.value = key
}

function getRetestOptionClass(key) {
  const correct = retestDetail.value?.question?.answer
  return {
    selected: retestAnswer.value === key,
    correct: retestResultText.value && correct === key,
    wrong: retestResultText.value && retestAnswer.value === key && correct !== key
  }
}

async function submitRetestAnswer() {
  if (!retestDetail.value || !retestAnswer.value || retestResultText.value) {
    return
  }

  retestSubmitting.value = true
  try {
    const result = await reviewWrongQuestion({
      question_id: getDetailQuestionId(retestDetail.value),
      client_submission_id: getRetestSubmissionId(getDetailQuestionId(retestDetail.value)),
      selected_answer: retestAnswer.value,
      used_time: 0,
      exam_code: examCode.value
    })
    const isCorrect = Boolean(result.is_correct)
    const correctAnswer = result.correct_answer || retestDetail.value?.question?.answer || ''
    retestResultText.value = isCorrect ? '本题答对，继续保持。' : `本题答错，正确答案是 ${correctAnswer}。`
    retestResults.value[retestIndex.value] = {
      question_id: getDetailQuestionId(retestDetail.value),
      selected_answer: retestAnswer.value,
      correct_answer: correctAnswer,
      is_correct: isCorrect
    }
    await loadLearningSummary()
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '重测提交失败'), icon: 'none' })
  } finally {
    retestSubmitting.value = false
  }
}

async function nextRetestQuestion() {
  if (retestIndex.value + 1 >= retestItems.value.length) {
    retestCompleted.value = true
    await loadWrongQuestions()
    await loadLearningSummary()
    return
  }
  retestIndex.value += 1
  await loadRetestQuestion()
}

function jumpRetestReview(index) {
  if (index < 0 || index >= retestItems.value.length) return
  retestCompleted.value = false
  retestIndex.value = index
  loadRetestQuestion()
}

function restartWrongRetest() {
  startWrongRetest()
}

function exitWrongRetest() {
  retestMode.value = false
  retestItems.value = []
  retestIndex.value = 0
  retestDetail.value = null
  retestAnswer.value = ''
  retestResultText.value = ''
  retestResults.value = []
  retestSubmissionIds.value = {}
  retestLoading.value = false
  retestCompleted.value = false
  loadWrongQuestions()
  loadLearningSummary()
}

function confirmExitRetest() {
  uni.showModal({
    title: '退出重测？',
    content: '本轮重测进度不会继续保存，但已经提交的题目会同步到错题统计。',
    confirmText: '退出',
    cancelText: '继续做题',
    success: (res) => {
      if (res.confirm) {
        exitWrongRetest()
      }
    }
  })
}

function levelClass(level) {
  return {
    stable: level === '稳定',
    normal: level === '一般',
    weak: level === '薄弱',
    critical: level === '重点补强'
  }
}

function formatDateTime(value) {
  if (!value) {
    return '暂无'
  }
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) {
    return String(value).slice(0, 10)
  }
  return `${date.getMonth() + 1}/${date.getDate()} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

</script>

<style scoped>
.home-page {
  box-sizing: border-box;
  width: 100%;
  max-width: 100vw;
  min-height: 100vh;
  min-height: 100dvh;
  overflow-x: hidden;
  overflow-x: clip;
  padding: calc(env(safe-area-inset-top) + 16rpx) 22rpx calc(env(safe-area-inset-bottom) + 124px);
}

.home-page.profile-function-page {
  padding-top: 0;
}

.home-detail-route-page {
  position: fixed !important;
  inset: 0;
  z-index: 50 !important;
  box-sizing: border-box;
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior-y: contain;
  -webkit-overflow-scrolling: touch;
  padding: 0 22rpx calc(env(safe-area-inset-bottom) + 36rpx);
  background: var(--gyt-page-bg, #fbfcff);
}

.home-page.circle-glass-page {
  --circle-bg: #e6eceb;
  --circle-bg-muted: #dce6e7;
  --circle-card: #fbfcfb;
  --circle-card-muted: #f4f7f5;
  --circle-card-border: rgba(255, 255, 255, 0.88);
  --circle-line: rgba(49, 76, 84, 0.12);
  --circle-text: #1c2423;
  --circle-muted: #657473;
  --circle-brand: #16786f;
  --circle-brand-soft: rgba(22, 120, 111, 0.13);
  --circle-mint: #3d9c90;
  --circle-mint-soft: rgba(61, 156, 144, 0.13);
  --circle-radius-card: 30px;
  --circle-radius-control: 20px;
  --circle-screen-gutter: 16px;
  --circle-space: 12px;
  --circle-shadow: 0 16px 38px rgba(30, 55, 56, 0.1);
  --circle-glass-surface: rgba(250, 253, 252, 0.46);
  --circle-glass-surface-strong: rgba(249, 252, 251, 0.62);
  --circle-glass-border: rgba(255, 255, 255, 0.58);
  --circle-glass-card: rgba(251, 253, 252, 0.58);
  --circle-glass-card-mint: rgba(240, 248, 245, 0.58);
  --circle-glass-control: rgba(248, 251, 250, 0.42);
  --circle-glass-selected: rgba(225, 242, 237, 0.62);
  --circle-glass-active: rgba(255, 255, 255, 0.48);
  --circle-glass-blur: 20px;
  --circle-glass-press: 0.98;
  --circle-insight-slide-gap: 8px;
  --circle-insight-slide-offset: 4px;
  --circle-tab-bg: rgba(247, 250, 249, 0.38);
  --circle-tab-shadow: 0 14px 34px rgba(30, 55, 56, 0.16);
  --circle-font: var(--gyt-app-font);
  position: relative;
  isolation: isolate;
  overflow-x: clip;
  padding: calc(env(safe-area-inset-top) + 16px) 16px calc(env(safe-area-inset-bottom) + 124px);
  background: #416d6e;
  color: var(--circle-text);
  font-family: var(--circle-font);
}

/* App 端的页面内容与固定研圈标题栏共用同一套状态栏高度，避免首屏内容落入安全区。 */
/* #ifdef APP-PLUS */
.home-page.circle-glass-page {
  padding-top: calc(var(--status-bar-height, env(safe-area-inset-top)) + 16px);
}
/* #endif */

.home-page.circle-glass-page::before {
  content: '';
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background:
    linear-gradient(180deg, rgba(10, 41, 42, 0.22) 0%, rgba(18, 49, 49, 0.12) 48%, rgba(18, 43, 43, 0.32) 100%),
    url('/static/circle-study-sky.jpg') center center / cover no-repeat;
  filter: saturate(84%) contrast(90%);
}

.circle-glass-page .circle-dashboard,
.circle-glass-page :deep(.icp-footer) {
  position: relative;
  z-index: 1;
}

:deep(.icp-footer.is-route-obscured) {
  visibility: hidden;
  pointer-events: none;
}

/* 首页沿用研圈的背景，但维持资讯门户所需的阅读对比度。 */
.landing-glass-page::before {
  background:
    linear-gradient(180deg, rgba(224, 236, 232, 0.82) 0%, rgba(237, 245, 242, 0.8) 50%, rgba(221, 234, 229, 0.84) 100%),
    url('/static/circle-study-sky.jpg') center center / cover no-repeat;
  filter: saturate(62%) contrast(86%) blur(1px);
  transform: scale(1.015);
}

.landing-glass-page .landing-dashboard {
  position: relative;
  z-index: 1;
}

.landing-glass-page .home-header {
  padding-right: 4rpx;
  padding-left: 4rpx;
}

.landing-glass-page .home-header-copy,
.landing-glass-page .home-status-pill,
.landing-glass-page .message-bell,
.landing-glass-page .profile-entry {
  border: 1rpx solid var(--circle-glass-border, rgba(255, 255, 255, 0.58));
  background: rgba(248, 251, 250, 0.38);
  box-shadow: 0 10rpx 24rpx rgba(30, 55, 56, 0.09);
  -webkit-backdrop-filter: blur(16px) saturate(118%);
  backdrop-filter: blur(16px) saturate(118%);
}

.landing-glass-page .home-header-copy {
  padding: 14rpx 16rpx 16rpx;
  border-radius: 28rpx;
  background: rgba(248, 251, 250, 0.26);
}

.landing-glass-page .home-header-title {
  color: #1d4f4b;
}

.landing-glass-page .home-status-label {
  color: rgba(45, 61, 59, 0.72);
}

.landing-glass-page .home-status-pill {
  border-color: rgba(255, 255, 255, 0.62);
  background: rgba(248, 251, 250, 0.5);
}

.landing-glass-page .home-status-value {
  color: #16786f;
}

.landing-glass-page .message-bell {
  color: #2d3d3b;
  border: 0;
  background: transparent;
  background-color: transparent !important;
  box-shadow: none;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
  -webkit-appearance: none;
  appearance: none;
}

.landing-glass-page .profile-entry {
  color: #16786f;
}

.landing-glass-page .landing-focus-swiper {
  box-shadow: none;
}

.landing-glass-page .landing-focus-slide {
  border: 1rpx solid var(--circle-glass-border, rgba(255, 255, 255, 0.68));
  box-shadow: none;
  -webkit-backdrop-filter: blur(16px) saturate(118%);
  backdrop-filter: blur(16px) saturate(118%);
}

.landing-glass-page .landing-focus-slide.is-blue {
  background: linear-gradient(135deg, rgba(44, 104, 119, 0.82), rgba(70, 145, 146, 0.74));
}

.landing-glass-page .landing-focus-slide.is-violet {
  background: linear-gradient(135deg, rgba(88, 76, 144, 0.82), rgba(126, 103, 174, 0.74));
}

.landing-glass-page .landing-focus-slide.is-mint {
  background: linear-gradient(135deg, rgba(31, 112, 104, 0.84), rgba(83, 165, 145, 0.74));
}

.landing-glass-page .landing-focus-art {
  border-color: rgba(255, 255, 255, 0.56);
  background: rgba(249, 252, 251, 0.82);
  box-shadow: 0 14rpx 28rpx rgba(30, 55, 56, 0.16);
}

.landing-glass-page .landing-focus-art-card {
  border-color: rgba(22, 120, 111, 0.14);
  color: #16786f;
}

.landing-glass-page .landing-focus-art-label {
  color: #597470;
}

.landing-glass-page .landing-focus-art-line {
  background: #dbece8;
}

.landing-glass-page .landing-focus-dot {
  background: rgba(255, 255, 255, 0.5);
  box-shadow: 0 3rpx 8rpx rgba(30, 55, 56, 0.08);
}

.landing-glass-page .landing-focus-dot.active {
  background: #16786f;
}

.landing-glass-page .landing-section-title {
  color: #1c2423;
}

.landing-glass-page .landing-more-button {
  color: #16786f;
}

.landing-glass-page .landing-news-card {
  border-color: var(--circle-glass-border, rgba(255, 255, 255, 0.72));
  background: rgba(249, 252, 251, 0.66);
  box-shadow: 0 12rpx 28rpx rgba(30, 55, 56, 0.085);
  -webkit-backdrop-filter: blur(18px) saturate(118%);
  backdrop-filter: blur(18px) saturate(118%);
}

.landing-glass-page .landing-news-source {
  color: #16786f;
}

.landing-glass-page .landing-news-title {
  color: #1f2b2a;
}

.landing-glass-page .landing-news-date {
  color: #71817f;
}

.landing-glass-page .landing-news-cover {
  border: 1rpx solid rgba(255, 255, 255, 0.58);
  box-shadow: inset 0 1rpx 0 rgba(255, 255, 255, 0.55);
}

.landing-glass-page .landing-service-card {
  border-color: var(--circle-glass-border, rgba(255, 255, 255, 0.7));
  box-shadow: 0 10rpx 24rpx rgba(30, 55, 56, 0.075);
  -webkit-backdrop-filter: blur(17px) saturate(116%);
  backdrop-filter: blur(17px) saturate(116%);
}

.landing-glass-page .landing-service-card.is-school {
  background: rgba(241, 248, 251, 0.58);
}

.landing-glass-page .landing-service-card.is-major {
  background: rgba(247, 244, 252, 0.58);
}

.landing-glass-page .landing-service-card.is-guide {
  background: rgba(241, 250, 247, 0.58);
}

.landing-glass-page .landing-service-card.is-school .landing-service-icon {
  background: transparent;
  box-shadow: none;
}

.landing-glass-page .landing-service-card.is-major .landing-service-icon {
  background: transparent;
  box-shadow: none;
}

.landing-glass-page .landing-service-card.is-guide .landing-service-icon {
  background: transparent;
  box-shadow: none;
}

.landing-glass-page .landing-service-title {
  color: #263937;
}

.landing-glass-page :deep(.icp-footer.inline),
.landing-glass-page :deep(.icp-footer.inline .icp-link) {
  color: #657875;
}

.landing-glass-page :deep(.tabbar.glass) {
  border-color: rgba(255, 255, 255, 0.7);
  background: rgba(247, 251, 250, 0.46);
  box-shadow: 0 14px 34px rgba(30, 55, 56, 0.15);
}


/* 方案一：将研圈玻璃质感延展到首页、刷题、报告和我的的主卡片。 */
.glass-theme-page > view:not(.tabbar):not(.official-modal-mask):not(.mentor-filter-mask):not(.subscription-sheet-mask) {
  position: relative;
  z-index: 1;
}

.glass-theme-page:not(.landing-glass-page) .welcome-card,
.glass-theme-page:not(.landing-glass-page) .stats-card,
.glass-theme-page:not(.landing-glass-page) :deep(.module-card),
.glass-theme-page:not(.landing-glass-page) .mock-exam-card,
.glass-theme-page:not(.landing-glass-page) .subject-report-card,
.glass-theme-page:not(.landing-glass-page) .learning-advice-card,
.glass-theme-page:not(.landing-glass-page) .account-card,
.glass-theme-page:not(.landing-glass-page) .member-card,
.glass-theme-page:not(.landing-glass-page) .profile-section-card,
.glass-theme-page:not(.landing-glass-page) .logout-card,
.glass-theme-page:not(.landing-glass-page) :deep(.section-card) {
  border-color: var(--circle-glass-border, rgba(255, 255, 255, 0.66));
  background: rgba(250, 253, 252, 0.62);
  box-shadow: 0 16rpx 38rpx rgba(30, 55, 56, 0.11);
  -webkit-backdrop-filter: blur(18px) saturate(118%);
  backdrop-filter: blur(18px) saturate(118%);
}

.glass-theme-page:not(.landing-glass-page) .stats-card,
.glass-theme-page:not(.landing-glass-page) :deep(.module-card) .divider,
.glass-theme-page:not(.landing-glass-page) .stat-divider,
.glass-theme-page:not(.landing-glass-page) .menu-row {
  border-color: rgba(255, 255, 255, 0.44);
}

.glass-theme-page:not(.landing-glass-page) .stats-card,
.glass-theme-page:not(.landing-glass-page) .member-card.active {
  background: rgba(249, 253, 252, 0.56);
}

.glass-theme-page:not(.landing-glass-page) .welcome-title,
.glass-theme-page:not(.landing-glass-page) .mock-exam-title,
.glass-theme-page:not(.landing-glass-page) .account-name,
.glass-theme-page:not(.landing-glass-page) .member-title,
.glass-theme-page:not(.landing-glass-page) .profile-section-title {
  color: #1c2423;
}

.glass-theme-page:not(.landing-glass-page) .welcome-subtitle,
.glass-theme-page:not(.landing-glass-page) .mock-exam-sub,
.glass-theme-page:not(.landing-glass-page) .account-desc,
.glass-theme-page:not(.landing-glass-page) .member-subtitle,
.glass-theme-page:not(.landing-glass-page) .stat-label {
  color: #657473;
}

@supports not (backdrop-filter: blur(1px)) {
  .landing-glass-page .landing-news-card,
  .landing-glass-page .landing-service-card,
  .glass-theme-page:not(.landing-glass-page) .welcome-card,
  .glass-theme-page:not(.landing-glass-page) .stats-card,
  .glass-theme-page:not(.landing-glass-page) .mock-exam-card,
  .glass-theme-page:not(.landing-glass-page) .subject-report-card,
  .glass-theme-page:not(.landing-glass-page) .learning-advice-card,
  .glass-theme-page:not(.landing-glass-page) .account-card,
  .glass-theme-page:not(.landing-glass-page) .member-card,
  .glass-theme-page:not(.landing-glass-page) .profile-section-card,
  .glass-theme-page:not(.landing-glass-page) .logout-card {
    background: #f8fbfa;
  }
}

.home-page.no-tab-page {
  padding-bottom: calc(env(safe-area-inset-bottom) + 36rpx);
}

.home-page.landing-home-page {
  height: 100vh;
  height: 100dvh;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  overscroll-behavior-y: none;
}

.home-dashboard {
  box-sizing: border-box;
  width: 100%;
  max-width: 760rpx;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  overflow-x: hidden;
}

.landing-dashboard {
  box-sizing: border-box;
  width: 100%;
  max-width: 760rpx;
  min-height: 0;
  flex: 1 1 auto;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
  overflow: hidden;
}

/* #ifdef H5 */
.landing-dashboard :deep(.icp-footer.inline) {
  flex: none;
}
/* #endif */

.home-dashboard view,
.home-dashboard text,
.home-dashboard button,
.home-dashboard scroll-view {
  box-sizing: border-box;
}

.landing-dashboard view,
.landing-dashboard text,
.landing-dashboard button,
.landing-dashboard swiper,
.landing-dashboard swiper-item {
  box-sizing: border-box;
}

.landing-focus-block {
  --landing-focus-slide-gap: 8px;
  --landing-focus-slide-offset: 4px;

  display: flex;
  flex-direction: column;
  flex: none;
  gap: 8rpx;
}

.landing-focus-swiper {
  width: calc(100% + var(--landing-focus-slide-gap));
  min-height: 0;
  height: clamp(190rpx, 16dvh, 236rpx);
  flex: none;
  margin-left: calc(0px - var(--landing-focus-slide-offset));
}

.landing-focus-swiper swiper-item,
.landing-focus-swiper .landing-focus-slide {
  box-sizing: border-box;
  height: 100%;
}

.landing-focus-slide {
  position: relative;
  box-sizing: border-box;
  width: calc(100% - var(--landing-focus-slide-gap));
  height: 100%;
  margin: 0 var(--landing-focus-slide-offset);
  padding: 22rpx 28rpx;
  border-radius: 34rpx;
  overflow: hidden;
  color: #ffffff;
  display: flex;
  align-items: stretch;
  box-shadow: none;
}

.landing-focus-slide::before,
.landing-focus-slide::after {
  content: '';
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
}

.landing-focus-slide::before {
  right: -62rpx;
  top: -84rpx;
  width: 266rpx;
  height: 266rpx;
  background: rgba(255, 255, 255, 0.1);
}

.landing-focus-slide::after {
  right: 126rpx;
  bottom: -84rpx;
  width: 164rpx;
  height: 164rpx;
  background: rgba(255, 255, 255, 0.08);
}

.landing-focus-slide.is-blue {
  background: linear-gradient(135deg, #307cf4 0%, #5795f5 56%, #779ff6 100%);
}

.landing-focus-slide.is-violet {
  background: linear-gradient(135deg, #725bc9 0%, #8c70df 54%, #ae94ee 100%);
}

.landing-focus-slide.is-mint {
  background: linear-gradient(135deg, #177e85 0%, #32a6a3 55%, #69c6b8 100%);
}

.landing-focus-copy {
  position: relative;
  z-index: 1;
  max-width: calc(100% - 178rpx);
  display: flex;
  flex-direction: column;
  align-self: stretch;
  padding: 2rpx 0;
}

.landing-focus-copy-main {
  display: flex;
  flex-direction: column;
  gap: 9rpx;
  margin-top: 20rpx;
}

.landing-focus-badge {
  align-self: flex-start;
  padding: 7rpx 12rpx;
  border: 1rpx solid rgba(255, 255, 255, 0.34);
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.15);
  color: #ffffff;
  font-size: 19rpx;
  line-height: 1.2;
  font-weight: 800;
}

.landing-focus-title {
  color: #ffffff;
  font-size: 32rpx;
  line-height: 1.24;
  font-weight: 900;
}

.landing-focus-subtitle {
  color: rgba(255, 255, 255, 0.84);
  font-size: 22rpx;
  line-height: 1.45;
  font-weight: 600;
}

.landing-focus-art {
  position: absolute;
  z-index: 1;
  right: 28rpx;
  top: 50%;
  width: 126rpx;
  height: 150rpx;
  padding: 11rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.32);
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 14rpx 24rpx rgba(10, 47, 108, 0.16);
  transform: translateY(-50%) rotate(6deg);
}

.landing-focus-art-card {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  padding: 13rpx 11rpx;
  border: 2rpx solid rgba(32, 93, 184, 0.12);
  border-radius: 12rpx;
  color: #2d73d9;
  display: flex;
  flex-direction: column;
  gap: 9rpx;
}

.landing-focus-art-year {
  font-size: 27rpx;
  line-height: 1;
  font-weight: 900;
}

.landing-focus-art-label {
  color: #5575a7;
  font-size: 17rpx;
  line-height: 1.3;
  font-weight: 800;
}

.landing-focus-art-line {
  width: 100%;
  height: 7rpx;
  border-radius: 999rpx;
  background: #dce9fc;
}

.landing-focus-art-line.short {
  width: 62%;
}

.landing-focus-pagination {
  display: flex;
  justify-content: center;
  gap: 10rpx;
}

.landing-focus-dot {
  width: 13rpx;
  min-width: 13rpx;
  height: 13rpx;
  min-height: 13rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 999rpx;
  background: #d3dceb;
  transition: width 180ms ease, background-color 180ms ease;
}

.landing-focus-dot::after,
.landing-more-button::after,
.landing-service-card::after {
  border: 0;
}

.landing-focus-dot.active {
  width: 34rpx;
  background: var(--gyt-primary, #3478f6);
}

.landing-section {
  flex: none;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.landing-section-heading {
  min-height: 52rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 0 4rpx;
}

.landing-section-heading > view {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 7rpx;
}

.landing-section-title {
  color: #182235;
  font-size: 32rpx;
  line-height: 1.1;
  font-weight: 900;
}

.landing-more-button {
  min-height: 52rpx;
  margin: 0;
  padding: 0 4rpx;
  border: 0;
  background: transparent;
  color: var(--gyt-primary, #3478f6);
  font-size: 23rpx;
  line-height: 1;
  font-weight: 800;
  white-space: nowrap;
}

.landing-more-button text {
  margin-left: 2rpx;
  font-size: 34rpx;
  font-weight: 500;
  vertical-align: -2rpx;
}

.landing-news-list {
  min-height: 0;
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.landing-news-card {
  min-height: 132rpx;
  flex: 1 1 0;
  height: auto;
  padding: 12rpx 14rpx;
  border: 2rpx solid #e7edf7;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 12rpx 30rpx rgba(30, 55, 93, 0.06);
  display: flex;
  align-items: center;
  gap: 14rpx;
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.landing-news-card:active,
.landing-service-card:active {
  transform: scale(0.985);
}

.landing-news-copy {
  min-width: 0;
  flex: 1;
  padding-top: 2rpx;
  display: flex;
  flex-direction: column;
  gap: 7rpx;
}

.landing-news-source {
  color: var(--gyt-primary, #3478f6);
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 800;
}

.landing-news-title {
  overflow: hidden;
  color: #263044;
  font-size: 23rpx;
  line-height: 1.34;
  font-weight: 800;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.landing-news-date {
  margin-top: auto;
  color: #98a2b3;
  font-size: 19rpx;
  line-height: 1.2;
  font-weight: 600;
}

.landing-news-cover {
  box-sizing: border-box;
  width: 146rpx;
  min-width: 146rpx;
  height: 108rpx;
  flex: 0 0 auto;
  padding: 10rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.landing-news-cover.is-blue {
  background: linear-gradient(145deg, #e3efff, #bcd5ff);
}

.landing-news-cover.is-orange {
  background: linear-gradient(145deg, #fff0dc, #f8cc8c);
}

.landing-news-cover.is-mint {
  background: linear-gradient(145deg, #dff6ef, #a9dfcd);
}

.landing-news-document {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  padding: 9rpx;
  border-radius: 10rpx;
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 8rpx 18rpx rgba(37, 72, 117, 0.12);
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  overflow: hidden;
}

.landing-news-document-top {
  color: #5276ac;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4rpx;
  font-size: 14rpx;
  line-height: 1.1;
  font-weight: 800;
}

.landing-news-document-top text:last-child {
  color: #95a7c0;
  font-size: 12rpx;
}

.landing-news-document-title {
  color: #32466c;
  font-size: 18rpx;
  line-height: 1.32;
  font-weight: 900;
}

.landing-news-document-lines {
  display: flex;
  flex-direction: column;
  gap: 5rpx;
}

.landing-news-document-lines view {
  width: 100%;
  height: 4rpx;
  border-radius: 999rpx;
  background: #dfe7f2;
}

.landing-news-document-lines view:nth-child(2) {
  width: 82%;
}

.landing-news-document-lines view:nth-child(3) {
  width: 66%;
}

.landing-service-grid {
  flex: none;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
}

.landing-news-section {
  min-height: 0;
  flex: 1 1 0;
}

.landing-services-section {
  flex: none;
  margin-top: 0;
}

.landing-service-card {
  position: relative;
  min-width: 0;
  min-height: 0;
  height: clamp(140rpx, 12dvh, 180rpx);
  margin: 0;
  padding: 16rpx 16rpx 14rpx;
  border: 2rpx solid transparent;
  border-radius: 26rpx;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: center;
  gap: 0;
  overflow: hidden;
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.landing-service-card.is-school {
  border-color: rgba(229, 226, 224, .94);
  background: rgba(255, 255, 255, .94);
}

.landing-service-card.is-major {
  border-color: rgba(229, 226, 224, .94);
  background: rgba(255, 255, 255, .94);
}

.landing-service-card.is-guide {
  border-color: rgba(229, 226, 224, .94);
  background: rgba(255, 255, 255, .94);
}

.landing-service-icon {
  width: 52rpx;
  height: 52rpx;
  margin: 0 auto;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gyt-primary, #3478f6);
  font-size: 25rpx;
  line-height: 1;
  font-weight: 900;
  overflow: hidden;
}

.landing-service-icon-image {
  display: block;
  width: 100%;
  height: 100%;
  transform: scale(1.62);
  transform-origin: center;
}

.landing-service-card.is-school .landing-service-icon {
  color: #377ce7;
}

.landing-service-card.is-major .landing-service-icon {
  color: #7759c7;
}

.landing-service-card.is-guide .landing-service-icon {
  color: #2a9b78;
}

.landing-service-row {
  position: relative;
  width: 100%;
  min-width: 0;
  min-height: 28rpx;
  margin-top: 16rpx;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.landing-service-title {
  display: block;
  width: 100%;
  color: #273149;
  font-size: 22rpx;
  line-height: 1.2;
  font-weight: 900;
  text-align: center;
  white-space: nowrap;
}

@media (max-width: 600px) and (max-height: 900px) {
  .landing-dashboard {
    gap: 14rpx;
  }

  .landing-focus-swiper {
    height: clamp(190rpx, 16dvh, 236rpx);
  }

  .landing-focus-slide {
    height: 100%;
  }

  .landing-focus-slide {
    padding: 18rpx 24rpx;
  }

  .landing-focus-copy {
    padding-top: 2rpx;
  }

  .landing-focus-copy-main {
    gap: 7rpx;
    margin-top: 16rpx;
  }

  .landing-focus-title {
    font-size: 29rpx;
  }

  .landing-focus-art {
    right: 22rpx;
    top: 50%;
    width: 114rpx;
    height: 138rpx;
  }

  .landing-section {
    gap: 10rpx;
  }

  .landing-section-heading {
    min-height: 48rpx;
  }

  .landing-news-card {
    min-height: 136rpx;
    height: auto;
    padding: 10rpx 12rpx;
  }

  .landing-news-title {
    font-size: 21rpx;
  }

  .landing-news-cover {
    width: 132rpx;
    min-width: 132rpx;
    height: 96rpx;
    padding: 8rpx;
  }

  .landing-service-card {
    padding: 10rpx 8rpx;
  }

  .landing-service-icon {
    width: 48rpx;
    height: 48rpx;
    font-size: 21rpx;
  }

  .landing-service-row {
    margin-top: 14rpx;
  }

}

@media (max-width: 600px) and (max-height: 760px) {
  .landing-news-section,
  .landing-news-list,
  .landing-news-card {
    flex: none;
  }

  .landing-news-card {
    min-height: 0;
    height: clamp(136rpx, 9.2dvh, 160rpx);
  }

  .landing-services-section {
    margin-top: auto;
  }
}

@media (max-width: 350px) {
  .landing-focus-slide {
    padding-right: 22rpx;
    padding-left: 22rpx;
  }

  .landing-focus-copy {
    max-width: calc(100% - 158rpx);
  }

  .landing-focus-title {
    font-size: 31rpx;
  }

  .landing-focus-art {
    right: 18rpx;
    width: 108rpx;
  }

  .landing-news-card {
    gap: 10rpx;
    padding: 11rpx;
  }

  .landing-news-cover {
    width: 122rpx;
    min-width: 122rpx;
  }

  .landing-service-card {
    padding-right: 8rpx;
    padding-left: 8rpx;
  }

  .landing-service-title {
    font-size: 23rpx;
  }
}

.circle-dashboard {
  box-sizing: border-box;
  width: 100%;
  max-width: 860rpx;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 0;
  overflow-x: hidden;
}

.circle-view-stage {
  position: relative;
  width: 100%;
  min-width: 0;
  isolation: isolate;
  contain: paint;
  overflow-x: hidden;
  overflow-x: clip;
}

.circle-view-panel {
  position: relative;
  width: 100%;
  min-width: 0;
  isolation: isolate;
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
  transform: translateZ(0);
}

/* #ifdef APP-PLUS */
/* App 端直接切换页面节点，避免 swiper/canvas 原生层被 transform/contain 留在新页面上方。 */
.circle-view-stage {
  isolation: auto;
  contain: none;
  overflow-x: hidden;
}

.circle-view-panel {
  isolation: auto;
  -webkit-backface-visibility: visible;
  backface-visibility: visible;
  transform: none;
}
/* #endif */

.circle-detail-route-layer {
  position: fixed;
  inset: 0;
  z-index: 24;
  box-sizing: border-box;
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  min-height: 0;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  isolation: isolate;
  background:
    linear-gradient(180deg, rgba(10, 41, 42, 0.22) 0%, rgba(18, 49, 49, 0.12) 48%, rgba(18, 43, 43, 0.32) 100%),
    url('/static/circle-study-sky.jpg') center center / cover no-repeat;
}

.circle-detail-route-layer.is-route-moving {
  pointer-events: none;
  transform: translate3d(0, 0, 0);
  transition: transform var(--gyt-route-duration, 380ms) var(--gyt-route-ease, cubic-bezier(0.25, 0.8, 0.25, 1));
  will-change: transform;
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
}

.circle-detail-route-layer.is-route-moving.is-route-offscreen {
  transform: translate3d(100%, 0, 0);
}

.circle-detail-route-layer.is-community-reader-underlay {
  pointer-events: none;
}

.circle-detail-route-layer.is-route-dragging,
.circle-detail-route-layer.is-route-settling {
  box-shadow: -18rpx 0 42rpx rgba(17, 31, 47, 0.2);
  -webkit-user-select: none;
  user-select: none;
}

.circle-detail-route-layer.is-route-dragging {
  touch-action: none;
}

/* #ifdef APP-PLUS */
/* App 端使用位置动画，避免 transform 祖先影响详情内的 scroll-view/canvas 原生层。 */
.circle-detail-route-layer.is-route-moving {
  right: auto;
  left: 0;
  transform: none;
  transition: left var(--gyt-route-duration, 380ms) var(--gyt-route-ease, cubic-bezier(0.25, 0.8, 0.25, 1));
  will-change: left;
}

.circle-detail-route-layer.is-route-moving.is-route-offscreen {
  left: 100vw;
  transform: none;
}

/* 考研圈等纯 DOM 详情使用合成层位移动画，避免 left 动画逐帧触发布局与重绘。 */
.circle-detail-route-layer.is-route-moving.is-route-compositor-safe {
  right: 0;
  left: 0;
  transform: translate3d(0, 0, 0);
  transition: transform var(--gyt-route-duration, 380ms) var(--gyt-route-ease, cubic-bezier(0.25, 0.8, 0.25, 1));
  will-change: transform;
}

.circle-detail-route-layer.is-route-moving.is-route-compositor-safe.is-route-offscreen {
  left: 0;
  transform: translate3d(100%, 0, 0);
}
/* #endif */

.circle-themed-page .circle-detail-route-layer {
  background: var(--gyt-page-bg, #f4f8ff);
}

.circle-detail-route-scroll {
  width: 100%;
  height: 0;
  min-height: 0;
  flex: 1;
}

.circle-detail-route-content {
  box-sizing: border-box;
  width: 100%;
  max-width: 860rpx;
  min-height: 100%;
  margin: 0 auto;
  padding: 18rpx 22rpx calc(env(safe-area-inset-bottom) + 36rpx);
}

.circle-dashboard view,
.circle-dashboard text,
.circle-dashboard button,
.circle-dashboard scroll-view {
  box-sizing: border-box;
}

.circle-overview,
.circle-detail-page {
  display: flex;
  flex-direction: column;
  gap: var(--circle-space, 32rpx);
}

.circle-overview {
  min-height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 124px);
  min-height: calc(100dvh - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 124px);
}

.circle-overview.is-app-route-underlay {
  pointer-events: none;
  contain: layout paint;
  will-change: transform, opacity;
}

.circle-overview.is-app-route-underlay .circle-glass-surface,
.circle-overview.is-app-route-underlay .circle-entry {
  -webkit-backdrop-filter: none !important;
  backdrop-filter: none !important;
}

.home-page :deep(.tabbar.is-circle-route-underlay-tab) {
  background: rgba(255, 255, 255, 0.72);
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
  transition: none;
}

/* 详情层必须与根导航处于同一堆叠上下文：静止时盖住导航，离场时从下方自然露出。 */
.home-page.circle-detail-active > .circle-dashboard {
  z-index: auto !important;
}

.home-page.circle-detail-active .circle-view-stage {
  isolation: auto;
  contain: none;
}

.circle-trend-card {
  min-height: 176px;
  padding: 16px 16px 14px;
  border: 1px solid var(--circle-card-border, rgba(255, 255, 255, 0.62));
  border-radius: var(--circle-radius-card, 24px);
  background: var(--circle-card, rgba(255, 255, 255, 0.8));
  box-shadow: none;
  overflow: hidden;
  isolation: isolate;
  flex-shrink: 0;
}

.circle-trend-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.circle-trend-title {
  min-width: 0;
  color: var(--circle-text, #1d1d1f);
  font-size: 26px;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 0;
  white-space: nowrap;
}

.circle-trend-peak {
  margin-left: auto;
  display: inline-flex;
  align-items: baseline;
  color: var(--circle-muted, #718096);
  font-size: 14px;
  line-height: 1.35;
  font-weight: 500;
  white-space: nowrap;
}

.circle-trend-peak-value {
  margin: 0 2px;
  color: var(--circle-brand, #5b8fdf);
  font-weight: 700;
}

.circle-trend-chart {
  position: relative;
  height: 110px;
  margin-top: 10px;
}

.circle-trend-state {
  height: 110px;
  margin-top: 10px;
  color: var(--circle-muted, #718096);
  font-size: 13px;
  line-height: 1.55;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.circle-trend-state.is-error {
  flex-direction: column;
  gap: 10px;
  color: #b66b24;
}

.circle-trend-state button {
  min-width: 88px;
  height: 30px;
  margin: 0;
  padding: 0 12px;
  border: 0;
  border-radius: 999px;
  background: var(--circle-brand-soft, #edf4ff);
  color: var(--circle-brand, #5b8fdf);
  font-size: 12px;
  line-height: 30px;
  font-weight: 700;
}

.circle-trend-state button::after {
  border: 0;
}

.circle-trend-grid,
.circle-trend-axis {
  position: absolute;
  top: 9px;
  bottom: 23px;
}

.circle-trend-grid {
  left: 28px;
  right: 0;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.circle-trend-grid-line {
  width: 100%;
  border-top: 1px solid var(--circle-line, rgba(128, 147, 171, 0.16));
}

.circle-trend-axis {
  left: 0;
  width: 23px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: var(--circle-muted, #718096);
  font-size: 11px;
  line-height: 1;
  font-weight: 500;
}

.circle-trend-axis text {
  transform: translateY(-50%);
}

.circle-trend-axis text:last-child {
  transform: translateY(50%);
}

.circle-trend-bars {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 0;
  left: 28px;
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  column-gap: 5px;
}

.circle-trend-column {
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.circle-trend-bar-space {
  width: 100%;
  flex: 1;
  padding: 13px 0 14px;
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.circle-trend-bar {
  position: relative;
  width: 10px;
  min-height: 6px;
  border-radius: 999rpx;
  background: linear-gradient(180deg, #9bd5c9 0%, var(--circle-mint, #74bdad) 100%);
}

.circle-trend-bar.latest {
  background: linear-gradient(180deg, #b6e5dc 0%, #83cabc 100%);
}

.circle-trend-bar.empty {
  min-height: 0;
}

.circle-trend-value {
  position: absolute;
  left: 50%;
  bottom: calc(100% + 5px);
  transform: translateX(-50%);
  color: var(--circle-text, #1d1d1f);
  font-size: 11px;
  line-height: 1;
  font-weight: 600;
  white-space: nowrap;
}

.circle-trend-day {
  height: 12px;
  color: var(--circle-muted, #718096);
  font-size: 11px;
  line-height: 12px;
  font-weight: 500;
  white-space: nowrap;
}

.circle-entry-list {
  min-height: 0;
  flex: 0 0 auto;
  display: grid;
  grid-template-rows: repeat(4, 112px);
  gap: var(--circle-space, 16px);
}

.circle-entry {
  width: 100%;
  min-height: 0;
  height: 100%;
  margin: 0;
  padding: 12px 20px;
  border: 1px solid var(--circle-card-border, rgba(255, 255, 255, 0.62));
  border-radius: var(--circle-radius-card, 24px);
  background: var(--circle-entry-bg, var(--circle-card, rgba(255, 255, 255, 0.8)));
  display: flex;
  align-items: center;
  gap: 14px;
  box-shadow: none;
  overflow: hidden;
  isolation: isolate;
  text-align: left;
}

.circle-entry:nth-child(1) {
  --circle-entry-bg: rgba(255, 255, 255, 0.62);
  --circle-entry-icon-bg: rgba(91, 143, 223, 0.12);
  --circle-entry-icon-color: #5b8fdf;
}

.circle-entry:nth-child(2) {
  --circle-entry-bg: rgba(248, 251, 255, 0.62);
  --circle-entry-icon-bg: rgba(115, 150, 204, 0.12);
  --circle-entry-icon-color: #6e91bf;
}

.circle-entry:nth-child(3) {
  --circle-entry-bg: rgba(250, 253, 253, 0.62);
  --circle-entry-icon-bg: var(--circle-mint-soft, rgba(116, 189, 173, 0.14));
  --circle-entry-icon-color: #69aa9c;
}

.circle-entry:nth-child(4) {
  --circle-entry-bg: rgba(250, 252, 255, 0.62);
  --circle-entry-icon-bg: rgba(127, 144, 179, 0.11);
  --circle-entry-icon-color: #778db5;
}

.circle-entry::after,
.experience-filter-chip::after,
.material-subject-chip::after,
.material-action::after,
.circle-post-action-row button::after {
  border: 0;
}

.circle-entry:active {
  transform: scale(0.98);
}

.circle-entry-icon,
.circle-empty-icon {
  width: 54px;
  height: 54px;
  border-radius: 16px;
  background: var(--circle-entry-icon-bg, var(--circle-brand-soft, rgba(91, 143, 223, 0.14)));
  color: var(--circle-entry-icon-color, var(--circle-brand, #5b8fdf));
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.circle-entry-icon-image {
  width: 100%;
  height: 100%;
}

.circle-entry-icon-image {
  display: block;
  opacity: 0.82;
}

.circle-entry-label {
  min-width: 0;
  flex: 1;
  color: var(--circle-text, #1d1d1f);
  font-size: 22px;
  line-height: 1.24;
  font-weight: 600;
}

.circle-entry-arrow {
  width: 36px;
  height: 36px;
  border-radius: 999rpx;
  background: rgba(112, 133, 161, 0.08);
  color: #788aa4;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--gyt-app-font);
  font-size: 20px;
  line-height: 1;
  font-weight: 400;
  flex-shrink: 0;
}

.circle-glass-page .circle-trend-card {
  -webkit-backdrop-filter: blur(18px) saturate(112%);
  backdrop-filter: blur(18px) saturate(112%);
}

.circle-glass-page .circle-entry {
  -webkit-backdrop-filter: blur(16px) saturate(108%);
  backdrop-filter: blur(16px) saturate(108%);
  transition: transform 180ms ease;
}

.circle-glass-page .circle-entry:active {
  transform: scale(0.98);
}

@supports not (backdrop-filter: blur(1px)) {
  .circle-glass-page .circle-trend-card {
    background: #ffffff;
  }

  .circle-glass-page .circle-entry {
    background: #f9fbfd;
  }
}

@media (max-width: 350px) {
  .circle-trend-heading {
    gap: 8px;
  }

  .circle-trend-title {
    font-size: 22px;
  }

  .circle-trend-peak {
    font-size: 11px;
  }

  .circle-entry {
    padding-right: 14px;
    padding-left: 14px;
    gap: 10px;
  }

  .circle-entry-label {
    font-size: 21px;
  }
}

@media (prefers-reduced-motion: reduce) {
  .circle-glass-page .circle-trend-card,
  .circle-glass-page .circle-entry {
    animation: none;
    transition: none;
  }
}

/* Content stays opaque; only navigation and compact controls use glass. */
.circle-glass-page .circle-overview {
  height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 140px);
  height: calc(100dvh - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 140px);
  min-height: 0;
  gap: 10px;
}

.circle-glass-page .circle-glass-group {
  position: relative;
  isolation: isolate;
}

.circle-insight-swiper {
  width: calc(100% + var(--circle-insight-slide-gap));
  height: 210px;
  flex: 0 0 210px;
  margin-left: calc(0px - var(--circle-insight-slide-offset));
}

.circle-insight-route-mirror {
  pointer-events: none;
}

.circle-score-mirror-plot {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 17px;
  left: 25px;
  overflow: visible;
}

.circle-score-mirror-grid-line {
  position: absolute;
  left: 10%;
  width: 87.333%;
  height: 1px;
  background: rgba(49, 76, 84, 0.12);
}

.circle-score-mirror-segment {
  position: absolute;
  height: 3px;
  margin-top: -1.5px;
  border-radius: 999px;
  background: var(--gyt-primary, #3478f6);
  transform-origin: 0 50%;
}

.circle-score-mirror-point {
  position: absolute;
  box-sizing: border-box;
  width: 12px;
  height: 12px;
  border: 3px solid var(--gyt-primary, #3478f6);
  border-radius: 50%;
  background: #ffffff;
  transform: translate(-50%, -50%);
}

.circle-insight-swiper swiper-item,
.circle-insight-swiper .circle-glass-surface {
  box-sizing: border-box;
  height: 100%;
  min-height: 0;
}

.circle-insight-swiper .circle-glass-surface {
  width: calc(100% - var(--circle-insight-slide-gap));
  margin: 0 var(--circle-insight-slide-offset);
}

.circle-insight-pagination {
  height: 10px;
  flex: 0 0 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.circle-insight-dot {
  width: 7px;
  height: 7px;
  min-width: 7px;
  min-height: 7px;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.56);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.56);
  transition: width 180ms ease, background-color 180ms ease, transform 180ms ease;
}

.circle-insight-dot::after {
  border: 0;
}

.circle-insight-dot.active {
  width: 20px;
  background: rgba(18, 111, 103, 0.82);
}

.circle-insight-dot:active {
  transform: scale(0.92);
}

.circle-glass-page .circle-trend-card {
  padding: 18px 18px 14px;
  border-color: var(--circle-glass-border, rgba(255, 255, 255, 0.78));
  border-radius: 30px;
  background: var(--circle-glass-surface-strong, rgba(249, 252, 251, 0.82));
  box-shadow: none;
  -webkit-backdrop-filter: blur(var(--circle-glass-blur, 20px)) saturate(125%);
  backdrop-filter: blur(var(--circle-glass-blur, 20px)) saturate(125%);
}

.circle-glass-page .circle-trend-title {
  color: #1c2423;
  font-size: 25px;
  font-weight: 650;
}

.circle-glass-page .circle-trend-peak {
  color: #657473;
  font-size: 13px;
}

.circle-glass-page .circle-trend-peak-value {
  color: #16786f;
}

.circle-glass-page .circle-trend-chart {
  height: 116px;
  margin-top: 8px;
}

.circle-glass-page .circle-trend-grid,
.circle-glass-page .circle-trend-bars {
  left: 30px;
}

.circle-glass-page .circle-trend-grid-line {
  border-color: rgba(49, 76, 84, 0.12);
}

.circle-glass-page .circle-trend-axis {
  width: 25px;
  color: #768482;
  font-size: 10px;
}

.circle-glass-page .circle-trend-bars {
  column-gap: 6px;
}

.circle-glass-page .circle-trend-bar-space {
  padding: 16px 0;
}

.circle-glass-page .circle-trend-bar {
  width: 11px;
  background: linear-gradient(180deg, #82c9bf 0%, #3d9c90 100%);
}

.circle-glass-page .circle-trend-bar.latest {
  background: linear-gradient(180deg, #70b9f0 0%, #3b78c5 100%);
}

.circle-glass-page .circle-trend-value {
  bottom: calc(100% + 6px);
  color: #314240;
  font-size: 10px;
}

.circle-glass-page .circle-trend-day {
  height: 13px;
  color: #768482;
  font-size: 10px;
  line-height: 13px;
}

.circle-glass-page .circle-entry-list {
  min-height: 0;
  flex: 1 1 0;
  grid-template-rows: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.circle-glass-page .circle-entry {
  padding: 12px 16px 12px 18px;
  gap: 13px;
  border-color: var(--circle-glass-border, rgba(255, 255, 255, 0.78));
  border-radius: 28px;
  background: var(--circle-entry-bg, var(--circle-glass-surface, rgba(250, 253, 252, 0.66)));
  box-shadow: none;
  -webkit-backdrop-filter: blur(var(--circle-glass-blur, 20px)) saturate(120%);
  backdrop-filter: blur(var(--circle-glass-blur, 20px)) saturate(120%);
  transition: transform 180ms ease, background-color 180ms ease;
}

.circle-glass-page .circle-entry:nth-child(1) {
  --circle-entry-bg: rgba(248, 253, 251, 0.48);
  --circle-entry-icon-bg: rgba(221, 241, 236, 0.42);
  --circle-entry-icon-color: #16786f;
}

.circle-glass-page .circle-entry:nth-child(2) {
  --circle-entry-bg: rgba(249, 251, 253, 0.48);
  --circle-entry-icon-bg: rgba(226, 236, 247, 0.42);
  --circle-entry-icon-color: #55738f;
}

.circle-glass-page .circle-entry:nth-child(3) {
  --circle-entry-bg: rgba(253, 251, 247, 0.48);
  --circle-entry-icon-bg: rgba(247, 232, 209, 0.42);
  --circle-entry-icon-color: #a56c3b;
}

.circle-glass-page .circle-entry:nth-child(4) {
  --circle-entry-bg: rgba(250, 250, 253, 0.48);
  --circle-entry-icon-bg: rgba(235, 230, 247, 0.42);
  --circle-entry-icon-color: #756491;
}

.circle-glass-page .circle-entry-icon {
  width: 52px;
  height: 52px;
  border-radius: 18px;
  border: 1px solid rgba(255, 255, 255, 0.58);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.34);
  -webkit-backdrop-filter: blur(12px) saturate(116%);
  backdrop-filter: blur(12px) saturate(116%);
}

.circle-glass-page .circle-entry-icon-image {
  width: 100%;
  height: 100%;
}

.circle-glass-page .circle-entry-label {
  color: #1c2423;
  font-size: 21px;
  font-weight: 600;
}

.circle-glass-page .circle-entry-arrow {
  width: 38px;
  height: 38px;
  border: 1px solid rgba(255, 255, 255, 0.76);
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.38);
  color: #536967;
  font-size: 25px;
  -webkit-backdrop-filter: blur(14px) saturate(118%);
  backdrop-filter: blur(14px) saturate(118%);
}

.circle-glass-page .circle-entry:active {
  transform: scale(var(--circle-glass-press, 0.98));
}

.circle-score-card {
  padding: 18px 18px 14px;
  border: 1px solid var(--circle-glass-border, rgba(255, 255, 255, 0.78));
  border-radius: 30px;
  background: var(--circle-glass-surface-strong, rgba(249, 252, 251, 0.82));
  box-shadow: none;
  overflow: hidden;
  isolation: isolate;
  display: flex;
  flex-direction: column;
  -webkit-backdrop-filter: blur(var(--circle-glass-blur, 20px)) saturate(125%);
  backdrop-filter: blur(var(--circle-glass-blur, 20px)) saturate(125%);
}

.circle-score-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.circle-score-copy {
  min-width: 0;
  flex: 1;
}

.circle-score-title {
  color: #1c2423;
  font-size: 24px;
  line-height: 1.18;
  font-weight: 650;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.circle-score-subtitle {
  margin-top: 3px;
  color: #657473;
  font-size: 12px;
  line-height: 1.2;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.circle-score-total {
  padding-top: 4px;
  color: #657473;
  font-size: 13px;
  line-height: 1.2;
  font-weight: 500;
  white-space: nowrap;
}

.circle-score-total text {
  margin-left: 2px;
  color: var(--gyt-primary, #3478f6);
  font-size: 17px;
  font-weight: 700;
}

.circle-score-chart {
  position: relative;
  min-height: 0;
  flex: 1;
  margin-top: 5px;
}

.circle-score-axis {
  position: absolute;
  z-index: 1;
  top: 10px;
  bottom: 19px;
  left: 0;
  width: 25px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: #768482;
  font-size: 10px;
  line-height: 1;
  font-weight: 500;
}

.circle-score-axis text {
  transform: translateY(-50%);
}

.circle-score-axis text:last-child {
  transform: translateY(50%);
}

.circle-score-svg,
.circle-score-canvas {
  position: absolute;
  top: 0;
  right: 0;
  bottom: 17px;
  left: 25px;
  width: calc(100% - 25px);
  height: calc(100% - 17px);
  overflow: visible;
}

.circle-score-grid-line {
  stroke: rgba(49, 76, 84, 0.12);
  stroke-width: 1;
}

.circle-score-line {
  fill: none;
  stroke: var(--gyt-primary, #3478f6);
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 3;
}

.circle-score-point {
  fill: #ffffff;
  stroke: var(--gyt-primary, #3478f6);
  stroke-width: 3;
  transition: stroke-width 160ms ease, fill 160ms ease;
}

.circle-score-point.is-active {
  stroke-width: 4;
}

.circle-score-point-hit {
  cursor: pointer;
}

.circle-score-point-hit-area {
  fill: rgba(255, 255, 255, 0.001);
  stroke: transparent;
  pointer-events: all;
}

.circle-score-tooltip-layer {
  position: absolute;
  z-index: 3;
  top: 0;
  right: 0;
  bottom: 17px;
  left: 25px;
  pointer-events: none;
}

.circle-score-tooltip {
  position: absolute;
  min-width: 58px;
  height: 24px;
  padding: 0 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  transform: translate(-50%, -50%);
  border-radius: 12px;
  background: var(--gyt-primary, #3478f6);
  fill: #ffffff;
  color: #ffffff;
  font-size: 11px;
  line-height: 1;
  font-weight: 750;
  white-space: nowrap;
}

.circle-score-years {
  position: absolute;
  right: 0;
  bottom: 0;
  left: 25px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  color: #768482;
  font-size: 10px;
  line-height: 1;
  font-weight: 500;
  text-align: center;
}

.circle-score-card[role='button'] {
  cursor: pointer;
  transition: transform 180ms ease;
}

.circle-score-card[role='button']:active {
  transform: scale(var(--circle-glass-press, 0.98));
}

.scoreline-section {
  gap: 20rpx;
}

.home-page.scoreline-browser-page {
  display: flex;
  min-height: 0;
  height: 100vh;
  height: 100dvh;
  flex-direction: column;
  overflow: hidden;
}

.home-page.scoreline-browser-page .circle-dashboard,
.home-page.scoreline-browser-page .circle-view-stage,
.home-page.scoreline-browser-page .circle-detail-route-layer,
.home-page.scoreline-browser-page .circle-detail-route-scroll,
.home-page.scoreline-browser-page .circle-detail-route-content,
.home-page.scoreline-browser-page .circle-detail-page,
.home-page.scoreline-browser-page .circle-scoreline-section,
.home-page.scoreline-browser-page .scoreline-browser-layout {
  min-height: 0;
  flex: 1;
}

.home-page.scoreline-browser-page .circle-dashboard,
.home-page.scoreline-browser-page .circle-view-stage,
.home-page.scoreline-browser-page .circle-detail-route-content {
  display: flex;
}

.scoreline-search,
.scoreline-select-control,
.scoreline-results-frame,
.scoreline-school-card,
.scoreline-detail-card,
.scoreline-load-more {
  box-sizing: border-box;
}

.scoreline-search {
  min-height: 80rpx;
  padding: 0 20rpx;
  border: 2rpx solid rgba(215, 229, 255, 0.9);
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.78);
  display: flex;
  align-items: center;
  gap: 12rpx;
  -webkit-backdrop-filter: blur(16px) saturate(116%);
  backdrop-filter: blur(16px) saturate(116%);
}

.scoreline-search-icon {
  color: var(--gyt-primary, #3478f6);
}

.scoreline-search-input {
  min-width: 0;
  flex: 1;
  height: 76rpx;
  color: #1d2d2b;
  font-size: 26rpx;
  line-height: 1.2;
  font-weight: 600;
}

.scoreline-search-placeholder {
  color: #8b9a9b;
  font-weight: 500;
}

.scoreline-search-clear {
  width: 40rpx;
  height: 40rpx;
  min-width: 40rpx;
  min-height: 40rpx;
  margin: 0;
  padding: 9rpx;
  border: 0;
  border-radius: 50%;
  background: rgba(22, 120, 111, 0.1);
  color: #16786f;
  display: flex;
  align-items: center;
  justify-content: center;
}

.scoreline-search-clear::after,
.scoreline-results-reset::after,
.scoreline-school-card::after,
.scoreline-load-more::after {
  border: 0;
}

.scoreline-browser-layout {
  display: flex;
  min-height: 0;
  flex: 1;
  flex-direction: column;
  gap: 14rpx;
}

.scoreline-filter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.scoreline-select {
  display: block;
  width: 100%;
  min-width: 0;
}

.scoreline-select-control {
  display: flex;
  min-height: 66rpx;
  align-items: center;
  justify-content: space-between;
  gap: 10rpx;
  padding: 0 16rpx;
  overflow: hidden;
  border: 2rpx solid rgba(215, 229, 255, 0.92);
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.78);
  transition: transform 180ms ease, border-color 180ms ease, background-color 180ms ease;
  -webkit-backdrop-filter: blur(16px) saturate(116%);
  backdrop-filter: blur(16px) saturate(116%);
}

.scoreline-select:active .scoreline-select-control {
  transform: scale(0.985);
}

.scoreline-select-name {
  flex: 0 0 auto;
  color: #637682;
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 750;
}

.scoreline-select-value {
  min-width: 0;
  flex: 1;
  color: var(--gyt-primary, #3478f6);
  overflow: hidden;
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 800;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scoreline-select-arrow-icon {
  display: block;
  width: 18rpx;
  height: 11rpx;
  flex: 0 0 auto;
}

.scoreline-school-card:active,
.scoreline-load-more:active,
.scoreline-results-reset:active {
  transform: scale(0.985);
}

.scoreline-results-frame {
  display: flex;
  min-height: 0;
  flex: 0 0 auto;
  flex-direction: column;
  overflow: hidden;
  border: 2rpx solid rgba(215, 229, 255, 0.92);
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.82);
  -webkit-backdrop-filter: blur(18px) saturate(116%);
  backdrop-filter: blur(18px) saturate(116%);
}

.scoreline-results-heading {
  display: flex;
  min-height: 78rpx;
  flex: 0 0 auto;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 15rpx 20rpx;
  border-bottom: 2rpx solid rgba(103, 130, 132, 0.12);
}

.scoreline-results-heading-copy {
  min-width: 0;
}

.scoreline-results-title,
.scoreline-results-count {
  display: block;
}

.scoreline-results-title {
  color: #1c2423;
  overflow: hidden;
  font-size: 26rpx;
  line-height: 1.25;
  font-weight: 850;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scoreline-results-count {
  margin-top: 4rpx;
  color: var(--gyt-primary, #3478f6);
  font-size: 19rpx;
  line-height: 1.3;
  font-weight: 750;
}

.scoreline-results-reset {
  min-height: 44rpx;
  margin: 0;
  padding: 0 8rpx;
  border: 0;
  border-radius: 14rpx;
  background: transparent;
  color: var(--gyt-primary, #3478f6);
  font-size: 20rpx;
  line-height: 44rpx;
  font-weight: 750;
  transition: transform 180ms ease;
}

.scoreline-results-scroll {
  height: auto;
  min-height: 0;
  flex: 0 0 auto;
}

.scoreline-results-scroll::-webkit-scrollbar,
.scoreline-results-scroll ::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.scoreline-results-content {
  min-height: 100%;
  box-sizing: border-box;
  padding: 16rpx 16rpx 24rpx;
}

.scoreline-school-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.scoreline-school-card {
  width: 100%;
  margin: 0;
  padding: 22rpx;
  border: 2rpx solid rgba(215, 229, 255, 0.92);
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.82);
  color: inherit;
  text-align: left;
  transition: transform 180ms ease, border-color 180ms ease, background-color 180ms ease;
  -webkit-backdrop-filter: blur(16px) saturate(116%);
  backdrop-filter: blur(16px) saturate(116%);
}

.scoreline-school-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.scoreline-school-copy {
  min-width: 0;
  display: flex;
  flex: 1;
  flex-direction: column;
}

.scoreline-school-name {
  color: #1c2423;
  font-size: 28rpx;
  line-height: 1.35;
  font-weight: 800;
  word-break: break-word;
}

.scoreline-school-unit {
  display: block;
  max-width: 100%;
  margin-top: 3rpx;
  overflow: hidden;
  color: #7f8b99;
  font-size: 21rpx;
  line-height: 1.4;
  font-weight: 400;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scoreline-school-meta {
  margin-top: 7rpx;
  color: #728284;
  font-size: 20rpx;
  line-height: 1.35;
  font-weight: 600;
}

.scoreline-school-arrow {
  color: var(--gyt-primary, #3478f6);
  font-size: 42rpx;
  line-height: 0.9;
  font-weight: 400;
}

.scoreline-year-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10rpx;
  margin-top: 18rpx;
}

.scoreline-year-cell {
  min-width: 0;
  min-height: 78rpx;
  padding: 12rpx;
  border-radius: 18rpx;
  background: rgba(240, 246, 253, 0.82);
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 5rpx;
}

.scoreline-year-label {
  color: #7c8a91;
  font-size: 18rpx;
  line-height: 1.1;
  font-weight: 650;
}

.scoreline-year-value {
  color: #16786f;
  overflow: hidden;
  font-size: 23rpx;
  line-height: 1.15;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scoreline-year-value.is-note {
  color: #60716f;
  font-size: 20rpx;
}

.scoreline-load-more {
  min-height: 74rpx;
  margin: 2rpx 0 0;
  padding: 0 24rpx;
  border: 2rpx solid rgba(215, 229, 255, 0.92);
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.72);
  color: var(--gyt-primary, #3478f6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 750;
  transition: transform 180ms ease;
}

.scoreline-detail-toolbar {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 16rpx;
}

.scoreline-detail-source {
  min-width: 0;
  color: #728284;
  font-size: 19rpx;
  line-height: 1.3;
  font-weight: 600;
  text-align: right;
}

.scoreline-detail-card {
  padding: 26rpx;
  border: 2rpx solid rgba(215, 229, 255, 0.92);
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.84);
  -webkit-backdrop-filter: blur(18px) saturate(116%);
  backdrop-filter: blur(18px) saturate(116%);
}

.scoreline-detail-school-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
}

.scoreline-detail-school {
  color: #1c2423;
  font-size: 34rpx;
  line-height: 1.3;
  font-weight: 850;
  word-break: break-word;
}

.scoreline-detail-meta {
  margin-top: 9rpx;
  color: #728284;
  font-size: 21rpx;
  line-height: 1.45;
  font-weight: 600;
}

.scoreline-detail-region {
  flex-shrink: 0;
  padding: 9rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(226, 244, 239, 0.84);
  color: #16786f;
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 800;
}

.scoreline-detail-chart {
  margin-top: 26rpx;
  padding-top: 22rpx;
  border-top: 2rpx solid rgba(103, 130, 132, 0.12);
}

.scoreline-detail-chart-title {
  color: #4f6260;
  font-size: 22rpx;
  line-height: 1.2;
  font-weight: 750;
}

.scoreline-detail-chart-plot {
  position: relative;
  height: 230rpx;
  margin-top: 12rpx;
}

.scoreline-detail-note {
  margin-top: 24rpx;
  padding: 18rpx;
  border-radius: 20rpx;
  background: rgba(240, 246, 253, 0.8);
  color: #60716f;
  font-size: 21rpx;
  line-height: 1.55;
  font-weight: 600;
}

.scoreline-history-list {
  display: flex;
  flex-direction: column;
  margin-top: 26rpx;
  border-top: 2rpx solid rgba(103, 130, 132, 0.12);
}

.scoreline-history-item {
  padding: 21rpx 0;
  border-bottom: 2rpx solid rgba(103, 130, 132, 0.1);
}

.scoreline-history-main {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 18rpx;
}

.scoreline-history-year {
  color: #1d2d2b;
  font-size: 24rpx;
  line-height: 1.2;
  font-weight: 800;
}

.scoreline-history-value {
  color: #16786f;
  font-size: 24rpx;
  line-height: 1.25;
  font-weight: 800;
  text-align: right;
}

.scoreline-history-value.is-note {
  color: #60716f;
}

.scoreline-history-copy {
  display: block;
  margin-top: 11rpx;
  color: #6f7f81;
  font-size: 20rpx;
  line-height: 1.58;
  font-weight: 550;
  word-break: break-word;
}

.circle-glass-page .scoreline-search,
.circle-glass-page .scoreline-select-control,
.circle-glass-page .scoreline-results-frame,
.circle-glass-page .scoreline-school-card,
.circle-glass-page .scoreline-load-more,
.circle-glass-page .scoreline-detail-card {
  border-color: var(--circle-glass-border, rgba(255, 255, 255, 0.58));
  background: var(--circle-glass-control, rgba(249, 252, 251, 0.52));
}

.circle-glass-page .scoreline-school-card,
.circle-glass-page .scoreline-detail-card,
.circle-glass-page .scoreline-results-frame {
  background: var(--circle-glass-card, rgba(249, 252, 251, 0.72));
}

.circle-glass-page .scoreline-results-heading {
  border-color: rgba(103, 130, 132, 0.12);
}

.circle-glass-page .scoreline-year-cell,
.circle-glass-page .scoreline-detail-note {
  background: rgba(235, 246, 243, 0.52);
}

@supports not (backdrop-filter: blur(1px)) {
  .circle-glass-page .scoreline-search,
  .circle-glass-page .scoreline-select-control,
  .circle-glass-page .scoreline-results-frame,
  .circle-glass-page .scoreline-school-card,
  .circle-glass-page .scoreline-load-more,
  .circle-glass-page .scoreline-detail-card {
    background: #f9fbfa;
  }
}

@media (hover: hover) {
  .circle-glass-page .circle-entry:hover {
    background: rgba(255, 255, 255, 0.76);
  }
}

@supports not (backdrop-filter: blur(1px)) {
  .circle-glass-page .circle-trend-card,
  .circle-glass-page .circle-entry,
  .circle-glass-page .circle-score-card {
    background: #f9fbfa;
  }

  .circle-glass-page .circle-entry-arrow {
    background: #f5f8f7;
  }
}

@media (max-width: 350px) {
  .circle-glass-page .circle-trend-card {
    padding-right: 14px;
    padding-left: 14px;
  }

  .circle-glass-page .circle-entry {
    padding-right: 12px;
    padding-left: 14px;
  }

  .circle-glass-page .circle-entry-label {
    font-size: 20px;
  }
}

.circle-detail-header {
  min-height: 76rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.circle-detail-route-header {
  position: relative;
  z-index: 2;
  width: 100%;
  flex: 0 0 auto;
  min-height: calc(var(--status-bar-height, env(safe-area-inset-top)) + 104rpx);
  margin: 0;
  padding: calc(var(--status-bar-height, env(safe-area-inset-top)) + 14rpx) 16px 14rpx;
  box-sizing: border-box;
  background: var(--gyt-page-bg, #f8faff);
  box-shadow: 0 14rpx 30rpx rgba(25, 48, 89, var(--circle-community-header-shadow-opacity, 0));
  transition: box-shadow 180ms ease;
}

/* #ifdef MP-WEIXIN */
.circle-detail-route-layer {
  padding-top: var(--mp-page-content-top, 96px);
}

.circle-detail-route-header {
  min-height: 104rpx;
  padding: 14rpx 16px;
}
/* #endif */

.circle-back-button,
.circle-detail-header-spacer {
  width: 76rpx;
  height: 76rpx;
  flex-shrink: 0;
}

.circle-back-button {
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 26rpx;
  background: #ffffff;
  color: #172033;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.08);
}

.circle-back-button::after {
  border: 0;
}

.circle-back-button image {
  width: 30rpx;
  height: 30rpx;
}

.circle-detail-heading {
  position: absolute;
  left: 50%;
  transform: translateX(-50%);
  color: #172033;
  font-size: 32rpx;
  line-height: 1.2;
  font-weight: 900;
  white-space: nowrap;
  pointer-events: none;
}

.circle-my-verification-entry {
  position: relative;
  z-index: 1;
  box-sizing: border-box;
  min-width: 124rpx;
  height: 76rpx;
  min-height: 76rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: var(--gyt-primary, #3478f6);
  display: flex;
  align-items: center;
  justify-content: flex-end;
  font-size: 27rpx;
  line-height: 1;
  font-weight: 900;
  letter-spacing: 1rpx;
  white-space: nowrap;
  box-shadow: none;
}

.circle-my-verification-entry::after {
  border: 0;
}

.circle-my-verification-entry:active {
  opacity: 0.58;
}

.circle-section {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.circle-section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18rpx;
  padding: 0 6rpx;
}

.circle-section-title {
  color: #101828;
  font-size: 34rpx;
  line-height: 1.22;
  font-weight: 900;
}

.circle-section-subtitle {
  margin-top: 8rpx;
  color: #8a94a6;
  font-size: 23rpx;
  line-height: 1.5;
  font-weight: 700;
}

.circle-section-count {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: #ffffff;
  color: var(--gyt-primary, #3478f6);
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  font-size: 21rpx;
  line-height: 1.2;
  font-weight: 900;
  flex-shrink: 0;
}

.experience-search {
  box-sizing: border-box;
  min-height: 76rpx;
  padding: 0 18rpx;
  border: 2rpx solid #edf2fb;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.92);
  box-shadow: 0 12rpx 28rpx rgba(25, 48, 89, 0.05);
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.experience-search-icon {
  color: var(--gyt-primary, #3478f6);
}

.experience-search-input {
  min-width: 0;
  flex: 1;
  height: 72rpx;
  color: #1c2423;
  font-size: 25rpx;
  line-height: 1.2;
  font-weight: 600;
}

.experience-search-placeholder {
  color: #8a9897;
  font-weight: 500;
}

.experience-search-clear {
  box-sizing: border-box;
  width: 40rpx;
  height: 40rpx;
  min-width: 40rpx;
  min-height: 40rpx;
  margin: 0;
  padding: 9rpx;
  border: 0;
  border-radius: 50%;
  background: rgba(22, 120, 111, 0.1);
  color: #16786f;
  display: flex;
  align-items: center;
  justify-content: center;
}

.experience-search-clear::after {
  border: 0;
}

.community-post-sort-picker {
  display: block;
  min-width: 116rpx;
  flex: 0 0 auto;
}

.community-post-sort-control {
  box-sizing: border-box;
  min-height: 48rpx;
  padding-left: 16rpx;
  border-left: 2rpx solid rgba(22, 120, 111, 0.14);
  color: #16786f;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10rpx;
  font-size: 24rpx;
  line-height: 1.2;
  font-weight: 800;
  transition: transform 180ms ease, color 180ms ease;
}

.community-post-sort-arrow {
  width: 0;
  height: 0;
  margin-top: 4rpx;
  border-top: 9rpx solid currentColor;
  border-right: 6rpx solid transparent;
  border-left: 6rpx solid transparent;
  opacity: 0.72;
}

.community-post-sort-picker:active .community-post-sort-control {
  transform: scale(0.98);
}

.mentor-search .community-post-sort-picker {
  min-width: 142rpx;
}

.mentor-search .mentor-sort-control {
  border-left: 0;
  color: var(--gyt-primary, #3478f6);
  font-size: 22rpx;
}

.mentor-filter-trigger,
.mentor-empty-reset {
  box-sizing: border-box;
  margin: 0;
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  border-radius: 999rpx;
  background: rgba(237, 244, 255, 0.82);
  color: var(--gyt-primary, #3478f6);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  font-size: 22rpx;
  line-height: 1.2;
  font-weight: 800;
}

.mentor-filter-trigger {
  min-width: 116rpx;
  min-height: 48rpx;
  padding: 0 16rpx;
  flex-shrink: 0;
}

.mentor-search-filter-trigger {
  position: relative;
  width: 82rpx;
  min-width: 82rpx;
  min-height: 56rpx;
  padding: 0 18rpx 0 0;
  border: 0;
  border-left: 2rpx solid rgba(52, 120, 246, 0.16);
  border-radius: 0;
  background: transparent;
  flex: 0 0 82rpx;
  justify-content: flex-end;
  gap: 0;
  transition: background 160ms ease;
}

.mentor-search-filter-trigger.has-filters {
  background: transparent;
}

.mentor-search-filter-trigger:active {
  background: rgba(52, 120, 246, 0.06);
}

.mentor-filter-trigger::after,
.mentor-empty-reset::after,
.mentor-filter-sheet button::after {
  border: 0;
}

.mentor-filter-trigger-icon {
  width: 24rpx;
  height: 22rpx;
  display: inline-flex;
  flex-direction: column;
  align-items: flex-start;
  justify-content: space-between;
  flex-shrink: 0;
}

.mentor-filter-trigger-icon view {
  height: 3rpx;
  border-radius: 999rpx;
  background: currentColor;
}

.mentor-filter-trigger-icon view:nth-child(1) { width: 24rpx; }
.mentor-filter-trigger-icon view:nth-child(2) { width: 17rpx; }
.mentor-filter-trigger-icon view:nth-child(3) { width: 10rpx; }

.mentor-filter-trigger-icon view::after {
  border: 0;
}

.mentor-filter-trigger-count {
  position: absolute;
  top: 4rpx;
  right: 8rpx;
  min-width: 24rpx;
  height: 24rpx;
  padding: 0 4rpx;
  border: 2rpx solid #ffffff;
  border-radius: 999rpx;
  background: var(--gyt-primary, #3478f6);
  color: #ffffff;
  font-size: 16rpx;
  line-height: 20rpx;
  font-weight: 850;
  text-align: center;
}

.mentor-feed {
  width: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 14rpx;
}

.mentor-directory-grid .mentor-empty-card {
  width: 100%;
}

.mentor-loading-card {
  box-sizing: border-box;
  min-height: 430rpx;
  padding: 22rpx 28rpx;
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  border-radius: 30rpx;
  background: var(--gyt-panel-bg, #ffffff);
  box-shadow: 0 16rpx 38rpx rgba(52, 120, 246, 0.06);
}

.mentor-loading-person-row,
.mentor-loading-bottom-row {
  display: flex;
  align-items: center;
}

.mentor-loading-person-row { gap: 16rpx; }
.mentor-loading-copy { min-width: 0; flex: 1; }
.mentor-loading-avatar,
.mentor-loading-line,
.mentor-loading-action {
  background: linear-gradient(90deg, #edf3fb 0%, #f7faff 50%, #edf3fb 100%);
  background-size: 200% 100%;
  animation: mentor-directory-skeleton 1.45s ease-in-out infinite;
}
.mentor-loading-avatar { width: 74rpx; height: 74rpx; border-radius: 50%; flex-shrink: 0; }
.mentor-loading-line { height: 18rpx; border-radius: 999rpx; }
.mentor-loading-line-name { width: 142rpx; height: 22rpx; }
.mentor-loading-line-school { width: 104rpx; margin-top: 12rpx; }
.mentor-loading-line-meta { width: 58%; margin-top: 28rpx; }
.mentor-loading-line-copy { width: 100%; margin-top: 16rpx; }
.mentor-loading-line-copy.short { width: 68%; }
.mentor-loading-bottom-row { justify-content: space-between; gap: 18rpx; margin-top: 28rpx; }
.mentor-loading-line-price { width: 130rpx; height: 24rpx; }
.mentor-loading-action { width: 150rpx; height: 62rpx; border-radius: 18rpx; flex-shrink: 0; }

@keyframes mentor-directory-skeleton {
  to { background-position: -200% 0; }
}

.mentor-empty-card {
  align-items: flex-start;
}

.mentor-empty-reset {
  margin-top: 18rpx;
  min-height: 52rpx;
  padding: 0 22rpx;
}

.mentor-filter-mask {
  position: fixed;
  z-index: 120;
  inset: 0;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 36rpx 20rpx calc(20rpx + env(safe-area-inset-bottom));
  background: rgba(20, 38, 68, 0.32);
}

.mentor-filter-mask.is-visible {
  animation: mentor-filter-mask-slide-in 200ms ease-out both;
}

.mentor-filter-mask.is-leaving {
  animation: mentor-filter-mask-slide-out 180ms ease-in both;
}

.mentor-filter-sheet {
  box-sizing: border-box;
  width: 100%;
  max-width: 720rpx;
  max-height: min(1080rpx, 80vh);
  overflow: hidden;
  border: 2rpx solid rgba(255, 255, 255, 0.84);
  border-radius: 34rpx;
  background: rgba(250, 253, 255, 0.98);
  box-shadow: 0 -18rpx 60rpx rgba(24, 58, 113, 0.16);
  display: flex;
  flex-direction: column;
  will-change: transform;
}

.mentor-filter-mask.is-visible .mentor-filter-sheet {
  animation: mentor-filter-sheet-slide-in 300ms cubic-bezier(0.22, 0.9, 0.32, 1) both;
}

.mentor-filter-mask.is-leaving .mentor-filter-sheet {
  animation: mentor-filter-sheet-slide-out 240ms cubic-bezier(0.4, 0, 1, 1) both;
}

@keyframes mentor-filter-mask-slide-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes mentor-filter-mask-slide-out {
  from { opacity: 1; }
  to { opacity: 0; }
}

@keyframes mentor-filter-sheet-slide-in {
  from { transform: translate3d(0, 120%, 0); }
  to { transform: translate3d(0, 0, 0); }
}

@keyframes mentor-filter-sheet-slide-out {
  from { transform: translate3d(0, 0, 0); }
  to { transform: translate3d(0, 120%, 0); }
}

.mentor-filter-sheet-heading {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  padding: 18rpx 30rpx 8rpx;
}

.mentor-filter-sheet-close {
  box-sizing: border-box;
  width: 52rpx;
  height: 52rpx;
  min-width: 52rpx;
  min-height: 52rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #edf4ff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 0;
  line-height: 1;
}

.mentor-filter-sheet-close-icon {
  color: #6b85b5;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-family: var(--gyt-app-font);
  font-size: 38rpx;
  font-weight: 400;
  line-height: 1;
  transform: translateY(-1rpx);
}

.mentor-filter-sheet-scroll {
  min-height: 0;
  flex: 1;
}

.mentor-filter-sheet-body {
  padding: 0 30rpx 20rpx;
}

.mentor-filter-field + .mentor-filter-field {
  margin-top: 28rpx;
}

.mentor-filter-field-label {
  margin-bottom: 14rpx;
  color: #2c3b55;
  font-size: 24rpx;
  line-height: 1.25;
  font-weight: 850;
}

.mentor-filter-option-row button {
  min-height: 48rpx;
  margin: 0;
  padding: 0 16rpx;
  border: 2rpx solid #e1eafa;
  border-radius: 14rpx;
  background: #fff;
  color: #67768e;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 21rpx;
  line-height: 1.2;
  font-weight: 700;
}

.mentor-filter-option-row {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.mentor-filter-option-row button.active {
  border-color: #b8d1ff;
  background: #edf4ff;
  color: var(--gyt-primary, #3478f6);
}

.mentor-filter-sheet-actions {
  display: grid;
  grid-template-columns: 1fr 1.6fr;
  align-items: center;
  gap: 14rpx;
  padding: 20rpx 30rpx calc(24rpx + env(safe-area-inset-bottom));
  border-top: 2rpx solid #edf1f8;
  background: rgba(255, 255, 255, 0.96);
}

.mentor-filter-reset-button,
.mentor-filter-confirm-button {
  min-height: 76rpx;
  height: 76rpx;
  box-sizing: border-box;
  margin: 0;
  padding: 0 16rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  line-height: 1.2;
  font-weight: 850;
}

.mentor-filter-action-label {
  width: 100%;
  height: 100%;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
  transform: translateY(-1rpx);
}

.mentor-filter-reset-button {
  border: 2rpx solid #d8e5fb;
  background: #f7faff;
  color: #657a9d;
}

.mentor-filter-confirm-button {
  border: 2rpx solid var(--gyt-primary, #3478f6);
  background: var(--gyt-primary, #3478f6);
  color: #fff;
  box-shadow: 0 10rpx 24rpx rgba(52, 120, 246, 0.2);
}

.experience-filter-scroll {
  width: 100%;
  white-space: nowrap;
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.experience-filter-scroll::-webkit-scrollbar,
.community-filter-scroll::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.experience-filter-row {
  display: flex;
  gap: 12rpx;
  min-width: max-content;
  padding: 0 2rpx 2rpx;
}

.experience-filter-chip {
  min-width: 116rpx;
  min-height: 58rpx;
  margin: 0;
  padding: 0 18rpx;
  border-radius: 18rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.72);
  background: rgba(248, 251, 250, 0.62);
  color: #60716f;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 22rpx;
  line-height: 1.2;
  font-weight: 800;
  -webkit-backdrop-filter: blur(14px) saturate(112%);
  backdrop-filter: blur(14px) saturate(112%);
  transition: transform 180ms ease, color 180ms ease, background-color 180ms ease;
}

.experience-filter-chip.active {
  border-color: rgba(22, 120, 111, 0.16);
  background: rgba(225, 242, 237, 0.82);
  color: #16786f;
}

.experience-card {
  padding: 28rpx;
  border-radius: 30rpx;
  background: #ffffff;
  border: 2rpx solid #edf2fb;
  box-shadow: 0 16rpx 42rpx rgba(25, 48, 89, 0.07);
}

.experience-author-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 20rpx;
}

.experience-avatar {
  width: 62rpx;
  height: 62rpx;
  border-radius: 22rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 25rpx;
  line-height: 1;
  font-weight: 900;
}

.experience-avatar-image {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: inherit;
  object-fit: cover;
}

.experience-author-main {
  min-width: 0;
  flex: 1;
}

.experience-author-name {
  color: #101828;
  font-size: 25rpx;
  line-height: 1.25;
  font-weight: 900;
}

.experience-author-role {
  margin-top: 4rpx;
  color: #98a2b3;
  font-size: 21rpx;
  line-height: 1.25;
  font-weight: 800;
}

.experience-exam {
  padding: 7rpx 12rpx;
  border-radius: 999rpx;
  background: #f6f8fc;
  color: #667085;
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 900;
  flex-shrink: 0;
}

.experience-card:active,
.material-card:active {
  transform: translateY(1rpx);
}

.experience-top,
.experience-footer,
.material-title-row,
.material-share-line {
  display: flex;
  align-items: center;
}

.experience-top,
.experience-footer,
.material-title-row {
  justify-content: space-between;
  gap: 16rpx;
}

.experience-tag,
.material-badge {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  font-size: 21rpx;
  line-height: 1.2;
  font-weight: 900;
}

.experience-read {
  color: #98a2b3;
  font-size: 22rpx;
  line-height: 1.2;
  font-weight: 800;
}

.experience-title {
  margin-top: 18rpx;
  color: #101828;
  font-size: 32rpx;
  line-height: 1.35;
  font-weight: 900;
}

.experience-summary {
  margin-top: 12rpx;
  color: #667085;
  font-size: 25rpx;
  line-height: 1.55;
  font-weight: 700;
}

.experience-meta-row {
  margin-top: 14rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx 16rpx;
  color: #98a2b3;
  font-size: 21rpx;
  line-height: 1.3;
  font-weight: 800;
}

.experience-points,
.material-tags {
  margin-top: 18rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.experience-points text,
.material-tags text {
  padding: 8rpx 12rpx;
  border-radius: 12rpx;
  background: #f6f8fc;
  color: #475467;
  font-size: 21rpx;
  line-height: 1.2;
  font-weight: 800;
}

.experience-footer {
  margin-top: 20rpx;
  padding-top: 18rpx;
  border-top: 2rpx solid #f0f4fb;
}

.experience-author {
  color: #8a94a6;
  font-size: 23rpx;
  line-height: 1.2;
  font-weight: 800;
}

.experience-stats {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8rpx 12rpx;
  min-width: 0;
  color: #98a2b3;
  font-size: 21rpx;
  line-height: 1.3;
  font-weight: 800;
}

.experience-action {
  color: var(--gyt-primary, #3478f6);
  font-size: 24rpx;
  line-height: 1.2;
  font-weight: 900;
}

.circle-community-section {
  gap: 14rpx;
  padding-bottom: 24rpx;
}

.circle-community-tabs {
  position: relative;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 0;
  padding: 0 10rpx;
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 8rpx 22rpx rgba(25, 48, 89, 0.055);
  overflow: hidden;
}

.circle-community-tab {
  position: relative;
  min-width: 0;
  min-height: 72rpx;
  margin: 0;
  padding: 0 6rpx;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: #69758a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  line-height: 1.2;
  font-weight: 760;
  transition: color 180ms ease, transform 180ms ease;
}

.circle-community-tab::after,
.community-filter-chip::after {
  border: 0;
}

.circle-community-tab.active {
  background: transparent;
  color: var(--gyt-primary, #3478f6);
  box-shadow: none;
  font-weight: 900;
}

.circle-community-tab.active::before {
  content: '';
  position: absolute;
  right: 28%;
  bottom: 7rpx;
  left: 28%;
  height: 5rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary, #3478f6);
}

.circle-community-tab:active,
.community-filter-chip:active {
  transform: scale(0.98);
}

.community-filter-scroll {
  width: 100%;
  white-space: nowrap;
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.community-filter-scroll :deep(.uni-scroll-view) {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.community-filter-scroll :deep(.uni-scroll-view)::-webkit-scrollbar {
  display: none;
  width: 0;
  height: 0;
}

.community-filter-row {
  display: flex;
  gap: 7rpx;
  min-width: max-content;
  padding: 0 2rpx 4rpx;
}

.community-filter-chip {
  min-width: 112rpx;
  min-height: 54rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 0;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.76);
  color: #647086;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 21rpx;
  line-height: 1.2;
  font-weight: 760;
  transition: transform 180ms ease, color 180ms ease, background-color 180ms ease;
}

.community-filter-chip.active {
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  font-weight: 900;
}

.community-feed {
  box-sizing: border-box;
  width: 100%;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 0;
  border: 2rpx solid rgba(215, 229, 255, 0.9);
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 12rpx 34rpx rgba(25, 48, 89, 0.065);
  overflow: hidden;
}

.community-feed.is-empty {
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  overflow: visible;
}

.community-load-state {
  width: 100%;
  box-sizing: border-box;
  padding: 24rpx 20rpx;
  border-top: 2rpx solid rgba(94, 111, 138, 0.09);
  color: #8190a4;
  font-size: 19rpx;
  line-height: 1.4;
  font-weight: 750;
  text-align: center;
}

.community-post-card {
  padding: 28rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.78);
  border-radius: 30rpx;
  background: rgba(248, 252, 250, 0.8);
  box-shadow: 0 16rpx 40rpx rgba(30, 55, 56, 0.075);
  -webkit-backdrop-filter: blur(18px) saturate(118%);
  backdrop-filter: blur(18px) saturate(118%);
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.community-post-card:active {
  transform: scale(0.985);
  box-shadow: 0 10rpx 26rpx rgba(30, 55, 56, 0.08);
}

.community-post-header {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.community-avatar {
  width: 64rpx;
  height: 64rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.76);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #16786f;
  font-size: 25rpx;
  line-height: 1;
  font-weight: 800;
  flex-shrink: 0;
}

.community-avatar-image {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: inherit;
  object-fit: cover;
}

.community-avatar.tone-mint {
  background: #dff0eb;
  color: #16786f;
}

.community-avatar.tone-blue {
  background: #e4eef7;
  color: #4c718e;
}

.community-avatar.tone-warm {
  background: #f4eadb;
  color: #a56c3b;
}

.community-avatar.tone-violet {
  background: #ece9f4;
  color: #756491;
}

.community-author-main {
  min-width: 0;
  flex: 1;
}

.community-author-name {
  color: #1c2423;
  font-size: 25rpx;
  line-height: 1.25;
  font-weight: 800;
}

.community-author-meta {
  margin-top: 4rpx;
  color: #83918f;
  font-size: 21rpx;
  line-height: 1.2;
  font-weight: 600;
}

.community-topic {
  max-width: 150rpx;
  padding: 8rpx 12rpx;
  border-radius: 999rpx;
  background: rgba(232, 242, 239, 0.82);
  color: #4f6c67;
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 800;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex-shrink: 0;
}

.community-post-title {
  margin-top: 20rpx;
  color: #172221;
  font-size: 31rpx;
  line-height: 1.38;
  font-weight: 800;
}

.community-post-copy {
  margin-top: 12rpx;
  color: #647573;
  font-size: 24rpx;
  line-height: 1.58;
  font-weight: 600;
}

.community-media-grid {
  margin-top: 20rpx;
  display: grid;
  grid-template-columns: repeat(3, 180rpx);
  justify-content: start;
  gap: 12rpx;
}

.community-media-tile {
  box-sizing: border-box;
  width: 180rpx;
  height: 320rpx;
  padding: 18rpx 16rpx;
  border-radius: 20rpx;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
  overflow: hidden;
}

.community-media-tile.is-image {
  padding: 0;
  background: #e7efee;
}

.community-media-image {
  width: 100%;
  height: 100%;
  display: block;
}

.community-media-text {
  margin-top: auto;
}

.community-media-tile.tone-sky {
  background: linear-gradient(145deg, #dcecf2, #accbd8);
  color: #315867;
}

.community-media-tile.tone-mint {
  background: linear-gradient(145deg, #d9eee8, #a9d2c7);
  color: #285f57;
}

.community-media-tile.tone-warm {
  background: linear-gradient(145deg, #f5ebdb, #dfc49d);
  color: #79522c;
}

.community-media-tile.tone-paper {
  background: linear-gradient(145deg, #f5f1e8, #d9d0bf);
  color: #625d50;
}

.community-media-kicker {
  font-size: 18rpx;
  line-height: 1.2;
  font-weight: 700;
  opacity: 0.76;
}

.community-media-title {
  margin-top: 8rpx;
  font-size: 23rpx;
  line-height: 1.25;
  font-weight: 800;
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.community-media-copy {
  margin-top: 6rpx;
  font-size: 18rpx;
  line-height: 1.3;
  font-weight: 600;
  opacity: 0.8;
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.community-comment-preview-list {
  margin-top: 18rpx;
  padding-top: 16rpx;
  border-top: 2rpx solid rgba(99, 124, 120, 0.12);
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.community-comment-preview {
  color: #667775;
  font-size: 22rpx;
  line-height: 1.5;
  font-weight: 600;
  display: flex;
  min-width: 0;
}

.community-comment-name {
  color: #3f5b56;
  font-weight: 800;
  flex-shrink: 0;
}

.community-comment-preview-copy {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.community-post-footer {
  margin-top: 18rpx;
  padding-top: 16rpx;
  border-top: 2rpx solid rgba(99, 124, 120, 0.12);
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: center;
  gap: 10rpx;
  color: #83918f;
  font-size: 26rpx;
  line-height: 1.25;
  font-weight: 700;
}

.community-post-action {
  width: 100%;
  box-sizing: border-box;
  min-width: 0;
  min-height: 56rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  color: #7a8987;
  font: inherit;
  white-space: nowrap;
}

.community-post-action::after {
  border: 0;
}

.community-post-action.active {
  color: #eb5964;
}

.community-post-action:active {
  transform: scale(0.96);
}

.community-action-icon {
  width: 34rpx;
  height: 34rpx;
  flex: 0 0 34rpx;
}

.home-page.circle-glass-page .community-stream .community-stream-card {
  min-width: 0;
  padding: 28rpx 26rpx 18rpx;
  border: 0;
  border-radius: 0;
  background: #ffffff;
  box-shadow: none;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
  transform: none;
  transition: background-color 160ms ease;
}

.home-page.circle-glass-page .community-stream .community-stream-card + .community-stream-card {
  border-top: 12rpx solid var(--gyt-page-bg, #f4f8ff);
}

.home-page.circle-glass-page .community-stream .community-stream-card:active {
  background: #fbfcff;
  box-shadow: none;
  transform: none;
}

.community-stream .community-post-header {
  gap: 14rpx;
}

.community-stream .community-avatar {
  width: 70rpx;
  height: 70rpx;
  font-size: 25rpx;
  box-shadow: 0 5rpx 14rpx rgba(25, 48, 89, 0.08);
}

.community-stream .community-author-name {
  overflow: hidden;
  color: #172033;
  font-size: 25rpx;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.community-stream .community-author-meta {
  margin-top: 6rpx;
  color: #8b96a8;
  font-size: 18rpx;
}

.community-stream-header-actions {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 5rpx;
  flex-shrink: 0;
}

.community-topic-list {
  min-width: 0;
  max-width: 292rpx;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 6rpx;
}

.community-topic-list .community-topic {
  max-width: none;
  flex: 0 0 auto;
}

.community-detail-topic-list {
  margin-left: auto;
}

.community-stream .community-topic {
  max-width: 142rpx;
  padding: 7rpx 12rpx;
  background: var(--gyt-primary-tint, #f4f8ff);
  color: var(--gyt-primary, #3478f6);
  font-size: 18rpx;
}

.community-post-more {
  width: 52rpx;
  height: 52rpx;
  min-width: 52rpx;
  min-height: 52rpx;
  margin: 0 -6rpx 0 0;
  padding: 12rpx;
  border: 0;
  border-radius: 50%;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
}

.community-post-more::after {
  border: 0;
}

.community-post-more image {
  width: 100%;
  height: 100%;
  opacity: 0.62;
}

.community-post-more:active {
  background: var(--gyt-primary-soft, #edf4ff);
}

.community-stream .community-post-title {
  margin-top: 22rpx;
  color: #151d2c;
  font-size: 31rpx;
  line-height: 1.36;
  font-weight: 900;
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.community-stream .community-post-copy {
  margin-top: 10rpx;
  color: #4f5e72;
  font-size: 24rpx;
  line-height: 1.62;
  font-weight: 560;
  display: -webkit-box;
  overflow: hidden;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.community-stream .community-media-grid {
  width: 100%;
  margin-top: 20rpx;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6rpx;
}

.community-stream .community-media-grid.count-1 {
  grid-template-columns: minmax(0, 1fr);
}

.community-stream .community-media-grid.count-2 {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.community-stream .community-media-tile {
  position: relative;
  width: 100%;
  height: 206rpx;
  min-width: 0;
  padding: 16rpx 14rpx;
  border-radius: 18rpx;
  background: #edf2f7;
}

.community-stream .community-media-grid.count-1 .community-media-tile {
  height: 390rpx;
  border-radius: 24rpx;
}

.community-stream .community-media-grid.count-2 .community-media-tile {
  height: 284rpx;
  border-radius: 20rpx;
}

.community-stream .community-media-kicker,
.community-stream .community-media-copy {
  font-size: 17rpx;
}

.community-stream .community-media-title {
  margin-top: 6rpx;
  font-size: 21rpx;
}

.community-media-more {
  position: absolute;
  right: 8rpx;
  bottom: 8rpx;
  min-width: 40rpx;
  padding: 5rpx 8rpx;
  border-radius: 999rpx;
  background: rgba(19, 32, 49, 0.62);
  color: #fff;
  font-size: 17rpx;
  line-height: 1.2;
  font-weight: 800;
  text-align: center;
}

.community-stream .community-comment-preview-list {
  margin-top: 18rpx;
  padding: 14rpx 16rpx;
  border: 0;
  border-radius: 16rpx;
  background: #f6f8fb;
}

.community-stream .community-comment-preview {
  font-size: 21rpx;
  line-height: 1.42;
}

.community-stream .community-post-footer {
  margin-top: 15rpx;
  padding-top: 12rpx;
  border-top-color: rgba(94, 111, 138, 0.1);
  gap: 6rpx;
  font-size: 22rpx;
}

.community-stream .community-post-action {
  min-height: 50rpx;
  gap: 8rpx;
}

.community-stream .community-action-icon {
  width: 30rpx;
  height: 30rpx;
  flex-basis: 30rpx;
}

.community-publish-button {
  position: fixed;
  z-index: 30;
  right: 20px;
  bottom: calc(env(safe-area-inset-bottom) + 22px);
  width: 56px;
  height: 56px;
  min-width: 56px;
  min-height: 56px;
  margin: 0;
  padding: 15px;
  border: 0;
  border-radius: 50%;
  background: #3478F6;
  box-shadow: 0 12px 26px rgba(52, 120, 246, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: auto;
  touch-action: manipulation;
  -webkit-tap-highlight-color: transparent;
  transition: transform 180ms ease, box-shadow 180ms ease, background-color 180ms ease;
}

.mentor-console-entry,
.mentor-pending-entry {
  width: auto;
  height: 50px;
  min-height: 50px;
  padding: 0 16px;
  border-radius: 999px;
}

.mentor-console-entry {
  min-width: 108px;
}

.mentor-pending-entry {
  min-width: 88px;
  background: #6687ba;
  box-shadow: 0 10px 22px rgba(69, 103, 154, 0.24);
}

.mentor-entry-content {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 7px;
  color: #fff;
  font-size: 14px;
  line-height: 1;
  font-weight: 760;
  white-space: nowrap;
}

.mentor-entry-grid-icon {
  width: 13px;
  height: 13px;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 2px;
}

.mentor-entry-grid-icon view {
  border-radius: 2px;
  background: currentColor;
}

.mentor-entry-pending-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #dceaff;
  box-shadow: 0 0 0 3px rgba(220, 234, 255, 0.18);
}

.community-publish-button::after {
  border: 0;
}

.community-publish-button image {
  width: 100%;
  height: 100%;
  display: block;
  pointer-events: none;
}

.community-publish-button:active {
  transform: scale(0.94);
  box-shadow: 0 7px 16px rgba(52, 120, 246, 0.2);
  background: #2867DE;
}

.community-reader {
  position: fixed;
  z-index: 110;
  inset: 0;
  box-sizing: border-box;
  width: 100vw;
  height: 100vh;
  height: 100dvh;
  overflow: hidden;
  background: rgba(15, 48, 51, 0.42);
  transform: translate3d(0, 0, 0);
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
}

.community-reader.is-route-moving {
  pointer-events: none;
  transition: transform var(--gyt-route-duration, 380ms) var(--gyt-route-ease, cubic-bezier(0.25, 0.8, 0.25, 1));
  box-shadow: -18rpx 0 42rpx rgba(17, 31, 47, 0.18);
}

.community-reader.is-route-moving,
.community-reader.is-route-offscreen {
  will-change: transform;
}

.community-reader.is-route-offscreen {
  transform: translate3d(100%, 0, 0);
}

.community-reader-surface {
  width: 100%;
  max-width: 860rpx;
  height: 100vh;
  height: 100dvh;
  margin: 0 auto;
  overflow: hidden;
  isolation: isolate;
  -webkit-backface-visibility: hidden;
  backface-visibility: hidden;
  background:
    linear-gradient(180deg, rgba(224, 239, 237, 0.96) 0%, rgba(245, 249, 247, 0.98) 38%, rgba(232, 241, 239, 0.98) 100%),
    url('/static/circle-study-sky.jpg') center / cover;
  display: flex;
  flex-direction: column;
}

.community-reader.is-closing .community-reader-surface {
  pointer-events: none;
}

.community-reader-topbar {
  box-sizing: border-box;
  min-height: 116rpx;
  padding: calc(env(safe-area-inset-top) + 20rpx) 24rpx 18rpx;
  border-bottom: 2rpx solid rgba(78, 111, 106, 0.12);
  background: rgba(243, 249, 248, 0.84);
  display: flex;
  align-items: center;
  gap: 14rpx;
  flex: 0 0 auto;
  -webkit-backdrop-filter: blur(18px) saturate(118%);
  backdrop-filter: blur(18px) saturate(118%);
}

.community-reader-back,
.community-reader-share {
  width: 66rpx;
  height: 66rpx;
  min-width: 66rpx;
  min-height: 66rpx;
  margin: 0;
  padding: 16rpx;
  border: 0;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.72);
  color: #2d8580;
  display: flex;
  align-items: center;
  justify-content: center;
}

.community-reader-back::after,
.community-reader-share::after {
  border: 0;
}

.community-reader-back image {
  width: 100%;
  height: 100%;
}

.community-reader-share {
  padding: 0 0 8rpx 2rpx;
  color: #237a76;
  font-size: 44rpx;
  line-height: 1;
  font-weight: 500;
}

.community-reader-author {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex: 1;
}

.community-reader-avatar,
.community-reader-comment-avatar {
  overflow: hidden;
  border: 2rpx solid rgba(255, 255, 255, 0.88);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 800;
  flex: 0 0 auto;
}

.community-reader-avatar {
  width: 62rpx;
  height: 62rpx;
  color: #2e7a77;
  font-size: 26rpx;
}

.community-reader-avatar image,
.community-reader-comment-avatar image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.community-reader-author-copy {
  min-width: 0;
}

.community-reader-top-hitbox {
  min-width: 28rpx;
  align-self: stretch;
  flex: 1;
  -webkit-user-select: none;
  user-select: none;
  touch-action: manipulation;
}

.community-reader-author-name {
  overflow: hidden;
  color: #1b2b2a;
  font-size: 27rpx;
  line-height: 1.25;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.community-reader-author-meta {
  overflow: hidden;
  margin-top: 3rpx;
  color: #788a87;
  font-size: 19rpx;
  line-height: 1.2;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.community-reader-category {
  max-width: 122rpx;
  padding: 12rpx 15rpx;
  overflow: hidden;
  border-radius: 999rpx;
  background: rgba(45, 133, 128, 0.11);
  color: #237a76;
  font-size: 19rpx;
  line-height: 1;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 0 1 auto;
}

.community-reader-tag-list {
  min-width: 0;
  max-width: 286rpx;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 6rpx;
  flex: 0 1 auto;
}

.community-reader-tag-list .community-reader-category {
  max-width: none;
  flex: 0 0 auto;
}

.community-reader-scroll {
  width: 100%;
  min-height: 0;
  flex: 1;
}

.community-reader-body {
  box-sizing: border-box;
  min-height: 100%;
  padding: 34rpx 30rpx calc(env(safe-area-inset-bottom) + 46rpx);
}

.community-reader-title {
  color: #172725;
  font-size: 42rpx;
  line-height: 1.32;
  font-weight: 800;
  word-break: break-word;
}

.community-reader-copy {
  margin-top: 20rpx;
  color: #506562;
  font-size: 28rpx;
  line-height: 1.72;
  font-weight: 600;
  white-space: pre-line;
  word-break: break-word;
}

.community-reader-media {
  position: relative;
  margin-top: 28rpx;
}

.community-reader-media + .community-reader-title {
  margin-top: 32rpx;
}

.community-reader-media-swiper {
  height: min(72vh, 920rpx);
  overflow: hidden;
  border: 2rpx solid rgba(255, 255, 255, 0.9);
  border-radius: 30rpx;
  background: rgba(255, 255, 255, 0.62);
  box-shadow: 0 16rpx 34rpx rgba(39, 80, 75, 0.12);
}

.community-reader-media-slide {
  width: 100%;
  height: 100%;
  overflow: hidden;
  background: #eaf3f2;
  display: flex;
  align-items: center;
  justify-content: center;
}

.community-reader-media-slide image {
  width: 100%;
  height: 100%;
  cursor: zoom-in;
}

.community-reader-owner-status {
  width: fit-content;
  margin-bottom: 20rpx;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: rgba(52, 120, 246, .1);
  color: #3478f6;
  font-size: 20rpx;
  line-height: 1;
  font-weight: 800;
}

.community-reader-owner-status.is-pending {
  background: rgba(214, 151, 44, .12);
  color: #a36d15;
}

.community-reader-owner-status.is-archived {
  background: rgba(126, 136, 156, .12);
  color: #69758a;
}

.community-reader-media-slide.tone-blue {
  background: linear-gradient(145deg, #dceeff, #edf6fc);
}

.community-reader-media-slide.tone-mint {
  background: linear-gradient(145deg, #dff4ee, #eef8f5);
}

.community-reader-media-slide.tone-sand {
  background: linear-gradient(145deg, #f8ecd8, #fff7ed);
}

.community-reader-media-slide.tone-lilac {
  background: linear-gradient(145deg, #eee7fa, #f8f4fd);
}

.community-reader-media-fallback {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  padding: 56rpx 42rpx;
  color: #2c5d5a;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.community-reader-media-fallback view {
  font-size: 24rpx;
  line-height: 1.25;
  font-weight: 700;
}

.community-reader-media-fallback-title {
  margin-top: 14rpx;
  color: #214e4a;
  font-size: 42rpx;
  line-height: 1.25;
}

.community-reader-media-fallback text {
  margin-top: 16rpx;
  font-size: 28rpx;
  line-height: 1.55;
  font-weight: 600;
}

.community-reader-media-count {
  position: absolute;
  top: 18rpx;
  right: 18rpx;
  min-width: 70rpx;
  padding: 11rpx 14rpx;
  border-radius: 999rpx;
  background: rgba(25, 58, 57, 0.66);
  color: #ffffff;
  font-size: 21rpx;
  line-height: 1;
  font-weight: 800;
  text-align: center;
}

.community-reader-comments-section {
  box-sizing: border-box;
  min-height: calc(100dvh - 320rpx);
  margin-top: 46rpx;
  padding: 30rpx 0 44rpx;
  border-top: 2rpx solid rgba(85, 116, 112, 0.16);
}

.community-reader-comments-toolbar {
  min-height: 68rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.community-reader-comments-tabs {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex: 1;
}

.community-reader-comments-tab {
  min-height: 58rpx;
  margin: 0;
  padding: 0 16rpx;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  color: #7a8a87;
  font-size: 26rpx;
  line-height: 1;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  white-space: nowrap;
}

.community-reader-comments-tab::after,
.community-reader-sort button::after,
.community-reader-actions button::after {
  border: 0;
}

.community-reader-comments-tab.active {
  background: rgba(255, 255, 255, 0.78);
  color: #1d2d2b;
  box-shadow: 0 4rpx 14rpx rgba(44, 79, 74, 0.08);
}

.community-reader-sort {
  min-height: 62rpx;
  padding: 4rpx;
  border-radius: 999rpx;
  background: rgba(223, 237, 234, 0.92);
  display: flex;
  align-items: center;
  flex: 0 0 auto;
}

.community-reader-sort button {
  width: 62rpx;
  min-width: 62rpx;
  height: 54rpx;
  min-height: 54rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 999rpx;
  background: transparent;
  color: #71817e;
  font-size: 19rpx;
  line-height: 1;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.community-reader-sort button.active {
  background: rgba(255, 255, 255, 0.94);
  color: #3478f6;
  box-shadow: 0 3rpx 10rpx rgba(53, 84, 80, 0.08);
}

.community-reader-comment-placeholder {
  color: #9aa9a6;
}

.community-reader-empty {
  margin-top: 26rpx;
  padding: 32rpx 24rpx;
  border-radius: 24rpx;
  background: rgba(236, 245, 243, 0.82);
  color: #768683;
  font-size: 24rpx;
  line-height: 1.55;
  font-weight: 600;
  text-align: center;
}

.community-reader-comment-list,
.community-reader-like-list {
  margin-top: 16rpx;
}

.community-comments-page-action {
  width: 100%;
  min-height: 58rpx;
  margin: 0 0 8rpx;
  padding: 0;
  border: 0;
  background: transparent;
  color: #5f7f7b;
  font-size: 21rpx;
  line-height: 58rpx;
  font-weight: 700;
  text-align: center;
}

.community-comments-page-action::after,
.community-comment-retry::after {
  border: 0;
}

.community-reader-comment-item,
.community-reader-like-item {
  padding: 28rpx 0;
  border-bottom: 2rpx solid rgba(91, 120, 116, 0.12);
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
}

.community-reader-comment-item.is-sending {
  opacity: 0.72;
}

.community-reader-comment-item.is-failed {
  border-radius: 18rpx;
  background: rgba(235, 89, 100, 0.045);
}

.community-reader-comment-avatar {
  width: 72rpx;
  height: 72rpx;
  background: #e1f0ed;
  color: #217b75;
  font-size: 28rpx;
}

.community-reader-comment-main {
  min-width: 0;
  padding-top: 3rpx;
  flex: 1;
}

.community-reader-comment-author {
  overflow: hidden;
  color: #263c39;
  font-size: 26rpx;
  line-height: 1.3;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.community-reader-comment-copy {
  margin-top: 10rpx;
  color: #4e625f;
  font-size: 28rpx;
  line-height: 1.58;
  font-weight: 600;
  word-break: break-word;
}

.community-reader-comment-time {
  margin-top: 11rpx;
  color: #98a6a3;
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 600;
}

.community-comment-delivery-state {
  color: #718c88;
}

.community-comment-retry {
  display: inline-flex;
  min-height: 36rpx;
  margin: 0 0 0 8rpx;
  padding: 0;
  border: 0;
  background: transparent;
  color: #d84b58;
  font-size: 20rpx;
  line-height: 36rpx;
  font-weight: 750;
  vertical-align: middle;
}

.community-reader-comment-like {
  width: 88rpx;
  min-width: 88rpx;
  min-height: 96rpx;
  margin: 0;
  padding: 8rpx 0;
  border: 0;
  background: transparent;
  color: #81918e;
  display: flex;
  flex: 0 0 88rpx;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4rpx;
}

.community-reader-comment-like::after {
  border: 0;
}

.community-reader-comment-like-icon-image {
  display: block;
  width: 42rpx;
  height: 42rpx;
  opacity: 0.72;
  transition: opacity 180ms ease, transform 180ms ease;
}

.community-reader-comment-like text {
  min-width: 100%;
  color: currentColor;
  font-size: 21rpx;
  line-height: 1.1;
  font-weight: 800;
  text-align: center;
}

.community-reader-comment-like.active {
  color: #eb5964;
}

.community-reader-comment-like.active .community-reader-comment-like-icon-image {
  opacity: 1;
  animation: community-reader-like-pop 260ms cubic-bezier(0.2, 0.9, 0.3, 1.22);
  transform: scale(1);
}

.community-reader-actions {
  position: relative;
  z-index: 8;
  box-sizing: border-box;
  min-height: 104rpx;
  padding: 14rpx 24rpx calc(env(safe-area-inset-bottom) + 14rpx);
  border-top: 2rpx solid rgba(84, 117, 112, 0.13);
  background: rgba(245, 250, 248, 0.92);
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex: 0 0 auto;
  -webkit-backdrop-filter: blur(18px) saturate(120%);
  backdrop-filter: blur(18px) saturate(120%);
  transition-property: transform;
  transition-timing-function: cubic-bezier(0.22, 0.8, 0.28, 1);
  will-change: transform;
}

.community-reader-actions.keyboard-open {
  padding-bottom: 14rpx;
  background: rgba(245, 250, 248, 0.98);
  box-shadow: 0 -12rpx 30rpx rgba(36, 73, 69, 0.1);
}

.community-reader-actions.keyboard-open .community-reader-comment-entry {
  background: #ffffff;
  box-shadow: inset 0 0 0 2rpx rgba(45, 133, 128, 0.16);
}

.community-reader-comment-entry {
  min-width: 0;
  min-height: 66rpx;
  margin: 0;
  padding: 0 18rpx;
  border: 0;
  border-radius: 999rpx;
  background: rgba(224, 237, 234, 0.92);
  color: #80918e;
  display: flex;
  align-items: center;
  gap: 10rpx;
  font-size: 23rpx;
  line-height: 1;
  font-weight: 700;
  flex: 1;
}

.community-reader-comment-entry image {
  width: 28rpx;
  height: 28rpx;
  opacity: 0.72;
  flex: 0 0 28rpx;
}

.community-reader-comment-entry input {
  min-width: 0;
  color: #25413d;
  font-size: 23rpx;
  font-weight: 700;
  flex: 1;
}

.community-reader-comment-prompt {
  min-width: 0;
  overflow: hidden;
  color: #9aa9a6;
  font-size: 23rpx;
  line-height: 1.4;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
}

.community-reader-action {
  min-width: 86rpx;
  min-height: 76rpx;
  margin: 0;
  padding: 0 12rpx;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  color: #70827f;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
  font-size: 21rpx;
  line-height: 1;
  font-weight: 800;
  flex: 0 0 auto;
  overflow: visible;
}

.community-reader-action image {
  width: 30rpx;
  height: 30rpx;
}

.community-reader-action::after {
  border: 0;
}

.community-reader-like-icon-wrap {
  position: relative;
  z-index: 1;
  width: 46rpx;
  height: 46rpx;
  flex: 0 0 46rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
}

.community-reader-action .community-reader-like-icon {
  position: relative;
  z-index: 1;
  display: block;
  width: 46rpx;
  height: 46rpx;
  flex: 0 0 46rpx;
  transform-origin: center;
}

.community-reader-action.active {
  color: #eb5964;
}

.community-reader-action.is-bursting .community-reader-like-icon {
  animation: community-reader-like-pop 260ms cubic-bezier(0.2, 0.9, 0.3, 1.22) both;
}

.community-like-burst {
  position: absolute;
  z-index: 2;
  inset: 0;
  pointer-events: none;
  overflow: visible;
}

.community-reader-action .community-like-bubble {
  --community-like-bubble-x: 0rpx;
  --community-like-bubble-y: -70rpx;
  --community-like-bubble-rotate: 0deg;
  position: absolute;
  top: 50%;
  left: 50%;
  display: block;
  width: 18rpx;
  height: 18rpx;
  opacity: 0;
  transform: translate(-50%, -50%) translate3d(0, 6rpx, 0) scale(0.35);
  transform-origin: center;
  animation: community-like-bubble-rise 480ms cubic-bezier(0.2, 0.72, 0.24, 1) forwards;
  will-change: transform, opacity;
}

.community-reader-action .community-like-bubble:nth-child(1) {
  --community-like-bubble-x: -42rpx;
  --community-like-bubble-y: -60rpx;
  --community-like-bubble-rotate: -18deg;
  width: 16rpx;
  height: 16rpx;
}

.community-reader-action .community-like-bubble:nth-child(2) {
  --community-like-bubble-x: -22rpx;
  --community-like-bubble-y: -84rpx;
  --community-like-bubble-rotate: 12deg;
  animation-delay: 36ms;
}

.community-reader-action .community-like-bubble:nth-child(3) {
  --community-like-bubble-y: -74rpx;
  --community-like-bubble-rotate: -8deg;
  width: 21rpx;
  height: 21rpx;
  animation-delay: 18ms;
}

@keyframes community-reader-like-pop {
  0% {
    transform: scale(0.9);
  }
  46% {
    transform: scale(1.12);
  }
  100% {
    transform: scale(1);
  }
}

@keyframes community-like-bubble-rise {
  0% {
    opacity: 0;
    transform: translate(-50%, -50%) translate3d(0, 6rpx, 0) scale(0.35) rotate(0deg);
  }
  18% {
    opacity: 0.96;
  }
  68% {
    opacity: 0.88;
    transform: translate(-50%, -50%) translate3d(var(--community-like-bubble-x), var(--community-like-bubble-y), 0) scale(1) rotate(var(--community-like-bubble-rotate));
  }
  100% {
    opacity: 0;
    transform: translate(-50%, -50%) translate3d(var(--community-like-bubble-x), var(--community-like-bubble-y), 0) scale(0.72) rotate(var(--community-like-bubble-rotate));
  }
}

@media (prefers-reduced-motion: reduce) {
  .community-reader-comment-like.active .community-reader-comment-like-icon-image,
  .community-reader-action.is-bursting .community-reader-like-icon {
    animation-duration: 1ms;
  }

  .community-reader-action .community-like-bubble {
    display: none;
  }
}

.community-reader-share:active,
.community-reader-back:active {
  transform: scale(0.96);
}

.community-reader-action:active {
  transform: none;
}

@media (max-width: 340px) {
  .community-reader-topbar {
    gap: 10rpx;
  }

  .community-reader-tag-list {
    max-width: 170rpx;
  }

  .community-reader-category {
    max-width: 82rpx;
    padding-right: 10rpx;
    padding-left: 10rpx;
  }

  .community-reader-comments-tab {
    padding-right: 10rpx;
    padding-left: 10rpx;
    font-size: 23rpx;
  }

  .community-reader-sort button {
    width: 54rpx;
    min-width: 54rpx;
    font-size: 18rpx;
  }

  .community-reader-actions {
    gap: 7rpx;
  }

  .community-reader-comment-entry {
    padding-right: 13rpx;
    padding-left: 13rpx;
  }

  .community-reader-action {
    min-width: 54rpx;
    padding-right: 4rpx;
    padding-left: 4rpx;
  }
}

.community-detail-mask {
  position: fixed;
  z-index: 90;
  inset: 0;
  padding: 0 22rpx;
  background: rgba(18, 35, 35, 0.34);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.community-detail-sheet {
  position: relative;
  box-sizing: border-box;
  width: 100%;
  max-width: 760rpx;
  max-height: min(84vh, 1180rpx);
  padding: 20rpx 28rpx calc(env(safe-area-inset-bottom) + 22rpx);
  border: 2rpx solid rgba(255, 255, 255, 0.86);
  border-radius: 36rpx 36rpx 0 0;
  background: rgba(250, 253, 252, 0.96);
  box-shadow: 0 -18rpx 52rpx rgba(20, 43, 42, 0.2);
  -webkit-backdrop-filter: blur(22px) saturate(118%);
  backdrop-filter: blur(22px) saturate(118%);
  display: flex;
  flex-direction: column;
}

.community-detail-handle {
  width: 70rpx;
  height: 8rpx;
  margin: 0 auto 20rpx;
  border-radius: 999rpx;
  background: rgba(88, 110, 107, 0.18);
}

.community-detail-close {
  position: absolute;
  top: 18rpx;
  right: 22rpx;
  width: 48rpx;
  height: 48rpx;
  min-width: 48rpx;
  min-height: 48rpx;
  margin: 0;
  padding: 12rpx;
  border: 0;
  border-radius: 50%;
  background: rgba(52, 120, 246, 0.08);
  color: #3478f6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.community-detail-close::after {
  border: 0;
}

.community-detail-heading {
  padding-right: 66rpx;
  color: #1c2423;
  font-size: 32rpx;
  line-height: 1.2;
  font-weight: 800;
}

.community-detail-scroll {
  min-height: 0;
  max-height: 62vh;
  margin-top: 22rpx;
  flex: 1;
}

.community-detail-author-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.community-detail-title {
  margin-top: 22rpx;
  color: #172221;
  font-size: 34rpx;
  line-height: 1.38;
  font-weight: 800;
}

.community-detail-copy {
  margin-top: 14rpx;
  padding-right: 2rpx;
  color: #526562;
  font-size: 26rpx;
  line-height: 1.68;
  font-weight: 600;
  white-space: pre-line;
}

.community-detail-media {
  margin-top: 22rpx;
}

.community-detail-stats {
  margin-top: 24rpx;
  padding: 16rpx 0;
  border-top: 2rpx solid rgba(99, 124, 120, 0.12);
  border-bottom: 2rpx solid rgba(99, 124, 120, 0.12);
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #7a8987;
  font-size: 23rpx;
  line-height: 1.25;
  font-weight: 700;
}

.community-detail-like {
  min-height: 54rpx;
  margin: 0;
  padding: 0 16rpx;
  border: 0;
  border-radius: 18rpx;
  background: rgba(52, 120, 246, 0.08);
  color: #3478f6;
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  font-size: 23rpx;
  font-weight: 800;
}

.community-detail-like::after {
  border: 0;
}

.community-detail-like image {
  width: 28rpx;
  height: 28rpx;
}

.community-detail-like.active {
  background: rgba(52, 120, 246, 0.16);
}

.community-detail-like.pending {
  pointer-events: none;
}

.community-detail-comments-entry {
  width: 100%;
  margin: 22rpx 0 2rpx;
  padding: 20rpx;
  border: 2rpx solid rgba(222, 234, 231, 0.92);
  border-radius: 22rpx;
  background: rgba(242, 248, 246, 0.82);
  color: #3478f6;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  text-align: left;
}

.community-detail-comments-entry::after {
  border: 0;
}

.community-detail-comments-entry:active {
  transform: scale(0.98);
}

.community-detail-comments-count {
  color: #1c2423;
  font-size: 26rpx;
  line-height: 1.3;
  font-weight: 800;
}

.community-detail-comments-copy {
  margin-top: 4rpx;
  color: #82908e;
  font-size: 21rpx;
  line-height: 1.35;
  font-weight: 600;
}

.community-detail-comments-entry text {
  flex-shrink: 0;
  font-size: 22rpx;
  line-height: 1.2;
  font-weight: 800;
}

.community-comment-composer {
  margin-top: 18rpx;
  padding-top: 18rpx;
  border-top: 2rpx solid rgba(99, 124, 120, 0.12);
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.community-comment-input {
  min-width: 0;
  height: 68rpx;
  padding: 0 18rpx;
  border-radius: 20rpx;
  background: rgba(237, 244, 242, 0.86);
  color: #243532;
  font-size: 24rpx;
  font-weight: 600;
  flex: 1;
}

.community-comment-placeholder {
  color: #99a7a4;
  font-weight: 500;
}

.community-comment-submit {
  min-width: 92rpx;
  min-height: 68rpx;
  margin: 0;
  padding: 0 18rpx;
  border: 0;
  border-radius: 20rpx;
  background: #3478f6;
  color: #ffffff;
  font-size: 23rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
}

.community-comment-submit::after {
  border: 0;
}

.community-comment-submit[disabled] {
  opacity: 0.48;
}

.community-comments-mask {
  position: fixed;
  z-index: 96;
  inset: 0;
  background: rgba(18, 35, 35, 0.38);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.community-comments-sheet {
  position: relative;
  box-sizing: border-box;
  width: 100%;
  max-width: 760rpx;
  height: min(82vh, 1180rpx);
  padding: 20rpx 28rpx calc(env(safe-area-inset-bottom) + 22rpx);
  border: 2rpx solid rgba(255, 255, 255, 0.88);
  border-radius: 36rpx 36rpx 0 0;
  background: rgba(250, 253, 252, 0.97);
  box-shadow: 0 -18rpx 52rpx rgba(20, 43, 42, 0.22);
  -webkit-backdrop-filter: blur(22px) saturate(118%);
  backdrop-filter: blur(22px) saturate(118%);
  display: flex;
  flex-direction: column;
}

.community-comments-toolbar {
  min-height: 64rpx;
  padding-right: 0;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 14rpx;
}

.community-comments-counts {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 18rpx;
  white-space: nowrap;
}

.community-comments-count {
  min-height: 54rpx;
  margin: 0;
  padding: 0 14rpx;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  color: #93a09e;
  font-size: 26rpx;
  line-height: 1;
  font-weight: 800;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.community-comments-count::after {
  border: 0;
}

.community-comments-count.active {
  background: rgba(255, 255, 255, 0.56);
  color: #1c2423;
}

.community-comment-sort {
  min-height: 68rpx;
  margin-left: auto;
  padding: 5rpx;
  border-radius: 999rpx;
  background: rgba(231, 240, 238, 0.86);
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.community-comments-close {
  position: static;
  width: 58rpx;
  height: 58rpx;
  min-width: 58rpx;
  min-height: 58rpx;
  padding: 14rpx;
  flex: 0 0 58rpx;
}

.community-comments-counts + .community-comments-close {
  margin-left: auto;
}

.community-comment-sort-button {
  width: 84rpx;
  min-width: 84rpx;
  height: 58rpx;
  min-height: 58rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 999rpx;
  background: transparent;
  color: #73817f;
  font-size: 22rpx;
  line-height: 1;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.community-comment-sort-button::after {
  border: 0;
}

.community-comment-sort-button.active {
  background: rgba(255, 255, 255, 0.94);
  color: #3478f6;
  box-shadow: 0 4rpx 12rpx rgba(44, 71, 67, 0.08);
}

.community-comments-scroll {
  min-height: 0;
  margin-top: 24rpx;
  flex: 1;
}

.community-comments-list {
  padding-bottom: 8rpx;
}

.community-comments-item {
  padding: 22rpx 0;
  border-bottom: 2rpx solid rgba(99, 124, 120, 0.1);
  display: flex;
  gap: 16rpx;
}

.community-comments-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: #e5f2ee;
  color: #16786f;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  line-height: 1;
  font-weight: 800;
  flex: 0 0 64rpx;
}

.community-comments-avatar-image,
.community-likes-avatar-image {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: inherit;
  object-fit: cover;
}

.community-comments-main {
  min-width: 0;
  flex: 1;
}

.community-comments-author {
  color: #314643;
  font-size: 25rpx;
  line-height: 1.3;
  font-weight: 800;
}

.community-comments-copy {
  margin-top: 8rpx;
  color: #526562;
  font-size: 27rpx;
  line-height: 1.55;
  font-weight: 600;
  word-break: break-word;
}

.community-comments-time {
  margin-top: 9rpx;
  color: #99a6a4;
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 600;
}

.community-comments-empty {
  margin-top: 8rpx;
  padding: 28rpx 24rpx;
  border-radius: 22rpx;
  background: rgba(240, 246, 244, 0.78);
  color: #74817f;
  font-size: 23rpx;
  line-height: 1.5;
  font-weight: 600;
  text-align: center;
}

.community-likes-list {
  padding-bottom: 8rpx;
}

.community-likes-item {
  min-height: 84rpx;
  padding: 20rpx 0;
  border-bottom: 2rpx solid rgba(99, 124, 120, 0.1);
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.community-likes-avatar {
  width: 64rpx;
  height: 64rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.78);
  border-radius: 50%;
  background: #e5f2ee;
  color: #16786f;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  line-height: 1;
  font-weight: 800;
  flex: 0 0 64rpx;
}

.community-likes-main {
  min-width: 0;
  flex: 1;
}

.community-likes-author {
  overflow: hidden;
  color: #314643;
  font-size: 25rpx;
  line-height: 1.3;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.community-likes-time {
  margin-top: 7rpx;
  color: #99a6a4;
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 600;
}

.community-comments-composer {
  margin-top: 16rpx;
}

.material-subject-scroll {
  width: 100%;
  white-space: nowrap;
}

.material-subject-row {
  display: flex;
  gap: 12rpx;
  min-width: max-content;
  padding: 0 2rpx 2rpx;
}

.material-subject-chip {
  min-width: 132rpx;
  min-height: 62rpx;
  padding: 0 18rpx;
  border-radius: 18rpx;
  border: 2rpx solid #edf2fb;
  background: #ffffff;
  color: #667085;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 23rpx;
  line-height: 1.2;
  font-weight: 900;
}

.material-subject-chip.active {
  border-color: var(--gyt-primary-border, #d7e5ff);
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
}

.material-subject-card {
  padding: 26rpx 28rpx;
  border-radius: 28rpx;
  border: 2rpx solid rgba(229, 226, 224, .94);
  background: rgba(255, 255, 255, .94);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.material-subject-title {
  color: #101828;
  font-size: 30rpx;
  line-height: 1.2;
  font-weight: 900;
}

.material-subject-copy {
  margin-top: 8rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.45;
  font-weight: 700;
}

.material-subject-mark {
  width: 78rpx;
  height: 78rpx;
  border-radius: 24rpx;
  background: #ffffff;
  color: var(--gyt-primary, #3478f6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  line-height: 1;
  font-weight: 900;
  flex-shrink: 0;
}

.material-card {
  padding: 26rpx;
  border-radius: 28rpx;
  border: 2rpx solid #edf2fb;
  background: #ffffff;
  box-shadow: 0 14rpx 38rpx rgba(25, 48, 89, 0.06);
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.material-main {
  flex: 1;
  min-width: 0;
}

.material-title {
  color: #101828;
  font-size: 28rpx;
  line-height: 1.35;
  font-weight: 900;
}

.material-desc {
  margin-top: 10rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.5;
  font-weight: 700;
}

.material-share-line {
  margin-top: 16rpx;
  flex-wrap: wrap;
  gap: 10rpx 16rpx;
  color: #98a2b3;
  font-size: 21rpx;
  line-height: 1.35;
  font-weight: 800;
}

.material-action {
  width: 86rpx;
  min-height: 72rpx;
  padding: 0;
  border-radius: 20rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 23rpx;
  line-height: 1.2;
  font-weight: 900;
  flex-shrink: 0;
}

.circle-empty-card {
  min-height: 360rpx;
  padding: 44rpx 34rpx;
  border-radius: 28rpx;
  border: 2rpx solid #e8edf5;
  background: #ffffff;
  box-shadow: 0 14rpx 34rpx rgba(29, 42, 67, 0.05);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.circle-empty-icon {
  width: 96rpx;
  height: 96rpx;
  border-radius: 30rpx;
}

.circle-empty-title {
  margin-top: 22rpx;
  color: #172033;
  font-size: 34rpx;
  line-height: 1.25;
  font-weight: 900;
}

.circle-empty-copy {
  margin-top: 12rpx;
  max-width: 520rpx;
  color: #667085;
  font-size: 25rpx;
  line-height: 1.55;
  font-weight: 700;
}

.circle-resource-empty-section,
.circle-resource-empty-state {
  width: 100%;
  min-height: 620rpx;
}

.circle-resource-empty-state {
  padding: 40rpx 20rpx 72rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  text-align: center;
}

.circle-resource-empty-image {
  width: 240rpx;
  height: 240rpx;
  max-width: 150px;
  max-height: 150px;
  display: block;
  opacity: 0.92;
}

.circle-resource-empty-title {
  margin-top: 10rpx;
  color: #8d95a3;
  font-size: 28rpx;
  line-height: 1.35;
  font-weight: 800;
}

.circle-post-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 80;
  background: rgba(16, 24, 40, 0.36);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  padding: 0 22rpx;
}

.circle-post-sheet {
  position: relative;
  width: 100%;
  max-width: 760rpx;
  max-height: 78vh;
  padding: 20rpx 28rpx calc(env(safe-area-inset-bottom) + 30rpx);
  border-radius: 34rpx 34rpx 0 0;
  background: #ffffff;
  box-shadow: 0 -18rpx 52rpx rgba(25, 48, 89, 0.16);
}

.circle-post-handle {
  width: 78rpx;
  height: 8rpx;
  border-radius: 999rpx;
  background: #d9e1ef;
  margin: 0 auto 22rpx;
}

.circle-post-close {
  position: absolute;
  top: 22rpx;
  right: 24rpx;
  width: 58rpx;
  height: 58rpx;
  padding: 0;
  border-radius: 999rpx;
  background: #f4f7fb;
  display: flex;
  align-items: center;
  justify-content: center;
}

.circle-post-close::after {
  border: 0;
}

.circle-post-tag {
  display: inline-flex;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  font-size: 21rpx;
  line-height: 1.2;
  font-weight: 900;
}

.circle-post-title {
  margin-top: 18rpx;
  padding-right: 66rpx;
  color: #101828;
  font-size: 36rpx;
  line-height: 1.32;
  font-weight: 900;
}

.circle-post-meta {
  margin-top: 10rpx;
  color: #98a2b3;
  font-size: 23rpx;
  line-height: 1.2;
  font-weight: 800;
}

.circle-post-author-row {
  margin-top: 18rpx;
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.circle-post-avatar {
  width: 58rpx;
  height: 58rpx;
  border-radius: 20rpx;
}

.circle-post-author-main {
  min-width: 0;
  flex: 1;
}

.circle-post-author-name {
  color: #101828;
  font-size: 25rpx;
  line-height: 1.25;
  font-weight: 900;
}

.circle-post-stat-row {
  margin-top: 18rpx;
  padding: 16rpx 18rpx;
  border-radius: 20rpx;
  background: #f7f9fd;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx 16rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 800;
}

.circle-post-scroll {
  margin-top: 22rpx;
  max-height: 48vh;
}

.circle-post-section {
  margin-bottom: 24rpx;
}

.circle-post-section-title {
  margin-bottom: 10rpx;
  color: #101828;
  font-size: 28rpx;
  line-height: 1.3;
  font-weight: 900;
}

.circle-post-paragraph {
  color: #475467;
  font-size: 27rpx;
  line-height: 1.68;
  font-weight: 700;
}

.circle-post-checklist {
  margin-top: 10rpx;
  padding: 20rpx;
  border-radius: 24rpx;
  background: #f7f9fd;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.circle-post-point {
  display: flex;
  align-items: center;
  gap: 12rpx;
  color: #344054;
  font-size: 25rpx;
  line-height: 1.4;
  font-weight: 800;
}

.circle-post-point text:first-child {
  color: var(--gyt-primary, #3478f6);
  font-weight: 900;
}

.circle-post-action-row {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.circle-post-action-row button {
  min-height: 76rpx;
  margin: 0;
  padding: 0 16rpx;
  border-radius: 22rpx;
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24rpx;
  line-height: 1.2;
  font-weight: 900;
}

.home-header,
.brand-line,
.welcome-main {
  display: flex;
  align-items: center;
}

.home-header {
  --home-header-control-size: 72rpx;
  justify-content: space-between;
  gap: 18rpx;
  padding: 0 2rpx;
  align-items: center;
}

.brand-line {
  min-width: 0;
  flex: 1;
  align-items: center;
  gap: 0;
}

.home-header-copy {
  min-width: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.home-header-brand {
  min-width: 0;
  max-width: 100%;
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.home-header-logo {
  box-sizing: border-box;
  display: block;
  width: var(--home-header-control-size);
  height: var(--home-header-control-size);
  flex: 0 0 var(--home-header-control-size);
  border-radius: 18rpx;
  background: #ffffff;
  box-shadow: 0 8rpx 18rpx rgba(20, 31, 66, 0.08);
}

.home-header-title {
  color: #101828;
  min-width: 0;
  max-width: 100%;
  overflow: hidden;
  font-size: 32rpx;
  line-height: 1.2;
  font-weight: 900;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.home-header-status {
  max-width: 100%;
  margin-top: 14rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
  overflow: hidden;
}

.home-status-pill {
  min-width: 0;
  max-width: 100%;
  padding: 10rpx 16rpx;
  border: 1rpx solid rgba(52, 120, 246, 0.12);
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.74);
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  white-space: nowrap;
  box-shadow: 0 6rpx 16rpx rgba(20, 31, 66, 0.04);
}

.home-status-label {
  overflow: hidden;
  color: #667085;
  font-size: 20rpx;
  line-height: 1;
  font-weight: 700;
  text-overflow: ellipsis;
}

.home-status-value {
  color: var(--gyt-primary, #3478f6);
  font-size: 21rpx;
  line-height: 1;
  font-weight: 900;
}

.profile-entry {
  box-sizing: border-box;
  width: var(--home-header-control-size);
  height: var(--home-header-control-size);
  flex: 0 0 var(--home-header-control-size);
  border-radius: 50%;
  background: linear-gradient(180deg, var(--gyt-primary-tint, #f2f5fb), var(--gyt-primary-soft, #e3e9f4));
  color: var(--gyt-primary, #8b95a8);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  font-weight: 900;
  box-shadow: inset 0 -4rpx 8rpx rgba(20, 31, 66, 0.04);
}

.profile-entry-image {
  display: block;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.home-actions {
  display: flex;
  align-items: center;
  gap: 14rpx;
  flex-shrink: 0;
}

.message-bell {
  position: relative;
  box-sizing: border-box;
  width: var(--home-header-control-size);
  height: var(--home-header-control-size);
  flex: 0 0 var(--home-header-control-size);
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 999rpx;
  background: transparent;
  background-color: transparent !important;
  color: #344054;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
  line-height: 72rpx;
  box-shadow: none;
  -webkit-appearance: none;
  appearance: none;
  overflow: visible;
}

.message-bell::after {
  display: none;
}

.message-bell.unread {
  color: #f5b700;
}

.message-bell-icon-image {
  display: block;
  width: 34rpx;
  height: 34rpx;
  flex-shrink: 0;
  opacity: 0.82;
}

.message-bell.unread .message-bell-icon-image {
  opacity: 1;
}

.message-dot {
  position: absolute;
  right: 10rpx;
  top: 10rpx;
  width: 14rpx;
  height: 14rpx;
  border-radius: 999rpx;
  background: #ef4444;
  border: 3rpx solid #ffffff;
}

.welcome-card {
  border-radius: 34rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 2rpx solid #e8effc;
  box-shadow: 0 18rpx 48rpx rgba(25, 48, 89, 0.08);
}

.welcome-card {
  padding: 32rpx 26rpx 28rpx;
  overflow: hidden;
  position: relative;
  cursor: pointer;
  transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.welcome-card:active {
  transform: scale(0.992);
}

.welcome-main {
  position: relative;
  z-index: 1;
  gap: 18rpx;
}

.wave-icon {
  width: 70rpx;
  height: 70rpx;
  border-radius: 22rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.wave-icon svg {
  width: 46rpx;
  height: 46rpx;
  display: block;
}

.welcome-copy {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.welcome-title {
  color: #101828;
  font-size: 32rpx;
  line-height: 1.28;
  font-weight: 900;
}

.welcome-subtitle {
  color: #8a95a8;
  font-size: 24rpx;
  line-height: 1.5;
  font-weight: 600;
}

.hero-illustration {
  position: absolute;
  right: -12rpx;
  top: -8rpx;
  color: var(--gyt-primary-soft, rgba(22, 119, 255, 0.12));
  transform: rotate(-10deg);
  z-index: -1;
}

.hero-illustration svg {
  width: 112rpx;
  height: 126rpx;
  display: block;
}

.stats-card {
  position: relative;
  z-index: 1;
  margin-top: 26rpx;
  padding: 24rpx 8rpx;
  border-radius: 28rpx;
  background: #ffffff;
  display: flex;
  align-items: center;
  box-shadow: 0 16rpx 38rpx rgba(25, 48, 89, 0.08);
}

.stat-item {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-value {
  color: var(--gyt-primary, #1677ff);
  font-size: 40rpx;
  line-height: 1;
  font-weight: 900;
}

.stat-label {
  margin-top: 12rpx;
  color: #8a95a8;
  font-size: 25rpx;
  font-weight: 600;
}

.stat-divider {
  width: 2rpx;
  height: 70rpx;
  background: #e6edf8;
}

.module-grid {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.mock-exam-card {
  position: relative;
  box-sizing: border-box;
  min-height: 200rpx;
  margin-top: 18rpx;
  margin-bottom: 24rpx;
  padding: 20rpx 24rpx;
  border-radius: 28rpx;
  background:
    linear-gradient(135deg, rgba(255, 255, 255, 0.98), rgba(245, 248, 255, 0.96)),
    radial-gradient(circle at top right, var(--gyt-primary-shadow), transparent 45%);
  border: 2rpx solid var(--gyt-primary-border);
  box-shadow: 0 16rpx 34rpx rgba(20, 31, 66, 0.08);
}

.mock-exam-main {
  display: flex;
  align-items: center;
  gap: 18rpx;
  padding-right: 46rpx;
}

.mock-exam-icon {
  width: 96rpx;
  height: 96rpx;
  flex: 0 0 96rpx;
  border-radius: 28rpx;
  background: var(--gyt-primary-soft);
  display: flex;
  align-items: center;
  justify-content: center;
}

.mock-exam-icon-image {
  width: 78rpx;
  height: 78rpx;
  flex: 0 0 78rpx;
  display: block;
}

.mock-exam-copy {
  flex: 1;
  min-width: 0;
}

.mock-exam-title {
  color: #172033;
  font-size: 31rpx;
  font-weight: 900;
}

.mock-exam-sub {
  margin-top: 6rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.45;
}

.mock-exam-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 14rpx;
}

.mock-exam-meta text {
  padding: 6rpx 10rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-tint);
  color: var(--gyt-primary);
  font-size: 20rpx;
  font-weight: 800;
}

.mock-exam-arrow {
  position: absolute;
  right: 24rpx;
  top: 28rpx;
  color: var(--gyt-primary);
  font-size: 44rpx;
  font-weight: 700;
}

/* 手机浏览器可视区较短时，让刷题入口、三科练习和模拟测试同屏可见。 */
@media (max-width: 500px) and (max-height: 820px) {
  .practice-dashboard {
    gap: 14rpx;
  }

  .practice-dashboard .welcome-card {
    padding: 28rpx 26rpx 24rpx;
  }

  .practice-dashboard .stats-card {
    margin-top: 20rpx;
    padding-top: 20rpx;
    padding-bottom: 20rpx;
  }

  .practice-dashboard .module-grid {
    gap: 14rpx;
  }

  .practice-dashboard :deep(.module-card) {
    min-height: 200rpx;
    padding-top: 18rpx;
    padding-bottom: 18rpx;
  }

  .practice-dashboard .mock-exam-card {
    margin-top: 10rpx;
    margin-bottom: 22rpx;
  }
}

.state-box {
  margin-bottom: 18rpx;
  padding: 20rpx 22rpx;
  border-radius: 22rpx;
  background: var(--gyt-primary-tint);
  border: 2rpx dashed var(--gyt-primary-border);
  color: #36527f;
  font-size: 24rpx;
  line-height: 1.6;
}

.state-box.warning {
  background: #fff8eb;
  border-color: #fde7b0;
  color: #9a6510;
}

.state-box.mastered {
  background: #effcf4;
  border-color: #b7ebc6;
  color: #17663a;
}

.beta-grid,
.ability-list,
.wrong-detail,
.wrong-options,
.detail-actions,
.daily-list,
.pro-preview {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.beta-item {
  padding: 18rpx 20rpx;
  border-radius: 24rpx;
  background: var(--gyt-primary-tint);
  color: #344054;
  font-size: 24rpx;
  line-height: 1.7;
}

.beta-item.muted {
  background: var(--gyt-primary-tint);
  color: #667085;
}

.wrong-filter-card {
  margin: -2rpx 0 18rpx;
  padding: 14rpx;
  border: 2rpx solid rgba(221, 230, 246, 0.92);
  border-radius: 24rpx;
  background: rgba(247, 250, 255, 0.96);
}

.wrong-filter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.wrong-filter-select {
  display: block;
  min-width: 0;
}

.wrong-filter-select.is-submodule {
  grid-column: 1 / -1;
}

.wrong-filter-select-control {
  display: flex;
  align-items: center;
  gap: 8rpx;
  min-height: 64rpx;
  padding: 0 16rpx;
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  border-radius: 16rpx;
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.96);
}

.wrong-filter-select-name {
  flex: 0 0 auto;
  color: #69778c;
  font-size: 22rpx;
  line-height: 1.3;
  font-weight: 780;
}

.wrong-filter-select-value {
  min-width: 0;
  flex: 1;
  overflow: hidden;
  color: #253047;
  font-size: 21rpx;
  line-height: 1.3;
  font-weight: 760;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.wrong-filter-select-value.muted {
  color: #9aa5b6;
}

.wrong-filter-select-arrow-icon {
  width: 13rpx;
  height: 13rpx;
  flex: 0 0 auto;
  border-right: 3rpx solid var(--gyt-primary, #2563eb);
  border-bottom: 3rpx solid var(--gyt-primary, #2563eb);
  transform: translateY(-3rpx) rotate(45deg);
  box-sizing: border-box;
}

.wrong-filter-select.disabled .wrong-filter-select-control {
  border-color: #e5eaf3;
  background: rgba(245, 247, 251, 0.92);
}

.wrong-filter-select.disabled .wrong-filter-select-arrow-icon {
  border-color: #b2bac7;
}

.list-load-state {
  margin-top: 22rpx;
  padding: 18rpx 20rpx;
  border-radius: 24rpx;
  background: var(--gyt-primary-tint);
  color: #667085;
  text-align: center;
  font-size: 23rpx;
  line-height: 1.5;
}

.report-dashboard {
  width: 100%;
  max-width: 760rpx;
  margin: 0 auto;
  padding-bottom: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.report-empty-card,
.report-diagnosis-card,
.report-trend-card,
.weekly-breakthrough-card,
.today-training-card {
  box-sizing: border-box;
  border: 2rpx solid #e2ebfa;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.97);
  box-shadow: 0 16rpx 42rpx rgba(25, 48, 89, 0.08);
}

.report-empty-card {
  padding: 44rpx 30rpx;
  text-align: center;
}

.report-empty-icon,
.report-diagnosis-icon,
.today-training-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  color: var(--gyt-primary, #1677ff);
  background: var(--gyt-primary-soft, #eef5ff);
}

.report-empty-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 24rpx;
}

.report-empty-icon image {
  display: block;
  width: 42rpx;
  height: 42rpx;
}

.report-empty-title {
  margin-top: 18rpx;
  color: #101828;
  font-size: 29rpx;
  font-weight: 950;
}

.report-empty-copy {
  margin: 12rpx auto 0;
  max-width: 520rpx;
  color: #7b879a;
  font-size: 22rpx;
  line-height: 1.55;
  font-weight: 650;
}

.report-empty-action {
  min-width: 280rpx;
  min-height: 70rpx;
  margin-top: 24rpx;
  border: 0;
  border-radius: 20rpx;
  background: var(--gyt-primary, #1677ff);
  color: #fff;
  font-size: 24rpx;
  font-weight: 850;
  box-shadow: 0 12rpx 24rpx var(--gyt-primary-shadow, rgba(22, 119, 255, 0.18));
}

.report-empty-action::after,
.subject-report-action::after,
.advice-task-action::after {
  border: 0;
}

.report-diagnosis-card {
  padding: 27rpx 24rpx 23rpx;
  background:
    radial-gradient(circle at 90% 5%, var(--gyt-primary-shadow, rgba(22, 119, 255, 0.13)), transparent 30%),
    rgba(255, 255, 255, 0.97);
}

.report-card-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.report-card-title {
  color: #101828;
  font-size: 29rpx;
  line-height: 1.32;
  font-weight: 950;
}

.report-card-subtitle {
  margin-top: 7rpx;
  color: #8a95a8;
  font-size: 20rpx;
  line-height: 1.4;
  font-weight: 650;
}

.report-diagnosis-icon,
.today-training-icon {
  width: 52rpx;
  height: 52rpx;
  flex: 0 0 52rpx;
  border-radius: 17rpx;
  font-size: 28rpx;
  font-weight: 900;
}

.diagnosis-copy {
  margin-top: 20rpx;
  color: #40506b;
  font-size: 23rpx;
  line-height: 1.56;
  font-weight: 700;
}

.diagnosis-metrics {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 22rpx;
  padding: 18rpx 8rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.86);
  box-shadow: inset 0 0 0 2rpx rgba(228, 236, 248, 0.86);
}

.diagnosis-metric {
  min-width: 0;
  padding: 0 10rpx;
  border-right: 2rpx solid #e8eef7;
  text-align: center;
}

.diagnosis-metric:last-child {
  border-right: 0;
}

.diagnosis-metric-value {
  color: var(--gyt-primary, #1677ff);
  font-size: 27rpx;
  line-height: 1.16;
  font-weight: 950;
  white-space: nowrap;
}

.diagnosis-metric-value.green,
.breakthrough-score.green {
  color: #1b9c67;
}

.diagnosis-metric-value.orange,
.breakthrough-score.orange {
  color: #d88418;
}

.diagnosis-metric-value.red,
.breakthrough-score.red {
  color: #df5a5a;
}

.diagnosis-metric-value.up {
  color: #20a06a;
}

.diagnosis-metric-value.down {
  color: #df5a5a;
}

.diagnosis-metric-value.muted {
  color: #8b98ad;
}

.diagnosis-metric-label {
  margin-top: 8rpx;
  overflow: hidden;
  color: #8a95a8;
  font-size: 18rpx;
  line-height: 1.2;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.diagnosis-footnote {
  margin-top: 16rpx;
  color: #7c8aa0;
  font-size: 19rpx;
  line-height: 1.45;
  font-weight: 650;
}

.report-trend-card,
.weekly-breakthrough-card,
.today-training-card {
  padding: 25rpx 24rpx;
}

.trend-weekly-badge {
  padding: 8rpx 13rpx;
  border-radius: 999rpx;
  background: #eef5ff;
  color: var(--gyt-primary, #1677ff);
  font-size: 19rpx;
  line-height: 1.2;
  font-weight: 850;
  white-space: nowrap;
}

.trend-weekly-badge.up {
  background: #ecfaf3;
  color: #199664;
}

.trend-weekly-badge.down {
  background: #fff1f2;
  color: #dc5a63;
}

.trend-weekly-badge.muted {
  background: #f0f4fa;
  color: #8090a7;
}

.trend-chart-wrap {
  height: 188rpx;
  margin-top: 16rpx;
  padding: 8rpx 2rpx 0;
}

.trend-chart {
  display: block;
  width: 100%;
  height: 100%;
  overflow: visible;
}

.trend-grid-line {
  stroke: #e9eef7;
  stroke-width: 1.5;
}

.trend-area-path {
  fill: var(--gyt-primary-soft, #eef5ff);
  opacity: 0.78;
}

.trend-line-path {
  fill: none;
  stroke: var(--gyt-primary, #1677ff);
  stroke-width: 4;
  stroke-linecap: round;
  stroke-linejoin: round;
}

.trend-point {
  fill: #fff;
  stroke: var(--gyt-primary, #1677ff);
  stroke-width: 3;
}

.trend-axis-labels {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
  margin-top: 5rpx;
  color: #97a4b6;
  font-size: 18rpx;
  line-height: 1.2;
  font-weight: 650;
  text-align: center;
}

.trend-conclusion {
  margin-top: 18rpx;
  padding: 14rpx 16rpx;
  border-radius: 16rpx;
  background: #f0f5ff;
  color: var(--gyt-primary, #1677ff);
  font-size: 21rpx;
  line-height: 1.45;
  font-weight: 800;
}

.trend-conclusion.up {
  background: #edfaf3;
  color: #198f61;
}

.trend-conclusion.down {
  background: #fff2f3;
  color: #d2555f;
}

.trend-conclusion.muted {
  background: #f2f5f9;
  color: #728198;
}

.trend-unlock-state {
  margin-top: 20rpx;
  padding: 26rpx 20rpx;
  border: 2rpx dashed #d7e5fb;
  border-radius: 20rpx;
  background: #fafcff;
}

.trend-unlock-title {
  color: #4b5f7e;
  font-size: 23rpx;
  line-height: 1.5;
  font-weight: 850;
}

.trend-unlock-meta {
  margin-top: 12rpx;
  color: #8a99ad;
  font-size: 19rpx;
  font-weight: 700;
}

.trend-unlock-track {
  height: 9rpx;
  margin-top: 10rpx;
  overflow: hidden;
  border-radius: 999rpx;
  background: #e7edf7;
}

.trend-unlock-track view {
  height: 100%;
  border-radius: inherit;
  background: var(--gyt-primary-gradient, linear-gradient(90deg, #1677ff, #63a4ff));
}

.report-section-heading {
  padding: 2rpx 6rpx 0;
}

.report-section-title {
  color: #1e2b42;
  font-size: 29rpx;
  line-height: 1.25;
  font-weight: 950;
}

.report-section-subtitle {
  margin-top: 7rpx;
  color: #8a95a8;
  font-size: 20rpx;
  font-weight: 650;
}

.subject-report-card,
.learning-advice-card {
  border: 2rpx solid #e7eefb;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16rpx 42rpx rgba(25, 48, 89, 0.08);
}

.subject-report-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.subject-report-card {
  padding: 24rpx;
  display: flex;
  align-items: flex-start;
  gap: 22rpx;
}

.ring-wrap {
  width: 124rpx;
  height: 124rpx;
  flex: 0 0 124rpx;
  border-radius: 50%;
  border: 12rpx solid var(--gyt-primary, #1677ff);
  background: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 8rpx var(--gyt-primary-soft, #eef5ff);
}

.ring-wrap.orange {
  border-color: #f59e0b;
  box-shadow: inset 0 0 0 8rpx #fff7ed;
}

.ring-wrap.green {
  border-color: #27a778;
  box-shadow: inset 0 0 0 8rpx #ecfaf3;
}

.ring-wrap.red {
  border-color: #ef4444;
  box-shadow: inset 0 0 0 8rpx #fff1f2;
}

.ring-score {
  color: var(--gyt-primary, #1677ff);
  font-size: 30rpx;
  line-height: 1;
  font-weight: 950;
}

.ring-wrap.orange .ring-score {
  color: #f59e0b;
}

.ring-wrap.green .ring-score {
  color: #209768;
}

.ring-wrap.red .ring-score {
  color: #ef4444;
}

.ring-label {
  margin-top: 6rpx;
  color: #8a95a8;
  font-size: 18rpx;
  font-weight: 700;
}

.subject-report-main {
  flex: 1;
  min-width: 0;
}

.subject-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.subject-name {
  display: flex;
  align-items: center;
  gap: 12rpx;
  min-width: 0;
}

.subject-icon {
  width: 50rpx;
  height: 50rpx;
  flex: 0 0 50rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f4f7ff;
}

.report-diagnosis-icon image {
  display: block;
  width: 32rpx;
  height: 32rpx;
}

.subject-icon image {
  display: block;
  width: 34rpx;
  height: 34rpx;
}

.subject-title {
  flex: 1;
  min-width: 0;
  color: #101828;
  font-size: 28rpx;
  font-weight: 950;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.subject-status {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  color: var(--gyt-primary, #1677ff);
  background: var(--gyt-primary-soft, #eef5ff);
  font-size: 20rpx;
  font-weight: 900;
  white-space: nowrap;
}

.subject-status.orange {
  color: #d97706;
  background: #fff7ed;
}

.subject-status.green {
  color: #198f61;
  background: #ecfaf3;
}

.subject-status.red {
  color: #dc2626;
  background: #fff1f2;
}

.subject-count-label {
  margin-top: 12rpx;
  color: #8a95a8;
  font-size: 22rpx;
  font-weight: 700;
}

.subject-count {
  margin-top: 4rpx;
  color: #101828;
  font-size: 34rpx;
  font-weight: 950;
}

.subject-count text {
  margin-left: 6rpx;
  color: #667085;
  font-size: 22rpx;
  font-weight: 700;
}

.subject-count-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12rpx;
}

.subject-weekly-change {
  padding-bottom: 4rpx;
  color: #8a95a8;
  font-size: 18rpx;
  line-height: 1.3;
  font-weight: 750;
  white-space: nowrap;
}

.subject-weekly-change.up {
  color: #209768;
}

.subject-weekly-change.down {
  color: #dc5a63;
}

.subject-weekly-change.muted {
  color: #8b98aa;
}

.progress-track {
  margin-top: 16rpx;
  height: 8rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: #e8eef7;
}

.progress-fill {
  height: 100%;
  border-radius: inherit;
  background: var(--gyt-primary-gradient, linear-gradient(90deg, #1677ff, #63a4ff));
}

.progress-fill.orange {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.progress-fill.green {
  background: linear-gradient(90deg, #27a778, #5fc99b);
}

.progress-fill.red {
  background: linear-gradient(90deg, #ef4444, #fb7185);
}

.subject-weakness {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
  margin-top: 12rpx;
  color: #8a95a8;
  font-size: 19rpx;
  line-height: 1.35;
  font-weight: 700;
}

.subject-weakness text:last-child {
  min-width: 0;
  color: #58677f;
  font-weight: 850;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.subject-trend {
  margin-top: 8rpx;
  color: #667085;
  font-size: 20rpx;
  line-height: 1.45;
}

.subject-report-action,
.advice-task-action {
  width: auto;
  min-height: 42rpx;
  margin: 10rpx 0 0;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--gyt-primary, #1677ff);
  font-size: 20rpx;
  line-height: 1.35;
  font-weight: 900;
  text-align: left;
}

.subject-report-action::after,
.advice-task-action::after {
  border: 0;
}

.subject-report-action text,
.advice-task-action text {
  margin-left: 4rpx;
  font-size: 25rpx;
}

.weekly-breakthrough-card {
  padding-bottom: 14rpx;
}

.breakthrough-list {
  margin-top: 16rpx;
}

.breakthrough-item {
  display: flex;
  align-items: center;
  gap: 14rpx;
  padding: 16rpx 0;
  border-bottom: 2rpx solid #edf1f7;
}

.breakthrough-item:last-child {
  border-bottom: 0;
}

.breakthrough-rank {
  width: 40rpx;
  height: 40rpx;
  flex: 0 0 40rpx;
  border-radius: 14rpx;
  background: #eef5ff;
  color: var(--gyt-primary, #1677ff);
  text-align: center;
  font-size: 21rpx;
  line-height: 40rpx;
  font-weight: 900;
}

.breakthrough-main {
  min-width: 0;
  flex: 1;
}

.breakthrough-title {
  overflow: hidden;
  color: #35445c;
  font-size: 22rpx;
  line-height: 1.35;
  font-weight: 850;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.breakthrough-meta {
  margin-top: 5rpx;
  color: #96a1b1;
  font-size: 18rpx;
  line-height: 1.3;
  font-weight: 650;
}

.breakthrough-score {
  flex: 0 0 auto;
  color: var(--gyt-primary, #1677ff);
  font-size: 25rpx;
  line-height: 1;
  font-weight: 950;
}

.learning-advice-card {
  position: relative;
  overflow: hidden;
  padding: 26rpx 24rpx;
}

.learning-advice-card::after {
  content: "";
  position: absolute;
  right: -20rpx;
  bottom: -26rpx;
  width: 150rpx;
  height: 150rpx;
  border-radius: 38rpx;
  background: var(--gyt-primary-soft, linear-gradient(135deg, rgba(22, 119, 255, 0.12), rgba(22, 119, 255, 0.02)));
  transform: rotate(-10deg);
}

.advice-head {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.advice-title-wrap {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  min-width: 0;
}

.advice-icon {
  width: 48rpx;
  height: 48rpx;
  flex: 0 0 48rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #fff8d8;
}

.advice-icon image,
.today-training-icon image {
  display: block;
  width: 32rpx;
  height: 32rpx;
}

.advice-title {
  color: #101828;
  font-size: 28rpx;
  line-height: 1.3;
  font-weight: 950;
}

.advice-subtitle {
  margin-top: 8rpx;
  color: #8a95a8;
  font-size: 22rpx;
  line-height: 1.45;
}

.advice-list {
  position: relative;
  z-index: 1;
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.advice-task-list {
  position: relative;
  z-index: 1;
  margin-top: 18rpx;
  display: flex;
  flex-direction: column;
}

.advice-task-item {
  padding: 18rpx 0;
  border-bottom: 2rpx solid #edf1f7;
}

.advice-task-item:first-child {
  padding-top: 0;
}

.advice-task-item:last-child {
  padding-bottom: 0;
  border-bottom: 0;
}

.advice-task-index {
  color: var(--gyt-primary, #1677ff);
  font-size: 18rpx;
  line-height: 1.2;
  font-weight: 900;
}

.advice-task-title {
  margin-top: 8rpx;
  color: #24344e;
  font-size: 24rpx;
  line-height: 1.35;
  font-weight: 900;
}

.advice-task-meta {
  margin-top: 6rpx;
  color: #7f8da1;
  font-size: 19rpx;
  line-height: 1.3;
  font-weight: 700;
}

.advice-task-desc {
  margin-top: 8rpx;
  color: #64738b;
  font-size: 20rpx;
  line-height: 1.5;
  font-weight: 650;
}

.advice-item {
  display: flex;
  align-items: flex-start;
  gap: 10rpx;
  color: #475467;
  font-size: 23rpx;
  line-height: 1.55;
  font-weight: 700;
}

.advice-dot {
  width: 28rpx;
  height: 28rpx;
  flex: 0 0 28rpx;
  margin-top: 4rpx;
  border-radius: 50%;
  background: var(--gyt-primary, #1677ff);
  color: #ffffff;
  text-align: center;
  font-size: 18rpx;
  line-height: 28rpx;
  font-weight: 900;
}

.advice-loading {
  position: relative;
  z-index: 1;
  margin-top: 18rpx;
}

.advice-detail-btn {
  position: relative;
  z-index: 1;
  width: 100%;
  min-height: 72rpx;
  margin: 20rpx 0 0;
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  border-radius: 22rpx;
  background: var(--gyt-primary-tint, #f7fbff);
  color: var(--gyt-primary, #1677ff);
  font-size: 24rpx;
  line-height: 72rpx;
  font-weight: 900;
  box-shadow: none;
}

.report-action-btn {
  position: relative;
  z-index: 1;
  width: 100%;
  min-height: 82rpx;
  margin-top: 22rpx;
  border: 0;
  border-radius: 24rpx;
  background: var(--gyt-primary-gradient, linear-gradient(135deg, #1677ff, #4f86ff));
  color: #ffffff;
  font-size: 26rpx;
  font-weight: 900;
  box-shadow: 0 16rpx 28rpx var(--gyt-primary-shadow, rgba(22, 119, 255, 0.18));
}

.today-training-card {
  background:
    radial-gradient(circle at 90% 12%, var(--gyt-primary-shadow, rgba(22, 119, 255, 0.13)), transparent 31%),
    rgba(255, 255, 255, 0.97);
}

.today-training-list {
  display: flex;
  flex-wrap: wrap;
  gap: 9rpx;
  margin-top: 20rpx;
}

.today-training-list text {
  padding: 10rpx 13rpx;
  border-radius: 14rpx;
  background: var(--gyt-primary-soft, #eef5ff);
  color: #48628e;
  font-size: 20rpx;
  line-height: 1.3;
  font-weight: 800;
}

.training-sheet-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 80;
  display: flex;
  align-items: flex-end;
  background: rgba(15, 23, 42, 0.38);
}

/* “我的”页订阅入口：沿用白卡体系的 Plus 底部抽屉。 */
.subscription-sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 400;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  overflow: hidden;
  background: rgba(28, 29, 31, 0.38);
  backdrop-filter: blur(8rpx);
  -webkit-backdrop-filter: blur(8rpx);
  opacity: 0;
  transition: opacity 240ms ease;
  will-change: opacity;
}

.subscription-sheet {
  position: relative;
  width: 100%;
  max-height: calc(100dvh - env(safe-area-inset-top) - 20rpx);
  padding: 42rpx 48rpx calc(env(safe-area-inset-bottom) + 38rpx);
  border-radius: 56rpx 56rpx 0 0;
  background: rgba(255, 255, 255, 0.985);
  box-sizing: border-box;
  overflow-x: hidden;
  overflow-y: auto;
  overscroll-behavior: contain;
  box-shadow: 0 -18rpx 56rpx rgba(20, 22, 26, 0.16);
  -webkit-overflow-scrolling: touch;
  transform: translateY(105%);
  transition: transform 320ms cubic-bezier(0.22, 1, 0.36, 1);
  will-change: transform;
}

.subscription-sheet.is-dragging {
  transition: none;
}

.subscription-sheet-drag-handle {
  position: absolute;
  top: 4rpx;
  right: 0;
  left: 0;
  z-index: 2;
  height: 38rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  touch-action: none;
}

.subscription-sheet-drag-bar {
  width: 72rpx;
  height: 8rpx;
  border-radius: 999rpx;
  background: #d6d7da;
}

.subscription-sheet-mask.is-visible {
  opacity: 1;
}

.subscription-sheet-mask.is-visible .subscription-sheet {
  transform: translateY(0);
}

.subscription-sheet-head {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.subscription-sheet-close {
  width: 76rpx;
  min-width: 76rpx;
  height: 76rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #f4f4f3;
  color: #111214;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
}

.subscription-sheet-close::after {
  border: 0;
}

.subscription-sheet-close :deep(svg) {
  width: 38rpx;
  height: 38rpx;
}

.subscription-sheet-title {
  color: #111214;
  font-size: 42rpx;
  line-height: 1.2;
  font-weight: 900;
  letter-spacing: 0.02em;
}

.subscription-brand {
  margin: 46rpx auto 44rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.subscription-brand-logo {
  width: 190rpx;
  height: 190rpx;
  display: block;
  border-radius: 48rpx;
  transform: scale(1.32);
}

.subscription-brand-name {
  margin-top: 22rpx;
  color: #111214;
  font-size: 40rpx;
  line-height: 1.25;
  font-weight: 900;
  letter-spacing: 0.01em;
  text-align: center;
}

.subscription-benefit-card {
  padding: 34rpx 34rpx;
  border-radius: 38rpx;
  background: #f7f7f6;
  box-shadow: inset 0 1rpx 0 rgba(255, 255, 255, 0.8);
}

.subscription-benefit-row {
  min-height: 70rpx;
  display: flex;
  align-items: center;
  gap: 22rpx;
  color: #202124;
  font-size: 29rpx;
  line-height: 1.5;
  font-weight: 700;
}

.subscription-benefit-row + .subscription-benefit-row {
  margin-top: 18rpx;
}

.subscription-benefit-check {
  width: 34rpx;
  flex: 0 0 34rpx;
  color: #18a66a;
  font-family: var(--gyt-app-font);
  font-size: 46rpx;
  line-height: 1;
  font-weight: 400;
  text-align: center;
}

.subscription-status {
  margin: 30rpx 0 22rpx;
  color: #777774;
  font-size: 26rpx;
  line-height: 1.45;
  font-weight: 700;
  text-align: center;
}

.subscription-primary-button,
.subscription-secondary-button {
  width: 100%;
  min-height: 96rpx;
  margin: 0;
  padding: 0 28rpx;
  border: 0;
  box-sizing: border-box;
  font-size: 31rpx;
  font-weight: 900;
  line-height: 96rpx;
}

.subscription-primary-button {
  border-radius: 999rpx;
  background: #111214;
  color: #ffffff;
  box-shadow: 0 14rpx 26rpx rgba(17, 18, 20, 0.16);
}

.subscription-primary-button::after,
.subscription-secondary-button::after {
  border: 0;
}

.subscription-secondary-button {
  margin-top: 8rpx;
  background: transparent;
  color: #535350;
  font-size: 27rpx;
  font-weight: 700;
}

.subscription-copy {
  margin: 4rpx auto 0;
  max-width: 590rpx;
  color: #91918d;
  font-size: 22rpx;
  line-height: 1.65;
  font-weight: 600;
  text-align: center;
}

.subscription-terms {
  margin-top: 28rpx;
  color: #3f403e;
  font-size: 24rpx;
  line-height: 1.45;
  font-weight: 700;
  text-align: center;
}

.training-sheet {
  width: 100%;
  max-height: 88vh;
  padding: 16rpx 40rpx calc(env(safe-area-inset-bottom) + 28rpx);
  border-radius: 48rpx 48rpx 0 0;
  background: #ffffff;
  box-shadow: 0 -18rpx 52rpx rgba(15, 23, 42, 0.18);
  box-sizing: border-box;
  overflow: hidden;
}

.sheet-handle {
  width: 72rpx;
  height: 8rpx;
  margin: 0 auto 20rpx;
  border-radius: 999rpx;
  background: #d7deeb;
}

.sheet-head {
  text-align: center;
}

.sheet-title {
  color: #101828;
  font-size: 34rpx;
  line-height: 1.3;
  font-weight: 950;
}

.sheet-subtitle {
  margin-top: 10rpx;
  color: #8a95a8;
  font-size: 22rpx;
  line-height: 1.45;
  font-weight: 600;
}

.sheet-section {
  margin-top: 26rpx;
  padding: 24rpx;
  border: 2rpx solid #e8eef7;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 12rpx 30rpx rgba(25, 48, 89, 0.06);
}

.sheet-row,
.manual-count-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.sheet-section-title,
.manual-title {
  color: #172033;
  font-size: 26rpx;
  line-height: 1.35;
  font-weight: 950;
}

.sheet-section-sub {
  margin-top: 6rpx;
  color: #8a95a8;
  font-size: 21rpx;
  line-height: 1.45;
}

.smart-recommend-card,
.manual-settings {
  margin-top: 22rpx;
}

.recommend-lines {
  margin-top: 0;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.recommend-line {
  display: flex;
  align-items: flex-start;
  gap: 8rpx;
  color: #475467;
  font-size: 23rpx;
  line-height: 1.45;
  font-weight: 700;
}

.recommend-line text:first-child {
  flex: 0 0 118rpx;
  color: #667085;
}

.recommend-value {
  color: var(--gyt-primary, #3478f6);
  font-weight: 950;
}

.recommend-text {
  flex: 1;
  min-width: 0;
  color: #475467;
}

.manual-label {
  color: #475467;
  font-size: 23rpx;
  line-height: 1.4;
  font-weight: 800;
}

.manual-title + .manual-label {
  margin-top: 20rpx;
}

.difficulty-options {
  margin-top: 14rpx;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12rpx;
}

.difficulty-chip {
  min-width: 0;
  min-height: 58rpx;
  margin: 0;
  padding: 0 8rpx;
  border: 2rpx solid #e0e7f2;
  border-radius: 14rpx;
  background: #ffffff;
  color: #475467;
  font-size: 21rpx;
  line-height: 58rpx;
  font-weight: 800;
  box-shadow: none;
}

.difficulty-chip.active {
  border-color: var(--gyt-primary, #3478f6);
  background: var(--gyt-primary-soft, #eef5ff);
  color: var(--gyt-primary, #3478f6);
  box-shadow: 0 8rpx 20rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.12));
}

.manual-count-head {
  margin-top: 24rpx;
}

.manual-count-value {
  color: var(--gyt-primary, #3478f6);
  font-size: 24rpx;
  font-weight: 950;
}

.question-slider {
  margin: 14rpx 0 0;
}

.slider-scale {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 6rpx;
  color: #98a2b3;
  font-size: 19rpx;
  font-weight: 700;
}

.sheet-actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 18rpx;
  margin-top: 22rpx;
}

.sheet-cancel-btn,
.sheet-generate-btn {
  min-height: 84rpx;
  margin: 0;
  border: 0;
  border-radius: 18rpx;
  font-size: 27rpx;
  line-height: 84rpx;
  font-weight: 900;
}

.sheet-cancel-btn {
  background: #f6f8fb;
  color: #475467;
  border: 0;
}

.sheet-cancel-btn::after,
.sheet-generate-btn::after {
  border: 0;
}

.sheet-generate-btn {
  background: var(--gyt-primary-gradient, linear-gradient(135deg, #3478f6, #4f86ff));
  color: #ffffff;
  box-shadow: 0 16rpx 30rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.22));
}

.sheet-generate-btn[disabled] {
  opacity: 0.68;
  box-shadow: none;
}

.subject-setting {
  margin-bottom: 22rpx;
  padding-bottom: 22rpx;
  border-bottom: 2rpx solid #edf2f8;
}

.subject-options {
  margin-top: 14rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.subject-chip {
  min-width: 0;
  min-height: 60rpx;
  margin: 0;
  padding: 0 10rpx;
  border: 2rpx solid #e0e7f2;
  border-radius: 16rpx;
  background: #ffffff;
  color: #475467;
  font-size: 22rpx;
  line-height: 60rpx;
  font-weight: 850;
  box-shadow: none;
}

.subject-chip.active {
  border-color: var(--gyt-primary, #3478f6);
  background: var(--gyt-primary-soft, #eef5ff);
  color: var(--gyt-primary, #3478f6);
  box-shadow: 0 10rpx 24rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.12));
}

.generating-modal-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 95;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40rpx;
  background: rgba(15, 23, 42, 0.42);
  box-sizing: border-box;
}

.generating-modal-card {
  width: 100%;
  max-width: 640rpx;
  padding: 44rpx 36rpx 34rpx;
  border-radius: 32rpx;
  background: #ffffff;
  box-shadow: 0 24rpx 70rpx rgba(15, 23, 42, 0.2);
  text-align: center;
  box-sizing: border-box;
}

.generating-orbit {
  position: relative;
  width: 78rpx;
  height: 78rpx;
  margin: 0 auto 22rpx;
  border: 6rpx solid #e8f0ff;
  border-top-color: var(--gyt-primary, #3478f6);
  border-radius: 50%;
  animation: generating-spin 0.9s linear infinite;
}

.generating-dot {
  position: absolute;
  right: 2rpx;
  top: 6rpx;
  width: 14rpx;
  height: 14rpx;
  border-radius: 50%;
  background: var(--gyt-primary, #3478f6);
}

.generating-title {
  color: #101828;
  font-size: 32rpx;
  line-height: 1.35;
  font-weight: 950;
}

.generating-subtitle {
  margin-top: 12rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.55;
  font-weight: 700;
}

.generating-countdown {
  margin-top: 22rpx;
  color: var(--gyt-primary, #3478f6);
  font-size: 26rpx;
  line-height: 1.3;
  font-weight: 950;
}

.generating-progress {
  height: 12rpx;
  margin-top: 18rpx;
  border-radius: 999rpx;
  background: #edf2fb;
  overflow: hidden;
}

.generating-progress-bar {
  height: 100%;
  border-radius: inherit;
  background: var(--gyt-primary-gradient, linear-gradient(135deg, #3478f6, #75a2ff));
  transition: width 0.25s ease;
}

.generating-cancel-btn {
  min-height: 76rpx;
  margin: 28rpx 0 0;
  border: 0;
  border-radius: 18rpx;
  background: #f8fafc;
  color: #475467;
  font-size: 25rpx;
  line-height: 76rpx;
  font-weight: 900;
  box-shadow: none;
}

.generating-cancel-btn::after {
  border: 0;
}

@keyframes generating-spin {
  to {
    transform: rotate(360deg);
  }
}

.advice-detail-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 90;
  display: flex;
  align-items: flex-end;
  background: rgba(15, 23, 42, 0.38);
}

.advice-detail-sheet {
  position: relative;
  width: 100%;
  max-height: 88vh;
  padding: 16rpx 36rpx calc(env(safe-area-inset-bottom) + 28rpx);
  border-radius: 48rpx 48rpx 0 0;
  background: #ffffff;
  box-shadow: 0 -18rpx 54rpx rgba(15, 23, 42, 0.18);
  box-sizing: border-box;
  overflow: hidden;
}

.advice-detail-handle {
  width: 74rpx;
  height: 8rpx;
  margin: 0 auto 18rpx;
  border-radius: 999rpx;
  background: #d8deea;
}

.advice-detail-close {
  position: absolute;
  right: 26rpx;
  top: 22rpx;
  width: 58rpx;
  height: 58rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #f3f6fb;
  color: #98a2b3;
  font-size: 34rpx;
  line-height: 58rpx;
  font-weight: 900;
}

.advice-detail-head {
  padding: 0 64rpx 18rpx;
  text-align: center;
}

.advice-detail-title {
  color: #101828;
  font-size: 34rpx;
  line-height: 1.3;
  font-weight: 950;
}

.advice-detail-subtitle {
  margin-top: 10rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.5;
  font-weight: 700;
}

.advice-detail-scroll {
  max-height: 60vh;
}

.advice-subject-card {
  margin-bottom: 18rpx;
  padding: 24rpx;
  border: 2rpx solid rgba(229, 226, 224, .94);
  border-radius: 26rpx;
  background: rgba(255, 255, 255, .94);
}

.advice-subject-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16rpx;
}

.advice-subject-title {
  color: #101828;
  font-size: 28rpx;
  line-height: 1.3;
  font-weight: 950;
}

.advice-subject-meta {
  margin-top: 6rpx;
  color: #667085;
  font-size: 21rpx;
  font-weight: 700;
}

.advice-subject-badge {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-soft, #eef5ff);
  color: var(--gyt-primary, #1677ff);
  font-size: 20rpx;
  font-weight: 900;
  white-space: nowrap;
}

.detail-block {
  margin-top: 18rpx;
}

.detail-block-title {
  color: #1f2a44;
  font-size: 23rpx;
  line-height: 1.35;
  font-weight: 950;
}

.detail-line {
  position: relative;
  margin-top: 10rpx;
  padding-left: 22rpx;
  color: #52627a;
  font-size: 22rpx;
  line-height: 1.55;
  font-weight: 700;
}

.detail-line::before {
  content: "";
  position: absolute;
  left: 0;
  top: 15rpx;
  width: 8rpx;
  height: 8rpx;
  border-radius: 50%;
  background: var(--gyt-primary, #3478f6);
}

.detail-line.strong {
  color: #1f2a44;
}

.advice-detail-action {
  width: 100%;
  min-height: 82rpx;
  margin-top: 18rpx;
  border: 0;
  border-radius: 24rpx;
  background: var(--gyt-primary-gradient, linear-gradient(135deg, #1677ff, #4f86ff));
  color: #ffffff;
  font-size: 26rpx;
  line-height: 82rpx;
  font-weight: 900;
  box-shadow: 0 16rpx 28rpx var(--gyt-primary-shadow, rgba(22, 119, 255, 0.18));
}

.pro-modal-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 82;
  display: flex;
  align-items: flex-end;
  background: rgba(15, 23, 42, 0.36);
}

.pro-modal-sheet {
  position: relative;
  width: 100%;
  max-height: 88vh;
  padding: 16rpx 40rpx calc(env(safe-area-inset-bottom) + 30rpx);
  border-radius: 48rpx 48rpx 0 0;
  background: #ffffff;
  box-shadow: 0 -18rpx 54rpx rgba(15, 23, 42, 0.16);
  box-sizing: border-box;
  overflow: hidden;
}

.pro-modal-handle {
  width: 74rpx;
  height: 8rpx;
  margin: 0 auto 18rpx;
  border-radius: 999rpx;
  background: #d8deea;
}

.pro-modal-close {
  position: absolute;
  top: 20rpx;
  right: 28rpx;
  width: 58rpx;
  height: 58rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 50%;
  background: #f5f7fb;
  color: #8a95a8;
  font-size: 36rpx;
  line-height: 56rpx;
  font-weight: 800;
}

.pro-modal-head {
  padding: 0 58rpx;
  text-align: center;
}

.pro-modal-title {
  color: #101828;
  font-size: 36rpx;
  line-height: 1.25;
  font-weight: 950;
}

.pro-modal-subtitle {
  margin-top: 10rpx;
  color: #8a95a8;
  font-size: 23rpx;
  line-height: 1.45;
  font-weight: 650;
}

.pro-status-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-top: 12rpx;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
  background: #f6f8fc;
  color: #667085;
  font-size: 21rpx;
  line-height: 1.3;
  font-weight: 800;
}

.pro-benefit-list {
  margin-top: 26rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.pro-benefit-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  min-height: 92rpx;
  padding: 18rpx 22rpx;
  border: 2rpx solid #edf1f7;
  border-radius: 18rpx;
  background: #ffffff;
  box-shadow: 0 8rpx 24rpx rgba(25, 48, 89, 0.04);
}

.pro-benefit-icon {
  width: 72rpx;
  height: 72rpx;
  flex: 0 0 72rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 27rpx;
  line-height: 1;
  font-weight: 950;
}

.pro-benefit-icon.blue {
  color: var(--gyt-primary, #3478f6);
  background: var(--gyt-primary-soft, #eef5ff);
}

.pro-benefit-icon.green {
  color: #10b981;
  background: #edfdf6;
}

.pro-benefit-icon.purple {
  color: #7c3aed;
  background: #f2edff;
}

.pro-benefit-icon.orange {
  color: #f59e0b;
  background: #fff7e8;
}

.pro-benefit-copy {
  flex: 1;
  min-width: 0;
}

.pro-benefit-title {
  color: #172033;
  font-size: 26rpx;
  line-height: 1.35;
  font-weight: 950;
}

.pro-benefit-desc {
  margin-top: 6rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.45;
  font-weight: 650;
}

.pro-modal-actions {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 18rpx;
  margin-top: 24rpx;
}

.pro-later-btn,
.pro-open-btn {
  min-height: 84rpx;
  margin: 0;
  border: 0;
  border-radius: 18rpx;
  font-size: 27rpx;
  line-height: 84rpx;
  font-weight: 900;
}

.pro-later-btn {
  background: #f6f8fb;
  color: #475467;
  border: 0;
}

.pro-open-btn {
  background: var(--gyt-primary-gradient, linear-gradient(135deg, #3478f6, #4f86ff));
  color: #ffffff;
  box-shadow: 0 16rpx 30rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.22));
}

.pro-later-btn::after,
.pro-open-btn::after {
  border: 0;
}

.official-modal-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 58;
  display: flex;
  align-items: flex-end;
  padding: 28rpx 24rpx calc(env(safe-area-inset-bottom) + 28rpx);
  background: rgba(15, 23, 42, 0.38);
}

.official-modal-sheet {
  position: relative;
  width: 100%;
  max-height: 72vh;
  border-radius: 36rpx;
  background: #ffffff;
  overflow: hidden;
  box-shadow: 0 -18rpx 46rpx rgba(15, 23, 42, 0.18);
}

.official-modal-handle {
  width: 76rpx;
  height: 8rpx;
  margin: 18rpx auto 0;
  border-radius: 999rpx;
  background: #d8dee9;
}

.official-modal-close {
  position: absolute;
  right: 26rpx;
  top: 28rpx;
  width: 64rpx;
  height: 64rpx;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  color: #667085;
  font-size: 40rpx;
  line-height: 60rpx;
  font-weight: 900;
}

.official-modal-close::after {
  border: 0;
}

.official-modal-head {
  padding: 26rpx 108rpx 22rpx;
  border-bottom: 2rpx solid #eef2f8;
  text-align: center;
}

.official-modal-title {
  color: #101828;
  font-size: 36rpx;
  font-weight: 950;
  line-height: 1.3;
}

.official-modal-scroll {
  max-height: 48vh;
  padding: 24rpx 30rpx;
  box-sizing: border-box;
}

.official-empty {
  padding: 48rpx 0;
  color: #98a2b3;
  text-align: center;
  font-size: 26rpx;
}

.official-message-card {
  padding: 24rpx;
  border-radius: 24rpx;
  border: 2rpx solid #e6ebf5;
  background: #fbfcff;
}

.official-message-card + .official-message-card {
  margin-top: 18rpx;
}

.official-message-card.unread {
  border-color: var(--gyt-primary-border, #dbe7ff);
  background: var(--gyt-primary-tint, #f7fbff);
}

.official-message-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.official-message-title {
  color: #172033;
  font-size: 29rpx;
  font-weight: 950;
  line-height: 1.4;
}

.official-unread-badge {
  flex: 0 0 auto;
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  background: #ef4444;
  color: #ffffff;
  font-size: 18rpx;
  font-weight: 900;
}

.official-message-date {
  margin-top: 8rpx;
  color: #98a2b3;
  font-size: 21rpx;
  font-weight: 700;
}

.official-message-content {
  margin-top: 16rpx;
  color: #475467;
  font-size: 25rpx;
  line-height: 1.75;
  font-weight: 650;
  white-space: pre-wrap;
}

.official-done-btn {
  width: calc(100% - 60rpx);
  min-height: 82rpx;
  margin: 0 30rpx 28rpx;
  border: 0;
  border-radius: 24rpx;
  background: var(--gyt-primary, #1677ff);
  color: #ffffff;
  font-size: 28rpx;
  line-height: 82rpx;
  font-weight: 900;
}

.retest-entry-btn {
  flex: 0 0 auto;
  min-width: 150rpx;
  min-height: 64rpx;
  margin: 0;
  padding: 0 22rpx;
  border: 0;
  border-radius: 22rpx;
  background: var(--gyt-primary);
  color: #ffffff;
  font-size: 24rpx;
  line-height: 1.2;
  font-weight: 900;
  box-shadow: 0 14rpx 28rpx var(--gyt-primary-shadow);
  display: flex;
  align-items: center;
  justify-content: center;
}

.retest-entry-btn.ghost,
.retest-entry-btn:disabled {
  background: var(--gyt-primary-soft);
  color: #7a8aa6;
  box-shadow: none;
}

.wrong-stem {
  color: #172033;
  font-size: 30rpx;
  line-height: 1.7;
  font-weight: 800;
}

.wrong-meta,
.answer-line,
.explain-text {
  color: #475467;
  font-size: 24rpx;
  line-height: 1.7;
}

.wrong-option {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  min-height: 76rpx;
  padding: 18rpx;
  border: 2rpx solid #e6ebf5;
  border-radius: 22rpx;
  background: #ffffff;
  color: #172033;
  text-align: left;
  font-size: 24rpx;
}

.wrong-option.selected {
  border-color: var(--gyt-primary);
  background: var(--gyt-primary-soft);
}

.wrong-option.correct {
  border-color: rgba(22, 163, 74, 0.45);
  background: rgba(22, 163, 74, 0.1);
}

.wrong-option.wrong {
  border-color: rgba(239, 68, 68, 0.45);
  background: rgba(239, 68, 68, 0.1);
}

.option-key {
  width: 42rpx;
  height: 42rpx;
  border-radius: 14rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
}

.task-btn.ghost {
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  border: 0;
}

.wrong-modal-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 50;
  display: flex;
  align-items: flex-end;
  padding: 22rpx 24rpx calc(env(safe-area-inset-bottom) + 22rpx);
  background: rgba(15, 23, 42, 0.46);
}

.wrong-modal-panel {
  width: 100%;
  max-height: 82vh;
  border-radius: 34rpx;
  background: #ffffff;
  box-shadow: 0 -20rpx 54rpx rgba(15, 23, 42, 0.22);
  overflow: hidden;
}

.wrong-modal-grabber {
  width: 72rpx;
  height: 8rpx;
  margin: 18rpx auto 0;
  border-radius: 999rpx;
  background: #d8dee9;
}

.wrong-modal-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 20rpx 34rpx 22rpx;
  border-bottom: 2rpx solid #eef2f8;
}

.wrong-modal-heading {
  flex: 1;
  min-width: 0;
}

.wrong-modal-title {
  color: #101828;
  font-size: 32rpx;
  line-height: 1.3;
  font-weight: 950;
}

.wrong-modal-sub {
  display: inline-flex;
  margin-top: 10rpx;
  padding: 7rpx 14rpx;
  border-radius: 999rpx;
  background: #f4f7fb;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.35;
  font-weight: 800;
}

.wrong-modal-close {
  width: 54rpx;
  height: 54rpx;
  margin: 0 0 0 auto;
  flex: 0 0 54rpx;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  color: #667085;
  font-size: 32rpx;
  line-height: 50rpx;
  font-weight: 900;
}

.wrong-modal-close::after {
  border: 0;
}

.wrong-modal-scroll {
  max-height: 66vh;
  padding: 24rpx 34rpx 26rpx;
  box-sizing: border-box;
}

.wrong-modal-panel .wrong-detail {
  gap: 18rpx;
}

.wrong-section-label {
  color: #667085;
  font-size: 21rpx;
  line-height: 1.2;
  font-weight: 900;
  margin-bottom: -6rpx;
}

.wrong-modal-panel .wrong-stem {
  padding: 22rpx 24rpx;
  border: 2rpx solid #edf1f7;
  border-radius: 24rpx;
  background: #f8fafd;
  font-size: 29rpx;
  line-height: 1.56;
  text-align: left;
  box-shadow: inset 0 0 0 1rpx rgba(255, 255, 255, 0.65);
}

.wrong-modal-panel .wrong-options {
  gap: 14rpx;
  width: 100%;
}

.wrong-modal-panel .wrong-option {
  width: 100%;
  min-height: 78rpx;
  margin: 0;
  padding: 16rpx 18rpx;
  border-radius: 20rpx;
  align-items: center;
  box-sizing: border-box;
  box-shadow: none;
}

.wrong-modal-panel .option-key {
  width: 42rpx;
  height: 42rpx;
  flex: 0 0 42rpx;
  border-radius: 14rpx;
  font-size: 23rpx;
}

.retest-detail {
  gap: 24rpx;
}

.retest-detail .wrong-stem {
  padding: 18rpx 2rpx 8rpx;
  font-size: 32rpx;
  line-height: 1.65;
}

.retest-detail .wrong-options {
  width: 100%;
  gap: 18rpx;
}

.retest-detail .wrong-option {
  width: 100%;
  min-height: 98rpx;
  margin: 0;
  padding: 22rpx 24rpx;
  border-radius: 28rpx;
  box-sizing: border-box;
  background: #ffffff;
  box-shadow: 0 10rpx 24rpx rgba(20, 31, 66, 0.05);
}

.retest-detail .option-key {
  width: 52rpx;
  height: 52rpx;
  flex: 0 0 52rpx;
  border-radius: 18rpx;
  font-size: 26rpx;
}

.retest-detail .detail-actions {
  margin-top: 6rpx;
}

.option-text {
  flex: 1;
  min-width: 0;
  color: #263247;
  font-size: 28rpx;
  line-height: 1.55;
  font-weight: 700;
}

.wrong-modal-panel .option-text {
  font-size: 26rpx;
  line-height: 1.45;
}

.review-hint {
  padding: 14rpx 18rpx;
  border-radius: 20rpx;
  background: #f8fafc;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.6;
}

.wrong-modal-panel .review-hint {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 8rpx 16rpx;
}

.review-hint-main {
  color: #475467;
  font-weight: 800;
}

.review-hint-sub {
  color: #98a2b3;
  text-align: right;
  font-weight: 700;
}

.modal-submit-btn {
  width: 100%;
  min-height: 82rpx;
  margin: 0;
  border: 0;
  border-radius: 22rpx;
  background: linear-gradient(135deg, var(--gyt-primary), var(--gyt-primary));
  color: #ffffff;
  font-size: 26rpx;
  line-height: 82rpx;
  font-weight: 900;
  box-shadow: 0 16rpx 30rpx var(--gyt-primary-shadow);
}

.modal-submit-btn:disabled,
.modal-submit-btn[disabled] {
  background: #e8edf7;
  color: #98a2b3;
  box-shadow: none;
  opacity: 1;
}

.modal-submit-btn.done {
  background: #111827;
  box-shadow: 0 16rpx 30rpx rgba(17, 24, 39, 0.18);
}

.retest-summary-card {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.summary-score {
  color: var(--gyt-primary);
  font-size: 58rpx;
  line-height: 1;
  font-weight: 950;
  text-align: center;
}

.summary-copy {
  color: #475467;
  font-size: 26rpx;
  line-height: 1.7;
  text-align: center;
}

.answer-map {
  display: flex;
  flex-wrap: wrap;
  gap: 14rpx;
  justify-content: center;
}

.answer-dot {
  width: 58rpx;
  height: 58rpx;
  border: 0;
  border-radius: 18rpx;
  color: #ffffff;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 58rpx;
}

.answer-dot.correct {
  background: #16a34a;
}

.answer-dot.wrong {
  background: #ef4444;
}

.daily-card {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
  padding: 22rpx;
  border-radius: 26rpx;
  border: 2rpx solid #e6ebf5;
  background: #fbfcff;
}

.daily-title {
  color: #172033;
  font-size: 26rpx;
  font-weight: 900;
  line-height: 1.5;
}

.daily-desc {
  margin-top: 8rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.6;
}

.pro-preview-item {
  padding: 18rpx 20rpx;
  border-radius: 22rpx;
  background: var(--gyt-primary-tint);
  color: #36527f;
  font-size: 24rpx;
  line-height: 1.6;
}

.pro-btn,
.feedback-btn {
  margin-top: 18rpx;
}

.pro-entry {
  background: linear-gradient(135deg, #111827, #334155);
}

.ability-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
  padding: 18rpx 0;
  border-bottom: 2rpx dashed #edf1f7;
}

.ability-row:last-child {
  border-bottom: 0;
}

.ability-title {
  color: #172033;
  font-size: 25rpx;
  font-weight: 800;
}

.ability-sub {
  margin-top: 8rpx;
  color: #667085;
  font-size: 22rpx;
}

.ability-pill {
  padding: 12rpx 16rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 22rpx;
  font-weight: 800;
  white-space: nowrap;
}

.ability-pill.stable {
  background: #effcf4;
  color: #17663a;
}

.ability-pill.normal {
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
}

.ability-pill.weak {
  background: #fff8eb;
  color: #9a6510;
}

.ability-pill.critical {
  background: #fff1f2;
  color: #b42318;
}

.diagnosis-card {
  margin-top: 20rpx;
  padding: 28rpx;
  border-radius: 34rpx;
  background: rgba(255, 255, 255, .94);
  border: 2rpx solid rgba(229, 226, 224, .94);
}

.diagnosis-title {
  font-size: 30rpx;
  font-weight: 800;
  color: #172033;
}

.diagnosis-text {
  margin-top: 14rpx;
  color: #384a6b;
  font-size: 25rpx;
  line-height: 1.8;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.task-item {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 18rpx;
  padding: 10rpx 0;
  border-bottom: 2rpx dashed #edf1f7;
}

.task-item:last-child {
  border-bottom: 0;
  padding-bottom: 0;
}

.task-copy {
  flex: 1;
}

.task-title {
  font-size: 26rpx;
  line-height: 1.6;
  font-weight: 800;
  color: #172033;
}

.task-desc {
  margin-top: 10rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.6;
}

.task-btn {
  padding: 18rpx 22rpx;
  border: 0;
  border-radius: 22rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 24rpx;
  font-weight: 800;
}

.task-btn::after {
  border: 0;
}

.unlock-btn {
  margin-top: 22rpx;
  width: 100%;
  min-height: 94rpx;
  border: 0;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #111827, #334155);
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 800;
  box-shadow: 0 16rpx 30rpx rgba(17, 24, 39, 0.22);
}

.profile-dashboard {
  width: 100%;
  max-width: 760rpx;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  overflow-x: hidden;
}

.account-card,
.member-card,
.profile-section-card,
.logout-card {
  background: rgba(255, 255, 255, 0.96);
  border: 2rpx solid #e8effc;
  border-radius: 30rpx;
  box-shadow: 0 16rpx 42rpx rgba(25, 48, 89, 0.08);
}

.account-card {
  padding: 26rpx 24rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.account-card.guest {
  align-items: flex-start;
  background: var(
    --gyt-panel-bg,
    radial-gradient(circle at 94% 20%, var(--gyt-primary-shadow), transparent 30%),
    linear-gradient(135deg, #ffffff 0%, var(--gyt-primary-tint) 100%)
  );
}

.account-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-gradient, linear-gradient(135deg, #4f7dff, #87aaff));
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 36rpx;
  font-weight: 900;
  box-shadow: 0 14rpx 26rpx var(--gyt-primary-shadow, rgba(37, 99, 235, 0.22));
}

.account-avatar-image {
  display: block;
  object-fit: cover;
  background: #ffffff;
}

.account-main {
  flex: 1;
  min-width: 0;
}

.account-name-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.account-name {
  color: #101828;
  font-size: 34rpx;
  line-height: 1.2;
  font-weight: 900;
}

.account-badge {
  padding: 6rpx 12rpx;
  border-radius: 14rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #1677ff);
  font-size: 21rpx;
  font-weight: 900;
}

.account-desc {
  margin-top: 10rpx;
  color: #8a95a8;
  font-size: 23rpx;
  line-height: 1.4;
  font-weight: 600;
}

.exam-switch {
  margin-top: 16rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.exam-pill {
  min-width: 100rpx;
  min-height: 54rpx;
  margin: 0;
  padding: 0 18rpx;
  border: 2rpx solid var(--gyt-primary-border, #dbe7ff);
  border-radius: 18rpx;
  background: #ffffff;
  color: var(--gyt-primary, #1677ff);
  font-size: 23rpx;
  font-weight: 900;
  line-height: 54rpx;
}

.exam-pill.active {
  color: #ffffff;
  border-color: var(--gyt-primary, #1677ff);
  background: var(--gyt-primary, #1677ff);
  box-shadow: 0 8rpx 18rpx var(--gyt-primary-shadow, rgba(22, 119, 255, 0.18));
}

.account-login-btn {
  width: 210rpx;
  min-height: 72rpx;
  margin: 18rpx 0 0;
  border: 0;
  border-radius: 18rpx;
  background: var(--gyt-primary, #1677ff);
  color: #ffffff;
  font-size: 26rpx;
  line-height: 72rpx;
  font-weight: 900;
  box-shadow: 0 12rpx 26rpx var(--gyt-primary-shadow, rgba(22, 119, 255, 0.18));
}

.account-arrow,
.menu-arrow {
  color: #98a2b3;
  font-size: 42rpx;
  font-weight: 800;
}

.member-card {
  position: relative;
  overflow: hidden;
  padding: 30rpx 24rpx 24rpx;
  background: var(
    --gyt-panel-bg,
    radial-gradient(circle at 82% 26%, var(--gyt-primary-shadow), transparent 28%),
    linear-gradient(135deg, #ffffff 0%, var(--gyt-primary-soft) 100%)
  );
}

.member-card.active {
  background:
    radial-gradient(circle at 82% 26%, rgba(16, 185, 129, 0.16), transparent 28%),
    linear-gradient(135deg, #ffffff 0%, #ecfdf5 100%);
}

.member-copy {
  position: relative;
  z-index: 1;
  max-width: 430rpx;
}

.member-kicker {
  display: inline-flex;
  margin-bottom: 12rpx;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-soft, rgba(22, 119, 255, 0.1));
  color: var(--gyt-primary, #1677ff);
  font-size: 21rpx;
  line-height: 1.2;
  font-weight: 900;
}

.member-card.active .member-kicker {
  background: rgba(16, 185, 129, 0.12);
  color: #059669;
}

.member-title {
  color: #101828;
  font-size: 34rpx;
  font-weight: 900;
  line-height: 1.35;
}

.member-subtitle {
  margin-top: 10rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.5;
  font-weight: 600;
}

.member-login-btn {
  margin: 24rpx 0 0;
  width: 210rpx;
  min-height: 72rpx;
  border: 0;
  border-radius: 18rpx;
  background: var(--gyt-primary, #1677ff);
  color: #ffffff;
  font-size: 26rpx;
  font-weight: 900;
  line-height: 72rpx;
}

.shield-art {
  position: absolute;
  right: 40rpx;
  top: 28rpx;
  width: 150rpx;
  height: 150rpx;
  border-radius: 42rpx;
  background: var(--gyt-primary-gradient, linear-gradient(145deg, #72a5ff, #1677ff));
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 82rpx;
  font-weight: 900;
  transform: rotate(-8deg);
  box-shadow: 0 18rpx 36rpx var(--gyt-primary-shadow, rgba(22, 119, 255, 0.28));
  opacity: 0.92;
}

.shield-art.active {
  background: linear-gradient(145deg, #34d399, #10b981);
  font-size: 42rpx;
  letter-spacing: 0;
  transform: rotate(-6deg);
  box-shadow: 0 18rpx 36rpx rgba(16, 185, 129, 0.24);
}

.benefit-row {
  position: relative;
  z-index: 1;
  margin-top: 28rpx;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12rpx;
}

.benefit-item {
  min-width: 0;
  text-align: center;
  cursor: default;
}

.benefit-icon {
  position: relative;
  width: 54rpx;
  height: 54rpx;
  margin: 0 auto 10rpx;
  border-radius: 18rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #1677ff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 900;
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  box-shadow: 0 8rpx 20rpx var(--gyt-primary-shadow, rgba(22, 119, 255, 0.12));
  box-sizing: border-box;
}

.benefit-icon-img {
  width: 32rpx;
  height: 32rpx;
  display: block;
}

.benefit-icon.book-icon,
.benefit-icon.report-icon,
.menu-icon.book-icon,
.menu-icon.report-icon {
  font-size: 0;
}

.benefit-icon.book-icon::before,
.menu-icon.book-icon::before {
  content: '';
  position: absolute;
  width: 25rpx;
  height: 31rpx;
  border: 4rpx solid currentColor;
  border-radius: 6rpx 10rpx 10rpx 6rpx;
  background: rgba(255, 255, 255, 0.62);
  box-sizing: border-box;
  transform: translateX(2rpx);
}

.benefit-icon.book-icon::after,
.menu-icon.book-icon::after {
  content: '';
  position: absolute;
  width: 12rpx;
  height: 3rpx;
  border-radius: 999rpx;
  background: currentColor;
  opacity: 0.48;
  transform: translate(4rpx, -8rpx);
  box-shadow: 0 8rpx 0 currentColor, 0 16rpx 0 currentColor;
}

.benefit-icon.report-icon::before,
.menu-icon.report-icon::before {
  content: '';
  position: absolute;
  left: 16rpx;
  bottom: 15rpx;
  width: 5rpx;
  height: 18rpx;
  border-radius: 999rpx;
  background: currentColor;
  box-shadow: 11rpx -7rpx 0 currentColor, 22rpx -14rpx 0 currentColor;
}

.benefit-icon.report-icon::after,
.menu-icon.report-icon::after {
  content: '';
  position: absolute;
  left: 14rpx;
  bottom: 13rpx;
  width: 31rpx;
  height: 28rpx;
  border-left: 3rpx solid currentColor;
  border-bottom: 3rpx solid currentColor;
  border-radius: 0 0 0 5rpx;
  opacity: 0.34;
  box-sizing: border-box;
}

.benefit-label {
  color: #344054;
  font-size: 20rpx;
  line-height: 1.25;
  font-weight: 700;
}

.profile-section-card {
  padding: 28rpx 24rpx 8rpx;
}

.profile-section-title {
  margin-bottom: 8rpx;
  color: #101828;
  font-size: 29rpx;
  font-weight: 900;
}

.menu-list {
  display: flex;
  flex-direction: column;
}

.menu-row {
  display: flex;
  align-items: center;
  gap: 18rpx;
  min-height: 96rpx;
  padding: 18rpx 0;
  border-bottom: 2rpx solid #edf2fb;
}

.menu-row:last-child {
  border-bottom: 0;
}

.menu-row.locked {
  opacity: 0.74;
}

.menu-icon {
  position: relative;
  width: 58rpx;
  height: 58rpx;
  border-radius: 18rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #1677ff);
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 28rpx;
  font-weight: 900;
  box-sizing: border-box;
}

.menu-unread-dot {
  position: absolute;
  top: -6rpx;
  right: -6rpx;
  z-index: 2;
  width: 16rpx;
  height: 16rpx;
  border: 3rpx solid #ffffff;
  border-radius: 50%;
  background: #f05d5d;
  box-shadow: 0 3rpx 8rpx rgba(240, 93, 93, 0.34);
  box-sizing: border-box;
}

.menu-icon-img {
  width: 34rpx;
  height: 34rpx;
  display: block;
}

.menu-icon.green {
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #1677ff);
}

.menu-icon.purple {
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #1677ff);
}

.menu-icon.orange {
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #1677ff);
}

.menu-icon.dark {
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #1677ff);
}

.menu-icon.locked {
  background: var(--gyt-primary-tint, #f4f8ff);
  color: var(--gyt-primary, #1677ff);
  opacity: 0.58;
}

.menu-copy {
  display: flex;
  align-items: center;
  flex: 1;
  min-width: 0;
  min-height: 58rpx;
}

.menu-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.menu-title {
  color: #101828;
  font-size: 30rpx;
  line-height: 1.35;
  font-weight: 900;
}

.pro-lock-badge {
  padding: 5rpx 12rpx;
  border-radius: 999rpx;
  background: #f2f4f7;
  color: #98a2b3;
  font-size: 18rpx;
  line-height: 1.2;
  font-weight: 900;
}

.logout-card {
  min-height: 84rpx;
  color: #ef4444;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 27rpx;
  font-weight: 900;
}

.home-page.profile-reference-page {
  padding-right: 34rpx;
  padding-left: 34rpx;
  background: #f5f3f7;
  color: #202633;
}

.home-page.profile-reference-page::before {
  background: #f5f3f7;
  filter: none;
  transform: none;
}

.profile-reference-page .profile-dashboard {
  position: relative;
  z-index: 1;
  max-width: 680rpx;
  gap: 0;
  overflow: visible;
}

.profile-avatar-button::after,
.profile-exam-selector::after,
.profile-exam-option::after,
.profile-exam-modal-cancel::after {
  border: 0;
}

.profile-identity {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.profile-avatar-button {
  position: relative;
  width: 222rpx;
  height: 222rpx;
  margin: 4rpx 0 0;
  padding: 0;
  border: 0;
  border-radius: 999rpx;
  background: transparent;
  overflow: visible;
}

.profile-reference-avatar {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  border: 10rpx solid rgba(255, 255, 255, 0.94);
  border-radius: 999rpx;
  background: linear-gradient(145deg, #ded9d4, #cfc8bd);
  color: #786f65;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 64rpx;
  line-height: 1;
  font-weight: var(--gyt-font-weight-bold, 700);
  box-shadow: 0 18rpx 44rpx rgba(57, 50, 66, 0.08);
}

.profile-reference-avatar-image {
  display: block;
  object-fit: cover;
}

.profile-avatar-edit {
  position: absolute;
  right: 4rpx;
  bottom: 12rpx;
  min-width: 60rpx;
  height: 42rpx;
  padding: 0 12rpx;
  border: 4rpx solid #f5f3f7;
  border-radius: 999rpx;
  background: #ffffff;
  color: #6f6a74;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18rpx;
  line-height: 1;
  font-weight: var(--gyt-font-weight-semibold, 600);
  box-shadow: 0 8rpx 18rpx rgba(38, 33, 45, 0.1);
}

.profile-reference-name {
  max-width: 90%;
  margin-top: 22rpx;
  overflow: hidden;
  color: #2b292d;
  font-family: var(--gyt-app-font);
  font-size: 42rpx;
  line-height: 1.25;
  font-weight: var(--gyt-font-weight-bold, 700);
  white-space: nowrap;
  text-overflow: ellipsis;
}

.profile-exam-selector {
  min-width: 224rpx;
  min-height: 70rpx;
  margin: 24rpx 0 0;
  padding: 0 24rpx;
  border: 0;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.96);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
  color: #73707a;
  box-shadow: 0 12rpx 30rpx rgba(58, 51, 66, 0.05);
}

.profile-exam-mark {
  width: 48rpx;
  height: 36rpx;
  border-radius: 12rpx;
  background: linear-gradient(135deg, #5c6df2, #9b54e8);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17rpx;
  line-height: 1;
  font-weight: var(--gyt-font-weight-bold, 700);
}

.profile-exam-code {
  font-size: 26rpx;
  line-height: 1;
  font-weight: var(--gyt-font-weight-semibold, 600);
  letter-spacing: 0.5rpx;
}

.profile-exam-arrow {
  margin-top: -5rpx;
  color: #bbb7bf;
  font-size: 28rpx;
  line-height: 1;
  font-weight: var(--gyt-font-weight-semibold, 600);
}

.profile-reference-divider {
  height: 2rpx;
  margin: 18rpx 82rpx;
  background: rgba(69, 61, 77, 0.09);
}

.profile-group + .profile-group {
  margin-top: 30rpx;
}

.profile-group-title {
  margin: 0 20rpx 14rpx;
  color: #9b98a0;
  font-size: 27rpx;
  line-height: 1.3;
  font-weight: var(--gyt-font-weight-semibold, 600);
}

.profile-reference-page .profile-reference-card {
  padding: 6rpx 28rpx;
  border: 0;
  border-radius: 36rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14rpx 36rpx rgba(56, 49, 64, 0.04);
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.profile-reference-page .menu-row {
  min-height: 92rpx;
  padding: 15rpx 0;
  gap: 16rpx;
  border-bottom: 2rpx solid rgba(42, 38, 48, 0.055);
}

.profile-reference-page .menu-icon {
  width: 48rpx;
  height: 48rpx;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: #282329;
  box-shadow: none;
  font-size: 26rpx;
}

.profile-reference-page .menu-icon.green,
.profile-reference-page .menu-icon.purple,
.profile-reference-page .menu-icon.orange,
.profile-reference-page .menu-icon.dark,
.profile-reference-page .menu-icon.locked {
  border: 0;
  background: transparent;
  color: #282329;
}

.profile-reference-page .menu-icon-img {
  width: 31rpx;
  height: 31rpx;
}

.profile-reference-page .menu-copy {
  min-height: 48rpx;
}

.profile-reference-page .menu-title {
  color: #243343;
  font-size: 27rpx;
  line-height: 1.35;
  font-weight: var(--gyt-font-weight-semibold, 600);
}

.menu-row-value {
  max-width: 180rpx;
  overflow: hidden;
  color: #b5b1b8;
  font-size: 23rpx;
  line-height: 1.2;
  font-weight: var(--gyt-font-weight-medium, 500);
  white-space: nowrap;
  text-overflow: ellipsis;
}

.profile-reference-page .menu-arrow {
  color: #d0cdd2;
  font-size: 36rpx;
  line-height: 1;
  font-weight: 600;
}

.profile-reference-page .logout-card {
  min-height: 92rpx;
  margin: 32rpx 0 14rpx;
  border: 2rpx solid #dc2626;
  border-radius: 30rpx;
  background: linear-gradient(135deg, #f25555 0%, #e53935 100%);
  color: #ffffff;
  box-shadow: 0 14rpx 30rpx rgba(220, 38, 38, 0.22);
  font-size: 28rpx;
  font-weight: var(--gyt-font-weight-semibold, 600);
  letter-spacing: 2rpx;
  transition: transform 140ms ease, opacity 140ms ease;
}

.profile-reference-page .logout-card--pressed {
  opacity: 0.88;
  transform: scale(0.985);
}

/* “我的”页与全 App 共用同一套系统无衬线字体。 */
.profile-reference-page {
  --profile-display-font: var(--gyt-app-font);
  font-family: var(--profile-display-font);
}

.profile-reference-page,
.profile-reference-page * {
  font-family: var(--profile-display-font);
}

.profile-reference-page .profile-reference-name {
  font-family: var(--profile-display-font);
  font-size: 46rpx;
  font-weight: var(--gyt-font-weight-bold, 700);
}

.profile-reference-page .profile-exam-selector {
  min-height: 74rpx;
  margin-top: 8rpx;
  padding-right: 26rpx;
  padding-left: 26rpx;
}

.profile-reference-page .profile-exam-mark {
  width: 54rpx;
  height: 40rpx;
  font-size: 18rpx;
}

.profile-reference-page .profile-exam-code {
  font-size: 30rpx;
  font-weight: var(--gyt-font-weight-semibold, 600);
}

.profile-reference-page .profile-group-title {
  margin-bottom: 8rpx;
  font-size: 31rpx;
  font-weight: var(--gyt-font-weight-semibold, 600);
}

.profile-reference-page .profile-reference-card {
  padding-right: 30rpx;
  padding-left: 30rpx;
  border-radius: 38rpx;
}

.profile-reference-page .menu-row {
  min-height: 120rpx;
  padding-top: 18rpx;
  padding-bottom: 18rpx;
  gap: 18rpx;
}

.profile-reference-page .menu-icon {
  width: 56rpx;
  height: 56rpx;
  flex: 0 0 56rpx;
  font-size: 30rpx;
}

.profile-reference-page .menu-icon-img {
  width: 38rpx;
  height: 38rpx;
}

.profile-reference-page .menu-copy {
  min-height: 56rpx;
}

.profile-reference-page .menu-title-row {
  gap: 14rpx;
}

.profile-reference-page .menu-title {
  font-family: var(--profile-display-font);
  font-size: 31rpx;
  line-height: 1.3;
  font-weight: var(--gyt-font-weight-semibold, 600);
}

.profile-reference-page .menu-row-value {
  max-width: 196rpx;
  font-size: 26rpx;
  font-weight: var(--gyt-font-weight-medium, 500);
}

.profile-reference-page .menu-arrow {
  font-size: 40rpx;
  font-weight: var(--gyt-font-weight-medium, 500);
}

.profile-reference-page .pro-lock-badge {
  padding: 6rpx 13rpx;
  font-size: 19rpx;
}

.profile-reference-page .logout-card {
  font-size: 28rpx;
}

/* 导航栏同步全局字体，保留原有字号、图标尺寸与间距。 */
.profile-reference-page :deep(.tabbar.glass),
.profile-reference-page :deep(.tabbar.glass *) {
  font-family: var(--gyt-app-font);
}

.profile-reference-page :deep(.tabbar.glass .tab-icon-image) {
  width: 20px;
  height: 20px;
}

.profile-reference-page :deep(.tabbar.glass .tab-icon) {
  font-size: 34rpx;
  line-height: 1;
  font-weight: 900;
}

.profile-reference-page :deep(.tabbar.glass .tab-label) {
  font-size: 12px;
  line-height: 1.2;
  font-weight: 600;
}

.profile-reference-page :deep(.tabbar.glass .tab-item) {
  gap: 1px;
}

.profile-reference-page :deep(.tabbar.glass .tab-compact .tab-icon-image) {
  width: 20px;
  height: 20px;
}

.profile-reference-page :deep(.tabbar.glass .tab-compact .tab-label) {
  font-size: 14px;
  font-weight: 650;
}

.profile-exam-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 360;
  padding: calc(env(safe-area-inset-top) + 30rpx) 34rpx calc(env(safe-area-inset-bottom) + 30rpx);
  background: rgba(31, 29, 34, 0.36);
  display: flex;
  align-items: center;
  justify-content: center;
  -webkit-backdrop-filter: blur(6px);
  backdrop-filter: blur(6px);
  animation: profile-exam-backdrop-in 180ms ease-out both;
}

.profile-exam-modal {
  box-sizing: border-box;
  width: 100%;
  max-width: 650rpx;
  padding: 38rpx 32rpx 26rpx;
  border-radius: 40rpx;
  background: #ffffff;
  box-shadow: 0 30rpx 80rpx rgba(28, 25, 31, 0.2);
  transform-origin: 50% 55%;
  will-change: transform, opacity;
  animation: profile-exam-surface-in 260ms cubic-bezier(0.22, 1, 0.36, 1) both;
}

.profile-exam-modal-title {
  color: #29272b;
  text-align: center;
  font-size: 36rpx;
  line-height: 1.25;
  font-weight: 900;
}

@keyframes profile-exam-backdrop-in {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

@keyframes profile-exam-surface-in {
  from {
    opacity: 0;
    transform: translate3d(0, 28rpx, 0) scale(0.94);
  }

  to {
    opacity: 1;
    transform: translate3d(0, 0, 0) scale(1);
  }
}

.profile-exam-option-list {
  margin-top: 28rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.profile-exam-option {
  width: 100%;
  min-height: 124rpx;
  margin: 0;
  padding: 20rpx 22rpx;
  border: 2rpx solid #eeebf0;
  border-radius: 26rpx;
  background: #faf9fb;
  display: flex;
  align-items: center;
  gap: 18rpx;
  text-align: left;
}

.profile-exam-option.active {
  border-color: rgba(117, 91, 222, 0.36);
  background: #f4f1ff;
}

.profile-exam-option-copy {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.profile-exam-option-code {
  color: #302d35;
  font-size: 28rpx;
  line-height: 1.2;
  font-weight: 900;
}

.profile-exam-option-check {
  width: 42rpx;
  height: 42rpx;
  border: 2rpx solid #d8d4dc;
  border-radius: 999rpx;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 22rpx;
  line-height: 1;
  font-weight: 900;
}

.profile-exam-option.active .profile-exam-option-check {
  border-color: #765be0;
  background: #765be0;
}

.profile-exam-modal-cancel {
  width: 100%;
  min-height: 74rpx;
  margin: 18rpx 0 0;
  padding: 0;
  border: 0;
  border-radius: 22rpx;
  background: transparent;
  color: #76717a;
  font-size: 25rpx;
  line-height: 74rpx;
  font-weight: 750;
}

@media (prefers-reduced-motion: reduce) {
  .profile-exam-modal-mask,
  .profile-exam-modal {
    animation: none;
  }
}

.profile-edit-modal-mask,
.profile-email-modal-mask {
  position: fixed;
  inset: 0;
  z-index: 370;
  box-sizing: border-box;
  padding: calc(env(safe-area-inset-top) + 24rpx) 28rpx calc(env(safe-area-inset-bottom) + 24rpx);
  background: rgba(31, 29, 39, 0.38);
  display: flex;
  align-items: center;
  justify-content: center;
  -webkit-backdrop-filter: blur(8px);
  backdrop-filter: blur(8px);
}

.profile-edit-modal,
.profile-email-modal {
  position: relative;
  box-sizing: border-box;
  width: 100%;
  max-width: 650rpx;
  max-height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 48rpx);
  overflow-y: auto;
  padding: 34rpx 32rpx calc(28rpx + env(safe-area-inset-bottom));
  border: 1rpx solid rgba(113, 92, 192, 0.08);
  border-radius: 38rpx;
  background: #ffffff;
  box-shadow: 0 30rpx 90rpx rgba(36, 30, 60, 0.22);
}

.profile-email-modal {
  padding-bottom: calc(34rpx + env(safe-area-inset-bottom));
}

.profile-edit-modal-head {
  position: relative;
  min-height: 54rpx;
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.profile-edit-modal-title {
  position: absolute;
  left: 50%;
  top: 50%;
  width: calc(100% - 150rpx);
  overflow: hidden;
  transform: translate(-50%, -50%);
  color: #282532;
  text-align: center;
  font-size: 34rpx;
  line-height: 1.3;
  font-weight: 900;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.profile-edit-modal-cancel,
.profile-edit-avatar-trigger,
.profile-edit-save,
.profile-email-code-button {
  border: 0;
}

.profile-edit-modal-cancel::after,
.profile-edit-avatar-trigger::after,
.profile-edit-save::after,
.profile-email-code-button::after {
  border: 0;
}

.profile-edit-modal-cancel {
  position: relative;
  z-index: 1;
  width: 78rpx;
  height: 54rpx;
  margin: 0;
  padding: 0;
  border-radius: 18rpx;
  background: #f5f3f8;
  color: #777183;
  font-size: 23rpx;
  line-height: 54rpx;
  font-weight: 750;
}

.profile-edit-avatar-trigger {
  position: relative;
  width: 190rpx;
  height: 190rpx;
  margin: 30rpx auto 0;
  padding: 0;
  border-radius: 999rpx;
  background: linear-gradient(145deg, #ded9d4, #cfc8bd);
  color: #786f65;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
  box-shadow: 0 16rpx 36rpx rgba(57, 50, 66, 0.12);
}

.profile-edit-avatar-trigger.uploading {
  opacity: 0.68;
}

.profile-edit-avatar-image,
.profile-edit-avatar-fallback {
  display: block;
  width: 100%;
  height: 100%;
  border: 8rpx solid #ffffff;
  border-radius: 999rpx;
  box-sizing: border-box;
}

.profile-edit-avatar-image {
  object-fit: cover;
}

.profile-edit-avatar-fallback {
  color: #786f65;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 58rpx;
  line-height: 1;
  font-weight: 850;
}

.profile-edit-avatar-badge {
  position: absolute;
  right: -6rpx;
  bottom: 4rpx;
  min-width: 62rpx;
  height: 42rpx;
  padding: 0 12rpx;
  border: 4rpx solid #ffffff;
  border-radius: 999rpx;
  background: #765be0;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18rpx;
  line-height: 1;
  font-weight: 800;
  box-shadow: 0 8rpx 18rpx rgba(81, 62, 168, 0.2);
}

.profile-edit-avatar-hint {
  margin-top: 16rpx;
  color: #9b96a4;
  text-align: center;
  font-size: 21rpx;
  line-height: 1.4;
  font-weight: 600;
}

.profile-edit-field-label {
  margin: 28rpx 0 12rpx;
  color: #393442;
  font-size: 24rpx;
  line-height: 1.3;
  font-weight: 850;
}

.profile-edit-input {
  box-sizing: border-box;
  width: 100%;
  min-height: 84rpx;
  padding: 0 24rpx;
  border: 2rpx solid #ebe8f0;
  border-radius: 22rpx;
  background: #faf9fc;
  color: #292633;
  font-size: 27rpx;
  line-height: 84rpx;
  font-weight: 650;
}

.profile-edit-input:focus {
  border-color: rgba(118, 91, 224, 0.58);
  background: #ffffff;
}

.profile-edit-input::placeholder {
  color: #b5b0bd;
  font-weight: 500;
}

.profile-edit-copy {
  margin-top: 16rpx;
  color: #a09ba8;
  font-size: 20rpx;
  line-height: 1.45;
  font-weight: 550;
}

.profile-edit-save {
  width: 100%;
  min-height: 84rpx;
  margin: 28rpx 0 0;
  padding: 0 24rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #6b66e8, #7650c8);
  color: #ffffff;
  font-size: 27rpx;
  line-height: 84rpx;
  font-weight: 850;
  box-shadow: 0 14rpx 28rpx rgba(102, 79, 205, 0.2);
}

.profile-edit-save[disabled],
.profile-email-code-button[disabled] {
  opacity: 0.55;
}

.profile-email-current {
  margin-top: 28rpx;
  padding: 18rpx 20rpx;
  border-radius: 18rpx;
  background: #f7f5fb;
  color: #777181;
  font-size: 22rpx;
  line-height: 1.45;
  font-weight: 650;
}

.profile-email-code-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.profile-email-code-input {
  min-width: 0;
  flex: 1;
}

.profile-email-code-button {
  flex: 0 0 190rpx;
  height: 84rpx;
  margin: 0;
  padding: 0 12rpx;
  border-radius: 22rpx;
  background: #eeebff;
  color: #6650c7;
  font-size: 22rpx;
  line-height: 84rpx;
  font-weight: 800;
  white-space: nowrap;
}

@media screen and (max-width: 360px) {
  .profile-edit-modal-mask,
  .profile-email-modal-mask {
    padding-right: 18rpx;
    padding-left: 18rpx;
  }

  .profile-edit-modal,
  .profile-email-modal {
    padding-right: 24rpx;
    padding-left: 24rpx;
    border-radius: 32rpx;
  }

  .profile-email-code-row {
    gap: 10rpx;
  }

  .profile-email-code-button {
    flex-basis: 164rpx;
    font-size: 20rpx;
  }
}

.advice-detail-close,
.official-modal-close,
.wrong-modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
}

.circle-glass-page .circle-detail-page {
  gap: 18px;
}

.circle-glass-page .circle-detail-heading,
.circle-glass-page .circle-section-title,
.circle-glass-page .experience-title,
.circle-glass-page .material-title,
.circle-glass-page .circle-empty-title,
.circle-glass-page .circle-post-title,
.circle-glass-page .circle-post-section-title {
  color: #1c2423;
}

.circle-glass-page .circle-detail-heading,
.circle-glass-page .circle-section-title {
  font-weight: 650;
}

.circle-glass-page .circle-community-tabs {
  border-color: var(--circle-glass-border, rgba(255, 255, 255, 0.58));
  background: var(--circle-glass-surface);
}

.circle-glass-page .circle-community-tab.active {
  background: var(--circle-glass-active);
}

.circle-glass-page .community-filter-chip {
  border-color: var(--circle-glass-border, rgba(255, 255, 255, 0.58));
  background: var(--circle-glass-control);
}

.circle-glass-page .community-filter-chip.active,
.circle-glass-page .community-topic {
  background: var(--circle-glass-selected);
}

.circle-glass-page .community-post-card {
  border-color: var(--circle-glass-border, rgba(255, 255, 255, 0.58));
  background: var(--circle-glass-card);
  box-shadow: 0 16rpx 38rpx rgba(30, 55, 56, 0.09);
}

.circle-glass-page .circle-section-subtitle,
.circle-glass-page .experience-summary,
.circle-glass-page .material-desc,
.circle-glass-page .circle-empty-copy,
.circle-glass-page .circle-post-paragraph {
  color: #657473;
  font-weight: 500;
}

.circle-glass-page .circle-back-button {
  border: 0;
  border-radius: 26rpx;
  background: #ffffff;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.08);
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
  transition: transform 180ms ease, background-color 180ms ease;
}

.circle-glass-page .experience-search {
  border: 1px solid var(--circle-glass-border, rgba(255, 255, 255, 0.58));
  background: rgba(249, 252, 251, 0.38);
  box-shadow: 0 10px 24px rgba(30, 55, 56, 0.08);
  -webkit-backdrop-filter: blur(16px) saturate(118%);
  backdrop-filter: blur(16px) saturate(118%);
}

.circle-glass-page .experience-search-input {
  color: #2d3d3b;
}

.circle-glass-page .experience-search-placeholder {
  color: #758381;
}

.circle-glass-page .experience-search-clear {
  background: rgba(22, 120, 111, 0.1);
  color: #16786f;
}

.circle-glass-page .community-post-sort-control {
  border-color: rgba(22, 120, 111, 0.14);
  color: #16786f;
}

.circle-glass-page .circle-section-count,
.circle-glass-page .experience-filter-chip,
.circle-glass-page .material-subject-chip,
.circle-glass-page .material-action,
.circle-glass-page .circle-post-close,
.circle-glass-page .circle-post-action-row button {
  border-color: var(--circle-glass-border, rgba(255, 255, 255, 0.58));
  background: var(--circle-glass-control);
  color: #60716f;
  -webkit-backdrop-filter: blur(16px) saturate(118%);
  backdrop-filter: blur(16px) saturate(118%);
  transition: transform 180ms ease, background-color 180ms ease;
}

.circle-glass-page .experience-filter-chip.active,
.circle-glass-page .material-subject-chip.active {
  border-color: rgba(22, 120, 111, 0.16);
  background: var(--circle-glass-selected);
  color: #16786f;
}

.circle-glass-page .experience-card,
.circle-glass-page .material-card,
.circle-glass-page .material-subject-card,
.circle-glass-page .circle-empty-card,
.circle-glass-page .circle-post-sheet {
  border-color: var(--circle-glass-border, rgba(255, 255, 255, 0.78));
  background: var(--circle-glass-card);
  box-shadow: 0 16px 38px rgba(30, 55, 56, 0.09);
  -webkit-backdrop-filter: blur(18px) saturate(118%);
  backdrop-filter: blur(18px) saturate(118%);
}

.circle-glass-page .material-subject-card {
  background: var(--circle-glass-card-mint);
}

.circle-glass-page .experience-avatar,
.circle-glass-page .material-subject-mark,
.circle-glass-page .circle-post-stat-row,
.circle-glass-page .circle-post-checklist {
  border-color: transparent;
  background: #e8f1ee;
  color: #16786f;
}

.circle-glass-page .experience-tag,
.circle-glass-page .material-badge,
.circle-glass-page .experience-points text,
.circle-glass-page .material-tags text,
.circle-glass-page .experience-exam {
  background: #eef4f2;
  color: #49625f;
}

.circle-glass-page .experience-card,
.circle-glass-page .material-card {
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.circle-glass-page .experience-card:active,
.circle-glass-page .material-card:active {
  transform: scale(var(--circle-glass-press, 0.98));
}

.circle-glass-page .circle-back-button:active,
.circle-glass-page .experience-filter-chip:active,
.circle-glass-page .material-subject-chip:active,
.circle-glass-page .material-action:active,
.circle-glass-page .circle-post-close:active,
.circle-glass-page .circle-post-action-row button:active {
  transform: scale(var(--circle-glass-press, 0.98));
}

@supports not (backdrop-filter: blur(1px)) {
  .circle-glass-page .experience-search,
  .circle-glass-page .circle-community-tabs,
  .circle-glass-page .community-filter-chip,
  .circle-glass-page .circle-section-count,
  .circle-glass-page .experience-filter-chip,
  .circle-glass-page .material-subject-chip,
  .circle-glass-page .material-action,
  .circle-glass-page .circle-post-close,
  .circle-glass-page .circle-post-action-row button {
    background: #f7faf8;
  }

  .circle-glass-page .experience-card,
  .circle-glass-page .material-card,
  .circle-glass-page .material-subject-card,
  .circle-glass-page .circle-empty-card,
  .circle-glass-page .community-post-card,
  .circle-glass-page .circle-post-sheet {
    background: #fbfcfb;
  }

  .circle-glass-page .circle-community-tab.active {
    background: #ffffff;
  }
}

@media (prefers-reduced-motion: reduce) {
  .circle-glass-page .circle-entry,
  .circle-glass-page .circle-back-button,
  .circle-glass-page .experience-filter-chip,
  .circle-glass-page .material-subject-chip,
  .circle-glass-page .material-action,
  .circle-glass-page .circle-post-close,
  .circle-glass-page .circle-post-action-row button,
  .circle-glass-page .experience-card,
  .circle-glass-page .material-card {
    transition: none;
  }
}

@media (max-width: 350px) {
  .circle-glass-page .circle-trend-card {
    padding-right: 13px;
    padding-left: 13px;
  }

  .circle-glass-page .circle-trend-heading {
    gap: 5px;
  }

  .circle-glass-page .circle-trend-title {
    font-size: 21px;
  }

  .circle-glass-page .circle-trend-peak {
    font-size: 11px;
  }

  .circle-score-title {
    font-size: 20px;
  }

  .circle-score-total {
    font-size: 11px;
  }

  .circle-score-total text {
    font-size: 15px;
  }
}

@media (max-height: 760px) {
  .circle-insight-swiper {
    height: 200px;
    flex-basis: 200px;
  }

  .circle-glass-page .circle-entry {
    padding-top: 8px;
    padding-bottom: 8px;
  }

  .circle-glass-page .circle-entry-icon {
    width: 46px;
    height: 46px;
    border-radius: 16px;
  }

  .circle-glass-page .circle-entry-label {
    font-size: 19px;
  }

  .circle-glass-page .circle-entry-arrow {
    width: 34px;
    height: 34px;
    font-size: 22px;
  }
}

/* 清爽蓝主题下，研圈沿用全局蓝色配色与统一页面背景。 */
.home-page.circle-glass-page.circle-themed-page {
  --circle-bg: var(--gyt-primary-tint, #f4f8ff);
  --circle-bg-muted: var(--gyt-primary-soft, #edf4ff);
  --circle-card: #ffffff;
  --circle-card-muted: #ffffff;
  --circle-card-border: var(--gyt-primary-border, #d7e5ff);
  --circle-line: rgba(20, 31, 66, 0.1);
  --circle-text: #172033;
  --circle-muted: #667085;
  --circle-brand: var(--gyt-primary, #3478f6);
  --circle-brand-soft: var(--gyt-primary-soft, #edf4ff);
  --circle-mint: var(--gyt-primary, #3478f6);
  --circle-mint-soft: var(--gyt-primary-soft, #edf4ff);
  --circle-shadow: 0 16rpx 38rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.16));
  --circle-glass-surface: var(--gyt-panel-bg, #ffffff);
  --circle-glass-surface-strong: var(--gyt-panel-bg, #ffffff);
  --circle-glass-border: var(--gyt-primary-border, #d7e5ff);
  --circle-glass-card: var(--gyt-panel-bg, #ffffff);
  --circle-glass-card-mint: var(--gyt-panel-bg, #ffffff);
  --circle-glass-control: var(--gyt-primary-soft, #edf4ff);
  --circle-glass-selected: var(--gyt-primary-soft, #edf4ff);
  --circle-glass-active: var(--gyt-primary-tint, #f4f8ff);
  --circle-tab-bg: rgba(255, 255, 255, 0.94);
  --circle-tab-shadow: 0 20rpx 52rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.12));
  --circle-font: var(--gyt-app-font);
  background: var(--gyt-page-bg);
  color: #172033;
}

.home-page.circle-glass-page.circle-themed-page::before {
  content: none;
}

.home-page.circle-glass-page.circle-themed-page .circle-insight-dot {
  background: var(--gyt-primary-border, #d7e5ff);
  box-shadow: none;
}

.home-page.circle-glass-page.circle-themed-page .circle-insight-dot.active {
  background: var(--gyt-primary, #3478f6);
}

.home-page.circle-glass-page.circle-themed-page .circle-trend-peak-value,
.home-page.circle-glass-page.circle-themed-page .circle-score-total text {
  color: var(--gyt-primary, #3478f6);
}

.home-page.circle-glass-page.circle-themed-page .circle-trend-bar,
.home-page.circle-glass-page.circle-themed-page .circle-trend-bar.latest {
  background: var(--gyt-primary-gradient, linear-gradient(135deg, #3478f6, #68a0ff));
}

.home-page.circle-glass-page.circle-themed-page .circle-score-line,
.home-page.circle-glass-page.circle-themed-page .circle-score-point {
  stroke: var(--gyt-primary, #3478f6);
}

.home-page.circle-glass-page.circle-themed-page .circle-score-mirror-segment {
  background: var(--gyt-primary, #3478f6);
}

.home-page.circle-glass-page.circle-themed-page .circle-score-mirror-point {
  border-color: var(--gyt-primary, #3478f6);
}

.home-page.circle-glass-page.circle-themed-page .circle-entry:nth-child(n) {
  --circle-entry-bg: var(--gyt-panel-bg, #ffffff);
  --circle-entry-icon-bg: var(--gyt-primary-soft, #edf4ff);
  --circle-entry-icon-color: var(--gyt-primary, #3478f6);
}

.home-page.circle-glass-page.circle-themed-page .circle-entry-arrow {
  border-color: var(--gyt-primary-border, #d7e5ff);
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
}

.home-page.circle-glass-page.circle-themed-page .circle-back-button,
.home-page.circle-glass-page.circle-themed-page .experience-search,
.home-page.circle-glass-page.circle-themed-page .circle-community-tabs,
.home-page.circle-glass-page.circle-themed-page .community-filter-chip,
.home-page.circle-glass-page.circle-themed-page .scoreline-search,
.home-page.circle-glass-page.circle-themed-page .scoreline-select-control,
.home-page.circle-glass-page.circle-themed-page .scoreline-results-frame,
.home-page.circle-glass-page.circle-themed-page .scoreline-school-card,
.home-page.circle-glass-page.circle-themed-page .scoreline-load-more,
.home-page.circle-glass-page.circle-themed-page .scoreline-detail-card,
.home-page.circle-glass-page.circle-themed-page .experience-filter-chip,
.home-page.circle-glass-page.circle-themed-page .material-subject-chip,
.home-page.circle-glass-page.circle-themed-page .material-action,
.home-page.circle-glass-page.circle-themed-page .circle-post-close,
.home-page.circle-glass-page.circle-themed-page .circle-post-action-row button {
  border-color: var(--gyt-primary-border, #d7e5ff);
  background: var(--gyt-panel-bg, #ffffff);
  color: #667085;
}

.home-page.circle-glass-page.circle-themed-page .circle-back-button {
  border: 0;
  border-radius: 26rpx;
  background: #ffffff;
  color: #172033;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.08);
}

.home-page.circle-glass-page.circle-themed-page .circle-community-tab.active,
.home-page.circle-glass-page.circle-themed-page .community-filter-chip.active,
.home-page.circle-glass-page.circle-themed-page .experience-filter-chip.active,
.home-page.circle-glass-page.circle-themed-page .material-subject-chip.active {
  border-color: var(--gyt-primary-border, #d7e5ff);
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
}

.home-page.circle-glass-page.circle-themed-page .experience-search-clear,
.home-page.circle-glass-page.circle-themed-page .community-post-sort-control,
.home-page.circle-glass-page.circle-themed-page .circle-section-count,
.home-page.circle-glass-page.circle-themed-page .scoreline-select-value,
.home-page.circle-glass-page.circle-themed-page .scoreline-select-arrow-icon,
.home-page.circle-glass-page.circle-themed-page .scoreline-results-count,
.home-page.circle-glass-page.circle-themed-page .scoreline-results-reset,
.home-page.circle-glass-page.circle-themed-page .material-action,
.home-page.circle-glass-page.circle-themed-page .circle-post-close,
.home-page.circle-glass-page.circle-themed-page .circle-post-action-row button {
  color: var(--gyt-primary, #3478f6);
}

.home-page.circle-glass-page.circle-themed-page .experience-avatar,
.home-page.circle-glass-page.circle-themed-page .material-subject-mark,
.home-page.circle-glass-page.circle-themed-page .circle-post-stat-row,
.home-page.circle-glass-page.circle-themed-page .circle-post-checklist {
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
}

.home-page.circle-glass-page.circle-themed-page .experience-tag,
.home-page.circle-glass-page.circle-themed-page .material-badge,
.home-page.circle-glass-page.circle-themed-page .experience-points text,
.home-page.circle-glass-page.circle-themed-page .material-tags text,
.home-page.circle-glass-page.circle-themed-page .experience-exam,
.home-page.circle-glass-page.circle-themed-page .community-topic {
  background: var(--gyt-primary-tint, #f4f8ff);
  color: var(--gyt-primary, #3478f6);
}

/* 考研圈采用连续信息流：控制区轻量、内容区保持高阅读对比度。 */
.home-page.circle-glass-page.circle-themed-page .circle-community-tabs {
  border-color: var(--gyt-primary-border, #d7e5ff);
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 8rpx 22rpx rgba(25, 48, 89, 0.055);
}

.home-page.circle-glass-page.circle-themed-page .circle-community-tab.active {
  border: 0;
  background: transparent;
  color: var(--gyt-primary, #3478f6);
  box-shadow: none;
}

.home-page.circle-glass-page.circle-themed-page .experience-search {
  min-height: 72rpx;
  padding-right: 16rpx;
  padding-left: 16rpx;
  border-color: rgba(205, 219, 241, 0.92);
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 7rpx 20rpx rgba(25, 48, 89, 0.045);
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.home-page.circle-glass-page.circle-themed-page .community-filter-chip {
  border: 0;
  background: rgba(255, 255, 255, 0.8);
  color: #647086;
  box-shadow: none;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.home-page.circle-glass-page.circle-themed-page .community-filter-chip.active {
  border: 0;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
}
/* 刷题与研圈首页共用同一套首屏坐标：顶部概览区 + 四个等高入口。 */
.home-page.practice-home-page {
  --practice-overview-height: 230px;
  --practice-entry-gap: 10px;
  padding: calc(env(safe-area-inset-top) + 16px) 16px calc(env(safe-area-inset-bottom) + 124px);
}

.practice-dashboard {
  width: 100%;
  max-width: 860rpx;
  height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 140px);
  height: calc(100dvh - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 140px);
  min-height: 0;
  gap: var(--practice-entry-gap);
}

.practice-overview-carousel {
  position: relative;
  width: 100%;
  height: var(--practice-overview-height);
  min-height: 0;
  flex: 0 0 var(--practice-overview-height);
}

.practice-overview-swiper {
  width: 100%;
  height: 100%;
}

.practice-overview-swiper swiper-item,
.practice-overview-swiper .welcome-card {
  box-sizing: border-box;
  width: 100%;
  height: 100%;
  min-height: 0;
}

.practice-overview-pagination {
  position: absolute;
  right: 0;
  bottom: -8px;
  left: 0;
  z-index: 4;
  height: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  pointer-events: none;
}

.practice-overview-dot {
  width: 6px;
  height: 6px;
  min-height: 0;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 999px;
  background: rgba(126, 136, 156, 0.24);
  line-height: 0;
  transition: width 180ms ease, background-color 180ms ease;
  pointer-events: auto;
}

.practice-overview-dot::after {
  border: 0;
}

.practice-overview-dot.active {
  width: 18px;
  background: var(--gyt-primary, #3478f6);
}

.practice-dashboard .welcome-card {
  height: var(--practice-overview-height);
  min-height: 0;
  flex: 0 0 var(--practice-overview-height);
  padding: 24px 18px 20px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.practice-dashboard .practice-data-card {
  justify-content: flex-start;
  padding: 12px 14px 9px;
}

.practice-dashboard .daily-rank-preview-card {
  overflow: hidden;
  justify-content: flex-start;
  padding: 12px 14px 9px;
}

.daily-rank-preview-header {
  min-height: 38px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}

.daily-rank-preview-subtitle {
  display: block;
  margin-top: 3px;
  color: #8b94a4;
  font-size: 10px;
  line-height: 1.15;
  font-weight: 550;
}

.daily-rank-preview-live {
  min-height: 25px;
  padding: 0 9px;
  border-radius: 999px;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 9px;
  line-height: 1;
  font-weight: 700;
  white-space: nowrap;
}

.daily-rank-preview-live view {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--gyt-primary, #3478f6);
}

.daily-rank-preview-list,
.daily-rank-preview-state {
  min-height: 0;
  flex: 1 1 0;
}

.daily-rank-preview-list {
  display: grid;
  grid-template-rows: repeat(3, minmax(0, 1fr));
  gap: 2px;
}

.daily-rank-preview-row {
  min-width: 0;
  padding: 2px 4px;
  border-radius: 11px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.daily-rank-preview-row:first-child {
  background: var(--gyt-primary-tint, #f6f9ff);
}

.daily-rank-preview-position {
  width: 27px;
  height: 30px;
  flex: 0 0 27px;
  border-radius: 8px;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  line-height: 1;
  font-weight: 800;
}

.daily-rank-preview-position.has-medal {
  border-radius: 0;
  background: transparent;
}

.daily-rank-preview-medal {
  display: block;
  width: 27px;
  height: 30px;
}

.daily-rank-preview-avatar {
  width: 28px;
  height: 28px;
  flex: 0 0 28px;
  overflow: hidden;
  border-radius: 50%;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 800;
}

.daily-rank-preview-avatar image {
  width: 100%;
  height: 100%;
}

.daily-rank-preview-user {
  min-width: 0;
  flex: 1;
}

.daily-rank-preview-user > text {
  display: block;
  overflow: hidden;
  color: #243343;
  font-size: 12px;
  line-height: 1.15;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.daily-rank-preview-user > .daily-rank-preview-answer-count {
  margin-top: 2px;
  color: #929baa;
  font-size: 9px;
  font-weight: 550;
}

.daily-rank-preview-duration {
  flex: 0 0 auto;
  color: #172033;
  font-size: 12px;
  line-height: 1;
  font-weight: 800;
  white-space: nowrap;
}

.daily-rank-preview-state {
  color: #8b94a4;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 20px;
  text-align: center;
  font-size: 11px;
  line-height: 1.45;
}

.daily-rank-preview-state.is-error {
  color: #a85b55;
}

.daily-rank-preview-footer {
  min-height: 19px;
  padding: 1px 2px 0;
  color: #7d8798;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  font-size: 9px;
  line-height: 1;
  font-weight: 650;
}

.daily-rank-preview-footer > text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.daily-rank-preview-footer > view {
  flex: 0 0 auto;
  color: #4d596b;
  display: flex;
  align-items: center;
  gap: 3px;
  font-size: 10px;
  font-weight: 700;
}

.practice-data-header {
  min-height: 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.practice-data-title {
  min-width: 0;
  color: #172033;
  font-size: 19px;
  line-height: 1.2;
  font-weight: 800;
  white-space: nowrap;
}

.profile-phone-note {
  margin: 22rpx 2rpx 0;
  color: #8b94a4;
  font-size: 20rpx;
  line-height: 1.55;
  font-weight: 600;
}

.practice-data-period {
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  gap: 6px;
  color: #7d8798;
  font-size: 12px;
  line-height: 1;
  font-weight: 600;
}

.practice-data-overview {
  flex: 1 1 0;
  min-height: 0;
  margin-top: 6px;
  display: grid;
  grid-template-columns: 132px minmax(0, 1fr);
  align-items: center;
  gap: 8px;
}

.practice-accuracy-ring {
  position: relative;
  width: 128px;
  height: 128px;
  justify-self: center;
  display: flex;
  align-items: center;
  justify-content: center;
}

.practice-accuracy-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  transform: rotate(-90deg);
}

.practice-accuracy-app-ring {
  position: absolute;
  inset: 0;
  border-radius: 50%;
  background: var(--gyt-primary-soft, #edf4ff);
  background: conic-gradient(
    var(--gyt-primary, #3478f6) 0 var(--practice-ring-progress, 0%),
    var(--gyt-primary-soft, #edf4ff) var(--practice-ring-progress, 0%) 100%
  );
  transition: background 320ms ease;
}

/* 数字与圆环由同一条 JS 时间线驱动，动画期间关闭 CSS 过渡以保持同步。 */
.practice-accuracy-ring.is-animating .practice-accuracy-app-ring,
.practice-accuracy-ring.is-animating .practice-accuracy-progress {
  transition: none;
}

.practice-accuracy-app-ring::after {
  content: '';
  position: absolute;
  inset: 10px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.98);
}

.practice-accuracy-track,
.practice-accuracy-progress {
  fill: none;
  stroke-width: 8;
}

.practice-accuracy-track {
  stroke: var(--gyt-primary-soft, #edf4ff);
}

.practice-accuracy-progress {
  stroke: var(--gyt-primary, #3478f6);
  stroke-linecap: round;
  transition: stroke-dashoffset 320ms ease;
}

.practice-accuracy-copy {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.practice-accuracy-value {
  color: #172033;
  font-size: 30px;
  line-height: 1;
  font-weight: 900;
  letter-spacing: -0.5px;
}

.practice-accuracy-label {
  margin-top: 5px;
  color: #7d8798;
  font-size: 12px;
  line-height: 1;
  font-weight: 600;
}

.practice-key-metrics {
  min-width: 0;
  height: 128px;
  box-sizing: border-box;
  padding-left: 60px;
  display: grid;
  grid-template-rows: repeat(3, minmax(0, 1fr));
  align-items: stretch;
}

.practice-key-metric {
  min-width: 0;
  display: flex;
  align-items: center;
}

.practice-key-copy {
  min-width: 0;
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.practice-key-value {
  min-width: 50px;
  color: #172033;
  font-size: 22px;
  line-height: 1;
  font-weight: 900;
  white-space: nowrap;
}

.practice-key-label {
  overflow: hidden;
  color: #7d8798;
  font-size: 13px;
  line-height: 1.2;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.practice-data-link {
  min-height: 18px;
  margin-top: 2px;
  color: #4d596b;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  font-size: 12px;
  line-height: 1;
  font-weight: 700;
}

.practice-data-link-arrow {
  color: var(--gyt-primary, #3478f6);
  font-size: 19px;
  line-height: 0.8;
  font-weight: 700;
}

.practice-dashboard .welcome-main {
  gap: 13px;
}

.practice-dashboard .wave-icon {
  width: 52px;
  height: 52px;
  border-radius: 18px;
}

.practice-dashboard .welcome-title {
  font-size: 21px;
  line-height: 1.24;
  font-weight: 600;
}

.practice-dashboard .stats-card {
  margin-top: 20px;
  padding: 12px 4px;
  border-radius: 24px;
  box-shadow: none;
}

.practice-dashboard .stat-value {
  font-size: 24px;
}

.practice-dashboard .stat-label {
  margin-top: 6px;
  font-size: 14px;
}

.practice-dashboard .stat-divider {
  width: 1px;
  height: 38px;
}

.practice-entry-list {
  box-sizing: border-box;
  min-height: 0;
  flex: 1 1 0;
  display: grid;
  grid-template-rows: repeat(4, minmax(0, 1fr));
  gap: 0;
  padding: 6rpx 30rpx;
  border: 0;
  border-radius: 38rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14rpx 36rpx rgba(56, 49, 64, 0.045);
  overflow: hidden;
}

.practice-entry-list :deep(.module-card),
.practice-dashboard .mock-exam-card {
  width: 100%;
  min-height: 108rpx;
  height: 100%;
  margin: 0;
  padding: 18rpx 0;
  border: 0;
  border-bottom: 2rpx solid rgba(42, 55, 79, 0.065);
  border-radius: 0;
  background: transparent;
  box-shadow: none;
}

.practice-dashboard .mock-exam-card {
  display: flex;
  align-items: center;
  gap: 18rpx;
  overflow: hidden;
  transition: background-color 160ms ease, opacity 160ms ease;
}

.practice-dashboard .mock-exam-card:active {
  background: var(--gyt-primary-tint, #f4f8ff);
  opacity: 0.88;
}

.practice-dashboard .mock-exam-main {
  min-width: 0;
  flex: 1;
  gap: 18rpx;
  padding: 0;
}

.practice-dashboard .mock-exam-icon {
  width: 96rpx;
  height: 96rpx;
  flex: 0 0 96rpx;
  border-radius: 28rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  box-shadow: none;
  font-size: 70rpx;
  font-weight: 800;
}

.practice-dashboard .mock-exam-title {
  color: #243343;
  font-size: 38rpx;
  line-height: 1.3;
  font-weight: 800;
}

.practice-dashboard .mock-exam-sub {
  margin-top: 5rpx;
  overflow: hidden;
  font-size: 21rpx;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.practice-dashboard .mock-exam-arrow {
  position: static;
  width: 40rpx;
  height: 56rpx;
  flex: 0 0 40rpx;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: #c5cbd4;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 40rpx;
  line-height: 1;
  font-weight: 650;
}

.practice-dashboard .mock-exam-card {
  border-bottom: 0;
}

.glass-theme-page:not(.landing-glass-page) .practice-entry-list :deep(.module-card),
.glass-theme-page:not(.landing-glass-page) .practice-dashboard .mock-exam-card {
  box-shadow: none;
}

@media (max-height: 760px) {
  .home-page.practice-home-page {
    --practice-overview-height: 220px;
  }

  .practice-dashboard .welcome-card {
    padding: 20px 16px 16px;
  }

  .practice-dashboard .practice-data-card {
    padding: 9px 12px 7px;
  }

  .practice-data-title {
    font-size: 18px;
  }

  .practice-data-overview {
    grid-template-columns: 116px minmax(0, 1fr);
    gap: 8px;
  }

  .practice-accuracy-ring,
  .practice-key-metrics {
    width: 112px;
    height: 112px;
  }

  .practice-key-metrics {
    width: auto;
    padding-left: 56px;
  }

  .practice-accuracy-value {
    font-size: 27px;
  }

  .practice-accuracy-label {
    font-size: 11px;
  }

  .practice-key-value {
    min-width: 44px;
    font-size: 20px;
  }

  .practice-key-label {
    font-size: 12px;
  }

  .practice-data-link {
    margin-top: 2px;
  }

  .practice-dashboard .wave-icon {
    width: 46px;
    height: 46px;
    border-radius: 16px;
  }

  .practice-dashboard .welcome-title {
    font-size: 19px;
  }

  .practice-dashboard .stats-card {
    margin-top: 16px;
    padding-top: 10px;
    padding-bottom: 10px;
  }

  .practice-dashboard .stat-value {
    font-size: 22px;
  }

  .practice-dashboard .stat-label {
    font-size: 13px;
  }

  .practice-entry-list :deep(.module-card),
  .practice-dashboard .mock-exam-card {
    min-height: 96rpx;
    padding: 14rpx 0;
    gap: 16rpx;
  }

  .practice-entry-list {
    grid-template-rows: repeat(4, minmax(0, 1fr));
    padding-top: 4rpx;
    padding-bottom: 4rpx;
  }

  .practice-dashboard .mock-exam-main {
    gap: 16rpx;
  }

  .practice-dashboard .mock-exam-icon {
    width: 84rpx;
    height: 84rpx;
    flex-basis: 84rpx;
    border-radius: 24rpx;
    font-size: 62rpx;
  }

  .practice-dashboard .mock-exam-title {
    font-size: 36rpx;
  }

  .practice-dashboard .mock-exam-sub {
    font-size: 20rpx;
  }

  .practice-dashboard .mock-exam-arrow {
    width: 36rpx;
    height: 52rpx;
    flex-basis: 36rpx;
    font-size: 36rpx;
  }
}

@media (max-width: 350px) {
  .practice-data-overview {
    grid-template-columns: 108px minmax(0, 1fr);
    gap: 7px;
  }

  .practice-accuracy-ring,
  .practice-key-metrics {
    width: 104px;
    height: 104px;
  }

  .practice-key-metrics {
    width: auto;
    padding-left: 50px;
  }

  .practice-key-copy {
    gap: 5px;
  }

  .practice-key-value {
    min-width: 38px;
    font-size: 19px;
  }

  .practice-key-label {
    font-size: 10px;
  }

  .practice-entry-list :deep(.module-card),
  .practice-dashboard .mock-exam-card {
    gap: 14rpx;
  }

  .practice-dashboard .mock-exam-main {
    gap: 14rpx;
  }
}

/* 刷题与研圈入口统一采用“我的”页面的分组列表语言。 */
.home-page.circle-glass-page .circle-overview .circle-entry-list {
  box-sizing: border-box;
  min-height: 0;
  flex: 1 1 0;
  display: grid;
  grid-template-rows: repeat(4, minmax(0, 1fr));
  gap: 0;
  padding: 6rpx 30rpx;
  border: 0;
  border-radius: 38rpx;
  background: rgba(255, 255, 255, 0.94);
  box-shadow: 0 14rpx 36rpx rgba(56, 49, 64, 0.045);
  overflow: hidden;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.home-page.circle-glass-page .circle-overview .circle-entry {
  box-sizing: border-box;
  min-height: 108rpx;
  height: 100%;
  margin: 0;
  padding: 18rpx 0;
  border: 0;
  border-bottom: 2rpx solid rgba(42, 55, 79, 0.065);
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  gap: 18rpx;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
  transition: background-color 160ms ease, opacity 160ms ease;
}

.home-page.circle-glass-page .circle-overview .circle-entry:last-child {
  border-bottom: 0;
}

.home-page.circle-glass-page .circle-overview .circle-entry:active {
  background: var(--gyt-primary-tint, #f4f8ff);
  opacity: 0.88;
  transform: none;
}

.home-page.circle-glass-page .circle-overview .circle-entry-icon {
  box-sizing: border-box;
  width: 96rpx;
  height: 96rpx;
  flex: 0 0 96rpx;
  border: 0;
  border-radius: 28rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #3478f6);
  box-shadow: none;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.home-page.circle-glass-page .circle-overview .circle-entry-icon-image {
  width: 88rpx;
  height: 88rpx;
}

.home-page.circle-glass-page .circle-overview .circle-entry-label {
  color: #243343;
  font-size: 38rpx;
  line-height: 1.3;
  font-weight: 800;
}

.home-page.circle-glass-page .circle-overview .circle-entry-arrow {
  width: 40rpx;
  height: 56rpx;
  flex: 0 0 40rpx;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: #c5cbd4;
  font-size: 40rpx;
  line-height: 1;
  font-weight: 650;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.circle-entry-unread-count,
.circle-community-tab-unread {
  box-sizing: border-box;
  min-width: 30rpx;
  height: 30rpx;
  padding: 0 8rpx;
  border: 3rpx solid rgba(255, 255, 255, 0.94);
  border-radius: 999rpx;
  background: #f25555;
  color: #ffffff;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 17rpx;
  line-height: 1;
  font-weight: var(--gyt-font-weight-bold, 700);
  white-space: nowrap;
  box-shadow: 0 4rpx 10rpx rgba(242, 85, 85, 0.2);
}

.circle-entry-unread-count {
  flex: 0 0 auto;
}

.circle-community-tab-unread {
  margin-left: 7rpx;
  transform: translateY(-8rpx);
}

.mentor-unread-entry-list {
  display: flex;
  flex-direction: column;
  gap: 2rpx;
  overflow: hidden;
  border: 2rpx solid rgba(52, 120, 246, 0.12);
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.9);
}

.mentor-unread-entry {
  min-height: 80rpx;
  margin: 0;
  padding: 14rpx 18rpx;
  border: 0;
  border-radius: 0;
  background: transparent;
  display: flex;
  align-items: center;
  gap: 13rpx;
  text-align: left;
}

.mentor-unread-entry + .mentor-unread-entry {
  border-top: 2rpx solid rgba(42, 55, 79, 0.065);
}

.mentor-unread-entry::after {
  border: 0;
}

.mentor-unread-entry:active {
  background: var(--gyt-primary-tint, #f4f8ff);
}

.mentor-unread-entry-dot {
  width: 14rpx;
  height: 14rpx;
  flex: 0 0 14rpx;
  border-radius: 50%;
  background: #f25555;
  box-shadow: 0 0 0 6rpx rgba(242, 85, 85, 0.1);
}

.mentor-unread-entry-copy {
  min-width: 0;
  flex: 1;
}

.mentor-unread-entry-copy strong,
.mentor-unread-entry-copy text {
  display: block;
}

.mentor-unread-entry-copy strong {
  color: #26384f;
  font-size: 23rpx;
  line-height: 1.3;
  font-weight: 900;
}

.mentor-unread-entry-copy text {
  margin-top: 4rpx;
  color: #8491a4;
  font-size: 18rpx;
  line-height: 1.35;
  font-weight: 700;
}

.mentor-unread-entry-arrow {
  flex: 0 0 auto;
  color: #a8b3c2;
  font-size: 34rpx;
  line-height: 1;
}

.community-unread-entry {
  min-height: 68rpx;
  margin: 0;
  padding: 12rpx 17rpx;
  border: 2rpx solid rgba(242, 85, 85, 0.12);
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.88);
  color: #5d6d82;
  display: flex;
  align-items: center;
  gap: 13rpx;
  font-size: 20rpx;
  line-height: 1.35;
  font-weight: 750;
  text-align: left;
}

.community-unread-entry::after {
  border: 0;
}

.community-unread-entry text {
  min-width: 0;
  flex: 1;
}

.community-unread-entry strong {
  flex: 0 0 auto;
  color: var(--gyt-primary, #3478f6);
  font-size: 20rpx;
  font-weight: 900;
}

.community-post-card.has-unread-interaction {
  background: rgba(255, 255, 255, 0.96);
}

.community-post-unread-badge {
  min-width: max-content;
  padding: 7rpx 11rpx;
  border-radius: 999rpx;
  background: rgba(242, 85, 85, 0.1);
  color: #d94b4b;
  font-size: 18rpx;
  line-height: 1;
  font-weight: 900;
  white-space: nowrap;
}

.mentor-console-entry {
  position: fixed;
}

@media (max-height: 760px) {
  .home-page.circle-glass-page .circle-overview .circle-entry-list {
    grid-template-rows: repeat(4, minmax(0, 1fr));
    padding-top: 4rpx;
    padding-bottom: 4rpx;
  }

  .home-page.circle-glass-page .circle-overview .circle-entry {
    min-height: 96rpx;
    padding-top: 14rpx;
    padding-bottom: 14rpx;
    gap: 16rpx;
  }

  .home-page.circle-glass-page .circle-overview .circle-entry-icon {
    width: 84rpx;
    height: 84rpx;
    flex-basis: 84rpx;
    border-radius: 24rpx;
  }

  .home-page.circle-glass-page .circle-overview .circle-entry-icon-image {
    width: 78rpx;
    height: 78rpx;
  }

  .home-page.circle-glass-page .circle-overview .circle-entry-label {
    font-size: 36rpx;
  }

  .home-page.circle-glass-page .circle-overview .circle-entry-arrow {
    width: 36rpx;
    height: 52rpx;
    flex-basis: 36rpx;
    font-size: 36rpx;
  }
}

/* #ifdef MP-WEIXIN */
.home-page {
  padding-top: var(--mp-page-content-top, 96px);
}

.home-page.practice-home-page {
  padding-top: var(--mp-page-content-top, 96px);
}

.home-header {
  --home-header-control-size: 68rpx;
  min-height: 0;
  padding: 2rpx 10rpx 0;
}

.brand-line {
  gap: 0;
  align-items: center;
}

.home-header-brand {
  gap: 10rpx;
}

.home-header-logo {
  border-radius: 16rpx;
}

.home-header-title {
  font-size: 30rpx;
}

.home-header-status {
  margin-top: 12rpx;
  gap: 8rpx;
}

.home-status-pill {
  padding: 9rpx 12rpx;
  gap: 6rpx;
}

.home-status-label {
  font-size: 18rpx;
}

.home-status-value {
  font-size: 19rpx;
}

.home-actions {
  gap: 12rpx;
}

.message-bell {
  line-height: 1;
}

.message-bell-icon {
  width: 30rpx;
  height: 30rpx;
}

.profile-entry {
  border: 2rpx solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 8rpx 20rpx rgba(20, 31, 66, 0.1);
}

/* #endif */

@media (prefers-reduced-motion: reduce) {
  .circle-detail-route-layer.is-route-moving,
  .community-reader.is-route-moving,
  .subscription-sheet-mask,
  .subscription-sheet {
    transition-duration: 1ms !important;
  }
}

.community-author-verified {
  display: inline-flex;
  align-items: center;
  margin-left: 8rpx;
  padding: 3rpx 7rpx;
  border-radius: 999rpx;
  vertical-align: middle;
  color: #287d6d;
  background: #e5f7f1;
  font-size: 16rpx;
  font-weight: 800;
  line-height: 1.25;
}

.community-reader-comment-more {
  width: 54rpx;
  min-width: 54rpx;
  height: 54rpx;
  min-height: 54rpx;
  margin: 0 0 0 4rpx;
  padding: 0;
  border: 0;
  border-radius: 50%;
  color: #91a0b1;
  background: transparent;
  font-size: 20rpx;
  line-height: 1;
}

.community-reader-comment-more::after {
  border: 0;
}

.profile-message-entry {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin: 20rpx 0;
  padding: 21rpx 22rpx;
  border: 2rpx solid rgba(229, 226, 224, .94);
  border-radius: 25rpx;
  background: rgba(255, 255, 255, .94);
  box-shadow: 0 10rpx 24rpx rgba(48, 42, 38, .045);
}

.profile-message-icon {
  width: 54rpx;
  height: 54rpx;
  flex: none;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 18rpx;
  color: var(--gyt-primary, #3478f6);
  background: var(--gyt-primary-soft, #edf4ff);
}

.profile-message-copy {
  min-width: 0;
  flex: 1;
}

.profile-message-title {
  color: #2b3d59;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1.35;
}

.profile-message-desc {
  margin-top: 5rpx;
  overflow: hidden;
  color: #8495aa;
  font-size: 19rpx;
  line-height: 1.4;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.profile-message-count {
  min-width: 32rpx;
  height: 32rpx;
  padding: 0 8rpx;
  box-sizing: border-box;
  border-radius: 16rpx;
  color: #fff;
  background: #f05d5d;
  font-size: 17rpx;
  font-weight: 900;
  line-height: 32rpx;
  text-align: center;
}

/* 历年分数线沿用“我的”页的分组卡语言：暖灰底、白卡、深色信息，
   仅保留绿色分数作为数据语义色。 */
.home-page.circle-glass-page .circle-scoreline-section {
  --scoreline-surface: rgba(255, 255, 255, 0.96);
  --scoreline-soft: #f7f6f8;
  --scoreline-ink: #243343;
  --scoreline-muted: #85808a;
  --scoreline-line: rgba(42, 38, 48, 0.065);
  --scoreline-arrow: #c9c5cc;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-select-control,
.home-page.circle-glass-page .circle-scoreline-section .scoreline-search {
  border: 0;
  background: var(--scoreline-surface);
  box-shadow: 0 10rpx 26rpx rgba(56, 49, 64, 0.045);
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-select-control {
  min-height: 72rpx;
  padding-right: 20rpx;
  padding-left: 20rpx;
  border-radius: 24rpx;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-search {
  min-height: 84rpx;
  border-radius: 28rpx;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-select-name,
.home-page.circle-glass-page .circle-scoreline-section .scoreline-search-placeholder {
  color: var(--scoreline-muted);
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-select-value {
  color: #4b4750;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-search-clear {
  background: #f0eef2;
  color: #68636c;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-results-frame {
  border: 0;
  border-radius: 36rpx;
  background: var(--scoreline-surface);
  box-shadow: 0 14rpx 36rpx rgba(56, 49, 64, 0.04);
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-results-heading {
  min-height: 86rpx;
  padding: 18rpx 28rpx;
  border-bottom-color: var(--scoreline-line);
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-results-title,
.home-page.circle-glass-page .circle-scoreline-section .scoreline-school-name {
  color: var(--scoreline-ink);
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-results-count,
.home-page.circle-glass-page .circle-scoreline-section .scoreline-results-reset {
  color: #8f8a93;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-results-content {
  padding: 0 28rpx 24rpx;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-school-list {
  gap: 0;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-school-card {
  padding: 26rpx 0;
  border: 0;
  border-bottom: 2rpx solid var(--scoreline-line);
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-school-card:last-child {
  border-bottom: 0;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-school-card:active {
  background: rgba(247, 246, 248, 0.72);
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-school-meta,
.home-page.circle-glass-page .circle-scoreline-section .scoreline-year-label {
  color: var(--scoreline-muted);
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-school-arrow {
  color: var(--scoreline-arrow);
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-year-cell,
.home-page.circle-glass-page .circle-scoreline-section .scoreline-detail-note {
  background: var(--scoreline-soft);
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-load-more {
  margin-top: 18rpx;
  border: 0;
  background: var(--scoreline-soft);
  color: #68636c;
  box-shadow: none;
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-empty-card {
  border: 0;
  background: transparent;
  box-shadow: none;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-detail-card {
  border: 0;
  background: var(--scoreline-surface);
  box-shadow: 0 14rpx 36rpx rgba(56, 49, 64, 0.04);
  -webkit-backdrop-filter: none;
  backdrop-filter: none;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-detail-region {
  background: #f0eef2;
  color: #68636c;
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-detail-chart,
.home-page.circle-glass-page .circle-scoreline-section .scoreline-history-list,
.home-page.circle-glass-page .circle-scoreline-section .scoreline-history-item {
  border-color: var(--scoreline-line);
}

.home-page.circle-glass-page .circle-scoreline-section .scoreline-detail-card .circle-score-line,
.home-page.circle-glass-page .circle-scoreline-section .scoreline-detail-card .circle-score-point {
  stroke: var(--gyt-primary, #3478f6);
}

/* 顶部轮播数据卡与“我的”页分组卡使用同一层白色底。 */
.home-page.circle-glass-page .circle-overview .circle-insight-swiper .circle-glass-surface {
  background: rgba(255, 255, 255, 0.94);
}

</style>
