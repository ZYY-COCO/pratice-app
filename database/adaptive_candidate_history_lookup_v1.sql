-- Bounded candidate-history lookup for the adaptive /next hot path.
--
-- Apply after database/adaptive_question_delivery_v1.sql.
-- This is an additive migration. It deliberately does not modify or replay
-- adaptive_question_delivery_v1.sql. Apply it before enabling adaptive rollout.

begin;

create index if not exists idx_user_question_progress_user_question_exam
  on public.user_question_progress (user_id, question_id, stats_exam_code);

drop function if exists public.get_adaptive_candidate_history_v1(
  uuid,
  text,
  text,
  uuid[],
  integer,
  boolean
);

create function public.get_adaptive_candidate_history_v1(
  p_user_id uuid,
  p_stats_exam_code text,
  p_subject text,
  p_question_ids uuid[],
  p_recent_limit integer default 100,
  p_include_global_seen boolean default true
)
returns jsonb
language plpgsql
stable
security invoker
set search_path = public, pg_temp
as $$
declare
  normalized_recent_limit integer := least(greatest(coalesce(p_recent_limit, 100), 0), 100);
  candidate_count integer;
begin
  if p_user_id is null then
    raise exception 'adaptive_candidate_history_invalid_user';
  end if;
  if not (
    (p_stats_exam_code = 'Z001' and p_subject in ('中华文化', '英语运用', '逻辑推理'))
    or
    (p_stats_exam_code = 'Z002' and p_subject in ('中华文化', '英语运用', '数学基础'))
  ) then
    raise exception 'adaptive_candidate_history_invalid_scope';
  end if;

  select count(*)::integer
  into candidate_count
  from (
    select distinct candidate.question_id
    from unnest(coalesce(p_question_ids, array[]::uuid[])) as candidate(question_id)
    where candidate.question_id is not null
  ) bounded_candidates;

  if candidate_count > 3000 then
    raise exception 'adaptive_candidate_history_pool_too_large';
  end if;

  return (
    with candidate_ids as materialized (
      select distinct candidate.question_id
      from unnest(coalesce(p_question_ids, array[]::uuid[])) as candidate(question_id)
      where candidate.question_id is not null
    ),
    recent_answers as (
      select answers.question_id
      from public.user_answers answers
      join public.questions questions on questions.id = answers.question_id
      where answers.user_id = p_user_id
        and answers.stats_exam_code = p_stats_exam_code
        and questions.subject = p_subject
        and questions.exam_code in ('COMMON', p_stats_exam_code)
        and (
          questions.exam_code <> 'COMMON'
          or questions.subject in ('中华文化', '英语运用')
        )
      order by answers.created_at desc, answers.id desc
      limit normalized_recent_limit
    ),
    recent_ids as (
      select distinct recent_answers.question_id
      from recent_answers
    ),
    globally_seen_ids as (
      select candidates.question_id
      from candidate_ids candidates
      join public.questions questions on questions.id = candidates.question_id
      where p_include_global_seen
        and questions.subject = p_subject
        and questions.exam_code in ('COMMON', p_stats_exam_code)
        and (
          questions.exam_code <> 'COMMON'
          or questions.subject in ('中华文化', '英语运用')
        )
        and exists (
          select 1
          from public.user_answers answers
          where answers.user_id = p_user_id
            and answers.question_id = candidates.question_id
        )
    ),
    scoped_progress as (
      select
        progress.question_id,
        progress.stats_exam_code,
        progress.correct_count,
        progress.last_is_correct,
        progress.last_answered_at
      from candidate_ids candidates
      join public.user_question_progress progress
        on progress.user_id = p_user_id
       and progress.stats_exam_code = p_stats_exam_code
       and progress.question_id = candidates.question_id
      join public.questions questions on questions.id = progress.question_id
      where questions.subject = p_subject
        and questions.exam_code in ('COMMON', p_stats_exam_code)
        and (
          questions.exam_code <> 'COMMON'
          or questions.subject in ('中华文化', '英语运用')
        )
    )
    select jsonb_build_object(
      'recent_question_ids', coalesce(
        (select jsonb_agg(recent_ids.question_id order by recent_ids.question_id) from recent_ids),
        '[]'::jsonb
      ),
      'ever_answered_question_ids', coalesce(
        (
          select jsonb_agg(globally_seen_ids.question_id order by globally_seen_ids.question_id)
          from globally_seen_ids
        ),
        '[]'::jsonb
      ),
      'progress_rows', coalesce(
        (
          select jsonb_agg(
            jsonb_build_object(
              'question_id', scoped_progress.question_id,
              'stats_exam_code', scoped_progress.stats_exam_code,
              'correct_count', scoped_progress.correct_count,
              'last_is_correct', scoped_progress.last_is_correct,
              'last_answered_at', scoped_progress.last_answered_at
            )
            order by scoped_progress.question_id
          )
          from scoped_progress
        ),
        '[]'::jsonb
      )
    )
  );
end;
$$;

revoke all on function public.get_adaptive_candidate_history_v1(
  uuid,
  text,
  text,
  uuid[],
  integer,
  boolean
) from public, anon, authenticated;

grant execute on function public.get_adaptive_candidate_history_v1(
  uuid,
  text,
  text,
  uuid[],
  integer,
  boolean
) to service_role;

notify pgrst, 'reload schema';

commit;
