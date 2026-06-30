# Multi-Agent Governance Structure

## 智能体角色定义

### Agent 1: 项目经理 (PM Agent)
- **执行者**: Claude Code 实例 #1
- **职责**:
  - 监控整体进度，识别阻塞点
  - 协调各智能体之间的任务依赖
  - 风险预警与升级
  - 每轮检查产出 `pm_report.md`（进度/风险/决策/下一步）
  - 验收交付物质量
- **输入**: `task_tracker.md`, `progress_log.md`, 各agent产出
- **输出**: `agents/pm_report.md`

### Agent 2: 目标与需求管理专家 (Requirements Agent)
- **执行者**: Claude Code 实例 #2
- **职责**:
  - 将文章中的规划转化为可验证的需求条目
  - 定义每条需求的验收标准 (Acceptance Criteria)
  - 追踪需求覆盖矩阵 (Requirements Traceability)
  - 识别遗漏需求和隐性需求
  - 每轮检查产出 `req_report.md`（需求状态/缺口/变更建议）
- **输入**: 原始文章规划, `task_tracker.md`, 代码实现
- **输出**: `agents/req_report.md`, `agents/requirements_matrix.md`

### Agent 3: 实施工程师 (Implementation Agent)
- **执行者**: Cascade (本会话)
- **职责**:
  - 执行编码任务
  - 修复缺陷
  - 运行测试验证
- **输入**: PM和Requirements的指令
- **输出**: 代码变更

## 协作流程

```
Requirements Agent → 定义/更新需求 → PM Agent
PM Agent → 拆解任务/分配优先级 → Implementation Agent
Implementation Agent → 完成代码 → PM Agent 验收
PM Agent → 更新进度 → Requirements Agent 验证覆盖
```

## 启动顺序
1. Requirements Agent 先运行，产出需求矩阵
2. PM Agent 基于需求矩阵审查当前状态
3. 两者产出合并后，Implementation Agent 执行剩余工作
