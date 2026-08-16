-- 考研圈内容类型升级：为已执行 circle_community.sql 的数据库补上“研友聊 / 经验贴”分流。
-- 在 Supabase SQL Editor 中执行一次即可。

alter table public.circle_community_posts
  add column if not exists post_type text not null default 'chat';

do $$
begin
  if not exists (
    select 1
    from pg_constraint
    where conname = 'circle_community_posts_post_type_check'
      and conrelid = 'public.circle_community_posts'::regclass
  ) then
    alter table public.circle_community_posts
      add constraint circle_community_posts_post_type_check
      check (post_type in ('chat', 'experience'));
  end if;
end;
$$;

create index if not exists idx_circle_community_posts_type_published_created
  on public.circle_community_posts (post_type, is_published, created_at desc);

-- The application can temporarily store the type in media for databases that
-- predate this column. Fold that marker into the canonical column when this
-- migration is eventually applied, without retaining an invisible media item.
with migrated_posts as (
  select
    post.id,
    marker.post_type,
    marker.media
  from public.circle_community_posts as post
  cross join lateral (
    select
      max(element ->> '_circle_post_type') filter (where element ? '_circle_post_type') as post_type,
      coalesce(
        jsonb_agg(element order by ordinal) filter (where not (element ? '_circle_post_type')),
        '[]'::jsonb
      ) as media
    from jsonb_array_elements(coalesce(post.media, '[]'::jsonb)) with ordinality as elements(element, ordinal)
  ) as marker
  where marker.post_type in ('chat', 'experience')
)
update public.circle_community_posts as post
set
  post_type = migrated.post_type,
  media = migrated.media
from migrated_posts as migrated
where post.id = migrated.id;

-- New community content is created by users; this migration does not seed example posts.
