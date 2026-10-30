# MIFlu Related Work: Papers with Code & Reproducibility

**For your friend's research opportunities**: List of related papers that have either released code, detailed implementations, or are more concrete than MIFlu.

---

## Table of Contents

1. [LLM-Based Time Series Forecasting (Code Available)](#llm-based-time-series-forecasting-code-available)
2. [Influenza Forecasting Specific Work](#influenza-forecasting-specific-work)
3. [Comparison: MIFlu vs. Related Work](#comparison-miflu-vs-related-work)
4. [Research Opportunities (Gaps)](#research-opportunities-gaps)
5. [Quick Reference Table](#quick-reference-table)

---

## LLM-Based Time Series Forecasting (Code Available)

### 1. **Time-LLM** (ICLR 2024) ⭐ MOST RELEVANT

**Title**: Time-LLM: Time Series Forecasting by Reprogramming Large Language Models

**Authors**: Zhou et al.

**Key Innovation**: Reprogramming framework that converts time series into text prototypes, then uses LLM with prompt context.

**Code Available**: ✅ **YES** - GitHub repo with full implementation
- https://github.com/KimMeen/Time-LLM
- Supports: GPT-2, LLaMA-7B, BERT
- PyTorch implementation
- Jupyter notebooks included

**Architecture**:
```
Time Series 
    ↓
Patch Tokenization (similar to MIFlu)
    ↓
Text Prototype Representation
    ↓
Prompt Augmentation (domain knowledge)
    ↓
LLM Forecasting
```

**Key Parameters**:
- Patch length (P)
- Stride (S)
- Text embedding dimension
- LLM selection (GPT-2, LLaMA, BERT)

**Performance**: Outperforms transformers on long-term forecasting

**Related to MIFlu**: YES
- Both use patching + text prompts + LLM
- Time-LLM has **full code released** (MIFlu does not)
- Time-LLM tested on multiple LLMs; MIFlu only GPT2

**Reproducibility**: ⭐⭐⭐⭐⭐ (Excellent - code + config + examples)

**Good For**: Learning proper LLM time-series integration; baseline comparisons

---

### 2. **Chronos: Learning the Language of Time Series** (Amazon, 2024) ⭐⭐

**Title**: Chronos: Learning the Language of Time Series

**Company**: Amazon Science

**Key Innovation**: Pretrained foundation model for time series using quantization + language model tokenization

**Code Available**: ✅ **YES** - Full package on PyPI
- https://github.com/amazon-science/chronos-forecasting
- `pip install chronos-forecasting`
- Pre-trained models on Hugging Face
- Active development (latest: Chronos-2, June 2026)

**Architecture**:
```
Time Series
    ↓
Scaling & Quantization (unique tokenization strategy)
    ↓
Token IDs (like language tokens)
    ↓
Language Model Training (cross-entropy loss)
    ↓
Sampling (multiple trajectories for uncertainty)
```

**Key Parameters**:
- Quantization levels (unique approach)
- Scaling strategy
- Model size (Chronos-2: 120M params)
- Batch size (recommended: 32-64)
- Learning rate (provided in docs)

**Performance**:
- Zero-shot on new datasets
- State-of-the-art on fev-bench, GIFT-Eval
- 300+ forecasts/sec on A10G GPU

**Related to MIFlu**: PARTIALLY
- Uses LLM for time-series
- NO explicit text/domain knowledge injection (unlike MIFlu)
- Pure quantization approach (vs. MIFlu's patching)
- Can fine-tune on new tasks

**Reproducibility**: ⭐⭐⭐⭐⭐ (Excellent - maintained repo, notebooks, Hugging Face integration)

**Good For**: Baseline comparison; zero-shot evaluation; production deployment

**Deployment Options**:
- AWS SageMaker
- AutoGluon-Cloud (serverless)
- Local CPU/GPU

---

### 3. **LLMTime** (NeurIPS 2023) ⭐

**Title**: Large Language Models Are Zero Shot Time Series Forecasters

**Authors**: Gruver, Finzi, Qiu, Wilson

**Key Innovation**: Zero-shot forecasting by encoding numbers as text, sampling completions

**Code Available**: ✅ **YES** - GitHub repo
- https://github.com/ngruver/llmtime
- Works with GPT-3, GPT-4, LLaMA-2, Mistral
- Minimal dependencies
- Demo notebook included

**Approach**:
```
Time Series: [1.2, 3.4, 2.1, 5.6, ...]
    ↓
Text Encoding: "1.2, 3.4, 2.1, 5.6,"
    ↓
LLM Prompt: "Continue the sequence"
    ↓
LLM Completion Sampling
    ↓
Extract predictions
```

**Key Finding**: 
- GPT-3 outperforms GPT-4 (alignment models hurt performance)
- Scaling helps (larger models → better forecasts)
- Zero-shot without any fine-tuning

**Related to MIFlu**: MINIMAL
- No patching, no domain knowledge
- Pure text-based approach
- No fine-tuning required
- Different conceptual approach

**Reproducibility**: ⭐⭐⭐⭐⭐ (Code + quick demo)

**Good For**: Understanding zero-shot capabilities; quick baselines; API-based experiments

---

### 4. **GPT4TS** (Referenced in MIFlu) ⭐⭐

**Title**: One Fits All: Power General Time Series Analysis by Pre-trained LM

**Key Innovation**: Freeze most LLM layers, fine-tune only shallow layers with LoRA

**Related to MIFlu**: YES (MIFlu uses GPT4TS as comparison baseline)

**Code Availability**: Likely available (referenced in Table IV of MIFlu)

**Architecture** (from MIFlu context):
- K=6 layers from GPT2
- Freeze: positional encoding + layer normalization
- Fine-tune: LoRA on attention
- No multimodal component

**Performance**: Baseline for MIFlu (MIFlu beats GPT4TS by 21-31% MSE)

**Key Difference from MIFlu**: 
- GPT4TS = unimodal (time-series only)
- MIFlu = multimodal (time-series + text prompts)

**Reproducibility**: ⭐⭐⭐ (Referenced in multiple papers)

---

### 5. **PromptCast** (2023) ⭐

**Title**: PromptCast: A New Prompt-based Learning Paradigm for Time Series Forecasting

**Key Innovation**: "Codeless" approach using prompts without explicit architecture design

**Approach**: Soft prompts + LLM for time series

**Related to MIFlu**: PARTIALLY
- Both use prompting + LLM
- PromptCast = soft prompt learning
- MIFlu = hard prompt templates (Table I/X)

**Reproducibility**: ⭐⭐⭐ (Paper available; implementation less clear)

---

### 6. **LLM4TS** (2023) ⭐⭐

**Title**: LLM4TS: Two-stage Fine-tuning for Time Series Forecasting with Pre-trained LLMs

**Key Innovation**: Two-stage approach (pretraining then task-specific tuning)

**Architecture**:
```
Stage 1: Pretrain on large TS corpus
Stage 2: Fine-tune on target task
```

**Related to MIFlu**: PARTIALLY
- Both fine-tune LLMs for time-series
- LLM4TS = two-stage
- MIFlu = single-stage with LoRA

**Reproducibility**: ⭐⭐⭐ (Referenced in multiple works)

---

### 7. **TEMPO** (2023) ⭐

**Title**: TEMPO: Prompt-based Time Series Decomposition for Forecasting

**Key Innovation**: Decomposition (trend + seasonality) before LLM forecasting

**Related to MIFlu**: MINIMAL
- Different decomposition approach
- Time-series only (no multimodal)

**Code Available**: Likely in referenced papers

**Reproducibility**: ⭐⭐

---

### 8. **Causal Graph Fuzzy LLMs** (2024) ⭐

**Title**: Causal Graph Fuzzy LLMs: Time Series Forecasting with Interpretable Representations

**Key Innovation**: Combine fuzzy time-series + causal graphs + GPT-2

**Architecture**:
```
Time Series
    ↓
Fuzzification (convert to linguistic values)
    ↓
Causal Analysis
    ↓
Interpretable Text → GPT-2
    ↓
Forecast
```

**Related to MIFlu**: PARTIALLY
- Uses domain knowledge (causal + fuzzy)
- Converts to interpretable text
- Similar to MIFlu's textual injection idea

**Code Available**: ✅ YES (mentioned in paper as open-source)

**Reproducibility**: ⭐⭐⭐⭐

---

### 9. **TS-HTFA** (2024) ⭐

**Title**: TS-HTFA: Advancing Time Series Forecasting via Hierarchical Text-Free Alignment

**Key Innovation**: Hierarchical alignment without explicit text

**Related to MIFlu**: OPPOSITE DIRECTION
- Tries to align WITHOUT text
- MIFlu = WITH text
- Research opportunity: compare text vs. no-text alignment

**Reproducibility**: ⭐⭐

---

### 10. **Nearest Neighbor Contrastive Learning for LLMs** (2024) ⭐

**Title**: Rethinking Time Series Forecasting with LLMs via Nearest Neighbor Contrastive Learning

**Key Innovation**: Use nearest neighbors to find similar patterns, feed as context to LLM

**Architecture**:
```
Test Series
    ↓
Find K-NN similar series from training
    ↓
Aggregate context
    ↓
LLM forecast
```

**Related to MIFlu**: COMPLEMENTARY
- Different context injection method
- Could combine with MIFlu's text prompts

**Code Availability**: Likely (recent arXiv paper)

**Reproducibility**: ⭐⭐⭐

---

## Influenza Forecasting Specific Work

### 1. **SAIFlu-Net** (Self-Attention Influenza, 2021) ⭐⭐

**Authors**: Jung et al.

**Paper**: Self-Attention-Based Deep Learning Network for Regional Influenza Forecasting

**Key Innovation**: Self-attention for regional pattern capture

**Architecture**:
```
LSTM per region (temporal)
    ↓
Self-Attention (regional patterns)
    ↓
Forecast
```

**Performance** (from MIFlu Table VI):
- L=2: RMSE=1016.2, PCC=0.908
- L=20: RMSE=2225.9, PCC=0.578
- MIFlu beats by ~15-20% RMSE

**Code Available**: ⚠️ UNCLEAR (should check their GitHub)

**Related to MIFlu**: YES
- Same datasets (US-Region)
- Regional ILI forecasting
- Baseline comparison in MIFlu

**Reproducibility**: ⭐⭐⭐ (Referenced in CDC challenge)

**Research Opportunity**: Combine SAIFlu-Net attention with MIFlu's text prompts

---

### 2. **Cola-GNN** (Cross-Location Attention, 2020) ⭐⭐

**Title**: Cola-GNN: Cross-location Attention based Graph Neural Networks for Long-term ILI Prediction

**Key Innovation**: Graph neural networks with cross-location attention

**Architecture**:
```
Regional ILI data
    ↓
Graph representation (regions = nodes)
    ↓
GNN + Cross-Location Attention
    ↓
Long-term forecast
```

**Performance** (from MIFlu Table VI):
- L=2: RMSE=1006.1, PCC=0.920 (competitive!)
- L=20: RMSE=2423.1, PCC=0.475 (MIFlu wins)

**Code Available**: ⚠️ LIKELY (should check authors' GitHub)

**Related to MIFlu**: YES
- Same datasets
- Graph-based approach (vs. MIFlu's LLM)
- Attention mechanisms

**Research Opportunity**: Graph neural networks + LLM + text (hybrid approach)

---

### 3. **ReILIF** (Recurrent with Exogenous Features, 2024) ⭐⭐

**Title**: Long-term Regional Influenza-Like-Illness Forecasting Using Exogenous Data

**Authors**: Papagiannopoulou et al.

**Key Innovation**: Uses exogenous data (weather, population) with self-attention

**Architecture**:
```
Regional ILI + Exogenous Features (weather, demographic)
    ↓
Self-Attention Integration
    ↓
Forecast
```

**Performance** (from MIFlu Table VI):
- L=2: RMSE=1354.8, PCC=0.876 (MIFlu wins 43%)
- L=20: RMSE=2431.7, PCC=0.596 (MIFlu wins 21%)

**Issue**: Uses time-varying exogenous data; MIFlu uses static text

**Related to MIFlu**: YES
- Same datasets
- Exogenous feature integration (vs. MIFlu's textual)

**Research Opportunity**: Replace ReILIF's time-varying features with MIFlu's static text prompts; compare

---

### 4. **DICE (Dynamics of Interacting Community Epidemics)** ⭐⭐⭐

**Title**: National and Regional Influenza-Like-Illness Forecasts for the USA

**Code Available**: ✅ **YES** - R package
- https://github.com/predsci/DICE
- Mechanistic + statistical approach
- Used in CDC forecasting challenge

**Key Innovation**: Mechanistic model (disease transmission) + statistical fitting

**Architecture**:
```
Disease transmission model (mechanistic)
    ↓
Region-to-region coupling
    ↓
Statistical parameter fitting
    ↓
Forecast + Uncertainty
```

**Related to MIFlu**: OPPOSITE
- MIFlu = data-driven (LLM-based)
- DICE = mechanistic (first-principles)
- Research opportunity: hybrid mechanistic + LLM

**Reproducibility**: ⭐⭐⭐⭐ (Active GitHub, R package)

**Good For**: Baseline; mechanistic understanding

---

### 5. **LSTM + PM2.5/Weather Integration** (2020) ⭐

**Title**: Influenza-like Illness Prediction Using LSTM with Multiple Open Data Sources

**Key Innovation**: Integrate air quality (PM2.5) + LSTM for ILI prediction

**Architecture**:
```
ILI + Air Quality (PM2.5)
    ↓
LSTM
    ↓
Forecast
```

**Related to MIFlu**: PARTIAL
- Multimodal approach (ILI + exogenous)
- LSTM instead of LLM
- Simpler than MIFlu

**Research Opportunity**: Replace LSTM with LLM; test on ILI + air quality + text prompts

---

### 6. **EpiGNN** (Epidemic Graph Neural Networks) ⭐⭐

**Title**: EpiGNN: Exploring Spatial Transmission with Graph Neural Network for Regional Epidemic Forecasting

**Key Innovation**: GNNs for epidemic spatial patterns

**Related to MIFlu**: PARTIAL
- Graph-based spatial modeling
- MIFlu doesn't explicitly model spatial patterns

**Research Opportunity**: Combine MIFlu's text prompts with EpiGNN's spatial GNN architecture

---

### 7. **FNN + Bayesian Model Averaging** (2019) ⭐

**Title**: Forecasting Influenza in Hong Kong with Google Search Queries and Statistical Model Fusion

**Key Innovation**: Ensemble approach (GLM + LASSO + ARIMA + DL) with Bayesian Model Averaging

**Architecture**:
```
Multiple models (statistical + deep learning)
    ↓
Bayesian Model Averaging (BMA)
    ↓
Ensemble forecast
```

**Related to MIFlu**: ENSEMBLE PERSPECTIVE
- MIFlu is single model
- Could ensemble MIFlu with other methods

**Research Opportunity**: Ensemble MIFlu + DICE + SAIFlu-Net using BMA

---

## Comparison: MIFlu vs. Related Work

| Method | Year | Code | Multimodal | Text Prompts | LLM | ILI Tested | Reproducibility |
|--------|------|------|-----------|-------------|-----|-----------|-----------------|
| **MIFlu** | 2025 | ❌ No | ✅ Yes | ✅ Yes (hard) | GPT-2 | ✅ Yes | ⭐⭐ Low |
| **Time-LLM** | 2024 | ✅ Yes | ❌ No | ✅ Yes | GPT2,LLaMA,BERT | ❌ No | ⭐⭐⭐⭐⭐ |
| **Chronos** | 2024 | ✅ Yes | ❌ No | ❌ No | Custom T5 | ❌ No | ⭐⭐⭐⭐⭐ |
| **LLMTime** | 2023 | ✅ Yes | ❌ No | ✅ Yes (zero-shot) | GPT3,GPT4,LLaMA | ❌ No | ⭐⭐⭐⭐⭐ |
| **SAIFlu-Net** | 2021 | ⚠️ Maybe | ❌ No | ❌ No | None (attention) | ✅ Yes | ⭐⭐⭐ |
| **Cola-GNN** | 2020 | ⚠️ Maybe | ❌ No | ❌ No | None (GNN) | ✅ Yes | ⭐⭐⭐ |
| **ReILIF** | 2024 | ⚠️ Maybe | ✅ Yes | ❌ No (exogenous TS) | None | ✅ Yes | ⭐⭐⭐ |
| **DICE** | 2019 | ✅ Yes (R) | ❌ No | ❌ No | None (mechanistic) | ✅ Yes | ⭐⭐⭐⭐ |
| **LLM4TS** | 2023 | ⚠️ Maybe | ❌ No | ✅ Yes | GPT2 | ❌ No | ⭐⭐⭐ |
| **TEMPO** | 2023 | ⚠️ Maybe | ❌ No | ✅ Yes | LLM | ❌ No | ⭐⭐ |

---

## Research Opportunities (Gaps)

### **Tier 1: High Impact, Medium Effort**

#### 1. **MIFlu + Time-LLM Comparison**
- Time-LLM has code, supports multiple LLMs
- MIFlu only has conceptual description
- **Opportunity**: Implement MIFlu properly on public datasets, compare with Time-LLM
- **Why**: Time-LLM code is production-ready; use as reference implementation

#### 2. **MIFlu + SAIFlu-Net Hybrid**
- SAIFlu-Net: self-attention for spatial patterns
- MIFlu: text prompts for domain knowledge
- **Opportunity**: Combine both (attention + text prompts)
- **Why**: MIFlu doesn't model spatial patterns explicitly

#### 3. **MIFlu + Chronos Zero-Shot**
- Chronos: pure zero-shot (no fine-tuning)
- MIFlu: requires fine-tuning + prompts
- **Opportunity**: Can Chronos + your friend's domain prompts outperform MIFlu?
- **Why**: Chronos is maintained, production-ready; test if prompts help

#### 4. **Dynamic Prompt Generation** (Your Friend's Original Idea!)
- MIFlu uses static prompts (Table I/X)
- **Opportunity**: Auto-generate prompts from data (what MIFlu future work suggests)
- **Why**: This is explicitly the paper's future direction
- **Approach Options**:
  - FlexMoe for dynamic routing of prompt sections
  - Reinforcement learning (avoid - data too sparse; 520 samples/week)
  - Supervised prompt generation (learn text patterns from time-series)
  - UCS/I2Moe for selective prompt components

### **Tier 2: High Impact, High Effort**

#### 5. **Mechanistic + LLM Hybrid** (DICE + MIFlu)
- DICE: mechanistic, interpretable, but limited
- MIFlu: data-driven, flexible, but black-box
- **Opportunity**: Hybrid model (mechanistic priors + LLM forecasting)
- **Why**: Best of both worlds for epidemiology

#### 6. **Multimodal Fusion** (ReILIF + MIFlu)
- ReILIF: time-varying exogenous (weather, demographic)
- MIFlu: static text (domain knowledge)
- **Opportunity**: Time-series features + text prompts together
- **Why**: Real-world data has both; test if combination > sum

#### 7. **Ensemble Method** (BMA approach)
- Combine: SAIFlu-Net + Cola-GNN + MIFlu + DICE
- Weight by Bayesian Model Averaging
- **Opportunity**: Benchmark ensemble vs. single models
- **Why**: Ensemble usually beats individual models

### **Tier 3: Lower Hanging Fruit**

#### 8. **Chronos Fine-Tuning on ILI**
- Chronos is zero-shot; can it fine-tune on ILI?
- **Opportunity**: Train Chronos on national + regional ILI
- **Why**: Code is available; should take 1-2 days

#### 9. **Time-LLM on ILI Datasets**
- Time-LLM has code; test on CDC ILI data
- **Opportunity**: Benchmark Time-LLM vs. MIFlu
- **Why**: Easiest comparison (Time-LLM code exists)

#### 10. **Prompt Optimization for MIFlu**
- Current prompt: Table I/X (static)
- **Opportunity**: Ablate prompt sections (already done in Table VIII)
- **Why**: What if you add seasonal patterns? Holiday effects? Variant info?

---

## Quick Reference Table

### Immediate Action Items for Your Friend

| Goal | Recommended Repo | Why |
|------|------------------|-----|
| **Learn LLM + TS properly** | Time-LLM (GitHub) | Full code, clean implementation, multiple LLMs |
| **Baseline for MIFlu** | Chronos (GitHub + PyPI) | Maintained, zero-shot, production-ready |
| **Compare ILI forecasting** | SAIFlu-Net (find authors) | Best regional baseline; attention-based |
| **Mechanistic alternative** | DICE (GitHub, R) | Open-source mechanistic model; interpretable |
| **Ensemble framework** | BMA literature | Combine multiple models systematically |
| **Dynamic prompts research** | Time-LLM codebase | Use as starting point for prompt optimization |

---

## Paper-by-Paper Details

### Time-LLM (Most Recommended)

```
GitHub: https://github.com/KimMeen/Time-LLM
Paper: https://openreview.net/forum?id=yl56yWa1ty (ICLR 2024)
Citation: Jin et al., "Time-LLM: Time Series Forecasting by Reprogramming Large Language Models"

Quick Start:
1. Clone repo
2. pip install -r requirements.txt
3. python scripts/train.py --config configs/gpt2.yaml
4. Tests on ETTh1, ETTh2, ECL, Weather, Electricity datasets

Key Files:
- models/Time-LLM.py (architecture)
- data_provider/data_factory.py (data loading)
- scripts/train.py (training loop)
- exp/exp_long_term_main.py (evaluation)
```

### Chronos (Production-Ready)

```
GitHub: https://github.com/amazon-science/chronos-forecasting
Hugging Face: amazon/chronos-2
PyPI: pip install chronos-forecasting

Quick Start:
1. pip install chronos-forecasting
2. from chronos import ChronosPipeline
3. pipeline = ChronosPipeline.from_pretrained("amazon/chronos-2")
4. forecast = pipeline.predict(context)

Deployment:
- AWS SageMaker (managed)
- AWS AutoGluon-Cloud (serverless)
- Local GPU/CPU
```

### LLMTime (Zero-Shot Experiments)

```
GitHub: https://github.com/ngruver/llmtime
Paper: NeurIPS 2023

Quick Start:
1. Clone repo
2. jupyter notebook demo.ipynb
3. Works with GPT-3.5, GPT-4, LLaMA APIs

No training required; pure API calls to LLMs
```

---

## Gaps in MIFlu That Related Work Addresses

| Gap | MIFlu | Related Work | Solution |
|-----|-------|--------------|----------|
| **No code** | ❌ | Time-LLM, Chronos | Use as reference implementation |
| **Static prompts** | ❌ (future work) | None yet | Research opportunity! |
| **Not maintained** | ❌ | Chronos (active) | Build on Chronos instead |
| **No spatial modeling** | ❌ | SAIFlu-Net, Cola-GNN | Hybrid attention + LLM |
| **No exogenous features** | ✅ (text) | ReILIF (TS) | Compare text vs. time-series features |
| **Single LLM (GPT2)** | ❌ | Time-LLM (multi-LLM) | Test MIFlu on LLaMA, Mistral |
| **No mechanism** | ❌ | DICE | Add interpretability |
| **High data needs assumed** | ✅ (addresses) | Chronos (zero-shot) | Compare training regimes |

---

## Your Friend's Research Roadmap

### Phase 1: Reproduction & Validation (2-3 weeks)
1. Implement Time-LLM from public GitHub
2. Apply to ILI datasets (National-Illness + US-Region)
3. Compare with published MIFlu numbers
4. Validate data preprocessing matches

### Phase 2: MIFlu Reimplementation (2-3 weeks)
1. Build MIFlu architecture (using Time-LLM as reference)
2. Implement Table I/X prompt template
3. Reproduce Table V/VI results
4. Debug gaps vs. paper

### Phase 3: Extensions (4-6 weeks) - Choose One:
- **Option A**: Dynamic prompt generation (your friend's original idea)
  - Start with LM-based prompt generation
  - Use few-shot learning to generate prompts from time-series patterns
  
- **Option B**: Hybrid models
  - Combine MIFlu attention patterns + SAIFlu-Net spatial modeling
  - Test on same datasets
  
- **Option C**: Chronos fine-tuning
  - Fine-tune Chronos on ILI
  - Add soft prompts for domain knowledge
  - Compare with MIFlu hard prompts

### Phase 4: Novel Contribution (8+ weeks)
- Based on Phase 3 results, propose hybrid/improved method
- Test on new datasets or tasks
- Compare with all baselines (DICE, SAIFlu-Net, Cola-GNN, Chronos, Time-LLM)

---

## Recommended Reading Order

1. **Start Here**: Time-LLM paper (learn LLM + TS properly)
2. **Then**: Chronos paper (understand quantization-based approach)
3. **Then**: MIFlu paper (understand their multimodal addition)
4. **Then**: SAIFlu-Net paper (understand spatial attention for ILI)
5. **Then**: ReILIF paper (understand exogenous feature integration)
6. **Finally**: DICE paper (mechanistic perspective)

---

## Datasets to Use

### Public ILI Datasets
- **National-Illness**: CDC surveillance, 2002-2021, 1,040 weeks, 7 variables
  - Source: https://gis.cdc.gov/grasp/fluview/fluportaldashboard.html
  - Download: FluView historical data export
  
- **US-Region (HHS)**: 10 regions, 1997-2020, 1,149 weeks
  - Same source as above

### General Time-Series Benchmarks (for baseline models)
- **ETTh1/ETTh2**: Electricity demand, 17,420 samples
- **Weather**: 21,000 samples
- **Electricity**: 26,280 samples
- All from: https://github.com/zhouhaoyi/ETDataset

---

## Key Takeaways for Your Friend

1. **MIFlu has no public code**: Use Time-LLM as reference
2. **Static prompts are a limitation**: This is your friend's research opportunity!
3. **Multiple baselines exist**: DICE, SAIFlu-Net, Cola-GNN, Chronos
4. **Hybrid approaches unexplored**: Combine spatial (GNN) + text (LLM) + mechanistic (DICE)
5. **Chronos is maintained & production-ready**: Better to build on Chronos than reproduce MIFlu
6. **Few-shot learning is critical**: MIFlu's few-shot advantage (Fig. 7) is underexplored

---

## Contact Info for Original Authors

If your friend wants to reach out:

- **MIFlu (Moon et al.)**: Korea University, Seoul
  - Corresponding: Eenjun Hwang (ehwang04@korea.ac.kr)
  - Lab: School of Electrical Engineering, Korea University

- **Time-LLM (Jin et al.)**: Check GitHub for contact info
  - GitHub maintainer: KimMeen

- **Chronos (Amazon)**: 
  - GitHub: amazon-science/chronos-forecasting
  - Paper: https://www.amazon.science/code-and-datasets/chronos-learning-the-language-of-time-series

---

**Last Updated**: August 2026  
**Status**: Active research area with multiple implementations available  
**Recommendation**: Start with Time-LLM code as foundation; build MIFlu extensions from there
