# COST Lab 03 audit

**Review status:** Filing review prepared with AI support at the student's direction. Student verification and partner checks remain separate and pending.

**Report reviewed:** `COST_lab03_report_20261101_093152.md`
**10-K:** accession `0000909832-26-000093`, fiscal year ended 2026-08-30
**Earnings release:** Exhibit 99.1, 8-K accession `0000909832-26-000084`
**Peer 10-Ks:** WMT `0000104169-26-000055`; TGT `0000027419-26-000016`; BJ `0001531152-26-000007`
**Source text:** numbered `10k.txt` and `earnings_release_exhibit_99_1.txt` files in this run folder and the saved peer run folders.

## Eleven required claims

| # | Claim | Audit result | Filing evidence and check |
|---:|---|---|---|
| 1 | Latest 10-K total revenue | Correct | `$303.154B`, fiscal year ended 2026-08-30. The 10-K reports net sales `$297.247B` plus membership fees `$5.907B`, total revenue `$303.154B` (lines 00623-00625). XBRL tag `RevenueFromContractWithCustomerExcludingAssessedTax`, accession `0000909832-26-000093`. |
| 2 | Annual revenue growth | Correct | `(303.154 / 275.235) - 1 = 10.14%`. The 10-K reports 2025 total revenue of `$275.235B` (line 00625). The report's 10.14% matches. |
| 3 | Operating income and operating margin | Correct | Operating income `$11.685B` (line 00629). `$11.685B / $303.154B = 3.85%`. The denominator includes membership-fee revenue. |
| 4 | Net income attributable to parent | Correct | Net income `$9.226B` (line 00635). It matches the report. |
| 5 | GAAP diluted EPS | Correct | `$20.76` for FY2026 (line 00638). It matches the report. |
| 6 | Return on average equity | Correct | Equity was `$35.803B` at 2026-08-30 and `$29.164B` at 2025-08-31 (line 00704). `$9.226B / (($35.803B + $29.164B) / 2) = 28.40%`. |
| 7 | Debt/equity, including current debt | Correct | Current debt `$2.248B` (line 00687), long-term debt `$3.914B` (line 00691), and equity `$35.803B` (line 00704). `($2.248B + $3.914B) / $35.803B = 17.21%`. |
| 8 | Free cash flow | Correct | Cash from operations `$15.817B` (line 00766) less additions to property and equipment `$6.435B` (line 00768) equals `$9.382B`. |
| 9 | Latest-quarter total revenue | **Missing** | The report gives no Q4 FY2026 total revenue. The 16-week Q4 total was `$95.723B`, versus `$86.156B` in Q4 FY2025 (release line 00043). |
| 10 | Latest-quarter revenue growth | **Missing** | `(95.723 / 86.156) - 1 = 11.10%`. The release describes net sales growth as 11.2% (line 00010); that is a different measure from total-revenue growth. |
| 11 | Latest-quarter GAAP diluted EPS | **Missing** | The report gives FY2026 diluted EPS, but not Q4 diluted EPS. Q4 diluted EPS was `$6.75`, versus `$5.87` (release line 00056; narrative at line 00020). |

**Core result:** 8 correct, 0 wrong, 0 unsupported, 3 missing. The original report is not complete because it omits all three required latest-quarter claims.

## Other figures, citations, and wording

