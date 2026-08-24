-- 前辈咨询订单的结算确认、争议裁决与审计事件闭环。
-- 在 Supabase SQL Editor 中执行一次；依赖 mentor_consultation.sql 和 mentor_consultation_reports.sql。

begin;

alter table public.mentor_consultation_orders
  add column if not exists applicant_completion_confirmed_at timestamptz,
  add column if not exists mentor_completion_confirmed_at timestamptz,
  add column if not exists refund_amount_cents integer not null default 0
    check (refund_amount_cents between 0 and 100000),
  add column if not exists refund_reference text;

alter table public.mentor_consultation_reports
  add column if not exists respondent_user_id uuid references public.users(id) on delete restrict,
  add column if not exists respondent_content text
    check (respondent_content is null or char_length(btrim(respondent_content)) between 20 and 500),
  add column if not exists responded_at timestamptz,
  add column if not exists resolution text not null default 'none'
    check (resolution in ('none', 'continue_service', 'refund_full', 'refund_partial', 'close_service', 'warn_participant')),
  add column if not exists refund_amount_cents integer not null default 0
    check (refund_amount_cents between 0 and 100000);

-- 早期迁移的 resolution 检查约束不含“部分退款”；统一替换为当前裁决集合。
do $$
declare
  constraint_name text;
begin
  for constraint_name in
    select conname
    from pg_constraint
    where conrelid = 'public.mentor_consultation_reports'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) like '%resolution%'
  loop
    execute format('alter table public.mentor_consultation_reports drop constraint %I', constraint_name);
  end loop;

  alter table public.mentor_consultation_reports
    add constraint mentor_consultation_reports_resolution_check
    check (resolution in ('none', 'continue_service', 'refund_full', 'refund_partial', 'close_service', 'warn_participant'));
end $$;

alter table public.mentor_consultation_report_evidence
  add column if not exists submitter_role text not null default 'reporter'
    check (submitter_role in ('reporter', 'respondent'));

-- 历史记录在早期版本中已保存目标用户；对前辈目标补齐其档案归属人。
update public.mentor_consultation_reports report
set respondent_user_id = coalesce(report.target_user_id, mentor.owner_user_id)
from public.mentor_profiles mentor
where report.respondent_user_id is null
  and report.target_role = 'mentor'
  and report.target_mentor_id = mentor.id;

update public.mentor_consultation_reports
set respondent_user_id = target_user_id
where respondent_user_id is null
  and target_user_id is not null;

do $$
begin
  if not exists (
    select 1
    from public.mentor_consultation_reports
    where respondent_user_id is null
  ) then
    alter table public.mentor_consultation_reports
      alter column respondent_user_id set not null;
  end if;
end $$;

create table if not exists public.mentor_consultation_order_events (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.mentor_consultation_orders(id) on delete restrict,
  actor_user_id uuid references public.users(id) on delete set null,
  actor_role text not null check (actor_role in ('applicant', 'mentor', 'admin', 'system')),
  event_type text not null check (char_length(btrim(event_type)) between 1 and 80),
  details jsonb not null default '{}'::jsonb check (jsonb_typeof(details) = 'object'),
  created_at timestamptz not null default now()
);

create index if not exists idx_mentor_consultation_order_events_order_created
  on public.mentor_consultation_order_events (order_id, created_at desc);

create index if not exists idx_mentor_consultation_reports_resolution_created
  on public.mentor_consultation_reports (resolution, created_at desc);

create index if not exists idx_mentor_consultation_reports_respondent_created
  on public.mentor_consultation_reports (respondent_user_id, created_at desc);

create index if not exists idx_mentor_consultation_report_evidence_submitter_created
  on public.mentor_consultation_report_evidence (report_id, submitter_role, created_at);

alter table public.mentor_consultation_order_events enable row level security;

drop policy if exists "participants can read own consultation reports" on public.mentor_consultation_reports;
drop policy if exists "participants can read consultation reports" on public.mentor_consultation_reports;
create policy "participants can read consultation reports"
  on public.mentor_consultation_reports for select
  using (
    auth.uid() = reporter_user_id
    or auth.uid() = respondent_user_id
    or auth.uid() = target_user_id
  );

drop policy if exists "reporters can read their report evidence" on public.mentor_consultation_report_evidence;
drop policy if exists "report participants can read report evidence" on public.mentor_consultation_report_evidence;
create policy "report participants can read report evidence"
  on public.mentor_consultation_report_evidence for select
  using (
    exists (
      select 1
      from public.mentor_consultation_reports report
      where report.id = mentor_consultation_report_evidence.report_id
        and (
          report.reporter_user_id = auth.uid()
          or report.respondent_user_id = auth.uid()
          or report.target_user_id = auth.uid()
        )
    )
  );

drop policy if exists "reporters can create their report evidence" on public.mentor_consultation_report_evidence;
drop policy if exists "report participants can create report evidence" on public.mentor_consultation_report_evidence;
create policy "report participants can create report evidence"
  on public.mentor_consultation_report_evidence for insert
  with check (
    exists (
      select 1
      from public.mentor_consultation_reports report
      where report.id = mentor_consultation_report_evidence.report_id
        and (
          (report.reporter_user_id = auth.uid() and mentor_consultation_report_evidence.submitter_role = 'reporter')
          or (
            (report.respondent_user_id = auth.uid() or report.target_user_id = auth.uid())
            and mentor_consultation_report_evidence.submitter_role = 'respondent'
          )
        )
    )
  );

drop policy if exists "consultation participants can read order events" on public.mentor_consultation_order_events;
create policy "consultation participants can read order events"
  on public.mentor_consultation_order_events for select
  using (
    exists (
      select 1
      from public.mentor_consultation_orders orders
      left join public.mentor_profiles profile on profile.id = orders.mentor_id
      where orders.id = mentor_consultation_order_events.order_id
        and (orders.applicant_user_id = auth.uid() or profile.owner_user_id = auth.uid())
    )
  );

commit;
