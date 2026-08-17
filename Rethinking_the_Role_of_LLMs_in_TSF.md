# Rethinking the Role of LLMs in Time Series Forecasting

**Authors:** Xin Qiu¹ ², Junlong Tong¹, Yirong Sun¹, Yunpu Ma³, Wei Zhang¹, Xiaoyu Shen¹

¹ Ningbo Key Laboratory of Spatial Intelligence and Digital Derivative, Institute of Digital Twin, Eastern Institute of Technology, Ningbo
² Zhejiang University
³ LMU Munich

Correspondence to: Xiaoyu Shen <xyshen@eitech.edu.cn>

*Preprint. March 4, 2026.*

arXiv:2602.14744v2 [cs.CL] 2 Mar 2026

Code: https://github.com/EIT-NLP/LLM4TSF

---

## Abstract

Large language models (LLMs) have been introduced to time series forecasting (TSF) to incorporate contextual knowledge beyond numerical signals. However, existing studies question whether LLMs provide genuine benefits, often reporting comparable performance without LLMs. We show that such conclusions stem from limited evaluation settings and do not hold at scale.

We conduct a large-scale study of LLM-based TSF (LLM4TSF) across 8 billion observations, 17 forecasting scenarios, 4 horizons, multiple alignment strategies, and both in-domain and out-of-domain settings. Our results demonstrate that LLM4TS indeed improves forecasting performance, with especially large gains in cross-domain generalization. Pre-alignment outperforms post-alignment in over 90% of tasks. Both pretrained knowledge and model architecture of LLMs contribute and play complementary roles: pretraining is critical under distribution shifts, while architecture excels at modeling complex temporal dynamics. Moreover, under large-scale mixed distributions, a fully intact LLM becomes indispensable, as confirmed by token-level routing analysis and prompt-based improvements. Overall, our findings overturn prior negative assessments, establish clear conditions under which LLMs are useful, and provide practical guidance for effective model design.

---

## 1. Introduction

Time series forecasting (TSF) is a fundamental learning task with broad applications across many domains (Liu & Wang, 2024; Kim et al., 2025; Kong et al., 2025). Despite decades of research on statistical and machine learning approaches (De Gooijer & Hyndman, 2006; Masini et al., 2023; Yunita et al., 2025), accurate TSF remains challenging due to the coexistence of long-term trends, periodic patterns, abrupt changes, and stochastic noise. Inspired by the success of Transformers in fields such as speech, vision, and video understanding (Dong et al., 2018; Liu et al., 2021; 2022b; Cao et al., 2022), prior work has introduced Transformer-based architectures to TSF (Wu et al., 2021; Zhang et al., 2024a; Liang et al., 2024; Li et al., 2025). By leveraging attention mechanisms, these models enable more flexible modeling of temporal dependencies.

However, most Transformer-based TSF models are trained from scratch on uni-modal numerical time series. Such representations are inherently abstract and lack explicit encoding of real-world context or environmental factors that often underlie temporal observations (Liu et al., 2024a; Huang et al., 2025; Lei et al.). This limitation has motivated recent explorations of LLM-based time series forecasting (LLM4TSF), aiming to leverage the rich world knowledge embedded in LLMs pretrained on large-scale text corpora (Hu et al., 2025a; Liu et al., 2025a; Hu et al., 2025b; Wolff et al., 2025). To reduce the modality gap between numerical time series and language representations, existing approaches typically follow two alignment paradigms:

- **Pre-alignment** methods map time series into language-compatible representations via cross-attention with word embeddings before feeding them into an LLM (Hu et al., 2025a; Liu et al., 2025a).
- **Post-alignment** methods jointly fine-tune time series encoders and LLMs through supervised learning, adapting both components simultaneously (Meunier et al., 2025; Liu et al., 2025c).

Despite this progress, a fundamental question remains unresolved: are LLMs truly indispensable for TSF? Many recent studies raise doubts, arguing that existing alignment strategies may induce only pseudo-alignment (Zheng et al., 2025a;b), or observing that removing the LLM module causes little to no performance degradation (Tan et al., 2024; Zheng et al., 2025a; Zhang et al., 2025). These findings have sparked an ongoing debate about whether LLMs contribute genuine modeling capability, or merely act as architectural or parameter-level augmentations.

We argue that existing analyses are insufficient to answer this question conclusively. Prior studies are typically conducted on small-scale datasets, rely on only the shallow layers of LLMs (Tan et al., 2024; Zheng et al., 2025a), focus primarily on in-domain evaluation (Zhang et al., 2025), and rarely probe the underlying mechanisms responsible for performance differences. Importantly, the core strength of LLMs lies not in their architecture alone, but in their pretrained world knowledge, instruction-following ability, and capacity for multi-task generalization (Brown et al., 2020). Evaluating LLM4TSF under single-task, in-domain settings with partially utilized LLM parameters fails to reflect these capabilities and may lead to misleading conclusions.

To address these limitations, we conduct a large-scale, systematic study of LLM4TSF across diverse settings. Our evaluation spans 8 billion observations, 17 forecasting scenarios, both in-domain and out-of-domain distributions, and four forecasting horizons. We examine representative pre-alignment and post-alignment strategies, and explicitly disentangle the roles of pretrained knowledge, model architecture, and alignment design in LLM4TSF.

Our empirical analysis provides clear evidence that LLM4TSF indeed improves forecasting performance:

1. Alignment strategy plays a decisive role: pre-alignment methods outperform post-alignment approaches in over 90% of tasks overall.
2. Performance gains arise from a complementary interaction between pretrained knowledge and architectural capacity. Pretraining proves particularly valuable under distribution shifts and out-of-domain settings, while architectural components excel at capturing complex temporal dynamics.
3. Data diversity is critical: models trained on multi-source time series consistently outperform single-dataset baselines in more than 70% of in-domain tasks and exhibit stronger cross-domain generalization than TS-specific models.
4. LLM4TSF models show clear preferences for certain statistical regimes, performing especially well on data with frequent transitions and high variability.

Further analysis under mixed-distribution and large-scale settings yields additional insights. Unlike low-data regimes where randomizing or removing the LLM has minimal impact (Tan et al., 2024), we find that a fully intact LLM becomes essential for robust forecasting at scale, and partial fine-tuning is no longer sufficient. Token-level routing analysis provides mechanistic evidence for this effect: the model's decision to route tokens through or around the LLM strongly correlates with forecasting errors, indicating adaptive utilization of LLM capabilities. Moreover, informative textual prompts consistently improve performance, underscoring the importance of semantic guidance beyond simply increasing model size.

At the same time, our study highlights clear limitations. LLM4TSF does not automatically benefit from larger LLMs without careful alignment, and performance remains sensitive to data distribution, preventing uniformly strong results across all scenarios.

### Main Contributions

1. A large-scale empirical study that provides the first comprehensive assessment of the benefits and limitations of LLM4TSF.
2. A principled decomposition of performance gains, clarifying the distinct and complementary benefits of pretrained knowledge and model architecture.
3. A routing-based analysis that links token-level path selection to macroscopic forecasting performance, offering concrete evidence of LLM effectiveness.
4. Practical guidelines and capability boundaries for applying LLMs to TSF, informing the design of future LLM-based forecasting systems.

---

## 2. Preliminary

### 2.1. Single & Cross-Dataset Learning Paradigm

TSF applications often involve TS data from diverse domains with substantial differences in statistical properties (Liu et al., 2024b; Chang et al., 2025). Ideally, a model should not only achieve strong performance on a single dataset, but also be capable of transferring knowledge across heterogeneous datasets (Cheng et al., 2024; Xiao et al., 2025). However, many existing LLM4TSF still adopt a single-dataset learning paradigm. For example, S2IP (Pan et al., 2024), FSCA (Hu et al., 2025a), TransDF (Wang et al., 2025b), and CALF (Liu et al., 2025c) are typically trained and evaluated on individual datasets. Such settings are prone to overfitting on limited data and limit the potential generalization advantages of LLMs. Inspired by domain-specific TS foundation models trained from scratch on large-scale data (Ansari et al., 2024; Ning et al., 2025; Liu et al., 2025d), prior work such as UniTime (Liu et al., 2024b) adopts cross-dataset learning for LLM4TSF, enabling stable in-domain and out-of-domain generalization, while we further introduce fine-grained instructions to support instruction-driven task generalization (Zhou et al., 2023a).

### 2.2. Core components of LLM4TSF

Typical architecture of LLM4TSF models consist of three core components: TS encoder, LLM backbone and TS decoder. Both the TS encoder and decoder are implemented as lightweight MLPs, decoupling low-level numerical processing from high-level learning (Chen et al., 2025). The LLM backbone is instantiated with a pre-trained LLM.

**(I) TS encoder.** Given a TS X₁:L ∈ ℝ^(L×d), channel-independent and instance normalization strategies are applied to mitigate scale variations across variables (Kim et al., 2021). Subsequently, a patching operation is employed to divide each TS into a sequence of local patches (Nie et al., 2023). Specifically, we denote the patch length as P and the stride as S. The patching produces patch-level x_p ∈ ℝ^(P×N), where N denotes the patch numbers, defined as N = (L−P)/S + 2. The TS embeddings are then obtained as X = f_enc(x_p), where f_enc(·) denotes the TS encoder.

**(II) LLM backbone.** To activate the prior knowledge in the LLM, textual prompts are introduced to describe background information and task specifications. The text prompts are processed by the LLM tokenizer to obtain prompt embeddings. At the input layer of the LLM, the prompt embeddings are fed with the TS embeddings. The resulting hidden states are used as the integrated representations, expressed as h = f_LLM(Z, X), where Z and X denote the prompt and TS embeddings.

**(III) TS decoder.** A TS decoder maps the outputs h back to forecasts: X̂_(L+1:L+H) = f_dec(h), where f_dec(·) denotes the TS decoder.

### 2.3. Alignment Strategy for LLMs on TSF

Applying LLMs to TSF involves bridging the modality gap between TS and text modalities. Existing methods mainly adopt one of two strategies to enable effective cross-modal interaction (Jin et al., 2023; Woo et al., 2024b; Liu et al., 2025c; Meunier et al., 2025; Hu et al., 2025a), namely **pre-alignment** and **post-alignment**.

**Figure 1** *(diagram, described textually below)*: Two mainstream alignment strategies for LLM4TSF.

- **Pre-alignment pipeline:** Time Series → Patch → TS Encoder → Multi-Head Attention (Q from TS embeddings; K, V from PCA-reduced LLM Word Embedding) → [combined with Text Prompt → LLM Tokenizer] → Pre-trained LLM Backbone (frozen) → TS Decoder
- **Post-alignment pipeline:** Time Series → Patch → TS Encoder → [combined with Text Prompt → LLM Tokenizer] → Pre-trained LLM Backbone (trainable) → TS Decoder

**Pre-alignment.** Pre-alignment aligns TS to the textual modality *before* input to the LLM, exploiting the semantic structure of pre-trained word embeddings while keeping the LLM frozen. Let X ∈ ℝ^(N×M) denote the TS embeddings to be aligned, where N is the number of TS tokens and M is the embedding dimension. Let D ∈ ℝ^(|A|×M) denote the word embedding dictionary of the LLM, where |A| is the vocabulary size. Due to the large size of D, directly aligning TS embeddings with the full dictionary is expensive. Therefore, principal component analysis (PCA) is applied to obtain a set of principal word embeddings: D̂ = PCA(D), where D̂ ∈ ℝ^(d×M) and d ≪ |A|. Alignment is performed via attention, using TS embeddings as queries and the principal word embeddings as keys and values.

**Post-alignment.** Post-alignment performs modality alignment between TS and text within the representation space of the LLM, by jointly modeling TS embeddings and textual embeddings. In this paradigm, TS embeddings and prompt embeddings are fed into the LLM for cross-modal modeling. Let X ∈ ℝ^(N×M) denote the TS embeddings and Z ∈ ℝ^(C×M) denote the prompt embeddings, where C is the number of text tokens. The LLM produces integrated representations as: h = f_LLM(Z, X), where f_LLM(·) denotes the forward mapping of the LLM. During training, the parameters of the LLM are updated using supervision from the TSF task, thereby enabling alignment between TS and text modalities in the latent space.

---

## 3. Benefits of Diverse TS Data in LLM4TSF

Although prior studies have examined LLM-based TSF, their evaluations are mostly conducted under single distribution. In addition, many approaches adapt LLMs using only shallow layers (Pan et al., 2024; Liu et al., 2025a), restricting the capacity of pretrained models and making results sensitive to overfitting or dataset-specific artifacts. Consequently, the true capability of LLMs in TSF remains difficult to assess (Tan et al., 2024; Zheng et al., 2025a). More importantly, pretrained LLMs are designed to learn transferable representations from diverse data. When evaluated on a single TS dataset, this potential may be underutilized. Motivated by this observation, we adopt cross-dataset learning with full-scale LLMs and compare its performance against single-dataset learning under both in-domain and out-of-domain settings (see Appendix C).

### 3.1. Experimental Setup

**Datasets.** We conduct experiments on a collection of 62 real-world, publicly available TS datasets spanning over 10 application domains. The entire dataset collection is denoted as 𝒟 and is partitioned into two disjoint subsets, 𝒟 = 𝒟_A ∪ 𝒟_B. The subset 𝒟_A contains 55 datasets and is used for model development, while 𝒟_B consists of the remaining 7 datasets, which are completely excluded from training and used solely for out-of-domain evaluation. For each dataset D_i ∈ 𝒟_A, we apply train–test splits, where the training split is used for model optimization and the held-out test split is used to evaluate in-domain performance. Overall, the combined datasets comprise over 8B observations, providing a diverse testbed for studying in-domain and out-of-domain settings (see Appendix F.1).

**Models.** We consider both the *pre-alignment* and *post-alignment* strategies introduced in Sec. 2.3. Under each alignment strategy, models are trained following two learning paradigms described in Sec. 2.1, namely *single-dataset learning* and *cross-dataset learning*. This results in two model variants, denoted as **LLM4TSF (Pre-align)** and **LLM4TSF (Post-align)**.

