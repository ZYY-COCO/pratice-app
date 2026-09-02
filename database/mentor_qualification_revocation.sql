-- 前辈资格取消闭环。
-- 执行位置：Supabase SQL Editor。
-- 前置依赖：database/mentor_consultation.sql。

begin;

alter table public.mentor_profiles
  drop constraint if exists mentor_profiles_verification_status_check;

alter table public.mentor_profiles
  add constraint mentor_profiles_verification_status_check
  check (verification_status in ('unverified', 'pending', 'verified', 'rejected', 'revoked'));

alter table public.mentor_verification_applications
  add column if not exists revocation_reason text,
  add column if not exists revoked_by uuid references public.users(id) on delete set null,
  add column if not exists revoked_at timestamptz;

alter table public.mentor_verification_applications
  drop constraint if exists mentor_verification_applications_application_status_check,
  drop constraint if exists mentor_verification_applications_revocation_reason_check,
  drop constraint if exists mentor_verification_applications_revocation_state_check;

alter table public.mentor_verification_applications
  add constraint mentor_verification_applications_application_status_check
    check (application_status in ('pending', 'approved', 'rejected', 'revoked')),
  add constraint mentor_verification_applications_revocation_reason_check
    check (revocation_reason is null or char_length(btrim(revocation_reason)) between 5 and 1000),
  add constraint mentor_verification_applications_revocation_state_check
    check (
      application_status <> 'revoked'
      or (revoked_at is not null and char_length(btrim(coalesce(revocation_reason, ''))) >= 5)
    );

create or replace function public.revoke_mentor_qualification(
  p_application_id uuid,
  p_admin_user_id uuid,
  p_reason text
)
returns setof public.mentor_verification_applications
language plpgsql
security definer
set search_path = public
as $$
declare
  v_application public.mentor_verification_applications%rowtype;
  v_mentor_id uuid;
  v_reason text := btrim(coalesce(p_reason, ''));
begin
  if char_length(v_reason) < 5 or char_length(v_reason) > 1000 then
    raise exception '资格取消原因需为 5 至 1000 个字';
  end if;

  select *
  into v_application
  from public.mentor_verification_applications
  where id = p_application_id
  for update;

  if not found then
    raise exception '未找到前辈申请';
  end if;

  if v_application.application_status <> 'approved' then
    raise exception '仅可取消当前已通过的前辈资格';
  end if;

  select id
  into v_mentor_id
  from public.mentor_profiles
  where owner_user_id = v_application.applicant_user_id
  for update;

  if not found then
    raise exception '未找到与申请关联的前辈档案';
  end if;

  update public.mentor_profiles
  set verification_status = 'revoked',
      consultation_enabled = false,
      accepts_booking = false,
      online_status = 'offline',
      is_published = false,
      is_featured = false
  where id = v_mentor_id;

  update public.mentor_availability_slots
  set status = 'closed'
  where mentor_id = v_mentor_id
    and status = 'available';

  update public.mentor_verification_applications
  set application_status = 'revoked',
      revocation_reason = v_reason,
      revoked_by = p_admin_user_id,
      revoked_at = now()
  where id = p_application_id
    and application_status = 'approved'
  returning * into v_application;

  if not found then
    raise exception '前辈资格状态已变化，请刷新后重试';
  end if;

  return next v_application;
end;
$$;

revoke all on function public.revoke_mentor_qualification(uuid, uuid, text) from public;
revoke all on function public.revoke_mentor_qualification(uuid, uuid, text) from anon;
revoke all on function public.revoke_mentor_qualification(uuid, uuid, text) from authenticated;
grant execute on function public.revoke_mentor_qualification(uuid, uuid, text) to service_role;

commit;
