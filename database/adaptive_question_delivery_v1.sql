-- 港研通个性化出题 V1：学科隔离、题目曝光、能力状态与原子更新基础
-- 执行位置：Supabase SQL Editor
-- 前置依赖：supabase_schema.sql、answer_reliability_and_learning_stats.sql、
--           add_question_learning_tags.sql
--
-- 设计不变量：
--   1. 所有用户能力和学习进度都以 user_id + stats_exam_code + subject 为边界；
--   2. COMMON 只表示题目可复用，用户状态仍按实际 Z001 / Z002 分开；
--   3. user_question_progress 从 user_answers 重建；wrong_questions 只迁移当前仍在
--      错题本中的题，避免已通过复习移除的历史错题复活；
--   4. 自适应状态由 service role 通过原子 RPC 写入，客户端只读自己的数据；
--   5. 标准模拟考试不使用这些个性化题单表。
--   6. 本迁移不把历史正确率粗略映射成 theta；老用户状态需由同版本算法按时间顺序
--      独立重放，或在产品侧显式采用懒校准策略后再开启流量。

begin;

-- 防止重建派生表时有新的作答并发写入。锁只持续到本迁移事务结束。
lock table public.user_answers in share row exclusive mode;
lock table public.wrong_questions in access exclusive mode;
lock table public.user_question_progress in access exclusive mode;

-- ---------------------------------------------------------------------------
-- 一、修复公共题跨考试版本串扰
-- ---------------------------------------------------------------------------

alter table public.wrong_questions
  add column if not exists stats_exam_code text;

alter table public.user_question_progress
  add column if not exists stats_exam_code text;

alter table public.user_answers
  add column if not exists scope_attempt_number integer not null default 1,
  add column if not exists is_first_attempt_in_scope boolean not null default false;

alter table public.user_answers
  drop constraint if exists user_answers_scope_attempt_number_check;
alter table public.user_answers
  add constraint user_answers_scope_attempt_number_check
  check (scope_attempt_number >= 1);

-- wrong_questions 的“是否存在”包含用户通过错题复习移除题目的业务状态，不能只凭
-- 历史上曾经答错来重建。先保存当前活动错题集合；旧表没有作用域时 stats_exam_code
-- 为 null，后续仅把仍活动的题映射到其实际发生过错误的考试版本。
create temporary table adaptive_active_wrong_questions_snapshot
on commit drop
as
select
  user_id,
  question_id,
  stats_exam_code,
  wrong_count,
  last_wrong_at,
  created_at,
  updated_at
from public.wrong_questions;

-- 老约束不允许同一 COMMON 题在 Z001、Z002 各自保留状态，必须先替换。
alter table public.wrong_questions
  drop constraint if exists wrong_questions_user_id_question_id_key;
alter table public.wrong_questions
  drop constraint if exists wrong_questions_user_exam_question_key;
alter table public.user_question_progress
  drop constraint if exists user_question_progress_pkey;

-- progress 是完整作答投影；wrong_questions 则会在清空后按上面的活动集合迁移。
delete from public.wrong_questions;
delete from public.user_question_progress;

alter table public.wrong_questions
  alter column stats_exam_code set not null;
alter table public.wrong_questions
  drop constraint if exists wrong_questions_stats_exam_code_check;
alter table public.wrong_questions
  add constraint wrong_questions_stats_exam_code_check
  check (stats_exam_code in ('Z001', 'Z002'));
alter table public.wrong_questions
  add constraint wrong_questions_user_exam_question_key
  unique (user_id, stats_exam_code, question_id);

alter table public.user_question_progress
  alter column stats_exam_code set not null;
alter table public.user_question_progress
  drop constraint if exists user_question_progress_stats_exam_code_check;
alter table public.user_question_progress
  add constraint user_question_progress_stats_exam_code_check
  check (stats_exam_code in ('Z001', 'Z002'));
alter table public.user_question_progress
  add constraint user_question_progress_pkey
  primary key (user_id, stats_exam_code, question_id);

-- attempt_number / is_first_attempt 继续表达“是否第一次见到这道物理题”，防止
-- COMMON 题在另一个考试版本中因记忆答案被当作全新能力证据。另设 scope 字段
-- 表达该考试版本内的首次作答，并由 scoped progress 表服务版本内学习进度。
with global_ranked as (
  select
    id,
    row_number() over (
      partition by user_id, question_id
      order by created_at asc, id asc
    )::integer as global_attempt_number
  from public.user_answers
)
update public.user_answers answers
set attempt_number = ranked.global_attempt_number,
    is_first_attempt = ranked.global_attempt_number = 1
from global_ranked ranked
where answers.id = ranked.id
  and (
    answers.attempt_number is distinct from ranked.global_attempt_number
    or answers.is_first_attempt is distinct from (ranked.global_attempt_number = 1)
  );

with scoped_ranked as (
  select
    id,
    row_number() over (
      partition by user_id, stats_exam_code, question_id
      order by created_at asc, id asc
    )::integer as next_scope_attempt_number
  from public.user_answers
)
update public.user_answers answers
set scope_attempt_number = ranked.next_scope_attempt_number,
    is_first_attempt_in_scope = ranked.next_scope_attempt_number = 1
from scoped_ranked ranked
where answers.id = ranked.id
  and (
    answers.scope_attempt_number is distinct from ranked.next_scope_attempt_number
    or answers.is_first_attempt_in_scope is distinct from (ranked.next_scope_attempt_number = 1)
  );

insert into public.user_question_progress (
  user_id,
  stats_exam_code,
  question_id,
  first_attempt_is_correct,
  first_answered_at,
  attempt_count,
  correct_count,
  last_is_correct,
  last_answered_at,
  updated_at
)
select
  answers.user_id,
  answers.stats_exam_code,
  answers.question_id,
  (array_agg(answers.is_correct order by answers.created_at asc, answers.id asc))[1],
  min(answers.created_at),
  count(*)::integer,
  count(*) filter (where answers.is_correct)::integer,
  (array_agg(answers.is_correct order by answers.created_at desc, answers.id desc))[1],
  max(answers.created_at),
  max(answers.created_at)
from public.user_answers answers
group by answers.user_id, answers.stats_exam_code, answers.question_id;

-- AI 临时训练题沿用现有行为：参与作答进度，但不进入普通错题本。
-- 这里必须以内存快照中的活动错题为入口，不能从全部历史错误直接重建，否则
-- “答错 -> 在错题复习中答对 -> 已移除”的题会在迁移后复活。
insert into public.wrong_questions (
  user_id,
  stats_exam_code,
  question_id,
  wrong_count,
  last_wrong_at,
  created_at,
  updated_at
)
select
  answers.user_id,
  answers.stats_exam_code,
  answers.question_id,
  count(*)::integer,
  max(answers.created_at),
  min(snapshot.created_at),
  greatest(max(answers.created_at), max(snapshot.updated_at))
from public.user_answers answers
join public.questions questions on questions.id = answers.question_id
join adaptive_active_wrong_questions_snapshot snapshot
  on snapshot.user_id = answers.user_id
 and snapshot.question_id = answers.question_id
 and (
   snapshot.stats_exam_code is null
   or snapshot.stats_exam_code = answers.stats_exam_code
 )
where not answers.is_correct
  and coalesce(questions.source_type, '') <> 'ai_deepseek'
group by answers.user_id, answers.stats_exam_code, answers.question_id;

drop index if exists public.idx_wrong_questions_user_last;
create index idx_wrong_questions_user_last
  on public.wrong_questions (user_id, stats_exam_code, last_wrong_at desc, id desc);

drop index if exists public.idx_user_question_progress_user_updated;
create index idx_user_question_progress_user_updated
  on public.user_question_progress (user_id, stats_exam_code, updated_at desc);

create index if not exists idx_user_answers_user_exam_subject_history
  on public.user_answers (user_id, stats_exam_code, created_at desc, id desc);

create index if not exists idx_user_answers_user_exam_question_created
  on public.user_answers (
    user_id,
    stats_exam_code,
    question_id,
    created_at asc,
    id asc
  );

comment on column public.wrong_questions.stats_exam_code is
  'Actual exam version in which the mistake occurred; COMMON questions remain separated by Z001/Z002.';
comment on column public.user_question_progress.stats_exam_code is
  'Actual exam version for this per-question progress row; never stores COMMON.';
comment on column public.user_answers.is_first_attempt is
  'True only for the first exposure to this physical question across exam versions.';
comment on column public.user_answers.is_first_attempt_in_scope is
  'True for the first answer to this question inside the actual Z001/Z002 statistics scope.';

-- ---------------------------------------------------------------------------
-- 二、V1 用户能力状态
-- ---------------------------------------------------------------------------

create table if not exists public.user_subject_state (
  user_id uuid not null references public.users(id) on delete cascade,
  stats_exam_code text not null check (stats_exam_code in ('Z001', 'Z002')),
  subject text not null check (char_length(btrim(subject)) between 1 and 80),
  theta double precision not null default 0 check (theta between -6 and 6),
  uncertainty double precision not null default 1.6
    check (uncertainty > 0 and uncertainty <= 10),
  effective_evidence double precision not null default 0
    check (effective_evidence >= 0),
  reliable_first_attempt_count integer not null default 0
    check (reliable_first_attempt_count >= 0),
  diagnostic_status text not null default 'NEW'
    check (diagnostic_status in (
      'NEW', 'PROBING', 'VERIFYING', 'CALIBRATING', 'STABLE', 'RECALIBRATING'
    )),
  pending_conflict_count integer not null default 0
    check (pending_conflict_count >= 0),
  state_version bigint not null default 0 check (state_version >= 0),
  model_version text not null default 'theta-shrinkage-v1'
    check (char_length(btrim(model_version)) between 1 and 80),
  last_answered_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, stats_exam_code, subject),
  constraint user_subject_state_exam_subject_check check (
    (stats_exam_code = 'Z001' and subject in ('中华文化', '英语运用', '逻辑推理'))
    or
    (stats_exam_code = 'Z002' and subject in ('中华文化', '英语运用', '数学基础'))
  )
);

create table if not exists public.user_topic_state (
  user_id uuid not null references public.users(id) on delete cascade,
  stats_exam_code text not null check (stats_exam_code in ('Z001', 'Z002')),
  subject text not null check (char_length(btrim(subject)) between 1 and 80),
  module text not null check (char_length(btrim(module)) between 1 and 160),
  submodule text not null check (char_length(btrim(submodule)) between 1 and 160),
  theta double precision not null default 0 check (theta between -6 and 6),
  uncertainty double precision not null default 1.6
    check (uncertainty > 0 and uncertainty <= 10),
  effective_evidence double precision not null default 0
    check (effective_evidence >= 0),
  reliable_first_attempt_count integer not null default 0
    check (reliable_first_attempt_count >= 0),
  pending_conflict_count integer not null default 0
    check (pending_conflict_count >= 0),
  state_version bigint not null default 0 check (state_version >= 0),
  model_version text not null default 'theta-shrinkage-v1'
    check (char_length(btrim(model_version)) between 1 and 80),
  last_answered_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (user_id, stats_exam_code, subject, module, submodule),
  constraint user_topic_state_exam_subject_check check (
    (stats_exam_code = 'Z001' and subject in ('中华文化', '英语运用', '逻辑推理'))
    or
    (stats_exam_code = 'Z002' and subject in ('中华文化', '英语运用', '数学基础'))
  )
);

create index if not exists idx_user_subject_state_scope_updated
  on public.user_subject_state (user_id, stats_exam_code, subject, updated_at desc);

create index if not exists idx_user_topic_state_scope_updated
  on public.user_topic_state (
    user_id,
    stats_exam_code,
    subject,
    updated_at desc
  );

drop trigger if exists set_user_subject_state_updated_at on public.user_subject_state;
create trigger set_user_subject_state_updated_at
before update on public.user_subject_state
for each row execute function public.set_updated_at();

drop trigger if exists set_user_topic_state_updated_at on public.user_topic_state;
create trigger set_user_topic_state_updated_at
before update on public.user_topic_state
for each row execute function public.set_updated_at();

comment on table public.user_subject_state is
  'Adaptive V1 subject-level state, strictly scoped by user + actual exam version + subject.';
comment on table public.user_topic_state is
  'Adaptive V1 module/submodule state; sparse topic evidence shrinks toward the subject state in application logic.';
comment on column public.user_subject_state.state_version is
  'Optimistic concurrency version checked by apply_adaptive_model_update.';

-- ---------------------------------------------------------------------------
-- 三、练习会话与题目曝光链路
-- ---------------------------------------------------------------------------

create table if not exists public.practice_sessions (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  client_session_id text
    check (client_session_id is null or char_length(btrim(client_session_id)) between 1 and 120),
  stats_exam_code text not null check (stats_exam_code in ('Z001', 'Z002')),
  subject text not null check (char_length(btrim(subject)) between 1 and 80),
  mode text not null check (mode in ('comprehensive', 'special')),
  module text,
  submodule text,
  scope_filter jsonb not null default '[]'::jsonb
    check (jsonb_typeof(scope_filter) = 'array'),
  user_preference text not null default 'standard'
    check (user_preference in ('steady', 'standard', 'challenge')),
  status text not null default 'ACTIVE'
    check (status in ('ACTIVE', 'COMPLETED', 'ABANDONED')),
  diagnostic_status text not null default 'NEW'
    check (diagnostic_status in (
      'NEW', 'PROBING', 'VERIFYING', 'CALIBRATING', 'STABLE', 'RECALIBRATING'
    )),
  requested_question_count integer not null check (requested_question_count between 1 and 100),
  strategy_version text not null default 'adaptive-delivery-v1'
    check (char_length(btrim(strategy_version)) between 1 and 80),
  model_version text not null default 'theta-shrinkage-v1'
    check (char_length(btrim(model_version)) between 1 and 80),
  experiment_key text
    check (experiment_key is null or char_length(btrim(experiment_key)) between 1 and 120),
  experiment_group text
    check (experiment_group is null or char_length(btrim(experiment_group)) between 1 and 120),
  state_snapshot jsonb not null default '{}'::jsonb
    check (jsonb_typeof(state_snapshot) = 'object'),
  strategy_config jsonb not null default '{}'::jsonb
    check (jsonb_typeof(strategy_config) = 'object'),
  fallback_reason text,
  started_at timestamptz not null default now(),
  last_activity_at timestamptz not null default now(),
  completed_at timestamptz,
  abandoned_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint practice_sessions_exam_subject_check check (
    (stats_exam_code = 'Z001' and subject in ('中华文化', '英语运用', '逻辑推理'))
    or
    (stats_exam_code = 'Z002' and subject in ('中华文化', '英语运用', '数学基础'))
  ),
  constraint practice_sessions_scope_check check (
    (mode = 'comprehensive' and module is null and submodule is null and scope_filter = '[]'::jsonb)
    or (mode = 'special' and jsonb_array_length(scope_filter) between 1 and 50)
  ),
  constraint practice_sessions_completion_check check (
    (status = 'ACTIVE' and completed_at is null and abandoned_at is null)
    or (status = 'COMPLETED' and completed_at is not null and abandoned_at is null)
    or (status = 'ABANDONED' and abandoned_at is not null and completed_at is null)
  )
);

