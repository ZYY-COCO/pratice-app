-- 前辈咨询举报与凭证数据结构。
-- 执行位置：Supabase SQL Editor。
-- 前置依赖：database/supabase_schema.sql、database/mentor_consultation.sql、database/admin_management.sql。
-- 图片文件由后端写入私有 Storage bucket；本文件只保存文件路径，不公开真实链接。

create extension if not exists "pgcrypto";

create table if not exists public.mentor_consultation_reports (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.mentor_consultation_orders(id) on delete restrict,
  reporter_user_id uuid not null references public.users(id) on delete restrict,
  reporter_role text not null check (reporter_role in ('applicant', 'mentor')),
  respondent_user_id uuid not null references public.users(id) on delete restrict,
  target_role text not null check (target_role in ('applicant', 'mentor')),
  target_user_id uuid references public.users(id) on delete restrict,
  target_mentor_id uuid references public.mentor_profiles(id) on delete restrict,
  issue_type text not null check (char_length(btrim(issue_type)) between 1 and 60),
  content text not null check (char_length(btrim(content)) between 20 and 500),
  respondent_content text check (respondent_content is null or char_length(btrim(respondent_content)) between 20 and 500),
  responded_at timestamptz,
  status text not null default 'pending'
    check (status in ('pending', 'reviewing', 'resolved', 'dismissed')),
  first_response_due_at timestamptz not null default (now() + interval '48 hours'),
  first_response_at timestamptz,
  priority text not null default 'normal'
    check (priority in ('normal', 'high', 'urgent')),
  escalation_level smallint not null default 0 check (escalation_level >= 0),
  escalated_at timestamptz,
  admin_note text check (admin_note is null or char_length(btrim(admin_note)) <= 1000),
  handled_by uuid references public.users(id) on delete set null,
  handled_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint mentor_consultation_reports_target_check check (
    (target_role = 'mentor' and target_mentor_id is not null)
    or (target_role = 'applicant' and target_user_id is not null)
  ),
  constraint mentor_consultation_reports_one_per_participant unique (order_id, reporter_user_id)
);

create table if not exists public.mentor_consultation_report_evidence (
  id uuid primary key default gen_random_uuid(),
  report_id uuid not null references public.mentor_consultation_reports(id) on delete cascade,
  file_url text not null,
  file_name text not null check (char_length(btrim(file_name)) between 1 and 255),
  mime_type text,
  submitter_role text not null default 'reporter' check (submitter_role in ('reporter', 'respondent')),
  created_at timestamptz not null default now()
);

-- 已有早期举报表时，先补齐字段，避免后续索引和 RLS 策略引用不存在的列。
-- respondent_user_id 的完整历史回填与非空约束在 dispute_resolution 迁移中执行。
alter table public.mentor_consultation_reports
  add column if not exists respondent_user_id uuid references public.users(id) on delete restrict,
  add column if not exists respondent_content text
    check (respondent_content is null or char_length(btrim(respondent_content)) between 20 and 500),
  add column if not exists responded_at timestamptz,
  add column if not exists first_response_due_at timestamptz,
  add column if not exists first_response_at timestamptz,
  add column if not exists priority text not null default 'normal'
    check (priority in ('normal', 'high', 'urgent')),
  add column if not exists escalation_level smallint not null default 0 check (escalation_level >= 0),
  add column if not exists escalated_at timestamptz;

-- Historical cases predate the service-level fields. Treat any legacy human
-- handling action as the first response so the operations queue only escalates
-- genuinely unanswered cases.
update public.mentor_consultation_reports
set first_response_due_at = created_at + interval '48 hours'
where first_response_due_at is null;

update public.mentor_consultation_reports
set first_response_at = coalesce(handled_at, updated_at, created_at)
where first_response_at is null
  and status in ('reviewing', 'resolved', 'dismissed');

alter table public.mentor_consultation_reports
  alter column first_response_due_at set not null;

alter table public.mentor_consultation_report_evidence
  add column if not exists submitter_role text not null default 'reporter'
    check (submitter_role in ('reporter', 'respondent'));

create index if not exists idx_mentor_consultation_reports_status_created
  on public.mentor_consultation_reports (status, created_at desc);

create index if not exists idx_mentor_consultation_reports_order
  on public.mentor_consultation_reports (order_id, created_at desc);

create index if not exists idx_mentor_consultation_reports_reporter
  on public.mentor_consultation_reports (reporter_user_id, created_at desc);

create index if not exists idx_mentor_consultation_reports_respondent
  on public.mentor_consultation_reports (respondent_user_id, created_at desc);

create index if not exists idx_mentor_consultation_reports_first_response_sla
  on public.mentor_consultation_reports (status, first_response_at, first_response_due_at, escalation_level desc);

create index if not exists idx_mentor_consultation_report_evidence_report
  on public.mentor_consultation_report_evidence (report_id, created_at);

create index if not exists idx_mentor_consultation_report_evidence_submitter
  on public.mentor_consultation_report_evidence (report_id, submitter_role, created_at);

drop trigger if exists set_mentor_consultation_reports_updated_at on public.mentor_consultation_reports;
create trigger set_mentor_consultation_reports_updated_at
before update on public.mentor_consultation_reports
for each row execute function public.set_updated_at();

alter table public.mentor_consultation_reports enable row level security;
alter table public.mentor_consultation_report_evidence enable row level security;

drop policy if exists "participants can read own consultation reports" on public.mentor_consultation_reports;
drop policy if exists "participants can read consultation reports" on public.mentor_consultation_reports;
create policy "participants can read consultation reports"
  on public.mentor_consultation_reports for select
  using (
    auth.uid() = reporter_user_id
    or auth.uid() = respondent_user_id
    or auth.uid() = target_user_id
  );

drop policy if exists "participants can create own consultation reports" on public.mentor_consultation_reports;
create policy "participants can create own consultation reports"
  on public.mentor_consultation_reports for insert
  with check (auth.uid() = reporter_user_id);

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
