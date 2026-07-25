from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

REQUIRED_SCHEMA_FIELDS = [
    "data_source",
    "timestamp",
    "symbol",
    "metric_name",
    "metric_value",
    "units",
    "frequency",
]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if cleaned in {"", ".", "None", "null", "N/A", "NA", "-"}:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None
    return None


def normalize_record(
    data_source: str,
    timestamp: str,
    symbol: Optional[str],
    metric_name: str,
    metric_value: Any,
    units: str,
    frequency: str,
    provider_timestamp: Optional[str] = None,
    status: str = "raw",
    message: Optional[str] = None,
) -> Dict[str, Any]:
    record = {
        "data_source": data_source,
        "timestamp": timestamp,
        "symbol": symbol,
        "metric_name": metric_name,
        "metric_value": safe_float(metric_value),
        "units": units,
        "frequency": frequency,
        "provider_timestamp": provider_timestamp,
        "status": status,
        "message": message,
    }
    return record


def validate_schema(record: Dict[str, Any]) -> bool:
    return all(field in record for field in REQUIRED_SCHEMA_FIELDS)
