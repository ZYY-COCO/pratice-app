# 个性化普通刷题灰度与真实性能验证预检

更新时间：2026-09-04

本文件描述灰度前验证与门禁实现，不把代码进入发布候选等同于已经启用功能或完成真实性能测试。2026-09-04 已完成生产数据库增量迁移与权限核验；应用发布保持 `ADAPTIVE_PRACTICE_ENABLED=false` 和 0% 放量，没有导入题目或诊断校准。

## 1. 当前结论

| 检查项 | 当前证据 | 结论 |
| --- | --- | --- |
| SQL 执行计划 | `docs/practice_question_delivery_model.md` 要求补 `EXPLAIN (ANALYZE, BUFFERS)`，仓库中没有自适应查询的计划结果或基线 | 待补 |
| 专项并发 claim | Python 测试覆盖状态冲突、幂等回读和模拟的并发槽位冲突；SQL 契约测试检查锁与约束文本 | 只有 mock/静态契约，没有真实 PostgreSQL 并发 |
| 综合并发 claim/submit | SQL 契约测试覆盖完整题单、清单锁定、整卷批量持久化、幂等与 finalize；服务测试覆盖丢响应续算 | 只有 mock/静态契约，没有真实 PostgreSQL 并发 |
| 50/100/200 VU | 仓库没有 k6、Locust、Artillery、wrk 或同类自适应压测 runner/result | 待补 |
| 前端体验埋点 | 页面实现了 1.2 秒前台等待预算和预取状态，但没有导出首帧耗时、预取命中、综合本地切题或违规 `/next` 指标 | 待补 |
| 后端/API 埋点 | 自适应服务有错误日志，`monotonic()` 只用于候选缓存 TTL；没有请求直方图、RPC 分段耗时或结构化维度 | 待补 |
| 1% 灰度能力 | 本地已实现总开关、内部用户白名单与 HMAC 稳定百分比分桶 | 代码与测试已就绪，尚未部署；线上仍不得打开总开关 |
| 题库答案直读边界 | 生产增量已撤销 `PUBLIC/anon/authenticated` 的整表与全部 32 列直读并保留 `service_role` CRUD；匿名直连返回 `42501`，FastAPI 题库统计仍为 200 | 数据库边界已完成；登录账号完整答题与管理员接口冒烟随应用部署执行 |
| D4 诊断供给 | 75 个补题记录只是候选槽位；71 题为 `REWORK`、4 题为 `PENDING_HUMAN_REVIEW`，当前可用数为 0、数据库写入为 0 | 不得导入、发布或加入诊断池 |
| 生产运行拓扑 | systemd 以单个 `uvicorn app.main:app` 进程启动，没有显式 workers | 必须按这一真实拓扑压测，或先明确容量拓扑后再测 |

因此，在真实 staging 证据完成前应继续保持 `ADAPTIVE_PRACTICE_ENABLED=false`。2026-09-04 本次提交范围的最终定向复跑为后端自适应、作答可靠性及 SQL/权限合同 204 项，旧普通组题、游标分页和管理员题库权限 20 项，以及负载 trace 门禁 28 项，共 252 项全部通过；前端自适应契约 5 项和 H5、微信小程序、App 三端构建也全部成功。D4 补题与诊断池工具测试不属于本次发布提交。这些结果证明的是功能与迁移契约，不等价于真实 Supabase 网络延迟或并发吞吐。

## 2. 放量前的最小缺口

按阻塞关系排序：

