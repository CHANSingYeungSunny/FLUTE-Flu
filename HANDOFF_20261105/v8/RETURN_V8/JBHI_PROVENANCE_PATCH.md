# JBHI_PROVENANCE_PATCH

**Proposed provenance text for `PAPER_TO_CODE.md` / manuscript provenance — NOT YET APPLIED.**

- **Date:** 2026-11-06
- **What this is:** the exact, paste-ready block to append to the manuscript provenance / `PAPER_TO_CODE.md`.
- **Scope discipline:** this task did **not** edit any existing `PAPER_TO_CODE.md`. Known copies (left untouched, byte-identical):
  - `handoffs/20261105_return/PAPER_TO_CODE.md`
  - `HANDOFF_20261105/v7/RETURN_V7/PAPER_TO_CODE.md`
- The block below is the **only** content proposed for insertion. Full evidence: `HANDOFF_20261105/v8/JBHI_VERIFICATION_20261106.md`.

---

## Paste-ready block (copy everything inside the fence)

```
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
```

---

## Notes for the person applying the patch

- Append the fenced block verbatim to the end of `PAPER_TO_CODE.md`; keep the existing `verification_level = unverified` status and the 2026-11-04 re-check note intact.
- Do **not** upgrade the main `PAPER_TO_CODE` table to `verified`; this patch concerns **submission guidance**, not the paper-text/code provenance that the table tracks.
- The phrase "does NOT make the manuscript submission-ready" is deliberate and must be preserved (TASK 5 / AGENTS.md RULE 5: no fabricated readiness).
- Do not invent a template class file, a download URL, or a status code that was not observed (see `JBHI_VERIFICATION_20261106.md` §2–§3 for the exact codes).
