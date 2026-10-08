# 精简终版报告 — 渲染/结构审计

环境说明：本环境未安装 LibreOffice/soffice，无法执行 DOCX→PDF→PNG 的逐页视觉渲染。以下以“可打开 + 部件级结构”审计替代，覆盖表宽、图片嵌入、标题层级、A4、字体、无空表、无未解析占位符等要点。

## 检查项

[PASS] DOCX opens with python-docx
[PASS] A4 page size (210x297mm) — 210x297mm
[PASS] Heading-1 sections present (>=8) — 11 H1
[PASS] Tables present (>=5) — 10 tables
[PASS] Figures embedded — 6 images
[PASS] No empty tables — []
[PASS] CJK Normal font set — Microsoft YaHei
[PASS] Cover page author-data SHA present in text
[PASS] Final champion value present
[PASS] PTE/PIE section present
[PASS] Track C unchanged (no retrain claim) — frozen contract used verbatim

DOCX SHA-256: 73f97cc2439f56950b37fa9a8726cac1f84e375b54553700f93b2f196b2ea5f6

## 逐页视觉渲染

未执行（缺 LibreOffice）。建议在有 Word / LibreOffice 的环境中打开本 DOCX，确认：每页表宽、重复表头、无空白页、无孤立图注、无裁切图、无标题单字换行、A4 页面、页码、中文字形、PTE/PIE 表完整、最终排名视觉突出。
