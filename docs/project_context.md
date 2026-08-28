# 港研通项目上下文

更新时间：2026-06-19

## 项目定位

港研通是一个面向港澳台考研用户的移动端刷题 App，当前以 uni-app H5/App 前端、FastAPI 后端、Supabase 数据库为核心。产品重点是专项刷题、综合刷题、错题复盘、学习报告、Pro 会员权益、AI 专项出题和后续题库重建。

当前根目录：

```text
C:\Users\1111\Documents\New project
```

根目录已有 `README.md` 作为项目入口。新窗口接手时先读 `README.md`，再读本文件，并按任务查看对应专题文档。

## 技术栈

- 前端：uni-app / Vue 3，目录 `frontend`
- 后端：FastAPI，目录 `backend`
- 数据库：Supabase
- 当前主要部署：腾讯云 Ubuntu + Nginx + systemd + GitHub Actions SSH 部署
- AI：DeepSeek 接口已接入，用于 AI 专项出题和后续学习建议
- 文件识别：后台题库批量导入支持文本 / Office / PDF 解析，图片和无文本 PDF 可走腾讯云 OCR
- App 打包：HBuilderX / uni-app App-Android 方向已尝试，另有 `android-wrapper/` 方案留存

## Git 状态检查

截至 2026-06-02，工作区经常包含大量已修改和未跟踪文件，主要集中在题库批次、资料抽取产物、报告、生成脚本、前端页面和后端接口。不要依赖本文档中的旧列表判断当前状态，开始工作前必须实时运行：

```powershell
git status --short
```

注意：不要一次性 `git add .`。每次提交前必须明确本轮要提交的文件范围，避免把临时素材、未审核题库或大文件误提交。

## 前端状态

常用命令：

```powershell
cd frontend
npm run build:h5
```

主要目录：

- `frontend/src/pages/home/index.vue`：首页
- `frontend/src/pages/login/index.vue`：登录注册页
- `frontend/src/pages/practice/index.vue`：专项刷题、综合刷题、AI 出题、模拟测试等主要练习页面
- `frontend/src/pages/pro/index.vue`：会员中心
- `frontend/src/pages/profile/index.vue`：个人资料
- `frontend/src/pages/history/index.vue`：练习历史
- `frontend/src/pages/favorites/index.vue`：收藏夹
- `frontend/src/pages/admin/index.vue`：后台管理，包含用户、反馈、题库管理、审核队列、发布 / 下架
- `frontend/src/pages/admin/question-image-import.vue`：题库批量导入，支持文件识别、预览、dry-run 校验和导入待审核
- `frontend/src/components/MathText.vue`：数学文本格式化展示
- `frontend/src/utils/mathText.js`：数学符号文本格式化
- `frontend/src/utils/theme.js`：外观主题
- `frontend/src/api/config.js`：API Base URL

当前 `frontend/src/api/config.js` 的默认值为：

```text
H5: /api
微信小程序: https://www.gangyantong.com/api
```

H5 可通过构建环境变量覆盖：

```bash
VITE_API_BASE_URL=/api
```

微信小程序构建会强制使用 `https://www.gangyantong.com/api`，需要在微信公众平台配置 request 合法域名 `https://www.gangyantong.com`。

## 后端状态

主要入口：

- `backend/app/main.py`
- `backend/app/config.py`
- `backend/app/routes/`
- `backend/app/services/`
- `backend/app/schemas/`

已接入的主要模块：

- 邮箱验证码注册、登录、找回密码
- 手机号验证码登录骨架
- 微信登录骨架
- token 持久化
- 题目查询、专项刷题、综合刷题
- 答题提交、错题写入、能力统计
- 错题本、收藏夹、练习历史
- 学习报告
- 会员订单与会员状态
- DeepSeek AI 专项出题
- 后台题库管理：列表筛选、详情、编辑、新增、单题 / 批量发布与下架、审核状态流转
- 题库批量导入：支持图片、JSON、CSV、TXT、XLSX、DOCX、PDF 识别，导入前 dry-run，写入后默认待审核 / 下架
- 中华文化学习范围进度和艾宾浩斯复习接口

