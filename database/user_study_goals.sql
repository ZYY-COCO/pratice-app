-- 用户学习任务：按账号与考试版本保存每日时长和每周刷题目标。
-- 执行位置：Supabase SQL Editor。
-- FastAPI 使用 service role 读写；RLS 同时限制直连客户端只能访问自己的记录。

create extension if not exists "pgcrypto";

create table if not exists public.user_study_goals (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  exam_code text not null check (exam_code in ('Z001', 'Z002')),
  daily_minutes integer not null default 60
    check (daily_minutes between 20 and 180 and daily_minutes % 10 = 0),
  weekly_question_target integer not null default 300
    check (
      weekly_question_target between 50 and 2000
      and weekly_question_target % 50 = 0
    ),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint uq_user_study_goals_user_exam unique (user_id, exam_code)
);

create or replace function public.touch_user_study_goals_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = public
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists trg_user_study_goals_updated_at on public.user_study_goals;
create trigger trg_user_study_goals_updated_at
before update on public.user_study_goals
for each row execute function public.touch_user_study_goals_updated_at();

alter table public.user_study_goals enable row level security;

drop policy if exists "users can read own study goals" on public.user_study_goals;
create policy "users can read own study goals"
  on public.user_study_goals for select
  using (auth.uid() = user_id);

drop policy if exists "users can insert own study goals" on public.user_study_goals;
create policy "users can insert own study goals"
  on public.user_study_goals for insert
  with check (auth.uid() = user_id);

drop policy if exists "users can update own study goals" on public.user_study_goals;
create policy "users can update own study goals"
  on public.user_study_goals for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "users can delete own study goals" on public.user_study_goals;
create policy "users can delete own study goals"
  on public.user_study_goals for delete
  using (auth.uid() = user_id);
