-- Normalize the production question bank back to four choices (A-D).
-- Run this once in Supabase SQL Editor after deploying the code change.

begin;

alter table public.questions
  add column if not exists option_e text;

-- Keep historical answer records valid before tightening the check constraint.
-- Rows where a user selected old E are mapped to D because E no longer exists.
update public.user_answers ua
set
  selected_answer = 'D',
  is_correct = case
    when q.answer = 'E' then true
    else false
  end
from public.questions q
where ua.question_id = q.id
  and ua.selected_answer = 'E';

-- If the correct answer used to be E, keep that correct option by moving it to D.
update public.questions
set
  option_d = option_e,
  answer = 'D',
  explanation = replace(
    replace(
      replace(
        replace(
          replace(
            replace(coalesce(explanation, ''), 'E项', 'D项'),
            'E 项',
            'D 项'
          ),
          '选E',
          '选D'
        ),
        '答案为E',
        '答案为D'
      ),
      '答案 E',
      '答案 D'
    ),
    '正确答案 E',
    '正确答案 D'
  )
where answer = 'E'
  and option_e is not null
  and btrim(option_e) <> '';

-- Safety fallback for any malformed row whose answer is E but option_e is empty.
update public.questions
set answer = 'D'
where answer = 'E';

update public.questions
set option_e = null
where option_e is not null;

alter table public.questions
  drop constraint if exists questions_answer_check;

alter table public.questions
  add constraint questions_answer_check
  check (answer in ('A', 'B', 'C', 'D'));

alter table public.user_answers
  drop constraint if exists user_answers_selected_answer_check;

alter table public.user_answers
  add constraint user_answers_selected_answer_check
  check (selected_answer in ('A', 'B', 'C', 'D'));

commit;
