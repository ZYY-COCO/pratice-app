-- Add learning-analysis metadata columns for App wrong-question analysis and AI study reports.
alter table public.questions add column if not exists skill_tags text[] not null default ARRAY[]::text[];
alter table public.questions add column if not exists mistake_tags text[] not null default ARRAY[]::text[];
alter table public.questions add column if not exists solution_type text;
alter table public.questions add column if not exists estimated_time_sec integer;

create index if not exists idx_questions_skill_tags on public.questions using gin (skill_tags);
create index if not exists idx_questions_mistake_tags on public.questions using gin (mistake_tags);
create index if not exists idx_questions_solution_type on public.questions (solution_type);
