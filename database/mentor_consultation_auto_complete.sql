-- 前辈咨询服务窗口到期自动完成。
-- 执行位置：Supabase SQL Editor。
-- 前置依赖：mentor_consultation.sql、mentor_consultation_reports.sql、
-- mentor_consultation_dispute_resolution.sql、mentor_consultation_report_appeals.sql、
-- mentor_consultation_payment_foundation.sql（通知 outbox）。

begin;

alter table public.mentor_consultation_orders
  add column if not exists service_ends_at timestamptz;

create index if not exists idx_mentor_consultation_reports_open_order
  on public.mentor_consultation_reports (order_id)
  where status in ('pending', 'reviewing');

create index if not exists idx_mentor_consultation_report_appeals_open_report
  on public.mentor_consultation_report_appeals (report_id)
  where status in ('pending', 'reviewing');

-- 自动完成的审计事件和系统消息都使用稳定业务键。即使未来调用方重试，
-- 同一订单也只会保留一条到期事件和一条到期提示。
create unique index if not exists uq_mentor_consultation_auto_completed_event
  on public.mentor_consultation_order_events (order_id, event_type)
  where event_type = 'consultation_auto_completed';

create unique index if not exists uq_mentor_consultation_system_message_business_key
  on public.mentor_consultation_messages (order_id, client_message_id)
  where sender_role = 'system' and client_message_id is not null;

create unique index if not exists uq_mentor_consultation_started_at_backfill_event
  on public.mentor_consultation_order_events (order_id, event_type)
  where event_type = 'consultation_started_at_backfilled';

-- 早期服务中记录可能在开始接口完善前未保留 started_at。优先使用可信的
-- accepted_at，再回退到 created_at；每次回填先写独立审计事件，便于后续追溯。
insert into public.mentor_consultation_order_events (
  order_id,
  actor_role,
  event_type,
  details
)
select
  orders.id,
  'system',
  'consultation_started_at_backfilled',
  jsonb_build_object(
    'source', case when orders.accepted_at is not null then 'accepted_at' else 'created_at' end,
    'backfilled_started_at', coalesce(orders.accepted_at, orders.created_at),
    'reason', 'legacy_in_progress_without_started_at'
  )
from public.mentor_consultation_orders orders
where orders.order_status = 'in_progress'
  and orders.started_at is null
on conflict do nothing;

-- 回填技术字段不改写历史订单的业务 updated_at。
alter table public.mentor_consultation_orders
  disable trigger set_mentor_orders_updated_at;

update public.mentor_consultation_orders orders
set started_at = coalesce(orders.accepted_at, orders.created_at)
where orders.order_status = 'in_progress'
  and orders.started_at is null;

update public.mentor_consultation_orders orders
set service_ends_at = case
  when orders.started_at is null then null
  else orders.started_at + make_interval(
    mins => greatest(15, least(180, orders.consultation_window_minutes::integer))
  )
end
where orders.service_ends_at is distinct from case
  when orders.started_at is null then null
  else orders.started_at + make_interval(
    mins => greatest(15, least(180, orders.consultation_window_minutes::integer))
  )
end;

alter table public.mentor_consultation_orders
  enable trigger set_mentor_orders_updated_at;

create or replace function public.sync_mentor_consultation_service_ends_at()
returns trigger
language plpgsql
set search_path = public, pg_temp
as $$
begin
  new.service_ends_at := case
    when new.started_at is null then null
    else new.started_at + make_interval(
      mins => greatest(15, least(180, new.consultation_window_minutes::integer))
    )
  end;
  return new;
end;
$$;

drop trigger if exists sync_mentor_consultation_service_ends_at
  on public.mentor_consultation_orders;
create trigger sync_mentor_consultation_service_ends_at
before insert or update of started_at, consultation_window_minutes
on public.mentor_consultation_orders
for each row execute function public.sync_mentor_consultation_service_ends_at();

-- 后台批量 RPC 直接按真实截止时间过滤，避免未到期的长时长订单或已开案订单
-- 占满扫描批次并饿死后续已到期订单。
create index if not exists idx_mentor_consultation_orders_in_progress_service_end
  on public.mentor_consultation_orders (service_ends_at, id)
  where order_status = 'in_progress' and service_ends_at is not null;

-- 咨询案件写入与订单自动完成共用同一个事务锁。这样在服务到期的
-- 临界时刻，已先获得锁的事务形成唯一顺序：案件先写入时自动完成会暂停；
-- 自动完成先提交时，后续仍可依现有规则提交售后问题，但不会回写或伪造双方确认时间。
create or replace function public.lock_mentor_consultation_order_for_report_write()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  perform pg_advisory_xact_lock(
    hashtextextended('mentor-consultation-order:' || new.order_id::text, 0)
  );
  return new;
end;
$$;

drop trigger if exists lock_mentor_consultation_order_for_report_write
  on public.mentor_consultation_reports;
create trigger lock_mentor_consultation_order_for_report_write
before insert or update of status on public.mentor_consultation_reports
for each row execute function public.lock_mentor_consultation_order_for_report_write();

