# T5_VERDICT — TASK 5 (JBHI verification)

```
status: COMPLETED
```

**Basis:** TASK 5 acceptance is "a dated verification record or a precise UNVERIFIED note". A dated, live-observed verification record **was produced** (`JBHI_VERIFICATION_20261106.md`), therefore the task itself is `COMPLETED`. The **template-download sub-item is `UNVERIFIED`** (see below); it is explicitly not claimed as verified.

```
template_download_status: UNVERIFIED
manuscript_submission_ready: NO
```

## Timing (UTC)

```
start_utc: 2026-11-06T13:20:29Z   # first T5 command (env / date / curl / v8 listing)
first_http_probe_utc: 2026-11-06T13:22:12Z
main_status_batch_utc: 2026-11-06T13:22:39Z -> 2026-11-06T13:22:57Z
verification_end_utc: 2026-11-06T13:29:00Z  # last verification command
end_utc: 2026-11-06T13:32:44Z    # file finalization (this verdict + hashes)
```

## Commands (exact, as run)

1. `date -u +"%Y-%m-%dT%H:%M:%SZ"` ; `curl --version | head -1` ; `ls -la "HANDOFF_20261105/v8/"` — env/version/dir check.
2. `find . -iname "PAPER_TO_CODE*" -type f` ; `find . -iname "*JBHI*"` ; `ls v8/evidence/ v8/scripts/` — read-only context.
3. `curl -s -o /dev/null -w "%{http_code}" --max-time 20 "https://www.embs.org/jbhi/prepare-and-submit-your-manuscript/"` — single connectivity probe.
4. Main batch: `check() { curl -s -o /dev/null -w "%{http_code}" --max-time 25 [-A "<UA>"] "$url"; }` over 11 URL/UA combinations (U1–U10, incl. two UA variants of the deep link). Full command and per-URL output reproduced in `JBHI_VERIFICATION_20261106.md` §6.
5. Reproducibility/forensics: 8x browser-UA deep link, 8x `python-requests/2.31.0`-UA-only deep link, 8x full python-requests default-header profile, header-isolation probes, native Python 3.13 `urllib` probe, 6x `/api` + `%{redirect_url}` + `curl -L -w "final_code=%{http_code} num_redirects=%{num_redirects}"`.
6. Verbatim-quote corroboration: `curl -s <URL> | python -c '<strip tags / html.unescape / collapse ws / phrase check>'` for the JBHI page (default UA) and the IEEE AI policy page (Chrome UA).
7. Templates-page link inventory: `curl -s <U4> | python -c '<regex href scan for template-selector / .cls|.zip|.docx|.tex>'`.
8. Mirror drift: `curl -s "https://eshukan.com/bd_show.aspx?cid=1&id=20553" | python -c '<context scan for 12 / 14 / page limit>'`.
9. Final re-confirm (`13:29:00Z`): three `curl ... -w "%{http_code}"` calls + `date -u`.
10. `wc -c` + `sha256sum JBHI_VERIFICATION_20261106.md JBHI_PROVENANCE_PATCH.md | awk '{print toupper($1)"  "$2}'` — output hashes.

## Exit codes