环境变量不要提交到仓库。腾讯云后端环境文件位置：

```bash
/opt/gangyantong/backend.env
```

常见后端环境变量包括：

```text
SUPABASE_URL
SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
API_CORS_ORIGINS
SMTP_*
PAYMENT_WEBHOOK_SECRET
DEEPSEEK_API_KEY
DEEPSEEK_BASE_URL
DEEPSEEK_MODEL
PHONE_AUTH_PASSWORD_SECRET
SMS_PROVIDER
TENCENT_SMS_*
TENCENT_OCR_*
WECHAT_OAUTH_*
```

## 部署状态

腾讯云部署目录：

```text
/opt/gangyantong/app
```

腾讯云前端发布目录：

```text
/var/www/gangyantong
```

腾讯云后端服务：

```text
gangyantong-backend
```

腾讯云部署脚本：

```text
deploy/tencent-cloud/deploy.sh
```

手动部署命令：

```bash
cd /opt/gangyantong/app
BRANCH=main bash deploy/tencent-cloud/deploy.sh
```

常用排查命令：

```bash
sudo systemctl status gangyantong-backend --no-pager
sudo journalctl -u gangyantong-backend -n 100 --no-pager
sudo nginx -t
sudo systemctl reload nginx
curl http://127.0.0.1:8000/health
```

GitHub Actions 自动部署文件：

```text
.github/workflows/tencent-cloud-deploy.yml
```

需要的 GitHub Secrets：

```text
TENCENT_HOST
TENCENT_USER
TENCENT_PORT
TENCENT_SSH_KEY
```

曾经遇到过的问题：

- `Bad port '***'`：`TENCENT_PORT` 填错或带非数字字符。
- `hostname contains invalid characters`：`TENCENT_HOST` 填了 URL、用户名或多余字符。
- SSH 私钥必须填入 `TENCENT_SSH_KEY`，不是公钥。

## 域名与备案

域名：

```text
gangyantong.com
www.gangyantong.com
```

当前需要注意：

- 备案曾被驳回，原因是个人备案服务名称和备注不符合要求。
- 个人备案不要写产品化、经营性、平台化表述。
- 建议服务名称偏个人学习记录/学习笔记性质。
- `http://159.75.155.82` 是腾讯云 IP 访问入口。

## 数据库与题库

重要 SQL：

- `database/supabase_schema.sql`
- `database/auth_email_codes.sql`
- `database/phone_auth.sql`
- `database/profile_settings.sql`
- `database/membership.sql`
- `database/ai_training.sql`
- `database/full_reset_for_question_rebuild.sql`

题库导入脚本：

```powershell
& "C:\Users\1111\Documents\New project\backend\.venv\Scripts\python.exe" scripts\import_questions.py --file data\xxx.json --dry-run
& "C:\Users\1111\Documents\New project\backend\.venv\Scripts\python.exe" scripts\import_questions_bulk.py --file data\xxx.json --batch-size 100
```

题库 JSON 字段结构以 `scripts/import_questions.py` 校验为准，核心字段：

```text
exam_code
subject
module
submodule
question_type
stem
option_a
option_b
option_c
option_d
answer
explanation
difficulty
source_type
source_year
```

目前题库重建方向：

- 用户已决定清空并重建题库。
- 用户不介意清空当前测试用户数据，因为还没有真实落地。
- 中华文化题库要重新从 `中华文化/` 文件夹全量资料生成。
- 不能只依赖 Excel。
- 要读取 PDF、DOCX、XLSX 等全部可解析资料，再生成高质量题目。
- 旧 `.doc` 文件如果本地无法解析，要在报告里标记为跳过，不要悄悄忽略。

## 中华文化题库重建要求

用户最新明确要求：

