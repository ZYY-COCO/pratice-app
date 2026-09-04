  -- 考研圈经验贴“申请制”考试类别升级。
  -- 依赖 database/circle_community.sql 与
  -- database/circle_community_experience_stages_and_idempotency.sql。
  -- 在 Supabase SQL Editor 中手动执行；脚本可重复执行。

  begin;

  alter table public.circle_community_posts
    add column if not exists experience_stages text[] default '{}'::text[];

  -- 先移除旧分类/阶段约束，避免迁移“申请制”时被旧白名单拦截。
  alter table public.circle_community_posts
    drop constraint if exists circle_community_posts_category_check,
    drop constraint if exists circle_community_posts_experience_stages_check;

  -- 旧数据曾把“申请制”保存在 experience_stages：
  -- 现在将其提升为考试类别，并只保留“初试 / 复试”阶段。
  -- 其他帖子也同步按固定顺序去重；研友聊的阶段始终清空。
  with normalized_posts as (
    select
      post.id,
      case
        when post.post_type = 'experience'
          and '申请制' = any(coalesce(post.experience_stages, '{}'::text[]))
          then '申请制'
        else post.category
      end as category,
      case
        when post.post_type = 'experience' then array(
          select allowed.stage
          from unnest(array['初试', '复试']::text[]) with ordinality
            as allowed(stage, stage_order)
          where allowed.stage = any(coalesce(post.experience_stages, '{}'::text[]))
          order by allowed.stage_order
        )
        else '{}'::text[]
      end as experience_stages
    from public.circle_community_posts as post
  )
  update public.circle_community_posts as post
  set
    category = normalized.category,
    experience_stages = normalized.experience_stages
  from normalized_posts as normalized
  where post.id = normalized.id
    and (
      post.category is distinct from normalized.category
      or post.experience_stages is distinct from normalized.experience_stages
    );

  alter table public.circle_community_posts
    alter column experience_stages set default '{}'::text[],
    alter column experience_stages set not null;

  -- “专业课 / 复试”仅为历史兼容值；新接口只写入 Z001、Z002、申请制。
  alter table public.circle_community_posts
    add constraint circle_community_posts_category_check
    check (
      (
        post_type = 'chat'
        and category in ('备考日常', '中华文化', '数学基础', '英语运用', '逻辑推理')
      )
      or (
        post_type = 'experience'
        and category in ('Z001', 'Z002', '申请制', '专业课', '复试')
      )
    ) not valid;

  -- 表级约束只负责阶段集合、非空元素和去重，允许历史 Z001 / Z002 空阶段继续互动。
  -- 新建与重提时的 Z001 / Z002 阶段必填分别由后端 Pydantic 和下方 RPC 强制；
  -- 待历史空阶段完成核对后，再单独增加并验证数据库必填约束。
  alter table public.circle_community_posts
    add constraint circle_community_posts_experience_stages_check
    check (
      (
        post_type = 'chat'
        and cardinality(experience_stages) = 0
      )
      or (
        post_type = 'experience'
        and experience_stages <@ array['初试', '复试']::text[]
        and array_position(experience_stages, null) is null
        and cardinality(experience_stages) <= 2
        and cardinality(array_positions(experience_stages, '初试')) <= 1
        and cardinality(array_positions(experience_stages, '复试')) <= 1
      )
    ) not valid;

  -- 数据已在上方完成归一，两项约束都必须立即验证；若发现未知历史值，
  -- 整个事务会回滚，而不会留下可能阻断旧帖互动的 NOT VALID 约束。
  alter table public.circle_community_posts
    validate constraint circle_community_posts_category_check;
  alter table public.circle_community_posts
    validate constraint circle_community_posts_experience_stages_check;

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
      or char_length(v_content) not between 1 and 3000
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
