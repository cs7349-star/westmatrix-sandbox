from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Tuple

from .normalize import REQUIRED_SCHEMA_FIELDS, safe_float, validate_schema


def parse_date(value: Any):
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    text = str(value).replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        try:
            return datetime.strptime(str(value)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return None


def find_missing_values(record: Dict[str, Any]) -> List[str]:
    missing = []
    for field in REQUIRED_SCHEMA_FIELDS:
        if field not in record or record[field] is None or record[field] == "":
            missing.append(field)
    return missing


def has_invalid_numeric_value(record: Dict[str, Any]) -> bool:
    value = safe_float(record.get("metric_value"))
    if value is None:
        return True
    metric = str(record.get("metric_name", "")).lower()
    if any(keyword in metric for keyword in ["price", "market cap", "high", "low", "gdp", "cpi", "unemployment"]):
        return value < 0
    return False


def is_stale(record: Dict[str, Any], max_age_days: int = 7) -> bool:
    metric = str(record.get("metric_name", "")).lower()
    frequency = str(record.get("frequency", "")).lower()
    date_value = record.get("provider_timestamp") or record.get("timestamp")
    observed_at = parse_date(date_value)
    if observed_at is None:
        return True
    now = datetime.now(timezone.utc)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=timezone.utc)
    if "quarter" in frequency or "gdp" in metric:
        max_age_days = max(max_age_days, 140)
    elif "monthly" in frequency or "cpi" in metric or "unemployment" in metric:
        max_age_days = max(max_age_days, 60)
    return (now - observed_at).days > max_age_days


def duplicate_keys(records: Iterable[Dict[str, Any]]) -> List[Tuple[Any, ...]]:
    seen = set()
    duplicates = []
    for record in records:
        key = (
            record.get("data_source"),
            record.get("symbol"),
            record.get("metric_name"),
            record.get("provider_timestamp") or record.get("timestamp"),
        )
        if key in seen and key not in duplicates:
            duplicates.append(key)
        seen.add(key)
    return duplicates


def price_difference_pct(yahoo_price: Any, alpha_price: Any) -> float | None:
    y = safe_float(yahoo_price)
    a = safe_float(alpha_price)
    if y is None or a is None or y == 0:
        return None
    return abs(y - a) / y * 100


def compare_provider_prices(records: List[Dict[str, Any]], tolerance_pct: float = 2.0) -> Dict[str, Dict[str, Any]]:
    results: Dict[str, Dict[str, Any]] = {}
    by_symbol: Dict[str, Dict[str, float]] = {}
    for record in records:
        symbol = record.get("symbol")
        metric = str(record.get("metric_name", "")).lower()
        source = str(record.get("data_source", "")).lower()
        if not symbol or "price" not in metric:
            continue
        by_symbol.setdefault(symbol, {})[source] = record.get("metric_value")
    for symbol, values in by_symbol.items():
        yahoo = values.get("yahoo finance")
        alpha = values.get("alpha vantage")
        diff = price_difference_pct(yahoo, alpha)
        if diff is None:
            status = "Warning"
        elif diff > tolerance_pct:
            status = "Warning"
        else:
            status = "Pass"
        results[symbol] = {
            "yahoo_price": yahoo,
            "alpha_vantage_price": alpha,
            "difference_pct": diff,
            "tolerance_pct": tolerance_pct,
            "status": status,
        }
    return results


def evaluate_records(records: List[Dict[str, Any]], stale_days: int = 7, tolerance_pct: float = 2.0) -> Dict[str, Any]:
    issues = []
    duplicate_list = duplicate_keys(records)
    duplicate_set = set(duplicate_list)
    for index, record in enumerate(records):
        record_issues = []
        if not validate_schema(record):
            missing_schema = [field for field in REQUIRED_SCHEMA_FIELDS if field not in record]
            record_issues.append(f"schema_missing:{','.join(missing_schema)}")
        missing = find_missing_values(record)
        if missing:
            record_issues.append(f"missing:{','.join(missing)}")
        if has_invalid_numeric_value(record):
            record_issues.append("invalid_numeric")
        if is_stale(record, stale_days):
            record_issues.append("stale_observation")
        if str(record.get("status", "")).lower() in {"api_failure", "rate_limited", "error"}:
            record_issues.append("api_failure_or_rate_limit")
        key = (
            record.get("data_source"),
            record.get("symbol"),
            record.get("metric_name"),
            record.get("provider_timestamp") or record.get("timestamp"),
        )
        if key in duplicate_set:
            record_issues.append("duplicate_record")
        if record_issues:
            issues.append({"index": index, "record": record, "issues": record_issues})
    provider_comparison = compare_provider_prices(records, tolerance_pct)
    for symbol, comparison in provider_comparison.items():
        if comparison["status"] != "Pass":
            issues.append({"symbol": symbol, "issues": ["provider_price_difference"], "comparison": comparison})
    status = assign_status(issues)
    by_source = source_status(records, issues)
    return {
        "overall_status": status,
        "record_count": len(records),
        "issue_count": len(issues),
        "issues": issues,
        "provider_price_comparison": provider_comparison,
        "status_by_source": by_source,
        "rules": status_rules(),
    }


def assign_status(issues: List[Dict[str, Any]]) -> str:
    if not issues:
        return "Pass"
    severe = {"schema_missing", "missing", "invalid_numeric", "api_failure_or_rate_limit"}
    for issue in issues:
        for label in issue.get("issues", []):
            root = label.split(":", 1)[0]
            if root in severe:
                return "Fail"
    return "Warning"


def source_status(records: List[Dict[str, Any]], issues: List[Dict[str, Any]]) -> Dict[str, str]:
    sources = {str(record.get("data_source")) for record in records if record.get("data_source")}
    result = {source: "Pass" for source in sources}
    for issue in issues:
        record = issue.get("record") or {}
        source = record.get("data_source")
        if not source:
            continue
        status = assign_status([issue])
        if status == "Fail":
            result[source] = "Fail"
        elif status == "Warning" and result.get(source) != "Fail":
            result[source] = "Warning"
    return result


def status_rules() -> Dict[str, str]:
    return {
        "Pass": "No required-field, numeric, freshness, duplicate, API, schema, or provider-comparison warnings were detected.",
        "Warning": "Non-critical issues were detected, such as stale data, duplicates, or provider price differences above tolerance.",
        "Fail": "Critical issues were detected, such as missing required fields, invalid numeric values, schema failures, or API failures/rate limits.",
    }
