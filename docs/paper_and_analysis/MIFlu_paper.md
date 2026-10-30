# MIFlu: Large Language Model-Based Multimodal Influenza Forecasting Scheme

**Authors:** Jaeuk Moon (Member, IEEE), Jonghwa Shim, Eunbeen Kim, and Eenjun Hwang (Member, IEEE)

*IEEE Journal of Biomedical and Health Informatics, Vol. 29, No. 10, October 2025, pp. 7790–7801*
DOI: 10.1109/JBHI.2025.3561214

Received 18 November 2024; revised 21 March 2025 and 27 March 2025; accepted 12 April 2025. Date of publication 15 April 2025; date of current version 7 October 2025. This work was supported by NRF (National Research Foundation of Korea) under Grant RS-2023-00252257 and in part by the NRF Korean Government (MSIT) under Grant RS-2024-00397293. (Corresponding author: Eenjun Hwang.)

The authors are with the School of Electrical Engineering, Korea University, Seoul 02841, South Korea (e-mail: jaewookmo@korea.ac.kr; indexlibrorum3822@korea.ac.kr; gichanac@korea.ac.kr; ehwang04@korea.ac.kr).

© 2025 IEEE. Personal use is permitted, but republication/redistribution requires IEEE permission.

---

## Abstract

In order to minimize the impact of influenza on public health, accurate early forecasting is essential. Various deep-learning-based models have been proposed to predict future influenza occurrences by capturing temporal/regional patterns from past occurrence time-series data. However, the prediction performance of these unimodal approaches is limited because they extract knowledge only from collected data, and users cannot input contextual information and domain knowledge to them. Recently, large language models (LLMs) have demonstrated the potential to improve prediction accuracy by linking contextual text information to time-series predictions. In this paper, we propose MIFlu, a multimodal influenza forecasting scheme that can fuse contextual text information to time-series influenza occurrences using two LLMs. It first extracts text embeddings from the user's text prompts that contain contextual information using a text-embedding LLM. Then, MIFlu fuses the text embeddings and time-series embeddings and uses the fused embeddings to predict future occurrences using a forecasting LLM. In extensive experiments using public national/regional influenza datasets, MIFlu outperforms other predictive models, improving prediction performance by up to 26.2% compared to state-of-the-art models. We also analyze the effect of various textual input embedders, hyperparameters, and the amount of training data on forecasting accuracy.

**Index Terms:** Artificial neural network, deep learning, ILI prediction, large language models, multimodal forecasting.

---

## I. Introduction

Infectious diseases transmitted through the respiratory tract have severe economic, social, and health impacts on society. The recent coronavirus disease (COVID-19) outbreak has clearly demonstrated the widespread negative consequences of infectious diseases, such as massive mortality and global economic disruption. Influenza is also a major public health challenge, with the World Health Organization (WHO) estimating that influenza causes 3 to 5 million severe symptomatic illnesses and 290,000 to 650,000 deaths every year [1]. Early forecasting of influenza outbreaks can reduce the severity of impacts by allowing time for countermeasures such as vaccine manufacturing, implementation of prevention policies, and introduction of quarantine protocols before an outbreak occurs [2].

To date, influenza forecasting has typically relied on multivariate time-series forecasting approaches that predict future influenza occurrences in multiple regions/variables using only past occurrence data for those regions/variables. Here, exogenous data such as internet search or weather data are not utilized because of their limited availability and reliability [3]–[5]. To this end, researchers have attempted to capture temporal patterns and interrelationships in influenza occurrence data across different regions/variables (i.e., regional patterns) using deep-learning-based models [3]–[5]. For example, graph neural networks (GNNs), which consider each region/variable as a graph node and represent regional patterns as an adjacency matrix, have been used for influenza forecasting [3], [4]. More recently, self-attention mechanisms, which assign higher weights to relatively important components in the input data, have replaced GNNs for the modeling of regional patterns [5].

Domain knowledge such as disease characteristics, health policy changes, and task instructions (e.g., user prediction instructions) can be effectively used for influenza forecasting. Nevertheless, conventional forecasting methods are very limited in leveraging this contextual information because they are based on unimodal models that capture time-series temporal/regional patterns in historical influenza occurrences. To address this problem, an effective way to fuse data from different modalities, such as contextual text information and historical time-series data, is needed. One option for this is large language models (LLM), which have been extensively studied in various fields such as natural language processing [6], computer vision [7], and time-series tasks [8], [9]. In particular, autoregressive LLM models (e.g., GPT and LLaMA) based on transformer decoders can be used for predictions by pre-training the LLM via causal language modeling to predict masked words that appear after the input text, thus making them suitable for time-series forecasting [8], [9]. Pre-trained LLMs can also adapt to new tasks with only a few data points based on their pre-trained background knowledge and have the ability to encode the meaning/sequential patterns of text as latent vectors. Therefore, contextual information can be expressed as text and incorporated into time-series forecasting.

Based on this observation, this paper proposes MIFlu, a multimodal influenza forecasting scheme that can produce more accurate predictions by fusing contextual information expressed in text format with time-series influenza occurrence data using two LLMs. MIFlu consists of three components:

1. A **textual input embedder** that outputs text embeddings using a tokenizer and text-embedding LLM for text prompts containing forecasting instructions, statistical knowledge of data, dataset description, and domain knowledge from experts.
2. A **time-series input embedder** that normalizes time-series influenza occurrence data, divides it into patches, and outputs time-series input embeddings.
3. A **forecasting LLM** that predicts future influenza occurrences based on the fusion of the two embeddings by fine-tuning only a few LLM parameters and additional parameters using a parameter-efficient fine-tuning (PEFT) technique.

The forecasting accuracy of MIFlu was compared with comparative models using national/regional influenza forecasting tasks, and its performance was analyzed with changes to the textual input embedder, hyperparameters, text prompt, and amount of training data. Finally, an ablation study investigates whether each component of MIFlu is essential.

### Main contributions

- A multimodal influenza forecasting model that fuses textual domain knowledge and time-series occurrence data using two LLMs is proposed — to the best of the authors' knowledge, the first study to employ multimodal forecasting based on LLM for influenza forecasting.
- Various experiments demonstrate that the proposed model outperforms other state-of-the-art (SOTA) models in national/regional influenza forecasting tasks.
- A prompt template is presented that provides contextual information to the forecasting LLM to enrich its interpretation of time-series influenza occurrences.

**Paper organization:** Section II presents related work; Section III provides preliminaries; Section IV describes the proposed model; Section V describes the experimental settings; Section VI summarizes the results; Section VII concludes the paper and discusses limitations and future work.

---

## II. Related Work

Regional influenza forecasting predicts future influenza occurrences in multiple regions using only historical occurrence data from those regions. Exogenous data such as internet search (e.g., Google Trends) or weather data are not utilized because of their limited availability and reliability [3]–[5]. Due to the nature of infectious diseases, which spread rapidly across regions over time, researchers have focused on jointly capturing temporal and regional patterns of influenza outbreaks [10]. To achieve this, deep-learning models such as recurrent neural networks (RNNs) and GNNs have been widely used.

