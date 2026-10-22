"""Derive season / month / year / period_key from a VModal video filename + stream_name.

    python fashion_period.py period NOVEMBER_2025_MILAN_SHOPPING_VLOG_ITALIAN_AUTUMN_STREET_STYLE_whatarepeoplewearing Fall_Fashion_Trends_and_Classic_Pieces_for_dressing_this_Autumn
    -> {"season": "fall", "month": 11, "year": 2025, "period_key": "2025-11"}

period_key: "YYYY-MM" (month+year) | "YYYY-<season>" (year only) | "<season>-unknown" (no year).
"""
from typing import List, Dict, Tuple, Optional, Any, Union
from dataclasses import dataclass
import os, sys, re, json
import fire
try:
    from src.utils.util_log import log_info, log_error, log_trace, log_warning
except ImportError:  # skill runs outside the repo: plain stderr logger
    def log_info(*s): print(*s, file=sys.stderr)
    log_error = log_trace = log_warning = log_info


MONTHS = {
    "JANUARY": 1, "FEBRUARY": 2, "MARCH": 3, "APRIL": 4, "MAY": 5, "JUNE": 6, "JULY": 7,
    "AUGUST": 8, "SEPTEMBER": 9, "OCTOBER": 10, "NOVEMBER": 11, "DECEMBER": 12,
    "GENNAIO": 1, "FEBBRAIO": 2, "MARZO": 3, "APRILE": 4, "MAGGIO": 5, "GIUGNO": 6, "LUGLIO": 7,
    "AGOSTO": 8, "SETTEMBRE": 9, "OTTOBRE": 10, "NOVEMBRE": 11, "DICEMBRE": 12,
}
SEASONS = {
    "SUMMER": "summer", "ESTATE": "summer", "FALL": "fall", "AUTUMN": "fall", "AUTUNNO": "fall",
    "WINTER": "winter", "INVERNO": "winter", "SPRING": "spring", "PRIMAVERA": "spring",
}
# month used to place a season-only period on the time axis
SEASON_MONTH = {"winter": 1, "spring": 4, "summer": 7, "fall": 10, "unknown": 0}


def month_to_season(m: int) -> str:
    return {12: "winter", 1: "winter", 2: "winter", 3: "spring", 4: "spring", 5: "spring",
            6: "summer", 7: "summer", 8: "summer"}.get(m, "fall")


def str_tokens(s: str) -> List[str]:
    return [t for t in re.split(r"[^A-Za-z0-9]+", s or "") if t]


def str_season(s: str) -> str:
    for t in str_tokens(s):
        if t.upper() in SEASONS:
            return SEASONS[t.upper()]
    return "unknown"


def period_parse(filename: str, stream_name: str = "") -> Dict[str, Any]:
    """First month token + first year token of filename; season from month, else filename, else stream."""
    month, year = None, None
    for t in str_tokens(filename):
        u = t.upper()
        if month is None and u in MONTHS:
            month = MONTHS[u]
        if year is None and re.fullmatch(r"20\d\d", u):
            year = int(u)
    season = month_to_season(month) if month else str_season(filename)
    if season == "unknown":
        season = str_season(stream_name)

    if year and month:
        key = f"{year}-{month:02d}"
    elif year:
        key = f"{year}-{season}"
    else:
        key = f"{season}-unknown"
    return {"season": season, "month": month, "year": year, "period_key": key}


def period_sort(p: Dict[str, Any]) -> Tuple[int, int]:
    """Dated periods by (year, month); undated ones last."""
    if not p["year"]:
        return (9999, SEASON_MONTH.get(p["season"], 0))
    return (p["year"], p["month"] or SEASON_MONTH.get(p["season"], 0))


def period(filename: str, stream_name: str = ""):
    """CLI: print the period as JSON."""
    print(json.dumps(period_parse(str(filename), str(stream_name))))


if __name__ == "__main__":
    fire.Fire()
