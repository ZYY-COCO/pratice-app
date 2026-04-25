-- Add optional E choice support for logic questions.
-- Existing A-D questions remain valid because option_e is nullable.

alter table public.questions
  add column if not exists option_e text;

alter table public.questions
  drop constraint if exists questions_answer_check;

alter table public.questions
  add constraint questions_answer_check
  check (answer in ('A', 'B', 'C', 'D', 'E'));

alter table public.user_answers
  drop constraint if exists user_answers_selected_answer_check;

alter table public.user_answers
  add constraint user_answers_selected_answer_check
  check (selected_answer in ('A', 'B', 'C', 'D', 'E'));
