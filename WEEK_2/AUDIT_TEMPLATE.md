# FIN 67110 Lab 02 and Lab 03 Audit Worksheet

This worksheet records the filing review and the student's verification status.

> **Student verification: complete on 2026-11-02.** The user confirms they reviewed and agree with the filing-review findings and corrected drafts for all seven reports, and with the CMG Lab 02 and Lab 03 checks recorded here. This confirms the user's review; it does not change the recorded errors or missing claims in the original model reports. The older Lab 02 extractor did not provide current debt or debt/equity, so those two original data-pull checks remain incorrect. The reviewed Lab 03 draft calculates 0.00x from the 10-K's no-borrowings disclosure; leases are excluded. The CMG peer statement-line check is complete: the latest 10-K text for MCD, YUM, and CAVA is saved in the CMG run folder and the revenue, operating income, periods, and margins are checked below. Partner checks, reflection, and Brightspace fields remain open.

**Audited run:** `WEEK_2/runs/CHIPOTLE_MEXICAN_GRILL_INC_20261101_101158_EST/`
**Report:** `CMG_lab03_report_20261101_101604.md` (model `qwen3:8b`)
**Line numbers:** `10k.txt`, `10q.txt` and `earnings_release_exhibit_99_1.txt` use the five-digit `NNNNN:` prefix on each line.

## Lab 02: seven checks

| Step | Claim/source to inspect | Correct | Incorrect | Notes / filing line |
|---|---|:---:|:---:|---|
| 1 | Ticker maps to the right company and CIK | ✓ |  | CMG = Chipotle Mexican Grill, CIK 0001058090, file no. 001-32731 (manifest and filing cover). |
| 2 | Latest 10-K, 10-Q, and newest Item 2.02 8-K; accession and accepted time | ✓ |  | 10-K 0001058090-26-000009, accepted 2026-02-04 21:51Z. 10-Q 0001058090-26-000104, accepted 2026-10-28 22:23Z (filed 2026-10-29). 8-K 0001058090-26-000103, accepted 2026-10-28 20:10Z, Items 2.02 and 9.01 (`earnings_8k.txt` line 38). **Newest Item 2.02 checked against EDGAR's CMG 8-K list (2026-11-02):** 2026-10-28 (0001058090-26-000103, Items 2.02, 9.01) is the newest. The earlier 2.02 filings are 2026-07-29 (-000063), 2026-04-29 (-000027) and 2026-02-03 (-000007); the later-dated 2026-09-14 filing (-000088) is Item 5.02 only. Re-check on EDGAR yourself. |
| 3 | Saved text is from selected filings and Exhibit 99.1 | ✓ |  | Release is Exhibit 99.1 (line 6), "third quarter ended September 30, 2026" (line 16). 10-K text is "As of December 31, 2025" (10-K line 179). |
| 4 | XBRL concept, unit, fiscal period, and accession match the requested fact |  | ✓ | The listed facts match the saved Company Facts data. **Incomplete:** `current_debt` is null; the run does not provide the requested current portion or its tag. `LongTermDebt` is 0. **Filing check done:** the 10-K balance sheet (lines 00702-00713) has no debt line and no current portion of debt; its only liabilities are payables, accruals, unearned revenue and leases. The 10-Q balance sheet (lines 00162-00174) is the same. The 10-K says "no outstanding borrowings under the credit facility" (line 01334), with $500.0M undrawn (line 00604). Company Facts has only `LongTermDebt` = 0 and no current-debt tag. So the true current-debt value is **$0**, and `null` is not a usable output. Keep this step marked incorrect: the run did not give the requested fact. |
| 5 | Ratio arithmetic and definitions |  | ✓ | Revenue growth 5.41%, operating margin 16.23%, ROAE 47.36%, FCF $1,447.6M, and P/E 24.54 recalculate from the listed inputs. **Incomplete:** debt/equity is printed as unavailable because `current_debt` is null. **Required result from the filings:** debt/equity = ($0 long-term + $0 current) ÷ $2,830.607M = **0.00x** (FY2025). The instructor's Costco run uses the same shape, (long-term debt + current portion) ÷ equity. Operating leases ($302.4M current, $4,773.4M long-term, 10-K lines 00707 and 00710) are left out of borrowings. If your class counts leases as debt, D/E = (302.380 + 4,773.434) ÷ 2,830.607 = 1.79x, so state your definition. The run printed "unavailable" instead of 0.00x, so keep this step marked incorrect. P/E uses Oct-2026 price with FY2025 EPS, not TTM EPS. |
| 6 | Latest-quarter total revenue and diluted GAAP EPS match the release | ✓ |  | Release line 70: total revenue $3,293,162K vs $3,003,444K (+9.65%, release says 9.6%). Line 88: diluted EPS $0.27 vs $0.29. The numbers are right; the *report* leaves out the EPS (see claim 11). |
| 7 | Peer facts and operating margin use the same definition | ✓ |  | **Verified against each latest 10-K statement.** MCD FY2025: total revenue $26,885m (line 00808); operating income $12,393m (line 00821); margin `$12,393m / $26,885m = 46.10%`. YUM FY2025: total revenue $8,214m (line 01083); operating profit $2,574m (line 01092); margin `$2,574m / $8,214m = 31.34%`. CAVA FY2025: revenue $1,179,664 thousand (line 01156); income from operations $55,285 thousand (line 01170); margin `$55,285k / $1,179,664k = 4.69%`. Each revenue and operating-income pair has the same fiscal period and uses GAAP totals. See [`CMG_LAB02_STEP7_PEER_CHECK.md`](CMG_LAB02_STEP7_PEER_CHECK.md) and the saved peer `10k.txt` files. |

