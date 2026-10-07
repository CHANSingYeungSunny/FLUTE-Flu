# Stage 5 — 启动命令（未执行；需 D-compute 授权）

所有命令均通过 `sbatch` 提交至 `stingy` 分区；**不在 login node 训练**。
stingy QOS 限制 **1 运行 + 1 排队**，因此作业必须链式提交（轮询 `squeue -u $USER -h -p stingy` 后自动投下一个）。
窗口规则统一为 `--containment strict`（Stage 5 §2.2，目标完整包含于划分）。

## 0. 预检（先于一切训练）

```bash
sbatch recovery/stage5/preflight_sbatch.sh
```

## 1. A2-MIFlu（修正 MIFlu，全文通路，LoRA r=4）— 12 拟合

```bash
#SBATCH --partition=stingy --gres=gpu:a100:1 --time=01:00:00
for L in 24 36 48 60; do
  for S in 42 43 44; do
    python scripts/train_miflu.py --horizon $L --seed $S --reps 1 \
      --epochs 20 --batch 16 --profile author_966 --containment strict \
      --export-dir results/stage5/author_966/miflu/ \
      --ckpt-dir   results/stage5/ckpt/author_966/miflu/
  done
done
```

## 2. A2-NOTEXT（`no_multi`：移除整个文本通路，保留 LoRA）— 12 拟合

```bash
for L in 24 36 48 60; do
  for S in 42 43 44; do
    python scripts/train_ablation.py --variant no_multi \
      --horizon $L --seed $S --reps 1 --epochs 20 --batch 16 \
      --profile author_966 --containment strict \
      --export-dir results/stage5/author_966/notext/
  done
done
```

## 3. A2-NLIN（NLinear）— 12 拟合

```bash
for L in 24 36 48 60; do
  for S in 42 43 44; do
    python scripts/train_nlinear_966.py --horizon $L --seed $S \
      --profile author_966 --containment strict \
      --export-dir results/stage5/author_966/nlinear/
  done
done
```

## 4. 确定性基线（Last Value + Seasonal Naive）— 8 评价

```bash
for L in 24 36 48 60; do
  python scripts/train_naive_966.py --name last_value_naive   --horizon $L \
    --profile author_966 --export-dir results/stage5/author_966/naive/
  python scripts/train_naive_966.py --name seasonal_naive     --horizon $L \
    --profile author_966 --export-dir results/stage5/author_966/naive/
done
```

## 5. Checkpoint 锁定后：统一评分（独立入口）

- 锁定清单：每个 (模型, L, seed) 的最佳验证 epoch 与 checkpoint 哈希；
- 使用与训练分离的评价入口，一次性对**全部**模型与 8 个基线任务评分；
- 保存完整七变量预测与真值（origin、目标 epiweek、lead、seed、L、模型、缩放信息、掩码），可无损重算 `average_MSE_4L`；
- 朴素基线的实现检查已在前置步骤完成，但**其 Test 分数在选模完成前不得展示**。

## 6. A0（作者发布代码重放）— 仍 BLOCKED

```bash
# 需先解决 D-a0-env
python main_ILI_lora.py --pred_len 24 --seq_len 104 --patch_size 24 --stride 2 \
  --gpt_layers 6 --d_model 768 --itr 1 --train_epochs 20 --batch_size 16 \
  --learning_rate 0.0001
# 作者发布默认：--multimodal 0 --PEFT 0 --freeze 1 --pretrain 1
```
