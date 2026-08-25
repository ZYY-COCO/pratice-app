-- 港研通第三批：作答可靠性与学习统计正确性
-- 执行位置：Supabase SQL Editor
-- 目标：
--   1. 为作答增加客户端幂等键和不可变的首次作答事实；
--   2. 在一个数据库事务内写入作答、错题、题目进度和能力统计；
--   3. 为并发作答提供按用户/题目的行级锁；
--   4. 应用层会阻止物理删除已有作答记录的题目，避免级联数据丢失。

begin;

alter table public.user_answers
  add column if not exists client_submission_id text,
  add column if not exists stats_exam_code text,
  add column if not exists attempt_number integer not null default 1,
  add column if not exists is_first_attempt boolean not null default false;

alter table public.user_answers
  drop constraint if exists user_answers_client_submission_id_check;
alter table public.user_answers
  add constraint user_answers_client_submission_id_check
  check (client_submission_id is null or char_length(btrim(client_submission_id)) between 1 and 120);

alter table public.user_answers
  drop constraint if exists user_answers_attempt_number_check;
alter table public.user_answers
  add constraint user_answers_attempt_number_check
  check (attempt_number >= 1);

update public.user_answers answers
set stats_exam_code = case
  when questions.subject in ('中华文化', '英语运用')
       and users.exam_target in ('Z001', 'Z002') then users.exam_target
  when questions.exam_code in ('Z001', 'Z002') then questions.exam_code
  when users.exam_target in ('Z001', 'Z002') then users.exam_target
  else 'Z001'
end
from public.questions questions, public.users users
where answers.question_id = questions.id
  and answers.user_id = users.id
  and answers.stats_exam_code is null;

alter table public.user_answers
  drop constraint if exists user_answers_stats_exam_code_check;
alter table public.user_answers
  add constraint user_answers_stats_exam_code_check
  check (stats_exam_code in ('Z001', 'Z002'));
alter table public.user_answers
  alter column stats_exam_code set not null;

-- 先为历史作答补齐稳定的尝试序号和首次作答标记。
with ranked as (
  select
    id,
    row_number() over (
      partition by user_id, question_id
      order by created_at asc, id asc
    )::integer as next_attempt_number
  from public.user_answers
)
update public.user_answers answers
set attempt_number = ranked.next_attempt_number,
    is_first_attempt = ranked.next_attempt_number = 1
from ranked
where answers.id = ranked.id;

create unique index if not exists uq_user_answers_client_submission
  on public.user_answers (user_id, client_submission_id)
  where client_submission_id is not null;

create index if not exists idx_user_answers_user_question_created
  on public.user_answers (user_id, question_id, created_at asc, id asc);

create table if not exists public.user_question_progress (
  user_id uuid not null references public.users(id) on delete cascade,
  question_id uuid not null references public.questions(id) on delete cascade,
  first_attempt_is_correct boolean,
  first_answered_at timestamptz,
  attempt_count integer not null default 0 check (attempt_count >= 0),
  correct_count integer not null default 0 check (correct_count >= 0),
  last_is_correct boolean,
  last_answered_at timestamptz,
  updated_at timestamptz not null default now(),
  primary key (user_id, question_id)
);

-- 进度事实完全由作答明细派生；重跑迁移时先清空，避免残留已不存在的历史聚合。
delete from public.user_question_progress;
insert into public.user_question_progress (
  user_id,
  question_id,
  first_attempt_is_correct,
  first_answered_at,
  attempt_count,
  correct_count,
  last_is_correct,
  last_answered_at
)
select
  answers.user_id,
  answers.question_id,
  (array_agg(answers.is_correct order by answers.created_at asc, answers.id asc))[1],
  min(answers.created_at),
  count(*)::integer,
  count(*) filter (where answers.is_correct)::integer,
  (array_agg(answers.is_correct order by answers.created_at desc, answers.id desc))[1],
  max(answers.created_at)
from public.user_answers answers
group by answers.user_id, answers.question_id
on conflict (user_id, question_id) do update
set first_attempt_is_correct = excluded.first_attempt_is_correct,
    first_answered_at = excluded.first_answered_at,
    attempt_count = excluded.attempt_count,
    correct_count = excluded.correct_count,
    last_is_correct = excluded.last_is_correct,
    last_answered_at = excluded.last_answered_at,
    updated_at = now();

