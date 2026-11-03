# Lab 04 V — verifier test results

**Date:** 2026-11-03  
**Source run:** `WEEK_3/lab4_runs/COSTCO_WHOLESALE_CORP_NEW_20261103_142427_181525_EST/`  
The three tests below use copies of this run. The source run and its report were left unchanged.

## Seeded diluted-EPS error

In the copied report, I changed FY2026 diluted EPS from `$20.76` to `$21.76` and cited 10-K line `00638`.

The verifier marked the claim **wrong**. It corrected the value to `$20.76` and cited 10-K line `00638` and accession `0000909832-26-000093`. This copy has 11 other correct checks, 1 wrong check, and 0 unsupported checks.

- Test copy: `WEEK_3/lab4_runs/COST_V_seeded_EPS_error_20261103/`
- Verified report: `COST_verified_report_20261103_155952_971748_EST.md`

## Invented revenue-growth claim

In another copy, I added a claim that `$303,154 million` of FY2026 revenue and `$275,235 million` of FY2025 revenue imply `14.14%` growth.

The verifier marked the claim **wrong**. Its correction gives the arithmetic: `(303,154 / 275,235) - 1 = 10.14%`, with 10-K line `00625` and accession `0000909832-26-000093`. This copy has 85 other correct checks, 1 wrong check, and 0 unsupported checks.

- Test copy: `WEEK_3/lab4_runs/COST_V_invented_growth_20261103/`
- Verified report: `COST_verified_report_20261103_154329_762626_EST.md`

## Clean report

I used the corrected Lab 03 COST draft as the basis for a clean report copy. The copy contains all eleven audited core claim areas. The verifier marked all **12 detailed checks correct**, with **0 wrong** and **0 unsupported**. It produced 12 marks because it checked operating income and operating margin as separate items within one core claim.

- Test copy: `WEEK_3/lab4_runs/COST_V_clean_Lab03_reviewed_20261103/`
- Verified report: `COST_verified_report_20261103_155417_861984_EST.md`

## Verifier skip test

I searched `WEEK_3/week3_process_demo/src/week3_process_demo/lab4_flow.py`. The normal graph routes from `strategy_manager` to `verifier`. The CLI has `--verify-only`, which runs the Verifier alone. It has no `--skip-verifier`, `--no-verifier`, or equivalent bypass option.

## Code adjustments made during verification

The direct EPS test showed that the model could leave a line-cited EPS sentence unmarked. The clean report also showed that quarterly revenue growth could be mistaken for quarterly revenue. I added deterministic checks for annual diluted EPS against its 10-K per-share line, annual growth against two quoted 10-K revenues, and quarterly growth against the two amounts on the selected release line. The clean report then passed all core checks.

## Debug note

One report-edit attempt ran from `WEEK_3/week3_process_demo/` and used this relative file path in its Python command: `Path('WEEK_3/lab4_runs/COST_V_clean_Lab03_reviewed_20261103/COST_report.md').read_text()`. The path was relative to the package directory, so the file was not found. The exact exception was:

```text
FileNotFoundError: [Errno 2] No such file or directory: 'WEEK_3/lab4_runs/COST_V_clean_Lab03_reviewed_20261103/COST_report.md'
```

I reran the edit with the absolute workspace path. The Lab 4 verification commands completed.
