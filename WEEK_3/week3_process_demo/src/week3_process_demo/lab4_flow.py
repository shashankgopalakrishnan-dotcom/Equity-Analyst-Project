"""Lab 4 fixed-order equity research team using CrewAI Flow."""
from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import re
import sys
import operator
from statistics import median
from datetime import date, datetime
from pathlib import Path
from typing import Any, Literal

from crewai import Agent, LLM
from crewai.flow import Flow, listen, router, start
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from .lab5_calculations import persona_calculations, business_score_average, trailing_ttm_margin

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


def expert_lenses(*names: str) -> dict[str, str]:
    """Load the installed professor-provided expert philosophies as guidance."""
    root = Path.home() / '.codex' / 'skills' / 'financial-researcher' / 'experts'
    result = {}
    for name in names:
        path = root / f'{name}.md'
        if not path.is_file():
            continue
        text = path.read_text(encoding='utf-8', errors='replace')
        section = text.split('## Your Investment Philosophy', 1)
        if len(section) == 2:
            result[name] = section[1].split('\n---', 1)[0].strip()[:2500]
    return result


def normalize_insight(markdown: str) -> str:
    """Normalize an analyst's existing Insight heading and citation formatting."""
    lines = markdown.splitlines()
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if re.match(r'^\s*#{1,6}\s*Insight\s*:?\s*$', line, re.I):
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                line = lines[j].strip()
                if not re.match(r'^Insight:', line, re.I):
                    line = 'Insight: ' + line
                i = j
        if re.match(r'^\s*Insight:', line, re.I):
            line = re.sub(r'\[(10-K|10-Q|8-K|release) line (\d{1,5})\]', lambda m: f'[{m.group(1)} line {int(m.group(2)):05d}]', line, flags=re.I)
            # Research outputs sometimes cite the filing section in prose, for
            # example "(Item 7—MD&A, line 00399)". Normalize it to the single
            # citation form used by the Manager and Verifier.
            line = re.sub(
                r'\((?:Item\s+[17][^,)]*,\s*)?line\s+(\d{1,5})\)',
                lambda m: f'[10-K line {int(m.group(1)):05d}]',
                line,
                flags=re.I,
            )
            line = re.sub(
                r'\((\d{5})\)',
                lambda m: f'[10-K line {m.group(1)}]',
                line,
            )
            line = re.sub(r'\((10-K|10-Q|8-K|release)\s*,?\s*line\s+(\d+)\)', r'[\1 line \2]', line, flags=re.I)
            line = re.sub(r'\[(10-K|10-Q|8-K|release)\s*,\s*line\s+(\d+)\]', r'[\1 line \2]', line, flags=re.I)
            line = re.sub(r'\[(10-K|10-Q|8-K|release)\s+(?:Business|MD&A)(?:\s+section)?\s*,?\s*line\s+(\d+)\]', r'[\1 line \2]', line, flags=re.I)
            line = re.sub(r'\[(10-K|10-Q|8-K|release) line (\d{1,5})\]', lambda m: f'[{m.group(1)} line {int(m.group(2)):05d}]', line, flags=re.I)
        out.append(line)
        i += 1
    return '\n'.join(out)


