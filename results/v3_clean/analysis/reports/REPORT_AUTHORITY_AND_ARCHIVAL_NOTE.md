# 报告权限与归档说明
## REPORT AUTHORITY AND ARCHIVAL NOTE

| | |
|---|---|
| 生成日期 | 2026-10-07 |
| 仓库 commit | `5304f9473e8f67b97c23abda1b31775439d5a353`（2026-10-07 21:52:36 +0800） |
| 作者数据 SHA-256 | `2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589e3bbca95ebfe5` |
| 严格 Test 键集 SHA-256 | `4ad79bb14b2cc11ec3ae1e07e13ae4bdcf41a87161d5149774ab1a94f95d1961` |

---

## 1. 结论速览

| | **当前正式报告** | **历史报告** |
|---|---|---|
| 文件 | `MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版.docx` | `MIFlu_非LLM与LLM流感预测最终报告_中文版.docx` |
| 位置 | `results/v3_clean/analysis/reports/`（原地） | 原地**保留**，并另存归档副本于 `reports/archive/` |
| SHA-256 | `f41652ff3d108575a9e93d789810f2fd0d345bb3b8536f14a5367922691f57ef` | `9c573f48fb65e590c7973223d6cb5e0ab74e2dfa4f6df11ec936f980a6b50ead` |
| 大小 | 44,675 bytes | 1,372,896 bytes |
| 描述轨道 | **Track R**（论文复现）+ **Track C**（严格 966 行八模型 Test 冠军赛） | **Track H**（历史 1025 行自建实验） |
| 权限状态 | **CURRENT** | **SUPERSEDED_HISTORICAL_REPORT** |
| 可否作为最终结论引用 | ✅ 是 | ❌ 否，仅限带历史标签引用 |

> 本说明同时适用于历史报告的 PDF 渲染件
> `MIFlu_非LLM与LLM流感预测最终报告_中文版.pdf`
> （SHA-256 `e1e1ecbb0bf498433dae309633b83a302f47f538dd5ee3bb56b3e356e7f9dbfe`），
> 其归档副本为 `reports/archive/MIFlu_..._旧版_历史1025行实验.pdf`。

---

## 2. 当前正式报告（CURRENT）

**路径**：`results/v3_clean/analysis/reports/MIFlu_非LLM与LLM流感预测最终报告_中文版_官方仓库966行严格测试冠军版.docx`

其内容建立在：

- 作者**官方仓库**代码（`recovery/author_repo`）；
- 作者 **966 行**原始数据（SHA-256 `2a96dfed…ebfe5`），经 Table II 七变量描述统计 **7/7** 验证；
- 划分 **676 / 97 / 193**；
- **严格包含**（strict containment）窗口契约，Test 键集 SHA-256 `4ad79bb1…d1961`；
- 匹配种子 **42 / 43 / 44**；
- Validation 仅用于选点，**Test 一次性**且**仅**用于冠军排名；
- 八模型、四 horizon、96 个格子。

**冠军结论**：基于官方仓库的修正版 MIFlu 为八模型冠军，
mean Test `average_MSE_4L` = **1.8652**（SD 0.0916），mean Test `average_MAE_4L` = **0.8842**。

---

## 3. 历史报告（SUPERSEDED_HISTORICAL_REPORT）

**路径**：`results/v3_clean/analysis/reports/MIFlu_非LLM与LLM流感预测最终报告_中文版.docx`
**归档副本**：`results/v3_clean/analysis/reports/archive/MIFlu_非LLM与LLM流感预测最终报告_中文版_旧版_历史1025行实验.docx`

原件**未被删除、未被修改**（归档副本 SHA-256 与原件逐位一致）。

---

## 4. 为何被取代

历史报告的结论**在其自身契约内是自洽的**，但它描述的是**另一套实验**。五项契约差异决定了二者不可互相替代：

| # | 维度 | 历史报告（Track H） | 当前报告（Track R / C） |
|---:|---|---|---|
| 1 | 数据集 | **1025 行** July-2026 快照 | **966 行**作者原始数据 |
| 2 | Table II 校验 | 仅 **1/7** 变量匹配 | **7/7** 匹配（最大偏差约 0.02%） |
| 3 | MIFlu 实现 | 项目**自建** MIFlu | **官方仓库**代码 + R1-B 修正实现 |
| 4 | 划分 / 窗口契约 | 历史划分，后被发现存在**边界污染** | 严格包含（`target_start >= split_start`，`target_end <= split_end - 1`），无污染 |
| 5 | Test 范围与排名依据 | 八模型仅在 **Validation** 上比较；最终 **Test / Holdout** 仅三个冻结模型 | 八模型全部在 **一次性 Test** 上排名 |

**时序事实**：作者官方仓库是在历史实验**完成之后**才被克隆的。因此历史报告不可能使用官方仓库代码，这不是它的缺陷，而是它的时代属性。

---

## 5. 为何保留

历史报告是**以下内容的唯一完整记录**，删除将造成不可逆的证据损失：

1. 官方仓库介入之前的**项目自建阶段**完整过程；
2. **1025 行历史数据集**上的实验结果；
3. **自建 MIFlu** 的实现与表现；
4. 旧的 **Wave-1 Validation 排名**；
5. 旧的**三模型 Test / Holdout 实验**；
6. 此前的 **NLinear Test 结论**。

---

## 6. 分类声明：SUPERSEDED_HISTORICAL_REPORT

本说明**不**将历史报告中的陈述定性为「错误」（false）。

其正确分类是：

```
SUPERSEDED_HISTORICAL_REPORT
```

**理由**：历史报告的各项结论，是**针对其自身的数据集、MIFlu 实现、划分/窗口契约与 Test 范围**得出的。在这些前提下它们成立。**被取代的原因是契约变更，不是结论失效。**

因此：

- 引用历史报告的数值时，**必须**同时标注「Track H / 1025 行 / 自建 MIFlu / 历史划分契约」；
- **不得**将历史报告的数值与当前报告的数值直接相减、相除或并列排名；
- **不得**将历史报告的 NLinear 结论外推到当前 966 行契约；
- 历史报告中凡涉及 Test 的结论，其 Test 范围仅为**三个冻结模型**，不代表八模型冠军赛。

---

## 7. 权限执行清单

- [x] 历史报告 DOCX 保留在原位（未删除、未修改）
- [x] 归档副本写入 `reports/archive/`，SHA-256 与原件一致
- [x] 历史报告 PDF 一并归档
- [x] 当前冠军版报告保留在原位，作为 CURRENT
- [ ] v2 完整报告生成并通过渲染审计后，接管 CURRENT 权限（见 `FINAL_REPORT_V2_CHANGELOG.md`）
