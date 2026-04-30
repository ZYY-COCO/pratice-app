-- 手机号验证码登录/注册支持。
-- 先在 Supabase SQL Editor 执行本文件，再启用后端手机号登录接口。

alter table public.users
  add column if not exists phone text;

alter table public.users
  add column if not exists auth_provider text not null default 'email'
    check (auth_provider in ('email', 'phone', 'wechat'));

alter table public.users
  add column if not exists wechat_openid text;

create unique index if not exists idx_users_phone_unique
  on public.users (phone)
  where phone is not null;

create unique index if not exists idx_users_wechat_openid_unique
  on public.users (wechat_openid)
  where wechat_openid is not null;

create table if not exists public.auth_phone_codes (
  id uuid primary key default gen_random_uuid(),
  phone text not null,
  purpose text not null check (purpose in ('login', 'register', 'bind_phone')),
  code_hash text not null,
  expires_at timestamptz not null,
  consumed_at timestamptz,
  created_at timestamptz not null default now()
);

create index if not exists idx_auth_phone_codes_phone_purpose_created
  on public.auth_phone_codes (phone, purpose, created_at desc);

create index if not exists idx_auth_phone_codes_expires
  on public.auth_phone_codes (expires_at);

alter table public.auth_phone_codes enable row level security;

drop policy if exists "service role manages phone codes" on public.auth_phone_codes;
create policy "service role manages phone codes"
  on public.auth_phone_codes
  for all
  using (auth.role() = 'service_role')
  with check (auth.role() = 'service_role');