-- ability_stats 是作答记录的派生聚合；迁移时从真实历史重新建立一次基线。
delete from public.ability_stats;
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
)
select
  answers.user_id,
  answers.stats_exam_code,
  questions.subject,
  questions.module,
  questions.submodule,
  count(*)::integer,
  count(*) filter (where answers.is_correct)::integer,
  round(
    count(*) filter (where answers.is_correct)::numeric * 100 / count(*),
    2
  ),
  max(answers.created_at)
from public.user_answers answers
join public.questions questions on questions.id = answers.question_id
group by
  answers.user_id,
  answers.stats_exam_code,
  questions.subject,
  questions.module,
  questions.submodule;

create index if not exists idx_user_question_progress_user_updated
  on public.user_question_progress (user_id, updated_at desc);

alter table public.user_question_progress enable row level security;
drop policy if exists "users can read own question progress" on public.user_question_progress;
create policy "users can read own question progress"
  on public.user_question_progress for select
  using (auth.uid() = user_id);

revoke all on table public.user_question_progress from anon, authenticated;
grant select on table public.user_question_progress to authenticated;

-- 正式作答统一经过后端 service role 调用原子 RPC，关闭可伪造正确率的客户端直写入口。
drop policy if exists "users can insert own answers" on public.user_answers;
drop policy if exists "users can upsert own wrong questions" on public.wrong_questions;
drop policy if exists "users can upsert own ability stats" on public.ability_stats;
revoke insert, update, delete on table public.user_answers from anon, authenticated;
revoke insert, update, delete on table public.wrong_questions from anon, authenticated;
revoke insert, update, delete on table public.ability_stats from anon, authenticated;


