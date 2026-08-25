-- 导师咨询第二批可靠性基础：订单幂等、预约预占、通知 outbox 与双向账本。
-- 执行位置：Supabase SQL Editor。
-- 前置依赖：mentor_consultation.sql、mentor_consultation_dispute_resolution.sql、
--           mentor_consultation_message_delivery.sql、user_notifications.sql。
-- 本迁移不接入任何真实支付/退款/提现渠道；demo 与 real 账本完全隔离。

begin;

create extension if not exists "pgcrypto";

-- ---------------------------------------------------------------------------
-- 1. 客户端订单幂等与预约时段支付前预占
-- ---------------------------------------------------------------------------

alter table public.mentor_consultation_orders
  add column if not exists client_order_id text,
  add column if not exists request_fingerprint text,
  add column if not exists payment_expires_at timestamptz,
  add column if not exists payment_mode text not null default 'real';

update public.mentor_consultation_orders
set payment_mode = 'demo'
where upper(coalesce(payment_reference, '')) like 'DEMO-%'
   or upper(coalesce(payment_reference, '')) like 'MOCK-%';

-- 旧版待支付订单没有原子预占依据；统一给予“立即过期”标记，由生命周期安全关闭。
update public.mentor_consultation_orders
set payment_expires_at = now()
where order_status = 'pending_payment'
  and payment_status in ('unpaid', 'failed')
  and payment_expires_at is null;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'mentor_consultation_orders_client_order_id_check'
      and conrelid = 'public.mentor_consultation_orders'::regclass
  ) then
    alter table public.mentor_consultation_orders
      add constraint mentor_consultation_orders_client_order_id_check
      check (client_order_id is null or char_length(btrim(client_order_id)) between 1 and 80);
  end if;
  if not exists (
    select 1 from pg_constraint
    where conname = 'mentor_consultation_orders_request_fingerprint_check'
      and conrelid = 'public.mentor_consultation_orders'::regclass
  ) then
    alter table public.mentor_consultation_orders
      add constraint mentor_consultation_orders_request_fingerprint_check
      check (request_fingerprint is null or char_length(btrim(request_fingerprint)) between 16 and 128);
  end if;
  if not exists (
    select 1 from pg_constraint
    where conname = 'mentor_consultation_orders_payment_mode_check'
      and conrelid = 'public.mentor_consultation_orders'::regclass
  ) then
    alter table public.mentor_consultation_orders
      add constraint mentor_consultation_orders_payment_mode_check
      check (payment_mode in ('demo', 'real'));
  end if;
end $$;

create unique index if not exists uq_mentor_consultation_orders_client_order
  on public.mentor_consultation_orders (applicant_user_id, client_order_id)
  where client_order_id is not null;

create index if not exists idx_mentor_consultation_orders_payment_expiry
  on public.mentor_consultation_orders (payment_expires_at)
  where order_status = 'pending_payment';

-- 旧 status 约束不包含 held，替换为当前状态集合。
do $$
declare
  constraint_name text;
begin
  for constraint_name in
    select conname
    from pg_constraint
    where conrelid = 'public.mentor_availability_slots'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) like '%status%'
  loop
    execute format(
      'alter table public.mentor_availability_slots drop constraint %I',
      constraint_name
    );
  end loop;

  alter table public.mentor_availability_slots
    add constraint mentor_availability_slots_status_check
    check (status in ('available', 'held', 'booked', 'expired', 'closed'));
end $$;

alter table public.mentor_availability_slots
  add column if not exists held_order_id uuid,
  add column if not exists hold_expires_at timestamptz;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'mentor_availability_slots_held_order_fk'
      and conrelid = 'public.mentor_availability_slots'::regclass
  ) then
    alter table public.mentor_availability_slots
      add constraint mentor_availability_slots_held_order_fk
      foreign key (held_order_id)
      references public.mentor_consultation_orders(id)
      on delete set null;
  end if;
  if not exists (
    select 1 from pg_constraint
    where conname = 'mentor_availability_slots_hold_shape_check'
      and conrelid = 'public.mentor_availability_slots'::regclass
  ) then
    alter table public.mentor_availability_slots
      add constraint mentor_availability_slots_hold_shape_check
      check (
        (status = 'held' and held_order_id is not null and hold_expires_at is not null)
        or
        (status <> 'held' and held_order_id is null and hold_expires_at is null)
      );
  end if;
end $$;

create unique index if not exists uq_mentor_availability_slots_held_order
  on public.mentor_availability_slots (held_order_id)
  where held_order_id is not null;

create index if not exists idx_mentor_availability_slots_hold_expiry
  on public.mentor_availability_slots (hold_expires_at)
  where status = 'held';

