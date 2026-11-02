# Lab 03: Reconstructed Coding Prompt

Use this prompt in place of the original Lab 03 request. Build on my seven-step Python data desk from Lab 02. Add the four roles in Figure 1 of Francis and Zhang (2026). Use the report structure in Figure 2.

Use the official Python SDK for this model provider: `[OpenAI | Anthropic | Google]`. Replace the bracket with the provider you use. Read `SEC_USER_AGENT`, `API_KEY`, and `FINANCIAL_DATASETS_PROFESSOR_API_KEY` from the `.env` file in this folder. Send `SEC_USER_AGENT` with every SEC request. Use `API_KEY` only to authenticate calls to the selected model provider. Use `FINANCIAL_DATASETS_PROFESSOR_API_KEY` for Financial Datasets data requests. Send it in the `X-API-KEY` request header. Keep the model key and data key separate. Never print, log, save, commit, or upload either key. Do not upload `.env`.

Use Financial Datasets API endpoints to retrieve company financial or market data when the task needs that data. Keep EDGAR as the source for filing discovery, filing text, accession numbers, and the manual filing audit. Record the data endpoint, ticker, period or price date, unit, and the filing source when the API provides it. Check reported values against the SEC filing text before using them in the report. If a Financial Datasets value and the filing differ, report the difference and use the filing value for an audited claim.

The program must accept:

- A ticker as its main argument.
- An optional `--peers` list of tickers.
- An optional `--price` number.
- An optional `--price-date` in `YYYY-MM-DD` format, so the report can identify the price date.
- An optional `--step` number to run one of the seven data steps only.

Do not name a company in the code. Use the ticker to find the company.

## Seven data steps

Print these seven steps as they run:

1. Find the ticker's CIK in SEC's `company_tickers.json`.
2. Get the company's filings from the EDGAR submissions API. Select the latest 10-K, the latest 10-Q, and the latest 8-K that reports Item 2.02, the earnings release. Print each filing's accession number and its “Accepted” time from the EDGAR filing index page.
3. Download the selected 10-K, 10-Q, and 8-K. Download the earnings release exhibit from the 8-K. Use Exhibit 99.1 when the filing identifies the release as Exhibit 99.1. If the filing uses another exhibit label, identify the correct release from the filing index and report its actual label. Do not call it Exhibit 99.1 unless the filing does. Convert the documents to plain text. Keep numbered source lines. Save the files in a new folder named with the company, date, and time of the run.
4. Get the company's XBRL Company Facts. For the latest fiscal year, print total revenue, operating income, net income attributable to the company, diluted GAAP EPS, stockholders' equity, long-term debt and its current portion, cash from operations, and additions to property and equipment. For each fact, print its tag, unit, period end, and filing. If a concept has candidate tags, choose the tag with the newest available annual period. Use the same fiscal year as revenue for every annual concept. Show the prior-year fact beside it. Keep total revenue distinct from net sales. Check each selected fact against the matching 10-K statement line.
5. Calculate in Python and print the inputs and arithmetic for:
   - Annual revenue growth, using current and prior-year total revenue from the same 10-K.
   - Operating margin: operating income divided by total revenue.
   - Return on average equity: net income divided by the average of current-year and prior-year stockholders' equity.
   - Debt to equity: long-term debt, including its current portion, divided by stockholders' equity.
   - Free cash flow: cash from operations minus additions to property and equipment.
   - P/E: `--price` divided by diluted GAAP EPS. Print the price and `--price-date`. If `--price` is not supplied, retrieve the closing price for `--price-date` from Financial Datasets and record its source and date. Do not substitute a current quote for a requested historical close.
   - Latest-quarter revenue growth, using the quarter and same quarter in the prior year from the earnings release.

   A model must not calculate a ratio. Run every calculation in Python code. If a required input is absent, print that the calculation is unavailable and state why. Do not guess.
6. From the earnings release text, print the lines for latest-quarter total revenue, the same quarter's revenue one year earlier, and diluted GAAP EPS. Preserve the filing's labels and units. Do not substitute net sales for total revenue or non-GAAP EPS for GAAP EPS.
7. For each peer, get its latest 10-K facts. Print revenue, operating income, their tags, units, periods, and filings. Calculate operating margin as operating income divided by total revenue. Use that same definition for the company and every peer. Name each peer's fiscal year end.

Save the Company Facts data beside the text files. Keep the selected filings, numbered text, facts, calculations, peer facts, price, and price date available to the model roles.

