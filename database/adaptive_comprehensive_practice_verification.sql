-- Read-only verification companion for the adaptive comprehensive, bounded
-- candidate-history, whole-sheet persistence, candidate-freshness, and
-- question-read-access migrations. Run the relevant SELECT blocks in the
-- confirmed Supabase SQL Editor before and after each migration. This file
-- performs no DDL or DML.

-- A. Human identity cross-check aid. Match this Dashboard project independently
-- against the deployment target before trusting the remaining results.
select
  current_database() as database_name,
  current_user as database_user,
  current_setting('server_version') as server_version,
  now() as checked_at;

-- B. Re-read the mutable row-count baseline immediately before and after the
-- migration. All adaptive tables were empty during the 2026-09-04 preflight.
select 'user_answers' as relation_name, count(*)::bigint as row_count
from public.user_answers
union all
select 'wrong_questions', count(*)::bigint from public.wrong_questions
union all
select 'user_question_progress', count(*)::bigint from public.user_question_progress
union all
select 'user_subject_state', count(*)::bigint from public.user_subject_state
union all
select 'user_topic_state', count(*)::bigint from public.user_topic_state
union all
select 'practice_sessions', count(*)::bigint from public.practice_sessions
union all
select 'practice_session_items', count(*)::bigint from public.practice_session_items
union all
select 'practice_session_item_question_snapshots', count(*)::bigint
from public.practice_session_item_question_snapshots
union all
select 'question_calibration', count(*)::bigint from public.question_calibration
union all
select 'adaptive_model_updates', count(*)::bigint from public.adaptive_model_updates
union all
select 'adaptive_conflicts', count(*)::bigint from public.adaptive_conflicts
union all
select 'practice_sessions_active', count(*)::bigint
from public.practice_sessions
where status = 'ACTIVE'
order by relation_name;

-- C. Pre-migration compatibility gate. The four functions replaced by the
-- comprehensive migration accept either the reviewed production predecessor
-- or the reviewed embargo-aware first-layer body. Every exists/security/body/
-- search-path/owner/ACL value must be true. A false value means the additive
-- comprehensive migration is not proven compatible with the deployed revision.
with expected(signature, allowed_md5) as (
  values
    ('public.claim_next_adaptive_practice_item(uuid,uuid,uuid,integer,bigint,jsonb,timestamptz)', array['a49e0d6863b722198224766e2295f1da']::text[]),
    ('public.apply_adaptive_model_update(uuid,uuid,uuid,jsonb,timestamptz)', array['9dcb9ac1196ce9af928bf439a1f2b005']::text[]),
    ('public.get_adaptive_question_snapshot(uuid,uuid,uuid)', array['d2e2be3a78f1a5b9522c639be8729de7', '7255f4d5a37a55bd49ec09c78c66f6ad']::text[]),
    ('public.record_practice_session_item_event(uuid,uuid,uuid,text,timestamptz)', array['73bfd2b45fa01b4535aa703222d5a676', '42b4400fa3fdc080055d11849807976b']::text[]),
    ('public.complete_practice_session(uuid,uuid,text,timestamptz)', array['b1557754912e57cddcdad7c7062d9df7', 'c945ae789dd4ad8074902b857dd356b0']::text[]),
    ('public.get_pending_adaptive_update_items(uuid,text,text,uuid,integer)', array['3f09faf68c2a5ecd1c0fa6ce541c9334', 'a4f121c8006d6b4b4046c85f242834c4']::text[])
)
select
  expected.signature,
  procedure.oid is not null as exists,
  coalesce(procedure.prosecdef, false) as security_definer,
  coalesce(
    'search_path=public, pg_temp' = any(procedure.proconfig),
    false
  ) as fixed_search_path,
  md5(
    btrim(replace(procedure.prosrc, chr(13), ''), E' \t\n')
  ) as actual_md5,
  md5(
    btrim(replace(procedure.prosrc, chr(13), ''), E' \t\n')
  ) = any(expected.allowed_md5) as body_matches,
  coalesce(pg_get_userbyid(procedure.proowner) = 'postgres', false) as owner_matches,
  coalesce(
    procedure.proacl::text = '{postgres=X/postgres,service_role=X/postgres}',
    false
  ) as acl_matches
