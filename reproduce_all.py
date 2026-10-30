#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""reproduce_all.py — 一键复现 MIFlu TRACK_C 全链（发表版）.

按序编排七个脚本，从已冻结预测文件出发，重建权威表 + 权威报告
DOCX/MD 镜像，并核对一致性串。每个阶段输出 PASS/FAIL 与产物路径。

用法::

    python reproduce_all.py              # 全链
    python reproduce_all.py --stage 3    # 仅跑到第 3 阶段
    python reproduce_all.py --list       # 列出全部阶段

注意（诚实声明）：
  - 8 模型逐格预测（14 个 .npz）在 test_eval_download.tar.gz / r1c_logs.tgz
    内，本地运行时不存在。若缺失，评分阶段会如实报缺，不会静默跳过。
  - 训练复现需在 GPU 环境运行 hpc_results/official_repo_reproduction_20261006/
    miflu_strict966_train.py（本脚本不含训练）。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PY = sys.executable

STAGES = [
    {
        "name": "score_predictions_independent",
        "desc": "独立评分 14 预测文件 → TRACK_C_TEST_MSE_RANKING.csv",
        "script": "scripts/score_predictions_independent.py",
        "outputs": ["results/v3_clean/scoring/TRACK_C_TEST_MSE_RANKING.csv"],
    },
    {
        "name": "verify_metrics",
        "desc": "逐模型逐 horizon 算术一致性硬校验",
        "script": "scripts/verify_metrics.py",
        "outputs": [],
    },
    {
        "name": "compute_pte_pie_track_c",
        "desc": "PTE/Pie 曲线数据 + fig13",
        "script": "scripts/compute_pte_pie_track_c.py",
        "outputs": ["results/v3_clean/scoring/TRACK_C_PTE_PIE_TABLE.csv"],
    },
    {
        "name": "parse_r1c_results",
        "desc": "R1C 日志解析 → PANEL_TABLE / SURVIVAL_*",
        "script": "scripts/parse_r1c_results.py",
        "outputs": [
            "results/v3_clean/final/STRICT_966_PANEL_TABLE.csv",
            "results/v3_clean/final/R1C_SURVIVAL_LEADERBOARD.csv",
        ],
    },
    {
        "name": "build_track_c_docx",
        "desc": "权威报告 DOCX + docx_inputs/ 权威表",
        "script": "scripts/build_track_c_docx.py",
        "outputs": [
            "reports/concise_final/REPORT_精简终版.docx",
            "hpc_results/official_repo_reproduction_20261006/r1_v2_verification_20261007/docx_inputs/TRACK_C_TEST_MSE_RANKING.csv",
        ],
    },
    {
        "name": "extract_docx_to_md",
        "desc": "DOCX → MD 镜像 + 六个一致性串 + SHA 校验",
        "script": "scripts/extract_docx_to_md.py",
        "outputs": ["reports/concise_final/REPORT_精简终版.md"],
    },
    {
        "name": "verify_report_parity",
        "desc": "DOCX↔MD 双向 parity 终检",
        "script": "scripts/verify_report_parity.py",
        "outputs": [],
    },
]


def run_stage(idx: int, stage: dict) -> bool:
    script = ROOT / stage["script"]
    if not script.exists():
        print(f"[FAIL] {stage['name']}: 脚本不存在 {stage['script']}")
        return False
    print(f"\n{'='*60}")
    print(f"[{idx}/{len(STAGES)}] {stage['name']} — {stage['desc']}")
    print(f"{'='*60}")
    result = subprocess.run(
        [PY, str(script)],
        cwd=str(ROOT),
        capture_output=False,
    )
    if result.returncode != 0:
        print(f"[FAIL] {stage['name']} 退出码 {result.returncode}")
        return False
    for out in stage["outputs"]:
        p = ROOT / out
        status = "OK" if p.exists() else "MISSING"
        print(f"  产物 {out}: {status}")
    print(f"[PASS] {stage['name']}")
    return True


def main() -> int:
    args = sys.argv[1:]
    if "--list" in args:
        for i, s in enumerate(STAGES, 1):
            print(f"  {i}. {s['name']}: {s['desc']}")
        return 0
    limit = len(STAGES)
    if "--stage" in args:
        limit = int(args[args.index("--stage") + 1])

    for i, stage in enumerate(STAGES[:limit], 1):
        if not run_stage(i, stage):
            print(f"\n中止：阶段 {i} 失败。请检查缺失输入（预测 .npz 或脚本路径）。")
            return 1

    print(f"\n{'='*60}")
    print(f"全链完成：{limit} 个阶段全部 PASS")
    print(f"权威报告 DOCX: reports/concise_final/REPORT_精简终版.docx")
    print(f"权威表: hpc_results/.../docx_inputs/TRACK_C_TEST_MSE_RANKING.csv")
    print(f"{'='*60}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
