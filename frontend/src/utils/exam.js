export const EXAM_OPTIONS = [
  {
    code: 'Z001',
    shortLabel: 'Z001',
    title: 'Z001 综合能力（一）',
    subtitle: '中华文化 55 分 / 英语运用 50 分 / 逻辑推理 45 分',
    heroTitle: '逻辑强化模式',
    heroTag: '本周数据已同步',
    heroSubtitle: '聚焦中华文化、英语运用和逻辑推理的刷题路径。',
    thirdSubject: '逻辑推理',
    thirdIcon: '🧠',
    subjects: ['中华文化', '英语运用', '逻辑推理']
  },
  {
    code: 'Z002',
    shortLabel: 'Z002',
    title: 'Z002 综合能力（二）',
    subtitle: '中华文化 55 分 / 英语运用 50 分 / 数学基础 45 分',
    heroTitle: '数学强化模式',
    heroTag: '本周数据已同步',
    heroSubtitle: '聚焦中华文化、英语运用和数学基础的刷题路径。',
    thirdSubject: '数学基础',
    thirdIcon: '📐',
    subjects: ['中华文化', '英语运用', '数学基础']
  }
]

export function getExamOption(code) {
  return EXAM_OPTIONS.find((item) => item.code === code) || EXAM_OPTIONS[0]
}
