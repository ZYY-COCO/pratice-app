<template>
  <view class="admin-page" :class="{ 'question-mode': activeTab === 'questions' }" :style="themeInlineStyle">
    <view class="admin-hero">
      <button class="back-btn" @tap="goBack">
        <image class="back-icon" src="/static/ui-icons/back.svg" mode="aspectFit" />
      </button>
      <view class="admin-heading">
        <view class="admin-title">{{ pageTitle }}</view>
        <view class="admin-subtitle">{{ pageSubtitle }}</view>
      </view>
      <button v-if="activeTab === 'questions'" class="hero-refresh-btn" @tap="questionCreateMode ? openCreateQuestionActions() : refreshQuestionManager">
        {{ questionCreateMode ? '⋮' : '↻' }}
      </button>
    </view>

    <view v-if="loading" class="state-card">正在读取后台数据...</view>
    <view v-else-if="!allowed" class="state-card denied">
      <view class="state-title">无后台权限</view>
      <view class="state-copy">请使用管理员账号登录后再访问。</view>
    </view>

    <template v-else>
      <view v-if="activeTab !== 'questions'" class="stat-grid">
        <view v-for="item in primaryOverviewCards" :key="item.label" class="stat-card primary">
          <view class="stat-label">{{ item.label }}</view>
          <view class="stat-value">{{ item.value }}</view>
        </view>
      </view>
      <view v-if="activeTab !== 'questions'" class="metric-strip">
        <view v-for="item in secondaryOverviewCards" :key="item.label" class="metric-item">
          <text class="metric-label">{{ item.label }}</text>
          <text class="metric-value">{{ item.value }}</text>
        </view>
      </view>

      <view v-if="!questionEntryMode" class="tab-bar">
        <button
          v-for="tab in tabs"
          :key="tab.key"
          class="tab-btn"
          :class="{ active: activeTab === tab.key }"
          @tap="switchTab(tab.key)"
        >
          {{ tab.label }}
        </button>
      </view>

      <view v-if="activeTab === 'users'" class="panel-card">
        <view class="panel-head">
          <view>
            <view class="panel-title">用户数据</view>
            <view class="panel-subtitle">账号、刷题量与会员状态</view>
          </view>
          <button class="ghost-btn refresh-btn" @tap="loadUsers">刷新</button>
        </view>
        <view class="search-row">
          <input v-model="userSearch" class="search-input" placeholder="搜索邮箱" confirm-type="search" @confirm="loadUsers" />
          <button class="search-btn" @tap="loadUsers">搜索</button>
        </view>
        <view class="filter-row">
          <button
            v-for="item in userFilterOptions"
            :key="item.key"
            class="filter-chip"
            :class="{ active: userFilter === item.key }"
            @tap="userFilter = item.key"
          >
            {{ item.label }}
          </button>
        </view>
        <view v-if="usersLoading" class="inline-state">正在加载用户...</view>
        <view v-else-if="visibleUsers.length === 0" class="inline-state">暂无匹配用户</view>
        <view v-else class="record-list">
          <view v-for="user in visibleUsers" :key="user.id" class="record-card" @tap="openUser(user)">
            <view class="record-main">
              <view class="record-title">{{ user.email || user.phone || '未绑定账号' }}</view>
              <view class="record-subtitle">
                {{ user.nickname || '未设置昵称' }} · {{ user.exam_target || '未设置目标' }} · 刷题 {{ user.answer_count || 0 }} 道
              </view>
              <view class="badge-row">
                <text class="badge" :class="{ active: user.membership_status === 'active' }">
                  {{ user.membership_status === 'active' ? '会员' : '非会员' }}
                </text>
                <text v-if="user.role === 'admin'" class="badge admin">管理员</text>
                <text v-if="user.membership_expires_at" class="record-date">至 {{ formatDate(user.membership_expires_at) }}</text>
              </view>
            </view>
            <button class="small-btn" @tap.stop="openMembershipActions(user)">{{ membershipActionLabel(user) }}</button>
          </view>
        </view>
      </view>

      <view v-if="activeTab === 'feedback'" class="panel-card">
        <view class="panel-head">
          <view>
            <view class="panel-title">用户反馈</view>
            <view class="panel-subtitle">来自 App 内帮助与反馈</view>
          </view>
          <button class="ghost-btn refresh-btn" @tap="loadFeedback">刷新</button>
        </view>
        <view v-if="feedbackLoading" class="inline-state">正在加载反馈...</view>
        <view v-else-if="feedbackItems.length === 0" class="inline-state">暂无反馈</view>
        <view v-else class="record-list">
          <view v-for="item in feedbackItems" :key="item.id" class="record-card feedback-card" @tap="openFeedback(item)">
            <view class="record-title">{{ item.feedback_type || '反馈' }}</view>
            <view class="record-subtitle clamp">{{ item.content }}</view>
            <view class="badge-row">
              <text class="badge" :class="{ active: item.status === 'resolved' || item.status === 'reviewed' }">
                {{ feedbackStatusText(item.status) }}
              </text>
              <text class="record-date">{{ formatDate(item.created_at) }} · {{ item.source_page || '未知来源' }}</text>
            </view>
            <button class="small-btn inline-action" @tap.stop="openFeedbackStatusAction(item)">处理状态</button>
          </view>
        </view>
      </view>

      <view v-if="activeTab === 'questions' && questionCreateMode" class="question-create-page">
        <view class="question-create-card">
          <view class="create-meta-grid">
            <view class="create-field">
              <view class="create-label">科目</view>
              <picker :range="createQuestionSubjectLabels" :value="selectedCreateSubjectIndex" @change="handleCreateSubjectChange">
                <view class="create-picker">
                  <text>{{ selectedCreateSubjectLabel }}</text>
                  <text class="create-picker-arrow">⌄</text>
                </view>
              </picker>
            </view>
            <view class="create-field">
              <view class="create-label">模块</view>
              <picker :range="createQuestionModuleLabels" :value="selectedCreateModuleIndex" @change="handleCreateModuleChange">
                <view class="create-picker">
                  <text>{{ selectedCreateModuleLabel }}</text>
                  <text class="create-picker-arrow">⌄</text>
                </view>
              </picker>
            </view>
          </view>

          <view class="create-field full">
            <view class="create-label">考点</view>
            <picker :range="createQuestionSubmoduleLabels" :value="selectedCreateSubmoduleIndex" @change="handleCreateSubmoduleChange">
              <view class="create-picker">
                <text>{{ selectedCreateSubmoduleLabel }}</text>
                <text class="create-picker-arrow">⌄</text>
              </view>
            </picker>
          </view>

          <view class="create-section-title">难度选择</view>
          <view class="create-difficulty-row">
            <button
              v-for="item in createDifficultyOptions"
              :key="item"
              class="create-difficulty-btn"
              :class="{ active: Number(createQuestionForm.difficulty) === item }"
              @tap="createQuestionForm.difficulty = item"
            >
              {{ item }}
            </button>
          </view>

          <view class="create-divider"></view>

          <view class="create-section-head">
            <view class="create-section-title">题干</view>
            <text class="create-required-tag">必填</text>
          </view>
          <textarea
            v-model.trim="createQuestionForm.stem"
            class="create-textarea stem"
            placeholder="请输入题干，英语填空建议包含 ____，数学公式建议使用 LaTeX"
          />

          <view class="create-section-head options">
            <view class="create-section-title">选项</view>
            <text class="create-section-hint">设置 A-D 四个选项，并选择正确答案</text>
          </view>
          <view class="create-option-list">
            <view class="create-option-row" :class="{ selected: createQuestionForm.answer === 'A' }" @tap="setCreateAnswer('A')">
              <text class="create-radio">{{ createQuestionForm.answer === 'A' ? '●' : '○' }}</text>
              <text class="create-option-label">A.</text>
              <input v-model.trim="createQuestionForm.option_a" class="create-option-input" placeholder="A 选项" />
            </view>
            <view class="create-option-row" :class="{ selected: createQuestionForm.answer === 'B' }" @tap="setCreateAnswer('B')">
              <text class="create-radio">{{ createQuestionForm.answer === 'B' ? '●' : '○' }}</text>
              <text class="create-option-label">B.</text>
              <input v-model.trim="createQuestionForm.option_b" class="create-option-input" placeholder="B 选项" />
            </view>
            <view class="create-option-row" :class="{ selected: createQuestionForm.answer === 'C' }" @tap="setCreateAnswer('C')">
              <text class="create-radio">{{ createQuestionForm.answer === 'C' ? '●' : '○' }}</text>
              <text class="create-option-label">C.</text>
              <input v-model.trim="createQuestionForm.option_c" class="create-option-input" placeholder="C 选项" />
            </view>
            <view class="create-option-row" :class="{ selected: createQuestionForm.answer === 'D' }" @tap="setCreateAnswer('D')">
              <text class="create-radio">{{ createQuestionForm.answer === 'D' ? '●' : '○' }}</text>
              <text class="create-option-label">D.</text>
              <input v-model.trim="createQuestionForm.option_d" class="create-option-input" placeholder="D 选项" />
            </view>
          </view>

          <view class="create-section-head">
            <view class="create-section-title">解析</view>
            <text class="create-suggest-tag">建议填写</text>
          </view>
          <textarea
            v-model.trim="createQuestionForm.explanation"
            class="create-textarea explanation"
            placeholder="写清楚答案理由、易错点或推导过程"
          />
        </view>

        <view class="question-create-footer">
          <button
            class="create-footer-btn outline"
            :disabled="questionCreateSaving"
            @tap="submitCreatedQuestion('pending')"
          >
            <text class="create-footer-icon">◷</text>
            <text>进入待审核</text>
          </button>
          <button
            class="create-footer-btn primary"
            :disabled="questionCreateSaving"
            @tap="submitCreatedQuestion('publish')"
          >
            <text class="create-footer-icon">↥</text>
            <text>直接发布</text>
          </button>
        </view>
      </view>

      <view v-if="activeTab === 'questions' && !questionCreateMode" class="question-manager">
        <view class="question-stats-grid">
          <view
            v-for="item in questionStatCards"
            :key="item.label"
            class="question-stat-card"
            :class="item.tone"
          >
            <view class="question-stat-head">
              <view class="question-stat-icon">
                <image
                  v-if="item.iconSrc"
                  class="question-stat-image"
                  :src="item.iconSrc"
                  mode="aspectFit"
                />
                <text v-else>{{ item.icon }}</text>
              </view>
              <view class="question-stat-label">{{ item.label }}</view>
            </view>
            <view class="question-stat-value">{{ item.value }}</view>
          </view>
        </view>

        <view class="question-search-box">
          <text class="question-search-icon">⌕</text>
          <input
            v-model.trim="questionFilters.search"
            class="question-search-input"
            placeholder="搜索题干 / ID"
            confirm-type="search"
            @input="handleQuestionSearchInput"
            @confirm="applyQuestionFilters"
          />
        </view>

        <view class="question-filter-row">
          <picker :range="questionSubjectLabels" :value="selectedQuestionSubjectIndex" @change="handleQuestionSubjectChange">
            <view class="question-filter-pill">
              <text>{{ selectedQuestionSubjectLabel }}</text>
              <text class="question-filter-arrow">⌄</text>
            </view>
          </picker>
          <picker :range="questionModuleLabels" :value="selectedQuestionModuleIndex" @change="handleQuestionModuleChange">
            <view class="question-filter-pill">
              <text>{{ selectedQuestionModuleLabel }}</text>
              <text class="question-filter-arrow">⌄</text>
            </view>
          </picker>
          <picker :range="questionDifficultyLabels" :value="selectedQuestionDifficultyIndex" @change="handleQuestionDifficultyChange">
            <view class="question-filter-pill">
              <text>{{ selectedQuestionDifficultyLabel }}</text>
              <text class="question-filter-arrow">⌄</text>
            </view>
          </picker>
          <picker :range="questionStatusLabels" :value="selectedQuestionStatusIndex" @change="handleQuestionStatusChange">
            <view class="question-filter-pill">
              <text>{{ selectedQuestionStatusLabel }}</text>
              <text class="question-filter-arrow">⌄</text>
            </view>
          </picker>
        </view>

        <view class="question-action-row" :class="{ compact: !canShowReviewQueueEntry }">
          <button class="question-action-btn outline" @tap="openCreateQuestion">
            <text class="question-action-icon">＋</text>
            <text>新增题目</text>
          </button>
          <button class="question-action-btn outline" @tap="openQuestionImageImport">
            <text class="question-action-icon">⇧</text>
            <text>批量导入图片</text>
          </button>
          <button v-if="canShowReviewQueueEntry" class="question-action-btn filled" @tap="openReviewQueue">
            <text class="question-action-icon">☷</text>
            <text>进入审核队列</text>
          </button>
        </view>

        <view v-if="questionsLoading" class="inline-state">正在加载题库...</view>
        <view v-else-if="questionLoadError" class="question-empty-state">
          <view class="question-empty-title">题库加载失败</view>
          <view class="question-empty-copy">请检查管理员登录状态和网络连接，或稍后重新加载。</view>
          <button class="question-empty-btn" @tap="refreshQuestionManager">重新加载</button>
        </view>
        <view v-else-if="questions.length === 0" class="question-empty-state">
          <view class="question-empty-title">{{ questionEmptyTitle }}</view>
          <view class="question-empty-copy">{{ questionEmptyCopy }}</view>
          <button v-if="hasQuestionFilters" class="question-empty-btn" @tap="clearQuestionFilters">清空筛选</button>
        </view>
        <view v-else class="question-card-list">
          <view v-for="item in questions" :key="item.id" class="question-admin-card" @tap="openQuestion(item)">
            <button
              class="question-check"
              :class="{ checked: isQuestionSelected(item.id) }"
              @tap.stop="toggleQuestionSelection(item.id)"
            >
              {{ isQuestionSelected(item.id) ? '✓' : '' }}
            </button>
            <view class="question-card-main">
              <view class="question-chip-row">
                <text class="question-chip">{{ item.subject || item.exam_code || '未分类' }}</text>
                <text class="question-chip">{{ item.submodule || item.module || '未分模块' }}</text>
                <text class="question-chip">难度 {{ item.difficulty || '-' }}</text>
              </view>
              <view class="question-stem-preview">{{ previewQuestionStem(item.stem) }}</view>
              <view class="question-status-row">
                <text class="question-status-pill" :class="questionStatusTone(questionDisplayStatus(item))">
                  {{ questionStatusText(questionDisplayStatus(item)) }}
                </text>
                <text v-if="item.answer" class="question-answer">答案 {{ item.answer }}</text>
              </view>
            </view>
            <button class="question-edit-btn" @tap.stop="openQuestion(item)">
              <text class="question-edit-icon">✎</text>
              <text>编辑</text>
            </button>
          </view>
        </view>

        <view class="question-bulk-bar" :class="[questionBulkBarMode, { idle: selectedQuestionCount === 0 }]">
          <view class="question-selected-label">
            已选 <text class="question-selected-count">{{ selectedQuestionCount }}</text> 题
          </view>
          <button class="question-bulk-btn" @tap="toggleSelectAllQuestions">
            <image class="question-bulk-image" src="/static/admin-icons/select-all.svg" mode="aspectFit" />
            <text>{{ allVisibleQuestionsSelected ? '取消' : '全选' }}</text>
          </button>
          <button v-if="canBulkArchiveQuestions" class="question-bulk-btn archive" @tap="archiveSelectedQuestions">
            <image class="question-bulk-image" src="/static/admin-icons/unpublish.svg" mode="aspectFit" />
            <text>下架</text>
          </button>
          <button v-if="canBulkPublishQuestions" class="question-bulk-btn publish" @tap="publishSelectedQuestions">
            <image class="question-bulk-image" src="/static/admin-icons/publish.svg" mode="aspectFit" />
            <text>发布</text>
          </button>
        </view>
      </view>

      <view v-if="activeTab === 'messages'" class="panel-card">
        <view class="panel-head">
          <view>
            <view class="panel-title">官方消息</view>
            <view class="panel-subtitle">发布首页铃铛公告，用户读后不再自动弹出</view>
          </view>
          <button class="ghost-btn" @tap="resetMessageForm">新建</button>
        </view>

        <view class="message-editor">
          <input v-model.trim="messageForm.title" class="search-input" placeholder="消息标题" />
          <textarea v-model.trim="messageForm.content" class="message-textarea" placeholder="消息内容，支持换行" />
          <view class="message-status-row">
            <button
              v-for="item in messageStatusOptions"
              :key="item.value"
              class="status-chip"
              :class="{ active: messageForm.status === item.value }"
              @tap="messageForm.status = item.value"
            >
              {{ item.label }}
            </button>
          </view>
          <button class="search-btn wide" @tap="saveOfficialMessage">
            {{ messageForm.id ? '保存消息' : '创建消息' }}
          </button>
        </view>

        <view class="panel-head compact">
          <view class="panel-title small">消息列表</view>
          <button class="ghost-btn refresh-btn" @tap="loadMessages">刷新</button>
        </view>
        <view v-if="messagesLoading" class="inline-state">正在加载消息...</view>
        <view v-else-if="officialMessageItems.length === 0" class="inline-state">暂无官方消息</view>
        <view v-else class="record-list">
          <view v-for="item in officialMessageItems" :key="item.id" class="record-card feedback-card" @tap="editOfficialMessage(item)">
            <view class="record-title">{{ item.title }}</view>
            <view class="record-subtitle clamp">{{ item.content }}</view>
            <view class="badge-row">
              <text class="badge" :class="{ active: item.status === 'published', archived: item.status === 'archived' }">
                {{ messageStatusText(item.status) }}
              </text>
              <text class="record-date">{{ formatDate(item.published_at || item.created_at) }}</text>
            </view>
            <button class="small-btn inline-action" @tap.stop="editOfficialMessage(item)">编辑</button>
          </view>
        </view>
      </view>
    </template>

    <view v-if="reviewQueueVisible" class="review-overlay" @tap="closeReviewQueue">
      <view class="review-sheet" @tap.stop>
        <view class="review-sheet-head">
          <view class="review-head-copy">
            <view class="review-title">审核队列</view>
            <view class="review-subtitle">逐题检查题干、答案与解析</view>
          </view>
          <view class="review-progress">{{ reviewQueuePosition }} / {{ reviewQueueCount }}</view>
          <text
            v-if="activeReviewQuestion"
            class="review-status-pill"
            :class="reviewStatusTone(activeReviewQuestion.review_status)"
          >
            {{ reviewStatusText(activeReviewQuestion.review_status) }}
          </text>
          <button class="review-close-btn" @tap="closeReviewQueue">×</button>
        </view>

        <view v-if="reviewQueueLoading" class="inline-state">正在加载审核队列...</view>
        <view v-else-if="!activeReviewQuestion" class="review-empty">
          当前筛选下暂无待审核题目
        </view>
        <view v-else class="review-body">
          <view class="review-section-head">
            <view>
              <view class="review-section-title">题目</view>
              <view class="review-section-subtitle">检查题干、分类与难度</view>
            </view>
            <view class="review-edit-actions">
              <button v-if="reviewEditing" class="review-mini-btn muted" @tap="cancelReviewEditing">取消</button>
              <button class="review-mini-btn" @tap="reviewEditing ? saveReviewEdits() : startReviewEditing()">
                {{ reviewEditing ? '保存' : '编辑' }}
              </button>
            </view>
          </view>

          <view v-if="reviewEditing" class="review-meta-grid">
            <input v-model.trim="reviewForm.subject" class="review-input" placeholder="科目" />
            <input v-model.trim="reviewForm.module" class="review-input" placeholder="模块" />
            <input v-model.trim="reviewForm.submodule" class="review-input" placeholder="考点" />
            <view class="review-difficulty-row">
              <button
                v-for="item in reviewDifficultyOptions"
                :key="item"
                class="review-difficulty-btn"
                :class="{ active: Number(reviewForm.difficulty) === item }"
                @tap="reviewForm.difficulty = item"
              >
                {{ item }}
              </button>
            </view>
          </view>

          <view class="review-question-box" :class="{ editing: reviewEditing }">
            <textarea
              v-if="reviewEditing"
              v-model.trim="reviewForm.stem"
              class="review-textarea stem"
              placeholder="题干"
            />
            <view v-else class="review-stem">{{ activeReviewQuestion.stem || '未填写题干' }}</view>
            <view class="question-chip-row review-chips">
              <text class="question-chip">{{ reviewEditing ? reviewForm.subject : (activeReviewQuestion.subject || '未分类') }}</text>
              <text class="question-chip">{{ reviewEditing ? reviewForm.submodule : (activeReviewQuestion.submodule || activeReviewQuestion.module || '未分模块') }}</text>
              <text class="question-chip">难度 {{ reviewEditing ? reviewForm.difficulty : (activeReviewQuestion.difficulty || '-') }}</text>
            </view>
          </view>

          <view class="review-section-head compact">
            <view class="review-section-title">选项</view>
            <view class="review-section-subtitle">勾选 1 个正确答案</view>
          </view>
          <view class="review-option-list">
            <view class="review-option-row" :class="{ selected: reviewCurrentAnswer() === 'A' }" @tap="setReviewAnswer('A')">
              <text class="review-radio">{{ reviewCurrentAnswer() === 'A' ? '●' : '○' }}</text>
              <text v-if="reviewEditing" class="review-option-label">A.</text>
              <input v-if="reviewEditing" v-model.trim="reviewForm.option_a" class="review-option-input" placeholder="A 选项" />
              <text v-else class="review-option-text">A. {{ activeReviewQuestion.option_a }}</text>
            </view>
            <view class="review-option-row" :class="{ selected: reviewCurrentAnswer() === 'B' }" @tap="setReviewAnswer('B')">
              <text class="review-radio">{{ reviewCurrentAnswer() === 'B' ? '●' : '○' }}</text>
              <text v-if="reviewEditing" class="review-option-label">B.</text>
              <input v-if="reviewEditing" v-model.trim="reviewForm.option_b" class="review-option-input" placeholder="B 选项" />
              <text v-else class="review-option-text">B. {{ activeReviewQuestion.option_b }}</text>
            </view>
            <view class="review-option-row" :class="{ selected: reviewCurrentAnswer() === 'C' }" @tap="setReviewAnswer('C')">
              <text class="review-radio">{{ reviewCurrentAnswer() === 'C' ? '●' : '○' }}</text>
              <text v-if="reviewEditing" class="review-option-label">C.</text>
              <input v-if="reviewEditing" v-model.trim="reviewForm.option_c" class="review-option-input" placeholder="C 选项" />
              <text v-else class="review-option-text">C. {{ activeReviewQuestion.option_c }}</text>
            </view>
            <view class="review-option-row" :class="{ selected: reviewCurrentAnswer() === 'D' }" @tap="setReviewAnswer('D')">
              <text class="review-radio">{{ reviewCurrentAnswer() === 'D' ? '●' : '○' }}</text>
              <text v-if="reviewEditing" class="review-option-label">D.</text>
              <input v-if="reviewEditing" v-model.trim="reviewForm.option_d" class="review-option-input" placeholder="D 选项" />
              <text v-else class="review-option-text">D. {{ activeReviewQuestion.option_d }}</text>
            </view>
          </view>

          <view class="review-section-head compact">
            <view class="review-section-title">解析</view>
          </view>
          <textarea
            v-if="reviewEditing"
            v-model.trim="reviewForm.explanation"
            class="review-textarea explanation"
            placeholder="解析"
          />
          <view v-else class="review-explanation-box">
            {{ activeReviewQuestion.explanation || '暂无解析' }}
          </view>

          <view class="review-section-head compact">
            <view class="review-section-title">审核备注</view>
            <view class="review-section-subtitle">标记需修改时必填</view>
          </view>
          <textarea
            v-model.trim="reviewForm.review_note"
            class="review-textarea note"
            placeholder="例如：题干出处不足、答案有争议、解析需要补充依据"
          />
        </view>

        <view class="review-footer">
          <button class="review-footer-btn muted" :disabled="reviewSaving || !activeReviewQuestion" @tap="markReviewNeedsChanges">
            需修改
          </button>
          <button class="review-footer-btn outline" :disabled="reviewSaving || reviewQueueIndex === 0" @tap="goReviewPrev">
            上一题
          </button>
          <button class="review-footer-btn primary" :disabled="reviewSaving || !activeReviewQuestion" @tap="publishReviewQuestion">
            发布
          </button>
          <button class="review-footer-btn blue" :disabled="reviewSaving || !activeReviewQuestion" @tap="goReviewNext">
            下一题
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import {
  cancelAdminMembership,
  createAdminQuestion,
  createAdminMessage,
  fetchAdminFeedback,
  fetchAdminMe,
  fetchAdminMessages,
  fetchAdminOverview,
  fetchAdminQuestionDetail,
  fetchAdminQuestions,
  fetchAdminUserDetail,
  fetchAdminUsers,
  grantAdminMembership,
  bulkUpdateAdminQuestionStatus,
  updateAdminQuestion,
  updateAdminMessage,
  updateAdminFeedbackStatus,
  updateAdminQuestionReview,
  updateAdminQuestionStatus
} from '../../api/admin'
import { getAuthUser, isLoggedIn, updateAuthUser } from '../../utils/auth'
import { isAiGeneratedQuestion } from '../../utils/questionSource'
import { buildThemeStyle, getStoredThemeKey } from '../../utils/theme'

