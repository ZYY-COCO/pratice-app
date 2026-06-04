-- Align historical question review state with the admin review workflow.
-- Existing active questions were already published before the review workflow existed,
-- so they should not fill the pending review queue by default.

update public.questions
set
  review_status = 'approved',
  review_note = null,
  reviewed_at = coalesce(reviewed_at, created_at),
  review_updated_at = coalesce(review_updated_at, now())
where status = 'active'
  and review_status = 'pending';

update public.questions
set
  review_status = 'needs_changes',
  review_note = coalesce(review_note, '历史归档题，需人工复核后再发布'),
  review_updated_at = coalesce(review_updated_at, now())
where status = 'archived'
  and review_status = 'pending';

alter table public.questions
  alter column status set default 'archived';

alter table public.questions
  alter column review_status set default 'pending';
