-- 未通过及已取消资格前辈申请的后台归档。
-- 执行位置：Supabase SQL Editor。
-- 前置依赖：database/mentor_qualification_revocation.sql。
--
-- 归档只让记录从前辈审核列表中消失；登录账号、前辈档案、证明材料、
-- 咨询订单及审核日志均继续保留。

begin;

alter table public.mentor_verification_applications
  add column if not exists admin_archived_at timestamptz,
  add column if not exists admin_archived_by uuid references public.users(id) on delete set null;

alter table public.mentor_verification_applications
  drop constraint if exists mentor_verification_applications_admin_archive_state_check;

alter table public.mentor_verification_applications
  add constraint mentor_verification_applications_admin_archive_state_check
  check (
    admin_archived_by is null
    or admin_archived_at is not null
  );

create index if not exists idx_mentor_applications_admin_active_list
  on public.mentor_verification_applications (application_status, created_at desc, id desc)
  where admin_archived_at is null;

create index if not exists idx_mentor_applications_admin_archive
  on public.mentor_verification_applications (admin_archived_at desc, id desc)
  where admin_archived_at is not null;

create or replace function public.archive_revoked_mentor_applications(
  p_application_ids uuid[],
  p_admin_user_id uuid
)
returns table(application_id uuid)
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_now timestamptz := now();
  v_requested_ids uuid[];
  v_archived_ids uuid[];
begin
  select coalesce(array_agg(selected_id order by selected_id), array[]::uuid[])
  into v_requested_ids
  from (
    select distinct selected_id
    from unnest(coalesce(p_application_ids, array[]::uuid[])) as selected(selected_id)
  ) as requested;

  if cardinality(v_requested_ids) = 0 then
    return;
  end if;

  with archived as (
    update public.mentor_verification_applications as application
    set
      admin_archived_at = v_now,
      admin_archived_by = p_admin_user_id,
      updated_at = v_now
    where application.id = any(v_requested_ids)
      and application.application_status in ('rejected', 'revoked')
      and application.admin_archived_at is null
    returning application.id
  )
  select coalesce(array_agg(archived.id order by archived.id), array[]::uuid[])
  into v_archived_ids
  from archived;

  if cardinality(v_archived_ids) <> cardinality(v_requested_ids) then
    raise exception 'MENTOR_APPLICATION_ARCHIVE_INELIGIBLE';
  end if;

  return query
  select archived_id
  from unnest(v_archived_ids) as archived(archived_id);
end;
$$;

comment on column public.mentor_verification_applications.admin_archived_at is
  '管理员将未通过或已取消资格申请从前辈审核列表移除的时间。';
comment on function public.archive_revoked_mentor_applications(uuid[], uuid) is
  '原子归档未通过或已取消资格的前辈申请，不删除用户账号或任何历史业务数据。';

revoke all on function public.archive_revoked_mentor_applications(uuid[], uuid)
  from public, anon, authenticated;
grant execute on function public.archive_revoked_mentor_applications(uuid[], uuid)
  to service_role;

commit;

notify pgrst, 'reload schema';
