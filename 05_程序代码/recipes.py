#!/usr/bin/env python
"""
recipes.py — Training-recipe ablation (Advisor Question 4)
==========================================================

MOTIVATION
----------
MIFlu (MIFlu_paper.md §V-C / Table IV) discloses batch size, learning rate,
epochs and repetition count, but says NOTHING about:

    * optimizer family (Adam vs AdamW)
    * beta1 / beta2 / epsilon
    * weight decay
    * LR scheduler
    * loss function
    * gradient clipping

Those six choices materially change the result, so a journal reviewer will ask
"did you check that your numbers are not an artefact of an undisclosed recipe?"
This module makes that check explicit and reproducible.

Three recipes are defined (plus a placeholder for future additions). `baseline`
reproduces EXACTLY what `train_miflu.py` / the original `train_ablation.py`
used, so the ablation is anchored on the published numbers.

USAGE
-----
    from recipes import build_recipe, RECIPES
    opt, crit, sched, clip = build_recipe("adamw_cosine", model, epochs=20)
    ...
    loss = crit(pred, target)
    loss.backward()
    if clip: torch.nn.utils.clip_grad_norm_(model.parameters(), clip)
    opt.step()
    ...
    if sched: sched.step()          # once per EPOCH, after the val loop
"""

from __future__ import annotations

import torch
import torch.nn as nn

# Adam defaults that MIFlu never states, now written down explicitly so the
# reviewer can see exactly what was (and was not) swept.
ADAM_BETAS = (0.9, 0.999)
ADAM_EPS = 1e-8

RECIPES: dict = {
    # ------------------------------------------------------------------ #
    "baseline": {
        "optimizer": "adam",
        "lr": 5e-4,
        "weight_decay": 0.0,
        "betas": ADAM_BETAS,
        "eps": ADAM_EPS,
        "scheduler": None,
        "loss": "mse",
        "grad_clip": None,
        "note": "Identical to the published MIFlu reproduction "
                "(train_miflu.py / original train_ablation.py).",
    },
    # ------------------------------------------------------------------ #
    "adamw_cosine": {
        "optimizer": "adamw",
        "lr": 5e-4,
        "weight_decay": 0.01,
        "betas": ADAM_BETAS,
        "eps": ADAM_EPS,
        "scheduler": "cosine",
        "loss": "mse",
        "grad_clip": None,
        "note": "AdamW (decoupled weight decay) + cosine LR decay to 0 over "
                "the full epoch budget.",
    },
    # ------------------------------------------------------------------ #
    "huber_clip": {
        "optimizer": "adamw",
        "lr": 1e-4,
        "weight_decay": 0.01,
        "betas": ADAM_BETAS,
        "eps": ADAM_EPS,
        "scheduler": None,
        "loss": "huber",
        "huber_delta": 1.0,
        "grad_clip": 5.0,
        "note": "Robust Huber loss (linear beyond delta=1.0, so a single "
                "missed peak cannot dominate) + gradient clipping at "
                "max_norm=5.0 + lower LR for stability.",
    },
}

DEFAULT_RECIPE = "baseline"


def _trainable_params(model):
    params = [p for p in model.parameters() if p.requires_grad]
    if not params:
        raise ValueError("model has no trainable parameters — check the freeze "
                         "logic (LoRA off + everything frozen)")
    return params


def _build_optimizer(cfg: dict, params):
    name = cfg["optimizer"].lower()
    if name == "adam":
        return torch.optim.Adam(params, lr=cfg["lr"],
                                betas=cfg["betas"], eps=cfg["eps"],
                                weight_decay=cfg.get("weight_decay", 0.0))
    if name == "adamw":
        return torch.optim.AdamW(params, lr=cfg["lr"],
                                 betas=cfg["betas"], eps=cfg["eps"],
                                 weight_decay=cfg.get("weight_decay", 0.0))
    raise ValueError(f"unknown optimizer: {cfg['optimizer']!r}")


def _build_criterion(cfg: dict):
    name = cfg["loss"].lower()
    if name == "mse":
        return nn.MSELoss()
    if name == "huber":
        return nn.HuberLoss(delta=cfg.get("huber_delta", 1.0))
    raise ValueError(f"unknown loss: {cfg['loss']!r}")


def _build_scheduler(cfg: dict, optimizer, epochs: int):
    name = cfg.get("scheduler")
    if name is None:
        return None
    if name == "cosine":
        # T_max = epochs: LR decays to ~0 exactly at the final epoch.
        return torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)
    raise ValueError(f"unknown scheduler: {name!r}")


def build_recipe(name: str, model, epochs: int):
    """Build (optimizer, criterion, scheduler, grad_clip) for recipe `name`.

    Returns:
        optimizer  : torch.optim.Optimizer
        criterion  : callable(pred, target) -> scalar loss
        scheduler  : torch LR scheduler or None (call `.step()` once per EPOCH)
        grad_clip  : float or None (pass to torch.nn.utils.clip_grad_norm_)
    """
    if name not in RECIPES:
        raise KeyError(f"unknown recipe {name!r}; available: {sorted(RECIPES)}")
    cfg = RECIPES[name]
    params = _trainable_params(model)
    opt = _build_optimizer(cfg, params)
    crit = _build_criterion(cfg)
    sched = _build_scheduler(cfg, opt, epochs)
    return opt, crit, sched, cfg.get("grad_clip")


def describe(name: str) -> str:
    """One-line, log-friendly description of a recipe."""
    cfg = RECIPES[name]
    bits = [f"{cfg['optimizer']}", f"lr={cfg['lr']:g}",
            f"wd={cfg.get('weight_decay', 0.0):g}",
            f"loss={cfg['loss']}"]
    if cfg.get("scheduler"):
        bits.append(f"sched={cfg['scheduler']}")
    if cfg.get("grad_clip"):
        bits.append(f"clip={cfg['grad_clip']:g}")
    bits.append(f"betas={cfg['betas']} eps={cfg['eps']:g}")
    return ", ".join(bits)


def _self_check() -> None:
    import torch.nn as nn

    model = nn.Linear(4, 2)
    for name in RECIPES:
        opt, crit, sched, clip = build_recipe(name, model, epochs=20)
        assert isinstance(crit, nn.Module)
        if name == "baseline":
            assert type(opt).__name__ == "Adam", type(opt).__name__
            assert sched is None and clip is None
            assert opt.param_groups[0]["lr"] == 5e-4
            assert opt.param_groups[0]["weight_decay"] == 0.0
        elif name == "adamw_cosine":
            assert type(opt).__name__ == "AdamW", type(opt).__name__
            assert sched is not None, "cosine scheduler expected"
            assert clip is None
            assert opt.param_groups[0]["weight_decay"] == 0.01
        elif name == "huber_clip":
            assert type(opt).__name__ == "AdamW", type(opt).__name__
            assert isinstance(crit, nn.HuberLoss), type(crit).__name__
            assert clip == 5.0, clip
            assert opt.param_groups[0]["lr"] == 1e-4
            assert sched is None
        print(f"  {name:14s} -> {describe(name)}")

    try:
        build_recipe("does_not_exist", model, 20)
    except KeyError:
        pass
    else:
        raise AssertionError("unknown recipe should raise KeyError")
    print("[recipes] self-check OK")


if __name__ == "__main__":
    _self_check()