from expected
left join pg_proc as procedure
  on procedure.oid = to_regprocedure(expected.signature)
order by expected.signature;

-- D. Expected transition state. Before migration the result must be
-- old13=true/private13=false/new17=false/active_sessions=0. After migration it
-- must be old13=false/private13=true/new17=true/active_sessions=0.
select
  to_regprocedure(
    'public.record_answer_submission(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
  ) is not null as old13,
  to_regprocedure(
    'public.record_answer_submission_pre_comprehensive_v1(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
  ) is not null as private13,
  to_regprocedure(
    'public.record_answer_submission(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid,text,uuid,text,text)'
  ) is not null as new17,
  (
    select count(*)::bigint
    from public.practice_sessions
    where status = 'ACTIVE'
  ) as active_sessions;

-- E. New RPC inventory. All seven exists values must be false before the four
-- adaptive incrementals and true after they have committed.
with expected(signature) as (
  values
    ('public.claim_adaptive_comprehensive_practice_items(uuid,uuid,bigint,jsonb,timestamptz)'),
    ('public.assert_single_answer_feedback_allowed(uuid,uuid,uuid)'),
    ('public.begin_adaptive_comprehensive_submission(uuid,uuid,text,text,jsonb,timestamptz)'),
    ('public.record_adaptive_comprehensive_skip(uuid,uuid,uuid,text,text,timestamptz)'),
    ('public.finalize_adaptive_comprehensive_submission(uuid,uuid,text,text,timestamptz)'),
    ('public.get_adaptive_candidate_history_v1(uuid,text,text,uuid[],integer,boolean)'),
    ('public.persist_adaptive_comprehensive_answers_batch(uuid,uuid,text,text,timestamptz)')
)
select signature, to_regprocedure(signature) is not null as exists
from expected
order by signature;

-- F. Post-migration function-body gate. Run only after the migration commits;
-- every exists/security/body/search-path value must be true.
with expected(signature, expected_md5) as (
  values
    ('public.claim_adaptive_comprehensive_practice_items(uuid,uuid,bigint,jsonb,timestamptz)', '1b070654e9337b5e8d113d2a9f798c81'),
    ('public.assert_single_answer_feedback_allowed(uuid,uuid,uuid)', '0382bd8997279101224bd667ab9bdaef'),
    ('public.record_answer_submission(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid,text,uuid,text,text)', '72f23b7a4623aa444bbc4f06fccec579'),
    ('public.begin_adaptive_comprehensive_submission(uuid,uuid,text,text,jsonb,timestamptz)', 'db863dbf366415d83a900a9a42c3d906'),
    ('public.record_adaptive_comprehensive_skip(uuid,uuid,uuid,text,text,timestamptz)', 'a25564b1b963bc22b2374e2f183791d7'),
    ('public.finalize_adaptive_comprehensive_submission(uuid,uuid,text,text,timestamptz)', '15d5dc19d6ed37acb2c69c3e1cfb7e39'),
    ('public.get_adaptive_question_snapshot(uuid,uuid,uuid)', '7255f4d5a37a55bd49ec09c78c66f6ad'),
    ('public.record_practice_session_item_event(uuid,uuid,uuid,text,timestamptz)', '42b4400fa3fdc080055d11849807976b'),
    ('public.complete_practice_session(uuid,uuid,text,timestamptz)', 'c945ae789dd4ad8074902b857dd356b0'),
    ('public.get_pending_adaptive_update_items(uuid,text,text,uuid,integer)', 'a4f121c8006d6b4b4046c85f242834c4'),
    ('public.persist_adaptive_comprehensive_answers_batch(uuid,uuid,text,text,timestamptz)', '6e58a83fc2e468fcad46435d4a4e8456')
)
select
  expected.signature,
  procedure.oid is not null as exists,
  coalesce(procedure.prosecdef, false) as security_definer,
  coalesce(
    'search_path=public, pg_temp' = any(procedure.proconfig),
    false
  ) as fixed_search_path,
  md5(
    btrim(replace(procedure.prosrc, chr(13), ''), E' \t\n')
  ) as actual_md5,
  md5(
    btrim(replace(procedure.prosrc, chr(13), ''), E' \t\n')
  ) = expected.expected_md5 as body_matches,
  coalesce(has_function_privilege('anon', procedure.oid, 'EXECUTE'), false)
    as anon_can_execute,
  coalesce(has_function_privilege('authenticated', procedure.oid, 'EXECUTE'), false)
    as authenticated_can_execute,
  coalesce(has_function_privilege('service_role', procedure.oid, 'EXECUTE'), false)
    as service_role_can_execute,
  coalesce(pg_get_userbyid(procedure.proowner) = 'postgres', false) as owner_matches,
  coalesce(
    procedure.proacl::text = '{postgres=X/postgres,service_role=X/postgres}',
    false
  ) as acl_matches
