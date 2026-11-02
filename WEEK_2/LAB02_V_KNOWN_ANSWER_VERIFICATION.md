# Lab 02 V — Costco known-answer verification

**Checked:** October 27, 2026
**Run reviewed:** `COSTCO_WHOLESALE_CORP_NEW_20261026_223242_EDT`
**Result:** The saved seven-step Costco run agrees with the SEC filings and SEC Company Facts for the checks below. This is a source review of the saved output. It does not establish that the student or partner completed the in-class paper checklist.

## Seven checks

| Step | Status | Evidence and finding |
|---|---|---|
| 1. Resolve ticker | Verified | The manifest maps `COST` to CIK `0000909832`, Costco Wholesale Corporation. The selected Costco EDGAR filings show that same CIK. |
| 2. Select filings | Verified, with time-zone normalization | The latest 10-K is accession `0000909832-26-000093`; the latest 10-Q is `0000909832-26-000051`; and the selected earnings 8-K is `0000909832-26-000084`. The EDGAR index pages show the matching accession and Accepted time. The saved manifest records the same instants in UTC, while EDGAR displays Eastern time. The October 16 and October 14 8-Ks are newer, but their items are 5.02/9.01 and 8.01/9.01, so they are correctly skipped for the earnings-release task. The September 24 8-K reports Item 2.02. |
| 3. Save source texts | Verified | The saved text headers identify `cost-20260830.htm` (10-K), `cost-20260510.htm` (10-Q), and `cost-20260924.htm` (8-K). The release text is `costex9918-k92426.htm`, listed by EDGAR as Exhibit 99.1. The 8-K says Exhibit 99.1 is its press release. |
| 4. Select annual facts | Verified against the saved SEC Company Facts export and 10-K statements | All selected facts are filed on the 10-K accession and match fiscal year-end August 30, 2026. Revenue: `RevenueFromContractWithCustomerExcludingAssessedTax`, $303,154 million. Operating income: `OperatingIncomeLoss`, $11,685 million. Net income: `NetIncomeLoss`, $9,226 million. Diluted EPS: `EarningsPerShareDiluted`, $20.76. Equity: `StockholdersEquity`, $35,803 million. Long-term debt excluding current portion: `LongTermDebtNoncurrent`, $3,914 million. Current debt: `LongTermDebtCurrent`, $2,248 million. Cash from operations: `NetCashProvidedByUsedInOperatingActivities`, $15,817 million. Property/equipment additions: `PaymentsToAcquirePropertyPlantAndEquipment`, $6,435 million. The 10-K statement lines support these values. Prior balance-sheet comparison values end August 31, 2025; the current balance-sheet values end August 30, 2026. Annual flow facts cover the 52 weeks ended August 30, 2026. |
| 5. Recalculate | Verified | Revenue growth: `(303,154 / 275,235) - 1 = 10.14%`. Operating margin: `11,685 / 303,154 = 3.85%`. Return on average equity: `9,226 / ((35,803 + 29,164) / 2) = 28.40%`. Debt/equity: `(3,914 + 2,248) / 35,803 = 17.21%`. Free cash flow: `15,817 - 6,435 = $9,382 million`. P/E using the supplied `--price 904.70`: `904.70 / 20.76 = 43.58x`. September 23, 2026 historical close is $904.70. The records confirm the close, but do not prove that this was the exact number used in the instructor's on-screen run. |
| 6. Check release lines | Verified | The saved Exhibit 99.1 text contains `Total revenue 95,723 86,156 303,154 275,235` and `Diluted $ 6.75 $ 5.87 $ 20.76 $ 18.21`. The requested latest-quarter values are $95,723 million and $6.75 per diluted share. |
| 7. Compare peers | Verified | Same definition used: GAAP operating income divided by total revenue, including membership-related revenue where reported. WMT: `$29,825m / $713,163m = 4.18%`. TGT: `$5,117m / $104,780m = 4.88%`. BJ: `$816.604m / $21,457.274m = 3.81%`. The revenue and operating-income figures appear in each peer's latest 10-K; the saved SEC Company Facts exports use those same 10-K accessions and fiscal year ends. |

