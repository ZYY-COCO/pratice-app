-- Profile settings fields for the personal profile page.
-- Apply this in Supabase before using avatar/gender and email binding updates.

alter table public.users
  add column if not exists avatar_url text,
  add column if not exists gender text;

alter table public.users
  drop constraint if exists users_gender_check;

alter table public.users
  add constraint users_gender_check
  check (gender is null or gender in ('male', 'female'));

alter table public.auth_email_codes
  drop constraint if exists auth_email_codes_purpose_check;

alter table public.auth_email_codes
  add constraint auth_email_codes_purpose_check
  check (purpose in ('register', 'reset_password', 'change_email'));
