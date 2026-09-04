-- Keep question answers, explanations and review metadata behind the FastAPI
-- service-role boundary.  Product clients receive safe question projections
-- from the backend and must not read public.questions through PostgREST.

begin;

drop policy if exists "authenticated users can read questions"
  on public.questions;

-- Supabase projects commonly grant table privileges to API roles by default.
-- Revoke the table privilege first: a column-level REVOKE alone cannot override
-- an existing table-level SELECT grant.
revoke all privileges on table public.questions
  from public, anon, authenticated;

-- Also remove any explicit sensitive-column grants left by an older migration.
revoke select (answer, explanation) on table public.questions
  from public, anon, authenticated;

-- All current question reads and management writes are server-side.
grant select, insert, update, delete on table public.questions
  to service_role;

notify pgrst, 'reload schema';

commit;
