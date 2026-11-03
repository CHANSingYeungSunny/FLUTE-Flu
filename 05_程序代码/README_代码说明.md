# 05_程序代码/ 里面是什么

**你平时不需要打开这个文件夹**，只有要"重新跑一遍"或"改代码"时才用。

## 按用途分类

### 训练模型（跑一次要几小时，用 GPU）
| 文件 | 作用 |
|------|------|
| `train_miflu.py` | 训练 MIFlu 模型 |
| `train_backbone_966.py` | 训练普通模型（神经网络/Transformer） |
| `train_nlinear_966.py` | 训练 NLinear |
| `train_regional.py` | 区域预测训练 |
| `miflu_model.py` | MIFlu 模型的定义 |
| `configs.py` | 参数配置 |

### 分析结果（不需要 GPU，几分钟）
| 文件 | 作用 |
|------|------|
| `analysis_expanded.py` | **主分析**：算所有模型的 MSE，生成表格 |
| `analysis_postprocess.py` | 后处理（效率、配对检验等） |
| `seasonal_naive_baseline.py` | 算季节朴素基线 |
| `plot_bench.py` | 画基准对比图 |
| `plot_pareto.py` | 画 Pareto 前沿图 |
| `compute_pte_pie_track_c.py` | 算峰值预测 PTE/PIE |

### 验证（检查数字对不对）
| 文件 | 作用 |
|------|------|
| `verify_miflu_oracle.py` | 验证 MIFlu 数字与论文一致 |
| `verify_bench_unchanged.py` | 验证基准表没被误改 |
| `verify_docs.py` | 验证报告生成正确 |

### 生成文档
| 文件 | 作用 |
|------|------|
| `md_to_docx.py` / `render_docx.py` | Markdown 转 Word |
| `build_*.py` | 生成各类表格 |

### 下载数据
| 文件 | 作用 |
|------|------|
| `download_national_illness.py` | 下载全国流感数据 |
| `download_us_region.py` | 下载区域数据 |

---

**最常用的三条命令**（在项目根目录运行）：

```bash
python 05_程序代码/analysis_expanded.py        # 算所有数字
python 01_最终报告/_build2/build_docs.py       # 生成报告
python 01_最终报告/_build2/verify_docs.py      # 检查报告
```

**子文件夹**：
- `innovation/` —— 创新实验代码
- `v3/` `v3_clean/` —— 第三版实验代码

**其他一次性脚本已挪到 `99_旧文件存档/`。**
