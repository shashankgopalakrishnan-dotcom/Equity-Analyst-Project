# AAPL Lab 03 report audit

**Status:** AI-assisted filing audit. The user confirmed AI may be used for this audit. The partner check remains separate and is not recorded here.

**Report:** `AAPL_lab03_report_20261101_093730.md`
**10-K:** `0000320193-25-000079`, year ended 2025-09-27
**Release:** Exhibit 99.1 to 8-K `0000320193-26-000018`, Q3 FY2026

## Eleven required claims

| # | Claim | Result | Filing check |
|---:|---|---|---|
| 1 | FY2025 revenue | Correct | $416.161B; 10-K lines 00407 and 00562. Prior year $391.035B. |
| 2 | Annual revenue growth | **Missing** | `(416.161 / 391.035) − 1 = 6.43%`; the report does not state it. |
| 3 | Operating income and margin | Correct | $133.050B; `$133.050B / $416.161B = 31.97%`; line 00572. |
| 4 | Net income | Correct | $112.010B; line 00576. |
| 5 | FY diluted EPS | Correct | $7.46; lines 00579 and 00792. |
| 6 | Return on average equity | Correct | `$112.010B / (($73.733B + $56.950B)/2) = 171.42%`; equity lines 00648 and 00678. |
| 7 | Debt/equity including current debt | Correct | `($78.328B + $12.350B)/$73.733B = 122.98%`; debt lines 00635 and 00638; equity line 00648. |
| 8 | Free cash flow | Correct | `$111.482B − $12.715B = $98.767B`; 10-K lines 00704 and 00709. |
| 9 | Latest-quarter revenue | Correct, rounded | $109.417B; release lines 00010, 00043 and 00088. |
| 10 | Latest-quarter revenue growth | Correct | 16% year over year; release line 00010. |
| 11 | Latest-quarter diluted GAAP EPS | Correct | $2.02, up 29%; release lines 00010 and 00070. |

**Core result:** 10 correct, 0 wrong, 1 missing. The annual growth calculation is the missing required claim.

## Other claims, citations, and recommendation

- The report's principal annual values match the 10-K, but several citations do not. Revenue, operating income, and net income should cite lines 00562, 00572, and 00576. Line 00142 is business description; line 00155 describes Services; line 00479 explains tax-rate drivers, not net income or the numeric effective tax rate.
- Q3 FY2026 release figures are accurate: revenue $109.417B (rounded to $109.4B), 16% growth, and diluted EPS $2.02 with 29% growth. The release also says tariff refunds contributed about two percentage points to gross margin and $0.11 to diluted EPS (line 00010). Include this when explaining the quarter.
- The P/E of 46.53x recalculates as `$347.10 / $7.46 = 46.53x`. It uses FY2025 EPS, not trailing or forecast EPS for the 2026 share-price date. The report's citation `[pe line 00000]` is not a filing citation. Cite the price source and 10-K EPS separately.
- The 2025 iPhone 17 product introductions are listed in 10-K lines 00376–00389. The report should state that they were listed as products introduced during the fiscal year and keep the period clear.
- Siri AI was discussed in the Q3 2026 earnings release, where Apple says it was introduced at WWDC26 (release line 00011). Cite the release rather than 10-K lines 00387–00389 for that development. Treat it as a product development, not proof of future financial results.
- The $100B repurchase authorization is supported by 10-K lines 00360 and 00498. The report should distinguish the authorization from completed repurchases; the filing says $221M had been used as of 2025-09-27.
- The 15.6% effective tax rate is supported by 10-K lines 00474–00477. Cite line 00477 for the rate; line 00479 explains some drivers.
- The $56.2B manufacturing purchase obligations are supported by 10-K line 00490. The filing says $55.4B was payable within 12 months; include this date and timing if discussing the commitment.
- The Buy thesis omits the one-time $0.11 Q3 tariff-refund EPS benefit and uses a trailing FY2025 P/E of 46.53x without discussing valuation risk. The recommendation says risks are outweighed but supplies no valuation range or explicit uncertainty. Reassess after adding the annual growth claim and these caveats.

## Result

Add annual revenue growth of 6.43%. Replace unsupported or mismatched citations for the product, Siri, tax, buyback, and supply commitments. State that Q3 EPS includes a $0.11 one-time tariff-refund benefit. Student hand audit and partner check remain pending.
