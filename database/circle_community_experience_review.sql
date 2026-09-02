-- 经验贴发布审核闭环。
-- 在 Supabase SQL Editor 中执行一次；本文件可安全重复执行。

begin;

alter table public.circle_community_posts
  add column if not exists experience_stages text[] not null default '{}'::text[],
  add column if not exists moderation_note text,
  add column if not exists review_status text not null default 'approved',
  add column if not exists review_version integer not null default 0,
  add column if not exists review_reason_code text,
  add column if not exists review_note text,
  add column if not exists reviewed_by uuid references public.users(id) on delete set null,
  add column if not exists reviewed_at timestamptz,
  add column if not exists submitted_at timestamptz;

-- 首次执行时，历史经验贴继续保持原展示状态；后续重复执行不会覆盖新审核状态。
update public.circle_community_posts
set
  review_status = case
    when is_published = false and moderation_note is null then 'pending'
    else 'approved'
  end,
  review_version = 1,
  submitted_at = coalesce(submitted_at, created_at)
where post_type = 'experience'
  and review_version = 0;

update public.circle_community_posts
set
  review_status = 'approved',
  review_version = 0,
  review_reason_code = null,
  review_note = null,
  reviewed_by = null,
  reviewed_at = null,
  submitted_at = null
where post_type = 'chat'
  and (
    review_status <> 'approved'
    or review_version <> 0
    or review_reason_code is not null
    or review_note is not null
    or reviewed_by is not null
    or reviewed_at is not null
    or submitted_at is not null
  );

alter table public.circle_community_posts
  drop constraint if exists circle_community_posts_review_status_check,
  drop constraint if exists circle_community_posts_review_version_check,
  drop constraint if exists circle_community_posts_review_reason_code_check,
  drop constraint if exists circle_community_posts_review_note_check,
  drop constraint if exists circle_community_posts_review_visibility_check;

alter table public.circle_community_posts
  add constraint circle_community_posts_review_status_check
    check (review_status in ('pending', 'approved', 'rejected')),
  add constraint circle_community_posts_review_version_check
    check (review_version >= 0),
  add constraint circle_community_posts_review_reason_code_check
    check (
      review_reason_code is null
      or review_reason_code in (
        'advertising_or_diversion',
        'false_or_misleading',
        'infringement',
        'privacy',
        'inappropriate',
        'low_quality',
        'other'
      )
    ),
  add constraint circle_community_posts_review_note_check
    check (review_note is null or char_length(btrim(review_note)) between 1 and 1000),
  add constraint circle_community_posts_review_visibility_check
    check (
      post_type <> 'experience'
      or review_status = 'approved'
      or is_published = false
    );

create table if not exists public.circle_community_post_review_history (
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references public.circle_community_posts(id) on delete cascade,
  submission_version integer not null check (submission_version >= 1),
  action text not null check (action in ('submitted', 'approved', 'rejected')),
  from_status text check (from_status is null or from_status in ('pending', 'approved', 'rejected')),
  to_status text not null check (to_status in ('pending', 'approved', 'rejected')),
  reason_code text check (
    reason_code is null
    or reason_code in (
      'advertising_or_diversion',
      'false_or_misleading',
      'infringement',
      'privacy',
      'inappropriate',
      'low_quality',
      'other'
    )
  ),
  review_note text check (review_note is null or char_length(btrim(review_note)) between 1 and 1000),
  actor_user_id uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  unique (post_id, submission_version, action)
);

create index if not exists idx_circle_community_posts_experience_review_queue
  on public.circle_community_posts (review_status, submitted_at desc, id desc)
  where post_type = 'experience';

create index if not exists idx_circle_community_post_review_history_post
  on public.circle_community_post_review_history (post_id, created_at desc);

create or replace function public.circle_community_prepare_experience_review()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  if new.post_type = 'experience' then
    new.review_status := 'pending';
    new.review_version := greatest(coalesce(new.review_version, 0), 1);
    new.review_reason_code := null;
    new.review_note := null;
    new.reviewed_by := null;
    new.reviewed_at := null;
    new.submitted_at := coalesce(new.submitted_at, now());
    new.is_published := false;
  else
    new.review_status := 'approved';
    new.review_version := 0;
    new.review_reason_code := null;
    new.review_note := null;
    new.reviewed_by := null;
    new.reviewed_at := null;
    new.submitted_at := null;
  end if;
  return new;