1. 建立与生产拓扑一致的 staging：独立数据库、合成账号、合成题目与诊断校准，依次执行 `adaptive_question_delivery_v1.sql`、`adaptive_comprehensive_practice_v1.sql`、`adaptive_candidate_history_lookup_v1.sql`、`adaptive_comprehensive_submission_batch_v1.sql`、`adaptive_candidate_freshness_hardening.sql`，完整核验后再执行 `question_answer_read_access_hardening.sql`；严禁复用生产用户 token 或生产数据写连接。
2. 补齐迁移后的登录态端到端冒烟：authenticated PostgREST 探针被拒，FastAPI 安全题面不含答案，持久化提交后才返回反馈，管理员题库查询与 dry-run 正常。数据库角色权限、匿名直连拒绝和 FastAPI 服务端读取已经通过。
3. 部署并核验本地已经实现的可控灰度入口：内部账号 allowlist、稳定用户分桶百分比、默认 0%、非法配置关闭本功能，以及创建响应丢失后仍能恢复既有幂等会话。
4. 增加最小体验埋点：专项答题反馈、专项预取命中/在线切题、综合整卷可用、综合本地切题、综合轮内 `/next` 计数。事件必须带匿名 user key、会话、题位、实际考试版本、学科、模式、客户端版本和结果码，禁止记录 token、答案、题干或解析。
5. 增加后端分段耗时：入口总时长、Supabase operation 名称与时长、重试次数、响应状态、作用域和策略版本。至少能区分候选读取、状态读取、pending barrier、claim RPC、答题持久化、模型更新、综合 begin/整卷持久化/有序模型更新/finalize。
6. 在 staging 实测关键 SQL 计划和 RPC 总时长，随后完成真实并发不变量测试和 50/100/200 VU 阶梯测试。
7. 补齐其余非性能上线门：诊断池仍需人工审核与 dry-run，D4 补题包仍需返工与人工审核；自适应基础及四个后续增量仍需回写主 schema 或建立可靠的新环境迁移入口。

### 2.1 建议的灰度配置语义

后端已经增加以下配置；部署环境仍保持默认关闭：

| 配置 | 默认值 | 语义 |
| --- | --- | --- |
| `ADAPTIVE_PRACTICE_ENABLED` | `false` | 总开关/新会话 kill switch。为 `false` 时白名单和百分比都不得创建新自适应会话 |
| `ADAPTIVE_PRACTICE_ROLLOUT_USER_IDS` | 空 | 逗号分隔的内部用户 UUID；总开关为 `true` 时始终命中，用于百分比为 0 的内部验收 |
| `ADAPTIVE_PRACTICE_ROLLOUT_PERCENT` | `0` | `0..100`；只控制非白名单用户的新会话。默认 0，禁止因只打开总开关而意外全量 |
| `ADAPTIVE_PRACTICE_ROLLOUT_SALT` | 无默认生产值 | 服务端稳定分桶盐；灰度开始后保持不变，变更它会重排用户群 |

判定顺序固定为：

```text
总开关 false → 拒绝所有新自适应会话
总开关 true 且用户在 allowlist → 允许
非白名单且 rollout percent = 0 → 拒绝
其余 → HMAC-SHA256(salt, user_id) 映射到 0..9999，bucket < percent × 100 时允许
```

分桶只使用 `user_id`，不拼接考试版本、学科或设备，因此同一用户在所有学科和端上稳定处于同一灰度组，避免一半自适应、一半旧逻辑污染体验和能力证据。比例精确到 0.01 个百分点，使用十进制定点换算，不受二进制浮点误差影响。比例越界、非数字或 0% 均关闭非白名单入口；1%–99.99% 未配置盐值时也关闭。拒绝真正的新建请求继续使用现有兼容回退契约；如果首个创建响应丢失，同一 `client_session_id` 仍可越过当前门禁恢复数据库中的既有会话。已开始会话的 `/next`、事件、完成和综合交卷始终允许收尾。每次创建判定只记录 `rollout_basis_points + bucket + decision_source`，其中 `decision_source` 只能是 `master_off/allowlist/bucket_hit/bucket_miss/config_invalid`，不记录原始 user ID。

## 3. 性能 trace 契约与离线门禁

`scripts/validate_adaptive_load_trace.py` 只读取本地 JSON/JSONL，不联网、不接库。正式大文件使用 JSONL，脚本逐行解码；JSON 数组仅保留给小型夹具。门禁分别在 50、100、200 VU 的稳定窗口计算第 9.10 节指标，不再把三个档位聚合后相互稀释：

