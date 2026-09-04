-- 港研通综合刷题增量迁移 V1
--
-- 前置依赖：database/adaptive_question_delivery_v1.sql
-- 本文件增加综合刷题的固定整轮 claim 与会话级交卷清单锁，并就地替换
-- 受综合交卷隔离影响的既有 RPC；不会重跑旧迁移中的历史重建和表锁步骤。

begin;

-- Refuse to upgrade an unknown or partially migrated first-layer revision.
-- The production predecessor exists in two reviewed shapes: the original
-- special-practice-only functions and the later first-layer functions that
-- already contain the comprehensive embargo guards.  Both are safe inputs to
-- the same CREATE OR REPLACE definitions below.  Any other body, privilege,
-- signature state, or active adaptive session aborts this transaction before
-- the first schema change.
do $predecessor_gate$
declare
  expected record;
  actual_oid oid;
  actual_hash text;
  actual_security_definer boolean;
  actual_config text[];
  actual_volatility text;
  actual_owner text;
  actual_acl text;
  actual_service_execute boolean;
begin
  if exists (
    select 1
    from public.practice_sessions
    where status = 'ACTIVE'
  ) then
    raise exception 'adaptive_comprehensive_active_session_present';
  end if;

  if to_regprocedure(
       'public.record_answer_submission(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
     ) is null
     or to_regprocedure(
       'public.record_answer_submission_pre_comprehensive_v1(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
     ) is not null
     or to_regprocedure(
       'public.record_answer_submission(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid,text,uuid,text,text)'
     ) is not null then
    raise exception 'adaptive_comprehensive_answer_rpc_transition_invalid';
  end if;

  if to_regprocedure(
       'public.claim_adaptive_comprehensive_practice_items(uuid,uuid,bigint,jsonb,timestamptz)'
     ) is not null
     or to_regprocedure(
       'public.assert_single_answer_feedback_allowed(uuid,uuid,uuid)'
     ) is not null
     or to_regprocedure(
       'public.begin_adaptive_comprehensive_submission(uuid,uuid,text,text,jsonb,timestamptz)'
     ) is not null
     or to_regprocedure(
       'public.record_adaptive_comprehensive_skip(uuid,uuid,uuid,text,text,timestamptz)'
     ) is not null
     or to_regprocedure(
       'public.finalize_adaptive_comprehensive_submission(uuid,uuid,text,text,timestamptz)'
     ) is not null
     or to_regprocedure(
       'public.get_adaptive_candidate_history_v1(uuid,text,text,uuid[],integer,boolean)'
     ) is not null
     or to_regprocedure(
       'public.persist_adaptive_comprehensive_answers_batch(uuid,uuid,text,text,timestamptz)'
     ) is not null then
    raise exception 'adaptive_comprehensive_partial_or_prior_migration_present';
  end if;

  for expected in
    select *
    from (
      values
        (
          'public.claim_next_adaptive_practice_item(uuid,uuid,uuid,integer,bigint,jsonb,timestamptz)',
          array['a49e0d6863b722198224766e2295f1da']::text[],
          'v', true
        ),
        (
          'public.apply_adaptive_model_update(uuid,uuid,uuid,jsonb,timestamptz)',
          array['9dcb9ac1196ce9af928bf439a1f2b005']::text[],
          'v', true
        ),
        (
          'public.get_adaptive_question_snapshot(uuid,uuid,uuid)',
          array[
            'd2e2be3a78f1a5b9522c639be8729de7',
            '7255f4d5a37a55bd49ec09c78c66f6ad'
          ]::text[],
          's', true
        ),
        (
          'public.record_practice_session_item_event(uuid,uuid,uuid,text,timestamptz)',
          array[
            '73bfd2b45fa01b4535aa703222d5a676',
            '42b4400fa3fdc080055d11849807976b'
          ]::text[],
          'v', true
        ),
        (
          'public.complete_practice_session(uuid,uuid,text,timestamptz)',
          array[
            'b1557754912e57cddcdad7c7062d9df7',
            'c945ae789dd4ad8074902b857dd356b0'
          ]::text[],
          'v', true
        ),
        (
          'public.get_pending_adaptive_update_items(uuid,text,text,uuid,integer)',
          array[
            '3f09faf68c2a5ecd1c0fa6ce541c9334',
            'a4f121c8006d6b4b4046c85f242834c4'
          ]::text[],
          's', true
        ),
        (
          'public.record_answer_submission(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)',
          array['d377f77e8a3cf4fc85c6b4e49b52fcc9']::text[],
          'v', true
        ),
        (
          'public.validate_practice_session_item_scope()',
          array['6fd9e1cfe1d526a36a64b52e014c4dd1']::text[],
          'v', true
        )
    ) as reviewed(
      signature,
      allowed_hashes,
      expected_volatility,
      service_can_execute
    )
  loop
    actual_oid := to_regprocedure(expected.signature);
    if actual_oid is null then
      raise exception 'adaptive_comprehensive_predecessor_missing'
        using detail = expected.signature;
    end if;

    select
      md5(btrim(replace(procedure.prosrc, chr(13), ''), E' \t\n')),
      procedure.prosecdef,
      procedure.proconfig,
      procedure.provolatile::text,
      pg_get_userbyid(procedure.proowner),
      procedure.proacl::text,
      coalesce(has_function_privilege('service_role', procedure.oid, 'EXECUTE'), false)
    into
      actual_hash,
      actual_security_definer,
      actual_config,
      actual_volatility,
      actual_owner,
      actual_acl,
      actual_service_execute
    from pg_proc as procedure
    where procedure.oid = actual_oid;

    if not (actual_hash = any(expected.allowed_hashes))
       or not actual_security_definer
       or not coalesce('search_path=public, pg_temp' = any(actual_config), false)
       or actual_volatility <> expected.expected_volatility
       or actual_owner <> 'postgres'
       or actual_acl <> '{postgres=X/postgres,service_role=X/postgres}'
       or coalesce(has_function_privilege('anon', actual_oid, 'EXECUTE'), false)
       or coalesce(has_function_privilege('authenticated', actual_oid, 'EXECUTE'), false)
       or actual_service_execute is distinct from expected.service_can_execute then
      raise exception 'adaptive_comprehensive_predecessor_drift'
        using detail = expected.signature || ':' || coalesce(actual_hash, 'missing');
    end if;
  end loop;
end;
$predecessor_gate$;

create or replace function public.claim_adaptive_comprehensive_practice_items(
  p_user_id uuid,
  p_session_id uuid,
  p_expected_subject_state_version bigint,
  p_items jsonb,
  p_now timestamptz default now()
)
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  session_snapshot public.practice_sessions%rowtype;
  session_row public.practice_sessions%rowtype;
  subject_row public.user_subject_state%rowtype;
  question_row public.questions%rowtype;
  calibration_row public.question_calibration%rowtype;
  inserted_item public.practice_session_items%rowtype;
  entry jsonb;
  item_payload jsonb;
  selected_question_id uuid;
  requested_position integer;
  position_index integer;
  existing_count integer;
  existing_snapshot_count integer;
  selection_reason text;
  target_zone text;
  predicted_probability double precision;
  theta_before double precision;
  item_difficulty double precision;
  score_components jsonb;
  strategy_metadata jsonb;
  is_diagnostic boolean;
  is_challenge boolean;
  fallback_reason text;
  result_items jsonb;
