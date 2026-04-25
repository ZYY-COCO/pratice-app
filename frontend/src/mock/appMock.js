import { getExamOption } from '../utils/exam'

const compactMistakes = [
  {
    title: '《孟子》与“性善论”易混概念题',
    tags: ['中华文化', '先秦儒家', '错因：概念混淆']
  },
  {
    title: '阅读理解：作者态度判断题',
    tags: ['英语运用', '阅读逻辑', '错因：证据定位不准']
  }
]

const fullMistakes = [
  {
    title: '古代职官与科举：三省六部制细节辨析',
    tags: ['历史常识', '失分率高', '建议复刷']
  },
  {
    title: '阅读理解：作者隐含态度题',
    tags: ['英语运用', '证据定位慢', '建议限时训练']
  },
  {
    title: '积分换元：凑微分识别错误',
    tags: ['数学基础', 'Z002', '建议计时训练']
  }
]

const reportMetrics = [
  { label: '词汇量', value: 66 },
  { label: '阅读逻辑', value: 72 },
  { label: '文化常识广度', value: 48 },
  { label: '古代典籍深度', value: 40 },
  { label: '微积分运算', value: 82 }
]

const reportTasks = [
  {
    title: '建议重刷：先秦诸子百家易错题集合',
    desc: '目标：快速纠正概念边界混淆，建立儒、道、墨、法基本框架。',
    action: '直达'
  },
  {
    title: '阅读理解专项：态度判断 20 题',
    desc: '目标：缩短证据定位时间，提升选项排除效率。',
    action: '直达'
  },
  {
    title: '数学基础：换元积分法计时训练',
    desc: '目标：控制单题耗时，强化识别“凑微分”意识。',
    action: '直达'
  }
]

const profileStats = [
  { label: '累计刷题', value: '1,286 题' },
  { label: '本周正确率', value: '73%' },
  { label: 'AI 诊断次数', value: '8 次' },
  { label: '当前主攻', value: '中华文化 + 阅读理解' }
]

const tagCountMap = {
  中华文化: {
    儒家: 12,
    道家: 9,
    墨家: 8,
    法家: 6,
    后代学派流变: 7,
    古代宗教流变: 5,
    古代职官与科举: 14,
    古代礼俗与称谓: 10,
    古代衣食住行: 7,
    古代军事战争: 6,
    古代经济发展: 8,
    古代图书文物: 5,
    近现代史学常识: 4,
    文体流变: 11,
    代表作家及作品: 13,
    创作群体及文学流派: 9,
    文学总集: 4,
    民族史诗: 3,
    书法: 6,
    绘画: 7,
    雕塑: 4,
    建筑: 4,
    音乐: 5,
    戏剧: 8,
    民俗: 5,
    天文历法与算学: 6,
    地理舆图: 4,
    农业水利: 5,
    医学: 4,
    科技发明: 8
  },
  英语运用: {
    词汇: 16,
    语法: 14,
    语用: 10,
    阅读主旨题: 12,
    阅读细节题: 15,
    阅读推断题: 11,
    阅读词义题: 9,
    阅读结构题: 8
  },
  逻辑推理: {
    概念种类: 9,
    概念关系: 12,
    定义: 10,
    划分: 8,
    判断种类: 7,
    判断关系: 7,
    演绎推理: 11,
    归纳推理: 9,
    类比推理: 8,
    综合推理: 10,
    加强: 13,
    削弱: 12,
    解释: 9,
    谬误识别: 7
  },
  数学基础: {
    极限: 10,
    连续: 6,
    导数: 14,
    微分: 7,
    高阶导数: 6,
    洛必达法则: 5,
    单调性: 9,
    极值与最值: 12,
    凹凸性: 6,
    拐点: 5,
    渐近线: 6,
    原函数: 8,
    定积分: 12,
    变限定积分: 5,
    '牛顿-莱布尼兹公式': 6,
    换元积分: 11,
    分部积分: 9,
    几何应用: 5,
    物理应用: 4,
    偏导数: 8,
    全微分: 6,
    二阶偏导: 5,
    链导法则: 7,
    隐函数求导: 8,
    二元函数极值: 6
  }
}

