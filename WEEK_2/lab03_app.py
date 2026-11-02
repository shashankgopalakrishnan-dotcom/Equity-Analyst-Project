#!/usr/bin/env python3
"""Four-role report workflow for FIN 67110 Lab 03.

Uses the OpenAI Python SDK with Purdue GenAI Studio's documented
OpenAI-compatible chat-completions endpoint. It reads API_KEY only at run time. It does not
print, save, or transmit the key except as the Authorization header.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from openai import APIError, OpenAI

ROOT = Path(__file__).resolve().parents[1]
API_BASE_URL_DEFAULT = "https://genai.rcac.purdue.edu/api"
REPORT_PARTS = [
    "Overview",
    "Market Positioning and Growth Outlook",
    "Valuation Insights",
    "Future Developments and Strategic Recommendations",
    "Investment Recommendation",
]


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


def json_content(content: str) -> dict:
    cleaned = content.strip()
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.I)
    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else {"result": data}
    except json.JSONDecodeError:
        return {"text": content}


class StudioClient:
    def __init__(self, api_key: str, model: str, base_url: str) -> None:
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=180.0, max_retries=0)
        self.last_call = 0.0

    def call(self, role_name: str, instructions: str, payload: dict) -> dict:
        print(f"Role: {role_name}")
        wait = 3.2 - (time.monotonic() - self.last_call)
        if wait > 0:
            time.sleep(wait)
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": instructions},
                {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
            ],
            stream=False,
        )
        self.last_call = time.monotonic()
        message = response.choices[0].message.content if response.choices else None
        if not isinstance(message, str) or not message.strip():
            raise RuntimeError("GenAI Studio returned an empty response.")
        return json_content(message)


def get_file(folder: Path, name: str) -> str:
    path = folder / name
    return path.read_text(encoding="utf-8") if path.exists() else ""


def numbered_item_excerpt(text: str, item: str, next_item: str, limit: int) -> str:
    lines = text.splitlines()
    start_re = re.compile(rf"^\s*\d+\s*:\s*Item\s+{item}.*$", re.I)
    end_re = re.compile(rf"^\s*\d+\s*:\s*Item\s+{next_item}\b", re.I)
    start = next((i for i, line in enumerate(lines) if start_re.match(line)), None)
    if start is None:
        return ""
    end = next((i for i in range(start + 1, len(lines)) if end_re.match(lines[i])), len(lines))
    chunk = "\n".join(lines[start:end])
    if len(chunk) <= limit:
        return chunk
    clipped = chunk[:limit]
    return clipped.rsplit("\n", 1)[0]


def research_source(tenk: str) -> str:
    business = numbered_item_excerpt(tenk, r"1\s*[.\-—– ]\s*Business", r"1A", 12_000)
    mda = numbered_item_excerpt(tenk, r"7\s*[.\-—– ]\s*Management", r"7A", 16_000)
    if not business and not mda:
        return tenk[:28_000]
    return "\n\n".join(("10-K Item 1: Business\n" + business, "10-K Item 7: MD&A\n" + mda))


def data_payload(manifest: dict) -> dict:
    facts = manifest.get("facts", {})
    values = facts.get("values", {})
    calculated = manifest.get("calculations", {})
    out = {"ticker": manifest.get("ticker"), "company": manifest.get("company"), "fiscal_end": facts.get("fiscal_end"), "facts": {}}
    for key, record in values.items():
        current = record.get("current") or {}
        prior = record.get("prior") or {}
        out["facts"][key] = {
            "current": current.get("val"), "current_end": current.get("end"),
            "current_filing": current.get("accn"), "prior": prior.get("val"),
            "prior_end": prior.get("end"), "prior_filing": prior.get("accn"),
            "tag": facts.get("tags", {}).get(key), "unit": facts.get("units", {}).get(key),
        }
    out["ratios_and_arithmetic"] = calculated
    out["market_price"] = manifest.get("latest_market_quote")
    out["peers"] = manifest.get("peers", [])
    out["filings"] = {
        key: {k: val for k, val in row.items() if k in ("form", "accessionNumber", "filingDate", "acceptanceDateTime", "primaryDocument")}
        for key, row in manifest.get("filings", {}).items()
    }
    return out


def role_payload(task: str, context: dict, expected: str) -> dict:
    return {"task": task, "context": context, "expected_output": expected}


def render_text(result: dict) -> str:
    return result.get("markdown") or result.get("text") or json.dumps(result, indent=2, ensure_ascii=False)


def parts_missing(markdown: str) -> list[str]:
    normalized = re.sub(r"[^a-z0-9 ]", "", markdown.lower())
    return [part for part in REPORT_PARTS if re.sub(r"[^a-z0-9 ]", "", part.lower()) not in normalized]


def manifest_filings_header(manifest: dict) -> str:
    filings = manifest.get("filings", {})
    labels = ("10k", "10q", "earnings_8k")
    items = []
    for label in labels:
        row = filings.get(label, {})
        if row:
            if label == "earnings_8k":
                release = manifest.get("earnings_release_document")
                exhibit = release.get("type") if isinstance(release, dict) else None
                name = f"earnings release ({exhibit})" if exhibit else "earnings release exhibit"
            else:
                name = row.get("form", label)
            items.append(f"{name} accession {row.get('accessionNumber', 'unknown')}")
    return "Filings read: " + "; ".join(items)


def financial_datasets_close(ticker: str, price_date: str, api_key: str) -> dict:
    day = date.fromisoformat(price_date)
    params = urlencode({
        "ticker": ticker,
        "interval": "day",
        "start_date": day.isoformat(),
        "end_date": (day + timedelta(days=1)).isoformat(),
    })
    request = Request(
        "https://api.financialdatasets.ai/prices?" + params,
        headers={"X-API-KEY": api_key, "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=30) as response:
            payload = json.load(response)
    except HTTPError as exc:
        raise RuntimeError(f"Financial Datasets price request failed with HTTP {exc.code}.") from None
    except (URLError, TimeoutError, json.JSONDecodeError):
        raise RuntimeError("Financial Datasets price request failed or returned invalid JSON.") from None
    rows = payload.get("prices", []) if isinstance(payload, dict) else []
    row = next((item for item in rows if str(item.get("time", ""))[:10] == day.isoformat()), None)
    if not row or row.get("close") is None:
        raise RuntimeError(f"Financial Datasets returned no daily close for {ticker} on {price_date}.")
    return {
        "ticker": ticker,
        "price": float(row["close"]),
        "currency": "USD",
        "as_of_date": day.isoformat(),
        "source": "Financial Datasets historical daily prices",
        "endpoint": "/prices",
        "price_type": "daily close",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build and save the Lab 03 five-part report")
    parser.add_argument("run_folder", type=Path, help="Lab 02 run folder containing desk_manifest.json and filing text")
    parser.add_argument("--price", type=float, help="Optional supplied share price")
    parser.add_argument("--price-date", help="Historical close date (YYYY-MM-DD); fetched from Financial Datasets when --price is omitted")
    parser.add_argument("--model", help="Override the model ID in .env for this run")
    args = parser.parse_args()
    folder = args.run_folder.expanduser().resolve()
    env = read_env(ROOT / ".env")
    api_key = env.get("API_KEY", "").strip()
    model = (args.model or env.get("GENAI_MODEL", "")).strip()
    base_url = env.get("GENAI_BASE_URL", API_BASE_URL_DEFAULT).strip()
    if not api_key or api_key.startswith("your_"):
        print("Set a current, rotated API_KEY in the local .env file. Do not paste it into chat or commit it.", file=sys.stderr)
        return 2
    if not model:
        print("Set GENAI_MODEL to a model ID available to your Purdue GenAI Studio account in .env.", file=sys.stderr)
        return 2
    manifest_path = folder / "desk_manifest.json"
    if not manifest_path.exists():
        print(f"Missing {manifest_path}. Run Lab 02 first.", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if args.price_date:
        try:
            date.fromisoformat(args.price_date)
        except ValueError:
            print("--price-date must use YYYY-MM-DD format.", file=sys.stderr)
            return 2
    if args.price is not None:
        quote = {
            "ticker": manifest.get("ticker"), "price": args.price, "currency": "USD",
            "as_of_date": args.price_date, "source": "user-supplied --price",
            "endpoint": None, "price_type": "user-supplied close",
        }
        manifest["latest_market_quote"] = quote
    elif args.price_date:
        data_key = env.get("FINANCIAL_DATASETS_PROFESSOR_API_KEY", "").strip()
        if not data_key:
            print("Set FINANCIAL_DATASETS_PROFESSOR_API_KEY in the local .env file.", file=sys.stderr)
            return 2
        try:
            quote = financial_datasets_close(manifest.get("ticker", ""), args.price_date, data_key)
        except RuntimeError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        manifest["latest_market_quote"] = quote
    else:
        quote = manifest.get("latest_market_quote")
    if quote:
        price_value = quote.get("price")
        eps = manifest.get("facts", {}).get("values", {}).get("diluted_eps", {}).get("current", {}).get("val")
        manifest.setdefault("calculations", {})["pe"] = price_value / eps if price_value is not None and eps else None
        manifest["share_price_input"] = price_value
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    tenk = get_file(folder, "10k.txt")
    release_paths = sorted(folder.glob("earnings_release_exhibit_*.txt"))
    release = release_paths[0].read_text(encoding="utf-8") if release_paths else ""
    if not tenk or not release:
        print("The run folder must include the saved 10-K and earnings release text. Re-run Lab 02.", file=sys.stderr)
        return 2
    # Keep the relevant numbered sections and citations while bounding each model payload.
    tenk_excerpt = research_source(tenk)
    release_excerpt = release[:30000]
    base = data_payload(manifest)
    client = StudioClient(api_key, model, base_url)

    research = client.call(
        "Research Analyst",
        "You are the Research Analyst. Use only the source text and metadata in the JSON supplied by the Strategy Manager. Make no unsupported claims. Every factual claim must include a direct short quote and its numbered source line, in the form [10-K line 00001] or [release line 00001]. State when evidence is absent. Return a JSON object with a markdown field.",
        role_payload(
            "Describe the business model, competitive position, catalysts, and recent developments. Use the 10-K business and MD&A sections and the earnings release.",
            {"ticker": base["ticker"], "company": base["company"], "10k_numbered_source": tenk_excerpt, "release_numbered_source": release_excerpt},
            "JSON object: {markdown: string, sources: array}. Include evidence lines for each claim.",
        ),
    )

    financial = client.call(
        "Financial Analyst",
        "You are the Financial Analyst. Use only the JSON supplied by the Strategy Manager. Never calculate a ratio in the model; quote the calculator's arithmetic. Every number must state its filing and XBRL tag, period, or numbered release line. State the definition where alternatives exist. Return a JSON object with a markdown field.",
        role_payload(
            "State all eleven Lab 03 audit claims: (1) latest 10-K total revenue; (2) annual revenue growth; (3) operating income and operating margin using total revenue; (4) net income attributable to the company; (5) GAAP diluted EPS; (6) return on average equity; (7) debt/equity including current long-term debt; (8) free cash flow; (9) latest-quarter total revenue; (10) latest-quarter revenue growth versus the same quarter last year; (11) latest-quarter GAAP diluted EPS. Also report peers, P/E, price date, and arithmetic when available. Use only supplied facts, calculations, and release lines. Do not invent missing numbers.",
            {"verified_data_and_calculator_output": base, "release_numbered_source": release_excerpt},
            "JSON object: {markdown: string, numeric_claims: array}. Each claim has value, source, and period.",
        ),
    )

    advisor = client.call(
        "Investment Advisor",
        "You are the Investment Advisor. Use only the two specialist outputs in this JSON. Do not add external facts or calculate. Give a Buy, Hold, or Sell recommendation with a thesis and name the single reported number that most drives it. Use only numbers and claims stated in the two supplied role outputs. Flag low confidence if the evidence is insufficient. Return a JSON object with a markdown field.",
        role_payload(
            "Write a concise investment thesis and recommendation based only on the Research Analyst and Financial Analyst outputs.",
            {"research_analyst_output": research, "financial_analyst_output": financial},
            "JSON object: {markdown: string, recommendation: Buy|Hold|Sell, deciding_number: string}.",
        ),
    )

    roles = {"research": research, "financial": financial, "advisor": advisor}
    manager_review = client.call(
        "Strategy Manager",
        "You are the Strategy Manager. Check all five exact report parts and check consistency against the specialist outputs. Return valid JSON with keys complete (boolean), failing_parts (array of exact part names and why), and report_markdown (string). If a part fails, name its originating role. Do not invent facts, citations, calculations, or prices.",
        role_payload("Review the five-part report and mark any missing or inconsistent part for one targeted return to its role.", roles, "JSON manager review."),
    )
    failures = manager_review.get("failing_parts", []) if isinstance(manager_review.get("failing_parts", []), list) else []
    for failure in failures:
        if not isinstance(failure, dict):
            continue
        part = failure.get("part", "")
        why = failure.get("why", "").strip()
        if part not in REPORT_PARTS:
            continue
        role_key = "research" if part in REPORT_PARTS[:2] or part == REPORT_PARTS[3] else "financial" if part == REPORT_PARTS[2] else "advisor"
        corrected = client.call(
            f"{role_key.title()} Analyst — one revision",
            "Revise only the assigned report part. Use only the JSON context provided. Keep every claim supported and every number sourced. Return JSON with markdown.",
            role_payload(f"Fix the part '{part}'. Manager feedback: {why}", {"prior_role_output": roles[role_key], "verified_data": base if role_key == "financial" else {"ticker": base["ticker"], "company": base["company"], "10k_numbered_source": tenk_excerpt, "release_numbered_source": release_excerpt}}, "JSON object with markdown for the revised part only."),
        )
        roles[role_key] = corrected

    final_review = client.call(
        "Strategy Manager — compile",
        "You are the Strategy Manager. Compile the role outputs into exactly five Markdown sections with these headings: Overview; Market Positioning and Growth Outlook; Valuation Insights; Future Developments and Strategic Recommendations; Investment Recommendation. Preserve citations and arithmetic. Do not add facts or numbers. Return JSON with report_markdown.",
        role_payload("Compile the final report from the revised role outputs. Do not include claims outside those outputs.", roles, "JSON object with report_markdown."),
    )
    report = final_review.get("report_markdown") or final_review.get("markdown") or render_text(final_review)
    missing = parts_missing(report)
    if missing:
        print("Warning: manager output appears to omit these required section headings: " + ", ".join(missing), file=sys.stderr)
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    quote = manifest.get("latest_market_quote") or {}
    price_line = f"Price input: ${quote['price']:.2f} USD on {quote.get('as_of_date') or 'date not supplied'} from {quote.get('source', 'saved run data')}\n" if quote.get("price") is not None else "Price input: unavailable\n"
    header = f"{manifest_filings_header(manifest)}\nRun time: {now}\n{price_line}Status: AI-generated draft; hand audit required\n\n"
    report_path = folder / f"{manifest.get('ticker', 'company')}_lab03_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path.write_text(header + report.rstrip() + "\n", encoding="utf-8")
    print(f"Report saved: {report_path}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, RuntimeError, APIError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
