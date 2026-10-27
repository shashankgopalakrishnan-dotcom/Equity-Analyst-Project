# FIN 67110 — Week 2

**Prepared:** October 26, 2026
**Official page:** [Week 2 — The Desk, Then Make It Yours](https://cinderzhang.github.io/FIN67110-Fall2026/week-02/index.html)

## Week 2 goal

Build the desk's seven data steps from a ticker to SEC filings, XBRL facts, and ratios. Match each number to the filing. Then add four model roles, produce a five-part report, and audit the report by hand.

## Current status

- **Week 2 work:** Not started.
- **Lab 02:** Pending. It uses code and SEC data. It does not need a model API key.
- **Lab 03:** Pending. It needs an API key and the Lab 02 steps running on Costco and Walmart.
- **Lab 01 prerequisite:** `check_env.py` previously read the local `.env`. A screenshot exposed part of its API key. Revoke that key and replace it locally before Lab 03. Never put the replacement key in chat or GitHub.
- **GitHub status:** The supplied repository is private. The user has authorized adding Week 1 and Week 2 coursework files. Keep the repository private unless the user separately asks to change visibility. Never upload `.env`.

## Before Session 2 — about 60 minutes

- [ ] Finish any Lab 01 partner-check row that was not initialed. Debug with AI if needed.
- [ ] Watch the Karpathy talk linked on the [Week 1 page](https://cinderzhang.github.io/FIN67110-Fall2026/week-01/index.html). Write one line: where is the autonomy slider in your agent?
- [ ] Reread Francis & Zhang (2026), Section 3.1 and Figure 2. Keep Report A open.
- [ ] Read the [report audit](https://cinderzhang.github.io/FIN67110-Fall2026/reference/audit-checklist.html).
- [ ] Read the abstract and first results table of [Kim, Muhn, and Nikolaev (2024)](https://arxiv.org/abs/2407.17866). Write one sentence about why their reported edge might shrink on companies and years the model did not see.
- [ ] Open Costco's [latest 10-K list](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000909832&type=10-K&dateb=&owner=include&count=10) and [XBRL company facts](https://data.sec.gov/api/xbrl/companyfacts/CIK0000909832.json). Find net income attributable to Costco and diluted EPS in the 10-K. Find `EarningsPerShareDiluted` in company facts and check the same value, period, and filing.

## Session 2 — Lab 02: The Desk's Steps

Official instructions: [Lab 02 — The Desk's Steps](https://cinderzhang.github.io/FIN67110-Fall2026/week-02/lab-02-desk-on-one-page.html).

Build the program incrementally from the instructor's demo. It takes a ticker, optional peer tickers, optional price, and optional single-step selector. The code must not name a company. It reads `SEC_USER_AGENT` from `.env` and sends it with every SEC request. **No model key is needed for this lab.**

1. Resolve ticker to CIK with SEC `company_tickers.json`.
2. Read EDGAR submissions. Select the latest 10-K, latest 10-Q, and latest 8-K that reports Item 2.02. Print accession numbers and accepted times.
3. Download those filings and the 8-K's Exhibit 99.1. Convert them to plain text and save them in a company/date/time run folder.
4. Fetch XBRL facts for total revenue, operating income, net income, diluted EPS, stockholders' equity, long-term debt and current debt portion, cash from operations, and property/equipment additions. Print each tag, period end, and filing. Use facts for the same fiscal year as revenue, show the prior year, and select the newest valid candidate tag.
5. Compute and print the arithmetic for revenue growth, operating margin, return on average equity, debt/equity including current debt, free cash flow, and P/E when `--price` is supplied.
6. From the earnings release text, print the lines for latest-quarter total revenue and diluted EPS.
7. For every peer, retrieve the same facts and calculate operating margin on the same definition.

The expected demo command is `COST --peers WMT,TGT,BJ --price P`, where `P` is the instructor's closing price. Replace `P` with the demo value. Do not guess it. Follow the instructor's package-install and run commands.

### Lab 02 manual checks

- [ ] Match the CIK to Costco's EDGAR filing list.
- [ ] Match each accession number and accepted time to its index page. Confirm the earnings filing reports Item 2.02 and skip newer non-earnings 8-Ks.
- [ ] Open saved text and confirm it matches the filing; confirm the release text comes from Exhibit 99.1.
- [ ] Match every fact to the 10-K line. Check period ends against the fiscal year end and confirm the tag contains the latest year.
- [ ] Redo each ratio by hand using the report-audit definitions.
- [ ] Match the two quarter figures word for word to the release.
- [ ] Match peer revenue and operating income to each peer's own latest 10-K. Use one margin definition.
- [ ] Mark each step right or wrong by hand. Have the partner check two marks.
- [ ] Explain XBRL and the tag/period trap to the partner. Complete the Lab 02 reflection.

## Before Session 3 — about 45 minutes

- [ ] Get all seven steps running if they did not finish in class.
- [ ] Run the steps on Walmart (`WMT`) with chosen peers. Match latest fiscal-year revenue and operating income to Walmart's latest 10-K. Confirm the selected revenue tag means total revenue and redo operating margin by hand.
- [ ] Rotate the exposed API key. Put the replacement in `.env` locally and run `python3.12 check_env.py`. This checks file reading only; it does not validate the key.
- [ ] Confirm the provider and official SDK expected for Lab 03. Course notes mention an OpenAI API key, but the existing key was generated through Purdue GenAI Studio; compatibility is unverified.
- [ ] After building the code and both saved facts folders, push them to the private repository. Keep `.env` out. The current upload contains the available coursework notes; the Lab 02 program and saved facts folders are not yet present.

## Session 3 — Lab 03: The App

Official instructions: [Lab 03 — The App](https://cinderzhang.github.io/FIN67110-Fall2026/week-02/lab-03-make-it-yours.html).

- [ ] Add four separate model roles with the provider's official Python SDK: Research Analyst, Financial Analyst, Investment Advisor, and Strategy Manager.
- [ ] Give each role only its assigned task, context, and expected output as JSON. The model must not calculate ratios; use the code calculator.
- [ ] Have the Manager check the five report parts, return a failing part to its role once, then compile the report.
- [ ] Run on Costco with the Tuesday closing price. Save a five-part Markdown report in the run folder. Name the filings/accession numbers and run time at the top.
- [ ] Audit the report by hand using the [audit checklist](https://cinderzhang.github.io/FIN67110-Fall2026/reference/audit-checklist.html). Mark the eleven core claims, every other financial number, the five-part template, and the recommendation. Report errors (`wrong + unsupported`) and missing claims.
- [ ] Ask the partner to choose a U.S. company that reported this month. Run the same desk for its ticker. Have the partner check two claims; audit all eleven claims yourself.
- [ ] Complete the partner reflection and submit Checkpoint 1 in Brightspace by its due date. It requires a repository commit permalink. The repository is private, so confirm the grader can access the permalink.

## Definition checks to remember

- Costco total revenue includes net sales and membership fees. Do not substitute net sales for total revenue.
- Costco's gross margin on net sales differs from gross margin on total revenue. State the definition used.
- Return on average equity uses the average of this year's and last year's equity.
- Debt/equity includes long-term debt and its current portion.
- Free cash flow is cash from operations minus additions to property and equipment.
- The latest 8-K is not always the earnings release. Select the newest 8-K with Item 2.02.
- The latest revenue tag can change across years. Require the fact's period end to match the 10-K fiscal year end.

## Local Week 1 references

- [Week 1 setup](../WEEK_1_SETUP.md)
- [Week 1 reading notes](../WEEK_1_READING_NOTES.md)
- [Workspace restart point](../RESTART_HERE.md)
