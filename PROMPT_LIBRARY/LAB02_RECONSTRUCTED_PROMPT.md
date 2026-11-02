# Lab 02: Reconstructed Coding Prompt

Build a Python program for the data part of an equity research desk. Model it on Section 3.1 of Francis and Zhang (2026). We will add the model roles later.

Read `SEC_USER_AGENT` from the `.env` file in this folder. Send it with every SEC request. Do not read or print any API key.

The program must accept:

- A ticker as its main argument.
- An optional `--peers` list of tickers.
- An optional `--price` number.
- An optional `--step` number to run only one step.

Do not name a company in the code. Use the ticker to find the company.

Print these seven steps as they run:

1. Find the ticker's CIK in SEC's `company_tickers.json`.
2. Get the company's filings from the EDGAR submissions API. Select the latest 10-K, the latest 10-Q, and the latest 8-K that reports Item 2.02, the earnings release. Print each filing's accession number and its “Accepted” time from the EDGAR filing index page.
3. Download the selected 10-K, 10-Q, and 8-K. Also download Exhibit 99.1 from the 8-K. Convert the documents to plain text. Save them in a new folder named with the company, date, and time of the run.
4. Get the company's XBRL Company Facts. For the latest fiscal year, print total revenue, operating income, net income, diluted EPS, stockholders' equity, long-term debt, its current portion, cash from operations, and additions to property and equipment. For each fact, print its tag, period end, and filing. If a concept has candidate tags, choose the tag with the newest available fiscal year. Use the same fiscal year as revenue for every concept. Show the prior-year fact beside it.
5. Calculate and print each formula:
   - Revenue growth
   - Operating margin
   - Return on average equity
   - Debt to equity, including the current portion of long-term debt
   - Free cash flow: cash from operations minus additions to property and equipment
   - P/E using `--price`

   Print the inputs and arithmetic for each calculation.
6. From the earnings release text, print the lines that state quarterly total revenue and diluted EPS.
7. For each peer, print the same facts and calculate operating margin using the same definition.

Save the Company Facts data beside the text files.

When the program is complete, give me the exact command to install any required packages. Also give me the exact command to run the program with a ticker, peers, and a price.