end;
$$;

drop trigger if exists trg_circle_community_prepare_experience_review
  on public.circle_community_posts;
create trigger trg_circle_community_prepare_experience_review
before insert on public.circle_community_posts
for each row execute function public.circle_community_prepare_experience_review();

create or replace function public.circle_community_capture_experience_submission()
returns trigger
language plpgsql
set search_path = public
as $$
declare
  v_from_status text;
begin
  if new.post_type <> 'experience' or new.review_status <> 'pending' then
    return new;
  end if;

  if tg_op = 'INSERT' then
    v_from_status := null;
  elsif old.review_status is distinct from 'pending'
    or old.review_version is distinct from new.review_version
  then
    v_from_status := old.review_status;
  else
    return new;
  end if;

    insert into public.circle_community_post_review_history (
      post_id,
      submission_version,
      action,
      from_status,
      to_status,
      actor_user_id,
      created_at
    ) values (
      new.id,
      new.review_version,
      'submitted',
      v_from_status,
      'pending',
      new.author_id,
      coalesce(new.submitted_at, now())
    )
    on conflict (post_id, submission_version, action) do nothing;
  return new;
end;
$$;

drop trigger if exists trg_circle_community_capture_experience_submission
  on public.circle_community_posts;
create trigger trg_circle_community_capture_experience_submission
after insert or update of review_status, review_version
on public.circle_community_posts
for each row execute function public.circle_community_capture_experience_submission();

-- 为历史经验贴留下一条明确的迁移记录；不会伪造审核人或审核时间。
insert into public.circle_community_post_review_history (
  post_id,
  submission_version,
  action,
  from_status,
  to_status,
  reason_code,
  review_note,
  actor_user_id,
  created_at
)
select
  post.id,
  greatest(post.review_version, 1),
  case post.review_status when 'pending' then 'submitted' else post.review_status end,
  null,
  post.review_status,
  post.review_reason_code,
  post.review_note,
  case when post.review_status = 'pending' then post.author_id else post.reviewed_by end,
  coalesce(post.reviewed_at, post.submitted_at, post.created_at)
from public.circle_community_posts as post
where post.post_type = 'experience'
on conflict (post_id, submission_version, action) do nothing;

create or replace function public.review_circle_community_experience_post(
  p_post_id uuid,
  p_reviewer_id uuid,
  p_decision text,
  p_reason_code text default null,
  p_review_note text default null
)
returns setof public.circle_community_posts
language plpgsql
security definer
set search_path = public
as $$
declare
  v_current public.circle_community_posts%rowtype;
  v_updated public.circle_community_posts%rowtype;
  v_decision text := btrim(coalesce(p_decision, ''));
  v_reason_code text := nullif(btrim(coalesce(p_reason_code, '')), '');
  v_review_note text := nullif(btrim(coalesce(p_review_note, '')), '');
begin
  if v_decision not in ('approved', 'rejected') then
    raise exception using errcode = '22023', message = '不支持的经验贴审核结论';
  end if;
  if v_decision = 'rejected' and (
    v_reason_code is null
    or v_reason_code not in (
      'advertising_or_diversion',
      'false_or_misleading',
      'infringement',
      'privacy',
      'inappropriate',
      'low_quality',
      'other'
    )
    or v_review_note is null
  ) then
    raise exception using errcode = '22023', message = '驳回经验贴时必须选择官方理由并填写处理说明';
  end if;

  select *
  into v_current
  from public.circle_community_posts
  where id = p_post_id
  for update;

  if not found or v_current.post_type <> 'experience' then
    raise exception using errcode = 'P0002', message = '经验贴不存在';
  end if;
  if v_current.review_status <> 'pending' then
    raise exception using errcode = 'P0001', message = '该经验贴审核状态已变化，请刷新后重试';
  end if;

  update public.circle_community_posts
  set
    review_status = v_decision,
    review_reason_code = case when v_decision = 'rejected' then v_reason_code else null end,
    review_note = v_review_note,
    reviewed_by = p_reviewer_id,
    reviewed_at = now(),
    is_published = (v_decision = 'approved'),
    is_featured = case when v_decision = 'approved' then is_featured else false end,
    updated_at = now()
  where id = p_post_id
  returning * into v_updated;

  insert into public.circle_community_post_review_history (
    post_id,
    submission_version,
    action,
    from_status,
    to_status,
    reason_code,
    review_note,
    actor_user_id
  ) values (
    v_updated.id,
    v_updated.review_version,
    v_decision,
    v_current.review_status,
    v_decision,
    case when v_decision = 'rejected' then v_reason_code else null end,
    v_review_note,
    p_reviewer_id
  )
  on conflict (post_id, submission_version, action) do nothing;

  return next v_updated;