create unique index if not exists uq_practice_sessions_client_session
  on public.practice_sessions (user_id, client_session_id)
  where client_session_id is not null;

create index if not exists idx_practice_sessions_user_scope_created
  on public.practice_sessions (
    user_id,
    stats_exam_code,
    subject,
    created_at desc
  );

create index if not exists idx_practice_sessions_active
  on public.practice_sessions (user_id, last_activity_at desc)
  where status = 'ACTIVE';

create table if not exists public.practice_session_items (
  id uuid primary key default gen_random_uuid(),
  session_id uuid not null references public.practice_sessions(id) on delete cascade,
  question_id uuid not null references public.questions(id) on delete restrict,
  position integer not null check (position >= 1),
  item_status text not null default 'SELECTED'
    check (item_status in ('SELECTED', 'PRESENTED', 'ANSWERED', 'SKIPPED')),
  selection_reason text not null
    check (char_length(btrim(selection_reason)) between 1 and 120),
  target_zone text not null
    check (target_zone in (
      'diagnostic', 'verify', 'consolidation', 'main', 'challenge', 'coverage'
    )),
  predicted_probability double precision
    check (predicted_probability is null or predicted_probability between 0 and 1),
  theta_before double precision check (theta_before is null or theta_before between -6 and 6),
  item_difficulty double precision
    check (item_difficulty is null or item_difficulty between -6 and 6),
  score_components jsonb not null default '{}'::jsonb
    check (jsonb_typeof(score_components) = 'object'),
  strategy_metadata jsonb not null default '{}'::jsonb
    check (jsonb_typeof(strategy_metadata) = 'object'),
  is_diagnostic boolean not null default false,
  is_challenge boolean not null default false,
  fallback_reason text,
  answer_id uuid references public.user_answers(id) on delete set null,
  adaptive_model_updated_at timestamptz,
  selected_at timestamptz not null default now(),
  presented_at timestamptz,
  answered_at timestamptz,
  skipped_at timestamptz,
  explanation_viewed_at timestamptz,
  exit_observed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (session_id, position),
  unique (session_id, question_id),
  constraint practice_session_items_event_check check (
    (item_status = 'SELECTED' and presented_at is null and answered_at is null and skipped_at is null)
    or (item_status = 'PRESENTED' and presented_at is not null and answered_at is null and skipped_at is null)
    or (item_status = 'ANSWERED' and presented_at is not null and answered_at is not null
      and skipped_at is null and answer_id is not null)
    or (item_status = 'SKIPPED' and presented_at is not null and skipped_at is not null
      and answered_at is null and answer_id is null)
  )
);

alter table public.practice_session_items
  add column if not exists adaptive_model_updated_at timestamptz;

-- The grading/display version selected for an adaptive item is an immutable
-- private fact.  Keep it outside practice_session_items because learners may
-- SELECT their own item rows and the snapshot contains the answer and
-- explanation.  Every claim writes this row in the same transaction as the
-- item, so another API worker (or a restarted worker) grades the exact version
-- that was shown instead of whichever questions row happens to be current.
create table if not exists public.practice_session_item_question_snapshots (
  practice_session_item_id uuid primary key
    references public.practice_session_items(id) on delete cascade,
  question_id uuid not null references public.questions(id) on delete restrict,
  question_snapshot jsonb not null,
  created_at timestamptz not null default now(),
  constraint practice_session_item_question_snapshot_shape_check check (
    jsonb_typeof(question_snapshot) = 'object'
    and question_snapshot->>'id' = question_id::text
    and jsonb_typeof(question_snapshot->'answer') = 'string'
    and question_snapshot->>'answer' in ('A', 'B', 'C', 'D')
  )
);

create index if not exists idx_practice_item_question_snapshots_question
  on public.practice_session_item_question_snapshots (question_id, created_at desc);

-- This migration has not been released yet, but keep reruns/rolling test
-- environments deterministic.  For an item created by an older draft, the
-- current row is the only recoverable baseline at migration time.
insert into public.practice_session_item_question_snapshots (
  practice_session_item_id,
  question_id,
  question_snapshot,
  created_at
)
select
  item.id,
  item.question_id,
  to_jsonb(question_row),
  item.selected_at
from public.practice_session_items item
join public.questions question_row on question_row.id = item.question_id
on conflict (practice_session_item_id) do nothing;

create unique index if not exists uq_practice_session_items_answer
  on public.practice_session_items (answer_id)
  where answer_id is not null;

create index if not exists idx_practice_session_items_session_position
  on public.practice_session_items (session_id, position);

create index if not exists idx_practice_session_items_question_selected
  on public.practice_session_items (question_id, selected_at desc);

create index if not exists idx_practice_session_items_unanswered_exposure
  on public.practice_session_items (session_id, presented_at desc)
  where item_status = 'PRESENTED';

-- The compensation barrier walks answered items in chronological order and
-- anti-joins the authoritative adaptive_model_updates row by answer_id.  Do
-- not predicate this index on the denormalized marker: a missing audit row must
-- remain discoverable even if that marker is ever stale.
create index if not exists idx_practice_session_items_answered_audit_barrier
  on public.practice_session_items (session_id, answered_at, id)
  include (answer_id, question_id, position)
  where answer_id is not null;

create index if not exists idx_practice_session_items_open_verification_slot
  on public.practice_session_items (
    (lower(strategy_metadata->>'verification_conflict_id')),
    ((strategy_metadata->>'verification_expected_count'))
  )
  where target_zone = 'verify'
    and answer_id is null
    and item_status in ('SELECTED', 'PRESENTED')
    and not (strategy_metadata @> '{"verification_slot_expired": true}'::jsonb);

create index if not exists idx_practice_session_items_verification_lease
  on public.practice_session_items ((coalesce(presented_at, selected_at)))
  where target_zone = 'verify'
    and answer_id is null
    and item_status in ('SELECTED', 'PRESENTED');

drop trigger if exists set_practice_sessions_updated_at on public.practice_sessions;
create trigger set_practice_sessions_updated_at
before update on public.practice_sessions
for each row execute function public.set_updated_at();

drop trigger if exists set_practice_session_items_updated_at on public.practice_session_items;
create trigger set_practice_session_items_updated_at
before update on public.practice_session_items
for each row execute function public.set_updated_at();

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
    -- admin_management.sql adds questions.status. Converting the composite row
    -- to JSON keeps this migration compatible with a minimal prerequisite
    -- schema while enforcing active-only selection whenever the column exists.
    if coalesce(to_jsonb(question_row)->>'status', 'active') <> 'active' then
      raise exception 'adaptive_question_not_active';
    end if;

    -- Candidate ranking may come from the short process cache, but the item
    -- difficulty and quality evidence persisted here must match the locked
    -- question/calibration state at the claim transaction's linearization point.
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

drop trigger if exists validate_practice_session_item_scope
  on public.practice_session_items;
create trigger validate_practice_session_item_scope
before insert or update of session_id, question_id, position
on public.practice_session_items
for each row execute function public.validate_practice_session_item_scope();

create or replace function public.guard_practice_session_scope_immutable()
returns trigger
language plpgsql
set search_path = public, pg_temp
as $$
begin
  if new.user_id is distinct from old.user_id
     or new.stats_exam_code is distinct from old.stats_exam_code
     or new.subject is distinct from old.subject
     or new.mode is distinct from old.mode
     or new.module is distinct from old.module
     or new.submodule is distinct from old.submodule
     or new.scope_filter is distinct from old.scope_filter
     or new.requested_question_count is distinct from old.requested_question_count
     or new.strategy_version is distinct from old.strategy_version
     or new.model_version is distinct from old.model_version then
    raise exception 'adaptive_session_scope_immutable';
  end if;
  return new;
end;
$$;

drop trigger if exists guard_practice_session_scope_immutable
  on public.practice_sessions;
create trigger guard_practice_session_scope_immutable
before update of user_id, stats_exam_code, subject, mode, module, submodule,
  scope_filter, requested_question_count, strategy_version, model_version
on public.practice_sessions
for each row execute function public.guard_practice_session_scope_immutable();

revoke all on function public.validate_practice_session_item_scope()
  from public, anon, authenticated, service_role;
revoke all on function public.guard_practice_session_scope_immutable()
  from public, anon, authenticated;

comment on table public.practice_sessions is
  'One adaptive practice run within one immutable exam-version and subject scope.';
comment on table public.practice_session_items is
  'Selection and exposure log; SELECTED is distinct from actually PRESENTED, ANSWERED, SKIPPED or exit-observed.';
comment on table public.practice_session_item_question_snapshots is
  'Service-only immutable question version used to display and grade one claimed adaptive item.';
comment on column public.practice_session_item_question_snapshots.question_snapshot is
  'Full locked questions row at claim time, including private answer and explanation fields.';
comment on column public.practice_session_items.score_components is
  'Normalized scoring factors used when the item was selected; retained for replay and experiments.';
comment on column public.practice_session_items.adaptive_model_updated_at is
  'Hot-path completion marker written atomically with the immutable adaptive_model_updates audit row.';

-- ---------------------------------------------------------------------------
-- 四、题目校准与可审计的模型更新
-- ---------------------------------------------------------------------------

create table if not exists public.question_calibration (
  question_id uuid not null references public.questions(id) on delete cascade,
  stats_exam_code text not null check (stats_exam_code in ('Z001', 'Z002')),
  item_difficulty double precision check (item_difficulty is null or item_difficulty between -6 and 6),
  difficulty_uncertainty double precision
    check (difficulty_uncertainty is null or (difficulty_uncertainty > 0 and difficulty_uncertainty <= 10)),
  discrimination double precision
    check (discrimination is null or (discrimination > 0 and discrimination <= 5)),
  reliable_attempt_count integer not null default 0 check (reliable_attempt_count >= 0),
  reliable_correct_count integer not null default 0 check (reliable_correct_count >= 0),
  empirical_accuracy double precision
    check (empirical_accuracy is null or empirical_accuracy between 0 and 1),
  quality_weight double precision not null default 0.7 check (quality_weight between 0 and 1),
  quality_status text not null default 'UNREVIEWED'
    check (quality_status in ('UNREVIEWED', 'APPROVED', 'FLAGGED', 'EXCLUDED')),
  is_diagnostic_candidate boolean not null default false,
  diagnostic_priority integer not null default 0 check (diagnostic_priority between 0 and 100),
  diagnostic_review_notes text,
  reviewed_by uuid references public.users(id) on delete set null,
  reviewed_at timestamptz,
  model_version text not null default 'adaptive-v1'
    check (char_length(btrim(model_version)) between 1 and 80),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (question_id, stats_exam_code),
  constraint question_calibration_counts_check
    check (reliable_correct_count <= reliable_attempt_count),
  constraint question_calibration_review_check
    check (not is_diagnostic_candidate or quality_status = 'APPROVED')
);

create index if not exists idx_question_calibration_diagnostic_pool
  on public.question_calibration (
    stats_exam_code,
    diagnostic_priority desc,
    question_id
  )
  where is_diagnostic_candidate and quality_status = 'APPROVED';

create index if not exists idx_question_calibration_quality
  on public.question_calibration (stats_exam_code, quality_status, updated_at desc);

drop trigger if exists set_question_calibration_updated_at on public.question_calibration;
create trigger set_question_calibration_updated_at
before update on public.question_calibration
for each row execute function public.set_updated_at();

create table if not exists public.adaptive_model_updates (
  id uuid primary key default gen_random_uuid(),
  answer_id uuid not null references public.user_answers(id) on delete cascade,
  practice_session_item_id uuid references public.practice_session_items(id) on delete set null,
  user_id uuid not null references public.users(id) on delete cascade,
  stats_exam_code text not null check (stats_exam_code in ('Z001', 'Z002')),
  subject text not null,
  module text not null,
  submodule text not null,
  model_version text not null check (char_length(btrim(model_version)) between 1 and 80),
  predicted_probability double precision not null check (predicted_probability between 0 and 1),
  evidence_weight double precision not null check (evidence_weight between 0 and 1),
  item_difficulty double precision not null check (item_difficulty between -6 and 6),
  actual_correct boolean not null,
  subject_state_version_before bigint not null check (subject_state_version_before >= 0),
  subject_state_version_after bigint not null check (subject_state_version_after >= 1),
  subject_theta_before double precision not null,
  subject_theta_after double precision not null,
  subject_delta_theta double precision not null,
  subject_uncertainty_before double precision not null,
  subject_uncertainty_after double precision not null,
  topic_state_version_before bigint not null check (topic_state_version_before >= 0),
  topic_state_version_after bigint not null check (topic_state_version_after >= 1),
  topic_theta_before double precision not null,
  topic_theta_after double precision not null,
  topic_delta_theta double precision not null,
  topic_uncertainty_before double precision not null,
  topic_uncertainty_after double precision not null,
  diagnostic_status_before text not null,
  diagnostic_status_after text not null,
  pending_conflict_count_before integer not null check (pending_conflict_count_before >= 0),
  pending_conflict_count_after integer not null check (pending_conflict_count_after >= 0),
  update_reason text not null check (char_length(btrim(update_reason)) between 1 and 120),
  update_payload jsonb not null default '{}'::jsonb
    check (jsonb_typeof(update_payload) = 'object'),
  created_at timestamptz not null default now(),
  unique (answer_id),
  constraint adaptive_model_updates_scope_check check (
    (stats_exam_code = 'Z001' and subject in ('中华文化', '英语运用', '逻辑推理'))
    or
    (stats_exam_code = 'Z002' and subject in ('中华文化', '英语运用', '数学基础'))
  ),
  constraint adaptive_model_updates_version_transition_check check (
    subject_state_version_after = subject_state_version_before + 1
    and topic_state_version_after = topic_state_version_before + 1
  ),
  constraint adaptive_model_updates_delta_check check (
    abs(subject_delta_theta - (subject_theta_after - subject_theta_before)) <= 0.0000001
    and abs(topic_delta_theta - (topic_theta_after - topic_theta_before)) <= 0.0000001
  ),
  constraint adaptive_model_updates_uncertainty_check check (
    subject_uncertainty_before > 0
    and subject_uncertainty_after > 0
    and topic_uncertainty_before > 0
    and topic_uncertainty_after > 0
  )
);

