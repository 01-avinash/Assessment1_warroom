"""
tools.py — Shared tools that agents call programmatically.
Tool 1: aggregate_metrics   — computes summary stats for each metric
Tool 2: detect_anomalies    — flags metrics that breached success criteria
Tool 3: summarize_sentiment — counts and scores user feedback sentiment
Tool 4: compare_trend       — compares pre/post launch averages
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Any

DATA_DIR = Path(__file__).parent / "data"
LAUNCH_DATE = "2026-04-01"


# ─────────────────────────────────────────
# Tool 1: Metric Aggregation
# ─────────────────────────────────────────
def aggregate_metrics(metrics_path: str = None) -> dict:
    """Load metrics and compute basic stats per metric."""
    path = metrics_path or DATA_DIR / "metrics.json"
    with open(path) as f:
        data = json.load(f)

    results = {}
    for metric_name, series in data["metrics"].items():
        if not isinstance(series, list):
            continue
        # Only use simple numeric series
        values = []
        for point in series:
            for k, v in point.items():
                if k != "date" and isinstance(v, (int, float)):
                    values.append(v)
                    break

        if not values:
            continue

        pre_launch = []
        post_launch = []
        for point in series:
            date_str = point.get("date", "")
            for k, v in point.items():
                if k != "date" and isinstance(v, (int, float)):
                    if date_str < LAUNCH_DATE:
                        pre_launch.append(v)
                    else:
                        post_launch.append(v)
                    break

        results[metric_name] = {
            "pre_launch_avg": round(sum(pre_launch) / len(pre_launch), 4) if pre_launch else None,
            "post_launch_avg": round(sum(post_launch) / len(post_launch), 4) if post_launch else None,
            "latest_value": values[-1],
            "min": min(values),
            "max": max(values),
            "data_points": len(values),
        }

    print(f"[TOOL: aggregate_metrics] Processed {len(results)} metrics.")
    return results


# ─────────────────────────────────────────
# Tool 2: Anomaly Detection
# ─────────────────────────────────────────
def detect_anomalies(metrics_path: str = None) -> dict:
    """Compare latest metric values against success criteria. Return breaches."""
    path = metrics_path or DATA_DIR / "metrics.json"
    with open(path) as f:
        data = json.load(f)

    criteria = data.get("success_criteria", {})
    metrics = data["metrics"]
    anomalies = []
    all_clear = []

    checks = {
        "activation_conversion": (">=", criteria.get("activation_conversion_min")),
        "crash_rate": ("<=", criteria.get("crash_rate_max")),
        "api_latency_p95_ms": ("<=", criteria.get("api_latency_p95_max_ms")),
        "payment_success_rate": (">=", criteria.get("payment_success_rate_min")),
        "support_tickets": ("<=", criteria.get("support_tickets_max_daily")),
        "churn_cancellations": ("<=", criteria.get("churn_max_daily")),
        "retention_d1": (">=", criteria.get("retention_d1_min")),
    }

    for metric_name, (op, threshold) in checks.items():
        series = metrics.get(metric_name)
        if not series or threshold is None:
            continue
        latest = None
        for point in series:
            for k, v in point.items():
                if k != "date" and isinstance(v, (int, float)):
                    latest = v
                    break
        if latest is None:
            continue

        passed = (latest >= threshold) if op == ">=" else (latest <= threshold)
        entry = {
            "metric": metric_name,
            "latest_value": latest,
            "threshold": threshold,
            "operator": op,
            "breach": not passed,
            "severity": "HIGH" if not passed else "OK",
        }
        if not passed:
            anomalies.append(entry)
        else:
            all_clear.append(entry)

    print(f"[TOOL: detect_anomalies] Found {len(anomalies)} breaches, {len(all_clear)} passing.")
    return {"breaches": anomalies, "passing": all_clear, "total_breaches": len(anomalies)}


# ─────────────────────────────────────────
# Tool 3: Sentiment Summary
# ─────────────────────────────────────────
def summarize_sentiment(feedback_path: str = None) -> dict:
    """Count sentiments, extract top repeated issues, compute sentiment score."""
    path = feedback_path or DATA_DIR / "user_feedback.json"
    with open(path) as f:
        feedback = json.load(f)

    counts = {"positive": 0, "neutral": 0, "negative": 0}
    negative_keywords = {}
    positive_themes = []
    negative_samples = []
    positive_samples = []

    keyword_list = ["crash", "slow", "payment", "broken", "cancel", "refund",
                    "error", "unusable", "uninstall", "fix", "rollback"]

    for item in feedback:
        s = item.get("sentiment", "neutral")
        counts[s] = counts.get(s, 0) + 1
        text = item.get("text", "").lower()

        if s == "negative":
            negative_samples.append(item["text"])
            for kw in keyword_list:
                if kw in text:
                    negative_keywords[kw] = negative_keywords.get(kw, 0) + 1
        elif s == "positive":
            positive_samples.append(item["text"])

    total = sum(counts.values())
    sentiment_score = round((counts["positive"] - counts["negative"]) / total, 3) if total else 0

    top_issues = sorted(negative_keywords.items(), key=lambda x: x[1], reverse=True)[:5]

    result = {
        "total_feedback": total,
        "counts": counts,
        "sentiment_score": sentiment_score,  # -1 to +1
        "negative_pct": round(counts["negative"] / total * 100, 1) if total else 0,
        "positive_pct": round(counts["positive"] / total * 100, 1) if total else 0,
        "top_issues": [{"keyword": k, "mentions": v} for k, v in top_issues],
        "sample_negative": negative_samples[:3],
        "sample_positive": positive_samples[:2],
    }

    print(f"[TOOL: summarize_sentiment] {total} feedback items. Score: {sentiment_score}. "
          f"Negative: {result['negative_pct']}%")
    return result


# ─────────────────────────────────────────
# Tool 4: Trend Comparison
# ─────────────────────────────────────────
def compare_trend(metrics_path: str = None) -> dict:
    """Compute % change for each metric from pre-launch avg to latest value."""
    path = metrics_path or DATA_DIR / "metrics.json"
    with open(path) as f:
        data = json.load(f)

    aggregated = aggregate_metrics(metrics_path)
    trends = []

    for metric_name, stats in aggregated.items():
        pre = stats["pre_launch_avg"]
        latest = stats["latest_value"]
        if pre and pre != 0:
            change_pct = round((latest - pre) / abs(pre) * 100, 2)
            direction = "UP" if change_pct > 0 else "DOWN"
            # Higher is better for some, lower for others
            lower_is_better = {"crash_rate", "api_latency_p95_ms", "support_tickets", "churn_cancellations"}
            is_bad = (direction == "DOWN" and metric_name not in lower_is_better) or \
                     (direction == "UP" and metric_name in lower_is_better)

            trends.append({
                "metric": metric_name,
                "pre_launch_avg": pre,
                "latest_value": latest,
                "change_pct": change_pct,
                "direction": direction,
                "concerning": is_bad and abs(change_pct) > 5,
            })

    concerning = [t for t in trends if t["concerning"]]
    print(f"[TOOL: compare_trend] {len(concerning)} concerning trends out of {len(trends)} metrics.")
    return {"trends": trends, "concerning_count": len(concerning), "concerning_metrics": concerning}
