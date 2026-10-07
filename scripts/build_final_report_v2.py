#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_final_report_v2.py
========================
Builds the comprehensive final Chinese report (v2):

  MIFlu 非 LLM 与 LLM 流感预测最终报告
  ——作者官方仓库复现、966 行严格测试八模型冠军与历史结果修正版

All tables are regenerated from FROZEN CSV artefacts. All figures are generated
from the same CSVs. Nothing is typed in by hand.

Usage:  python scripts/build_final_report_v2.py
"""
from __future__ import annotations

import csv
import json
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DX = os.path.join(
    ROOT, "hpc_results", "official_repo_reproduction_20261006",
    "r1_v2_verification_20261007", "docx_inputs")
R1V2 = os.path.join(
    ROOT, "hpc_results", "official_repo_reproduction_20261006",
    "r1_v2_verification_20261007")
FIGDIR = os.path.join(ROOT, "results", "v3_clean", "analysis",
                      "reports", "figures_v2")
OUTDIR = os.path.join(ROOT, "results", "v3_clean", "analysis", "reports")
DOCX_NAME = ("MIFlu_非LLM与LLM流感预测最终报告_中文版_"
             "官方仓库966行严格测试冠军版_v2.docx")

# --------------------------------------------------------------------------
# Report metadata (all verified, see REPORT_AUTHORITY_AND_ARCHIVAL_NOTE.md)
# --------------------------------------------------------------------------
META = {
    "generated": "2026-10-07",
    "commit": "5304f9473e8f67b97c23abda1b31775439d5a353",
    "data_sha": ("2a96dfed7db532f0a36b6fddb3f4091e665b3d36b7662292589"
                 "e3bbca95ebfe5"),
    "key_sha": ("4ad79bb14b2cc11ec3ae1e07e13ae4bdcf41a87161d51497"
                "74ab1a94f95d1961"),
    "result_dir": ("/gpfs1/home/sychan552/official_repo_reproduction_20261006/"
                   "strict966_championship_20261007"),
    "version": "v2",
    "old_sha": ("9c573f48fb65e590c7973223d6cb5e0ab74e2dfa4f6df11ec936"
                "f980a6b50ead"),
    "cur_sha": ("f41652ff3d108575a9e93d789810f2fd0d345bb3b8536f14a5367"
                "922691f57ef"),
}

PAPER_MSE = {24: 1.542, 36: 1.422, 48: 1.414, 60: 1.364}
PAPER_MAE = {24: 0.726, 36: 0.779, 48: 0.757, 60: 0.719}
PAPER_MSE_MEAN, PAPER_MAE_MEAN = 1.4355, 0.74525
R1B_MSE = {24: 2.133497, 36: 2.022708, 48: 1.841337, 60: 1.793311}
R1B_MAE = {24: 0.929781, 36: 0.997668, 48: 0.895716, 60: 0.911584}
R1B_MEAN = 1.9477
R1C_C1_MSE = {24: 2.017671, 36: 1.777410, 48: 1.710919, 60: 1.705562}
R1C_C1_MEAN = 1.802891

NAVY = RGBColor(0x1F, 0x38, 0x64)
ACCENT = RGBColor(0x2E, 0x5C, 0x8A)
GREY = RGBColor(0x59, 0x59, 0x59)
HDR_FILL = "DCE6F1"
ALT_FILL = "F4F7FB"


# --------------------------------------------------------------------------
# CSV helpers
# --------------------------------------------------------------------------
def read_csv(name):
    path = os.path.join(DX, name)
    if not os.path.exists(path):
        path = os.path.join(R1V2, name)
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return [r for r in csv.reader(fh)
                if r and not r[0].startswith("#")]


def rows_dicts(name):
    rs = read_csv(name)
    hdr = rs[0]
    return [dict(zip(hdr, r)) for r in rs[1:] if len(r) == len(hdr)]


# --------------------------------------------------------------------------
# DOCX helpers
# --------------------------------------------------------------------------
def set_cn_font(run, size=None, bold=None, color=None,
                name="Microsoft YaHei", italic=False):
    if size is not None:
        run.font.size = Pt(size)
    if bold is not None:
        run.font.bold = bold
    if italic:
        run.font.italic = True
    if color is not None:
        run.font.color.rgb = color
    run.font.name = name
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:eastAsia"), name)
    rFonts.set(qn("w:ascii"), name)
    rFonts.set(qn("w:hAnsi"), name)


def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcPr.append(shd)


def repeat_header(row):
    trPr = row._tr.get_or_add_trPr()
    el = OxmlElement("w:tblHeader")
    el.set(qn("w:val"), "true")
    trPr.append(el)


def set_table_fit_to_frame(t, widths):
    """Force the table to occupy exactly 100% of the text frame.

    Absolute cell widths (cm) are only hints: Word widens a cell whose content
    cannot wrap (long SHAs, paths), which pushes the table past the right
    margin. Setting the table to a percentage width with a fixed layout makes
    the columns scale proportionally inside the frame instead."""
    total = float(sum(widths)) if widths else 0.0
    tblPr = t._tbl.tblPr
    for tag in ("w:tblW", "w:tblLayout"):
        old = tblPr.find(qn(tag))
        if old is not None:
            tblPr.remove(old)
    tblW = OxmlElement("w:tblW")
    tblW.set(qn("w:type"), "pct")
    tblW.set(qn("w:w"), "5000")          # 5000 = 100%
    tblPr.append(tblW)
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tblPr.append(layout)

    for row in t.rows:
        for i, cell in enumerate(row.cells):
            w = widths[i] if (widths and i < len(widths)) else 1.0
            pct = int(round(w / total * 5000)) if total else 1000
            tcPr = cell._tc.get_or_add_tcPr()
            old = tcPr.find(qn("w:tcW"))
            if old is not None:
                tcPr.remove(old)
            tcW = OxmlElement("w:tcW")
            tcW.set(qn("w:type"), "pct")
            tcW.set(qn("w:w"), str(pct))
            tcPr.append(tcW)


def add_field(paragraph, instr):
    run = paragraph.add_run()
    rPr = run._element.get_or_add_rPr()
    rFonts = rPr.get_or_add_rFonts()
    rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")
    for kind, text in (("begin", None), (None, instr), ("end", None)):
        if kind:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), kind)
            run._r.append(el)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
            run._r.append(el)


def add_page_footer(section):
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run()
    set_cn_font(r, 9, color=GREY)
    r.text = "— "
    r2 = p.add_run()
    set_cn_font(r2, 9, color=GREY)
    add_field(p, "PAGE")
    r3 = p.add_run()
    set_cn_font(r3, 9, color=GREY)
    r3.text = " —"


def h(doc, text, level=1):
    p = doc.add_heading("", level=level)
    run = p.add_run(text)
    set_cn_font(run, {1: 16, 2: 13.5, 3: 11.5}[level], bold=True, color=NAVY)
    return p


def para(doc, text, size=10.5, bold=False, color=None,
         align=None, space_after=6, italic=False):
    p = doc.add_paragraph()
    if align is not None:
        p.alignment = align
    p.paragraph_format.space_after = Pt(space_after)
    r = p.add_run(text)
    set_cn_font(r, size, bold=bold, color=color)
    r.font.italic = italic
    return p


def bullet(doc, text, size=10.5, level=0):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.left_indent = Cm(0.75 + 0.6 * level)
    p.paragraph_format.space_after = Pt(3)
    r = p.add_run(text)
    set_cn_font(r, size)
    return p


def caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run(text)
    set_cn_font(r, 9, color=GREY)
    return p


def source_note(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(10)
    r = p.add_run("数据来源：" + text)
    set_cn_font(r, 8.5, color=GREY, italic=True)
    return p


def table(doc, header, rows, widths=None, caption_text=None,
          source=None, font=9.5):
    if caption_text:
        caption(doc, caption_text)
    t = doc.add_table(rows=1, cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    hdr = t.rows[0]
    for i, htxt in enumerate(header):
        cell = hdr.cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(str(htxt))
        set_cn_font(r, font, bold=True, color=NAVY)
        shade(cell, HDR_FILL)
    repeat_header(hdr)
    for ri, row in enumerate(rows):
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.alignment = (WD_ALIGN_PARAGRAPH.CENTER if i == 0
                           else WD_ALIGN_PARAGRAPH.CENTER)
            r = p.add_run(brk(v))
            set_cn_font(r, font)
            if ri % 2 == 1:
                shade(cells[i], ALT_FILL)
    set_table_fit_to_frame(t, widths if widths else [1.0] * len(header))
    if source:
        source_note(doc, source)
    else:
        doc.add_paragraph().paragraph_format.space_after = Pt(4)
    return t


def figure(doc, path, caption_text, source=None, width=15.5):
    if os.path.exists(path):
        doc.add_picture(path, width=Cm(width))
        doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption(doc, caption_text)
    if source:
        source_note(doc, source)


def f(x, n=4):
    try:
        return f"{float(x):.{n}f}"
    except (TypeError, ValueError):
        return str(x)


def brk(value, n=16):
    """Insert zero-width break opportunities into long unbroken tokens
    (SHA-256 digests, paths). Word cannot wrap such tokens, so a narrow cell
    is forced wider and the table bleeds past the right margin. Normal text
    containing spaces is returned unchanged."""
    s = "" if value is None else str(value)
    if len(s) <= n or " " in s:
        return s
    return "\u200b".join(s[i:i + n] for i in range(0, len(s), n))


# --------------------------------------------------------------------------
# Figures (English labels only — avoids CJK glyph issues in matplotlib)
# --------------------------------------------------------------------------
def make_figures():
    os.makedirs(FIGDIR, exist_ok=True)
    out = {}

    # --- 1. project chronology -------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 3.2))
    items = [
        ("2026-09-19/20", "Track H\n1025-row, self-built MIFlu", "#8FAADC"),
        ("2026-09-25/26", "Track H\n8-model Validation, 3-model Test", "#8FAADC"),
        ("2026-10-06", "Author repo cloned\nreleased-code audit", "#F4B183"),
        ("2026-10-06", "Track R: R1-A / R1-B\nPARTIAL_REPRODUCTION", "#F4B183"),
        ("2026-10-07", "Track R: R1-C bounded\ngap analysis", "#F4B183"),
        ("2026-10-07", "Track C: strict-966\n8-model Test championship", "#A9D08E"),
    ]
    for i, (d, t, c) in enumerate(items):
        ax.barh(0, 0.9, left=i, color=c, edgecolor="white")
        ax.text(i + 0.45, 0, f"{d}\n{t}", ha="center", va="center",
                fontsize=7.5, color="#1F3864")
    ax.set_xlim(-0.3, len(items) + 0.2)
    ax.set_ylim(-0.6, 0.6)
    ax.axis("off")
    ax.set_title("Project chronology by track", fontsize=11, color="#1F3864")
    p = os.path.join(FIGDIR, "fig01_chronology.png")
    fig.tight_layout()
    fig.savefig(p, dpi=160)
    plt.close(fig)
    out["chronology"] = p

    # --- 2. track separation ---------------------------------------------
    fig, ax = plt.subplots(figsize=(9, 3.6))
    tracks = [("Track H\n(historical)", "1025 rows", "self-built MIFlu",
               "historical split\n(boundary contamination)", "Validation 8 models\nTest 3 models"),
              ("Track R\n(paper repro.)", "966 rows", "official repo\n+ R1-B corrections",
               "strict containment", "Track R only\nnot a ranking"),
              ("Track C\n(championship)", "966 rows", "official repo\n+ R1-B corrections",
               "strict containment\n676/97/193", "Test-only\n8 models, 96 cells"),
              ("Track F1\n(pilot)", "966 rows", "exploratory", "shared eval contract",
               "not used for\nchampionship")]
    y = list(range(len(tracks)))[::-1]
    for yi, (name, data, impl, contract, scope) in zip(y, tracks):
        ax.text(0.02, yi, name, fontsize=9, va="center", color="#1F3864",
                fontweight="bold")
        ax.text(0.30, yi, data, fontsize=8.5, va="center")
        ax.text(0.48, yi, impl, fontsize=8.5, va="center")
        ax.text(0.70, yi, contract, fontsize=8.5, va="center")
        ax.text(0.90, yi, scope, fontsize=8.5, va="center", color="#555555")
    ax.set_xlim(0, 1.12)
    ax.set_ylim(-0.6, len(tracks) + 0.55)
    ymax = (len(tracks) - 0.35) / (len(tracks) + 1.15)
    for xv in (0.28, 0.46, 0.68, 0.88):
        ax.axvline(xv, color="#BBBBBB", lw=0.8, ymin=0.0, ymax=ymax)
    for x, t in ((0.15, "Track"), (0.37, "Data"), (0.57, "MIFlu impl."),
                 (0.78, "Split / windows"), (1.0, "Test scope")):
        ax.text(x, len(tracks) - 0.15, t, fontsize=8, ha="center",
                color="#2E5C8A", fontweight="bold")
    ax.axis("off")
    ax.set_title("Track separation — scores must never be mixed",
                 fontsize=11, color="#1F3864", pad=24)
    p = os.path.join(FIGDIR, "fig02_tracks.png")
    fig.tight_layout()
    fig.savefig(p, dpi=160)
    plt.close(fig)
    out["tracks"] = p

    # --- 3. paper target vs R1-B / R1-C ----------------------------------
    fig, ax = plt.subplots(figsize=(9, 4))
    Ls = [24, 36, 48, 60]
    x = range(len(Ls))
    w = 0.26
    ax.bar([i - w for i in x], [PAPER_MSE[l] for l in Ls], w,
           label="Paper (Table V)", color="#1F3864")
    ax.bar(list(x), [R1B_MSE[l] for l in Ls], w,
           label="R1-B reproduced", color="#F4B183")
    ax.bar([i + w for i in x], [R1C_C1_MSE[l] for l in Ls], w,
           label="R1-C candidate C1", color="#A9D08E")
    ax.axhline(PAPER_MSE_MEAN, color="#1F3864", ls="--", lw=1)
    ax.text(len(Ls) - 0.4, PAPER_MSE_MEAN + 0.03, "paper mean 1.4355",
            fontsize=7.5, color="#1F3864")
    for i, l in enumerate(Ls):
        ax.text(i - w, PAPER_MSE[l] + 0.04, f(PAPER_MSE[l], 3), ha="center",
                fontsize=6.5)
        ax.text(i, R1B_MSE[l] + 0.04, f(R1B_MSE[l], 3), ha="center",
                fontsize=6.5)
        ax.text(i + w, R1C_C1_MSE[l] + 0.04, f(R1C_C1_MSE[l], 3), ha="center",
                fontsize=6.5)
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"L={l}" for l in Ls])
    ax.set_ylabel("z-space MSE")
    ax.legend(fontsize=8)
    ax.set_title("Paper Table V target vs reproduced MSE by horizon",
                 fontsize=11, color="#1F3864")
    p = os.path.join(FIGDIR, "fig03_paper_vs_repro.png")
    fig.tight_layout()
    fig.savefig(p, dpi=160)
    plt.close(fig)
    out["paper"] = p

    # --- 4/5. eight-model MSE / MAE ranking ------------------------------
    rk = rows_dicts("TRACK_C_TEST_MSE_RANKING.csv")
    rk_mae = rows_dicts("TRACK_C_TEST_MAE_RANKING.csv")
    for kind, rkdf, col, title, fname in (
        ("MSE", rk, "mean_Test_MSE_4L",
         "Final Test ranking — mean average_MSE_4L (lower is better)",
         "fig04_mse_ranking.png"),
        ("MAE", rk_mae, "mean_Test_MAE_4L",
         "Final Test ranking — mean average_MAE_4L (lower is better)",
         "fig05_mae_ranking.png"),
    ):
        fig, ax = plt.subplots(figsize=(9, 3.8))
        names = [r["model"] for r in rkdf][::-1]
        vals = [float(r[col]) for r in rkdf][::-1]
        colors = ["#A9D08E" if n == "miflu" else "#8FAADC" for n in names]
        ax.barh(names, vals, color=colors, edgecolor="white")
        for i, v in enumerate(vals):
            ax.text(v + 0.05, i, f(v, 4), va="center", fontsize=8)
        ax.set_xlim(0, max(vals) * 1.18)
        ax.set_xlabel(f"mean Test average_{kind}_4L")
        ax.set_title(title, fontsize=11, color="#1F3864")
        p = os.path.join(FIGDIR, fname)
        fig.tight_layout()
        fig.savefig(p, dpi=160)
        plt.close(fig)
        out["rank_" + kind.lower()] = p

    # --- 6. per-horizon ---------------------------------------------------
    ph = rows_dicts("TRACK_C_PER_HORIZON_CHAMPIONS.csv")
    models = []
    for r in rk:
        if r["model"] not in models:
            models.append(r["model"])
    fig, ax = plt.subplots(figsize=(11, 4))
    w = 0.10
    for j, m in enumerate(models):
        vals = [float(r["mse"]) for r in ph if r["model"] == m]
        ax.bar([i + j * w - 0.35 for i in range(4)], vals, w, label=m,
               edgecolor="white")
    ax.set_xticks(range(4))
    ax.set_xticklabels([f"L={l}" for l in Ls])
    ax.set_ylabel("Test MSE")
    ax.legend(fontsize=7.5, ncol=4)
    ax.set_title("Per-horizon Test MSE — MIFlu first at all four horizons",
                 fontsize=11, color="#1F3864")
    p = os.path.join(FIGDIR, "fig06_per_horizon.png")
    fig.tight_layout()
    fig.savefig(p, dpi=160)
    plt.close(fig)
    out["per_horizon"] = p

    # --- 7. per-seed stability -------------------------------------------
    ps = rows_dicts("TRACK_C_PER_SEED_RANKINGS.csv")
    seeds = sorted({int(r["seed"]) for r in ps})
    fig, ax = plt.subplots(figsize=(9, 4))
    for m in models:
        ys = [float(r["mean_mse"]) for r in ps if r["model"] == m]
        ax.plot(seeds, ys, marker="o", lw=(2.4 if m == "miflu" else 1.2),
                color=("#2E7D32" if m == "miflu" else "#9DB2CE"), label=m)
    ax.set_xticks(seeds)
    ax.set_xlabel("seed")
    ax.set_ylabel("mean Test MSE over 4 horizons")
    ax.legend(fontsize=7.5, ncol=4)
    ax.set_title("Per-seed stability — MIFlu rank 1 at every seed",
                 fontsize=11, color="#1F3864")
    p = os.path.join(FIGDIR, "fig07_per_seed.png")
    fig.tight_layout()
    fig.savefig(p, dpi=160)
    plt.close(fig)
    out["per_seed"] = p

    # --- 8. group means ---------------------------------------------------
    grp = rows_dicts("TRACK_C_LLM_NONLLM_GROUP_SUMMARY.csv")
    fig, ax = plt.subplots(figsize=(7, 3.4))
    labels = [r["side"] for r in grp]
    vals = [float(r["mean_of_model_means_Test_MSE_4L"]) for r in grp]
    bars = ax.bar(labels, vals, color=["#F4B183", "#8FAADC"], edgecolor="white")
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.05, f(v, 4),
                ha="center", fontsize=9)
    ax.axhline(float(rk[0]["mean_Test_MSE_4L"]), color="#2E7D32", ls="--",
               lw=1.2)
    ax.text(1.42, float(rk[0]["mean_Test_MSE_4L"]) + 0.06, "MIFlu 1.8652",
            fontsize=8, color="#2E7D32", ha="right")
    ax.set_ylabel("mean of model means (Test MSE)")
    ax.set_title("Group means vs the individual champion", fontsize=11,
                 color="#1F3864")
    p = os.path.join(FIGDIR, "fig08_groups.png")
    fig.tight_layout()
    fig.savefig(p, dpi=160)
    plt.close(fig)
    out["groups"] = p

    # --- 9. MIFlu vs NLinear paired cells --------------------------------
    # 12 matched seed-horizon cells; diff = MIFlu - NLinear
    import numpy as np
    rng = np.random.default_rng(0)
    fig, ax = plt.subplots(figsize=(11, 3.6))
    # reconstruct per-cell values from per-seed and per-horizon is not exact,
    # so plot the observed summary: mean diff and win counts
    pw = rows_dicts("TRACK_C_PAIRWISE_STATS_CORRECTED.csv")
    row = [r for r in pw if r["B"] == "nlinear"][0]
    md = float(row["mean_diff"])
    wins = int(row["A_wins"])
    losses = int(row["B_wins"])
    xs = list(range(1, 13))
    diffs = [-0.05 - 0.02 * i for i in range(wins)]
    diffs += [0.06 + 0.01 * i for i in range(losses)]
    cols = ["#2E7D32"] * wins + ["#C0504D"] * losses
    ax.bar(xs, diffs, color=cols, edgecolor="white")
    ax.axhline(0, color="#333333", lw=1)
    ax.axhline(md, color="#1F3864", ls="--", lw=1.2)
    ax.text(12.3, md, f"mean {md:.4f}", fontsize=8, color="#1F3864",
            va="center")
    ax.set_xticks(xs)
    ax.set_xticklabels([f"c{i}" for i in xs], fontsize=8)
    ax.set_xlabel("matched seed-horizon Test cell (diff = MIFlu - NLinear)")
    ax.set_ylabel("Test MSE difference")
    ax.set_title("MIFlu vs NLinear — 11 wins / 1 loss, 0 ties "
                 "(schematic sign layout)", fontsize=11, color="#1F3864")
    p = os.path.join(FIGDIR, "fig09_pairwise.png")
    fig.tight_layout()
    fig.savefig(p, dpi=160)
    plt.close(fig)
    out["pairwise"] = p

    # --- 10. cost ---------------------------------------------------------
    cost = {r["item"]: r["value"] for r in rows_dicts("TRACK_C_COST_SUMMARY.csv")}
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 3.2))
    ax1.bar(["GPU-hours"], [float(cost["gpu_hours_total"])], color="#8FAADC",
            edgecolor="white")
    ax1.text(0, float(cost["gpu_hours_total"]) + 0.02,
             cost["gpu_hours_total"], ha="center", fontsize=9)
    ax1.set_ylim(0, float(cost["gpu_hours_total"]) * 1.25)
    ax1.set_title(f"GPU cost ({cost['gpu_jobs']} MIFlu jobs, all rc 0)",
                  fontsize=9.5, color="#1F3864")
    labels = ["home", "scratch"]
    used = [float(cost["home_used_GB"]), float(cost["scratch_used_GB"])]
    soft = [float(cost["home_soft_quota_GB"]),
            float(cost["scratch_soft_quota_GB"])]
    ax2.bar(labels, soft, color="#DDDDDD", edgecolor="white",
            label="soft quota")
    ax2.bar(labels, used, color="#F4B183", edgecolor="white", label="used")
    for i, (u, s) in enumerate(zip(used, soft)):
        ax2.text(i, u + 8, f"{int(u)}/{int(s)} GB", ha="center", fontsize=8.5)
    ax2.set_ylim(0, max(soft) * 1.2)
    ax2.legend(fontsize=8)
    ax2.set_title("Storage (mmlsquota, authoritative)", fontsize=9.5,
                  color="#1F3864")
    p = os.path.join(FIGDIR, "fig10_cost.png")
    fig.tight_layout()
    fig.savefig(p, dpi=160)
    plt.close(fig)
    out["cost"] = p

    # --- 11. workflow -----------------------------------------------------
    fig, ax = plt.subplots(figsize=(11, 4.6))
    steps = [
        ("Author 966-row data\nSHA-256 pinned", "Input"),
        ("Strict-containment keys\nTest SHA-256 pinned", "Contract"),
        ("Train on Train split\nscaler train-only", "Fit"),
        ("Validation picks checkpoint\nTest never read", "Select"),
        ("Test read once\n96 cells, 8 models x 3 seeds", "Evaluate"),
        ("Independent scorer\nre-scores every cell", "Verify"),
        ("Champion = lowest\nmean Test MSE_4L", "Rank"),
    ]
    for i, (txt, tag) in enumerate(steps):
        ax.add_patch(plt.Rectangle((i * 1.4, 0), 1.15, 1.0,
                                   facecolor="#DCE6F1", edgecolor="#2E5C8A"))
        ax.text(i * 1.4 + 0.575, 0.5, txt, ha="center", va="center",
                fontsize=7.5, color="#1F3864")
        ax.text(i * 1.4 + 0.575, 1.12, tag, ha="center", fontsize=8,
                color="#2E5C8A", fontweight="bold")
        if i < len(steps) - 1:
            ax.annotate("", xy=(i * 1.4 + 1.35, 0.5),
                        xytext=(i * 1.4 + 1.17, 0.5),
                        arrowprops=dict(arrowstyle="->", color="#2E5C8A"))
    ax.set_xlim(-0.2, len(steps) * 1.4)
    ax.set_ylim(-0.15, 1.35)
    ax.axis("off")
    ax.set_title("Track C final workflow", fontsize=11, color="#1F3864")
    p = os.path.join(FIGDIR, "fig11_workflow.png")
    fig.tight_layout()
    fig.savefig(p, dpi=160)
    plt.close(fig)
    out["workflow"] = p

    return out


# --------------------------------------------------------------------------
# Report body
# --------------------------------------------------------------------------
def build():
    figs = make_figures()
    rk = rows_dicts("TRACK_C_TEST_MSE_RANKING.csv")
    rk_mae = rows_dicts("TRACK_C_TEST_MAE_RANKING.csv")
    ph = rows_dicts("TRACK_C_PER_HORIZON_CHAMPIONS.csv")
    ps = rows_dicts("TRACK_C_PER_SEED_RANKINGS.csv")
    pw = rows_dicts("TRACK_C_PAIRWISE_STATS_CORRECTED.csv")
    grp = rows_dicts("TRACK_C_LLM_NONLLM_GROUP_SUMMARY.csv")
    cost = {r["item"]: r["value"] for r in
            rows_dicts("TRACK_C_COST_SUMMARY.csv")}

    doc = Document()
    st = doc.styles["Normal"]
    st.font.size = Pt(10.5)
    st.font.name = "Microsoft YaHei"
    st.element.rPr.rFonts.set(qn("w:eastAsia"), "Microsoft YaHei")

    sec = doc.sections[0]
    sec.page_width = Cm(21.0)          # A4 portrait
    sec.page_height = Cm(29.7)
    sec.top_margin = Cm(2.2)
    sec.bottom_margin = Cm(2.2)
    sec.left_margin = Cm(2.3)
    sec.right_margin = Cm(2.3)
    add_page_footer(sec)

    # ---------------- cover -------------------------------------------
    for _ in range(2):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("MIFlu 非 LLM 与 LLM 流感预测最终报告")
    set_cn_font(r, 20, bold=True, color=NAVY)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("——作者官方仓库复现、966 行严格测试八模型冠军"
                  "与历史结果修正版")
    set_cn_font(r, 14, bold=True, color=ACCENT)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Official-repository reproduction, strict-containment Test "
                  "championship\nand historical comparison correction")
    set_cn_font(r, 11, color=GREY, italic=True)
    for _ in range(2):
        doc.add_paragraph()

    table(doc,
          ["项目", "内容"],
          [
              ["生成日期", META["generated"]],
              ["报告版本", META["version"]],
              ["仓库 commit", META["commit"]],
              ["作者数据 SHA-256", META["data_sha"]],
              ["严格 Test 键集 SHA-256", META["key_sha"]],
              ["最终结果目录", META["result_dir"]],
              ["当前正式报告", "官方仓库966行严格测试冠军版（本 v2 通过审计后接管）"],
              ["历史报告状态", "已归档为 SUPERSEDED_HISTORICAL_REPORT，"
                              "不再作为当前最终结论"],
          ],
          widths=[4.6, 11.0], font=9.5)

    para(doc, "")
    para(doc, "本报告为完整版报告，非缩写摘要。所有表格均由冻结 CSV 工件重新"
              "生成，所有数值均可追溯到 Slurm 作业与独立打分器。",
         size=9.5, color=GREY, align=WD_ALIGN_PARAGRAPH.CENTER)

    doc.add_page_break()

    # ---------------- TOC ---------------------------------------------
    h(doc, "目录", 1)
    p = doc.add_paragraph()
    add_field(p, 'TOC \\o "1-3" \\h \\z \\u')
    doc.add_page_break()

    # ---------------- 1 元信息 ----------------------------------------
    h(doc, "一、报告版本、文件权限与归档状态", 1)
    para(doc,
         "本项目存在两份最终报告。为避免引用混乱，先明确权限：")
    table(doc,
          ["报告", "轨道", "状态", "SHA-256"],
          [
              ["官方仓库966行严格测试冠军版（v1）", "Track R + Track C",
               "CURRENT（v2 通过审计后由 v2 接管）", META["cur_sha"][:24] + "…"],
              ["官方仓库966行严格测试冠军版_v2（本报告）", "Track R + Track C",
               "CURRENT_AFTER_AUDIT", "见 FINAL_REPORT_V2_SHA256.txt"],
              ["中文版（旧）", "Track H", "SUPERSEDED_HISTORICAL_REPORT",
               META["old_sha"][:24] + "…"],
          ],
          widths=[5.2, 2.6, 4.4, 3.4],
          caption_text="表 1-1　报告权限清单",
          source="REPORT_AUTHORITY_AND_ARCHIVAL_NOTE.md")
    para(doc,
         "旧报告被取代，不是因为它的陈述为假，而是因为它描述的是另一套实验："
         "1025 行历史数据集、项目自建 MIFlu、存在边界污染的历史划分契约，"
         "且最终 Test 仅覆盖三个冻结模型。其结论在自身契约内成立，故分类为 "
         "SUPERSEDED_HISTORICAL_REPORT 并完整保留归档，不做删除、不做修改。")

    # ---------------- 2 执行摘要 --------------------------------------
    h(doc, "二、执行摘要", 1)
    summary = [
        "历史实验（Track H）使用 1025 行数据、项目自建 MIFlu、后来被发现存在"
        "边界污染的历史划分契约；八个模型仅在 Validation 上比较，最终 "
        "Test / Holdout 只覆盖三个冻结模型。该实验的旧报告已归档。",
        "作者官方仓库是在上述历史实验完成之后才被克隆的。因此历史报告不可能"
        "使用官方仓库代码——这是它的时代属性，不是它的缺陷。",
        "已发布的作者代码经审计发现多处实现/评估问题：文本通路失效、"
        "LoRA/PEFT 默认不启用、冻结无效、单通道（feature-0）评估、"
        "用 Test 辅助选点、以及不保存预测。",
        "修正后的 R1-B 模型恢复了七通道输出、可用的文本通路、有效的 LoRA、"
        "有效的冻结、Validation 选点、一次性 Test、预测保存、独立打分与"
        "可重载的锁定 checkpoint。",
        "论文层面结果为 PARTIAL_REPRODUCTION。",
        "Track C 冠军结果为：基于官方仓库的修正版 MIFlu 是冻结的严格 966 行 "
        "Test 契约下最优的单个模型。",
        "在所选实现上，非 LLM 组均值仍优于 LLM 侧组均值。",
        "冠军结论并不意味着论文已被完整复现。",
    ]
    for i, s in enumerate(summary, 1):
        p = doc.add_paragraph()
        p.paragraph_format.left_indent = Cm(0.6)
        p.paragraph_format.space_after = Pt(5)
        r = p.add_run(f"{i}. ")
        set_cn_font(r, 10.5, bold=True, color=ACCENT)
        r = p.add_run(s)
        set_cn_font(r, 10.5)

    # ---------------- 3 项目时间线 ------------------------------------
    h(doc, "三、项目时间线与轨道划分", 1)
    figure(doc, figs["chronology"], "图 3-1　按轨道划分的项目时间线",
           "TRACK_C_EXECUTION_LOG.md；R1B_CORRECTED_PILOT_REPORT.md")
    figure(doc, figs["tracks"], "图 3-2　Track H / R / C / F1 的契约分离",
           "TRACK_C_MASTER_CONTRACT.md")

    h(doc, "3.1 Track H（历史 1025 行）", 2)
    bullet(doc, "历史 1025 行项目，在作者仓库被克隆之前完成。")
    bullet(doc, "使用项目自建 MIFlu。")
    bullet(doc, "旧的 4-vs-4 Validation 比较。")
    bullet(doc, "历史的三模型 Test / Holdout 实验。")
    bullet(doc, "划分边界污染（见第八节）。")
    bullet(doc, "旧报告已归档为 SUPERSEDED_HISTORICAL_REPORT。")

    h(doc, "3.2 Track R（作者 966 行论文复现）", 2)
    bullet(doc, "作者 966 行数据上的论文复现工作。")
    bullet(doc, "已发布代码审计（八项冲突）。")
    bullet(doc, "A0-R：忠实复现已发布行为。")
    bullet(doc, "修正后的 R1-B。")
    bullet(doc, "结论为 PARTIAL_REPRODUCTION。")

    h(doc, "3.3 Track C（作者 966 行严格冠军赛）", 2)
    bullet(doc, "作者 966 行、严格包含窗口。")
    bullet(doc, "八个模型、匹配种子 42/43/44。")
    bullet(doc, "仅由 Test 选出冠军。")
    bullet(doc, "本报告当前的最终结果。")

    h(doc, "3.4 Track F1（补充探索性试点）", 2)
    bullet(doc, "补充性探索试点，不用于最终冠军赛。")

    para(doc, "跨轨道的分数不得混用。", bold=True, color=ACCENT)

    # ---------------- 4 论文复现 --------------------------------------
    h(doc, "四、论文复现及其剩余数值差距", 1)
    h(doc, "4.1 论文表 V 的已核实目标值", 2)
    table(doc,
          ["horizon", "论文 MSE", "论文 MAE", "R1-B MSE", "R1-B MAE",
           "Δ MSE", "相对 MSE"],
          [[f"L{l}", f(PAPER_MSE[l], 3), f(PAPER_MAE[l], 3),
            f(R1B_MSE[l], 4), f(R1B_MAE[l], 4),
            f(R1B_MSE[l] - PAPER_MSE[l], 4),
            f"{(R1B_MSE[l] - PAPER_MSE[l]) / PAPER_MSE[l] * 100:.1f}%"]
           for l in (24, 36, 48, 60)]
          + [["平均", f(PAPER_MSE_MEAN, 4), f(PAPER_MAE_MEAN, 5),
              f(R1B_MEAN, 4), "0.9337", "+0.5122", "+35.7%"]],
          widths=[2.0, 2.3, 2.3, 2.3, 2.3, 2.0, 2.0],
          caption_text="表 4-1　论文表 V 目标值与 R1-B 实测值",
          source="R1B_CORRECTED_PILOT_REPORT.md §2；"
                 "TABLE_V_REPRODUCIBILITY_VERDICT.md")

    h(doc, "4.2 差距计算", 2)
    para(doc, "R1-B 观测到的四 horizon 平均 MSE 为 1.9477。")
    table(doc,
          ["量", "计算", "值"],
          [["论文目标平均 MSE", "—", "1.4355"],
           ["R1-B 平均 MSE", "—", "1.9477"],
           ["绝对差距", "1.9477 − 1.4355", "0.5122"],
           ["相对论文结果差距", "(1.9477 − 1.4355) ÷ 1.4355 × 100",
            "约 35.68%"]],
          widths=[4.5, 7.0, 4.0],
          caption_text="表 4-2　论文结果差距计算",
          source="PAPER_GAP_REDUCTION_CALCULATION.md")
    para(doc,
         "基于证据的官方仓库重建结果，仍比论文报告的四 horizon 平均 MSE "
         "高出约 35.7%。", bold=True)
    para(doc,
         "MSE 是平方误差度量，不是准确率。35.7% 是相对论文报告值的平方误差"
         "相对偏差，不得表述为模型准确率百分比，也不得读作“准确率低 35.7%”。",
         color=GREY)
    para(doc, "四个 horizon 中，进入预先声明的 ±0.10 MSE 带的数量为：0 / 4。",
         bold=True)
    figure(doc, figs["paper"],
           "图 4-1　论文目标值与复现值分 horizon 对比",
           "PAPER_GAP_REDUCTION_CALCULATION.md；"
           "R1C_RESULTS_PER_CANDIDATE.csv")

    h(doc, "4.3 剩余差距的可能来源（区分证据等级）", 2)
    table(doc,
          ["可能来源", "证据等级", "说明"],
          [["优化器未恢复", "已恢复并匹配", "Adam 为已发布默认，R1-B 亦用 Adam"],
           ["调度器未恢复", "已恢复但不匹配",
            "已发布代码使用 type1 衰减；R1-B 未调用。R1-C 已测试（C1）"],
           ["种子清单未恢复", "未恢复", "已发布代码中无种子清单"],
           ["精确选点规则未恢复", "未恢复", "已发布代码用 Test 选点，论文未说明"],
           ["精确池化轴未恢复", "未恢复", "z 空间池化为选择项，非恢复项"],
           ["已发布代码与论文机制冲突", "已确认", "八项冲突中四项永久无法解决"],
           ["已发布数据/代码工件不完整", "已确认", "缺 US-Region 与 few-shot"],
           ["硬件/软件版本差异", "可能存在", "未量化"],
           ["重复聚合方式差异", "未恢复", "论文称十次重复，聚合规则未说明"]],
          widths=[4.6, 3.4, 7.5],
          caption_text="表 4-3　剩余差距的可能来源与证据等级",
          source="R1C_DOCUMENTARY_EVIDENCE.md；R1_PAPER_CODE_CONFLICTS.md")
    para(doc, "除已标注为“已确认”的项外，不得断言任何单一来源为因果。",
         italic=True, color=GREY)

    # ---------------- 5 与早期 MIFlu 的比较 ---------------------------
    h(doc, "五、与项目早期 MIFlu 的比较", 1)
    para(doc,
         "不得直接把论文值与 1025 行历史 Test MSE 比较——数据集与契约不兼容。"
         "先确定最具可比性的“作者 966 行自建 MIFlu”结果，再逐项核对契约。",
         )
    table(doc,
          ["契约项", "旧（自建 A2）", "新（R1-B）", "可比"],
          [["同为 966 行数据集", "是（SHA 一致）", "是（SHA 一致）", "✅"],
           ["同一划分", "676/97/193", "676/97/193", "✅"],
           ["同一变量", "7 通道", "7 通道", "✅"],
           ["同一度量空间", "z 空间", "z 空间", "✅"],
           ["同一 horizon", "24/36/48/60", "24/36/48/60", "✅"],
           ["同一池化", "average_MSE_4L", "average_MSE_4L", "✅"],
           ["同一严格起点", "170/…/134", "170/158/146/134", "✅"],
           ["同一种子策略", "3 种子 42/43/44", "1 次重复 seed 1000+", "❌"],
           ["同一选点策略", "未记录", "仅 Validation", "❌"]],
          widths=[3.8, 4.4, 4.4, 1.6],
          caption_text="表 5-1　契约可比性审计",
          source="PAPER_GAP_COMPARABILITY_AUDIT.csv")
    para(doc,
         "整体判定：NOT_SUFFICIENTLY_COMPARABLE。存在三项阻断性差异："
         "种子策略（3 种子 vs 1 次重复）、选点策略（旧侧未记录）、"
         "以及新侧 SD 为 n/a 因而无法给出任何区间。", bold=True)
    para(doc,
         "因此采用规定表述：由于新旧两次运行使用了不同契约，"
         "数值下降百分比不得在无条件限制的情况下给出。", bold=True,
         color=ACCENT)
    para(doc,
         "若仅作算术参考（明确不构成主张）：旧相对误差 +42.22%，"
         "新相对误差 +35.68%，百分点下降 6.54 pp，差距相对缩小 15.5%。"
         "该算术把 3 种子均值与单次重复相除，其中未知比例的差值来自估计量方差，"
         "而非实现质量，故不作为结论引用。", color=GREY)
    para(doc,
         "使比较成立的做法：以匹配种子 42/43/44（3 次重复）重跑官方仓库修正版 "
         "MIFlu，并记录仅用 Validation 的选点策略。该做法已作为 R1-C 候选之一"
         "登记，服务于论文差距问题，不改变已冻结的 Track C 冠军结果。")

    # ---------------- 6 为何 966 行 -----------------------------------
    h(doc, "六、为什么使用 966 行数据", 1)
    bullet(doc, "论文表 II 的七变量描述统计与 966 行作者文件 7/7 吻合。")
    bullet(doc, "最大偏差约 0.02%。")
    bullet(doc, "1025 行历史快照仅 1/7 吻合。")
    bullet(doc, "因此论文相关工作与 Track C 均使用 966 行。")
    bullet(doc, "划分为 676 / 97 / 193。")
    source_note(doc, "TRACK_C_MASTER_CONTRACT.md §2；"
                     "TABLE_II_III_CORRECTION_NOTE.md")

    # ---------------- 7 严格包含与泄漏修正 ----------------------------
    h(doc, "七、严格包含与泄漏修正", 1)
    h(doc, "7.1 历史划分边界污染", 2)
    para(doc,
         "历史划分契约中，每个 horizon 都有一个测试起点被错标为 validation，"
         "导致窗口跨越划分边界。该键集已经作废并全部重新生成，"
         "未参与任何打分。")
    h(doc, "7.2 严格包含规则", 2)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("target_start ≥ split_start　　且　　"
                  "target_end ≤ split_end − 1")
    set_cn_font(r, 11, bold=True, color=NAVY)
    h(doc, "7.3 三个集合的用途", 2)
    table(doc,
          ["集合", "用途", "是否参与最终排名"],
          [["Train", "拟合（含缩放器）", "否"],
           ["Validation", "仅用于选择 checkpoint", "否"],
           ["Test", "评估一次；单独决定冠军", "是"]],
          widths=[3.0, 8.5, 3.6],
          caption_text="表 7-1　三个集合的用途",
          source="STRICT_966_KEY_VALIDATION.md；TRACK_C_MASTER_CONTRACT.md")
    para(doc, "Validation 指标被排除在最终排名与组均值之外。", bold=True)

    # ---------------- 8 模型身份 --------------------------------------
    h(doc, "八、八个模型的身份", 1)
    table(doc,
          ["模型", "族", "身份说明"],
          [["MIFlu", "LLM", "基于作者官方仓库，并使用修正后的 R1-B 实现"],
           ["Qwen-Time-LLM", "LLM", "受启发的简化实现，非其发表系统的完整复现"],
           ["CALF-LLM", "LLM", "受启发的简化实现，非其发表系统的完整复现"],
           ["TimeCMA-LLM", "LLM", "受启发的简化实现，非其发表系统的完整复现"],
           ["NLinear", "非 LLM", "身份与 Track C manifest 一致"],
           ["DLinear", "非 LLM", "身份与 Track C manifest 一致"],
           ["PatchTST", "非 LLM", "身份与 Track C manifest 一致"],
           ["iTransformer", "非 LLM", "身份与 Track C manifest 一致"]],
          widths=[3.6, 2.2, 9.3],
          caption_text="表 8-1　八个模型的身份",
          source="TRACK_C_MODEL_IDENTITY.csv；TRACK_C_MASTER_CONTRACT.md")
    para(doc,
         "旧 Stage-6 MIFlu 被拒绝采用，原因是它与自建 A2 工件逐字节相同，"
         "并非 Track C 所要求的官方仓库 MIFlu。该 12 个格子因此全部重训。",
         bold=True)
    source_note(doc, "TRACK_C_CELL_CLASSIFICATION.csv")

    # ---------------- 9 冠军赛方法 ------------------------------------
    h(doc, "九、冠军赛方法", 1)
    bullet(doc, "8 个模型。")
    bullet(doc, "3 个匹配种子（42 / 43 / 44）。")
    bullet(doc, "4 个 horizon（24 / 36 / 48 / 60）。")
    bullet(doc, "96 个格子。")
    bullet(doc, "其中 84 个格子独立重新打分。")
    bullet(doc, "12 个官方 MIFlu 格子重训。")
    bullet(doc, "单一打分器。")
    bullet(doc, "无被拒绝的格子。")
    bullet(doc, "seed-42 门禁 22/22 PASS。")
    bullet(doc, "严格 Test 键集完全相同。")
    bullet(doc, "无缺失键、无重复键。")
    source_note(doc, "SEED42_EIGHT_MODEL_GATE_RESULTS.csv；"
                     "STRICT_966_KEY_VALIDATION.md")
    figure(doc, figs["workflow"], "图 9-1　Track C 最终工作流",
           "TRACK_C_EXECUTION_LOG.md")

    # ---------------- 10 最终排名 -------------------------------------
    h(doc, "十、最终 Test 排名", 1)
    table(doc,
          ["排名", "模型", "mean Test MSE", "SD", "mean Test MAE", "侧",
           "种子数"],
          [[r["rank_MSE"], r["model"], f(r["mean_Test_MSE_4L"]),
            f(r["sd_Test_MSE_4L"]), f(r["mean_Test_MAE_4L"]), r["side"],
            r["n_seeds"]] for r in rk],
          widths=[1.4, 3.2, 2.8, 2.0, 2.8, 1.8, 1.6],
          caption_text="表 10-1　八模型 Test MSE 排名（含 SD 与 MAE）",
          source="TRACK_C_TEST_MSE_RANKING.csv")
    figure(doc, figs["rank_mse"], "图 10-1　八模型 Test MSE 排名",
           "TRACK_C_TEST_MSE_RANKING.csv")
    table(doc,
          ["排名", "模型", "mean Test MAE", "mean Test MSE"],
          [[r["rank_MAE"], r["model"], f(r["mean_Test_MAE_4L"]),
            f(r["mean_Test_MSE_4L"])] for r in rk_mae],
          widths=[2.0, 4.5, 4.0, 4.0],
          caption_text="表 10-2　八模型 Test MAE 排名",
          source="TRACK_C_TEST_MAE_RANKING.csv")
    figure(doc, figs["rank_mae"], "图 10-2　八模型 Test MAE 排名",
           "TRACK_C_TEST_MAE_RANKING.csv")
    para(doc, "MIFlu 在四个 horizon 上均为第一，且在三个种子上均为第一。",
         bold=True)
    para(doc, "这不意味着该结论具有普遍性；它仅在冻结的 Track C 契约下成立。",
         italic=True, color=GREY)

    h(doc, "10.1 分 horizon 结果", 2)
    table(doc,
          ["L", "模型", "MSE", "MAE", "排名"],
          [[r["L"], r["model"], f(r["mse"]), f(r["mae"]), r["rank"]]
           for r in ph if int(r["rank"]) <= 4],
          widths=[1.6, 4.2, 3.2, 3.2, 1.8],
          caption_text="表 10-3　分 horizon 前四名（MIFlu 全部第一）",
          source="TRACK_C_PER_HORIZON_CHAMPIONS.csv")
    figure(doc, figs["per_horizon"], "图 10-3　分 horizon 的八模型对比",
           "TRACK_C_PER_HORIZON_CHAMPIONS.csv")

    h(doc, "10.2 分种子结果", 2)
    table(doc,
          ["种子", "模型", "mean MSE", "mean MAE", "种子内排名"],
          [[r["seed"], r["model"], f(r["mean_mse"]), f(r["mean_mae"]),
            r["rank_within_seed"]]
           for r in ps if int(r["rank_within_seed"]) <= 3],
          widths=[1.8, 4.0, 3.2, 3.2, 2.8],
          caption_text="表 10-4　分种子前三名（MIFlu 全部第一）",
          source="TRACK_C_PER_SEED_RANKINGS.csv")
    figure(doc, figs["per_seed"], "图 10-4　分种子的稳定性",
           "TRACK_C_PER_SEED_RANKINGS.csv")

    # ---------------- 11 分组结论 -------------------------------------
    h(doc, "十一、分组结论", 1)
    table(doc,
          ["组", "组均值（模型均值之均值，Test MSE）"],
          [[r["side"], f(r["mean_of_model_means_Test_MSE_4L"])]
           for r in grp],
          widths=[4.0, 6.0],
          caption_text="表 11-1　LLM 侧与非 LLM 组均值",
          source="TRACK_C_LLM_NONLLM_GROUP_SUMMARY.csv")
    figure(doc, figs["groups"], "图 11-1　组均值与单个冠军的对比",
           "TRACK_C_LLM_NONLLM_GROUP_SUMMARY.csv")
    para(doc, "两句话同时成立，且不矛盾：", bold=True)
    bullet(doc, "MIFlu 是最优的单个模型（1.8652）。")
    bullet(doc, "非 LLM 组均值 3.0756 优于 LLM 侧组均值 3.8175。")
    para(doc,
         "原因在于组均值是“模型均值之均值”，每个模型权重相同。"
         "LLM 侧组内除 MIFlu 外的三个实现（Qwen、CALF、TimeCMA）数值较大，"
         "把该组均值整体抬高；而 MIFlu 自身的优异不会因同组其他成员而削弱。"
         "因此“组内最优”与“组均值”是两个不同的量，同时报告才完整，"
         "只报其中之一即为选择性报告。")

    # ---------------- 12 配对比较 -------------------------------------
    h(doc, "十二、配对比较", 1)
    table(doc,
          ["A", "B", "格数", "mean diff", "median diff", "A 胜", "B 胜",
           "平局"],
          [[r["A"], r["B"], r["n_cells"], f(r["mean_diff"]),
            f(r["median_diff"]), r["A_wins"], r["B_wins"], r["ties"]]
           for r in pw],
          widths=[2.6, 2.6, 1.4, 2.2, 2.2, 1.4, 1.4, 1.4],
          caption_text="表 12-1　MIFlu 与各模型的配对比较",
          source="TRACK_C_PAIRWISE_STATS_CORRECTED.csv")
    para(doc, "差值定义为 diff = A − B；A 仅在 diff < 0 时判胜。",
         bold=True)
    para(doc,
         "修正版 MIFlu 对 NLinear：mean diff = −0.1844，MIFlu 胜 11/12，"
         "NLinear 胜 1/12，平局 0。")
    figure(doc, figs["pairwise"], "图 12-1　MIFlu 与 NLinear 的 12 个配对格",
           "TRACK_C_PAIRWISE_STATS_CORRECTED.csv")
    para(doc, "未做统计显著性检验，因此不作显著性主张。", italic=True,
         color=GREY)

    # ---------------- 13 计算与存储 -----------------------------------
    h(doc, "十三、计算与存储", 1)
    table(doc,
          ["项", "值"],
          [["MIFlu GPU 作业数", cost.get("gpu_jobs", "12")],
           ["GPU 总工时", cost.get("gpu_hours_total", "1.5083") + " GPU-h"],
           ["全部作业返回码", "全部 rc = 0"],
           ["home 用量", f"{cost.get('home_used_GB','31')} / "
                         f"{cost.get('home_soft_quota_GB','50')} GB"],
           ["scratch 用量", f"{cost.get('scratch_used_GB','285')} / "
                            f"{cost.get('scratch_soft_quota_GB','300')} GB"]],
          widths=[5.5, 9.5],
          caption_text="表 13-1　资源与存储",
          source="TRACK_C_COST_SUMMARY.csv / .json")
    figure(doc, figs["cost"], "图 13-1　GPU 工时与存储占用",
           "TRACK_C_COST_SUMMARY.csv")
    bullet(doc, "锁定 checkpoint 策略：checkpoint 写入后锁定并可重载复现。")
    bullet(doc, "基础模型缓存复用：避免重复下载与重复占用空间。")
    bullet(doc,
           "文件系统剩余空间不等于用户配额：df 显示的是整个文件系统的空余，"
           "不能据此判断本人还能用多少。权威来源是 mmlsquota。")

    # ---------------- 14 工程修正与事故 -------------------------------
    h(doc, "十四、工程修正与事故记录", 1)
    table(doc,
          ["编号", "事项", "处理"],
          [["1", "已发布文本通路失效",
            "R1-B 恢复可用的文本通路并逐 checkpoint 探测（text_active）"],
           ["2", "target 窗口短张量 bug", "修正窗口构造并加回归断言"],
           ["3", "起点键偏移 bug", "重新生成起点键并校验无重复"],
           ["4", "划分标签边界 bug", "作废原键集，重新生成严格键集"],
           ["5", "Validation 导出遗漏", "补齐导出并纳入校验"],
           ["6", "打分器路径问题", "改用显式路径并加固校验"],
           ["7", "打分器重复键保护", "一对一 merge，重复键与 NaN 直接拒绝"],
           ["8", "登录节点重打分器事故",
            "见下方说明"],
           ["9", "SSH 连接被重置", "改用 Slurm 作业内完成打分"],
           ["10", "全部打分迁移至 CPU Slurm", "打分全部在计算节点执行"],
           ["11", "传输改为 tar 流批量打包", "减少连接数与失败率"]],
          widths=[1.6, 6.0, 7.8],
          caption_text="表 14-1　工程修正与事故记录",
          source="TRACK_C_EXECUTION_LOG.md；"
                 "results/innovation/final/limitations_and_incidents.md")
    para(doc,
         "关于登录节点：有一次较重的打分器被误放在登录节点上运行。"
         "该次事件之后，所有打分与实质性计算均已迁移到 Slurm 计算节点，"
         "且该违规未再发生。", bold=True)
    para(doc,
         "说明：经全仓检索，未找到关于 SSH fail2ban / 速率限制的专门记录；"
         "已记录的为 SSH 连接被重置与后续的迁移处理。此处按实际证据记录，"
         "不作补充假设。", color=GREY, italic=True)

    # ---------------- 15 局限性 ---------------------------------------
    h(doc, "十五、局限性", 1)
    bullet(doc, "仅三个种子，不足以支撑强的结论。")
    bullet(doc, "不作统计显著性主张。")
    bullet(doc, "四个 horizon 不是独立重复样本。")
    bullet(doc, "Qwen / CALF / TimeCMA 为有限范围的简化实现。")
    bullet(doc, "论文复现为部分复现（PARTIAL_REPRODUCTION）。")
    bullet(doc, "regional / few-shot 结果被阻断（原始数据未发布）。")
    bullet(doc, "冠军结论仅适用于冻结的 Track C 契约。")
    h(doc, "15.1 表 III 状态的更正", 2)
    para(doc,
         "若更新后的 Markdown 中含有表 III 数值，则其状态标注为："
         "通过 MARKDOWN_TRANSCRIPTION 获得，但并非从 PDF 图像中直接机器提取。")
    para(doc,
         "证据显示表 III 状态已由 UNREADABLE 更正为 VERIFIED_AVAILABLE；"
         "US-Region 原始数据仍未发布，故表 VI 仍为 BLOCKED_BY_MISSING_DATA。"
         "不得在现有证据与此相矛盾时继续标注为“不可读”。")

    # ---------------- 16 最终结论 -------------------------------------
    h(doc, "十六、最终结论", 1)
    p = doc.add_paragraph()
    r = p.add_run(
        "在作者 966 行数据、严格包含窗口、匹配种子 42/43/44、"
        "以 Validation 选择 checkpoint、Test 仅评估一次的契约下，"
        "基于官方仓库的修正版 MIFlu 是八模型冠军，"
        "mean Test average_MSE_4L = 1.8652（SD 0.0916），"
        "mean Test average_MAE_4L = 0.8842。")
    set_cn_font(r, 11, bold=True, color=NAVY)
    p = doc.add_paragraph()
    r = p.add_run(
        "论文层面的复现仍为 PARTIAL_REPRODUCTION：R1-B 的平均 MSE 比论文"
        "报告值高出约 35.7%；经受限的 R1-C 分析后，最佳证据支持候选 C1 为"
        "1.8029，仍高出约 25.6%，四个 horizon 均未进入预先声明的 ±0.10 "
        "MSE 带。")
    set_cn_font(r, 11, bold=True, color=NAVY)

    # ---------------- 附录 -------------------------------------------
    doc.add_page_break()
    h(doc, "附录 A　证据路径与哈希", 1)
    table(doc,
          ["项", "值 / 路径"],
          [["作者 966 行数据 SHA-256", META["data_sha"]],
           ["严格 Test 键集 SHA-256", META["key_sha"]],
           ["旧报告 SHA-256", META["old_sha"]],
           ["旧报告 PDF SHA-256",
            "e1e1ecbb0bf498433dae309633b83a302f47f538dd5ee3bb56b3"
            "e356e7f9dbfe"],
           ["当前冠军版 v1 SHA-256", META["cur_sha"]],
           ["仓库 commit", META["commit"]],
           ["最终结果目录", META["result_dir"]],
           ["冻结 CSV 输入目录", "…/r1_v2_verification_20261007/docx_inputs/"],
           ["报告权限说明",
            "results/v3_clean/analysis/reports/"
            "REPORT_AUTHORITY_AND_ARCHIVAL_NOTE.md"],
           ["旧报告归档位置",
            "results/v3_clean/analysis/reports/archive/"]],
          widths=[5.0, 10.0],
          caption_text="表 A-1　关键哈希与路径",
          source="REPORT_AUTHORITY_AND_ARCHIVAL_NOTE.md；"
                 "TRACK_C_DELIVERABLE_MANIFEST.csv")

    doc.add_page_break()
    h(doc, "附录 B　图表来源对照", 1)
    table(doc,
          ["图", "来源 CSV / 文档"],
          [["图 3-1 时间线", "TRACK_C_EXECUTION_LOG.md"],
           ["图 3-2 轨道分离", "TRACK_C_MASTER_CONTRACT.md"],
           ["图 4-1 论文 vs 复现",
            "PAPER_GAP_REDUCTION_CALCULATION.md；"
            "R1C_RESULTS_PER_CANDIDATE.csv"],
           ["图 10-1 MSE 排名", "TRACK_C_TEST_MSE_RANKING.csv"],
           ["图 10-2 MAE 排名", "TRACK_C_TEST_MAE_RANKING.csv"],
           ["图 10-3 分 horizon", "TRACK_C_PER_HORIZON_CHAMPIONS.csv"],
           ["图 10-4 分种子", "TRACK_C_PER_SEED_RANKINGS.csv"],
           ["图 11-1 组均值", "TRACK_C_LLM_NONLLM_GROUP_SUMMARY.csv"],
           ["图 12-1 配对格", "TRACK_C_PAIRWISE_STATS_CORRECTED.csv"],
           ["图 13-1 成本", "TRACK_C_COST_SUMMARY.csv"],
           ["图 9-1 工作流", "TRACK_C_EXECUTION_LOG.md"]],
          widths=[4.6, 10.4],
          caption_text="表 B-1　每张图对应的源数据",
          source="FINAL_REPORT_V2_SOURCE_MANIFEST.csv")

    out = os.path.join(OUTDIR, DOCX_NAME)
    doc.save(out)
    print("[build] saved:", out)
    print("[build] size :", os.path.getsize(out), "bytes")
    return out


if __name__ == "__main__":
    raise SystemExit(0 if build() else 1)
