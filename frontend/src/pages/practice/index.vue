<template>
  <view
    class="page practice-page"
    :class="{
      'quiz-page': mode === 'quiz' && !reviewMode && !summaryMode && !aiSummaryMode,
      'result-summary-page': summaryMode && !aiSummaryMode
    }"
    :style="themeInlineStyle"
  >
    <view
      class="top-nav"
      :class="{ 'scope-top-nav': usesScopeHeader }"
      :style="usesScopeHeader ? scopeHeaderStyle : undefined"
    >
      <button class="back-btn" :disabled="practiceFlowLocked" @tap="goBack">
        <image class="back-icon" src="/static/ui-icons/png/original/back.png" mode="aspectFit" />
      </button>
      <view class="top-copy" :class="{ 'scope-top-copy': usesScopeHeader }">
        <view class="top-title-row">
          <view class="top-title">{{ pageTitle }}</view>
          <view v-if="topSubtitle" class="top-sub">{{ topSubtitle }}</view>
        </view>
      </view>
    </view>
    <view v-if="usesScopeHeader" class="scope-top-nav-spacer"></view>

    <template v-if="mode === 'tags'">
      <view v-if="showCultureProgress" class="culture-progress-card">
        <view class="culture-progress-head">
          <view>
            <view class="culture-progress-title">学习范围</view>
            <view class="culture-progress-sub">
              {{ cultureProgressLoading ? '正在整理你的刷题记录...' : `已学习 ${cultureLearnedText} / 共 ${cultureTotalText}` }}
            </view>
          </view>
          <view class="culture-percent">{{ cultureProgressPercent }}%</view>
        </view>

        <view class="culture-progress-track">
          <view class="culture-progress-fill" :style="{ width: cultureProgressWidth }"></view>
        </view>
      </view>

      <view class="mode-card">
        <view
          v-for="item in practiceModeOptions"
          :key="item.value"
          class="mode-option"
          :class="{ active: practiceMode === item.value }"
          @tap="switchPracticeMode(item.value)"
        >
          <view class="mode-title">{{ item.label }}</view>
          <view class="mode-sub">{{ item.description }}</view>
        </view>
      </view>

      <view class="count-card">
        <view class="count-head">
          <view class="count-copy">
            <view class="count-title">本轮题量</view>
          </view>
          <view class="count-value">{{ selectedQuestionSize }}题</view>
        </view>

        <view class="count-slider-wrap">
          <slider
            class="count-slider"
            :value="selectedQuestionSize"
            :min="questionCountOptions[0]"
            :max="questionCountOptions[questionCountOptions.length - 1]"
            :step="5"
            :activeColor="currentTheme.primary"
            :backgroundColor="currentTheme.primaryBorder"
            block-color="#ffffff"
            block-size="26"
            @changing="handleQuestionSizeChange"
            @change="handleQuestionSizeChange"
          />
          <view class="count-scale">
            <text
              v-for="count in questionCountOptions"
              :key="count"
              class="scale-value"
              :class="{ active: selectedQuestionSize === count }"
              :style="{ left: getQuestionScalePosition(count) }"
            >
              {{ count }}
            </text>
          </view>
        </view>
      </view>

      <view v-if="loadError" class="state-box warning">{{ loadError }}</view>
      <view v-if="shortageTip" class="state-box">{{ shortageTip }}</view>

      <TagAccordion
        v-if="practiceMode === 'special'"
        :sections="subjectTree"
        :selected-tags="selectedTags"
        :open-map="openMap"
        :get-count="getCount"
        @toggle-open="toggleOpen"
        @toggle-section="toggleSection"
        @toggle-tag="toggleTag"
      />

      <view class="sticky-bar">
        <view
          class="sticky-copy"
          :class="{
            'sticky-copy--single': practiceMode === 'special' || practiceMode === 'comprehensive',
            'sticky-copy--comprehensive': practiceMode === 'comprehensive'
          }"
        >
          <view class="sticky-title">{{ stickyTitle }}</view>
        </view>
        <view class="sticky-actions" :class="{ dual: showCultureProgress }">
          <button
            v-if="showCultureProgress"
            class="sticky-btn review-sticky-btn"
            :disabled="cultureReviewDisabled"
            hover-class="sticky-btn--pressed"
            :hover-stay-time="60"
            @tap="startCultureReview"
          >
            <text>开始复习</text>
            <text class="sticky-btn-sub">{{ cultureReviewButtonText }}</text>
          </button>
          <button
            class="sticky-btn start-sticky-btn"
            :disabled="loading || quizStartInProgress"
            hover-class="sticky-btn--pressed"
            :hover-stay-time="60"
            @tap="startQuiz"
          >
            <text class="start-sticky-label">{{ quizStartBackgrounded ? '后台准备中...' : (loading || quizStartInProgress ? '加载中...' : startButtonText) }}</text>
          </button>
        </view>
      </view>

      <view v-if="practiceMode === 'special'" class="adaptive-preference-card">
        <view class="adaptive-preference-head">
          <view>
            <view class="adaptive-preference-title">练习节奏</view>
            <view class="adaptive-preference-sub">只影响本轮题目节奏，不会改变系统对你能力的判断。</view>
          </view>
          <view class="adaptive-preference-badge">智能出题</view>
        </view>
        <view class="adaptive-preference-options">
          <button
            v-for="item in adaptivePreferenceOptions"
            :key="item.value"
            class="adaptive-preference-option"
            :class="{ active: adaptivePreference === item.value }"
            hover-class="none"
            @tap="selectAdaptivePreference(item.value)"
          >
            <text class="adaptive-preference-option-title">{{ item.label }}</text>
            <text class="adaptive-preference-option-sub">{{ item.description }}</text>
          </button>
        </view>
        <view class="adaptive-preference-tip">能力按 {{ examCode }} / {{ subject }} 独立计算；首次练习会自动进入 8 题智能热身。</view>
      </view>
    </template>

    <template v-else>
      <!-- #ifndef MP-WEIXIN -->
      <template v-if="aiSummaryMode">
        <view class="summary-card ai-summary-card">
          <view class="summary-kicker">AI 训练总结</view>
          <view class="summary-score">{{ aiSummaryAccuracy }}%</view>
          <view class="summary-sub">本轮答对 {{ aiSummaryCorrect }} / {{ aiSummaryTotal }} 题。看完解析后，系统会把错题继续纳入能力统计。</view>
        </view>

        <view class="ai-diagnosis-card">
          <view class="ai-diagnosis-title">本轮诊断</view>
          <view class="ai-diagnosis-text">{{ aiSummary?.summary || '已完成本轮 AI 专项训练。' }}</view>
          <view class="ai-diagnosis-title">下一步建议</view>
          <view class="ai-diagnosis-text">{{ aiSummary?.next_step || '建议回看错题解析后，再生成一组同知识点训练。' }}</view>
          <view v-if="aiSummary?.weak_points?.length" class="ai-weak-tags">
            <text v-for="item in aiSummary.weak_points" :key="item">{{ item }}</text>
          </view>
        </view>

        <view class="summary-grid">
          <button
            v-for="(item, index) in aiReviewResults"
            :key="item.question.questionId || item.question.id"
            class="summary-dot"
            :class="{ correct: item.isCorrect === true, wrong: item.isCorrect === false && !item.syncFailed, pending: item.syncFailed }"
            @tap="openAiReviewQuestion(index)"
          >
            {{ index + 1 }}
          </button>
        </view>

        <view class="summary-actions">
          <button class="next-btn" @tap="openAiReviewQuestion(0)">回看本轮解析</button>
          <button class="ghost-button back-tags" @tap="resetToTags">返回刷题范围</button>
        </view>
      </template>
      <!-- #endif -->

      <!-- #ifndef MP-WEIXIN -->
      <template v-else-if="summaryMode">
      <!-- #endif -->
      <!-- #ifdef MP-WEIXIN -->
      <template v-if="summaryMode">
      <!-- #endif -->
        <view class="summary-card summary-card--with-stats result-overview-card" :class="{ 'mock-summary-card': mockExamMode }">
          <view class="result-overview-main">
            <view class="summary-card-copy">
              <view class="summary-kicker">{{ summaryKicker }}</view>
              <view class="summary-score" :aria-label="mockExamMode ? `${mockExamScore} 分，共 ${mockExamTotalScore} 分` : `答对 ${correctCount} 题，共 ${summaryQuestionCount} 题`">
                <text class="summary-score-main">{{ mockExamMode ? mockExamScore : correctCount }}</text>
                <text class="summary-score-total">/ {{ mockExamMode ? mockExamTotalScore : summaryQuestionCount }}</text>
              </view>
            </view>
            <view class="summary-stat-stack" aria-label="本轮练习统计">
              <view class="summary-stat-row">
                <view class="summary-stat-icon" aria-hidden="true">
                  <image
                    :src="getThemeIconSrc('/static/ui-icons/png/original/report.png', getStoredThemeKey())"
                    mode="aspectFit"
                  />
                </view>
                <view class="summary-stat-copy">
                  <view class="summary-stat-value">{{ summaryAccuracy }}%</view>
                  <view class="summary-stat-label">正确率</view>
                </view>
              </view>
              <view class="summary-stat-row">
                <view class="summary-stat-icon" aria-hidden="true">
                  <image
                    :src="getThemeIconSrc('/static/ui-icons/png/original/timer.png', getStoredThemeKey())"
                    mode="aspectFit"
                  />
                </view>
                <view class="summary-stat-copy">
                  <view class="summary-stat-value">{{ summaryElapsedTime }}</view>
                  <view class="summary-stat-label">本次用时</view>
                </view>
              </view>
            </view>
          </view>
        </view>

        <view v-if="adaptivePracticeActive && !mockExamMode" class="adaptive-summary-card">
          <view class="adaptive-summary-head">
            <view>
              <view class="adaptive-summary-eyebrow">{{ adaptiveWarmupCompleted ? '智能热身定位' : '本轮个性化反馈' }}</view>
              <view class="adaptive-summary-level">{{ adaptiveSummaryLevel }}</view>
            </view>
            <view class="adaptive-summary-confidence">{{ adaptiveSummaryConfidence }}</view>
          </view>
          <view class="adaptive-summary-copy">{{ adaptiveSummaryDescription }}</view>
        </view>

        <view v-if="mockExamMode" class="mock-section-card">
          <view class="mock-section-title">分项得分</view>
          <view
            v-for="item in mockExamSectionScores"
            :key="item.key"
            class="mock-section-row"
          >
            <view>
              <view class="mock-section-name">{{ item.label }}</view>
              <view class="mock-section-sub">答对 {{ item.correct }} / {{ item.totalQuestions }} 题</view>
            </view>
            <view class="mock-section-score">{{ item.score }} / {{ item.totalScore }}</view>
          </view>
        </view>

        <view class="summary-grid result-answer-card">
          <view class="result-answer-head">
            <view class="result-answer-title">答题情况</view>
          </view>
          <view class="result-question-grid">
            <button
              v-for="(item, index) in reviewResults"
              :key="item.question.questionId || item.question.id"
              class="summary-dot"
              :class="{ correct: item.isCorrect === true, wrong: item.isCorrect === false && !item.syncFailed, pending: item.syncFailed }"
              @tap="openReviewQuestion(index)"
            >
              {{ index + 1 }}
            </button>
          </view>
        </view>

        <view class="result-advice">
          <image
            class="result-advice-icon"
            :src="getThemeIconSrc('/static/ui-icons/png/original/lightbulb.png', getStoredThemeKey())"
            mode="aspectFit"
            aria-hidden="true"
          />
          <text>{{ summaryAdviceText }}</text>
        </view>

        <view class="summary-actions result-summary-actions">
          <button class="summary-action-primary" :disabled="loading || quizStartInProgress" @tap="openFirstReviewQuestion">
            <text>查看错题解析</text>
            <text class="summary-action-arrow" aria-hidden="true">→</text>
          </button>
          <button class="summary-action-secondary" :disabled="loading || quizStartInProgress" @tap="retryPractice">
            <text>{{ loading || quizStartInProgress ? '正在准备...' : '再练一组' }}</text>
          </button>
          <button class="summary-action-secondary" :disabled="loading || quizStartInProgress" @tap="handleSummaryBack">
            <text>{{ mockExamMode ? '返回模拟卷' : '返回刷题范围' }}</text>
          </button>
        </view>
      </template>

      <template v-else>
      <view class="quiz-shell">
        <view class="quiz-top">
          <view class="quiz-top-leading">
            <view class="badge">{{ quizProgressText }}</view>
          </view>
          <view class="quiz-top-actions">
            <view class="timer">
              <image class="timer-icon" src="/static/ui-icons/png/gold/timer.png" mode="aspectFit" aria-hidden="true" />
              <text>{{ formattedTimer }}</text>
            </view>
            <button
              v-if="showQuestionSheetEntry"
              class="question-map-btn"
              @tap="openAnswerSheet"
            >
              题卡
            </button>
          </view>
        </view>

        <view class="question-card">
          <button
            class="favorite-btn"
            :class="{ active: currentFavorited }"
            :disabled="!canFavoriteCurrent"
            :aria-busy="favoriteLoading ? 'true' : 'false'"
            :aria-label="currentFavorited ? '取消收藏' : '收藏题目'"
            hover-class="none"
            @tap.stop="toggleCurrentFavorite"
          >
            <image
              class="practice-favorite-icon"
              :src="currentFavorited
                ? '/static/ui-icons/png/gold/star.png'
                : '/static/ui-icons/png/neutral/star.png'"
              mode="aspectFit"
              aria-hidden="true"
            />
          </button>
          <QuestionStem class="question-title" :question="normalizedCurrentQuestion" />
        </view>
      </view>

      <view v-if="!currentQuestionHasBlockingIssue" class="options">
        <OptionCard
          v-for="option in normalizedCurrentQuestion.options"
          :key="option.key"
          :label="option.key"
          :content="option.text"
          :is-math="normalizedCurrentQuestion.isMath"
          :compact="mode === 'quiz' && !reviewMode"
          :selected="selectedOption === option.key"
          :submitted="optionSubmitted"
          :correct="submitted && option.key === correctAnswer"
          :wrong="submitted && option.key === selectedOption && selectedOption !== correctAnswer"
          @select="selectOption"
        />
      </view>
      <view v-else class="state-box warning">{{ currentQuestionIssueText }}</view>

      <view v-if="currentQuestionHasBlockingIssue" class="primary-action-row">
        <button class="prev-btn" :disabled="!hasPrevQuestion || practiceMutationLocked" @tap="goPrevQuestion">上一题</button>
        <button class="submit-btn" :disabled="practiceMutationLocked" @tap="handleInvalidQuestionNext">
          {{ canAdvanceQuestion ? '跳过异常题' : '结束本轮' }}
        </button>
      </view>
      <view v-else-if="!reviewMode && !submitted" class="primary-action-row">
        <button class="prev-btn" :disabled="!hasPrevQuestion || practiceMutationLocked" @tap="goPrevQuestion">上一题</button>
        <button
          class="submit-btn"
          :disabled="!selectedOption || practiceMutationLocked || currentQuestionHasBlockingIssue"
          hover-class="submit-btn--pressed"
          :hover-stay-time="80"
          @tap="handlePrimaryAction"
        >
          {{ submitting ? '正在提交...' : primaryButtonText }}
        </button>
      </view>
      <button
        v-if="showUnfamiliarShortcut"
        class="unfamiliar-btn"
        :disabled="practiceMutationLocked"
        @tap="markCurrentUnfamiliarAndNext"
      >
          {{ adaptiveNavigationQueued ? '保存后自动继续' : (markingUnfamiliar ? '正在加入复习...' : '不熟悉，加入复习') }}
      </button>

      <view v-if="submitted && !reviewMode" class="action-row">
        <view class="review-nav-row">
          <button
            class="next-btn secondary"
            :disabled="!hasPrevQuestion || practiceMutationLocked"
            @tap="goPrevQuestion"
          >上一题</button>
          <button
            v-if="canAdvanceQuestion"
            class="next-btn"
            :disabled="adaptiveForwardNavigationLocked"
            @tap="goNextQuestion"
          >
            {{ adaptiveNavigationQueued ? (adaptiveAnswerSyncing ? '保存后自动继续' : '匹配后自动继续') : (adaptiveAnswerSyncing ? '同步中，点此继续' : (adaptiveNextLoading ? '正在匹配...' : (adaptiveNextPrefetching ? '后台匹配中，可继续' : '下一题'))) }}
          </button>
          <button v-else class="next-btn done" :disabled="adaptiveForwardNavigationLocked" @tap="finishQuiz">
            {{ adaptiveNavigationQueued ? '保存后自动完成' : (adaptiveNextLoading ? '正在同步...' : (adaptiveAnswerSyncing ? '同步中，点此完成' : (isAiTrainingMode ? '查看 AI 总结' : '完成本轮'))) }}
          </button>
        </view>
      </view>

      <view v-if="submitted && !reviewMode" class="post-submit-action-row">
        <button
          v-if="showUnfamiliarAfterCorrect"
          class="unfamiliar-btn post-submit-unfamiliar-btn"
          :disabled="practiceMutationLocked"
          @tap="markCurrentUnfamiliarAndNext"
        >
          {{ adaptiveNavigationQueued ? '保存后自动继续' : (markingUnfamiliar ? '正在加入复习...' : '不熟悉') }}
        </button>
        <button
          class="explanation-toggle-btn"
          :disabled="questionNavigationLocked"
          @tap="toggleExplanation"
        >
          {{ explanationToggleText }}
        </button>
      </view>

      <view id="result-anchor">
        <ExplanationPanel
          :visible="reviewMode"
          :correct-answer="correctAnswer"
          :explanation="answerExplanation"
        />
      </view>

      <view v-if="reviewMode" class="action-row">
        <view class="review-nav-row">
          <button class="next-btn secondary" :disabled="!hasPrevQuestion || questionNavigationLocked" @tap="goPrevQuestion">上一题</button>
          <button class="next-btn" :disabled="!hasNextQuestion || questionNavigationLocked" @tap="goNextQuestion">下一题</button>
        </view>
        <button class="next-btn outline" @tap="isAiTrainingMode ? showAiSummary() : showSummary()">
          {{ isAiTrainingMode ? '返回 AI 总结' : '查看结果总览' }}
        </button>
      </view>

      <button v-if="mockExamMode" class="ghost-button back-tags" @tap="confirmExitPractice">
        退出模拟测试
      </button>
      </template>
    </template>

    <!-- #ifndef MP-WEIXIN -->
    <AiQuestionAssistant
      v-if="showQuestionAssistant"
      :question-id="assistantQuestionId"
      :subject="subject"
      :module-name="questionMeta.module || currentQuestion.module"
      :submodule="questionMeta.submodule || currentQuestion.submodule"
      :submitted="assistantQuestionSubmitted"
      :selected-answer="selectedOption"
      :correct-answer="correctAnswer"
    />
    <!-- #endif -->

	<view v-if="showAnswerSheet" class="answer-sheet-mask" @tap="closeAnswerSheet">
		<view class="answer-sheet" @tap.stop>
			<view class="sheet-handle"></view>
			<view class="answer-sheet-head">
				<view class="sheet-title">答题卡</view>
				<button class="sheet-cancel-btn" @tap.stop="closeAnswerSheet">取消</button>
			</view>

        <view
          v-for="section in answerSheetSections"
          :key="section.label"
          class="sheet-section"
        >
          <view class="sheet-section-head">
            <text>{{ section.label }}</text>
            <text>{{ section.answered }} / {{ section.items.length }}</text>
          </view>
          <view class="sheet-grid">
            <button
              v-for="item in section.items"
              :key="item.index"
              class="sheet-number"
              :class="{ answered: item.answered, current: item.index === currentQuestionIndex }"
              @tap="jumpToQuestion(item.index)"
            >
              {{ item.index + 1 }}
            </button>
          </view>
        </view>

		</view>
	</view>

    <view
      v-if="submitted && explanationExpanded && !reviewMode"
      class="explanation-sheet-mask"
      @tap="closeExplanation"
    >
      <view class="explanation-sheet" @tap.stop>
        <view class="sheet-handle explanation-sheet-handle"></view>
        <view class="explanation-sheet-head">
          <view class="explanation-sheet-title">题目解析</view>
          <button class="explanation-sheet-close" @tap.stop="closeExplanation">关闭</button>
        </view>
        <scroll-view class="explanation-sheet-body" scroll-y>
          <ExplanationPanel
            :visible="true"
            :correct-answer="correctAnswer"
            :explanation="answerExplanation"
          />
        </scroll-view>
      </view>
    </view>

    <view
      v-if="showGradingFeedback"
      class="grading-feedback-mask"
      role="status"
      aria-live="polite"
      @tap.stop
      @touchmove.stop.prevent
    >
      <view class="grading-feedback-card">
        <text class="grading-feedback-title">正在批改整卷...</text>
        <view class="grading-feedback-progress" aria-hidden="true">
          <view class="grading-feedback-progress-bar"></view>
        </view>
        <text class="grading-feedback-copy">正在生成成绩与解析，请稍候</text>
      </view>
    </view>

    <!-- #ifdef H5 -->
    <IcpFooter v-if="mode !== 'quiz' || summaryMode || aiSummaryMode" />
    <!-- #endif -->
  </view>
</template>

<script setup>
import { computed, nextTick, ref, watch } from 'vue'
import { buildThemeStyle, getStoredThemeKey, getThemePreset } from '../../utils/theme'
import { onBackPress, onHide, onLoad, onPageScroll, onShow, onUnload } from '@dcloudio/uni-app'
import {
  completeAdaptivePracticeSession,
  createAdaptivePracticeSession,
  fetchNextAdaptivePracticeItem,
  recordAdaptivePracticeItemEvent,
  submitAdaptiveComprehensivePracticeSession
} from '../../api/adaptivePractice'
import { fetchAiTrainingSession, fetchAiTrainingSummary } from '../../api/ai'
import { fetchAnswerHistory, markQuestionUnfamiliar } from '../../api/answers'
import { fetchFavoriteStatus, toggleFavorite } from '../../api/favorites'
import { request } from '../../api/http'
import { fetchQuestionProgress, fetchReviewDueQuestions } from '../../api/questions'
import { fetchMockExamPaperDetail } from '../../api/mockExams'
import { readLegacyH5Storage } from '../../platform/runtime'
// #ifndef MP-WEIXIN
import AiQuestionAssistant from '../../components/AiQuestionAssistant.vue'
// #endif
import ExplanationPanel from '../../components/ExplanationPanel.vue'
import IcpFooter from '../../components/IcpFooter.vue'
import OptionCard from '../../components/OptionCard.vue'
import QuestionStem from '../../components/QuestionStem.vue'
import TagAccordion from '../../components/TagAccordion.vue'
import { getPracticeQuestion, getTagCount } from '../../mock/appMock'
import { getAuthUser } from '../../utils/auth'
import { confirmFavoriteRemoval } from '../../utils/favorites'
import {
  flushPendingAnswerSubmissions,
  releaseAnswerSubmissionSettlement,
  schedulePendingAnswerFlush,
  submitAnswerWithReliableSync,
  waitForAnswerSubmissionSettlement
} from '../../utils/answerSubmissionQueue'
import { createAdaptiveNextRequestBroker } from '../../utils/adaptiveNextRequestBroker'
import {
  buildAdaptiveComprehensiveSubmissionPayload,
  isAdaptiveWarmupSession,
  mapAdaptiveComprehensiveResults,
  normalizeAdaptiveComprehensiveItems,
  summarizeAdaptiveReviewResults
} from '../../utils/adaptiveComprehensivePractice'
import {
  createAdaptiveComprehensiveSubmissionQueue,
  isAdaptiveComprehensiveCompletedResponse,
  isAdaptiveComprehensiveTerminalSubmissionError
} from '../../utils/adaptiveComprehensiveSubmissionQueue'
import { getThemeIconSrc } from '../../utils/iconAssets'
import { getSubjectTree } from '../../utils/knowledgeTree'
import { normalizeQuestion, validateQuestion } from '../../utils/questionQuality'

const MOCK_EXAM_TOTAL_SCORE = 105
const MOCK_EXAM_TOTAL_COUNT = 55
const CULTURE_SUBJECT = '中华文化'
const ADAPTIVE_PREFERENCE_STORAGE_KEY = 'adaptivePracticePreference'
const themeInlineStyle = buildThemeStyle(getStoredThemeKey())
const DEFAULT_CULTURE_PROGRESS = {
  total_questions: 0,
  mastered_questions: 0,
  progress_percent: 0,
  review_due_count: 0,
  review_days: [1, 2, 4, 7, 15, 30]
}
const ADAPTIVE_HISTORY_MIN_COUNT = 10
const ADAPTIVE_HISTORY_LIMIT = 100
const ADAPTIVE_FOREGROUND_PREFETCH_WAIT_MS = 1200
const ADAPTIVE_PREFETCH_STILL_RUNNING = Symbol('adaptive-prefetch-still-running')
const ADAPTIVE_LEGACY_START_STILL_RUNNING = Symbol('adaptive-legacy-start-still-running')
const DIFFICULTY_LEVELS = [1, 2, 3, 4, 5]
const adaptivePreferenceOptions = [
  { value: 'steady', label: '稳一点', description: '更多巩固题' },
  { value: 'standard', label: '标准', description: '难度均衡' },
  { value: 'challenge', label: '更有挑战', description: '适当提高上限' }
]
const MOCK_EXAM_DIFFICULTY_PROFILE = [
  { key: 'basic', label: '基础', ratio: 0.35 },
  { key: 'medium', label: '中等', ratio: 0.5 },
  { key: 'hard', label: '较难', ratio: 0.15 }
]

const practiceModeOptions = [
  {
    value: 'special',
    label: '专项刷题',
    description: '选择一个或多个知识点，提交后立即看解析。'
  },
  {
    value: 'comprehensive',
    label: '综合刷题',
    description: '全部知识点随机混合，整轮完成后统一公布答案。'
  }
]

