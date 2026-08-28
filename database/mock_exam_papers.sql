-- Administrator-curated mock papers.
-- Apply this migration in Supabase SQL Editor before enabling the fixed-paper UI.

create table if not exists public.mock_exam_papers (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  exam_code text not null check (exam_code in ('Z001', 'Z002')),
  description text not null default '',
  duration_minutes integer not null default 120 check (duration_minutes between 30 and 360),
  status text not null default 'draft' check (status in ('draft', 'published', 'archived')),
  version integer not null default 1 check (version >= 1),
  question_count integer not null default 0 check (question_count between 0 and 55),
  total_score integer not null default 0 check (total_score between 0 and 105),
  sort_order integer not null default 0,
  created_by uuid references public.users(id) on delete set null,
  published_by uuid references public.users(id) on delete set null,
  published_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_mock_exam_papers_public
  on public.mock_exam_papers (exam_code, status, sort_order, published_at desc);

drop trigger if exists set_mock_exam_papers_updated_at on public.mock_exam_papers;
create trigger set_mock_exam_papers_updated_at
before update on public.mock_exam_papers
for each row execute function public.set_updated_at();

create table if not exists public.mock_exam_paper_items (
  id uuid primary key default gen_random_uuid(),
  paper_id uuid not null references public.mock_exam_papers(id) on delete cascade,
  question_id uuid not null references public.questions(id) on delete restrict,
  section_key text not null check (section_key in ('culture', 'english', 'third')),
  position integer not null check (position between 1 and 55),
  point_value integer not null check (point_value in (1, 2, 3)),
  created_at timestamptz not null default now(),
  unique (paper_id, question_id),
  unique (paper_id, position)
);

create index if not exists idx_mock_exam_paper_items_paper_position
  on public.mock_exam_paper_items (paper_id, position);

create index if not exists idx_mock_exam_paper_items_question
  on public.mock_exam_paper_items (question_id);

create or replace function public.replace_mock_exam_paper_items(
  p_paper_id uuid,
  p_items jsonb
)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  if jsonb_typeof(coalesce(p_items, '[]'::jsonb)) <> 'array' then
    raise exception 'mock_exam_items_must_be_an_array';
  end if;

  if jsonb_array_length(coalesce(p_items, '[]'::jsonb)) > 55 then
    raise exception 'mock_exam_item_limit_exceeded';
  end if;

  if not exists (select 1 from public.mock_exam_papers where id = p_paper_id) then
    raise exception 'mock_exam_paper_not_found';
  end if;

  delete from public.mock_exam_paper_items where paper_id = p_paper_id;

  insert into public.mock_exam_paper_items (
    paper_id,
    question_id,
    section_key,
    position,
    point_value
  )
  select
    p_paper_id,
    item.question_id,
    item.section_key,
    item.position,
    item.point_value
  from jsonb_to_recordset(coalesce(p_items, '[]'::jsonb)) as item(
    question_id uuid,
    section_key text,
    position integer,
    point_value integer
  )
  order by item.position;
end;
$$;

revoke all on function public.replace_mock_exam_paper_items(uuid, jsonb) from public, anon, authenticated;
grant execute on function public.replace_mock_exam_paper_items(uuid, jsonb) to service_role;

alter table public.mock_exam_papers enable row level security;
alter table public.mock_exam_paper_items enable row level security;

revoke all on public.mock_exam_papers from anon, authenticated;
revoke all on public.mock_exam_paper_items from anon, authenticated;
grant all on public.mock_exam_papers to service_role;
grant all on public.mock_exam_paper_items to service_role;