from expected
left join pg_proc as procedure
  on procedure.oid = to_regprocedure(expected.signature)
order by expected.signature;

-- G. The renamed 13-parameter core must be private even from service_role;
-- only the public 17-parameter wrapper may call it internally.
select
  to_regprocedure(
    'public.record_answer_submission_pre_comprehensive_v1(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
  ) is not null as private_core_exists,
  coalesce(
    has_function_privilege(
      'anon',
      to_regprocedure(
        'public.record_answer_submission_pre_comprehensive_v1(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
      ),
      'EXECUTE'
    ),
    false
  ) as anon_can_execute,
  coalesce(
    has_function_privilege(
      'authenticated',
      to_regprocedure(
        'public.record_answer_submission_pre_comprehensive_v1(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
      ),
      'EXECUTE'
    ),
    false
  ) as authenticated_can_execute,
  coalesce(
    has_function_privilege(
      'service_role',
      to_regprocedure(
        'public.record_answer_submission_pre_comprehensive_v1(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
      ),
      'EXECUTE'
    ),
    false
  ) as service_role_can_execute;

-- H. Bounded candidate-history lookup. Run after
-- adaptive_candidate_history_lookup_v1.sql. Every boolean must be true except
-- security_definer/anon/authenticated, which must be false. The service role
-- must be the only listed application role with effective EXECUTE.
with expected(signature, expected_md5) as (
  values (
    'public.get_adaptive_candidate_history_v1(uuid,text,text,uuid[],integer,boolean)',
    'e6adb88c8664395872268e9d72686fa2'
  )
)
select
  expected.signature,
  procedure.oid is not null as exists,
  coalesce(procedure.provolatile = 's', false) as stable,
  coalesce(procedure.prosecdef, false) as security_definer,
  coalesce(not procedure.prosecdef, false) as security_invoker,
  coalesce(
    'search_path=public, pg_temp' = any(procedure.proconfig),
    false
  ) as fixed_search_path,
  md5(
    btrim(replace(procedure.prosrc, chr(13), ''), E' \t\n')
  ) as actual_md5,
  coalesce(
    md5(btrim(replace(procedure.prosrc, chr(13), ''), E' \t\n')) =
      expected.expected_md5,
    false
  ) as body_matches,
  coalesce(has_function_privilege('anon', procedure.oid, 'EXECUTE'), false)
    as anon_can_execute,
  coalesce(has_function_privilege('authenticated', procedure.oid, 'EXECUTE'), false)
    as authenticated_can_execute,
  coalesce(has_function_privilege('service_role', procedure.oid, 'EXECUTE'), false)
    as service_role_can_execute,
  procedure.proacl
from expected
left join pg_proc as procedure
  on procedure.oid = to_regprocedure(expected.signature);

-- I. The candidate-history index must exist, be valid/ready, and preserve the
-- exact user/question/exam key order used by the bounded progress lookup.
with candidate_index as (
  select
    index_meta.indexrelid,
    index_meta.indisvalid,
    index_meta.indisready,
    pg_get_indexdef(index_meta.indexrelid) as index_definition
  from pg_index index_meta
  where index_meta.indexrelid =
    to_regclass('public.idx_user_question_progress_user_question_exam')
)
select
  candidate_index.indexrelid is not null as exists,
  coalesce(candidate_index.indisvalid, false) as valid,
  coalesce(candidate_index.indisready, false) as ready,
  coalesce(
    regexp_replace(lower(candidate_index.index_definition), E'\\s+', ' ', 'g') =
      'create index idx_user_question_progress_user_question_exam on public.user_question_progress using btree (user_id, question_id, stats_exam_code)',
    false
  ) as definition_matches,
  candidate_index.index_definition
