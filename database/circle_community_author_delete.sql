-- 作者删除研圈帖子：用户侧立即消失，治理与申诉记录继续保留。
-- 在 Supabase SQL Editor 中执行一次；依赖 database/circle_community.sql。

begin;

alter table public.circle_community_posts
  add column if not exists author_deleted_at timestamptz;

-- 兼容应用先于迁移上线的短窗口：旧后端会在 media 内写入不可见删除标记。
with marked_posts as (
  select
    post.id,
    coalesce(
      (
        select nullif(marker ->> '_circle_author_deleted_at', '')::timestamptz
        from jsonb_array_elements(coalesce(post.media, '[]'::jsonb)) as marker
        where marker ? '_circle_author_deleted_at'
        limit 1
      ),
      now()
    ) as deleted_at,
    coalesce(
      (
        select jsonb_agg(media_item)
        from jsonb_array_elements(coalesce(post.media, '[]'::jsonb)) as media_item
        where not (media_item ? '_circle_author_deleted_at')
      ),
      '[]'::jsonb
    ) as cleaned_media
  from public.circle_community_posts as post
  where exists (
    select 1
    from jsonb_array_elements(coalesce(post.media, '[]'::jsonb)) as marker
    where marker ? '_circle_author_deleted_at'
  )
)
update public.circle_community_posts as post
set
  author_deleted_at = coalesce(post.author_deleted_at, marked.deleted_at),
  media = marked.cleaned_media,
  is_published = false,
  is_featured = false,
  updated_at = greatest(post.updated_at, marked.deleted_at)
from marked_posts as marked
where post.id = marked.id;

-- 若迁移前曾人工写入删除时间，确保这些内容不会重新出现在公开研圈。
update public.circle_community_posts
set
  is_published = false,
  is_featured = false,
  updated_at = greatest(updated_at, author_deleted_at)
where author_deleted_at is not null
  and (is_published = true or is_featured = true);

alter table public.circle_community_posts
  drop constraint if exists circle_community_posts_author_deleted_hidden_check;

alter table public.circle_community_posts
  add constraint circle_community_posts_author_deleted_hidden_check
  check (
    author_deleted_at is null
    or (is_published = false and is_featured = false)
  );

create index if not exists idx_circle_community_posts_author_active_created
  on public.circle_community_posts (author_id, created_at desc, id desc)
  where author_deleted_at is null;

comment on column public.circle_community_posts.author_deleted_at is
  '作者在客户端删除帖子的时间；保留原内容及治理外键，仅从作者列表和公开研圈隐藏。';

commit;

notify pgrst, 'reload schema';
