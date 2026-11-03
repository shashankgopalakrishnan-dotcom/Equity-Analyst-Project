"""Filing-grounded CrewAI prototype of the Research Analyst in Francis & Zhang (2026)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Literal

from crewai import Agent, Crew, LLM, Process, Task
from crewai.tools import BaseTool
from pydantic import BaseModel, Field


COURSE_ROOT = Path(__file__).resolve().parents[4]
COURSE_ENV = COURSE_ROOT / ".env"
DEFAULT_MODEL = "gemini-3.8-flash"


class FilingSearchInput(BaseModel):
    query: str = Field(description="Words or a short phrase to find in the filing text.")
    document: Literal["10-K", "release"] = Field(
        description="Search the 10-K Business/MD&A text or the earnings-release Exhibit 99.1."
    )


class FilingSearchTool(BaseTool):
    name: str = "search_sec_filing"
    description: str = (
        "Search the supplied company's 10-K Business and MD&A sections, or its "
        "earnings-release Exhibit 99.1. Returns exact filing lines with their "
        "source line numbers. Use these results to support every factual claim."
    )
    args_schema: type[BaseModel] = FilingSearchInput
    documents: dict[str, list[str]] = Field(default_factory=dict, exclude=True)
    max_usage_count: int = 10

    def _run(self, query: str, document: Literal["10-K", "release"]) -> str:
        lines = self.documents.get(document, [])
        terms = {
            term for term in re.findall(r"[a-z0-9]+", query.lower()) if len(term) > 2
        }
        if not lines or not terms:
            return "No searchable filing text was available for that request."

        ranked: list[tuple[int, int, str]] = []
        for index, line in enumerate(lines):
            lowered = line.lower()
            score = sum(lowered.count(term) for term in terms)
            if score:
                ranked.append((score, index, line))
        ranked.sort(key=lambda item: (-item[0], item[1]))
        selected = sorted(ranked[:8], key=lambda item: item[1])
        if not selected:
            return f"No lines matched {query!r} in {document}. Try different keywords."

        excerpts = []
        for _, _, line in selected:
            excerpts.append(line[:1200])
        label = "10-K Business/MD&A" if document == "10-K" else "Exhibit 99.1"
        return f"Source: {label}\n" + "\n".join(excerpts)


def read_env(path: Path) -> dict[str, str]:
    """Read simple KEY=value entries without printing credential values."""
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


def extract_section(lines: list[str], start: re.Pattern[str], end: re.Pattern[str]) -> list[str]:
    start_index = next((i for i, line in enumerate(lines) if start.search(line)), None)
    if start_index is None:
        raise ValueError("The requested 10-K section was not found.")
    end_index = next(
        (i for i in range(start_index + 1, len(lines)) if end.search(lines[i])),
        len(lines),
    )
    return lines[start_index:end_index]


def load_filing_documents(run_folder: Path) -> tuple[dict[str, list[str]], dict]:
    manifest_path = run_folder / "desk_manifest.json"
    ten_k_path = run_folder / "10k.txt"
    release_path = run_folder / "earnings_release_exhibit_99_1.txt"
    missing = [p.name for p in (manifest_path, ten_k_path, release_path) if not p.is_file()]
    if missing:
        raise ValueError("Run folder is missing required files: " + ", ".join(missing))

    ten_k_lines = ten_k_path.read_text(encoding="utf-8", errors="replace").splitlines()
    business = extract_section(
        ten_k_lines,
        re.compile(r"^\d{5}:\s*Item\s+1[—–-]\s*Business\b", re.IGNORECASE),
        re.compile(r"^\d{5}:\s*Item\s+1A[—–-]", re.IGNORECASE),
    )
    mda = extract_section(
        ten_k_lines,
        re.compile(r"^\d{5}:\s*Item\s+7[—–-]", re.IGNORECASE),
        re.compile(r"^\d{5}:\s*Item\s+7A[—–-]", re.IGNORECASE),
    )
    release_lines = release_path.read_text(
        encoding="utf-8", errors="replace"
    ).splitlines()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    return {"10-K": business + mda, "release": release_lines}, manifest


def make_payload(manifest: dict) -> dict:
    filings = manifest.get("filings", {})
    ten_k = filings.get("10k", {})
    release = filings.get("earnings_8k", {})
    return {
        "task": (
            "Assess the company's business model, competitive position, catalysts, "
            "and recent developments. Use the 10-K Business/MD&A sections and the "
            "earnings-release Exhibit 99.1. Search the filing text when you need evidence."
        ),
        "context": {
            "company": manifest.get("company", "Unknown company"),
            "ticker": manifest.get("ticker", "Unknown ticker"),
            "10-K_accession": ten_k.get("accessionNumber", "not recorded"),
            "earnings_8-K_accession": release.get("accessionNumber", "not recorded"),
            "available_sources": [
                "10-K Item 1 Business",
                "10-K Item 7 Management's Discussion and Analysis",
                "earnings-release Exhibit 99.1",
            ],
        },
        "expected_output": (
            "A concise Markdown research brief with headings for Business Model, "
            "Competitive Position, Catalysts, and Recent Developments. Cite each "
            "factual claim with the source document and exact line number. Include "
            "a short supporting quotation for each claim. Mark missing evidence as "
            "not found. Do not calculate ratios or make a Buy/Hold/Sell recommendation."
        ),
    }


def create_research_analyst(documents: dict[str, list[str]], model_name: str, api_key: str) -> Crew:
    model = model_name if "/" in model_name else f"gemini/{model_name}"
    llm = LLM(
        model=model,
        api_key=api_key,
        timeout=120,
        max_output_tokens=3000,
    )
    filing_search = FilingSearchTool(documents=documents)
    analyst = Agent(
        role="Research Analyst",
        goal=(
            "Produce a filing-grounded qualitative research brief on the business model, "
            "competitive position, catalysts, and recent developments."
        ),
        backstory=(
            "You are the qualitative and filings analyst on an equity research team. "
            "You distinguish reported facts from management expectations and do not "
            "invent support for a claim."
        ),
        tools=[filing_search],
        llm=llm,
        allow_delegation=False,
        max_iter=10,
        max_rpm=6,
        verbose=False,
    )
    task = Task(
        description=(
            "You are the Research Analyst role from the paper's four-agent system. "
            "Your complete request is the JSON value below. It has task, context, "
            "and expected_output fields. Follow all three fields. Use the "
            "search_sec_filing tool to retrieve exact evidence. The tool can access "
            "only the 10-K Business/MD&A sections and Exhibit 99.1 supplied for this run. "
            "Cite only line numbers returned by the tool. Do not use outside knowledge. "
            "Do not create a financial recommendation or calculate ratios.\n\n"
            "Request JSON:\n{agent_request}"
        ),
        expected_output=(
            "The Markdown research brief specified in the request JSON, with exact "
            "source line citations and supporting quotations for factual claims."
        ),
        agent=analyst,
    )
    return Crew(
        agents=[analyst],
        tasks=[task],
        process=Process.sequential,
        max_rpm=6,
        verbose=False,
    )


def kickoff() -> None:
    parser = argparse.ArgumentParser(
        description="Run the filing-based Research Analyst role from Francis & Zhang (2026)."
    )
    parser.add_argument(
        "run_folder",
        type=Path,
        help="Lab 02 run folder with desk_manifest.json, 10k.txt, and Exhibit 99.1 text.",
    )
    parser.add_argument("--model", default=None, help="Optional Gemini model ID override.")
    args = parser.parse_args()

    run_folder = args.run_folder.expanduser().resolve()
    env = read_env(COURSE_ENV)
    api_key = env.get("GOOGLE_API_KEY", "").strip() or env.get("GEMINI_API_KEY", "").strip()
    model_name = (args.model or env.get("GEMINI_MODEL", DEFAULT_MODEL)).strip()
    if not api_key:
        parser.error("Set GOOGLE_API_KEY or GEMINI_API_KEY in the course .env file.")
    try:
        documents, manifest = load_filing_documents(run_folder)
        payload = make_payload(manifest)
        crew = create_research_analyst(documents, model_name, api_key)
        result = crew.kickoff(inputs={"agent_request": json.dumps(payload, ensure_ascii=False)})
    except Exception as exc:
        print(
            "Research Analyst run failed. Check the run-folder files, Gemini model access, "
            f"and API quota. Error type: {type(exc).__name__}.",
            file=sys.stderr,
        )
        raise SystemExit(1) from None

    content = result.raw
    if api_key:
        content = content.replace(api_key, "[REDACTED]")
    filing = payload["context"]
    header = (
        f"# Research Analyst: {filing['company']} ({filing['ticker']})\n\n"
        f"10-K accession: {filing['10-K_accession']}  \n"
        f"Earnings 8-K accession: {filing['earnings_8-K_accession']}  \n"
        f"Model: {model_name}  \n"
        f"Generated: {datetime.now().astimezone().isoformat(timespec='seconds')}\n\n"
    )
    output_path = run_folder / "research_analyst_report.md"
    output_path.write_text(header + content.rstrip() + "\n", encoding="utf-8")
    print(f"Saved Research Analyst report to {output_path}")


if __name__ == "__main__":
    kickoff()