const examCode = ref(uni.getStorageSync('examCode') || 'Z001')
const subject = ref(uni.getStorageSync('subject') || '中华文化')
const mode = ref('tags')
const practiceMode = ref('special')
const selectedTags = ref([])
const questionCountOptions = [5, 10, 15, 20, 25, 30]
const selectedQuestionSize = ref(10)
const adaptivePreference = ref(readAdaptivePreference())
const adaptiveSession = ref(null)
const adaptiveSummary = ref(null)
const adaptiveInitialPhase = ref('')
const adaptiveInitialReliableCount = ref(null)
const adaptiveNextLoading = ref(false)
const adaptiveNextPrefetching = ref(false)
const adaptiveAnswerSyncing = ref(false)
const adaptiveEventSyncing = ref(false)
const adaptiveFallbackMode = ref(false)
const adaptiveLegacyFallbackLoading = ref(false)
const adaptiveNextExhausted = ref(false)
const adaptiveNextFinishAvailable = ref(false)
const adaptiveQueuedNavigation = ref(null)
const questionNavigationPending = ref(false)
const quizStartInProgress = ref(false)
const quizStartBackgrounded = ref(false)
const aiSessionId = ref('')
const selectedOption = ref('')
const submitted = ref(false)
const submitting = ref(false)
const explanationExpanded = ref(false)
const markingUnfamiliar = ref(false)
const loading = ref(false)
const loadError = ref('')
const shortageTip = ref('')
const cultureProgress = ref({ ...DEFAULT_CULTURE_PROGRESS })
const cultureProgressLoading = ref(false)
const cultureReviewLoading = ref(false)
const timerSeconds = ref(0)
const questionElapsedByKey = ref({})
const submissionIdsByQuestion = ref({})
const submissionUsedTimeByQuestion = ref({})
const submissionSessionId = ref('')
const accessToken = ref(readAccessToken())
const questionPool = ref([buildMockQuestion(subject.value, examCode.value)])
const currentQuestionIndex = ref(0)
const correctAnswer = ref('')
const answerExplanation = ref('')
const resultTag = ref('')
const abilityAccuracy = ref(null)
const currentFavorited = ref(false)
const favoriteLoading = ref(false)
const favoriteQuestionId = ref('')
const showGradingFeedback = ref(false)
const questionMeta = ref({
  questionId: '',
  module: '',
  submodule: ''
})
const comprehensiveAnswers = ref({})
const comprehensiveSkippedQuestions = ref({})
const reviewMode = ref(false)
const reviewResults = ref([])
const instantQuestionResults = ref({})
const unfamiliarQuestionMap = ref({})
const summaryMode = ref(false)
const aiSummaryMode = ref(false)
const aiSummary = ref(null)
const aiReviewResults = ref([])
const mockExamMode = ref(false)
const mockExamPaperId = ref('')
const mockExamPaperTitle = ref('')
const showAnswerSheet = ref(false)
const scopeHeaderScrollTop = ref(0)

const questionCache = new Map()
const favoriteStatusCache = new Map()
let timerId = null
let activeTimerQuestionKey = ''
let exitConfirmVisible = false
let exitNavigationPending = false
let adaptiveRecordedEvents = new Set()
let adaptivePendingSubmissionPayloads = new Map()
let adaptiveAnswerSubmissionTasks = new Map()
let adaptiveLegacyFallbackTasks = new Map()
let adaptiveComprehensiveSubmissionSnapshot = null
let adaptiveFlowGeneration = 0
let adaptiveNextRequestSequence = 0
let activeAdaptiveNextRequestToken = 0
let adaptiveNextLoadingSequence = 0
let activeAdaptiveNextLoadingToken = 0
let adaptiveNextPrefetchSequence = 0
let activeAdaptiveNextPrefetchToken = 0
let adaptiveAnswerRequestSequence = 0
let activeAdaptiveAnswerRequestToken = 0
let adaptiveEventRequestSequence = 0
let activeAdaptiveEventRequestToken = 0
let unfamiliarRequestSequence = 0
let activeUnfamiliarRequestToken = 0
let questionNavigationSequence = 0
let activeQuestionNavigationToken = 0
let quizStartRequestSequence = 0
let activeQuizStartRequestToken = 0
const adaptiveClosingSessionIds = new Set()
const adaptiveNextRequestBroker = createAdaptiveNextRequestBroker()
const adaptiveComprehensiveSubmissionStorage = Object.freeze({
  getStorageSync(key) {
    return uni.getStorageSync(key)
  },
  setStorageSync(key, value) {
    return uni.setStorageSync(key, value)
  },
  removeStorageSync(key) {
    return uni.removeStorageSync(key)
  }
})
const adaptiveComprehensiveSubmissionQueue = createAdaptiveComprehensiveSubmissionQueue({
  storage: adaptiveComprehensiveSubmissionStorage,
  getOwnerId: getCurrentAdaptiveSubmissionOwnerId,
  submit: submitAdaptiveComprehensivePracticeSession
})

const subjectTree = computed(() => getSubjectTree(subject.value))
const openMap = ref(buildOpenMap(subjectTree.value))
const hasAccessToken = computed(() => Boolean(accessToken.value))
const plannedQuestionLimit = computed(() => selectedQuestionSize.value)
const currentTheme = computed(() => getThemePreset(getStoredThemeKey()))
const isAiTrainingMode = computed(() => Boolean(aiSessionId.value))
const isCultureSubject = computed(() => subject.value === CULTURE_SUBJECT)
const showCultureProgress = computed(() => mode.value === 'tags' && isCultureSubject.value)
const currentQuestion = computed(() => questionPool.value[currentQuestionIndex.value] || (isAiTrainingMode.value ? buildEmptyAiQuestion() : buildMockQuestion(subject.value, examCode.value)))
const normalizedCurrentQuestion = computed(() => normalizeQuestion(currentQuestion.value, { subject: subject.value, examCode: examCode.value }))
const currentQuestionQuality = computed(() => validateQuestion(normalizedCurrentQuestion.value))
const currentQuestionHasBlockingIssue = computed(() => !currentQuestionQuality.value.valid)
const currentQuestionIssueText = computed(() => {
  const reasons = currentQuestionQuality.value.reasons || []
  return reasons.length ? `题目数据异常，请检查题库：${reasons.join('；')}` : '题目数据异常，请检查题库'
})
const currentQuestionKey = computed(() => currentQuestion.value.questionId || currentQuestion.value.id)
const assistantQuestionId = computed(() => {
  const id = questionMeta.value.questionId || currentQuestion.value.questionId || currentQuestion.value.id || ''
  return String(id).startsWith('mock-') ? '' : id
})
const assistantQuestionSubmitted = computed(() => submitted.value || reviewMode.value)
const showQuestionAssistant = computed(() => mode.value !== 'tags' && !summaryMode.value && !aiSummaryMode.value && !showAnswerSheet.value)
const isCurrentMarkedUnfamiliar = computed(() => Boolean(unfamiliarQuestionMap.value[currentQuestionKey.value]))
const hasPrevQuestion = computed(() => currentQuestionIndex.value > 0)
const hasNextQuestion = computed(() => currentQuestionIndex.value < questionPool.value.length - 1)
const adaptivePracticeActive = computed(() => Boolean(adaptiveSession.value?.id) && !adaptiveFallbackMode.value)
const adaptiveComprehensivePracticeActive = computed(() => (
  adaptivePracticeActive.value &&
  practiceMode.value === 'comprehensive' &&
  String(adaptiveSession.value?.practice_mode || '').toLowerCase() === 'comprehensive'
))
const adaptiveQuestionTotal = computed(() => {
  const total = Number(adaptiveSession.value?.question_count || 0)
  return total > 0 ? total : questionPool.value.length
})
const adaptiveSessionEnded = computed(() => {
  const status = String(adaptiveSession.value?.status || '').trim().toLowerCase()
  return ['completed', 'abandoned', 'cancelled'].includes(status)
})
const adaptiveMayHaveNext = computed(() =>
  adaptivePracticeActive.value &&
  !adaptiveSessionEnded.value &&
  !adaptiveNextExhausted.value &&
  questionPool.value.length < adaptiveQuestionTotal.value
)
const canAdvanceQuestion = computed(() => (
  hasNextQuestion.value || adaptiveLegacyFallbackLoading.value || (
    !adaptiveNextFinishAvailable.value &&
    (adaptiveMayHaveNext.value || adaptiveNextPrefetching.value)
  )
))
const questionNavigationLocked = computed(() => (
  submitting.value ||
  markingUnfamiliar.value ||
  adaptiveAnswerSyncing.value ||
  adaptiveNextLoading.value ||
  adaptiveEventSyncing.value ||
  questionNavigationPending.value
))
const adaptiveForwardNavigationQueueable = computed(() => (
  submitted.value &&
  !reviewMode.value &&
  Boolean(currentQuestion.value?.adaptiveSessionItemId) &&
  adaptiveAnswerSyncing.value &&
  !submitting.value &&
  !markingUnfamiliar.value &&
  !adaptiveNextLoading.value &&
  !adaptiveEventSyncing.value &&
  !questionNavigationPending.value
))
const adaptiveForwardNavigationLocked = computed(() => (
  Boolean(adaptiveQueuedNavigation.value) ||
  (questionNavigationLocked.value && !adaptiveForwardNavigationQueueable.value)
))
const adaptiveNavigationQueued = computed(() => Boolean(adaptiveQueuedNavigation.value))
const practiceMutationLocked = computed(() => (
  questionNavigationLocked.value || adaptiveNavigationQueued.value
))
const practiceFlowLocked = computed(() => (
  questionNavigationLocked.value ||
  loading.value ||
  (quizStartInProgress.value && !quizStartBackgrounded.value)
))
const scoredReviewSummary = computed(() => summarizeAdaptiveReviewResults(reviewResults.value))
const summaryQuestionCount = computed(() => scoredReviewSummary.value.answeredCount)
const correctCount = computed(() => scoredReviewSummary.value.correctCount)
const summaryAccuracy = computed(() => scoredReviewSummary.value.accuracy)
const summaryElapsedSeconds = computed(() => {
  const recordedSeconds = Object.values(questionElapsedByKey.value || {}).reduce(
    (total, value) => total + Math.max(0, Number(value || 0)),
    0
  )
  return recordedSeconds || Math.max(0, Number(timerSeconds.value || 0))
})
const summaryElapsedTime = computed(() => formatDuration(summaryElapsedSeconds.value))
const firstReviewIndex = computed(() => {
  const index = reviewResults.value.findIndex((item) => item.syncFailed || item.isCorrect === false)
  return index >= 0 ? index : 0
})
const summaryKicker = computed(() => {
  if (mockExamMode.value) return mockExamPaperTitle.value ? `${mockExamPaperTitle.value}成绩` : '模拟测试成绩'
  if (adaptiveWarmupCompleted.value) return '8 题智能热身结果'
  if (adaptiveComprehensivePracticeActive.value) return '综合刷题结果'
  if (adaptivePracticeActive.value) return '个性化专项结果'
  return practiceMode.value === 'comprehensive' ? '综合刷题结果' : '专项刷题结果'
})
const adaptiveWarmupCompleted = computed(() => {
  return isAdaptiveWarmupSession({
    active: adaptivePracticeActive.value,
    questionCount: adaptiveQuestionTotal.value,
    diagnosticStatus: adaptiveInitialPhase.value,
    reliableFirstAttemptCount: adaptiveInitialReliableCount.value
  })
})
const adaptiveSummaryLevel = computed(() => {
  const level = String(adaptiveSummary.value?.initial_level_range || '').trim()
  return level || (adaptiveWarmupCompleted.value ? '初步定位校准中' : '能力画像持续更新中')
})
const adaptiveSummaryConfidence = computed(() => {
  const label = String(adaptiveSummary.value?.confidence_label || '').trim()
  return label || (adaptiveWarmupCompleted.value ? '初步判断' : '持续校准')
})
const adaptiveSummaryDescription = computed(() => {
  const evidence = Number(adaptiveSummary.value?.effective_evidence || 0)
  const conflicts = Number(adaptiveSummary.value?.pending_conflicts || 0)
  if (conflicts > 0) {
    return `发现 ${conflicts} 组需要复验的表现，后续会穿插同类题确认，不会因一道题直接升降难度。`
  }
  if (adaptiveWarmupCompleted.value) {
    return evidence > 0
      ? `已积累 ${formatEvidenceAmount(evidence)} 条有效证据；继续练习后，定位会逐步稳定。`
      : '这是初步起点，继续练习后系统会逐步提高判断置信度。'
  }
  return '下一轮仍会保留巩固、主训练和挑战题，并根据本学科表现持续校准。'
})
const summaryAdviceText = computed(() => {
  if (adaptiveWarmupCompleted.value) {
    return '这只是初步定位。建议先回看错题，再继续完成同学科校准。'
  }
  if (adaptivePracticeActive.value) {
    return '系统已记录本学科表现；回看错题后再练一组，题目会继续随你调整。'
  }
  return '建议先查看错题解析，弄清错误原因后再练一组。'
})
const aiSummaryTotal = computed(() => aiSummary.value?.total_count ?? (aiReviewResults.value.length || questionPool.value.length || 0))
const aiSummaryCorrect = computed(() => aiSummary.value?.correct_count ?? aiReviewResults.value.filter((item) => item.isCorrect).length)
const aiSummaryAccuracy = computed(() => {
  if (aiSummary.value?.accuracy !== undefined) {
    return Math.round(Number(aiSummary.value.accuracy || 0))
  }
  return aiSummaryTotal.value ? Math.round((aiSummaryCorrect.value / aiSummaryTotal.value) * 100) : 0
})
const canFavoriteCurrent = computed(() => {
  const questionId = questionMeta.value.questionId
  return Boolean(questionId) && !String(questionId).startsWith('mock-')
})
// Keep the selected option neutral until the server returns the graded result.
const optionSubmitted = computed(() => reviewMode.value || submitted.value)
const canMarkCurrentUnfamiliar = computed(() =>
  isCultureSubject.value &&
  practiceMode.value === 'special' &&
  !reviewMode.value &&
  canFavoriteCurrent.value &&
  !isCurrentMarkedUnfamiliar.value
)
const showUnfamiliarShortcut = computed(() => canMarkCurrentUnfamiliar.value && !submitted.value)
const showUnfamiliarAfterCorrect = computed(() =>
  canMarkCurrentUnfamiliar.value &&
  !currentQuestion.value?.adaptiveSessionItemId &&
  submitted.value &&
  selectedOption.value === correctAnswer.value
)
const explanationToggleText = computed(() => {
  return selectedOption.value === correctAnswer.value ? '查看解析' : '展示解析'
})
const usesScopeHeader = computed(() => mode.value === 'tags' || mode.value === 'quiz')

const pageTitle = computed(() => {
  if (mockExamMode.value) {
    return mockExamPaperTitle.value || '模拟测试'
  }
  if (mode.value === 'quiz' && adaptiveWarmupCompleted.value) {
    return '8 题智能热身'
  }
  if (mode.value === 'tags' || mode.value === 'quiz') {
    return subject.value || '专题练习'
  }
  if (isAiTrainingMode.value) {
    return 'AI 专项出题'
  }
  return practiceMode.value === 'comprehensive' ? '综合刷题' : '专项刷题'
})
const topSubtitle = computed(() => {
  if (mockExamMode.value) return `${examCode.value} / 55题 · 105分`
  if (mode.value === 'quiz' && adaptiveWarmupCompleted.value) return `${examCode.value} / ${subject.value}`
  if (mode.value === 'tags' || mode.value === 'quiz') return ''
  return `${examCode.value} / ${subject.value}`
})
const scopeHeaderStyle = computed(() => {
  const progress = Math.min(1, Math.max(0, scopeHeaderScrollTop.value / 240))
  return {
    '--scope-header-shadow-opacity': String(progress * 0.12)
  }
})
const dataModeLabel = computed(() => (hasAccessToken.value ? '将使用真实题库' : '当前使用 mock 题目'))
const selectedQuestionCount = computed(() => selectedTags.value.reduce((sum, tag) => sum + getCount(tag), 0))
const stickyTitle = computed(() => {
  if (practiceMode.value === 'comprehensive') {
    return `综合刷题：全部知识点`
  }
  return `已选：${selectedTags.value.length} 个考点`
})
const stickySub = computed(() => {
  if (practiceMode.value === 'comprehensive') {
    return `${dataModeLabel.value} · 覆盖 ${getAllModuleInfos().length} 个考点`
  }
  return `预计 ${selectedQuestionCount.value} 道题 · ${dataModeLabel.value}`
})
const startButtonText = computed(() => '开始刷题')
const cultureProgressPercent = computed(() => Math.max(0, Math.min(100, Number(cultureProgress.value.progress_percent || 0))))
const cultureProgressWidth = computed(() => `${cultureProgressPercent.value}%`)
const cultureReviewDueCount = computed(() => Number(cultureProgress.value.review_due_count || 0))
const cultureLearnedText = computed(() => formatQuestionAmount(cultureProgress.value.mastered_questions))
const cultureTotalText = computed(() => formatQuestionAmount(cultureProgress.value.total_questions))
const cultureReviewDisabled = computed(() => loading.value || cultureReviewLoading.value || (hasAccessToken.value && cultureReviewDueCount.value <= 0))
const cultureReviewButtonText = computed(() => {
  if (cultureReviewLoading.value) return '加载中'
  if (!hasAccessToken.value) return '登录后同步'
  return `${cultureReviewDueCount.value}题待复习`
})
const quizProgressText = computed(() => {
  const prefix = reviewMode.value ? '查看解析' : '当前进度'
  const total = adaptivePracticeActive.value ? adaptiveQuestionTotal.value : questionPool.value.length
  return `${prefix} ${currentQuestionIndex.value + 1} / ${total}`
})
const questionHelperText = computed(() => {
  if (mockExamMode.value) {
    return reviewMode.value
      ? '本题答案和解析已公布，可对照复盘。'
      : '本题属于 105 分轻量模拟测试，完成整卷后统一公布答案与解析。'
  }
  if (practiceMode.value === 'comprehensive') {
    return reviewMode.value ? '答案和解析已公布，可逐题回看。' : '本题知识点已隐藏，完成本轮后统一公布答案。'
  }
  return currentQuestion.value.helper
})
const primaryButtonText = computed(() => {
  if (practiceMode.value === 'comprehensive') {
    return hasNextQuestion.value ? '下一题' : (mockExamMode.value ? '交卷并查看成绩' : '提交整卷并查看答案')
  }
  return '提交'
})
const showQuestionSheetEntry = computed(() => mockExamMode.value || practiceMode.value === 'comprehensive')
const mockExamTotalScore = computed(() => MOCK_EXAM_TOTAL_SCORE)
const mockExamScore = computed(() =>
  reviewResults.value.reduce((sum, item) => sum + (item.isCorrect ? Number(item.question?.pointValue || 0) : 0), 0)
)
const mockExamSectionScores = computed(() => {
  const config = getMockExamConfig(examCode.value)
  return config.map((section) => {
    const items = reviewResults.value.filter((item) => item.question?.mockSectionKey === section.key)
    const correct = items.filter((item) => item.isCorrect).length
    return {
      key: section.key,
      label: section.label,
      correct,
      totalQuestions: section.count,
      score: correct * section.pointValue,
      totalScore: section.count * section.pointValue
    }
  })
})
const answerSheetSections = computed(() => {
  if (!questionPool.value.length) return []
  const groups = []
  questionPool.value.forEach((question, index) => {
    const label = mockExamMode.value ? question.mockSection || '模拟测试' : '本轮题目'
    let group = groups.find((item) => item.label === label)
    if (!group) {
      group = { label, items: [] }
      groups.push(group)
    }
    const answered = isQuestionAnswered(question)
    group.items.push({ index, answered })
  })
  return groups.map((group) => ({
    ...group,
    answered: group.items.filter((item) => item.answered).length
  }))
})

const formattedTimer = computed(() => {
  return formatDuration(timerSeconds.value)
})

watch(subject, () => {
  if (isAiTrainingMode.value || mockExamMode.value) {
    return
  }
  openMap.value = buildOpenMap(getSubjectTree(subject.value))
  questionPool.value = [buildMockQuestion(subject.value, examCode.value)]
  currentQuestionIndex.value = 0
  resetQuizState()
  loadCultureProgress()
})

onLoad((options) => {
  syncAccessToken()
  resumePendingAdaptiveComprehensiveSubmissions()
  if (options?.mock_paper_id) {
    const nextExamCode = decodeRouteValue(options.exam_code, examCode.value || 'Z001')
    const paperId = decodeRouteValue(options.mock_paper_id)
    examCode.value = nextExamCode
    subject.value = getMockExamThirdSubject(nextExamCode)
    uni.setStorageSync('examCode', nextExamCode)
    uni.setStorageSync('subject', subject.value)
    mockExamMode.value = true
    mockExamPaperId.value = paperId
    practiceMode.value = 'comprehensive'
    selectedQuestionSize.value = MOCK_EXAM_TOTAL_COUNT
    openMap.value = buildOpenMap(getSubjectTree(subject.value))
    startFixedMockExam(paperId)
    return
  }
  if (options?.mock_exam === '1') {
    const nextExamCode = decodeRouteValue(options.exam_code, examCode.value || 'Z001')
    examCode.value = nextExamCode
    subject.value = getMockExamThirdSubject(nextExamCode)
    uni.setStorageSync('examCode', nextExamCode)
    uni.setStorageSync('subject', subject.value)
    mockExamMode.value = true
    practiceMode.value = 'comprehensive'
    selectedQuestionSize.value = MOCK_EXAM_TOTAL_COUNT
    openMap.value = buildOpenMap(getSubjectTree(subject.value))
    startMockExam()
    return
  }
  if (options?.subject) {
    subject.value = decodeRouteValue(options.subject)
    uni.setStorageSync('subject', subject.value)
  }
  if (options?.count) {
    const nextCount = Number(decodeRouteValue(options.count))
    if (questionCountOptions.includes(nextCount)) {
      selectedQuestionSize.value = nextCount
    }
  }
  openMap.value = buildOpenMap(getSubjectTree(subject.value))
  if (options?.module && options?.submodule) {
    const module = decodeRouteValue(options.module)
    const submodule = decodeRouteValue(options.submodule)
    openMap.value = {
      ...openMap.value,
      [module]: true
    }
    selectedTags.value = [submodule]
  }
  if (options?.ai_session_id) {
    // #ifdef MP-WEIXIN
    uni.showToast({ title: '该功能暂未在小程序开放', icon: 'none' })
    setTimeout(() => {
      uni.reLaunch({ url: '/pages/home/index' })
    }, 500)
    return
    // #endif

    // #ifndef MP-WEIXIN
    aiSessionId.value = decodeRouteValue(options.ai_session_id)
    loadAiTrainingSession(aiSessionId.value)
    return
    // #endif
  }
  loadCultureProgress()
})

onShow(() => {
  syncAccessToken()
  void flushPendingAnswerSubmissions()
  resumePendingAdaptiveComprehensiveSubmissions()
  loadCultureProgress()
  if (
    mode.value === 'quiz'
    && !reviewMode.value
    && !summaryMode.value
    && !aiSummaryMode.value
    && !submitted.value
    && !questionNavigationLocked.value
    && !timerId
  ) {
    startTimer(questionMeta.value.questionId || currentQuestionKey.value)
  }
})

onHide(() => {
  clearTimer()
})

onPageScroll(({ scrollTop }) => {
  scopeHeaderScrollTop.value = Number(scrollTop) || 0
})

onUnload(() => {
  adaptiveFlowGeneration += 1
  adaptiveNextRequestBroker.invalidate()
  adaptiveLegacyFallbackTasks.clear()
  adaptiveLegacyFallbackLoading.value = false
  activeAdaptiveNextRequestToken = 0
  activeAdaptiveNextLoadingToken = 0
  activeAdaptiveNextPrefetchToken = 0
  activeAdaptiveAnswerRequestToken = 0
  activeAdaptiveEventRequestToken = 0
  activeUnfamiliarRequestToken = 0
  activeQuestionNavigationToken = 0
  activeQuizStartRequestToken = 0
  quizStartInProgress.value = false
  quizStartBackgrounded.value = false
  clearAdaptiveAnswerSubmissionTasks()
  clearTimer()
  showGradingFeedback.value = false
  // Page teardown cannot reliably finish an async session-close request. Keep
  // the durable answer queue replayable and let the server expire orphaned runs.
})

onBackPress(() => {
  if (exitConfirmVisible || exitNavigationPending) {
    return true
  }
  if (showGradingFeedback.value) {
    return true
  }
  if (practiceFlowLocked.value) {
    uni.showToast({ title: adaptiveAnswerSyncing.value ? '本题正在保存，请稍候' : '题目正在加载，请稍候', icon: 'none' })
    return true
  }
  if (isAiTrainingMode.value) {
    returnToProfilePage()
    return true
  }
  if (aiSummaryMode.value || summaryMode.value || reviewMode.value || mode.value === 'quiz') {
    confirmExitPractice()
    return true
  }
  return false
})

function buildOpenMap(sections) {
  return sections.reduce((result, item, index) => {
    result[item.module] = false
    return result
  }, {})
}

function decodeRouteValue(value, fallback = '') {
  let text = value === undefined || value === null ? fallback : String(value)
  for (let index = 0; index < 3; index += 1) {
    try {
      const decoded = decodeURIComponent(text)
      if (decoded === text) break
      text = decoded
    } catch (error) {
      break
    }
  }
  return text
}

function readAdaptivePreference() {
  try {
    const stored = String(uni.getStorageSync(ADAPTIVE_PREFERENCE_STORAGE_KEY) || '').trim()
    return adaptivePreferenceOptions.some((item) => item.value === stored) ? stored : 'standard'
  } catch (error) {
    return 'standard'
  }
}

function selectAdaptivePreference(value) {
  if (loading.value || quizStartInProgress.value) return
  const normalized = String(value || '').trim()
  if (!adaptivePreferenceOptions.some((item) => item.value === normalized)) {
    return
  }
  adaptivePreference.value = normalized
  try {
    uni.setStorageSync(ADAPTIVE_PREFERENCE_STORAGE_KEY, normalized)
  } catch (error) {
    // The selection remains valid for this page even when local storage is unavailable.
  }
}

function formatEvidenceAmount(value) {
  const numeric = Math.max(0, Number(value || 0))
  const rounded = Math.round(numeric * 10) / 10
  return Number.isInteger(rounded) ? String(rounded) : rounded.toFixed(1)
}

function readAccessToken() {
  let token = ''

  try {
    token = uni.getStorageSync('accessToken') || ''
  } catch (error) {
    token = ''
  }

  if (!token) {
    token = readLegacyH5Storage(['uni-storage-accessToken', 'accessToken'])
  }

  return typeof token === 'string' ? token.trim() : ''
}

function syncAccessToken() {
  const token = readAccessToken()
  if (token !== accessToken.value) {
    favoriteStatusCache.clear()
  }
  accessToken.value = token
  if (token) {
    uni.setStorageSync('accessToken', token)
  }
}

function buildMockQuestion(nextSubject, nextExamCode, index = 0) {
  const mock = getPracticeQuestion(nextSubject, nextExamCode)
  return {
    ...mock,
    id: `${mock.id}-${index}`,
    year: mock.year || '题库练习',
    badge: mock.badge || '专项练习',
    helper: `${mock.helper}（mock 模式）`
  }
}

function buildEmptyAiQuestion() {
  return {
    id: 'ai-loading',
    year: 'AI 训练',
    badge: '正在整理',
    stem: '正在整理 AI 训练题目...',
    helper: '如果长时间停留在这里，请返回重新生成训练。',
    options: [],
    answer: '',
    explanation: '',
    autoTag: '',
    questionId: '',
    module: '',
    submodule: ''
  }
}