create or replace function public.lock_mentor_consultation_order_for_appeal_write()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_order_id uuid;
begin
  select report.order_id
    into v_order_id
  from public.mentor_consultation_reports report
  where report.id = new.report_id;

  if v_order_id is not null then
    perform pg_advisory_xact_lock(
      hashtextextended('mentor-consultation-order:' || v_order_id::text, 0)
    );
  end if;
  return new;
end;
$$;

drop trigger if exists lock_mentor_consultation_order_for_appeal_write
  on public.mentor_consultation_report_appeals;
create trigger lock_mentor_consultation_order_for_appeal_write
before insert or update of status on public.mentor_consultation_report_appeals
for each row execute function public.lock_mentor_consultation_order_for_appeal_write();

create or replace function public.guard_mentor_consultation_participant_message_write()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_order_status text;
  v_service_ends_at timestamptz;
  v_applicant_completion_confirmed_at timestamptz;
  v_mentor_completion_confirmed_at timestamptz;
begin
  if new.sender_role = 'system' then
    return new;
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended('mentor-consultation-order:' || new.order_id::text, 0)
  );

  select
    orders.order_status,
    orders.service_ends_at,
    orders.applicant_completion_confirmed_at,
    orders.mentor_completion_confirmed_at
    into
      v_order_status,
      v_service_ends_at,
      v_applicant_completion_confirmed_at,
      v_mentor_completion_confirmed_at
  from public.mentor_consultation_orders orders
  where orders.id = new.order_id
  for update;

  if v_order_status is distinct from 'in_progress'
     or v_service_ends_at is null
     or v_service_ends_at <= clock_timestamp()
     or v_applicant_completion_confirmed_at is not null
     or v_mentor_completion_confirmed_at is not null then
    raise exception 'consultation_message_window_closed'
      using errcode = 'P0001';
  end if;
  return new;
end;
$$;

drop trigger if exists guard_mentor_consultation_participant_message_write
  on public.mentor_consultation_messages;
create trigger guard_mentor_consultation_participant_message_write
before insert on public.mentor_consultation_messages
for each row execute function public.guard_mentor_consultation_participant_message_write();

create or replace function public.auto_complete_expired_mentor_consultation_order(
  p_order_id uuid,
  p_now timestamptz default now()
)
returns setof public.mentor_consultation_orders
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_order public.mentor_consultation_orders%rowtype;
  v_service_ends_at timestamptz;
  v_mentor_owner_user_id uuid;
  v_window_minutes integer;