const ADMIN_EMAIL = '2221073755@qq.com'
const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const loading = ref(true)
const allowed = ref(false)
const overview = ref({})
const activeTab = ref('users')
const questionEntryMode = ref(false)
const questionCreateMode = ref(false)
const questionCreateSaving = ref(false)
const users = ref([])
const usersLoading = ref(false)
const userSearch = ref('')
const userFilter = ref('all')
const feedbackItems = ref([])
const feedbackLoading = ref(false)
const questions = ref([])
const questionsLoading = ref(false)
const questionLoadError = ref(false)
const questionListCount = ref(0)
const selectedQuestionIds = ref([])
const allMatchingQuestionsSelected = ref(false)
const bulkSelectionStatus = ref('')
const questionStats = reactive({
  active: 0,
  archived: 0,
  pendingReview: 0
})
const reviewQueueVisible = ref(false)
const reviewQueueLoading = ref(false)
const reviewQueueItems = ref([])
const reviewQueueCount = ref(0)
const reviewQueueIndex = ref(0)
const reviewEditing = ref(false)
const reviewSaving = ref(false)
const officialMessageItems = ref([])
const messagesLoading = ref(false)
const authUser = ref(getAuthUser())

const messageStatusOptions = [
  { value: 'draft', label: '草稿' },
  { value: 'published', label: '发布' },
  { value: 'archived', label: '归档' }
]

const messageForm = reactive({
  id: '',
  title: '',
  content: '',
  status: 'draft',
  expires_at: ''
})

const questionFilters = reactive({
  exam_code: '',
  subject: '',
  module: '',
  difficulty: '',
  status: '',
  search: ''
})

const questionSubjectOptions = [
  { label: '科目', value: '' },
  { label: '中华文化', value: '中华文化' },
  { label: '英语运用', value: '英语运用' },
  { label: '数学基础', value: '数学基础' },
  { label: '逻辑推理', value: '逻辑推理' }
]

