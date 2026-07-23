-- Internal question-bank portal access and dashboard aggregation.
-- Apply this migration before granting non-admin users access to the portal.

create table if not exists public.question_admin_access (
  user_id uuid primary key references public.users(id) on delete cascade,
  display_name text,
  note text,
  is_active boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_question_admin_access_active
  on public.question_admin_access (is_active)
  where is_active = true;

drop trigger if exists set_question_admin_access_updated_at
  on public.question_admin_access;
create trigger set_question_admin_access_updated_at
before update on public.question_admin_access
for each row execute function public.set_updated_at();

alter table public.question_admin_access enable row level security;

revoke all on public.question_admin_access from anon, authenticated;
grant all on public.question_admin_access to service_role;

create or replace function public.question_admin_dashboard_snapshot(
  p_limit integer default 8
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
  today_practicing as (
    select count(distinct ua.user_id)::integer as total
    from public.user_answers ua
    cross join boundaries b
    where ua.created_at >= b.today_start
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
    group by ua.question_id
    order by
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
        order by rq.wrong_count desc, rq.attempt_count desc
      ),
      '[]'::jsonb
    ) as items
    from ranked_questions rq
    join public.questions q on q.id = rq.question_id
  )
  select jsonb_build_object(
    'today_practicing_users', (select total from today_practicing),
    'online_members', (select total from online_member_activity),
    'online_window_minutes', 15,
    'difficult_questions', (select items from difficult_questions)
  );
$$;

revoke all on function public.question_admin_dashboard_snapshot(integer)
  from public, anon, authenticated;
grant execute on function public.question_admin_dashboard_snapshot(integer)
  to service_role;

-- Grant access by inserting an existing app user. There is intentionally no
-- management UI for this table.
--
-- insert into public.question_admin_access (user_id, display_name, note)
-- select id, coalesce(nickname, email), '题库后台'
-- from public.users
-- where lower(email) = lower('editor@example.com')
-- on conflict (user_id) do update
-- set is_active = true,
--     display_name = excluded.display_name,
--     note = excluded.note,
--     updated_at = now();
