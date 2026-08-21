-- 考研圈精选帖子：为已执行 circle_community.sql 的数据库补上精选标记。
-- 在 Supabase SQL Editor 中执行一次即可。

begin;

alter table public.circle_community_posts
  add column if not exists is_featured boolean not null default false;

create index if not exists idx_circle_community_posts_featured_visible
  on public.circle_community_posts (post_type, created_at desc)
  where is_published = true and is_featured = true;

commit;