RNNs and their variants, such as long short-term memory (LSTM) and gated recurrent units, are specialized for capturing temporal patterns. For example, Wu et al. [4] utilized an RNN to learn temporal patterns in specific regions and adopted a convolutional neural network (CNN) to fuse temporal patterns in multiple regions to capture regional patterns, adding residual connections between time sequences to avoid overfitting. In contrast, GNNs consider each region as a graph node and can effectively represent regional patterns with an adjacency matrix. Deng et al. [3] first captured the temporal patterns of nodes using a temporal CNN and utilized these patterns in a node feature matrix, then used an RNN to extract features from each node to construct an adjacency matrix representing regional patterns; the node feature matrix and adjacency matrix were incorporated using a GNN to predict future influenza occurrences.

Self-attention mechanisms can also capture regional patterns by assigning higher weights to relatively important input components. Jung et al. [5], [10] proposed SAIFlu-Net, which uses LSTM to obtain temporal patterns for each region as query/key inputs, then applies self-attention to calculate regional patterns for regional influenza forecasting; SAIFlu-Net was shown to be superior to previous models including CNNRNN and Cola-GNN.

Transformers, introduced by Vaswani et al. [11], have recently been used for multivariate time-series forecasting. The transformer architecture relies heavily on self-attention with an encoder (understands input data) and decoder (generates output based on encoder knowledge), and is suitable for capturing long-term temporal patterns. Researchers have used transformers and variants for long-term forecasting, including national influenza forecasting. Kitaev et al. [12] proposed Reformer, using locality-sensitive hashing for approximate nearest-neighbor search to create a more memory-efficient transformer. Wu et al. [13] modified a transformer into a decomposition forecasting architecture (Autoformer), decomposing the input series into patches and replacing self-attention with an auto-correlation module to capture seasonal/cyclic patterns.

Recently, LLMs based on transformer architectures pretrained on large-scale text databases have shown remarkable NLP performance, prompting attempts to align time-series features with text features. Zhou et al. [9] proved that fine-tuning only the first several layers of pre-trained GPT2 with an added output layer can outperform existing transformer-based models across time-series tasks (long/short-term forecasting, classification, anomaly detection).

These previous approaches are unimodal influenza forecasting models trained solely to predict future values from historical time-series data, and cannot leverage expert domain knowledge or external (mostly textual) information. Fusing multiple modalities is useful for improving epidemic-prediction accuracy. Papagiannopoulou et al. [14] incorporated exogenous data (meteorological, population) via self-attention to capture ILI variation, achieving SOTA regional forecasting accuracy — but represented exogenous information as time-series data, meaning the model cannot be used in countries lacking such exogenous data (input dimensions differ). This limitation can be addressed by enriching ILI information with textual prompts alongside time-series data and using an LLM pre-trained on multimodal data.

---

## III. Preliminaries

### A. Problem Formulation

Influenza forecasting is formulated as a multivariate time-series forecasting task predicting the number of future ILI patients ("ILI" = ILI patient count, for both national and regional forecasting).

- **N** = number of variables
- **L** = number of future weeks to predict
- **T** = time length of the input data
- x<sub>t</sub><sup>i</sup> ∈ ℝ denotes the ILI for the i-th variable at time t
- X<sub>i</sub> = [x<sub>i</sub><sup>1</sup>, …, x<sub>i</sub><sup>T</sup>] ∈ ℝ<sup>T</sup> is the set of ILIs in region i over the past T weeks

**1) National ILI Forecasting:** Predicts not only the ILI for the entire country, but also several sub-indicator variables (national ILI, ILI by age group, ILI adjusted for population size or number of reporting providers; see Table II). Following [9], the goal is to predict ILI for L continuous future weeks based on N variables over a window of the past T weeks, where X<sub>input</sub> ∈ ℝ<sup>N×T</sup> is the input to forecasting model f:

**Equation (1):**

Ŷ = [Ŷ<sub>t+L</sub>, …, Ŷ<sub>t+1</sub>] = f(X<sub>input</sub>) = f(X<sub>t−(T−1)</sub>, …, X<sub>t−1</sub>, X<sub>t</sub>)

$$
\hat{Y} = [\hat{Y}_{t+L}, \dots, \hat{Y}_{t+1}] = f(X_{input}) = f\!\left(
\begin{bmatrix}
x_1^{t-(T-1)} & \cdots & x_1^{t} \\
\vdots & \ddots & \vdots \\
x_N^{t-(T-1)} & \cdots & x_N^{t}
\end{bmatrix}
\right) \tag{1}
$$

**2) Regional ILI Forecasting:** The variables consist only of ILI for N regions. Following [3]–[5], [14], the goal is to forecast the ILI after L weeks in N regions using X<sub>input</sub> as input for f:

**Equation (2):**

$$
\hat{y}^{t+L} = f(X_{input}) \tag{2}
$$

### B. LLM

Most LLMs are based on a transformer relying on self-attention. The transformer structure generally consists of an encoder and a decoder, leading to two main LLM types:

- **Autoencoding models** based on an encoder (e.g., BERT [15]) — widely used where understanding input text is important (word/document classification, sentiment analysis).
- **Autoregressive models** based on a decoder (e.g., GPT [16], LLaMA [17]) — generate text likely to follow the input text, trained on large volumes of unlabeled text via self-supervised learning to predict the next masked word.

This causal-language-modeling predictive ability makes LLMs suitable for time-series forecasting tasks [18].

### C. Parameter Efficient Fine-Tuning

Since LLMs are pre-trained on diverse, large data, fine-tuning is essential for a specific task. However, fine-tuning *all* layers on a small, domain-specific dataset can cause **catastrophic forgetting** — the LLM forgets most pre-trained knowledge during fine-tuning [22].

PEFT [23] addresses this by selectively optimizing essential parameters while leaving others unchanged. Among PEFT techniques, this work uses **low-rank adaptation (LoRA)** [24] for its adaptation performance. LoRA adds lightweight, fully connected layers in parallel to specific pre-trained LLM layers and updates only these added layers.

---

## IV. Proposed Scheme

The overall structure of MIFlu (Fig. 1) consists of three modules: a textual input embedder, a time-series input embedder, and a forecasting LLM.

### Figure 1 — Architecture of the Proposed Scheme (description)

The diagram shows two parallel input branches feeding into a shared Forecasting LLM:

