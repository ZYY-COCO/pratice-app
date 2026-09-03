-- 考研圈互动数据。
-- 在 Supabase SQL Editor 执行一次；后端使用 service role 写入，前端仅访问后端 API。

create table if not exists public.circle_community_posts (
  id uuid primary key default gen_random_uuid(),
  author_id uuid references public.users(id) on delete set null,
  author_name text not null,
  author_avatar text not null default '研',
  author_tone text not null default 'blue'
    check (author_tone in ('mint', 'blue', 'warm', 'violet')),
  post_type text not null default 'chat'
    check (post_type in ('chat', 'experience')),
  category text not null check (
    (post_type = 'chat' and category in ('备考日常', '中华文化', '数学基础', '英语运用', '逻辑推理'))
    or (post_type = 'experience' and category in ('Z001', 'Z002', '专业课', '复试'))
  ),
  title text not null check (char_length(btrim(title)) between 1 and 80),
  content text not null check (char_length(btrim(content)) between 1 and 3000),
  media jsonb not null default '[]'::jsonb check (jsonb_typeof(media) = 'array'),
  like_count integer not null default 0 check (like_count >= 0),
  comment_count integer not null default 0 check (comment_count >= 0),
  view_count integer not null default 0 check (view_count >= 0),
  is_published boolean not null default true,
  is_featured boolean not null default false,
  author_deleted_at timestamptz,
  admin_deleted_at timestamptz,
  admin_deleted_by uuid references public.users(id) on delete set null,
  admin_purge_after timestamptz,
  admin_restore_is_published boolean,
  admin_restore_is_featured boolean,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint circle_community_posts_author_deleted_hidden_check check (
    author_deleted_at is null
    or (is_published = false and is_featured = false)
  ),
  constraint circle_community_posts_admin_trash_state_check check (
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
  )
);