create index if not exists idx_adaptive_model_updates_user_scope_created
  on public.adaptive_model_updates (
    user_id,
    stats_exam_code,
    subject,
    created_at desc
  );

create index if not exists idx_adaptive_model_updates_session_item
  on public.adaptive_model_updates (practice_session_item_id)
  where practice_session_item_id is not null;

-- Reconcile the denormalized marker in both directions before installing its
-- maintenance trigger.  The audit row is always the final source of truth.
update public.practice_session_items item
set adaptive_model_updated_at = null
where item.adaptive_model_updated_at is not null
  and not exists (
    select 1
    from public.adaptive_model_updates model_update
    where model_update.answer_id = item.answer_id
  );

update public.practice_session_items item
set adaptive_model_updated_at = model_update.created_at
from public.adaptive_model_updates model_update
where model_update.answer_id = item.answer_id
  and item.answer_id is not null
  and item.adaptive_model_updated_at is distinct from model_update.created_at;

create or replace function public.sync_adaptive_model_update_marker()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  if tg_op in ('DELETE', 'UPDATE') then
    update public.practice_session_items item
    set adaptive_model_updated_at = null
    where (
        item.answer_id = old.answer_id
        or item.id = old.practice_session_item_id
      )
      and not exists (
        select 1
        from public.adaptive_model_updates remaining_update
        where remaining_update.answer_id = item.answer_id
      );
  end if;

  if tg_op in ('INSERT', 'UPDATE') then
    update public.practice_session_items item
    set adaptive_model_updated_at = new.created_at
    where item.answer_id = new.answer_id
      and item.adaptive_model_updated_at is distinct from new.created_at;
  end if;

  if tg_op = 'DELETE' then
    return old;
  end if;
  return new;
end;
$$;

drop trigger if exists sync_adaptive_model_update_marker
  on public.adaptive_model_updates;
create trigger sync_adaptive_model_update_marker
after insert or update or delete on public.adaptive_model_updates
for each row execute function public.sync_adaptive_model_update_marker();

revoke all on function public.sync_adaptive_model_update_marker()
  from public, anon, authenticated;

comment on table public.question_calibration is
  'Per-question empirical parameters by actual exam population; COMMON questions may have separate Z001 and Z002 rows.';
comment on table public.adaptive_model_updates is
  'Immutable audit row for the one production adaptive update attributable to an answer.';

create table if not exists public.adaptive_conflicts (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  stats_exam_code text not null check (stats_exam_code in ('Z001', 'Z002')),
  subject text not null,
  module text not null,
  submodule text not null,
  question_type text not null default 'single_choice',
  low_question_id uuid not null references public.questions(id) on delete restrict,
  high_question_id uuid not null references public.questions(id) on delete restrict,
  status text not null default 'PENDING'
    check (status in ('PENDING', 'RESOLVED', 'DEFERRED', 'CANCELLED')),
  verification_count integer not null default 0 check (verification_count between 0 and 20),
  resolution text,
  opened_at timestamptz not null default now(),
  resolved_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint adaptive_conflicts_distinct_questions_check
    check (low_question_id <> high_question_id),
  constraint adaptive_conflicts_resolution_check check (
    (status = 'PENDING' and resolved_at is null and resolution is null)
    or (
      status <> 'PENDING'
      and resolved_at is not null
      and resolution is not null
      and char_length(btrim(resolution)) between 1 and 240
    )
  ),
  constraint adaptive_conflicts_question_type_check
    check (char_length(btrim(question_type)) between 1 and 80),
  constraint adaptive_conflicts_scope_check check (
    (stats_exam_code = 'Z001' and subject in ('中华文化', '英语运用', '逻辑推理'))
    or
    (stats_exam_code = 'Z002' and subject in ('中华文化', '英语运用', '数学基础'))
  )
);

-- Keep the migration repeatable if an earlier draft of this V1 table already
-- exists in a non-production environment.
alter table public.adaptive_conflicts
  drop constraint if exists adaptive_conflicts_resolution_check;
alter table public.adaptive_conflicts
  add constraint adaptive_conflicts_resolution_check check (
    (status = 'PENDING' and resolved_at is null and resolution is null)
    or (
      status <> 'PENDING'
      and resolved_at is not null
      and resolution is not null
      and char_length(btrim(resolution)) between 1 and 240
    )
  );
alter table public.adaptive_conflicts
  drop constraint if exists adaptive_conflicts_question_type_check;
alter table public.adaptive_conflicts
  add constraint adaptive_conflicts_question_type_check
  check (char_length(btrim(question_type)) between 1 and 80);

create unique index if not exists uq_adaptive_conflicts_pending_pair
  on public.adaptive_conflicts (
    user_id, stats_exam_code, subject, low_question_id, high_question_id
  )
  where status = 'PENDING';

create index if not exists idx_adaptive_conflicts_pending_scope
  on public.adaptive_conflicts (
    user_id, stats_exam_code, subject, opened_at
  )
  where status = 'PENDING';

drop trigger if exists set_adaptive_conflicts_updated_at on public.adaptive_conflicts;
create trigger set_adaptive_conflicts_updated_at
before update on public.adaptive_conflicts
for each row execute function public.set_updated_at();

comment on table public.adaptive_conflicts is
  'Auditable low-wrong/high-correct pairs awaiting interleaved parallel-item verification.';

-- ---------------------------------------------------------------------------
-- 五、行级权限：客户端只读自己的安全状态/会话，内部审计仅限 service role
-- ---------------------------------------------------------------------------

alter table public.user_subject_state enable row level security;
alter table public.user_topic_state enable row level security;
alter table public.practice_sessions enable row level security;
alter table public.practice_session_items enable row level security;
alter table public.practice_session_item_question_snapshots enable row level security;
alter table public.question_calibration enable row level security;
alter table public.adaptive_model_updates enable row level security;
alter table public.adaptive_conflicts enable row level security;

drop policy if exists "users can read own subject state" on public.user_subject_state;
create policy "users can read own subject state"
  on public.user_subject_state for select
  using (auth.uid() = user_id);

drop policy if exists "users can read own topic state" on public.user_topic_state;
create policy "users can read own topic state"
  on public.user_topic_state for select
  using (auth.uid() = user_id);

drop policy if exists "users can read own practice sessions" on public.practice_sessions;
create policy "users can read own practice sessions"
  on public.practice_sessions for select
  using (auth.uid() = user_id);

drop policy if exists "users can read own practice session items" on public.practice_session_items;
create policy "users can read own practice session items"
  on public.practice_session_items for select
  using (
    exists (
      select 1
      from public.practice_sessions sessions
      where sessions.id = practice_session_items.session_id
        and sessions.user_id = auth.uid()
    )
  );

drop policy if exists "users can read own adaptive model updates" on public.adaptive_model_updates;
drop policy if exists "users can read own adaptive conflicts" on public.adaptive_conflicts;

-- Model deltas and probabilistic conflict reasons are internal audit data.
-- Product clients receive only a safe status/count summary from the backend.

-- Empirical item parameters are an internal recommendation input. They are
-- intentionally not exposed directly to authenticated clients.
revoke all on table public.question_calibration from anon, authenticated;
revoke insert, update, delete on table public.user_subject_state from anon, authenticated;
revoke insert, update, delete on table public.user_topic_state from anon, authenticated;
revoke insert, update, delete on table public.practice_sessions from anon, authenticated;
revoke insert, update, delete on table public.practice_session_items from anon, authenticated;
revoke all on table public.practice_session_item_question_snapshots from public, anon, authenticated;
revoke all on table public.adaptive_model_updates from anon, authenticated;
revoke all on table public.adaptive_conflicts from anon, authenticated;

grant select on table public.user_subject_state to authenticated;
grant select on table public.user_topic_state to authenticated;
grant select on table public.practice_sessions to authenticated;
grant select on table public.practice_session_items to authenticated;

grant select, insert, update, delete on table public.user_subject_state to service_role;
grant select, insert, update, delete on table public.user_topic_state to service_role;
grant select, insert, update, delete on table public.practice_sessions to service_role;
grant select, insert, update, delete on table public.practice_session_items to service_role;
grant select on table public.practice_session_item_question_snapshots to service_role;
grant select, insert, update, delete on table public.question_calibration to service_role;
grant select, insert, update, delete on table public.adaptive_model_updates to service_role;
grant select, insert, update, delete on table public.adaptive_conflicts to service_role;

-- ---------------------------------------------------------------------------
-- 六、按实际考试版本维护题目进度
-- ---------------------------------------------------------------------------

drop trigger if exists sync_user_answer_progress_after_owner_change
  on public.user_answers;
drop function if exists public.sync_user_answer_progress_after_owner_change();
drop function if exists public.refresh_user_question_progress(uuid, uuid, timestamptz);

create or replace function public.refresh_user_question_progress(
  p_user_id uuid,
  p_stats_exam_code text,
  p_question_id uuid,
  p_now timestamptz default now()
)
returns void
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  answer_count integer;
  answer_correct_count integer;
  first_correct boolean;
  first_at timestamptz;
  last_correct boolean;
  last_at timestamptz;
begin
  if p_user_id is null or p_question_id is null
     or p_stats_exam_code not in ('Z001', 'Z002') then
    return;
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(
      p_user_id::text || ':' || p_stats_exam_code || ':' || p_question_id::text,
      0
    )
  );
  perform pg_advisory_xact_lock(
    hashtextextended(p_user_id::text || ':' || p_question_id::text, 0)
  );

  -- Preserve the global physical-question attempt facts.
  with ranked as (
    select
      id,
      row_number() over (order by created_at asc, id asc)::integer as next_attempt_number
    from public.user_answers
    where user_id = p_user_id and question_id = p_question_id
  )
  update public.user_answers answers
  set attempt_number = ranked.next_attempt_number,
      is_first_attempt = ranked.next_attempt_number = 1
  from ranked
  where answers.id = ranked.id
    and (
      answers.attempt_number is distinct from ranked.next_attempt_number
      or answers.is_first_attempt is distinct from (ranked.next_attempt_number = 1)
    );

  -- Scope-local attempt facts support Z001/Z002 progress without pretending a
  -- previously seen COMMON item is a new psychometric observation.
  with ranked as (
    select
      id,
      row_number() over (order by created_at asc, id asc)::integer as next_scope_attempt_number
    from public.user_answers
    where user_id = p_user_id
      and stats_exam_code = p_stats_exam_code
      and question_id = p_question_id
  )
  update public.user_answers answers
  set scope_attempt_number = ranked.next_scope_attempt_number,
      is_first_attempt_in_scope = ranked.next_scope_attempt_number = 1
  from ranked
  where answers.id = ranked.id
    and (
      answers.scope_attempt_number is distinct from ranked.next_scope_attempt_number
      or answers.is_first_attempt_in_scope is distinct from (ranked.next_scope_attempt_number = 1)
    );

  select
    count(*)::integer,
    count(*) filter (where is_correct)::integer,
    (array_agg(is_correct order by created_at asc, id asc))[1],
    min(created_at),
    (array_agg(is_correct order by created_at desc, id desc))[1],
    max(created_at)
  into
    answer_count,
    answer_correct_count,
    first_correct,
    first_at,
    last_correct,
    last_at
  from public.user_answers
  where user_id = p_user_id
    and stats_exam_code = p_stats_exam_code
    and question_id = p_question_id;

  if answer_count = 0 then
    delete from public.user_question_progress
    where user_id = p_user_id
      and stats_exam_code = p_stats_exam_code
      and question_id = p_question_id;
    return;
  end if;

  insert into public.user_question_progress (
    user_id,
    stats_exam_code,
    question_id,
    first_attempt_is_correct,
    first_answered_at,
    attempt_count,
    correct_count,
    last_is_correct,
    last_answered_at,
    updated_at
  ) values (
    p_user_id,
    p_stats_exam_code,
    p_question_id,
    first_correct,
    first_at,
    answer_count,
    answer_correct_count,
    last_correct,
    last_at,
    p_now
  )
  on conflict (user_id, stats_exam_code, question_id) do update
  set first_attempt_is_correct = excluded.first_attempt_is_correct,
      first_answered_at = excluded.first_answered_at,
      attempt_count = excluded.attempt_count,
      correct_count = excluded.correct_count,
      last_is_correct = excluded.last_is_correct,
      last_answered_at = excluded.last_answered_at,
      updated_at = excluded.updated_at;
end;
$$;

revoke all on function public.refresh_user_question_progress(uuid, text, uuid, timestamptz)
  from public, anon, authenticated;
grant execute on function public.refresh_user_question_progress(uuid, text, uuid, timestamptz)
  to service_role;

create or replace function public.sync_user_answer_progress_after_scope_change()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  perform public.refresh_user_question_progress(
    old.user_id,
    old.stats_exam_code,
    old.question_id,
    now()
  );
  if new.user_id is distinct from old.user_id
     or new.stats_exam_code is distinct from old.stats_exam_code
     or new.question_id is distinct from old.question_id then
    perform public.refresh_user_question_progress(
      new.user_id,
      new.stats_exam_code,
      new.question_id,
      now()
    );
  end if;
  return new;
end;
$$;

drop trigger if exists sync_user_answer_progress_after_scope_change
  on public.user_answers;
create trigger sync_user_answer_progress_after_scope_change
after update of user_id, stats_exam_code, question_id on public.user_answers
for each row execute function public.sync_user_answer_progress_after_scope_change();

-- Resolve an adaptive grading snapshot without exposing the private snapshot
-- table to the authenticated client role.  The API calls this only on a
-- process-cache miss; ownership and question identity are checked together.
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

revoke all on function public.get_adaptive_question_snapshot(uuid, uuid, uuid)
  from public, anon, authenticated;
grant execute on function public.get_adaptive_question_snapshot(uuid, uuid, uuid)
  to service_role;
comment on function public.get_adaptive_question_snapshot(uuid, uuid, uuid) is
  'Returns one owner-validated private claim-time question snapshot to the backend service role.';

-- ---------------------------------------------------------------------------
-- 七、替换作答 RPC：保留原接口签名，同时按版本维护进度和错题
-- ---------------------------------------------------------------------------

