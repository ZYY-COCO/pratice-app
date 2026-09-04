# 个性化普通刷题迁移预检（2026-09-04）

本文记录 2026-09-04 对当前远端数据库进行的迁移预检、已审核 predecessor 合同、实际执行结果与后续部署门禁。可直接运行的只读核验脚本为 `database/adaptive_comprehensive_practice_verification.sql`，已覆盖综合基础、候选历史查询、整卷批量持久化、候选新鲜度加固和题库读取权限边界。记录中不保存任何环境变量值、密钥或连接串。

## 1. 结论

迁移前远端不是全新环境，而是“较早版本第一层已经存在、第二层综合刷题增量尚未应用”的升级环境：

- REST 可达，服务端角色的只读访问有效；前置字段齐全。
- 第一层 8 张自适应表均存在：`user_subject_state`、`user_topic_state`、`practice_sessions`、`practice_session_items`、`practice_session_item_question_snapshots`、`question_calibration`、`adaptive_model_updates`、`adaptive_conflicts`。
- 第一层专项 RPC 存在。只读预检时，自适应表均为 0 行，`ACTIVE` 自适应会话为 0。
- 同一时点的业务基线为：`user_answers=2819`、`wrong_questions=879`、`user_question_progress=2182`。这些只是迁移前核对基线，不是长期固定值；正式执行前必须重新读取。
- `record_answer_submission` 仍处于旧的 13 参数公开签名；重命名后的 13 参数私有核心不存在，新的 17 参数公开包装器不存在。
- 第二层 5 个综合 RPC 均不存在：`claim_adaptive_comprehensive_practice_items`、`assert_single_answer_feedback_allowed`、`begin_adaptive_comprehensive_submission`、`record_adaptive_comprehensive_skip`、`finalize_adaptive_comprehensive_submission`。
- 迁移前，`get_adaptive_candidate_history_v1` 与 `persist_adaptive_comprehensive_answers_batch` 两个 RPC 均不存在；执行窗口已用函数签名、正文 hash、ACL 和 PostgREST schema cache 明确核验迁移结果。
- 迁移前的 `validate_practice_session_item_scope` 来自既有第一层；旧定义已经保存，执行后已匹配本地加固正文与 trigger 绑定。
- Dashboard 已独立确认目标项目、project ref、`main / Production`、Tokyo、Healthy；配置所指 host 与该 ref 一致。项目标识只保存在仓库外证据包，不写入本文。
- 当前 Free 计划明确显示 `No backups`，没有 scheduled backup 或 PITR。用户已于 2026-09-04 接受以仓库外定向逻辑回退包继续；该选择只覆盖本次五份事务型迁移的目标对象，不等同于全库灾难恢复能力。
- 四个原先报告为漂移的函数已完成逐正文审查：它们是综合交卷隔离加入前的已知 production predecessor，不是未知改动。综合增量现已在事务第一条 DDL 前强制检查签名、允许 hash、volatility、`SECURITY DEFINER`、固定 `search_path`、owner、精确 ACL、迁移状态和 `ACTIVE=0`；不匹配会让整笔事务退出。
- 2026-09-04 已按顺序正式提交四份自适应增量和题库读取权限增量。最终门禁核验了 13 个函数，正文、owner、安全属性、固定 `search_path` 与角色权限全部通过；候选历史索引和 freshness trigger 有效，旧 13 参数公开函数已消失，私有核心对 `service_role` 也无直接执行权。
- 实际迁移窗口前后业务行数保持 `user_answers=2844`、`wrong_questions=890`、`user_question_progress=2207`，8 张自适应表均为 0 行，`ACTIVE=0`。没有导入题目或诊断校准；应用代码仍待部署，总开关继续关闭。
- 题表权限硬化后，`PUBLIC/anon/authenticated` 对整表和全部 32 列均无读取权，`service_role` 保留 CRUD；匿名 PostgREST 读取题干及答案投影均返回 `42501`，线上 FastAPI 健康检查和两个学科的题库统计接口继续返回 200。

本次执行顺序为：`database/adaptive_comprehensive_practice_v1.sql` → `database/adaptive_candidate_history_lookup_v1.sql` → `database/adaptive_comprehensive_submission_batch_v1.sql` → `database/adaptive_candidate_freshness_hardening.sql` → 完整只读核验 → `database/question_answer_read_access_hardening.sql` → 权限复核与应用冒烟，现已全部完成数据库阶段。`database/adaptive_question_delivery_v1.sql` 包含历史派生状态重建、表锁和清空后重建步骤，今后仍禁止在这个已经有第一层对象的远端重新执行，也禁止把它当作回滚脚本。