def extract_release_opening_paragraph(numbered_text: str) -> str | None:
    """Return the dateline/lead paragraph after the release title, or fail closed."""
    lines = numbered_text.splitlines()
    titles = [i for i, line in enumerate(lines[:40])
              if re.search(r'\b(?:results|operating results|financial results)\b', line, re.I)
              and len(re.sub(r'^\d{5}:\s*', '', line).strip()) <= 180]
    if not titles:
        return None
    title_i = titles[0]
    # SEC plain-text conversion keeps each paragraph as one numbered line.
    date_pattern = re.compile(r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+20\d{2}\b', re.I)
    # Filings use both "City, ST, ..." and "City, State. — ..." datelines.
    dateline = re.compile(r'^\d{5}:\s*[A-Z][A-Za-z .\'-]+,\s*(?:[A-Z]{2}|[A-Z][a-z]{1,12}\.?)\s*(?:,|[-–—])\s+', re.I)
    candidates = [line.strip() for line in lines[title_i + 1:title_i + 31]
                  if date_pattern.search(line) and dateline.search(line)
                  and re.search(r'\s[-–—]\s+.+\b(?:results|announced|reported|reports|announces)\b', line, re.I)]
    return candidates[0] if len(candidates) == 1 else None


def financial_figures(text: str) -> set[tuple[str, float]]:
    """Extract amounts and percentages, but ignore years and line citations."""
    text = re.sub(r'\[(?:10-K|10-Q|8-K|release) line \d{1,5}\]', '', text, flags=re.I)
    pattern = re.compile(r'(?i)(?:(?:US\$|\$)\s*(\d[\d,]*(?:\.\d+)?)\s*(billion|million|thousand)?|(\d[\d,]*(?:\.\d+)?)\s*-?\s*(billion|million|thousand|%|percent|weeks?|months?|quarters?|days?))')
    quantity_pattern = re.compile(r'(?i)(\d[\d,]*(?:\.\d+)?)\s+(?:active\s+|new\s+|company-owned\s+|international\s+)*(square feet|sq\.?\s*ft\.?|skus|warehouses|restaurants|stores|locations|members|countries|states|employees|restaurants|chipotlanes)\b')
    scales = {None: 1.0, 'billion': 1_000_000_000.0, 'million': 1_000_000.0, 'thousand': 1_000.0, '%': 1.0, 'percent': 1.0}
    result = set()
    for match in pattern.finditer(text):
        amount = float((match.group(1) or match.group(3)).replace(',', ''))
        unit = (match.group(2) or match.group(4) or '').casefold()
        kind = 'percent' if unit in {'%', 'percent'} else 'period' if unit in {'week', 'weeks', 'month', 'months', 'quarter', 'quarters', 'day', 'days'} else 'money'
        result.add((kind, amount * scales.get(unit or None, 1.0)))
    for match in quantity_pattern.finditer(text):
        result.add(('quantity', float(match.group(1).replace(',', ''))))
    return result


def release_money_amount(text: str, default_multiplier: float = 1.0) -> float | None:
    """Read a revenue amount from the cited line, honoring units on that line."""
    match = re.search(r"\$\s*(\d[\d,]*(?:\.\d+)?)\s*(billion|million|thousand)?\b", text, re.I)
    if not match:
        match = re.search(r"(?<![\w.])(\d[\d,]*(?:\.\d+)?)\s*(billion|million|thousand)\b", text, re.I)
    if not match:
        # Statement rows often put the unit in a prior header line, for example
        # "Total revenue 95,723 86,156 ..." after "dollars in millions".
        table_row = re.search(r"\b(?:total\s+revenue|total\s+net\s+sales|net\s+sales)\b[^\d$]*\$?\s*(\d[\d,]*(?:\.\d+)?)", text, re.I)
        if not table_row:
            return None
        amount = float(table_row.group(1).replace(",", ""))
        return amount * default_multiplier
    amount = float(match.group(1).replace(",", ""))
    unit = (match.group(2) or "").casefold()
    multiplier = {"billion": 1_000_000_000, "million": 1_000_000, "thousand": 1_000}.get(unit, default_multiplier)
    return amount * multiplier


def format_release_money(amount: float) -> str:
    """Render release revenue with the largest exact common unit."""
    for divisor, label in ((1_000_000_000, "billion"), (1_000_000, "million")):
        scaled = amount / divisor
        if scaled >= 1 and abs(scaled - round(scaled)) < 1e-9:
            return f"${scaled:,.0f} {label}"
        if scaled >= 1 and abs(scaled - round(scaled, 1)) < 1e-9:
            return f"${scaled:,.1f} {label}"
    if amount >= 1_000_000 and abs(amount / 1_000_000 - round(amount / 1_000_000)) < 1e-9:
        return f"${amount / 1_000_000:,.0f} million"
    return f"${amount:,.0f}"


def safe_arithmetic(expression: str) -> float:
    """Evaluate simple arithmetic without eval, exponentiation or names."""
    tree = ast.parse(expression.replace(',', ''), mode='eval')
    binary = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv}
    unary = {ast.UAdd: operator.pos, ast.USub: operator.neg}
    def visit(node):
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
            return float(node.value)
        if isinstance(node, ast.BinOp) and type(node.op) in binary:
            return binary[type(node.op)](visit(node.left), visit(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in unary:
            return unary[type(node.op)](visit(node.operand))
        raise ValueError('Unsupported arithmetic expression')
    return float(visit(tree))


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
    insight_marks: list[VerifierMark] = Field(description="One mark for every Insight line supplied in insight_claims, copying each claim exactly; use an empty list only when there are no Insight lines.")
    marks: list[VerifierMark] = Field(default_factory=list)


class AnalystResult(BaseModel):
    markdown: str
    scores: dict[str, float | None] = Field(default_factory=dict)


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
            raw_facts = json.loads(Path(self.facts["all_facts_path"]).read_text(encoding="utf-8"))
            reference_end = max(filter(None, (self.filings["10k"].get("reportDate"), self.filings["10q"].get("reportDate"))), default=self.facts["fiscal_end"])
            self.facts["ttm"] = trailing_ttm_margin(raw_facts, self.facts["tags"],
                                                      self.filings["10k"]["accessionNumber"],
                                                      self.filings["10q"]["accessionNumber"],
                                                      reference_end)
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
                raw_facts = json.loads(Path(pb["all_facts_path"]).read_text(encoding="utf-8"))
                peer_reference_end = max(filter(None, (pfilings["10k"].get("reportDate"), pfilings["10q"].get("reportDate"))), default=pb.get("fiscal_end"))
                pb["ttm"] = trailing_ttm_margin(raw_facts, pb["tags"],
                                                  pfilings["10k"]["accessionNumber"],
                                                  pfilings["10q"]["accessionNumber"],
                                                  peer_reference_end)
                margin = self.desk.calculate(pb, None)["operating_margin"]
                for key, filename in (("10k", "10k.txt"), ("10q", "10q.txt"), ("earnings_8k", "earnings_8k.txt")):
                    text = pfilings.get("earnings_8k_text") if key == "earnings_8k" else self.desk.filing_text(pcik, pfilings[key], self.user_agent)
                    (pdir / filename).write_text(self.desk.numbered(text), encoding="utf-8")
                self.peer_results.append({"ticker": peer, "company": pname, "cik": pcik, "facts": pb, "margin": margin, "ttm": pb["ttm"],
                                          "filings": {k: {**pfilings[k], "accepted": self.desk.accepted(pfilings[k], pcik, self.user_agent)} for k in ("10k", "10q", "earnings_8k")}})
            result = [{"ticker": x["ticker"], "company": x["company"], "fiscal_end": x["facts"]["fiscal_end"], "margin": x["margin"], "ttm": x["ttm"], "facts": x["facts"]} for x in self.peer_results]
        else:
            raise ValueError(f"Unknown desk step {step}")
        record = {"step": step, "output": result}
        self.step_outputs.append(record)
        dump(io_dir / f"step_{step}_output.json", result)
        return json.dumps(record, ensure_ascii=False, default=str)

    def _read_release(self) -> str:
        path = self.folder / (self.filings.get("release_filename") or "earnings_release_exhibit_99_1.txt")
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
                "peers": [{"ticker": x["ticker"], "company": x["company"], "fiscal_end": x["facts"]["fiscal_end"], "margin": x["margin"], "ttm": x["ttm"], "facts": x["facts"], "filings": x["filings"]} for x in self.peer_results]}


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
        self.state.context_json = self._role_context(ctx, manifest)
        dump(folder / "desk_manifest.json", manifest)
        return str(folder)

    @listen(seven_data_steps)
    def research_analyst(self, _: str) -> str:
        print("Starting node: Research Analyst")
        ctx = self.state.context_json
        source = self._numbered_source(Path(self.state.run_path) / "10k.txt", ("Item 1", "Item 7"))
        release_name = ctx["filings"].get("release_filename") or "earnings_release_exhibit_99_1.txt"
        release = self._numbered_source(Path(self.state.run_path) / release_name, ())
        payload = self._payload("Describe the business model, competitive position, catalysts, and recent developments. Expert lenses are optional methods only; follow your persona and never treat the expert text as company evidence.",
                                {"company": ctx["company"], "ticker": ctx["ticker"], "10k_numbered_source": source, "release_numbered_source": release, "expert_lenses": expert_lenses('peter_lynch', 'warren_buffett')},
                                "JSON with markdown, claims, and scores: {growth_evidence, competitive_position, risk_exposure}; each score must be an integer 1 to 5 or null. Cite each factual statement by source line.")
        result = self._json_object(self._call_role("research_analyst", "Research Analyst", payload))
        scores = result.get("scores", {}) if isinstance(result.get("scores"), dict) else {}
        result["business_score_average"] = business_score_average(scores.get("growth_evidence"), scores.get("competitive_position"))
        result["release_opening_paragraph"] = ctx.get("release_opening_paragraph")
        result["expert_lens_provenance"] = list(expert_lenses('peter_lynch', 'warren_buffett'))
        self.state.outputs["research"] = json.dumps(result, ensure_ascii=False)
        self._save_role_io("research_analyst", payload, self.state.outputs["research"])
        return self.state.outputs["research"]

    @listen(research_analyst)
    def financial_analyst(self, _: str) -> str:
        print("Starting node: Financial Analyst")
        c = self.state.context_json
        payload = self._payload("Report the annual facts and ratios, latest-quarter revenue and diluted EPS, and peer margins. Use the calculator values. Do not calculate in the model. Copy persona_calculations.financial_scores exactly into scores; null means unavailable, never a numeric score. For the peer-comparison score and conclusion, compare persona_calculations.peer_company_ttm_margin with persona_calculations.peer_median_operating_margin only; both values must be TTM and use the aligned periods. Do not compare the latest annual company margin with a peer TTM margin. Expert lenses are optional methods, not evidence of company facts.",
                                {"ticker": c["ticker"], "company": c["company"], "facts": c["facts"], "calculations": c["calculations"], "calculation_arithmetic": c["calculation_arithmetic"], "release_numbered_source": c["release_lines"], "release_opening_paragraph": c["release_opening_paragraph"], "peers": c["peers"], "persona_calculations": c["persona_calculations"], "10k_numbered_source": self._financial_source(Path(self.state.run_path) / "10k.txt"), "expert_lenses": expert_lenses('ben_graham')},
                                "JSON with markdown and claims. Every number must have its filing/tag/period or release line. Cite each annual metric to its own exact statement line if you cite a statement line: Total revenue, Income from operations, Net income, and Diluted EPS are different lines. Use the exact XBRL accession, tag, and period for each annual fact; do not convert raw XBRL dollars into another unit unless you label the unit. Do not reuse one line citation for several metrics.")
        result = self._json_object(self._call_role("financial_analyst", "Financial Analyst", payload))
        expected_scores = c['persona_calculations']['financial_scores']
        result['score_validation'] = {'expected': expected_scores, 'valid': result.get('scores') == expected_scores}
        values = list(expected_scores.values())
        result['financial_support_score'] = None if any(value is None for value in values) else (3 if values.count(3) >= 3 else 1 if values.count(1) >= 3 else 2)
        self.state.outputs["financial"] = json.dumps(result, ensure_ascii=False)
        self._save_role_io("financial_analyst", payload, self.state.outputs["financial"])
        return self.state.outputs["financial"]

    @listen(financial_analyst)
    def investment_advisor(self, _: str) -> str:
        print("Starting node: Investment Advisor")
        research = self._json_object(self.state.outputs['research'])
        financial = self._json_object(self.state.outputs['financial'])
        expected = {'business_evidence': research.get('business_score_average'), 'financial_support': financial.get('financial_support_score'), 'risk_exposure': research.get('scores', {}).get('risk_exposure')}
        payload = self._payload("Give a thesis, Buy/Hold/Sell recommendation, and one deciding reported number. Use only the two analyst outputs. A null score is unavailable; do not substitute a number. Recommend Buy only when business evidence is at least 4, financial support is exactly 3, and risk exposure is 3 or below. If any Buy condition is false or unavailable, choose Hold unless the evidence supports Sell.",
                                {"research_analyst_output": research, "financial_analyst_output": financial},
                                "Return markdown and copy these externally validated values exactly into scores: " + json.dumps(expected))
        result = self._json_object(self._call_role("investment_advisor", "Investment Advisor", payload))
        result['score_validation'] = {'expected': expected, 'valid': result.get('scores') == expected}
        result['markdown'], result['recommendation_validation'] = self._enforce_advisor_buy_rule(
            str(result.get('markdown', '')), expected)
        self.state.outputs["advisor"] = json.dumps(result, ensure_ascii=False)
        self._save_role_io("investment_advisor", payload, self.state.outputs["advisor"])
        return self.state.outputs["advisor"]

    @staticmethod
    def _enforce_advisor_buy_rule(markdown: str, scores: dict) -> tuple[str, dict]:
        """Prevent a Buy when the persona's three required scores do not qualify."""
        patterns = (
            r'(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?Recommendation(?:\*\*)?\s*:\s*(?:\*\*)?(?P<decision>Buy|Hold|Sell)(?:\*\*)?\s*$',
            r'(?im)^\s*(?:#{1,6}\s*)?(?:\*\*)?(?P<decision>Buy|Hold|Sell)(?:\*\*)?\s*$',
        )
        match = next((found for pattern in patterns if (found := re.search(pattern, markdown))), None)
        business = scores.get('business_evidence')
        financial = scores.get('financial_support')
        risk = scores.get('risk_exposure')
        eligible = (isinstance(business, (int, float)) and not isinstance(business, bool) and business >= 4
                    and financial == 3
                    and isinstance(risk, (int, float)) and not isinstance(risk, bool) and risk <= 3)
        if not match:
            return markdown, {'valid': False, 'reported': None, 'buy_eligible': eligible,
                              'reason': 'No standalone Buy, Hold, or Sell recommendation was found.'}
        reported = match.group('decision')
        if reported.casefold() != 'buy' or eligible:
            return markdown, {'valid': True, 'reported': reported, 'buy_eligible': eligible, 'reason': ''}
        reason = (f"Buy requires business evidence >= 4, financial support = 3, and risk exposure <= 3. "
                  f"Supplied scores are business={business}, financial={financial}, risk={risk}; use Hold.")
        corrected = markdown[:match.start('decision')] + 'Hold' + markdown[match.end('decision'):]
        lines = corrected.splitlines()
        idx = markdown[:match.start('decision')].count('\n')
        if 0 <= idx < len(lines):
            lines.insert(idx + 1, f"**Recommendation rule:** {reason}")
        corrected = '\n'.join(lines)
        return corrected, {'valid': True, 'reported': 'Hold', 'original': reported,
                           'buy_eligible': eligible, 'reason': reason, 'corrected_by_rule': True}

    def _insight_issues(self, role: str, output: str, opening: str) -> list[str]:
        """Deterministic Manager checks for one role's required Insight line."""
        body = str(self._json_object(output).get("markdown", output))
        insights = re.findall(r'(?im)^\s*(?:[-*]\s*)?(?:\*\*)?Insight:(?:\*\*)?\s*(.+)$', body)
        if len(insights) != 1:
            return [f"Return exactly one Insight line; found {len(insights)}."]
        claim = "Insight: " + insights[0].strip()
        citation = re.search(r'\[(10-K|10-Q|8-K|release) line (\d{5})\]', claim, re.I)
        if not citation:
            return ["Use one zero-padded five-digit filing-line citation."]
        filing, line_no = citation.groups()
        folder = Path(self.state.run_path)
        manifest = json.loads((folder / "desk_manifest.json").read_text(encoding="utf-8"))
        release_name = manifest.get("release_filename") or "earnings_release_exhibit_99_1.txt"
        source_name = {"10-k": "10k.txt", "10-q": "10q.txt", "8-k": "earnings_8k.txt", "release": release_name}[filing.casefold()]
        source_lines = (folder / source_name).read_text(encoding="utf-8", errors="replace").splitlines() if (folder / source_name).exists() else []
        source_line = source_lines[int(line_no) - 1] if 0 < int(line_no) <= len(source_lines) else ""
        issues = []
        if not source_line.startswith(f"{int(line_no):05d}:") or not source_line.split(":", 1)[-1].strip():
            issues.append(f"Citation {filing} line {line_no} is not a saved source line.")
        if role == "research" and (filing.casefold() != "10-k" or not self._is_business_or_mda_line(source_lines, int(line_no))):
            issues.append("Research Insight must cite a line inside the 10-K Business or MD&A section.")
        repeated = financial_figures(claim) & financial_figures(opening)
        if repeated:
            display = ", ".join(f"{kind} {value:g}" for kind, value in sorted(repeated))
            issues.append(f"Insight repeats opening-paragraph figure(s): {display}.")
        return issues

    @staticmethod
    def _same_insight_claim(left: str, right: str) -> bool:
        """Detect repeated wording or the same reported figure about the same subject."""
        citation = r"\[(?:10-K|10-Q|8-K|release) line \d{5}\]"

        def clean(value: str) -> str:
            value = re.sub(citation, "", value, flags=re.I)
            value = value.replace("’", "'").replace("‘", "'")
            return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()

        left_text, right_text = clean(left), clean(right)
        if not left_text or not right_text:
            return False
        if left_text == right_text:
            return True
        shared_figures = financial_figures(left) & financial_figures(right)
        if not shared_figures:
            return False
        anchors = {
            "revenue", "sales", "income", "earnings", "eps", "margin", "debt", "equity",
            "cash", "capex", "warehouse", "membership", "members", "stores", "restaurants",
            "fees", "dividend", "buyback", "repurchase", "employees", "customers",
        }
        left_anchors = set(left_text.split()) & anchors
        right_anchors = set(right_text.split()) & anchors
        return bool(left_anchors & right_anchors)

    def _duplicate_insight_issues(self) -> dict[str, str]:
        """Require a distinct claim for each role's Insight line."""
        seen: list[tuple[str, str]] = []
        issues: dict[str, str] = {}
        for role in ("research", "financial", "advisor"):
            body = str(self._json_object(self.state.outputs.get(role, "")).get("markdown", ""))
            found = re.findall(r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?Insight:(?:\*\*)?\s*(.+)$", body)
            if len(found) != 1:
                continue
            claim = found[0]
            prior = next((prior_role for prior_role, prior_claim in seen
                          if self._same_insight_claim(claim, prior_claim)), None)
            if prior:
                issues[role] = f"Insight repeats the {prior.title()}'s claim or reported figure. Select a different claim already supported in the analyst outputs, with its exact numbered filing line."
            else:
                seen.append((role, claim))
        return issues

    def _distinct_insight_candidate(self, role: str) -> str:
        """Select a distinct cited sentence already present in role outputs."""
        if role != "advisor":
            return ""
        opening = str(self.state.context_json.get("release_opening_paragraph", ""))
        used = []
        for other_role in ("research", "financial"):
            markdown = str(self._json_object(self.state.outputs.get(other_role, "")).get("markdown", ""))
            for claim in re.findall(r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?Insight:(?:\*\*)?\s*(.+)$", markdown):
                used.append(claim)
        citation = re.compile(r"\[(10-K|10-Q|8-K|release) line \d{5}\]", re.I)
        for source_role in ("advisor", "research", "financial"):
            markdown = str(self._json_object(self.state.outputs.get(source_role, "")).get("markdown", ""))
            for line in markdown.splitlines():
                if re.match(r"(?i)^\s*(?:[-*]\s*)?(?:\*\*)?Insight:", line):
                    continue
                for sentence in re.split(r"(?<=[.!?])\s+", line.strip()):
                    if len(citation.findall(sentence)) != 1:
                        continue
                    sentence = re.sub(r"^\s*(?:[-*]\s*)?(?:\*\*)?[^*]+(?:\*\*)?:\s*", "", sentence).strip()
                    if not sentence or not citation.search(sentence):
                        continue
                    claim = "Insight: " + sentence
                    numbers = financial_figures(claim)
                    if numbers & financial_figures(opening):
                        continue
                    if any(self._same_insight_claim(sentence, other) for other in used):
                        continue
                    if self._insight_issues(role, json.dumps({"markdown": claim}), opening):
                        continue
                    return claim
        return ""

    @staticmethod
    def _is_business_or_mda_line(lines: list[str], line_number: int) -> bool:
        active = ""
        for index, line in enumerate(lines, 1):
            clean = re.sub(r"^\d{5}:\s*", "", line)
            if re.match(r"ITEM\s+1\s*(?:[.—–-]\s*)?BUSINESS\b", clean, re.I):
                active = "business"
            elif re.match(r"ITEM\s+1A\b", clean, re.I) and active == "business":
                active = ""
            elif re.match(r"ITEM\s+7\s*(?:[.—–-]\s*)?(?:MANAGEMENT|MD&A)", clean, re.I):
                active = "mda"
            elif re.match(r"ITEM\s+7A\b", clean, re.I) and active == "mda":
                active = ""
            if index == line_number:
                return active in {"business", "mda"}
        return False

    @listen(investment_advisor)
    def strategy_manager(self, _: str) -> str:
        print("Starting node: Strategy Manager")
        if not self.state.context_json.get("release_opening_paragraph"):
            raise RuntimeError("Cannot identify the earnings release opening paragraph; Insight comparison cannot be completed.")
        payload = self._payload("Check all five required sections and consistency. For each role require an Insight: line with a cited filing line. A role fails if its Insight is missing or only repeats a figure in the release opening paragraph. If the opening paragraph is unavailable, report that the comparison cannot be completed; do not assume it passed. Identify each failing section and its originating role. Return valid JSON with failing_parts and report_markdown.",
                                {"role_outputs": self.state.outputs, "required_parts": PARTS, "release_opening_paragraph": self.state.context_json.get("release_opening_paragraph")},
                                "JSON with failing_parts array and report_markdown.")
        first = self._call_role("strategy_manager", "Strategy Manager", payload)
        parsed = self._json_object(first)
        if not isinstance(parsed.get("failing_parts"), list):
            raise RuntimeError("Strategy Manager did not return a failing_parts list; refusing to treat the review as passed.")
        failures = parsed["failing_parts"]
        role_for_part = {PARTS[0]: "research", PARTS[1]: "research", PARTS[2]: "financial", PARTS[3]: "research", PARTS[4]: "advisor"}
        for role, part in (("research", PARTS[0]), ("financial", PARTS[2]), ("advisor", PARTS[4])):
            for issue in self._insight_issues(role, self.state.outputs.get(role, ""), self.state.context_json["release_opening_paragraph"]):
                failures.append({"part": part, "role": role, "why": issue, "deterministic": True})
        for role, issue in self._duplicate_insight_issues().items():
            part = PARTS[4] if role == "advisor" else PARTS[2]
            failures.append({"part": part, "role": role, "why": issue, "deterministic": True})
        financial_validation = self._json_object(self.state.outputs.get('financial', '')).get('score_validation', {})
        if not financial_validation.get('valid', False):
            failures.append({'part': PARTS[2], 'role': 'financial', 'why': 'Use the exact supplied calculator scores, including null for unavailable data.'})
        advisor_validation = self._json_object(self.state.outputs.get('advisor', '')).get('score_validation', {})
        if not advisor_validation.get('valid', False):
            failures.append({'part': PARTS[4], 'role': 'advisor', 'why': 'Copy these validated scores exactly, including null for unavailable data: ' + json.dumps(advisor_validation.get('expected'))})
        corrections: dict[str, str] = {}
        revised_roles: set[str] = set()
        grouped: dict[str, list[dict]] = {}
        for failure in failures if isinstance(failures, list) else []:
            if isinstance(failure, str):
                part = next((candidate for candidate in PARTS if candidate.casefold() in failure.casefold()), None)
                failure = {"part": part, "why": failure} if part else {}
            if not isinstance(failure, dict):
                continue
            part = failure.get("part")
            role = failure.get("role")
            if role not in self.state.outputs:
                role = role_for_part.get(part)
            if part not in PARTS or role not in self.state.outputs:
                continue
            why = str(failure.get("why", ""))
            # The deterministic checks above cover Insight count, citation,
            # section eligibility, opening-paragraph overlap, and duplicates.
            # Ignore the Manager model's Insight findings; its role attribution
            # and figure comparisons can be false even when another Insight has
            # a separate valid issue.
            if re.search(r"insight|opening.paragraph|repeats? a figure", why, re.I) and not failure.get("deterministic"):
                continue
            grouped.setdefault(role, []).append(failure)
        accepted_failures = [failure for role_failures in grouped.values() for failure in role_failures]
        for role, role_failures in grouped.items():
            revised_roles.add(role)
            part_names = list(dict.fromkeys(item["part"] for item in role_failures))
            role_name = {"research": "Research Analyst", "financial": "Financial Analyst", "advisor": "Investment Advisor"}[role]
            print(f"Starting node: {role_name} (revision for {', '.join(part_names)})")
            source_name = {'research': 'research_analyst', 'financial': 'financial_analyst', 'advisor': 'investment_advisor'}[role]
            original_input = Path(self.state.run_path) / 'node_io' / f'{source_name}_input.json'
            original_context = json.loads(original_input.read_text(encoding='utf-8')).get('context', {}) if original_input.exists() else {}
            previous = self._json_object(self.state.outputs[role])
            expected_scores = previous.get("scores", {})
            if role == "financial":
                expected_scores = self.state.context_json["persona_calculations"]["financial_scores"]
            elif role == "advisor":
                expected_scores = advisor_validation.get("expected", {})
            existing_insights = {}
            for other_role in ("research", "financial", "advisor"):
                if other_role == role:
                    continue
                other_markdown = str(self._json_object(self.state.outputs.get(other_role, "")).get("markdown", ""))
                other_lines = re.findall(r'(?im)^\s*(?:[-*]\s*)?(?:\*\*)?Insight:(?:\*\*)?\s*.+$', other_markdown)
                if len(other_lines) == 1:
                    existing_insights[other_role] = other_lines[0].strip()
            revision_payload = self._payload(f"Revise only these failing report parts: {part_names}. Feedback: {role_failures}",
                                             {"prior_role_output": self.state.outputs[role], "parts": role_failures,
                                              "source_context": original_context, "validated_scores": expected_scores,
                                              "release_opening_paragraph": self.state.context_json["release_opening_paragraph"],
                                              "other_roles_insights_do_not_repeat": existing_insights},
                                             "JSON with revised markdown for each assigned report part and the supplied validated scores. Preserve the scores exactly. Return exactly one Insight line. If the Insight failed because it repeats a claim, choose a different, source-supported claim from the supplied analyst outputs. Do not repeat or paraphrase any Insight in other_roles_insights_do_not_repeat. Cite a real numbered filing line in the exact format [10-K line 00123] or [release line 00123]. Do not use page numbers, Item labels, or line ranges. Select the five-digit number from the supplied numbered source.")
            corrected = self._call_role({"research":"research_analyst", "financial":"financial_analyst", "advisor":"investment_advisor"}[role], role_name, revision_payload)
            corrected_obj = self._json_object(corrected)
            supplied_scores = corrected_obj.get("scores")
            if supplied_scores and supplied_scores != expected_scores:
                role_failures.append({"part": part_names[0], "role": role, "why": "The role changed a code-supplied score during a prose revision; the original validated score was retained."})
            corrected_obj["scores"] = expected_scores
            corrected_markdown = str(corrected_obj.get("markdown", ""))
            recommendation_validation = None
            if role == "advisor":
                corrected_markdown, recommendation_validation = self._enforce_advisor_buy_rule(
                    corrected_markdown, expected_scores)
                corrected_obj["markdown"] = corrected_markdown
            revised_insights = re.findall(r'(?im)^\s*(?:[-*]\s*)?(?:\*\*)?Insight:(?:\*\*)?\s*.+$', corrected_markdown)
            if len(revised_insights) == 1:
                previous["markdown"] = corrected_markdown
            revised_role_output = dict(previous)
            revised_role_output["scores"] = expected_scores
            if role == "financial":
                revised_role_output["score_validation"] = {"expected": expected_scores, "valid": True}
            elif role == "advisor":
                revised_role_output["score_validation"] = {"expected": expected_scores, "valid": True}
                revised_role_output["recommendation_validation"] = recommendation_validation or {"valid": False}
            self.state.outputs[role] = json.dumps(revised_role_output, ensure_ascii=False)
            corrected_obj["markdown"] = corrected_markdown or previous.get("markdown", "")
            for part in part_names:
                target_part = PARTS[2] if role == "financial" else PARTS[4] if role == "advisor" else part
                corrections[target_part] = corrected_obj.get(part) or corrected_markdown or corrected
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
        insight_fallbacks = []
        advisor_issues = self._insight_issues("advisor", self.state.outputs.get("advisor", ""),
                                              self.state.context_json["release_opening_paragraph"])
        if advisor_issues or "advisor" in self._duplicate_insight_issues():
            fallback = self._distinct_insight_candidate("advisor")
            if fallback:
                advisor = self._json_object(self.state.outputs.get("advisor", ""))
                advisor_markdown = str(advisor.get("markdown", ""))
                advisor_markdown = re.sub(r'(?im)^\s*(?:[-*]\s*)?(?:\*\*)?Insight:(?:\*\*)?.*$', '', advisor_markdown).rstrip()
                advisor["markdown"] = advisor_markdown + "\n\n" + fallback
                self.state.outputs["advisor"] = json.dumps(advisor, ensure_ascii=False)
                corrections[PARTS[4]] = advisor["markdown"]
                insight_fallbacks.append({"role": "advisor", "claim": fallback,
                                          "reason": "The revised Advisor Insight was missing or duplicated; this distinct claim was copied from an already cited analyst output."})
        # Keep the Manager's review and compilation call, then normalize its
        # output to one instance of each required section. Use the assigned
        # role's revised section when the Manager repeats or merges headings.
        report = self._canonical_report(corrections)
        unresolved = []
        for role in ("research", "financial", "advisor"):
            issues = self._insight_issues(role, self.state.outputs.get(role, ""), self.state.context_json["release_opening_paragraph"])
            unresolved.extend({"role": role, "issue": issue} for issue in issues)
        unresolved.extend({"role": role, "issue": issue} for role, issue in self._duplicate_insight_issues().items())
        unresolved_roles = {item["role"] for item in unresolved}
        # The Advisor's thesis stays outside the verifier's audit. Place only
        # each role's cited Insight before it, so all three can be checked.
        report = re.sub(r'(?im)^\s*(?:[-*]\s*)?(?:\*\*)?Insight:(?:\*\*)?.*$', '', report)
        insight_rows = []
        role_parts = {'research': 'Overview', 'financial': 'Valuation Insights', 'advisor': 'Investment Recommendation'}
        for role, part in role_parts.items():
            source = self.state.outputs.get(role, '')
            source_obj = self._json_object(source)
            content = source_obj.get('markdown', source)
            found = re.findall(r'(?im)^\s*(?:[-*]\s*)?(?:\*\*)?Insight:(?:\*\*)?\s*(.+)$', str(content))
            label = {'research': 'Research Analyst', 'financial': 'Financial Analyst', 'advisor': 'Investment Advisor'}[role]
            insight_text = found[0].strip() if len(found) == 1 and role not in unresolved_roles else "[missing or unresolved; see Verifier marks]"
            insight_rows.append(f'**{label}**\n\nInsight: ({label}) {insight_text}')
        marker = re.search(r'(?im)^##\s*Future Developments and Strategic Recommendations\b', report)
        if not marker:
            marker = re.search(r'(?im)^##\s*Investment Recommendation\b', report)
        section = '\n\n### Analyst Insights\n\n' + '\n\n'.join(insight_rows) + '\n\n'
        report = report[:marker.start()] + section + report[marker.start():] if marker else report + section
        missing = [part for part in PARTS if part.casefold() not in report.casefold()]
        for part in PARTS:
            match = re.search(r"(?im)^##\s*" + re.escape(part) + r"\s*$([\s\S]*?)(?=^##\s|\Z)", report)
            if not match or not match.group(1).strip():
                missing.append(part)
        missing = list(dict.fromkeys(missing))
        manifest = json.loads((Path(self.state.run_path) / "desk_manifest.json").read_text(encoding="utf-8"))
        filings_line = self._filings_line(manifest)
        report_text = f"{filings_line}\nRun time: {datetime.now().astimezone().isoformat(timespec='seconds')}\n\n{report.strip()}\n"
        report_text = self._append_source_linked_data(report_text, manifest, Path(self.state.run_path))
        report_path = Path(self.state.run_path) / f"{self.state.context_json['ticker']}_report.md"
        report_path.write_text(report_text, encoding="utf-8")
        self.state.report_path = str(report_path)
        self.state.manager_decision = {"failing_parts": accepted_failures, "revised_roles": sorted(revised_roles), "manager_calls": 2 if corrections else 1, "missing_after_compile": missing, "unresolved_after_one_revision": unresolved, "insight_fallbacks": insight_fallbacks}
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
        saved_manifest = json.loads((folder / "desk_manifest.json").read_text(encoding="utf-8")) if (folder / "desk_manifest.json").exists() else {}
        report_paths = sorted(p for p in folder.glob("*_report.md") if not p.name.endswith("_verified_report.md"))
        if self.state.report_path:
            report_path = Path(self.state.report_path)
        else:
            ticker_report = folder / f"{self._ticker_from_run(folder, saved_manifest)}_report.md"
            candidates = [p for p in report_paths if "_before_" not in p.name and "_original" not in p.name]
            report_path = ticker_report if ticker_report.is_file() else (candidates[0] if candidates else folder / "report.md")
        if not report_path.is_file():
            raise FileNotFoundError(f"No compiled report found in saved run: {folder}")
        report = report_path.read_text(encoding="utf-8")
        facts_paths = list(folder.glob("*_companyfacts.json"))
        facts_summary = saved_manifest.get("facts", {})
        facts_summary["peers"] = saved_manifest.get("peers", [])
        facts_summary["release_lines"] = saved_manifest.get("release_lines", [])
        facts_summary["calculations"] = saved_manifest.get("calculations", {})
        facts_summary["share_price_input"] = saved_manifest.get("share_price_input")
        facts_summary["persona_calculations"] = saved_manifest.get("persona_calculations", {})
        facts_summary["release_opening_paragraph"] = saved_manifest.get("release_opening_paragraph", "")
        facts_summary["release_filename"] = saved_manifest.get("release_filename") or "earnings_release_exhibit_99_1.txt"
        research_output_path = folder / "node_io" / "research_analyst_output.json"
        if research_output_path.is_file():
            try:
                research_wrapper = json.loads(research_output_path.read_text(encoding="utf-8"))
                research_result = json.loads(research_wrapper.get("raw", "{}"))
                facts_summary["research_scores"] = research_result.get("scores", {})
            except (TypeError, ValueError, json.JSONDecodeError):
                facts_summary["research_scores"] = {}
        facts_summary["raw_companyfacts_files"] = [p.name for p in facts_paths]
        texts = {p.name: p.read_text(encoding="utf-8", errors="replace") for p in folder.glob("*.txt")}
        if not texts or not facts_summary:
            raise RuntimeError("Verifier needs the saved filing texts and facts in the run folder.")
        audited_report, advisor_section = self._without_advisor_section(report)
        audited_report_lines = audited_report.splitlines()
        if audited_report_lines and audited_report_lines[0].startswith("Filings read:"):
            audited_report = "\n".join(audited_report_lines[2:]).strip()
        insight_claims = [line.strip() for line in audited_report.splitlines() if re.match(r'^\s*Insight:', line, re.I)]
        excerpts = self._cited_lines(audited_report, texts, facts_summary["release_filename"])
        model_texts = {name: '\n'.join(lines) for name, lines in excerpts.items()}
        payload = self._payload(
            "First return exactly one mark for EACH entry in insight_claims, even if it has no numeric value. Copy each complete Insight line exactly into claim; check its cited line and meaning. Then audit every other numeric claim in the report. Every claim field must be copied verbatim from one complete line in compiled_report; do not summarize, combine, or invent claims. If no exact report line supports a candidate mark, omit it. Do not audit or reproduce the omitted Investment Advisor thesis. The saved filing texts are numbered excerpts around cited lines, not complete documents: if evidence is missing, mark the claim unsupported rather than guessing. For every XBRL claim, compare its value, tag, accession, and period with saved_facts. For every filing-line citation, confirm the cited numbered line exists in saved_filing_texts and that it states the number for the stated period and definition. Recalculate every ratio from its quoted inputs. If the filing offers more than one definition, mark a ratio unsupported unless its definition is stated. Mark each claim correct, wrong, or unsupported. For each wrong or unsupported claim, give a corrected claim with the actual filing line or XBRL tag and period. Do not add claims or reproduce the source files.",
            {"insight_claims": insight_claims, "compiled_report": audited_report, "saved_filing_texts": model_texts, "saved_facts": facts_summary},
            "Valid JSON with insight_marks and marks arrays. insight_marks must contain exactly one mark for each complete Insight line, with the claim copied exactly. Each mark must have claim, status, reason, correction, source, and corrected_claim. Use corrected_claim only when saved evidence supports the correction. Do not return or reproduce the filing texts.")
        raw = self._call_role("verifier", "Verifier", payload, verifier=True)
        result = self._json_object(raw)
        insight_marks = result.get("insight_marks", []) if isinstance(result.get("insight_marks", []), list) else []
        other_marks = result.get("marks", []) if isinstance(result.get("marks", []), list) else []
        marks = insight_marks + other_marks
        report_lines = {line.strip().casefold() for line in audited_report.splitlines() if line.strip()}
        # The model can invent peer rows or rephrase a claim. Such text is not
        # part of the report and must not appear as an audit finding.
        marks = [mark for mark in marks if isinstance(mark, dict)
                 and str(mark.get("claim", "")).strip().casefold() in report_lines]
        marks = self._code_checks(marks, audited_report, texts, facts_summary)
        unique_marks = {}
        for mark in marks:
            key = str(mark.get('claim', '')).strip().casefold()
            if not key:
                continue
            previous = unique_marks.get(key)
            priority = lambda item: (bool(item.get('deterministic_check')), bool(item.get('replacement_claim')), {'wrong': 2, 'unsupported': 1, 'correct': 0}.get(item.get('status'), 1))
            if previous is None or priority(mark) > priority(previous):
                unique_marks[key] = mark
        marks = list(unique_marks.values())
        opening_figures = financial_figures(str(facts_summary.get("release_opening_paragraph", "")))
        for line in audited_report.splitlines():
            claim = line.strip()
            if not re.match(r'^Insight:', claim, re.I):
                continue
            mark = next((item for item in marks if str(item.get('claim', '')).strip() == claim), None)
            if mark is None:
                mark = {'claim': claim, 'status': 'unsupported', 'reason': 'The verifier did not return a mark for this Insight.', 'correction': 'Check the filing line before use.', 'source': ''}
                marks.append(mark)
            if financial_figures(claim) & opening_figures:
                mark['status'] = 'wrong'
                mark['reason'] = 'Insight repeats a financial figure or period length from the earnings release opening paragraph.'
                mark['correction'] = 'Replace it with a different source-supported filing claim.'
                mark.pop('replacement_claim', None)
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
        if role_name in {"Research Analyst", "Financial Analyst", "Investment Advisor"}:
            payload = dict(payload)
            citation_rule = ('For every company-specific factual claim, cite the exact numbered source line at the end of the sentence. '
                             'Use only [10-K line 00123] or [release line 00123] format with the actual five-digit line number. '
                             'Do not cite page numbers, Item labels, or line ranges. Do not invent a citation.')
            if role_name == "Research Analyst":
                payload['task'] += (' Use only the supplied numbered 10-K Business and MD&A lines and earnings release lines for factual claims. '
                                    + citation_rule + ' The Insight must cite one 10-K Business or MD&A line and must not repeat a figure or period length from the release opening paragraph.')
            elif role_name == "Financial Analyst":
                payload['task'] += (' Use the supplied facts and calculator values. For reported filing facts, include the exact tag, accession, and period in the source-linked data already appended by code. '
                                    + citation_rule + ' Do not use a report page number as a source.')
            else:
                payload['task'] += (' Use only the two analyst outputs. Copy an exact numbered filing-line citation from an analyst claim; do not replace it with a page citation or create a new source. '
                                    'Write an Insight claim that is different from both analyst Insight claims. Select a different specific claim already supported in either analyst output, and copy its exact numbered filing-line citation. '
                                    + citation_rule + ' Do not repeat a figure or period length from the release opening paragraph.')
            payload['expected_output'] += (' Return your report in the markdown field. End that field with exactly one Insight: line. '
                                          'Use an exact citation formatted [10-K line 00123] or [release line 00123] with the actual line number. '
                                          'Do not use page numbers or invent a citation.')
        message = json.dumps(payload, ensure_ascii=False, default=str)
        analyst = role_name in {"Research Analyst", "Financial Analyst", "Investment Advisor"}
        result = agent.kickoff(message, response_format=VerifierResult if verifier else AnalystResult) if verifier or analyst else agent.kickoff(message)
        if verifier or analyst:
            structured = getattr(result, "pydantic", None)
            if structured is None:
                raise RuntimeError(f"The {role_name} did not return the required structured output.")
            data = structured.model_dump()
            if analyst:
                data['markdown'] = normalize_insight(data['markdown'])
            return json.dumps(data, ensure_ascii=False)
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
        current = {key: (values.get(key, {}).get("current") or {}).get("val") for key in values}
        prior = {key: (values.get(key, {}).get("prior") or {}).get("val") for key in values}
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

        release_file = folder / (manifest.get("release_filename") or "earnings_release_exhibit_99_1.txt")
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
                quoted_content = re.sub(r"^\d{5}:\s*", "", content)
                rows.append(f"- \"{quoted_content}\" [release line {line_no:05d}]")
            default_multiplier = 1_000_000 if re.search(r"dollars in millions|amounts in millions", "\n".join(release_numbered), re.I) else (1_000 if re.search(r"dollars in thousands|amounts in thousands", "\n".join(release_numbered), re.I) else 1)
            for line_no, content in release_refs:
                clean = re.sub(r"^\d{5}:\s*", "", content)
                revenue_value = release_money_amount(clean, default_multiplier=default_multiplier)
                if re.search(r"total\s+revenue|total\s+net\s+sales|net\s+sales", clean, re.I) and revenue_value is not None:
                    display = format_release_money(revenue_value)
                    rows.append(f"- Latest-quarter Total Revenue: {display} [release line {line_no:05d}]")
                elif re.search(r"diluted", clean, re.I):
                    eps_match = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", clean)
                    if eps_match:
                        rows.append(f"- Latest-quarter Diluted EPS: ${float(eps_match.group(1).replace(',', '')):,.2f} [release line {line_no:05d}]")

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
                op = (bundle.get("values", {}).get("operating_income", {}).get("current") or {}).get("val")
                rev = (bundle.get("values", {}).get("revenue", {}).get("current") or {}).get("val")
                peer_rows.append(f"| {peer.get('ticker')} Operating Margin | {float(margin):.2%} | [arithmetic: {op} / {rev} = {float(margin):.12g}] |")
        if peer_rows:
            rows.extend(["", "Peer facts and margins:", "", "| Peer fact | Value | Unit | Accession | XBRL tag | Period end |", "|---|---:|---|---|---|---|"])
            rows.extend(row for row in peer_rows if "Operating Margin" not in row)
            rows.extend(["", "| Peer margin | Value | Arithmetic |", "|---|---:|---|"])
            rows.extend(row for row in peer_rows if "Operating Margin" in row)

        aligned = manifest.get("facts", {}).get("ttm")
        aligned_rows = []
        companies = [(manifest.get("ticker", "COMPANY"), aligned)]
        companies.extend((peer.get("ticker", "PEER"), peer.get("ttm")) for peer in manifest.get("peers", []))
        for ticker, ttm in companies:
            if not isinstance(ttm, dict) or not ttm.get("available"):
                continue
            source_names = []
            for metric, label in (("revenue", "Revenue"), ("operating_income", "Operating Income")):
                source = ttm.get(f"{metric}_source", {})
                annual = source.get("annual") or source
                current_ytd, prior_ytd = source.get("current_ytd"), source.get("prior_ytd")
                if current_ytd and prior_ytd:
                    expression = f"{annual['val']} + {current_ytd['val']} - {prior_ytd['val']}"
                    source_names.append(f"{annual.get('accn')}+{current_ytd.get('accn')}-{prior_ytd.get('accn')}")
                else:
                    expression = f"{annual['val']}"
                    source_names.append(str(annual.get("accn", "")))
                amount = float(ttm[metric])
                shown = f"${amount:,.0f}" if amount.is_integer() else f"${amount:,.2f}"
                aligned_rows.append(f"| {ticker} TTM {label} | {shown} | [arithmetic: {expression} = {amount:.12g}] | {ttm.get('period_start')} to {ttm.get('period_end')} | {source.get('tag', '')}; {'/'.join(x for x in source_names if x)} |")
            margin = float(ttm["margin"])
            percent = margin * 100
            revenue = float(ttm["revenue"])
            operating_income = float(ttm["operating_income"])
            aligned_rows.append(f"| {ticker} TTM Operating Margin | {percent:.2f}% | [arithmetic: {operating_income:.12g} / {revenue:.12g} = {margin:.12g}] | {ttm.get('period_start')} to {ttm.get('period_end')} | Same trailing 12-month window |")
        if aligned_rows:
            rows.extend(["", "Aligned trailing-12-month peer data (annual filings plus current YTD less prior-year YTD where required):", "", "| Measure | Value | Arithmetic | Period | Source basis |", "|---|---:|---|---|---|"])
            rows.extend(aligned_rows)
            alignment = manifest.get("persona_calculations", {})
            median_value = alignment.get("peer_median_operating_margin")
            rows.append(f"| Peer TTM median operating margin | {f'{float(median_value):.2%}' if median_value is not None else 'insufficient evidence'} | {alignment.get('peer_comparison_status', 'No aligned peer TTM data')} | Anchor: {(aligned or {}).get('period_end', '')}; maximum date difference: {alignment.get('peer_alignment_window_days', 45)} days |")

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
            matches = [i for i, line in enumerate(lines) if claim.casefold() == line.strip().casefold() or line.strip().casefold().startswith(claim.casefold())]
            if not matches:
                continue
            if replacement:
                for matched in matches:
                    lines[matched] = replacement
            elif str(mark.get("status", "")).lower() == "unsupported":
                for matched in matches:
                    if claim.casefold().startswith("insight:"):
                        role = re.search(r"\(([^)]+)\)", claim)
                        lines[matched] = f"Insight: ({role.group(1) if role else 'Analyst'}) unresolved; see audit table."
                    else:
                        lines[matched] = ""
                prior_correction = str(mark.get("correction", "")).strip()
                mark["correction"] = (prior_correction + " Removed the claim from the verified body because saved evidence did not support it.").strip()
            else:
                # Keep an unsupported number out of the verified body when the
                # saved records do not provide a defensible replacement.
                for matched in matches:
                    if claim.casefold().startswith("insight:"):
                        role = re.search(r"\(([^)]+)\)", claim)
                        lines[matched] = f"Insight: ({role.group(1) if role else 'Analyst'}) unresolved; see audit table."
                    else:
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
        release_path = ctx.folder / (ctx.filings.get("release_filename") or "earnings_release_exhibit_99_1.txt")
        release = release_path.read_text(encoding="utf-8", errors="replace") if release_path.exists() else ""
        opening = extract_release_opening_paragraph(release)
        if not opening:
            raise RuntimeError("Could not identify the earnings release opening paragraph from its numbered saved text.")
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
        peer_data = [{"ticker": x["ticker"], "fiscal_end": x["facts"].get("fiscal_end"), "operating_margin": x["margin"], "ttm": x.get("ttm")} for x in ctx.peer_results]
        persona_scores = persona_calculations(facts_compact, peer_data, ctx.facts.get("fiscal_end"), ctx.facts.get("ttm"))
        manifest["persona_calculations"] = persona_scores
        manifest["release_opening_paragraph"] = opening
        manifest["release_filename"] = ctx.filings.get("release_filename") or "earnings_release_exhibit_99_1.txt"
        return {"ticker": ctx.ticker, "company": ctx.company, "facts": facts_compact, "release_opening_paragraph": opening,
                "company_ttm": ctx.facts.get("ttm"),
                "persona_calculations": persona_scores,
                "tags": ctx.facts.get("tags", {}), "units": ctx.facts.get("units", {}),
                "fiscal_end": ctx.facts.get("fiscal_end"), "calculations": ctx.calculations,
                "calculation_arithmetic": ctx._calculation_lines(), "release_lines": release_lines,
                "peers": [{"ticker": x["ticker"], "company": x["company"], "facts": x["facts"]["values"], "tags": x["facts"]["tags"], "units": x["facts"]["units"], "fiscal_end": x["facts"]["fiscal_end"], "operating_margin": x["margin"], "ttm": x["ttm"], "filings": x["filings"]} for x in ctx.peer_results],
                "filings": manifest["filings"]}

    @staticmethod
    def _financial_source(path: Path) -> str:
        if not path.exists():
            return ""
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        pattern = re.compile(r"total revenue|net sales|net income|operating income|long.term debt|net cash provided by operating|additions to property|diluted", re.I)
        return "\n".join(line for line in lines if pattern.search(line))[:40000]

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
                if re.match(r"ITEM\s+1\s*(?:[.—–-]\s*)?BUSINESS\b", clean, re.I):
                    section = "business"
                elif re.match(r"ITEM\s+1A\b", clean, re.I) and section == "business":
                    section = ""
                elif re.match(r"ITEM\s+7\s*(?:[.—–-]\s*)?(?:MANAGEMENT|MD&A)", clean, re.I):
                    section = "mda"
                elif re.match(r"ITEM\s+7A\b", clean, re.I) and section == "mda":
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
        return {"markdown": raw, "report_markdown": raw}

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

    @staticmethod
    def _release_quarter_rows(manifest: dict, folder: Path) -> list[str]:
        """Render the selected release's current-quarter revenue and diluted EPS."""
        release_name = manifest.get("release_filename") or "earnings_release_exhibit_99_1.txt"
        path = folder / release_name
        if not path.exists():
            path = folder / "earnings_release_exhibit_99.txt"
        if not path.exists():
            return ["Quarterly revenue and diluted EPS were unavailable in the saved release lines."]
        numbered = path.read_text(encoding="utf-8", errors="replace").splitlines()
        contents = "\n".join(numbered)
        default_multiplier = (1_000_000 if re.search(r"dollars in millions|amounts in millions", contents, re.I)
                             else 1_000 if re.search(r"dollars in thousands|amounts in thousands", contents, re.I) else 1)
        selected = [str(x) for x in manifest.get("release_lines", [])]
        rows: list[str] = []
        for text in selected:
            clean = re.sub(r"^\d{5}:\s*", "", text).strip()
            found = next(((i + 1, line) for i, line in enumerate(numbered)
                          if re.sub(r"^\d{5}:\s*", "", line).strip().casefold() == clean.casefold()), None)
            if not found:
                continue
            line_no, source = found
            plain = re.sub(r"^\d{5}:\s*", "", source).strip()
            if re.search(r"(?i)^total\s+revenue\b|\btotal\s+revenue\s+(?:in|was|of)\b", plain):
                amount = release_money_amount(plain, default_multiplier=default_multiplier)
                if amount is not None:
                    rows.append(f"- Latest-quarter Total Revenue: {format_release_money(amount)} [release line {line_no:05d}]")
            elif re.search(r"(?i)diluted", plain):
                eps = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", plain)
                if eps:
                    rows.append(f"- Latest-quarter Diluted EPS: ${float(eps.group(1).replace(',', '')):,.2f} [release line {line_no:05d}]")
        if not rows:
            return ["Quarterly revenue and diluted EPS were unavailable in the selected release lines."]
        unit_line = next(((i + 1, re.sub(r"^\d{5}:\s*", "", line).strip())
                          for i, line in enumerate(numbered)
                          if re.search(r"dollars in (?:millions|thousands)|amounts in (?:millions|thousands)|per share data", line, re.I)), None)
        if unit_line:
            line_no, text = unit_line
            rows.insert(0, f"- Release statement unit context: {text} [release line {line_no:05d}]")
        return rows

    def _canonical_report(self, corrections: dict[str, str]) -> str:
        """Render one clean section per role after the Manager's review."""
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
            return ""

        def combine(*chunks: str) -> str:
            return "\n\n".join(chunk.strip() for chunk in chunks if chunk and chunk.strip())

        # Build each report part from the matching analyst subsections. A full
        # role response is not a valid substitute for a missing report part.
        overview = combine(
            section(research, "Business Model"),
        ) or "The Research Analyst did not return a supported business model section."
        positioning = combine(
            section(research, "Growth Evidence"),
            section(research, "Competitive Position"),
            section(research, "Risk Exposure") or section(research, "Risks"),
            section(research, "Scores"),
        ) or "The Research Analyst did not return supported growth, competition, or risk analysis."
        future = combine(
            section(research, "Catalysts"),
            section(research, "Recent Developments"),
        ) or "The Research Analyst did not return supported catalyst or development information."
        future += ("\n\n**Strategic monitoring focus:** Track the disclosed catalysts and risks above against the next reported results. "
                   "This is an analytical monitoring suggestion, not a company forecast.")

        # Use exact SEC fact values and metadata for the financial fact rows.
        # The prose model can then focus on interpretation, while the verifier
        # can compare each reported amount with one saved XBRL record.
        run_folder = Path(self.state.run_path)
        manifest_path = run_folder / "desk_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else {}
        context_facts = manifest.get("facts", self.state.context_json.get("facts", {}))
        values = context_facts.get("values", {})
        tags = context_facts.get("tags", {})
        units = context_facts.get("units", {})
        metric_labels = {
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
        fact_rows = ["### Annual Facts and Ratios"]
        for metric, label in metric_labels.items():
            record = values.get(metric, {}).get("current")
            if not isinstance(record, dict):
                continue
            raw_value = float(record.get("val", 0))
            unit = str(units.get(metric, ""))
            tag = str(tags.get(metric, ""))
            accession = str(record.get("accn", ""))
            period_end = str(record.get("end", ""))
            if unit.casefold() == "usd/shares":
                rendered = f"${raw_value:,.2f}"
            elif unit.upper().startswith("USD"):
                rendered = f"${raw_value:,.2f}" if not raw_value.is_integer() else f"${raw_value:,.0f}"
            else:
                rendered = f"{raw_value:,.2f}" if not raw_value.is_integer() else f"{raw_value:,.0f}"
            fact_rows.append(
                f"- **{label}**: {rendered} [filing accession: {accession}, tag: {tag}, period-end: {period_end}]"
            )
        fact_rows.append("- Calculator ratios, arithmetic, quarter figures, and peer comparisons are listed in Source-linked desk data.")
        financial = re.sub(
            r"(?ims)^#{1,6}\s+Annual Facts and Ratios(?:\s+\([^\n]*\))?\s*$[\s\S]*?(?=^#{1,6}\s|\Z)",
            "\n".join(fact_rows) + "\n\n",
            financial,
            count=1,
        )
        quarter_block = "### Latest Quarter Revenue and Diluted EPS\n\n" + "\n".join(self._release_quarter_rows(manifest, run_folder))
        financial = re.sub(
            r"(?ims)^#{1,6}\s+Latest Quarter Revenue and Diluted EPS\s*$[\s\S]*?(?=^#{1,6}\s|\Z)",
            quarter_block + "\n\n",
            financial,
            count=1,
        )
        parts = {
            "Overview": overview,
            "Market Positioning and Growth Outlook": positioning,
            "Valuation Insights": re.sub(r'(?m)^##\s+', '### ', financial) if financial else "The financial analyst did not return a supported section.",
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
    def _cited_lines(report: str, texts: dict[str, str], release_filename: str = "earnings_release_exhibit_99_1.txt") -> dict[str, list[str]]:
        cited: dict[str, list[str]] = {}
        pattern = re.compile(r"\[(10-K|10-Q|8-K|release) line (\d{5})\]", re.I)
        mapping = {"10-K": "10k.txt", "10-Q": "10q.txt", "8-K": "earnings_8k.txt", "release": release_filename}
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
            "release": facts.get("release_filename") or "earnings_release_exhibit_99_1.txt",
        }
        opening_figures = financial_figures(str(facts.get("release_opening_paragraph", "")))
        for line in auditable.splitlines():
            claim = line.strip()
            if not re.match(r"(?i)^Insight:", claim):
                continue
            citation = citation_re.search(claim)
            if not citation:
                checked.append({"claim": claim, "status": "unsupported", "reason": "Insight has no zero-padded filing-line citation.", "correction": "Select a filing-supported Insight with its exact line.", "source": ""})
                checked_claims.add(claim.casefold())
                continue
            filing, line_no = citation.groups()
            if financial_figures(claim) & opening_figures:
                checked.append({"claim": claim, "status": "wrong", "reason": "Insight repeats a financial figure from the earnings release opening paragraph.", "correction": "Replace it with a different source-supported filing claim.", "source": f"release opening paragraph: {facts.get('release_opening_paragraph', '')}"})
                checked_claims.add(claim.casefold())
                continue
            source_lines = texts.get(filing_for_form[filing.casefold()], "").splitlines()
            source_line = source_lines[int(line_no) - 1] if 0 < int(line_no) <= len(source_lines) else ""
            if not source_line.startswith(f"{int(line_no):05d}:"):
                checked.append({"claim": claim, "status": "unsupported", "reason": "Insight citation is not a line in the saved filing text.", "correction": "Use an existing numbered line from the saved filing.", "source": source_line})
                checked_claims.add(claim.casefold())
                continue

        # A verbatim quotation can be relocated only when it matches exactly
        # one saved line. This corrects citation offsets without inventing text.
        for line in auditable.splitlines():
            claim = line.strip()
            if not claim.lower().startswith('insight:'):
                continue
            cite = citation_re.search(claim)
            quote = re.search(r'["“]([^"”]{30,})["”]', claim)
            if not cite or not quote:
                continue
            source = texts.get(filing_for_form[cite.group(1).lower()], '')
            normalized_quote = re.sub(r'\s+', ' ', quote.group(1)).strip().casefold()
            if normalized_quote.endswith(('...', '…')):
                normalized_quote = normalized_quote.rstrip('.…').rstrip()
            matches = [saved for saved in source.splitlines() if normalized_quote in re.sub(r'\s+', ' ', saved).casefold()]
            if len(matches) != 1:
                continue
            number = re.match(r'^(\d{5}):', matches[0])
            if number and number.group(1) != cite.group(2):
                replacement = claim[:cite.start()] + f'[{cite.group(1)} line {number.group(1)}]' + claim[cite.end():]
                checked.append({'claim': claim, 'status': 'wrong', 'reason': 'The quoted text appears on a different saved filing line.', 'correction': f'Use {cite.group(1)} line {number.group(1)}.', 'source': matches[0], 'replacement_claim': replacement})
                checked_claims.add(claim.casefold())

        def cells(row: str) -> list[str]:
            return [x.strip() for x in row.strip().strip("|").split("|")]

        def numeric(value: str) -> float | None:
            match = re.search(r"(?<![\w.])(-?\$?\(?[\d,]+(?:\.\d+)?\)?)", value)
            if not match:
                return None
            try:
                token = match.group(1).replace("$", "").replace(",", "")
                if token.startswith("(") and token.endswith(")"):
                    return -float(token[1:-1])
                return float(token)
            except ValueError:
                return None

        def arithmetic(expression: str) -> float:
            return safe_arithmetic(expression)

        def ticker_in_line(ticker: str, line: str) -> bool:
            return bool(re.search(r"(?<![A-Z0-9])" + re.escape(str(ticker).upper()) + r"(?![A-Z0-9])", line.upper()))

        release_text = texts.get(facts.get("release_filename") or "earnings_release_exhibit_99_1.txt", "")
        if not release_text:
            release_text = texts.get("earnings_release_exhibit_99.txt", "")
        release_lines = release_text.splitlines()
        release_multiplier = (1_000_000 if re.search(r"dollars in millions|amounts in millions", release_text, re.I)
                              else 1_000 if re.search(r"dollars in thousands|amounts in thousands", release_text, re.I) else 1)
        for line in auditable.splitlines():
            label = line.casefold()
            if "latest-quarter total revenue" not in label and "latest-quarter diluted eps" not in label:
                continue
            claim = line.strip()
            if claim.casefold() in checked_claims:
                continue
            citation = citation_re.search(line)
            line_no = int(citation.group(2)) if citation and citation.group(1).casefold() == "release" else 0
            source_line = release_lines[line_no - 1] if 0 < line_no <= len(release_lines) else ""
            reported = numeric(line[:citation.start()] if citation else line)
            if "latest-quarter total revenue" in label:
                expected = release_money_amount(re.sub(r"^\d{5}:\s*", "", source_line), release_multiplier) if source_line else None
                unit = re.search(r"\b(billion|million|thousand)\b", line, re.I)
                factor = {"billion": 1_000_000_000, "million": 1_000_000, "thousand": 1_000}.get(unit.group(1).casefold(), 1) if unit else 1
                value_ok = reported is not None and expected is not None and abs(reported * factor - expected) <= 0.01
                description = "Quarter revenue matches the selected release line and its stated unit." if value_ok else "Quarter revenue does not match the selected release line or its stated unit."
            else:
                expected_match = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", source_line, re.I) if source_line else None
                expected = float(expected_match.group(1).replace(",", "")) if expected_match else None
                value_ok = reported is not None and expected is not None and abs(reported - expected) <= 0.005
                description = "Quarter diluted EPS matches the selected release line." if value_ok else "Quarter diluted EPS does not match the selected release line."
            status = "correct" if value_ok else "wrong" if source_line else "unsupported"
            checked.append({"claim": claim, "status": status, "reason": description,
                            "correction": "" if value_ok else source_line,
                            "source": f"release line {line_no:05d}" if source_line else ""})
            checked_claims.add(claim.casefold())

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
        release_name = facts.get("release_filename") or "earnings_release_exhibit_99_1.txt"
        if release_name not in texts and "earnings_release_exhibit_99.txt" in texts:
            release_name = "earnings_release_exhibit_99.txt"
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
            expected_number = None
            if selected and is_revenue:
                expected_number = release_money_amount(selected, default_multiplier=release_unit_factor)
            elif selected and is_eps:
                eps_match = re.search(r"\$\s*([\d,]+(?:\.\d+)?)", selected)
                expected_number = float(eps_match.group(1).replace(",", "")) if eps_match else None
            cite = citation_re.search(line)
            cited_line = int(cite.group(2)) if cite and cite.group(1).casefold() == "release" else 0
            actual_source = release_lines[cited_line - 1] if 0 < cited_line <= len(release_lines) else ""
            selected_line_no = 0
            if selected:
                selected_clean = re.sub(r"^\d{5}:\s*", "", selected).strip().casefold()
                selected_line_no = next((i + 1 for i, x in enumerate(release_lines) if re.sub(r"^\d{5}:\s*", "", x).strip().casefold() == selected_clean), 0)
            reported_text = row.group(3).split("[", 1)[0]
            if expected_number is not None and is_revenue:
                expected_absolute = expected_number
                reported_absolute = release_money_amount(reported_text)
                amount_ok = reported_absolute is not None and abs(reported_absolute - expected_absolute) <= max(0.01, abs(expected_absolute) * 1e-9)
                display_value = format_release_money(expected_absolute)
            else:
                expected_absolute = expected_number
                reported = numeric(reported_text)
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
                accession = str((facts.get("values", {}).get("diluted_eps", {}).get("current") or {}).get("accn", ""))
                correction = f"Use ${expected_eps:.2f} diluted EPS [10-K line {line_no:05d}; accession {accession}]."
                replacement_claim = line[:claim_eps.start(1)] + f"{expected_eps:.2f}" + line[claim_eps.end(1):]
            claim = line.strip()
            checked.append({"claim": claim, "status": status, "reason": reason, "correction": correction,
                            "source": f"10-K line {line_no:05d}; {saved_line}; {(facts.get('values', {}).get('diluted_eps', {}).get('current') or {}).get('accn', '')}",
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
            accession = str((facts.get("values", {}).get("revenue", {}).get("current") or {}).get("accn", ""))
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
            if formula_expression:
                try:
                    formula_value = safe_arithmetic(formula_expression)
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
                line_peer = next((p for p in facts.get("peers", []) if p.get("ticker") and ticker_in_line(p.get("ticker"), line)), None)
                target_peer = line_peer or (next((p for p in facts.get("peers", []) if str(p.get("ticker", "")).upper() == active_peer), None) if peer_section and active_peer else None)
                target_ttm = target_peer.get("ttm", {}) if target_peer else facts.get("ttm", {})
                if "ttm revenue" in label and target_ttm.get("available"):
                    source = target_ttm.get("revenue_source", {})
                    annual, current_ytd, prior_ytd = source.get("annual"), source.get("current_ytd"), source.get("prior_ytd")
                    expected_expression = (f"{annual['val']} + {current_ytd['val']} - {prior_ytd['val']}" if annual and current_ytd and prior_ytd else f"{source.get('val')}")
                elif "ttm operating income" in label and target_ttm.get("available"):
                    source = target_ttm.get("operating_income_source", {})
                    annual, current_ytd, prior_ytd = source.get("annual"), source.get("current_ytd"), source.get("prior_ytd")
                    expected_expression = (f"{annual['val']} + {current_ytd['val']} - {prior_ytd['val']}" if annual and current_ytd and prior_ytd else f"{source.get('val')}")
                if target_peer and "ttm operating margin" in label:
                    ttm = target_peer.get("ttm", {})
                    if ttm.get("available"):
                        expected_expression = f"{ttm.get('operating_income')} / {ttm.get('revenue')}"
                elif target_peer and "operating margin" in label:
                    peer = target_peer
                    bundle = peer.get("facts", {}) if peer else {}
                    op = (bundle.get("values", {}).get("operating_income", {}).get("current") or {}).get("val")
                    rev = (bundle.get("values", {}).get("revenue", {}).get("current") or {}).get("val")
                    if op is not None and rev:
                        expected_expression = f"{op} / {rev}"
                else:
                    vals = facts.get("values", {})
                    getval = lambda metric, period="current": (vals.get(metric, {}).get(period) or {}).get("val")
                    rev, prior_rev = getval("revenue"), getval("revenue", "prior")
                    op, net = getval("operating_income"), getval("net_income")
                    eq, prior_eq = getval("equity"), getval("equity", "prior")
                    ltd, cur = getval("long_term_debt"), getval("current_debt")
                    cfo, capex, eps = getval("cash_from_operations"), getval("capex"), getval("diluted_eps")
                    price = facts.get("share_price_input")
                    if "ttm operating margin" in label and facts.get("ttm", {}).get("available"):
                        ttm = facts["ttm"]
                        expected_expression = f"{ttm['operating_income']} / {ttm['revenue']}"
                    elif "revenue growth" in label and rev is not None and prior_rev:
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
        deterministic_claims = {str(item.get("claim", "")).strip().casefold() for item in checked}
        for line in auditable.splitlines():
            if not line.strip().startswith("|"):
                continue
            row = cells(line)
            if len(row) < 3 or set(row[0]) <= {"-", ":"}:
                continue
            claim = line.strip()
            if claim.casefold() in checked_claims:
                continue
            if "peer ttm median operating margin" in line.casefold():
                aligned = facts.get("ttm", {})
                alignment = facts.get("persona_calculations", {})
                anchor = aligned.get("period_end")
                window = int(alignment.get("peer_alignment_window_days", 45))
                aligned_values = []
                for item in facts.get("peers", []):
                    ttm = item.get("ttm", {})
                    try:
                        lag = abs((date.fromisoformat(anchor) - date.fromisoformat(ttm.get("period_end"))).days)
                    except (TypeError, ValueError):
                        continue
                    if ttm.get("available") and lag <= window:
                        aligned_values.append(float(ttm["margin"]))
                expected = median(aligned_values) if aligned_values else None
                reported = numeric(row[1]) if len(row) > 1 else None
                valid = expected is not None and reported is not None and abs(reported / 100 - expected) <= 0.00005
                checked.append({"claim": claim, "status": "correct" if valid else "wrong" if expected is not None else "unsupported",
                                "reason": "Median TTM operating margin matches peer TTM facts inside the saved period window." if valid else "The median does not match the aligned peer TTM facts or the aligned peer set is empty.",
                                "correction": "" if valid else (f"Use {expected:.2%} from {len(aligned_values)} aligned peer TTM margins." if expected is not None else "No aligned peer TTM facts are available."),
                                "source": f"saved company and peer TTM facts; anchor {anchor}; window {window} days"})
                checked_claims.add(claim.casefold())
                continue
            peer = next((x for x in facts.get("peers", []) if x.get("ticker") and ticker_in_line(x.get("ticker"), line)), None)
            data_bundle = peer.get("facts", {}) if peer else facts
            available_tags = sorted((known for known in data_bundle.get("tags", {}).values() if known), key=len, reverse=True)
            tag = next((known for known in available_tags if known in line), None)
            if tag and " ttm " not in line.casefold():
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
                    computed = safe_arithmetic(lhs)
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
                release_lines = texts.get(facts.get("release_filename") or "earnings_release_exhibit_99_1.txt", "").splitlines()
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
                peer_ttm = peer.get("ttm", {})
                expected = peer_ttm.get("margin")
                ok = shown is not None and expected is not None and abs(shown / 100 - float(expected)) <= 0.00005
                checked.append({"claim": claim, "status": "correct" if ok else "wrong" if expected is not None else "unsupported",
                                "reason": "Peer TTM margin matches TTM operating income divided by TTM revenue from its saved facts." if ok else "Peer margin does not match the saved TTM facts.",
                                "correction": "" if ok else (f"Use {expected:.2%} for {peer_ttm.get('period_start')} to {peer_ttm.get('period_end')} ({peer_ttm.get('basis')})." if expected is not None else "No saved peer TTM margin is available."),
                                "source": f"{peer.get('ticker')} TTM facts; {peer_ttm.get('period_start')} to {peer_ttm.get('period_end')}; {peer_ttm.get('basis')}"})
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
                def normalized_claim(value: str) -> str:
                    value = re.sub(r"\[[^\]]+\]", " ", value)
                    value = re.sub(r"[`*_#|]", " ", value)
                    value = re.sub(r"[^a-zA-Z0-9]+", " ", value).casefold()
                    return re.sub(r"\s+", " ", value).strip()
                normalized_report = normalized_claim(auditable)
                normalized_candidate = normalized_claim(claim)
                # The model can copy a factual sentence but omit its adjacent
                # citation. The actual report line is checked below, so do not
                # add a second unsupported mark for that paraphrase.
                stopwords = {"a", "an", "and", "are", "as", "at", "by", "for", "from", "in", "is", "it", "of", "on", "or", "the", "this", "to", "was", "were", "with"}
                candidate_terms = {word for word in normalized_candidate.split() if word not in stopwords}
                report_terms = set(normalized_report.split())
                overlap = len(candidate_terms & report_terms) / len(candidate_terms) if candidate_terms else 0
                if normalized_candidate and (normalized_candidate in normalized_report or overlap >= 0.8):
                    continue
                mark["status"] = "unsupported"
                mark["reason"] = "The Verifier returned a claim that does not appear in the compiled report."
                checked.append(mark)
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
        # Add deterministic unsupported marks for numeric report claims without
        # a verifier result. Ignore only calendar/year and fiscal-quarter labels.
        for line in auditable.splitlines():
            if line.strip().casefold() in checked_claims:
                continue
            if re.match(r"(?i)^\s*Run time:", line):
                continue
            if re.search(r"Filing Accession:", line, re.I):
                continue
            if re.match(r"(?i)^\s*Aligned trailing-12-month peer data\b", line):
                continue
            if re.match(r"(?i)^\s*Research Analyst scores:", line):
                scores = facts.get("research_scores", {})
                expected = [scores.get("growth_evidence"), scores.get("competitive_position"), scores.get("risk_exposure")]
                reported = [int(x) for x in re.findall(r"(?<!\d)([1-5])\s*/\s*5", line)]
                status = "correct" if len(expected) == 3 and reported == expected else "wrong"
                checked.append({"claim": line.strip(), "status": status,
                                "reason": "Research Analyst judgment scores match the saved role output." if status == "correct" else "Scores do not match the saved Research Analyst output.",
                                "correction": "" if status == "correct" else f"Use the saved Research Analyst scores: {expected}.",
                                "source": "saved Research Analyst role output"})
                checked_claims.add(line.strip().casefold())
                continue
            if re.match(r"(?i)^\s*Financial Analyst scores:", line):
                expected = facts.get("persona_calculations", {}).get("financial_scores", {})
                keys = {"cash flow support": "cash_flow_support", "operating margin trend": "operating_margin_trend",
                        "debt trend": "debt_trend", "peer comparison": "peer_comparison"}
                reported = {key: int(value) for label, value in re.findall(r"([A-Za-z ]+)\s*=\s*([1-3])", line)
                            if (key := keys.get(label.strip().casefold()))}
                status = "correct" if reported == expected else "wrong"
                checked.append({"claim": line.strip(), "status": status,
                                "reason": "Financial Analyst scores match the saved calculator results." if status == "correct" else "Scores do not match the saved calculator results.",
                                "correction": "" if status == "correct" else f"Use the saved financial scores: {expected}.",
                                "source": "saved persona_calculations.financial_scores"})
                checked_claims.add(line.strip().casefold())
                continue
            research_score_keys = {"growth evidence": "growth_evidence", "competitive position": "competitive_position",
                                   "risk exposure": "risk_exposure"}
            financial_score_keys = {"cash flow support": "cash_flow_support", "operating margin trend": "operating_margin_trend",
                                    "debt trend": "debt_trend", "peer comparison": "peer_comparison"}
            score_label = score_value = None
            score_match = re.match(r"(?i)^\s*(?:[-*]\s*)?\*\*([^*]+?)\s*:\s*(\d+)\*\*", line)
            if not score_match:
                score_match = re.match(r"(?i)^\s*(?:[-*]\s*)?\*\*([^*]+)\*\*\s*:\s*(\d+)\b", line)
            if score_match:
                score_label, score_value = score_match.group(1).strip().casefold(), int(score_match.group(2))
                score_label = re.sub(r"\s+score$", "", score_label)
            elif line.strip().startswith("|"):
                score_row = cells(line)
                if len(score_row) >= 3 and score_row[0].casefold() in research_score_keys | financial_score_keys:
                    try:
                        score_label, score_value = score_row[0].casefold(), int(score_row[1])
                    except ValueError:
                        score_label = None
            if score_label in research_score_keys:
                expected = facts.get("research_scores", {}).get(research_score_keys[score_label])
                status = "correct" if expected is not None and score_value == expected else "wrong" if expected is not None else "unsupported"
                checked.append({"claim": line.strip(), "status": status,
                                "reason": "Research score matches the saved Research Analyst output." if status == "correct" else "Research score does not match the saved output." if status == "wrong" else "No Research Analyst score is available for this criterion.",
                                "correction": "" if status == "correct" else (str(expected) if expected is not None else "Report insufficient evidence."),
                                "source": f"saved Research Analyst output: {research_score_keys[score_label]}"})
                checked_claims.add(line.strip().casefold())
                continue
            if score_label in financial_score_keys:
                expected = facts.get("persona_calculations", {}).get("financial_scores", {}).get(financial_score_keys[score_label])
                status = "correct" if expected is not None and score_value == expected else "wrong" if expected is not None else "unsupported"
                checked.append({"claim": line.strip(), "status": status,
                                "reason": "Financial score matches the saved calculator result." if status == "correct" else "Financial score does not match the saved calculator result." if status == "wrong" else "No calculator score is available for this criterion.",
                                "correction": "" if status == "correct" else (str(expected) if expected is not None else "Report insufficient evidence."),
                                "source": f"saved persona_calculations.financial_scores: {financial_score_keys[score_label]}"})
                checked_claims.add(line.strip().casefold())
                continue
            claim_without_citations = citation_re.sub("", line)
            numeric_claim = re.sub(r"\b(?:FY\s*20\d{2}|Q[1-4]|20\d{2})\b", "", claim_without_citations, flags=re.I)
            persona = facts.get("persona_calculations", {})
            company_ttm = persona.get("company_ttm", {})
            company_ttm_margin = persona.get("peer_company_ttm_margin")
            peer_median = persona.get("peer_median_operating_margin")
            if ("ttm" in claim.casefold() or "trailing 12-month" in claim.casefold()) and "operating margin" in claim.casefold():
                percent_values = [float(value.replace(",", "")) for value in
                                  re.findall(r"(?<![\w.])(-?\d[\d,]*(?:\.\d+)?)\s*%", claim)]
                source = (f"saved persona_calculations.company_ttm {company_ttm.get('period_start')} to "
                          f"{company_ttm.get('period_end')} and aligned peer median; "
                          f"alignment window {persona.get('peer_alignment_window_days')} days")
                expected_values = []
                if isinstance(company_ttm_margin, (int, float)) and not isinstance(company_ttm_margin, bool):
                    expected_values.append(company_ttm_margin * 100)
                if isinstance(peer_median, (int, float)) and not isinstance(peer_median, bool):
                    expected_values.append(peer_median * 100)
                is_peer_median = "median" in claim.casefold() and "peer" in claim.casefold()
                if is_peer_median and len(percent_values) == 1 and isinstance(peer_median, (int, float)):
                    status = "correct" if abs(percent_values[0] - peer_median * 100) <= 0.01 else "wrong"
                    checked.append({"claim": claim, "status": status,
                                    "reason": "TTM peer median matches the saved aligned peer calculation." if status == "correct" else "TTM peer median does not match the saved aligned peer calculation.",
                                    "correction": "" if status == "correct" else f"Use {peer_median * 100:.2f}% for the aligned TTM peer median.",
                                    "source": source, "deterministic_check": True})
                    checked_claims.add(claim.casefold())
                    continue
                if is_peer_median and len(percent_values) >= 2 and len(expected_values) == 2:
                    values_match = all(abs(actual - expected) <= 0.01 for actual, expected in zip(percent_values[:2], expected_values))
                    comparison = persona.get("peer_margin_comparison")
                    direction_matches = (comparison in {"above", "below", "equal"}
                                         and re.search(r"\b" + re.escape(comparison) + r"\b", claim, re.I))
                    status = "correct" if values_match and direction_matches else "wrong"
                    checked.append({"claim": claim, "status": status,
                                    "reason": "Company and peer TTM margins and their direction match the saved aligned calculations." if status == "correct" else "Company or peer TTM margin, or the stated comparison, does not match the saved calculations.",
                                    "correction": "" if status == "correct" else f"Use company {expected_values[0]:.2f}%, peer median {expected_values[1]:.2f}%, comparison {comparison}.",
                                    "source": source, "deterministic_check": True})
                    checked_claims.add(claim.casefold())
                    continue
            if line.strip().startswith("|"):
                row = cells(line)
                if len(row) >= 3 and not set(row[0]) <= {"-", ":"} and re.search(r"\d", numeric_claim):
                    checked.append({"claim": line.strip(), "status": "unsupported", "reason": "Numeric table row did not match a saved fact, cited release line, or checked arithmetic row.", "correction": "Remove or provide a verifiable source and calculation."})
                    checked_claims.add(line.strip().casefold())
                continue
            if re.search(r"\d", numeric_claim):
                has_source = bool(citation_re.search(line) or "[tag:" in line.casefold() or "[filing accession:" in line.casefold() or "[arithmetic:" in line.casefold() or "[calculated from" in line.casefold())
                citations = citation_re.findall(line)
                if citations:
                    cited_sources = []
                    sources_valid = True
                    for form, line_no in citations:
                        source_text = texts.get(filing_for_form[form.casefold()], "")
                        source_line = source_text.splitlines()[int(line_no) - 1] if 0 < int(line_no) <= len(source_text.splitlines()) else ""
                        if not source_line.startswith(f"{int(line_no):05d}:"):
                            sources_valid = False
                            break
                        cited_sources.append(source_line)
                    claim_figures = financial_figures(claim_without_citations)
                    source_figures = set().union(*(financial_figures(x) for x in cited_sources)) if cited_sources else set()
                    def supported_by(figure, available_figures):
                        kind, amount = figure
                        if figure in available_figures:
                            return True
                        if kind == "money":
                            return any((source_kind == kind and abs(source_amount * scale - amount) <= max(0.01, abs(amount) * 1e-8))
                                       for source_kind, source_amount in available_figures for scale in (1_000, 1_000_000, 1_000_000_000))
                        return False
                    def figure_supported(figure):
                        return supported_by(figure, source_figures)
                    if sources_valid and claim_figures and all(figure_supported(x) for x in claim_figures):
                        checked.append({"claim": line.strip(), "status": "correct", "reason": "Every extracted financial figure appears on the cited saved filing lines.", "correction": "", "source": "; ".join(cited_sources)})
                        checked_claims.add(line.strip().casefold())
                        continue
                    if claim_figures:
                        cited_forms = list(dict.fromkeys(form.casefold() for form, _ in citations))
                        cited_numbers = {form.casefold(): [int(number) for cited_form, number in citations if cited_form.casefold() == form.casefold()] for form in cited_forms}
                        corrected_lines = []
                        repairable = True
                        all_source_lines = []
                        for form in cited_forms:
                            filename = filing_for_form[form]
                            all_source_lines.extend((form, index, source_line)
                                                    for index, source_line in enumerate(texts.get(filename, "").splitlines(), 1)
                                                    if source_line.startswith(f"{index:05d}:"))
                        for figure in claim_figures:
                            matches = []
                            for form, index, source_line in all_source_lines:
                                source_figures_for_line = financial_figures(source_line)
                                if supported_by(figure, source_figures_for_line):
                                    matches.append((form, index, source_line))
                            near = [item for item in matches if any(abs(item[1] - cited_no) <= 2 for cited_no in cited_numbers.get(item[0], []))]
                            if len(near) == 1:
                                corrected_lines.append(near[0])
                            elif not near and len(matches) == 1:
                                corrected_lines.append(matches[0])
                            else:
                                repairable = False
                                break
                        unique_corrected = list(dict.fromkeys((form, number, text_line) for form, number, text_line in corrected_lines))
                        if repairable and unique_corrected:
                            corrected_citations = " ".join(f"[{form.upper()} line {number:05d}]" for form, number, _ in unique_corrected)
                            replacement_claim = citation_re.sub("", line.strip()).rstrip() + " " + corrected_citations
                            checked.append({"claim": line.strip(), "status": "wrong", "reason": "The cited line does not state every reported figure; the saved filing identifies a corrected source line.",
                                            "correction": f"Use {corrected_citations}.", "source": "; ".join(item[2] for item in unique_corrected),
                                            "replacement_claim": replacement_claim})
                            checked_claims.add(line.strip().casefold())
                            continue
                reason = "No matching verifier mark was returned for this sourced numeric claim." if has_source else "Numeric claim has no filing-line or XBRL source."
                checked.append({"claim": line.strip(), "status": "unsupported", "reason": reason, "correction": "Remove or source the claim before use."})
                checked_claims.add(line.strip().casefold())
        persona = facts.get("persona_calculations", {})
        comparable_peers = persona.get("comparable_peers", [])
        company_ttm = persona.get("company_ttm", {})
        for mark in checked:
            claim = str(mark.get("claim", ""))
            lowered = claim.casefold()
            if "ttm" in lowered and "operating margin" in lowered:
                percent_values = [float(value.replace(",", "")) for value in
                                  re.findall(r"(?<![\w.])(-?\d[\d,]*(?:\.\d+)?)\s*%", claim)]
                expected_margin = None
                expected_period = ""
                if "median" in lowered and "peer" in lowered:
                    expected_margin = persona.get("peer_median_operating_margin")
                    expected_period = f"aligned peer TTM median; company anchor {company_ttm.get('period_end')}"
                else:
                    for peer in comparable_peers:
                        ticker = str(peer.get("ticker", "")).upper()
                        if ticker and re.search(r"(?<![A-Z0-9])" + re.escape(ticker) + r"(?![A-Z0-9])", claim.upper()):
                            expected_margin = peer.get("margin")
                            expected_period = f"{peer.get('period_start')} to {peer.get('period_end')}; {peer.get('basis')}"
                            break
                if isinstance(expected_margin, (int, float)) and not isinstance(expected_margin, bool) and len(percent_values) == 1:
                    status = "correct" if abs(percent_values[0] - expected_margin * 100) <= 0.01 else "wrong"
                    mark.update({"status": status,
                                 "reason": "TTM peer margin matches the saved XBRL-based calculation." if status == "correct" else "TTM peer margin does not match the saved XBRL-based calculation.",
                                 "correction": "" if status == "correct" else f"Use {expected_margin * 100:.2f}% for {expected_period}.",
                                 "source": f"saved persona_calculations.comparable_peers: {expected_period}",
                                 "deterministic_check": True})
            if str(mark.get("claim", "")).strip().casefold() in deterministic_claims:
                mark["deterministic_check"] = True
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