function buildApiQuestion(apiQuestion, meta) {
  const options = [
    { key: 'A', text: apiQuestion.option_a },
    { key: 'B', text: apiQuestion.option_b },
    { key: 'C', text: apiQuestion.option_c },
    { key: 'D', text: apiQuestion.option_d }
  ]
  let sourceLabel = '真实题库'
  // #ifndef MP-WEIXIN
  sourceLabel = apiQuestion.source_type === 'ai_deepseek' ? 'AI专项出题' : '真实题库'
  // #endif

  return {
    id: apiQuestion.id,
    year: apiQuestion.source_year ? `${apiQuestion.source_year} 年题目` : '题库练习',
    badge: meta.submodule || apiQuestion.submodule || meta.module || apiQuestion.module,
    stem: apiQuestion.stem,
    helper: `当前来自${sourceLabel}：${apiQuestion.subject} / ${apiQuestion.module} / ${apiQuestion.submodule}`,
    options,
    answer: '',
    explanation: '',
    autoTag: '',
    questionId: apiQuestion.id,
    exam_code: apiQuestion.exam_code,
    subject: apiQuestion.subject,
    module: apiQuestion.module,
    submodule: apiQuestion.submodule,
    difficulty: apiQuestion.difficulty,
    source_type: apiQuestion.source_type,
    source_year: apiQuestion.source_year,
    mockSection: meta.mockSection || '',
    mockSectionKey: meta.mockSectionKey || '',
    pointValue: meta.pointValue || 1
  }
}

function getCurrentAdaptiveSubmissionOwnerId() {
  try {
    const user = getAuthUser() || {}
    return String(user.id || user.user_id || user.userId || '').trim()
  } catch (error) {
    return ''
  }
}

function resumePendingAdaptiveComprehensiveSubmissions() {
  if (!hasAccessToken.value || !getCurrentAdaptiveSubmissionOwnerId()) return
  void adaptiveComprehensiveSubmissionQueue.resumeAll().catch(() => {
    // A failed read or replay keeps the owner-scoped task untouched. The next
    // page show retries the exact same session and immutable payload.
  })
}

function isAdaptiveCreateFallbackError(error) {
  return [404, 503].includes(Number(error?.statusCode || error?.status || 0))
}

function isAdaptiveCreateImmediateFallbackError(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  if (statusCode === 404) return true
  if (statusCode !== 503) return false
  return /ADAPTIVE_(?:MIGRATION_PENDING|DIAGNOSTIC_POOL_UNAVAILABLE|COMPREHENSIVE_POOL_UNAVAILABLE)|个性化出题正在灰度开放|个性化出题数据迁移尚未启用/i.test(
    adaptiveErrorText(error)
  )
}

function adaptiveErrorText(error) {
  if (typeof error === 'string') return error
  try {
    return JSON.stringify(error || '')
  } catch (serializationError) {
    return String(error?.code || error?.error || error?.detail || error?.message || '')
  }
}

function adaptiveErrorMessage(error, fallback) {
  const detail = error?.detail
  if (typeof detail === 'string' && detail.trim()) return detail
  if (detail && typeof detail === 'object') {
    const message = detail.message || detail.error || detail.code
    if (typeof message === 'string' && message.trim()) return message
  }
  if (typeof error?.message === 'string' && error.message.trim()) return error.message
  return fallback
}

function isAdaptiveUpdatePendingError(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  return statusCode === 409 && /ADAPTIVE_UPDATE_PENDING/i.test(adaptiveErrorText(error))
}

function isAdaptiveComprehensiveSubmissionPendingError(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  const detailCode = String(error?.detail?.code || '').trim().toUpperCase()
  return statusCode === 409 && detailCode === 'ADAPTIVE_COMPREHENSIVE_SUBMISSION_PENDING'
}

function isAdaptiveNextFallbackError(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  if (statusCode === 404) return true
  if (statusCode !== 503) return false
  return /ADAPTIVE_(?:MIGRATION_PENDING|DIAGNOSTIC_POOL_UNAVAILABLE)/i.test(adaptiveErrorText(error))
}

function isAdaptiveSafePoolError(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  return statusCode === 503 && /ADAPTIVE_SAFE_POOL_UNAVAILABLE/i.test(adaptiveErrorText(error))
}

function isAdaptiveCreateRetryableError(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  if (isAdaptiveCreateImmediateFallbackError(error)) return false
  return error?.retryable === true || [408, 429, 502, 503, 504].includes(statusCode)
}

function captureAdaptiveQuestionContext(question = currentQuestion.value) {
  return {
    flowGeneration: adaptiveFlowGeneration,
    sessionId: String(question?.adaptiveSessionId || adaptiveSession.value?.id || ''),
    itemId: String(question?.adaptiveSessionItemId || ''),
    questionKey: String(question?.questionId || question?.id || '')
  }
}

function isAdaptiveSessionContextCurrent(context) {
  if (!context) return true
  return (
    context.flowGeneration === adaptiveFlowGeneration &&
    (!context.sessionId || String(adaptiveSession.value?.id || '') === context.sessionId)
  )
}

function isAdaptiveQuestionContextCurrent(context) {
  if (!isAdaptiveSessionContextCurrent(context)) return false
  return (
    String(currentQuestionKey.value || '') === context.questionKey &&
    String(currentQuestion.value?.adaptiveSessionItemId || '') === context.itemId
  )
}

function adaptiveContextsMatch(left, right) {
  return Boolean(
    left &&
    right &&
    left.flowGeneration === right.flowGeneration &&
    left.sessionId === right.sessionId &&
    left.itemId === right.itemId &&
    left.questionKey === right.questionKey
  )
}

function adaptiveAnswerSubmissionTaskKey(context) {
  if (!context) return ''
  return [
    context.flowGeneration,
    context.sessionId,
    context.itemId,
    context.questionKey
  ].join(':')
}

function clearAdaptiveAnswerSubmissionTasks() {
  for (const task of adaptiveAnswerSubmissionTasks.values()) {
    releaseAnswerSubmissionSettlement(task.submissionId)
  }
  adaptiveAnswerSubmissionTasks.clear()
}

function adaptiveSubmissionBarrierSatisfied(result) {
  const adaptive = getAdaptiveSubmissionOutcome(result)
  return result?.persisted === true && adaptive?.adaptive_updated === true
}

function isAdaptiveSubmissionRetryableError(error) {
  const statusCode = Number(error?.statusCode || error?.status || 0)
  return (
    isAdaptiveUpdatePendingError(error) ||
    isAdaptiveComprehensiveSubmissionPendingError(error) ||
    error?.retryable === true ||
    [408, 429, 500, 502, 503, 504].includes(statusCode) ||
    /NETWORK_(?:TIMEOUT|ERROR)/i.test(String(error?.code || ''))
  )
}

function rememberAdaptiveAnswerSubmission(
  context,
  payload,
  question,
  { initialInFlight = false } = {}
) {
  const key = adaptiveAnswerSubmissionTaskKey(context)
  const submissionId = String(payload?.client_submission_id || '')
  if (!key || !submissionId) return null
  const existing = adaptiveAnswerSubmissionTasks.get(key)
  if (existing) return existing

  let markInitialFlowDone = () => {}
  const initialFlowDonePromise = initialInFlight
    ? new Promise((resolve) => {
        markInitialFlowDone = resolve
      })
    : Promise.resolve()
  const task = {
    submissionId,
    context: { ...context },
    payload: { ...payload },
    question,
    initialPromise: null,
    initialFlowDonePromise,
    markInitialFlowDone,
    settlementPromise: waitForAnswerSubmissionSettlement(submissionId),
    readyPromise: null
  }
  adaptiveAnswerSubmissionTasks.set(key, task)
  task.readyPromise = Promise.all([
    task.settlementPromise,
    task.initialFlowDonePromise
  ]).then(async ([outcome]) => {
    if (adaptiveAnswerSubmissionTasks.get(key) !== task) {
      return false
    }
    if (!isAdaptiveSessionContextCurrent(task.context)) {
      adaptiveAnswerSubmissionTasks.delete(key)
      releaseAnswerSubmissionSettlement(task.submissionId)
      return false
    }
    if (outcome?.status === 'terminal') {
      if (outcome?.result?.persisted === true) {
        applyAdaptiveSubmissionResult(outcome.result)
        await switchAdaptiveSessionToLegacy('cancelled', task.context)
        if (
          adaptiveAnswerSubmissionTasks.get(key) !== task ||
          !isAdaptiveSessionContextCurrent(task.context)
        ) {
          return false
        }
        adaptivePendingSubmissionPayloads.delete(task.context.itemId)
        if (isAdaptiveQuestionContextCurrent(task.context)) {
          drainAdaptiveNavigationIntent(task.context)
        }
        adaptiveAnswerSubmissionTasks.delete(key)
        releaseAnswerSubmissionSettlement(task.submissionId)
        return true
      }
      adaptivePendingSubmissionPayloads.set(task.context.itemId, { ...task.payload })
      clearAdaptiveNavigationIntent(task.context)
      if (isAdaptiveQuestionContextCurrent(task.context)) {
        resultTag.value = '作答已判分，但保存没有完成，请退出本轮后重试。'
        uni.showToast({ title: '本题保存未完成，不会跳过这道题', icon: 'none' })
      }
      return false
    }

    const result = outcome?.result
    applyAdaptiveSubmissionResult(result)
    if (outcome?.status === 'migration') {
      await switchAdaptiveSessionToLegacy('cancelled', task.context)
    } else if (!adaptiveSubmissionBarrierSatisfied(result)) {
      return false
    }
    if (
      adaptiveAnswerSubmissionTasks.get(key) !== task ||
      !isAdaptiveSessionContextCurrent(task.context)
    ) {
      return false
    }

    adaptivePendingSubmissionPayloads.delete(task.context.itemId)
    if (result?.correct_answer) {
      applyResponsiveAnswerFeedback({
        question: task.question,
        questionKey: task.context.questionKey,
        selectedAnswer: task.payload.selected_answer,
        correctAnswer: result.correct_answer,
        explanation: result.explanation,
        isCorrect: result.is_correct,
        addedToWrongQuestions: result.added_to_wrong_questions,
        persisted: true,
        nextAbilityAccuracy: result.ability_accuracy ?? null
      })
    }
    if (isAdaptiveQuestionContextCurrent(task.context)) {
      void prefetchNextAdaptiveQuestion(task.question, task.context)
      drainAdaptiveNavigationIntent(task.context)
    }
    adaptiveAnswerSubmissionTasks.delete(key)
    releaseAnswerSubmissionSettlement(task.submissionId)
    return true
  })
  void task.readyPromise.catch(() => {})
  return task
}

function queueAdaptiveNavigationIntent(action) {
  if (!adaptiveForwardNavigationQueueable.value) return false
  const context = captureAdaptiveQuestionContext()
  if (adaptiveContextsMatch(adaptiveQueuedNavigation.value?.context, context)) return true
  setAdaptiveNavigationIntent(action, context, { ready: true })
  return true
}

function setAdaptiveNavigationIntent(action, context, { ready = false } = {}) {
  adaptiveQueuedNavigation.value = { action, context: { ...context }, ready }
}

function clearAdaptiveNavigationIntent(context) {
  if (!adaptiveContextsMatch(adaptiveQueuedNavigation.value?.context, context)) return false
  adaptiveQueuedNavigation.value = null
  return true
}

function drainAdaptiveNavigationIntent(context) {
  const queued = adaptiveQueuedNavigation.value
  if (!queued || !adaptiveContextsMatch(queued.context, context)) return false
  if (!isAdaptiveQuestionContextCurrent(context)) {
    adaptiveQueuedNavigation.value = null
    return false
  }
  const fallbackTask = getAdaptiveLegacyFallbackTask(context)
  if (fallbackTask && !fallbackTask.settled) {
    adaptiveQueuedNavigation.value = { ...queued, ready: false }
    return false
  }
  if (questionNavigationLocked.value) {
    adaptiveQueuedNavigation.value = { ...queued, ready: true }
    return false
  }
  adaptiveQueuedNavigation.value = null
  if (queued.action === 'finish') {
    if (practiceMode.value === 'comprehensive' && !mockExamMode.value && !reviewMode.value) {
      void submitComprehensiveAnswers()
    } else {
      void finishQuiz()
    }
    return true
  }
  if (hasNextQuestion.value) {
    void goNextQuestion()
  } else if (adaptiveNextExhausted.value || adaptiveNextFinishAvailable.value) {
    // The background observer drains before its prefetch flag is cleared. Give
    // the terminal result priority so that a stale "prefetching" bit cannot
    // consume the learner's tap and leave them needing to tap Finish again.
    void finishQuiz()
  } else if (canAdvanceQuestion.value) {
    void goNextQuestion()
  } else {
    void finishQuiz()
  }
  return true
}

function resetAdaptivePracticeState() {
  adaptiveFlowGeneration += 1
  adaptiveNextRequestBroker.invalidate()
  adaptiveLegacyFallbackTasks.clear()
  activeAdaptiveNextRequestToken = 0
  activeAdaptiveNextLoadingToken = 0
  activeAdaptiveNextPrefetchToken = 0
  activeAdaptiveAnswerRequestToken = 0
  activeAdaptiveEventRequestToken = 0
  activeUnfamiliarRequestToken = 0
  activeQuestionNavigationToken = 0
  adaptiveSession.value = null
  adaptiveSummary.value = null
  adaptiveInitialPhase.value = ''
  adaptiveInitialReliableCount.value = null
  adaptiveNextLoading.value = false
  adaptiveNextPrefetching.value = false
  adaptiveAnswerSyncing.value = false
  adaptiveEventSyncing.value = false
  adaptiveFallbackMode.value = false
  adaptiveLegacyFallbackLoading.value = false
  adaptiveNextExhausted.value = false
  adaptiveNextFinishAvailable.value = false
  adaptiveQueuedNavigation.value = null
  questionNavigationPending.value = false
  adaptiveRecordedEvents = new Set()
  adaptivePendingSubmissionPayloads = new Map()
  adaptiveComprehensiveSubmissionSnapshot = null
  clearAdaptiveAnswerSubmissionTasks()
  adaptiveAnswerSubmissionTasks = new Map()
}

function buildAdaptiveQuestion(item) {
  const apiQuestion = item?.question
  if (!item?.id || !apiQuestion?.id) {
    return null
  }
  return {
    ...buildApiQuestion(apiQuestion, {
      module: apiQuestion.module,
      submodule: apiQuestion.submodule
    }),
    adaptiveSessionId: String(item.session_id || adaptiveSession.value?.id || ''),
    adaptiveSessionItemId: String(item.id),
    adaptivePosition: Number(item.position || 0),
    adaptiveTargetZone: String(item.target_zone || ''),
    adaptiveReasonCodes: Array.isArray(item.reason_codes) ? item.reason_codes : [],
    adaptivePredictedCorrectProbability: item.predicted_correct_probability ?? null,
    adaptiveDiagnostic: item.is_diagnostic === true,
    adaptiveChallenge: item.is_challenge === true
  }
}

function mergeAdaptiveState(state) {
  if (!state || typeof state !== 'object' || Array.isArray(state)) {
    return
  }
  adaptiveSummary.value = {
    ...(adaptiveSummary.value || {}),
    ...state
  }
}

function applyAdaptiveEnvelope(response, { captureInitialPhase = false } = {}) {
  if (response?.session?.id) {
    adaptiveSession.value = {
      ...(adaptiveSession.value || {}),
      ...response.session
    }
  }
  if (response?.state) {
    mergeAdaptiveState(response.state)
  }
  if (captureInitialPhase) {
    if (!adaptiveInitialPhase.value) {
      adaptiveInitialPhase.value = String(
        response?.state?.diagnostic_status || response?.session?.diagnostic_status || ''
      ).trim().toUpperCase()
    }
    if (adaptiveInitialReliableCount.value === null) {
      const reliableCount = Number(response?.state?.reliable_first_attempt_count)
      adaptiveInitialReliableCount.value = Number.isFinite(reliableCount) ? reliableCount : null
    }
  }
}

function applyAdaptiveSubmissionResult(result) {
  const adaptive = result?.adaptive || result?.adaptive_state
  if (!adaptive || typeof adaptive !== 'object') {
    return
  }
  if (adaptive.state && typeof adaptive.state === 'object') {
    mergeAdaptiveState(adaptive.state)
    return
  }
  if (
    adaptive.theta !== undefined ||
    adaptive.effective_evidence !== undefined ||
    adaptive.diagnostic_status !== undefined
  ) {
    mergeAdaptiveState(adaptive)
  }
}

function getAdaptiveSubmissionOutcome(result) {
  const adaptive = result?.adaptive || result?.adaptive_state
  return adaptive && typeof adaptive === 'object' ? adaptive : null
}

function adaptiveSubmissionNeedsRetry(result) {
  const adaptive = getAdaptiveSubmissionOutcome(result)
  return (
    adaptive?.adaptive_updated === false &&
    (adaptive?.retryable === true || /ADAPTIVE_UPDATE_PENDING/i.test(String(adaptive?.error || '')))
  )
}

function adaptiveMigrationPending(result) {
  return (
    result?.persisted === true &&
    getAdaptiveSubmissionOutcome(result)?.migration_pending === true
  )
}

async function settleAdaptiveSubmission(
  result,
  payload,
  itemId,
  { retryOnce = true, context = null } = {}
) {
  let finalResult = result
  const canTouchCurrentFlow = () => isAdaptiveSessionContextCurrent(context)
  if (adaptiveMigrationPending(finalResult)) {
    if (canTouchCurrentFlow()) {
      startAdaptiveLegacyFallbackTask('cancelled', context)
      adaptivePendingSubmissionPayloads.delete(itemId)
    }
    return finalResult
  }

  if (retryOnce && adaptiveSubmissionNeedsRetry(finalResult)) {
    try {
      finalResult = await submitAnswerWithReliableSync(payload, {
        queueScopeKey: context?.sessionId || adaptiveSession.value?.id
      })
    } catch (error) {
      if (canTouchCurrentFlow()) {
        adaptivePendingSubmissionPayloads.set(itemId, { ...payload })
        uni.showToast({ title: '本题已保存，个性化进度同步中，请重试', icon: 'none' })
      }
      return result
    }
  }

  if (adaptiveMigrationPending(finalResult)) {
    if (canTouchCurrentFlow()) {
      startAdaptiveLegacyFallbackTask('cancelled', context)
      adaptivePendingSubmissionPayloads.delete(itemId)
    }
  } else if (adaptiveSubmissionNeedsRetry(finalResult)) {
    if (canTouchCurrentFlow()) {
      adaptivePendingSubmissionPayloads.set(itemId, { ...payload })
      uni.showToast({ title: '本题已保存，个性化进度同步中，请重试', icon: 'none' })
    }
  } else if (canTouchCurrentFlow()) {
    adaptivePendingSubmissionPayloads.delete(itemId)
  }
  return finalResult
}

function continueAdaptiveProgressInBackground(progressRequest, context) {
  void progressRequest
    .then((ready) => {
      if (!isAdaptiveQuestionContextCurrent(context)) {
        clearAdaptiveNavigationIntent(context)
        return
      }
      if (ready) {
        drainAdaptiveNavigationIntent(context)
      } else {
        clearAdaptiveNavigationIntent(context)
      }
    })
    .catch(() => {
      clearAdaptiveNavigationIntent(context)
    })
}

async function ensureAdaptiveProgressBeforeNext(
  question,
  { navigationAction = 'next' } = {}
) {
  const itemId = String(question?.adaptiveSessionItemId || '')
  const payload = adaptivePendingSubmissionPayloads.get(itemId)
  const context = captureAdaptiveQuestionContext(question)
  const fallbackTask = getAdaptiveLegacyFallbackTask(context)
  if (!fallbackTask && (!itemId || !payload)) {
    return true
  }

  let progressRequest
  if (fallbackTask) {
    progressRequest = fallbackTask.promise.then((outcome) => outcome?.ready === true)
  } else {
    const task = rememberAdaptiveAnswerSubmission(context, payload, question)
    if (!task) return false
    schedulePendingAnswerFlush(0, { queueScopeKey: context.sessionId })
    progressRequest = task.readyPromise
  }
  const loadingToken = ++adaptiveNextLoadingSequence
  activeAdaptiveNextLoadingToken = loadingToken
  adaptiveNextLoading.value = true

  try {
    const outcome = await Promise.race([
      progressRequest,
      new Promise((resolve) => {
        setTimeout(
          () => resolve(ADAPTIVE_PREFETCH_STILL_RUNNING),
          ADAPTIVE_FOREGROUND_PREFETCH_WAIT_MS
        )
      })
    ])
    if (outcome === ADAPTIVE_PREFETCH_STILL_RUNNING) {
      const action = navigationAction === 'finish' ? 'finish' : 'next'
      setAdaptiveNavigationIntent(action, context, { ready: false })
      continueAdaptiveProgressInBackground(progressRequest, context)
      uni.showToast({
        title: action === 'finish'
          ? '个性化进度后台同步，完成后自动展示结果'
          : '个性化进度后台同步，完成后自动继续',
        icon: 'none'
      })
      return false
    }
    return outcome === true
  } finally {
    if (activeAdaptiveNextLoadingToken === loadingToken) {
      activeAdaptiveNextLoadingToken = 0
      adaptiveNextLoading.value = false
    }
  }
}

async function recordAdaptiveEvent(question, eventType) {
  const sessionId = String(question?.adaptiveSessionId || adaptiveSession.value?.id || '')
  const itemId = String(question?.adaptiveSessionItemId || '')
  if (!sessionId || !itemId || adaptiveFallbackMode.value) {
    return false
  }
  const eventKey = `${sessionId}:${itemId}:${eventType}`
  if (adaptiveRecordedEvents.has(eventKey)) {
    return true
  }
  adaptiveRecordedEvents.add(eventKey)
  try {
    await recordAdaptivePracticeItemEvent(sessionId, itemId, eventType)
    return true
  } catch (error) {
    adaptiveRecordedEvents.delete(eventKey)
    return false
  }
}

async function endAdaptiveSession(reason = 'completed') {
  const session = adaptiveSession.value
  const sessionId = String(session?.id || '')
  const flowGeneration = adaptiveFlowGeneration
  const currentQuestionSnapshot = currentQuestion.value
  const status = String(session?.status || '').trim().toLowerCase()
  if (!sessionId || ['completed', 'abandoned', 'cancelled'].includes(status)) {
    return null
  }
  if (adaptiveClosingSessionIds.has(sessionId)) {
    return null
  }

  adaptiveClosingSessionIds.add(sessionId)
  try {
    if (reason === 'abandoned' && !submitted.value && !reviewMode.value) {
      await recordAdaptiveEvent(currentQuestionSnapshot, 'abandoned')
    }
    const response = await completeAdaptivePracticeSession(sessionId, reason)
    if (
      flowGeneration === adaptiveFlowGeneration &&
      adaptiveSession.value?.id === sessionId
    ) {
      adaptiveSession.value = {
        ...adaptiveSession.value,
        status: response?.status || reason
      }
      mergeAdaptiveState(response?.state)
    }
    return response
  } catch (error) {
    if (reason === 'completed') {
      throw error
    }
    return null
  } finally {
    adaptiveClosingSessionIds.delete(sessionId)
  }
}

function getMockExamThirdSubject(code) {
  return code === 'Z002' ? '数学基础' : '逻辑推理'
}

function getMockExamConfig(code) {
  const thirdSubject = getMockExamThirdSubject(code)
  return [
    {
      key: 'culture',
      label: '中华文化常识',
      subject: '中华文化',
      count: 20,
      pointValue: 2,
      include: (item) => !isReadingQuestion(item)
    },
    {
      key: 'english',
      label: '英语语言知识',
      subject: '英语运用',
      count: 20,
      pointValue: 1,
      include: (item) => item.module === '语言知识' && !isReadingQuestion(item)
    },
    {
      key: 'third',
      label: thirdSubject,
      subject: thirdSubject,
      count: 15,
      pointValue: 3,
      include: () => true
    }
  ]
}

function isReadingQuestion(item) {
  const text = [item.module, item.submodule, item.stem].filter(Boolean).join(' ')
  return text.includes('阅读理解') || text.includes('阅读')
}

function getDifficultyBand(item) {
  const value = item?.difficulty
  if (typeof value === 'number') {
    if (value <= 2) return 'basic'
    if (value === 3) return 'medium'
    return 'hard'
  }

  const text = String(value || '').trim()
  if (text.includes('较难') || text.includes('困难') || text.includes('挑战')) return 'hard'
  if (text.includes('中等') || text.includes('标准') || text.includes('提升')) return 'medium'
  if (text.includes('基础') || text.includes('简单') || text.includes('巩固')) return 'basic'
  return 'medium'
}

function getMockDifficultyTargets(total) {
  const targets = MOCK_EXAM_DIFFICULTY_PROFILE.map((item) => {
    const exact = item.ratio * total
    return {
      ...item,
      count: Math.floor(exact),
      remainder: exact - Math.floor(exact)
    }
  })
  let remaining = total - targets.reduce((sum, item) => sum + item.count, 0)
  const byRemainder = [...targets].sort((a, b) => b.remainder - a.remainder)

  for (let index = 0; remaining > 0; index = (index + 1) % byRemainder.length) {
    byRemainder[index].count += 1
    remaining -= 1
  }

  return targets
}

function selectStandardMockExamItems(items, count) {
  const shuffled = shuffleArray(items)
  const grouped = {
    basic: [],
    medium: [],
    hard: []
  }

  shuffled.forEach((item) => {
    grouped[getDifficultyBand(item)].push(item)
  })

  const selected = []
  const usedKeys = new Set()
  const targets = getMockDifficultyTargets(count)

  targets.forEach((target) => {
    const group = grouped[target.key] || []
    while (selected.length < count && group.length && selected.filter((item) => getDifficultyBand(item) === target.key).length < target.count) {
      const item = group.shift()
      const key = getQuestionIdentityKey(item)
      if (!item || usedKeys.has(key)) continue
      selected.push(item)
      usedKeys.add(key)
    }
  })

  for (const item of shuffled) {
    if (selected.length >= count) break
    const key = getQuestionIdentityKey(item)
    if (!item || usedKeys.has(key)) continue
    selected.push(item)
    usedKeys.add(key)
  }

  return shuffleArray(selected).slice(0, count)
}

function buildMockPool() {
  return Array.from({ length: selectedQuestionSize.value }, (_, index) => buildMockQuestion(subject.value, examCode.value, index))
}

function shuffleArray(items) {
  const result = [...items]
  for (let index = result.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1))
    ;[result[index], result[swapIndex]] = [result[swapIndex], result[index]]
  }
  return result
}

