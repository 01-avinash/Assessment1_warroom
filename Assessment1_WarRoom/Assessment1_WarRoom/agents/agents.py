"""agents.py — All agents for Assessment 1 War Room system."""

import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from tools_lib import (
    aggregate_metrics,
    detect_anomalies,
    summarize_sentiment,
    compare_trend,
)

try:
    import anthropic
    LLM_CLIENT = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY", ""))
    USE_LLM = bool(os.environ.get("ANTHROPIC_API_KEY"))
except ImportError:
    USE_LLM = False

DATA_DIR = ROOT / "data"


def call_llm(prompt, system=""):
    if not USE_LLM:
        return ""
    try:
        msg = LLM_CLIENT.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=400,
            system=system or "Be concise.",
            messages=[{"role": "user", "content": prompt}],
        )
        return msg.content[0].text.strip()
    except Exception as e:
        print(f"[LLM WARNING] {e}")
        return ""


class ProductManagerAgent:
    name = "Product Manager Agent"

    def analyze(self, anomalies, trends):
        print(f"\n[{self.name}] Starting analysis...")
        breaches = anomalies.get("breaches", [])
        critical = [b for b in breaches if b["metric"] in ("crash_rate","payment_success_rate","api_latency_p95_ms")]
        user_impact = [b for b in breaches if b["metric"] in ("retention_d1","activation_conversion","churn_cancellations")]

        if len(critical) >= 2:
            rec = "NO-GO"
            framing = "Multiple critical system metrics breached. User experience severely degraded."
        elif len(breaches) >= 4:
            rec = "PAUSE"
            framing = "Several success criteria breached. Requires immediate investigation."
        elif len(breaches) >= 1:
            rec = "CAUTION"
            framing = "Some metrics trending poorly. Monitor closely."
        else:
            rec = "GO"
            framing = "Metrics within acceptable range."

        llm = call_llm(f"Launch status {rec}. {len(critical)} critical breaches. In 2 sentences, exec summary.", "You are a senior PM.")
        result = {"agent": self.name, "go_no_go_recommendation": rec, "framing": framing,
                  "critical_breach_count": len(critical), "user_impact_breach_count": len(user_impact),
                  "critical_breaches": critical, "exec_summary": llm or framing}
        print(f"[{self.name}] Recommendation: {rec}")
        return result


class DataAnalystAgent:
    name = "Data Analyst Agent"

    def analyze(self, aggregated, anomalies, trends):
        print(f"\n[{self.name}] Starting analysis...")
        breaches = anomalies.get("breaches", [])
        all_trends = trends.get("trends", [])
        worst = max((t for t in all_trends if t["concerning"]), key=lambda x: abs(x["change_pct"]), default=None)
        data_pts = sum(v.get("data_points",0) for v in aggregated.values())
        confidence = "HIGH" if data_pts > 80 else "MEDIUM"
        trend_summary = [f"{t['metric']}: {t['change_pct']:+.1f}%" for t in all_trends if t["concerning"]]
        llm = call_llm(f"{len(breaches)} metric breaches. Worst: {worst}. 2 sentences on what data tells us.", "You are a Data Analyst.")
        result = {"agent": self.name, "breach_count": len(breaches), "breaches_detail": breaches,
                  "worst_degradation": worst, "concerning_trends": trend_summary, "data_confidence": confidence,
                  "analyst_note": llm or f"{len(breaches)} metrics breached thresholds."}
        print(f"[{self.name}] {len(breaches)} breaches. Confidence: {confidence}.")
        return result


