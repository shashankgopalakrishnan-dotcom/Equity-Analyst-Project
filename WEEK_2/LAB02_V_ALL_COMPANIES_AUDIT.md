# Lab 02 V — filing checks for Costco, Apple, and peers

**Checked:** October 27, 2026
**Runs reviewed:**

- Costco: `runs/COSTCO_WHOLESALE_CORP_NEW_20261027_092302_EDT`
- Apple: `runs/Apple_Inc._20261027_093055_EDT` (MSFT peer; October 26 close used for P/E)

This is a source-based audit. I checked the saved manifests and text, SEC filing indexes, selected 10-K statements, release lines, and arithmetic. It is not a handwritten worksheet. A partner still needs to check two marks with you.

## Marked checks

| Step | Costco | Apple / Microsoft | Evidence and note |
|---|---|---|---|
| 1. Resolve ticker | **Right** | **Right** | COST maps to CIK `0000909832`. AAPL maps to `0000320193`. Peer MSFT maps to `0000789019`. The CIKs match their SEC filing records. |
| 2. Select filings | **Right** | **Right** | Costco selected 10-K `0000909832-26-000093`, 10-Q `0000909832-26-000051`, and Item 2.02 8-K `0000909832-26-000084`. Newer October 16 and October 14 8-Ks have items 5.02 and 8.01, so they are skipped. Apple selected 10-K `0000320193-25-000079`, 10-Q `0000320193-26-000020`, and Item 2.02 8-K `0000320193-26-000018`. The newer September 1 Apple 8-K has item 5.02, so it is skipped. Accession numbers and accepted instants match the EDGAR index pages. The manifest uses UTC; EDGAR displays Eastern time. |
| 3. Save source text | **Right** | **Right** | Both run folders contain `10k.txt`, `10q.txt`, `earnings_8k.txt`, and `earnings_release_exhibit_99_1.txt`. Their headers identify the selected filing documents. EDGAR lists each release as Exhibit 99.1. |
| 4. Read annual facts | **Right** | **Right** | The selected current facts use the 10-K fiscal year end and the selected 10-K accession. Values and tags are listed below. Costco’s and Apple’s annual statement lines match the selected facts. MSFT’s two peer facts match its latest 10-K. |
| 5. Recalculate ratios | **Right, with price caveat** | **Right** | I recalculated the ratios below from the printed inputs. Costco P/E uses `$904.70`; that is the September 23, 2026 close, but the instructor-screen price is not confirmed. Apple P/E uses the October 26, 2026 close of `$343.91` and FY2025 diluted EPS of `$7.46`. These are independent calculations in this audit, not the student’s handwritten marks. |
| 6. Check release lines | **Right** | **Right, manually confirmed** | Costco’s release contains the extracted total-revenue and diluted-EPS rows. Apple’s release states quarterly revenue of `$109.4 billion` and diluted earnings per share of `$2.02`. These exact words appear in Exhibit 99.1. The automated text search missed the Apple lines, so I checked the saved release text directly. |
| 7. Check peer facts and margins | **Right** | **Right** | The revenue and operating-income inputs match each peer’s latest 10-K. Each margin uses GAAP operating income divided by total revenue. Costco peers: WMT, TGT, BJ. Apple peer: MSFT. Fiscal year ends differ between Apple and Microsoft. |

## Annual facts and tag check

Amounts are in USD millions, except EPS. Each current value is for the fiscal year shown. Balance-sheet values are as of that fiscal year end.

| Company | FY end | Revenue and tag | Operating income and tag |
|---|---|---|---|
| COST | 2026-08-30 | 303,154 — `RevenueFromContractWithCustomerExcludingAssessedTax` | 11,685 — `OperatingIncomeLoss` |
| AAPL | 2025-09-27 | 416,161 — `RevenueFromContractWithCustomerExcludingAssessedTax` | 133,050 — `OperatingIncomeLoss` |
| MSFT peer | 2026-06-30 | 331,839 — `RevenueFromContractWithCustomerExcludingAssessedTax` | 155,237 — `OperatingIncomeLoss` |

The selected tags hold the newest annual revenue values in the saved SEC Company Facts data. For Costco, `Revenues` ends at 2025-08-31; the selected revenue tag ends at 2026-08-30. For Apple, `Revenues` ends at 2018-09-29; the selected tag ends at 2025-09-27. For Microsoft, `Revenues` ends at 2010-06-30; the selected tag ends at 2026-06-30. Each selected revenue and operating-income pair has the same fiscal-year end.

The other current-year Costco tags are `NetIncomeLoss` ($9,226), `EarningsPerShareDiluted` ($20.76), `StockholdersEquity` ($35,803), `LongTermDebtNoncurrent` ($3,914), `LongTermDebtCurrent` ($2,248), `NetCashProvidedByUsedInOperatingActivities` ($15,817), and `PaymentsToAcquirePropertyPlantAndEquipment` ($6,435).