begin
  if p_user_id is null
     or p_session_id is null
     or p_expected_subject_state_version is null
     or p_expected_subject_state_version < 0
     or p_now is null
     or p_items is null
     or jsonb_typeof(p_items) is distinct from 'array' then
    raise exception 'adaptive_comprehensive_claim_invalid';
  end if;

  select * into session_snapshot
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;

  -- Serialize the moment a fixed round becomes answer-embargoed against the
  -- public single-answer assertion and every answer write for this learner.
  perform pg_advisory_xact_lock(
    hashtextextended(p_user_id::text || ':adaptive_comprehensive_embargo', 0)
  );
  perform pg_advisory_xact_lock(
    hashtextextended(
      p_user_id::text || ':' || session_snapshot.stats_exam_code || ':' || session_snapshot.subject,
      0
    )
  );

  select * into session_row
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id
  for update;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;
  if session_row.stats_exam_code <> session_snapshot.stats_exam_code
     or session_row.subject <> session_snapshot.subject then
    raise exception 'adaptive_session_scope_changed';
  end if;
  if session_row.mode <> 'comprehensive' then
    raise exception 'adaptive_practice_mode_mismatch';
  end if;
  if session_row.status <> 'ACTIVE' then
    raise exception 'adaptive_session_not_active';
  end if;

  -- Idempotent recovery is authoritative once the complete fixed round and all
  -- private snapshots exist.  A later answer in the same subject may advance
  -- state_version, but it must never make this session return a different list.
  select count(*)::integer into existing_count
  from public.practice_session_items
  where session_id = p_session_id;
  if existing_count > 0 then
    select count(*)::integer into existing_snapshot_count
    from public.practice_session_items item
    join public.practice_session_item_question_snapshots snapshot
      on snapshot.practice_session_item_id = item.id
     and snapshot.question_id = item.question_id
    where item.session_id = p_session_id;
    if existing_count <> session_row.requested_question_count
       or existing_snapshot_count <> existing_count then
      raise exception 'adaptive_comprehensive_round_incomplete';
    end if;
    select coalesce(
      jsonb_agg(
        to_jsonb(item) || jsonb_build_object(
          'question_snapshot', snapshot.question_snapshot
        )
        order by item.position
      ),
      '[]'::jsonb
    ) into result_items
    from public.practice_session_items item
    join public.practice_session_item_question_snapshots snapshot
      on snapshot.practice_session_item_id = item.id
     and snapshot.question_id = item.question_id
    where item.session_id = p_session_id;
    return result_items;
  end if;

  insert into public.user_subject_state (
    user_id, stats_exam_code, subject, model_version
  ) values (
    p_user_id, session_row.stats_exam_code, session_row.subject, session_row.model_version
  ) on conflict (user_id, stats_exam_code, subject) do nothing;

  select * into subject_row
  from public.user_subject_state
  where user_id = p_user_id
    and stats_exam_code = session_row.stats_exam_code
    and subject = session_row.subject
  for update;
  if not found then
    raise exception 'adaptive_subject_state_not_found';
  end if;
  if subject_row.state_version <> p_expected_subject_state_version then
    raise exception 'adaptive_state_conflict';
  end if;

  if exists (
    select 1
    from public.practice_sessions pending_session
    join public.practice_session_items pending_item
      on pending_item.session_id = pending_session.id
    where pending_session.user_id = p_user_id
      and pending_session.stats_exam_code = session_row.stats_exam_code
      and pending_session.subject = session_row.subject
      and pending_item.answer_id is not null
      and not exists (
        select 1
        from public.adaptive_model_updates applied_update
        where applied_update.answer_id = pending_item.answer_id
      )
  ) then
    raise exception 'adaptive_update_pending';
  end if;

  if jsonb_array_length(p_items) <> session_row.requested_question_count then
    raise exception 'adaptive_comprehensive_claim_count_mismatch';
  end if;

  for position_index in 1..session_row.requested_question_count loop
    entry := p_items -> (position_index - 1);
    if jsonb_typeof(entry) is distinct from 'object'
       or jsonb_typeof(entry->'question_id') is distinct from 'string'
       or jsonb_typeof(entry->'position') is distinct from 'number'
       or jsonb_typeof(entry->'item') is distinct from 'object' then
      raise exception 'adaptive_comprehensive_claim_invalid_shape';
    end if;
    begin
      selected_question_id := (entry->>'question_id')::uuid;
      requested_position := (entry->>'position')::integer;
    exception when others then
      raise exception 'adaptive_comprehensive_claim_invalid_value';
    end;
    if requested_position <> position_index then
      raise exception 'adaptive_comprehensive_claim_position_mismatch';
    end if;

    item_payload := entry->'item';
    if jsonb_typeof(item_payload->'selection_reason') is distinct from 'string'
       or jsonb_typeof(item_payload->'target_zone') is distinct from 'string'
       or jsonb_typeof(item_payload->'predicted_probability') is distinct from 'number'
       or jsonb_typeof(item_payload->'theta_before') is distinct from 'number'
       or jsonb_typeof(item_payload->'item_difficulty') is distinct from 'number'
       or jsonb_typeof(item_payload->'score_components') is distinct from 'object'
       or jsonb_typeof(item_payload->'strategy_metadata') is distinct from 'object'
       or jsonb_typeof(item_payload->'is_diagnostic') is distinct from 'boolean'
       or jsonb_typeof(item_payload->'is_challenge') is distinct from 'boolean'
       or (
         item_payload ? 'fallback_reason'
         and jsonb_typeof(item_payload->'fallback_reason') not in ('null', 'string')
       ) then
      raise exception 'adaptive_comprehensive_claim_invalid_shape';
    end if;
    begin
      selection_reason := btrim(item_payload->>'selection_reason');
      target_zone := lower(btrim(item_payload->>'target_zone'));
      predicted_probability := (item_payload->>'predicted_probability')::double precision;
      theta_before := (item_payload->>'theta_before')::double precision;
      item_difficulty := (item_payload->>'item_difficulty')::double precision;
      score_components := item_payload->'score_components';
      strategy_metadata := item_payload->'strategy_metadata';
      is_diagnostic := (item_payload->>'is_diagnostic')::boolean;
      is_challenge := (item_payload->>'is_challenge')::boolean;
      fallback_reason := nullif(btrim(item_payload->>'fallback_reason'), '');
    exception when others then
      raise exception 'adaptive_comprehensive_claim_invalid_value';
    end;
    if char_length(selection_reason) not between 1 and 120
       or target_zone not in ('diagnostic', 'consolidation', 'main', 'challenge', 'coverage')
       or predicted_probability not between 0 and 1
       or theta_before not between -6 and 6
       or abs(theta_before - subject_row.theta) > 0.0000001
       or item_difficulty not between -6 and 6 then
      raise exception 'adaptive_comprehensive_claim_invalid_value';
    end if;

    select * into question_row
    from public.questions
    where id = selected_question_id
    for share;
    if not found then
      raise exception 'adaptive_question_not_found';
    end if;
    if question_row.subject <> session_row.subject
       or question_row.exam_code not in ('COMMON', session_row.stats_exam_code)
       or (
         question_row.exam_code = 'COMMON'
         and question_row.subject not in ('中华文化', '英语运用')
       )
       or coalesce(to_jsonb(question_row)->>'status', 'active') <> 'active' then
      raise exception 'adaptive_session_item_scope_mismatch';
    end if;

    -- Comprehensive rounds are deliberately bounded to D1-D4. D5 remains an
    -- explicitly gated, one-at-a-time challenge owned by the specialist claim
    -- path and must not enter an immutable comprehensive batch even if an
    -- application-side candidate filter regresses.
    if question_row.difficulty is null
       or question_row.difficulty not between 1 and 4 then
      raise exception 'adaptive_comprehensive_difficulty_out_of_range';
    end if;

    if is_diagnostic then
      select * into calibration_row
      from public.question_calibration
      where question_calibration.question_id = selected_question_id
        and question_calibration.stats_exam_code = session_row.stats_exam_code
      for share;
      if not found
         or calibration_row.quality_status <> 'APPROVED'
         or calibration_row.quality_weight < 0.7
         or not calibration_row.is_diagnostic_candidate
         or jsonb_typeof(strategy_metadata->'manual_difficulty') is distinct from 'number'
         or (strategy_metadata->>'manual_difficulty')::integer <> question_row.difficulty then
        raise exception 'adaptive_trusted_candidate_changed';
      end if;
    end if;

    insert into public.practice_session_items (
      session_id, question_id, position, item_status, selection_reason,
      target_zone, predicted_probability, theta_before, item_difficulty,
      score_components, strategy_metadata, is_diagnostic, is_challenge,
      fallback_reason, selected_at, created_at, updated_at
    ) values (
      p_session_id, selected_question_id, requested_position, 'SELECTED', selection_reason,
      target_zone, predicted_probability, theta_before, item_difficulty,
      score_components, strategy_metadata, is_diagnostic, is_challenge,
      fallback_reason, p_now, p_now, p_now
    ) returning * into inserted_item;

    insert into public.practice_session_item_question_snapshots (
      practice_session_item_id, question_id, question_snapshot, created_at
    ) values (
      inserted_item.id, question_row.id, to_jsonb(question_row), p_now
    );
  end loop;

  update public.practice_sessions
  set last_activity_at = p_now,
      updated_at = p_now
  where id = p_session_id;

  select coalesce(
    jsonb_agg(
      to_jsonb(item) || jsonb_build_object(
        'question_snapshot', snapshot.question_snapshot
      )
      order by item.position
    ),
    '[]'::jsonb
  ) into result_items
  from public.practice_session_items item
  join public.practice_session_item_question_snapshots snapshot
    on snapshot.practice_session_item_id = item.id
   and snapshot.question_id = item.question_id
  where item.session_id = p_session_id;
  return result_items;
