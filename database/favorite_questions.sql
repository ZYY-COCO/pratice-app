-- User favorite questions.
-- Run this file once in Supabase SQL Editor before using the Favorites feature.

create table if not exists public.favorite_questions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  question_id uuid not null references public.questions(id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (user_id, question_id)
);

create index if not exists idx_favorite_questions_user_created
  on public.favorite_questions (user_id, created_at desc);

create index if not exists idx_favorite_questions_question
  on public.favorite_questions (question_id);

alter table public.favorite_questions enable row level security;

drop policy if exists "users can read own favorite questions" on public.favorite_questions;
create policy "users can read own favorite questions"
  on public.favorite_questions for select
  using (auth.uid() = user_id);

drop policy if exists "users can manage own favorite questions" on public.favorite_questions;
create policy "users can manage own favorite questions"
  on public.favorite_questions for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);