| Report statement | Result | Correction or source |
|---|---|---|
| U.S. annual membership fee `$65` | Correct | 10-K line 00157. |
| Executive reward of 2%; Executive sales penetration 75.2% | Correct, citation incomplete | Both are at 10-K line 00166. The report cites only line 00157. |
| Fewer than 4,000 active warehouse SKUs | Correct, wrong line cited | The exact statement is at line 00141, not 00134. |
| Cross-docking and depot efficiency | Supported, citation incomplete | Use lines 00135-00138. Line 00134 describes low prices, selection, volume purchasing, and efficiency in general. |
| Shorter hours and lower labor cost relative to sales volume | Supported | 10-K line 00140. Keep the comparison as the company states it; do not imply a measured labor-cost comparison with every retailer. |
| Digitally-enabled sales were 11% of net sales | Correct | 10-K line 00153. |
| Renewal rate 92.3% in U.S./Canada | Correct, citation incomplete | 10-K line 00167. Executive penetration 75.2% is on line 00166. Cite both lines. |
| Pricing, private-label, and online response to competition | Supported | 10-K line 00398. |
| 28 openings, 25 net new, with 18 U.S., 5 Canada, and 2 other international | Correct numbers, wrong source cited | The source is the 10-K line 00415, not earnings-release line 00016. The 28 gross openings include 3 relocations. |
| Net sales growth of 10% | Correct | 10-K line 00416. New warehouses contributed to growth; they did not alone cause all 10% growth (also line 00451). |
| Gasoline added `$3.501B`/130 basis points; foreign currency added `$1.332B`/49 basis points | Correct numbers, wrong source cited | These are in the 10-K at lines 00454-00455. They are not at release line 000454. Amounts in the 10-K are `$3,501M` and `$1,332M`. |
| IEEPA refunds of `$184M` in FY2026 and `$155M` after year-end | Amounts correct; accounting description needs correction | 10-K line 00426 says `$184M` was received in FY2026: `$174M` reduced merchandise costs and `$10M` was interest income. Costco later received `$155M` more. The report incorrectly says the full `$184M` reduced merchandise costs. Cite the 10-K, not “release line 000426.” |
| Tariff refund effect on Q4 EPS | Missing material context | The release says Q4 diluted EPS included a non-recurring `$0.15` benefit from IEEPA refunds (line 00020). Add this caveat when discussing the 14% annual net-income increase. |
| Annual net income +14%, sales +10%, dividend +13% | Numbers correct, source cited incorrectly | 10-K lines 00416, 00422-00423. The cited “release line 000423” is not in the release file. |
| Other International sales growth 12% compared with U.S. | Correct, citation incomplete | 10-K lines 00435-00438 show U.S. 10% and Other International 12% net-sales growth. Line 00405 discusses higher international square-footage growth, which is a different measure. |
| Digitally-enabled comparable sales grew 21% | Correct, wrong source cited | 10-K line 00452, not release line 000453. |
| E-commerce and travel contributed `$10.2B` of revenue | **Wrong** | 10-K line 00453 says sales in warehouse ancillary and other businesses increased `$10,199M` (20%), led by gasoline and pharmacy. This is an increase across those categories, not total digital revenue or e-commerce/travel revenue. Remove or state it accurately. |
| COST P/E 47.79 “compared to” WMT 4.18%, TGT 4.88%, BJ 3.81% | **Invalid comparison** | COST's 47.79 is a P/E ratio. The peer percentages are operating margins. Do not compare them as multiples. The peer margins themselves recalculate from each peer's latest 10-K: WMT `$29.825B / $713.163B = 4.18%` (lines 00955, 00959); TGT `$5.117B / $104.780B = 4.88%` (lines 00626, 00633); BJ `$816.604M / $21,457.274M = 3.81%` (lines 00869, 00873). All three peer 10-Ks end 2026-01-31. |
| Financial facts in the report | Values correct, traceability inadequate | The report uses tags and internal labels such as `[claim 2]`, `[claim 3-5]`, and `[Financial Analyst]`. Replace these with the 10-K line, tag, period, and accession for each figure. |
| Source lines labeled “release line 000454/000426/000423/000453” | **Wrong source labels** | These numbers refer to lines in the 10-K, not the 143-line release text. Use the 10-K accession and lines 00454-00455, 00426, 00422-00423, 00452-00453. |

## Recommendation review

The original **Buy** is not supported by the report as written. It relies in part on the incorrect `$10.2B` “digital revenue” claim. It also omits Q4 total revenue and diluted EPS, the non-recurring `$0.15` Q4 EPS benefit, and any uncertainty. It compares a P/E ratio with operating margins.

The corrected draft uses a **provisional Hold**. Its deciding figure is **47.79x FY2026 EPS** (`$992.13 / $20.76`). This is a judgment under incomplete forward estimates, not a fair-value conclusion. The draft states that limitation and reports the one-time tariff benefit.

## Remaining review items

- This filing review records the values, periods, calculations, and citation corrections above. Check each finding against the cited filing before submitting.
- The partner check remains pending.
- The provisional Hold is an analytical judgment based on the evidence stated above, not a forecast or fair-value conclusion.
