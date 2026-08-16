-- Real likes for individual comments in the circle community.
-- Run this once in the Supabase SQL Editor before enabling the endpoint.

alter table public.circle_community_comments
  add column if not exists like_count integer not null default 0;

create table if not exists public.circle_community_comment_likes (
  id uuid primary key default gen_random_uuid(),
  comment_id uuid not null references public.circle_community_comments(id) on delete cascade,
  user_id uuid not null references public.users(id) on delete cascade,
  created_at timestamptz not null default now(),
  unique (comment_id, user_id)
);

create index if not exists idx_circle_community_comment_likes_comment_created
  on public.circle_community_comment_likes (comment_id, created_at desc);

create index if not exists idx_circle_community_comment_likes_user
  on public.circle_community_comment_likes (user_id, created_at desc);

update public.circle_community_comments as comment
set like_count = counts.total
from (
  select
    comment_row.id as comment_id,
    count(comment_like.id)::integer as total
  from public.circle_community_comments as comment_row
  left join public.circle_community_comment_likes as comment_like
    on comment_like.comment_id = comment_row.id
  group by comment_row.id
) as counts
where comment.id = counts.comment_id;

alter table public.circle_community_comment_likes enable row level security;

drop policy if exists "published circle comment likes are readable"
  on public.circle_community_comment_likes;
create policy "published circle comment likes are readable"
  on public.circle_community_comment_likes for select
  using (
    exists (
      select 1
      from public.circle_community_comments as comment
      join public.circle_community_posts as post on post.id = comment.post_id
      where comment.id = circle_community_comment_likes.comment_id
        and post.is_published = true
    )
  );