create or replace function public.create_mentor_consultation_order_with_hold(
  p_order_no text,
  p_applicant_user_id uuid,
  p_mentor_id uuid,
  p_slot_id uuid,
  p_consultation_type text,
  p_questionnaire jsonb,
  p_price_cents integer,
  p_consultation_window_minutes smallint,
  p_client_order_id text,
  p_request_fingerprint text,
  p_payment_mode text,
  p_payment_expires_at timestamptz
)
returns setof public.mentor_consultation_orders
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  existing_order public.mentor_consultation_orders%rowtype;
  created_order public.mentor_consultation_orders%rowtype;
  selected_mentor public.mentor_profiles%rowtype;
  selected_slot public.mentor_availability_slots%rowtype;
begin
  if p_applicant_user_id is null
     or p_mentor_id is null
     or btrim(coalesce(p_order_no, '')) = ''
     or btrim(coalesce(p_client_order_id, '')) = ''
     or btrim(coalesce(p_request_fingerprint, '')) = '' then
    raise exception 'invalid_order_request';
  end if;
  if p_consultation_type not in ('instant', 'booking') then
    raise exception 'invalid_consultation_type';
  end if;
  if p_payment_mode not in ('demo', 'real') then
    raise exception 'invalid_payment_mode';
  end if;
  if p_payment_expires_at is null or p_payment_expires_at <= now() then
    raise exception 'invalid_payment_expiry';
  end if;

  -- 同一用户同一客户端键串行化，解决并发重试先后穿透唯一索引的问题。
  perform pg_advisory_xact_lock(
    hashtextextended(p_applicant_user_id::text || ':' || btrim(p_client_order_id), 0)
  );

  select orders.*
  into existing_order
  from public.mentor_consultation_orders orders
  where orders.applicant_user_id = p_applicant_user_id
    and orders.client_order_id = btrim(p_client_order_id)
  limit 1;

  if found then
    if existing_order.request_fingerprint is distinct from btrim(p_request_fingerprint) then
      raise exception 'client_order_conflict';
    end if;
    return next existing_order;
    return;
  end if;

  select mentors.*
  into selected_mentor
  from public.mentor_profiles mentors
  where mentors.id = p_mentor_id
    and mentors.verification_status = 'verified'
    and mentors.is_published = true;

  if not found then
    raise exception 'mentor_unavailable';
  end if;
  if selected_mentor.owner_user_id = p_applicant_user_id then
    raise exception 'self_consultation_not_allowed';
  end if;

  if p_consultation_type = 'booking' then
    if p_slot_id is null or not selected_mentor.accepts_booking then
      raise exception 'booking_unavailable';
    end if;

    select slots.*
    into selected_slot
    from public.mentor_availability_slots slots
    where slots.id = p_slot_id
    for update;

    if not found or selected_slot.mentor_id <> p_mentor_id then
      raise exception 'slot_mismatch';
    end if;

    -- 任意创建请求都可清理已过期的旧预占；订单与时段在同一事务内关闭/释放。
    if selected_slot.status = 'held'
       and selected_slot.hold_expires_at is not null
       and selected_slot.hold_expires_at <= now() then
      update public.mentor_consultation_orders
      set order_status = 'cancelled',
          ended_at = now(),
          updated_at = now()
      where id = selected_slot.held_order_id
        and order_status = 'pending_payment'
        and payment_status in ('unpaid', 'failed');

      update public.mentor_availability_slots
      set status = case when selected_slot.ends_at <= now() then 'expired' else 'available' end,
          held_order_id = null,
          hold_expires_at = null,
          updated_at = now()
      where id = selected_slot.id;

      select slots.*
      into selected_slot
      from public.mentor_availability_slots slots
      where slots.id = p_slot_id
      for update;
    end if;

    if selected_slot.status <> 'available' or selected_slot.starts_at <= now() then
      raise exception 'slot_unavailable';
    end if;
  elsif p_slot_id is not null then
    raise exception 'instant_slot_not_allowed';
  end if;

  insert into public.mentor_consultation_orders (
    order_no,
    applicant_user_id,
    mentor_id,
    slot_id,
    consultation_type,
    order_status,
    payment_status,
    questionnaire,
    price_cents,
    consultation_window_minutes,
    client_order_id,
    request_fingerprint,
    payment_expires_at,
    payment_mode
  )
  values (
    btrim(p_order_no),
    p_applicant_user_id,
    p_mentor_id,
    p_slot_id,
    p_consultation_type,
    'pending_payment',
    'unpaid',
    coalesce(p_questionnaire, '{}'::jsonb),
    greatest(0, p_price_cents),
    p_consultation_window_minutes,
    btrim(p_client_order_id),
    btrim(p_request_fingerprint),
    p_payment_expires_at,
    p_payment_mode
  )
  returning * into created_order;

  if p_consultation_type = 'booking' then
    update public.mentor_availability_slots
    set status = 'held',
        held_order_id = created_order.id,
        hold_expires_at = p_payment_expires_at,
        updated_at = now()
    where id = p_slot_id
      and status = 'available';

    if not found then
      raise exception 'slot_unavailable';
    end if;
  end if;

  return next created_order;