The core components of all models follow the architecture described in Sec. 2.2. Specifically, we adopt GPT-2 (Radford et al., 2019) as the LLM backbone. To preserve the full modeling capacity of the pretrained LLM, no layer truncation is applied. At the input stage, for the TS component, the look-back window length is set to T = 512. Non-overlapping patch-level sampling is applied with patch size P = 32 and stride S = 32, and each TS is processed using a channel-independent strategy and RevIN normalization. For the text prompts component, dataset identifiers, background information, and statistical descriptors associated with each TS instance are provided as inputs. All statistical descriptors are computed solely from the 512-step look-back window, ensuring that no future information is leaked (see Appendix D).

**Test Details.** The forecasting horizon H is evaluated at {96, 192, 336, 720}, covering short-term and long-term forecasting scenarios. Generalization is assessed under two settings: *in-domain* and *out-of-domain* test. The former is conducted on 10 datasets with held-out test splits, and the latter is performed on 7 datasets that are completely excluded from training (see Appendix C.2). Model performance is measured using MAE and MSE.

### 3.2. Evaluation Results

**In-domain Test.** First, we evaluate the in-domain performance of LLM4TSF under both alignment strategies when trained independently on individual datasets, reporting results across 10 benchmark datasets. Next, we conduct large-scale cross-dataset joint training and compare the resulting performance gains relative to single-dataset learning. The forecasting horizon H is evaluated at {96, 192, 336, 720}; due to space constraints, results are reported as the average over the four horizons.

Under the single-dataset learning paradigm, LLM4TSF with the pre-alignment strategy outperforms its post-alignment counterpart across most datasets. The performance gap is particularly pronounced on small-scale datasets that are prone to overfitting, such as ETT and Exchange, where pre-alignment demonstrates clear advantages. In addition, cross-dataset learning leads to better performance, regardless of whether pre-alignment or post-alignment strategies are adopted. This observation suggests that large-scale training on diverse TS data is more effective (full results in Appendix G.1).

**Figure 2. Comparison of LLM4TSF with pre-alignment and post-alignment strategies under single-dataset learning (radar chart, MAE and MSE).**

| Dataset | MAE (Pre-alignment) | MAE (Post-alignment) | MSE (Pre-alignment) | MSE (Post-alignment) |
|---|---|---|---|---|
| ETTh1 | 0.454 | 0.439 | 0.890 | 0.843 |
| ETTh2 | 0.424 | 0.415 | 0.482 | 0.449 |
| ETTm1 | 0.417 | 0.397 | 0.379 | 0.371 |
| ETTm2 | 0.337 | 0.322 | 0.238 | 0.166 |
| Weather | 0.280 | 0.284 | 0.385 | ~ |
| Traffic | 0.282 | 0.280 | 0.287 | 1.524 |
| Exchange | 0.427 | 0.410 | 0.410 | 0.367 |
| Covid | 0.056 | 0.053 | 0.422 | 0.403 |
| ECL | 0.673 | 0.642 | 1.540 | 0.379 |
| NN | 0.263 | 0.276 | 0.168 | 0.274, 0.240 |

*Note: Some values in Figure 2 (a radar/spider chart) are difficult to align precisely by axis due to overlapping labels in the original figure; refer to Table 10/Table 11 (Appendix G.1) for exact per-horizon MAE/MSE values.*

**Out-of-domain Test.** To evaluate the out-of-domain performance of the two alignment strategies after cross-dataset learning, we compare LLM4TSF (Pre-align) and LLM4TSF (Post-align) on seven datasets against three large-scale TS foundation models trained from scratch, namely Chronos (Ansari et al., 2024), UniTS (Gao et al., 2024), and Moirai (Woo et al., 2024a). All comparisons are conducted under a zero-shot setting, and the model configurations and parameters are taken directly from the original papers. In addition, we include two LLM-based TSF models, UniTime (Liu et al., 2024b) and TimeLLM (Jin et al., 2023), which are trained using single-dataset few-shot learning with only 5% of the training data.

As shown in Table 1, both LLM4TSF (Pre-align) and LLM4TSF (Post-align) achieve overall superior performance in zero-shot test compared to TS foundation models. Moreover, they even outperform LLM-based TSF models trained with 5% data (full results in Appendix G.5).

**Table 1. Out-of-domain test performance (MSE, averaged over horizons {96, 192, 336, 720}). Bold and underlined indicate the best and second-best results for each dataset.**

| Types | Zero-Shot: Pre-align | Zero-Shot: Post-align | Zero-Shot: Chronos | Zero-Shot: UniTS | Zero-Shot: Moirai | 5% Few-Shot: UniTime | 5% Few-Shot: TimeLLM |
|---|---|---|---|---|---|---|---|
| Wind | **1.015** (underlined) | 0.963 (bold) | 1.422 | 1.358 | 1.236 | 1.358 | 1.321 |
| Solar | 0.228 (underlined) | 0.274 | 0.434 | 0.871 | 0.936 | **0.218** (bold) | 0.577 |
| AQShunyi | **0.612** (bold) | 0.688 | 0.808 | 0.890 | 0.668 (underlined) | 0.905 | 0.859 |
| CzenLan | **0.274** (bold) | 0.288 (underlined) | 0.298 | 0.738 | 0.660 | 0.401 | 0.319 |
| ZafNoo | **0.547** (bold) | 0.583 | 0.550 (underlined) | 0.668 | 0.543 | 0.803 | 0.594 |
| NASDAQ | **0.735** (bold) | 0.749 (underlined) | 0.873 | 1.120 | 1.067 | 1.122 | 0.983 |
| PEMS | 0.256 (underlined) | 0.291 | 0.686 | 1.303 | **0.243** (bold) | 0.419 | 0.416 |

> These results indicate that, when trained with pretrained LLM parameters and large-scale TS data, the model not only performs well in in-domain settings but also exhibits strong cross-domain generalization. Moreover, this advantage is amplified with increasing data scale, as shown in Fig. 14.

---

## 4. Where do the Gains Really Come from?

Sec. 3 shows that LLM4TSF trained under cross-dataset learning achieves strong performance across a wide range of scenarios. However, it remains unclear where these performance gains actually come from. In this section, we conduct an attribution study by either removing the LLM module or randomly initializing parameters, thereby disrupting the pretrained knowledge and keeping the overall architecture and settings unchanged. This design enables us to isolate and rigorously evaluate the actual contribution.

**Figure 3. Comparison of LLM4TSF performance with pre- and post-alignment under single- and cross-dataset paradigm (Relative MAE Change).** Negative and Positive values indicate MAE decreases and increases under cross-dataset learning compared to single-dataset learning.

| Dataset | LLM4TSF (Pre-align) | LLM4TSF (Post-align) |
|---|---|---|
| ETTh1 | +1.4% | -4.0% |
| ETTh2 | -6.5% | -6.6% |
| ETTm1 | -5.5% | -7.9% |
| ETTm2 | -4.0% | -3.6% |
| Weather | -0.7% | -5.0% |
| Traffic | -5.1% | +3.9% |
| Exchange | -7.5% | -5.9% |
| Covid | +0.4% | -8.9% |
| ECL | -3.9% | +0.8% |
| NN | (unlabeled in fig) | -2.1% |

### 4.1. Ablation Setup

To investigate the impact of LLM parameters in TSF, we consider three model configurations (original architecture and two ablation variants) with different levels of reliance on pretrained LLMs:

1. **w/ pre-training** — the LLM serves as the backbone model and retains its pretrained weights; the LLM components are frozen in LLM4TSF(Pre-align) and fine-tuned in LLM4TSF(Post-align).
2. **w/o pre-training** — follows the same architecture as the pretrained setting but randomly initializes all LLM parameters.
3. **w/o LLM** — the LLM components are entirely removed from the architecture, retaining only other non-LLM modules.

The three architectures are trained following the same procedure as in Sec. 3.1 and evaluated on a variety of scenarios.

**Figure 4 (diagram description):** Three architectures compared:
- *w/ pre-training:* Text Prompt & Time Series → Encoder + Align → Pre-trained LLM Backbone → Decoder
- *w/o pre-training:* Text Prompt & Time Series → Encoder + Align → Random Init. LLM Backbone → Decoder
- *w/o LLM:* Text Prompt & Time Series → Encoder + Align → Decoder (no LLM backbone)

### 4.2. Ablation Results

**Main results.** As shown in Table 2, when comparing w/ pre-training against the two ablated counterparts (w/o pre-training and w/o LLM), LLM4TSF(Pre-align) with pretrained LLM parameters achieves the lowest forecasting error on 6/10 datasets in the in-domain test and 6/7 datasets in the out-of-domain test. Similarly, LLM4TSF(Post-align) with pre-training attains the lowest error on 7/10 in-domain and 5/7 out-of-domain datasets. To better understand the role of LLMs in TSF, we disentangle the effects of LLM, distinguishing whether gains arise from pretrained semantic priors or merely from architectural modeling capacity.

**(I) w/ pre-training vs. w/o pre-training.** LLM4TSF(Pre-align) consistently benefits from LLM prior knowledge: training with pretrained LLM parameters outperforms random initialization on all datasets (i.e., 10/10 in-domain and 7/7 out-of-domain test). For LLM4TSF(Post-align), models w/ pre-training perform better on 7/10 in-domain datasets and 5/7 out-of-domain test.

**(II) w/o pre-training vs. w/o LLM.** For LLM4TSF(Pre-align), retaining a randomly initialized LLM consistently underperforms directly removing the LLM backbone across all tests (10/10 in-domain and 7/7 out-of-domain). In contrast, for LLM4TSF(Post-align), retaining a randomly initialized LLM outperforms removing the LLM backbone on 7/10 in-domain tests and on all out-of-domain tests.

**Takeaways.** The gains of LLM4TSF models arise from both LLM parameters and architectural capacity. Moreover, two interesting findings emerge: (1) across different alignment strategies, pre-trained priors contribute to performance to varying extents; and (2) freezing LLM causes randomly initialized models to collapse, therefore under post-alignment, fully trainable LLMs can be optimized from scratch and outperform w/o LLM.

**Table 2. Ablation results of LLM4TSF (Pre-align) and LLM4TSF (Post-align), averaged over horizons {96, 192, 336, 720}. For each dataset, the best MAE is highlighted in red and the best MSE is highlighted in blue in the original.**

### In-Domain Test

| Dataset | Pre-align w/ Pre-training MAE | MSE | Pre-align w/o Pre-training MAE | MSE | Pre-align w/o LLM MAE | MSE | Post-align w/ Pre-training MAE | MSE | Post-align w/o Pre-training MAE | MSE | Post-align w/o LLM MAE | MSE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ETTh1 | 0.445 | 0.447 | 0.460 | 0.471 | 0.432 | 0.438 | 0.436 | 0.431 | 0.428 | 0.420 | 0.435 | 0.442 |
| ETTh2 | 0.388 | 0.348 | 0.414 | 0.377 | 0.407 | 0.363 | 0.396 | 0.357 | 0.429 | 0.403 | 0.439 | 0.424 |
| ETTm1 | 0.375 | 0.353 | 0.393 | 0.382 | 0.363 | 0.328 | 0.384 | 0.354 | 0.373 | 0.340 | 0.378 | 0.351 |
| ETTm2 | 0.309 | 0.252 | 0.330 | 0.290 | 0.315 | 0.271 | 0.325 | 0.265 | 0.341 | 0.290 | 0.355 | 0.307 |
| Weather | 0.256 | 0.225 | 0.275 | 0.244 | 0.268 | 0.240 | 0.266 | 0.226 | 0.275 | 0.242 | 0.287 | 0.261 |
| Traffic | 0.278 | 0.401 | 0.285 | 0.416 | 0.263 | 0.377 | 0.293 | 0.418 | 0.288 | 0.406 | 0.281 | 0.390 |
| Exchange | 0.389 | 0.332 | 0.423 | 0.426 | 0.407 | 0.385 | 0.402 | 0.384 | 0.465 | 0.517 | 0.477 | 0.539 |
| Covid | 0.049 | 1.383 | 0.066 | 2.135 | 0.053 | 1.539 | 0.051 | 1.436 | 0.059 | 1.722 | 0.063 | 1.995 |
| ECL | 0.268 | 0.168 | 0.277 | 0.184 | 0.255 | 0.158 | 0.265 | 0.169 | 0.274 | 0.177 | 0.269 | 0.181 |
| NN | 0.617 | 0.804 | 0.630 | 0.821 | 0.625 | 0.828 | 0.659 | 0.865 | 0.672 | 0.913 | 0.661 | 0.884 |

### Out-of-Domain Test

| Dataset | Pre-align w/ Pre-training MAE | MSE | Pre-align w/o Pre-training MAE | MSE | Pre-align w/o LLM MAE | MSE | Post-align w/ Pre-training MAE | MSE | Post-align w/o Pre-training MAE | MSE | Post-align w/o LLM MAE | MSE |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Wind | 0.737 | 1.015 | 0.779 | 1.655 | 0.769 | 1.447 | 0.722 | 0.963 | 0.755 | 1.324 | 0.772 | 1.564 |
| Solar | 0.295 | 0.228 | 0.361 | 0.293 | 0.349 | 0.287 | 0.322 | 0.274 | 0.341 | 0.297 | 0.353 | 0.311 |
| AQShunyi | 0.445 | 0.612 | 0.464 | 0.679 | 0.451 | 0.638 | 0.472 | 0.688 | 0.487 | 0.706 | 0.493 | 0.717 |
| CzenLan | 0.308 | 0.274 | 0.367 | 0.342 | 0.359 | 0.311 | 0.319 | 0.288 | 0.336 | 0.301 | 0.355 | 0.337 |
| ZafNoo | 0.458 | 0.547 | 0.447 | 0.548 | 0.430 | 0.512 | 0.471 | 0.583 | 0.465 | 0.574 | 0.490 | 0.622 |
| NASDAQ | 0.635 | 0.735 | 0.936 | 1.955 | 0.922 | 1.854 | 0.640 | 0.749 | 0.672 | 0.793 | 0.715 | 1.023 |
| PEMS | 0.301 | 0.256 | 0.321 | 0.270 | 0.317 | 0.275 | 0.332 | 0.291 | 0.314 | 0.266 | 0.328 | 0.281 |

---

## 5. Understanding When LLM4TSF Works

