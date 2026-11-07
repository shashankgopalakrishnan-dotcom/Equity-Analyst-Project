"""Deterministic calculations for the user's Lab 5 scoring rules."""
from __future__ import annotations

from datetime import date, timedelta
from statistics import median


def _date(value):
    try:
        return date.fromisoformat(str(value))
    except (TypeError, ValueError):
        return None


def trailing_ttm_margin(companyfacts: dict, tags: dict, annual_accession: str,
                        quarter_accession: str, reference_end: str) -> dict:
    """Build TTM Revenue and Operating Income from one 10-K and the latest 10-Q.

    Use the annual 10-K directly when it ends on the reference date. Otherwise,
    calculate FY revenue + current YTD - comparable prior YTD. The 10-Q must
    contain both YTD periods under its accession. Fail closed if dates or tags
    do not line up.
    """
    us_gaap = companyfacts.get("facts", {}).get("us-gaap", {})

    def entries(metric):
        concept = us_gaap.get(tags.get(metric, ""), {})
        units = concept.get("units", {})
        rows = units.get("USD", [])
        return [row for row in rows if isinstance(row, dict) and row.get("accn")]

    selected = {}
    annual_end = None
    for metric in ("revenue", "operating_income"):
        rows = entries(metric)
        annual = [r for r in rows if r.get("form") in ("10-K", "10-K/A") and r.get("accn") == annual_accession
                  and r.get("start") and 330 <= ((_date(r.get("end")) or date.min) - (_date(r.get("start")) or date.min)).days <= 400]
        if not annual:
            return {"available": False, "reason": f"No annual {metric} fact in the selected 10-K."}
        annual_row = max(annual, key=lambda r: str(r.get("end", "")))
        annual_end = annual_row.get("end") if annual_end is None else annual_end
        if annual_row.get("end") != annual_end:
            return {"available": False, "reason": "Annual revenue and operating income have different period ends."}

        if str(annual_row.get("end")) == str(reference_end):
            selected[metric] = {"val": annual_row.get("val"), "tag": tags.get(metric), "start": annual_row.get("start"),
                                "end": annual_row.get("end"), "accn": annual_row.get("accn"), "basis": "10-K annual"}
            continue

        start_date = (_date(annual_row.get("end")) or date.min) + timedelta(days=1)
        quarter_rows = [r for r in rows if r.get("form") in ("10-Q", "10-Q/A") and r.get("accn") == quarter_accession
                        and r.get("start") and _date(r.get("start")) and _date(r.get("end"))]
        q_rows = [r for r in quarter_rows if _date(r.get("start")) == start_date]
        if not q_rows:
            return {"available": False, "reason": f"The selected 10-Q has no current YTD {metric} fact after the latest 10-K."}
        current_row = max(q_rows, key=lambda r: str(r.get("end", "")))
        current_end = _date(current_row.get("end"))
        current_start = _date(current_row.get("start"))
        prior_candidates = []
        for row in quarter_rows:
            row_start, row_end = _date(row.get("start")), _date(row.get("end"))
            if not row_start or not row_end or row_start >= current_start or row_end >= current_end:
                continue
            if abs((current_start - row_start).days - 365) <= 7 and abs((current_end - row_end).days - 365) <= 7:
                current_duration = (current_end - current_start).days
                prior_duration = (row_end - row_start).days
                if abs(current_duration - prior_duration) <= 7:
                    prior_candidates.append(row)
        if not prior_candidates:
            return {"available": False, "reason": f"The selected 10-Q has no matching prior-year YTD {metric} fact."}
        prior_row = max(prior_candidates, key=lambda r: str(r.get("end", "")))
        if current_row.get("end") != current_end.isoformat() or prior_row.get("end") != _date(prior_row.get("end")).isoformat():
            return {"available": False, "reason": "A YTD fact has an invalid period end."}
        value = float(annual_row["val"]) + float(current_row["val"]) - float(prior_row["val"])
        selected[metric] = {"val": value, "tag": tags.get(metric), "start": (_date(prior_row["end"]) + timedelta(days=1)).isoformat(),
                            "end": current_row.get("end"), "basis": "latest 10-K + latest 10-Q YTD - comparative 10-Q YTD",
                            "annual": {"val": annual_row.get("val"), "tag": tags.get(metric), "start": annual_row.get("start"), "end": annual_row.get("end"), "accn": annual_row.get("accn")},
                            "current_ytd": {"val": current_row.get("val"), "tag": tags.get(metric), "start": current_row.get("start"), "end": current_row.get("end"), "accn": current_row.get("accn")},
                            "prior_ytd": {"val": prior_row.get("val"), "tag": tags.get(metric), "start": prior_row.get("start"), "end": prior_row.get("end"), "accn": prior_row.get("accn")}}

    if selected.get("revenue", {}).get("end") != selected.get("operating_income", {}).get("end") or selected.get("revenue", {}).get("start") != selected.get("operating_income", {}).get("start"):
        return {"available": False, "reason": "TTM revenue and operating income do not cover the same period."}
    revenue = selected["revenue"].get("val")
    income = selected["operating_income"].get("val")
    if not isinstance(revenue, (int, float)) or not isinstance(income, (int, float)) or revenue <= 0:
        return {"available": False, "reason": "TTM revenue or operating income is not numeric."}
    period_start, period_end = _date(selected["revenue"].get("start")), _date(selected["revenue"].get("end"))
    if not period_start or not period_end:
        return {"available": False, "reason": "TTM period dates are unavailable."}
    span = (period_end - period_start).days + 1
    if not 360 <= span <= 372:
        return {"available": False, "reason": f"The derived TTM period is {span} days; expected 360 to 372 days."}
    return {"available": True, "revenue": revenue, "operating_income": income, "margin": income / revenue,
            "period_start": selected["revenue"]["start"], "period_end": selected["revenue"]["end"],
            "period_days": span, "basis": selected["revenue"].get("basis"),
            "revenue_source": selected["revenue"], "operating_income_source": selected["operating_income"]}