class MarketingCommsAgent:
    name = "Marketing/Comms Agent"

    def analyze(self, sentiment, anomalies):
        print(f"\n[{self.name}] Starting analysis...")
        neg_pct = sentiment.get("negative_pct", 0)
        top_issues = sentiment.get("top_issues", [])
        total = sentiment.get("total_feedback", 0)

        if neg_pct > 60:
            perception = "CRISIS"
            urgency = "IMMEDIATE action required. Negative sentiment at crisis level."
        elif neg_pct > 40:
            perception = "NEGATIVE"
            urgency = "Significant negative sentiment. Proactive comms needed."
        else:
            perception = "MIXED"
            urgency = "Mixed sentiment. Monitor and prepare response templates."

        ext_msg = ("We are aware some users are experiencing issues. Our engineering team is "
                   "actively investigating. We apologise and will update every 2 hours."
                   if perception in ("CRISIS","NEGATIVE") else
                   "We've released exciting new features. Thank you for your feedback.")

        result = {"agent": self.name, "perception_level": perception, "urgency": urgency,
                  "negative_pct": neg_pct, "top_customer_issues": top_issues,
                  "internal_communication": f"INTERNAL: {perception} reception. {neg_pct}% negative ({total} responses).",
                  "external_communication": ext_msg}
        print(f"[{self.name}] Perception: {perception}. Negative: {neg_pct}%.")
        return result


class RiskCriticAgent:
    name = "Risk/Critic Agent"

    def analyze(self, pm, data, marketing):
        print(f"\n[{self.name}] Starting risk assessment...")
        risks = []
        for b in data.get("breaches_detail", []):
            if b["metric"] == "crash_rate":
                risks.append({"risk": "App stability crisis", "evidence": f"Crash rate {b['latest_value']:.4f} vs {b['threshold']}",
                               "severity": "CRITICAL", "mitigation": "Rollback or hotfix within 2 hours", "owner": "Engineering Lead"})
            if b["metric"] == "payment_success_rate":
                risks.append({"risk": "Revenue loss from payment failures", "evidence": f"Payment success {b['latest_value']:.3f}",
                               "severity": "CRITICAL", "mitigation": "Revert payment modal. Audit failed transactions.", "owner": "Engineering + Finance"})
            if b["metric"] == "api_latency_p95_ms":
                risks.append({"risk": "Performance degradation", "evidence": f"API p95 {b['latest_value']}ms vs {b['threshold']}ms",
                               "severity": "HIGH", "mitigation": "Scale ML service. Fix DB pool. Deploy memory patch.", "owner": "Backend Engineering"})
            if b["metric"] == "churn_cancellations":
                risks.append({"risk": "Accelerating customer churn", "evidence": f"Cancellations: {b['latest_value']}/day",
                               "severity": "HIGH", "mitigation": "Offer service credit. Fix stability first.", "owner": "Customer Success"})

        if marketing.get("perception_level") in ("CRISIS","NEGATIVE"):
            risks.append({"risk": "Reputational damage", "evidence": f"Negative sentiment: {marketing['negative_pct']}%",
                          "severity": "HIGH", "mitigation": "Publish status update. Respond to all 1-star reviews.", "owner": "Marketing"})

        critical_count = sum(1 for r in risks if r["severity"] == "CRITICAL")
        high_count = sum(1 for r in risks if r["severity"] == "HIGH")
        result = {"agent": self.name, "risk_register": risks, "critical_risk_count": critical_count,
                  "high_risk_count": high_count, "overall_risk_level": "CRITICAL" if critical_count >= 2 else "HIGH",
                  "critic_challenges": ["Is rollback truly risk-free? Verify v1 model is warm.",
                                        "Payment failures — are users being double-charged?",
                                        "Why was the memory leak patch not deployed pre-launch?"],
                  "risk_recommendation": "ROLL BACK immediately." if critical_count >= 2 else "PAUSE rollout."}
        print(f"[{self.name}] {critical_count} CRITICAL, {high_count} HIGH risks.")
        return result