- 实际出现的 VU 集合必须与 `--require-vus` 完全相等，多档或少档都失败；
- CLI 的 `--min-samples-per-metric` 只是附加下限，实际按 `max(CLI 下限, 统计下限)` 执行：带 p95 的指标每档至少 100 个有效样本，`special_online_transition` 因校验 p99 每档至少 300 个有效样本；
- `special_answer_feedback`：每档 p95 不超过 800 ms；
- `special_prefetch_transition`：每档 p95 不超过 100 ms；
- `special_online_transition`：每档 p95 不超过 500 ms，p99 不超过 1200 ms；
- `comprehensive_sheet_ready`：每档 p95 不超过 1500 ms；
- `comprehensive_local_transition`：每档 p95 不超过 50 ms；
- 综合整卷 submit 另行统计端到端 p50/p95/p99/max 和超过 30 秒比例；每档超过 30 秒的完成请求必须为 0，且 p95/p99 必须保留可审计结果；
- 每档至少 300 次自然专项转场，预取命中率至少 90%；定向在线 fallback 样本只测延迟，不污染自然命中率；
- 每档至少 1500 次题间转场，超过 2 秒的实测占比低于 0.2%；
- 每档只按成功且计入性能的事件统计 `anonymous_user_key`，去重数不得少于该档 VU 数；`audit_only` 账号不能为容量账号数注水；
- 声明的稳定窗口不少于 300 秒，并且该档有效性能事件的首末时间跨度加最多 5 秒边缘容差后仍须覆盖 300 秒；只声明长窗口、却把事件集中在一个瞬间会失败；
- 综合轮内 `/next`、跨用户/跨科/跨版本会话串扰、item 归属冲突、重复题位胜者和整卷物理重复题都必须为 0；
- `event_id` 全局唯一，`request_id + metric` 唯一，专项 `transition_id` 唯一；重复导出记录不计入样本且阻止通过；
- 一个 trace 只允许一个 `run_id` 和一组 `build_sha + strategy_version + model_version + app_version`；预热事件不得混入稳定窗口；
- trace 中任何未达到预期结果的 `ok=false` 都阻止通过。`sample_kind=audit_only` 当且仅当 `expected_outcome=expected_conflict`；普通成功和并发胜者不得借此退出延迟分位数。约定冲突还必须携带已登记场景、尝试组、并发度和精确预期错误码。

公共字段使用 schema v1。四个包含网络结果的指标（专项反馈、专项预取、专项在线转场、综合整卷可用）成功时必须是 HTTP 2xx；只有 `comprehensive_local_transition` 成功时使用 `status_code=0`。HTTP 错误必须带稳定 `error_code`，成功事件的 `error_code` 为空。`sample_kind` 只能是 `natural`、`forced_probe` 或 `audit_only`，其中只有 `natural` 进入预取命中率分母，前两者可进入延迟与转场统计。专项转场的 `foreground_budget_exceeded` 必须等于 `duration_ms > 1200`，门禁按档输出超预算次数与占比。

专项预取转场示例：

```json
{
  "schema_version": 1,
  "event_id": "event-uuid",
  "metric": "special_prefetch_transition",
  "occurred_at": "2026-09-04T10:03:12.345+08:00",
  "duration_ms": 42.7,
  "ok": true,
  "status_code": 200,
  "error_code": "",
  "expected_outcome": "success",
  "request_id": "request-uuid",
  "run_id": "adaptive-staging-20260904-01",
  "stage": "steady",
  "stage_started_at": "2026-09-04T10:00:00+08:00",
  "stage_ended_at": "2026-09-04T10:05:00+08:00",
  "sample_kind": "natural",
  "vus": 100,
  "practice_mode": "special",
  "anonymous_user_key": "salted-sha256-value",
  "session_id": "synthetic-session-id",
  "item_id": "session-item-id",
  "question_id": "question-id",
  "position": 3,
  "expected_exam_code": "Z001",
  "actual_exam_code": "Z001",
  "expected_subject": "逻辑推理",
  "actual_subject": "逻辑推理",
  "strategy_version": "adaptive-v1",
  "model_version": "ability-v1",
  "client_platform": "h5",
  "app_version": "1.0.0-rc1",
  "build_sha": "candidate-commit-sha",
  "transition_id": "next-click-uuid",
  "prefetch_hit": true,
  "foreground_budget_exceeded": false
}
```

