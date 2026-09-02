-- 前辈咨询真实数据结构。
-- 执行位置：Supabase SQL Editor。
-- 前置依赖：database/supabase_schema.sql、database/admin_management.sql。
-- 后端统一使用 service role 访问；前端只通过 FastAPI API 读取公开信息。

create extension if not exists "pgcrypto";

create table if not exists public.mentor_profiles (
  id uuid primary key default gen_random_uuid(),
  owner_user_id uuid unique references public.users(id) on delete set null,
  legal_name text not null check (char_length(btrim(legal_name)) between 2 and 40),
  display_name text not null check (char_length(btrim(display_name)) between 2 and 40),
  avatar_label text not null default '研' check (char_length(btrim(avatar_label)) between 1 and 4),
  avatar_url text,
  avatar_tone text not null default 'blue'
    check (avatar_tone in ('mint', 'blue', 'warm', 'violet')),
  school text not null check (char_length(btrim(school)) between 1 and 120),
  major text not null check (char_length(btrim(major)) between 1 and 120),
  admission_year smallint not null check (admission_year between 2000 and 2100),
  graduation_year smallint check (graduation_year between 2000 and 2100),
  exam_type text not null
    check (exam_type in ('Z001', 'Z002', 'application')),
  score smallint not null check (score between 0 and 150),
  bio text not null default '' check (char_length(bio) <= 500),
  story text not null default '' check (char_length(story) <= 2000),
  price_cents integer not null default 3900 check (price_cents between 0 and 100000),
  consultation_window_minutes smallint not null default 60
    check (consultation_window_minutes between 15 and 180),
  consultation_enabled boolean not null default true,
  online_status text not null default 'offline'
    check (online_status in ('online', 'offline', 'busy')),
  accepts_booking boolean not null default true,
  verification_status text not null default 'pending'
    check (verification_status in ('unverified', 'pending', 'verified', 'rejected')),
  is_published boolean not null default false,
  is_featured boolean not null default false,
  recommend_score integer not null default 0 check (recommend_score between 0 and 100),
  rating numeric(2, 1) not null default 0 check (rating between 0 and 5),
  rating_count integer not null default 0 check (rating_count >= 0),
  consult_count integer not null default 0 check (consult_count >= 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (graduation_year is null or graduation_year >= admission_year)
);

create table if not exists public.mentor_profile_skills (
  mentor_id uuid not null references public.mentor_profiles(id) on delete cascade,
  skill text not null check (char_length(btrim(skill)) between 1 and 40),
  sort_order smallint not null default 0 check (sort_order between 0 and 99),
  created_at timestamptz not null default now(),
  primary key (mentor_id, skill)
);

create table if not exists public.mentor_availability_slots (
  id uuid primary key default gen_random_uuid(),
  mentor_id uuid not null references public.mentor_profiles(id) on delete cascade,
  starts_at timestamptz not null,
  ends_at timestamptz not null,
  price_cents integer check (price_cents between 0 and 100000),
  status text not null default 'available'
    check (status in ('available', 'booked', 'expired', 'closed')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (ends_at > starts_at)
);

create table if not exists public.mentor_consultation_orders (
  id uuid primary key default gen_random_uuid(),
  order_no text not null unique,
  applicant_user_id uuid not null references public.users(id) on delete restrict,
  mentor_id uuid not null references public.mentor_profiles(id) on delete restrict,
  slot_id uuid references public.mentor_availability_slots(id) on delete set null,
  consultation_type text not null check (consultation_type in ('instant', 'booking')),
  order_status text not null default 'draft'
    check (order_status in ('draft', 'pending_payment', 'pending_accept', 'accepted', 'in_progress', 'completed', 'rejected', 'timeout', 'refunded', 'cancelled', 'booked')),
  payment_status text not null default 'unpaid'
    check (payment_status in ('unpaid', 'paid', 'refunding', 'refunded', 'failed')),
  questionnaire jsonb not null default '{}'::jsonb check (jsonb_typeof(questionnaire) = 'object'),
  price_cents integer not null check (price_cents between 0 and 100000),
  consultation_window_minutes smallint not null default 60
    check (consultation_window_minutes between 15 and 180),
  payment_reference text,
  accepted_at timestamptz,
  expires_at timestamptz,
  started_at timestamptz,
  ended_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists public.mentor_consultation_messages (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null references public.mentor_consultation_orders(id) on delete cascade,
  sender_role text not null check (sender_role in ('applicant', 'mentor', 'system')),
  sender_user_id uuid references public.users(id) on delete set null,
  message_type text not null default 'text'
    check (message_type in ('text', 'image', 'voice', 'system')),
  content text not null default '' check (char_length(content) <= 5000),
  media_url text,
  duration_seconds integer check (duration_seconds between 0 and 3600),
  client_message_id text,
  created_at timestamptz not null default now()
);

create table if not exists public.mentor_reviews (
  id uuid primary key default gen_random_uuid(),
  order_id uuid not null unique references public.mentor_consultation_orders(id) on delete cascade,
  mentor_id uuid not null references public.mentor_profiles(id) on delete cascade,
  reviewer_user_id uuid references public.users(id) on delete set null,
  reviewer_display_name text not null default '匿名用户',
  rating numeric(2, 1) not null check (rating between 1 and 5),
  tags jsonb not null default '[]'::jsonb check (jsonb_typeof(tags) = 'array'),
  content text not null default '' check (char_length(content) <= 300),
  is_published boolean not null default true,
  created_at timestamptz not null default now()
);

create table if not exists public.mentor_favorites (
  user_id uuid not null references public.users(id) on delete cascade,
  mentor_id uuid not null references public.mentor_profiles(id) on delete cascade,
  created_at timestamptz not null default now(),
  primary key (user_id, mentor_id)
);

create table if not exists public.mentor_verification_applications (
  id uuid primary key default gen_random_uuid(),
  applicant_user_id uuid not null references public.users(id) on delete cascade,
  legal_name text not null check (char_length(btrim(legal_name)) between 2 and 40),
  school text not null check (char_length(btrim(school)) between 1 and 120),
  major text not null check (char_length(btrim(major)) between 1 and 120),
  admission_year smallint not null check (admission_year between 2000 and 2100),
  graduation_year smallint check (graduation_year between 2000 and 2100),
  exam_type text not null check (exam_type in ('Z001', 'Z002', 'application')),
  score smallint not null check (score between 0 and 150),
  skills jsonb not null default '[]'::jsonb check (jsonb_typeof(skills) = 'array'),
  bio text not null default '' check (char_length(bio) <= 500),
  price_cents integer not null default 3900 check (price_cents between 0 and 100000),
  consultation_enabled boolean not null default true,
  application_status text not null default 'pending'
    check (application_status in ('pending', 'approved', 'rejected')),
  admin_note text check (char_length(admin_note) <= 1000),
  reviewed_by uuid references public.users(id) on delete set null,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  check (graduation_year is null or graduation_year >= admission_year)
);

create table if not exists public.mentor_verification_documents (
  id uuid primary key default gen_random_uuid(),
  application_id uuid not null references public.mentor_verification_applications(id) on delete cascade,
  file_url text not null,
  file_name text not null check (char_length(btrim(file_name)) between 1 and 255),
  document_type text not null default 'other'
    check (document_type in ('admission_notice', 'student_card', 'other')),
  mime_type text,
  created_at timestamptz not null default now()
);

create index if not exists idx_mentor_profiles_public_list
  on public.mentor_profiles (is_published, verification_status, recommend_score desc, created_at desc);

create index if not exists idx_mentor_profiles_consultation_public_list
  on public.mentor_profiles (
    consultation_enabled,
    is_published,
    verification_status,
    recommend_score desc,
    created_at desc
  );

create index if not exists idx_mentor_profiles_school_major
  on public.mentor_profiles (school, major);

create index if not exists idx_mentor_profiles_owner
  on public.mentor_profiles (owner_user_id)
  where owner_user_id is not null;

create index if not exists idx_mentor_profile_skills_mentor_sort
  on public.mentor_profile_skills (mentor_id, sort_order);

create index if not exists idx_mentor_slots_mentor_start
  on public.mentor_availability_slots (mentor_id, starts_at);

create index if not exists idx_mentor_orders_applicant_created
  on public.mentor_consultation_orders (applicant_user_id, created_at desc);

create index if not exists idx_mentor_orders_mentor_status_created
  on public.mentor_consultation_orders (mentor_id, order_status, created_at desc);

create index if not exists idx_mentor_messages_order_created
  on public.mentor_consultation_messages (order_id, created_at);

create unique index if not exists uq_mentor_messages_client_delivery
  on public.mentor_consultation_messages (order_id, sender_user_id, client_message_id);

create index if not exists idx_mentor_reviews_mentor_created
  on public.mentor_reviews (mentor_id, created_at desc)
  where is_published = true;

create index if not exists idx_mentor_applications_status_created
  on public.mentor_verification_applications (application_status, created_at desc);

drop trigger if exists set_mentor_profiles_updated_at on public.mentor_profiles;
create trigger set_mentor_profiles_updated_at
before update on public.mentor_profiles
for each row execute function public.set_updated_at();

drop trigger if exists set_mentor_slots_updated_at on public.mentor_availability_slots;
create trigger set_mentor_slots_updated_at
before update on public.mentor_availability_slots
for each row execute function public.set_updated_at();

drop trigger if exists set_mentor_orders_updated_at on public.mentor_consultation_orders;
create trigger set_mentor_orders_updated_at
before update on public.mentor_consultation_orders
for each row execute function public.set_updated_at();

drop trigger if exists set_mentor_applications_updated_at on public.mentor_verification_applications;
create trigger set_mentor_applications_updated_at
before update on public.mentor_verification_applications
for each row execute function public.set_updated_at();

alter table public.mentor_profiles enable row level security;
alter table public.mentor_profile_skills enable row level security;
alter table public.mentor_availability_slots enable row level security;
alter table public.mentor_consultation_orders enable row level security;
alter table public.mentor_consultation_messages enable row level security;
alter table public.mentor_reviews enable row level security;
alter table public.mentor_favorites enable row level security;
alter table public.mentor_verification_applications enable row level security;
alter table public.mentor_verification_documents enable row level security;

drop policy if exists "published verified mentors are readable" on public.mentor_profiles;
create policy "published verified mentors are readable"
  on public.mentor_profiles for select
  using (consultation_enabled = true and is_published = true and verification_status = 'verified');

drop policy if exists "published mentor skills are readable" on public.mentor_profile_skills;
create policy "published mentor skills are readable"
  on public.mentor_profile_skills for select
  using (
    exists (
      select 1 from public.mentor_profiles profile
      where profile.id = mentor_id
        and profile.consultation_enabled = true
        and profile.is_published = true
        and profile.verification_status = 'verified'
    )
  );

drop policy if exists "published mentor slots are readable" on public.mentor_availability_slots;
create policy "published mentor slots are readable"
  on public.mentor_availability_slots for select
  using (
    exists (
      select 1 from public.mentor_profiles profile
      where profile.id = mentor_id
        and profile.consultation_enabled = true
        and profile.is_published = true
        and profile.verification_status = 'verified'
    )
  );

drop policy if exists "published mentor reviews are readable" on public.mentor_reviews;
create policy "published mentor reviews are readable"
  on public.mentor_reviews for select
  using (
    is_published = true
    and exists (
      select 1 from public.mentor_profiles profile
      where profile.id = mentor_id
        and profile.consultation_enabled = true
        and profile.is_published = true
        and profile.verification_status = 'verified'
    )
  );

drop policy if exists "users can manage own mentor favorites" on public.mentor_favorites;
create policy "users can manage own mentor favorites"
  on public.mentor_favorites for all
  using (auth.uid() = user_id)
  with check (auth.uid() = user_id);

drop policy if exists "users can read own mentor orders" on public.mentor_consultation_orders;
create policy "users can read own mentor orders"
  on public.mentor_consultation_orders for select
  using (
    auth.uid() = applicant_user_id
    or exists (
      select 1 from public.mentor_profiles profile
      where profile.id = mentor_id and profile.owner_user_id = auth.uid()
    )
  );

drop policy if exists "consultation participants can read messages" on public.mentor_consultation_messages;
create policy "consultation participants can read messages"
  on public.mentor_consultation_messages for select
  using (
    exists (
      select 1
      from public.mentor_consultation_orders orders
      left join public.mentor_profiles profile on profile.id = orders.mentor_id
      where orders.id = order_id
        and (orders.applicant_user_id = auth.uid() or profile.owner_user_id = auth.uid())
    )
  );

drop policy if exists "users can read own mentor applications" on public.mentor_verification_applications;
create policy "users can read own mentor applications"
  on public.mentor_verification_applications for select
  using (auth.uid() = applicant_user_id);

drop policy if exists "users can read own mentor verification documents" on public.mentor_verification_documents;
create policy "users can read own mentor verification documents"
  on public.mentor_verification_documents for select
  using (
    exists (
      select 1 from public.mentor_verification_applications application
      where application.id = application_id and application.applicant_user_id = auth.uid()
    )
  );

-- 初始唯一公开前辈：钟*宏。owner_user_id 暂为空，后续在后台绑定其真实账号即可。
insert into public.mentor_profiles (
  id,
  owner_user_id,
  legal_name,
  display_name,
  avatar_label,
  avatar_tone,
  school,
  major,
  admission_year,
  graduation_year,
  exam_type,
  score,
  bio,
  story,
  price_cents,
  consultation_window_minutes,
  consultation_enabled,
  online_status,
  accepts_booking,
  verification_status,
  is_published,
  is_featured,
  recommend_score,
  rating,
  rating_count,
  consult_count
)
values (
  'b33c7c94-8c87-4c2f-9253-c9d4a02b1001',
  null,
  '钟源宏',
  '钟*宏',
  '钟',
  'blue',
  '暨南大学',
  '应用经济学',
  2025,
  2027,
  'Z001',
  110,
  '2025 年港澳台研究生考试上岸，熟悉院校选择、Z001 备考以及复试准备，可以帮助分析备考规划和目标院校情况。',
  '2025 年通过港澳台研究生招生考试录取至暨南大学应用经济学专业，初试 110 分，复试综合排名靠前。',
  3900,
  60,
  true,
  'online',
  true,
  'verified',
  true,
  true,
  98,
  0,
  0,
  0
)
on conflict (id) do update
set legal_name = excluded.legal_name,
    display_name = excluded.display_name,
    avatar_label = excluded.avatar_label,
    avatar_tone = excluded.avatar_tone,
    school = excluded.school,
    major = excluded.major,
    admission_year = excluded.admission_year,
    graduation_year = excluded.graduation_year,
    exam_type = excluded.exam_type,
    score = excluded.score,
    bio = excluded.bio,
    story = excluded.story,
    price_cents = excluded.price_cents,
    consultation_window_minutes = excluded.consultation_window_minutes,
    consultation_enabled = excluded.consultation_enabled,
    online_status = excluded.online_status,
    accepts_booking = excluded.accepts_booking,
    verification_status = excluded.verification_status,
    is_published = excluded.is_published,
    is_featured = excluded.is_featured,
    recommend_score = excluded.recommend_score,
    rating = excluded.rating,
    rating_count = excluded.rating_count,
    consult_count = excluded.consult_count,
    updated_at = now();

insert into public.mentor_profile_skills (mentor_id, skill, sort_order)
values
  ('b33c7c94-8c87-4c2f-9253-c9d4a02b1001', '院校选择', 1),
  ('b33c7c94-8c87-4c2f-9253-c9d4a02b1001', '初试备考', 2),
  ('b33c7c94-8c87-4c2f-9253-c9d4a02b1001', '复试经验', 3)
on conflict (mentor_id, skill) do update
set sort_order = excluded.sort_order;