end;
$$;

create or replace function public.assert_single_answer_feedback_allowed(
  p_user_id uuid,
  p_question_id uuid,
  p_practice_session_item_id uuid default null
)
returns boolean
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  item_question_id uuid;
  item_mode text;
  item_session_status text;
begin
  if p_user_id is null or p_question_id is null then
    raise exception 'adaptive_answer_feedback_invalid';
  end if;

  -- This user-wide gate is also acquired by comprehensive claim/begin and by
  -- record_answer_submission. It prevents a question-only legacy call from
  -- overtaking the transaction that makes a fixed round active and private.
  perform pg_advisory_xact_lock(
    hashtextextended(p_user_id::text || ':adaptive_comprehensive_embargo', 0)
  );

  if p_practice_session_item_id is not null then
    select item.question_id, session.mode, session.status
    into item_question_id, item_mode, item_session_status
    from public.practice_session_items item
    join public.practice_sessions session on session.id = item.session_id
    where item.id = p_practice_session_item_id
      and session.user_id = p_user_id;
    if not found or item_question_id <> p_question_id then
      raise exception 'adaptive_session_item_scope_mismatch';
    end if;
    if item_mode = 'comprehensive' and item_session_status = 'ACTIVE' then
      raise exception 'adaptive_comprehensive_batch_required';
    end if;
  end if;

  if exists (
    select 1
    from public.practice_session_items item
    join public.practice_sessions session on session.id = item.session_id
    where session.user_id = p_user_id
      and session.mode = 'comprehensive'
      and session.status = 'ACTIVE'
      and item.question_id = p_question_id
  ) then
    raise exception 'adaptive_comprehensive_batch_required';
  end if;

  return true;
end;
$$;

-- Upgrade an already-deployed pre-comprehensive answer RPC without replaying
-- the base migration's historical rebuild. Fresh installs already have the
-- extended signature, so this block deliberately leaves that implementation
-- in place. Existing installs rename the old core behind a revoked private
-- name and expose one capability-validating wrapper with an unambiguous shape.
do $answer_rpc_upgrade$
begin
  if to_regprocedure(
    'public.record_answer_submission(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid,text,uuid,text,text)'
  ) is null then
    if to_regprocedure(
      'public.record_answer_submission_pre_comprehensive_v1(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
    ) is null then
      if to_regprocedure(
        'public.record_answer_submission(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
      ) is null then
        raise exception 'adaptive_answer_rpc_upgrade_source_missing';
      end if;
      execute 'alter function public.record_answer_submission(
        uuid, uuid, text, text, boolean, integer, text, text, text, text,
        boolean, timestamptz, uuid
      ) rename to record_answer_submission_pre_comprehensive_v1';
      execute 'revoke all on function public.record_answer_submission_pre_comprehensive_v1(
        uuid, uuid, text, text, boolean, integer, text, text, text, text,
        boolean, timestamptz, uuid
      ) from public, anon, authenticated, service_role';
    end if;

    execute $create_answer_wrapper$
      create function public.record_answer_submission(
        p_user_id uuid,
        p_question_id uuid,
        p_client_submission_id text,
        p_selected_answer text,
        p_is_correct boolean,
        p_used_time integer,
        p_exam_code text,
        p_subject text,
        p_module text,
        p_submodule text,
        p_is_ai_generated boolean default false,
        p_now timestamptz default now(),
        p_practice_session_item_id uuid default null,
        p_submission_kind text default 'single',
        p_comprehensive_session_id uuid default null,
        p_comprehensive_client_submission_id text default null,
        p_comprehensive_manifest_hash text default null
      )
      returns jsonb
      language plpgsql
      security definer
      set search_path = public, pg_temp
      as $answer_wrapper$
      declare
        normalized_client_id text := nullif(btrim(coalesce(p_client_submission_id, '')), '');
        normalized_submission_kind text := lower(btrim(coalesce(p_submission_kind, '')));
        normalized_comprehensive_client_id text := nullif(
          btrim(coalesce(p_comprehensive_client_submission_id, '')),
          ''
        );
        session_snapshot public.practice_sessions%rowtype;
        session_row public.practice_sessions%rowtype;
        item_row public.practice_session_items%rowtype;
        manifest jsonb;
        answer_entry jsonb;
      begin
        if p_user_id is null or p_question_id is null
           or p_selected_answer not in ('A', 'B', 'C', 'D')
           or p_used_time is null or p_used_time not between 0 and 86400
           or p_exam_code not in ('Z001', 'Z002')
           or p_now is null
           or normalized_submission_kind not in ('single', 'comprehensive_batch') then
          raise exception 'answer_submission_invalid';
        end if;
        if p_practice_session_item_id is not null and normalized_client_id is null then
          raise exception 'adaptive_answer_requires_client_submission_id';
        end if;
        if normalized_submission_kind = 'single' and (
          p_comprehensive_session_id is not null
          or normalized_comprehensive_client_id is not null
          or p_comprehensive_manifest_hash is not null
        ) then
          raise exception 'adaptive_comprehensive_submission_state_invalid';
        end if;
        if normalized_submission_kind = 'comprehensive_batch' and (
          p_practice_session_item_id is null
          or p_comprehensive_session_id is null
          or normalized_comprehensive_client_id is null
          or char_length(normalized_comprehensive_client_id) not between 1 and 120
          or p_comprehensive_manifest_hash is null
          or p_comprehensive_manifest_hash !~ '^[0-9a-f]{64}$'
        ) then
          raise exception 'adaptive_comprehensive_submission_state_invalid';
        end if;

        perform pg_advisory_xact_lock(
          hashtextextended(p_user_id::text || ':adaptive_comprehensive_embargo', 0)
        );

        if p_practice_session_item_id is null then
          if normalized_submission_kind <> 'single' then
            raise exception 'adaptive_comprehensive_submission_state_invalid';
          end if;
          if exists (
            select 1
            from public.practice_session_items embargoed_item
            join public.practice_sessions embargoed_session
              on embargoed_session.id = embargoed_item.session_id
            where embargoed_session.user_id = p_user_id
              and embargoed_session.mode = 'comprehensive'
              and embargoed_session.status = 'ACTIVE'
              and embargoed_item.question_id = p_question_id
          ) then
            raise exception 'adaptive_comprehensive_batch_required';
          end if;
        else
          select session.* into session_snapshot
          from public.practice_sessions session
          join public.practice_session_items item on item.session_id = session.id
          where item.id = p_practice_session_item_id
            and session.user_id = p_user_id;
          if not found then
            raise exception 'adaptive_session_not_found';
          end if;
          perform pg_advisory_xact_lock(
            hashtextextended(
              p_user_id::text || ':' || session_snapshot.stats_exam_code || ':' || session_snapshot.subject,
              0
            )
          );
          select * into session_row
          from public.practice_sessions
          where id = session_snapshot.id and user_id = p_user_id
          for update;
          select * into item_row
          from public.practice_session_items
          where id = p_practice_session_item_id and session_id = session_row.id
          for update;
          if not found or item_row.question_id <> p_question_id then
            raise exception 'adaptive_scope_mismatch';
          end if;

          if session_row.mode = 'comprehensive' then
            if normalized_submission_kind <> 'comprehensive_batch'
               or p_comprehensive_session_id is distinct from session_row.id then
              raise exception 'adaptive_comprehensive_batch_required';
            end if;
            manifest := session_row.strategy_config->'comprehensive_submission';
            if jsonb_typeof(manifest) is distinct from 'object'
               or manifest->>'client_submission_id' <> normalized_comprehensive_client_id
               or manifest->>'manifest_hash' <> p_comprehensive_manifest_hash
               or upper(coalesce(manifest->>'phase', '')) not in ('LOCKED', 'COMPLETED')
               or jsonb_typeof(manifest->'answers') is distinct from 'array'
               or not (
                 (upper(manifest->>'phase') = 'LOCKED' and session_row.status = 'ACTIVE')
                 or
                 (upper(manifest->>'phase') = 'COMPLETED' and session_row.status = 'COMPLETED')
               ) then
              raise exception 'adaptive_comprehensive_submission_state_invalid';
            end if;
            select value into answer_entry
            from jsonb_array_elements(manifest->'answers') manifest_answer(value)
            where value->>'practice_session_item_id' = p_practice_session_item_id::text
              and (value->>'position')::integer = item_row.position
            limit 1;
            if not found
               or answer_entry->'selected_answer' = 'null'::jsonb
               or answer_entry->>'selected_answer' <> p_selected_answer
               or (answer_entry->>'used_time')::integer <> p_used_time
               or answer_entry->>'client_submission_id' <> normalized_client_id then
              raise exception 'adaptive_comprehensive_answer_manifest_mismatch';
            end if;
          elsif normalized_submission_kind <> 'single' then
            raise exception 'adaptive_comprehensive_submission_state_invalid';
          end if;
        end if;

        return public.record_answer_submission_pre_comprehensive_v1(
          p_user_id,
          p_question_id,
          p_client_submission_id,
          p_selected_answer,
          p_is_correct,
          p_used_time,
          p_exam_code,
          p_subject,
          p_module,
          p_submodule,
          p_is_ai_generated,
          p_now,
          p_practice_session_item_id
        );
      end;
      $answer_wrapper$
    $create_answer_wrapper$;
  end if;

  if to_regprocedure(
    'public.record_answer_submission_pre_comprehensive_v1(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
  ) is not null then
    execute 'revoke all on function public.record_answer_submission_pre_comprehensive_v1(
      uuid, uuid, text, text, boolean, integer, text, text, text, text,
      boolean, timestamptz, uuid
    ) from public, anon, authenticated, service_role';
  end if;

  if to_regprocedure(
    'public.record_answer_submission(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
  ) is not null then
    execute 'drop function public.record_answer_submission(
      uuid, uuid, text, text, boolean, integer, text, text, text, text,
      boolean, timestamptz, uuid
    )';
  end if;
