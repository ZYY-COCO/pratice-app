-- Incremental migration for high-frequency-question dashboard filters.
-- Run this in Supabase SQL Editor after deploying the dashboard filter update.

create or replace function public.question_admin_dashboard_snapshot(
  p_limit integer default 8,
  p_subject text default null,
  p_sort_by text default 'wrong_count',
  p_min_attempts integer default 5,
  p_period_days integer default 0
)
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
  with boundaries as (
    select
      (
        date_trunc('day', timezone('Asia/Shanghai', now()))
        at time zone 'Asia/Shanghai'
      ) as today_start,
      now() - interval '15 minutes' as online_start
  ),
  today_visitors as (
    select count(distinct auth_user.id)::integer as total
    from auth.users auth_user
    join public.users app_user on app_user.id = auth_user.id
    cross join boundaries b
    where auth_user.last_sign_in_at >= b.today_start
  ),
  online_member_activity as (
    select count(distinct ua.user_id)::integer as total
    from public.user_answers ua
    join public.users u on u.id = ua.user_id
    cross join boundaries b
    where ua.created_at >= b.online_start
      and u.membership_status = 'active'
      and (u.membership_expires_at is null or u.membership_expires_at > now())
  ),
  ranked_questions as (
    select
      ua.question_id,
      count(*)::integer as attempt_count,
      count(*) filter (where ua.is_correct = false)::integer as wrong_count,
      round(
        (
          count(*) filter (where ua.is_correct = true)::numeric
          / nullif(count(*), 0)
        ) * 100,
        1
      ) as accuracy
    from public.user_answers ua
    join public.questions q on q.id = ua.question_id
    where coalesce(q.source_type, '') <> 'ai_deepseek'
      and (p_subject is null or q.subject = p_subject)
      and (
        coalesce(p_period_days, 0) <= 0
        or ua.created_at >= now() - make_interval(days => p_period_days)
      )
    group by ua.question_id
    having count(*) >= greatest(1, least(coalesce(p_min_attempts, 5), 10000))
    order by
      case when p_sort_by = 'accuracy' then
        count(*) filter (where ua.is_correct = true)::numeric / nullif(count(*), 0)
      end asc nulls last,
      case when p_sort_by = 'attempt_count' then count(*) end desc,
      case when p_sort_by = 'wrong_count' then
        count(*) filter (where ua.is_correct = false)
      end desc,
      count(*) filter (where ua.is_correct = false) desc,
      count(*) desc
    limit greatest(1, least(coalesce(p_limit, 8), 20))
  ),
  difficult_questions as (
    select coalesce(
      jsonb_agg(
        jsonb_build_object(
          'question_id', q.id,
          'stem', q.stem,
          'subject', q.subject,
          'module', q.module,
          'wrong_count', rq.wrong_count,
          'attempt_count', rq.attempt_count,
          'accuracy', coalesce(rq.accuracy, 0)
        )
        order by
          case when p_sort_by = 'accuracy' then rq.accuracy end asc nulls last,
          case when p_sort_by = 'attempt_count' then rq.attempt_count end desc,
          case when p_sort_by = 'wrong_count' then rq.wrong_count end desc,
          rq.wrong_count desc,
          rq.attempt_count desc
      ),
      '[]'::jsonb
    ) as items
    from ranked_questions rq
    join public.questions q on q.id = rq.question_id
  )
  select jsonb_build_object(
    'today_practicing_users', (select total from today_visitors),
    'online_members', (select total from online_member_activity),
    'online_window_minutes', 15,
    'difficult_questions', (select items from difficult_questions)
  );
$$;

drop function if exists public.question_admin_dashboard_snapshot(integer);
drop function if exists public.question_admin_dashboard_snapshot(integer, text, text);

revoke all on function public.question_admin_dashboard_snapshot(integer, text, text, integer, integer)
  from public, anon, authenticated;
grant execute on function public.question_admin_dashboard_snapshot(integer, text, text, integer, integer)
  to service_role;