`special_online_transition` 使用相同契约但 `prefetch_hit=false`。定向触发 fallback 时设 `sample_kind=forced_probe`；它仍进入在线转场延迟分位数，但不计入自然预取命中率。

每个成功的 `comprehensive_sheet_ready` 必须携带一次完整权威题单及其哈希，而不只携带用户访问过的题位：

```json
{
  "comprehensive_next_calls": 0,
  "manifest_question_count": 2,
  "authoritative_manifest_hash": "c6e494529d79885c5d5ffe0f42cd93debbc90dfcbc0ffe1243e0a4e39ecd0e24",
  "manifest_items": [
    {"position": 1, "item_id": "item-1", "question_id": "question-1"},
    {"position": 2, "item_id": "item-2", "question_id": "question-2"}
  ]
}
```

哈希算法固定为：先按题位排序，将每项规范化为 `position/item_id/question_id`，再对 UTF-8、键排序、无多余空白的 JSON 数组计算 SHA-256。上例的哈希与示例清单真实对应。实际 `manifest_items` 长度必须等于 `manifest_question_count`，题位必须从 1 连续到题目总数，item 与物理题均不得重复。同一 `session_id` 在整个 trace 中只能属于同一匿名用户、模式、考试版本、学科、run 和 VU 档位；同一 `item_id` 只能映射到一个 session、题位和物理题。

`comprehensive_sheet_ready` 可省略事件自身的 `item_id/question_id/position`。`comprehensive_local_transition` 必须携带三者和 `navigation_kind`，正常情况下不再重复完整 manifest；门禁读完整个流后，用该 session 的 `comprehensive_sheet_ready` 权威清单核验题位映射，因此本地转场先于整卷事件出现在导出文件里也能正确判断。为了兼容诊断导出，本地转场仍可选重复完整 manifest，但只作为不可变性复核，不能替代该 session 的权威整卷事件。

当前登记的预期冲突场景包括：

| `conflict_scenario` | HTTP | `expected_error_code` | 模式 | 附加字段 |
| --- | ---: | --- | --- | --- |
| `special_update_pending` | 409 | `ADAPTIVE_UPDATE_PENDING` | 专项 | 无 |
| `comprehensive_manifest_conflict` | 409 | `ADAPTIVE_COMPREHENSIVE_SUBMISSION_CONFLICT` | 综合 | `attempted_manifest_hash`、`authoritative_manifest_hash`，二者必须不同 |

每条预期冲突还必须带非空 `attempt_group_id` 和整数 `concurrency >= 2`。综合清单冲突只提交两个哈希，不把失败尝试的 `manifest_items` 当成权威题单；`authoritative_manifest_hash` 必须能回连到同 session 的整卷成功事件。实际 `error_code` 必须与 `expected_error_code` 及场景登记值完全相等，不能用任意 409/422 冒充预期冲突。

运行正式门禁：

```powershell
& "backend\.venv\Scripts\python.exe" scripts\validate_adaptive_load_trace.py reports\adaptive_staging_load_trace.jsonl --require-vus 50,100,200 --min-samples-per-metric 30 --min-transitions-per-vu 1500 --min-natural-special-transitions-per-vu 300 --min-stable-seconds 300
```

上例保留 CLI 下限 30 以兼容调用入口，但最终 `required_count` 仍由脚本提升为 p95 指标 100、在线 p99 指标 300；门禁 JSON 输出会逐指标显示实际采用的 `required_count`。

脚本自身的纯合成正反例检查：