In Sec. 4, we observe that in 71% of the in-domain and out-of-domain tests, the w/ pre-training setting consistently outperforms both w/o pre-training and w/o LLM. Nevertheless, a small number of datasets exhibit failure cases where such benefits do not materialize. Accordingly, in this section, we first analyze (i) why LLMs may fail under certain TSF scenarios, and investigate (ii) how to better leverage LLM strengths to maximize their effectiveness in TSF.

### 5.1. Exploring LLM Preferences over TS Distributions

**Differences in the statistical properties of TS.** TS data exhibit substantial differences in statistical properties, leading to diverse modeling (Wang et al.; Siru et al., 2025; Cini et al., 2025). On the one hand, TS often contain prominent global structural characteristics, such as long-term trends and seasonal patterns, which describe stable regularities over extended time horizons (Wang et al., 2025a; Majeedi et al., 2025). On the other hand, TS exhibit local dynamic variations, including distribution shifting, changes in stationarity, and regime transitions (Masserano et al., 2024; Hu et al., 2025c), which reflect the evolving nature of temporal data.

**Dataset-level statistical analysis.** We analyze the statistical properties of all datasets used for evaluation from five perspectives, as shown in Fig. 12 (Appendix F.2).

- **(I) In-domain datasets.** In terms of shifting, ETTh2, ETTm2, Weather, Exchange, Covid, and NN exhibit high shifting values, indicating pronounced changes in data distributions over time. The transition metric shows that ETTh2, ETTm2, Weather, Exchange, and Covid experience more frequent and complex state changes, reflecting multi-stage and multi-pattern dynamics. Regarding stationarity, Exchange and Covid display lower stationarity levels (larger values indicate poorer stationarity). However, seasonality and trend are balanced across datasets.
- **(II) Out-of-domain datasets.** NASDAQ exhibits an exceptionally high shifting value. In terms of stationarity, both CzenLan and NASDAQ show low stationarity levels. By contrast, the remaining properties — transition, seasonality, and trend — are relatively balanced across datasets (details in Appendix F.2).

**Interactions between properties and performance.** Based on the statistical analysis, we observe a clear association between TS properties and model performance. When a TS exhibits strong shifting, pretrained LLM parameters tend to yield more pronounced gains. In contrast, when shifting is weak, satisfactory performance can often be achieved using only the encoder and decoder modules (Fig. 5). Moreover, under the post-alignment setting, where LLM parameters are updated during training, for datasets with high transition, the LLM from scratch can still outperform completely removing the LLM backbone.

Since the statistical properties of real-world datasets are often entangled, we adopt a synthetic data generation approach with controlled decoupling to investigate the individual effects of shifting and transition on forecasting error (Fig. 6; details in Appendix G.6 & Appendix H). As shifting increases, LLMs exhibit advantages; likewise, higher transition amplifies the performance gap between the w/o pre-training and w/o LLM settings.

**Takeaways.** Shifting and transition play distinct roles in determining the effectiveness of the LLM backbone in TSF:
1. When shifting is strong, pretrained LLM parameters are more likely to provide meaningful performance benefits.
2. When transition is high, a trainable Transformer backbone, even without pretrained LLM parameters, outperforms the w/o LLM variant.

### 5.2. Routing Analysis: Pass Through the LLM or Skip?

Previous analyses show the benefits of LLMs in TSF are scenario-dependent. We therefore examine when LLMs are more likely to play an active role. Specifically, we employ a routing mechanism to assign path preferences to individual TS segments (see Appendix I). As these routing decisions involve non-differentiable operations such as argmax or one-hot sampling, we use the Gumbel-Softmax reparameterization technique to facilitate optimization (Gumbel, 1954; Jang et al., 2017).

We pose four research questions (RQs):

**RQ1: What properties of TS are likely to rely on LLMs?**
We train LLM4TSF (Pre-align) & (Post-align) under a cross-dataset learning setting, where each token is routed to either pass through or skip the LLM. As shown in Fig. 7, datasets with stronger shifting or unseen (out-of-domain) distributions tend to exhibit higher ratios of tokens passing through the LLM. Moreover, the Post-align setting, which fine-tunes LLM parameters, leads to higher passing ratios compared to Pre-align. Since different TS segments within the same dataset may exhibit distinct properties, dataset-level analysis alone is insufficient to fully characterize the router's decision behavior. Therefore, we analyze the relationship between the properties of all test-set TS segments and their passing ratios to the LLM, visualizing the joint density p(x, D), where x denotes properties (e.g., shifting or transition) and D ∈ {pass, skip} indicates the routing decision (Fig. 9).

**RQ2: Do pre-trained parameters influence dependency?**
We compare models with pretrained LLM parameters against counterparts with randomly initialized LLMs, assessing how pretraining alters the model's tendency to use or skip the LLM. As shown in Table 3, datasets with higher shifting (e.g., ETTh2, ETTm2, Weather, and Exchange) tend to pass through the LLM, and the passing ratio decreases under the w/o pre-training setting; in contrast, datasets with lower shifting (e.g., ETTh1, ETTm1, Traffic, and ECL) exhibit the opposite trend. Moreover, under the LLM4TSF (Post-align) setting, datasets with lower transition (e.g., Traffic, ECL, and NN) show a strong tendency to skip the LLM, suggesting that for TS data with simpler transition patterns, the encoder & decoder modules alone may suffice for forecasting. Overall, the results in Table 2, together with the routing statistics in Table 3, indicate that tokens tend to select the path associated with lower forecasting error, with shifting and transition emerging as key factors underlying path selection behavior.

**Table 3. Impact of pretrained LLM parameters on the token passing ratio through the LLM, averaged over horizons {96, 192, 336, 720}.** *Ratio < 50% indicates a stronger tendency to skip the LLM.*

### In-Domain Test

| Dataset | Pre-align w/ Pretraining | Pre-align w/o Pretraining | Pre-align Change | Post-align w/ Pretraining | Post-align w/o Pretraining | Post-align Change |
|---|---|---|---|---|---|---|
| ETTh1 | 17% | 24% | +7% | 31% | 57% | +26% |
| ETTh2 | 64% | 43% | -21% | 71% | 62% | -9% |
| ETTm1 | 19% | 14% | -5% | 24% | 66% | +42% |
| ETTm2 | 73% | 28% | -45% | 76% | 68% | -8% |
| Weather | 62% | 39% | -23% | 68% | 62% | -6% |
| Traffic | 21% | 27% | +6% | 40% | 46% | +6% |
| Exchange | 70% | 31% | -39% | 74% | 59% | -15% |
| Covid | 68% | 15% | -53% | 65% | 55% | -10% |
| ECL | 14% | 21% | +7% | 19% | 37% | +18% |
| NN | 59% | 26% | -23% | 65% | 43% | -22% |

### Out-of-Domain Test

| Dataset | Pre-align w/ Pretraining | Pre-align w/o Pretraining | Pre-align Change | Post-align w/ Pretraining | Post-align w/o Pretraining | Post-align Change |
|---|---|---|---|---|---|---|
| Wind | 66% | 14% | -52% | 71% | 65% | -6% |
| Solar | 69% | 18% | -51% | 75% | 60% | -15% |
| AQShunyi | 84% | 25% | -59% | 80% | 58% | -22% |
| CzenLan | 71% | 21% | -50% | 77% | 71% | -6% |
| ZafNoo | 78% | 26% | -52% | 69% | 79% | +10% |
| NASDAQ | 65% | 19% | -46% | 83% | 75% | -8% |
| PEMS | 75% | 15% | -60% | 81% | 85% | +4% |

**RQ3: Do training strategies modulate the LLMs?**
By comparing different training strategies, we analyze whether they alter the overall tendency to use or skip the LLM. Taking full-parameter fine-tuning as the baseline, we consider LoRA (Hu et al., 2022) and a lightweight strategy that updates only positional embeddings and layer normalization, following prior work (Zhou et al., 2023b; Hu et al., 2025a). Fig. 10 shows that Full-Para enables the most effective utilization of the LLM, yielding the best overall performance. This indicates that unrestricted parameter optimization may better exploit the model's representational capacity, thereby improving task performance.

**Figure 10 data (LLM4TSF(Post-align) performance and token passing ratios under three training strategies):**

| Setting | In-Domain Avg. MSE | In-Domain Avg. Ratio | Out-of-Domain Avg. MSE | Out-of-Domain Avg. Ratio |
|---|---|---|---|---|
| Full-Para | 0.491 | 53.3% | 0.548 | 76.6% |
| LoRA | 0.524 | 42.1% | 0.597 | 62.2% |
| PE+LN | 0.571 | 37.4% | 0.682 | 51.9% |

**RQ4: Do stronger LLMs consistently lead to greater gains?**
We replace the LLM backbone with the stronger Qwen-3 (Yang et al., 2025) and observe that stronger general capabilities do not consistently translate into improved performance (Table 12). However, artificially truncating the model by retaining only half of its layers, as in prior work (Jin et al., 2023; Liu et al., 2024c; 2025a; Hu et al., 2025a), leads to noticeable performance degradation (see Appendix G.3). More importantly, omitting prompts weakens the effectiveness of LLMs and leads to noticeable performance degradation, an effect that is particularly pronounced in out-of-domain scenarios. This suggests that enriching prompt information is more impactful than indiscriminately scaling up the model backbone in TSF.

---

## 6. Discussion and Conclusion

### Discussion

1. **Cross-dataset learning is a crucial prerequisite for unlocking the full potential of LLMs.** By exposing LLMs to diverse data, cross-dataset learning enables stronger performance.
2. **Pre-alignment provides a more effective integration strategy for LLM4TSF.** Aligning TS inputs with word embeddings leads to more compatible representations, resulting in lower errors.
3. **The advantages of LLM4TSF arise from both pretrained knowledge and architectural modeling capacity.** They both contribute to improved forecasting capability.
4. **LLM4TSF exhibit inherent preferences toward certain TS properties.** In particular, LLMs tend to achieve advantages on TS with pronounced shifting or complex transition patterns.
5. **Both a complete architecture and sufficient parameter optimization are essential for achieving strong performance.** Preserving the full LLM architecture and enabling adequate parameter optimization are necessary to leverage the LLMs.
6. **The routing mechanism provides direct evidence for the observed macroscopic performance.** The routing offers a view of how LLM4TSF allocates modeling capacity, serving as a concrete explanation.
7. **Blindly scaling up LLM backbones does not necessarily lead to better performance.** Simply increasing model size without adequate modality alignment may yield diminishing returns, limiting the benefits.

More analysis is provided in Appendix B.

### Conclusion

In this work, we revisit the role of LLM4TSF and provide a clear characterization of when and why LLM4TSF models are effective. In addition, we show that the benefits of LLMs are neither universal nor incidental, but arise from the interplay between LLM knowledge and architectural capacity under specific distributions. By fine-grained routing analysis, we reveal that LLMs exhibit consistent preferences over TS with different statistical properties, which explains their empirical gains and limitations. We not only clarify ongoing debates surrounding LLM4TSF, but also offer guidance for designing more principled models.

---

## References

Ansari, A. F., Stella, L., Turkmen, C., Zhang, X., Mercado, P., Shen, H., Shchur, O., Rangapuram, S. S., Arango, S. P., Kapoor, S., et al. Chronos: Learning the language of time series. *arXiv preprint arXiv:2403.07815*, 2024.

Bengio, Y., Leonard, N., and Courville, A. Estimating or propagating gradients through stochastic neurons for conditional computation. *arXiv preprint arXiv:1308.3432*, 2013.

Bian, Y., Ju, X., Li, J., Xu, Z., Cheng, D., and Xu, Q. Multi-patch prediction: Adapting llms for time series representation learning. *arXiv preprint arXiv:2402.04852*, 2024.

Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P., Neelakantan, A., Shyam, P., Sastry, G., Askell, A., et al. Language models are few-shot learners. *Advances in neural information processing systems*, 33: 1877–1901, 2020.

Cao, H., Wang, Y., Chen, J., Jiang, D., Zhang, X., Tian, Q., and Wang, M. Swin-unet: Unet-like pure transformer for medical image segmentation. In *European conference on computer vision*, pp. 205–218. Springer, 2022.

Ceperic, V. and Markovic, T. Transforming time-series data for improved llm-based forecasting through adaptive encoding. *Int. J. Simul. Syst. Sci. Technol*, 25:8–1, 2024.

Chang, C., Wang, W.-Y., Peng, W.-C., and Chen, T.-F. Llm4ts: Aligning pre-trained llms as data-efficient time-series forecasters. *ACM Transactions on Intelligent Systems and Technology*, 16(3):1–20, 2025.

Chen, Y., Cespedes, N., and Barnaghi, P. A closer look at transformers for time series forecasting: Understanding why they work and where they struggle. In *Forty-second International Conference on Machine Learning*, 2025.

Cheng, D., Xu, Z., Jiang, X., Wang, N., Li, D., and Gao, X. Disentangled prompt representation for domain generalization. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, pp. 23595–23604, 2024.

Cini, A., Jenkins, A., Mandic, D., Alippi, C., and Bianchi, F. M. Relational conformal prediction for correlated time series. *arXiv preprint arXiv:2502.09443*, 2025.

De Gooijer, J. G. and Hyndman, R. J. 25 years of time series forecasting. *International journal of forecasting*, 22(3): 443–473, 2006.

Dong, L., Xu, S., and Xu, B. Speech-transformer: a no-recurrence sequence-to-sequence model for speech recognition. In *2018 IEEE international conference on acoustics, speech and signal processing (ICASSP)*, pp. 5884–5888. IEEE, 2018.

Gao, S., Koker, T., Queen, O., Hartvigsen, T., Tsiligkaridis, T., and Zitnik, M. Units: A unified multi-task time series model. *Advances in Neural Information Processing Systems*, 37:140589–140631, 2024.

Gumbel, E. J. *Statistical theory of extreme values and some practical applications: a series of lectures*, volume 33. US Government Printing Office, 1954.

He, H., Queen, O., Koker, T., Cuevas, C., Tsiligkaridis, T., and Zitnik, M. Domain adaptation for time series under feature and label shifts. In *International conference on machine learning*, pp. 12746–12774. PMLR, 2023.

