#!/usr/bin/env python3
"""Seven-step SEC equity-research data desk for FIN 67110 Lab 02.

Uses only the Python standard library. Reads SEC_USER_AGENT from the local
.env file. It does not read or use API_KEY.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
RUNS = Path(__file__).resolve().parent / "runs"
SEC = "https://www.sec.gov"
DATA = "https://data.sec.gov"

CONCEPTS = {
    "revenue": [
        # Prefer the generic total-revenue concept when dates tie. Some
        # retailers use the following contract tag for net sales only.
        "Revenues",
        "RevenueFromContractWithCustomerExcludingAssessedTax",
        "SalesRevenueNet",
        "SalesRevenueGoodsNet",
        "SalesRevenueServicesNet",
        "RevenueFromContractWithCustomerIncludingAssessedTax",
    ],
    "operating_income": ["OperatingIncomeLoss"],
    "net_income": ["NetIncomeLoss", "ProfitLoss"],
    "diluted_eps": ["EarningsPerShareDiluted"],
    "equity": ["StockholdersEquity", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"],
    "long_term_debt": [
        "LongTermDebtNoncurrent",
        "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
        "LongTermDebt",
    ],
    "current_debt": [
        "LongTermDebtCurrent",
        "LongTermDebtAndFinanceLeaseObligationsCurrent",
        "CurrentPortionOfLongTermDebt",
    ],
    "cash_from_operations": ["NetCashProvidedByUsedInOperatingActivities"],
    "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
}


def read_env(path: Path) -> dict[str, str]:
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


class TextExtractor(HTMLParser):
    """Convert filing HTML to readable, line-numbered plain text."""

    BLOCKS = {"p", "div", "br", "li", "h1", "h2", "h3", "h4"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "ix:header"}:
            self.hidden += 1
        elif not self.hidden and tag == "tr":
            self.parts.append("\n")
        elif not self.hidden and tag in {"td", "th"}:
            self.parts.append(" ")
        elif not self.hidden and tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "ix:header"} and self.hidden:
            self.hidden -= 1
        elif not self.hidden and tag == "tr":
            self.parts.append("\n")
        elif not self.hidden and tag in self.BLOCKS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden:
            self.parts.append(data)


def plain_text(document: bytes | str) -> str:
    source = document.decode("utf-8", errors="replace") if isinstance(document, bytes) else document
    parser = TextExtractor()
    parser.feed(source)
    lines = [re.sub(r"\s+", " ", html.unescape(x)).strip() for x in "".join(parser.parts).splitlines()]
    return "\n".join(line for line in lines if line)


def numbered(text: str) -> str:
    return "\n".join(f"{n:05d}: {line}" for n, line in enumerate(text.splitlines(), 1))


def sec_get(url: str, user_agent: str, *, retries: int = 4) -> bytes:
    request = Request(url, headers={"User-Agent": user_agent})
    for attempt in range(retries):
        try:
            with urlopen(request, timeout=40) as response:
                body = response.read()
            return body
        except HTTPError as exc:
            if exc.code in (403, 429, 503) and attempt + 1 < retries:
                time.sleep(2 ** (attempt + 1))
                continue
            raise RuntimeError(f"SEC returned HTTP {exc.code} for {url}") from exc
        except (URLError, TimeoutError) as exc:
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
                continue
            raise RuntimeError(f"SEC request failed for {url}: {exc}") from exc
    raise RuntimeError(f"SEC request failed for {url}")


def sec_json(url: str, user_agent: str) -> dict:
    return json.loads(sec_get(url, user_agent))


def cik_for(ticker: str, user_agent: str) -> tuple[str, str]:
    records = sec_json(f"{SEC}/files/company_tickers.json", user_agent)
    ticker = ticker.upper().strip()
    for row in records.values():
        if row.get("ticker", "").upper() == ticker:
            return str(row["cik_str"]).zfill(10), row["title"]
    raise ValueError(f"Ticker not found in SEC company_tickers.json: {ticker}")


def recent_filings(submissions: dict) -> list[dict]:
    recent = submissions.get("filings", {}).get("recent", {})
    count = len(recent.get("form", []))
    return [{k: recent[k][i] for k in recent} for i in range(count)]


def accession_url(cik: str, accession: str, document: str) -> str:
    return f"{SEC}/Archives/edgar/data/{int(cik)}/{accession.replace('-', '')}/{quote(document)}"


def filing_text(cik: str, row: dict, user_agent: str) -> str:
    raw = sec_get(accession_url(cik, row["accessionNumber"], row["primaryDocument"]), user_agent)
    return plain_text(raw)


def select_filings(cik: str, submissions: dict, user_agent: str) -> dict[str, dict]:
    rows = recent_filings(submissions)
    latest: dict[str, dict] = {}
    for row in rows:
        form = row.get("form", "")
        if form in ("10-K", "10-K/A") and "10k" not in latest:
            latest["10k"] = row
        elif form in ("10-Q", "10-Q/A") and "10q" not in latest:
            latest["10q"] = row
    for row in rows:
        if row.get("form") not in ("8-K", "8-K/A"):
            continue
        text = filing_text(cik, row, user_agent)
        if re.search(r"item\s+2[.]02\b", text, flags=re.IGNORECASE):
            latest["earnings_8k"] = row
            latest["earnings_8k_text"] = text  # type: ignore[assignment]
            break
    missing = {k for k in ("10k", "10q", "earnings_8k") if k not in latest}
    if missing:
        raise RuntimeError(f"Could not identify required latest filing(s): {', '.join(sorted(missing))}")
    return latest


def index_documents(cik: str, row: dict, user_agent: str) -> list[dict]:
    url = accession_url(cik, row["accessionNumber"], "index.json")
    index = sec_json(url, user_agent)
    return index.get("directory", {}).get("item", [])


def locate_exhibit(cik: str, row: dict, user_agent: str) -> str:
    items = index_documents(cik, row, user_agent)
    candidates = [x["name"] for x in items if x.get("name", "").lower().endswith((".htm", ".html"))]
    for name in candidates:
        if re.search(r"ex(?:hibit)?[\s_-]*99[._-]?1|ex991", name, flags=re.IGNORECASE):
            return name
    for name in candidates:
        if re.search(r"earnings.?release|press.?release", name, flags=re.IGNORECASE):
            return name
    # Index descriptions are sometimes more useful than document filenames.
    for item in items:
        description = item.get("description", "")
        if re.search(r"exhibit\s*99[.]1", description, flags=re.IGNORECASE):
            return item["name"]
    raise RuntimeError("The selected earnings 8-K has no identifiable Exhibit 99.1 in its index")


def accepted(row: dict) -> str:
    return row.get("acceptanceDateTime") or f"{row.get('filingDate', '')} (acceptance time unavailable)"


def run_folder(company: str) -> Path:
    stamp = datetime.now().astimezone().strftime("%Y%m%d_%H%M%S_%Z")
    path = RUNS / f"{re.sub(r'[^A-Za-z0-9._-]+', '_', company)}_{stamp}"
    path.mkdir(parents=True, exist_ok=False)
    return path


def fact_entries(companyfacts: dict, tags: list[str], unit: str, fiscal_end: str | None = None) -> tuple[str, dict] | None:
    facts = companyfacts.get("facts", {}).get("us-gaap", {})
    choices = []
    for tag in tags:
        concept = facts.get(tag)
        if not concept:
            continue
        units = concept.get("units", {})
        unit_name = unit if unit in units else next(iter(units), None)
        if not unit_name:
            continue
        entries = units[unit_name]
        valid = []
        for entry in entries:
            form = entry.get("form", "")
            if form not in ("10-K", "10-K/A"):
                continue
            end = entry.get("end", "")
            if fiscal_end and end != fiscal_end:
                continue
            start = entry.get("start")
            if start:
                try:
                    days = (datetime.fromisoformat(end) - datetime.fromisoformat(start)).days
                except ValueError:
                    continue
                if not 330 <= days <= 400:
                    continue
            valid.append(entry)
        if valid:
            choices.append((max(x["end"] for x in valid), tag, unit_name, valid))
    if not choices:
        return None
    newest = max(x[0] for x in choices)
    _, tag, unit_name, entries = next(x for x in choices if x[0] == newest)
    entries.sort(key=lambda x: (x.get("filed", ""), x.get("accn", "")))
    by_end: dict[str, dict] = {}
    for item in entries:
        by_end[item["end"]] = item
    return tag, {"unit": unit_name, "by_end": by_end}


def build_company_facts(cik: str, user_agent: str, folder: Path, ticker: str) -> dict:
    facts = sec_json(f"{DATA}/api/xbrl/companyfacts/CIK{cik}.json", user_agent)
    facts_path = folder / f"{ticker}_companyfacts.json"
    facts_path.write_text(json.dumps(facts, indent=2), encoding="utf-8")
    revenue = fact_entries(facts, CONCEPTS["revenue"], "USD")
    if not revenue:
        raise RuntimeError(f"No annual revenue fact found for {ticker}")
    _, initial_revenue_series = revenue
    fiscal_end = max(initial_revenue_series["by_end"])
    revenue = fact_entries(facts, CONCEPTS["revenue"], "USD", fiscal_end=fiscal_end)
    if not revenue:
        raise RuntimeError(f"No annual revenue fact found for {ticker} at {fiscal_end}")
    revenue_tag, revenue_series = revenue
    previous_ends = [end for end in revenue_series["by_end"] if end < fiscal_end]
    previous_end = max(previous_ends) if previous_ends else None
    values = {}
    tags = {"revenue": revenue_tag}
    units = {"revenue": revenue_series["unit"]}
    values["revenue"] = {"current": revenue_series["by_end"].get(fiscal_end), "prior": revenue_series["by_end"].get(previous_end) if previous_end else None}
    for metric, candidates in CONCEPTS.items():
        if metric == "revenue":
            continue
        unit = "USD/shares" if metric == "diluted_eps" else "USD"
        chosen = fact_entries(facts, candidates, unit)
        if not chosen:
            values[metric] = {"current": None, "prior": None}
            continue
        tag, series = chosen
        tags[metric] = tag
        units[metric] = series["unit"]
        metric_ends = sorted(end for end in series["by_end"] if end < fiscal_end)
        prior = metric_ends[-1] if metric_ends else None
        values[metric] = {"current": series["by_end"].get(fiscal_end), "prior": series["by_end"].get(prior) if prior else None}
    return {"ticker": ticker, "cik": cik, "fiscal_end": fiscal_end, "values": values, "tags": tags, "units": units, "all_facts_path": str(facts_path)}


def num(record: dict | None) -> float | None:
    if record is None:
        return None
    try:
        return float(record["val"])
    except (KeyError, TypeError, ValueError):
        return None


def source(record: dict | None, tag: str, unit: str) -> str:
    if not record:
        return "unavailable"
    return f"{tag}, {record.get('end', '?')}, {record.get('form', '?')} filed {record.get('filed', '?')} accession {record.get('accn', '?')} [{unit}]"


def display_fact(name: str, bundle: dict, *, prior: bool = True) -> None:
    item = bundle["values"].get(name, {})
    tag = bundle["tags"].get(name, "not found")
    unit = bundle["units"].get(name, "unknown unit")
    current, old = item.get("current"), item.get("prior")
    if current:
        print(f"  {name}: {current['val']} | {source(current, tag, unit)}")
        if prior and old:
            print(f"    prior: {old['val']} | {source(old, tag, unit)}")
    else:
        print(f"  {name}: unavailable | candidate tag(s): {', '.join(CONCEPTS[name])}")


def calculate(bundle: dict, price: float | None) -> dict[str, float | None]:
    v = bundle["values"]
    current = {key: num(v.get(key, {}).get("current")) for key in v}
    prior = {key: num(v.get(key, {}).get("prior")) for key in v}
    revenue, previous_revenue = current.get("revenue"), prior.get("revenue")
    operating, income = current.get("operating_income"), current.get("net_income")
    equity, prior_equity = current.get("equity"), prior.get("equity")
    ltd, current_debt = current.get("long_term_debt"), current.get("current_debt")
    cfo, capex = current.get("cash_from_operations"), current.get("capex")
    eps = current.get("diluted_eps")
    avg_eq = (equity + prior_equity) / 2 if equity is not None and prior_equity is not None else None
    total_debt = ltd + current_debt if ltd is not None and current_debt is not None else None
    return {
        "revenue_growth": (revenue / previous_revenue - 1) if revenue is not None and previous_revenue not in (None, 0) else None,
        "operating_margin": operating / revenue if operating is not None and revenue not in (None, 0) else None,
        "return_on_average_equity": income / avg_eq if income is not None and avg_eq not in (None, 0) else None,
        "debt_to_equity": total_debt / equity if total_debt is not None and equity not in (None, 0) else None,
        "free_cash_flow": cfo - capex if cfo is not None and capex is not None else None,
        "pe": price / eps if price is not None and eps not in (None, 0) else None,
    }


def print_calculations(bundle: dict, price: float | None) -> dict:
    m = bundle["values"]
    get = lambda k, p="current": num(m.get(k, {}).get(p))
    revenue, prior_revenue = get("revenue"), get("revenue", "prior")
    operating, net = get("operating_income"), get("net_income")
    equity, prior_equity = get("equity"), get("equity", "prior")
    long_debt, current_debt = get("long_term_debt"), get("current_debt")
    cfo, capex, eps = get("cash_from_operations"), get("capex"), get("diluted_eps")
    avg_equity = (equity + prior_equity) / 2 if equity is not None and prior_equity is not None else None
    debt = long_debt + current_debt if long_debt is not None and current_debt is not None else None
    calcs = calculate(bundle, price)
    print("  Revenue growth: ", f"({revenue} / {prior_revenue}) - 1 = {calcs['revenue_growth']:.2%}" if calcs["revenue_growth"] is not None else "unavailable (need current and prior revenue)")
    print("  Operating margin: ", f"{operating} / {revenue} = {calcs['operating_margin']:.2%}" if calcs["operating_margin"] is not None else "unavailable")
    print("  Return on average equity: ", f"{net} / (({equity} + {prior_equity}) / 2) = {calcs['return_on_average_equity']:.2%}" if calcs["return_on_average_equity"] is not None else "unavailable")
    print("  Debt/equity: ", f"({long_debt} + {current_debt}) / {equity} = {calcs['debt_to_equity']:.2%}" if calcs["debt_to_equity"] is not None else "unavailable (need long-term debt and current portion)")
    print("  Free cash flow: ", f"{cfo} - {capex} = {calcs['free_cash_flow']:,.0f}" if calcs["free_cash_flow"] is not None else "unavailable")
    if price is not None:
        print("  P/E: ", f"{price} / {eps} = {calcs['pe']:.2f}" if calcs["pe"] is not None else "unavailable")
    return calcs


def release_lines(text: str) -> list[str]:
    lines = text.splitlines()
    revenue = next((line for line in lines if re.search(r"^total\s+revenues?\s+[$0-9(]", line, flags=re.I)), None)
    diluted = next((line for line in lines if re.search(r"^diluted\b.*(?:share|eps).*\s[$0-9(]", line, flags=re.I)), None)
    if not diluted:
        for index, line in enumerate(lines):
            if re.search(r"net\s+income\s+per\s+common\s+share", line, flags=re.I):
                diluted = next((candidate for candidate in lines[index + 1:index + 5] if re.search(r"^diluted\s+[$0-9(]", candidate, flags=re.I)), None)
                break
    return [line for line in (revenue, diluted) if line]


def accession_summary(row: dict) -> str:
    return f"{row['form']} accession {row['accessionNumber']} accepted {accepted(row)}"


def run_ticker(ticker: str, peers: list[str], price: float | None, only_step: int | None, user_agent: str) -> Path:
    ticker = ticker.upper()
    print(f"\n=== {ticker} ===")
    cik, company = cik_for(ticker, user_agent)
    if only_step in (None, 1):
        print("Step 1 — Resolve ticker to CIK")
        print(f"  {ticker} -> CIK {cik} -> {company}")
    if only_step == 1:
        return RUNS

    submissions = sec_json(f"{DATA}/submissions/CIK{cik}.json", user_agent)
    filings = select_filings(cik, submissions, user_agent)
    if only_step in (None, 2):
        print("Step 2 — Select latest filings and earnings 8-K")
        for key in ("10k", "10q", "earnings_8k"):
            print(f"  {accession_summary(filings[key])}")
    if only_step == 2:
        return RUNS

    if only_step in (None, 3):
        print("Step 3 — Save filing text and Exhibit 99.1")
    folder = run_folder(company)
    for key, label in (("10k", "10k"), ("10q", "10q"), ("earnings_8k", "earnings_8k")):
        row = filings[key]
        text = filings.get("earnings_8k_text") if key == "earnings_8k" else filing_text(cik, row, user_agent)
        (folder / f"{label}.txt").write_text(numbered(text), encoding="utf-8")
        if key == "earnings_8k":
            exhibit = locate_exhibit(cik, row, user_agent)
            exhibit_text = plain_text(sec_get(accession_url(cik, row["accessionNumber"], exhibit), user_agent))
            (folder / "earnings_release_exhibit_99_1.txt").write_text(numbered(exhibit_text), encoding="utf-8")
            filings["release_text"] = exhibit_text
            filings["release_document"] = exhibit
    if only_step in (None, 3):
        print(f"  Saved source text under {folder}")
    if only_step == 3:
        return folder

    if only_step in (None, 4):
        print("Step 4 — Read annual XBRL facts for one matching fiscal year")
    bundle = build_company_facts(cik, user_agent, folder, ticker)
    if only_step in (None, 4):
        print(f"  Fiscal year end: {bundle['fiscal_end']}")
        for key in CONCEPTS:
            display_fact(key, bundle)
    if only_step == 4:
        return folder

    if only_step in (None, 5):
        print("Step 5 — Calculate ratios in code")
    calculations = print_calculations(bundle, price) if only_step in (None, 5) else calculate(bundle, price)
    if only_step == 5:
        return folder

    if only_step in (None, 6):
        print("Step 6 — Find latest-quarter revenue and diluted EPS in earnings release")
        lines = release_lines(filings.get("release_text", ""))
        for line in lines:
            print(f"  {line}")
        if not lines:
            print("  No matching lines were found by the text search. Inspect the saved release manually.")
    if only_step == 6:
        return folder

    peer_bundles = []
    if only_step in (None, 7):
        print("Step 7 — Compare peer operating margins on the same definition")
    for peer in peers:
        if peer.upper() == ticker:
            continue
        peer_cik, peer_company = cik_for(peer, user_agent)
        peer_folder = folder / "peers" / re.sub(r"[^A-Za-z0-9._-]+", "_", peer_company)
        peer_folder.mkdir(parents=True, exist_ok=True)
        peer_bundle = build_company_facts(peer_cik, user_agent, peer_folder, peer.upper())
        peer_margin = calculate(peer_bundle, None)["operating_margin"]
        margin_text = f"{peer_margin:.2%}" if peer_margin is not None else "unavailable"
        revenue_record = peer_bundle["values"]["revenue"]["current"]
        op_record = peer_bundle["values"]["operating_income"]["current"]
        print(f"  {peer.upper()} ({peer_company}), FY end {peer_bundle['fiscal_end']}: operating income / total revenue = {margin_text}")
        print(f"    Operating income: {source(op_record, peer_bundle['tags'].get('operating_income', 'not found'), peer_bundle['units'].get('operating_income', 'unknown'))}")
        print(f"    Total revenue: {source(revenue_record, peer_bundle['tags'].get('revenue', 'not found'), peer_bundle['units'].get('revenue', 'unknown'))}")
        peer_bundles.append({"ticker": peer.upper(), "company": peer_company, "bundle": peer_bundle, "margin": peer_margin})

    manifest = {
        "ticker": ticker,
        "company": company,
        "cik": cik,
        "run_time_local": datetime.now().astimezone().isoformat(),
        "filings": {key: {**row, "_text": None} for key, row in filings.items() if isinstance(row, dict)},
        "earnings_release_document": filings.get("release_document"),
        "facts": bundle,
        "calculations": calculations,
        "peers": [{"ticker": x["ticker"], "company": x["company"], "fiscal_end": x["bundle"]["fiscal_end"], "margin": x["margin"], "tags": x["bundle"]["tags"]} for x in peer_bundles],
        "limitations": ["Automated release text search needs manual confirmation.", "XBRL candidate tags and periods need checking against each filing.", "This program does not make an investment recommendation."],
    }
    (folder / "desk_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"  Run folder: {folder}")
    return folder


def main() -> int:
    parser = argparse.ArgumentParser(description="Seven-step SEC and XBRL equity-research data desk")
    parser.add_argument("ticker", help="SEC ticker symbol")
    parser.add_argument("--peers", default="", help="Comma-separated peer tickers")
    parser.add_argument("--price", type=float, help="Share price for P/E")
    parser.add_argument("--step", type=int, choices=range(1, 8), help="Run only this selected step (steps 4–7 also fetch the filings and facts they need)")
    args = parser.parse_args()
    env = read_env(ROOT / ".env")
    user_agent = env.get("SEC_USER_AGENT", "").strip()
    if not user_agent or "@" not in user_agent or "Your Name" in user_agent:
        print("Set SEC_USER_AGENT=Your Name your.email@example.com in the local .env file.", file=sys.stderr)
        return 2
    peers = [x.strip().upper() for x in args.peers.split(",") if x.strip()]
    try:
        folder = run_ticker(args.ticker, peers, args.price, args.step, user_agent)
        if folder != RUNS:
            print(f"\nCompleted through step {args.step or 7}. Saved run: {folder}")
        return 0
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        print("Save this exact error for debugging. Remove account details or secrets before sharing it.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
