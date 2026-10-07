# DEVIATION LEDGER

日期：2026-10-06　　范围：A0 / A1 / A2 三条轨相对「作者发布代码 + 论文披露内容」的每一处偏离。
规则：**每一条偏离必须写明来源位置、原因、精确改动、预期影响、是否有作者确认。** 无作者确认者一律标 `NOT_CONFIRMED_BY_AUTHOR`。

---

## D-01　`einops` 缺失 — A0 兼容层

| 项 | 内容 |
|---|---|
| 来源 | `models/GPT4TS_lora.py` L9 `from einops import rearrange` |
| 原因 | 环境未安装 einops |
| 改动 | 在独立 `sys.path` 目录实现发布代码用到的**恰好 3 个** pattern：`'b l m -> b m l'`、`'b m n p -> (b m) n p'`、`'(b m) l -> b l m'`；其他 pattern 抛异常 |
| 预期影响 | **行为性**（真的执行排列）。实现为正确排列，不是 stub |
| 作者确认 | `NOT_CONFIRMED_BY_AUTHOR` |
| 状态 | 已记录于 `recovery/a0/a0_compat.py` |

## D-02　`embed.py` 缺失 — A0 兼容层

| 项 | 内容 |
|---|---|
| 来源 | `GPT4TS_lora.py` L10 `from embed import DataEmbedding, DataEmbedding_wo_time` |
| 原因 | 发布树中 `embed.py` 缺失，仅剩 `__pycache__/embed.cpython-39.pyc` |
| 改动 | 从作者**自己的** `.pyc` 反汇编恢复 8 个类 |
| 预期影响 | **无**：这两个符号在发布代码中**导入后从未被引用**；真实投影是 `nn.Linear(patch_size, d_model)`（L92） |
| 作者确认 | `NOT_CONFIRMED_BY_AUTHOR` |
| 状态 | 已记录 |

## D-03　`peft>=0.8` 移除 `prepare_model_for_int8_training` — A0 兼容层

| 项 | 内容 |
|---|---|
| 来源 | `GPT4TS_lora.py` L17 import |
| 原因 | peft 0.17.1 已移除该符号 |
| 改动 | no-op callable |
| 预期影响 | **无**：该符号在发布代码中**只出现在注释里**（L85），且 `PEFT` 默认 0，该分支从不执行 |
| 作者确认 | `NOT_CONFIRMED_BY_AUTHOR` |

## D-04　`transformers.models.llama` 缺失 — 本轮 probe 新增 shim

| 项 | 内容 |
|---|---|
| 来源 | `GPT4TS_lora.py` L8 `from transformers.models.llama.modeling_llama import LlamaModel` |
| 原因 | 本地 transformers 4.25.0 < 4.28，无 llama 模块 |
| 改动 | 注册一个 `LlamaModel` 类，**被实例化时直接抛异常** |
| 预期影响 | **无**：`backbone='gpt2'`，该分支不执行；抛异常保证不会静默顶替真实实现 |
| 记录位置 | probe JSON 的 `dead_import_shims` 字段 |
| 作者确认 | `NOT_CONFIRMED_BY_AUTHOR` |
| 备注 | **HPC 环境（mlflu_hpc）有真实 peft/transformers，此 shim 只可能出现在本地运行** |

## D-05　文本内容替换的注入方式（probe 专用）

| 项 | 内容 |
|---|---|
| 来源 | `GPT4TS_lora.py` L132 硬编码相对路径 `./dataset/illness/text_emb/text_emb_label_0507_{L}.txt` |
| 原因 | 需要「等长不同内容」对照，但不能写进作者树（违反不修改规则） |
| 改动 | 在**调用期间**替换 `np.loadtxt` 的返回值，形状/dtype 完全相同 |
| 预期影响 | **无**：形状相同 → 序列长度相同 → dropout RNG 消耗相同 → 差异只能来自内容 |
| 作者确认 | `NOT_CONFIRMED_BY_AUTHOR` |

## D-06　A2 的 `patch_num` 与作者一致但**语义不同**