- **Textual input branch (left):** Textual input (a structured prompt containing `[Dataset description]`, `[Input variable description]` with statistics/domain knowledge for variables 1–N, and `[Instruction]`/task information) → **Textual input embedder**, consisting of a **Tokenizer** followed by a frozen **Text-embedding LLM** → produces **Textual input embeddings, h_text** (shown in tan/yellow blocks, of length `len(token)`).
- **Time-series input branch (right):** Time-series input (multiple raw time-series signals) → **Time-series input embedder**, consisting of **Instance norm + Patching** followed by a trainable **Linear embedder** → produces **Time-series input embeddings, h_time** (shown in blue blocks, of length `num(patches)`).
- The two embedding sequences (h_text and h_time) are concatenated and fed into the **Forecasting LLM**, whose internal structure (expanded on the right of the figure) is a stack of ×K transformer blocks, each containing:
  - Positional encoding (PE) added to hidden states
  - **Multi-Head Attention** block: Query (Q), Key (K), Value (V) projections (W_Q, W_K, W_V, shown frozen ❄) each with an added trainable **LoRA** 🔥 adapter path, feeding an **Attention** operation
  - **Add & Norm** (trainable 🔥)
  - **Feed Forward** layer (frozen ❄)
  - **Add & Norm** (trainable 🔥)
- The output of the K transformer blocks (Forecasting embeddings, h_forecast, green blocks) is passed to a trainable **Output projection** layer to produce the final forecast.
- **Legend:** Tan = Textual input embeddings h_text; Blue = Time-series input embeddings h_time; Green = Forecasting embeddings h_forecast; ❄ (snowflake) = Frozen parameters; 🔥 (fire) = Trainable parameters.

### A. Textual Input Embedder

The textual input embedder constructs a text prompt containing contextual information (domain knowledge, task instructions) and encodes it into text embeddings, enabling MIFlu to forecast future ILIs using richer information than unimodal forecasting — e.g., incorporating infectious-disease-expert insight about future ILI patterns or public-health-policy changes. Text prompts also allow real-time updates so the model can quickly adapt to rapid ILI pattern changes (e.g., emergence of new strains, public health interventions, changes in public behavior) [8].

A text prompt template for influenza forecasting was constructed including dataset information, task instructions, and description of input variables, following the template of [18]. The template is shown in **Table I** below (a full example appears in the Appendix, Table X).

#### Table I — Template of an Input Text Prompt

```
[Dataset information]
 <Description of dataset>
 Below (1) to (N) is the information about each feature:
***
[Input variable description]
 (1) <Description of variable 1> + <Statistics: Max, Min> + <Domain
     knowledge from experts/users of variable 1>
 …
 (i) <Description of variable i> + <Statistics: Max, Min> + <Domain
     knowledge from experts/users of variable i>
 …
 (N) <Description of variable N> + <Statistics: Max, Min> + <Domain
     knowledge from experts/users of variable N>
***
[Task instruction]
 Predict the next <L> steps given the previous <T> steps for the
 information attached.
```

The **dataset information** provides essential background (number of variables, dataset domain, period of X<sub>i</sub><sup>train</sup> — training input data of region i). The **input variable description** includes statistics (minimum/maximum of X<sub>i</sub><sup>train</sup>) and domain knowledge from the user, plus the overall trend for X<sub>i</sub><sup>train</sup> and the number of peak timings each year. The **task instruction** section details lead time L and window size T.

The textual input embedder consists of a **tokenizer** and a **text-embedding LLM**. After the prompt is constructed, the text-embedding LLM produces embedding vectors: the text is first tokenized using a pre-trained tokenizer, each token is mapped to a unique numerical ID via a pre-defined dictionary (built during LLM pre-training), and finally the LLM transforms each token into an embedding vector D. The module output is the hidden states of the textual inputs:

$$
h_{text} \in \mathbb{R}^{(len(token)) \times D}
$$

where `len(token)` is the total token length of the converted text, and D ∈ ℝ<sup>d</sup> is the dimension of the LLM's input/output.

### B. Time-Series Input Embedder

Since LLMs are usually pre-trained on text data, time-series ILI data must be converted for use as forecasting-LLM input. An input embedder with three layers is used: **instance normalization**, **patching**, and **linear embedder**.

ILI distribution varies over time; excessive distribution variation can cause overfitting and unstable training. To mitigate distribution shift, **reversible instance normalization** [19] is applied to each variable in X<sub>input</sub>, by subtracting the mean of X<sub>input</sub> and dividing by its standard deviation.

ILI data exhibits temporal patterns over various periods (weeks/months) with a repetitive peak pattern each year. The normalized X<sub>input</sub> is converted into patch-based tokens (incorporating adjacent time steps), which better preserves short-term patterns and reduces LLM computational load. The patch length is L<sub>p</sub>, and the total number of input patches is:

$$
\frac{T - L_p}{S} + 2
$$

where S is the horizontal sliding stride. The output of the instance-normalization and patching layers is:

$$
h_t \in \mathbb{R}^{(num(patches)) \times P}
$$

where `num(patches)` is the number of total patches from X<sub>input</sub>, and P is the patch size. A trainable **linear embedder** projects h_t onto the dimensions `[num(patches), D]` required for the forecasting LLM input. The module output is:

$$
h_{time} \in \mathbb{R}^{(num(patches)) \times D}
$$

### C. Forecasting LLM

The forecasting LLM module concatenates h_time and h_text to create a fused embedding:

$$
h_{fuse} \in \mathbb{R}^{(len(token) + num(patches)) \times D}
$$

used to predict future ILIs. An autoregressive LLM is used as the forecasting model for several reasons:

1. It employs causal language modeling, allowing masked words following the input text to be learned during training [18].
2. It contains multiple transformer decoders, which demonstrate outstanding performance in processing long-term temporal patterns [11]. Long-term forecasting matters because vaccine transportation/distribution, vaccination, policy decisions, and budget allocation are time-consuming.
3. The LLM can adapt to new tasks with small volumes of data via pre-trained knowledge — important for ILI forecasting because data are collected weekly rather than by minute/second [20]. (Weekly patient counts provide only about 520 data points after 10 years of collection, risking data shortage.)

The autoregressive LLM's main components are the **positional encoding (PE)** layer and **transformer blocks** (multi-head attention, layer normalization, feed-forward layers). Following standard technique [9], [21], only PE and layer-normalization layers are typically fine-tuned. However, unlike prior unimodal-LLM time-series studies [9], MIFlu forecasts using h_fuse, a fused text/time-series embedding — so the multi-head attention layer also needs fine-tuning to capture new relationships within the fused embedding. Since multi-head attention and feed-forward layers hold most pre-trained knowledge, fine-tuning them on small-scale ILI data risks catastrophic forgetting [22]. To address this, **LoRA is applied only to the multi-head attention layer**, letting the pre-trained LLM learn new relationships in h_fuse without compromising inference speed.

After the transformer blocks, the forecasting embeddings are obtained autoregressively:

$$
h_{forecast} \in \mathbb{R}^{(num(patches) + len(token)) \times D}
$$

