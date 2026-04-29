-- Execute in Supabase SQL Editor.
-- AI generated training sessions for Pro members.

create table if not exists public.ai_training_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  exam_code text not null check (exam_code in ('Z001', 'Z002')),
  subject text not null,
  module text not null,
  submodule text not null,
  difficulty text not null,
  question_count integer not null check (question_count between 1 and 50),
  smart_mode boolean not null default true,
  basis text,
  status text not null default 'generating'
    check (status in ('generating', 'completed', 'failed')),
  raw_request jsonb,
  raw_response jsonb,
  error_message text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.ai_training_session_questions (
  session_id uuid not null references public.ai_training_sessions(id) on delete cascade,
  question_id uuid not null references public.questions(id) on delete cascade,
  position integer not null check (position >= 1),
  created_at timestamptz not null default now(),
  primary key (session_id, question_id)
);

create index if not exists idx_ai_training_sessions_user_created
  on public.ai_training_sessions (user_id, created_at desc);

create index if not exists idx_ai_training_session_questions_session_position
  on public.ai_training_session_questions (session_id, position);

drop trigger if exists set_ai_training_sessions_updated_at on public.ai_training_sessions;
create trigger set_ai_training_sessions_updated_at
before update on public.ai_training_sessions
for each row execute function public.set_updated_at();

alter table public.ai_training_sessions enable row level security;
alter table public.ai_training_session_questions enable row level security;

drop policy if exists "users can read own ai training sessions" on public.ai_training_sessions;
create policy "users can read own ai training sessions"
  on public.ai_training_sessions for select
  using (auth.uid() = user_id);

drop policy if exists "users can read own ai training session questions" on public.ai_training_session_questions;
create policy "users can read own ai training session questions"
  on public.ai_training_session_questions for select
  using (
    exists (
      select 1
      from public.ai_training_sessions s
      where s.id = ai_training_session_questions.session_id
        and s.user_id = auth.uid()
    )
  );
