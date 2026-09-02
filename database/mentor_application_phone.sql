begin;

alter table public.mentor_verification_applications
  add column if not exists phone text;

alter table public.mentor_verification_applications
  drop constraint if exists mentor_verification_applications_phone_check;

alter table public.mentor_verification_applications
  add constraint mentor_verification_applications_phone_check
  check (phone is null or phone ~ '^[0-9]{11}$');

comment on column public.mentor_verification_applications.phone is
  '认证申请联系电话，仅供申请人本人和平台审核使用，不进入公开前辈资料。历史申请可为空，新申请由 API 强制填写 11 位数字。';

commit;
