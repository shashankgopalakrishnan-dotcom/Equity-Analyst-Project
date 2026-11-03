# FIN 67110 — Week 2

**Updated:** November 2, 2026
**Official page:** [Week 2 — The Desk, Then Make It Yours](https://cinderzhang.github.io/FIN67110-Fall2026/week-02/index.html)

## Status

- **Lab 02 program:** Created in `desk.py`. It follows the SEC filings, XBRL facts, arithmetic, earnings release, and peer comparison steps. Runs completed for Costco and Walmart.
- **Implementation update:** XBRL candidate tags for each measure are now limited to tags that contain the revenue fiscal year, while keeping prior annual facts for comparison. Step 7 now prints the selected current and prior facts for every peer, as well as the operating margin.
- **Source folders:** Original Costco and Walmart runs are [`COSTCO_WHOLESALE_CORP_NEW_20261026_220708_EDT`](runs/COSTCO_WHOLESALE_CORP_NEW_20261026_220708_EDT/) and [`Walmart_Inc._20261026_220827_EDT`](runs/Walmart_Inc._20261026_220827_EDT/). After the implementation update, the seven-step Costco command completed in [`COSTCO_WHOLESALE_CORP_NEW_20261026_223242_EDT`](runs/COSTCO_WHOLESALE_CORP_NEW_20261026_223242_EDT/). This latest output includes all nine facts, prior-year values, calculations, release lines, and selected peer facts. The earlier run and first unsuccessful Walmart attempt are retained as troubleshooting history.
- **Repository facts:** The full SEC Company Facts files for Costco and Walmart are now included in those two run folders and pushed. `.gitignore` continues to ignore new fact exports by default; those two course files were explicitly included.
- **Course audit:** The user confirmed their review of the filing findings and corrected drafts for all seven reports, and the CMG Lab 02 and Lab 03 checks, on November 2, 2026. The original run still has the errors listed in the worksheet; the corrected draft addresses them.
- **Lab 03 reports:** On November 1, 2026, the app completed sequential runs for COST, WMT, TGT, BJ, AAPL, and MSFT using the `qwen3:8b` override. CMG was the partner-selected ticker. The audit findings and corrected-draft paths are in [`LAB03_ALL_TICKERS_RUN_STATUS.md`](LAB03_ALL_TICKERS_RUN_STATUS.md).
- **Partner and Brightspace work:** The partner's two Lab 02 marks and two CMG Lab 03 claim checks are confirmed and recorded in [`AUDIT_TEMPLATE.md`](AUDIT_TEMPLATE.md). The user also explained the Lab 03 reflection to the partner. Submit Checkpoint 1 in Brightspace with a commit link the grader can access.
- **Current repository status:** Public repository; desk, partner-picked CMG report, audit records, and partner-check status are pushed. Keep `.env`, the supplied PDFs, `.vscode/`, and `CONVERSATION.md` out of the repository.

## Lab 02 evidence

The script uses only Python's standard library. It reads `SEC_USER_AGENT` from `.env`; it does not read `API_KEY`.

### Costco (`COST`)

- 10-K accession: `0000909832-26-000093`, accepted `2026-10-07T01:13:15Z`; fiscal year ended `2026-08-30`.
- 10-Q accession: `0000909832-26-000051`, accepted `2026-06-03T20:43:00Z`.
- Latest earnings 8-K: `0000909832-26-000084`, accepted `2026-09-24T20:17:37Z`, Items 2.02 and 9.01. Exhibit 99.1: `costex9918-k92426.htm`.
- Annual total revenue: `$303,154m` using `RevenueFromContractWithCustomerExcludingAssessedTax` (the newer fact); operating income `$11,685m`; net income `$9,226m`; diluted EPS `$20.76`.
- Calculated revenue growth `10.14%`; operating margin `3.85%`; return on average equity `28.40%`; debt/equity `17.21%`; free cash flow `$9,382m`.
- Latest-quarter release lines: total revenue `$95,723m`; diluted GAAP EPS `$6.75`.
- Saved numbered filing text was manually compared with the 10-K and release statement lines. Total revenue, net sales, membership fees, operating income, net income, diluted EPS, equity, current and long-term debt, operating cash flow, and additions to property/equipment were checked. The full hand-audit checklist remains open.
- Lab 03 used the September 23, 2026 close of `$904.70` (last close before the September 24 release); its P/E is `43.58x`. The report and original model draft are saved in run folder `COSTCO_WHOLESALE_CORP_NEW_20261026_221745_EDT`.

### Walmart (`WMT`)

- 10-K accession: `0000104169-26-000055`, accepted `2026-03-13T20:06:24Z`; fiscal year ended `2026-01-31`.
- 10-Q accession: `0000104169-26-000154`, accepted `2026-08-28T20:11:28Z`.
- Latest earnings 8-K: `0000104169-26-000145`, accepted `2026-08-20T10:59:01Z`.
- Annual revenue: `$713,163m`; operating income `$29,825m`; operating margin `4.18%`.
- Latest-quarter release lines: total revenue `$187,937m`; diluted EPS `$0.80` for the three months ended July 31, 2026.
- Saved release table confirms Walmart total revenue includes net sales plus membership and other income. The latest 10-K numbers and the matching XBRL tags still need the student's manual line-by-line check.

All amounts above are USD millions except per-share data and percentages. Recheck the units and periods in each cited source before using them in a report.

## Lab 02: instructions and human checks

Official instructions: [Lab 02 — The Desk's Steps](https://cinderzhang.github.io/FIN67110-Fall2026/week-02/lab-02-desk-on-one-page.html).

- [ ] Match the CIK, filing accessions, acceptance times, and Item 2.02 status to SEC EDGAR.
- [ ] Check every selected XBRL tag, unit, form, accession, and period against the annual report. Costco's total revenue includes net sales plus membership fees; Walmart's includes net sales plus membership and other income.
- [ ] Redo revenue growth, operating margin, return on average equity, debt/equity including current debt, and free cash flow by hand.
- [ ] Match quarter revenue and diluted EPS to the earnings releases.
- [ ] Match peer revenue and operating income to each peer's latest 10-K and use one margin definition.
- [ ] Mark all seven Lab 02 checks on the class worksheet; explain the XBRL tag and period issue; complete the separate Lab 02 reflection.
- [x] Partner checked two Lab 02 marks (COST Steps 5 and 6). Record and sources are in [`PEER_REPORT_FROM_PARTNER.md`](PEER_REPORT_FROM_PARTNER.md).

The script reads `acceptanceDateTime` from the SEC submissions API. The SEC archive directory index provides the filing document list, but does not show an “Accepted” timestamp in its page text. Compare the API timestamp with the SEC filing record when completing the course check.

### Lab 02 commands

No packages need to be installed; `desk.py` uses only the Python 3.12 standard library. From the workspace folder, run the Costco example with peers and the September 23, 2026 close used for the Lab 03 example:

```sh
python3.12 WEEK_2/desk.py COST --peers WMT,TGT,BJ --price 904.70
```

The SEC User-Agent must be set in the local `.env` file. Do not upload that file.

The expected in-class demo is `COST --peers WMT,TGT,BJ --price P`. Replace `P` with the instructor's close; do not guess a price. The Week 2 page defines the valuation price as the last close before the earnings release, with its date, from an exchange or LSEG Workspace. Example local command after setting `SEC_USER_AGENT` in `.env`:

```sh
python3.12 WEEK_2/desk.py COST --peers WMT,TGT,BJ
```

To focus on one step, use `--step N`. Steps 4–7 also fetch the filings and facts they need before showing the selected step. No model key is needed for Lab 02.

## Assigned readings and schedule

- [ ] Re-read Francis & Zhang (2026), Section 3.1 and Figure 2; keep Report A open.
- [ ] Read the [report audit checklist](https://cinderzhang.github.io/FIN67110-Fall2026/reference/audit-checklist.html).
- [ ] Watch the Karpathy talk linked from the [Week 1 page](https://cinderzhang.github.io/FIN67110-Fall2026/week-01/index.html); write where the autonomy slider is in the agent.
- **Kim, Muhn & Nikolaev (2024):** The linked arXiv record now says the paper is withdrawn. Its abstract describes the original paper; the results should not be presented as currently verified. Ask the instructor which version/table to use before writing the requested generalization sentence.
- **Supplementary PDF:** `JFQA-fire_sales-published.pdf` is a corporate bond liquidity paper, not on the listed Week 2 assigned-reading page. Brief notes are in [`PREP_NOTES.md`](PREP_NOTES.md); the source PDF stays local.
- Schedule shown on the course page: Session 2, Tuesday October 27, 2026; Session 3, Thursday October 29, 2026; Lab 03 and Checkpoint 1.

## Lab 03: status and next steps

Official instructions: [Lab 03 — The App](https://cinderzhang.github.io/FIN67110-Fall2026/week-02/lab-03-make-it-yours.html).

1. The API key and configured model ID are present locally. The model-list endpoint confirmed `qwen3-coder:latest` is available. Keep `.env` private.
2. The OpenAI SDK is installed in the ignored local `.venv` environment.
3. Costco's Lab 03 four-role report was generated. The original model output is `COST_lab03_model_draft.md`; the corrected review draft is `COST_lab03_report.md`.
4. **Student verification:** complete. The user confirms they reviewed the CMG audit and agrees with the findings recorded in [`AUDIT_TEMPLATE.md`](AUDIT_TEMPLATE.md).
5. The partner selected CMG. The report, audit, and partner checks are complete. The partner marks and source lines are in [`AUDIT_TEMPLATE.md`](AUDIT_TEMPLATE.md).
6. The partner reflection discussion is complete. Submit Checkpoint 1 in Brightspace with a commit link the grader can access. Confirm the grader can open the repository.

### Definition checks

- Costco total revenue includes net sales and membership fees; net sales alone is a different measure.
- State the denominator used for margins. Operating margin here is operating income divided by total revenue.
- Return on average equity uses the average of current and prior year-end equity.
- Debt/equity includes long-term debt and its current portion.
- Free cash flow here is cash from operations minus additions to property and equipment.
- The latest 8-K may not be the earnings release. Select the newest filing with Item 2.02.
- Confirm each XBRL period end matches the fiscal year and verify that the concept represents the requested item.

## References

- [Week 1 setup](../WEEK_1_SETUP.md)
- [Week 1 reading notes](../WEEK_1_READING_NOTES.md)
- [Workspace restart point](../RESTART_HERE.md)
- [Purdue GenAI Studio API documentation](https://docs.rcac.purdue.edu/services/genai/api/)