## 2. 执行前置与实际结果

以下四项已在进入执行窗口前完成并留存证据：

1. **独立确认项目身份（已完成）**：已在 Dashboard 核对显示名、project ref、组织、环境/分支、区域与健康状态，并与配置所指 host 匹配。
2. **建立本次迁移的定向逻辑回退包（已完成，接受无 PITR 风险）**：仓库外受控回退目录（具体路径不入库）已保存目标函数完整定义与元数据、三张业务表、`ability_stats`、8 张自适应表、题表原始 ACL/全部列 ACL/owner/RLS/policy、trigger 与相关索引。所有 JSON 均已解析并计算 SHA-256；执行窗口已重读行数并补充每步核验与最终发布门禁。
3. **完成 predecessor 审查与事务门禁（已完成）**：四个较早函数正文已逐项比较并确认为综合隔离前版本；完整综合迁移已在真实 PostgreSQL 中用最终 `ROLLBACK` 演练成功。正式执行时迁移自身会再次执行强制门禁。
4. **保存并核验题库读取权限（已完成）**：`public.questions` 的原始 `relacl`、32 列 `attacl`、owner、RLS/force-RLS 与全部 policy 已保存；权限硬化在四个自适应增量全部核验通过后提交，前端仍只经 FastAPI 读取题目。

迁移、部署和核验期间继续保持 `ADAPTIVE_PRACTICE_ENABLED=false`。

## 3. body hash 口径

本文的 body hash 固定为 PostgreSQL 系统目录中函数正文的：

```sql
md5(btrim(replace(pg_proc.prosrc, chr(13), ''), E' \t\n'))
```

它不是 SQL 文件哈希，也不是 `pg_get_functiondef` 整段 DDL 的哈希。建议在 SQL Editor 中保存以下只读查询结果：

```sql
select
  p.oid::regprocedure::text as function_signature,
  md5(btrim(replace(p.prosrc, chr(13), ''), E' \t\n')) as body_md5,
  p.prosecdef as security_definer,
  p.proconfig as function_config,
  pg_get_userbyid(p.proowner) as owner_name,
  p.proacl,
  pg_get_functiondef(p.oid) as function_definition,
  has_function_privilege('anon', p.oid, 'EXECUTE') as anon_can_execute,
  has_function_privilege('authenticated', p.oid, 'EXECUTE') as authenticated_can_execute,
  has_function_privilege('service_role', p.oid, 'EXECUTE') as service_role_can_execute,
  obj_description(p.oid, 'pg_proc') as function_comment
from pg_proc p
join pg_namespace n on n.oid = p.pronamespace
where n.nspname = 'public'
  and p.proname in (
    'claim_next_adaptive_practice_item',
    'apply_adaptive_model_update',
    'get_adaptive_question_snapshot',
    'record_practice_session_item_event',
    'complete_practice_session',
    'get_pending_adaptive_update_items',
    'record_answer_submission',
    'record_answer_submission_pre_comprehensive_v1',
    'claim_adaptive_comprehensive_practice_items',
    'assert_single_answer_feedback_allowed',
    'begin_adaptive_comprehensive_submission',
    'record_adaptive_comprehensive_skip',
    'finalize_adaptive_comprehensive_submission',
    'get_adaptive_candidate_history_v1',
    'persist_adaptive_comprehensive_answers_batch',
    'validate_practice_session_item_scope'
  )
order by p.oid::regprocedure::text;
```

迁移前允许的 predecessor 如下。斜线左侧是 2026-09-04 已捕获并审阅的 production predecessor；右侧是已带综合隔离保护的较新第一层正文。只有表中列出的 hash 可以进入升级：

| 函数 | `md5(btrim(replace(prosrc, chr(13), ''), E' \t\n'))` |
| --- | --- |
| `claim_next_adaptive_practice_item` | `a49e0d6863b722198224766e2295f1da` |
| `apply_adaptive_model_update` | `9dcb9ac1196ce9af928bf439a1f2b005` |
| `get_adaptive_question_snapshot` | `d2e2be3a78f1a5b9522c639be8729de7` / `7255f4d5a37a55bd49ec09c78c66f6ad` |
| `record_practice_session_item_event` | `73bfd2b45fa01b4535aa703222d5a676` / `42b4400fa3fdc080055d11849807976b` |
| `complete_practice_session` | `b1557754912e57cddcdad7c7062d9df7` / `c945ae789dd4ad8074902b857dd356b0` |
| `get_pending_adaptive_update_items` | `3f09faf68c2a5ecd1c0fa6ce541c9334` / `a4f121c8006d6b4b4046c85f242834c4` |
| 13 参数 `record_answer_submission` | `d377f77e8a3cf4fc85c6b4e49b52fcc9` |
| `validate_practice_session_item_scope` | `6fd9e1cfe1d526a36a64b52e014c4dd1` |

