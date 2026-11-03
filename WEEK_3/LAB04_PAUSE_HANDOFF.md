# Lab 04 resume checkpoint

**Updated:** 2026-11-03, America/Indiana/Indianapolis  
**Workspace:** `/Users/shashankgopalakrishnan/Documents/Courses/Mastering AI for finance`

## Completed

- The Lab 4 skill-aligned prompt is saved at `PROMPT_LIBRARY/LAB04_RECONSTRUCTED_PROMPT_SKILL_ALIGNED.md`. The original reconstructed prompt is preserved.
- The four role instructions include compatible methods from the installed Financial Researcher skill: value, growth, quality, cash flow, leverage, and risk. The course graph still has four roles and a Verifier. It does not add nine investor agents or unconfigured MCP services.
- The latest full COST run completed the seven data steps, all four roles, the Manager review and revision, and the Verifier. See `WEEK_3/lab4_runs/COSTCO_WHOLESALE_CORP_NEW_20261103_142427_181525_EST/`.
- The report shows Q4 total revenue of $95,723 million and diluted EPS of $6.75. It keeps the exact release lines. The report includes current and prior SEC facts, code-calculated ratios, and peer facts for WMT, TGT, and BJ.
- The latest normal-run verification is `WEEK_3/lab4_runs/COSTCO_WHOLESALE_CORP_NEW_20261103_142427_181525_EST/COST_verified_report_20261103_142702_458468_EST.md`. It contains one marks table under the filing line and records 85 correct, 0 wrong, and 0 unsupported marks. The Verifier input omits the Investment Advisor section.
- The run folder stores all three filing texts, the Exhibit 99.1 release text, Company Facts, peer data, and node inputs and outputs.
- Lab 04 V is complete. The seeded EPS error was marked wrong and corrected with 10-K line `00638`; the invented growth claim was marked wrong and corrected to `10.14%` with the arithmetic and 10-K source; the clean copy passed all eleven core claim areas with 12 correct detailed marks and no wrong or unsupported marks. The skip test found no verifier bypass flag. Full results: `WEEK_3/LAB04_V_TEST_RESULTS.md`.
- One XBRL gap item was worked in a separate AI agent conversation while COST ran. The computer-use tool could not open a visible browser chat tab.
- `.env` remains ignored by Git. No key was printed or copied. No commit or push was made.

## Still pending for class

1. Have the partner check one Costco filing citation.
2. Complete the Orchestrator/Evaluator questions and the Reflect discussion.
3. Confirm the Checkpoint 1 Brightspace submission. It is not verified here.

## Resume command

Run from `WEEK_3/week3_process_demo/`:

```bash
PYTHONPATH=src uv run python -m week3_process_demo.lab4_flow COST --peers WMT,TGT,BJ --price 992.13
```

To verify an existing run without fetching data or running other nodes:

```bash
PYTHONPATH=src uv run python -m week3_process_demo.lab4_flow --verify-only "/absolute/path/to/WEEK_3/lab4_runs/COST_run_folder"
```
