-- 邮箱验证码表
-- 执行前提：已执行 database/supabase_schema.sql

create table if not exists public.auth_email_codes (
  id uuid primary key default gen_random_uuid(),
  email text not null,
  purpose text not null check (purpose in ('register', 'reset_password', 'change_email')),
  code_hash text not null,
  expires_at timestamptz not null,
  consumed_at timestamptz,
  created_at timestamptz not null default now()
);

alter table public.auth_email_codes
  drop constraint if exists auth_email_codes_purpose_check;

alter table public.auth_email_codes
  add constraint auth_email_codes_purpose_check
  check (purpose in ('register', 'reset_password', 'change_email'));

create index if not exists idx_auth_email_codes_email_purpose_created
  on public.auth_email_codes (email, purpose, created_at desc);

create index if not exists idx_auth_email_codes_expires
  on public.auth_email_codes (expires_at);

alter table public.auth_email_codes enable row level security;
