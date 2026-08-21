-- Operations-center data models for the internal administration portal.
-- Apply this migration after admin_management.sql, question_admin_portal.sql,
-- and major_catalog.sql
-- and before deploying the user, admission-data, and homepage-operation modules.

create table if not exists public.historical_scoreline_import_runs (
  id uuid primary key default gen_random_uuid(),
  source_filename text not null,
  source_sha256 text not null,
  statistics jsonb not null default '{}'::jsonb,
  status text not null default 'draft'
    check (status in ('draft', 'published', 'archived', 'failed')),
  created_by uuid references public.users(id) on delete set null,
  published_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  published_at timestamptz,
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_historical_scoreline_import_runs_hash
  on public.historical_scoreline_import_runs (source_sha256);
create index if not exists idx_historical_scoreline_import_runs_status
  on public.historical_scoreline_import_runs (status, created_at desc);

create table if not exists public.historical_scoreline_records (
  id uuid primary key default gen_random_uuid(),
  import_run_id uuid not null references public.historical_scoreline_import_runs(id) on delete cascade,
  score_year text not null check (score_year ~ '^20[0-9]{2}$'),
  region text not null,
  school_name text not null,
  unit_name text not null default '',
  score_raw text not null default '',
  score_value numeric(7, 2),
  score_kind text not null default 'score'
    check (score_kind in ('score', 'missing', 'unavailable', 'official', 'multiple', 'note')),
  source_url text,
  source_note text,
  is_published boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_historical_scoreline_records_run_year
  on public.historical_scoreline_records (import_run_id, score_year, region, school_name);
create index if not exists idx_historical_scoreline_records_lookup
  on public.historical_scoreline_records (score_year, region, school_name);

create table if not exists public.school_announcement_import_runs (
  id uuid primary key default gen_random_uuid(),
  source_filename text not null,
  source_sha256 text not null,
  statistics jsonb not null default '{}'::jsonb,
  status text not null default 'draft'
    check (status in ('draft', 'published', 'archived', 'failed')),
  created_by uuid references public.users(id) on delete set null,
  published_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  published_at timestamptz,
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_school_announcement_import_runs_hash
  on public.school_announcement_import_runs (source_sha256);
create index if not exists idx_school_announcement_import_runs_status
  on public.school_announcement_import_runs (status, created_at desc);

create table if not exists public.school_announcement_records (
  id uuid primary key default gen_random_uuid(),
  import_run_id uuid not null references public.school_announcement_import_runs(id) on delete cascade,
  notice_year text not null check (notice_year ~ '^20[0-9]{2}$'),
  region text not null,
  school_name text not null,
  unit_name text not null default '',
  notice_type text not null check (notice_type in ('brochure', 'scoreline_retest')),
  title text not null,
  summary text not null default '',
  notice_date text,
  source_url text,
  content_text text not null default '',
  is_published boolean not null default true,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- Records are imported as a draft batch first.  The batch state is used for
-- version management, while the record state allows the operations team to
-- curate individual notices without copying the public dataset elsewhere.
alter table public.school_announcement_records
  add column if not exists status text not null default 'draft'
    check (status in ('draft', 'published', 'archived')),
  add column if not exists is_pinned boolean not null default false,
  add column if not exists sort_order integer not null default 0,
  add column if not exists published_at timestamptz,
  add column if not exists published_by uuid references public.users(id) on delete set null,
  add column if not exists archived_at timestamptz,
  add column if not exists archived_by uuid references public.users(id) on delete set null;

create index if not exists idx_school_announcement_records_run_year
  on public.school_announcement_records (import_run_id, notice_year, region, school_name);
create index if not exists idx_school_announcement_records_lookup
  on public.school_announcement_records (notice_year, region, school_name, notice_type);

create table if not exists public.home_content_items (
  id uuid primary key default gen_random_uuid(),
  slot text not null check (slot in ('focus', 'news', 'service')),
  title text not null,
  subtitle text not null default '',
  badge text not null default '',
  source text not null default '',
  display_date text,
  cover_label text not null default '',
  tone text not null default 'is-blue'
    check (tone in ('is-blue', 'is-violet', 'is-mint', 'is-orange', 'is-school', 'is-major', 'is-guide')),
  target_url text not null default '',
  route_key text not null default '',
  sort_order integer not null default 0,
  status text not null default 'draft'
    check (status in ('draft', 'published', 'archived')),
  starts_at timestamptz,
  ends_at timestamptz,
  created_by uuid references public.users(id) on delete set null,
  updated_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

-- ``announcement_record_id`` is optional: focus cards can be independent,
-- while the home-news slot normally points to an already published notice.
alter table public.home_content_items
  add column if not exists announcement_record_id uuid references public.school_announcement_records(id) on delete set null;

create index if not exists idx_home_content_items_slot_status_order
  on public.home_content_items (slot, status, sort_order, created_at desc);
create index if not exists idx_school_announcement_records_status_order
  on public.school_announcement_records (status, is_pinned desc, sort_order, created_at desc);

-- Professional catalogues are kept in a flat staging table first.  A single
-- published staging run is converted into the existing normalized catalogue
-- tables by the publish function below, so students never query a half-written
-- directory snapshot.
create table if not exists public.major_catalog_staging_runs (
  id uuid primary key default gen_random_uuid(),
  source_filename text not null,
  source_sha256 text not null,
  catalog_year text not null check (catalog_year ~ '^20[0-9]{2}$'),
  statistics jsonb not null default '{}'::jsonb,
  status text not null default 'draft'
    check (status in ('draft', 'published', 'archived', 'failed')),
  created_by uuid references public.users(id) on delete set null,
  published_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  published_at timestamptz,
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_major_catalog_staging_runs_hash
  on public.major_catalog_staging_runs (source_sha256);
create index if not exists idx_major_catalog_staging_runs_status
  on public.major_catalog_staging_runs (catalog_year, status, created_at desc);

create table if not exists public.major_catalog_staging_records (
  id uuid primary key default gen_random_uuid(),
  import_run_id uuid not null references public.major_catalog_staging_runs(id) on delete cascade,
  catalog_year text not null check (catalog_year ~ '^20[0-9]{2}$'),
  region text not null,
  school_name text not null,
  department_name text not null default '未区分院系所',
  program_name text not null,
  program_code text not null default '',
  direction_name text not null default '不区分研究方向',
  tutor text not null default '',
  exam_code text not null check (exam_code in ('Z001', 'Z002')),
  degree text not null default '',
  study_mode text not null default '',
  source_row integer not null,
  created_at timestamptz not null default now()
);

create index if not exists idx_major_catalog_staging_records_run
  on public.major_catalog_staging_records (import_run_id, source_row);

drop trigger if exists set_historical_scoreline_import_runs_updated_at on public.historical_scoreline_import_runs;
create trigger set_historical_scoreline_import_runs_updated_at
before update on public.historical_scoreline_import_runs
for each row execute function public.set_updated_at();

drop trigger if exists set_historical_scoreline_records_updated_at on public.historical_scoreline_records;
create trigger set_historical_scoreline_records_updated_at
before update on public.historical_scoreline_records
for each row execute function public.set_updated_at();

drop trigger if exists set_school_announcement_import_runs_updated_at on public.school_announcement_import_runs;
create trigger set_school_announcement_import_runs_updated_at
before update on public.school_announcement_import_runs
for each row execute function public.set_updated_at();

drop trigger if exists set_school_announcement_records_updated_at on public.school_announcement_records;
create trigger set_school_announcement_records_updated_at
before update on public.school_announcement_records
for each row execute function public.set_updated_at();

drop trigger if exists set_home_content_items_updated_at on public.home_content_items;
create trigger set_home_content_items_updated_at
before update on public.home_content_items
for each row execute function public.set_updated_at();

drop trigger if exists set_major_catalog_staging_runs_updated_at on public.major_catalog_staging_runs;
create trigger set_major_catalog_staging_runs_updated_at
before update on public.major_catalog_staging_runs
for each row execute function public.set_updated_at();

create or replace function public.question_admin_portal_user_overview()
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
  with boundaries as (
    select
      (date_trunc('day', timezone('Asia/Shanghai', now())) at time zone 'Asia/Shanghai') as today_start,
      now() - interval '7 days' as week_start
  )
  select jsonb_build_object(
    'total_users', (select count(*)::integer from public.users),
    'new_today', (select count(*)::integer from public.users u cross join boundaries b where u.created_at >= b.today_start),
    'new_week', (select count(*)::integer from public.users u cross join boundaries b where u.created_at >= b.week_start),
    'active_week', (select count(distinct ua.user_id)::integer from public.user_answers ua cross join boundaries b where ua.created_at >= b.week_start),
    'active_members', (select count(*)::integer from public.users where membership_status = 'active' and (membership_expires_at is null or membership_expires_at > now()))
  );
$$;

drop function if exists public.question_admin_portal_user_list(
  text, text, text, text, text, timestamptz, timestamptz, text, integer, integer
);

create or replace function public.question_admin_portal_user_list(
  p_search text default null,
  p_exam_target text default null,
  p_membership_status text default null,
  p_account_status text default 'all',
  p_activity text default 'all',
  p_registered_from timestamptz default null,
  p_registered_to timestamptz default null,
  p_sort_by text default 'created_at',
  p_sort_direction text default 'desc',
  p_limit integer default 20,
  p_offset integer default 0
)
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
  with answer_stats as (
    select
      ua.user_id,
      count(*)::integer as answer_count,
      count(*) filter (where ua.is_correct)::integer as correct_count,
      max(ua.created_at) as last_answer_at
    from public.user_answers ua
    group by ua.user_id
  ),
  filtered as (
    select
      u.id,
      u.email,
      u.phone,
      u.nickname,
      u.avatar_url,
      u.exam_target,
      u.membership_status,
      u.membership_plan,
      u.membership_expires_at,
      u.disabled_at,
      u.created_at,
      coalesce(stats.answer_count, 0) as answer_count,
      coalesce(stats.correct_count, 0) as correct_count,
      greatest(coalesce(stats.answer_count, 0) - coalesce(stats.correct_count, 0), 0) as wrong_count,
      case when coalesce(stats.answer_count, 0) > 0
        then round((stats.correct_count::numeric / stats.answer_count::numeric) * 100, 1)
        else 0
      end as accuracy,
      stats.last_answer_at
    from public.users u
    left join answer_stats stats on stats.user_id = u.id
    where
      (coalesce(trim(p_search), '') = '' or lower(concat_ws(' ', u.email, u.phone, u.nickname)) like '%' || lower(trim(p_search)) || '%')
      and (coalesce(trim(p_exam_target), '') = '' or u.exam_target = trim(p_exam_target))
      and (
        coalesce(trim(p_membership_status), '') = ''
        or (
          trim(p_membership_status) = 'active'
          and u.membership_status = 'active'
          and (u.membership_expires_at is null or u.membership_expires_at > now())
        )
        or (
          trim(p_membership_status) = 'inactive'
          and (u.membership_status is distinct from 'active' or u.membership_expires_at <= now())
        )
      )
      and (
        coalesce(trim(p_account_status), 'all') = 'all'
        or (trim(p_account_status) = 'active' and u.disabled_at is null)
        or (trim(p_account_status) = 'disabled' and u.disabled_at is not null)
      )
      and (p_registered_from is null or u.created_at >= p_registered_from)
      and (p_registered_to is null or u.created_at < p_registered_to)
      and (
        coalesce(trim(p_activity), 'all') = 'all'
        or (trim(p_activity) = 'active_7d' and stats.last_answer_at >= now() - interval '7 days')
        or (trim(p_activity) = 'inactive' and (stats.last_answer_at is null or stats.last_answer_at < now() - interval '30 days'))
      )
  ),
  ordered as (
    select *
    from filtered
    order by
      case when p_sort_by = 'exam_target' and p_sort_direction = 'asc' then exam_target end asc nulls last,
      case when p_sort_by = 'exam_target' and p_sort_direction = 'desc' then exam_target end desc nulls last,
      case when p_sort_by = 'answer_count' and p_sort_direction = 'asc' then answer_count end asc,
      case when p_sort_by = 'answer_count' and p_sort_direction = 'desc' then answer_count end desc,
      case when p_sort_by = 'accuracy' and p_sort_direction = 'asc' then accuracy end asc,
      case when p_sort_by = 'accuracy' and p_sort_direction = 'desc' then accuracy end desc,
      case when p_sort_by = 'last_active' and p_sort_direction = 'asc' then last_answer_at end asc nulls last,
      case when p_sort_by = 'last_active' and p_sort_direction = 'desc' then last_answer_at end desc nulls last,
      case when p_sort_by = 'created_at' and p_sort_direction = 'asc' then created_at end asc,
      case when p_sort_by = 'created_at' and p_sort_direction = 'desc' then created_at end desc,
      created_at desc,
      id
    limit greatest(1, least(coalesce(p_limit, 20), 100))
    offset greatest(0, coalesce(p_offset, 0))
  )
  select jsonb_build_object(
    'count', (select count(*)::integer from filtered),
    'items', coalesce((
      select jsonb_agg(jsonb_build_object(
        'id', id,
        'email', email,
        'phone', phone,
        'nickname', nickname,
        'avatar_url', avatar_url,
        'exam_target', exam_target,
        'membership_status', membership_status,
        'membership_plan', membership_plan,
        'membership_expires_at', membership_expires_at,
        'disabled_at', disabled_at,
        'created_at', created_at,
        'answer_count', answer_count,
        'correct_count', correct_count,
        'wrong_count', wrong_count,
        'accuracy', accuracy,
        'last_answer_at', last_answer_at
      ) order by
        case when p_sort_by = 'exam_target' and p_sort_direction = 'asc' then exam_target end asc nulls last,
        case when p_sort_by = 'exam_target' and p_sort_direction = 'desc' then exam_target end desc nulls last,
        case when p_sort_by = 'answer_count' and p_sort_direction = 'asc' then answer_count end asc,
        case when p_sort_by = 'answer_count' and p_sort_direction = 'desc' then answer_count end desc,
        case when p_sort_by = 'accuracy' and p_sort_direction = 'asc' then accuracy end asc,
        case when p_sort_by = 'accuracy' and p_sort_direction = 'desc' then accuracy end desc,
        case when p_sort_by = 'last_active' and p_sort_direction = 'asc' then last_answer_at end asc nulls last,
        case when p_sort_by = 'last_active' and p_sort_direction = 'desc' then last_answer_at end desc nulls last,
        case when p_sort_by = 'created_at' and p_sort_direction = 'asc' then created_at end asc,
        case when p_sort_by = 'created_at' and p_sort_direction = 'desc' then created_at end desc,
        created_at desc,
        id
      ) from ordered
    ), '[]'::jsonb)
  );
$$;

revoke all on function public.question_admin_portal_user_overview() from public, anon, authenticated;
grant execute on function public.question_admin_portal_user_overview() to service_role;
revoke all on function public.question_admin_portal_user_list(text, text, text, text, text, timestamptz, timestamptz, text, text, integer, integer) from public, anon, authenticated;
grant execute on function public.question_admin_portal_user_list(text, text, text, text, text, timestamptz, timestamptz, text, text, integer, integer) to service_role;

-- The user-detail panel has a bounded recent-answer feed, but its totals and
-- per-subject accuracy are always produced inside PostgreSQL.  This keeps the
-- desktop portal from fetching all answer rows for one user just to display a
-- few aggregates.
create or replace function public.question_admin_portal_user_detail(
  p_user_id uuid
)
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
  with answer_summary as (
    select
      count(*)::integer as total,
      count(*) filter (where is_correct)::integer as correct,
      max(created_at) as last_answer_at
    from public.user_answers
    where user_id = p_user_id
  ),
  subject_summary as (
    select
      q.subject,
      count(*)::integer as total,
      count(*) filter (where ua.is_correct)::integer as correct,
      round(
        (count(*) filter (where ua.is_correct)::numeric / nullif(count(*), 0)) * 100,
        1
      ) as accuracy
    from public.user_answers ua
    join public.questions q on q.id = ua.question_id
    where ua.user_id = p_user_id
    group by q.subject
  ),
  recent_answers as (
    select
      ua.id,
      ua.question_id,
      ua.selected_answer,
      ua.is_correct,
      ua.used_time,
      ua.created_at,
      q.exam_code,
      q.subject,
      q.module,
      q.submodule,
      q.stem
    from public.user_answers ua
    left join public.questions q on q.id = ua.question_id
    where ua.user_id = p_user_id
    order by ua.created_at desc
    limit 30
  ),
  membership_orders as (
    select id, provider, provider_order_id, plan_code, amount_cents, currency, status, paid_at, created_at
    from public.membership_orders
    where user_id = p_user_id
    order by created_at desc
    limit 20
  ),
  admin_actions as (
    select id, admin_user_id, action, target_type, target_id, details, created_at
    from public.admin_action_logs
    where target_type = 'user' and target_id = p_user_id
    order by created_at desc
    limit 20
  )
  select jsonb_build_object(
    'profile', coalesce((select to_jsonb(u) from public.users u where u.id = p_user_id), '{}'::jsonb),
    'answer_summary', jsonb_build_object(
      'total', coalesce((select total from answer_summary), 0),
      'correct', coalesce((select correct from answer_summary), 0),
      'wrong', greatest(coalesce((select total from answer_summary), 0) - coalesce((select correct from answer_summary), 0), 0),
      'accuracy', case
        when coalesce((select total from answer_summary), 0) > 0
          then round((select correct from answer_summary)::numeric / (select total from answer_summary)::numeric * 100, 1)
        else 0
      end,
      'last_answer_at', (select last_answer_at from answer_summary),
      'wrong_question_count', (select count(*)::integer from public.wrong_questions where user_id = p_user_id)
    ),
    'subject_accuracy', coalesce((
      select jsonb_agg(jsonb_build_object(
        'subject', subject,
        'total', total,
        'correct', correct,
        'wrong', greatest(total - correct, 0),
        'accuracy', coalesce(accuracy, 0)
      ) order by total desc, subject)
      from subject_summary
    ), '[]'::jsonb),
    'recent_answers', coalesce((select jsonb_agg(to_jsonb(recent_answers) order by created_at desc) from recent_answers), '[]'::jsonb),
    'membership_orders', coalesce((select jsonb_agg(to_jsonb(membership_orders) order by created_at desc) from membership_orders), '[]'::jsonb),
    'admin_actions', coalesce((select jsonb_agg(to_jsonb(admin_actions) order by created_at desc) from admin_actions), '[]'::jsonb)
  );
$$;

create or replace function public.question_admin_portal_operations_overview()
returns jsonb
language sql
stable
security definer
set search_path = public
as $$
  with boundaries as (
    select
      (date_trunc('day', timezone('Asia/Shanghai', now())) at time zone 'Asia/Shanghai') as today_start,
      now() - interval '7 days' as week_start
  )
  select jsonb_build_object(
    'total_users', (select count(*)::integer from public.users),
    'new_today', (
      select count(*)::integer
      from public.users u cross join boundaries b
      where u.created_at >= b.today_start
    ),
    'new_week', (
      select count(*)::integer
      from public.users u cross join boundaries b
      where u.created_at >= b.week_start
    ),
    'active_week', (
      select count(distinct ua.user_id)::integer
      from public.user_answers ua cross join boundaries b
      where ua.created_at >= b.week_start
    ),
    'active_members', (
      select count(*)::integer
      from public.users
      where membership_status = 'active'
        and (membership_expires_at is null or membership_expires_at > now())
    ),
    'published_home_items', (select count(*)::integer from public.home_content_items where status = 'published'),
    'published_announcements', (select count(*)::integer from public.school_announcement_records where status = 'published'),
    'scoreline_draft_runs', (select count(*)::integer from public.historical_scoreline_import_runs where status = 'draft'),
    'announcement_draft_runs', (select count(*)::integer from public.school_announcement_import_runs where status = 'draft'),
    'major_catalog_draft_runs', (select count(*)::integer from public.major_catalog_staging_runs where status = 'draft'),
    'recent_import_failures', (
      select count(*)::integer
      from (
        select created_at from public.historical_scoreline_import_runs where status = 'failed' and created_at >= now() - interval '30 days'
        union all
        select created_at from public.school_announcement_import_runs where status = 'failed' and created_at >= now() - interval '30 days'
        union all
        select created_at from public.major_catalog_staging_runs where status = 'failed' and created_at >= now() - interval '30 days'
      ) failed_runs
    )
  );
$$;

revoke all on function public.question_admin_portal_user_detail(uuid) from public, anon, authenticated;
grant execute on function public.question_admin_portal_user_detail(uuid) to service_role;
revoke all on function public.question_admin_portal_operations_overview() from public, anon, authenticated;
grant execute on function public.question_admin_portal_operations_overview() to service_role;

-- Publish and rollback are version switches, so they must be a single database
-- transaction.  An archived prior run can be published again to roll back the
-- public dataset without copying rows or losing its import trail.
create or replace function public.question_admin_portal_publish_import_run(
  p_dataset text,
  p_run_id uuid,
  p_actor_id uuid
)
returns jsonb
language plpgsql
security definer
set search_path = public
as $$
declare
  v_run jsonb;
  v_source_filename text;
  v_source_sha256 text;
  v_catalog_year text;
  v_statistics jsonb;
  v_catalog_run_id uuid;
begin
  if p_dataset = 'scorelines' then
    select to_jsonb(run) into v_run
    from public.historical_scoreline_import_runs run
    where run.id = p_run_id
    for update;
    if v_run is null then
      raise exception 'scoreline import run not found';
    end if;
    if coalesce(v_run ->> 'status', 'draft') = 'failed' then
      raise exception 'failed scoreline import run cannot be published';
    end if;
    if not exists (
      select 1 from public.historical_scoreline_records where import_run_id = p_run_id
    ) then
      raise exception 'scoreline import run has no records';
    end if;
    if (select count(*) from public.historical_scoreline_records where import_run_id = p_run_id)
      <> coalesce((v_run #>> '{statistics,valid_rows}')::integer, 0) then
      raise exception 'scoreline import run is incomplete';
    end if;

    update public.historical_scoreline_import_runs
    set status = 'archived'
    where status = 'published' and id <> p_run_id;
    update public.historical_scoreline_records
    set is_published = false
    where import_run_id <> p_run_id and is_published = true;
    update public.historical_scoreline_import_runs
    set status = 'published', published_by = p_actor_id, published_at = now()
    where id = p_run_id;
    update public.historical_scoreline_records
    set is_published = true
    where import_run_id = p_run_id;

    return jsonb_build_object('id', p_run_id, 'status', 'published', 'dataset', p_dataset);
  end if;

  if p_dataset = 'announcements' then
    select to_jsonb(run) into v_run
    from public.school_announcement_import_runs run
    where run.id = p_run_id
    for update;
    if v_run is null then
      raise exception 'school announcement import run not found';
    end if;
    if coalesce(v_run ->> 'status', 'draft') = 'failed' then
      raise exception 'failed school announcement import run cannot be published';
    end if;
    if not exists (
      select 1 from public.school_announcement_records where import_run_id = p_run_id
    ) then
      raise exception 'school announcement import run has no records';
    end if;
    if (select count(*) from public.school_announcement_records where import_run_id = p_run_id)
      <> coalesce((v_run #>> '{statistics,valid_rows}')::integer, 0) then
      raise exception 'school announcement import run is incomplete';
    end if;

    update public.school_announcement_import_runs
    set status = 'archived'
    where status = 'published' and id <> p_run_id;
    update public.school_announcement_records
    set status = 'archived', is_published = false, archived_at = now(), archived_by = p_actor_id
    where import_run_id <> p_run_id and status = 'published';
    update public.school_announcement_import_runs
    set status = 'published', published_by = p_actor_id, published_at = now()
    where id = p_run_id;
    update public.school_announcement_records
    set status = 'published', is_published = true, published_at = now(), published_by = p_actor_id,
        archived_at = null, archived_by = null
    where import_run_id = p_run_id;

    return jsonb_build_object('id', p_run_id, 'status', 'published', 'dataset', p_dataset);
  end if;

  if p_dataset = 'major-catalog' then
    select to_jsonb(run) into v_run
    from public.major_catalog_staging_runs run
    where run.id = p_run_id
    for update;
    if v_run is null then
      raise exception 'major catalog staging run not found';
    end if;
    if coalesce(v_run ->> 'status', 'draft') = 'failed' then
      raise exception 'failed major catalog staging run cannot be published';
    end if;
    if not exists (
      select 1 from public.major_catalog_staging_records where import_run_id = p_run_id
    ) then
      raise exception 'major catalog staging run has no records';
    end if;
    if (select count(*) from public.major_catalog_staging_records where import_run_id = p_run_id)
      <> coalesce((v_run #>> '{statistics,valid_rows}')::integer, 0) then
      raise exception 'major catalog staging run is incomplete';
    end if;

    select source_filename, source_sha256, catalog_year, statistics
    into v_source_filename, v_source_sha256, v_catalog_year, v_statistics
    from public.major_catalog_staging_runs
    where id = p_run_id;
    v_catalog_run_id := gen_random_uuid();

    insert into public.major_catalog_import_runs (
      id, source_filename, source_sha256, source_version, source_statistics, status, started_at
    ) values (
      v_catalog_run_id,
      v_source_filename,
      v_source_sha256,
      v_catalog_year || '-admin-xlsx-' || left(v_source_sha256, 12),
      v_statistics,
      'running',
      now()
    );

    -- Existing normalized rows may use IDs generated by the legacy JSON
    -- importer, while the operations workbook uses deterministic ops-* IDs.
    -- Replace the target year's snapshot inside this transaction before the
    -- upserts so secondary unique keys such as (region_name, name) cannot
    -- collide with rows that belong to the previous public version.
    if v_catalog_year = '2026' then
      delete from public.major_catalog_directions where id !~ '^20[0-9]{2}::';
      delete from public.major_catalog_programs where id !~ '^20[0-9]{2}::';
      delete from public.major_catalog_departments where id !~ '^20[0-9]{2}::';
      delete from public.major_catalog_schools where id !~ '^20[0-9]{2}::';
      delete from public.major_catalog_regions where name !~ '^20[0-9]{2}::region::';
    else
      delete from public.major_catalog_directions where id like v_catalog_year || '::%';
      delete from public.major_catalog_programs where id like v_catalog_year || '::%';
      delete from public.major_catalog_departments where id like v_catalog_year || '::%';
      delete from public.major_catalog_schools where id like v_catalog_year || '::%';
      delete from public.major_catalog_regions where name like v_catalog_year || '::region::%';
    end if;

    with source_rows as (
      select
        case when v_catalog_year = '2026' then region else v_catalog_year || '::region::' || region end as region_key,
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-school-' || substr(md5(region || chr(31) || school_name), 1, 16) as school_id,
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-department-' || substr(md5(region || chr(31) || school_name || chr(31) || department_name), 1, 16) as department_id,
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-program-' || substr(md5(region || chr(31) || school_name || chr(31) || department_name || chr(31) || program_name || chr(31) || program_code), 1, 16) as program_id,
        region, school_name, department_name, program_name, program_code,
        direction_name, tutor, exam_code, degree, study_mode, source_row
      from public.major_catalog_staging_records
      where import_run_id = p_run_id
    ), grouped as (
      select
        region_key,
        min(source_row) as sort_order,
        count(distinct school_id)::integer as school_count,
        count(distinct program_id)::integer as program_count,
        count(distinct school_id) filter (where exam_code = 'Z001')::integer as school_count_z001,
        count(distinct school_id) filter (where exam_code = 'Z002')::integer as school_count_z002,
        count(distinct program_id) filter (where exam_code = 'Z001')::integer as program_count_z001,
        count(distinct program_id) filter (where exam_code = 'Z002')::integer as program_count_z002
      from source_rows
      group by region_key
    )
    insert into public.major_catalog_regions (
      name, sort_order, school_count, program_count, school_count_z001, school_count_z002,
      program_count_z001, program_count_z002, sync_run_id, updated_at
    )
    select
      region_key,
      row_number() over (order by sort_order, region_key)::integer - 1,
      school_count, program_count, school_count_z001, school_count_z002,
      program_count_z001, program_count_z002, v_catalog_run_id, now()
    from grouped
    on conflict (name) do update set
      sort_order = excluded.sort_order,
      school_count = excluded.school_count,
      program_count = excluded.program_count,
      school_count_z001 = excluded.school_count_z001,
      school_count_z002 = excluded.school_count_z002,
      program_count_z001 = excluded.program_count_z001,
      program_count_z002 = excluded.program_count_z002,
      sync_run_id = excluded.sync_run_id,
      updated_at = excluded.updated_at;

    with source_rows as (
      select
        case when v_catalog_year = '2026' then region else v_catalog_year || '::region::' || region end as region_key,
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-school-' || substr(md5(region || chr(31) || school_name), 1, 16) as school_id,
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-department-' || substr(md5(region || chr(31) || school_name || chr(31) || department_name), 1, 16) as department_id,
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-program-' || substr(md5(region || chr(31) || school_name || chr(31) || department_name || chr(31) || program_name || chr(31) || program_code), 1, 16) as program_id,
        school_name, exam_code, source_row
      from public.major_catalog_staging_records
      where import_run_id = p_run_id
    ), grouped as (
      select
        school_id, region_key, max(school_name) as school_name, min(source_row) as sort_order,
        array_agg(distinct exam_code order by exam_code) as exam_codes,
        count(distinct department_id)::integer as department_count,
        count(distinct program_id)::integer as program_count,
        count(distinct department_id) filter (where exam_code = 'Z001')::integer as department_count_z001,
        count(distinct department_id) filter (where exam_code = 'Z002')::integer as department_count_z002,
        count(distinct program_id) filter (where exam_code = 'Z001')::integer as program_count_z001,
        count(distinct program_id) filter (where exam_code = 'Z002')::integer as program_count_z002
      from source_rows
      group by school_id, region_key
    )
    insert into public.major_catalog_schools (
      id, region_name, name, sort_order, exam_codes, department_count, program_count,
      department_count_z001, department_count_z002, program_count_z001, program_count_z002,
      sync_run_id, updated_at
    )
    select
      school_id, region_key, school_name, sort_order, exam_codes, department_count, program_count,
      department_count_z001, department_count_z002, program_count_z001, program_count_z002,
      v_catalog_run_id, now()
    from grouped
    on conflict (id) do update set
      region_name = excluded.region_name,
      name = excluded.name,
      sort_order = excluded.sort_order,
      exam_codes = excluded.exam_codes,
      department_count = excluded.department_count,
      program_count = excluded.program_count,
      department_count_z001 = excluded.department_count_z001,
      department_count_z002 = excluded.department_count_z002,
      program_count_z001 = excluded.program_count_z001,
      program_count_z002 = excluded.program_count_z002,
      sync_run_id = excluded.sync_run_id,
      updated_at = excluded.updated_at;

    with source_rows as (
      select
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-school-' || substr(md5(region || chr(31) || school_name), 1, 16) as school_id,
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-department-' || substr(md5(region || chr(31) || school_name || chr(31) || department_name), 1, 16) as department_id,
        department_name, source_row
      from public.major_catalog_staging_records
      where import_run_id = p_run_id
    ), grouped as (
      select department_id, school_id, max(department_name) as department_name, min(source_row) as sort_order
      from source_rows
      group by department_id, school_id
    )
    insert into public.major_catalog_departments (id, school_id, name, sort_order, sync_run_id, updated_at)
    select department_id, school_id, department_name, sort_order, v_catalog_run_id, now()
    from grouped
    on conflict (id) do update set
      school_id = excluded.school_id,
      name = excluded.name,
      sort_order = excluded.sort_order,
      sync_run_id = excluded.sync_run_id,
      updated_at = excluded.updated_at;

    with source_rows as (
      select
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-school-' || substr(md5(region || chr(31) || school_name), 1, 16) as school_id,
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-department-' || substr(md5(region || chr(31) || school_name || chr(31) || department_name), 1, 16) as department_id,
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-program-' || substr(md5(region || chr(31) || school_name || chr(31) || department_name || chr(31) || program_name || chr(31) || program_code), 1, 16) as program_id,
        program_name, program_code, direction_name, tutor, exam_code, degree, study_mode, source_row
      from public.major_catalog_staging_records
      where import_run_id = p_run_id
    ), grouped as (
      select
        program_id, school_id, department_id, max(program_name) as program_name, max(program_code) as program_code,
        min(source_row) as sort_order,
        array_agg(distinct exam_code order by exam_code) as exam_codes,
        coalesce(array_agg(distinct degree order by degree) filter (where degree <> ''), array[]::text[]) as degree_options,
        coalesce(array_agg(distinct study_mode order by study_mode) filter (where study_mode <> ''), array[]::text[]) as study_mode_options,
        count(distinct (direction_name, tutor, exam_code, degree, study_mode))::integer as direction_count
      from source_rows
      group by program_id, school_id, department_id
    )
    insert into public.major_catalog_programs (
      id, school_id, department_id, name, code, sort_order, exam_codes, degree_options,
      study_mode_options, direction_count, sync_run_id, updated_at
    )
    select
      program_id, school_id, department_id, program_name, program_code, sort_order, exam_codes,
      degree_options, study_mode_options, direction_count, v_catalog_run_id, now()
    from grouped
    on conflict (id) do update set
      school_id = excluded.school_id,
      department_id = excluded.department_id,
      name = excluded.name,
      code = excluded.code,
      sort_order = excluded.sort_order,
      exam_codes = excluded.exam_codes,
      degree_options = excluded.degree_options,
      study_mode_options = excluded.study_mode_options,
      direction_count = excluded.direction_count,
      sync_run_id = excluded.sync_run_id,
      updated_at = excluded.updated_at;

    with source_rows as (
      select
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-school-' || substr(md5(region || chr(31) || school_name), 1, 16) as school_id,
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-department-' || substr(md5(region || chr(31) || school_name || chr(31) || department_name), 1, 16) as department_id,
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-program-' || substr(md5(region || chr(31) || school_name || chr(31) || department_name || chr(31) || program_name || chr(31) || program_code), 1, 16) as program_id,
        (case when v_catalog_year = '2026' then '' else v_catalog_year || '::' end) ||
          'ops-direction-' || substr(md5(region || chr(31) || school_name || chr(31) || department_name || chr(31) || program_name || chr(31) || program_code || chr(31) || direction_name || chr(31) || tutor || chr(31) || exam_code || chr(31) || degree || chr(31) || study_mode), 1, 16) as direction_id,
        direction_name, tutor, exam_code, degree, study_mode, source_row
      from public.major_catalog_staging_records
      where import_run_id = p_run_id
    )
    insert into public.major_catalog_directions (
      id, school_id, department_id, program_id, name, tutor, exam_code, degree, study_mode,
      sort_order, sync_run_id, updated_at
    )
    select
      direction_id, school_id, department_id, program_id, direction_name, tutor, exam_code, degree,
      study_mode, source_row, v_catalog_run_id, now()
    from source_rows
    on conflict (id) do update set
      school_id = excluded.school_id,
      department_id = excluded.department_id,
      program_id = excluded.program_id,
      name = excluded.name,
      tutor = excluded.tutor,
      exam_code = excluded.exam_code,
      degree = excluded.degree,
      study_mode = excluded.study_mode,
      sort_order = excluded.sort_order,
      sync_run_id = excluded.sync_run_id,
      updated_at = excluded.updated_at;

    update public.major_catalog_import_runs
    set status = 'completed', completed_at = now(), failure_reason = null
    where id = v_catalog_run_id;
    update public.major_catalog_staging_runs
    set status = 'archived'
    where status = 'published' and id <> p_run_id;
    update public.major_catalog_staging_runs
    set status = 'published', published_by = p_actor_id, published_at = now()
    where id = p_run_id;

    return jsonb_build_object('id', p_run_id, 'status', 'published', 'dataset', p_dataset, 'catalog_run_id', v_catalog_run_id);
  end if;

  raise exception 'unsupported dataset: %', p_dataset;
end;
$$;

revoke all on function public.question_admin_portal_publish_import_run(text, uuid, uuid)
  from public, anon, authenticated;
grant execute on function public.question_admin_portal_publish_import_run(text, uuid, uuid)
  to service_role;

alter table public.historical_scoreline_import_runs enable row level security;
alter table public.historical_scoreline_records enable row level security;
alter table public.school_announcement_import_runs enable row level security;
alter table public.school_announcement_records enable row level security;
alter table public.home_content_items enable row level security;
alter table public.major_catalog_staging_runs enable row level security;
alter table public.major_catalog_staging_records enable row level security;

revoke all on table public.historical_scoreline_import_runs from anon, authenticated;
revoke all on table public.historical_scoreline_records from anon, authenticated;
revoke all on table public.school_announcement_import_runs from anon, authenticated;
revoke all on table public.school_announcement_records from anon, authenticated;
revoke all on table public.home_content_items from anon, authenticated;
revoke all on table public.major_catalog_staging_runs from anon, authenticated;
revoke all on table public.major_catalog_staging_records from anon, authenticated;
grant all on table public.historical_scoreline_import_runs to service_role;
grant all on table public.historical_scoreline_records to service_role;
grant all on table public.school_announcement_import_runs to service_role;
grant all on table public.school_announcement_records to service_role;
grant all on table public.home_content_items to service_role;
grant all on table public.major_catalog_staging_runs to service_role;
grant all on table public.major_catalog_staging_records to service_role;
