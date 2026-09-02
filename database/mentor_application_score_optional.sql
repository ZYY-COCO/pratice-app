-- 申请制前辈不填写初试成绩；Z001 / Z002 继续要求 0–150 分。
-- 执行位置：Supabase SQL Editor。
-- 前置依赖：database/mentor_consultation.sql、database/mentor_profile_change_requests.sql。

begin;

alter table public.mentor_profiles
  drop constraint if exists mentor_profiles_score_check;
alter table public.mentor_profiles
  drop constraint if exists mentor_profiles_exam_score_check;
alter table public.mentor_profiles
  alter column score drop not null;

alter table public.mentor_verification_applications
  drop constraint if exists mentor_verification_applications_score_check;
alter table public.mentor_verification_applications
  drop constraint if exists mentor_verification_applications_exam_score_check;
alter table public.mentor_verification_applications
  alter column score drop not null;

alter table public.mentor_profile_change_requests
  drop constraint if exists mentor_profile_change_requests_score_check;
alter table public.mentor_profile_change_requests
  drop constraint if exists mentor_profile_change_requests_exam_score_check;
alter table public.mentor_profile_change_requests
  alter column score drop not null;

-- 清理旧版前端为申请制写入的占位 0 分，避免前台继续展示“初试 0 分”。
update public.mentor_profiles
set score = null
where exam_type = 'application'
  and score is not null;

update public.mentor_verification_applications
set score = null
where exam_type = 'application'
  and score is not null;

update public.mentor_profile_change_requests
set score = null
where exam_type = 'application'
  and score is not null;

alter table public.mentor_profiles
  add constraint mentor_profiles_exam_score_check check (
    (exam_type = 'application' and score is null)
    or (exam_type in ('Z001', 'Z002') and score is not null and score between 0 and 150)
  );

alter table public.mentor_verification_applications
  add constraint mentor_verification_applications_exam_score_check check (
    (exam_type = 'application' and score is null)
    or (exam_type in ('Z001', 'Z002') and score is not null and score between 0 and 150)
  );

alter table public.mentor_profile_change_requests
  add constraint mentor_profile_change_requests_exam_score_check check (
    (exam_type = 'application' and score is null)
    or (exam_type in ('Z001', 'Z002') and score is not null and score between 0 and 150)
  );

commit;
