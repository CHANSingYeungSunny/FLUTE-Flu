#!/usr/bin/env python3
"""
r1b_model.py — R1-B corrected model, built ON TOP OF the author's released code.

The author's class is imported, not copied. This module subclasses it and applies
exactly the corrections recorded in R1B_IMPLEMENTATION_CHANGE_LEDGER.md. The
author's own file is never modified.

WHY EACH CORRECTION EXISTS (all six are DECLARED deviations):

  B-1  seven channels.  The released loader slices `feat_id:feat_id+1`, so every
       sample is univariate. The paper's task is over seven variables. The
       *model* already supports M channels natively — only the loader restricts
       it — so B-1 is mostly a data-side change. Model-side it shows up in one
       place: the released text branch tiles text to `(B, T, D)` while the patch
       tensor is `(B*M, n, D)`, which cannot concatenate when M > 1.

  B-2  functional text pathway.  The released forward concatenates
       `(patches, text)` and then keeps `outputs[:, :patch_num]`. Under causal
       attention the kept positions precede the text and therefore CANNOT read
       it. Measured: text substitution changes the prediction by exactly 0 and
       the text gradient is exactly 0 (CPU and A100, with a positive control).
       The repair prefixes the text and reads the patch positions that FOLLOW
       it. This is a DECLARED ALGORITHM CHANGE, not released behaviour.

  B-3  PEFT enabled.  The released `--PEFT` defaults to 0, so the author's
       get_peft_model branch never executes. Setting PEFT=1 enables it. NOTE:
       `--target_modules` must NOT be passed on the command line — the author's
       argparse declares it `type=str` with a LIST default, so an override
       arrives as a bare string and peft raises "Target modules c_attn not
       found".

  B-4  an effective freeze.  The released freeze loop only ever sets
       requires_grad = True and never False, leaving 82,705,944 / 82,705,944 =
       100% trainable. The paper says PE and layer-normalization are tuned.

  B-5  validation-only checkpoint selection  (in r1b_train.py, not here).
  B-6  persisted predictions                 (in r1b_train.py, not here).

Text embeddings are supplied to `forward` EXTERNALLY so that the text-substitution
probe and the training path use one code path and cannot drift.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import torch
import torch.nn as nn

# the author's tree is put on the path by the caller; import it unmodified
from models.GPT4TS_lora import GPT4TS          # noqa: E402
from einops import rearrange                    # noqa: E402


class R1BCorrectedMIFlu(GPT4TS):
    """Author's GPT4TS with B-2 (text prefix + readout) and B-4 (real freeze).

    Everything else — patch embedding, the GPT-2 backbone truncation, the LoRA
    branch, the output head — is the author's own code.
    """

    def __init__(self, configs, device, text_embeddings=None):
        super().__init__(configs, device)          # the author's __init__, verbatim

        # ---- B-4: make the freeze effective ---------------------------------
        self.freeze_report = self._apply_effective_freeze()

        # ---- B-2: hold the text embeddings outside the module so that the
        #           training path and the probe path are the same code path ----
        self.text_embeddings = None
        if text_embeddings is not None:
            self.set_text_embeddings(text_embeddings)

        self.corrections = ["B-1 multivariate windows (data side)",
                            "B-2 prefix text and read the patch positions after it",
                            "B-3 PEFT=1 so LoRA is applied",
                            "B-4 effective freeze",
                            "B-5 validation-only selection (trainer)",
                            "B-6 persisted predictions (trainer)"]

    # ── B-4 ─────────────────────────────────────────────────────────────────
    def _apply_effective_freeze(self):
        """Freeze the pretrained backbone except the parts the paper tunes.

        Kept trainable:
          * LoRA parameters (name contains 'lora_')
          * layer normalisation ('ln')
          * positional embeddings ('wpe')
        Everything else in the backbone is frozen.
        The released loop only ever set True; this one sets False first.
        """
        kept, frozen = [], 0
        for name, param in self.llmmodel.named_parameters():
            if ("lora_" in name) or ("ln" in name) or ("wpe" in name):
                param.requires_grad = True
                kept.append(name)
            else:
                param.requires_grad = False
                frozen += 1
        # the projection and head are trained, as in the author's design
        for m in (self.in_layer, self.out_layer):
            for n, p in m.named_parameters():
                p.requires_grad = True
        return {"kept_trainable_in_backbone": len(kept),
                "frozen_tensors_in_backbone": frozen,
                "examples_kept": kept[:6],
                "note": "the released loop only ever set requires_grad=True and "
                        "never False, leaving 100% trainable"}

    # ── B-2 ─────────────────────────────────────────────────────────────────
    def set_text_embeddings(self, arr):
        """arr: (T_text, D) float array, or None for the no-text control."""
        self.text_embeddings = None if arr is None else torch.as_tensor(
            np.asarray(arr), dtype=torch.float32)

    def forward(self, x, itr=0):
        """R1-B forward. Mirrors the author's forward with exactly two edits:
        the concatenation order, and which positions the head reads.
        """
        B, L, M = x.shape

        # ---- the author's instance normalisation, unchanged -----------------
        means = x.mean(1, keepdim=True).detach()
        x = x - means
        stdev = torch.sqrt(torch.var(x, dim=1, keepdim=True, unbiased=False) + 1e-5).detach()
        x = x / stdev

        x = rearrange(x, 'b l m -> b m l')
        x = self.padding_patch_layer(x)
        x = x.unfold(dimension=-1, size=self.patch_size, step=self.stride)
        x = rearrange(x, 'b m n p -> (b m) n p')
        outputs = self.in_layer(x)                      # (B*M, patch_num, D)
        patch_num = outputs.shape[1]

        # ---- B-2: prefix the text -------------------------------------------
        text_len = 0
        if self.multimodal == 1 and self.text_embeddings is not None:
            te = self.text_embeddings.to(outputs.device, outputs.dtype)   # (T, D)
            text_len = te.shape[0]
            te = te.unsqueeze(0).repeat(outputs.shape[0], 1, 1)           # (B*M, T, D)
            # EDIT 1 of 2 vs the author's line 139:
            #   author: torch.cat((outputs, text_emb), axis=1)   -> text LAST
            #   here:   torch.cat((te, outputs),   axis=1)       -> text FIRST
            outputs = torch.cat((te, outputs), axis=1)

        outputs = self.llmmodel(inputs_embeds=outputs).last_hidden_state

        # ---- B-2: read the patch positions that FOLLOW the text -------------
        # EDIT 2 of 2 vs the author's line 145:
        #   author: outputs[:, :self.patch_num, :]      -> the patch prefix
        #   here:   outputs[:, text_len:text_len+patch_num, :]
        outputs = outputs[:, text_len:text_len + patch_num, :]

        outputs = self.out_layer(outputs.reshape(B * M, -1))
        outputs = rearrange(outputs, '(b m) l -> b l m', b=B)

        outputs = outputs * stdev
        outputs = outputs + means
        return outputs                                  # (B, L, M)


def run_text_influence_check(model, x, probe_text, ctrl_text):
    """Deterministic equal-length text intervention on THIS model.

    Returns the max |delta prediction| and the gradient norms. Used by the
    acceptance tests and by the post-training probe, so both use one code path.
    """
    model.eval()
    was = model.text_embeddings
    try:
        with torch.no_grad():
            model.set_text_embeddings(probe_text)
            a = model(x, 0).detach()
            model.set_text_embeddings(ctrl_text)
            b = model(x, 0).detach()
        maxd = float((a - b).abs().max())

        model.zero_grad(set_to_none=True)
        model.set_text_embeddings(probe_text)
        t = model.text_embeddings.clone().requires_grad_(True)
        model.text_embeddings = t
        y = model(x, 0)
        loss = (y ** 2).mean()
        loss.backward()
        g_text = float(t.grad.detach().norm()) if t.grad is not None else 0.0
        g_all = float(sum(p.grad.detach().norm() ** 2
                          for p in model.parameters()
                          if p.grad is not None) ** 0.5)
        return {"max_abs_prediction_difference": maxd,
                "text_embedding_grad_norm": g_text,
                "total_grad_norm": g_all,
                "verdict": ("text_active"
                            if (maxd > 1e-6 or g_text > 0) else "text_inert")}
    finally:
        model.text_embeddings = was


if __name__ == "__main__":
    print("r1b_model: import OK")
    print("corrections implemented here: B-2 (text prefix + readout), B-4 (effective freeze)")
    print("corrections implemented in r1b_train.py: B-1, B-3, B-5, B-6, B-7")