Heidrich, B., Turowski, M., Phipps, K., Schmieder, K., Suß, W., Mikut, R., and Hagenmeyer, V. Controlling non-stationarity and periodicities in time series generation using conditional invertible neural networks. *Applied Intelligence*, 53(8):8826–8843, 2023.

Hu, E. J., Shen, Y., Wallis, P., Allen-Zhu, Z., Li, Y., Wang, S., Wang, L., Chen, W., et al. Lora: Low-rank adaptation of large language models. *ICLR*, 1(2):3, 2022.

Hu, Y., Li, Q., Zhang, D., Yan, J., and Chen, Y. Context-alignment: Activating and enhancing llms capabilities in time series. In Yue, Y., Garg, A., Peng, N., Sha, F., and Yu, R. (eds.), *International Conference on Representation Learning*, volume 2025, pp. 90696–90722, 2025a.

Hu, Y., Liao, H., Wu, M., and Yuan, L. Sst-llm: time series forecasting based on large language models. In *International Symposium on Artificial Intelligence Innovations (IS-AII 2025)*, volume 13681, pp. 198–206. SPIE, 2025b.

Hu, Y., Zhang, G., Liu, P., Lan, D., Li, N., Cheng, D., Dai, T., Xia, S.-T., and Pan, S. Timefilter: Patch-specific spatial-temporal graph filtration for time series forecasting. *arXiv preprint arXiv:2501.13041*, 2025c.

Huang, L., Zhong, S., Wu, X., and Li, R. The solution for the cvpr2024 nice image captioning challenge. *arXiv preprint arXiv:2404.12739*, 2024.

Huang, R., Zhang, Z., and Wang, Y. Cross-moe: An efficient temporal prediction framework integrating textual modality. In *Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing*, pp. 29915–29926, 2025.

Huynh, C., Yang, J., Tawari, A., Shah, M., Tran, S., Hamid, R., Chilimbi, T., and Shrivastava, A. Collm: A large language model for composed image retrieval. In *Proceedings of the Computer Vision and Pattern Recognition Conference*, pp. 3994–4004, 2025a.

Huynh, N. D., Bouadjenek, M. R., Aryal, S., Razzak, I., and Hacid, H. Visual question answering: from early developments to recent advances–a survey. *arXiv preprint arXiv:2501.03939*, 2025b.

Jain, S., Salman, H., Khaddaj, A., Wong, E., Park, S. M., and Mkadry, A. A data-based perspective on transfer learning. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, pp. 3613–3622, 2023.

Jang, E., Gu, S., and Poole, B. Categorical reparameterization with gumbel-softmax, 2017. URL https://arxiv.org/abs/1611.01144.

Jiang, Y., Pan, Z., Zhang, X., Garg, S., Schneider, A., Nevmyvaka, Y., and Song, D. Empowering time series analysis with large language models: A survey. *arXiv preprint arXiv:2402.03182*, 2024.

Jiang, Y., Yu, W., Lee, G., Song, D., Shin, K., Cheng, W., Liu, Y., and Chen, H. Explainable multi-modal time series prediction with llm-in-the-loop. *arXiv preprint arXiv:2503.01013*, 2025.

Jin, M., Wang, S., Ma, L., Chu, Z., Zhang, J. Y., Shi, X., Chen, P.-Y., Liang, Y., Li, Y.-F., Pan, S., et al. Time-llm: Time series forecasting by reprogramming large language models. *arXiv preprint arXiv:2310.01728*, 2023.

Kim, J., Kim, H., Kim, H., Lee, D., and Yoon, S. A comprehensive survey of deep learning for time series forecasting: architectural diversity and open challenges. *Artificial Intelligence Review*, 58(7):1–95, 2025.

Kim, T., Kim, J., Tae, Y., Park, C., Choi, J.-H., and Choo, J. Reversible instance normalization for accurate time-series forecasting against distribution shift. In *International conference on learning representations*, 2021.

Kong, X., Chen, Z., Liu, W., Ning, K., Zhang, L., Muhammad Marier, S., Liu, Y., Chen, Y., and Xia, F. Deep learning for time series forecasting: a survey. *International Journal of Machine Learning and Cybernetics*, pp. 1–34, 2025.

Kuckreja, K., Danish, M. S., Naseer, M., Das, A., Khan, S., and Khan, F. S. Geochat: Grounded large vision-language model for remote sensing. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, pp. 27831–27840, 2024.

Lee, G., Yu, W., Shin, K., Cheng, W., and Chen, H. Timecap: Learning to contextualize, augment, and predict time series events with large language model agents. In *Proceedings of the AAAI Conference on Artificial Intelligence*, volume 39, pp. 18082–18090, 2025.

Lei, P., Song, J., Hao, Y., Chen, T., Zhang, Y., JIA, L., Li, Y., et al. Itformer: Bridging time series and natural language for multi-modal qa with large-scale multitask dataset. In *Forty-second International Conference on Machine Learning*.

Li, M., Yang, M., Chen, S., Li, H., Xing, G., and Li, S. Fcp-former: Enhancing long-term multivariate time series forecasting with frequency compensation. *Sensors*, 25(18):5646, 2025.

Liang, X., Yang, E., Deng, C., and Yang, Y. Crossformer: Cross-modal representation learning via heterogeneous graph transformer. *ACM Transactions on Multimedia Computing, Communications and Applications*, 20(12):1–21, 2024.

Lin, B., Ye, Y., Zhu, B., Cui, J., Ning, M., Jin, P., and Yuan, L. Video-llava: Learning united visual representation by alignment before projection. In *Proceedings of the 2024 conference on empirical methods in natural language processing*, pp. 5971–5984, 2024.

Lin, Y., Koprinska, I., and Rana, M. Ssdnet: State space decomposition neural network for time series forecasting. In *2021 IEEE International conference on data mining (ICDM)*, pp. 370–378. IEEE, 2021.

Liu, C., Xu, Q., Miao, H., Yang, S., Zhang, L., Long, C., Li, Z., and Zhao, R. Timecma: Towards llm-empowered multivariate time series forecasting via cross-modality alignment. In *Proceedings of the AAAI Conference on Artificial Intelligence*, 2025a.

Liu, C., Zhou, S., Xu, Q., Miao, H., Long, C., Li, Z., and Zhao, R. Towards cross-modality modeling for time series analytics: A survey in the llm era. *arXiv preprint arXiv:2505.02583*, 2025b.

Liu, H., Xu, S., Zhao, Z., Kong, L., Prabhakar Kamarthi, H., Sasanur, A., Sharma, M., Cui, J., Wen, Q., Zhang, C., et al. Time-mmd: Multi-domain multimodal dataset for time series analysis. *Advances in Neural Information Processing Systems*, 37:77888–77933, 2024a.

Liu, P., Guo, H., Dai, T., Li, N., Bao, J., Ren, X., Jiang, Y., and Xia, S.-T. Calf: Aligning llms for time series forecasting via cross-modal fine-tuning. In *Proceedings of the AAAI Conference on Artificial Intelligence*, 2025c.

Liu, X. and Wang, W. Deep time series forecasting models: A comprehensive survey. *Mathematics*, 12(10):1504, 2024.

Liu, X., Hu, J., Li, Y., Diao, S., Liang, Y., Hooi, B., and Zimmermann, R. Unitime: A language-empowered unified model for cross-domain time series forecasting. In *Proceedings of the ACM Web Conference 2024*, pp. 4095–4106, 2024b.

Liu, Y., Wu, H., Wang, J., and Long, M. Non-stationary transformers: Exploring the stationarity in time series forecasting. *Advances in neural information processing systems*, 35:9881–9893, 2022a.

Liu, Y., Qin, G., Huang, X., Wang, J., and Long, M. Autotimes: Autoregressive time series forecasters via large language models. *Advances in Neural Information Processing Systems*, 37:122154–122184, 2024c.

Liu, Y., Qin, G., Shi, Z., Chen, Z., Yang, C., Huang, X., Wang, J., and Long, M. Sundial: A family of highly capable time series foundation models, 2025d.

Liu, Y., Wang, L., and Ng, B. F. Multitask-transfer-learning method for random-force frequency identification considering multisource uncertainties. *AIAA Journal*, 63(6):2345–2360, 2025e.

Liu, Z., Lin, Y., Cao, Y., Hu, H., Wei, Y., Zhang, Z., Lin, S., and Guo, B. Swin transformer: Hierarchical vision transformer using shifted windows. In *Proceedings of the IEEE/CVF international conference on computer vision*, pp. 10012–10022, 2021.

Liu, Z., Ning, J., Cao, Y., Wei, Y., Zhang, Z., Lin, S., and Hu, H. Video swin transformer. In *Proceedings of the IEEE/CVF conference on computer vision and pattern recognition*, pp. 3202–3211, 2022b.

Majeedi, A., Gajjala, V. R., GNVV, S. S. S. N., Elkordi, N. M., and Li, Y. Lets forecast: Learning embedology for time series forecasting. *arXiv preprint arXiv:2506.06454*, 2025.

Masini, R. P., Medeiros, M. C., and Mendes, E. F. Machine learning advances for time series forecasting. *Journal of economic surveys*, 37(1):76–111, 2023.

Masserano, L., Ansari, A. F., Han, B., Zhang, X., Faloutsos, C., Mahoney, M. W., Wilson, A. G., Park, Y., Rangapuram, S., Maddix, D. C., et al. Enhancing foundation models for time series forecasting via wavelet-based tokenization. *arXiv preprint arXiv:2412.05244*, 2024.

Meunier, R., Benamara, F., Moriceau, V., Qiao, Z., and Ramasamy, S. Crisists: Coupling social media textual data and meteorological time series for urgency classification. In *Proceedings of the 63rd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers)*, pp. 16082–16099, 2025.

Moon, J. H., Lee, H., Shin, W., Kim, Y.-H., and Choi, E. Multi-modal understanding and generation for medical images and text via vision-language pre-training. *IEEE Journal of Biomedical and Health Informatics*, 26(12):6070–6080, 2022.

Nie, Y., H. Nguyen, N., Sinthong, P., and Kalagnanam, J. A time series is worth 64 words: Long-term forecasting with transformers. In *International Conference on Learning Representations*, 2023.

Ning, K., Pan, Z., Liu, Y., Jiang, Y., Zhang, J. Y., Rasul, K., Schneider, A., Ma, L., Nevmyvaka, Y., and Song, D. Ts-rag: Retrieval-augmented generation based time series foundation models are stronger zero-shot forecaster, 2025.

Painblanc, F., Chapel, L., Courty, N., Friguet, C., Pelletier, C., and Tavenard, R. Match-and-deform: Time series domain adaptation through optimal transport and temporal alignment. In *Joint European Conference on Machine Learning and Knowledge Discovery in Databases*, pp. 341–356. Springer, 2023.

Pan, Z., Jiang, Y., Garg, S., Schneider, A., Nevmyvaka, Y., and Song, D. Ssip-llm: Semantic space informed prompt learning with llm for time series forecasting. In *Forty-first International Conference on Machine Learning*, 2024.

Qiu, X., Tong, J., Sun, Y., Ma, Y., and Shen, X. The few govern the many: unveiling few-layer dominance for time series models, 2025. URL https://arxiv.org/abs/2511.07237.

Radford, A., Wu, J., Child, R., Luan, D., Amodei, D., Sutskever, I., et al. Language models are unsupervised multitask learners. *OpenAI blog*, 1(8):9, 2019.

Siru, Z., Weilin, R., Jin, M., Huan, L., Qingsong, W., and Yuxuan, L. Time-vlm: Exploring multimodal vision-language models for augmented time series forecasting. In *Forty-Second International Conference on Machine Learning (ICML 2025)*. Proceedings of Machine Learning Research, 2025.

Sun, S., Zhang, K., Jiang, X., Meng, W., and Yang, Q. Enhancing llms for time series forecasting via structure-guided cross-modal alignment. *arXiv preprint arXiv:2505.13175*, 2025.

Tan, M., Merrill, M., Gupta, V., Althoff, T., and Hartvigsen, T. Are language models actually useful for time series forecasting? *Advances in Neural Information Processing Systems*, 37:60162–60191, 2024.

Tao, X., Zhang, S., Cheng, M., Wang, D., Pan, T., Pan, B., Zhang, C., and Wang, S. From values to tokens: An llm-driven framework for context-aware time series forecasting via symbolic discretization. *arXiv preprint arXiv:2508.09191*, 2025.

Wang, B., Yang, H., and Sheng, J. Timecf: A timemixer-based model with adaptive convolution and sharpness-aware minimization frequency domain loss for long-term time series forecasting. *arXiv preprint arXiv:2505.17532*, 2025a.

Wang, H., Pan, L., Chen, Z., Chen, X., Dai, Q., Wang, L., Li, H., and Lin, Z. Transdf: Time-series forecasting needs transformed label alignment. *arXiv preprint arXiv:2505.17847*, 2025b.

Wang, L., Ao, W., Boddeti, V. N., and Lim, S.-N. Generative zero-shot composed image retrieval. In *Proceedings of the Computer Vision and Pattern Recognition Conference*, pp. 29690–29700, 2025c.

Wang, X., Feng, M., Qiu, J., Gu, J., and Zhao, J. From news to forecast: Integrating event analysis in llm-based time series forecasting with reflection. *Advances in Neural Information Processing Systems*, 37:58118–58153, 2024.

Wang, Y., Qiu, Y., Chen, P., Zhao, K., Shu, Y., Rao, Z., Pan, L., Yang, B., and Guo, C. Towards a general time series forecasting model with unified representation and adaptive transfer. In *Forty-second International Conference on Machine Learning*.

Wang, Z. and Mao, Y. On f-divergence principled domain adaptation: An improved framework. *Advances in Neural Information Processing Systems*, 37:6711–6748, 2024.

Weiss, K., Khoshgoftaar, T. M., and Wang, D. A survey of transfer learning. *Journal of Big data*, 3(1):9, 2016.

Wilinski, M., Goswami, M., Potosnak, W., Zukowska, N., and Dubrawski, A. Exploring representations and interventions in time series foundation models. In *Forty-second International Conference on Machine Learning*, 2025. URL https://openreview.net/forum?id=goVzfYtj58.

