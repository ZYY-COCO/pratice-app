-- 前辈咨询评价争议的后台处置契约。
-- 执行位置：Supabase SQL Editor；依赖 mentor_consultation_reports.sql 与 mentor_consultation_dispute_resolution.sql。
-- 评价本身保留原记录，后台仅通过 is_published 控制公开展示；每次裁决仍写入咨询问题反馈、订单事件和管理员操作日志。

begin;

do $$
declare
  constraint_name text;
begin
  for constraint_name in
    select conname
    from pg_constraint
    where conrelid = 'public.mentor_consultation_reports'::regclass
      and contype = 'c'
      and pg_get_constraintdef(oid) like '%resolution%'
  loop
    execute format('alter table public.mentor_consultation_reports drop constraint %I', constraint_name);
  end loop;

  alter table public.mentor_consultation_reports
    add constraint mentor_consultation_reports_resolution_check
    check (
      resolution in (
        'none', 'continue_service', 'refund_full', 'refund_partial',
        'close_service', 'warn_participant', 'hide_review', 'restore_review'
      )
    );
end $$;

commit;
