-- Official messages and per-user read tracking.
-- Apply this in Supabase before deploying the official-message feature.

create table if not exists public.official_messages (
  id uuid primary key default gen_random_uuid(),
  title text not null,
  content text not null,
  status text not null default 'draft',
  published_at timestamptz,
  expires_at timestamptz,
  created_by uuid references public.users(id) on delete set null,
  updated_by uuid references public.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint official_messages_status_check
    check (status in ('draft', 'published', 'archived'))
);

create table if not exists public.user_official_message_reads (
  user_id uuid not null references public.users(id) on delete cascade,
  message_id uuid not null references public.official_messages(id) on delete cascade,
  read_at timestamptz not null default now(),
  primary key (user_id, message_id)
);

create index if not exists idx_official_messages_status_published
  on public.official_messages(status, published_at desc);

create index if not exists idx_user_official_message_reads_user
  on public.user_official_message_reads(user_id, read_at desc);

alter table public.official_messages enable row level security;
alter table public.user_official_message_reads enable row level security;

-- The backend uses the service-role key for official-message APIs; no direct client policy is granted here.
