-- 考研圈经验阶段与发布幂等键升级。
-- 依赖 database/circle_community.sql；在 Supabase SQL Editor 中手动执行。
-- 本迁移不猜测历史经验贴的 Z001 / Z002 考试类别，也不改写帖子正文或互动数据。

begin;

alter table public.circle_community_posts
  add column if not exists experience_stages text[] default '{}'::text[],
  add column if not exists client_request_id uuid;

-- 允许从曾经执行到一半的版本恢复，再统一为本文件定义的约束。
alter table public.circle_community_posts
  drop constraint if exists circle_community_posts_experience_stages_check;

-- 合并三类阶段来源并按固定顺序去重：
-- 1. 已存在的 experience_stages；
-- 2. media 中旧的 _circle_experience_stages 标记；
-- 3. 更早期借用 category 保存的“专业课 / 复试”。
-- Z001 / Z002 本身不代表阶段，因此不会据此补值；研友聊始终清空阶段。
with normalized_posts as (
  select
    post.id,
    case
      when post.post_type = 'experience' then array(
        select allowed.stage
        from unnest(array['申请制', '初试', '复试']::text[]) with ordinality
          as allowed(stage, stage_order)
        where allowed.stage = any(
          coalesce(post.experience_stages, '{}'::text[])
          || coalesce(markers.marker_stages, '{}'::text[])
          || case post.category
            when '专业课' then array['初试']::text[]
            when '复试' then array['复试']::text[]
            else '{}'::text[]
          end
        )
        order by allowed.stage_order
      )
      else '{}'::text[]
    end as experience_stages,
    cleaned.cleaned_media,
    cleaned.has_marker
  from public.circle_community_posts as post
  cross join lateral (
    select
      coalesce(array_agg(marker_stage.stage), '{}'::text[]) as marker_stages
    from jsonb_array_elements(
      case
        when jsonb_typeof(post.media) = 'array' then post.media
        else '[]'::jsonb
      end
    ) as media_element(element)
    cross join lateral jsonb_array_elements_text(
      case
        when jsonb_typeof(media_element.element) = 'object'
          and jsonb_typeof(media_element.element -> '_circle_experience_stages') = 'array'
          then media_element.element -> '_circle_experience_stages'
        else '[]'::jsonb
      end
    ) as marker_stage(stage)
  ) as markers
  cross join lateral (
    select
      coalesce(
        jsonb_agg(item.cleaned_element order by item.ordinal)
          filter (where not (item.is_marker and item.cleaned_element = '{}'::jsonb)),
        '[]'::jsonb
      ) as cleaned_media,
      coalesce(bool_or(item.is_marker), false) as has_marker
    from (
      select
        media_element.ordinal,
        jsonb_typeof(media_element.element) = 'object'
          and media_element.element ? '_circle_experience_stages' as is_marker,
        case
          when jsonb_typeof(media_element.element) = 'object'
            and media_element.element ? '_circle_experience_stages'
            then media_element.element - '_circle_experience_stages'
          else media_element.element
        end as cleaned_element
      from jsonb_array_elements(
        case
          when jsonb_typeof(post.media) = 'array' then post.media
          else '[]'::jsonb
        end
      ) with ordinality as media_element(element, ordinal)
    ) as item
  ) as cleaned
)
update public.circle_community_posts as post
set
  experience_stages = normalized.experience_stages,
  media = case
    when normalized.has_marker then normalized.cleaned_media
    else post.media
  end
from normalized_posts as normalized
where post.id = normalized.id
  and (
    post.experience_stages is distinct from normalized.experience_stages
    or normalized.has_marker
  );

alter table public.circle_community_posts
  alter column experience_stages set default '{}'::text[],
  alter column experience_stages set not null;

alter table public.circle_community_posts
  add constraint circle_community_posts_experience_stages_check
  check (
    (
      post_type = 'chat'
      and cardinality(experience_stages) = 0
    )
    or (
      post_type = 'experience'
      and experience_stages <@ array['申请制', '初试', '复试']::text[]
      and array_position(experience_stages, null) is null
      and cardinality(experience_stages) <= 3
      and cardinality(array_positions(experience_stages, '申请制')) <= 1
      and cardinality(array_positions(experience_stages, '初试')) <= 1
      and cardinality(array_positions(experience_stages, '复试')) <= 1
    )
  );

-- 若此前曾短暂写入重复幂等键，保留最早一条的键并只清空后续重复键；
-- 帖子本身及其正文、媒体、互动数据均保留。
with duplicate_request_ids as (
  select duplicate.id
  from (
    select
      post.id,
      row_number() over (
        partition by post.author_id, post.client_request_id
        order by post.created_at asc, post.id asc
      ) as duplicate_rank
    from public.circle_community_posts as post
    where post.client_request_id is not null
      and post.author_id is not null
  ) as duplicate
  where duplicate.duplicate_rank > 1
)
update public.circle_community_posts as post
set client_request_id = null
from duplicate_request_ids as duplicate
where post.id = duplicate.id;

create unique index if not exists uq_circle_community_posts_author_client_request
  on public.circle_community_posts (author_id, client_request_id)
  where client_request_id is not null;

-- experience_stage=... 的包含查询可使用该索引；仅索引经验贴以减少无效条目。
create index if not exists idx_circle_community_posts_experience_stages_gin
  on public.circle_community_posts using gin (experience_stages)
  where post_type = 'experience';

commit;
