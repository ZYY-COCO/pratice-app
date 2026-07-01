<template>
  <view class="page home-page" :class="{ 'no-tab-page': !showBottomTab }" :style="themeInlineStyle">
    <template v-if="activeTab === 'home'">
      <view class="home-dashboard">
        <view class="home-header">
          <view class="brand-line">
            <text class="brand-title">港研通</text>
            <text v-if="isAuthed" class="brand-badge">{{ examCode }}</text>
          </view>
          <view class="home-actions">
            <button v-if="isAuthed" class="message-bell" :class="{ unread: officialUnreadCount > 0 }" @tap="openOfficialMessages">
              <text>🔔</text>
              <view v-if="officialUnreadCount > 0" class="message-dot"></view>
            </button>
            <view class="profile-entry" @tap="activeTab = 'profile'">
              <text>{{ avatarText }}</text>
            </view>
          </view>
        </view>

        <view class="welcome-card" @tap="goLeaderboard">
          <view class="welcome-main">
            <view class="wave-icon">👋</view>
            <view class="welcome-copy">
              <text class="welcome-title">{{ dashboard.userName }}，今天刷一组题吧</text>
              <text class="welcome-subtitle">登录后可直接刷真题并同步错题本</text>
            </view>
            <view class="hero-illustration">📋</view>
          </view>

          <view class="stats-card">
            <view class="stat-item">
              <text class="stat-value">{{ homeStats.weeklyAnswers }}</text>
              <text class="stat-label">本周刷题</text>
            </view>
            <view class="stat-divider"></view>
            <view class="stat-item">
              <text class="stat-value">{{ homeStats.accuracy }}</text>
              <text class="stat-label">总正确率</text>
            </view>
            <view class="stat-divider"></view>
            <view class="stat-item">
              <text class="stat-value">{{ homeStats.wrongCount }}</text>
              <text class="stat-label">错题数</text>
            </view>
          </view>
        </view>

        <view class="module-grid">
          <ModuleCard
            v-for="(item, index) in moduleCards"
            :key="item.key"
            :item="item"
            :index="index + 1"
            @select="goModule"
          />
        </view>

        <view class="mock-exam-card" @tap="openMockExamIntro">
          <view class="mock-exam-main">
            <view class="mock-exam-icon">卷</view>
            <view class="mock-exam-copy">
              <view class="mock-exam-title">模拟测试</view>
              <view class="mock-exam-sub">55 题 / 105 分，按 {{ examCode }} 轻量组卷</view>
            </view>
          </view>
          <view class="mock-exam-meta">
            <text>中华文化常识</text>
            <text>英语语言知识</text>
            <text>{{ mockExamThirdSubject }}</text>
          </view>
          <view class="mock-exam-arrow">›</view>
        </view>

      </view>
    </template>

    <template v-else-if="activeTab === 'mistakes'">
      <view class="mistake-page-head">
        <button class="icon-back-btn" @tap="handleMistakeBack">
          <image class="back-icon" src="/static/ui-icons/back.svg" mode="aspectFit" />
        </button>
        <view class="mistake-head-copy">
          <view class="head-title">{{ retestMode ? '错题重测' : '错题本' }}</view>
          <view class="head-subtitle">{{ retestMode ? retestScopeText : mistakeSubtitle }}</view>
        </view>
        <button
          v-if="!retestMode"
          class="retest-entry-btn"
          :disabled="!isAuthed || retestCandidateMistakes.length === 0"
          @tap="startWrongRetest"
        >
          {{ retestButtonText }}
        </button>
      </view>

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

        <view v-else-if="retestLoading" class="state-box">正在加载本题...</view>

        <SectionCard v-else-if="retestDetail" :title="`重测进度 ${retestProgressLabel}`" subtitle="作答后立即查看本题解析。">
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
            <view v-if="!retestResultText" class="review-hint">请选择一个答案后提交，本题会立即显示正误和解析。</view>
            <view v-if="retestResultText" class="state-box" :class="{ mastered: retestMastered }">{{ retestResultText }}</view>
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
        <SectionCard title="最近需要重刷">
          <view v-if="!isAuthed" class="state-box warning">登录后才能查看你的真实错题本。</view>
          <view v-else class="filter-card">
            <view class="filter-tip">先选择科目或模块，再点击右上角重测，可只复盘当前范围的错题。</view>
            <scroll-view scroll-x class="filter-scroll">
              <button
                v-for="item in subjectFilters"
                :key="item"
                class="filter-chip"
                :class="{ active: wrongFilters.subject === item }"
                @tap="setWrongFilter('subject', item)"
              >
                {{ item || '全部科目' }}
              </button>
            </scroll-view>
            <scroll-view scroll-x class="filter-scroll">
              <button
                v-for="item in moduleFilters"
                :key="item"
                class="filter-chip"
                :class="{ active: wrongFilters.module === item }"
                @tap="setWrongFilter('module', item)"
              >
                {{ item || '全部模块' }}
              </button>
            </scroll-view>
            <scroll-view scroll-x class="filter-scroll">
              <button
                v-for="item in submoduleFilters"
                :key="item"
                class="filter-chip"
                :class="{ active: wrongFilters.submodule === item }"
                @tap="setWrongFilter('submodule', item)"
              >
                {{ item || '全部子模块' }}
              </button>
            </scroll-view>
          </view>
          <view v-if="wrongLoading" class="state-box">正在读取真实错题记录...</view>
          <view v-else-if="wrongError" class="state-box warning">{{ wrongError }}</view>
          <view v-else-if="isAuthed && filteredMistakes.length === 0" class="state-box">当前筛选条件下还没有错题。</view>
          <MistakeList v-else :items="visibleMistakes" @select="openWrongDetail" />
          <view v-if="fullMistakes.length" class="list-load-state" @tap="loadMoreMistakes">
            {{ hasMoreMistakes ? '继续下滑加载更多错题' : '已加载全部错题' }}
          </view>
        </SectionCard>
      </template>

      <view v-if="selectedWrongDetail" class="wrong-modal-mask" @tap="closeWrongDetail">
        <view class="wrong-modal-panel" @tap.stop>
          <view class="wrong-modal-grabber"></view>
          <view class="wrong-modal-head">
            <view>
              <view class="wrong-modal-title">错题重练</view>
              <view class="wrong-modal-sub">
                {{ selectedWrongDetail.question.subject }} / {{ selectedWrongDetail.question.module }}
              </view>
            </view>
            <button class="wrong-modal-close" @tap="closeWrongDetail">×</button>
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
    </template>

    <template v-else-if="activeTab === 'report'">
      <view class="report-dashboard">
        <view class="report-topbar">
          <button class="icon-back-btn" @tap="activeTab = 'profile'">
            <image class="back-icon" src="/static/ui-icons/back.svg" mode="aspectFit" />
          </button>
          <view class="report-top-title">学习报告</view>
          <view class="report-top-spacer"></view>
        </view>

        <view v-if="reportLoading" class="state-box">正在生成真实学习报告...</view>
        <view v-else-if="reportError" class="state-box warning">{{ reportError }}</view>

        <view class="report-overview-card">
          <view class="overview-copy">
            <view class="overview-title-row">
              <text class="overview-title">本周学习概览</text>
              <text class="overview-info">i</text>
            </view>
            <view class="overview-subtitle">{{ reportOverview.subtitle }}</view>
          </view>
          <view class="overview-art">📈</view>
          <view class="overview-metrics">
            <view class="overview-metric">
              <view class="metric-icon blue">▦</view>
              <view>
                <view class="metric-label">本周做题总数</view>
                <view class="metric-value">{{ reportOverview.weeklyAnswers }}<text>题</text></view>
              </view>
            </view>
            <view class="overview-metric">
              <view class="metric-icon green">◎</view>
              <view>
                <view class="metric-label">整体正确率</view>
                <view class="metric-value">{{ reportOverview.accuracy }}</view>
              </view>
            </view>
          </view>
          <view class="overview-trend">{{ reportOverview.trend }}</view>
        </view>

        <view v-if="!isAuthed" class="state-box warning">登录并完成几道题后，这里会显示你的真实能力统计。</view>
        <view v-else-if="report.items.length === 0" class="state-box">暂无能力统计。先完成一轮专项或综合刷题吧。</view>

        <view v-else class="subject-report-list">
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
                  <view class="subject-icon">{{ item.icon }}</view>
                  <view class="subject-title">{{ item.subject }}</view>
                </view>
                <view class="subject-status" :class="item.tone">{{ item.status }}</view>
              </view>
              <view class="subject-count-label">做题数量</view>
              <view class="subject-count">{{ item.total }}<text>题</text></view>
              <view class="progress-track">
                <view class="progress-fill" :class="item.tone" :style="{ width: `${item.accuracy}%` }"></view>
              </view>
              <view class="subject-trend">{{ item.tip }}</view>
            </view>
          </view>
        </view>

        <view class="learning-advice-card">
          <view class="advice-head">
            <view class="advice-title-wrap">
              <view class="advice-icon">💡</view>
              <view>
                <view class="advice-title">学习建议</view>
                <view class="advice-subtitle">{{ studyAdviceSubtitle }}</view>
              </view>
            </view>
          </view>
          <view v-if="studyAdviceLoading" class="state-box advice-loading">正在分析你的薄弱点...</view>
          <view v-else-if="studyAdviceError" class="state-box warning advice-loading">{{ studyAdviceError }}</view>
          <view class="advice-list">
            <view v-for="item in reportAdvice" :key="item" class="advice-item">
              <text class="advice-dot">✓</text>
              <text>{{ item }}</text>
            </view>
          </view>
          <button v-if="isAuthed" class="advice-detail-btn" @tap="openStudyAdviceDetail">
            查看详细建议
          </button>
          <button v-if="dailyPlan.length" class="report-action-btn" @tap="openRecommendedTrainingSheet">
            开始推荐训练
          </button>
        </view>
      </view>
    </template>

    <template v-else>
      <view class="profile-dashboard">
        <view class="profile-top-title">港研通</view>

        <view class="account-card" :class="{ guest: !isAuthed }" @tap="handleAccountEntry">
          <view class="account-avatar">{{ profileAvatarText }}</view>
          <view class="account-main">
            <view class="account-name-row">
              <text class="account-name">{{ profile.userName }}</text>
              <text class="account-badge">{{ profile.badge }}</text>
            </view>
            <view class="account-desc">{{ isAuthed ? profile.subtitle : '登录后同步学习进度与数据' }}</view>
            <button v-if="!isAuthed" class="account-login-btn" @tap.stop="goLogin">登录 / 注册</button>
            <view v-else class="exam-switch">
              <button
                v-for="option in examOptions"
                :key="option.code"
                class="exam-pill"
                :class="{ active: option.code === examCode }"
                @tap.stop="changeExam(option.code)"
              >
                {{ option.code }}
              </button>
            </view>
          </view>
          <view class="account-arrow">›</view>
        </view>

        <view class="member-card" :class="{ active: isProMember }">
          <view class="member-copy">
            <view class="member-kicker">{{ isProMember ? '学习权益 · 已开通' : '学习功能预览' }}</view>
            <view class="member-title">高级学习能力</view>
            <view class="member-subtitle">{{ memberCardSubtitle }}</view>
            <button v-if="isAuthed && isProMember" class="member-login-btn" @tap="handleProEntry">
              查看权益
            </button>
          </view>
          <view class="shield-art" :class="{ active: isProMember }">{{ isProMember ? 'PRO' : '✓' }}</view>
          <view class="benefit-row">
            <view v-for="item in profileBenefits" :key="item.label" class="benefit-item">
              <view class="benefit-icon" :class="item.iconClass">
                <image v-if="item.iconSrc" class="benefit-icon-img" :src="item.iconSrc" mode="aspectFit" />
                <text v-else-if="!item.iconClass">{{ item.icon }}</text>
              </view>
              <view class="benefit-label">{{ item.label }}</view>
            </view>
          </view>
        </view>

        <view class="profile-section-card">
          <view class="profile-section-title">练习工具</view>
          <view class="menu-list">
            <view
              v-for="item in practiceTools"
              :key="item.label"
              class="menu-row"
              :class="{ locked: item.locked }"
              @tap="handleMenu(item)"
            >
              <view class="menu-icon" :class="[item.tone, item.iconClass]">
                <image v-if="item.iconSrc" class="menu-icon-img" :src="item.iconSrc" mode="aspectFit" />
                <text v-else-if="!item.iconClass">{{ item.icon }}</text>
              </view>
              <view class="menu-copy">
                <view class="menu-title-row">
                  <text class="menu-title">{{ item.label }}</text>
                  <text v-if="item.locked" class="pro-lock-badge">Pro</text>
                </view>
                <view class="menu-subtitle">{{ item.desc }}</view>
              </view>
              <view class="menu-arrow">›</view>
            </view>
          </view>
        </view>

        <view class="profile-section-card">
          <view class="profile-section-title">其他服务</view>
          <view class="menu-list">
            <view v-for="item in serviceTools" :key="item.label" class="menu-row" @tap="handleMenu(item)">
              <view class="menu-icon" :class="item.tone">
                <image v-if="item.iconSrc" class="menu-icon-img" :src="item.iconSrc" mode="aspectFit" />
                <text v-else>{{ item.icon }}</text>
              </view>
              <view class="menu-copy">
                <view class="menu-title">{{ item.label }}</view>
                <view class="menu-subtitle">{{ item.desc }}</view>
              </view>
              <view class="menu-arrow">›</view>
            </view>
          </view>
        </view>

        <view v-if="isAuthed" class="logout-card" @tap="logout">退出登录</view>
      </view>
    </template>

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
            <view class="smart-tip">
              <view class="smart-tip-icon">✦</view>
              <view class="smart-tip-copy">
                {{ recommendationLoading ? '正在读取你的错题和能力统计...' : '系统将根据你的正确率、错题类型和薄弱知识点，自动生成本次训练题目。' }}
              </view>
            </view>
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

    <view v-if="showStudyAdviceDetail" class="advice-detail-mask" @tap="closeStudyAdviceDetail">
      <view class="advice-detail-sheet" @tap.stop>
        <view class="advice-detail-handle"></view>
        <button class="advice-detail-close" @tap="closeStudyAdviceDetail">×</button>
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
        <button class="advice-detail-action" @tap="openRecommendedTrainingSheet">按建议生成训练</button>
      </view>
    </view>

    <view v-if="showProModal" class="pro-modal-mask" @tap="handleCloseProModal">
      <view class="pro-modal-sheet" @tap.stop>
        <view class="pro-modal-handle"></view>
        <button class="pro-modal-close" @tap="handleCloseProModal">×</button>
        <view class="pro-modal-head">
          <view class="pro-modal-title">学习功能预览</view>
          <view class="pro-modal-subtitle">后续版本会逐步增强学习报告和训练建议</view>
          <view class="pro-status-pill">当前版本专注学习功能体验</view>
        </view>

        <view class="pro-benefit-list">
          <view
            v-for="item in proBenefits"
            :key="item.title"
            class="pro-benefit-item"
          >
            <view class="pro-benefit-icon" :class="item.tone">{{ item.icon }}</view>
            <view class="pro-benefit-copy">
              <view class="pro-benefit-title">{{ item.title }}</view>
              <view class="pro-benefit-desc">{{ item.desc }}</view>
            </view>
          </view>
        </view>

        <view class="pro-modal-actions">
          <button class="pro-later-btn" @tap="handleCloseProModal">知道了</button>
        </view>
      </view>
    </view>

    <view v-if="showFeedbackModal" class="feedback-modal-mask" @tap="handleCloseFeedbackModal">
      <view class="feedback-modal-sheet" @tap.stop>
        <view class="feedback-modal-handle"></view>
        <button class="feedback-modal-close" @tap="handleCloseFeedbackModal">×</button>
        <view class="feedback-modal-head">
          <view class="feedback-modal-title">帮助与反馈</view>
          <view class="feedback-modal-subtitle">提交题目质量、刷题体验或功能建议</view>
        </view>
        <scroll-view scroll-y class="feedback-modal-scroll">
          <BetaFeedbackForm source-page="profile" />
        </scroll-view>
      </view>
    </view>

    <view v-if="showThemeModal" class="theme-modal-mask" @tap="handleCloseThemeModal">
      <view class="theme-modal-sheet" @tap.stop>
        <view class="theme-modal-handle"></view>
        <button class="theme-modal-close" @tap="handleCloseThemeModal">×</button>
        <view class="theme-modal-head">
          <view class="theme-modal-title">外观主题</view>
          <view class="theme-modal-subtitle">选择一套浅色主题，首页和常用页面会立即更新。</view>
        </view>
        <view class="theme-option-list">
          <view
            v-for="item in themePresets"
            :key="item.key"
            class="theme-option"
            :class="{ active: selectedThemeKey === item.key }"
            @tap="selectTheme(item.key)"
          >
            <view class="theme-preview" :style="{ background: item.panelBg }">
              <view class="theme-preview-dot" :style="{ background: item.primary }"></view>
              <view class="theme-preview-line" :style="{ background: item.primarySoft }"></view>
            </view>
            <view class="theme-option-copy">
              <view class="theme-option-name">{{ item.name }}</view>
              <view class="theme-option-desc">{{ item.desc }}</view>
            </view>
            <view v-if="selectedThemeKey === item.key" class="theme-option-check">✓</view>
          </view>
        </view>
      </view>
    </view>

    <view v-if="showOfficialMessageModal" class="official-modal-mask" @tap="closeOfficialMessages">
      <view class="official-modal-sheet" @tap.stop>
        <view class="official-modal-handle"></view>
        <button class="official-modal-close" @tap="closeOfficialMessages">×</button>
        <view class="official-modal-head">
          <view class="official-modal-title">官方消息</view>
          <view class="official-modal-subtitle">港研通公告、更新与运营通知</view>
        </view>
        <scroll-view scroll-y class="official-modal-scroll">
          <view v-if="officialMessages.length === 0" class="official-empty">暂无官方消息</view>
          <view
            v-for="message in officialMessages"
            :key="message.id"
            class="official-message-card"
            :class="{ unread: !message.read }"
          >
            <view class="official-message-top">
              <view class="official-message-title">{{ message.title }}</view>
              <view v-if="!message.read" class="official-unread-badge">未读</view>
            </view>
            <view class="official-message-date">{{ formatDateTime(message.published_at || message.created_at) }}</view>
            <view class="official-message-content">{{ message.content }}</view>
          </view>
        </scroll-view>
        <button class="official-done-btn" @tap="closeOfficialMessages">我知道了</button>
      </view>
    </view>

    <!-- #ifdef H5 -->
    <IcpFooter :compact="showBottomTab" />
    <!-- #endif -->
    <BottomTabBar v-if="showBottomTab" v-model="activeTab" :items="tabs" />
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { onLoad, onReachBottom, onShow } from '@dcloudio/uni-app'
import BottomTabBar from '../../components/BottomTabBar.vue'
import IcpFooter from '../../components/IcpFooter.vue'
import MistakeList from '../../components/MistakeList.vue'
import ModuleCard from '../../components/ModuleCard.vue'
import SectionCard from '../../components/SectionCard.vue'
import BetaFeedbackForm from '../../components/BetaFeedbackForm.vue'
import MathText from '../../components/MathText.vue'
import { createAiTrainingRequestTask, fetchAiTrainingRecommendation } from '../../api/ai'
import { updateProfile } from '../../api/auth'
import { fetchMembershipStatus } from '../../api/membership'
import { fetchOfficialMessages, markOfficialMessageRead } from '../../api/officialMessages'
import { fetchAbilityReport, fetchLearningSummary, fetchStudyAdvice } from '../../api/reports'
import { fetchWrongQuestionDetail, fetchWrongQuestions, reviewWrongQuestion } from '../../api/wrongQuestions'
import {
  getFullMistakes,
  getHomeDashboard,
  getHomeModules,
  getProfileMock,
  getReportMock
} from '../../mock/appMock'
import { clearAuthSession, getAuthUser, isLoggedIn, updateAuthUser } from '../../utils/auth'
import { EXAM_OPTIONS } from '../../utils/exam'
import { THEME_PRESETS, applyThemeByKey, buildThemeStyle, getStoredThemeKey, getThemePreset } from '../../utils/theme'
import { getUserContactLabel, getUserDisplayName } from '../../utils/userDisplay'