```powershell
& "backend\.venv\Scripts\python.exe" scripts\validate_adaptive_load_trace.py --self-test
```

门禁脚本不是流量发生器，也不替代真机首帧埋点、真实 Supabase 压测或“一个学科作答不改变另一个学科 theta”的并发前后快照断言。`vus`、`concurrency`、`attempt_group_id` 都是 runner 提供的声明；完整的 2/5/10 并发矩阵、实际同时在线数、唯一胜者、最终数据库状态和 pending 清零仍必须由独立并发 runner 及数据库快照证明。本脚本只校验收到的 UX trace 与已登记冲突记录，不宣称仅凭这份 trace 已覆盖并发矩阵。它的作用是拒绝统计证据不完整、混档、混版本、重复或违反会话/题单不变量的 trace，并以非零退出码阻止不合格版本放量。

前端 `submitAdaptiveComprehensivePracticeSession` 当前设置 30 秒请求超时。这个数值只是客户端停止等待本次 HTTP 响应的失败边界，不是性能目标，也不代表服务端事务已经失败。超时后提交结果属于未知状态：客户端必须保留首次请求前已经持久化的不可变 `sessionId + client_submission_id + answers`，继续用原清单重试；不得重新生成批次 ID、替换答案清单或把超时当作可安全新交一卷。只有收到结构完整的 `COMPLETED` 响应或明确终态冲突后，才处理对应本地续交任务。

## 4. SQL 执行计划检查

先对下列读取形态分别保存 `EXPLAIN (ANALYZE, BUFFERS, WAL, FORMAT JSON)` 结果；使用与生产数据量级相近的 staging 数据，至少各测冷缓存和暖缓存三次：

1. 候选题：`exam_code + subject + status + module/submodule`，按 `id` 分页；
2. 候选校准：`stats_exam_code + question_id IN (...)`；
3. 最近作答与全局已见：`user_id + stats_exam_code + questions.subject`，按 `created_at/id` 分页；
4. 到期复习：`user_id + stats_exam_code + questions.subject`，按 `question_id` 分页；
5. pending barrier：同一用户、考试版本、学科下，对 `adaptive_model_updates.answer_id` 反连接并按 `answer.created_at/session.created_at/item.position/item.id` 排序；
6. 会话题位和私有快照的完整回读；
7. 待复验冲突与活动复验租约查找；
8. 综合 manifest 完整性与 finalize 的逐题核对。

验收时记录规划/执行耗时、shared hit/read blocks、temp read/write blocks、返回行数与估算行数偏差。出现顺序扫描并不自动失败，但必须解释表规模和选择性；出现大范围误估、磁盘排序、临时文件或随用户历史线性增长的读块数，应先修复再压测。

注意：

- `EXPLAIN ANALYZE SELECT public.claim_...(...)` 会实际执行写函数，只在可重置 staging 的事务中使用，并在测试后核对/回滚合成数据。
- 普通 `Function Scan` 只能给出 RPC 总耗时，通常看不到 PL/pgSQL 内部每条 SQL 的计划。需要把上述内部查询单独参数化执行，或在 staging 使用允许记录 nested statements 的数据库观测能力；不要把单行 `Function Scan` 当作完整计划证据。
- 不在生产上用 `EXPLAIN ANALYZE` 调用 claim、submit、skip、finalize 或模型更新函数。

## 5. 真实并发矩阵

所有用例使用合成账号；每轮生成唯一 client ID，并保存请求开始/结束、状态码、错误 code、会话/题位/题目映射。