end;
$answer_rpc_upgrade$;

-- Keep this migration independently upgradeable after the original adaptive
-- migration has already been applied. These same-signature replacements add
-- the comprehensive embargo/finalize rules without replaying any base-table
-- rebuild, backfill, or locking DDL from adaptive_question_delivery_v1.sql.
create or replace function public.get_adaptive_question_snapshot(
  p_user_id uuid,
  p_practice_session_item_id uuid,
  p_question_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  result_snapshot jsonb;
  session_mode text;
  session_status text;
begin
  if p_user_id is null
     or p_practice_session_item_id is null
     or p_question_id is null then
    raise exception 'adaptive_question_snapshot_invalid_identity';
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(p_user_id::text || ':adaptive_comprehensive_embargo', 0)
  );

  select snapshot.question_snapshot, session.mode, session.status
  into result_snapshot, session_mode, session_status
  from public.practice_session_item_question_snapshots snapshot
  join public.practice_session_items item
    on item.id = snapshot.practice_session_item_id
   and item.question_id = snapshot.question_id
  join public.practice_sessions session on session.id = item.session_id
  where snapshot.practice_session_item_id = p_practice_session_item_id
    and snapshot.question_id = p_question_id
    and session.user_id = p_user_id;

  if not found then
    raise exception 'adaptive_question_snapshot_not_found';
  end if;
  if session_mode = 'comprehensive' and session_status = 'ACTIVE' then
    raise exception 'adaptive_comprehensive_batch_required';
  end if;
  return result_snapshot;
end;
$$;

create or replace function public.record_practice_session_item_event(
  p_user_id uuid,
  p_session_id uuid,
  p_session_item_id uuid,
  p_event_type text,
  p_now timestamptz default now()
)
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  session_snapshot public.practice_sessions%rowtype;
  session_row public.practice_sessions%rowtype;
  item_row public.practice_session_items%rowtype;
  comprehensive_manifest jsonb;
begin
  if p_user_id is null or p_session_id is null or p_session_item_id is null
     or p_now is null
     or p_event_type is null
     or p_event_type not in ('presented', 'answer_viewed', 'skipped', 'abandoned') then
    raise exception 'adaptive_event_invalid';
  end if;

  select * into session_snapshot
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(p_user_id::text || ':adaptive_comprehensive_embargo', 0)
  );
  perform pg_advisory_xact_lock(
    hashtextextended(
      p_user_id::text || ':' || session_snapshot.stats_exam_code || ':' || session_snapshot.subject,
      0
    )
  );

  select * into session_row
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id
  for update;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;

  select * into item_row
  from public.practice_session_items
  where id = p_session_item_id and session_id = p_session_id
  for update;
  if not found then
    raise exception 'adaptive_session_item_not_found';
  end if;

  comprehensive_manifest := session_row.strategy_config->'comprehensive_submission';
  if session_row.mode = 'comprehensive' then
    if p_event_type = 'skipped' then
      raise exception 'adaptive_comprehensive_batch_required';
    end if;
    if p_event_type = 'answer_viewed' and session_row.status = 'ACTIVE' then
      raise exception 'adaptive_comprehensive_batch_required';
    end if;
    if p_event_type = 'abandoned'
       and jsonb_typeof(comprehensive_manifest) = 'object'
       and upper(coalesce(comprehensive_manifest->>'phase', '')) in ('LOCKED', 'COMPLETED') then
      raise exception 'adaptive_comprehensive_submission_in_progress';
    end if;
  end if;

  if p_event_type = 'presented' then
    if item_row.item_status in ('SELECTED', 'PRESENTED') then
      update public.practice_session_items
      set item_status = 'PRESENTED',
          presented_at = coalesce(presented_at, p_now),
          updated_at = p_now
      where id = p_session_item_id;
    end if;
  elsif p_event_type = 'answer_viewed' then
    update public.practice_session_items
    set explanation_viewed_at = coalesce(explanation_viewed_at, p_now),
        updated_at = p_now
    where id = p_session_item_id;
  elsif p_event_type = 'skipped' then
    if item_row.item_status <> 'ANSWERED' then
      update public.practice_session_items
      set item_status = 'SKIPPED',
          presented_at = coalesce(presented_at, p_now),
          skipped_at = coalesce(skipped_at, p_now),
          updated_at = p_now
      where id = p_session_item_id;
    end if;
  elsif p_event_type = 'abandoned' then
    update public.practice_session_items
    set exit_observed_at = coalesce(exit_observed_at, p_now),
        updated_at = p_now
    where id = p_session_item_id;
    if session_row.status = 'ACTIVE' then
      update public.practice_sessions
      set status = 'ABANDONED',
          abandoned_at = p_now,
          last_activity_at = p_now,
          updated_at = p_now
      where id = p_session_id;
    end if;
  else
    raise exception 'adaptive_event_invalid';
  end if;

  if p_event_type <> 'abandoned' then
    update public.practice_sessions
    set last_activity_at = p_now,
        updated_at = p_now
    where id = p_session_id;
  end if;

  return jsonb_build_object(
    'session_id', p_session_id,
    'session_item_id', p_session_item_id,
    'event_type', p_event_type,
    'recorded', true
  );