from (select true) seed
left join candidate_index on true;

-- J. Candidate freshness boundary. Run after
-- adaptive_candidate_freshness_hardening.sql. The trigger function must match
-- the reviewed body, remain SECURITY DEFINER with a fixed search_path, expose
-- no direct EXECUTE path to application roles, and remain attached/enabled.
with expected(signature, expected_md5) as (
  values (
    'public.validate_practice_session_item_scope()',
    '44d6eb45883359e4b129e26b1e7bf4e5'
  )
)
select
  expected.signature,
  procedure.oid is not null as exists,
  coalesce(procedure.prosecdef, false) as security_definer,
  coalesce(
    'search_path=public, pg_temp' = any(procedure.proconfig),
    false
  ) as fixed_search_path,
  md5(
    btrim(replace(procedure.prosrc, chr(13), ''), E' \t\n')
  ) as actual_md5,
  coalesce(
    md5(btrim(replace(procedure.prosrc, chr(13), ''), E' \t\n')) =
      expected.expected_md5,
    false
  ) as body_matches,
  coalesce(position('adaptive_candidate_changed' in procedure.prosrc) > 0, false)
    as stale_candidate_guard_present,
  coalesce(has_function_privilege('anon', procedure.oid, 'EXECUTE'), false)
    as anon_can_execute,
  coalesce(has_function_privilege('authenticated', procedure.oid, 'EXECUTE'), false)
    as authenticated_can_execute,
  coalesce(has_function_privilege('service_role', procedure.oid, 'EXECUTE'), false)
    as service_role_can_execute,
  exists (
    select 1
    from pg_trigger trigger_meta
    where trigger_meta.tgrelid = 'public.practice_session_items'::regclass
      and trigger_meta.tgname = 'validate_practice_session_item_scope'
      and not trigger_meta.tgisinternal
      and trigger_meta.tgenabled = 'O'
      and trigger_meta.tgtype = 23
      and (
        select array_agg(attribute_meta.attname order by attribute_meta.attname)
        from unnest(trigger_meta.tgattr::smallint[]) selected_attribute(attnum)
        join pg_attribute attribute_meta
          on attribute_meta.attrelid = trigger_meta.tgrelid
         and attribute_meta.attnum = selected_attribute.attnum
      ) = array['position', 'question_id', 'session_id']::name[]
      and trigger_meta.tgfoid = procedure.oid
  ) as trigger_attached_and_enabled,
  procedure.proacl
from expected
left join pg_proc as procedure
  on procedure.oid = to_regprocedure(expected.signature);

-- K. Question-answer access boundary. Save all three result sets before the
-- hardening migration, then run them again after it commits. Afterwards the
-- old authenticated-read policy must be absent; PUBLIC/anon/authenticated must
-- have no table or sensitive-column SELECT, while service_role keeps CRUD.
select policyname, roles, cmd, qual, with_check
from pg_policies
where schemaname = 'public' and tablename = 'questions'
order by policyname;

select grantee, privilege_type
from information_schema.table_privileges
where table_schema = 'public'
  and table_name = 'questions'
  and grantee in ('PUBLIC', 'anon', 'authenticated', 'service_role')
order by grantee, privilege_type;

select
  role_name,
  has_table_privilege(role_name, 'public.questions', 'SELECT') as can_select_table,
  has_column_privilege(role_name, 'public.questions', 'answer', 'SELECT') as can_select_answer,
  has_column_privilege(role_name, 'public.questions', 'explanation', 'SELECT') as can_select_explanation,
  has_table_privilege(role_name, 'public.questions', 'INSERT') as can_insert,
  has_table_privilege(role_name, 'public.questions', 'UPDATE') as can_update,
  has_table_privilege(role_name, 'public.questions', 'DELETE') as can_delete
from unnest(array['anon', 'authenticated', 'service_role']) as roles(role_name)
order by role_name;
