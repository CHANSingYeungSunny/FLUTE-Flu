# T2_FULL80.md — 完整 80 格基礎模型矩陣（2026-11-06 UTC）

## 狀態

`status: COMPLETED` — **80/80 cells `ok`，全部有限，80 個真實 NPZ**。

## 為什麼用 10 個 origins 而不是 10 個 seeds

ChatGPT 要求 `2 models × 4 L × 10 seeds = 80`。兩個檢查點都是**凍結零樣本**模型，沒有訓練步驟，因此訓練 seed 無法產生不同的模型；把同一 origin 用 10 個 RNG seed 重跑只會得到 10 份完全相同的預測，那是偽造 seed 維度。因此 10 次重複改用 **10 個不同的滾動預測起點**（origin rows 773–782），每一格都有自己的 context 與 target，80 個預測與分數都真正不同。
`seed_semantics=NOT_APPLICABLE`；字面的 10-seed 擴充仍為 `NOT_EXECUTED_BY_PROTOCOL`，原因如上。`replicate_kind=rolling_origin`。

## 指令與作業

- `sbatch t2_full80.sbatch` → job **744886** `t2_fm_full80`，`stingy` / A100-SXM4-80GB。
- `/usr/bin/time -v timeout 2400s /home/sychan552/.venvs/mlflu_fm/bin/python -u t2_full80.py`。
- `exit_code=0`，wall 50.71 s，Max RSS 5,088,224 KB。
- `nvidia-smi --query-gpu=memory.used -l 1` 每秒採樣。

## 實測資源

| 項目 | 值 |
|---|---|
| peak VRAM | **2608 MiB**（51 個採樣） |
| Chronos 推理延遲 | **10.229 ± 1.074 ms**（warm-up 1 / repeat 10，batch=7 序列，float32） |
| TimesFM 推理延遲 | **50.906 ± 4.459 ms**（warm-up 1 / repeat 5，batch=7 序列，freq=1） |
| Chronos 載入 | 見 `FOUNDATION_80_REPORT.json` |
| TimesFM 載入 | 見 `FOUNDATION_80_REPORT.json` |
| GPU / 軟體 | NVIDIA A100-SXM4-80GB；torch 2.6.0+cu124；chronos-forecasting 2.3.2；timesfm 1.3.0 |

## 80 格結果

- 總格數 80，`ok` 80，NPZ 80 個；labels {'foundation_chronos': 40, 'foundation_timesfm': 40}。
- 每格 MSE/MAE 見 `FOUNDATION_80_CELLS.csv`；逐格預測見 `full80_out/pred_*.npz`。

| label | L | n origins | 平均 MSE | 最小 MSE | 最大 MSE |
|---|---:|---:|---:|---:|---:|
| foundation_chronos | 24 | 10 | 2.178599 | 0.391328 | 3.731894 |
| foundation_chronos | 36 | 10 | 2.410157 | 2.207397 | 2.621930 |
| foundation_chronos | 48 | 10 | 1.859759 | 1.713536 | 2.012126 |
| foundation_chronos | 60 | 10 | 1.574592 | 1.400231 | 1.754762 |
| foundation_timesfm | 24 | 10 | 2.307629 | 0.729753 | 3.230249 |
| foundation_timesfm | 36 | 10 | 2.462393 | 1.925024 | 2.873582 |
| foundation_timesfm | 48 | 10 | 1.907467 | 1.485368 | 2.275477 |
| foundation_timesfm | 60 | 10 | 1.651942 | 1.394872 | 1.970093 |

## Adapter 與限制（必須隨結果引用）

- 兩個檢查點都是**單變量**；7 個通道以 batch 逐通道獨立預測，**丟失跨通道依賴**，與多變量臂並非資訊集對等。
- 各模型有自身內部歸一化；基準 z-space 直接送入、未做反標準化。
- 零樣本、未訓練/微調；TimesFM 用 `freq=1`（週）、`horizon_len=128` 再切片到 L。
- 標籤 `foundation_chronos` / `foundation_timesfm` 為**獨立 roster**，未併入 28-arm 家族。
- TimesFM 的 `cell_wall_ms` 是該 origin 單次共享 `forecast` 呼叫的牆鐘；4 個 L 是同一次預測的切片，不是 4 次獨立前向。

## 輸出檔案 + SHA-256

- `FOUNDATION_80_CELLS.csv` `627826765ee56f0ea84bac17aa2e073c86f833f0718bc4aa6e0cd7ca0cd192cf`
- `FOUNDATION_80_REPORT.json` `07654f2652d2c3d72cf022f7e836ea78a893db0971210b6da092bf315a683e84`
- 80 個 NPZ 個別雜湊見 `foundation/T2_EVIDENCE_HASHES_FULL80.txt`。
