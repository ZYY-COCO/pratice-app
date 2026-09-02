-- 前辈资格取消后的重新申请约束。
-- 执行位置：Supabase SQL Editor。
-- 前置依赖：database/mentor_qualification_revocation.sql。
--
-- 历史认证、前辈档案、订单、聊天、评价和统计均保留；本迁移只保证
-- 同一账号任一时刻最多存在一条待审核申请，避免弱网重试或连续点击重复提交。

begin;

create unique index if not exists uq_mentor_applications_one_pending_per_user
  on public.mentor_verification_applications (applicant_user_id)
  where application_status = 'pending';

commit;
