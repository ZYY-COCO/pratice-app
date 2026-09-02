<template>
  <view class="mentor-application-page" :class="{ 'is-compact': compact }">
    <view v-if="!compact && activeMailbox === 'applications'" class="summary-grid">
      <view class="summary-card"><text>全部申请</text><strong>{{ applicationCount }}</strong><small>已收到的前辈申请</small></view>
      <view class="summary-card pending"><text>待审核</text><strong>{{ pendingCount }}</strong><small>等待管理员处理</small></view>
      <view class="summary-card approved"><text>已通过</text><strong>{{ approvedCount }}</strong><small>已建立前辈档案</small></view>
      <view class="summary-card rejected"><text>未通过</text><strong>{{ rejectedCount }}</strong><small>已完成审核反馈</small></view>
    </view>

    <view v-if="activeMailbox === 'applications'" class="application-workspace">
      <view class="toolbar"><view class="search"><text>⌕</text><input v-model.trim="filters.keyword" placeholder="搜索申请人、院校或专业" @input="handleSearch" /><button v-if="filters.keyword" @tap="clearSearch">×</button></view><AdminSelect class="status-select" :options="statusOptions.map((item) => item.label)" :value-index="statusIndex" aria-label="申请状态" @change="selectStatus" /><button class="refresh-button" :disabled="loading" @tap="refresh">{{ loading ? '刷新中…' : '刷新' }}</button><button v-if="showMailboxSwitch" class="mailbox-button" @tap="openReportMailbox">举报信箱</button></view>

      <view class="table-wrap"><view class="table">
        <view class="grid table-head"><view>申请人</view><view>申请信息</view><view>申请留言</view><view>证明材料</view><view>提交时间</view><view>状态</view><view>操作</view></view>
        <view v-if="loading" class="table-state">正在加载前辈申请…</view>
        <view v-else-if="loadError" class="table-state error"><text>前辈申请加载失败，请检查网络和后台权限。</text><button @tap="refresh">重新加载</button></view>
        <view v-else-if="applications.length === 0" class="table-state">当前筛选下没有前辈申请</view>
        <view v-for="item in applications" v-else :key="item.id" class="grid row" @tap="openApplication(item)">
          <view class="applicant"><view class="avatar">{{ item.legal_name?.slice(0, 1) || '前' }}</view><view><strong>{{ item.legal_name || '未填写姓名' }}</strong><text>申请成为前辈</text></view></view>
          <view><strong>{{ item.school }}</strong><text>{{ item.major }} · {{ item.admission_year }}级</text><text class="consultation-request" :class="{ 'is-verification-only': !isConsultationEnabled(item) }">{{ consultationServiceText(item) }}</text></view>
          <view class="message">{{ item.bio || (isConsultationEnabled(item) ? '未填写申请留言' : '仅申请前辈认证，暂无咨询服务说明') }}</view>
          <view><text class="document-count">{{ item.document_count || 0 }} 份材料</text></view>
          <view>{{ formatDateTime(item.created_at) }}</view>
          <view><text class="status" :class="item.application_status">{{ statusText(item.application_status) }}</text></view>
          <view class="application-actions">
            <button
              v-if="item.application_status === 'approved'"
              class="qualification-revoke-button"
              :disabled="revoking"
              @tap.stop="openQualificationRevocationDialog(item)"
            >取消资格</button>
            <button class="open-button" :disabled="revoking" @tap.stop="openApplication(item)">查看</button>
          </view>
        </view>
      </view></view>

      <view class="mentor-pagination">
        <view class="mentor-pagination-info">共 {{ applicationCount }} 条，每页 {{ applicationPageSize }} 条</view>
        <view class="mentor-pagination-actions">
          <button :disabled="applicationPage <= 1 || loading" @tap="changeApplicationPage(applicationPage - 1)">‹</button>
          <view class="mentor-page-current">{{ applicationPage }}</view>
          <view class="mentor-page-total">/ {{ applicationTotalPages }}</view>
          <button :disabled="applicationPage >= applicationTotalPages || loading" @tap="changeApplicationPage(applicationPage + 1)">›</button>
        </view>
      </view>
    </view>

    <view v-if="detailVisible" class="backdrop" @tap="closeApplication"><view class="detail" @tap.stop>
      <view class="detail-header"><view><text>MENTOR APPLICATION</text><strong>前辈申请详情</strong></view><button class="admin-modal-close" :disabled="saving" @tap="closeApplication">×</button></view>
      <view v-if="detailLoading" class="table-state">正在读取申请详情…</view>
      <scroll-view v-else-if="detail?.application" scroll-y class="detail-scroll"><view class="detail-content">
        <view class="applicant-card"><view class="avatar large">{{ detail.application.legal_name?.slice(0, 1) || '前' }}</view><view><strong>{{ detail.applicant?.nickname || detail.application.legal_name }}</strong><text>{{ detail.applicant?.email || detail.applicant?.phone || shortId(detail.application.applicant_user_id) }}</text></view><text class="status" :class="detail.application.application_status">{{ statusText(detail.application.application_status) }}</text></view>
        <view class="application-fields"><view><text>真实姓名</text><strong>{{ detail.application.legal_name }}</strong></view><view><text>录取院校</text><strong>{{ detail.application.school }}</strong></view><view><text>录取专业</text><strong>{{ detail.application.major }}</strong></view><view><text>电话号码</text><strong>{{ detail.application.phone || '历史申请未填写' }}</strong></view><view><text>入学年份</text><strong>{{ detail.application.admission_year }} 年</strong></view><view><text>毕业年份</text><strong>{{ detail.application.graduation_year ? `${detail.application.graduation_year} 年` : '未填写' }}</strong></view><view><text>考试类别</text><strong>{{ examTypeText(detail.application.exam_type) }}</strong></view><view><text>初试成绩</text><strong>{{ applicationScoreText(detail.application) }}</strong></view><view><text>咨询服务</text><strong>{{ consultationServiceText(detail.application) }}</strong></view><view><text>咨询价格</text><strong>{{ isConsultationEnabled(detail.application) ? `¥${formatPrice(detail.application.price)} / 次` : '未申请开通' }}</strong></view></view>
        <view class="detail-heading">擅长领域</view><view v-if="detail.application.skills?.length" class="skill-list"><text v-for="skill in detail.application.skills" :key="skill">{{ skill }}</text></view><view v-else class="empty">{{ isConsultationEnabled(detail.application) ? '申请人未填写咨询擅长领域' : '本次仅申请前辈认证，未申请开通咨询服务' }}</view>
        <view class="detail-heading">申请留言</view><view class="bio">{{ detail.application.bio || (isConsultationEnabled(detail.application) ? '申请人未填写申请留言。' : '本次仅申请前辈认证，未填写咨询服务说明。') }}</view>
        <view class="detail-heading">证明材料</view><view v-if="detail.documents?.length" class="documents"><view v-for="document in detail.documents" :key="document.id" class="document"><view class="document-preview" role="button" tabindex="0" :aria-label="`查看大图：${document.file_name || '证明材料'}`" @tap.stop="previewDocuments(document, detail.documents)" @keyup.enter.stop="previewDocuments(document, detail.documents)"><image :src="document.file_url" mode="aspectFill" /><view class="document-preview-cue" aria-hidden="true"><image src="/static/admin-icons/admin-search.svg" mode="aspectFit" /></view></view><view><strong>{{ document.file_name }}</strong><text>{{ documentTypeText(document.document_type) }} · {{ formatDateTime(document.created_at) }}</text></view></view></view><view v-else class="empty">该申请暂未上传证明材料</view>
        <view v-if="detail.application.application_status === 'pending'" class="review"><view class="detail-heading">通过备注（选填）</view><textarea v-model.trim="reviewNote" maxlength="1000" placeholder="可填写认证通过后的补充说明" /><view class="review-actions"><button class="reject-button" :disabled="saving" @tap="openRejectDialog">驳回申请</button><button class="approve-button" :disabled="saving" @tap="decideApplication('approve')">{{ saving && pendingDecision === 'approve' ? '处理中…' : '通过申请' }}</button></view></view>
        <view v-else-if="detail.application.admin_note" class="admin-note"><text>审核备注</text><strong>{{ detail.application.admin_note }}</strong></view>
      </view></scroll-view>
    </view></view>

    <view v-if="approvalDialogVisible" class="approval-dialog-backdrop" @tap="closeApprovalDialog">
      <view class="approval-dialog" role="dialog" aria-modal="true" aria-label="确认通过前辈申请" @tap.stop>
        <strong>通过这份前辈申请？</strong>
        <text>通过后将建立前辈档案，并按申请内容开放对应的用户端能力。</text>
        <view v-if="approvalDecisionError" class="approval-dialog-error" role="alert">{{ approvalDecisionError }}</view>
        <view class="approval-dialog-actions">
          <button class="approval-dialog-cancel" :disabled="saving" @tap="closeApprovalDialog">取消</button>
          <button class="approval-dialog-confirm" :disabled="saving" @tap="submitApprovalDecision">{{ saving && pendingDecision === 'approve' ? '处理中…' : '确认通过' }}</button>
        </view>
      </view>
    </view>

    <view v-if="rejectDialogVisible" class="reject-dialog-backdrop" @tap="closeRejectDialog">
      <view class="reject-dialog" role="dialog" aria-modal="true" aria-label="填写驳回理由" @tap.stop>
        <view class="reject-dialog-header">
          <view><text>REJECTION REASON</text><strong>填写驳回理由</strong></view>
          <button class="admin-modal-close reject-dialog-close" :disabled="saving" aria-label="关闭驳回理由浮窗" @tap="closeRejectDialog">×</button>
        </view>
        <view class="reject-dialog-body">
          <view class="reject-dialog-copy">审核说明会发送给申请人，并在其重新申请时展示。请写明需要补充或修改的内容。</view>
          <view class="reject-reason-label"><strong>驳回理由 <text>必填</text></strong><text>{{ rejectReason.length }} / 1000</text></view>
          <textarea
            v-model="rejectReason"
            :focus="rejectDialogVisible"
            :disabled="saving"
            :class="{ 'has-error': rejectReasonError }"
            :aria-invalid="rejectReasonError ? 'true' : 'false'"
            maxlength="1000"
            placeholder="例如：录取证明信息不完整，请补充包含姓名和院校信息的清晰材料。"
            @input="clearRejectReasonError"
          />
          <view class="reject-reason-helper" :class="{ error: rejectReasonError }">{{ rejectReasonError || '请填写 5–1000 个字，说明具体原因和修改要求。' }}</view>
        </view>
        <view class="reject-dialog-actions">
          <button class="reject-dialog-cancel" :disabled="saving" @tap="closeRejectDialog">取消</button>
          <button class="reject-dialog-confirm" :disabled="saving" @tap="submitRejectDecision">{{ saving && pendingDecision === 'reject' ? '提交中…' : '确认驳回' }}</button>
        </view>
      </view>
    </view>

    <view v-if="revocationDialogVisible" class="reject-dialog-backdrop" @tap="closeQualificationRevocationDialog">
      <view class="reject-dialog qualification-revocation-dialog" role="dialog" aria-modal="true" aria-label="取消前辈资格" @tap.stop>
        <view class="reject-dialog-header">
          <view><text>REVOKE QUALIFICATION</text><strong>取消前辈资格</strong></view>
          <button class="admin-modal-close reject-dialog-close" :disabled="revoking" aria-label="关闭取消资格浮窗" @tap="closeQualificationRevocationDialog">×</button>
        </view>
        <view class="reject-dialog-body">
          <view class="reject-dialog-copy">取消后，该前辈将立即停止公开展示和新增接单；历史申请、审核记录及已有咨询订单会继续保留。</view>
          <view class="reject-reason-label"><strong>取消原因 <text>必填</text></strong><text>{{ revocationReason.length }} / 1000</text></view>
          <textarea
            v-model="revocationReason"
            :focus="revocationDialogVisible"
            :disabled="revoking"
            :class="{ 'has-error': revocationReasonError }"
            :aria-invalid="revocationReasonError ? 'true' : 'false'"
            maxlength="1000"
            placeholder="例如：认证材料经复核存在失实信息，现取消前辈资格。"
            @input="clearRevocationReasonError"
          />
          <view class="reject-reason-helper" :class="{ error: revocationReasonError }">{{ revocationReasonError || '请填写 5–1000 个字，说明取消资格的具体依据。' }}</view>
        </view>
        <view class="reject-dialog-actions">
          <button class="reject-dialog-cancel" :disabled="revoking" @tap="closeQualificationRevocationDialog">取消</button>
          <button class="reject-dialog-confirm" :disabled="revoking" @tap="submitQualificationRevocation">{{ revoking ? '处理中…' : '确认取消资格' }}</button>
        </view>
      </view>
    </view>

    <view v-if="activeMailbox === 'reports'" class="report-mailbox-page">
      <view v-if="!compact" class="summary-grid report-summary-grid">
        <view class="summary-card report-total"><text>全部举报</text><strong>{{ reportCount }}</strong><small>来自咨询双方的举报</small></view>
        <view class="summary-card pending"><text>待处理</text><strong>{{ pendingReportCount }}</strong><small>等待管理员核实</small></view>
        <view class="summary-card reviewing"><text>处理中</text><strong>{{ reviewingReportCount }}</strong><small>正在跟进处理</small></view>
        <view class="summary-card resolved"><text>已结案</text><strong>{{ closedReportCount }}</strong><small>已处理或已驳回</small></view>
      </view>

      <view class="application-workspace report-workspace">
        <view class="toolbar"><view class="search"><text>⌕</text><input v-model.trim="reportFilters.keyword" placeholder="搜索举报类型或举报说明" @input="handleSearch" /><button v-if="reportFilters.keyword" @tap="clearSearch">×</button></view><AdminSelect class="status-select" :options="reportStatusOptions.map((item) => item.label)" :value-index="reportStatusIndex" aria-label="举报处理状态" @change="selectReportStatus" /><AdminSelect class="report-target-select" :options="reportTargetOptions.map((item) => item.label)" :value-index="reportTargetIndex" aria-label="被举报对象" @change="selectReportTarget" /><AdminSelect class="report-target-select" :options="reportSlaOptions.map((item) => item.label)" :value-index="reportSlaIndex" aria-label="首响时限" @change="selectReportSla" /><AdminSelect class="report-target-select" :options="reportPriorityFilterOptions.map((item) => item.label)" :value-index="reportPriorityFilterIndex" aria-label="问题优先级" @change="selectReportPriorityFilter" /><button class="refresh-button" :disabled="reportLoading" @tap="refresh">{{ reportLoading ? '刷新中…' : '刷新' }}</button><button v-if="showMailboxSwitch" class="mailbox-button active" @tap="openApplicationMailbox">前辈申请</button></view>

        <view class="table-wrap"><view class="table report-table">
          <view class="report-grid table-head"><view>举报人</view><view>被举报对象</view><view>举报类型</view><view>举报说明</view><view>双方凭证</view><view>处理时限</view><view>举报时间</view><view>状态</view><view>操作</view></view>
          <view v-if="reportLoading" class="table-state">正在读取举报信…</view>
          <view v-else-if="reportLoadError" class="table-state error"><text>举报信加载失败，请检查网络和后台权限。</text><button @tap="refresh">重新加载</button></view>
          <view v-else-if="reports.length === 0" class="table-state">当前筛选下没有举报信</view>
          <view v-for="item in reports" v-else :key="item.id" class="report-grid row report-row" @tap="openReport(item)">
            <view class="applicant"><view class="avatar report-avatar">{{ reportPersonInitial(item.reporter) }}</view><view><strong>{{ item.reporter?.display_name || '举报用户' }}</strong><text>{{ reportRoleText(item.reporter_role) }}</text></view></view>
            <view><strong>{{ item.target?.display_name || '被举报对象' }}</strong><text>{{ reportTargetMeta(item.target) }}</text></view>
            <view><text class="report-type">{{ item.issue_type }}</text></view>
            <view class="message">{{ item.content }}</view>
            <view><text class="document-count">反馈 {{ item.reporter_evidence_count || 0 }} · 回应 {{ item.respondent_evidence_count || 0 }}</text></view>
            <view><text class="report-sla" :class="item.sla_status">{{ reportSlaLabel(item) }}</text><small>{{ casePriorityText(item.priority) }}</small></view>
            <view>{{ formatDateTime(item.created_at) }}</view>
            <view><text class="status report-status" :class="item.status">{{ reportStatusText(item.status) }}</text></view>
            <view><button class="open-button" @tap.stop="openReport(item)">查看</button></view>
          </view>
        </view></view>

        <view class="mentor-pagination">
          <view class="mentor-pagination-info">共 {{ reportCount }} 条，每页 {{ reportPageSize }} 条</view>
          <view class="mentor-pagination-actions"><button :disabled="reportPage <= 1 || reportLoading" @tap="changeReportPage(reportPage - 1)">‹</button><view class="mentor-page-current">{{ reportPage }}</view><view class="mentor-page-total">/ {{ reportTotalPages }}</view><button :disabled="reportPage >= reportTotalPages || reportLoading" @tap="changeReportPage(reportPage + 1)">›</button></view>
        </view>
      </view>

      <view v-if="reportDetailVisible" class="backdrop" @tap="closeReport"><view class="detail report-detail" @tap.stop>
        <view class="detail-header"><view><text>CONSULTATION REPORT</text><strong>举报详情</strong></view><button class="admin-modal-close" :disabled="reportSaving" @tap="closeReport">×</button></view>
        <view v-if="reportDetailLoading" class="table-state">正在读取举报详情…</view>
        <scroll-view v-else-if="reportDetail?.report" scroll-y class="detail-scroll"><view class="detail-content">
          <view class="report-party-grid"><view><text>举报人</text><strong>{{ reportDetail.report.reporter?.display_name || '举报用户' }}</strong><small>{{ reportRoleText(reportDetail.report.reporter_role) }}</small></view><view><text>被举报对象</text><strong>{{ reportDetail.report.target?.display_name || '被举报对象' }}</strong><small>{{ reportTargetMeta(reportDetail.report.target) }}</small></view></view>
          <view class="application-fields report-fields"><view><text>举报类型</text><strong>{{ reportDetail.report.issue_type }}</strong></view><view><text>关联订单</text><strong>{{ reportDetail.report.order_no || '—' }}</strong></view><view><text>举报时间</text><strong>{{ formatDateTime(reportDetail.report.created_at) }}</strong></view><view><text>首次响应时限</text><strong>{{ formatDateTime(reportDetail.report.first_response_due_at) }}</strong></view><view><text>首次响应</text><strong>{{ reportDetail.report.first_response_at ? formatDateTime(reportDetail.report.first_response_at) : reportSlaLabel(reportDetail.report) }}</strong></view><view><text>当前优先级</text><strong>{{ casePriorityText(reportDetail.report.priority) }}</strong></view><view><text>回应时间</text><strong>{{ reportDetail.report.responded_at ? formatDateTime(reportDetail.report.responded_at) : '未回应' }}</strong></view><view><text>处理时间</text><strong>{{ reportDetail.report.handled_at ? formatDateTime(reportDetail.report.handled_at) : '待处理' }}</strong></view></view>
          <view class="detail-heading">举报说明</view><view class="report-content">{{ reportDetail.report.content }}</view>
          <view class="detail-heading">举报方凭证</view><view v-if="reportEvidence(reportDetail.evidence, 'reporter').length" class="documents report-documents"><view v-for="evidence in reportEvidence(reportDetail.evidence, 'reporter')" :key="evidence.id" class="document"><image :src="evidence.file_url" mode="aspectFill" /><view><strong>{{ evidence.file_name }}</strong><text>举报方 · {{ formatDateTime(evidence.created_at) }}</text></view></view></view><view v-else class="empty">举报方未上传凭证</view>
          <view class="detail-heading">被举报方回应</view><view v-if="reportDetail.report.respondent_content" class="report-content response-content">{{ reportDetail.report.respondent_content }}</view><view v-else class="empty">被举报方暂未提交说明</view>
          <view class="detail-heading">被举报方凭证</view><view v-if="reportEvidence(reportDetail.evidence, 'respondent').length" class="documents report-documents"><view v-for="evidence in reportEvidence(reportDetail.evidence, 'respondent')" :key="evidence.id" class="document"><image :src="evidence.file_url" mode="aspectFill" /><view><strong>{{ evidence.file_name }}</strong><text>被举报方 · {{ formatDateTime(evidence.created_at) }}</text></view></view></view><view v-else class="empty">被举报方未上传凭证</view>
          <template v-if="reportDetail.review"><view class="detail-heading">关联服务评价</view><view class="review-context-card" :class="{ hidden: !reportDetail.review.is_published }"><view class="application-fields report-fields"><view><text>评分</text><strong>{{ reportDetail.review.rating }} / 5</strong></view><view><text>当前公开状态</text><strong>{{ reportDetail.review.is_published ? '公开展示中' : '已下架' }}</strong></view><view><text>评价人</text><strong>{{ reportDetail.review.reviewer_display_name || '匿名用户' }}</strong></view><view><text>提交时间</text><strong>{{ formatDateTime(reportDetail.review.created_at) }}</strong></view></view><view v-if="reportDetail.review.tags?.length" class="skill-list review-tags"><text v-for="tag in reportDetail.review.tags" :key="tag">{{ tag }}</text></view><view class="report-content" :class="{ 'review-hidden': !reportDetail.review.is_published }">{{ reportDetail.review.content || '评价人未填写文字反馈' }}</view></view></template>
          <view class="detail-heading">关联聊天记录</view><view v-if="reportDetail.messages?.length" class="report-message-list"><view v-for="message in reportDetail.messages" :key="message.id || `${message.created_at}-${message.content}`" class="report-message" :class="message.sender_role"><text>{{ reportRoleText(message.sender_role) }}</text><strong>{{ reportMessageText(message) }}</strong><small>{{ formatDateTime(message.created_at) }}</small></view></view><view v-else class="empty">暂无可核实的聊天记录</view>
          <view class="detail-heading">订单事件</view><view v-if="reportDetail.events?.length" class="report-message-list"><view v-for="event in reportDetail.events" :key="event.id || `${event.created_at}-${event.event_type}`" class="report-message event"><text>{{ reportEventLabel(event) }}</text><strong>{{ reportEventDetail(event) }}</strong><small>{{ formatDateTime(event.created_at) }}</small></view></view><view v-else class="empty">暂无订单事件记录</view>
          <view class="report-review"><view class="detail-heading">处理举报</view><view class="report-review-grid report-resolution-grid"><view class="form-field"><view class="form-label">处理状态</view><AdminSelect class="form-admin-select" :options="reportStatusOptions.slice(1).map((item) => item.label)" :value-index="reportDetailStatusIndex" aria-label="举报处理状态" @change="selectReportDetailStatus" /></view><view class="form-field"><view class="form-label">问题优先级</view><AdminSelect class="form-admin-select" :options="reportPriorityOptions.map((item) => item.label)" :value-index="reportDetailPriorityIndex" aria-label="问题优先级" @change="selectReportDetailPriority" /></view><view class="form-field"><view class="form-label">订单裁决</view><AdminSelect class="form-admin-select" :options="reportResolutionOptions.map((item) => item.label)" :value-index="reportDetailResolutionIndex" aria-label="订单裁决" @change="selectReportResolution" /></view><view v-if="reportResolution === 'refund_partial'" class="form-field"><view class="form-label">部分退款金额（元）</view><input v-model.trim="reportPartialRefundAmount" type="digit" placeholder="需小于订单总金额" /></view><view class="form-field report-note-field"><view class="form-label">管理员备注（结案必填）</view><textarea v-model.trim="reportAdminNote" maxlength="1000" placeholder="填写处理结论或跟进说明；双方会在咨询记录中看到此结果。" /></view></view><view class="review-actions"><button class="approve-button" :disabled="reportSaving" @tap="saveReportStatus">{{ reportSaving ? '保存中…' : '保存处理结果' }}</button></view></view>
        </view></scroll-view>
      </view></view>
    </view>
  </view>