- 使用 `中华文化/` 文件夹内所有资料。
- 不是只用 Excel。
- 可从资料中提取有价值题目，也可根据资料重新命题。
- 不标明“出处”“生成”“AI”等来源字样。
- 每题 4 个选项 A-D。
- 每题只有 1 个正确答案。
- 题干简洁直接，模仿港澳台考研真题风格。
- 不要科普题、问答题、材料分析题。
- 不要冷僻、争议性强或超出普通中华文化常识范围的题。
- 干扰项必须有迷惑性，来自相近知识领域。
- 解析控制在 50 字以内，只说明为什么选该答案。
- 考点要清楚。

必须覆盖五大板块：

1. 中国哲学常识
2. 中国历史学常识
3. 中国文学常识
4. 中国艺术常识
5. 中国古代科技常识

必须过滤的低质量题型或措辞：

```text
题干若考察
依据中华文化考纲
知识点归类
最准确的知识点归类
下列归类最准确
考查知识点
考察知识点
来源
生成
AI
图片
视频
```

不要再导入已被否定的第三批旧生成逻辑：

- `scripts/generate_common_culture_rebuild_500_batch_003.py`
- `data/common_culture_rebuild_500_batch_003.json`

这批曾出现题干和选项领域不匹配、干扰项离谱的问题。后续第三批应重做，而不是修修补补直接导入。

## 中华文化资料抽取入口

中华文化资料目录固定为 `中华文化/`，包含 PDF、DOCX、DOC、XLSX 等资料。继续生成前不要手工挑单一 Excel，要通过抽取脚本扫描所有可解析资料：

```text
scripts/extract_common_culture_sources.py
```

输出：

```text
data/common_culture_source_text/
data/common_culture_source_text/_extract_report.json
data/common_culture_source_text/_extract_report.md
```

再基于抽取文本生成新题库：

```text
data/common_culture_from_sources_batch_00x.json
data/common_culture_from_sources_batch_00x_review.md
scripts/generate_common_culture_from_sources_batch_00x.py
```

生成后必须先 dry-run 校验，再导入。

## 数学基础题库方向

数学基础范围：

- 一元函数微分学
- 一元函数积分学
- 多元函数微分学

明确不考：

- 线性代数
- 概率统计
- 级数
- 二重积分
- 微分方程
- 空间解析几何

用户希望数学题：

- 接近港澳台考研 Z002 综合能力（二）数学基础风格。
- 可参考 396 经济类联考数学基础选择题风格。
- 全部四选一。
- 需要更高质量解析。
- 数学符号需要尽量展示成常规卷面形式。

相关文件：

```text
frontend/src/components/MathText.vue
frontend/src/utils/mathText.js
```

## 英语运用题库方向

用户要求：

- 英语运用继续扩充大量题目。
- 选项要有混淆效果，设置陷阱。
- 后续 AI 生题也要遵守这个原则。
- 暂时可以先放下英语阅读理解，优先做语言知识类题目。

## 当前核心功能状态

已完成或已接入：

- 登录注册页面，支持邮箱和手机号验证码登录骨架
- 微信登录按钮目前偏“即将开放”或骨架状态，真实微信登录需正式域名和 HTTPS
- token 持久化
- 首页、我的页、个人资料页
- 专项刷题、综合刷题
- 模拟测试 105 分轻量模拟
- 题卡弹窗、跳题、做题状态点亮
- 提交答案写入 `user_answers`
- 错题写入 `wrong_questions`
- 能力统计写入 `ability_stats`
- 错题本、收藏夹、练习历史、学习报告
- Pro 会员中心、套餐展示、订单骨架、会员状态
- Pro 权益 gating：错题本、学习报告、AI 专项出题等
- AI 专项出题：DeepSeek 可生成多题，支持生成中弹窗和取消逻辑
- AI 训练总结页和错题解析流程已做过优化
- 后台题库管理：已从“我的”页进入，题库管理独立于用户 / 反馈后台；支持待审核、已发布、已下架状态筛选
- 后台审核队列：老师可逐题查看题干、选项、答案和解析，编辑后发布或标记需修改
- 题库批量导入：管理员可上传文件，识别题干、选项、答案、解析和分类，预览校验后导入待审核
- 首页外观主题：浅色主题切换，要求所有页面逐步跟随主题
- 中华文化学习范围模块：只在中华文化板块展示，后端有进度接口