(same dimensions as h_fuse). When the forecasting LLM takes the i-th token h_fuse[i] as input, the forecasting result for h_fuse[i] is h_forecast[i] — i.e., input and output token order is the same. Because the goal is to predict future ILIs after historical ILI input, the token portion is discarded:

$$
h_{forecast}[len(token){:}] \in \mathbb{R}^{(len(token)) \times D} \quad \text{is removed from } h_{forecast} \text{ to form } h_{forecast}' \in \mathbb{R}^{(num(patches)) \times D}
$$

Afterward, h_forecast′ is projected to the final forecasting result — ŷ<sup>t+L</sup> (regional ILI forecasting) or ŷ<sup>t+L</sup>, …, ŷ<sup>t+1</sup> (national ILI forecasting) — using the **output projection**, a linear embedder layer.

---

## V. Experimental Settings

### A. Datasets

Two datasets are used:

- **National-Illness [25]:** Seven variables for national ILIs occurring in the US between 2002 and 2021, including ILI occurrence for ages 0–4, number of outpatient providers, and total national ILI. Widely used to compare long-term ILI forecasting accuracy (lead times L > 24 weeks) of transformer-based models. Following [9], [21], data are split 70:10:20 (train:validation:test).
- **US-Region [25]:** The US Department of Health and Human Services (HHS) divides the US into 10 regions by grouping related states. Contains ILI for those 10 HHS regions from week 40, 1997 to week 18, 2020. Following [14] and prior work [5], data are split 50:10:40.

#### Table II — Descriptive Statistics of the National-Illness Dataset

*(Original table content: descriptive statistics — count, mean, std, min, max, and quartiles — for the seven National-Illness variables. Exact numeric cell values are not machine-extractable from the source PDF table image; see Fig. 2(a) boxen plot below for the visual distribution of each of the seven variables.)*

#### Table III — Descriptive Statistics of the US-Region Dataset

*(Original table content: descriptive statistics for ILI patient counts across the 10 HHS regions plus whole-dataset statistics. Exact numeric cell values are not machine-extractable from the source PDF table image; see Fig. 2(b) boxen plot below for the visual distribution across the 10 regions.)*

#### Figure 2 — Boxen plots for the variables and regions (description)

- **(a) Boxen plot for the National-Illness dataset:** Seven horizontal boxen plots, one per variable (Variable 1–7). Variables 1–2 are measured as "Percentage of ILI patient" (range roughly 0–8%); Variables 3–5 are measured as "ILI patient count" (Variable 3 up to ~25,000; Variable 4 up to ~40,000; Variable 5 up to ~100,000+); Variable 6 is "# of healthcare providers" (roughly 500–3,500); Variable 7 is "ILI patient count" on a much larger scale (up to ~1.8 × 10⁶). All distributions are right-skewed with long tails of high outlier values.
- **(b) Boxen plot for the US-Region dataset:** Ten horizontal boxen plots, one per HHS region (Region 1–10), all measured as "ILI patient count" (roughly 0–30,000). All regions show strongly right-skewed distributions with a dense cluster of low values and a long tail of outliers extending to 15,000–30,000.

### B. Evaluation Metrics

Two metrics are used per task:

- **National ILI forecasting:** Mean Square Error (MSE) and Mean Absolute Error (MAE) [9], [26]–[32]. MSE is sensitive to large errors (suitable for comparing peak-intensity prediction performance); MAE uses overall mean error (evaluates general prediction performance). Each input variable is first normalized to a normal distribution using StandardScaler.

- **Regional ILI forecasting:** Root Mean Square Error (RMSE) and Pearson Correlation Coefficient (PCC) [3]–[5], [10], [14], used after de-normalizing values to the original range. RMSE is more sensitive to large errors than MAE (square root of mean squared error). PCC evaluates whether the model captures the trend of ILI.

**Equation (3) — MSE:**

$$
MSE = \frac{1}{M}\sum_{n=1}^{M}\left(Y_n - \hat{Y}_n\right)^2 \tag{3}
$$

**Equation (4) — MAE:**

$$
MAE = \frac{1}{M}\sum_{n=1}^{M}\left|Y_n - \hat{Y}_n\right| \tag{4}
$$

**Equation (5) — RMSE:**

$$
RMSE = \sqrt{\frac{1}{M}\sum_{n=1}^{M}\left(Y_n - \hat{Y}_n\right)^2} \tag{5}
$$

**Equation (6) — PCC:**

$$
PCC = \frac{\sum_{n=1}^{M}\left(\hat{Y}_n - \overline{\hat{Y}}\right)\left(Y_n - \overline{Y}\right)}{\sqrt{\sum_{n=1}^{M}\left(\hat{Y}_n - \overline{\hat{Y}}\right)^2}\sqrt{\sum_{n=1}^{M}\left(Y_n - \overline{Y}\right)^2}} \tag{6}
$$

where Y<sub>n</sub> and Ŷ<sub>n</sub> are the actual and predicted ILI for M data points, respectively, and $\overline{Y}$ and $\overline{\hat{Y}}$ are the mean values of the actual and predicted ILIs.

### C. Experimental Details

SOTA models proposed for ILI forecasting are used as comparison baselines (**Table IV**, listing comparative models and hyperparameters — settings match [9], [14]). Results for the national and regional ILI forecasting models are taken from [9] and [14], respectively.

- **National ILI forecasting:** long-term forecasting (L ≥ 24).
- **Regional ILI forecasting:** shorter-term forecasting (L ≤ 24) — because regional-level influenza spread is rapid/irregular and inherently volatile, making short-term forecasts more practical for immediate public-health response, whereas national forecasts based on aggregated multi-region data suppress regional fluctuations and focus on long-term seasonal trends.

Three versions of the **ReILIF** model exist for regional ILI forecasting: ReILIF<sub>NoC</sub> (ILI only), ReILIF<sub>TV</sub> (ILI + time-varying exogenous data, e.g., wind/temperature), and ReILIF<sub>TV/S</sub> (static exogenous data, e.g., population/population density). Results for **ReILIF<sub>TV/S</sub>** are presented as the ReILIF representative, since MIFlu uses textual information that is static over time [14].

**MIFlu hyperparameters:**
- Training epochs and learning rate were set empirically (vary by base model).
- Forecasting LLM uses the first **K** layers of the original GPT2 [9]: K = 6 for national ILI forecasting (per [9]); K = 4 for regional ILI forecasting (per Section VI-D results).
- LoRA low-rank dimension **r = 4** (following [36]).
- National ILI forecasting: patch length L<sub>p</sub> = 24, stride S = 2 (per [9]).
- Regional ILI forecasting: L<sub>p</sub> = 4, S = 2 (based on the ratio of T, L<sub>p</sub>, S used in national ILI prediction).
- Textual input embedder: **full GPT2** used, to align pre-trained knowledge with the forecasting LLM (see Section VI-C).
- SOTA LLMs like GPT-4o were not considered, since their structure cannot be modified and they must be trained using only text data with a fixed template.

