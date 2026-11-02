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

These are generated drafts. The headings and report headers were checked. The financial claims, source-line citations, recommendation logic, and peer figures have not been fully audited against the filings. A spot review found issues to resolve: COST compares its P/E with peer operating-margin percentages; the BJ report labels peer values unclearly; some reports do not state all required quarter metrics clearly; and the CMG report has a clear 1,000x unit error. It writes `$11,925.6B` for annual revenue, while the saved XBRL fact is `$11,925,601,000` (about `$11.93B`), and it writes `$666.3B` for capex, while the saved fact is `$666,336,000` (about `$666.3M`). Do not submit these reports as audited work.

Still pending:

- Student hand audit of the eleven required claims and every other numeric claim in each report selected for coursework.
- Check source quotations and line numbers against the saved 10-K and earnings-release text.
- Check every peer number, label, fiscal period, and formula.
- Review recommendation and its stated deciding number.
- Partner-selected company: CMG. The data run and report are complete. The student must audit all eleven claims; the partner must check two claims.
- Complete the partner reflection and Brightspace Checkpoint 1 submission. Use a commit link the grader can access.

## Run details

- The six original runs and the CMG partner run completed sequentially on 2026-11-01. Five role calls completed in each run: Research Analyst, Financial Analyst, Investment Advisor, Strategy Manager, and Strategy Manager compile. No revision call was required by the manager response.
- The model override was `qwen3:8b`. The `.env` model setting was not changed.
- Prices are historical closes dated 2026-10-27 from the quotes already saved in each Lab 02 manifest. The report files state the price and date.
- Earlier failed attempts on 2026-10-29 are superseded by these successful generations.
- The selected reports and run artifacts were pushed to the private repository in commit `9bc9811`. A remote-tree check confirmed `.env`, PDFs, `.vscode/`, and `CONVERSATION.md` are absent. Brightspace was not submitted.
- Keep `.env` private.