## 中华文化学习范围逻辑

目标：

- 仅在中华文化板块显示“学习范围”。
- 显示：已学习 X 题 / 共 Y 题。
- 进度条显示百分比。
- 只把用户第一次作答就正确的题计入“已学习”。
- 背后复习机制使用艾宾浩斯周期，但 UI 不显示“待复习”和“复习周期”模块。
- 底部按钮有“开始复习”和“开始刷题”。

后端相关：

```text
backend/app/routes/questions.py
```

接口：

```text
GET /questions/progress
GET /questions/review-due
```

注意：中华文化公共题库逻辑已倾向让 Z001/Z002 共用更完整的中华文化题库，不要再人为维护两套不一致的中华文化题。

## 会员与付费策略

当前定价设想：

- 月卡：9.9 元/月
- 季卡：24.9 元/季

用户最担心：

- 付费用户觉得 Pro 不值。

已讨论的优化优先级：

1. 优先优化 AI 专项出题质量和训练总结页。
2. 做 Pro 学习报告 / 周报，让用户看到明确提升路径。
3. 优化付费权益展示和首次开通体验。

AI 成本策略：

- 不建议无节制调用大模型。
- 题库可优先调用本地题库。
- AI 主要用于薄弱点诊断、专项补题、总结、错因分析。
- 对 Pro 用户可设置每日或每月 AI 生成额度，避免 9.9 元套餐被 token 成本吃掉。

## 登录与短信/微信登录

手机号验证码骨架已做。

真实短信目前卡点：

- 腾讯云短信签名和模板需要资质审核。
- 没有短信签名和模板 ID，就无法走正式腾讯云短信。
- 可继续保留 mock 验证码用于内测。

微信登录要求：

- 正式域名
- HTTPS
- 微信后台配置网页授权域名
- App 或公众号能力配置

因此微信登录不建议在备案和 HTTPS 完成前强推。

## App 打包状态

用户已安装 HBuilderX 和 Android Studio。

相关文件：

```text
frontend/src/manifest.json
deploy/hbuilderx/android-pack.json
android-wrapper/
```

已讨论：

- HBuilderX 云打包和本地打包都尝试过。
- Android 公共测试证书会有安全提示，正式分发应使用自有证书。
- 短期目标是测试 APK，正式上架还需要签名、隐私合规、域名 HTTPS、备案等。

## 重要操作原则

- 不要上传真实 `.env`。
- 不要删除已有功能，除非用户明确要求。
- 不要大范围重构。
- 不要 `git add .`。
- 不要导入未通过质量检查的题库。
- 题库导入前必须 dry-run。
- 题库生成要保存 review 报告，方便人工复核。
- 题库中不要出现 E 选项；考试题统一 A-D。
- 不要保留“题干若考察”“依据考纲”等元描述。
- 如果生成题目来自资料，不在题干或解析里标注来源。

## 新窗口建议接手顺序

1. 运行：

   ```powershell
   git -c safe.directory="C:/Users/1111/Documents/New project" status -sb
   ```

2. 确认是否继续题库重建。
3. 如果继续中华文化题库：
   - 先写全资料抽取脚本。
   - 抽取 `中华文化/` 下所有可读取文件。
   - 输出抽取报告。
   - 基于抽取文本生成新 500 题。
   - 生成 review 报告。
   - dry-run 导入。
   - 用户确认后再写入 Supabase。
4. 如果继续业务功能：
   - 先确认腾讯云自动部署是否正常。
   - 前端构建用 `npm run build:h5`。
   - 腾讯云部署用 `deploy/tencent-cloud/deploy.sh`。

## 当前最重要的待办

最高优先级：

- 重做中华文化题库生成流程：全资料抽取，而不是只用 Excel。
- 避免继续使用被否定的 batch003 生成逻辑。
- 建立题库质检规则，防止低质量题进入数据库。

次优先级：

- 学习报告接入 DeepSeek 简要建议和详情建议。
- Pro 周报/学习报告增强，提升付费价值感。
- 全局主题继续覆盖更多页面。
- 域名备案、HTTPS、微信登录正式接入。