const questionModuleMap = {
  中华文化: ['中国哲学常识', '文学常识', '历史文化', '艺术民俗', '宗教思想'],
  英语运用: ['语言知识', '词汇', '语法', '语用'],
  数学基础: ['一元函数微分学', '一元函数积分学', '多元函数微分学'],
  逻辑推理: ['论证', '概念判断', '削弱加强', '推理规则']
}

const fallbackQuestionModules = ['中国哲学常识', '词汇', '论证', '一元函数微分学']

const createQuestionCatalog = {
  中华文化: {
    exam_code: 'COMMON',
    modules: {
      中国哲学常识: ['儒家', '道家', '墨家', '法家', '名家', '纵横家', '后代学派流变', '古代宗教流变'],
      中国历史学常识: ['古代职官与科举', '古代礼俗与称谓', '古代衣食住行', '古代军事战争', '古代经济发展', '古代图书文物', '近现代史学常识'],
      中国文学常识: ['文体流变', '代表作家及作品', '创作群体及文学流派', '文学总集', '民族史诗'],
      中国艺术常识: ['书法', '绘画', '雕塑', '建筑', '音乐', '戏剧', '民俗', '陶瓷'],
      中国古代科技常识: ['天文历法与算学', '地理舆图', '农业水利', '医学', '科技发明']
    }
  },
  英语运用: {
    exam_code: 'COMMON',
    modules: {
      语言知识: ['词汇', '语法', '语用']
    }
  },
  数学基础: {
    exam_code: 'Z002',
    modules: {
      一元函数微分学: ['极限', '连续', '导数', '微分', '高阶导数', '洛必达法则', '单调性', '极值与最值', '凹凸性', '拐点', '渐近线'],
      一元函数积分学: ['原函数', '定积分', '变限积分', '牛顿-莱布尼茨公式', '换元积分', '分部积分', '几何应用', '物理应用'],
      多元函数微分学: ['偏导数', '全微分', '二阶偏导', '链导法则', '隐函数求导', '二元函数极值']
    }
  },
  逻辑推理: {
    exam_code: 'Z001',
    modules: {
      概念判断: ['概念种类', '概念关系', '定义', '划分'],
      论证: ['加强', '削弱', '解释', '谬误识别'],
      削弱加强: ['加强', '削弱'],
      推理规则: ['演绎推理', '归纳推理', '类比推理', '综合推理']
    }
  }
}

const questionDifficultyOptions = [
  { label: '难度', value: '' },
  { label: '难度 1', value: '1' },
  { label: '难度 2', value: '2' },
  { label: '难度 3', value: '3' },
  { label: '难度 4', value: '4' },
  { label: '难度 5', value: '5' }
]

const QUESTION_STATUS_ACTIVE = 'active'
const QUESTION_STATUS_ARCHIVED = 'archived'
const QUESTION_STATUS_PENDING_REVIEW = 'pending_review'

const questionStatusOptions = [
  { label: '状态', value: '' },
  { label: '待审核', value: QUESTION_STATUS_PENDING_REVIEW },
  { label: '已下架', value: QUESTION_STATUS_ARCHIVED },
  { label: '已发布', value: QUESTION_STATUS_ACTIVE }
]

const reviewAnswerOptions = ['A', 'B', 'C', 'D']
const reviewDifficultyOptions = [1, 2, 3, 4, 5]

const reviewForm = reactive({
  id: '',
  exam_code: '',
  subject: '',
  module: '',
  submodule: '',
  stem: '',
  option_a: '',
  option_b: '',
  option_c: '',
  option_d: '',
  answer: 'A',
  explanation: '',
  difficulty: 2,
  review_note: ''
})

const createDifficultyOptions = [1, 2, 3, 4, 5]

const createQuestionForm = reactive({
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
  difficulty: 2
})

const tabs = [
  { key: 'users', label: '用户' },
  { key: 'feedback', label: '反馈' },
  { key: 'messages', label: '消息' }
]

const pageTitle = computed(() => {
  if (activeTab.value === 'questions' && questionCreateMode.value) return '新增题目'
  return activeTab.value === 'questions' ? '题库管理' : '后台管理'
})
const pageSubtitle = computed(() => (
  activeTab.value === 'questions' && questionCreateMode.value
    ? '编辑题干、选项、分类与发布状态'
    : activeTab.value === 'questions'
    ? '编辑、审核与题库质量运营'
    : '用户、反馈与消息运营面板'
))

const userFilterOptions = [
  { key: 'all', label: '全部' },
  { key: 'member', label: '会员' },
  { key: 'non_member', label: '非会员' },
  { key: 'active', label: '有刷题' }
]

const primaryOverviewCards = computed(() => [
  { label: '总用户', value: overview.value.total_users || 0 },
  { label: '今日活跃', value: overview.value.active_today || 0 },
  { label: '会员数', value: overview.value.active_members || 0 },
  { label: '待处理', value: overview.value.pending_feedback || 0 }
])

const secondaryOverviewCards = computed(() => [
  { label: '本周活跃', value: overview.value.active_week || 0 },
  { label: '本月活跃', value: overview.value.active_month || 0 },
  { label: '题库量', value: overview.value.total_questions || 0 },
  { label: '反馈数', value: overview.value.total_feedback || 0 }
])

const questionStatCards = computed(() => [
  {
    label: '题量',
    value: overview.value.total_questions || questionListCount.value || 0,
    iconSrc: '/static/admin-icons/question-count.svg',
    tone: 'blue'
  },
  {
    label: '待审核',
    value: questionStats.pendingReview,
    iconSrc: '/static/admin-icons/pending-review.svg',
    tone: 'orange'
  },
  {
    label: '下架',
    value: questionStats.archived,
    iconSrc: '/static/admin-icons/unpublish.svg',
    tone: 'green'
  },
  {
    label: '发布',
    value: questionStats.active,
    iconSrc: '/static/admin-icons/publish.svg',
    tone: 'blue'
  }
])

const questionModuleOptions = computed(() => {
  const modules = questionModuleMap[questionFilters.subject] || fallbackQuestionModules
  const uniqueModules = new Set(modules)
  if (questionFilters.module) {
    uniqueModules.add(questionFilters.module)
  }
  return [
    { label: '模块', value: '' },
    ...Array.from(uniqueModules).map((item) => ({ label: item, value: item }))
  ]
})

const questionSubjectLabels = computed(() => questionSubjectOptions.map((item) => item.label))
const questionModuleLabels = computed(() => questionModuleOptions.value.map((item) => item.label))
const questionDifficultyLabels = computed(() => questionDifficultyOptions.map((item) => item.label))
const questionStatusLabels = computed(() => questionStatusOptions.map((item) => item.label))

const selectedQuestionSubjectIndex = computed(() => getOptionIndex(questionSubjectOptions, questionFilters.subject))
const selectedQuestionModuleIndex = computed(() => getOptionIndex(questionModuleOptions.value, questionFilters.module))
const selectedQuestionDifficultyIndex = computed(() => getOptionIndex(questionDifficultyOptions, questionFilters.difficulty))
const selectedQuestionStatusIndex = computed(() => getOptionIndex(questionStatusOptions, questionFilters.status))

const selectedQuestionSubjectLabel = computed(() => questionSubjectOptions[selectedQuestionSubjectIndex.value]?.label || '科目')
const selectedQuestionModuleLabel = computed(() => questionModuleOptions.value[selectedQuestionModuleIndex.value]?.label || '模块')
const selectedQuestionDifficultyLabel = computed(() => questionDifficultyOptions[selectedQuestionDifficultyIndex.value]?.label || '难度')
const selectedQuestionStatusLabel = computed(() => questionStatusOptions[selectedQuestionStatusIndex.value]?.label || '状态')
const hasQuestionFilters = computed(() => Boolean(
  questionFilters.exam_code ||
  questionFilters.subject ||
  questionFilters.module ||
  questionFilters.difficulty ||
  questionFilters.status ||
  questionFilters.search
))
const questionEmptyTitle = computed(() => (
  hasQuestionFilters.value ? '当前筛选下暂无正式题目' : '暂无正式题库题目'
))
const questionEmptyCopy = computed(() => {
  if (hasQuestionFilters.value) {
    return '可以清空科目、模块、难度、状态或关键词后再查看。AI 专项出题不会进入题库管理。'
  }
  return '这里仅管理正式题库；AI 专项出题只会出现在用户收藏和练习历史中。'
})

const createQuestionSubjectOptions = computed(() => (
  Object.keys(createQuestionCatalog).map((subject) => ({ label: subject, value: subject }))
))
const createQuestionModuleOptions = computed(() => {
  const catalog = createQuestionCatalog[createQuestionForm.subject]
  const modules = catalog ? Object.keys(catalog.modules) : []
  return modules.map((module) => ({ label: module, value: module }))
})
const createQuestionSubmoduleOptions = computed(() => {
  const catalog = createQuestionCatalog[createQuestionForm.subject]
  const submodules = catalog?.modules?.[createQuestionForm.module] || []
  return submodules.map((submodule) => ({ label: submodule, value: submodule }))
})
const createQuestionSubjectLabels = computed(() => createQuestionSubjectOptions.value.map((item) => item.label))
const createQuestionModuleLabels = computed(() => createQuestionModuleOptions.value.map((item) => item.label))
const createQuestionSubmoduleLabels = computed(() => createQuestionSubmoduleOptions.value.map((item) => item.label))
const selectedCreateSubjectIndex = computed(() => getOptionIndex(createQuestionSubjectOptions.value, createQuestionForm.subject))
const selectedCreateModuleIndex = computed(() => getOptionIndex(createQuestionModuleOptions.value, createQuestionForm.module))
const selectedCreateSubmoduleIndex = computed(() => getOptionIndex(createQuestionSubmoduleOptions.value, createQuestionForm.submodule))
const selectedCreateSubjectLabel = computed(() => createQuestionSubjectOptions.value[selectedCreateSubjectIndex.value]?.label || '请选择科目')
const selectedCreateModuleLabel = computed(() => createQuestionModuleOptions.value[selectedCreateModuleIndex.value]?.label || '请选择模块')
const selectedCreateSubmoduleLabel = computed(() => createQuestionSubmoduleOptions.value[selectedCreateSubmoduleIndex.value]?.label || '请选择考点')

const selectedQuestionIdSet = computed(() => new Set(selectedQuestionIds.value))
const selectedQuestionCount = computed(() => (
  allMatchingQuestionsSelected.value ? questionListCount.value : selectedQuestionIds.value.length
))
const allVisibleQuestionsSelected = computed(() => (
  allMatchingQuestionsSelected.value ||
  (questions.value.length > 0 && questions.value.every((item) => selectedQuestionIdSet.value.has(item.id)))
))
const selectedQuestionItems = computed(() => (
  allMatchingQuestionsSelected.value
    ? []
    : questions.value.filter((item) => selectedQuestionIdSet.value.has(item.id))
))
const selectedQuestionBulkStatuses = computed(() => (
  selectedQuestionItems.value
    .map((item) => getQuestionBulkSelectionStatus(questionDisplayStatus(item)))
    .filter(Boolean)
))
const selectedBulkSelectionStatus = computed(() => {
  const statuses = selectedQuestionBulkStatuses.value
  if (statuses.length === 0) return ''
  const firstStatus = statuses[0]
  return statuses.every((status) => status === firstStatus) ? firstStatus : ''
})
const isArchivedQuestionFilter = computed(() => questionFilters.status === QUESTION_STATUS_ARCHIVED)
const isPendingReviewQuestionFilter = computed(() => questionFilters.status === QUESTION_STATUS_PENDING_REVIEW)
const canShowReviewQueueEntry = computed(() => (
  isArchivedQuestionFilter.value || isPendingReviewQuestionFilter.value
))
const currentBulkSelectionStatus = computed(() => (
  allMatchingQuestionsSelected.value
    ? bulkSelectionStatus.value || getQuestionBulkSelectionStatus(questionFilters.status)
    : selectedBulkSelectionStatus.value
))
const canBulkArchiveQuestions = computed(() => currentBulkSelectionStatus.value === QUESTION_STATUS_ACTIVE)
const canBulkPublishQuestions = computed(() => (
  currentBulkSelectionStatus.value === QUESTION_STATUS_ARCHIVED ||
  currentBulkSelectionStatus.value === QUESTION_STATUS_PENDING_REVIEW
))
const questionBulkBarMode = computed(() => (
  canBulkArchiveQuestions.value || canBulkPublishQuestions.value ? 'with-status-action' : 'selection-only'
))
const activeReviewQuestion = computed(() => reviewQueueItems.value[reviewQueueIndex.value] || null)
const reviewQueuePosition = computed(() => (activeReviewQuestion.value ? reviewQueueIndex.value + 1 : 0))

const visibleUsers = computed(() => {
  if (userFilter.value === 'member') {
    return users.value.filter((user) => user.membership_status === 'active')
  }
  if (userFilter.value === 'non_member') {
    return users.value.filter((user) => user.membership_status !== 'active')
  }
  if (userFilter.value === 'active') {
    return users.value.filter((user) => Number(user.answer_count || 0) > 0)
  }
  return users.value
})

onLoad(async (options = {}) => {
  if (options.tab === 'questions') {
    activeTab.value = 'questions'
    questionEntryMode.value = true
  }
  await bootstrap()
})

