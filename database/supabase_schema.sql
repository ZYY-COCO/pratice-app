-- 港澳台考研初试刷题 App - Supabase 数据库结构
-- 执行位置：Supabase SQL Editor
-- 说明：认证使用 Supabase Auth，业务用户信息落在 public.users。

create extension if not exists "pgcrypto";

-- 更新时间通用触发器
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

-- 业务用户表，与 auth.users 一一对应。
create table if not exists public.users (
  id uuid primary key references auth.users(id) on delete cascade,
  email text not null unique,
  nickname text,
  exam_target text check (exam_target in ('Z001', 'Z002')),
  created_at timestamptz not null default now()
);

create table if not exists public.passages (
  id uuid primary key default gen_random_uuid(),
  exam_code text not null check (exam_code in ('Z001', 'Z002', 'COMMON')),
  subject text not null,
  title text,
  content text not null,
  source_type text,
  source_year integer,
  created_at timestamptz not null default now()
);

create table if not exists public.questions (
  id uuid primary key default gen_random_uuid(),
  exam_code text not null check (exam_code in ('Z001', 'Z002', 'COMMON')),
  subject text not null,
  module text not null,
  submodule text not null,
  question_type text not null default 'single_choice',
  stem text not null,
  option_a text not null,
  option_b text not null,
  option_c text not null,
  option_d text not null,
  answer text not null check (answer in ('A', 'B', 'C', 'D')),
  explanation text not null default '',
  difficulty integer not null default 2 check (difficulty between 1 and 5),
  source_type text,
  source_year integer,
  passage_id uuid references public.passages(id) on delete set null,
  created_at timestamptz not null default now()
);

create table if not exists public.user_answers (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  question_id uuid not null references public.questions(id) on delete cascade,
  selected_answer text not null check (selected_answer in ('A', 'B', 'C', 'D')),
  is_correct boolean not null,
  used_time integer not null default 0 check (used_time >= 0),
  created_at timestamptz not null default now()
);

create table if not exists public.wrong_questions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  question_id uuid not null references public.questions(id) on delete cascade,
  wrong_count integer not null default 1 check (wrong_count >= 1),
  last_wrong_at timestamptz not null default now(),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (user_id, question_id)
);

create table if not exists public.ability_stats (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  exam_code text not null check (exam_code in ('Z001', 'Z002')),
  subject text not null,
  module text not null,
  submodule text not null,
  total_count integer not null default 0 check (total_count >= 0),
  correct_count integer not null default 0 check (correct_count >= 0),
  accuracy numeric(5, 2) not null default 0 check (accuracy >= 0 and accuracy <= 100),
  updated_at timestamptz not null default now(),
  unique (user_id, exam_code, subject, module, submodule)
);

drop trigger if exists set_wrong_questions_updated_at on public.wrong_questions;
create trigger set_wrong_questions_updated_at
before update on public.wrong_questions
for each row execute function public.set_updated_at();

drop trigger if exists set_ability_stats_updated_at on public.ability_stats;
create trigger set_ability_stats_updated_at
before update on public.ability_stats
for each row execute function public.set_updated_at();

create index if not exists idx_questions_exam_subject_module
  on public.questions (exam_code, subject, module, submodule);

create index if not exists idx_questions_passage_id
  on public.questions (passage_id);

create index if not exists idx_user_answers_user_created
  on public.user_answers (user_id, created_at desc);

create index if not exists idx_wrong_questions_user_last
  on public.wrong_questions (user_id, last_wrong_at desc);

create index if not exists idx_ability_stats_user_exam
  on public.ability_stats (user_id, exam_code, subject, module, submodule);

-- 启用 RLS。后端使用 service role 可绕过 RLS；客户端直连时仍能保护个人数据。
alter table public.users enable row level security;
alter table public.passages enable row level security;
alter table public.questions enable row level security;
alter table public.user_answers enable row level security;
alter table public.wrong_questions enable row level security;
alter table public.ability_stats enable row level security;

drop policy if exists "users can read own profile" on public.users;
create policy "users can read own profile"
  on public.users for select
  using (auth.uid() = id);

drop policy if exists "users can update own profile" on public.users;
create policy "users can update own profile"
  on public.users for update
  using (auth.uid() = id)
  with check (auth.uid() = id);

drop policy if exists "users can insert own profile" on public.users;
create policy "users can insert own profile"
  on public.users for insert
  with check (auth.uid() = id);

drop policy if exists "authenticated users can read passages" on public.passages;
create policy "authenticated users can read passages"
  on public.passages for select
  to authenticated
  using (true);

drop policy if exists "authenticated users can read questions" on public.questions;
create policy "authenticated users can read questions"
  on public.questions for select
  to authenticated
  using (true);

drop policy if exists "users can read own answers" on public.user_answers;
create policy "users can read own answers"
  on public.user_answers for select
  using (auth.uid() = user_id);

drop policy if exists "users can insert own answers" on public.user_answers;
create policy "users can insert own answers"
  on public.user_answers for insert
  with check (auth.uid() = user_id);

drop policy if exists "users can read own wrong questions" on public.wrong_questions;
create policy "users can read own wrong questions"
  on public.wrong_questions for select
  using (auth.uid() = user_id);

drop policy if exists "users can upsert own wrong questions" on public.wrong_questions;
create policy "users can upsert own wrong questions"
  on public.wrong_questions for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "users can read own ability stats" on public.ability_stats;
create policy "users can read own ability stats"
  on public.ability_stats for select
  using (auth.uid() = user_id);

drop policy if exists "users can upsert own ability stats" on public.ability_stats;
create policy "users can upsert own ability stats"
  on public.ability_stats for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

-- 示例题目，可用于本地联调。正式题库建议通过 CSV/后台导入。
insert into public.questions (
  id, exam_code, subject, module, submodule, stem,
  option_a, option_b, option_c, option_d,
  answer, explanation, difficulty, source_type, source_year
) values
  (
    '00000000-0000-0000-0000-000000000001',
    'Z001', '中华文化', '中国哲学常识', '儒家',
    '下列人物中，通常被认为是儒家学派创始人的是哪一位？',
    '老子', '孔子', '墨子', '韩非子',
    'B', '孔子是儒家学派的重要奠基者，其思想以仁、礼等为核心。', 1, 'sample', 2026
  ),
  (
    '00000000-0000-0000-0000-000000000002',
    'Z002', '数学基础', '一元函数微分学', '导数',
    '函数 f(x)=x^2 在 x=3 处的导数值为多少？',
    '3', '6', '9', '12',
    'B', 'f''(x)=2x，因此 f''(3)=6。', 1, 'sample', 2026
  )
on conflict do nothing;