</template>

<script setup>
import { computed, onBeforeUnmount, reactive, ref, watch } from 'vue'
import {
  decideAdminMentorVerificationApplication,
  fetchAdminMentorConsultationReport,
  fetchAdminMentorConsultationReports,
  fetchAdminMentorVerificationApplication,
  fetchAdminMentorVerificationApplications,
  revokeAdminMentorQualification,
  updateAdminMentorConsultationReportStatus
} from '../api/admin'
import AdminSelect from './AdminSelect.vue'

const props = defineProps({
  preview: Boolean,
  compact: Boolean,
  mailbox: { type: String, default: 'applications' },
  showMailboxSwitch: { type: Boolean, default: true }
})
const activeMailbox = ref(normalizeMailbox(props.mailbox))
const applications = ref([])
const applicationCount = ref(0)
const applicationPage = ref(1)
const applicationPageSize = 20
const loading = ref(false)
const loadError = ref(false)
const detailVisible = ref(false)
const detailLoading = ref(false)
const detail = ref(null)
const saving = ref(false)
const pendingDecision = ref('')
const reviewNote = ref('')
const approvalDialogVisible = ref(false)
const approvalDecisionError = ref('')
const rejectDialogVisible = ref(false)
const rejectReason = ref('')
const rejectReasonError = ref('')
const revocationDialogVisible = ref(false)
const revocationTarget = ref(null)
const revocationReason = ref('')
const revocationReasonError = ref('')
const revoking = ref(false)
const filters = reactive({ keyword: '', application_status: '' })
const reports = ref([])
const reportCount = ref(0)
const reportPage = ref(1)
const reportPageSize = 20
const reportLoading = ref(false)
const reportLoadError = ref(false)
const reportDetailVisible = ref(false)
const reportDetailLoading = ref(false)
const reportDetail = ref(null)
const reportSaving = ref(false)
const reportAdminNote = ref('')
const reportDetailStatus = ref('pending')
const reportDetailPriority = ref('normal')
const reportResolution = ref('none')
const reportPartialRefundAmount = ref('')
const reportFilters = reactive({ keyword: '', status: '', target_role: '', priority: '', sla_state: '' })
let searchTimer = null