end;
$$;

create or replace function public.complete_practice_session(
  p_user_id uuid,
  p_session_id uuid,
  p_reason text default 'completed',
  p_now timestamptz default now()
)
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  session_snapshot public.practice_sessions%rowtype;
  session_row public.practice_sessions%rowtype;
  final_status text;
  comprehensive_manifest jsonb;
begin
  if p_user_id is null or p_session_id is null or p_now is null
     or p_reason is null
     or char_length(btrim(p_reason)) not between 1 and 120 then
    raise exception 'adaptive_session_completion_invalid';
  end if;

  select * into session_snapshot
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(p_user_id::text || ':adaptive_comprehensive_embargo', 0)
  );
  perform pg_advisory_xact_lock(
    hashtextextended(
      p_user_id::text || ':' || session_snapshot.stats_exam_code || ':' || session_snapshot.subject,
      0
    )
  );

  select * into session_row
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id
  for update;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;

  comprehensive_manifest := session_row.strategy_config->'comprehensive_submission';
  if session_row.mode = 'comprehensive' then
    if session_row.status = 'COMPLETED'
       and jsonb_typeof(comprehensive_manifest) = 'object'
       and upper(coalesce(comprehensive_manifest->>'phase', '')) = 'COMPLETED' then
      return jsonb_build_object(
        'session_id', p_session_id,
        'status', 'COMPLETED',
        'reason', 'completed',
        'idempotent', true
      );
    end if;
    if jsonb_typeof(comprehensive_manifest) = 'object'
       and upper(coalesce(comprehensive_manifest->>'phase', '')) = 'LOCKED' then
      if p_reason = 'completed' then
        raise exception 'adaptive_comprehensive_finalize_required';
      end if;
      raise exception 'adaptive_comprehensive_submission_in_progress';
    end if;
    if p_reason = 'completed' then
      raise exception 'adaptive_comprehensive_finalize_required';
    end if;
  end if;

  -- Completion is terminal. A network retry returns the original result and
  -- never rewrites COMPLETED as ABANDONED (or vice versa).
  if session_row.status <> 'ACTIVE' then
    return jsonb_build_object(
      'session_id', p_session_id,
      'status', session_row.status,
      'reason', case
        when session_row.status = 'COMPLETED' then 'completed'
        else coalesce(session_row.fallback_reason, 'abandoned')
      end,
      'idempotent', true
    );
  end if;

  final_status := case when p_reason = 'completed' then 'COMPLETED' else 'ABANDONED' end;
  update public.practice_sessions
  set status = final_status,
      completed_at = case when final_status = 'COMPLETED' then coalesce(completed_at, p_now) else null end,
      abandoned_at = case when final_status = 'ABANDONED' then coalesce(abandoned_at, p_now) else null end,
      last_activity_at = p_now,
      fallback_reason = case when final_status = 'ABANDONED' then nullif(btrim(p_reason), '') else fallback_reason end,
      updated_at = p_now
  where id = p_session_id;

  return jsonb_build_object(
    'session_id', p_session_id,
    'status', final_status,
    'reason', p_reason,
    'idempotent', false
  );
end;
$$;

create or replace function public.get_pending_adaptive_update_items(
  p_user_id uuid,
  p_stats_exam_code text,
  p_subject text,
  p_session_id uuid default null,
  p_limit integer default 200
)
returns table (
  practice_session_item_id uuid,
  session_id uuid,
  question_id uuid,
  item_position integer,
  answer_id uuid,
  answered_at timestamptz,
  answer_stats_exam_code text,
  is_correct boolean,
  is_first_attempt boolean,
  used_time integer,
  answer_created_at timestamptz,
  question_exam_code text,
  question_subject text,
  module text,
  submodule text,
  question_type text,
  difficulty integer,
  estimated_time_sec integer,
  source_type text
)
language plpgsql
security definer
stable
set search_path = public, pg_temp
as $$
begin
  if p_user_id is null
     or p_stats_exam_code is null
     or p_subject is null
     or not (
       (p_stats_exam_code = 'Z001' and p_subject in ('中华文化', '英语运用', '逻辑推理'))
       or
       (p_stats_exam_code = 'Z002' and p_subject in ('中华文化', '英语运用', '数学基础'))
     ) then
    raise exception 'adaptive_pending_update_scope_invalid';
  end if;
  if p_limit is null or p_limit not between 1 and 1000 then
    raise exception 'adaptive_pending_update_limit_invalid';
  end if;
  if p_session_id is not null and not exists (
    select 1
    from public.practice_sessions scoped_session
    where scoped_session.id = p_session_id
      and scoped_session.user_id = p_user_id
      and scoped_session.stats_exam_code = p_stats_exam_code
      and scoped_session.subject = p_subject
  ) then
    raise exception 'adaptive_session_not_found';
  end if;

  return query
  select
    item.id,
    item.session_id,
    item.question_id,
    item.position,
    item.answer_id,
    item.answered_at,
    answer.stats_exam_code,
    answer.is_correct,
    answer.is_first_attempt,
    answer.used_time,
    answer.created_at,
    question.exam_code,
    question.subject,
    question.module,
    question.submodule,
    question.question_type,
    question.difficulty,
    question.estimated_time_sec,
    question.source_type
  from public.practice_sessions session
  join public.practice_session_items item on item.session_id = session.id
  join public.user_answers answer on answer.id = item.answer_id
  join public.practice_session_item_question_snapshots snapshot
    on snapshot.practice_session_item_id = item.id
   and snapshot.question_id = item.question_id
  cross join lateral jsonb_populate_record(
    null::public.questions,
    snapshot.question_snapshot
  ) question
  left join public.adaptive_model_updates model_update
    on model_update.answer_id = item.answer_id
  where session.user_id = p_user_id
    and session.stats_exam_code = p_stats_exam_code
    and session.subject = p_subject
    and (p_session_id is null or session.id = p_session_id)
    and item.answer_id is not null
    and model_update.answer_id is null
  order by answer.created_at asc, session.created_at asc, item.position asc, item.id asc
  limit p_limit;
end;
$$;

-- The answers array is part of the immutable capability. Drop the earlier
-- four-argument overload so PostgREST never resolves an incomplete manifest.
drop function if exists public.begin_adaptive_comprehensive_submission(
  uuid, uuid, text, text, timestamptz
);
drop function if exists public.begin_adaptive_comprehensive_submission(
  uuid, uuid, text, text, jsonb, timestamptz
);