The other current-year Apple tags are `NetIncomeLoss` ($112,010), `EarningsPerShareDiluted` ($7.46), `StockholdersEquity` ($73,733), `LongTermDebtNoncurrent` ($78,328), `LongTermDebtCurrent` ($12,350), `NetCashProvidedByUsedInOperatingActivities` ($111,482), and `PaymentsToAcquirePropertyPlantAndEquipment` ($12,715).

The numbers match the annual statement lines in the saved Costco and Apple 10-K text. The Costco release reports cash from operations of `$15,825 million`, while the 10-K reports `$15,817 million`. The requested Step 4 source is the 10-K, so the audited free-cash-flow calculation uses `$15,817 million`. Record this `$8 million` source difference if asked.

## Recalculation

### Costco

- Revenue growth: `(303,154 / 275,235) - 1 = 10.14%`
- Operating margin: `11,685 / 303,154 = 3.85%`
- Return on average equity: `9,226 / ((35,803 + 29,164) / 2) = 28.40%`
- Debt to equity: `(3,914 + 2,248) / 35,803 = 17.21%`
- Free cash flow: `15,817 - 6,435 = $9,382 million`
- P/E: `$904.70 / $20.76 = 43.58x`

### Apple

- Revenue growth: `(416,161 / 391,035) - 1 = 6.43%`
- Operating margin: `133,050 / 416,161 = 31.97%`
- Return on average equity: `112,010 / ((73,733 + 56,950) / 2) = 171.42%`
- Debt to equity: `(78,328 + 12,350) / 73,733 = 122.98%`
- Free cash flow: `111,482 - 12,715 = $98,767 million`
- P/E: `$343.91 / $7.46 = 46.10x`, using the October 26, 2026 close and Apple’s latest filed annual diluted EPS.

## Peer check

Definition for every peer: GAAP operating income divided by total revenue. Values are in USD millions.

| Peer | Fiscal year end | Operating income | Total revenue | Margin |
|---|---:|---:|---:|---:|
| WMT | 2026-01-31 | 29,825 | 713,163 | 4.18% |
| TGT | 2026-01-31 | 5,117 | 104,780 | 4.88% |
| BJ | 2026-01-31 | 816.604 | 21,457.274 | 3.81% |
| MSFT | 2026-06-30 | 155,237 | 331,839 | 46.78% |

Apple’s fiscal year ends 2025-09-27. Microsoft’s ends 2026-06-30. The periods are not aligned. Keep this caveat with the margin comparison.

## XBRL explanation to say to a partner

“XBRL is a way to label each reported number. The label tells us what the number means. The filing also gives the number a period and a unit. For Costco, the older `Revenues` tag ends in 2025. The newer `RevenueFromContractWithCustomerExcludingAssessedTax` tag gives 2026 total revenue. The code checks candidate tags and chooses the one with the latest annual period. Then it selects the other numbers for that same year. This helps stop a margin from dividing one year’s operating income by another year’s revenue. A company can use a different tag when its reported line or the taxonomy changes. We still need to check the tag, unit, filing, and period against the 10-K.”

## Human steps still pending

- Copy the marks by hand onto the class worksheet.
- Ask your partner to check two marks.
- Explain the XBRL answer to your partner.

## SEC source links

- Costco [10-K index](https://www.sec.gov/Archives/edgar/data/909832/000090983226000093/0000909832-26-000093-index.html), [10-K](https://www.sec.gov/Archives/edgar/data/909832/000090983226000093/cost-20260830.htm), [10-Q index](https://www.sec.gov/Archives/edgar/data/909832/000090983226000051/0000909832-26-000051-index.html), [earnings 8-K index](https://www.sec.gov/Archives/edgar/data/909832/000090983226000084/0000909832-26-000084-index.html), [Exhibit 99.1](https://www.sec.gov/Archives/edgar/data/909832/000090983226000084/costex9918-k92426.htm).
- Apple [10-K index](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079-index.html), [10-K](https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm), [10-Q index](https://www.sec.gov/Archives/edgar/data/320193/000032019326000020/0000320193-26-000020-index.html), [earnings 8-K index](https://www.sec.gov/Archives/edgar/data/320193/000032019326000018/0000320193-26-000018-index.html), [Exhibit 99.1](https://www.sec.gov/Archives/edgar/data/320193/000032019326000018/a8-kex991q3202606272026.htm).
- Apple close used for the P/E calculation: [October 26, 2026 historical close, `$343.91`](https://stockanalysis.com/stocks/aapl/history/).
- Microsoft [2026 10-K index](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/0001193125-26-323660-index.html) and [10-K](https://www.sec.gov/Archives/edgar/data/789019/000119312526323660/msft-20260630.htm).
- Costco peer 10-Ks: [Walmart](https://www.sec.gov/Archives/edgar/data/104169/000010416926000055/0000104169-26-000055-index.html), [Target](https://www.sec.gov/Archives/edgar/data/27419/000002741926000016/0000027419-26-000016-index.html), and [BJ’s Wholesale Club](https://www.sec.gov/Archives/edgar/data/1531152/000153115226000007/0001531152-26-000007-index.html).