end;
$$;

revoke all on function public.create_mentor_consultation_order_with_hold(
  text, uuid, uuid, uuid, text, jsonb, integer, smallint, text, text, text, timestamptz
) from public, anon, authenticated;
grant execute on function public.create_mentor_consultation_order_with_hold(
  text, uuid, uuid, uuid, text, jsonb, integer, smallint, text, text, text, timestamptz
) to service_role;

create or replace function public.expire_mentor_consultation_payment_hold(
  p_order_id uuid,
  p_now timestamptz default now()
)
returns setof public.mentor_consultation_orders
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  selected_order public.mentor_consultation_orders%rowtype;
begin
  select orders.*
  into selected_order
  from public.mentor_consultation_orders orders
  where orders.id = p_order_id
  for update;

  if not found then
    return;
  end if;

  if selected_order.order_status = 'pending_payment'
     and selected_order.payment_status in ('unpaid', 'failed')
     and selected_order.payment_expires_at is not null
     and selected_order.payment_expires_at <= p_now then
    update public.mentor_consultation_orders
    set order_status = 'cancelled',
        ended_at = p_now,
        updated_at = p_now
    where id = selected_order.id
    returning * into selected_order;

    if selected_order.slot_id is not null then
      update public.mentor_availability_slots
      set status = case when ends_at <= p_now then 'expired' else 'available' end,
          held_order_id = null,
          hold_expires_at = null,
          updated_at = p_now
      where id = selected_order.slot_id
        and status = 'held'
        and held_order_id = selected_order.id;
    end if;
  end if;

  return next selected_order;
end;
$$;

revoke all on function public.expire_mentor_consultation_payment_hold(uuid, timestamptz)
  from public, anon, authenticated;
grant execute on function public.expire_mentor_consultation_payment_hold(uuid, timestamptz)
  to service_role;

create or replace function public.confirm_mentor_consultation_payment(
  p_order_id uuid,
  p_payment_reference text,
  p_response_expires_at timestamptz,
  p_now timestamptz default now()
)
returns setof public.mentor_consultation_orders
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  selected_order public.mentor_consultation_orders%rowtype;
  selected_slot public.mentor_availability_slots%rowtype;
begin
  select orders.*
  into selected_order
  from public.mentor_consultation_orders orders
  where orders.id = p_order_id
  for update;

  if not found then
    return;
  end if;
  if selected_order.payment_status = 'paid' then
    return next selected_order;
    return;
  end if;
  if selected_order.order_status <> 'pending_payment'
     or selected_order.payment_status not in ('unpaid', 'failed') then
    raise exception 'order_not_payable';
  end if;
  if selected_order.payment_expires_at is not null
     and selected_order.payment_expires_at <= p_now then
    update public.mentor_consultation_orders
    set order_status = 'cancelled',
        ended_at = p_now,
        updated_at = p_now
    where id = selected_order.id
    returning * into selected_order;

    if selected_order.slot_id is not null then
      update public.mentor_availability_slots
      set status = case when ends_at <= p_now then 'expired' else 'available' end,
          held_order_id = null,
          hold_expires_at = null,
          updated_at = p_now
      where id = selected_order.slot_id
        and status = 'held'
        and held_order_id = selected_order.id;
    end if;
    return next selected_order;
    return;
  end if;

  if selected_order.consultation_type = 'booking' then
    select slots.*
    into selected_slot
    from public.mentor_availability_slots slots
    where slots.id = selected_order.slot_id
    for update;

    if not found
       or selected_slot.status <> 'held'
       or selected_slot.held_order_id <> selected_order.id
       or selected_slot.hold_expires_at <= p_now then
      raise exception 'booking_hold_lost';
    end if;

    update public.mentor_availability_slots
    set status = 'booked',
        held_order_id = null,
        hold_expires_at = null,
        updated_at = p_now
    where id = selected_slot.id;

    update public.mentor_consultation_orders
    set order_status = 'booked',
        payment_status = 'paid',
        payment_reference = btrim(p_payment_reference),
        payment_expires_at = null,
        expires_at = null,
        updated_at = p_now
    where id = selected_order.id
    returning * into selected_order;
  else
    update public.mentor_consultation_orders
    set order_status = 'pending_accept',
        payment_status = 'paid',
        payment_reference = btrim(p_payment_reference),
        payment_expires_at = null,
        expires_at = p_response_expires_at,
        updated_at = p_now
    where id = selected_order.id
    returning * into selected_order;
  end if;

  return next selected_order;
end;
$$;

revoke all on function public.confirm_mentor_consultation_payment(
  uuid, text, timestamptz, timestamptz
) from public, anon, authenticated;
grant execute on function public.confirm_mentor_consultation_payment(
  uuid, text, timestamptz, timestamptz
) to service_role;