create function public.begin_adaptive_comprehensive_submission(
  p_user_id uuid,
  p_session_id uuid,
  p_client_submission_id text,
  p_manifest_hash text,
  p_answers jsonb,
  p_now timestamptz default now()
)
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  session_snapshot public.practice_sessions%rowtype;
  session_row public.practice_sessions%rowtype;
  item_row public.practice_session_items%rowtype;
  existing_manifest jsonb;
  entry jsonb;
  normalized_answers jsonb := '[]'::jsonb;
  canonical_answers jsonb;
  normalized_client_submission_id text := btrim(coalesce(p_client_submission_id, ''));
  entry_client_submission_id text;
  entry_selected_answer text;
  entry_item_id uuid;
  entry_position integer;
  entry_used_time integer;
  seen_item_ids uuid[] := '{}'::uuid[];
  seen_positions integer[] := '{}'::integer[];
  seen_submission_ids text[] := '{}'::text[];
  item_count integer;
  snapshot_count integer;
  existing_phase text;
begin
  if p_user_id is null
     or p_session_id is null
     or p_now is null
     or char_length(normalized_client_submission_id) not between 1 and 120
     or p_manifest_hash is null
     or p_manifest_hash !~ '^[0-9a-f]{64}$'
     or p_answers is null
     or jsonb_typeof(p_answers) is distinct from 'array' then
    raise exception 'adaptive_comprehensive_submission_invalid';
  end if;

  select * into session_snapshot
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(p_user_id::text || ':adaptive_comprehensive_embargo', 0)
  );
  perform pg_advisory_xact_lock(
    hashtextextended(
      p_user_id::text || ':' || session_snapshot.stats_exam_code || ':' || session_snapshot.subject,
      0
    )
  );

  select * into session_row
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id
  for update;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;
  if session_row.stats_exam_code <> session_snapshot.stats_exam_code
     or session_row.subject <> session_snapshot.subject then
    raise exception 'adaptive_session_scope_changed';
  end if;
  if session_row.mode <> 'comprehensive' then
    raise exception 'adaptive_practice_mode_mismatch';
  end if;
  if jsonb_array_length(p_answers) <> session_row.requested_question_count then
    raise exception 'adaptive_comprehensive_answers_incomplete';
  end if;

  for entry in select value from jsonb_array_elements(p_answers) answer_entry(value)
  loop
    if jsonb_typeof(entry) is distinct from 'object'
       or jsonb_typeof(entry->'position') is distinct from 'number'
       or jsonb_typeof(entry->'practice_session_item_id') is distinct from 'string'
       or jsonb_typeof(entry->'used_time') is distinct from 'number'
       or jsonb_typeof(entry->'client_submission_id') is distinct from 'string'
       or not (entry ? 'selected_answer')
       or jsonb_typeof(entry->'selected_answer') not in ('null', 'string')
       or (entry->>'position') !~ '^[0-9]+$'
       or (entry->>'used_time') !~ '^[0-9]+$' then
      raise exception 'adaptive_comprehensive_answer_invalid_shape';
    end if;

    begin
      entry_position := (entry->>'position')::integer;
      entry_item_id := (entry->>'practice_session_item_id')::uuid;
      entry_used_time := (entry->>'used_time')::integer;
    exception when others then
      raise exception 'adaptive_comprehensive_answer_invalid_value';
    end;
    entry_client_submission_id := btrim(entry->>'client_submission_id');
    entry_selected_answer := case
      when jsonb_typeof(entry->'selected_answer') = 'null' then null
      else entry->>'selected_answer'
    end;

    if entry_position not between 1 and session_row.requested_question_count
       or entry_position = any(seen_positions)
       or entry_item_id = any(seen_item_ids)
       or entry_used_time not between 0 and 86400
       or char_length(entry_client_submission_id) not between 1 and 120
       or entry_client_submission_id = any(seen_submission_ids)
       or (entry_selected_answer is not null and entry_selected_answer not in ('A', 'B', 'C', 'D')) then
      raise exception 'adaptive_comprehensive_answer_invalid_value';
    end if;

    select * into item_row
    from public.practice_session_items
    where id = entry_item_id
      and session_id = p_session_id;
    if not found or item_row.position <> entry_position then
      raise exception 'adaptive_comprehensive_answer_item_mismatch';
    end if;

    seen_positions := array_append(seen_positions, entry_position);
    seen_item_ids := array_append(seen_item_ids, entry_item_id);
    seen_submission_ids := array_append(seen_submission_ids, entry_client_submission_id);
    normalized_answers := normalized_answers || jsonb_build_array(
      jsonb_build_object(
        'position', entry_position,
        'practice_session_item_id', entry_item_id,
        'selected_answer', entry_selected_answer,
        'used_time', entry_used_time,
        'client_submission_id', entry_client_submission_id
      )
    );
  end loop;

  select coalesce(
    jsonb_agg(value order by (value->>'position')::integer),
    '[]'::jsonb
  ) into canonical_answers
  from jsonb_array_elements(normalized_answers) normalized(value);
  if exists (
    select 1
    from generate_series(1, session_row.requested_question_count) expected(position)
    where not (expected.position = any(seen_positions))
  ) then
    raise exception 'adaptive_comprehensive_answers_incomplete';
  end if;

  select count(*)::integer into item_count
  from public.practice_session_items
  where session_id = p_session_id;
  select count(*)::integer into snapshot_count
  from public.practice_session_items item
  join public.practice_session_item_question_snapshots snapshot
    on snapshot.practice_session_item_id = item.id
   and snapshot.question_id = item.question_id
  where item.session_id = p_session_id;
  if item_count <> session_row.requested_question_count
     or snapshot_count <> item_count then
    raise exception 'adaptive_comprehensive_round_incomplete';
  end if;

  existing_manifest := session_row.strategy_config->'comprehensive_submission';
  if existing_manifest is not null then
    if jsonb_typeof(existing_manifest) is distinct from 'object'
       or existing_manifest->>'client_submission_id' <> normalized_client_submission_id
       or existing_manifest->>'manifest_hash' <> p_manifest_hash
       or existing_manifest->'answers' is distinct from canonical_answers then
      raise exception 'adaptive_comprehensive_submission_conflict';
    end if;
    existing_phase := upper(coalesce(existing_manifest->>'phase', ''));
    if existing_phase = 'LOCKED' and session_row.status = 'ACTIVE' then
      return jsonb_build_object(
        'session_id', p_session_id,
        'client_submission_id', normalized_client_submission_id,
        'manifest_hash', p_manifest_hash,
        'answers', canonical_answers,
        'phase', 'LOCKED',
        'idempotent', true,
        'status', 'ACTIVE'
      );
    end if;
    if existing_phase = 'COMPLETED' and session_row.status = 'COMPLETED'
       and jsonb_typeof(existing_manifest->'completion_state') = 'object' then
      return jsonb_build_object(
        'session_id', p_session_id,
        'client_submission_id', normalized_client_submission_id,
        'manifest_hash', p_manifest_hash,
        'answers', canonical_answers,
        'phase', 'COMPLETED',
        'idempotent', true,
        'status', 'COMPLETED',
        'completion_state', existing_manifest->'completion_state'
      );
    end if;
    raise exception 'adaptive_comprehensive_submission_state_invalid';
  end if;
  if session_row.status <> 'ACTIVE' then
    raise exception 'adaptive_session_not_active';
  end if;
  if exists (
    select 1
    from public.practice_session_items item
    where item.session_id = p_session_id
      and (
        item.item_status in ('ANSWERED', 'SKIPPED')
        or item.answer_id is not null
      )
  ) then
    raise exception 'adaptive_comprehensive_submission_state_invalid';
  end if;

  existing_manifest := jsonb_build_object(
    'client_submission_id', normalized_client_submission_id,
    'manifest_hash', p_manifest_hash,
    'answers', canonical_answers,
    'phase', 'LOCKED',
    'locked_at', p_now
  );
  update public.practice_sessions
  set strategy_config = jsonb_set(
        strategy_config,
        '{comprehensive_submission}',
        existing_manifest,
        true
      ),
      last_activity_at = p_now,
      updated_at = p_now
  where id = p_session_id;

  return jsonb_build_object(
    'session_id', p_session_id,
    'client_submission_id', normalized_client_submission_id,
    'manifest_hash', p_manifest_hash,
    'answers', canonical_answers,
    'phase', 'LOCKED',
    'idempotent', false,
    'status', 'ACTIVE'
  );