-- The adaptive item id is appended after the historical p_now argument so all
-- existing positional calls retain their meaning. Drop both possible signatures
-- to keep reruns deterministic and avoid ambiguous PostgREST overload resolution.
drop function if exists public.record_answer_submission(
  uuid, uuid, text, text, boolean, integer, text, text, text, text, boolean, timestamptz, uuid,
  text, uuid, text, text
);
drop function if exists public.record_answer_submission(
  uuid, uuid, text, text, boolean, integer, text, text, text, text, boolean, timestamptz, uuid
);
drop function if exists public.record_answer_submission(
  uuid, uuid, text, text, boolean, integer, text, text, text, text, boolean, timestamptz
);

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
as $$
declare
  normalized_client_id text := nullif(btrim(coalesce(p_client_submission_id, '')), '');
  existing_answer public.user_answers%rowtype;
  progress_row public.user_question_progress%rowtype;
  stats_row public.ability_stats%rowtype;
  question_row public.questions%rowtype;
  grading_snapshot jsonb;
  comprehensive_manifest jsonb;
  comprehensive_answer_entry jsonb;
  practice_session_row public.practice_sessions%rowtype;
  practice_item_row public.practice_session_items%rowtype;
  global_attempt_count integer;
  global_first_attempt boolean;
  next_attempt_number integer;
  scope_first_attempt boolean;
  next_scope_attempt_number integer;
  resolved_exam_code text;
  resolved_is_correct boolean;
  resolved_is_ai_generated boolean;
  normalized_submission_kind text := lower(btrim(coalesce(p_submission_kind, '')));
  normalized_comprehensive_client_id text := nullif(
    btrim(coalesce(p_comprehensive_client_submission_id, '')),
    ''
  );