const examOptions = EXAM_OPTIONS
const themePresets = THEME_PRESETS
const initialAuthUser = getAuthUser()
const examCode = ref(uni.getStorageSync('examCode') || initialAuthUser?.exam_target || 'Z001')
const activeTab = ref('home')
const authUser = ref(initialAuthUser)
const authed = ref(isLoggedIn())
const wrongItems = ref([])
const wrongLoading = ref(false)
const wrongError = ref('')
const visibleMistakeCount = ref(15)
const abilityReport = ref(null)
const learningSummary = ref(null)
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
const retestMastered = ref(false)
const retestResults = ref([])
const retestLoading = ref(false)
const retestCompleted = ref(false)
const showTrainingSheet = ref(false)
const showProModal = ref(false)
const showFeedbackModal = ref(false)
const showStudyAdviceDetail = ref(false)
const showThemeModal = ref(false)
const showOfficialMessageModal = ref(false)
const officialMessages = ref([])
const officialUnreadCount = ref(0)
const officialMessagesLoaded = ref(false)
const officialAutoShown = ref(false)
const selectedThemeKey = ref(getStoredThemeKey())
const generatingTraining = ref(false)
const recommendationLoading = ref(false)

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
const tabs = [
  { key: 'home', label: '首页', icon: '⌂' },
  { key: 'profile', label: '我的', icon: '☺' }
]
const showBottomTab = computed(() => !retestMode.value && !['mistakes', 'report'].includes(activeTab.value))
const difficultyOptions = ['基础巩固', '标准提升', '强化突破', '冲刺挑战']
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
const proPreviewItems = [
  'AI 薄弱诊断：把低正确率知识点转成更清晰的错因总结',
  '错题同类加练：围绕错题自动推荐同 submodule 题目',
  '每日训练计划：每天 10-20 题，优先补最低正确率模块',
  '每周提分报告：总结正确率变化、刷题量和下周重点'
]
const proBenefits = [
  {
    icon: '∞',
    title: '无限存储',
    desc: '收藏、错题和练习记录长期保存',
    tone: 'blue'
  },
  {
    icon: 'AI',
    title: 'AI 生题及解析',
    desc: '根据薄弱点智能生成题目与解析',
    tone: 'green'
  },
  {
    icon: '▥',
    title: '完整学习报告',
    desc: '查看更详细的正确率与能力分析',
    tone: 'purple'
  },
  {
    icon: '☆',
    title: '专属训练建议',
    desc: '自动推荐更适合你的训练内容',
    tone: 'orange'
  }
]
const profileBenefits = [
  { label: '无限存储', icon: '∞' },
  { label: '错题本', icon: '', iconSrc: '/static/ui-icons/wrong-book.svg' },
  { label: '学习报告', icon: '', iconSrc: '/static/ui-icons/report.svg' },
  { label: 'AI生题及解析', icon: 'AI' }
]