const statusOptions = [{ label: '全部申请状态', value: '' }, { label: '待审核', value: 'pending' }, { label: '已通过', value: 'approved' }, { label: '未通过', value: 'rejected' }, { label: '已取消资格', value: 'revoked' }]
const reportStatusOptions = [{ label: '全部处理状态', value: '' }, { label: '待处理', value: 'pending' }, { label: '处理中', value: 'reviewing' }, { label: '已处理', value: 'resolved' }, { label: '已驳回', value: 'dismissed' }]
const reportSlaOptions = [{ label: '全部首响时限', value: '' }, { label: '已超时', value: 'overdue' }, { label: '临近超时', value: 'due_soon' }, { label: '已升级', value: 'escalated' }]
const reportPriorityFilterOptions = [{ label: '全部优先级', value: '' }, { label: '普通', value: 'normal' }, { label: '高', value: 'high' }, { label: '紧急', value: 'urgent' }]
const reportPriorityOptions = [{ label: '普通', value: 'normal' }, { label: '高', value: 'high' }, { label: '紧急', value: 'urgent' }]
const reportResolutionOptions = [{ label: '不执行订单裁决', value: 'none' }, { label: '建议继续服务', value: 'continue_service' }, { label: '全额退款并结束', value: 'refund_full' }, { label: '部分退款并结束', value: 'refund_partial' }, { label: '平台结束服务', value: 'close_service' }, { label: '提醒相关参与方', value: 'warn_participant' }, { label: '下架关联服务评价', value: 'hide_review' }, { label: '恢复关联服务评价', value: 'restore_review' }]
const reportTargetOptions = [{ label: '全部被举报对象', value: '' }, { label: '认证前辈', value: 'mentor' }, { label: '咨询用户', value: 'applicant' }]
const statusIndex = computed(() => Math.max(0, statusOptions.findIndex((item) => item.value === filters.application_status)))
const reportStatusIndex = computed(() => Math.max(0, reportStatusOptions.findIndex((item) => item.value === reportFilters.status)))
const reportTargetIndex = computed(() => Math.max(0, reportTargetOptions.findIndex((item) => item.value === reportFilters.target_role)))
const reportSlaIndex = computed(() => Math.max(0, reportSlaOptions.findIndex((item) => item.value === reportFilters.sla_state)))
const reportPriorityFilterIndex = computed(() => Math.max(0, reportPriorityFilterOptions.findIndex((item) => item.value === reportFilters.priority)))
const reportDetailStatusIndex = computed(() => Math.max(0, reportStatusOptions.slice(1).findIndex((item) => item.value === reportDetailStatus.value)))
const reportDetailPriorityIndex = computed(() => Math.max(0, reportPriorityOptions.findIndex((item) => item.value === reportDetailPriority.value)))
const reportDetailResolutionIndex = computed(() => Math.max(0, reportResolutionOptions.findIndex((item) => item.value === reportResolution.value)))
const applicationTotalPages = computed(() => Math.max(1, Math.ceil(applicationCount.value / applicationPageSize)))
const reportTotalPages = computed(() => Math.max(1, Math.ceil(reportCount.value / reportPageSize)))
const pendingCount = computed(() => applications.value.filter((item) => item.application_status === 'pending').length)
const approvedCount = computed(() => applications.value.filter((item) => item.application_status === 'approved').length)
const rejectedCount = computed(() => applications.value.filter((item) => item.application_status === 'rejected').length)
const pendingReportCount = computed(() => reports.value.filter((item) => item.status === 'pending').length)
const reviewingReportCount = computed(() => reports.value.filter((item) => item.status === 'reviewing').length)
const closedReportCount = computed(() => reports.value.filter((item) => ['resolved', 'dismissed'].includes(item.status)).length)

refresh()
onBeforeUnmount(() => { if (searchTimer) clearTimeout(searchTimer) })
defineExpose({ refresh })

watch(() => props.mailbox, (mailbox) => {
  const nextMailbox = normalizeMailbox(mailbox)
  if (nextMailbox === activeMailbox.value) return
  activeMailbox.value = nextMailbox
  if (nextMailbox === 'reports') reportPage.value = 1
  else applicationPage.value = 1
  refresh()
})

async function refresh() {
  if (activeMailbox.value === 'reports') return refreshReports()
  return refreshApplications()
}

