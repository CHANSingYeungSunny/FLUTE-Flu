# PAPER_TO_CODE

Status: **verification_level = unverified** for the paper text and the official repository commit.

| Paper claim | Official code | Local code | Discrepancy | Evidence depth |
|---|---|---|---|---|
| 10 repetitions, seeds unspecified | not pinned | 10 seeds 2021-2030 in `train_miflu.py` | seed labels are the project's, not proven the paper's | static only |
| checkpoint selected on test | `main_ILI_lora.py` lines 211/225 (reported) | validation selection in `train_miflu.py` | disclosed deviation | reported, not re-read here |
| 7-variable aggregate metric | not pinned | `eval_windows.py --n_vars 7` | original loader reportedly 1 variable | static |
| T/L semantics | not pinned | T=104, L=24/36/48/60 | none observed | static |

The MIFlu PDF was not opened in this session; the official repository commit was not pinned.
Do not upgrade this table to verified without the PDF and a commit hash.


## RE-CHECK NOTE (2026-11-04)

This table remains `unverified`: the paper PDF and a pinned official commit were still not opened. The row claiming test-set checkpoint selection is a reported reading, not a re-verified one. Do not state as fact that the original authors leaked test data, and do not assert the paper covers only two evaluation dimensions, until the full text and a commit hash are read.

---

## v8 provenance update (applied 2026-11-06)

This file is the v8 copy. The v7 original at
`HANDOFF_20261105/v7/RETURN_V7/PAPER_TO_CODE.md` is preserved byte-identical.
The v8 builder deliberately prefers this file over the v7 skeleton when
assembling `RETURN_V8/PAPER_TO_CODE.md`, so TASK 5 step 4 ("update
`PAPER_TO_CODE.md`/manuscript provenance") is satisfied without touching frozen
v7 evidence.

## JBHI author-guidance verification (2026-11-06)

On 2026-11-06 the official IEEE JBHI author guidance was verified against live
pages (HTTP 200 observed): https://www.embs.org/jbhi/prepare-and-submit-your-manuscript/
and the IEEE-wide AI policy
https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/ .
Verified items: 14-page regular / 16-page review page limit including supplementary
material (applies to original AND revised submissions); abstract not more than 250
words; IEEE single-spaced, double-column format with embedded figures and tables;
hybrid open access with US$2,800 APC for 2026 submissions (IEEE Member 5% / Society
Member 20% discounts, not combinable) and $110/$250/$350 voluntary-overlength page
charges; and the IEEE-wide requirement that AI-generated content (text, figures,
images, code) be disclosed in the acknowledgments section, identifying the AI system,
the specific sections used, and the level of use (grammar/editing assistance is
recommended-but-not-required disclosure). This is an IEEE-wide policy, not a
JBHI-specific clause. A third-party mirror (eshukan.com) still shows an outdated
12/14-page limit and must not be used.

UNVERIFIED: no official IEEE JBHI template class file (.cls / Word / ZIP) could be
downloaded. The template selector deep link
https://template-selector.ieee.org/secure/templateSelector/publicationType returned
HTTP 404 to a browser client and HTTP 418 to a bot-like client (a UA/header-dependent
WAF block, not a missing page); /secure/downloadTemplate and
/latex-for-ieee-journals.zip returned 404; /api/ieee-template-selector returned 302
then 502. No template file was obtained, so the exact JBHI LaTeX/Word class to use
remains unverified.

This 2026-11-06 guidance check is documentation only. It does NOT make the
manuscript submission-ready: the required official template class file is still
unavailable/unverified, and no claim of submission readiness is made here.