async function bootstrap() {
  if (!isLoggedIn()) {
    uni.redirectTo({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/admin/index')}` })
    return
  }

  loading.value = true
  try {
    const me = await fetchAdminMe()
    allowed.value = Boolean(me?.is_admin)
    if (me?.profile) {
      const nextUser = updateAuthUser(me.profile)
      authUser.value = nextUser || me.profile
    }
    if (allowed.value) {
      const initialLoads = [loadOverview()]
      if (activeTab.value === 'questions') {
        initialLoads.push(loadQuestionStats(), loadQuestions())
      } else {
        initialLoads.push(loadUsers())
      }
      await Promise.all(initialLoads)
    }
  } catch (error) {
    const email = String(authUser.value?.email || '').toLowerCase()
    allowed.value = email === ADMIN_EMAIL
    if (!allowed.value) {
      uni.showToast({ title: '无后台权限', icon: 'none' })
    }
  } finally {
    loading.value = false
  }
}

async function loadOverview() {
  overview.value = await fetchAdminOverview()
}

async function switchTab(tab) {
  activeTab.value = tab
  if (tab === 'users' && users.value.length === 0) await loadUsers()
  if (tab === 'feedback' && feedbackItems.value.length === 0) await loadFeedback()
  if (tab === 'questions' && questions.value.length === 0) await refreshQuestionManager()
  if (tab === 'messages' && officialMessageItems.value.length === 0) await loadMessages()
}

async function refreshQuestionManager() {
  await Promise.all([loadOverview(), loadQuestionStats(), loadQuestions()])
}

async function loadUsers() {
  usersLoading.value = true
  try {
    const keyword = String(userSearch.value || '').trim()
    const params = {
      limit: 30,
      offset: 0
    }
    if (keyword) {
      params.search = keyword
    }
    const response = await fetchAdminUsers(params)
    users.value = normalizeListResponse(response)
  } catch (error) {
    uni.showToast({ title: '用户数据加载失败', icon: 'none' })
  } finally {
    usersLoading.value = false
  }
}

function normalizeListResponse(response) {
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.items)) return response.items
  if (Array.isArray(response?.users)) return response.users
  if (Array.isArray(response?.data)) return response.data
  return []
}

async function loadFeedback() {
  feedbackLoading.value = true
  try {
    const response = await fetchAdminFeedback({ limit: 50, offset: 0 })
    feedbackItems.value = response.items || []
  } catch (error) {
    uni.showToast({ title: '反馈加载失败', icon: 'none' })
  } finally {
    feedbackLoading.value = false
  }
}

async function loadQuestions() {
  questionsLoading.value = true
  questionLoadError.value = false
  try {
    const response = await fetchAdminQuestions({
      ...buildQuestionListParams(),
      limit: 50,
      offset: 0
    })
    const rawItems = (response.items || []).filter((item) => !isAiGeneratedQuestion(item))
    questions.value = rawItems
    questionListCount.value = Number(response.count || rawItems.length || 0)
    if (!allMatchingQuestionsSelected.value) {
      const visibleIds = new Set(rawItems.map((item) => item.id))
      selectedQuestionIds.value = selectedQuestionIds.value.filter((id) => visibleIds.has(id))
    }
  } catch (error) {
    questions.value = []
    questionListCount.value = 0
    questionLoadError.value = true
    uni.showToast({ title: '题库加载失败', icon: 'none' })
  } finally {
    questionsLoading.value = false
  }
}

function clearQuestionFilters() {
  questionFilters.exam_code = ''
  questionFilters.subject = ''
  questionFilters.module = ''
  questionFilters.difficulty = ''
  questionFilters.status = ''
  questionFilters.search = ''
  clearQuestionSelection()
  loadQuestions()
}

function buildQuestionListParams() {
  const params = {}
  if (questionFilters.exam_code) params.exam_code = questionFilters.exam_code
  if (questionFilters.subject) params.subject = questionFilters.subject
  if (questionFilters.module) params.module = questionFilters.module
  if (questionFilters.difficulty) params.difficulty = questionFilters.difficulty
  applyQuestionStatusParams(params, questionFilters.status)
  if (questionFilters.search) params.search = questionFilters.search
  return params
}

function applyQuestionStatusParams(params, status) {
  delete params.status
  delete params.review_status
  delete params.exclude_review_status
  if (status === QUESTION_STATUS_PENDING_REVIEW) {
    params.status = QUESTION_STATUS_ARCHIVED
    params.review_status = 'pending'
    return
  }
  if (status === QUESTION_STATUS_ARCHIVED) {
    params.status = QUESTION_STATUS_ARCHIVED
    params.exclude_review_status = 'pending'
    return
  }
  if (status === QUESTION_STATUS_ACTIVE) {
    params.status = QUESTION_STATUS_ACTIVE
  }
}

async function loadQuestionStats() {
  const [activeResult, archivedResult, pendingResult] = await Promise.allSettled([
    fetchAdminQuestions({ status: QUESTION_STATUS_ACTIVE, limit: 1, offset: 0 }),
    fetchAdminQuestions({
      status: QUESTION_STATUS_ARCHIVED,
      exclude_review_status: 'pending',
      limit: 1,
      offset: 0
    }),
    fetchAdminQuestions({
      status: QUESTION_STATUS_ARCHIVED,
      review_status: 'pending',
      limit: 1,
      offset: 0
    })
  ])
  questionStats.active = activeResult.status === 'fulfilled' ? Number(activeResult.value?.count || 0) : 0
  questionStats.archived = archivedResult.status === 'fulfilled' ? Number(archivedResult.value?.count || 0) : 0
  questionStats.pendingReview = pendingResult.status === 'fulfilled' ? Number(pendingResult.value?.count || 0) : 0
}

function getOptionIndex(options, value) {
  const index = options.findIndex((item) => item.value === value)
  return index >= 0 ? index : 0
}

function syncCreateQuestionClassification() {
  const catalog = createQuestionCatalog[createQuestionForm.subject] || createQuestionCatalog['英语运用']
  createQuestionForm.subject = createQuestionCatalog[createQuestionForm.subject] ? createQuestionForm.subject : '英语运用'
  createQuestionForm.exam_code = catalog.exam_code
  const modules = Object.keys(catalog.modules)
  if (!modules.includes(createQuestionForm.module)) {
    createQuestionForm.module = modules[0] || ''
  }
  const submodules = catalog.modules[createQuestionForm.module] || []
  if (!submodules.includes(createQuestionForm.submodule)) {
    createQuestionForm.submodule = submodules[0] || ''
  }
}

function resetCreateQuestionForm(seed = {}) {
  createQuestionForm.subject = createQuestionCatalog[seed.subject] ? seed.subject : '英语运用'
  createQuestionForm.module = seed.module || ''
  createQuestionForm.submodule = seed.submodule || (
    createQuestionForm.subject === '英语运用' ? '语法' : ''
  )
  syncCreateQuestionClassification()
  createQuestionForm.stem = ''
  createQuestionForm.option_a = ''
  createQuestionForm.option_b = ''
  createQuestionForm.option_c = ''
  createQuestionForm.option_d = ''
  createQuestionForm.answer = 'A'
  createQuestionForm.explanation = ''
  createQuestionForm.difficulty = Number(seed.difficulty || 2)
}

function openCreateQuestion() {
  clearQuestionSelection()
  resetCreateQuestionForm({
    subject: questionFilters.subject,
    module: questionFilters.module,
    difficulty: questionFilters.difficulty || 2
  })
  questionCreateMode.value = true
}

function openQuestionImageImport() {
  clearQuestionSelection()
  uni.navigateTo({ url: '/pages/admin/question-image-import' })
}

function openCreateQuestionActions() {
  uni.showActionSheet({
    itemList: ['清空当前内容', '返回题库管理'],
    success: ({ tapIndex }) => {
      if (tapIndex === 0) {
        resetCreateQuestionForm({
          subject: createQuestionForm.subject,
          module: createQuestionForm.module,
          submodule: createQuestionForm.submodule,
          difficulty: createQuestionForm.difficulty
        })
        return
      }
      closeCreateQuestion()
    }
  })
}

function isCreateQuestionDirty() {
  return [
    createQuestionForm.stem,
    createQuestionForm.option_a,
    createQuestionForm.option_b,
    createQuestionForm.option_c,
    createQuestionForm.option_d,
    createQuestionForm.explanation
  ].some((value) => String(value || '').trim())
}

function closeCreateQuestion() {
  if (!questionCreateMode.value) return false
  if (isCreateQuestionDirty()) {
    uni.showModal({
      title: '放弃新增题目？',
      content: '返回后当前未提交的题干、选项和解析不会保存。',
      confirmText: '放弃',
      confirmColor: '#ef4444',
      success: (result) => {
        if (!result.confirm) return
        questionCreateMode.value = false
      }
    })
    return true
  }
  questionCreateMode.value = false
  return true
}

function handleCreateSubjectChange(event) {
  const index = Number(event?.detail?.value || 0)
  createQuestionForm.subject = createQuestionSubjectOptions.value[index]?.value || '英语运用'
  createQuestionForm.module = ''
  createQuestionForm.submodule = ''
  syncCreateQuestionClassification()
}

function handleCreateModuleChange(event) {
  const index = Number(event?.detail?.value || 0)
  createQuestionForm.module = createQuestionModuleOptions.value[index]?.value || ''
  createQuestionForm.submodule = ''
  syncCreateQuestionClassification()
}

function handleCreateSubmoduleChange(event) {
  const index = Number(event?.detail?.value || 0)
  createQuestionForm.submodule = createQuestionSubmoduleOptions.value[index]?.value || ''
  syncCreateQuestionClassification()
}

function setCreateAnswer(answer) {
  if (!reviewAnswerOptions.includes(answer)) return
  createQuestionForm.answer = answer
}

function buildCreateQuestionPayload(target) {
  syncCreateQuestionClassification()
  const payload = {
    exam_code: createQuestionForm.exam_code,
    subject: createQuestionForm.subject,
    module: createQuestionForm.module,
    submodule: createQuestionForm.submodule,
    question_type: 'single_choice',
    stem: createQuestionForm.stem,
    option_a: createQuestionForm.option_a,
    option_b: createQuestionForm.option_b,
    option_c: createQuestionForm.option_c,
    option_d: createQuestionForm.option_d,
    answer: createQuestionForm.answer,
    explanation: createQuestionForm.explanation,
    difficulty: Number(createQuestionForm.difficulty),
    source_type: 'manual',
    source_year: null,
    status: target === 'publish' ? QUESTION_STATUS_ACTIVE : QUESTION_STATUS_ARCHIVED,
    review_status: target === 'publish' ? 'approved' : 'pending'
  }
  const requiredFields = ['subject', 'module', 'submodule', 'stem', 'option_a', 'option_b', 'option_c', 'option_d', 'answer']
  const missingField = requiredFields.find((field) => !String(payload[field] || '').trim())
  if (missingField) {
    uni.showToast({ title: '请补全分类、题干、四个选项和答案', icon: 'none' })
    return null
  }
  if (!reviewAnswerOptions.includes(payload.answer)) {
    uni.showToast({ title: '请选择正确答案', icon: 'none' })
    return null
  }
  if (!Number.isInteger(payload.difficulty) || payload.difficulty < 1 || payload.difficulty > 5) {
    uni.showToast({ title: '难度必须为 1-5', icon: 'none' })
    return null
  }
  return payload
}

async function submitCreatedQuestion(target) {
  if (questionCreateSaving.value) return
  const payload = buildCreateQuestionPayload(target)
  if (!payload) return
  const isPublish = target === 'publish'
  if (isPublish) {
    const confirmed = await new Promise((resolve) => {
      uni.showModal({
        title: '确认直接发布？',
        content: '发布后这道题会进入用户可刷题范围。请确认题干、答案和解析已经检查无误。',
        confirmText: '发布',
        confirmColor: '#1769ff',
        success: (result) => resolve(Boolean(result.confirm)),
        fail: () => resolve(false)
      })
    })
    if (!confirmed) return
  }

  questionCreateSaving.value = true
  try {
    await createAdminQuestion(payload)
    questionCreateMode.value = false
    questionFilters.subject = payload.subject
    questionFilters.module = payload.module
    questionFilters.difficulty = ''
    questionFilters.status = isPublish ? QUESTION_STATUS_ACTIVE : QUESTION_STATUS_PENDING_REVIEW
    questionFilters.search = ''
    resetCreateQuestionForm({ subject: payload.subject, module: payload.module, submodule: payload.submodule })
    uni.showToast({ title: isPublish ? '题目已发布' : '已进入待审核', icon: 'success' })
    await refreshQuestionManager()
  } catch (error) {
    uni.showToast({ title: '题目创建失败，请检查分类和必填内容', icon: 'none' })
  } finally {
    questionCreateSaving.value = false
  }
}

function handleQuestionSubjectChange(event) {
  const index = Number(event?.detail?.value || 0)
  questionFilters.subject = questionSubjectOptions[index]?.value || ''
  questionFilters.module = ''
  applyQuestionFilters()
}

function handleQuestionModuleChange(event) {
  const index = Number(event?.detail?.value || 0)
  questionFilters.module = questionModuleOptions.value[index]?.value || ''
  applyQuestionFilters()
}

function handleQuestionDifficultyChange(event) {
  const index = Number(event?.detail?.value || 0)
  questionFilters.difficulty = questionDifficultyOptions[index]?.value || ''
  applyQuestionFilters()
}

function handleQuestionStatusChange(event) {
  const index = Number(event?.detail?.value || 0)
  questionFilters.status = questionStatusOptions[index]?.value || ''
  applyQuestionFilters()
}

function handleQuestionSearchInput() {
  clearQuestionSelection()
}

function applyQuestionFilters() {
  clearQuestionSelection()
  loadQuestions()
}

function clearQuestionSelection() {
  allMatchingQuestionsSelected.value = false
  selectedQuestionIds.value = []
  bulkSelectionStatus.value = ''
}

function showComingSoon(label) {
  uni.showToast({ title: `${label}后续接入`, icon: 'none' })
}

async function openReviewQueue() {
  reviewQueueVisible.value = true
  reviewQueueIndex.value = 0
  reviewEditing.value = false
  await loadReviewQueue({ append: false })
}