function normalizeQuestionStem(value) {
  return String(value || '')
    .replace(/\s+/g, '')
    .replace(/[，。！？；：,.!?;:()[\]（）【】“”‘’"']/g, '')
    .toLowerCase()
}

function getQuestionIdentityKey(item) {
  const stemKey = normalizeQuestionStem(item?.stem)
  return stemKey || String(item?.questionId || item?.id || '')
}

function formatQuestionAmount(value) {
  const numeric = Number(value || 0)
  if (numeric >= 1000) {
    const rounded = Math.round(numeric / 100) / 10
    return `${rounded}k题`
  }
  return `${numeric}题`
}

function buildRandomQuestionPool(candidateGroups) {
  const groups = candidateGroups.map((group) => shuffleArray(group)).filter((group) => group.length)
  const selected = []
  const usedKeys = new Set()

  while (selected.length < plannedQuestionLimit.value && groups.some((group) => group.length)) {
    for (const group of groups) {
      const item = group.shift()
      const key = getQuestionIdentityKey(item)
      if (!item || usedKeys.has(key)) {
        continue
      }
      selected.push(item)
      usedKeys.add(key)
      if (selected.length >= plannedQuestionLimit.value) {
        break
      }
    }
  }

  return shuffleArray(selected)
}

function normalizeDifficulty(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric)) return 3
  return Math.min(5, Math.max(1, Math.round(numeric)))
}

function buildDiagnosticDifficultyTargets(limit) {
  const targets = {}
  DIFFICULTY_LEVELS.forEach((level) => {
    targets[level] = 0
  })
  for (let index = 0; index < limit; index += 1) {
    targets[DIFFICULTY_LEVELS[index % DIFFICULTY_LEVELS.length]] += 1
  }
  return targets
}

function buildAdaptiveDifficultyTargets(limit, historyItems = []) {
  const recentItems = historyItems
    .filter((item) => item?.question?.difficulty)
    .slice(0, Math.max(ADAPTIVE_HISTORY_MIN_COUNT, 20))

  if (recentItems.length < ADAPTIVE_HISTORY_MIN_COUNT) {
    return {
      mode: 'diagnostic',
      mainDifficulty: 3,
      targets: buildDiagnosticDifficultyTargets(limit)
    }
  }

  const correctCount = recentItems.filter((item) => item.is_correct).length
  const accuracy = correctCount / recentItems.length
  const averageDifficulty =
    recentItems.reduce((sum, item) => sum + normalizeDifficulty(item.question?.difficulty), 0) / recentItems.length
  let mainDifficulty = normalizeDifficulty(averageDifficulty)

  if (accuracy >= 0.8) {
    mainDifficulty = normalizeDifficulty(mainDifficulty + 1)
  } else if (accuracy < 0.55) {
    mainDifficulty = normalizeDifficulty(mainDifficulty - 1)
  }

  const lowerDifficulty = normalizeDifficulty(mainDifficulty - 1)
  const upperDifficulty = normalizeDifficulty(mainDifficulty + 1)
  const targets = {}
  DIFFICULTY_LEVELS.forEach((level) => {
    targets[level] = 0
  })
  targets[mainDifficulty] += Math.max(1, Math.round(limit * 0.5))
  if (lowerDifficulty !== mainDifficulty) {
    targets[lowerDifficulty] += Math.max(1, Math.floor(limit * 0.2))
  }
  if (upperDifficulty !== mainDifficulty) {
    targets[upperDifficulty] += Math.max(1, Math.floor(limit * 0.2))
  }

  let assigned = Object.values(targets).reduce((sum, count) => sum + count, 0)
  while (assigned < limit) {
    targets[mainDifficulty] += 1
    assigned += 1
  }
  while (assigned > limit && targets[mainDifficulty] > 1) {
    targets[mainDifficulty] -= 1
    assigned -= 1
  }

  return {
    mode: 'adaptive',
    mainDifficulty,
    targets
  }
}

function buildAdaptiveQuestionPool(candidateGroups, historyItems = []) {
  const limit = plannedQuestionLimit.value
  const candidates = []
  const seenKeys = new Set()

  candidateGroups.flat().forEach((item) => {
    const key = getQuestionIdentityKey(item)
    if (!item || seenKeys.has(key)) return
    candidates.push(item)
    seenKeys.add(key)
  })

  const profile = buildAdaptiveDifficultyTargets(limit, historyItems)
  const buckets = {}
  DIFFICULTY_LEVELS.forEach((level) => {
    buckets[level] = []
  })
  shuffleArray(candidates).forEach((item) => {
    buckets[normalizeDifficulty(item.difficulty)].push(item)
  })

  const selected = []
  const usedKeys = new Set()
  DIFFICULTY_LEVELS.forEach((level) => {
    const targetCount = profile.targets[level] || 0
    while (selected.length < limit && buckets[level].length && selected.filter((item) => normalizeDifficulty(item.difficulty) === level).length < targetCount) {
      const item = buckets[level].shift()
      const key = getQuestionIdentityKey(item)
      if (!item || usedKeys.has(key)) continue
      selected.push(item)
      usedKeys.add(key)
    }
  })

  for (const item of shuffleArray(candidates)) {
    if (selected.length >= limit) break
    const key = getQuestionIdentityKey(item)
    if (!item || usedKeys.has(key)) continue
    selected.push(item)
    usedKeys.add(key)
  }

  return shuffleArray(selected)
}

function getSelectedModuleInfos() {
  return selectedTags.value
    .map((tag) => {
      const found = subjectTree.value.find((section) => section.submodules.includes(tag))
      if (!found) {
        return null
      }
      return {
        module: found.module,
        submodule: tag
      }
    })
    .filter(Boolean)
}

function getAllModuleInfos() {
  return subjectTree.value.flatMap((section) =>
    section.submodules.map((submodule) => ({
      module: section.module,
      submodule
    }))
  )
}

function getTargetModuleInfos(modeValue = practiceMode.value) {
  return modeValue === 'comprehensive' ? getAllModuleInfos() : getSelectedModuleInfos()
}

function capturePracticeStartContext() {
  const practiceModeSnapshot = practiceMode.value
  return {
    examCode: String(examCode.value || ''),
    subject: String(subject.value || ''),
    practiceMode: practiceModeSnapshot,
    questionCount: Number(selectedQuestionSize.value || 0),
    preference: practiceModeSnapshot === 'special' ? adaptivePreference.value : 'standard'
  }
}

function isPracticeStartContextCurrent(context) {
  if (!context) return false
  return (
    String(examCode.value || '') === context.examCode &&
    String(subject.value || '') === context.subject &&
    practiceMode.value === context.practiceMode &&
    Number(selectedQuestionSize.value || 0) === context.questionCount &&
    (context.practiceMode !== 'special' || adaptivePreference.value === context.preference)
  )
}

function getCacheKey(moduleInfos) {
  return JSON.stringify({
    mode: practiceMode.value,
    examCode: examCode.value,
    subject: subject.value,
    tags: moduleInfos.map((item) => `${item.module}:${item.submodule}`).sort(),
    seed: practiceMode.value === 'comprehensive' ? Date.now() : ''
  })
}

function buildQuery(params) {
  return Object.keys(params)
    .filter((key) => params[key] !== undefined && params[key] !== null && params[key] !== '')
    .map((key) => `${encodeURIComponent(key)}=${encodeURIComponent(params[key])}`)
    .join('&')
}

function goBack() {
  if (practiceFlowLocked.value) {
    uni.showToast({ title: adaptiveAnswerSyncing.value ? '本题正在保存，请稍候' : '题目正在处理，请稍候', icon: 'none' })
    return
  }
  if (isAiTrainingMode.value) {
    returnToProfilePage()
    return
  }

  if (aiSummaryMode.value || summaryMode.value || reviewMode.value || mode.value === 'quiz') {
    confirmExitPractice()
    return
  }

  uni.navigateBack({
    delta: 1,
    fail() {
      uni.redirectTo({ url: '/pages/subjects/index' })
    }
  })
}

function returnToProfilePage() {
  clearTimer()
  aiSessionId.value = ''
  uni.reLaunch({
    url: '/pages/home/index?tab=profile',
    fail() {
      uni.redirectTo({ url: '/pages/home/index?tab=profile' })
    }
  })
}

function confirmExitPractice() {
  if (exitConfirmVisible || exitNavigationPending) return
  if (practiceFlowLocked.value) {
    uni.showToast({ title: adaptiveAnswerSyncing.value ? '本题正在保存，请稍候' : '题目正在处理，请稍候', icon: 'none' })
    return
  }

  exitConfirmVisible = true
  let shouldExit = false
  uni.showModal({
    title: mockExamMode.value ? '退出模拟测试？' : '退出本次练习？',
    content: mockExamMode.value ? '退出后本次模拟测试进度不会继续保留。' : '退出后本轮未完成的题目不会继续保留，已提交的答案仍会保存。',
    confirmText: '退出',
    cancelText: '继续做题',
    success(result) {
      shouldExit = Boolean(result.confirm)
    },
    complete() {
      exitConfirmVisible = false
      if (!shouldExit) return

      if (mockExamMode.value) {
        clearTimer()
        setTimeout(returnToMockExamList, 30)
        return
      }
      adaptiveQueuedNavigation.value = null
      resetToTags()
    }
  })
}

function switchPracticeMode(value) {
  if (loading.value || quizStartInProgress.value) return
  practiceMode.value = value
  selectedTags.value = []
  resetQuizState()
}

function normalizeQuestionSize(value) {
  const numeric = Number(value || selectedQuestionSize.value || 10)
  const min = questionCountOptions[0]
  const max = questionCountOptions[questionCountOptions.length - 1]
  const snapped = Math.round(numeric / 5) * 5
  return Math.min(max, Math.max(min, snapped))
}

function getQuestionScalePosition(count) {
  const min = questionCountOptions[0]
  const max = questionCountOptions[questionCountOptions.length - 1]
  const percent = ((Number(count) - min) / (max - min)) * 100
  return `${percent}%`
}

function handleQuestionSizeChange(event) {
  if (loading.value || quizStartInProgress.value) return
  selectedQuestionSize.value = normalizeQuestionSize(event?.detail?.value)
}

function toggleOpen(module) {
  if (loading.value || quizStartInProgress.value) return
  openMap.value = {
    ...openMap.value,
    [module]: !openMap.value[module]
  }
}

function toggleTag(tag) {
  if (loading.value || quizStartInProgress.value) return
  if (selectedTags.value.includes(tag)) {
    selectedTags.value = selectedTags.value.filter((item) => item !== tag)
    return
  }
  selectedTags.value = [...selectedTags.value, tag]
}

function toggleSection(section) {
  if (loading.value || quizStartInProgress.value) return
  const submodules = section?.submodules || []
  if (!submodules.length) {
    return
  }

  const selectedSet = new Set(selectedTags.value)
  const allSelected = submodules.every((item) => selectedSet.has(item))

  if (allSelected) {
    selectedTags.value = selectedTags.value.filter((item) => !submodules.includes(item))
    return
  }

  submodules.forEach((item) => selectedSet.add(item))
  selectedTags.value = Array.from(selectedSet)
}

function getCount(tag) {
  return getTagCount(subject.value, tag)
}

async function loadCultureProgress() {
  if (!isCultureSubject.value || mode.value !== 'tags' || isAiTrainingMode.value || mockExamMode.value) {
    return
  }

  syncAccessToken()
  cultureProgressLoading.value = true
  try {
    const data = await fetchQuestionProgress({
      exam_code: examCode.value,
      subject: CULTURE_SUBJECT
    })
    cultureProgress.value = {
      ...DEFAULT_CULTURE_PROGRESS,
      ...data
    }
  } catch (error) {
    cultureProgress.value = { ...DEFAULT_CULTURE_PROGRESS }
  } finally {
    cultureProgressLoading.value = false
  }
}

async function fetchAdaptiveHistory() {
  if (!hasAccessToken.value) return []
  try {
    const data = await fetchAnswerHistory({
      exam_code: examCode.value,
      subject: subject.value,
      limit: ADAPTIVE_HISTORY_LIMIT,
      offset: 0
    })
    return data.items || []
  } catch (error) {
    return []
  }
}

