# V8C_REBUILD_LOG.md — 三份 v8 DOCX/PDF 最終重建（2026-11-06 UTC）

3 份文件的**正文**與文末 V8C FINAL UPDATE 章節寫入最終結果：T2 80/80 格、T3 388/388 NPZ、T5 provenance 已套用、T6 六模型顯存。舊聲明明確標註 SUPERSEDED。

## 指令

```
python "HANDOFF_20261105/v8/docs/build_v8c_final.py"
```

PDF 轉換 `node cli.js convert --input <docx> --output <pdf>`；頁數 `node cli.js render --pages 1 --dpi 36`（pdfium `pageCount`）。轉換器拒絕覆蓋，故先移除自身舊 v8 PDF 再轉（非凍結 CSV、非 owner 檔）。

## 結果（全部 convert rc=0）

| 文件 | DOCX sha256 | PDF sha256 | 頁數 | 取代段落數 |
|---|---|---|---:|---:|
| ieee_manuscript_en_v8.docx | `756907d48981f70007fe22e284a4d53d403758baa4db36abbddbbb128f05ea5d` | `2d6b72e9c9b3efc63a9ae343798886252721df397216ba8a90455308d32d7796` | 10 | 6 |
| report_internal_zh_v8.docx | `c8d760935bd31f71e9f965cf710e14eb0901b02455a0f4f58e037ea2b4a65cc9` | `3c7483c78f3d5d28c6eeb5ef40afacfcb035439bdce4bfacfdecefd503e2cf8f` | 10 | 6 |
| report_internal_qa_zh_v8.docx | `e7815c51bb132ce7796d8df83cbf0c62308e28df0e3879d116257dc3e4160c42` | `574aacc2056b3e06562c06506ee64e83a9b4f4fd8d502eb361711a0c81ba5baf` | 16 | 2 |

## 被取代的舊聲明（正文中明確標註，未靜默覆蓋）

1. T2「BLOCKED / 8 格最小忠實子集 / 80 格 NOT_EXECUTED」→ **COMPLETED，80/80 有效格**（job 744886，10 個不同預測起點 773–782）。字面 10-seed 擴充仍 `NOT_EXECUTED_BY_PROTOCOL`。
2. T3「2 個 NPZ 隔離 / 386 格」→ **388/388 可讀**（job 744884），表 hash `a7d98ad8…e46`。
3. T6「PARTIAL / 其餘 5 行顯存 NOT_MEASURED」→ **6 個代表性模型全數實測**（744897/744899）；MIFlu/NLinear/PatchTST 的隔離單次前向延遲仍 NOT_MEASURED。
4. T5「provenance 補丁未套用」→ `v8/PAPER_TO_CODE.md` 已套用，打包器優先採用。

仍 UNVERIFIED：官方 JBHI 模板 class 檔。仍 NOT_MEASURED：3 個模型的隔離單次前向延遲。稿件非 submission-ready；結構驗證 PASS = `scientific_readiness: NOT_ASSESSED`。
