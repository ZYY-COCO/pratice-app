create table if not exists public.beta_feedback (
  id uuid primary key default gen_random_uuid(),
  user_id uuid references public.users(id) on delete set null,
  feedback_type text not null,
  content text not null,
  willing_to_pay boolean,
  acceptable_price text,
  contact text,
  source_page text,
  created_at timestamptz not null default now()
);

create index if not exists idx_beta_feedback_user_id on public.beta_feedback(user_id);
create index if not exists idx_beta_feedback_type on public.beta_feedback(feedback_type);
create index if not exists idx_beta_feedback_created_at on public.beta_feedback(created_at desc);
