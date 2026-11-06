# T6_FINAL_SWEEP.md — 六個代表性模型全部實測（2026-11-06 UTC）

## 狀態

`status: COMPLETED (all six representative models measured)` — 先前的
`PARTIAL (IMPROVED)` 與更早的「peak VRAM 全部 NOT_MEASURED」皆已被取代。

## 作業

- `sbatch t6_sweep.sbatch` → job **744897** `t6_final_sweep`，`stingy` / gpu-a100-03 /
  NVIDIA A100-SXM4-80GB，driver 580.167.08。
- `sbatch t6_miflu_fix.sbatch` → job **744899** `t6_miflu_fix`，修補 744897 中 MIFlu
  步驟的 `Permission denied`（腳本少了 python 前綴，rc=126）。
- 每個模型各自啟動 `nvidia-smi --query-gpu=memory.used -l 1` 採樣，並用
  `/usr/bin/time -v` 記錄牆鐘；原始日誌在 `v8/resource_logs/final_sweep/`。
- 對照作業：**744532**（MIFlu 首次實測）、**744886**（full80 的兩模型聯合實測）。

## 實測結果（全部來自 A100-SXM4-80GB）

| 模型 | peak VRAM (MiB) | 採樣數 | 真實模型前向延遲 | 作業牆鐘 | 載入 |
|---|---:|---:|---|---:|---:|
| MIFlu | **4816** | 46 (744899) / 63 (744532) | 未隔離單次前向；完整 7 通道 cell 匯出 62.94 s | 62.94 s | — |
| NLinear | **558** | 36 | 未隔離；完整 20 epoch 訓練+匯出 | 35.73 s | — |
| PatchTST | **720** | 7 | 未隔離；完整 20 epoch 訓練+匯出 | 6.86 s | — |
| GPT-2（凍結語言編碼器） | **1070** | 11 | **6.98 ± 0.097 ms**（warm-up 1 / repeat 10） | 10.94 s | 6.3224 s |
| Chronos Bolt Tiny | **596** | 6 | **9.854 ± 0.337 ms**（warm-up 1 / repeat 20） | 5.93 s | 0.4307 s |
| TimesFM 2.0-500m | **2594** | 11 | **48.273 ± 3.531 ms**（warm-up 1 / repeat 10） | 10.19 s | 6.9875 s |

軟體：MIFlu/NLinear/PatchTST 用 Python 3.9.25 + torch 2.5.1；
GPT-2/Chronos/TimesFM 用 Python 3.11.13 + torch 2.6.0+cu124 +
transformers 5.22.1 / chronos-forecasting 2.3.2 / timesfm 1.3.0。
batch/precision 逐行記錄於 `RESOURCE_MEASUREMENTS.csv`。

## 交叉驗證

- full80（744886）兩模型聯合 peak VRAM **2608 MiB**（51 採樣），與 TimesFM 單測 2594 MiB 一致。
- full80 的 Chronos **10.229 ± 1.074 ms**（repeat 10）、TimesFM
  **50.906 ± 4.459 ms**（repeat 5），與本 sweep 的 9.854 / 48.273 ms 一致。
- 744532 與 744899 兩次獨立 MIFlu 量測都得到 **4816 MiB**。

## 明確的範圍與仍缺的量

- 所有數值皆為**代表性子集**，每行 `scope=subset_only_not_full_1120`；
  **不做 full-1120 Pareto 宣稱**。
- MIFlu / NLinear / PatchTST 量到的是真實完整作業（cell 匯出或訓練+匯出）的牆鐘與峰值顯存，
  **沒有隔離的 warm-up + repeated 單次前向延遲**——CSV 中明確標為 `NOT_MEASURED`，
  不拿舊的 NPZ 評分路徑數字（0.0287–0.0297 ms）冒充；這些舊值已移到
  `npz_scoring_path_latency_ms_*` 欄並標明「不是模型前向」。
- 代表性凍結編碼器實測為**本機快取中的 GPT-2**；原列的
  DeepSeek-R1-Distill-Qwen-1.5B 24 s 訓練牆鐘屬另一個編碼器，僅作背景保留，未混寫。
- `RESOURCE_MEASUREMENTS.csv` sha256 `9574eeff6f0e39ddba6488b2e8fe8ef09b763c90fdd27223d7960b8f886b1117`。