以上函数还必须满足表中约定的 volatility、`security_definer=true`、`search_path=public, pg_temp`、owner 为 `postgres`，且迁移前 ACL 精确为 `{postgres=X/postgres,service_role=X/postgres}`。若任一条件不一致，综合迁移事务会在首个 schema change 前退出。

四个自适应增量执行成功后，新增或升级入口的本地期望值为：

| 函数 | `md5(btrim(replace(prosrc, chr(13), ''), E' \t\n'))` |
| --- | --- |
| `claim_adaptive_comprehensive_practice_items` | `1b070654e9337b5e8d113d2a9f798c81` |
| `assert_single_answer_feedback_allowed` | `0382bd8997279101224bd667ab9bdaef` |
| 17 参数 `record_answer_submission` 包装器 | `72f23b7a4623aa444bbc4f06fccec579` |
| `begin_adaptive_comprehensive_submission` | `db863dbf366415d83a900a9a42c3d906` |
| `record_adaptive_comprehensive_skip` | `a25564b1b963bc22b2374e2f183791d7` |
| `finalize_adaptive_comprehensive_submission` | `15d5dc19d6ed37acb2c69c3e1cfb7e39` |
| `get_adaptive_candidate_history_v1` | `e6adb88c8664395872268e9d72686fa2` |
| `persist_adaptive_comprehensive_answers_batch` | `6e58a83fc2e468fcad46435d4a4e8456` |
| `validate_practice_session_item_scope` | `44d6eb45883359e4b129e26b1e7bf4e5` |

第二层会就地刷新 `get_adaptive_question_snapshot`、`record_practice_session_item_event`、`complete_practice_session` 和 `get_pending_adaptive_update_items`；执行后这四个函数必须分别匹配右侧的综合隔离版本 hash，不能继续停留在 production predecessor。

其中 `get_adaptive_candidate_history_v1` 必须为 `STABLE + SECURITY INVOKER`，固定 `search_path=public, pg_temp`，且只有 `service_role` 拥有 `EXECUTE`。`validate_practice_session_item_scope` 必须为 `SECURITY DEFINER`、固定同一 `search_path`，不向 `PUBLIC/anon/authenticated/service_role` 暴露直接执行权，并由 `practice_session_items` 上已启用的同名 trigger 调用。

本次执行已单独归档五个迁移文件的 SHA-256：

| 文件 | SHA-256 |
| --- | --- |
| `database/adaptive_comprehensive_practice_v1.sql` | `3F396E122187A77E9D6B64BA13768CC24081762FDDC3ACDB21F8EA31D4843DF1` |
| `database/adaptive_candidate_history_lookup_v1.sql` | `EFDC9EC8757BE4DA82750FBA72AB7591AB3149AD62EBCA1D61D56D3DAA71821F` |
| `database/adaptive_comprehensive_submission_batch_v1.sql` | `E590A532C7814C2497CF80A5F9579AFB314F527A0D891E571D3B9E1A3E2FD704` |
| `database/adaptive_candidate_freshness_hardening.sql` | `6E31BAB2D445E8CF0B4E3B56AE0B5171F699B433EA39A8181366AAA32E57351A` |
| `database/question_answer_read_access_hardening.sql` | `EDF62A319871E0E08355B366EE28E247DB2D4546F71A9F83BE37E33A4E494357` |

这些值已在实际迁移窗口重新计算并与仓库外回退包的副本及 `manifest.json` 逐项匹配。回退包最终覆盖 35 个被引用文件且缺失/哈希不符均为 0；清单自身 SHA-256 为 `21BA388B6778D74E1AB65AA42E912F8193187B8F75ED0EB93EC3784C005B9F31`。

## 4. 执行前签名、数据与权限快照

签名前的函数签名状态必须是：

```text
old13=true
private13=false
new17=false
```

对应签名为：

```sql
select
  to_regprocedure(
    'public.record_answer_submission(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
  ) is not null as old13,
  to_regprocedure(
    'public.record_answer_submission_pre_comprehensive_v1(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid)'
  ) is not null as private13,
  to_regprocedure(
    'public.record_answer_submission(uuid,uuid,text,text,boolean,integer,text,text,text,text,boolean,timestamptz,uuid,text,uuid,text,text)'
  ) is not null as new17;
```

执行前还需保存：

