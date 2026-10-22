"""Build a trend matrix (item x period) from verified scene verdicts.

    python trend_matrix.py build  verdicts.jsonl  --out trend_matrix.json
    python trend_matrix.py md     trend_matrix.json

verdicts.jsonl, one verified scene per line:
  {"item", "stream_name", "filename", "ts_start_ms", "ts_end_ms",
   "verdict": "PASS|PARTIAL|FAIL", "evidence", "frame_png", "source": "street|window"}
source (default "street"): worn by a person outdoors vs shown on a mannequin / shop window.
"""
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import os, sys, json
import fire
try:
    from src.utils.util_log import log_info, log_error, log_trace, log_warning
except ImportError:  # skill runs outside the repo: plain stderr logger
    def log_info(*s): print(*s, file=sys.stderr)
    log_error = log_trace = log_warning = log_info

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fashion_period import period_parse, period_sort

MIN_VIEWED = 4      # a cell needs this many viewed scenes to count
MIN_PERIODS = 3     # an item needs this many counted, dated periods for a trend label
DELTA = 0.15        # fitted rate change first->last period for rising / fading
EVERGREEN = 0.5     # rate in every counted period
N_EVIDENCE = 3


def os_read_jsonl(path: str) -> List[Dict]:
    with open(path) as f:
        return [json.loads(x) for x in f if x.strip()]


def trend_label(rates: List[float]) -> str:
    """rates: counted, dated periods in time order."""
    n = len(rates)
    if n < MIN_PERIODS:
        return "insufficient"
    if min(rates) >= EVERGREEN:
        return "evergreen"
    xm, ym = (n - 1) / 2, sum(rates) / n
    slope = sum((i - xm) * (r - ym) for i, r in enumerate(rates)) / sum((i - xm) ** 2 for i in range(n))
    d = slope * (n - 1)
    return "rising" if d > DELTA else "fading" if d < -DELTA else "stable"


def matrix_build(rows: List[Dict], source: str = "street") -> Dict[str, Any]:
    """source: street | window | all."""
    seen, items, pinfo = set(), [], {}
    cells, evid = {}, {}
    for r in rows:
        if source != "all" and r.get("source", "street") != source:
            continue
        k = (r["item"], r["filename"], int(r["ts_start_ms"]))
        if k in seen:
            continue
        seen.add(k)
        it = r["item"]
        p = period_parse(r["filename"], r.get("stream_name", ""))
        pk = p["period_key"]
        pinfo[pk] = p
        if it not in cells:
            items.append(it)
            cells[it], evid[it] = {}, {}
        c = cells[it].setdefault(pk, {"pass": 0, "viewed": 0, "rate": 0.0})
        c["viewed"] += 1
        if r["verdict"] == "PASS":
            c["pass"] += 1
            ev = evid[it].setdefault(pk, [])
            if len(ev) < N_EVIDENCE and r.get("frame_png"):
                ev.append(r["frame_png"])

    periods = sorted(pinfo, key=lambda k: period_sort(pinfo[k]))
    trend = {}
    for it in items:
        for c in cells[it].values():
            c["rate"] = round(c["pass"] / c["viewed"], 3)
        rates = [cells[it][pk]["rate"] for pk in periods
                 if pk in cells[it] and pinfo[pk]["year"] and cells[it][pk]["viewed"] >= MIN_VIEWED]
        trend[it] = trend_label(rates)
    return {"source": source, "items": items, "periods": periods, "cells": cells, "trend": trend, "evidence": evid}


def md_matrix(m: Dict[str, Any]) -> str:
    ps = m["periods"]
    out = ["| Item | " + " | ".join(ps) + " | Trend |", "|---|" + "---|" * len(ps) + "---|"]
    for it in m["items"]:
        row = []
        for pk in ps:
            c = m["cells"][it].get(pk)
            row.append(f"{c['pass']}/{c['viewed']}" if c else "·")
        out.append(f"| {it} | " + " | ".join(row) + f" | {m['trend'][it]} |")
    return "\n".join(out)


def build(verdicts: str, out: str = "", source: str = "street"):
    """CLI: verdicts.jsonl -> trend_matrix[_<source>].json (default: next to verdicts)."""
    m = matrix_build(os_read_jsonl(verdicts), source)
    name = "trend_matrix.json" if source == "street" else f"trend_matrix_{source}.json"
    out = out or os.path.join(os.path.dirname(os.path.abspath(verdicts)), name)
    with open(out, "w") as f:
        json.dump(m, f, indent=1)
    log_info("saved", out)
    print(md_matrix(m))


def md(matrix_json: str):
    """CLI: print trend_matrix.json as a markdown table (cells = PASS/viewed)."""
    with open(matrix_json) as f:
        print(md_matrix(json.load(f)))


if __name__ == "__main__":
    fire.Fire()
