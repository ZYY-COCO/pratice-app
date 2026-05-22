-- Admin role and audit-log support for the management console.

alter table public.users
  add column if not exists role text not null default 'user',
  add column if not exists disabled_at timestamptz;

alter table public.questions
  add column if not exists status text not null default 'active',
  add column if not exists archived_at timestamptz,
  add column if not exists archived_by uuid references public.users(id) on delete set null;

alter table public.beta_feedback
  add column if not exists status text not null default 'open',
  add column if not exists admin_note text,
  add column if not exists handled_at timestamptz,
  add column if not exists handled_by uuid references public.users(id) on delete set null;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'users_role_check'
  ) then
    alter table public.users
      add constraint users_role_check
      check (role in ('user', 'admin'));
  end if;
end $$;

create index if not exists idx_users_role on public.users(role);
create index if not exists idx_users_disabled_at on public.users(disabled_at);
create index if not exists idx_questions_status on public.questions(status);
create index if not exists idx_beta_feedback_status on public.beta_feedback(status);

update public.users
set role = 'admin'
where lower(email) = '2221073755@qq.com';

revoke insert (role, disabled_at) on public.users from anon, authenticated;
revoke update (role, disabled_at) on public.users from anon, authenticated;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'questions_status_check'
  ) then
    alter table public.questions
      add constraint questions_status_check
      check (status in ('active', 'archived'));
  end if;

  if not exists (
    select 1
    from pg_constraint
    where conname = 'beta_feedback_status_check'
  ) then
    alter table public.beta_feedback
      add constraint beta_feedback_status_check
      check (status in ('open', 'reviewed', 'resolved', 'ignored'));
  end if;
end $$;

revoke insert (status, archived_at, archived_by) on public.questions from anon, authenticated;
revoke update (status, archived_at, archived_by) on public.questions from anon, authenticated;
revoke insert (status, admin_note, handled_at, handled_by) on public.beta_feedback from anon, authenticated;
revoke update (status, admin_note, handled_at, handled_by) on public.beta_feedback from anon, authenticated;

create table if not exists public.admin_action_logs (
  id uuid primary key default gen_random_uuid(),
  admin_user_id uuid references public.users(id) on delete set null,
  action text not null,
  target_type text not null,
  target_id uuid,
  details jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_admin_action_logs_admin_created
  on public.admin_action_logs(admin_user_id, created_at desc);

create index if not exists idx_admin_action_logs_target
  on public.admin_action_logs(target_type, target_id);

alter table public.admin_action_logs enable row level security;

-- The backend uses the service-role key for admin APIs; no client-side RLS policy is granted here.
