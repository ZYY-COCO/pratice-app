-- 港澳台考研初试刷题 App - 最小测试数据
-- 执行前提：已先执行 database/supabase_schema.sql
-- 覆盖范围：中华文化、英语运用、逻辑推理（Z001）、数学基础（Z002）

insert into public.passages (
  id, exam_code, subject, title, content, source_type, source_year
) values
  (
    '10000000-0000-0000-0000-000000000001',
    'Z001',
    '英语运用',
    'Reading Practice: Study Habits',
    'Many students improve their learning outcomes by setting a fixed review schedule. Short daily practice is often more effective than a long review session only before an exam.',
    'sample',
    2026
  ),
  (
    '10000000-0000-0000-0000-000000000002',
    'Z002',
    '英语运用',
    'Reading Practice: Time Management',
    'A clear study plan helps learners divide large goals into small tasks. When tasks are specific, it is easier to track progress and adjust the plan.',
    'sample',
    2026
  )
on conflict (id) do update set
  title = excluded.title,
  content = excluded.content,
  source_type = excluded.source_type,
  source_year = excluded.source_year;

insert into public.questions (
  id, exam_code, subject, module, submodule, question_type, stem,
  option_a, option_b, option_c, option_d,
  answer, explanation, difficulty, source_type, source_year, passage_id
) values
  (
    '20000000-0000-0000-0000-000000000001',
    'Z001', '中华文化', '中国哲学常识', '儒家', 'single_choice',
    '下列哪一项最能体现儒家思想中的“仁”？',
    '清静无为', '兼爱非攻', '爱人并重视礼的规范', '以法治国',
    'C',
    '儒家强调仁与礼，“仁者爱人”是儒家思想的重要表达。',
    1, 'sample', 2026, null
  ),
  (
    '20000000-0000-0000-0000-000000000002',
    'Z002', '中华文化', '中国文学常识', '代表作家及作品', 'single_choice',
    '《史记》的作者是下列哪一位？',
    '司马迁', '班固', '司马光', '刘向',
    'A',
    '《史记》是西汉司马迁撰写的纪传体通史。',
    1, 'sample', 2026, null
  ),
  (
    '20000000-0000-0000-0000-000000000003',
    'Z001', '英语运用', '语言知识', '词汇', 'single_choice',
    'Choose the closest meaning of “effective”.',
    'useful and successful', 'very expensive', 'hard to find', 'not complete',
    'A',
    'effective 表示“有效的、产生预期效果的”。',
    1, 'sample', 2026, null
  ),
  (
    '20000000-0000-0000-0000-000000000004',
    'Z002', '英语运用', '阅读理解', '阅读主旨题', 'single_choice',
    'According to the passage, what is the main benefit of a clear study plan?',
    'It removes all difficult tasks.', 'It helps divide goals and track progress.', 'It replaces daily practice.', 'It guarantees a high score.',
    'B',
    '材料指出清晰计划能把大目标拆成小任务，并帮助追踪进度。',
    2, 'sample', 2026, '10000000-0000-0000-0000-000000000002'
  ),
  (
    '20000000-0000-0000-0000-000000000005',
    'Z001', '逻辑推理', '概念', '概念关系', 'single_choice',
    '“学生”和“研究生”这两个概念之间最准确的关系是？',
    '全同关系', '属种关系', '矛盾关系', '交叉关系',
    'B',
    '研究生属于学生的一种，因此二者是属种关系。',
    2, 'sample', 2026, null
  ),
  (
    '20000000-0000-0000-0000-000000000006',
    'Z001', '逻辑推理', '论证', '削弱', 'single_choice',
    '若要削弱“每天刷题越多，成绩一定越好”的观点，下列哪项最合适？',
    '刷题需要时间', '部分学生大量刷题但不复盘，成绩没有提升', '考试包含多个科目', '许多学生喜欢刷题',
    'B',
    '该选项指出刷题数量增加但成绩未提升，直接削弱“一定越好”的结论。',
    2, 'sample', 2026, null
  ),
  (
    '20000000-0000-0000-0000-000000000007',
    'Z002', '数学基础', '一元函数微分学', '导数', 'single_choice',
    '函数 f(x)=3x^2+2x 的导函数是？',
    '3x+2', '6x+2', '6x', 'x^3+x^2',
    'B',
    '根据幂函数求导法则，(3x^2)''=6x，(2x)''=2，因此 f''(x)=6x+2。',
    1, 'sample', 2026, null
  ),
  (
    '20000000-0000-0000-0000-000000000008',
    'Z002', '数学基础', '一元函数积分学', '原函数', 'single_choice',
    '函数 f(x)=2x 的一个原函数是？',
    'x^2+C', '2+C', '2x^2+C', 'ln x+C',
    'A',
    '因为 (x^2+C)''=2x，所以 x^2+C 是 2x 的一个原函数。',
    1, 'sample', 2026, null
  )
on conflict (id) do update set
  exam_code = excluded.exam_code,
  subject = excluded.subject,
  module = excluded.module,
  submodule = excluded.submodule,
  question_type = excluded.question_type,
  stem = excluded.stem,
  option_a = excluded.option_a,
  option_b = excluded.option_b,
  option_c = excluded.option_c,
  option_d = excluded.option_d,
  answer = excluded.answer,
  explanation = excluded.explanation,
  difficulty = excluded.difficulty,
  source_type = excluded.source_type,
  source_year = excluded.source_year,
  passage_id = excluded.passage_id;