Partner checks: claim/step 1: ____________________  claim/step 2: ____________________

## Lab 03: eleven core claims

Mark one status for each claim: correct, wrong, unsupported, or missing. Add the exact source and line. Count **errors = wrong + unsupported**. Count missing separately.

| # | Core claim | Status | Source, period, and line | Correction / note |
|---:|---|---|---|---|
| 1 | Latest 10-K revenue | **wrong** | 10-K line 00732; XBRL `Revenues`, FY2025, $11,925,601,000, accn 0001058090-26-000009 | Report says `$11,925.6B`. Correct: about **$11.93B** ($11,925.6M). The error is 1,000x. |
| 2 | Revenue growth | correct (percentage only) | 10-K line 00732: FY2025 $11,925.601M vs FY2024 $11,313.853M | 5.41% matches. The report's prior-year amount is wrong by 1,000x; record it in the other-claims table below. |
| 3 | Operating income and operating margin | correct | 10-K line 00743; XBRL `OperatingIncomeLoss`, FY2025, $1,935,798,000 | $1.936B and 16.23% match. |
| 4 | Net income attributable to parent | correct | 10-K line 00747; XBRL `NetIncomeLoss`, FY2025, $1,535,761,000 | $1.536B matches. |
| 5 | GAAP diluted EPS | correct | 10-K line 00750; XBRL `EarningsPerShareDiluted`, FY2025, $1.14 | Matches. |
| 6 | Return on average equity | correct | 10-K lines 00720 and 00747; equity $2,830.607M (2025) and $3,655.546M (2024) | 47.36% matches. Equity fell after substantial buybacks, which raises ROE. The report does not explain this effect. |
| 7 | Debt/equity, including current portion of long-term debt | **missing** | `LongTermDebt` = 0; no current debt; $500M revolver undrawn (10-K line 604) | The original report never states debt/equity. Verified against the filings: no borrowings and no current portion (10-K lines 00702-00713, 01334), so the answer is **0.00x** on a borrowings basis (1.79x if leases are counted). The reviewed draft states 0.00x. Total liabilities of $6.16B (10-K line 713) are mostly leases, so do not use that for D/E. |
| 8 | Free cash flow | **wrong** | 10-K lines 00818 and 00820; cash from operations $2,113.926M − capex $666.336M | The reported FCF value $1.448B is right, but the report's displayed arithmetic subtracts `$666.3B`, which does not produce that result. The capex unit error makes the calculation as presented wrong. |
| 9 | Latest release quarterly revenue | correct | Release line 70: $3,293,162K; line 18: "$3.3 billion" | The report says $3.3B, which is rounded but right. |
| 10 | Quarterly revenue growth versus prior-year quarter | correct | Release lines 18 and 70: +9.6% | Matches. |
| 11 | Latest release GAAP diluted EPS | **missing** | Release lines 22 and 88: $0.27 vs $0.29 | The report never gives Q3 EPS. EPS fell 6.9%, and the report leaves it out. |

