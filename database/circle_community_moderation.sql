-- 考研圈内容治理与经验贴可信作者闭环。
-- 在 Supabase SQL Editor 中执行一次；依赖 database/circle_community.sql。
-- 本迁移保留已有帖子、评论和互动记录，只补齐审核、举报与处理留痕能力。

begin;

-- 先归一化早期帖子：历史“经验贴”曾沿用学科分类，普通讨论也可能留有旧标签。
-- 内容不变，仅修正为当前前台/后台共用的分类集合，避免新增约束阻断上线。
update public.circle_community_posts
set category = case
  when category = 'Z002'
    or category = '数学基础'
    or title ilike '%Z002%'
    or content ilike '%Z002%'
    or content ilike '%数学%'
    or content ilike '%微积分%'
    or content ilike '%导数%'
    or content ilike '%积分%'
    then 'Z002'
  else 'Z001'
end
where post_type = 'experience'
  and category not in ('Z001', 'Z002', '专业课', '复试');

update public.circle_community_posts
set category = '备考日常'
where post_type = 'chat'
  and category not in ('备考日常', '中华文化', '数学基础', '英语运用', '逻辑推理');

-- 经验贴的分类和前端可选项保持一致，避免“专业课 / 复试”在接口校验通过后被数据库拒绝。
alter table public.circle_community_posts
  drop constraint if exists circle_community_posts_category_check;

alter table public.circle_community_posts
  add constraint circle_community_posts_category_check
  check (
    (post_type = 'chat' and category in ('备考日常', '中华文化', '数学基础', '英语运用', '逻辑推理'))
    or (post_type = 'experience' and category in ('Z001', 'Z002', '专业课', '复试'))
  );

alter table public.circle_community_posts
  add column if not exists moderation_note text
    check (moderation_note is null or char_length(btrim(moderation_note)) <= 1000),
  add column if not exists moderated_at timestamptz;

alter table public.circle_community_comments
  add column if not exists is_published boolean not null default true,
  add column if not exists moderation_note text
    check (moderation_note is null or char_length(btrim(moderation_note)) <= 1000),
  add column if not exists moderated_at timestamptz;

create table if not exists public.circle_community_reports (
  id uuid primary key default gen_random_uuid(),
  reporter_user_id uuid not null references public.users(id) on delete restrict,
  target_type text not null check (target_type in ('post', 'comment')),
  post_id uuid not null references public.circle_community_posts(id) on delete restrict,
  comment_id uuid references public.circle_community_comments(id) on delete restrict,
  target_user_id uuid references public.users(id) on delete set null,
  reason text not null check (char_length(btrim(reason)) between 1 and 60),
  content text not null default '' check (char_length(btrim(content)) <= 500),
  status text not null default 'pending'
    check (status in ('pending', 'reviewing', 'resolved', 'dismissed')),
  moderation_action text not null default 'none'
    check (moderation_action in ('none', 'hide_post', 'restore_post', 'hide_comment', 'restore_comment')),
  admin_note text
    check (admin_note is null or char_length(btrim(admin_note)) <= 1000),
  handled_by uuid references public.users(id) on delete set null,
  handled_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint circle_community_reports_target_check check (
    (target_type = 'post' and comment_id is null)
    or (target_type = 'comment' and comment_id is not null)
  )
);

create unique index if not exists uq_circle_community_reports_reporter_post
  on public.circle_community_reports (reporter_user_id, post_id)
  where target_type = 'post';

create unique index if not exists uq_circle_community_reports_reporter_comment
  on public.circle_community_reports (reporter_user_id, comment_id)
  where target_type = 'comment';

create index if not exists idx_circle_community_reports_status_created
  on public.circle_community_reports (status, created_at desc);

create index if not exists idx_circle_community_reports_post_created
  on public.circle_community_reports (post_id, created_at desc);

create index if not exists idx_circle_community_reports_reporter_created
  on public.circle_community_reports (reporter_user_id, created_at desc);