- 三张现有业务表的实时行数：`user_answers`、`wrong_questions`、`user_question_progress`；
- 8 张第一层自适应表的行数，以及 `practice_sessions` 中 `status='ACTIVE'` 的数量；
- 第 3 节所有现存函数的完整定义与元数据；
- `anon`、`authenticated`、`service_role` 对这些函数的实际 `EXECUTE` 权限结果；
- `public.questions` 的 `pg_policies` 记录、表级权限，以及 `answer/explanation` 列级权限；
- Dashboard 备份/PITR 恢复点、项目身份签名和当前代码提交标识。

题库读取权限快照使用：

```sql
select policyname, roles, cmd, qual, with_check
from pg_policies
where schemaname = 'public' and tablename = 'questions'
order by policyname;

select grantee, privilege_type
from information_schema.table_privileges
where table_schema = 'public'
  and table_name = 'questions'
  and grantee in ('PUBLIC', 'anon', 'authenticated', 'service_role')
order by grantee, privilege_type;

select
  role_name,
  has_table_privilege(role_name, 'public.questions', 'SELECT') as can_select_table,
  has_column_privilege(role_name, 'public.questions', 'answer', 'SELECT') as can_select_answer,
  has_column_privilege(role_name, 'public.questions', 'explanation', 'SELECT') as can_select_explanation,
  has_table_privilege(role_name, 'public.questions', 'INSERT') as can_insert,
  has_table_privilege(role_name, 'public.questions', 'UPDATE') as can_update,
  has_table_privilege(role_name, 'public.questions', 'DELETE') as can_delete
from unnest(array['anon', 'authenticated', 'service_role']) as roles(role_name)
order by role_name;
```

迁移前实际状态与预期一致：5 个综合基础 RPC、1 个候选历史 RPC 和 1 个整卷批量 RPC 均缺失；`validate_practice_session_item_scope` 已存在但尚未匹配本轮加固版本。该段只保留为 predecessor 证据，当前远端已完成迁移，不再按“未迁移”环境处理。

## 5. 执行与执行后核验

本节同时保留可复现的执行手册和 2026-09-04 的实际执行证据。四份自适应增量、完整只读核验、题库权限增量与权限/应用只读冒烟均已按本节顺序完成；应用部署、登录账号完整答题冒烟与灰度仍属于后续阶段。

完成第 2–4 节签名后，在同一个已确认身份的 Supabase SQL Editor 窗口中先只执行：

```text
database/adaptive_comprehensive_practice_v1.sql
```

该文件自身使用事务。SQL Editor 报错时保存完整错误和执行时间，并确认事务没有留下部分对象；不要接着执行第一层文件或权限硬化增量。

提交成功后，立即核验：

1. 签名状态变为 `old13=false`、`private13=true`、`new17=true`。
2. 5 个综合 RPC 全部存在；第 3 节第二层 6 个公开入口的 body hash 全部匹配。
3. 第一层 6 个关键函数仍存在且 hash 匹配；所有受保护 RPC 都是 `SECURITY DEFINER`，`search_path` 固定为 `public, pg_temp`。
4. 公开 13 参数 `record_answer_submission` 已消失；私有 13 参数核心只供 17 参数包装器调用。
5. `anon`、`authenticated` 和 `PUBLIC` 没有这些受保护 RPC 的执行权，只有 `service_role` 有 `EXECUTE`。
6. `user_answers`、`wrong_questions`、`user_question_progress` 的行数与执行前快照一致；8 张自适应表的已有数据没有被历史重建。若执行窗口内仍有业务写入，先按主键/时间审计真实增量，再判断，不能只看总数差异。
7. `ACTIVE` 会话仍为 0。

以上七项全部通过后，再在同一项目执行：

```text
database/adaptive_candidate_history_lookup_v1.sql
```

该文件新增有界候选历史 RPC 与三字段进度索引，不扫描或重建历史数据。提交成功后立即确认：

1. `get_adaptive_candidate_history_v1(uuid,text,text,uuid[],integer,boolean)` 存在，正文 hash 为 `e6adb88c8664395872268e9d72686fa2`。
2. 函数为 `STABLE + SECURITY INVOKER`，`search_path=public, pg_temp`；`PUBLIC/anon/authenticated` 均无执行权，只有 `service_role` 有 `EXECUTE`。
3. `idx_user_question_progress_user_question_exam` 存在、`indisvalid=true`、`indisready=true`，索引键顺序固定为 `(user_id, question_id, stats_exam_code)`。
4. `user_answers`、`wrong_questions`、`user_question_progress` 和 8 张自适应表没有因迁移脚本本身产生行数变化。
5. staging 冒烟验证一次返回最近题、候选内全局已做物理题和当前考试版本进度；另一考试版本的私有题不进入结果，合法 `COMMON` 题只参与物理题记忆去重，不迁移能力状态。