const isAuthed = computed(() => authed.value)
const isProMember = computed(() => getMembershipStatus(authUser.value) === 'active')
const membershipExpiresAt = computed(() => getMembershipExpiresAt(authUser.value))
const memberCardSubtitle = computed(() => {
  if (!isAuthed.value) {
    return '登录后可查看会员权益与开通状态。'
  }
  if (isProMember.value) {
    return membershipExpiresAt.value
      ? `会员权益使用中，有效期至 ${membershipExpiresAt.value}。`
      : '学习权益使用中，可查看已开放的增强能力。'
  }
  return '当前版本先开放基础学习体验，后续增强能力会随版本逐步开放。'
})
const avatarText = computed(() => (dashboard.value.userName || '游').slice(0, 1))
const profileAvatarText = computed(() => {
  if (!isAuthed.value) return '研'
  return authUser.value?.avatar_url || (getUserDisplayName(authUser.value, profile.value.userName || examCode.value || '游')).slice(0, 1)
})

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
      wrongCount: '--'
    }
  }

  const weeklyAnswers = Number(learningSummary.value?.weekly_answers || 0)
  const totalAnswers = Number(learningSummary.value?.total_answers || 0)
  const accuracy = Number(learningSummary.value?.accuracy || 0)
  const wrongCount = Number(learningSummary.value?.wrong_question_count || wrongItems.value.length || 0)

  return {
    weeklyAnswers: String(weeklyAnswers),
    accuracy: totalAnswers ? `${Math.round(accuracy)}%` : '--',
    wrongCount: String(wrongCount)
  }
})