create or replace function public.register_mentor_consultation_late_payment(
  p_order_id uuid,
  p_payment_reference text,
  p_refund_reference text,
  p_now timestamptz default now()
)
returns setof public.mentor_consultation_orders
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  selected_order public.mentor_consultation_orders%rowtype;
begin
  select orders.*
  into selected_order
  from public.mentor_consultation_orders orders
  where orders.id = p_order_id
  for update;

  if not found then
    return;
  end if;
  if selected_order.payment_status in ('refunding', 'refunded')
     and selected_order.payment_reference = btrim(p_payment_reference) then
    return next selected_order;
    return;
  end if;
  if selected_order.order_status not in ('pending_payment', 'cancelled')
     or selected_order.payment_status not in ('unpaid', 'failed') then
    raise exception 'late_payment_not_registerable';
  end if;

  update public.mentor_consultation_orders
  set order_status = 'cancelled',
      payment_status = 'refunding',
      payment_reference = btrim(p_payment_reference),
      payment_expires_at = null,
      ended_at = coalesce(ended_at, p_now),
      refund_amount_cents = price_cents,
      refund_reference = btrim(p_refund_reference),
      updated_at = p_now
  where id = selected_order.id
  returning * into selected_order;

  if selected_order.slot_id is not null then
    update public.mentor_availability_slots
    set status = case when ends_at <= p_now then 'expired' else 'available' end,
        held_order_id = null,
        hold_expires_at = null,
        updated_at = p_now
    where id = selected_order.slot_id
      and status = 'held'
      and held_order_id = selected_order.id;
  end if;

  return next selected_order;
end;
$$;

revoke all on function public.register_mentor_consultation_late_payment(
  uuid, text, text, timestamptz
) from public, anon, authenticated;
grant execute on function public.register_mentor_consultation_late_payment(
  uuid, text, text, timestamptz
) to service_role;