Core result: wrong 2, unsupported 0, **errors = 2**, missing 2.

Other claim rows listed below: **18**  Wrong: **4**  Unsupported: **3**  Missing: **0**. Some rows group related numbers. Repeated claims elsewhere in the report still need review.

Detail on the other claims:

| Claim in report | Status | Source and note |
|---|---|---|
| 3,938 U.S. and 104 international restaurants | correct | 10-K line 179 |
| Digital sales 36.7% of revenue in 2025 | correct | 10-K line 205 (FY2025 food and beverage revenue) |
| Digital 38.8% in Q3 2026 "vs. 36.7% in 2025" | **unsupported** | Release line 27 compares 38.8% with **36.7% for Q3 2025**. The report compares a quarter with a full year and cites line 00024, which is the openings bullet. |
| Capex `$666.3B` | **wrong** | Fact is $666,336,000, about $666.3M. Same 1,000x unit error. |
| Q3 operating margin 13.7% vs 15.9%; comps +2.1% | correct, citation incomplete | Release line 20 gives the margins; line 19 gives comparable sales growth. The original report cites lines 00020-00022 and omits the comparable-sales citation. |
| "84 new U.S. locations" | **unsupported** | Release line 24 says 84 *company-owned* restaurants. It does not say all 84 were in the U.S. |
| 53 new locations with Chipotlanes | correct | Release line 24. Verify the exact wording when you re-open the line. |
| 5 international partner-operated openings | correct | Release line 24. Verify the exact wording when you re-open the line. |
| Expansion in "Middle East, South Korea" cited to 10-K lines 186-188 | **unsupported** | Those lines cover Food with Integrity and talent. The countries appear in the release (line 61). Fix the citation. |
| "Responsibly Raised®" | correct | 10-K line 188 |
| "90% leadership roles" filled internally | **wrong** | 10-K line 209 says **nearly 90%** of in-restaurant leadership roles. Keep “nearly.” |
| Prior-year revenue `$11,313.9B` | **wrong** | 10-K line 00732 reports FY2024 revenue of `$11,313,853 thousand`, or about `$11.314B`. The report's figure is 1,000x too high. |
| "4.5% YoY food cost inflation" | **wrong** | 10-K line 517: food, beverage and packaging cost *dollars* rose 4.5%. Inflation was 0.4% (line 519). The report mislabels growth as inflation. |
| "7.2% YoY labor cost increase" | correct | 10-K line 526 (dollars, $2,991.7M vs $2,789.8M) |
| $1.6B repurchase authorization left; $110M bought in Q3 | correct | Release line 35 |
| Price $27.98, P/E 24.54 | correct | Manifest quote 2026-10-27; 27.98 ÷ 1.14. See the Lab 02 step 5 caveat. |
| Peer margins MCD 46.10%, YUM 31.34%, CAVA 4.69% | correct | Recomputed from each peer's latest 10-K statement values and matched to the saved Company Facts. See [`CMG_LAB02_STEP7_PEER_CHECK.md`](CMG_LAB02_STEP7_PEER_CHECK.md). |
| Cash from operations $2.114B | correct | XBRL FY2025 $2,113,926,000 |

## Recommendation review