const moduleCards = computed(() => getHomeModules(examCode.value))
const mockExamThirdSubject = computed(() => (examCode.value === 'Z002' ? '数学基础' : '逻辑推理'))
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
const wrongSummaryCount = computed(() => {
  if (!isAuthed.value) return '0'
  return String(Number(learningSummary.value?.wrong_question_count || wrongItems.value.length || 0))
})
const reportStatus = computed(() => (isAuthed.value && abilityReport.value?.items?.length ? '已生成' : '未生成'))
const practiceTools = computed(() => {
  const proLocked = false
  return [
    { label: '收藏夹', desc: '查看我收藏的重点题目', icon: '', iconSrc: '/static/ui-icons/favorite.svg', tone: 'blue', action: 'favorites' },
    { label: '练习历史', desc: '回顾我的练习记录', icon: '', iconSrc: '/static/ui-icons/history.svg', tone: 'green', action: 'history' },
    {
      label: '错题本',
      desc: `查看与重刷 ${wrongSummaryCount.value} 道错题`,
      icon: '',
      iconSrc: '/static/ui-icons/wrong-book.svg',
      tone: proLocked ? 'locked' : 'blue',
      action: 'mistakes',
      proOnly: true,
      locked: proLocked
    },
    {
      label: '学习报告',
      desc: reportStatus.value === '已生成' ? '查看能力分析与提升建议' : '完成练习后生成报告',
      icon: '',
      iconSrc: '/static/ui-icons/report.svg',
      tone: proLocked ? 'locked' : 'purple',
      action: 'report',
      proOnly: true,
      locked: proLocked
    },
    {
      label: 'AI 专项出题',
      desc: '按知识点生成专项练习',
      icon: 'AI',
      tone: proLocked ? 'locked' : 'green',
      action: 'ai-generator',
      proOnly: true,
      locked: proLocked
    }
  ]
})
const currentTheme = computed(() => getThemePreset(selectedThemeKey.value))
const currentThemeName = computed(() => currentTheme.value.name)
const themeInlineStyle = computed(() => buildThemeStyle(selectedThemeKey.value))
const isAdminUser = computed(() => {
  const role = String(authUser.value?.role || '').toLowerCase()
  const email = String(authUser.value?.email || '').toLowerCase()
  return role === 'admin' || email === '2221073755@qq.com'
})
const serviceTools = computed(() => {
  const items = [
    { label: '外观主题', desc: `当前：${currentThemeName.value}`, icon: '◐', tone: 'blue', action: 'theme' },
    { label: '帮助与反馈', desc: '常见问题与意见反馈', icon: '?', tone: 'orange', action: 'feedback' },
    { label: '关于我们', desc: '了解项目定位与内测说明', icon: 'i', tone: 'blue', action: 'about' }
  ]
  if (isAdminUser.value) {
    items.unshift(
      {
        label: '后台管理',
        desc: '管理用户、反馈和系统消息',
        icon: '',
        iconSrc: '/static/ui-icons/admin.svg',
        tone: 'purple',
        action: 'admin'
      },
      {
        label: '题库管理',
        desc: '查看、筛选和上下架题目',
        icon: '',
        iconSrc: '/static/ui-icons/question-admin.svg',
        tone: 'blue',
        action: 'question-admin'
      }
    )
  }
  return items
})
const filteredMistakes = computed(() =>
  realMistakes.value.filter((item) => {
    if (wrongFilters.value.subject && item.subject !== wrongFilters.value.subject) return false
    if (wrongFilters.value.module && item.module !== wrongFilters.value.module) return false
    if (wrongFilters.value.submodule && item.submodule !== wrongFilters.value.submodule) return false
    return true
  })
)
const fullMistakes = computed(() => (isAuthed.value ? filteredMistakes.value : getFullMistakes()))
const visibleMistakes = computed(() => fullMistakes.value.slice(0, visibleMistakeCount.value))
const hasMoreMistakes = computed(() => visibleMistakeCount.value < fullMistakes.value.length)
const retestCandidateMistakes = computed(() => (isAuthed.value ? filteredMistakes.value : []))
const retestTotal = computed(() => retestItems.value.length)
const retestCorrectCount = computed(() => retestResults.value.filter((item) => item.is_correct).length)
const retestProgressLabel = computed(() => {
  if (!retestTotal.value) return '0 / 0'
  return `${Math.min(retestIndex.value + 1, retestTotal.value)} / ${retestTotal.value}`
})
const retestOptions = computed(() => buildQuestionOptions(retestDetail.value?.question))
const subjectFilters = computed(() => ['', '中华文化', '英语运用', '逻辑推理', '数学基础'])
const moduleFilters = computed(() => buildFilterOptions(realMistakes.value, 'module', { subject: wrongFilters.value.subject }))
const submoduleFilters = computed(() =>
  buildFilterOptions(realMistakes.value, 'submodule', {
    subject: wrongFilters.value.subject,
    module: wrongFilters.value.module
  })
)
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
const mistakeSubtitle = computed(() => {
  if (!isAuthed.value) {
    return '登录后会读取你的真实错题记录；当前展示示例内容。'
  }
  if (realMistakes.value.length) {
    return `已同步 ${realMistakes.value.length} 道真实错题，按最近错误时间排序。`
  }
  return '已连接真实错题接口，做错题后会自动归档到这里。'
})
const report = computed(() => buildReportView())
const dailyPlan = computed(() => report.value.tasks.slice(0, 3).map((item, index) => ({
  ...item,
  title: `今日任务 ${index + 1}：${item.subject} - ${item.submodule || item.module}`,
  desc: `建议先做 10 题。${item.desc}`
})))
const reportOverview = computed(() => {
  const weeklyAnswers = Number(learningSummary.value?.weekly_answers || 0)
  const totalAnswers = Number(learningSummary.value?.total_answers || 0)
  const summaryAccuracy = Number(learningSummary.value?.accuracy || 0)
  const cardAccuracy = subjectReportCards.value.length
    ? Math.round(subjectReportCards.value.reduce((sum, item) => sum + item.accuracy, 0) / subjectReportCards.value.length)
    : 0
  const accuracyValue = totalAnswers ? Math.round(summaryAccuracy) : cardAccuracy

  return {
    weeklyAnswers,
    accuracy: accuracyValue ? `${accuracyValue}%` : '--',
    subtitle: totalAnswers ? '坚持学习，稳步提升！' : '完成练习后，这里会生成你的真实学习概览。',
    trend: totalAnswers ? '真实数据已同步，继续保持刷题节奏 ↗' : '暂无趋势数据，先完成一轮练习吧'
  }
})
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
      return {
        ...item,
        accuracy,
        icon: getSubjectIcon(item.subject),
        status: getSubjectStatus(accuracy),
        tone: getSubjectTone(accuracy),
        tip: item.weakestModule ? `优先关注：${item.weakestModule}` : '当前表现稳定',
        action: '去练习'
      }
    })
    .sort((a, b) => {
      const aIndex = subjectOrder.indexOf(a.subject)
      const bIndex = subjectOrder.indexOf(b.subject)
      return (aIndex === -1 ? 99 : aIndex) - (bIndex === -1 ? 99 : bIndex)
    })
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
  syncTrainingSubject()
  studyAdvice.value = null
  studyAdviceExamCode.value = ''
  if (isAuthed.value) {
    loadAbilityReport()
    loadLearningSummary()
    if (activeTab.value === 'report') {
      loadStudyAdvice({ force: true })
    }
  }
})

