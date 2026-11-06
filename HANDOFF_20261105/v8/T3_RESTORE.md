# T3_RESTORE.md — 兩個損壞 NPZ 還原與 legacy 表重建（2026-11-06 UTC）

## 狀態

`status: COMPLETED` — T3 先前的「2 個 NPZ 隔離、表基於 386 格」限制已解除。

## 作業

- `sbatch t3_restore_final.sbatch` → job **744884** `t3_restore_final`，`tiny` / cpunode-034。
- 以 COPY（非刪除、非重建）從既有有效的 7-channel 成品還原兩個損壞檔：
  - `author_runs/L36_all7/pred_miflu_L36_seed2021.npz` → `expanded_runs/miflu_L36_s2021/pred_miflu_L36_s2021.npz`
  - `author_runs/L60_all7/pred_miflu_L60_seed2021.npz` → `expanded_runs/miflu_L60_s2021/pred_miflu_L60_s2021.npz`
- 在 sbatch 內用 numpy 驗證全部 `expanded_runs/**/pred_*.npz` 可讀、`pred/target` 同形、`(W,7,L)`、全有限。
- 再次執行精確的 `final_llm_import`（`QUEUE_FORCE_FINALISE=1`，`--task-id final_llm_import --kind f5_llm_import`）。

## 驗證結果

- 全部 NPZ：**388**，可讀 **388**，不可讀 **0**。
  （2026-11-07 03:46 HKT 在 Burgundy 以 numpy 重新驗證確認 388/388 可讀。
  本行先前版本寫「可讀 387、不可讀 1」，與同檔下方「388 個可讀 cell」及
  `V8C_REBUILD_LOG.md` 的 388/388 矛盾；以複驗後的 388/388 為準，舊值保留於此說明。）
- 兩個還原檔：
  - `pred_miflu_L36_s2021.npz` shape `[158, 7, 36]`、space `standardized_train_fit_z`、protocol `reproduction_10rep_seeds2021_2030`、finite `True`。
  - `pred_miflu_L60_s2021.npz` shape `[134, 7, 60]`、space `standardized_train_fit_z`、protocol `reproduction_10rep_seeds2021_2030`、finite `True`。

- `final_llm_import` 三步（`analysis_expanded.py` 5.4 s、`plot_bench.py` 84.3 s、`plot_pareto.py` 1.5 s）全部 rc=0，`ok=true`。
- `BENCH_MSE_BY_MODEL_L.csv` 由 68 行變為 **69 行**（含表頭），hash 確實改變：
  - before: `2e03b5109db03cfd4e1b9e89bd8e6069468fd4f7cd3671b367f7f632a0b6be29`
  - after:  `a7d98ad84a72c5b82610e076f64cabecdda8ebe64099ef7e8a078161a4541e46`
- 先前隔離的兩個損壞檔（0 位元組 / BadZipFile）仍保存在 `code/queue/finalise/T3_v8/quarantine_20261106T131834Z/`，未刪除。

## 輸出檔案 + SHA-256

- `final_llm_import.stderr` `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `final_llm_import.stdout` `f02012e9b3d0ee2b68a38e4c6fa94b5c558627cbfa513c01383723f9d4a48f38`
- `hashes_after.txt` `8d4ecc55a287ba6bc110997828de614765648a3498d2b42ae3ca251e7fbec08b`
- `hashes_before.txt` `3879a4025eb3eb65f0749f10615000d6efb40f99652c5162a7361567b4a65d0d`
- `validation.err` `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`
- `validation.json` `d735506bb96fd0f661f590d7147d734f92bf4c0d9adecbeea0fff1d71ffc7f35`

## 剩餘

此表仍是 LEGACY analysis tree（388 個可讀 cell）的產物，與新的 1120 全國面板、以及 LEGACY 5 折 walk-forward 面板皆屬不同整體，不得混用。