以上五项全部通过后，再执行：

```text
database/adaptive_comprehensive_submission_batch_v1.sql
```

该文件只新增有界的整卷答案持久化 RPC，不重放基础迁移。提交成功后立即确认：

1. `persist_adaptive_comprehensive_answers_batch(uuid,uuid,text,text,timestamptz)` 存在，正文 hash 为 `6e58a83fc2e468fcad46435d4a4e8456`。
2. 函数为 `SECURITY DEFINER`，`search_path=public, pg_temp`，`PUBLIC/anon/authenticated` 均无执行权，只有 `service_role` 有 `EXECUTE`。
3. `user_answers`、`wrong_questions`、`user_question_progress` 和 8 张自适应表没有因迁移脚本本身产生行数变化。
4. 使用同一固定清单的 staging 冒烟可幂等重放；不同清单复用批次 ID 稳定冲突，30 题上限生效。

以上四项全部通过后，再执行：

```text
database/adaptive_candidate_freshness_hardening.sql
```

该文件只替换既有题位作用域 trigger function，不重放第一层或修改历史行。提交成功后立即确认：

1. `validate_practice_session_item_scope()` 正文 hash 为 `44d6eb45883359e4b129e26b1e7bf4e5`，为 `SECURITY DEFINER` 且 `search_path=public, pg_temp`。
2. `PUBLIC/anon/authenticated/service_role` 均没有有效 `EXECUTE`；`practice_session_items` 上的 `validate_practice_session_item_scope` trigger 仍以普通 origin 模式启用，保持逐行 `BEFORE INSERT OR UPDATE OF session_id, question_id, position`，并指向该函数。
3. 正文包含 `adaptive_candidate_changed`，并复核活动状态、考试版本/学科/专项范围、人工难度、经验难度、质量状态、质量权重与有效性。
4. 三张业务表和 8 张自适应表行数没有因迁移脚本本身发生变化。

以上四项通过后，完整运行 `database/adaptive_comprehensive_practice_verification.sql`；所有函数、ACL、索引、trigger、签名和行数门禁全部符合预期后，才执行题库读取权限增量：

```text
database/question_answer_read_access_hardening.sql
```

权限增量提交后立即重复第 4 节的 policy/grant 查询，并要求：

1. `authenticated users can read questions` policy 不存在。
2. `anon`、`authenticated` 对题表的 `SELECT`，以及对 `answer/explanation` 的列读取均为 `false`；`PUBLIC` 不得通过公共授权重新获得访问。
3. `service_role` 的 `SELECT/INSERT/UPDATE/DELETE` 均为 `true`。
4. 使用 authenticated 测试账号直连 PostgREST 读取 `questions` 被拒；后端普通题目接口仍成功且出题响应中的 `answer/explanation` 为 `null`。
5. 部署保持关闭状态的后端后，提交作答才返回正确答案；管理员题库查询、编辑、发布/下架和导入 dry-run 仍正常。

迁移后的只读 REST 探测还需确认 5 个综合基础 RPC、候选历史 RPC 和整卷批量 RPC 共 7 个入口已进入 PostgREST schema cache，并确认直接题表读取已经关闭。只做缺参调用时，预期应从“函数不存在/未暴露”变化为函数自身的参数或身份校验错误；不得以会写入的有效业务参数做探测。

## 6. 回退与后续边界

- 事务提交前失败依赖 PostgreSQL 事务回滚，并用前后对象清单确认没有残留。
- 已提交但核验失败时，保持功能开关关闭，优先用迁移前导出的函数定义和 ACL 做精确恢复；涉及状态不明或数据变化时使用已确认的 Dashboard 备份/PITR 恢复流程。
- 权限硬化回退只使用执行前保存的精确 policy/ACL；不要凭记忆重建宽泛授权。若后端 service-role 冒烟失败，先保持功能关闭并核对 `service_role` 显式 CRUD，不向客户端恢复答案直读作为常规处置。
- 第一层迁移不是回退路径。
- 通过本文件的迁移核验只代表数据库第二层、候选历史查询、整卷批量持久化、候选新鲜度与题库读取边界就绪；诊断题人工审核与 dry-run、D4 补题返工与审核、真实并发/延迟压测、后端与前端部署、内部账号影子验证仍是独立上线门禁。当前 D4 补题包 75 个槽位中 71 题为 `REWORK`、4 题为 `PENDING_HUMAN_REVIEW`，可用数与数据库写入数均为 0。
