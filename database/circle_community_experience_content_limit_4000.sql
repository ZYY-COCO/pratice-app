-- 将经验贴正文上限提升到 4000 字，研友聊仍保持 3000 字。
-- 依赖 circle_community_posts 与 resubmit_circle_community_experience_post；
-- 在 Supabase SQL Editor 中执行一次，可安全重复执行，不改写已有帖子。

begin;

alter table public.circle_community_posts
  drop constraint if exists circle_community_posts_content_check;

-- 兼容早期建表语句自动生成、名称不同的正文长度约束。
do $$
declare
  constraint_name text;
begin
  for constraint_name in
    select constraint_row.conname
    from pg_constraint as constraint_row
    where constraint_row.conrelid = 'public.circle_community_posts'::regclass
      and constraint_row.contype = 'c'
      and pg_get_constraintdef(constraint_row.oid) ilike '%char_length%'
      and pg_get_constraintdef(constraint_row.oid) ilike '%btrim%'
      and pg_get_constraintdef(constraint_row.oid) ilike '%content%'
  loop
    execute format(
      'alter table public.circle_community_posts drop constraint %I',
      constraint_name
    );
  end loop;
end;
$$;

alter table public.circle_community_posts
  add constraint circle_community_posts_content_check
  check (
    (post_type = 'chat' and char_length(btrim(content)) between 1 and 3000)
    or (post_type = 'experience' and char_length(btrim(content)) between 1 and 4000)
  );

create or replace function public.resubmit_circle_community_experience_post(
  p_post_id uuid,
  p_author_id uuid,
  p_category text,
  p_experience_stages text[],
  p_title text,
  p_content text,
  p_media jsonb
)
returns setof public.circle_community_posts
language plpgsql
security definer
set search_path = public
as $$
declare
  v_current public.circle_community_posts%rowtype;
  v_updated public.circle_community_posts%rowtype;
  v_category text := btrim(coalesce(p_category, ''));
  v_input_stages text[] := coalesce(p_experience_stages, '{}'::text[]);
  v_stages text[];
  v_title text := btrim(coalesce(p_title, ''));
  v_content text := btrim(coalesce(p_content, ''));
begin
  if v_category not in ('Z001', 'Z002', '申请制') then
    raise exception using
      errcode = '22023',
      message = '经验贴考试类别仅支持 Z001、Z002、申请制';
  end if;

  if coalesce(array_ndims(v_input_stages), 1) > 1
    or array_position(v_input_stages, null) is not null
    or not v_input_stages <@ array['初试', '复试']::text[]
    or cardinality(v_input_stages) > 2
    or cardinality(array_positions(v_input_stages, '初试')) > 1
    or cardinality(array_positions(v_input_stages, '复试')) > 1
  then
    raise exception using
      errcode = '22023',
      message = '经验贴备考阶段仅支持初试、复试，且不可重复';
  end if;

  v_stages := array(
    select allowed.stage
    from unnest(array['初试', '复试']::text[]) with ordinality
      as allowed(stage, stage_order)
    where allowed.stage = any(v_input_stages)
    order by allowed.stage_order
  );

  if v_category in ('Z001', 'Z002')
    and cardinality(v_stages) = 0
  then
    raise exception using
      errcode = '22023',
      message = 'Z001、Z002 经验贴至少选择一个备考阶段';
  end if;

  if char_length(v_title) not between 1 and 80
    or char_length(v_content) not between 1 and 4000
  then
    raise exception using
      errcode = '22023',
      message = '经验贴标题或正文长度不符合要求';
  end if;

  if jsonb_typeof(coalesce(p_media, '[]'::jsonb)) <> 'array'
    or jsonb_array_length(coalesce(p_media, '[]'::jsonb)) > 9
  then
    raise exception using
      errcode = '22023',
      message = '经验贴图片数据不符合要求';
  end if;

  select *
  into v_current
  from public.circle_community_posts
  where id = p_post_id
  for update;

  if not found
    or v_current.post_type <> 'experience'
    or v_current.author_id is distinct from p_author_id
  then
    raise exception using errcode = 'P0002', message = '经验贴不存在';
  end if;

  if v_current.review_status is distinct from 'rejected' then
    raise exception using
      errcode = 'P0001',
      message = '只有审核未通过的经验贴可以修改后重新提交';
  end if;

  update public.circle_community_posts
  set
    category = v_category,
    experience_stages = v_stages,
    title = v_title,
    content = v_content,
    media = coalesce(p_media, '[]'::jsonb),
    review_status = 'pending',
    review_version = v_current.review_version + 1,
    review_reason_code = null,
    review_note = null,
    reviewed_by = null,
    reviewed_at = null,
    submitted_at = now(),
    is_published = false,
    is_featured = false,
    updated_at = now()
  where id = p_post_id
  returning * into v_updated;

  return next v_updated;
end;
$$;

revoke all on function public.resubmit_circle_community_experience_post(
  uuid,
  uuid,
  text,
  text[],
  text,
  text,
  jsonb
) from public, anon, authenticated;

grant execute on function public.resubmit_circle_community_experience_post(
  uuid,
  uuid,
  text,
  text[],
  text,
  text,
  jsonb
) to service_role;

commit;
