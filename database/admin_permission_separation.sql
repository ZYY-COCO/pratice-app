-- Correct the historical seed that granted a certified mentor mobile-admin access.
-- Mobile administration now uses public.users.role = 'admin'; the question/operations
-- portal continues to use public.question_admin_access; mentor identity is derived
-- only from the verified mentor profile owned by the user.

begin;

update public.users
set role = 'user'
where lower(email) = '2221073755@qq.com'
  and role = 'admin';

commit;