create table if not exists public.circle_community_likes (
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references public.circle_community_posts(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (post_id, user_id)
);

create table if not exists public.circle_community_comments (
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references public.circle_community_posts(id) on delete cascade,
  author_id uuid references public.users(id) on delete set null,
  author_name text not null,
  author_avatar text not null default '研',
  content text not null check (char_length(btrim(content)) between 1 and 500),
  created_at timestamptz not null default now()
);

create table if not exists public.circle_community_views (
  id uuid primary key default gen_random_uuid(),
  post_id uuid not null references public.circle_community_posts(id) on delete cascade,
  user_id uuid references public.users(id) on delete cascade,
  anonymous_id uuid,
  last_counted_at timestamptz not null default now(),
  constraint circle_community_views_viewer_check
    check (num_nonnulls(user_id, anonymous_id) = 1)
);

create index if not exists idx_circle_community_posts_published_created
  on public.circle_community_posts (is_published, created_at desc);

create index if not exists idx_circle_community_posts_category_created
  on public.circle_community_posts (category, created_at desc);

create index if not exists idx_circle_community_posts_type_published_created
  on public.circle_community_posts (post_type, is_published, created_at desc);

create index if not exists idx_circle_community_posts_featured_visible
  on public.circle_community_posts (post_type, created_at desc)
  where is_published = true and is_featured = true;

create index if not exists idx_circle_community_posts_author_active_created
  on public.circle_community_posts (author_id, created_at desc, id desc)
  where author_deleted_at is null;

create index if not exists idx_circle_community_posts_admin_trash_deleted
  on public.circle_community_posts (admin_deleted_at desc, id desc)
  where admin_deleted_at is not null;

create index if not exists idx_circle_community_posts_admin_trash_purge
  on public.circle_community_posts (admin_purge_after, id)
  where admin_deleted_at is not null;

create index if not exists idx_circle_community_likes_post
  on public.circle_community_likes (post_id, created_at desc);

create index if not exists idx_circle_community_likes_user_created
  on public.circle_community_likes (user_id, created_at desc);

create index if not exists idx_circle_community_comments_post_created
  on public.circle_community_comments (post_id, created_at asc);

create unique index if not exists idx_circle_community_views_user
  on public.circle_community_views (post_id, user_id)
  where user_id is not null;

create unique index if not exists idx_circle_community_views_anonymous
  on public.circle_community_views (post_id, anonymous_id)
  where anonymous_id is not null;

-- Community posts are created by users. No demo content is seeded here.

create or replace function public.circle_community_refresh_comment_count()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  if tg_op = 'INSERT' then
    update public.circle_community_posts
    set comment_count = comment_count + 1,
        updated_at = now()
    where id = new.post_id;
  elsif tg_op = 'DELETE' then
    update public.circle_community_posts
    set comment_count = greatest(comment_count - 1, 0),
        updated_at = now()
    where id = old.post_id;
  end if;
  return null;
end;
$$;

drop trigger if exists circle_community_comment_count on public.circle_community_comments;
create trigger circle_community_comment_count
after insert or delete on public.circle_community_comments
for each row execute function public.circle_community_refresh_comment_count();

create or replace function public.circle_community_toggle_like(
  p_post_id uuid,
  p_user_id uuid
)
returns table (is_liked boolean, like_count integer)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_liked boolean;
  v_like_count integer;
begin
  perform 1
  from public.circle_community_posts
  where id = p_post_id and is_published = true
  for update;

  if not found then
    raise exception 'Circle post not found';
  end if;

  select exists(
    select 1
    from public.circle_community_likes
    where post_id = p_post_id and user_id = p_user_id
  ) into v_liked;

  if v_liked then
    delete from public.circle_community_likes
    where post_id = p_post_id and user_id = p_user_id;

    update public.circle_community_posts as post
    set like_count = greatest(post.like_count - 1, 0),
        updated_at = now()
    where post.id = p_post_id
    returning post.like_count into v_like_count;
  else
    insert into public.circle_community_likes (post_id, user_id)
    values (p_post_id, p_user_id)
    on conflict (post_id, user_id) do nothing;

    select exists(
      select 1
      from public.circle_community_likes
      where post_id = p_post_id and user_id = p_user_id
    ) into v_liked;

    if v_liked then
      update public.circle_community_posts as post
      set like_count = post.like_count + 1,
          updated_at = now()
      where post.id = p_post_id
      returning post.like_count into v_like_count;
    else
      select post.like_count into v_like_count
      from public.circle_community_posts as post
      where post.id = p_post_id;
    end if;
  end if;

  return query select v_liked, v_like_count;
end;
$$;

create or replace function public.circle_community_register_view(
  p_post_id uuid,
  p_user_id uuid default null,
  p_anonymous_id uuid default null
)
returns table (counted boolean, view_count integer)
language plpgsql
security definer
set search_path = public
as $$
declare
  v_view_id uuid;
  v_counted boolean := false;
  v_view_count integer;
begin
  if p_user_id is null and p_anonymous_id is null then
    raise exception 'Viewer identity is required';
  end if;

  perform 1
  from public.circle_community_posts
  where id = p_post_id and is_published = true
  for update;

  if not found then
    raise exception 'Circle post not found';
  end if;

  if p_user_id is not null then
    insert into public.circle_community_views (post_id, user_id, last_counted_at)
    values (p_post_id, p_user_id, now())
    on conflict (post_id, user_id) where user_id is not null
    do update set last_counted_at = excluded.last_counted_at
    where public.circle_community_views.last_counted_at <= now() - interval '24 hours'
    returning id into v_view_id;
  else
    insert into public.circle_community_views (post_id, anonymous_id, last_counted_at)
    values (p_post_id, p_anonymous_id, now())
    on conflict (post_id, anonymous_id) where anonymous_id is not null
    do update set last_counted_at = excluded.last_counted_at
    where public.circle_community_views.last_counted_at <= now() - interval '24 hours'
    returning id into v_view_id;
  end if;

  v_counted := v_view_id is not null;
  if v_counted then
    update public.circle_community_posts as post
    set view_count = post.view_count + 1,
        updated_at = now()
    where post.id = p_post_id
    returning post.view_count into v_view_count;
  else
    select post.view_count into v_view_count
    from public.circle_community_posts as post
    where post.id = p_post_id;
  end if;

  return query select v_counted, v_view_count;
end;
$$;

alter table public.circle_community_posts enable row level security;
alter table public.circle_community_likes enable row level security;
alter table public.circle_community_comments enable row level security;
alter table public.circle_community_views enable row level security;

drop policy if exists "published circle posts are readable" on public.circle_community_posts;
create policy "published circle posts are readable"
  on public.circle_community_posts for select
  using (is_published = true);

drop policy if exists "published circle comments are readable" on public.circle_community_comments;
create policy "published circle comments are readable"
  on public.circle_community_comments for select
  using (
    exists (
      select 1 from public.circle_community_posts
      where id = post_id and is_published = true
    )
  );

drop policy if exists "users can read own circle likes" on public.circle_community_likes;
create policy "users can read own circle likes"
  on public.circle_community_likes for select
  using (auth.uid() = user_id);

revoke all on function public.circle_community_toggle_like(uuid, uuid) from public, anon, authenticated;
revoke all on function public.circle_community_register_view(uuid, uuid, uuid) from public, anon, authenticated;
grant execute on function public.circle_community_toggle_like(uuid, uuid) to service_role;
grant execute on function public.circle_community_register_view(uuid, uuid, uuid) to service_role;
