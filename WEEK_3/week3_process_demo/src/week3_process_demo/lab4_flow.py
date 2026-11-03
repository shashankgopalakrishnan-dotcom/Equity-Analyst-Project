"""Lab 4 fixed-order equity research team using CrewAI Flow."""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from crewai import Agent, LLM
from crewai.flow import Flow, listen, router, start
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

PACKAGE = Path(__file__).resolve().parent
COURSE_ROOT = Path(__file__).resolve().parents[4]
RUNS_ROOT = COURSE_ROOT / "WEEK_3" / "lab4_runs"
ROLE_DIR = PACKAGE / "roles"
PARTS = [
    "Overview",
    "Market Positioning and Growth Outlook",
    "Valuation Insights",
    "Future Developments and Strategic Recommendations",
    "Investment Recommendation",
]
_MODEL_LLM: LLM | None = None


def load_desk():
    path = COURSE_ROOT / "WEEK_2" / "desk.py"
    spec = importlib.util.spec_from_file_location("lab4_sec_desk", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load existing seven-step desk at {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def read_env(path: Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines() if path.exists() else []:
        line = raw.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            result[key.strip()] = value.strip().strip("\"'")
    return result


def dump(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


class StepInput(BaseModel):
    request: str = Field(default="Run the next fixed SEC data step.")


class VerifierMark(BaseModel):
    claim: str
    status: Literal["correct", "wrong", "unsupported"]
    reason: str
    correction: str = ""
    source: str = ""
    corrected_claim: str = ""


class VerifierResult(BaseModel):
    marks: list[VerifierMark] = Field(default_factory=list)


class DeskStepTool(BaseTool):
    name: str = "SEC data step"
    description: str = "Run one numbered step of the existing SEC and XBRL equity data desk."
    args_schema: type[BaseModel] = StepInput
    step_number: int = Field(exclude=True)
    run_context: Any = Field(exclude=True)

    def _run(self, request: str = "Run the next fixed SEC data step.") -> str:
        del request
        return self.run_context.run_step(self.step_number)


class RunContext:
    def __init__(self, ticker: str, peers: list[str], price: float | None, user_agent: str, folder: Path):
        self.desk = load_desk()
        self.ticker, self.peers, self.price = ticker.upper(), peers, price
        self.user_agent, self.folder = user_agent, folder
        self.cik = ""
        self.company = ""
        self.submissions: dict = {}
        self.filings: dict = {}
        self.facts: dict = {}
        self.calculations: dict = {}
        self.release: str = ""
        self.peer_results: list[dict] = []
        self.step_outputs: list[dict] = []
        self.release_lines: list[str] = []

    def run_step(self, step: int) -> str:
        io_dir = self.folder / "node_io"
        inputs = {"ticker": self.ticker, "peers": self.peers, "price": self.price, "step": step}
        dump(io_dir / f"step_{step}_input.json", inputs)
        if step == 1:
            self.cik, self.company = self.desk.cik_for(self.ticker, self.user_agent)
            result: Any = {"ticker": self.ticker, "cik": self.cik, "company": self.company}
        elif step == 2:
            self.submissions = self.desk.sec_json(f"{self.desk.DATA}/submissions/CIK{self.cik}.json", self.user_agent)
            self.filings = self.desk.select_filings(self.cik, self.submissions, self.user_agent)
            result = {}
            for key in ("10k", "10q", "earnings_8k"):
                row = self.filings[key]
                row["accepted"] = self.desk.accepted(row, self.cik, self.user_agent)
                result[key] = row
        elif step == 3:
            for key, filename in (("10k", "10k.txt"), ("10q", "10q.txt"), ("earnings_8k", "earnings_8k.txt")):
                row = self.filings[key]
                text = self.filings.get("earnings_8k_text") if key == "earnings_8k" else self.desk.filing_text(self.cik, row, self.user_agent)
                (self.folder / filename).write_text(self.desk.numbered(text), encoding="utf-8")
                if key == "earnings_8k":
                    exhibit = self.desk.locate_exhibit(self.cik, row, self.user_agent)
                    self.release = self.desk.plain_text(self.desk.sec_get(self.desk.accession_url(self.cik, row["accessionNumber"], exhibit), self.user_agent))
                    release_name = self.desk.release_text_filename(exhibit)
                    (self.folder / release_name).write_text(self.desk.numbered(self.release), encoding="utf-8")
                    self.filings["release_document"] = exhibit
                    self.filings["release_filename"] = release_name
            result = {"saved": ["10k.txt", "10q.txt", "earnings_8k.txt", self.filings["release_filename"]], "exhibit": self.filings["release_document"]}
        elif step == 4:
            self.facts = self.desk.build_company_facts(self.cik, self.user_agent, self.folder, self.ticker)
            result = self.facts
        elif step == 5:
            self.calculations = self.desk.calculate(self.facts, self.price)
            result = {"formulas": self._calculation_lines(), "values": self.calculations}
        elif step == 6:
            self.release = self.release or self._read_release()
            self.release_lines = self.desk.release_lines(self.release)
            result = {"release_lines": self.release_lines}
        elif step == 7:
            self.peer_results = []
            for peer in self.peers:
                pcik, pname = self.desk.cik_for(peer, self.user_agent)
                sub = self.desk.sec_json(f"{self.desk.DATA}/submissions/CIK{pcik}.json", self.user_agent)
                pfilings = self.desk.select_filings(pcik, sub, self.user_agent)
                pdir = self.folder / "peers" / re.sub(r"[^A-Za-z0-9._-]+", "_", pname)
                pdir.mkdir(parents=True, exist_ok=True)
                pb = self.desk.build_company_facts(pcik, self.user_agent, pdir, peer)
                margin = self.desk.calculate(pb, None)["operating_margin"]
                for key, filename in (("10k", "10k.txt"), ("10q", "10q.txt"), ("earnings_8k", "earnings_8k.txt")):
                    text = pfilings.get("earnings_8k_text") if key == "earnings_8k" else self.desk.filing_text(pcik, pfilings[key], self.user_agent)
                    (pdir / filename).write_text(self.desk.numbered(text), encoding="utf-8")
                self.peer_results.append({"ticker": peer, "company": pname, "cik": pcik, "facts": pb, "margin": margin,
                                          "filings": {k: {**pfilings[k], "accepted": self.desk.accepted(pfilings[k], pcik, self.user_agent)} for k in ("10k", "10q", "earnings_8k")}})
            result = [{"ticker": x["ticker"], "company": x["company"], "fiscal_end": x["facts"]["fiscal_end"], "margin": x["margin"], "facts": x["facts"]} for x in self.peer_results]
        else:
            raise ValueError(f"Unknown desk step {step}")
        record = {"step": step, "output": result}
        self.step_outputs.append(record)
        dump(io_dir / f"step_{step}_output.json", result)
        return json.dumps(record, ensure_ascii=False, default=str)

    def _read_release(self) -> str:
        path = self.folder / self.filings.get("release_filename", "earnings_release_exhibit_99_1.txt")
        text = path.read_text(encoding="utf-8", errors="replace")
        # Drop desk line-number prefixes for reuse by the release line finder.
        return "\n".join(re.sub(r"^\d{5}:\s*", "", line) for line in text.splitlines())

    def _calculation_lines(self) -> list[str]:
        b, c = self.facts, self.calculations
        def val(metric: str, period: str = "current"):
            item = b.get("values", {}).get(metric, {}).get(period)
            return item.get("val") if item else None
        rev0, rev1 = val("revenue"), val("revenue", "prior")
        op, inc = val("operating_income"), val("net_income")
        eq, old_eq = val("equity"), val("equity", "prior")
        debt, cur = val("long_term_debt"), val("current_debt")
        cfo, capex = val("cash_from_operations"), val("capex")
        eps = val("diluted_eps")
        return [
            f"Revenue growth = ({rev0} / {rev1}) - 1 = {c['revenue_growth']}" if c.get("revenue_growth") is not None else "Revenue growth unavailable",
            f"Operating margin = {op} / {rev0} = {c['operating_margin']}" if c.get("operating_margin") is not None else "Operating margin unavailable",
            f"Return on average equity = {inc} / (({eq} + {old_eq}) / 2) = {c['return_on_average_equity']}" if c.get("return_on_average_equity") is not None else "ROAE unavailable",
            f"Debt/equity = ({debt} + {cur}) / {eq} = {c['debt_to_equity']}" if c.get("debt_to_equity") is not None else "Debt/equity unavailable",
            f"Free cash flow = {cfo} - {capex} = {c['free_cash_flow']}" if c.get("free_cash_flow") is not None else "FCF unavailable",
            f"P/E = {self.price} / {eps} = {c['pe']}" if c.get("pe") is not None else "P/E unavailable",
        ]

    def manifest(self) -> dict:
        return {"ticker": self.ticker, "company": self.company, "cik": self.cik,
                "run_time_local": datetime.now().astimezone().isoformat(timespec="seconds"),
                "filings": {k: {x: v for x, v in row.items() if x != "_text"} for k, row in self.filings.items() if isinstance(row, dict)},
                "earnings_release_document": self.filings.get("release_document"),
                "facts": self.facts, "release_lines": self.release_lines, "share_price_input": self.price,
                "calculations": self.calculations,
                "peers": [{"ticker": x["ticker"], "company": x["company"], "fiscal_end": x["facts"]["fiscal_end"], "margin": x["margin"], "facts": x["facts"], "filings": x["filings"]} for x in self.peer_results]}


class Lab4State(BaseModel):
    ticker: str = ""
    peers: list[str] = Field(default_factory=list)
    price: float | None = None
    verify_only_path: str = ""
    run_path: str = ""
    context_json: dict = Field(default_factory=dict)
    outputs: dict[str, str] = Field(default_factory=dict)
    manager_decision: dict = Field(default_factory=dict)
    report_path: str = ""
    verified_report_path: str = ""


class Lab4Flow(Flow[Lab4State]):
    @start()
    def choose_entry(self) -> str:
        if self.state.verify_only_path:
            self.state.run_path = str(Path(self.state.verify_only_path).expanduser().resolve())
            return "verify_only"
        return "normal"

    @router(choose_entry)
    def route_entry(self) -> Literal["normal", "verify_only"]:
        return "verify_only" if self.state.verify_only_path else "normal"

    @listen("normal")
    def seven_data_steps(self) -> str:
        if not self.state.ticker.strip():
            raise ValueError("Provide a ticker for a normal run.")
        env = read_env(COURSE_ROOT / ".env")
        user_agent = env.get("SEC_USER_AGENT", "").strip()
        if not user_agent or "@" not in user_agent:
            raise RuntimeError("Set SEC_USER_AGENT in the private course .env file.")
        desk = load_desk()
        cik, company = desk.cik_for(self.state.ticker, user_agent)
        stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f_%Z")
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", company)
        folder = RUNS_ROOT / f"{safe_name}_{stamp}"
        folder.mkdir(parents=True, exist_ok=False)
        self.state.run_path = str(folder)
        ctx = RunContext(self.state.ticker, self.state.peers, self.state.price, user_agent, folder)
        ctx.cik, ctx.company = cik, company
        print("Starting node: Data Steps")
        for n in range(1, 8):
            print(f"  Running data tool: Step {n}")
            tool = DeskStepTool(name=f"SEC data step {n}", step_number=n, run_context=ctx)
            tool.run(request=f"Run step {n} in order")
        manifest = ctx.manifest()
        dump(folder / "desk_manifest.json", manifest)
        self.state.context_json = self._role_context(ctx, manifest)
        return str(folder)

    @listen(seven_data_steps)
    def research_analyst(self, _: str) -> str:
        print("Starting node: Research Analyst")
        ctx = self.state.context_json
        source = self._numbered_source(Path(self.state.run_path) / "10k.txt", ("Item 1", "Item 7"))
        release = self._numbered_source(Path(self.state.run_path) / "earnings_release_exhibit_99_1.txt", ())
        payload = self._payload("Describe the business model, competitive position, catalysts, and recent developments.",
                                {"company": ctx["company"], "ticker": ctx["ticker"], "10k_numbered_source": source, "release_numbered_source": release},
                                "JSON with markdown and claims. Cite each factual statement by source line.")
        self.state.outputs["research"] = self._call_role("research_analyst", "Research Analyst", payload)
        self._save_role_io("research_analyst", payload, self.state.outputs["research"])
        return self.state.outputs["research"]

    @listen(research_analyst)
    def financial_analyst(self, _: str) -> str:
        print("Starting node: Financial Analyst")
        c = self.state.context_json
        payload = self._payload("Report the annual facts and ratios, latest-quarter revenue and diluted EPS, and peer margins. Use the calculator values. Do not calculate in the model.",
                                {"ticker": c["ticker"], "company": c["company"], "facts": c["facts"], "calculations": c["calculations"], "calculation_arithmetic": c["calculation_arithmetic"], "release_numbered_source": c["release_lines"], "peers": c["peers"]},
                                "JSON with markdown and claims. Every number must have its filing/tag/period or release line.")
        self.state.outputs["financial"] = self._call_role("financial_analyst", "Financial Analyst", payload)
        self._save_role_io("financial_analyst", payload, self.state.outputs["financial"])
        return self.state.outputs["financial"]

    @listen(financial_analyst)
    def investment_advisor(self, _: str) -> str:
        print("Starting node: Investment Advisor")
        payload = self._payload("Give a thesis, Buy/Hold/Sell recommendation, and one deciding reported number.",
                                {"research_analyst_output": self.state.outputs["research"], "financial_analyst_output": self.state.outputs["financial"]},
                                "JSON with markdown and recommendation. Use only the two role outputs.")
        self.state.outputs["advisor"] = self._call_role("investment_advisor", "Investment Advisor", payload)
        self._save_role_io("investment_advisor", payload, self.state.outputs["advisor"])
        return self.state.outputs["advisor"]

    @listen(investment_advisor)
    def strategy_manager(self, _: str) -> str:
        print("Starting node: Strategy Manager")
        payload = self._payload("Check all five required sections and consistency. Identify any failing section and its originating role. Return valid JSON with failing_parts and report_markdown.",
                                {"role_outputs": self.state.outputs, "required_parts": PARTS},
                                "JSON with failing_parts array and report_markdown.")
        first = self._call_role("strategy_manager", "Strategy Manager", payload)
        parsed = self._json_object(first)
        failures = parsed.get("failing_parts", [])
        role_for_part = {PARTS[0]: "research", PARTS[1]: "research", PARTS[2]: "financial", PARTS[3]: "research", PARTS[4]: "advisor"}
        corrections: dict[str, str] = {}
        revised_roles: set[str] = set()
        grouped: dict[str, list[dict]] = {}
        for failure in failures if isinstance(failures, list) else []:
            if not isinstance(failure, dict):
                continue
            part = failure.get("part")
            role = failure.get("role") or role_for_part.get(part)
            if part not in PARTS or role not in self.state.outputs:
                continue
            grouped.setdefault(role, []).append(failure)
        for role, role_failures in grouped.items():
            revised_roles.add(role)
            part_names = [item["part"] for item in role_failures]
            role_name = {"research": "Research Analyst", "financial": "Financial Analyst", "advisor": "Investment Advisor"}[role]
            print(f"Starting node: {role_name} (revision for {', '.join(part_names)})")
            revision_payload = self._payload(f"Revise only these failing report parts: {part_names}. Feedback: {role_failures}",
                                             {"prior_role_output": self.state.outputs[role], "parts": role_failures,
                                              "source_context": self.state.context_json if role == "financial" else {"company": self.state.context_json["company"]}},
                                             "JSON with revised markdown for each assigned report part only.")
            corrected = self._call_role({"research":"research_analyst", "financial":"financial_analyst", "advisor":"investment_advisor"}[role], role_name, revision_payload)
            corrected_obj = self._json_object(corrected)
            for part in part_names:
                corrections[part] = corrected_obj.get(part) or corrected_obj.get("markdown") or corrected
            self._save_role_io(f"{role}_revision", revision_payload, corrected)
        if corrections:
            compile_payload = self._payload("Compile the revised role outputs into exactly five report sections. Preserve citations and arithmetic; add no facts.",
                                            {"role_outputs": self.state.outputs, "revisions": corrections, "required_parts": PARTS},
                                            "JSON with report_markdown and all five exact section headings.")
            second = self._call_role("strategy_manager", "Strategy Manager", compile_payload)
            parsed = self._json_object(second)
            self._save_role_io("strategy_manager_compile", compile_payload, second)
        report = parsed.get("report_markdown") or parsed.get("markdown") or ""
        if isinstance(report, dict):
            report = "\n\n".join(f"## {part}\n\n{report.get(part, '')}" for part in PARTS)
        if not isinstance(report, str):
            report = str(report)
        # Keep the Manager's review and compilation call, then normalize its
        # output to one instance of each required section. Use the assigned
        # role's revised section when the Manager repeats or merges headings.
        report = self._canonical_report(corrections)
        missing = [part for part in PARTS if part.casefold() not in report.casefold()]
        manifest = json.loads((Path(self.state.run_path) / "desk_manifest.json").read_text(encoding="utf-8"))
        filings_line = self._filings_line(manifest)
        report_text = f"{filings_line}\nRun time: {datetime.now().astimezone().isoformat(timespec='seconds')}\n\n{report.strip()}\n"
        report_text = self._append_source_linked_data(report_text, manifest, Path(self.state.run_path))
        report_path = Path(self.state.run_path) / f"{self.state.context_json['ticker']}_report.md"
        report_path.write_text(report_text, encoding="utf-8")
        self.state.report_path = str(report_path)
        self.state.manager_decision = {"failing_parts": failures, "revised_roles": sorted(revised_roles), "manager_calls": 2 if corrections else 1, "missing_after_compile": missing}
        dump(Path(self.state.run_path) / "node_io" / "strategy_manager_state.json", self.state.manager_decision)
        self._save_role_io("strategy_manager_review", payload, first)
        return str(report_path)

    @listen(strategy_manager)
    def verifier(self, _: str) -> str:
        print("Starting node: Verifier")
        return self._verify_saved(Path(self.state.run_path))

    @listen("verify_only")
    def verifier_only(self) -> str:
        print("Starting node: Verifier (verify-only)")
        return self._verify_saved(Path(self.state.run_path))

    def _verify_saved(self, folder: Path) -> str:
        folder = folder.expanduser().resolve()
        if not folder.is_dir():
            raise FileNotFoundError(f"Saved run folder does not exist: {folder}")
        verification_stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%f_%Z")
        report_paths = sorted(p for p in folder.glob("*_report.md") if not p.name.endswith("_verified_report.md"))
        report_path = Path(self.state.report_path) if self.state.report_path else (report_paths[-1] if report_paths else folder / "report.md")
        if not report_path.is_file():
            raise FileNotFoundError(f"No compiled report found in saved run: {folder}")
        report = report_path.read_text(encoding="utf-8")
        facts_paths = list(folder.glob("*_companyfacts.json"))
        saved_manifest = json.loads((folder / "desk_manifest.json").read_text(encoding="utf-8")) if (folder / "desk_manifest.json").exists() else {}
        facts_summary = saved_manifest.get("facts", {})
        facts_summary["peers"] = saved_manifest.get("peers", [])
        facts_summary["release_lines"] = saved_manifest.get("release_lines", [])
        facts_summary["calculations"] = saved_manifest.get("calculations", {})
        facts_summary["share_price_input"] = saved_manifest.get("share_price_input")
        facts_summary["raw_companyfacts_files"] = [p.name for p in facts_paths]
        texts = {p.name: p.read_text(encoding="utf-8", errors="replace") for p in folder.glob("*.txt")}
        if not texts or not facts_summary:
            raise RuntimeError("Verifier needs the saved filing texts and facts in the run folder.")
        audited_report, advisor_section = self._without_advisor_section(report)
        audited_report_lines = audited_report.splitlines()
        if audited_report_lines and audited_report_lines[0].startswith("Filings read:"):
            audited_report = "\n".join(audited_report_lines[2:]).strip()
        payload = self._payload(
            "Audit every numeric claim in the supplied report sections. Do not audit or reproduce the omitted Investment Advisor thesis. For every XBRL claim, compare its value, tag, accession, and period with saved_facts. For every filing-line citation, confirm the cited numbered line exists in saved_filing_texts and that it states the number for the stated period and definition. Recalculate every ratio from its quoted inputs. If the filing offers more than one definition, mark a ratio unsupported unless its definition is stated. Mark each claim correct, wrong, or unsupported. For each wrong or unsupported claim, give a corrected claim with the actual filing line or XBRL tag and period. Do not add claims or reproduce the source files.",
            {"compiled_report": audited_report, "saved_filing_texts": texts, "saved_facts": facts_summary},
            "Valid JSON with a marks array. Each mark must have claim, status, reason, correction, source, and corrected_claim. Use corrected_claim only when saved evidence supports the correction. Do not return or reproduce the filing texts.")
        raw = self._call_role("verifier", "Verifier", payload, verifier=True)
        result = self._json_object(raw)
        marks = result.get("marks", []) if isinstance(result.get("marks", []), list) else []
        marks = self._code_checks(marks, audited_report, texts, facts_summary)
        verification_io = folder / "node_io" / "verifications" / verification_stamp
        dump(verification_io / "verifier_input.json", payload)
        corrected = self._apply_verifier_corrections(report, marks)
        dump(verification_io / "verifier_output.json", {"model_output": raw, "marks": marks})
        table = ["| Claim | Mark | Reason / correction |", "|---|---|---|"]
        for mark in marks:
            claim = str(mark.get("claim", "" )).replace("|", "\\|")
            why = str(mark.get("reason", ""))
            correction = str(mark.get("correction", ""))
            detail = (why + (" Correction: " + correction if correction else "")).replace("|", "\\|").replace("\n", " ")
            table.append(f"| {claim} | {mark.get('status','unsupported')} | {detail} |")
        lines = corrected.splitlines()
        if lines and lines[0].startswith("Filings read:"):
            verified = lines[0] + "\n\n" + "\n".join(table) + "\n\n" + "\n".join(lines[1:]).lstrip()
        else:
            verified = "Filings read: unavailable\n\n" + "\n".join(table) + "\n\n" + corrected
        base = f"{self.state.ticker or self._ticker_from_run(folder, saved_manifest)}_verified_report"
        verified_path = folder / f"{base}_{verification_stamp}.md"
        verified_path.write_text(verified.rstrip() + "\n", encoding="utf-8")
        self.state.verified_report_path = str(verified_path)
        return str(verified_path)

    def _call_role(self, role_file: str, role_name: str, payload: dict, verifier: bool = False) -> str:
        instructions = (ROLE_DIR / f"{role_file}.md").read_text(encoding="utf-8")
        agent = Agent(role=role_name, goal=f"Complete the {role_name} node using only its supplied state.", backstory=instructions,
                      llm=_MODEL_LLM, allow_delegation=False, max_iter=1, max_execution_time=240, verbose=False)
        message = json.dumps(payload, ensure_ascii=False, default=str)
        result = agent.kickoff(message, response_format=VerifierResult) if verifier else agent.kickoff(message)
        if verifier:
            structured = getattr(result, "pydantic", None)
            if structured is None:
                raise RuntimeError("The Verifier did not return the required structured marks.")
            return json.dumps(structured.model_dump(), ensure_ascii=False)
        return result.raw if hasattr(result, "raw") else str(result)

    def _payload(self, task: str, context: dict, expected: str) -> dict:
        return {"task": task, "context": context, "expected_output": expected}

    @staticmethod
    def _append_source_linked_data(report: str, manifest: dict, folder: Path) -> str:
        facts = manifest.get("facts", {})
        values, tags, units = facts.get("values", {}), facts.get("tags", {}), facts.get("units", {})
        labels = {
            "revenue": "Revenue",
            "operating_income": "Operating Income",
            "net_income": "Net Income",
            "diluted_eps": "Diluted EPS",
            "equity": "Stockholders' Equity",
            "long_term_debt": "Long-Term Debt",
            "current_debt": "Current Portion of Long-Term Debt",
            "cash_from_operations": "Cash from Operations",
            "capex": "Additions to Property and Equipment",
        }
        rows = [
            "### Source-linked desk data",
            "",
            "The values below come from this run's saved SEC facts, calculator outputs, and selected release lines.",
            "",
            "| Metric | Value | Unit | Accession | XBRL tag | Period end |",
            "|---|---:|---|---|---|---|",
        ]
        for metric, label in labels.items():
            for period_name in ("current", "prior"):
                record = values.get(metric, {}).get(period_name)
                if not isinstance(record, dict):
                    continue
                value = float(record.get("val", 0))
                unit = units.get(metric, "")
                prefix = "$" if str(unit).upper().startswith("USD") else ""
                rendered = f"{prefix}{value:,.2f}" if not value.is_integer() else f"{prefix}{value:,.0f}"
                rows.append(f"| {label} ({period_name}) | {rendered} | {unit} | {record.get('accn', '')} | {tags.get(metric, '')} | {record.get('end', '')} |")

        calculations = manifest.get("calculations", {})
        current = {key: values.get(key, {}).get("current", {}).get("val") for key in values}
        prior = {key: values.get(key, {}).get("prior", {}).get("val") for key in values}
        equations = {
            "Revenue Growth": f"({current.get('revenue')} / {prior.get('revenue')}) - 1",
            "Operating Margin": f"{current.get('operating_income')} / {current.get('revenue')}",
            "Return on Average Equity": f"{current.get('net_income')} / (({current.get('equity')} + {prior.get('equity')}) / 2)",
            "Debt to Equity": f"({current.get('long_term_debt')} + {current.get('current_debt')}) / {current.get('equity')}",
            "Free Cash Flow": f"{current.get('cash_from_operations')} - {current.get('capex')}",
            "P/E": f"{manifest.get('share_price_input')} / {current.get('diluted_eps')}",
        }
        rows.extend(["", "| Calculator metric | Value | Arithmetic |", "|---|---:|---|"])
        for label, expression in equations.items():
            result = calculations.get({
                "Revenue Growth": "revenue_growth",
                "Operating Margin": "operating_margin",
                "Return on Average Equity": "return_on_average_equity",
                "Debt to Equity": "debt_to_equity",
                "Free Cash Flow": "free_cash_flow",
                "P/E": "pe",
            }[label])
            if result is None or "None" in expression:
                rendered, arithmetic_cell = "unavailable", "unavailable"
            elif label in {"Revenue Growth", "Operating Margin", "Return on Average Equity"}:
                rendered, arithmetic_cell = f"{float(result):.2%}", f"[arithmetic: {expression} = {float(result):.12g}]"
            elif label == "Free Cash Flow":
                rendered, arithmetic_cell = f"${float(result):,.0f}", f"[arithmetic: {expression} = {float(result):.12g}]"
            else:
                rendered, arithmetic_cell = f"{float(result):.2f}", f"[arithmetic: {expression} = {float(result):.12g}]"
            rows.append(f"| {label} | {rendered} | {arithmetic_cell} |")

        release_file = folder / "earnings_release_exhibit_99_1.txt"
        if not release_file.exists():
            release_file = folder / "earnings_release_exhibit_99.txt"
        release_numbered = release_file.read_text(encoding="utf-8", errors="replace").splitlines() if release_file.exists() else []
        selected_release = [str(x) for x in manifest.get("release_lines", [])]
        release_refs = []
        for selected in selected_release:
            clean = re.sub(r"^\d{5}:\s*", "", selected).strip()
            match = next(((i + 1, line) for i, line in enumerate(release_numbered) if re.sub(r"^\d{5}:\s*", "", line).strip().casefold() == clean.casefold()), None)
            if match:
                release_refs.append(match)
        if release_refs:
            rows.extend(["", "Quarterly release lines:"])
            for line_no, content in release_refs:
                unit_note = " (dollars in millions, except per-share data)" if "revenue" in content.casefold() and re.search(r"dollars in millions", "\n".join(release_numbered), re.I) else ""
                quoted_content = re.sub(r"^\d{5}:\s*", "", content)
                rows.append(f"- \"{quoted_content}\"{unit_note} [release line {line_no:05d}]")
            million_factor = 1_000_000 if re.search(r"dollars in millions|amounts in millions", "\n".join(release_numbered), re.I) else (1_000 if re.search(r"dollars in thousands|amounts in thousands", "\n".join(release_numbered), re.I) else 1)
            for line_no, content in release_refs:
                clean = re.sub(r"^\d{5}:\s*", "", content)
                numbers = re.findall(r"\$?\s*([\d,]+(?:\.\d+)?)", re.sub(r"^[A-Za-z\s]+", "", clean))
                if re.search(r"total\s+revenue|total\s+net\s+sales|net\s+sales", clean, re.I) and numbers:
                    value = float(numbers[0].replace(",", ""))
                    display = f"${value:,.0f} million" if million_factor == 1_000_000 else f"${value * million_factor:,.0f}"
                    rows.append(f"- Latest-quarter Total Revenue: {display} [release line {line_no:05d}]")
                elif re.search(r"diluted", clean, re.I) and numbers:
                    rows.append(f"- Latest-quarter Diluted EPS: ${float(numbers[0].replace(',', '')):,.2f} [release line {line_no:05d}]")

        peer_rows = []
        for peer in manifest.get("peers", []):
            bundle = peer.get("facts", {})
            for metric, label in labels.items():
                for period_name in ("current", "prior"):
                    record = bundle.get("values", {}).get(metric, {}).get(period_name)
                    if not isinstance(record, dict):
                        continue
                    value = float(record.get("val", 0))
                    unit = bundle.get("units", {}).get(metric, "")
                    prefix = "$" if str(unit).upper().startswith("USD") else ""
                    rendered = f"{value:,.2f}" if not value.is_integer() else f"{value:,.0f}"
                    peer_rows.append(f"| {peer.get('ticker')} {label} ({period_name}) | {prefix}{rendered} | {unit} | {record.get('accn', '')} | {bundle.get('tags', {}).get(metric, '')} | {record.get('end', '')} |")
            margin = peer.get("margin")
            if margin is not None:
                op = bundle.get("values", {}).get("operating_income", {}).get("current", {}).get("val")
                rev = bundle.get("values", {}).get("revenue", {}).get("current", {}).get("val")
                peer_rows.append(f"| {peer.get('ticker')} Operating Margin | {float(margin):.2%} | [arithmetic: {op} / {rev} = {float(margin):.12g}] |")
        if peer_rows:
            rows.extend(["", "Peer facts and margins:", "", "| Peer fact | Value | Unit | Accession | XBRL tag | Period end |", "|---|---:|---|---|---|---|"])
            rows.extend(row for row in peer_rows if "Operating Margin" not in row)
            rows.extend(["", "| Peer margin | Value | Arithmetic |", "|---|---:|---|"])
            rows.extend(row for row in peer_rows if "Operating Margin" in row)

        section = "\n".join(rows)
        marker = re.search(r"(?im)^#{1,6}\s*Future Developments and Strategic Recommendations\b", report)
        if marker:
            return report[:marker.start()].rstrip() + "\n\n" + section + "\n\n" + report[marker.start():]
        return report.rstrip() + "\n\n" + section + "\n"

    @staticmethod
    def _without_advisor_section(report: str) -> tuple[str, str]:
        match = re.search(r"(?im)^#{1,6}\s*Investment Recommendation\b.*$", report)
        if not match:
            return report, ""
        return report[:match.start()].rstrip(), report[match.start():].strip()

    @staticmethod
    def _ticker_from_run(folder: Path, manifest: dict) -> str:
        ticker = str(manifest.get("ticker", "")).strip().upper()
        if ticker:
            return ticker
        for path in folder.glob("*_report.md"):
            if not path.name.endswith("_verified_report.md"):
                return path.name.split("_", 1)[0].upper()
        return "verified"

    @staticmethod
    def _apply_verifier_corrections(report: str, marks: list[dict]) -> str:
        audited, advisor = Lab4Flow._without_advisor_section(report)
        lines = audited.splitlines()
        remove_lines: set[str] = set()
        for mark in marks:
            if not isinstance(mark, dict) or str(mark.get("status", "")).lower() not in {"wrong", "unsupported"}:
                continue
            remove_lines.update(str(x).strip().casefold() for x in mark.get("remove_lines", []) if str(x).strip())
            claim = str(mark.get("claim", "")).strip()
            # Only apply replacements that the deterministic code checks built
            # from saved facts or calculator inputs. Model-proposed text stays
            # in the audit table until its cited evidence passes code checks.
            replacement = str(mark.get("replacement_claim", "")).strip()
            if not claim:
                continue
            matched = next((i for i, line in enumerate(lines) if claim.casefold() == line.strip().casefold() or line.strip().casefold().startswith(claim.casefold())), None)
            if matched is None:
                continue
            if replacement:
                lines[matched] = replacement
            elif str(mark.get("status", "")).lower() == "unsupported":
                lines[matched] = ""
                prior_correction = str(mark.get("correction", "")).strip()
                mark["correction"] = (prior_correction + " Removed the claim from the verified body because saved evidence did not support it.").strip()
            else:
                # Keep an unsupported number out of the verified body when the
                # saved records do not provide a defensible replacement.
                lines[matched] = ""
                mark["correction"] = str(mark.get("correction", "")).strip() or "Removed the claim because a supported replacement could not be established."
        lines = [line for line in lines if line.strip().casefold() not in remove_lines]
        body = "\n".join(lines).strip()
        first_lines = report.splitlines()[:2]
        return "\n".join(first_lines + ["", body, "", advisor.strip()]).rstrip()

    def _save_role_io(self, name: str, payload: dict, output: str) -> None:
        dump(Path(self.state.run_path) / "node_io" / f"{name}_input.json", payload)
        dump(Path(self.state.run_path) / "node_io" / f"{name}_output.json", {"raw": output})

    def _role_context(self, ctx: RunContext, manifest: dict) -> dict:
        release_path = ctx.folder / ctx.filings.get("release_filename", "earnings_release_exhibit_99_1.txt")
        release = release_path.read_text(encoding="utf-8", errors="replace") if release_path.exists() else ""
        selected_release_lines = ctx.release_lines or ctx.desk.release_lines(ctx.release or release)
        numbered_release_lines = release.splitlines()
        release_lines = []
        for selected in selected_release_lines:
            normalized = re.sub(r"\s+", " ", selected).strip().casefold()
            match = next((line for line in numbered_release_lines if re.sub(r"^\d{5}:\s*", "", line).casefold() == normalized), None)
            if match:
                release_lines.append(match)
        facts_compact = {}
        for metric, value in ctx.facts.get("values", {}).items():
            facts_compact[metric] = value
        return {"ticker": ctx.ticker, "company": ctx.company, "facts": facts_compact,
                "tags": ctx.facts.get("tags", {}), "units": ctx.facts.get("units", {}),
                "fiscal_end": ctx.facts.get("fiscal_end"), "calculations": ctx.calculations,
                "calculation_arithmetic": ctx._calculation_lines(), "release_lines": release_lines,
                "peers": [{"ticker": x["ticker"], "company": x["company"], "facts": x["facts"]["values"], "tags": x["facts"]["tags"], "units": x["facts"]["units"], "fiscal_end": x["facts"]["fiscal_end"], "operating_margin": x["margin"], "filings": x["filings"]} for x in ctx.peer_results],
                "filings": manifest["filings"]}

    @staticmethod
    def _extract_release_numbers(text: str) -> list[str]:
        return [line for line in text.splitlines() if re.search(r"revenue|net sales|diluted|earnings per share", line, re.I) and re.search(r"\d", line)]

    @staticmethod
    def _numbered_source(path: Path, _sections: tuple[str, ...]) -> str:
        if not path.exists():
            return ""
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        # Prefer the 10-K's Business and MD&A sections. Keep exact line numbers.
        if path.name == "10k.txt":
            selected: list[str] = []
            section = ""
            for line in lines:
                clean = re.sub(r"^\d{5}:\s*", "", line)
                if re.match(r"Item\s+1\s*[—–-]\s*Business\b", clean, re.I):
                    section = "business"
                elif re.match(r"Item\s+1A\s*[—–-]", clean, re.I) and section == "business":
                    section = ""
                elif re.match(r"Item\s+7\s*[—–-]", clean, re.I):
                    section = "mda"
                elif re.match(r"Item\s+7A\s*[—–-]", clean, re.I) and section == "mda":
                    section = ""
                if section:
                    selected.append(line)
            if selected:
                lines = selected
        # Bound input size while retaining exact line numbers.
        if len(lines) > 1000:
            lines = lines[:700] + lines[-300:]
        return "\n".join(lines)

    @staticmethod
    def _json_object(raw: str) -> dict:
        try:
            obj = json.loads(raw)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass
        match = re.search(r"\{[\s\S]*\}", raw)
        if match:
            try:
                obj = json.loads(match.group(0))
                if isinstance(obj, dict):
                    return obj
            except Exception:
                pass
        return {"markdown": raw, "report_markdown": raw, "failing_parts": [], "marks": []}

    def _fallback_report(self, corrections: dict[str, str], existing: str = "") -> str:
        role_content = {"Overview": self._json_object(self.state.outputs.get("research", "")).get("markdown", self.state.outputs.get("research", "")),
                        "Market Positioning and Growth Outlook": self._json_object(self.state.outputs.get("research", "")).get("markdown", self.state.outputs.get("research", "")),
                        "Valuation Insights": self._json_object(self.state.outputs.get("financial", "")).get("markdown", self.state.outputs.get("financial", "")),
                        "Future Developments and Strategic Recommendations": self._json_object(self.state.outputs.get("research", "")).get("markdown", self.state.outputs.get("research", "")),
                        "Investment Recommendation": self._json_object(self.state.outputs.get("advisor", "")).get("markdown", self.state.outputs.get("advisor", ""))}
        out = []
        for part in PARTS:
            text = corrections.get(part) or role_content.get(part) or "No supported content was returned for this section."
            out.append(f"## {part}\n\n{text.strip()}")
        return existing + "\n\n" + "\n\n".join(out) if existing and not any(p.casefold() not in existing.casefold() for p in PARTS) else "\n\n".join(out)

    def _canonical_report(self, corrections: dict[str, str]) -> str:
        """Render one clean section per role after the Manager's review."""
        research = self._json_object(corrections.get("Overview", "") or self.state.outputs.get("research", "")).get("markdown", "")
        if not research:
            research = self._json_object(self.state.outputs.get("research", "")).get("markdown", "")
        financial = self._json_object(corrections.get("Valuation Insights", "") or self.state.outputs.get("financial", "")).get("markdown", "")
        advisor = self._json_object(corrections.get("Investment Recommendation", "") or self.state.outputs.get("advisor", "")).get("markdown", "")

        def section(markdown: str, title: str) -> str:
            lines = markdown.splitlines()
            starts = [i for i, line in enumerate(lines) if re.match(r"^#{1,6}\s+" + re.escape(title) + r"\s*$", line, re.I)]
            if starts:
                start = starts[0] + 1
                end = next((i for i in range(start, len(lines)) if re.match(r"^#{1,6}\s+", lines[i])), len(lines))
                return "\n".join(lines[start:end]).strip()
            return markdown.strip()

        research_fallback = self._json_object(self.state.outputs.get("research", "")).get("markdown", "")
        overview = section(research, "Overview") or section(research_fallback, "Business Model")
        positioning = section(research, "Market Positioning and Growth Outlook") or section(research_fallback, "Competitive Position")
        future = section(research, "Future Developments and Strategic Recommendations") or section(research_fallback, "Catalysts")
        parts = {
            "Overview": overview,
            "Market Positioning and Growth Outlook": positioning,
            "Valuation Insights": "The annual SEC facts, prior-year comparisons, code-calculated ratios, latest-quarter figures, and peer margins appear below with their source and arithmetic.",
            "Future Developments and Strategic Recommendations": future,
            "Investment Recommendation": advisor or "The Advisor did not return a recommendation.",
        }
        parts["Investment Recommendation"] = re.sub(
            r"(?m)^##\s+", "### ", parts["Investment Recommendation"]
        )
        return "\n\n".join(f"## {title}\n\n{parts[title]}" for title in PARTS)

    @staticmethod
    def _filings_line(manifest: dict) -> str:
        items = []
        for key in ("10k", "10q", "earnings_8k"):
            row = manifest.get("filings", {}).get(key, {})
            if row:
                items.append(f"{row.get('form')} {row.get('accessionNumber')} accepted {row.get('accepted', 'not recorded')}")
        return "Filings read: " + "; ".join(items)

    @staticmethod
    def _cited_lines(report: str, texts: dict[str, str]) -> dict[str, list[str]]:
        cited: dict[str, list[str]] = {}
        pattern = re.compile(r"\[(10-K|10-Q|8-K|release) line (\d{5})\]", re.I)
        mapping = {"10-K": "10k.txt", "10-Q": "10q.txt", "8-K": "earnings_8k.txt", "release": "earnings_release_exhibit_99_1.txt"}
        for form, line_no in pattern.findall(report):
            name = mapping.get(form.upper() if form.lower() != "release" else "release", mapping.get(form, ""))
            source = texts.get(name, "").splitlines()
            number = int(line_no)
            for idx in range(max(0, number - 2), min(len(source), number + 2)):
                cited.setdefault(name, []).append(source[idx])
        return {k: list(dict.fromkeys(v)) for k, v in cited.items()}

    @staticmethod
    def _code_checks(marks: list[dict], report: str, texts: dict[str, str], facts: dict) -> list[dict]:
        advisor_match = re.search(r"(?im)^#{1,6}\s*Investment Recommendation\b", report)
        advisor_start = advisor_match.start() if advisor_match else -1
        auditable = report if advisor_start < 0 else report[:advisor_start]
        citation_re = re.compile(r"\[(10-K|10-Q|8-K|release) line (\d{5})\]", re.I)
        checked = []
        checked_claims: set[str] = set()
        filing_for_form = {
            "10-k": "10k.txt",
            "10-q": "10q.txt",
            "8-k": "earnings_8k.txt",
            "release": "earnings_release_exhibit_99_1.txt",
        }

        def cells(row: str) -> list[str]:
            return [x.strip() for x in row.strip().strip("|").split("|")]

        def numeric(value: str) -> float | None:
            match = re.search(r"-?\$?([\d,]+(?:\.\d+)?)", value)
            if not match:
                return None
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                return None

        def arithmetic(expression: str) -> float:
            if not re.fullmatch(r"[0-9.,()*/+\-\s]+", expression):
                raise ValueError("unsupported arithmetic")
            return float(eval(expression.replace(",", ""), {"__builtins__": {}}, {}))

        # Normalize financial facts that the role may have split across several
        # markdown lines. Facts must end with an exact, single-line XBRL source.
        label_metrics = {
            "revenue": ("revenue",),
            "operating income": ("operating_income",),
            "net income": ("net_income",),
            "diluted eps": ("diluted_eps",),
            "equity": ("equity",),
            "stockholders' equity": ("equity",),
            "stockholders equity": ("equity",),
            "long-term debt": ("long_term_debt",),
            "long term debt": ("long_term_debt",),
            "current debt": ("current_debt",),
            "current portion of long-term debt": ("current_debt",),
            "cash from operations": ("cash_from_operations",),
            "capital expenditures": ("capex",),
            "additions to property and equipment": ("capex",),
        }
        fact_row = re.compile(r"^(\s*[-*]\s+(?:\*\*([^*]+)\*\*|([^:]+)):\s*)(.*)$")
        heading_title = ""
        peer_section = False
        active_peer = ""
        annual_section = False
        for index, line in enumerate(auditable.splitlines()):
            heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
            if heading:
                level, heading_title = len(heading.group(1)), heading.group(2)
                if "annual facts" in heading_title.casefold():
                    peer_section, active_peer, annual_section = False, "", True
                elif "peer margins" in heading_title.casefold():
                    peer_section, active_peer, annual_section = True, "", False
                elif peer_section and level >= 4:
                    match_peer = re.search(r"\(([A-Z][A-Z0-9.-]{0,9})\)", heading_title)
                    active_peer = match_peer.group(1) if match_peer else ""
                elif level <= 3:
                    peer_section, active_peer, annual_section = False, "", False
                continue
            matched_row = fact_row.match(line)
            if not matched_row:
                continue
            label = re.sub(r"\s*\([^)]*\)", "", (matched_row.group(2) or matched_row.group(3))).strip().casefold()
            metric_group = label_metrics.get(label)
            if not metric_group:
                continue
            if peer_section and active_peer:
                peer = next((p for p in facts.get("peers", []) if str(p.get("ticker", "")).upper() == active_peer), None)
                bundle = peer.get("facts", {}) if peer else {}
            elif annual_section:
                bundle = facts
            else:
                continue
            metric = metric_group[0]
            record = bundle.get("values", {}).get(metric, {}).get("current", {})
            expected_tag = bundle.get("tags", {}).get(metric, "")
            if not isinstance(record, dict) or not expected_tag:
                continue
            reported_value = numeric(matched_row.group(4).split("[", 1)[0])
            expected_value = record.get("val")
            expected_accession, expected_period = str(record.get("accn", "")), str(record.get("end", ""))
            block = "\n".join(auditable.splitlines()[index:index + 6])
            inline_source = re.search(r"\[filing accession:\s*(\d{10}-\d{2}-\d{6}),\s*tag:\s*([A-Za-z0-9]+),\s*period-end:\s*(\d{4}-\d{2}-\d{2})\]", block, re.I)
            separate_accession = re.search(r"(?:Filing Accession|filing accession):\s*(\d{10}-\d{2}-\d{6})", block, re.I)
            separate_tag = re.search(r"(?:Tag|tag):\s*`?([A-Za-z][A-Za-z0-9]+)", block, re.I)
            separate_period = re.search(r"(?:Period End|period-end):\s*(\d{4}-\d{2}-\d{2})", block, re.I)
            actual_accession = inline_source.group(1) if inline_source else (separate_accession.group(1) if separate_accession else "")
            actual_tag = inline_source.group(2) if inline_source else (separate_tag.group(1) if separate_tag else "")
            actual_period = inline_source.group(3) if inline_source else (separate_period.group(1) if separate_period else "")
            value_ok = reported_value is not None and abs(reported_value - float(expected_value)) <= max(1e-8, abs(float(expected_value)) * 1e-10)
            source_ok = bool(inline_source and actual_accession == expected_accession and actual_tag == expected_tag and actual_period == expected_period)
            valid = value_ok and source_ok
            original_prefix = matched_row.group(1)
            has_dollar = "$" in matched_row.group(4).split("[", 1)[0]
            expected_number = float(expected_value)
            number_text = f"{expected_number:,.2f}" if not expected_number.is_integer() else f"{expected_number:,.0f}"
            replacement = f"{original_prefix}{'$' if has_dollar else ''}{number_text} [filing accession: {expected_accession}, tag: {expected_tag}, period-end: {expected_period}]"
            removed_metadata = []
            if not peer_section:
                removed_metadata = [x for x in auditable.splitlines()[index + 1:index + 6] if re.search(r"Filing Accession:|^\s*-\s*(?:Tag|Period End):", x, re.I)]
            checked.append({
                "claim": line.strip(),
                "status": "correct" if valid else "wrong",
                "reason": "The reported value, XBRL tag, accession, and period end match the saved facts." if valid else "The fact value or its XBRL source does not match the saved facts.",
                "correction": "" if valid else f"Use {expected_value} with tag {expected_tag}, accession {expected_accession}, period end {expected_period}.",
                "source": f"{expected_tag}; {expected_period}; {expected_accession}",
                "replacement_claim": "" if valid else replacement,
                "remove_lines": removed_metadata,
            })
            checked_claims.add(line.strip().casefold())

        # Check the two release claims against the exact lines selected by step 6.
        release_name = "earnings_release_exhibit_99_1.txt" if "earnings_release_exhibit_99_1.txt" in texts else "earnings_release_exhibit_99.txt"
        release_text = texts.get(release_name, "")
        release_lines = release_text.splitlines()
        release_unit_factor = 1_000_000 if re.search(r"dollars in millions|amounts in millions", release_text, re.I) else (1_000 if re.search(r"dollars in thousands|amounts in thousands", release_text, re.I) else 1)
        selected_release = [str(x) for x in facts.get("release_lines", [])]
        for line in auditable.splitlines():
            row = re.match(r"^\s*[-*]\s+(?:\*\*([^*]+)\*\*|([^:]+)):\s*(.*)$", line)
            if not row:
                continue
            label = (row.group(1) or row.group(2)).casefold().replace("-", " ")
            is_revenue = "latest quarter" in label and "revenue" in label and "growth" not in label
            is_eps = "diluted eps" in label and ("quarter" in label or "latest" in label)
            if not (is_revenue or is_eps):
                continue
            expected_pattern = r"total\s+revenue|total\s+net\s+sales|net\s+sales" if is_revenue else r"diluted"
            selected = next((x for x in selected_release if re.search(expected_pattern, x, re.I)), None)
            if selected is None:
                selected = next((re.sub(r"^\d{5}:\s*", "", x) for x in release_lines if re.search(expected_pattern, re.sub(r"^\d{5}:\s*", "", x), re.I)), None)
            expected_number = numeric(selected or "")
            # For table rows, skip the line number and text label before reading values.
            if selected:
                expected_body = re.sub(r"^\d{5}:\s*", "", selected).strip()
                numbers = re.findall(r"\$?\s*([\d,]+(?:\.\d+)?)", re.sub(r"^[A-Za-z\s]+", "", expected_body))
                expected_number = float(numbers[0].replace(",", "")) if numbers else expected_number
            cite = citation_re.search(line)
            cited_line = int(cite.group(2)) if cite and cite.group(1).casefold() == "release" else 0
            actual_source = release_lines[cited_line - 1] if 0 < cited_line <= len(release_lines) else ""
            selected_line_no = 0
            if selected:
                selected_clean = re.sub(r"^\d{5}:\s*", "", selected).strip().casefold()
                selected_line_no = next((i + 1 for i, x in enumerate(release_lines) if re.sub(r"^\d{5}:\s*", "", x).strip().casefold() == selected_clean), 0)
            reported = numeric(row.group(3).split("[", 1)[0])
            if expected_number is not None and is_revenue:
                expected_absolute = expected_number * release_unit_factor
                amount_ok = reported is not None and (abs(reported - expected_absolute) <= 0.01 or abs(reported - expected_number) <= 0.01)
                display_value = f"${expected_number:,.0f} million" if release_unit_factor == 1_000_000 else f"${expected_absolute:,.0f}"
            else:
                expected_absolute = expected_number
                amount_ok = reported is not None and expected_absolute is not None and abs(reported - expected_absolute) <= 0.01
                display_value = f"${expected_absolute:,.2f}" if expected_absolute is not None else ""
            cite_ok = bool(selected_line_no and cited_line == selected_line_no and actual_source)
            valid = amount_ok and cite_ok
            claim = line.strip()
            replacement = re.sub(r"\s*\[release line \d{5}\]", "", line).rstrip()
            value_span = row.group(3).split("[", 1)[0].strip()
            replacement = replacement[:replacement.find(value_span)] + display_value + (f" [release line {selected_line_no:05d}]" if selected_line_no else "")
            checked.append({
                "claim": claim,
                "status": "correct" if valid else "wrong",
                "reason": "The amount and citation match the step 6 release line and its stated unit." if valid else "The quarterly amount, definition, or line citation does not match the step 6 release line.",
                "correction": "" if valid else f"Use {display_value} from release line {selected_line_no:05d}.",
                "source": f"release line {selected_line_no:05d}",
                "replacement_claim": "" if valid else replacement,
            })
            checked_claims.add(claim.casefold())

        # Verify every numbered citation against the exact saved filing line.
        # The model then judges whether that line supports the stated claim.
        for line in auditable.splitlines():
            citations = citation_re.findall(line)
            if not citations or not re.search(r"\d", line):
                continue
            for form, line_no in citations:
                filename = filing_for_form[form.lower()]
                source_text = texts.get(filename, "")
                if form.lower() == "release" and not source_text:
                    source_text = texts.get("earnings_release_exhibit_99.txt", "")
                source_lines = source_text.splitlines()
                index = int(line_no) - 1
                saved_line = source_lines[index] if 0 <= index < len(source_lines) else ""
                expected_prefix = f"{int(line_no):05d}:"
                line_present = saved_line.startswith(expected_prefix) and bool(saved_line[len(expected_prefix):].strip())
                quoted_text = re.findall(r"[\"“]([^\"”]{8,})[\"”]", line)
                quote_present = not quoted_text or any(
                    re.sub(r"\s+", " ", quote).strip().casefold()
                    in re.sub(r"\s+", " ", saved_line).strip().casefold()
                    for quote in quoted_text
                )
                if not line_present or not quote_present:
                    checked.append({
                        "claim": line.strip(),
                        "status": "unsupported",
                        "reason": f"The cited {form} line {line_no} does not match the saved filing text.",
                        "correction": saved_line or "Use a valid numbered line from the saved filing.",
                        "source": f"{form} line {line_no}",
                    })
                    checked_claims.add(line.strip().casefold())
                elif form.casefold() == "release" and quoted_text:
                    selected = [re.sub(r"^\d{5}:\s*", "", str(x)).strip() for x in facts.get("release_lines", [])]
                    exact_selected_quote = any(re.sub(r"\s+", " ", quote).strip().casefold() == re.sub(r"\s+", " ", item).strip().casefold() for quote in quoted_text for item in selected)
                    if exact_selected_quote:
                        checked.append({"claim": line.strip(), "status": "correct", "reason": "The quoted text exactly matches a release line selected by step 6.", "correction": "", "source": f"release line {line_no}"})
                        checked_claims.add(line.strip().casefold())

        # Check a direct annual diluted-EPS claim against its cited 10-K line.
        # This catches a changed per-share value even when the model omits the
        # claim or returns an unsupported mark for the surrounding paragraph.
        for line in auditable.splitlines():
            cite = citation_re.search(line)
            if not cite or cite.group(1).casefold() != "10-k" or "diluted eps" not in line.casefold():
                continue
            line_no = int(cite.group(2))
            source_lines = texts.get("10k.txt", "").splitlines()
            saved_line = source_lines[line_no - 1] if 0 < line_no <= len(source_lines) else ""
            source_eps = re.search(r"(?i)^\d{5}:\s*Diluted\s+\$\s*([\d,]+(?:\.\d+)?)", saved_line)
            claim_eps = re.search(r"(?i)diluted eps(?:\s*\([^)]*\))?(?:\s+(?:was|is|of))?\s*[:|]?\s*\$?\s*([\d,]+(?:\.\d+)?)", line)
            if not source_eps or not claim_eps or not saved_line.startswith(f"{line_no:05d}:"):
                continue
            expected_eps = float(source_eps.group(1).replace(",", ""))
            reported_eps = float(claim_eps.group(1).replace(",", ""))
            if abs(expected_eps - reported_eps) <= 1e-8:
                status = "correct"
                reason = f"Diluted EPS matches the 10-K per-share line {line_no:05d}."
                correction = ""
                replacement_claim = ""
            else:
                status = "wrong"
                reason = f"The cited 10-K per-share line reports ${expected_eps:.2f}, not ${reported_eps:.2f}."
                accession = str(facts.get("values", {}).get("diluted_eps", {}).get("current", {}).get("accn", ""))
                correction = f"Use ${expected_eps:.2f} diluted EPS [10-K line {line_no:05d}; accession {accession}]."
                replacement_claim = line[:claim_eps.start(1)] + f"{expected_eps:.2f}" + line[claim_eps.end(1):]
            claim = line.strip()
            checked.append({"claim": claim, "status": status, "reason": reason, "correction": correction,
                            "source": f"10-K line {line_no:05d}; {saved_line}; {facts.get('values', {}).get('diluted_eps', {}).get('current', {}).get('accn', '')}",
                            "replacement_claim": replacement_claim})
            checked_claims.add(claim.casefold())

        # Recalculate a revenue-growth sentence when it quotes both annual
        # revenue inputs and cites the 10-K. Keep the arithmetic with the mark.
        for line in auditable.splitlines():
            cite = citation_re.search(line)
            if not cite or cite.group(1).casefold() != "10-k" or "revenue growth" not in line.casefold():
                continue
            claim = line.strip()
            if claim.casefold() in checked_claims:
                continue
            reported_match = re.search(r"(?i)revenue growth\s*(?:was|of|=|:)?\s*([\d,]+(?:\.\d+)?)\s*%", line)
            quoted_inputs = re.findall(r"\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion)?", line[:cite.start()], re.I)
            if not reported_match or len(quoted_inputs) < 2:
                continue
            def to_usd(amount: str, unit: str) -> float:
                scale = 1_000_000_000 if unit.casefold() == "billion" else (1_000_000 if unit.casefold() == "million" else 1)
                return float(amount.replace(",", "")) * scale
            current_revenue = to_usd(*quoted_inputs[0])
            prior_revenue = to_usd(*quoted_inputs[1])
            expected_growth = (current_revenue / prior_revenue - 1) * 100 if prior_revenue else 0.0
            reported_growth = float(reported_match.group(1).replace(",", ""))
            correct_growth = abs(expected_growth - reported_growth) <= 0.0051
            line_no = int(cite.group(2))
            accession = str(facts.get("values", {}).get("revenue", {}).get("current", {}).get("accn", ""))
            arithmetic_text = f"({quoted_inputs[0][0]} / {quoted_inputs[1][0]}) - 1 = {expected_growth:.2f}%"
            replacement_claim = line
            if not correct_growth:
                replacement_claim = line[:reported_match.start(1)] + f"{expected_growth:.2f}" + line[reported_match.end(1):]
            checked.append({
                "claim": claim,
                "status": "correct" if correct_growth else "wrong",
                "reason": "The revenue-growth percentage matches the two quoted annual revenue figures." if correct_growth else "The percentage does not match the two quoted annual revenue figures.",
                "correction": "" if correct_growth else f"Arithmetic: {arithmetic_text}; use {expected_growth:.2f}% [10-K line {line_no:05d}; accession {accession}].",
                "source": f"10-K line {line_no:05d}; {accession}",
                "replacement_claim": "" if correct_growth else replacement_claim,
            })
            checked_claims.add(claim.casefold())

        # Recalculate a quarter revenue-growth row from the exact release line.
        for line in auditable.splitlines():
            if not re.search(r"(?i)(?:q[1-4]|quarter).*revenue growth|revenue growth.*(?:q[1-4]|quarter)", line):
                continue
            claim = line.strip()
            if claim.casefold() in checked_claims:
                continue
            if line.strip().startswith("|"):
                row = cells(line)
                reported_text = row[1] if len(row) > 1 else ""
            else:
                bullet = re.match(r"^\s*[-*]\s+(?:\*\*([^*]+)\*\*|([^:]+)):\s*(.*)$", line)
                if not bullet:
                    continue
                reported_text = bullet.group(3)
                row = [bullet.group(1) or bullet.group(2), reported_text]
            selected_release = next((str(x) for x in facts.get("release_lines", []) if re.search(r"(?i)^total\s+revenue\b", str(x))), "")
            amounts = re.findall(r"[\d,]+(?:\.\d+)?", selected_release)
            if not selected_release or len(amounts) < 2:
                continue
            current_q, prior_q = (float(x.replace(",", "")) for x in amounts[:2])
            expected_growth = (current_q / prior_q - 1) * 100 if prior_q else 0.0
            shown_match = re.search(r"(-?[\d,.]+)\s*%", reported_text)
            formula_match = re.search(r"\[arithmetic:\s*(.*?)\s*=\s*(-?[\d,.]+)\s*\]", line, re.I)
            shown_growth = float(shown_match.group(1).replace(",", "")) if shown_match else None
            formula_result = float(formula_match.group(2).replace(",", "")) if formula_match else None
            formula_expression = formula_match.group(1) if formula_match else ""
            formula_value = None
            if formula_expression and re.fullmatch(r"[0-9.,()*/+\-\s]+", formula_expression):
                try:
                    formula_value = float(eval(formula_expression.replace(",", ""), {"__builtins__": {}}, {}))
                except (ValueError, TypeError, SyntaxError, ZeroDivisionError):
                    formula_value = None
            cited = re.search(r"\[release line (\d{5})\]", line, re.I)
            release_source_line = next((str(x) for x in facts.get("release_lines", []) if re.sub(r"^\d{5}:\s*", "", str(x)).strip().casefold() == selected_release.strip().casefold()), "")
            cited_source_line = int(cited.group(1)) if cited else 0
            expected_source_line = next((idx + 1 for idx, text in enumerate(release_lines) if re.sub(r"^\d{5}:\s*", "", text).strip().casefold() == selected_release.strip().casefold()), 0)
            valid = (shown_growth is not None and abs(shown_growth - expected_growth) <= 0.0051
                     and formula_result is not None and abs(formula_result - expected_growth / 100) <= 1e-6
                     and formula_value is not None and abs(formula_value - expected_growth / 100) <= 1e-6
                     and cited_source_line == expected_source_line and bool(release_source_line))
            correction = "" if valid else f"Arithmetic: ({int(current_q):,} / {int(prior_q):,}) - 1 = {expected_growth:.2f}%; use {expected_growth:.2f}% [release line {expected_source_line:05d}]."
            replacement_claim = line
            if not valid and shown_match:
                value_offset = line.find(reported_text)
                if value_offset >= 0:
                    start, end = value_offset + shown_match.start(1), value_offset + shown_match.end(1)
                    replacement_claim = line[:start] + f"{expected_growth:.2f}" + line[end:]
            checked.append({"claim": claim, "status": "correct" if valid else "wrong",
                            "reason": "Quarter revenue growth matches the two amounts on the selected release line." if valid else "Quarter revenue growth does not match the two amounts on the selected release line.",
                            "correction": correction, "source": f"release line {expected_source_line:05d}",
                            "replacement_claim": "" if valid else replacement_claim})
            checked_claims.add(claim.casefold())

        # Check annual XBRL claims in the role's inline citations.
        inline_fact = re.compile(r"\[filing accession:\s*(\d{10}-\d{2}-\d{6}),\s*tag:\s*([A-Za-z0-9]+),\s*period-end:\s*(\d{4}-\d{2}-\d{2})\]", re.I)
        for line in auditable.splitlines():
            if line.strip().casefold() in checked_claims:
                continue
            if any(
                str(mark.get("status", "")).lower() == "unsupported"
                and str(mark.get("claim", "")).strip()
                and (line.strip().casefold().startswith(str(mark.get("claim", "")).strip().casefold())
                     or str(mark.get("claim", "")).strip().casefold().startswith(line.strip().casefold()))
                for mark in checked if isinstance(mark, dict)
            ):
                continue
            match = inline_fact.search(line)
            if not match:
                continue
            if re.search(r"operating margin|p/e|price.?to.?earnings|ratio", line, re.I):
                continue
            accession, tag, period = match.groups()
            metric = next((m for m, t in facts.get("tags", {}).items() if t == tag), None)
            # Parse after the fact label, not a fiscal year in the label.
            value = numeric(line[:match.start()].rsplit(":", 1)[-1])
            records = facts.get("values", {}).get(metric, {}) if metric else {}
            record = next((r for r in (records.get("current"), records.get("prior")) if isinstance(r, dict) and r.get("accn") == accession and r.get("end") == period), None)
            valid = record is not None and value is not None and abs(value - float(record.get("val", 0))) < 1e-8
            if not valid and value is not None:
                correct_metric = next((m for m, group in facts.get("values", {}).items()
                                       if any(isinstance(r, dict) and r.get("accn") == accession and r.get("end") == period and abs(value - float(r.get("val", 0))) < 1e-8
                                              for r in (group.get("current"), group.get("prior")))), None)
                correct_tag = facts.get("tags", {}).get(correct_metric) if correct_metric else None
            else:
                correct_metric, correct_tag = metric, tag
            correction = "" if valid else (f"Use {record.get('val')} from {tag}, {record.get('end')}, accession {record.get('accn')}." if record else (f"The value matches {correct_tag} ({period}, accession {accession}); use that tag." if correct_tag else "Use a matching saved XBRL fact."))
            replacement_claim = line.strip()
            if not valid and correct_tag:
                replacement_claim = re.sub(r"(?i)(tag:\s*)" + re.escape(tag) + r"(?=\s*[,\]])", rf"\g<1>{correct_tag}", replacement_claim, count=1)
            checked.append({"claim": line.strip(), "status": "correct" if valid else "wrong", "reason": "XBRL tag, accession, period end, and value match the saved facts." if valid else "XBRL citation does not match the saved tag, accession, period end, and value.", "correction": correction, "source": f"{tag}; {period}; {accession}", "replacement_claim": replacement_claim if not valid and correct_tag else ""})
            checked_claims.add(line.strip().casefold())

        # Recompute each quoted ratio from its formula in code.
        inline_arithmetic = re.compile(r"\[(?:arithmetic:\s*(.*?)\s*=\s*(-?[\d,.]+)|calculated from\s*(.*?))\s*\]", re.I)
        peer_section = False
        active_peer = ""
        for line in auditable.splitlines():
            if line.strip().casefold() in checked_claims:
                continue
            heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
            if heading:
                level, title = len(heading.group(1)), heading.group(2)
                if "peer margins" in title.casefold():
                    peer_section, active_peer = True, ""
                elif peer_section and level >= 4:
                    peer_match = re.search(r"\(([A-Z][A-Z0-9.-]{0,9})\)", title)
                    active_peer = peer_match.group(1) if peer_match else ""
                elif level <= 3:
                    peer_section, active_peer = False, ""
                continue
            match = inline_arithmetic.search(line)
            if not match:
                continue
            expression = match.group(1) or match.group(3) or ""
            claimed_result = match.group(2)
            try:
                computed = arithmetic(expression)
                reported_formula = float(claimed_result.replace(",", "")) if claimed_result else computed
                label_value = numeric(line[:match.start()])
                if label_value is None:
                    raise ValueError("reported ratio missing")
                displayed = label_value / 100 if "%" in line[:match.start()] else label_value
                label = line.casefold()
                expected_expression = ""
                line_peer = next((p for p in facts.get("peers", []) if p.get("ticker") and str(p.get("ticker")).upper() in line.upper()), None)
                target_peer = line_peer or (next((p for p in facts.get("peers", []) if str(p.get("ticker", "")).upper() == active_peer), None) if peer_section and active_peer else None)
                if target_peer and "operating margin" in label:
                    peer = target_peer
                    bundle = peer.get("facts", {}) if peer else {}
                    op = bundle.get("values", {}).get("operating_income", {}).get("current", {}).get("val")
                    rev = bundle.get("values", {}).get("revenue", {}).get("current", {}).get("val")
                    if op is not None and rev:
                        expected_expression = f"{op} / {rev}"
                else:
                    vals = facts.get("values", {})
                    getval = lambda metric, period="current": vals.get(metric, {}).get(period, {}).get("val")
                    rev, prior_rev = getval("revenue"), getval("revenue", "prior")
                    op, net = getval("operating_income"), getval("net_income")
                    eq, prior_eq = getval("equity"), getval("equity", "prior")
                    ltd, cur = getval("long_term_debt"), getval("current_debt")
                    cfo, capex, eps = getval("cash_from_operations"), getval("capex"), getval("diluted_eps")
                    price = facts.get("share_price_input")
                    if "revenue growth" in label and rev is not None and prior_rev:
                        expected_expression = f"({rev} / {prior_rev}) - 1"
                    elif "operating margin" in label and op is not None and rev:
                        expected_expression = f"{op} / {rev}"
                    elif "return on average equity" in label and net is not None and eq is not None and prior_eq is not None:
                        expected_expression = f"{net} / (({eq} + {prior_eq}) / 2)"
                    elif "debt to equity" in label and ltd is not None and cur is not None and eq:
                        expected_expression = f"({ltd} + {cur}) / {eq}"
                    elif "free cash flow" in label and cfo is not None and capex is not None:
                        expected_expression = f"{cfo} - {capex}"
                    elif "p/e" in label and price is not None and eps:
                        expected_expression = f"{price} / {eps}"
                target_expression = expected_expression or expression
                target_computed = arithmetic(target_expression)
                expr_numbers = [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", expression)]
                target_numbers = [float(x.replace(",", "")) for x in re.findall(r"\d[\d,]*(?:\.\d+)?", target_expression)]
                formula_ok = abs(computed - reported_formula) <= max(1e-8, abs(computed) * 1e-6)
                inputs_ok = not expected_expression or expr_numbers == target_numbers
                # The displayed number can be rounded to two decimal places.
                if "%" in line[:match.start()]:
                    display_ok = abs(displayed - target_computed) <= 0.000051
                else:
                    display_ok = abs(displayed - target_computed) <= max(0.01, abs(target_computed) * 1e-4)
                close = formula_ok and inputs_ok and display_ok
                replacement_claim = line.strip()
                if not close:
                    prefix = line[:match.start()]
                    shown_match = re.search(r"(-?\$?[\d,]+(?:\.\d+)?)(%)?\s*$", prefix)
                    if shown_match:
                        shown_value = target_computed * 100 if shown_match.group(2) else target_computed
                        if shown_match.group(2):
                            shown_text = f"{shown_value:,.2f}%"
                        else:
                            shown_text = f"{shown_value:,.0f}" if float(shown_value).is_integer() else f"{shown_value:.2f}"
                        prefix = prefix[:shown_match.start()] + shown_text
                        replacement_claim = prefix + line[match.start():]
                        replacement_claim = inline_arithmetic.sub(f"[arithmetic: {target_expression} = {target_computed:.12g}]", replacement_claim, count=1)
                elif match.group(3):
                    replacement_claim = inline_arithmetic.sub(f"[arithmetic: {target_expression} = {target_computed:.12g}]", replacement_claim, count=1)
                checked.append({"claim": line.strip(), "status": "correct" if close else "wrong", "reason": "The displayed ratio and its inputs match the saved facts and code calculation." if close else "The ratio, its quoted inputs, or both do not match the saved facts and code calculation.", "correction": "" if close else str(target_computed), "source": target_expression, "replacement_claim": replacement_claim if not close else ""})
                checked_claims.add(line.strip().casefold())
            except (ValueError, ZeroDivisionError, SyntaxError):
                checked.append({"claim": line.strip(), "status": "unsupported", "reason": "The ratio formula or its inputs could not be checked in code.", "correction": "", "source": ""})
                checked_claims.add(line.strip().casefold())

        # Deterministically check tagged XBRL rows, ratio arithmetic, release lines,
        # and peer margins before accepting the model's semantic judgments.
        for line in auditable.splitlines():
            if not line.strip().startswith("|"):
                continue
            row = cells(line)
            if len(row) < 3 or set(row[0]) <= {"-", ":"}:
                continue
            claim = line.strip()
            if claim.casefold() in checked_claims:
                continue
            peer = next((x for x in facts.get("peers", []) if x.get("ticker") and str(x.get("ticker")).upper() in line.upper()), None)
            data_bundle = peer.get("facts", {}) if peer else facts
            available_tags = sorted((known for known in data_bundle.get("tags", {}).values() if known), key=len, reverse=True)
            tag = next((known for known in available_tags if known in line), None)
            if tag:
                metric = next((m for m, t in data_bundle.get("tags", {}).items() if t == tag), None)
                records = data_bundle.get("values", {}).get(metric, {}) if metric else {}
                amount = numeric(row[1]) if len(row) > 1 else None
                accession = next((x for x in row if re.fullmatch(r"\d{10}-\d{2}-\d{6}", x)), "")
                period = row[-1]
                matched = None
                for rec in (records.get("current"), records.get("prior")):
                    if not isinstance(rec, dict):
                        continue
                    if accession == rec.get("accn") and period == rec.get("end"):
                        matched = rec
                        break
                valid_value = matched is not None and amount is not None and abs(amount - float(matched.get("val", 0))) < 1e-8
                status = "correct" if valid_value else "wrong"
                if valid_value:
                    reason = f"Tag, accession, period end, and value match the saved facts ({tag}, {matched.get('end')})."
                    correction = ""
                else:
                    source_rec = next((r for r in (records.get("current"), records.get("prior")) if isinstance(r, dict) and r.get("accn") == accession), None)
                    if source_rec:
                        reason = f"The tag/source row does not match the saved fact. Correct source: {tag}, {source_rec.get('end')}, accession {source_rec.get('accn')}."
                        correction = str(source_rec.get("val"))
                    else:
                        reason, correction = f"No saved fact matches {tag}, accession {accession}, and period {period}.", ""
                checked.append({"claim": claim, "status": status, "reason": reason, "correction": correction, "source": f"{tag}; {period}; {accession}"})
                checked_claims.add(claim.casefold())
                continue

            if len(row) >= 3 and "=" in row[-1]:
                equation = row[-1].split("=", 1)
                try:
                    lhs, rhs = equation[0].strip(), float(equation[1].strip().replace(",", ""))
                    if not re.fullmatch(r"[0-9.()*/+\-\s]+", lhs):
                        raise ValueError("unsupported arithmetic")
                    computed = float(eval(lhs, {"__builtins__": {}}, {}))
                    shown = numeric(row[1])
                    if shown is None:
                        raise ValueError("reported value missing")
                    shown_scaled = shown / 100 if "%" in row[1] else shown
                    expected_shown = rhs / 100 if "%" in row[1] else rhs
                    ok = abs(computed - rhs) <= max(1e-8, abs(computed) * 1e-6) and abs(shown_scaled - expected_shown) <= max(0.00005 if "%" in row[1] else 1e-8, abs(expected_shown) * 1e-6)
                    status = "correct" if ok else "wrong"
                    reason = "The displayed value matches its quoted arithmetic." if ok else "The displayed value or arithmetic does not match the quoted inputs."
                    checked.append({"claim": claim, "status": status, "reason": reason, "correction": "" if ok else f"Arithmetic result: {computed}", "source": row[-1]})
                    checked_claims.add(claim.casefold())
                    continue
                except (ValueError, TypeError, SyntaxError, ZeroDivisionError):
                    pass

            if len(row) >= 4 and row[2].isdigit():
                line_no = int(row[2])
                release_lines = texts.get("earnings_release_exhibit_99_1.txt", "").splitlines()
                source_line = release_lines[line_no - 1] if 0 < line_no <= len(release_lines) else ""
                amount = numeric(row[1])
                direct_numbers = [float(x.replace(",", "")) for x in re.findall(r"\$?([\d,]+(?:\.\d+)?)", source_line)]
                exact = amount is not None and any(abs(amount - x) < 1e-8 for x in direct_numbers)
                # A citation to a rounded release amount must retain its wording.
                status = "correct" if exact else "wrong"
                reason = "The release line contains the reported amount." if exact else f"The cited release line does not state this exact amount. Source line: {source_line}"
                correction = "" if exact else source_line
                checked.append({"claim": claim, "status": status, "reason": reason, "correction": correction, "source": f"release line {line_no:05d}"})
                checked_claims.add(claim.casefold())
                continue

            if peer and "%" in line:
                shown = numeric(next((x for x in row if "%" in x), ""))
                expected = peer.get("margin")
                ok = shown is not None and expected is not None and abs(shown / 100 - float(expected)) <= 0.00005
                checked.append({"claim": claim, "status": "correct" if ok else "wrong", "reason": "Peer margin matches operating income divided by revenue from its saved facts." if ok else "Peer margin does not match the saved facts.", "correction": "" if ok else str(expected), "source": f"{peer.get('ticker')} saved XBRL facts"})
                checked_claims.add(claim.casefold())

        for mark in marks:
            if not isinstance(mark, dict):
                continue
            claim = str(mark.get("claim", ""))
            if re.match(r"\s*-?\s*Filing Accession:\s*\d{10}-\d{2}-\d{6}\s*$", claim, re.I):
                continue
            if claim.strip().casefold() in checked_claims:
                continue
            if claim and claim.casefold() not in auditable.casefold():
                continue
            status = str(mark.get("status", "unsupported")).lower()
            source = str(mark.get("source", ""))
            if not source and not citation_re.search(claim):
                status = "unsupported"
                mark["reason"] = (str(mark.get("reason", "")) + " No verifiable source was supplied.").strip()
            check = mark.get("code_check")
            if isinstance(check, dict) and check.get("tag"):
                tag, period, value = str(check["tag"]), str(check.get("period", "")), check.get("value")
                found = False
                for metric, tag_name in facts.get("tags", {}).items():
                    if tag_name == tag:
                        record = facts.get("values", {}).get(metric, {})
                        found = any(str(rec.get("end")) == period and str(rec.get("val")) == str(value) for rec in (record.get("current"), record.get("prior")) if isinstance(rec, dict))
                if not found:
                    status = "wrong"
                    mark["reason"] = "The supplied tag, period, and value do not match the saved facts."
            ratio = mark.get("ratio_check")
            if isinstance(ratio, dict):
                try:
                    operation = ratio.get("operation")
                    inputs = [float(x) for x in ratio.get("inputs", [])]
                    reported = float(ratio.get("reported"))
                    if operation == "divide" and len(inputs) == 2:
                        expected = inputs[0] / inputs[1]
                    elif operation == "subtract" and len(inputs) == 2:
                        expected = inputs[0] - inputs[1]
                    elif operation == "growth" and len(inputs) == 2:
                        expected = inputs[0] / inputs[1] - 1
                    else:
                        expected = reported
                    if abs(expected - reported) > max(1e-8, abs(expected) * 1e-6):
                        status = "wrong"
                        mark["reason"] = "The reported ratio does not match the arithmetic on its quoted inputs."
                except (TypeError, ValueError, ZeroDivisionError):
                    status = "unsupported"
                    mark["reason"] = "The ratio inputs or arithmetic are incomplete."
            cite = citation_re.search(claim) or citation_re.search(source)
            if cite:
                form, line = cite.groups()
                fname = filing_for_form[form.lower()]
                source_text = texts.get(fname, "")
                if form.lower() == "release" and not source_text:
                    source_text = texts.get("earnings_release_exhibit_99.txt", "")
                source_lines = source_text.splitlines()
                index = int(line) - 1
                saved_line = source_lines[index] if 0 <= index < len(source_lines) else ""
                if not saved_line.startswith(f"{int(line):05d}:"):
                    status = "unsupported"
                    mark["reason"] = "The cited line number is absent from the saved filing text."
            mark["status"] = status if status in {"correct", "wrong", "unsupported"} else "unsupported"
            checked.append(mark)
            checked_claims.add(claim.strip().casefold())
        # Add deterministic unsupported marks for numeric sentences with no source.
        for line in auditable.splitlines():
            if line.strip().casefold() in checked_claims:
                continue
            if re.search(r"Filing Accession:", line, re.I):
                continue
            claim_without_citations = citation_re.sub("", line)
            if re.search(r"\d", claim_without_citations) and not line.strip().startswith("|") and not re.search(r"\b(?:FY|Q[1-4]|20\d{2})\b", claim_without_citations):
                has_source = bool(citation_re.search(line) or "[tag:" in line.casefold() or "[filing accession:" in line.casefold() or "[arithmetic:" in line.casefold() or "[calculated from" in line.casefold())
                reason = "No matching verifier mark was returned for this sourced numeric claim." if has_source else "Numeric claim has no filing-line or XBRL source."
                checked.append({"claim": line.strip(), "status": "unsupported", "reason": reason, "correction": "Remove or source the claim before use."})
                checked_claims.add(line.strip().casefold())
        return checked


def kickoff() -> int:
    global _MODEL_LLM
    parser = argparse.ArgumentParser(description="Lab 4 fixed-order CrewAI equity research desk")
    parser.add_argument("ticker", nargs="?", default="", help="Company ticker (required for a normal run)")
    parser.add_argument("--peers", default="")
    parser.add_argument("--price", type=float)
    parser.add_argument("--verify-only", default="", help="Verify a saved Lab 4 run folder only")
    args = parser.parse_args()
    if not args.verify_only and not args.ticker:
        parser.error("Provide a ticker for a normal run. Use --verify-only with a saved run folder to verify only.")
    env = read_env(COURSE_ROOT / ".env")
    key, model = env.get("API_KEY", "").strip(), env.get("GENAI_MODEL", "").strip()
    base_url = env.get("GENAI_BASE_URL", "https://genai.rcac.purdue.edu/api").strip()
    if not key or not model:
        parser.error("Set API_KEY and GENAI_MODEL in the private course .env file.")
    try:
        _MODEL_LLM = LLM(model=model if "/" in model else f"openai/{model}", api_key=key, base_url=base_url, timeout=240, max_tokens=6000) if key else None
        flow = Lab4Flow()
        flow.kickoff(inputs={"ticker": args.ticker.upper(), "peers": [x.strip().upper() for x in args.peers.split(",") if x.strip()], "price": args.price, "verify_only_path": args.verify_only})
        print(f"Run folder: {flow.state.run_path}")
        if flow.state.report_path:
            print(f"Report: {flow.state.report_path}")
        if flow.state.verified_report_path:
            print(f"Verified report: {flow.state.verified_report_path}")
        return 0
    except Exception as exc:
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(kickoff())
