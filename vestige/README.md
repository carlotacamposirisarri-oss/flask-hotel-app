# Vestige Intelligence

Clienteling, competitive mapping, relationship strategy and growth platform for
[Vestige](https://www.vestigeloyalty.com). Claude is the primary strategist; Chat
Astra is optional (per task or as fallback). Everything is exportable as an
editorial deck (print-to-PDF or PowerPoint).

## Run it

```bash
pip install -r vestige/requirements.txt
python -m vestige.seed          # optional: fictional demo portfolio
python -m vestige               # http://127.0.0.1:5050
```

Then open **Settings** and paste the Anthropic API key (or set `ANTHROPIC_API_KEY`
in `.env`). Keys stay on the server: env vars or `vestige/instance/secrets.json`
(mode 600). They are never sent to the browser.

Locally there is no login (bound to `127.0.0.1`). Set `VESTIGE_PASSWORD` to require one.

## Deploy on Render

1. Render → **New → Blueprint** → select this repository (uses `render.yaml`).
2. Fill in `VESTIGE_PASSWORD` (the shared access password) and `ANTHROPIC_API_KEY`.
3. Deploy. Data lives on a 1 GB persistent disk at `/var/data` (requires the paid Starter instance;
   on a free instance the database would be wiped on every restart).
4. Optional: set `VESTIGE_DEMO_SEED=1` once to load the fictional demo portfolio, then remove it.

On Render the app refuses to serve anything until `VESTIGE_PASSWORD` is set. Sessions use secure,
HTTP-only cookies; login is throttled to 5 attempts per 15 minutes per IP.

## What's inside

| Module | Where | What it does |
|---|---|---|
| Brand engagements | `+ New engagement` | Heritage, values, visual codes, tone, archetypes, positioning, gaps. Every AI output is filtered through them. |
| Client intelligence | `Clients` | Gallery, 360° portraits, interest network graph, timeline, AI "gaps & next best action". |
| Client discovery | `Client discovery` | Paste raw notes → AI builds a structured profile with affinity scores → you confirm. |
| CRM import | `CRM import` | CSV/XLSX from Salesforce, HubSpot, SAP…; auto field mapping you can correct; upserts by email/name; import log. |
| Competitors | `Competitors` | Competitor set, configurable strategic map, AI cross-examination per rival. |
| Insights & prospecting | `Insights` | Ranked insight feed + ask-anything analyst. |
| Story & community | `Story & community` | Story arcs, messaging angles, community blueprints. |
| Retention & experiences | `Retention` | Archetype retention plays, experiential initiatives, 12-month roadmap. |
| Collaborations | `Collaborations` | Partner pipeline with compatibility, brand-fit check, rival conflicts. |
| Emotion & audit | `Emotion & audit` | Emotional CX map, beat-by-beat event designer, strategy audit with pivots. |
| Intelligence layer | `Intelligence layer` | Anonymised cross-brand patterns, benchmarks, saved queries, AI intelligence briefs. |
| Growth studio | `Growth studio` | Practice KPIs, goals, AI growth plan, opportunity radar, health check, course corrections. |
| Deliverable studio | `Deliverable studio` | Assemble or AI-compose decks from any work, edit/reorder slides, PDF and PPTX export. |

Every AI item can be accepted, dismissed, prioritised, refined and annotated, and is
stamped with the model and the maison it was filtered through.

## Architecture

- Flask + SQLite (`vestige/instance/vestige.db`), server-rendered, no build step.
- `prompts.py` — the registry of work types (`KINDS`): add a deliverable type by adding an entry.
- `analytics.py` — context builders for the AI and anonymised aggregates.
- `ai.py` — Claude (Anthropic SDK, server-side refusal fallback) and Chat Astra (OpenAI-compatible endpoint).
- All brand data carries `brand_id`; the internal and growth layers only read anonymised aggregates.
  Auth can be added later as a blueprint `before_request` without schema changes.