-- 内容被下架后，作者可发起一次申诉；申诉本身和原举报独立留档，便于后台复核。
create table if not exists public.circle_community_appeals (
  id uuid primary key default gen_random_uuid(),
  appellant_user_id uuid not null references public.users(id) on delete restrict,
  target_type text not null check (target_type in ('post', 'comment')),
  post_id uuid not null references public.circle_community_posts(id) on delete restrict,
  comment_id uuid references public.circle_community_comments(id) on delete restrict,
  content text not null check (char_length(btrim(content)) between 10 and 500),
  status text not null default 'pending'
    check (status in ('pending', 'reviewing', 'resolved', 'dismissed')),
  moderation_action text not null default 'none'
    check (moderation_action in ('none', 'restore_post', 'restore_comment', 'uphold')),
  admin_note text
    check (admin_note is null or char_length(btrim(admin_note)) <= 1000),
  handled_by uuid references public.users(id) on delete set null,
  handled_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint circle_community_appeals_target_check check (
    (target_type = 'post' and comment_id is null)
    or (target_type = 'comment' and comment_id is not null)
  )
);

create unique index if not exists uq_circle_community_appeals_appellant_post
  on public.circle_community_appeals (appellant_user_id, post_id)
  where target_type = 'post';

create unique index if not exists uq_circle_community_appeals_appellant_comment
  on public.circle_community_appeals (appellant_user_id, comment_id)
  where target_type = 'comment';

create index if not exists idx_circle_community_appeals_status_created
  on public.circle_community_appeals (status, created_at desc);

create index if not exists idx_circle_community_appeals_appellant_created
  on public.circle_community_appeals (appellant_user_id, created_at desc);

drop trigger if exists set_circle_community_reports_updated_at on public.circle_community_reports;
create trigger set_circle_community_reports_updated_at
before update on public.circle_community_reports
for each row execute function public.set_updated_at();

drop trigger if exists set_circle_community_appeals_updated_at on public.circle_community_appeals;
create trigger set_circle_community_appeals_updated_at
before update on public.circle_community_appeals
for each row execute function public.set_updated_at();

-- 被下架的评论不会继续出现在帖子详情，也不会继续计入公开评论数。
create or replace function public.circle_community_refresh_comment_count()
returns trigger
language plpgsql
set search_path = public
as $$
begin
  if tg_op = 'INSERT' and new.is_published then
    update public.circle_community_posts
    set comment_count = comment_count + 1,
        updated_at = now()
    where id = new.post_id;
  elsif tg_op = 'DELETE' and old.is_published then
    update public.circle_community_posts
    set comment_count = greatest(comment_count - 1, 0),
        updated_at = now()
    where id = old.post_id;
  elsif tg_op = 'UPDATE' and old.is_published is distinct from new.is_published then
    update public.circle_community_posts
    set comment_count = greatest(comment_count + case when new.is_published then 1 else -1 end, 0),
        updated_at = now()
    where id = new.post_id;
  end if;
  return null;
end;
$$;

drop trigger if exists circle_community_comment_count on public.circle_community_comments;
create trigger circle_community_comment_count
after insert or delete or update of is_published on public.circle_community_comments
for each row execute function public.circle_community_refresh_comment_count();

update public.circle_community_posts as post
set comment_count = counts.total,
    updated_at = now()
from (
  select post_row.id as post_id, count(comment.id)::integer as total
  from public.circle_community_posts as post_row
  left join public.circle_community_comments as comment
    on comment.post_id = post_row.id
    and comment.is_published = true
  group by post_row.id
) as counts
where post.id = counts.post_id;

alter table public.circle_community_reports enable row level security;
alter table public.circle_community_appeals enable row level security;

drop policy if exists "users can read own circle reports" on public.circle_community_reports;
create policy "users can read own circle reports"
  on public.circle_community_reports for select
  using (auth.uid() = reporter_user_id);

drop policy if exists "users can create own circle reports" on public.circle_community_reports;
create policy "users can create own circle reports"
  on public.circle_community_reports for insert
  with check (auth.uid() = reporter_user_id);

drop policy if exists "users can read own circle appeals" on public.circle_community_appeals;
create policy "users can read own circle appeals"
  on public.circle_community_appeals for select
  using (auth.uid() = appellant_user_id);

drop policy if exists "users can create own circle appeals" on public.circle_community_appeals;
create policy "users can create own circle appeals"
  on public.circle_community_appeals for insert
  with check (auth.uid() = appellant_user_id);

commit;