## Four roles and report

Each of the four roles must use its own model call and its own instructions. The Python harness must send each role a JSON object with these fields: `task`, `context`, and `expected_output`. Send only the information that the role needs. Print each role's name as it runs. Require structured output that the harness can check.

1. **Research Analyst** — Explain the business model, competitive position, catalysts, and recent developments. Use the 10-K's Business and MD&A sections and the earnings release. Support every factual claim with a short exact quotation, the source file, and its numbered line. State when the sources do not support a claim. Do not add outside facts.
2. **Financial Analyst** — Analyze the Step 4 statements and facts, Step 5 calculations, Step 6 quarter, and Step 7 peers. Include all eleven core claims below. Give every number its filing and its line or XBRL tag, unit, and period. Show the arithmetic for every ratio. State the definition when a filing offers more than one. You may ask the Python calculator for another ratio. Never calculate in the model. State when a value is unavailable; do not fill a gap with a guess.
3. **Investment Advisor** — Give a thesis and one recommendation: Buy, Hold, or Sell. Name the one reported number that most drives the recommendation. Use only the Research Analyst's and Financial Analyst's outputs. Do not use outside facts or add unsupported claims.
4. **Strategy Manager** — Coordinate the three analysis roles, check the report, and compile it. Check that all five parts are present and consistent:
   - Overview
   - Market Positioning and Growth Outlook
   - Valuation Insights
   - Future Developments and Strategic Recommendations
   - Investment Recommendation

   Use a checklist in the Python harness to check the five headings and required outputs. The Strategy Manager must also identify missing or inconsistent parts. Send each failing part back to its role once for revision. Then compile the report. Do not retry a part a second time. If a gap remains, state it in the report. Do not mark the report as audited or verified.

Send the Investment Advisor only the Research Analyst's and Financial Analyst's outputs. Use the role outputs and source-backed data to build the report. Do not let a role use information that the Strategy Manager did not send it.

## Eleven claims the report must state

Include these claims so the report can be checked against the Lab 03 report audit:

1. Latest 10-K total revenue.
2. Annual revenue growth versus the prior year, calculated from both years in the same 10-K.
3. Operating income and operating margin, with operating margin defined as operating income divided by total revenue.
4. Net income attributable to the company.
5. GAAP diluted EPS.
6. Return on average equity: net income divided by the average of current-year and prior-year stockholders' equity.
7. Debt to equity: long-term debt, including the current portion, divided by stockholders' equity.
8. Free cash flow: cash from operations minus additions to property and equipment.
9. Latest-quarter total revenue from the earnings release.
10. Latest-quarter revenue growth versus the same quarter one year earlier.
11. Latest-quarter GAAP diluted EPS from the earnings release.

Also include P/E when `--price` is supplied. State its price date and arithmetic. Include peer operating margins on the same total-revenue definition. Label every definition and period clearly. A non-GAAP EPS value does not replace either GAAP EPS claim.

## Report file and commands

Save the report as Markdown in the run folder. Put the filings read and their accession numbers on the first line. Put the run time on the second line. Then write the five report parts using the exact headings above. Print the report's full path.

When the program is complete, give me:

- The exact command to install its required packages, including the selected provider's official Python SDK.
- The exact command to run the desk with a ticker, peers, price, and price date. Use this format: `python3.12 WEEK_2/desk.py TICKER --peers PEER1,PEER2 --price PRICE --price-date YYYY-MM-DD`.

Keep the provider, ticker, company, peers, price, and date configurable. Do not put a company name or real API key in the code.

## Lab 03 work after the program is built

These are student tasks. Do them after the coding agent finishes. Do not ask the coding agent or any model to fill in the audit marks.

1. Run the desk on COST with peers WMT, TGT, and BJ. Use the Tuesday closing price required by the class instructions. Expect seven data steps, the four role names, and the saved report path.
2. Read the report audit. By hand, check the eleven claims against the filings. Then check every other number in the Financial Analyst's section, the five report parts, and the recommendation. Mark each as correct, wrong, unsupported, or missing. Count errors as wrong plus unsupported. Count missing claims separately. Save the audit table in the repository.
3. Ask your partner to choose a U.S. company that reported this month. Run the same desk on its ticker with peers you choose. Have your partner check two core claims against that company's filings by hand.
4. Keep the partner's company run and report in the repository. Do not include `.env` or an API key in the repository. Use the report as a draft until the human audit is complete.
