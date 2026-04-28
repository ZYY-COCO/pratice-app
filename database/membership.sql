-- Membership fields and payment-order skeleton.
-- Apply this in Supabase before enabling real payment callbacks.

alter table public.users
  add column if not exists membership_status text not null default 'inactive',
  add column if not exists membership_plan text,
  add column if not exists membership_started_at timestamptz,
  add column if not exists membership_expires_at timestamptz,
  add column if not exists membership_updated_at timestamptz;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'users_membership_status_check'
  ) then
    alter table public.users
      add constraint users_membership_status_check
      check (membership_status in ('inactive', 'active', 'expired', 'cancelled'));
  end if;
end $$;

create index if not exists idx_users_membership_status
  on public.users (membership_status);

revoke insert (
  membership_status,
  membership_plan,
  membership_started_at,
  membership_expires_at,
  membership_updated_at
) on public.users from anon, authenticated;

revoke update (
  membership_status,
  membership_plan,
  membership_started_at,
  membership_expires_at,
  membership_updated_at
) on public.users from anon, authenticated;

create table if not exists public.membership_orders (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  provider text not null,
  provider_order_id text,
  plan_code text not null,
  amount_cents integer,
  currency text not null default 'CNY',
  status text not null default 'pending'
    check (status in ('pending', 'paid', 'failed', 'cancelled', 'refunded')),
  paid_at timestamptz,
  raw_payload jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'membership_orders_plan_code_check'
  ) then
    alter table public.membership_orders
      add constraint membership_orders_plan_code_check
      check (plan_code in ('pro_monthly', 'pro_quarterly'));
  end if;
end $$;

create unique index if not exists idx_membership_orders_provider_order
  on public.membership_orders (provider, provider_order_id)
  where provider_order_id is not null;

create index if not exists idx_membership_orders_user_created
  on public.membership_orders (user_id, created_at desc);

alter table public.membership_orders enable row level security;

drop policy if exists "users can read own membership orders" on public.membership_orders;
create policy "users can read own membership orders"
  on public.membership_orders for select
  using (auth.uid() = user_id);
