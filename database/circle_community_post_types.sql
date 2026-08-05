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

-- 保留原经验贴内容，并把它们转为可点赞、可评论、可统计浏览量的真实帖子。
insert into public.circle_community_posts (
  id, author_name, author_avatar, author_tone, post_type, category, title, content,
  like_count, comment_count, view_count, created_at
) values
  (
    '7aa84b22-9b9d-4d28-9ef8-7a09d42b0101',
    '研友 A', 'A', 'mint', 'experience', '备考节奏',
    '三科并行时，先把每天的固定题量跑顺',
    E'适合刚开始准备 Z001 的同学，把中华文化、英语运用和逻辑推理拆成可执行的日计划。\n\n先固定动作\n最容易拖慢进度的不是某一个知识点，而是每天不知道先做什么。我把三科拆成固定动作：中华文化 20 题、英语语言知识 20 题、逻辑推理 15 题，先保证不断档。\n\n错题当天处理\n错题不要堆到周末统一看。当天错的题，至少写下题干关键词、误选原因和正确选项理由；第二天开始前先看昨天的错题，再进入新题。\n\n周末只看两个指标\n复盘只看哪一科掉分最多、哪一种题型最拖时间，下周把这两个点放进每天第一组题里。',
    86, 0, 1268, '2026-08-03T08:00:00+08'
  ),
  (
    '7aa84b22-9b9d-4d28-9ef8-7a09d42b0102',
    '研友 B', '文', 'blue', 'experience', '中华文化',
    '中华文化别死背，先按人物、作品、朝代建索引',
    E'把文学、历史、艺术和科技常识放进同一张索引表，做题时更容易定位干扰项。\n\n先把知识点放进位置\n中华文化题看起来杂，但常见干扰项通常来自相近领域，例如人物和作品、朝代和制度、艺术门类和代表作。\n\n用索引表补全连接\n先建人物、作品、朝代、关键词四列。遇到新知识点就补进去，不追求一次背完，但每次补充都要和旧知识发生连接。\n\n解析只留判断理由\n解析不用抄长段材料，只保留关键判断理由，越短越容易复盘。',
    73, 0, 982, '2026-08-02T08:00:00+08'
  ),
  (
    '7aa84b22-9b9d-4d28-9ef8-7a09d42b0103',
    '研友 C', '数', 'warm', 'experience', '数学基础',
    '数学基础的提分点，常常藏在计算检查里',
    E'适合 Z002 用户，把极限、导数和积分题拆成公式选择、代入和验算三个动作。\n\n条件比公式更先出现\n很多失分来自条件没看清，尤其是极限、导数和积分里的定义域、连续性和可导性。\n\n代入前先写公式\n先写本题对应公式，再把题目条件代进去，最后才做化简，可以减少一上来就算偏的情况。\n\n最后检查问法\n做完一定检查答案有没有违反定义域、端点条件或题干问法。',
    51, 0, 746, '2026-08-01T08:00:00+08'
  ),
  (
    '7aa84b22-9b9d-4d28-9ef8-7a09d42b0104',
    '研友 D', '英', 'violet', 'experience', '英语运用',
    '英语语言知识先抓固定搭配，再回头补语法',
    E'把词汇、短语和语法分成两条线，先解决选择题里最容易反复错的搭配问题。\n\n先处理高频短语\n很多语言知识题并不是整句看不懂，而是固定搭配和词义边界没记牢。先把高频短语和动词搭配过一轮，做题速度会更稳定。\n\n错题按词性归档\n把错题按名词、动词、形容词、副词和介词搭配归类，复盘时就能看出自己经常在哪类词上犹豫。\n\n语法只抓触发条件\n重点记触发条件：看到从句、非谓语、虚拟语气的标志，就能更快排除不合适的选项。',
    48, 0, 689, '2026-07-31T08:00:00+08'
  ),
  (
    '7aa84b22-9b9d-4d28-9ef8-7a09d42b0105',
    '研友 E', '逻', 'mint', 'experience', '逻辑推理',
    '逻辑题别急着选，先把论点和论据圈出来',
    E'适合论证类题反复错的同学，用固定拆题模板降低读题压力。\n\n把题干拆成两层\n先圈论点，再划论据，确认题目在问加强、削弱、假设还是解释。\n\n选项看作用而不是语气\n很多选项语气很像正确答案，但没有真正改变论点和论据之间的关系。判断时要问：它让结论更稳，还是更不稳？\n\n错题复盘保留结构\n复盘时写清原论点、原论据、自己误选项的作用，以及正确选项为什么更贴合题目问法。',
    67, 0, 812, '2026-07-30T08:00:00+08'
  )
on conflict (id) do nothing;

insert into public.circle_community_comments (id, post_id, author_name, author_avatar, content) values
  ('7aa84b22-9b9d-4d28-9ef8-7a09d42b1001', '7aa84b22-9b9d-4d28-9ef8-7a09d42b0101', '研友小林', '林', '我也会先把固定题量跑顺，再慢慢加题。'),
  ('7aa84b22-9b9d-4d28-9ef8-7a09d42b1002', '7aa84b22-9b9d-4d28-9ef8-7a09d42b0102', '研友阿言', '言', '索引表很适合复盘，我准备从人物和作品两列先整理。'),
  ('7aa84b22-9b9d-4d28-9ef8-7a09d42b1003', '7aa84b22-9b9d-4d28-9ef8-7a09d42b0103', '研友小周', '周', '定义域和题干问法确实是我最容易漏掉的地方。'),
  ('7aa84b22-9b9d-4d28-9ef8-7a09d42b1004', '7aa84b22-9b9d-4d28-9ef8-7a09d42b0104', '研友可乐', '可', '先记搭配再做语法题的节奏很适合每天短时间复习。'),
  ('7aa84b22-9b9d-4d28-9ef8-7a09d42b1005', '7aa84b22-9b9d-4d28-9ef8-7a09d42b0105', '研友西西', '西', '先圈论点和论据后，选项判断确实清楚很多。')
on conflict (id) do nothing;

update public.circle_community_posts as post
set comment_count = counts.total
from (
  select post_id, count(*)::integer as total
  from public.circle_community_comments
  where post_id in (
    '7aa84b22-9b9d-4d28-9ef8-7a09d42b0101',
    '7aa84b22-9b9d-4d28-9ef8-7a09d42b0102',
    '7aa84b22-9b9d-4d28-9ef8-7a09d42b0103',
    '7aa84b22-9b9d-4d28-9ef8-7a09d42b0104',
    '7aa84b22-9b9d-4d28-9ef8-7a09d42b0105'
  )
  group by post_id
) as counts
where post.id = counts.post_id;
