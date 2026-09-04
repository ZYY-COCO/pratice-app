-- Bounded whole-sheet persistence for adaptive comprehensive practice.
--
-- Apply after:
--   1. database/adaptive_question_delivery_v1.sql
--   2. database/adaptive_comprehensive_practice_v1.sql
--
-- This migration is intentionally separate from the comprehensive-practice
-- foundation so an already deployed environment can add the optimization
-- without replaying either foundation migration.

begin;

create or replace function public.persist_adaptive_comprehensive_answers_batch(
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
  item_row public.practice_session_items%rowtype;
  question_row public.questions%rowtype;
  answer_row public.user_answers%rowtype;
  subject_row public.user_subject_state%rowtype;
  manifest jsonb;
  entry jsonb;
  entry_item_id uuid;
  entry_position integer;
  entry_used_time integer;
  entry_selected_answer text;
  entry_client_submission_id text;
  item_result jsonb;
  persisted_items jsonb := '[]'::jsonb;
  normalized_client_submission_id text := btrim(coalesce(p_client_submission_id, ''));
  item_count integer;
  snapshot_count integer;
  processed_count integer := 0;
  all_idempotent boolean := true;
  topic_states jsonb := '[]'::jsonb;
  pending_conflict jsonb := null;
  external_pending_count integer := 0;
begin
  if p_user_id is null or p_session_id is null or p_now is null
     or char_length(normalized_client_submission_id) not between 1 and 120
     or p_manifest_hash is null
     or p_manifest_hash !~ '^[0-9a-f]{64}$' then
    raise exception 'adaptive_comprehensive_batch_persist_invalid';
  end if;

  select * into session_snapshot
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;

  -- Keep the same global lock order as begin/finalize and every answer path.
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

  manifest := session_row.strategy_config->'comprehensive_submission';
  if jsonb_typeof(manifest) is distinct from 'object'
     or manifest->>'client_submission_id' <> normalized_client_submission_id
     or manifest->>'manifest_hash' <> p_manifest_hash
     or upper(coalesce(manifest->>'phase', '')) <> 'LOCKED'
     or jsonb_typeof(manifest->'answers') is distinct from 'array'
     or session_row.status <> 'ACTIVE' then
    raise exception 'adaptive_comprehensive_submission_conflict';
  end if;
  if jsonb_array_length(manifest->'answers') <> session_row.requested_question_count
     or session_row.requested_question_count not between 1 and 30 then
    raise exception 'adaptive_comprehensive_round_incomplete';
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

  for entry in
    select value
    from jsonb_array_elements(manifest->'answers') manifest_answer(value)
    order by (value->>'position')::integer
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
      entry_item_id := (entry->>'practice_session_item_id')::uuid;
      entry_position := (entry->>'position')::integer;
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
       or entry_used_time not between 0 and 86400
       or char_length(entry_client_submission_id) not between 1 and 120
       or (
         entry_selected_answer is not null
         and entry_selected_answer not in ('A', 'B', 'C', 'D')
       ) then
      raise exception 'adaptive_comprehensive_answer_invalid_value';
    end if;

    select * into item_row
    from public.practice_session_items
    where id = entry_item_id
      and session_id = p_session_id
      and position = entry_position
    for update;
    if not found then
      raise exception 'adaptive_comprehensive_answer_item_mismatch';
    end if;

    select populated.* into question_row
    from public.practice_session_item_question_snapshots snapshot
    cross join lateral jsonb_populate_record(
      null::public.questions,
      snapshot.question_snapshot
    ) populated
    where snapshot.practice_session_item_id = item_row.id
      and snapshot.question_id = item_row.question_id;
    if not found
       or question_row.id is distinct from item_row.question_id
       or question_row.subject is distinct from session_row.subject
       or question_row.answer not in ('A', 'B', 'C', 'D')
       or question_row.exam_code not in ('COMMON', session_row.stats_exam_code)
       or (
         question_row.exam_code = 'COMMON'
         and question_row.subject not in ('中华文化', '英语运用')
       ) then
      raise exception 'adaptive_comprehensive_snapshot_scope_mismatch';
    end if;

    if entry_selected_answer is null then
      item_result := public.record_adaptive_comprehensive_skip(
        p_user_id,
        p_session_id,
        item_row.id,
        normalized_client_submission_id,
        p_manifest_hash,
        p_now
      );
      persisted_items := persisted_items || jsonb_build_array(
        jsonb_build_object(
          'position', entry_position,
          'practice_session_item_id', item_row.id,
          'question_id', item_row.question_id,
          'selected_answer', null,
          'status', 'SKIPPED',
          'idempotent', coalesce((item_result->>'idempotent')::boolean, false)
        )
      );
    else
      item_result := public.record_answer_submission(
        p_user_id => p_user_id,
        p_question_id => item_row.question_id,
        p_client_submission_id => entry_client_submission_id,
        p_selected_answer => entry_selected_answer,
        p_is_correct => (entry_selected_answer = question_row.answer),
        p_used_time => entry_used_time,
        p_exam_code => session_row.stats_exam_code,
        p_subject => session_row.subject,
        p_module => question_row.module,
        p_submodule => question_row.submodule,
        p_is_ai_generated => (coalesce(question_row.source_type, '') = 'ai_deepseek'),
        p_now => p_now,
        p_practice_session_item_id => item_row.id,
        p_submission_kind => 'comprehensive_batch',
        p_comprehensive_session_id => p_session_id,
        p_comprehensive_client_submission_id => normalized_client_submission_id,
        p_comprehensive_manifest_hash => p_manifest_hash
      );
      select * into answer_row
      from public.user_answers
      where id = (item_result->>'submission_id')::uuid
        and user_id = p_user_id
        and question_id = item_row.question_id;
      if not found then
        raise exception 'adaptive_answer_not_found';
      end if;
      persisted_items := persisted_items || jsonb_build_array(
        jsonb_build_object(
          'position', entry_position,
          'practice_session_item_id', item_row.id,
          'question_id', item_row.question_id,
          'selected_answer', entry_selected_answer,
          'status', 'ANSWERED',
          'answer_id', item_result->'submission_id',
          'stats_exam_code', item_result->'stats_exam_code',
          'is_correct', item_result->'is_correct',
          'is_first_attempt', item_result->'is_first_attempt',
          'used_time', answer_row.used_time,
          'answer_created_at', answer_row.created_at,
          'adaptive_updated', exists (
            select 1
            from public.adaptive_model_updates applied
            where applied.answer_id = answer_row.id
              and applied.practice_session_item_id = item_row.id
          ),
          'idempotent', coalesce((item_result->>'idempotent')::boolean, false)
        )
      );
    end if;

    all_idempotent := all_idempotent
      and coalesce((item_result->>'idempotent')::boolean, false);
    processed_count := processed_count + 1;
  end loop;

  if processed_count <> session_row.requested_question_count then
    raise exception 'adaptive_comprehensive_answers_incomplete';
  end if;

  select * into subject_row
  from public.user_subject_state
  where user_id = p_user_id
    and stats_exam_code = session_row.stats_exam_code
    and subject = session_row.subject;
  if not found then
    raise exception 'adaptive_subject_state_not_found';
  end if;

  select coalesce(
    jsonb_agg(to_jsonb(topic_state) order by topic_state.module, topic_state.submodule),
    '[]'::jsonb
  ) into topic_states
  from public.user_topic_state topic_state
  where topic_state.user_id = p_user_id
    and topic_state.stats_exam_code = session_row.stats_exam_code
    and topic_state.subject = session_row.subject;

  select to_jsonb(conflict_row) into pending_conflict
  from public.adaptive_conflicts conflict_row
  where conflict_row.user_id = p_user_id
    and conflict_row.stats_exam_code = session_row.stats_exam_code
    and conflict_row.subject = session_row.subject
    and conflict_row.status = 'PENDING'
  order by conflict_row.opened_at asc, conflict_row.id asc
  limit 1;

  select count(*)::integer into external_pending_count
  from public.practice_sessions pending_session
  join public.practice_session_items pending_item
    on pending_item.session_id = pending_session.id
  where pending_session.user_id = p_user_id
    and pending_session.stats_exam_code = session_row.stats_exam_code
    and pending_session.subject = session_row.subject
    and pending_session.id <> p_session_id
    and pending_item.answer_id is not null
    and not exists (
      select 1
      from public.adaptive_model_updates applied
      where applied.answer_id = pending_item.answer_id
    );

  return jsonb_build_object(
    'session_id', p_session_id,
    'client_submission_id', normalized_client_submission_id,
    'manifest_hash', p_manifest_hash,
    'phase', 'LOCKED',
    'status', 'ACTIVE',
    'item_count', processed_count,
    'items', persisted_items,
    'subject_state', to_jsonb(subject_row),
    'topic_states', topic_states,
    'pending_conflict', pending_conflict,
    'external_pending_count', external_pending_count,
    'idempotent', all_idempotent
  );
end;
$$;

revoke all on function public.persist_adaptive_comprehensive_answers_batch(
  uuid, uuid, text, text, timestamptz
) from public, anon, authenticated;
grant execute on function public.persist_adaptive_comprehensive_answers_batch(
  uuid, uuid, text, text, timestamptz
) to service_role;

comment on function public.persist_adaptive_comprehensive_answers_batch(
  uuid, uuid, text, text, timestamptz
) is 'Atomically persists every answer and skip from one locked comprehensive manifest in position order (maximum 30 items).';

notify pgrst, 'reload schema';

commit;