async function refreshApplications() {
  loading.value = true
  loadError.value = false
  try {
    const response = props.preview ? buildPreviewApplicationPage() : await fetchAdminMentorVerificationApplications({
      ...filters,
      limit: applicationPageSize,
      offset: (applicationPage.value - 1) * applicationPageSize
    })
    applications.value = response?.items || []
    applicationCount.value = Number(response?.count || 0)
    if (applicationCount.value > 0 && applications.value.length === 0 && applicationPage.value > applicationTotalPages.value) {
      applicationPage.value = applicationTotalPages.value
      await refresh()
      return
    }
  } catch (error) {
    applications.value = []
    applicationCount.value = 0
    loadError.value = true
  } finally { loading.value = false }
}

async function refreshReports() {
  reportLoading.value = true
  reportLoadError.value = false
  try {
    const response = props.preview ? buildPreviewReportPage() : await fetchAdminMentorConsultationReports({
      ...reportFilters,
      limit: reportPageSize,
      offset: (reportPage.value - 1) * reportPageSize
    })
    reports.value = response?.items || []
    reportCount.value = Number(response?.count || 0)
    if (reportCount.value > 0 && reports.value.length === 0 && reportPage.value > reportTotalPages.value) {
      reportPage.value = reportTotalPages.value
      await refreshReports()
      return
    }
  } catch (error) {
    reports.value = []
    reportCount.value = 0
    reportLoadError.value = true
  } finally { reportLoading.value = false }
}

function applyApplicationFilters() { applicationPage.value = 1; refresh() }
function applyReportFilters() { reportPage.value = 1; refresh() }
function handleSearch() { if (searchTimer) clearTimeout(searchTimer); searchTimer = setTimeout(() => (activeMailbox.value === 'reports' ? applyReportFilters() : applyApplicationFilters()), 360) }
function clearSearch() { if (activeMailbox.value === 'reports') { reportFilters.keyword = ''; applyReportFilters(); return }; filters.keyword = ''; applyApplicationFilters() }
function selectStatus(event) { filters.application_status = statusOptions[Number(event?.detail?.value || 0)]?.value || ''; applyApplicationFilters() }
function changeApplicationPage(page) { const next = Math.max(1, Math.min(applicationTotalPages.value, Number(page) || 1)); if (next !== applicationPage.value) { applicationPage.value = next; refresh() } }
function selectReportStatus(event) { reportFilters.status = reportStatusOptions[Number(event?.detail?.value || 0)]?.value || ''; applyReportFilters() }
function selectReportTarget(event) { reportFilters.target_role = reportTargetOptions[Number(event?.detail?.value || 0)]?.value || ''; applyReportFilters() }
function selectReportSla(event) { reportFilters.sla_state = reportSlaOptions[Number(event?.detail?.value || 0)]?.value || ''; applyReportFilters() }
function selectReportPriorityFilter(event) { reportFilters.priority = reportPriorityFilterOptions[Number(event?.detail?.value || 0)]?.value || ''; applyReportFilters() }
function changeReportPage(page) { const next = Math.max(1, Math.min(reportTotalPages.value, Number(page) || 1)); if (next !== reportPage.value) { reportPage.value = next; refresh() } }

function openReportMailbox() {
  detailVisible.value = false
  activeMailbox.value = 'reports'
  reportPage.value = 1
  refresh()
}

function openApplicationMailbox() {
  reportDetailVisible.value = false
  activeMailbox.value = 'applications'
  applicationPage.value = 1
  refresh()
}

function normalizeMailbox(value) {
  return value === 'reports' ? 'reports' : 'applications'
}

async function openApplication(item) {
  if (!item?.id || detailLoading.value) return
  detailVisible.value = true; detailLoading.value = true; detail.value = null; reviewNote.value = ''; resetApprovalDialog(); resetRejectDialog()
  try {
    detail.value = props.preview ? previewApplicationDetail(item) : await fetchAdminMentorVerificationApplication(item.id)
    reviewNote.value = detail.value?.application?.admin_note || ''
  } catch (error) {
    uni.showToast({ title: error?.detail || '申请详情加载失败', icon: 'none' })
    detailVisible.value = false
  } finally { detailLoading.value = false }
}

function closeApplication() {
  if (saving.value) return
  detailVisible.value = false
  detail.value = null
  reviewNote.value = ''
  resetApprovalDialog()
  resetRejectDialog()
}

function decideApplication(decision) {
  const application = detail.value?.application
  if (!application?.id || saving.value) return
  if (decision !== 'approve') {
    openRejectDialog()
    return
  }
  openApprovalDialog()
}

function openApprovalDialog() {
  const application = detail.value?.application
  if (!application?.id || application.application_status !== 'pending' || saving.value) return
  approvalDecisionError.value = ''
  approvalDialogVisible.value = true
}

function closeApprovalDialog() {
  if (saving.value) return
  resetApprovalDialog()
}

function resetApprovalDialog() {
  approvalDialogVisible.value = false
  approvalDecisionError.value = ''
}

async function submitApprovalDecision() {
  const application = detail.value?.application
  if (!application?.id || application.application_status !== 'pending' || saving.value) return
  approvalDecisionError.value = ''
  const saved = await persistApplicationDecision('approve', reviewNote.value)
  if (saved) resetApprovalDialog()
}

function openRejectDialog() {
  const application = detail.value?.application
  if (!application?.id || application.application_status !== 'pending' || saving.value) return
  rejectReason.value = ''
  rejectReasonError.value = ''
  rejectDialogVisible.value = true
}

function closeRejectDialog() {
  if (saving.value) return
  resetRejectDialog()
}

function resetRejectDialog() {
  rejectDialogVisible.value = false
  rejectReason.value = ''
  rejectReasonError.value = ''
}

function clearRejectReasonError() {
  if (rejectReasonError.value && rejectReason.value.trim().length >= 5) rejectReasonError.value = ''
}

async function submitRejectDecision() {
  if (saving.value) return
  const reason = rejectReason.value.trim()
  if (!reason) {
    rejectReasonError.value = '请填写驳回理由。'
    return
  }
  if (reason.length < 5) {
    rejectReasonError.value = '驳回理由至少填写 5 个字。'
    return
  }
  const saved = await persistApplicationDecision('reject', reason)
  if (saved) resetRejectDialog()
}

async function persistApplicationDecision(decision, adminNote) {
  const application = detail.value?.application
  if (!application?.id || saving.value) return false
  const normalizedNote = String(adminNote || '').trim()
  const approving = decision === 'approve'
  saving.value = true; pendingDecision.value = decision
  try {
    const updated = props.preview ? { ...application, application_status: approving ? 'approved' : 'rejected', admin_note: normalizedNote || null, reviewed_at: new Date().toISOString() } : await decideAdminMentorVerificationApplication(application.id, { decision, admin_note: normalizedNote || null })
    applications.value = applications.value.map((item) => item.id === updated.id ? { ...item, ...updated } : item)
    detail.value = { ...detail.value, application: { ...detail.value.application, ...updated } }
    uni.showToast({ title: approving ? '申请已通过' : '申请已驳回', icon: 'success' })
    return true
  } catch (error) {
    const errorMessage = String(error?.detail || error?.message || '审核处理失败')
    if (approving && approvalDialogVisible.value) approvalDecisionError.value = errorMessage
    else uni.showToast({ title: errorMessage, icon: 'none' })
    return false
  } finally {
    saving.value = false
    pendingDecision.value = ''
  }
}

function openQualificationRevocationDialog(application) {
  if (!application?.id || application.application_status !== 'approved' || revoking.value) return
  revocationTarget.value = application
  revocationReason.value = ''
  revocationReasonError.value = ''
  revocationDialogVisible.value = true
}

function closeQualificationRevocationDialog() {
  if (revoking.value) return
  resetQualificationRevocationDialog()
}

function resetQualificationRevocationDialog() {
  revocationDialogVisible.value = false
  revocationTarget.value = null
  revocationReason.value = ''
  revocationReasonError.value = ''
}

function clearRevocationReasonError() {
  if (revocationReasonError.value && revocationReason.value.trim().length >= 5) revocationReasonError.value = ''
}

async function submitQualificationRevocation() {
  const application = revocationTarget.value
  if (!application?.id || revoking.value) return
  const reason = revocationReason.value.trim()
  if (!reason) {
    revocationReasonError.value = '请填写取消资格的原因。'
    return
  }
  if (reason.length < 5) {
    revocationReasonError.value = '取消原因至少填写 5 个字。'
    return
  }

  revoking.value = true
  try {
    const updated = props.preview
      ? { ...application, application_status: 'revoked', revocation_reason: reason, revoked_at: new Date().toISOString() }
      : await revokeAdminMentorQualification(application.id, { reason })
    applications.value = applications.value.map((item) => item.id === updated.id ? { ...item, ...updated } : item)
    if (detail.value?.application?.id === updated.id) {
      detail.value = { ...detail.value, application: { ...detail.value.application, ...updated } }
    }
    uni.showToast({ title: '前辈资格已取消', icon: 'success' })
    resetQualificationRevocationDialog()
    await refreshApplications()
  } catch (error) {
    uni.showToast({ title: error?.detail || '取消资格失败', icon: 'none' })
  } finally {
    revoking.value = false
  }
}

async function openReport(item) {
  if (!item?.id || reportDetailLoading.value) return
  reportDetailVisible.value = true
  reportDetailLoading.value = true
  reportDetail.value = null
  reportAdminNote.value = ''
  try {
    reportDetail.value = props.preview ? previewReportDetail(item) : await fetchAdminMentorConsultationReport(item.id)
    reportDetailStatus.value = reportDetail.value?.report?.status || 'pending'
    reportDetailPriority.value = reportDetail.value?.report?.priority || 'normal'
    reportResolution.value = reportDetail.value?.report?.resolution || 'none'
    reportPartialRefundAmount.value = reportResolution.value === 'refund_partial' ? String(reportDetail.value?.report?.refund_amount || '') : ''
    reportAdminNote.value = reportDetail.value?.report?.admin_note || ''
  } catch (error) {
    uni.showToast({ title: error?.detail || '举报详情加载失败', icon: 'none' })
    reportDetailVisible.value = false
  } finally { reportDetailLoading.value = false }
}

function closeReport() {
  if (reportSaving.value) return
  reportDetailVisible.value = false
  reportDetail.value = null
  reportAdminNote.value = ''
  reportDetailPriority.value = 'normal'
  reportResolution.value = 'none'
  reportPartialRefundAmount.value = ''
}