const mockQuestions = {
  中华文化: {
    id: 'mock-culture-1',
    year: '2024 年真题',
    badge: '文学常识',
    stem: '“仁者爱人”这一表述最能体现先秦哪一学派的核心伦理思想？',
    helper: '当前为 mock 题目展示，后续可替换为题干图片、材料题或富文本。',
    options: [
      { key: 'A', text: '道家' },
      { key: 'B', text: '法家' },
      { key: 'C', text: '儒家' },
      { key: 'D', text: '墨家' }
    ],
    answer: 'C',
    explanation:
      '“仁者爱人”突出的是以“仁”为中心的人伦伦理观，这是孔子思想中的核心表达。它强调人与人之间的关怀、责任与秩序。道家更强调顺其自然，法家重制度与法术，墨家则强调“兼爱”“非攻”，与儒家“仁爱”的概念来源和理论体系不同，因此本题最优答案是儒家。',
    autoTag: '已自动加入错题本并打上薄弱标签：中华文化 / 中国哲学常识 / 儒家 / 概念辨析'
  },
  英语运用: {
    id: 'mock-english-1',
    year: '2024 年真题',
    badge: '阅读理解',
    stem: 'According to the passage, what is the main benefit of a clear study plan?',
    helper: '后续可接阅读材料 + 多题结构；当前先展示单题交互。',
    options: [
      { key: 'A', text: 'It removes all difficult tasks.' },
      { key: 'B', text: 'It helps divide goals and track progress.' },
      { key: 'C', text: 'It replaces daily practice.' },
      { key: 'D', text: 'It guarantees a high score.' }
    ],
    answer: 'B',
    explanation:
      '材料强调 clear study plan 能把大的学习目标拆分为小任务，并帮助学习者追踪进度，因此最准确的主旨是 B。',
    autoTag: '已自动加入错题本并打上薄弱标签：英语运用 / 阅读理解 / 阅读主旨题'
  },
  逻辑推理: {
    id: 'mock-logic-1',
    year: '2024 年真题',
    badge: '论证削弱',
    stem: '若要削弱“每天刷题越多，成绩一定越好”的观点，下列哪项最合适？',
    helper: '逻辑模式下可继续扩展成题组训练与错因标签。',
    options: [
      { key: 'A', text: '刷题需要时间。' },
      { key: 'B', text: '部分学生大量刷题但不复盘，成绩没有提升。' },
      { key: 'C', text: '考试包含多个科目。' },
      { key: 'D', text: '许多学生喜欢刷题。' }
    ],
    answer: 'B',
    explanation:
      'B 直接给出反例，说明“刷题越多，成绩一定越好”并不成立，因此削弱力度最强。',
    autoTag: '已自动加入错题本并打上薄弱标签：逻辑推理 / 论证 / 削弱'
  },
  数学基础: {
    id: 'mock-math-1',
    year: '2024 年真题',
    badge: '一元函数微分学',
    stem: '函数 f(x)=3x²+2x 的导函数是？',
    helper: '数学模式下这里可替换为公式图片、手写板或步骤提示。',
    options: [
      { key: 'A', text: '3x+2' },
      { key: 'B', text: '6x+2' },
      { key: 'C', text: '6x' },
      { key: 'D', text: 'x³+x²' }
    ],
    answer: 'B',
    explanation:
      '根据幂函数求导法则，(3x²)\'=6x，(2x)\'=2，因此 f\'(x)=6x+2。',
    autoTag: '已自动加入错题本并打上薄弱标签：数学基础 / 一元函数微分学 / 导数'
  }
}

export function getHomeModules(examCode) {
  const exam = getExamOption(examCode)
  return [
    {
      key: '中华文化',
      icon: '📚',
      title: '中华文化',
      desc: '哲学 / 历史 / 文学 / 艺术 / 典籍常识'
    },
    {
      key: '英语运用',
      icon: '📝',
      title: '英语运用',
      desc: '词汇语法 / 阅读理解 / 语篇判断'
    },
    {
      key: exam.thirdSubject,
      icon: exam.thirdIcon,
      title: exam.thirdSubject,
      desc: examCode === 'Z001' ? '形式逻辑 / 论证分析 / 推理题型专项' : '函数 / 极限 / 导数 / 积分 / 基础运算'
    }
  ]
}

export function getHomeDashboard(examCode) {
  return {
    userName: '小钟',
    statusText: '今日学习状态：稳定推进',
    heroTag: '学习看板',
    heroTitle: '本周已刷真题：128 道',
    heroSubtitle:
      examCode === 'Z001'
        ? '错题本已更新，AI 弱点诊断已就绪。当前最需要补强的是：中国历史学常识、阅读逻辑和论证削弱。'
        : '错题本已更新，AI 弱点诊断已就绪。当前最需要补强的是：中国历史学常识、阅读逻辑和积分换元速度。'
  }
}

export function getCompactMistakes() {
  return compactMistakes
}

export function getFullMistakes() {
  return fullMistakes
}

export function getReportMock() {
  return {
    metrics: reportMetrics,
    diagnosis:
      '你在【中国历史学常识 - 古代职官与科举】板块失分率达 75%，主要问题是官职职能与制度背景混淆；英语部分【阅读逻辑 - 态度判断】证据定位偏慢；若切换到数学版本，当前【一元函数积分学 - 换元积分法】的平均耗时高于目标线 31%。',
    tasks: reportTasks
  }
}

export function getProfileMock() {
  return {
    userName: '小钟',
    subtitle: '港澳台考研备考中',
    badge: '普通版',
    stats: profileStats
  }
}

export function getTagCount(subject, tag) {
  return tagCountMap[subject]?.[tag] || 0
}

export function getPracticeQuestion(subject, examCode) {
  if (subject === '英语运用') {
    return mockQuestions['英语运用']
  }
  if (subject === '中华文化') {
    return mockQuestions['中华文化']
  }
  if (subject === '数学基础' || examCode === 'Z002') {
    return mockQuestions['数学基础']
  }
  return mockQuestions['逻辑推理']
}