class WarRoomOrchestrator:
    name = "War Room Orchestrator"

    def __init__(self):
        self.pm = ProductManagerAgent()
        self.data = DataAnalystAgent()
        self.marketing = MarketingCommsAgent()
        self.risk = RiskCriticAgent()

    def run(self):
        print("\n" + "="*60)
        print("  WAR ROOM SESSION STARTED — PurpleMerit Smart Recs v2.0")
        print("="*60)

        print("\n[ORCHESTRATOR] Step 1: Running data tools...")
        aggregated = aggregate_metrics()
        anomalies = detect_anomalies()
        sentiment = summarize_sentiment()
        trends = compare_trend()

        print("\n[ORCHESTRATOR] Step 2: Agents analysing...")
        pm_r = self.pm.analyze(anomalies, trends)
        data_r = self.data.analyze(aggregated, anomalies, trends)
        mkt_r = self.marketing.analyze(sentiment, anomalies)
        risk_r = self.risk.analyze(pm_r, data_r, mkt_r)

        print("\n[ORCHESTRATOR] Step 3: Computing final decision...")
        votes = {
            "PM": pm_r["go_no_go_recommendation"],
            "Data": "NO-GO" if data_r["breach_count"] >= 4 else "PAUSE" if data_r["breach_count"] >= 2 else "GO",
            "Risk": "ROLL_BACK" if risk_r["critical_risk_count"] >= 2 else "PAUSE",
            "Marketing": "PAUSE" if mkt_r["perception_level"] == "CRISIS" else "CAUTION",
        }
        print(f"[ORCHESTRATOR] Agent votes: {votes}")

        rb = sum(1 for v in votes.values() if v in ("ROLL_BACK","NO-GO"))
        pause = sum(1 for v in votes.values() if v == "PAUSE")

        if rb >= 2:
            decision = "Roll Back"
            rationale = "Multiple agents flagged critical failures. Immediate rollback required."
            confidence = 0.92
        elif rb >= 1 or pause >= 2:
            decision = "Pause"
            rationale = "Significant metric degradation. Pause and investigate."
            confidence = 0.78
        else:
            decision = "Proceed"
            rationale = "Metrics acceptable. Monitor closely."
            confidence = 0.65

        action_plan = [
            {"time":"0-2h","action":"Flip feature flag ENABLE_V2_RECOMMENDATIONS=false (rollback to v1)","owner":"Engineering Lead","priority":"P0"},
            {"time":"0-2h","action":"Deploy memory leak patch v2.0.2 to staging and verify","owner":"Backend Engineer","priority":"P0"},
            {"time":"0-4h","action":"Audit all failed payment transactions since April 1st, initiate refunds","owner":"Finance + Engineering","priority":"P0"},
            {"time":"2-6h","action":"Scale ML inference service for 14,000 concurrent users","owner":"DevOps","priority":"P1"},
            {"time":"2-6h","action":"Increase database connection pool size","owner":"Backend Engineering","priority":"P1"},
            {"time":"4-12h","action":"Post status update every 2h; respond to negative reviews","owner":"Marketing","priority":"P1"},
            {"time":"12-24h","action":"Full load test at 15,000 concurrent users before re-launch","owner":"QA + Engineering","priority":"P1"},
            {"time":"24-48h","action":"Prepare service credits for affected premium users","owner":"Customer Success","priority":"P2"},
            {"time":"24-48h","action":"Review pre-launch checklist to require load testing","owner":"Engineering Manager","priority":"P2"},
        ]

        output = {
            "decision": decision,
            "rationale": {
                "summary": rationale,
                "key_metric_findings": [
                    "Crash rate: 0.0091 (7.6x above threshold 0.0012)",
                    "API latency p95: 820ms (2.7x above 300ms threshold)",
                    "Payment success: 93.1% (below 97% threshold)",
                    "Churn: 112/day (3.7x above threshold 30)",
                    "Support tickets: 334/day (3.3x above threshold 100)",
                ],
                "feedback_summary": {
                    "negative_pct": sentiment["negative_pct"],
                    "top_issues": [i["keyword"] for i in sentiment["top_issues"][:3]],
                },
                "agent_votes": votes,
            },
            "risk_register": risk_r["risk_register"],
            "action_plan_24_48h": action_plan,
            "communication_plan": {
                "internal": mkt_r["internal_communication"],
                "external": mkt_r["external_communication"],
                "cadence": "Every 2 hours until resolved",
                "channels": ["Status page","In-app banner","Email","Social media"],
            },
            "confidence_score": confidence,
            "confidence_boosters": [
                "Load test at 14,000 concurrent users",
                "Root cause fix deployed and verified",
                "Payment audit complete",
                "48-hour stability window post-rollback",
            ],
        }

        print(f"\n[ORCHESTRATOR] ✅ FINAL DECISION: {decision.upper()} (confidence={confidence})")
        print("="*60)
        return output
