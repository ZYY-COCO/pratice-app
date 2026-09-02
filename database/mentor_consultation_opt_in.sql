-- 将“前辈身份认证”与“开通咨询服务”拆分。
-- 旧申请和旧档案保持原有行为，统一视为已开通咨询。

begin;

alter table public.mentor_verification_applications
  add column if not exists consultation_enabled boolean;

update public.mentor_verification_applications
set consultation_enabled = true
where consultation_enabled is null;

alter table public.mentor_verification_applications
  alter column consultation_enabled set default true,
  alter column consultation_enabled set not null;

alter table public.mentor_profiles
  add column if not exists consultation_enabled boolean;

update public.mentor_profiles
set consultation_enabled = true
where consultation_enabled is null;

alter table public.mentor_profiles
  alter column consultation_enabled set default true,
  alter column consultation_enabled set not null;

create index if not exists idx_mentor_profiles_consultation_public_list
  on public.mentor_profiles (
    consultation_enabled,
    is_published,
    verification_status,
    recommend_score desc,
    created_at desc
  );

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

commit;