Forecasting performance is assessed as the mean of **10 repetitions**. Implementation: Python 3.9.18, PyTorch 2.1.0, GeForce RTX 3090.

---

## VI. Experimental Results

### A. National ILI Forecasting

**Table V — MSE and MAE of the Comparative Models for National ILI Forecasting**

| L | Metric | MIFlu | GPT4TS | DLinear | PatchTST | TimesNet | FEDformer | Autoformer | Stationary | ETSformer | LightTS | Informer | Reformer |
|---|--------|-------|--------|---------|----------|----------|-----------|------------|------------|-----------|---------|----------|----------|
| 24 | MSE | **1.542** | 2.063 | 2.215 | **1.319** | 2.317 | 3.228 | 3.483 | 2.294 | 2.527 | 8.313 | 5.764 | 4.400 |
| 24 | MAE | **0.726** | 0.881 | 1.081 | *0.754* | 0.934 | 1.260 | 1.287 | 0.945 | 1.020 | 2.144 | 1.677 | 1.382 |
| 36 | MSE | **1.422** | 1.868 | 1.963 | *1.430* | 1.972 | 2.679 | 3.103 | 1.825 | 2.615 | 6.631 | 4.755 | 4.783 |
| 36 | MAE | **0.779** | 0.892 | 0.963 | *0.834* | 0.920 | 1.080 | 1.148 | 0.848 | 1.007 | 1.902 | 1.467 | 1.448 |
| 48 | MSE | **1.414** | 1.790 | 2.130 | *1.553* | 2.238 | 2.622 | 2.669 | 2.010 | 2.359 | 7.299 | 4.763 | 4.832 |
| 48 | MAE | **0.757** | 0.884 | 1.024 | *0.815* | 0.940 | 1.078 | 1.085 | 0.900 | 0.972 | 1.982 | 1.469 | 1.465 |
| 60 | MSE | **1.364** | 1.979 | 2.368 | *1.470* | 2.027 | 2.857 | 2.770 | 2.178 | 2.487 | 7.283 | 5.264 | 4.882 |
| 60 | MAE | **0.719** | 0.957 | 1.096 | *0.788* | 0.928 | 1.157 | 1.125 | 0.963 | 1.016 | 1.985 | 1.564 | 1.483 |