function selectReportDetailStatus(event) {
  reportDetailStatus.value = reportStatusOptions.slice(1)[Number(event?.detail?.value || 0)]?.value || 'pending'
}

function selectReportDetailPriority(event) {
  reportDetailPriority.value = reportPriorityOptions[Number(event?.detail?.value || 0)]?.value || 'normal'
}

function selectReportResolution(event) {
  reportResolution.value = reportResolutionOptions[Number(event?.detail?.value || 0)]?.value || 'none'
  if (reportResolution.value !== 'refund_partial') reportPartialRefundAmount.value = ''
}

async function saveReportStatus() {
  const report = reportDetail.value?.report
  if (!report?.id || reportSaving.value) return
  if (['resolved', 'dismissed'].includes(reportDetailStatus.value) && !reportAdminNote.value.trim()) {
    uni.showToast({ title: '结案时请填写处理结论', icon: 'none' })
    return
  }
  if (reportResolution.value !== 'none' && reportDetailStatus.value !== 'resolved') {
    uni.showToast({ title: '执行订单裁决时请将举报标记为已处理', icon: 'none' })
    return
  }
  const orderStatus = String(reportDetail.value?.order?.order_status || '')
  const terminalOrder = ['completed', 'refunded', 'cancelled', 'rejected', 'timeout'].includes(orderStatus)
  if (['hide_review', 'restore_review'].includes(reportResolution.value) && !reportDetail.value?.review) {
    uni.showToast({ title: '该订单没有可处置的服务评价', icon: 'none' })
    return
  }
  if (reportResolution.value === 'continue_service' && terminalOrder) {
    uni.showToast({ title: '该订单已结束，不能再建议继续服务', icon: 'none' })
    return
  }
  const partialRefundAmount = Number(reportPartialRefundAmount.value)
  const orderAmount = Number(reportDetail.value?.order?.price || 0)
  if (reportResolution.value === 'refund_partial' && (!Number.isFinite(partialRefundAmount) || partialRefundAmount <= 0 || partialRefundAmount >= orderAmount)) {
    uni.showToast({ title: '部分退款金额需大于 0 且小于订单总金额', icon: 'none' })
    return
  }
  const confirmed = await confirmDecision(
    '保存举报处理结果？',
    '处理状态和管理员备注会写入举报信并保留处理记录。',
    '确认保存'
  )
  if (!confirmed) return
  reportSaving.value = true
  try {
    const updated = props.preview
      ? { ...report, status: reportDetailStatus.value, priority: reportDetailPriority.value, resolution: reportResolution.value, refund_amount: reportResolution.value === 'refund_partial' ? partialRefundAmount : report.refund_amount, admin_note: reportAdminNote.value || null, first_response_at: report.first_response_at || (reportDetailStatus.value === 'pending' ? null : new Date().toISOString()), handled_at: ['resolved', 'dismissed'].includes(reportDetailStatus.value) ? new Date().toISOString() : null }
      : await updateAdminMentorConsultationReportStatus(report.id, { status: reportDetailStatus.value, priority: reportDetailPriority.value, resolution: reportResolution.value, refund_amount: reportResolution.value === 'refund_partial' ? partialRefundAmount : 0, admin_note: reportAdminNote.value || null })
    reports.value = reports.value.map((item) => item.id === updated.id ? { ...item, ...updated } : item)
    reportDetail.value = { ...reportDetail.value, report: { ...report, ...updated } }
    uni.showToast({ title: '举报处理结果已保存', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.detail || '举报处理状态保存失败', icon: 'none' })
  } finally { reportSaving.value = false }
}

