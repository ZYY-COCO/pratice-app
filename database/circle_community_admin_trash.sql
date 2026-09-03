-- 研圈帖子管理员回收站：删除后保留 7 天，可恢复或立即永久删除。
-- 在 Supabase SQL Editor 中执行一次；依赖：
-- database/circle_community.sql
-- database/circle_community_moderation.sql

begin;

alter table public.circle_community_posts
  add column if not exists admin_deleted_at timestamptz,
  add column if not exists admin_deleted_by uuid references public.users(id) on delete set null,
  add column if not exists admin_purge_after timestamptz,
  add column if not exists admin_restore_is_published boolean,
  add column if not exists admin_restore_is_featured boolean;

alter table public.circle_community_posts
  drop constraint if exists circle_community_posts_admin_trash_state_check;

alter table public.circle_community_posts
  add constraint circle_community_posts_admin_trash_state_check
  check (
    (
      admin_deleted_at is null
      and admin_purge_after is null
      and admin_restore_is_published is null
      and admin_restore_is_featured is null
    )
    or (
      admin_deleted_at is not null
      and admin_purge_after is not null
      and admin_purge_after > admin_deleted_at
      and admin_restore_is_published is not null
      and admin_restore_is_featured is not null
      and is_published = false
      and is_featured = false
    )
  );

create index if not exists idx_circle_community_posts_admin_trash_deleted
  on public.circle_community_posts (admin_deleted_at desc, id desc)
  where admin_deleted_at is not null;

create index if not exists idx_circle_community_posts_admin_trash_purge
  on public.circle_community_posts (admin_purge_after, id)
  where admin_deleted_at is not null;

create or replace function public.circle_community_admin_trash_posts(
  p_post_ids uuid[],
  p_admin_user_id uuid
)
returns table(post_id uuid)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_now timestamptz := now();
begin
  if coalesce(cardinality(p_post_ids), 0) = 0 then
    return;
  end if;

  return query
  update public.circle_community_posts as post
  set
    admin_deleted_at = v_now,
    admin_deleted_by = p_admin_user_id,
    admin_purge_after = v_now + interval '7 days',
    admin_restore_is_published = post.is_published,
    admin_restore_is_featured = post.is_featured,
    is_published = false,
    is_featured = false,
    updated_at = v_now
  where post.id = any(p_post_ids)
    and post.admin_deleted_at is null
  returning post.id;
end;
$$;

create or replace function public.circle_community_admin_restore_posts(
  p_post_ids uuid[]
)
returns table(post_id uuid)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_now timestamptz := now();
begin
  if coalesce(cardinality(p_post_ids), 0) = 0 then
    return;
  end if;

  return query
  update public.circle_community_posts as post
  set
    is_published = coalesce(post.admin_restore_is_published, false)
      and post.author_deleted_at is null,
    is_featured = coalesce(post.admin_restore_is_featured, false)
      and coalesce(post.admin_restore_is_published, false)
      and post.author_deleted_at is null,
    admin_deleted_at = null,
    admin_deleted_by = null,
    admin_purge_after = null,
    admin_restore_is_published = null,
    admin_restore_is_featured = null,
    updated_at = v_now
  where post.id = any(p_post_ids)
    and post.admin_deleted_at is not null
    and post.admin_purge_after > v_now
  returning post.id;
end;
$$;

create or replace function public.circle_community_admin_purge_posts(
  p_post_ids uuid[]
)
returns table(post_id uuid)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_post_ids uuid[];
begin
  if coalesce(cardinality(p_post_ids), 0) = 0 then
    return;
  end if;

  select coalesce(array_agg(locked_post.id), array[]::uuid[])
  into v_post_ids
  from (
    select post.id
    from public.circle_community_posts as post
    where post.id = any(p_post_ids)
      and post.admin_deleted_at is not null
    for update
  ) as locked_post;

  if cardinality(v_post_ids) = 0 then
    return;
  end if;

  -- 举报与申诉保留了 restrict 外键，永久删除帖子前必须先清理这些治理记录。
  delete from public.circle_community_reports
  where post_id = any(v_post_ids);

  delete from public.circle_community_appeals
  where post_id = any(v_post_ids);

  return query
  delete from public.circle_community_posts as post
  where post.id = any(v_post_ids)
    and post.admin_deleted_at is not null
  returning post.id;
end;
$$;

create or replace function public.circle_community_purge_expired_admin_trash()
returns integer
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_post_ids uuid[];
  v_deleted_count integer := 0;
begin
  select coalesce(array_agg(post.id), array[]::uuid[])
  into v_post_ids
  from public.circle_community_posts as post
  where post.admin_deleted_at is not null
    and post.admin_purge_after <= now();

  if cardinality(v_post_ids) = 0 then
    return 0;
  end if;

  select count(*)::integer
  into v_deleted_count
  from public.circle_community_admin_purge_posts(v_post_ids);

  return v_deleted_count;
end;
$$;

comment on column public.circle_community_posts.admin_deleted_at is
  '管理员将帖子移入回收站的时间；普通后台列表与用户端均不展示。';
comment on column public.circle_community_posts.admin_purge_after is
  '回收站自动永久清除时间，固定为管理员删除后的 7 天。';
comment on function public.circle_community_admin_trash_posts(uuid[], uuid) is
  '将帖子移入管理员回收站，并保存删除前的公开与精选状态。';
comment on function public.circle_community_admin_restore_posts(uuid[]) is
  '在保留期内恢复帖子及其删除前的公开与精选状态。';
comment on function public.circle_community_admin_purge_posts(uuid[]) is
  '永久删除回收站帖子及其关联治理记录；互动和审核历史按外键级联删除。';

revoke all on function public.circle_community_admin_trash_posts(uuid[], uuid) from public, anon, authenticated;
revoke all on function public.circle_community_admin_restore_posts(uuid[]) from public, anon, authenticated;
revoke all on function public.circle_community_admin_purge_posts(uuid[]) from public, anon, authenticated;
revoke all on function public.circle_community_purge_expired_admin_trash() from public, anon, authenticated;
grant execute on function public.circle_community_admin_trash_posts(uuid[], uuid) to service_role;
grant execute on function public.circle_community_admin_restore_posts(uuid[]) to service_role;
grant execute on function public.circle_community_admin_purge_posts(uuid[]) to service_role;
grant execute on function public.circle_community_purge_expired_admin_trash() to service_role;

commit;

-- 每 15 分钟清理一次已到期记录；同名任务重复执行时只更新原任务。
create extension if not exists pg_cron;

select cron.schedule(
  'circle-community-admin-trash-purge',
  '*/15 * * * *',
  $$select public.circle_community_purge_expired_admin_trash();$$
);

notify pgrst, 'reload schema';
