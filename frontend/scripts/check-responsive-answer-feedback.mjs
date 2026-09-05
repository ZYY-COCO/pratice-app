import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'

const apiUrl = new URL('../src/api/answers.js', import.meta.url)
const practiceUrl = new URL('../src/pages/practice/index.vue', import.meta.url)
let apiSource = await readFile(apiUrl, 'utf8')
const practiceSource = await readFile(practiceUrl, 'utf8')

assert.doesNotMatch(
  apiSource,
  /['"]\/answers\/grade['"]/,
  'responsive feedback must not start a second durable submission request'
)
assert.equal(
  (apiSource.match(/['"]\/answers\/submit-responsive['"]/g) || []).length,
  1,
  'one tap must create exactly one responsive submission request'
)
assert.match(
  apiSource,
  /result\?\.persisted === true/,
  'the responsive API must accept only a durably persisted response'
)
assert.doesNotMatch(
  practiceSource,
  /正在提交\.\.\./,
  'ordinary practice must not show a waiting label between submit and feedback'
)
assert.equal(
  (practiceSource.match(/:class="\{ correct: item\.isCorrect === true, wrong: item\.isCorrect === false, pending: !hasResolvedAnswerGrade\(item\.isCorrect\) \}"/g) || []).length,
  2,
  'AI and ordinary result grids must color only resolved grades red or green'
)

const firstReviewStart = practiceSource.indexOf('const firstReviewIndex = computed')
const firstReviewEnd = practiceSource.indexOf('const summaryKicker', firstReviewStart)
assert.ok(firstReviewStart >= 0 && firstReviewEnd > firstReviewStart)
const firstReviewSource = practiceSource.slice(firstReviewStart, firstReviewEnd)
assert.match(
  firstReviewSource,
  /findIndex\(\(item\) => item\.isCorrect === false\)/,
  'review must open the first genuinely wrong answer before any pending item'
)

const pendingResultStart = practiceSource.indexOf('function buildPendingComprehensiveResult')
const pendingResultEnd = practiceSource.indexOf('function buildSkippedComprehensiveResult', pendingResultStart)
assert.ok(pendingResultStart >= 0 && pendingResultEnd > pendingResultStart)
assert.match(
  practiceSource.slice(pendingResultStart, pendingResultEnd),
  /isCorrect:\s*null/,
  'a missing authoritative grade must remain ungraded instead of being counted wrong'
)

const feedbackStart = practiceSource.indexOf('function applyResponsiveAnswerFeedback')
const feedbackEnd = practiceSource.indexOf('async function submitComprehensiveBatch', feedbackStart)
assert.ok(feedbackStart >= 0 && feedbackEnd > feedbackStart)
const feedbackSource = practiceSource.slice(feedbackStart, feedbackEnd)
assert.match(feedbackSource, /correctAnswer\.value = nextCorrectAnswer/)
assert.match(feedbackSource, /submitted\.value = true/)
assert.match(feedbackSource, /submitting\.value = false/)

const submissionStart = practiceSource.indexOf('async function submitAnswer()')
const submissionEnd = practiceSource.indexOf('function applyReviewAt', submissionStart)
assert.ok(submissionStart >= 0 && submissionEnd > submissionStart)
const submissionSource = practiceSource.slice(submissionStart, submissionEnd)
assert.match(submissionSource, /onGraded\(grade\)/)
assert.doesNotMatch(
  submissionSource,
  /onGraded\(grade\)[\s\S]{0,300}persisted:\s*false/,
  'authoritative grade feedback must not be labeled as unpersisted'
)
assert.match(
  submissionSource,
  /settleAdaptiveSubmission\([\s\S]*?\{ retryOnce: false, context: adaptiveContext \}/,
  'adaptive progress must settle through the queue instead of an immediate second foreground request'
)
const reviewStart = practiceSource.indexOf('function applyReviewAt')
const reviewEnd = practiceSource.indexOf('function openReviewQuestion', reviewStart)
assert.ok(reviewStart >= 0 && reviewEnd > reviewStart)
const reviewSource = practiceSource.slice(reviewStart, reviewEnd)
assert.match(reviewSource, /const graded = hasResolvedAnswerGrade\(result\.isCorrect\)/)
assert.match(
  reviewSource,
  /syncState === 'pending'[\s\S]*?result\.isCorrect \? '答对' : '答错'/,
  'a graded pending-sync answer must retain its true correct/wrong meaning in review'
)

const adaptiveSettlementStart = practiceSource.indexOf('function rememberAdaptiveAnswerSubmission')
const adaptiveSettlementEnd = practiceSource.indexOf('function queueAdaptiveNavigationIntent', adaptiveSettlementStart)
assert.ok(adaptiveSettlementStart >= 0 && adaptiveSettlementEnd > adaptiveSettlementStart)
const adaptiveSettlementSource = practiceSource.slice(adaptiveSettlementStart, adaptiveSettlementEnd)
assert.match(
  adaptiveSettlementSource,
  /outcome\?\.status === 'terminal'[\s\S]*?adaptiveAnswerSubmissionTasks\.delete\(key\)[\s\S]*?releaseAnswerSubmissionSettlement\(task\.submissionId\)[\s\S]*?return false/,
  'a terminal adaptive submission must release its completed settlement task before retry'
)

const specialReviewStart = practiceSource.indexOf('function buildSpecialPracticeReviewResults')
const specialReviewEnd = practiceSource.indexOf('function resetQuizState', specialReviewStart)
assert.ok(specialReviewStart >= 0 && specialReviewEnd > specialReviewStart)
const specialReviewSource = practiceSource.slice(specialReviewStart, specialReviewEnd)
assert.doesNotMatch(
  specialReviewSource,
  /String\(saved\.selectedAnswer[\s\S]{0,160}===\s*String\(saved\.correctAnswer/,
  'an unresolved grade must not be inferred from cached answer text'
)

const requests = []
const pendingRequests = []
globalThis.__responsiveAnswerTestRequest = (options) => new Promise((resolve, reject) => {
  requests.push(options)
  pendingRequests.push({ options, resolve, reject })
})

apiSource = apiSource.replace(
  "import { request } from './http'",
  'const request = globalThis.__responsiveAnswerTestRequest'
)
const apiModule = await import(
  `data:text/javascript;base64,${Buffer.from(apiSource).toString('base64')}`
)

const headerGrades = []
const headerSubmission = apiModule.submitAnswerResponsive(
  {
    question_id: 'question-1',
    selected_answer: 'A',
    client_submission_id: 'run-1:answer:question-1',
    used_time: 5,
    exam_code: 'Z001'
  },
  (grade) => headerGrades.push(grade)
)

assert.equal(requests.length, 1)
assert.equal(requests[0].url, '/answers/submit-responsive')
assert.equal(requests[0].enableChunked, true)
pendingRequests[0].options.onHeadersReceived?.({
  header: {
    'X-GYT-Grading-Ready': '1',
    'X-GYT-Question-Id': 'question-1',
    'X-GYT-Correct-Answer': 'C',
    'X-GYT-Is-Correct': '0',
    'X-GYT-Added-To-Wrong-Questions': '1'
  }
})
assert.deepEqual(headerGrades, [{
  questionId: 'question-1',
  correctAnswer: 'C',
  isCorrect: false,
  addedToWrongQuestions: true
}])

pendingRequests[0].resolve({
  question_id: 'question-1',
  correct_answer: 'C',
  is_correct: false,
  added_to_wrong_questions: true,
  persisted: true
})
const headerResult = await headerSubmission
assert.equal(headerResult.persisted, true)
assert.equal(headerGrades.length, 1, 'the final body must not render the same grade twice')
assert.equal(requests.length, 1, 'header feedback must not start a second request')

const bodyGrades = []
const bodySubmission = apiModule.submitAnswerResponsive(
  {
    question_id: 'question-2',
    selected_answer: 'B',
    client_submission_id: 'run-1:answer:question-2',
    used_time: 6,
    exam_code: 'Z001'
  },
  (grade) => bodyGrades.push(grade)
)
assert.equal(requests.length, 2)
pendingRequests[1].resolve({
  question_id: 'question-2',
  correct_answer: 'B',
  is_correct: true,
  added_to_wrong_questions: false,
  persisted: true
})
assert.equal((await bodySubmission).persisted, true)
assert.deepEqual(bodyGrades, [{
  questionId: 'question-2',
  correctAnswer: 'B',
  isCorrect: true,
  addedToWrongQuestions: false
}])
assert.equal(requests.length, 2, 'body fallback must reuse the responsive request')

const unpersistedGrades = []
const unpersistedSubmission = apiModule.submitAnswerResponsive(
  {
    question_id: 'question-3',
    selected_answer: 'D',
    client_submission_id: 'run-1:answer:question-3',
    used_time: 7,
    exam_code: 'Z001'
  },
  (grade) => unpersistedGrades.push(grade)
)
assert.equal(requests.length, 3)
pendingRequests[2].resolve({
  question_id: 'question-3',
  correct_answer: 'A',
  is_correct: false,
  added_to_wrong_questions: true,
  persisted: false,
  persistence_retryable: true,
  persistence_error: '作答记录正在后台同步'
})
await assert.rejects(
  unpersistedSubmission,
  (error) => (
    error?.code === 'ANSWER_SUBMISSION_NOT_PERSISTED' &&
    error?.retryable === true &&
    error?.result?.persisted === false
  )
)
assert.deepEqual(unpersistedGrades, [], 'an unpersisted body must not disclose the grade')
assert.equal(requests.length, 3, 'contract rejection must not start a fallback request')

console.log('responsive answer feedback: ok')
