#!/usr/bin/env python3
"""
Progress checker — every 2 hours, scan task_tracker.md,
report completion status, and suggest next actions.

Usage: python3 check_progress.py
Designed to be called by crontab every 2 hours.
"""

import re
import os
import sys
from datetime import datetime
from pathlib import Path

TRACKER = Path(__file__).parent / "task_tracker.md"
PROGRESS_LOG = Path(__file__).parent / "progress_log.md"
LESSONS = Path(__file__).parent / "lessons_learned.md"

PHASES = {
    "Phase 1": {"prefix": "P1", "items": 5, "name": "侦察审计"},
    "Phase 2": {"prefix": "P2", "items": 13, "name": "最小数据底座"},
    "Phase 3": {"prefix": "P3", "items": 12, "name": "本地MCP"},
    "Phase 4": {"prefix": "P4", "items": 7, "name": "Skills"},
    "Phase 5": {"prefix": "P5", "items": 9, "name": "验收测试"},
}

def parse_tracker():
    """Parse task_tracker.md and count completed/pending items per phase."""
    if not TRACKER.exists():
        return {"error": "task_tracker.md not found"}
    
    content = TRACKER.read_text(encoding="utf-8")
    results = {}
    
    for phase_key, info in PHASES.items():
        prefix = info["prefix"]
        # Match lines like: - [x] P1.1 ...  or  - [ ] P1.1 ...
        pattern = rf"- \[([ x])\] ({prefix}\.\d+)"
        matches = re.findall(pattern, content)
        total = len(matches)
        completed = sum(1 for m in matches if m[0] == "x")
        results[phase_key] = {
            "name": info["name"],
            "total": total,
            "completed": completed,
            "pending": total - completed,
            "progress_pct": round(completed / total * 100, 1) if total > 0 else 0,
        }
    
    return results

def find_next_actions(results):
    """Identify the first incomplete item in each phase that has incomplete predecessors."""
    if not TRACKER.exists():
        return ["ERROR: task_tracker.md not found"]
    
    content = TRACKER.read_text(encoding="utf-8")
    actions = []
    
    for phase_key, info in PHASES.items():
        prefix = info["prefix"]
        pattern = rf"- \[ \] ({prefix}\.\d+) (.+)"
        matches = re.findall(pattern, content)
        if matches:
            first_id, first_desc = matches[0]
            actions.append(f"  - {first_id}: {first_desc.strip()}")
            break  # Only suggest the very next action across all phases
    
    if not actions:
        actions.append("  - ALL TASKS COMPLETE! 🎉")
    
    return actions

def check_artifacts():
    """Check if expected deliverable artifacts exist."""
    base = Path(__file__).parent
    artifacts = {
        "Phase 1": [
            base / "third_party",
            base / "audits" / "project_matrix.csv",
            base / "audits" / "source_endpoint_catalog.md",
            base / "audits" / "reuse_decisions.md",
        ],
        "Phase 2": [
            base / "pyproject.toml",
            base / "src" / "adapters",
            base / "src" / "lake",
            base / "db" / "market.duckdb",
        ],
        "Phase 3": [
            base / "mcp",
        ],
        "Phase 4": [
            base / "skills",
        ],
        "Phase 5": [
            base / "tests",
        ],
    }
    
    status = {}
    for phase, paths in artifacts.items():
        existing = [str(p.relative_to(base)) for p in paths if p.exists()]
        missing = [str(p.relative_to(base)) for p in paths if not p.exists()]
        status[phase] = {"existing": existing, "missing": missing}
    
    return status

def generate_report():
    """Generate the progress report."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    results = parse_tracker()
    artifacts = check_artifacts()
    
    if "error" in results:
        return f"[{now}] ERROR: {results['error']}"
    
    total_all = sum(r["total"] for r in results.values())
    completed_all = sum(r["completed"] for r in results.values())
    overall_pct = round(completed_all / total_all * 100, 1) if total_all > 0 else 0
    
    lines = []
    lines.append(f"## 进度检查 — {now}")
    lines.append("")
    lines.append(f"**总进度: {completed_all}/{total_all} ({overall_pct}%)**")
    lines.append("")
    lines.append("| 阶段 | 完成 | 总数 | 进度 |")
    lines.append("|---|---|---|---|")
    for phase_key, r in results.items():
        bar = "█" * int(r["progress_pct"] / 10) + "░" * (10 - int(r["progress_pct"] / 10))
        lines.append(f"| {phase_key} {r['name']} | {r['completed']} | {r['total']} | {bar} {r['progress_pct']}% |")
    lines.append("")
    
    # Next actions
    actions = find_next_actions(results)
    lines.append("### 下一步行动")
    lines.append("")
    for a in actions:
        lines.append(a)
    lines.append("")
    
    # Artifact status
    lines.append("### 交付物状态")
    lines.append("")
    for phase, status in artifacts.items():
        if status["missing"]:
            lines.append(f"- **{phase}** 缺失: {', '.join(status['missing'])}")
        else:
            lines.append(f"- **{phase}** ✅ 所有预期交付物已存在")
    lines.append("")
    
    # Decision: continue or modify
    if overall_pct == 0:
        decision = "⚠️ 无进展 — 需要立即启动 Phase 1"
    elif overall_pct < 100:
        decision = f"🔄 进行中 — 继续执行当前任务"
    else:
        decision = "✅ 全部完成 — 可进入验收"
    
    lines.append(f"**决策: {decision}**")
    lines.append("")
    lines.append("---")
    
    return "\n".join(lines)

def main():
    report = generate_report()
    print(report)
    
    # Append to progress log
    with open(PROGRESS_LOG, "a", encoding="utf-8") as f:
        f.write(report + "\n")
    
    # Update task_tracker.md progress table
    if TRACKER.exists():
        content = TRACKER.read_text(encoding="utf-8")
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        results = parse_tracker()
        if "error" not in results:
            total_all = sum(r["total"] for r in results.values())
            completed_all = sum(r["completed"] for r in results.values())
            overall_pct = round(completed_all / total_all * 100, 1) if total_all > 0 else 0
            
            if overall_pct == 0:
                status = "待启动"
            elif overall_pct < 100:
                status = "进行中"
            else:
                status = "已完成"
            
            new_row = f"| {now} | {completed_all} | {total_all} | {status} | 自动检查 |"
            
            # Find the progress table and add row
            lines = content.split("\n")
            updated = False
            for i, line in enumerate(lines):
                if line.startswith("| 2026-06-29 22:41"):
                    # Insert new row after the last data row in the table
                    # Find the next non-table line
                    j = i + 1
                    while j < len(lines) and lines[j].startswith("|"):
                        j += 1
                    # Insert before the separator/empty line
                    lines.insert(j, new_row)
                    updated = True
                    break
            
            if updated:
                TRACKER.write_text("\n".join(lines), encoding="utf-8")
                print(f"\n[check_progress] Updated task_tracker.md with progress row at {now}")

if __name__ == "__main__":
    main()
