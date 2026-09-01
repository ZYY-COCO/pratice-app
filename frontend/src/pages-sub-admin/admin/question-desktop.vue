<template>
  <view
    class="portal-shell"
    :class="{
      'sidebar-collapsed': sidebarCollapsed,
      'dashboard-focus-mode': sidebarCollapsed && activeSection === 'dashboard',
      'import-preview-focus-mode': sidebarCollapsed && activeSection === 'import' && importPreviewVisible
    }"
  >
    <aside class="portal-sidebar">
      <view class="sidebar-brand">
        <view class="brand-mark">
          <image class="brand-logo" src="/static/brand/gangyantong-logo.webp" mode="aspectFit" />
        </view>
        <view class="brand-copy">
          <view class="brand-name">港研通</view>
          <view class="brand-caption">后台管理</view>
        </view>
        <button
          class="sidebar-focus-toggle"
          :title="sidebarToggleTitle"
          :aria-label="sidebarToggleTitle"
          @tap.stop="toggleSidebarCollapsed"
        >
          <image
            class="sidebar-toggle-icon sidebar-toggle-icon-default"
            :src="sidebarCollapsed ? '/static/admin-icons/sidebar-panel-open.svg' : '/static/admin-icons/sidebar-panel.svg'"
            mode="aspectFit"
          />
          <image
            class="sidebar-toggle-icon sidebar-toggle-icon-hover"
            :src="sidebarCollapsed ? '/static/admin-icons/sidebar-panel-open.svg' : '/static/admin-icons/sidebar-panel-close.svg'"
            mode="aspectFit"
          />
        </button>
      </view>

      <view class="sidebar-section-label">工作台</view>
      <view class="sidebar-nav">
        <button
          v-for="item in visibleNavItems"
          :key="item.key"
          class="nav-item"
          :class="{ active: navItemActive(item.key) }"
          @tap="switchSection(item.key)"
        >
          <view class="nav-icon" :style="{ '--nav-icon-url': `url(${item.icon})` }"></view>
          <text class="nav-label">{{ item.label }}</text>
        </button>
      </view>

      <view class="sidebar-spacer"></view>
      <button class="logout-button" @tap="logout">
        <text class="nav-glyph">↗</text>
        <text class="nav-label">退出登录</text>
      </button>
    </aside>

    <main class="portal-main">
      <header class="portal-header">
        <view class="header-left">
          <button
            v-if="showHeaderBackButton"
            class="header-back-button"
            :disabled="headerBackDisabled"
            @tap="handleHeaderBack"
          >
            <image class="header-back-icon" src="/static/admin-icons/admin-back.svg" mode="aspectFit" />
          </button>
          <view class="header-title-group">
            <view class="header-breadcrumb">港研通 / {{ currentNavLabel }}</view>
            <view class="header-title">{{ pageTitle }}</view>
          </view>
        </view>
        <view class="header-actions">
          <view v-if="activeSection === 'import'" class="header-import-actions">
            <button class="header-import-button template" @tap="downloadQuestionImportTemplate">
              下载模板
            </button>
            <button class="header-import-button guide" @tap="downloadQuestionImportGuide">
              填写说明
            </button>
            <button class="header-import-button history" @tap="showQuestionImportHistory">
              <text class="header-import-history-icon">◷</text>
              <text>导入记录</text>
            </button>
          </view>
          <button class="header-refresh" :disabled="refreshing" @tap="refreshCurrentSection">
            <view class="refresh-symbol" :class="{ spinning: refreshing }" aria-hidden="true"><AppRefreshIcon /></view>
            <text>{{ refreshing ? '刷新中' : '刷新数据' }}</text>
          </button>
          <view class="profile-chip">
            <view class="profile-avatar">
              <image class="profile-avatar-image" src="/static/brand/question-bank-manager-avatar.png" mode="aspectFit" />
            </view>
            <view class="profile-copy">
              <view class="profile-name">{{ profileName }}</view>
            </view>
          </view>
        </view>
      </header>

      <view v-if="portalLoading" class="page-state">
        <view class="state-spinner"></view>
        <view class="state-title">正在验证内部权限</view>
        <view class="state-copy">请稍候，系统正在建立安全会话。</view>
      </view>

      <view v-else-if="portalBootstrapError" class="page-state portal-access-error">
        <view class="state-title">{{ portalBootstrapError.title }}</view>
        <view class="state-copy">{{ portalBootstrapError.message }}</view>
        <button class="secondary-button portal-retry-button" @tap="bootstrap">重新连接</button>
      </view>

      <template v-else>
        <section v-if="activeSection === 'dashboard'" class="content-section dashboard-section">
          <view class="welcome-row">
            <view>
              <view class="welcome-kicker">{{ todayLabel }}</view>
              <view class="welcome-title">{{ greeting }}，{{ profileName }}</view>
              <view class="welcome-copy">这里汇总今天的刷题活跃、注册增长与高频错题。</view>
            </view>
            <view class="welcome-badge">
              <text class="badge-dot"></text>
              数据口径已校准
            </view>
          </view>

          <view class="dashboard-metrics">
            <view class="metric-card">
              <view class="metric-icon metric-icon-asset">
                <image class="metric-icon-image" src="/static/admin-icons/dashboard-visits.svg" mode="aspectFit" />
              </view>
              <view class="metric-content">
                <view class="metric-label">今日访问</view>
                <view class="metric-value">{{ formatCount(dashboard.today_practicing_users) }}</view>
                <view class="metric-note">今日成功登录的去重用户</view>
              </view>
              <view class="metric-chip">北京时间</view>
            </view>

            <view class="metric-card registered-users-card">
              <view class="metric-icon metric-icon-asset">
                <image class="metric-icon-image" src="/static/admin-icons/dashboard-members.svg" mode="aspectFit" />
              </view>
              <view class="metric-content">
                <view class="metric-label">注册人数</view>
                <view class="metric-value">{{ formatCount(dashboard.registered_users) }}</view>
                <view class="metric-note">累计完成注册的用户</view>
              </view>
              <view
                v-if="dashboard.today_registered_users > 0"
                class="metric-growth"
                :aria-label="`今日新增 ${formatCount(dashboard.today_registered_users)} 人`"
              >
                <text class="metric-growth-count">+{{ formatCount(dashboard.today_registered_users) }}</text>
                <text class="metric-growth-label">今日新增</text>
              </view>
            </view>

            <view class="metric-card">
              <view class="metric-icon metric-icon-asset">
                <image class="metric-icon-image" src="/static/admin-icons/dashboard-question-bank.svg" mode="aspectFit" />
              </view>
              <view class="metric-content">
                <view class="metric-label">正式题库</view>
                <view class="metric-value">{{ formatCount(totalQuestionCount) }}</view>
                <view class="metric-note">其中 {{ formatCount(questionStats.pendingReview) }} 道等待审核</view>
              </view>
              <button class="metric-link" @tap="switchSection('questions')">查看题库 →</button>
            </view>
          </view>

          <view class="dashboard-panel">
            <view class="panel-heading">
              <view>
                <view class="panel-title">高频错题</view>
              </view>
              <view class="dashboard-filter-bar">
                <view class="dashboard-filter-control">
                  <text class="dashboard-filter-label">题目类型</text>
                  <AdminSelect
                    class="dashboard-admin-select"
                    :options="dashboardSubjectLabels"
                    :value-index="selectedDashboardSubjectIndex"
                    menu-align="right"
                    aria-label="题目类型"
                    @change="handleDashboardSubjectChange"
                  />
                </view>
                <view class="dashboard-filter-control">
                  <text class="dashboard-filter-label">时间范围</text>
                  <AdminSelect
                    class="dashboard-admin-select compact"
                    :options="dashboardTimeRangeLabels"
                    :value-index="selectedDashboardTimeRangeIndex"
                    menu-align="right"
                    aria-label="时间范围"
                    @change="handleDashboardTimeRangeChange"
                  />
                </view>
                <view class="dashboard-filter-control">
                  <text class="dashboard-filter-label">排序</text>
                  <AdminSelect
                    class="dashboard-admin-select sort"
                    :options="dashboardSortOptions"
                    :value-index="selectedDashboardSortIndex"
                    menu-align="right"
                    aria-label="排序"
                    @change="handleDashboardSortChange"
                  />
                </view>
              </view>
            </view>

            <view v-if="dashboardLoading" class="inline-loading">正在汇总刷题数据…</view>
            <view v-else-if="dashboard.difficult_questions.length === 0" class="empty-panel">
              <view class="empty-icon">∿</view>
              <view class="empty-title">暂无可汇总的刷题记录</view>
              <view class="empty-copy">产生用户答题记录后，这里会自动显示高频错题。</view>
            </view>
            <view v-else>
              <view class="data-table difficult-table">
                <view class="table-row table-head">
                  <view class="rank-cell">排名</view>
                  <view class="stem-cell">题目</view>
                  <view class="category-cell">分类</view>
                  <view class="number-cell">答错次数</view>
                  <view class="number-cell">作答次数</view>
                  <view class="accuracy-cell">正确率</view>
                </view>
                <button
                  v-for="(item, index) in dashboard.difficult_questions"
                  :key="item.question_id"
                  class="table-row difficult-row"
                  @tap="openQuestionById(item.question_id)"
                >
                  <view class="rank-cell">
                    <text class="rank-badge" :class="{ top: dashboardRankOffset + index < 3 }">
                      {{ dashboardRankOffset + index + 1 }}
                    </text>
                  </view>
                  <view class="stem-cell">
                    <MathText class="stem-primary" :value="item.stem" />
                    <view class="stem-id">ID {{ shortId(item.question_id) }}</view>
                  </view>
                  <view class="category-cell">
                    <text class="category-primary">{{ item.subject || '未分类' }}</text>
                    <text class="category-secondary">{{ item.module || '未分模块' }}</text>
                  </view>
                  <view class="number-cell wrong-number">{{ item.wrong_count }}</view>
                  <view class="number-cell">{{ item.attempt_count }}</view>
                  <view class="accuracy-cell">
                    <view class="accuracy-copy">
                      <text>{{ formatAccuracy(item.accuracy) }}</text>
                      <text class="accuracy-tone" :class="accuracyTone(item.accuracy)">
                        {{ accuracyHint(item.accuracy) }}
                      </text>
                    </view>
                    <view class="accuracy-track">
                      <view
                        class="accuracy-fill"
                        :class="accuracyTone(item.accuracy)"
                        :style="{ width: `${clampAccuracy(item.accuracy)}%` }"
                      ></view>
                    </view>
                  </view>
                </button>
              </view>
              <view class="pagination-row dashboard-pagination-row">
                <view class="pagination-actions">
                  <button
                    :disabled="dashboardDifficultPage <= 1 || dashboardLoading"
                    @tap="changeDashboardDifficultPage(dashboardDifficultPage - 1)"
                  >‹</button>
                  <view class="page-current">{{ dashboardDifficultPage }}</view>
                  <view class="page-total">/ {{ dashboardDifficultTotalPages }}</view>
                  <button
                    :disabled="dashboardDifficultPage >= dashboardDifficultTotalPages || dashboardLoading"
                    @tap="changeDashboardDifficultPage(dashboardDifficultPage + 1)"
                  >›</button>
                </view>
              </view>
            </view>
          </view>
        </section>

        <section v-if="activeSection === 'community'" class="content-section community-section">
          <view class="content-management-switcher" aria-label="内容管理分类">
            <button
              v-for="tab in contentManagementTabs"
              :key="tab.key"
              class="content-management-tab"
              :class="{ active: contentManagementTab === tab.key }"
              @tap="selectContentManagementTab(tab.key)"
            >
              <image class="content-management-tab-icon" :src="tab.icon" mode="aspectFit" />
              <view class="content-management-tab-copy">
                <text class="content-management-tab-label">{{ tab.label }}</text>
                <text class="content-management-tab-description">{{ tab.description }}</text>
              </view>
              <text class="content-management-tab-arrow">›</text>
            </button>
          </view>

          <view v-show="contentManagementTab === 'posts'" class="content-management-view">
          <view class="question-workspace community-workspace">
            <view class="filter-toolbar community-filter-toolbar">
              <view class="search-shell community-search-shell">
                <view class="search-icon">
                  <image class="search-icon-image" src="/static/admin-icons/admin-search.svg" mode="aspectFit" />
                </view>
                <input
                  v-model.trim="communityFilters.search"
                  class="search-input"
                  placeholder="搜索帖子、正文或用户"
                  confirm-type="search"
                  @input="handleCommunitySearchInput"
                  @confirm="applyCommunityFilters"
                />
                <button v-if="communityFilters.search" class="search-clear" @tap="clearCommunitySearch">×</button>
              </view>

              <AdminSelect
                class="question-admin-select community-admin-select"
                :options="communityStatusLabels"
                :value-index="selectedCommunityStatusIndex"
                aria-label="帖子状态筛选"
                @change="handleCommunityStatusChange"
              />
              <AdminSelect
                class="question-admin-select community-admin-select"
                :options="communityTypeLabels"
                :value-index="selectedCommunityTypeIndex"
                aria-label="帖子类型筛选"
                @change="handleCommunityTypeChange"
              />
              <AdminSelect
                class="question-admin-select community-admin-select sort"
                :options="communitySortLabels"
                :value-index="selectedCommunitySortIndex"
                aria-label="帖子排序方式"
                @change="handleCommunitySortChange"
              />
              <button
                class="community-featured-button"
                :class="{ remove: communityBulkFeaturedAction && !communityBulkFeaturedAction.isFeatured }"
                :disabled="!communityBulkFeaturedAction || communitySaving"
                @tap="handleCommunityBulkFeaturedAction"
              >{{ communityBulkFeaturedAction?.label || '加入精选' }}</button>
              <button v-if="communityHasFilters" class="clear-filter-button" @tap="clearCommunityFilters">清空</button>
            </view>

            <view class="question-table-wrap">
              <view class="question-table community-table">
                <view class="community-grid table-head" :class="{ selecting: communitySelectedIds.length }">
                  <view class="check-cell">
                    <button class="check-box" :class="{ checked: allCommunityPageSelected }" @tap="toggleSelectCommunityPage">
                      {{ allCommunityPageSelected ? '✓' : '' }}
                    </button>
                  </view>
                  <view v-if="communitySelectedIds.length" class="community-selection-header">
                    <view class="bulk-copy">已选择 <text>{{ communitySelectedIds.length }}</text> 条帖子</view>
                    <view class="bulk-actions">
                      <button
                        v-if="communityBulkVisibilityAction"
                        class="bulk-button"
                        :class="communityBulkVisibilityAction.tone"
                        @tap="bulkChangeCommunityVisibility(communityBulkVisibilityAction.isPublished)"
                      >
                        {{ communityBulkVisibilityAction.label }}
                      </button>
                      <button class="bulk-cancel" @tap="communitySelectedIds = []">取消选择</button>
                    </view>
                  </view>
                  <view v-else>帖子</view>
                  <view>发布用户</view>
                  <view>分类</view>
                  <view>浏览</view>
                  <view>点赞</view>
                  <view>评论</view>
                  <view>状态</view>
                  <view>发布时间</view>
                  <view>{{ communitySelectedIds.length ? '' : '操作' }}</view>
                </view>

                <view v-if="communityLoading" class="table-state">正在加载社区内容…</view>
                <view v-else-if="communityLoadError" class="table-state error">
                  <view>社区内容加载失败，请检查网络或权限状态。</view>
                  <button @tap="loadCommunityData">重新加载</button>
                </view>
                <view v-else-if="communityPosts.length === 0" class="table-state">
                  <view>当前条件下没有帖子</view>
                </view>
                <view
                  v-for="item in communityPosts"
                  v-else
                  :key="item.id"
                  class="community-grid community-row"
                  :class="{ selected: isCommunitySelected(item.id) }"
                  @tap="openCommunityPostDetail(item)"
                >
                  <view class="check-cell">
                    <button
                      class="check-box"
                      :class="{ checked: isCommunitySelected(item.id) }"
                      @tap.stop="toggleCommunitySelection(item.id)"
                    >
                      {{ isCommunitySelected(item.id) ? '✓' : '' }}
                    </button>
                  </view>
                  <view class="community-post-cell">
                    <view class="community-post-title">{{ item.title || '未填写标题' }}</view>
                    <view class="community-post-copy">{{ item.content || '未填写正文' }}</view>
                  </view>
                  <view class="community-author-cell">
                    <view class="community-author-avatar">{{ item.author_avatar || item.author_name?.slice(0, 1) || '研' }}</view>
                    <view class="community-author-meta">
                      <view class="community-author-name">{{ item.author_name || '研友' }}</view>
                      <view class="community-author-id">ID {{ shortId(item.author_id) }}</view>
                    </view>
                  </view>
                  <view class="community-category-cell">
                    <view class="community-category-primary">{{ item.category || '未分类' }}</view>
                    <view class="community-category-type">{{ communityPostTypeText(item.post_type) }}</view>
                  </view>
                  <view class="community-stat-cell">{{ formatCount(item.view_count) }}</view>
                  <view class="community-stat-cell">{{ formatCount(item.like_count) }}</view>
                  <view class="community-stat-cell">{{ formatCount(item.comment_count) }}</view>
                  <view class="status-cell">
                    <text class="status-pill" :class="item.is_published ? 'published' : 'archived'">
                      {{ communityPostStatusText(item.is_published) }}
                    </text>
                  </view>
                  <view class="date-cell">{{ formatDate(item.created_at) }}</view>
                  <view class="community-action-cell">
                    <button v-if="!communitySelectedIds.length" class="row-action" @tap.stop="openCommunityPostDetail(item)">查看</button>
                    <button
                      v-if="!communitySelectedIds.length"
                      class="community-visibility-button"
                      :class="{ restore: !item.is_published }"
                      @tap.stop="toggleCommunityPostVisibility(item)"
                    >
                      {{ item.is_published ? '下架' : '恢复' }}
                    </button>
                  </view>
                </view>
              </view>
            </view>

            <view class="pagination-row">
              <view class="pagination-info">共 {{ formatCount(communityCount) }} 条，每页 {{ communityPageSize }} 条</view>
              <view class="pagination-actions">
                <button :disabled="communityPage <= 1 || communityLoading" @tap="changeCommunityPage(communityPage - 1)">‹</button>
                <view class="page-current">{{ communityPage }}</view>
                <view class="page-total">/ {{ communityTotalPages }}</view>
                <button :disabled="communityPage >= communityTotalPages || communityLoading" @tap="changeCommunityPage(communityPage + 1)">›</button>
              </view>
            </view>
          </view>
          </view>

          <view v-if="contentManagementMountedTabs.reports" v-show="contentManagementTab === 'reports'" class="content-management-view">
            <AdminCommunityModeration ref="communityModerationRef" :preview="devPreviewMode" />
          </view>

          <view v-if="contentManagementMountedTabs.appeals" v-show="contentManagementTab === 'appeals'" class="content-management-view">
            <AdminCommunityAppeals ref="communityAppealsRef" :preview="devPreviewMode" />
          </view>
        </section>

        <section v-if="activeSection === 'consultation'" class="content-section operations-section">
          <AdminConsultationManagement
            ref="consultationManagementRef"
            :preview="devPreviewMode"
            :initial-view="consultationInitialView"
            :initial-case-view="consultationInitialCaseView"
          />
        </section>

        <section v-if="activeSection === 'users'" class="content-section operations-section">
          <view class="operations-summary-grid">
            <view class="operations-summary-card">
              <view class="operations-summary-label">总用户</view>
              <view class="operations-summary-value">{{ operationsMetricValue('total_users') }}</view>
              <view class="operations-summary-note">已注册账号</view>
            </view>
            <view class="operations-summary-card mint">
              <view class="operations-summary-label">今日新增</view>
              <view class="operations-summary-value">{{ operationsMetricValue('new_today') }}</view>
              <view class="operations-summary-note">按北京时间统计</view>
            </view>
            <view
              class="operations-summary-card blue membership-management-summary"
              role="button"
              aria-label="打开会员管理"
              @tap="openMembershipPageManager"
            >
              <view class="operations-summary-label">会员管理</view>
              <view class="operations-summary-value">PLUS</view>
              <view class="operations-summary-note">页面文案与套餐定价</view>
            </view>
            <view class="operations-summary-card slate">
              <view class="operations-summary-label">有效会员</view>
              <view class="operations-summary-value">{{ operationsMetricValue('active_members') }}</view>
              <view class="operations-summary-note">当前会员状态有效</view>
            </view>
          </view>

          <view v-if="operationsOverviewError" class="operations-inline-alert">
            <view><strong>用户汇总暂未更新</strong><text>列表仍可使用，顶部数字不会以 0 冒充未知状态。</text></view>
            <button @tap="loadOperationsOverview">重新读取</button>
          </view>

          <view class="question-workspace user-workspace">
            <view class="workspace-heading">
              <view>
                <view class="panel-title">用户管理</view>
                <view class="panel-subtitle">查看注册时间、刷题正确率、活跃度和会员状态；异常账号可停用后恢复。</view>
              </view>
            </view>
            <view class="filter-toolbar user-filter-toolbar">
              <view class="search-shell user-search-shell">
                <view class="search-icon"><image class="search-icon-image" src="/static/admin-icons/admin-search.svg" mode="aspectFit" /></view>
                <input v-model.trim="userFilters.search" class="search-input" placeholder="搜索邮箱、手机号或昵称" @input="handlePortalUserSearchInput" @confirm="applyPortalUserFilters" />
                <button v-if="userFilters.search" class="search-clear" @tap="clearPortalUserSearch">×</button>
              </view>
              <AdminSelect class="question-admin-select" :options="portalUserExamOptions.map((item) => item.label)" :value-index="portalUserExamIndex" aria-label="考试类型" @change="handlePortalUserExamChange" />
              <AdminSelect class="question-admin-select" :options="portalUserMembershipOptions.map((item) => item.label)" :value-index="portalUserMembershipIndex" aria-label="会员状态" @change="handlePortalUserMembershipChange" />
              <AdminSelect class="question-admin-select" :options="portalUserAccountStatusOptions.map((item) => item.label)" :value-index="portalUserAccountStatusIndex" aria-label="账号状态" @change="handlePortalUserAccountStatusChange" />
              <AdminSelect class="question-admin-select" :options="portalUserActivityOptions.map((item) => item.label)" :value-index="portalUserActivityIndex" aria-label="用户活跃度" @change="handlePortalUserActivityChange" />
            </view>

            <view class="question-table-wrap">
              <view class="question-table portal-user-table">
                <view class="portal-user-grid table-head">
                  <view>用户</view>
                  <view class="portal-user-sort-header" :class="{ active: userSort.field === 'exam_target' }" @tap="sortPortalUsers('exam_target')">目标<text v-if="userSort.field === 'exam_target'" class="portal-user-sort-icon">{{ userSort.direction === 'asc' ? '▲' : '▼' }}</text></view>
                  <view class="portal-user-sort-header" :class="{ active: userSort.field === 'answer_count' }" @tap="sortPortalUsers('answer_count')">刷题数据<text v-if="userSort.field === 'answer_count'" class="portal-user-sort-icon">{{ userSort.direction === 'asc' ? '▲' : '▼' }}</text></view>
                  <view class="portal-user-sort-header" :class="{ active: userSort.field === 'accuracy' }" @tap="sortPortalUsers('accuracy')">正确率<text v-if="userSort.field === 'accuracy'" class="portal-user-sort-icon">{{ userSort.direction === 'asc' ? '▲' : '▼' }}</text></view>
                  <view class="portal-user-sort-header" :class="{ active: userSort.field === 'last_active' }" @tap="sortPortalUsers('last_active')">最近作答<text v-if="userSort.field === 'last_active'" class="portal-user-sort-icon">{{ userSort.direction === 'asc' ? '▲' : '▼' }}</text></view>
                  <view class="portal-user-sort-header" :class="{ active: userSort.field === 'created_at' }" @tap="sortPortalUsers('created_at')">注册时间<text v-if="userSort.field === 'created_at'" class="portal-user-sort-icon">{{ userSort.direction === 'asc' ? '▲' : '▼' }}</text></view>
                  <view>会员</view>
                  <view>状态</view>
                  <view>操作</view>
                </view>
                <view v-if="portalUsersLoading" class="table-state">正在加载用户数据…</view>
                <view v-else-if="portalUsersError" class="table-state error"><view>用户数据加载失败，请检查网络或权限状态。</view><button @tap="loadPortalUsers">重新加载</button></view>
                <view v-else-if="portalUsers.length === 0" class="table-state">当前筛选下没有用户</view>
                <view v-else v-for="item in portalUsers" :key="item.id" class="portal-user-grid portal-user-row" @tap="openPortalUserDetail(item)">
                  <view class="portal-user-identity"><view class="portal-user-avatar">{{ item.nickname?.slice(0, 1) || item.email?.slice(0, 1) || '研' }}</view><view><view class="portal-user-name">{{ item.nickname || '未设置昵称' }}</view><view class="portal-user-contact">{{ item.email || item.phone || shortId(item.id) }}</view></view></view>
                  <view>{{ item.exam_target || '—' }}</view>
                  <view><strong>{{ formatCount(item.answer_count) }}</strong><text> 题</text></view>
                  <view class="portal-accuracy" :class="accuracyTone(item.accuracy)">{{ formatAccuracy(item.accuracy) }}</view>
                  <view>{{ formatDate(item.last_answer_at) }}</view>
                  <view>{{ formatDate(item.created_at) }}</view>
                  <view>{{ portalUserMembershipLabel(item) }}</view>
                  <view><text class="status-pill" :class="item.disabled_at ? 'archived' : 'published'">{{ item.disabled_at ? '已停用' : '正常' }}</text></view>
                  <view class="portal-user-actions"><button class="row-action" :disabled="portalUserSavingId === item.id" @tap.stop="openPortalUserDetail(item)">查看</button><button class="portal-membership-button" :disabled="portalUserSavingId === item.id" @tap.stop="openPortalUserMembership(item)">{{ portalUserSavingId === item.id ? '处理中' : '会员管理' }}</button></view>
                </view>
              </view>
            </view>
            <view class="pagination-row"><view class="pagination-info">共 {{ formatCount(portalUserCount) }} 位用户，每页 {{ portalUserPageSize }} 位</view><view class="pagination-actions"><button :disabled="portalUserPage <= 1 || portalUsersLoading" @tap="changePortalUserPage(portalUserPage - 1)">‹</button><view class="page-current">{{ portalUserPage }}</view><view class="page-total">/ {{ portalUserTotalPages }}</view><button :disabled="portalUserPage >= portalUserTotalPages || portalUsersLoading" @tap="changePortalUserPage(portalUserPage + 1)">›</button></view></view>
          </view>
        </section>

        <section v-if="activeSection === 'admission'" class="content-section operations-section">
          <view class="operations-heading-row">
            <view><view class="welcome-kicker">ADMISSION DATA</view><view class="operations-page-title">报考资料</view><view class="operations-page-copy">历史分数线、院校公告和专业目录统一在后台维护，导入前先完成字段检查。</view></view>
            <view class="operations-status-chip"><text class="badge-dot"></text> {{ operationsMetricValue('published_announcements') }} 条公告已发布</view>
          </view>
          <view class="operations-tab-strip">
            <view v-for="item in admissionDatasets" :key="item.key" class="operations-tab" :class="{ active: admissionDataset === item.key }">
              <view class="operations-tab-copy" role="button" :aria-label="`查看${item.label}数据`" @tap="switchAdmissionDataset(item.key)"><text>{{ item.label }}</text><small>点击查看或导入数据</small></view>
              <button class="admission-card-import-button" @tap.stop="openAdmissionImport(item.key)">导入数据</button>
            </view>
          </view>

            <view v-if="admissionDataset === 'scorelines'" class="question-workspace scoreline-record-workspace">
              <view class="workspace-heading scoreline-workspace-heading">
                <view><view class="panel-title">分数线逐条管理</view><view class="panel-subtitle">{{ selectedAdmissionRun ? `当前数据：${selectedAdmissionRun.source_filename}` : '暂无分数线数据，请先导入' }}</view></view>
                <view class="scoreline-heading-tools"><text>{{ formatCount(scorelineRecordCount) }} 条</text><button v-if="!admissionRunsLoading && !admissionRuns.length" class="row-action" :disabled="scorelineRecordBootstrapLoading" @tap="bootstrapExistingScorelineRecords">{{ scorelineRecordBootstrapLoading ? '接入中…' : '接入现有数据' }}</button></view>
              </view>
              <view v-if="selectedAdmissionRun" class="scoreline-filter-toolbar">
                <input v-model.trim="scorelineFilters.keyword" class="scoreline-filter-input scoreline-filter-search" maxlength="100" placeholder="搜索院校" confirm-type="search" @input="handleScorelineFilterInput" @confirm="applyScorelineFilters" />
                <AdminSelect class="scoreline-filter-select" :options="scorelineYearFilterOptions" :value-index="scorelineYearFilterIndex" aria-label="年份筛选" @change="handleScorelineYearFilterChange" />
                <AdminSelect class="scoreline-filter-select scoreline-filter-region-select" :options="scorelineRegionFilterOptions" :value-index="scorelineRegionFilterIndex" aria-label="地区筛选" @change="handleScorelineRegionFilterChange" />
                <button v-if="scorelineFilters.keyword || scorelineFilters.score_year || scorelineFilters.region" class="scoreline-filter-clear" @tap="clearScorelineFilters">×</button>
              </view>
              <view class="question-table-wrap">
                <view class="question-table scoreline-record-table">
                  <view class="scoreline-record-grid table-head"><view>年份</view><view>地区</view><view>招生单位</view><view>分数线</view><view>来源与备注</view><view>更新时间</view><view>操作</view></view>
                  <view v-if="!selectedAdmissionRun" class="table-state">暂无分数线数据，请先导入</view>
                  <view v-else-if="scorelineRecordsLoading" class="table-state">正在读取分数线…</view>
                  <view v-else-if="scorelineRecordsError" class="table-state error"><view>分数线记录读取失败。</view><button @tap="loadScorelineRecords">重新加载</button></view>
                  <view v-else-if="!scorelineRecords.length" class="table-state">当前筛选下没有分数线记录</view>
                  <view v-else v-for="item in scorelineRecords" :key="item.id" class="scoreline-record-grid scoreline-record-row">
                    <view class="scoreline-year-cell">{{ item.score_year }}</view>
                    <view>{{ item.region }}</view>
                    <view><strong>{{ item.school_name }}</strong><text>{{ item.unit_name || '招生单位' }}</text></view>
                    <view><strong class="scoreline-value">{{ item.score_raw }}</strong><text class="scoreline-kind" :class="`is-${item.score_kind || 'note'}`">{{ scorelineKindText(item.score_kind) }}</text></view>
                    <view class="scoreline-source-cell"><strong v-if="item.source_note">{{ item.source_note }}</strong><text v-else>—</text><small v-if="item.source_url">已附来源链接</small></view>
                    <view>{{ formatDateTime(item.updated_at || item.created_at) }}</view>
                    <view><button class="row-action" :disabled="scorelineRecordSaving && scorelineRecordEditingId === item.id" @tap="openScorelineRecordEditor(item)">编辑</button></view>
                  </view>
                </view>
              </view>
              <view v-if="selectedAdmissionRun" class="pagination-row scoreline-pagination"><view class="pagination-info">共 {{ formatCount(scorelineRecordCount) }} 条，每页 {{ scorelineRecordPageSize }} 条</view><view class="pagination-actions"><button :disabled="scorelineRecordPage <= 1 || scorelineRecordsLoading" @tap="changeScorelineRecordPage(scorelineRecordPage - 1)">‹</button><view class="page-current">{{ scorelineRecordPage }}</view><view class="page-total">/ {{ scorelineRecordTotalPages }}</view><button :disabled="scorelineRecordPage >= scorelineRecordTotalPages || scorelineRecordsLoading" @tap="changeScorelineRecordPage(scorelineRecordPage + 1)">›</button></view></view>
            </view>

            <view v-if="admissionDataset === 'announcements'" class="question-workspace announcement-record-workspace">
              <view class="workspace-heading announcement-workspace-heading">
                <view><view class="panel-title">公告逐条管理</view><view class="panel-subtitle">用户端已发布院校公告</view></view>
                <view class="announcement-heading-tools">
                  <text>{{ formatCount(announcementRecordCount) }} 条</text>
                  <button v-if="canBootstrapExistingAdmissionSnapshot" class="row-action" :disabled="admissionSnapshotBootstrapLoading" @tap="bootstrapExistingAdmissionSnapshot('announcements')">{{ admissionSnapshotBootstrapLoading ? '接入中…' : '接入现有数据' }}</button>
                </view>
              </view>
              <view class="scoreline-filter-toolbar announcement-filter-toolbar">
                <input v-model.trim="announcementFilters.keyword" class="scoreline-filter-input scoreline-filter-search" maxlength="80" placeholder="搜索院校、学院、公告标题或正文" confirm-type="search" @confirm="applyAnnouncementFilters" />
                <AdminSelect class="scoreline-filter-select" :options="announcementNoticeTypeFilterOptions" :value-index="announcementNoticeTypeFilterIndex" aria-label="公告类型筛选" @change="handleAnnouncementNoticeTypeFilterChange" />
                <AdminSelect class="scoreline-filter-select" :options="announcementYearFilterOptions" :value-index="announcementYearFilterIndex" aria-label="公告年份筛选" @change="handleAnnouncementYearFilterChange" />
                <AdminSelect class="scoreline-filter-select scoreline-filter-region-select" :options="announcementRegionFilterOptions" :value-index="announcementRegionFilterIndex" aria-label="地域查找" @change="handleAnnouncementRegionFilterChange" />
                <AdminSelect class="scoreline-filter-select major-catalog-school-select" :options="announcementSchoolFilterOptions" :value-index="announcementSchoolFilterIndex" :disabled="!announcementFilters.region" aria-label="招生院校筛选" @change="handleAnnouncementSchoolFilterChange" />
                <button class="scoreline-filter-apply" @tap="applyAnnouncementFilters">查找</button>
                <button v-if="announcementFilters.notice_type || announcementFilters.notice_year || announcementFilters.region || announcementFilters.school_id || announcementFilters.keyword" class="scoreline-filter-clear" @tap="clearAnnouncementFilters">×</button>
              </view>
              <view class="question-table-wrap">
                <view class="question-table announcement-record-table">
                  <view class="announcement-record-grid table-head"><view>公告</view><view>院校</view><view>类型</view><view>发布日期</view><view>状态</view><view>操作</view></view>
                  <view v-if="announcementRecordsLoading" class="table-state">正在读取公告…</view>
                  <view v-else-if="announcementRecordsError" class="table-state error"><view>公告记录读取失败。</view><button @tap="loadAnnouncementRecords">重新加载</button></view>
                  <view v-else-if="!announcementRecords.length" class="table-state">当前筛选下没有公告</view>
                  <view v-else v-for="item in announcementRecords" :key="item.id" class="announcement-record-grid announcement-record-row">
                    <view><strong>{{ item.title }}</strong><text>{{ item.summary || '—' }}</text></view>
                    <view>{{ item.school_name }}<text v-if="item.unit_name"> · {{ item.unit_name }}</text></view>
                    <view>{{ item.notice_type === 'brochure' ? '招生简章' : '复试分数线' }}</view>
                    <view>{{ item.notice_date || '—' }}</view>
                    <view class="announcement-status-cell"><text class="status-pill" :class="item.status === 'published' ? 'published' : item.status === 'archived' ? 'archived' : 'pending'">{{ admissionRunStatusText(item.status) }}</text></view>
                    <view class="announcement-record-actions"><template v-if="canManageSelectedAnnouncementRecords"><button class="row-action" :disabled="announcementUpdatingId === item.id" @tap="setAnnouncementRecordStatus(item, item.status === 'published' ? 'archived' : 'published')">{{ announcementUpdatingId === item.id ? '处理中' : item.status === 'published' ? '归档' : '发布' }}</button><button class="row-action" :disabled="announcementRecordSaving && announcementRecordEditingId === item.id" @tap="openAnnouncementRecordEditor(item)">编辑</button></template><text v-else class="row-unavailable-copy">暂未开放操作</text></view>
                  </view>
                </view>
              </view>
            </view>

            <view v-if="admissionDataset === 'major-catalog'" class="question-workspace major-catalog-workspace">
              <view class="workspace-heading major-catalog-workspace-heading">
                <view><view class="panel-title">专业目录逐条管理</view><view class="panel-subtitle">用户端已发布目录：全部目录、2026 年、2025 年</view></view>
                <view class="major-catalog-heading-tools">
                  <text>{{ formatCount(majorCatalogRecordCount) }} 条方向</text>
                  <button v-if="canBootstrapExistingAdmissionSnapshot" class="row-action" :disabled="admissionSnapshotBootstrapLoading" @tap="bootstrapExistingAdmissionSnapshot('major-catalog')">{{ admissionSnapshotBootstrapLoading ? '接入中…' : '接入现有数据' }}</button>
                </view>
              </view>
              <view class="scoreline-filter-toolbar major-catalog-filter-toolbar">
                <input v-model.trim="majorCatalogFilters.keyword" class="scoreline-filter-input scoreline-filter-search" maxlength="100" placeholder="搜索院校、专业、代码或研究方向" confirm-type="search" @confirm="applyMajorCatalogFilters" />
                <AdminSelect class="scoreline-filter-select" :options="majorCatalogYearFilterOptions" :value-index="majorCatalogYearFilterIndex" aria-label="目录年份筛选" @change="handleMajorCatalogYearFilterChange" />
                <AdminSelect class="scoreline-filter-select scoreline-filter-region-select" :options="majorCatalogRegionFilterOptions" :value-index="majorCatalogRegionFilterIndex" aria-label="地域查找" @change="handleMajorCatalogRegionFilterChange" />
                <AdminSelect class="scoreline-filter-select major-catalog-school-select" :options="majorCatalogSchoolFilterOptions" :value-index="majorCatalogSchoolFilterIndex" :disabled="!majorCatalogFilters.region" aria-label="招生院校筛选" @change="handleMajorCatalogSchoolFilterChange" />
                <AdminSelect class="scoreline-filter-select" :options="majorCatalogExamCodeFilterOptions" :value-index="majorCatalogExamCodeFilterIndex" aria-label="统考科目筛选" @change="handleMajorCatalogExamCodeFilterChange" />
                <button class="scoreline-filter-apply" @tap="applyMajorCatalogFilters">查找</button>
                <button v-if="majorCatalogFilters.catalog_year || majorCatalogFilters.keyword || majorCatalogFilters.region || majorCatalogFilters.school_name || majorCatalogFilters.exam_code" class="scoreline-filter-clear" @tap="clearMajorCatalogFilters">×</button>
              </view>
              <view class="question-table-wrap">
                <view class="question-table major-catalog-record-table">
                  <view class="major-catalog-record-grid table-head"><view>地区</view><view>院校及院系</view><view>专业及方向</view><view class="exam-code-cell">考试类别</view><view>学位 / 学习方式</view><view>操作</view></view>
                  <view v-if="majorCatalogRecordsLoading" class="table-state">正在读取专业目录…</view>
                  <view v-else-if="majorCatalogRecordsError" class="table-state error"><view>专业目录记录读取失败。</view><button @tap="loadMajorCatalogRecords">重新加载</button></view>
                  <view v-else-if="!majorCatalogRecords.length" class="table-state">当前筛选下没有专业目录记录</view>
                  <view v-else v-for="item in majorCatalogRecords" :key="item.id" class="major-catalog-record-grid major-catalog-record-row">
                    <view>{{ item.region }}</view>
                    <view><strong>{{ item.school_name }}</strong><text>{{ item.department_name || '未区分院系所' }}</text></view>
                    <view><strong>{{ item.program_name }}</strong><text>{{ item.program_code ? `${item.program_code} · ` : '' }}{{ item.direction_name || '不区分研究方向' }}</text></view>
                    <view class="exam-code-cell"><text class="exam-code-pill" :class="item.exam_code === 'Z002' ? 'is-z002' : 'is-z001'">{{ item.exam_code }}</text></view>
                    <view><strong>{{ item.degree || '—' }}</strong><text>{{ item.study_mode || '—' }}</text></view>
                    <view><button class="row-action" :disabled="majorCatalogRecordSaving && majorCatalogRecordEditingId === item.id" @tap="openMajorCatalogRecordEditor(item)">编辑</button></view>
                  </view>
                </view>
              </view>
              <view class="pagination-row scoreline-pagination"><view class="pagination-info">共 {{ formatCount(majorCatalogRecordCount) }} 条，每页 {{ majorCatalogRecordPageSize }} 条</view><view class="pagination-actions"><button :disabled="majorCatalogRecordPage <= 1 || majorCatalogRecordsLoading" @tap="changeMajorCatalogRecordPage(majorCatalogRecordPage - 1)">‹</button><view class="page-current">{{ majorCatalogRecordPage }}</view><view class="page-total">/ {{ majorCatalogRecordTotalPages }}</view><button :disabled="majorCatalogRecordPage >= majorCatalogRecordTotalPages || majorCatalogRecordsLoading" @tap="changeMajorCatalogRecordPage(majorCatalogRecordPage + 1)">›</button></view></view>
            </view>
        </section>

        <section v-if="activeSection === 'resources'" class="content-section operations-section">
          <AdminResourceManagement ref="resourceManagementRef" :preview="devPreviewMode" />
        </section>

        <section v-if="activeSection === 'homeOps'" class="content-section operations-section home-operations-content-section">
          <view v-if="homeContentEditorVisible" class="drawer-backdrop home-content-editor-backdrop" @tap="closeHomeContentEditor()">
            <view class="home-content-editor-modal" @tap.stop>
              <view class="workspace-heading home-editor-modal-heading"><view><view class="panel-title">{{ homeContentEditingId ? '编辑首页内容' : '新增首页内容' }}</view><view class="panel-subtitle">{{ homeContentSlotLabel(homeContentForm.slot) }} · {{ homeContentForm.status === 'published' ? '保存后会立即更新学生端。' : homeContentForm.status === 'archived' ? '可仅保存修改，或保存并重新上架。' : '可保存为草稿，或保存并上架。' }}</view></view><button class="drawer-close admin-modal-close" :disabled="homeContentSaving" @tap="closeHomeContentEditor">×</button></view>
              <scroll-view scroll-y class="home-editor-scroll">
                <view class="home-editor-content">
                  <view class="home-editor-grid">
              <view class="form-field full"><view class="form-label">标题</view><input v-model.trim="homeContentForm.title" class="form-input" maxlength="120" placeholder="填写用户端展示标题" /></view>
              <view class="form-field"><view class="form-label">排序</view><input v-model.number="homeContentForm.sort_order" class="form-input" type="number" /></view>
              <view class="form-field"><view class="form-label">{{ homeContentForm.slot === 'focus' ? '标签' : '来源' }}</view><input v-if="homeContentForm.slot === 'focus'" v-model.trim="homeContentForm.badge" class="form-input" maxlength="30" placeholder="例如：备考指南" /><input v-else v-model.trim="homeContentForm.source" class="form-input" maxlength="80" placeholder="例如：广东省教育考试院" /></view>
              <view class="form-field full"><view class="form-label">说明 / 摘要</view><textarea v-model.trim="homeContentForm.subtitle" class="form-textarea" maxlength="240" placeholder="填写简短说明" /></view>
              <view class="form-field"><view class="form-label">卡片标识</view><input v-model.trim="homeContentForm.cover_label" class="form-input" maxlength="40" placeholder="例如：准考证、官方公告" /></view>
              <view class="form-field"><view class="form-label">展示颜色</view><AdminSelect class="form-admin-select" :options="homeToneLabels" :value-index="homeToneIndex" aria-label="首页卡片颜色" @change="handleHomeToneChange" /></view>
              <view v-if="homeContentForm.slot === 'news'" class="form-field"><view class="form-label">展示日期</view><input v-model.trim="homeContentForm.display_date" class="form-input" type="date" /></view>
              <view class="form-field"><view class="form-label">点击去向</view><AdminSelect class="form-admin-select" :options="homeTargetLabels" :value-index="homeTargetIndex" aria-label="首页内容点击去向" @change="handleHomeTargetChange" /></view>
              <view v-if="!homeContentForm.route_key" class="form-field full"><view class="form-label">外部链接（选填）</view><input v-model.trim="homeContentForm.target_url" class="form-input" maxlength="1000" placeholder="https://...；留空则卡片不可点击" /></view>
              <view class="form-field"><view class="form-label">生效时间（选填）</view><input v-model="homeContentForm.starts_at" class="form-input" type="datetime-local" /></view>
              <view class="form-field"><view class="form-label">下线时间（选填）</view><input v-model="homeContentForm.ends_at" class="form-input" type="datetime-local" /></view>
                  </view>
                  <view class="home-editor-sample" :class="homeContentForm.tone"><small>{{ homeContentForm.slot === 'focus' ? '焦点轮播预览' : '考研资讯预览' }}</small><strong>{{ homeContentForm.title || '标题将在这里显示' }}</strong><text>{{ homeContentForm.slot === 'focus' ? (homeContentForm.subtitle || homeContentForm.badge || '补充简短说明') : `${homeContentForm.source || '信息来源'} · ${homeContentForm.display_date || '展示日期'}` }}</text></view>
                </view>
              </scroll-view>
              <view class="home-editor-actions">
                <button class="secondary-button" :disabled="homeContentSaving" @tap="closeHomeContentEditor">取消</button>
                <button
                  v-if="homeContentForm.status !== 'published'"
                  class="secondary-button home-editor-save-button"
                  :disabled="homeContentSaving || !homeContentForm.title"
                  @tap="saveHomeContent"
                >{{ homeContentSaving ? '保存中…' : '保存内容' }}</button>
                <button
                  class="primary-button"
                  :disabled="homeContentSaving || !homeContentForm.title"
                  @tap="homeContentForm.status === 'published' ? saveHomeContent() : saveHomeContent('published')"
                >{{ homeContentSaving ? '保存中…' : homeContentForm.status === 'published' ? '保存并更新' : homeContentForm.status === 'archived' ? '保存并重新上架' : '保存并上架' }}</button>
              </view>
            </view>
          </view>

          <view class="question-workspace home-live-preview-workspace">
            <view class="workspace-heading"><view><view class="panel-title">用户端当前展示</view><view class="panel-subtitle">以下内容按发布状态、生效时间和排序实时计算，与首页首屏规则一致。</view></view><view v-if="!homeContentLoading && !homeContentError" class="home-preview-counts"><text>轮播 {{ homeVisibleFocusItems.length }}/3</text><text>资讯 {{ homeVisibleNewsItems.length }}/3</text></view></view>
            <view v-if="homeContentLoading" class="table-state">正在计算用户端展示…</view>
            <view v-else-if="homeContentError" class="table-state error"><view>用户端展示预览暂时不可用。</view><button @tap="loadHomeContent">重新加载</button></view>
            <view v-else class="home-user-preview-grid">
              <view class="home-user-preview-panel"><view class="home-user-preview-label">焦点轮播</view><view v-if="homeVisibleFocusItems.length" class="home-preview-focus-list"><view v-for="item in homeVisibleFocusItems" :key="`preview-${item.id}`" class="home-preview-focus-item" :class="item.tone"><text>{{ item.badge || '官方资讯' }}</text><strong>{{ item.title }}</strong><small>{{ item.subtitle || item.cover_label || '—' }}</small></view></view><view v-else class="home-preview-empty">当前没有生效中的轮播内容</view></view>
              <view class="home-user-preview-panel"><view class="home-user-preview-label">考研资讯</view><view v-if="homeVisibleNewsItems.length" class="home-preview-news-list"><view v-for="item in homeVisibleNewsItems" :key="`preview-${item.id}`" class="home-preview-news-item"><view class="home-content-chip" :class="item.tone">{{ item.cover_label || '资讯' }}</view><view><strong>{{ item.title }}</strong><text>{{ item.source || '港研通' }} · {{ item.display_date || '—' }}</text></view></view></view><view v-else class="home-preview-empty">当前没有生效中的资讯内容</view></view>
            </view>
          </view>

          <view class="home-content-columns">
            <view class="question-workspace home-content-column">
              <view class="workspace-heading"><view><view class="panel-title">焦点轮播</view><view class="panel-subtitle">最多 {{ HOME_CONTENT_SLOT_LIMITS.focus }} 个 · 已发布 {{ homeFocusPublishedCount }}/{{ HOME_CONTENT_SLOT_LIMITS.focus }}</view></view><button class="row-action home-content-add-button" :disabled="homeFocusContentAtCapacity" @tap="openHomeContentEditor('focus')">{{ homeFocusContentAtCapacity ? `已满 ${HOME_CONTENT_SLOT_LIMITS.focus}/${HOME_CONTENT_SLOT_LIMITS.focus}` : '新增' }}</button></view>
              <view v-if="homeContentLoading" class="table-state">正在读取首页内容…</view>
              <view v-else-if="homeContentError" class="table-state error"><view>首页内容读取失败。</view><button @tap="loadHomeContent">重新加载</button></view>
              <view v-else-if="!homeFocusContentItems.length" class="table-state">暂未配置焦点轮播</view>
              <view v-else v-for="(item, index) in homeFocusContentItems" :key="item.id" class="home-content-row"><view class="home-content-chip" :class="item.tone">{{ item.cover_label || '焦点' }}</view><view class="home-content-copy"><strong>{{ item.title }}</strong><text>{{ homeContentListMeta(item, index) }}</text></view><text class="status-pill" :class="homeContentStatusClass(item)">{{ homeContentStatusText(item) }}</text><button v-if="item.status === 'published'" class="row-action" :disabled="homeContentStatusSavingId === item.id" @tap="archiveHomeContent(item)">{{ homeContentStatusSavingId === item.id ? '处理中' : '下架' }}</button><button v-else class="row-action home-content-publish-action" :disabled="homeContentStatusSavingId === item.id" @tap="publishHomeContent(item)">{{ homeContentStatusSavingId === item.id ? '处理中' : item.status === 'archived' ? '重新上架' : '上架' }}</button><button class="row-action" :disabled="homeContentStatusSavingId === item.id" @tap="openHomeContentEditor(item.slot, item)">编辑</button></view>
            </view>
            <view class="question-workspace home-content-column">
              <view class="workspace-heading"><view><view class="panel-title">港澳台考研资讯</view><view class="panel-subtitle">最多 {{ HOME_CONTENT_SLOT_LIMITS.news }} 个 · 已发布 {{ homeNewsPublishedCount }}/{{ HOME_CONTENT_SLOT_LIMITS.news }}</view></view><button class="row-action home-content-add-button" :disabled="homeNewsContentAtCapacity" @tap="openHomeContentEditor('news')">{{ homeNewsContentAtCapacity ? `已满 ${HOME_CONTENT_SLOT_LIMITS.news}/${HOME_CONTENT_SLOT_LIMITS.news}` : '新增' }}</button></view>
              <view v-if="homeContentLoading" class="table-state">正在读取首页内容…</view>
              <view v-else-if="homeContentError" class="table-state error"><view>首页内容读取失败。</view><button @tap="loadHomeContent">重新加载</button></view>
              <view v-else-if="!homeNewsContentItems.length" class="table-state">暂未配置考研资讯</view>
              <view v-else v-for="(item, index) in homeNewsContentItems" :key="item.id" class="home-content-row"><view class="home-content-chip" :class="item.tone">{{ item.cover_label || '资讯' }}</view><view class="home-content-copy"><strong>{{ item.title }}</strong><text>{{ homeContentListMeta(item, index) }}</text></view><text class="status-pill" :class="homeContentStatusClass(item)">{{ homeContentStatusText(item) }}</text><button v-if="item.status === 'published'" class="row-action" :disabled="homeContentStatusSavingId === item.id" @tap="archiveHomeContent(item)">{{ homeContentStatusSavingId === item.id ? '处理中' : '下架' }}</button><button v-else class="row-action home-content-publish-action" :disabled="homeContentStatusSavingId === item.id" @tap="publishHomeContent(item)">{{ homeContentStatusSavingId === item.id ? '处理中' : item.status === 'archived' ? '重新上架' : '上架' }}</button><button class="row-action" :disabled="homeContentStatusSavingId === item.id" @tap="openHomeContentEditor(item.slot, item)">编辑</button></view>
            </view>
          </view>
        </section>

        <section
          v-if="activeSection === 'questions' && !activeQuestionBank && !showGlobalQuestionList"
          class="content-section question-bank-section"
        >
          <view v-if="questionBanksLoading" class="bank-library-state">
            <view class="state-spinner"></view>
            <text>正在加载题库文件…</text>
          </view>
          <view v-else-if="questionBanksError" class="bank-library-state error">
            <view>题库文件加载失败，请检查网络或权限状态。</view>
            <button class="secondary-button" @tap="loadQuestionBanks">重新加载</button>
          </view>
          <view v-else class="bank-file-grid">
            <view v-if="canManageQuestions" class="bank-file-card bank-file-card--mock-exam">
              <view class="bank-file-icon" aria-hidden="true">
                <view class="bank-file-tab"></view>
                <view class="bank-file-face bank-file-face--mock-exam">
                  <text>卷</text>
                </view>
              </view>
              <view class="bank-file-main">
                <view class="bank-file-title-row">
                  <view class="bank-file-name">模拟卷</view>
                  <text class="bank-file-fixed-badge">固定组卷</text>
                </view>
                <view class="bank-file-date">可同时选用已发布和未发布题目</view>
              </view>
              <button class="bank-file-enter" @tap="openMockExamManagement">
                进入组卷 <text>→</text>
              </button>
            </view>

            <view
              v-for="bank in questionBanks"
              :key="bank.id"
              class="bank-file-card"
            >
              <view class="bank-file-icon" aria-hidden="true">
                <view class="bank-file-tab"></view>
                <view class="bank-file-face">
                  <text>题</text>
                </view>
              </view>
              <view class="bank-file-main">
                <view class="bank-file-title-row">
                  <view class="bank-file-name">{{ bank.name }}</view>
                  <button v-if="canManageQuestions" class="bank-rename-button" @tap.stop="openQuestionBankDialog('rename', bank)">
                    重命名
                  </button>
                </view>
                <view class="bank-file-date">最近修改：{{ formatDateTime(bank.updated_at) }}</view>
              </view>
              <button class="bank-file-enter" @tap="openQuestionBank(bank)">
                进入题库 <text>→</text>
              </button>
            </view>

            <button v-if="canManageQuestions" class="bank-file-card bank-file-create-card" @tap="openQuestionBankDialog('create')">
              <view class="bank-file-create-icon">＋</view>
              <view class="bank-file-create-title">新建题库</view>
            </button>
          </view>
        </section>

        <section
          v-if="activeSection === 'mockExams'"
          class="content-section mock-exam-management-section"
        >
          <AdminMockExamManagement ref="mockExamManagementRef" />
        </section>

        <section
          v-if="(activeSection === 'questions' && (activeQuestionBank || showGlobalQuestionList)) || activeSection === 'review'"
          class="content-section question-section"
        >
          <view v-if="activeSection !== 'review'" class="question-summary">
            <button
              v-for="item in summaryCards"
              :key="item.key"
              class="summary-card"
              :class="{ static: !item.interactive, interactive: item.interactive }"
              @tap="handleSummaryCardTap(item)"
            >
              <view class="summary-top">
                <view class="summary-icon summary-icon-asset" :class="item.tone">
                  <image class="summary-icon-image" :src="item.iconSrc" mode="aspectFit" />
                </view>
                <view class="summary-label">{{ item.label }}</view>
              </view>
              <view class="summary-value">{{ formatCount(item.value) }}</view>
            </button>
          </view>

          <view class="question-workspace" :class="{ compact: activeSection === 'review' }">
            <view class="workspace-heading">
              <view>
                <view class="panel-title">
                  {{ activeSection === 'review' ? '审核队列' : `${activeQuestionBank?.name || '全部题目'} · 题目列表` }}
                </view>
                <view class="panel-subtitle">
                  {{ activeSection === 'review'
                    ? '逐题检查内容，确认后发布或退回修改。'
                    : activeQuestionBank
                      ? canManageQuestions
                        ? '搜索、筛选、编辑并维护当前题库。'
                        : '可搜索和筛选当前题库；该账号仅拥有查看权限。'
                      : '按状态筛选并查看全部题库中的题目。' }}
                </view>
              </view>
              <view v-if="activeSection === 'review'" class="workspace-actions">
                <button
                  class="secondary-button publish-question-button review-start-button"
                  :disabled="questionsLoading || questionCount <= 0"
                  @tap="startReviewQueue"
                >
                  开始审核
                </button>
                <button class="primary-button publish-question-button" @tap="confirmPublishReviewQueue">
                  发布题目
                </button>
              </view>
            </view>

            <view class="filter-toolbar">
              <view class="search-shell">
                <view class="search-icon">
                  <image class="search-icon-image" src="/static/admin-icons/admin-search.svg" mode="aspectFit" />
                </view>
                <input
                  v-model.trim="filters.search"
                  class="search-input"
                  placeholder="搜索题干或题目 ID"
                  confirm-type="search"
                  @input="handleSearchInput"
                  @confirm="applyFilters"
                />
                <button v-if="filters.search" class="search-clear" @tap="clearSearch">×</button>
              </view>

              <AdminSelect
                class="question-admin-select"
                :options="subjectLabels"
                :value-index="selectedSubjectIndex"
                aria-label="科目筛选"
                @change="handleSubjectChange"
              />
              <AdminSelect
                class="question-admin-select"
                :options="moduleLabels"
                :value-index="selectedModuleIndex"
                aria-label="模块筛选"
                @change="handleModuleChange"
              />
              <AdminSelect
                class="question-admin-select narrow"
                :options="difficultyLabels"
                :value-index="selectedDifficultyIndex"
                aria-label="难度筛选"
                @change="handleDifficultyChange"
              />
              <AdminSelect
                v-if="activeSection !== 'review'"
                class="question-admin-select narrow"
                :options="statusLabels"
                :value-index="selectedStatusIndex"
                aria-label="状态筛选"
                @change="handleStatusChange"
              />
              <button
                v-if="activeSection !== 'review' && hasFilters"
                class="clear-filter-button"
                @tap="clearFilters"
              >清空</button>
            </view>

            <view v-if="canManageQuestions && activeSection !== 'review' && selectedIds.length" class="bulk-toolbar">
              <view class="bulk-copy">已选择 <text>{{ selectedIds.length }}</text> 道题</view>
              <view class="bulk-actions">
                <button
                  v-if="selectedBulkStatusAction"
                  class="bulk-button"
                  :class="selectedBulkStatusAction.tone"
                  @tap="bulkChangeStatus(selectedBulkStatusAction.status)"
                >
                  {{ selectedBulkStatusAction.label }}
                </button>
                <button class="bulk-cancel" @tap="selectedIds = []">取消选择</button>
                <button class="bulk-delete" @tap="deleteSelectedQuestions">删除</button>
              </view>
            </view>

            <view class="question-table-wrap">
              <view class="question-table">
                <view class="question-grid table-head">
                  <view class="check-cell">
                    <button v-if="canManageQuestions" class="check-box" :class="{ checked: allPageSelected }" @tap="toggleSelectPage">
                      {{ allPageSelected ? '✓' : '' }}
                    </button>
                  </view>
                  <view class="id-cell">题目 ID</view>
                  <view class="question-stem-cell">题干</view>
                  <view class="question-category-cell">科目 / 模块</view>
                  <view class="difficulty-cell">难度</view>
                  <view class="status-cell">状态</view>
                  <button
                    class="date-cell question-date-sort-button"
                    :aria-label="questionSortDirection === 'desc' ? '创建时间，当前倒序，点击切换为正序' : '创建时间，当前正序，点击切换为倒序'"
                    @tap="toggleQuestionDateSort"
                  >
                    <text>创建时间</text>
                    <text class="question-date-sort-icon">{{ questionSortDirection === 'asc' ? '▲' : '▼' }}</text>
                  </button>
                  <view class="action-cell">操作</view>
                </view>

                <view v-if="questionsLoading" class="table-state">正在加载题库…</view>
                <view v-else-if="questionLoadError" class="table-state error">
                  <view>题库加载失败，请检查网络或权限状态。</view>
                  <button @tap="loadQuestions">重新加载</button>
                </view>
                <view v-else-if="questions.length === 0" class="table-state">
                  <view>当前条件下没有题目</view>
                </view>
                <view
                  v-for="item in questions"
                  v-else
                  :key="item.id"
                  class="question-grid question-row"
                >
                  <view class="check-cell">
                    <button
                      v-if="canManageQuestions"
                      class="check-box"
                      :class="{ checked: isSelected(item.id) }"
                      @tap.stop="toggleSelection(item.id)"
                    >
                      {{ isSelected(item.id) ? '✓' : '' }}
                    </button>
                  </view>
                  <view class="id-cell mono">{{ shortId(item.id) }}</view>
                  <view class="question-stem-cell">
                    <MathText class="table-stem" :value="item.stem || '未填写题干'" />
                    <view class="table-answer">答案 {{ item.answer || '-' }} · {{ item.submodule || '未设置考点' }}</view>
                  </view>
                  <view class="question-category-cell">
                    <text class="table-subject">{{ item.subject || item.exam_code || '未分类' }}</text>
                    <text class="table-module">{{ item.module || '未分模块' }}</text>
                  </view>
                  <view class="difficulty-cell">
                    <view class="difficulty-dots">
                      <text
                        v-for="level in 5"
                        :key="level"
                        :class="{ active: level <= Number(item.difficulty || 0) }"
                      ></text>
                    </view>
                    <text class="difficulty-copy">{{ item.difficulty || '-' }}</text>
                  </view>
                  <view class="status-cell">
                    <text class="status-pill" :class="questionStatusTone(questionDisplayStatus(item))">
                      {{ questionStatusText(questionDisplayStatus(item)) }}
                    </text>
                  </view>
                  <view class="date-cell">{{ formatDate(item.created_at) }}</view>
                  <view class="action-cell">
                    <button class="row-action" @tap.stop="openEditDrawer(item, activeSection === 'review')">
                      {{ activeSection === 'review' ? '审核' : canManageQuestions ? '编辑' : '查看' }}
                    </button>
                  </view>
                </view>
              </view>
            </view>

            <view class="pagination-row">
              <view class="pagination-info">
                共 {{ formatCount(questionCount) }} 道，每页 {{ pageSize }} 道
              </view>
              <view class="pagination-actions">
                <button :disabled="currentPage <= 1" @tap="changePage(currentPage - 1)">‹</button>
                <view class="page-current">{{ currentPage }}</view>
                <view class="page-total">/ {{ totalPages }}</view>
                <button :disabled="currentPage >= totalPages" @tap="changePage(currentPage + 1)">›</button>
              </view>
            </view>
          </view>
        </section>

        <section v-if="activeSection === 'import'" class="content-section import-section">
          <QuestionImageImport
            ref="questionImageImportRef"
            embedded
            :sidebar-collapsed="sidebarCollapsed"
            :dev-preview="devPreviewMode"
            :portal-entry="true"
            :question-bank-id="importQuestionBankId"
            :question-bank-name="importQuestionBankName"
            @preview-mode-change="handleImportPreviewModeChange"
          />
        </section>
      </template>
    </main>

    <view v-if="admissionImportVisible" class="drawer-backdrop admission-import-backdrop" @tap="closeAdmissionImport()">
      <view class="admission-import-modal" @tap.stop>
        <view class="drawer-header">
          <view><view class="drawer-kicker">IMPORT DATA</view><view class="drawer-title">{{ currentAdmissionDataset.label }}导入</view></view>
          <button class="drawer-close admin-modal-close" :disabled="admissionCommitting || admissionPreviewLoading" @tap="closeAdmissionImport()">×</button>
        </view>
        <scroll-view scroll-y class="admission-import-scroll">
          <view class="admission-import-content">
            <view class="admission-import-actions">
              <view class="admission-file-picker">
                <input ref="admissionFileInputRef" class="admission-file-input" type="file" accept=".xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" @change="handleAdmissionFileChange" />
                <button class="admission-file-picker-trigger" type="button" @click="openAdmissionFilePicker"><text>{{ admissionFileName || '选择标准 .xlsx 文件' }}</text></button>
              </view>
              <button class="secondary-button" :disabled="!admissionFile || admissionPreviewLoading" @tap="previewAdmissionImport">{{ admissionPreviewLoading ? '检查中…' : '导入预览' }}</button>
              <button class="primary-button" :disabled="!canCommitAdmissionImport || admissionCommitting" @tap="commitAdmissionImport">{{ admissionCommitting ? '导入中…' : '确认导入' }}</button>
              <button class="header-import-button template admission-template-button" @tap="downloadAdmissionTemplate">下载模板</button>
            </view>
            <view v-if="admissionPreview" class="admission-preview-summary" :class="{ error: Number(admissionPreview.invalid_rows || 0) > 0 }"><view><strong>{{ admissionPreview.valid_rows || 0 }}</strong><text> 行可提交</text></view><view><strong>{{ admissionPreview.invalid_rows || 0 }}</strong><text> 行需修正</text></view><view><text>文件校验码 {{ String(admissionPreview.source_sha256 || '').slice(0, 12) }}</text></view></view>
            <view v-if="admissionPreview?.preview_items?.length" class="admission-preview-list"><view v-for="item in admissionPreview.preview_items.slice(0, 6)" :key="`${item.source_row}-${item.title || item.school_name || ''}`" class="admission-preview-row" :class="{ invalid: item.valid === false }"><text>第 {{ item.source_row || '—' }} 行</text><text>{{ item.title || item.school_name || '字段检查' }}</text><text>{{ item.valid === false ? (item.errors || []).join('；') : '字段有效' }}</text></view></view>
          </view>
        </scroll-view>
      </view>
    </view>

    <view v-if="scorelineRecordEditorVisible" class="drawer-backdrop scoreline-editor-backdrop" @tap="closeScorelineRecordEditor">
      <view class="scoreline-editor-modal" @tap.stop>
        <view class="drawer-header">
          <view><view class="drawer-kicker">SCORELINE RECORD</view><view class="drawer-title">编辑分数线</view></view>
          <button class="drawer-close admin-modal-close" :disabled="scorelineRecordSaving" @tap="closeScorelineRecordEditor">×</button>
        </view>
        <scroll-view scroll-y class="scoreline-editor-scroll">
          <view class="scoreline-editor-content">
            <view class="scoreline-editor-grid">
              <view class="form-field"><view class="form-label">年份</view><input v-model.trim="scorelineRecordForm.score_year" class="form-input" type="number" maxlength="4" placeholder="例如 2026" /></view>
              <view class="form-field"><view class="form-label">地区</view><input v-model.trim="scorelineRecordForm.region" class="form-input" maxlength="60" placeholder="例如 广东" /></view>
              <view class="form-field"><view class="form-label">院校</view><input v-model.trim="scorelineRecordForm.school_name" class="form-input" maxlength="160" placeholder="填写院校名称" /></view>
              <view class="form-field"><view class="form-label">院系（选填）</view><input v-model.trim="scorelineRecordForm.unit_name" class="form-input" maxlength="160" placeholder="例如 研究生院" /></view>
              <view class="form-field"><view class="form-label">分数线内容</view><input v-model.trim="scorelineRecordForm.score_raw" class="form-input" maxlength="1000" placeholder="例如 90 或各专业分数线不同" /></view>
              <view class="form-field"><view class="form-label">数据状态</view><AdminSelect class="form-admin-select" :options="scorelineKindLabels" :value-index="scorelineKindIndex" aria-label="分数线数据状态" @change="handleScorelineKindChange" /></view>
              <view class="form-field"><view class="form-label">来源链接（选填）</view><input v-model.trim="scorelineRecordForm.source_url" class="form-input" maxlength="1000" placeholder="https://..." /></view>
              <view class="form-field"><view class="form-label">来源备注（选填）</view><input v-model.trim="scorelineRecordForm.source_note" class="form-input" maxlength="2000" placeholder="填写院校、公告或核验说明" /></view>
            </view>
          </view>
        </scroll-view>
        <view class="drawer-footer"><button class="footer-button secondary" :disabled="scorelineRecordSaving" @tap="closeScorelineRecordEditor">取消</button><button class="footer-button primary" :disabled="scorelineRecordSaving" @tap="saveScorelineRecord">{{ scorelineRecordSaving ? '保存中…' : '保存修改' }}</button></view>
      </view>
    </view>

    <view v-if="announcementRecordEditorVisible" class="drawer-backdrop scoreline-editor-backdrop" @tap="closeAnnouncementRecordEditor">
      <view class="scoreline-editor-modal announcement-editor-modal" @tap.stop>
        <view class="drawer-header">
          <view><view class="drawer-kicker">SCHOOL ANNOUNCEMENT</view><view class="drawer-title">编辑公告</view></view>
          <button class="drawer-close admin-modal-close" :disabled="announcementRecordSaving" @tap="closeAnnouncementRecordEditor">×</button>
        </view>
        <scroll-view scroll-y class="scoreline-editor-scroll">
          <view class="scoreline-editor-content">
            <view class="announcement-editor-grid">
              <view class="form-field"><view class="form-label">年份</view><input v-model.trim="announcementRecordForm.notice_year" class="form-input" type="number" maxlength="4" placeholder="例如 2026" /></view>
              <view class="form-field"><view class="form-label">地区</view><input v-model.trim="announcementRecordForm.region" class="form-input" maxlength="60" placeholder="例如 广东" /></view>
              <view class="form-field"><view class="form-label">院校</view><input v-model.trim="announcementRecordForm.school_name" class="form-input" maxlength="160" placeholder="填写院校名称" /></view>
              <view class="form-field"><view class="form-label">院系（选填）</view><input v-model.trim="announcementRecordForm.unit_name" class="form-input" maxlength="160" placeholder="例如 研究生院" /></view>
              <view class="form-field"><view class="form-label">公告类型</view><AdminSelect class="form-admin-select" :options="announcementRecordNoticeTypeOptions" :value-index="announcementRecordNoticeTypeIndex" aria-label="公告类型" @change="handleAnnouncementRecordNoticeTypeChange" /></view>
              <view class="form-field"><view class="form-label">发布日期（选填）</view><input v-model.trim="announcementRecordForm.notice_date" class="form-input" type="date" /></view>
              <view class="form-field full"><view class="form-label">公告标题</view><input v-model.trim="announcementRecordForm.title" class="form-input" maxlength="500" placeholder="填写公告标题" /></view>
              <view class="form-field full"><view class="form-label">摘要（选填）</view><textarea v-model.trim="announcementRecordForm.summary" class="form-textarea" maxlength="5000" placeholder="填写简短摘要" /></view>
              <view class="form-field full"><view class="form-label">原文链接（选填）</view><input v-model.trim="announcementRecordForm.source_url" class="form-input" maxlength="1000" placeholder="https://..." /></view>
              <view class="form-field full"><view class="form-label">公告正文（选填）</view><textarea v-model.trim="announcementRecordForm.content_text" class="form-textarea announcement-content-textarea" maxlength="100000" placeholder="填写或修正公告正文" /></view>
            </view>
          </view>
        </scroll-view>
        <view class="drawer-footer"><button class="footer-button secondary" :disabled="announcementRecordSaving" @tap="closeAnnouncementRecordEditor">取消</button><button class="footer-button primary" :disabled="announcementRecordSaving" @tap="saveAnnouncementRecord">{{ announcementRecordSaving ? '保存中…' : '保存修改' }}</button></view>
      </view>
    </view>

    <view v-if="majorCatalogRecordEditorVisible" class="drawer-backdrop scoreline-editor-backdrop" @tap="closeMajorCatalogRecordEditor">
      <view class="scoreline-editor-modal major-catalog-editor-modal" @tap.stop>
        <view class="drawer-header">
          <view><view class="drawer-kicker">MAJOR CATALOG</view><view class="drawer-title">编辑专业目录</view></view>
          <button class="drawer-close admin-modal-close" :disabled="majorCatalogRecordSaving" @tap="closeMajorCatalogRecordEditor">×</button>
        </view>
        <scroll-view scroll-y class="scoreline-editor-scroll">
          <view class="scoreline-editor-content">
            <view class="major-catalog-editor-grid">
              <view class="form-field"><view class="form-label">目录年份</view><input :value="majorCatalogRecordYear" class="form-input" disabled /></view>
              <view class="form-field"><view class="form-label">地区</view><input v-model.trim="majorCatalogRecordForm.region" class="form-input" maxlength="60" placeholder="例如 广东" /></view>
              <view class="form-field"><view class="form-label">院校</view><input v-model.trim="majorCatalogRecordForm.school_name" class="form-input" maxlength="160" placeholder="填写院校名称" /></view>
              <view class="form-field"><view class="form-label">院系</view><input v-model.trim="majorCatalogRecordForm.department_name" class="form-input" maxlength="300" placeholder="例如 文学院" /></view>
              <view class="form-field"><view class="form-label">专业名称</view><input v-model.trim="majorCatalogRecordForm.program_name" class="form-input" maxlength="300" placeholder="填写专业名称" /></view>
              <view class="form-field"><view class="form-label">专业代码（选填）</view><input v-model.trim="majorCatalogRecordForm.program_code" class="form-input" maxlength="60" placeholder="例如 050101" /></view>
              <view class="form-field"><view class="form-label">研究方向</view><input v-model.trim="majorCatalogRecordForm.direction_name" class="form-input" maxlength="500" placeholder="例如 不区分研究方向" /></view>
              <view class="form-field"><view class="form-label">导师（选填）</view><input v-model.trim="majorCatalogRecordForm.tutor" class="form-input" maxlength="300" placeholder="填写导师姓名" /></view>
              <view class="form-field"><view class="form-label">考试类别</view><AdminSelect class="form-admin-select" :options="majorCatalogExamCodeEditOptions" :value-index="majorCatalogExamCodeEditIndex" aria-label="考试类别" @change="handleMajorCatalogExamCodeChange" /></view>
              <view class="form-field"><view class="form-label">学位（选填）</view><input v-model.trim="majorCatalogRecordForm.degree" class="form-input" maxlength="100" placeholder="例如 硕士" /></view>
              <view class="form-field"><view class="form-label">学习方式（选填）</view><input v-model.trim="majorCatalogRecordForm.study_mode" class="form-input" maxlength="100" placeholder="例如 全日制" /></view>
            </view>
          </view>
        </scroll-view>
        <view class="drawer-footer"><button class="footer-button secondary" :disabled="majorCatalogRecordSaving" @tap="closeMajorCatalogRecordEditor">取消</button><button class="footer-button primary" :disabled="majorCatalogRecordSaving" @tap="saveMajorCatalogRecord">{{ majorCatalogRecordSaving ? '保存中…' : '保存修改' }}</button></view>
      </view>
    </view>

    <view v-if="portalUserDetailVisible" class="drawer-backdrop portal-user-detail-backdrop" @tap="closePortalUserDetail">
      <view class="portal-user-detail-modal" @tap.stop>
        <view class="drawer-header"><view><view class="drawer-kicker">USER PROFILE</view><view class="drawer-title">用户详情</view></view><button class="drawer-close admin-modal-close" :disabled="portalUserSaving" @tap="closePortalUserDetail">×</button></view>
        <view v-if="portalUserDetailLoading" class="drawer-state">正在读取用户详情…</view>
        <scroll-view v-else-if="portalUserDetail" scroll-y class="portal-user-detail-scroll"><view class="portal-user-detail-content"><view class="portal-user-profile-card"><view class="portal-user-avatar large">{{ portalUserDetail.profile?.nickname?.slice(0, 1) || portalUserDetail.profile?.email?.slice(0, 1) || '研' }}</view><view><view class="portal-user-profile-name">{{ portalUserDetail.profile?.nickname || '未设置昵称' }}</view><view class="portal-user-profile-contact">{{ portalUserDetail.profile?.email || portalUserDetail.profile?.phone || shortId(portalUserDetail.profile?.id) }}</view><view class="portal-user-profile-meta">注册于 {{ formatDateTime(portalUserDetail.profile?.created_at) }}</view></view><text class="status-pill" :class="portalUserDetail.profile?.disabled_at ? 'archived' : 'published'">{{ portalUserDetail.profile?.disabled_at ? '已停用' : '正常' }}</text></view><view class="portal-user-detail-stats"><view><text>累计作答</text><strong>{{ formatCount(portalUserDetail.answer_summary?.total) }}</strong></view><view><text>答对</text><strong>{{ formatCount(portalUserDetail.answer_summary?.correct) }}</strong></view><view><text>正确率</text><strong>{{ formatAccuracy(portalUserDetail.answer_summary?.accuracy) }}</strong></view><view><text>错题</text><strong>{{ formatCount(portalUserDetail.answer_summary?.wrong_question_count || portalUserDetail.answer_summary?.wrong) }}</strong></view></view><view class="portal-user-detail-heading">各科正确率</view><view v-if="portalUserDetail.subject_accuracy?.length" class="portal-subject-accuracy-list"><view v-for="item in portalUserDetail.subject_accuracy" :key="item.subject" class="portal-subject-accuracy-row"><view><strong>{{ item.subject }}</strong><text>{{ formatCount(item.total) }} 题</text></view><view class="portal-subject-accuracy-value" :class="accuracyTone(item.accuracy)">{{ formatAccuracy(item.accuracy) }}</view></view></view><view v-else class="portal-detail-empty">尚无可统计的学科作答数据</view><view class="portal-user-detail-heading">最近作答</view><view v-if="portalUserDetail.recent_answers?.length" class="portal-answer-list"><view v-for="item in portalUserDetail.recent_answers.slice(0, 8)" :key="item.id" class="portal-answer-row"><text :class="item.is_correct ? 'is-correct' : 'is-wrong'">{{ item.is_correct ? '正确' : '错误' }}</text><view><strong>{{ item.subject || '题目' }}</strong><text>{{ formatMathText(item.stem || item.questions?.stem || '—') }}</text></view><time>{{ formatDateTime(item.created_at) }}</time></view></view><view v-else class="portal-detail-empty">暂无作答记录</view></view></scroll-view>
        <view class="drawer-footer"><button class="footer-button secondary" :disabled="portalUserSaving" @tap="closePortalUserDetail">关闭</button><button v-if="portalUserDetail?.profile" class="footer-button" :class="portalUserDetail.profile.disabled_at ? 'primary' : 'danger'" :disabled="portalUserSaving" @tap="togglePortalUserDisabled(portalUserDetail.profile)">{{ portalUserDetail.profile.disabled_at ? '恢复账号' : '停用账号' }}</button></view>
      </view>
    </view>

    <view v-if="portalMembershipVisible" class="drawer-backdrop portal-membership-backdrop" @tap="closePortalUserMembership">
      <view class="portal-membership-modal" @tap.stop>
        <view class="drawer-header"><view><view class="drawer-kicker">MEMBERSHIP MANAGEMENT</view><view class="drawer-title">会员管理</view></view><button class="drawer-close admin-modal-close" :disabled="portalMembershipSaving" @tap="closePortalUserMembership">×</button></view>
        <view v-if="portalMembershipLoading" class="drawer-state">正在读取会员信息…</view>
        <scroll-view v-else-if="portalMembershipDetail?.profile" scroll-y class="portal-membership-scroll"><view class="portal-membership-content"><view class="portal-user-profile-card"><view class="portal-user-avatar large">{{ portalMembershipDetail.profile?.nickname?.slice(0, 1) || portalMembershipDetail.profile?.email?.slice(0, 1) || '研' }}</view><view><view class="portal-user-profile-name">{{ portalMembershipDetail.profile?.nickname || '未设置昵称' }}</view><view class="portal-user-profile-contact">{{ portalMembershipDetail.profile?.email || portalMembershipDetail.profile?.phone || shortId(portalMembershipDetail.profile?.id) }}</view></view></view><view class="portal-membership-summary"><view><text>会员状态</text><strong>{{ portalUserMembershipLabel(portalMembershipDetail.profile) }}</strong></view><view><text>当前到期日</text><strong>{{ portalMembershipDetail.profile?.membership_expires_at ? formatDateTime(portalMembershipDetail.profile.membership_expires_at) : '—' }}</strong></view></view><view class="portal-user-detail-heading">会员操作</view><view class="portal-membership-actions"><button class="portal-membership-action cancel" :disabled="portalMembershipSaving || !isPortalUserMembershipActive(portalMembershipDetail.profile)" @tap="cancelPortalUserMembership">{{ portalMembershipAction === 'cancel' ? '处理中…' : '取消会员' }}</button><button class="portal-membership-action" :disabled="portalMembershipSaving" @tap="renewPortalUserMembership(1)">{{ portalMembershipAction === 'renew-1' ? '处理中…' : '续费 1 个月' }}</button><button class="portal-membership-action" :disabled="portalMembershipSaving" @tap="renewPortalUserMembership(4)">{{ portalMembershipAction === 'renew-4' ? '处理中…' : '续费一个季度（4 个月）' }}</button></view><view class="portal-user-detail-heading">会员充值记录</view><view v-if="portalMembershipDetail.membership_orders?.length" class="portal-membership-order-list"><view v-for="order in portalMembershipDetail.membership_orders" :key="order.id" class="portal-membership-order-row"><view><strong>{{ membershipOrderPlanLabel(order) }}</strong><text>{{ membershipOrderProviderLabel(order) }}</text></view><view class="portal-membership-order-meta"><text class="membership-order-status" :class="membershipOrderStatusTone(order)">{{ membershipOrderStatusLabel(order) }}</text><strong>{{ membershipOrderAmount(order) }}</strong><time>{{ formatDateTime(order.paid_at || order.created_at) }}</time></view></view></view><view v-else class="portal-detail-empty">该用户暂无会员充值记录</view></view></scroll-view>
      </view>
    </view>

    <view v-if="communityDetailVisible" class="drawer-backdrop community-detail-backdrop" @tap="closeCommunityPostDetail">
      <view class="community-detail-modal" @tap.stop>
        <view class="drawer-header community-detail-header">
          <view>
            <view class="drawer-kicker">COMMUNITY CONTENT</view>
            <view class="drawer-title">帖子详情</view>
          </view>
          <button class="drawer-close admin-modal-close" :disabled="communitySaving" @tap="closeCommunityPostDetail">×</button>
        </view>

        <view v-if="communityDetailLoading" class="drawer-state">正在读取帖子详情…</view>
        <scroll-view v-else-if="communityDetail?.post" scroll-y class="community-detail-scroll">
          <view class="community-detail-content">
            <view class="community-detail-meta">
              <view class="community-detail-author">
                <view class="community-detail-avatar">
                  {{ communityDetail.post.author_avatar || communityDetail.post.author_name?.slice(0, 1) || '研' }}
                </view>
                <view>
                  <view class="community-detail-author-name">{{ communityDetail.post.author_name || '研友' }}</view>
                  <view class="community-detail-author-id">用户 ID {{ shortId(communityDetail.post.author_id) }}</view>
                </view>
              </view>
              <view class="community-detail-status">
                <text class="status-pill" :class="communityDetail.post.is_published ? 'published' : 'archived'">
                  {{ communityPostStatusText(communityDetail.post.is_published) }}
                </text>
                <text>{{ formatDateTime(communityDetail.post.created_at) }}</text>
              </view>
            </view>

            <view class="community-detail-stat-grid">
              <view><text>浏览</text><strong>{{ formatCount(communityDetail.post.view_count) }}</strong></view>
              <view><text>点赞</text><strong>{{ formatCount(communityDetail.post.like_count) }}</strong></view>
              <view><text>评论</text><strong>{{ formatCount(communityDetail.post.comment_count) }}</strong></view>
              <view><text>分类</text><strong>{{ communityDetail.post.category || '未分类' }}</strong></view>
            </view>

            <view class="community-detail-topic-row">
              <text>{{ communityPostTypeText(communityDetail.post.post_type) }}</text>
              <text>{{ communityDetail.post.category || '未分类' }}</text>
            </view>
            <view class="community-detail-title">{{ communityDetail.post.title || '未填写标题' }}</view>
            <view class="community-detail-body">{{ communityDetail.post.content || '未填写正文' }}</view>

            <view v-if="communityDetail.post.media?.length" class="community-detail-media-grid">
              <view
                v-for="media in communityDetail.post.media"
                :key="media.imageUrl || media.image_url || `${media.kicker}-${media.title}`"
                class="community-detail-media-item"
              >
                <image
                  v-if="media.imageUrl || media.image_url"
                  :src="media.imageUrl || media.image_url"
                  mode="aspectFill"
                />
                <view v-else class="community-detail-media-fallback">
                  <text>{{ media.title || '帖子附件' }}</text>
                </view>
              </view>
            </view>

            <view class="community-detail-comments-heading">
              评论 <text>{{ formatCount(communityDetail.comments?.length) }}</text>
            </view>
            <view v-if="communityDetail.comments?.length" class="community-detail-comments">
              <view v-for="comment in communityDetail.comments" :key="comment.id" class="community-detail-comment">
                <view class="community-comment-avatar">{{ comment.author_avatar || comment.author_name?.slice(0, 1) || '研' }}</view>
                <view class="community-comment-main">
                  <view class="community-comment-topline">
                    <text>{{ comment.author_name || '研友' }}</text>
                    <text>{{ formatDateTime(comment.created_at) }}</text>
                  </view>
                  <view class="community-comment-copy">{{ comment.content }}</view>
                </view>
                <view class="community-comment-likes">赞 {{ formatCount(comment.like_count) }}</view>
                <view class="community-comment-management">
                  <text class="community-comment-status" :class="comment.is_published !== false ? 'published' : 'archived'">{{ comment.is_published !== false ? '展示中' : '已下架' }}</text>
                  <button :class="{ restore: comment.is_published === false }" :disabled="communitySaving" @tap.stop="toggleCommunityCommentVisibility(communityDetail.post, comment)">{{ comment.is_published !== false ? '下架' : '恢复' }}</button>
                </view>
              </view>
            </view>
            <view v-else class="community-detail-empty-comments">暂无评论</view>
          </view>
        </scroll-view>

        <view class="drawer-footer community-detail-footer">
          <button class="footer-button secondary" :disabled="communitySaving" @tap="closeCommunityPostDetail">关闭</button>
          <button
            v-if="communityDetail?.post"
            class="footer-button"
            :class="communityDetail.post.is_published ? 'danger' : 'primary'"
            :disabled="communitySaving"
            @tap="toggleCommunityPostVisibility(communityDetail.post)"
          >
            {{ communityDetail.post.is_published ? '下架帖子' : '恢复帖子' }}
          </button>
        </view>
      </view>
    </view>

    <view
      v-if="drawerVisible"
      class="drawer-backdrop"
      :class="{ 'review-modal-backdrop': drawerMode === 'review' }"
      @tap="requestCloseDrawer"
    >
      <view class="question-drawer" :class="{ 'review-modal': drawerMode === 'review' }" @tap.stop>
        <view class="drawer-header">
          <view>
            <view class="drawer-kicker">{{ drawerKicker }}</view>
            <view class="drawer-title">{{ drawerTitle }}</view>
          </view>
          <button class="drawer-close admin-modal-close" @tap="requestCloseDrawer">×</button>
        </view>

        <view v-if="drawerLoading" class="drawer-state">正在读取题目详情…</view>
        <scroll-view v-else scroll-y class="drawer-scroll">
          <view class="drawer-content">
            <view class="drawer-meta-grid">
              <view class="form-field">
                <view class="form-label">科目</view>
                <AdminSelect
                  class="form-admin-select"
                  :options="editorSubjectLabels"
                  :value-index="editorSubjectIndex"
                  :disabled="!canManageQuestions"
                  aria-label="科目"
                  @change="handleEditorSubjectChange"
                />
              </view>
              <view class="form-field">
                <view class="form-label">模块</view>
                <AdminSelect
                  class="form-admin-select"
                  :options="editorModuleLabels"
                  :value-index="editorModuleIndex"
                  :disabled="!canManageQuestions"
                  aria-label="模块"
                  @change="handleEditorModuleChange"
                />
              </view>
            </view>

            <view class="drawer-meta-grid">
              <view class="form-field">
                <view class="form-label">考点</view>
                <AdminSelect
                  class="form-admin-select"
                  :options="editorSubmoduleLabels"
                  :value-index="editorSubmoduleIndex"
                  :disabled="!canManageQuestions"
                  aria-label="考点"
                  @change="handleEditorSubmoduleChange"
                />
              </view>
              <view class="form-field">
                <view class="form-label">难度</view>
                <view class="difficulty-picker">
                  <button
                    v-for="level in 5"
                    :key="level"
                    :class="{ active: Number(form.difficulty) === level }"
                    :disabled="!canManageQuestions"
                    @tap="form.difficulty = level"
                  >{{ level }}</button>
                </view>
              </view>
            </view>

            <MathQuestionPaperPreview
              v-if="form.subject === '数学基础'"
              class="drawer-math-preview"
              :stem="form.stem"
              :option-a="form.option_a"
              :option-b="form.option_b"
              :option-c="form.option_c"
              :option-d="form.option_d"
              :answer="form.answer"
              :explanation="form.explanation"
            />

            <view class="form-field full">
              <view class="form-heading">
                <view class="form-label">题干</view>
                <text class="required-tag">必填</text>
              </view>
              <textarea v-model.trim="form.stem" class="form-textarea stem" :disabled="!canManageQuestions" placeholder="请输入完整题干" />
            </view>

            <view class="form-field full">
              <view class="form-heading">
                <view class="form-label">选项与答案</view>
                <text class="form-hint">点击字母设置正确答案</text>
              </view>
              <view class="option-editor">
                <view
                  v-for="option in answerOptions"
                  :key="option"
                  class="option-row"
                  :class="{ correct: form.answer === option }"
                >
                  <button class="answer-selector" :disabled="!canManageQuestions" @tap="form.answer = option">{{ option }}</button>
                  <input
                    v-model.trim="form[`option_${option.toLowerCase()}`]"
                    class="option-input"
                    :disabled="!canManageQuestions"
                    :placeholder="`${option} 选项`"
                  />
                </view>
              </view>
            </view>

            <view class="form-field full">
              <view class="form-heading">
                <view class="form-label">解析</view>
                <text class="form-hint">建议包含答案理由与易错点</text>
              </view>
              <textarea v-model.trim="form.explanation" class="form-textarea explanation" :disabled="!canManageQuestions" placeholder="请输入题目解析" />
            </view>

            <view v-if="drawerMode === 'review'" class="form-field full review-note-field">
              <view class="form-label">审核备注</view>
              <textarea v-model.trim="form.review_note" class="form-textarea note" :disabled="!canManageQuestions" placeholder="退回修改时请写明问题" />
            </view>

            <view v-if="form.id" class="question-meta-note">
              <text>ID {{ form.id }}</text>
              <text>当前状态：{{ questionStatusText(questionDisplayStatus(form)) }}</text>
            </view>
          </view>
        </scroll-view>

        <view class="drawer-footer">
          <button v-if="!canManageQuestions" class="footer-button secondary" @tap="requestCloseDrawer">关闭</button>
          <button v-if="canManageQuestions && drawerMode === 'review'" class="footer-button warning" :disabled="saving" @tap="markNeedsChanges">
            需要修改
          </button>
          <button
            v-if="canManageQuestions && drawerMode === 'edit' && form.id"
            class="footer-button select"
            :class="{ active: isSelected(form.id) }"
            :disabled="saving"
            @tap="toggleCurrentQuestionSelection"
          >
            {{ isSelected(form.id) ? '已选中' : '选中' }}
          </button>
          <button v-if="canManageQuestions && drawerMode !== 'create'" class="footer-button secondary" :disabled="saving" @tap="saveQuestionEdits">
            保存修改
          </button>
          <button v-if="canManageQuestions && drawerMode === 'create'" class="footer-button secondary" :disabled="saving" @tap="createQuestion('pending')">
            存入待审核
          </button>
          <button v-if="canManageQuestions && drawerMode === 'review'" class="footer-button primary" :disabled="saving" @tap="approveAndPublish">
            通过并发布
          </button>
          <button v-else-if="canManageQuestions && drawerMode === 'create'" class="footer-button primary" :disabled="saving" @tap="createQuestion('publish')">
            直接发布
          </button>
          <button
            v-else-if="canManageQuestions"
            class="footer-button"
            :class="questionDisplayStatus(form) === 'active' ? 'danger' : 'primary'"
            :disabled="saving"
            @tap="toggleCurrentQuestionStatus"
          >
            {{ questionDisplayStatus(form) === 'active' ? '下架题目' : '发布题目' }}
          </button>
        </view>
      </view>
    </view>

    <view
      v-if="publishQuestionBankDialogVisible"
      class="bank-dialog-backdrop"
      @tap="closePublishQuestionBankDialog"
    >
      <view class="bank-dialog publish-question-dialog" @tap.stop>
        <view class="bank-dialog-kicker">PUBLISH QUESTIONS</view>
        <view class="bank-dialog-title">选择发布题库</view>
        <view class="bank-dialog-copy">
          选择题库后先统计待发布题目数量；确认前还会进行一次明确提示。
        </view>

        <view v-if="questionBanksLoading" class="publish-bank-state">
          <view class="state-spinner"></view>
          <text>正在加载题库文件…</text>
        </view>
        <view v-else-if="questionBanksError" class="publish-bank-state error">
          <text>题库文件加载失败，请稍后重试。</text>
          <button class="secondary-button" @tap="loadQuestionBanks">重新加载</button>
        </view>
        <view v-else-if="questionBanks.length === 0" class="publish-bank-state">
          <text>暂无可发布的题库，请先在题目管理中新建题库。</text>
        </view>
        <view v-else class="publish-bank-grid">
          <button
            v-for="bank in questionBanks"
            :key="bank.id"
            class="publish-bank-option"
            :class="{ selected: publishQuestionBankId === bank.id }"
            @tap="selectPublishQuestionBank(bank)"
          >
            <view class="publish-bank-folder" aria-hidden="true">
              <view class="publish-bank-folder-tab"></view>
              <text>题</text>
            </view>
            <view class="publish-bank-meta">
              <view class="publish-bank-name">{{ bank.name }}</view>
              <view class="publish-bank-date">最近修改：{{ formatDateTime(bank.updated_at) }}</view>
            </view>
            <view class="publish-bank-check">{{ publishQuestionBankId === bank.id ? '✓' : '' }}</view>
          </button>
        </view>

        <view v-if="publishQuestionBankId" class="publish-preview" :class="{ error: publishPendingPreviewError }">
          <text v-if="publishPendingPreviewLoading">正在统计待发布题目数量…</text>
          <template v-else-if="publishPendingPreviewError">
            <text>待发布数量获取失败，请重新统计后再确认。</text>
            <button class="publish-preview-retry" @tap="loadPublishPendingPreview">重新统计</button>
          </template>
          <template v-else-if="publishPendingPreview">
            <text>
              将发布 <text class="publish-preview-count">{{ formatCount(publishPendingPreview.pending_count) }}</text>
              道待审核题目，发布后将立即对用户可见。
            </text>
          </template>
        </view>

        <view class="bank-dialog-actions">
          <button
            class="bank-dialog-cancel"
            :disabled="publishingQuestions"
            @tap="closePublishQuestionBankDialog"
          >
            取消
          </button>
          <button
            class="bank-dialog-confirm"
            :disabled="publishingQuestions || !publishQuestionBankId || publishPendingPreviewLoading || publishPendingPreviewError || !publishPendingPreview"
            @tap="publishPendingQuestionsToBank"
          >
            {{ publishingQuestions ? '发布中…' : '确认发布' }}
          </button>
        </view>
      </view>
    </view>

    <view v-if="questionBankDialogVisible" class="bank-dialog-backdrop" @tap="closeQuestionBankDialog">
      <view class="bank-dialog" @tap.stop>
        <view class="bank-dialog-kicker">
          {{ questionBankDialogMode === 'create' ? 'NEW QUESTION BANK' : 'RENAME QUESTION BANK' }}
        </view>
        <view class="bank-dialog-title">
          {{ questionBankDialogMode === 'create' ? '新建题库' : '重命名题库' }}
        </view>
        <input
          v-model.trim="questionBankNameDraft"
          class="bank-dialog-input"
          maxlength="80"
          placeholder="请输入题库名称"
          confirm-type="done"
          @confirm="saveQuestionBankDialog"
        />
        <view class="bank-dialog-actions">
          <button class="bank-dialog-cancel" :disabled="questionBankSaving" @tap="closeQuestionBankDialog">取消</button>
          <button class="bank-dialog-confirm" :disabled="questionBankSaving" @tap="saveQuestionBankDialog">
            {{ questionBankSaving ? '保存中…' : '保存' }}
          </button>
        </view>
      </view>
    </view>

    <AdminMembershipPageManager
      v-if="membershipPageManagerVisible"
      :preview="devPreviewMode"
      @close="closeMembershipPageManager"
    />
  </view>
</template>

<script setup>
import { computed, nextTick, onUnmounted, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import AdminCommunityAppeals from '../../components/AdminCommunityAppeals.vue'
import AdminCommunityModeration from '../../components/AdminCommunityModeration.vue'
import AdminConsultationManagement from '../../components/AdminConsultationManagement.vue'
import AdminMembershipPageManager from '../../components/AdminMembershipPageManager.vue'
import AdminMockExamManagement from '../../components/AdminMockExamManagement.vue'
import AdminResourceManagement from '../../components/AdminResourceManagement.vue'
import AdminSelect from '../../components/AdminSelect.vue'
import AppRefreshIcon from '../../components/ui/AppRefreshIcon.vue'
import {
  bootstrapQuestionAdminScorelines,
  bulkUpdateQuestionAdminCommunityPostFeatured,
  bulkUpdateQuestionAdminCommunityPostVisibility,
  bulkUpdateAdminQuestionStatus,
  cancelQuestionAdminPortalUserMembership,
  createAdminQuestion,
  createAdminQuestionBank,
  createQuestionAdminHomeContent,
  deleteAdminQuestions,
  fetchAdminQuestionBankPendingPublishPreview,
  fetchAdminQuestionDetail,
  fetchAdminQuestionBanks,
  fetchAdminQuestions,
  fetchAdminQuestionStats,
  fetchQuestionAdminCommunityOverview,
  fetchQuestionAdminCommunityPostDetail,
  fetchQuestionAdminCommunityPosts,
  fetchQuestionAdminDashboard,
  fetchQuestionAdminAdmissionRuns,
  fetchQuestionAdminAnnouncementRecords,
  fetchQuestionAdminMajorCatalogRecords,
  fetchQuestionAdminHomeContent,
  fetchQuestionAdminOperationsOverview,
  fetchQuestionAdminPortalMe,
  fetchQuestionAdminPortalUserDetail,
  fetchQuestionAdminPortalUsers,
  fetchQuestionAdminScorelineRecords,
  bootstrapQuestionAdminAdmissionSnapshot,
  previewQuestionAdminAdmissionImport,
  publishAdminQuestionBankPendingQuestions,
  renameAdminQuestionBank,
  renewQuestionAdminPortalUserMembership,
  updateQuestionAdminAnnouncementRecord,
  updateQuestionAdminMajorCatalogRecord,
  updateQuestionAdminHomeContent,
  updateAdminQuestion,
  updateAdminQuestionReview,
   updateAdminQuestionStatus,
   updateQuestionAdminCommunityCommentVisibility,
   updateQuestionAdminCommunityPostVisibility,
  updateQuestionAdminPortalUserDisabled,
  updateQuestionAdminScorelineRecord,
  commitQuestionAdminAdmissionImport
} from '../../api/admin'
import MathText from '../../components/MathText.vue'
import MathQuestionPaperPreview from '../../components/MathQuestionPaperPreview.vue'
import QuestionImageImport from './question-image-import.vue'
import { historicalScoreLineRecords as legacyHistoricalScoreLineRecords } from '../../data/historicalScoreLines'
import { clearAuthSession, getAuthUser, isLoggedIn, updateAuthUser } from '../../utils/auth'
import { formatMathText } from '../../utils/mathText'
import { isAiGeneratedQuestion } from '../../utils/questionSource'
import { downloadReturnedQuestionsWorkbook } from '../../utils/xlsxQuestionExport.mjs'
import {
  QUESTION_CATALOG,
  QUESTION_MODULES,
  QUESTION_STATUS,
  QUESTION_SUBJECTS
} from './question-admin-catalog'

const portalLoading = ref(true)
const portalBootstrapError = ref(null)
const refreshing = ref(false)
const dashboardLoading = ref(false)
const communityLoading = ref(false)
const communityLoadError = ref(false)
const communityDetailVisible = ref(false)
const communityDetailLoading = ref(false)
const communitySaving = ref(false)
const questionsLoading = ref(false)
const questionLoadError = ref(false)
const questionBanksLoading = ref(false)
const questionBanksError = ref(false)
const activeSection = ref('dashboard')
const contentManagementTab = ref('posts')
const contentManagementMountedTabs = reactive({ posts: true, reports: false, appeals: false })
const consultationManagementRef = ref(null)
const consultationInitialView = ref('applications')
const consultationInitialCaseView = ref('reports')
const mockExamManagementRef = ref(null)
const resourceManagementRef = ref(null)
const communityModerationRef = ref(null)
const communityAppealsRef = ref(null)
const sidebarCollapsed = ref(false)
const sidebarToggleTitle = computed(() => (sidebarCollapsed.value ? '打开边栏' : '关闭边栏'))
const authUser = ref(getAuthUser() || {})
const portalPermissions = reactive({
  scope: 'none',
  allowed_question_bank_ids: [],
  can_access_full_portal: false,
  can_view_questions: false,
  can_import_questions: false,
  can_manage_questions: false
})
const canAccessFullPortal = computed(() => Boolean(portalPermissions.can_access_full_portal))
const canViewQuestions = computed(() => Boolean(portalPermissions.can_view_questions))
const canImportQuestions = computed(() => Boolean(portalPermissions.can_import_questions))
const canManageQuestions = computed(() => Boolean(portalPermissions.can_manage_questions))
const dashboard = reactive({
  today_practicing_users: 0,
  registered_users: 0,
  today_registered_users: 0,
  difficult_questions_count: 0,
  difficult_questions: []
})
const dashboardFilters = reactive({
  subject: '',
  sort_by: 'wrong_count',
  period_days: 0
})
const dashboardDifficultPage = ref(1)
const dashboardDifficultPageSize = 20
const communityOverview = reactive({
  total_posts: 0,
  published_posts: 0,
  archived_posts: 0,
  today_posts: 0,
  total_reports: 0,
  pending_reports: 0,
  reviewing_reports: 0
})
const communityFilters = reactive({
  status: 'all',
  post_type: 'all',
  sort_by: 'newest',
  search: ''
})
const communityPosts = ref([])
const communityCount = ref(0)
const communityPage = ref(1)
const communityPageSize = 20
const communitySelectedIds = ref([])
const communityDetail = ref(null)
const operationsOverview = reactive({
  total_users: 0,
  new_today: 0,
  new_week: 0,
  active_week: 0,
  active_members: 0,
  published_home_items: 0,
  published_announcements: 0,
  scoreline_draft_runs: 0,
  announcement_draft_runs: 0,
  major_catalog_draft_runs: 0,
  recent_import_failures: 0
})
const operationsOverviewLoading = ref(true)
const operationsOverviewError = ref(false)
const userFilters = reactive({
  search: '',
  exam_target: '',
  membership_status: '',
  account_status: 'all',
  activity: 'all'
})
const userSort = reactive({
  field: 'created_at',
  direction: 'desc'
})
const portalUsers = ref([])
const portalUserCount = ref(0)
const portalUsersLoading = ref(false)
const portalUsersError = ref(false)
const portalUserPage = ref(1)
const portalUserPageSize = 20
const portalUserDetailVisible = ref(false)
const portalUserDetailLoading = ref(false)
const portalUserDetail = ref(null)
const portalUserSaving = ref(false)
const portalUserSavingId = ref('')
const portalMembershipVisible = ref(false)
const portalMembershipLoading = ref(false)
const portalMembershipDetail = ref(null)
const portalMembershipSaving = ref(false)
const portalMembershipAction = ref('')
const membershipPageManagerVisible = ref(false)
const devPreviewPortalUsers = ref([])
const admissionDataset = ref('scorelines')
const admissionRuns = ref([])
const devPreviewAdmissionRuns = {
  scorelines: [],
  announcements: [],
  'major-catalog': []
}
const admissionRunsLoading = ref(false)
const admissionRunsError = ref(false)
const admissionFile = ref(null)
const admissionFileName = ref('')
const admissionFileInputRef = ref(null)
const admissionPreview = ref(null)
const admissionImportVisible = ref(false)
const admissionPreviewLoading = ref(false)
const admissionCommitting = ref(false)
const admissionSnapshotBootstrapLoading = ref(false)
const selectedAdmissionRunId = ref('')
const scorelineRecords = ref([])
const scorelineRecordCount = ref(0)
const scorelineRecordsLoading = ref(false)
const scorelineRecordsError = ref(false)
const scorelineRecordPage = ref(1)
const scorelineRecordPageSize = 50
const scorelineRecordBootstrapLoading = ref(false)
const scorelineRecordEditorVisible = ref(false)
const scorelineRecordSaving = ref(false)
const scorelineRecordEditingId = ref('')
const scorelineFilters = reactive({
  score_year: '',
  region: '',
  keyword: ''
})
const scorelineFilterOptions = ref({ years: [], regions: [] })
const scorelineYearFilterOptions = computed(() => {
  const years = new Set(scorelineFilterOptions.value.years)
  if (scorelineFilters.score_year) years.add(scorelineFilters.score_year)
  return [
    { label: '全部年份', value: '' },
    ...Array.from(years)
      .map((value) => String(value || '').trim())
      .filter(Boolean)
      .sort((left, right) => right.localeCompare(left))
      .map((value) => ({ label: value, value }))
  ]
})
const scorelineRegionFilterOptions = computed(() => {
  const regions = new Set(scorelineFilterOptions.value.regions)
  if (scorelineFilters.region) regions.add(scorelineFilters.region)
  return [
    { label: '全部地区', value: '' },
    ...Array.from(regions)
      .map((value) => String(value || '').trim())
      .filter(Boolean)
      .sort((left, right) => left.localeCompare(right, 'zh-CN'))
      .map((value) => ({ label: value, value }))
  ]
})
const scorelineYearFilterIndex = computed(() => optionIndex(scorelineYearFilterOptions.value, scorelineFilters.score_year))
const scorelineRegionFilterIndex = computed(() => optionIndex(scorelineRegionFilterOptions.value, scorelineFilters.region))
const scorelineRecordForm = reactive({
  score_year: '',
  region: '',
  school_name: '',
  unit_name: '',
  score_raw: '',
  score_kind: 'score',
  source_url: '',
  source_note: ''
})
const devPreviewScorelineRecords = ref([])
const announcementRecords = ref([])
const announcementRecordCount = ref(0)
const announcementRecordsLoading = ref(false)
const announcementRecordsError = ref(false)
const announcementFilters = reactive({
  notice_type: '',
  notice_year: '',
  region: '',
  school_id: '',
  keyword: ''
})
const announcementFilterOptions = ref({ years: [], regions: [], schools: [] })
const announcementUpdatingId = ref('')
const announcementRecordEditorVisible = ref(false)
const announcementRecordSaving = ref(false)
const announcementRecordEditingId = ref('')
const announcementRecordForm = reactive({
  notice_year: '',
  region: '',
  school_name: '',
  unit_name: '',
  notice_type: 'brochure',
  title: '',
  summary: '',
  notice_date: '',
  source_url: '',
  content_text: ''
})
const devPreviewAnnouncementRecords = ref([])
const majorCatalogRecords = ref([])
const majorCatalogRecordCount = ref(0)
const majorCatalogRecordsLoading = ref(false)
const majorCatalogRecordsError = ref(false)
const majorCatalogRecordPage = ref(1)
const majorCatalogRecordPageSize = 50
const majorCatalogRecordEditorVisible = ref(false)
const majorCatalogRecordSaving = ref(false)
const majorCatalogRecordEditingId = ref('')
const majorCatalogRecordYear = ref('')
const majorCatalogFilters = reactive({
  catalog_year: '',
  region: '',
  school_name: '',
  exam_code: '',
  keyword: ''
})
const majorCatalogFilterOptions = ref({ years: [], regions: [], schools: [], exam_codes: [] })
const majorCatalogRecordForm = reactive({
  region: '',
  school_name: '',
  department_name: '',
  program_name: '',
  program_code: '',
  direction_name: '',
  tutor: '',
  exam_code: 'Z001',
  degree: '',
  study_mode: ''
})
const devPreviewMajorCatalogRecords = ref([])
const homeContentItems = ref([])
const devPreviewHomeContentItems = ref([])
const homeContentLoading = ref(false)
const homeContentError = ref(false)
const homeContentEditorVisible = ref(false)
const homeContentSaving = ref(false)
const homeContentStatusSavingId = ref('')
const homeContentEditingId = ref('')
const homeContentClock = ref(Date.now())
let homeContentClockTimer = null
const homeContentForm = reactive({
  slot: 'focus',
  title: '',
  subtitle: '',
  badge: '',
  source: '',
  display_date: '',
  cover_label: '',
  tone: 'is-blue',
  target_url: '',
  route_key: '',
  sort_order: 0,
  status: 'draft',
  starts_at: '',
  ends_at: ''
})
const globalQuestionStats = reactive({
  active: 0,
  archived: 0,
  pendingReview: 0
})
const questionStats = reactive({
  active: 0,
  archived: 0,
  pendingReview: 0
})
const questionBanks = ref([])
const activeQuestionBank = ref(null)
const reviewQuestionBank = ref(null)
const showGlobalQuestionList = ref(false)
const importQuestionBankId = ref('')
const importQuestionBankName = ref('')
const questionImageImportRef = ref(null)
const importPreviewVisible = ref(false)
const questionBankDialogVisible = ref(false)
const questionBankDialogMode = ref('create')
const questionBankNameDraft = ref('')
const questionBankTarget = ref(null)
const questionBankSaving = ref(false)
const publishQuestionBankDialogVisible = ref(false)
const publishQuestionBankId = ref('')
const publishPendingPreview = ref(null)
const publishPendingPreviewLoading = ref(false)
const publishPendingPreviewError = ref(false)
const publishingQuestions = ref(false)
const requestedQuestionBankId = ref('')
const questions = ref([])
const questionCount = ref(0)
const currentPage = ref(1)
const pageSize = 20
const questionSortDirection = ref('desc')
const selectedIds = ref([])
const drawerVisible = ref(false)
const drawerLoading = ref(false)
const drawerMode = ref('edit')
const saving = ref(false)
const devPreviewMode = ref(false)
const returnedReviewQuestions = ref([])
const returnedReviewBatchExported = ref(false)
let searchTimer = null
let communitySearchTimer = null
let portalUserSearchTimer = null
let scorelineSearchTimer = null
let majorCatalogSearchTimer = null

const filters = reactive({
  subject: '',
  module: '',
  difficulty: '',
  status: '',
  search: ''
})

const form = reactive({
  id: '',
  exam_code: 'COMMON',
  subject: '英语运用',
  module: '语言知识',
  submodule: '语法',
  stem: '',
  option_a: '',
  option_b: '',
  option_c: '',
  option_d: '',
  answer: 'A',
  explanation: '',
  difficulty: 2,
  status: 'archived',
  review_status: 'pending',
  review_note: '',
  source_type: 'manual',
  source_year: '',
  original_review_note: ''
})

const navItems = [
  { key: 'dashboard', label: '仪表盘', icon: '/static/admin-icons/nav-dashboard.svg' },
  { key: 'users', label: '用户管理', icon: '/static/admin-icons/dashboard-visits.svg' },
  { key: 'community', label: '内容管理', icon: '/static/ui-icons/circle-community.svg' },
  { key: 'consultation', label: '咨询管理', icon: '/static/ui-icons/mentor-chat-add.svg' },
  { key: 'admission', label: '报考服务', icon: '/static/ui-icons/home-school-notices.svg' },
  { key: 'resources', label: '资料管理', icon: '/static/ui-icons/circle-materials.svg' },
  { key: 'homeOps', label: '首页运营', icon: '/static/ui-icons/tab-home.svg' },
  { key: 'questions', label: '题目管理', icon: '/static/admin-icons/nav-question-management.svg' },
  { key: 'import', label: '批量导入', icon: '/static/admin-icons/nav-batch-import.svg' }
]
const visibleNavItems = computed(() => navItems.filter((item) => canAccessSection(item.key)))

const contentManagementTabs = [
  { key: 'posts', label: '社区内容', description: '研友聊、经验贴', icon: '/static/ui-icons/circle-community.svg' },
  { key: 'reports', label: '内容举报', description: '用户举报内容', icon: '/static/ui-icons/report.svg' },
  { key: 'appeals', label: '内容申诉复核', description: '内容处置申诉', icon: '/static/ui-icons/community-comment-heart.svg' }
]

const difficultyOptions = [
  { label: '全部难度', value: '' },
  ...[1, 2, 3, 4, 5].map((value) => ({ label: `难度 ${value}`, value: String(value) }))
]
const statusOptions = [
  { label: '全部状态', value: '' },
  { label: '待审核', value: QUESTION_STATUS.PENDING_REVIEW },
  { label: '已发布', value: QUESTION_STATUS.ACTIVE },
  { label: '已下架', value: QUESTION_STATUS.ARCHIVED }
]
const dashboardSortOptions = [
  { label: '答错次数：从高到低', value: 'wrong_count' },
  { label: '正确率：从低到高', value: 'accuracy' },
  { label: '作答次数：从高到低', value: 'attempt_count' }
]
const dashboardTimeRangeOptions = [
  { label: '全部时间', value: 0 },
  { label: '近 7 天', value: 7 },
  { label: '近 30 天', value: 30 }
]
const communityStatusOptions = [
  { label: '全部状态', value: 'all' },
  { label: '公开展示', value: 'published' },
  { label: '精选', value: 'featured' },
  { label: '已下架', value: 'archived' }
]
const communityTypeOptions = [
  { label: '全部帖子', value: 'all' },
  { label: '研友聊', value: 'chat' },
  { label: '经验贴', value: 'experience' }
]
const communitySortOptions = [
  { label: '最新发布', value: 'newest' },
  { label: '浏览量：从高到低', value: 'views' },
  { label: '点赞数：从高到低', value: 'likes' },
  { label: '评论数：从高到低', value: 'comments' }
]
const portalUserExamOptions = [
  { label: '全部考试', value: '' },
  { label: 'Z001', value: 'Z001' },
  { label: 'Z002', value: 'Z002' }
]
const portalUserMembershipOptions = [
  { label: '全部会员状态', value: '' },
  { label: '有效会员', value: 'active' },
  { label: '非会员', value: 'inactive' }
]
const portalUserAccountStatusOptions = [
  { label: '全部账号状态', value: 'all' },
  { label: '正常账号', value: 'active' },
  { label: '已停用账号', value: 'disabled' }
]
const portalUserActivityOptions = [
  { label: '全部活跃度', value: 'all' },
  { label: '近 7 天作答', value: 'active_7d' },
  { label: '30 天未作答', value: 'inactive' }
]
const admissionDatasets = [
  { key: 'scorelines', label: '历年分数线', description: '以完整年度快照维护院校分数线，发布后同步学生端。' },
  { key: 'announcements', label: '院校公告', description: '统一导入招生简章与复试分数线，可逐条编辑、发布或归档。' },
  { key: 'major-catalog', label: '专业目录', description: '请上传包含院校、院系、专业与研究方向的完整年度快照；发布时会以事务方式切换学生端目录。' }
]
const homeToneOptions = [
  { label: '蓝色', value: 'is-blue' },
  { label: '青绿', value: 'is-mint' },
  { label: '橙色', value: 'is-orange' },
  { label: '紫色', value: 'is-violet' }
]
const HOME_CONTENT_SLOT_LIMITS = Object.freeze({ focus: 3, news: 3 })
const homeTargetOptions = [
  { label: '外部链接 / 不跳转', value: '' },
  { label: '院校公告', value: 'school-announcements' },
  { label: '专业目录', value: 'major-catalog' },
  { label: '报考资讯归档', value: 'application-guide' }
]
const announcementNoticeTypeFilterOptions = [
  { label: '全部公告', value: '' },
  { label: '招生简章', value: 'brochure' },
  { label: '分数线与复试', value: 'scoreline_retest' }
]
const announcementRecordNoticeTypeOptions = [
  { label: '招生简章', value: 'brochure' },
  { label: '复试分数线', value: 'scoreline_retest' }
]
const majorCatalogExamCodeEditOptions = [
  { label: 'Z001', value: 'Z001' },
  { label: 'Z002', value: 'Z002' }
]
const scorelineKindOptions = [
  { label: '数字分数', value: 'score' },
  { label: '暂无数据', value: 'missing' },
  { label: '未划线', value: 'unavailable' },
  { label: '详见官网', value: 'official' },
  { label: '多套标准', value: 'multiple' },
  { label: '文字说明', value: 'note' }
]
const answerOptions = ['A', 'B', 'C', 'D']
const previewQuestions = [
  {
    id: '6d7b1b2a-8f21-4cf1-91c2-a10294db8301',
    exam_code: 'COMMON',
    subject: '中华文化',
    module: '中国文学常识',
    submodule: '代表作家及作品',
    stem: '下列作品与作者对应正确的是哪一项？',
    option_a: '《文心雕龙》—刘勰',
    option_b: '《世说新语》—司马迁',
    option_c: '《资治通鉴》—班固',
    option_d: '《梦溪笔谈》—郦道元',
    answer: 'A',
    explanation: '《文心雕龙》是南朝文学理论家刘勰创作的文学理论专著。',
    difficulty: 2,
    status: 'active',
    review_status: 'approved',
    created_at: '2026-07-22T08:20:00Z'
  },
  {
    id: '274f0ca7-145b-4ffd-bf04-51458d8ac802',
    exam_code: 'COMMON',
    subject: '英语运用',
    module: '语言知识',
    submodule: '语法',
    stem: 'Had the weather been better, we ____ the outdoor ceremony as planned.',
    option_a: 'would hold',
    option_b: 'would have held',
    option_c: 'held',
    option_d: 'had held',
    answer: 'B',
    explanation: '题干使用省略 if 的虚拟条件句，表示与过去事实相反。',
    difficulty: 3,
    status: 'archived',
    review_status: 'pending',
    created_at: '2026-07-22T07:15:00Z'
  },
  {
    id: '0327ad6f-b5c5-46f7-a297-ce378e199203',
    exam_code: 'Z002',
    subject: '数学基础',
    module: '一元函数微分学',
    submodule: '极值与最值',
    stem: '函数 \\(f(x)=x^3-3x\\) 在区间 \\([-2,2]\\) 上的最大值为（ ）。',
    option_a: '2',
    option_b: '3',
    option_c: '4',
    option_d: '6',
    answer: 'A',
    explanation: '比较驻点与区间端点处的函数值可得最大值。',
    difficulty: 3,
    status: 'active',
    review_status: 'approved',
    created_at: '2026-07-21T11:40:00Z'
  },
  {
    id: '887c5694-74e1-4e92-b1ae-fae9b5023604',
    exam_code: 'Z001',
    subject: '逻辑推理',
    module: '论证',
    submodule: '削弱',
    stem: '某校认为延长图书馆开放时间能显著提高学生平均成绩。下列哪项最能削弱该结论？',
    option_a: '延长开放后，到馆人数明显增加',
    option_b: '多数到馆学生主要使用自习座位',
    option_c: '同期学校调整了课程考核方式',
    option_d: '学生普遍支持延长开放时间',
    answer: 'C',
    explanation: '同期考核方式变化为成绩提高提供了另一种解释。',
    difficulty: 4,
    status: 'archived',
    review_status: 'needs_changes',
    created_at: '2026-07-20T05:18:00Z'
  }
]

const previewCommunityPosts = [
  {
    id: 'preview-community-001',
    author_id: 'a1b2c3d4-e5f6-4a7b-8c9d-0123456789ab',
    author_name: '林同学',
    author_avatar: '林',
    category: '中华文化',
    post_type: 'chat',
    title: '中华文化复习怎么安排更高效？',
    content: '最近开始整理中国文学常识，大家是按模块刷题，还是先做一轮综合题再回头补弱项？',
    media: [],
    view_count: 328,
    like_count: 26,
    comment_count: 4,
    is_published: true,
    is_featured: true,
    created_at: '2026-08-07T01:15:00Z',
    updated_at: '2026-08-07T01:15:00Z',
    comments: [
      {
        id: 'preview-comment-001',
        author_name: '陈同学',
        author_avatar: '陈',
        content: '我先按模块过一遍，再用错题本回顾，节奏会更稳。',
        like_count: 5,
        created_at: '2026-08-07T01:30:00Z'
      },
      {
        id: 'preview-comment-002',
        author_name: '周同学',
        author_avatar: '周',
        content: '建议文学和历史交替刷，连续做同类题容易疲劳。',
        like_count: 3,
        created_at: '2026-08-07T02:05:00Z'
      }
    ]
  },
  {
    id: 'preview-community-002',
    author_id: 'b1c2d3e4-f5a6-4b7c-8d9e-0123456789ab',
    author_name: '许同学',
    author_avatar: '许',
    category: 'Z001',
    post_type: 'experience',
    title: 'Z001 逻辑推理二刷笔记',
    content: '二刷时把错题拆成概念判断、论证和分析推理三个文件夹，每晚只复盘当天错误的题目。',
    media: [],
    view_count: 781,
    like_count: 74,
    comment_count: 11,
    is_published: true,
    is_featured: true,
    created_at: '2026-08-06T08:25:00Z',
    updated_at: '2026-08-06T08:25:00Z',
    comments: []
  },
  {
    id: 'preview-community-003',
    author_id: 'c1d2e3f4-a5b6-4c7d-8e9f-0123456789ab',
    author_name: '何同学',
    author_avatar: '何',
    category: '英语运用',
    post_type: 'chat',
    title: '英语词汇总是记了又忘怎么办？',
    content: '想试试把词汇放到真题句子里复习，大家有没有适合日常打卡的方法？',
    media: [],
    view_count: 194,
    like_count: 18,
    comment_count: 7,
    is_published: false,
    created_at: '2026-08-05T03:10:00Z',
    updated_at: '2026-08-06T09:30:00Z',
    comments: []
  },
  {
    id: 'preview-community-004',
    author_id: 'd1e2f3a4-b5c6-4d7e-8f9a-0123456789ab',
    author_name: '苏同学',
    author_avatar: '苏',
    category: 'Z002',
    post_type: 'experience',
    title: '数学基础错题复盘节奏分享',
    content: '我把每道错题按错因标记为计算、概念和审题，隔天再做一次，正确后才归档。',
    media: [],
    view_count: 612,
    like_count: 51,
    comment_count: 8,
    is_published: true,
    created_at: '2026-08-04T12:40:00Z',
    updated_at: '2026-08-04T12:40:00Z',
    comments: []
  }
]

const currentNavLabel = computed(() => {
  if (activeSection.value === 'import' && importPreviewVisible.value) {
    return '批量导入 / 导入预览'
  }
  if (activeSection.value === 'community') {
    return `内容管理 / ${contentManagementTabLabel.value}`
  }
  if (activeSection.value === 'review') {
    return reviewQuestionBank.value
      ? `题目管理 / ${reviewQuestionBank.value.name} / 待审核`
      : '题目管理 / 待审核'
  }
  if (activeSection.value === 'mockExams') {
    return '题目管理 / 模拟卷'
  }
  const label = visibleNavItems.value.find((item) => item.key === activeSection.value)?.label || '后台管理'
  return activeSection.value === 'questions' && activeQuestionBank.value
    ? `${label} / ${activeQuestionBank.value.name}`
    : label
})
const contentManagementTabLabel = computed(() => (
  contentManagementTabs.find((item) => item.key === contentManagementTab.value)?.label || '社区内容'
))
const showHeaderBackButton = computed(() => (
  activeSection.value === 'review' ||
  activeSection.value === 'mockExams' ||
  (activeSection.value === 'import' && importPreviewVisible.value) ||
  (activeSection.value === 'questions' && (activeQuestionBank.value || showGlobalQuestionList.value))
))
const headerBackDisabled = computed(() => (
  (activeSection.value === 'questions' && saving.value) ||
  (activeSection.value === 'mockExams' && Boolean(mockExamManagementRef.value?.isBusy?.()))
))
const pageTitle = computed(() => {
  if (activeSection.value === 'import' && importPreviewVisible.value) {
    return '导入预览'
  }
  const titles = {
    dashboard: '后台仪表盘',
    users: '用户管理',
    community: '内容管理',
    consultation: '咨询管理',
    admission: '报考资料',
    resources: '资料管理',
    homeOps: '首页运营',
    questions: '题目管理',
    mockExams: '模拟卷',
    review: '审核队列',
    import: '批量导入'
  }
  if (activeSection.value === 'questions' && activeQuestionBank.value) {
    return activeQuestionBank.value.name
  }
  return titles[activeSection.value] || '后台管理'
})
const profileName = '后台管理'
const todayLabel = computed(() => new Intl.DateTimeFormat('zh-CN', {
  month: 'long',
  day: 'numeric',
  weekday: 'long'
}).format(new Date()))
const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 12) return '早上好'
  if (hour < 18) return '下午好'
  return '晚上好'
})
const totalQuestionCount = computed(() => (
  Number(globalQuestionStats.active || 0) +
  Number(globalQuestionStats.archived || 0) +
  Number(globalQuestionStats.pendingReview || 0)
))
const currentQuestionStats = computed(() => (
  activeQuestionBank.value ? questionStats : globalQuestionStats
))
const activeQuestionBankCount = computed(() => (
  Number(currentQuestionStats.value.active || 0) +
  Number(currentQuestionStats.value.archived || 0) +
  Number(currentQuestionStats.value.pendingReview || 0)
))
const summaryCards = computed(() => [
  { key: '', label: '全部题目', value: activeQuestionBankCount.value, iconSrc: '/static/admin-icons/question-count.svg', tone: 'blue', interactive: true },
  { key: QUESTION_STATUS.PENDING_REVIEW, label: '待审核', value: currentQuestionStats.value.pendingReview, iconSrc: '/static/admin-icons/pending-review.svg', tone: 'orange', interactive: canManageQuestions.value },
  { key: QUESTION_STATUS.ACTIVE, label: '已发布', value: currentQuestionStats.value.active, iconSrc: '/static/admin-icons/publish.svg', tone: 'mint', interactive: false },
  { key: QUESTION_STATUS.ARCHIVED, label: '已下架', value: currentQuestionStats.value.archived, iconSrc: '/static/admin-icons/unpublish.svg', tone: 'slate', interactive: false }
])
const moduleOptions = computed(() => [
  { label: '全部模块', value: '' },
  ...(QUESTION_MODULES[filters.subject] || []).map((item) => ({ label: item, value: item }))
])
const subjectLabels = computed(() => QUESTION_SUBJECTS.map((item) => item.label))
const dashboardSubjectOptions = computed(() => [
  { label: '全部类型', value: '' },
  { label: '中华文化', value: '中华文化' },
  { label: '英语运用', value: '英语运用' },
  { label: '逻辑推理', value: '逻辑推理' },
  { label: '数学基础', value: '数学基础' }
])
const dashboardSubjectLabels = computed(() => dashboardSubjectOptions.value.map((item) => item.label))
const dashboardTimeRangeLabels = computed(() => dashboardTimeRangeOptions.map((item) => item.label))
const moduleLabels = computed(() => moduleOptions.value.map((item) => item.label))
const difficultyLabels = computed(() => difficultyOptions.map((item) => item.label))
const statusLabels = computed(() => statusOptions.map((item) => item.label))
const selectedSubjectIndex = computed(() => optionIndex(QUESTION_SUBJECTS, filters.subject))
const selectedDashboardSubjectIndex = computed(() => optionIndex(
  dashboardSubjectOptions.value,
  dashboardFilters.subject
))
const selectedDashboardSortIndex = computed(() => optionIndex(
  dashboardSortOptions,
  dashboardFilters.sort_by
))
const selectedDashboardTimeRangeIndex = computed(() => optionIndex(
  dashboardTimeRangeOptions,
  Number(dashboardFilters.period_days || 0)
))
const dashboardDifficultTotalPages = computed(() => Math.max(
  1,
  Math.ceil(Number(dashboard.difficult_questions_count || dashboard.difficult_questions.length || 0) / dashboardDifficultPageSize)
))
const dashboardRankOffset = computed(() => (dashboardDifficultPage.value - 1) * dashboardDifficultPageSize)
const communityStatusLabels = computed(() => communityStatusOptions.map((item) => item.label))
const communityTypeLabels = computed(() => communityTypeOptions.map((item) => item.label))
const communitySortLabels = computed(() => communitySortOptions.map((item) => item.label))
const selectedCommunityStatusIndex = computed(() => optionIndex(communityStatusOptions, communityFilters.status))
const selectedCommunityTypeIndex = computed(() => optionIndex(communityTypeOptions, communityFilters.post_type))
const selectedCommunitySortIndex = computed(() => optionIndex(communitySortOptions, communityFilters.sort_by))
const communityTotalPages = computed(() => Math.max(1, Math.ceil(Number(communityCount.value || 0) / communityPageSize)))
const portalUserExamIndex = computed(() => optionIndex(portalUserExamOptions, userFilters.exam_target))
const portalUserMembershipIndex = computed(() => optionIndex(portalUserMembershipOptions, userFilters.membership_status))
const portalUserAccountStatusIndex = computed(() => optionIndex(portalUserAccountStatusOptions, userFilters.account_status))
const portalUserActivityIndex = computed(() => optionIndex(portalUserActivityOptions, userFilters.activity))
const portalUserTotalPages = computed(() => Math.max(1, Math.ceil(Number(portalUserCount.value || 0) / portalUserPageSize)))
const currentAdmissionDataset = computed(() => (
  admissionDatasets.find((item) => item.key === admissionDataset.value) || admissionDatasets[0]
))
const admissionImportEnabled = computed(() => true)
const canCommitAdmissionImport = computed(() => (
  Boolean(admissionFile.value) &&
  Boolean(admissionPreview.value) &&
  Number(admissionPreview.value.invalid_rows || 0) === 0 &&
  Number(admissionPreview.value.valid_rows || 0) > 0
))
const selectedAdmissionRun = computed(() => (
  admissionRuns.value.find((item) => item.id === selectedAdmissionRunId.value) || null
))
const canBootstrapExistingAdmissionSnapshot = computed(() => (
  ['announcements', 'major-catalog'].includes(admissionDataset.value)
  && !admissionRunsLoading.value
  && !admissionRunsError.value
  && !admissionRuns.value.some((item) => item.status !== 'failed')
))
const scorelineRecordTotalPages = computed(() => Math.max(1, Math.ceil(scorelineRecordCount.value / scorelineRecordPageSize)))
const scorelineKindLabels = computed(() => scorelineKindOptions.map((item) => item.label))
const scorelineKindIndex = computed(() => optionIndex(scorelineKindOptions, scorelineRecordForm.score_kind))
const legacyScorelineImportRecords = computed(() => buildLegacyScorelineImportRecords())
const canManageSelectedAnnouncementRecords = computed(() => true)
const announcementYearFilterOptions = computed(() => {
  const years = new Set(announcementFilterOptions.value.years)
  if (announcementFilters.notice_year) years.add(announcementFilters.notice_year)
  return [
    { label: '全部年份', value: '' },
    ...Array.from(years)
      .filter((value) => /^20\d{2}$/.test(String(value)))
      .sort((left, right) => String(right).localeCompare(String(left)))
      .map((value) => ({ label: `${value} 年`, value }))
  ]
})
const announcementRegionFilterOptions = computed(() => {
  const regions = new Set(announcementFilterOptions.value.regions)
  if (announcementFilters.region) regions.add(announcementFilters.region)
  return [
    { label: '全部地域', value: '' },
    ...Array.from(regions)
      .map((value) => String(value || '').trim())
      .filter(Boolean)
      .sort((left, right) => left.localeCompare(right, 'zh-CN'))
      .map((value) => ({ label: value, value }))
  ]
})
const announcementSchoolFilterOptions = computed(() => {
  if (!announcementFilters.region) return [{ label: '请先选择地域', value: '' }]
  const schools = new Map(
    announcementFilterOptions.value.schools
      .filter((item) => item?.region === announcementFilters.region)
      .map((item) => [String(item?.id || ''), String(item?.name || '').trim()])
      .filter(([id, name]) => id && name)
  )
  if (announcementFilters.school_id && !schools.has(announcementFilters.school_id)) {
    schools.set(announcementFilters.school_id, announcementFilters.school_id)
  }
  return [
    { label: '全部院校', value: '' },
    ...Array.from(schools.entries())
      .sort((left, right) => left[1].localeCompare(right[1], 'zh-CN'))
      .map(([value, label]) => ({ label, value }))
  ]
})
const announcementNoticeTypeFilterIndex = computed(() => optionIndex(announcementNoticeTypeFilterOptions, announcementFilters.notice_type))
const announcementYearFilterIndex = computed(() => optionIndex(announcementYearFilterOptions.value, announcementFilters.notice_year))
const announcementRegionFilterIndex = computed(() => optionIndex(announcementRegionFilterOptions.value, announcementFilters.region))
const announcementSchoolFilterIndex = computed(() => optionIndex(announcementSchoolFilterOptions.value, announcementFilters.school_id))
const announcementRecordNoticeTypeIndex = computed(() => optionIndex(announcementRecordNoticeTypeOptions, announcementRecordForm.notice_type))
const majorCatalogRecordTotalPages = computed(() => Math.max(1, Math.ceil(majorCatalogRecordCount.value / majorCatalogRecordPageSize)))
const majorCatalogYearFilterOptions = computed(() => {
  const years = new Set(majorCatalogFilterOptions.value.years)
  const currentYear = String(selectedAdmissionRun.value?.statistics?.catalog_year || '').trim()
  if (currentYear) years.add(currentYear)
  if (majorCatalogFilters.catalog_year) years.add(majorCatalogFilters.catalog_year)
  return [
    { label: '全部目录', value: '' },
    ...Array.from(years)
      .filter((value) => /^20\d{2}$/.test(String(value)))
      .sort((left, right) => String(right).localeCompare(String(left)))
      .map((value) => ({ label: `${value} 年`, value }))
  ]
})
const majorCatalogRegionFilterOptions = computed(() => {
  const regions = new Set(majorCatalogFilterOptions.value.regions)
  if (majorCatalogFilters.region) regions.add(majorCatalogFilters.region)
  return [
    { label: '全部地域', value: '' },
    ...Array.from(regions)
      .map((value) => String(value || '').trim())
      .filter(Boolean)
      .sort((left, right) => left.localeCompare(right, 'zh-CN'))
      .map((value) => ({ label: value, value }))
  ]
})
const majorCatalogSchoolFilterOptions = computed(() => {
  if (!majorCatalogFilters.region) return [{ label: '请选择地域', value: '' }]
  const schools = new Set(
    majorCatalogFilterOptions.value.schools
      .filter((item) => item?.region === majorCatalogFilters.region)
      .map((item) => String(item?.name || '').trim())
      .filter(Boolean)
  )
  if (majorCatalogFilters.school_name) schools.add(majorCatalogFilters.school_name)
  return [
    { label: '全部招生院校', value: '' },
    ...Array.from(schools)
      .sort((left, right) => left.localeCompare(right, 'zh-CN'))
      .map((value) => ({ label: value, value }))
  ]
})
const majorCatalogExamCodeFilterOptions = computed(() => {
  const examCodes = new Set(majorCatalogFilterOptions.value.exam_codes)
  if (majorCatalogFilters.exam_code) examCodes.add(majorCatalogFilters.exam_code)
  return [
    { label: '全部统考科目', value: '' },
    ...Array.from(examCodes)
      .map((value) => String(value || '').trim().toUpperCase())
      .filter(Boolean)
      .sort()
      .map((value) => ({ label: value, value }))
  ]
})
const majorCatalogYearFilterIndex = computed(() => optionIndex(majorCatalogYearFilterOptions.value, majorCatalogFilters.catalog_year))
const majorCatalogRegionFilterIndex = computed(() => optionIndex(majorCatalogRegionFilterOptions.value, majorCatalogFilters.region))
const majorCatalogSchoolFilterIndex = computed(() => optionIndex(majorCatalogSchoolFilterOptions.value, majorCatalogFilters.school_name))
const majorCatalogExamCodeFilterIndex = computed(() => optionIndex(majorCatalogExamCodeFilterOptions.value, majorCatalogFilters.exam_code))
const majorCatalogExamCodeEditIndex = computed(() => optionIndex(majorCatalogExamCodeEditOptions, majorCatalogRecordForm.exam_code))
const homeFocusContentItems = computed(() => sortHomeContentItems(homeContentItems.value.filter((item) => item.slot === 'focus')))
const homeNewsContentItems = computed(() => sortHomeContentItems(homeContentItems.value.filter((item) => item.slot === 'news')))
const homeFocusPublishedCount = computed(() => homeFocusContentItems.value.filter((item) => item.status === 'published').length)
const homeNewsPublishedCount = computed(() => homeNewsContentItems.value.filter((item) => item.status === 'published').length)
const homeFocusContentAtCapacity = computed(() => homeFocusPublishedCount.value >= HOME_CONTENT_SLOT_LIMITS.focus)
const homeNewsContentAtCapacity = computed(() => homeNewsPublishedCount.value >= HOME_CONTENT_SLOT_LIMITS.news)
const homeVisibleFocusItems = computed(() => homeFocusContentItems.value.filter(isHomeContentVisibleNow).slice(0, HOME_CONTENT_SLOT_LIMITS.focus))
const homeVisibleNewsItems = computed(() => homeNewsContentItems.value.filter(isHomeContentVisibleNow).slice(0, HOME_CONTENT_SLOT_LIMITS.news))
const homeToneLabels = computed(() => homeToneOptions.map((item) => item.label))
const homeToneIndex = computed(() => optionIndex(homeToneOptions, homeContentForm.tone))
const homeTargetLabels = computed(() => homeTargetOptions.map((item) => item.label))
const homeTargetIndex = computed(() => optionIndex(homeTargetOptions, homeContentForm.route_key))
const communitySelectedSet = computed(() => new Set(communitySelectedIds.value))
const allCommunityPageSelected = computed(() => (
  communityPosts.value.length > 0 && communityPosts.value.every((item) => communitySelectedSet.value.has(item.id))
))
const selectedCommunityPosts = computed(() => (
  communityPosts.value.filter((item) => communitySelectedSet.value.has(item.id))
))
const communityBulkVisibilityAction = computed(() => {
  const items = selectedCommunityPosts.value
  if (!items.length || items.length !== communitySelectedIds.value.length) return null
  const publishedStates = Array.from(new Set(items.map((item) => Boolean(item.is_published))))
  if (publishedStates.length !== 1) return null
  const isPublished = publishedStates[0]
  return {
    isPublished: !isPublished,
    label: isPublished ? (items.length > 1 ? '批量下架' : '下架') : (items.length > 1 ? '批量恢复' : '恢复'),
    tone: isPublished ? 'danger' : 'publish'
  }
})
const communityBulkFeaturedAction = computed(() => {
  const items = selectedCommunityPosts.value
  if (!items.length || items.length !== communitySelectedIds.value.length) return null
  const allFeatured = items.every((item) => Boolean(item.is_featured))
  return {
    isFeatured: !allFeatured,
    label: allFeatured ? '移出精选' : '加入精选'
  }
})
const communityHasFilters = computed(() => Boolean(
  communityFilters.status !== 'all' ||
  communityFilters.post_type !== 'all' ||
  communityFilters.sort_by !== 'newest' ||
  communityFilters.search
))
const selectedModuleIndex = computed(() => optionIndex(moduleOptions.value, filters.module))
const selectedDifficultyIndex = computed(() => optionIndex(difficultyOptions, filters.difficulty))
const selectedStatusIndex = computed(() => optionIndex(statusOptions, filters.status))
const hasFilters = computed(() => Boolean(
  filters.subject || filters.module || filters.difficulty || filters.status || filters.search
))
const totalPages = computed(() => Math.max(1, Math.ceil(Number(questionCount.value || 0) / pageSize)))
const selectedSet = computed(() => new Set(selectedIds.value))
const selectedQuestions = computed(() => questions.value.filter((item) => selectedSet.value.has(item.id)))
const selectedBulkStatusAction = computed(() => {
  const items = selectedQuestions.value
  if (!items.length || items.length !== selectedIds.value.length) return null
  const statuses = Array.from(new Set(items.map((item) => questionDisplayStatus(item))))
  if (statuses.length !== 1) return null
  const selectedCount = items.length
  if (statuses[0] === QUESTION_STATUS.ACTIVE) {
    return {
      status: QUESTION_STATUS.ARCHIVED,
      label: selectedCount > 1 ? '批量下架' : '下架',
      tone: 'danger'
    }
  }
  if (statuses[0] === QUESTION_STATUS.ARCHIVED) {
    return {
      status: QUESTION_STATUS.ACTIVE,
      label: selectedCount > 1 ? '批量发布' : '发布',
      tone: 'publish'
    }
  }
  return null
})
const allPageSelected = computed(() => (
  questions.value.length > 0 && questions.value.every((item) => selectedSet.value.has(item.id))
))

const editorSubjects = computed(() => Object.keys(QUESTION_CATALOG))
const editorModules = computed(() => Object.keys(QUESTION_CATALOG[form.subject]?.modules || {}))
const editorSubmodules = computed(() => QUESTION_CATALOG[form.subject]?.modules?.[form.module] || [])
const editorSubjectLabels = computed(() => editorSubjects.value)
const editorModuleLabels = computed(() => editorModules.value)
const editorSubmoduleLabels = computed(() => editorSubmodules.value)
const editorSubjectIndex = computed(() => Math.max(0, editorSubjects.value.indexOf(form.subject)))
const editorModuleIndex = computed(() => Math.max(0, editorModules.value.indexOf(form.module)))
const editorSubmoduleIndex = computed(() => Math.max(0, editorSubmodules.value.indexOf(form.submodule)))
const drawerKicker = computed(() => (
  drawerMode.value === 'create' ? 'NEW QUESTION' : drawerMode.value === 'review' ? 'REVIEW QUEUE' : canManageQuestions.value ? 'QUESTION DETAIL' : 'READ ONLY'
))
const drawerTitle = computed(() => (
  drawerMode.value === 'create' ? '新增题目' : drawerMode.value === 'review' ? '审核题目' : canManageQuestions.value ? '编辑题目' : '查看题目'
))

function applyPortalPermissions(rawPermissions) {
  const permissions = rawPermissions && typeof rawPermissions === 'object'
    ? rawPermissions
    : {
        scope: 'full',
        allowed_question_bank_ids: [],
        can_access_full_portal: true,
        can_view_questions: true,
        can_import_questions: true,
        can_manage_questions: true
      }
  portalPermissions.scope = String(permissions.scope || 'none')
  portalPermissions.allowed_question_bank_ids = Array.isArray(permissions.allowed_question_bank_ids)
    ? permissions.allowed_question_bank_ids.map((value) => String(value || '')).filter(Boolean)
    : []
  portalPermissions.can_access_full_portal = Boolean(permissions.can_access_full_portal)
  portalPermissions.can_view_questions = Boolean(permissions.can_view_questions)
  portalPermissions.can_import_questions = Boolean(permissions.can_import_questions)
  portalPermissions.can_manage_questions = Boolean(permissions.can_manage_questions)
}

function canAccessSection(section) {
  if (canAccessFullPortal.value) return true
  if (section === 'questions') return canViewQuestions.value
  if (section === 'import') return canImportQuestions.value
  return false
}

function requireQuestionManagementAccess() {
  if (canManageQuestions.value) return true
  uni.showToast({ title: '当前账号仅支持查看和批量导入', icon: 'none' })
  return false
}

onLoad(async (options = {}) => {
  homeContentClockTimer = setInterval(() => {
    homeContentClock.value = Date.now()
  }, 30_000)
  const legacyContentSections = {
    community: 'posts',
    communityReports: 'reports',
    communityAppeals: 'appeals'
  }
  const legacyConsultationSections = {
    mentors: { view: 'applications', caseView: 'reports' },
    mentorOrders: { view: 'orders', caseView: 'reports' },
    mentorAppeals: { view: 'cases', caseView: 'appeals' }
  }
  if (legacyContentSections[options.section]) {
    activeSection.value = 'community'
    contentManagementTab.value = legacyContentSections[options.section]
    contentManagementMountedTabs[contentManagementTab.value] = true
  } else if (legacyConsultationSections[options.section]) {
    activeSection.value = 'consultation'
    consultationInitialView.value = legacyConsultationSections[options.section].view
    consultationInitialCaseView.value = legacyConsultationSections[options.section].caseView
  } else if (['dashboard', 'users', 'consultation', 'admission', 'resources', 'homeOps', 'questions', 'mockExams', 'import'].includes(options.section)) {
    activeSection.value = options.section
  }
  requestedQuestionBankId.value = String(options.question_bank_id || '')
  if (import.meta.env.DEV && options.preview === '1') {
    devPreviewMode.value = true
    loadDevPreview()
    return
  }
  await bootstrap()
})

onUnmounted(() => {
  if (searchTimer) clearTimeout(searchTimer)
  if (communitySearchTimer) clearTimeout(communitySearchTimer)
  if (portalUserSearchTimer) clearTimeout(portalUserSearchTimer)
  if (scorelineSearchTimer) clearTimeout(scorelineSearchTimer)
  if (majorCatalogSearchTimer) clearTimeout(majorCatalogSearchTimer)
  if (homeContentClockTimer) clearInterval(homeContentClockTimer)
})

async function bootstrap() {
  if (!isLoggedIn()) {
    goToPortalLogin()
    return
  }
  portalLoading.value = true
  portalBootstrapError.value = null
  try {
    const me = await fetchQuestionAdminPortalMe()
    applyPortalPermissions(me?.permissions)
    if (me?.profile) {
      authUser.value = updateAuthUser(me.profile) || me.profile
    }
    if (!canAccessSection(activeSection.value)) {
      activeSection.value = canViewQuestions.value ? 'questions' : 'import'
    }
    if (canAccessFullPortal.value) {
      await Promise.all([loadDashboard(), loadQuestionStats()])
    }
    if (activeSection.value === 'community') {
      await refreshContentManagementTab()
    } else if (activeSection.value === 'users') {
      await Promise.all([loadOperationsOverview(), loadPortalUsers()])
    } else if (activeSection.value === 'admission') {
      await Promise.all([loadOperationsOverview(), loadAdmissionWorkspace()])
    } else if (activeSection.value === 'resources') {
      await nextTick()
      await resourceManagementRef.value?.refresh?.()
    } else if (activeSection.value === 'homeOps') {
      await Promise.all([loadOperationsOverview(), loadHomeContent()])
    } else if (activeSection.value === 'mockExams') {
      await nextTick()
    } else if (activeSection.value === 'questions') {
      await loadQuestionBanks()
      const requestedBank = questionBanks.value.find((item) => item.id === requestedQuestionBankId.value)
      if (requestedBank) await openQuestionBank(requestedBank)
    }
  } catch (error) {
    if (isPortalAuthenticationError(error)) {
      goToPortalLogin()
      return
    }
    portalBootstrapError.value = buildPortalBootstrapError(error)
  } finally {
    portalLoading.value = false
  }
}

function isPortalAuthenticationError(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  return statusCode === 401 || error?.code === 'AUTH_REFRESH_REJECTED' || error?.code === 'AUTH_REFRESH_UNAVAILABLE'
}

function buildPortalBootstrapError(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  if (statusCode === 403) {
    return {
      title: '当前账号没有后台管理权限',
      message: '请联系管理员将该账号加入后台管理访问白名单。'
    }
  }
  if (statusCode === 503) {
    return {
      title: '后台管理暂不可用',
      message: '服务正在维护或配置中，请稍后重试。'
    }
  }
  return {
    title: '无法连接后台管理',
    message: '请检查网络后重试；登录状态已保留。'
  }
}

async function loadDashboard() {
  if (devPreviewMode.value) {
    loadDevPreviewDashboard()
    return
  }
  dashboardLoading.value = true
  try {
    const response = await fetchQuestionAdminDashboard({
      subject: dashboardFilters.subject,
      sort_by: dashboardFilters.sort_by,
      min_attempts: 1,
      period_days: dashboardFilters.period_days,
      page: dashboardDifficultPage.value,
      page_size: dashboardDifficultPageSize
    })
    dashboard.today_practicing_users = Number(response?.today_practicing_users || 0)
    dashboard.registered_users = Number(response?.registered_users || 0)
    dashboard.today_registered_users = Number(response?.today_registered_users || 0)
    const difficultQuestions = Array.isArray(response?.difficult_questions) ? response.difficult_questions : []
    dashboard.difficult_questions_count = Number(
      response?.difficult_questions_count == null
        ? difficultQuestions.length
        : response.difficult_questions_count
    )
    dashboardDifficultPage.value = Math.max(1, Number(response?.difficult_questions_page || dashboardDifficultPage.value || 1))
    const dashboardTotalPages = Math.max(
      1,
      Math.ceil(Number(dashboard.difficult_questions_count || difficultQuestions.length || 0) / dashboardDifficultPageSize)
    )
    if (dashboard.difficult_questions_count > 0 && difficultQuestions.length === 0 && dashboardDifficultPage.value > dashboardTotalPages) {
      dashboardDifficultPage.value = dashboardTotalPages
      await loadDashboard()
      return
    }
    dashboard.difficult_questions = difficultQuestions
  } catch (error) {
    dashboard.difficult_questions = []
    dashboard.difficult_questions_count = 0
    uni.showToast({ title: '仪表盘数据加载失败', icon: 'none' })
  } finally {
    dashboardLoading.value = false
  }
}

async function loadCommunityData() {
  if (devPreviewMode.value) {
    loadDevPreviewCommunity()
    return
  }
  communityLoading.value = true
  communityLoadError.value = false
  try {
    const [overviewResponse, postsResponse] = await Promise.all([
      fetchQuestionAdminCommunityOverview(),
      fetchQuestionAdminCommunityPosts({
        status: communityFilters.status,
        post_type: communityFilters.post_type,
        sort_by: communityFilters.sort_by,
        search: communityFilters.search,
        limit: communityPageSize,
        offset: (communityPage.value - 1) * communityPageSize
      })
    ])
    communityOverview.total_posts = Number(overviewResponse?.total_posts || 0)
    communityOverview.published_posts = Number(overviewResponse?.published_posts || 0)
    communityOverview.archived_posts = Number(overviewResponse?.archived_posts || 0)
    communityOverview.today_posts = Number(overviewResponse?.today_posts || 0)
    communityOverview.total_reports = Number(overviewResponse?.total_reports || 0)
    communityOverview.pending_reports = Number(overviewResponse?.pending_reports || 0)
    communityOverview.reviewing_reports = Number(overviewResponse?.reviewing_reports || 0)
    communityPosts.value = Array.isArray(postsResponse?.items) ? postsResponse.items : []
    communityCount.value = Number(postsResponse?.count || 0)
    const totalPages = Math.max(1, Math.ceil(communityCount.value / communityPageSize))
    if (communityCount.value > 0 && communityPosts.value.length === 0 && communityPage.value > totalPages) {
      communityPage.value = totalPages
      await loadCommunityData()
      return
    }
    communitySelectedIds.value = []
  } catch (error) {
    communityPosts.value = []
    communityCount.value = 0
    communityLoadError.value = true
  } finally {
    communityLoading.value = false
  }
}

async function loadQuestionStats(questionBankId = '') {
  const target = questionBankId ? questionStats : globalQuestionStats
  if (!questionBankId && !canAccessFullPortal.value) {
    target.active = 0
    target.archived = 0
    target.pendingReview = 0
    return
  }
  if (devPreviewMode.value) {
    target.active = questionBankId ? 2846 : 11321
    target.archived = questionBankId ? 126 : 326
    target.pendingReview = questionBankId ? 38 : 0
    if (!questionBankId && (!activeQuestionBank.value || activeSection.value === 'review')) {
      Object.assign(questionStats, target)
    }
    return
  }
  try {
    const response = await fetchAdminQuestionStats(
      questionBankId ? { question_bank_id: questionBankId } : {}
    )
    target.active = Number(response?.active || 0)
    target.archived = Number(response?.archived || 0)
    target.pendingReview = Number(response?.pending_review || 0)
  } catch (error) {
    target.active = 0
    target.archived = 0
    target.pendingReview = 0
  }
  if (!questionBankId && (!activeQuestionBank.value || activeSection.value === 'review')) {
    Object.assign(questionStats, target)
  }
}

async function loadQuestionBanks() {
  if (devPreviewMode.value) {
    questionBanks.value = [{
      id: 'preview-question-bank-z',
      name: 'Z',
      question_count: 3010,
      created_at: '2026-07-18T03:00:00Z',
      updated_at: '2026-07-24T10:30:00Z'
    }]
    questionBanksError.value = false
    return
  }
  questionBanksLoading.value = true
  questionBanksError.value = false
  try {
    const response = await fetchAdminQuestionBanks()
    questionBanks.value = Array.isArray(response?.items) ? response.items : []
  } catch (error) {
    questionBanks.value = []
    questionBanksError.value = true
  } finally {
    questionBanksLoading.value = false
  }
}

async function loadQuestions() {
  if (activeSection.value === 'questions' && !activeQuestionBank.value && !showGlobalQuestionList.value) {
    await loadQuestionBanks()
    return
  }
  if (devPreviewMode.value) {
    const status = activeSection.value === 'review' ? QUESTION_STATUS.PENDING_REVIEW : filters.status
    const filtered = previewQuestions.filter((item) => {
      if (filters.subject && item.subject !== filters.subject) return false
      if (filters.module && item.module !== filters.module) return false
      if (filters.difficulty && String(item.difficulty) !== String(filters.difficulty)) return false
      if (filters.search && !`${item.id} ${item.stem}`.toLowerCase().includes(filters.search.toLowerCase())) return false
      if (status && questionDisplayStatus(item) !== status) return false
      return true
    })
    questions.value = [...filtered].sort((left, right) => {
      const createdAtComparison = String(left.created_at || '').localeCompare(String(right.created_at || ''))
      const stableComparison = createdAtComparison || String(left.id || '').localeCompare(String(right.id || ''))
      return questionSortDirection.value === 'asc' ? stableComparison : -stableComparison
    })
    questionCount.value = status ? filtered.length : 3010
    questionsLoading.value = false
    questionLoadError.value = false
    selectedIds.value = []
    return
  }
  questionsLoading.value = true
  questionLoadError.value = false
  try {
    const response = await fetchAdminQuestions({
      ...buildQuestionParams(),
      limit: pageSize,
      offset: (currentPage.value - 1) * pageSize
    })
    questions.value = (response?.items || []).filter((item) => !isAiGeneratedQuestion(item))
    questionCount.value = Number(response?.count || 0)
    selectedIds.value = []
  } catch (error) {
    questions.value = []
    questionCount.value = 0
    questionLoadError.value = true
  } finally {
    questionsLoading.value = false
  }
}

async function switchSection(section) {
  if (!canAccessSection(section)) {
    uni.showToast({ title: '当前账号无此栏目权限', icon: 'none' })
    return
  }
  if (section === 'review') return
  if (activeSection.value === section) {
    if (section === 'questions' && (activeQuestionBank.value || showGlobalQuestionList.value)) {
      await returnToQuestionBanks()
    } else if (section === 'users') {
      await Promise.all([loadOperationsOverview(), loadPortalUsers()])
    } else if (section === 'community') {
      await refreshContentManagementTab()
    } else if (section === 'consultation') {
      await consultationManagementRef.value?.refresh?.()
    } else if (section === 'admission') {
      await Promise.all([loadOperationsOverview(), loadAdmissionWorkspace()])
    } else if (section === 'resources') {
      await resourceManagementRef.value?.refresh?.()
    } else if (section === 'homeOps') {
      await Promise.all([loadOperationsOverview(), loadHomeContent()])
    }
    return
  }
  reviewQuestionBank.value = null
  if (section === 'import') {
    importQuestionBankId.value = activeSection.value === 'questions' ? activeQuestionBank.value?.id || '' : ''
    importQuestionBankName.value = activeSection.value === 'questions' ? activeQuestionBank.value?.name || '' : ''
  } else {
    importPreviewVisible.value = false
  }
  activeSection.value = section
  currentPage.value = 1
  selectedIds.value = []
  communitySelectedIds.value = []
  if (section === 'questions') {
    activeQuestionBank.value = null
    showGlobalQuestionList.value = false
    if (filters.status === QUESTION_STATUS.PENDING_REVIEW) filters.status = ''
    await loadQuestionBanks()
  } else if (section === 'dashboard') {
    await Promise.all([loadDashboard(), loadQuestionStats()])
  } else if (section === 'users') {
    await Promise.all([loadOperationsOverview(), loadPortalUsers()])
  } else if (section === 'community') {
    await refreshContentManagementTab()
  } else if (section === 'consultation') {
    await consultationManagementRef.value?.refresh?.()
  } else if (section === 'admission') {
    await Promise.all([loadOperationsOverview(), loadAdmissionWorkspace()])
  } else if (section === 'resources') {
    await nextTick()
    await resourceManagementRef.value?.refresh?.()
  } else if (section === 'homeOps') {
    await Promise.all([loadOperationsOverview(), loadHomeContent()])
  }
}

function selectContentManagementTab(tab) {
  if (!contentManagementTabs.some((item) => item.key === tab)) return
  contentManagementMountedTabs[tab] = true
  contentManagementTab.value = tab
}

async function refreshContentManagementTab() {
  await nextTick()
  if (contentManagementTab.value === 'reports') {
    await communityModerationRef.value?.refresh?.()
    return
  }
  if (contentManagementTab.value === 'appeals') {
    await communityAppealsRef.value?.refresh?.()
    return
  }
  await loadCommunityData()
}

function toggleSidebarCollapsed() {
  sidebarCollapsed.value = !sidebarCollapsed.value
}

async function refreshCurrentSection() {
  if (refreshing.value) return
  refreshing.value = true
  try {
    if (activeSection.value === 'dashboard') {
      await Promise.all([loadDashboard(), loadQuestionStats()])
    } else if (activeSection.value === 'users') {
      await Promise.all([loadOperationsOverview(), loadPortalUsers()])
    } else if (activeSection.value === 'community') {
      await refreshContentManagementTab()
    } else if (activeSection.value === 'consultation') {
      await consultationManagementRef.value?.refresh?.()
    } else if (activeSection.value === 'admission') {
      await Promise.all([loadOperationsOverview(), loadAdmissionWorkspace()])
    } else if (activeSection.value === 'resources') {
      await resourceManagementRef.value?.refresh?.()
    } else if (activeSection.value === 'homeOps') {
      await Promise.all([loadOperationsOverview(), loadHomeContent()])
    } else if (activeSection.value === 'mockExams') {
      await mockExamManagementRef.value?.refresh?.()
    } else if (activeSection.value === 'questions' && !activeQuestionBank.value && !showGlobalQuestionList.value) {
      await loadQuestionBanks()
    } else if (activeSection.value === 'questions' || activeSection.value === 'review') {
      await refreshQuestionData()
    } else {
      await loadQuestionStats()
    }
  } finally {
    refreshing.value = false
  }
}

function downloadQuestionImportTemplate() {
  questionImageImportRef.value?.downloadImportTemplate?.()
}

function downloadQuestionImportGuide() {
  questionImageImportRef.value?.downloadImportGuide?.()
}

function showQuestionImportHistory() {
  questionImageImportRef.value?.showImportHistory?.()
}

function handleImportPreviewModeChange(visible) {
  importPreviewVisible.value = !!visible
}

async function refreshQuestionData() {
  const questionBankId = activeSection.value === 'questions'
    ? activeQuestionBank.value?.id || ''
    : activeSection.value === 'review'
      ? reviewQuestionBank.value?.id || ''
      : ''
  const tasks = [loadQuestionStats(questionBankId), loadQuestions()]
  if (questionBankId && canAccessFullPortal.value) tasks.push(loadQuestionStats())
  await Promise.all(tasks)
}

function buildQuestionParams() {
  const params = {}
  if (activeSection.value === 'questions' && activeQuestionBank.value?.id) {
    params.question_bank_id = activeQuestionBank.value.id
  } else if (activeSection.value === 'review' && reviewQuestionBank.value?.id) {
    params.question_bank_id = reviewQuestionBank.value.id
  }
  if (filters.subject) params.subject = filters.subject
  if (filters.module) params.module = filters.module
  if (filters.difficulty) params.difficulty = filters.difficulty
  if (filters.search) params.search = filters.search
  params.sort_direction = questionSortDirection.value
  const status = activeSection.value === 'review' ? QUESTION_STATUS.PENDING_REVIEW : filters.status
  if (status === QUESTION_STATUS.PENDING_REVIEW) {
    params.status = QUESTION_STATUS.ARCHIVED
    params.review_status = 'pending'
  } else if (status === QUESTION_STATUS.ARCHIVED) {
    params.status = QUESTION_STATUS.ARCHIVED
    params.exclude_review_status = 'pending'
  } else if (status === QUESTION_STATUS.ACTIVE) {
    params.status = QUESTION_STATUS.ACTIVE
  }
  return params
}

function applyFilters() {
  currentPage.value = 1
  loadQuestions()
}

function clearFilters() {
  filters.subject = ''
  filters.module = ''
  filters.difficulty = ''
  filters.search = ''
  filters.status = activeSection.value === 'review' ? QUESTION_STATUS.PENDING_REVIEW : ''
  applyFilters()
}

function clearSearch() {
  filters.search = ''
  applyFilters()
}

function handleSearchInput() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(applyFilters, 420)
}

function handleSubjectChange(event) {
  filters.subject = QUESTION_SUBJECTS[Number(event?.detail?.value || 0)]?.value || ''
  filters.module = ''
  applyFilters()
}

function handleModuleChange(event) {
  filters.module = moduleOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  applyFilters()
}

function handleDifficultyChange(event) {
  filters.difficulty = difficultyOptions[Number(event?.detail?.value || 0)]?.value || ''
  applyFilters()
}

function handleStatusChange(event) {
  filters.status = statusOptions[Number(event?.detail?.value || 0)]?.value || ''
  applyFilters()
}

function applyCommunityFilters() {
  communityPage.value = 1
  loadCommunityData()
}

function clearCommunityFilters() {
  communityFilters.status = 'all'
  communityFilters.post_type = 'all'
  communityFilters.sort_by = 'newest'
  communityFilters.search = ''
  applyCommunityFilters()
}

function clearCommunitySearch() {
  communityFilters.search = ''
  applyCommunityFilters()
}

function handleCommunitySearchInput() {
  if (communitySearchTimer) clearTimeout(communitySearchTimer)
  communitySearchTimer = setTimeout(applyCommunityFilters, 420)
}

function handleCommunityStatusChange(event) {
  communityFilters.status = communityStatusOptions[Number(event?.detail?.value || 0)]?.value || 'all'
  applyCommunityFilters()
}

function handleCommunityTypeChange(event) {
  communityFilters.post_type = communityTypeOptions[Number(event?.detail?.value || 0)]?.value || 'all'
  applyCommunityFilters()
}

function handleCommunitySortChange(event) {
  communityFilters.sort_by = communitySortOptions[Number(event?.detail?.value || 0)]?.value || 'newest'
  applyCommunityFilters()
}

function handleCommunityBulkFeaturedAction() {
  const action = communityBulkFeaturedAction.value
  if (!action) return
  bulkChangeCommunityFeatured(action.isFeatured)
}

async function handleDashboardSubjectChange(event) {
  dashboardFilters.subject = dashboardSubjectOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  dashboardDifficultPage.value = 1
  await loadDashboard()
}

async function handleDashboardSortChange(event) {
  const value = dashboardSortOptions[Number(event?.detail?.value || 0)]?.value || 'wrong_count'
  if (dashboardFilters.sort_by === value) return
  dashboardFilters.sort_by = value
  dashboardDifficultPage.value = 1
  await loadDashboard()
}

async function handleDashboardTimeRangeChange(event) {
  dashboardFilters.period_days = Number(
    dashboardTimeRangeOptions[Number(event?.detail?.value || 0)]?.value || 0
  )
  dashboardDifficultPage.value = 1
  await loadDashboard()
}

async function applySummaryFilter(status) {
  if (status === QUESTION_STATUS.ACTIVE || status === QUESTION_STATUS.ARCHIVED) return
  if (status === QUESTION_STATUS.PENDING_REVIEW) {
    if (!requireQuestionManagementAccess()) return
    resetReturnedReviewExportBatch()
    reviewQuestionBank.value = activeQuestionBank.value || null
    activeSection.value = 'review'
    activeQuestionBank.value = null
    showGlobalQuestionList.value = false
    filters.status = status
  } else {
    reviewQuestionBank.value = null
    activeSection.value = 'questions'
    showGlobalQuestionList.value = !activeQuestionBank.value
    filters.status = status
  }
  currentPage.value = 1
  const questionBankId = activeSection.value === 'questions'
    ? activeQuestionBank.value?.id || ''
    : activeSection.value === 'review'
      ? reviewQuestionBank.value?.id || ''
      : ''
  await Promise.all([loadQuestionStats(questionBankId), loadQuestions()])
}

function handleSummaryCardTap(item) {
  if (!item?.interactive) return
  applySummaryFilter(item.key)
}

async function startReviewQueue() {
  if (!requireQuestionManagementAccess()) return
  if (questionsLoading.value || drawerLoading.value) return
  const firstPendingQuestion = questions.value.find((item) => (
    questionDisplayStatus(item) === QUESTION_STATUS.PENDING_REVIEW
  ))
  if (!firstPendingQuestion) {
    uni.showToast({ title: '当前没有待审核题目', icon: 'none' })
    return
  }
  await openEditDrawer(firstPendingQuestion, true)
}

function navItemActive(key) {
  return key === activeSection.value || (
    key === 'questions' && ['review', 'mockExams'].includes(activeSection.value)
  )
}

async function openMockExamManagement() {
  if (!requireQuestionManagementAccess()) return
  activeSection.value = 'mockExams'
  activeQuestionBank.value = null
  reviewQuestionBank.value = null
  showGlobalQuestionList.value = false
  currentPage.value = 1
  selectedIds.value = []
  await nextTick()
}

function openQuestionBankDialog(mode, bank = null) {
  if (!requireQuestionManagementAccess()) return
  questionBankDialogMode.value = mode
  questionBankTarget.value = bank
  questionBankNameDraft.value = mode === 'rename' ? String(bank?.name || '') : ''
  questionBankDialogVisible.value = true
}

function closeQuestionBankDialog(force = false) {
  if (questionBankSaving.value && !force) return
  questionBankDialogVisible.value = false
  questionBankTarget.value = null
  questionBankNameDraft.value = ''
}

async function saveQuestionBankDialog() {
  if (!requireQuestionManagementAccess()) return
  if (questionBankSaving.value) return
  const name = String(questionBankNameDraft.value || '').trim()
  if (!name) {
    uni.showToast({ title: '请输入题库名称', icon: 'none' })
    return
  }
  questionBankSaving.value = true
  try {
    if (questionBankDialogMode.value === 'create') {
      await createAdminQuestionBank({ name })
      uni.showToast({ title: '题库已创建', icon: 'success' })
    } else if (questionBankTarget.value?.id) {
      await renameAdminQuestionBank(questionBankTarget.value.id, { name })
      uni.showToast({ title: '题库名称已更新', icon: 'success' })
    }
    closeQuestionBankDialog(true)
    await loadQuestionBanks()
  } catch (error) {
    uni.showToast({
      title: questionBankDialogMode.value === 'create' ? '题库创建失败' : '题库重命名失败',
      icon: 'none'
    })
  } finally {
    questionBankSaving.value = false
  }
}

async function openQuestionBank(bank) {
  if (!bank?.id) return
  activeSection.value = 'questions'
  activeQuestionBank.value = bank
  reviewQuestionBank.value = null
  showGlobalQuestionList.value = false
  currentPage.value = 1
  selectedIds.value = []
  clearFiltersForQuestionBank()
  await Promise.all([loadQuestionStats(bank.id), loadQuestions()])
}

async function returnToQuestionBanks() {
  if (saving.value) return
  drawerVisible.value = false
  activeQuestionBank.value = null
  reviewQuestionBank.value = null
  showGlobalQuestionList.value = false
  currentPage.value = 1
  selectedIds.value = []
  clearFiltersForQuestionBank()
  Object.assign(questionStats, globalQuestionStats)
  await loadQuestionBanks()
}

async function returnFromImportSection() {
  if (importPreviewVisible.value && questionImageImportRef.value?.returnToFileSelection) {
    questionImageImportRef.value.returnToFileSelection()
    importPreviewVisible.value = false
    return
  }
  if (importQuestionBankId.value) {
    activeSection.value = 'questions'
    const bank = questionBanks.value.find((item) => item.id === importQuestionBankId.value) || {
      id: importQuestionBankId.value,
      name: importQuestionBankName.value || '题库'
    }
    activeQuestionBank.value = bank
    reviewQuestionBank.value = null
    showGlobalQuestionList.value = false
    currentPage.value = 1
    selectedIds.value = []
    clearFiltersForQuestionBank()
    await Promise.all([loadQuestionStats(bank.id), loadQuestions()])
    return
  }
  activeSection.value = 'questions'
  await returnToQuestionBanks()
}

async function returnFromReviewSection() {
  const bank = reviewQuestionBank.value
  activeSection.value = 'questions'
  reviewQuestionBank.value = null
  currentPage.value = 1
  selectedIds.value = []
  clearFiltersForQuestionBank()
  if (bank?.id) {
    activeQuestionBank.value = bank
    showGlobalQuestionList.value = false
    await Promise.all([loadQuestionStats(bank.id), loadQuestions()])
    return
  }
  activeQuestionBank.value = null
  showGlobalQuestionList.value = false
  Object.assign(questionStats, globalQuestionStats)
  await loadQuestionBanks()
}

async function returnFromMockExamSection() {
  const editorClosed = await mockExamManagementRef.value?.closeEditor?.()
  if (editorClosed) return
  activeSection.value = 'questions'
  await returnToQuestionBanks()
}

async function handleHeaderBack() {
  if (activeSection.value === 'import') {
    await returnFromImportSection()
    return
  }
  if (activeSection.value === 'review') {
    await returnFromReviewSection()
    return
  }
  if (activeSection.value === 'mockExams') {
    await returnFromMockExamSection()
    return
  }
  await returnToQuestionBanks()
}

function clearFiltersForQuestionBank() {
  filters.subject = ''
  filters.module = ''
  filters.difficulty = ''
  filters.status = ''
  filters.search = ''
}

function changePage(page) {
  const next = Math.max(1, Math.min(totalPages.value, Number(page || 1)))
  if (next === currentPage.value) return
  currentPage.value = next
  loadQuestions()
}

function toggleQuestionDateSort() {
  questionSortDirection.value = questionSortDirection.value === 'desc' ? 'asc' : 'desc'
  currentPage.value = 1
  loadQuestions()
}

function changeDashboardDifficultPage(page) {
  const next = Math.max(1, Math.min(dashboardDifficultTotalPages.value, Number(page || 1)))
  if (next === dashboardDifficultPage.value) return
  dashboardDifficultPage.value = next
  loadDashboard()
}

function changeCommunityPage(page) {
  const next = Math.max(1, Math.min(communityTotalPages.value, Number(page || 1)))
  if (next === communityPage.value) return
  communityPage.value = next
  loadCommunityData()
}

function isCommunitySelected(id) {
  return communitySelectedSet.value.has(id)
}

function toggleCommunitySelection(id) {
  communitySelectedIds.value = isCommunitySelected(id)
    ? communitySelectedIds.value.filter((item) => item !== id)
    : [...communitySelectedIds.value, id]
}

function toggleSelectCommunityPage() {
  if (allCommunityPageSelected.value) {
    const visibleIds = new Set(communityPosts.value.map((item) => item.id))
    communitySelectedIds.value = communitySelectedIds.value.filter((id) => !visibleIds.has(id))
    return
  }
  communitySelectedIds.value = Array.from(new Set([
    ...communitySelectedIds.value,
    ...communityPosts.value.map((item) => item.id)
  ]))
}

function closeCommunityPostDetail(force = false) {
  if (communitySaving.value && !force) return
  communityDetailVisible.value = false
  communityDetailLoading.value = false
  communityDetail.value = null
}

async function openCommunityPostDetail(item) {
  if (!item?.id || communitySaving.value) return
  communityDetailVisible.value = true
  communityDetailLoading.value = true
  communityDetail.value = null
  if (devPreviewMode.value) {
    const post = previewCommunityPosts.find((candidate) => candidate.id === item.id) || item
    communityDetail.value = {
      post: { ...post },
      comments: Array.isArray(post.comments) ? post.comments : []
    }
    communityDetailLoading.value = false
    return
  }
  try {
    const response = await fetchQuestionAdminCommunityPostDetail(item.id)
    if (!response?.post) throw new Error('Community post not found')
    communityDetail.value = response
  } catch (error) {
    closeCommunityPostDetail(true)
    uni.showToast({ title: '帖子详情加载失败', icon: 'none' })
  } finally {
    communityDetailLoading.value = false
  }
}

async function toggleCommunityPostVisibility(item) {
  if (!item?.id || communitySaving.value) return
  const publish = !item.is_published
  const actionText = publish ? '恢复展示' : '下架'
  const confirmed = await confirmAction(
    `确认${actionText}？`,
    publish
      ? '恢复后，帖子会重新对用户可见。'
      : '下架后，帖子将不再对用户可见，但可在后台恢复。',
    actionText
  )
  if (!confirmed) return
  communitySaving.value = true
  try {
    let updatedPost = null
    if (devPreviewMode.value) {
      const previewPost = previewCommunityPosts.find((candidate) => candidate.id === item.id)
      if (previewPost) {
        previewPost.is_published = publish
        previewPost.updated_at = new Date().toISOString()
        updatedPost = { ...previewPost }
      }
    } else {
      updatedPost = await updateQuestionAdminCommunityPostVisibility(item.id, { is_published: publish })
    }
    if (communityDetail.value?.post?.id === item.id && updatedPost) {
      communityDetail.value = { ...communityDetail.value, post: updatedPost }
    }
    uni.showToast({ title: publish ? '帖子已恢复' : '帖子已下架', icon: 'success' })
    await loadCommunityData()
  } catch (error) {
    uni.showToast({ title: publish ? '帖子恢复失败' : '帖子下架失败', icon: 'none' })
  } finally {
    communitySaving.value = false
  }
}

async function toggleCommunityCommentVisibility(post, comment) {
  if (!post?.id || !comment?.id || communitySaving.value) return
  const publish = comment.is_published === false
  const actionText = publish ? '恢复展示' : '下架'
  const confirmed = await confirmAction(
    `确认${actionText}这条评论？`,
    publish
      ? '恢复后，评论会重新对用户可见，并同步更新相关处理记录。'
      : '下架后，评论将不再对用户可见；作者可在“我的举报”的“内容处理”中查看原因并提交申诉。',
    actionText
  )
  if (!confirmed) return
  communitySaving.value = true
  try {
    let updatedComment = null
    if (devPreviewMode.value) {
      const previewPost = previewCommunityPosts.find((candidate) => candidate.id === post.id)
      const previewComment = previewPost?.comments?.find((candidate) => candidate.id === comment.id)
      if (previewComment) {
        previewComment.is_published = publish
        previewComment.moderated_at = new Date().toISOString()
        updatedComment = { ...previewComment }
      }
    } else {
      updatedComment = await updateQuestionAdminCommunityCommentVisibility(post.id, comment.id, { is_published: publish })
    }
    if (communityDetail.value?.post?.id === post.id && updatedComment) {
      communityDetail.value = {
        ...communityDetail.value,
        comments: (communityDetail.value.comments || []).map((item) => item.id === comment.id ? { ...item, ...updatedComment } : item)
      }
    }
    uni.showToast({ title: publish ? '评论已恢复' : '评论已下架', icon: 'success' })
    await loadCommunityData()
  } catch (error) {
    uni.showToast({ title: publish ? '评论恢复失败' : '评论下架失败', icon: 'none' })
  } finally {
    communitySaving.value = false
  }
}

async function bulkChangeCommunityVisibility(isPublished) {
  if (!communitySelectedIds.value.length || communitySaving.value) return
  const actionText = isPublished ? '恢复展示' : '下架'
  const confirmed = await confirmAction(
    `确认批量${actionText}？`,
    `将对已选择的 ${communitySelectedIds.value.length} 条帖子执行${actionText}。`,
    actionText
  )
  if (!confirmed) return
  communitySaving.value = true
  try {
    let updatedCount = 0
    if (devPreviewMode.value) {
      const selected = new Set(communitySelectedIds.value)
      previewCommunityPosts.forEach((item) => {
        if (!selected.has(item.id)) return
        item.is_published = isPublished
        item.updated_at = new Date().toISOString()
        updatedCount += 1
      })
    } else {
      const response = await bulkUpdateQuestionAdminCommunityPostVisibility({
        ids: communitySelectedIds.value,
        is_published: isPublished
      })
      updatedCount = Number(response?.updated_count || 0)
    }
    uni.showToast({ title: `已处理 ${updatedCount} 条`, icon: 'success' })
    await loadCommunityData()
  } catch (error) {
    uni.showToast({ title: '批量操作失败', icon: 'none' })
  } finally {
    communitySaving.value = false
  }
}

async function bulkChangeCommunityFeatured(isFeatured) {
  if (!communitySelectedIds.value.length || communitySaving.value || typeof isFeatured !== 'boolean') return
  const actionText = isFeatured ? '加入精选' : '移出精选'
  const confirmed = await confirmAction(
    `确认${actionText}？`,
    isFeatured
      ? `已选择的 ${communitySelectedIds.value.length} 条帖子会标记为精选；当前公开展示的帖子会进入用户端“精选”列表，并以随机顺序展示。`
      : `已选择的 ${communitySelectedIds.value.length} 条帖子会从用户端“精选”列表移除。`,
    actionText
  )
  if (!confirmed) return
  communitySaving.value = true
  try {
    let updatedCount = 0
    if (devPreviewMode.value) {
      const selected = new Set(communitySelectedIds.value)
      previewCommunityPosts.forEach((item) => {
        if (!selected.has(item.id)) return
        item.is_featured = isFeatured
        item.updated_at = new Date().toISOString()
        updatedCount += 1
      })
    } else {
      const response = await bulkUpdateQuestionAdminCommunityPostFeatured({
        ids: communitySelectedIds.value,
        is_featured: isFeatured
      })
      updatedCount = Number(response?.updated_count || 0)
    }
    uni.showToast({ title: `${actionText} ${updatedCount} 条`, icon: 'success' })
    await loadCommunityData()
  } catch (error) {
    uni.showToast({ title: '精选状态更新失败', icon: 'none' })
  } finally {
    communitySaving.value = false
  }
}

function isSelected(id) {
  return selectedSet.value.has(id)
}

function toggleSelection(id) {
  if (!canManageQuestions.value) return
  selectedIds.value = isSelected(id)
    ? selectedIds.value.filter((item) => item !== id)
    : [...selectedIds.value, id]
}

function toggleCurrentQuestionSelection() {
  if (!canManageQuestions.value) return
  if (!form.id) return
  toggleSelection(form.id)
}

function toggleSelectPage() {
  if (!canManageQuestions.value) return
  if (allPageSelected.value) {
    const visibleIds = new Set(questions.value.map((item) => item.id))
    selectedIds.value = selectedIds.value.filter((id) => !visibleIds.has(id))
    return
  }
  selectedIds.value = Array.from(new Set([
    ...selectedIds.value,
    ...questions.value.map((item) => item.id)
  ]))
}

async function bulkChangeStatus(status) {
  if (!requireQuestionManagementAccess()) return
  if (!selectedIds.value.length) return
  const actionText = status === QUESTION_STATUS.ACTIVE ? '发布' : '下架'
  const isBulk = selectedIds.value.length > 1
  const confirmed = await confirmAction(
    `确认${isBulk ? '批量' : ''}${actionText}？`,
    `将对已选择的 ${selectedIds.value.length} 道题执行${actionText}。`,
    actionText
  )
  if (!confirmed) return
  try {
    const response = await bulkUpdateAdminQuestionStatus({
      status,
      ids: selectedIds.value
    })
    uni.showToast({ title: `已${actionText} ${response?.updated_count || 0} 道`, icon: 'success' })
    selectedIds.value = []
    await refreshQuestionData()
  } catch (error) {
    uni.showToast({ title: `批量${actionText}失败`, icon: 'none' })
  }
}

async function deleteSelectedQuestions() {
  if (!requireQuestionManagementAccess()) return
  if (!selectedIds.value.length) return
  const confirmed = await confirmAction(
    '确认删除题目？',
    `将删除已选择的 ${selectedIds.value.length} 道题。删除后不可恢复，请确认。`,
    '删除'
  )
  if (!confirmed) return
  try {
    const response = await deleteAdminQuestions({ ids: selectedIds.value })
    uni.showToast({ title: `已删除 ${response?.deleted_count || 0} 道`, icon: 'success' })
    selectedIds.value = []
    await refreshQuestionData()
  } catch (error) {
    uni.showToast({ title: '删除题目失败', icon: 'none' })
  }
}

async function openPublishQuestionBankDialog() {
  if (!requireQuestionManagementAccess()) return
  if (publishingQuestions.value) return
  publishQuestionBankId.value = ''
  publishPendingPreview.value = null
  publishPendingPreviewError.value = false
  publishQuestionBankDialogVisible.value = true
  await loadQuestionBanks()
}

async function confirmPublishReviewQueue() {
  if (!requireQuestionManagementAccess()) return
  if (publishingQuestions.value || activeSection.value !== 'review') return

  const targetBank = reviewQuestionBank.value
  if (targetBank?.id) {
    publishingQuestions.value = true
    try {
      const preview = await fetchAdminQuestionBankPendingPublishPreview(targetBank.id)
      const pendingCount = Number(preview?.pending_count || 0)
      if (pendingCount <= 0) {
        uni.showToast({ title: '当前题库暂无待审核题目', icon: 'none' })
        await refreshQuestionData()
        return
      }
      const confirmed = await confirmAction(
        '是否确认发布？',
        `将发布题库“${targetBank.name}”中的 ${pendingCount} 道待审核题目，发布后用户将立即可见。`,
        '确认发布'
      )
      if (!confirmed) return

      const response = await publishAdminQuestionBankPendingQuestions(targetBank.id, {
        expected_pending_count: pendingCount
      })
      const updatedCount = Number(response?.updated_count || 0)
      uni.showToast({
        title: updatedCount > 0 ? `已发布 ${updatedCount} 道题` : '当前题库暂无待审核题目',
        icon: updatedCount > 0 ? 'success' : 'none'
      })
      await refreshQuestionData()
      maybeExportReturnedReviewBatch()
    } catch (error) {
      uni.showToast({ title: '发布失败，请刷新后重试', icon: 'none' })
    } finally {
      publishingQuestions.value = false
    }
    return
  }

  const reviewIds = questions.value
    .filter((item) => questionDisplayStatus(item) === QUESTION_STATUS.PENDING_REVIEW)
    .map((item) => item.id)
    .filter(Boolean)
  if (!reviewIds.length) {
    uni.showToast({ title: '当前没有待审核题目', icon: 'none' })
    return
  }
  const confirmed = await confirmAction(
    '是否确认发布？',
    `将发布当前列表中的 ${reviewIds.length} 道待审核题目，发布后用户将立即可见。`,
    '确认发布'
  )
  if (!confirmed) return

  publishingQuestions.value = true
  try {
    const response = await bulkUpdateAdminQuestionStatus({
      status: QUESTION_STATUS.ACTIVE,
      ids: reviewIds
    })
    const updatedCount = Number(response?.updated_count || 0)
    uni.showToast({
      title: updatedCount > 0 ? `已发布 ${updatedCount} 道题` : '当前没有待审核题目',
      icon: updatedCount > 0 ? 'success' : 'none'
    })
    await refreshQuestionData()
    maybeExportReturnedReviewBatch()
  } catch (error) {
    uni.showToast({ title: '发布失败，请刷新后重试', icon: 'none' })
  } finally {
    publishingQuestions.value = false
  }
}

function closePublishQuestionBankDialog(force = false) {
  if (publishingQuestions.value && !force) return
  publishQuestionBankDialogVisible.value = false
  publishQuestionBankId.value = ''
  publishPendingPreview.value = null
  publishPendingPreviewError.value = false
}

async function selectPublishQuestionBank(bank) {
  if (!bank?.id || publishingQuestions.value) return
  publishQuestionBankId.value = bank.id
  await loadPublishPendingPreview()
}

async function loadPublishPendingPreview() {
  if (!publishQuestionBankId.value) return
  const targetBankId = publishQuestionBankId.value
  publishPendingPreview.value = null
  publishPendingPreviewError.value = false
  publishPendingPreviewLoading.value = true
  try {
    const preview = await fetchAdminQuestionBankPendingPublishPreview(targetBankId)
    if (publishQuestionBankId.value === targetBankId) {
      publishPendingPreview.value = preview || null
    }
  } catch (error) {
    if (publishQuestionBankId.value === targetBankId) {
      publishPendingPreviewError.value = true
    }
  } finally {
    if (publishQuestionBankId.value === targetBankId) {
      publishPendingPreviewLoading.value = false
    }
  }
}

async function publishPendingQuestionsToBank() {
  if (!requireQuestionManagementAccess()) return
  if (publishingQuestions.value || !publishQuestionBankId.value || !publishPendingPreview.value) return
  const targetBank = questionBanks.value.find((bank) => bank.id === publishQuestionBankId.value)
  if (!targetBank) {
    uni.showToast({ title: '请选择题库文件', icon: 'none' })
    return
  }

  const pendingCount = Number(publishPendingPreview.value.pending_count || 0)
  if (pendingCount <= 0) {
    uni.showToast({ title: '该题库暂无待审核题目', icon: 'none' })
    return
  }
  const confirmed = await confirmAction(
    '确认发布待审核题目？',
    `题库“${targetBank.name}”将发布 ${pendingCount} 道待审核题目，发布后用户将立即可见。`,
    '确认发布'
  )
  if (!confirmed) return

  publishingQuestions.value = true
  try {
    const response = await publishAdminQuestionBankPendingQuestions(targetBank.id, {
      expected_pending_count: pendingCount
    })
    const updatedCount = Number(response?.updated_count || 0)
    closePublishQuestionBankDialog(true)
    uni.showToast({
      title: updatedCount > 0 ? `已发布 ${updatedCount} 道题` : '该题库暂无待审核题目',
      icon: updatedCount > 0 ? 'success' : 'none'
    })
    await refreshQuestionData()
  } catch (error) {
    await loadPublishPendingPreview()
    uni.showToast({ title: '题目数量可能已变化，请重新确认', icon: 'none' })
  } finally {
    publishingQuestions.value = false
  }
}

function openCreateDrawer() {
  if (!requireQuestionManagementAccess()) return
  resetForm({
    subject: filters.subject || '英语运用',
    module: filters.module || '',
    difficulty: filters.difficulty || 2
  })
  drawerMode.value = 'create'
  drawerVisible.value = true
}

async function openEditDrawer(item, review = false) {
  if (review && !requireQuestionManagementAccess()) return
  drawerVisible.value = true
  drawerLoading.value = true
  drawerMode.value = review ? 'review' : 'edit'
  if (devPreviewMode.value) {
    fillForm(previewQuestions.find((question) => question.id === item.id) || item)
    drawerLoading.value = false
    return
  }
  try {
    const response = await fetchAdminQuestionDetail(item.id)
    fillForm(response?.question || item)
  } catch (error) {
    drawerVisible.value = false
    uni.showToast({ title: '题目详情加载失败', icon: 'none' })
  } finally {
    drawerLoading.value = false
  }
}

async function openQuestionById(questionId) {
  await openEditDrawer({ id: questionId }, false)
}

function resetForm(seed = {}) {
  form.id = ''
  form.subject = QUESTION_CATALOG[seed.subject] ? seed.subject : '英语运用'
  form.module = seed.module || ''
  form.submodule = ''
  form.stem = ''
  form.option_a = ''
  form.option_b = ''
  form.option_c = ''
  form.option_d = ''
  form.answer = 'A'
  form.explanation = ''
  form.difficulty = Number(seed.difficulty || 2)
  form.status = 'archived'
  form.review_status = 'pending'
  form.review_note = ''
  form.source_type = 'manual'
  form.source_year = ''
  form.original_review_note = ''
  syncEditorClassification()
}

function fillForm(question) {
  form.id = String(question?.id || '')
  form.subject = QUESTION_CATALOG[question?.subject] ? question.subject : '英语运用'
  form.module = String(question?.module || '')
  form.submodule = String(question?.submodule || '')
  syncEditorClassification()
  form.stem = String(question?.stem || '')
  form.option_a = String(question?.option_a || '')
  form.option_b = String(question?.option_b || '')
  form.option_c = String(question?.option_c || '')
  form.option_d = String(question?.option_d || '')
  form.answer = answerOptions.includes(question?.answer) ? question.answer : 'A'
  form.explanation = String(question?.explanation || '')
  form.difficulty = Number(question?.difficulty || 2)
  form.status = String(question?.status || 'archived')
  form.review_status = String(question?.review_status || 'pending')
  form.review_note = String(question?.review_note || '')
  form.source_type = String(question?.source_type || 'manual')
  form.source_year = question?.source_year == null ? '' : String(question.source_year)
  form.original_review_note = String(question?.review_note || '')
}

function syncEditorClassification() {
  const catalog = QUESTION_CATALOG[form.subject] || QUESTION_CATALOG['英语运用']
  form.subject = QUESTION_CATALOG[form.subject] ? form.subject : '英语运用'
  form.exam_code = catalog.exam_code
  const modules = Object.keys(catalog.modules)
  if (!modules.includes(form.module)) form.module = modules[0] || ''
  const submodules = catalog.modules[form.module] || []
  if (!submodules.includes(form.submodule)) form.submodule = submodules[0] || ''
}

function handleEditorSubjectChange(event) {
  form.subject = editorSubjects.value[Number(event?.detail?.value || 0)] || '英语运用'
  form.module = ''
  form.submodule = ''
  syncEditorClassification()
}

function handleEditorModuleChange(event) {
  form.module = editorModules.value[Number(event?.detail?.value || 0)] || ''
  form.submodule = ''
  syncEditorClassification()
}

function handleEditorSubmoduleChange(event) {
  form.submodule = editorSubmodules.value[Number(event?.detail?.value || 0)] || ''
  syncEditorClassification()
}

function buildEditablePayload() {
  syncEditorClassification()
  const payload = {
    exam_code: form.exam_code,
    subject: String(form.subject || '').trim(),
    module: String(form.module || '').trim(),
    submodule: String(form.submodule || '').trim(),
    stem: String(form.stem || '').trim(),
    option_a: String(form.option_a || '').trim(),
    option_b: String(form.option_b || '').trim(),
    option_c: String(form.option_c || '').trim(),
    option_d: String(form.option_d || '').trim(),
    answer: form.answer,
    explanation: String(form.explanation || '').trim(),
    difficulty: Number(form.difficulty || 2)
  }
  const required = ['subject', 'module', 'submodule', 'stem', 'option_a', 'option_b', 'option_c', 'option_d', 'answer']
  if (required.some((field) => !String(payload[field] || '').trim())) {
    uni.showToast({ title: '请补全分类、题干、选项和答案', icon: 'none' })
    return null
  }
  return payload
}

async function createQuestion(target) {
  if (!requireQuestionManagementAccess()) return
  if (saving.value) return
  const editable = buildEditablePayload()
  if (!editable) return
  if (target === 'publish') {
    const confirmed = await confirmAction('确认直接发布？', '新题将跳过待审核队列并立即进入正式题库。', '发布')
    if (!confirmed) return
  }
  saving.value = true
  try {
    await createAdminQuestion({
      ...editable,
      question_bank_id: activeQuestionBank.value?.id || null,
      question_type: 'single_choice',
      source_type: 'manual',
      source_year: null,
      status: target === 'publish' ? QUESTION_STATUS.ACTIVE : QUESTION_STATUS.ARCHIVED,
      review_status: target === 'publish' ? 'approved' : 'pending',
      review_note: null
    })
    uni.showToast({ title: target === 'publish' ? '题目已发布' : '已进入待审核', icon: 'success' })
    drawerVisible.value = false
    await refreshQuestionData()
  } catch (error) {
    uni.showToast({ title: '新增题目失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

async function saveQuestionEdits(showSuccess = true) {
  if (!requireQuestionManagementAccess()) return false
  if (saving.value || !form.id) return false
  const payload = buildEditablePayload()
  if (!payload) return false
  saving.value = true
  try {
    const response = await updateAdminQuestion(form.id, payload)
    fillForm(response?.question || { ...form, ...payload })
    if (showSuccess) uni.showToast({ title: '修改已保存', icon: 'success' })
    await loadQuestions()
    return true
  } catch (error) {
    uni.showToast({ title: '保存失败', icon: 'none' })
    return false
  } finally {
    saving.value = false
  }
}

async function approveAndPublish() {
  if (!requireQuestionManagementAccess()) return
  if (!form.id || saving.value) return
  const saved = await saveQuestionEdits(false)
  if (!saved) return
  saving.value = true
  try {
    await updateAdminQuestionReview(form.id, {
      review_status: 'approved',
      review_note: form.review_note || null,
      publish: true
    })
    uni.showToast({ title: '审核通过并已发布', icon: 'success' })
    drawerVisible.value = false
    await refreshQuestionData()
  } catch (error) {
    uni.showToast({ title: '审核操作失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

async function markNeedsChanges() {
  if (!requireQuestionManagementAccess()) return
  if (!form.id || saving.value) return
  if (!String(form.review_note || '').trim()) {
    uni.showToast({ title: '请填写需要修改的原因', icon: 'none' })
    return
  }
  saving.value = true
  try {
    await updateAdminQuestionReview(form.id, {
      review_status: 'needs_changes',
      review_note: form.review_note,
      publish: false
    })
    rememberReturnedReviewQuestion({
      ...form,
      return_reason: form.review_note,
      import_note: form.original_review_note
    })
    uni.showToast({ title: '已标记为需要修改', icon: 'success' })
    drawerVisible.value = false
    await refreshQuestionData()
    maybeExportReturnedReviewBatch()
  } catch (error) {
    uni.showToast({ title: '审核操作失败', icon: 'none' })
  } finally {
    saving.value = false
  }
}

function resetReturnedReviewExportBatch() {
  returnedReviewQuestions.value = []
  returnedReviewBatchExported.value = false
}

function rememberReturnedReviewQuestion(question) {
  const item = normalizeReturnedReviewQuestion(question)
  const key = item.question_id || `${item.stem}-${item.return_reason}`
  returnedReviewQuestions.value = [
    ...returnedReviewQuestions.value.filter((existing) => (
      (existing.question_id || `${existing.stem}-${existing.return_reason}`) !== key
    )),
    item
  ]
  returnedReviewBatchExported.value = false
}

function normalizeReturnedReviewQuestion(question) {
  const subject = String(question?.subject || '').trim()
  const catalog = QUESTION_CATALOG[subject] || {}
  return {
    question_id: String(question?.id || question?.question_id || ''),
    exam_code: String(question?.exam_code || catalog.exam_code || '').trim(),
    subject,
    module: String(question?.module || '').trim(),
    submodule: String(question?.submodule || '').trim(),
    stem: String(question?.stem || '').trim(),
    option_a: String(question?.option_a || '').trim(),
    option_b: String(question?.option_b || '').trim(),
    option_c: String(question?.option_c || '').trim(),
    option_d: String(question?.option_d || '').trim(),
    answer: String(question?.answer || '').trim().toUpperCase(),
    explanation: String(question?.explanation || '').trim(),
    difficulty: String(question?.difficulty || '').trim(),
    source_type: String(question?.source_type || 'manual').trim() || 'manual',
    source_year: question?.source_year == null ? '' : String(question.source_year).trim(),
    return_reason: String(question?.return_reason || question?.review_note || '需要修改').trim(),
    reviewer: profileName,
    reviewed_at: formatExportDateTime(new Date()),
    question_bank_name: reviewQuestionBank.value?.name || activeQuestionBank.value?.name || '',
    import_note: String(question?.import_note || question?.original_review_note || '').trim()
  }
}

function maybeExportReturnedReviewBatch(force = false) {
  if (!returnedReviewQuestions.value.length || returnedReviewBatchExported.value) return
  if (!force && Number(questionCount.value || 0) > 0) return

  try {
    downloadReturnedQuestionsWorkbook(returnedReviewQuestions.value, {
      bankName: reviewQuestionBank.value?.name || activeQuestionBank.value?.name || '题库',
      reviewer: profileName,
      reviewedAt: formatExportDateTime(new Date())
    })
    returnedReviewBatchExported.value = true
    uni.showToast({
      title: `已导出 ${returnedReviewQuestions.value.length} 道退回题`,
      icon: 'success'
    })
  } catch (error) {
    uni.showToast({ title: '退回 Excel 导出失败', icon: 'none' })
  }
}

function formatExportDateTime(value) {
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

async function toggleCurrentQuestionStatus() {
  if (!requireQuestionManagementAccess()) return
  if (!form.id || saving.value) return
  const next = questionDisplayStatus(form) === QUESTION_STATUS.ACTIVE
    ? QUESTION_STATUS.ARCHIVED
    : QUESTION_STATUS.ACTIVE
  const label = next === QUESTION_STATUS.ACTIVE ? '发布' : '下架'
  const confirmed = await confirmAction(
    `确认${label}题目？`,
    next === QUESTION_STATUS.ACTIVE
      ? '发布后题目将进入普通刷题抽题范围。'
      : '下架后题目不会进入新练习，但历史记录仍保留。',
    label
  )
  if (!confirmed) return
  saving.value = true
  try {
    const response = await updateAdminQuestionStatus(form.id, { status: next })
    fillForm(response?.question || { ...form, status: next })
    uni.showToast({ title: `题目已${label}`, icon: 'success' })
    await refreshQuestionData()
  } catch (error) {
    uni.showToast({ title: `${label}失败`, icon: 'none' })
  } finally {
    saving.value = false
  }
}

function requestCloseDrawer() {
  if (saving.value) return
  drawerVisible.value = false
}

function openImportWorkspace() {
  if (!canImportQuestions.value) {
    uni.showToast({ title: '当前账号无批量导入权限', icon: 'none' })
    return
  }
  importQuestionBankId.value = activeSection.value === 'questions' ? activeQuestionBank.value?.id || '' : ''
  importQuestionBankName.value = activeSection.value === 'questions' ? activeQuestionBank.value?.name || '' : ''
  importPreviewVisible.value = false
  activeSection.value = 'import'
}

function logout() {
  if (devPreviewMode.value) {
    goToPortalLogin()
    return
  }
  uni.showModal({
    title: '退出后台管理？',
    content: '退出后需要重新输入内部账号和密码。',
    confirmText: '退出',
    confirmColor: '#d85a5a',
    success(result) {
      if (!result.confirm) return
      clearAuthSession()
      goToPortalLogin()
    }
  })
}

function goToPortalLogin() {
  const redirect = encodeURIComponent('/pages-sub-admin/admin/question-desktop')
  uni.reLaunch({ url: `/pages/login/index?portal=1&redirect=${redirect}` })
}

function loadDevPreview() {
  applyPortalPermissions()
  authUser.value = {
    id: 'preview-user',
    email: 'editor@ganguantong.local',
    nickname: '题库老师'
  }
  portalLoading.value = false
  loadDevPreviewDashboard()
  loadQuestionStats()
  if (activeSection.value === 'questions') {
    loadQuestionBanks().then(() => {
      const requestedBank = questionBanks.value.find((item) => item.id === requestedQuestionBankId.value)
      if (requestedBank) openQuestionBank(requestedBank)
    })
  } else if (activeSection.value === 'community') {
    loadDevPreviewCommunity()
  } else if (activeSection.value === 'users') {
    loadDevPreviewOperations()
  } else if (activeSection.value === 'admission') {
    loadDevPreviewOperations()
    loadDevPreviewAdmission()
    ensureSelectedAdmissionRun()
    if (admissionDataset.value === 'scorelines') {
      loadScorelineRecords()
    } else if (admissionDataset.value === 'announcements') {
      loadAnnouncementRecords()
    }
  } else if (activeSection.value === 'homeOps') {
    loadDevPreviewOperations()
    loadDevPreviewHomeContent()
  } else if (activeSection.value === 'review') {
    loadQuestions()
  }
}

function loadDevPreviewDashboard() {
  dashboard.today_practicing_users = 186
  dashboard.registered_users = 1286
  dashboard.today_registered_users = 6
  const previewItems = [
    {
      question_id: previewQuestions[3].id,
      stem: previewQuestions[3].stem,
      subject: previewQuestions[3].subject,
      module: previewQuestions[3].module,
      wrong_count: 89,
      attempt_count: 152,
      accuracy: 41.4,
      latest_answered_at: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      question_id: previewQuestions[2].id,
      stem: previewQuestions[2].stem,
      subject: previewQuestions[2].subject,
      module: previewQuestions[2].module,
      wrong_count: 76,
      attempt_count: 113,
      accuracy: 32.7,
      latest_answered_at: new Date(Date.now() - 9 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      question_id: previewQuestions[1].id,
      stem: previewQuestions[1].stem,
      subject: previewQuestions[1].subject,
      module: previewQuestions[1].module,
      wrong_count: 64,
      attempt_count: 174,
      accuracy: 63.2,
      latest_answered_at: new Date(Date.now() - 18 * 24 * 60 * 60 * 1000).toISOString()
    },
    {
      question_id: previewQuestions[0].id,
      stem: previewQuestions[0].stem,
      subject: previewQuestions[0].subject,
      module: previewQuestions[0].module,
      wrong_count: 43,
      attempt_count: 201,
      accuracy: 78.6,
      latest_answered_at: new Date(Date.now() - 43 * 24 * 60 * 60 * 1000).toISOString()
    }
  ]
  const periodDays = Number(dashboardFilters.period_days || 0)
  const periodStart = periodDays ? Date.now() - periodDays * 24 * 60 * 60 * 1000 : 0
  const filteredItems = previewItems.filter((item) => {
    if (dashboardFilters.subject && item.subject !== dashboardFilters.subject) return false
    if (periodStart && new Date(item.latest_answered_at).getTime() < periodStart) return false
    return true
  })
  filteredItems.sort((left, right) => {
    if (dashboardFilters.sort_by === 'accuracy') {
      return left.accuracy - right.accuracy || right.wrong_count - left.wrong_count
    }
    if (dashboardFilters.sort_by === 'attempt_count') {
      return right.attempt_count - left.attempt_count || right.wrong_count - left.wrong_count
    }
    return right.wrong_count - left.wrong_count || right.attempt_count - left.attempt_count
  })
  dashboard.difficult_questions_count = filteredItems.length
  const offset = (dashboardDifficultPage.value - 1) * dashboardDifficultPageSize
  dashboard.difficult_questions = filteredItems.slice(offset, offset + dashboardDifficultPageSize)
}

function loadDevPreviewCommunity() {
  const keyword = String(communityFilters.search || '').trim().toLowerCase()
  const filtered = previewCommunityPosts.filter((item) => {
    if (communityFilters.status === 'published' && !item.is_published) return false
    if (communityFilters.status === 'featured' && !item.is_featured) return false
    if (communityFilters.status === 'archived' && item.is_published) return false
    if (communityFilters.post_type !== 'all' && item.post_type !== communityFilters.post_type) return false
    if (keyword) {
      const searchable = `${item.title} ${item.content} ${item.author_name} ${item.category}`.toLowerCase()
      if (!searchable.includes(keyword)) return false
    }
    return true
  })
  filtered.sort((left, right) => {
    if (communityFilters.sort_by === 'views') return right.view_count - left.view_count
    if (communityFilters.sort_by === 'likes') return right.like_count - left.like_count
    if (communityFilters.sort_by === 'comments') return right.comment_count - left.comment_count
    return new Date(right.created_at).getTime() - new Date(left.created_at).getTime()
  })
  communityCount.value = filtered.length
  const offset = (communityPage.value - 1) * communityPageSize
  communityPosts.value = filtered.slice(offset, offset + communityPageSize).map((item) => ({ ...item }))
  communityOverview.total_posts = previewCommunityPosts.length
  communityOverview.published_posts = previewCommunityPosts.filter((item) => item.is_published).length
  communityOverview.archived_posts = previewCommunityPosts.filter((item) => !item.is_published).length
  communityOverview.today_posts = previewCommunityPosts.filter((item) => item.created_at.startsWith('2026-08-07')).length
  communityOverview.total_reports = 2
  communityOverview.pending_reports = 1
  communityOverview.reviewing_reports = 1
  communityLoadError.value = false
  communityLoading.value = false
  communitySelectedIds.value = []
}

async function loadOperationsOverview() {
  if (devPreviewMode.value) {
    loadDevPreviewOperations()
    operationsOverviewLoading.value = false
    operationsOverviewError.value = false
    return
  }
  operationsOverviewLoading.value = true
  operationsOverviewError.value = false
  try {
    const response = await fetchQuestionAdminOperationsOverview()
    Object.keys(operationsOverview).forEach((key) => {
      operationsOverview[key] = Number(response?.[key] || 0)
    })
  } catch (error) {
    operationsOverviewError.value = true
  } finally {
    operationsOverviewLoading.value = false
  }
}

function operationsMetricValue(key) {
  if (operationsOverviewLoading.value) return '…'
  if (operationsOverviewError.value) return '—'
  return formatCount(operationsOverview[key])
}

function openMembershipPageManager() {
  membershipPageManagerVisible.value = true
}

function closeMembershipPageManager() {
  membershipPageManagerVisible.value = false
}

async function loadPortalUsers() {
  if (devPreviewMode.value) {
    loadDevPreviewOperations()
    return
  }
  portalUsersLoading.value = true
  portalUsersError.value = false
  try {
    const response = await fetchQuestionAdminPortalUsers({
      ...userFilters,
      sort_by: userSort.field,
      sort_direction: userSort.direction,
      limit: portalUserPageSize,
      offset: (portalUserPage.value - 1) * portalUserPageSize
    })
    portalUsers.value = response?.items || []
    portalUserCount.value = Number(response?.count || 0)
  } catch (error) {
    portalUsers.value = []
    portalUserCount.value = 0
    portalUsersError.value = true
  } finally {
    portalUsersLoading.value = false
  }
}

function applyPortalUserFilters() {
  portalUserPage.value = 1
  loadPortalUsers()
}

function sortPortalUsers(field) {
  if (userSort.field === field) {
    userSort.direction = userSort.direction === 'asc' ? 'desc' : 'asc'
  } else {
    userSort.field = field
    userSort.direction = field === 'exam_target' ? 'asc' : 'desc'
  }
  portalUserPage.value = 1
  loadPortalUsers()
}

function handlePortalUserSearchInput() {
  if (portalUserSearchTimer) clearTimeout(portalUserSearchTimer)
  portalUserSearchTimer = setTimeout(applyPortalUserFilters, 420)
}

function clearPortalUserSearch() {
  userFilters.search = ''
  applyPortalUserFilters()
}

function handlePortalUserExamChange(event) {
  userFilters.exam_target = portalUserExamOptions[Number(event?.detail?.value || 0)]?.value || ''
  applyPortalUserFilters()
}

function handlePortalUserMembershipChange(event) {
  userFilters.membership_status = portalUserMembershipOptions[Number(event?.detail?.value || 0)]?.value || ''
  applyPortalUserFilters()
}

function handlePortalUserAccountStatusChange(event) {
  userFilters.account_status = portalUserAccountStatusOptions[Number(event?.detail?.value || 0)]?.value || 'all'
  applyPortalUserFilters()
}

function handlePortalUserActivityChange(event) {
  userFilters.activity = portalUserActivityOptions[Number(event?.detail?.value || 0)]?.value || 'all'
  applyPortalUserFilters()
}

function changePortalUserPage(page) {
  const nextPage = Math.min(Math.max(1, Number(page) || 1), portalUserTotalPages.value)
  if (nextPage === portalUserPage.value) return
  portalUserPage.value = nextPage
  loadPortalUsers()
}

async function openPortalUserDetail(item) {
  portalUserDetailVisible.value = true
  portalUserDetailLoading.value = true
  portalUserDetail.value = null
  try {
    if (devPreviewMode.value) {
      portalUserDetail.value = buildDevPreviewUserDetail(item)
      return
    }
    portalUserDetail.value = await fetchQuestionAdminPortalUserDetail(item.id)
  } catch (error) {
    uni.showToast({ title: error?.detail || '用户详情加载失败', icon: 'none' })
    portalUserDetailVisible.value = false
  } finally {
    portalUserDetailLoading.value = false
  }
}

function closePortalUserDetail() {
  if (portalUserSaving.value) return
  portalUserDetailVisible.value = false
  portalUserDetail.value = null
}

async function openPortalUserMembership(item) {
  if (!item?.id || portalMembershipLoading.value) return
  portalMembershipVisible.value = true
  portalMembershipLoading.value = true
  portalMembershipDetail.value = null
  try {
    portalMembershipDetail.value = devPreviewMode.value
      ? buildDevPreviewUserDetail(item)
      : await fetchQuestionAdminPortalUserDetail(item.id)
  } catch (error) {
    uni.showToast({ title: error?.detail || '会员信息加载失败', icon: 'none' })
    portalMembershipVisible.value = false
  } finally {
    portalMembershipLoading.value = false
  }
}

function closePortalUserMembership() {
  if (portalMembershipSaving.value) return
  portalMembershipVisible.value = false
  portalMembershipDetail.value = null
  portalMembershipAction.value = ''
}

function nextPortalMembershipExpiry(profile, months) {
  const now = Date.now()
  const currentExpiry = new Date(profile?.membership_expires_at || '').getTime()
  const baseTime = Number.isFinite(currentExpiry) && currentExpiry > now ? currentExpiry : now
  return new Date(baseTime + months * 30 * 24 * 60 * 60 * 1000).toISOString()
}

async function syncPortalUserMembership(updated) {
  if (devPreviewMode.value) {
    devPreviewPortalUsers.value = devPreviewPortalUsers.value.map((candidate) => (
      candidate.id === updated.id ? { ...candidate, ...updated } : candidate
    ))
  }
  const leavesCurrentFilter = (
    (userFilters.membership_status === 'active' && !isPortalUserMembershipActive(updated))
    || (userFilters.membership_status === 'inactive' && isPortalUserMembershipActive(updated))
  )
  if (leavesCurrentFilter) {
    await loadPortalUsers()
  } else {
    portalUsers.value = portalUsers.value.map((candidate) => (
      candidate.id === updated.id ? { ...candidate, ...updated } : candidate
    ))
  }
  if (portalUserDetail.value?.profile?.id === updated.id) {
    portalUserDetail.value = { ...portalUserDetail.value, profile: { ...portalUserDetail.value.profile, ...updated } }
  }
  if (portalMembershipDetail.value?.profile?.id === updated.id) {
    portalMembershipDetail.value = {
      ...portalMembershipDetail.value,
      profile: { ...portalMembershipDetail.value.profile, ...updated }
    }
  }
}

async function renewPortalUserMembership(months) {
  const profile = portalMembershipDetail.value?.profile
  if (!profile?.id || portalMembershipSaving.value || ![1, 4].includes(months)) return
  const duration = months === 4 ? '一个季度（4 个月）' : '1 个月'
  const confirmed = await confirmAction(
    `为该用户续费 ${duration}？`,
    `会员有效期将顺延至 ${formatDateTime(nextPortalMembershipExpiry(profile, months))}。`,
    '确认续费'
  )
  if (!confirmed) return
  portalMembershipSaving.value = true
  portalMembershipAction.value = `renew-${months}`
  portalUserSavingId.value = profile.id
  try {
    const updated = devPreviewMode.value
      ? {
          ...profile,
          membership_status: 'active',
          membership_plan: 'admin_grant',
          membership_started_at: profile.membership_started_at || new Date().toISOString(),
          membership_expires_at: nextPortalMembershipExpiry(profile, months),
          membership_updated_at: new Date().toISOString()
        }
      : await renewQuestionAdminPortalUserMembership(profile.id, { months })
    await syncPortalUserMembership(updated)
    uni.showToast({ title: `已续费 ${duration}`, icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '会员续费失败', icon: 'none' })
  } finally {
    portalMembershipSaving.value = false
    portalMembershipAction.value = ''
    portalUserSavingId.value = ''
  }
}

async function cancelPortalUserMembership() {
  const profile = portalMembershipDetail.value?.profile
  if (!profile?.id || portalMembershipSaving.value || !isPortalUserMembershipActive(profile)) return
  const confirmed = await confirmAction(
    '取消该用户的会员？',
    '取消后该用户将立即失去会员权益，原有效期将被清空。',
    '确认取消'
  )
  if (!confirmed) return
  portalMembershipSaving.value = true
  portalMembershipAction.value = 'cancel'
  portalUserSavingId.value = profile.id
  try {
    const updated = devPreviewMode.value
      ? {
          ...profile,
          membership_status: 'inactive',
          membership_plan: null,
          membership_started_at: null,
          membership_expires_at: null,
          membership_updated_at: new Date().toISOString()
        }
      : await cancelQuestionAdminPortalUserMembership(profile.id)
    await syncPortalUserMembership(updated)
    uni.showToast({ title: '会员已取消', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '会员取消失败', icon: 'none' })
  } finally {
    portalMembershipSaving.value = false
    portalMembershipAction.value = ''
    portalUserSavingId.value = ''
  }
}

async function togglePortalUserDisabled(item) {
  if (!item?.id || portalUserSavingId.value) return
  const shouldDisable = !item?.disabled_at
  const confirmed = await confirmAction(
    shouldDisable ? '停用该账号？' : '恢复该账号？',
    shouldDisable ? '停用后该用户无法继续登录和刷题，可在后台恢复。' : '恢复后该用户可以再次正常登录和刷题。',
    shouldDisable ? '确认停用' : '确认恢复'
  )
  if (!confirmed) return
  portalUserSaving.value = true
  portalUserSavingId.value = item.id
  try {
    const updated = devPreviewMode.value
      ? { ...item, disabled_at: shouldDisable ? new Date().toISOString() : null }
      : await updateQuestionAdminPortalUserDisabled(item.id, { disabled: shouldDisable })
    if (devPreviewMode.value) {
      devPreviewPortalUsers.value = devPreviewPortalUsers.value.map((candidate) => (
        candidate.id === updated.id ? { ...candidate, ...updated } : candidate
      ))
    }
    const leavesCurrentFilter = (
      (userFilters.account_status === 'active' && updated.disabled_at)
      || (userFilters.account_status === 'disabled' && !updated.disabled_at)
    )
    if (leavesCurrentFilter) {
      await loadPortalUsers()
    } else {
      portalUsers.value = portalUsers.value.map((candidate) => candidate.id === updated.id ? { ...candidate, ...updated } : candidate)
    }
    if (portalUserDetail.value?.profile?.id === updated.id) {
      portalUserDetail.value = {
        ...portalUserDetail.value,
        profile: { ...portalUserDetail.value.profile, ...updated }
      }
    }
    uni.showToast({ title: shouldDisable ? '账号已停用' : '账号已恢复', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '账号状态更新失败', icon: 'none' })
  } finally {
    portalUserSaving.value = false
    portalUserSavingId.value = ''
  }
}

async function loadAdmissionWorkspace() {
  await loadAdmissionRuns()
  if (admissionDataset.value === 'scorelines') {
    await loadScorelineRecords()
  } else if (admissionDataset.value === 'announcements') {
    await loadAnnouncementRecords()
  } else if (admissionDataset.value === 'major-catalog') {
    await loadMajorCatalogRecords()
  }
}

async function switchAdmissionDataset(dataset) {
  if (admissionDataset.value === dataset) return
  admissionDataset.value = dataset
  admissionFile.value = null
  admissionFileName.value = ''
  admissionPreview.value = null
  admissionRuns.value = []
  selectedAdmissionRunId.value = ''
  scorelineRecordPage.value = 1
  scorelineFilters.score_year = ''
  scorelineFilters.region = ''
  scorelineFilters.keyword = ''
  scorelineRecords.value = []
  scorelineRecordCount.value = 0
  scorelineRecordsError.value = false
  announcementFilters.notice_type = ''
  announcementFilters.notice_year = ''
  announcementFilters.region = ''
  announcementFilters.school_id = ''
  announcementFilters.keyword = ''
  announcementRecords.value = []
  majorCatalogRecordPage.value = 1
  majorCatalogFilters.catalog_year = ''
  majorCatalogFilters.region = ''
  majorCatalogFilters.school_name = ''
  majorCatalogFilters.exam_code = ''
  majorCatalogFilters.keyword = ''
  majorCatalogRecords.value = []
  majorCatalogRecordCount.value = 0
  majorCatalogRecordsError.value = false
  await loadAdmissionWorkspace()
}

async function openAdmissionImport(dataset = admissionDataset.value) {
  if (dataset !== admissionDataset.value) {
    await switchAdmissionDataset(dataset)
  }
  admissionFile.value = null
  admissionFileName.value = ''
  admissionPreview.value = null
  admissionImportVisible.value = true
}

function closeAdmissionImport(force = false) {
  if ((admissionCommitting.value || admissionPreviewLoading.value) && !force) return
  admissionImportVisible.value = false
  admissionFile.value = null
  admissionFileName.value = ''
  admissionPreview.value = null
}

function ensureSelectedAdmissionRun(preferredRunId = '') {
  if (!['scorelines', 'announcements', 'major-catalog'].includes(admissionDataset.value)) {
    selectedAdmissionRunId.value = ''
    return
  }
  const preferred = preferredRunId || selectedAdmissionRunId.value
  const nextRun = admissionRuns.value.find((item) => item.id === preferred)
    || admissionRuns.value.find((item) => item.status === 'published')
    || admissionRuns.value[0]
    || null
  selectedAdmissionRunId.value = nextRun?.id || ''
}

async function loadAdmissionRuns(preferredRunId = '') {
  if (devPreviewMode.value) {
    loadDevPreviewAdmission()
    ensureSelectedAdmissionRun(preferredRunId)
    return
  }
  admissionRunsLoading.value = true
  admissionRunsError.value = false
  try {
    const response = await fetchQuestionAdminAdmissionRuns(admissionDataset.value)
    admissionRuns.value = response?.items || []
    ensureSelectedAdmissionRun(preferredRunId)
  } catch (error) {
    admissionRuns.value = []
    selectedAdmissionRunId.value = ''
    admissionRunsError.value = true
  } finally {
    admissionRunsLoading.value = false
  }
}

function buildLegacyScorelineImportRecords() {
  const rowsByKey = new Map()
  legacyHistoricalScoreLineRecords.forEach((record) => {
    Object.entries(record?.scores || {}).forEach(([scoreYear, score]) => {
      const scoreRaw = String(score?.raw || '').trim()
      if (!scoreRaw) return
      const row = {
        score_year: String(scoreYear),
        region: String(record?.region || '').trim(),
        school_name: String(record?.schoolName || record?.school || '').trim(),
        unit_name: String(record?.unitName || '').trim(),
        score_raw: scoreRaw,
        score_kind: String(score?.kind || 'note')
      }
      const key = [row.score_year, row.region, row.school_name, row.unit_name].join('|')
      const existing = rowsByKey.get(key)
      if (existing) {
        existing.score_raw = `${existing.score_raw}；${row.score_raw}`
        existing.score_kind = 'multiple'
        return
      }
      rowsByKey.set(key, row)
    })
  })
  return [...rowsByKey.values()]
}

function scorelineNumericValue(scoreRaw, scoreKind) {
  if (scoreKind !== 'score') return null
  const normalized = String(scoreRaw || '').trim().replace(/分$/, '').trim()
  return /^\d+(?:\.\d+)?$/.test(normalized) ? Number(normalized) : null
}

function ensureDevPreviewScorelineRecords() {
  if (devPreviewScorelineRecords.value.length) return
  devPreviewScorelineRecords.value = legacyScorelineImportRecords.value.map((item, index) => ({
    ...item,
    id: `preview-scoreline-${index + 1}`,
    import_run_id: 'preview-score-run-1',
    score_value: scorelineNumericValue(item.score_raw, item.score_kind),
    source_url: null,
    source_note: '',
    created_at: '2026-08-10T02:00:00Z',
    updated_at: '2026-08-10T02:00:00Z'
  }))
}

async function loadScorelineRecords() {
  if (!selectedAdmissionRunId.value) {
    scorelineRecords.value = []
    scorelineRecordCount.value = 0
    scorelineRecordsError.value = false
    scorelineFilterOptions.value = { years: [], regions: [] }
    return
  }
  if (devPreviewMode.value) {
    ensureDevPreviewScorelineRecords()
    const keyword = scorelineFilters.keyword.trim().toLowerCase()
    const region = scorelineFilters.region.trim().toLowerCase()
    const scoreYear = scorelineFilters.score_year.trim()
    const recordsForRun = devPreviewScorelineRecords.value.filter((item) => item.import_run_id === selectedAdmissionRunId.value)
    updateScorelineFilterOptions(recordsForRun)
    const filtered = recordsForRun.filter((item) => (
      (!scoreYear || item.score_year === scoreYear)
      && (!region || String(item.region || '').toLowerCase().includes(region))
      && (!keyword || `${item.school_name || ''} ${item.unit_name || ''}`.toLowerCase().includes(keyword))
    )).sort((left, right) => (
      String(right.score_year || '').localeCompare(String(left.score_year || ''))
      || String(left.region || '').localeCompare(String(right.region || ''))
      || String(left.school_name || '').localeCompare(String(right.school_name || ''))
    ))
    scorelineRecordCount.value = filtered.length
    const maxPage = Math.max(1, Math.ceil(filtered.length / scorelineRecordPageSize))
    if (scorelineRecordPage.value > maxPage) scorelineRecordPage.value = maxPage
    const start = (scorelineRecordPage.value - 1) * scorelineRecordPageSize
    scorelineRecords.value = filtered.slice(start, start + scorelineRecordPageSize).map((item) => ({ ...item }))
    scorelineRecordsError.value = false
    return
  }
  scorelineRecordsLoading.value = true
  scorelineRecordsError.value = false
  try {
    const response = await fetchQuestionAdminScorelineRecords({
      import_run_id: selectedAdmissionRunId.value,
      score_year: scorelineFilters.score_year.trim() || undefined,
      region: scorelineFilters.region.trim() || undefined,
      keyword: scorelineFilters.keyword.trim() || undefined,
      limit: scorelineRecordPageSize,
      offset: (scorelineRecordPage.value - 1) * scorelineRecordPageSize
    })
    scorelineRecords.value = response?.items || []
    scorelineRecordCount.value = Number(response?.count || 0)
    scorelineFilterOptions.value = {
      years: Array.isArray(response?.filter_years) ? response.filter_years : [],
      regions: Array.isArray(response?.filter_regions) ? response.filter_regions : []
    }
  } catch (error) {
    scorelineRecords.value = []
    scorelineRecordCount.value = 0
    scorelineRecordsError.value = true
  } finally {
    scorelineRecordsLoading.value = false
  }
}

function applyScorelineFilters() {
  scorelineRecordPage.value = 1
  loadScorelineRecords()
}

function handleScorelineFilterInput() {
  if (scorelineSearchTimer) clearTimeout(scorelineSearchTimer)
  scorelineSearchTimer = setTimeout(applyScorelineFilters, 360)
}

function handleScorelineYearFilterChange(event) {
  scorelineFilters.score_year = scorelineYearFilterOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  applyScorelineFilters()
}

function handleScorelineRegionFilterChange(event) {
  scorelineFilters.region = scorelineRegionFilterOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  applyScorelineFilters()
}

function updateScorelineFilterOptions(records) {
  scorelineFilterOptions.value = {
    years: Array.from(new Set(records.map((item) => String(item?.score_year || '').trim()).filter(Boolean))),
    regions: Array.from(new Set(records.map((item) => String(item?.region || '').trim()).filter(Boolean)))
  }
}

function clearScorelineFilters() {
  scorelineFilters.score_year = ''
  scorelineFilters.region = ''
  scorelineFilters.keyword = ''
  applyScorelineFilters()
}

function changeScorelineRecordPage(page) {
  const nextPage = Math.min(Math.max(1, Number(page) || 1), scorelineRecordTotalPages.value)
  if (nextPage === scorelineRecordPage.value) return
  scorelineRecordPage.value = nextPage
  loadScorelineRecords()
}

function ensureDevPreviewMajorCatalogRecords() {
  if (devPreviewMajorCatalogRecords.value.length) return
  devPreviewMajorCatalogRecords.value = [
    { id: 'preview-major-1', import_run_id: 'preview-major-run-1', catalog_year: '2026', region: '北京', school_name: '中国人民大学', department_name: '文学院', program_name: '中国语言文学', program_code: '050100', direction_name: '中国古代文学', tutor: '', exam_code: 'Z001', degree: '硕士', study_mode: '全日制', source_row: 1 },
    { id: 'preview-major-2', import_run_id: 'preview-major-run-1', catalog_year: '2026', region: '北京', school_name: '北京大学', department_name: '国际关系学院', program_name: '国际关系', program_code: '030207', direction_name: '国际安全与战略研究', tutor: '', exam_code: 'Z001', degree: '硕士', study_mode: '全日制', source_row: 2 },
    { id: 'preview-major-3', import_run_id: 'preview-major-run-1', catalog_year: '2026', region: '广东', school_name: '暨南大学', department_name: '新闻与传播学院', program_name: '新闻与传播', program_code: '055200', direction_name: '不区分研究方向', tutor: '', exam_code: 'Z002', degree: '硕士', study_mode: '全日制', source_row: 3 },
    { id: 'preview-major-4', import_run_id: 'preview-major-run-1', catalog_year: '2026', region: '广东', school_name: '中山大学', department_name: '管理学院', program_name: '工商管理', program_code: '125100', direction_name: '不区分研究方向', tutor: '', exam_code: 'Z002', degree: '硕士', study_mode: '非全日制', source_row: 4 },
    { id: 'preview-major-5', import_run_id: 'preview-major-run-1', catalog_year: '2026', region: '上海', school_name: '复旦大学', department_name: '数学科学学院', program_name: '应用统计', program_code: '025200', direction_name: '金融统计与风险管理', tutor: '', exam_code: 'Z002', degree: '硕士', study_mode: '全日制', source_row: 5 },
    { id: 'preview-major-6', import_run_id: 'preview-major-run-1', catalog_year: '2026', region: '浙江', school_name: '浙江大学', department_name: '计算机科学与技术学院', program_name: '电子信息', program_code: '085400', direction_name: '人工智能', tutor: '', exam_code: 'Z001', degree: '硕士', study_mode: '全日制', source_row: 6 },
    { id: 'preview-major-2025-1', import_run_id: 'preview-major-run-1', catalog_year: '2025', region: '浙江', school_name: '浙江师范大学', department_name: '地理与环境科学学院', program_name: '地理学与工程', program_code: '083000', direction_name: '不区分研究方向', tutor: '', exam_code: 'Z002', degree: '硕士', study_mode: '全日制', source_row: 1 },
    { id: 'preview-major-2025-2', import_run_id: 'preview-major-run-1', catalog_year: '2025', region: '广东', school_name: '暨南大学', department_name: '新闻与传播学院', program_name: '新闻与传播', program_code: '055200', direction_name: '不区分研究方向', tutor: '', exam_code: 'Z002', degree: '硕士', study_mode: '全日制', source_row: 2 }
  ]
}

function updateMajorCatalogFilterOptions(records) {
  majorCatalogFilterOptions.value = {
    years: Array.from(new Set(records.map((item) => String(item?.catalog_year || '').trim()).filter(Boolean))),
    regions: Array.from(new Set(records.map((item) => String(item?.region || '').trim()).filter(Boolean))),
    schools: Array.from(new Map(records.map((item) => {
      const region = String(item?.region || '').trim()
      const name = String(item?.school_name || '').trim()
      return [`${region}\u0000${name}`, { region, name }]
    })).values()).filter((item) => item.region && item.name),
    exam_codes: Array.from(new Set(records.map((item) => String(item?.exam_code || '').trim()).filter(Boolean)))
  }
}

async function loadMajorCatalogRecords() {
  if (devPreviewMode.value && !selectedAdmissionRunId.value) {
    majorCatalogRecords.value = []
    majorCatalogRecordCount.value = 0
    majorCatalogRecordsError.value = false
    majorCatalogFilterOptions.value = { years: [], regions: [], schools: [], exam_codes: [] }
    return
  }
  if (devPreviewMode.value) {
    ensureDevPreviewMajorCatalogRecords()
    const keyword = majorCatalogFilters.keyword.trim().toLowerCase()
    const recordsForRun = devPreviewMajorCatalogRecords.value.filter((item) => item.import_run_id === selectedAdmissionRunId.value)
    const activeCatalogYear = majorCatalogFilters.catalog_year || '2026'
    const recordsForCatalogYear = recordsForRun.filter((item) => item.catalog_year === activeCatalogYear)
    updateMajorCatalogFilterOptions(recordsForCatalogYear)
    majorCatalogFilterOptions.value.years = Array.from(new Set(recordsForRun.map((item) => item.catalog_year).filter(Boolean)))
    const filtered = recordsForCatalogYear.filter((item) => (
      (!majorCatalogFilters.region || item.region === majorCatalogFilters.region)
      && (!majorCatalogFilters.school_name || item.school_name === majorCatalogFilters.school_name)
      && (!majorCatalogFilters.exam_code || item.exam_code === majorCatalogFilters.exam_code)
      && (!keyword || `${item.school_name || ''} ${item.department_name || ''} ${item.program_name || ''} ${item.program_code || ''} ${item.direction_name || ''} ${item.tutor || ''}`.toLowerCase().includes(keyword))
    )).sort((left, right) => (
      String(left.region || '').localeCompare(String(right.region || ''), 'zh-CN')
      || String(left.school_name || '').localeCompare(String(right.school_name || ''), 'zh-CN')
      || Number(left.source_row || 0) - Number(right.source_row || 0)
    ))
    majorCatalogRecordCount.value = filtered.length
    const maxPage = Math.max(1, Math.ceil(filtered.length / majorCatalogRecordPageSize))
    if (majorCatalogRecordPage.value > maxPage) majorCatalogRecordPage.value = maxPage
    const start = (majorCatalogRecordPage.value - 1) * majorCatalogRecordPageSize
    majorCatalogRecords.value = filtered.slice(start, start + majorCatalogRecordPageSize).map((item) => ({ ...item }))
    majorCatalogRecordsError.value = false
    return
  }
  majorCatalogRecordsLoading.value = true
  majorCatalogRecordsError.value = false
  try {
    const response = await fetchQuestionAdminMajorCatalogRecords({
      catalog_year: majorCatalogFilters.catalog_year || undefined,
      region: majorCatalogFilters.region || undefined,
      school_name: majorCatalogFilters.school_name || undefined,
      exam_code: majorCatalogFilters.exam_code || undefined,
      keyword: majorCatalogFilters.keyword.trim() || undefined,
      limit: majorCatalogRecordPageSize,
      offset: (majorCatalogRecordPage.value - 1) * majorCatalogRecordPageSize
    })
    majorCatalogRecords.value = response?.items || []
    majorCatalogRecordCount.value = Number(response?.count || 0)
    majorCatalogFilterOptions.value = {
      years: Array.isArray(response?.filter_years) ? response.filter_years : [],
      regions: Array.isArray(response?.filter_regions) ? response.filter_regions : [],
      schools: Array.isArray(response?.filter_schools) ? response.filter_schools : [],
      exam_codes: Array.isArray(response?.filter_exam_codes) ? response.filter_exam_codes : []
    }
  } catch (error) {
    majorCatalogRecords.value = []
    majorCatalogRecordCount.value = 0
    majorCatalogRecordsError.value = true
  } finally {
    majorCatalogRecordsLoading.value = false
  }
}

function applyMajorCatalogFilters() {
  majorCatalogRecordPage.value = 1
  loadMajorCatalogRecords()
}

function handleMajorCatalogYearFilterChange(event) {
  majorCatalogFilters.catalog_year = majorCatalogYearFilterOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  majorCatalogFilters.region = ''
  majorCatalogFilters.school_name = ''
  applyMajorCatalogFilters()
}

function handleMajorCatalogRegionFilterChange(event) {
  majorCatalogFilters.region = majorCatalogRegionFilterOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  majorCatalogFilters.school_name = ''
  applyMajorCatalogFilters()
}

function handleMajorCatalogSchoolFilterChange(event) {
  majorCatalogFilters.school_name = majorCatalogSchoolFilterOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  applyMajorCatalogFilters()
}

function handleMajorCatalogExamCodeFilterChange(event) {
  majorCatalogFilters.exam_code = majorCatalogExamCodeFilterOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  applyMajorCatalogFilters()
}

function clearMajorCatalogFilters() {
  majorCatalogFilters.catalog_year = ''
  majorCatalogFilters.region = ''
  majorCatalogFilters.school_name = ''
  majorCatalogFilters.exam_code = ''
  majorCatalogFilters.keyword = ''
  applyMajorCatalogFilters()
}

function changeMajorCatalogRecordPage(page) {
  const nextPage = Math.min(Math.max(1, Number(page) || 1), majorCatalogRecordTotalPages.value)
  if (nextPage === majorCatalogRecordPage.value) return
  majorCatalogRecordPage.value = nextPage
  loadMajorCatalogRecords()
}

function openMajorCatalogRecordEditor(item) {
  if (!item?.id || majorCatalogRecordSaving.value) return
  majorCatalogRecordEditingId.value = item.id
  majorCatalogRecordYear.value = String(item.catalog_year || selectedAdmissionRun.value?.statistics?.catalog_year || '')
  majorCatalogRecordForm.region = String(item.region || '')
  majorCatalogRecordForm.school_name = String(item.school_name || '')
  majorCatalogRecordForm.department_name = String(item.department_name || '未区分院系所')
  majorCatalogRecordForm.program_name = String(item.program_name || '')
  majorCatalogRecordForm.program_code = String(item.program_code || '')
  majorCatalogRecordForm.direction_name = String(item.direction_name || '不区分研究方向')
  majorCatalogRecordForm.tutor = String(item.tutor || '')
  majorCatalogRecordForm.exam_code = String(item.exam_code || 'Z001')
  majorCatalogRecordForm.degree = String(item.degree || '')
  majorCatalogRecordForm.study_mode = String(item.study_mode || '')
  majorCatalogRecordEditorVisible.value = true
}

function closeMajorCatalogRecordEditor(force = false) {
  if (majorCatalogRecordSaving.value && !force) return
  majorCatalogRecordEditorVisible.value = false
  majorCatalogRecordEditingId.value = ''
}

function handleMajorCatalogExamCodeChange(event) {
  majorCatalogRecordForm.exam_code = majorCatalogExamCodeEditOptions[Number(event?.detail?.value || 0)]?.value || 'Z001'
}

async function saveMajorCatalogRecord() {
  if (!majorCatalogRecordEditingId.value || majorCatalogRecordSaving.value) return
  const payload = {
    region: majorCatalogRecordForm.region.trim(),
    school_name: majorCatalogRecordForm.school_name.trim(),
    department_name: majorCatalogRecordForm.department_name.trim(),
    program_name: majorCatalogRecordForm.program_name.trim(),
    program_code: majorCatalogRecordForm.program_code.trim(),
    direction_name: majorCatalogRecordForm.direction_name.trim(),
    tutor: majorCatalogRecordForm.tutor.trim(),
    exam_code: majorCatalogRecordForm.exam_code,
    degree: majorCatalogRecordForm.degree.trim(),
    study_mode: majorCatalogRecordForm.study_mode.trim()
  }
  if (!payload.region || !payload.school_name || !payload.department_name || !payload.program_name || !payload.direction_name) {
    uni.showToast({ title: '请完整填写地区、院校、院系、专业和研究方向', icon: 'none' })
    return
  }
  const syncsStudentView = true
  const confirmed = await confirmAction(
    '保存专业目录修改？',
    syncsStudentView ? '当前目录正在用户端展示，保存后会重新同步这一年度目录。' : '修改会保存在当前导入批次中。',
    '保存修改'
  )
  if (!confirmed) return
  majorCatalogRecordSaving.value = true
  try {
    if (devPreviewMode.value) {
      devPreviewMajorCatalogRecords.value = devPreviewMajorCatalogRecords.value.map((record) => (
        record.id === majorCatalogRecordEditingId.value ? { ...record, ...payload } : record
      ))
    } else {
      await updateQuestionAdminMajorCatalogRecord(majorCatalogRecordEditingId.value, payload)
    }
    closeMajorCatalogRecordEditor(true)
    await loadMajorCatalogRecords()
    uni.showToast({ title: syncsStudentView ? '专业目录已保存并同步' : '专业目录已保存', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '专业目录保存失败', icon: 'none' })
  } finally {
    majorCatalogRecordSaving.value = false
  }
}

function scorelineKindText(kind) {
  return scorelineKindOptions.find((item) => item.value === kind)?.label || '文字说明'
}

async function bootstrapExistingScorelineRecords() {
  if (scorelineRecordBootstrapLoading.value || !legacyScorelineImportRecords.value.length) return
  const confirmed = await confirmAction(
    '接入现有分数线？',
    `将 ${formatCount(legacyScorelineImportRecords.value.length)} 条现有分数信息接入后台管理，学生端现有内容保持不变。`,
    '接入数据'
  )
  if (!confirmed) return
  scorelineRecordBootstrapLoading.value = true
  try {
    const response = await bootstrapQuestionAdminScorelines({ records: legacyScorelineImportRecords.value })
    await loadAdmissionRuns(response?.run?.id)
    await loadScorelineRecords()
    uni.showToast({ title: response?.created === false ? '现有分数线已接入' : '已接入分数线数据', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '现有数据接入失败', icon: 'none' })
  } finally {
    scorelineRecordBootstrapLoading.value = false
  }
}

async function bootstrapExistingAdmissionSnapshot(dataset) {
  if (!['announcements', 'major-catalog'].includes(dataset) || admissionSnapshotBootstrapLoading.value) return
  const isAnnouncement = dataset === 'announcements'
  const confirmed = await confirmAction(
    isAnnouncement ? '接入现有院校公告？' : '接入现有专业目录？',
    isAnnouncement
      ? '将当前学生端院校公告接入后台管理，当前展示不受影响。'
      : '将当前学生端 2026 专业目录接入后台管理，当前展示不受影响。',
    '接入数据'
  )
  if (!confirmed) return
  admissionSnapshotBootstrapLoading.value = true
  try {
    const response = await bootstrapQuestionAdminAdmissionSnapshot(dataset)
    if (admissionDataset.value === dataset) {
      await loadAdmissionRuns(response?.run?.id)
      if (dataset === 'announcements') await loadAnnouncementRecords()
      if (dataset === 'major-catalog') await loadMajorCatalogRecords()
    }
    await loadOperationsOverview()
    uni.showToast({ title: response?.created === false ? '现有数据已接入' : isAnnouncement ? '已接入院校公告' : '已接入专业目录', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || (isAnnouncement ? '院校公告接入失败' : '专业目录接入失败'), icon: 'none' })
  } finally {
    admissionSnapshotBootstrapLoading.value = false
  }
}

function openScorelineRecordEditor(item) {
  if (!item?.id) return
  scorelineRecordEditingId.value = item.id
  scorelineRecordForm.score_year = String(item.score_year || '')
  scorelineRecordForm.region = String(item.region || '')
  scorelineRecordForm.school_name = String(item.school_name || '')
  scorelineRecordForm.unit_name = String(item.unit_name || '')
  scorelineRecordForm.score_raw = String(item.score_raw || '')
  scorelineRecordForm.score_kind = String(item.score_kind || 'note')
  scorelineRecordForm.source_url = String(item.source_url || '')
  scorelineRecordForm.source_note = String(item.source_note || '')
  scorelineRecordEditorVisible.value = true
}

function closeScorelineRecordEditor(force = false) {
  if (scorelineRecordSaving.value && !force) return
  scorelineRecordEditorVisible.value = false
  scorelineRecordEditingId.value = ''
}

function handleScorelineKindChange(event) {
  scorelineRecordForm.score_kind = scorelineKindOptions[Number(event?.detail?.value || 0)]?.value || 'note'
}

async function saveScorelineRecord() {
  if (!scorelineRecordEditingId.value || scorelineRecordSaving.value) return
  const payload = {
    score_year: scorelineRecordForm.score_year.trim(),
    region: scorelineRecordForm.region.trim(),
    school_name: scorelineRecordForm.school_name.trim(),
    unit_name: scorelineRecordForm.unit_name.trim(),
    score_raw: scorelineRecordForm.score_raw.trim(),
    score_kind: scorelineRecordForm.score_kind,
    source_url: scorelineRecordForm.source_url.trim(),
    source_note: scorelineRecordForm.source_note.trim()
  }
  if (!/^20\d{2}$/.test(payload.score_year) || !payload.region || !payload.school_name || !payload.score_raw) {
    uni.showToast({ title: '请完整填写年份、地区、院校和分数线', icon: 'none' })
    return
  }
  const syncsStudentView = selectedAdmissionRun.value?.status === 'published'
  const confirmed = await confirmAction(
    '保存分数线修改？',
    syncsStudentView ? '当前数据已同步学生端，保存后将立即生效。' : '修改会保存在当前后台数据中。',
    '保存修改'
  )
  if (!confirmed) return
  scorelineRecordSaving.value = true
  try {
    if (devPreviewMode.value) {
      const updatedAt = new Date().toISOString()
      devPreviewScorelineRecords.value = devPreviewScorelineRecords.value.map((item) => (
        item.id === scorelineRecordEditingId.value
          ? { ...item, ...payload, score_value: scorelineNumericValue(payload.score_raw, payload.score_kind), updated_at: updatedAt }
          : item
      ))
    } else {
      await updateQuestionAdminScorelineRecord(scorelineRecordEditingId.value, payload)
    }
    closeScorelineRecordEditor(true)
    await loadScorelineRecords()
    uni.showToast({ title: '分数线已保存', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '分数线保存失败', icon: 'none' })
  } finally {
    scorelineRecordSaving.value = false
  }
}

async function loadAnnouncementRecords() {
  if (devPreviewMode.value && !selectedAdmissionRunId.value) {
    announcementRecords.value = []
    announcementRecordCount.value = 0
    announcementRecordsError.value = false
    announcementFilterOptions.value = { years: [], regions: [], schools: [] }
    return
  }
  if (devPreviewMode.value) {
    const publishedRecords = devPreviewAnnouncementRecords.value.filter((item) => item.status === 'published')
    const filterRecords = publishedRecords.filter((item) => (
      (!announcementFilters.notice_year || item.notice_year === announcementFilters.notice_year)
      && (!announcementFilters.notice_type || item.notice_type === announcementFilters.notice_type)
    ))
    announcementFilterOptions.value = {
      years: Array.from(new Set(publishedRecords.map((item) => String(item.notice_year || '')).filter(Boolean))),
      regions: Array.from(new Set(filterRecords.map((item) => String(item.region || '')).filter(Boolean))),
      schools: Array.from(new Map(filterRecords.map((item) => [
        String(item.school_id || ''),
        { id: String(item.school_id || ''), region: String(item.region || ''), name: String(item.school_name || '') }
      ])).values()).filter((item) => item.id && item.region && item.name)
    }
    const keyword = announcementFilters.keyword.trim().toLowerCase()
    announcementRecords.value = filterRecords.filter((item) => (
      (!announcementFilters.region || item.region === announcementFilters.region)
      && (!announcementFilters.school_id || item.school_id === announcementFilters.school_id)
      && (!keyword || `${item.school_name || ''} ${item.unit_name || ''} ${item.title || ''} ${item.summary || ''} ${item.content_text || ''}`.toLowerCase().includes(keyword))
    )).map((item) => ({ ...item })).sort((left, right) => (
      Number(left.sort_order || 0) - Number(right.sort_order || 0)
      || String(right.notice_date || '').localeCompare(String(left.notice_date || ''))
    ))
    announcementRecordCount.value = announcementRecords.value.length
    announcementRecordsError.value = false
    return
  }
  announcementRecordsLoading.value = true
  announcementRecordsError.value = false
  try {
    const response = await fetchQuestionAdminAnnouncementRecords({
      notice_type: announcementFilters.notice_type || undefined,
      notice_year: announcementFilters.notice_year || undefined,
      region: announcementFilters.region || undefined,
      school_id: announcementFilters.school_id || undefined,
      keyword: announcementFilters.keyword.trim() || undefined,
      limit: 100
    })
    announcementRecords.value = response?.items || []
    announcementRecordCount.value = Number(response?.count || 0)
    announcementFilterOptions.value = {
      years: Array.isArray(response?.filter_years) ? response.filter_years : [],
      regions: Array.isArray(response?.filter_regions) ? response.filter_regions : [],
      schools: Array.isArray(response?.filter_schools) ? response.filter_schools : []
    }
  } catch (error) {
    announcementRecords.value = []
    announcementRecordCount.value = 0
    announcementRecordsError.value = true
  } finally {
    announcementRecordsLoading.value = false
  }
}

function applyAnnouncementFilters() {
  loadAnnouncementRecords()
}

function handleAnnouncementNoticeTypeFilterChange(event) {
  announcementFilters.notice_type = announcementNoticeTypeFilterOptions[Number(event?.detail?.value || 0)]?.value || ''
  announcementFilters.school_id = ''
  applyAnnouncementFilters()
}

function handleAnnouncementYearFilterChange(event) {
  announcementFilters.notice_year = announcementYearFilterOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  announcementFilters.school_id = ''
  applyAnnouncementFilters()
}

function handleAnnouncementRegionFilterChange(event) {
  announcementFilters.region = announcementRegionFilterOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  announcementFilters.school_id = ''
  applyAnnouncementFilters()
}

function handleAnnouncementSchoolFilterChange(event) {
  announcementFilters.school_id = announcementSchoolFilterOptions.value[Number(event?.detail?.value || 0)]?.value || ''
  applyAnnouncementFilters()
}

function clearAnnouncementFilters() {
  announcementFilters.notice_type = ''
  announcementFilters.notice_year = ''
  announcementFilters.region = ''
  announcementFilters.school_id = ''
  announcementFilters.keyword = ''
  applyAnnouncementFilters()
}

function openAdmissionFilePicker() {
  const fileInput = admissionFileInputRef.value?.$el || admissionFileInputRef.value
  fileInput?.click?.()
}

function handleAdmissionFileChange(event) {
  const selected = event?.target?.files?.[0] || event?.detail?.files?.[0] || null
  admissionFile.value = selected
  admissionFileName.value = selected?.name || ''
  admissionPreview.value = null
}

async function previewAdmissionImport() {
  if (!admissionFile.value) return
  admissionPreviewLoading.value = true
  try {
    admissionPreview.value = await previewQuestionAdminAdmissionImport(admissionDataset.value, {
      file: admissionFile.value,
      fileName: admissionFileName.value
    })
    const invalidCount = Number(admissionPreview.value?.invalid_rows || 0)
    uni.showToast({ title: invalidCount ? `发现 ${invalidCount} 行需修正` : '字段检查通过', icon: invalidCount ? 'none' : 'success' })
  } catch (error) {
    admissionPreview.value = null
    uni.showToast({ title: error?.detail || 'Excel 检查失败', icon: 'none' })
  } finally {
    admissionPreviewLoading.value = false
  }
}

async function commitAdmissionImport() {
  if (!canCommitAdmissionImport.value || !admissionFile.value) return
  const confirmed = await confirmAction('确认导入数据？', '数据会先保存到后台，导入后可在当前列表继续维护。', '确认导入')
  if (!confirmed) return
  admissionCommitting.value = true
  try {
    const response = await commitQuestionAdminAdmissionImport(admissionDataset.value, {
      file: admissionFile.value,
      fileName: admissionFileName.value
    })
    admissionPreview.value = null
    admissionFile.value = null
    admissionFileName.value = ''
    await loadAdmissionRuns(response?.run?.id)
    if (admissionDataset.value === 'scorelines') await loadScorelineRecords()
    if (admissionDataset.value === 'major-catalog') await loadMajorCatalogRecords()
    closeAdmissionImport(true)
    uni.showToast({ title: response?.created === false ? '该文件已存在于导入记录' : '数据已导入', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '导入提交失败', icon: 'none' })
  } finally {
    admissionCommitting.value = false
  }
}

async function setAnnouncementRecordStatus(item, nextStatus) {
  if (!item?.id || announcementUpdatingId.value) return
  if (!canManageSelectedAnnouncementRecords.value) {
    uni.showToast({ title: '请先发布该公告版本', icon: 'none' })
    return
  }
  const confirmed = await confirmAction(
    nextStatus === 'published' ? '发布这条公告？' : '归档这条公告？',
    nextStatus === 'published' ? '发布后学生可在院校公告页面查看该内容。' : '归档后学生端立即停止展示，后台记录仍会保留。',
    nextStatus === 'published' ? '确认发布' : '确认归档'
  )
  if (!confirmed) return
  announcementUpdatingId.value = item.id
  try {
    const updated = devPreviewMode.value
      ? { ...item, status: nextStatus }
      : await updateQuestionAdminAnnouncementRecord(item.id, { status: nextStatus })
    if (devPreviewMode.value) {
      devPreviewAnnouncementRecords.value = devPreviewAnnouncementRecords.value.map((record) => (
        record.id === updated.id ? { ...record, ...updated } : record
      ))
    }
    await loadAnnouncementRecords()
    uni.showToast({ title: nextStatus === 'published' ? '公告已发布' : '公告已归档', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '公告状态更新失败', icon: 'none' })
  } finally {
    announcementUpdatingId.value = ''
  }
}

function openAnnouncementRecordEditor(item) {
  if (!item?.id || announcementRecordSaving.value) return
  if (!canManageSelectedAnnouncementRecords.value) {
    uni.showToast({ title: '请先发布该公告版本', icon: 'none' })
    return
  }
  announcementRecordEditingId.value = item.id
  announcementRecordForm.notice_year = String(item.notice_year || '')
  announcementRecordForm.region = String(item.region || '')
  announcementRecordForm.school_name = String(item.school_name || '')
  announcementRecordForm.unit_name = String(item.unit_name || '')
  announcementRecordForm.notice_type = String(item.notice_type || 'brochure')
  announcementRecordForm.title = String(item.title || '')
  announcementRecordForm.summary = String(item.summary || '')
  announcementRecordForm.notice_date = String(item.notice_date || '')
  announcementRecordForm.source_url = String(item.source_url || '')
  announcementRecordForm.content_text = String(item.content_text || '')
  announcementRecordEditorVisible.value = true
}

function closeAnnouncementRecordEditor(force = false) {
  if (announcementRecordSaving.value && !force) return
  announcementRecordEditorVisible.value = false
  announcementRecordEditingId.value = ''
}

function handleAnnouncementRecordNoticeTypeChange(event) {
  announcementRecordForm.notice_type = announcementRecordNoticeTypeOptions[Number(event?.detail?.value || 0)]?.value || 'brochure'
}

async function saveAnnouncementRecord() {
  if (!announcementRecordEditingId.value || announcementRecordSaving.value) return
  const payload = {
    notice_year: announcementRecordForm.notice_year.trim(),
    region: announcementRecordForm.region.trim(),
    school_name: announcementRecordForm.school_name.trim(),
    unit_name: announcementRecordForm.unit_name.trim(),
    notice_type: announcementRecordForm.notice_type,
    title: announcementRecordForm.title.trim(),
    summary: announcementRecordForm.summary.trim(),
    notice_date: announcementRecordForm.notice_date.trim() || null,
    source_url: announcementRecordForm.source_url.trim(),
    content_text: announcementRecordForm.content_text.trim()
  }
  if (!/^20\d{2}$/.test(payload.notice_year) || !payload.region || !payload.school_name || !payload.title) {
    uni.showToast({ title: '请完整填写年份、地区、院校和标题', icon: 'none' })
    return
  }
  const syncsStudentView = selectedAdmissionRun.value?.status === 'published'
  const confirmed = await confirmAction(
    '保存公告修改？',
    syncsStudentView ? '当前公告正在用户端展示，保存后将立即生效。' : '修改会保存在当前后台数据中。',
    '保存修改'
  )
  if (!confirmed) return
  announcementRecordSaving.value = true
  try {
    if (devPreviewMode.value) {
      const updatedAt = new Date().toISOString()
      devPreviewAnnouncementRecords.value = devPreviewAnnouncementRecords.value.map((record) => (
        record.id === announcementRecordEditingId.value ? { ...record, ...payload, updated_at: updatedAt } : record
      ))
    } else {
      await updateQuestionAdminAnnouncementRecord(announcementRecordEditingId.value, payload)
    }
    closeAnnouncementRecordEditor(true)
    await loadAnnouncementRecords()
    uni.showToast({ title: '公告已保存', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '公告保存失败', icon: 'none' })
  } finally {
    announcementRecordSaving.value = false
  }
}

function downloadAdmissionTemplate() {
  const fileName = admissionDataset.value === 'scorelines'
    ? 'historical-scoreline-import-template.xlsx'
    : admissionDataset.value === 'announcements'
      ? 'school-announcement-import-template.xlsx'
      : 'major-catalog-import-template.xlsx'
  const url = `/static/admin-templates/${fileName}`
  // #ifdef H5
  window.open(url, '_blank')
  // #endif
  // #ifdef APP-PLUS
  plus.runtime.openURL(url)
  // #endif
}

async function loadHomeContent() {
  if (devPreviewMode.value) {
    loadDevPreviewHomeContent()
    return
  }
  homeContentLoading.value = true
  homeContentError.value = false
  try {
    const response = await fetchQuestionAdminHomeContent()
    homeContentItems.value = response?.items || []
  } catch (error) {
    homeContentItems.value = []
    homeContentError.value = true
  } finally {
    homeContentLoading.value = false
  }
}

function resetHomeContentForm(slot = 'focus') {
  homeContentEditingId.value = ''
  Object.assign(homeContentForm, {
    slot,
    title: '',
    subtitle: '',
    badge: '',
    source: '',
    display_date: '',
    cover_label: '',
    tone: 'is-blue',
    target_url: '',
    route_key: '',
    sort_order: 0,
    status: 'draft',
    starts_at: '',
    ends_at: ''
  })
}

function openHomeContentEditor(slot, item = null) {
  if (!item && homeContentSlotAtCapacity(slot)) {
    uni.showToast({ title: `${homeContentSlotLabel(slot)}最多发布 ${homeContentSlotLimit(slot)} 个，请先下架现有内容`, icon: 'none' })
    return
  }
  if (item) {
    homeContentEditingId.value = item.id
    Object.assign(homeContentForm, {
      slot: item.slot || slot,
      title: item.title || '',
      subtitle: item.subtitle || '',
      badge: item.badge || '',
      source: item.source || '',
      display_date: item.display_date || '',
      cover_label: item.cover_label || '',
      tone: item.tone || 'is-blue',
      target_url: item.target_url || '',
      route_key: item.route_key || '',
      sort_order: Number(item.sort_order || 0),
      status: item.status || 'draft',
      starts_at: toHomeDatetimeLocal(item.starts_at),
      ends_at: toHomeDatetimeLocal(item.ends_at)
    })
  } else {
    resetHomeContentForm(slot)
  }
  homeContentEditorVisible.value = true
}

function closeHomeContentEditor(force = false) {
  if (homeContentSaving.value && !force) return
  homeContentEditorVisible.value = false
  resetHomeContentForm()
}

function handleHomeToneChange(event) {
  homeContentForm.tone = homeToneOptions[Number(event?.detail?.value || 0)]?.value || 'is-blue'
}

function handleHomeTargetChange(event) {
  homeContentForm.route_key = homeTargetOptions[Number(event?.detail?.value || 0)]?.value || ''
  if (homeContentForm.route_key) homeContentForm.target_url = ''
}

function toHomeDatetimeLocal(value) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  const pad = (part) => String(part).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function homeDatetimeToIso(value) {
  if (!value) return null
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? null : parsed.toISOString()
}

async function saveHomeContent(requestedStatus = '') {
  if (!homeContentForm.title.trim()) return
  const explicitStatus = typeof requestedStatus === 'string' ? requestedStatus : ''
  const desiredStatus = explicitStatus || homeContentForm.status
  const isPublishingInactiveContent = desiredStatus === 'published' && homeContentForm.status !== 'published'
  const startsAt = homeDatetimeToIso(homeContentForm.starts_at)
  const endsAt = homeDatetimeToIso(homeContentForm.ends_at)
  if ((homeContentForm.starts_at && !startsAt) || (homeContentForm.ends_at && !endsAt)) {
    uni.showToast({ title: '请检查生效与下线时间', icon: 'none' })
    return
  }
  if (startsAt && endsAt && new Date(startsAt).getTime() >= new Date(endsAt).getTime()) {
    uni.showToast({ title: '下线时间必须晚于生效时间', icon: 'none' })
    return
  }
  if (isPublishingInactiveContent && homeContentSlotAtCapacity(homeContentForm.slot)) {
    uni.showToast({ title: `${homeContentSlotLabel(homeContentForm.slot)}已满 ${homeContentSlotLimit(homeContentForm.slot)}/${homeContentSlotLimit(homeContentForm.slot)}，请先下架现有内容`, icon: 'none' })
    return
  }
  if (isPublishingInactiveContent && endsAt && new Date(endsAt).getTime() < Date.now()) {
    uni.showToast({ title: '下线时间已过期，请调整后再上架', icon: 'none' })
    return
  }
  if (desiredStatus === 'published') {
    const isRepublishing = homeContentForm.status === 'archived'
    const confirmed = await confirmAction(
      isPublishingInactiveContent ? (isRepublishing ? '保存并重新上架？' : '保存并上架？') : '保存已发布内容？',
      isPublishingInactiveContent
        ? '保存后会恢复为已发布状态，并继续遵循当前排序、生效时间和下线时间。'
        : '标题、排序、点击去向和展示时间的修改会立即同步到学生端。',
      isPublishingInactiveContent ? (isRepublishing ? '重新上架' : '上架') : '确认保存'
    )
    if (!confirmed) return
  }
  const previousStatus = homeContentForm.status
  homeContentSaving.value = true
  try {
    const payload = {
      ...homeContentForm,
      status: desiredStatus,
      display_date: homeContentForm.slot === 'news' ? (homeContentForm.display_date || null) : null,
      target_url: homeContentForm.route_key ? '' : homeContentForm.target_url,
      starts_at: startsAt,
      ends_at: endsAt
    }
    let updated
    if (devPreviewMode.value) {
      updated = { ...payload, id: homeContentEditingId.value || `preview-home-${Date.now()}` }
      devPreviewHomeContentItems.value = homeContentEditingId.value
        ? devPreviewHomeContentItems.value.map((item) => item.id === updated.id ? { ...item, ...updated } : item)
        : [...devPreviewHomeContentItems.value, updated]
    } else {
      updated = homeContentEditingId.value
        ? await updateQuestionAdminHomeContent(homeContentEditingId.value, payload)
        : await createQuestionAdminHomeContent(payload)
    }
    if (homeContentEditingId.value) {
      homeContentItems.value = homeContentItems.value.map((item) => item.id === updated.id ? { ...item, ...updated } : item)
    } else {
      homeContentItems.value = [...homeContentItems.value, updated]
    }
    closeHomeContentEditor(true)
    await loadOperationsOverview()
    uni.showToast({
      title: isPublishingInactiveContent
        ? (previousStatus === 'archived' ? '首页内容已重新上架' : '首页内容已上架')
        : '首页内容已保存',
      icon: 'success'
    })
  } catch (error) {
    uni.showToast({ title: error?.detail || '首页内容保存失败', icon: 'none' })
  } finally {
    homeContentSaving.value = false
  }
}

function homeContentPayloadFromItem(item, status = item.status) {
  return {
    slot: item.slot,
    title: item.title || '',
    subtitle: item.subtitle || '',
    badge: item.badge || '',
    source: item.source || '',
    display_date: item.display_date || null,
    cover_label: item.cover_label || '',
    tone: item.tone || 'is-blue',
    target_url: item.target_url || '',
    route_key: item.route_key || '',
    sort_order: Number(item.sort_order || 0),
    status,
    starts_at: item.starts_at || null,
    ends_at: item.ends_at || null,
    announcement_record_id: item.announcement_record_id || null
  }
}

async function updateHomeContentStatus(item, nextStatus) {
  if (!item?.id || homeContentStatusSavingId.value) return
  const isPublishing = nextStatus === 'published'
  if ((isPublishing && item.status === 'published') || (!isPublishing && item.status !== 'published')) return
  if (isPublishing && homeContentSlotAtCapacity(item.slot)) {
    uni.showToast({ title: `${homeContentSlotLabel(item.slot)}已满 ${homeContentSlotLimit(item.slot)}/${homeContentSlotLimit(item.slot)}，请先下架现有内容`, icon: 'none' })
    return
  }
  if (isPublishing && homeContentTimeState(item) === 'expired') {
    const editNow = await confirmAction(
      '下线时间已过期',
      '请先编辑并调整下线时间，再重新上架，避免状态已发布但学生端仍不展示。',
      '去编辑'
    )
    if (editNow) openHomeContentEditor(item.slot, item)
    return
  }
  const isRepublishing = isPublishing && item.status === 'archived'
  const confirmed = await confirmAction(
    isPublishing ? (isRepublishing ? '重新上架首页内容？' : '上架首页内容？') : '下架首页内容？',
    isPublishing
      ? '上架后会恢复为已发布状态，并继续遵循当前排序、生效时间和下线时间。'
      : '下架后学生端将不再展示该内容，后台记录会保留。',
    isPublishing ? (isRepublishing ? '重新上架' : '上架') : '下架'
  )
  if (!confirmed) return
  homeContentStatusSavingId.value = item.id
  try {
    const updated = devPreviewMode.value
      ? { ...item, status: nextStatus }
      : await updateQuestionAdminHomeContent(item.id, homeContentPayloadFromItem(item, nextStatus))
    if (devPreviewMode.value) {
      devPreviewHomeContentItems.value = devPreviewHomeContentItems.value.map((candidate) => (
        candidate.id === updated.id ? { ...candidate, ...updated } : candidate
      ))
    }
    homeContentItems.value = homeContentItems.value.map((candidate) => candidate.id === updated.id ? { ...candidate, ...updated } : candidate)
    await loadOperationsOverview()
    uni.showToast({ title: isPublishing ? (isRepublishing ? '首页内容已重新上架' : '首页内容已上架') : '首页内容已下架', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '首页状态更新失败', icon: 'none' })
  } finally {
    homeContentStatusSavingId.value = ''
  }
}

function archiveHomeContent(item) {
  return updateHomeContentStatus(item, 'archived')
}

function publishHomeContent(item) {
  return updateHomeContentStatus(item, 'published')
}

function sortHomeContentItems(items) {
  return [...items].sort((left, right) => (
    Number(left.sort_order || 0) - Number(right.sort_order || 0)
    || String(right.created_at || '').localeCompare(String(left.created_at || ''))
  ))
}

function homeContentTimeState(item, now = homeContentClock.value) {
  const startsAt = item?.starts_at ? new Date(item.starts_at).getTime() : null
  const endsAt = item?.ends_at ? new Date(item.ends_at).getTime() : null
  if (Number.isFinite(startsAt) && startsAt > now) return 'scheduled'
  if (Number.isFinite(endsAt) && endsAt < now) return 'expired'
  return 'current'
}

function isHomeContentVisibleNow(item) {
  return item?.status === 'published' && homeContentTimeState(item) === 'current'
}

function homeContentStatusText(item) {
  if (item?.status === 'archived') return '已下架'
  if (item?.status !== 'published') return '草稿'
  const timing = homeContentTimeState(item)
  if (timing === 'scheduled') return '待生效'
  if (timing === 'expired') return '已到期'
  return '展示中'
}

function homeContentStatusClass(item) {
  const text = homeContentStatusText(item)
  if (text === '展示中') return 'published'
  if (text === '已下架' || text === '已到期') return 'archived'
  return 'pending'
}

function homeContentListMeta(item, index) {
  const limit = item.slot === 'focus' ? 3 : 2
  const currentList = item.slot === 'focus' ? homeVisibleFocusItems.value : homeVisibleNewsItems.value
  const visibleIndex = currentList.findIndex((candidate) => candidate.id === item.id)
  if (visibleIndex >= 0) return `用户端第 ${visibleIndex + 1} 位 · 排序 ${Number(item.sort_order || 0)}`
  if (isHomeContentVisibleNow(item) && index >= limit) return `已发布，但排序在首屏 ${limit} 条之后`
  return `${homeContentStatusText(item)} · 排序 ${Number(item.sort_order || 0)}`
}

function admissionRunStatusText(value) {
  return { draft: '待发布', published: '已发布', archived: '已归档', failed: '失败' }[String(value || '')] || '待发布'
}

function loadDevPreviewOperations() {
  operationsOverviewLoading.value = false
  operationsOverviewError.value = false
  Object.assign(operationsOverview, {
    total_users: 3218,
    new_today: 18,
    new_week: 146,
    active_week: 892,
    active_members: 326,
    published_home_items: 5,
    published_announcements: 360,
    scoreline_draft_runs: 1,
    announcement_draft_runs: 2,
    major_catalog_draft_runs: 1,
    recent_import_failures: 0
  })
  if (!devPreviewPortalUsers.value.length) {
    devPreviewPortalUsers.value = [
      { id: 'preview-user-001', nickname: '陈同学', email: 'chen@example.com', exam_target: 'Z001', answer_count: 487, correct_count: 328, wrong_count: 159, accuracy: 67.4, last_answer_at: '2026-08-18T15:20:00Z', created_at: '2026-06-12T09:00:00Z', membership_status: 'active', membership_expires_at: '2027-06-12T09:00:00Z', disabled_at: null },
      { id: 'preview-user-002', nickname: '林同学', email: 'lin@example.com', exam_target: 'Z002', answer_count: 166, correct_count: 104, wrong_count: 62, accuracy: 62.7, last_answer_at: '2026-08-17T10:15:00Z', created_at: '2026-07-01T08:00:00Z', membership_status: 'active', membership_expires_at: '2026-07-31T08:00:00Z', disabled_at: null },
      { id: 'preview-user-003', nickname: '周同学', phone: '138****2201', exam_target: 'Z001', answer_count: 42, correct_count: 20, wrong_count: 22, accuracy: 47.6, last_answer_at: '2026-07-02T06:20:00Z', created_at: '2026-07-23T02:00:00Z', membership_status: 'inactive', disabled_at: '2026-08-12T04:30:00Z' }
    ]
  }
  const previewUsers = devPreviewPortalUsers.value
  const search = userFilters.search.trim().toLowerCase()
  const now = Date.now()
  let filteredUsers = previewUsers.filter((item) => {
    const searchable = `${item.nickname || ''} ${item.email || ''} ${item.phone || ''}`.toLowerCase()
    const lastAnswerAt = item.last_answer_at ? new Date(item.last_answer_at).getTime() : 0
    if (search && !searchable.includes(search)) return false
    if (userFilters.exam_target && item.exam_target !== userFilters.exam_target) return false
    if (userFilters.membership_status === 'active' && !isPortalUserMembershipActive(item)) return false
    if (userFilters.membership_status === 'inactive' && isPortalUserMembershipActive(item)) return false
    if (userFilters.account_status === 'active' && item.disabled_at) return false
    if (userFilters.account_status === 'disabled' && !item.disabled_at) return false
    if (userFilters.activity === 'active_7d' && (!lastAnswerAt || now - lastAnswerAt > 7 * 86400000)) return false
    if (userFilters.activity === 'inactive' && lastAnswerAt && now - lastAnswerAt < 30 * 86400000) return false
    return true
  })
  filteredUsers = sortPortalUserItems(filteredUsers)
  portalUsers.value = filteredUsers
  portalUserCount.value = portalUsers.value.length
}

function homeContentSlotLimit(slot) {
  return HOME_CONTENT_SLOT_LIMITS[slot] || 0
}

function homeContentSlotLabel(slot) {
  return slot === 'news' ? '港澳台考研资讯' : '焦点轮播'
}

function homeContentSlotAtCapacity(slot) {
  const count = slot === 'news' ? homeNewsPublishedCount.value : homeFocusPublishedCount.value
  return count >= homeContentSlotLimit(slot)
}

function sortPortalUserItems(items) {
  const direction = userSort.direction === 'asc' ? 1 : -1
  const valueFor = (item) => {
    if (userSort.field === 'exam_target') return String(item.exam_target || '')
    if (userSort.field === 'answer_count') return Number(item.answer_count || 0)
    if (userSort.field === 'accuracy') return Number(item.accuracy || 0)
    const timestamp = item[userSort.field === 'last_active' ? 'last_answer_at' : 'created_at']
    return timestamp ? new Date(timestamp).getTime() : null
  }
  return [...items].sort((left, right) => {
    const leftValue = valueFor(left)
    const rightValue = valueFor(right)
    if (leftValue === null || rightValue === null) {
      if (leftValue !== rightValue) return leftValue === null ? 1 : -1
    } else if (typeof leftValue === 'string') {
      const comparison = leftValue.localeCompare(rightValue)
      if (comparison) return comparison * direction
    } else if (leftValue !== rightValue) {
      return (leftValue - rightValue) * direction
    }
    const createdAtComparison = String(right.created_at || '').localeCompare(String(left.created_at || ''))
    return createdAtComparison || String(left.id || '').localeCompare(String(right.id || ''))
  })
}

function buildDevPreviewUserDetail(item) {
  return {
    profile: { ...item },
    answer_summary: { total: item.answer_count, correct: item.correct_count, wrong: item.wrong_count, wrong_question_count: Math.round(item.wrong_count / 2), accuracy: item.accuracy },
    subject_accuracy: [
      { subject: '中华文化', total: 132, correct: 91, wrong: 41, accuracy: 68.9 },
      { subject: '英语运用', total: 118, correct: 78, wrong: 40, accuracy: 66.1 },
      { subject: '逻辑推理', total: 93, correct: 61, wrong: 32, accuracy: 65.6 }
    ],
    recent_answers: [
      { id: 'preview-answer-1', subject: '中华文化', stem: '下列关于宋代理学的说法，正确的是：', is_correct: true, created_at: '2026-08-18T15:20:00Z' },
      { id: 'preview-answer-2', subject: '英语运用', stem: 'The word “abundant” is closest in meaning to ____.', is_correct: false, created_at: '2026-08-18T15:18:00Z' }
    ],
    membership_orders: [],
    admin_actions: []
  }
}

function loadDevPreviewAdmission() {
  const dataset = admissionDataset.value
  if (!devPreviewAdmissionRuns[dataset].length) {
    if (dataset === 'scorelines') {
      devPreviewAdmissionRuns[dataset] = [
        { id: 'preview-score-run-1', source_filename: '学生端历史分数线（2024-2026）', record_count: legacyScorelineImportRecords.value.length, status: 'published', created_at: '2026-08-10T02:00:00Z', published_at: '2026-08-10T03:00:00Z', statistics: { valid_rows: legacyScorelineImportRecords.value.length } },
        { id: 'preview-score-run-2', source_filename: '2026历年分数线补充.xlsx', record_count: 18, status: 'draft', created_at: '2026-08-18T09:20:00Z', statistics: { valid_rows: 18 } },
        { id: 'preview-score-run-3', source_filename: '格式错误示例.xlsx', record_count: 0, status: 'failed', created_at: '2026-08-18T06:20:00Z', statistics: { valid_rows: 0 } }
      ]
    } else if (dataset === 'announcements') {
      devPreviewAdmissionRuns[dataset] = [
        { id: 'preview-notice-run-1', source_filename: '2026院校公告.xlsx', record_count: 360, status: 'published', created_at: '2026-08-08T06:00:00Z', published_at: '2026-08-08T07:00:00Z', statistics: { valid_rows: 360 } },
        { id: 'preview-notice-run-2', source_filename: '2026院校公告增量.xlsx', record_count: 12, status: 'draft', created_at: '2026-08-18T08:10:00Z', statistics: { valid_rows: 12 } }
      ]
    } else {
      devPreviewAdmissionRuns[dataset] = [
        { id: 'preview-major-run-1', source_filename: '2026专业目录完整快照.xlsx', record_count: 29756, status: 'published', created_at: '2026-08-06T03:00:00Z', published_at: '2026-08-06T04:15:00Z', statistics: { valid_rows: 29756, catalog_year: '2026' } },
        { id: 'preview-major-run-2', source_filename: '2026专业目录更新.xlsx', record_count: 126, status: 'draft', created_at: '2026-08-18T07:40:00Z', statistics: { valid_rows: 126, catalog_year: '2026' } }
      ]
    }
  }
  admissionRuns.value = devPreviewAdmissionRuns[dataset].map((item) => ({
    ...item,
    statistics: { ...(item.statistics || {}) }
  }))
  if (dataset === 'announcements' && !devPreviewAnnouncementRecords.value.length) {
    devPreviewAnnouncementRecords.value = [
      { id: 'preview-notice-1', import_run_id: 'preview-notice-run-1', notice_year: '2026', region: '广东', school_id: 'preview-school-jnu', school_name: '暨南大学', unit_name: '研究生院', notice_type: 'brochure', title: '2026 年面向港澳台地区研究生招生简章', summary: '含报名条件、考试科目与录取办法。', notice_date: '2026-04-08', status: 'published' },
      { id: 'preview-notice-2', import_run_id: 'preview-notice-run-1', notice_year: '2026', region: '广东', school_id: 'preview-school-scut', school_name: '华南理工大学', unit_name: '', notice_type: 'scoreline_retest', title: '2026 年港澳台研究生复试分数线', summary: '各学院复试安排以学院通知为准。', notice_date: '2026-04-06', status: 'published' },
      { id: 'preview-notice-3', import_run_id: 'preview-notice-run-2', notice_year: '2026', region: '广东', school_id: 'preview-school-sysu', school_name: '中山大学', unit_name: '研究生院', notice_type: 'brochure', title: '2026 年港澳台研究生招生补充说明', summary: '补充报名材料与时间安排。', notice_date: '2026-08-18', status: 'draft' }
    ]
  }
}

function loadDevPreviewHomeContent() {
  if (!devPreviewHomeContentItems.value.length) {
    devPreviewHomeContentItems.value = [
      { id: 'preview-focus-1', slot: 'focus', title: '初试统考准考证打印提醒', subtitle: '广州报考点考生请及时核对考试信息', badge: '考试提醒', cover_label: '准考证', tone: 'is-blue', route_key: 'application-guide', status: 'published', sort_order: 1 },
      { id: 'preview-focus-2', slot: 'focus', title: '查看 2026 专业目录', subtitle: '按地区、院校和考试类别筛选招生专业', badge: '专业目录', cover_label: '专业目录', tone: 'is-mint', route_key: 'major-catalog', status: 'published', sort_order: 2 },
      { id: 'preview-focus-3', slot: 'focus', title: '院校公告更新提醒', subtitle: '最新简章与复试分数线集中查看', badge: '院校公告', cover_label: '公告', tone: 'is-violet', route_key: 'school-announcements', status: 'published', sort_order: 3, starts_at: '2026-08-25T00:00:00Z' },
      { id: 'preview-focus-4', slot: 'focus', title: 'Z001 / Z002 考试指南', subtitle: '了解考试模块、范围与备考方向', badge: '备考指南', cover_label: '考试指南', tone: 'is-orange', status: 'draft', sort_order: 4 },
      { id: 'preview-news-1', slot: 'news', title: '2026 年面向港澳台地区研究生招生初试统考准考证打印提醒', source: '广东省教育考试院', display_date: '2026-04-01', cover_label: '准考证打印', tone: 'is-blue', target_url: 'https://www.gatzs.com.cn/', status: 'published', sort_order: 1 },
      { id: 'preview-news-2', slot: 'news', title: '2026 年港澳台研究生招生广州报考点通告', source: '广东省教育考试院', display_date: '2025-12-16', cover_label: '广州报考点', tone: 'is-orange', status: 'published', sort_order: 2 },
      { id: 'preview-news-3', slot: 'news', title: '2026 年面向香港、澳门、台湾地区研究生招生考试指南正式公布', source: '教育部教育考试院', display_date: '2025-12-07', cover_label: '考试指南', tone: 'is-mint', status: 'published', sort_order: 3 }
    ]
  }
  homeContentItems.value = devPreviewHomeContentItems.value.map((item) => ({ ...item }))
}

function optionIndex(options, value) {
  const index = options.findIndex((item) => item.value === value)
  return index >= 0 ? index : 0
}

function questionDisplayStatus(question) {
  const status = String(question?.status || QUESTION_STATUS.ARCHIVED)
  const reviewStatus = String(question?.review_status || '')
  if (status === QUESTION_STATUS.ARCHIVED && reviewStatus === 'pending') {
    return QUESTION_STATUS.PENDING_REVIEW
  }
  return status
}

function communityPostStatusText(isPublished) {
  return isPublished ? '公开展示' : '已下架'
}

function communityPostTypeText(postType) {
  return postType === 'experience' ? '经验贴' : '研友聊'
}

function questionStatusText(status) {
  return {
    [QUESTION_STATUS.ACTIVE]: '已发布',
    [QUESTION_STATUS.ARCHIVED]: '已下架',
    [QUESTION_STATUS.PENDING_REVIEW]: '待审核'
  }[status] || '待审核'
}

function questionStatusTone(status) {
  return {
    [QUESTION_STATUS.ACTIVE]: 'published',
    [QUESTION_STATUS.ARCHIVED]: 'archived',
    [QUESTION_STATUS.PENDING_REVIEW]: 'pending'
  }[status] || 'pending'
}

function confirmAction(title, content, confirmText) {
  return new Promise((resolve) => {
    uni.showModal({
      title,
      content,
      confirmText,
      cancelText: '取消',
      success: (result) => resolve(Boolean(result.confirm)),
      fail: () => resolve(false)
    })
  })
}

function formatCount(value) {
  return Number(value || 0).toLocaleString('zh-CN')
}

function compactCount(value) {
  const count = Number(value || 0)
  if (count > 999) return '999+'
  return String(count)
}

function isPortalUserMembershipActive(item, now = Date.now()) {
  if (item?.membership_status !== 'active') return false
  if (!item?.membership_expires_at) return true
  const expiresAt = new Date(item.membership_expires_at).getTime()
  return Number.isFinite(expiresAt) && expiresAt > now
}

function portalUserMembershipLabel(item) {
  if (isPortalUserMembershipActive(item)) return '有效会员'
  if (item?.membership_status === 'active' && item?.membership_expires_at) return '会员已过期'
  return '普通用户'
}

function membershipOrderPlanLabel(order) {
  if (order?.plan_code === 'pro_monthly') return '月度会员'
  if (order?.plan_code === 'pro_quarterly') return '季度会员'
  return order?.plan_code || '会员订单'
}

function membershipOrderProviderLabel(order) {
  const provider = String(order?.provider || '支付订单')
  const orderId = String(order?.provider_order_id || '')
  return orderId ? `${provider} · ${orderId.slice(-8)}` : provider
}

function membershipOrderStatusLabel(order) {
  const labels = { paid: '已支付', pending: '待支付', failed: '支付失败', cancelled: '已取消', refunded: '已退款' }
  return labels[String(order?.status || '').toLowerCase()] || '状态未知'
}

function membershipOrderStatusTone(order) {
  return `is-${String(order?.status || 'pending').toLowerCase()}`
}

function membershipOrderAmount(order) {
  const cents = Number(order?.amount_cents)
  if (!Number.isFinite(cents)) return '金额待确认'
  return `${order?.currency || 'CNY'} ${(cents / 100).toFixed(2)}`
}

function shortId(value) {
  return String(value || '').replace(/-/g, '').slice(0, 8).toUpperCase() || '—'
}

function formatDate(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('zh-CN', {
    year: '2-digit',
    month: '2-digit',
    day: '2-digit'
  }).format(date)
}

function formatDateTime(value) {
  if (!value) return '—'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return new Intl.DateTimeFormat('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  }).format(date)
}

function clampAccuracy(value) {
  return Math.max(0, Math.min(100, Number(value || 0)))
}

function formatAccuracy(value) {
  return `${Number(value || 0).toFixed(1)}%`
}

function accuracyTone(value) {
  const accuracy = Number(value || 0)
  if (accuracy < 40) return 'critical'
  if (accuracy < 65) return 'warning'
  return 'healthy'
}

function accuracyHint(value) {
  const tone = accuracyTone(value)
  return tone === 'critical' ? '高关注' : tone === 'warning' ? '需留意' : '正常'
}
</script>

<style scoped>
page {
  background: #eef3f7;
}

button::after {
  border: 0;
}

button {
  font-family: inherit;
}

.portal-shell {
  --sidebar: #21354b;
  --sidebar-deep: #1a2b3f;
  --sidebar-control-size: 43px;
  --ink: #182438;
  --muted: #748195;
  --line: #dde6eb;
  --soft-line: #eaf0f3;
  --panel: #ffffff;
  --page: #eef3f7;
  --mint: #50d0b4;
  --mint-dark: #22aa8f;
  min-height: 100vh;
  color: var(--ink);
  background: var(--page);
  font-family: var(--gyt-app-font);
}

.portal-sidebar {
  position: fixed;
  z-index: 20;
  left: 0;
  top: 0;
  bottom: 0;
  width: 238px;
  padding: 28px 18px 20px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
  background:
    radial-gradient(circle at 10% 0%, rgba(89, 211, 184, 0.14), transparent 26%),
    linear-gradient(180deg, var(--sidebar), var(--sidebar-deep));
  color: #fff;
  transition: width 0.28s ease, padding 0.28s ease, transform 0.28s ease, opacity 0.22s ease;
}

.sidebar-brand {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  min-height: 43px;
  padding: 0 10px;
  transition: padding 0.24s ease, justify-content 0.24s ease;
}

.sidebar-focus-toggle {
  width: var(--sidebar-control-size);
  height: var(--sidebar-control-size);
  min-height: var(--sidebar-control-size);
  margin: 0;
  padding: 0;
  position: absolute;
  top: 0;
  right: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border: 1px solid rgba(119, 226, 202, 0.38);
  border-radius: 13px;
  box-sizing: border-box;
  color: #89ead4;
  background: rgba(255, 255, 255, 0.07);
  box-shadow: 0 8px 20px rgba(9, 25, 42, 0.18);
  cursor: pointer;
  line-height: 1;
  transition: border-color 0.18s ease, background 0.18s ease, transform 0.18s ease;
}

.sidebar-focus-toggle::after {
  border: 0;
}

.sidebar-focus-toggle:hover {
  border-color: rgba(119, 226, 202, 0.72);
  background: rgba(80, 208, 180, 0.14);
}

.sidebar-toggle-icon {
  width: 24px;
  height: 24px;
  position: absolute;
  inset: 50% auto auto 50%;
  transform: translate(-50%, -50%);
  transition: opacity 0.16s ease, transform 0.16s ease;
}

.sidebar-toggle-icon-hover {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.9);
}

.sidebar-focus-toggle:hover .sidebar-toggle-icon-default {
  opacity: 0;
  transform: translate(-50%, -50%) scale(0.9);
}

.sidebar-focus-toggle:hover .sidebar-toggle-icon-hover {
  opacity: 1;
  transform: translate(-50%, -50%) scale(1);
}

.brand-mark {
  width: var(--sidebar-control-size);
  height: var(--sidebar-control-size);
  flex: 0 0 auto;
  overflow: hidden;
  border-radius: 13px;
  background: #ffffff;
  box-shadow: 0 10px 22px rgba(20, 40, 65, 0.2);
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.brand-logo {
  display: block;
  width: 100%;
  height: 100%;
}

.brand-name {
  font-size: 17px;
  line-height: 1.2;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.brand-copy,
.sidebar-section-label,
.nav-label {
  transition: opacity 0.18s ease, max-width 0.22s ease;
}

.brand-caption {
  margin-top: 4px;
  color: rgba(255, 255, 255, 0.48);
  font-size: 11px;
  letter-spacing: 0.13em;
}

.sidebar-section-label {
  margin: 42px 13px 12px;
  color: rgba(255, 255, 255, 0.35);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.18em;
}

.sidebar-nav {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.nav-item,
.logout-button {
  width: 100%;
  min-height: 46px;
  margin: 0;
  padding: 0 13px;
  display: flex;
  align-items: center;
  gap: 12px;
  border-radius: 10px;
  color: rgba(255, 255, 255, 0.62);
  background: transparent;
  font-size: 13px;
  text-align: left;
  line-height: 1;
  transition: color 0.2s, background 0.2s;
}

.nav-item:hover,
.logout-button:hover {
  color: rgba(255, 255, 255, 0.9);
  background: rgba(255, 255, 255, 0.06);
}

.nav-item.active {
  color: #143d39;
  background: linear-gradient(135deg, #72dfc7, #4fceb2);
  box-shadow: 0 10px 20px rgba(46, 190, 158, 0.16);
  font-weight: 700;
}

.nav-glyph {
  width: 22px;
  flex: 0 0 auto;
  font-size: 17px;
  text-align: center;
  transition: width 0.2s ease, transform 0.18s ease;
}

.nav-icon {
  width: 20px;
  height: 20px;
  flex: 0 0 auto;
  background: currentColor;
  -webkit-mask: var(--nav-icon-url) center / contain no-repeat;
  mask: var(--nav-icon-url) center / contain no-repeat;
  opacity: 0.95;
  transition: width 0.2s ease, height 0.2s ease, transform 0.18s ease, opacity 0.18s ease;
}

.nav-label {
  flex: 1;
}

.nav-count {
  min-width: 19px;
  height: 19px;
  padding: 0 5px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 10px;
  color: #fff;
  background: #ee806c;
  box-sizing: border-box;
  font-size: 9px;
  font-weight: 700;
}

.nav-item.active .nav-count {
  color: #206857;
  background: rgba(255, 255, 255, 0.62);
}

.sidebar-spacer {
  flex: 1;
}

.logout-button {
  color: rgba(255, 255, 255, 0.45);
}

.portal-main {
  min-height: 100vh;
  margin-left: 238px;
  transition: margin-left 0.28s ease;
}

.portal-header {
  height: 86px;
  padding: 0 34px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e1e8ec;
  box-sizing: border-box;
  background: rgba(248, 251, 252, 0.92);
  overflow: hidden;
  transition: height 0.24s ease, padding 0.24s ease, opacity 0.18s ease;
}

.header-left {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-title-group {
  min-width: 0;
}

.header-back-button {
  width: 32px;
  height: 32px;
  margin: 0;
  padding: 0;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #b8e9f6;
  border-radius: 7px;
  box-sizing: border-box;
  color: #1d8fb6;
  background: #f8fdff;
  font-size: 18px;
  font-weight: 800;
  line-height: 1;
  box-shadow: 0 7px 16px rgba(31, 132, 172, 0.08);
}

.header-back-button[disabled] {
  opacity: 0.55;
}

.header-back-icon {
  width: 18px;
  height: 18px;
  display: block;
}

.header-breadcrumb {
  color: #8995a5;
  font-size: 10px;
}

.header-title {
  margin-top: 5px;
  color: #1d2b3f;
  font-size: 21px;
  font-weight: 700;
  letter-spacing: 0;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 18px;
}

.header-import-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-import-button {
  width: auto;
  height: 36px;
  margin: 0;
  padding: 0 13px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border-radius: 9px;
  box-sizing: border-box;
  font-size: 11px;
  font-weight: 700;
  line-height: 1;
}

.header-import-button.template {
  border: 1px solid #9be3d4;
  color: #087c6d;
  background: #effcf8;
}

.header-import-button.guide {
  border: 1px solid #c5d6ed;
  color: #395f9b;
  background: #f7faff;
}

.header-import-button.history {
  border: 1px solid #bdcce1;
  color: #50647d;
  background: #ffffff;
}

.header-import-history-icon {
  font-size: 13px;
  line-height: 1;
}

.header-refresh {
  width: auto;
  height: 36px;
  margin: 0;
  padding: 0 13px;
  display: flex;
  align-items: center;
  gap: 7px;
  border: 1px solid #dce5e9;
  border-radius: 9px;
  color: #607086;
  background: #fff;
  font-size: 11px;
  line-height: 1;
}

.refresh-symbol {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
}

.refresh-symbol.spinning {
  animation: spin 0.9s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.profile-chip {
  padding-left: 18px;
  display: flex;
  align-items: center;
  gap: 10px;
  border-left: 1px solid #e0e8ec;
}

.profile-avatar {
  width: 35px;
  height: 35px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  border-radius: 11px;
  background: #101c2a;
}

.profile-avatar-image {
  width: 100%;
  height: 100%;
  display: block;
}

.profile-name {
  max-width: 130px;
  overflow: hidden;
  color: #304056;
  font-size: 11px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.content-section {
  padding: 30px 34px 44px;
  box-sizing: border-box;
  transition: padding 0.26s ease;
}

.import-section {
  padding: 0;
}

.question-bank-section {
  max-width: 1420px;
}

.mock-exam-management-section {
  max-width: 1800px;
}

.bank-library-state {
  min-height: 280px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border: 1px solid #e0e8ec;
  border-radius: 15px;
  color: #8592a1;
  background: #fff;
  font-size: 11px;
}

.bank-library-state.error {
  color: #b2605b;
}

.bank-file-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(255px, 1fr));
  gap: 15px;
}

.bank-file-card {
  min-height: 172px;
  padding: 21px;
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 15px;
  overflow: hidden;
  border: 1px solid #e0e8ec;
  border-radius: 14px;
  box-sizing: border-box;
  cursor: default;
  background: #fff;
  box-shadow: 0 9px 24px rgba(31, 50, 71, 0.025);
  transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}

.bank-file-card:hover {
  transform: translateY(-2px);
  border-color: #9bdfd0;
  box-shadow: 0 14px 30px rgba(38, 109, 96, 0.11);
}

.bank-file-card--mock-exam {
  border-color: #b9e5dc;
  background: linear-gradient(145deg, #ffffff 0%, #f3fbf8 100%);
}

.bank-file-icon {
  width: 55px;
  height: 49px;
  margin-top: 4px;
  position: relative;
  flex: 0 0 auto;
}

.bank-file-tab {
  width: 24px;
  height: 10px;
  position: absolute;
  top: 0;
  left: 5px;
  border-radius: 7px 7px 0 0;
  background: #a6ead9;
}

.bank-file-face {
  width: 55px;
  height: 40px;
  position: absolute;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #8edcca;
  border-radius: 8px 10px 10px 10px;
  color: #258371;
  background: linear-gradient(135deg, #dff8f1, #bcecdf);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.7);
  font-size: 14px;
  font-weight: 800;
}

.bank-file-face--mock-exam {
  border-color: #69cdb8;
  color: #197964;
  background: linear-gradient(135deg, #d4f6ed, #9fe3d3);
}

.bank-file-main {
  min-width: 0;
  flex: 1;
}

.bank-file-title-row {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.bank-file-name {
  min-width: 0;
  overflow: hidden;
  color: #2c3a4d;
  font-size: 14px;
  font-weight: 760;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bank-rename-button {
  width: 56px;
  height: 28px;
  margin: 0;
  padding: 0;
  flex: 0 0 auto;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #dce8e6;
  border-radius: 6px;
  box-sizing: border-box;
  color: #5d827b;
  background: #f7fbfa;
  font-size: 8px;
  font-weight: 700;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
}

.bank-file-date {
  margin-top: 12px;
  color: #96a1ad;
  font-size: 8px;
}

.bank-file-enter {
  position: absolute;
  right: 20px;
  bottom: 17px;
  display: inline-flex;
  align-items: center;
  width: auto;
  min-height: 0;
  margin: 0;
  padding: 0;
  border: 0;
  color: #5b9c8f;
  background: transparent;
  cursor: pointer;
  font-size: 8px;
  line-height: 1.3;
}

.bank-file-enter::after {
  border: 0;
}

.bank-file-enter text {
  margin-left: 3px;
  font-size: 11px;
}

.bank-file-create-card {
  width: 100%;
  min-height: 172px;
  margin: 0;
  padding: 21px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 7px;
  border-style: dashed;
  border-color: #b8dbd4;
  color: #66817c;
  background: rgba(255, 255, 255, 0.6);
  cursor: pointer;
}

.bank-file-create-card:hover {
  border-color: #62c8b2;
  background: #f8fdfc;
}

.bank-file-create-icon {
  width: 35px;
  height: 35px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 11px;
  color: #288c78;
  background: #dff5ef;
  font-size: 21px;
  font-weight: 400;
}

.bank-file-create-title {
  margin-top: 3px;
  color: #49726b;
  font-size: 12px;
  font-weight: 750;
}

.welcome-row {
  max-height: 110px;
  overflow: hidden;
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  opacity: 1;
  transition: max-height 0.22s ease, opacity 0.16s ease, transform 0.22s ease;
}

.welcome-kicker {
  color: #8491a1;
  font-size: 11px;
}

.welcome-title {
  margin-top: 7px;
  color: #17253a;
  font-size: 27px;
  line-height: 1.25;
  font-weight: 720;
  letter-spacing: 0;
}

.welcome-copy {
  margin-top: 8px;
  color: #7d8999;
  font-size: 12px;
}

.welcome-badge {
  height: 30px;
  padding: 0 12px;
  display: flex;
  align-items: center;
  gap: 7px;
  border: 1px solid #d9e8e3;
  border-radius: 15px;
  color: #5d786f;
  background: rgba(255, 255, 255, 0.55);
  font-size: 10px;
}

.badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #4ecdb0;
}

.dashboard-metrics {
  margin-top: 25px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16px;
  transition: margin-top 0.22s ease;
}

.sidebar-collapsed .portal-sidebar {
  width: 72px;
  padding: 28px 10px 20px;
  transform: none;
  opacity: 1;
  pointer-events: auto;
}

.sidebar-collapsed .portal-main {
  margin-left: 72px;
}

.sidebar-collapsed:not(.dashboard-focus-mode):not(.import-preview-focus-mode) .portal-header {
  padding-left: 24px;
  padding-right: 22px;
}

.sidebar-collapsed .sidebar-brand {
  justify-content: center;
  padding: 0;
}

.sidebar-collapsed .brand-copy,
.sidebar-collapsed .sidebar-section-label,
.sidebar-collapsed .nav-label {
  max-width: 0;
  opacity: 0;
  overflow: hidden;
  pointer-events: none;
  visibility: hidden;
}

.sidebar-collapsed .brand-mark {
  opacity: 0;
  transform: scale(0.86);
  pointer-events: none;
  visibility: hidden;
}

.sidebar-collapsed .sidebar-focus-toggle {
  width: var(--sidebar-control-size);
  height: var(--sidebar-control-size);
  min-height: var(--sidebar-control-size);
  top: 0;
  right: auto;
  left: 50%;
  padding: 0;
  border-radius: 13px;
  border-color: rgba(119, 226, 202, 0.54);
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 18px rgba(9, 25, 42, 0.16);
  opacity: 1;
  transform: translateX(-50%);
}

.sidebar-collapsed .sidebar-focus-toggle:focus {
  border-color: rgba(119, 226, 202, 0.54);
  background: rgba(255, 255, 255, 0.1);
  box-shadow: 0 8px 18px rgba(9, 25, 42, 0.16);
  opacity: 1;
}

.sidebar-collapsed .sidebar-focus-toggle:hover {
  transform: translateX(-50%);
}

.sidebar-collapsed .sidebar-section-label {
  margin: 28px 0 10px;
}

.sidebar-collapsed .sidebar-nav {
  align-items: center;
  gap: 8px;
}

.sidebar-collapsed .nav-item,
.sidebar-collapsed .logout-button {
  width: 44px;
  min-height: 44px;
  padding: 0;
  justify-content: center;
  gap: 0;
}

.sidebar-collapsed .nav-glyph,
.sidebar-collapsed .nav-icon {
  width: auto;
  transform: scale(1.08);
}

.sidebar-collapsed .nav-icon {
  width: 20px;
  height: 20px;
}

.sidebar-collapsed .nav-count {
  position: absolute;
  margin: -25px 0 0 25px;
}

.sidebar-collapsed .question-bank-section {
  max-width: none;
  padding: 22px 22px 36px;
}

.sidebar-collapsed .bank-file-grid {
  grid-template-columns: repeat(auto-fill, minmax(280px, 320px));
  gap: 14px;
}

.dashboard-focus-mode .portal-header {
  height: 0;
  padding-top: 0;
  padding-bottom: 0;
  border-bottom-color: transparent;
  opacity: 0;
  pointer-events: none;
}

.dashboard-focus-mode .dashboard-section {
  min-height: 100vh;
  padding: 16px 18px 30px;
}

.dashboard-focus-mode .welcome-row {
  max-height: 0;
  opacity: 0;
  transform: translateY(-12px);
  pointer-events: none;
}

.dashboard-focus-mode .dashboard-metrics {
  margin-top: 0;
}

.dashboard-focus-mode .metric-card {
  min-height: 126px;
}

.dashboard-focus-mode .dashboard-panel {
  margin-top: 14px;
}

.import-preview-focus-mode .portal-header {
  height: 0;
  padding-top: 0;
  padding-bottom: 0;
  border-bottom-color: transparent;
  opacity: 0;
  pointer-events: none;
}

.import-preview-focus-mode .import-section {
  min-height: 100vh;
  padding: 0;
}

.metric-card {
  min-height: 142px;
  padding: 20px;
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 15px;
  border: 1px solid #e1e8ec;
  border-radius: 14px;
  box-sizing: border-box;
  background: #fff;
  box-shadow: 0 9px 26px rgba(31, 50, 71, 0.035);
}

.metric-icon,
.summary-icon {
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  font-size: 13px;
  font-weight: 800;
}

.metric-icon.mint,
.summary-icon.mint {
  color: #16836e;
  background: #dcf6ef;
}

.metric-icon.blue,
.summary-icon.blue {
  color: #416b98;
  background: #e5eef8;
}

.metric-icon.slate,
.summary-icon.slate {
  color: #65758b;
  background: #edf1f4;
}

.metric-icon.metric-icon-asset {
  padding: 9px;
  box-sizing: border-box;
  background: #e7f6f1;
  border: 1px solid #d0eee5;
}

.metric-icon-image {
  width: 100%;
  height: 100%;
  display: block;
  filter: brightness(0) saturate(100%) invert(45%) sepia(30%) saturate(1130%) hue-rotate(121deg) brightness(94%) contrast(88%);
}

.summary-icon.orange {
  color: #bd7544;
  background: #fff0e1;
}

.metric-content {
  min-width: 0;
  flex: 1;
}

.metric-label {
  color: #748195;
  font-size: 11px;
  font-weight: 600;
}

.metric-value {
  margin-top: 8px;
  color: #17263a;
  font-size: 31px;
  line-height: 1;
  font-weight: 700;
  letter-spacing: 0;
}

.metric-note {
  margin-top: 12px;
  color: #98a2af;
  font-size: 9px;
  line-height: 1.5;
}

.metric-growth {
  position: absolute;
  right: 18px;
  bottom: 18px;
  display: flex;
  align-items: baseline;
  gap: 5px;
  color: #df706c;
  opacity: 0;
  pointer-events: none;
  transform: translateY(5px);
  transition: opacity 0.24s ease, transform 0.24s ease;
}

.metric-growth-count {
  font-size: 15px;
  font-weight: 800;
  line-height: 1;
}

.metric-growth-label {
  font-size: 9px;
  font-weight: 700;
  line-height: 1;
}

@media (hover: hover) {
  .registered-users-card:hover .metric-growth {
    opacity: 1;
    transform: translateY(0);
  }
}

.metric-chip {
  position: absolute;
  top: 17px;
  right: 17px;
  color: #8190a1;
  font-size: 8px;
}

.metric-chip {
  padding: 5px 7px;
  border-radius: 6px;
  background: #f3f6f7;
}

.metric-link {
  width: auto;
  margin: 0;
  padding: 5px;
  position: absolute;
  right: 14px;
  bottom: 13px;
  color: #2aad91;
  background: transparent;
  font-size: 9px;
  line-height: 1;
}

.dashboard-panel,
.question-workspace {
  margin-top: 19px;
  border: 1px solid #e0e8ec;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 9px 26px rgba(31, 50, 71, 0.03);
}

.question-workspace.compact {
  margin-top: 0;
}

.community-summary {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 13px;
}

.content-management-switcher {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 18px;
}

.content-management-tab {
  min-width: 0;
  min-height: 112px;
  margin: 0;
  padding: 18px 20px;
  display: flex;
  align-items: center;
  gap: 14px;
  box-sizing: border-box;
  border: 1px solid #dfe9eb;
  border-top: 3px solid #9aa9b8;
  border-radius: 8px;
  background: #ffffff;
  color: #314a65;
  box-shadow: 0 8px 24px rgba(39, 62, 79, 0.04);
  line-height: 1;
  text-align: left;
}

.content-management-tab::after {
  border: 0;
}

.content-management-tab.active {
  border-color: #94dccc;
  border-top-color: #34b399;
  background: #f2fcf8;
  box-shadow: 0 10px 28px rgba(52, 179, 153, 0.12);
}

.content-management-tab-icon {
  width: 32px;
  height: 32px;
  flex: 0 0 32px;
}

.content-management-tab-copy {
  min-width: 0;
  flex: 1;
}

.content-management-tab-label,
.content-management-tab-description {
  display: block;
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.bank-file-fixed-badge {
  flex: 0 0 auto;
  padding: 4px 7px;
  border-radius: 999px;
  color: #267d6d;
  background: #e2f7f1;
  font-size: 8px;
  font-weight: 750;
  line-height: 1;
}

.content-management-tab-label {
  color: #385069;
  font-size: 15px;
  font-weight: 800;
  line-height: 1.25;
}

.content-management-tab-description {
  margin-top: 7px;
  color: #8292a1;
  font-size: 11px;
  line-height: 1.25;
}

.content-management-tab-arrow {
  color: #90a3ad;
  font-size: 24px;
  line-height: 1;
}

.content-management-tab.active .content-management-tab-arrow {
  color: #299b84;
}

@media (max-width: 1040px) {
  .content-management-switcher {
    grid-template-columns: 1fr;
  }
}

.community-summary-card {
  min-height: 104px;
  padding: 16px 18px;
  position: relative;
  overflow: hidden;
  border: 1px solid #dbe6ea;
  border-radius: 10px;
  box-sizing: border-box;
  background: #fff;
  box-shadow: 0 7px 22px rgba(31, 50, 71, 0.025);
}

.community-summary-card::before {
  width: 4px;
  content: '';
  position: absolute;
  inset: 16px auto 16px 0;
  border-radius: 0 3px 3px 0;
  background: #75a8d7;
}

.community-summary-card.mint::before {
  background: #57cbb1;
}

.community-summary-card.slate::before {
  background: #96a6b8;
}

.community-summary-card.blue::before {
  background: #5c9de2;
}

.community-summary-label {
  color: #718096;
  font-size: 10px;
  font-weight: 700;
}

.community-summary-value {
  margin-top: 12px;
  color: #1f2f44;
  font-size: 23px;
  font-weight: 750;
  line-height: 1;
}

.community-summary-note {
  margin-top: 10px;
  color: #98a3af;
  font-size: 9px;
}

.community-workspace {
  margin-top: 0;
}

.community-filter-toolbar {
  background: #fbfcfd;
}

.community-search-shell {
  width: 292px;
}

.community-admin-select {
  width: 120px;
  --admin-select-menu-min-width: 132px;
}

.community-admin-select.sort {
  width: 164px;
  --admin-select-menu-min-width: 164px;
}

.community-featured-button {
  width: 96px;
  height: 37px;
  margin: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border: 1px solid #a9ddcf;
  border-radius: 8px;
  box-sizing: border-box;
  color: #197966;
  background: #eaf8f4;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
}

.community-featured-button:hover:not([disabled]) {
  border-color: #66c6ae;
  background: #ddf5ee;
}

.community-featured-button.remove {
  border-color: #d8e0e5;
  color: #66778a;
  background: #f5f7f8;
}

.community-featured-button[disabled] {
  border-color: #e1e8eb;
  color: #a3afb9;
  background: #f6f8f9;
}

.community-table {
  min-width: 980px;
}

.community-grid {
  width: 100%;
  padding: 0 15px;
  display: grid;
  grid-template-columns: 42px minmax(220px, 2.3fr) minmax(118px, 0.9fr) 76px 48px 48px 48px 68px 76px 58px;
  align-items: center;
  box-sizing: border-box;
}

.community-row {
  min-height: 84px;
  border-top: 1px solid #edf1f3;
  color: #536176;
  background: #fff;
  cursor: pointer;
  transition: background 0.16s ease;
}

.community-row:hover {
  background: #f7fbfa;
}

.community-row.selected {
  background: #f3fbf8;
}

.community-grid.table-head.selecting {
  color: #5d716c;
  background: #f0faf7;
}

.community-selection-header {
  grid-column: 2 / 3;
  min-width: 0;
  min-height: 42px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 20px;
}

.community-selection-header .bulk-copy {
  margin-right: 0;
}

.community-post-cell,
.community-author-cell,
.community-category-cell,
.community-action-cell {
  min-width: 0;
}

.community-post-title {
  overflow: hidden;
  color: #26364a;
  font-size: 12px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.community-post-copy {
  margin-top: 6px;
  overflow: hidden;
  color: #9aa4b0;
  font-size: 10px;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.community-author-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.community-author-avatar,
.community-detail-avatar,
.community-comment-avatar {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border: 1px solid #d2ebe5;
  color: #267b6d;
  background: #e7f7f2;
  font-weight: 800;
}

.community-author-avatar {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  font-size: 11px;
}

.community-author-meta {
  min-width: 0;
}

.community-author-name {
  overflow: hidden;
  color: #43546a;
  font-size: 11px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.community-author-id,
.community-category-type {
  margin-top: 4px;
  overflow: hidden;
  color: #9aa5b1;
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.community-category-primary {
  color: #4c5d71;
  font-size: 11px;
  font-weight: 700;
}

.community-stat-cell {
  color: #536277;
  font-size: 11px;
  font-weight: 650;
}

.community-action-cell {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.community-action-cell .row-action,
.community-visibility-button {
  width: 52px;
  height: 25px;
  margin: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #f0d0cd;
  border-radius: 6px;
  box-sizing: border-box;
  color: #a65a53;
  background: #fff7f6;
  font-size: 9px;
  font-weight: 700;
  line-height: 1;
}

.community-visibility-button.restore {
  border-color: #cce8e1;
  color: #267f6e;
  background: #f3fbf8;
}

.community-detail-backdrop {
  z-index: 106;
  align-items: stretch;
  justify-content: flex-end;
  padding: 0;
}

.community-detail-modal {
  width: min(840px, 100vw);
  height: 100vh;
  max-height: none;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid rgba(221, 233, 235, 0.92);
  border-radius: 0;
  box-sizing: border-box;
  background: #fff;
  box-shadow: 0 22px 64px rgba(19, 35, 52, 0.2);
}

.community-detail-header {
  flex: 0 0 auto;
}

.community-detail-scroll {
  min-height: 0;
  flex: 1;
  background: #fbfcfd;
}

.community-detail-content {
  padding: 22px 28px 30px;
}

.community-detail-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.community-detail-author {
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.community-detail-avatar {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  font-size: 13px;
}

.community-detail-author-name {
  color: #35465b;
  font-size: 12px;
  font-weight: 750;
}

.community-detail-author-id,
.community-detail-status > text:last-child {
  margin-top: 5px;
  color: #98a3af;
  font-size: 9px;
}

.community-detail-status {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.community-detail-stat-grid {
  margin-top: 19px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  border: 1px solid #e3eaed;
  border-radius: 9px;
  background: #fff;
}

.community-detail-stat-grid > view {
  min-height: 68px;
  padding: 13px 15px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  border-right: 1px solid #edf1f3;
  box-sizing: border-box;
}

.community-detail-stat-grid > view:last-child {
  border-right: 0;
}

.community-detail-stat-grid text {
  color: #97a2ae;
  font-size: 9px;
}

.community-detail-stat-grid strong {
  margin-top: 7px;
  overflow: hidden;
  color: #3c4d62;
  font-size: 13px;
  font-weight: 750;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.community-detail-topic-row {
  margin-top: 22px;
  display: flex;
  align-items: center;
  gap: 7px;
}

.community-detail-topic-row text {
  padding: 4px 7px;
  border-radius: 6px;
  color: #39776c;
  background: #e9f7f2;
  font-size: 9px;
  font-weight: 700;
}

.community-detail-title {
  margin-top: 14px;
  color: #243449;
  font-size: 17px;
  font-weight: 750;
  line-height: 1.45;
}

.community-detail-body {
  margin-top: 12px;
  color: #536276;
  font-size: 12px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.community-detail-media-grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.community-detail-media-item {
  aspect-ratio: 1;
  overflow: hidden;
  border-radius: 8px;
  background: #e8f0ef;
}

.community-detail-media-item image {
  width: 100%;
  height: 100%;
  display: block;
}

.community-detail-media-fallback {
  width: 100%;
  height: 100%;
  padding: 12px;
  display: flex;
  align-items: flex-end;
  box-sizing: border-box;
  color: #507269;
  background: #e6f3ef;
  font-size: 10px;
}

.community-detail-comments-heading {
  margin-top: 26px;
  padding-bottom: 9px;
  border-bottom: 1px solid #e6ecef;
  color: #405166;
  font-size: 11px;
  font-weight: 750;
}

.community-detail-comments-heading text {
  margin-left: 5px;
  color: #76a098;
}

.community-detail-comment {
  padding: 13px 0;
  display: flex;
  align-items: flex-start;
  gap: 9px;
  border-bottom: 1px solid #eef2f4;
}

.community-comment-avatar {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  font-size: 10px;
}

.community-comment-main {
  min-width: 0;
  flex: 1;
}

.community-comment-topline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  color: #647387;
  font-size: 10px;
  font-weight: 700;
}

.community-comment-topline text:last-child,
.community-comment-likes {
  color: #a0aab5;
  font-size: 9px;
  font-weight: 400;
}

.community-comment-copy {
  margin-top: 5px;
  color: #58687b;
  font-size: 10px;
  line-height: 1.6;
}

.community-comment-likes {
  min-width: 42px;
  padding-top: 2px;
  text-align: right;
}

.community-comment-management {
  min-width: 56px;
  display: grid;
  justify-items: end;
  gap: 5px;
}

.community-comment-status {
  padding: 3px 6px;
  border-radius: 999px;
  color: #258675;
  background: #e8f7f2;
  font-size: 8px;
  font-weight: 750;
}

.community-comment-status.archived {
  color: #b2655e;
  background: #fbeceb;
}

.community-comment-management button {
  min-width: 42px;
  height: 22px;
  margin: 0;
  padding: 0 7px;
  border: 1px solid #edcbc7;
  border-radius: 5px;
  color: #b55f57;
  background: #fff8f7;
  font-size: 8px;
  line-height: 1;
}

.community-comment-management button.restore {
  border-color: #cce8e1;
  color: #267f6e;
  background: #f3fbf8;
}

.community-comment-management button::after {
  border: 0;
}

.community-detail-empty-comments {
  padding: 22px 0 4px;
  color: #9aa5b0;
  font-size: 10px;
  text-align: center;
}

.community-detail-footer {
  flex: 0 0 auto;
}

.panel-heading,
.workspace-heading {
  min-height: 78px;
  padding: 0 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e8eef1;
  box-sizing: border-box;
}

.dashboard-panel .panel-heading {
  gap: 18px;
}

.panel-title {
  color: #26354a;
  font-size: 14px;
  font-weight: 750;
}

.panel-subtitle {
  margin-top: 5px;
  color: #8b96a5;
  font-size: 9px;
}

.dashboard-filter-bar {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 12px;
}

.dashboard-filter-control {
  display: flex;
  align-items: center;
  gap: 7px;
}

.dashboard-filter-label {
  color: #8693a3;
  font-size: 9px;
  font-weight: 700;
  white-space: nowrap;
}

.dashboard-admin-select {
  width: 126px;
  --admin-select-height: 34px;
  --admin-select-font-size: 11px;
  --admin-select-menu-min-width: 126px;
}

.dashboard-admin-select.sort {
  width: 174px;
  --admin-select-menu-min-width: 174px;
}

.dashboard-admin-select.compact {
  width: 104px;
  --admin-select-menu-min-width: 126px;
}

.data-table {
  min-width: 760px;
}

.table-row {
  width: 100%;
  margin: 0;
  padding: 0 20px;
  display: grid;
  align-items: center;
  box-sizing: border-box;
  text-align: left;
}

.difficult-table .table-row {
  grid-template-columns: 60px minmax(260px, 2.2fr) minmax(140px, 1fr) 95px 95px minmax(150px, 1fr);
}

.table-head {
  min-height: 41px;
  color: #8a96a5;
  background: #f8fafb;
  font-size: 10px;
  font-weight: 700;
}

.difficult-row {
  min-height: 73px;
  border-top: 1px solid #edf1f3;
  border-radius: 0;
  color: #46556a;
  background: #fff;
  font-size: 10px;
  line-height: 1.3;
}

.difficult-row:hover,
.question-row:hover {
  background: #f7fbfa;
}

.rank-badge {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #7a8797;
  background: #f0f3f5;
  font-size: 9px;
  font-weight: 800;
}

.rank-badge.top {
  color: #16846f;
  background: #ddf5ef;
}

.stem-cell,
.category-cell,
.question-stem-cell,
.question-category-cell {
  min-width: 0;
}

.stem-primary,
.table-stem {
  overflow: hidden;
  color: #26364a;
  font-size: 12px;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stem-id,
.table-answer {
  margin-top: 6px;
  color: #9aa4b0;
  font-size: 10px;
}

.category-cell,
.question-category-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.category-primary,
.table-subject {
  color: #4a596d;
  font-size: 11px;
  font-weight: 700;
}

.category-secondary,
.table-module {
  color: #939eab;
  font-size: 10px;
}

.number-cell {
  color: #536277;
  font-size: 11px;
  font-weight: 650;
}

.wrong-number {
  color: #d66f61;
}

.accuracy-copy {
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: #45546a;
  font-size: 10px;
  font-weight: 700;
}

.accuracy-tone {
  font-size: 8px;
  font-weight: 600;
}

.accuracy-tone.critical { color: #d45f57; }
.accuracy-tone.warning { color: #cf8c4a; }
.accuracy-tone.healthy { color: #2baa8d; }

.accuracy-track {
  height: 4px;
  margin-top: 7px;
  overflow: hidden;
  border-radius: 3px;
  background: #edf1f3;
}

.accuracy-fill {
  height: 100%;
  border-radius: 3px;
}

.accuracy-fill.critical { background: #e77f74; }
.accuracy-fill.warning { background: #e4ad68; }
.accuracy-fill.healthy { background: #50cdb1; }

.inline-loading,
.empty-panel,
.table-state,
.drawer-state {
  min-height: 230px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #8a96a5;
  font-size: 11px;
}

.empty-icon {
  width: 46px;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 15px;
  color: #4ebda5;
  background: #e4f6f1;
  font-size: 22px;
  font-weight: 700;
}

.empty-icon.small {
  width: 34px;
  height: 34px;
  border-radius: 11px;
  font-size: 15px;
}

.empty-title {
  margin-top: 14px;
  color: #4b5b70;
  font-size: 12px;
  font-weight: 700;
}

.empty-copy {
  margin-top: 6px;
  color: #9aa4b0;
  font-size: 9px;
}

.question-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 13px;
}

.summary-card {
  min-height: 100px;
  margin: 0;
  padding: 15px 17px;
  border: 1px solid #e0e8ec;
  border-radius: 13px;
  box-sizing: border-box;
  color: inherit;
  background: #fff;
  text-align: left;
  box-shadow: 0 7px 22px rgba(31, 50, 71, 0.025);
  transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
}

.summary-card.interactive {
  cursor: pointer;
}

.summary-card.interactive:hover {
  border-color: #72d7c0;
  box-shadow: 0 0 0 3px rgba(79, 205, 176, 0.08), 0 12px 30px rgba(50, 148, 128, 0.1);
  transform: translateY(-1px);
}

.summary-card.interactive:active {
  transform: translateY(0);
}

.summary-card.static {
  cursor: default;
}

.summary-top {
  display: flex;
  align-items: center;
  gap: 10px;
}

.summary-icon {
  width: 31px;
  height: 31px;
  border-radius: 9px;
  border: 1px solid transparent;
  box-sizing: border-box;
  font-size: 10px;
}

.summary-icon.summary-icon-asset {
  padding: 6px;
  box-sizing: border-box;
}

.summary-icon-image {
  width: 100%;
  height: 100%;
  display: block;
}

.summary-icon.blue {
  border-color: #d5e7fb;
  background: #eef6ff;
}

.summary-icon.blue .summary-icon-image {
  filter: brightness(0) saturate(100%) invert(39%) sepia(89%) saturate(923%) hue-rotate(184deg) brightness(94%) contrast(94%);
}

.summary-icon.orange {
  border-color: #fde5c5;
  background: #fff7ed;
}

.summary-icon.orange .summary-icon-image {
  filter: brightness(0) saturate(100%) invert(55%) sepia(68%) saturate(956%) hue-rotate(359deg) brightness(97%) contrast(94%);
}

.summary-icon.mint {
  border-color: #ccece7;
  background: #ecfdf8;
}

.summary-icon.mint .summary-icon-image {
  filter: brightness(0) saturate(100%) invert(33%) sepia(30%) saturate(1581%) hue-rotate(131deg) brightness(93%) contrast(92%);
}

.summary-icon.slate {
  border-color: #dce4ec;
  background: #f3f6f8;
}

.summary-icon.slate .summary-icon-image {
  filter: brightness(0) saturate(100%) invert(39%) sepia(14%) saturate(751%) hue-rotate(176deg) brightness(89%) contrast(90%);
}

.summary-label {
  color: #738095;
  font-size: 10px;
  font-weight: 650;
}

.summary-value {
  margin: 10px 0 0 41px;
  color: #1d2b3f;
  font-size: 22px;
  line-height: 1;
  font-weight: 720;
}

.workspace-actions {
  display: flex;
  gap: 9px;
}

.primary-button,
.secondary-button {
  width: auto;
  height: 35px;
  margin: 0;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
}

.primary-button {
  color: #153f3a;
  background: linear-gradient(135deg, #69ddc4, #4ccaae);
}

.publish-question-button {
  min-width: 104px;
  font-size: 13px;
  font-weight: 900;
  letter-spacing: 0;
}

.review-start-button {
  border-color: #8ddfcd;
  color: #176b5d;
  background: #f4fcfa;
}

.workspace-actions .publish-question-button {
  width: 124px;
  min-width: 124px;
  height: 46px;
  min-height: 46px;
  max-height: 46px;
  padding: 0 18px;
  border: 1px solid #d9e5e9;
  border-radius: 10px;
  box-sizing: border-box;
  box-shadow: 0 10px 22px rgba(31, 50, 71, 0.06);
  font-size: 14px;
  font-weight: 800;
}

.workspace-actions .primary-button.publish-question-button {
  border-color: #4fcdb1;
  color: #173f3a;
  background: linear-gradient(135deg, #68dec5, #4fcdb1);
}

.workspace-actions .secondary-button.publish-question-button {
  color: #40536a;
  background: #fff;
}

.review-start-button:hover:not([disabled]) {
  border-color: #5fcdb5;
  background: #e7f8f3;
}

.secondary-button {
  border: 1px solid #d9e3e8;
  color: #617086;
  background: #fff;
}

.primary-button.large {
  height: 43px;
  margin-top: 25px;
  padding: 0 19px;
  border-radius: 10px;
  font-size: 11px;
}

.filter-toolbar {
  min-height: 64px;
  padding: 11px 17px;
  display: flex;
  align-items: center;
  gap: 9px;
  border-bottom: 1px solid #e8eef1;
  box-sizing: border-box;
  background: #fbfcfd;
}

.search-shell {
  width: 270px;
  height: 37px;
  padding: 0 10px;
  display: flex;
  align-items: center;
  border: 1px solid #dbe4e8;
  border-radius: 8px;
  box-sizing: border-box;
  background: #fff;
}

.search-shell:focus-within {
  border-color: #67cdb7;
  box-shadow: 0 0 0 3px rgba(79, 205, 176, 0.08);
}

.search-icon {
  width: 23px;
  height: 35px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  flex: 0 0 auto;
}

.search-icon-image {
  width: 15px;
  height: 15px;
  display: block;
  opacity: 0.52;
}

.search-input {
  min-width: 0;
  height: 35px;
  flex: 1;
  color: #34445a;
  font-size: 10px;
}

.search-clear {
  width: 22px;
  height: 22px;
  margin: 0;
  padding: 0;
  border-radius: 7px;
  color: #8e99a7;
  background: #f1f4f5;
  font-size: 15px;
  line-height: 22px;
}

.question-admin-select {
  width: 132px;
  flex: 0 0 auto;
  --admin-select-height: 37px;
  --admin-select-font-size: 10px;
  --admin-select-menu-min-width: 132px;
}

.question-admin-select.narrow {
  width: 104px;
  --admin-select-menu-min-width: 118px;
}

.clear-filter-button {
  width: 92px;
  height: 37px;
  margin: 0 7px 0 auto;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #d7e4ea;
  border-radius: 8px;
  box-sizing: border-box;
  color: #607188;
  background: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  box-shadow: 0 7px 16px rgba(24, 48, 76, 0.04);
}

.bulk-toolbar {
  min-height: 45px;
  padding: 7px 17px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #cdece4;
  box-sizing: border-box;
  background: #f0faf7;
}

.bulk-copy {
  margin-right: auto;
  color: #5d716c;
  font-size: 9px;
}

.bulk-copy text {
  color: #16846f;
  font-weight: 800;
}

.bulk-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bulk-button,
.bulk-cancel,
.bulk-delete {
  min-width: 72px;
  height: 32px;
  margin: 0;
  padding: 0 12px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  box-sizing: border-box;
  color: #267b69;
  background: #d8f3ec;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
}

.bulk-button.publish {
  color: #167361;
  background: #d8f3ec;
}

.bulk-button.danger {
  color: #ae5c56;
  background: #fae5e3;
}

.bulk-cancel {
  border: 1px solid #d9e5e8;
  color: #7d8998;
  background: #fff;
}

.bulk-delete {
  border: 1px solid #efc3be;
  color: #a24e48;
  background: #fff1ef;
}

.question-table-wrap {
  overflow-x: auto;
}

.question-table {
  min-width: 950px;
}

.question-grid {
  width: 100%;
  padding: 0 15px;
  display: grid;
  grid-template-columns: 42px 88px minmax(270px, 2.3fr) minmax(145px, 1fr) 78px 90px 82px 62px;
  align-items: center;
  box-sizing: border-box;
}

.question-row {
  min-height: 74px;
  margin: 0;
  border-top: 1px solid #edf1f3;
  border-radius: 0;
  color: #536176;
  background: #fff;
  text-align: left;
}

.question-workspace.compact .question-row {
  min-height: 82px;
}

.question-workspace.compact .table-stem {
  font-size: 13px;
  line-height: 1.45;
}

.question-workspace.compact .table-answer,
.question-workspace.compact .table-module,
.question-workspace.compact .date-cell,
.question-workspace.compact .difficulty-copy {
  font-size: 11px;
}

.question-workspace.compact .table-subject {
  font-size: 12px;
}

.check-box {
  width: 17px;
  height: 17px;
  margin: 0;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #cbd6dc;
  border-radius: 5px;
  color: #fff;
  background: #fff;
  font-size: 9px;
  line-height: 1;
}

.check-box.checked {
  border-color: #45bea3;
  background: #4fcdb1;
}

.mono {
  color: #718094;
  font-family: "SFMono-Regular", Consolas, monospace;
  font-size: 9px;
  letter-spacing: 0.03em;
}

.difficulty-cell {
  display: flex;
  align-items: center;
  gap: 7px;
}

.difficulty-dots {
  display: flex;
  gap: 2px;
}

.difficulty-dots text {
  width: 4px;
  height: 11px;
  border-radius: 2px;
  background: #e4e9ec;
}

.difficulty-dots text.active {
  background: #54cdb2;
}

.difficulty-copy {
  color: #7b8796;
  font-size: 10px;
}

.status-pill {
  padding: 5px 8px;
  display: inline-flex;
  border-radius: 10px;
  font-size: 10px;
  font-weight: 700;
}

.status-pill.published {
  color: #16816c;
  background: #dcf5ee;
}

.status-pill.pending {
  color: #b06e3f;
  background: #fff0e1;
}

.status-pill.archived {
  color: #69778a;
  background: #edf1f4;
}

.date-cell {
  color: #8793a2;
  font-size: 10px;
}

.question-date-sort-button {
  width: 100%;
  min-height: 41px;
  margin: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: flex-start;
  gap: 4px;
  border: 0;
  border-radius: 0;
  box-sizing: border-box;
  color: #718195;
  background: transparent;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  cursor: pointer;
}

.question-date-sort-button::after {
  border: 0;
}

.question-date-sort-button:hover,
.question-date-sort-button:focus-visible {
  color: #287f70;
}

.question-date-sort-button:focus-visible {
  outline: 2px solid rgba(79, 205, 177, 0.55);
  outline-offset: -3px;
}

.question-date-sort-icon {
  flex: 0 0 auto;
  color: #2a8a76;
  font-size: 8px;
  line-height: 1;
}

.row-action {
  width: 58px;
  height: 27px;
  margin: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #d7e4e1;
  border-radius: 7px;
  box-sizing: border-box;
  color: #2a8a76;
  background: #f5fbf9;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  text-align: center;
}

.home-content-add-button {
  width: 68px;
}

.home-content-add-button:disabled {
  border-color: #e2e8eb;
  color: #9aa7b2;
  background: #f4f6f7;
  opacity: 1;
}

.table-state.error {
  color: #b2605b;
}

.table-state button {
  width: auto;
  height: 30px;
  margin: 12px 0 0;
  padding: 0 11px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  box-sizing: border-box;
  color: #267c6a;
  background: #dff5ef;
  font-size: 9px;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
}

.pagination-row {
  min-height: 58px;
  padding: 0 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid #e8eef1;
  box-sizing: border-box;
}

.dashboard-pagination-row {
  justify-content: center;
}

.pagination-info,
.page-total {
  color: #929daa;
  font-size: 9px;
}

.pagination-actions {
  display: flex;
  align-items: center;
  gap: 7px;
}

.pagination-actions button {
  width: 29px;
  height: 29px;
  margin: 0;
  padding: 0;
  border: 1px solid #dce5e9;
  border-radius: 7px;
  color: #536277;
  background: #fff;
  font-size: 16px;
  line-height: 27px;
}

.pagination-actions button[disabled] {
  color: #c1c8cf;
  background: #f5f7f8;
}

.page-current {
  width: 29px;
  height: 29px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  color: #185a50;
  background: #dff5ef;
  font-size: 9px;
  font-weight: 800;
}

.import-hero-card {
  min-height: 305px;
  padding: 47px 56px;
  position: relative;
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  align-items: center;
  overflow: hidden;
  border-radius: 18px;
  background:
    radial-gradient(circle at 85% 18%, rgba(100, 224, 198, 0.22), transparent 26%),
    linear-gradient(145deg, #21384f, #2e4a63);
  color: #fff;
  box-sizing: border-box;
}

.import-eyebrow {
  color: #6ddcc4;
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.import-title {
  margin-top: 13px;
  font-size: 29px;
  font-weight: 700;
  letter-spacing: 0;
}

.import-copy {
  max-width: 590px;
  margin-top: 13px;
  color: rgba(255, 255, 255, 0.58);
  font-size: 11px;
  line-height: 1.75;
}

.import-visual {
  width: 220px;
  height: 220px;
  margin-left: auto;
  position: relative;
}

.import-orbit {
  position: absolute;
  inset: 15px;
  border: 1px dashed rgba(105, 222, 197, 0.28);
  border-radius: 50%;
}

.import-center {
  width: 72px;
  height: 72px;
  position: absolute;
  left: 74px;
  top: 74px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 23px;
  color: #194a43;
  background: linear-gradient(145deg, #80e4cf, #4dcdb0);
  box-shadow: 0 18px 42px rgba(43, 196, 163, 0.24);
  font-size: 28px;
}

.import-file {
  position: absolute;
  padding: 8px 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.66);
  background: rgba(255, 255, 255, 0.07);
  font-size: 8px;
  font-weight: 700;
}

.file-one { left: 5px; top: 50px; transform: rotate(-9deg); }
.file-two { right: 0; top: 40px; transform: rotate(8deg); }
.file-three { right: 18px; bottom: 35px; transform: rotate(-5deg); }

.import-flow {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.flow-card {
  min-height: 132px;
  padding: 18px;
  border: 1px solid #e0e8ec;
  border-radius: 13px;
  box-sizing: border-box;
  background: #fff;
}

.flow-index {
  color: #49bfa5;
  font-size: 9px;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.flow-title {
  margin-top: 14px;
  color: #334359;
  font-size: 12px;
  font-weight: 750;
}

.flow-copy {
  margin-top: 8px;
  color: #8c97a5;
  font-size: 9px;
  line-height: 1.65;
}

.import-safety {
  margin-top: 15px;
  padding: 16px 18px;
  display: flex;
  gap: 12px;
  border: 1px solid #cfe8e1;
  border-radius: 12px;
  background: #f3faf8;
}

.safety-icon {
  width: 25px;
  height: 25px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  color: #16816c;
  background: #d9f3ec;
  font-size: 11px;
  font-weight: 800;
}

.safety-title {
  color: #3b645b;
  font-size: 10px;
  font-weight: 750;
}

.safety-copy {
  margin-top: 5px;
  color: #759087;
  font-size: 9px;
  line-height: 1.55;
}

.bank-dialog-backdrop {
  position: fixed;
  z-index: 101;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 22px;
  box-sizing: border-box;
  background: rgba(20, 35, 52, 0.37);
  backdrop-filter: blur(3px);
}

.bank-dialog {
  width: min(400px, 100%);
  padding: 28px;
  border: 1px solid rgba(221, 233, 235, 0.9);
  border-radius: 16px;
  box-sizing: border-box;
  background: #fff;
  box-shadow: 0 22px 64px rgba(19, 35, 52, 0.2);
}

.publish-question-dialog {
  width: min(620px, 100%);
}

.publish-bank-grid {
  max-height: min(390px, 48vh);
  margin-top: 20px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  overflow-y: auto;
}

.publish-bank-option {
  min-height: 105px;
  margin: 0;
  padding: 17px;
  position: relative;
  display: flex;
  align-items: center;
  gap: 14px;
  border: 1px solid #dfe8eb;
  border-radius: 13px;
  text-align: left;
  background: #fbfcfc;
  transition: border-color 0.18s ease, background 0.18s ease, box-shadow 0.18s ease;
}

.publish-bank-option:hover,
.publish-bank-option.selected {
  border-color: #69cfb8;
  background: #f3fbf8;
  box-shadow: 0 8px 22px rgba(52, 135, 118, 0.1);
}

.publish-bank-folder {
  width: 48px;
  height: 43px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border: 1px solid #8bd9c8;
  border-radius: 8px 8px 10px 10px;
  color: #248f7b;
  background: linear-gradient(145deg, #ddf8f1, #bcecdf);
  font-size: 15px;
  font-weight: 800;
}

.publish-bank-folder-tab {
  width: 22px;
  height: 8px;
  position: absolute;
  top: -6px;
  left: 5px;
  border-radius: 6px 6px 0 0;
  background: #a5e5d6;
}

.publish-bank-meta {
  min-width: 0;
  flex: 1;
}

.publish-bank-name {
  overflow: hidden;
  color: #27374c;
  font-size: 13px;
  font-weight: 760;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.publish-bank-date {
  margin-top: 8px;
  color: #93a0ad;
  font-size: 9px;
  line-height: 1.4;
}

.publish-bank-check {
  width: 22px;
  height: 22px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 auto;
  border: 1px solid #d8e3e6;
  border-radius: 50%;
  color: #fff;
  background: #fff;
  font-size: 12px;
  font-weight: 800;
}

.publish-bank-option.selected .publish-bank-check {
  border-color: #53c6ad;
  background: #53c6ad;
}

.publish-bank-state {
  min-height: 150px;
  margin-top: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-direction: column;
  gap: 12px;
  border: 1px dashed #d9e5e7;
  border-radius: 13px;
  color: #8493a2;
  background: #fbfcfc;
  font-size: 10px;
}

.publish-bank-state.error {
  color: #b2605b;
}

.publish-preview {
  min-height: 42px;
  margin-top: 14px;
  padding: 11px 13px;
  display: flex;
  align-items: center;
  gap: 8px;
  border: 1px solid #cde8e1;
  border-radius: 8px;
  box-sizing: border-box;
  color: #3d7168;
  background: #f2fbf8;
  font-size: 10px;
  line-height: 1.5;
}

.publish-preview.error {
  border-color: #f0d1cf;
  color: #a65e5a;
  background: #fff7f6;
}

.publish-preview-count {
  margin: 0 2px;
  color: #167765;
  font-size: 14px;
  font-weight: 800;
}

.publish-preview-retry {
  min-width: auto;
  height: 24px;
  margin: 0 0 0 auto;
  padding: 0 8px;
  border: 1px solid currentColor;
  border-radius: 5px;
  color: inherit;
  background: transparent;
  font-size: 9px;
}

.bank-dialog-kicker {
  color: #4ba993;
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 0.14em;
}

.bank-dialog-title {
  margin-top: 8px;
  color: #28374b;
  font-size: 18px;
  font-weight: 760;
}

.bank-dialog-copy {
  margin-top: 8px;
  color: #8491a0;
  font-size: 10px;
  line-height: 1.65;
}

.bank-dialog-input {
  width: 100%;
  height: 40px;
  margin-top: 20px;
  padding: 0 12px;
  border: 1px solid #d9e4e8;
  border-radius: 9px;
  box-sizing: border-box;
  color: #304057;
  background: #fbfcfc;
  font-size: 12px;
}

.bank-dialog-input:focus {
  border-color: #6acbb6;
  background: #fff;
}

.bank-dialog-actions {
  margin-top: 22px;
  display: flex;
  justify-content: flex-end;
  gap: 9px;
}

.bank-dialog-cancel,
.bank-dialog-confirm {
  min-width: 76px;
  height: 36px;
  margin: 0;
  padding: 0 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  box-sizing: border-box;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
}

.bank-dialog-cancel {
  border: 1px solid #dce5e9;
  color: #718095;
  background: #fff;
}

.bank-dialog-confirm {
  color: #153f3a;
  background: linear-gradient(135deg, #69ddc4, #4ccaae);
}

.bank-dialog-confirm[disabled],
.bank-dialog-cancel[disabled] {
  opacity: 0.58;
}

@media (max-width: 680px) {
  .publish-bank-grid {
    grid-template-columns: 1fr;
  }
}

.drawer-backdrop {
  position: fixed;
  z-index: 100;
  inset: 0;
  display: flex;
  justify-content: flex-end;
  background: rgba(18, 31, 45, 0.42);
  backdrop-filter: blur(2px);
}

.drawer-backdrop.review-modal-backdrop {
  padding: 40px;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.question-drawer {
  width: min(630px, calc(100vw - 90px));
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8fafb;
  box-shadow: -20px 0 50px rgba(22, 37, 53, 0.15);
}

.question-drawer.review-modal {
  width: min(920px, calc(100vw - 120px));
  height: min(820px, calc(100vh - 80px));
  overflow: hidden;
  border: 1px solid rgba(216, 229, 232, 0.95);
  border-radius: 18px;
  box-shadow: 0 28px 80px rgba(20, 36, 52, 0.24);
}

.question-drawer.review-modal .drawer-content {
  padding: 24px 28px 36px;
}

.drawer-header {
  height: 81px;
  padding: 0 25px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #e0e8ec;
  box-sizing: border-box;
  background: #fff;
}

.drawer-kicker {
  color: #43b79e;
  font-size: 8px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.drawer-title {
  margin-top: 5px;
  color: #26364a;
  font-size: 18px;
  font-weight: 750;
}

.drawer-close {
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  margin: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  border: 0;
  border-radius: 50%;
  color: #768695;
  background: #f2f5f7;
  font-size: 20px;
  line-height: 1;
  text-align: center;
}

:deep(.admin-modal-close) {
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  margin: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  border: 0;
  border-radius: 50%;
  color: #768695;
  background: #f2f5f7;
  font-size: 20px;
  line-height: 1;
  text-align: center;
}

:deep(.admin-modal-close text) {
  line-height: 1;
}

:deep(.admin-modal-close::after) {
  border: 0;
}

.drawer-scroll {
  min-height: 0;
  flex: 1;
}

.drawer-content {
  padding: 22px 25px 34px;
}

.drawer-meta-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 13px;
}

.drawer-meta-grid + .drawer-meta-grid,
.form-field.full {
  margin-top: 18px;
}

.form-label {
  color: #556479;
  font-size: 10px;
  font-weight: 700;
}

.form-admin-select {
  margin-top: 8px;
  --admin-select-height: 38px;
  --admin-select-font-size: 11px;
  --admin-select-menu-min-width: 100%;
}

.difficulty-picker {
  height: 38px;
  margin-top: 8px;
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  overflow: hidden;
  border: 1px solid #dbe4e8;
  border-radius: 8px;
  background: #fff;
}

.difficulty-picker button {
  height: 36px;
  margin: 0;
  padding: 0;
  border-radius: 0;
  color: #7b8796;
  background: #fff;
  font-size: 9px;
  line-height: 36px;
}

.difficulty-picker button + button {
  border-left: 1px solid #e7ecef;
}

.difficulty-picker button.active {
  color: #176b5d;
  background: #dff5ef;
  font-weight: 800;
}

.form-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.required-tag,
.form-hint {
  color: #9aa4b0;
  font-size: 8px;
}

.required-tag {
  padding: 3px 6px;
  border-radius: 5px;
  color: #b26358;
  background: #fbe9e6;
}

.form-textarea {
  width: 100%;
  margin-top: 8px;
  padding: 12px;
  border: 1px solid #dbe4e8;
  border-radius: 9px;
  box-sizing: border-box;
  color: #334359;
  background: #fff;
  font-size: 10px;
  line-height: 1.65;
}

.form-textarea:focus {
  border-color: #62cbb4;
}

.form-textarea.stem { min-height: 105px; }
.form-textarea.explanation { min-height: 120px; }
.form-textarea.note { min-height: 76px; }

.question-drawer.review-modal .form-label {
  font-size: 12px;
}

.question-drawer.review-modal .form-admin-select {
  --admin-select-height: 42px;
  --admin-select-font-size: 13px;
}

.question-drawer.review-modal .difficulty-picker {
  height: 42px;
}

.question-drawer.review-modal .difficulty-picker button {
  height: 40px;
  font-size: 12px;
  line-height: 40px;
}

.question-drawer.review-modal .required-tag,
.question-drawer.review-modal .form-hint {
  font-size: 10px;
}

.question-drawer.review-modal .form-textarea {
  padding: 15px 16px;
  border-radius: 10px;
  font-size: 14px;
  line-height: 1.75;
}

.question-drawer.review-modal .form-textarea.stem { min-height: 140px; }
.question-drawer.review-modal .form-textarea.explanation { min-height: 150px; }
.question-drawer.review-modal .form-textarea.note { min-height: 92px; }

.drawer-math-preview {
  margin-bottom: 18px;
}

.option-editor {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.option-row {
  min-height: 43px;
  padding: 5px 9px 5px 5px;
  display: flex;
  align-items: center;
  gap: 9px;
  border: 1px solid #dfe6ea;
  border-radius: 9px;
  box-sizing: border-box;
  background: #fff;
}

.option-row.correct {
  border-color: #6dd3bd;
  background: #f2fbf8;
}

.answer-selector {
  width: 32px;
  height: 32px;
  margin: 0;
  padding: 0;
  border-radius: 7px;
  color: #69778a;
  background: #edf1f3;
  font-size: 10px;
  font-weight: 800;
  line-height: 32px;
}

.option-row.correct .answer-selector {
  color: #176b5d;
  background: #d6f2eb;
}

.option-input {
  min-width: 0;
  height: 32px;
  flex: 1;
  color: #3f4f64;
  font-size: 10px;
}

.question-drawer.review-modal .option-editor {
  gap: 10px;
}

.question-drawer.review-modal .option-row {
  min-height: 52px;
  padding: 8px 13px 8px 8px;
  border-radius: 10px;
}

.question-drawer.review-modal .answer-selector {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 36px;
}

.question-drawer.review-modal .option-input {
  height: 36px;
  font-size: 14px;
  line-height: 1.5;
}

.review-note-field {
  padding: 15px;
  border: 1px solid #f0ddc8;
  border-radius: 10px;
  background: #fffaf4;
}

.question-meta-note {
  margin-top: 20px;
  padding: 12px 0;
  display: flex;
  justify-content: space-between;
  border-top: 1px dashed #dce4e8;
  color: #9aa4b0;
  font-family: Consolas, monospace;
  font-size: 8px;
}

.drawer-footer {
  min-height: 74px;
  padding: 14px 24px 16px;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 10px;
  border-top: 1px solid #dfe7eb;
  box-sizing: border-box;
  background: #fff;
}

.footer-button {
  width: 94px;
  height: 40px;
  margin: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  box-sizing: border-box;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  text-align: center;
  white-space: nowrap;
}

.footer-button.primary {
  color: #17423c;
  background: #59d2b7;
}

.footer-button.secondary {
  border: 1px solid #d8e2e7;
  color: #617087;
  background: #fff;
}

.footer-button.select {
  border: 1px solid #cfe5df;
  color: #3d7c70;
  background: #f7fbfa;
}

.footer-button.select.active {
  border-color: #73d8c1;
  color: #155e52;
  background: #dcf6ef;
}

.footer-button.warning {
  color: #a86639;
  background: #fff0df;
}

.footer-button.danger {
  border: 1px solid #f0c7c3;
  color: #a95650;
  background: #fae4e2;
}

.footer-button[disabled] {
  opacity: 0.58;
}

.page-state {
  min-height: calc(100vh - 86px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #7e8b9c;
}

.state-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #d8e4e5;
  border-top-color: #4fcbb0;
  border-radius: 50%;
  animation: spin 0.9s linear infinite;
}

.state-title {
  margin-top: 16px;
  color: #45566b;
  font-size: 13px;
  font-weight: 700;
}

.state-copy {
  margin-top: 6px;
  color: #929daa;
  font-size: 9px;
}

.portal-access-error .state-title {
  color: #9d665d;
}

.portal-retry-button {
  min-width: 84px;
  height: 32px;
  margin-top: 18px;
  font-size: 10px;
}

.operations-section {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.home-operations-content-section {
  padding-bottom: 8px;
}

.home-status-section {
  padding-top: 10px;
}

.operations-summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 14px;
}

.operations-summary-card {
  box-sizing: border-box;
  min-height: 112px;
  padding: 17px 18px;
  border: 1px solid #e2eaee;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 12px 26px rgba(33, 54, 74, 0.04);
}

.operations-summary-card.mint {
  border-color: #ccece4;
}

.operations-summary-card.blue {
  border-color: #d9e8f6;
}

.membership-management-summary {
  cursor: pointer;
  transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
}

.membership-management-summary:hover {
  border-color: #98bde5;
  box-shadow: 0 16px 30px rgba(49, 92, 133, 0.11);
  transform: translateY(-2px);
}

.membership-management-summary:active {
  transform: translateY(0);
}

.operations-summary-card.slate {
  border-color: #e3e8ee;
}

.operations-summary-label,
.operations-summary-note {
  color: #8a99aa;
  font-size: 11px;
}

.operations-summary-value {
  margin: 8px 0 6px;
  color: #1e3047;
  font-size: 28px;
  font-weight: 800;
  line-height: 1;
}

.user-workspace,
.scoreline-record-workspace,
.announcement-record-workspace,
.major-catalog-workspace,
.home-content-editor-modal,
.home-content-column,
.home-live-preview-workspace {
  border: 1px solid #e2eaee;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 12px 26px rgba(33, 54, 74, 0.04);
}

.user-filter-toolbar {
  display: grid;
  grid-template-columns: minmax(220px, 1.55fr) repeat(5, minmax(112px, 1fr));
  align-items: center;
  gap: 9px;
}

.user-search-shell {
  width: 100%;
  min-width: 0;
}

.user-filter-toolbar .question-admin-select {
  width: 100%;
  min-width: 0;
}

.operations-inline-alert {
  display: flex;
  min-height: 54px;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 10px 14px;
  border: 1px solid #f0d6ac;
  border-radius: 7px;
  color: #876b43;
  background: #fffaf1;
}

.operations-inline-alert strong,
.operations-inline-alert text {
  display: block;
}

.operations-inline-alert strong {
  color: #6b5130;
  font-size: 11px;
}

.operations-inline-alert text {
  margin-top: 4px;
  font-size: 10px;
}

.operations-inline-alert button {
  flex: 0 0 auto;
  min-width: 76px;
  height: 30px;
  border: 1px solid #e4c58f;
  border-radius: 6px;
  color: #7d613b;
  font-size: 10px;
  background: #ffffff;
}

.portal-user-table,
.scoreline-record-table,
.announcement-record-table,
.major-catalog-record-table {
  min-width: 100%;
}

.portal-user-grid {
  box-sizing: border-box;
  display: grid;
  grid-template-columns: minmax(190px, 1.45fr) 52px 72px 64px 80px 80px 82px 64px 112px;
  min-width: 900px;
  align-items: center;
  gap: 8px;
}

.portal-user-grid.table-head,
.scoreline-record-grid.table-head,
.announcement-record-grid.table-head,
.major-catalog-record-grid.table-head {
  box-sizing: border-box;
  min-height: 42px;
  padding: 0 16px;
  color: #8595a7;
  font-size: 10px;
  font-weight: 700;
  background: #f8fafb;
}

.portal-user-sort-header {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  min-width: 0;
  cursor: pointer;
  user-select: none;
}

.portal-user-sort-header.active {
  color: #34799f;
}

.portal-user-sort-icon {
  flex: 0 0 auto;
  color: #34799f;
  font-size: 8px;
  line-height: 1;
}

.portal-user-row {
  min-height: 64px;
  padding: 7px 16px;
  border-top: 1px solid #edf1f3;
  color: #536478;
  font-size: 11px;
  cursor: pointer;
}

.portal-user-row > view {
  min-width: 0;
}

.portal-user-row:hover,
.scoreline-record-row:hover,
.announcement-record-row:hover,
.major-catalog-record-row:hover {
  background: #f8fcfb;
}

.portal-user-identity {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
}

.portal-user-avatar {
  display: grid;
  width: 30px;
  height: 30px;
  flex: 0 0 30px;
  place-items: center;
  border: 1px solid #cfe9e4;
  border-radius: 8px;
  color: #178f7c;
  font-size: 12px;
  font-weight: 800;
  background: #eaf8f5;
}

.portal-user-avatar.large {
  width: 46px;
  height: 46px;
  flex-basis: 46px;
  font-size: 18px;
}

.portal-user-name,
.portal-user-profile-name {
  overflow: hidden;
  color: #263a51;
  font-size: 12px;
  font-weight: 700;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.portal-user-contact,
.portal-user-profile-contact,
.portal-user-profile-meta {
  overflow: hidden;
  margin-top: 3px;
  color: #98a6b5;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.portal-accuracy.critical,
.portal-subject-accuracy-value.critical {
  color: #db7466;
}

.portal-accuracy.warning,
.portal-subject-accuracy-value.warning {
  color: #d89b4c;
}

.portal-accuracy.normal,
.portal-subject-accuracy-value.normal {
  color: #28a58c;
}

.portal-user-actions,
.announcement-record-actions {
  display: flex;
  align-items: center;
  gap: 5px;
}

.portal-user-actions button {
  min-width: 48px;
  padding-right: 8px;
  padding-left: 8px;
}

.portal-membership-button {
  min-width: 58px !important;
  height: 25px;
  margin: 0;
  padding: 0 7px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #b6d7ef;
  border-radius: 6px;
  box-sizing: border-box;
  color: #34799f;
  font-size: 9px;
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
  background: #f1f8fc;
}

.portal-membership-button[disabled] {
  border-color: #e1e8eb;
  color: #a3afb9;
  background: #f6f8f9;
}

.operations-heading-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
}

.operations-page-title {
  margin-top: 5px;
  color: #20334a;
  font-size: 26px;
  font-weight: 800;
  line-height: 1.1;
}

.operations-page-copy {
  margin-top: 9px;
  color: #8394a8;
  font-size: 12px;
}

.operations-status-chip {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 9px 13px;
  border: 1px solid #dce8e8;
  border-radius: 999px;
  color: #548073;
  font-size: 11px;
  background: #fbfdfd;
}

.operations-tab-strip {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.operations-tab {
  display: flex;
  min-height: 70px;
  border: 1px solid #dfe8ec;
  border-radius: 8px;
  box-sizing: border-box;
  color: #607388;
  background: #ffffff;
}

.operations-tab-copy {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  justify-content: center;
  padding: 13px 8px 13px 16px;
  line-height: 1.3;
  text-align: left;
  cursor: pointer;
}

.operations-tab-copy text {
  display: block;
  color: inherit;
  font-size: 13px;
  font-weight: 700;
}

.operations-tab-copy small {
  display: block;
  margin-top: 7px;
  color: #9aa9b8;
  font-size: 10px;
}

.operations-tab.active {
  border-color: #72ceb9;
  color: #177f70;
  background: #edfaf7;
  box-shadow: inset 0 0 0 1px rgba(79, 203, 176, 0.12);
}

.operations-tab.active .operations-tab-copy small {
  color: #5c968a;
}

.admission-card-import-button {
  width: 82px;
  height: 32px;
  flex: 0 0 82px;
  align-self: center;
  margin: 0 13px 0 8px;
  padding: 0;
  border: 1px solid #b9ddd5;
  border-radius: 6px;
  color: #287d70;
  font-size: 10px;
  font-weight: 700;
  line-height: 30px;
  background: #f6fcfa;
}

.operations-tab.active .admission-card-import-button {
  border-color: #7bcfbd;
  color: #176f62;
  background: #ffffff;
}

.admission-import-backdrop {
  z-index: 108;
  padding: 36px;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.admission-import-modal {
  display: flex;
  width: min(760px, calc(100vw - 72px));
  max-height: min(680px, calc(100vh - 72px));
  flex-direction: column;
  overflow: hidden;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 22px 60px rgba(27, 43, 60, 0.2);
}

.admission-import-scroll {
  min-height: 0;
  flex: 1;
}

.admission-import-content {
  padding: 22px 24px 28px;
}

.scoreline-editor-backdrop {
  z-index: 109;
  padding: 36px;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.scoreline-editor-modal {
  display: flex;
  width: min(760px, calc(100vw - 72px));
  max-height: min(720px, calc(100vh - 72px));
  flex-direction: column;
  overflow: hidden;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 22px 60px rgba(27, 43, 60, 0.2);
}

.announcement-editor-modal,
.major-catalog-editor-modal {
  height: min(720px, calc(100vh - 72px));
}

.scoreline-editor-scroll {
  min-height: 0;
  flex: 1;
}

.scoreline-editor-content {
  padding: 22px 24px 28px;
}

.scoreline-editor-grid,
.announcement-editor-grid,
.major-catalog-editor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.scoreline-editor-grid .form-label,
.announcement-editor-grid .form-label,
.major-catalog-editor-grid .form-label {
  color: #64778b;
  font-size: 11px;
}

.announcement-editor-grid .form-field.full {
  grid-column: 1 / -1;
}

.scoreline-editor-grid .form-input,
.announcement-editor-grid .form-input,
.announcement-editor-grid .form-textarea,
.major-catalog-editor-grid .form-input {
  width: 100%;
  height: 38px;
  margin-top: 8px;
  padding: 0 11px;
  border: 1px dashed #9fcfc4;
  border-radius: 7px;
  box-sizing: border-box;
  color: #40566d;
  font-size: 12px;
  background: #fbfefd;
}

.announcement-editor-grid .form-textarea {
  min-height: 78px;
  padding-top: 10px;
  padding-bottom: 10px;
  line-height: 1.5;
  resize: vertical;
}

.announcement-editor-grid .announcement-content-textarea {
  min-height: 148px;
}

.scoreline-editor-grid .form-input:focus,
.announcement-editor-grid .form-input:focus,
.announcement-editor-grid .form-textarea:focus,
.major-catalog-editor-grid .form-input:focus {
  border-color: #58bba5;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(80, 208, 180, 0.09);
}

.admission-import-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.admission-template-button {
  margin-left: auto;
  flex: 0 0 auto;
}

.admission-import-actions .secondary-button,
.admission-import-actions .primary-button {
  width: 72px;
  min-width: 72px;
  max-width: 72px;
  height: 35px;
  min-height: 35px;
  max-height: 35px;
  margin: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 72px;
  box-sizing: border-box;
  line-height: 1;
}

.admission-file-picker {
  display: flex;
  min-width: 290px;
  height: 38px;
}

.admission-file-input {
  display: none;
}

.admission-file-picker-trigger {
  width: 100%;
  height: 100%;
  margin: 0;
  padding: 0 13px;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  border: 1px dashed #aaccc6;
  border-radius: 7px;
  box-sizing: border-box;
  color: #5d7288;
  font-size: 11px;
  line-height: 1;
  text-align: left;
  background: #fbfefd;
  cursor: pointer;
}

.admission-file-picker-trigger::after {
  border: 0;
}

.admission-file-picker-trigger text {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.admission-preview-summary {
  display: flex;
  align-items: center;
  gap: 24px;
  margin: 18px 0 0;
  padding: 12px 14px;
  border: 1px solid #ccebe3;
  border-radius: 7px;
  color: #588277;
  font-size: 11px;
  background: #f4fcfa;
}

.admission-preview-summary.error {
  border-color: #f1c6bd;
  color: #b36c5f;
  background: #fff8f6;
}

.admission-preview-summary strong {
  margin-right: 4px;
  color: #24374e;
  font-size: 17px;
}

.admission-preview-list {
  margin: 14px 0 0;
  border: 1px solid #e6ecee;
  border-radius: 7px;
  overflow: hidden;
}

.admission-preview-row {
  display: grid;
  grid-template-columns: 85px minmax(0, 1fr) minmax(160px, 1.2fr);
  gap: 12px;
  min-height: 32px;
  align-items: center;
  padding: 0 12px;
  border-top: 1px solid #edf1f3;
  color: #6a7c90;
  font-size: 10px;
}

.admission-preview-row:first-child {
  border-top: 0;
}

.admission-preview-row.invalid {
  color: #c76b5c;
  background: #fff9f7;
}

.row-unavailable-copy {
  color: #a3adb8;
  font-size: 10px;
}

.scoreline-record-row strong,
.announcement-record-row strong,
.major-catalog-record-row strong {
  display: block;
  overflow: hidden;
  color: #33475e;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.scoreline-record-row text,
.announcement-record-row text,
.major-catalog-record-row text {
  display: block;
  margin-top: 4px;
  color: #98a7b7;
  font-size: 9px;
}

.scoreline-record-grid {
  display: grid;
  grid-template-columns: 58px 74px minmax(180px, 1.15fr) minmax(130px, 0.9fr) minmax(180px, 1.2fr) 124px 64px;
  min-width: 1040px;
  align-items: center;
  gap: 12px;
}

.scoreline-record-row {
  box-sizing: border-box;
  min-height: 64px;
  padding: 8px 18px;
  border-top: 1px solid #edf1f3;
  color: #64768b;
  font-size: 11px;
}

.scoreline-record-row > view {
  min-width: 0;
}

.scoreline-year-cell {
  color: #3e5872;
  font-weight: 700;
}

.scoreline-record-row .scoreline-value {
  color: #1e6f63;
  font-size: 13px;
}

.scoreline-record-row .scoreline-kind {
  margin-top: 3px;
  color: #8d9eaf;
}

.scoreline-record-row .scoreline-kind.is-score {
  color: #28967f;
}

.scoreline-record-row .scoreline-kind.is-multiple,
.scoreline-record-row .scoreline-kind.is-note {
  color: #9b7a52;
}

.scoreline-record-row .scoreline-kind.is-missing,
.scoreline-record-row .scoreline-kind.is-unavailable {
  color: #a7afb8;
}

.scoreline-source-cell strong {
  max-width: 100%;
}

.scoreline-source-cell small {
  display: block;
  margin-top: 3px;
  color: #4c9b8b;
  font-size: 9px;
}

.scoreline-workspace-heading {
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.scoreline-workspace-heading > view:first-child {
  min-width: 240px;
  flex: 1;
}

.scoreline-heading-tools {
  display: flex;
  align-items: center;
  gap: 10px;
}

.scoreline-heading-tools > text {
  color: #8d9bab;
  font-size: 10px;
  white-space: nowrap;
}

.scoreline-filter-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 20px 14px;
}

.scoreline-filter-input {
  height: 34px;
  padding: 0 10px;
  border: 1px solid #dce6e9;
  border-radius: 6px;
  box-sizing: border-box;
  color: #40566d;
  font-size: 10px;
  background: #ffffff;
}

.scoreline-filter-input:focus {
  border-color: #71cbb9;
}

.scoreline-filter-search {
  width: 360px;
  min-width: 220px;
  flex: 0 1 360px;
}

.scoreline-filter-select {
  width: 116px;
  flex: 0 0 116px;
  --admin-select-height: 34px;
  --admin-select-radius: 6px;
  --admin-select-font-size: 10px;
  --admin-select-padding-x: 10px;
  --admin-select-menu-min-width: 132px;
}

.scoreline-filter-region-select {
  width: 132px;
  flex-basis: 132px;
}

.major-catalog-school-select {
  width: 180px;
  flex-basis: 180px;
  --admin-select-menu-min-width: 220px;
}

.scoreline-filter-apply {
  width: 54px;
  height: 34px;
  margin: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 54px;
  border: 1px solid #b9ded5;
  border-radius: 6px;
  box-sizing: border-box;
  color: #287d6d;
  font-size: 10px;
  font-weight: 700;
  line-height: 1;
  background: #f3fbf8;
}

.scoreline-filter-clear {
  width: 30px;
  height: 30px;
  margin: 0;
  padding: 0;
  flex: 0 0 30px;
  border-radius: 6px;
  color: #7f90a2;
  font-size: 15px;
  line-height: 28px;
  background: #f2f6f7;
}

.scoreline-pagination {
  margin: 0 20px 14px;
}

.announcement-record-grid {
  display: grid;
  grid-template-columns: minmax(250px, 1.6fr) minmax(140px, 180px) 90px 90px 74px 140px;
  min-width: 860px;
  align-items: center;
  gap: 12px;
}

.announcement-record-row {
  box-sizing: border-box;
  min-height: 64px;
  padding: 8px 18px;
  border-top: 1px solid #edf1f3;
  color: #64768b;
  font-size: 11px;
}

.major-catalog-record-grid {
  display: grid;
  grid-template-columns: 72px minmax(180px, 1.05fr) minmax(230px, 1.4fr) 78px minmax(120px, 0.8fr) 64px;
  min-width: 900px;
  align-items: center;
  gap: 12px;
}

.major-catalog-record-row {
  box-sizing: border-box;
  min-height: 64px;
  padding: 8px 18px;
  border-top: 1px solid #edf1f3;
  color: #64768b;
  font-size: 11px;
}

.major-catalog-record-row > view {
  min-width: 0;
}

.exam-code-cell {
  min-width: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.exam-code-pill {
  display: inline-flex;
  min-width: 42px;
  height: 22px;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  text-align: center;
  border-radius: 6px;
  font-size: 9px;
  font-weight: 800;
  line-height: 1;
}

.exam-code-cell .exam-code-pill {
  display: inline-flex;
  margin-top: 0;
}

.exam-code-pill.is-z001 {
  color: #257568;
  background: #e4f7f1;
}

.exam-code-pill.is-z002 {
  color: #55789e;
  background: #eaf2fa;
}

.announcement-status-cell {
  display: flex;
  align-items: center;
  justify-content: center;
}

.announcement-status-cell .status-pill {
  margin-top: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.announcement-workspace-heading,
.major-catalog-workspace-heading {
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.announcement-workspace-heading > view:first-child,
.major-catalog-workspace-heading > view:first-child {
  min-width: 240px;
  flex: 1;
}

.announcement-heading-tools,
.major-catalog-heading-tools {
  display: flex;
  align-items: center;
  gap: 10px;
}

.announcement-heading-tools > text,
.major-catalog-heading-tools > text {
  color: #8d9bab;
  font-size: 10px;
  white-space: nowrap;
}

.announcement-heading-tools .question-admin-select {
  min-width: 150px;
}

.major-catalog-guard {
  display: flex;
  align-items: center;
  gap: 15px;
  margin: 0 20px 20px;
  padding: 18px;
  border: 1px solid #d9ebe9;
  border-radius: 7px;
  background: #f8fcfc;
}

.major-catalog-guard-mark {
  display: grid;
  width: 42px;
  height: 42px;
  flex: 0 0 42px;
  place-items: center;
  border-radius: 8px;
  color: #238f7e;
  font-size: 17px;
  font-weight: 800;
  background: #dff6f0;
}

.major-catalog-guard-title {
  color: #345168;
  font-size: 13px;
  font-weight: 700;
}

.major-catalog-guard-copy {
  margin-top: 6px;
  color: #8293a6;
  font-size: 11px;
  line-height: 1.6;
}

.home-content-editor-backdrop {
  z-index: 110;
  padding: 36px;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.home-content-editor-modal {
  width: min(860px, calc(100vw - 72px));
  height: min(720px, calc(100vh - 72px));
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 10px;
}

.home-editor-modal-heading {
  flex: 0 0 auto;
}

.home-editor-scroll {
  min-height: 0;
  flex: 1;
}

.home-editor-content {
  padding: 22px 24px 26px;
}

.home-editor-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.home-editor-grid .form-field.full {
  grid-column: span 2;
  margin-top: 0;
}

.home-editor-grid .form-label {
  color: #64778b;
  font-size: 11px;
}

.home-editor-grid .form-input,
.home-editor-grid .form-textarea {
  width: 100%;
  height: 38px;
  margin-top: 8px;
  padding: 0 11px;
  border: 1px dashed #9fcfc4;
  border-radius: 7px;
  box-sizing: border-box;
  color: #40566d;
  font-size: 12px;
  background: #fbfefd;
}

.home-editor-grid .form-textarea {
  min-height: 88px;
  padding-top: 10px;
  padding-bottom: 10px;
  line-height: 1.5;
  resize: vertical;
}

.home-editor-grid .form-input:focus,
.home-editor-grid .form-textarea:focus {
  border-color: #58bba5;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(80, 208, 180, 0.09);
}

.home-editor-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 14px 24px;
  flex: 0 0 auto;
  border-top: 1px solid #e8eef1;
  background: #ffffff;
}

.home-editor-sample {
  display: grid;
  min-height: 82px;
  align-content: center;
  gap: 5px;
  margin: 16px 0 0;
  padding: 14px 16px;
  border-left: 3px solid #6a9fd0;
  color: #38536e;
  background: #eef6ff;
}

.home-editor-sample.is-mint {
  border-color: #55bda6;
  color: #31685d;
  background: #edf9f6;
}

.home-editor-sample.is-orange {
  border-color: #e1a45f;
  color: #765735;
  background: #fff7eb;
}

.home-editor-sample.is-violet {
  border-color: #8c7bc4;
  color: #5f5483;
  background: #f5f2ff;
}

.home-editor-sample small {
  font-size: 9px;
  opacity: 0.72;
}

.home-editor-sample strong {
  font-size: 13px;
}

.home-editor-sample text {
  overflow: hidden;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-content-columns {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.home-live-preview-workspace {
  overflow: hidden;
}

.home-preview-counts {
  display: flex;
  gap: 8px;
}

.home-preview-counts text {
  padding: 5px 8px;
  border-radius: 5px;
  color: #547267;
  font-size: 9px;
  background: #edf8f5;
}

.home-user-preview-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.15fr) minmax(0, 0.85fr);
  border-top: 1px solid #edf1f3;
}

.home-user-preview-panel {
  min-width: 0;
  padding: 16px 18px 18px;
}

.home-user-preview-panel + .home-user-preview-panel {
  border-left: 1px solid #edf1f3;
}

.home-user-preview-label {
  margin-bottom: 10px;
  color: #7d8fa2;
  font-size: 10px;
  font-weight: 700;
}

.home-preview-focus-list,
.home-preview-news-list {
  display: grid;
  gap: 8px;
}

.home-preview-focus-list {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}

.home-preview-focus-item {
  display: grid;
  min-width: 0;
  min-height: 96px;
  align-content: center;
  gap: 6px;
  padding: 12px;
  border-top: 3px solid #6097ca;
  color: #34536e;
  background: #eef6ff;
}

.home-preview-focus-item.is-mint {
  border-color: #51b89f;
  color: #2f685b;
  background: #edf9f6;
}

.home-preview-focus-item.is-orange {
  border-color: #dfa05b;
  color: #725536;
  background: #fff6e9;
}

.home-preview-focus-item.is-violet {
  border-color: #8975bd;
  color: #5d5180;
  background: #f4f1ff;
}

.home-preview-focus-item text,
.home-preview-focus-item small {
  overflow: hidden;
  font-size: 9px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-preview-focus-item strong {
  display: -webkit-box;
  overflow: hidden;
  font-size: 11px;
  line-height: 1.45;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.home-preview-news-item {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  border-top: 1px solid #edf1f3;
}

.home-preview-news-item:first-child {
  border-top: 0;
}

.home-preview-news-item > view:last-child {
  min-width: 0;
  flex: 1;
}

.home-preview-news-item strong,
.home-preview-news-item text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-preview-news-item strong {
  color: #3b5269;
  font-size: 10px;
}

.home-preview-news-item text {
  margin-top: 5px;
  color: #96a5b4;
  font-size: 9px;
}

.home-preview-empty {
  min-height: 96px;
  display: grid;
  place-items: center;
  border: 1px dashed #d9e4e7;
  color: #9aa8b6;
  font-size: 10px;
}

.home-status-workspace {
  overflow: hidden;
}

.home-status-list {
  border-top: 1px solid #edf1f3;
}

.home-status-row {
  display: flex;
  min-height: 52px;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 0 20px;
  border-top: 1px solid #edf1f3;
}

.home-status-row:first-child {
  border-top: 0;
}

.home-status-row > view:first-child {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  min-width: 0;
  align-items: center;
  column-gap: 10px;
  row-gap: 3px;
}

.home-status-row strong {
  overflow: hidden;
  color: #3d5268;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-status-row small {
  grid-column: 2;
  color: #98a6b5;
  font-size: 9px;
}

.home-status-slot {
  flex: 0 0 auto;
  color: #8092a5;
  font-size: 10px;
}

.home-status-actions {
  display: flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 8px;
}

.home-content-row {
  display: flex;
  min-height: 64px;
  align-items: center;
  gap: 10px;
  padding: 9px 18px;
  border-top: 1px solid #edf1f3;
}

.home-content-chip {
  display: grid;
  width: 48px;
  min-height: 40px;
  flex: 0 0 48px;
  place-items: center;
  padding: 0 4px;
  border-radius: 7px;
  color: #3566a7;
  font-size: 9px;
  text-align: center;
  background: #e9f2ff;
}

.home-content-chip.is-mint {
  color: #247f6f;
  background: #dff5ef;
}

.home-content-chip.is-orange {
  color: #b27438;
  background: #fff0d8;
}

.home-content-chip.is-violet {
  color: #7561b6;
  background: #ede8ff;
}

.home-content-copy {
  min-width: 0;
  flex: 1;
}

.home-content-copy strong,
.home-content-copy text {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-content-copy strong {
  color: #33475e;
  font-size: 11px;
}

.home-content-copy text {
  margin-top: 5px;
  color: #99a8b7;
  font-size: 9px;
}

.portal-user-detail-modal {
  display: flex;
  width: min(720px, calc(100vw - 48px));
  height: 100vh;
  max-height: none;
  flex-direction: column;
  overflow: hidden;
  border-radius: 0;
  background: #ffffff;
  box-shadow: 0 22px 60px rgba(27, 43, 60, 0.2);
}

.portal-user-detail-backdrop {
  align-items: stretch;
  justify-content: flex-end;
  padding: 0;
}

.portal-membership-modal {
  display: flex;
  width: min(640px, calc(100vw - 48px));
  max-height: min(720px, calc(100vh - 56px));
  flex-direction: column;
  overflow: hidden;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 22px 60px rgba(27, 43, 60, 0.2);
}

.portal-membership-scroll {
  max-height: 620px;
}

.portal-membership-content {
  padding: 20px 26px 28px;
}

.portal-membership-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-top: 18px;
  border: 1px solid #e4edef;
  border-radius: 7px;
  overflow: hidden;
}

.portal-membership-summary > view {
  display: flex;
  min-height: 66px;
  flex-direction: column;
  justify-content: center;
  padding: 0 14px;
  border-left: 1px solid #e7edf0;
}

.portal-membership-summary > view:first-child {
  border-left: 0;
}

.portal-membership-summary text {
  color: #98a7b6;
  font-size: 10px;
}

.portal-membership-summary strong {
  margin-top: 6px;
  color: #2e4359;
  font-size: 13px;
}

.portal-membership-actions {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}

.portal-membership-action {
  min-height: 34px;
  margin: 0;
  padding: 0 8px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #b6d7ef;
  border-radius: 7px;
  box-sizing: border-box;
  color: #34799f;
  font-size: 10px;
  font-weight: 700;
  line-height: 1.25;
  text-align: center;
  background: #f1f8fc;
}

.portal-membership-action.cancel {
  border-color: #ecc8c3;
  color: #b36258;
  background: #fff7f5;
}

.portal-membership-action[disabled] {
  border-color: #e1e8eb;
  color: #a3afb9;
  background: #f6f8f9;
}

.portal-membership-order-list {
  border: 1px solid #e6edef;
  border-radius: 7px;
  overflow: hidden;
}

.portal-membership-order-row {
  display: flex;
  min-height: 58px;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 8px 13px;
  border-top: 1px solid #edf1f3;
}

.portal-membership-order-row:first-child {
  border-top: 0;
}

.portal-membership-order-row > view:first-child {
  min-width: 0;
}

.portal-membership-order-row strong {
  display: block;
  overflow: hidden;
  color: #40556b;
  font-size: 11px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.portal-membership-order-row > view:first-child text {
  display: block;
  overflow: hidden;
  margin-top: 4px;
  color: #94a3b3;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.portal-membership-order-meta {
  display: grid;
  grid-template-columns: auto auto;
  align-items: center;
  justify-items: end;
  column-gap: 8px;
  row-gap: 4px;
  flex: 0 0 auto;
}

.portal-membership-order-meta time {
  grid-column: 1 / -1;
  color: #9aa8b7;
  font-size: 9px;
}

.membership-order-status {
  font-size: 9px;
  font-weight: 700;
}

.membership-order-status.is-paid {
  color: #2da28c;
}

.membership-order-status.is-pending {
  color: #d89b4c;
}

.membership-order-status.is-failed,
.membership-order-status.is-cancelled,
.membership-order-status.is-refunded {
  color: #c97067;
}

.portal-user-detail-scroll {
  min-height: 0;
  flex: 1;
  max-height: none;
}

.portal-user-detail-content {
  padding: 20px 26px 28px;
}

.portal-user-profile-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-bottom: 18px;
  border-bottom: 1px solid #e8eef1;
}

.portal-user-profile-card .status-pill {
  margin-left: auto;
}

.portal-user-detail-stats {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  margin-top: 18px;
  border: 1px solid #e4edef;
  border-radius: 7px;
  overflow: hidden;
}

.portal-user-detail-stats > view {
  display: flex;
  min-height: 68px;
  flex-direction: column;
  justify-content: center;
  padding: 0 14px;
  border-left: 1px solid #e7edf0;
}

.portal-user-detail-stats > view:first-child {
  border-left: 0;
}

.portal-user-detail-stats text {
  color: #98a7b6;
  font-size: 10px;
}

.portal-user-detail-stats strong {
  margin-top: 6px;
  color: #2e4359;
  font-size: 18px;
}

.portal-user-detail-heading {
  margin: 22px 0 10px;
  color: #354b62;
  font-size: 12px;
  font-weight: 700;
}

.portal-subject-accuracy-list,
.portal-answer-list {
  border: 1px solid #e6edef;
  border-radius: 7px;
  overflow: hidden;
}

.portal-subject-accuracy-row {
  display: flex;
  min-height: 42px;
  align-items: center;
  justify-content: space-between;
  padding: 0 13px;
  border-top: 1px solid #edf1f3;
}

.portal-subject-accuracy-row:first-child,
.portal-answer-row:first-child {
  border-top: 0;
}

.portal-subject-accuracy-row strong,
.portal-answer-row strong {
  color: #40556b;
  font-size: 11px;
}

.portal-subject-accuracy-row text {
  margin-left: 8px;
  color: #9ba9b7;
  font-size: 10px;
}

.portal-answer-row {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) 120px;
  min-height: 52px;
  align-items: center;
  gap: 8px;
  padding: 0 13px;
  border-top: 1px solid #edf1f3;
}

.portal-answer-row > text {
  font-size: 10px;
  font-weight: 700;
}

.portal-answer-row > text.is-correct {
  color: #2da28c;
}

.portal-answer-row > text.is-wrong {
  color: #d66f60;
}

.portal-answer-row view text {
  display: block;
  overflow: hidden;
  margin-top: 4px;
  color: #94a3b3;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.portal-answer-row time {
  color: #9aa8b7;
  font-size: 9px;
  text-align: right;
}

.portal-detail-empty {
  padding: 18px;
  border: 1px dashed #dbe5e8;
  border-radius: 7px;
  color: #9aa9b8;
  font-size: 11px;
  text-align: center;
}

@media (max-width: 1180px) {
  .operations-summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .home-editor-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .user-filter-toolbar {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }

  .sidebar-focus-toggle {
    display: flex;
  }

  .portal-sidebar {
    width: 82px;
    padding-left: 12px;
    padding-right: 12px;
  }

  .portal-main {
    margin-left: 82px;
  }

  .brand-copy,
  .sidebar-section-label,
  .nav-label,
  .profile-copy {
    display: none;
  }

  .sidebar-brand,
  .nav-item,
  .logout-button {
    justify-content: center;
  }

  .nav-item,
  .logout-button {
    padding: 0;
  }

  .nav-glyph,
  .nav-icon {
    width: auto;
  }

  .nav-icon {
    width: 20px;
    height: 20px;
  }

  .nav-count {
    position: absolute;
    margin: -27px 0 0 26px;
  }

  .sidebar-collapsed .portal-sidebar {
    width: 72px;
    padding-left: 10px;
    padding-right: 10px;
  }

  .sidebar-collapsed .portal-main {
    margin-left: 72px;
  }

  .dashboard-metrics,
  .community-summary {
    grid-template-columns: 1fr 1fr;
  }

  .metric-card:last-child {
    grid-column: 1 / -1;
  }

  .filter-toolbar {
    flex-wrap: wrap;
  }

  .dashboard-panel .panel-heading {
    min-height: 104px;
    padding-top: 14px;
    padding-bottom: 14px;
    flex-wrap: wrap;
  }

  .dashboard-filter-bar {
    margin-left: 0;
  }
}

@media (max-width: 820px) {
  .operations-summary-grid,
  .operations-tab-strip,
  .home-content-columns,
  .home-editor-grid,
  .home-user-preview-grid,
  .home-preview-focus-list,
  .user-filter-toolbar {
    grid-template-columns: 1fr;
  }

  .home-editor-grid .form-field.full {
    grid-column: auto;
  }

  .operations-heading-row,
  .admission-import-actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .announcement-workspace-heading,
  .major-catalog-workspace-heading {
    align-items: flex-start;
  }

  .announcement-workspace-heading > view:first-child,
  .major-catalog-workspace-heading > view:first-child {
    width: 100%;
    min-width: 0;
  }

  .announcement-heading-tools,
  .major-catalog-heading-tools {
    width: 100%;
    flex-wrap: wrap;
    justify-content: space-between;
  }

  .announcement-heading-tools .question-admin-select {
    min-width: 132px;
    flex: 1;
  }

  .scoreline-workspace-heading {
    align-items: flex-start;
  }

  .scoreline-workspace-heading > view:first-child,
  .scoreline-heading-tools {
    width: 100%;
    min-width: 0;
  }

  .scoreline-heading-tools {
    justify-content: space-between;
  }

  .scoreline-filter-toolbar {
    flex-wrap: wrap;
  }

  .scoreline-filter-search {
    width: 100%;
    min-width: 0;
    flex: 1 1 100%;
  }

  .scoreline-filter-select {
    width: calc(50% - 4px);
    min-width: 0;
    flex: 1 1 calc(50% - 4px);
  }

  .major-catalog-school-select {
    width: calc(50% - 4px);
    flex-basis: calc(50% - 4px);
  }

  .scoreline-filter-apply {
    margin-left: auto;
  }

  .scoreline-filter-clear {
    margin-left: auto;
  }

  .home-preview-counts {
    flex-wrap: wrap;
  }

  .home-user-preview-panel + .home-user-preview-panel {
    border-top: 1px solid #edf1f3;
    border-left: 0;
  }

  .home-status-row {
    min-height: 0;
    align-items: flex-start;
    flex-direction: column;
    padding-top: 12px;
    padding-bottom: 12px;
  }

  .home-status-row > view:first-child,
  .home-status-actions {
    width: 100%;
  }

  .home-status-actions {
    justify-content: flex-end;
  }

  .admission-file-picker {
    width: 100%;
    min-width: 0;
  }

  .admission-import-backdrop {
    padding: 16px;
  }

  .home-content-editor-backdrop {
    padding: 16px;
  }

  .home-content-editor-modal {
    width: 100%;
    height: calc(100vh - 32px);
  }

  .home-editor-content {
    padding: 18px;
  }

  .home-editor-actions {
    padding: 14px 18px;
  }

  .admission-import-modal {
    width: 100%;
    max-height: calc(100vh - 32px);
  }

  .admission-import-content {
    padding: 18px 18px 22px;
  }

  .scoreline-editor-backdrop {
    padding: 16px;
  }

  .scoreline-editor-modal {
    width: 100%;
    max-height: calc(100vh - 32px);
  }

  .announcement-editor-modal,
  .major-catalog-editor-modal {
    height: calc(100vh - 32px);
  }

  .scoreline-editor-content {
    padding: 18px 18px 22px;
  }

  .scoreline-editor-grid,
  .announcement-editor-grid,
  .major-catalog-editor-grid {
    grid-template-columns: 1fr;
  }

  .announcement-editor-grid .form-field.full {
    grid-column: auto;
  }

  .admission-template-button {
    margin-left: 0;
    order: -1;
    align-self: flex-end;
  }

  .admission-preview-summary {
    flex-wrap: wrap;
    gap: 12px;
  }

  .admission-preview-row {
    grid-template-columns: 68px minmax(0, 1fr);
  }

  .admission-preview-row text:last-child {
    grid-column: 2;
  }

  .portal-user-detail-modal {
    width: calc(100vw - 28px);
  }

  .portal-user-detail-content {
    padding-left: 18px;
    padding-right: 18px;
  }

  .portal-membership-content {
    padding-right: 18px;
    padding-left: 18px;
  }

  .portal-user-detail-stats {
    grid-template-columns: 1fr 1fr;
  }

  .portal-membership-actions {
    grid-template-columns: 1fr;
  }

  .portal-user-detail-stats > view:nth-child(3) {
    border-left: 0;
  }

  .portal-user-detail-stats > view:nth-child(-n + 2) {
    border-bottom: 1px solid #e7edf0;
  }

  .portal-sidebar {
    display: none;
  }

  .portal-main {
    margin-left: 0;
  }

  .portal-header,
  .content-section {
    padding-left: 18px;
    padding-right: 18px;
  }

  .dashboard-metrics,
  .community-summary,
  .question-summary,
  .import-flow {
    grid-template-columns: 1fr 1fr;
  }

  .community-detail-content {
    padding-left: 18px;
    padding-right: 18px;
  }

  .community-detail-stat-grid {
    grid-template-columns: 1fr 1fr;
  }

  .community-detail-stat-grid > view:nth-child(2) {
    border-right: 0;
  }

  .community-detail-stat-grid > view:nth-child(-n + 2) {
    border-bottom: 1px solid #edf1f3;
  }

  .bank-file-grid {
    grid-template-columns: 1fr 1fr;
  }

  .import-hero-card {
    grid-template-columns: 1fr;
  }

  .import-visual {
    display: none;
  }

  .dashboard-panel .panel-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .dashboard-filter-bar {
    width: 100%;
    flex-wrap: wrap;
  }

}
</style>
