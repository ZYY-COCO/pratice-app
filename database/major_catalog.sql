-- 港澳台研究生专业目录。
-- 在 Supabase SQL Editor 执行一次；前端只通过 FastAPI 读取，数据表不直接开放给客户端。

create table if not exists public.major_catalog_import_runs (
  id uuid primary key,
  source_filename text not null,
  source_sha256 text not null,
  source_version text not null,
  source_statistics jsonb not null default '{}'::jsonb,
  status text not null default 'running'
    check (status in ('running', 'completed', 'failed')),
  started_at timestamptz not null default now(),
  completed_at timestamptz,
  failure_reason text
);

create index if not exists idx_major_catalog_import_runs_completed
  on public.major_catalog_import_runs (status, completed_at desc);

create table if not exists public.major_catalog_regions (
  name text primary key,
  sort_order integer not null check (sort_order >= 0),
  school_count integer not null default 0 check (school_count >= 0),
  program_count integer not null default 0 check (program_count >= 0),
  school_count_z001 integer not null default 0 check (school_count_z001 >= 0),
  school_count_z002 integer not null default 0 check (school_count_z002 >= 0),
  program_count_z001 integer not null default 0 check (program_count_z001 >= 0),
  program_count_z002 integer not null default 0 check (program_count_z002 >= 0),
  sync_run_id uuid not null references public.major_catalog_import_runs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.major_catalog_schools (
  id text primary key,
  region_name text not null references public.major_catalog_regions(name)
    on update cascade on delete restrict,
  name text not null,
  sort_order integer not null check (sort_order >= 0),
  exam_codes text[] not null default array[]::text[]
    check (exam_codes <@ array['Z001', 'Z002']::text[]),
  department_count integer not null default 0 check (department_count >= 0),
  program_count integer not null default 0 check (program_count >= 0),
  department_count_z001 integer not null default 0 check (department_count_z001 >= 0),
  department_count_z002 integer not null default 0 check (department_count_z002 >= 0),
  program_count_z001 integer not null default 0 check (program_count_z001 >= 0),
  program_count_z002 integer not null default 0 check (program_count_z002 >= 0),
  sync_run_id uuid not null references public.major_catalog_import_runs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (region_name, name)
);

create index if not exists idx_major_catalog_schools_region_order
  on public.major_catalog_schools (region_name, sort_order, name);

create table if not exists public.major_catalog_departments (
  id text primary key,
  school_id text not null references public.major_catalog_schools(id)
    on update cascade on delete cascade,
  name text not null,
  sort_order integer not null check (sort_order >= 0),
  sync_run_id uuid not null references public.major_catalog_import_runs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (school_id, name)
);

create index if not exists idx_major_catalog_departments_school_order
  on public.major_catalog_departments (school_id, sort_order, name);

create table if not exists public.major_catalog_programs (
  id text primary key,
  school_id text not null references public.major_catalog_schools(id)
    on update cascade on delete cascade,
  department_id text not null references public.major_catalog_departments(id)
    on update cascade on delete cascade,
  name text not null,
  code text not null default '',
  sort_order integer not null check (sort_order >= 0),
  exam_codes text[] not null default array[]::text[]
    check (exam_codes <@ array['Z001', 'Z002']::text[]),
  degree_options text[] not null default array[]::text[],
  study_mode_options text[] not null default array[]::text[],
  direction_count integer not null default 0 check (direction_count >= 0),
  sync_run_id uuid not null references public.major_catalog_import_runs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (department_id, name, code)
);

create index if not exists idx_major_catalog_programs_school_department_order
  on public.major_catalog_programs (school_id, department_id, sort_order, name);

create table if not exists public.major_catalog_directions (
  id text primary key,
  school_id text not null references public.major_catalog_schools(id)
    on update cascade on delete cascade,
  department_id text not null references public.major_catalog_departments(id)
    on update cascade on delete cascade,
  program_id text not null references public.major_catalog_programs(id)
    on update cascade on delete cascade,
  name text not null,
  tutor text not null default '',
  exam_code text not null check (exam_code in ('Z001', 'Z002')),
  degree text not null default '',
  study_mode text not null default '',
  sort_order integer not null check (sort_order >= 0),
  sync_run_id uuid not null references public.major_catalog_import_runs(id),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_major_catalog_directions_school_exam_order
  on public.major_catalog_directions (school_id, exam_code, sort_order);

create index if not exists idx_major_catalog_directions_program_order
  on public.major_catalog_directions (program_id, sort_order);

alter table public.major_catalog_import_runs enable row level security;
alter table public.major_catalog_regions enable row level security;
alter table public.major_catalog_schools enable row level security;
alter table public.major_catalog_departments enable row level security;
alter table public.major_catalog_programs enable row level security;
alter table public.major_catalog_directions enable row level security;

-- 所有目录查询都经由后端 service-role 进行，浏览器端不直连这些表。
revoke all on table public.major_catalog_import_runs from anon, authenticated;
revoke all on table public.major_catalog_regions from anon, authenticated;
revoke all on table public.major_catalog_schools from anon, authenticated;
revoke all on table public.major_catalog_departments from anon, authenticated;
revoke all on table public.major_catalog_programs from anon, authenticated;
revoke all on table public.major_catalog_directions from anon, authenticated;
