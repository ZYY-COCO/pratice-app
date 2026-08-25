# 第三批：作答可靠性与学习统计口径

更新时间：2026-08-24

## 目标

本批次解决“用户已经作答但记录丢失、弱网重试重复计数、首次作答口径漂移、能力统计与明细不一致”四类问题。

- 作答接口必须在返回成功前确认数据库已经持久化。
- 同一次客户端提交使用稳定的 `client_submission_id`，相同内容重试只返回原记录；同键异文返回 HTTP 409。
- `user_answers` 保留每一次作答；`attempt_number` 和 `is_first_attempt` 固化该题的尝试顺序。
- `user_question_progress` 保存每个用户、每道题的首次作答及累计进度事实。
- “学习范围”只把第一次作答就正确的题计为已学习；能力统计仍按全部真实作答累计。
- `stats_exam_code` 固化作答发生时的考试版本，公共科目按用户版本归属，版本专属科目按题目版本归属。

## 原子写入闭环

正式路径由 `record_answer_submission` 数据库函数在同一事务中完成：

1. 从数据库题目记录重新判定正确答案，不信任客户端正确率。
2. 按“用户 + 题目”加事务级锁，确定首次作答和尝试序号。
3. 写入 `user_answers`。
4. 更新 `user_question_progress`。
5. 答错且不是 AI 临时训练题时，更新 `wrong_questions`。
6. 原子递增 `ability_stats` 并重新计算正确率。
7. 返回持久化记录号、幂等状态、考试归属、尝试序号和最新正确率。

题目已有作答、错题、收藏或 AI 训练引用时，后台物理删除返回 HTTP 409；应改用归档，避免级联删除学习历史。

## 执行迁移

在 Supabase SQL Editor 中完整执行：

```text
database/answer_reliability_and_learning_stats.sql
```

脚本由 `begin` / `commit` 包裹，并在提交时通知 PostgREST 刷新 schema cache；会补齐历史作答字段，并从 `user_answers` 重建 `user_question_progress` 和 `ability_stats`。这两个表是派生数据，重建不会删除作答明细。

如果 SQL Editor 返回 `40P01: deadlock detected`，本次事务已经整体回滚。先等待其他查询结束，并确认没有另一个 SQL 标签页同时执行迁移，再重新运行完整脚本；不要从报错行或脚本中段继续执行。

迁移同时关闭 `authenticated` / `anon` 对作答、错题和能力统计表的直接写权限。正式客户端统一经过 FastAPI，由 service role 调用原子函数；各表自己的只读策略保留。

## 迁移后只读核验

以下查询均应返回 `0`：

```sql
-- 每个“用户 + 题目”只能有一条首次作答。
select count(*)
from (
  select user_id, question_id
  from public.user_answers
  group by user_id, question_id
  having count(*) filter (where is_first_attempt) <> 1
) invalid_first_attempt_groups;

-- 尝试序号必须从 1 连续排列。
select count(*)
from (
  select user_id, question_id
  from public.user_answers
  group by user_id, question_id
  having min(attempt_number) <> 1
     or max(attempt_number) <> count(*)
     or count(distinct attempt_number) <> count(*)
) invalid_attempt_sequences;

-- 进度表必须和作答明细一一覆盖。
select count(*)
from (
  select user_id, question_id from public.user_answers group by user_id, question_id
  except
  select user_id, question_id from public.user_question_progress
) missing_progress_rows;
```

函数和索引存在性核验：

```sql
select to_regprocedure(
  'public.record_answer_submission(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamp with time zone)'
) as answer_rpc;

select to_regclass('public.uq_user_answers_client_submission') as idempotency_index;
```

## 本地验收重点

- 正常单题：只新增一条作答，历史、错题本和学习报告同步更新。
- 弱网重试：重复点击或请求超时后重试，不重复增加作答数和错误次数。
- 同键异文：同一个 `client_submission_id` 改答案重发，接口返回 409。
- 综合练习：批量请求中途失败后逐题补交，已经成功的题走幂等返回。
- 首次答错后答对：学习范围仍不增加，但作答次数和能力统计正常增加。
- 首次答对后答错：学习范围保持已学习，错题本新增或累计。
- Z002 用户作答中华文化/英语运用公共题：历史和报告归入 Z002。
- 已有学习记录的题目：后台物理删除提示改用归档。

迁移尚未执行时，后端会走同步兼容路径维持本地页面可用；并发原子性、数据库级幂等和新的首次作答事实以迁移执行完成为生效边界。
