# R1B MODEL CONTRACT

Built by **subclassing** `models.GPT4TS_lora.GPT4TS`; the author's file is unmodified.

## Kept exactly as released

| Element | Value |
|---|---|
| patch embedding | `nn.Linear(patch_size, d_model)` |
| padding / patch / stride | `ReplicationPad1d((0, stride))`, Lp=**24**, S=**2**, `patch_num` = 42 at T=104 |
| backbone | `GPT2Model.from_pretrained('gpt2')` truncated to `h[:6]` (K=6) |
| head | `nn.Linear(d_model * patch_num, pred_len)` |
| instance normalisation | inside `forward`, and reversed at the end |
| LoRA branch | the author's own `get_peft_model` code — only the `PEFT` flag differs |

## Changed (declared)

| # | Change | Class |
|---|---|---|
| B-2 | text prefixed; head reads the patch positions **after** the text | **declared algorithm change** |
| B-3 | `PEFT=1` so LoRA is applied | paper-required |
| B-4 | effective freeze: only LoRA, `ln*`, `wpe` trainable in the backbone | repairs a released defect |

## Measured parameter inventory (job 607887, HPC)

| Quantity | Value |
|---|---:|
| total parameters | **82,779,672** |
| trainable (PEFT=1) | **1,673,496** = **2.02 %** |
| LoRA tensors / parameters | **12 / 73,728**, all in `c_attn` |
| non-LoRA trainable tensors | 31 (`in_layer`, `out_layer`, backbone `ln_*`) |
| **frozen backbone tensors** | **49** |
| PEFT=0 control | 1,599,768 trainable, **0** LoRA tensors |

The LoRA rank is 4 and the target module is `c_attn`, both PAPER_EXPLICIT.
**`--target_modules` must never be passed**: the author's argparse declares it `type=str`
with a LIST default, so an override becomes a bare string and peft raises
`Target modules c_attn not found` (observed on job 606361).