create or replace function public.refresh_user_question_progress(
  p_user_id uuid,
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
  if p_user_id is null or p_question_id is null then
    return;
  end if;

  perform pg_advisory_xact_lock(
    hashtextextended(p_user_id::text || ':' || p_question_id::text, 0)
  );

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
  where user_id = p_user_id and question_id = p_question_id;

  if answer_count = 0 then
    delete from public.user_question_progress
    where user_id = p_user_id and question_id = p_question_id;
    return;
  end if;

  insert into public.user_question_progress (
    user_id,
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
    p_question_id,
    first_correct,
    first_at,
    answer_count,
    answer_correct_count,
    last_correct,
    last_at,
    p_now
  )
  on conflict (user_id, question_id) do update
  set first_attempt_is_correct = excluded.first_attempt_is_correct,
      first_answered_at = excluded.first_answered_at,
      attempt_count = excluded.attempt_count,
      correct_count = excluded.correct_count,
      last_is_correct = excluded.last_is_correct,
      last_answered_at = excluded.last_answered_at,
      updated_at = excluded.updated_at;
end;
$$;

revoke all on function public.refresh_user_question_progress(uuid, uuid, timestamptz)
  from public, anon, authenticated;
grant execute on function public.refresh_user_question_progress(uuid, uuid, timestamptz)
  to service_role;

create or replace function public.sync_user_answer_progress_after_owner_change()
returns trigger
language plpgsql
security definer
set search_path = public, pg_temp
as $$
begin
  perform public.refresh_user_question_progress(old.user_id, old.question_id, now());
  if new.user_id is distinct from old.user_id
     or new.question_id is distinct from old.question_id then
    perform public.refresh_user_question_progress(new.user_id, new.question_id, now());
  end if;
  return new;
end;
$$;

drop trigger if exists sync_user_answer_progress_after_owner_change
  on public.user_answers;
create trigger sync_user_answer_progress_after_owner_change
after update of user_id on public.user_answers
for each row execute function public.sync_user_answer_progress_after_owner_change();

create or replace function public.record_answer_submission(
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
  p_now timestamptz default now()
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
  first_attempt boolean;
  next_attempt_number integer;
  resolved_exam_code text;
  resolved_is_correct boolean;
  resolved_is_ai_generated boolean;
begin
  if p_user_id is null or p_question_id is null then
    raise exception 'answer_submission_invalid_identity';
  end if;
  if p_selected_answer not in ('A', 'B', 'C', 'D') then
    raise exception 'answer_submission_invalid_option';
  end if;
  if p_used_time is null or p_used_time < 0 then
    raise exception 'answer_submission_invalid_time';
  end if;
  if p_exam_code not in ('Z001', 'Z002') then
    raise exception 'answer_submission_invalid_exam_code';
  end if;

  select * into question_row
  from public.questions
  where id = p_question_id;
  if not found then
    raise exception 'answer_submission_question_not_found';
  end if;
  resolved_exam_code := case
    when question_row.subject in ('中华文化', '英语运用') then p_exam_code
    when question_row.exam_code in ('Z001', 'Z002') then question_row.exam_code
    else p_exam_code
  end;
  resolved_is_correct := p_selected_answer = question_row.answer;
  resolved_is_ai_generated := coalesce(question_row.source_type, '') = 'ai_deepseek';

  -- 同一用户对同一题的所有写入串行化，确保首次作答和能力增量不会竞争覆盖。
  perform pg_advisory_xact_lock(
    hashtextextended(p_user_id::text || ':' || p_question_id::text, 0)
  );

  -- 同一客户端提交键重试时返回原记录；不同正文/选项使用同键则明确冲突。
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
      where user_id = p_user_id and question_id = p_question_id;

      select * into stats_row
      from public.ability_stats
      where user_id = p_user_id
        and exam_code = resolved_exam_code
        and subject = question_row.subject
        and module = question_row.module
        and submodule = question_row.submodule;

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
        'ability_accuracy', coalesce(stats_row.accuracy, 0),
        'ability_total_count', coalesce(stats_row.total_count, 0),
        'ability_correct_count', coalesce(stats_row.correct_count, 0)
      );
    end if;
  end if;

  insert into public.user_question_progress (user_id, question_id)
  values (p_user_id, p_question_id)
  on conflict (user_id, question_id) do nothing;

  select *
  into progress_row
  from public.user_question_progress
  where user_id = p_user_id and question_id = p_question_id
  for update;

  first_attempt := progress_row.attempt_count = 0;
  next_attempt_number := progress_row.attempt_count + 1;

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
    first_attempt,
    p_now
  )
  returning * into existing_answer;

  update public.user_question_progress
  set first_attempt_is_correct = case
        when first_attempt then resolved_is_correct
        else first_attempt_is_correct
      end,
      first_answered_at = case
        when first_attempt then p_now
        else first_answered_at
      end,
      attempt_count = next_attempt_number,
      correct_count = progress_row.correct_count + case when resolved_is_correct then 1 else 0 end,
      last_is_correct = resolved_is_correct,
      last_answered_at = p_now,
      updated_at = p_now
  where user_id = p_user_id and question_id = p_question_id;

  if not resolved_is_correct and not resolved_is_ai_generated then
    insert into public.wrong_questions (
      user_id, question_id, wrong_count, last_wrong_at, created_at, updated_at
    ) values (
      p_user_id, p_question_id, 1, p_now, p_now, p_now
    )
    on conflict (user_id, question_id) do update
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
    'ability_accuracy', coalesce(stats_row.accuracy, 0),
    'ability_total_count', coalesce(stats_row.total_count, 0),
    'ability_correct_count', coalesce(stats_row.correct_count, 0)
  );
end;
$$;

revoke all on function public.record_answer_submission(
  uuid, uuid, text, text, boolean, integer, text, text, text, text, boolean, timestamptz
) from public, anon, authenticated;
grant execute on function public.record_answer_submission(
  uuid, uuid, text, text, boolean, integer, text, text, text, text, boolean, timestamptz
) to service_role;

comment on function public.record_answer_submission(
  uuid, uuid, text, text, boolean, integer, text, text, text, text, boolean, timestamptz
) is 'Atomically records one answer, first-attempt fact, wrong-question update and ability-stat increment.';

-- 让 Supabase 的 PostgREST 在事务提交后立即刷新新表、字段和 RPC 的 schema cache。
notify pgrst, 'reload schema';

commit;