end;
$$;

create or replace function public.record_adaptive_comprehensive_skip(
  p_user_id uuid,
  p_session_id uuid,
  p_session_item_id uuid,
  p_client_submission_id text,
  p_manifest_hash text,
  p_now timestamptz default now()
)
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  session_snapshot public.practice_sessions%rowtype;
  session_row public.practice_sessions%rowtype;
  item_row public.practice_session_items%rowtype;
  manifest jsonb;
  answer_entry jsonb;
  manifest_phase text;
  normalized_client_submission_id text := btrim(coalesce(p_client_submission_id, ''));
begin
  if p_user_id is null or p_session_id is null or p_session_item_id is null
     or p_now is null
     or char_length(normalized_client_submission_id) not between 1 and 120
     or p_manifest_hash is null
     or p_manifest_hash !~ '^[0-9a-f]{64}$' then
    raise exception 'adaptive_comprehensive_skip_invalid';
  end if;

  select * into session_snapshot
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;
  perform pg_advisory_xact_lock(
    hashtextextended(p_user_id::text || ':adaptive_comprehensive_embargo', 0)
  );
  perform pg_advisory_xact_lock(
    hashtextextended(
      p_user_id::text || ':' || session_snapshot.stats_exam_code || ':' || session_snapshot.subject,
      0
    )
  );

  select * into session_row
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id
  for update;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;
  if session_row.mode <> 'comprehensive' then
    raise exception 'adaptive_practice_mode_mismatch';
  end if;
  select * into item_row
  from public.practice_session_items
  where id = p_session_item_id and session_id = p_session_id
  for update;
  if not found then
    raise exception 'adaptive_session_item_not_found';
  end if;

  manifest := session_row.strategy_config->'comprehensive_submission';
  if jsonb_typeof(manifest) is distinct from 'object'
     or manifest->>'client_submission_id' <> normalized_client_submission_id
     or manifest->>'manifest_hash' <> p_manifest_hash
     or jsonb_typeof(manifest->'answers') is distinct from 'array' then
    raise exception 'adaptive_comprehensive_submission_conflict';
  end if;
  select value into answer_entry
  from jsonb_array_elements(manifest->'answers') answer_value(value)
  where value->>'practice_session_item_id' = p_session_item_id::text
    and (value->>'position')::integer = item_row.position
  limit 1;
  if not found or answer_entry->'selected_answer' is distinct from 'null'::jsonb then
    raise exception 'adaptive_comprehensive_skip_manifest_mismatch';
  end if;

  manifest_phase := upper(coalesce(manifest->>'phase', ''));
  if manifest_phase = 'COMPLETED' then
    if session_row.status = 'COMPLETED'
       and item_row.item_status = 'SKIPPED'
       and item_row.answer_id is null then
      return jsonb_build_object(
        'session_id', p_session_id,
        'session_item_id', p_session_item_id,
        'status', 'SKIPPED',
        'phase', 'COMPLETED',
        'idempotent', true
      );
    end if;
    raise exception 'adaptive_comprehensive_submission_state_invalid';
  end if;
  if manifest_phase <> 'LOCKED' or session_row.status <> 'ACTIVE' then
    raise exception 'adaptive_comprehensive_submission_state_invalid';
  end if;
  if item_row.item_status = 'ANSWERED' or item_row.answer_id is not null then
    raise exception 'adaptive_comprehensive_skip_answer_conflict';
  end if;
  if item_row.item_status = 'SKIPPED' then
    return jsonb_build_object(
      'session_id', p_session_id,
      'session_item_id', p_session_item_id,
      'status', 'SKIPPED',
      'phase', 'LOCKED',
      'idempotent', true
    );
  end if;

  update public.practice_session_items
  set item_status = 'SKIPPED',
      presented_at = coalesce(presented_at, p_now),
      skipped_at = coalesce(skipped_at, p_now),
      updated_at = p_now
  where id = p_session_item_id;
  update public.practice_sessions
  set last_activity_at = p_now,
      updated_at = p_now
  where id = p_session_id;

  return jsonb_build_object(
    'session_id', p_session_id,
    'session_item_id', p_session_item_id,
    'status', 'SKIPPED',
    'phase', 'LOCKED',
    'idempotent', false
  );
end;
$$;

create or replace function public.finalize_adaptive_comprehensive_submission(
  p_user_id uuid,
  p_session_id uuid,
  p_client_submission_id text,
  p_manifest_hash text,
  p_now timestamptz default now()
)
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  session_snapshot public.practice_sessions%rowtype;
  session_row public.practice_sessions%rowtype;
  subject_row public.user_subject_state%rowtype;
  manifest jsonb;
  completed_manifest jsonb;
  completion_state jsonb;
  manifest_phase text;
  normalized_client_submission_id text := btrim(coalesce(p_client_submission_id, ''));
  item_count integer;
  snapshot_count integer;
