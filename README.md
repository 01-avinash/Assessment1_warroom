Assessment 1 — War Room Launch Decision System

PurpleMerit AI/ML Engineer Assessment | April 2026

What This Does

A multi-agent AI system that simulates a cross-functional "war room". It reads 14 days of product metrics + 45 user feedback entries, then 5 agents collaborate to decide: Proceed / Pause / Roll Back a feature launch.

Agent Flow

Orchestrator
   ├── calls 4 tools (aggregate, anomaly, sentiment, trend)
   ├── PM Agent          → go/no-go framing
   ├── Data Analyst      → metric breach analysis
   ├── Marketing Agent   → sentiment + comms
   ├── Risk/Critic Agent → risk register
   └── Final Decision    → JSON output
Run on Mac

cd Assessment1_WarRoom
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
Run on Windows

cd Assessment1_WarRoom
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python main.py
Optional LLM Mode

export ANTHROPIC_API_KEY=sk-ant-your-key   # Mac
set ANTHROPIC_API_KEY=sk-ant-your-key      # Windows
python main.py
Output

output/launch_decision_latest.json
Traces

All agent steps print to console. Save with:

python main.py 2>&1 | tee output/trace.log