## Source links

- Costco [2026 10-K filing index](https://www.sec.gov/Archives/edgar/data/909832/000090983226000093/0000909832-26-000093-index.html) and [10-K document](https://www.sec.gov/Archives/edgar/data/909832/000090983226000093/cost-20260830.htm).
- Costco [2026 10-Q filing index](https://www.sec.gov/Archives/edgar/data/909832/000090983226000051/0000909832-26-000051-index.html).
- Costco [September 24, 2026 8-K index](https://www.sec.gov/Archives/edgar/data/909832/000090983226000084/0000909832-26-000084-index.html) and [Exhibit 99.1](https://www.sec.gov/Archives/edgar/data/909832/000090983226000084/costex9918-k92426.htm).
- Newer 8-K indexes: [October 16](https://www.sec.gov/Archives/edgar/data/909832/000090983226000100/0000909832-26-000100-index.html) and [October 14](https://www.sec.gov/Archives/edgar/data/909832/000090983226000096/0000909832-26-000096-index.html).
- Peer latest 10-K indexes and statements: [Walmart](https://www.sec.gov/Archives/edgar/data/104169/000010416926000055/0000104169-26-000055-index.html), [Target](https://www.sec.gov/Archives/edgar/data/27419/000002741926000016/0000027419-26-000016-index.html), and [BJ's](https://www.sec.gov/Archives/edgar/data/1531152/000153115226000007/0001531152-26-000007-index.html).
- September 23, 2026 Costco close: [Financial Times historical prices](https://markets.ft.com/data/equities/tearsheet/historical?s=COST%3ANSQ).

## One discrepancy to record

The Costco earnings-release cash-flow table in the saved Exhibit 99.1 text says cash from operations was `$15,825 million`. The 10-K statement and SEC Company Facts value used in Step 4 say `$15,817 million`. The assignment's Step 4 check asks for the 10-K figure, so the Step 5 free-cash-flow calculation correctly uses `$15,817 million`. Record the $8 million release-versus-10-K difference if the instructor asks you to reconcile the sources.

## XBRL and tag-trap check

XBRL gives each reported fact a concept tag, a value, a unit, and a reporting context. The context states a period or date. SEC Company Facts provides tagged facts for each company in a JSON file.

For Costco revenue, the saved Company Facts file shows that the `Revenues` tag ends at August 31, 2025. It does not contain Costco's fiscal 2026 total revenue. The tag `RevenueFromContractWithCustomerExcludingAssessedTax` contains `$303,154 million` for the 52 weeks ending August 30, 2026. The code compares its candidate revenue tags by latest period end, so it selects the newer tag. It records the selected tag, unit, period, form, and accession.

The current revenue and operating-income facts used for Costco's margin both end August 30, 2026. The 2025 revenue and operating-income comparison facts both end August 31, 2025. The current peer margin inputs also share each peer's January 31, 2026 period end. The current saved run does not show either tag trap described in the course prompt.

Tags can change when the taxonomy changes or when the company maps a reported line to a different concept. The tag name alone does not prove that a fact is current or comparable. Check the concept label, unit, form, accession, and reporting period. Here, the code anchors the other current-year measures to the selected revenue fiscal-year end. That prevents a current numerator from being divided by an old-year denominator.

Partner explanation to use after your own review: “Costco's `Revenues` tag stops at August 31, 2025. The newer tag `RevenueFromContractWithCustomerExcludingAssessedTax` contains total revenue for the year ending August 30, 2026. My code picks the candidate tag with the latest fiscal period. It then selects the other annual facts for that same fiscal year. This keeps the operating margin from dividing one year's operating income by another year's revenue.”

## Still requires student or partner evidence

- The calculations above were independently recomputed here. They were not handwritten by the student.
- The two partner marks and partner reflection are not in the workspace.
- The XBRL explanation above is study support. It does not prove that you explained it to your partner.
- The exact instructor-screen price is unverified, even though `$904.70` is the September 23 close before the September 24 release.