| 项 | 内容 |
|---|---|
| 来源 | 作者 `patch_num = (seq_len - patch_size)//stride + 1` 然后 `+= 1` |
| 事实 | T=104, Lp=24, S=2 → **42 patches**（作者与 A2 相同） |
| 改动 | 无 |
| 说明 | 此条为**澄清**而非偏离。作者的多余 `+1` 是 ReplicationPad1d 造成的真实需要，不是 bug |

## D-07　A2 的真实算法偏离（相对发布代码）

| 项 | 发布代码 | A2 | 原因 | 作者确认 |
|---|---|---|---|---|
| **文本通路位置** | 文本拼在 patch **之后**，因果注意力使其不可达 | 文本在**前**，读取文本后的 patch 位置 | 使文本真正参与预测 | `NOT_CONFIRMED_BY_AUTHOR` — 这是**声明式算法变更** |
| **LoRA** | `PEFT=0` 默认 → **从不应用** | 真实应用 `c_attn`，r=4，73,728 参数 | 论文要求 LoRA | `NOT_CONFIRMED_BY_AUTHOR`（论文写了 LoRA，但没写代码怎么开） |
| **参数冻结** | `freeze` 是 no-op（100% 可训练） | GPT-2 冻结，仅 LoRA + 指定层解冻 | 论文写"只微调 PE 与 layer-norm" | 部分符合论文文字 |
| **checkpoint 选择** | 每 epoch 读 Test，用 Test MSE 选权重 | **validation-only**，训练全程不读 Test | 消除 Test 泄漏 | 无争议的修正 |
| **Test 变量覆盖** | 仅 `feat_id = [0]` | 全部 7 变量 | 论文用 7 变量 | 无争议的修正 |
| **Test 批次** | `drop_last` 丢尾批 | 不丢弃 | 保证覆盖全部合法 origin | 无争议的修正 |
| **窗口归属** | 未定义 | `--containment strict`，目标块必须完整落位 | 消除跨划分泄漏 | 无争议的修正 |
| **七变量联合** | 逐特征 `(B,T,M=1)` | 联合 7 变量 | 论文为多变量任务 | 需注明 |

> **A2 = 修正后的公平比较基准，不是「未修改的论文复现」。** 命名必须一直保持这个区分。

## D-08　A1 的重建参数（无证据）

| 项 | 值 | 状态 |
|---|---|---|
| epochs | 20 | **reconstructed assumption**（论文未披露；作者默认 1） |
| learning rate | 5e-4 | **reconstructed assumption**（论文未披露；作者默认 1e-4） |
| optimizer / scheduler | Adam / 无 | reconstructed assumption |

详见 `HYPERPARAMETER_PROVENANCE.md`。**禁止**为逼近论文数值而搜索这些值。

## D-09　本轮（2026-10-06）的偏离

| 项 | 内容 |
|---|---|
| probe 的阳性对照 | 对发布 `forward` 源码做恰好两处替换后 `exec`；**声明式算法变更**，结果单独报告，不混入 A0 判决 |
| probe 的 flag control | 额外跑一次 `multimodal=0`，**仅用于说明 A0 信号的来源**，不作为文本证据 |
| 本地 compat 目录 | `local_compat/`（einops/embed/peft shim），**HPC 运行不需要**；已单独存放，不进入作者树 |
| 未提交任何 Slurm 作业 | SSH 不可达（见 `STATUS_BEFORE_CONTINUATION.md` §0） |

## D-10　【新增 2026-10-06 · A1 实测】作者 argparse 的 `--target_modules` 类型陷阱

| 项 | 内容 |
|---|---|
| 来源 | `main_ILI_lora.py` L47 `parser.add_argument('--target_modules', type=str, default=["c_attn"])` |
| 现象 | **默认值是 list，但 `type=str`**。因此任何命令行覆盖都会变成**字符串**而非 `["c_attn"]` |
| 后果 | `get_peft_model` 抛 `ValueError: Target modules c_attn not found in the base model` → **A1 直接崩溃**（实测作业 606361，7 秒即退出） |
| 诊断 | CPU 作业 606362 逐一实测 7 种写法（ZERO GPU-hours） |
| 结论 | `target_modules=["c_attn"]`（list）✅ trainable=147,456；`"c_attn"`（字符串）❌；`["attn.c_attn"]` ✅；`r"^.*c_attn$"` ✅ |
| **A1 的处理** | **不传 `--target_modules`**，让作者自己的 list 默认值生效 |
| 性质 | **不是**算法修改，是**避免踩作者 argparse 的类型陷阱**。已在 `miflu_a1_array.sbatch` 内联注释 |
| 作者确认 | `NOT_CONFIRMED_BY_AUTHOR` |

