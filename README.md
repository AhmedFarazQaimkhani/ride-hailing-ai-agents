# Ride-Hailing Driver Co-Pilot — AI Agents

**AI co-pilot for ride-hailing drivers to earn more with less stress.**

This repo implements **7 agentic AI agents** that work together inside a driver app (e.g. Uber / Careem / inDrive) to give proactive, personalized recommendations.

## Where is the AI? Do I need an API key?

- **By default you don’t need any API key.** All agents use rule-based and mock logic (time, traffic, simple scores). The “AI” is in the **agent design** (multiple specialized agents, clear protocol, orchestration).
- **If you add an OpenAI API key:** Copy `.env.example` to `.env` and set `OPENAI_API_KEY=sk-...`. Then **Demand Anticipation**, **Idle-Time Optimization**, and **Earnings Strategy** use the LLM to generate their recommendations; the **Explainable Coach** uses it to generate the “why” for each one. No key → all of that is rule-based, no API calls.
- **Later:** You can plug in real ML (demand forecasting, RL for idle-time, etc.); those typically don’t require OpenAI.

## Agents

| Agent | Role |
|-------|------|
| **1. Demand Anticipation** | Predicts where demand *will* be (not just heatmaps). e.g. *"In 12 mins, demand will spike near Mall X — move now."* |
| **2. Idle-Time Optimization** | Suggests best waiting spot, micro-movements (200–500 m), or short breaks. *"Wait here 6 mins — moving now reduces your chances."* |
| **3. Earnings Strategy** | Personalized: when to log in/out, which rides to accept/skip. *"Skipping this ride likely gives higher fare in 8 mins nearby."* |
| **4. Parking & Waiting Safety** | Legal waiting spots, no-parking zones, enforcement risk. Avoids fines. |
| **5. Fatigue & Stress Monitoring** | Monitors continuous driving and break patterns. *"Your earnings drop after 3.5 hours — take a 15-min break."* |
| **6. Multi-App Arbitrage** | For drivers on Uber + Careem + inDrive: which app to prioritize, when to switch. *"Pause Uber — Careem demand rising nearby."* |
| **7. Explainable AI Coach** | Turns agent outputs into clear explanations to build driver trust. |

## What we used

- **Python 3.11+** — core logic; no agent framework (each agent is a class with `run(context) → list[Recommendation]`).
- **FastAPI + Uvicorn** — API for the web UI. **Vanilla HTML/CSS/JS** — frontend.
- **Optional: OpenAI** — with `OPENAI_API_KEY` set, **Demand Anticipation**, **Idle-Time Optimization**, and **Earnings Strategy** use `gpt-4o-mini` to generate recommendations; the **Explainable Coach** uses it to generate the “why” text. Without the key, all of that is rule-based (no API calls).

For **LinkedIn post templates** and a **one-line elevator pitch**, see **[LINKEDIN.md](LINKEDIN.md)**.

## Architecture

- **`core/`** — Shared types: `DriverContext`, `AgentContext`, `Recommendation`, and the `DriverAgent` protocol.
- **`agents/`** — One module per agent; each implements `run(context) -> list[Recommendation]`.
- **`copilot/`** — **Driver Co-Pilot** orchestrator: runs all agents, filters by confidence, enriches with explanations, and sorts by priority.
- **`data/`** — Mock context builders for demos.

## Setup

```bash
cd "Ride Hailing Ai Agents"
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Run demo

```bash
PYTHONPATH=. python run_demo.py              # default scenario
PYTHONPATH=. python run_demo.py fatigue      # long session → fatigue nudge
PYTHONPATH=. python run_demo.py multi_app    # evening rush, multi-app switch
PYTHONPATH=. python run_demo.py rain_event   # rain + event → demand + parking
```

## Run web UI (LinkedIn-ready)

```bash
PYTHONPATH=. python run_web.py
```

Then open **http://localhost:8000** in your browser. Use the scenario buttons to switch contexts and see different agent recommendations. Ideal for screenshots and screen recordings for LinkedIn.

## Deploy for free

See **[DEPLOY.md](DEPLOY.md)** for hosting on **Render**, **Railway**, or **Fly.io** at no cost. Add your `OPENAI_API_KEY` in the platform’s environment for LLM-powered recommendations.

## Extending

- **Real demand model**: Replace mock logic in `DemandAnticipationAgent` with a forecasting model (e.g. time series + events + weather).
- **RL for idle time**: Use reinforcement learning in `IdleTimeOptimizationAgent` to learn wait vs move policies.
- **LLM explanations**: Call an LLM in `ExplainableCoachAgent.enrich()` to generate natural-language explanations from `reasoning` and `action_payload`.

## License

MIT (or your choice).