| 场景 | 并发 | 必须满足 |
| --- | ---: | --- |
| 同会话专项 `/next` | 2、5、10 | 一个题位只有一个数据库胜者；其余请求回读同一胜者或得到约定的可重试冲突；没有两个 question/item |
| 同用户同学科的两个专项会话 | 2、5 | 状态版本按数据库顺序推进；无漏更新、重复 update 或跨会话题位绑定 |
| 同用户不同学科/考试版本 | 每 scope 5 | 返回 scope 始终匹配；一个学科结果不改变另一学科候选与 theta |
| 综合同 client session 并发创建 | 2、5、10 | 只得到一个 session ID 和一份连续、完整、无重复固定题单 |
| 综合同清单并发 submit | 2、5、10 | 最终只形成一份不可变 manifest 和一份完成快照；临时 pending 可重试后收敛到同一结果 |
| 综合同 batch ID 不同清单 | 2 | 恰有一个清单胜出，另一清单稳定返回 conflict；胜出清单不被改写 |
| 综合与公共单题反馈竞态 | 2、5 | 交卷前公共判分、解析和“不熟悉”旁路始终被拒绝 |
| 模型补偿与新 `/next` 竞态 | 2、5 | 下一题不越过未结算答案；补偿按稳定顺序且每个 answer ID 只有一个审计行 |

并发矩阵中的约定冲突不是失败请求：runner 只把命中第 3 节登记场景、HTTP 状态和精确业务码的结果记录为 `expected_outcome=expected_conflict`、`sample_kind=audit_only` 和 `ok=true`，同时记录 `conflict_scenario + attempt_group_id + concurrency + expected_error_code`。状态码或业务码不符合预期时记录 `ok=false`。预期冲突只参加审计，不进入用户体验延迟样本；并发胜者仍是普通成功样本，不能标成 `audit_only` 隐去延迟。

不要用同一用户模拟全部 200 VU：按用户/学科的 advisory lock 本来就会序列化同一能力作用域，这会把“单用户争用测试”误当成真实容量。容量阶段使用 200 个独立合成账号，同时另跑上表的小比例热点争用场景。

## 6. 50/100/200 VU 阶梯

建议每档先预热 2 分钟，再稳定运行至少 5 分钟，档间等待 pending update 清零。预热记录不写入门禁 trace；稳定记录统一写 `stage=steady`，并带该档一致的 `stage_started_at/stage_ended_at`。每档有效性能事件的实际首末跨度至少 295 秒，每档参与性能统计的匿名账号去重数至少等于 VU 数，三个稳定窗口不得重叠，且 trace 中不得混入未要求的 VU 档。流量组合应接近产品行为：

- 55% 专项：创建、presented、答题、结果早显、后台预取、点击下一题；
- 35% 综合：创建整卷、本地切题若干次、一次整卷 submit、幂等重放少量请求；
- 10% 热点与恢复：重复 `/next`、相同清单重试、一次响应丢失后的续交。

每档同时观察：API p50/p95/p99/max、错误 code 分布、Nginx upstream time、应用 CPU/RSS、线程池排队、Supabase 请求/RPC 时长、数据库 CPU/连接/锁等待、deadlock、临时文件和慢查询。生产服务当前是单 Uvicorn worker，测试环境必须先按该拓扑建立基线；如果调整 workers，必须重测并记录最终线上值。

除产品门槛外，建议把以下条件也设为硬门：

- HTTP 5xx、未预期 409/422、死锁、超时和连接池耗尽为 0；
- 综合整卷 submit 的端到端 p95/p99 已分别统计，每档超过 30 秒的完成请求为 0；客户端超时恢复测试最终必须收敛到同一 completion snapshot；
- 每档结束后 pending model updates 最终归零；
- 会话完成率 100%，没有超过测试窗口仍 ACTIVE/LOCKED 的合成会话；
- 同一 client ID 的重试结果一致；
- 50→100→200 VU 的吞吐、延迟、CPU、数据库锁等待曲线可解释，没有突变拐点。

## 7. 埋点最小定义

建议使用以下稳定事件名，正好映射离线门禁的 `metric`：

| 事件 | 起点 | 终点 |
| --- | --- | --- |
| `special_answer_feedback` | 用户提交点击 | 正误态第一次绘制完成 |
| `special_prefetch_transition` | 用户点击下一题 | 已预取题目的题干首帧绘制完成 |
| `special_online_transition` | 用户点击下一题 | 在线 claim 得到的题干首帧绘制完成 |
| `comprehensive_sheet_ready` | 用户点击开始 | 完整固定题单校验完成且首题首帧绘制完成 |
| `comprehensive_local_transition` | 用户点击下一题/上一题/题卡题位 | 目标题题干首帧绘制完成 |

