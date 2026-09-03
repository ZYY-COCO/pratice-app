import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import {
  getMentorConsultationOrderUiState,
  mergeMentorConsultationStopState
} from '../src/utils/mentorConsultationState.mjs'

const NOW = Date.parse('2026-09-03T12:00:00Z')
const baseOrder = {
  id: 'order-state-contract',
  orderStatus: 'in_progress',
  startedAt: '2026-09-03T11:30:00Z',
  serviceEndsAt: '2026-09-03T12:30:00Z',
  consultationWindowMinutes: 60,
  serverClockOffsetMs: 0
}

function state(overrides = {}, viewerRole = 'mentor') {
  return getMentorConsultationOrderUiState(
    { ...baseOrder, ...overrides },
    { viewerRole, now: NOW }
  )
}

assert.deepEqual(
  { phase: state().phase, action: state().action, label: state().actionLabel },
  { phase: 'in_progress', action: 'enter', label: '进入咨询' }
)
assert.deepEqual(
  {
    phase: state({ applicantCompletionConfirmedAt: '2026-09-03T11:45:00Z' }).phase,
    action: state({ applicantCompletionConfirmedAt: '2026-09-03T11:45:00Z' }).action,
    label: state({ applicantCompletionConfirmedAt: '2026-09-03T11:45:00Z' }).actionLabel
  },
  { phase: 'awaiting_viewer_confirmation', action: 'history', label: '查看并处理' }
)
assert.deepEqual(
  {
    phase: state({ mentorCompletionConfirmedAt: '2026-09-03T11:45:00Z' }).phase,
    action: state({ mentorCompletionConfirmedAt: '2026-09-03T11:45:00Z' }).action,
    label: state({ mentorCompletionConfirmedAt: '2026-09-03T11:45:00Z' }).actionLabel
  },
  { phase: 'viewer_confirmed', action: 'history', label: '查看结束状态' }
)
assert.equal(state({ serviceEndsAt: '2026-09-03T12:00:00Z' }).phase, 'ending')
assert.equal(state({ serviceEndsAt: '2026-09-03T12:00:00Z' }).actionLabel, '查看聊天记录')
assert.equal(state({
  serviceEndsAt: '2026-09-03T12:00:00Z',
  autoCompletionBlockedByDispute: true
}).phase, 'platform_processing')
assert.equal(state({
  serviceEndsAt: '2026-09-03T12:00:00Z',
  autoCompletionBlockedByDispute: true
}).actionLabel, '查看聊天记录')
assert.equal(state({ orderStatus: 'completed' }).actionLabel, '查看聊天记录')
assert.equal(state({ orderStatus: 'accepted' }).action, 'start')
assert.equal(state({ orderStatus: 'booked' }).action, 'start')
assert.equal(state({ orderStatus: 'rejected', startedAt: '' }).action, 'none')
assert.equal(state({ orderStatus: 'cancelled' }).action, 'history')
assert.equal(state({
  serviceEndsAt: '',
  startedAt: '',
  acceptedAt: '2026-09-03T10:00:00Z'
}).phase, 'ending')
assert.equal(state({
  serviceEndsAt: '2026-09-03T12:10:00Z',
  serverClockOffsetMs: 15 * 60 * 1000
}).phase, 'ending')

const stoppedOrderCases = [
  { applicantCompletionConfirmedAt: '2026-09-03T11:45:00Z' },
  { mentorCompletionConfirmedAt: '2026-09-03T11:45:00Z' },
  {
    applicantCompletionConfirmedAt: '2026-09-03T11:45:00Z',
    mentorCompletionConfirmedAt: '2026-09-03T11:46:00Z'
  },
  { serviceEndsAt: '2026-09-03T12:00:00Z' },
  {
    serviceEndsAt: '2026-09-03T12:00:00Z',
    autoCompletionBlockedByDispute: true
  },
  { orderStatus: 'completed' }
]

for (const viewerRole of ['mentor', 'applicant']) {
  for (const overrides of stoppedOrderCases) {
    const result = state(overrides, viewerRole)
    assert.equal(result.isLiveChat, false)
    assert.notEqual(result.actionLabel, '进入咨询')
  }
}

