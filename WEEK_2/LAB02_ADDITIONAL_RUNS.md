# Lab 02 additional ticker runs

**Run date:** October 29, 2026
**Prompt:** `PROMPT_LIBRARY/LAB02_RECONSTRUCTED_PROMPT.md`
**Program:** `WEEK_2/desk.py`

These runs completed steps 1 through 7. Each run folder contains the downloaded filing text, earnings-release exhibit text, company facts, and run output.

| Ticker | Peers | Command | Final run folder | Notes |
|---|---|---|---|---|
| TGT | WMT, COST, BJ | `python3.12 WEEK_2/desk.py TGT --peers WMT,COST,BJ` | `WEEK_2/runs/TARGET_CORP_20261029_000915_EDT` | The latest earnings 8-K uses Exhibit 99, not Exhibit 99.1. The program saved the identified release as `earnings_release_exhibit_99.txt`. Current debt uses `LongTermDebtAndCapitalLeaseObligationsCurrent`. |
| BJ | COST, WMT, TGT | `python3.12 WEEK_2/desk.py BJ --peers COST,WMT,TGT` | `WEEK_2/runs/BJ_s_Wholesale_Club_Holdings_Inc._20261029_000808_EDT` | The release is Exhibit 99.1. |
| MSFT | AAPL | `python3.12 WEEK_2/desk.py MSFT --peers AAPL` | `WEEK_2/runs/MICROSOFT_CORP_20261029_000818_EDT` | The release is Exhibit 99.1. AAPL and MSFT fiscal year ends differ. |

No `--price` was provided for these three runs, so the program did not calculate P/E. COST, WMT, and AAPL already have earlier runs in `WEEK_2/runs/`. No instructor-provided price was available for the new runs.

## Scope

The script prints the selected filing accession numbers and EDGAR index accepted times. It saves the 10-K, 10-Q, earnings 8-K, earnings release exhibit, and Company Facts data. It prints same-fiscal-year annual facts and calculations, checks the release text for quarterly revenue and diluted EPS, and calculates peer operating margins.

This record confirms program runs and saved files. It does not mark the student’s handwritten worksheet or partner check as complete.
