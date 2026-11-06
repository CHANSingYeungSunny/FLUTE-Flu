# AGENT HARD RULE (read AGENTS.md first)

---

## HARD RULE — Burgundy login node (2026-11-05 incident, applies to EVERY agent)

**All model work must run via `sbatch` on a compute node.** Never run inference,
`torch.load`, `import torch/transformers`, recursive `du -sh` or downloads on the
login node — that caused a ~2-hour outage on 2026-11-05. Login node is only for
`squeue`/`sacct`/`scontrol`/`mmlsquota`/short `ls`/`cat`.

If ssh authenticates but returns zero bytes: disable
`ServerAliveInterval/CountMax`, open ONE connection with no retry loop, and issue
`pkill` as the **FIRST** command in the first shell window (a `D`-state task keeps
`SIGKILL` pending; `ps` first lost a real window). Never `scancel`.

Full rules: **`AGENTS.md`** (root). SOP: `04_详细说明文档/HPC_LOGIN_NODE_DSTATE_RECOVERY.md`.
Incident: `HANDOFF_20261105/INCIDENT_20261105_LOGIN_NODE_DSTATE.md`.
Tool: `05_程序代码/hpc_login_node_recover.py`.
Also: a `legacy_done.tsv` row is NOT a validated cell, and `squeue -h` prints a
`Last update ...` line so `grep -q .` is not a valid job-existence guard.


# Start here revision 9.2

Read README.md and DELIVERY_INDEX.json for current roles. For DeepSeek execution, follow handoff_revision9/PROMPT_TO_DEEPSEEK.md and RETURN_CONTRACT.json. For a future return to ChatGPT, use handoff_revision9/PROMPT_RETURN_TO_CHATGPT.md. Historical scientific results remain distinct from dated execution status. Do not use older prompts or manuscript builders to overwrite this release. The current authoring entry point is scripts/build_delivery_v9.py.

Revision 9.1 changes FYP Part A metadata only. The official progress template requires meetings and weekly hours; keep them blank until the owner supplies actual values. The manuscript, internal report, deck and English notes retain revision-9 scientific contents.

Revision 9.2: the Chinese main internal report is concise; Q01–Q25 and all paper reasoning are in 01_最终报告/report_internal_qa_zh.docx / .pdf. The full build now runs scripts/split_internal_qa_zh.py after the current Chinese addendum. Keep these two documents separate and synchronized.
