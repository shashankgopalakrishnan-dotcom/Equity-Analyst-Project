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
