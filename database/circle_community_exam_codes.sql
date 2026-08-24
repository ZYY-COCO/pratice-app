-- 考研圈标签与内容长度升级。
-- 仅在需要把现有 Supabase 数据迁移到 Z001 / Z002 分类时执行一次。

begin;

-- 经验贴保留考试代码/阶段标签，研友聊保留通用讨论和四个学科标签。
update public.circle_community_posts
set category = case
  when post_type = 'experience' then
    case
      when category in ('专业课', '复试') then category
      when category = 'Z002'
        or category = '数学基础'
        or title ilike '%Z002%'
        or content ilike '%Z002%'
        then 'Z002'
      else 'Z001'
    end
  when category in ('备考日常', '中华文化', '数学基础', '英语运用', '逻辑推理') then category
  when category = 'Z002'
    or title ilike '%Z002%'
    or title ilike '%数学%'
    or content ilike '%数学%'
    or content ilike '%微积分%'
    or content ilike '%导数%'
    or content ilike '%积分%'
    then '数学基础'
  when title ilike '%英语%'
    or content ilike '%英语%'
    or content ilike '%词汇%'
    or content ilike '%语法%'
    or content ilike '%短语%'
    then '英语运用'
  when title ilike '%逻辑%'
    or content ilike '%逻辑%'
    or content ilike '%论点%'
    or content ilike '%论据%'
    or content ilike '%推理%'
    then '逻辑推理'
  else '中华文化'
end;

do $$
declare
  constraint_name text;
begin
  for constraint_name in
    select conname
    from pg_constraint
    where conrelid = 'public.circle_community_posts'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) like '%category%'
  loop
    execute format('alter table public.circle_community_posts drop constraint %I', constraint_name);
  end loop;
end;
$$;

alter table public.circle_community_posts
  add constraint circle_community_posts_category_check
  check (
    (post_type = 'chat' and category in ('备考日常', '中华文化', '数学基础', '英语运用', '逻辑推理'))
    or (post_type = 'experience' and category in ('Z001', 'Z002', '专业课', '复试'))
  );

do $$
declare
  constraint_name text;
begin
  for constraint_name in
    select conname
    from pg_constraint
    where conrelid = 'public.circle_community_posts'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) like '%btrim(content)%'
  loop
    execute format('alter table public.circle_community_posts drop constraint %I', constraint_name);
  end loop;
end;
$$;

alter table public.circle_community_posts
  add constraint circle_community_posts_content_check
  check (char_length(btrim(content)) between 1 and 3000);

commit;
