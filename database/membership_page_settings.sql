-- User-facing PLUS subscription-sheet content and plan pricing.
-- Apply after database/membership.sql. The backend uses service-role access;
-- direct client access is intentionally blocked by RLS.

create table if not exists public.membership_page_settings (
  id text primary key default 'default'
    check (id = 'default'),
  title text not null,
  brand_name text not null,
  benefits jsonb not null
    check (jsonb_typeof(benefits) = 'array'),
  monthly_price_cents integer not null
    check (monthly_price_cents > 0),
  quarterly_price_cents integer not null
    check (quarterly_price_cents > 0),
  plan_hint text not null,
  primary_button_text text not null,
  secondary_button_text text not null,
  description_text text not null,
  terms_text text not null,
  updated_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

insert into public.membership_page_settings (
  id,
  title,
  brand_name,
  benefits,
  monthly_price_cents,
  quarterly_price_cents,
  plan_hint,
  primary_button_text,
  secondary_button_text,
  description_text,
  terms_text
)
values (
  'default',
  '开通 PLUS',
  'HMTC 升学交流圈',
  '["完整访问港澳台考研题库", "获得 AI 专项训练与学习建议", "查看学习报告与错题复盘", "优先体验后续 PLUS 学习权益"]'::jsonb,
  8800,
  22800,
  '选择适合你的学习计划',
  '订阅 PLUS',
  '恢复购买',
  '订阅服务开通后，将按所选套餐为你提供 PLUS 学习权益。',
  '服务条款 · 隐私政策'
)
on conflict (id) do nothing;

alter table public.membership_page_settings enable row level security;
