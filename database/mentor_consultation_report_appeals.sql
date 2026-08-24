-- 前辈咨询裁决复核闭环。
-- 依赖 mentor_consultation_reports.sql 与 mentor_consultation_dispute_resolution.sql。
-- 双方各可对同一咨询反馈提交一次复核申请；后台可维持原结论或重新开启原案。

begin;

create extension if not exists "pgcrypto";

create table if not exists public.mentor_consultation_report_appeals (
  id uuid primary key default gen_random_uuid(),
  report_id uuid not null references public.mentor_consultation_reports(id) on delete cascade,
  appellant_user_id uuid not null references public.users(id) on delete restrict,
  appellant_role text not null check (appellant_role in ('reporter', 'respondent')),
  content text not null check (char_length(btrim(content)) between 20 and 500),
  status text not null default 'pending'
    check (status in ('pending', 'reviewing', 'resolved', 'dismissed')),
  first_response_due_at timestamptz not null default (now() + interval '48 hours'),
  first_response_at timestamptz,
  priority text not null default 'normal'
    check (priority in ('normal', 'high', 'urgent')),
  escalation_level smallint not null default 0 check (escalation_level >= 0),
  escalated_at timestamptz,
  decision text not null default 'none'
    check (decision in ('none', 'uphold', 'reopen')),
  admin_note text check (admin_note is null or char_length(btrim(admin_note)) <= 1000),
  handled_by uuid references public.users(id) on delete set null,
  handled_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint mentor_consultation_report_appeals_one_per_participant unique (report_id, appellant_user_id)
);

-- Safe when this migration is executed against an earlier appeals table.
alter table public.mentor_consultation_report_appeals
  add column if not exists first_response_due_at timestamptz,
  add column if not exists first_response_at timestamptz,
  add column if not exists priority text not null default 'normal'
    check (priority in ('normal', 'high', 'urgent')),
  add column if not exists escalation_level smallint not null default 0 check (escalation_level >= 0),
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

create table if not exists public.mentor_consultation_report_appeal_evidence (
  id uuid primary key default gen_random_uuid(),
  appeal_id uuid not null references public.mentor_consultation_report_appeals(id) on delete cascade,
  file_url text not null,
  file_name text not null check (char_length(btrim(file_name)) between 1 and 255),
  mime_type text,
  created_at timestamptz not null default now()
);

create index if not exists idx_mentor_consultation_report_appeals_status_created
  on public.mentor_consultation_report_appeals (status, created_at desc);

create index if not exists idx_mentor_consultation_report_appeals_report_created
  on public.mentor_consultation_report_appeals (report_id, created_at desc);

create index if not exists idx_mentor_consultation_report_appeals_appellant_created
  on public.mentor_consultation_report_appeals (appellant_user_id, created_at desc);

create index if not exists idx_mentor_consultation_report_appeals_first_response_sla
  on public.mentor_consultation_report_appeals (status, first_response_at, first_response_due_at, escalation_level desc);

create index if not exists idx_mentor_consultation_report_appeal_evidence_appeal_created
  on public.mentor_consultation_report_appeal_evidence (appeal_id, created_at);

drop trigger if exists set_mentor_consultation_report_appeals_updated_at on public.mentor_consultation_report_appeals;
create trigger set_mentor_consultation_report_appeals_updated_at
before update on public.mentor_consultation_report_appeals
for each row execute function public.set_updated_at();

alter table public.mentor_consultation_report_appeals enable row level security;
alter table public.mentor_consultation_report_appeal_evidence enable row level security;

drop policy if exists "participants can read own consultation report appeals" on public.mentor_consultation_report_appeals;
create policy "participants can read own consultation report appeals"
  on public.mentor_consultation_report_appeals for select
  using (auth.uid() = appellant_user_id);

drop policy if exists "participants can create own consultation report appeals" on public.mentor_consultation_report_appeals;
create policy "participants can create own consultation report appeals"
  on public.mentor_consultation_report_appeals for insert
  with check (
    auth.uid() = appellant_user_id
    and exists (
      select 1
      from public.mentor_consultation_reports report
      where report.id = mentor_consultation_report_appeals.report_id
        and report.status in ('resolved', 'dismissed')
        and (
          report.reporter_user_id = auth.uid()
          or report.respondent_user_id = auth.uid()
          or report.target_user_id = auth.uid()
        )
    )
  );

drop policy if exists "participants can read own consultation report appeal evidence" on public.mentor_consultation_report_appeal_evidence;
create policy "participants can read own consultation report appeal evidence"
  on public.mentor_consultation_report_appeal_evidence for select
  using (
    exists (
      select 1
      from public.mentor_consultation_report_appeals appeal
      where appeal.id = mentor_consultation_report_appeal_evidence.appeal_id
        and appeal.appellant_user_id = auth.uid()
    )
  );

drop policy if exists "participants can create own consultation report appeal evidence" on public.mentor_consultation_report_appeal_evidence;
create policy "participants can create own consultation report appeal evidence"
  on public.mentor_consultation_report_appeal_evidence for insert
  with check (
    exists (
      select 1
      from public.mentor_consultation_report_appeals appeal
      where appeal.id = mentor_consultation_report_appeal_evidence.appeal_id
        and appeal.appellant_user_id = auth.uid()
        and appeal.status in ('pending', 'reviewing')
    )
  );

commit;