“首帧完成”应在 Vue 状态提交后的下一次可观察渲染点测量，不以 HTTP Promise resolve 代替。综合网络拦截器还需按 session 计数 `/adaptive-practice/sessions/{id}/next`；综合轮内任何一次都立即上报违规。

所有性能事件的最小公共字段固定为：

```text
schema_version, event_id, metric, occurred_at, duration_ms, ok,
status_code, error_code, expected_outcome, request_id,
run_id, stage, stage_started_at, stage_ended_at, sample_kind, vus,
anonymous_user_key, session_id, item_id, question_id, position,
expected_exam_code, actual_exam_code, expected_subject, actual_subject, practice_mode,
strategy_version, model_version, client_platform, app_version, build_sha
```

专项转场再带唯一 `transition_id + prefetch_hit + foreground_budget_exceeded`；只有成功的 `comprehensive_sheet_ready` 必带 `manifest_question_count + manifest_items + authoritative_manifest_hash`。综合本地转场另带 `navigation_kind + comprehensive_next_calls`，通常不重复 manifest，事件自身的题位映射在流结束后回连权威清单。预期冲突带 `conflict_scenario + attempt_group_id + concurrency + expected_error_code`；综合不同清单冲突再带 `attempted_manifest_hash + authoritative_manifest_hash`。

后端 RPC 分段事件可另带 `supabase_operation + operation_duration_ms + retry_count + cache_hit`，但这些后端细分事件应保存到独立观测流，不混入只接受五类用户体验 metric 的门禁文件。`error_code` 使用稳定业务 code，不把完整异常文本塞入高基数字段。任何事件都不记录 access/refresh token、原始 user ID、所选答案、正确答案、题干或解析；`anonymous_user_key` 使用当次观测环境的带盐不可逆摘要。

## 8. 灰度、停止与证据归档

完整顺序为：第一层自适应增量 → 综合基础增量 → 候选历史查询增量 → 整卷批量持久化增量 → 候选新鲜度加固 → 完整只读核验 → 题库答案直读权限硬化 → 权限与 service-role CRUD 冒烟 → 保持总开关关闭部署应用 → 诊断池审核与 dry-run/经确认导入 → staging 计划/并发/负载验收 → 内部 allowlist → 1% 稳定用户分桶 → 5% → 20% → 50% → 100%。已有第一层的当前远端跳过第一层重放，严格按 `docs/adaptive_practice_migration_preflight_2026-09-04.md` 的四个自适应增量顺序执行。每档至少覆盖一个业务高峰窗口，且只在上一档所有门槛通过后扩大。

停止条件包括：任何跨科/跨版本串扰、综合轮内 `/next`、authenticated 题表直读或其他答案旁路、不同清单覆盖、重复题位胜者、service-role 题库 CRUD 回归、死锁、p95/p99 超门槛、超过 2 秒占比超门槛或 pending backlog 持续增长。停止时先把新会话比例降为 0；现有设计允许已经开始的会话完成，因此还需持续观察旧会话直至收敛，不能把“禁止新建”误报为所有自适应流量已停止。

每次候选发布至少归档：commit SHA、自适应第一层、综合基础、候选历史、整卷批量、候选新鲜度及题库权限增量各自的文件 SHA-256、数据库函数 body hash、题表迁移前后 policy/grant 快照与 authenticated/service-role 冒烟结果、开关/分桶配置、后端 worker 拓扑、数据库规模摘要、EXPLAIN JSON、压测 runner 配置、原始 trace、离线门禁输出、服务与数据库监控截图、失败 code 分布和最终批准人。每个独立增量都必须单独留存 checksum，不能用综合基础迁移的 checksum 代替。