async function loadReviewQueue({ append = false } = {}) {
  reviewQueueLoading.value = !append
  try {
    const response = await fetchAdminQuestions({
      ...buildReviewQueueParams(),
      review_status: 'pending',
      status: QUESTION_STATUS_ARCHIVED,
      limit: 50,
      offset: append ? reviewQueueItems.value.length : 0
    })
    const items = (response.items || []).filter((item) => !isAiGeneratedQuestion(item))
    reviewQueueItems.value = append ? [...reviewQueueItems.value, ...items] : items
    reviewQueueCount.value = Number(response.count || reviewQueueItems.value.length || 0)
    if (!append) {
      reviewQueueIndex.value = 0
    }
    syncReviewForm()
    if (!reviewQueueItems.value.length) {
      uni.showToast({ title: '当前筛选下暂无待审核题目', icon: 'none' })
    }
  } catch (error) {
    reviewQueueItems.value = append ? reviewQueueItems.value : []
    reviewQueueCount.value = append ? reviewQueueCount.value : 0
    uni.showToast({ title: '审核队列加载失败，请先确认数据库迁移已执行', icon: 'none' })
  } finally {
    reviewQueueLoading.value = false
  }
}

function buildReviewQueueParams() {
  const params = buildQuestionListParams()
  delete params.status
  delete params.review_status
  delete params.exclude_review_status
  return params
}

function closeReviewQueue() {
  if (reviewEditing.value) {
    uni.showModal({
      title: '放弃未保存编辑？',
      content: '关闭审核队列会丢弃当前题目的未保存修改。',
      confirmText: '关闭',
      confirmColor: '#ef4444',
      success: (result) => {
        if (!result.confirm) return
        reviewQueueVisible.value = false
        reviewEditing.value = false
      }
    })
    return
  }
  reviewQueueVisible.value = false
}

function syncReviewForm() {
  const question = activeReviewQuestion.value
  if (!question) {
    resetReviewForm()
    return
  }
  reviewForm.id = question.id || ''
  reviewForm.exam_code = question.exam_code || ''
  reviewForm.subject = question.subject || ''
  reviewForm.module = question.module || ''
  reviewForm.submodule = question.submodule || ''
  reviewForm.stem = question.stem || ''
  reviewForm.option_a = question.option_a || ''
  reviewForm.option_b = question.option_b || ''
  reviewForm.option_c = question.option_c || ''
  reviewForm.option_d = question.option_d || ''
  reviewForm.answer = reviewAnswerOptions.includes(question.answer) ? question.answer : 'A'
  reviewForm.explanation = question.explanation || ''
  reviewForm.difficulty = Number(question.difficulty || 2)
  reviewForm.review_note = question.review_note || ''
}

function resetReviewForm() {
  reviewForm.id = ''
  reviewForm.exam_code = ''
  reviewForm.subject = ''
  reviewForm.module = ''
  reviewForm.submodule = ''
  reviewForm.stem = ''
  reviewForm.option_a = ''
  reviewForm.option_b = ''
  reviewForm.option_c = ''
  reviewForm.option_d = ''
  reviewForm.answer = 'A'
  reviewForm.explanation = ''
  reviewForm.difficulty = 2
  reviewForm.review_note = ''
}

function startReviewEditing() {
  syncReviewForm()
  reviewEditing.value = true
}

function cancelReviewEditing() {
  syncReviewForm()
  reviewEditing.value = false
}

function reviewCurrentAnswer() {
  if (reviewEditing.value) return reviewForm.answer || 'A'
  return activeReviewQuestion.value?.answer || 'A'
}

function setReviewAnswer(answer) {
  if (!reviewEditing.value || !reviewAnswerOptions.includes(answer)) return
  reviewForm.answer = answer
}

function buildReviewEditPayload() {
  const payload = {
    exam_code: reviewForm.exam_code,
    subject: reviewForm.subject,
    module: reviewForm.module,
    submodule: reviewForm.submodule,
    stem: reviewForm.stem,
    option_a: reviewForm.option_a,
    option_b: reviewForm.option_b,
    option_c: reviewForm.option_c,
    option_d: reviewForm.option_d,
    answer: reviewForm.answer,
    explanation: reviewForm.explanation,
    difficulty: Number(reviewForm.difficulty)
  }
  const requiredFields = ['exam_code', 'subject', 'module', 'submodule', 'stem', 'option_a', 'option_b', 'option_c', 'option_d', 'answer']
  const missingField = requiredFields.find((field) => !String(payload[field] || '').trim())
  if (missingField) {
    uni.showToast({ title: '请补全题干、分类、选项和答案', icon: 'none' })
    return null
  }
  if (!reviewAnswerOptions.includes(payload.answer)) {
    uni.showToast({ title: '请选择正确答案', icon: 'none' })
    return null
  }
  if (!Number.isInteger(payload.difficulty) || payload.difficulty < 1 || payload.difficulty > 5) {
    uni.showToast({ title: '难度必须为 1-5', icon: 'none' })
    return null
  }
  return payload
}

async function saveReviewEdits({ silent = false } = {}) {
  if (!activeReviewQuestion.value?.id) return false
  const payload = buildReviewEditPayload()
  if (!payload) return false
  const currentReviewNote = reviewForm.review_note
  reviewSaving.value = true
  try {
    const response = await updateAdminQuestion(activeReviewQuestion.value.id, payload)
    const nextQuestion = response.question || { ...activeReviewQuestion.value, ...payload }
    updateReviewQuestionInMemory(nextQuestion)
    reviewEditing.value = false
    syncReviewForm()
    reviewForm.review_note = currentReviewNote
    if (!silent) {
      uni.showToast({ title: '题目已保存', icon: 'success' })
    }
    return true
  } catch (error) {
    uni.showToast({ title: '题目保存失败', icon: 'none' })
    return false
  } finally {
    reviewSaving.value = false
  }
}

function updateReviewQuestionInMemory(question) {
  if (!question?.id) return
  reviewQueueItems.value = reviewQueueItems.value.map((item) => (
    item.id === question.id ? { ...item, ...question } : item
  ))
  questions.value = questions.value.map((item) => (
    item.id === question.id ? { ...item, ...question } : item
  ))
}

async function publishReviewQuestion() {
  const questionId = activeReviewQuestion.value?.id
  if (!questionId || reviewSaving.value) return
  if (reviewEditing.value) {
    const saved = await saveReviewEdits({ silent: true })
    if (!saved) return
  }
  await updateReviewQuestionStatus('approved', { publish: true, successTitle: '题目已发布' })
}

function markReviewNeedsChanges() {
  if (!activeReviewQuestion.value?.id || reviewSaving.value) return
  const note = String(reviewForm.review_note || '').trim()
  if (!note) {
    uni.showToast({ title: '请先填写审核备注', icon: 'none' })
    return
  }
  uni.showModal({
    title: '标记为需修改？',
    content: '该题会下架并移出待审核队列，后续可按备注修订后再发布。',
    confirmText: '需修改',
    confirmColor: '#f97316',
    success: async (result) => {
      if (!result.confirm) return
      if (reviewEditing.value) {
        const saved = await saveReviewEdits({ silent: true })
        if (!saved) return
      }
      await updateReviewQuestionStatus('needs_changes', { publish: false, successTitle: '已标记需修改' })
    }
  })
}

async function updateReviewQuestionStatus(reviewStatus, { publish = false, successTitle = '审核状态已更新' } = {}) {
  const questionId = activeReviewQuestion.value?.id
  if (!questionId) return
  reviewSaving.value = true
  try {
    const response = await updateAdminQuestionReview(questionId, {
      review_status: reviewStatus,
      review_note: String(reviewForm.review_note || '').trim() || null,
      publish
    })
    const nextQuestion = response.question || activeReviewQuestion.value
    updateReviewQuestionInMemory(nextQuestion)
    removeReviewedQuestion(questionId)
    uni.showToast({ title: successTitle, icon: 'success' })
    await Promise.all([loadQuestionStats(), loadQuestions()])
  } catch (error) {
    uni.showToast({ title: '审核状态更新失败', icon: 'none' })
  } finally {
    reviewSaving.value = false
  }
}

function removeReviewedQuestion(questionId) {
  reviewQueueItems.value = reviewQueueItems.value.filter((item) => item.id !== questionId)
  reviewQueueCount.value = Math.max(0, reviewQueueCount.value - 1)
  if (reviewQueueIndex.value >= reviewQueueItems.value.length) {
    reviewQueueIndex.value = Math.max(0, reviewQueueItems.value.length - 1)
  }
  reviewEditing.value = false
  syncReviewForm()
}

function goReviewPrev() {
  if (reviewEditing.value) {
    uni.showToast({ title: '请先保存或取消编辑', icon: 'none' })
    return
  }
  if (reviewQueueIndex.value <= 0) return
  reviewQueueIndex.value -= 1
  syncReviewForm()
}

async function goReviewNext() {
  if (reviewEditing.value) {
    uni.showToast({ title: '请先保存或取消编辑', icon: 'none' })
    return
  }
  if (reviewQueueIndex.value < reviewQueueItems.value.length - 1) {
    reviewQueueIndex.value += 1
    syncReviewForm()
    return
  }
  if (reviewQueueItems.value.length < reviewQueueCount.value) {
    await loadReviewQueue({ append: true })
    if (reviewQueueIndex.value < reviewQueueItems.value.length - 1) {
      reviewQueueIndex.value += 1
      syncReviewForm()
    }
    return
  }
  uni.showToast({ title: '已经是最后一题', icon: 'none' })
}

function previewQuestionStem(stem) {
  const text = String(stem || '未填写题干').replace(/\s+/g, ' ').trim()
  if (text.length <= 58) return text
  return `${text.slice(0, 58)}...`
}

function questionStatusTone(status) {
  if (status === 'archived') return 'archived'
  if (status === 'pending' || status === 'pending_review') return 'pending'
  if (status === 'needs_review' || status === 'rejected') return 'warning'
  return 'published'
}

function questionDisplayStatus(question) {
  if (question?.review_status === 'pending') return QUESTION_STATUS_PENDING_REVIEW
  return question?.status
}

function getQuestionBulkSelectionStatus(status) {
  if (
    status === QUESTION_STATUS_ACTIVE ||
    status === QUESTION_STATUS_ARCHIVED ||
    status === QUESTION_STATUS_PENDING_REVIEW
  ) {
    return status
  }
  return ''
}

function reviewStatusTone(status) {
  if (status === 'approved') return 'published'
  if (status === 'needs_changes' || status === 'rejected') return 'warning'
  return 'pending'
}

function isQuestionSelected(id) {
  return allMatchingQuestionsSelected.value || selectedQuestionIdSet.value.has(id)
}

function toggleQuestionSelection(id) {
  if (!id) return
  if (allMatchingQuestionsSelected.value) {
    allMatchingQuestionsSelected.value = false
    bulkSelectionStatus.value = ''
    selectedQuestionIds.value = questions.value
      .map((item) => item.id)
      .filter((itemId) => itemId && itemId !== id)
    return
  }
  if (selectedQuestionIdSet.value.has(id)) {
    selectedQuestionIds.value = selectedQuestionIds.value.filter((item) => item !== id)
    return
  }
  selectedQuestionIds.value = [...selectedQuestionIds.value, id]
}

function toggleSelectAllQuestions() {
  if (allMatchingQuestionsSelected.value || allVisibleQuestionsSelected.value) {
    clearQuestionSelection()
    return
  }
  if (questionListCount.value === 0) {
    uni.showToast({ title: '当前没有可选题目', icon: 'none' })
    return
  }
  const nextBulkSelectionStatus = currentBulkSelectionStatus.value ||
    getQuestionBulkSelectionStatus(questionFilters.status)
  if (!nextBulkSelectionStatus) {
    uni.showToast({ title: '请先筛选状态或勾选同一状态题目', icon: 'none' })
    return
  }
  const shouldApplyDerivedStatusFilter = !questionFilters.status && nextBulkSelectionStatus
  if (shouldApplyDerivedStatusFilter) {
    questionFilters.status = nextBulkSelectionStatus
  }
  bulkSelectionStatus.value = nextBulkSelectionStatus
  allMatchingQuestionsSelected.value = true
  selectedQuestionIds.value = []
  uni.showToast({ title: '已全选当前状态题目', icon: 'none' })
  if (shouldApplyDerivedStatusFilter) {
    loadQuestions()
  }
}

function archiveSelectedQuestions() {
  if (!canBulkArchiveQuestions.value) {
    uni.showToast({ title: '只有已发布题目可以批量下架', icon: 'none' })
    return
  }
  updateSelectedQuestionStatus('archived')
}

function publishSelectedQuestions() {
  if (!canBulkPublishQuestions.value) {
    uni.showToast({ title: '请先筛选已下架或待审核题目', icon: 'none' })
    return
  }
  updateSelectedQuestionStatus('active')
}

