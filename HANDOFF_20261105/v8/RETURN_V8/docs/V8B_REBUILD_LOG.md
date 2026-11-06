# V8B 重建记录 — 2026-11-06 UTC

3 份 v8 DOCX/PDF 已重建，正文写入 T2 / T6 / T4 的最终结果，并明确标注早期声明已被取代。

## 命令

```
python "HANDOFF_20261105/v8/docs/build_v8b_final.py"
```

PDF 转换：`node cli.js convert --input <docx> --output <pdf>`；页数：`node cli.js render --pages 1 --dpi 36`（pdfium，`pageCount`）。
转换器拒绝覆盖已存在 PDF，故先移除自身产生的旧 v8 PDF 再转换（非冻结 CSV、非 owner 文件）。
英文稿第一次转换因 EEXIST 失败，修复后重跑产生重复 V8B 章节，已删除重复段落并单独重新转换。

## 结果（全部 convert rc=0）

| 文件 | DOCX sha256 | PDF sha256 | 页数 |
|---|---|---|---|
| ieee_manuscript_en_v8 | `2910848a9726ad7c513bbe099793a832fb37d22d7cf8449ad1f73549f367c756` | `bcbc73644b56eeda790302438564dc0683d1a0cdab27425a68a136cc9ef7329d` | 9 |
| report_internal_zh_v8 | `31e8b8b858bfa13dd4d8da70dbe0d19b63f9075997f77113c9beb663dd52a755` | `5b255734191214626053f9557bde405005b8f2b33c423f4571a72365f3bb786e` | 9 |
| report_internal_qa_zh_v8 | `55c7383281cf06cbc69e2c55b0fe544ef18ba62040c6a7c03923540004772749` | `48f598b0e58bf02278b6ddc2784577b25eab0bf5d4336c80e85fff31bac4dbec` | 15 |

## 被取代的旧声明（正文中均明确标注 SUPERSEDED）

1. T2 基础模型 BLOCKED / 无权重 / 无环境 / 无 pilot → `COMPLETED_WITH_DOCUMENTED_SCOPE`（8 个有效零样本单元，pilot 744589、matrix 744607）。
2. 全部 peak VRAM NOT_MEASURED → MIFlu 实测 4816 MiB（63 采样，job 744532）；其余 5 行仍 NOT_MEASURED。
3. T4 CDC vintage PARTIAL/BLOCKED → COMPLETED（项目冻结 `02_数字表格/cdc_vintage*.csv`，18 季 as-of 峰值重评分）。
4. 80 格 10-seed 扩展仍 `NOT_EXECUTED_BY_PROTOCOL`（冻结零样本模型无训练 seed 维度）；T5 模板 class 档仍 UNVERIFIED。

原 Q01–Q25 题目与答案保留；稿件仍非 submission-ready；结构验证 PASS 等于 `scientific_readiness: NOT_ASSESSED`。