async function startCultureReview() {
  syncAccessToken()
  if (!hasAccessToken.value) {
    uni.navigateTo({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/practice/index')}` })
    return
  }

  if (cultureReviewDueCount.value <= 0) {
    uni.showToast({ title: '当前没有到期复习题', icon: 'none' })
    return
  }

  cultureReviewLoading.value = true
  loadError.value = ''
  shortageTip.value = ''
  uni.showLoading({ title: '正在整理复习题...' })

  try {
    const data = await fetchReviewDueQuestions({
      exam_code: examCode.value,
      subject: CULTURE_SUBJECT,
      limit: plannedQuestionLimit.value
    })
    const items = (data.items || []).map((item) =>
      buildApiQuestion(item, {
        module: item.module,
        submodule: item.submodule
      })
    )

    if (!items.length) {
      cultureProgress.value = {
        ...cultureProgress.value,
        review_due_count: 0
      }
      uni.showToast({ title: '当前没有到期复习题', icon: 'none' })
      return
    }

    resetQuizState()
    practiceMode.value = 'special'
    selectedTags.value = []
    reviewMode.value = false
    reviewResults.value = []
    summaryMode.value = false
    aiSummaryMode.value = false
    comprehensiveAnswers.value = {}
    questionPool.value = items
    mode.value = 'quiz'
    applyQuestionAt(0)
  } catch (error) {
    const detail = error?.detail || '复习题加载失败'
    loadError.value = detail
    uni.showToast({ title: detail, icon: 'none' })
  } finally {
    cultureReviewLoading.value = false
    uni.hideLoading()
  }
}

async function fetchRealQuestionCandidates(moduleInfos) {
  if (practiceMode.value === 'comprehensive') {
    const query = buildQuery({
      exam_code: examCode.value,
      subject: subject.value,
      limit: String(Math.min(100, Math.max(plannedQuestionLimit.value * 8, 30))),
      randomize: 'true'
    })

    const data = await request({
      url: `/questions?${query}`
    })

    const items = (data.items || []).map((item) =>
      buildApiQuestion(item, {
        module: item.module,
        submodule: item.submodule
      })
    )

    return items.length ? [items] : []
  }

  const perTagLimit =
    Math.min(50, Math.max(20, plannedQuestionLimit.value, Math.ceil(plannedQuestionLimit.value / moduleInfos.length) * 4))

  const responses = await Promise.all(
    moduleInfos.map((meta) => {
      const query = buildQuery({
        exam_code: examCode.value,
        subject: subject.value,
        module: meta.module,
        submodule: meta.submodule,
        limit: String(perTagLimit)
      })

      return request({
        url: `/questions/by-module?${query}`
      }).then((data) => ({
        ok: true,
        meta,
        items: data.items || []
      })).catch(() => ({
        ok: false,
        meta,
        items: []
      }))
    })
  )

  return responses
    .filter((response) => response.ok)
    .map((response) => response.items.map((item) => buildApiQuestion(item, response.meta)))
    .filter((items) => items.length)
}

async function fetchSubjectSupplement(existingKeys) {
  const query = buildQuery({
    exam_code: examCode.value,
    subject: subject.value,
    limit: String(Math.min(50, plannedQuestionLimit.value * 3)),
    randomize: 'true'
  })

  const data = await request({
    url: `/questions?${query}`
  })

  return (data.items || [])
    .filter((item) => !existingKeys.has(getQuestionIdentityKey(item)))
    .map((item) =>
      buildApiQuestion(item, {
        module: item.module,
        submodule: item.submodule
      })
    )
}

async function loadLegacyQuestionPool(
  moduleInfos,
  { updateShortageTip = true } = {}
) {
  const cacheKey = getCacheKey(moduleInfos)
  let candidateGroups = questionCache.get(cacheKey)
  let nextPool = []
  const adaptiveHistory = await fetchAdaptiveHistory()

  if (!candidateGroups) {
    if (hasAccessToken.value && moduleInfos.length) {
      candidateGroups = await fetchRealQuestionCandidates(moduleInfos)
    }

    if (candidateGroups?.length) {
      questionCache.set(cacheKey, candidateGroups)
    }
  }

  if (candidateGroups?.length) {
    nextPool = buildAdaptiveQuestionPool(candidateGroups, adaptiveHistory)
  }

  if (nextPool.length < plannedQuestionLimit.value) {
    const existingKeys = new Set(nextPool.map((item) => getQuestionIdentityKey(item)))
    const supplement = await fetchSubjectSupplement(existingKeys)
    if (supplement.length) {
      nextPool = buildAdaptiveQuestionPool([nextPool, supplement], adaptiveHistory)
      if (updateShortageTip) {
        shortageTip.value = '当前题库较少，已为你随机补充同科目题目。'
      }
    }
  }

  return nextPool
}

async function fetchMockExamSectionPool(section, usedKeys) {
  const query = buildQuery({
    exam_code: examCode.value,
    subject: section.subject,
    limit: '100',
    randomize: 'true'
  })

  const data = await request({
    url: `/questions?${query}`
  })

  const items = (data.items || [])
    .filter((item) => !usedKeys.has(getQuestionIdentityKey(item)))
    .filter(section.include)

  return selectStandardMockExamItems(items, section.count)
    .map((item) => {
      usedKeys.add(getQuestionIdentityKey(item))
      return buildApiQuestion(item, {
        module: item.module,
        submodule: item.submodule,
        mockSection: section.label,
        mockSectionKey: section.key,
        pointValue: section.pointValue
      })
    })
}

function applyQuestionAt(index) {
  clearTimer()
  currentQuestionIndex.value = index
  const nextQuestion = questionPool.value[index]
  if (!nextQuestion) {
    return
  }
  // Any explicit question change supersedes a queued intent for the old item.
  adaptiveQueuedNavigation.value = null
  const nextQuestionKey = nextQuestion.questionId || nextQuestion.id
  const savedInstantResult = practiceMode.value === 'comprehensive' ? null : instantQuestionResults.value[nextQuestionKey]
  questionMeta.value = {
    questionId: nextQuestionKey,
    module: nextQuestion.module || '',
    submodule: nextQuestion.submodule || ''
  }
  submitting.value = false
  explanationExpanded.value = false

  if (savedInstantResult) {
    selectedOption.value = savedInstantResult.selectedAnswer
    correctAnswer.value = savedInstantResult.correctAnswer
    answerExplanation.value = savedInstantResult.explanation
    resultTag.value = savedInstantResult.resultTag
    abilityAccuracy.value = savedInstantResult.abilityAccuracy ?? null
    submitted.value = true
    clearTimer()
  } else {
    correctAnswer.value = ''
    answerExplanation.value = ''
    resultTag.value = ''
    selectedOption.value = practiceMode.value === 'comprehensive' ? comprehensiveAnswers.value[nextQuestionKey] || '' : ''
    submitted.value = false
    abilityAccuracy.value = null
    startTimer(nextQuestionKey)
  }

  void recordAdaptiveEvent(nextQuestion, 'presented')
  if (savedInstantResult && nextQuestion.adaptiveSessionItemId) {
    // Returning from an earlier item to the answered frontier should restart
    // one-item look-ahead immediately. A settlement that completed while the
    // learner viewed the previous item must not turn the following tap into a
    // cold network request.
    void prefetchNextAdaptiveQuestion(
      nextQuestion,
      captureAdaptiveQuestionContext(nextQuestion)
    )
  }
  loadCurrentFavoriteStatus()
  scrollToQuestionTop()
}

async function loadAiTrainingSession(sessionId) {
  syncAccessToken()
  if (!hasAccessToken.value) {
    uni.navigateTo({ url: `/pages/login/index?redirect=${encodeURIComponent(`/pages/practice/index?ai_session_id=${sessionId}`)}` })
    return
  }

  loading.value = true
  loadError.value = ''
  resetQuizState()
  reviewMode.value = false
  reviewResults.value = []
  summaryMode.value = false
  aiSummaryMode.value = false
  aiSummary.value = null
  aiReviewResults.value = []
  comprehensiveAnswers.value = {}
  questionPool.value = []
  mode.value = 'quiz'
  uni.showLoading({ title: '正在整理 AI 训练...' })

  try {
    const data = await fetchAiTrainingSession(sessionId)
    const items = data?.items || []
    if (!items.length) {
      throw new Error('AI 训练题目为空，请重新生成')
    }

    examCode.value = data.exam_code || examCode.value
    subject.value = data.target?.subject || items[0]?.subject || subject.value
    selectedQuestionSize.value = normalizeQuestionSize(items.length)
    practiceMode.value = 'special'
    questionPool.value = items.map((item) =>
      buildApiQuestion(item, {
        module: item.module,
        submodule: item.submodule
      })
    )
    mode.value = 'quiz'
    applyQuestionAt(0)
  } catch (error) {
    const detail = error?.detail || error?.message || 'AI 训练加载失败'
    loadError.value = detail
    uni.showModal({
      title: '加载失败',
      content: detail,
      showCancel: false,
      confirmText: '知道了',
      success() {
        uni.navigateBack({
          delta: 1,
          fail() {
            uni.redirectTo({ url: '/pages/home/index' })
          }
        })
      }
    })
  } finally {
    loading.value = false
    uni.hideLoading()
  }
}

async function startMockExam() {
  syncAccessToken()
  loadError.value = ''
  shortageTip.value = ''
  showAnswerSheet.value = false

  if (!hasAccessToken.value) {
    uni.showModal({
      title: '请先登录',
      content: '登录后才能使用真实题库生成模拟测试，并保存分数与复盘记录。',
      confirmText: '去登录',
      cancelText: '先不登录',
      success(result) {
        if (result.confirm) {
          const redirect = `/pages/practice/index?mock_exam=1&exam_code=${encodeURIComponent(examCode.value)}`
          uni.navigateTo({ url: `/pages/login/index?redirect=${encodeURIComponent(redirect)}` })
        } else {
          uni.navigateBack({
            delta: 1,
            fail() {
              uni.redirectTo({ url: '/pages/home/index' })
            }
          })
        }
      }
    })
    return
  }

  loading.value = true
  resetQuizState()
  reviewMode.value = false
  reviewResults.value = []
  summaryMode.value = false
  aiSummaryMode.value = false
  comprehensiveAnswers.value = {}
  questionPool.value = []
  mode.value = 'quiz'
  uni.showLoading({ title: '正在组卷...' })

  try {
    const usedKeys = new Set()
    const config = getMockExamConfig(examCode.value)
    const sectionPools = []
    const shortageSections = []

    for (const section of config) {
      const pool = await fetchMockExamSectionPool(section, usedKeys)
      if (pool.length < section.count) {
        shortageSections.push(`${section.label} ${pool.length}/${section.count}`)
      }
      sectionPools.push(pool)
    }

    const nextPool = sectionPools.flat()
    if (!nextPool.length) {
      throw new Error('当前题库暂无可用于模拟测试的题目，请稍后再试')
    }

    if (shortageSections.length) {
      shortageTip.value = `题库数量暂不足：${shortageSections.join('，')}。本次先按可用题目组卷。`
    }

    questionPool.value = nextPool
    selectedQuestionSize.value = nextPool.length
    subject.value = getMockExamThirdSubject(examCode.value)
    timerSeconds.value = 0
    applyQuestionAt(0)

    if (shortageTip.value) {
      uni.showToast({ title: '题库暂不足，已按可用题目组卷', icon: 'none' })
    }
  } catch (error) {
    const detail = error?.detail || error?.message || '模拟测试组卷失败'
    loadError.value = detail
    mode.value = 'tags'
    uni.showModal({
      title: '组卷失败',
      content: detail,
      showCancel: false,
      confirmText: '知道了',
      success() {
        uni.navigateBack({
          delta: 1,
          fail() {
            uni.redirectTo({ url: '/pages/home/index' })
          }
        })
      }
    })
  } finally {
    loading.value = false
    uni.hideLoading()
  }
}

async function startFixedMockExam(paperId) {
  syncAccessToken()
  loadError.value = ''
  shortageTip.value = ''
  showAnswerSheet.value = false

  if (!hasAccessToken.value) {
    uni.showModal({
      title: '请先登录',
      content: '登录后才能作答固定模拟卷，并保存分数与复盘记录。',
      confirmText: '去登录',
      cancelText: '先不登录',
      success(result) {
        if (result.confirm) {
          const redirect = `/pages/practice/index?mock_paper_id=${encodeURIComponent(paperId)}&exam_code=${encodeURIComponent(examCode.value)}`
          uni.navigateTo({ url: `/pages/login/index?redirect=${encodeURIComponent(redirect)}` })
        } else {
          returnToMockExamList()
        }
      }
    })
    return
  }

  loading.value = true
  resetQuizState()
  reviewMode.value = false
  reviewResults.value = []
  summaryMode.value = false
  aiSummaryMode.value = false
  comprehensiveAnswers.value = {}
  questionPool.value = []
  mode.value = 'quiz'
  uni.showLoading({ title: '正在打开试卷...' })

  try {
    const response = await fetchMockExamPaperDetail(paperId)
    const paper = response?.paper || {}
    const nextExamCode = paper.exam_code || examCode.value
    const items = (response?.questions || [])
      .slice()
      .sort((left, right) => Number(left.position || 0) - Number(right.position || 0))
      .map((item) => buildApiQuestion(item, {
        module: item.module,
        submodule: item.submodule,
        mockSection: item.mock_section,
        mockSectionKey: item.mock_section_key,
        pointValue: item.point_value
      }))

    if (items.length !== MOCK_EXAM_TOTAL_COUNT) {
      throw new Error(`该模拟卷题目数量异常，当前 ${items.length}/${MOCK_EXAM_TOTAL_COUNT} 题`)
    }

    examCode.value = nextExamCode
    subject.value = getMockExamThirdSubject(nextExamCode)
    mockExamPaperId.value = String(paper.id || paperId)
    mockExamPaperTitle.value = String(paper.title || '模拟测试')
    selectedQuestionSize.value = items.length
    questionPool.value = items
    timerSeconds.value = 0
    uni.setStorageSync('examCode', nextExamCode)
    uni.setStorageSync('subject', subject.value)
    applyQuestionAt(0)
  } catch (error) {
    const detail = error?.detail || error?.message || '固定模拟卷加载失败'
    loadError.value = typeof detail === 'string' ? detail : '固定模拟卷加载失败'
    mode.value = 'tags'
    uni.showModal({
      title: '试卷加载失败',
      content: loadError.value,
      showCancel: false,
      confirmText: '返回模拟卷',
      success() {
        returnToMockExamList()
      }
    })
  } finally {
    loading.value = false
    uni.hideLoading()
  }
}

function buildAdaptiveComprehensiveQuestionPool(response, startContext) {
  const sessionId = String(response?.session?.id || '')
  const expectedCount = Number(response?.session?.question_count || 0)
  const items = normalizeAdaptiveComprehensiveItems(response?.items, {
    sessionId,
    expectedCount
  })

  return items.map((item, index) => {
    const question = buildAdaptiveQuestion(item)
    if (!question) {
      const error = new Error(`综合刷题第 ${index + 1} 道题数据不完整`)
      error.statusCode = 503
      error.detail = {
        code: 'ADAPTIVE_COMPREHENSIVE_SHEET_INVALID',
        message: error.message
      }
      throw error
    }
    const quality = validateQuestion(normalizeQuestion(question, {
      subject: startContext.subject,
      examCode: startContext.examCode
    }))
    if (!quality.valid) {
      const error = new Error(`综合刷题第 ${index + 1} 道题数据异常`)
      error.statusCode = 503
      error.detail = {
        code: 'ADAPTIVE_COMPREHENSIVE_SHEET_INVALID',
        message: error.message
      }
      throw error
    }
    return question
  })
}

async function createAdaptivePractice(
  moduleInfos,
  {
    flowGeneration,
    clientSessionId,
    startContext
  }
) {
  const isComprehensive = startContext.practiceMode === 'comprehensive'
  const payload = {
    exam_code: startContext.examCode,
    subject: startContext.subject,
    practice_mode: startContext.practiceMode,
    scopes: isComprehensive
      ? []
      : moduleInfos.map((item) => ({
          module: item.module,
          submodule: item.submodule
        })),
    question_count: startContext.questionCount,
    preference: startContext.preference,
    accepted_challenge: !isComprehensive && startContext.preference === 'challenge',
    client_session_id: clientSessionId
  }
  let response
  try {
    response = await createAdaptivePracticeSession(payload)
  } catch (error) {
    if (
      !isAdaptiveCreateRetryableError(error) ||
      flowGeneration !== adaptiveFlowGeneration ||
      !isPracticeStartContextCurrent(startContext)
    ) {
      throw error
    }
    // Reuse the exact client id so a timed-out first POST resolves to the same
    // server session instead of creating a second active run.
    response = await createAdaptivePracticeSession({
      ...payload,
      resume_existing_session: true
    })
  }
  if (
    flowGeneration !== adaptiveFlowGeneration ||
    !isPracticeStartContextCurrent(startContext)
  ) {
    if (response?.session?.id) {
      void completeAdaptivePracticeSession(response.session.id, 'abandoned').catch(() => {})
    }
    return false
  }
  applyAdaptiveEnvelope(response, { captureInitialPhase: true })
  let nextPool
  try {
    if (isComprehensive) {
      nextPool = buildAdaptiveComprehensiveQuestionPool(response, startContext)
    } else {
      const firstQuestion = buildAdaptiveQuestion(response?.next_item)
      if (!firstQuestion) {
        throw new Error('当前所选考点暂无可用题目，请调整范围后再试')
      }
      nextPool = [firstQuestion]
    }
  } catch (error) {
    if (response?.session?.id) {
      void completeAdaptivePracticeSession(response.session.id, 'abandoned').catch(() => {})
      if (String(adaptiveSession.value?.id || '') === String(response.session.id)) {
        adaptiveSession.value = {
          ...adaptiveSession.value,
          status: 'abandoned'
        }
      }
    }
    throw error
  }

  adaptiveFallbackMode.value = false
  adaptiveNextExhausted.value = isComprehensive
  adaptiveNextFinishAvailable.value = false
  questionPool.value = nextPool
  mode.value = 'quiz'
  applyQuestionAt(0)
  return true
}

async function startQuiz() {
  if (loading.value || quizStartInProgress.value) return
  syncAccessToken()
  loadError.value = ''
  shortageTip.value = ''
  const startContext = capturePracticeStartContext()

  if (!hasAccessToken.value) {
    uni.showModal({
      title: '请先登录',
      content: '登录后才能使用真实题库、保存作答记录、同步错题本和能力报告。',
      confirmText: '去登录',
      cancelText: '先不登录',
      success(result) {
        if (result.confirm) {
          uni.navigateTo({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/practice/index')}` })
        }
      }
    })
    return
  }

  if (startContext.practiceMode === 'special' && !selectedTags.value.length) {
    uni.showToast({ title: '请先选择至少一个考点', icon: 'none' })
    return
  }

  const startRequestToken = ++quizStartRequestSequence
  activeQuizStartRequestToken = startRequestToken
  quizStartInProgress.value = true
  quizStartBackgrounded.value = false
  loading.value = true
  let startContinuesInBackground = false
  try {
    // The previous run is already superseded by this start intent. Close it in
    // the background so its 12s event + 15s completion budget cannot delay the
    // first question of the new run.
    const previousSessionClose = endAdaptiveSession('abandoned').catch(() => null)
    void previousSessionClose
    if (activeQuizStartRequestToken !== startRequestToken) return

    resetAdaptivePracticeState()
    resetQuizState()
    const flowGeneration = adaptiveFlowGeneration
    const clientSessionId = ensureSubmissionSession()
    mode.value = 'tags'
    reviewMode.value = false
    reviewResults.value = []
    summaryMode.value = false
    aiSummaryMode.value = false
    aiSummary.value = null
    aiReviewResults.value = []
    comprehensiveAnswers.value = {}
    uni.showLoading({ title: '正在整理题目...' })

    const moduleInfos = getTargetModuleInfos(startContext.practiceMode)
    const applyLegacyStartPool = (nextPool) => {
      if (!nextPool.length) {
        throw new Error('当前题库暂无可用题目，请换一个科目或稍后再试')
      }

      if (
        activeQuizStartRequestToken !== startRequestToken ||
        flowGeneration !== adaptiveFlowGeneration ||
        !isPracticeStartContextCurrent(startContext)
      ) {
        return false
      }
      questionPool.value = nextPool
      mode.value = 'quiz'
      applyQuestionAt(0)

      if (shortageTip.value) {
        uni.showToast({ title: shortageTip.value, icon: 'none' })
      } else if (questionPool.value.length < plannedQuestionLimit.value) {
        shortageTip.value = '当前题库较少，本轮先按可用题目练习。'
        uni.showToast({ title: shortageTip.value, icon: 'none' })
      }
      return true
    }

    try {
      const created = await createAdaptivePractice(moduleInfos, {
        flowGeneration,
        clientSessionId,
        startContext
      })
      if (!created) return
      return
    } catch (error) {
      if (!isAdaptiveCreateFallbackError(error)) {
        throw error
      }
      adaptiveFallbackMode.value = true
      adaptiveNextExhausted.value = true
      shortageTip.value = '智能出题服务正在更新，本轮已切换为普通组题。'
    }

    const legacyPoolRequest = loadLegacyQuestionPool(moduleInfos, {
      updateShortageTip: false
    })
    const legacyPoolOutcome = await Promise.race([
      legacyPoolRequest,
      new Promise((resolve) => {
        setTimeout(
          () => resolve(ADAPTIVE_LEGACY_START_STILL_RUNNING),
          ADAPTIVE_FOREGROUND_PREFETCH_WAIT_MS
        )
      })
    ])
    if (legacyPoolOutcome === ADAPTIVE_LEGACY_START_STILL_RUNNING) {
      startContinuesInBackground = true
      quizStartBackgrounded.value = true
      loading.value = false
      uni.hideLoading()
      uni.showToast({ title: '题目正在后台准备，完成后自动开始', icon: 'none' })
      void legacyPoolRequest
        .then((nextPool) => {
          applyLegacyStartPool(nextPool)
        })
        .catch((error) => {
          if (activeQuizStartRequestToken !== startRequestToken) return
          const failedSessionClose = endAdaptiveSession('abandoned').catch(() => null)
          void failedSessionClose
          const detail = adaptiveErrorMessage(error, '加载题目失败')
          loadError.value = detail
          uni.showToast({ title: detail, icon: 'none' })
        })
        .finally(() => {
          if (activeQuizStartRequestToken === startRequestToken) {
            activeQuizStartRequestToken = 0
            quizStartInProgress.value = false
            quizStartBackgrounded.value = false
            loading.value = false
            uni.hideLoading()
          }
        })
      return
    }
    applyLegacyStartPool(legacyPoolOutcome)
  } catch (error) {
    if (activeQuizStartRequestToken !== startRequestToken) return
    const failedSessionClose = endAdaptiveSession('abandoned').catch(() => null)
    void failedSessionClose
    const detail = adaptiveErrorMessage(error, '加载题目失败')
    loadError.value = detail
    uni.showToast({ title: detail, icon: 'none' })
  } finally {
    if (
      activeQuizStartRequestToken === startRequestToken &&
      !startContinuesInBackground
    ) {
      activeQuizStartRequestToken = 0
      quizStartInProgress.value = false
      quizStartBackgrounded.value = false
      loading.value = false
      uni.hideLoading()
    }
  }
}

function selectOption(key) {
  if (
    submitted.value ||
    practiceMutationLocked.value ||
    reviewMode.value ||
    currentQuestionHasBlockingIssue.value
  ) {
    return
  }
  if (
    adaptiveComprehensivePracticeActive.value &&
    adaptiveComprehensiveSubmissionSnapshot?.sessionId === String(adaptiveSession.value?.id || '')
  ) {
    uni.showToast({ title: '整卷已进入提交流程，请重试交卷', icon: 'none' })
    return
  }
  selectedOption.value = key
  if (practiceMode.value === 'comprehensive') {
    comprehensiveAnswers.value = {
      ...comprehensiveAnswers.value,
      [currentQuestionKey.value]: key
    }
  }
}

function isQuestionAnswered(question) {
  const key = question?.questionId || question?.id
  return Boolean(
    key &&
    (comprehensiveAnswers.value[key] || comprehensiveSkippedQuestions.value[key])
  )
}

function openAnswerSheet() {
  if (practiceMutationLocked.value) return
  showAnswerSheet.value = true
}

function closeAnswerSheet() {
  showAnswerSheet.value = false
}

function jumpToQuestion(index) {
  if (practiceMutationLocked.value) {
    return
  }
  showAnswerSheet.value = false
  if (reviewMode.value) {
    applyReviewAt(index)
  } else {
    applyQuestionAt(index)
  }
}

async function handlePrimaryAction() {
  if (practiceMutationLocked.value) {
    return
  }
  if (currentQuestionHasBlockingIssue.value) {
    handleInvalidQuestionNext()
    return
  }
  if (practiceMode.value === 'comprehensive') {
    await handleComprehensiveAction()
    return
  }
  await submitAnswer()
}

async function handleInvalidQuestionNext() {
  if (practiceMutationLocked.value) return
  const question = currentQuestion.value
  const isComprehensive = practiceMode.value === 'comprehensive' && !mockExamMode.value
  const id = normalizedCurrentQuestion.value.id || normalizedCurrentQuestion.value.questionId || '(no-id)'
  // eslint-disable-next-line no-console
  console.warn('[question-quality-skip]', id, currentQuestionQuality.value.reasons)
  if (isComprehensive) {
    const nextAnswers = { ...comprehensiveAnswers.value }
    delete nextAnswers[currentQuestionKey.value]
    comprehensiveAnswers.value = nextAnswers
    comprehensiveSkippedQuestions.value = {
      ...comprehensiveSkippedQuestions.value,
      [currentQuestionKey.value]: true
    }
    if (hasNextQuestion.value) {
      applyQuestionAt(currentQuestionIndex.value + 1)
    } else {
      await submitComprehensiveAnswers()
    }
    return
  }
  const context = captureAdaptiveQuestionContext(question)
  const requiresAdaptiveSkip = Boolean(context.sessionId && context.itemId && !adaptiveFallbackMode.value)
  const navigationAction = canAdvanceQuestion.value ? 'next' : 'finish'
  const eventRequestToken = ++adaptiveEventRequestSequence
  activeAdaptiveEventRequestToken = eventRequestToken
  adaptiveEventSyncing.value = true
  const skipRequest = (async () => {
    try {
      const recorded = await recordAdaptiveEvent(question, 'skipped')
      if (
        activeAdaptiveEventRequestToken !== eventRequestToken ||
        !isAdaptiveQuestionContextCurrent(context)
      ) {
        return false
      }
      if (requiresAdaptiveSkip && !recorded) {
        uni.showToast({ title: '跳过状态保存失败，请重试', icon: 'none' })
        return false
      }
      return true
    } finally {
      if (activeAdaptiveEventRequestToken === eventRequestToken) {
        activeAdaptiveEventRequestToken = 0
        adaptiveEventSyncing.value = false
      }
    }
  })()

  const outcome = await Promise.race([
    skipRequest,
    new Promise((resolve) => {
      setTimeout(
        () => resolve(ADAPTIVE_PREFETCH_STILL_RUNNING),
        ADAPTIVE_FOREGROUND_PREFETCH_WAIT_MS
      )
    })
  ])
  if (outcome === ADAPTIVE_PREFETCH_STILL_RUNNING) {
    // Keep the server-side item barrier intact, but stop presenting the event
    // request as a blocking foreground operation.
    adaptiveEventSyncing.value = false
    setAdaptiveNavigationIntent(navigationAction, context, { ready: false })
    continueAdaptiveProgressInBackground(skipRequest, context)
    uni.showToast({ title: '跳过状态后台保存，完成后自动继续', icon: 'none' })
    return
  }
  if (outcome !== true) return
  if (navigationAction === 'next') {
    await goNextQuestion()
    return
  }
  await finishQuiz()
}

function toggleExplanation() {
  if (questionNavigationLocked.value) return
  explanationExpanded.value = true
  void recordAdaptiveEvent(currentQuestion.value, 'answer_viewed')
}

function closeExplanation() {
  explanationExpanded.value = false
}

async function markCurrentUnfamiliarAndNext() {
  syncAccessToken()

  if (!hasAccessToken.value) {
    uni.navigateTo({ url: `/pages/login/index?redirect=${encodeURIComponent('/pages/practice/index')}` })
    return
  }

  if (
    !canMarkCurrentUnfamiliar.value ||
    practiceMutationLocked.value
  ) {
    return
  }

  const question = currentQuestion.value
  const questionKey = currentQuestionKey.value
  const context = captureAdaptiveQuestionContext(question)
  const adaptiveItemId = String(question.adaptiveSessionItemId || '')
  const wasAlreadySubmitted = submitted.value
  const attachAdaptiveItem = Boolean(adaptiveItemId && !wasAlreadySubmitted)
  const navigationAction = canAdvanceQuestion.value ? 'next' : 'finish'
  const unfamiliarRequestToken = ++unfamiliarRequestSequence
  activeUnfamiliarRequestToken = unfamiliarRequestToken
  markingUnfamiliar.value = true
  clearTimer()
  const usedTime = getSubmissionUsedTime(questionKey, 'unfamiliar')

  const unfamiliarRequest = (async () => {
    try {
      const clientSubmissionId = getClientSubmissionId(questionKey, 'unfamiliar')
      let result = await markQuestionUnfamiliar({
        question_id: question.questionId || question.id,
        client_submission_id: clientSubmissionId,
        used_time: usedTime,
        exam_code: examCode.value,
        ...(attachAdaptiveItem ? { practice_session_item_id: adaptiveItemId } : {})
      })

      if (attachAdaptiveItem) {
        const retryPayload = {
          question_id: question.questionId || question.id,
          selected_answer: result.selected_answer,
          client_submission_id: clientSubmissionId,
          used_time: usedTime,
          exam_code: examCode.value,
          practice_session_item_id: adaptiveItemId
        }
        result = await settleAdaptiveSubmission(
          result,
          retryPayload,
          adaptiveItemId,
          { retryOnce: true, context }
        )
      }

      if (
        activeUnfamiliarRequestToken !== unfamiliarRequestToken ||
        !isAdaptiveQuestionContextCurrent(context)
      ) {
        return false
      }
      if (attachAdaptiveItem) {
        applyAdaptiveSubmissionResult(result)
      }

      unfamiliarQuestionMap.value = {
        ...unfamiliarQuestionMap.value,
        [questionKey]: true
      }

      resultTag.value = '已标记不熟悉，已加入错题本和复习队列。'
      abilityAccuracy.value = result.ability_accuracy
      clearTimer()

      if (!wasAlreadySubmitted) {
        selectedOption.value = selectedOption.value || result.selected_answer
        correctAnswer.value = result.correct_answer
        answerExplanation.value = result.explanation
        submitted.value = true
        saveInstantQuestionResult({
          question,
          selectedAnswer: selectedOption.value || result.selected_answer,
          correctAnswer: result.correct_answer,
          explanation: result.explanation,
          isCorrect: false,
          syncFailed: false
        })
      }

      uni.showToast({ title: '已加入复习', icon: 'none' })
      return true
    } catch (error) {
      if (
        activeUnfamiliarRequestToken === unfamiliarRequestToken &&
        isAdaptiveQuestionContextCurrent(context)
      ) {
        uni.showToast({ title: error?.detail || '标记不熟悉失败', icon: 'none' })
      }
      return false
    } finally {
      if (activeUnfamiliarRequestToken === unfamiliarRequestToken) {
        activeUnfamiliarRequestToken = 0
        markingUnfamiliar.value = false
      }
    }
  })()

  const outcome = await Promise.race([
    unfamiliarRequest,
    new Promise((resolve) => {
      setTimeout(
        () => resolve(ADAPTIVE_PREFETCH_STILL_RUNNING),
        ADAPTIVE_FOREGROUND_PREFETCH_WAIT_MS
      )
    })
  ])
  if (outcome === ADAPTIVE_PREFETCH_STILL_RUNNING) {
    markingUnfamiliar.value = false
    setAdaptiveNavigationIntent(navigationAction, context, { ready: false })
    continueAdaptiveProgressInBackground(unfamiliarRequest, context)
    uni.showToast({ title: '正在后台加入复习，完成后自动继续', icon: 'none' })
    return
  }
  if (outcome !== true) return
  if (navigationAction === 'next') {
    await goNextQuestion()
    return
  }
  await finishQuiz()
}

async function handleComprehensiveAction() {
  if (!selectedOption.value || submitting.value) {
    return
  }

  comprehensiveAnswers.value = {
    ...comprehensiveAnswers.value,
    [currentQuestionKey.value]: selectedOption.value
  }

  if (hasNextQuestion.value) {
    applyQuestionAt(currentQuestionIndex.value + 1)
    return
  }

  await submitComprehensiveAnswers()
}

function getAdaptiveComprehensiveSubmissionTask() {
  const sessionId = String(adaptiveSession.value?.id || '')
  if (!adaptiveComprehensiveSubmissionSnapshot?.sessionId || adaptiveComprehensiveSubmissionSnapshot.sessionId !== sessionId) {
    const payload = buildAdaptiveComprehensiveSubmissionPayload({
      sessionId,
      clientSubmissionId: getClientSubmissionId(sessionId, 'comprehensive-batch'),
      questions: questionPool.value,
      answersByQuestion: { ...comprehensiveAnswers.value },
      getQuestionSubmissionId: (questionKey) => getClientSubmissionId(questionKey, 'comprehensive-answer'),
      getUsedTime: (questionKey) => getSubmissionUsedTime(questionKey)
    })
    adaptiveComprehensiveSubmissionSnapshot = {
      sessionId,
      payload
    }
  }

  // This synchronous durable write and read-back verification are a hard
  // barrier before the first submit request can lock the server manifest.
  const durableTask = adaptiveComprehensiveSubmissionQueue.persist({
    sessionId,
    payload: adaptiveComprehensiveSubmissionSnapshot.payload
  })
  adaptiveComprehensiveSubmissionSnapshot = durableTask
  return durableTask
}

function getAdaptiveComprehensiveSubmissionPayload() {
  return getAdaptiveComprehensiveSubmissionTask().payload
}

function removeAdaptiveComprehensiveSubmissionTask(task) {
  if (!task) return false
  try {
    return adaptiveComprehensiveSubmissionQueue.remove(task)
  } catch (error) {
    // A confirmed server completion remains idempotently replayable if local
    // storage is temporarily unavailable, so the durable task is left intact.
    return false
  }
}

function releaseTerminalAdaptiveComprehensiveSubmission(error, task) {
  if (!isAdaptiveComprehensiveTerminalSubmissionError(error)) return false
  removeAdaptiveComprehensiveSubmissionTask(task)
  if (
    adaptiveComprehensiveSubmissionSnapshot?.sessionId === task?.sessionId &&
    adaptiveComprehensiveSubmissionSnapshot?.payload?.client_submission_id === task?.payload?.client_submission_id
  ) {
    adaptiveComprehensiveSubmissionSnapshot = null
  }
  return true
}

async function submitAdaptiveComprehensiveAnswers(entries) {
  const task = getAdaptiveComprehensiveSubmissionTask()
  const sessionId = String(task?.sessionId || '')
  let response
  try {
    response = await adaptiveComprehensiveSubmissionQueue.submit(task)
  } catch (error) {
    if (!isAdaptiveSubmissionRetryableError(error)) {
      releaseTerminalAdaptiveComprehensiveSubmission(error, task)
      throw error
    }
    try {
      response = await adaptiveComprehensiveSubmissionQueue.submit(task)
    } catch (retryError) {
      releaseTerminalAdaptiveComprehensiveSubmission(retryError, task)
      throw retryError
    }
  }

  if (!isAdaptiveComprehensiveCompletedResponse(task, response)) {
    if (String(response?.session_id || '') !== sessionId) {
      const error = new Error('综合刷题交卷响应与当前会话不一致')
      error.code = 'ADAPTIVE_COMPREHENSIVE_CONTRACT_INVALID'
      throw error
    }
    const error = new Error('综合刷题交卷响应与当前会话不一致')
    error.message = '综合刷题交卷尚未完成，请重试'
    error.code = 'ADAPTIVE_COMPREHENSIVE_SUBMISSION_PENDING'
    error.retryable = true
    throw error
  }

  const results = mapAdaptiveComprehensiveResults(entries, response?.results)
  // The matching session and its full result contract are now confirmed.
  // Clear only this exact owner/session/client-id task; a failed local removal
  // safely leaves it for an idempotent replay on the next page show.
  removeAdaptiveComprehensiveSubmissionTask(task)
  applyAdaptiveEnvelope({
    session: {
      id: sessionId,
      status: response.status
    },
    state: response?.state
  })
  adaptiveNextExhausted.value = true
  adaptiveComprehensiveSubmissionSnapshot = null
  return results
}

async function submitComprehensiveAnswers() {
  if (submitting.value) {
    return
  }
  syncAccessToken()
  const entries = questionPool.value.map((question) => {
    const key = question.questionId || question.id
    return {
      question,
      selected: comprehensiveAnswers.value[key],
      skipped: Boolean(comprehensiveSkippedQuestions.value[key])
    }
  })
  const firstUnansweredIndex = entries.findIndex((item) => !item.selected && !item.skipped)
  if (firstUnansweredIndex >= 0) {
    const unansweredCount = entries.filter((item) => !item.selected && !item.skipped).length
    uni.showModal({
      title: '还有未作答题目',
      content: `还有 ${unansweredCount} 道题未完成，建议先补齐后再交卷。`,
      confirmText: '去补题',
      cancelText: '查看题卡',
      success(result) {
        if (result.confirm) {
          applyQuestionAt(firstUnansweredIndex)
        } else {
          openAnswerSheet()
        }
      }
    })
    return
  }

  submitting.value = true
  showGradingFeedback.value = true

  try {
    const useRealSubmit = entries.every(({ question }) => isRealSubmitQuestion(question))
    let results
    if (adaptiveComprehensivePracticeActive.value) {
      if (!useRealSubmit) {
        throw new Error('综合刷题固定题单包含无效题目，请重新开始')
      }
      results = await submitAdaptiveComprehensiveAnswers(entries)
    } else {
      const gradableEntries = entries.filter((item) => !item.skipped && item.selected)
      const gradableResults = gradableEntries.length
        ? (
            useRealSubmit
              ? await submitComprehensiveBatch(gradableEntries)
              : gradableEntries.map(buildLocalComprehensiveResult)
          )
        : []
      const resultMap = new Map(
        gradableResults.map((item) => [item.question.questionId || item.question.id, item])
      )
      results = entries.map((entry) => {
        const key = entry.question.questionId || entry.question.id
        return entry.skipped ? buildSkippedComprehensiveResult(entry.question) : resultMap.get(key)
      }).filter(Boolean)
    }

    reviewResults.value = results
    summaryMode.value = true
    reviewMode.value = false
    submitted.value = false
    clearTimer()
    await nextTick()
    scrollToQuestionTop()
  } catch (error) {
    if (
      adaptiveComprehensivePracticeActive.value &&
      isAdaptiveComprehensiveTerminalSubmissionError(error)
    ) {
      adaptiveComprehensiveSubmissionSnapshot = null
    }
    uni.showToast({ title: adaptiveErrorMessage(error, '提交整卷失败'), icon: 'none' })
  } finally {
    showGradingFeedback.value = false
    submitting.value = false
  }
}

function isRealSubmitQuestion(question) {
  return hasAccessToken.value && question.questionId && !String(question.questionId).startsWith('mock-')
}

function buildRemoteComprehensiveResult(question, selected, result) {
  return {
    question,
    selectedAnswer: selected,
    correctAnswer: result.correct_answer,
    explanation: result.explanation,
    isCorrect: result.is_correct,
    syncFailed: false
  }
}

function buildLocalComprehensiveResult({ question, selected }) {
  return {
    question,
    selectedAnswer: selected,
    correctAnswer: question.answer,
    explanation: question.explanation,
    isCorrect: selected === question.answer,
    syncFailed: false
  }
}

function buildPendingComprehensiveResult(question, selected, error) {
  const reason = error?.detail ? `（${error.detail}）` : ''
  return {
    question,
    selectedAnswer: selected,
    correctAnswer: '待同步',
    explanation: `本题做题记录已提交或正在同步，但移动端网络返回异常${reason}。请稍后到练习历史查看完整答案与解析。`,
    isCorrect: false,
    syncFailed: true
  }
}

function buildSkippedComprehensiveResult(question) {
  return {
    question,
    selectedAnswer: '',
    correctAnswer: '',
    explanation: '本题题面数据异常，本轮已跳过且不计入能力判断。',
    isCorrect: null,
    skipped: true,
    syncFailed: false
  }
}

function saveInstantQuestionResult(answerResult, metadata = {}) {
  if (!answerResult || practiceMode.value === 'comprehensive') {
    return
  }

  const key = answerResult.question?.questionId || answerResult.question?.id
  if (!key) {
    return
  }

  instantQuestionResults.value = {
    ...instantQuestionResults.value,
    [key]: {
      selectedAnswer: answerResult.selectedAnswer,
      correctAnswer: answerResult.correctAnswer,
      explanation: answerResult.explanation,
      isCorrect: answerResult.isCorrect,
      syncFailed: Boolean(answerResult.syncFailed),
      resultTag: metadata.resultTag ?? resultTag.value,
      abilityAccuracy: metadata.abilityAccuracy ?? abilityAccuracy.value
    }
  }
}

function applyResponsiveAnswerFeedback({
  question,
  questionKey,
  selectedAnswer,
  correctAnswer: nextCorrectAnswer,
  explanation,
  isCorrect,
  addedToWrongQuestions,
  persisted,
  nextAbilityAccuracy
}) {
  const syncPending = persisted !== true
  const nextResultTag = syncPending
    ? '答案已显示，作答记录正在同步。'
    : addedToWrongQuestions
      ? `已写入错题本：${subject.value} / ${question.module || ''} / ${question.submodule || ''}`
      : '本题答对，当前知识点继续保持。'
  const answerResult = {
    question,
    selectedAnswer,
    correctAnswer: nextCorrectAnswer,
    explanation: explanation || '解析正在同步中，请稍候。',
    isCorrect,
    syncFailed: syncPending
  }

  saveInstantQuestionResult(answerResult, {
    resultTag: nextResultTag,
    abilityAccuracy: nextAbilityAccuracy ?? null
  })
  if (isAiTrainingMode.value) {
    upsertAiReviewResult(answerResult)
  }

  if (currentQuestionKey.value !== questionKey || selectedOption.value !== selectedAnswer) {
    return
  }

  correctAnswer.value = nextCorrectAnswer
  if (explanation) {
    answerExplanation.value = explanation
  } else if (!answerExplanation.value) {
    answerExplanation.value = '解析正在同步中，请稍候。'
  }
  resultTag.value = nextResultTag
  abilityAccuracy.value = nextAbilityAccuracy ?? null
  submitted.value = true
  submitting.value = false
  clearTimer()
}

async function submitComprehensiveBatch(entries) {
  clearTimer()
  try {
    const resultItems = []
    for (let offset = 0; offset < entries.length; offset += 50) {
      const batchEntries = entries.slice(offset, offset + 50)
      const response = await request({
        url: '/answers/submit-batch',
        method: 'POST',
        timeout: 25000,
        data: {
          exam_code: examCode.value,
          answers: batchEntries.map(({ question, selected }) => ({
            question_id: question.questionId,
            selected_answer: selected,
            client_submission_id: getClientSubmissionId(question.questionId),
            used_time: getSubmissionUsedTime(question.questionId)
          }))
        }
      })
      resultItems.push(...(response.items || []))
    }

    const resultMap = new Map(resultItems.map((item) => [item.question_id, item]))
    return entries.map(({ question, selected }) => {
      const result = resultMap.get(question.questionId)
      return result ? buildRemoteComprehensiveResult(question, selected, result) : buildPendingComprehensiveResult(question, selected)
    })
  } catch (error) {
    const results = []
    for (const entry of entries) {
      results.push(await submitComprehensiveSingle(entry, error))
    }
    return results
  }
}

async function submitComprehensiveSingle({ question, selected }, batchError) {
  try {
    const result = await request({
      url: '/answers/submit',
      method: 'POST',
      timeout: 20000,
      data: {
        question_id: question.questionId,
        selected_answer: selected,
        client_submission_id: getClientSubmissionId(question.questionId),
        used_time: getSubmissionUsedTime(question.questionId),
        exam_code: examCode.value
      }
    })
    return buildRemoteComprehensiveResult(question, selected, result)
  } catch (error) {
    return buildPendingComprehensiveResult(question, selected, error || batchError)
  }
}

async function submitAnswer() {
  syncAccessToken()
  if (!selectedOption.value || practiceMutationLocked.value) {
    return
  }

  submitting.value = true
  explanationExpanded.value = false
  const submittedQuestionKey = currentQuestionKey.value
  const submittedQuestion = currentQuestion.value
  const submittedQuestionId = questionMeta.value.questionId
  let submittedOption = selectedOption.value
  const usesRemoteSubmission = hasAccessToken.value && isRealQuestion()
  const adaptiveItemId = String(submittedQuestion.adaptiveSessionItemId || '')
  const adaptiveContext = adaptiveItemId
    ? captureAdaptiveQuestionContext(submittedQuestion)
    : null
  const answerRequestToken = adaptiveItemId ? ++adaptiveAnswerRequestSequence : 0
  let remotePayload = null
  let adaptiveSubmissionTask = null
  let adaptiveSubmissionReady = false
  if (adaptiveItemId) {
    activeAdaptiveAnswerRequestToken = answerRequestToken
    adaptiveAnswerSyncing.value = true
  }
  clearTimer()
  const usedTime = getSubmissionUsedTime(submittedQuestionKey)
  let earlyGradeReceived = false
  try {
    let answerResult = null
    if (usesRemoteSubmission) {
      const payload = {
        question_id: submittedQuestionId,
        selected_answer: submittedOption,
        client_submission_id: getClientSubmissionId(submittedQuestionKey),
        used_time: usedTime,
        exam_code: examCode.value,
        ...(submittedQuestion.adaptiveSessionItemId
          ? { practice_session_item_id: submittedQuestion.adaptiveSessionItemId }
          : {})
      }
      remotePayload = payload
      const initialSubmissionPromise = submitAnswerWithReliableSync(payload, {
        queueScopeKey: adaptiveContext?.sessionId,
        onPayloadLocked(lockedPayload) {
          remotePayload = { ...lockedPayload }
          if (adaptiveContext) {
            adaptiveSubmissionTask = rememberAdaptiveAnswerSubmission(
              adaptiveContext,
              remotePayload,
              submittedQuestion,
              { initialInFlight: true }
            )
          }
          const lockedOption = String(lockedPayload?.selected_answer || '').trim().toUpperCase()
          if (!/^[ABCD]$/.test(lockedOption)) return
          submittedOption = lockedOption
          if (currentQuestionKey.value === submittedQuestionKey) {
            selectedOption.value = lockedOption
          }
        },
        onGraded(grade) {
          if (grade.questionId && grade.questionId !== submittedQuestionId) return
          if (
            adaptiveContext &&
            (
              activeAdaptiveAnswerRequestToken !== answerRequestToken ||
              !isAdaptiveQuestionContextCurrent(adaptiveContext)
            )
          ) return
          earlyGradeReceived = true
          applyResponsiveAnswerFeedback({
            question: submittedQuestion,
            questionKey: submittedQuestionKey,
            selectedAnswer: submittedOption,
            correctAnswer: grade.correctAnswer,
            explanation: '',
            isCorrect: grade.isCorrect,
            addedToWrongQuestions: grade.addedToWrongQuestions,
            persisted: false,
            nextAbilityAccuracy: null
          })
        }
      })
      if (adaptiveSubmissionTask) {
        adaptiveSubmissionTask.initialPromise = initialSubmissionPromise
      }
      let result = await initialSubmissionPromise
      if (adaptiveItemId) {
        result = await settleAdaptiveSubmission(
          result,
          remotePayload || payload,
          adaptiveItemId,
          { retryOnce: true, context: adaptiveContext }
        )
      }
      if (
        adaptiveContext &&
        (
          activeAdaptiveAnswerRequestToken !== answerRequestToken ||
          !isAdaptiveQuestionContextCurrent(adaptiveContext)
        )
      ) {
        return
      }
      applyAdaptiveSubmissionResult(result)
      if (
        adaptiveItemId &&
        remotePayload &&
        !adaptiveSubmissionBarrierSatisfied(result) &&
        !adaptiveMigrationPending(result) &&
        isAdaptiveQuestionContextCurrent(adaptiveContext)
      ) {
        adaptivePendingSubmissionPayloads.set(adaptiveItemId, { ...remotePayload })
      }

      answerResult = {
        question: submittedQuestion,
        selectedAnswer: submittedOption,
        correctAnswer: result.correct_answer,
        explanation: result.explanation,
        isCorrect: result.is_correct,
        syncFailed: result.persisted !== true
      }
      applyResponsiveAnswerFeedback({
        question: submittedQuestion,
        questionKey: submittedQuestionKey,
        selectedAnswer: submittedOption,
        correctAnswer: result.correct_answer,
        explanation: result.explanation,
        isCorrect: result.is_correct,
        addedToWrongQuestions: result.added_to_wrong_questions,
        persisted: result.persisted,
        nextAbilityAccuracy: result.ability_accuracy ?? null
      })
      if (adaptivePendingSubmissionPayloads.has(adaptiveItemId)) {
        resultTag.value = '本题已保存，个性化进度同步中，请重试。'
      }
      if (result.persisted !== true) {
        if (result.persistence_retryable !== false) {
          schedulePendingAnswerFlush(undefined, { queueScopeKey: adaptiveContext?.sessionId })
        } else {
          uni.showToast({ title: result.persistence_error || '作答记录保存失败，请稍后重试', icon: 'none' })
        }
      }
      if (
        adaptiveItemId &&
        adaptiveSubmissionBarrierSatisfied(result) &&
        !adaptivePendingSubmissionPayloads.has(adaptiveItemId) &&
        activeAdaptiveAnswerRequestToken === answerRequestToken &&
        isAdaptiveQuestionContextCurrent(adaptiveContext)
      ) {
        // Claim while the learner is reading the result. The question is only
        // presented after an explicit tap, so selection and exposure remain
        // distinct while the usual next-step network wait is hidden.
        void prefetchNextAdaptiveQuestion(submittedQuestion, adaptiveContext)
      }
      if (
        adaptiveItemId &&
        adaptiveSubmissionBarrierSatisfied(result) &&
        !adaptivePendingSubmissionPayloads.has(adaptiveItemId)
      ) {
        adaptiveSubmissionReady = true
      }
    } else {
      correctAnswer.value = submittedQuestion.answer
      answerExplanation.value = submittedQuestion.explanation
      resultTag.value = submittedQuestion.autoTag
      abilityAccuracy.value = null
      answerResult = buildLocalComprehensiveResult({ question: submittedQuestion, selected: submittedOption })
      saveInstantQuestionResult(answerResult)
      submitted.value = true
      submitting.value = false
    }

    if (isAiTrainingMode.value && answerResult && !usesRemoteSubmission) {
      upsertAiReviewResult(answerResult)
    }
  } catch (error) {
    const adaptiveRequestStillCurrent = !adaptiveContext || (
      activeAdaptiveAnswerRequestToken === answerRequestToken &&
      isAdaptiveQuestionContextCurrent(adaptiveContext)
    )
    if (earlyGradeReceived) {
      if (
        adaptiveItemId &&
        remotePayload &&
        adaptiveRequestStillCurrent
      ) {
        adaptivePendingSubmissionPayloads.set(adaptiveItemId, { ...remotePayload })
        resultTag.value = isAdaptiveSubmissionRetryableError(error)
          ? '本题已判分，作答记录和个性化进度正在后台同步。'
          : '本题已判分，但保存没有完成，请退出本轮后重试。'
      }
      schedulePendingAnswerFlush(undefined, { queueScopeKey: adaptiveContext?.sessionId })
      if (adaptiveRequestStillCurrent) {
        uni.showToast({
          title: adaptiveItemId
            ? (
                isAdaptiveSubmissionRetryableError(error)
                  ? '本题已判分，后台保存完成后会自动继续'
                  : '本题保存未完成，不会跳过这道题'
              )
            : '答案已显示，作答记录将在网络恢复后同步',
          icon: 'none'
        })
      }
      return
    }
    if (isAiTrainingMode.value && usesRemoteSubmission) {
      const pending = buildPendingComprehensiveResult(submittedQuestion, submittedOption, error)
      correctAnswer.value = pending.correctAnswer
      answerExplanation.value = pending.explanation
      resultTag.value = '本题已尝试提交，网络返回异常，稍后可在 AI 总结页重新读取结果。'
      abilityAccuracy.value = null
      upsertAiReviewResult(pending)
      saveInstantQuestionResult(pending)
      submitted.value = true
      clearTimer()
      return
    }
    schedulePendingAnswerFlush()
    if (adaptiveRequestStillCurrent) {
      uni.showToast({ title: error?.detail || '提交失败', icon: 'none' })
    }
  } finally {
    adaptiveSubmissionTask?.markInitialFlowDone()
    if (adaptiveItemId) {
      if (activeAdaptiveAnswerRequestToken === answerRequestToken) {
        activeAdaptiveAnswerRequestToken = 0
        submitting.value = false
        adaptiveAnswerSyncing.value = false
        if (adaptiveSubmissionReady && adaptiveContext) {
          drainAdaptiveNavigationIntent(adaptiveContext)
        } else if (
          adaptiveContextsMatch(adaptiveQueuedNavigation.value?.context, adaptiveContext) &&
          adaptiveFallbackMode.value &&
          !adaptiveLegacyFallbackLoading.value
        ) {
          drainAdaptiveNavigationIntent(adaptiveContext)
        } else if (
          adaptiveContextsMatch(adaptiveQueuedNavigation.value?.context, adaptiveContext) &&
          !adaptiveSubmissionTask &&
          !adaptivePendingSubmissionPayloads.has(adaptiveItemId) &&
          !adaptiveLegacyFallbackLoading.value
        ) {
          clearAdaptiveNavigationIntent(adaptiveContext)
        }
      }
    } else if (currentQuestionKey.value === submittedQuestionKey) {
      submitting.value = false
    }
  }
}

function applyReviewAt(index) {
  currentQuestionIndex.value = index
  const result = reviewResults.value[index]
  const question = result.question
  questionMeta.value = {
    questionId: question.questionId || question.id,
    module: question.module || '',
    submodule: question.submodule || ''
  }
  selectedOption.value = result.selectedAnswer
  correctAnswer.value = result.correctAnswer
  answerExplanation.value = result.explanation
  resultTag.value = result.skipped
    ? '本题已跳过，不计入能力判断。'
    : result.syncFailed
      ? '本题记录已提交，答案解析稍后可在练习历史中查看。'
      : result.isCorrect
        ? '本题答对。'
        : '本题答错，已纳入错题统计。'
  submitted.value = true
  explanationExpanded.value = true
  abilityAccuracy.value = null
  loadCurrentFavoriteStatus()
}

function openReviewQuestion(index) {
  summaryMode.value = false
  reviewMode.value = true
  applyReviewAt(index)
  nextTick(() => {
    scrollToQuestionTop()
  })
}

function upsertAiReviewResult(result) {
  const key = result.question.questionId || result.question.id
  const nextResults = [...aiReviewResults.value]
  const existingIndex = nextResults.findIndex((item) => (item.question.questionId || item.question.id) === key)
  if (existingIndex >= 0) {
    nextResults[existingIndex] = result
  } else {
    nextResults[currentQuestionIndex.value] = result
  }
  aiReviewResults.value = nextResults.filter(Boolean)
}

function openAiReviewQuestion(index) {
  if (!aiReviewResults.value.length) {
    return
  }
  aiSummaryMode.value = false
  summaryMode.value = false
  reviewMode.value = true
  reviewResults.value = aiReviewResults.value
  applyReviewAt(Math.max(0, Math.min(index, aiReviewResults.value.length - 1)))
  nextTick(() => {
    scrollToQuestionTop()
  })
}

function isRealQuestion() {
  return canFavoriteCurrent.value
}

async function loadCurrentFavoriteStatus() {
  syncAccessToken()
  const questionId = questionMeta.value.questionId
  favoriteQuestionId.value = questionId
  favoriteLoading.value = false
  currentFavorited.value = favoriteStatusCache.has(questionId)
    ? Boolean(favoriteStatusCache.get(questionId))
    : false

  if (!hasAccessToken.value || !isRealQuestion()) {
    return
  }

  if (favoriteStatusCache.has(questionId)) {
    return
  }

  favoriteLoading.value = true
  try {
    const result = await fetchFavoriteStatus(questionId)
    if (favoriteQuestionId.value === questionId) {
      currentFavorited.value = Boolean(result.is_favorited)
      favoriteStatusCache.set(questionId, currentFavorited.value)
    }
  } catch (error) {
    // Keep the stable local state when the status request is temporarily unavailable.
  } finally {
    if (favoriteQuestionId.value === questionId) {
      favoriteLoading.value = false
    }
  }
}

async function toggleCurrentFavorite() {
  syncAccessToken()

  if (!hasAccessToken.value) {
    uni.showToast({ title: '登录后才能收藏题目', icon: 'none' })
    return
  }

  if (!isRealQuestion() || favoriteLoading.value) {
    return
  }

  const questionId = questionMeta.value.questionId
  const previousFavorited = currentFavorited.value
  favoriteLoading.value = true
  try {
    if (previousFavorited) {
      const confirmed = await confirmFavoriteRemoval()
      if (!confirmed) return
    }

    const nextFavorited = !previousFavorited
    currentFavorited.value = nextFavorited
    favoriteStatusCache.set(questionId, nextFavorited)

    const result = await toggleFavorite(questionId)
    const persistedFavorited = Boolean(result.is_favorited)
    favoriteStatusCache.set(questionId, persistedFavorited)
    if (favoriteQuestionId.value === questionId) {
      currentFavorited.value = persistedFavorited
    }
  } catch (error) {
    favoriteStatusCache.set(questionId, previousFavorited)
    if (favoriteQuestionId.value === questionId) {
      currentFavorited.value = previousFavorited
    }
    uni.showToast({ title: error?.detail || '收藏状态更新失败', icon: 'none' })
  } finally {
    if (favoriteQuestionId.value === questionId) {
      favoriteLoading.value = false
    }
  }
}

function adaptiveLegacyFallbackTaskKey(context) {
  const sessionId = String(context?.sessionId || '')
  if (!sessionId) return ''
  return `${Number(context?.flowGeneration)}:${sessionId}`
}

function getAdaptiveLegacyFallbackTask(context = captureAdaptiveQuestionContext()) {
  const key = adaptiveLegacyFallbackTaskKey(context)
  if (!key || !isAdaptiveSessionContextCurrent(context)) return null
  return adaptiveLegacyFallbackTasks.get(key) || null
}

function startAdaptiveLegacyFallbackTask(
  reason = 'abandoned',
  context = captureAdaptiveQuestionContext()
) {
  if (!isAdaptiveSessionContextCurrent(context)) return null
  const key = adaptiveLegacyFallbackTaskKey(context)
  if (!key) return null
  const existingTask = adaptiveLegacyFallbackTasks.get(key)
  if (existingTask) return existingTask

  const taskContext = {
    flowGeneration: context.flowGeneration,
    sessionId: context.sessionId
  }
  const moduleInfos = getTargetModuleInfos()
  const requestedFallbackLimit = Number(
    adaptiveSession.value?.question_count || plannedQuestionLimit.value || 0
  )
  // Closing the old adaptive run is best-effort once fallback begins. The
  // question fallback starts immediately and never waits for that request.
  const closePromise = endAdaptiveSession(reason).catch(() => null)
  if (adaptiveSession.value?.id) {
    adaptiveSession.value = {
      ...adaptiveSession.value,
      status: reason === 'completed' ? 'completed' : 'abandoned'
    }
  }
  adaptiveFallbackMode.value = true
  adaptiveLegacyFallbackLoading.value = true
  adaptiveNextExhausted.value = true
  adaptiveNextFinishAvailable.value = false
  void closePromise

  const task = {
    key,
    context: taskContext,
    settled: false,
    promise: null
  }
  adaptiveLegacyFallbackTasks.set(key, task)
  task.promise = (async () => {
    try {
      const legacyPool = await loadLegacyQuestionPool(moduleInfos, {
        updateShortageTip: false
      })
      if (
        adaptiveLegacyFallbackTasks.get(key) !== task ||
        !isAdaptiveSessionContextCurrent(taskContext)
      ) {
        return { ready: false, stale: true, extended: false }
      }
      const existingQuestions = [...questionPool.value]
      const usedKeys = new Set(existingQuestions.map((item) => getQuestionIdentityKey(item)))
      const additions = legacyPool.filter((item) => !usedKeys.has(getQuestionIdentityKey(item)))
      const fallbackLimit = Math.max(requestedFallbackLimit, existingQuestions.length)
      questionPool.value = [...existingQuestions, ...additions].slice(0, fallbackLimit)
      shortageTip.value = '智能出题服务正在更新，本轮后续题目已切换为普通组题。'
      return {
        ready: true,
        stale: false,
        extended: questionPool.value.length > existingQuestions.length
      }
    } catch (error) {
      if (
        adaptiveLegacyFallbackTasks.get(key) === task &&
        isAdaptiveSessionContextCurrent(taskContext)
      ) {
        shortageTip.value = '个性化进度已安全保存，后续题目暂时加载失败。'
        return { ready: true, stale: false, extended: false }
      }
      return { ready: false, stale: true, extended: false }
    } finally {
      task.settled = true
      if (
        adaptiveLegacyFallbackTasks.get(key) === task &&
        isAdaptiveSessionContextCurrent(taskContext)
      ) {
        adaptiveLegacyFallbackLoading.value = false
      }
    }
  })()
  return task
}

async function switchAdaptiveSessionToLegacy(
  reason = 'abandoned',
  context = captureAdaptiveQuestionContext()
) {
  const task = startAdaptiveLegacyFallbackTask(reason, context)
  if (!task) return false
  const outcome = await task.promise
  return outcome?.ready === true && outcome?.extended === true
}

function adaptiveNextRequestKey(context) {
  return [
    context?.flowGeneration,
    context?.sessionId,
    context?.itemId
  ].map((value) => String(value ?? '')).join(':')
}

function requestAdaptiveNextQuestion(context) {
  const sessionId = String(context?.sessionId || adaptiveSession.value?.id || '')
  const requestKey = adaptiveNextRequestKey(context)
  return adaptiveNextRequestBroker.run(requestKey, async ({ isCurrent }) => {
    if (!isCurrent() || !isAdaptiveSessionContextCurrent(context)) {
      return { available: false, stale: true }
    }

    const requestToken = ++adaptiveNextRequestSequence
    activeAdaptiveNextRequestToken = requestToken
    const requestIsCurrent = () => (
      isCurrent() &&
      activeAdaptiveNextRequestToken === requestToken &&
      isAdaptiveSessionContextCurrent(context)
    )

    try {
      let pendingRetryUsed = false
      let duplicateRetryUsed = false
      while (requestIsCurrent()) {
        let response
        try {
          response = await fetchNextAdaptivePracticeItem(sessionId)
        } catch (error) {
          if (isAdaptiveUpdatePendingError(error) && !pendingRetryUsed) {
            pendingRetryUsed = true
            await flushPendingAnswerSubmissions({ queueScopeKey: sessionId })
            continue
          }
          throw error
        }
        if (!requestIsCurrent()) return { available: false, stale: true }
        if (response?.session?.id && String(response.session.id) !== sessionId) {
          throw new Error('个性化会话响应不一致，请重试')
        }

        applyAdaptiveEnvelope(response)
        const nextQuestion = buildAdaptiveQuestion(response?.next_item)
        if (!nextQuestion || response?.finished === true) {
          adaptiveNextExhausted.value = true
          return { available: false, finished: true }
        }

        const itemId = String(nextQuestion.adaptiveSessionItemId || '')
        const existingIndex = questionPool.value.findIndex(
          (item) => String(item.adaptiveSessionItemId || '') === itemId
        )
        if (existingIndex >= 0) {
          if (itemId !== String(context?.itemId || '')) {
            return { available: true, index: existingIndex, itemId }
          }
          if (!duplicateRetryUsed) {
            duplicateRetryUsed = true
            await flushPendingAnswerSubmissions({ queueScopeKey: sessionId })
            continue
          }
          return { available: false, duplicate: true }
        }

        questionPool.value = [...questionPool.value, nextQuestion]
        return {
          available: true,
          index: questionPool.value.length - 1,
          itemId
        }
      }
      return { available: false, stale: true }
    } catch (error) {
      if (!requestIsCurrent()) return { available: false, stale: true }
      if (isAdaptiveNextFallbackError(error)) {
        const previousLength = questionPool.value.length
        const extended = await switchAdaptiveSessionToLegacy('abandoned', context)
        if (extended && requestIsCurrent()) {
          return {
            available: true,
            index: Math.min(previousLength, questionPool.value.length - 1),
            fallback: true
          }
        }
        if (requestIsCurrent()) adaptiveNextExhausted.value = true
        return { available: false, finished: true, fallback: true }
      }
      throw error
    } finally {
      if (activeAdaptiveNextRequestToken === requestToken) {
        activeAdaptiveNextRequestToken = 0
      }
    }
  })
}

function exposeAdaptiveSafePoolCompletion(requestContext, { notify = false } = {}) {
  if (!isAdaptiveSessionContextCurrent(requestContext)) return false
  adaptiveNextExhausted.value = true
  adaptiveNextFinishAvailable.value = true
  shortageTip.value = '当前专项暂时没有合适的回稳题，可以先完成本轮。'
  if (notify) {
    uni.showToast({ title: shortageTip.value, icon: 'none' })
  }
  return true
}

function continueAdaptiveNextRequestInBackground(nextRequest, requestContext) {
  const prefetchToken = ++adaptiveNextPrefetchSequence
  activeAdaptiveNextPrefetchToken = prefetchToken
  adaptiveNextPrefetching.value = true
  void nextRequest
    .then((outcome) => {
      if (!isAdaptiveSessionContextCurrent(requestContext)) return
      if (outcome?.available || outcome?.finished) {
        drainAdaptiveNavigationIntent(requestContext)
      } else {
        clearAdaptiveNavigationIntent(requestContext)
      }
    })
    .catch((error) => {
      if (!isAdaptiveSessionContextCurrent(requestContext)) return
      if (isAdaptiveSafePoolError(error)) {
        exposeAdaptiveSafePoolCompletion(requestContext)
        drainAdaptiveNavigationIntent(requestContext)
      } else {
        clearAdaptiveNavigationIntent(requestContext)
      }
    })
    .finally(() => {
      if (activeAdaptiveNextPrefetchToken === prefetchToken) {
        activeAdaptiveNextPrefetchToken = 0
        adaptiveNextPrefetching.value = false
      }
    })
}

async function loadNextAdaptiveQuestion({ prefetchOnly = false, context = null } = {}) {
  const requestContext = context || captureAdaptiveQuestionContext()
  const sessionId = String(requestContext?.sessionId || adaptiveSession.value?.id || '')
  const joinsInFlightPrefetch = adaptiveNextRequestBroker.hasInFlight(
    adaptiveNextRequestKey(requestContext)
  )
  if (
    !sessionId ||
    !isAdaptiveSessionContextCurrent(requestContext) ||
    (!adaptiveMayHaveNext.value && !joinsInFlightPrefetch)
  ) {
    return false
  }

  const loadingToken = prefetchOnly ? 0 : ++adaptiveNextLoadingSequence
  const prefetchToken = prefetchOnly ? ++adaptiveNextPrefetchSequence : 0
  if (!prefetchOnly) {
    activeAdaptiveNextLoadingToken = loadingToken
    adaptiveNextLoading.value = true
  } else {
    activeAdaptiveNextPrefetchToken = prefetchToken
    adaptiveNextPrefetching.value = true
  }

  try {
    const nextRequest = requestAdaptiveNextQuestion(requestContext)
    const outcome = !prefetchOnly
      ? await Promise.race([
          nextRequest,
          new Promise((resolve) => {
            setTimeout(
              () => resolve(ADAPTIVE_PREFETCH_STILL_RUNNING),
              ADAPTIVE_FOREGROUND_PREFETCH_WAIT_MS
            )
          })
        ])
      : await nextRequest
    if (!isAdaptiveSessionContextCurrent(requestContext)) return false
    if (outcome === ADAPTIVE_PREFETCH_STILL_RUNNING) {
      setAdaptiveNavigationIntent('next', requestContext, { ready: false })
      if (!joinsInFlightPrefetch) {
        continueAdaptiveNextRequestInBackground(nextRequest, requestContext)
      }
      uni.showToast({ title: '下一题仍在后台匹配，完成后可直接继续', icon: 'none' })
      return false
    }
    if (!outcome?.available) {
      if (prefetchOnly && outcome?.finished) {
        drainAdaptiveNavigationIntent(requestContext)
      } else if (
        prefetchOnly &&
        adaptiveContextsMatch(adaptiveQueuedNavigation.value?.context, requestContext)
      ) {
        adaptiveQueuedNavigation.value = null
      }
      if (!prefetchOnly && outcome?.duplicate) {
        uni.showToast({ title: '作答记录正在同步，请稍后再试', icon: 'none' })
      }
      return false
    }
    if (prefetchOnly) {
      drainAdaptiveNavigationIntent(requestContext)
      return true
    }

    const nextIndex = currentQuestionIndex.value + 1
    if (!questionPool.value[nextIndex]) return false
    clearAdaptiveNavigationIntent(requestContext)
    applyQuestionAt(nextIndex)
    return true
  } catch (error) {
    if (!isAdaptiveSessionContextCurrent(requestContext)) return false
    // Transient speculative failures stay quiet and remain retryable. A safe-pool
    // shortage is terminal for this run, but never falls back to a harder item.
    if (prefetchOnly) {
      if (isAdaptiveSafePoolError(error)) {
        exposeAdaptiveSafePoolCompletion(requestContext)
        drainAdaptiveNavigationIntent(requestContext)
      } else if (adaptiveContextsMatch(adaptiveQueuedNavigation.value?.context, requestContext)) {
        adaptiveQueuedNavigation.value = null
      }
      return false
    }
    if (isAdaptiveSafePoolError(error)) {
      exposeAdaptiveSafePoolCompletion(requestContext, { notify: true })
      return false
    }
    if (isAdaptiveUpdatePendingError(error)) {
      uni.showToast({ title: '个性化进度正在同步，请稍后重试', icon: 'none' })
      return false
    }
    uni.showToast({
      title: adaptiveErrorMessage(error, '下一题匹配失败，请稍后重试'),
      icon: 'none'
    })
    return false
  } finally {
    if (!prefetchOnly && activeAdaptiveNextLoadingToken === loadingToken) {
      activeAdaptiveNextLoadingToken = 0
      adaptiveNextLoading.value = false
    }
    if (prefetchOnly && activeAdaptiveNextPrefetchToken === prefetchToken) {
      activeAdaptiveNextPrefetchToken = 0
      adaptiveNextPrefetching.value = false
    }
  }
}

function prefetchNextAdaptiveQuestion(question, context = captureAdaptiveQuestionContext(question)) {
  const itemId = String(question?.adaptiveSessionItemId || '')
  if (
    !itemId ||
    !isAdaptiveQuestionContextCurrent(context) ||
    adaptivePendingSubmissionPayloads.has(itemId) ||
    hasNextQuestion.value ||
    !adaptiveMayHaveNext.value
  ) {
    return Promise.resolve(false)
  }
  return loadNextAdaptiveQuestion({ prefetchOnly: true, context })
}

function goPrevQuestion() {
  if (!hasPrevQuestion.value || practiceMutationLocked.value) {
    return
  }

  if (reviewMode.value) {
    applyReviewAt(currentQuestionIndex.value - 1)
    scrollToQuestionTop()
  } else {
    applyQuestionAt(currentQuestionIndex.value - 1)
  }
}

async function goNextQuestion() {
  if (adaptiveForwardNavigationQueueable.value) {
    queueAdaptiveNavigationIntent('next')
    return
  }
  if (practiceMutationLocked.value) return
  adaptiveQueuedNavigation.value = null
  const navigationToken = ++questionNavigationSequence
  activeQuestionNavigationToken = navigationToken
  questionNavigationPending.value = true
  const context = captureAdaptiveQuestionContext()
  let finishAfterNavigation = false
  try {
    if (reviewMode.value) {
      applyReviewAt(currentQuestionIndex.value + 1)
      scrollToQuestionTop()
      return
    }

    const adaptiveProgressReady = await ensureAdaptiveProgressBeforeNext(currentQuestion.value)
    if (
      !adaptiveProgressReady ||
      activeQuestionNavigationToken !== navigationToken ||
      !isAdaptiveQuestionContextCurrent(context)
    ) {
      return
    }

    if (hasNextQuestion.value) {
      applyQuestionAt(currentQuestionIndex.value + 1)
      return
    }

    if (adaptiveMayHaveNext.value || adaptiveNextPrefetching.value) {
      const advanced = await loadNextAdaptiveQuestion()
      if (
        !advanced &&
        adaptiveNextExhausted.value &&
        !adaptiveNextFinishAvailable.value &&
        !adaptiveContextsMatch(adaptiveQueuedNavigation.value?.context, context)
      ) {
        finishAfterNavigation = true
      }
    } else if (
      adaptiveFallbackMode.value &&
      !hasNextQuestion.value &&
      !adaptiveLegacyFallbackLoading.value
    ) {
      finishAfterNavigation = true
    }
  } finally {
    if (activeQuestionNavigationToken === navigationToken) {
      activeQuestionNavigationToken = 0
      questionNavigationPending.value = false
      if (
        adaptiveQueuedNavigation.value?.ready === true &&
        adaptiveContextsMatch(adaptiveQueuedNavigation.value?.context, context)
      ) {
        drainAdaptiveNavigationIntent(context)
      }
    }
  }
  if (finishAfterNavigation) await finishQuiz()
}

function showSummary() {
  summaryMode.value = true
  aiSummaryMode.value = false
  reviewMode.value = false
  submitted.value = false
  nextTick(() => {
    scrollToQuestionTop()
  })
}

function openFirstReviewQuestion() {
  if (!reviewResults.value.length) {
    return
  }
  openReviewQuestion(firstReviewIndex.value)
}

async function retryPractice() {
  if (loading.value || quizStartInProgress.value) return
  if (mockExamMode.value) {
    if (mockExamPaperId.value) {
      await startFixedMockExam(mockExamPaperId.value)
    } else {
      await startMockExam()
    }
    return
  }
  await startQuiz()
}

function handleSummaryBack() {
  if (mockExamMode.value) {
    clearTimer()
    returnToMockExamList()
    return
  }
  resetToTags()
}

function returnToMockExamList() {
  if (exitNavigationPending) return

  exitNavigationPending = true
  const url = `/pages/mock-exams/index?exam_code=${encodeURIComponent(examCode.value)}`
  uni.redirectTo({
    url,
    fail() {
      uni.reLaunch({
        url,
        fail() {
          exitNavigationPending = false
          uni.showToast({ title: '退出失败，请再试一次', icon: 'none' })
        }
      })
    }
  })
}

function buildAiReviewResultFromSummaryItem(item) {
  const question = questionPool.value.find((row) => (row.questionId || row.id) === item.question_id)
  if (!question) {
    return null
  }
  return {
    question,
    selectedAnswer: item.selected_answer || '',
    correctAnswer: item.correct_answer || '待同步',
    explanation: item.explanation || '解析正在同步中，请稍后再试。',
    isCorrect: item.is_correct,
    syncFailed: item.is_correct === null || item.is_correct === undefined
  }
}

async function showAiSummary() {
  if (!aiSessionId.value) {
    showSummary()
    return
  }

  uni.showLoading({ title: '正在生成总结...' })
  try {
    const summary = await fetchAiTrainingSummary(aiSessionId.value)
    aiSummary.value = summary
    const summaryResults = (summary.items || []).map(buildAiReviewResultFromSummaryItem).filter(Boolean)
    if (summaryResults.length) {
      aiReviewResults.value = summaryResults
    }
  } catch (error) {
    aiSummary.value = {
      total_count: questionPool.value.length,
      correct_count: aiReviewResults.value.filter((item) => item.isCorrect).length,
      accuracy: aiSummaryAccuracy.value,
      summary: '本轮 AI 训练已完成，但总结同步暂时失败。',
      next_step: '可以先回看题目解析，稍后再进入练习历史查看完整记录。',
      weak_points: []
    }
  } finally {
    uni.hideLoading()
  }

  aiSummaryMode.value = true
  summaryMode.value = false
  reviewMode.value = false
  submitted.value = false
  nextTick(() => {
    scrollToQuestionTop()
  })
}

async function finishQuiz() {
  if (adaptiveForwardNavigationQueueable.value) {
    queueAdaptiveNavigationIntent('finish')
    return
  }
  if (practiceMutationLocked.value) return
  adaptiveQueuedNavigation.value = null
  const navigationToken = ++questionNavigationSequence
  activeQuestionNavigationToken = navigationToken
  questionNavigationPending.value = true
  const context = captureAdaptiveQuestionContext()
  try {
    if (isAiTrainingMode.value) {
      await showAiSummary()
      return
    }

    const adaptiveProgressReady = await ensureAdaptiveProgressBeforeNext(currentQuestion.value, {
      navigationAction: 'finish'
    })
    if (
      !adaptiveProgressReady ||
      activeQuestionNavigationToken !== navigationToken ||
      !isAdaptiveQuestionContextCurrent(context)
    ) {
      return
    }
    if (hasNextQuestion.value) {
      applyQuestionAt(currentQuestionIndex.value + 1)
      return
    }

    const completionPromise = endAdaptiveSession('completed').catch(() => null)
    const results = buildSpecialPracticeReviewResults()
    if (!results.length) {
      if (activeQuestionNavigationToken === navigationToken) resetToTags()
      void completionPromise
      return
    }

    reviewResults.value = results
    showAnswerSheet.value = false
    explanationExpanded.value = false
    showSummary()
    void completionPromise
  } catch (error) {
    if (activeQuestionNavigationToken === navigationToken) {
      uni.showToast({
        title: adaptiveErrorMessage(error, '练习结果同步失败，请重试'),
        icon: 'none'
      })
    }
  } finally {
    if (activeQuestionNavigationToken === navigationToken) {
      activeQuestionNavigationToken = 0
      questionNavigationPending.value = false
      if (
        adaptiveQueuedNavigation.value?.ready === true &&
        adaptiveContextsMatch(adaptiveQueuedNavigation.value?.context, context)
      ) {
        drainAdaptiveNavigationIntent(context)
      }
    }
  }
}

function buildSpecialPracticeReviewResults() {
  return questionPool.value
    .map((question) => {
      const key = question.questionId || question.id
      const saved = instantQuestionResults.value[key]
      if (!saved) return null

      return {
        question,
        selectedAnswer: saved.selectedAnswer || '',
        correctAnswer: saved.correctAnswer || question.answer || '',
        explanation: saved.explanation || question.explanation || '',
        isCorrect: saved.isCorrect ?? (saved.selectedAnswer === saved.correctAnswer),
        syncFailed: Boolean(saved.syncFailed)
      }
    })
    .filter(Boolean)
}

function resetQuizState() {
  clearTimer()
  showGradingFeedback.value = false
  selectedOption.value = ''
  submitted.value = false
  submitting.value = false
  explanationExpanded.value = false
  markingUnfamiliar.value = false
  timerSeconds.value = 0
  questionElapsedByKey.value = {}
  submissionIdsByQuestion.value = {}
  submissionUsedTimeByQuestion.value = {}
  submissionSessionId.value = createClientNonce()
  abilityAccuracy.value = null
  correctAnswer.value = ''
  answerExplanation.value = ''
  resultTag.value = ''
  instantQuestionResults.value = {}
  unfamiliarQuestionMap.value = {}
  comprehensiveSkippedQuestions.value = {}
  adaptiveComprehensiveSubmissionSnapshot = null
}

function hasDurableAdaptiveComprehensiveSubmissionTask() {
  return Boolean(
    adaptiveComprehensiveSubmissionSnapshot?.ownerUserId &&
    adaptiveComprehensiveSubmissionSnapshot?.sessionId &&
    adaptiveComprehensiveSubmissionSnapshot.sessionId === String(adaptiveSession.value?.id || '') &&
    adaptiveComprehensiveSubmissionSnapshot?.payload?.client_submission_id
  )
}

function resetToTags() {
  if (adaptiveAnswerSyncing.value || adaptiveNavigationQueued.value) {
    uni.showToast({ title: '本题正在后台保存，完成后会自动继续', icon: 'none' })
    return
  }
  activeQuizStartRequestToken = 0
  quizStartInProgress.value = false
  quizStartBackgrounded.value = false
  loading.value = false
  uni.hideLoading()
  const preserveDurableComprehensiveSubmission = hasDurableAdaptiveComprehensiveSubmissionTask()
  if (preserveDurableComprehensiveSubmission) {
    resumePendingAdaptiveComprehensiveSubmissions()
  } else {
    void endAdaptiveSession('abandoned')
  }
  aiSessionId.value = ''
  mockExamMode.value = false
  showAnswerSheet.value = false
  mode.value = 'tags'
  questionPool.value = buildMockPool()
  currentQuestionIndex.value = 0
  questionMeta.value = {
    questionId: '',
    module: '',
    submodule: ''
  }
  comprehensiveAnswers.value = {}
  reviewMode.value = false
  reviewResults.value = []
  summaryMode.value = false
  aiSummaryMode.value = false
  aiSummary.value = null
  aiReviewResults.value = []
  resetAdaptivePracticeState()
  resetQuizState()
  loadCultureProgress()
}

function createClientNonce() {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
}

function ensureSubmissionSession() {
  if (!submissionSessionId.value) {
    submissionSessionId.value = createClientNonce()
  }
  return submissionSessionId.value
}

function getClientSubmissionId(questionKey, kind = 'answer') {
  const normalizedKey = String(questionKey || '').trim()
  if (!normalizedKey) {
    return null
  }
  const mapKey = `${kind}:${normalizedKey}`
  const existing = submissionIdsByQuestion.value[mapKey]
  if (existing) {
    return existing
  }
  const value = `${ensureSubmissionSession()}:${kind}:${normalizedKey}`.slice(0, 120)
  submissionIdsByQuestion.value = {
    ...submissionIdsByQuestion.value,
    [mapKey]: value
  }
  return value
}

function getQuestionElapsed(questionKey) {
  const normalizedKey = String(questionKey || '').trim()
  return Math.max(0, Number(questionElapsedByKey.value[normalizedKey] || 0))
}

function getSubmissionUsedTime(questionKey, kind = 'answer') {
  const normalizedKey = String(questionKey || '').trim()
  if (!normalizedKey) {
    return 0
  }
  const mapKey = `${kind}:${normalizedKey}`
  if (submissionUsedTimeByQuestion.value[mapKey] !== undefined) {
    return Math.max(0, Number(submissionUsedTimeByQuestion.value[mapKey] || 0))
  }
  const usedTime = getQuestionElapsed(normalizedKey)
  submissionUsedTimeByQuestion.value = {
    ...submissionUsedTimeByQuestion.value,
    [mapKey]: usedTime
  }
  return usedTime
}

function saveCurrentQuestionTime() {
  const normalizedKey = String(activeTimerQuestionKey || '').trim()
  if (!normalizedKey) {
    return
  }
  const elapsed = Math.max(0, Number(timerSeconds.value || 0))
  questionElapsedByKey.value = {
    ...questionElapsedByKey.value,
    [normalizedKey]: elapsed
  }
}

function startTimer(questionKey) {
  clearTimer()
  const normalizedKey = String(questionKey || '').trim()
  if (!normalizedKey) {
    return
  }
  activeTimerQuestionKey = normalizedKey
  timerSeconds.value = getQuestionElapsed(normalizedKey)
  timerId = setInterval(() => {
    timerSeconds.value += 1
    questionElapsedByKey.value = {
      ...questionElapsedByKey.value,
      [normalizedKey]: timerSeconds.value
    }
  }, 1000)
}

function clearTimer() {
  saveCurrentQuestionTime()
  if (timerId) {
    clearInterval(timerId)
    timerId = null
  }
  activeTimerQuestionKey = ''
}

function formatDuration(seconds) {
  const total = Math.max(0, Math.round(Number(seconds || 0)))
  const min = String(Math.floor(total / 60)).padStart(2, '0')
  const sec = String(total % 60).padStart(2, '0')
  return `${min}:${sec}`
}

function scrollToQuestionTop() {
  uni.pageScrollTo({
    scrollTop: 0,
    duration: 0
  })
}

</script>

<style scoped>
.practice-page {
  min-height: 100vh;
  min-height: 100dvh;
  padding: calc(var(--status-bar-height) + 16rpx) 28rpx calc(env(safe-area-inset-bottom) + 188rpx);
  background:
    radial-gradient(circle at top right, var(--gyt-primary-shadow), transparent 28%),
    var(--gyt-page-bg);
}

.practice-page.result-summary-page {
  padding: 0 28rpx calc(env(safe-area-inset-bottom) + 56rpx);
  background: #f7f6f8 !important;
}

.top-nav {
  display: flex;
  align-items: center;
  gap: 18rpx;
  margin-bottom: 22rpx;
}

.practice-page.quiz-page {
  height: 100vh;
  height: 100dvh;
  min-height: 0;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  overscroll-behavior: contain;
  padding: calc(var(--status-bar-height) + 10rpx) 28rpx calc(env(safe-area-inset-bottom) + 18rpx);
}

.quiz-page .top-nav {
  flex: 0 0 auto;
  margin-bottom: 10rpx;
}

.quiz-page .back-btn {
  width: 68rpx;
  height: 68rpx;
  border-radius: 22rpx;
}

.quiz-page .top-title {
  font-size: 32rpx;
}

.quiz-page .top-sub {
  margin-top: 2rpx;
  font-size: 20rpx;
}

.scope-top-nav {
  position: fixed;
  top: 0;
  right: 0;
  left: 0;
  z-index: 24;
  min-height: calc(var(--status-bar-height, env(safe-area-inset-top)) + 108rpx);
  margin: 0;
  padding: calc(var(--status-bar-height, env(safe-area-inset-top)) + 16rpx) 28rpx 16rpx;
  box-sizing: border-box;
  background: var(--gyt-page-bg, #f8faff);
  box-shadow: 0 14rpx 30rpx rgba(20, 31, 66, var(--scope-header-shadow-opacity, 0));
  transition: box-shadow 180ms ease;
}

.quiz-page .scope-top-nav {
  flex: 0 0 auto;
  margin: 0;
}

.quiz-page .scope-top-nav .back-btn {
  width: 76rpx;
  height: 76rpx;
  border-radius: 26rpx;
}

.quiz-page .scope-top-nav .top-title {
  font-size: 38rpx;
}

.scope-top-nav-spacer {
  width: 100%;
  height: 114rpx;
  flex: 0 0 114rpx;
}

.result-summary-page .scope-top-nav {
  min-height: calc(var(--status-bar-height, env(safe-area-inset-top)) + 124rpx);
  padding: calc(var(--status-bar-height, env(safe-area-inset-top)) + 12rpx) 28rpx 12rpx;
  background: #f7f6f8;
  box-shadow: none;
}

.result-summary-page .scope-top-nav-spacer {
  height: calc(var(--status-bar-height, env(safe-area-inset-top)) + 124rpx);
  flex: 0 0 calc(var(--status-bar-height, env(safe-area-inset-top)) + 124rpx);
}

.result-summary-page .scope-top-nav .back-btn {
  width: 100rpx;
  height: 100rpx;
  border-radius: 38rpx;
  box-shadow: 0 8rpx 24rpx rgba(22, 32, 51, 0.045);
}

.result-summary-page .scope-top-nav .back-icon {
  width: 32rpx;
  height: 32rpx;
}

.result-summary-page .scope-top-copy .top-title-row {
  top: calc(var(--status-bar-height, env(safe-area-inset-top)) + 62rpx);
}

.result-summary-page .scope-top-copy .top-title {
  color: #162033;
  font-size: 40rpx;
  font-weight: 900;
}

.back-btn {
  width: 76rpx;
  height: 76rpx;
  padding: 0;
  border: 0;
  border-radius: 26rpx;
  background: #ffffff;
  color: #172033;
  font-size: 42rpx;
  font-weight: 700;
  line-height: 76rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.08);
}

.back-btn::after {
  border: 0;
}

.back-icon {
  width: 30rpx;
  height: 30rpx;
  display: block;
}

.top-copy {
  min-width: 0;
  flex: 1;
}

.top-title-row {
  min-width: 0;
}

.scope-top-copy {
  min-height: 76rpx;
  margin-top: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.top-title {
  color: #172033;
  font-size: 38rpx;
  font-weight: 900;
}

.scope-top-copy .top-title-row {
  position: absolute;
  top: calc(var(--status-bar-height, env(safe-area-inset-top)) + 54rpx);
  left: 50%;
  width: max-content;
  max-width: calc(100% - 220rpx);
  display: flex;
  align-items: baseline;
  justify-content: center;
  gap: 10rpx;
  pointer-events: none;
  transform: translate(-50%, -50%);
}

.scope-top-copy .top-title {
  min-width: 0;
  overflow: hidden;
  text-align: center;
  line-height: 1.35;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.top-sub {
  margin-top: 6rpx;
  color: #667085;
  font-size: 24rpx;
}

.scope-top-copy .top-sub {
  flex: 0 0 auto;
  margin-top: 0;
  line-height: 1.35;
  white-space: nowrap;
}

.setup-hero {
  margin-bottom: 22rpx;
  padding: 34rpx 30rpx;
  border-radius: 36rpx;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.94), rgba(238, 244, 255, 0.96)),
    radial-gradient(circle at 0 0, var(--gyt-primary-shadow), transparent 46%);
  border: 2rpx solid rgba(219, 228, 245, 0.92);
  box-shadow: 0 20rpx 46rpx rgba(20, 31, 66, 0.08);
}

.setup-eyebrow {
  color: var(--gyt-primary);
  font-size: 23rpx;
  font-weight: 900;
}

.setup-title {
  margin-top: 8rpx;
  color: #101828;
  font-size: 44rpx;
  line-height: 1.22;
  font-weight: 900;
}

.setup-sub {
  margin-top: 14rpx;
  color: #667085;
  font-size: 25rpx;
  line-height: 1.65;
}

.mode-card,
.count-card,
.adaptive-preference-card {
  margin-bottom: 24rpx;
  padding: 26rpx;
  border-radius: 34rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 16rpx 36rpx rgba(20, 31, 66, 0.06);
}

.mode-card {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18rpx;
}

.mode-option {
  min-height: 138rpx;
  padding: 26rpx 22rpx;
  border-radius: 28rpx;
  border: 2rpx solid var(--gyt-primary-border);
  background: var(--gyt-primary-tint);
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.mode-option.active {
  border-color: var(--gyt-primary);
  background: linear-gradient(180deg, var(--gyt-primary-tint) 0%, var(--gyt-primary-soft) 100%);
  box-shadow: 0 10rpx 22rpx var(--gyt-primary-shadow);
}

.mode-title,
.count-title {
  color: #172033;
  font-size: 30rpx;
  font-weight: 900;
}

.mode-sub {
  margin-top: 8rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.6;
}

.state-box {
  margin-bottom: 20rpx;
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

.culture-progress-card {
  margin-bottom: 24rpx;
  padding: 28rpx;
  border-radius: 34rpx;
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(248, 250, 255, 0.94)),
    radial-gradient(circle at 100% 0, var(--gyt-primary-shadow), transparent 42%);
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 16rpx 36rpx rgba(20, 31, 66, 0.06);
}

.adaptive-preference-head,
.adaptive-summary-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
}

.adaptive-preference-title {
  color: #172033;
  font-size: 29rpx;
  font-weight: 900;
}

.adaptive-preference-sub,
.adaptive-preference-tip,
.adaptive-summary-copy {
  color: #667085;
  font-size: 23rpx;
  line-height: 1.55;
}

.adaptive-preference-sub {
  margin-top: 6rpx;
}

.adaptive-preference-badge,
.adaptive-summary-confidence {
  flex-shrink: 0;
  padding: 8rpx 15rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 21rpx;
  font-weight: 800;
}

.adaptive-preference-options {
  margin-top: 22rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12rpx;
}

.adaptive-preference-option {
  min-width: 0;
  min-height: 106rpx;
  padding: 16rpx 10rpx;
  border: 2rpx solid #e5eaf3;
  border-radius: 22rpx;
  background: #f8fafc;
  color: #344054;
  line-height: 1.3;
}

.adaptive-preference-option::after {
  border: 0;
}

.adaptive-preference-option.active {
  border-color: var(--gyt-primary);
  background: var(--gyt-primary-tint);
  color: var(--gyt-primary);
  box-shadow: 0 8rpx 18rpx var(--gyt-primary-shadow);
}

.adaptive-preference-option-title,
.adaptive-preference-option-sub {
  display: block;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.adaptive-preference-option-title {
  font-size: 24rpx;
  font-weight: 850;
}

.adaptive-preference-option-sub {
  margin-top: 7rpx;
  font-size: 20rpx;
}

.adaptive-preference-tip {
  margin-top: 18rpx;
}

.culture-progress-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20rpx;
}

.culture-progress-title {
  color: #172033;
  font-size: 30rpx;
  font-weight: 900;
}

.culture-progress-sub {
  margin-top: 8rpx;
  color: #667085;
  font-size: 23rpx;
  line-height: 1.5;
}

.culture-percent {
  min-width: 100rpx;
  padding: 10rpx 16rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 27rpx;
  font-weight: 950;
  text-align: center;
  flex-shrink: 0;
}

.culture-progress-track {
  height: 14rpx;
  margin-top: 24rpx;
  border-radius: 999rpx;
  background: #eef2f8;
  overflow: hidden;
}

.culture-progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, var(--gyt-primary), #7ea8ff);
  box-shadow: 0 8rpx 20rpx var(--gyt-primary-shadow);
}

.count-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 22rpx;
}

.count-copy {
  flex: 1;
  min-width: 0;
}

.count-value {
  min-width: 104rpx;
  padding: 10rpx 18rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 26rpx;
  line-height: 1.2;
  font-weight: 900;
  text-align: center;
  flex-shrink: 0;
}

.count-slider-wrap {
  margin-top: 26rpx;
  padding: 8rpx 18rpx 0;
}

.count-slider {
  margin: 0;
}

.count-scale {
  position: relative;
  height: 54rpx;
  padding: 0;
  margin-top: -2rpx;
}

.scale-value {
  position: absolute;
  top: 0;
  transform: translateX(-50%);
  min-width: 38rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #98a2b3;
  font-size: 21rpx;
  line-height: 1.2;
  font-weight: 800;
  text-align: center;
}

.scale-value.active {
  color: var(--gyt-primary);
  font-size: 23rpx;
  font-weight: 950;
}

.scale-value::before {
  content: '';
  width: 6rpx;
  height: 6rpx;
  margin: 0 auto 10rpx;
  border-radius: 50%;
  background: #c9d3e5;
  display: block;
}

.scale-value.active::before {
  width: 8rpx;
  height: 8rpx;
  background: var(--gyt-primary);
}

.sticky-bar {
  position: fixed;
  z-index: 30;
  left: 28rpx;
  right: 28rpx;
  bottom: calc(env(safe-area-inset-bottom) + 22rpx);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 22rpx 24rpx;
  border-radius: 36rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 18rpx 44rpx rgba(20, 31, 66, 0.12);
  backdrop-filter: blur(16rpx);
}

.sticky-copy {
  min-width: 0;
  flex: 1;
}

.sticky-copy--single {
  min-height: 92rpx;
  display: flex;
  align-items: center;
}

.sticky-copy--comprehensive .sticky-title {
  white-space: nowrap;
  word-break: keep-all;
}

.sticky-title {
  font-size: 28rpx;
  font-weight: 900;
  color: #172033;
}

.sticky-btn {
  min-width: 196rpx;
  min-height: 92rpx;
  padding: 0 24rpx;
  border: 0;
  border-radius: 28rpx;
  background: var(--gyt-primary);
  color: #ffffff;
  font-size: 26rpx;
  font-weight: 900;
  box-shadow: 0 14rpx 28rpx var(--gyt-primary-shadow);
  -webkit-tap-highlight-color: transparent;
  transform: translateZ(0);
  transition: transform 120ms ease, filter 120ms ease, box-shadow 120ms ease;
}

.sticky-btn::after {
  border: 0;
}

.sticky-btn:not([disabled]):active,
.sticky-btn:not([disabled]).sticky-btn--pressed {
  filter: brightness(0.95);
  transform: scale(0.985);
  box-shadow: 0 8rpx 16rpx var(--gyt-primary-shadow);
}

.sticky-actions {
  display: flex;
  align-items: center;
  gap: 14rpx;
  flex-shrink: 0;
}

.sticky-actions.dual .sticky-btn {
  min-width: 156rpx;
  padding: 0 16rpx;
}

.sticky-actions.dual {
  gap: 12rpx;
}

.start-sticky-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1.2;
}

.start-sticky-label {
  transform: translateY(2rpx);
}

.review-sticky-btn {
  background: #ffffff;
  color: var(--gyt-primary);
  border: 0;
  box-shadow: 0 12rpx 26rpx rgba(20, 31, 66, 0.08);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  line-height: 1.2;
}

.sticky-btn-sub {
  margin-top: 6rpx;
  font-size: 19rpx;
  font-weight: 800;
  opacity: 0.86;
}

.start-sticky-btn[disabled] {
  border: 0;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  box-shadow: none;
  opacity: 1;
}

.review-sticky-btn[disabled] {
  background: #f2f4f7;
  color: #a7afb9;
  border: 0;
  box-shadow: none;
}

.quiz-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12rpx;
  margin-bottom: 16rpx;
}

