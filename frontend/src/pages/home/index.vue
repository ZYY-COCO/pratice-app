<template>
  <view
    class="page home-page"
    :class="{
      'no-tab-page': !showBottomTab,
      'circle-glass-page': activeTab === 'circle'
    }"
    :style="pageInlineStyle"
  >
    <template v-if="activeTab === 'home'">
      <view class="home-dashboard">
        <view class="home-header">
          <view class="brand-line">
            <view class="brand-title" aria-label="港研通">
              <image
                class="brand-title-image"
                :src="wordmarkSrc"
                mode="widthFix"
                alt="港研通"
              />
            </view>
            <text v-if="isAuthed" class="brand-badge">{{ examCode }}</text>
          </view>
          <view class="home-actions">
            <button v-if="isAuthed" class="message-bell" :class="{ unread: officialUnreadCount > 0 }" @tap="openOfficialMessages">
              <view class="message-bell-icon" aria-hidden="true"></view>
              <view v-if="officialUnreadCount > 0" class="message-dot"></view>
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

    <template v-else-if="activeTab === 'circle'">
      <view class="circle-dashboard">
        <view v-if="selectedCircleSection === 'overview'" class="circle-overview">
          <swiper
            class="circle-insight-swiper"
            :current="circleInsightIndex"
            :autoplay="true"
            :interval="5000"
            :duration="420"
            circular
            @change="handleCircleInsightChange"
          >
            <swiper-item>
              <view class="circle-trend-card circle-glass-surface">
                <view class="circle-trend-heading">
                  <view class="circle-trend-title">近 7 天刷题人数</view>
                  <view class="circle-trend-peak">
                    <text>峰值 </text>
                    <text class="circle-trend-peak-value">{{ circleTrendPeak }}</text>
                    <text> 人</text>
                  </view>
                </view>
                <view class="circle-trend-chart" aria-label="近 7 天刷题人数统计图">
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
                          :class="{ latest: item.latest }"
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
              <view class="circle-score-card circle-glass-surface">
                <view class="circle-score-heading">
                  <view>
                    <view class="circle-score-title">{{ activeCircleScoreSchool.name }}</view>
                    <view class="circle-score-subtitle">历年分数线</view>
                  </view>
                  <view class="circle-score-total">总分 <text>150</text></view>
                </view>
                <view class="circle-score-chart" :aria-label="`${activeCircleScoreSchool.name}历年分数线`">
                  <view class="circle-score-axis" aria-hidden="true">
                    <text v-for="label in circleScoreAxis" :key="label">{{ label }}</text>
                  </view>
                  <svg class="circle-score-svg" viewBox="0 0 300 112" preserveAspectRatio="none" aria-hidden="true">
                    <line v-for="y in circleScoreGridY" :key="y" x1="30" x2="292" :y1="y" :y2="y" class="circle-score-grid-line" />
                    <polyline :points="circleScoreLinePoints" class="circle-score-line" />
                    <g v-for="(score, index) in activeCircleScoreSchool.scores" :key="circleScoreYears[index]">
                      <circle :cx="circleScoreX[index]" :cy="getCircleScoreY(score)" r="4.5" class="circle-score-point" />
                      <text :x="circleScoreX[index]" :y="getCircleScoreY(score) - 10" class="circle-score-value">{{ score }}</text>
                    </g>
                  </svg>
                  <view class="circle-score-years" aria-hidden="true">
                    <text v-for="year in circleScoreYears" :key="year">{{ year }}</text>
                  </view>
                </view>
              </view>
            </swiper-item>
          </swiper>

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
                <view class="circle-entry-icon-mask" :style="getThemeIconStyle(item.iconSrc)"></view>
              </view>
              <text class="circle-entry-label">{{ item.label }}</text>
              <view class="circle-entry-arrow" aria-hidden="true">›</view>
            </button>
          </view>
        </view>

        <view v-else class="circle-detail-page">
          <view class="circle-detail-header">
            <button class="circle-back-button" aria-label="返回研圈首页" @tap="returnToCircleOverview">
              <image src="/static/ui-icons/back.svg" mode="aspectFit" />
            </button>
            <view class="circle-detail-heading">{{ selectedCircleSectionLabel }}</view>
            <view class="circle-detail-header-spacer"></view>
          </view>

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
                {{ item.label }}
              </button>
            </view>

            <template v-if="selectedCircleCommunityTab">
              <view class="experience-search circle-glass-group">
                <text class="experience-search-icon">⌕</text>
                <input
                  v-model="activeCommunitySearchKeyword"
                  class="experience-search-input"
                  :placeholder="selectedCircleCommunityTab === 'experience' ? '搜索经验贴' : '搜索研友聊'"
                  placeholder-class="experience-search-placeholder"
                  confirm-type="search"
                />
                <button
                  v-if="activeCommunitySearchKeyword"
                  class="experience-search-clear"
                  aria-label="清除搜索"
                  @tap.stop="clearActiveCommunitySearch"
                >
                  <CloseIcon />
                </button>
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

              <view class="community-feed">
                <view
                  v-for="post in filteredActiveCommunityPosts"
                  :key="post.id"
                  class="community-post-card"
                  @tap="openCommunityPost(post)"
                >
                  <view class="community-post-header">
                    <view class="community-avatar" :class="`tone-${post.tone}`">{{ post.avatar }}</view>
                    <view class="community-author-main">
                      <view class="community-author-name">{{ post.author }}</view>
                      <view class="community-author-meta">{{ post.publishTime }}</view>
                    </view>
                    <view class="community-topic">{{ post.category }}</view>
                  </view>

                  <view class="community-post-title">{{ post.title }}</view>
                  <view class="community-post-copy">{{ post.summary }}</view>

                  <view v-if="post.media.length" class="community-media-grid" :class="`count-${post.media.length}`">
                    <view
                      v-for="media in post.media"
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

                  <view v-if="post.commentPreviews.length" class="community-comment-preview-list">
                    <view
                      v-for="comment in post.commentPreviews"
                      :key="comment.id"
                      class="community-comment-preview"
                      @tap.stop="openCommunityComments(post)"
                    >
                      <text class="community-comment-name">{{ comment.author }}：</text>
                      <text class="community-comment-preview-copy">{{ comment.text }}</text>
                    </view>
                  </view>

                  <view class="community-post-footer">
                    <button
                      class="community-post-action"
                      :class="{ active: post.liked, pending: communityLikePostId === post.id }"
                      :aria-label="post.liked ? '取消点赞' : '点赞'"
                      :aria-pressed="post.liked"
                      @tap.stop="toggleCommunityLike(post)"
                    >
                      <image class="community-action-icon" src="/static/ui-icons/circle-like.svg" mode="aspectFit" />
                      <text>{{ post.stats.likes }}</text>
                    </button>
                    <button
                      class="community-post-action"
                      aria-label="查看并评论"
                      @tap.stop="openCommunityComments(post)"
                    >
                      <image class="community-action-icon" src="/static/ui-icons/circle-comment.svg" mode="aspectFit" />
                      <text>{{ post.stats.comments }}</text>
                    </button>
                    <button
                      class="community-post-action"
                      aria-label="查看帖子"
                      @tap.stop="openCommunityPost(post)"
                    >
                      <image class="community-action-icon" src="/static/ui-icons/circle-view.svg" mode="aspectFit" />
                      <text>{{ post.stats.views }}</text>
                    </button>
                  </view>
                </view>

                <view v-if="filteredActiveCommunityPosts.length === 0" class="circle-empty-card">
                  <view class="circle-empty-title">暂无匹配的{{ selectedCircleCommunityTab === 'experience' ? '经验贴' : '交流内容' }}</view>
                  <view class="circle-empty-copy">换个关键词或分类试试。</view>
                </view>
              </view>

              <button
                v-if="!selectedCommunityPost"
                class="community-publish-button"
                aria-label="发布话题"
                @tap="openCommunityPublishPage(selectedCircleCommunityTab)"
              >
                <image src="/static/ui-icons/circle-publish.svg" mode="aspectFit" />
              </button>
            </template>

            <template v-else>
              <view class="experience-search circle-glass-group">
                <text class="experience-search-icon">⌕</text>
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
                  <view class="experience-avatar">{{ post.avatar }}</view>
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
                    <text>{{ post.stats.views }} 阅读</text>
                    <text>{{ post.stats.likes }} 赞</text>
                    <text>{{ post.stats.saves }} 收藏</text>
                  </view>
                </view>
              </view>

              <view v-if="filteredCircleExperiencePosts.length === 0" class="circle-empty-card">
                <view class="circle-empty-title">暂无匹配的经验贴</view>
                <view class="circle-empty-copy">换个关键词或分类试试</view>
              </view>
            </template>
          </view>

          <view v-else-if="selectedCircleSection === 'materials'" class="circle-section">
            <view class="circle-section-head">
              <view>
                <view class="circle-section-title">推荐资料</view>
                <view class="circle-section-subtitle">按科目归档，资料卡片预留网盘链接、提取码和更新记录。</view>
              </view>
              <view class="circle-section-count">{{ filteredCircleMaterials.length }} 份</view>
            </view>

            <scroll-view scroll-x class="material-subject-scroll">
              <view class="material-subject-row circle-glass-group">
                <button
                  v-for="subject in circleMaterialSubjects"
                  :key="subject"
                  class="material-subject-chip"
                  :class="{ active: selectedMaterialSubject === subject }"
                  @tap="selectCircleMaterialSubject(subject)"
                >
                  {{ subject }}
                </button>
              </view>
            </scroll-view>

            <view class="material-subject-card">
              <view>
                <view class="material-subject-title">{{ selectedMaterialSubject }}</view>
                <view class="material-subject-copy">{{ circleMaterialSubjectSummary }}</view>
              </view>
              <view class="material-subject-mark">网盘</view>
            </view>

            <view
              v-for="item in filteredCircleMaterials"
              :key="item.id"
              class="material-card"
            >
              <view class="material-main">
                <view class="material-title-row">
                  <view class="material-title">{{ item.title }}</view>
                  <view class="material-badge">{{ item.level }}</view>
                </view>
                <view class="material-desc">{{ item.desc }}</view>
                <view class="material-tags">
                  <text v-for="tag in item.tags" :key="tag">{{ tag }}</text>
                </view>
                <view class="material-share-line">
                  <text>网盘链接：{{ item.shareUrl }}</text>
                  <text>提取码：{{ item.shareCode }}</text>
                </view>
              </view>
              <button class="material-action" @tap="copyMaterialShare(item)">复制</button>
            </view>
          </view>

          <view v-else class="circle-empty-card">
            <view class="circle-empty-icon">
              <view class="circle-entry-icon-mask" :style="getThemeIconStyle(circlePlannedSection.iconSrc)"></view>
            </view>
            <view class="circle-empty-title">敬请期待</view>
            <view class="circle-empty-copy">{{ circlePlannedSection.label }}正在整理中，后续会在这里开放。</view>
          </view>
        </view>
      </view>
    </template>

    <template v-else-if="activeTab === 'mistakes'">
      <view
        class="mistake-page-head"
        :class="{ 'mistake-list-head': !retestMode }"
        :style="!retestMode ? mistakeHeaderStyle : undefined"
      >
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
      <view v-if="!retestMode" class="mistake-list-head-spacer"></view>

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
        <SectionCard>
          <view v-if="!isAuthed" class="state-box warning">登录后才能查看你的真实错题本。</view>
          <view v-else class="filter-card">
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
    </template>

    <template v-else-if="activeTab === 'report'">
      <view class="report-dashboard">
        <view class="report-topbar" :style="reportHeaderStyle">
          <button class="icon-back-btn" @tap="activeTab = 'profile'">
            <image class="back-icon" src="/static/ui-icons/back.svg" mode="aspectFit" />
          </button>
          <view class="report-top-title">学习报告</view>
          <view class="report-top-spacer"></view>
        </view>
        <view class="report-header-spacer"></view>

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
          <!-- #ifndef MP-WEIXIN -->
          <button v-if="dailyPlan.length" class="report-action-btn" @tap="openRecommendedTrainingSheet">
            开始推荐训练
          </button>
          <!-- #endif -->
        </view>
      </view>
    </template>

    <template v-else>
      <view class="profile-dashboard">
        <view class="profile-top-title">港研通</view>

        <view class="account-card" :class="{ guest: !isAuthed }" @tap="handleAccountEntry">
          <image
            v-if="avatarImageUrl"
            class="account-avatar account-avatar-image"
            :src="avatarImageUrl"
            mode="aspectFill"
            alt="用户头像"
          />
          <view v-else class="account-avatar">{{ profileAvatarText }}</view>
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

        <view class="member-card active">
          <view class="member-copy">
            <view class="member-kicker">免费学习功能 · 已开放</view>
            <view class="member-title">学习工具免费使用</view>
            <view class="member-subtitle">{{ memberCardSubtitle }}</view>
          </view>
          <view class="shield-art active">FREE</view>
          <view class="benefit-row">
            <view v-for="item in profileBenefits" :key="item.label" class="benefit-item">
              <view class="benefit-icon" :class="item.iconClass">
                <!-- #ifdef MP-WEIXIN -->
                <image
                  v-if="item.iconSrc"
                  class="benefit-icon-img"
                  :src="getMpThemeIconSrc(item.iconSrc)"
                  mode="aspectFit"
                />
                <text v-else-if="!item.iconClass">{{ item.icon }}</text>
                <!-- #endif -->
                <!-- #ifndef MP-WEIXIN -->
                <view
                  v-if="item.iconSrc"
                  class="benefit-icon-img theme-icon-mask"
                  :style="getThemeIconStyle(item.iconSrc)"
                />
                <text v-else-if="!item.iconClass">{{ item.icon }}</text>
                <!-- #endif -->
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
                <!-- #ifdef MP-WEIXIN -->
                <image
                  v-if="item.iconSrc"
                  class="menu-icon-img"
                  :src="getMpThemeIconSrc(item.iconSrc)"
                  mode="aspectFit"
                />
                <text v-else-if="!item.iconClass">{{ item.icon }}</text>
                <!-- #endif -->
                <!-- #ifndef MP-WEIXIN -->
                <view
                  v-if="item.iconSrc"
                  class="menu-icon-img theme-icon-mask"
                  :style="getThemeIconStyle(item.iconSrc)"
                />
                <text v-else-if="!item.iconClass">{{ item.icon }}</text>
                <!-- #endif -->
              </view>
              <view class="menu-copy">
                <view class="menu-title-row">
                  <text class="menu-title">{{ item.label }}</text>
                  <text v-if="item.locked" class="pro-lock-badge">登录</text>
                </view>
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
                <!-- #ifdef MP-WEIXIN -->
                <image
                  v-if="item.iconSrc"
                  class="menu-icon-img"
                  :src="getMpThemeIconSrc(item.iconSrc)"
                  mode="aspectFit"
                />
                <text v-else>{{ item.icon }}</text>
                <!-- #endif -->
                <!-- #ifndef MP-WEIXIN -->
                <view
                  v-if="item.iconSrc"
                  class="menu-icon-img theme-icon-mask"
                  :style="getThemeIconStyle(item.iconSrc)"
                />
                <text v-else>{{ item.icon }}</text>
                <!-- #endif -->
              </view>
              <view class="menu-copy">
                <view class="menu-title">{{ item.label }}</view>
              </view>
              <view class="menu-arrow">›</view>
            </view>
          </view>
        </view>

        <view v-if="isAuthed" class="logout-card" @tap="logout">退出登录</view>
      </view>
    </template>

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

    <view v-if="showThemeModal" class="theme-modal-mask" @tap="handleCloseThemeModal">
      <view class="theme-modal-sheet" @tap.stop>
        <view class="theme-modal-handle"></view>
        <button class="theme-modal-close" aria-label="关闭" @tap="handleCloseThemeModal"><CloseIcon /></button>
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
        <button class="official-modal-close" aria-label="关闭" @tap="closeOfficialMessages"><CloseIcon /></button>
        <view class="official-modal-head">
          <view class="official-modal-title">官方消息</view>
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

    <view v-if="selectedCommunityPost" class="community-detail-mask" @tap="closeCommunityPost">
      <view class="community-detail-sheet" @tap.stop>
        <view class="community-detail-handle"></view>
        <button class="community-detail-close" aria-label="关闭帖子详情" @tap="closeCommunityPost"><CloseIcon /></button>
        <view class="community-detail-heading">帖子详情</view>
        <scroll-view scroll-y class="community-detail-scroll">
          <view class="community-detail-author-row">
            <view class="community-avatar" :class="`tone-${selectedCommunityPost.tone}`">{{ selectedCommunityPost.avatar }}</view>
            <view class="community-author-main">
              <view class="community-author-name">{{ selectedCommunityPost.author }}</view>
              <view class="community-author-meta">{{ selectedCommunityPost.publishTime }}</view>
            </view>
            <view class="community-topic">{{ selectedCommunityPost.category }}</view>
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
              :class="{ active: selectedCommunityPost.liked, pending: communityLikePostId === selectedCommunityPost.id }"
              @tap="toggleCommunityLike(selectedCommunityPost)"
            >
              <image src="/static/ui-icons/circle-like.svg" mode="aspectFit" />
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

    <view v-if="selectedCommunityCommentsPost" class="community-comments-mask" @tap="closeCommunityComments">
      <view class="community-comments-sheet" @tap.stop>
        <view class="community-detail-handle"></view>
        <button class="community-detail-close" aria-label="关闭评论" @tap="closeCommunityComments"><CloseIcon /></button>

        <view class="community-comments-toolbar">
          <view class="community-comments-counts">
            <text class="community-comments-count active">评论 {{ selectedCommunityCommentsPost.stats.comments }}</text>
            <text class="community-comments-count">点赞 {{ selectedCommunityCommentsPost.stats.likes }}</text>
          </view>
          <view class="community-comment-sort" aria-label="评论排序">
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
        </view>

        <scroll-view scroll-y class="community-comments-scroll">
          <view v-if="communityCommentsLoading" class="community-comments-empty">正在加载评论</view>
          <view v-else-if="sortedCommunityComments.length === 0" class="community-comments-empty">
            暂无评论，来留下第一条讨论吧。
          </view>
          <view v-else class="community-comments-list">
            <view v-for="comment in sortedCommunityComments" :key="comment.id" class="community-comments-item">
              <view class="community-comments-avatar">{{ comment.avatar }}</view>
              <view class="community-comments-main">
                <view class="community-comments-author">{{ comment.author }}</view>
                <view class="community-comments-copy">{{ comment.content }}</view>
                <view class="community-comments-time">{{ formatCommunityCommentTime(comment.createdAt) }}</view>
              </view>
            </view>
          </view>
        </scroll-view>

        <view class="community-comment-composer community-comments-composer">
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
          <view class="experience-avatar circle-post-avatar">{{ selectedCirclePost.avatar }}</view>
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

    <!-- #ifdef H5 -->
    <IcpFooter
      :compact="showBottomTab"
      :glass="activeTab === 'circle'"
    />
    <!-- #endif -->
    <BottomTabBar
      v-if="showBottomTab"
      v-model="activeTab"
      :items="tabs"
      :glass="activeTab === 'circle'"
      :collapsed="isCircleTabbarCollapsed"
      @expand="expandCircleTabbar"
    />
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { onHide, onLoad, onPageScroll, onReachBottom, onShow } from '@dcloudio/uni-app'
import BottomTabBar from '../../components/BottomTabBar.vue'
import CloseIcon from '../../components/CloseIcon.vue'
import IcpFooter from '../../components/IcpFooter.vue'
import MistakeList from '../../components/MistakeList.vue'
import ModuleCard from '../../components/ModuleCard.vue'
import SectionCard from '../../components/SectionCard.vue'
import MathText from '../../components/MathText.vue'
import { createAiTrainingRequestTask, fetchAiTrainingRecommendation } from '../../api/ai'
import { updateProfile } from '../../api/auth'
import {
  createCommunityComment,
  fetchCommunityPost,
  fetchCommunityPosts,
  registerCommunityPostView,
  toggleCommunityPostLike
} from '../../api/community'
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
import { buildMpPageSafeStyle } from '../../utils/mpSafeLayout'
import { THEME_PRESETS, applyThemeByKey, buildThemeStyle, getStoredThemeKey, getThemePreset } from '../../utils/theme'
import { getUserContactLabel, getUserDisplayName } from '../../utils/userDisplay'