function updateSelectedQuestionStatus(nextStatus) {
  const ids = [...selectedQuestionIds.value]
  const totalSelected = selectedQuestionCount.value
  if (totalSelected === 0) {
    uni.showToast({ title: '请先选择题目', icon: 'none' })
    return
  }
  const isArchive = nextStatus === 'archived'
  const isReviewPublish = nextStatus === 'active' &&
    currentBulkSelectionStatus.value === QUESTION_STATUS_PENDING_REVIEW
  const scopeText = allMatchingQuestionsSelected.value ? questionFilterScopeText() : '手动选择'
  uni.showModal({
    title: isArchive ? '确认下架所选题目？' : (isReviewPublish ? '确认审核通过并发布？' : '确认发布所选题目？'),
    content: isArchive
      ? `将下架${scopeText}的 ${totalSelected} 道题，下架后不会进入普通刷题抽题。`
      : (isReviewPublish
          ? `将${scopeText}的 ${totalSelected} 道题标为审核通过，并进入可刷题范围。`
          : `将发布${scopeText}的 ${totalSelected} 道题，发布后会进入可刷题范围。`),
    confirmText: isArchive ? '下架' : (isReviewPublish ? '审核发布' : '发布'),
    confirmColor: isArchive ? '#16a34a' : '#2563eb',
    success: async (result) => {
      if (!result.confirm) return
      try {
        const payload = allMatchingQuestionsSelected.value
          ? { status: nextStatus, filters: buildQuestionFilterPayload() }
          : { status: nextStatus, ids }
        const response = await bulkUpdateAdminQuestionStatus(payload)
        clearQuestionSelection()
        uni.showToast({
          title: `${isArchive ? '已下架' : '已发布'} ${response?.updated_count || totalSelected} 道`,
          icon: 'success'
        })
        await refreshQuestionManager()
      } catch (error) {
        uni.showToast({ title: '批量状态更新失败', icon: 'none' })
      }
    }
  })
}

function buildQuestionFilterPayload() {
  const params = buildQuestionListParams()
  if (allMatchingQuestionsSelected.value) {
    applyQuestionStatusParams(
      params,
      bulkSelectionStatus.value || getQuestionBulkSelectionStatus(questionFilters.status)
    )
  }
  if (params.difficulty) {
    params.difficulty = Number(params.difficulty)
  }
  return params
}

function questionFilterScopeText() {
  const labels = []
  if (questionFilters.subject) labels.push(questionFilters.subject)
  if (questionFilters.module) labels.push(questionFilters.module)
  if (questionFilters.difficulty) labels.push(`难度 ${questionFilters.difficulty}`)
  const statusScope = bulkSelectionStatus.value || questionFilters.status
  if (statusScope) labels.push(questionStatusText(statusScope))
  if (questionFilters.search) labels.push(`包含“${questionFilters.search}”`)
  if (labels.length === 0) return '全部题库'
  return `当前筛选（${labels.join(' / ')}）`
}

async function loadMessages() {
  messagesLoading.value = true
  try {
    const response = await fetchAdminMessages({ limit: 50, offset: 0 })
    officialMessageItems.value = response.items || []
  } catch (error) {
    uni.showToast({ title: '消息加载失败', icon: 'none' })
  } finally {
    messagesLoading.value = false
  }
}

function resetMessageForm() {
  messageForm.id = ''
  messageForm.title = ''
  messageForm.content = ''
  messageForm.status = 'draft'
  messageForm.expires_at = ''
}

function editOfficialMessage(item) {
  messageForm.id = item.id || ''
  messageForm.title = item.title || ''
  messageForm.content = item.content || ''
  messageForm.status = item.status || 'draft'
  messageForm.expires_at = item.expires_at || ''
}

function messageStatusText(status) {
  const map = {
    draft: '草稿',
    published: '已发布',
    archived: '已归档'
  }
  return map[status] || '草稿'
}

async function saveOfficialMessage() {
  if (!messageForm.title || !messageForm.content) {
    uni.showToast({ title: '请填写标题和内容', icon: 'none' })
    return
  }
  const payload = {
    title: messageForm.title,
    content: messageForm.content,
    status: messageForm.status,
    expires_at: messageForm.expires_at || null
  }
  try {
    if (messageForm.id) {
      await updateAdminMessage(messageForm.id, payload)
      uni.showToast({ title: '消息已保存', icon: 'success' })
    } else {
      await createAdminMessage(payload)
      uni.showToast({ title: payload.status === 'published' ? '消息已发布' : '消息已创建', icon: 'success' })
    }
    resetMessageForm()
    await loadMessages()
  } catch (error) {
    uni.showToast({ title: '消息保存失败', icon: 'none' })
  }
}

function openMembershipActions(user) {
  const isActiveMember = user.membership_status === 'active'
  const itemList = isActiveMember
    ? ['续期 1 个月', '续期 3 个月', '续期 6 个月', '续期 12 个月', '取消会员']
    : ['开通 1 个月', '开通 3 个月', '开通 6 个月', '开通 12 个月']

  uni.showActionSheet({
    itemList,
    success: async ({ tapIndex }) => {
      if (isActiveMember && tapIndex === 4) {
        await confirmCancelMembership(user)
        return
      }
      const months = [1, 3, 6, 12][tapIndex] || 1
      await grantMembership(user, months, isActiveMember)
    }
  })
}

function membershipActionLabel(user) {
  return user.membership_status === 'active' ? '管理会员' : '开通会员'
}

async function grantMembership(user, months, isRenewal = false) {
  try {
    await grantAdminMembership(user.id, { months, plan: `admin_${months}_month` })
    uni.showToast({ title: isRenewal ? '会员已续期' : '会员已授权', icon: 'success' })
    await Promise.all([loadUsers(), loadOverview()])
  } catch (error) {
    uni.showToast({ title: isRenewal ? '续期失败' : '授权失败', icon: 'none' })
  }
}

function confirmCancelMembership(user) {
  return new Promise((resolve) => {
    uni.showModal({
      title: '确认取消会员？',
      content: `将取消 ${user.email || user.phone || '该用户'} 的会员权益。取消后不会删除用户账号和刷题记录。`,
      confirmText: '取消会员',
      confirmColor: '#ef4444',
      success: async (result) => {
        if (!result.confirm) {
          resolve(false)
          return
        }
        try {
          await cancelAdminMembership(user.id)
          uni.showToast({ title: '会员已取消', icon: 'success' })
          await Promise.all([loadUsers(), loadOverview()])
          resolve(true)
        } catch (error) {
          uni.showToast({ title: '取消失败', icon: 'none' })
          resolve(false)
        }
      },
      fail: () => resolve(false)
    })
  })
}

async function openUser(user) {
  try {
    const detail = await fetchAdminUserDetail(user.id)
    const profile = detail.profile || user
    const summary = detail.answer_summary || {}
    const latestOrder = (detail.membership_orders || [])[0]
    const latestMembershipAction = (detail.admin_actions || []).find((action) => (
      action.action === 'grant_membership' || action.action === 'cancel_membership'
    ))
    const content = [
      `账号：${profile.email || profile.phone || '未绑定'}`,
      `昵称：${profile.nickname || '未设置'}`,
      `目标：${profile.exam_target || '未设置'}`,
      `角色：${profile.role || 'user'}`,
      `会员：${profile.membership_status || 'inactive'}`,
      profile.membership_expires_at ? `到期：${formatDate(profile.membership_expires_at)}` : '',
      `累计作答：${summary.total || 0} 题，正确 ${summary.correct || 0} 题，正确率 ${summary.accuracy || 0}%`,
      latestOrder ? `最近订单：${latestOrder.plan_code || '-'} / ${latestOrder.status || '-'}` : '暂无会员订单记录',
      latestMembershipAction ? `最近后台操作：${membershipActionText(latestMembershipAction)} / ${formatDate(latestMembershipAction.created_at)}` : '暂无后台会员操作记录'
    ].filter(Boolean).join('\n')
    uni.showModal({ title: '用户详情', content, showCancel: false, confirmText: '关闭' })
  } catch (error) {
    uni.showToast({ title: '用户详情加载失败', icon: 'none' })
  }
}

function membershipActionText(action) {
  if (action.action === 'cancel_membership') return '取消会员'
  return `授权 ${action.details?.months || '-'} 个月`
}

function feedbackStatusText(status) {
  const map = {
    open: '待处理',
    reviewed: '已查看',
    resolved: '已解决',
    ignored: '忽略'
  }
  return map[status] || '待处理'
}

function questionStatusText(status) {
  const map = {
    active: '已发布',
    archived: '已下架',
    pending: '待审核',
    pending_review: '待审核',
    needs_review: '需修改',
    rejected: '需修改'
  }
  return map[status] || '待审核'
}

function reviewStatusText(status) {
  const map = {
    pending: '待审核',
    needs_changes: '需修改',
    approved: '已审核',
    rejected: '已拒绝'
  }
  return map[status] || '待审核'
}

async function openFeedback(item) {
  let latest = item
  try {
    // The list already contains full rows; keep this lightweight for now.
    latest = item
  } catch (error) {
    latest = item
  }
  uni.showModal({
    title: latest.feedback_type || '用户反馈',
    content: `${latest.content || ''}\n\n状态：${feedbackStatusText(latest.status)}\n联系方式：${latest.contact || '未填写'}\n备注：${latest.admin_note || '无'}`,
    showCancel: false,
    confirmText: '知道了'
  })
}

function openFeedbackStatusAction(item) {
  uni.showActionSheet({
    itemList: ['标记已查看', '标记已解决', '标记忽略', '重新打开'],
    success: async ({ tapIndex }) => {
      const statuses = ['reviewed', 'resolved', 'ignored', 'open']
      const nextStatus = statuses[tapIndex] || 'reviewed'
      try {
        await updateAdminFeedbackStatus(item.id, { status: nextStatus })
        uni.showToast({ title: '反馈状态已更新', icon: 'success' })
        await Promise.all([loadFeedback(), loadOverview()])
      } catch (error) {
        uni.showToast({ title: '状态更新失败', icon: 'none' })
      }
    }
  })
}

async function openQuestion(item) {
  let question = item
  try {
    const response = await fetchAdminQuestionDetail(item.id)
    question = response.question || item
  } catch (error) {
    question = item
  }
  const content = [
    question.stem,
    `A. ${question.option_a}`,
    `B. ${question.option_b}`,
    `C. ${question.option_c}`,
    `D. ${question.option_d}`,
    `答案：${question.answer}`,
    `状态：${questionStatusText(question.status)}`,
    question.explanation ? `解析：${question.explanation}` : ''
  ].filter(Boolean).join('\n')
  uni.showModal({
    title: `${question.subject || '题目'}详情`,
    content,
    showCancel: false,
    confirmText: '关闭'
  })
}

function toggleQuestionStatus(item) {
  const nextStatus = item.status === 'archived' ? 'active' : 'archived'
  uni.showModal({
    title: nextStatus === 'archived' ? '确认下架题目？' : '确认恢复题目？',
    content: nextStatus === 'archived'
      ? '下架后，该题不会再进入普通刷题抽题，但历史记录仍保留。'
      : '恢复后，该题会重新进入普通刷题抽题范围。',
    confirmText: nextStatus === 'archived' ? '下架' : '恢复',
    confirmColor: nextStatus === 'archived' ? '#ef4444' : '#16a34a',
    success: async (result) => {
      if (!result.confirm) return
      try {
        await updateAdminQuestionStatus(item.id, { status: nextStatus })
        uni.showToast({ title: nextStatus === 'archived' ? '题目已下架' : '题目已发布', icon: 'success' })
        await refreshQuestionManager()
      } catch (error) {
        uni.showToast({ title: '题目状态更新失败', icon: 'none' })
      }
    }
  })
}

function formatDate(value) {
  if (!value) return '无日期'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return String(value).slice(0, 10)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

function goBack() {
  if (questionCreateMode.value) {
    closeCreateQuestion()
    return
  }
  uni.navigateBack({
    fail() {
      uni.redirectTo({ url: '/pages/home/index?tab=profile' })
    }
  })
}
</script>

<style scoped>
.admin-page {
  min-height: 100vh;
  padding: 24rpx 24rpx 170rpx;
  background: linear-gradient(180deg, #eef5ff 0%, #f6f8fb 28%, #f6f8fb 100%);
  box-sizing: border-box;
}

.admin-page.question-mode {
  padding-bottom: calc(env(safe-area-inset-bottom) + 310rpx);
  background:
    radial-gradient(circle at 12% 0%, rgba(186, 226, 255, 0.72) 0, rgba(186, 226, 255, 0) 300rpx),
    radial-gradient(circle at 92% 2%, rgba(205, 249, 216, 0.78) 0, rgba(205, 249, 216, 0) 320rpx),
    linear-gradient(180deg, #f7fbff 0%, #ffffff 48%, #f7fbff 100%);
}

.admin-hero {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100rpx;
  padding: 2rpx 96rpx 12rpx;
  margin-bottom: 12rpx;
  box-sizing: border-box;
}

.back-btn {
  position: absolute;
  left: 0;
  top: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 70rpx;
  height: 70rpx;
  padding: 0;
  transform: translateY(-50%);
  border-radius: 22rpx;
  border: 0;
  background: #ffffff;
  box-shadow: 0 14rpx 34rpx rgba(15, 23, 42, 0.08);
}

.back-icon {
  width: 30rpx;
  height: 30rpx;
  display: block;
}

.back-btn::after,
.hero-refresh-btn::after,
.tab-btn::after,
.ghost-btn::after,
.search-btn::after,
.small-btn::after,
.status-chip::after,
.question-action-btn::after,
.question-check::after,
.question-edit-btn::after,
.question-bulk-btn::after,
.create-difficulty-btn::after,
.create-footer-btn::after,
.review-close-btn::after,
.review-mini-btn::after,
.review-difficulty-btn::after,
.review-footer-btn::after {
  border: 0;
}

.hero-refresh-btn {
  position: absolute;
  right: 0;
  top: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 70rpx;
  height: 70rpx;
  margin: 0;
  transform: translateY(-50%);
  border: 0;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.68);
  color: #101828;
  font-size: 44rpx;
  line-height: 1;
  box-shadow: none;
}

.admin-heading {
  min-width: 0;
  text-align: center;
}

.admin-title {
  color: #101828;
  font-size: 38rpx;
  font-weight: 900;
  line-height: 1.2;
}

.admin-subtitle {
  margin-top: 8rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.35;
}

.state-card,
.panel-card {
  border-radius: 28rpx;
  background: #ffffff;
  border: 1rpx solid #e6edf6;
  box-shadow: 0 20rpx 50rpx rgba(15, 23, 42, 0.06);
}

.state-card {
  padding: 48rpx 34rpx;
  color: #667085;
  font-size: 28rpx;
}

.state-card.denied {
  color: #b42318;
  background: #fff7f5;
}

.state-title {
  color: #101828;
  font-size: 32rpx;
  font-weight: 900;
}

.state-copy {
  margin-top: 12rpx;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
  margin-bottom: 12rpx;
}

.stat-card {
  min-height: 118rpx;
  padding: 20rpx 22rpx;
  border-radius: 22rpx;
  background: #ffffff;
  border: 1rpx solid #e6edf6;
  box-sizing: border-box;
}

.stat-card.primary:first-child {
  background: linear-gradient(135deg, #ffffff 0%, #eff6ff 100%);
  border-color: #d7e6ff;
}

.stat-label {
  color: #667085;
  font-size: 24rpx;
  line-height: 1.25;
}

.stat-value {
  margin-top: 8rpx;
  color: #101828;
  font-size: 38rpx;
  font-weight: 900;
  line-height: 1.1;
}

.metric-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8rpx;
  margin-bottom: 18rpx;
  padding: 10rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.74);
  border: 1rpx solid #e6edf6;
}

.metric-item {
  min-width: 0;
  text-align: center;
}

.metric-label {
  display: block;
  color: #667085;
  font-size: 19rpx;
  line-height: 1.2;
}

.metric-value {
  display: block;
  margin-top: 4rpx;
  color: #101828;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1.15;
}

.tab-bar {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0;
  margin-bottom: 20rpx;
  padding: 8rpx;
  border-radius: 24rpx;
  background: #ffffff;
  border: 1rpx solid #e6edf6;
  box-shadow: 0 12rpx 28rpx rgba(15, 23, 42, 0.05);
}

.tab-btn,
.ghost-btn,
.search-btn,
.small-btn {
  border: 0;
  border-radius: 20rpx;
  font-weight: 800;
}

.tab-btn {
  height: 60rpx;
  border-radius: 18rpx;
  color: #475467;
  background: transparent;
  font-size: 25rpx;
  box-shadow: none;
}

.tab-btn.active {
  color: #ffffff;
  background: #3b82f6;
  box-shadow: 0 10rpx 22rpx rgba(59, 130, 246, 0.24);
}

.panel-card {
  padding: 26rpx;
}

.panel-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
  margin-bottom: 22rpx;
}

