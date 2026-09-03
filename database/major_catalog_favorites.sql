-- 用户在专业目录中收藏院校或专业。
-- 先于依赖收藏接口的后端/前端版本在 Supabase SQL Editor 执行。

create table if not exists public.major_catalog_favorites (
  id uuid primary key default gen_random_uuid(),
  user_id uuid not null references public.users(id) on delete cascade,
  catalog_year text not null check (catalog_year ~ '^20[0-9]{2}$'),
  target_type text not null check (target_type in ('school', 'program')),
  target_id text not null check (char_length(btrim(target_id)) between 1 and 128),
  school_id text not null check (char_length(btrim(school_id)) between 1 and 128),
  snapshot jsonb not null default '{}'::jsonb check (jsonb_typeof(snapshot) = 'object'),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint major_catalog_favorites_school_identity_check check (
    target_type = 'program' or target_id = school_id
  ),
  constraint major_catalog_favorites_user_target_key unique (
    user_id,
    catalog_year,
    target_type,
    target_id
  )
);

create index if not exists idx_major_catalog_favorites_user_created
  on public.major_catalog_favorites (user_id, created_at desc, id desc);

create index if not exists idx_major_catalog_favorites_school
  on public.major_catalog_favorites (school_id);

drop trigger if exists set_major_catalog_favorites_updated_at on public.major_catalog_favorites;
create trigger set_major_catalog_favorites_updated_at
before update on public.major_catalog_favorites
for each row execute function public.set_updated_at();

alter table public.major_catalog_favorites enable row level security;

drop policy if exists "users can read own major catalog favorites"
  on public.major_catalog_favorites;
create policy "users can read own major catalog favorites"
  on public.major_catalog_favorites for select
  using (auth.uid() = user_id);

drop policy if exists "users can insert own major catalog favorites"
  on public.major_catalog_favorites;
create policy "users can insert own major catalog favorites"
  on public.major_catalog_favorites for insert
  with check (auth.uid() = user_id);

drop policy if exists "users can update own major catalog favorites"
  on public.major_catalog_favorites;
create policy "users can update own major catalog favorites"
  on public.major_catalog_favorites for update
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "users can delete own major catalog favorites"
  on public.major_catalog_favorites;
create policy "users can delete own major catalog favorites"
  on public.major_catalog_favorites for delete
  using (auth.uid() = user_id);

-- 所有收藏读写均经由后端 service-role 进行，浏览器端不直连该表。
revoke all on table public.major_catalog_favorites from anon, authenticated;