begin
  -- 与举报/申诉写入的触发器共用锁，将到期完成与案件变更串行化。
  perform pg_advisory_xact_lock(
    hashtextextended('mentor-consultation-order:' || p_order_id::text, 0)
  );

  select orders.*
    into v_order
  from public.mentor_consultation_orders orders
  where orders.id = p_order_id
  for update;

  if not found
     or v_order.order_status <> 'in_progress'
     or v_order.started_at is null then
    return;
  end if;

  v_window_minutes := greatest(15, least(180, v_order.consultation_window_minutes::integer));
  v_service_ends_at := coalesce(
    v_order.service_ends_at,
    v_order.started_at + make_interval(mins => v_window_minutes)
  );

  if v_service_ends_at > p_now then
    return;
  end if;

  if exists (
    select 1
    from public.mentor_consultation_reports report
    where report.order_id = p_order_id
      and report.status in ('pending', 'reviewing')
  ) then
    return;
  end if;

  if exists (
    select 1
    from public.mentor_consultation_report_appeals appeal
    join public.mentor_consultation_reports report
      on report.id = appeal.report_id
    where report.order_id = p_order_id
      and appeal.status in ('pending', 'reviewing')
  ) then
    return;
  end if;

  update public.mentor_consultation_orders orders
  set order_status = 'completed',
      -- 记录准确的合同服务截止点，不受后台扫描间隔影响。
      ended_at = v_service_ends_at
  where orders.id = p_order_id
    and orders.order_status = 'in_progress'
    and orders.started_at = v_order.started_at
  returning orders.* into v_order;

  if found then
    -- 订单、系统消息、审计事件和双方通知入队在同一事务中提交。
    insert into public.mentor_consultation_messages (
      order_id,
      sender_role,
      message_type,
      content,
      client_message_id
    ) values (
      p_order_id,
      'system',
      'system',
      format('本次咨询已达到 %s 分钟服务时限，系统已自动结束；聊天记录将继续保留。', v_window_minutes),
      'system:auto-completed:' || p_order_id::text
    ) on conflict do nothing;

    insert into public.mentor_consultation_order_events (
      order_id,
      actor_role,
      event_type,
      details
    ) values (
      p_order_id,
      'system',
      'consultation_auto_completed',
      jsonb_build_object(
        'completion', 'service_window_expired',
        'started_at', v_order.started_at,
        'service_ends_at', v_service_ends_at,
        'consultation_window_minutes', v_window_minutes,
        'applicant_completion_confirmed', v_order.applicant_completion_confirmed_at is not null,
        'mentor_completion_confirmed', v_order.mentor_completion_confirmed_at is not null
      )
    ) on conflict do nothing;

    select profile.owner_user_id
      into v_mentor_owner_user_id
    from public.mentor_profiles profile
    where profile.id = v_order.mentor_id;

    insert into public.user_notification_outbox (
      recipient_user_id,
      category,
      notification_type,
      title,
      summary,
      content,
      related_type,
      related_id,
      route_path,
      delivery_payload,
      event_key
    )
    select
      recipient.recipient_user_id,
      'consultation',
      'mentor_order_status',
      '本次咨询已按时完成',
      format('%s 分钟服务窗口已结束，系统已自动完成订单。', v_window_minutes),
      case
        when recipient.audience = 'mentor' then '聊天记录会继续保留，可随时返回查看。'
        else '聊天记录会继续保留，现在可以评价本次咨询。'
      end,
      'mentor_consultation_order',
      p_order_id::text || ':service_window_auto_completed',
      '/pages-sub-consultation/consultation/mentor-chat?mentorId=' || v_order.mentor_id::text
        || '&orderId=' || p_order_id::text
        || '&role=' || recipient.audience
        || '&from=' || case when recipient.audience = 'mentor' then 'mentor-center' else 'my-consultations' end,
      jsonb_build_object(
        'schema_version', 1,
        'event', 'service_window_auto_completed',
        'title', '本次咨询已按时完成',
        'body', format('%s 分钟服务窗口已结束，系统已自动完成订单。', v_window_minutes),
        'route_path', '/pages-sub-consultation/consultation/mentor-chat?mentorId=' || v_order.mentor_id::text
          || '&orderId=' || p_order_id::text
          || '&role=' || recipient.audience
          || '&from=' || case when recipient.audience = 'mentor' then 'mentor-center' else 'my-consultations' end,
        'related_type', 'mentor_consultation_order',
        'related_id', p_order_id::text || ':service_window_auto_completed',
        'surface', 'mentor_order',
        'audience', recipient.audience,
        'order_id', p_order_id,
        'mentor_id', v_order.mentor_id,
        'order_status', 'completed',
        'service_ends_at', v_service_ends_at
      ),
      'mentor-order-auto-completed:' || p_order_id::text || ':' || recipient.audience
    from (
      values
        (v_order.applicant_user_id, 'applicant'::text),
        (v_mentor_owner_user_id, 'mentor'::text)
    ) as recipient(recipient_user_id, audience)
    where recipient.recipient_user_id is not null
    on conflict (recipient_user_id, event_key) do nothing;

    -- 已结束的预约时段不应长期残留为 booked。若时段自身尚未到期，
    -- 保持 booked 直到后台的 ends_at 清理，避免被重新预约。
    if v_order.consultation_type = 'booking' and v_order.slot_id is not null then
      update public.mentor_availability_slots slot
      set status = 'expired'
      where slot.id = v_order.slot_id
        and slot.status = 'booked'
        and slot.ends_at <= p_now;
    end if;

    return next v_order;
  end if;
  return;
end;
$$;

revoke all on function public.auto_complete_expired_mentor_consultation_order(uuid, timestamptz)
  from public, anon, authenticated;
grant execute on function public.auto_complete_expired_mentor_consultation_order(uuid, timestamptz)
  to service_role;

create or replace function public.auto_complete_expired_mentor_consultation_orders(
  p_limit integer default 200,
  p_now timestamptz default now()
)
returns setof public.mentor_consultation_orders
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_order_id uuid;
  v_completed public.mentor_consultation_orders%rowtype;
begin
  for v_order_id in
    select orders.id
    from public.mentor_consultation_orders orders
    where orders.order_status = 'in_progress'
      and orders.service_ends_at is not null
      and orders.service_ends_at <= p_now
      and not exists (
        select 1
        from public.mentor_consultation_reports report
        where report.order_id = orders.id
          and report.status in ('pending', 'reviewing')
      )
      and not exists (
        select 1
        from public.mentor_consultation_report_appeals appeal
        join public.mentor_consultation_reports report
          on report.id = appeal.report_id
        where report.order_id = orders.id
          and appeal.status in ('pending', 'reviewing')
    )
    order by orders.service_ends_at, orders.id
    limit greatest(1, least(coalesce(p_limit, 200), 500))
  loop
    select completed.*
      into v_completed
    from public.auto_complete_expired_mentor_consultation_order(
      v_order_id,
      p_now
    ) completed;

    if found then
      return next v_completed;
    end if;
  end loop;
  return;
end;
$$;

revoke all on function public.auto_complete_expired_mentor_consultation_orders(integer, timestamptz)
  from public, anon, authenticated;
grant execute on function public.auto_complete_expired_mentor_consultation_orders(integer, timestamptz)
  to service_role;

-- 让 PostgREST 立即识别新 RPC。
notify pgrst, 'reload schema';

commit;
