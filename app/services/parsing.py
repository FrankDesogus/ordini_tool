from __future__ import annotations

from datetime import datetime, date
from dateutil import parser

def parse_date(value) -> date | None:
    if value is None:
        return None
    if isinstance(value, float):
        # pandas NaN
        return None
    s = str(value).strip()
    if s == "" or s.lower() == "nan":
        return None
    try:
        # supporta 'YYYY-MM-DD' e timestamp ISO
        dt = parser.parse(s)
        return dt.date()
    except Exception:
        return None

def parse_datetime(value) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, float):
        return None
    s = str(value).strip()
    if s == "" or s.lower() == "nan":
        return None
    try:
        return parser.parse(s)
    except Exception:
        return None

def parse_float(value) -> float | None:
    if value is None:
        return None
    try:
        if isinstance(value, str):
            v = value.strip().replace(",", ".")
            if v == "" or v.lower() == "nan":
                return None
            return float(v)
        if str(value).lower() == "nan":
            return None
        return float(value)
    except Exception:
        return None