// #ifdef MP-WEIXIN
const wordmarkSrc = '/static/gangyantong-wordmark.png'
// #endif

// #ifndef MP-WEIXIN
const wordmarkSrc = '/static/gangyantong-home-wordmark-4k.png'
// #endif

const examOptions = EXAM_OPTIONS
const themePresets = THEME_PRESETS
const ENABLE_CIRCLE = true
const initialAuthUser = getAuthUser()
const examCode = ref(uni.getStorageSync('examCode') || initialAuthUser?.exam_target || 'Z001')
const activeTab = ref(ENABLE_CIRCLE ? 'circle' : 'home')
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
const retestResults = ref([])
const retestLoading = ref(false)
const retestCompleted = ref(false)
const mistakeHeaderScrollTop = ref(0)
const showTrainingSheet = ref(false)
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
const selectedCircleSection = ref('overview')
const selectedCirclePost = ref(null)
const circleInsightIndex = ref(0)
const circleScoreSchoolIndex = ref(Math.floor(Math.random() * 4))
const selectedMaterialSubject = ref('中华文化')
const selectedExperienceCategory = ref('全部')
const experienceSearchKeyword = ref('')
const selectedCircleCommunityTab = ref('chat')
const selectedCommunityCategory = ref('全部')
const communitySearchKeyword = ref('')
const selectedCommunityPost = ref(null)
const selectedCommunityCommentsPost = ref(null)
const communityComments = ref([])
const communityCommentsLoading = ref(false)
const communityCommentSort = ref('default')
const communityPostsLoading = ref(false)
const communityLikePostId = ref('')
const communityCommentDraft = ref('')
const communityCommentSubmitting = ref(false)
const circleTabCollapsed = ref(false)
const circleLastScrollTop = ref(0)

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
const communityPostsLoadingTypes = new Set()
const tabs = computed(() => {
  const items = [
    {
      key: 'home',
      label: '刷题',
      iconSrc: '/static/ui-icons/tab-home.svg',
      mpIconSrc: getMpThemeIconSrc('/static/ui-icons/tab-home.svg')
    }
  ]

  if (ENABLE_CIRCLE) {
    items.push({
      key: 'circle',
      label: '研圈',
      iconSrc: '/static/ui-icons/tab-circle.svg'
    })
  }

  items.push({
    key: 'profile',
    label: '我的',
    iconSrc: '/static/ui-icons/tab-profile.svg',
    mpIconSrc: getMpThemeIconSrc('/static/ui-icons/tab-profile.svg')
  })

  return items
})
const isCircleDetail = computed(() =>
  activeTab.value === 'circle' && selectedCircleSection.value !== 'overview'
)
const showBottomTab = computed(() =>
  !retestMode.value && !['mistakes', 'report'].includes(activeTab.value) && !isCircleDetail.value
)
const isCircleTabbarCollapsed = computed(() =>
  activeTab.value === 'circle' && selectedCircleSection.value !== 'overview' && circleTabCollapsed.value
)
const difficultyOptions = ['基础巩固', '标准提升', '强化突破', '冲刺挑战']
const circleSections = [
  {
    key: 'community',
    label: '考研圈',
    iconSrc: '/static/ui-icons/tab-circle.svg'
  },
  {
    key: 'scores',
    label: '历年分数线',
    iconSrc: '/static/ui-icons/circle-scores.svg'
  },
  {
    key: 'materials',
    label: '推荐资料',
    iconSrc: '/static/ui-icons/circle-materials.svg'
  },
  {
    key: 'courses',
    label: '精选课程',
    iconSrc: '/static/ui-icons/circle-courses.svg'
  }
]
const circlePracticeTrend = [
  { day: '周一', count: 356 },
  { day: '周二', count: 418 },
  { day: '周三', count: 472 },
  { day: '周四', count: 439 },
  { day: '周五', count: 516 },
  { day: '周六', count: 468 },
  { day: '周日', count: 592, latest: true }
]
const circleScoreSchools = [
  { name: '香港大学', scores: [103, 108, 112] },
  { name: '香港中文大学', scores: [96, 101, 105] },
  { name: '香港科技大学', scores: [98, 104, 106] },
  { name: '香港城市大学', scores: [92, 95, 99] }
]
const circleScoreYears = ['2024', '2025', '2026']
const circleScoreAxis = [150, 100, 50]
const circleScoreGridY = [18, 54, 90]
const circleScoreX = [58, 160, 262]
const activeCircleScoreSchool = computed(() =>
  circleScoreSchools[circleScoreSchoolIndex.value] || circleScoreSchools[0]
)
const circleScoreLinePoints = computed(() =>
  activeCircleScoreSchool.value.scores
    .map((score, index) => `${circleScoreX[index]},${getCircleScoreY(score)}`)
    .join(' ')
)
const circleCommunityTabs = [
  { key: 'chat', label: '研友聊' },
  { key: 'experience', label: '经验贴' }
]
const circleCommunityCategories = ['全部', '备考日常', '择校答疑', '复习打卡', '资料互助']
const circleCommunityPosts = ref([
  {
    id: '0b46a665-7b7d-4e0c-a62c-f42282f4e101',
    category: '备考日常',
    author: '南栀同学',
    avatar: '南',
    publishTime: '18 分钟前',
    tone: 'mint',
    title: 'Z001 三科刚起步，大家一周都怎么排？',
    summary: '我先按固定题量排了第一周，怕节奏太满坚持不下来，想看看大家有没有更稳的安排。',
    media: [
      { kicker: '周一', title: '文化 20 题', copy: '错题当天回看', tone: 'sky' },
      { kicker: '周三', title: '英语 20 题', copy: '短语优先', tone: 'mint' },
      { kicker: '周五', title: '逻辑 15 题', copy: '周末做小结', tone: 'warm' }
    ],
    commentPreviews: [
      { id: 'mock-pace-1', author: '研友小林', text: '我也是先把固定题量跑顺，第二周再慢慢加题。' },
      { id: 'mock-pace-2', author: '橙子同学', text: '可以先把每科放在固定时段，执行起来会更稳。' },
      { id: 'mock-pace-3', author: '阿远', text: '周末留半天复盘，后面加题时不容易乱。' }
    ],
    stats: { likes: 34, comments: 12, views: 186 }
  },
  {
    id: '2fd58d9c-7c70-4d90-9d88-3a261c4847af',
    category: '择校答疑',
    author: '阿澈',
    avatar: '澈',
    publishTime: '46 分钟前',
    tone: 'blue',
    title: '港大和港中文的分数线，应该怎么看？',
    summary: '目前基础一般，想申请文科方向。除了分数线，大家还会优先比较哪些信息？',
    media: [],
    commentPreviews: [
      { id: 'mock-score-1', author: '思远', text: '先看专业和年度要求，再把语言成绩、材料和自己的准备周期一起算进去。' }
    ],
    stats: { likes: 21, comments: 18, views: 153 }
  },
  {
    id: '423377f8-7fcf-4ddb-a34d-6ea7e25504da',
    category: '复习打卡',
    author: '小卷',
    avatar: '卷',
    publishTime: '1 小时前',
    tone: 'warm',
    title: '中华文化索引表打卡第 6 天',
    summary: '今天补了人物、作品和朝代三列，发现做题时定位干扰项比以前快很多。',
    media: [
      { kicker: '今日笔记', title: '人物 × 作品', copy: '补齐 16 个易混点', tone: 'paper' }
    ],
    commentPreviews: [
      { id: 'mock-culture-1', author: '小麦', text: '这个方法很好，我今晚也准备按这个结构补索引。' }
    ],
    stats: { likes: 48, comments: 9, views: 217 }
  },
  {
    id: 'f7cd37cc-bf32-4873-b954-ffa5522d6e0b',
    category: '资料互助',
    author: '知行',
    avatar: '知',
    publishTime: '2 小时前',
    tone: 'violet',
    title: '整理了一份数学基础错题复盘模板',
    summary: '模板按公式条件、代入过程和最后验算拆分，适合把重复错误记得更清楚。',
    media: [],
    commentPreviews: [
      { id: 'mock-math-1', author: 'M 同学', text: '正好需要这个思路，做完题只记答案确实很难复盘。' }
    ],
    stats: { likes: 29, comments: 7, views: 141 }
  }
])
const circleExperienceCategories = ['全部', 'Z001', 'Z002']
const circleExperiencePosts = [
  {
    id: 'exp-z001-pace',
    category: '备考节奏',
    tag: '备考节奏',
    examCode: 'Z001',
    subject: '综合备考',
    title: '三科并行时，先把每天的固定题量跑顺',
    summary: '适合刚开始准备 Z001 的同学，把中华文化、英语运用和逻辑推理拆成可执行的日计划。',
    author: '研友 A',
    authorRole: 'Z001 上岸经验',
    avatar: 'A',
    publishDate: '2026-08-03',
    updatedDate: '2026-08-03',
    readTime: '4 分钟',
    stats: {
      views: 1268,
      likes: 86,
      saves: 42
    },
    points: ['每天先做固定题量', '错题当天复盘', '周末做一次小结'],
    sections: [
      {
        heading: '先固定动作',
        body: '最容易拖慢进度的不是某个知识点，而是每天不知道先做什么。我的做法是把三科拆成固定动作：中华文化 20 题、英语语言知识 20 题、逻辑推理 15 题，先保证不断档。'
      },
      {
        heading: '错题当天处理',
        body: '错题不要堆到周末统一看。当天错的题，至少要把题干关键词、误选原因和正确选项理由写出来。第二天开始前先看昨天的错题，再进入新题。'
      },
      {
        heading: '周末只看两个指标',
        body: '周末复盘只看两件事：哪一科掉分最多，哪一种题型最拖时间。下一周就把这两个点放到每天第一组题里。'
      }
    ]
  },
  {
    id: 'exp-culture-memory',
    category: '中华文化',
    tag: '中华文化',
    examCode: 'COMMON',
    subject: '中华文化',
    title: '中华文化别死背，先按人物、作品、朝代建索引',
    summary: '把文学、历史、艺术和科技常识放进同一张索引表，做题时更容易定位干扰项。',
    author: '研友 B',
    authorRole: '文化常识高分复盘',
    avatar: '文',
    publishDate: '2026-08-02',
    updatedDate: '2026-08-03',
    readTime: '5 分钟',
    stats: {
      views: 982,
      likes: 73,
      saves: 58
    },
    points: ['先归类再背诵', '干扰项找相近领域', '解析只记判断理由'],
    sections: [
      {
        heading: '先把知识点放进位置',
        body: '中华文化题看起来杂，但常见干扰项通常来自相近领域。比如人物和作品、朝代和制度、艺术门类和代表作，经常会互相混淆。'
      },
      {
        heading: '用索引表补全连接',
        body: '我会先建四列：人物、作品、朝代、关键词。刷题遇到新的知识点就补进去，不追求一次背完，但要求每次补充都能和旧知识发生连接。'
      },
      {
        heading: '解析只留判断理由',
        body: '解析不用抄长段材料，只保留判断理由。比如“这部作品属于某朝代”“这个概念对应某学派”，越短越容易复盘。'
      }
    ]
  },
  {
    id: 'exp-math-check',
    category: '数学基础',
    tag: '数学基础',
    examCode: 'Z002',
    subject: '数学基础',
    title: '数学基础的提分点，常常藏在计算检查里',
    summary: '适合 Z002 用户，把极限、导数和积分题拆成公式选择、代入和验算三个动作。',
    author: '研友 C',
    authorRole: 'Z002 数学复盘',
    avatar: '数',
    publishDate: '2026-08-01',
    updatedDate: '2026-08-03',
    readTime: '3 分钟',
    stats: {
      views: 746,
      likes: 51,
      saves: 33
    },
    points: ['先写公式条件', '代入后再化简', '最后检查定义域'],
    sections: [
      {
        heading: '条件比公式更先出现',
        body: '数学基础不是只看会不会套公式。很多失分来自条件没看清，尤其是极限、导数和积分里的定义域、连续性和可导性。'
      },
      {
        heading: '代入前先写公式',
        body: '我的顺序是：先写本题对应公式，再把题目条件代进去，最后才做化简。这样能减少一上来就算偏的情况。'
      },
      {
        heading: '最后检查问法',
        body: '做完一定检查答案有没有违反定义域、端点条件或题干问法。这个步骤很短，但能救回不少分。'
      }
    ]
  },
  {
    id: 'exp-english-language',
    category: '英语运用',
    tag: '英语运用',
    examCode: 'COMMON',
    subject: '英语运用',
    title: '英语语言知识先抓固定搭配，再回头补语法',
    summary: '把词汇、短语和语法分成两条线，先解决选择题里最容易反复错的搭配问题。',
    author: '研友 D',
    authorRole: '英语运用复盘',
    avatar: '英',
    publishDate: '2026-07-31',
    updatedDate: '2026-08-03',
    readTime: '4 分钟',
    stats: {
      views: 689,
      likes: 48,
      saves: 37
    },
    points: ['固定搭配优先', '错题按词性归类', '语法点只记触发条件'],
    sections: [
      {
        heading: '先处理高频短语',
        body: '英语运用的语言知识题，很多时候不是整句都看不懂，而是固定搭配和词义边界没记牢。先把高频短语和动词搭配过一轮，做题速度会明显稳定。'
      },
      {
        heading: '错题按词性归档',
        body: '我会把错题按名词、动词、形容词、副词和介词搭配归类。这样复盘时不是孤立背一个答案，而是知道自己经常在哪类词上犹豫。'
      },
      {
        heading: '语法只抓触发条件',
        body: '语法点不用写很长的定义，重点记触发条件。看到从句、非谓语、虚拟语气的标志，就能更快排除不合适的选项。'
      }
    ]
  },
  {
    id: 'exp-logic-template',
    category: '逻辑推理',
    tag: '逻辑推理',
    examCode: 'Z001',
    subject: '逻辑推理',
    title: '逻辑题别急着选，先把论点和论据圈出来',
    summary: '适合论证类题反复错的同学，用固定拆题模板降低读题压力。',
    author: '研友 E',
    authorRole: '逻辑推理提分记录',
    avatar: '逻',
    publishDate: '2026-07-30',
    updatedDate: '2026-08-03',
    readTime: '4 分钟',
    stats: {
      views: 812,
      likes: 67,
      saves: 49
    },
    points: ['先找论点', '再看论据', '最后判断选项作用'],
    sections: [
      {
        heading: '把题干拆成两层',
        body: '论证题最怕一口气读完后直接看选项。我的做法是先圈论点，再划论据，确认题目是在问加强、削弱、假设还是解释。'
      },
      {
        heading: '选项看作用而不是语气',
        body: '很多选项语气很像正确答案，但它没有真正改变论点和论据之间的关系。判断时要问一句：这个选项到底让结论更稳，还是让结论更不稳。'
      },
      {
        heading: '错题复盘保留结构',
        body: '复盘时不要只写“看错了”。要写清楚原论点、原论据、自己误选的选项作用，以及正确选项为什么更贴合题目问法。'
      }
    ]
  }
]
const circleExperienceSeedPostIds = {
  'exp-z001-pace': '7aa84b22-9b9d-4d28-9ef8-7a09d42b0101',
  'exp-culture-memory': '7aa84b22-9b9d-4d28-9ef8-7a09d42b0102',
  'exp-math-check': '7aa84b22-9b9d-4d28-9ef8-7a09d42b0103',
  'exp-english-language': '7aa84b22-9b9d-4d28-9ef8-7a09d42b0104',
  'exp-logic-template': '7aa84b22-9b9d-4d28-9ef8-7a09d42b0105'
}
const circleExperienceCommunityPosts = ref(
  circleExperiencePosts.map((post, index) => normalizeCommunityPost({
    id: circleExperienceSeedPostIds[post.id],
    postType: 'experience',
    category: post.category,
    author: post.author,
    avatar: post.avatar,
    publishTime: post.publishDate,
    tone: ['mint', 'blue', 'warm', 'violet', 'mint'][index] || 'blue',
    title: post.title,
    summary: post.summary,
    content: [
      post.summary,
      ...post.sections.map((section) => `${section.heading}\n${section.body}`)
    ].join('\n\n'),
    media: [],
    commentPreviews: [{
      id: `${post.id}-preview`,
      author: '研友小林',
      text: `我会先按“${post.points[0]}”来复盘。`
    }],
    stats: {
      likes: post.stats.likes,
      comments: 1,
      views: post.stats.views
    }
  }))
)
const circleMaterialSubjects = ['中华文化', '英语运用', '数学基础', '逻辑推理']
const circleMaterialSummaries = {
  中华文化: '文学、历史、哲学、艺术和古代科技常识资料包。',
  英语运用: '词汇、短语、语法和语用题型的基础资料包。',
  数学基础: '极限、导数、积分和多元函数微分学资料包。',
  逻辑推理: '判断、推理、论证和综合题型资料包。'
}
const circleMaterialResources = [
  {
    id: 'mat-culture-core',
    subject: '中华文化',
    title: '中华文化常识核心索引',
    desc: '按人物、作品、朝代、学派和艺术门类整理，适合刷题前快速过一遍。',
    tags: ['文学', '历史', '艺术'],
    level: '基础',
    shareUrl: '待配置',
    shareCode: '待配置'
  },
  {
    id: 'mat-culture-mistake',
    subject: '中华文化',
    title: '中华文化易混点清单',
    desc: '集中整理相近人物、相近作品和常见朝代误配，适合错题复盘。',
    tags: ['易混点', '复盘'],
    level: '提升',
    shareUrl: '待配置',
    shareCode: '待配置'
  },
  {
    id: 'mat-english-vocab',
    subject: '英语运用',
    title: '英语高频词汇与短语包',
    desc: '覆盖语言知识常见词汇、短语和固定搭配，适合每日短时记忆。',
    tags: ['词汇', '短语'],
    level: '基础',
    shareUrl: '待配置',
    shareCode: '待配置'
  },
  {
    id: 'mat-english-grammar',
    subject: '英语运用',
    title: '英语语法错题归纳',
    desc: '围绕时态、从句、非谓语和虚拟语气整理，适合配合错题本使用。',
    tags: ['语法', '错题'],
    level: '提升',
    shareUrl: '待配置',
    shareCode: '待配置'
  },
  {
    id: 'mat-math-calculus',
    subject: '数学基础',
    title: '微积分公式速查',
    desc: '按一元函数微分学、积分学和多元函数微分学拆分常用公式。',
    tags: ['公式', '微积分'],
    level: '基础',
    shareUrl: '待配置',
    shareCode: '待配置'
  },
  {
    id: 'mat-math-errors',
    subject: '数学基础',
    title: '数学基础常见计算坑',
    desc: '整理极限、导数、积分计算中容易忽略的条件和验算步骤。',
    tags: ['验算', '易错'],
    level: '提升',
    shareUrl: '待配置',
    shareCode: '待配置'
  },
  {
    id: 'mat-logic-judge',
    subject: '逻辑推理',
    title: '逻辑判断关系速记',
    desc: '把充分、必要、逆否、削弱和加强等常见关系做成短表。',
    tags: ['判断', '关系'],
    level: '基础',
    shareUrl: '待配置',
    shareCode: '待配置'
  },
  {
    id: 'mat-logic-argument',
    subject: '逻辑推理',
    title: '论证题型拆解模板',
    desc: '按论点、论据、假设、削弱和加强步骤整理答题路径。',
    tags: ['论证', '模板'],
    level: '提升',
    shareUrl: '待配置',
    shareCode: '待配置'
  }
]
const filteredCircleMaterials = computed(() =>
  circleMaterialResources.filter((item) => item.subject === selectedMaterialSubject.value)
)
const filteredCircleCommunityPosts = computed(() => {
  const keyword = communitySearchKeyword.value.trim().toLowerCase()
  return circleCommunityPosts.value.filter((item) => {
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
const filteredCircleExperiencePosts = computed(() => {
  const keyword = experienceSearchKeyword.value.trim().toLowerCase()
  return circleExperienceCommunityPosts.value.filter((item) => {
    const itemExamCode = getExperienceExamCode(item)
    const matchesExamCode = selectedExperienceCategory.value === '全部'
      || itemExamCode === selectedExperienceCategory.value
      || itemExamCode === 'COMMON'
    if (!matchesExamCode || !keyword) return matchesExamCode
    return [
      item.author,
      item.category,
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
const filteredActiveCommunityPosts = computed(() => (
  selectedCircleCommunityTab.value === 'experience'
    ? filteredCircleExperiencePosts.value
    : filteredCircleCommunityPosts.value
))
const circleTrendPeak = computed(() => Math.max(...circlePracticeTrend.map((item) => item.count)))
const circleTrendScaleMax = computed(() => Math.ceil(circleTrendPeak.value / 100) * 100)
const circleTrendAxis = computed(() => [circleTrendScaleMax.value, Math.round(circleTrendScaleMax.value / 2), 0])
const selectedCircleSectionLabel = computed(() =>
  circleSections.find((item) => item.key === selectedCircleSection.value)?.label || '研圈'
)
const circleMaterialSubjectSummary = computed(() =>
  circleMaterialSummaries[selectedMaterialSubject.value] || '按科目整理资料包。'
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
const profileBenefits = [
  { label: '无限存储', icon: '∞' },
  { label: '错题本', icon: '', iconSrc: '/static/ui-icons/wrong-book.svg' },
  { label: '学习报告', icon: '', iconSrc: '/static/ui-icons/report.svg' },
  // #ifdef MP-WEIXIN
  { label: '练习历史', icon: '', iconSrc: '/static/ui-icons/history.svg' }
  // #endif
  // #ifndef MP-WEIXIN
  { label: 'AI生题及解析', icon: 'AI' }
  // #endif
]

const isAuthed = computed(() => authed.value)
const memberCardSubtitle = computed(() => {
  if (!isAuthed.value) {
    // #ifdef MP-WEIXIN
    return '登录后即可免费使用刷题记录、错题本、练习历史和学习报告。'
    // #endif
    // #ifndef MP-WEIXIN
    return '登录后即可免费使用刷题记录、错题本、学习报告和 AI 生题功能。'
    // #endif
  }
  return '当前版本所有学习功能均免费开放，不提供付费购买、订阅或外部支付入口。'
})
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
    { label: '收藏夹', desc: '查看我收藏的重点题目', icon: '', iconSrc: '/static/ui-icons/favorite.svg', tone: 'blue', action: 'favorites' },
    { label: '练习历史', desc: '回顾我的练习记录', icon: '', iconSrc: '/static/ui-icons/history.svg', tone: 'green', action: 'history' },
    {
      label: '错题本',
      desc: `查看与重刷 ${wrongSummaryCount.value} 道错题`,
      icon: '',
      iconSrc: '/static/ui-icons/wrong-book.svg',
      tone: proLocked ? 'locked' : 'blue',
      action: 'mistakes',
      locked: proLocked
    },
    {
      label: '学习报告',
      desc: reportStatus.value === '已生成' ? '查看能力分析与提升建议' : '完成练习后生成报告',
      icon: '',
      iconSrc: '/static/ui-icons/report.svg',
      tone: proLocked ? 'locked' : 'purple',
      action: 'report',
      locked: proLocked
    }
  ]
  // #ifndef MP-WEIXIN
  items.push({
    label: 'AI 专项出题',
    desc: '按知识点生成专项练习',
    icon: 'AI',
    tone: proLocked ? 'locked' : 'green',
    action: 'ai-generator',
    locked: proLocked
  })
  // #endif
  return items
})
const currentTheme = computed(() => getThemePreset(selectedThemeKey.value))
const currentThemeName = computed(() => currentTheme.value.name)
const themeInlineStyle = computed(() => buildThemeStyle(selectedThemeKey.value))
const mpLayoutStyle = ref('')
const pageInlineStyle = computed(() => [themeInlineStyle.value, mpLayoutStyle.value].filter(Boolean).join(';'))
const mistakeHeaderStyle = computed(() => {
  const progress = Math.min(1, Math.max(0, mistakeHeaderScrollTop.value / 220))
  return {
    '--mistake-header-opacity': String(0.2 + progress * 0.78),
    '--mistake-header-shadow-opacity': String(progress * 0.11)
  }
})
const reportHeaderStyle = computed(() => {
  const progress = Math.min(1, Math.max(0, mistakeHeaderScrollTop.value / 220))
  return {
    '--report-header-opacity': String(0.2 + progress * 0.78),
    '--report-header-shadow-opacity': String(progress * 0.11)
  }
})

// #ifdef MP-WEIXIN
function syncMpSafeLayout() {
  mpLayoutStyle.value = buildMpPageSafeStyle()
}
// #endif

const getMpThemeIconSrc = (iconSrc) => {
  const filename = String(iconSrc || '').split('/').pop().replace(/\.svg$/i, '.png')
  return `/static/mp-weixin/theme-icons/${selectedThemeKey.value}/${filename}`
}
const getThemeIconStyle = (iconSrc) => ({
  WebkitMaskImage: `url("${iconSrc}")`,
  maskImage: `url("${iconSrc}")`
})
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
      label: '外观主题',
      desc: `当前：${currentThemeName.value}`,
      icon: '',
      iconSrc: '/static/ui-icons/theme.svg',
      tone: 'blue',
      action: 'theme'
    },
    {
      label: '关于我们',
      desc: '帮助反馈、隐私政策与支持信息',
      icon: '',
      iconSrc: '/static/ui-icons/about.svg',
      tone: 'blue',
      action: 'about'
    }
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
  examMistakes.value.filter((item) => {
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
const subjectFilters = computed(() => ['', ...activeExamSubjects.value])
const moduleFilters = computed(() => buildFilterOptions(examMistakes.value, 'module', { subject: wrongFilters.value.subject }))
const submoduleFilters = computed(() =>
  buildFilterOptions(examMistakes.value, 'submodule', {
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
const mistakeSubtitle = computed(() => `已同步 ${examMistakes.value.length} 道错题`)
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
    if (activeTab.value === 'report') {
      loadStudyAdvice({ force: true })
    }
  }
})

watch(activeTab, (value) => {
  resetCircleTabbar()
  if (value === 'circle' && !ENABLE_CIRCLE) {
    activeTab.value = 'home'
    return
  }
  if (value === 'circle') {
    selectedCircleSection.value = 'overview'
    selectedCirclePost.value = null
    closeCommunityPost()
  }
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
  if (value !== 'circle') {
    selectedCirclePost.value = null
    closeCommunityPost()
  }
})

watch(wrongFilters, () => {
  resetMistakeVisibleCount()
}, { deep: true })

watch(wrongItems, () => {
  resetMistakeVisibleCount()
})

onLoad((options) => {
  // #ifdef MP-WEIXIN
  syncMpSafeLayout()
  // #endif
  if (options?.tab === 'circle' && ENABLE_CIRCLE) {
    activeTab.value = 'circle'
    return
  }
  if (options?.tab === 'home') {
    activeTab.value = 'home'
    return
  }
  if (options?.tab === 'profile') {
    activeTab.value = 'profile'
  }
})

onShow(() => {
  // #ifdef MP-WEIXIN
  syncMpSafeLayout()
  // #endif
  authUser.value = getAuthUser()
  authed.value = isLoggedIn()
  refreshLearningData()
  loadOfficialMessages(true)
  if (activeTab.value === 'circle' && selectedCircleSection.value === 'community') {
    loadCircleCommunityPosts(selectedCircleCommunityTab.value)
  }
})

onHide(() => {
  clearCommunityViewTimer()
})

onPageScroll(({ scrollTop }) => {
  const nextScrollTop = Number(scrollTop) || 0
  mistakeHeaderScrollTop.value = nextScrollTop
  updateCircleTabbarOnScroll(nextScrollTop)
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

function openCircleSection(key) {
  if (!circleSections.some((item) => item.key === key)) return
  resetCircleTabbar()
  selectedCircleSection.value = key
  selectedCirclePost.value = null
  closeCommunityPost()
  if (key === 'community') {
    selectedCircleCommunityTab.value = 'chat'
    selectedCommunityCategory.value = '全部'
    communitySearchKeyword.value = ''
    loadCircleCommunityPosts('chat')
  }
}

function returnToCircleOverview() {
  resetCircleTabbar()
  selectedCircleSection.value = 'overview'
  selectedCirclePost.value = null
  closeCommunityPost()
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
  const scaleMax = Math.max(1, Number(circleTrendScaleMax.value) || 1)
  const ratio = (Number(count) || 0) / scaleMax
  return `${Math.max(7, Math.round(ratio * 100))}%`
}

function getCircleScoreY(score) {
  const safeScore = Math.min(150, Math.max(50, Number(score) || 50))
  return 18 + ((150 - safeScore) / 100) * 72
}

function rotateCircleScoreSchool() {
  if (circleScoreSchools.length < 2) return
  let nextIndex = circleScoreSchoolIndex.value
  while (nextIndex === circleScoreSchoolIndex.value) {
    nextIndex = Math.floor(Math.random() * circleScoreSchools.length)
  }
  circleScoreSchoolIndex.value = nextIndex
}

function handleCircleInsightChange(event) {
  const nextIndex = Number(event?.detail?.current)
  if (!Number.isInteger(nextIndex) || nextIndex === circleInsightIndex.value) return
  circleInsightIndex.value = nextIndex
  if (nextIndex === 1) {
    rotateCircleScoreSchool()
  }
}

function selectCircleInsight(index) {
  if (index !== 0 && index !== 1) return
  if (circleInsightIndex.value === index) return
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
  selectedExperienceCategory.value = category
  selectedCirclePost.value = null
}

function clearExperienceSearch() {
  experienceSearchKeyword.value = ''
}

function clearCommunitySearch() {
  communitySearchKeyword.value = ''
}

function clearActiveCommunitySearch() {
  if (selectedCircleCommunityTab.value === 'experience') {
    clearExperienceSearch()
    return
  }
  clearCommunitySearch()
}

function getExperienceExamCode(post = {}) {
  const explicitCode = String(post.examCode || post.exam_code || '').toUpperCase()
  if (['Z001', 'Z002', 'COMMON'].includes(explicitCode)) return explicitCode

  const category = String(post.category || '')
  const text = `${post.title || ''} ${post.summary || ''}`.toUpperCase()
  if (category === '数学基础' || text.includes('Z002')) return 'Z002'
  if (category === '逻辑推理' || category === '备考节奏' || text.includes('Z001')) return 'Z001'
  return 'COMMON'
}

function normalizeCommunityPost(post = {}) {
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

  return {
    ...post,
    id: String(post.id || ''),
    postType: post.postType || post.post_type || 'chat',
    examCode: getExperienceExamCode(post),
    category: post.category || '备考日常',
    author: post.author || '研友',
    avatar: post.avatar || '研',
    publishTime: post.publishTime || post.publish_time || '刚刚',
    tone: post.tone || 'blue',
    title: post.title || '',
    summary: post.summary || post.content || '',
    content: post.content || post.summary || '',
    media: Array.isArray(post.media) ? post.media.slice(0, 9) : [],
    commentPreviews,
    commentPreview: commentPreviews[0] || null,
    liked: Boolean(post.liked || post.is_liked),
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
    content: comment.content || '',
    createdAt: comment.createdAt || comment.created_at || new Date().toISOString(),
    isMine: Boolean(comment.isMine || comment.is_mine)
  }
}

function patchCommunityPost(postId, patch) {
  if (!postId) return
  const applyPatch = (post) => ({
    ...post,
    ...patch,
    stats: {
      ...post.stats,
      ...(patch.stats || {})
    }
  })
  circleCommunityPosts.value = circleCommunityPosts.value.map((post) => (
    post.id === postId ? applyPatch(post) : post
  ))
  circleExperienceCommunityPosts.value = circleExperienceCommunityPosts.value.map((post) => (
    post.id === postId ? applyPatch(post) : post
  ))
  if (selectedCommunityPost.value?.id === postId) {
    selectedCommunityPost.value = applyPatch(selectedCommunityPost.value)
  }
  if (selectedCommunityCommentsPost.value?.id === postId) {
    selectedCommunityCommentsPost.value = applyPatch(selectedCommunityCommentsPost.value)
  }
}

async function loadCircleCommunityPosts(postType = 'chat') {
  const normalizedPostType = postType === 'experience' ? 'experience' : 'chat'
  if (communityPostsLoadingTypes.has(normalizedPostType)) return
  communityPostsLoadingTypes.add(normalizedPostType)
  communityPostsLoading.value = true
  try {
    const response = await fetchCommunityPosts({ limit: 50, post_type: normalizedPostType })
    if (Array.isArray(response?.items)) {
      const posts = response.items.map((post) => normalizeCommunityPost(post))
      if (normalizedPostType === 'experience') {
        circleExperienceCommunityPosts.value = posts
      } else {
        circleCommunityPosts.value = posts
      }
    }
  } catch (error) {
    // 保留本地示例内容，避免数据库迁移完成前的界面出现空白。
  } finally {
    communityPostsLoadingTypes.delete(normalizedPostType)
    communityPostsLoading.value = communityPostsLoadingTypes.size > 0
  }
}

async function openCommunityPost(post) {
  const initialPost = normalizeCommunityPost(post)
  if (!initialPost.id) return
  clearCommunityViewTimer()
  selectedCommunityPost.value = initialPost
  scheduleCommunityView(initialPost.id)

  try {
    const response = await fetchCommunityPost(initialPost.id)
    if (response?.post && selectedCommunityPost.value?.id === initialPost.id) {
      const remotePost = normalizeCommunityPost(response.post)
      selectedCommunityPost.value = remotePost
      patchCommunityPost(initialPost.id, remotePost)
    }
  } catch (error) {
    // 详情的本地预览仍可阅读；互动请求会明确提示服务状态。
  }
}

function closeCommunityPost() {
  clearCommunityViewTimer()
  closeCommunityComments()
  selectedCommunityPost.value = null
}

async function openCommunityComments(post) {
  const initialPost = normalizeCommunityPost(post)
  if (!initialPost.id) return

  selectedCommunityCommentsPost.value = initialPost
  communityCommentSort.value = 'default'
  communityCommentDraft.value = ''
  communityComments.value = initialPost.commentPreviews.map((comment) => normalizeCommunityComment({
    id: comment.id,
    author: comment.author,
    avatar: comment.author.slice(0, 1),
    content: comment.text,
    createdAt: ''
  }))
  communityCommentsLoading.value = true

  try {
    const response = await fetchCommunityPost(initialPost.id)
    if (response?.post && selectedCommunityCommentsPost.value?.id === initialPost.id) {
      const remotePost = normalizeCommunityPost(response.post)
      selectedCommunityCommentsPost.value = remotePost
      patchCommunityPost(initialPost.id, remotePost)
      communityComments.value = Array.isArray(response.comments)
        ? response.comments.map((comment) => normalizeCommunityComment(comment))
        : []
    }
  } catch (error) {
    // 接口暂不可用时保留帖子卡片带入的本地评论预览。
  } finally {
    if (selectedCommunityCommentsPost.value?.id === initialPost.id) {
      communityCommentsLoading.value = false
    }
  }
}

function closeCommunityComments() {
  selectedCommunityCommentsPost.value = null
  communityComments.value = []
  communityCommentsLoading.value = false
  communityCommentSort.value = 'default'
  communityCommentDraft.value = ''
}

function clearCommunityViewTimer() {
  if (!communityViewTimerId) return
  clearTimeout(communityViewTimerId)
  communityViewTimerId = null
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

async function toggleCommunityLike(post) {
  if (!post?.id || communityLikePostId.value === post.id) return
  if (!isAuthed.value) {
    goLogin()
    return
  }

  communityLikePostId.value = post.id
  try {
    const response = await toggleCommunityPostLike(post.id)
    patchCommunityPost(post.id, {
      liked: Boolean(response?.is_liked),
      stats: { likes: Number(response?.like_count || 0) }
    })
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '点赞失败，请稍后重试'), icon: 'none' })
  } finally {
    communityLikePostId.value = ''
  }
}

async function submitCommunityComment() {
  const post = selectedCommunityCommentsPost.value
  const content = communityCommentDraft.value.trim()
  if (!post?.id || !content || communityCommentSubmitting.value) return
  if (!isAuthed.value) {
    goLogin()
    return
  }

  communityCommentSubmitting.value = true
  try {
    const response = await createCommunityComment(post.id, { content })
    if (response?.comment) {
      const comment = normalizeCommunityComment(response.comment)
      const commentPreviews = [
        {
          id: comment.id,
          author: comment.author,
          text: comment.content
        },
        ...post.commentPreviews.filter((item) => item.id !== comment.id)
      ].slice(0, 3)
      communityComments.value.push(comment)
      patchCommunityPost(post.id, {
        commentPreviews,
        commentPreview: commentPreviews[0] || null,
        stats: { comments: Number(response.comment_count || 0) }
      })
      communityCommentDraft.value = ''
      uni.showToast({ title: '评论已发布', icon: 'success' })
    }
  } catch (error) {
    uni.showToast({ title: getSafeError(error, '评论发布失败，请稍后重试'), icon: 'none' })
  } finally {
    communityCommentSubmitting.value = false
  }
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

function openCommunityPublishPage(postType = selectedCircleCommunityTab.value) {
  const normalizedPostType = postType === 'experience' ? 'experience' : 'chat'
  uni.navigateTo({ url: `/pages/circle/publish?type=${normalizedPostType}` })
}

function selectCircleCommunityTab(tab) {
  if (!circleCommunityTabs.some((item) => item.key === tab)) return
  selectedCircleCommunityTab.value = tab
  selectedCirclePost.value = null
  closeCommunityPost()
  loadCircleCommunityPosts(tab)
  resetCircleTabbar()
}

function selectCircleCommunityCategory(category) {
  if (!circleCommunityCategories.includes(category)) return
  selectedCommunityCategory.value = category
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

function selectCircleMaterialSubject(subject) {
  if (!circleMaterialSubjects.includes(subject)) return
  selectedMaterialSubject.value = subject
}

function copyMaterialShare(item) {
  if (!item || !item.shareUrl || item.shareUrl === '待配置') {
    uni.showToast({ title: '资料网盘链接待配置', icon: 'none' })
    return
  }

  const shareText = `${item.title}\n网盘链接：${item.shareUrl}\n提取码：${item.shareCode || '无'}`
  uni.setClipboardData({
    data: shareText,
    success() {
      uni.showToast({ title: '已复制网盘信息', icon: 'none' })
    }
  })
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
      uni.reLaunch({ url: '/pages/login/index' })
    }
  })
}

function openProfileTab() {
  activeTab.value = 'profile'
  // #ifdef MP-WEIXIN
  uni.pageScrollTo({ scrollTop: 0, duration: 0 })
  // #endif
}

function openMistakes() {
  activeTab.value = 'mistakes'
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
  if (item.action === 'ai-generator') {
    openRecommendedTrainingSheet()
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
    uni.navigateTo({ url: '/pages/about/index' })
    return
  }
  showMockToast()
}

function showMockToast() {
  uni.showToast({ title: '完整 AI 诊断后续再接入', icon: 'none' })
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
  padding: calc(env(safe-area-inset-top) + 16rpx) 22rpx calc(env(safe-area-inset-bottom) + 152rpx);
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
  --circle-glass-surface: rgba(250, 253, 252, 0.66);
  --circle-glass-surface-strong: rgba(249, 252, 251, 0.82);
  --circle-glass-border: rgba(255, 255, 255, 0.78);
  --circle-glass-blur: 20px;
  --circle-glass-press: 0.98;
  --circle-insight-slide-gap: 8px;
  --circle-insight-slide-offset: 4px;
  --circle-tab-bg: rgba(247, 250, 249, 0.58);
  --circle-tab-shadow: 0 14px 34px rgba(30, 55, 56, 0.16);
  --circle-font: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", "Helvetica Neue", Arial, sans-serif;
  position: relative;
  isolation: isolate;
  overflow-x: clip;
  padding: calc(env(safe-area-inset-top) + 16px) 16px calc(env(safe-area-inset-bottom) + 92px);
  background: #416d6e;
  color: var(--circle-text);
  font-family: var(--circle-font);
}

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
  min-height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 92px);
  min-height: calc(100dvh - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 92px);
}

.circle-trend-card {
  min-height: 176px;
  padding: 16px 16px 14px;
  border: 1px solid var(--circle-card-border, rgba(255, 255, 255, 0.62));
  border-radius: var(--circle-radius-card, 24px);
  background: var(--circle-card, rgba(255, 255, 255, 0.8));
  box-shadow: var(--circle-shadow, 0 10px 28px rgba(45, 66, 93, 0.1));
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
  box-shadow: var(--circle-shadow, 0 10px 28px rgba(45, 66, 93, 0.1));
  text-align: left;
}

.circle-entry:nth-child(1) {
  --circle-entry-bg: rgba(255, 255, 255, 0.82);
  --circle-entry-icon-bg: rgba(91, 143, 223, 0.12);
  --circle-entry-icon-color: #5b8fdf;
}

.circle-entry:nth-child(2) {
  --circle-entry-bg: rgba(248, 251, 255, 0.82);
  --circle-entry-icon-bg: rgba(115, 150, 204, 0.12);
  --circle-entry-icon-color: #6e91bf;
}

.circle-entry:nth-child(3) {
  --circle-entry-bg: rgba(250, 253, 253, 0.82);
  --circle-entry-icon-bg: var(--circle-mint-soft, rgba(116, 189, 173, 0.14));
  --circle-entry-icon-color: #69aa9c;
}

.circle-entry:nth-child(4) {
  --circle-entry-bg: rgba(250, 252, 255, 0.82);
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

.circle-entry-icon-mask {
  width: 24px;
  height: 24px;
  background: currentColor;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-size: contain;
  mask-size: contain;
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
  font-family: var(--circle-font, Arial, sans-serif);
  font-size: 20px;
  line-height: 1;
  font-weight: 400;
  flex-shrink: 0;
}

.circle-glass-page .circle-trend-card {
  -webkit-backdrop-filter: blur(18px) saturate(112%);
  backdrop-filter: blur(18px) saturate(112%);
  animation: circle-overview-enter 360ms ease-out both;
}

.circle-glass-page .circle-entry {
  -webkit-backdrop-filter: blur(16px) saturate(108%);
  backdrop-filter: blur(16px) saturate(108%);
  transition: transform 180ms ease, box-shadow 180ms ease;
  animation: circle-overview-enter 400ms ease-out both;
}

.circle-glass-page .circle-entry:active {
  transform: scale(0.98);
}

.circle-glass-page .circle-entry:nth-child(1) {
  animation-delay: 60ms;
}

.circle-glass-page .circle-entry:nth-child(2) {
  animation-delay: 110ms;
}

.circle-glass-page .circle-entry:nth-child(3) {
  animation-delay: 160ms;
}

.circle-glass-page .circle-entry:nth-child(4) {
  animation-delay: 210ms;
}

@keyframes circle-overview-enter {
  from {
    opacity: 0;
    transform: translateY(12px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
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
  height: calc(100vh - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 108px);
  height: calc(100dvh - env(safe-area-inset-top) - env(safe-area-inset-bottom) - 108px);
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
  box-shadow: 0 18px 40px rgba(30, 55, 56, 0.1);
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
  box-shadow: 0 10px 24px rgba(30, 55, 56, 0.075);
  -webkit-backdrop-filter: blur(var(--circle-glass-blur, 20px)) saturate(120%);
  backdrop-filter: blur(var(--circle-glass-blur, 20px)) saturate(120%);
  transition: transform 180ms ease, box-shadow 180ms ease, background-color 180ms ease;
}

.circle-glass-page .circle-entry:nth-child(1) {
  --circle-entry-bg: rgba(248, 253, 251, 0.68);
  --circle-entry-icon-bg: #e5f0ed;
  --circle-entry-icon-color: #16786f;
}

.circle-glass-page .circle-entry:nth-child(2) {
  --circle-entry-bg: rgba(249, 251, 253, 0.68);
  --circle-entry-icon-bg: #e8eef4;
  --circle-entry-icon-color: #55738f;
}

.circle-glass-page .circle-entry:nth-child(3) {
  --circle-entry-bg: rgba(253, 251, 247, 0.68);
  --circle-entry-icon-bg: #f3eadc;
  --circle-entry-icon-color: #a56c3b;
}

.circle-glass-page .circle-entry:nth-child(4) {
  --circle-entry-bg: rgba(250, 250, 253, 0.68);
  --circle-entry-icon-bg: #ece9f3;
  --circle-entry-icon-color: #756491;
}

.circle-glass-page .circle-entry-icon {
  width: 52px;
  height: 52px;
  border-radius: 18px;
}

.circle-glass-page .circle-entry-icon-mask {
  width: 23px;
  height: 23px;
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
  background: rgba(255, 255, 255, 0.58);
  color: #536967;
  font-size: 25px;
  -webkit-backdrop-filter: blur(14px) saturate(118%);
  backdrop-filter: blur(14px) saturate(118%);
}

.circle-glass-page .circle-entry:active {
  transform: scale(var(--circle-glass-press, 0.98));
  box-shadow: 0 6px 16px rgba(30, 55, 56, 0.075);
}

.circle-score-card {
  padding: 18px 18px 14px;
  border: 1px solid var(--circle-glass-border, rgba(255, 255, 255, 0.78));
  border-radius: 30px;
  background: var(--circle-glass-surface-strong, rgba(249, 252, 251, 0.82));
  box-shadow: 0 18px 40px rgba(30, 55, 56, 0.1);
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

.circle-score-title {
  color: #1c2423;
  font-size: 24px;
  line-height: 1.18;
  font-weight: 650;
  white-space: nowrap;
}

.circle-score-subtitle {
  margin-top: 3px;
  color: #657473;
  font-size: 12px;
  line-height: 1.2;
  font-weight: 500;
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
  color: #16786f;
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

.circle-score-svg {
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
  stroke: #16786f;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 3;
}

.circle-score-point {
  fill: #ffffff;
  stroke: #16786f;
  stroke-width: 3;
}

.circle-score-value {
  fill: #314240;
  font-size: 12px;
  font-weight: 700;
  text-anchor: middle;
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

@media (hover: hover) {
  .circle-glass-page .circle-entry:hover {
    background: rgba(255, 255, 255, 0.76);
    box-shadow: 0 14px 28px rgba(30, 55, 56, 0.11);
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
  min-height: 72rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.circle-back-button,
.circle-detail-header-spacer {
  width: 64rpx;
  height: 64rpx;
  flex-shrink: 0;
}

.circle-back-button {
  margin: 0;
  padding: 0;
  border: 2rpx solid #e8edf5;
  border-radius: 20rpx;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
}

.circle-back-button::after {
  border: 0;
}

.circle-back-button image {
  width: 30rpx;
  height: 30rpx;
}

.circle-detail-heading {
  color: #172033;
  font-size: 32rpx;
  line-height: 1.2;
  font-weight: 900;
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
  color: #7c8c8c;
  font-size: 32rpx;
  line-height: 1;
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
  gap: 16rpx;
  padding-bottom: 24rpx;
}

.circle-community-tabs {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8rpx;
  padding: 8rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.74);
  border-radius: 24rpx;
  background: rgba(245, 250, 249, 0.64);
  box-shadow: 0 12rpx 28rpx rgba(30, 55, 56, 0.06);
  -webkit-backdrop-filter: blur(16px) saturate(116%);
  backdrop-filter: blur(16px) saturate(116%);
}

.circle-community-tab {
  min-height: 64rpx;
  margin: 0;
  padding: 0 16rpx;
  border: 0;
  border-radius: 18rpx;
  background: transparent;
  color: #70807e;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 25rpx;
  line-height: 1.2;
  font-weight: 800;
  transition: color 180ms ease, background-color 180ms ease, transform 180ms ease;
}

.circle-community-tab::after,
.community-filter-chip::after {
  border: 0;
}

.circle-community-tab.active {
  background: rgba(255, 255, 255, 0.8);
  color: #16786f;
  box-shadow: 0 5rpx 16rpx rgba(35, 65, 63, 0.09);
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

.community-filter-row {
  display: flex;
  gap: 12rpx;
  min-width: max-content;
  padding: 0 2rpx 2rpx;
}

.community-filter-chip {
  min-width: 122rpx;
  min-height: 58rpx;
  margin: 0;
  padding: 0 18rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.72);
  border-radius: 18rpx;
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

.community-filter-chip.active {
  border-color: rgba(22, 120, 111, 0.16);
  background: rgba(225, 242, 237, 0.82);
  color: #16786f;
}

.community-feed {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
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
  grid-template-columns: repeat(3, minmax(0, 1fr));
  align-items: center;
  gap: 10rpx;
  color: #83918f;
  font-size: 26rpx;
  line-height: 1.25;
  font-weight: 700;
}

.community-post-action {
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
  color: #3478f6;
}

.community-post-action.pending {
  opacity: 0.56;
}

.community-post-action:active {
  transform: scale(0.96);
}

.community-action-icon {
  width: 34rpx;
  height: 34rpx;
  flex: 0 0 34rpx;
}

.community-publish-button {
  position: fixed;
  z-index: 24;
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
  transition: transform 180ms ease, box-shadow 180ms ease, background-color 180ms ease;
}

.community-publish-button::after {
  border: 0;
}

.community-publish-button image {
  width: 100%;
  height: 100%;
}

.community-publish-button:active {
  transform: scale(0.94);
  box-shadow: 0 7px 16px rgba(52, 120, 246, 0.2);
  background: #2867DE;
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
  opacity: 0.56;
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
  padding-right: 56rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
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
  color: #93a09e;
  font-size: 26rpx;
  line-height: 1.2;
  font-weight: 800;
}

.community-comments-count.active {
  color: #1c2423;
}

.community-comment-sort {
  padding: 4rpx;
  border-radius: 999rpx;
  background: rgba(231, 240, 238, 0.86);
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.community-comment-sort-button {
  min-width: 62rpx;
  min-height: 48rpx;
  margin: 0;
  padding: 0 10rpx;
  border: 0;
  border-radius: 999rpx;
  background: transparent;
  color: #73817f;
  font-size: 20rpx;
  line-height: 1.2;
  font-weight: 800;
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
  border: 2rpx solid var(--gyt-primary-border, #d7e5ff);
  background: linear-gradient(135deg, #ffffff 0%, var(--gyt-primary-tint, #f4f8ff) 100%);
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
  position: relative;
  width: 170rpx;
  height: 60rpx;
  flex-shrink: 0;
  overflow: hidden;
}

.brand-title-image {
  position: absolute;
  left: -37rpx;
  top: -38rpx;
  display: block;
  width: 244rpx;
  height: auto;
  mix-blend-mode: multiply;
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
  color: #f5b700;
}

.message-bell-icon {
  display: block;
  width: 34rpx;
  height: 34rpx;
  flex-shrink: 0;
  background-color: currentColor;
  -webkit-mask: url('/static/ui-icons/notification-bell.svg') center / contain no-repeat;
  mask: url('/static/ui-icons/notification-bell.svg') center / contain no-repeat;
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
  position: sticky;
  top: calc(env(safe-area-inset-top) + 12rpx);
  z-index: 24;
  margin: -8rpx -12rpx 16rpx;
  padding: 14rpx 12rpx 12rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
  background: #ffffff;
  border-bottom: 2rpx solid rgba(230, 235, 245, 0.96);
  box-shadow: 0 10rpx 22rpx rgba(20, 31, 66, 0.05);
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
  position: fixed;
  top: var(--status-bar-height, env(safe-area-inset-top));
  right: 0;
  left: 0;
  z-index: 24;
  min-height: 100rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14rpx 22rpx;
  box-sizing: border-box;
  background: rgba(248, 250, 255, var(--report-header-opacity, 0.2));
  box-shadow: 0 14rpx 30rpx rgba(25, 48, 89, var(--report-header-shadow-opacity, 0));
  backdrop-filter: blur(18rpx);
  -webkit-backdrop-filter: blur(18rpx);
  transition: background 180ms ease, box-shadow 180ms ease;
}

.report-header-spacer {
  width: 100%;
  height: 78rpx;
  flex: 0 0 78rpx;
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

.mistake-page-head {
  display: flex;
  align-items: center;
  gap: 18rpx;
  margin: 2rpx auto 22rpx;
  width: 100%;
  max-width: 760rpx;
}

.mistake-list-head {
  position: fixed;
  top: var(--status-bar-height, env(safe-area-inset-top));
  right: 0;
  left: 0;
  z-index: 24;
  width: auto;
  max-width: none;
  min-height: 124rpx;
  margin: 0;
  padding: 16rpx 22rpx;
  box-sizing: border-box;
  background: rgba(248, 250, 255, var(--mistake-header-opacity, 0.2));
  box-shadow: 0 14rpx 30rpx rgba(25, 48, 89, var(--mistake-header-shadow-opacity, 0));
  backdrop-filter: blur(18rpx);
  -webkit-backdrop-filter: blur(18rpx);
  transition: background 180ms ease, box-shadow 180ms ease;
}

.mistake-list-head-spacer {
  width: 100%;
  height: 130rpx;
  flex: 0 0 130rpx;
}

.mistake-list-head .head-title {
  position: absolute;
  top: 20rpx;
  left: 50%;
  z-index: 1;
  width: max-content;
  max-width: calc(100% - 310rpx);
  overflow: hidden;
  text-align: center;
  text-overflow: ellipsis;
  white-space: nowrap;
  pointer-events: none;
  transform: translateX(-50%);
}

.mistake-list-head .mistake-head-copy {
  align-self: stretch;
  display: flex;
  align-items: flex-end;
  padding-top: 62rpx;
}

.mistake-list-head .head-subtitle {
  margin-top: 0;
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

.theme-icon-mask {
  background-color: currentColor;
  -webkit-mask-position: center;
  mask-position: center;
  -webkit-mask-repeat: no-repeat;
  mask-repeat: no-repeat;
  -webkit-mask-size: contain;
  mask-size: contain;
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

.advice-detail-close,
.theme-modal-close,
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

.circle-glass-page .circle-section-subtitle,
.circle-glass-page .experience-summary,
.circle-glass-page .material-desc,
.circle-glass-page .circle-empty-copy,
.circle-glass-page .circle-post-paragraph {
  color: #657473;
  font-weight: 500;
}

.circle-glass-page .circle-back-button {
  border: 1px solid rgba(255, 255, 255, 0.72);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.54);
  box-shadow: 0 8px 20px rgba(30, 55, 56, 0.1);
  -webkit-backdrop-filter: blur(18px) saturate(120%);
  backdrop-filter: blur(18px) saturate(120%);
  transition: transform 180ms ease, background-color 180ms ease;
}

.circle-glass-page .experience-search {
  border: 1px solid rgba(255, 255, 255, 0.72);
  background: rgba(249, 252, 251, 0.58);
  box-shadow: 0 10px 24px rgba(30, 55, 56, 0.08);
  -webkit-backdrop-filter: blur(16px) saturate(118%);
  backdrop-filter: blur(16px) saturate(118%);
}

.circle-glass-page .experience-search-icon,
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

.circle-glass-page .circle-section-count,
.circle-glass-page .experience-filter-chip,
.circle-glass-page .material-subject-chip,
.circle-glass-page .material-action,
.circle-glass-page .circle-post-close,
.circle-glass-page .circle-post-action-row button {
  border-color: rgba(255, 255, 255, 0.72);
  background: rgba(248, 251, 250, 0.62);
  color: #60716f;
  -webkit-backdrop-filter: blur(16px) saturate(118%);
  backdrop-filter: blur(16px) saturate(118%);
  transition: transform 180ms ease, background-color 180ms ease;
}

.circle-glass-page .experience-filter-chip.active,
.circle-glass-page .material-subject-chip.active {
  border-color: rgba(22, 120, 111, 0.16);
  background: rgba(225, 242, 237, 0.82);
  color: #16786f;
}

.circle-glass-page .experience-card,
.circle-glass-page .material-card,
.circle-glass-page .material-subject-card,
.circle-glass-page .circle-empty-card,
.circle-glass-page .circle-post-sheet {
  border-color: var(--circle-glass-border, rgba(255, 255, 255, 0.78));
  background: rgba(251, 253, 252, 0.78);
  box-shadow: 0 16px 38px rgba(30, 55, 56, 0.09);
  -webkit-backdrop-filter: blur(18px) saturate(118%);
  backdrop-filter: blur(18px) saturate(118%);
}

.circle-glass-page .material-subject-card {
  background: rgba(240, 248, 245, 0.78);
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
  .circle-glass-page .circle-back-button,
  .circle-glass-page .experience-search,
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
  .circle-glass-page .circle-post-sheet {
    background: #fbfcfb;
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

/* #ifdef MP-WEIXIN */
.home-page {
  padding-top: var(--mp-page-content-top, 96px);
}

.home-header {
  min-height: var(--mp-page-header-height, 40px);
  padding: 2rpx 10rpx 0;
}

.brand-line {
  gap: 12rpx;
}

.brand-title {
  width: 190rpx;
  height: 64rpx;
}

.brand-title-image {
  left: -34rpx;
  top: -36rpx;
  width: 244rpx;
  mix-blend-mode: multiply;
}

.brand-badge {
  padding: 8rpx 14rpx;
  font-size: 24rpx;
}

.home-actions {
  gap: 12rpx;
}

.message-bell {
  width: 66rpx;
  height: 66rpx;
  line-height: 66rpx;
}

.message-bell-icon {
  width: 30rpx;
  height: 30rpx;
}

.profile-entry {
  width: 68rpx;
  height: 68rpx;
  border-radius: 34rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 8rpx 20rpx rgba(20, 31, 66, 0.1);
}

.mistake-list-head,
.report-topbar {
  top: var(--mp-page-content-top, 96px);
}

.mistake-list-head-spacer {
  height: calc(var(--mp-page-header-height, 40px) + 38rpx);
  flex-basis: calc(var(--mp-page-header-height, 40px) + 38rpx);
}

.report-header-spacer {
  height: calc(var(--mp-page-header-height, 40px) + 22rpx);
  flex-basis: calc(var(--mp-page-header-height, 40px) + 22rpx);
}
/* #endif */
</style>
