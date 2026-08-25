-- 研圈资料管理：推荐资料（百度网盘链接）与未来精选课程共用一张资源表。
-- 该脚本可重复执行。请在 Supabase SQL Editor 中单独运行。

create table if not exists public.circle_resource_items (
  id uuid primary key default gen_random_uuid(),
  resource_type text not null check (resource_type in ('material', 'course')),
  title text not null check (char_length(btrim(title)) between 1 and 120),
  summary text not null default '' check (char_length(summary) <= 1000),
  subject text not null default '' check (char_length(subject) <= 80),
  tags jsonb not null default '[]'::jsonb check (jsonb_typeof(tags) = 'array'),
  cover_url text not null default '' check (char_length(cover_url) <= 1000),
  share_url text not null default '' check (char_length(share_url) <= 1000),
  access_code text not null default '' check (char_length(access_code) <= 120),
  instructor_name text not null default '' check (char_length(instructor_name) <= 80),
  course_price numeric(10, 2) check (course_price is null or course_price >= 0),
  sort_order integer not null default 0 check (sort_order between -10000 and 10000),
  status text not null default 'draft' check (status in ('draft', 'published', 'archived')),
  published_at timestamptz,
  created_by uuid references public.users(id) on delete set null,
  updated_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint circle_resource_items_published_material_check check (
    status <> 'published'
    or resource_type <> 'material'
    or char_length(btrim(share_url)) > 0
  ),
  constraint circle_resource_items_published_course_check check (
    status <> 'published'
    or resource_type <> 'course'
    or course_price is not null
  )
);

alter table public.circle_resource_items
  add column if not exists resource_type text,
  add column if not exists title text,
  add column if not exists summary text not null default '',
  add column if not exists subject text not null default '',
  add column if not exists tags jsonb not null default '[]'::jsonb,
  add column if not exists cover_url text not null default '',
  add column if not exists share_url text not null default '',
  add column if not exists access_code text not null default '',
  add column if not exists instructor_name text not null default '',
  add column if not exists course_price numeric(10, 2),
  add column if not exists sort_order integer not null default 0,
  add column if not exists status text not null default 'draft',
  add column if not exists published_at timestamptz,
  add column if not exists created_by uuid references public.users(id) on delete set null,
  add column if not exists updated_by uuid references public.users(id) on delete set null,
  add column if not exists created_at timestamptz not null default now(),
  add column if not exists updated_at timestamptz not null default now();

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'circle_resource_items_resource_type_check'
      and conrelid = 'public.circle_resource_items'::regclass
  ) then
    alter table public.circle_resource_items
      add constraint circle_resource_items_resource_type_check
      check (resource_type in ('material', 'course'));
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'circle_resource_items_status_check'
      and conrelid = 'public.circle_resource_items'::regclass
  ) then
    alter table public.circle_resource_items
      add constraint circle_resource_items_status_check
      check (status in ('draft', 'published', 'archived'));
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'circle_resource_items_published_material_check'
      and conrelid = 'public.circle_resource_items'::regclass
  ) then
    alter table public.circle_resource_items
      add constraint circle_resource_items_published_material_check
      check (
        status <> 'published'
        or resource_type <> 'material'
        or char_length(btrim(share_url)) > 0
      );
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'circle_resource_items_published_course_check'
      and conrelid = 'public.circle_resource_items'::regclass
  ) then
    alter table public.circle_resource_items
      add constraint circle_resource_items_published_course_check
      check (
        status <> 'published'
        or resource_type <> 'course'
        or course_price is not null
      );
  end if;
end $$;

create index if not exists circle_resource_items_public_list_idx
  on public.circle_resource_items (resource_type, status, sort_order, published_at desc);

create index if not exists circle_resource_items_admin_list_idx
  on public.circle_resource_items (resource_type, status, updated_at desc);

create or replace function public.touch_circle_resource_item_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

drop trigger if exists circle_resource_items_touch_updated_at on public.circle_resource_items;
create trigger circle_resource_items_touch_updated_at
before update on public.circle_resource_items
for each row execute function public.touch_circle_resource_item_updated_at();

alter table public.circle_resource_items enable row level security;

drop policy if exists circle_resource_items_public_read on public.circle_resource_items;
create policy circle_resource_items_public_read
on public.circle_resource_items
for select
to anon, authenticated
using (status = 'published');
