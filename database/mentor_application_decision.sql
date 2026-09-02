-- 前辈认证审核快速路径。
-- 执行位置：Supabase SQL Editor。
-- 前置依赖：database/mentor_consultation.sql、database/admin_management.sql、
--           database/mentor_qualification_revocation.sql。
--
-- 将申请锁定、前辈档案建立/恢复、擅长领域同步、申请状态更新和审核日志
-- 合并为一个事务，避免后台审批时多次往返 Supabase。

begin;

create or replace function public.resolve_mentor_verification_application(
  p_application_id uuid,
  p_decision text,
  p_reviewer_user_id uuid,
  p_admin_note text default null
)
returns jsonb
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
  v_application public.mentor_verification_applications%rowtype;
  v_resolved_application public.mentor_verification_applications%rowtype;
  v_decision text := lower(btrim(coalesce(p_decision, '')));
  v_admin_note text := nullif(btrim(coalesce(p_admin_note, '')), '');
  v_mentor_id uuid;
  v_existing_profile_status text;
  v_profile_exists boolean := false;
  v_restored_existing_profile boolean := false;
  v_consultation_enabled boolean;
  v_document_count integer := 0;
begin
  if v_decision not in ('approve', 'reject') then
    raise exception 'MENTOR_APPLICATION_DECISION_UNSUPPORTED';
  end if;

  if v_decision = 'reject' and char_length(coalesce(v_admin_note, '')) < 5 then
    raise exception 'MENTOR_APPLICATION_REJECT_REASON_REQUIRED';
  end if;

  select *
  into v_application
  from public.mentor_verification_applications
  where id = p_application_id
  for update;

  if not found then
    raise exception 'MENTOR_APPLICATION_NOT_FOUND';
  end if;

  if v_application.application_status <> 'pending' then
    raise exception 'MENTOR_APPLICATION_ALREADY_PROCESSED';
  end if;

  if v_decision = 'approve' then
    v_consultation_enabled := coalesce(v_application.consultation_enabled, true);

    select profile.id, profile.verification_status
    into v_mentor_id, v_existing_profile_status
    from public.mentor_profiles profile
    where profile.owner_user_id = v_application.applicant_user_id
    for update;

    v_profile_exists := found;

    if v_profile_exists then
      if v_existing_profile_status <> 'revoked' then
        raise exception 'MENTOR_PROFILE_ALREADY_ACTIVE';
      end if;

      update public.mentor_profiles
      set legal_name = btrim(v_application.legal_name),
          display_name = case
            when char_length(btrim(v_application.legal_name)) <= 1 then btrim(v_application.legal_name)
            when char_length(btrim(v_application.legal_name)) = 2 then left(btrim(v_application.legal_name), 1) || '*'
            else left(btrim(v_application.legal_name), 1) || '*' || right(btrim(v_application.legal_name), 1)
          end,
          avatar_label = left(btrim(v_application.legal_name), 1),
          school = btrim(v_application.school),
          major = btrim(v_application.major),
          admission_year = v_application.admission_year,
          graduation_year = v_application.graduation_year,
          exam_type = v_application.exam_type,
          score = v_application.score,
          bio = coalesce(v_application.bio, ''),
          price_cents = v_application.price_cents,
          online_status = 'offline',
          accepts_booking = v_consultation_enabled,
          consultation_enabled = v_consultation_enabled,
          verification_status = 'verified',
          is_published = true,
          is_featured = false,
          updated_at = now()
      where id = v_mentor_id
        and owner_user_id = v_application.applicant_user_id
        and verification_status = 'revoked';

      if not found then
        raise exception 'MENTOR_PROFILE_STATE_CHANGED';
      end if;

      v_restored_existing_profile := true;
    else
      insert into public.mentor_profiles (
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
        online_status,
        accepts_booking,
        consultation_enabled,
        verification_status,
        is_published,
        is_featured,
        recommend_score,
        rating,
        rating_count,
        consult_count
      ) values (
        v_application.applicant_user_id,
        btrim(v_application.legal_name),
        case
          when char_length(btrim(v_application.legal_name)) <= 1 then btrim(v_application.legal_name)
          when char_length(btrim(v_application.legal_name)) = 2 then left(btrim(v_application.legal_name), 1) || '*'
          else left(btrim(v_application.legal_name), 1) || '*' || right(btrim(v_application.legal_name), 1)
        end,
        left(btrim(v_application.legal_name), 1),
        'blue',
        btrim(v_application.school),
        btrim(v_application.major),
        v_application.admission_year,
        v_application.graduation_year,
        v_application.exam_type,
        v_application.score,
        coalesce(v_application.bio, ''),
        '',
        v_application.price_cents,
        60,
        'offline',
        v_consultation_enabled,
        v_consultation_enabled,
        'verified',
        true,
        false,
        0,
        0,
        0,
        0
      )
      returning id into v_mentor_id;
    end if;

    delete from public.mentor_profile_skills
    where mentor_id = v_mentor_id;

    insert into public.mentor_profile_skills (mentor_id, skill, sort_order)
    select
      v_mentor_id,
      normalized.skill,
      row_number() over (order by normalized.first_position)::smallint
    from (
      select
        left(btrim(skill.value), 40) as skill,
        min(skill.ordinality) as first_position
      from jsonb_array_elements_text(coalesce(v_application.skills, '[]'::jsonb))
        with ordinality as skill(value, ordinality)
      where btrim(skill.value) <> ''
      group by left(btrim(skill.value), 40)
      order by min(skill.ordinality)
      limit 12
    ) normalized;
  end if;

  update public.mentor_verification_applications
  set application_status = case when v_decision = 'approve' then 'approved' else 'rejected' end,
      admin_note = v_admin_note,
      reviewed_by = p_reviewer_user_id,
      reviewed_at = now(),
      revocation_reason = null,
      revoked_by = null,
      revoked_at = null,
      updated_at = now()
  where id = p_application_id
    and application_status = 'pending'
  returning * into v_resolved_application;

  if not found then
    raise exception 'MENTOR_APPLICATION_ALREADY_PROCESSED';
  end if;

  insert into public.admin_action_logs (
    admin_user_id,
    action,
    target_type,
    target_id,
    details
  ) values (
    p_reviewer_user_id,
    case
      when v_decision = 'approve' then 'approve_mentor_application'
      else 'reject_mentor_application'
    end,
    'mentor_verification_application',
    p_application_id,
    jsonb_build_object(
      'mentor_id', v_mentor_id,
      'admin_note', v_admin_note,
      'restored_existing_profile', v_restored_existing_profile
    )
  );

  select count(*)::integer
  into v_document_count
  from public.mentor_verification_documents
  where application_id = p_application_id;

  return jsonb_build_object(
    'application', to_jsonb(v_resolved_application),
    'mentor_id', v_mentor_id,
    'restored_existing_profile', v_restored_existing_profile,
    'document_count', v_document_count
  );
end;
$$;

revoke all on function public.resolve_mentor_verification_application(uuid, text, uuid, text)
  from public, anon, authenticated;
grant execute on function public.resolve_mentor_verification_application(uuid, text, uuid, text)
  to service_role;

-- 让 PostgREST 立即识别新建/替换的 RPC，避免等待 schema cache 自动刷新。
notify pgrst, 'reload schema';

commit;
