# Lab 03 report run status

Updated: 2026-11-02

## Generated reports

The six existing Lab 02 runs were processed one at a time with `qwen3:8b`. Each report has the five required section headings, filing accessions, run time, price/date, and an AI-draft warning.

| Ticker | Report |
| --- | --- |
| COST | `WEEK_2/runs/COSTCO_WHOLESALE_CORP_NEW_20261027_092302_EDT/COST_lab03_report_20261101_093152.md` |
| WMT | `WEEK_2/runs/Walmart_Inc._20261026_220827_EDT/WMT_lab03_report_20261101_093313.md` |
| TGT | `WEEK_2/runs/TARGET_CORP_20261029_000915_EDT/TGT_lab03_report_20261101_093456.md` |
| BJ | `WEEK_2/runs/BJ_s_Wholesale_Club_Holdings_Inc._20261029_000808_EDT/BJ_lab03_report_20261101_093620.md` |
| AAPL | `WEEK_2/runs/Apple_Inc._20261027_093055_EDT/AAPL_lab03_report_20261101_093730.md` |
| MSFT | `WEEK_2/runs/MICROSOFT_CORP_20261029_000818_EDT/MSFT_lab03_report_20261101_093901.md` |

The partner selected **CMG**. Its seven-step Lab 02 run used peers MCD, YUM, and CAVA. Its Lab 03 report was generated on 2026-11-01:

`WEEK_2/runs/CHIPOTLE_MEXICAN_GRILL_INC_20261101_101158_EST/CMG_lab03_report_20261101_101604.md`

The run used the Financial Datasets closing price of `$27.98` on `2026-10-27`, the last close before the October 28 earnings release.

## Audit status

Filing reviews were prepared with AI support for all seven reports on 2026-11-02. **Student verification: complete on 2026-11-02.** The user confirms they reviewed and agree with the audit findings and corrected drafts for all seven reports. Audit notes and corrected drafts are saved beside each original report:

- COST audit: `WEEK_2/runs/COSTCO_WHOLESALE_CORP_NEW_20261027_092302_EDT/COST_lab03_audit_20261102.md`
- COST corrected draft: `WEEK_2/runs/COSTCO_WHOLESALE_CORP_NEW_20261027_092302_EDT/COST_lab03_reviewed_draft_20261102.md`
- CMG audit worksheet: `WEEK_2/AUDIT_TEMPLATE.md`
- CMG corrected draft: `WEEK_2/runs/CHIPOTLE_MEXICAN_GRILL_INC_20261101_101158_EST/CMG_lab03_reviewed_draft_20261102.md`
- WMT corrected draft: `WEEK_2/runs/Walmart_Inc._20261026_220827_EDT/WMT_lab03_reviewed_draft_20261102.md`
- TGT corrected draft: `WEEK_2/runs/TARGET_CORP_20261029_000915_EDT/TGT_lab03_reviewed_draft_20261102.md`
- BJ corrected draft: `WEEK_2/runs/BJ_s_Wholesale_Club_Holdings_Inc._20261029_000808_EDT/BJ_lab03_reviewed_draft_20261102.md`
- AAPL corrected draft: `WEEK_2/runs/Apple_Inc._20261027_093055_EDT/AAPL_lab03_reviewed_draft_20261102.md`
- MSFT corrected draft: `WEEK_2/runs/MICROSOFT_CORP_20261029_000818_EDT/MSFT_lab03_reviewed_draft_20261102.md`

The COST review found eight correct and three missing core claims. It corrected the missing-quarter metrics and invalid P/E-to-margin comparison in a separate draft. The CMG review found the `$11,925.6B` revenue and `$666.3B` capex displays are each 1,000x too high and corrected units and arithmetic in a separate draft. The other five audit findings and corrections are listed above. The user has verified and agrees with these filing-review findings. The partner's two-claim check and the partner reflection remain separate tasks.

The other five reports also received filing reviews against the saved run filings on 2026-11-02. Their audit notes are saved beside the reports:

- WMT: `WEEK_2/runs/Walmart_Inc._20261026_220827_EDT/WMT_lab03_audit_20261102.md` — eleven core values and periods match; citations and recommendation support need work.
- TGT: `WEEK_2/runs/TARGET_CORP_20261029_000915_EDT/TGT_lab03_audit_20261102.md` — ten core claims correct; Q2 diluted EPS is missing.
- BJ: `WEEK_2/runs/BJ_s_Wholesale_Club_Holdings_Inc._20261029_000808_EDT/BJ_lab03_audit_20261102.md` — eight correct; quarter labels/amount and diluted EPS need correction; peer comparison is invalid.
- AAPL: `WEEK_2/runs/Apple_Inc._20261027_093055_EDT/AAPL_lab03_audit_20261102.md` — ten correct; annual revenue growth is missing.
- MSFT: `WEEK_2/runs/MICROSOFT_CORP_20261029_000818_EDT/MSFT_lab03_audit_20261102.md` — eight correct; latest quarter is mislabeled, diluted EPS is missing, and the OpenAI attribution needs correction.

The five reviewed drafts incorporate the findings in their audit notes. The original reports remain unchanged. Review the drafts and select the reports required for submission.

Student verification of the seven report reviews and the CMG worksheet is complete. The CMG peer filing check for MCD, YUM, and CAVA is also complete; numbered peer filing texts and calculations are in `WEEK_2/CMG_LAB02_STEP7_PEER_CHECK.md` and the CMG run's `peers/` folders. The corrected Lab 03 CMG draft uses CMG's no-borrowings disclosure for 0.00x debt/equity.

Still pending:

- Record the partner's two Lab 2 marks and two CMG report-claim checks in `AUDIT_TEMPLATE.md`. A peer-check note has been received; confirm the partner's final marks and complete the worksheet fields.
- Complete the partner reflection.
- Partner-selected company: CMG. The data run, filing review, and student verification are complete. Record the partner's check of two claims.
- Complete the partner reflection and Brightspace Checkpoint 1 submission. Use a commit link the grader can access.

## Run details

- The six original runs and the CMG partner run completed sequentially on 2026-11-01. Five role calls completed in each run: Research Analyst, Financial Analyst, Investment Advisor, Strategy Manager, and Strategy Manager compile. No revision call was required by the manager response.
- The model override was `qwen3:8b`. The `.env` model setting was not changed.
- Prices are historical closes dated 2026-10-27 from the quotes already saved in each Lab 02 manifest. The report files state the price and date.
- Earlier failed attempts on 2026-10-29 are superseded by these successful generations.
- The selected reports and run artifacts were pushed earlier. Partner review notes were pushed in commit `278a105`. The repository is public. A Git-history scan found no credential-pattern matches. `.env`, PDFs, `.vscode/`, and `CONVERSATION.md` are not in the checked commit. Brightspace was not submitted.
- Keep `.env` private.