end;
$$;

create or replace function public.resubmit_circle_community_experience_post(
  p_post_id uuid,
  p_author_id uuid,
  p_category text,
  p_experience_stages text[],
  p_title text,
  p_content text,
  p_media jsonb
)
returns setof public.circle_community_posts
language plpgsql
security definer
set search_path = public
as $$
declare
  v_current public.circle_community_posts%rowtype;
  v_updated public.circle_community_posts%rowtype;
  v_category text := btrim(coalesce(p_category, ''));
  v_title text := btrim(coalesce(p_title, ''));
  v_content text := btrim(coalesce(p_content, ''));
begin
  if v_category not in ('Z001', 'Z002') then
    raise exception using errcode = '22023', message = '经验贴考试类别仅支持 Z001、Z002';
  end if;
  if coalesce(cardinality(p_experience_stages), 0) = 0
    or not p_experience_stages <@ array['申请制', '初试', '复试']::text[]
    or array_position(p_experience_stages, null) is not null
  then
    raise exception using errcode = '22023', message = '经验贴至少选择一个有效备考阶段';
  end if;
  if char_length(v_title) not between 1 and 80
    or char_length(v_content) not between 1 and 3000
  then
    raise exception using errcode = '22023', message = '经验贴标题或正文长度不符合要求';
  end if;
  if jsonb_typeof(coalesce(p_media, '[]'::jsonb)) <> 'array'
    or jsonb_array_length(coalesce(p_media, '[]'::jsonb)) > 9
  then
    raise exception using errcode = '22023', message = '经验贴图片数据不符合要求';
  end if;

  select *
  into v_current
  from public.circle_community_posts
  where id = p_post_id
  for update;

  if not found
    or v_current.post_type <> 'experience'
    or v_current.author_id is distinct from p_author_id
  then
    raise exception using errcode = 'P0002', message = '经验贴不存在';
  end if;
  if v_current.review_status <> 'rejected' then
    raise exception using errcode = 'P0001', message = '只有审核未通过的经验贴可以修改后重新提交';
  end if;

  update public.circle_community_posts
  set
    category = v_category,
    experience_stages = array(
      select allowed.stage
      from unnest(array['申请制', '初试', '复试']::text[]) with ordinality
        as allowed(stage, stage_order)
      where allowed.stage = any(p_experience_stages)
      order by allowed.stage_order
    ),
    title = v_title,
    content = v_content,
    media = coalesce(p_media, '[]'::jsonb),
    review_status = 'pending',
    review_version = v_current.review_version + 1,
    review_reason_code = null,
    review_note = null,
    reviewed_by = null,
    reviewed_at = null,
    submitted_at = now(),
    is_published = false,
    is_featured = false,
    updated_at = now()
  where id = p_post_id
  returning * into v_updated;

  return next v_updated;
end;
$$;

alter table public.circle_community_post_review_history enable row level security;

revoke all on table public.circle_community_post_review_history from public, anon, authenticated;
grant select, insert on table public.circle_community_post_review_history to service_role;

revoke all on function public.review_circle_community_experience_post(uuid, uuid, text, text, text)
  from public, anon, authenticated;
revoke all on function public.resubmit_circle_community_experience_post(uuid, uuid, text, text[], text, text, jsonb)
  from public, anon, authenticated;
grant execute on function public.review_circle_community_experience_post(uuid, uuid, text, text, text)
  to service_role;
grant execute on function public.resubmit_circle_community_experience_post(uuid, uuid, text, text[], text, text, jsonb)
  to service_role;

commit;