.quiz-top-leading {
  min-width: 0;
  display: flex;
  align-items: flex-start;
  gap: 10rpx;
  flex: 1 1 auto;
}

.quiz-top-leading > .badge {
  flex: 0 0 auto;
  white-space: nowrap;
}

.quiz-top-actions {
  display: flex;
  align-items: center;
  gap: 10rpx;
  flex: 0 0 auto;
}

.quiz-page .quiz-shell {
  flex: 0 0 auto;
  padding: 16rpx 20rpx 14rpx;
  border-radius: 30rpx;
}

.quiz-page .quiz-top {
  margin-bottom: 8rpx;
}

.quiz-page .quiz-top-leading,
.quiz-page .quiz-top-actions {
  gap: 8rpx;
}

.quiz-page .badge {
  padding: 8rpx 14rpx;
  font-size: 21rpx;
}

.quiz-page .timer {
  padding: 10rpx 14rpx;
  border-radius: 18rpx;
  font-size: 21rpx;
}

.quiz-page .question-head {
  margin-bottom: 8rpx;
}

.quiz-page .favorite-btn {
  width: 54rpx;
  height: 54rpx;
  font-size: 30rpx;
}

.quiz-page .question-card {
  min-height: 92rpx;
  padding: 4rpx 4rpx;
}

