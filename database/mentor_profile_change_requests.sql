-- 前辈资料修改审核申请。
-- 执行位置：Supabase SQL Editor。
-- 前置依赖：database/mentor_consultation.sql、database/admin_management.sql。
-- 设计原则：前辈提交修改时不直接覆盖 mentor_profiles；管理员批准后才原子更新公开档案。

create table if not exists public.mentor_profile_change_requests (
  id uuid primary key default gen_random_uuid(),
  mentor_id uuid not null references public.mentor_profiles(id) on delete cascade,
  owner_user_id uuid not null references public.users(id) on delete cascade,
  school text not null check (char_length(btrim(school)) between 1 and 120),
  major text not null check (char_length(btrim(major)) between 1 and 120),
  exam_type text not null check (exam_type in ('Z001', 'Z002', 'application')),
  score smallint,
  skills jsonb not null default '[]'::jsonb check (jsonb_typeof(skills) = 'array'),
  bio text not null default '' check (char_length(bio) <= 500),
  price_cents integer not null check (price_cents between 0 and 100000),
  request_status text not null default 'pending'
    check (request_status in ('pending', 'approved', 'rejected')),
  admin_note text check (char_length(admin_note) <= 1000),
  reviewed_by uuid references public.users(id) on delete set null,
  reviewed_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint mentor_profile_change_requests_exam_score_check check (
    (exam_type = 'application' and score is null)
    or (exam_type in ('Z001', 'Z002') and score is not null and score between 0 and 150)
  )
);

create index if not exists idx_mentor_profile_change_requests_owner_created
  on public.mentor_profile_change_requests (owner_user_id, created_at desc);

create index if not exists idx_mentor_profile_change_requests_status_created
  on public.mentor_profile_change_requests (request_status, created_at desc);

create unique index if not exists uq_mentor_profile_change_requests_pending
  on public.mentor_profile_change_requests (mentor_id)
  where request_status = 'pending';

drop trigger if exists set_mentor_profile_change_requests_updated_at on public.mentor_profile_change_requests;
create trigger set_mentor_profile_change_requests_updated_at
before update on public.mentor_profile_change_requests
for each row execute function public.set_updated_at();

alter table public.mentor_profile_change_requests enable row level security;

drop policy if exists "owners can read own mentor profile change requests" on public.mentor_profile_change_requests;
create policy "owners can read own mentor profile change requests"
  on public.mentor_profile_change_requests for select
  using (auth.uid() = owner_user_id);

drop policy if exists "owners can create own mentor profile change requests" on public.mentor_profile_change_requests;
create policy "owners can create own mentor profile change requests"
  on public.mentor_profile_change_requests for insert
  with check (
    auth.uid() = owner_user_id
    and exists (
      select 1
      from public.mentor_profiles profile
      where profile.id = mentor_id
        and profile.owner_user_id = auth.uid()
    )
  );

create or replace function public.resolve_mentor_profile_change_request(
  p_request_id uuid,
  p_decision text,
  p_reviewer_user_id uuid,
  p_admin_note text default null
)
returns public.mentor_profile_change_requests
language plpgsql
security definer
set search_path = public
as $$
declare
  request_row public.mentor_profile_change_requests%rowtype;
  resolved_row public.mentor_profile_change_requests%rowtype;
  normalized_note text;
begin
  if p_decision not in ('approve', 'reject') then
    raise exception 'unsupported decision';
  end if;

  select *
  into request_row
  from public.mentor_profile_change_requests
  where id = p_request_id
  for update;

  if not found then
    raise exception 'mentor profile change request not found';
  end if;

  if request_row.request_status <> 'pending' then
    raise exception 'mentor profile change request already processed';
  end if;

  normalized_note := nullif(btrim(coalesce(p_admin_note, '')), '');

  if p_decision = 'approve' then
    update public.mentor_profiles
    set school = request_row.school,
        major = request_row.major,
        exam_type = request_row.exam_type,
        score = request_row.score,
        bio = request_row.bio,
        price_cents = request_row.price_cents,
        updated_at = now()
    where id = request_row.mentor_id
      and owner_user_id = request_row.owner_user_id;

    if not found then
      raise exception 'mentor profile owner binding changed';
    end if;

    delete from public.mentor_profile_skills
    where mentor_id = request_row.mentor_id;

    insert into public.mentor_profile_skills (mentor_id, skill, sort_order)
    select
      request_row.mentor_id,
      skill.value,
      skill.ordinality::smallint
    from jsonb_array_elements_text(request_row.skills) with ordinality as skill(value, ordinality);
  end if;

  update public.mentor_profile_change_requests
  set request_status = case when p_decision = 'approve' then 'approved' else 'rejected' end,
      admin_note = normalized_note,
      reviewed_by = p_reviewer_user_id,
      reviewed_at = now(),
      updated_at = now()
  where id = request_row.id
    and request_status = 'pending'
  returning * into resolved_row;

  if not found then
    raise exception 'mentor profile change request already processed';
  end if;

  return resolved_row;
end;
$$;

revoke all on function public.resolve_mentor_profile_change_request(uuid, text, uuid, text) from public;
grant execute on function public.resolve_mentor_profile_change_request(uuid, text, uuid, text) to service_role;
