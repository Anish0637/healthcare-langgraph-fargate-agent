from datetime import datetime, timezone


def get_utc_time(_: dict | None = None) -> str:
    return datetime.now(timezone.utc).isoformat()


def patient_risk_score(args: dict) -> str:
    age = int(args.get("age", 50))
    chronic = int(args.get("chronic_conditions", 0))
    score = min(100, age + chronic * 10)
    return f"risk_score={score}"


TOOLS = {
    "get_utc_time": get_utc_time,
    "patient_risk_score": patient_risk_score,
}