function confirmDecision(title, content, confirmText) { return new Promise((resolve) => uni.showModal({ title, content, confirmText, success: (result) => resolve(Boolean(result.confirm)) })) }
function buildPreviewApplicationPage() {
  const keyword = filters.keyword.trim().toLowerCase()
  const filtered = previewApplications().filter((item) => {
    if (filters.application_status && item.application_status !== filters.application_status) return false
    if (!keyword) return true
    return [item.legal_name, item.school, item.major].some((value) => String(value || '').toLowerCase().includes(keyword))
  })
  const offset = (applicationPage.value - 1) * applicationPageSize
  return { items: filtered.slice(offset, offset + applicationPageSize), count: filtered.length }
}
function previewApplications() { return [
  { id: 'preview-mentor-application-001', applicant_user_id: 'preview-user-001', legal_name: '陈同学', school: '暨南大学', major: '应用经济学', admission_year: 2025, graduation_year: 2027, exam_type: 'Z001', score: 110, consultation_enabled: true, skills: ['院校选择', '初试备考', '复试经验'], bio: '我已录取暨南大学应用经济学，希望帮助同样准备 Z001 的同学梳理院校选择和备考节奏。', price: 39, application_status: 'pending', document_count: 2, created_at: '2026-08-21T02:30:00Z' },
  { id: 'preview-mentor-application-002', applicant_user_id: 'preview-user-002', legal_name: '林同学', school: '中山大学', major: '金融学', admission_year: 2024, graduation_year: 2026, exam_type: 'Z002', score: 122, consultation_enabled: false, skills: [], bio: '', price: 0, application_status: 'approved', document_count: 1, created_at: '2026-08-18T09:20:00Z', admin_note: '认证材料核验通过。' },
  { id: 'preview-mentor-application-003', applicant_user_id: 'preview-user-003', legal_name: '周同学', school: '华南理工大学', major: '工商管理', admission_year: 2025, graduation_year: 2027, exam_type: 'application', score: null, consultation_enabled: true, skills: ['院校选择'], bio: '希望分享申请制项目的准备经历。', price: 39, application_status: 'rejected', document_count: 0, created_at: '2026-08-16T03:10:00Z', admin_note: '请补充录取证明后重新申请。' }
] }
function previewApplicationDetail(application) { return { application: { ...application }, applicant: { nickname: application.legal_name, email: 'mentor-applicant@example.com' }, documents: Array.from({ length: application.document_count || 0 }, (_, index) => ({ id: `preview-document-${index}`, file_url: '/static/ui-icons/circle-community.svg', file_name: index ? '学生证照片' : '录取通知书', document_type: index ? 'student_card' : 'admission_notice', created_at: application.created_at })) } }
function buildPreviewReportPage() {
  const keyword = reportFilters.keyword.trim().toLowerCase()
  const filtered = previewReports().filter((item) => {
    if (reportFilters.status && item.status !== reportFilters.status) return false
    if (reportFilters.target_role && item.target_role !== reportFilters.target_role) return false
    if (reportFilters.priority && item.priority !== reportFilters.priority) return false
    if (reportFilters.sla_state && (reportFilters.sla_state === 'escalated' ? !Number(item.escalation_level || 0) : item.sla_status !== reportFilters.sla_state)) return false
    if (!keyword) return true
    return [item.issue_type, item.content].some((value) => String(value || '').toLowerCase().includes(keyword))
  })
  const offset = (reportPage.value - 1) * reportPageSize
  return { items: filtered.slice(offset, offset + reportPageSize), count: filtered.length }
}
function previewReports() { return [
  { id: 'preview-consultation-report-001', order_id: 'preview-order-001', order_no: 'MC202608210001', reporter_role: 'applicant', target_role: 'mentor', issue_type: '服务态度与沟通问题', content: '咨询过程中多次出现不当表达，影响正常沟通体验，希望平台核实本次聊天记录。', status: 'pending', priority: 'urgent', escalation_level: 1, sla_status: 'overdue', first_response_due_at: '2026-08-22T10:20:00Z', created_at: '2026-08-21T10:20:00Z', reporter: { id: 'preview-user-001', role: 'applicant', display_name: '同学 A' }, target: { id: 'preview-mentor-001', role: 'mentor', display_name: '钟*宏', school: '暨南大学', major: '应用经济学' }, evidence_count: 2, reporter_evidence_count: 2, respondent_evidence_count: 0 },
  { id: 'preview-consultation-report-002', order_id: 'preview-order-002', order_no: 'MC202608180002', reporter_role: 'mentor', target_role: 'applicant', issue_type: '恶意评价或失实反馈', content: '咨询用户在评价中描述的事实与站内聊天记录不符，希望平台结合本次咨询全过程核实。', respondent_content: '评价内容来自个人实际感受，希望平台结合聊天记录核实。', responded_at: '2026-08-18T09:10:00Z', status: 'reviewing', priority: 'high', sla_status: 'responded', first_response_due_at: '2026-08-18T14:30:00Z', first_response_at: '2026-08-18T09:20:00Z', created_at: '2026-08-18T08:30:00Z', reporter: { id: 'preview-mentor-user-001', role: 'mentor', display_name: '林前辈' }, target: { id: 'preview-user-002', role: 'applicant', display_name: '同学 B' }, evidence_count: 2, reporter_evidence_count: 1, respondent_evidence_count: 1 },
  { id: 'preview-consultation-report-003', order_id: 'preview-order-003', order_no: 'MC202608150003', reporter_role: 'applicant', target_role: 'mentor', issue_type: '其他问题', content: '希望平台协助确认咨询收费与订单信息是否一致。', status: 'resolved', priority: 'normal', sla_status: 'closed', first_response_due_at: '2026-08-16T12:10:00Z', first_response_at: '2026-08-15T13:00:00Z', created_at: '2026-08-15T12:10:00Z', handled_at: '2026-08-16T03:00:00Z', reporter: { id: 'preview-user-003', role: 'applicant', display_name: '同学 C' }, target: { id: 'preview-mentor-002', role: 'mentor', display_name: '陈前辈', school: '中山大学', major: '金融学' }, evidence_count: 0, reporter_evidence_count: 0, respondent_evidence_count: 0 }
] }
function previewReportDetail(report) { return {
  report: { ...report, admin_note: report.status === 'resolved' ? '已核实订单信息并向双方说明处理结果。' : null },
  evidence: Array.from({ length: report.evidence_count || 0 }, (_, index) => ({ id: `preview-report-evidence-${index}`, file_name: `${index < (report.reporter_evidence_count || 0) ? '举报方' : '被举报方'}凭证 ${index + 1}`, file_url: '/static/ui-icons/report.svg', submitter_role: index < (report.reporter_evidence_count || 0) ? 'reporter' : 'respondent', created_at: report.created_at })),
  review: report.issue_type === '恶意评价或失实反馈' ? { id: 'preview-review-002', order_id: report.order_id, mentor_id: 'preview-mentor-001', reviewer_display_name: '匿名用户', rating: 1, tags: ['回复较慢'], content: '沟通体验不如预期，部分问题没有及时回应。', is_published: true, created_at: report.created_at } : null,
  order: { id: report.order_id, order_no: report.order_no },
  messages: [
    { id: 'preview-message-1', sender_role: 'applicant', message_type: 'text', content: '你好，想咨询一下备考安排。', created_at: report.created_at },
    { id: 'preview-message-2', sender_role: 'mentor', message_type: 'text', content: '好的，请先说明你的报考方向。', created_at: report.created_at }
  ],
  events: [
    { id: 'preview-event-1', event_type: 'consultation_report_created', actor_role: report.reporter_role, details: { issue_type: report.issue_type }, created_at: report.created_at },
    ...(report.responded_at ? [{ id: 'preview-event-2', event_type: 'consultation_report_responded', actor_role: report.target_role, details: {}, created_at: report.responded_at }] : [])
  ]
} }
function statusText(value) { return { pending: '待审核', approved: '已通过', rejected: '未通过', revoked: '已取消资格' }[value] || '待审核' }
function reportStatusText(value) { return { pending: '待处理', reviewing: '处理中', resolved: '已处理', dismissed: '已驳回' }[value] || '待处理' }
function casePriorityText(value) { return { normal: '普通', high: '高优先级', urgent: '紧急' }[value] || '普通' }
function reportSlaLabel(item = {}) { if (item.first_response_at) return '已首响'; if (item.sla_status === 'overdue') return Number(item.escalation_level || 0) > 0 ? '超时已升级' : '首响超时'; if (item.sla_status === 'due_soon') return '临近超时'; return item.first_response_due_at ? '等待首响' : '未设时限' }
function reportRoleText(value) { return value === 'mentor' ? '认证前辈' : '咨询用户' }
function reportTargetMeta(target) { return [target?.school, target?.major].filter(Boolean).join(' · ') || reportRoleText(target?.role) }
function reportPersonInitial(person) { return String(person?.display_name || '举').slice(0, 1) || '举' }
function reportMessageText(message) { if (message?.content) return message.content; return message?.message_type === 'image' ? '图片消息' : message?.message_type === 'voice' ? '语音消息' : '系统消息' }
function reportEvidence(evidence, role) { return (Array.isArray(evidence) ? evidence : []).filter((item) => (item?.submitter_role || 'reporter') === role) }
function reportEventText(event) { return { consultation_order_created: '创建咨询订单', consultation_payment_intent_created: '创建支付订单', consultation_mock_payment_recorded: '已记录历史模拟支付', consultation_demo_payment_recorded: '已记录测试支付', consultation_payment_confirmed: '支付回调确认成功', consultation_payment_failed: '支付回调确认失败', consultation_refund_requested: '已提交退款处理', consultation_refund_completed: '退款回调确认完成', consultation_refund_failed: '退款回调返回异常', mentor_order_decision: '前辈处理接单', consultation_started: '咨询已开始', completion_confirmed: '一方确认结束', consultation_completed: '双方确认完成', order_cancelled_by_applicant: '咨询用户取消订单', consultation_report_created: '提交问题反馈', consultation_report_responded: '被举报方提交说明', consultation_report_evidence_uploaded: '补充处理凭证', consultation_report_appeal_created: '提交复核申请', consultation_report_appeal_evidence_uploaded: '补充复核凭证', consultation_report_appeal_reviewing: '平台开始复核', consultation_report_reopened_after_appeal: '平台重新开启原案', consultation_report_appeal_resolved: '平台更新复核结果', consultation_report_resolved: '平台更新处理结果', consultation_review_hidden: '平台下架关联评价', consultation_review_restored: '平台恢复关联评价', order_timed_out: '订单超时自动取消', accepted_start_timed_out: '前辈接单后未开始，订单已取消', booking_no_show_timed_out: '预约未开始，订单已取消' }[event?.event_type] || '订单处理事件' }
function reportEventLabel(event) { return { consultation_report_acknowledged: '平台已受理问题反馈', consultation_report_sla_escalated: '问题反馈首响超时升级', consultation_report_priority_escalated: '问题反馈已调整优先级', consultation_report_appeal_sla_escalated: '复核首响超时升级', consultation_report_appeal_priority_escalated: '复核已调整优先级' }[event?.event_type] || reportEventText(event) }
function reportEventDetail(event) { const details = event?.details && typeof event.details === 'object' ? event.details : {}; if (event?.event_type === 'consultation_report_created') return details.issue_type ? `问题类型：${details.issue_type}` : '已关联本次咨询订单'; if (event?.event_type === 'consultation_report_evidence_uploaded') return details.submitter_role === 'respondent' ? '被举报方已补充凭证' : '举报方已补充凭证'; if (event?.event_type === 'consultation_report_reopened_after_appeal') return '原问题反馈已重新进入处理中'; if (event?.event_type === 'consultation_report_appeal_resolved') return details.decision === 'uphold' ? '平台维持原处理结论' : '平台已保存复核结果'; if (event?.event_type === 'consultation_review_hidden') return '关联服务评价已停止对外展示'; if (event?.event_type === 'consultation_review_restored') return '关联服务评价已恢复对外展示'; if (event?.event_type === 'consultation_report_resolved') return details.resolution ? `平台裁决：${details.resolution}` : '平台已保存处理结果'; return '已记录到本次订单的处理链路' }
function isConsultationEnabled(application = {}) { return application?.consultation_enabled !== false }
function consultationServiceText(application = {}) { return isConsultationEnabled(application) ? '申请开通咨询' : '仅申请前辈认证' }
function examTypeText(value) { return { Z001: 'Z001', Z002: 'Z002', application: '申请制' }[value] || value || '—' }
function applicationScoreText(application = {}) {
  if (application.exam_type === 'application') return '不适用（申请制）'
  return application.score === null || application.score === undefined || application.score === ''
    ? '未填写'
    : `${application.score} 分`
}
function documentTypeText(value) { return { admission_notice: '录取通知书', student_card: '学生证', other: '其他证明' }[value] || '证明材料' }
function previewDocuments(currentDocument, documents) {
  const urls = (Array.isArray(documents) ? documents : [])
    .map((item) => String(item?.file_url || '').trim())
    .filter(Boolean)
  const current = String(currentDocument?.file_url || '').trim()
  if (!current || !urls.length) return
  uni.previewImage({ current, urls })
}
function formatPrice(value) { const price = Number(value || 0); return Number.isInteger(price) ? price : price.toFixed(2) }
function shortId(value) { const id = String(value || ''); return id ? `${id.slice(0, 8)}…${id.slice(-4)}` : '—' }
function formatDateTime(value) { const date = new Date(value); return Number.isNaN(date.getTime()) ? '—' : new Intl.DateTimeFormat('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(date) }
</script>

<style scoped>
.mentor-application-page{color:#31465d}.summary-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}.summary-card{min-height:112px;padding:18px 20px;border:1px solid #e2eaee;border-top:3px solid #9aa9b8;border-radius:9px;background:#fff;box-shadow:0 8px 24px rgba(39,62,79,.04)}.summary-card text,.summary-card strong,.summary-card small{display:block}.summary-card text{color:#7d8d9e;font-size:11px;font-weight:700}.summary-card strong{margin-top:10px;color:#314a65;font-size:28px}.summary-card small{margin-top:7px;color:#9aa7b4;font-size:10px}.summary-card.pending{border-top-color:#dbaf55}.summary-card.approved{border-top-color:#57cdb7}.summary-card.rejected{border-top-color:#de9088}.application-workspace{margin-top:18px;border:1px solid #e0e8ec;border-radius:10px;background:#fff;overflow:hidden;box-shadow:0 10px 30px rgba(38,59,77,.04)}.heading{min-height:76px;padding:0 22px;display:flex;align-items:center;justify-content:space-between;gap:20px;border-bottom:1px solid #e9eef1}.title{font-size:15px;font-weight:800}.subtitle{margin-top:5px;color:#8c9aa8;font-size:10px}.refresh-button{height:36px;margin:0;padding:0 16px;border:1px solid #d7e3e6;border-radius:7px;background:#fff;color:#617286;font-size:10px;font-weight:750}.toolbar{padding:14px 18px;display:grid;grid-template-columns:minmax(260px,1fr) 170px;gap:10px;border-bottom:1px solid #edf1f3;background:#fbfcfd}.search{height:38px;padding:0 10px;display:flex;align-items:center;gap:8px;border:1px solid #dae4e8;border-radius:8px;background:#fff}.search>text{color:#91a0af}.search input{min-width:0;flex:1;height:36px;font-size:11px}.search button{width:26px;height:26px;margin:0;padding:0;border:0;background:transparent;color:#93a1af}.refresh-button::after,.search button::after,.open-button::after,.detail button::after{border:0}.table-wrap{overflow-x:auto}.table{min-width:1050px}.grid{display:grid;grid-template-columns:1.1fr 1.3fr 1.8fr .7fr .85fr .75fr 60px;align-items:center;gap:14px;padding:0 18px}.table-head{min-height:42px;color:#8796a4;background:#f7f9fa;font-size:10px;font-weight:800}.row{min-height:76px;border-top:1px solid #edf1f3;cursor:pointer;font-size:11px}.row:hover{background:#fbfefd}.row strong,.row text{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.row strong{color:#394f65;font-size:11px}.row>view:not(.applicant) text,.applicant text{margin-top:4px;color:#98a5b2;font-size:9px}.applicant{display:flex;align-items:center;gap:10px;min-width:0}.avatar{width:36px;height:36px;flex:0 0 36px;display:flex;align-items:center;justify-content:center;border-radius:50%;background:#e4f5f0;color:#278d77;font-size:13px;font-weight:900}.message{overflow:hidden;display:-webkit-box;color:#718297;font-size:10px;line-height:1.4;-webkit-box-orient:vertical;-webkit-line-clamp:2}.document-count,.status{display:inline-flex!important;margin:0!important;padding:5px 8px;border-radius:99px;font-size:9px!important;font-weight:800}.document-count{background:#eef5fc;color:#5880a6!important}.status.pending{background:#fff4df;color:#ae7a29}.status.approved{background:#e8f7f2;color:#238b75}.status.rejected{background:#fceceb;color:#b45f59}.open-button{height:30px;margin:0;padding:0 11px;border:0;border-radius:6px;background:#eef7f5;color:#278b78;font-size:10px;font-weight:800}.table-state{padding:54px 20px;color:#91a0ae;text-align:center;font-size:12px}.table-state.error{color:#ba6962}.table-state button{display:block;margin:12px auto 0;font-size:11px}.backdrop{position:fixed;z-index:6000;inset:0;padding:24px;display:flex;align-items:center;justify-content:center;background:rgba(24,39,55,.38);backdrop-filter:blur(4px)}.detail{width:min(760px,calc(100vw - 48px));height:min(760px,calc(100vh - 48px));display:flex;flex-direction:column;overflow:hidden;border:1px solid #dfe8eb;border-radius:12px;background:#fff;box-shadow:0 30px 90px rgba(26,42,58,.24)}.detail-header{padding:18px 22px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #e9eef1}.detail-header text,.detail-header strong{display:block}.detail-header text{color:#35a78f;font-size:9px;font-weight:850;letter-spacing:.12em}.detail-header strong{margin-top:5px;color:#30465d;font-size:17px}.detail-header button{width:34px;height:34px;margin:0;padding:0;border:0;border-radius:50%;background:#f2f5f7;color:#768695;font-size:20px}.detail-scroll{min-height:0;flex:1}.detail-content{padding:22px}.applicant-card{display:flex;align-items:center;gap:11px;padding-bottom:17px;border-bottom:1px solid #e8eef1}.avatar.large{width:46px;height:46px;flex-basis:46px;font-size:17px}.applicant-card strong,.applicant-card text{display:block}.applicant-card strong{color:#3b5269;font-size:13px}.applicant-card text{margin-top:5px;color:#98a6b4;font-size:10px}.applicant-card .status{margin-left:auto!important}.application-fields{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));margin-top:18px;border:1px solid #e4edef;border-radius:8px;overflow:hidden}.application-fields>view{min-height:62px;padding:12px 14px;display:flex;flex-direction:column;justify-content:center;border-top:1px solid #e7edf0;border-left:1px solid #e7edf0}.application-fields>view:nth-child(-n+2){border-top:0}.application-fields>view:nth-child(odd){border-left:0}.application-fields text{color:#98a7b6;font-size:10px}.application-fields strong{margin-top:5px;color:#40566c;font-size:11px}.detail-heading{margin:20px 0 9px;color:#40566c;font-size:12px;font-weight:800}.skill-list{display:flex;flex-wrap:wrap;gap:7px}.skill-list text{padding:6px 9px;border-radius:99px;background:#eaf7f3;color:#297f6e;font-size:10px;font-weight:750}.bio,.empty{padding:13px;border:1px solid #e3ebee;border-radius:8px;color:#708196;font-size:11px;line-height:1.6;background:#fbfcfd}.empty{border-style:dashed;text-align:center}.documents{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.document{min-width:0;overflow:hidden;border:1px solid #e1e9ec;border-radius:8px;background:#fff}.document image{width:100%;height:104px;background:#f4f8fb}.document>view{padding:9px}.document strong,.document text{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.document strong{color:#41566b;font-size:10px}.document text{margin-top:4px;color:#96a5b2;font-size:8px}.review{margin-top:20px;padding-top:1px;border-top:1px solid #e8eef1}.review textarea{box-sizing:border-box;width:100%;min-height:78px;padding:10px 11px;border:1px dashed #9fcfc4;border-radius:7px;color:#40566d;font-size:11px;line-height:1.5;background:#fbfefd}.review-actions{margin-top:12px;display:flex;justify-content:flex-end;gap:9px}.review-actions button{min-width:92px;height:34px;margin:0;border-radius:7px;font-size:10px;font-weight:800}.reject-button{border:1px solid #ecc8c3;background:#fff7f5;color:#b36258}.approve-button{border:0;background:#34b399;color:#fff}.admin-note{margin-top:20px;padding:12px 13px;border:1px solid #e1eaed;border-radius:8px;background:#fbfcfd}.admin-note text,.admin-note strong{display:block}.admin-note text{color:#93a1ae;font-size:9px}.admin-note strong{margin-top:5px;color:#52677b;font-size:11px;line-height:1.5}@media(max-width:1180px){.summary-grid{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:820px){.summary-grid,.toolbar,.application-fields{grid-template-columns:1fr}.detail{width:100%;height:calc(100vh - 28px)}.backdrop{padding:14px}.application-fields>view{border-left:0}.application-fields>view:nth-child(2){border-top:1px solid #e7edf0}.documents{grid-template-columns:1fr 1fr}.heading{align-items:flex-start;flex-direction:column;padding:16px 18px}.detail-content{padding:18px}.review-actions button{flex:1}}
.refresh-button,
.open-button,
.qualification-revoke-button,
.review-actions button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  line-height: 1;
  text-align: center;
}

.table {
  min-width: 1140px;
}

.grid {
  grid-template-columns: 1.1fr 1.3fr 1.8fr .7fr .85fr .75fr 150px;
}

.application-actions {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  gap: 8px;
}

.application-actions button {
  width: 68px;
  height: 30px;
  min-height: 30px;
  margin: 0;
  padding: 0;
  border-radius: 6px;
  font-size: 10px;
  font-weight: 800;
}

.qualification-revoke-button {
  border: 1px solid #edcbc7;
  background: #fff8f7;
  color: #b45f59;
}

.application-actions button:disabled {
  opacity: .58;
}

.application-actions button::after {
  border: 0;
}

.status.revoked {
  background: #f5eceb;
  color: #a35d58;
}

.row .consultation-request {
  color: #278b78;
  font-weight: 800;
}

.row .consultation-request.is-verification-only {
  color: #8b98a5;
}

.document-preview {
  position: relative;
  padding: 0 !important;
  overflow: hidden;
  cursor: zoom-in;
  outline: none;
}

.document-preview > image:first-child {
  display: block;
  transition: transform 160ms ease, filter 160ms ease;
}

.document-preview-cue {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 255, 255, .72);
  border-radius: 50%;
  background: rgba(30, 47, 64, .7);
  box-shadow: 0 4px 12px rgba(25, 42, 58, .18);
  opacity: 0;
  transform: translateY(-3px);
  transition: opacity 160ms ease, transform 160ms ease;
  pointer-events: none;
}

.document-preview-cue image {
  width: 14px;
  height: 14px;
  filter: brightness(0) invert(1);
}

.document-preview:hover > image:first-child,
.document-preview:focus-visible > image:first-child {
  transform: scale(1.025);
  filter: brightness(.86);
}

.document-preview:hover .document-preview-cue,
.document-preview:focus-visible .document-preview-cue {
  opacity: 1;
  transform: translateY(0);
}

.document-preview:focus-visible {
  box-shadow: inset 0 0 0 2px #34b399;
}

:global(#u-a-p > div) {
  z-index: 7000 !important;
}

.approval-dialog-backdrop {
  position: fixed;
  z-index: 7200;
  inset: 0;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  background: rgba(24, 39, 55, .48);
  backdrop-filter: blur(4px);
}

.approval-dialog {
  width: min(420px, calc(100vw - 48px));
  padding: 24px;
  box-sizing: border-box;
  border: 1px solid #dfe8eb;
  border-radius: 8px;
  background: #ffffff;
  box-shadow: 0 28px 80px rgba(26, 42, 58, .28);
  text-align: center;
}

.approval-dialog > strong,
.approval-dialog > text {
  display: block;
}

.approval-dialog > strong {
  color: #30465d;
  font-size: 17px;
  line-height: 1.45;
}

.approval-dialog > text {
  margin-top: 12px;
  color: #7d8d9e;
  font-size: 12px;
  line-height: 1.65;
}

.approval-dialog-error {
  margin-top: 14px;
  padding: 9px 11px;
  border: 1px solid #efd4d0;
  border-radius: 7px;
  color: #b45f59;
  background: #fff8f7;
  font-size: 11px;
  line-height: 1.55;
  overflow-wrap: anywhere;
}

.approval-dialog-actions {
  margin-top: 22px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.approval-dialog-actions button {
  width: 100%;
  height: 38px;
  min-height: 38px;
  margin: 0;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  border-radius: 7px;
  font-size: 11px;
  font-weight: 850;
  line-height: 1;
  text-align: center;
}

.approval-dialog-cancel {
  border: 1px solid #dfe7ea;
  color: #718194;
  background: #ffffff;
}

.approval-dialog-confirm {
  border: 1px solid #2da58b;
  color: #ffffff;
  background: #2da58b;
}

.approval-dialog-actions button:disabled {
  opacity: .6;
}

.approval-dialog-actions button::after {
  border: 0;
}

.reject-dialog-backdrop {
  position: fixed;
  z-index: 7200;
  inset: 0;
  padding: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(24, 39, 55, .52);
  backdrop-filter: blur(5px);
}

.reject-dialog {
  width: min(520px, calc(100vw - 48px));
  overflow: hidden;
  border: 1px solid #dfe8eb;
  border-radius: 10px;
  background: #ffffff;
  box-shadow: 0 32px 96px rgba(21, 35, 49, .32);
}

.reject-dialog-header {
  padding: 18px 20px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  border-bottom: 1px solid #e9eef1;
}

.reject-dialog-header text,
.reject-dialog-header strong {
  display: block;
}

.reject-dialog-header > view > text {
  color: #bc6a61;
  font-size: 9px;
  font-weight: 850;
  letter-spacing: .12em;
}

.reject-dialog-header strong {
  margin-top: 5px;
  color: #30465d;
  font-size: 17px;
}

.reject-dialog-close {
  width: 34px;
  height: 34px;
  min-height: 34px;
  margin: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex: 0 0 34px;
  border: 0;
  border-radius: 50%;
  background: #f2f5f7;
  color: #768695;
  font-size: 20px;
  line-height: 1;
}

.reject-dialog-body {
  padding: 20px;
}

.reject-dialog-copy {
  color: #718297;
  font-size: 12px;
  line-height: 1.65;
}

.reject-reason-label {
  margin-top: 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  color: #8796a4;
  font-size: 10px;
}

.reject-reason-label strong {
  color: #40566c;
  font-size: 12px;
}

.reject-reason-label strong text {
  display: inline;
  margin-left: 5px;
  color: #bd695f;
  font-size: 9px;
}

.reject-dialog textarea {
  box-sizing: border-box;
  width: 100%;
  min-height: 128px;
  margin-top: 9px;
  padding: 12px 13px;
  border: 1px solid #dce6e9;
  border-radius: 8px;
  background: #fbfcfd;
  color: #40566d;
  font-size: 12px;
  line-height: 1.65;
}

.reject-dialog textarea:focus {
  border-color: #65bba8;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(80, 180, 158, .1);
}

.reject-dialog textarea.has-error {
  border-color: #d98980;
  background: #fffafa;
}

.reject-reason-helper {
  min-height: 17px;
  margin-top: 7px;
  color: #98a6b3;
  font-size: 10px;
  line-height: 1.5;
}

.reject-reason-helper.error {
  color: #b65f56;
  font-weight: 750;
}

.reject-dialog-actions {
  padding: 14px 20px 18px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  border-top: 1px solid #edf1f3;
}

.reject-dialog-actions button {
  box-sizing: border-box;
  min-width: 104px;
  height: 38px;
  min-height: 38px;
  margin: 0;
  padding: 0 16px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 7px;
  font-size: 11px;
  line-height: 1;
  font-weight: 800;
}

.reject-dialog-cancel {
  border: 1px solid #dce5e8;
  background: #ffffff;
  color: #687b8e;
}

.reject-dialog-confirm {
  border: 1px solid #d48278;
  background: #c96f66;
  color: #ffffff;
}

.reject-dialog-actions button:disabled,
.reject-dialog-close:disabled {
  opacity: .58;
}

.reject-dialog-actions button::after,
.reject-dialog-close::after {
  border: 0;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
}

.toolbar .search {
  width: min(360px, 42vw);
  flex: 0 1 360px;
}

.toolbar .status-select {
  width: 170px;
  flex: 0 0 170px;
}

.toolbar .refresh-button {
  min-width: 76px;
  padding: 0 14px;
  flex: 0 0 auto;
}

.mentor-pagination {
  min-height: 58px;
  padding: 0 18px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  border-top: 1px solid #eaf0f2;
  box-sizing: border-box;
  background: #ffffff;
}

.mentor-pagination-info {
  color: #90a0af;
  font-size: 10px;
}

.mentor-pagination-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #9aa8b6;
  font-size: 10px;
}

.mentor-pagination-actions button,
.mentor-page-current {
  width: 34px;
  height: 34px;
  margin: 0;
  padding: 0;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #dfe8eb;
  border-radius: 7px;
  box-sizing: border-box;
  color: #718295;
  background: #ffffff;
  font-size: 16px;
  line-height: 1;
}

.mentor-page-current {
  border-color: #d6eee8;
  color: #268b78;
  background: #eaf8f4;
  font-size: 11px;
  font-weight: 800;
}

.mentor-pagination-actions button:disabled {
  color: #c4cdd5;
  background: #f8fafb;
}

.mentor-pagination-actions button::after {
  border: 0;
}

.detail-header button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
  line-height: 1;
  text-align: center;
}

