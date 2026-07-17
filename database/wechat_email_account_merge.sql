-- 微信账号绑定 QQ 邮箱及账号合并支持。
-- 必须在部署依赖 /auth/bind-wechat-email 的后端代码前，于 Supabase SQL Editor 执行。

create or replace function public.merge_wechat_email_accounts(
  p_source_user_id uuid,
  p_target_user_id uuid,
  p_profile_source text
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  source_profile public.users%rowtype;
  target_profile public.users%rowtype;
  merged_profile jsonb;
begin
  if p_source_user_id = p_target_user_id then
    raise exception 'source and target accounts must be different';
  end if;

  if p_profile_source not in ('wechat', 'email') then
    raise exception 'profile source must be wechat or email';
  end if;

  select * into source_profile
  from public.users
  where id = p_source_user_id
  for update;

  select * into target_profile
  from public.users
  where id = p_target_user_id
  for update;

  if source_profile.id is null or target_profile.id is null then
    raise exception 'source or target account not found';
  end if;

  if source_profile.wechat_openid is null then
    raise exception 'source account is not linked to WeChat';
  end if;

  if target_profile.wechat_openid is not null
     and target_profile.wechat_openid <> source_profile.wechat_openid then
    raise exception 'target email is already linked to another WeChat account';
  end if;

  -- 保留所有历史作答。
  update public.user_answers
  set user_id = p_target_user_id
  where user_id = p_source_user_id;

  -- 错题按题目合并，累计错误次数并保留最近一次时间。
  insert into public.wrong_questions (
    user_id,
    question_id,
    wrong_count,
    last_wrong_at,
    created_at,
    updated_at
  )
  select
    p_target_user_id,
    question_id,
    wrong_count,
    last_wrong_at,
    created_at,
    updated_at
  from public.wrong_questions
  where user_id = p_source_user_id
  on conflict (user_id, question_id) do update
  set wrong_count = wrong_questions.wrong_count + excluded.wrong_count,
      last_wrong_at = greatest(wrong_questions.last_wrong_at, excluded.last_wrong_at),
      created_at = least(wrong_questions.created_at, excluded.created_at),
      updated_at = greatest(wrong_questions.updated_at, excluded.updated_at);

  delete from public.wrong_questions where user_id = p_source_user_id;

  -- 收藏按题目去重。
  insert into public.favorite_questions (user_id, question_id, created_at)
  select p_target_user_id, question_id, created_at
  from public.favorite_questions
  where user_id = p_source_user_id
  on conflict (user_id, question_id) do update
  set created_at = least(favorite_questions.created_at, excluded.created_at);

  delete from public.favorite_questions where user_id = p_source_user_id;

  -- 能力统计按同一考点累计并重新计算正确率。
  insert into public.ability_stats (
    user_id,
    exam_code,
    subject,
    module,
    submodule,
    total_count,
    correct_count,
    accuracy,
    updated_at
  )
  select
    p_target_user_id,
    exam_code,
    subject,
    module,
    submodule,
    total_count,
    correct_count,
    case
      when total_count > 0 then round((correct_count * 100.0 / total_count)::numeric, 2)
      else 0
    end,
    updated_at
  from public.ability_stats
  where user_id = p_source_user_id
  on conflict (user_id, exam_code, subject, module, submodule) do update
  set total_count = ability_stats.total_count + excluded.total_count,
      correct_count = ability_stats.correct_count + excluded.correct_count,
      accuracy = case
        when ability_stats.total_count + excluded.total_count > 0 then
          round((
            (ability_stats.correct_count + excluded.correct_count) * 100.0
            / (ability_stats.total_count + excluded.total_count)
          )::numeric, 2)
        else 0
      end,
      updated_at = greatest(ability_stats.updated_at, excluded.updated_at);

  delete from public.ability_stats where user_id = p_source_user_id;

  -- 其余直接归属用户的数据。
  if to_regclass('public.membership_orders') is not null then
    execute 'update public.membership_orders set user_id = $1 where user_id = $2'
      using p_target_user_id, p_source_user_id;
  end if;

  if to_regclass('public.ai_training_sessions') is not null then
    execute 'update public.ai_training_sessions set user_id = $1 where user_id = $2'
      using p_target_user_id, p_source_user_id;
  end if;

  if to_regclass('public.beta_feedback') is not null then
    execute 'update public.beta_feedback set user_id = $1 where user_id = $2'
      using p_target_user_id, p_source_user_id;
  end if;

  if to_regclass('public.user_official_message_reads') is not null then
    execute $sql$
      insert into public.user_official_message_reads (user_id, message_id, read_at)
      select $1, message_id, read_at
      from public.user_official_message_reads
      where user_id = $2
      on conflict (user_id, message_id) do update
      set read_at = greatest(user_official_message_reads.read_at, excluded.read_at)
    $sql$ using p_target_user_id, p_source_user_id;
    execute 'delete from public.user_official_message_reads where user_id = $1'
      using p_source_user_id;
  end if;

  -- 管理操作中的用户引用一并迁移，避免删除源账号后变成空值。
  if to_regclass('public.admin_action_logs') is not null then
    execute 'update public.admin_action_logs set admin_user_id = $1 where admin_user_id = $2'
      using p_target_user_id, p_source_user_id;
    execute $sql$
      update public.admin_action_logs
      set target_id = $1
      where target_type = 'user' and target_id = $2
    $sql$ using p_target_user_id, p_source_user_id;
  end if;

  if to_regclass('public.official_messages') is not null then
    execute 'update public.official_messages set created_by = $1 where created_by = $2'
      using p_target_user_id, p_source_user_id;
    execute 'update public.official_messages set updated_by = $1 where updated_by = $2'
      using p_target_user_id, p_source_user_id;
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'questions'
      and column_name = 'archived_by'
  ) then
    execute 'update public.questions set archived_by = $1 where archived_by = $2'
      using p_target_user_id, p_source_user_id;
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'questions'
      and column_name = 'reviewed_by'
  ) then
    execute 'update public.questions set reviewed_by = $1 where reviewed_by = $2'
      using p_target_user_id, p_source_user_id;
  end if;

  if exists (
    select 1
    from information_schema.columns
    where table_schema = 'public'
      and table_name = 'beta_feedback'
      and column_name = 'handled_by'
  ) then
    execute 'update public.beta_feedback set handled_by = $1 where handled_by = $2'
      using p_target_user_id, p_source_user_id;
  end if;

  -- 始终保留权益更高、有效期更长的会员状态。
  if source_profile.membership_status = 'active'
     and (
        target_profile.membership_status <> 'active'
        or coalesce(source_profile.membership_expires_at, 'infinity'::timestamptz)
          > coalesce(target_profile.membership_expires_at, 'infinity'::timestamptz)
      ) then
    update public.users
    set membership_status = source_profile.membership_status,
        membership_plan = source_profile.membership_plan,
        membership_started_at = source_profile.membership_started_at,
        membership_expires_at = source_profile.membership_expires_at,
        membership_updated_at = source_profile.membership_updated_at
    where id = p_target_user_id;
  end if;

  -- 用户只选择昵称、头像、性别和考试目标使用哪一侧；学习数据始终合并。
  if p_profile_source = 'wechat' then
    update public.users
    set nickname = coalesce(source_profile.nickname, nickname),
        avatar_url = coalesce(source_profile.avatar_url, avatar_url),
        gender = coalesce(source_profile.gender, gender),
        exam_target = coalesce(source_profile.exam_target, exam_target)
    where id = p_target_user_id;
  end if;

  -- 先释放唯一 OpenID，再绑定到保留的邮箱账号。
  update public.users
  set wechat_openid = null
  where id = p_source_user_id;

  update public.users
  set wechat_openid = source_profile.wechat_openid
  where id = p_target_user_id;

  delete from public.users where id = p_source_user_id;

  select to_jsonb(u) into merged_profile
  from public.users u
  where u.id = p_target_user_id;

  return merged_profile;
end;
$$;

revoke all on function public.merge_wechat_email_accounts(uuid, uuid, text) from public;
revoke all on function public.merge_wechat_email_accounts(uuid, uuid, text) from anon;
revoke all on function public.merge_wechat_email_accounts(uuid, uuid, text) from authenticated;
grant execute on function public.merge_wechat_email_accounts(uuid, uuid, text) to service_role;
