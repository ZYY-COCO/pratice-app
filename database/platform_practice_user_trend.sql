-- 平台近七天刷题人数：按上海自然日统计当日提交过至少一题的去重用户数。
-- 在 Supabase SQL Editor 执行一次；后端会通过 service_role 调用。

begin;

create index if not exists idx_user_answers_created_user
  on public.user_answers (created_at desc, user_id);

create or replace function public.platform_practice_user_trend(
  p_days integer default 7
)
returns table (
  stat_date date,
  practice_users integer
)
language sql
stable
security definer
set search_path = public
as $$
  with settings as (
    select greatest(1, least(coalesce(p_days, 7), 31)) as day_count,
           (now() at time zone 'Asia/Shanghai')::date as today
  ),
  trend_days as (
    select generated_day::date as stat_date
    from settings,
    generate_series(
      settings.today - settings.day_count + 1,
      settings.today,
      interval '1 day'
    ) as generated_day
  )
  select
    trend_day.stat_date,
    count(distinct answer.user_id)::integer as practice_users
  from trend_days as trend_day
  left join public.user_answers as answer
    on answer.created_at >= (trend_day.stat_date::timestamp at time zone 'Asia/Shanghai')
    and answer.created_at < ((trend_day.stat_date + 1)::timestamp at time zone 'Asia/Shanghai')
  group by trend_day.stat_date
  order by trend_day.stat_date;
$$;

revoke all on function public.platform_practice_user_trend(integer) from public, anon, authenticated;
grant execute on function public.platform_practice_user_trend(integer) to service_role;

commit;
