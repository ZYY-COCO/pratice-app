-- Question review workflow fields for the admin question-bank console.

alter table public.questions
  add column if not exists review_status text not null default 'pending',
  add column if not exists review_note text,
  add column if not exists reviewed_by uuid references public.users(id) on delete set null,
  add column if not exists reviewed_at timestamptz,
  add column if not exists review_updated_at timestamptz;

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'questions_review_status_check'
  ) then
    alter table public.questions
      add constraint questions_review_status_check
      check (review_status in ('pending', 'needs_changes', 'approved', 'rejected'));
  end if;
end $$;

create index if not exists idx_questions_review_status
  on public.questions(review_status);

create index if not exists idx_questions_review_queue
  on public.questions(review_status, created_at desc);

revoke insert (review_status, review_note, reviewed_by, reviewed_at, review_updated_at)
  on public.questions from anon, authenticated;

revoke update (review_status, review_note, reviewed_by, reviewed_at, review_updated_at)
  on public.questions from anon, authenticated;

revoke select (review_note, reviewed_by, reviewed_at, review_updated_at)
  on public.questions from anon, authenticated;
