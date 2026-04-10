"""
main.py — Entry point for Assessment 1: War Room Launch Decision System
Usage:  cd assessment1 && python main.py
Output: output/launch_decision_latest.json
"""

import json
import io
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path so agents and tools are found
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "agents"))

from agents import WarRoomOrchestrator

OUTPUT_DIR = ROOT / "output"
OUTPUT_DIR.mkdir(exist_ok=True)


def main():
    print("\n" + "🚨 " * 20)
    print("PURPLEMERIT — WAR ROOM LAUNCH DECISION SYSTEM")
    print("Assessment 1: Multi-Agent Product Launch Analyser")
    print("🚨 " * 20 + "\n")

    if os.environ.get("ANTHROPIC_API_KEY"):
        print("✅ LLM Mode: Claude API key detected.\n")
    else:
        print("⚠️  Rule-based Mode: No API key — running with rule-based logic.\n")

    orchestrator = WarRoomOrchestrator()
    result = orchestrator.run()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = OUTPUT_DIR / f"launch_decision_{timestamp}.json"
    latest_file = OUTPUT_DIR / "launch_decision_latest.json"

    with open(output_file, "w") as f:
        json.dump(result, f, indent=2)
    with open(latest_file, "w") as f:
        json.dump(result, f, indent=2)

    print("\n" + "="*60)
    print("FINAL STRUCTURED OUTPUT")
    print("="*60)
    summary = {
        "decision": result["decision"],
        "confidence_score": result["confidence_score"],
        "rationale_summary": result["rationale"]["summary"],
        "critical_risks": len([r for r in result["risk_register"] if r["severity"] == "CRITICAL"]),
        "immediate_actions": [a["action"] for a in result["action_plan_24_48h"] if a["priority"] == "P0"],
    }
    print(json.dumps(summary, indent=2))
    print(f"\n✅ Full output saved to: {output_file}")
    print(f"✅ Latest output at:    {latest_file}")

if __name__ == "__main__":
    main()