begin
  if p_user_id is null or p_session_id is null or p_now is null
     or char_length(normalized_client_submission_id) not between 1 and 120
     or p_manifest_hash is null
     or p_manifest_hash !~ '^[0-9a-f]{64}$' then
    raise exception 'adaptive_comprehensive_finalize_invalid';
  end if;

  select * into session_snapshot
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;
  perform pg_advisory_xact_lock(
    hashtextextended(p_user_id::text || ':adaptive_comprehensive_embargo', 0)
  );
  perform pg_advisory_xact_lock(
    hashtextextended(
      p_user_id::text || ':' || session_snapshot.stats_exam_code || ':' || session_snapshot.subject,
      0
    )
  );

  select * into session_row
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id
  for update;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;
  if session_row.mode <> 'comprehensive' then
    raise exception 'adaptive_practice_mode_mismatch';
  end if;
  manifest := session_row.strategy_config->'comprehensive_submission';
  if jsonb_typeof(manifest) is distinct from 'object'
     or manifest->>'client_submission_id' <> normalized_client_submission_id
     or manifest->>'manifest_hash' <> p_manifest_hash
     or jsonb_typeof(manifest->'answers') is distinct from 'array' then
    raise exception 'adaptive_comprehensive_submission_conflict';
  end if;

  manifest_phase := upper(coalesce(manifest->>'phase', ''));
  if manifest_phase = 'COMPLETED' then
    if session_row.status = 'COMPLETED'
       and jsonb_typeof(manifest->'completion_state') = 'object' then
      return jsonb_build_object(
        'session_id', p_session_id,
        'client_submission_id', normalized_client_submission_id,
        'manifest_hash', p_manifest_hash,
        'phase', 'COMPLETED',
        'status', 'COMPLETED',
        'idempotent', true,
        'completion_state', manifest->'completion_state'
      );
    end if;
    raise exception 'adaptive_comprehensive_submission_state_invalid';
  end if;
  if manifest_phase <> 'LOCKED' or session_row.status <> 'ACTIVE' then
    raise exception 'adaptive_comprehensive_submission_state_invalid';
  end if;

  select count(*)::integer into item_count
  from public.practice_session_items
  where session_id = p_session_id;
  select count(*)::integer into snapshot_count
  from public.practice_session_items item
  join public.practice_session_item_question_snapshots snapshot
    on snapshot.practice_session_item_id = item.id
   and snapshot.question_id = item.question_id
  where item.session_id = p_session_id;
  if item_count <> session_row.requested_question_count
     or jsonb_array_length(manifest->'answers') <> item_count
     or snapshot_count <> item_count then
    raise exception 'adaptive_comprehensive_round_incomplete';
  end if;

  if exists (
    select 1
    from jsonb_array_elements(manifest->'answers') answer_entry(value)
    left join public.practice_session_items item
      on item.id = (answer_entry.value->>'practice_session_item_id')::uuid
     and item.session_id = p_session_id
     and item.position = (answer_entry.value->>'position')::integer
    left join public.user_answers answer on answer.id = item.answer_id
    where item.id is null
       or case
         when answer_entry.value->'selected_answer' = 'null'::jsonb then
           item.item_status is distinct from 'SKIPPED'
           or item.answer_id is not null
         else
           item.item_status is distinct from 'ANSWERED'
           or item.answer_id is null
           or answer.user_id is distinct from p_user_id
           or answer.question_id is distinct from item.question_id
           or answer.stats_exam_code is distinct from session_row.stats_exam_code
           or answer.selected_answer is distinct from (answer_entry.value->>'selected_answer')
           or answer.used_time is distinct from (answer_entry.value->>'used_time')::integer
           or answer.client_submission_id is distinct from (answer_entry.value->>'client_submission_id')
       end
  ) then
    raise exception 'adaptive_comprehensive_submission_incomplete';
  end if;

  if exists (
    select 1
    from public.practice_session_items item
    where item.session_id = p_session_id
      and item.item_status = 'ANSWERED'
      and (
        item.answer_id is null
        or not exists (
          select 1
          from public.adaptive_model_updates applied
          where applied.answer_id = item.answer_id
            and applied.practice_session_item_id = item.id
        )
      )
  ) then
    raise exception 'adaptive_update_pending';
  end if;

  select * into subject_row
  from public.user_subject_state
  where user_id = p_user_id
    and stats_exam_code = session_row.stats_exam_code
    and subject = session_row.subject
  for update;
  if not found then
    raise exception 'adaptive_subject_state_not_found';
  end if;
  completion_state := jsonb_build_object(
    'theta', subject_row.theta,
    'uncertainty', subject_row.uncertainty,
    'effective_evidence', subject_row.effective_evidence,
    'reliable_first_attempt_count', subject_row.reliable_first_attempt_count,
    'diagnostic_status', subject_row.diagnostic_status,
    'pending_conflict_count', subject_row.pending_conflict_count,
    'state_version', subject_row.state_version,
    'model_version', subject_row.model_version,
    'last_answered_at', subject_row.last_answered_at
  );
  completed_manifest := manifest || jsonb_build_object(
    'phase', 'COMPLETED',
    'completed_at', p_now,
    'completion_state', completion_state
  );

  update public.practice_sessions
  set strategy_config = jsonb_set(
        strategy_config,
        '{comprehensive_submission}',
        completed_manifest,
        true
      ),
      status = 'COMPLETED',
      completed_at = coalesce(completed_at, p_now),
      abandoned_at = null,
      last_activity_at = p_now,
      updated_at = p_now
  where id = p_session_id;

  return jsonb_build_object(
    'session_id', p_session_id,
    'client_submission_id', normalized_client_submission_id,
    'manifest_hash', p_manifest_hash,
    'phase', 'COMPLETED',
    'status', 'COMPLETED',
    'idempotent', false,
    'completion_state', completion_state
  );
end;
$$;

revoke all on function public.record_answer_submission(
  uuid, uuid, text, text, boolean, integer, text, text, text, text, boolean, timestamptz, uuid,
  text, uuid, text, text
) from public, anon, authenticated;
grant execute on function public.record_answer_submission(
  uuid, uuid, text, text, boolean, integer, text, text, text, text, boolean, timestamptz, uuid,
  text, uuid, text, text
) to service_role;

revoke all on function public.get_adaptive_question_snapshot(uuid, uuid, uuid)
  from public, anon, authenticated;
grant execute on function public.get_adaptive_question_snapshot(uuid, uuid, uuid)
  to service_role;

revoke all on function public.record_practice_session_item_event(uuid, uuid, uuid, text, timestamptz)
  from public, anon, authenticated;
grant execute on function public.record_practice_session_item_event(uuid, uuid, uuid, text, timestamptz)
  to service_role;

revoke all on function public.complete_practice_session(uuid, uuid, text, timestamptz)
  from public, anon, authenticated;
grant execute on function public.complete_practice_session(uuid, uuid, text, timestamptz)
  to service_role;

revoke all on function public.get_pending_adaptive_update_items(uuid, text, text, uuid, integer)
  from public, anon, authenticated;
grant execute on function public.get_pending_adaptive_update_items(uuid, text, text, uuid, integer)
  to service_role;

revoke all on function public.claim_adaptive_comprehensive_practice_items(
  uuid, uuid, bigint, jsonb, timestamptz
) from public, anon, authenticated;
grant execute on function public.claim_adaptive_comprehensive_practice_items(
  uuid, uuid, bigint, jsonb, timestamptz
) to service_role;

revoke all on function public.assert_single_answer_feedback_allowed(
  uuid, uuid, uuid
) from public, anon, authenticated;
grant execute on function public.assert_single_answer_feedback_allowed(
  uuid, uuid, uuid
) to service_role;

revoke all on function public.begin_adaptive_comprehensive_submission(
  uuid, uuid, text, text, jsonb, timestamptz
) from public, anon, authenticated;
grant execute on function public.begin_adaptive_comprehensive_submission(
  uuid, uuid, text, text, jsonb, timestamptz
) to service_role;

revoke all on function public.record_adaptive_comprehensive_skip(
  uuid, uuid, uuid, text, text, timestamptz
) from public, anon, authenticated;
grant execute on function public.record_adaptive_comprehensive_skip(
  uuid, uuid, uuid, text, text, timestamptz
) to service_role;

revoke all on function public.finalize_adaptive_comprehensive_submission(
  uuid, uuid, text, text, timestamptz
) from public, anon, authenticated;
grant execute on function public.finalize_adaptive_comprehensive_submission(
  uuid, uuid, text, text, timestamptz
) to service_role;

comment on function public.claim_adaptive_comprehensive_practice_items(
  uuid, uuid, bigint, jsonb, timestamptz
) is 'Atomically claims and snapshots one complete immutable comprehensive-practice round.';
comment on function public.assert_single_answer_feedback_allowed(
  uuid, uuid, uuid
) is 'Rejects single-answer feedback for any question held by the user in an active comprehensive round.';
comment on function public.begin_adaptive_comprehensive_submission(
  uuid, uuid, text, text, jsonb, timestamptz
) is 'Validates, canonicalizes and locks one complete immutable comprehensive submission manifest.';
comment on function public.record_adaptive_comprehensive_skip(
  uuid, uuid, uuid, text, text, timestamptz
) is 'Idempotently records a skipped item only when authorized by the locked comprehensive manifest.';
comment on function public.finalize_adaptive_comprehensive_submission(
  uuid, uuid, text, text, timestamptz
) is 'Atomically verifies a fully settled comprehensive manifest and stores its immutable completion state.';

comment on function public.record_answer_submission(
  uuid, uuid, text, text, boolean, integer, text, text, text, text, boolean, timestamptz, uuid,
  text, uuid, text, text
) is 'Atomically records one answer; active comprehensive items require an exact locked-manifest capability.';
comment on function public.get_adaptive_question_snapshot(uuid, uuid, uuid) is
  'Returns one owner-validated private claim-time question snapshot to the backend service role.';
comment on function public.get_pending_adaptive_update_items(uuid, text, text, uuid, integer) is
  'Returns a bounded chronological batch of durable adaptive answers that have no model-update audit row.';

notify pgrst, 'reload schema';

commit;