Wolff, M. L., Yang, S., Torkkola, K., and Mahoney, M. W. Using pre-trained llms for multivariate time series forecasting. *arXiv preprint arXiv:2501.06386*, 2025.

Woo, G., Liu, C., Kumar, A., Xiong, C., Savarese, S., and Sahoo, D. Unified training of universal time series forecasting transformers. In *Proceedings of the 41st International Conference on Machine Learning, ICML'24*. JMLR.org, 2024a.

Woo, G., Liu, C., Kumar, A., Xiong, C., Savarese, S., and Sahoo, D. Unified training of universal time series forecasting transformers. 2024b.

Wu, H., Xu, J., Wang, J., and Long, M. Autoformer: Decomposition transformers with auto-correlation for long-term series forecasting. *Advances in neural information processing systems*, 34:22419–22430, 2021.

Xiao, C., Zhou, J., Xiao, Y., Lu, X., Zhang, L., and Xiong, H. Timefound: A foundation model for time series forecasting, 2025.

Xiong, J., Wang, C., Sun, H., Jing, Y., Qi, Q., Zhuang, Z., Zhang, L., Liao, J., and Wang, J. Beyond statistical analysis: Multimodal framework for time series forecasting with llm-driven temporal pattern. In *Proceedings of the Thirty-Fourth International Joint Conference on Artificial Intelligence*, pp. 6696–6704, 2025.

Yang, A., Li, A., Yang, B., Zhang, B., Hui, B., Zheng, B., Yu, B., Gao, C., Huang, C., Lv, C., Zheng, C., Liu, D., Zhou, F., Huang, F., Hu, F., Ge, H., Wei, H., Lin, H., Tang, J., Yang, J., Tu, J., Zhang, J., Yang, J., Yang, J., Zhou, J., Zhou, J., Lin, J., Dang, K., Bao, K., Yang, K., Yu, L., Deng, L., Li, M., Xue, M., Li, M., Zhang, P., Wang, P., Zhu, Q., Men, R., Gao, R., Liu, S., Luo, S., Li, T., Tang, T., Yin, W., Ren, X., Wang, X., Zhang, X., Ren, X., Fan, Y., Su, Y., Zhang, Y., Zhang, Y., Wan, Y., Liu, Y., Wang, Z., Cui, Z., Zhang, Z., Zhou, Z., and Qiu, Z. Qwen3 technical report, 2025.

Yu, H., Yi, S., Niu, K., Zhuo, M., and Li, B. Umit: Unifying medical imaging tasks via vision-language models, 2025. URL https://arxiv.org/abs/2503.15892.

Yu, J., Wang, Z., Vasudevan, V., Yeung, L., Seyedhosseini, M., and Wu, Y. Coca: Contrastive captioners are image-text foundation models. *arXiv preprint arXiv:2205.01917*, 2022.

Yunita, A., Pratama, M. I., Almuzakki, M. Z., Ramadhan, H., Akhir, E. A. P., Mansur, A. B. F., and Basori, A. H. Performance analysis of neural network architectures for time series forecasting: A comparative study of rnn, lstm, gru, and hybrid models. *MethodsX*, 15:103462, 2025.

Zhan, Y., Xiong, Z., and Yuan, Y. Skyeyegpt: Unifying remote sensing vision-language tasks via instruction tuning with large language model. *ISPRS Journal of Photogrammetry and Remote Sensing*, 221:64–77, 2025.

Zhang, W., Wang, H., and Zhang, F. Skip-timeformer: Skip-time interaction transformer for long sequence time-series forecasting. In *International joint conference on artificial intelligence*, pp. 5499–5507, 2024a.

Zhang, X., Chowdhury, R. R., Gupta, R. K., and Shang, J. Large language models for time series: A survey. *arXiv preprint arXiv:2402.01801*, 2024b.

Zhang, X., Feng, S., and Li, X. From text to time? rethinking the effectiveness of the large language model for time series forecasting. *arXiv preprint arXiv:2504.08818*, 2025.

Zhang, Y., Dong, Y., Zhang, S., Min, T., Su, H., and Zhu, J. Exploring the transferability of visual prompting for multimodal large language models. In *Proceedings of the IEEE/CVF Conference on Computer Vision and Pattern Recognition*, pp. 26562–26572, 2024c.

Zheng, L. N., Dong, C., Zhang, W. E., Yue, L., Xu, M., Maennel, O., and Chen, W. Understanding why large language models can be ineffective in time series analysis: The impact of modality alignment. In *Proceedings of the 31st ACM SIGKDD Conference on Knowledge Discovery and Data Mining V. 2*, pp. 4026–4037, 2025a.

Zheng, L. N., Liang, W., Zhang, W. E., Xu, M., Maennel, O., and Chen, W. Lifting manifolds to mitigate pseudo-alignment in llm4ts, 2025b. URL https://arxiv.org/abs/2510.12847.

Zhou, J., Lu, T., Mishra, S., Brahma, S., Basu, S., Luan, Y., Zhou, D., and Hou, L. Instruction-following evaluation for large language models. *arXiv preprint arXiv:2311.07911*, 2023a.

Zhou, S., Schoner, H., Lyu, H., Fouché, E., and Wang, S. Balm-tsf: Balanced multimodal alignment for llm-based time series forecasting. In *Proceedings of the 34th ACM International Conference on Information and Knowledge Management*, pp. 4498–4508, 2025.

Zhou, T., Niu, P., Sun, L., Jin, R., et al. One fits all: Power general time series analysis by pretrained lm. *Advances in neural information processing systems*, 36:43322–43355, 2023b.

---

## Appendix A. Related Work

### A.1. LLMs for TSF

Directly applying fully pretrained LLMs to TSF tasks poses a central challenge in achieving effective modality alignment, as LLMs are originally optimized for discrete textual tokens rather than continuous temporal signals. Bridging the representational gap between TS data and the linguistic embedding space of LLMs has therefore become a key research focus (Jiang et al., 2024; Wang et al., 2024; Liu et al., 2024c; 2025b; Jiang et al., 2025). Existing studies addressing this challenge can be broadly categorized into two representative paradigms, depending on whether alignment is performed before or after the LLM is involved in the modeling pipeline (Zhou et al., 2025; Xiong et al., 2025; Hu et al., 2025b; Tao et al., 2025).

The first category follows a **pre-alignment** strategy, which aims to align TS and textual modalities prior to LLM input. In this paradigm, raw or encoded TS are transformed into intermediate representations that are compatible with the LLM token embedding space, often via learnable projection layers or modality-specific encoders. These TS representations are then concatenated or interleaved with textual prompts and fed into a frozen LLM for downstream forecasting tasks. By keeping the LLM parameters fixed, this approach preserves the pretrained linguistic and semantic knowledge of the LLM while enabling it to process TS information in a unified embedding space. As a result, pre-alignment methods offer strong parameter efficiency and stability, making them particularly attractive in low-resource or deployment-constrained scenarios (Zhang et al., 2024b; Ceperic & Markovic, 2024).

The second category adopts a **post-alignment** strategy, in which LLMs are fine-tuned to adapt to TSF tasks by reducing the representational discrepancy between textual and TS modalities within the LLM embedding space (Bian et al., 2024; Lee et al., 2025; Sun et al., 2025). Rather than enforcing compatibility before input, these methods rely on task-driven learning signals to implicitly or explicitly align modalities during training. This is commonly achieved through joint optimization objectives, cross-modal alignment losses, or auxiliary supervision that encourages coherent representations across modalities. While the original LLM architecture is typically preserved, a subset of model parameters is updated to improve task-specific performance. Consequently, post-alignment approaches offer greater flexibility and expressive power at the cost of increased training complexity and computational overhead.

### A.2. Transfer Learning

Transfer learning has become a widely adopted paradigm in deep learning, demonstrating remarkable effectiveness across a wide range of domains (Weiss et al., 2016; Jain et al., 2023; Wang & Mao, 2024; Zhang et al., 2024c; Liu et al., 2025e). By pretraining models on large-scale datasets and transferring them to downstream tasks, prior work has shown substantial improvements in both performance and data efficiency. In vision–language research, for example, pretrained multimodal models jointly learn representations from images and text, enabling effective transfer to applications such as image retrieval (Wang et al., 2025c; Huynh et al., 2025a), image captioning (Yu et al., 2022; Huang et al., 2024), and visual question answering (Lin et al., 2024; Huynh et al., 2025b). In speech and language modeling, pretraining strategies that integrate acoustic signals with textual supervision have significantly advanced automatic speech recognition and semantic understanding. Similar successes have also been observed in domains such as healthcare (Moon et al., 2022; Yu et al., 2025) and remote sensing (Kuckreja et al., 2024; Zhan et al., 2025).

These advances suggest that when different modalities exhibit strong semantic complementarity, large-scale pretrained models — particularly LLMs — can learn representations with high transferability and generalization capability. However, this assumption does not directly extend to TS data and TSF tasks. Unlike images or speech signals, TS data represent real-world processes in a highly abstract numerical form, often lacking explicit semantic grounding in natural language. As a result, the correspondence between TS and textual modalities is inherently ambiguous, making it difficult to directly transfer pretrained knowledge from LLMs to TSF. At the same time, generalization — especially under cross-domain settings — is a fundamental requirement of practical TSF systems. In many applications, the target domain may differ from the source domain in terms of data distributions, temporal patterns, or underlying dynamics, while labeled TS data in the target domain are often limited or unavailable. Models trained with strong domain-specific inductive biases therefore tend to suffer significant performance degradation when deployed across domains. In this context, LLMs offer a promising opportunity for cross-domain TSF due to their strong generalization abilities.

---

## Appendix B. Analysis

**(1) Cross-dataset learning is a crucial prerequisite for unlocking the full potential of LLMs.** Compared to small-scale training on a single dataset, diverse cross-dataset learning within a unified framework more effectively exploits the capabilities of LLMs. This strategy not only alleviates overfitting but also leads to stronger overall performance. Specifically, it surpasses single-dataset baselines on in-domain tasks and consistently outperforms a range of strong time-series foundation models as well as LLM-based approaches in out-of-domain evaluations, with the performance gains becoming increasingly pronounced as the diversity and scale of training data grow (Fig. 14).

**(2) Pre-alignment provides a more effective integration strategy for LLM4TSF.** We observe that aligning TS inputs with word embeddings before feeding them into LLMs yields lower forecasting errors than performing alignment between text and TS representations within the LLM space. This finding suggests that pre-alignment enables a more compatible input representation, leading to more effective utilization of the pretrained LLM parameters.

**(3) The advantages of LLM4TSF arise from both pretrained knowledge and architectural modeling capacity.** Our analysis shows that the performance improvements of LLM4TSF models stem from two complementary sources. Pretrained parameters endow the model with rich prior knowledge, while the expressive Transformer-based architecture provides strong sequence modeling capacity. Together, these factors enable LLM4TSF to achieve strong performance across a wide range of forecasting scenarios.

**(4) LLM4TSF exhibit inherent preferences toward certain TS properties.** On the one hand, pretrained knowledge provides strong priors that are particularly beneficial when data distributions shift substantially over time or when models are evaluated on previously unseen out-of-domain datasets. On the other hand, the expressive architecture of LLMs offers strong modeling capacity, enabling them to better capture complex temporal dynamics characterized by frequent or abrupt transitions in underlying patterns. In contrast, factors such as stationarity, seasonality, or trends are not the primary driver, suggesting that simpler models may already be sufficient when such characteristics dominate.

**(5) Both a complete architecture and sufficient parameter optimization are essential for achieving strong performance.** Our results show that full-parameter fine-tuning consistently outperforms parameter-efficient alternatives such as LoRA or partial adaptation strategies (e.g., positional encoding and layer normalization tuning). Moreover, artificially truncating the LLM by retaining only its shallow layers leads to noticeable performance degradation, as it undermines the model's ability to fully exploit its architectural depth and pretrained capacity (Fig. 15).

**(6) The routing mechanism provides direct evidence for the observed macroscopic performance.** We not only observe performance gaps in overall MAE/MSE, but also gain fine-grained insight into model decision-making. Empirically, the model prefers paths that yield lower prediction errors. This token-level routing preference closely aligns with macroscopic performance trends, offering direct micro-level evidence for when and why incorporating LLMs leads to performance gains.

**(7) Blindly scaling up LLM backbones does not necessarily lead to better performance.** Our experiments reveal that simply replacing the backbone with a larger LLM does not consistently yield performance improvements. One possible reason is the inherent modality gap between natural language and TS data, which makes direct alignment of increasingly large LLMs with TSF tasks more challenging. In addition, prior studies have shown that large-scale TS models often contain substantial internal redundancy (Qiu et al., 2025; Wilinski et al., 2025), which may limit the practical benefits of naive model scaling.

---

## Appendix C. Time Series Forecasting Task

### C.1. Problem Formulation

The TSF task aims to predict future observations based on historical TS data. Formally, given a multivariate TS of length T,

X₁:T = {x₁, x₂, …, x_T}, x_t ∈ ℝ^d,

where x_t denotes the d-dimensional observation at time step t, the objective of TSF is to forecast the next H time steps,

X̂_(T+1:T+H) = {x̂_(T+1), x̂_(T+2), …, x̂_(T+H)}.

Each observation is first mapped into a latent representation space to facilitate downstream modeling. Specifically, the embedding at time step t is defined as:

z_t = f_encoder(x_t), z_t ∈ ℝ^k,

where f_encoder(·) denotes the embedding function and k is the latent dimensionality. Based on the encoded sequence {z₁, z₂, …, z_T}, a forecasting model learns a mapping that captures temporal dependencies and generates predictions for future time steps.

### C.2. In-domain and Cross-domain Evaluation

We consider both in-domain and cross-domain evaluation settings for the TSF task, which differ in the relationship between the training and testing data distributions.

**In-domain Evaluation.** In the in-domain setting, the training and test TS are drawn from the same underlying data distribution. Formally, let D_train and D_test denote the distributions of the training and test TS, respectively. In-domain evaluation assumes D_train = D_test. Under this setting, the forecasting model is trained and evaluated on TS that share similar temporal patterns, statistical properties, and domain characteristics. The goal is to assess the model's ability to capture temporal dependencies within a fixed domain.