def persona_calculations(facts: dict, peers: list[dict], fiscal_end: str | None,
                         company_ttm: dict | None = None, peer_window_days: int = 45) -> dict:
    def value(bundle, metric, period):
        item = bundle.get(metric, {}).get(period) or {}
        number = item.get('val')
        return number if isinstance(number, (int, float)) and not isinstance(number, bool) else None

    margins = {}
    totals = {}
    for period in ('current', 'prior'):
        revenue = value(facts, 'revenue', period)
        income = value(facts, 'operating_income', period)
        margins[period] = income / revenue if income is not None and revenue else None
        long_term = value(facts, 'long_term_debt', period)
        current = value(facts, 'current_debt', period)
        totals[period] = long_term + current if long_term is not None and current is not None else None
    change = ((margins['current'] - margins['prior']) * 100
              if margins['current'] is not None and margins['prior'] is not None else None)
    comparable = []
    anchor = _date((company_ttm or {}).get("period_end"))
    for peer in peers:
        ttm = peer.get('ttm') or {}
        end = _date(ttm.get('period_end'))
        start = _date(ttm.get('period_start'))
        margin = ttm.get('margin')
        if (anchor and end and start and abs((anchor - end).days) <= peer_window_days
                and isinstance(margin, (int, float)) and not isinstance(margin, bool)
                and 360 <= (end - start).days + 1 <= 372):
            comparable.append({'ticker': peer.get('ticker'), 'period_start': start.isoformat(),
                               'period_end': end.isoformat(), 'margin': margin,
                               'days_from_anchor': (end - anchor).days, 'basis': ttm.get('basis')})
    benchmark = median(x['margin'] for x in comparable) if comparable else None
    company_ttm_margin = ((company_ttm or {}).get('margin')
                          if (company_ttm or {}).get('available') else None)
    comparison = (None if benchmark is None or company_ttm_margin is None
                  else 'above' if company_ttm_margin > benchmark
                  else 'below' if company_ttm_margin < benchmark else 'equal')
    cfo, net_income = value(facts, 'cash_from_operations', 'current'), value(facts, 'net_income', 'current')
    cash_score = None
    if cfo is not None and net_income is not None:
        if cfo > net_income:
            cash_score = 3
        elif cfo > 0 and cfo <= net_income:
            cash_score = 2
        elif cfo < 0 and net_income > 0:
            cash_score = 1
    margin_score = None if change is None else (3 if change > 0.1 else 1 if change < -0.1 else 2)
    debt_score = None if None in totals.values() else (3 if totals['current'] < totals['prior'] else 1 if totals['current'] > totals['prior'] else 2)
    peer_score = {'above': 3, 'equal': 2, 'below': 1}.get(comparison)
    peer_status = (f"TTM peer median uses comparable peers ending within {peer_window_days} days of company TTM end {anchor.isoformat()}."
                   if benchmark is not None else f"Insufficient evidence: no peer TTM period ends within {peer_window_days} days of company TTM end {anchor.isoformat() if anchor else fiscal_end}.")
    return {'total_debt': totals, 'operating_margin': margins,
            'operating_margin_change_percentage_points': change,
            'company_ttm': company_ttm, 'peer_company_ttm_margin': company_ttm_margin,
            'peer_alignment_window_days': peer_window_days,
            'peer_comparison_status': peer_status,
            'comparable_peers': comparable, 'peer_median_operating_margin': benchmark,
            'peer_margin_comparison': comparison,
            'financial_scores': {'cash_flow_support': cash_score, 'operating_margin_trend': margin_score,
                                 'debt_trend': debt_score, 'peer_comparison': peer_score}}


def business_score_average(growth, competitive):
    scores = (growth, competitive)
    if any(isinstance(x, bool) or not isinstance(x, (int, float)) or x not in (1, 2, 3, 4, 5) for x in scores):
        return None
    return sum(scores) / 2