.panel-head > view {
  min-width: 0;
  flex: 1;
}

.panel-head.compact {
  margin-top: 26rpx;
  margin-bottom: 14rpx;
}

.panel-title {
  color: #101828;
  font-size: 30rpx;
  font-weight: 900;
}

.panel-title.small {
  font-size: 26rpx;
}

.panel-subtitle {
  margin-top: 6rpx;
  color: #667085;
  font-size: 22rpx;
}

.ghost-btn {
  height: 56rpx;
  min-width: 96rpx;
  padding: 0 20rpx;
  color: #2563eb;
  background: #eff6ff;
  font-size: 24rpx;
  box-shadow: 0 8rpx 20rpx rgba(37, 99, 235, 0.08);
}

.refresh-btn {
  flex: 0 0 auto;
  height: 58rpx;
  min-width: 100rpx;
  margin-top: 2rpx;
  border-radius: 18rpx;
}

.search-row {
  display: flex;
  gap: 14rpx;
  align-items: center;
  margin-bottom: 14rpx;
}

.filter-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10rpx;
  margin-bottom: 22rpx;
}

.filter-chip {
  height: 52rpx;
  border: 0;
  border-radius: 16rpx;
  color: #475467;
  background: #f3f6fb;
  font-size: 22rpx;
  font-weight: 800;
}

.filter-chip::after {
  border: 0;
}

.filter-chip.active {
  color: #2563eb;
  background: #eff6ff;
}

.search-input {
  min-width: 0;
  height: 68rpx;
  padding: 0 22rpx;
  border-radius: 18rpx;
  background: #f3f6fb;
  border: 1rpx solid #dbe6f5;
  color: #101828;
  font-size: 26rpx;
  box-sizing: border-box;
}

.search-row .search-input {
  flex: 1;
}

.search-btn {
  width: 128rpx;
  height: 68rpx;
  color: #ffffff;
  background: #3b82f6;
  font-size: 26rpx;
}

.search-btn.wide {
  width: 100%;
  margin: 16rpx 0 22rpx;
}

.inline-state {
  padding: 36rpx 0;
  color: #667085;
  text-align: center;
  font-size: 26rpx;
}

.question-empty-state {
  padding: 38rpx 28rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.88);
  border: 1rpx solid rgba(211, 220, 232, 0.9);
  text-align: center;
  box-shadow: 0 14rpx 36rpx rgba(15, 23, 42, 0.05);
}

.question-empty-title {
  color: #101828;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1.35;
}

.question-empty-copy {
  margin-top: 12rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.6;
}

.question-empty-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 220rpx;
  height: 64rpx;
  margin: 24rpx auto 0;
  padding: 0;
  border-radius: 14rpx;
  color: #1769ff;
  background: #ffffff;
  border: 1rpx solid #1769ff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.record-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  padding: 22rpx;
  border-radius: 22rpx;
  background: #f8fbff;
  border: 1rpx solid #e3ebf7;
}

.feedback-card {
  display: block;
}

.record-main {
  min-width: 0;
  flex: 1;
}

.record-title {
  color: #101828;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 1.45;
  word-break: break-all;
}

.record-subtitle {
  margin-top: 6rpx;
  color: #667085;
  font-size: 22rpx;
  line-height: 1.5;
}

.clamp {
  display: -webkit-box;
  overflow: hidden;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.badge-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10rpx;
  margin-top: 12rpx;
}

.badge {
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  color: #475467;
  background: #eef2f7;
  font-size: 21rpx;
  font-weight: 800;
}

.badge.active {
  color: #15803d;
  background: #dcfce7;
}

.badge.admin {
  color: #5b21b6;
  background: #ede9fe;
}

.badge.archived {
  color: #b42318;
  background: #fee4e2;
}

.record-date {
  color: #98a2b3;
  font-size: 21rpx;
}

.small-btn {
  flex: 0 0 auto;
  width: 164rpx;
  height: 58rpx;
  color: #ffffff;
  background: #0f172a;
  font-size: 23rpx;
}

.inline-action {
  margin-top: 16rpx;
}

.filter-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
}

.question-manager {
  display: flex;
  flex-direction: column;
  gap: 22rpx;
}

.question-stats-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12rpx;
}

.question-stat-card {
  min-height: 138rpx;
  padding: 20rpx 16rpx 18rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 1rpx solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 18rpx 44rpx rgba(15, 23, 42, 0.08);
  box-sizing: border-box;
}

.question-stat-head {
  display: flex;
  align-items: center;
  gap: 10rpx;
  min-width: 0;
}

.question-stat-icon {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36rpx;
  height: 36rpx;
  color: #2563eb;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1;
}

.question-stat-image {
  width: 36rpx;
  height: 36rpx;
  display: block;
}

.question-stat-card.orange .question-stat-icon,
.question-stat-card.orange .question-stat-value {
  color: #f97316;
}

.question-stat-card.green .question-stat-icon,
.question-stat-card.green .question-stat-value {
  color: #16a34a;
}

.question-stat-label {
  min-width: 0;
  color: #344054;
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1.2;
  white-space: nowrap;
}

.question-stat-value {
  margin-top: 24rpx;
  color: #1d4ed8;
  font-size: 40rpx;
  font-weight: 900;
  line-height: 1;
}

.question-search-box {
  display: flex;
  align-items: center;
  gap: 16rpx;
  height: 78rpx;
  padding: 0 24rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.9);
  border: 1rpx solid #d5deeb;
  box-shadow: inset 0 1rpx 0 rgba(255, 255, 255, 0.8);
  box-sizing: border-box;
}

.question-search-icon {
  flex: 0 0 auto;
  color: #98a2b3;
  font-size: 42rpx;
  line-height: 1;
}

.question-search-input {
  min-width: 0;
  flex: 1;
  height: 78rpx;
  color: #101828;
  font-size: 27rpx;
  line-height: 78rpx;
}

.question-filter-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12rpx;
}

.question-filter-row picker {
  min-width: 0;
}

.question-filter-pill {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  height: 64rpx;
  padding: 0 10rpx;
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.84);
  border: 1rpx solid #d5deeb;
  color: #344054;
  font-size: 24rpx;
  font-weight: 800;
  line-height: 1;
  box-sizing: border-box;
  white-space: nowrap;
}

.question-filter-arrow {
  color: #667085;
  font-size: 22rpx;
  transform: translateY(-2rpx);
}

.question-action-row {
  display: grid;
  grid-template-columns: 1fr 1fr 1.28fr;
  gap: 12rpx;
}

.question-action-row.compact {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.question-action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  min-width: 0;
  height: 70rpx;
  margin: 0;
  padding: 0 10rpx;
  border-radius: 12rpx;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 1;
  box-sizing: border-box;
}

.question-action-btn.outline {
  color: #1769ff;
  background: rgba(255, 255, 255, 0.92);
  border: 1rpx solid #1769ff;
}

.question-action-btn.filled {
  color: #ffffff;
  background: linear-gradient(135deg, #0ea5b7 0%, #0891b2 100%);
  border: 1rpx solid #0891b2;
  box-shadow: 0 16rpx 30rpx rgba(8, 145, 178, 0.2);
}

.question-action-icon {
  font-size: 30rpx;
  font-weight: 900;
  line-height: 1;
}

.question-card-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  padding-bottom: 170rpx;
}

.question-admin-card {
  display: grid;
  grid-template-columns: 42rpx minmax(0, 1fr) 122rpx;
  align-items: center;
  column-gap: 16rpx;
  min-height: 150rpx;
  padding: 24rpx 22rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid #edf2f7;
  box-shadow: 0 14rpx 38rpx rgba(15, 23, 42, 0.07);
  box-sizing: border-box;
}

.question-check {
  grid-column: 1;
  grid-row: 1;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 34rpx;
  height: 34rpx;
  margin: 0;
  padding: 0;
  border-radius: 8rpx;
  border: 1rpx solid #98a2b3;
  background: #ffffff;
  color: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1;
}

.question-check.checked {
  border-color: #1769ff;
  background: #1769ff;
}

.question-card-main {
  grid-column: 2;
  grid-row: 1;
  min-width: 0;
  flex: 1;
}

.question-chip-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10rpx;
}

.question-chip {
  max-width: 180rpx;
  padding: 7rpx 13rpx;
  border-radius: 10rpx;
  color: #1769ff;
  background: #eff6ff;
  font-size: 22rpx;
  font-weight: 900;
  line-height: 1.15;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.question-stem-preview {
  margin-top: 16rpx;
  color: #101828;
  font-size: 26rpx;
  font-weight: 800;
  line-height: 1.45;
  word-break: break-word;
}

.question-status-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 16rpx;
}

.question-status-pill {
  padding: 8rpx 14rpx;
  border-radius: 12rpx;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 1;
}

.question-status-pill.published {
  color: #16a34a;
  background: #dcfce7;
}

.question-status-pill.archived {
  color: #64748b;
  background: #f1f5f9;
}

.question-status-pill.pending {
  color: #f97316;
  background: #fff7ed;
}

.question-status-pill.warning {
  color: #ea580c;
  background: #ffedd5;
}

.question-answer {
  color: #98a2b3;
  font-size: 22rpx;
  font-weight: 700;
}

.question-edit-btn {
  grid-column: 3;
  grid-row: 1;
  flex: 0 0 auto;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  width: 122rpx;
  height: 60rpx;
  margin: 0;
  padding: 0;
  border-radius: 12rpx;
  border: 1rpx solid #1769ff;
  color: #1769ff;
  background: #ffffff;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1;
}

.question-edit-icon {
  font-size: 26rpx;
  line-height: 1;
}

.question-bulk-bar {
  position: fixed;
  left: 24rpx;
  right: 24rpx;
  bottom: calc(env(safe-area-inset-bottom) + 14rpx);
  z-index: 30;
  display: grid;
  grid-template-columns: 0.85fr 1fr;
  align-items: center;
  gap: 10rpx;
  min-height: 78rpx;
  padding: 12rpx 18rpx;
  border-radius: 18rpx;
  background: rgba(255, 255, 255, 0.96);
  border: 1rpx solid #edf2f7;
  box-shadow: 0 12rpx 44rpx rgba(15, 23, 42, 0.12);
  box-sizing: border-box;
}

.question-bulk-bar.with-status-action {
  grid-template-columns: 0.85fr 1fr 0.9fr;
}

.question-bulk-bar.selection-only {
  grid-template-columns: 0.85fr 1fr;
}

.question-bulk-bar.idle {
  background: rgba(255, 255, 255, 0.9);
  box-shadow: 0 10rpx 32rpx rgba(15, 23, 42, 0.08);
}

.question-selected-label {
  min-width: 0;
  color: #475467;
  font-size: 22rpx;
  font-weight: 700;
  white-space: nowrap;
}

.question-selected-count {
  color: #1769ff;
  font-size: 32rpx;
  font-weight: 900;
}

.question-bulk-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  min-width: 0;
  height: 56rpx;
  margin: 0;
  padding: 0 10rpx;
  border-radius: 12rpx;
  border: 1rpx solid #1769ff;
  color: #1769ff;
  background: #ffffff;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 1;
  box-sizing: border-box;
}

.question-bulk-btn.archive {
  color: #16a34a;
  border-color: #16a34a;
}

.question-bulk-btn.publish {
  color: #1769ff;
  border-color: #1769ff;
}

