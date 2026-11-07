# CrewAI Flow and process demo

This small project compares CrewAI's two process implementations inside a CrewAI Flow.

- `Process.sequential` runs the tasks in the order set in the code.
- `Process.hierarchical` gives task assignment to a manager model.
- The Flow routes to one process based on the `--process` command-line value.
- Each run saves its result under `output/`.

The hierarchical path is a separate comparison. The Lab 4 equity desk should keep its analyst and verifier nodes in a fixed Flow order.

## Python and package management

Use Python 3.12 and `uv`. The demo reads `API_KEY`, `GENAI_MODEL`, and
`GENAI_BASE_URL` from the course `.env` file in the project root at run time.
It does not copy the key into this demo folder, print it, or save it with the
result. Keep the root `.env` private and out of Git.

```bash
cd WEEK_3/week3_process_demo
uv sync
```

The course `.env` must contain the three settings above. If `GENAI_BASE_URL`
is absent, the demo uses Purdue GenAI Studio's OpenAI-compatible endpoint.

## Run one process mode

```bash
uv run kickoff --process sequential
uv run kickoff --process hierarchical
```

The first command assigns `Process.sequential` to the `Crew` constructor. The
second assigns `Process.hierarchical` and provides a manager agent. Both paths
use the configured Purdue GenAI Studio model.

To pass other evidence to the demo:

```bash
uv run kickoff --process sequential --evidence "Revenue increased 8% year over year."
```

These commands call a model. The hierarchical path delegates task assignment
to the manager model. The Flow code chooses which process path runs.


## Run the paper's Research Analyst role

The `research-analyst` command is a local CrewAI prototype of the Research
Analyst role in Francis and Zhang (2026). It uses one agent and one task. It
searches the saved 10-K Business and MD&A sections and the saved earnings
release Exhibit 99.1. It asks the agent to cite exact source line numbers for
each claim. It does not use web search, calculate ratios, or make an investment
recommendation.

The command reads `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) from the course `.env`
file. It uses `GEMINI_MODEL` if set. Otherwise, it uses `gemini-3.8-flash`.
To run it on the saved Costco filings:

```bash
cd WEEK_3/week3_process_demo
uv run research-analyst ../../WEEK_2/runs/COSTCO_WHOLESALE_CORP_NEW_20261027_092302_EDT
```

The command saves `research_analyst_report.md` in that filing run folder. It
calls Gemini and uses the API key's quota. The command has not been run as part
of this setup.

## Lab 4 fixed-order agent team

`lab4` runs the seven existing SEC data steps as separate CrewAI tools. It then
runs the four analyst roles, the Strategy Manager, and the Verifier in a fixed
CrewAI Flow. It reads `API_KEY`, `GENAI_MODEL`, `GENAI_BASE_URL`, and
`SEC_USER_AGENT` from the private course `.env`. It does not save the key in a
run folder.

Install or sync the dependencies from this folder:

```bash
uv sync
```

Run the Lab 4 COST example with the Lab 03 price and peers:

```bash
PYTHONPATH=src uv run python -m week3_process_demo.lab4_flow COST --peers WMT,TGT,BJ --price 992.13
```

Run the Verifier only on a saved run:

```bash
PYTHONPATH=src uv run python -m week3_process_demo.lab4_flow --verify-only "/absolute/path/to/WEEK_3/lab4_runs/COST_run_folder"
```

Each normal run creates a new dated folder in `WEEK_3/lab4_runs/`. The run
contains saved filings, facts, each node's JSON input and output, the report,
and the verified report. The Verifier's marks go below the filings line.

## Lab 5 local page

From this folder, start the page:

```bash
PYTHONPATH=src uv run python -m week3_process_demo.lab5_ui
```

Open `http://127.0.0.1:8765` in a browser. Enter a ticker, optional comma-separated peers, and an optional price. The page shows node progress and the verified report when the run finishes. The existing command-line entry point remains available.

The Lab 5 Flow reads optional expert philosophies from the installed `financial-researcher` skill at `~/.codex/skills/financial-researcher/experts/`. These are analysis guidance, not sources for company facts. The Financial Datasets and Tavily MCP servers are not required for the SEC-only Flow.

Step 7 keeps each peer's latest 10-K margin and fiscal year-end for the filing check. The persona peer score uses trailing-12-month (TTM) margins. It calculates each TTM margin as the latest 10-K annual value plus the latest 10-Q year-to-date value minus the comparable prior-year year-to-date value. It compares periods that end within 45 days on either side of the company's TTM end. This allows different fiscal year-ends while keeping the measured periods close. It reports `insufficient evidence` if the facts do not support the calculation or period window. It does not compare unmatched annual margins as if they covered the same period.

The Manager checks that each role returns exactly one source-line Insight and that it does not repeat a financial figure or period length from the earnings release opening paragraph. The Verifier marks all three Insights, checks cited lines against the full saved filing texts in code, and omits the Investment Advisor's thesis from its audit.

The latest COST run is saved under `../lab4_runs/COSTCO_WHOLESALE_CORP_NEW_20261107_151455_820621_EST/`. The CMG run under `../lab4_runs/CHIPOTLE_MEXICAN_GRILL_INC_20261107_152356_740181_EST/` is a technical practice run. CMG's selected earnings filing was accepted on October 28, 2026, so it does not meet a November “reported this month” requirement. Use a partner-selected eligible ticker for that check.