*(Bold = best; italic = second-best, per the paper's bold/underline convention.)*

MIFlu outperforms the other models in all cases except MSE at L = 24 (where PatchTST is best). Because national ILI forecasting generally involves long-term predictions, most previous models rely on transformer architectures that effectively capture long-term temporal patterns. However, recent non-transformer models (TimesNet, DLinear) still perform well. Except for PatchTST, GPT4TS outperforms all other compared models due to its pre-trained knowledge of a large volume of textual data; PatchTST maximizes transformer performance and achieves second-best on average MSE/MAE. MIFlu performs well because it incorporates the user's prior knowledge via the textual input embedder and LoRA fine-tuning, improving on GPT2's forecasting performance.

**Figure 3 — Comparison of average forecasting performance for L = 24, 36, 48, 60 (description):** A grouped bar chart with two panels (MSE and MAE evaluation metrics) on the x-axis, and average "Value" on the y-axis (0–7+ for MSE, roughly 0–2 for MAE), comparing all 12 models (MIFlu, GPT4TS, DLinear, PatchTST, TimesNet, FEDformer, Autoformer, Stationary, ETSformer, LightTS, Informer, Reformer) as colored bars. LightTS shows by far the tallest MSE bar (~7.4); MIFlu and PatchTST show the shortest bars in both panels, confirming MIFlu outperforms all comparative models on average across all L.

### B. Regional ILI Forecasting

**Table VI — RMSE/PCC of the Comparative Models for Regional ILI Forecasting**

| L | MIFlu | GPT4TS | ReILIF | TFT | SAIFlu-Net | Cola-GNN | STNN | CNNRNN |
|---|-------|--------|--------|-----|------------|----------|------|--------|
| 2 | **771.9 / 0.937** | 998.1 / 0.915 | 1354.8 / 0.876 | 1247.2 / 0.867 | 1016.2 / 0.908 | *1006.1 / 0.920* | 1259.0 / 0.885 | 1130.4 / 0.902 |
| 3 | **963.4 / 0.883** | 1306.0 / *0.850* | 1555.2 / 0.819 | 1444.6 / 0.816 | *1306.0* / 0.847 | 1431.3 / 0.832 | 1576.5 / 0.820 | 1492.6 / 0.818 |
| 5 | **1331.49 / 0.779** | *1571.5 / 0.761* | 2293.7 / 0.707 | 1675.8 / 0.738 | 1681.8 / 0.728 | 1737.4 / *0.750* | 1934.5 / 0.677 | 1844.0 / 0.727 |
| 10 | **1893.4 / 0.719** | 1992.4 / 0.685 | *1955.4 / 0.701* | 2167.1 / 0.601 | 2050.0 / 0.608 | 2289.9 / 0.494 | 2404.6 / 0.255 | 2382.7 / 0.271 |
| 13 | **1943.8 / 0.701** | 2047.1 / 0.682 | *1996.4 / 0.685* | 2388.4 / 0.530 | 2140.0 / 0.599 | 2448.5 / 0.448 | 2339.1 / 0.259 | 2465.5 / 0.198 |
| 15 | **1923.8 / 0.678** | *2213.0 / 0.651* | 2512.9 / 0.538 | 2518.2 / 0.479 | 2330.7 / 0.531 | 2437.9 / 0.446 | 2356.9 / 0.318 | 2482.5 / 0.147 |
| 20 | **1920.8 / 0.689** | 2077.3 / *0.641* | 2431.7 / 0.596 | 2723.5 / 0.369 | 2225.9 / 0.578 | 2423.1 / 0.475 | 2428.5 / 0.421 | 2542.3 / 0.195 |

*(Values shown as RMSE / PCC. Bold = best; italic = second-best.)*

Following [5], [14], results with L > 5 are considered long-term and L ≤ 5 short-term in regional ILI forecasting; forecasting results for L = 1 are not considered (influenza monitoring data are delayed by at least one week).

MIFlu demonstrates the best performance in all cases. SAIFlu-Net, Cola-GNN, and ReILIF also perform well due to attention mechanisms capturing regional patterns. ReILIF sometimes outperforms GPT4TS (since ReILIF uses exogenous time-series data while GPT4TS uses only ILI data), but GPT4TS outperforms ReILIF in long-term forecasting (L = 15, 20) due to its multi-transformer-decoder architecture. MIFlu utilizes expert knowledge in textual format with two LLMs to predict future ILI via multimodal data, improving on GPT4TS's forecasting accuracy with a **relative performance gain of up to 26.2%** compared to the SOTA model, and a **relative gain of up to 43.0%** compared to ReILIF (the SOTA model before GPT4TS was applied to regional ILI forecasting).

#### Figure 4 — Comparison of real and predicted ILIs for MIFlu using the US-Region dataset (description)

Two line charts (Actual Data vs. Predicted Data) over "Time Step" (x-axis, 0–roughly 450) vs. "ILI occurrences" (y-axis, 0–~12,000):

- **(a) L = 2:** Predicted (red) closely tracks Actual (yellow-green) across all seasonal peaks, including sharp/unusual peak intensities.
- **(b) L = 20:** Predicted (red) tracks the actual seasonal trend and general peak timing reasonably well but with more smoothing/deviation than the L = 2 case, especially around the sharpest peaks.

This shows MIFlu can predict unusual peak timing and peak intensity in short-term forecasting (L = 2) — crucial for infectious-disease experts' decision-making — and can also predict actual ILI trends in long-term forecasting (L = 20).

### C. Textual Input Embedder Analysis

Candidates for the textual input embedder: **BERT**, **LLaMA2-7B**, and **GPT2**.

**Table VII — Forecasting Accuracy (MSE/MAE) Comparison Depending on Textual Input Embedder**

| Textual input embedder | L=24 | L=36 | L=48 | L=60 |
|---|---|---|---|---|
| GPT2 (MIFlu) | 1.542 / 0.726 | 1.422 / 0.779 | 1.414 / 0.757 | 1.364 / 0.719 |
| LLaMA2-7B | 1.553 / 0.783 | 1.447 / 0.774 | 1.433 / 0.761 | 1.486 / 0.792 |
| BERT | 1.602 / 0.797 | 1.564 / 0.774 | 1.572 / 0.803 | 1.525 / 0.783 |
| X (GPT4TS, no textual embedder) | 2.063 / 0.881 | 1.868 / 0.892 | 1.790 / 0.884 | 1.979 / 0.957 |

*(Each cell: MSE / MAE)*

All three textual input embedders improve ILI forecasting performance compared to unimodal GPT2 (X/GPT4TS). LLaMA2-7B outperforms BERT — likely because LLaMA2-7B has 7 billion parameters vs. only 110 million for BERT, and is pre-trained on about 600× more dataset tokens. However, even though both LLaMA2-7B and GPT2 are transformer decoders, they have different pre-trained knowledge/structure, so GPT2 (the forecasting LLM) may struggle to understand LLaMA2-7B's text embeddings. Thus, using GPT2 as *both* the textual input embedder and forecasting LLM may improve overall forecasting performance, since the semantic information embedded by GPT2 in the previous stage is better aligned.

### D. Sensitivity Analysis

**Window size T:** Fig. 5 shows forecasting results as T varies between 10 and 50 (US-Region dataset, L = 20), in terms of RMSE and PCC.

#### Figure 5 — Changes in forecasting accuracy according to T (description)

- **(a) RMSE:** Line chart, x-axis "Window size T" (10–50), y-axis RMSE (~1400–2800). RMSE starts very high (~2780) at T=10, drops sharply to a low point (~1450) around T=40, then rises slightly by T=50.
- **(b) PCC:** Line chart, x-axis "Window size T" (10–50), y-axis PCC (~0.1–0.8). PCC starts very low (~0.1) at T=10, rises sharply, peaks (~0.75–0.8) around T=30–40, then dips slightly by T=50.

When the target forecasting time is too far into the future, short input windows (e.g., T = 10) yield poor prediction accuracy. Up to T = 40, larger windows improve performance (more training data utilized); at T = 50, excessive input data causes overfitting, degrading accuracy.

**Number of GPT2 layers (K):** The original small GPT2 model has 12 layers. Fig. 6 shows results as K varies between 1 and 7 (US-Region dataset, L = 20).

#### Figure 6 — Changes in forecasting accuracy according to K (description)

- **(a) RMSE:** Line chart, x-axis "# of gpt layers K" (1–7), y-axis RMSE (~1950–2200). RMSE starts high (~2200) at K=1–2, drops sharply to a minimum (~1950) around K=4, then rises slightly and plateaus (~1970–2000) for K=5–7.
- **(b) PCC:** Line chart, x-axis "# of gpt layers K" (1–7), y-axis PCC (~0.56–0.68). PCC starts low (~0.57) at K=1, rises sharply, peaks (~0.68) around K=4, then declines slightly and plateaus for K=5–7.

In a pre-trained LLM, layers near the input hold generalizable information transferable to other tasks, while layers near the output hold task/data-specific information [37]. Up to K = 4, a higher K improves forecasting performance (smaller models have less pre-trained information to adapt); beyond six layers, more text-specific information is incorporated, which can reduce forecasting accuracy. Regardless of K, MIFlu outperforms the SOTA model ReILIF (RMSE = 2431.7, PCC = 0.596).

### E. Ablation Study

MIFlu has three core components: (1) a text prompt template, (2) a textual input embedder for multimodality, and (3) a LoRA adapter for fine-tuning. The text prompt template itself has three sections: dataset description, task instructions, and input variables. The ablation study (on the National-Illness dataset) removes each component/section from full MIFlu:

- **MIFlu w/o Dataset information** — prompt without the Dataset information section.
- **MIFlu w/o Task instruction** — prompt without the Task instruction section.
- **MIFlu w/o Input variable description** — prompt without the Input variable description section.
- **MIFlu w/o LoRA** — no PEFT; forecasting LLM fine-tuned only by updating PE and layer-normalization layers.
- **MIFlu w/o multimodality** — no textual input embedder; predicts future ILI unimodally.
- **MIFlu w/o LoRA + multimodality** — no textual input embedder and no LoRA; fine-tunes only PE and layer-normalization layers (this setting is identical to GPT4TS [9]).

**Table VIII — Ablation Study Results Using the National-Illness Dataset** *(average MSE/MAE for L = 24, 36, 48, 60)*

| Scheme | MSE | MAE |
|---|---|---|
| MIFlu | 1.436 | 0.745 |
| MIFlu w/o Dataset information | 1.473 | 0.770 |
| MIFlu w/o Task instruction | 1.465 | 0.759 |
| MIFlu w/o Input variable description | 1.538 | 0.779 |
| MIFlu w/o LoRA | 1.570 | 0.794 |
| MIFlu w/o multimodality | 1.647 | 0.816 |
| MIFlu w/o LoRA+multimodality | 1.925 | 0.904 |

Removing any part of the input text prompt degrades forecasting accuracy — all parts of the prompt template (Table I) are indispensable. Among the three parts, the **input variable description** has the greatest impact.

MIFlu w/o LoRA shows that adding LoRA fine-tuning improves forecasting accuracy of GPT4TS even in unimodality — because the LLM is pre-trained mainly on text data, so fine-tuning the multi-head self-attention layer via LoRA is needed to capture temporal patterns in historical time-series ILI. MIFlu w/o multimodality shows multimodal forecasting improves performance, since the forecasting LLM can leverage contextual information encoded by the textual input embedder. Using both LoRA and multimodal forecasting together yields significant performance improvements.

### F. Few-Shot Forecasting

To demonstrate data efficiency, few-shot forecasting performance is analyzed qualitatively using the last two seasons of the 'ILITOTAL' variable in the National-Illness dataset, using the first 50% (L = 48) and first 10% (L = 24) of the time steps of training data.

#### Figure 7 — Few-shot forecasting comparison results using the National-Illness dataset (description)

Two line charts (MIFlu vs. GPT4TS vs. Actual ILI) over "Time Step" (x-axis, 0–~100) vs. normalized "ILI occurrences" (y-axis, roughly −1 to 4):

- **(a) L = 48, 50% training data:** MIFlu (green) tracks Actual ILI (red) reasonably closely through two seasonal peaks; GPT4TS (yellow/orange) deviates more, especially overestimating/underestimating peak timing and intensity.
- **(b) L = 24, 10% training data:** With far less training data, MIFlu (green) still tracks the actual single seasonal peak's timing and intensity noticeably better than GPT4TS (yellow/orange), which shows larger deviation.

MIFlu achieves significantly better forecasting performance than GPT4TS even in the few-shot setting, especially for predicting peak intensity and peak timing — extremely important for infectious-disease-related decision-making.

### G. Training Time

**Table IX — Training Time of Regional ILI Forecasting Models**

| Model | Training time (min.) |
|---|---|
| ReILIF | 130 |
| MIFlu | 119 |

Despite being a larger model, MIFlu took less training time than ReILIF (US-Region dataset).

---

## VII. Conclusion

This paper proposes MIFlu, a multimodal ILI forecasting scheme based on LLMs, which integrates textual domain knowledge from infectious disease experts into a time-series forecasting LLM using a textual input embedder. Extensive experiments show MIFlu outperforms other SOTA national/regional ILI forecasting models in most cases, improving forecasting performance by up to 26.2% over SOTA models. The most accurate forecasting performance is achieved when GPT2, used as the forecasting LLM, is also used as the textual input embedder. The impact of hyperparameters (window size, number of GPT2 layers) on forecasting accuracy was analyzed, confirming the scheme performs well even as the number of layers changes. All components are confirmed essential via the ablation study, and MIFlu is shown to effectively enhance the forecasting performance of the unimodal model in the few-shot setting.

**Limitation / future work:** Even though the proposed model outperforms previously reported models, it uses a fixed text-embedding process from a pre-defined text prompt. Future work plans to construct a forecasting model that can fine-tune not only the forecasting LLM but also the textual input embedder, to automatically generate suitable text prompts from the input time-series data and further improve short-term ILI forecasting performance.

---

## Appendix — Example of Input Text Prompt

**Table X — Example of an Input Text Prompt** (actual example for the National-Illness dataset)

```
[Dataset information]
This multivariate time series dataset includes 7 features
that recorded influenza patients data from Centers for
Disease Control and Prevention of the United States
between 2002 and 2021.
Below (1) to (7) is the information about each feature:
***
[Input variable description]
(1) Percentage of patient visits in the healthcare system
attributed to influenza, adjusted for the proportion of
each reporting center's total patient visits. Minimum
value: <min(X1_train)>, maximum value: <max(X1_train)>.
This variable peaks 1 time for 1 year.

(2) Percentage of unweighted influenza, not adjusted
for the proportion of each reporting total patient visits.
Minimum value: <min(X2_train)>, maximum value:
<max(X2_train)>. This variable peaks 1 time for 1 year.

(3) Total number of influenza patients between age 0
and 4. Minimum value: <min(X3_train)>, maximum value:
<max(X3_train)>. This variable peaks 1 time for 1 year.

(4) Total number of influenza patients between age 5
and 24. Minimum value: <min(X4_train)>, maximum
value: <max(X4_train)>. This variable peaks 1 time for 1
year.

(5) Total number of influenza patients. Minimum value:
<min(X5_train)>, maximum value: <max(X5_train)>. This
variable peaks 1 time for 1 year.

(6) A number of influenza providers. Minimum value:
<min(X6_train)>, maximum value: <max(X6_train)>. This
variable peaks 1 time for 1 year. The overall trend is
upward.

(7) 'OT' feature for long-term forecasting task.
Minimum value: <min(X7_train)>, maximum value:
<max(X7_train)>. This variable peaks 2 times for 1 year.
The overall trend is upward.
***
[Task instruction]
Predict the next 24 steps given the previous 104 steps for the
information attached.
```

---

## References

1. WHO, "Seasonal influenza newsroom," 2024. [Online]. Available: https://www.who.int/en/news-room/fact-sheets/detail/influenza-(seasonal)
2. J. Moon, S. Jung, S. Park, and E. Hwang, "Machine learning-based two-stage data selection scheme for long-term influenza forecasting," *Comput. Materials Continua*, vol. 68, no. 3, pp. 2945–2959, 2021, doi: 10.32604/cmc.2021.017435.
3. S. Deng, S. Wang, H. Rangwala, L. Wang, and Y. Ning, "Cola-GNN: Cross-location attention based graph neural networks for long-term ILI prediction," in *Proc. 29th ACM Int. Conf. Inform. Knowl. Manage.*, 2020, pp. 245–254, doi: 10.1145/3340531.3411975.
4. Y. Wu, Y. Yang, H. Nishiura, and M. Saitoh, "Deep learning for epidemiological predictions," in *Proc. 41st Int. ACM SIGIR Conf. Res. Develop. Inf. Retrieval*, 2018, pp. 1085–1088, doi: 10.1145/3209978.3210077.
5. S. Jung, J. Moon, S. Park, and E. Hwang, "Self-attention-based deep learning network for regional influenza forecasting," *IEEE J. Biomed. Health*, vol. 26, no. 2, pp. 922–933, Feb. 2021, doi: 10.1109/JBHI.2021.3093897.
6. A. Radford, J. Wu, R. Child, D. Luan, D. Amodei, and I. Sutskever, "Language models are unsupervised multitask learners," *OpenAI Blog*, vol. 1, no. 8, 2019, Art. no. 9.
7. Z. Gu, B. Zhu, G. Zhu, Y. Chen, M. Tang, and J. Wang, "AnomalyGPT: Detecting industrial anomalies using large vision-language models," in *Proc. AAAI Conf. Artif. Intell.*, 2024, pp. 1932–1940, doi: 10.1609/aaai.v38i3.27963.
8. H. Xue and F. D. Salim, "Promptcast: A new prompt-based learning paradigm for time series forecasting," *IEEE Trans. Knowl. Data Eng.*, vol. 36, no. 11, pp. 6851–6864, Nov. 2024, doi: 10.1109/TKDE.2023.3342137.
9. T. Zhou, P. Niu, L. Sun, and R. Jin, "One fits all: Power general time series analysis by pre-trained LM," in *Proc. 37th Int. Conf. Neural Inform. Process. Syst.*, 2023, pp. 43322–43355.
10. J. Moon, S. Jung, S. Park, and E. Hwang, "RESEAT: Recurrent self-attention network for multi-regional influenza forecasting," *IEEE J. Biomed. Health Inform.*, vol. 27, no. 5, pp. 2585–2596, May 2023, doi: 10.1109/JBHI.2023.3247687.
11. A. Vaswani et al., "Attention is all you need," in *Proc. 31st Int. Conf. Neural Inform. Process. Syst.*, 2017, pp. 6000–6010.
12. N. Kitaev, Ł. Kaiser, and A. Levskaya, "Reformer: The efficient transformer," 2020, arXiv:2001.04451.
13. H. Wu, J. Xu, J. Wang, and M. Long, "Autoformer: Decomposition transformers with auto-correlation for long-term series forecasting," in *Proc. 35th Int. Conf. Neural Inform. Process. Syst.*, 2021, pp. 22419–22430.
14. E. Papagiannopoulou, M. Bossa, N. Deligiannis, and H. Sahli, "Long-term regional influenza-like-illness forecasting using exogenous data," *IEEE J. Biomed. Health Inform.*, vol. 28, no. 6, pp. 3781–3792, Jun. 2024, doi: 10.1109/JBHI.2024.3377529.
15. J. Devlin, M. W. Chang, K. Lee, and K. Toutanova, "BERT: Pre-training of deep bidirectional transformers for language understanding," in *Proc. ACL Int. Conf. North Amer. Comp. Ling.*, 2019.
16. A. Radford, K. Narasimhan, T. Salimans, and I. Sutskever, "Improving language understanding by generative pre-training," *OpenAI Blog*, vol. 1, pp. 1–12, 2018.
17. H. Touvron et al., "Llama 2: Open foundation and fine-tuned chat models," 2023, arXiv:2307.09288.
18. M. Jin et al., "Time-LLM: Time series forecasting by reprogramming large language models," in *Proc. 12th Int. Conf. Learn. Representations*, 2023. [Online]. Available: https://openreview.net/forum?id=sHXLsv9AOw
19. T. Kim, J. Kim, Y. Tae, C. Park, J.-H. Choi, and J. Choo, "Reversible instance normalization for accurate timeseries forecasting against distribution shift," in *Proc. Int. Conf. Learn. Representations*, 2022. [Online]. Available: https://openreview.net/forum?id=cGDAkQo1C0p
20. J. Moon, S. Jung, S. Park, and E. Hwang, "Conditional tabular GAN-based two-stage data generation scheme for short-term load forecasting," *IEEE Access*, vol. 8, pp. 205327–205339, 2020, doi: 10.1109/ACCESS.2020.3037063.
21. N. Houlsby et al., "Parameter-efficient transfer learning for NLP," in *Proc. 36th Int. Conf. Mach. Learn.*, 2019, pp. 2790–2799.
22. R. Kemker, M. McClure, A. Abitino, T. L. Hayes, and C. Kanan, "Measuring catastrophic forgetting in neural networks," in *Proc. AAAI Conf. Artif. Intell.*, 2018, pp. 3390–3398, doi: 10.1609/AAAI.V32I1.11651.
23. P. Ye et al., "Partial fine-tuning: A successor to full fine-tuning for vision transformers," 2023, arXiv:2312.15681.
24. E. Hu et al., "LoRA: Low-rank adaptation of large language models," 2021, arXiv:2106.09685.
25. Centers for Disease Control and Prevention (CDC), "National, regional, and state level outpatient illness and viral surveillance," 2024. [Online]. Available: https://gis.cdc.gov/grasp/fluview/fluportaldashboard.html
26. H. Wu, T. Hu, Y. Liu, H. Zhou, J. Wang, and M. Long, "TimesNet: Temporal 2D-variation modeling for general time series analysis," 2022, arXiv:2210.02186.
27. G. Woo, C. Liu, D. Sahoo, A. Kumar, and S. Hoi, "ETSformer: Exponential smoothing transformers for time-series forecasting," 2022, arXiv:2202.01381.
28. T. Zhang et al., "Less is more: Fast multivariate time series forecasting with light sampling-oriented MLP structures," 2022, arXiv:2207.01186.
29. A. Zeng, M. Chen, L. Zhang, and Q. Xu, "Are transformers effective for time series forecasting?" in *Proc. AAAI Conf. Artif. Intell.*, 2023, pp. 10906–10914.
30. T. Zhou, Z. Ma, Q. Wen, X. Wang, L. Sun, and R. Jin, "FEDformer: Frequency enhanced decomposed transformer for long-term series forecasting," in *Proc. 39th Int. Conf. Mach. Learn.*, 2022, pp. 27268–27286.
31. Y. Nie, N. H. Nguyen, P. Sinthong, and J. Kalagnanam, "A time series is worth 64 words: Long-term forecasting with transformers," in *Proc. 11th Int. Conf. Learn. Representations*, 2023.
32. Y. Liu, H. Wu, J. Wang, and M. Long, "Non-stationary transformers: Exploring the stationarity in time series forecasting," in *Proc. 36th Int. Conf. Neural Inform. Process. Syst.*, 2022, pp. 9881–9893.
33. H. Zhou et al., "Informer: Beyond efficient transformer for long sequence time-series forecasting," in *Proc. AAAI Conf. Artif. Intell.*, 2021, pp. 11106–11115.
34. B. Lim, S. O. Arık, N. Loeff, and T. Pfister, "Temporal fusion transformers for interpretable multi-horizon time series forecasting," *Int. J. Forecasting*, vol. 37, no. 4, pp. 1748–1764, 2021, doi: 10.1016/j.ijforecast.2021.03.012.
35. R. Wang, H. Wu, Y. Wu, J. Zheng, and Y. Li, "Improving influenza surveillance based on multi-granularity deep spatiotemporal neural network," *Comput. Biol. Med.*, vol. 134, 2021, Art. no. 104482, doi: 10.1016/j.compbiomed.2021.104482.
36. C. Chang, W. C. Peng, and T. F. Chen, "LLM4TS: Two-stage fine-tuning for time-series forecasting with pre-trained LLMs," 2023, arXiv:2308.08469.
37. L. Yang, R. Y. Zhang, Y. Wang, and X. Xie, "MMA: Multi-modal adapter for vision-language models," in *Proc. IEEE/CVF Conf. Comput. Vis. Pattern Recognit.*, 2024, pp. 23826–23837.

---

*Note on figures/tables: Figures 1–7 and Tables II–III (which are statistical summary tables/diagrams rendered as images in the source PDF) are reproduced here as detailed textual descriptions of their visual content, since their exact pixel/graphical data cannot be losslessly converted into text. Tables I, IV–X, and Equations 1–6 (mathematical/textual content) are reproduced verbatim/in full.*
