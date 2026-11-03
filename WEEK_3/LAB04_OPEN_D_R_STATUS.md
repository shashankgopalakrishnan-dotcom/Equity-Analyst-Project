# Lab 04 status

**Checked:** 2026-11-03  
**Scope:** Open, D, R, I, and V. Reflect and partner work remain outstanding.

## Open, D, and R

- The seven-step desk and saved COST Lab 03 report are available under `WEEK_2/`.
- The user's one-line Kasparov response is in `WEEK_3/KASPAROV_RESPONSE.md`.
- CrewAI Flows is the selected framework. The project uses Python 3.12 and CrewAI 1.15.34.
- The partner must still check one cited Costco number against its filing.
- One XBRL gap item was worked in a separate AI agent conversation while a COST run was active. The computer-use tool could not open a visible browser chat tab.
- The user must confirm the Checkpoint 1 Brightspace submission. It is not verified here.

## I — build and run

- Implemented the Lab 4 flow in `WEEK_3/week3_process_demo/src/week3_process_demo/lab4_flow.py`.
- Added separate role instructions in `WEEK_3/week3_process_demo/src/week3_process_demo/roles/`.
- Wrapped each existing SEC data step as a separate CrewAI tool. The normal graph order is fixed in code: seven data steps, Research Analyst, Financial Analyst, Investment Advisor, Strategy Manager, Verifier.
- Each role gets one model call with JSON fields `task`, `context`, and `expected_output`. The Manager can request one revision per affected role. The Verifier always runs on a normal run. `--verify-only` starts only the Verifier.
- The flow reads the Purdue model key and SEC User-Agent from the private course `.env`. It does not save either value. `git check-ignore -v .env` confirms that `.env` is ignored.
- Python compilation, the `uv` run command, and `git diff --check` completed successfully after the skill-aligned changes.
- The latest full run completed the required sequence: seven data steps, Research Analyst, Financial Analyst, Investment Advisor, Strategy Manager, and Verifier. Its folder is `WEEK_3/lab4_runs/COSTCO_WHOLESALE_CORP_NEW_20261103_142427_181525_EST/`.
- The report has the five required top-level sections. Its first line lists the 10-K, 10-Q, and Item 2.02 8-K with accession numbers and Accepted times. Its second line gives the run time. Filing texts, Company Facts, peer data, and node input/output files are saved in the run folder.
- The report shows latest-quarter total revenue as $95,723 million and diluted EPS as $6.75. It quotes the exact release lines. It also includes current and prior annual facts, calculator arithmetic, and current and prior facts for WMT, TGT, and BJ.
- The latest verified report is `WEEK_3/lab4_runs/COSTCO_WHOLESALE_CORP_NEW_20261103_142427_181525_EST/COST_verified_report_20261103_142702_458468_EST.md`. The Verifier marked 85 claims correct, 0 wrong, and 0 unsupported. It omits the Investment Advisor section from its input and preserves that section in the report.
- The installed Financial Researcher skill informed the role instructions and the value, growth, quality, cash-flow, leverage, and risk lenses. The fixed course graph remains unchanged. The code does not add investor agents or unconfigured MCP data services.
- The skill-aligned prompt is `PROMPT_LIBRARY/LAB04_RECONSTRUCTED_PROMPT_SKILL_ALIGNED.md`. The original reconstructed prompt remains unchanged.
- No files were pushed to GitHub. `.env` remains ignored and private.
- Lab 04 V is complete. The seeded EPS error was marked wrong and corrected to `$20.76` from 10-K line `00638`. The invented `14.14%` annual growth claim was marked wrong and corrected to `10.14%` from `$303,154 million` and `$275,235 million`. The clean report copy passed all eleven core claim areas; its 12 detailed marks were all correct. The skip test found no verifier bypass flag. See `WEEK_3/LAB04_V_TEST_RESULTS.md`. The normal run remains a course-audit draft, and the partner citation check is still separate.
- I did not run CrewAI AMP evaluation. The logged-out project still has `main.py` set to the earlier sequential/hierarchical demo, so its default evaluation would grade that demo rather than this Lab 4 command. The separate local Lab 4 command and live run were checked instead.

## Commands

Run these from `WEEK_3/week3_process_demo/`:

```bash
uv sync
PYTHONPATH=src uv run python -m week3_process_demo.lab4_flow COST --peers WMT,TGT,BJ --price 992.13
PYTHONPATH=src uv run python -m week3_process_demo.lab4_flow --verify-only "/absolute/path/to/WEEK_3/lab4_runs/COST_run_folder"
```

The price is the one used in the saved Lab 03 COST report.

## Still required for Lab 04

1. Have the partner check one Costco filing citation.
2. Complete the Orchestrator/Evaluator questions and Reflect discussion.
