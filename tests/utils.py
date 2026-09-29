from datetime import UTC, datetime, timedelta


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def future_iso(days: int = 1) -> str:
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()