- Steps 1–3, 5, 7–10: shell exit code **0**.
- Step 4 (main batch): exit code **0**; every curl `rc=0` (network reachable for all 11 requests; no `not observed` status codes).
- Step 6 first attempt used native `urllib` to fetch the pages → `urllib.error.HTTPError: HTTP Error 403: Forbidden`, python exit **1** (site bot-blocks urllib). Method switched to `curl | python` pipe; rerun exit **0**, all quotes `FOUND`. This failed method and its reason are recorded, not hidden.
- Related: `python -c "import requests"` → `ModuleNotFoundError: No module named 'requests'`, exit **1** (requests not installed; the original python-requests client could not be run verbatim, so `418` was reproduced via curl with pyreq's default header set).
- One intermediate `curl -o /tmp/...` + `python` read produced a `FileNotFoundError` (Git Bash `/tmp` vs native Windows Python `C:\tmp` path mismatch); that sub-step's shell command still exited **0** and the check was correctly rerun via stdin pipe. Recorded for transparency.

## Output paths + sha256

All outputs written **only** into `HANDOFF_20261105/v8/`. No other file was created, modified, or deleted. Owner-edited files and other agents' `v8/evidence`, `v8/scripts` artifacts were left untouched.

| Output path | Bytes | SHA-256 (uppercase) |
|---|---|---|
| `HANDOFF_20261105/v8/JBHI_VERIFICATION_20261106.md` | 17044 | `24E2F553C17977D67F0743B811EA7F1D6699A22BDBACB86001395967AC3F9259` |
| `HANDOFF_20261105/v8/JBHI_PROVENANCE_PATCH.md` | 3434 | `724D5B98041BCE028A711E86670B5A67C006C427A883BCABB7C6757E46219D4C` |
| `HANDOFF_20261105/v8/T5_VERDICT.md` | (this file) | own SHA-256 is self-referential: computed after this file was finalized and **reported in the task final answer** rather than embedded here (embedding it would change its own hash). |

## Evidence

**VERIFIED — live HTTP 200 + verbatim quotes `FOUND`** (exact URLs and quotes in `JBHI_VERIFICATION_20261106.md` §1):
- `https://www.embs.org/jbhi/prepare-and-submit-your-manuscript/` → `200` (curl default UA, 242,519 B): page limit 14/16 incl. supplementary (original + revised), abstract ≤250 words, IEEE single-spaced double-column with embedded figures/tables, hybrid OA, US$2,800 APC (2026), IEEE Member 5% / Society Member 20% discounts (cannot be combined), $110/$250/$350 voluntary-overlength page charges. All 10 checked phrases `FOUND`.
- `https://journals.ieeeauthorcenter.ieee.org/become-an-ieee-journal-author/publishing-ethics/guidelines-and-policies/submission-and-peer-review-policies/` → `200`: IEEE-wide AI disclosure in acknowledgments + AI system/sections/level identified; grammar/editing exception (disclosure not required, recommended) `FOUND`. This is IEEE-wide, **not** a JBHI-specific clause.
- `https://open.ieee.org/author-guidelines-for-artificial-intelligence-ai-generated-text/` → `200` (2024-04-16 date from the 2026-11-06 research note; the date string itself `not observed` live).

**VERIFIED — status codes only (no document content):**
- `https://journals.ieeeauthorcenter.ieee.org/create-your-ieee-journal-article/authoring-tools-and-templates/tools-for-ieee-authors/ieee-article-templates/` → `200`; exactly one `template-selector` link (`https://template-selector.ieee.org/`), **no** `.cls/.zip/.docx/.tex` file links.
- `https://template-selector.ieee.org/` → `200` (SPA shell only).
- `https://template-selector.ieee.org/secure/templateSelector/publicationType` → `404` (browser UA 8/8; pyreq UA-string-only 8/8; urllib) and `418` (full python-requests default header profile 8/8) — **UA/header-profile-dependent WAF bot block, NOT a missing page** (see `JBHI_VERIFICATION_20261106.md` §2).
- `https://template-selector.ieee.org/api/ieee-template-selector` → `302` (6/6), `Location: http://tselpav21.awsi.ieee.org:8001/ieee-template-selector/`, `curl -L` final `502`, `num_redirects=1` (§3).
- `https://template-selector.ieee.org/secure/downloadTemplate` → `404`.
- `https://template-selector.ieee.org/latex-for-ieee-journals.zip` → `404`.
- `https://eshukan.com/bd_show.aspx?cid=1&id=20553` → `200`, body contains the **outdated** "12 pages for regular paper and 14 pages for review papers" limit → **version drift** recorded (official current = 14/16).

**UNVERIFIED (template download):**
- No official `.cls` / Word class file could be downloaded. Every candidate endpoint returned `404`, a WAF `418`, or a `302`→`502` chain. Exact URLs + codes above and in `JBHI_VERIFICATION_20261106.md` rows 9–11, §2–§3. The `418` is UA-dependent WAF blocking rather than a missing page.

**Integrity:** all status codes above were observed live on 2026-11-06; none invented. No `not observed` status codes in the main batch (all 11 reachable). Two earlier research-note codes were **refined** by observation: deep-link `418` requires the full pyreq header profile (UA string alone → `404`), and `/api` `502` is the post-`302`-redirect hop (direct → `302`).

**Not done (by explicit scope):** no existing `PAPER_TO_CODE.md` was edited; `JBHI_PROVENANCE_PATCH.md` contains the paste-ready proposed text only. No HPC/SLURM access used or needed. No manuscript, PPTX, frozen CSV, or prediction file touched.

## Remaining

- **Template class file:** still UNVERIFIED. Smallest next action: obtain the official IEEE JBHI LaTeX/Word template through a human browser session at `https://template-selector.ieee.org/` (the WAF blocks automated clients), then pin its exact filename + SHA-256 and record the download URL/status. Until then, do not assert a template was obtained.
- **Apply the provenance patch:** a human/owner must append the fenced block from `JBHI_PROVENANCE_PATCH.md` to `PAPER_TO_CODE.md` and the manuscript provenance; this task deliberately did not edit those files.
- **Do NOT call the manuscript submission-ready.** This verification is guidance documentation only; `manuscript_submission_ready: NO`.
- Downstream v8 tasks (TASK 7 documents, TASK 8 package) remain outside TASK 5 scope and were not started here.
