-- Admin role and audit-log support for the management console.

alter table public.users
  add column if not exists role text not null default 'user',
  add column if not exists disabled_at timestamptz;

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

update public.users
set role = 'admin'
where lower(email) = '2221073755@qq.com';

revoke insert (role, disabled_at) on public.users from anon, authenticated;
revoke update (role, disabled_at) on public.users from anon, authenticated;

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
