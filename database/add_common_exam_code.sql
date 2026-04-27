-- 支持公共题库：中华文化、英语运用可统一存为 COMMON，供 Z001 / Z002 共同调用。
-- 执行位置：Supabase SQL Editor

alter table public.questions
  drop constraint if exists questions_exam_code_check;

alter table public.questions
  add constraint questions_exam_code_check
  check (exam_code in ('Z001', 'Z002', 'COMMON'));

alter table public.passages
  drop constraint if exists passages_exam_code_check;

alter table public.passages
  add constraint passages_exam_code_check
  check (exam_code in ('Z001', 'Z002', 'COMMON'));

create index if not exists idx_questions_common_subject_module
  on public.questions (subject, module, submodule, exam_code);