> 附带证实：`type(c_attn)` 在 transformers 4.57.6 上是 `transformers.pytorch_utils.Conv1D`，**peft 0.17.1 仍能正确注入 LoRA**（trainable 147,456 = 12 层 × 12,288）。所以「peft 不支持 Conv1D」不是问题，类型陷阱才是。

## D-11　【新增 2026-10-06 · 环境】scratch 用户配额超额

| 项 | 内容 |
|---|---|
| 实测 | `mmlsquota -u sychan552`：scratch 已用 **433,264,576 KB ≈ 413 GB**，配额 **314,572,800 KB = 300 GB**，`grace = expired` |
| 后果 | `/gpfs1/scratch` 上的写入**间歇性失败**（`scp` 报 `Disk quota exceeded`） |
| 本轮的应对 | 所有**写入**改到 `/gpfs1/home/sychan552/`（home 用 25.5/50 GB，有 headroom）；scratch 仅作**只读**（作者仓库 checkout） |
| 未做的事 | **未删除任何文件**。占用大户见 `STATUS_BEFORE_CONTINUATION.md`（CHATTIME 190 GB + 多个 `innovation_deploy_root_v3_*` 各 10–52 GB） |
| 需要用户决定 | 是否清理那些部署暂存目录以解除配额（本轮不擅自删除） |

## D-12　【新增 2026-10-06 · 调度】stingy QOS 限制

| 项 | 值 |
|---|---|
| `sacctmgr show qos partition-stingy` | `MaxSubmit=1  MaxJobsPU=1  MaxWall=06:00:00` |
| 后果 | **同一时刻只能有 1 个作业**；`--array=1-2` 会被拒（`QOSMaxSubmitJobPerUserLimit`，实测） |
| 本轮的应对 | A1 的每个 horizon **单独提交、逐个等待** |

## D-13　【新增 2026-10-06 · A1 实测】作者代码**确实**应用了学习率调度

| 项 | 内容 |
|---|---|
| 来源 | `main_ILI_lora.py` 每 epoch 调用 `adjust_learning_rate(model_optim, epoch+1, args)`（`args.cos=0` 分支） |
| 实测证据 | A1 运行日志出现 `Updating learning rate to 0.00019371024450000004`（作业 606378） |
| 含义 | `--lradj type1 --decay_fac 0.75` 是**指数衰减**，lr 从 5e-4 逐 epoch 下降。**这不是 no-op** |
| 对 A1/A2 差异的影响 | A2 声明「无 scheduler」（`recovery/stage5/results_report_zh.md` §2），**A1 有指数衰减** → 两者训练配方不同，不可直接比较 |
| 此前记录的更正 | `HYPERPARAMETER_PROVENANCE.md` 中「发布 `lradj=type1` 在默认路径不生效」一句**过于宽松**。精确表述应为：**`cos=0` 时走 `adjust_learning_rate`，type1 生效并衰减 lr**；只有 `cos=1` 才走 CosineAnnealingLR |
| 作者确认 | 不适用（这是一手实测行为，不是推测） |

---

## 偏离影响分级（用于重跑决策）

| 级别 | 含义 | 条目 |
|---|---|---|
| **evaluation-only** | 只影响评估/汇总，可从已存预测重算 | D-07 的 checkpoint 选择、变量覆盖、`drop_last`、窗口归属 |
| **training-affecting** | 改变训练轨迹，必须重训 | D-07 的文本通路位置、LoRA、冻结、七变量联合 |
| **import-only** | 不可能影响任何张量 | D-01…D-04（D-01 例外：是行为性的但实现为正确排列） |
| **probe-only** | 只存在于诊断脚本 | D-05、D-09 |

**推论**：A2 的 116 个评分格相对**发布代码**属 `training-affecting` 偏离，因此 **A2 结果不能用来声称「作者代码复现」**；但 A2 **内部**的八模型比较是**同协议**的，可用于公平比较（这正是它的设计目的）。