.mentor-application-page {
  display: flex;
  min-height: calc(100vh - 158px);
  flex-direction: column;
}

.application-workspace {
  min-height: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
}

.application-workspace .table-wrap {
  min-height: 0;
  flex: 1;
}

.application-workspace .table {
  min-height: 100%;
}

@media (max-width: 820px) {
  .mentor-application-page {
    min-height: auto;
  }

  .toolbar {
    flex-wrap: wrap;
  }

  .toolbar .search {
    width: 100%;
    flex-basis: 100%;
  }

  .mentor-pagination {
    align-items: flex-start;
    flex-direction: column;
    justify-content: center;
    padding-top: 12px;
    padding-bottom: 12px;
  }
}

.mailbox-button {
  min-width: 82px;
  height: 36px;
  margin: 0;
  padding: 0 14px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #cfe4df;
  border-radius: 7px;
  box-sizing: border-box;
  color: #287d6d;
  background: #f3fbf8;
  font-size: 10px;
  font-weight: 800;
  line-height: 1;
}

.mailbox-button.active {
  border-color: #65c8b3;
  color: #166d5f;
  background: #dff6ef;
}

.mailbox-button::after {
  border: 0;
}

.report-mailbox-page {
  min-height: calc(100vh - 158px);
  display: flex;
  flex-direction: column;
}