.question-bulk-icon {
  font-size: 24rpx;
  line-height: 1;
}

.question-bulk-image {
  width: 26rpx;
  height: 26rpx;
  display: block;
  flex: 0 0 26rpx;
}

.question-create-page {
  padding-bottom: 130rpx;
}

.question-create-card {
  padding: 28rpx 24rpx 30rpx;
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.94);
  border: 1rpx solid rgba(226, 232, 240, 0.92);
  box-shadow: 0 18rpx 48rpx rgba(15, 23, 42, 0.08);
  box-sizing: border-box;
}

.create-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.create-field {
  min-width: 0;
}

.create-field.full {
  margin-top: 22rpx;
}

.create-label,
.create-section-title {
  color: #101828;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 1.2;
}

.create-picker {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
  height: 68rpx;
  margin-top: 14rpx;
  padding: 0 20rpx;
  border-radius: 14rpx;
  border: 1rpx solid #cfd8e3;
  background: rgba(255, 255, 255, 0.92);
  color: #101828;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1;
  box-sizing: border-box;
}

.create-picker text:first-child {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.create-picker-arrow {
  flex: 0 0 auto;
  color: #667085;
  font-size: 28rpx;
  line-height: 1;
  transform: translateY(-2rpx);
}

.create-difficulty-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  margin-top: 14rpx;
  border-radius: 14rpx;
  border: 1rpx solid #cfd8e3;
  overflow: hidden;
}

.create-difficulty-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 62rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-right: 1rpx solid #cfd8e3;
  border-radius: 0;
  color: #101828;
  background: #ffffff;
  font-size: 27rpx;
  font-weight: 700;
  line-height: 1;
}

.create-difficulty-btn:last-child {
  border-right: 0;
}

.create-difficulty-btn.active {
  color: #ffffff;
  background: linear-gradient(135deg, #1769ff 0%, #0f5fe8 100%);
  box-shadow: 0 10rpx 22rpx rgba(23, 105, 255, 0.22);
}

.create-divider {
  height: 1rpx;
  margin: 28rpx 0;
  background: #e4eaf2;
}

.create-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-top: 26rpx;
}

.create-section-head:first-of-type {
  margin-top: 0;
}

.create-section-head.options {
  justify-content: flex-start;
  flex-wrap: wrap;
}

.create-required-tag,
.create-suggest-tag {
  flex: 0 0 auto;
  padding: 7rpx 12rpx;
  border-radius: 8rpx;
  color: #f97316;
  background: #fff7ed;
  font-size: 22rpx;
  font-weight: 800;
  line-height: 1;
}

.create-section-hint {
  color: #667085;
  font-size: 22rpx;
  font-weight: 700;
  line-height: 1.3;
}

.create-textarea {
  width: 100%;
  margin-top: 14rpx;
  padding: 20rpx 22rpx;
  border-radius: 14rpx;
  border: 1rpx solid #cfd8e3;
  background: rgba(255, 255, 255, 0.94);
  color: #101828;
  font-size: 25rpx;
  line-height: 1.55;
  letter-spacing: 0;
  box-sizing: border-box;
}

.create-textarea.stem {
  min-height: 176rpx;
}

.create-textarea.explanation {
  min-height: 154rpx;
}

.create-option-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
  margin-top: 14rpx;
}

.create-option-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
  min-height: 68rpx;
  padding: 0 18rpx;
  border-radius: 12rpx;
  border: 1rpx solid #d5deeb;
  background: rgba(255, 255, 255, 0.94);
  box-sizing: border-box;
}

.create-option-row.selected {
  border-color: #1769ff;
  background: #f8fbff;
  box-shadow: inset 0 0 0 1rpx rgba(23, 105, 255, 0.18);
}

.create-radio {
  flex: 0 0 30rpx;
  width: 30rpx;
  color: #1769ff;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1;
  text-align: center;
}

.create-option-label {
  flex: 0 0 38rpx;
  color: #101828;
  font-size: 26rpx;
  font-weight: 800;
  line-height: 1;
}

.create-option-input {
  min-width: 0;
  flex: 1;
  height: 66rpx;
  color: #101828;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 66rpx;
}

.question-create-footer {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 40;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 18rpx;
  padding: 18rpx 28rpx calc(env(safe-area-inset-bottom) + 18rpx);
  background: rgba(255, 255, 255, 0.96);
  border-top: 1rpx solid #edf2f7;
  box-shadow: 0 -12rpx 36rpx rgba(15, 23, 42, 0.08);
  box-sizing: border-box;
}

.create-footer-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12rpx;
  height: 72rpx;
  margin: 0;
  padding: 0 14rpx;
  border-radius: 14rpx;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1;
  text-align: center;
  box-sizing: border-box;
}

.create-footer-btn.outline {
  color: #1769ff;
  background: #ffffff;
  border: 1rpx solid #1769ff;
}

.create-footer-btn.primary {
  color: #ffffff;
  background: linear-gradient(135deg, #1769ff 0%, #0f5fe8 100%);
  border: 1rpx solid #1769ff;
  box-shadow: 0 14rpx 28rpx rgba(23, 105, 255, 0.22);
}

.create-footer-btn[disabled] {
  opacity: 0.58;
}

.create-footer-icon {
  font-size: 34rpx;
  font-weight: 900;
  line-height: 1;
}

.review-overlay {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 90;
  display: flex;
  align-items: flex-end;
  background: rgba(15, 23, 42, 0.16);
  backdrop-filter: blur(10rpx);
}

.review-sheet {
  display: flex;
  flex-direction: column;
  width: 100%;
  max-height: calc(100vh - 128rpx);
  border-radius: 28rpx 28rpx 0 0;
  background: rgba(255, 255, 255, 0.98);
  border: 1rpx solid rgba(226, 232, 240, 0.92);
  box-shadow: 0 -16rpx 54rpx rgba(15, 23, 42, 0.16);
  overflow: hidden;
  box-sizing: border-box;
}

.review-sheet-head {
  flex: 0 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto auto;
  align-items: center;
  gap: 14rpx;
  padding: 28rpx 28rpx 20rpx;
  box-sizing: border-box;
}

.review-head-copy {
  min-width: 0;
}

.review-title {
  color: #101828;
  font-size: 34rpx;
  font-weight: 900;
  line-height: 1.15;
}

.review-subtitle {
  margin-top: 8rpx;
  color: #475467;
  font-size: 23rpx;
  font-weight: 700;
  line-height: 1.25;
}

.review-progress {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 54rpx;
  padding: 12rpx 20rpx;
  border-radius: 14rpx;
  color: #1769ff;
  background: #eff6ff;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 1;
  white-space: nowrap;
}

.review-status-pill {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 54rpx;
  padding: 12rpx 18rpx;
  border-radius: 14rpx;
  color: #f97316;
  background: #fff7ed;
  font-size: 24rpx;
  font-weight: 900;
  line-height: 1;
  white-space: nowrap;
}

.review-status-pill.published {
  color: #1769ff;
  background: #eff6ff;
}

.review-status-pill.warning {
  color: #ea580c;
  background: #ffedd5;
}

.review-close-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 58rpx;
  height: 58rpx;
  margin: 0;
  padding: 0;
  border-radius: 18rpx;
  border: 0;
  color: #344054;
  background: #f8fafc;
  font-size: 48rpx;
  line-height: 1;
}

.review-empty {
  padding: 80rpx 28rpx 100rpx;
  color: #667085;
  text-align: center;
  font-size: 27rpx;
  font-weight: 700;
}

.review-body {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  min-height: 0;
  padding: 8rpx 28rpx 24rpx;
  overflow-y: auto;
  box-sizing: border-box;
}

.review-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.review-section-head.compact {
  align-items: baseline;
  justify-content: flex-start;
  margin-top: 4rpx;
}

.review-section-title {
  color: #101828;
  font-size: 29rpx;
  font-weight: 900;
  line-height: 1.2;
}

.review-section-subtitle {
  color: #667085;
  font-size: 23rpx;
  font-weight: 700;
  line-height: 1.2;
}

.review-edit-actions {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex: 0 0 auto;
}

.review-mini-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 112rpx;
  height: 54rpx;
  margin: 0;
  padding: 0 18rpx;
  border-radius: 12rpx;
  border: 1rpx solid #1769ff;
  color: #1769ff;
  background: #ffffff;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 1;
  text-align: center;
  box-sizing: border-box;
}

.review-mini-btn.muted {
  color: #667085;
  border-color: #d0d5dd;
}

.review-meta-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12rpx;
}

.review-input,
.review-option-input {
  min-width: 0;
  height: 64rpx;
  padding: 0 18rpx;
  border-radius: 14rpx;
  border: 1rpx solid #d5deeb;
  background: #ffffff;
  color: #101828;
  font-size: 25rpx;
  font-weight: 700;
  line-height: 64rpx;
  box-sizing: border-box;
}

.review-difficulty-row {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8rpx;
}

.review-difficulty-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 64rpx;
  margin: 0;
  padding: 0;
  border-radius: 14rpx;
  border: 1rpx solid #d5deeb;
  color: #475467;
  background: #ffffff;
  font-size: 23rpx;
  font-weight: 900;
  line-height: 1;
}

.review-difficulty-btn.active {
  color: #1769ff;
  border-color: #1769ff;
  background: #eff6ff;
}

.review-question-box,
.review-explanation-box {
  padding: 22rpx;
  border-radius: 18rpx;
  border: 1rpx solid #dbe6f5;
  background: #f8fbff;
  box-sizing: border-box;
}

.review-question-box.editing {
  padding: 16rpx;
}

.review-stem {
  color: #101828;
  font-size: 29rpx;
  font-weight: 800;
  line-height: 1.55;
  word-break: break-word;
}

.review-chips {
  margin-top: 22rpx;
}

.review-textarea {
  width: 100%;
  min-height: 150rpx;
  padding: 18rpx 20rpx;
  border-radius: 16rpx;
  border: 1rpx solid #d5deeb;
  background: #ffffff;
  color: #101828;
  font-size: 25rpx;
  line-height: 1.55;
  letter-spacing: 0;
  box-sizing: border-box;
}

.review-textarea.stem {
  min-height: 220rpx;
  padding: 22rpx 22rpx;
  font-size: 24rpx;
  line-height: 1.62;
  word-break: normal;
  overflow-wrap: break-word;
  white-space: pre-wrap;
}

.review-textarea.explanation {
  min-height: 190rpx;
}

.review-textarea.note {
  min-height: 120rpx;
  background: #fffaf5;
  border-color: #fed7aa;
}

.review-option-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.review-option-row {
  display: flex;
  align-items: center;
  gap: 14rpx;
  min-height: 70rpx;
  padding: 0 18rpx;
  border-radius: 14rpx;
  border: 1rpx solid #dbe6f5;
  background: #ffffff;
  box-sizing: border-box;
}

.review-option-row.selected {
  border-color: #1769ff;
  background: #f8fbff;
  box-shadow: inset 0 0 0 1rpx rgba(23, 105, 255, 0.18);
}

.review-radio {
  flex: 0 0 auto;
  width: 32rpx;
  color: #1769ff;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1;
  text-align: center;
}

.review-option-label {
  flex: 0 0 auto;
  width: 42rpx;
  color: #101828;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 1;
}

.review-option-text {
  min-width: 0;
  color: #101828;
  font-size: 27rpx;
  font-weight: 700;
  line-height: 1.45;
  word-break: break-word;
}

.review-option-input {
  flex: 1;
  height: 68rpx;
  padding: 0;
  border: 0;
  background: transparent;
  line-height: 68rpx;
}

.review-explanation-box {
  color: #101828;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.65;
  word-break: break-word;
}

.review-footer {
  flex: 0 0 auto;
  display: grid;
  grid-template-columns: 0.9fr 0.9fr 1fr 1fr;
  gap: 12rpx;
  padding: 18rpx 28rpx calc(env(safe-area-inset-bottom) + 20rpx);
  border-top: 1rpx solid #edf2f7;
  background: rgba(255, 255, 255, 0.98);
  box-sizing: border-box;
}

.review-footer-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
  height: 68rpx;
  margin: 0;
  padding: 0 10rpx;
  border-radius: 14rpx;
  border: 1rpx solid #d0d5dd;
  color: #667085;
  background: #ffffff;
  font-size: 25rpx;
  font-weight: 900;
  line-height: 1;
  text-align: center;
  box-sizing: border-box;
}

.review-footer-btn.outline {
  color: #1769ff;
  border-color: #1769ff;
}

.review-footer-btn.primary {
  color: #ffffff;
  border-color: #0891b2;
  background: linear-gradient(135deg, #0ea5b7 0%, #0891b2 100%);
}

.review-footer-btn.blue {
  color: #ffffff;
  border-color: #1769ff;
  background: #1769ff;
}

.review-footer-btn.muted {
  color: #94a3b8;
  border-color: #dbe6f5;
  background: #ffffff;
}

.review-footer-btn[disabled] {
  opacity: 0.45;
}

.message-editor {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  padding: 18rpx;
  border-radius: 22rpx;
  background: #f8fbff;
  border: 1rpx solid #e3ebf7;
}

.message-textarea {
  min-height: 180rpx;
  padding: 18rpx 22rpx;
  border-radius: 18rpx;
  background: #ffffff;
  border: 1rpx solid #dbe6f5;
  color: #101828;
  font-size: 25rpx;
  line-height: 1.6;
  box-sizing: border-box;
}

.message-status-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.status-chip {
  height: 58rpx;
  border: 0;
  border-radius: 18rpx;
  background: #eef2f7;
  color: #475467;
  font-size: 23rpx;
  font-weight: 800;
}

.status-chip.active {
  background: #3b82f6;
  color: #ffffff;
}
</style>
