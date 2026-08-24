-- 前辈咨询问题反馈与复核的首次响应 SLA。
-- 已执行 reports / dispute_resolution / report_appeals 迁移的环境，只需在 Supabase SQL Editor
-- 额外执行本文件一次；新环境同时更新了上述基础迁移，仍可安全重复执行本文件。

begin;

alter table public.mentor_consultation_reports
  add column if not exists first_response_due_at timestamptz,
  add column if not exists first_response_at timestamptz,
  add column if not exists priority text not null default 'normal',
  add column if not exists escalation_level smallint not null default 0,
  add column if not exists escalated_at timestamptz;

update public.mentor_consultation_reports
set first_response_due_at = created_at + interval '48 hours'
where first_response_due_at is null;

update public.mentor_consultation_reports
set first_response_at = coalesce(handled_at, updated_at, created_at)
where first_response_at is null
  and status in ('reviewing', 'resolved', 'dismissed');

alter table public.mentor_consultation_reports
  alter column first_response_due_at set not null;

alter table public.mentor_consultation_report_appeals
  add column if not exists first_response_due_at timestamptz,
  add column if not exists first_response_at timestamptz,
  add column if not exists priority text not null default 'normal',
  add column if not exists escalation_level smallint not null default 0,
  add column if not exists escalated_at timestamptz;

update public.mentor_consultation_report_appeals
set first_response_due_at = created_at + interval '48 hours'
where first_response_due_at is null;

update public.mentor_consultation_report_appeals
set first_response_at = coalesce(handled_at, updated_at, created_at)
where first_response_at is null
  and status in ('reviewing', 'resolved', 'dismissed');

alter table public.mentor_consultation_report_appeals
  alter column first_response_due_at set not null;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.mentor_consultation_reports'::regclass
      and conname = 'mentor_consultation_reports_priority_check'
  ) then
    alter table public.mentor_consultation_reports
      add constraint mentor_consultation_reports_priority_check
      check (priority in ('normal', 'high', 'urgent'));
  end if;
  if not exists (
    select 1 from pg_constraint
    where conrelid = 'public.mentor_consultation_report_appeals'::regclass
      and conname = 'mentor_consultation_report_appeals_priority_check'
  ) then
    alter table public.mentor_consultation_report_appeals
      add constraint mentor_consultation_report_appeals_priority_check
      check (priority in ('normal', 'high', 'urgent'));
  end if;
end $$;

create index if not exists idx_mentor_consultation_reports_first_response_sla
  on public.mentor_consultation_reports (status, first_response_at, first_response_due_at, escalation_level desc);

create index if not exists idx_mentor_consultation_report_appeals_first_response_sla
  on public.mentor_consultation_report_appeals (status, first_response_at, first_response_due_at, escalation_level desc);

commit;
