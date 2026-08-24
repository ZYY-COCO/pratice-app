-- 用户消息投递载荷增量：在已执行 user_notifications.sql 的环境中补齐。
-- 执行位置：Supabase SQL Editor。
-- 本次仅预留统一的站内提醒 / App 原生推送数据，不会发送真实推送。

alter table public.user_notifications
  add column if not exists delivery_payload jsonb not null default '{}'::jsonb;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'user_notifications_delivery_payload_object_check'
      and conrelid = 'public.user_notifications'::regclass
  ) then
    alter table public.user_notifications
      add constraint user_notifications_delivery_payload_object_check
      check (jsonb_typeof(delivery_payload) = 'object');
  end if;
end $$;