**Cross-domain Evaluation.** In contrast, the cross-domain setting evaluates the model's generalization ability when the training and test TS originate from different domains. Specifically, the training and test distributions satisfy D_train ≠ D_test. These domains may differ in data distributions, temporal dynamics, scales, or underlying generative processes. During training, the model has access only to TS sampled from D_train, while at test time it is required to perform TSF on unseen TS drawn from D_test.

### C.3. Zero-shot and Few-shot Test

In cross-domain TSF, we consider zero-shot and few-shot test settings, which differ in the amount of target-domain supervision available at test time. Let D_src denote the source-domain TS distribution used for training, and D_tgt denote the target-domain TS distribution used for testing, where D_src ≠ D_tgt.

**Zero-shot Test.** In the zero-shot setting, the forecasting model is trained solely on TS sampled from the source domain and is directly evaluated on the target domain without observing any labeled TS from D_tgt. Formally, the model learns a forecasting function f_θ using training samples: {X^(i)_(1:T), X^(i)_(T+1:T+H)}^N_(i=1) ∼ D_src, and is evaluated on TS X_(1:T) ∼ D_tgt, where the predicted future values are given by X̂_(T+1:T+H) = f_θ(X_(1:T)). This setting evaluates the model's ability to generalize across domains purely through transferable representations learned during pretraining.

**Few-shot Test.** In the few-shot setting, the model is provided with a small labeled support set from the target domain. Specifically, a support set S_tgt = {X^(j)_(1:T), X^(j)_(T+1:T+H)}^K_(j=1), K ≪ N, is sampled from D_tgt. The model adapts to the target domain by conditioning on S_tgt, yielding an adapted predictor f'_θ = A(f_θ, S_tgt), where A(·) denotes a lightweight adaptation mechanism, such as prompt-based conditioning or parameter-efficient tuning. The adapted model is then evaluated on unseen TS from D_tgt. Compared to zero-shot test, the few-shot setting assesses whether limited target-domain supervision can further improve forecasting performance, while still maintaining strong generalization across domains.

---

## Appendix D. Text Prompt

**ETTh1 prompt.** The ETTh1 designed for time-series forecasting at 1-hour intervals, contains data points with the target variable "oil temperature" and six power load features. Given the past 512 observations, predict the next 96 time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**ETTh2 prompt.** The ETTh2 designed for time-series forecasting at 1-hour intervals, contains data points with the target variable "oil temperature" and six power load features. Given the past 512 observations, predict the next 96 time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**ETTm1 prompt.** The ETTm1 designed for time-series forecasting at 15-minute intervals, contains data points with the target variable "oil temperature" and six power load features. Given the past 512 observations, predict the next 96 time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**ETTm2 prompt.** The ETTm2 designed for time-series forecasting at 15-minute intervals, contains data points with the target variable "oil temperature" and six power load features. Given the past 512 observations, predict the next 96 time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**Weather prompt.** The Weather dataset is designed for time-series forecasting with data recorded every 10 minutes and contains 21 meteorological indicators, such as air temperature, humidity, and wind-related variables. Given the past input length observations, predict the next prediction length time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**Traffic prompt.** The Traffic dataset describes road occupancy conditions and contains hourly measurements collected from highway sensors. Given the past input length observations, predict the next prediction length time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**Exchange prompt.** The Exchange dataset contains daily exchange rate data for eight countries and is commonly used for time-series analysis and forecasting of currency fluctuations. Given the past input length observations, predict the next prediction length time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**ECL prompt.** The ECL dataset represents the hourly electricity consumption, recorded in kilowatts. Given the past input length observations, predict the next prediction length time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**NN prompt.** The NN dataset consists of 111 daily time series drawn from a homogeneous population of empirical cash demand data. Given the past input length observations, predict the next prediction length time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**Wind prompt.** The Wind dataset consists of time-series data recorded at 15-minute intervals, and includes variables such as wind speed, wind direction, temperature, pressure, humidity, and wind power. Given the past input length observations, predict the next prediction length time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**Solar prompt.** The Solar dataset contains 137 time series representing solar power production, recorded at 10-minute intervals. Given the past input length observations, predict the next prediction length time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**AQShunyi prompt.** The AQShunyi dataset includes 11 hourly time series capturing air quality and meteorological conditions in the Shunyi District of Beijing, with variables such as PM2.5, PM10, SO2, NO2, CO, O3, temperature, air pressure, humidity, wind speed, and precipitation. Given the past input length observations, predict the next prediction length time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**Czelan prompt.** The Czelan dataset contains eight time series of plant sap flow measurements recorded at half-hour intervals. Given the past input length observations, predict the next prediction length time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**ZafNoo prompt.** The ZafNoo dataset consists of 11 time series of plant sap flow measurements, recorded at half-hour intervals. Given the past input length observations, predict the next prediction length time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**PEMS prompt.** The PEMS dataset includes 48 months of hourly data describing road occupancy rates measured by various traffic sensors. Given the past input length observations, predict the next prediction length time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

**NASDAQ prompt.** The NASDAQ dataset encompasses companies listed on the NASDAQ stock exchange, with regularly updated time-series data excluding test listings. Given the past input length observations, predict the next prediction length time steps. The input window includes a minimum value of {min value}, a maximum value of {max value}, and a median value of {median value}.

---

## Appendix E. Baselines

**Chronos** (Ansari et al., 2024) reformulates time series forecasting for Transformer-based architectures via a two-stage pre-processing strategy consisting of normalization and discretization. Specifically, each observation is normalized by the mean absolute value of its historical window to ensure scale consistency across different series. The normalized values are then quantized into a finite set of bins, converting the continuous time series into discrete token sequences. These tokens are subsequently modeled using a T5-style Transformer trained with a cross-entropy objective, allowing the model to learn generalizable TS representations while fully exploiting the strengths of sequence modeling frameworks.

**UniTS** (Gao et al., 2024) is a unified time series foundation model that supports a universal task formulation, enabling a wide range of TS tasks including forecasting, classification, imputation, and anomaly detection within a single framework. This capability is realized through a unified network backbone that integrates sequence-wise and variable-wise attention mechanisms together with a dynamic linear operator, allowing the model to flexibly capture temporal dependencies and inter-variable relationships. The entire architecture is trained end-to-end as a single unified model across tasks. Extensive experiments conducted on 38 datasets spanning multiple domains demonstrate that UniTS consistently outperforms specialized task-specific models as well as repurposed natural language-based LLMs.

**Moirai** (Woo et al., 2024a) is a large-scale foundation model for TSF that departs from the conventional practice of training separate models for individual datasets. Through architectural enhancements to the standard Transformer, Moirai enables effective cross-frequency learning, accommodates arbitrary multivariate input dimensionalities, and adapts to heterogeneous data distributions across diverse domains. The model is trained on the Large-scale Open Time Series Archive, comprising more than 27 billion observations spanning nine domains. Owing to its large-scale pretraining, Moirai exhibits strong zero-shot forecasting performance, often matching or outperforming models that are fully fine-tuned on target datasets.

**UniTime** (Liu et al., 2024b) is a unified foundation model for time series analysis that supports multiple tasks under a single modeling framework, including forecasting, classification, imputation, and anomaly detection. It introduces a unified task formulation together with a shared backbone architecture, allowing different TS tasks to be jointly learned without task-specific redesign. By leveraging a task-agnostic representation and a unified training objective, UniTime achieves strong generalization across tasks and datasets. Extensive evaluations demonstrate that UniTime consistently outperforms task-specific baselines and exhibits robust zero-shot and few-shot performance when transferred to unseen datasets and tasks, highlighting its effectiveness as a general-purpose time series model.

**Time-LLM** (Jin et al., 2023) performs time series forecasting by reusing a pretrained large language model whose parameters remain entirely frozen. To adapt the model to TS inputs and outputs, it introduces two lightweight trainable modules: Patch Reprogramming, which converts TS segments into LLM-compatible representations, and Output Projection, which maps the model outputs to the forecasting space. In addition, the method follows a channel-independent formulation, decomposing multivariate forecasting problems into multiple parallel univariate prediction tasks, thereby enabling efficient adaptation without modifying the backbone LLM.

---

## Appendix F. Datasets

### F.1. General Overview

The training datasets cover a wide range of real-world domains, including web, transportation, energy, nature, environment, climate, sales, economics, healthcare, and industry. Such broad domain coverage introduces substantial diversity in temporal patterns, scales, seasonalities, and noise characteristics, which is crucial for learning transferable representations and improving generalization in cross-domain TSF settings.

**Figure 11. Proportional distribution of training datasets across ten real-world domains:**

| Domain | Proportion (%) |
|---|---|
| Web | ~12 |
| Transportation | ~10 |
| Energy | ~14 |
| Climate | ~16 |
| Nature | ~11 |
| Environment | ~9 |
| Sales | ~8 |
| Economics | ~5 |
| Healthcare | ~7 |
| Industry | ~8 |

In addition, the datasets used for in-domain and out-of-domain tests are listed separately, as summarized in Table 4. Among them, 10 datasets, including ETT (four subsets), Weather, Traffic, Exchange, Covid, ECL, and NN, are further split into training, validation, and test subsets. The held-out test splits of these datasets are used for in-domain evaluation. For the ETT datasets, we follow the standard train–validation–test split ratio of 6:2:2, while all other datasets in set A are split using a 7:1:2 ratio. Set B contains 7 datasets, namely Wind, Solar, AQShunyi, CzenLan, ZafNoo, NASDAQ, and PEMS. Set B is completely excluded from the training process and is used solely for out-of-domain test. Some of the collected datasets contain N/A or invalid values. To ensure data quality and training stability, we apply linear interpolation to impute missing values in all datasets.

**Table 4. Summary of datasets used in experiments. The table reports the number of variables and timestamps for each time series dataset.**

| Dataset | Variables | Timestamps | Dataset | Variables | Timestamps |
|---|---|---|---|---|---|
| ETTh1 | 7 | 14,400 | Wind | 7 | 48,673 |
| ETTh2 | 7 | 14,400 | Solar | 137 | 52,560 |
| ETTm1 | 7 | 57,600 | AQShunyi | 11 | 35,064 |
| ETTm2 | 7 | 57,600 | CzenLan | 11 | 19,934 |
| Weather | 21 | 52,696 | ZafNoo | 11 | 19,225 |
| Traffic | 862 | 17,544 | NASDAQ | 5 | 1,244 |
| Exchange | 8 | 7,588 | PEMS | 170 | 17,856 |
| Covid | 948 | 1,392 | | | |
| ECL | 321 | 26,304 | | | |
| NN | 111 | 791 | | | |

### F.2. Statistical Properties of Dataset

We visualize the statistical properties of all datasets used in testing (Fig. 12). **Shifting** describes how the activation regions of the TS evolve along the temporal axis, capturing changes in distributional structure over time. **Stationarity** reflects whether the statistical properties of a TS remain stable over time, indicating the presence or absence of distributional drift. **Transition** characterizes the sequential dependency between symbolic states, reflecting the complexity of temporal transitions and local dynamical behavior. **Seasonality** measures the strength of recurring temporal patterns at fixed intervals, which are commonly observed in real-world periodic processes. **Trend** characterizes the long-term directional movement of the series, revealing persistent growth or decline patterns. The corresponding computation procedures are summarized in Tables 5–9.

**Table 5. Algorithm: Shifting Computation**

**Input:** Time series X ∈ ℝ^(T×1)
**Output:** Shifting δ ∈ (0, 1)

1. Normalize X using z-score normalization to obtain Z ∈ ℝ^(T×1).
2. Compute Z_min = min(Z) and Z_max = max(Z).
3. Construct m uniformly spaced value levels: ℓ_i = Z_min + [(i−1)/(m−1)](Z_max − Z_min), i = 1, …, m.
4. For each level ℓ_i:
   - Identify activated time indices T_i = { t | Z_t > ℓ_i, 1 ≤ t ≤ T }.
   - Compute the temporal center c_i = median(T_i).
5. Apply min–max normalization to {c_i}^m_(i=1) to obtain {c̃_i}^m_(i=1).
6. **Return** δ = |median({c̃_1, c̃_2, …, c̃_m})|.

**Table 6. Algorithm 2: Stationarity Computation**

**Input:** Time series X = ⟨x_1, x_2, …, x_T⟩ ∈ ℝ^(T×1)
**Output:** Stationarity indicator γ ∈ {0, 1} of X

1. Compute the Augmented Dickey–Fuller (ADF) statistic s ← ADF(X).
2. **Return** γ = 1 if s ≤ 0.05, otherwise 0.

**Table 7. Algorithm: Transition Computation**

**Input:** Time series X ∈ ℝ^(T×1)
**Output:** Transition Δ ∈ (0, 1/3)