const snakeCaseState = getMentorConsultationOrderUiState({
  order_status: 'in_progress',
  started_at: '2026-09-03T11:30:00Z',
  service_ends_at: '2026-09-03T12:30:00Z',
  applicant_completion_confirmed_at: '2026-09-03T11:45:00Z'
}, { viewerRole: 'mentor', now: NOW })
assert.equal(snakeCaseState.phase, 'awaiting_viewer_confirmation')
assert.equal(snakeCaseState.canOpenChat, true)
assert.equal(snakeCaseState.isLiveChat, false)

const locallyStoppedOrder = mergeMentorConsultationStopState(baseOrder, {
  ...baseOrder,
  applicantCompletionConfirmedAt: '2026-09-03T11:45:00Z'
})
assert.equal(state(locallyStoppedOrder).isLiveChat, false)
assert.equal(locallyStoppedOrder.applicantCompletionConfirmedAt, '2026-09-03T11:45:00Z')

const staleActiveOrder = mergeMentorConsultationStopState(
  { ...baseOrder },
  { ...baseOrder, orderStatus: 'completed', endedAt: '2026-09-03T11:50:00Z' }
)
const terminalOrderAfterStaleRead = mergeMentorConsultationStopState(
  { ...baseOrder },
  staleActiveOrder
)
assert.equal(terminalOrderAfterStaleRead.orderStatus, 'completed')
assert.equal(terminalOrderAfterStaleRead.endedAt, '2026-09-03T11:50:00Z')
assert.equal(state(terminalOrderAfterStaleRead).isLiveChat, false)

const resolvedDisputeOrder = mergeMentorConsultationStopState(
  { ...baseOrder, autoCompletionBlockedByDispute: false },
  { ...baseOrder, autoCompletionBlockedByDispute: true }
)
assert.equal(resolvedDisputeOrder.autoCompletionBlockedByDispute, false)

const crossOrderEvidence = mergeMentorConsultationStopState(
  baseOrder,
  { ...baseOrder, id: 'another-order', orderStatus: 'completed' }
)
assert.equal(crossOrderEvidence, baseOrder)

const entryBindings = [
  [
    '../src/pages-sub-consultation/consultation/mentor-apply.vue',
    'getOrderActionLabel(order)',
    'syncVisibleMentorOrderStates',
    'syncMentorOrderFromDraft',
    'isCurrentMentorOrderRead'
  ],
  [
    '../src/pages-sub-consultation/consultation/my-consultations.vue',
    'getOrderChatActionLabel(order)',
    'syncVisibleOrderStates',
    'syncOrderFromDraft',
    'isCurrentOrderRead'
  ],
  [
    '../src/pages-sub-consultation/consultation/mentor-waiting.vue',
    'currentOrderUiState.actionLabel',
    'shouldPollOrder',
    'syncOrderFromDraft',
    'requestedRevision !== orderStateRevision'
  ]
]

for (const [relativePath, binding, syncMarker, draftMarker, staleReadGuard] of entryBindings) {
  const source = readFileSync(new URL(relativePath, import.meta.url), 'utf8')
  assert.match(source, /getMentorConsultationOrderUiState/)
  assert.ok(source.includes(binding), `${relativePath} must render the shared action label`)
  assert.ok(source.includes(syncMarker), `${relativePath} must keep visible order state synchronized`)
  assert.ok(source.includes(draftMarker), `${relativePath} must restore the latest cross-page order snapshot`)
  assert.ok(source.includes(staleReadGuard), `${relativePath} must reject stale order responses`)
}

const mentorInfoSource = readFileSync(
  new URL('../src/pages-sub-consultation/consultation/mentor-info.vue', import.meta.url),
  'utf8'
)
assert.match(mentorInfoSource, /getMentorConsultationOrderUiState/)
assert.ok(mentorInfoSource.includes('mentorOrderClock.value'))
assert.ok(mentorInfoSource.includes('syncMentorOrderCounts'))
assert.ok(mentorInfoSource.includes('isCurrentMentorInfoRead'))

const mentorChatSource = readFileSync(
  new URL('../src/pages-sub-consultation/consultation/mentor-chat.vue', import.meta.url),
  'utf8'
)
assert.ok(mentorChatSource.includes('currentOrderSnapshot.value = normalizeMentorConsultationOrder'))
assert.ok(mentorChatSource.includes('mergeMentorConsultationStopState(incomingOrder, currentOrderSnapshot.value)'))

console.log('Mentor consultation order state audit passed.')
