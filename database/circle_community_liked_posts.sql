-- “赞过的帖子”入口：为既有考研圈数据库补上用户点赞列表索引。
-- 在 Supabase SQL Editor 执行一次即可。

begin;

create index if not exists idx_circle_community_likes_user_created
  on public.circle_community_likes (user_id, created_at desc);

commit;