The report says **Buy**, driven by 9.6% Q3 revenue growth. The sourced evidence points both ways, and the report does not say so:

- Q3 diluted EPS fell 6.9% ($0.27 vs $0.29, release line 22). The report omits this.
- Operating margin fell 2.2 points, 15.9% to 13.7% (release line 20). The report says free cash flow and buybacks "offset" this, with no evidence.
- Comps grew only 2.1%, with transactions up 0.8% (release line 27).
- ROAE of 47% is inflated because buybacks shrank equity.
- The valuation uses FY2025 EPS, not current earnings. The report gives no price target or valuation range.
- The report does not state any uncertainty, so the last required-parts box stays unchecked.

**Reviewed draft (`CMG_lab03_reviewed_draft_20261102.md`), checked 2026-11-02:** all cited lines match the saved text (10-K lines 00179, 00188, 00205, 00209, 00517, 00519, 00526, 00604, 00720, 00732, 00743, 00747, 00750, 00818, 00820, 01334; release lines 00018-00020, 00022, 00024, 00027, 00035, 00061, 00070, 00088). Its figures recompute. It fixes the unit errors, the "inflation" label, the quarter-versus-year digital comparison, the "U.S." openings claim and the "nearly 90%" wording. It states debt/equity as 0.00x and gives a **Hold** with the evidence (revenue +9.6%, EPS −6.9%, margin −2.2 points, P/E 24.54x on historical EPS) and an explicit statement that no forecast or target exists. The Hold follows from that evidence. Remaining limits: the peer margins mix franchisors with a company-operated chain, and the 24.54x P/E uses FY2025 EPS. The draft is more careful than the original, but the original report is what the audit grades unless your instructor accepts the revised one.

## Required report parts

- [x] Overview
- [x] Market Positioning and Growth Outlook
- [x] Valuation Insights
- [x] Future Developments and Strategic Recommendations
- [x] Investment Recommendation
- [ ] Recommendation follows from sourced evidence and states uncertainty

## Your verification before submission

- [x] Check the CMG filing selection against EDGAR. Done 2026-11-02 (AI-assisted): -000103 is the newest Item 2.02 8-K. Re-confirm on EDGAR before you sign.
- [x] Check the Lab 02 Step 4 debt facts against the 10-K. Done 2026-11-02 (AI-assisted): no debt on the balance sheet, no outstanding borrowings (line 01334), current debt = $0. Re-open those lines yourself.
- [x] Redo the Lab 02 ratios from the printed inputs. Done 2026-11-02 (AI-assisted): all recompute; D/E = 0.00x on borrowings. Confirm your class's debt definition (leases in or out).
- [x] Review and agree with the seven Lab 02 checks recorded above. Step 4 and Step 5 remain marked incorrect for the original run because current debt was null and debt/equity was unavailable. The CMG Step 7 peer figures and source lines are recorded above and in `CMG_LAB02_STEP7_PEER_CHECK.md`.
- [x] CMG: all eleven core claims, other material numbers, citations and the recommendation checked against the filings. User confirmed the findings on 2026-11-02. The original Buy is not supported; the reviewed Hold is.
- [x] Review and agree with the filing-review findings and corrected drafts for COST, WMT, TGT, BJ, AAPL, and MSFT. User confirmed on 2026-11-02. See `LAB03_ALL_TICKERS_RUN_STATUS.md` for report-specific findings.
- [ ] Ask your partner to check two Lab 02 marks and two CMG report claims. Record the source lines for the claims.
- [ ] Complete the partner reflection and submit Checkpoint 1 in Brightspace with a commit link the grader can open.

Partner-selected company: Chipotle Mexican Grill, Inc.  Ticker: CMG  Reported this month: Oct 28, 2026 (Q3 2026 release)

Partner checked two claims: ____________________ / ____________________

Student verification completed: **Yes — 2026-11-02**  Partner reflection completed: ________  Brightspace Checkpoint 1 submitted: ________  Commit permalink: ____________________
