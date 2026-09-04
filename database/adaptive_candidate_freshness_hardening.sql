-- 港研通个性化候选 freshness 原子校验增量迁移
--
-- 前置依赖：database/adaptive_question_delivery_v1.sql
-- 可重复执行；只替换既有题位作用域 trigger function，不改历史数据。

begin;

create or replace function public.validate_practice_session_item_scope()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  session_row public.practice_sessions%rowtype;
  question_row public.questions%rowtype;
  calibration_row record;
  expected_manual_difficulty integer;
  expected_quality_status text;
  expected_quality_weight double precision;
  expected_item_difficulty double precision;
  expected_question_valid boolean;
begin
  select * into session_row
  from public.practice_sessions
  where id = new.session_id;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;

  select * into question_row
  from public.questions
  where id = new.question_id
  for share;
  if not found then
    raise exception 'adaptive_question_not_found';
  end if;

  if question_row.subject <> session_row.subject
     or question_row.exam_code not in ('COMMON', session_row.stats_exam_code)
     or (question_row.exam_code = 'COMMON' and question_row.subject not in ('中华文化', '英语运用'))
     or new.position > session_row.requested_question_count then
    raise exception 'adaptive_session_item_scope_mismatch';
  end if;
  if session_row.mode = 'special' and not exists (
    select 1
    from jsonb_array_elements(session_row.scope_filter) as selected_scope(value)
    where jsonb_typeof(selected_scope.value) = 'object'
      and jsonb_typeof(selected_scope.value->'module') = 'string'
      and (
        not (selected_scope.value ? 'submodule')
        or jsonb_typeof(selected_scope.value->'submodule') in ('null', 'string')
      )
      and btrim(selected_scope.value->>'module') = question_row.module
      and (
        nullif(btrim(selected_scope.value->>'submodule'), '') is null
        or btrim(selected_scope.value->>'submodule') = question_row.submodule
      )
  ) then
    raise exception 'adaptive_session_item_outside_selected_scope';
  end if;

  if tg_op = 'INSERT' then
    if session_row.status <> 'ACTIVE' then
      raise exception 'adaptive_session_not_active';
    end if;
    if coalesce(to_jsonb(question_row)->>'status', 'active') <> 'active' then
      raise exception 'adaptive_question_not_active';
    end if;

    if jsonb_typeof(new.strategy_metadata->'manual_difficulty') is distinct from 'number'
       or (new.strategy_metadata->>'manual_difficulty') !~ '^[1-5]$' then
      raise exception 'adaptive_candidate_changed'
        using detail = 'manual_difficulty_metadata_invalid';
    end if;
    begin
      expected_manual_difficulty :=
        (new.strategy_metadata->>'manual_difficulty')::integer;
    exception when others then
      raise exception 'adaptive_candidate_changed'
        using detail = 'manual_difficulty_metadata_invalid';
    end;
    if question_row.difficulty is distinct from expected_manual_difficulty then
      raise exception 'adaptive_candidate_changed'
        using detail = 'question_difficulty_changed';
    end if;

    select * into calibration_row
    from public.question_calibration
    where question_id = new.question_id
      and stats_exam_code = session_row.stats_exam_code
    for share;
    expected_quality_status := case
      when found then upper(coalesce(calibration_row.quality_status, 'UNREVIEWED'))
      else 'UNREVIEWED'
    end;
    expected_quality_weight := case
      when expected_quality_status = 'FLAGGED'
        then least(coalesce(calibration_row.quality_weight, 0.7), 0.4)
      else coalesce(calibration_row.quality_weight, 0.7)
    end;
    expected_item_difficulty := coalesce(
      calibration_row.item_difficulty,
      case question_row.difficulty
        when 1 then -1.6
        when 2 then -0.8
        when 3 then 0.0
        when 4 then 0.8
        when 5 then 1.6
      end
    );
    expected_question_valid :=
      expected_quality_status <> 'EXCLUDED' and expected_quality_weight > 0;

    if expected_quality_status = 'EXCLUDED'
       or jsonb_typeof(new.strategy_metadata->'quality_weight') is distinct from 'number'
       or abs(
         (new.strategy_metadata->>'quality_weight')::double precision
         - expected_quality_weight
       ) > 0.0000001
       or jsonb_typeof(new.strategy_metadata->'question_valid') is distinct from 'boolean'
       or (new.strategy_metadata->>'question_valid')::boolean
            is distinct from expected_question_valid
       or new.item_difficulty is null
       or expected_item_difficulty is null
       or abs(new.item_difficulty - expected_item_difficulty) > 0.0000001
       or not (new.strategy_metadata ? 'quality_status')
       or jsonb_typeof(new.strategy_metadata->'quality_status')
            is distinct from 'string'
       or upper(btrim(new.strategy_metadata->>'quality_status'))
            <> expected_quality_status
       then
      raise exception 'adaptive_candidate_changed'
        using detail = 'question_calibration_changed';
    end if;
  end if;
  return new;
end;
$$;

revoke all on function public.validate_practice_session_item_scope()
  from public, anon, authenticated, service_role;

notify pgrst, 'reload schema';

commit;
