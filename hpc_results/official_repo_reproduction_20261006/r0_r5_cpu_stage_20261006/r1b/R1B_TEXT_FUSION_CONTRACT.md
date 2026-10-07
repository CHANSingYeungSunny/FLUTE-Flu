# R1B TEXT FUSION CONTRACT

## Why this is a declared algorithm change, not a repair of released behaviour

The paper's own token order is **self-contradictory**: L205 writes
`R^{(len(token)+num(patches))xD}` (text first) while L219 writes
`R^{(num(patches)+len(token))xD}` (text last). The released code implements the second
order and then keeps `outputs[:, :patch_num]` — the patch prefix. Under GPT-2's causal
attention those positions **cannot** attend to text that follows them.

**Measured consequence (released code):** equal-length different-content text substitution
changes the prediction by **exactly 0.000e+00** and the text gradient is **exactly 0.0** —
on CPU *and* on an A100, with a positive control proving the probe has power.

## R1-B's definition

```
hfuse = cat( text_embeddings (T_text, D) tiled to (B*M, T_text, D) ,
             patch_embeddings (B*M, patch_num, D) )
hidden = llmmodel(inputs_embeds=hfuse).last_hidden_state
read   = hidden[:, T_text : T_text + patch_num, :]     # the patches AFTER the text
```

`text_len` is 0 when there is no text, so the **matched no-text control** uses the same
code path with the block omitted.

## Measured effect on R1-B

| Setting | `max|dPred|` | `|grad_text|` | verdict |
|---|---:|---:|---|
| local CPU, PEFT=0 | **5.88e-02** | 1.04e-03 | `text_active` |
| **HPC, PEFT=1 (job 607887)** | **4.63e-02** | 1.16e-03 | **`text_active`** |

## Provenance

Text embeddings are supplied to `forward` **externally**, so the training path and the
substitution probe use **one code path** and cannot drift. R1-B uses the author's **own**
shipped embeddings (`dataset/illness/text_emb/text_emb_label_0507_<L>.txt`) — the author's
text representation for that horizon — rather than inventing a prompt encoding.

**Author confirmation is required for B-2.** Until then it is a declared algorithm change.
