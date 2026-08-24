-- 用户消息中心：用于保存面向单个用户的处理结果、复核结论与咨询动态。
-- 执行位置：Supabase SQL Editor。
-- 平台公告仍沿用 official_messages；本表只保存指定接收人的站内通知。

create extension if not exists "pgcrypto";

create table if not exists public.user_notifications (
  id uuid primary key default gen_random_uuid(),
  recipient_user_id uuid not null references public.users(id) on delete cascade,
  category text not null check (category in ('community', 'consultation', 'official')),
  notification_type text not null check (char_length(btrim(notification_type)) between 1 and 80),
  title text not null check (char_length(btrim(title)) between 1 and 120),
  summary text not null default '',
  content text not null default '',
  related_type text,
  related_id text,
  route_path text,
  delivery_payload jsonb not null default '{}'::jsonb,
  event_key text not null check (char_length(btrim(event_key)) between 1 and 255),
  created_at timestamptz not null default now(),
  read_at timestamptz,
  constraint user_notifications_route_path_check
    check (route_path is null or left(route_path, 1) = '/'),
  constraint user_notifications_delivery_payload_object_check
    check (jsonb_typeof(delivery_payload) = 'object')
);

create unique index if not exists uq_user_notifications_recipient_event
  on public.user_notifications (recipient_user_id, event_key);

create index if not exists idx_user_notifications_recipient_created
  on public.user_notifications (recipient_user_id, created_at desc);

create index if not exists idx_user_notifications_recipient_unread
  on public.user_notifications (recipient_user_id, created_at desc)
  where read_at is null;

alter table public.user_notifications enable row level security;

drop policy if exists "users can read own notifications" on public.user_notifications;
create policy "users can read own notifications"
  on public.user_notifications for select
  using (auth.uid() = recipient_user_id);

-- 写入和已读状态均由 FastAPI 使用 service role 完成，客户端不直连修改。