-- 真实退款命令与订单更新同事务入队；微信适配器上线后只需领取此队列并回传结果。
create table if not exists public.mentor_payment_operation_outbox (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.mentor_consultation_orders(id) on delete restrict,
  operation_type text not null check (operation_type in ('refund')),
  fund_mode text not null check (fund_mode in ('demo', 'real')),
  provider text,
  idempotency_key text not null unique check (char_length(btrim(idempotency_key)) between 3 and 255),
  payment_reference text not null,
  refund_reference text not null,
  amount_cents integer not null check (amount_cents > 0),
  status text not null default 'pending'
    check (status in ('pending', 'processing', 'succeeded', 'failed')),
  attempts integer not null default 0 check (attempts >= 0),
  available_at timestamptz not null default now(),
  locked_at timestamptz,
  completed_at timestamptz,
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_mentor_payment_operation_outbox_claim
  on public.mentor_payment_operation_outbox (status, available_at, created_at)
  where status in ('pending', 'processing');

drop trigger if exists set_mentor_payment_operation_outbox_updated_at
  on public.mentor_payment_operation_outbox;
create trigger set_mentor_payment_operation_outbox_updated_at
before update on public.mentor_payment_operation_outbox
for each row execute function public.set_updated_at();

alter table public.mentor_payment_operation_outbox enable row level security;

create or replace function public.sync_mentor_refund_operation_outbox()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if new.payment_mode = 'real'
     and new.payment_status = 'refunding'
     and old.payment_status is distinct from new.payment_status
     and new.payment_reference is not null
     and new.refund_reference is not null
     and new.refund_amount_cents > 0 then
    insert into public.mentor_payment_operation_outbox (
      order_id,
      operation_type,
      fund_mode,
      idempotency_key,
      payment_reference,
      refund_reference,
      amount_cents
    ) values (
      new.id,
      'refund',
      new.payment_mode,
      'consultation-refund:' || new.id::text || ':' || new.refund_reference,
      new.payment_reference,
      new.refund_reference,
      new.refund_amount_cents
    )
    on conflict (idempotency_key) do nothing;
  elsif new.payment_status = 'refunded'
        and old.payment_status is distinct from new.payment_status
        and new.refund_reference is not null then
    update public.mentor_payment_operation_outbox
    set status = 'succeeded',
        completed_at = now(),
        locked_at = null,
        last_error = null,
        updated_at = now()
    where order_id = new.id
      and refund_reference = new.refund_reference
      and status in ('pending', 'processing');
  elsif new.payment_status = 'failed'
        and old.payment_status = 'refunding'
        and new.refund_reference is not null then
    update public.mentor_payment_operation_outbox
    set status = 'failed',
        completed_at = now(),
        locked_at = null,
        updated_at = now()
    where order_id = new.id
      and refund_reference = new.refund_reference
      and status in ('pending', 'processing');
  end if;
  return new;
end;
$$;

drop trigger if exists sync_mentor_refund_operation_outbox
  on public.mentor_consultation_orders;
create trigger sync_mentor_refund_operation_outbox
after update of payment_status, refund_reference, refund_amount_cents
on public.mentor_consultation_orders
for each row execute function public.sync_mentor_refund_operation_outbox();

insert into public.mentor_payment_operation_outbox (
  order_id,
  operation_type,
  fund_mode,
  idempotency_key,
  payment_reference,
  refund_reference,
  amount_cents
)
select
  orders.id,
  'refund',
  orders.payment_mode,
  'consultation-refund:' || orders.id::text || ':' || orders.refund_reference,
  orders.payment_reference,
  orders.refund_reference,
  orders.refund_amount_cents
from public.mentor_consultation_orders orders
where orders.payment_mode = 'real'
  and orders.payment_status = 'refunding'
  and orders.payment_reference is not null
  and orders.refund_reference is not null
  and orders.refund_amount_cents > 0
on conflict (idempotency_key) do nothing;

create or replace function public.claim_mentor_payment_operations(
  p_provider text,
  p_limit integer default 50,
  p_now timestamptz default now()
)
returns setof public.mentor_payment_operation_outbox
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  return query
  with candidates as (
    select outbox.id
    from public.mentor_payment_operation_outbox outbox
    where (
      (outbox.status = 'pending' and outbox.available_at <= p_now)
      or
      (outbox.status = 'processing' and outbox.locked_at < p_now - interval '5 minutes')
    )
    order by outbox.available_at, outbox.created_at
    for update skip locked
    limit greatest(1, least(coalesce(p_limit, 50), 200))
  )
  update public.mentor_payment_operation_outbox outbox
  set status = 'processing',
      provider = nullif(btrim(coalesce(p_provider, '')), ''),
      attempts = outbox.attempts + 1,
      locked_at = p_now,
      last_error = null,
      updated_at = p_now
  from candidates
  where outbox.id = candidates.id
  returning outbox.*;
end;
$$;

revoke all on function public.claim_mentor_payment_operations(text, integer, timestamptz)
  from public, anon, authenticated;
grant execute on function public.claim_mentor_payment_operations(text, integer, timestamptz)
  to service_role;

-- ---------------------------------------------------------------------------
-- 2. 通知 outbox：源业务只入队，后台可重试投递到 user_notifications
-- ---------------------------------------------------------------------------

create table if not exists public.user_notification_outbox (
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
  status text not null default 'pending'
    check (status in ('pending', 'processing', 'delivered', 'failed')),
  attempts integer not null default 0 check (attempts >= 0),
  available_at timestamptz not null default now(),
  locked_at timestamptz,
  delivered_at timestamptz,
  delivered_notification_id uuid references public.user_notifications(id) on delete set null,
  last_error text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint user_notification_outbox_route_path_check
    check (route_path is null or left(route_path, 1) = '/'),
  constraint user_notification_outbox_delivery_payload_object_check
    check (jsonb_typeof(delivery_payload) = 'object')
);

create unique index if not exists uq_user_notification_outbox_recipient_event
  on public.user_notification_outbox (recipient_user_id, event_key);

create index if not exists idx_user_notification_outbox_delivery
  on public.user_notification_outbox (status, available_at, created_at)
  where status in ('pending', 'processing');

drop trigger if exists set_user_notification_outbox_updated_at
  on public.user_notification_outbox;
create trigger set_user_notification_outbox_updated_at
before update on public.user_notification_outbox
for each row execute function public.set_updated_at();

alter table public.user_notification_outbox enable row level security;

create or replace function public.claim_user_notification_outbox(
  p_limit integer default 50,
  p_now timestamptz default now()
)
returns setof public.user_notification_outbox
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  return query
  with candidates as (
    select outbox.id
    from public.user_notification_outbox outbox
    where (
      (outbox.status = 'pending' and outbox.available_at <= p_now)
      or
      (outbox.status = 'processing' and outbox.locked_at < p_now - interval '5 minutes')
    )
    order by outbox.available_at, outbox.created_at
    for update skip locked
    limit greatest(1, least(coalesce(p_limit, 50), 200))
  )
  update public.user_notification_outbox outbox
  set status = 'processing',
      attempts = outbox.attempts + 1,
      locked_at = p_now,
      last_error = null,
      updated_at = p_now
  from candidates
  where outbox.id = candidates.id
  returning outbox.*;
end;
$$;

revoke all on function public.claim_user_notification_outbox(integer, timestamptz)
  from public, anon, authenticated;
grant execute on function public.claim_user_notification_outbox(integer, timestamptz)
  to service_role;

-- ---------------------------------------------------------------------------
-- 3. 渠道无关不可变双向账本。demo/real 是账本维度，不允许混算。
-- ---------------------------------------------------------------------------

create table if not exists public.wallet_accounts (
  id uuid primary key default gen_random_uuid(),
  account_code text not null unique check (char_length(btrim(account_code)) between 3 and 180),
  owner_user_id uuid references public.users(id) on delete restrict,
  account_type text not null
    check (account_type in (
      'platform_cash', 'consultation_escrow', 'mentor_pending',
      'mentor_available', 'user_wallet', 'platform_revenue'
    )),
  balance_class text not null check (balance_class in ('asset', 'liability', 'revenue', 'expense')),
  fund_mode text not null check (fund_mode in ('demo', 'real')),
  currency text not null default 'CNY' check (currency = 'CNY'),
  created_at timestamptz not null default now()
);

create unique index if not exists uq_wallet_accounts_owner_type_mode_currency
  on public.wallet_accounts (owner_user_id, account_type, fund_mode, currency)
  where owner_user_id is not null
    and account_type in ('mentor_pending', 'mentor_available', 'user_wallet');

create table if not exists public.wallet_transactions (
  id uuid primary key default gen_random_uuid(),
  transaction_no text not null unique check (char_length(btrim(transaction_no)) between 3 and 100),
  event_key text not null unique check (char_length(btrim(event_key)) between 3 and 255),
  business_type text not null check (char_length(btrim(business_type)) between 1 and 80),
  business_id text,
  fund_mode text not null check (fund_mode in ('demo', 'real')),
  currency text not null default 'CNY' check (currency = 'CNY'),
  gross_amount_cents integer not null check (gross_amount_cents > 0),
  status text not null default 'posted' check (status in ('posted', 'reversed')),
  description text not null default '',
  metadata jsonb not null default '{}'::jsonb check (jsonb_typeof(metadata) = 'object'),
  occurred_at timestamptz not null default now(),
  created_at timestamptz not null default now()
);

create table if not exists public.wallet_entries (
  id uuid primary key default gen_random_uuid(),
  transaction_id uuid not null references public.wallet_transactions(id) on delete restrict,
  account_id uuid not null references public.wallet_accounts(id) on delete restrict,
  direction text not null check (direction in ('debit', 'credit')),
  amount_cents integer not null check (amount_cents > 0),
  created_at timestamptz not null default now()
);

create index if not exists idx_wallet_entries_account_created
  on public.wallet_entries (account_id, created_at desc);
create index if not exists idx_wallet_transactions_business
  on public.wallet_transactions (business_type, business_id, created_at desc);
create index if not exists idx_wallet_transactions_mode_created
  on public.wallet_transactions (fund_mode, created_at desc);

create or replace function public.reject_wallet_immutable_mutation()
returns trigger
language plpgsql
as $$
begin
  raise exception 'wallet_ledger_is_immutable';
end;
$$;

drop trigger if exists wallet_transactions_immutable on public.wallet_transactions;
create trigger wallet_transactions_immutable
before update or delete on public.wallet_transactions
for each row execute function public.reject_wallet_immutable_mutation();

drop trigger if exists wallet_entries_immutable on public.wallet_entries;
create trigger wallet_entries_immutable
before update or delete on public.wallet_entries
for each row execute function public.reject_wallet_immutable_mutation();

create or replace function public.validate_wallet_transaction_balance()
returns trigger
language plpgsql
as $$
declare
  target_transaction_id uuid;
  debit_total bigint;
  credit_total bigint;
begin
  if tg_table_name = 'wallet_entries' then
    target_transaction_id := new.transaction_id;
  else
    target_transaction_id := new.id;
  end if;
  select
    coalesce(sum(case when direction = 'debit' then amount_cents else 0 end), 0),
    coalesce(sum(case when direction = 'credit' then amount_cents else 0 end), 0)
  into debit_total, credit_total
  from public.wallet_entries
  where transaction_id = target_transaction_id;

  if debit_total <= 0 or debit_total <> credit_total then
    raise exception 'wallet_transaction_unbalanced';
  end if;
  return new;
end;
$$;

drop trigger if exists wallet_transaction_balance_on_transaction on public.wallet_transactions;
create constraint trigger wallet_transaction_balance_on_transaction
after insert on public.wallet_transactions
deferrable initially deferred
for each row execute function public.validate_wallet_transaction_balance();

drop trigger if exists wallet_transaction_balance_on_entry on public.wallet_entries;
create constraint trigger wallet_transaction_balance_on_entry
after insert on public.wallet_entries
deferrable initially deferred
for each row execute function public.validate_wallet_transaction_balance();

create or replace function public.post_wallet_transaction(
  p_transaction_no text,
  p_event_key text,
  p_business_type text,
  p_business_id text,
  p_fund_mode text,
  p_gross_amount_cents integer,
  p_description text,
  p_metadata jsonb,
  p_entries jsonb,
  p_occurred_at timestamptz default now()
)
returns setof public.wallet_transactions
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  existing_transaction public.wallet_transactions%rowtype;
  created_transaction public.wallet_transactions%rowtype;
  entry jsonb;
  selected_account public.wallet_accounts%rowtype;
  debit_total bigint := 0;
  credit_total bigint := 0;
  entry_amount integer;
  entry_direction text;
  entry_account_code text;
  entry_owner_user_id uuid;
  entry_account_type text;
  entry_balance_class text;
begin
  if p_fund_mode not in ('demo', 'real')
     or p_gross_amount_cents <= 0
     or jsonb_typeof(p_entries) <> 'array'
     or jsonb_array_length(p_entries) < 2 then
    raise exception 'invalid_wallet_transaction';
  end if;

  perform pg_advisory_xact_lock(hashtextextended(btrim(p_event_key), 0));

  select transactions.*
  into existing_transaction
  from public.wallet_transactions transactions
  where transactions.event_key = btrim(p_event_key)
  limit 1;

  if found then
    if existing_transaction.business_type is distinct from btrim(p_business_type)
       or existing_transaction.business_id is distinct from nullif(btrim(coalesce(p_business_id, '')), '')
       or existing_transaction.fund_mode is distinct from p_fund_mode
       or existing_transaction.gross_amount_cents is distinct from p_gross_amount_cents then
      raise exception 'wallet_event_conflict';
    end if;
    return next existing_transaction;
    return;
  end if;

  for entry in select value from jsonb_array_elements(p_entries)
  loop
    entry_amount := (entry ->> 'amount_cents')::integer;
    entry_direction := btrim(entry ->> 'direction');
    entry_account_code := btrim(entry ->> 'account_code');
    entry_owner_user_id := nullif(btrim(coalesce(entry ->> 'owner_user_id', '')), '')::uuid;
    entry_account_type := btrim(entry ->> 'account_type');
    entry_balance_class := btrim(entry ->> 'balance_class');

    if entry_amount <= 0
       or entry_direction not in ('debit', 'credit')
       or entry_account_code = '' then
      raise exception 'invalid_wallet_entry';
    end if;

    insert into public.wallet_accounts (
      account_code, owner_user_id, account_type, balance_class, fund_mode, currency
    ) values (
      entry_account_code,
      entry_owner_user_id,
      entry_account_type,
      entry_balance_class,
      p_fund_mode,
      'CNY'
    )
    on conflict (account_code) do nothing;

    select accounts.*
    into selected_account
    from public.wallet_accounts accounts
    where accounts.account_code = entry_account_code;

    if selected_account.owner_user_id is distinct from entry_owner_user_id
       or selected_account.account_type is distinct from entry_account_type
       or selected_account.balance_class is distinct from entry_balance_class
       or selected_account.fund_mode is distinct from p_fund_mode then
      raise exception 'wallet_account_conflict';
    end if;

    if entry_direction = 'debit' then
      debit_total := debit_total + entry_amount;
    else
      credit_total := credit_total + entry_amount;
    end if;
  end loop;

  if debit_total <= 0 or debit_total <> credit_total then
    raise exception 'wallet_transaction_unbalanced';
  end if;

  insert into public.wallet_transactions (
    transaction_no,
    event_key,
    business_type,
    business_id,
    fund_mode,
    gross_amount_cents,
    description,
    metadata,
    occurred_at
  ) values (
    btrim(p_transaction_no),
    btrim(p_event_key),
    btrim(p_business_type),
    nullif(btrim(coalesce(p_business_id, '')), ''),
    p_fund_mode,
    p_gross_amount_cents,
    coalesce(p_description, ''),
    coalesce(p_metadata, '{}'::jsonb),
    coalesce(p_occurred_at, now())
  )
  returning * into created_transaction;

  for entry in select value from jsonb_array_elements(p_entries)
  loop
    select accounts.*
    into selected_account
    from public.wallet_accounts accounts
    where accounts.account_code = btrim(entry ->> 'account_code');

    insert into public.wallet_entries (
      transaction_id, account_id, direction, amount_cents
    ) values (
      created_transaction.id,
      selected_account.id,
      btrim(entry ->> 'direction'),
      (entry ->> 'amount_cents')::integer
    );
  end loop;

  return next created_transaction;
end;
$$;

revoke all on function public.post_wallet_transaction(
  text, text, text, text, text, integer, text, jsonb, jsonb, timestamptz
) from public, anon, authenticated;
grant execute on function public.post_wallet_transaction(
  text, text, text, text, text, integer, text, jsonb, jsonb, timestamptz
) to service_role;

create or replace view public.wallet_user_balances
with (security_invoker = true)
as
select
  accounts.owner_user_id as user_id,
  case
    when accounts.account_type in ('mentor_pending', 'mentor_available') then 'mentor'
    else 'user'
  end as wallet_role,
  accounts.fund_mode,
  accounts.account_type,
  coalesce(sum(
    case accounts.balance_class
      when 'asset' then case entries.direction when 'debit' then entries.amount_cents else -entries.amount_cents end
      else case entries.direction when 'credit' then entries.amount_cents else -entries.amount_cents end
    end
  ), 0)::bigint as balance_cents
from public.wallet_accounts accounts
left join public.wallet_entries entries on entries.account_id = accounts.id
left join public.wallet_transactions transactions
  on transactions.id = entries.transaction_id
  and transactions.status = 'posted'
where accounts.owner_user_id is not null
  and accounts.account_type in ('mentor_pending', 'mentor_available', 'user_wallet')
  and (entries.id is null or transactions.id is not null)
group by accounts.owner_user_id, wallet_role, accounts.fund_mode, accounts.account_type;

create or replace view public.wallet_user_activity
with (security_invoker = true)
as
select
  transactions.id,
  transactions.transaction_no,
  transactions.event_key,
  transactions.business_type,
  transactions.business_id,
  transactions.fund_mode,
  transactions.currency,
  transactions.gross_amount_cents,
  transactions.status,
  transactions.description,
  transactions.metadata,
  transactions.occurred_at,
  transactions.created_at,
  transactions.metadata ->> 'applicant_user_id' as user_id,
  'user'::text as wallet_role,
  case
    when transactions.business_type in ('consultation_refund', 'consultation_income_reversed') then transactions.gross_amount_cents
    else -transactions.gross_amount_cents
  end as display_amount_cents
from public.wallet_transactions transactions
where coalesce(transactions.metadata ->> 'applicant_user_id', '') <> ''
  and transactions.business_type in ('consultation_payment', 'consultation_refund', 'consultation_income_reversed')
union all
select
  transactions.id,
  transactions.transaction_no,
  transactions.event_key,
  transactions.business_type,
  transactions.business_id,
  transactions.fund_mode,
  transactions.currency,
  transactions.gross_amount_cents,
  transactions.status,
  transactions.description,
  transactions.metadata,
  transactions.occurred_at,
  transactions.created_at,
  transactions.metadata ->> 'mentor_owner_user_id' as user_id,
  'mentor'::text as wallet_role,
  case
    when transactions.business_type = 'consultation_income_reversed' then -transactions.gross_amount_cents
    else transactions.gross_amount_cents
  end as display_amount_cents
from public.wallet_transactions transactions
where coalesce(transactions.metadata ->> 'mentor_owner_user_id', '') <> ''
  and transactions.business_type in (
    'consultation_income_pending',
    'consultation_income_settled',
    'consultation_income_reversed'
  );

create or replace view public.wallet_user_summaries
with (security_invoker = true)
as
select
  activity.user_id,
  activity.wallet_role,
  activity.fund_mode,
  coalesce(sum(
    case
      when activity.wallet_role = 'user'
       and activity.business_type = 'consultation_payment'
       and activity.display_amount_cents < 0
       and date_trunc('month', timezone('Asia/Shanghai', activity.occurred_at))
           = date_trunc('month', timezone('Asia/Shanghai', now()))
      then abs(activity.display_amount_cents)
      else 0
    end
  ), 0)::bigint as monthly_expense_cents,
  coalesce(sum(
    case
      when activity.wallet_role = 'user'
       and activity.business_type in ('consultation_refund', 'consultation_income_reversed')
       and activity.display_amount_cents > 0
       and date_trunc('month', timezone('Asia/Shanghai', activity.occurred_at))
           = date_trunc('month', timezone('Asia/Shanghai', now()))
      then activity.display_amount_cents
      else 0
    end
  ), 0)::bigint as monthly_refund_cents,
  coalesce(sum(
    case
      when activity.wallet_role = 'mentor'
       and activity.business_type in ('consultation_income_pending', 'consultation_income_reversed')
       and date_trunc('month', timezone('Asia/Shanghai', activity.occurred_at))
           = date_trunc('month', timezone('Asia/Shanghai', now()))
      then activity.display_amount_cents
      else 0
    end
  ), 0)::bigint as monthly_income_cents,
  coalesce(sum(
    case
      when activity.wallet_role = 'mentor'
       and activity.business_type in ('consultation_income_pending', 'consultation_income_reversed')
      then activity.display_amount_cents
      else 0
    end
  ), 0)::bigint as total_income_cents,
  coalesce(sum(
    case
      when activity.wallet_role = 'user'
       and activity.business_type = 'consultation_payment'
       and activity.display_amount_cents < 0
      then abs(activity.display_amount_cents)
      else 0
    end
  ), 0)::bigint as total_paid_cents
from public.wallet_user_activity activity
group by activity.user_id, activity.wallet_role, activity.fund_mode;

alter table public.wallet_accounts enable row level security;
alter table public.wallet_transactions enable row level security;
alter table public.wallet_entries enable row level security;

-- 钱包只通过 FastAPI service role 查询；客户端不直接写入或读取底层分录。

commit;
