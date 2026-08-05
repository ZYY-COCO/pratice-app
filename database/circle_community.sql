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
  category text not null check (char_length(btrim(category)) between 1 and 24),
  title text not null check (char_length(btrim(title)) between 1 and 80),
  content text not null check (char_length(btrim(content)) between 1 and 2000),
  media jsonb not null default '[]'::jsonb check (jsonb_typeof(media) = 'array'),
  like_count integer not null default 0 check (like_count >= 0),
  comment_count integer not null default 0 check (comment_count >= 0),
  view_count integer not null default 0 check (view_count >= 0),
  is_published boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
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

create index if not exists idx_circle_community_likes_post
  on public.circle_community_likes (post_id, created_at desc);

create index if not exists idx_circle_community_comments_post_created
  on public.circle_community_comments (post_id, created_at asc);

create unique index if not exists idx_circle_community_views_user
  on public.circle_community_views (post_id, user_id)
  where user_id is not null;

create unique index if not exists idx_circle_community_views_anonymous
  on public.circle_community_views (post_id, anonymous_id)
  where anonymous_id is not null;

-- 现有本地示例帖作为首批可互动内容。固定 UUID 让前端预览和线上数据保持一致。
insert into public.circle_community_posts (
  id, author_name, author_avatar, author_tone, category, title, content, media,
  like_count, comment_count, view_count
) values
  (
    '0b46a665-7b7d-4e0c-a62c-f42282f4e101',
    '南栀同学', '南', 'mint', '备考日常',
    'Z001 三科刚起步，大家一周都怎么排？',
    '我先按固定题量排了第一周，怕节奏太满坚持不下来，想看看大家有没有更稳的安排。',
    jsonb_build_array(
      jsonb_build_object('kicker', '周一', 'title', '文化 20 题', 'copy', '错题当天回看', 'tone', 'sky'),
      jsonb_build_object('kicker', '周三', 'title', '英语 20 题', 'copy', '短语优先', 'tone', 'mint'),
      jsonb_build_object('kicker', '周五', 'title', '逻辑 15 题', 'copy', '周末做小结', 'tone', 'warm')
    ),
    34, 12, 186
  ),
  (
    '2fd58d9c-7c70-4d90-9d88-3a261c4847af',
    '阿澈', '澈', 'blue', '择校答疑',
    '港大和港中文的分数线，应该怎么看？',
    '目前基础一般，想申请文科方向。除了分数线，大家还会优先比较哪些信息？',
    '[]'::jsonb,
    21, 18, 153
  ),
  (
    '423377f8-7fcf-4ddb-a34d-6ea7e25504da',
    '小卷', '卷', 'warm', '复习打卡',
    '中华文化索引表打卡第 6 天',
    '今天补了人物、作品和朝代三列，发现做题时定位干扰项比以前快很多。',
    jsonb_build_array(
      jsonb_build_object('kicker', '今日笔记', 'title', '人物 × 作品', 'copy', '补齐 16 个易混点', 'tone', 'paper')
    ),
    48, 9, 217
  ),
  (
    'f7cd37cc-bf32-4873-b954-ffa5522d6e0b',
    '知行', '知', 'violet', '资料互助',
    '整理了一份数学基础错题复盘模板',
    '模板按公式条件、代入过程和最后验算拆分，适合把重复错误记得更清楚。',
    '[]'::jsonb,
    29, 7, 141
  )
on conflict (id) do nothing;

-- 每张示例帖保留一条可进入详情查看的历史评论，计数基线保持当前页面展示的数字。
insert into public.circle_community_comments (id, post_id, author_name, author_avatar, content) values
  ('f4065c3c-f9f5-41ee-98d7-5b2c79c1c0a1', '0b46a665-7b7d-4e0c-a62c-f42282f4e101', '研友小林', '林', '我也是先把固定题量跑顺，第二周再慢慢加题。'),
  ('f4065c3c-f9f5-41ee-98d7-5b2c79c1c0a2', '2fd58d9c-7c70-4d90-9d88-3a261c4847af', '思远', '思', '先看专业和年度要求，再把语言成绩、材料和自己的准备周期一起算进去。'),
  ('f4065c3c-f9f5-41ee-98d7-5b2c79c1c0a3', '423377f8-7fcf-4ddb-a34d-6ea7e25504da', '小麦', '麦', '这个方法很好，我今晚也准备按这个结构补索引。'),
  ('f4065c3c-f9f5-41ee-98d7-5b2c79c1c0a4', 'f7cd37cc-bf32-4873-b954-ffa5522d6e0b', 'M 同学', 'M', '正好需要这个思路，做完题只记答案确实很难复盘。')
on conflict (id) do nothing;

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

    update public.circle_community_posts
    set like_count = greatest(like_count - 1, 0),
        updated_at = now()
    where id = p_post_id
    returning like_count into v_like_count;
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
      update public.circle_community_posts
      set like_count = like_count + 1,
          updated_at = now()
      where id = p_post_id
      returning like_count into v_like_count;
    else
      select like_count into v_like_count
      from public.circle_community_posts
      where id = p_post_id;
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
    update public.circle_community_posts
    set view_count = view_count + 1,
        updated_at = now()
    where id = p_post_id
    returning view_count into v_view_count;
  else
    select view_count into v_view_count
    from public.circle_community_posts
    where id = p_post_id;
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