.quiz-page .question-title {
  padding-right: 62rpx;
  font-size: 34rpx;
  line-height: 1.42;
}

.question-map-btn {
  min-width: 92rpx;
  min-height: 58rpx;
  margin: 0;
  padding: 0 20rpx;
  border: 0;
  border-radius: 18rpx;
  background: #ffffff;
  color: var(--gyt-primary);
  font-size: 23rpx;
  font-weight: 900;
  box-shadow: 0 10rpx 24rpx rgba(20, 31, 66, 0.08);
}

.question-map-btn::after {
  border: 0;
}

.quiz-shell {
  padding: 24rpx 22rpx 22rpx;
  border-radius: 36rpx;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.86), rgba(245, 248, 255, 0.94)),
    radial-gradient(circle at top left, var(--gyt-primary-shadow), transparent 42%);
  border: 2rpx solid rgba(230, 235, 245, 0.9);
  box-shadow: 0 16rpx 36rpx rgba(20, 31, 66, 0.06);
}

.badge {
  display: inline-flex;
  align-items: center;
  padding: 12rpx 18rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 23rpx;
  font-weight: 900;
}

.badge.plain {
  margin-bottom: 0;
}

.question-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  margin-bottom: 18rpx;
}

.favorite-btn {
  position: absolute;
  top: 50%;
  right: 0;
  width: 64rpx;
  height: 64rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  color: #98a2b3;
  font-size: 34rpx;
  font-weight: 900;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: none;
  transform: translate3d(0, -50%, 0);
  transition: none;
  -webkit-tap-highlight-color: transparent;
}