begin
  if p_user_id is null or p_question_id is null then
    raise exception 'answer_submission_invalid_identity';
  end if;
  if p_selected_answer is null or p_selected_answer not in ('A', 'B', 'C', 'D') then
    raise exception 'answer_submission_invalid_option';
  end if;
  if p_used_time is null or p_used_time not between 0 and 86400 then
    raise exception 'answer_submission_invalid_time';
  end if;
  if p_exam_code is null or p_exam_code not in ('Z001', 'Z002') then
    raise exception 'answer_submission_invalid_exam_code';
  end if;
  if p_now is null then
    raise exception 'answer_submission_invalid_timepoint';
  end if;
  if p_practice_session_item_id is not null and normalized_client_id is null then
    raise exception 'adaptive_answer_requires_client_submission_id';
  end if;
  if normalized_submission_kind not in ('single', 'comprehensive_batch') then
    raise exception 'answer_submission_kind_invalid';
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
    select * into question_row
    from public.questions
    where id = p_question_id;
    if not found then
      raise exception 'answer_submission_question_not_found';
    end if;
  else
    -- An adaptive answer is graded against the immutable claim-time version,
    -- not the mutable master question row.  Join through the owning session so
    -- a caller cannot use another learner's item as an answer oracle.
    select snapshot.question_snapshot
    into grading_snapshot
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

    select populated.* into question_row
    from jsonb_populate_record(
      null::public.questions,
      grading_snapshot
    ) populated;
    if question_row.id is distinct from p_question_id
       or question_row.answer not in ('A', 'B', 'C', 'D') then
      raise exception 'adaptive_question_snapshot_invalid';
    end if;
  end if;

  resolved_exam_code := case
    when question_row.subject in ('中华文化', '英语运用') then p_exam_code
    when question_row.exam_code in ('Z001', 'Z002') then question_row.exam_code
    else p_exam_code
  end;
  resolved_is_correct := p_selected_answer = question_row.answer;
  resolved_is_ai_generated := coalesce(question_row.source_type, '') = 'ai_deepseek';
  if question_row.exam_code not in ('COMMON', resolved_exam_code)
     or (question_row.exam_code = 'COMMON' and question_row.subject not in ('中华文化', '英语运用'))
     or not (
       (resolved_exam_code = 'Z001' and question_row.subject in ('中华文化', '英语运用', '逻辑推理'))
       or
       (resolved_exam_code = 'Z002' and question_row.subject in ('中华文化', '英语运用', '数学基础'))
     ) then
    raise exception 'answer_submission_scope_mismatch';
  end if;

  -- Serialize every theta-relevant write inside one user/exam/subject scope.
  perform pg_advisory_xact_lock(
    hashtextextended(
      p_user_id::text || ':' || resolved_exam_code || ':' || question_row.subject,
      0
    )
  );
  perform pg_advisory_xact_lock(
    hashtextextended(p_user_id::text || ':' || p_question_id::text, 0)
  );

  if p_practice_session_item_id is null then
    if normalized_submission_kind <> 'single' then
      raise exception 'adaptive_comprehensive_submission_state_invalid';
    end if;
    -- A caller already knows the physical question id and must not bypass the
    -- batch channel merely by omitting practice_session_item_id.
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
  end if;

  if p_practice_session_item_id is not null then
    -- Match the lock order used by the other adaptive RPCs: scope advisory lock,
    -- then session row, then session-item row.
    select sessions.* into practice_session_row
    from public.practice_sessions sessions
    join public.practice_session_items items on items.session_id = sessions.id
    where items.id = p_practice_session_item_id
      and sessions.user_id = p_user_id
    for update of sessions;
    if not found then
      raise exception 'adaptive_session_not_found';
    end if;

    select * into practice_item_row
    from public.practice_session_items
    where id = p_practice_session_item_id
      and session_id = practice_session_row.id
    for update;
    if not found then
      raise exception 'adaptive_session_item_not_found';
    end if;
    if practice_item_row.question_id <> p_question_id
       or practice_session_row.stats_exam_code <> resolved_exam_code
       or practice_session_row.subject <> question_row.subject then
      raise exception 'adaptive_scope_mismatch';
    end if;

    if practice_session_row.mode = 'comprehensive' then
      if normalized_submission_kind <> 'comprehensive_batch'
         or p_comprehensive_session_id is distinct from practice_session_row.id then
        raise exception 'adaptive_comprehensive_batch_required';
      end if;
      comprehensive_manifest := practice_session_row.strategy_config->'comprehensive_submission';
      if jsonb_typeof(comprehensive_manifest) is distinct from 'object'
         or comprehensive_manifest->>'client_submission_id'
              <> normalized_comprehensive_client_id
         or comprehensive_manifest->>'manifest_hash'
              <> p_comprehensive_manifest_hash
         or upper(coalesce(comprehensive_manifest->>'phase', ''))
              not in ('LOCKED', 'COMPLETED')
         or jsonb_typeof(comprehensive_manifest->'answers') is distinct from 'array'
         or not (
           (upper(comprehensive_manifest->>'phase') = 'LOCKED'
             and practice_session_row.status = 'ACTIVE')
           or
           (upper(comprehensive_manifest->>'phase') = 'COMPLETED'
             and practice_session_row.status = 'COMPLETED')
         ) then
        raise exception 'adaptive_comprehensive_submission_state_invalid';
      end if;

      select value into comprehensive_answer_entry
      from jsonb_array_elements(comprehensive_manifest->'answers') answer_entry(value)
      where value->>'practice_session_item_id' = p_practice_session_item_id::text
        and (value->>'position')::integer = practice_item_row.position
      limit 1;
      if not found
         or comprehensive_answer_entry->'selected_answer' = 'null'::jsonb
         or comprehensive_answer_entry->>'selected_answer' <> p_selected_answer
         or (comprehensive_answer_entry->>'used_time')::integer <> p_used_time
         or comprehensive_answer_entry->>'client_submission_id' <> normalized_client_id then
        raise exception 'adaptive_comprehensive_answer_manifest_mismatch';
      end if;
    elsif normalized_submission_kind <> 'single' then
      raise exception 'adaptive_comprehensive_submission_state_invalid';
    end if;

    if practice_item_row.item_status = 'SKIPPED' then
      raise exception 'adaptive_session_item_already_skipped';
    end if;
  end if;

  if normalized_client_id is not null then
    perform pg_advisory_xact_lock(
      hashtextextended(p_user_id::text || ':submission:' || normalized_client_id, 0)
    );
    select *
    into existing_answer
    from public.user_answers
    where user_id = p_user_id
      and client_submission_id = normalized_client_id
    for update;

    if found then
      if existing_answer.question_id <> p_question_id
         or existing_answer.selected_answer <> p_selected_answer
         or existing_answer.used_time <> p_used_time
         or existing_answer.stats_exam_code <> resolved_exam_code
         or existing_answer.is_correct <> resolved_is_correct then
        raise exception 'answer_submission_conflict';
      end if;

      select * into progress_row
      from public.user_question_progress
      where user_id = p_user_id
        and stats_exam_code = resolved_exam_code
        and question_id = p_question_id;

      select * into stats_row
      from public.ability_stats
      where user_id = p_user_id
        and exam_code = resolved_exam_code
        and subject = question_row.subject
        and module = question_row.module
        and submodule = question_row.submodule;

      if p_practice_session_item_id is not null then
        -- Use the durable answer timestamp on an idempotent retry.  A network
        -- delay must not turn an originally timely answer into a late one.
        if practice_item_row.target_zone = 'verify'
           and practice_item_row.item_status in ('SELECTED', 'PRESENTED')
           and practice_item_row.answer_id is null
           and not (
             practice_item_row.strategy_metadata
               @> '{"verification_slot_expired": true}'::jsonb
           )
           and coalesce(
             practice_item_row.presented_at,
             practice_item_row.selected_at
           ) <= existing_answer.created_at - interval '15 minutes' then
          update public.practice_session_items
          set strategy_metadata = strategy_metadata || jsonb_build_object(
                'verification_slot_expired', true,
                'verification_slot_expired_at', existing_answer.created_at,
                'verification_slot_lease_seconds', 900
              ),
              updated_at = p_now
          where id = p_practice_session_item_id
          returning * into practice_item_row;
        end if;

        if practice_item_row.answer_id is null
           and practice_session_row.status <> 'ACTIVE'
           and not (
             practice_item_row.strategy_metadata
               @> '{"verification_slot_expired": true}'::jsonb
           ) then
          raise exception 'adaptive_session_not_active';
        end if;
        if practice_item_row.answer_id is not null
           and practice_item_row.answer_id <> existing_answer.id then
          raise exception 'adaptive_session_item_answer_conflict';
        end if;
        if exists (
          select 1
          from public.practice_session_items other_item
          where other_item.answer_id = existing_answer.id
            and other_item.id <> p_practice_session_item_id
        ) then
          raise exception 'adaptive_answer_already_attached';
        end if;
        update public.practice_session_items
        set item_status = 'ANSWERED',
            presented_at = coalesce(presented_at, existing_answer.created_at),
            answered_at = coalesce(answered_at, existing_answer.created_at),
            answer_id = existing_answer.id,
            adaptive_model_updated_at = case
              when answer_id = existing_answer.id then adaptive_model_updated_at
              else null
            end,
            updated_at = p_now
        where id = p_practice_session_item_id;
        update public.practice_sessions
        set last_activity_at = p_now,
            updated_at = p_now
        where id = practice_session_row.id;
      end if;

      return jsonb_build_object(
        'submission_id', existing_answer.id,
        'client_submission_id', existing_answer.client_submission_id,
        'stats_exam_code', existing_answer.stats_exam_code,
        'idempotent', true,
        'persisted', true,
        'selected_answer', existing_answer.selected_answer,
        'correct_answer', question_row.answer,
        'is_correct', existing_answer.is_correct,
        'explanation', question_row.explanation,
        'added_to_wrong_questions', (not existing_answer.is_correct and not resolved_is_ai_generated),
        'is_first_attempt', existing_answer.is_first_attempt,
        'attempt_number', existing_answer.attempt_number,
        'is_first_attempt_in_scope', existing_answer.is_first_attempt_in_scope,
        'scope_attempt_number', existing_answer.scope_attempt_number,
        'practice_session_item_id', p_practice_session_item_id,
        'ability_accuracy', coalesce(stats_row.accuracy, 0),
        'ability_total_count', coalesce(stats_row.total_count, 0),
        'ability_correct_count', coalesce(stats_row.correct_count, 0)
      );
    end if;
  end if;

  if p_practice_session_item_id is not null then
    -- The scope lock linearizes a first answer against replacement claims.  A
    -- late answer stays bindable, but the marker makes every model worker treat
    -- it as ordinary evidence rather than consuming the released VERIFY slot.
    if practice_item_row.target_zone = 'verify'
       and practice_item_row.item_status in ('SELECTED', 'PRESENTED')
       and practice_item_row.answer_id is null
       and not (
         practice_item_row.strategy_metadata
           @> '{"verification_slot_expired": true}'::jsonb
       )
       and coalesce(
         practice_item_row.presented_at,
         practice_item_row.selected_at
       ) <= p_now - interval '15 minutes' then
      update public.practice_session_items
      set strategy_metadata = strategy_metadata || jsonb_build_object(
            'verification_slot_expired', true,
            'verification_slot_expired_at', p_now,
            'verification_slot_lease_seconds', 900
          ),
          updated_at = p_now
      where id = p_practice_session_item_id
      returning * into practice_item_row;
    end if;

    if practice_session_row.status <> 'ACTIVE'
       and not (
         practice_item_row.strategy_metadata
           @> '{"verification_slot_expired": true}'::jsonb
       ) then
      raise exception 'adaptive_session_not_active';
    end if;
    if practice_item_row.answer_id is not null then
      raise exception 'adaptive_session_item_answer_conflict';
    end if;
  end if;

  select count(*)::integer
  into global_attempt_count
  from public.user_answers
  where user_id = p_user_id and question_id = p_question_id;
  global_first_attempt := global_attempt_count = 0;
  next_attempt_number := global_attempt_count + 1;

  insert into public.user_question_progress (
    user_id, stats_exam_code, question_id
  ) values (
    p_user_id, resolved_exam_code, p_question_id
  )
  on conflict (user_id, stats_exam_code, question_id) do nothing;

  select *
  into progress_row
  from public.user_question_progress
  where user_id = p_user_id
    and stats_exam_code = resolved_exam_code
    and question_id = p_question_id
  for update;

  scope_first_attempt := progress_row.attempt_count = 0;
  next_scope_attempt_number := progress_row.attempt_count + 1;

  insert into public.user_answers (
    user_id,
    question_id,
    client_submission_id,
    stats_exam_code,
    selected_answer,
    is_correct,
    used_time,
    attempt_number,
    is_first_attempt,
    scope_attempt_number,
    is_first_attempt_in_scope,
    created_at
  ) values (
    p_user_id,
    p_question_id,
    normalized_client_id,
    resolved_exam_code,
    p_selected_answer,
    resolved_is_correct,
    p_used_time,
    next_attempt_number,
    global_first_attempt,
    next_scope_attempt_number,
    scope_first_attempt,
    p_now
  )
  returning * into existing_answer;

  update public.user_question_progress
  set first_attempt_is_correct = case
        when scope_first_attempt then resolved_is_correct
        else first_attempt_is_correct
      end,
      first_answered_at = case
        when scope_first_attempt then p_now
        else first_answered_at
      end,
      attempt_count = next_scope_attempt_number,
      correct_count = progress_row.correct_count + case when resolved_is_correct then 1 else 0 end,
      last_is_correct = resolved_is_correct,
      last_answered_at = p_now,
      updated_at = p_now
  where user_id = p_user_id
    and stats_exam_code = resolved_exam_code
    and question_id = p_question_id;

  if not resolved_is_correct and not resolved_is_ai_generated then
    insert into public.wrong_questions (
      user_id, stats_exam_code, question_id, wrong_count, last_wrong_at, created_at, updated_at
    ) values (
      p_user_id, resolved_exam_code, p_question_id, 1, p_now, p_now, p_now
    )
    on conflict (user_id, stats_exam_code, question_id) do update
    set wrong_count = public.wrong_questions.wrong_count + 1,
        last_wrong_at = p_now,
        updated_at = p_now;
  end if;

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
  ) values (
    p_user_id,
    resolved_exam_code,
    question_row.subject,
    question_row.module,
    question_row.submodule,
    1,
    case when resolved_is_correct then 1 else 0 end,
    case when resolved_is_correct then 100 else 0 end,
    p_now
  )
  on conflict (user_id, exam_code, subject, module, submodule) do update
  set total_count = public.ability_stats.total_count + 1,
      correct_count = public.ability_stats.correct_count + case when resolved_is_correct then 1 else 0 end,
      accuracy = round(
        (
          (public.ability_stats.correct_count + case when resolved_is_correct then 1 else 0 end)::numeric
          * 100
        ) / (public.ability_stats.total_count + 1),
        2
      ),
      updated_at = p_now
  returning * into stats_row;

  if p_practice_session_item_id is not null then
    update public.practice_session_items
    set item_status = 'ANSWERED',
        presented_at = coalesce(presented_at, p_now),
        answered_at = coalesce(answered_at, p_now),
        answer_id = existing_answer.id,
        adaptive_model_updated_at = null,
        updated_at = p_now
    where id = p_practice_session_item_id;
    update public.practice_sessions
    set last_activity_at = p_now,
        updated_at = p_now
    where id = practice_session_row.id;
  end if;

  return jsonb_build_object(
    'submission_id', existing_answer.id,
    'client_submission_id', existing_answer.client_submission_id,
    'stats_exam_code', existing_answer.stats_exam_code,
    'idempotent', false,
    'persisted', true,
    'selected_answer', existing_answer.selected_answer,
    'correct_answer', question_row.answer,
    'is_correct', existing_answer.is_correct,
    'explanation', question_row.explanation,
    'added_to_wrong_questions', (not existing_answer.is_correct and not resolved_is_ai_generated),
    'is_first_attempt', existing_answer.is_first_attempt,
    'attempt_number', existing_answer.attempt_number,
    'is_first_attempt_in_scope', existing_answer.is_first_attempt_in_scope,
    'scope_attempt_number', existing_answer.scope_attempt_number,
    'practice_session_item_id', p_practice_session_item_id,
    'ability_accuracy', coalesce(stats_row.accuracy, 0),
    'ability_total_count', coalesce(stats_row.total_count, 0),
    'ability_correct_count', coalesce(stats_row.correct_count, 0)
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
comment on function public.record_answer_submission(
  uuid, uuid, text, text, boolean, integer, text, text, text, text, boolean, timestamptz, uuid,
  text, uuid, text, text
) is 'Atomically records one answer; active comprehensive items require an exact locked-manifest capability.';

-- ---------------------------------------------------------------------------
-- 八、练习曝光事件与幂等模型更新 RPC
-- ---------------------------------------------------------------------------

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

-- Return only durable answers whose adaptive model update is still missing.
-- Callers consume a bounded batch, apply it in this order, and call again until
-- the function returns no rows.  The anti-join uses the unique answer_id index
-- on adaptive_model_updates instead of downloading all historical items.
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

-- Atomically claim one computed recommendation.  Candidate ranking remains in
-- application code, but the database is authoritative about whether that
-- recommendation was computed from the current subject state and whether every
-- earlier durable answer in the same ability scope has been modeled.
create or replace function public.claim_next_adaptive_practice_item(
  p_user_id uuid,
  p_session_id uuid,
  p_question_id uuid,
  p_position integer,
  p_expected_subject_state_version bigint,
  p_item jsonb,
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
  item_row public.practice_session_items%rowtype;
  question_row public.questions%rowtype;
  persisted_question_snapshot jsonb;
  trusted_calibration_row public.question_calibration%rowtype;
  verification_conflict_row public.adaptive_conflicts%rowtype;
  expected_position integer;
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
  verification_conflict_id uuid;
  verification_expected_count integer;
  verification_expected_difficulty integer;
  current_verification_difficulty integer;
  trusted_expected_difficulty integer;
begin
  if p_user_id is null
     or p_session_id is null
     or p_question_id is null
     or p_position is null
     or p_position < 1
     or p_expected_subject_state_version is null
     or p_expected_subject_state_version < 0
     or p_now is null then
    raise exception 'adaptive_next_claim_invalid';
  end if;
  if p_item is null or jsonb_typeof(p_item) is distinct from 'object' then
    raise exception 'adaptive_next_claim_invalid_shape';
  end if;
  if jsonb_typeof(p_item->'selection_reason') is distinct from 'string'
     or jsonb_typeof(p_item->'target_zone') is distinct from 'string'
     or jsonb_typeof(p_item->'predicted_probability') is distinct from 'number'
     or jsonb_typeof(p_item->'theta_before') is distinct from 'number'
     or jsonb_typeof(p_item->'item_difficulty') is distinct from 'number'
     or jsonb_typeof(p_item->'score_components') is distinct from 'object'
     or jsonb_typeof(p_item->'strategy_metadata') is distinct from 'object'
     or jsonb_typeof(p_item->'is_diagnostic') is distinct from 'boolean'
     or jsonb_typeof(p_item->'is_challenge') is distinct from 'boolean'
     or (
       p_item ? 'fallback_reason'
       and jsonb_typeof(p_item->'fallback_reason') not in ('null', 'string')
     ) then
    raise exception 'adaptive_next_claim_invalid_shape';
  end if;

  begin
    selection_reason := btrim(p_item->>'selection_reason');
    target_zone := lower(btrim(p_item->>'target_zone'));
    predicted_probability := (p_item->>'predicted_probability')::double precision;
    theta_before := (p_item->>'theta_before')::double precision;
    item_difficulty := (p_item->>'item_difficulty')::double precision;
    score_components := p_item->'score_components';
    strategy_metadata := p_item->'strategy_metadata';
    is_diagnostic := (p_item->>'is_diagnostic')::boolean;
    is_challenge := (p_item->>'is_challenge')::boolean;
    fallback_reason := nullif(btrim(p_item->>'fallback_reason'), '');
  exception when others then
    raise exception 'adaptive_next_claim_invalid_value';
  end;
  if char_length(selection_reason) not between 1 and 120
     or target_zone not in (
       'diagnostic', 'verify', 'consolidation', 'main', 'challenge', 'coverage'
     )
     or predicted_probability not between 0 and 1
     or theta_before not between -6 and 6
     or item_difficulty not between -6 and 6 then
    raise exception 'adaptive_next_claim_invalid_value';
  end if;

  -- The first read discovers the scope only.  All authoritative checks happen
  -- after taking the same scope advisory lock used by answer/model updates.
  select * into session_snapshot
  from public.practice_sessions
  where id = p_session_id and user_id = p_user_id;
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
  where id = p_session_id and user_id = p_user_id
  for update;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;
  if session_row.stats_exam_code <> session_snapshot.stats_exam_code
     or session_row.subject <> session_snapshot.subject then
    raise exception 'adaptive_session_scope_changed';
  end if;
  if session_row.status <> 'ACTIVE' then
    raise exception 'adaptive_session_not_active';
  end if;
  if p_position > session_row.requested_question_count then
    raise exception 'adaptive_next_position_out_of_range';
  end if;

  -- A brand-new scope has the canonical version-zero state.  Materializing it
  -- here gives this transaction a row lock as well as the scope advisory lock.
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
  if subject_row.state_version <> p_expected_subject_state_version
     or abs(subject_row.theta - theta_before) > 0.0000001 then
    raise exception 'adaptive_state_conflict'
      using detail = 'next_item_subject_snapshot_mismatch';
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

  -- A VERIFY reservation is a lease, not a permanent lock. Release abandoned
  -- slots before checking either the session's previous item or the requested
  -- conflict/count pair so a crashed client cannot block this scope forever.
  -- Keep the item itself SELECTED/PRESENTED: a late answer remains bindable and
  -- contributes ordinary ability evidence, but no longer owns a VERIFY slot.
  update public.practice_session_items expired_item
  set strategy_metadata = expired_item.strategy_metadata || jsonb_build_object(
        'verification_slot_expired', true,
        'verification_slot_expired_at', p_now,
        'verification_slot_lease_seconds', 900
      ),
      updated_at = p_now
  from public.practice_sessions expired_session
  where expired_session.id = expired_item.session_id
    and expired_session.user_id = p_user_id
    and expired_session.stats_exam_code = session_row.stats_exam_code
    and expired_session.subject = session_row.subject
    and expired_session.status = 'ACTIVE'
    and expired_item.target_zone = 'verify'
    and expired_item.item_status in ('SELECTED', 'PRESENTED')
    and expired_item.answer_id is null
    and not (
      expired_item.strategy_metadata @> '{"verification_slot_expired": true}'::jsonb
    )
    and coalesce(expired_item.presented_at, expired_item.selected_at)
      <= p_now - interval '15 minutes';

  -- A concurrent retry may have won this position while the caller was ranking.
  -- Return that durable winner; never create a second recommendation.
  select * into item_row
  from public.practice_session_items
  where session_id = p_session_id and position = p_position;
  if found then
    if item_row.item_status not in ('SELECTED', 'PRESENTED')
       or item_row.answer_id is not null then
      raise exception 'adaptive_next_position_conflict';
    end if;
    select snapshot.question_snapshot
    into persisted_question_snapshot
    from public.practice_session_item_question_snapshots snapshot
    where snapshot.practice_session_item_id = item_row.id
      and snapshot.question_id = item_row.question_id;
    if not found then
      raise exception 'adaptive_question_snapshot_not_found';
    end if;
    return to_jsonb(item_row) || jsonb_build_object(
      'claimed', false,
      'idempotent', true,
      'requested_question_id', p_question_id,
      'subject_state_version', subject_row.state_version,
      'question_snapshot', persisted_question_snapshot
    );
  end if;

  -- Always linearize the displayed/grading snapshot against the authoritative
  -- question row.  Candidate ranking may use a short process-local cache, but
  -- the RPC result sent back to the application must reflect the row that was
  -- current when the durable item was claimed.  The row lock also prevents a
  -- concurrent editor from changing the content between this read and insert.
  select * into question_row
  from public.questions
  where id = p_question_id
  for share;
  if not found then
    if target_zone = 'verify' or is_diagnostic then
      raise exception 'adaptive_trusted_candidate_changed'
        using detail = 'question_not_found';
    end if;
    raise exception 'adaptive_question_not_found';
  end if;

  -- Cached ranking may be up to 90 seconds old.  Trusted diagnostic and
  -- verification claims therefore re-check the authoritative question and
  -- calibration rows while holding row locks in this transaction.  A
  -- concurrent revoke either wins before these reads (and is rejected here) or
  -- waits until this claim commits, giving the claim one clear linearization
  -- point for its eligibility decision.
  if is_diagnostic or target_zone = 'verify' then
    if question_row.subject <> session_row.subject
       or question_row.exam_code not in ('COMMON', session_row.stats_exam_code)
       or (
         question_row.exam_code = 'COMMON'
         and question_row.subject not in ('中华文化', '英语运用')
       )
       or coalesce(to_jsonb(question_row)->>'status', 'active') <> 'active'
       or (
         session_row.mode = 'special'
         and not exists (
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
         )
       ) then
      raise exception 'adaptive_trusted_candidate_changed'
        using detail = 'question_not_active_or_out_of_scope';
    end if;

    -- VERIFY has the stricter conflict-owned D2/D3 check below.  Other trusted
    -- diagnostic evidence must still prove that the cached manual difficulty
    -- is the one currently stored on the locked question row.
    if target_zone <> 'verify' then
      if jsonb_typeof(strategy_metadata->'manual_difficulty') is distinct from 'number'
         or (strategy_metadata->>'manual_difficulty') !~ '^[1-5]$' then
        raise exception 'adaptive_trusted_candidate_changed'
          using detail = 'diagnostic_difficulty_metadata_invalid';
      end if;
      begin
        trusted_expected_difficulty :=
          (strategy_metadata->>'manual_difficulty')::integer;
      exception when others then
        raise exception 'adaptive_trusted_candidate_changed'
          using detail = 'diagnostic_difficulty_metadata_invalid';
      end;
      if question_row.difficulty <> trusted_expected_difficulty then
        raise exception 'adaptive_trusted_candidate_changed'
          using detail = 'diagnostic_difficulty_changed';
      end if;
    end if;

    select * into trusted_calibration_row
    from public.question_calibration
    where question_id = p_question_id
      and stats_exam_code = session_row.stats_exam_code
    for share;
    if not found
       or trusted_calibration_row.quality_status <> 'APPROVED'
       or trusted_calibration_row.quality_weight < 0.7
       or (
         target_zone <> 'verify'
         and not trusted_calibration_row.is_diagnostic_candidate
       ) then
      raise exception 'adaptive_trusted_candidate_changed'
        using detail = 'calibration_not_trusted';
    end if;
  end if;

  if exists (
    select 1
    from public.practice_session_items previous_item
    where previous_item.session_id = p_session_id
      and previous_item.item_status in ('SELECTED', 'PRESENTED')
      and previous_item.answer_id is null
      and not (
        previous_item.strategy_metadata @> '{"verification_slot_expired": true}'::jsonb
      )
  ) then
    raise exception 'adaptive_previous_item_pending';
  end if;

  select coalesce(max(existing_item.position), 0) + 1
  into expected_position
  from public.practice_session_items existing_item
  where existing_item.session_id = p_session_id;
  if p_position <> expected_position then
    raise exception 'adaptive_next_position_conflict'
      using detail = 'expected_position=' || expected_position::text;
  end if;

  if target_zone = 'verify' then
    if jsonb_typeof(strategy_metadata->'verification_conflict_id') is distinct from 'string'
       or jsonb_typeof(strategy_metadata->'verification_expected_count') is distinct from 'number'
       or jsonb_typeof(strategy_metadata->'verification_expected_difficulty') is distinct from 'number'
       or (strategy_metadata->>'verification_expected_count') !~ '^(0|[1-9][0-9]*)$'
       or (strategy_metadata->>'verification_expected_difficulty') !~ '^[1-5]$' then
      raise exception 'adaptive_conflict_verification_metadata_invalid';
    end if;
    begin
      verification_conflict_id :=
        (strategy_metadata->>'verification_conflict_id')::uuid;
      verification_expected_count :=
        (strategy_metadata->>'verification_expected_count')::integer;
      verification_expected_difficulty :=
        (strategy_metadata->>'verification_expected_difficulty')::integer;
    exception when others then
      raise exception 'adaptive_conflict_verification_metadata_invalid';
    end;

    select * into verification_conflict_row
    from public.adaptive_conflicts
    where id = verification_conflict_id
      and user_id = p_user_id
      and stats_exam_code = session_row.stats_exam_code
      and subject = session_row.subject
      and status = 'PENDING'
    for update;
    if not found then
      raise exception 'adaptive_conflict_verification_snapshot_mismatch'
        using detail = 'pending_conflict_not_found';
    end if;

    current_verification_difficulty := case
      when mod(verification_conflict_row.verification_count, 2) = 0 then 2
      else 3
    end;
    if verification_expected_count <> verification_conflict_row.verification_count then
      raise exception 'adaptive_conflict_verification_snapshot_mismatch'
        using detail =
          'expected_count=' || verification_conflict_row.verification_count::text
          || ',claimed_count=' || verification_expected_count::text;
    end if;
    if verification_expected_difficulty <> current_verification_difficulty
       or question_row.difficulty <> current_verification_difficulty then
      raise exception 'adaptive_conflict_verification_difficulty_mismatch'
        using detail =
          'expected=' || current_verification_difficulty::text
          || ',claimed=' || verification_expected_difficulty::text
          || ',actual=' || question_row.difficulty::text;
    end if;
    if question_row.subject <> verification_conflict_row.subject
       or question_row.module <> verification_conflict_row.module
       or question_row.submodule <> verification_conflict_row.submodule
       or question_row.question_type <> verification_conflict_row.question_type
       or question_row.id in (
         verification_conflict_row.low_question_id,
         verification_conflict_row.high_question_id
       ) then
      raise exception 'adaptive_conflict_verification_scope_mismatch';
    end if;

    -- The scope advisory lock makes this an atomic reservation check.  It does
    -- not advance verification_count until an answer is accepted, but it keeps
    -- another active session from displaying the same D2/D3 slot concurrently.
    if exists (
      select 1
      from public.practice_sessions claimed_session
      join public.practice_session_items claimed_item
        on claimed_item.session_id = claimed_session.id
      where claimed_session.user_id = p_user_id
        and claimed_session.stats_exam_code = session_row.stats_exam_code
        and claimed_session.subject = session_row.subject
        and claimed_session.status = 'ACTIVE'
        and claimed_item.target_zone = 'verify'
        and claimed_item.item_status in ('SELECTED', 'PRESENTED')
        and claimed_item.answer_id is null
        and not (
          claimed_item.strategy_metadata @> '{"verification_slot_expired": true}'::jsonb
        )
        and lower(claimed_item.strategy_metadata->>'verification_conflict_id')
          = verification_conflict_id::text
        and claimed_item.strategy_metadata->>'verification_expected_count'
          = verification_expected_count::text
    ) then
      raise exception 'adaptive_conflict_verification_slot_claimed';
    end if;
  end if;

  insert into public.practice_session_items (
    session_id,
    question_id,
    position,
    item_status,
    selection_reason,
    target_zone,
    predicted_probability,
    theta_before,
    item_difficulty,
    score_components,
    strategy_metadata,
    is_diagnostic,
    is_challenge,
    fallback_reason,
    selected_at,
    created_at,
    updated_at
  ) values (
    p_session_id,
    p_question_id,
    p_position,
    'SELECTED',
    selection_reason,
    target_zone,
    predicted_probability,
    theta_before,
    item_difficulty,
    score_components,
    strategy_metadata,
    is_diagnostic,
    is_challenge,
    fallback_reason,
    p_now,
    p_now,
    p_now
  ) returning * into item_row;

  persisted_question_snapshot := to_jsonb(question_row);
  insert into public.practice_session_item_question_snapshots (
    practice_session_item_id,
    question_id,
    question_snapshot,
    created_at
  ) values (
    item_row.id,
    item_row.question_id,
    persisted_question_snapshot,
    p_now
  );

  update public.practice_sessions
  set last_activity_at = p_now,
      updated_at = p_now
  where id = p_session_id;

  return to_jsonb(item_row) || jsonb_build_object(
    'claimed', true,
    'idempotent', false,
    'subject_state_version', subject_row.state_version,
    'question_snapshot', persisted_question_snapshot
  );
end;
$$;

create or replace function public.apply_adaptive_model_update(
  p_user_id uuid,
  p_answer_id uuid,
  p_session_item_id uuid,
  p_update jsonb,
  p_now timestamptz default now()
)
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  answer_row public.user_answers%rowtype;
  question_row public.questions%rowtype;
  item_row public.practice_session_items%rowtype;
  session_row public.practice_sessions%rowtype;
  subject_row public.user_subject_state%rowtype;
  topic_row public.user_topic_state%rowtype;
  existing_update public.adaptive_model_updates%rowtype;
  conflict_row public.adaptive_conflicts%rowtype;
  low_question_row public.questions%rowtype;
  high_question_row public.questions%rowtype;
  item_session_id uuid;
  expected_subject_version bigint;
  expected_topic_version bigint;
  next_subject_version bigint;
  next_topic_version bigint;
  subject_before_theta double precision;
  subject_before_uncertainty double precision;
  subject_before_evidence double precision;
  subject_before_reliable integer;
  subject_before_conflicts integer;
  subject_before_status text;
  next_subject_status text;
  next_subject_theta double precision;
  next_subject_uncertainty double precision;
  next_subject_evidence double precision;
  next_subject_reliable integer;
  next_subject_conflicts integer;
  topic_before_theta double precision;
  topic_before_uncertainty double precision;
  topic_before_evidence double precision;
  topic_before_reliable integer;
  topic_before_conflicts integer;
  next_topic_theta double precision;
  next_topic_uncertainty double precision;
  next_topic_evidence double precision;
  next_topic_reliable integer;
  next_topic_conflicts integer;
  predicted_probability double precision;
  evidence_weight double precision;
  item_difficulty double precision;
  v_model_version text;
  v_update_reason text;
  conflict_payload jsonb;
  conflict_action text;
  effective_conflict_action text := 'none';
  requested_conflict_id uuid;
  affected_conflict_id uuid;
  v_low_question_id uuid;
  v_high_question_id uuid;
  conflict_module text;
  conflict_submodule text;
  conflict_question_type text;
  conflict_resolution text;
  expected_verification_difficulty integer;
  item_verification_conflict_id uuid;
  item_verification_expected_count integer;
  item_verification_expected_difficulty integer;
  pending_subject_conflicts integer;
  pending_topic_conflicts integer;
  covered_topic_count integer;
  reliable_increment integer;
  affected_rows integer;
begin
  if p_user_id is null or p_answer_id is null or p_session_item_id is null
     or p_now is null then
    raise exception 'adaptive_update_invalid_identity';
  end if;
  if p_update is null or jsonb_typeof(p_update) is distinct from 'object' then
    raise exception 'adaptive_update_invalid';
  end if;

  select * into answer_row
  from public.user_answers
  where id = p_answer_id and user_id = p_user_id;
  if not found then
    raise exception 'adaptive_answer_not_found';
  end if;

  select populated.* into question_row
  from public.practice_session_item_question_snapshots snapshot
  cross join lateral jsonb_populate_record(
    null::public.questions,
    snapshot.question_snapshot
  ) populated
  where snapshot.practice_session_item_id = p_session_item_id
    and snapshot.question_id = answer_row.question_id;
  if not found then
    raise exception 'adaptive_question_snapshot_not_found';
  end if;

  select session_id into item_session_id
  from public.practice_session_items
  where id = p_session_item_id;
  if not found then
    raise exception 'adaptive_session_item_not_found';
  end if;

  -- All state-changing RPCs acquire the scope lock before row locks. Session
  -- and item rows then use the same session -> item order as the event RPC.
  perform pg_advisory_xact_lock(
    hashtextextended(
      p_user_id::text || ':' || answer_row.stats_exam_code || ':' || question_row.subject,
      0
    )
  );

  select * into session_row
  from public.practice_sessions
  where id = item_session_id and user_id = p_user_id
  for update;
  if not found then
    raise exception 'adaptive_session_not_found';
  end if;

  select * into item_row
  from public.practice_session_items
  where id = p_session_item_id and session_id = session_row.id
  for update;
  if not found then
    raise exception 'adaptive_session_item_not_found';
  end if;

  if item_row.question_id <> answer_row.question_id
     or session_row.stats_exam_code <> answer_row.stats_exam_code
     or session_row.subject <> question_row.subject then
    raise exception 'adaptive_scope_mismatch';
  end if;
  if item_row.item_status = 'SKIPPED' then
    raise exception 'adaptive_session_item_already_skipped';
  end if;
  if item_row.answer_id is not null and item_row.answer_id <> p_answer_id then
    raise exception 'adaptive_session_item_answer_conflict';
  end if;
  if exists (
    select 1
    from public.practice_session_items other_item
    where other_item.answer_id = p_answer_id
      and other_item.id <> p_session_item_id
  ) then
    raise exception 'adaptive_answer_already_attached';
  end if;

  select * into existing_update
  from public.adaptive_model_updates
  where answer_id = p_answer_id;
  if found then
    if existing_update.practice_session_item_id is distinct from p_session_item_id then
      raise exception 'adaptive_update_conflict';
    end if;
    update public.practice_session_items
    set adaptive_model_updated_at = coalesce(
          adaptive_model_updated_at,
          existing_update.created_at,
          p_now
        ),
        updated_at = p_now
    where id = p_session_item_id;
    return jsonb_build_object(
      'adaptive_updated', true,
      'idempotent', true,
      'answer_id', p_answer_id,
      'practice_session_item_id', p_session_item_id,
      'diagnostic_status', existing_update.diagnostic_status_after,
      'theta', existing_update.subject_theta_after,
      'uncertainty', existing_update.subject_uncertainty_after,
      'effective_evidence', existing_update.update_payload #> '{subject_after,effective_evidence}',
      'pending_conflicts', existing_update.pending_conflict_count_after,
      'conflict_action', coalesce(
        existing_update.update_payload #>> '{conflict_result,action}',
        'none'
      ),
      'conflict_id', existing_update.update_payload #>> '{conflict_result,id}'
    );
  end if;

  -- Reject malformed JSON before casting so bad payloads fail with one stable
  -- domain error rather than leaking implementation-specific cast failures.
  if jsonb_typeof(p_update->'model_version') is distinct from 'string'
     or jsonb_typeof(p_update->'update_reason') is distinct from 'string'
     or jsonb_typeof(p_update->'predicted_probability') is distinct from 'number'
     or jsonb_typeof(p_update->'evidence_weight') is distinct from 'number'
     or jsonb_typeof(p_update->'item_difficulty') is distinct from 'number'
     or jsonb_typeof(p_update->'subject_before') is distinct from 'object'
     or jsonb_typeof(p_update->'subject_after') is distinct from 'object'
     or jsonb_typeof(p_update->'topic_before') is distinct from 'object'
     or jsonb_typeof(p_update->'topic_after') is distinct from 'object'
     or jsonb_typeof(p_update->'conflict') is distinct from 'object'
     or (
       p_update ? 'evidence_reasons'
       and jsonb_typeof(p_update->'evidence_reasons') is distinct from 'array'
     )
     or (
       p_update ? 'question_valid'
       and jsonb_typeof(p_update->'question_valid') is distinct from 'boolean'
     ) then
    raise exception 'adaptive_update_invalid_shape';
  end if;

  if jsonb_typeof(p_update #> '{subject_before,theta}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{subject_before,uncertainty}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{subject_before,effective_evidence}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{subject_before,reliable_first_attempt_count}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{subject_before,pending_conflict_count}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{subject_before,state_version}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{subject_before,diagnostic_status}') is distinct from 'string'
     or jsonb_typeof(p_update #> '{subject_after,theta}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{subject_after,uncertainty}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{subject_after,effective_evidence}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{subject_after,reliable_first_attempt_count}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{subject_after,pending_conflict_count}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{subject_after,state_version}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{subject_after,diagnostic_status}') is distinct from 'string'
     or jsonb_typeof(p_update #> '{topic_before,theta}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{topic_before,uncertainty}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{topic_before,effective_evidence}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{topic_before,reliable_first_attempt_count}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{topic_before,pending_conflict_count}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{topic_before,state_version}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{topic_after,theta}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{topic_after,uncertainty}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{topic_after,effective_evidence}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{topic_after,reliable_first_attempt_count}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{topic_after,pending_conflict_count}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{topic_after,state_version}') is distinct from 'number'
     or jsonb_typeof(p_update #> '{conflict,action}') is distinct from 'string' then
    raise exception 'adaptive_update_invalid_state_shape';
  end if;
  if p_update ? 'evidence_reasons' and exists (
    select 1
    from jsonb_array_elements(p_update->'evidence_reasons') reason(value)
    where jsonb_typeof(reason.value) is distinct from 'string'
  ) then
    raise exception 'adaptive_update_invalid_evidence_reasons';
  end if;

  v_model_version := btrim(p_update->>'model_version');
  v_update_reason := btrim(p_update->>'update_reason');
  conflict_payload := p_update->'conflict';
  conflict_action := lower(btrim(conflict_payload->>'action'));
  subject_before_status := upper(btrim(p_update #>> '{subject_before,diagnostic_status}'));
  next_subject_status := upper(btrim(p_update #>> '{subject_after,diagnostic_status}'));
  if char_length(v_model_version) not between 1 and 80
     or char_length(v_update_reason) not between 1 and 120
     or conflict_action not in ('none', 'open', 'verify', 'resolve', 'defer')
     or subject_before_status not in (
       'NEW', 'PROBING', 'VERIFYING', 'CALIBRATING', 'STABLE', 'RECALIBRATING'
     )
     or next_subject_status not in (
       'NEW', 'PROBING', 'VERIFYING', 'CALIBRATING', 'STABLE', 'RECALIBRATING'
     ) then
    raise exception 'adaptive_update_invalid_enum';
  end if;

  if (p_update #>> '{subject_before,state_version}') !~ '^(0|[1-9][0-9]*)$'
     or (p_update #>> '{subject_after,state_version}') !~ '^(0|[1-9][0-9]*)$'
     or (p_update #>> '{topic_before,state_version}') !~ '^(0|[1-9][0-9]*)$'
     or (p_update #>> '{topic_after,state_version}') !~ '^(0|[1-9][0-9]*)$'
     or (p_update #>> '{subject_before,reliable_first_attempt_count}') !~ '^(0|[1-9][0-9]*)$'
     or (p_update #>> '{subject_after,reliable_first_attempt_count}') !~ '^(0|[1-9][0-9]*)$'
     or (p_update #>> '{subject_before,pending_conflict_count}') !~ '^(0|[1-9][0-9]*)$'
     or (p_update #>> '{subject_after,pending_conflict_count}') !~ '^(0|[1-9][0-9]*)$'
     or (p_update #>> '{topic_before,reliable_first_attempt_count}') !~ '^(0|[1-9][0-9]*)$'
     or (p_update #>> '{topic_after,reliable_first_attempt_count}') !~ '^(0|[1-9][0-9]*)$'
     or (p_update #>> '{topic_before,pending_conflict_count}') !~ '^(0|[1-9][0-9]*)$'
     or (p_update #>> '{topic_after,pending_conflict_count}') !~ '^(0|[1-9][0-9]*)$' then
    raise exception 'adaptive_update_invalid_integer';
  end if;

  begin
    predicted_probability := (p_update->>'predicted_probability')::double precision;
    evidence_weight := (p_update->>'evidence_weight')::double precision;
    item_difficulty := (p_update->>'item_difficulty')::double precision;
    expected_subject_version := (p_update #>> '{subject_before,state_version}')::bigint;
    expected_topic_version := (p_update #>> '{topic_before,state_version}')::bigint;
    next_subject_version := (p_update #>> '{subject_after,state_version}')::bigint;
    next_topic_version := (p_update #>> '{topic_after,state_version}')::bigint;
    subject_before_theta := (p_update #>> '{subject_before,theta}')::double precision;
    subject_before_uncertainty := (p_update #>> '{subject_before,uncertainty}')::double precision;
    subject_before_evidence := (p_update #>> '{subject_before,effective_evidence}')::double precision;
    subject_before_reliable := (p_update #>> '{subject_before,reliable_first_attempt_count}')::integer;
    subject_before_conflicts := (p_update #>> '{subject_before,pending_conflict_count}')::integer;
    next_subject_theta := (p_update #>> '{subject_after,theta}')::double precision;
    next_subject_uncertainty := (p_update #>> '{subject_after,uncertainty}')::double precision;
    next_subject_evidence := (p_update #>> '{subject_after,effective_evidence}')::double precision;
    next_subject_reliable := (p_update #>> '{subject_after,reliable_first_attempt_count}')::integer;
    next_subject_conflicts := (p_update #>> '{subject_after,pending_conflict_count}')::integer;
    topic_before_theta := (p_update #>> '{topic_before,theta}')::double precision;
    topic_before_uncertainty := (p_update #>> '{topic_before,uncertainty}')::double precision;
    topic_before_evidence := (p_update #>> '{topic_before,effective_evidence}')::double precision;
    topic_before_reliable := (p_update #>> '{topic_before,reliable_first_attempt_count}')::integer;
    topic_before_conflicts := (p_update #>> '{topic_before,pending_conflict_count}')::integer;
    next_topic_theta := (p_update #>> '{topic_after,theta}')::double precision;
    next_topic_uncertainty := (p_update #>> '{topic_after,uncertainty}')::double precision;
    next_topic_evidence := (p_update #>> '{topic_after,effective_evidence}')::double precision;
    next_topic_reliable := (p_update #>> '{topic_after,reliable_first_attempt_count}')::integer;
    next_topic_conflicts := (p_update #>> '{topic_after,pending_conflict_count}')::integer;
  exception when others then
    raise exception 'adaptive_update_invalid_number';
  end;

  if expected_subject_version >= 9223372036854775807
     or expected_topic_version >= 9223372036854775807 then
    raise exception 'adaptive_update_invalid_transition';
  end if;

  if predicted_probability not between 0 and 1
     or evidence_weight not between 0 and 1
     or item_difficulty not between -6 and 6
     or subject_before_theta not between -6 and 6
     or next_subject_theta not between -6 and 6
     or topic_before_theta not between -6 and 6
     or next_topic_theta not between -6 and 6
     or subject_before_uncertainty <= 0 or subject_before_uncertainty > 10
     or next_subject_uncertainty <= 0 or next_subject_uncertainty > 10
     or topic_before_uncertainty <= 0 or topic_before_uncertainty > 10
     or next_topic_uncertainty <= 0 or next_topic_uncertainty > 10
     or subject_before_evidence < 0 or next_subject_evidence < 0
     or topic_before_evidence < 0 or next_topic_evidence < 0
     or next_subject_version <> expected_subject_version + 1
     or next_topic_version <> expected_topic_version + 1
     or abs(next_subject_theta - subject_before_theta) > 0.250001
     or abs(next_topic_theta - topic_before_theta) > 0.250001
     or (answer_row.is_correct and next_subject_theta < subject_before_theta - 0.0000001)
     or (not answer_row.is_correct and next_subject_theta > subject_before_theta + 0.0000001)
     or (answer_row.is_correct and next_topic_theta < topic_before_theta - 0.0000001)
     or (not answer_row.is_correct and next_topic_theta > topic_before_theta + 0.0000001)
     or abs(next_subject_evidence - (subject_before_evidence + evidence_weight)) > 0.00001
     or abs(next_topic_evidence - (topic_before_evidence + evidence_weight)) > 0.00001 then
    raise exception 'adaptive_update_invalid_transition';
  end if;

  reliable_increment := case
    when answer_row.is_first_attempt and evidence_weight >= 0.7 then 1
    else 0
  end;
  if next_subject_reliable <> subject_before_reliable + reliable_increment
     or next_topic_reliable <> topic_before_reliable + reliable_increment then
    raise exception 'adaptive_update_invalid_reliable_count';
  end if;

  -- A missing subject state has one canonical prior; a caller cannot create a
  -- fabricated version or replace that prior through the RPC payload.
  if expected_subject_version = 0 then
    insert into public.user_subject_state (
      user_id, stats_exam_code, subject, theta, uncertainty, effective_evidence,
      reliable_first_attempt_count, diagnostic_status, pending_conflict_count,
      state_version, model_version, last_answered_at
    ) values (
      p_user_id, answer_row.stats_exam_code, question_row.subject,
      0, 1.6, 0, 0, 'NEW', 0, 0, v_model_version, null
    ) on conflict (user_id, stats_exam_code, subject) do nothing;
  end if;

  select * into subject_row
  from public.user_subject_state
  where user_id = p_user_id
    and stats_exam_code = answer_row.stats_exam_code
    and subject = question_row.subject
  for update;
  if not found or subject_row.state_version <> expected_subject_version then
    raise exception 'adaptive_state_conflict';
  end if;
  if abs(subject_row.theta - subject_before_theta) > 0.0000001
     or abs(subject_row.uncertainty - subject_before_uncertainty) > 0.0000001
     or abs(subject_row.effective_evidence - subject_before_evidence) > 0.0000001
     or subject_row.reliable_first_attempt_count <> subject_before_reliable
     or subject_row.pending_conflict_count <> subject_before_conflicts
     or subject_row.diagnostic_status <> subject_before_status then
    raise exception 'adaptive_state_conflict'
      using detail = 'subject_snapshot_mismatch';
  end if;

  -- A sparse topic starts at the current subject theta, but all other fields
  -- use the canonical empty-evidence prior.
  if expected_topic_version = 0 then
    insert into public.user_topic_state (
      user_id, stats_exam_code, subject, module, submodule, theta, uncertainty,
      effective_evidence, reliable_first_attempt_count, pending_conflict_count,
      state_version, model_version, last_answered_at
    ) values (
      p_user_id, answer_row.stats_exam_code, question_row.subject,
      question_row.module, question_row.submodule,
      subject_row.theta, 1.6, 0, 0, 0, 0, v_model_version, null
    ) on conflict (user_id, stats_exam_code, subject, module, submodule) do nothing;
  end if;

  select * into topic_row
  from public.user_topic_state
  where user_id = p_user_id
    and stats_exam_code = answer_row.stats_exam_code
    and subject = question_row.subject
    and module = question_row.module
    and submodule = question_row.submodule
  for update;
  if not found or topic_row.state_version <> expected_topic_version then
    raise exception 'adaptive_state_conflict';
  end if;
  if abs(topic_row.theta - topic_before_theta) > 0.0000001
     or abs(topic_row.uncertainty - topic_before_uncertainty) > 0.0000001
     or abs(topic_row.effective_evidence - topic_before_evidence) > 0.0000001
     or topic_row.reliable_first_attempt_count <> topic_before_reliable
     or topic_row.pending_conflict_count <> topic_before_conflicts then
    raise exception 'adaptive_state_conflict'
      using detail = 'topic_snapshot_mismatch';
  end if;

  select count(*)::integer into covered_topic_count
  from public.user_topic_state covered_topic
  where covered_topic.user_id = p_user_id
    and covered_topic.stats_exam_code = answer_row.stats_exam_code
    and covered_topic.subject = question_row.subject
    and (
      (
        covered_topic.module = question_row.module
        and covered_topic.submodule = question_row.submodule
        and next_topic_reliable > 0
      )
      or (
        (
          covered_topic.module <> question_row.module
          or covered_topic.submodule <> question_row.submodule
        )
        and covered_topic.reliable_first_attempt_count > 0
      )
    );

  -- Conflict changes and theta changes share this transaction. The database
  -- validates the referenced pair, consumes one verification answer once, and
  -- then derives both pending counters from conflict facts rather than trusting
  -- the counters supplied by the application.
  if conflict_action in ('open', 'verify', 'resolve', 'defer')
     and item_row.strategy_metadata
       @> '{"verification_slot_expired": true}'::jsonb then
    -- Defense in depth for stale workers or delayed clients.  The answer and
    -- theta update remain valid, while every conflict mutation from the old
    -- slot is ignored, including an obsolete request to open a new conflict.
    effective_conflict_action := 'none';
  elsif conflict_action = 'open' then
    if jsonb_typeof(conflict_payload->'low_question_id') is distinct from 'string'
       or jsonb_typeof(conflict_payload->'high_question_id') is distinct from 'string'
       or jsonb_typeof(conflict_payload->'module') is distinct from 'string'
       or jsonb_typeof(conflict_payload->'submodule') is distinct from 'string'
       or jsonb_typeof(conflict_payload->'question_type') is distinct from 'string' then
      raise exception 'adaptive_conflict_payload_invalid';
    end if;
    begin
      v_low_question_id := (conflict_payload->>'low_question_id')::uuid;
      v_high_question_id := (conflict_payload->>'high_question_id')::uuid;
    exception when others then
      raise exception 'adaptive_conflict_question_id_invalid';
    end;
    conflict_module := btrim(conflict_payload->>'module');
    conflict_submodule := btrim(conflict_payload->>'submodule');
    conflict_question_type := btrim(conflict_payload->>'question_type');
    if v_low_question_id = v_high_question_id
       or char_length(conflict_module) not between 1 and 160
       or char_length(conflict_submodule) not between 1 and 160
       or char_length(conflict_question_type) not between 1 and 80 then
      raise exception 'adaptive_conflict_payload_invalid';
    end if;

    select populated.* into low_question_row
    from public.user_answers low_answer
    join public.practice_session_items low_item
      on low_item.answer_id = low_answer.id
     and low_item.question_id = low_answer.question_id
    join public.practice_sessions low_session
      on low_session.id = low_item.session_id
     and low_session.user_id = low_answer.user_id
     and low_session.stats_exam_code = low_answer.stats_exam_code
    join public.practice_session_item_question_snapshots low_snapshot
      on low_snapshot.practice_session_item_id = low_item.id
     and low_snapshot.question_id = low_item.question_id
    cross join lateral jsonb_populate_record(
      null::public.questions,
      low_snapshot.question_snapshot
    ) populated
    where low_answer.user_id = p_user_id
      and low_answer.stats_exam_code = answer_row.stats_exam_code
      and low_answer.question_id = v_low_question_id
      and low_answer.is_first_attempt
      and not low_answer.is_correct
    order by low_answer.created_at asc, low_answer.id asc
    limit 1;
    if not found then
      raise exception 'adaptive_conflict_evidence_mismatch';
    end if;
    select populated.* into high_question_row
    from public.user_answers high_answer
    join public.practice_session_items high_item
      on high_item.answer_id = high_answer.id
     and high_item.question_id = high_answer.question_id
    join public.practice_sessions high_session
      on high_session.id = high_item.session_id
     and high_session.user_id = high_answer.user_id
     and high_session.stats_exam_code = high_answer.stats_exam_code
    join public.practice_session_item_question_snapshots high_snapshot
      on high_snapshot.practice_session_item_id = high_item.id
     and high_snapshot.question_id = high_item.question_id
    cross join lateral jsonb_populate_record(
      null::public.questions,
      high_snapshot.question_snapshot
    ) populated
    where high_answer.user_id = p_user_id
      and high_answer.stats_exam_code = answer_row.stats_exam_code
      and high_answer.question_id = v_high_question_id
      and high_answer.is_first_attempt
      and high_answer.is_correct
    order by high_answer.created_at asc, high_answer.id asc
    limit 1;
    if not found then
      raise exception 'adaptive_conflict_evidence_mismatch';
    end if;
    if low_question_row.subject <> question_row.subject
       or high_question_row.subject <> question_row.subject
       or low_question_row.module <> conflict_module
       or high_question_row.module <> conflict_module
       or low_question_row.submodule <> conflict_submodule
       or high_question_row.submodule <> conflict_submodule
       or low_question_row.question_type <> conflict_question_type
       or high_question_row.question_type <> conflict_question_type
       or low_question_row.exam_code not in ('COMMON', answer_row.stats_exam_code)
       or high_question_row.exam_code not in ('COMMON', answer_row.stats_exam_code)
       or (
         (low_question_row.exam_code = 'COMMON' or high_question_row.exam_code = 'COMMON')
         and question_row.subject not in ('中华文化', '英语运用')
       )
       or high_question_row.difficulty - low_question_row.difficulty < 2 then
      raise exception 'adaptive_conflict_scope_mismatch';
    end if;
    select * into conflict_row
    from public.adaptive_conflicts
    where user_id = p_user_id
      and stats_exam_code = answer_row.stats_exam_code
      and subject = question_row.subject
      and status = 'PENDING'
    order by opened_at asc, id asc
    limit 1
    for update;
    if found then
      affected_conflict_id := conflict_row.id;
      effective_conflict_action := 'already_pending';
    else
      -- A resolved/deferred pair remains terminal for this exact evidence pair.
      -- Session history can still contain the original inversion after it has
      -- been verified, so do not reopen it on every later answer.
      select * into conflict_row
      from public.adaptive_conflicts historical_conflict
      where historical_conflict.user_id = p_user_id
        and historical_conflict.stats_exam_code = answer_row.stats_exam_code
        and historical_conflict.subject = question_row.subject
        and historical_conflict.low_question_id = v_low_question_id
        and historical_conflict.high_question_id = v_high_question_id
        and historical_conflict.status <> 'PENDING'
      order by historical_conflict.resolved_at desc nulls last, historical_conflict.id desc
      limit 1
      for update;
      if found then
        affected_conflict_id := conflict_row.id;
        effective_conflict_action := case
          when conflict_row.status = 'DEFERRED' then 'already_deferred'
          when conflict_row.status = 'CANCELLED' then 'already_cancelled'
          else 'already_resolved'
        end;
      elsif answer_row.question_id not in (v_low_question_id, v_high_question_id) then
        -- This can only be stale session history or a delayed repair. Avoid
        -- mutating the wrong topic state in the current answer transaction.
        effective_conflict_action := 'stale_open_ignored';
      else
        insert into public.adaptive_conflicts (
          user_id, stats_exam_code, subject, module, submodule, question_type,
          low_question_id, high_question_id, status, verification_count,
          opened_at, created_at, updated_at
        ) values (
          p_user_id, answer_row.stats_exam_code, question_row.subject,
          conflict_module, conflict_submodule, conflict_question_type,
          v_low_question_id, v_high_question_id, 'PENDING', 0,
          p_now, p_now, p_now
        ) returning id into affected_conflict_id;
        effective_conflict_action := 'open';
      end if;
    end if;
  elsif conflict_action in ('verify', 'resolve', 'defer') then
    if jsonb_typeof(conflict_payload->'id') is distinct from 'string' then
      raise exception 'adaptive_conflict_payload_invalid';
    end if;
    if jsonb_typeof(item_row.strategy_metadata->'verification_conflict_id') is distinct from 'string'
       or jsonb_typeof(item_row.strategy_metadata->'verification_expected_count') is distinct from 'number'
       or jsonb_typeof(item_row.strategy_metadata->'verification_expected_difficulty') is distinct from 'number'
       or (item_row.strategy_metadata->>'verification_expected_count') !~ '^(0|[1-9][0-9]*)$'
       or (item_row.strategy_metadata->>'verification_expected_difficulty') !~ '^[1-5]$' then
      raise exception 'adaptive_conflict_verification_metadata_invalid';
    end if;
    begin
      requested_conflict_id := (conflict_payload->>'id')::uuid;
    exception when others then
      raise exception 'adaptive_conflict_id_invalid';
    end;
    begin
      item_verification_conflict_id :=
        (item_row.strategy_metadata->>'verification_conflict_id')::uuid;
      item_verification_expected_count :=
        (item_row.strategy_metadata->>'verification_expected_count')::integer;
      item_verification_expected_difficulty :=
        (item_row.strategy_metadata->>'verification_expected_difficulty')::integer;
    exception when others then
      raise exception 'adaptive_conflict_verification_metadata_invalid';
    end;
    if item_verification_conflict_id <> requested_conflict_id then
      raise exception 'adaptive_conflict_verification_snapshot_mismatch'
        using detail = 'conflict_id_mismatch';
    end if;
    select * into conflict_row
    from public.adaptive_conflicts
    where id = requested_conflict_id
      and user_id = p_user_id
      and stats_exam_code = answer_row.stats_exam_code
      and subject = question_row.subject
    for update;
    if not found then
      raise exception 'adaptive_conflict_not_found';
    end if;
    affected_conflict_id := conflict_row.id;
    if conflict_row.status <> 'PENDING' then
      effective_conflict_action := case
        when conflict_row.status = 'DEFERRED' then 'already_deferred'
        when conflict_row.status = 'CANCELLED' then 'already_cancelled'
        else 'already_resolved'
      end;
    else
      if item_row.target_zone <> 'verify'
         or question_row.module <> conflict_row.module
         or question_row.submodule <> conflict_row.submodule
         or question_row.question_type <> conflict_row.question_type
         or question_row.id in (conflict_row.low_question_id, conflict_row.high_question_id) then
        raise exception 'adaptive_conflict_verification_scope_mismatch';
      end if;
      -- verification_count is read from the conflict row while it is locked.
      -- This is the concurrency authority for the D2 parallel check followed by
      -- the D3 transfer check; two sessions that both selected D2 from an old
      -- snapshot cannot both consume a verification slot.
      expected_verification_difficulty := case
        when mod(conflict_row.verification_count, 2) = 0 then 2
        else 3
      end;
      if item_verification_expected_count <> conflict_row.verification_count then
        raise exception 'adaptive_conflict_verification_snapshot_mismatch'
          using detail =
            'expected_count=' || conflict_row.verification_count::text
            || ',claimed_count=' || item_verification_expected_count::text
            || ',conflict_id=' || conflict_row.id::text;
      end if;
      if item_verification_expected_difficulty <> expected_verification_difficulty
         or question_row.difficulty <> expected_verification_difficulty then
        raise exception 'adaptive_conflict_verification_difficulty_mismatch'
          using detail =
            'expected=' || expected_verification_difficulty::text
            || ',claimed=' || item_verification_expected_difficulty::text
            || ',actual=' || question_row.difficulty::text
            || ',conflict_id=' || conflict_row.id::text;
      end if;
      if not answer_row.is_first_attempt
         or evidence_weight < 0.7
         or coalesce(p_update->'question_valid', 'true'::jsonb) <> 'true'::jsonb then
        raise exception 'adaptive_conflict_verification_evidence_invalid';
      end if;

      if conflict_action in ('resolve', 'defer')
         and conflict_row.verification_count + 1 >= 2 then
        if jsonb_typeof(conflict_payload->'resolution') is distinct from 'string' then
          raise exception 'adaptive_conflict_resolution_invalid';
        end if;
        conflict_resolution := btrim(conflict_payload->>'resolution');
        if char_length(conflict_resolution) not between 1 and 240 then
          raise exception 'adaptive_conflict_resolution_invalid';
        end if;
        update public.adaptive_conflicts
        set status = case when conflict_action = 'defer' then 'DEFERRED' else 'RESOLVED' end,
            verification_count = least(20, verification_count + 1),
            resolution = conflict_resolution,
            resolved_at = p_now,
            updated_at = p_now
        where id = conflict_row.id;
        effective_conflict_action := conflict_action;
      else
        update public.adaptive_conflicts
        set verification_count = least(20, verification_count + 1),
            updated_at = p_now
        where id = conflict_row.id;
        effective_conflict_action := 'verify';
      end if;
    end if;
  end if;

  select count(*)::integer into pending_subject_conflicts
  from public.adaptive_conflicts
  where user_id = p_user_id
    and stats_exam_code = answer_row.stats_exam_code
    and subject = question_row.subject
    and status = 'PENDING';
  select count(*)::integer into pending_topic_conflicts
  from public.adaptive_conflicts
  where user_id = p_user_id
    and stats_exam_code = answer_row.stats_exam_code
    and subject = question_row.subject
    and module = question_row.module
    and submodule = question_row.submodule
    and status = 'PENDING';
  next_subject_conflicts := pending_subject_conflicts;
  next_topic_conflicts := pending_topic_conflicts;
  if next_subject_conflicts > 0 then
    next_subject_status := case
      when subject_row.diagnostic_status in ('STABLE', 'RECALIBRATING') then 'RECALIBRATING'
      else 'VERIFYING'
    end;
  elsif next_subject_reliable < 4 then
    next_subject_status := 'PROBING';
  elsif next_subject_reliable >= 20
        and next_subject_evidence >= 18
        and next_subject_uncertainty <= 0.75
        and covered_topic_count >= 2 then
    next_subject_status := 'STABLE';
  else
    next_subject_status := 'CALIBRATING';
  end if;

  p_update := jsonb_set(
    p_update,
    '{subject_after,pending_conflict_count}',
    to_jsonb(next_subject_conflicts),
    false
  );
  p_update := jsonb_set(
    p_update,
    '{subject_after,diagnostic_status}',
    to_jsonb(next_subject_status),
    false
  );
  p_update := jsonb_set(
    p_update,
    '{topic_after,pending_conflict_count}',
    to_jsonb(next_topic_conflicts),
    false
  );
  p_update := p_update || jsonb_build_object(
    'conflict_result', jsonb_build_object(
      'requested_action', conflict_action,
      'action', effective_conflict_action,
      'id', affected_conflict_id,
      'pending_subject_count', next_subject_conflicts,
      'pending_topic_count', next_topic_conflicts
    )
  );

  update public.user_subject_state
  set theta = next_subject_theta,
      uncertainty = next_subject_uncertainty,
      effective_evidence = next_subject_evidence,
      reliable_first_attempt_count = next_subject_reliable,
      diagnostic_status = next_subject_status,
      pending_conflict_count = next_subject_conflicts,
      state_version = next_subject_version,
      model_version = v_model_version,
      last_answered_at = p_now,
      updated_at = p_now
  where user_id = p_user_id
    and stats_exam_code = answer_row.stats_exam_code
    and subject = question_row.subject
    and state_version = expected_subject_version;
  get diagnostics affected_rows = row_count;
  if affected_rows <> 1 then
    raise exception 'adaptive_state_conflict';
  end if;

  update public.user_topic_state
  set theta = next_topic_theta,
      uncertainty = next_topic_uncertainty,
      effective_evidence = next_topic_evidence,
      reliable_first_attempt_count = next_topic_reliable,
      pending_conflict_count = next_topic_conflicts,
      state_version = next_topic_version,
      model_version = v_model_version,
      last_answered_at = p_now,
      updated_at = p_now
  where user_id = p_user_id
    and stats_exam_code = answer_row.stats_exam_code
    and subject = question_row.subject
    and module = question_row.module
    and submodule = question_row.submodule
    and state_version = expected_topic_version;
  get diagnostics affected_rows = row_count;
  if affected_rows <> 1 then
    raise exception 'adaptive_state_conflict';
  end if;

  update public.practice_session_items
  set item_status = 'ANSWERED',
      presented_at = coalesce(presented_at, p_now),
      answered_at = coalesce(answered_at, p_now),
      answer_id = p_answer_id,
      adaptive_model_updated_at = p_now,
      strategy_metadata = strategy_metadata || jsonb_build_object(
        'evidence_weight', evidence_weight,
        'evidence_reasons', coalesce(p_update->'evidence_reasons', '[]'::jsonb),
        'question_valid', coalesce(p_update->'question_valid', 'true'::jsonb)
      ),
      updated_at = p_now
  where id = p_session_item_id;

  update public.practice_sessions
  set diagnostic_status = next_subject_status,
      last_activity_at = p_now,
      updated_at = p_now
  where id = session_row.id;

  insert into public.adaptive_model_updates (
    answer_id, practice_session_item_id, user_id, stats_exam_code, subject,
    module, submodule, model_version, predicted_probability, evidence_weight,
    item_difficulty, actual_correct,
    subject_state_version_before, subject_state_version_after,
    subject_theta_before, subject_theta_after, subject_delta_theta,
    subject_uncertainty_before, subject_uncertainty_after,
    topic_state_version_before, topic_state_version_after,
    topic_theta_before, topic_theta_after, topic_delta_theta,
    topic_uncertainty_before, topic_uncertainty_after,
    diagnostic_status_before, diagnostic_status_after,
    pending_conflict_count_before, pending_conflict_count_after,
    update_reason, update_payload, created_at
  ) values (
    p_answer_id, p_session_item_id, p_user_id, answer_row.stats_exam_code,
    question_row.subject, question_row.module, question_row.submodule,
    v_model_version,
    predicted_probability,
    evidence_weight,
    item_difficulty,
    answer_row.is_correct,
    subject_row.state_version, next_subject_version,
    subject_row.theta, next_subject_theta, next_subject_theta - subject_row.theta,
    subject_row.uncertainty, next_subject_uncertainty,
    topic_row.state_version, next_topic_version,
    topic_row.theta, next_topic_theta, next_topic_theta - topic_row.theta,
    topic_row.uncertainty, next_topic_uncertainty,
    subject_row.diagnostic_status, next_subject_status,
    subject_row.pending_conflict_count, next_subject_conflicts,
    v_update_reason,
    p_update,
    p_now
  );

  return jsonb_build_object(
    'adaptive_updated', true,
    'idempotent', false,
    'answer_id', p_answer_id,
    'practice_session_item_id', p_session_item_id,
    'diagnostic_status', next_subject_status,
    'theta', next_subject_theta,
    'uncertainty', next_subject_uncertainty,
    'effective_evidence', next_subject_evidence,
    'pending_conflicts', next_subject_conflicts,
    'conflict_action', effective_conflict_action,
    'conflict_id', affected_conflict_id
  );
end;
$$;

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

revoke all on function public.claim_next_adaptive_practice_item(
  uuid, uuid, uuid, integer, bigint, jsonb, timestamptz
) from public, anon, authenticated;
grant execute on function public.claim_next_adaptive_practice_item(
  uuid, uuid, uuid, integer, bigint, jsonb, timestamptz
) to service_role;

revoke all on function public.apply_adaptive_model_update(uuid, uuid, uuid, jsonb, timestamptz)
  from public, anon, authenticated;
grant execute on function public.apply_adaptive_model_update(uuid, uuid, uuid, jsonb, timestamptz)
  to service_role;

comment on function public.get_pending_adaptive_update_items(uuid, text, text, uuid, integer) is
  'Returns a bounded chronological batch of durable adaptive answers that have no model-update audit row.';
comment on function public.claim_next_adaptive_practice_item(
  uuid, uuid, uuid, integer, bigint, jsonb, timestamptz
) is
  'Atomically claims one recommendation only when its subject state snapshot is current and its ability scope has no pending answer update.';

notify pgrst, 'reload schema';

commit;
