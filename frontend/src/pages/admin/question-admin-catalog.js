import catalog from '../../../../backend/app/question_catalog.json'

export const QUESTION_STATUS = {
  ACTIVE: 'active',
  ARCHIVED: 'archived',
  PENDING_REVIEW: 'pending_review'
}

export const QUESTION_CATALOG = catalog

export const QUESTION_SUBJECTS = [
  { label: '全部科目', value: '' },
  ...Object.keys(QUESTION_CATALOG).map((subject) => ({ label: subject, value: subject }))
]

export const QUESTION_MODULES = Object.fromEntries(
  Object.entries(QUESTION_CATALOG).map(([subject, config]) => [
    subject,
    Object.keys(config.modules || {})
  ])
)