1. Estimate the characteristic lag τ as the first zero-crossing point of the autocorrelation function of X.
2. Downsample X with stride τ to obtain a reduced sequence Y ∈ ℝ^(T'×1).
3. Obtain the rank ordering of Y by computing the permutation index r = argsort(Y).
4. Discretize Y into a symbolic sequence Z ∈ {0, 1, 2}^(T') via Z_j = ⌊3·r_j/T'⌋, j = 1, …, T'.
5. Initialize a transition count matrix M ∈ ℝ^(3×3) with zeros.
6. For j = 1 to T'−1: increment the transition count M_(Z_j, Z_(j+1)) ← M_(Z_j, Z_(j+1)) + 1.
7. Normalize the transition matrix by sequence length: M' = (1/T')M.
8. Compute the covariance matrix C of the column vectors of M'.
9. **Return** Δ = tr(C).

**Table 8. Algorithm: Seasonality Computation**

**Input:** Time series X = {x_1, x_2, …, x_T} ∈ ℝ^(T×1)
**Output:** Seasonality value ζ ∈ (0, 1)

1. Decompose X into seasonal, trend, and residual components using STL: X = S + T + R.
2. Compute the variance of the residual component R.
3. Compute the variance of the combined seasonal and residual component S + R.
4. **Return** ζ = max(0, 1 − var(R)/var(S+R)).

**Table 9. Algorithm: Trend Computation**

**Input:** Time series X = {x_1, x_2, …, x_T} ∈ ℝ^(T×1)
**Output:** Trend value β ∈ (0, 1)

1. Decompose X into seasonal, trend, and residual components using STL: X = S + T + R.
2. Compute the variance of the residual component R.
3. Compute the variance of the combined non-seasonal component T + R.
4. **Return** β = max(0, 1 − var(R)/var(T+R)).

---

## Appendix G. More Results

### G.1. Single- and Cross-Dataset Evaluation Results

We report the MAE and MSE results under both single-dataset and cross-dataset learning strategies, evaluated with two alignment schemes across four forecasting horizons {96, 192, 336, 720} (Tables 10 and 11).

**Figure 13. Comparison of LLM4TSF performance with pre- and post-alignment under single- and cross-dataset paradigm (Relative MSE Change).** Negative and Positive values indicate MSE decreases and increases under cross-dataset learning compared to single-dataset learning.

| Dataset | LLM4TSF (Pre-align) | LLM4TSF (Post-align) |
|---|---|---|
| ETTh1 | -0.4% | -10.6% |
| ETTh2 | -6.2% | -5.8% |
| ETTm1 | -6.9% | -8.1% |
| ETTm2 | -8.0% | -7.7% |
| Weather | -6.2% | -5.0% |
| Traffic | -0.5% | +2.0% |
| Exchange | -9.5% | -9.0% |
| Covid | -9.3% | -6.8% |
| ECL | +1.2% | +0.6% |
| NN | -4.6% | -2.8% |

### G.2. Effect of Training Data in Cross-Dataset Learning

During cross-dataset learning, we vary the ratio of training data and gradually increase the available data volume. We observe that both MSE and MAE consistently decrease as the training data ratio increases, indicating a strong correlation between model performance and the amount of training data. This trend suggests that cross-dataset forecasting benefits substantially from larger and more diverse training samples (Fig. 14).

**Figure 14 data (Effect of training data on cross-dataset learning performance):**

| Data ratio | MAE (Pre-align) | MAE (Post-align) | MSE (Pre-align) | MSE (Post-align) |
|---|---|---|---|---|
| 0.2 | ~0.377 | ~0.389 | ~0.522 | ~0.539 |
| 0.4 | ~0.371 | ~0.383 | ~0.508 | ~0.523 |
| 0.6 | ~0.360 | ~0.379 | ~0.484 | ~0.509 |
| 0.8 | ~0.353 | ~0.362 | ~0.483 | ~0.502 |
| 1.0 | ~0.335 | ~0.347 | ~0.472 | ~0.490 |

*(Values approximated from chart; see main-text discussion for the qualitative trend — both MAE and MSE decrease as the ratio of data increases.)*

**Table 10. MAE comparison under different settings.**

| Dataset | Horizon | Pre-Single | Pre-Cross | Post-Single | Post-Cross |
|---|---|---|---|---|---|
| ETTh1 | 96 | 0.407 | 0.414 | 0.421 | 0.398 |
| ETTh1 | 192 | 0.435 | 0.437 | 0.432 | 0.420 |
| ETTh1 | 336 | 0.452 | 0.448 | 0.462 | 0.446 |
| ETTh1 | 720 | 0.461 | 0.479 | 0.499 | 0.481 |
| ETTh2 | 96 | 0.368 | 0.333 | 0.374 | 0.352 |
| ETTh2 | 192 | 0.399 | 0.374 | 0.416 | 0.379 |
| ETTh2 | 336 | 0.435 | 0.411 | 0.446 | 0.418 |
| ETTh2 | 720 | 0.459 | 0.435 | 0.458 | 0.435 |
| ETTm1 | 96 | 0.342 | 0.355 | 0.374 | 0.345 |
| ETTm1 | 192 | 0.391 | 0.359 | 0.399 | 0.370 |
| ETTm1 | 336 | 0.417 | 0.377 | 0.428 | 0.396 |
| ETTm1 | 720 | 0.438 | 0.410 | 0.467 | 0.426 |
| ETTm2 | 96 | 0.253 | 0.248 | 0.264 | 0.260 |
| ETTm2 | 192 | 0.297 | 0.277 | 0.313 | 0.300 |
| ETTm2 | 336 | 0.347 | 0.328 | 0.369 | 0.344 |
| ETTm2 | 720 | 0.392 | 0.382 | 0.402 | 0.396 |
| Weather | 96 | 0.226 | 0.197 | 0.221 | 0.203 |
| Weather | 192 | 0.264 | 0.231 | 0.254 | 0.247 |
| Weather | 336 | 0.286 | 0.269 | 0.295 | 0.281 |
| Weather | 720 | 0.359 | 0.325 | 0.348 | 0.331 |
| Traffic | 96 | 0.254 | 0.241 | 0.271 | 0.276 |
| Traffic | 192 | 0.274 | 0.282 | 0.279 | 0.290 |
| Traffic | 336 | 0.282 | 0.288 | 0.277 | 0.295 |
| Traffic | 720 | 0.311 | 0.302 | 0.300 | 0.310 |
| Exchange | 96 | 0.225 | 0.213 | 0.231 | 0.202 |
| Exchange | 192 | 0.312 | 0.294 | 0.325 | 0.296 |
| Exchange | 336 | 0.415 | 0.393 | 0.432 | 0.410 |
| Exchange | 720 | 0.686 | 0.655 | 0.718 | 0.698 |
| Covid | 96 | 0.044 | 0.041 | 0.046 | 0.041 |
| Covid | 192 | 0.049 | 0.045 | 0.052 | 0.048 |
| Covid | 336 | 0.058 | 0.051 | 0.060 | 0.056 |
| Covid | 720 | 0.061 | 0.057 | 0.064 | 0.059 |
| ECL | 96 | 0.233 | 0.228 | 0.237 | 0.239 |
| ECL | 192 | 0.259 | 0.253 | 0.251 | 0.254 |
| ECL | 336 | 0.274 | 0.280 | 0.267 | 0.269 |
| ECL | 720 | 0.303 | 0.311 | 0.298 | 0.298 |
| NN | 96 | 0.613 | 0.584 | 0.641 | 0.622 |
| NN | 192 | 0.622 | 0.601 | 0.650 | 0.642 |
| NN | 336 | 0.640 | 0.623 | 0.677 | 0.663 |
| NN | 720 | 0.691 | 0.659 | 0.723 | 0.709 |

**Table 11. MSE comparison under different settings.**

| Dataset | Horizon | Pre-Single | Pre-Cross | Post-Single | Post-Cross |
|---|---|---|---|---|---|
| ETTh1 | 96 | 0.404 | 0.412 | 0.420 | 0.377 |
| ETTh1 | 192 | 0.435 | 0.439 | 0.455 | 0.416 |
| ETTh1 | 336 | 0.472 | 0.455 | 0.488 | 0.444 |
| ETTh1 | 720 | 0.485 | 0.481 | 0.566 | 0.488 |
| ETTh2 | 96 | 0.303 | 0.279 | 0.307 | 0.283 |
| ETTh2 | 192 | 0.361 | 0.347 | 0.375 | 0.354 |
| ETTh2 | 336 | 0.396 | 0.372 | 0.409 | 0.389 |
| ETTh2 | 720 | 0.425 | 0.395 | 0.425 | 0.403 |
| ETTm1 | 96 | 0.322 | 0.291 | 0.336 | 0.290 |
| ETTm1 | 192 | 0.355 | 0.332 | 0.363 | 0.331 |
| ETTm1 | 336 | 0.386 | 0.361 | 0.392 | 0.369 |
| ETTm1 | 720 | 0.454 | 0.426 | 0.449 | 0.427 |
| ETTm2 | 96 | 0.171 | 0.165 | 0.179 | 0.169 |
| ETTm2 | 192 | 0.244 | 0.231 | 0.254 | 0.226 |
| ETTm2 | 336 | 0.310 | 0.274 | 0.327 | 0.288 |
| ETTm2 | 720 | 0.371 | 0.339 | 0.388 | 0.377 |
| Weather | 96 | 0.158 | 0.151 | 0.161 | 0.147 |
| Weather | 192 | 0.209 | 0.193 | 0.195 | 0.185 |
| Weather | 336 | 0.266 | 0.244 | 0.262 | 0.248 |
| Weather | 720 | 0.325 | 0.311 | 0.335 | 0.322 |
| Traffic | 96 | 0.376 | 0.359 | 0.385 | 0.391 |
| Traffic | 192 | 0.391 | 0.403 | 0.404 | 0.413 |
| Traffic | 336 | 0.401 | 0.412 | 0.406 | 0.418 |
| Traffic | 720 | 0.443 | 0.429 | 0.443 | 0.451 |
| Exchange | 96 | 0.084 | 0.080 | 0.099 | 0.085 |
| Exchange | 192 | 0.185 | 0.172 | 0.201 | 0.156 |
| Exchange | 336 | 0.368 | 0.321 | 0.379 | 0.327 |
| Exchange | 720 | 0.829 | 0.754 | 1.010 | 0.969 |
| Covid | 96 | 1.032 | 1.011 | 1.057 | 1.023 |
| Covid | 192 | 1.355 | 1.246 | 1.343 | 1.215 |
| Covid | 336 | 1.689 | 1.318 | 1.657 | 1.518 |
| Covid | 720 | 2.021 | 1.955 | 2.103 | 1.986 |
| ECL | 96 | 0.135 | 0.129 | 0.139 | 0.139 |
| ECL | 192 | 0.148 | 0.142 | 0.155 | 0.156 |
| ECL | 336 | 0.158 | 0.166 | 0.170 | 0.171 |
| ECL | 720 | 0.221 | 0.234 | 0.207 | 0.208 |
| NN | 96 | 0.807 | 0.754 | 0.816 | 0.811 |
| NN | 192 | 0.824 | 0.786 | 0.833 | 0.829 |
| NN | 336 | 0.818 | 0.799 | 0.894 | 0.854 |
| NN | 720 | 0.921 | 0.877 | 1.016 | 0.965 |

### G.3. Impact of Model Completeness

To examine the effect of model completeness, we compare a full LLM with a truncated variant that retains only the first 50% of layers. Both models are trained on the same data under identical settings and evaluated on in-domain and out-of-domain test sets (Fig. 15). The results indicate that truncating the model degrades performance, leading to higher MSE across evaluation scenarios (for all three backbones tested: GPT-2, Qwen-3 0.6B, Qwen-3 1.7B, and under both Pre-align and Post-align, and both In-domain and Out-of-domain settings, Truncated MSE > Original MSE).

### G.4. Effect of LLM Backbone and Prompt

**Table 12. Comparison of average MSE and token ratios across different LLM backbones under w/ prompt or w/o prompt.**

#### LLM4TSF(Pre-align)

| LLM | In-Domain w/ Prompt MSE | Ratio(%) | In-Domain w/o Prompt MSE | Ratio(%) | Out-of-Domain w/ Prompt MSE | Ratio(%) | Out-of-Domain w/o Prompt MSE | Ratio(%) |
|---|---|---|---|---|---|---|---|---|
| GPT-2 | 0.471 | 46.7 | 0.488↑ | 41.5↓ | 0.524 | 72.6 | 0.673↑ | 37.9↓ |
| Qwen-3 0.6B | 0.485 | 48.2 | 0.495↑ | 42.2↓ | 0.541 | 70.9 | 0.726↑ | 40.6↓ |
| Qwen-3 1.7B | 0.477 | 45.9 | 0.502↑ | 42.9↓ | 0.529 | 74.6 | 0.679↑ | 35.5↓ |

#### LLM4TSF(Post-align)

| LLM | In-Domain w/ Prompt MSE | Ratio(%) | In-Domain w/o Prompt MSE | Ratio(%) | Out-of-Domain w/ Prompt MSE | Ratio(%) | Out-of-Domain w/o Prompt MSE | Ratio(%) |
|---|---|---|---|---|---|---|---|---|
| GPT-2 | 0.491 | 53.3 | 0.511↑ | 47.7↓ | 0.548 | 76.6 | 0.626↑ | 38.5↓ |
| Qwen-3 0.6B | 0.477 | 55.6 | 0.527↑ | 51.3↓ | 0.525 | 73.9 | 0.619↑ | 34.9↓ |
| Qwen-3 1.7B | 0.484 | 52.7 | 0.535↑ | 48.6↓ | 0.541 | 77.3 | 0.685↑ | 28.8↓ |

*(↑ indicates MSE increases without prompt; ↓ indicates token-passing ratio decreases without prompt.)*

### G.5. Baseline Results in Out-of-Domain Tests

To assess the out-of-domain generalization of the two alignment strategies after cross-dataset training, we evaluate LLM4TSF (Pre-align) and LLM4TSF (Post-align) on seven unseen datasets, and compare them with three large-scale TS foundation models trained from scratch, namely Chronos, UniTS, and Moirai. All methods are evaluated under a zero-shot setting, with model configurations and hyperparameters adopted from the original implementations. We further include two LLM-based TSF models, UniTime and TimeLLM, trained using single-dataset few-shot learning with only 5% of the training data, as additional baselines (Tables 13 & 14).

**Table 13. MAE of baseline out-of-domain test performance.**

| Dataset | Horizon | Chronos | UniTS | MOIRAI | UniTime | TimeLLM |
|---|---|---|---|---|---|---|
| Wind | 96 | 0.696 | 0.755 | 0.640 | 0.685 | 0.664 |
| Wind | 192 | 0.767 | 0.823 | 0.722 | 0.786 | 0.767 |
| Wind | 336 | 0.848 | 0.881 | 0.809 | 0.878 | 0.862 |
| Wind | 720 | 0.934 | 0.945 | 0.866 | 0.953 | 0.945 |
| Solar | 96 | 0.327 | 0.611 | 0.477 | 0.281 | 0.313 |
| Solar | 192 | 0.339 | 0.655 | 0.526 | 0.270 | 0.377 |
| Solar | 336 | 0.342 | 0.679 | 0.554 | 0.284 | 0.395 |
| Solar | 720 | 0.358 | 0.753 | 0.597 | 0.278 | 0.411 |
| AQShunyi | 96 | 0.491 | 0.509 | 0.460 | 0.546 | 0.530 |
| AQShunyi | 192 | 0.522 | 0.538 | 0.475 | 0.578 | 0.551 |
| AQShunyi | 336 | 0.537 | 0.577 | 0.497 | 0.572 | 0.565 |
| AQShunyi | 720 | 0.565 | 0.594 | 0.563 | 0.592 | 0.584 |
| CzenLan | 96 | 0.246 | 0.487 | 0.477 | 0.377 | 0.318 |
| CzenLan | 192 | 0.277 | 0.523 | 0.515 | 0.397 | 0.346 |
| CzenLan | 336 | 0.312 | 0.566 | 0.573 | 0.403 | 0.354 |
| CzenLan | 720 | 0.388 | 0.638 | 0.622 | 0.434 | 0.399 |
| ZafNoo | 96 | 0.399 | 0.553 | 0.404 | 0.603 | 0.485 |
| ZafNoo | 192 | 0.437 | 0.571 | 0.452 | 0.661 | 0.479 |
| ZafNoo | 336 | 0.478 | 0.604 | 0.481 | 0.691 | 0.565 |
| ZafNoo | 720 | 0.507 | 0.669 | 0.514 | 0.724 | 0.577 |
| NASDAQ | 96 | 0.494 | 0.769 | 0.577 | 0.614 | 0.503 |
| NASDAQ | 192 | 0.623 | 0.811 | 0.653 | 0.668 | 0.638 |
| NASDAQ | 336 | 0.744 | 0.853 | 0.786 | 0.719 | 0.727 |
| NASDAQ | 720 | 0.786 | 0.860 | 0.813 | 0.885 | 0.822 |
| PEMS | 96 | 0.424 | 0.839 | 0.255 | 0.356 | 0.339 |
| PEMS | 192 | 0.486 | 0.854 | 0.271 | 0.364 | 0.375 |
| PEMS | 336 | 0.501 | 0.889 | 0.288 | 0.389 | 0.382 |
| PEMS | 720 | 0.597 | 0.916 | 0.304 | 0.418 | 0.419 |

**Table 14. MSE of baseline out-of-domain test performance.**

| Dataset | Horizon | Chronos | UniTS | MOIRAI | UniTime | TimeLLM |
|---|---|---|---|---|---|---|
| Wind | 96 | 1.250 | 1.038 | 0.963 | 1.022 | 0.981 |
| Wind | 192 | 1.357 | 1.224 | 1.199 | 1.241 | 1.201 |
| Wind | 336 | 1.428 | 1.516 | 1.268 | 1.482 | 1.444 |
| Wind | 720 | 1.653 | 1.653 | 1.513 | 1.688 | 1.658 |
| Solar | 96 | 0.418 | 0.779 | 0.858 | 0.216 | 0.402 |
| Solar | 192 | 0.403 | 0.822 | 0.913 | 0.209 | 0.518 |
| Solar | 336 | 0.425 | 0.913 | 0.977 | 0.228 | 0.655 |
| Solar | 720 | 0.488 | 0.968 | 0.995 | 0.220 | 0.733 |
| AQShunyi | 96 | 0.733 | 0.855 | 0.607 | 0.868 | 0.788 |
| AQShunyi | 192 | 0.779 | 0.874 | 0.622 | 0.912 | 0.853 |
| AQShunyi | 336 | 0.850 | 0.902 | 0.685 | 0.893 | 0.876 |
| AQShunyi | 720 | 0.871 | 0.928 | 0.759 | 0.945 | 0.920 |
| CzenLan | 96 | 0.249 | 0.649 | 0.629 | 0.359 | 0.263 |
| CzenLan | 192 | 0.271 | 0.711 | 0.644 | 0.396 | 0.308 |
| CzenLan | 336 | 0.308 | 0.768 | 0.671 | 0.399 | 0.318 |
| CzenLan | 720 | 0.363 | 0.825 | 0.695 | 0.450 | 0.385 |
| ZafNoo | 96 | 0.475 | 0.585 | 0.455 | 0.679 | 0.536 |
| ZafNoo | 192 | 0.511 | 0.655 | 0.516 | 0.790 | 0.530 |
| ZafNoo | 336 | 0.560 | 0.694 | 0.579 | 0.853 | 0.645 |
| ZafNoo | 720 | 0.654 | 0.736 | 0.623 | 0.891 | 0.663 |
| NASDAQ | 96 | 0.506 | 0.954 | 0.714 | 0.833 | 0.655 |
| NASDAQ | 192 | 0.569 | 1.036 | 0.968 | 1.016 | 0.926 |
| NASDAQ | 336 | 1.112 | 1.255 | 1.253 | 1.188 | 1.033 |
| NASDAQ | 720 | 1.305 | 1.236 | 1.333 | 1.452 | 1.317 |
| PEMS | 96 | 0.485 | 1.094 | 0.159 | 0.349 | 0.337 |
| PEMS | 192 | 0.622 | 1.186 | 0.197 | 0.413 | 0.425 |
| PEMS | 336 | 0.765 | 1.455 | 0.251 | 0.453 | 0.444 |
| PEMS | 720 | 0.872 | 1.476 | 0.365 | 0.461 | 0.456 |

### G.6. Impact of Statistical Properties

In addition to shifting and transition, we further analyze how variations in stationarity, seasonality, and trend affect the performance of different models. We observe that stationarity plays a non-negligible role in forecasting difficulty: as the degree of stationarity decreases, prediction errors consistently increase. However, under varying stationarity levels, the performance gap between models with and without pre-training, as well as those with and without LLM components, remains relatively small, indicating no significant advantage for either strategy in this regime. Moreover, our results suggest that changes in seasonality strength and trend magnitude do not fundamentally alter the overall forecasting difficulty, and the relative performance of different models remains largely stable across these settings (Fig. 16).

Fig. 17 shows that when using LLMs w/ pre-training, the distribution of samples passed through the LLM is insensitive to variations in stationarity, seasonality, and trend, exhibiting a relatively uniform pattern.

Fig. 18 shows that under the LLM w/ pre-training setting, the pass distribution remains uniform with respect to these properties; however, due to the randomly initialized LLM under the pre-alignment scheme, the proportion of skipped samples is higher than that of passed samples.

---

## Appendix H. Synthetic TS Generation

To isolate the effect of individual temporal properties, we independently construct synthetic TS using property-specific generative operators. Each operator controls a particular temporal characteristic while preserving intrinsic structure, enabling systematic analysis of forecasting difficulty. For synthetic data generation, we construct 100 time series for each attribute, with each series containing 20,000 observations. We adopt a standard dataset splitting protocol for training, validation, and testing. The forecasting setup uses an input length of 512 time steps to predict the next 192 horizons. To ensure that the effect of each attribute is examined in isolation and to avoid confounding factors, we strictly separate the synthetic datasets corresponding to different attributes.

**Shifting Synthesis.** Shifting describes gradual and continuous distributional drift over time. We model shifting as a time-dependent transformation applied to an underlying latent temporal structure (He et al., 2023). Let v(t) denote a latent oscillatory process. A shifted TS is defined as x_t = S_s(v(t)), where S_s(·) denotes a shifting operator parameterized by strength s. The operator induces smooth temporal drift through joint modulation of phase, amplitude, and noise statistics, causing the marginal distribution of x_t to vary gradually with time. Larger values of s correspond to stronger and more complex shifting behavior.

**Stationarity Synthesis.** Stationarity describes whether the statistical properties of a TS remain invariant over time. We synthesize sequences with varying degrees of stationarity by applying time-dependent distributional transformations (Liu et al., 2022a). Let v(t) be a stationary latent process. The generated TS is defined as x_t = σ_s(t)·v(t) + μ_s(t), where μ_s(t) and σ_s(t) denote time-varying mean and scale functions. Increasing s induces progressively stronger departures from stationarity, while preserving local temporal regularities in v(t).

**Transition Synthesis.** Transition characterizes the complexity of temporal dependency structures governing state evolution. We construct transition-dominated sequences by composing the TS from latent regimes with structured switching behavior (Painblanc et al., 2023). Let {π_k}^K_(k=1) denote a finite set of latent temporal patterns. The generated sequence is given by x_t = π_(z_t)(t), where z_t is a latent regime index evolving according to a transition operator z_t ∼ T_s(z_(1:t−1)). Here, T_s(·) denotes a transition mechanism whose effective dependency order increases with s. As s grows, transitions become increasingly context-dependent, requiring longer temporal history to infer future regimes.

**Seasonality Synthesis.** Seasonality reflects recurring temporal patterns across one or multiple time scales. We generate seasonal TS by modulating periodic structures with time-varying amplitude and phase (Heidrich et al., 2023). Let P(t) denote a collection of periodic basis functions. A seasonal sequence is defined as x_t = A_s(t)·P(t + φ_s(t)), where A_s(t) and φ_s(t) denote amplitude and phase modulation functions, respectively. The parameter s controls the strength and complexity of seasonal variation, allowing a smooth transition from simple stationary periodicity to multi-scale and non-aligned seasonal patterns.

**Trend Synthesis.** Trend captures long-term directional movement that is not necessarily governed by a globally extrapolatable function (Lin et al., 2021). We construct trend-dominated sequences by composing bounded temporal patterns with structured trend components. Let v(t) denote a bounded latent pattern. A trend-augmented TS is given by x_t = v(t) + g_s(t), where g_s(t) denotes a trend function whose functional form and smoothness vary with s. Larger values of s correspond to more complex and non-linear trend behavior, yielding increasing difficulty for parametric extrapolation methods.

Across all properties, the strength parameter s controls temporal complexity while preserving underlying structure. This design ensures that forecasting difficulty increases in a controlled and interpretable manner, favoring models capable of capturing long-range dependencies and adaptive temporal representations. Five types of synthetic TS generated by controlling different statistical properties are illustrated in Fig. 19.

---

## Appendix I. Router Mechanism

### I.1. Gumbel-Softmax and STE

For each token, a routing module generates a pair of logits z = [z₁, z₂], representing the routing preferences over two possible paths. To obtain a discrete routing decision, we employ the Gumbel-Max trick (Jang et al., 2017), where independent Gumbel noise variables g_i ∼ Gumbel(0, 1) are added to the logits, and the routing outcome is sampled as:

y_hard = one-hot(argmax_i(z_i + g_i)).

However, the argmax(·) operation is non-differentiable, which prevents gradients from propagating through the routing decision. To overcome this limitation, we adopt the Gumbel-Softmax relaxation to obtain a continuous and differentiable approximation of the discrete routing variable:

y_i = exp((z_i + g_i)/τ) / Σ_j exp((z_j + g_j)/τ),

where τ is a temperature parameter that controls the smoothness of the resulting distribution. As τ decreases, the output distribution becomes increasingly peaked, approaching a one-hot representation.

In practice, we further integrate the Gumbel-Softmax mechanism with the Straight-Through Estimator (STE) (Bengio et al., 2013). During the forward pass, the discrete routing decision y_hard is used to perform token-level path selection, while in the backward pass, gradients are propagated through the continuous approximation y_soft. This is achieved by constructing the final routing variable as:

y = y_hard − detach(y_soft) + y_soft.

This design enables effective discrete routing at inference time while maintaining differentiability during training.

### I.2. Algorithm: Token-Level Routing

**Table 15. Algorithm: Token-Level Routing**

**Require:** Dataset D, routing module parameters θ, temperature τ
**Output:** Differentiable token-level routing decisions y

1. Initialize routing module parameters θ
2. For each training iteration:
   1. Sample a token of TS segments X ∼ D
   2. For each token t in X:
      1. Compute routing logits z_t = [z_(t,1), z_(t,2)] using the routing module
      2. Sample Gumbel noise g_i ∼ Gumbel(0, 1) for each routing option
      3. Obtain discrete routing decision using Gumbel-Max: y^hard_t ← one-hot(argmax_i(z_(t,i) + g_i))
      4. Compute continuous routing weights via Gumbel-Softmax relaxation: y^soft_(t,i) ← exp((z_(t,i) + g_i)/τ) / Σ_j exp((z_(t,j) + g_j)/τ)
      5. Apply Straight-Through Estimator (STE): y_t ← y^hard_t − detach(y^soft_t) + y^soft_t
      6. Route token t according to y_t
   3. Backpropagate gradients through y_soft and update θ
3. **Return** learned routing mechanism

---

## Appendix J. Reproducibility Details

To ensure that the results and conclusions can be reproduced accurately, we provide the exact training configurations used in our experiments (Table 16). Additional details of the routing analysis are provided in Table 17.

**Table 16. Training Configuration**

| Hyperparameter | Value |
|---|---|
| Framework | HuggingFace Transformers |
| Distributed Training | DeepSpeed, Accelerate |
| GPU | 4× NVIDIA A100 40GB / H100 80GB |
| Random Seed | Fixed 2026 |
| Optimizer | AdamW |
| Learning Rate | 1 × 10⁻⁴ |
| Adam β1 | 0.9 |
| Adam β2 | 0.95 |
| Adam ε | 1 × 10⁻⁶ |
| Weight Decay | 0.01 |
| LR Scheduler | Cosine decay |
| Warmup Ratio | 0 |
| Precision | bf16 |
| DeepSpeed Stage | ZeRO Stage 2 |
| Micro Batch Size per GPU | 64 |
| Gradient Accumulation Steps | 1 |
| Gradient Clipping | Default |

**Table 17. Routing Analysis Configuration**

| Routing Parameter | Value |
|---|---|
| Number of Routing Paths | 2 |
| Routing Module Output | Logits z = [z₁, z₂] |
| Gumbel Noise Distribution | Gumbel(0, 1) |
| Temperature τ (init) | 1.0 |
| Temperature τ (final) | 0.1 |
| Discrete Sampling | Gumbel-Max for y_hard |
| Straight-Through Estimator | Enabled |
| Forward Pass Routing | Hard one-hot y_hard |
| Backward Pass Gradient | Soft y_soft |
| Inference-time Routing | argmax(z) |
| Routing Regularization | Entropy penalty on y_soft |
| Entropy Weight | 1 × 10⁻³ |
| Target Routing Ratio | 0.5 |
| Ratio Penalty Weight | 1 × 10⁻² |
| Router Optimizer | AdamW |
| Router Learning Rate | 3 × 10⁻⁴ |
| Weight Decay | 0.01 |
| Gradient Clipping | 1.0 |

---

*End of document.*
