# 港研通项目入口

港研通是面向港澳台考研用户的移动端刷题 App。当前项目包含 uni-app/Vue 3 前端、FastAPI 后端、Supabase 数据库、题库生成与导入脚本、部署配置和多科目资料。

## 快速定位

```text
frontend/            uni-app 前端，H5 / 微信小程序 / App 构建入口
backend/             FastAPI 后端，接口、服务和配置
database/            Supabase schema 与增量 SQL
scripts/             题库生成、校验、修复、导入和审计脚本
data/                题库 JSON、抽取文本、批次报告和导入中间产物
docs/                项目上下文、架构、题库规范、回归测试和专题文档
deploy/              腾讯云部署脚本与说明
business_plan_assets/商业计划书与路演素材，含可编辑 PPTX/SVG/PNG
ios-swiftui/         iOS SwiftUI 包装方案留存
materials/           题库生成参考材料与整理稿
中华文化/             中华文化题库资料
英语运用/             英语运用题库资料
数学基础/             Z002 数学基础题库资料
逻辑推理/             Z001 逻辑推理题库资料
```

## 本地运行

后端：

```powershell
cd backend
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

后端接口文档：

```text
http://127.0.0.1:8000/docs
```

前端 H5：

```powershell
cd frontend
npm run dev:h5
```

前端构建：

```powershell
cd frontend
npm run build:h5
npm run build:mp-weixin
```

## 文档入口

- [docs/project_context.md](docs/project_context.md)：当前项目状态、部署、题库重建方向和接手顺序。
- [docs/question_bank_generation_rules.md](docs/question_bank_generation_rules.md)：英语运用、Z002 数学基础题库生成硬规则。
- [docs/ai_question_generation_spec.md](docs/ai_question_generation_spec.md)：通用 AI 题库 JSON 格式和导入工作流。
- [docs/culture_explanation_model_v3.md](docs/culture_explanation_model_v3.md)：中华文化教学型解析 V3 字段契约、题型路由和质量门。
- [docs/logic_question_model_v2.md](docs/logic_question_model_v2.md)：逻辑推理 V2 分类、2025 真题校准、形式化验证和审计分级。
- [docs/wechat_miniprogram_architecture.md](docs/wechat_miniprogram_architecture.md)：微信小程序技术预检说明。
- [docs/wechat_miniprogram_regression_checklist.md](docs/wechat_miniprogram_regression_checklist.md)：小程序发布前回归清单。
- [deploy/tencent-cloud/README.md](deploy/tencent-cloud/README.md)：腾讯云部署说明。
- [backend/README.md](backend/README.md)：后端启动、部署和核心接口。
- [frontend/README.md](frontend/README.md)：前端页面范围和 API 配置。

## 题库导入红线

- 不上传、打印或提交真实 `.env` 内容。
- 不使用 `git add .`。
- 不正式导入未经 dry-run 的题库。
- dry-run 未确认 `Invalid questions: 0` 时不得正式导入。
- 不直接导入用户明确否定的旧批次。
- 批量导入前必须让用户明确同意。

常用 dry-run：

```powershell
& "C:\Users\1111\Documents\New project\backend\.venv\Scripts\python.exe" scripts\import_questions.py --file data\<file>.json --dry-run
```

常用批量导入：

```powershell
& "C:\Users\1111\Documents\New project\backend\.venv\Scripts\python.exe" scripts\import_questions_bulk.py --file data\<file>.json --batch-size 100
```

## 题库审计入口

本地批次库存与线上导入状态比对：

```powershell
& "C:\Users\1111\Documents\New project\backend\.venv\Scripts\python.exe" scripts\inventory_question_batches.py
```

输出：

```text
reports/question_batch_inventory.md
reports/question_batch_inventory.json
```

线上题库只读质量体检：

```powershell
& "C:\Users\1111\Documents\New project\backend\.venv\Scripts\python.exe" scripts\audit_live_question_bank.py
```

输出：

```text
reports/question_bank_live_audit.md
reports/question_bank_live_audit.json
```

## Git 注意事项

当前工作区经常有大量未跟踪的题库批次、资料抽取产物和生成脚本。提交前先查看范围：

```powershell
git status --short
```

只暂存本轮明确需要提交的文件，避免把未审核题库、临时资料或大文件误提交。