watch(activeTab, (value) => {
  if (value !== 'mistakes') {
    selectedWrongDetail.value = null
    if (retestMode.value) {
      exitWrongRetest()
    }
  } else {
    resetMistakeVisibleCount()
  }
  if (value === 'report') {
    loadStudyAdvice()
  }
})

watch(wrongFilters, () => {
  resetMistakeVisibleCount()
}, { deep: true })

watch(wrongItems, () => {
  resetMistakeVisibleCount()
})

onLoad((options) => {
  if (options?.tab === 'profile') {
    activeTab.value = 'profile'
  }
})

onShow(() => {
  authUser.value = getAuthUser()
  authed.value = isLoggedIn()
  refreshMembershipStatus()
  refreshLearningData()
  loadOfficialMessages(true)
})

onReachBottom(() => {
  if (activeTab.value === 'mistakes' && !retestMode.value) {
    loadMoreMistakes()
  }
})

async function changeExam(code) {
  if (!EXAM_OPTIONS.some((item) => item.code === code)) return
  const previousCode = examCode.value
  examCode.value = code
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
  } catch (error) {
    examCode.value = previousCode
    const revertedUser = updateAuthUser({ exam_target: previousCode })
    if (revertedUser) {
      authUser.value = revertedUser
    }
    uni.showToast({ title: '目标版本同步失败，请稍后重试', icon: 'none' })
  }
}

async function refreshMembershipStatus() {
  if (!isLoggedIn()) return
  try {
    const membership = await fetchMembershipStatus()
    const nextUser = updateAuthUser(membership)
    if (nextUser) {
      authUser.value = nextUser
    }
  } catch (error) {
    // Membership tables may not be migrated yet; keep the current cached user state.
  }
}

function goModule(subject) {
  uni.setStorageSync('subject', subject)
  uni.navigateTo({ url: `/pages/practice/index?subject=${encodeURIComponent(subject)}` })
}

function openMockExamIntro() {
  const thirdSubject = mockExamThirdSubject.value
  uni.showModal({
    title: '模拟测试说明',
    content: `本次为 105 分轻量模拟测试，共 55 题：中华文化常识 20 题、英语语言知识 20 题、${thirdSubject} 15 题。不包含中华文化阅读理解和英语阅读理解题型，按标准卷难度组卷：基础 35%、中等 50%、较难 15%，完成后会生成分数与复盘。`,
    confirmText: '开始测试',
    cancelText: '稍后再说',
    success(result) {
      if (!result.confirm) return
      uni.setStorageSync('subject', thirdSubject)
      uni.navigateTo({
        url: `/pages/practice/index?mock_exam=1&exam_code=${encodeURIComponent(examCode.value)}`
      })
    }
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
  if (!isAuthed.value || !isProMember.value || recommendationLoading.value) {
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
  if (!isProMember.value) {
    handleOpenProModal()
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

function handleAccountEntry() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  uni.navigateTo({ url: '/pages/profile/index' })
}

function goLeaderboard() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  uni.navigateTo({ url: '/pages/leaderboard/index' })
}

function goPro() {
  uni.navigateTo({ url: '/pages/pro/index' })
}

async function loadOfficialMessages(autoPopup = false) {
  if (!isAuthed.value) {
    officialMessages.value = []
    officialUnreadCount.value = 0
    officialMessagesLoaded.value = false
    return
  }
  try {
    const response = await fetchOfficialMessages()
    officialMessages.value = response.items || []
    officialUnreadCount.value = Number(response.unread_count || 0)
    officialMessagesLoaded.value = true
    if (autoPopup && !officialAutoShown.value && officialUnreadCount.value > 0) {
      officialAutoShown.value = true
      showOfficialMessageModal.value = true
    }
  } catch (error) {
    officialMessagesLoaded.value = false
  }
}

async function openOfficialMessages() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  if (!officialMessagesLoaded.value) {
    await loadOfficialMessages(false)
  }
  showOfficialMessageModal.value = true
}

async function closeOfficialMessages() {
  showOfficialMessageModal.value = false
  const unreadItems = officialMessages.value.filter((item) => !item.read)
  if (unreadItems.length === 0) return
  officialMessages.value = officialMessages.value.map((item) => ({ ...item, read: true }))
  officialUnreadCount.value = 0
  await Promise.allSettled(unreadItems.map((item) => markOfficialMessageRead(item.id)))
}

function handleProEntry() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  if (isProMember.value) {
    goPro()
    return
  }
  handleOpenProModal()
}

function handleOpenProModal() {
  showProModal.value = true
}

function handleCloseProModal() {
  showProModal.value = false
}

function handleViewProPlans() {
  handleCloseProModal()
  goPro()
}

function logout() {
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
      uni.showToast({ title: '已退出登录', icon: 'none' })
    }
  })
}