.report-summary-grid .summary-card.reviewing {
  border-top-color: #7b9cc7;
}

.report-summary-grid .summary-card.resolved {
  border-top-color: #5fc2aa;
}

.report-workspace {
  flex: 1;
}

.report-target-select {
  width: 156px;
  flex: 0 0 156px;
}

.report-table {
  min-width: 1300px;
}

.report-grid {
  display: grid;
  grid-template-columns: 1.02fr 1.12fr .96fr 1.65fr .72fr .9fr .78fr .72fr 60px;
  align-items: center;
  gap: 14px;
  padding: 0 18px;
}

.report-type {
  display: inline-flex !important;
  max-width: 100%;
  margin: 0 !important;
  padding: 5px 8px;
  overflow: hidden;
  border-radius: 5px;
  box-sizing: border-box;
  color: #7d6a36 !important;
  font-size: 9px !important;
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
  background: #fff5df;
}

.report-avatar {
  color: #8a6651;
  background: #f8eee5;
}

.report-status.reviewing {
  color: #4d78a6;
  background: #eaf2fc;
}

.report-status.resolved {
  color: #238b75;
  background: #e8f7f2;
}

.report-status.dismissed {
  color: #8a7680;
  background: #f0eef1;
}

.report-sla {
  display: inline-flex !important;
  margin: 0 !important;
  padding: 5px 8px;
  border-radius: 99px;
  background: #eef4ff;
  color: #5279ad !important;
  font-size: 9px !important;
  font-weight: 800;
}

.report-sla.due_soon {
  background: #fff4df;
  color: #a7772c !important;
}

.report-sla.overdue {
  background: #fceceb;
  color: #b45f59 !important;
}

.report-sla.responded,
.report-sla.closed {
  background: #e8f7f2;
  color: #238b75 !important;
}

.report-grid small {
  display: block;
  margin-top: 4px;
  color: #98a5b2;
  font-size: 9px;
}

.report-party-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  margin-bottom: 18px;
  overflow: hidden;
  border: 1px solid #e4edef;
  border-radius: 8px;
}

.report-party-grid > view {
  min-width: 0;
  min-height: 74px;
  padding: 13px 14px;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.report-party-grid > view + view {
  border-left: 1px solid #e7edf0;
}

.report-party-grid text,
.report-party-grid small {
  color: #98a7b6;
  font-size: 10px;
}

.report-party-grid strong {
  margin-top: 5px;
  overflow: hidden;
  color: #40566c;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.report-party-grid small {
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.report-content {
  padding: 13px;
  border: 1px solid #e3ebee;
  border-radius: 8px;
  color: #52677b;
  font-size: 11px;
  line-height: 1.7;
  background: #fbfcfd;
  white-space: pre-wrap;
}

.review-context-card {
  padding: 13px;
  border: 1px solid #dcebe7;
  border-radius: 9px;
  background: #fbfefd;
}

.review-context-card.hidden {
  border-color: #eadfc9;
  background: #fffdf8;
}

.review-context-card .application-fields {
  margin-top: 0;
}

.review-tags {
  margin: 12px 0;
}

.report-content.review-hidden {
  color: #8d7751;
  background: #fffaf0;
}

.report-documents .document image {
  object-fit: cover;
}

.report-message-list {
  display: grid;
  gap: 8px;
}

.report-message {
  padding: 10px 12px;
  border: 1px solid #e4ecef;
  border-radius: 8px;
  background: #fbfcfd;
}

.report-message.mentor {
  border-color: #d7ebe5;
  background: #f2fbf8;
}

.report-message text,
.report-message strong,
.report-message small {
  display: block;
}

.report-message text,
.report-message small {
  color: #95a4b1;
  font-size: 9px;
}

.report-message strong {
  margin-top: 4px;
  color: #4b6177;
  font-size: 11px;
  font-weight: 650;
  line-height: 1.55;
  white-space: pre-wrap;
}

.report-message small {
  margin-top: 5px;
}

.report-review {
  margin-top: 20px;
  padding-top: 1px;
  border-top: 1px solid #e8eef1;
}

.report-review-grid {
  display: grid;
  grid-template-columns: minmax(150px, .62fr) minmax(0, 1.38fr);
  gap: 14px;
}

.report-resolution-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}

.report-resolution-grid .report-note-field {
  grid-column: 1 / -1;
}

.report-review textarea {
  width: 100%;
  min-height: 78px;
  margin-top: 8px;
  padding: 10px 11px;
  border: 1px dashed #9fcfc4;
  border-radius: 7px;
  box-sizing: border-box;
  color: #40566d;
  font-size: 11px;
  line-height: 1.5;
  background: #fbfefd;
}

.report-review input {
  width: 100%;
  height: 36px;
  margin-top: 8px;
  padding: 0 11px;
  border: 1px dashed #9fcfc4;
  border-radius: 7px;
  box-sizing: border-box;
  color: #40566d;
  font-size: 11px;
  background: #fbfefd;
}

.report-review textarea:focus {
  border-color: #58bba5;
  background: #ffffff;
  box-shadow: 0 0 0 3px rgba(80, 208, 180, .09);
}

@media (max-width: 820px) {
  .report-mailbox-page {
    min-height: auto;
  }

  .report-target-select {
    width: calc(50% - 5px);
    flex-basis: calc(50% - 5px);
  }

  .report-party-grid,
  .report-review-grid {
    grid-template-columns: 1fr;
  }

  .report-party-grid > view + view {
    border-top: 1px solid #e7edf0;
    border-left: 0;
  }
}
</style>

<style scoped>
.mentor-application-page.is-compact {
  min-height: 0;
}

.mentor-application-page.is-compact .application-workspace {
  margin-top: 0;
}
</style>