.favorite-btn::after {
  border: 0;
}

.practice-favorite-icon {
  width: 32rpx;
  height: 32rpx;
  display: block;
  flex: none;
  transform: none;
  transition: none;
}

.favorite-btn.active {
  color: #f5b700;
}

.favorite-btn[disabled] {
  opacity: 1;
}

.favorite-btn:active,
.favorite-btn.active,
.favorite-btn[disabled] {
  transform: translate3d(0, -50%, 0);
}

.timer {
  padding: 14rpx 18rpx;
  border-radius: 20rpx;
  background: #fff8eb;
  color: #b7791f;
  border: 2rpx solid #fde7b0;
  font-size: 23rpx;
  font-weight: 900;
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
}

.timer-icon {
  display: block;
  width: 26rpx;
  height: 26rpx;
}

.question-card {
  position: relative;
  min-height: 104rpx;
  padding: 18rpx 8rpx 12rpx;
  border-radius: 0;
  background: #ffffff;
  border: 0;
  box-shadow: none;
  background: transparent;
  display: flex;
  align-items: center;
}

.question-title {
  width: 100%;
  box-sizing: border-box;
  padding-right: 70rpx;
  color: #172033;
  font-size: 38rpx;
  line-height: 1.55;
  font-weight: 900;
}

.helper-box {
  margin-top: 22rpx;
  padding: 22rpx;
  border-radius: 24rpx;
  border: 2rpx dashed var(--gyt-primary-border);
  background: var(--gyt-primary-tint);
  color: #476089;
  font-size: 24rpx;
  line-height: 1.6;
  text-align: center;
}

.options {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  margin: 24rpx 0;
}

.submit-btn {
  width: 100%;
  min-height: 104rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 28rpx;
  background: var(--gyt-primary);
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 900;
  line-height: 1.25;
  text-align: center;
  box-shadow: 0 14rpx 28rpx var(--gyt-primary-shadow);
  -webkit-tap-highlight-color: transparent;
  transform: translateZ(0);
  transition: transform 110ms ease, filter 110ms ease, box-shadow 110ms ease;
}

.submit-btn::after {
  border: 0;
}

.submit-btn:not([disabled]):active,
.submit-btn:not([disabled]).submit-btn--pressed {
  filter: brightness(0.9);
  transform: translateY(2rpx) scale(0.97);
  box-shadow: 0 5rpx 12rpx var(--gyt-primary-shadow);
}

.quiz-page .options {
  flex: 1 1 auto;
  min-height: 0;
  display: grid;
  grid-template-rows: repeat(4, minmax(112rpx, 1fr));
  gap: 12rpx;
  margin: 12rpx 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  scrollbar-width: none;
}

.quiz-page .options::-webkit-scrollbar {
  display: none;
}

.submit-btn[disabled] {
  border: 0;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  box-shadow: none;
}

.summary-card {
  padding: 36rpx 32rpx;
  border-radius: 36rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.05);
}

.summary-card--with-stats {
  min-height: 0;
}

.adaptive-summary-card {
  margin-top: 24rpx;
  padding: 26rpx 28rpx;
  border: 1rpx solid var(--gyt-primary-border);
  border-radius: 36rpx;
  background: linear-gradient(145deg, #ffffff, var(--gyt-primary-tint));
}

.adaptive-summary-eyebrow {
  color: var(--gyt-primary);
  font-size: 21rpx;
  font-weight: 800;
}

.adaptive-summary-level {
  margin-top: 7rpx;
  color: #172033;
  font-size: 34rpx;
  font-weight: 900;
}

.adaptive-summary-copy {
  margin-top: 18rpx;
}

.result-summary-page .result-overview-card {
  padding: 30rpx 30rpx 26rpx;
  border: 1rpx solid #e8edf5;
  border-radius: 56rpx;
  background: #ffffff;
  box-shadow: none;
}

.result-overview-main {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 26rpx;
}

.summary-card-copy {
  min-width: 0;
  flex: 1 1 auto;
}

.summary-stat-stack {
  width: 45%;
  min-width: 224rpx;
  flex: 0 0 45%;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.summary-stat-row {
  min-width: 0;
  min-height: 68rpx;
  padding: 8rpx 14rpx;
  box-sizing: border-box;
  border: 1rpx solid #edf1f6;
  border-radius: 34rpx;
  background: #f6f8fb;
  display: flex;
  align-items: center;
  gap: 11rpx;
}

.summary-stat-icon {
  width: 38rpx;
  height: 38rpx;
  flex: 0 0 38rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-stat-icon image {
  width: 30rpx;
  height: 30rpx;
  display: block;
}

.summary-stat-copy {
  min-width: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.summary-stat-value {
  overflow: hidden;
  color: #162033;
  font-size: 28rpx;
  line-height: 1.1;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.summary-stat-label {
  margin-top: 4rpx;
  color: #7e889c;
  font-size: 21rpx;
  line-height: 1.1;
  font-weight: 500;
  white-space: nowrap;
}

.result-overview-card .summary-kicker {
  color: var(--gyt-primary);
  font-size: 23rpx;
  line-height: 1.35;
  font-weight: 800;
}

.result-overview-card .summary-score {
  margin-top: 12rpx;
  display: flex;
  align-items: baseline;
  color: #162033;
  line-height: 1;
}

.summary-score-main {
  font-size: 76rpx;
  font-weight: 900;
  letter-spacing: -3rpx;
}

.summary-score-total {
  margin-left: 10rpx;
  color: #7e889c;
  font-size: 46rpx;
  font-weight: 700;
  letter-spacing: -1rpx;
}

.mock-summary-card {
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.98), rgba(240, 246, 255, 0.96)),
    radial-gradient(circle at top right, var(--gyt-primary-shadow), transparent 48%);
}

.result-summary-page .mock-section-card {
  margin-top: 36rpx;
  border: 1rpx solid #e8edf5;
  border-radius: 52rpx;
  box-shadow: none;
}

.mock-section-card {
  margin-top: 22rpx;
  padding: 26rpx;
  border-radius: 32rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.05);
}

.mock-section-title {
  color: #172033;
  font-size: 28rpx;
  font-weight: 900;
}

.mock-section-row {
  margin-top: 18rpx;
  padding: 18rpx 20rpx;
  border-radius: 24rpx;
  background: #f8fbff;
  border: 2rpx solid #eef3fb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18rpx;
}

.mock-section-name {
  color: #172033;
  font-size: 24rpx;
  font-weight: 900;
}

.mock-section-sub {
  margin-top: 6rpx;
  color: #667085;
  font-size: 21rpx;
}

.mock-section-score {
  color: var(--gyt-primary);
  font-size: 28rpx;
  font-weight: 900;
  white-space: nowrap;
}

.ai-summary-card {
  background:
    linear-gradient(145deg, rgba(255, 255, 255, 0.96), rgba(235, 244, 255, 0.96)),
    radial-gradient(circle at top right, var(--gyt-primary-shadow), transparent 42%);
}

.ai-diagnosis-card {
  margin-top: 22rpx;
  padding: 30rpx;
  border-radius: 34rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
  box-shadow: 0 12rpx 28rpx rgba(20, 31, 66, 0.05);
}

.ai-diagnosis-title {
  color: #172033;
  font-size: 28rpx;
  font-weight: 900;
}

.ai-diagnosis-title + .ai-diagnosis-text {
  margin-top: 10rpx;
}

.ai-diagnosis-text + .ai-diagnosis-title {
  margin-top: 24rpx;
}

.ai-diagnosis-text {
  color: #667085;
  font-size: 25rpx;
  line-height: 1.65;
}

.ai-weak-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
  margin-top: 24rpx;
}

.ai-weak-tags text {
  padding: 9rpx 14rpx;
  border-radius: 999rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 22rpx;
  font-weight: 800;
}

.summary-kicker {
  color: var(--gyt-primary);
  font-size: 24rpx;
  font-weight: 800;
}

.summary-score {
  margin-top: 12rpx;
  color: #172033;
  font-size: 64rpx;
  font-weight: 900;
}

.summary-sub {
  margin-top: 10rpx;
  color: #667085;
  font-size: 24rpx;
  line-height: 1.6;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 22rpx;
  padding: 24rpx;
  border-radius: 32rpx;
  background: #ffffff;
  border: 2rpx solid #e6ebf5;
}

.summary-dot {
  width: 100%;
  min-width: 0;
  min-height: 78rpx;
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  border: 0;
  border-radius: 22rpx;
  color: #ffffff;
  font-size: 28rpx;
  line-height: 1;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}

.summary-dot.correct {
  background: #16a34a;
}

.summary-dot.wrong {
  background: #ef4444;
}

.summary-dot.pending {
  background: #f59e0b;
}

.result-answer-card {
  margin-top: 36rpx;
  padding: 26rpx 28rpx 28rpx;
  display: block;
  border: 1rpx solid #e8edf5;
  border-radius: 52rpx;
  background: #ffffff;
  box-shadow: none;
}

.result-answer-head {
  display: flex;
  align-items: center;
  justify-content: flex-start;
  gap: 20rpx;
}

.result-answer-title {
  color: #162033;
  font-size: 28rpx;
  line-height: 1.3;
  font-weight: 800;
}

.result-question-grid {
  margin-top: 22rpx;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14rpx;
}

.result-question-grid .summary-dot {
  width: 80rpx;
  min-height: 80rpx;
  justify-self: center;
  border-radius: 24rpx;
  font-size: 27rpx;
}

.result-question-grid .summary-dot.correct {
  background: #2f946f;
}

.result-question-grid .summary-dot.wrong {
  background: #d95c63;
}

.result-question-grid .summary-dot.pending {
  background: #bd8730;
}

.result-advice {
  min-height: 120rpx;
  margin-top: 32rpx;
  padding: 18rpx 22rpx;
  box-sizing: border-box;
  border-radius: 40rpx;
  background: var(--gyt-primary-tint, #f4f8ff);
  color: #56647a;
  display: flex;
  align-items: center;
  gap: 16rpx;
  font-size: 26rpx;
  line-height: 1.5;
  font-weight: 500;
}

.result-advice-icon {
  width: 34rpx;
  height: 34rpx;
  flex: 0 0 34rpx;
  display: block;
}

.summary-actions {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 20rpx;
}

.result-summary-actions {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14rpx;
  margin-top: 40rpx;
}

.summary-action-primary,
.summary-action-secondary {
  box-sizing: border-box;
  width: 100%;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  font-weight: 700;
  line-height: 1.25;
}

.summary-action-primary {
  grid-column: 1 / -1;
  min-height: 116rpx;
  padding: 0 24rpx;
  border: 0;
  border-radius: 48rpx;
  background: #172238;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 800;
  gap: 20rpx;
}

.summary-action-primary:active {
  opacity: 0.88;
}

.summary-action-arrow {
  font-size: 38rpx;
  line-height: 1;
  font-weight: 400;
}

.summary-action-secondary {
  min-height: 96rpx;
  padding: 0 14rpx;
  border: 3rpx solid #526076;
  border-radius: 44rpx;
  background: #ffffff;
  color: #26344b;
  font-size: 26rpx;
  font-weight: 700;
  gap: 11rpx;
}

.summary-action-secondary:active {
  background: var(--gyt-primary-tint, #f4f8ff);
}

.summary-action-primary::after,
.summary-action-secondary::after {
  border: 0;
}

.primary-action-row {
  display: flex;
  align-items: stretch;
  gap: 16rpx;
}

.quiz-page .primary-action-row {
  flex: 0 0 auto;
  gap: 12rpx;
}

.quiz-page .prev-btn,
.quiz-page .submit-btn {
  min-height: 112rpx;
  border-radius: 28rpx;
  font-size: 28rpx;
}

.quiz-page .unfamiliar-btn {
  min-height: 96rpx;
  margin-top: 12rpx;
  border-radius: 26rpx;
  font-size: 26rpx;
}

/* 答题后的底部操作区与未答题状态使用同一套占位尺寸，保持一屏完成操作。 */
.quiz-page .action-row {
  flex: 0 0 auto;
  gap: 12rpx;
  margin-top: 0;
}

.quiz-page .review-nav-row {
  gap: 12rpx;
}

.quiz-page .review-nav-row .next-btn.secondary {
  flex: 0 0 35%;
}

.quiz-page .action-row .next-btn {
  min-height: 112rpx;
}

.quiz-page .post-submit-action-row {
  flex: 0 0 auto;
  margin-top: 12rpx;
}

.quiz-page .post-submit-action-row .unfamiliar-btn,
.quiz-page .post-submit-action-row .explanation-toggle-btn {
  min-height: 96rpx;
  font-size: 26rpx;
}

.prev-btn {
  flex: 0 0 35%;
  min-height: 104rpx;
  margin: 0;
  padding: 0 18rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 28rpx;
  border: 0;
  background: #ffffff;
  color: var(--gyt-primary);
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1.25;
  text-align: center;
  box-shadow: 0 10rpx 22rpx rgba(20, 31, 66, 0.06);
}

.prev-btn::after,
.next-btn::after {
  border: 0;
}

.primary-action-row .submit-btn {
  flex: 1;
  width: auto;
  margin: 0;
}

.unfamiliar-btn {
  width: 100%;
  min-height: 88rpx;
  margin-top: 16rpx;
  padding: 0 24rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 26rpx;
  border: 0;
  background: #fff7ed;
  color: #c2410c;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 1.25;
  text-align: center;
  box-shadow: none;
}

.unfamiliar-btn::after {
  border: 0;
}

.unfamiliar-btn[disabled] {
  border: 0;
  background: #f2f4f7;
  color: #98a2b3;
}

.post-submit-action-row {
  display: flex;
  align-items: stretch;
  gap: 12rpx;
  margin-top: 12rpx;
}

.post-submit-action-row .unfamiliar-btn,
.explanation-toggle-btn {
  flex: 1 1 0;
  width: auto;
  min-width: 0;
  min-height: 96rpx;
  margin-top: 0;
}

.explanation-toggle-btn {
  padding: 0 24rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 26rpx;
  background: var(--gyt-primary);
  color: #ffffff;
  font-size: 27rpx;
  font-weight: 900;
  line-height: 1.25;
  text-align: center;
  box-shadow: 0 10rpx 22rpx var(--gyt-primary-shadow);
}

.action-row .unfamiliar-btn {
  margin-top: 0;
}

.prev-btn[disabled] {
  border: 0;
  background: #f2f4f7;
  color: #98a2b3;
  box-shadow: none;
}

.action-row {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
  margin-top: 18rpx;
}

.review-nav-row {
  display: flex;
  gap: 16rpx;
}

.next-btn {
  flex: 1;
  width: 100%;
  min-height: 102rpx;
  margin: 0;
  padding: 0 20rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 0;
  border-radius: 28rpx;
  background: #172033;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 900;
  line-height: 1.25;
  text-align: center;
}

.next-btn.done {
  background: #0f8b5f;
}

.next-btn.secondary {
  background: #475569;
}

.next-btn.outline {
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  border: 0;
  box-shadow: none;
}

.next-btn[disabled] {
  background: #c6d3f2;
  color: #ffffff;
  box-shadow: none;
}

.back-tags {
  margin-top: 20rpx;
}

.answer-sheet-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 80;
  background: rgba(15, 23, 42, 0.38);
  display: flex;
  align-items: flex-end;
}

.answer-sheet {
  width: 100%;
  max-height: 78vh;
  padding: 18rpx 32rpx calc(env(safe-area-inset-bottom) + 28rpx);
  border-radius: 40rpx 40rpx 0 0;
  background: #ffffff;
  box-shadow: 0 -18rpx 48rpx rgba(15, 23, 42, 0.18);
  overflow-y: auto;
}

.sheet-handle {
  width: 76rpx;
  height: 8rpx;
  margin: 0 auto 22rpx;
  border-radius: 999rpx;
  background: #d7deea;
}

.answer-sheet-head {
  position: relative;
  min-height: 64rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.answer-sheet-head .sheet-title {
  width: 100%;
}

.sheet-title {
  text-align: center;
  color: #172033;
  font-size: 32rpx;
  font-weight: 900;
}

.sheet-section {
  margin-top: 26rpx;
}

.sheet-section-head {
  display: flex;
  justify-content: space-between;
  color: #344054;
  font-size: 24rpx;
  font-weight: 900;
}

.sheet-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14rpx;
}

.sheet-number {
  min-height: 70rpx;
  margin: 0;
  padding: 0;
  border: 2rpx solid #e4eaf4;
  border-radius: 20rpx;
  background: #f2f5fa;
  color: #8a95a8;
  font-size: 25rpx;
  font-weight: 900;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sheet-number.answered {
  background: var(--gyt-primary);
  border-color: var(--gyt-primary);
  color: #ffffff;
}

.sheet-number.current {
  background: #ffffff;
  border-color: var(--gyt-primary);
  color: var(--gyt-primary);
  box-shadow: 0 10rpx 24rpx var(--gyt-primary-shadow);
}

.explanation-sheet-mask {
  position: fixed;
  inset: 0;
  z-index: 240;
  display: flex;
  align-items: flex-end;
  background: rgba(15, 23, 42, 0.36);
  animation: explanation-mask-in 180ms ease-out both;
}

.explanation-sheet {
  width: 100%;
  height: 70vh;
  height: 70dvh;
  min-height: 56vh;
  min-height: 56dvh;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  border-radius: 40rpx 40rpx 0 0;
  background: #ffffff;
  box-shadow: 0 -18rpx 48rpx rgba(15, 23, 42, 0.22);
  overflow: hidden;
  animation: explanation-sheet-up 260ms cubic-bezier(0.22, 0.8, 0.24, 1) both;
}

.explanation-sheet-handle {
  flex: 0 0 auto;
  margin-top: 18rpx;
  margin-bottom: 14rpx;
}

.explanation-sheet-head {
  flex: 0 0 auto;
  min-height: 64rpx;
  padding: 0 32rpx 16rpx;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2rpx solid #edf1f7;
}

.explanation-sheet-title {
  color: #172033;
  font-size: 30rpx;
  font-weight: 900;
}

.sheet-cancel-btn,
.explanation-sheet-close {
  min-width: 92rpx;
  min-height: 58rpx;
  margin: 0;
  padding: 0 16rpx;
  border: 0;
  border-radius: 18rpx;
  background: var(--gyt-primary-soft);
  color: var(--gyt-primary);
  font-size: 24rpx;
  font-weight: 800;
  line-height: 58rpx;
}

.sheet-cancel-btn {
  position: absolute;
  top: 50%;
  right: 0;
  transform: translateY(-50%);
}

.sheet-cancel-btn::after,
.explanation-sheet-close::after {
  border: 0;
}

.explanation-sheet-body {
  flex: 1 1 auto;
  min-height: 0;
  box-sizing: border-box;
  padding: 28rpx 32rpx calc(env(safe-area-inset-bottom) + 36rpx);
}

.explanation-sheet-body :deep(.panel) {
  padding: 0;
  border: 0;
  border-radius: 0;
  box-shadow: none;
}

.grading-feedback-mask {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  z-index: 320;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: calc(env(safe-area-inset-top) + 36rpx) 48rpx calc(env(safe-area-inset-bottom) + 36rpx);
  background: rgba(248, 250, 255, 0.88);
  -webkit-backdrop-filter: blur(10px);
  backdrop-filter: blur(10px);
  animation: grading-feedback-in 160ms ease-out both;
}

.grading-feedback-card {
  width: 100%;
  max-width: 520rpx;
  box-sizing: border-box;
  padding: 38rpx 36rpx 34rpx;
  border: 2rpx solid rgba(215, 229, 255, 0.9);
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: 0 20rpx 54rpx rgba(39, 86, 170, 0.12);
  text-align: center;
  transform: translateY(-72rpx);
}

.grading-feedback-title,
.grading-feedback-copy {
  display: block;
  font-weight: 400;
}

.grading-feedback-title {
  color: #33445f;
  font-size: 30rpx;
  line-height: 1.5;
}

.grading-feedback-progress {
  width: 100%;
  height: 10rpx;
  margin: 28rpx 0 22rpx;
  overflow: hidden;
  border-radius: 999rpx;
  background: var(--gyt-primary-soft, #eaf2ff);
}

.grading-feedback-progress-bar {
  width: 42%;
  height: 100%;
  border-radius: inherit;
  background: var(--gyt-primary-gradient, linear-gradient(90deg, #3478f6, #70a5ff));
  box-shadow: 0 0 16rpx var(--gyt-primary-shadow, rgba(52, 120, 246, 0.2));
  will-change: transform;
  animation: grading-progress-slide 1.05s cubic-bezier(0.4, 0, 0.2, 1) infinite;
}

.grading-feedback-copy {
  color: #7a899d;
  font-size: 24rpx;
  line-height: 1.5;
}

@keyframes grading-feedback-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes grading-progress-slide {
  from { transform: translateX(-120%); }
  to { transform: translateX(340%); }
}

@keyframes explanation-mask-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes explanation-sheet-up {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}
</style>