function openMistakes() {
  activeTab.value = 'mistakes'
}

function openReport() {
  activeTab.value = 'report'
}

function handleMenu(item) {
  if (!item) return
  if (item.proOnly && !isProMember.value) {
    handleProEntry()
    return
  }
  if (item.action === 'mistakes') {
    openMistakes()
    return
  }
  if (item.action === 'report') {
    openReport()
    return
  }
  if (item.action === 'pro') {
    handleProEntry()
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
  if (item.action === 'ai-generator') {
    openRecommendedTrainingSheet()
    return
  }
  if (item.action === 'feedback') {
    handleOpenFeedbackModal()
    return
  }
  if (item.action === 'theme') {
    handleOpenThemeModal()
    return
  }
  if (item.action === 'admin') {
    uni.navigateTo({ url: '/pages/admin/index' })
    return
  }
  if (item.action === 'question-admin') {
    uni.navigateTo({ url: '/pages/admin/index?tab=questions' })
    return
  }
  if (item.action === 'about') {
    uni.showToast({ title: '当前版本：内测版，专注刷题闭环验证', icon: 'none' })
    return
  }
  showMockToast()
}

function showMockToast() {
  uni.showToast({ title: '完整 AI 诊断后续再接入', icon: 'none' })
}

function handleOpenFeedbackModal() {
  showFeedbackModal.value = true
}

function handleCloseFeedbackModal() {
  showFeedbackModal.value = false
}

function handleOpenThemeModal() {
  showThemeModal.value = true
}

function handleCloseThemeModal() {
  showThemeModal.value = false
}

function selectTheme(key) {
  selectedThemeKey.value = getThemePreset(key).key
  applyThemeByKey(selectedThemeKey.value)
  uni.showToast({ title: '主题已更新', icon: 'none' })
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
  if (activeTab.value === 'report') {
    loadStudyAdvice()
  }
}

async function loadWrongQuestions() {
  if (wrongLoading.value) return

  wrongLoading.value = true
  wrongError.value = ''
  try {
    const response = await fetchWrongQuestions({ limit: 100 })
    wrongItems.value = response?.items || []
  } catch (error) {
    wrongError.value = getSafeError(error, '错题本同步失败，请稍后重试')
  } finally {
    wrongLoading.value = false
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

async function loadStudyAdvice(options = {}) {
  if (!isAuthed.value) {
    studyAdvice.value = null
    studyAdviceError.value = ''
    studyAdviceExamCode.value = ''
    return
  }
  if (studyAdviceLoading.value) return
  if (!options.force && studyAdvice.value && studyAdviceExamCode.value === examCode.value) {
    return
  }

  studyAdviceLoading.value = true
  studyAdviceError.value = ''
  try {
    studyAdvice.value = await fetchStudyAdvice({ exam_code: examCode.value })
    studyAdviceExamCode.value = examCode.value
  } catch (error) {
    studyAdvice.value = null
    studyAdviceExamCode.value = ''
    studyAdviceError.value = getSafeError(error, '学习建议生成失败，已显示本地建议')
  } finally {
    studyAdviceLoading.value = false
  }
}

function openStudyAdviceDetail() {
  if (!isAuthed.value) {
    goLogin()
    return
  }
  showStudyAdviceDetail.value = true
  loadStudyAdvice()
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

function getSubjectIcon(subject) {
  const iconMap = {
    中华文化: '📚',
    英语运用: '📝',
    逻辑推理: '🧠',
    数学基础: '📐'
  }
  return iconMap[subject] || '📊'
}

function getSubjectStatus(accuracy) {
  if (accuracy >= 80) return '表现优秀'
  if (accuracy >= 70) return '表现良好'
  if (accuracy >= 60) return '继续加油'
  return '重点补强'
}

function getSubjectTone(accuracy) {
  if (accuracy >= 70) return 'blue'
  if (accuracy >= 60) return 'orange'
  return 'red'
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

function setWrongFilter(field, value) {
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
  if (!hasMoreMistakes.value) return
  visibleMistakeCount.value += 15
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
  try {
    selectedWrongDetail.value = await fetchWrongQuestionDetail(item.id)
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '错题详情读取失败'), icon: 'none' })
  }
}

function closeWrongDetail() {
  selectedWrongDetail.value = null
  reviewAnswer.value = ''
  reviewResultText.value = ''
  reviewMastered.value = false
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

async function submitWrongReview() {
  if (!selectedWrongDetail.value || !reviewAnswer.value) {
    return
  }

  reviewingWrong.value = true
  try {
    const result = await reviewWrongQuestion({
      question_id: getDetailQuestionId(selectedWrongDetail.value),
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
  retestMastered.value = false
  try {
    retestDetail.value = await fetchWrongQuestionDetail(item.id)
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
      selected_answer: retestAnswer.value,
      used_time: 0,
      exam_code: examCode.value
    })
    const isCorrect = Boolean(result.is_correct)
    const correctAnswer = result.correct_answer || retestDetail.value?.question?.answer || ''
    retestMastered.value = isCorrect
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
  retestMastered.value = false
  retestResults.value = []
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

function getMembershipStatus(user) {
  const status = String(
    user?.membership_status ||
    user?.pro_status ||
    user?.subscription_status ||
    user?.vip_status ||
    uni.getStorageSync('proMembershipStatus') ||
    ''
  ).toLowerCase()
  if (user?.membership_active || user?.is_pro || user?.isPro || user?.pro_member || status === 'active' || status === 'paid') {
    return 'active'
  }
  return 'inactive'
}

function getMembershipExpiresAt(user) {
  const rawValue = user?.membership_expires_at || user?.pro_expires_at || user?.vip_expires_at || ''
  if (!rawValue) return ''
  const date = new Date(rawValue)
  if (Number.isNaN(date.getTime())) {
    return String(rawValue).slice(0, 10)
  }
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
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
  padding: calc(env(safe-area-inset-top) + 16rpx) 22rpx calc(env(safe-area-inset-bottom) + 152rpx);
}

.home-page.no-tab-page {
  padding-bottom: calc(env(safe-area-inset-bottom) + 36rpx);
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

.home-dashboard view,
.home-dashboard text,
.home-dashboard button,
.home-dashboard scroll-view {
  box-sizing: border-box;
}

.home-header,
.brand-line,
.welcome-main {
  display: flex;
  align-items: center;
}

.home-header {
  justify-content: space-between;
  gap: 18rpx;
  padding: 0 2rpx;
}

.brand-line {
  min-width: 0;
  flex: 1;
  gap: 18rpx;
}

.brand-title {
  color: #101828;
  font-size: 42rpx;
  line-height: 1.15;
  font-weight: 900;
  letter-spacing: -1rpx;
  white-space: nowrap;
}

.brand-badge {
  padding: 10rpx 20rpx;
  border-radius: 18rpx;
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #1677ff);
  font-size: 28rpx;
  line-height: 1.2;
  font-weight: 800;
}

.profile-entry {
  width: 78rpx;
  height: 78rpx;
  border-radius: 39rpx;
  background: linear-gradient(180deg, var(--gyt-primary-tint, #f2f5fb), var(--gyt-primary-soft, #e3e9f4));
  color: var(--gyt-primary, #8b95a8);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 32rpx;
  font-weight: 900;
  box-shadow: inset 0 -4rpx 8rpx rgba(20, 31, 66, 0.04);
}

.home-actions {
  display: flex;
  align-items: center;
  gap: 14rpx;
  flex-shrink: 0;
}

.message-bell {
  position: relative;
  width: 72rpx;
  height: 72rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.72);
  color: #344054;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 34rpx;
  line-height: 72rpx;
  box-shadow: 0 10rpx 24rpx rgba(20, 31, 66, 0.06);
}

.message-bell.unread {
  background: var(--gyt-primary-soft, #edf4ff);
  color: var(--gyt-primary, #1677ff);
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
  font-size: 44rpx;
  flex-shrink: 0;
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
  font-size: 118rpx;
  transform: rotate(-10deg);
  z-index: -1;
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
  margin-top: 18rpx;
  padding: 26rpx 28rpx;
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
  gap: 20rpx;
  padding-right: 46rpx;
}

.mock-exam-icon {
  width: 76rpx;
  height: 76rpx;
  border-radius: 24rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26rpx;
  font-weight: 900;
  box-shadow: 0 12rpx 26rpx var(--gyt-primary-shadow);
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
  margin-top: 8rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.45;
}

.mock-exam-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 20rpx;
}

.mock-exam-meta text {
  padding: 8rpx 12rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-tint);
  color: var(--gyt-primary);
  font-size: 20rpx;
  font-weight: 800;
}

.mock-exam-arrow {
  position: absolute;
  right: 28rpx;
  top: 34rpx;
  color: var(--gyt-primary);
  font-size: 44rpx;
  font-weight: 700;
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

.filter-card {
  margin-bottom: 16rpx;
  padding: 8rpx 0 2rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.filter-tip {
  color: #667085;
  font-size: 22rpx;
  line-height: 1.5;
}

.filter-scroll {
  white-space: nowrap;
}

.filter-chip {
  display: inline-flex;
  margin-right: 12rpx;
  padding: 12rpx 18rpx;
  border: 2rpx solid var(--gyt-primary-border);
  border-radius: 999rpx;
  background: var(--gyt-primary-tint);
  color: #476089;
  font-size: 21rpx;
  font-weight: 700;
}

.filter-chip.active {
  border-color: var(--gyt-primary, #2563eb);
  background: var(--gyt-primary-soft, #edf3ff);
  color: var(--gyt-primary, #2563eb);
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

.report-topbar {
  min-height: 68rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.report-top-title {
  flex: 1;
  color: #101828;
  text-align: center;
  font-size: 31rpx;
  line-height: 1.3;
  font-weight: 950;
}

.report-top-spacer {
  width: 74rpx;
  height: 74rpx;
  flex: 0 0 74rpx;
}

.report-overview-card,
.subject-report-card,
.learning-advice-card {
  border: 2rpx solid #e7eefb;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 16rpx 42rpx rgba(25, 48, 89, 0.08);
}

.report-overview-card {
  position: relative;
  overflow: hidden;
  padding: 28rpx 24rpx 22rpx;
  background: var(
    --gyt-panel-bg,
    radial-gradient(circle at 86% 10%, var(--gyt-primary-shadow), transparent 30%),
    linear-gradient(135deg, #ffffff 0%, #eef6ff 100%)
  );
}

.overview-copy {
  position: relative;
  z-index: 1;
}

.overview-title-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.overview-title {
  color: #1f2a44;
  font-size: 28rpx;
  font-weight: 900;
}

.overview-info {
  width: 28rpx;
  height: 28rpx;
  border-radius: 50%;
  border: 2rpx solid #cbd5e1;
  color: #98a2b3;
  text-align: center;
  font-size: 18rpx;
  line-height: 25rpx;
  font-weight: 800;
}

.overview-subtitle {
  margin-top: 12rpx;
  color: #6b778d;
  font-size: 24rpx;
  line-height: 1.5;
  font-weight: 600;
}

.overview-art {
  position: absolute;
  right: 20rpx;
  top: 20rpx;
  width: 106rpx;
  height: 106rpx;
  border-radius: 30rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.72);
  color: var(--gyt-primary, #1677ff);
  font-size: 56rpx;
  transform: rotate(-5deg);
  box-shadow: 0 16rpx 34rpx var(--gyt-primary-shadow, rgba(22, 119, 255, 0.12));
}

.overview-metrics {
  position: relative;
  z-index: 1;
  margin-top: 26rpx;
  padding: 24rpx 10rpx;
  border-radius: 28rpx;
  background: rgba(255, 255, 255, 0.94);
  display: flex;
  box-shadow: 0 14rpx 30rpx rgba(25, 48, 89, 0.07);
}

.overview-metric {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
  border-right: 2rpx solid #e8eef7;
}

.overview-metric:last-child {
  border-right: 0;
}

.metric-icon {
  width: 56rpx;
  height: 56rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--gyt-primary, #1677ff);
  background: var(--gyt-primary-soft, #eef5ff);
  font-size: 28rpx;
  font-weight: 900;
}

.metric-icon.green {
  color: #16a34a;
  background: #eefbf3;
}

.metric-copy {
  min-width: 0;
}

.metric-label {
  color: #8a95a8;
  font-size: 20rpx;
  font-weight: 700;
}

.metric-value {
  margin-top: 4rpx;
  color: var(--gyt-primary, #1677ff);
  font-size: 38rpx;
  line-height: 1;
  font-weight: 950;
}

.metric-value text {
  margin-left: 4rpx;
  font-size: 20rpx;
  font-weight: 800;
}

.overview-trend {
  margin-top: 16rpx;
  color: #16a34a;
  text-align: center;
  font-size: 21rpx;
  font-weight: 800;
}

.subject-report-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.subject-report-card {
  padding: 24rpx;
  display: flex;
  align-items: center;
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
  font-size: 26rpx;
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

.progress-fill.red {
  background: linear-gradient(90deg, #ef4444, #fb7185);
}

.subject-trend {
  margin-top: 12rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.45;
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
  font-size: 25rpx;
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

.smart-tip {
  display: flex;
  align-items: flex-start;
  gap: 16rpx;
  padding: 20rpx;
  border-radius: 20rpx;
  background: var(--gyt-primary-soft, #eef5ff);
}

.smart-tip-icon {
  width: 42rpx;
  height: 42rpx;
  flex: 0 0 42rpx;
  border-radius: 50%;
  background: var(--gyt-primary-gradient, linear-gradient(135deg, #3478f6, #7ca7ff));
  color: #ffffff;
  text-align: center;
  font-size: 24rpx;
  line-height: 42rpx;
  font-weight: 900;
}

.smart-tip-copy {
  flex: 1;
  min-width: 0;
  color: #52627a;
  font-size: 22rpx;
  line-height: 1.55;
  font-weight: 700;
}

.recommend-lines {
  margin-top: 20rpx;
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
  border: 2rpx solid #e1e8f4;
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
  border: 2rpx solid #e1e8f4;
  border-radius: 18rpx;
  background: #f8fafc;
  color: #475467;
  font-size: 25rpx;
  line-height: 76rpx;
  font-weight: 900;
  box-shadow: none;
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
  border: 2rpx solid #e7eefb;
  border-radius: 26rpx;
  background: linear-gradient(180deg, #ffffff 0%, var(--gyt-primary-tint) 100%);
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
  border: 2rpx solid #e1e8f4;
}

.pro-open-btn {
  background: var(--gyt-primary-gradient, linear-gradient(135deg, #3478f6, #4f86ff));
  color: #ffffff;
  box-shadow: 0 16rpx 30rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.22));
}

.feedback-modal-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 84;
  display: flex;
  align-items: flex-end;
  background: rgba(15, 23, 42, 0.36);
}

.feedback-modal-sheet {
  position: relative;
  width: 100%;
  max-height: 88vh;
  padding: 16rpx 36rpx calc(env(safe-area-inset-bottom) + 30rpx);
  border-radius: 48rpx 48rpx 0 0;
  background: #ffffff;
  box-shadow: 0 -18rpx 54rpx rgba(15, 23, 42, 0.16);
  box-sizing: border-box;
}

.feedback-modal-handle {
  width: 74rpx;
  height: 8rpx;
  margin: 0 auto 18rpx;
  border-radius: 999rpx;
  background: #d8deea;
}

.feedback-modal-close {
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

.feedback-modal-head {
  padding: 0 58rpx 18rpx;
  text-align: center;
}

.feedback-modal-title {
  color: #101828;
  font-size: 36rpx;
  line-height: 1.25;
  font-weight: 950;
}

.feedback-modal-subtitle {
  margin-top: 10rpx;
  color: #8a95a8;
  font-size: 23rpx;
  line-height: 1.45;
  font-weight: 650;
}

.feedback-modal-scroll {
  max-height: 70vh;
  padding-bottom: 4rpx;
  box-sizing: border-box;
}

.theme-modal-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 86;
  display: flex;
  align-items: flex-end;
  background: rgba(15, 23, 42, 0.36);
}

.theme-modal-sheet {
  position: relative;
  width: 100%;
  max-height: 86vh;
  padding: 16rpx 34rpx calc(env(safe-area-inset-bottom) + 30rpx);
  border-radius: 48rpx 48rpx 0 0;
  background: #ffffff;
  box-shadow: 0 -18rpx 54rpx rgba(15, 23, 42, 0.16);
  box-sizing: border-box;
}

.theme-modal-handle {
  width: 74rpx;
  height: 8rpx;
  margin: 0 auto 18rpx;
  border-radius: 999rpx;
  background: #d8deea;
}

.theme-modal-close {
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

.theme-modal-head {
  padding: 0 58rpx 18rpx;
  text-align: center;
}

.theme-modal-title {
  color: #101828;
  font-size: 36rpx;
  line-height: 1.25;
  font-weight: 950;
}

.theme-modal-subtitle {
  margin-top: 10rpx;
  color: #8a95a8;
  font-size: 23rpx;
  line-height: 1.45;
  font-weight: 650;
}

.theme-option-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.theme-option {
  min-height: 112rpx;
  padding: 16rpx 18rpx;
  border: 2rpx solid #edf1f7;
  border-radius: 24rpx;
  background: #ffffff;
  display: flex;
  align-items: center;
  gap: 18rpx;
  box-shadow: 0 8rpx 24rpx rgba(25, 48, 89, 0.04);
}

.theme-option.active {
  border-color: var(--gyt-primary, #3478f6);
  background: var(--gyt-primary-tint, #f7fbff);
}

.theme-preview {
  width: 96rpx;
  height: 72rpx;
  flex: 0 0 96rpx;
  border-radius: 22rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.76);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  box-shadow: inset 0 0 0 2rpx rgba(255, 255, 255, 0.45);
}

.theme-preview-dot {
  width: 24rpx;
  height: 24rpx;
  border-radius: 999rpx;
}

.theme-preview-line {
  width: 34rpx;
  height: 12rpx;
  border-radius: 999rpx;
}

.theme-option-copy {
  flex: 1;
  min-width: 0;
}

.theme-option-name {
  color: #172033;
  font-size: 26rpx;
  line-height: 1.35;
  font-weight: 950;
}

.theme-option-desc {
  margin-top: 6rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.4;
  font-weight: 650;
}

.theme-option-check {
  width: 42rpx;
  height: 42rpx;
  flex: 0 0 42rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary, #3478f6);
  color: #ffffff;
  text-align: center;
  font-size: 25rpx;
  line-height: 42rpx;
  font-weight: 950;
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
  border: 0;
  border-radius: 999rpx;
  background: #f3f6fb;
  color: #667085;
  font-size: 40rpx;
  line-height: 60rpx;
  font-weight: 900;
}

.official-modal-head {
  padding: 26rpx 32rpx 22rpx;
  border-bottom: 2rpx solid #eef2f8;
}

.official-modal-title {
  color: #101828;
  font-size: 36rpx;
  font-weight: 950;
  line-height: 1.3;
}

.official-modal-subtitle {
  margin-top: 8rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.4;
  font-weight: 700;
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

.mistake-page-head {
  display: flex;
  align-items: center;
  gap: 18rpx;
  margin: 2rpx auto 22rpx;
  width: 100%;
  max-width: 760rpx;
}

.icon-back-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 72rpx;
  height: 72rpx;
  flex: 0 0 72rpx;
  padding: 0;
  border: 0;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 10rpx 26rpx rgba(20, 31, 66, 0.06);
}

.icon-back-btn::after {
  border: 0;
}

.back-icon {
  width: 30rpx;
  height: 30rpx;
  display: block;
}

.mistake-head-copy {
  flex: 1;
  min-width: 0;
}

.head-title {
  color: #101828;
  font-size: 46rpx;
  line-height: 1.25;
  font-weight: 950;
}

.head-subtitle {
  margin-top: 8rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.45;
}

.retest-entry-btn {
  flex: 0 0 auto;
  min-width: 150rpx;
  min-height: 64rpx;
  padding: 0 22rpx;
  border: 0;
  border-radius: 22rpx;
  background: var(--gyt-primary);
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  box-shadow: 0 14rpx 28rpx var(--gyt-primary-shadow);
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
  background: #ffffff;
  color: #475467;
  border: 2rpx solid var(--gyt-primary-border);
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
  flex: 0 0 54rpx;
  border: 0;
  border-radius: 18rpx;
  background: #f3f6fb;
  color: #667085;
  font-size: 32rpx;
  line-height: 50rpx;
  font-weight: 900;
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
  background: linear-gradient(135deg, var(--gyt-primary-shadow), rgba(128, 90, 213, 0.08));
  border: 2rpx solid rgba(91, 140, 255, 0.28);
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

.profile-top-title {
  padding: 2rpx 0 4rpx;
  color: #101828;
  text-align: center;
  font-size: 30rpx;
  line-height: 1.3;
  font-weight: 900;
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
  background: #ffffff;
  color: var(--gyt-primary, #1677ff);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 900;
  box-shadow: 0 8rpx 20rpx rgba(25, 48, 89, 0.08);
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
  padding: 22rpx 0;
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
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 28rpx;
  font-weight: 900;
}

.menu-icon-img {
  width: 34rpx;
  height: 34rpx;
  display: block;
}

.menu-icon.green {
  background: #eafbf1;
  color: #16a34a;
}

.menu-icon.purple {
  background: #f0edff;
  color: #6d5dfc;
}

.menu-icon.orange {
  background: #fff3e8;
  color: #f97316;
}

.menu-icon.dark {
  background: #eef2f7;
  color: #344054;
}

.menu-icon.locked {
  background: #f2f4f7;
  color: #98a2b3;
}

.menu-copy {
  flex: 1;
  min-width: 0;
}

.menu-title-row {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.menu-title {
  color: #101828;
  font-size: 27rpx;
  line-height: 1.3;
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

.menu-subtitle {
  margin-top: 8rpx;
  color: #8a95a8;
  font-size: 22rpx;
  line-height: 1.35;
  font-weight: 600;
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
</style>
