-- Internal question-bank folders.
-- Run this migration in Supabase SQL Editor before using the folder-based
-- question management workspace.

create table if not exists public.question_banks (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  created_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create unique index if not exists idx_question_banks_name_lower
  on public.question_banks (lower(name));

drop trigger if exists set_question_banks_updated_at on public.question_banks;
create trigger set_question_banks_updated_at
before update on public.question_banks
for each row execute function public.set_updated_at();

alter table public.question_banks enable row level security;
revoke all on public.question_banks from anon, authenticated;
grant all on public.question_banks to service_role;

-- Existing official questions belong to the initial internal bank.
insert into public.question_banks (name)
values ('Z')
on conflict ((lower(name))) do nothing;

alter table public.questions
  add column if not exists question_bank_id uuid references public.question_banks(id) on delete restrict;

update public.questions q
set question_bank_id = bank.id
from public.question_banks bank
where lower(bank.name) = lower('Z')
  and q.question_bank_id is null;

alter table public.questions
  alter column question_bank_id set not null;

create index if not exists idx_questions_question_bank_id
  on public.questions (question_bank_id);

-- Keep existing import scripts compatible: an omitted bank is assigned to Z.
create or replace function public.assign_default_question_bank()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
declare
  default_bank_id uuid;
begin
  if new.question_bank_id is not null then
    return new;
  end if;

  select id into default_bank_id
  from public.question_banks
  where lower(name) = lower('Z')
  limit 1;

  if default_bank_id is null then
    raise exception 'Default question bank Z does not exist';
  end if;

  new.question_bank_id := default_bank_id;
  return new;
end;
$$;

drop trigger if exists assign_default_question_bank on public.questions;
create trigger assign_default_question_bank
before insert on public.questions
for each row execute function public.assign_default_question_bank();

-- A bank's modified time follows every question create, edit, or removal.
create or replace function public.touch_question_bank_on_question_change()
returns trigger
language plpgsql
security definer
set search_path = public
as $$
begin
  if tg_op = 'DELETE' then
    update public.question_banks set updated_at = now() where id = old.question_bank_id;
    return old;
  end if;

  update public.question_banks
  set updated_at = now()
  where id = new.question_bank_id
     or (tg_op = 'UPDATE' and id = old.question_bank_id);
  return new;
end;
$$;

drop trigger if exists touch_question_bank_on_question_change on public.questions;
create trigger touch_question_bank_on_question_change
after insert or update or delete on public.questions
for each row execute function public.touch_question_bank_on_question_change();
