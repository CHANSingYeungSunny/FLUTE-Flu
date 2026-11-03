# 01_最终报告/ 里面有什么

> 这个文件夹放的是**最终成果**——你要交的东西都在这里。

---

## 一、三份报告（中文优先看这个）

| 文件 | 是什么 | 页数 | 什么时候看 |
|------|--------|------|-----------|
| **`report_internal_zh.pdf`** | **内部技术报告（最全）** | 20 页 | 想了解全部细节 |
| `report_internal_zh.docx` | 同上，Word 版 | — | 要修改内容 |
| **`progress_report_zh.pdf`** | **FYP 进度报告（简版）** | 5 页 | 交给老师 |
| `progress_report_zh.docx` | 同上，Word 版 | — | 要按学校模板改 |
| **`ieee_manuscript_zh.pdf`** | **IEEE 论文稿** | 6 页 | 想投稿 |
| `ieee_manuscript_zh.docx` | 同上，Word 版 | — | 要改论文 |

`_en` 结尾的是英文版，内容一样。

**PDF 已签名、字体已嵌入，可直接发出去。**

---

## 二、图（`figures/`）

| 文件 | 画的是什么 |
|------|-----------|
| `fig_forecast_L24.png` | 3 个模型在 **L=24 周**的预测 vs 真值 |
| `fig_forecast_L36.png` | 同上，L=36 周 |
| `fig_forecast_L48.png` | 同上，L=48 周 |
| `fig_forecast_L60.png` | 同上，L=60 周 |
| `fig_forecast_all_horizons.png` | **4 个跨度合在一起看**（2×2 大图） |
| `fig_llm_encoders_vs_baseline.png` | **11 个 LLM 编码器**和最佳常规模型的对比 |
| `fig_pareto_frontier.png` | 准确率 vs 模型大小（哪个更划算） |
| `fig_pte_pie_heatmap.png` | 峰值预测准不准的热力图 |
| `figure_captions.json` | 每张图的文字说明（自动用在报告里） |

**怎么看**：`fig_forecast_L24.png` 里黑色实线是真值，彩色虚线是模型预测。
三个面板分别是 MIFlu（红）、NLinear（蓝）、PatchTST（绿）。

---

## 三、打包文件

| 文件 | 是什么 | 用在哪 |
|------|--------|--------|
| `PROJECT_HANDOFF.zip` | **全部材料打包**（2.3 GB） | 发给 ChatGPT 写论文 |
| `chatgpt_prompt.md` | **给 ChatGPT 的指令书** | 和 zip 一起发给它 |
| `MANIFEST.md` | 打包里有什么的清单 | 核对用 |

---

## 四、生成报告的工具（`_build2/`）

这个文件夹是**自动从数字生成报告的脚本**，你不用打开它。

如果需要重新生成报告（比如改了数字）：

```bash
python 01_最终报告/_build2/build_docs.py    # 生成 Word
python 01_最终报告/_build2/to_pdf.py        # 转 PDF
python 01_最终报告/_build2/verify_docs.py   # 检查（必须 FAILURES: 0）
```

---

## 五、报告里写的核心结论

1. **复现基本成功**：4 个跨度平均 1.4995，论文是 1.4355，**差 4.5%**（2 个更好、2 个更差）
2. **MIFlu 自己最准**：1.5574（第二名 PatchTST 1.6621）
3. **NLinear 和 MIFlu 峰值预测并列最好**：各通过 4 次 Kramer & Shaman 标准
4. **LLM 编码器没用**：11 个里最好的 Hunyuan-1.8B 是 4.7374，比 MIFlu 差 3 倍
5. **核心发现**：MSE 冠军 ≠ 峰值冠军 —— 该部署哪个取决于你要什么
