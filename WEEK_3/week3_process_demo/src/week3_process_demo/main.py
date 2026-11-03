#!/usr/bin/env python
"""Compare CrewAI sequential and hierarchical processes inside a Flow.

This is a small learning demo. It does not call real financial data sources.
"""

import argparse
from pathlib import Path
from typing import Literal

from crewai import Agent, Crew, LLM, Process, Task
from crewai.flow import Flow, listen, router, start
from pydantic import BaseModel


COURSE_ROOT = Path(__file__).resolve().parents[4]
COURSE_ENV = COURSE_ROOT / ".env"
_MODEL_LLM: LLM | None = None


class ProcessDemoState(BaseModel):
    process_mode: Literal["sequential", "hierarchical"] = "sequential"
    evidence: str = "Sample evidence: revenue increased 8% year over year."
    result: str = ""
    output_path: str = ""


def build_crew(
    process_mode: Literal["sequential", "hierarchical"], evidence: str
) -> Crew:
    """Build a Crew and assign its process implementation explicitly."""
    if _MODEL_LLM is None:
        raise RuntimeError("Model settings are not loaded. Run through kickoff().")

    analyst = Agent(
        role="Evidence Analyst",
        goal="State only what the supplied evidence supports.",
        backstory="You are a careful analyst. You do not add facts that are absent from the evidence.",
        llm=_MODEL_LLM,
        allow_delegation=False,
    )
    reviewer = Agent(
        role="Evidence Reviewer",
        goal="Check whether the analysis matches the supplied evidence.",
        backstory="You are a careful reviewer. You flag claims that the evidence does not support.",
        llm=_MODEL_LLM,
        allow_delegation=False,
    )

    analysis = Task(
        description=(
            "Analyze this evidence. State the reported change and quote the evidence. "
            "Do not add outside facts.\n\nEvidence: " + evidence
        ),
        expected_output="A short claim with the exact supporting evidence.",
        agent=analyst if process_mode == "sequential" else None,
    )
    review = Task(
        description=(
            "Review the analysis. Confirm whether each claim is supported by the "
            "same evidence. Correct any unsupported wording.\n\nEvidence: " + evidence
        ),
        expected_output="A corrected short claim, or a note that the claim is unsupported.",
        agent=reviewer if process_mode == "sequential" else None,
        context=[analysis] if process_mode == "sequential" else None,
    )

    agents = [analyst, reviewer]
    tasks = [analysis, review]

    if process_mode == "sequential":
        return Crew(
            agents=agents,
            tasks=tasks,
            process=Process.sequential,
            max_rpm=6,
        )

    manager = Agent(
        role="Evidence Manager",
        goal=(
            "Assign the two evidence tasks to the best team member, review the results, "
            "and return one concise, evidence-based conclusion."
        ),
        backstory=(
            "You coordinate a small evidence review team. Delegate each task once, "
            "then combine the supported findings without adding facts."
        ),
        llm=_MODEL_LLM,
        allow_delegation=True,
        max_iter=5,
        max_execution_time=180,
    )
    return Crew(
        agents=agents,
        tasks=tasks,
        process=Process.hierarchical,
        manager_agent=manager,
        max_rpm=6,
    )


class ProcessComparisonFlow(Flow[ProcessDemoState]):
    """Use code to route to the selected Crew process demo."""

    @start()
    def choose_process(self) -> str:
        print(f"Flow selected process: {self.state.process_mode}")
        return self.state.process_mode

    @router(choose_process)
    def route_process(self) -> Literal["sequential_path", "hierarchical_path"]:
        if self.state.process_mode == "sequential":
            return "sequential_path"
        return "hierarchical_path"

    @listen("sequential_path")
    def run_sequential(self) -> str:
        return self._run_crew("sequential")

    @listen("hierarchical_path")
    def run_hierarchical(self) -> str:
        return self._run_crew("hierarchical")

    def _run_crew(self, process_mode: Literal["sequential", "hierarchical"]) -> str:
        crew = build_crew(process_mode, self.state.evidence)
        result = crew.kickoff()
        self.state.result = result.raw

        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_path = output_dir / f"{process_mode}_process_demo.md"
        output_path.write_text(self.state.result, encoding="utf-8")
        self.state.output_path = str(output_path)
        print(f"Saved {process_mode} result to {output_path}")
        return self.state.result


def kickoff() -> None:
    global _MODEL_LLM

    parser = argparse.ArgumentParser(description="Compare CrewAI process modes.")
    parser.add_argument(
        "--process",
        choices=["sequential", "hierarchical"],
        default="sequential",
        help="Choose the Crew process that the Flow will run.",
    )
    parser.add_argument("--evidence", default=ProcessDemoState().evidence)
    args = parser.parse_args()

    env = read_env(COURSE_ENV)
    api_key = env.get("API_KEY", "").strip()
    model = env.get("GENAI_MODEL", "").strip()
    base_url = env.get("GENAI_BASE_URL", "https://genai.rcac.purdue.edu/api").strip()
    if not api_key or not model or not base_url:
        parser.error(
            "Set API_KEY, GENAI_MODEL, and GENAI_BASE_URL in the course .env file."
        )
    try:
        _MODEL_LLM = LLM(
            model=model,
            custom_openai=True,
            base_url=base_url,
            api_key=api_key,
            timeout=180,
        )
    except Exception:
        parser.error("Could not configure CrewAI for the Purdue GenAI endpoint.")

    flow = ProcessComparisonFlow()
    flow.kickoff(inputs={"process_mode": args.process, "evidence": args.evidence})


def read_env(path: Path) -> dict[str, str]:
    """Read key/value pairs without exposing credential values in output."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("\"'")
    return values


def plot() -> None:
    ProcessComparisonFlow().plot("process_demo_flow.html", show=False)


if __name__ == "__main__":
    kickoff()
